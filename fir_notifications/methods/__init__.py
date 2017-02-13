import json

from django.template import Template, Context


class NotificationMethod(object):
    """
    Base class for a notification method.

    Subclass this class to create a new notification method
    """
    name = 'method_template'
    verbose_name = 'Notification method template'
    # This notification method uses the template subject
    use_subject = False
    # This notification method uses the template short description
    use_short_description = False
    # This notification method uses the template description
    use_description = False
    # Method configuration options (dict: index_name: form field instance)
    options = {}

    def __init__(self):
        self.server_configured = False

    def enabled(self, event, user, paths):
        """
        Checks if this method is enabled for an event and its business lines in the user preferences
        """
        from fir_notifications.models import NotificationPreference
        try:
            preference = NotificationPreference.objects.get(event=event, method=self.name, user=user)
        except NotificationPreference.DoesNotExist:
            return False
        for bl in preference.business_lines.all():
            if any([bl.path.startswith(path) for path in paths]):
                return True
        return False

    @staticmethod
    def prepare(template_object, instance, extra_context=None):
        """
        Renders a notification template (subject, description, short description) for a given instance
        which fired an event
        """
        if extra_context is None:
            extra_context = {}
        extra_context.update({'instance': instance})
        context = Context(extra_context)
        return {
            'subject': Template(getattr(template_object, 'subject', "")).render(context),
            'short_description': Template(getattr(template_object, 'short_description', "")).render(context),
            'description': Template(getattr(template_object, 'description', "")).render(context)
        }

    def _get_template(self, templates):
        """
        Choose the first matching template in a template list
        """
        for template in templates:
            if self.use_subject and template.subject is None:
                continue
            if self.use_short_description and template.short_description is None:
                continue
            if self.use_description and template.description is None:
                continue
            return template
        return None

    def _get_configuration(self, user):
        """
        Retrieve user configuration for this method as a dict
        """
        from fir_notifications.models import MethodConfiguration
        try:
            string_config = MethodConfiguration.objects.get(user=user, key=self.name).value
        except MethodConfiguration.DoesNotExist:
            return {}
        try:
            return json.loads(string_config)
        except:
            return {}

    def send(self, event, users, instance, paths):
        raise NotImplementedError

    def configured(self, user):
        """
        Checks if this method is configured for a given user
        """
        return self.server_configured and user.is_active

    def form(self, *args, **kwargs):
        """
        Returns this method configuration form
        """
        from fir_notifications.forms import MethodConfigurationForm
        if not len(self.options):
            return None
        user = kwargs.pop('user', None)
        if user is not None:
            kwargs['initial'] = self._get_configuration(user)
            kwargs['user'] = user
        kwargs['method'] = self
        return MethodConfigurationForm(*args, **kwargs)
