# for token Generation
import io

from django.apps import apps
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.shortcuts import get_object_or_404
from django.core.files import File as FileWrapper
from django.contrib.auth.models import User
from django.db.models import Q

from rest_framework.renderers import JSONRenderer
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.authtoken.models import Token
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework import renderers
from rest_framework.response import Response
from rest_framework.filters import OrderingFilter

from fir_api.serializers import (
    UserSerializer,
    IncidentSerializer,
    ArtifactSerializer,
    FileSerializer,
    CommentsSerializer,
    LabelSerializer,
    AttributeSerializer,
    BusinessLineSerializer,
    IncidentCategoriesSerializer,
    ValidAttributeSerializer,
)
from django_filters.rest_framework import DjangoFilterBackend
from fir_api.filters import (
    IncidentFilter,
    ArtifactFilter,
    LabelFilter,
    AttributeFilter,
    BLFilter,
    CommentFilter,
    IncidentCategoriesFilter,
    ValidAttributeFilter,
    FileFilter,
)
from fir_api.permissions import IsIncidentHandler
from fir_artifacts.files import handle_uploaded_file, do_download
from fir_artifacts.models import Artifact, File
from incidents.models import (
    Incident,
    Comments,
    Label,
    Attribute,
    BusinessLine,
    IncidentCategory,
    ValidAttribute,
)


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """

    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated, IsAdminUser)


class IncidentViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows creation of, viewing, and closing of incidents
    """

    queryset = Incident.objects.all()
    serializer_class = IncidentSerializer
    permission_classes = (IsAuthenticated, IsIncidentHandler)
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = ["id", "date", "status", "subject", "concerned_business_lines"]
    filterset_class = IncidentFilter

    def get_queryset(self):
        queryset = Incident.authorization.for_user(
            self.request.user, "incidents.view_incidents"
        )
        return queryset

    def perform_create(self, serializer):
        serializer.is_valid(raise_exception=True)
        instance = serializer.save(opened_by=self.request.user)
        instance.refresh_main_business_lines()
        instance.done_creating()

    def perform_update(self, serializer):
        serializer.is_valid(raise_exception=True)
        self.check_object_permissions(self.request, serializer.instance)
        Comments.create_diff_comment(
            self.get_object(), serializer.validated_data, self.request.user
        )
        instance = serializer.save()
        instance.refresh_main_business_lines()


class ArtifactViewSet(ListModelMixin, viewsets.GenericViewSet):
    queryset = Artifact.objects.all()
    serializer_class = ArtifactSerializer
    lookup_field = "value"
    lookup_value_regex = ".+"
    permission_classes = (IsAuthenticated, IsIncidentHandler)
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = ["id", "type", "value"]
    filterset_class = ArtifactFilter

    def get_queryset(self):
        incidents_allowed = Incident.authorization.for_user(
            self.request.user, "incidents.view_incidents"
        )
        queryset = Artifact.objects.filter(incidents__in=incidents_allowed).distinct()
        return queryset


class CommentViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows creation of, viewing, and closing of comments
    """

    queryset = Comments.objects.all()
    serializer_class = CommentsSerializer
    permission_classes = (IsAuthenticated, IsIncidentHandler)
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = ["id", "date"]
    filterset_class = CommentFilter

    def get_queryset(self):
        incidents_allowed = Incident.authorization.for_user(
            self.request.user, "incidents.view_incidents"
        )
        queryset = Comments.objects.filter(incident__in=incidents_allowed)
        return queryset

    def perform_create(self, serializer):
        incident_object = get_object_or_404(
            Incident.authorization.for_user(
                self.request.user, "incidents.handle_incidents"
            ),
            pk=self.request.data.get("incident"),
        )
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
    queryset = Label.objects.all()
    serializer_class = LabelSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = [DjangoFilterBackend]
    filterset_class = LabelFilter

    def get_queryset(self):
        return super().get_queryset()


class FileViewSet(ListModelMixin, RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = File.objects.all()
    serializer_class = FileSerializer
    permission_classes = (IsAuthenticated, IsIncidentHandler)
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = ["id", "date", "incident"]
    filterset_class = FileFilter

    def get_queryset(self):
        incidents_allowed = Incident.authorization.for_user(
            self.request.user, "incidents.view_incidents"
        )
        queryset = File.objects.filter(incident__in=incidents_allowed)
        return queryset

    @action(detail=True, renderer_classes=[renderers.StaticHTMLRenderer])
    def download(self, request, pk):
        file_object = File.objects.get(pk=pk)
        self.check_object_permissions(self.request, file_object.incident)
        return do_download(request, pk)

    @action(detail=True, methods=["POST"])
    def upload(self, request, pk):
        incident = get_object_or_404(
            Incident.authorization.for_user(
                self.request.user, "incidents.handle_incidents"
            ),
            pk=pk,
        )
        files_added = []

        uploaded_files = request.FILES.getlist("file")
        descriptions = (
            request.data.getlist("description")
            if "description" in request.data
            else None
        )

        if descriptions is None or len(descriptions) != len(uploaded_files):
            return Response(
                data={"Error": "Missing 'description' or 'file'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        for uploaded_file, description in zip(
            request.FILES.getlist("file"), request.data.getlist("description")
        ):
            file_wrapper = FileWrapper(uploaded_file.file)
            file_wrapper.name = uploaded_file.name
            file = handle_uploaded_file(file_wrapper, description, incident)
            files_added.append(file)

        resp_data = FileSerializer(
            files_added, many=True, context={"request": request}
        ).data
        return Response(resp_data)


class AttributeViewSet(viewsets.ModelViewSet):
    queryset = Attribute.objects.all()
    serializer_class = AttributeSerializer
    permission_classes = (IsAuthenticated, IsIncidentHandler)
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = ["id", "name", "value", "incident"]
    filterset_class = AttributeFilter

    def get_queryset(self):
        incidents_allowed = Incident.authorization.for_user(
            self.request.user, "incidents.view_incidents"
        )
        queryset = Attribute.objects.filter(incident__in=incidents_allowed)
        return queryset

    def perform_create(self, serializer):
        incident_object = get_object_or_404(
            Incident.authorization.for_user(
                self.request.user, "incidents.handle_incidents"
            ),
            pk=self.request.data.get("incident"),
        )
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
        except Attribute.DoesNotExist:
            serializer.save()

    def perform_update(self, serializer):
        self.check_object_permissions(self.request, serializer.instance.incident)
        serializer.save()

    def perform_destroy(self, instance):
        self.check_object_permissions(self.request, instance.incident)
        return super().perform_destroy(instance)


class ValidAttributeViewSet(viewsets.ModelViewSet):
    queryset = ValidAttribute.objects.all()
    serializer_class = ValidAttributeSerializer
    permission_classes = (IsAuthenticated, IsIncidentHandler)
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = ["id", "name", "unit", "description", "categories"]
    filterset_class = ValidAttributeFilter


class BusinessLinesViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = BusinessLine.objects.all()
    serializer_class = BusinessLineSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = ["id", "name"]
    filterset_class = BLFilter

    def get_queryset(self):
        queryset = BusinessLine.authorization.for_user(
            self.request.user, ["incidents.handle_incidents", "incidents.report_events"]
        )
        return queryset


class IncidentCategoriesViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = IncidentCategory.objects.all()
    serializer_class = IncidentCategoriesSerializer
    permission_classes = (IsAuthenticated, IsIncidentHandler)
    filterset_class = IncidentCategoriesFilter


# Todos API
if apps.is_installed("fir_todos"):
    from fir_todos.models import TodoItem
    from fir_api.serializers import TodoSerializer
    from fir_api.filters import TodoFilter

    class TodoViewSet(viewsets.ModelViewSet):
        """
        API endpoint for Todo items
        """

        queryset = TodoItem.objects.all()
        serializer_class = TodoSerializer
        permission_classes = (IsAuthenticated, IsIncidentHandler)
        filter_backends = [DjangoFilterBackend, OrderingFilter]
        ordering_fields = ["id", "incident", "done_time"]
        filterset_class = TodoFilter

        def get_queryset(self):
            incidents_allowed = Incident.authorization.for_user(
                self.request.user, "incidents.view_incidents"
            )
            queryset = TodoItem.objects.filter(incident__in=incidents_allowed)
            return queryset

        def perform_create(self, serializer):
            incident_object = get_object_or_404(
                Incident.authorization.for_user(
                    self.request.user, "incidents.handle_incidents"
                ),
                pk=self.request.data.get("incident"),
            )
            self.check_object_permissions(self.request, incident_object)
            serializer.save()

        def perform_update(self, serializer):
            self.check_object_permissions(self.request, serializer.instance.incident)
            serializer.save()

        def perform_destroy(self, instance):
            self.check_object_permissions(self.request, instance.incident)
            return super().perform_destroy(instance)


if apps.is_installed("fir_nuggets"):
    from fir_nuggets.models import Nugget
    from fir_api.serializers import NuggetSerializer
    from fir_api.filters import NuggetFilter

    class NuggetViewSet(viewsets.ModelViewSet):
        queryset = Nugget.objects.all()
        serializer_class = NuggetSerializer
        permission_classes = (IsAuthenticated, IsIncidentHandler)
        filter_backends = [DjangoFilterBackend, OrderingFilter]
        ordering_fields = [
            "id",
            "source",
            "start_timestamp",
            "end_timestamp",
            "interpretation",
            "incident",
        ]
        filterset_class = NuggetFilter

        def get_queryset(self):
            incidents_allowed = Incident.authorization.for_user(
                self.request.user, "incidents.view_incidents"
            )
            queryset = Nugget.objects.filter(incident__in=incidents_allowed)
            return queryset

        def perform_create(self, serializer):
            incident_object = get_object_or_404(
                Incident.authorization.for_user(
                    self.request.user, "incidents.handle_incidents"
                ),
                pk=self.request.data.get("incident"),
            )
            self.check_object_permissions(self.request, incident_object)
            instance = serializer.save(found_by=self.request.user)
            incident_object.refresh_artifacts(instance.raw_data)

        def perform_update(self, serializer):
            self.check_object_permissions(self.request, serializer.instance.incident)
            incident_object = get_object_or_404(
                Incident.authorization.for_user(
                    self.request.user, "incidents.handle_incidents"
                ),
                pk=self.request.data.get("incident"),
            )
            instance = serializer.save(found_by=self.request.user)
            incident_object.refresh_artifacts(instance.raw_data)

        def perform_destroy(self, instance):
            self.check_object_permissions(self.request, instance.incident)
            return super().perform_destroy(instance)


# Token Generation ===========================================================


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)
