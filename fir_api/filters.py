import importlib
from django.apps import apps
from rest_framework.exceptions import ParseError
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.db.models import Q
from django.apps import apps
from django_filters.rest_framework import (
    FilterSet,
    DateTimeFilter,
    CharFilter,
    NumberFilter,
    MultipleChoiceFilter,
    BooleanFilter,
    ModelChoiceFilter,
    ModelMultipleChoiceFilter,
    ChoiceFilter,
)

from incidents.models import (
    Incident,
    Label,
    IncidentCategory,
    ValidAttribute,
    Comments,
    File,
    STATUS_CHOICES,
    CONFIDENTIALITY_LEVEL,
)
from fir_artifacts.models import File, Artifact
from fir_api.lexer import SearchParser
from fir.config.base import INSTALLED_APPS


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


class ValueChoiceFilter(ChoiceFilter):
    def __init__(self, choices, **kwargs):
        self._choices = choices
        super(ValueChoiceFilter, self).__init__(choices=choices, **kwargs)

    def filter(self, qs, value):
        for choice in self._choices:
            if choice[1] == value:
                return super().filter(qs, choice[0])
        return qs

    @property
    def field(self):
        fields = super().field
        fields.choices = [(b[1], b[1]) for b in self._choices]
        return fields


class IncidentFilter(FilterSet):
    """
    A custom filter class for Incidents filtering
    """

    id = NumberFilter(field_name="id")
    severity = NumberFilter(field_name="severity")
    created_before = DateTimeFilter(field_name="date", lookup_expr="lte")
    created_after = DateTimeFilter(field_name="date", lookup_expr="gte")
    subject = CharFilter(field_name="subject", lookup_expr="icontains")
    description = CharFilter(field_name="description", lookup_expr="icontains")
    status = ValueChoiceFilter(field_name="status", choices=STATUS_CHOICES)
    status__not = ValueChoiceFilter(
        field_name="status",
        choices=STATUS_CHOICES,
        exclude=True,
        label=_("Status is not"),
    )
    confidentiality = ValueChoiceFilter(
        field_name="confidentiality", choices=CONFIDENTIALITY_LEVEL
    )
    is_starred = BooleanFilter(field_name="is_starred")
    concerned_business_lines = AllValuesMultipleFilterAllAllowed(
        field_name="concerned_business_lines__name", lookup_expr="icontains"
    )
    category = ModelChoiceFilter(
        to_field_name="name",
        field_name="category__name",
        queryset=IncidentCategory.objects.all(),
    )
    detection = ModelChoiceFilter(
        field_name="detection__name",
        to_field_name="name",
        queryset=Label.objects.filter(group__name="detection"),
    )
    is_incident = BooleanFilter(field_name="is_incident")
    is_major = BooleanFilter(field_name="is_major")
    last_comment_date_before = DateTimeFilter(
        field_name="last_comment_date",
        lookup_expr="lte",
        label=_("Last comment date is less than or equal to"),
    )
    last_comment_date_after = DateTimeFilter(
        field_name="last_comment_date",
        lookup_expr="gte",
        label=_("Last comment date is greater than or equal to"),
    )
    query = CharFilter(
        method="search_query", label=_("Custom search query (DSL syntax)")
    )
    attribute = ModelMultipleChoiceFilter(
        to_field_name="name",
        field_name="attribute__name",
        queryset=ValidAttribute.objects.all(),
        label=_("Has attribute"),
    )
    search_filters = []
    keyword_filters = {}

    def search_query(self, queryset, name, search_query):
        # Build possible fields list
        possible_fields = {}
        for field in queryset.model._meta.fields:
            if str(field.get_internal_type()) in [
                "CharField",
                "TextField",
            ]:
                possible_fields[field.name.lower()] = field.name.lower() + "__icontains"

        # Define custom mapping for specific fields
        possible_fields.update(
            {
                "bl": "concerned_business_lines__in",
                "plan": "plan__name",
                "id": lambda x: Q(
                    id=(
                        x.removesuffix(settings.INCIDENT_ID_PREFIX)
                        if settings.INCIDENT_SHOW_ID
                        else x
                    )
                ),
                "starred": lambda x: Q(
                    is_starred=True if x.lower() in ["true", 1, "yes", "y"] else False
                ),
                "opened_by": "opened_by__username",
                "category": "category__name__icontains",
                "status": "status",
                "severity": "severity__name",
            }
        )
        # Custom fields added by plugins
        possible_fields.update(self.keyword_filters)

        # Text entered without "field:"
        # Searching in subject description and comments by default
        default_fields = [
            lambda x: Q(subject__icontains=x)
            | Q(description__icontains=x)
            | Q(comments__comment__icontains=x)
        ]
        # default field added by plugins
        default_fields.extend(self.search_filters)

        try:
            lexer = SearchParser(possible_fields, default_fields, search_query)
            q = lexer.get_q()
        except Exception as e:
            raise ParseError(_(f"Query DSL is not valid: %s" % e))
        return queryset.filter(q)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Load Additional incident filters defined in plugins via a hook
        for app in INSTALLED_APPS:
            if app.startswith("fir_"):
                try:
                    h = importlib.import_module(f"{app}.hooks")
                except ImportError:
                    continue

                fields = h.hooks.get("incident_fields", [])
                if isinstance(fields, list):
                    for field in fields:
                        if isinstance(field[3], dict):
                            for k, v in field[3].items():
                                self.filters.update({k: v})
                fields = h.hooks.get("search_filter", [])
                if isinstance(fields, list):
                    self.search_filters.extend(fields)

                fields = h.hooks.get("keyword_filter", {})
                if isinstance(fields, dict):
                    self.keyword_filters.update(fields)

    class Meta:
        model = Incident
        fields = [
            "id",
            "subject",
            "description",
            "status",
            "concerned_business_lines",
            "severity",
            "category",
            "detection",
            "query",
            "attribute",
        ]


