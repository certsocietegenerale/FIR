from mozilla_django_oidc.contrib.drf import OIDCAuthentication
from incidents.models import User, Log
from django.core.exceptions import SuspiciousOperation
from rest_framework import exceptions


class APIOIDCAuthentication(OIDCAuthentication):
    def authenticate(self, request):
        try:
            access_token = self.get_access_token(request)
            if not access_token:
                return None

            claims = self.backend.verify_token(access_token)

            if not self.backend.verify_claims(claims, is_api=True):
                raise SuspiciousOperation("Claims verification failed")

            claims_mapping = self.backend.get_settings("AUTH_OICD_API_CLAIM_MAP")

            name = self.backend.jsonpath_get(claims_mapping, claims, "username")[:30]
            roles = self.backend.jsonpath_get(
                claims_mapping, claims, "roles", multi=True
            )

            user = self.backend.UserModel.objects.filter(username=name)
            if not user:
                if self.backend.get_settings("OIDC_CREATE_USER", True):
                    user = [self.backend.UserModel.objects.create_user(name)]
                    Log.log("User account created", user[0])
                else:
                    return SuspiciousOperation("User does not exist.")

            user = self.backend.set_roles(user[0], roles)

            if callable(
                self.backend.get_settings("AUTH_OIDC_CLAIM_MAP_FUNCTION", False)
            ):
                user = self.backend.get_settings("AUTH_OIDC_CLAIM_MAP_FUNCTION")(
                    user, claims
                )
            user.save()

        except Exception as e:
            raise exceptions.AuthenticationFailed(e)

        return user, access_token
