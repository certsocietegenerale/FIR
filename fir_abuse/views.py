from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from fir_abuse.models import EmailForm


@login_required
def emailform(request):
    email_form = EmailForm(auto_id="abuse_%s")

    return render(request, "fir_abuse/emailform.html", {"form": email_form})
