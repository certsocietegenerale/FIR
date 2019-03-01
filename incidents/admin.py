from incidents.models import *
from django.contrib import admin
from django.contrib.auth import admin as auth_admin, get_user_model
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory

User = get_user_model()


class ACENestedAdmin(admin.TabularInline):
    model = AccessControlEntry


class UserAdmin(auth_admin.UserAdmin):
    inlines = [ACENestedAdmin, ]
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active')


class BusinessLineAdmin(TreeAdmin):
    search_fields = ('name', )
    form = movenodeform_factory(BusinessLine)


class IncidentAdmin(admin.ModelAdmin):
    exclude = ("artifacts", )

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
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
