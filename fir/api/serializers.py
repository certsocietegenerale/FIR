from django.contrib.auth.models import User, Group
from django.http import HttpResponse
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from rest_framework import viewsets
from rest_framework import serializers

from incidents.models import Incident


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
class IncidentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Incident
        fields = ('date', 'is_starred', 'subject', 'description', 'severity', 'category', 'detection', 'opened_by', 'is_incident')

        def incident_list(request):
            """
            List all incidents, or create a new incident.
            """
            if request.method == 'GET':
                incidents = Incident.objects.all()
                serializer = IncidentSerializer(incidents, many=True)
                return JSONResponse(serializer.data)

            elif request.method == 'POST':
                data = JSONParser().parse(request)
                serializer = IncidentSerializer(data=request)
                if serializer.is_valid():
                    serializer.save()
                    return JSONResponse(serializer.data, status=201)
                return JSONResponse(serializer.errors, status=400)
