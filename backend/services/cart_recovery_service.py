from sqlalchemy.orm import Session

from backend.repositories.cart_recovery_repository import (
    CartRecoveryRepository
)

from backend.repositories.notification_repository import (
    NotificationRepository
)

from backend.services.notification_sender import (
    MockNotificationSender
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

            # 1. Create recovery record
            recovery = (
                CartRecoveryRepository.create_recovery(
                    db=db,
                    cart_id=cart.cart_id,
                    recovery_status="DETECTED",
                )
            )

            # 2. Create notification linked to this recovery
            notification = NotificationRepository.create_notification(
                db=db,
                customer_id=cart.customer_id,
                recovery_id=recovery.recovery_id,
                channel="EMAIL",
                message="You left items in your cart.",
            )

            # 3. Send notification
            sent_successfully = MockNotificationSender.send_email(
                customer_id=cart.customer_id,
                message=notification.message,
            )

            # 4. Update database only if sending succeeds
            if sent_successfully:

                # Mark notification as sent
                notification = NotificationRepository.mark_as_sent(
                    db=db,
                    notification=notification,
                )

                # Mark recovery as notified
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