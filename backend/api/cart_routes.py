from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas.cart_schema import CartCreate, CartResponse
from backend.services.cart_service import CartService

router = APIRouter(
    prefix="/carts",
    tags=["Carts"]
)


@router.post(
    "",
    response_model=CartResponse
)
def create_cart(
    request: CartCreate,
    db: Session = Depends(get_db)
):

    cart = CartService.create_cart(
        db=db,
        customer_id=request.customer_id
    )

    return {
        "message": "Cart created successfully",
        "cart_id": cart.cart_id
    }