from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class NotificationsConfig(AppConfig):
    name = 'fir_notifications'
    verbose_name = _('Notifications')

    def ready(self):
        pass
