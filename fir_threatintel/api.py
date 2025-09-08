import requests
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from rest_framework import viewsets, status, serializers, mixins
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import APIException
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from django_filters.rest_framework import CharFilter, FilterSet, DjangoFilterBackend

from fir_threatintel.models import YetiProfile
from fir_api.permissions import CanViewIncident, CanWriteIncident
from fir_api.renderers import FilterButtonBrowsableAPIRenderer
from fir_api.filter_backends import DummyFilterBackend


class YetiFilter(FilterSet):
    observable = CharFilter(label=_("observable"))


class YetiSerializer(serializers.Serializer):
    observables = serializers.JSONField(
        initial=[{"value": "example.com", "tags": ["malware"], "fid": "FIR-1234"}]
    )


class YetiViewSet(
    viewsets.GenericViewSet,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
):
    """
    Interact with Yeti observables
    """

    serializer_class = YetiSerializer
    permission_classes = [IsAuthenticated, CanViewIncident | CanWriteIncident]
    queryset = YetiProfile.objects.none()
    filterset_class = YetiFilter
    filter_backends = [DummyFilterBackend]
    renderer_classes = [JSONRenderer, FilterButtonBrowsableAPIRenderer]

    def get_yp(self, user):
        yp, created = YetiProfile.objects.get_or_create(user_id=user)
        # Allow Yeti connection to be defined via global settings
        if (
            not yp.endpoint
            and not yp.api_key
            and hasattr(settings, "YETI_URL")
            and hasattr(settings, "YETI_APIKEY")
        ):
            yp.endpoint = settings.YETI_URL
            yp.api_key = settings.YETI_APIKEY
        if not yp.endpoint or not yp.api_key:
            raise APIException(
                _(
                    "Yeti URL or API key missing. Please set them on your profile page or in FIR config."
                )
            )

        auth = requests.post(
            yp.endpoint + "/api/v2/auth/api-token",
            headers={"X-Yeti-Apikey": yp.api_key},
        )
        auth.raise_for_status()
        yp.access_token = "Bearer " + auth.json()["access_token"]
        return yp

    def list(self, request, *args, **kwargs):
        self.filter_queryset(self.get_queryset())
        observables = request.query_params.getlist("observable")

        if not observables:
            raise APIException(
                _(
                    "No observable provided. Please provide one or multiple observable as GET parameter."
                )
            )

        try:
            yp = self.get_yp(request.user)
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
            for obs in observables:
                if all([a["value"] != obs for a in results["known"]]):
                    results["unknown"].append(obs)
        except (requests.exceptions.RequestException, ValueError) as e:
            return Response(
                {"error": _("Unable to retrieve content from Yeti"), "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return Response(results)

    def create(self, request, *args, **kwargs):
        yp = self.get_yp(request.user)
        try:
            req = request.data.get("observables", [])
            for obs in req:
                if not isinstance(obs, dict):
                    raise ValueError("list of dict expected for observables")
                if not isinstance(obs.get("tags", False), list):
                    raise ValueError("list expected for tags")
                for tag in obs.get("tags", []):
                    if not isinstance(tag, str):
                        raise ValueError("string expected for each tag")
                if not isinstance(obs.get("value", False), str):
                    raise ValueError("string expected for value")
                if not isinstance(obs.get("fid", False), str):
                    raise ValueError("string expected for fid")

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
                    obs_id = observable_creation.json()["added"][0]["id"]

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
            return Response(
                {"error": _("Unable to retrieve content from Yeti"), "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except (KeyError, ValueError) as e:
            return Response(
                {"error": _("Invalid request"), "detail": str(e)},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        return Response({"response": "ok"})
