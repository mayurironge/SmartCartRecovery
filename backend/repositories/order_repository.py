from sqlalchemy.orm import Session

from backend.models.order import Order
from backend.models.order_item import OrderItem


class OrderRepository:

    @staticmethod
    def create_order(
        db: Session,
        customer_id: int,
        cart_id: int,
        total_amount: float,
    ):

        order = Order(
            customer_id=customer_id,
            cart_id=cart_id,
            total_amount=total_amount,
            status="PLACED",
        )

        db.add(order)
        db.flush()

        return order

    @staticmethod
    def add_order_item(
        db: Session,
        order_id: int,
        product_id: int,
        quantity: int,
        price: float,
    ):

        order_item = OrderItem(
            order_id=order_id,
            product_id=product_id,
            quantity=quantity,
            price=price,
        )

        db.add(order_item)

    @staticmethod
    def commit(db: Session):
        db.commit()

    @staticmethod
    def rollback(db: Session):
        db.rollback()