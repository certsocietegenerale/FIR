import importlib
from django.apps import apps
from rest_framework.exceptions import ParseError
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.db.models import Q, Subquery
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
    BusinessLine,
    ValidAttribute,
    Comments,
    File,
    SeverityChoice,
    IncidentStatus,
    CONFIDENTIALITY_LEVEL,
)
from fir_artifacts.models import File, Artifact
from fir_api.lexer import SearchParser
from fir.config.base import INSTALLED_APPS


class BLChoiceFilter(ModelMultipleChoiceFilter):
    def __init__(self, *args, **kwargs):
        kwargs["method"] = self.filter_bl
        super().__init__(*args, **kwargs)

    @staticmethod
    def get_incidents_q(bls):
        """
        Function to filter incidents based on businessLine
        Use a subquery for optimization
        """
        if not bls:
            return Q()

        ids = Subquery(
            Incident.objects.filter(concerned_business_lines__in=bls)
            .values("id")
            .distinct()
        )
        return Q(id__in=ids)

    def filter_bl(self, queryset, name, value):
        """
        Custom handling to also retrieve children BLs
        """
        bls = []
        for v in value:
            bls.append(v)
            bls.extend(v.get_descendants())
        if self.model == Incident:
            queryset = queryset.filter(self.get_incidents_q(bls))
        elif bls:
            filter_dict = {name + "__in": [b.name for b in bls]}
            queryset = queryset.filter(**filter_dict)
        return queryset


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
    severity = ModelMultipleChoiceFilter(
        to_field_name="name",
        field_name="severity__name",
        queryset=SeverityChoice.objects.all(),
    )
    created_before = DateTimeFilter(field_name="date", lookup_expr="lte")
    created_after = DateTimeFilter(field_name="date", lookup_expr="gte")
    subject = CharFilter(field_name="subject", lookup_expr="icontains")
    description = CharFilter(field_name="description", lookup_expr="icontains")
    status = ModelChoiceFilter(
        field_name="status__name",
        to_field_name="name",
        queryset=IncidentStatus.objects.all(),
    )
    status__not = ModelMultipleChoiceFilter(
        field_name="status__name",
        to_field_name="name",
        queryset=IncidentStatus.objects.all(),
        exclude=True,
        label=_("Status is not"),
    )
    confidentiality = ValueChoiceFilter(
        field_name="confidentiality", choices=CONFIDENTIALITY_LEVEL
    )
    is_starred = BooleanFilter(field_name="is_starred")
    concerned_business_lines = BLChoiceFilter(
        to_field_name="name",
        field_name="concerned_business_lines__name",
        queryset=BusinessLine.objects.all(),
    )
    category = ModelMultipleChoiceFilter(
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

    # BL search: search in selected BL and childrens
    @staticmethod
    def search_bl(x):
        bls = []
        for bl in BusinessLine.objects.filter(name__iexact=x):
            bls.append(bl)
            bls.extend(bl.get_descendants())
        q = BLChoiceFilter.get_incidents_q(bls)
        if not q:
            q = Q(concerned_business_lines__name__iexact=x)
        return q

    # Comment search: use a subquery for performance
    @staticmethod
    def comment_contains(x):
        comments = Subquery(
            Comments.objects.filter(
                comment__icontains=x,
            )
            .values("incident_id")
            .distinct()
        )
        return Q(id__in=comments)

    # Status search: handle translations
    @staticmethod
    def status_iexact(x):
        reverse_map = {
            _(obj.name).lower(): obj.name.lower()
            for obj in IncidentStatus.objects.all()
        }
        x = reverse_map.get(x.lower(), x)
        return Q(status__name__iexact=x)

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
                "bl": self.search_bl,
                "plan": "plan__name__iexact",
                "id": lambda x: Q(
                    id=(
                        x.lower().removeprefix(settings.INCIDENT_ID_PREFIX.lower())
                        if (
                            settings.INCIDENT_SHOW_ID
                            and x.lower()
                            .removeprefix(settings.INCIDENT_ID_PREFIX.lower())
                            .isnumeric()
                        )
                        else (x if x.isnumeric() else 0)
                    )
                ),
                "starred": lambda x: Q(
                    is_starred=True if x.lower() in ["true", 1, "yes", "y"] else False
                ),
                "opened_by": "opened_by__username__iexact",
                "category": "category__name__icontains",
                "status": self.status_iexact,
                "severity": "severity__name__iexact",
            }
        )
        # Custom fields added by plugins
        possible_fields.update(self.keyword_filters)

        # Text entered without "field:"
        # Searching in subject description and comments by default
        default_fields = [
            lambda x: Q(subject__icontains=x) | Q(description__icontains=x),
            self.comment_contains,
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
        # Reset search_filter to accommodate object reuse
        self.search_filters = []

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


class CategoryFilter(FilterSet):
    """
    Custom filtering for incidents categories
    """

    id = NumberFilter(field_name="id")
    name = CharFilter(field_name="name")
    is_major = BooleanFilter(field_name="is_major")


class SeverityFilter(FilterSet):
    """
    Custom filtering for incidents severities
    """

    name = CharFilter(field_name="name")
    color = CharFilter(field_name="color")


class StatusFilter(FilterSet):
    """
    Custom filtering for incidents statuses
    """

    name = CharFilter(field_name="name", lookup_expr="iequals")
    icon = CharFilter(field_name="icon", lookup_expr="iequals")
    flag = CharFilter(field_name="flag", lookup_expr="iequals")


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
    Custom filtering class for BL Filtering
    """

    id = NumberFilter(field_name="id")
    name = BLChoiceFilter(
        to_field_name="name",
        field_name="name",
        queryset=BusinessLine.objects.all(),
    )


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
