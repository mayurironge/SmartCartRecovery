from backend.database import SessionLocal
from backend.models.customer import Customer
from backend.schemas.customer_schema import CustomerCreate


def create_customer(customer: CustomerCreate):

    db = SessionLocal()

    try:
        new_customer = Customer(
            first_name=customer.first_name,
            last_name=customer.last_name,
            email=customer.email,
            phone=customer.phone,
        )

        db.add(new_customer)

        db.commit()

        db.refresh(new_customer)

        return {
            "message": "Customer created successfully",
            "customer_id": new_customer.customer_id,
        }

    finally:
        db.close()