from json import dumps as json_dumps
from urllib2 import urlopen, Request

from django import forms
from django.utils.translation import ugettext_lazy as _

from fir_notifications.methods import NotificationMethod


class WebhookMethod(NotificationMethod):
    use_subject = True
    use_short_description = True
    use_description = True
    name = 'webhook'
    verbose_name = 'Webhook'
    options = {
        'url': forms.CharField(max_length=256, label=_('URL')),
        'token': forms.CharField(max_length=256, label=_('Token'))
    }

    def __init__(self):
        super(WebhookMethod, self).__init__()
        self.server_configured = True

    def _get_url(self, user):
        return self._get_configuration(user).get('url', None)

    def _get_token(self, user):
        return self._get_configuration(user).get('token', None)

    @staticmethod
    def _prepare_json(token, event, instance):
        date = getattr(instance, 'date', None)
        timestamp = int(date.strftime('%s')) if date is not None else None
        return json_dumps({
            'token': token,
            'event': event,
            'id': getattr(instance, 'id', None),
            'subject': getattr(instance, 'subject', None),
            'status': getattr(instance, 'status', None),
            'category_id': getattr(instance, 'category_id', None),
            'category_name': getattr(getattr(instance, 'category', None), 'name', None),
            'confidentiality': getattr(instance, 'confidentiality', None),
            'timestamp': timestamp,
            'description': getattr(instance, 'description', None),
            'detection_id': getattr(instance, 'detection_id', None),
            'detection_name': getattr(getattr(instance, 'detection', None), 'name', None),
            'is_incident': getattr(instance, 'is_incident', False),
            'is_major': getattr(instance, 'is_major', False),
            'is_starred': getattr(instance, 'is_starred', False),
            'opened_by_id': getattr(instance, 'opened_by_id', None),
            'opened_by_name': getattr(getattr(instance, 'opened_by', None), 'username', None),
            'plan_id': getattr(instance, 'plan_id', None),
            'plan_name': getattr(getattr(instance, 'plan', None), 'name', None),
            'severity': getattr(instance, 'severity', None)
        })

    def send(self, event, users, instance, paths):
        for user, templates in users.items():
            url = self._get_url(user)
            token = self._get_token(user)
            if not self.enabled(event, user, paths) or not url:
                continue
            request = Request(url)
            request.add_header('Content-Type', 'application/json')
            urlopen(request, self._prepare_json(token, event, instance))

    def configured(self, user):
        return super(WebhookMethod, self).configured(user) and self._get_url(user)
