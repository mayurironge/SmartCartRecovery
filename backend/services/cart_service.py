from fastapi import HTTPException
from sqlalchemy.orm import Session
from backend.repositories.cart_event_repository import CartEventRepository
from backend.repositories.cart_repository import CartRepository
from backend.repositories.customer_repository import CustomerRepository


class CartService:

    @staticmethod
    def create_cart(
        db: Session,
        customer_id: int,
    ):
        
        # Check whether customer exists
        customer = CustomerRepository.get_customer(
            db=db,
            customer_id=customer_id,
        )

        if not customer:
            raise HTTPException(
                status_code=404,
                detail="Customer not found",
            )

        # Check whether customer already has an active cart
        existing_cart = CartRepository.get_active_cart(
            db=db,
            customer_id=customer_id,
        )

        if existing_cart:
            return existing_cart, False

        # Create a new cart
        new_cart = CartRepository.create_cart(
            db=db,
            customer_id=customer_id,
        )

        CartEventRepository.create_event(
            db=db,
            cart_id=new_cart.cart_id,
            event_type="CART_CREATED",
)

        return new_cart, True

    @staticmethod
    def view_cart(
        db: Session,
        cart_id: int,
):

        cart = CartRepository.get_cart(
            db=db,
            cart_id=cart_id,
        )

        if not cart:
            raise HTTPException(
                status_code=404,
                detail="Cart not found",
            )

        items = []
        total_amount = 0

        for item in cart.items:

            subtotal = float(item.product.price) * item.quantity
            total_amount += subtotal

            items.append(
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
            "items": items,
            "total_amount": total_amount,
        }