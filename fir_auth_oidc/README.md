This module allows users to authenticate to FIR using an OpenID Connect provider.

Two OpenID connect flows are supported: `authorization code` (for user authentication) and `client credentials` (for API/machine-to-machine authentication).

## Install

Follow the generic plugin installation instructions in [the FIR wiki](https://github.com/certsocietegenerale/FIR/wiki/Plugins).

# Usage

To enable OIDC authentication, the first step is to obtain a client ID & client secret from your OpenID Connect Provider (OP).

When generating these, you may be requested to enter a redirect URI. The redirect URI of FIR is `http(s)://YOURFIRINSTALL/oidc/callback/`


Then, you need to add (and edit according to your setup) the following settings to `production.py`:

```
# For the sake of example, the settings below are pre-configured for Azure Entra ID. FIR is compatible with any OIDC provider.

OIDC_OP_JWKS_ENDPOINT = "https://login.microsoftonline.com/<AzureTenantID>/discovery/v2.0/keys"
OIDC_OP_AUTHORIZATION_ENDPOINT = "https://login.microsoftonline.com/<AzureTenantID>/oauth2/v2.0/authorize"
OIDC_OP_TOKEN_ENDPOINT = "https://login.microsoftonline.com/<AzureTenantID>/oauth2/v2.0/token"
OIDC_OP_USER_ENDPOINT = "https://graph.microsoft.com/beta/me"  # userinfo endpoint

OIDC_RP_SCOPES = "openid profile email User.Read api://<FIRclientID>/FIR"  # To create a scope in Azure: App Registration > Expose an API > Add a scope
OIDC_RP_CLIENT_ID = "11111111-1111-1111-1111-111111111111"
OIDC_RP_CLIENT_SECRET = ""  # To create a client secret in Azure: App Registration > Certificates & Secrets > New client secret


# Define which OIDC claim should be used to retrieve user attributes. JSONpath can be used here
AUTH_OICD_CLAIM_MAP = {
    "email": "email",
    "first_name": "given_name",
    "last_name": "family_name",
    "username": "preferred_username",  # use "preferred_username" claim to retrieve username
    "roles": "roles",
}

# API access: Define which OIDC claim should be used to retrieve attributes from a service principal access_token. JSONpath can be used here
AUTH_OICD_API_CLAIM_MAP = {
    "username": "appid",
    "roles": "roles",
}

## Define which OIDC role should correspond to which Django group
## To create a role in Azure: App Registration > App roles > Create app role
AUTH_OIDC_GROUP_MAP = {
    "FIR.globaleditor": ["Incident handlers"],
    "FIR.entity.audit": ["Incident viewers"],
}

## Define which flag should each user have depending on its OIDC role
## To create a role in Azure: App Registration > App roles > Create app role
AUTH_OIDC_FLAG_MAP = {
    "FIR.admins": ["is_superuser", "is_active", "is_staff"],
    "FIR.businessline1": ["is_active"],
    "FIR.businessline2": ["is_active"],
}

## Define which permission on each business line should each user have depending on its OIDC role
## To create a role in Azure: App Registration > App roles > Create app role
AUTH_OIDC_ROLE_MAP = {
    "FIR.entity.businessline1": [
        ("Demo BusinessLine 1", "Incident handlers"),
    ],
    "FIR.entity.businessline2": [
        ("Sub BL 1", "Incident viewers"),
        ("Demo BusinessLine 2", "Incident handlers"),
    ],
}

LOGIN_URL = "oidc_authentication_init"
LOGIN_REDIRECT_URL_FAILURE = "/account/login/"
OIDC_TOKEN_USE_BASIC_AUTH = True
OIDC_RP_SIGN_ALGO = "RS256"
OIDC_STORE_ACCESS_TOKEN = True
OIDC_STORE_ID_TOKEN = True
OIDC_CALLBACK_CLASS = "fir_auth_oidc.views.SessionOIDCAuthenticationCallbackView"
AUTHENTICATION_BACKENDS += (
    "fir_auth_oidc.backend.ClaimMappingOIDCAuthenticationBackend",
)
INSTALLED_APPS += ("mozilla_django_oidc",)
REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] += (
    "fir_auth_oidc.api.APIOIDCAuthentication",
)

# If you wish to view user claims as seen by FIR, you can enable debug logs:
LOGGING["loggers"]["mozilla_django_oidc"] = {"handlers": ["console"], "level": "DEBUG"}
```
