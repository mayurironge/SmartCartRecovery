from sqlalchemy.orm import Session

from backend.models.customer import Customer


class CustomerRepository:

    @staticmethod
    def create(
        db: Session,
        customer: Customer,
    ):
        db.add(customer)
        db.flush()

        return customer

    @staticmethod
    def get_customer(
        db: Session,
        customer_id: int,
    ):
        return (
            db.query(Customer)
            .filter(Customer.customer_id == customer_id)
            .first()
        )
