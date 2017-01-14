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

def incs_for_art(art_string):
    from fir_artifacts.models import Artifact
    artifacts = Artifact.objects.filter(value__contains=art_string)
    incs = []
    for a in artifacts:
        incs.extend(a.relations.all())
    return incs


def all_for_object(obj, raw=False, user=None):
    result = []
    total_count = 0
    correlated_count = 0

    if not hasattr(obj, "artifacts"):
        return (result, total_count, correlated_count)

    for artifact in INSTALLED_ARTIFACTS:
        values = obj.artifacts.filter(type=artifact)
        artifact_collection = INSTALLED_ARTIFACTS[artifact](values, obj, user=user)
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

    def __init__(self, artifacts, event, user=None):
        class ArtifactDisplay(object):
            def __init__(self, artifact, user):
                self.artifact = artifact
                self.correlation_count = self.artifact.relations_for_user(user).count()

            @property
            def value(self):
                return self.artifact.value

            @property
            def type(self):
                return self.artifact.type

            @property
            def id(self):
                return self.artifact.id

            @property
            def pk(self):
                return self.artifact.pk

        self._artifacts = [ArtifactDisplay(artifact, user) for artifact in artifacts]
        self._event = event

        self._correlated = []
        for artifact in self._artifacts:
            if artifact.correlation_count > 1:
                self._correlated.append(artifact)

    def json(self, request):
        return self.display(request, correlated=False, json=True)

    def display(self, request, correlated=False, json=False):
        context = RequestContext(request)
        template = get_template(self.__class__.template)
        context['artifact_name'] = self.__class__.display_name
        if correlated:
            context['artifact_values'] = self._correlated
        else:
            context['artifact_values'] = self._artifacts

        context['event'] = self._event

        if not json:
            return template.render(context.flatten(), request)
        else:
            return context.flatten()

    def correlated_count(self):
        return len(self._correlated)