class ArtifactFilter(FilterSet):
    """
    A custom filter class for artifacts filtering
    """

    id = NumberFilter(field_name="id")
    type = CharFilter(field_name="type")
    value = CharFilter(field_name="value", lookup_expr="icontains")
    incidents = NumberFilter(field_name="incidents__id")

    class Meta:
        model = Artifact
        fields = ["id", "type", "incidents", "value"]


class LabelFilter(FilterSet):
    """
    A custom filter class for Label filtering
    """

    id = NumberFilter(field_name="id")
    name = CharFilter(field_name="name")

    class Meta:
        model = Label
        fields = ["id", "name", "group"]


class ValidAttributeFilter(FilterSet):
    id = NumberFilter(field_name="id")
    name = CharFilter(field_name="name")
    unit = NumberFilter(field_name="unit")
    description = CharFilter(field_name="description")
    categories = ModelChoiceFilter(
        to_field_name="name",
        field_name="categories__name",
        queryset=IncidentCategory.objects.all(),
    )


class IncidentCategoriesFilter(FilterSet):
    """
    Custom filtering for incidents categories
    """

    id = NumberFilter(field_name="id")
    name = CharFilter(field_name="name")
    is_major = BooleanFilter(field_name="is_major")


class AttributeFilter(FilterSet):
    id = NumberFilter(field_name="id")
    name = CharFilter(field_name="name")
    value = CharFilter(field_name="value", lookup_expr="icontains")
    incident = NumberFilter(field_name="incident")


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
    name = CharFilter(field_name="name", lookup_expr="icontains", method="filter_name")

    def filter_name(self, queryset, name, value):
        """
        And custom handling that we do return children
        of the searched name
        """
        split_values = []
        if " > " in value:
            split_values = value.split(" > ")
            lookup = {name + "__icontains": split_values[-1]}
        else:
            lookup = {name + "__icontains": value}
        filtered_queryset = queryset.filter(**lookup)
        if split_values:
            for node in filtered_queryset:
                ancestors = node.get_ancestors()
                for value in split_values[:-1]:
                    if not ancestors.filter(name=value):
                        filtered_queryset = filtered_queryset.exclude(pk=node.pk)
                        break
        for node in filtered_queryset:
            if node.numchild > 0:
                filtered_queryset = filtered_queryset.union(node.get_descendants())
        return filtered_queryset


class CommentFilter(FilterSet):
    """
    A custom filter class for Comment filtering
    """

    id = NumberFilter(field_name="id")
    created_before = DateTimeFilter(field_name="date", lookup_expr="lte")
    created_after = DateTimeFilter(field_name="date", lookup_expr="gte")
    opened_by = CharFilter(field_name="opened_by__username")
    action = ModelChoiceFilter(
        to_field_name="name",
        field_name="action__name",
        queryset=Label.objects.filter(group__name="action"),
    )
    incident = NumberFilter(field_name="incident__id")

    class Meta:
        model = Comments
        fields = ["id", "date", "incident", "opened_by", "action"]


class StatsFilter(IncidentFilter):
    last_comment_date_before = None
    last_comment_date_after = None

    aggregation = CharFilter(
        method="aggregate_by", label=_("Aggregate by"), required=True
    )

    def aggregate_by(self, queryset, name, aggregate_by):
        valid_aggregations = [
            "category",
            "severity",
            "entity",
            "detection",
            "actor",
            "date",
        ]

        for elem in aggregate_by.split(","):
            if elem not in valid_aggregations:
                raise ParseError(_(f"'{elem}' is not part of {valid_aggregations}"))

        return queryset

    class Meta:
        model = Incident
        fields = [
            "id",
            "subject",
            "description",
            "status",
            "concerned_business_lines",
            "severity",
            "category",
            "detection",
            "query",
            "aggregation",
        ]
