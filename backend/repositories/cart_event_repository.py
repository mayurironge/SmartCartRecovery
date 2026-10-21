from sqlalchemy.orm import Session

from backend.models.cart_event import CartEvent


class CartEventRepository:

    @staticmethod
    def create_event(
        db: Session,
        cart_id: int,
        event_type: str,
    ):
        event = CartEvent(
            cart_id=cart_id,
            event_type=event_type,
        )

        db.add(event)
        db.flush()

        return event
