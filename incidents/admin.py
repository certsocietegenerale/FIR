from incidents.models import *
from django.contrib import admin


class BusinessLineAdmin(admin.ModelAdmin):
    search_fields = ('name', )
    ordering = ('name', )

admin.site.register(Incident)
admin.site.register(BusinessLine, BusinessLineAdmin)
admin.site.register(BaleCategory)
admin.site.register(Comments)
admin.site.register(LabelGroup)
admin.site.register(Label)
admin.site.register(IncidentCategory)
admin.site.register(Log)
admin.site.register(Profile)
admin.site.register(IncidentTemplate)
admin.site.register(Attribute)
admin.site.register(ValidAttribute)
