from rest_framework import serializers, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import (
    DjangoFilterBackend,
    FilterSet,
    DateTimeFilter,
    CharFilter,
    NumberFilter,
    BooleanFilter,
)

from fir_api.permissions import IsIncidentHandler
from fir_todos.models import TodoItem
from incidents.models import BusinessLine, Incident


class TodoFilter(FilterSet):
    """
    A custom filter class for Todo items
    """

    id = NumberFilter(field_name="id")
    incident = NumberFilter(field_name="incident__id")
    category = CharFilter(field_name="category__name")
    business_line = CharFilter(field_name="business_line__name")
    deadline = DateTimeFilter(field_name="deadline")
    done_time_before = DateTimeFilter(field_name="done_time", lookup_expr="lte")
    done_time_after = DateTimeFilter(field_name="done_time", lookup_expr="gte")
    done = BooleanFilter(field_name="done")


class TodoSerializer(serializers.ModelSerializer):
    """
    Serializer for Todo items
    """

    category = serializers.SlugRelatedField(
        many=False, read_only=True, slug_field="name"
    )
    business_line = serializers.SlugRelatedField(
        slug_field="name",
        queryset=BusinessLine.objects.all(),
        required=False,
        default=None,
    )

    class Meta:
        model = TodoItem
        fields = [
            "id",
            "description",
            "incident",
            "category",
            "business_line",
            "done",
            "done_time",
        ]
        read_only_fields = ["id"]


class TodoViewSet(viewsets.ModelViewSet):
    """
    API endpoints for listing, creating or editing Todo items
    """

    queryset = TodoItem.objects.all()
    serializer_class = TodoSerializer
    permission_classes = (IsAuthenticated, IsIncidentHandler)
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = ["id", "incident", "done_time"]
    filterset_class = TodoFilter

    def get_queryset(self):
        incidents_allowed = Incident.authorization.for_user(
            self.request.user, "incidents.view_incidents"
        )
        queryset = TodoItem.objects.filter(incident__in=incidents_allowed).order_by("-id")
        return queryset

    def perform_create(self, serializer):
        business_line = BusinessLine.objects.get(
            name=self.request.data.get("business_line")
        )
        if business_line:
            allowed_businesslines = BusinessLine.authorization.for_user(
                self.request.user, "incidents.handle_incidents"
            )
            if business_line not in allowed_businesslines:
                return Response(
                    data={"Error": "Chosen businessline not allowed for user"},
                    status=status.HTTP_403_FORBIDDEN,
                )
        else:
            request_business_line = None
        incident_object_id = self.request.data.get("incident")
        incident_object = Incident.objects.get(pk=incident_object_id)
        self.check_object_permissions(self.request, incident_object)
        category = incident_object.category
        serializer.save(category=category, business_line=business_line),

    def perform_update(self, serializer):
        self.check_object_permissions(self.request, serializer.instance.incident)
        business_line = BusinessLine.objects.get(
            name=self.request.data.get("business_line")
        )
        if business_line:
            allowed_businesslines = BusinessLine.authorization.for_user(
                self.request.user, "incidents.handle_incidents"
            )
            if business_line not in allowed_businesslines:
                return Response(
                    {"error": "Chosen businessline not allowed for user"},
                    status=401,
                )
        incident_object_id = self.request.data.get("incident")
        incident_object = Incident.objects.get(pk=incident_object_id)
        self.check_object_permissions(self.request, incident_object)
        category = incident_object.category
        serializer.save(category=category, business_line=business_line)

    def perform_destroy(self, instance):
        self.check_object_permissions(self.request, instance.incident)
        return super().perform_destroy(instance)
