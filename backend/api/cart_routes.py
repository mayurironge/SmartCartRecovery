from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db

from backend.schemas.cart_schema import (
    CartCreate,
    CartResponse,
    CartViewResponse,
)

from backend.schemas.cart_item_schema import (
    CartItemCreate,
    CartItemUpdate,
    CartItemResponse,
)

from backend.services.cart_service import CartService
from backend.services.cart_item_service import CartItemService


router = APIRouter(
    prefix="/carts",
    tags=["Carts"]
)


# -----------------------------
# Create Cart
# -----------------------------
@router.post(
    "",
    response_model=CartResponse
)
def create_cart(
    request: CartCreate,
    db: Session = Depends(get_db),
):

    cart = CartService.create_cart(
        db=db,
        customer_id=request.customer_id,
    )

    return {
        "message": "Cart created successfully",
        "cart_id": cart.cart_id,
    }


# -----------------------------
# Add Product to Cart
# -----------------------------
@router.post(
    "/{cart_id}/items",
    response_model=CartItemResponse,
)
def add_product_to_cart(
    cart_id: int,
    request: CartItemCreate,
    db: Session = Depends(get_db),
):

    CartItemService.add_product(
        db=db,
        cart_id=cart_id,
        product_id=request.product_id,
        quantity=request.quantity,
    )

    return {
        "message": "Product added to cart successfully"
    }


# -----------------------------
# Remove Product from Cart
# -----------------------------
@router.delete(
    "/{cart_id}/items/{product_id}"
)
def remove_product_from_cart(
    cart_id: int,
    product_id: int,
    db: Session = Depends(get_db),
):

    return CartItemService.remove_product(
        db=db,
        cart_id=cart_id,
        product_id=product_id,
    )


# -----------------------------
# Update Product Quantity
# -----------------------------
@router.put(
    "/{cart_id}/items/{product_id}",
    response_model=CartItemResponse,
)
def update_cart_item(
    cart_id: int,
    product_id: int,
    request: CartItemUpdate,
    db: Session = Depends(get_db),
):

    return CartItemService.update_quantity(
        db=db,
        cart_id=cart_id,
        product_id=product_id,
        quantity=request.quantity,
    )

@router.get(
    "/{cart_id}",
    response_model=CartViewResponse,
)
def view_cart(
    cart_id: int,
    db: Session = Depends(get_db),
):

    return CartService.view_cart(
        db=db,
        cart_id=cart_id,
    )

@router.delete(
    "/{cart_id}/items",
    response_model=CartItemResponse,
)
def empty_cart(
    cart_id: int,
    db: Session = Depends(get_db),
):

    return CartItemService.empty_cart(
        db=db,
        cart_id=cart_id,
    )