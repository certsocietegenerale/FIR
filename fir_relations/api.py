from rest_framework.filters import OrderingFilter
from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.mixins import (
    DestroyModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
)
from django_filters.rest_framework import FilterSet, DjangoFilterBackend, CharFilter
from django.utils.translation import gettext_lazy as _

from fir_relations.models import Relation, TemplateRelation


class RelationFilter(FilterSet):
    """
    A custom filter class for incident relation filtering
    """

    source_type = CharFilter(
        field_name="src_content_type__model",
        lookup_expr="iexact",
        label=_("Source Type"),
    )
    target_type = CharFilter(
        field_name="tgt_content_type__model",
        lookup_expr="iexact",
        label=_("Target Type"),
    )

    class Meta:
        model = Relation
        fields = ["source_type", "target_type"]


class RelationSerializer(serializers.ModelSerializer):
    """
    Serializer for /api/relations
    """

    source = serializers.SerializerMethodField()
    target = serializers.SerializerMethodField()

    def _build_template(self, obj, relation_type):
        request = self.context.get("request")
        template = TemplateRelation(obj, request, relation_type=relation_type)

        if not template.can_view:
            return None

        return {
            "id": template.id_text,
            "type": template.object_type,
            "name": str(template),
            "can_delete": template.can_edit,
        }

    def get_source(self, obj):
        return self._build_template(obj, "source")

    def get_target(self, obj):
        return self._build_template(obj, "target")

    class Meta:
        model = Relation
        fields = [
            "id",
            "source",
            "target",
        ]


class RelationViewSet(
    ListModelMixin, RetrieveModelMixin, DestroyModelMixin, viewsets.GenericViewSet
):
    """
    API endpoint to list incident relations.
    Relations can't be created or edited via the API, they are automatically generated from incident descriptions and comments.
    """

    queryset = Relation.objects.filter(active=True).select_related(
        "src_content_type", "tgt_content_type"
    )
    serializer_class = RelationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = ["id"]
    filterset_class = RelationFilter

    def get_queryset(self):
        """
        Restrict to relations user can view
        """
        qs = super().get_queryset()

        # filter using TemplateRelation logic
        allowed_pks = [
            rel.pk
            for rel in qs
            if TemplateRelation(rel, self.request, "target").can_view
            and TemplateRelation(rel, self.request, "source").can_view
        ]
        return qs.filter(pk__in=allowed_pks)

    def perform_destroy(self, instance):
        instance.active = False
        instance.save()
