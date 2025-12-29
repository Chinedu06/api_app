from rest_framework import permissions

class IsOperatorOrReadOnly(permissions.BasePermission):
    """
    - Anyone can read (GET list/detail) approved services.
    - Only authenticated users with role == 'operator' can create services.
    - Only the operator who owns the Service (or admin/staff) can update/delete.
    """
    def has_permission(self, request, view):
        if view.action in ['list', 'retrieve']:
            return True
        if view.action == 'create':
            user = request.user
            return user and user.is_authenticated and getattr(user, "role", None) == 'operator'
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user.is_staff or request.user.is_superuser:
            return True
        return getattr(obj, "operator_id", None) == getattr(request.user, "id", None)


class IsOperatorOwnerOrAdmin(permissions.BasePermission):
    """
    Permission for Package operations:
    - Read: anyone (list/detail) — but packages are tied to approved services in views.
    - Create/Update/Delete: only operator who owns the parent service OR admin/staff.
    """
    def has_permission(self, request, view):
        # allow safe reads
        if request.method in permissions.SAFE_METHODS:
            return True
        # for create: must be authenticated and operator
        if request.method == 'POST':
            user = request.user
            return user and user.is_authenticated and getattr(user, "role", None) == 'operator'
        # for other methods require auth and defer to object check
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # safe methods allowed
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user.is_staff or request.user.is_superuser:
            return True
        # obj here is a Package => check package.service.operator
        return getattr(obj.service, "operator_id", None) == getattr(request.user, "id", None)
