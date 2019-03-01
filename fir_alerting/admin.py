from django.contrib import admin
from fir_alerting.models import RecipientTemplate, CategoryTemplate
from fir_plugins.admin import MarkdownModelAdmin


class CategoryTemplateAdmin(MarkdownModelAdmin):
    markdown_fields = ('body', )

admin.site.register(RecipientTemplate)
admin.site.register(CategoryTemplate, CategoryTemplateAdmin)
