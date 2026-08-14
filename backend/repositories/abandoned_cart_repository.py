class AbandonedCartRepository:

    @staticmethod
    def get_abandoned_candidates(
        db,
        threshold_time,
    ):
        ...

    @staticmethod
    def mark_abandoned(
        db,
        cart,
    ):
        ...