from django.contrib.auth.models import User, Group
from django.http import HttpResponse
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from rest_framework import viewsets
from rest_framework import serializers

from incidents.models import Incident, Artifact


# serializes data from the FIR User model
class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'username', 'email', 'groups')

# User Group model
class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ('url', 'name')


# FIR Incident model
class IncidentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Incident
        fields = ('date', 'is_starred', 'subject', 'description', 'main_business_lines', 'severity', 'category', 'detection', 'opened_by', 'is_incident', 'status')

# FIR Artifact model
class ArtifactSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Artifact
        fields = ('type', 'value', 'incidents')
