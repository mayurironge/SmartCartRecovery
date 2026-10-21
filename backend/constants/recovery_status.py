# Detected and waiting for a reminder to be delivered.
PENDING = "PENDING"
NOTIFIED = "NOTIFIED"
# The customer checked out after being notified.
RECOVERED = "RECOVERED"
# Closed without a delivered reminder (send retries exhausted,
# or the customer checked out before a reminder went out).
EXPIRED = "EXPIRED"
