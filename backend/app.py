from fastapi import FastAPI

from backend.api.customer_routes import router

app = FastAPI(
    title="Smart Cart Recovery API",
    version="1.0.0"
)

app.include_router(router)