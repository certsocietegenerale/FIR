## Install

Follow the generic plugin installation instructions in [the FIR wiki](https://github.com/certsocietegenerale/FIR/wiki/Plugins).

Then, edit the `fir/settings.py` and set :

```python
REST_FRAMEWORK = {
    # Django REST framework default pagination.
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 100,

    # Any access to the API requires the user to be authenticated.
    'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.IsAuthenticated',),

    # If you prefer to use default TokenAuthentication using Basic Auth mechanism,
    # replace fir_api.authentication.TokenAuthentication with rest_framework.authentication.TokenAuthentication.
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'fir_api.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication'),

    # Following configuration is dedicated to fir_api.authentication.TokenAuthentication.
    'TOKEN_AUTHENTICATION_KEYWORD': 'Token',

    # HTTP_X_API == "X-Api" in HTTP headers.
    'TOKEN_AUTHENTICATION_META': 'HTTP_X_API',
}
```

## Usage

The `fir_api` plugin allows you to interact with FIR programmatically.
The API is pretty much self documented in the dedicated web interface available at `http(s)://YOURFIRINSTALL/api/`.

### Authentication

You need to be authenticated in order to use the API.
It will accept session or token based authentication.
Tokens can be managed in the administration interface and should be specified as a request header.
Example:

```
X-Api: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
```
