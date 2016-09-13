from django.core.exceptions import PermissionDenied
from django.db import models
from django.db.models import Q
from django.utils import six
from django.apps.registry import apps

from incidents.authorization import AuthorizationManager


def get_authorization_filter(cls, user, permission=None, fields=None):
    if not hasattr(cls, '_authorization_meta'):
        raise Exception("No Authorization metadata for model {}".format(cls.__name__))
    if isinstance(permission, six.string_types):
        permission = [permission, ]

    if fields is None:
        fields = cls._authorization_meta.fields
    if isinstance(fields, six.string_types):
        fields = (fields,)
    objects =  cls._authorization_meta.model.get_authorization_objects_filter(user, fields, permission=permission)
    if cls._authorization_meta.owner_field and cls._authorization_meta.owner_permission and \
                    cls._authorization_meta.owner_permission in permission:
        objects |= Q(**{cls._authorization_meta.owner_field: user.pk})
    return objects


def has_perm(self, user, permission):
    if user.is_superuser:
        return True
    if isinstance(permission, six.string_types):
        permission = [permission, ]
    if user.has_perms(permission):
        return True
    if self._authorization_meta.owner_field and self._authorization_meta.owner_permission and \
       self._authorization_meta.owner_permission in permission and \
       user.pk == getattr(self, self._authorization_meta.owner_field).pk:
        return True
    paths = self._authorization_meta.model.get_authorization_paths(user, permission)
    if not paths.count():
        return False
    for field in self._authorization_meta.fields:
        f = self._meta.get_field(field)
        relation = getattr(self, field)
        if isinstance(f, models.ManyToManyField):
            qs_filter = reduce(lambda x, y: x | y, [Q(path__startswith=path) for path in paths])
            if relation.filter(qs_filter).distinct().exists():
                return True
        elif isinstance(f, models.ForeignKey):
            if relation is not None and any(relation.path.startswith(p) for p in paths):
                return True
    return False


def has_model_perm(cls, user, permission):
    model_perm =  cls._authorization_meta.model.has_model_perm(user, permission)
    if not model_perm and cls._authorization_meta.owner_field and cls._authorization_meta.owner_permission and \
                    cls._authorization_meta.owner_permission in permission:
        return cls.objects.filter(**{cls._authorization_meta.owner_field: user.pk}).distinct().exists()
    return model_perm


def tree_authorization(fields=None, tree_model='incidents.BusinessLine', owner_field=None, owner_permission=None):
    def set_meta(cls):
        if not hasattr(cls, '_authorization_meta'):
            class AuthorizationMeta:
                owner_field = None
                owner_permission = None
                fields = ('business_lines',)
                tree_model = None

                @property
                def model(self):
                    if isinstance(self.tree_model, six.string_types):
                        self.tree_model = apps.get_model(*self.tree_model.split('.'))
                    return self.tree_model

            AuthorizationMeta.tree_model = tree_model
            cls._authorization_meta = AuthorizationMeta()
        if fields is not None:
            if isinstance(fields, (tuple, list)):
                cls._authorization_meta.fields = fields
            elif isinstance(fields, six.string_types):
                cls._authorization_meta.fields = (fields,)
            else:
                raise Exception("Linking field unrecognized")
        for field in cls._authorization_meta.fields:
            f = cls._meta.get_field(field)
            if not isinstance(f, (models.ForeignKey, models.ManyToManyField)):
                raise Exception("Linking field not a link")
        if isinstance(owner_permission, six.string_types) and isinstance(owner_field, six.string_types):
            f = cls._meta.get_field(owner_field)
            if isinstance(f, models.ForeignKey):
                cls._authorization_meta.owner_permission = owner_permission
                cls._authorization_meta.owner_field = owner_field
        cls.get_authorization_filter = classmethod(get_authorization_filter)
        cls.add_to_class('has_perm', has_perm)
        cls.has_model_perm = classmethod(has_model_perm)
        AuthorizationManager().contribute_to_class(cls, 'authorization')
        return cls

    return set_meta
