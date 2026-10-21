from datetime import datetime, timedelta, timezone

from sqlalchemy import exists, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from backend.constants import cart_status, recovery_status
from backend.models.cart import Cart
from backend.models.cart_item import CartItem
from backend.models.cart_event import CartEvent
from backend.models.cart_recovery import CartRecovery


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

        has_items = exists().where(CartItem.cart_id == Cart.cart_id)

        carts = (
            db.query(
                Cart,
                latest_events.c.last_activity,
            )
            .join(
                latest_events,
                Cart.cart_id == latest_events.c.cart_id,
            )
            .options(joinedload(Cart.customer))
            .filter(
                Cart.status == cart_status.ACTIVE,
                latest_events.c.last_activity <= cutoff_time,
                has_items,
            )
            .all()
        )

        abandoned = []

        for cart, last_activity in carts:
            recovery = CartRecoveryRepository.get_latest_recovery(
                db=db,
                cart_id=cart.cart_id,
            )

            if (
                recovery
                and recovery.recovery_status != recovery_status.PENDING
            ):
                closed_at = recovery.notified_at or recovery.detected_at

                # No activity since the last recovery closed, so it already
                # covers this abandonment.
                if last_activity <= closed_at:
                    continue

                # The customer came back and abandoned the cart again.
                recovery = None

            # A PENDING recovery is returned so delivery can be retried.
            abandoned.append(
                {
                    "cart": cart,
                    "last_activity": last_activity,
                    "recovery": recovery,
                }
            )

        return abandoned

    @staticmethod
    def get_latest_recovery(
        db: Session,
        cart_id: int,
    ):
        return (
            db.query(CartRecovery)
            .filter(CartRecovery.cart_id == cart_id)
            .order_by(CartRecovery.recovery_id.desc())
            .first()
        )

    @staticmethod
    def get_pending_recovery(
        db: Session,
        cart_id: int,
    ):
        return (
            db.query(CartRecovery)
            .filter(
                CartRecovery.cart_id == cart_id,
                CartRecovery.recovery_status == recovery_status.PENDING,
            )
            .first()
        )

    @staticmethod
    def lock_pending_recovery(
        db: Session,
        recovery_id: int,
    ):
        # Returns None if another run holds the lock or already finished it.
        return (
            db.query(CartRecovery)
            .filter(
                CartRecovery.recovery_id == recovery_id,
                CartRecovery.recovery_status == recovery_status.PENDING,
            )
            .with_for_update(skip_locked=True)
            .populate_existing()
            .first()
        )

    @staticmethod
    def create_recovery(
        db: Session,
        cart_id: int,
    ):
        recovery = CartRecovery(
            cart_id=cart_id,
            recovery_status=recovery_status.PENDING,
        )

        try:
            # A savepoint keeps a duplicate from rolling back the caller's work.
            with db.begin_nested():
                db.add(recovery)

            return recovery

        except IntegrityError:
            # Another run opened a recovery for this cart first.
            existing = CartRecoveryRepository.get_pending_recovery(
                db=db,
                cart_id=cart_id,
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
        recovery.recovery_status = recovery_status.NOTIFIED
        recovery.notified_at = datetime.now(timezone.utc)

        return recovery

    @staticmethod
    def record_failed_attempt(
        db: Session,
        recovery: CartRecovery,
        max_attempts: int,
    ):
        recovery.attempts += 1

        if recovery.attempts >= max_attempts:
            recovery.recovery_status = recovery_status.EXPIRED

        return recovery

    @staticmethod
    def close_for_checkout(
        db: Session,
        cart_id: int,
    ):
        recovery = CartRecoveryRepository.get_latest_recovery(
            db=db,
            cart_id=cart_id,
        )

        if recovery is None:
            return None

        # Only a delivered reminder can take credit for the checkout.
        if recovery.recovery_status == recovery_status.NOTIFIED:
            recovery.recovery_status = recovery_status.RECOVERED

        elif recovery.recovery_status == recovery_status.PENDING:
            recovery.recovery_status = recovery_status.EXPIRED

        return recovery
