from collections import OrderedDict

from fir_notifications.methods.email import EmailMethod


class Notifications(object):
    def __init__(self):
        self.methods = OrderedDict()
        self.events = OrderedDict()

    def register_method(self, method, name=None, verbose_name=None):
        if not method.server_configured:
            return
        if name is not None:
            method.name = name
        if verbose_name is not None:
            method.verbose_name = verbose_name
        if not method.verbose_name:
            method.verbose_name = method.name
        self.methods[method.name] = method

    def register_event(self, name, signal, model, callback, verbose_name=None):
        if verbose_name is None:
            verbose_name = name
        self.events[name] = verbose_name

        signal.connect(callback, sender=model, dispatch_uid="fir_notifications.{}".format(name))

    def get_event_choices(self):
        return self.events.items()

    def get_method_choices(self):
        return [(obj.name, obj.verbose_name) for obj in self.methods.values()]

    def get_methods(self):
        return self.methods.values()


registry = Notifications()
registry.register_method(EmailMethod())
