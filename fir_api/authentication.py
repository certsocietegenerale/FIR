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

        auth = auth.split(' ')
        if auth[0].lower() != self.keyword.lower().encode():
            return None
        
        if len(auth) == 1:
            msg = _('Invalid token header. No credentials provided.')
            raise exceptions.AuthenticationFailed(msg)
        elif len(auth) > 2:
            msg = _('Invalid token header. Token string should not contain spaces.')
            raise exceptions.AuthenticationFailed(msg)

        try:
            token = auth[1].decode()
        except UnicodeError:
            msg = _('Invalid token header. Token string should not contain invalid characters.')
            raise exceptions.AuthenticationFailed(msg)

        return self.authenticate_credentials(token)
