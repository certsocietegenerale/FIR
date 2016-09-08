"""
Authentication backend for Django

 Supports object based permissions

"""
from django.db import models


def check_object_support(obj):
    """
    Returns ``True`` if given ``obj`` is supported
    """
    # Backend checks only object permissions (isinstance implies that obj
    # is not None)
    # Backend checks only permissions for Django models
    return isinstance(obj, models.Model) and hasattr(obj, 'has_perm')


def check_support(user_obj, obj):
    """
    Combination of ``check_object_support`` and ``check_user_support``
    """
    obj_support = check_object_support(obj)
    return obj_support and user_obj.is_authenticated()


class ObjectPermissionBackend(object):
    supports_object_permissions = True
    supports_anonymous_user = True
    supports_inactive_user = True

    def authenticate(self, username, password):
        return None

    def has_perm(self, user_obj, perm, obj=None):
        # check if user_obj and object are supported
        if not check_support(user_obj, obj):
            return False
        if user_obj.has_perm(perm):
            return True
        return obj.has_perm(user_obj, perm)