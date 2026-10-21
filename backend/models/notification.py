from datetime import datetime

from sqlalchemy import Integer, String, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base


class Notification(Base):
    __tablename__ = "notifications"

    # One notification per recovery, so retries reuse it.
    __table_args__ = (
        Index(
            "uq_notifications_recovery_id",
            "recovery_id",
            unique=True,
        ),
    )

    notification_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    customer_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("customers.customer_id"),
        nullable=True,
    )

    recovery_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("cart_recovery.recovery_id"),
        nullable=True,
    )

    channel: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    sent: Mapped[bool | None] = mapped_column(
        Boolean,
        default=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    customer = relationship("Customer")

    recovery = relationship("CartRecovery")