from backend.database import SessionLocal
from backend.models.product import Product
from backend.repositories.product_repository import ProductRepository
from backend.schemas.product_schema import ProductCreate


repository = ProductRepository()


def create_product(product: ProductCreate):

    db = SessionLocal()

    try:

        new_product = Product(
            product_name=product.product_name,
            category=product.category,
            price=product.price,
            stock=product.stock,
        )

        product = repository.create(db, new_product)

        return {
            "message": "Product created successfully",
            "product_id": product.product_id,
        }

    finally:
        db.close()