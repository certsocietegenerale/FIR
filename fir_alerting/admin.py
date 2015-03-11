from django.contrib import admin

from fir_alerting.models import RecipientTemplate, CategoryTemplate

admin.site.register(RecipientTemplate)
admin.site.register(CategoryTemplate)
