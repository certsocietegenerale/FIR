import json

from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

from incidents.models import BusinessLine

from fir_notifications import signals
from fir_notifications.registry import registry
from fir_notifications.models import MethodConfiguration, NotificationPreference


class MethodConfigurationForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.method = kwargs.pop("method")
        self.user = kwargs.pop("user", None)
        super(MethodConfigurationForm, self).__init__(*args, **kwargs)
        for option_id, option_field in self.method.options.items():
            self.fields[option_id] = option_field
        self.title = _("Configure %(method)s" % {"method": self.method.verbose_name})

    def save(self, *args, **kwargs):
        if self.user is None:
            return None
        json_value = json.dumps(self.cleaned_data)
        config, created = MethodConfiguration.objects.update_or_create(
            user=self.user, method=self.method.name, defaults={"value": json_value}
        )
        return config


class NotificationTemplateForm(forms.ModelForm):
    event = forms.ChoiceField(choices=registry.get_event_choices())

    class Meta:
        fields = "__all__"


class NotificationPreferenceForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super(NotificationPreferenceForm, self).__init__(*args, **kwargs)
        self.fields["business_lines"].queryset = BusinessLine.authorization.for_user(
            self.user, "incidents.view_incidents"
        )

    user = forms.ModelChoiceField(
        queryset=get_user_model().objects.all(),
        widget=forms.HiddenInput(),
        required=False,
    )
    event = forms.ChoiceField(choices=registry.get_event_choices(), label=_("Event"))
    method = forms.ChoiceField(choices=registry.get_method_choices(), label=_("Method"))
    business_lines = forms.ModelMultipleChoiceField(
        BusinessLine.objects.all(), label=_("Business lines")
    )

    class Meta:
        fields = "__all__"
        model = NotificationPreference
