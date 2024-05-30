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
    if (
        not yp.endpoint
        and not yp.api_key
        and hasattr(settings, "YETI_URL")
        and hasattr(settings, "YETI_APIKEY")
    ):
        yp.endpoint = settings.YETI_URL
        yp.api_key = settings.YETI_APIKEY

    auth = requests.post(
        yp.endpoint + "/api/v2/auth/api-token",
        headers={"X-Yeti-Apikey": yp.api_key},
    )
    auth.raise_for_status()
    yp.access_token = "Bearer " + auth.json()["access_token"]
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

    try:
        yp = get_yp(request.user)
        ret = requests.post(
            f"{yp.endpoint}/api/v2/observables/search",
            json={"query": {"value__in": observables}},
            headers={"Authorization": yp.access_token},
        )
        ret.raise_for_status()
        results = {"known": [], "unknown": []}
        for entry in ret.json()["observables"]:
            results["known"].append(
                {
                    "url": yp.endpoint + "/observables/" + entry["id"],
                    "value": entry["value"],
                    "tags": [t for t in entry["tags"]],
                    "source": [s["source"] for s in entry["context"]],
                }
            )
        for obs in req["observables"]:
            if all([a["value"] != obs for a in results["known"]]):
                results["unknown"].append(obs)
    except (requests.exceptions.RequestException, ValueError) as e:
        return JsonResponse(
            {"error": "Unable to retrieve content from Yeti", "details": str(e)},
            status=500,
        )
    return JsonResponse(results)


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
    try:
        yp = get_yp(request.user)
        for obs in req["observables"]:
            search = requests.post(
                f"{yp.endpoint}/api/v2/observables/search",
                json={"query": {"value": obs["value"]}},
                headers={"Authorization": yp.access_token},
            )
            search.raise_for_status()
            if len(search.json()["observables"]) == 1:
                obs_id = search.json()["observables"][0]["id"]
                tag_edition = requests.post(
                    f"{yp.endpoint}/api/v2/observables/tag",
                    json={"tags": obs["tags"], "ids": [obs_id]},
                    headers={"Authorization": yp.access_token},
                )
                tag_edition.raise_for_status()
            else:
                observable_creation = requests.post(
                    f"{yp.endpoint}/api/v2/observables/bulk",
                    json={
                        "observables": [
                            {
                                "value": obs["value"],
                                "tags": obs["tags"],
                                "type": "guess",
                            }
                        ]
                    },
                    headers={"Authorization": yp.access_token},
                )
                observable_creation.raise_for_status()
                search = requests.post(
                    f"{yp.endpoint}/api/v2/observables/search",
                    json={"query": {"value": obs["value"]}},
                    headers={"Authorization": yp.access_token},
                )
                search.raise_for_status()
                obs_id = search.json()["observables"][0]["id"]

            ret = requests.post(
                f"{yp.endpoint}/api/v2/observables/{obs_id}/context",
                json={
                    "context": {"Description": "Seen in " + obs["fid"]},
                    "source": "FIR",
                },
                headers={"Authorization": yp.access_token},
            )
            ret.raise_for_status()
    except requests.exceptions.RequestException as e:
        return JsonResponse(
            {"error": "Unable to send data to Yeti", "details": str(e)},
            status=500,
        )

    return JsonResponse({"response": "ok"})
