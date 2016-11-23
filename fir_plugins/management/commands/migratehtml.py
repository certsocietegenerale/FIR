from django.core.management.base import BaseCommand, CommandError
from django.apps import apps

import re


class Command(BaseCommand):
    models = {
        'incidents': {
            'Incident': ['description', ],
            'IncidentTemplate': ['description', ],
            'Comments': ['comment', ]
        },
        'fir_alerting': {
            'CategoryTemplate': ['body', ]
        }
    }

    def add_arguments(self, parser):
        parser.add_argument('app_label', nargs='*', type=unicode)

    def handle(self, *args, **options):
        try:
            import html2text
            converter = html2text.HTML2Text()
            converter.single_line_break = True
            converter.emphasis_mark = '*'
        except ImportError:
            raise CommandError(u"You must install 'html2text' to migrate your data.")
        models = {}
        if not 'app_label' in options or not len(options['app_label']):
            applications = self.models.keys()
        else:
            applications = options['app_label']
        for app_label in applications:
            if app_label in self.models.keys():
                try:
                    apps.get_app_config(app_label)
                except LookupError:
                    raise CommandError(u"App '{app_label}' not in installed apps.".format(app_label=app_label))
                for model_name, field_names in self.models[app_label].items():
                    try:
                        model = apps.get_model(app_label, model_name)
                        models[model] = field_names
                    except LookupError:
                        raise CommandError(u"App '{app_label}' has no '{model_name}' Model.".format(app_label=app_label,
                                                                                                  model_name=model_name))
                    for field in field_names:
                        try:
                            model._meta.get_field(field)
                        except:
                            raise CommandError(
                                u"Model '{app_label}.{model_name}' has no '{field}' attribute.".format(app_label=app_label,
                                                                                                       model_name=model_name,
                                                                                                       field=field))
        for model, field_names in models.items():
            for field in field_names:
                for instance in model.objects.all():
                    html_value = getattr(instance, field, '')
                    # HTML should have one opening and one closing tag
                    if html_value and len(html_value) and html_value.count('<') > 1 and html_value.count('>') > 1:
                        print("Processing '{field}' field of '{instance}'.".format(field=field, instance=instance))
                        html_value = re.sub(r"\r\n\r\n", "<br>", html_value)
                        md_data = converter.handle(html_value)
                        setattr(instance, field, md_data)
                        instance.save()
