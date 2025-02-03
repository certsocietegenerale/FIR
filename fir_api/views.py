# for token Generation
import io

from django.apps import apps
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.shortcuts import get_object_or_404
from django.core.files import File as FileWrapper
from django.contrib.auth.models import User
from django.db.models import Q, Max

from rest_framework.renderers import JSONRenderer
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.exceptions import PermissionDenied
from rest_framework.authtoken.models import Token
from rest_framework.mixins import (
    ListModelMixin,
    RetrieveModelMixin,
    CreateModelMixin,
    UpdateModelMixin,
)
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework import renderers
from rest_framework.response import Response
from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

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
    API endpoints that allow users to be viewed or edited.
    """

    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated, IsAdminUser)


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

    queryset = (Incident.objects.all()).annotate(
        last_comment_date=Max("comments__date")
    )  # Will be overriden by get_queryset(). We still need to define this property as DRF use it to get the basename
    serializer_class = IncidentSerializer
    permission_classes = (IsAuthenticated, IsIncidentHandler)
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = [
        "id",
        "date",
        "status",
        "subject",
        "concerned_business_lines",
        "last_comment_date",
    ]
    filterset_class = IncidentFilter

    def get_queryset(self):
        queryset = (
            Incident.authorization.for_user(
                self.request.user, "incidents.view_incidents"
            )
            .annotate(last_comment_date=Max("comments__date"))
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


class ArtifactViewSet(ListModelMixin, RetrieveModelMixin, viewsets.GenericViewSet):
    """
    API endpoint to list artifacts.
    Artifacts can't be created or edited via the API, they are automatically generated from incident descriptions and comments.
    You can view all incidents having an artifact by accessing /artifacts/<id>
    """

    queryset = Artifact.objects.all()
    serializer_class = ArtifactSerializer
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

    def retrieve(self, request, *args, **kwargs):
        artifact = self.get_queryset().get(pk=self.kwargs.get("pk"))
        correlations = artifact.relations_for_user(user=None).group()
        if all([not link_type.objects.exists() for link_type in correlations.values()]):
            raise PermissionError
        serializer = self.get_serializer(artifact)
        return Response(serializer.data)


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

    queryset = Label.objects.all()
    serializer_class = LabelSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = [DjangoFilterBackend]
    filterset_class = LabelFilter

    def get_queryset(self):
        return super().get_queryset()


class FileViewSet(ListModelMixin, RetrieveModelMixin, viewsets.GenericViewSet):
    """
    API endpoint for listing files.
    Files can be uploaded and downloaded via endpoints /files/<incidentID>/upload and /files/<incidentID>/download
    """

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
        if type(self.request.data).__name__ == "dict":
            uploaded_files = request.FILES.get("file", [])
        else:
            uploaded_files = request.FILES.getlist("file", [])

        if type(self.request.data).__name__ == "dict":
            descriptions = request.data.get("description", [])
        else:
            descriptions = request.data.getlist("description", [])

        if len(descriptions) != len(uploaded_files):
            return Response(
                data={"Error": "Missing 'description' or 'file'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        for uploaded_file, description in zip(uploaded_files, descriptions):
            file_wrapper = FileWrapper(uploaded_file.file)
            file_wrapper.name = uploaded_file.name
            file = handle_uploaded_file(file_wrapper, description, incident)
            files_added.append(file)

        resp_data = FileSerializer(
            files_added, many=True, context={"request": request}
        ).data
        return Response(resp_data)


class AttributeViewSet(viewsets.ModelViewSet):
    """
    API endpoints for listing, creating or editing incident attributes.
    Before adding an attribute to an incident, you have to register the said attribute in ValidAttributes (see endpoints /validattributes)
    """

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
        except Attribute.DoesNotExist:
            serializer.save()

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

    queryset = ValidAttribute.objects.all()
    serializer_class = ValidAttributeSerializer
    permission_classes = (IsAuthenticated, IsIncidentHandler)
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = ["id", "name", "unit", "description", "categories"]
    filterset_class = ValidAttributeFilter


class BusinessLinesViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for listing Business Lines.
    """

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
    """
    API endpoint for listing Incident Categories.
    """

    queryset = IncidentCategory.objects.all()
    serializer_class = IncidentCategoriesSerializer
    permission_classes = (IsAuthenticated, IsIncidentHandler)
    filterset_class = IncidentCategoriesFilter
    filter_backends = [DjangoFilterBackend, OrderingFilter]


# Token Generation ===========================================================


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)
