from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.views.decorators.http import require_POST

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
    return redirect('user:profile')