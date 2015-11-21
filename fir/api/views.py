from django.contrib.auth.models import User, Group
from rest_framework import viewsets

from fir.api.serializers import UserSerializer, GroupSerializer, IncidentSerializer
from incidents.models import Incident


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer

class IncidentViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows creation of, viewing, and closing of incidents
    """
    queryset = Incident.objects.all()
    serializer_class = IncidentSerializer
