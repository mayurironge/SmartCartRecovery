from sqlalchemy.orm import Session

from backend.models import cart_item
from backend.models.cart_item import CartItem


class CartItemRepository:

    @staticmethod
    def get_cart_item(
        db: Session,
        cart_id: int,
        product_id: int
    ):
        return (
            db.query(CartItem)
            .filter(
                CartItem.cart_id == cart_id,
                CartItem.product_id == product_id
            )
            .first()
        )

    @staticmethod
    def add_item(
        db: Session,
        cart_item: CartItem
    ):
        db.add(cart_item)
        db.commit()
        db.refresh(cart_item)

        return cart_item

    @staticmethod
    def update_item(
        db: Session,
        cart_item: CartItem
    ):
        db.commit()
        db.refresh(cart_item)

        return cart_item
    
    @staticmethod
    def decrement_quantity(
        db: Session,
        cart_item: CartItem
    ):
        cart_item.quantity -= 1

        db.commit()
        db.refresh(cart_item)

        return cart_item

    @staticmethod
    def delete_item(
        db: Session,
        cart_item: CartItem
    ):
        db.delete(cart_item)
        db.commit()

    @staticmethod
    def update_quantity(
        db: Session,
        cart_item: CartItem,
        quantity: int,
):
            cart_item.quantity = quantity

            db.commit()
            db.refresh(cart_item)

            return cart_item
    
    @staticmethod
    def get_cart_items(
        db: Session,
        cart_id: int,
):
        return (
            db.query(CartItem)
            .filter(CartItem.cart_id == cart_id)
            .all()
        )
    
    @staticmethod
    def empty_cart(
        db: Session,
        cart_id: int,
):
        (
            db.query(CartItem)
            .filter(CartItem.cart_id == cart_id)
            .delete()
        )

        db.commit()

    @staticmethod
    def get_cart_items(
        db: Session,
        cart_id: int,
):
        return (
            db.query(CartItem)
            .filter(
                CartItem.cart_id == cart_id
            )
            .all()
        )