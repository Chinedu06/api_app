from rest_framework import permissions

class IsBookingOwnerOrOperatorOrAdmin(permissions.BasePermission):
    """
    - Admin/staff: full access.
    - Operator: can view bookings for their own services.
    - Booking creator (user) can view their booking.
    - Otherwise read-only allowed for admin only.
    """
    def has_object_permission(self, request, view, obj):
        # staff/admin full
        if request.user and (request.user.is_staff or request.user.is_superuser):
            return True
        # operator: check service.operator
        if hasattr(request.user, "role") and request.user.role == "operator":
            return obj.service.operator_id == request.user.id
        # creator:
        if obj.user and request.user.is_authenticated:
            return obj.user_id == request.user.id
        # anonymous creator (no user) — only admin/operator can view
        return False