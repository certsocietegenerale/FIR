from django.contrib.auth.decorators import login_required
from django import forms
from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST
from django.contrib.auth import get_user_model

from fir_notifications.forms import NotificationPreferenceFormset
from fir_notifications.models import NotificationPreference
from fir_notifications.registry import registry

from incidents.models import BusinessLine


@require_POST
@login_required
def method_configuration(request, method):
    method_object = registry.methods.get(method, None)
    if method is None:
        return redirect('user:profile')
    form = method_object.form(request.POST, user=request.user)
    if form.is_valid():
        form.save()
    else:
        for error in form.errors.items():
            messages.error(request, error[1])
    return redirect('user:profile')


@login_required
def preferences(request):

    class NotificationPreferenceForm(forms.ModelForm):
        event = forms.ChoiceField(choices=registry.get_event_choices(), disabled=True, widget=forms.HiddenInput())
        method = forms.ChoiceField(choices=registry.get_method_choices(), disabled=True, widget=forms.HiddenInput())
        business_lines = forms.ModelMultipleChoiceField(BusinessLine.authorization.for_user(request.user,
                                                                                            'incidents.view_incidents'),
                                                        required=False)

        class Meta:
            fields = "__all__"

    formset = forms.inlineformset_factory(get_user_model(), NotificationPreference,
                                          formset=NotificationPreferenceFormset,
                                          form=NotificationPreferenceForm)
    if request.method == 'POST':
        fs = formset(request.POST, instance=request.user)
        if fs.is_valid():
            fs.save()
        return redirect('user:profile')
    else:
        fs = formset(instance=request.user)

    return render(request, "fir_notifications/preferences.html", {'formset': fs})
