from pydantic import BaseModel


class CartCreate(BaseModel):
    customer_id: int


class CartResponse(BaseModel):
    message: str
    cart_id: int