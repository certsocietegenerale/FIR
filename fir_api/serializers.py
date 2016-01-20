from django.contrib.auth.models import User, Group
from rest_framework import serializers

from incidents.models import Incident, Artifact


# serializes data from the User model
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'url', 'username', 'email', 'groups')

# User Group model
class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ('id', 'url', 'name')


# FIR Incident model
class IncidentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Incident
        fields = ('id', 'date', 'is_starred', 'subject', 'description', 'main_business_lines', 'severity', 'category', 'detection', 'opened_by', 'is_incident', 'status')

# FIR Artifact model
class ArtifactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Artifact
        fields = ('id', 'type', 'value', 'incidents')
