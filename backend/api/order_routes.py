from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from backend.database import get_db
from datetime import date
from fastapi import Query
from backend.services.order_service import OrderService
from backend.schemas.order_schema import (
    OrderResponse,
    OrderDetailsResponse,
    OrderSummaryResponse,
    OrderStatusUpdate)

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
        "order_id": order.order_id,
        "customer_id": order.customer_id,
        "cart_id": order.cart_id,
        "total_amount": float(order.total_amount),
        "order_status": order.status,
        "ordered_at": order.order_date,
    }

@router.get(
    "",
    response_model=List[OrderResponse],
)
def get_all_orders(
    db: Session = Depends(get_db),
):

    return OrderService.get_all_orders(db)

@router.get(
    "/history",
    response_model=list[OrderSummaryResponse],
)
def get_order_history(
    customer_id: int | None = Query(
        default=None,
        ge=1,
    ),
    status: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
):

    return OrderService.get_order_history(
        db=db,
        customer_id=customer_id,
        status=status,
        start_date=start_date,
        end_date=end_date,
    )
@router.get(
    "/{order_id}",
    response_model=OrderDetailsResponse,
)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
):

    return OrderService.get_order(
        db=db,
        order_id=order_id,
    )

@router.get(
    "/customer/{customer_id}",
    response_model=list[OrderSummaryResponse],
)
def get_orders_by_customer(
    customer_id: int,
    db: Session = Depends(get_db),
):

    return OrderService.get_orders_by_customer(
        db=db,
        customer_id=customer_id,
    )
@router.put("/{order_id}/status")
def update_order_status(
    order_id: int,
    request: OrderStatusUpdate,
    db: Session = Depends(get_db),
):

    return OrderService.update_order_status(
        db=db,
        order_id=order_id,
        order_status=request.order_status,
    )

@router.put("/{order_id}/cancel")
def cancel_order(
    order_id: int,
    db: Session = Depends(get_db),
):

    return OrderService.cancel_order(
        db=db,
        order_id=order_id,
    )

