from rest_framework.permissions import BasePermission, IsAdminUser, SAFE_METHODS
from incidents.models import AccessControlEntry, BusinessLine, Incident
from django.conf import settings


class BaseIncidentPermission(BasePermission):
    def get_incident_bls(self, obj):
        if hasattr(obj, "incident"):
            obj = obj.incident
        return obj.concerned_business_lines.all()

    def has_perm(self, user, perm, bls):
        return user.has_perm(perm) or any(user.has_perm(perm, bl) for bl in bls)

    def is_handler(self, user, bls):
        return self.has_perm(user, "incidents.handle_incidents", bls)

    def is_writer(self, user, bls):
        return self.has_perm(user, "incidents.report_events", bls)

    def is_viewer(self, user, bls):
        return self.has_perm(user, "incidents.view_incidents", bls)


class CanViewIncident(BaseIncidentPermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS

    def has_object_permission(self, request, view, obj):
        if request.method not in SAFE_METHODS:
            return False
        bls = self.get_incident_bls(obj)
        return self.is_viewer(request.user, bls) or self.is_handler(request.user, bls)


class CanWriteIncident(BaseIncidentPermission):
    def has_permission(self, request, view):
        return request.method not in SAFE_METHODS

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return False
        bls = self.get_incident_bls(obj)
        return self.is_writer(request.user, bls) or self.is_handler(request.user, bls)


class CanViewComment(BaseIncidentPermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS

    def has_object_permission(self, request, view, obj):
        if request.method not in SAFE_METHODS:
            return False
        bls = self.get_incident_bls(obj)
        return self.is_viewer(request.user, bls) or self.is_handler(request.user, bls)


class CanWriteComment(BaseIncidentPermission):
    def has_permission(self, request, view):
        return request.method not in SAFE_METHODS

    def has_object_permission(self, request, view, obj):
        bls = self.get_incident_bls(obj)
        user = request.user

        if self.is_handler(user, bls):
            return True

        if request.method == "POST":
            return self.is_writer(user, bls) or (
                settings.INCIDENT_VIEWER_CAN_COMMENT and self.is_viewer(user, bls)
            )

        if request.method in ["PUT", "PATCH"]:
            return (
                settings.INCIDENT_VIEWER_CAN_COMMENT
                and hasattr(obj, "opened_by")
                and obj.opened_by == user
            )

        return False


class IsAdminUserOrReadOnly(IsAdminUser):
    def has_permission(self, request, view):
        is_admin = super().has_permission(request, view)
        return request.method in SAFE_METHODS or is_admin
