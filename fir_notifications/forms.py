import json

from django import forms
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import get_user_model

from incidents.models import BusinessLine

from fir_notifications.registry import registry
from fir_notifications.models import MethodConfiguration, NotificationPreference


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


class NotificationPreferenceForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        instance = kwargs.get('instance', None)
        if self.user is None and instance is not None:
            self.user = instance.user
        if instance is None and kwargs.get('data', None) is not None:
            data = kwargs.get('data')
            event = data.get('event', None)
            method = data.get('method', None)
            if event and method and self.user:
                try:
                    kwargs['instance'] = NotificationPreference.objects.get(user=self.user, event=event, method=method)
                except (NotificationPreference.DoesNotExist, NotificationPreference.MultipleObjectsReturned):
                    pass
        super(NotificationPreferenceForm, self).__init__(*args, **kwargs)
        self.fields['business_lines'].queryset = BusinessLine.authorization.for_user(self.user,
                                                                                     'incidents.view_incidents')
        if instance is not None:
            self.fields['event'].disabled = True
            self.fields['method'].disabled = True

    def clean_user(self):
        if self.user is None:
            raise forms.ValidationError(_("Notification preference must be linked to a user."))
        return self.user

    user = forms.ModelChoiceField(queryset=get_user_model().objects.all(), widget=forms.HiddenInput(), required=False)
    event = forms.ChoiceField(choices=registry.get_event_choices(), label=_('Event'))
    method = forms.ChoiceField(choices=registry.get_method_choices(), label=_('Method'))
    business_lines = forms.ModelMultipleChoiceField(BusinessLine.objects.all(), label=_('Business lines'))

    class Meta:
        fields = '__all__'
        model = NotificationPreference
