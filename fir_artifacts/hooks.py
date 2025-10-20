from django.db.models import Q
from django_filters.rest_framework import CharFilter

from fir_artifacts.api import FileSerializer, IncidentArtifactSerializer

hooks = {
    "incident_fields": [
        (
            "artifacts",  # name of the new field
            None,  # Django ModelForm.
            IncidentArtifactSerializer(many=True, read_only=True),  # Serializer
            {"artifact": CharFilter(field_name="artifacts__value")},  # Filters
        ),
        (
            "file_set",
            None,
            FileSerializer(many=True, read_only=True),
            None,
        ),
    ],
    "keyword_filter": {"artifact": lambda x: Q(artifacts__value__iexact=x)},
}
