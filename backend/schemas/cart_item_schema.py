from pydantic import BaseModel, Field


class CartItemCreate(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0, le=100)


class CartItemUpdate(BaseModel):
    quantity: int = Field(..., gt=0, le=100)


class CartItemResponse(BaseModel):
    message: str