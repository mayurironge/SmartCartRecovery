from fastapi import FastAPI
import backend.models
from backend.api.customer_routes import router as customer_router
from backend.api.product_routes import router as product_router
from backend.api.cart_routes import router as cart_router
app = FastAPI(
    title="Smart Cart Recovery API",
    version="1.0.0"
)

app.include_router(customer_router)
app.include_router(product_router)
app.include_router(cart_router)
