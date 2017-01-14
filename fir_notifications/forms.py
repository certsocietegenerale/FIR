import json

from django import forms
from django.utils.translation import ugettext_lazy as _

from fir_notifications.registry import registry
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


class NotificationTemplateForm(forms.ModelForm):
    event = forms.ChoiceField(choices=registry.get_event_choices())

    class Meta:
        fields = '__all__'


class EmailMethodConfigurationForm(MethodConfigurationForm):
    def save(self, *args, **kwargs):
        if self.user is None or not self.user.email:
            return None
        try:
            from djembe.models import Identity
        except ImportError:
            return None
        config, created = Identity.objects.update_or_create(address=self.user.email, defaults=self.cleaned_data)
        return config
