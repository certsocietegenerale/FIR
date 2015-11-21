from django.contrib.auth.models import User, Group
from incidents.models import Incident
from rest_framework import serializers

# serializes data from the FIR User model
class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'username', 'email', 'groups')

# FIR User Group model
class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ('url', 'name')


# Main FIR Incident model
class IncidentSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Incident
        fields = ('date', 'is_starred', 'subject', 'description', 'severity', 'opened_by', 'is_incident', 'is_major')


    def create(self, validated_data):
        """
        Create and return a new `Incident` instance, given the validated data.
        """
        return Incident.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """
        Update and return an existing `Incident` instance, given the validated data.
        """
        instance.title = validated_data.get('title', instance.title)
        instance.code = validated_data.get('code', instance.code)
        instance.linenos = validated_data.get('linenos', instance.linenos)
        instance.language = validated_data.get('language', instance.language)
        instance.style = validated_data.get('style', instance.style)
        instance.save()
        return instance

    def close(self, instance, validated_data):
        """
        Close and return an existing `Incident` instance
        """
        return Incident.objects.delete(instance)
    
