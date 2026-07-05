from fastapi import APIRouter

from backend.schemas.product_schema import ProductCreate
from backend.services.product_service import create_product

router = APIRouter(prefix="/products", tags=["Products"])


@router.post("")
def add_product(product: ProductCreate):
    return create_product(product)