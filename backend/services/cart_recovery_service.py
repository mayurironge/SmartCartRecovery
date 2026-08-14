from sqlalchemy.orm import Session

from backend.repositories.cart_recovery_repository import (
    CartRecoveryRepository
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

            recovery = (
                CartRecoveryRepository.create_recovery(
                    db=db,
                    cart_id=cart.cart_id,
                    recovery_status="DETECTED",
                )
            )

            detected.append(
                {
                    "recovery_id": recovery.recovery_id,
                    "cart_id": cart.cart_id,
                    "customer_id": cart.customer_id,
                    "last_activity": last_activity,
                    "recovery_status": recovery.recovery_status,
                }
            )

        return detected