from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.constants import cart_events, cart_status
from backend.constants.order_status import (
    ALL_STATUSES,
    ALLOWED_TRANSITIONS,
    CANCELLED,
)
from backend.repositories.cart_event_repository import CartEventRepository
from backend.repositories.cart_repository import CartRepository
from backend.repositories.cart_item_repository import CartItemRepository
from backend.repositories.product_repository import ProductRepository
from backend.repositories.order_repository import OrderRepository
from backend.repositories.customer_repository import CustomerRepository
from backend.repositories.cart_recovery_repository import (
    CartRecoveryRepository,
)

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
            products = {}

            # Validate stock and calculate total
            for item in cart_items:

                product = ProductRepository.get_product(
                    db=db,
                    product_id=item.product_id,
                )

                if not product:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Product {item.product_id} is no longer available",
                    )

                products[item.product_id] = product

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

                product = products[item.product_id]

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
                status=cart_status.CHECKED_OUT,
            )

            CartRecoveryRepository.close_for_checkout(
                db=db,
                cart_id=cart.cart_id,
            )

            CartEventRepository.create_event(
                db=db,
                cart_id=cart.cart_id,
                event_type=cart_events.CHECKOUT_COMPLETED,
            )

            OrderRepository.commit(db)

            return order

        except Exception:
            OrderRepository.rollback(db)
            raise

       
    @staticmethod
    def get_all_orders(
        db: Session,
    ):

        orders = OrderRepository.get_all_orders(db)

        response = []

        for order in orders:

            response.append(
                {
                    "order_id": order.order_id,
                    "customer_id": order.customer_id,
                    "cart_id": order.cart_id,
                    "total_amount": float(order.total_amount),
                    "order_status": order.status,
                    "ordered_at": order.order_date,
                }
            )

        return response
    #oders by order_id
    @staticmethod
    def get_order(
        db: Session,
        order_id: int,
):

        order = OrderRepository.get_order(
            db=db,
            order_id=order_id,
        )

        if not order:
            raise HTTPException(
                status_code=404,
                detail="Order not found",
            )

        items = []

        for item in order.items:

            subtotal = float(item.price) * item.quantity

            items.append(
                {
                    "product_id": item.product.product_id,
                    "product_name": item.product.product_name,
                    "quantity": item.quantity,
                    "price": float(item.price),
                    "subtotal": subtotal,
                }
            )

        return {
            "order_id": order.order_id,
            "customer_id": order.customer_id,
            "cart_id": order.cart_id,
            "total_amount": float(order.total_amount),
            "order_status": order.status,
            "ordered_at": order.order_date,
            "items": items,
        }
    
    #order by customer_id
    @staticmethod
    def get_orders_by_customer(
        db: Session,
        customer_id: int,
):

        orders = OrderRepository.get_orders_by_customer(
            db=db,
            customer_id=customer_id,
        )

        if not orders:
            raise HTTPException(
                status_code=404,
                detail="No orders found for this customer",
            )

        response = []

        for order in orders:

            response.append(
                {
                    "order_id": order.order_id,
                    "customer_id": order.customer_id,
                    "cart_id": order.cart_id,
                    "total_amount": float(order.total_amount),
                    "order_status": order.status,
                    "ordered_at": order.order_date,
                }
            )

        return response
    
    @staticmethod
    def update_order_status(
    db: Session,
    order_id: int,
    order_status: str,
):

        order = OrderRepository.get_order(
            db=db,
            order_id=order_id,
        )

        if not order:
            raise HTTPException(
                status_code=404,
                detail="Order not found",
            )

        if order_status not in ALL_STATUSES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid order status: {order_status}",
            )

        # Cancelling must also restore stock.
        if order_status == CANCELLED:
            return OrderService.cancel_order(
                db=db,
                order_id=order_id,
            )

        current_status = order.status

        if order_status not in ALLOWED_TRANSITIONS.get(current_status, []):
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Cannot change order status from "
                    f"{current_status} to {order_status}"
                ),
            )

        OrderRepository.update_order_status(
            db=db,
            order=order,
            order_status=order_status,
        )

        OrderRepository.commit(db)

        return {
            "message": "Order status updated successfully",
            "order_id": order.order_id,
            "order_status": order.status,
        }
    
    @staticmethod
    def cancel_order(
        db: Session,
        order_id: int,
):

        try:

            order = OrderRepository.get_order(
                db=db,
                order_id=order_id,
            )

            if not order:
                raise HTTPException(
                    status_code=404,
                    detail="Order not found",
                )

            # Cannot cancel twice
            if order.status == CANCELLED:
                raise HTTPException(
                    status_code=400,
                    detail="Order is already cancelled",
                )

            # Same rule as status transitions: only before shipping
            if CANCELLED not in ALLOWED_TRANSITIONS.get(order.status, []):
                raise HTTPException(
                    status_code=400,
                    detail=f"{order.status} orders cannot be cancelled",
                )

            # Restore inventory
            for item in order.items:

                product = ProductRepository.get_product(
                    db=db,
                    product_id=item.product_id,
                )

                ProductRepository.restore_stock(
                    db=db,
                    product=product,
                    quantity=item.quantity,
                )

            # Update status
            OrderRepository.cancel_order(
                db=db,
                order=order,
            )

            CartEventRepository.create_event(
                db=db,
                cart_id=order.cart_id,
                event_type=cart_events.ORDER_CANCELLED,
            )

            OrderRepository.commit(db)

            return {
                "message": "Order cancelled successfully",
                "order_id": order.order_id,
                "order_status": order.status,
            }

        except Exception:
            OrderRepository.rollback(db)
            raise


    @staticmethod
    def get_order_history(
        db: Session,
        customer_id: int | None = None,
        status: str | None = None,
        start_date=None,
        end_date=None,
):

        # 1. Validate order status
        if status and status not in ALL_STATUSES:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Invalid order status. "
                    "Allowed values are PLACED, PROCESSING, "
                    "SHIPPED, DELIVERED and CANCELLED."
                ),
            )

        # 2. Validate date range
        if (
            start_date
            and end_date
            and start_date > end_date
        ):
            raise HTTPException(
                status_code=400,
                detail="start_date cannot be later than end_date.",
            )

        # 3. Validate customer exists
        if customer_id:

            customer = CustomerRepository.get_customer(
                db=db,
                customer_id=customer_id,
            )

            if not customer:
                raise HTTPException(
                    status_code=404,
                    detail="Customer not found.",
                )

        # 4. Fetch orders
        orders = OrderRepository.get_order_history(
            db=db,
            customer_id=customer_id,
            status=status,
            start_date=start_date,
            end_date=end_date,
        )

        # 5. No matching orders
        if not orders:
            raise HTTPException(
                status_code=404,
                detail="No matching orders found.",
            )

        response = []

        for order in orders:

            response.append(
                {
                    "order_id": order.order_id,
                    "customer_id": order.customer_id,
                    "cart_id": order.cart_id,
                    "total_amount": float(order.total_amount),
                    "order_status": order.status,
                    "ordered_at": order.order_date,
                }
            )

        return response