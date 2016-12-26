from django.contrib import admin

from fir_abuse.models import AbuseTemplate, ArtifactEnrichment, AbuseContact

admin.site.register(AbuseTemplate)
admin.site.register(ArtifactEnrichment)
admin.site.register(AbuseContact)
