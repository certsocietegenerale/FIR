import re

from django import template
from django.template.loader import get_template
from django.template import RequestContext

register = template.Library()

INSTALLED_ARTIFACTS = dict()


def install(artifact_class):
    INSTALLED_ARTIFACTS[artifact_class.key] = artifact_class


def find(data):
    from fir_artifacts.models import ArtifactBlacklistItem

    result = dict()
    for key in INSTALLED_ARTIFACTS:
        blacklist = ArtifactBlacklistItem.objects.filter(type=key).values_list('value', flat=True)
        values = INSTALLED_ARTIFACTS[key].find(data)
        values = [v for v in values if v not in blacklist]
        result[key] = values

    return result


def after_save(type, value, event):
    return INSTALLED_ARTIFACTS[type].after_save(value, event)


def all_for_object(obj, raw=False):
    result = []
    total_count = 0
    correlated_count = 0

    if not hasattr(obj, "artifacts"):
        return (result, total_count, correlated_count)

    for artifact in INSTALLED_ARTIFACTS:
        values = obj.artifacts.filter(type=artifact)
        artifact_collection = INSTALLED_ARTIFACTS[artifact](values, obj)
        total_count += values.count()
        correlated_count += artifact_collection.correlated_count()
        result.append(artifact_collection)

    return (result, total_count, correlated_count)


class AbstractArtifact:
    case_sensitive = False
    template = 'fir_artifacts/default.html'

    @classmethod
    def find(cls, data):
        results = []
        for i in re.finditer(cls.regex, data):
            if cls.case_sensitive:
                results.append(i.group('search'))
            else:
                results.append(i.group('search').lower())

        return results

    @classmethod
    def after_save(cls, value, event):
        # Do nothing, allows for specific callback in subclasses
        pass

    def __init__(self, artifacts, event):
        self._artifacts = artifacts
        self._event = event

        self._correlated = []
        for artifact in self._artifacts:
            if artifact.relations.count() > 1:
                self._correlated.append(artifact)

    def display(self, request, correlated=False):
        context = RequestContext(request)
        template = get_template(self.__class__.template)
        context['artifact_name'] = self.__class__.display_name
        if correlated:
            context['artifact_values'] = self._correlated
        else:
            context['artifact_values'] = self._artifacts
        context['event'] = self._event

        return template.render(context.flatten(), request)

    def correlated_count(self):
        return len(self._correlated)
