from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base


class CartEvent(Base):
    __tablename__ = "cart_events"

    event_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    cart_id: Mapped[int] = mapped_column(
        ForeignKey("carts.cart_id")
    )

    event_type: Mapped[str] = mapped_column(
        String(50)
    )

    event_time: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )