from sqlalchemy.orm import Session

from backend.models.product import Product
from backend.repositories.product_repository import ProductRepository
from backend.schemas.product_schema import ProductCreate


class ProductService:

    @staticmethod
    def create_product(
        db: Session,
        product: ProductCreate,
    ):

        new_product = ProductRepository.create(
            db=db,
            product=Product(
                product_name=product.product_name,
                category=product.category,
                price=product.price,
                stock=product.stock,
            ),
        )

        db.commit()

        return {
            "message": "Product created successfully",
            "product_id": new_product.product_id,
        }
