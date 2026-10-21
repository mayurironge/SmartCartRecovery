"""Detects abandoned carts in near real time from the cart-events stream.

Keeps one timer per cart: every event restarts it, checkout cancels it,
and when it runs out the API is asked to recover that one cart. The API
re-checks everything (still active, has items, no recent activity), so a
late or duplicate timer can never send a wrong email.

Timers live in memory. If this service is down they are lost, which is
fine: the scheduled Airflow sweep still catches every abandoned cart.

Run:  python -m streaming.abandonment_consumer
"""

import json
import os
import signal
from datetime import datetime, timedelta, timezone

import requests
from confluent_kafka import Consumer, KafkaException
from confluent_kafka.admin import AdminClient, NewTopic

from backend.config.settings import (
    CART_EVENTS_TOPIC,
    KAFKA_BOOTSTRAP_SERVERS,
    RECOVERY_THRESHOLD_MINUTES,
)
from backend.constants import cart_events

API_URL = os.getenv("SMART_CART_API_URL", "http://api:8000")

# Fire a little after the threshold so the API's own check has passed too.
GRACE = timedelta(seconds=10)
RETRY_DELAY = timedelta(minutes=1)
MAX_ATTEMPTS = 3

# These end a cart's shopping session; nothing left to recover.
CLOSING_EVENTS = {
    cart_events.CHECKOUT_COMPLETED,
    cart_events.ORDER_CANCELLED,
}

running = True


def stop(signum, frame):
    global running
    running = False


def ensure_topic():
    admin = AdminClient({"bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS})
    futures = admin.create_topics([
        NewTopic(CART_EVENTS_TOPIC, num_partitions=3, replication_factor=1)
    ])

    for topic, future in futures.items():
        try:
            future.result()
            print(f"[CONSUMER] Created topic {topic}")
        except KafkaException as exc:
            if "TOPIC_ALREADY_EXISTS" not in str(exc):
                raise


def recover_cart(cart_id):
    response = requests.post(
        f"{API_URL}/cart-recovery/detect",
        params={"cart_id": cart_id},
        timeout=120,
    )
    response.raise_for_status()

    return response.json()


def main():
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)

    threshold = timedelta(minutes=RECOVERY_THRESHOLD_MINUTES)
    ensure_topic()

    consumer = Consumer({
        "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
        "group.id": "abandonment-detector",
        # A new group starts from the oldest kept event.
        "auto.offset.reset": "earliest",
    })
    consumer.subscribe([CART_EVENTS_TOPIC])

    # cart_id -> (when to check it, attempts so far)
    timers = {}

    print(
        f"[CONSUMER] Listening on {CART_EVENTS_TOPIC}; carts are checked "
        f"{RECOVERY_THRESHOLD_MINUTES} min after their last event"
    )

    try:
        while running:
            message = consumer.poll(1.0)

            if message is not None and message.error():
                print(f"[CONSUMER] Kafka error: {message.error()}")

            elif message is not None:
                payload = json.loads(message.value())
                cart_id = payload["cart_id"]

                if payload["event_type"] in CLOSING_EVENTS:
                    timers.pop(cart_id, None)
                else:
                    last_activity = datetime.fromisoformat(payload["event_time"])
                    timers[cart_id] = (last_activity + threshold + GRACE, 0)

            now = datetime.now(timezone.utc)

            for cart_id, (due, attempts) in list(timers.items()):
                if due > now:
                    continue

                del timers[cart_id]

                try:
                    results = recover_cart(cart_id)
                    outcome = (
                        f"reminder {results[0]['recovery_status']}"
                        if results else "nothing to do"
                    )
                    print(f"[CONSUMER] Cart {cart_id}: {outcome}")

                except requests.RequestException as exc:
                    if attempts + 1 < MAX_ATTEMPTS:
                        timers[cart_id] = (now + RETRY_DELAY, attempts + 1)
                    print(f"[CONSUMER] Cart {cart_id}: API call failed: {exc}")

    finally:
        consumer.close()
        print("[CONSUMER] Stopped")


if __name__ == "__main__":
    main()
