from rest_framework import permissions


class ServicePermission(permissions.BasePermission):
    """
    Services Permission Rules:

    READ (GET):
    - Public users can read only active + approved services
    - Operators can read their own services (including inactive/unapproved drafts)
    - Admin can read all services

    WRITE (POST, PUT, PATCH, DELETE):
    - Operators can manage ONLY their own services
    - Admin can manage ALL services
    """

    def has_permission(self, request, view):
        # READ access (public)
        if request.method in permissions.SAFE_METHODS:
            return True

        # WRITE access requires authentication
        if not request.user or not request.user.is_authenticated:
            return False

        # Admin override
        if request.user.is_staff or request.user.is_superuser:
            return True

        # Operator only
        return getattr(request.user, "role", None) == "operator"

    def has_object_permission(self, request, view, obj):
        # READ access
        if request.method in permissions.SAFE_METHODS:
            # Admin can view all
            if request.user and request.user.is_authenticated and (
                request.user.is_staff or request.user.is_superuser
            ):
                return True

            # Operators can view their own services (even if inactive/unapproved)
            if request.user and request.user.is_authenticated and getattr(request.user, "role", None) == "operator":
                return getattr(obj, "operator_id", None) == request.user.id

            # Public can only view active + approved
            return obj.is_active and obj.is_approved

        # WRITE access
        # Admin override
        if request.user.is_staff or request.user.is_superuser:
            return True

        # Operator owns the service
        return getattr(obj, "operator_id", None) == request.user.id


class PackagePermission(permissions.BasePermission):
    """
    Packages Permission Rules:

    READ (GET):
    - Public users can read packages tied to active + approved services
    - Operators can read packages under their services (including drafts)
    - Admin can read all packages

    WRITE (POST, PUT, PATCH, DELETE):
    - Operators can manage packages ONLY under their services
    - Admin can manage ALL packages
    """

    def has_permission(self, request, view):
        # READ access
        if request.method in permissions.SAFE_METHODS:
            return True

        # WRITE requires authentication
        if not request.user or not request.user.is_authenticated:
            return False

        # Admin override
        if request.user.is_staff or request.user.is_superuser:
            return True

        # Operator only
        return getattr(request.user, "role", None) == "operator"

    def has_object_permission(self, request, view, obj):
        # READ access
        if request.method in permissions.SAFE_METHODS:
            # Admin can view all
            if request.user and request.user.is_authenticated and (
                request.user.is_staff or request.user.is_superuser
            ):
                return True

            # Operator can view packages under their own services
            if request.user and request.user.is_authenticated and getattr(request.user, "role", None) == "operator":
                return obj.service.operator_id == request.user.id

            # Public: only if parent service is active + approved
            return obj.service.is_active and obj.service.is_approved

        # WRITE access
        # Admin override
        if request.user.is_staff or request.user.is_superuser:
            return True

        # Operator owns parent service
        return obj.service.operator_id == request.user.id