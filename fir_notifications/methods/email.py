import markdown2
from django import forms
from django.conf import settings
from django.core import mail
from django.utils.translation import ugettext_lazy as _


from fir_notifications.methods import NotificationMethod, request
from fir_plugins.links import registry as link_registry


class EmailMethod(NotificationMethod):
    use_subject = True
    use_description = True
    name = 'email'
    verbose_name = 'Email'

    def __init__(self):
        super(EmailMethod, self).__init__()
        if hasattr(settings, 'NOTIFICATIONS_EMAIL_FROM'):
            self.server_configured = True
        if 'djembe' in settings.INSTALLED_APPS:
            self.options['certificate'] = forms.CharField(required=False,
                                                          widget=forms.Textarea(attrs={'cols': 60, 'rows': 15}),
                                                          help_text=_('Encryption certificate in PEM format.'))

    def send(self, event, users, instance, paths):
        from_address = settings.NOTIFICATIONS_EMAIL_FROM
        reply_to = {}
        if hasattr(settings, 'NOTIFICATIONS_EMAIL_REPLY_TO'):
            reply_to = {'Reply-To': settings.NOTIFICATIONS_EMAIL_REPLY_TO,
                        'Return-Path': settings.NOTIFICATIONS_EMAIL_REPLY_TO}
        messages = []
        for user, templates in users.items():
            if not self.enabled(event, user, paths) or not user.email:
                continue
            template = self._get_template(templates)
            if template is None:
                continue
            params = self.prepare(template, instance)
            e = mail.EmailMultiAlternatives(
                subject=params['subject'],
                body=params['description'],
                from_email=from_address,
                to=[user.email, ],
                headers=reply_to
            )
            e.attach_alternative(markdown2.markdown(params['description'], extras=["link-patterns"],
                                                    link_patterns=link_registry.link_patterns(request), safe_mode=True),
                                 'text/html')
            messages.append(e)
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
