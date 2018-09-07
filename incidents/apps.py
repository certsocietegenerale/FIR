from django.apps import AppConfig


class IncidentsConfig(AppConfig):
    name = 'incidents'

    def ready(self):
        from fir_plugins.links import registry
        from django.conf import settings
        registry.register_reverse_link(settings.INCIDENT_ID_PREFIX + "(\d+)", 'incidents:details',
                                       model='incidents.Incident', reverse=settings.INCIDENT_ID_PREFIX + "{}")
