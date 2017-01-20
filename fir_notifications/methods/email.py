from django import forms
from django.conf import settings
from django.core import mail
from django.utils.translation import ugettext_lazy as _

from fir_email.helpers import prepare_email_message

from fir_notifications.methods import NotificationMethod
from fir_notifications.methods.utils import request


class EmailMethod(NotificationMethod):
    use_subject = True
    use_description = True
    name = 'email'
    verbose_name = 'Email'

    def __init__(self):
        super(EmailMethod, self).__init__()
        if hasattr(settings, 'EMAIL_FROM') and settings.EMAIL_FROM is not None:
            self.server_configured = True
        if 'djembe' in settings.INSTALLED_APPS:
            self.options['certificate'] = forms.CharField(required=False, label=_('Certificate'),
                                                          widget=forms.Textarea(attrs={'cols': 60, 'rows': 15}),
                                                          help_text=_('Encryption certificate in PEM format.'))

    def send(self, event, users, instance, paths):
        messages = []
        for user, templates in users.items():
            if not self.enabled(event, user, paths) or not user.email:
                continue
            template = self._get_template(templates)
            if template is None:
                continue
            params = self.prepare(template, instance)
            email_message = prepare_email_message([user.email, ], params['subject'], params['description'],
                                                  request=request)
            messages.append(email_message)
        if len(messages):
            connection = mail.get_connection()
            connection.send_messages(messages)

    def configured(self, user):
        return super(EmailMethod, self).configured(user) and user.email is not None

    def _get_configuration(self, user):
        if not user.email:
            return {}
        try:
            from djembe.models import Identity
        except ImportError:
            return {}
        try:
            identity = Identity.objects.get(address=user.email)
        except Identity.DoesNotExist:
            return {}
        except Identity.MultipleObjectsReturned:
            identity = Identity.objects.filter(address=user.email).first()
        return {'certificate': identity.certificate}

    def form(self, *args, **kwargs):
        from fir_notifications.forms import EmailMethodConfigurationForm
        if not len(self.options):
            return None
        user = kwargs.pop('user', None)
        if user is not None:
            kwargs['initial'] = self._get_configuration(user)
            kwargs['user'] = user
        kwargs['method'] = self
        return EmailMethodConfigurationForm(*args, **kwargs)
