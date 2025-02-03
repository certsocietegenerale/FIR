from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import (
    DjangoFilterBackend,
    FilterSet,
    DateTimeFilter,
    CharFilter,
    NumberFilter,
)

from fir_api.permissions import IsIncidentHandler
from fir_nuggets.models import Nugget
from incidents.models import Incident


class NuggetFilter(FilterSet):
    """
    A custom filter class for nuggets items
    """

    id = NumberFilter(field_name="id")
    start_timestamp_before = DateTimeFilter(
        field_name="start_timestamp", lookup_expr="lte"
    )
    start_timestamp_after = DateTimeFilter(
        field_name="start_timestamp", lookup_expr="gte"
    )
    end_timestamp_before = DateTimeFilter(field_name="end_timestamp", lookup_expr="lte")
    end_timestamp_after = DateTimeFilter(field_name="end_timestamp", lookup_expr="lte")
    incident = NumberFilter(field_name="incident__id")
    interpretation = CharFilter(field_name="interpretation", lookup_expr="icontains")
    source = CharFilter(field_name="source", lookup_expr="icontains")
    raw_data = CharFilter(field_name="raw_data", lookup_expr="icontains")


class NuggetSerializer(serializers.ModelSerializer):

    found_by = serializers.SlugRelatedField(
        many=False, read_only=True, slug_field="username"
    )

    class Meta:
        model = Nugget
        fields = (
            "id",
            "raw_data",
            "source",
            "start_timestamp",
            "end_timestamp",
            "interpretation",
            "incident",
            "found_by",
        )
        read_only_fields = ("id", "found_by")


class NuggetViewSet(viewsets.ModelViewSet):
    """
    API endpoints for listing, creating or editing Nuggets
    """

    queryset = Nugget.objects.all()
    serializer_class = NuggetSerializer
    permission_classes = (IsAuthenticated, IsIncidentHandler)
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = [
        "id",
        "source",
        "start_timestamp",
        "end_timestamp",
        "interpretation",
        "incident",
    ]
    filterset_class = NuggetFilter

    def get_queryset(self):
        incidents_allowed = Incident.authorization.for_user(
            self.request.user, "incidents.view_incidents"
        )
        queryset = Nugget.objects.filter(incident__in=incidents_allowed).order_by("-id")
        return queryset

    def perform_create(self, serializer):
        incident_object_id = self.request.data.get("incident")
        incident_object = Incident.objects.get(pk=incident_object_id)
        self.check_object_permissions(self.request, incident_object)
        instance = serializer.save(found_by=self.request.user)
        incident_object.refresh_artifacts(instance.raw_data)

    def perform_update(self, serializer):
        self.check_object_permissions(self.request, serializer.instance.incident)
        instance = serializer.save()
        e = get_object_or_404(
            Incident.authorization.for_user(
                self.request.user, "incidents.handle_incidents"
            ),
            pk=instance.incident_id,
        )
        e.refresh_artifacts(instance.raw_data)

    def perform_destroy(self, instance):
        self.check_object_permissions(self.request, instance.incident)

    def perform_destroy(self, instance):
        self.check_object_permissions(self.request, instance.incident)
        return super().perform_destroy(instance)
