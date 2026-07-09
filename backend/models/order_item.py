from sqlalchemy import ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base


class OrderItem(Base):
    __tablename__ = "order_items"

    order_item_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.order_id")
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.product_id")
    )

    quantity: Mapped[int] = mapped_column(
        Integer
    )

    price: Mapped[float] = mapped_column(
        Numeric(10, 2)
    )

    order = relationship(
        "Order",
        back_populates="items"
    )

    product = relationship(
        "Product"
    )