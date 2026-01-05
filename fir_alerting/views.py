from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from fir_alerting.models import EmailForm


@login_required
def emailform(request):
    email_form = EmailForm()

    return render(request, "fir_alerting/emailform.html", {"form": email_form})
