from django.db import models
from django.db.models import Q
from django.utils import six
from django.apps.registry import apps

from incidents.authorization import AuthorizationManager


def get_authorization_filter(cls, user, permission=None, fields=None):
    if not hasattr(cls, '_authorization_meta'):
        raise Exception("No Authorization metadata for model {}".format(cls.__name__))
    if fields is None:
        fields = cls._authorization_meta.fields
    if isinstance(fields, six.string_types):
        fields = (fields, )
    return cls._authorization_meta.model.get_authorization_objects_filter(user, fields, permission=permission)


def has_perm(self, user, permission):
    paths = self._authorization_meta.model.get_authorization_paths(user, permission)
    if not paths.count():
        return False
    for field in self._authorization_meta.fields:
        f = self._meta.get_field(field)
        relation = getattr(self, field)
        if isinstance(f, models.ManyToManyField):
            qs_filter = reduce(lambda x, y: x | y, [Q(path__startswith=path) for path in paths])
            if relation.filter(qs_filter).count() > 0:
                return True
        elif isinstance(f, models.ForeignKey):
            if relation is not None and any(relation.path.startswith(p) for p in paths):
                return True
    return False


def has_model_perm(cls, user, permission):
    return cls._authorization_meta.model.has_model_perm(user, permission)


def tree_authorization(fields=None, tree_model='incidents.BusinessLine'):
    def set_meta(cls):
        if not hasattr(cls, '_authorization_meta'):
            class AuthorizationMeta:
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
                cls._authorization_meta.fields = (fields, )
            else:
                raise Exception("Linking field unrecognized")
        for field in cls._authorization_meta.fields:
            f = cls._meta.get_field(field)
            if not isinstance(f, (models.ForeignKey, models.ManyToManyField)):
                raise Exception("Linking field not a link")

        cls.get_authorization_filter = classmethod(get_authorization_filter)
        cls.add_to_class('has_perm', has_perm)
        cls.has_model_perm = classmethod(has_model_perm)
        AuthorizationManager().contribute_to_class(cls, 'authorization')
        return cls
    return set_meta