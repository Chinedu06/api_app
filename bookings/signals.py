import logging
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .models import Booking, Notification

# Create a logger for this app
logger = logging.getLogger('bookings')


@receiver(pre_save, sender=Booking)
def booking_pre_save(sender, instance, **kwargs):
    """
    Capture the previous booking status before saving.
    This allows post_save to detect changes (status transitions).
    """
    if instance.pk:
        try:
            old = Booking.objects.get(pk=instance.pk)
            instance._old_status = old.status
        except Booking.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


@receiver(post_save, sender=Booking)
def booking_post_save(sender, instance, created, **kwargs):
    """
    Handle booking notifications after save events.
    - On create: notify operator (and optionally admins globally).
    - On status change: notify operator, user, and admins accordingly.
    """
    try:
        # --- helper to safely create notifications ---
        def create_notification(recipient, message):
            Notification.objects.create(recipient=recipient, message=message)

        service = getattr(instance, "service", None)
        operator = getattr(service, "operator", None) if service else None

        # 1 New booking created — notify operator + admin
        if created:
            # notify operator (owner of the service)
            if operator:
                create_notification(
                    operator,
                    f"New booking #{instance.pk} created for your service '{service.title}'."
                )

            # global admin notification (recipient=None)
            create_notification(
                None,
                f"New booking #{instance.pk} received for '{service.title}' by {instance.given_name} {instance.surname}."
            )
            return

        # 2 Detect status change
        old_status = getattr(instance, "_old_status", None)
        new_status = instance.status
        if old_status == new_status:
            return  # nothing changed

        # 3 Booking confirmed
        if new_status == Booking.STATUS_CONFIRMED:
            if operator:
                create_notification(operator, f"Booking #{instance.pk} for '{service.title}' has been approved.")
            if instance.user:
                create_notification(instance.user, f"Your booking #{instance.pk} has been approved.")

        # 4 Booking rejected
        elif new_status == Booking.STATUS_REJECTED:
            reason = instance.admin_note or "No reason provided."
            if operator:
                create_notification(operator, f"Booking #{instance.pk} was rejected. Reason: {reason}")
            if instance.user:
                create_notification(instance.user, f"Your booking #{instance.pk} was rejected. Reason: {reason}")
            # NEW: admin global notification for audit visibility
            create_notification(None, f"Booking #{instance.pk} for '{service.title}' was rejected by admin. Reason: {reason}")

        # 5 Booking cancelled
        elif new_status == Booking.STATUS_CANCELLED:
            initiator = getattr(instance.user, 'username', 'Unknown')
            create_notification(None, f"Booking #{instance.pk} has been cancelled by {initiator}.")
            if operator:
                create_notification(operator, f"Booking #{instance.pk} has been cancelled.")
            if instance.user:
                create_notification(instance.user, f"Your booking #{instance.pk} has been cancelled.")

    except Exception as e:
        # Log exception to logs/bookings_signals.log via configured handler
        logger.exception(f"Error in booking_post_save for Booking#{instance.pk if instance.pk else 'new'}: {e}")
