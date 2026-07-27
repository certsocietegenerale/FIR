from django import template
from django.conf import settings

register = template.Library()


@register.filter
def get_inc_id_with_prefix(incident_id):
    inc_prefix = getattr(settings, "INCIDENT_ID_PREFIX", "FIR-") or "FIR-"
    incident_id_with_prefix = f"{inc_prefix}{incident_id}"
    return incident_id_with_prefix
