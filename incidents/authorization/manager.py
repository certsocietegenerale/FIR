from django.db import models
from django.utils import six


class AuthorizationManager(models.Manager):
    def for_user(self, user, permission=None):
        if isinstance(permission, six.string_types):
            permission = (permission,)
        if user.is_superuser:
            return self.get_queryset()
        if permission is not None and user.has_perms(permission):
            return self.get_queryset()
        qs_filter = self.model.get_authorization_filter(user, permission)
        return self.get_queryset().filter(qs_filter).distinct()
