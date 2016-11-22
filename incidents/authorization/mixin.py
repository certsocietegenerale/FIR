from django.contrib.auth.models import Permission
from django.db import models
from django.utils import six

from incidents.authorization import AuthorizationManager


class AuthorizationModelMixin(models.Model):
    _permissions_cache = {}
    authorization = AuthorizationManager()

    class Meta:
        abstract = True

    @classmethod
    def _get_permission_ids(cls, permission_codes):
        permissions = list()
        for perm in permission_codes:
            perm_id = cls._permissions_cache.get(perm, None)
            if perm_id is None:
                try:
                    app_label, codename = perm.split('.', 1)
                except ValueError:
                    raise ValueError("String permissions must be in"
                                     " format: 'app_label.codename' (is %r)" % perm)
                perm_obj = Permission.objects.get(content_type__app_label=app_label,
                                                  codename=codename)
                perm_id = perm_obj.pk
                cls._permissions_cache[perm] = perm_id
            permissions.append(perm_id)
        return permissions

    @classmethod
    def get_authorization_paths(cls, user, permission=None):
        if user.is_superuser:
            return cls.objects.all()
        user_obj = user
        user = user.pk
        qs_filter = {'acl__user': user}
        if permission is not None:
            if not isinstance(permission, (tuple, list)):
                permission = (permission,)
            if user_obj.has_perms(permission):
                return cls.objects.all()

            permissions = cls._get_permission_ids(permission)

            if len(permissions) == 1:
                qs_filter['acl__role__permissions'] = permissions[0]
            else:
                qs_filter['acl__role__permissions__in'] = permissions
        return cls.objects.filter(**qs_filter).distinct().values_list('path', flat=True)

    @classmethod
    def get_authorization_filter(cls, user, permission=None):
        lookup = models.Q(pk=0)
        if permission is not None and user.has_perms(permission):
            return models.Q()
        paths = cls.get_authorization_paths(user, permission=permission)
        if not paths.count():
            return lookup
        lookup |= reduce(lambda x, y: x | y, [models.Q(**{'path__startswith': path}) for path in paths])
        return lookup

    @classmethod
    def get_authorization_objects_filter(cls, user, fields, permission=None):
        paths = cls.get_authorization_paths(user, permission=permission)
        lookup = models.Q(pk=0)
        if not paths.count():
            return lookup
        if isinstance(fields, six.string_types):
            fields = (fields,)
        for field in fields:
            key = '{field}__path__startswith'.format(field=field)
            lookup |= reduce(lambda x, y: x | y, [models.Q(**{key: path}) for path in paths])
        return lookup

    def has_perm(self, user, permission):
        return self.__class__.authorization.for_user(user, permission).filter(pk=self.pk).distinct().exists()

    @classmethod
    def has_model_perm(cls, user, permission):
        return cls.authorization.for_user(user, permission).distinct().exists()
