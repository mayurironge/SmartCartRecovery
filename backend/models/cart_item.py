from datetime import datetime

from sqlalchemy import ForeignKey, Integer, DateTime

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)

from backend.models.base import Base


class CartItem(Base):
    __tablename__ = "cart_items"

    cart_item_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    cart_id: Mapped[int] = mapped_column(
        ForeignKey("carts.cart_id")
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.product_id")
    )

    quantity: Mapped[int] = mapped_column(Integer)

    added_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    cart = relationship(
        "Cart",
        back_populates="items"
    )

    product = relationship(
        "Product",
        back_populates="cart_items"
    )