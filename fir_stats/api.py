from datetime import datetime, timedelta
from collections import defaultdict
from collections.abc import Mapping
from functools import cached_property

from django.utils.translation import gettext_lazy as _
from django.db.models import Count, OuterRef, Subquery, Func
from django.db.models.functions import (
    TruncMonth,
    TruncYear,
    TruncDay,
    TruncHour,
)

from rest_framework.serializers import (
    ModelSerializer,
    CharField,
    DateTimeField,
    IntegerField,
)
from rest_framework.exceptions import ParseError
from rest_framework.permissions import BasePermission
from rest_framework.renderers import JSONRenderer
from rest_framework.permissions import IsAuthenticated
from rest_framework.mixins import ListModelMixin
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework.utils.serializer_helpers import ReturnDict

from django_filters.rest_framework import (
    CharFilter,
    DjangoFilterBackend,
    MultipleChoiceFilter,
    ModelMultipleChoiceFilter,
)

from incidents.models import Incident, BusinessLine, Attribute
from fir_api.filters import IncidentFilter
from fir_api.renderers import FilterButtonBrowsableAPIRenderer
from fir_api.serializers import BaselCategoryField
from fir_stats.permissions import can_view_statistics


class CanViewStatistics(BasePermission):
    def has_permission(self, request, view):
        return can_view_statistics(request.user)


class StatsFilter(IncidentFilter):
    aggregation = CharFilter(method="aggregate_by", label=_("Aggregate by"))
    unit = CharFilter(method="set_unit", label=_("Perform stats on"))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for k in self.filters:
            # Disable distinct count for MultipleChoiceFilter
            if isinstance(
                self.filters[k], (ModelMultipleChoiceFilter, MultipleChoiceFilter)
            ):
                self.filters[k].distinct = False

    def set_unit(self, queryset, name, unit):
        valid_unit = ["attribute", "incident"]

        if unit not in valid_unit:
            raise ParseError(_(f"'{unit}' is not part of {valid_unit}"))

        return queryset

    def aggregate_by(self, queryset, name, aggregate_by):
        valid_aggregations = [
            "category",
            "severity",
            "entity",
            "detection",
            "actor",
            "date",
            "baselcategory",
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
            "unit",
            "aggregation",
        ]


class StatsSerializer(ModelSerializer):
    year = DateTimeField(required=False, format="%Y")
    month = DateTimeField(required=False, format="%Y-%m")
    day = DateTimeField(required=False, format="%Y-%m-%d")
    hour = DateTimeField(required=False, format="%Y-%m-%d %H:%M")
    count = IntegerField(required=False)
    category = CharField(required=False, source="category__name")
    severity = CharField(required=False, source="severity__name")
    actor = CharField(required=False, source="actor__name")
    detection = CharField(required=False, source="detection__name")
    baselcategory = BaselCategoryField(
        required=False,
        source="category__bale_subcategory__name",
        slug_field="name",
        read_only=True,
    )
    entity = CharField(required=False, source="concerned_business_lines__name")

    class Meta:
        model = Incident
        fields = [
            "year",
            "month",
            "day",
            "hour",
            "category",
            "severity",
            "actor",
            "detection",
            "entity",
            "baselcategory",
            "count",
        ]



