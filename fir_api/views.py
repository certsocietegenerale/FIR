# for token Generation
import io
from axes.signals import user_locked_out

from django.apps import apps
from django.conf import settings
from django.db.models import Q, OuterRef, Subquery
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _

from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.exceptions import PermissionDenied
from rest_framework.authtoken.models import Token
from rest_framework.mixins import (
    ListModelMixin,
    RetrieveModelMixin,
    CreateModelMixin,
    UpdateModelMixin,
    DestroyModelMixin,
)
from rest_framework import viewsets, status
from rest_framework.renderers import JSONRenderer, AdminRenderer
from rest_framework.response import Response
from rest_framework.filters import OrderingFilter

from django_filters.rest_framework import DjangoFilterBackend

from fir_api.serializers import (
    UserSerializer,
    IncidentSerializer,
    CommentsSerializer,
    LabelSerializer,
    AttributeSerializer,
    BusinessLineSerializer,
    CategorySerializer,
    ValidAttributeSerializer,
    SeveritySerializer,
    StatusSerializer,
)
from fir_api.filters import (
    IncidentFilter,
    LabelFilter,
    AttributeFilter,
    BLFilter,
    CommentFilter,
    CategoryFilter,
    ValidAttributeFilter,
    SeverityFilter,
    StatusFilter,
)
from fir_api.permissions import (
    IsIncidentHandler,
    IsAdminUserOrReadOnly,
)
from fir_api.permissions import IsIncidentHandler
from incidents.models import (
    Incident,
    Comments,
    Label,
    Log,
    Attribute,
    BusinessLine,
    IncidentCategory,
    ValidAttribute,
    SeverityChoice,
    IncidentStatus,
)


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoints that allow users to be viewed or edited.
    Unless disabled by admins, users can change their own password by making
    POST requests to /api/users/change_password
    """

    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    renderer_classes = [JSONRenderer, AdminRenderer]

    @action(detail=False, permission_classes=[IsAuthenticated], methods=["POST"])
    def change_password(self, request):
        if not settings.USER_SELF_SERVICE.get("CHANGE_PASSWORD", True):
            return Response(
                data={"Error": "Password change is disabled."},
                status=status.HTTP_403_FORBIDDEN,
            )

        password = request.data.get("old_password", "")
        new_password = request.data.get("new_password1", "")
        new_password2 = request.data.get("new_password2", "")

        if not request.user.check_password(raw_password=password):
            return Response(
                data={"Error": _("Current password is invalid.")},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if new_password != new_password2:
            return Response(
                data={"Error": _("New password does not match its confirmation.")},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            validate_password(new_password, request.user)
        except ValidationError:
            return Response(
                data={"Error": _("New password is too weak.")},
                status=status.HTTP_400_BAD_REQUEST,
            )
        request.user.set_password(new_password)
        request.user.save()
        Log.log("Password updated", request.user)
        update_session_auth_hash(request, request.user)
        return Response({"status": _("Password changed.")})


class IncidentViewSet(
    viewsets.GenericViewSet,
    ListModelMixin,
    CreateModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
):
    """
    API endpoints for viewing, creating and editing incidents
    """

    serializer_class = IncidentSerializer
    permission_classes = [IsAuthenticated, IsIncidentHandler]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = [
        "id",
        "date",
        "status",
        "subject",
        "concerned_business_lines",
        "last_comment_date",
        "category",
        "severity",
        "confidentiality",
        "actor",
        "detection",
        "opened_by",
    ]
    filterset_class = IncidentFilter

    def get_queryset(self):
        last_comment_action = Subquery(
            Comments.objects.filter(
                incident_id=OuterRef("id"),
            )
            .order_by("-date")
            .values("action__name")[:1]
        )

        last_comment_date = Subquery(
            Comments.objects.filter(
                incident_id=OuterRef("id"),
            )
            .order_by("-date")
            .values("date")[:1]
        )

        queryset = (
            Incident.authorization.for_user(
                self.request.user, "incidents.view_incidents"
            )
            .annotate(last_comment_date=last_comment_date)
            .annotate(last_comment_action=last_comment_action)
            .order_by("-id")
        )

        return queryset

    def get_businesslines(self, businesslines):
        """
        ::

                Gets businessline objects based on a list
                of businesslines

                Args:
                    businesslines (_type_): _description_

                Returns:
                    QuerySet: A QuerySet with BusinessLine objects as per filter
        """
        bl_filter = Q()
        for bline in businesslines:
            if " > " in bline:
                bline = bline.split(" > ")[-1]
            bl_filter = bl_filter | Q(name=bline)
        bls = BusinessLine.authorization.for_user(
            self.request.user, permission=["incidents.report_events"]
        ).filter(bl_filter)
        return bls

    def perform_create(self, serializer):
        opened_by = self.request.user
        serializer.is_valid(raise_exception=True)
        if type(self.request.data).__name__ == "dict":
            bls = self.request.data.get("concerned_business_lines", [])
        else:
            bls = self.request.data.getlist("concerned_business_lines", [])
        concerned_business_lines = []
        if bls:
            concerned_business_lines = self.get_businesslines(businesslines=bls)
        if bls and not concerned_business_lines:
            raise PermissionDenied(
                {
                    "message": "You don't have write permission on the business lines associated with this incident."
                }
            )
        if not (bls or opened_by.has_perm("incidents.handle_incidents")):
            raise PermissionDenied(
                {
                    "message": "Incidents without business line can only be created by global incident handlers."
                }
            )
        serializer.is_valid(raise_exception=True)
        instance = serializer.save(
            opened_by=opened_by,
            concerned_business_lines=concerned_business_lines,
        )
        instance.refresh_main_business_lines()
        instance.done_creating()

    def perform_update(self, serializer):
        serializer.is_valid(raise_exception=True)
        self.check_object_permissions(self.request, serializer.instance)
        Comments.create_diff_comment(
            self.get_object(), serializer.validated_data, self.request.user
        )
        if type(self.request.data).__name__ == "dict":
            bls = self.request.data.get("concerned_business_lines", [])
        else:
            bls = self.request.data.getlist("concerned_business_lines", [])
        extra_dataset = {}
        if bls:
            extra_dataset["concerned_business_lines"] = self.get_businesslines(
                businesslines=bls
            )
        if bls and not extra_dataset["concerned_business_lines"]:
            raise PermissionDenied(
                {
                    "message": "You don't have write permission on the business lines associated with this incident."
                }
            )
        if not (bls or self.request.user.has_perm("incidents.handle_incidents")):
            raise PermissionDenied(
                {
                    "message": "Incidents without business line can only be created by global incident handlers."
                }
            )

        instance = serializer.save(**extra_dataset)
        instance.refresh_main_business_lines()
        if "description" in serializer.validated_data:
            instance.refresh_artifacts(serializer.validated_data["description"])


class CommentViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows creation of, viewing, and closing of comments
    """

    serializer_class = CommentsSerializer
    permission_classes = [IsAuthenticated, IsIncidentHandler]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = ["id", "date"]
    filterset_class = CommentFilter

    def get_queryset(self):
        incidents_allowed = Incident.authorization.for_user(
            self.request.user, "incidents.view_incidents"
        )
        queryset = Comments.objects.filter(incident__in=incidents_allowed).order_by(
            "id", "date"
        )
        return queryset

    def perform_create(self, serializer):
        incident_object = Incident.objects.get(pk=self.request.data.get("incident"))
        self.check_object_permissions(self.request, incident_object)
        serializer.save(opened_by=self.request.user)
        serializer.validated_data["incident"].refresh_artifacts(
            serializer.validated_data["comment"]
        )

    def perform_update(self, serializer):
        self.check_object_permissions(self.request, serializer.instance.incident)
        serializer.save()
        serializer.validated_data["incident"].refresh_artifacts(
            serializer.validated_data["comment"]
        )

    def perform_destroy(self, instance):
        self.check_object_permissions(self.request, instance.incident)
        return super().perform_destroy(instance)


