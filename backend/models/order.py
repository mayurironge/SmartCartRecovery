from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base


class Order(Base):
    __tablename__ = "orders"

    order_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.customer_id")
    )

    cart_id: Mapped[int] = mapped_column(
        ForeignKey("carts.cart_id")
    )

    total_amount: Mapped[float] = mapped_column(
        Numeric(10, 2)
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="PLACED"
    )

    order_date: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    items = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan"
    )