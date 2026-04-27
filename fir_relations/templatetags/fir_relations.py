from django import template
from django.contrib.contenttypes.models import ContentType

from fir_relations.models import Relation
from incidents.models import Incident

register = template.Library()


@register.inclusion_tag("fir_relations/relations_sidebar.html", takes_context=True)
def display_relations_sidebar(context, event):
    content_type = ContentType.objects.get_for_model(event)

    references = Relation.objects.filter(
        src_content_type=content_type, src_object_id=event.id, active=True
    ).as_template_objects(context["request"], relation_type="target")
    referenced_by = Relation.objects.filter(
        tgt_content_type=content_type, tgt_object_id=event.id, active=True
    ).as_template_objects(context["request"], relation_type="source")
    return {"references": references, "referenced_by": referenced_by}
