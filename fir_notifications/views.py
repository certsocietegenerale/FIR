from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST, require_GET
from django.utils.translation import ugettext_lazy as _

from fir_notifications.forms import NotificationPreferenceForm
from fir_notifications.models import NotificationPreference
from fir_notifications.registry import registry


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


@require_GET
@login_required
def subscriptions(request):
    instances = NotificationPreference.objects.filter(user=request.user,
                                                      event__in=registry.events.keys(),
                                                      method__in=registry.methods.keys(),
                                                      business_lines__isnull=False).distinct()
    return render(request, "fir_notifications/subscriptions.html", {'preferences': instances})


@login_required
def edit_subscription(request, object_id=None):
    instance = None
    if object_id is not None:
        instance = get_object_or_404(NotificationPreference, pk=object_id, user=request.user)
    if request.method == 'POST':
        form = NotificationPreferenceForm(instance=instance, data=request.POST, user=request.user)
        if form.is_valid():
            form.save()
            return JsonResponse({'status': 'success'})
        else:
            errors = render_to_string("fir_notifications/subscribe.html",
                                      {'form': form})
            return JsonResponse({'status': 'error', 'data': errors})
    else:
        form = NotificationPreferenceForm(instance=instance, user=request.user)
    return render(request, "fir_notifications/subscribe.html", {'form': form})


@require_POST
@login_required
def unsubscribe(request, object_id=None):
    if object_id is not None:
        try:
            instance = NotificationPreference.objects.get(pk=object_id, user=request.user)
            instance.delete()
            messages.info(request, _('Unsubscribed.'))
        except NotificationPreference.DoesNotExist:
            messages.error(request, _("Subscription does not exist."))
        except NotificationPreference.MultipleObjectsReturned:
            messages.error(request, _("Subscription is invalid."))
    else:
        messages.error(request, _("Subscription does not exist."))
    return redirect('user:profile')
