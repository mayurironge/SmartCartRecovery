from sqlalchemy.orm import Session

from backend.repositories.cart_repository import CartRepository


class CartService:

    @staticmethod
    def create_cart(db: Session, customer_id: int):

        return CartRepository.create_cart(
            db=db,
            customer_id=customer_id
        )