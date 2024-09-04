# -*- coding: utf-8 -*-
from functools import wraps

from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import login_required


def fir_auth_required(view=None, redirect_field_name=None, login_url=None):
    decorator = login_required(
        function=view, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None
    )

    return decorator
