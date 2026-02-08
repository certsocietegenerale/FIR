from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from fir_notifications.registry import registry
from fir_notifications.tasks import handle_notification
from incidents.models import BusinessLine


def notification_event(event, signal, model, verbose_name=None, section=None):
    """
    Decorates a Django signal handler to create a notification event
    Args:
        event: event name
        signal: Django signal to listen to
        model: Django model sending the signal (and event)
        verbose_name: verbose name of the notification event
        section: section in the user preference panel (default model application name)

    The signal handler function must return a tuple (model instance, business lines list concerned by the event)

    If settings.NOTIFICATIONS_MERGE_INCIDENTS_AND_EVENTS is False, automatically
    register a paired 'event' notification for non-incident items.
    """

    def decorator_func(func):
        def wrapper_func(*args, **kwargs):
            instance, business_lines = func(*args, **kwargs)
            if instance is None:
                return instance, business_lines

            if isinstance(business_lines, BusinessLine):
                business_lines = [business_lines.path]
            else:
                business_lines = list(
                    business_lines.distinct().values_list("path", flat=True)
                )

            handle_notification.delay(
                ContentType.objects.get_for_model(instance).pk,
                instance.pk,
                business_lines,
                event,
            )
            return instance, business_lines

        registry.register_event(
            event, signal, model, wrapper_func, _(verbose_name), _(section)
        )

        # If merging is disabled, automatically register the "event" version
        if not hasattr(settings, "NOTIFICATIONS_MERGE_INCIDENTS_AND_EVENTS") or (
            not settings.NOTIFICATIONS_MERGE_INCIDENTS_AND_EVENTS
            and event.startswith("incident:")
        ):
            event_event_name = event.replace("incident:", "event:")

            def event_wrapper(sender, instance, **kwargs):
                # Skip if this is actually an incident
                if instance.is_incident:
                    return None, None
                return instance, instance.concerned_business_lines

            # Update verbose_name and section for the event
            event_verbose_name = None
            event_section = None

            if verbose_name:
                event_verbose_name = _(verbose_name.replace("Incident", "Event"))
            if section:
                event_section = _(section.replace("Incident", "Event"))

            registry.register_event(
                event_event_name,
                signal,
                model,
                event_wrapper,
                event_verbose_name,
                event_section,
            )

        return wrapper_func

    return decorator_func
