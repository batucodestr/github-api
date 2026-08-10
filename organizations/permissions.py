from rest_framework.permissions import BasePermission
from .models import OrganizationMember


class IsOrganizationAdmin(BasePermission):

    def has_permission(self, request, view):
        organization_id = view.kwargs.get("organization_id")

        return OrganizationMember.objects.filter(
            organization_id=organization_id,
            user=request.user,
            role="admin",
        ).exists()

class IsOrganizationMember(BasePermission):

    def has_permission(self, request, view):
        organization_id = view.kwargs.get("organization_id")

        return OrganizationMember.objects.filter(
            organization_id=organization_id,
            user=request.user,
        ).exists()

class IsOrganizationOwner(BasePermission):

    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user