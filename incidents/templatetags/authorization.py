from django import template
from django.apps import apps
from django.forms import ModelForm
from django.conf import settings
from django.utils import six

register = template.Library()


@register.simple_tag(takes_context=True)
def has_perm(context, *permissions, **kwargs):
    obj = kwargs.get('obj', None)
    if obj is None:
        obj = kwargs.get('model', None)
        if isinstance(obj, ModelForm):
            obj = obj._meta.model
        elif isinstance(obj, six.string_types):
            obj = apps.get_model(*obj.split('.'))
    return context['user'].has_perm(permissions, obj=obj)


@register.simple_tag(takes_context=True)
def can_comment(context, incident):
    permissions = ['incidents.handle_incidents', ]
    if getattr(settings, 'INCIDENT_VIEWER_CAN_COMMENT', False):
        permissions.append('incidents.view_incidents')
    return incident.has_perm(context['user'], permissions)
