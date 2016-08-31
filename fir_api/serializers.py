from django.contrib.auth.models import User
from rest_framework import serializers

from incidents.models import Incident, Artifact, Label, File, IncidentCategory, BusinessLine


# serializes data from the FIR User model
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'url', 'username', 'email', 'groups')
        read_only_fields = ('id',)
        extra_kwargs = {'url': {'view_name': 'api:user-detail'}}


# FIR Artifact model
class ArtifactSerializer(serializers.ModelSerializer):
    incidents = serializers.HyperlinkedRelatedField(many=True, read_only=True, view_name='api:incident-detail')

    class Meta:
        model = Artifact
        fields = ('id', 'type', 'value', 'incidents')
        read_only_fields = ('id',)


# FIR File model

class AttachedFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = ('id', 'description', 'url')
        read_only_fields = ('id',)
        extra_kwargs = {'url': {'view_name': 'api:file-detail'}}


class FileSerializer(serializers.ModelSerializer):
    incident = serializers.HyperlinkedRelatedField(read_only=True, view_name='api:incident-detail')

    class Meta:
        model = File
        fields = ('id', 'description', 'incident', 'url', 'file')
        read_only_fields = ('id',)
        extra_kwargs = {'url': {'view_name': 'api:file-download'}}
        depth = 2


# FIR Incident model

class IncidentSerializer(serializers.ModelSerializer):
    detection = serializers.PrimaryKeyRelatedField(queryset=Label.objects.filter(group__name='detection'))
    actor = serializers.PrimaryKeyRelatedField(queryset=Label.objects.filter(group__name='actor'))
    plan = serializers.PrimaryKeyRelatedField(queryset=Label.objects.filter(group__name='plan'))
    file_set = AttachedFileSerializer(many=True, read_only=True)

    class Meta:
        model = Incident
        exclude = ['main_business_lines', 'artifacts']
        read_only_fields = ('id', 'opened_by', 'main_business_lines', 'file_set')
