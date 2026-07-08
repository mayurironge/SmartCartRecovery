from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.models.cart_item import CartItem
from backend.repositories.cart_item_repository import CartItemRepository
from backend.repositories.cart_repository import CartRepository
from backend.repositories.product_repository import ProductRepository


class CartItemService:

    @staticmethod
    def add_product(
        db: Session,
        cart_id: int,
        product_id: int,
        quantity: int,
    ):

        cart = CartRepository.get_cart(db, cart_id)

        if not cart:
            raise HTTPException(
                status_code=404,
                detail="Cart not found"
            )

        product = ProductRepository.get_product(db, product_id)

        if not product:
            raise HTTPException(
                status_code=404,
                detail="Product not found"
            )

        existing = CartItemRepository.get_cart_item(
            db,
            cart_id,
            product_id,
        )

        if existing:
            existing.quantity += quantity

            CartItemRepository.update_item(
                db,
                existing,
            )

            return existing

        cart_item = CartItem(
            cart_id=cart_id,
            product_id=product_id,
            quantity=quantity,
        )

        CartItemRepository.add_item(
            db,
            cart_item,
        )

        return cart_item

    @staticmethod
    def remove_product(
        db: Session,
        cart_id: int,
        product_id: int,
):

        cart = CartRepository.get_cart(db, cart_id)

        if not cart:
            raise HTTPException(
                status_code=404,
                detail="Cart not found"
            )

        cart_item = CartItemRepository.get_cart_item(
            db,
            cart_id,
            product_id,
        )

        if not cart_item:
            raise HTTPException(
                status_code=404,
                detail="Product not found in cart"
            )

        if cart_item.quantity > 1:

            CartItemRepository.decrement_quantity(
                db,
                cart_item,
            )

            return {
                "message": "Product quantity decreased",
                "quantity": cart_item.quantity
            }

        CartItemRepository.delete_item(
            db,
            cart_item,
        )

        return {
            "message": "Product removed from cart"
        }
    
        @staticmethod
        def update_quantity(
            db: Session,
            cart_id: int,
            product_id: int,
            quantity: int,
    ):

            cart = CartRepository.get_cart(db, cart_id)

            if not cart:
                raise HTTPException(
                    status_code=404,
                    detail="Cart not found"
                )

            cart_item = CartItemRepository.get_cart_item(
                db,
                cart_id,
                product_id,
            )

            if not cart_item:
                raise HTTPException(
                    status_code=404,
                    detail="Product not found in cart"
                )

            CartItemRepository.update_quantity(
                db,
                cart_item,
                quantity,
            )

            return {
                "message": "Quantity updated successfully"
            }

    @staticmethod
    def empty_cart(
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
                detail="Cart not found"
            )

        CartItemRepository.empty_cart(
            db,
            cart_id,
        )

        return {
            "message": "Cart emptied successfully"
        }