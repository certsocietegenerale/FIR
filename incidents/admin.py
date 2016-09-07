from incidents.models import *
from django.contrib import admin

from treebeard.admin import TreeAdmin


class BusinessLineAdmin(TreeAdmin):
    search_fields = ('name', )
    exclude = ('path', 'depth', 'numchild')


class IncidentAdmin(admin.ModelAdmin):
    exclude = ("artifacts", )
    pass

admin.site.register(Incident, IncidentAdmin)
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