class StatsViewSet(ListModelMixin, GenericViewSet):
    """
    API endpoint displaying counts based on aggregations.
    """

    serializer_class = StatsSerializer
    permission_classes = [IsAuthenticated, CanViewStatistics]
    filter_backends = [DjangoFilterBackend]
    filterset_class = StatsFilter
    pagination_class = None
    renderer_classes = [FilterButtonBrowsableAPIRenderer, JSONRenderer]

    def split_by_date(self, queryset, filterset, values):
        """
        Aggregate a queryset by time
        Eg: qs = qs.annotate(year=TruncYear("date")).annotate(count=Count("pk")).values("year", "count")
        """

        date_from = filterset.get("created_after", False) or datetime.min
        date_to = filterset.get("created_before", False) or datetime.now()

        date_diff = date_to - date_from

        if date_diff < timedelta(days=3):
            # Less than 3 days, use hours
            split_by_kwargs = {"hour": TruncHour("date")}
        elif date_diff < timedelta(days=31):
            # Between 3 days and 1 month, use days
            split_by_kwargs = {"day": TruncDay("date")}
        elif date_diff < timedelta(days=1825):
            # Between 10 months and 5 years, use months
            split_by_kwargs = {"month": TruncMonth("date")}
        else:
            # Otherwise, use years
            split_by_kwargs = {"year": TruncYear("date")}

        applied_aggregation = list(split_by_kwargs.keys())[0]
        values.append(applied_aggregation)

        queryset = queryset.annotate(**split_by_kwargs).values(*values)

        if not "count" in values:
            values.append("count")
            queryset = queryset.annotate(count=Count("pk")).values(*values)

        queryset = queryset.order_by(*[v for v in values if v != "count"])
        return queryset, values, applied_aggregation

    def split_by_foreignkey_name(self, fk, queryset, values):
        """
        Aggregate a queryset by foreign_key
        Eg: qs = qs.values("category__name").annotate(count=Count("pk")).values("category__name", "count")
        """
        values.append(f"{fk}__name")
        queryset = queryset.values(*values)

        if not "count" in values:
            values.append("count")
            queryset = queryset.annotate(count=Count("pk")).values(*values)

        queryset = queryset.order_by(*[v for v in values if v != "count"])
        return queryset, values

    def get_queryset(self, return_applied_aggregations=False):
        queryset = Incident.authorization.for_user(
            self.request.user, "incidents.view_statistics"
        )

        values = []
        aggregation = ""
        applied_aggregations = []

        filterset = StatsFilter(
            data=self.request.query_params, queryset=queryset, request=self.request
        )
        _ = filterset.is_valid()  # Used to calculate cleaned_data.

        if filterset.form.cleaned_data.get("unit", "") == "attribute":
            # If unit=attribute is set: count selected attributes
            attr_names = [
                n.name for n in filterset.form.cleaned_data.get("attribute", [])
            ]
            attr_subquery = Attribute.objects.filter(incident=OuterRef("id"))
            if attr_names:
                attr_subquery = attr_subquery.filter(name__in=attr_names)
            attr_subquery = Subquery(
                attr_subquery.annotate(
                    count=Func("value", function="Sum")
                ).values(  # Perform per-incident sum of all selected attributes
                    "count"
                )
            )
            values.append("count")
            queryset = (
                queryset.annotate(count=attr_subquery)
                .filter(count__isnull=False)
                .values(*values)
            )

            # Remove attribute filter as it was already applied
            self.request.query_params._mutable = True
            self.request.query_params.pop("attribute", None)
            self.request.query_params._mutable = False

        for agg in filterset.form.cleaned_data.get("aggregation", "").split(","):
            # Split the querySet depending on the requested GET parameter. Store the applied aggregations
            if agg == "date":
                queryset, values, applied_agg = self.split_by_date(
                    queryset, filterset.form.cleaned_data, values
                )
                applied_aggregations.append(applied_agg)
            elif agg in ["category", "severity", "actor", "detection"]:
                queryset, values = self.split_by_foreignkey_name(agg, queryset, values)
                applied_aggregations.append(agg)
            elif agg == "entity":
                queryset, values = self.split_by_foreignkey_name(
                    "concerned_business_lines", queryset, values
                )
                applied_aggregations.append(agg)
            elif agg == "baselcategory":
                queryset, values = self.split_by_foreignkey_name(
                    "category__bale_subcategory", queryset, values
                )
                applied_aggregations.append(agg)

        if return_applied_aggregations:
            return queryset, applied_aggregations
        else:
            return queryset

    @cached_property
    def bl_to_rootbl_dict(self):
        """
        Return a flatten dict linking each BusinessLine to its top parent
        """
        bl_to_rootbl = {}
        for root in BusinessLine.objects.filter(depth=1):
            for child in root.get_descendants():
                bl_to_rootbl[child.name] = root.name
            bl_to_rootbl[root.name] = root.name
        return bl_to_rootbl

    def deep_update(self, source, overrides):
        """
        Update a nested dictionary or similar mapping.
        Modify ``source`` in place.
        From: https://stackoverflow.com/a/30655448
        """
        for key, value in overrides.items():
            if isinstance(value, Mapping) and value:
                returned = self.deep_update(source.get(key, {}), value)
                source[key] = returned
            elif isinstance(source.get(key, None), int) and isinstance(
                overrides[key], int
            ):
                source[key] += overrides[key]
            else:
                source[key] = overrides[key]
        return source

    def nest_dict(self, flatten_dict, aggregations, path={}):
        """
        Nest a flatten dict
        Eg: flatten_dict=[
            {"category": "Phishing", "year": "2024", "count": 100},
            {"category": "Phishing", "year": "2025", "count": 42}
        ]
        aggregations = ["category", "year"]

        will return
        {"Phishing": {"2024": 100, "2025": 42}}
        """
        final_dict = defaultdict(dict)
        agg = aggregations.pop(0)
        already_processed = []

        for entry in flatten_dict:
            val = entry[agg]

            if all([entry[k] == v for k, v in path.items()]):
                if aggregations:
                    new_path = path.copy()
                    new_path[agg] = entry[agg]
                    nested = self.nest_dict(flatten_dict, aggregations[:], new_path)
                    if agg == "entity":
                        if val in already_processed:
                            # Avoid processing the same entity multiple time
                            continue
                        already_processed.append(val)

                        # If we filtered by entity: get top BusinessLine from the aggregated BL
                        val = self.bl_to_rootbl_dict.get(val, "Undefined")
                        final_dict[val] = self.deep_update(final_dict[val], nested)
                    else:
                        final_dict[val] = nested
                elif isinstance(entry["count"], int):
                    if agg == "entity":
                        # If we filtered by entity: group count by top BusinessLine
                        val = self.bl_to_rootbl_dict.get(val, "Undefined")
                    if not isinstance(final_dict[val], int):
                        final_dict[val] = 0
                    final_dict[val] += entry["count"]

        return final_dict

    def list(self, request, *args, **kwargs):
        queryset, applied_aggregations = self.get_queryset(
            return_applied_aggregations=True
        )
        queryset = self.filter_queryset(queryset)
        serializer = self.get_serializer(queryset, many=True)

        # Convert the flatten list of entries to a nested dict
        if applied_aggregations:
            nested = self.nest_dict(serializer.data, applied_aggregations)
        else:
            if self.request.query_params.get("unit", "") == "attribute":
                nested = {
                    "attributes": sum(
                        a["count"]
                        for a in serializer.data
                        if isinstance(a["count"], int)
                    )
                }
            else:
                nested = {"incidents": len(serializer.data)}

        return Response(ReturnDict(nested, serializer=serializer))
