from sqlalchemy.orm import Session

from backend.repositories.cart_repository import CartRepository
from fastapi import HTTPException

from backend.repositories.cart_repository import CartRepository
from backend.repositories.cart_item_repository import CartItemRepository

class CartService:

    @staticmethod
    def create_cart(db: Session, customer_id: int):

        return CartRepository.create_cart(
            db=db,
            customer_id=customer_id
        )
    @staticmethod
    def view_cart(
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

        items = CartItemRepository.get_cart_items(
            db,
            cart_id,
        )

        response_items = []

        total = 0

        for item in items:

            subtotal = float(item.product.price) * item.quantity

            total += subtotal

            response_items.append(
                {
                    "product_id": item.product.product_id,
                    "product_name": item.product.product_name,
                    "price": float(item.product.price),
                    "quantity": item.quantity,
                    "subtotal": subtotal,
                }
            )

        return {
            "cart_id": cart.cart_id,
            "customer_id": cart.customer_id,
            "status": cart.status,
            "items": response_items,
            "total_amount": total,
        }
    
    