class LabelViewSet(ListModelMixin, viewsets.GenericViewSet):
    """
    API endpoint for viewing labels
    """

    serializer_class = LabelSerializer
    permission_classes = [IsAuthenticated, IsAdminUserOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = LabelFilter

    def get_queryset(self):
        return Label.objects.all().order_by("id")


class AttributeViewSet(viewsets.ModelViewSet):
    """
    API endpoints for listing, creating or editing incident attributes.
    Before adding an attribute to an incident, you have to register the said attribute in ValidAttributes (see endpoints /validattributes)
    """

    serializer_class = AttributeSerializer
    permission_classes = [IsAuthenticated, IsIncidentHandler]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = ["id", "name", "value", "incident"]
    filterset_class = AttributeFilter

    def get_queryset(self):
        incidents_allowed = Incident.authorization.for_user(
            self.request.user, "incidents.view_incidents"
        )
        queryset = Attribute.objects.filter(incident__in=incidents_allowed).order_by(
            "incident", "id"
        )
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        response_serializer = self.get_serializer(self.created_instance)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        incident_object_id = self.request.data.get("incident")
        incident_object = Incident.objects.get(pk=incident_object_id)
        self.check_object_permissions(self.request, incident_object)
        get_object_or_404(ValidAttribute, name=self.request.data.get("name"))
        # See if there is already an attribute in this incident with that name
        try:
            existing_attribute = Attribute.objects.get(
                name=self.request.data.get("name"), incident=incident_object
            )
            # If the value is an integer we just add to it
            try:
                new_value = int(existing_attribute.value) + int(
                    self.request.data.get("value")
                )
                existing_attribute.value = str(new_value)
            # If not an integer we overwrite
            except ValueError:
                existing_attribute.value = self.request.data.get("value")
            existing_attribute.save()
            self.created_instance = existing_attribute
        except Attribute.DoesNotExist:
            serializer.save()
            self.created_instance = serializer.instance

    def perform_update(self, serializer):
        self.check_object_permissions(self.request, serializer.instance.incident)
        serializer.save()

    def perform_destroy(self, instance):
        self.check_object_permissions(self.request, instance.incident)
        return super().perform_destroy(instance)


class ValidAttributeViewSet(viewsets.ModelViewSet):
    """
    API endpoints for listing, creating or editing valid (possible) attributes.
    """

    queryset = ValidAttribute.objects.all().order_by("id")
    serializer_class = ValidAttributeSerializer
    permission_classes = [IsAuthenticated, IsIncidentHandler]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = ["id", "name", "unit", "description", "categories"]
    filterset_class = ValidAttributeFilter


class BusinessLinesViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for listing Business Lines.
    """

    serializer_class = BusinessLineSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = ["id", "name"]
    filterset_class = BLFilter

    def get_queryset(self):
        queryset = BusinessLine.authorization.for_user(
            self.request.user, ["incidents.handle_incidents", "incidents.report_events"]
        ).order_by("id")
        return queryset


class CategoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint for listing Incident Categories.
    """

    queryset = IncidentCategory.objects.all().order_by("id")
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, IsAdminUserOrReadOnly]
    filterset_class = CategoryFilter
    filter_backends = [DjangoFilterBackend, OrderingFilter]


class SeverityViewSet(viewsets.ModelViewSet):
    """
    API endpoint for listing Incident Severities.
    """

    queryset = SeverityChoice.objects.all().order_by("name")
    serializer_class = SeveritySerializer
    permission_classes = [IsAuthenticated, IsAdminUserOrReadOnly]
    filterset_class = SeverityFilter
    filter_backends = [DjangoFilterBackend, OrderingFilter]


class StatusViewSet(viewsets.ModelViewSet):
    """
    API endpoint for listing Incident Statuses.
    """

    queryset = IncidentStatus.objects.all().order_by("name")
    serializer_class = StatusSerializer
    permission_classes = [IsAuthenticated, IsAdminUserOrReadOnly]
    filterset_class = StatusFilter
    filter_backends = [DjangoFilterBackend, OrderingFilter]


# Token Generation ===========================================================


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)


@receiver(user_locked_out)
def raise_permission_denied(*args, **kwargs):
    raise PermissionDenied(_("Too many failed login attempts"))
