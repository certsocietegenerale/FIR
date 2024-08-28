from django_otp.decorators import otp_required
from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME

import fir.decorators


def fir_auth_required_2fa(view=None, redirect_field_name=None, login_url=None):
    if hasattr(settings, "ENFORCE_2FA") and settings.ENFORCE_2FA:
        decorator = otp_required(
            view=view,
            redirect_field_name=REDIRECT_FIELD_NAME,
            login_url=login_url,
            if_configured=False,
        )
    else:
        decorator = otp_required(
            view=view,
            redirect_field_name=REDIRECT_FIELD_NAME,
            login_url=login_url,
            if_configured=True,
        )

    return decorator


# Patch decorator to enable 2FA
fir.decorators.fir_auth_required = fir_auth_required_2fa
