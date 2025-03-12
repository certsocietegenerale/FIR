# for token Generation
import io
from datetime import datetime, timedelta
from collections import defaultdict
from collections.abc import Mapping
from functools import cached_property

from django.apps import apps
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.shortcuts import get_object_or_404
from django.core.files import File as FileWrapper
from django.contrib.auth.models import User
from django.db.models import Q, Count, OuterRef, Subquery, Func
from django.db.models.functions import (
    TruncMonth,
    TruncYear,
    TruncDay,
    TruncHour,
)

from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.exceptions import PermissionDenied
from rest_framework.authtoken.models import Token
from rest_framework.mixins import (
    ListModelMixin,
    RetrieveModelMixin,
    CreateModelMixin,
    UpdateModelMixin,
)
from rest_framework import viewsets, status, renderers
from rest_framework.decorators import action
from rest_framework.renderers import JSONRenderer, AdminRenderer, BrowsableAPIRenderer
from rest_framework.response import Response
from rest_framework.filters import OrderingFilter
from rest_framework.utils.serializer_helpers import ReturnDict

from django_filters.rest_framework import DjangoFilterBackend

from fir_api.serializers import (
    UserSerializer,
    IncidentSerializer,
    ArtifactSerializer,
    FileSerializer,
    CommentsSerializer,
    LabelSerializer,
    AttributeSerializer,
    BusinessLineSerializer,
    CategorySerializer,
    ValidAttributeSerializer,
    SeveritySerializer,
    StatsSerializer,
)
from fir_api.filters import (
    IncidentFilter,
    ArtifactFilter,
    LabelFilter,
    AttributeFilter,
    BLFilter,
    CommentFilter,
    CategoryFilter,
    ValidAttributeFilter,
    FileFilter,
    SeverityFilter,
    StatsFilter,
)
from fir_api.permissions import (
    IsIncidentHandler,
    CanViewStatistics,
    IsAdminUserOrReadOnly,
)
from fir_artifacts.files import handle_uploaded_file, do_download
from fir_artifacts.models import Artifact, File
from incidents.models import (
    Incident,
    Comments,
    Label,
    Attribute,
    BusinessLine,
    IncidentCategory,
    ValidAttribute,
    SeverityChoice,
)


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoints that allow users to be viewed or edited.
    """

    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    renderer_classes = [JSONRenderer, AdminRenderer]


class IncidentViewSet(
    viewsets.GenericViewSet,
    ListModelMixin,
    CreateModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
):
    """
    API endpoints for viewing, creating and editing incidents
    """

    serializer_class = IncidentSerializer
    permission_classes = [IsAuthenticated, IsIncidentHandler]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = [
        "id",
        "date",
        "status",
        "subject",
        "concerned_business_lines",
        "last_comment_date",
        "category",
        "severity",
        "confidentiality",
        "actor",
        "detection",
        "opened_by",
    ]
    filterset_class = IncidentFilter

    def get_queryset(self):
        last_comment_action = Subquery(
            Comments.objects.filter(
                incident_id=OuterRef("id"),
            )
            .order_by("-date")
            .values("action__name")[:1]
        )

        last_comment_date = Subquery(
            Comments.objects.filter(
                incident_id=OuterRef("id"),
            )
            .order_by("-date")
            .values("date")[:1]
        )

        queryset = (
            Incident.authorization.for_user(
                self.request.user, "incidents.view_incidents"
            )
            .annotate(last_comment_date=last_comment_date)
            .annotate(last_comment_action=last_comment_action)
            .order_by("-id")
        )

        # Hide listing of closed incidents if the user checked the corresponding config
        if (
            self.action == "list"
            and hasattr(self.request.user, "profile")
            and hasattr(self.request.user.profile, "hide_closed")
            and self.request.user.profile.hide_closed
        ):
            queryset = queryset.filter(~Q(status="C"))

        return queryset

    def get_businesslines(self, businesslines):
        """
        ::

                Gets businessline objects based on a list
                of businesslines

                Args:
                    businesslines (_type_): _description_

                Returns:
                    QuerySet: A QuerySet with BusinessLine objects as per filter
        """
        bl_filter = Q()
        for bline in businesslines:
            if " > " in bline:
                bline = bline.split(" > ")[-1]
            bl_filter = bl_filter | Q(name=bline)
        bls = BusinessLine.authorization.for_user(
            self.request.user, permission=["incidents.report_events"]
        ).filter(bl_filter)
        return bls

    def perform_create(self, serializer):
        opened_by = self.request.user
        serializer.is_valid(raise_exception=True)
        if type(self.request.data).__name__ == "dict":
            bls = self.request.data.get("concerned_business_lines", [])
        else:
            bls = self.request.data.getlist("concerned_business_lines", [])
        concerned_business_lines = []
        if bls:
            concerned_business_lines = self.get_businesslines(businesslines=bls)
        if bls and not concerned_business_lines:
            raise PermissionDenied(
                {
                    "message": "You don't have write permission on the business lines associated with this incident."
                }
            )
        if not (bls or opened_by.has_perm("incidents.handle_incidents")):
            raise PermissionDenied(
                {
                    "message": "Incidents without business line can only be created by global incident handlers."
                }
            )
        serializer.is_valid(raise_exception=True)
        instance = serializer.save(
            opened_by=opened_by,
            concerned_business_lines=concerned_business_lines,
        )
        instance.refresh_main_business_lines()
        instance.done_creating()

    def perform_update(self, serializer):
        serializer.is_valid(raise_exception=True)
        self.check_object_permissions(self.request, serializer.instance)
        Comments.create_diff_comment(
            self.get_object(), serializer.validated_data, self.request.user
        )
        if type(self.request.data).__name__ == "dict":
            bls = self.request.data.get("concerned_business_lines", [])
        else:
            bls = self.request.data.getlist("concerned_business_lines", [])
        extra_dataset = {}
        if bls:
            extra_dataset["concerned_business_lines"] = self.get_businesslines(
                businesslines=bls
            )
        if bls and not extra_dataset["concerned_business_lines"]:
            raise PermissionDenied(
                {
                    "message": "You don't have write permission on the business lines associated with this incident."
                }
            )
        if not (bls or self.request.user.has_perm("incidents.handle_incidents")):
            raise PermissionDenied(
                {
                    "message": "Incidents without business line can only be created by global incident handlers."
                }
            )

        instance = serializer.save(**extra_dataset)
        instance.refresh_main_business_lines()
        if "description" in serializer.validated_data:
            instance.refresh_artifacts(serializer.validated_data["description"])


class ArtifactViewSet(ListModelMixin, RetrieveModelMixin, viewsets.GenericViewSet):
    """
    API endpoint to list artifacts.
    Artifacts can't be created or edited via the API, they are automatically generated from incident descriptions and comments.
    You can view all incidents having an artifact by accessing /artifacts/<id>
    """

    serializer_class = ArtifactSerializer
    permission_classes = [IsAuthenticated, IsIncidentHandler]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = ["id", "type", "value"]
    filterset_class = ArtifactFilter

    def get_queryset(self):
        incidents_allowed = Incident.authorization.for_user(
            self.request.user, "incidents.view_incidents"
        )
        queryset = (
            Artifact.objects.filter(incidents__in=incidents_allowed)
            .distinct()
            .order_by("id")
        )
        return queryset

    def retrieve(self, request, *args, **kwargs):
        artifact = self.get_queryset().get(pk=self.kwargs.get("pk"))
        correlations = artifact.relations_for_user(user=None).group()
        if all([not link_type.objects.exists() for link_type in correlations.values()]):
            raise PermissionError
        serializer = self.get_serializer(artifact)
        return Response(serializer.data)


class CommentViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows creation of, viewing, and closing of comments
    """

    serializer_class = CommentsSerializer
    permission_classes = [IsAuthenticated, IsIncidentHandler]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = ["id", "date"]
    filterset_class = CommentFilter

    def get_queryset(self):
        incidents_allowed = Incident.authorization.for_user(
            self.request.user, "incidents.view_incidents"
        )
        queryset = Comments.objects.filter(incident__in=incidents_allowed).order_by(
            "id", "date"
        )
        return queryset

    def perform_create(self, serializer):
        incident_object = Incident.objects.get(pk=self.request.data.get("incident"))
        self.check_object_permissions(self.request, incident_object)
        serializer.save(opened_by=self.request.user)
        serializer.validated_data["incident"].refresh_artifacts(
            serializer.validated_data["comment"]
        )

    def perform_update(self, serializer):
        self.check_object_permissions(self.request, serializer.instance.incident)
        serializer.save()
        serializer.validated_data["incident"].refresh_artifacts(
            serializer.validated_data["comment"]
        )

    def perform_destroy(self, instance):
        self.check_object_permissions(self.request, instance.incident)
        return super().perform_destroy(instance)


