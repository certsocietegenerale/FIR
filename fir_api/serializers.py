from django.contrib.auth.models import User
from rest_framework import serializers

from incidents.models import Incident, Artifact


# serializes data from the FIR User model
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'url', 'username', 'email', 'groups')
        read_only_fields = ('id')
        extra_kwargs = {'url': {'view_name': 'api:user-detail'}}


# FIR Incident model
class IncidentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Incident
        fields = ('id', 'date', 'is_starred', 'subject', 'description', 'concerned_business_lines', 'main_business_lines', 'severity', 'category', 'detection', 'opened_by', 'is_incident', 'status')
        read_only_fields = ('id', 'opened_by', 'main_business_lines')


# FIR Artifact model
class ArtifactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Artifact
        fields = ('id', 'type', 'value', 'incidents')
        read_only_fields = ('id')
