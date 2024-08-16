# REST framework settings
REST_FRAMEWORK = {
    # Django REST framework default pagination.
    "DEFAULT_PAGINATION_CLASS": "fir_api.pagination.CustomPageNumberPagination",
    "PAGE_SIZE": 25,
    # Any access to the API requires the user to be authenticated.
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    # If you prefer to use default TokenAuthentication using Basic Auth mechanism,
    # replace fir_api.authentication.TokenAuthentication with rest_framework.authentication.TokenAuthentication.
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "fir_api.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    # Following configuration is dedicated to fir_api.authentication.TokenAuthentication.
    "TOKEN_AUTHENTICATION_KEYWORD": "Token",
    # HTTP_X_API == "X-Api" in HTTP headers.
    "TOKEN_AUTHENTICATION_META": "HTTP_X_API",
}
