from pydantic import BaseModel


class CartCreate(BaseModel):
    customer_id: int


class CartResponse(BaseModel):
    message: str
    cart_id: int


class CartItemView(BaseModel):
    product_id: int
    product_name: str
    price: float
    quantity: int
    subtotal: float


class CartViewResponse(BaseModel):
    cart_id: int
    customer_id: int
    status: str
    items: list[CartItemView]
    total_amount: float