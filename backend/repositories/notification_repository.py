from sqlalchemy.orm import Session

from backend.models.notification import Notification
from sqlalchemy.exc import IntegrityError

class NotificationRepository:

    @staticmethod
    def get_by_recovery(
        db: Session,
        recovery_id: int,
    ):
        return (
            db.query(Notification)
            .filter(Notification.recovery_id == recovery_id)
            .order_by(Notification.notification_id.desc())
            .first()
        )


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

        try:
            db.add(notification)
            db.commit()
            db.refresh(notification)
            return notification

        except IntegrityError:
            db.rollback()

            # Another request may have created this notification first.
            existing = NotificationRepository.get_by_recovery(
                db=db,
                recovery_id=recovery_id,
            )

            if existing:
                return existing

            # Preserve unrelated database errors.
            raise


    @staticmethod
    def mark_as_sent(
        db: Session,
        notification: Notification,
    ):
        notification.sent = True

        db.commit()
        db.refresh(notification)

        return notification
