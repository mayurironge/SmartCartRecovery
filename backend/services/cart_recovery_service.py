from sqlalchemy.orm import Session

from backend.repositories.cart_recovery_repository import (
    CartRecoveryRepository,
)
from backend.repositories.notification_repository import (
    NotificationRepository,
)
from backend.services.notification_sender import (
    EmailNotificationSender,
)


class CartRecoveryService:

    @staticmethod
    def detect_abandoned_carts(
        db: Session,
        threshold_minutes: int = 30,
    ):
        abandoned_carts = (
            CartRecoveryRepository.get_abandoned_carts(
                db=db,
                threshold_minutes=threshold_minutes,
            )
        )

        detected = []

        for entry in abandoned_carts:
            cart = entry["cart"]
            last_activity = entry["last_activity"]
            recovery = entry["recovery"]

            # Reuse an unfinished recovery instead of creating a duplicate.
            if recovery is None:
                recovery = CartRecoveryRepository.create_recovery(
                    db=db,
                    cart_id=cart.cart_id,
                    recovery_status="DETECTED",
                )

            # Reuse the existing notification when retrying.
            notification = NotificationRepository.get_by_recovery(
                db=db,
                recovery_id=recovery.recovery_id,
            )

            if notification is None:
                notification = NotificationRepository.create_notification(
                    db=db,
                    customer_id=cart.customer_id,
                    recovery_id=recovery.recovery_id,
                    channel="EMAIL",
                    message="You left items in your cart.",
                )

            # Only attempt delivery if the notification has not been sent.
            if not notification.sent:
                email_sent = EmailNotificationSender.send_email(
                    recipient_email=cart.customer.email,
                    subject="You left items in your cart.",
                    message="You left items in your cart.",
                )

                if email_sent:
                    notification = NotificationRepository.mark_as_sent(
                        db=db,
                        notification=notification,
                    )

                    recovery = CartRecoveryRepository.mark_as_notified(
                        db=db,
                        recovery=recovery,
                    )

            detected.append(
                {
                    "recovery_id": recovery.recovery_id,
                    "cart_id": cart.cart_id,
                    "customer_id": cart.customer_id,
                    "last_activity": last_activity,
                    "recovery_status": recovery.recovery_status,
                    "notification_id": notification.notification_id,
                    "notification_sent": notification.sent,
                }
            )

        return detected
