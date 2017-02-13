from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.views.decorators.http import require_POST
from django.contrib import messages

from fir_email.forms import SMIMECertificateForm


@require_POST
@login_required
def smime_configuration(request):
    form = SMIMECertificateForm(request.POST, user=request.user)
    if form.is_valid():
        form.save()
    else:
        for error in form.errors.items():
            messages.error(request, error[1])
    return redirect('user:profile')