This module allows users to use 2FA when connecting to FIR.

The module supports the following second-factors:
- Yubikeys, which are validated against YubiCloud by default
- Webauthn
- TOTP

## Install

Follow the generic plugin installation instructions in [the FIR wiki](https://github.com/certsocietegenerale/FIR/wiki/Plugins).

Once installed, please set the following settings in `production.py`

```
ENFORCE_2FA = True  # If False, 2FA will be enabled but not enforced

LOGIN_URL = "two_factor:login"
LOGIN_REDIRECT_URL = "two_factor:profile"
MIDDLEWARE += (
    "django_otp.middleware.OTPMiddleware",
)
INSTALLED_APPS += (
    "django_otp",
    "django_otp.plugins.otp_static",
    "django_otp.plugins.otp_totp",
    "two_factor",
    "otp_yubikey",
    "two_factor.plugins.yubikey",  # <- for yubikey capability
    "two_factor.plugins.webauthn",  # <- for webauthn capability
)

# Webauthn Relying Party
TWO_FACTOR_WEBAUTHN_RP_NAME = 'YOURFIRINSTALL'
```
