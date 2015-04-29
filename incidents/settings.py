from django.conf import settings

settings.INCIDENT_SHOW_ID = getattr(settings, "INCIDENT_SHOW_ID", False)
