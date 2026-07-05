from fastapi import APIRouter

from backend.schemas.customer_schema import CustomerCreate
from backend.services.customer_service import create_customer

router = APIRouter()


@router.post("/customers")
def add_customer(customer: CustomerCreate):
    return create_customer(customer)