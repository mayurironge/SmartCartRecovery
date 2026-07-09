from sqlalchemy.orm import Session

from backend.models.cart import Cart


class CartRepository:

    @staticmethod
    def create_cart(
        db: Session,
        customer_id: int,
    ):

        cart = Cart(
            customer_id=customer_id,
            status="ACTIVE",
        )

        db.add(cart)
        db.commit()
        db.refresh(cart)

        return cart

    @staticmethod
    def get_cart(
        db: Session,
        cart_id: int,
    ):

        return (
            db.query(Cart)
            .filter(Cart.cart_id == cart_id)
            .first()
        )

    @staticmethod
    def get_active_cart_by_id(
        db: Session,
        cart_id: int,
    ):

        return (
            db.query(Cart)
            .filter(
                Cart.cart_id == cart_id,
                Cart.status == "ACTIVE",
            )
            .first()
        )

    @staticmethod
    def get_active_cart(
        db: Session,
        customer_id: int,
    ):

        return (
            db.query(Cart)
            .filter(
                Cart.customer_id == customer_id,
                Cart.status == "ACTIVE",
            )
            .first()
        )

    @staticmethod
    def update_status(
        db: Session,
        cart: Cart,
        status: str,
    ):

        cart.status = status