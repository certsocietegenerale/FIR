from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.utils.translation import gettext_lazy as _
from fir_notifications.decorators import notification_event

from fir_notifications.registry import registry
import fir_notifications.signals
from incidents.models import (
    model_created,
    Incident,
    model_updated,
    Comments,
    model_status_changed,
)


class MethodConfiguration(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="method_preferences",
        verbose_name=_("user"),
    )
    method = models.CharField(
        max_length=60, choices=registry.get_method_choices(), verbose_name=_("method")
    )
    value = models.TextField(verbose_name=_("configuration"))

    def __str__(self):
        return f"{self.user}: {self.method} configuration"

    class Meta:
        verbose_name = _("method configuration")
        verbose_name_plural = _("method configurations")
        unique_together = (("user", "method"),)
        indexes = [models.Index(fields=["user", "method"])]


class NotificationTemplate(models.Model):
    event = models.CharField(
        max_length=60, choices=registry.get_event_choices(), verbose_name=_("event")
    )
    business_lines = models.ManyToManyField(
        "incidents.BusinessLine",
        related_name="+",
        blank=True,
        verbose_name=_("business line"),
    )
    subject = models.CharField(
        max_length=200, blank=True, default="", verbose_name=_("subject")
    )
    short_description = models.TextField(
        blank=True, default="", verbose_name=_("short description")
    )
    description = models.TextField(
        blank=True, default="", verbose_name=_("description")
    )

    class Meta:
        verbose_name = _("notification template")
        verbose_name_plural = _("notification templates")


class NotificationPreference(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notification_preferences",
        verbose_name=_("user"),
    )
    event = models.CharField(max_length=60, verbose_name=_("event"))
    method = models.CharField(max_length=60, verbose_name=_("method"))
    business_lines = models.ManyToManyField(
        "incidents.BusinessLine",
        related_name="+",
        blank=True,
        verbose_name=_("business lines"),
    )

    def __str__(self):
        return f"{self.user}: {self.event} notification preference for {self.method}"

    class Meta:
        verbose_name = _("notification preference")
        verbose_name_plural = _("notification preferences")
        unique_together = ("user", "event", "method")
        indexes = [models.Index(fields=["user", "event", "method"])]
        ordering = ["user", "event", "method"]
