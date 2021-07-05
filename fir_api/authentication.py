from rest_framework import authentication, exceptions
from rest_framework.settings import api_settings

class TokenAuthentication(authentication.TokenAuthentication):
    """
    Simple token based authentication.
    Clients should authenticate by passing the token key in the "Authorization"
    HTTP header, prepended with the string "Token ".  For example:
        X-Api: Token 401f7ac837da42b97f613d789819ff93537bee6a
    """

    keyword = api_settings.user_settings['TOKEN_AUTHENTICATION_KEYWORD']

    def authenticate(self, request):
        meta = api_settings.user_settings['TOKEN_AUTHENTICATION_META']
        auth = request.META.get(meta)        
        if not auth:
            return None
        try:
            auth_keyword, auth_token = auth.split(' ')
        except ValueError:
            msg = "Invalid token header. Header must be defined the following way: 'Token hexstring'"
            raise exceptions.AuthenticationFailed(msg)
        if auth_keyword.lower() != self.keyword.lower():
            msg = f"Provided keyword '{auth_keyword.lower()}' does not match defined one '{self.keyword.lower()}'"
            raise exceptions.AuthenticationFailed(msg)
        return self.authenticate_credentials(auth_token)
