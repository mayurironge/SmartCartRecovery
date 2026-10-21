from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.models.notification import Notification


class NotificationRepository:

    @staticmethod
    def get_by_recovery(
        db: Session,
        recovery_id: int,
    ):
        return (
            db.query(Notification)
            .filter(Notification.recovery_id == recovery_id)
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
            # A savepoint keeps a duplicate from rolling back the caller's work.
            with db.begin_nested():
                db.add(notification)

            return notification

        except IntegrityError:
            # Another run created the notification for this recovery first.
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

        return notification
