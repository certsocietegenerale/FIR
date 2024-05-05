import requests
import json
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect
from django.conf import settings

from incidents.views import is_incident_handler

from fir_threatintel.models import YetiProfile


def get_yp(user):
    yp, _ = YetiProfile.objects.get_or_create(user_id=user)
    # Allow Yeti connection to be defined via global settings
    if not yp.endpoint and not yp.api_key and hasattr(settings, "YETI_URL") and hasattr(settings, "YETI_APIKEY"):
        yp.endpoint = settings.YETI_URL
        yp.api_key = settings.YETI_APIKEY
    return yp


@login_required
@user_passes_test(is_incident_handler)
def update_api(request):
    yp, _ = YetiProfile.objects.get_or_create(user_id=request.user)

    yp.api_key = request.POST.get("yeti_api", "")
    yp.endpoint = request.POST.get("endpoint", "")
    yp.save()

    messages.success(request, "Yeti API successfully updated")
    return redirect("user:profile")


@login_required
@user_passes_test(is_incident_handler)
def query_yeti_artifacts(request):
    try:
        observables = []
        req = json.loads(request.body)
        for elem in req["observables"]:
            if not isinstance(elem, str):
                raise ValueError("string expected")
            observables.append(elem)
    except (KeyError, ValueError):
        return JsonResponse({"error": "Invalid request"}, status=401)

    yp = get_yp(request.user)
    try:
        ret = requests.post(
            yp.endpoint + "/analysis/match",
            json={"observables": observables},
            headers={"X-Api-Key": yp.api_key, "Accept": "application/json"},
        )
        ret.raise_for_status()
        ret = ret.json()
    except (requests.exceptions.RequestException, ValueError) as e:
        return JsonResponse(
            {"error": "Unable to retrieve content from Yeti", "details": str(e)},
            status=500,
        )
    return JsonResponse({"results": ret})


@login_required
@user_passes_test(is_incident_handler)
def send_yeti_artifacts(request):
    try:
        observables = []
        req = json.loads(request.body)
        for obs in req["observables"]:
            for tag in obs["tags"]:
                if not isinstance(tag, str):
                    raise ValueError("string expected for tag")
            if not isinstance(obs["value"], str):
                raise ValueError("string expected for value")
            if not isinstance(obs["fid"], str):
                raise ValueError("string expected for fid")
            observables.append(
                {
                    "context": {
                        "source": "FIR",
                        "Description": "Seen in " + obs["fid"],
                    },
                    "value": obs["value"],
                    "tags": obs["tags"],
                }
            )
    except (KeyError, ValueError):
        return JsonResponse({"error": "Invalid request"}, status=401)

    yp = get_yp(request.user)
    try:
        ret = requests.post(
            yp.endpoint + "/observable/bulk",
            json={"observables": observables, "refang": False},
            headers={"X-Api-Key": yp.api_key, "Accept": "application/json"},
        )
        ret.raise_for_status()
        ret = ret.json()
    except (requests.exceptions.RequestException, ValueError) as e:
        return JsonResponse(
            {"error": "Unable to send data to Yeti", "details": str(e)},
            status=500,
        )

    return JsonResponse({"response": "ok"})
