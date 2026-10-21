from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.constants import cart_events, cart_status
from backend.models.cart_item import CartItem
from backend.repositories.cart_event_repository import CartEventRepository
from backend.repositories.cart_item_repository import CartItemRepository
from backend.repositories.cart_repository import CartRepository
from backend.repositories.product_repository import ProductRepository


class CartItemService:

    @staticmethod
    def _get_active_cart(
        db: Session,
        cart_id: int,
    ):

        cart = CartRepository.get_cart(
            db,
            cart_id,
        )

        if not cart:
            raise HTTPException(
                status_code=404,
                detail="Cart not found",
            )

        if cart.status != cart_status.ACTIVE:
            raise HTTPException(
                status_code=400,
                detail="Cart is no longer active",
            )

        return cart

    @staticmethod
    def _get_cart_item(
        db: Session,
        cart_id: int,
        product_id: int,
    ):

        cart_item = CartItemRepository.get_cart_item(
            db,
            cart_id,
            product_id,
        )

        if not cart_item:
            raise HTTPException(
                status_code=404,
                detail="Product not found in cart",
            )

        return cart_item

    @staticmethod
    def _record_change(
        db: Session,
        cart,
        event_type: str,
    ):

        CartRepository.touch_cart(
            db=db,
            cart=cart,
        )

        CartEventRepository.create_event(
            db=db,
            cart_id=cart.cart_id,
            event_type=event_type,
        )

        db.commit()

    @staticmethod
    def add_product(
        db: Session,
        cart_id: int,
        product_id: int,
        quantity: int,
    ):

        cart = CartItemService._get_active_cart(
            db,
            cart_id,
        )

        product = ProductRepository.get_product(
            db,
            product_id,
        )

        if not product:
            raise HTTPException(
                status_code=404,
                detail="Product not found",
            )

        existing = CartItemRepository.get_cart_item(
            db,
            cart_id,
            product_id,
        )

        if existing:
            CartItemRepository.increase_quantity(
                db,
                existing,
                quantity,
            )
            message = "Product quantity updated successfully"

        else:
            CartItemRepository.add_item(
                db,
                CartItem(
                    cart_id=cart_id,
                    product_id=product_id,
                    quantity=quantity,
                ),
            )
            message = "Product added to cart successfully"

        CartItemService._record_change(
            db,
            cart,
            cart_events.PRODUCT_ADDED,
        )

        return {
            "message": message
        }

    @staticmethod
    def remove_product(
        db: Session,
        cart_id: int,
        product_id: int,
    ):

        cart = CartItemService._get_active_cart(
            db,
            cart_id,
        )

        cart_item = CartItemService._get_cart_item(
            db,
            cart_id,
            product_id,
        )

        if cart_item.quantity > 1:
            CartItemRepository.decrement_quantity(
                db,
                cart_item,
            )
            message = "Product quantity decreased"

        else:
            CartItemRepository.delete_item(
                db,
                cart_item,
            )
            message = "Product removed from cart"

        CartItemService._record_change(
            db,
            cart,
            cart_events.PRODUCT_REMOVED,
        )

        return {
            "message": message
        }

    @staticmethod
    def update_quantity(
        db: Session,
        cart_id: int,
        product_id: int,
        quantity: int,
    ):

        cart = CartItemService._get_active_cart(
            db,
            cart_id,
        )

        cart_item = CartItemService._get_cart_item(
            db,
            cart_id,
            product_id,
        )

        CartItemRepository.update_quantity(
            db,
            cart_item,
            quantity,
        )

        CartItemService._record_change(
            db,
            cart,
            cart_events.QUANTITY_UPDATED,
        )

        return {
            "message": "Quantity updated successfully"
        }

    @staticmethod
    def empty_cart(
        db: Session,
        cart_id: int,
    ):

        cart = CartItemService._get_active_cart(
            db,
            cart_id,
        )

        CartItemRepository.empty_cart(
            db,
            cart_id,
        )

        CartItemService._record_change(
            db,
            cart,
            cart_events.CART_EMPTIED,
        )

        return {
            "message": "Cart emptied successfully"
        }
