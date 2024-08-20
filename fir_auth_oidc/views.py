from mozilla_django_oidc.views import OIDCAuthenticationCallbackView
from incidents.views import init_session


class SessionOIDCAuthenticationCallbackView(OIDCAuthenticationCallbackView):
    def login_success(self):
        ret = super().login_success()
        init_session(self.request)
        return ret
