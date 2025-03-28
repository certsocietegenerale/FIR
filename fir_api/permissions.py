from rest_framework.permissions import BasePermission, IsAdminUser, SAFE_METHODS
from incidents.models import Incident, AccessControlEntry


class IsIncidentHandler(BasePermission):
    def has_permission(self, request, view):
        # Checks for handle_incidents permissions for non GET requests
        if request.method == "GET":
            return True
        if request.user.has_perm("incidents.handle_incidents"):
            return True
        # Get any possible access control entries that would allow the user
        # to perform actions from handle_incidents perspective
        user_access_controls = AccessControlEntry.objects.filter(
            user=request.user, role__permissions__codename="handle_incidents"
        )
        if user_access_controls:
            return True
        return False

    def has_object_permission(self, request, view, obj):
        try:
            if type(obj) == Incident:
                incident = obj
            elif hasattr(obj, "incident"):
                incident = obj.incident
            else:
                # The object is not related to an incident (ValidAttribute, etc)
                return True
            Incident.authorization.for_user(
                request.user, "incidents.view_incidents"
            ).get(pk=incident.id)
            return True
        except:
            return False


class IsAdminUserOrReadOnly(IsAdminUser):
    def has_permission(self, request, view):
        is_admin = super().has_permission(request, view)
        return request.method in SAFE_METHODS or is_admin
