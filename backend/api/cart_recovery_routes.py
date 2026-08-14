from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.services.cart_recovery_service import (
    CartRecoveryService
)


router = APIRouter(
    prefix="/cart-recovery",
    tags=["Cart Recovery"],
)


@router.get("/detect")
def detect_abandoned_carts(
    db: Session = Depends(get_db),
):

    return CartRecoveryService.detect_abandoned_carts(
        db=db,
    )