from django.core.urlresolvers import reverse
from django.db import models
from django.utils import six
import re


class LinkUrl(object):
    def __init__(self, url, request=None):
        self.url = url
        self.request = request

    def __call__(self, match):
        path = reverse(self.url, args=match.groups())
        if self.request is not None:
            return self.request.build_absolute_uri(path)
        return path


class Links(object):
    def __init__(self):
        self.reverse_links = []
        self.regex_links = []
        self.model_links = {}

    def register_reverse_link(self, parser_regex, url_name, model=None, reverse=None):
        """
        Registers a new parser for links using Django urlconf
        :param parser_regex: string or regex object
        :param url_name: urlconf name
        :param model: model label (app_label.model_name) or model class (used by fir_relations)
        :param reverse: string template to render object id to text (used by fir_relations)
        """
        if not isinstance(parser_regex, re._pattern_type):
            parser_regex = re.compile(parser_regex)
        self.reverse_links.append((parser_regex, url_name))
        if model is not None:
            if not isinstance(model, six.string_types) and issubclass(models.Model, model):
                model = model._meta.label
            self.model_links[model] = (parser_regex, url_name, reverse)

    def register_regex_link(self, parser_regex, template):
        """
        Registers a new parser for links using regex replacement
        :param parser_regex: string or regex object
        :param template: template to pass to regex expand
        """
        if not isinstance(parser_regex, re._pattern_type):
            parser_regex = re.compile(parser_regex)
        self.regex_links.append((parser_regex, template))

    def _reverse(self, request=None):
        patterns = []
        for regex, url in self.reverse_links:
            patterns.append((regex, LinkUrl(url, request)))
        return patterns

    def link_patterns(self, request=None):
        links = list(self.regex_links)
        links.extend(self._reverse(request=request))
        return links

    def parser_for_model(self, model):
        if isinstance(model, models.Model):
            model = model._meta.label
        return self.model_links.get(model, None)

registry = Links()
