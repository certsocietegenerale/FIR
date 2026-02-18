import requests
import json
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect
from django.conf import settings

from incidents.views import is_incident_handler

from fir_misp.models import MISPProfile

from fir_misp.mispclient import MISPClient
from pymisp.exceptions import PyMISPError
import logging

def get_mp(user):
    mp, _ = MISPProfile.objects.get_or_create(user_id=user)
    # Allow MISP connection to be defined via global settings
    if (
        not mp.endpoint
        and not mp.api_key
        and hasattr(settings, "MISP_URL")
        and hasattr(settings, "MISP_APIKEY")
    ):
        mp.endpoint = settings.MISP_URL
        mp.api_key = settings.MISP_APIKEY
    py_misp = MISPClient(mp.endpoint, mp.api_key, ssl=False)
    mp.py_misp = py_misp
    return py_misp

def get_misp_related_events(user, incident_id):
    try:
        mp = get_mp(user)
        tags_to_search = 'fir-' + str(incident_id)
        tags_list = mp.searchtag(tags_to_search)
        related_events = []
        if len(tags_list) > 0:
            tags_list = tags_list[0]
            for elt in tags_list["result"]:
                entry = {}
                entry["url"] = tags_list["url"]  + "/events/view/" + str(elt["id"])
                entry["event_id"] = elt["id"]
                entry["org_name"] = str(elt["Orgc"]["name"])
                entry["event_tags"] = [t["name"] for t in elt["Tag"]]
                entry["date"] = str(elt["date"])
                entry["info"] = str(elt["info"])
                related_events.append(entry)
        return related_events
    except PyMISPError as err:
        logging.error("Got PyMISPError into get_misp_related_events" + str(err)) 
        return []
    except Exception as err:
        logging.error("Got error into get_misp_related_events" + str(err))
        return []

@login_required
@user_passes_test(is_incident_handler)
def update_api(request):
    mp, _ = MISPProfile.objects.get_or_create(user_id=request.user)

    mp.api_key = request.POST.get("misp_api", "")
    mp.endpoint = request.POST.get("endpoint", "")
    mp.save()

    messages.success(request, "MISP API successfully updated")
    return redirect("user:profile")


@login_required
@user_passes_test(is_incident_handler)
def query_misp_artifacts(request):
    try:
        observables = []
        req = json.loads(request.body)
        for elem in req["observables"]:
            if not isinstance(elem, str):
                raise ValueError("string expected")
            observables.append(elem)
        incident_id = int(req["incident_id"])
    except (KeyError, ValueError):
        return JsonResponse({"error": "Invalid request."}, status=401)
    try:
        mp = get_mp(request.user)
        # We don't have the artifact type
        # So we search in all types. Can be very slow
        basic_tags = ["fir-incident", "fir-" + str(incident_id)]
        results = {"known": [], "unknown": [], "basic_tags": basic_tags}
        for entry in observables :
            ret = mp.searchall(entry)
            for r in ret : 
                if r["result"] != []:
                    # we take the last result (the most recent)
                    # We want to know the creator org, the threatlevel, the name + a link (relatedevent) & a date
                    last_res = r["result"][-1]
                    if "Tag" in last_res.keys():
                        tags = [t["name"] for t in last_res["Tag"]]
                    else:
                        tags = []
                    results["known"].append(
                        {
                            "url": r["url"] + "/events/view/" + str(last_res["id"]),
                            "value": entry,
                            "threat_level": str(last_res["threat_level_id"]),
                            "date": str(last_res["date"]),
                            "info": str(last_res["info"]),
                            "org_name": str(last_res["Orgc"]["name"]),
                            "tags": tags,
                            "basic_tags": [x for x in basic_tags if x not in tags],
                        }
                    )
                else:
                    results["unknown"].append(
                        {
                            "value": entry,
                            "basic_tags": basic_tags,
                        }
                    )
        # Now we search the related events
        related_events = get_misp_related_events(request.user, incident_id)
        if len(related_events) > 0:
            results["related_events"] = related_events
    except PyMISPError as e:
        return JsonResponse(
            {"error": "Unable to retrieve content from MISP", "details": str(e)},
            status=500,
        )
    except (requests.exceptions.RequestException, ValueError) as e:
        return JsonResponse(
            {"error": "Unable to retrieve content from MISP", "details": str(e)},
            status=500,
        )
    return JsonResponse(results)



@login_required
@user_passes_test(is_incident_handler)
def send_misp_artifacts(request):
    try:
        observables = []
        misp_events = []
        req = json.loads(request.body)
        for misp_event in req["misp_events"]:
            misp_events.append(int(misp_event["value"]))
        if req["observables"] == []:
            raise ValueError("observables can't be empty")
        if not isinstance(req["fid"], str):
            raise ValueError("string expected for fid")
        fir_id = req["fid"]
        tags_for_event = ["fir-incident", str(fir_id).lower()]
        for obs in req["observables"]:
            for tag in obs["tags"]:
                if not isinstance(tag, str):
                    raise ValueError("string expected for tag")
                tags_for_event.append(tag)
            if not isinstance(obs["value"], str):
                raise ValueError("string expected for value")
            
            observables.append(
                {
                    "value": obs["value"],
                    "tags": obs["tags"],
                    "type": "other"
                }
            )
    except (KeyError, ValueError):
        return JsonResponse({"error": "Invalid request"}, status=401)
    try:
        mp = get_mp(request.user)
        if misp_events == []:
            # we create a new one
            new_events = mp.create_event("Event from " + str(fir_id), tags=[]) # tags will be added later
            misp_events = new_events
        # Search for the given artifact in the given misp event
        for event in misp_events:
            # Add tags fir-incident & fir-id if the event does'nt have them
            mp.add_tags_to_event(event, list(set(tags_for_event)))
            mp.add_attributes_to_event(observables, event, comment="imported from "+ str(fir_id))
    except PyMISPError as e:
        return JsonResponse(
            {"error": "Unable to retrieve content from MISP", "details": str(e)},
            status=500,
        )
    except requests.exceptions.RequestException as e:
        return JsonResponse(
            {"error": "Unable to send data to MISP", "details": str(e)},
            status=500,
        )

    return JsonResponse({"response": "ok"})
