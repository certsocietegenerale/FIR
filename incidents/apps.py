from django.apps import AppConfig


class IncidentsConfig(AppConfig):
    name = 'incidents'

    def ready(self):
        from fir_plugins.links import registry
        registry.register_reverse_link("FID:(\d+)", 'incidents:details', model='incidents.Incident', reverse="#{}")
