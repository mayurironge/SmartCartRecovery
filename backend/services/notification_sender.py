class MockNotificationSender:

    @staticmethod
    def send_email(
        customer_id: int,
        message: str,
    ) -> bool:

        print(
            f"[MOCK EMAIL] Sending notification to customer "
            f"{customer_id}: {message}"
        )

        return True