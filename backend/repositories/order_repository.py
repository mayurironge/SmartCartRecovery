from sqlalchemy.orm import Session

from backend.models import order
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
    def get_all_orders(
        db: Session,
    ):
            return (
                db.query(Order)
                .order_by(Order.order_id)
                .all()
            )
    
    @staticmethod
    def get_order(
        db: Session,
        order_id: int,
):

        return (
            db.query(Order)
            .filter(Order.order_id == order_id)
            .first()
        )
    @staticmethod
    def get_orders_by_customer(
        db: Session,
        customer_id: int,
):

        return (
            db.query(Order)
            .filter(Order.customer_id == customer_id)
            .all()
        )
    
    @staticmethod
    def update_order_status(
        db: Session,
        order: Order,
        order_status: str,
):


        order.status = order_status

   
    @staticmethod
    def cancel_order(
        db: Session,
        order: Order,
):
        order.status = "CANCELLED"


    @staticmethod
    def get_order_history(
        db: Session,
        customer_id: int | None = None,
        status: str | None = None,
        start_date=None,
        end_date=None,
):

            query = db.query(Order)

            if customer_id:
                query = query.filter(
                    Order.customer_id == customer_id
                )

            if status:
                query = query.filter(
                    Order.status == status
                )

            if start_date:
                query = query.filter(
                    Order.order_date >= start_date
                )

            if end_date:
                query = query.filter(
                    Order.order_date <= end_date
                )

            return (
                query
                .order_by(Order.order_date.desc())
                .all()
            )

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