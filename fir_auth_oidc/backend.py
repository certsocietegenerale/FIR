#!/usr/bin/python3
import json
import base64
import logging
from django.contrib.auth.models import User, Group
from django.core.exceptions import ImproperlyConfigured, SuspiciousOperation
from mozilla_django_oidc.auth import OIDCAuthenticationBackend
from jsonpath_ng.ext import parse
from jsonpath_ng.exceptions import JSONPathError
import incidents.models


class ClaimMappingOIDCAuthenticationBackend(OIDCAuthenticationBackend):
    def verify_claims(self, claims, is_api=False):
        claims = self.get_claims(claims, log=True)

        claims_mapping = self.get_settings("AUTH_OICD_CLAIM_MAP")
        if is_api:
            claims_mapping = self.get_settings("AUTH_OICD_API_CLAIM_MAP")

        if callable(self.get_settings("AUTH_OIDC_CLAIM_MAP_FUNCTION", False)):
            # users permissions are handled through a custom function
            return True

        role_map = self.get_settings("AUTH_OIDC_ROLE_MAP")
        group_map = self.get_settings("AUTH_OIDC_GROUP_MAP")
        flag_map = self.get_settings("AUTH_OIDC_FLAG_MAP")

        roles = self.jsonpath_get(claims_mapping, claims, "roles", multi=True)

        has_any_role = any([role_map.get(role, False) for role in roles])
        has_any_flag = any([flag_map.get(role, False) for role in roles])
        has_any_group = any([group_map.get(role, False) for role in roles])

        return has_any_role or has_any_flag or has_any_group

    def get_claims(self, userinfo_claims, log=False):
        try:
            id_claims = self.request.session["oidc_id_token"].split(".")[1]
            claims = json.loads(base64.b64decode(id_claims + "=="))
        except:
            claims = {}

        try:
            access_claims = self.request.session["oidc_access_token"].split(".")[1]
            decoded_claims = json.loads(base64.b64decode(access_claims + "=="))
            claims.update(decoded_claims)
        except:
            pass

        claims.update(userinfo_claims)
        if log:
            logging.getLogger("mozilla_django_oidc").debug(f"user claims: {claims}")
        return claims

    def filter_users_by_claims(self, claims):
        claims = self.get_claims(claims)

        email = self.jsonpath_get(
            self.get_settings("AUTH_OICD_CLAIM_MAP"), claims, "email"
        )
        try:
            return [User.objects.get(email=email)]
        except User.DoesNotExist:
            pass
        return self.UserModel.objects.none()

    def create_user(self, claims):
        return self.update_user(None, claims)

    def jsonpath_get(self, mapping, claims, elem_to_get, multi=False):
        claim_value = []
        jsonpath = mapping[elem_to_get]

        try:
            for found_claim in parse(jsonpath).find(claims):
                if isinstance(found_claim.value, str):
                    claim_value += found_claim.value.split(" ")
                elif isinstance(found_claim.value, list):
                    claim_value += found_claim.value
                else:
                    claim_value.append(found_role.value)
        except JSONPathError as e:
            raise ImproperlyConfigured(
                f"JSON path of claim '%s' is invalid: '%s'. If you are a FIR administrator, please check the claim path in config files."
                % (elem_to_get, e.args[0])
            )

        if multi:
            return claim_value
        elif len(claim_value) >= 1:
            return claim_value[0]
        elif elem_to_get == "roles":
            raise SuspiciousOperation("No role found for user.")
        else:
            raise ImproperlyConfigured(
                "Unable to find '%s' in user claims ('%s')\n" % (jsonpath, claims)
            )

    def set_roles(self, user, roles):
        role_mapping = self.get_settings("AUTH_OIDC_ROLE_MAP")
        flag_mapping = self.get_settings("AUTH_OIDC_FLAG_MAP")
        group_mapping = self.get_settings("AUTH_OIDC_GROUP_MAP")

        user.groups.clear()
        user.is_staff = False
        user.is_superuser = False
        user.is_active = False
        incidents.models.AccessControlEntry.objects.filter(user=user).delete()

        for role in roles:
            flags = flag_mapping.get(role, [])
            for flag in flags:
                setattr(user, flag, True)

            groups = group_mapping.get(role, [])
            for group in groups:
                try:
                    group = Group.objects.get(name=group)
                    user.groups.add(group)
                except Group.DoesNotExist:
                    pass

            acls = role_mapping.get(role, [])
            for acl in acls:
                try:
                    bl = incidents.models.BusinessLine.objects.get(name=acl[0])
                    group = Group.objects.get(name=acl[1])
                    incidents.models.AccessControlEntry.objects.get_or_create(
                        user=user, business_line=bl, role=group
                    )
                except (incidents.models.BusinessLine.DoesNotExist, Group.DoesNotExist):
                    pass

        return user

    def update_user(self, user, claims):
        claims = self.get_claims(claims)

        claims_mapping = self.get_settings("AUTH_OICD_CLAIM_MAP")

        email = self.jsonpath_get(claims_mapping, claims, "email")
        username = self.jsonpath_get(claims_mapping, claims, "username")[:30]
        if user is None and self.get_settings("OIDC_CREATE_USER", True):
            user = self.UserModel.objects.create_user(username, email=email)
            user.save()
        elif user is None:
            return SuspiciousOperation("User does not exist.")

        user.first_name = self.jsonpath_get(claims_mapping, claims, "first_name")
        user.last_name = self.jsonpath_get(claims_mapping, claims, "last_name")
        user.email = email

        roles = self.jsonpath_get(claims_mapping, claims, "roles", multi=True)
        user = self.set_roles(user, roles)

        if callable(self.get_settings("AUTH_OIDC_CLAIM_MAP_FUNCTION", False)):
            user = self.get_settings("AUTH_OIDC_CLAIM_MAP_FUNCTION")(user, claims)
        user.save()

        incidents.models.Profile.objects.get_or_create(user=user)

        return user
