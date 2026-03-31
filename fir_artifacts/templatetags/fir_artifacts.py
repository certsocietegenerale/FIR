from django import template
from django.utils.safestring import mark_safe
import urllib.parse

from fir_artifacts.artifacts import all_for_object

register = template.Library()


@register.filter
def display_artifact(artifact, request):
    return artifact.display(request)


@register.filter
def display_correlated_artifact(artifact, request):
    return artifact.display(request, True)


@register.filter(is_safe=True)
def hashes_line(obj):
    hash_list = ["", "", ""]
    for h in obj.all():
        if len(h.value) == 64:
            hash_list[0] = h.value
        elif len(h.value) == 40:
            hash_list[1] = h.value
        elif len(h.value) == 32:
            hash_list[2] = h.value
    return mark_safe("<td>%s</td><td>%s</td><td>%s</td>" % tuple(hash_list))


@register.filter
def correlations_url(artifact):
    quoted_artifact = artifact.replace("\\", "\\\\").replace('"', '\\"')
    query = urllib.parse.quote('artifact:"' + quoted_artifact + '"', safe="")
    return "/search?q=" + query


@register.inclusion_tag("fir_artifacts/correlated_artifacts.html", takes_context=True)
def get_correlated_artifacts(context, obj):
    request = context["request"]

    artifacts, artifacts_count, correlated_count = all_for_object(
        obj, user=request.user
    )

    return {
        "artifacts": artifacts,
        "artifacts_count": artifacts_count,
        "correlated_count": correlated_count,
        "request": request,
    }


@register.inclusion_tag("fir_artifacts/artifacts_count.html", takes_context=True)
def get_artifacts_count(context, obj):
    request = context["request"]

    _, artifacts_count, _ = all_for_object(obj, user=request.user)

    return {
        "artifacts_count": artifacts_count,
    }


@register.simple_tag(takes_context=True)
def load_artifacts(context, obj):
    request = context["request"]

    artifacts, artifacts_count, correlated_count = all_for_object(
        obj, user=request.user
    )

    return artifacts
