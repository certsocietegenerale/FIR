from django.db.models.signals import post_save
from django.utils.translation import gettext_lazy as _
from fir_notifications.decorators import notification_event
from incidents.models import (
    Incident,
    IncidentStatus,
    Comments,
    model_created,
    model_updated,
    model_status_changed,
)


@notification_event(
    "incident:created",
    model_created,
    Incident,
    verbose_name="Incident created",
    section="Incident",
)
def incident_created(sender, instance, **kwargs):
    if not instance.is_incident:
        return None, None
    return instance, instance.concerned_business_lines


@notification_event(
    "incident:updated",
    model_updated,
    Incident,
    verbose_name="Incident updated",
    section="Incident",
)
def incident_updated(sender, instance, **kwargs):
    if not instance.is_incident:
        return None, None
    return instance, instance.concerned_business_lines


@notification_event(
    "incident:commented",
    post_save,
    Comments,
    verbose_name="Incident commented",
    section="Incident",
)
def incident_commented(sender, instance, **kwargs):
    if not instance.incident.is_incident:
        return None, None
    if IncidentStatus.objects.filter(associated_action=instance.action).exists():
        return None, None
    return instance, instance.incident.concerned_business_lines


@notification_event(
    "incident:status_changed",
    model_status_changed,
    Incident,
    verbose_name="Incident status changed",
    section="Incident",
)
def incident_status_changed(sender, instance, **kwargs):
    if not instance.is_incident:
        return None, None
    return instance, instance.concerned_business_lines
