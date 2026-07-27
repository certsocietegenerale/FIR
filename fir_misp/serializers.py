from rest_framework import serializers
from incidents.models import Incident
from fir_artifacts.models import Artifact


class ObservableTagSerializer(serializers.Serializer):
    value = serializers.CharField()
    tags = serializers.ListField(child=serializers.CharField())


class MISPEventSerializer(serializers.Serializer):
    value = serializers.IntegerField()


class MISPSerializer(serializers.Serializer):
    observables = ObservableTagSerializer(many=True)
    misp_events = MISPEventSerializer(many=True, allow_empty=True)
    fir_incident_id = serializers.PrimaryKeyRelatedField(
        queryset=Incident.objects.all(), allow_null=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        user = self.context.get("request").user
        action = self.context.get("view").action
        if action == "list":
            self.fields["fir_incident_id"].required = False
            self.fields["fir_incident_id"].queryset = Incident.authorization.for_user(
                user, "incidents.view_incidents"
            )
        else:
            self.fields["fir_incident_id"].required = True
            self.fields["fir_incident_id"].allow_null = False
            self.fields["fir_incident_id"].queryset = Incident.authorization.for_user(
                user, "incidents.handle_incidents"
            )

    def validate(self, data):
        # We verify that the given observables are related to the given incident, or related to an incident the user can view
        incident = data.get("fir_incident_id", None)
        observables = data.get("observables", [])
        user = self.context.get("request").user
        action = self.context.get("view").action
        allowed_incidents = Incident.authorization.for_user(
            user, "incidents.view_incidents"
        )

        for item in observables:
            if incident:
                observable_exists = Artifact.objects.filter(
                    value=item["value"], incidents=incident
                ).exists()
            else:
                observable_exists = (
                    Artifact.objects.filter(incidents__in=allowed_incidents)
                    .filter(value=item["value"])
                    .exists()
                )

            if not observable_exists:
                raise serializers.ValidationError(
                    f"The artifact '{item['value']}' doesn't exist or is not related to the given incident."
                )

        return data
