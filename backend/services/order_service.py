from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.repositories.cart_repository import CartRepository
from backend.repositories.cart_item_repository import CartItemRepository
from backend.repositories.product_repository import ProductRepository
from backend.repositories.order_repository import OrderRepository


class OrderService:

    @staticmethod
    def checkout(
        db: Session,
        cart_id: int,
    ):

        try:

            # Fetch only ACTIVE cart
            cart = CartRepository.get_active_cart_by_id(
                db=db,
                cart_id=cart_id,
            )

            if not cart:
                raise HTTPException(
                    status_code=400,
                    detail="Cart is already checked out or does not exist.",
                )

            cart_items = CartItemRepository.get_cart_items(
                db=db,
                cart_id=cart_id,
            )

            if not cart_items:
                raise HTTPException(
                    status_code=400,
                    detail="Cart is empty",
                )

            total_amount = 0

            # Validate stock and calculate total
            for item in cart_items:

                product = ProductRepository.get_product(
                    db=db,
                    product_id=item.product_id,
                )

                if product.stock < item.quantity:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Insufficient stock for {product.product_name}",
                    )

                total_amount += float(product.price) * item.quantity

            # Create order
            order = OrderRepository.create_order(
                db=db,
                customer_id=cart.customer_id,
                cart_id=cart.cart_id,
                total_amount=total_amount,
            )

            # Copy items to order and reduce stock
            for item in cart_items:

                product = ProductRepository.get_product(
                    db=db,
                    product_id=item.product_id,
                )

                OrderRepository.add_order_item(
                    db=db,
                    order_id=order.order_id,
                    product_id=product.product_id,
                    quantity=item.quantity,
                    price=product.price,
                )

                ProductRepository.update_stock(
                    db=db,
                    product=product,
                    quantity=item.quantity,
                )

            # Mark cart as checked out
            CartRepository.update_status(
                db=db,
                cart=cart,
                status="CHECKED_OUT",
            )

            OrderRepository.commit(db)

            return order

        except Exception:
            OrderRepository.rollback(db)
            raise