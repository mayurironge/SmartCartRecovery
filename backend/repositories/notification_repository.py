from sqlalchemy.orm import Session

from backend.models.notification import Notification


class NotificationRepository:

    @staticmethod
    def create_notification(
        db: Session,
        customer_id: int,
        recovery_id: int,
        channel: str,
        message: str,
    ):

        notification = Notification(
            customer_id=customer_id,
            recovery_id=recovery_id,
            channel=channel,
            message=message,
            sent=False,
        )

        db.add(notification)
        db.commit()
        db.refresh(notification)

        return notification

    @staticmethod
    def mark_as_sent(
        db: Session,
        notification: Notification,
    ):

        notification.sent = True

        db.commit()
        db.refresh(notification)

        return notification