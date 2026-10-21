from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.models.customer import Customer
from backend.repositories.customer_repository import CustomerRepository
from backend.schemas.customer_schema import CustomerCreate


class CustomerService:

    @staticmethod
    def create_customer(
        db: Session,
        customer: CustomerCreate,
    ):

        try:
            new_customer = CustomerRepository.create(
                db=db,
                customer=Customer(
                    first_name=customer.first_name,
                    last_name=customer.last_name,
                    email=customer.email,
                    phone=customer.phone,
                ),
            )

            db.commit()

        except IntegrityError:
            db.rollback()

            raise HTTPException(
                status_code=409,
                detail="A customer with this email already exists",
            )

        return {
            "message": "Customer created successfully",
            "customer_id": new_customer.customer_id,
        }
