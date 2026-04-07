from django import template
from django.conf import settings
from django.utils.html import mark_safe
from django.template import TemplateDoesNotExist
from django.template.loader import get_template
from django.contrib.contenttypes.models import ContentType

from fir_plugins.links import registry

register = template.Library()

apps = settings.INSTALLED_APPS


@register.simple_tag(takes_context=True)
def plugin_point(context, name):
    templates = [f"{app}/plugins/{name}.html" for app in apps]

    result = ""
    context = context.flatten()
    for template in templates:
        try:
            t = get_template(template)
            result += t.render(context, context["request"])
        except TemplateDoesNotExist:
            pass
    return mark_safe(result)


@register.filter
def content_type(obj):
    if not obj:
        return False
    return ContentType.objects.get_for_model(obj).pk


@register.filter
def object_id(obj):
    id_template = registry.model_links.get(obj._meta.label, ["", "", None])[2]
    if not id_template:
        id_template = "#{}"
    return id_template.format(obj.pk)
