from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, Index, text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from backend.constants import recovery_status
from backend.models.base import Base


class CartRecovery(Base):

    __tablename__ = "cart_recovery"

    # A cart can be abandoned (and recovered) more than once, but only one
    # recovery per cart may be waiting for delivery at a time. Concurrent
    # detection runs rely on this to avoid opening duplicates.
    __table_args__ = (
        Index(
            "uq_cart_recovery_open_cart",
            "cart_id",
            unique=True,
            postgresql_where=text(
                f"recovery_status = '{recovery_status.PENDING}'"
            ),
        ),
    )

    recovery_id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    cart_id = Column(
        Integer,
        ForeignKey("carts.cart_id"),
        nullable=False,
    )

    recovery_status = Column(
        String,
        nullable=False,
    )

    attempts = Column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    detected_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    notified_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    cart = relationship("Cart")
