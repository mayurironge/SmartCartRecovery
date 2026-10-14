from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.models.cart import Cart
from backend.models.cart_item import CartItem
from backend.models.cart_event import CartEvent
from backend.models.cart_recovery import CartRecovery
from sqlalchemy.exc import IntegrityError


class CartRecoveryRepository:

    @staticmethod
    def get_abandoned_carts(
        db: Session,
        threshold_minutes: int = 30,
    ):
        cutoff_time = datetime.now(timezone.utc) - timedelta(
            minutes=threshold_minutes
        )

        latest_events = (
            db.query(
                CartEvent.cart_id,
                func.max(CartEvent.event_time).label("last_activity"),
            )
            .group_by(CartEvent.cart_id)
            .subquery()
        )

        carts = (
            db.query(
                Cart,
                latest_events.c.last_activity,
            )
            .join(
                latest_events,
                Cart.cart_id == latest_events.c.cart_id,
            )
            .filter(
                Cart.status == "ACTIVE",
                latest_events.c.last_activity <= cutoff_time,
            )
            .all()
        )

        abandoned = []

        for cart, last_activity in carts:
            has_items = (
                db.query(CartItem)
                .filter(CartItem.cart_id == cart.cart_id)
                .first()
            )

            if not has_items:
                continue

            recovery = (
                db.query(CartRecovery)
                .filter(CartRecovery.cart_id == cart.cart_id)
                .order_by(CartRecovery.recovery_id.desc())
                .first()
            )

            # A successfully notified cart does not need another reminder.
            if recovery and recovery.recovery_status == "NOTIFIED":
                continue

            # If a recovery exists but is not complete, return it for retry.
            abandoned.append(
                {
                    "cart": cart,
                    "last_activity": last_activity,
                    "recovery": recovery,
                }
            )

        return abandoned


    @staticmethod
    def create_recovery(db: Session, cart_id: int, recovery_status: str = "DETECTED"):
        recovery = CartRecovery(
            cart_id=cart_id,
            recovery_status=recovery_status,
        )

        try:
            db.add(recovery)
            db.commit()
            db.refresh(recovery)
            return recovery

        except IntegrityError:
            db.rollback()

            # Another request may have created this recovery first.
            existing = (
                db.query(CartRecovery)
                .filter(CartRecovery.cart_id == cart_id)
                .first()
            )

            if existing:
                return existing

            # If the error was unrelated to a duplicate cart, don't hide it.
            raise


    @staticmethod
    def mark_as_notified(
        db: Session,
        recovery: CartRecovery,
    ):
        recovery.recovery_status = "NOTIFIED"
        recovery.notified_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(recovery)

        return recovery
