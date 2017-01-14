from __future__ import unicode_literals

from django.db import models
from django.conf import settings
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from fir_notifications.registry import registry


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

