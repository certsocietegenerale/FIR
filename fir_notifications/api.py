import json
import ast
from rest_framework.filters import OrderingFilter
from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.validators import UniqueTogetherValidator
from django_filters.rest_framework import FilterSet, DjangoFilterBackend, CharFilter

from fir_api.permissions import CanViewIncident, CanWriteIncident
from fir_api.serializers import BusinessLineSlugField
from fir_api.filters import BLChoiceFilter
from fir_notifications.registry import registry
from fir_notifications.models import NotificationPreference, MethodConfiguration
from incidents.models import BusinessLine


class MethodConfigurationFilter(FilterSet):
    """
    filter class for user-specific settings for a specific notification method
    """

    class Meta:
        model = MethodConfiguration
        fields = ["method"]


class NotificationPreferenceFilter(FilterSet):
    """
    filter class for user notification preferences
    """

    business_lines = BLChoiceFilter(
        to_field_name="name",
        field_name="business_lines__name",
        queryset=BusinessLine.objects.all(),
    )

    class Meta:
        model = NotificationPreference
        fields = ["event", "method", "business_lines"]


class JSONCharField(serializers.Field):
    def to_representation(self, value):
        if isinstance(value, str):
            try:
                return json.loads(value)
            except ValueError:
                return value
        return value

    def to_internal_value(self, data):
        if isinstance(data, dict):
            return json.dumps(data)
        elif isinstance(data, str):
            # Try JSON first
            try:
                return json.dumps(json.loads(data))
            except ValueError:
                pass

            # Fallback: Python dict literal (Browsable API)
            try:
                parsed = ast.literal_eval(data)
                if isinstance(parsed, dict):
                    return json.dumps(parsed)
            except (ValueError, SyntaxError):
                pass
        raise serializers.ValidationError("Invalid JSON value")


class MethodConfigurationSerializer(serializers.ModelSerializer):
    """
    Serializer for /api/notifications_method_configuration
    """

    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    value = JSONCharField()

    class Meta:
        model = MethodConfiguration
        fields = ["method", "value", "user"]


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """
    Serializer for /api/notifications_preferences
    """

    business_lines = BusinessLineSlugField(
        many=True,
        slug_field="name",
        queryset=BusinessLine.objects.all(),
        required=False,
    )

    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = NotificationPreference
        fields = ["user", "event", "method", "business_lines"]


class MethodConfigurationViewSet(viewsets.ModelViewSet):
    serializer_class = MethodConfigurationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = ["method"]
    filterset_class = MethodConfigurationFilter
    lookup_field = "method"
    lookup_value_regex = "[^/]+"

    def get_queryset(self):
        queryset = MethodConfiguration.objects.filter(
            user=self.request.user,
        ).distinct()

        return queryset


class NotificationPreferenceViewSet(viewsets.ModelViewSet):
    """
    API endpoint to manage User notification's preferences
    """

    serializer_class = NotificationPreferenceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = ["event", "method", "business_lines"]
    filterset_class = NotificationPreferenceFilter
    lookup_field = "event"
    lookup_value_regex = "[^/]+"

    def get_queryset(self):
        allowed_bls = BusinessLine.authorization.for_user(
            self.request.user, "incidents.view_incidents"
        )
        queryset = NotificationPreference.objects.filter(
            user=self.request.user,
            method__in=registry.methods.keys(),
            business_lines__in=allowed_bls,
        ).distinct()

        return queryset
