from django.db.models import Q
from django_filters.rest_framework import CharFilter

from fir_artifacts.api import FileSerializer, IncidentArtifactSerializer

hooks = {
    "incident_fields": [
        (
            "artifact_set",  # name of the new field
            None,  # Django ModelForm.
            IncidentArtifactSerializer(many=True, read_only=True),  # Serializer
            {"artifact": CharFilter(field_name="artifact_set__value")},  # Filters
        ),
        (
            "file_set",
            None,
            FileSerializer(many=True, read_only=True),
            None,
        ),
    ],
    "keyword_filter": {"artifact": lambda x: Q(artifact_set__value__iexact=x)},
}
