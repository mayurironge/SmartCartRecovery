from sqlalchemy.orm import Session

from backend.models.notification import Notification


class NotificationRepository:

    @staticmethod
    def create_notification(
        db: Session,
        customer_id: int,
        channel: str,
        message: str,
    ):

        notification = Notification(
            customer_id=customer_id,
            channel=channel,
            message=message,
            sent=False,
        )

        db.add(notification)
        db.commit()
        db.refresh(notification)

        return notification