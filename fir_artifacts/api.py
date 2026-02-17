from django.core.files import File as FileWrapper
from django.shortcuts import get_object_or_404
from rest_framework import serializers, viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response
from django_filters.rest_framework import (
    NumberFilter,
    CharFilter,
    DateTimeFilter,
    FilterSet,
    DjangoFilterBackend,
)
from rest_framework.mixins import (
    DestroyModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
)

from incidents.models import Incident
from fir_api.permissions import CanViewIncident, CanWriteIncident
from fir_artifacts.models import File, Artifact
from fir_artifacts.files import handle_uploaded_file, do_download, do_download_archive


class ArtifactFilter(FilterSet):
    """
    A custom filter class for artifacts filtering
    """

    id = NumberFilter(field_name="id")
    type = CharFilter(field_name="type")
    value = CharFilter(field_name="value", lookup_expr="icontains")
    incidents = NumberFilter(field_name="incidents__id")

    class Meta:
        model = Artifact
        fields = ["id", "type", "incidents", "value"]


class FileFilter(FilterSet):
    """
    Custom filtering so we can partially match on name
    """

    id = NumberFilter(field_name="id")
    description = CharFilter(field_name="description", lookup_expr="icontains")
    uploaded_before = DateTimeFilter(field_name="date", lookup_expr="lte")
    uploaded_after = DateTimeFilter(field_name="date", lookup_expr="gte")
    incident = NumberFilter(field_name="incident__id")

    class Meta:
        model = File
        fields = ["id", "description", "incident"]


class ArtifactSerializer(serializers.ModelSerializer):
    """
    Serializer for /api/artifacts
    """
    incidents = serializers.SerializerMethodField()

    def get_incidents(self, obj):
        request = self.context.get("request")
        if not request:
            return []

        allowed_incidents = Incident.authorization.for_user(
            request.user, "incidents.view_incidents"
        )

        return list(
            obj.incidents
               .filter(id__in=allowed_incidents.values_list("id", flat=True))
               .values_list("id", flat=True)
        )

    class Meta:
        model = Artifact
        fields = ["id", "type", "value", "incidents"]
        read_only_fields = ["id", "type", "value"]



class IncidentArtifactSerializer(serializers.ModelSerializer):
    """
    Serializer for /api/incident/<id>
    """

    incidents_count = serializers.IntegerField(source="incidents.count", read_only=True)

    class Meta:
        model = Artifact
        fields = ("id", "type", "value", "incidents_count")
        read_only_fields = ("id", "type", "value", "incidents_count")


class FileSerializer(serializers.ModelSerializer):
    incident = serializers.HyperlinkedRelatedField(
        read_only=True, view_name="api:incidents-detail"
    )
    url = serializers.HyperlinkedIdentityField(view_name="api:files-detail")

    class Meta:
        model = File
        fields = ["id", "description", "url", "incident"]
        read_only_fields = ["id"]


class FileViewSet(
    DestroyModelMixin, ListModelMixin, RetrieveModelMixin, viewsets.GenericViewSet
):
    """
    API endpoint for listing files.
    Files can be uploaded and downloaded via endpoints /files/<incidentID>/upload , /files/<fileID>/download and /files/<incidentID>/download-all
    """

    serializer_class = FileSerializer
    permission_classes = [IsAuthenticated, CanViewIncident | CanWriteIncident]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = ["id", "date", "incident"]
    filterset_class = FileFilter

    def get_queryset(self):
        incidents_allowed = Incident.authorization.for_user(
            self.request.user, "incidents.view_incidents"
        )
        queryset = File.objects.filter(incident__in=incidents_allowed).order_by(
            "id", "date"
        )
        return queryset

    @action(detail=True)
    def download(self, request, pk):
        file_object = get_object_or_404(File, pk=pk)
        self.check_object_permissions(self.request, file_object.incident)
        return do_download(request, pk)

    @action(detail=True, url_path="download-all")
    def download_all(self, request, pk):
        inc = get_object_or_404(Incident, pk=pk)
        self.check_object_permissions(self.request, Incident.objects.get(pk=pk))
        if inc.file_set.count() == 0:
            return Response(
                data={"Error": "Incident does not have any file."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return do_download_archive(request, pk)

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


class ArtifactViewSet(ListModelMixin, RetrieveModelMixin, viewsets.GenericViewSet):
    """
    API endpoint to list artifacts.
    Artifacts can't be created or edited via the API, they are automatically generated from incident descriptions and comments.
    You can detach an artifact from an incident by accessing /artifacts/<id>/detach/<incidentID>
    """

    serializer_class = ArtifactSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = ["id", "type", "value"]
    filterset_class = ArtifactFilter

    def get_queryset(self):
        incidents_allowed = Incident.authorization.for_user(
            self.request.user, "incidents.view_incidents"
        )
        queryset = (
            Artifact.objects.filter(incidents__in=incidents_allowed)
            .distinct()
            .order_by("id")
        )
        return queryset

    @action(detail=True, methods=["POST"], url_path=r"detach/(?P<incident_id>\d+)")
    def detach(self, request, pk, incident_id):
        artifact = get_object_or_404(Artifact, pk=pk)

        try:
            related = artifact.incidents.get(pk=incident_id)
        except Incident.DoesNotExist:
            return Response(
                data={"detail": "Unknown related object"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not request.user.has_perm("incidents.handle_incidents", obj=related):
            raise PermissionDenied()

        artifact.relations.remove(related)
        if artifact.relations.count() == 0:
            artifact.delete()

        return Response({"detail": "Artifact detached"})
