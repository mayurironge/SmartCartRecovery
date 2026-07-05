from backend.models.product import Product


class ProductRepository:

    def create(self, db, product):
        db.add(product)
        db.commit()
        db.refresh(product)

        return product