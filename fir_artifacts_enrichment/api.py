from django.http import Http404
from django.urls import reverse
from rest_framework import serializers, viewsets, mixins
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import action
from rest_framework.response import Response

from fir_artifacts.models import Artifact
from fir_artifacts_enrichment.models import ArtifactEnrichment
from fir_artifacts_enrichment.tasks import enrich_artifact
from fir_api.permissions import CanViewIncident, CanWriteIncident
from incidents.models import Incident


class ArtifactsEnrichmentSerializer(serializers.ModelSerializer):
    """
    Serializer for /api/artifacts_enrichment
    """

    value = serializers.CharField(source="artifact.value", read_only=True)

    class Meta:
        model = ArtifactEnrichment
        fields = ["email", "name", "value", "raw"]
        read_only_fields = ["email", "name", "value", "raw"]


class ArtifactsEnrichmentViewSet(
    viewsets.GenericViewSet,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
):
    """
    List, retrieve and get status of artifacts enrichment
    """

    serializer_class = ArtifactsEnrichmentSerializer
    permission_classes = [IsAuthenticated]
    lookup_value_regex = r".+"

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def get_queryset(self):
        incidents_allowed = Incident.authorization.for_user(
            self.request.user, "incidents.view_incidents"
        )
        queryset = (
            ArtifactEnrichment.objects.filter(artifact__incidents__in=incidents_allowed)
            .distinct()
            .order_by("id")
        )
        return queryset

    def retrieve(self, request, *args, **kwargs):
        try:
            enrichment = self.get_queryset().get(artifact__value=self.kwargs.get("pk"))
            correlations = enrichment.artifact.relations_for_user(user=None).group()
            if all(
                [not link_type.objects.exists() for link_type in correlations.values()]
            ):
                raise PermissionDenied()
            serializer = self.get_serializer(enrichment)
            return Response(serializer.data)
        except ArtifactEnrichment.DoesNotExist:
            raise Http404()

    @action(detail=False, methods=["GET"], url_path=r"(?P<value>.+)/status")
    def status(self, request, value=None):
        try:
            artifact = Artifact.objects.get(value=value)
        except Artifact.DoesNotExist:
            data = {"state": "UNKNOWN"}
        else:
            try:
                enrichment = ArtifactEnrichment.objects.get(artifact=artifact)
                task = enrich_artifact.AsyncResult(str(enrichment.pk))
                data = {"state": task.state}
                if task.state == "PENDING":
                    # if an ArtifactEnrichment exist, then the task
                    # is a success, even if celery lost track of it
                    data = {"state": "SUCCESS"}
            except ArtifactEnrichment.DoesNotExist:
                data = {"state": "PENDING"}
        return Response(data)
