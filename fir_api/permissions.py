from rest_framework.permissions import BasePermission


class IsIncidentHandler(BasePermission):
    def has_permission(self, request, view):
        return request.user.has_perm('incidents.handle_incidents')
