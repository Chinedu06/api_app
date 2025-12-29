from rest_framework import permissions

class IsOperator(permissions.BasePermission):
    """
    Allows access only to users with role == 'operator'.
    """
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and getattr(user, "role", None) == "operator")

class IsVerifiedOperator(permissions.BasePermission):
    """
    Allows access only to verified operators (is_verified==True).
    """
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and getattr(user, "role", None) == "operator" and user.is_verified)

class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Allow access only to resource owner (profile.user) or admin/staff.
    """
    def has_object_permission(self, request, view, obj):
        # Admin/staff always allowed
        if request.user.is_staff or request.user.is_superuser:
            return True
        # Owner allowed
        return getattr(obj, "user", None) == request.user
