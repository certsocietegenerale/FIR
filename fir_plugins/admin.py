from django.contrib import admin

from fir_plugins.widgets import MarkdownTextarea


class MarkdownModelAdmin(admin.ModelAdmin):
    markdown_fields = ()

    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name in self.markdown_fields:
            kwargs['widget'] = MarkdownTextarea
        return super(MarkdownModelAdmin, self).formfield_for_dbfield(db_field, **kwargs)

    class Media:
        css = {
            'all': ('css/bootstrap.min.css', 'admin/fix_bootstrap.css')
        }
        js = ('js/jquery.min.js', 'js/bootstrap.min.js',)
