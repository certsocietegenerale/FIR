import json

from django.forms import forms

from fir_notifications.models import MethodConfiguration


class MethodConfigurationForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.method = kwargs.pop('method')
        self.user = kwargs.pop('user', None)
        super(MethodConfigurationForm, self).__init__(*args, **kwargs)
        for option_id, option_field in self.method.options.items():
            self.fields[option_id] = option_field
        self.title = _("Configure %(method)s" % {'method': self.method.verbose_name})

    def save(self, *args, **kwargs):
        if self.user is None:
            return None
        json_value = json.dumps(self.cleaned_data)
        config, created = MethodConfiguration.objects.update_or_create(user=self.user, key=self.method.name,
                                                                       defaults={'value': json_value})
        return config
