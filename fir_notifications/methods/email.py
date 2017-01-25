from django.conf import settings
from django.core import mail

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
