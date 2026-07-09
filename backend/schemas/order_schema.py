from pydantic import BaseModel


class OrderResponse(BaseModel):
    message: str
    order_id: int