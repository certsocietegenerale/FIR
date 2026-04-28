from django import template

register = template.Library()


@register.filter
def artifact_json(artifact, request):
    return artifact.json(request)
