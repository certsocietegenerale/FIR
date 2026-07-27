from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.shortcuts import redirect

from incidents.views import is_incident_handler

from fir_misp.models import MISPProfile


@login_required
@user_passes_test(is_incident_handler)
def update_api(request):
    mp, _ = MISPProfile.objects.get_or_create(user_id=request.user)

    mp.api_key = request.POST.get("misp_api", "")
    mp.endpoint = request.POST.get("endpoint", "")
    mp.save()

    messages.success(request, "MISP API successfully updated")
    return redirect("user:profile")