class LabelViewSet(ListModelMixin, viewsets.GenericViewSet):
    """
    API endpoint for viewing labels
    """

    serializer_class = LabelSerializer
    permission_classes = [IsAuthenticated, IsAdminUserOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = LabelFilter

    def get_queryset(self):
        return Label.objects.all().order_by("id")


class FileViewSet(ListModelMixin, RetrieveModelMixin, viewsets.GenericViewSet):
    """
    API endpoint for listing files.
    Files can be uploaded and downloaded via endpoints /files/<incidentID>/upload and /files/<incidentID>/download
    """

    serializer_class = FileSerializer
    permission_classes = [IsAuthenticated, IsIncidentHandler]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = ["id", "date", "incident"]
    filterset_class = FileFilter

    def get_queryset(self):
        incidents_allowed = Incident.authorization.for_user(
            self.request.user, "incidents.view_incidents"
        )
        queryset = File.objects.filter(incident__in=incidents_allowed).order_by(
            "id", "date"
        )
        return queryset

    @action(detail=True, renderer_classes=[renderers.StaticHTMLRenderer])
    def download(self, request, pk):
        file_object = File.objects.get(pk=pk)
        self.check_object_permissions(self.request, file_object.incident)
        return do_download(request, pk)

    @action(detail=True, methods=["POST"])
    def upload(self, request, pk):
        incident = get_object_or_404(
            Incident.authorization.for_user(
                self.request.user, "incidents.handle_incidents"
            ),
            pk=pk,
        )
        files_added = []
        if type(self.request.data).__name__ == "dict":
            uploaded_files = request.FILES.get("file", [])
        else:
            uploaded_files = request.FILES.getlist("file", [])

        if type(self.request.data).__name__ == "dict":
            descriptions = request.data.get("description", [])
        else:
            descriptions = request.data.getlist("description", [])

        if len(descriptions) != len(uploaded_files):
            return Response(
                data={"Error": "Missing 'description' or 'file'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        for uploaded_file, description in zip(uploaded_files, descriptions):
            file_wrapper = FileWrapper(uploaded_file.file)
            file_wrapper.name = uploaded_file.name
            file = handle_uploaded_file(file_wrapper, description, incident)
            files_added.append(file)

        resp_data = FileSerializer(
            files_added, many=True, context={"request": request}
        ).data
        return Response(resp_data)


class AttributeViewSet(viewsets.ModelViewSet):
    """
    API endpoints for listing, creating or editing incident attributes.
    Before adding an attribute to an incident, you have to register the said attribute in ValidAttributes (see endpoints /validattributes)
    """

    serializer_class = AttributeSerializer
    permission_classes = [IsAuthenticated, IsIncidentHandler]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = ["id", "name", "value", "incident"]
    filterset_class = AttributeFilter

    def get_queryset(self):
        incidents_allowed = Incident.authorization.for_user(
            self.request.user, "incidents.view_incidents"
        )
        queryset = Attribute.objects.filter(incident__in=incidents_allowed).order_by(
            "incident", "id"
        )
        return queryset

    def perform_create(self, serializer):
        incident_object_id = self.request.data.get("incident")
        incident_object = Incident.objects.get(pk=incident_object_id)
        self.check_object_permissions(self.request, incident_object)
        get_object_or_404(ValidAttribute, name=self.request.data.get("name"))
        # See if there is already an attribute in this incident with that name
        try:
            existing_attribute = Attribute.objects.get(
                name=self.request.data.get("name"), incident=incident_object
            )
            # If the value is an integer we just add to it
            try:
                new_value = int(existing_attribute.value) + int(
                    self.request.data.get("value")
                )
                existing_attribute.value = str(new_value)
            # If not an integer we overwrite
            except ValueError:
                existing_attribute.value = self.request.data.get("value")
            existing_attribute.save()
        except Attribute.DoesNotExist:
            serializer.save()

    def perform_update(self, serializer):
        self.check_object_permissions(self.request, serializer.instance.incident)
        serializer.save()

    def perform_destroy(self, instance):
        self.check_object_permissions(self.request, instance.incident)
        return super().perform_destroy(instance)


class ValidAttributeViewSet(viewsets.ModelViewSet):
    """
    API endpoints for listing, creating or editing valid (possible) attributes.
    """

    queryset = ValidAttribute.objects.all().order_by("id")
    serializer_class = ValidAttributeSerializer
    permission_classes = [IsAuthenticated, IsIncidentHandler]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = ["id", "name", "unit", "description", "categories"]
    filterset_class = ValidAttributeFilter


class BusinessLinesViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for listing Business Lines.
    """

    serializer_class = BusinessLineSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = ["id", "name"]
    filterset_class = BLFilter

    def get_queryset(self):
        queryset = BusinessLine.authorization.for_user(
            self.request.user, ["incidents.handle_incidents", "incidents.report_events"]
        ).order_by("id")
        return queryset


class CategoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint for listing Incident Categories.
    """

    queryset = IncidentCategory.objects.all().order_by("id")
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, IsAdminUserOrReadOnly]
    filterset_class = CategoryFilter
    filter_backends = [DjangoFilterBackend, OrderingFilter]


class SeverityViewSet(viewsets.ModelViewSet):
    """
    API endpoint for listing Incident Severities.
    """

    queryset = SeverityChoice.objects.all().order_by("name")
    serializer_class = SeveritySerializer
    permission_classes = [IsAuthenticated, IsAdminUserOrReadOnly]
    filterset_class = SeverityFilter
    filter_backends = [DjangoFilterBackend, OrderingFilter]


class FilterButtonBrowsableAPIRenderer(BrowsableAPIRenderer):

    def get_filter_form(self, data, view, request):
        #  Pass an empty list to force the 'filter' HTML button
        #  to be always displayed
        return super().get_filter_form([], view, request)


class StatsViewSet(ListModelMixin, viewsets.GenericViewSet):
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
                attr_subquery
                .annotate(
                    count=Func("value", function="Sum")
                )  # Perform per-incident sum of all selected attributes
                .values("count")
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

        for entry in flatten_dict:
            val = entry[agg]
            if all([entry[k] == v for k, v in path.items()]):
                if aggregations:
                    new_path = path.copy()
                    new_path[agg] = entry[agg]
                    nested = self.nest_dict(flatten_dict, aggregations[:], new_path)
                    if agg == "entity":
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


# Token Generation ===========================================================


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)
