from django import template

register = template.Library()

@register.filter
def display_artifact(artifact, request):
	return artifact.display(request)

@register.filter
def display_correlated_artifact(artifact, request):
	return artifact.display(request, True)
