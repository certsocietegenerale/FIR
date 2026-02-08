from django import template

from fir_notifications.registry import registry
from fir_notifications.forms import NotificationPreferenceForm

register = template.Library()


@register.simple_tag
def get_configurable_notification_methods():
    actions = {}
    for method_name, method_object in registry.methods.items():
        if len(method_object.options):
            actions[method_name] = method_object.verbose_name
    return actions


@register.inclusion_tag("fir_notifications/options_modalform.html", takes_context=True)
def configure_notification_method_modalform(context):
    actions = {}
    for method_name, method_object in registry.methods.items():
        if len(method_object.options):
            actions[method_name] = method_object.form(user=context["user"])
    return {"method_configuration_forms": actions}


@register.inclusion_tag(
    "fir_notifications/subscriptions_modalform.html", takes_context=True
)
def configure_notification_subscriptions_modalform(context):
    form = NotificationPreferenceForm(user=context["user"])
    return {"form": form}
