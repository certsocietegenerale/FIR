from __future__ import unicode_literals

from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from fir_notifications.decorators import notification_event

from fir_notifications.registry import registry
from incidents.models import model_created, Incident, model_updated, Comments, model_status_changed


@python_2_unicode_compatible
class MethodConfiguration(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='method_preferences', verbose_name=_('user'))
    key = models.CharField(max_length=60, choices=registry.get_method_choices(), verbose_name=_('method'))
    value = models.TextField(verbose_name=_('configuration'))

    def __str__(self):
        return "{user}: {method} configuration".format(user=self.user, method=self.key)

    class Meta:
        verbose_name = _('method configuration')
        verbose_name_plural = _('method configurations')
        unique_together = (("user", "key"),)
        index_together = ["user", "key"]


class NotificationTemplate(models.Model):
    event = models.CharField(max_length=60, choices=registry.get_event_choices(), verbose_name=_('event'))
    business_lines = models.ManyToManyField('incidents.BusinessLine', related_name='+', blank=True,
                                            verbose_name=_('business line'))
    subject = models.CharField(max_length=200, blank=True, default="", verbose_name=_('subject'))
    short_description = models.TextField(blank=True, default="", verbose_name=_('short description'))
    description = models.TextField(blank=True, default="", verbose_name=_('description'))

    class Meta:
        verbose_name = _('notification template')
        verbose_name_plural = _('notification templates')


@python_2_unicode_compatible
class NotificationPreference(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='notification_preferences', verbose_name=_('user'))
    event = models.CharField(max_length=60, verbose_name=_('event'))
    method = models.CharField(max_length=60, verbose_name=_('method'))
    business_lines = models.ManyToManyField('incidents.BusinessLine', related_name='+', blank=True,
                                            verbose_name=_('business lines'))

    def __str__(self):
        return "{user}: {event} notification preference for {method}".format(user=self.user,
                                                                             event=self.event,
                                                                             method=self.method)

    class Meta:
        verbose_name = _('notification preference')
        verbose_name_plural = _('notification preferences')
        unique_together = (("user", "event", "method"),)
        index_together = ["user", "event", "method"]
        ordering = ['user', 'event', 'method']


if not settings.NOTIFICATIONS_MERGE_INCIDENTS_AND_EVENTS:
    @notification_event('event:created', model_created, Incident, verbose_name=_('Event created'),
                        section=_('Event'))
    def event_created(sender, instance, **kwargs):
        if instance.is_incident:
            return None, None
        return instance, instance.concerned_business_lines


    @notification_event('event:updated', model_updated, Incident, verbose_name=_('Event updated'),
                        section=_('Event'))
    def event_updated(sender, instance, **kwargs):
        if instance.is_incident:
            return None, None
        return instance, instance.concerned_business_lines


    @notification_event('event:commented', post_save, Comments, verbose_name=_('Event commented'),
                        section=_('Event'))
    def event_commented(sender, instance, **kwargs):
        if not instance.incident and instance.incident.is_incident:
            return None, None
        if instance.action.name in ['Opened', 'Blocked', 'Closed']:
            return None, None
        return instance, instance.incident.concerned_business_lines


    @notification_event('event:status_changed', model_status_changed, Incident, verbose_name=_('Event status changed'),
                        section=_('Event'))
    def event_status_changed(sender, instance, **kwargs):
        if instance.is_incident:
            return None, None
        return instance, instance.concerned_business_lines


@notification_event('incident:created', model_created, Incident, verbose_name=_('Incident created'),
                    section=_('Incident'))
def incident_created(sender, instance, **kwargs):
    if not instance.is_incident:
        return None, None
    return instance, instance.concerned_business_lines


@notification_event('incident:updated', model_updated, Incident, verbose_name=_('Incident updated'),
                    section=_('Incident'))
def incident_updated(sender, instance, **kwargs):
    if not settings.NOTIFICATIONS_MERGE_INCIDENTS_AND_EVENTS and not instance.is_incident:
        return None, None
    return instance, instance.concerned_business_lines


@notification_event('incident:commented', post_save, Comments, verbose_name=_('Incident commented'),
                    section=_('Incident'))
def incident_commented(sender, instance, **kwargs):
    if not instance.incident and not settings.NOTIFICATIONS_MERGE_INCIDENTS_AND_EVENTS and not instance.incident.is_incident:
        return None, None
    if instance.action.name in ['Opened', 'Blocked', 'Closed']:
        return None, None
    return instance, instance.incident.concerned_business_lines


@notification_event('incident:status_changed', model_status_changed, Incident, verbose_name=_('Incident status changed'),
                    section=_('Incident'))
def incident_status_changed(sender, instance, **kwargs):
    if not settings.NOTIFICATIONS_MERGE_INCIDENTS_AND_EVENTS and not instance.is_incident:
        return None, None
    return instance, instance.concerned_business_lines