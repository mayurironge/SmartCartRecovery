from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas.order_schema import OrderResponse
from backend.services.order_service import OrderService

router = APIRouter(
    prefix="/orders",
    tags=["Orders"]
)


@router.post(
    "/checkout/{cart_id}",
    response_model=OrderResponse,
)
def checkout(
    cart_id: int,
    db: Session = Depends(get_db),
):

    order = OrderService.checkout(
        db=db,
        cart_id=cart_id,
    )

    return {
        "message": "Order placed successfully",
        "order_id": order.order_id,
    }