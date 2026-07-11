from datetime import datetime
from pydantic import BaseModel


class OrderResponse(BaseModel):
    order_id: int
    customer_id: int
    cart_id: int
    total_amount: float
    order_status: str
    ordered_at: datetime

class OrderItemView(BaseModel):
    product_id: int
    product_name: str
    quantity: int
    price: float
    subtotal: float


class OrderDetailsResponse(BaseModel):
    order_id: int
    customer_id: int
    cart_id: int
    total_amount: float
    order_status: str
    ordered_at: datetime
    items: list[OrderItemView]

class OrderSummaryResponse(BaseModel):
    order_id: int
    customer_id: int
    cart_id: int
    total_amount: float
    order_status: str
    ordered_at: datetime

class OrderStatusUpdate(BaseModel):
    order_status: str