from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class NotificationsConfig(AppConfig):
    name = 'fir_notifications'
    verbose_name = _('Notifications')

    def ready(self):
        pass
