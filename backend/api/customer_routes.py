from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas.customer_schema import CustomerCreate
from backend.services.customer_service import CustomerService

router = APIRouter(tags=["Customers"])


@router.post("/customers")
def add_customer(
    customer: CustomerCreate,
    db: Session = Depends(get_db),
):
    return CustomerService.create_customer(
        db=db,
        customer=customer,
    )
