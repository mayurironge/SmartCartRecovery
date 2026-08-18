import smtplib
from email.message import EmailMessage

from backend.config.settings import (
    SMTP_HOST,
    SMTP_PORT,
    SMTP_USERNAME,
    SMTP_PASSWORD,
)


class EmailNotificationSender:

    @staticmethod
    def send_email(
        recipient_email: str,
        subject: str,
        message: str,
    ) -> bool:

        email = EmailMessage()

        email["Subject"] = subject
        email["From"] = SMTP_USERNAME
        email["To"] = recipient_email

        email.set_content(message)

        try:
            with smtplib.SMTP(
                SMTP_HOST,
                int(SMTP_PORT),
            ) as server:

                server.ehlo()
                server.starttls()
                server.ehlo()

                server.login(
                    SMTP_USERNAME,
                    SMTP_PASSWORD,
                )

                server.send_message(email)

            return True

        except Exception as exc:
            print(f"[EMAIL ERROR] Failed to send email: {exc}")
            return False
        