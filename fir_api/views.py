# for token Generation
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.authtoken.models import Token
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework import viewsets

from fir_api.serializers import UserSerializer, IncidentSerializer, ArtifactSerializer
from fir_api.permissions import IsIncidentHandler
from incidents.models import Incident, Artifact, Comments


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated, IsAdminUser)


class IncidentViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows creation of, viewing, and closing of incidents
    """
    queryset = Incident.objects.all()
    serializer_class = IncidentSerializer
    permission_classes = (IsAuthenticated, IsIncidentHandler)

    def perform_create(self, serializer):
        instance = serializer.save(opened_by=self.request.user)
        instance.refresh_main_business_lines()
        instance.done_creating()

    def perform_update(self, serializer):
        Comments.create_diff_comment(self.get_object(), serializer.validated_data, self.request.user)
        instance = serializer.save()
        instance.refresh_main_business_lines()


class ArtifactViewSet(ListModelMixin, RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = Artifact.objects.all()
    serializer_class = ArtifactSerializer
    lookup_field = 'value'
    lookup_value_regex = '.+'
    permission_classes = (IsAuthenticated, IsIncidentHandler)


# Token Generation ===========================================================

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)
