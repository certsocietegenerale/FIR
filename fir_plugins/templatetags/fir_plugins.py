from django import template
from django.conf import settings
from django.template import TemplateDoesNotExist
from django.template.loader import get_template

register = template.Library()

apps = settings.INSTALLED_APPS


def template_path(app, name):
	return '/'.join((app, 'plugins', name)) + '.html'


@register.simple_tag(takes_context=True)
def plugin_point(context, name):
	templates = [template_path(app, name) for app in apps]

	result = ""
	for template in templates:
		try:
			t = get_template(template)
			result += t.render(context)
		except TemplateDoesNotExist:
			pass

	return result

@register.filter
def relation_name(obj):
	return obj.__class__.__name__.lower()+'s'
