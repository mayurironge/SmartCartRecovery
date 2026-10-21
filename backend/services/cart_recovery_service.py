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

# After this many failed sends the recovery is marked EXPIRED.
MAX_SEND_ATTEMPTS = 3

RECOVERY_MESSAGE = "You left items in your cart."


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

            # Reuse a pending recovery instead of creating a duplicate.
            if recovery is None:
                recovery = CartRecoveryRepository.create_recovery(
                    db=db,
                    cart_id=cart.cart_id,
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
                    message=RECOVERY_MESSAGE,
                )

            db.commit()

            # Lock the recovery while sending so a concurrent run skips it
            # instead of emailing the customer a second time.
            recovery = CartRecoveryRepository.lock_pending_recovery(
                db=db,
                recovery_id=recovery.recovery_id,
            )

            if recovery is None:
                db.rollback()
                continue

            if notification.sent or EmailNotificationSender.send_email(
                recipient_email=cart.customer.email,
                subject=RECOVERY_MESSAGE,
                message=notification.message,
            ):
                NotificationRepository.mark_as_sent(
                    db=db,
                    notification=notification,
                )

                CartRecoveryRepository.mark_as_notified(
                    db=db,
                    recovery=recovery,
                )

            else:
                CartRecoveryRepository.record_failed_attempt(
                    db=db,
                    recovery=recovery,
                    max_attempts=MAX_SEND_ATTEMPTS,
                )

            db.commit()

            detected.append(
                {
                    "recovery_id": recovery.recovery_id,
                    "cart_id": cart.cart_id,
                    "customer_id": cart.customer_id,
                    "last_activity": last_activity,
                    "recovery_status": recovery.recovery_status,
                    "attempts": recovery.attempts,
                    "notification_id": notification.notification_id,
                    "notification_sent": notification.sent,
                }
            )

        return detected
