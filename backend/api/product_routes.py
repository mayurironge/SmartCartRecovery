from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas.product_schema import ProductCreate
from backend.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["Products"])


@router.post("")
def add_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
):
    return ProductService.create_product(
        db=db,
        product=product,
    )
