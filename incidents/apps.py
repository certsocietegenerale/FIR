from django.apps import AppConfig


class IncidentsConfig(AppConfig):
    name = 'incidents'

    def ready(self):
        from fir_plugins import links
        import re
        from django.core.urlresolvers import reverse
        links.install(re.compile("(?:^|\s)#(\d+)"), r"%s\1/" % reverse('incidents:index'))