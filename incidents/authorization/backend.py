"""
Authentication backend for Django

 Supports object based permissions

"""
from django.db import models

import inspect


def check_object_support(obj):
    """
    Returns the permission check method for supported methods and classes
    """
    if isinstance(obj, models.Model) and hasattr(obj, 'has_perm'):
        return obj.has_perm
    if inspect.isclass(obj) and issubclass(obj, models.Model) and hasattr(obj, 'has_model_perm'):
        return obj.has_model_perm
    return False


def check_support(user_obj, obj):
    """
    Combination of ``check_object_support`` and user check
    """
    if user_obj.is_authenticated() and user_obj.is_active:
        return check_object_support(obj)
    return False


class ObjectPermissionBackend(object):
    supports_object_permissions = True
    supports_anonymous_user = True
    supports_inactive_user = True

    def authenticate(self, username, password):
        return None

    def has_perm(self, user_obj, perm, obj=None):
        # check if user_obj and object are supported
        if obj is None:
            return False
        test_func = check_support(user_obj, obj)
        if not test_func:
            return False
        if user_obj.has_perm(perm):
            return True
        return test_func(user_obj, perm)