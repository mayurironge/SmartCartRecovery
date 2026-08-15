from sqlalchemy import Column, Integer, ForeignKey, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from backend.models.base import Base


class CartRecovery(Base):

    __tablename__ = "cart_recovery"

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

    detected_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    notified_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    cart = relationship("Cart")