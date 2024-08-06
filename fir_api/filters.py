from django.apps import apps
from django_filters.rest_framework import (
    FilterSet,
    DateTimeFilter,
    CharFilter,
    NumberFilter,
    MultipleChoiceFilter,
    BooleanFilter,
    ModelChoiceFilter,
    ChoiceFilter,
)

from incidents.models import (
    Incident,
    Label,
    IncidentCategory,
    Comments,
    File,
    STATUS_CHOICES,
)
from fir_artifacts.models import File


class AllValuesMultipleFilterAllAllowed(MultipleChoiceFilter):

    @property
    def field(self):
        if "__" in self.field_name:
            field_name, field_attribute = tuple(self.field_name.split("__"))
            field_model = self.model._meta.get_field(field_name)
            choices = field_model.related_model.objects.all().values_list(
                field_attribute, flat=True
            )
            self.extra["choices"] = [(choice, choice) for choice in choices]
        else:
            self.extra["choices"] = self.model._meta.get_field(
                self.field_name
            ).get_choices()
        return super().field


class IncidentFilter(FilterSet):
    """
    A custom filter class for Incidents filtering
    """

    id = NumberFilter(field_name="id")
    severity = NumberFilter(field_name="severity")
    created_before = DateTimeFilter(field_name="date", lookup_expr="lte")
    created_after = DateTimeFilter(field_name="date", lookup_expr="gte")
    subject = CharFilter(field_name="subject", lookup_expr="icontains")
    status = ChoiceFilter(field_name="status", choices=STATUS_CHOICES)
    is_starred = BooleanFilter(field_name="is_starred")
    category = ModelChoiceFilter(
        field_name="category__name", queryset=IncidentCategory.objects.all()
    )
    detection = ModelChoiceFilter(
        field_name="detection__name",
        queryset=Label.objects.filter(group__name="detection"),
    )

    class Meta:
        model = Incident
        fields = [
            "id",
            "date",
            "subject",
            "status",
            "concerned_business_lines",
            "severity",
            "category",
            "detection",
        ]


class ArtifactFilter(FilterSet):
    """
    A custom filter class for artifacts filtering
    """

    id = NumberFilter(field_name="id")
    type = CharFilter(field_name="type")
    incident = AllValuesMultipleFilterAllAllowed(field_name="incidents")


class LabelFilter(FilterSet):
    """
    A custom filter class for Label filtering
    """

    id = NumberFilter(field_name="id")
    name = CharFilter(field_name="name")

    class Meta:
        model = Label
        fields = ["id", "name", "group"]


class AttributeFilter(FilterSet):
    id = NumberFilter(field_name="id")
    name = CharFilter(field_name="name")
    value = CharFilter(field_name="value", lookup_expr="icontains")
    incident = NumberFilter(field_name="incident")


class ValidAttributeFilter(FilterSet):
    id = NumberFilter(field_name="id")
    name = CharFilter(field_name="name")
    is_major = BooleanFilter(field_name="is_major")
    unit = NumberFilter(field_name="unit")
    description = CharFilter(field_name="description")
    categories = ModelChoiceFilter(
        field_name="category__name", queryset=IncidentCategory.objects.all()
    )


class IncidentCategoriesFilter(FilterSet):
    """
    Custom filtering for incidents categories
    """

    id = NumberFilter(field_name="id")
    name = CharFilter(field_name="name")
    is_major = BooleanFilter(field_name="is_major")


class FileFilter(FilterSet):
    """
    Custom filtering so we can partially match on name
    """

    id = NumberFilter(field_name="id")
    description = CharFilter(field_name="description", lookup_expr="icontains")
    uploaded_before = DateTimeFilter(field_name="date", lookup_expr="lte")
    uploaded_after = DateTimeFilter(field_name="date", lookup_expr="gte")
    incident = NumberFilter(field_name="incident__id")

    class Meta:
        model = File
        fields = ["id", "description", "incident"]


class BLFilter(FilterSet):
    """
    Custom filtering so we can partially match on name
    """

    id = NumberFilter(field_name="id")
    name = CharFilter(field_name="name", lookup_expr="icontains")


class CommentFilter(FilterSet):
    """
    A custom filter class for Comment filtering
    """

    id = NumberFilter(field_name="id")
    created_before = DateTimeFilter(field_name="date", lookup_expr="lte")
    created_after = DateTimeFilter(field_name="date", lookup_expr="gte")
    opened_by = CharFilter(field_name="opened_by__username")
    action = ModelChoiceFilter(
        field_name="action__name",
        queryset=Label.objects.filter(group__name="action"),
    )
    incident = NumberFilter(field_name="incident__id")

    class Meta:
        model = Comments
        fields = ["id", "date", "incident", "opened_by", "action"]


if apps.is_installed("fir_todos"):
    from fir_todos.models import TodoItem

    class TodoFilter(FilterSet):
        """
        A custom filter class for Todo items
        """

        id = NumberFilter(field_name="id")
        incident = NumberFilter(field_name="incident__id")
        done_time_before = DateTimeFilter(field_name="done_time", lookup_expr="lte")
        done_time_after = DateTimeFilter(field_name="done_time", lookup_expr="gte")
        done = BooleanFilter(field_name="done")

        class Meta:
            model = TodoItem
            fields = ["id", "category", "done", "done_time", "incident"]


if apps.is_installed("fir_nuggets"):

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
        end_timestamp_before = DateTimeFilter(
            field_name="end_timestamp", lookup_expr="lte"
        )
        end_timestamp_after = DateTimeFilter(
            field_name="end_timestamp", lookup_expr="lte"
        )
        incident = NumberFilter(field_name="incident__id")
        interpretation = CharFilter(
            field_name="interpretation", lookup_expr="icontains"
        )
        source = CharFilter(field_name="source", lookup_expr="icontains")
        raw_data = CharFilter(field_name="raw_data", lookup_expr="icontains")
