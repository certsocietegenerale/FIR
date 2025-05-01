import importlib
from django.forms import ModelForm
from django import forms
from incidents.models import (
    IncidentCategory,
    Incident,
    Comments,
    BusinessLine,
    IncidentStatus,
    get_initial_status,
)
from incidents.fields import DateTimeLocalField, TranslatedModelChoiceField
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist

from fir.config.base import INSTALLED_APPS


class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label=False,
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "name": "username",
                "placeholder": "Username",
            }
        ),
    )
    password = forms.CharField(
        label=False,
        max_length=64,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "name": "password",
                "placeholder": "Password",
            }
        ),
    )
    remember = forms.BooleanField(
        required=False,
        label="Remember me",
        widget=forms.CheckboxInput(attrs={"class": "checkbox", "name": "remember"}),
    )


class CustomAuthenticationTokenForm(ModelForm):
    def __init__(self, user, initial_device, **kwargs):
        super(CustomAuthenticationTokenForm, self).__init__(
            user, initial_device, **kwargs
        )


class IncidentForm(ModelForm):
    date = DateTimeLocalField()
    status = TranslatedModelChoiceField(queryset=IncidentStatus.objects.all())
    _additional_forms = {}

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("for_user", None)
        permissions = kwargs.pop("permissions", None)
        has_permission = True
        if permissions is None:
            permissions = [
                "incidents.handle_incidents",
            ]
            has_permission = False
        super(ModelForm, self).__init__(*args, **kwargs)
        if self.user is not None:
            if not isinstance(permissions, (list, tuple)):
                permissions = [
                    permissions,
                ]
            if "instance" not in kwargs and not has_permission:
                permissions.append("incidents.report_events")
            self.fields["concerned_business_lines"].queryset = (
                BusinessLine.authorization.for_user(self.user, permissions)
            )
        field_required = _("This field is required.")
        self.fields["subject"].error_messages["required"] = field_required
        self.fields["category"].error_messages["required"] = field_required
        self.fields["concerned_business_lines"].error_messages[
            "required"
        ] = field_required
        self.fields["detection"].error_messages["required"] = field_required
        self.fields["severity"].error_messages["required"] = field_required
        self.fields["is_major"].error_messages["required"] = field_required
        self.fields["is_major"].label = _("Major?")

        self.fields["status"].initial = get_initial_status()
        self.fields["status"].empty_label = None

        # Load Additional incident fields defined in plugins via a hook
        for app in INSTALLED_APPS:
            if app.startswith("fir_"):
                try:
                    h = importlib.import_module(f"{app}.hooks")
                except ImportError:
                    continue

                for field in h.hooks.get("incident_fields", []):
                    if field[0].endswith("_set") or field[1] is None:
                        # OneToMany fields are not supported
                        continue

                    kwargs["instance"], __ = field[1].Meta.model.objects.get_or_create(
                        incident=kwargs.get("instance", None)
                    )
                    model_sub_form = field[1](*args, **kwargs)
                    setattr(self, field[0], model_sub_form)
                    self._additional_forms[field[0]] = model_sub_form

    def clean(self):
        cleaned_data = super(IncidentForm, self).clean()
        if self.user is not None:
            business_lines = cleaned_data.get("concerned_business_lines")
            is_incident = cleaned_data.get("is_incident")
            if not (business_lines or self.user.has_perm("incidents.handle_incidents")):
                self.add_error(
                    "concerned_business_lines",
                    forms.ValidationError(
                        _(
                            "Incidents without business line can only be created by global incident handlers."
                        )
                    ),
                )

        return cleaned_data

    def is_valid(self):
        for form in self._additional_forms:
            if not self._additional_forms[form].is_valid():
                return False
        return super().is_valid()

    def _save_m2m(self):
        for form in self._additional_forms:
            elem = self._additional_forms[form].save(commit=False)
            elem.incident = self.instance
            elem.save()
        return super()._save_m2m()

    class Meta:
        model = Incident
        exclude = ["opened_by", "main_business_lines", "is_starred", "artifacts"]


class CommentForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(ModelForm, self).__init__(*args, **kwargs)
        self.fields["comment"].error_messages["required"] = _("This field is required.")
        self.fields["action"].error_messages["required"] = _("This field is required.")

    class Meta:
        model = Comments
        exclude = ["incident", "opened_by"]
        widgets = {
            "action": forms.Select(attrs={"required": True, "class": "form-control"})
        }


class UploadFileForm(forms.Form):
    title = forms.CharField()
    file = forms.FileField()


class IncidentStatusAdminForm(forms.ModelForm):
    class Meta:
        model = IncidentStatus
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        flag = cleaned_data.get("flag")

        if flag == "initial":
            if (
                IncidentStatus.objects.exclude(pk=self.instance.pk)
                .filter(flag="initial")
                .exists()
            ):
                raise forms.ValidationError(_("There can only be one initial status."))

        return cleaned_data
