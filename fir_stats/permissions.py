from incidents.models import AccessControlEntry


def can_view_statistics(user):
    if user.has_perm("incidents.view_statistics"):
        return True

    if AccessControlEntry.objects.filter(
        user=user, role__permissions__codename="view_statistics"
    ):
        return True
    return False
