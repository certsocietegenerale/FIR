import requests
import logging
import json
from requests.exceptions import RequestException, ConnectionError, Timeout
from django.test import RequestFactory
from rest_framework.renderers import JSONRenderer

from django import forms
from django.utils.translation import gettext_lazy as _

from fir_notifications.methods import NotificationMethod
from fir_notifications.methods.utils import request as external_url


class WebhookMethod(NotificationMethod):
    use_subject = True
    use_short_description = True
    use_description = True
    name = "webhook"
    verbose_name = "Webhook"
    options = {
        "url": forms.CharField(max_length=256, label=_("URL")),
        "token": forms.CharField(max_length=256, label=_("Token")),
    }

    def __init__(self):
        super(WebhookMethod, self).__init__()
        self.server_configured = True

    def _get_url(self, user):
        return self._get_configuration(user).get("url", None)

    def _get_token(self, user):
        return self._get_configuration(user).get("token", None)

    @staticmethod
    def _prepare_json(event, instance, user):
        from fir_api.serializers import IncidentSerializer

        event_type = event.split(":")[0]
        url = external_url.build_absolute_uri(f"/{event_type}s/{instance.id}/")

        request = RequestFactory().get("/")
        request.user = user
        serializer = IncidentSerializer(instance, context={"request": request})
        data = json.loads(JSONRenderer().render(serializer.data))

        data["url"] = url
        data["event"] = event
        return data

    def send(self, event, users, instance, paths):
        for user, templates in users.items():
            url = self._get_url(user)
            token = self._get_token(user)
            if not self.enabled(event, user, paths) or not url:
                continue

            try:
                requests.post(
                    url,
                    headers={"Authorization": f"Token {token}"},
                    json=self._prepare_json(event, instance, user),
                    allow_redirects=True,
                )
            except (RequestException, ConnectionError, Timeout):
                logging.getLogger("FIR").error(
                    f"Webhook to {url} failed", exc_info=True
                )

    def configured(self, user):
        return super(WebhookMethod, self).configured(user) and self._get_url(user)
