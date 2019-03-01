from django.contrib import admin

from fir_abuse.models import AbuseTemplate, AbuseContact

admin.site.register(AbuseTemplate)
admin.site.register(AbuseContact)
