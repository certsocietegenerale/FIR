This module allow users to authenticate to FIR using an LDAP server

## Install

Follow the generic plugin installation instructions in [the FIR wiki](https://github.com/certsocietegenerale/FIR/wiki/Plugins).

# Usage

To enable LDAP authentication, you need to add (and edit according to your setup) the following settings to `production.py`:
```
import ldap
from django_auth_ldap.config import LDAPSearch, GroupOfNamesType
from django.conf import settings

AUTH_LDAP_SERVER_URI = "ldaps://dc1.example.com"
AUTH_LDAP_USER_SEARCH = LDAPSearch(
    "CN=Users,DC=example,DC=com", ldap.SCOPE_SUBTREE, "(sAMAccountName=%(user)s)"
)

AUTH_LDAP_USER_ATTR_MAP = {
    "first_name": "givenName",
    "last_name": "sn",
    "email": "mail",
}

AUTH_LDAP_BIND_DN = "CN=FIR Service Account,OU=serviceAccounts,DC=example,DC=com"
AUTH_LDAP_BIND_PASSWORD = ""

# Define which flag should each user have depending on its LDAP groups
AUTH_LDAP_USER_FLAGS_BY_GROUP = {
    "is_active": [
        "CN=businessline1,OU=groups,DC=example,DC=com",
        "CN=globalHandlers,OU=groups,DC=example,DC=com",
        "CN=firadmins,OU=groups,DC=example,DC=com",
    ],
    "is_staff": ["CN=firadmins,OU=groups,DC=example,DC=com"],
    "is_superuser": ["CN=firadmins,OU=groups,DC=example,DC=com"],
}

# Define which LDAP group should correspond to which Django group
AUTH_LDAP_USER_GROUP_MAP = {
    "CN=globalHandlers,OU=groups,DC=example,DC=com": "Incident handlers",
}

# Define which permission on each business line should each user have depending on its LDAP groups
AUTH_LDAP_USER_ROLE_MAP = {
    "CN=businessline1,OU=groups,DC=example,DC=com": [
        ("Demo BusinessLine 2", "Incident handlers"),
        ("Sub BL 2", "Incident viewers"),
    ],
}

AUTH_LDAP_GROUP_SEARCH = LDAPSearch(
    "OU=groups,DC=example,DC=com", ldap.SCOPE_SUBTREE, "(objectClass=groupOfNames)"
)

AUTHENTICATION_BACKENDS += ("fir_auth_ldap.backend.AttributesLDAPBackend",)
AUTH_LDAP_CACHE_GROUPS = True
AUTH_LDAP_GROUP_CACHE_TIMEOUT = 3600
AUTH_LDAP_FIND_GROUP_PERMS = True

class UserAttributeGroupType(GroupOfNamesType):
    def user_groups(self, ldap_user, group_search):
        return [(group.lower(), {}) for group in ldap_user.attrs.get("memberOf", [])]

    def group_name_from_info(self, group_info):
        group_map = {k.lower(): v for k, v in settings.AUTH_LDAP_USER_GROUP_MAP.items()}
        return group_map.get(group_info[0], None)


AUTH_LDAP_GROUP_TYPE = UserAttributeGroupType()
```
