from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    product_name: str = Field(min_length=2, max_length=150)
    category: str
    price: float = Field(gt=0)
    stock: int = Field(ge=0)