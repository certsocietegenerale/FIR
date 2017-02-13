from collections import OrderedDict

from django.apps import apps
from django.utils.encoding import python_2_unicode_compatible
from django.conf import settings

from fir_notifications.methods.email import EmailMethod
from fir_notifications.methods.jabber import XmppMethod


@python_2_unicode_compatible
class RegisteredEvent(object):
    def __init__(self, name, model, verbose_name=None, section=None):
        self.name = name
        if section is None:
            section = apps.get_app_config(model._meta.app_label).verbose_name
        self.section = section
        if verbose_name is None:
            verbose_name = name
        self.verbose_name = verbose_name

    def __str__(self):
        return self.verbose_name


class Notifications(object):
    def __init__(self):
        self.methods = OrderedDict()
        self.events = OrderedDict()

    def register_method(self, method, name=None, verbose_name=None):
        """
        Registers a notification method, instance of a subclass of `fir_notifications.methods.NotificationMethod`
        Args:
            method: instance of the notification method
            name: overrides the instance.name
            verbose_name: overrides the instance.verbose_name
        """
        if not method.server_configured:
            return
        if name is not None:
            method.name = name
        if verbose_name is not None:
            method.verbose_name = verbose_name
        if not method.verbose_name:
            method.verbose_name = method.name
        self.methods[method.name] = method

    def register_event(self, name, signal, model, callback, verbose_name=None, section=None):
        """
        Registers a notification event
        Args:
            name: event name
            signal: Django signal to listen to
            model: Django model sending the signal (and event)
            callback: Django signal handler
            verbose_name: verbose name of the event
            section: section in the user preference panel (default model application name)
        """
        if name in settings.NOTIFICATIONS_DISABLED_EVENTS:
            return
        if verbose_name is None:
            verbose_name = name
        self.events[name] = RegisteredEvent(name, model, verbose_name=verbose_name, section=section)

        signal.connect(callback, sender=model, dispatch_uid="fir_notifications.{}".format(name))

    def get_event_choices(self):
        results = OrderedDict()
        for obj in self.events.values():
            if obj.section not in results:
                results[obj.section] = list()
            results[obj.section].append((obj.name, obj.verbose_name))
        return [(section, sorted(choices)) for section, choices in results.items()]

    def get_method_choices(self):
        return sorted([(obj.name, obj.verbose_name) for obj in self.methods.values()])

    def get_methods(self):
        return self.methods.values()


registry = Notifications()
registry.register_method(EmailMethod())
registry.register_method(XmppMethod())
