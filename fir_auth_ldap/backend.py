#!/usr/bin/python3
from django_auth_ldap.backend import LDAPBackend
from django.contrib.auth.models import Group
from django.conf import settings
import incidents.models


class AttributesLDAPBackend(LDAPBackend):
    def authenticate(self, *args, **kwargs):
        user = super().authenticate(*args, **kwargs)
        if user:
            incidents.models.AccessControlEntry.objects.filter(user=user).delete()

            role_map = {
                k.lower(): v for k, v in settings.AUTH_LDAP_USER_ROLE_MAP.items()
            }
            for group in user.ldap_user._get_groups()._get_group_infos():
                acls = role_map.get(group[0], [])
                for acl in acls:
                    try:
                        bl = incidents.models.BusinessLine.objects.get(name=acl[0])
                        group = Group.objects.get(name=acl[1])
                        incidents.models.AccessControlEntry.objects.get_or_create(
                            user=user, business_line=bl, role=group
                        )
                    except (
                        incidents.models.BusinessLine.DoesNotExist,
                        Group.DoesNotExist,
                    ):
                        pass
        return user
