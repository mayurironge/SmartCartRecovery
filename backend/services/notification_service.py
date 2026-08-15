from sqlalchemy.orm import Session

from backend.repositories.notification_repository import (
    NotificationRepository
)


class NotificationService:

    @staticmethod
    def create_cart_recovery_notification(
        db: Session,
        customer_id: int,
        recovery_id: int,
    ):
        message = "You left items in your cart."

        notification = (
            NotificationRepository.create_notification(
                db=db,
                customer_id=customer_id,
                recovery_id=recovery_id,
                channel="EMAIL",
                message=message,
            )
        )

        return notification