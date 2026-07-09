from sqlalchemy.orm import Session

from backend.models.customer import Customer


class CustomerRepository:

    @staticmethod
    def create(
        db: Session,
        customer: Customer,
    ):
        db.add(customer)
        db.commit()
        db.refresh(customer)

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