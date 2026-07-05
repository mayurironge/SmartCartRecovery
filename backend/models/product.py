from sqlalchemy import Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base


class Product(Base):
    __tablename__ = "products"

    product_id: Mapped[int] = mapped_column(Integer, primary_key=True)

    product_name: Mapped[str] = mapped_column(String(150))

    category: Mapped[str] = mapped_column(String(100))

    price: Mapped[float] = mapped_column(Numeric(10, 2))

    stock: Mapped[int] = mapped_column(Integer)