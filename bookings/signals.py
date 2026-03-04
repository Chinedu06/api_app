import logging
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .models import Booking, Notification
from .emails import (
    email_admins_new_booking,
    email_tourist_booking_received,
    email_operator_booking_paid,
    email_tourist_booking_confirmed,
    email_tourist_booking_rejected,
)

logger = logging.getLogger("bookings")


@receiver(pre_save, sender=Booking)
def booking_pre_save(sender, instance, **kwargs):
    """
    Capture previous state before saving so post_save can detect transitions.
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
    Keep dashboard notifications as-is, but ALSO send emails (new requirement).
    """
    try:
        def create_notification(recipient, message):
            Notification.objects.create(recipient=recipient, message=message)

        service = getattr(instance, "service", None)
        operator = getattr(service, "operator", None) if service else None

        # 1) Booking created
        if created:
            # Notifications (existing behavior)
            if operator:
                create_notification(
                    operator,
                    f"New booking #{instance.pk} created for your service '{service.title}'."
                )

            create_notification(
                None,
                f"New booking #{instance.pk} received for '{service.title}' by {instance.given_name} {instance.surname}."
            )

            # Emails (new behavior)
            email_admins_new_booking(instance)
            email_tourist_booking_received(instance)

            return

        # 2) Detect changes
        old_status = getattr(instance, "_old_status", None)
        old_payment = getattr(instance, "_old_payment_status", None)

        new_status = instance.status
        new_payment = instance.payment_status

        # 3) Payment became PAID -> notify operator (email + dashboard)
        if old_payment != Booking.PAYMENT_PAID and new_payment == Booking.PAYMENT_PAID:
            if operator:
                create_notification(
                    operator,
                    f"Booking #{instance.pk} for '{service.title}' is now PAID. You can confirm or reject."
                )
            create_notification(
                None,
                f"Booking #{instance.pk} marked PAID for '{service.title}'. Operator can now confirm."
            )

            email_operator_booking_paid(instance)

        # 4) Status changes -> notify + email tourist if needed
        if old_status == new_status:
            return  # nothing else changed

        if new_status == Booking.STATUS_CONFIRMED:
            if operator:
                create_notification(operator, f"Booking #{instance.pk} for '{service.title}' has been confirmed.")
            create_notification(None, f"Booking #{instance.pk} for '{service.title}' confirmed by operator.")
            # Tourist email (guest booking uses booking.email)
            email_tourist_booking_confirmed(instance)

        elif new_status == Booking.STATUS_REJECTED:
            reason = instance.admin_note or "No reason provided."
            if operator:
                create_notification(operator, f"Booking #{instance.pk} was rejected. Reason: {reason}")
            create_notification(None, f"Booking #{instance.pk} for '{service.title}' was rejected. Reason: {reason}")
            email_tourist_booking_rejected(instance)

        elif new_status == Booking.STATUS_CANCELLED:
            initiator = getattr(instance.user, "username", "Guest")
            create_notification(None, f"Booking #{instance.pk} has been cancelled by {initiator}.")
            if operator:
                create_notification(operator, f"Booking #{instance.pk} has been cancelled.")

    except Exception as e:
        logger.exception(f"Error in booking_post_save for Booking#{instance.pk if instance.pk else 'new'}: {e}")