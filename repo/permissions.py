from rest_framework.permissions import BasePermission, SAFE_METHODS

from organizations.models import OrganizationMember


def can_view_repo(user, repo):
    """Herkese açık depolar herkes tarafından görülebilir; özel depolar sadece sahibi
    veya sahibi olan organizasyonun üyeleri tarafından görülebilir."""
    if repo.visibility == 'public':
        return True
    if not user or not user.is_authenticated:
        return False
    return has_repo_write_access(user, repo)


def has_repo_write_access(user, repo):
    """Depo sahibi kullanıcı ya da depo bir organizasyona aitse organizasyon üyeleri yazma
    yetkisine sahiptir."""
    if not user or not user.is_authenticated:
        return False
    if repo.owner_id == user.id:
        return True
    if repo.organization_id:
        return OrganizationMember.objects.filter(
            organization_id=repo.organization_id,
            user=user,
        ).exists()
    return False


class RepoWriteAccessPermission(BasePermission):
    """Depo sahibi ya da depoyu barındıran organizasyonun üyesi olan kullanıcılara yazma
    (dal/commit/issue/PR oluşturma) izni verir. Okuma istekleri görünürlük kuralına tabidir."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        repo = obj if hasattr(obj, 'visibility') else obj.repository
        if request.method in SAFE_METHODS:
            return can_view_repo(request.user, repo)
        return has_repo_write_access(request.user, repo)
