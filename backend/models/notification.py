from datetime import datetime

from sqlalchemy import Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base


class Notification(Base):
    __tablename__ = "notifications"

    notification_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    customer_id: Mapped[int | None] = mapped_column(
        ForeignKey("customers.customer_id"),
        nullable=True
    )

    channel: Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )

    message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    sent: Mapped[bool | None] = mapped_column(
        Boolean,
        default=False,
        nullable=True
    )

    created_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=True
    )

    customer = relationship(
        "Customer",
        back_populates="notifications"
    )