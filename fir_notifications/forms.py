import json
from collections import OrderedDict

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


class NotificationPreferenceFormset(forms.BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        self.notifications = OrderedDict()
        for e, verbose_e in registry.events.items():
            for m, verbose_m in registry.methods.items():
                self.notifications["{}_{}".format(e, m)] = {'event': e,
                                                            'verbose_event': verbose_e,
                                                            'method': m,
                                                            'verbose_method': verbose_m.verbose_name}
        self.min_num = len(self.notifications)
        self.max_num = len(self.notifications)
        self.can_delete = False
        super(NotificationPreferenceFormset, self).__init__(*args, **kwargs)

    def _construct_form(self, i, **kwargs):
        method = None
        event = None
        if self.is_bound and i < self.initial_form_count():
            pk_key = "%s-%s" % (self.add_prefix(i), self.model._meta.pk.name)
            pk = self.data[pk_key]
            pk_field = self.model._meta.pk
            to_python = self._get_to_python(pk_field)
            pk = to_python(pk)
            instance = self._existing_object(pk)
            notification = self.notifications.pop("{}_{}".format(instance.event, instance.method))
            event = notification['verbose_event']
            method = notification['verbose_method']
            kwargs['instance'] = instance
        if i < self.initial_form_count() and 'instance' not in kwargs:
            instance = self.get_queryset()[i]
            notification = self.notifications.pop("{}_{}".format(instance.event, instance.method))
            event = notification['verbose_event']
            method = notification['verbose_method']
            kwargs['instance'] = self.get_queryset()[i]
        if i >= self.initial_form_count() and self.notifications:
            # Set initial values for extra forms
            try:
                key, initial = self.notifications.popitem()
                event = initial['verbose_event']
                method = initial['verbose_method']
                kwargs['initial'] = {'event': initial['event'], 'method': initial['method']}
            except IndexError:
                pass
        form = forms.BaseFormSet._construct_form(self, i, **kwargs)
        if self.save_as_new:
            # Remove the primary key from the form's data, we are only
            # creating new instances
            form.data[form.add_prefix(self._pk_field.name)] = None

            # Remove the foreign key from the form's data
            form.data[form.add_prefix(self.fk.name)] = None

            # Set the fk value here so that the form can do its validation.
        fk_value = self.instance.pk
        if self.fk.remote_field.field_name != self.fk.remote_field.model._meta.pk.name:
            fk_value = getattr(self.instance, self.fk.remote_field.field_name)
            fk_value = getattr(fk_value, 'pk', fk_value)
        setattr(form.instance, self.fk.get_attname(), fk_value)
        setattr(form, 'get_notification_display', lambda: u"{} via {}".format(event.verbose_name, method))
        setattr(form, 'get_event', lambda: event)
        return form

    @property
    def labelled_forms(self):
        fs_forms = {}
        for form in self.forms:
            label = form.get_event().section
            if label not in fs_forms:
                fs_forms[label] = []
            fs_forms[label].append(form)
            fs_forms[label] = sorted(fs_forms[label], key=lambda form: form.get_event().name)
        return fs_forms
