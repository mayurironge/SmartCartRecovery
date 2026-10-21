from dotenv import load_dotenv
import os

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = os.getenv("SMTP_PORT")
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

# Minutes without cart activity before a cart counts as abandoned.
RECOVERY_THRESHOLD_MINUTES = int(os.getenv("RECOVERY_THRESHOLD_MINUTES", "30"))

# Gemini writes the recovery emails; without a key a plain template is used.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

# Shown before prices in recovery emails.
CURRENCY_SYMBOL = os.getenv("CURRENCY_SYMBOL", "₹")
