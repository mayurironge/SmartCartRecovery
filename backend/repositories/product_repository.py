from itertools import product

from sqlalchemy.orm import Session

from backend.models.product import Product


class ProductRepository:

    @staticmethod
    def create(db: Session, product: Product):
        db.add(product)
        db.commit()
        db.refresh(product)

        return product

    @staticmethod
    def get_product(
        db: Session,
        product_id: int,
):
        return (
            db.query(Product)
            .filter(Product.product_id == product_id)
            .first()
        )
    
    @staticmethod
    def update_stock(
        db: Session,
        product,
        quantity: int,
):
        product.stock -= quantity