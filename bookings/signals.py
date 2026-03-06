import logging
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from .models import Booking, Notification
from .emails import (
    email_admin_new_booking,
    email_tourist_booking_received,
    email_operator_booking_paid,
    email_tourist_booking_confirmed,
    email_tourist_booking_rejected,
)

logger = logging.getLogger("bookings")


@receiver(pre_save, sender=Booking)
def booking_pre_save(sender, instance, **kwargs):
    """
    Track old status & payment_status so we can detect transitions.
    """
    if instance.pk:
        try:
            old = Booking.objects.get(pk=instance.pk)
            instance._old_status = old.status
            instance._old_payment_status = old.payment_status
        except Booking.DoesNotExist:
            instance._old_status = None
            instance._old_payment_status = None
    else:
        instance._old_status = None
        instance._old_payment_status = None


@receiver(post_save, sender=Booking)
def booking_post_save(sender, instance, created, **kwargs):
    """
    Keep your dashboard Notification table intact, but ALSO send emails.
    """
    try:
        def create_notification(recipient, message):
            Notification.objects.create(recipient=recipient, message=message)

        service = getattr(instance, "service", None)
        operator = getattr(service, "operator", None) if service else None

        # ==========================================================
        # 1) Booking created (PENDING / UNPAID)
        # ==========================================================
        if created:
            # dashboard notifications (existing behavior)
            if operator:
                create_notification(
                    operator,
                    f"New booking #{instance.pk} created for your service '{service.title}'."
                )

            create_notification(
                None,
                f"New booking #{instance.pk} received for '{service.title}' by {instance.given_name} {instance.surname}."
            )

            # emails (NEW)
            email_admin_new_booking(instance)          # all admins
            email_tourist_booking_received(instance)   # tourist

            return

        # ==========================================================
        # 2) Detect status & payment changes
        # ==========================================================
        old_status = getattr(instance, "_old_status", None)
        new_status = instance.status

        old_payment = getattr(instance, "_old_payment_status", None)
        new_payment = instance.payment_status

        status_changed = old_status != new_status
        payment_changed = old_payment != new_payment

        # ==========================================================
        # 3) Payment became PAID -> notify operator (email + dashboard)
        #    (This is the key moment: operator can now confirm)
        # ==========================================================
        if payment_changed and new_payment == Booking.PAYMENT_PAID:
            # dashboard notification
            if operator:
                create_notification(
                    operator,
                    f"Booking #{instance.pk} for '{service.title}' is now PAID and awaiting your confirmation."
                )

            # email operator
            email_operator_booking_paid(instance)

        # ==========================================================
        # 4) Operator confirms -> notify tourist (email + dashboard)
        # ==========================================================
        if status_changed and new_status == Booking.STATUS_CONFIRMED:
            if operator:
                create_notification(operator, f"Booking #{instance.pk} for '{service.title}' has been confirmed.")
            if instance.user:
                create_notification(instance.user, f"Your booking #{instance.pk} has been confirmed.")

            email_tourist_booking_confirmed(instance)

        # ==========================================================
        # 5) Operator rejects -> notify tourist (email + dashboard)
        # ==========================================================
        if status_changed and new_status == Booking.STATUS_REJECTED:
            reason = instance.admin_note or "No reason provided."

            if operator:
                create_notification(operator, f"Booking #{instance.pk} was rejected. Reason: {reason}")
            if instance.user:
                create_notification(instance.user, f"Your booking #{instance.pk} was rejected. Reason: {reason}")

            create_notification(None, f"Booking #{instance.pk} for '{service.title}' was rejected. Reason: {reason}")

            email_tourist_booking_rejected(instance)

        # ==========================================================
        # 6) Cancelled -> (optional email later if you want)
        # ==========================================================
        if status_changed and new_status == Booking.STATUS_CANCELLED:
            initiator = getattr(instance.user, "username", "Unknown")
            create_notification(None, f"Booking #{instance.pk} has been cancelled by {initiator}.")
            if operator:
                create_notification(operator, f"Booking #{instance.pk} has been cancelled.")
            if instance.user:
                create_notification(instance.user, f"Your booking #{instance.pk} has been cancelled.")

    except Exception as e:
        logger.exception(f"Error in booking_post_save for Booking#{instance.pk}: {e}")