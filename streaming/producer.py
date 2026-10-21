"""Publishes cart events to Kafka once they are safely in the database.

Hooks into the SQLAlchemy session: events are collected when they are
flushed and published only after the transaction commits, so a rolled-back
change is never announced. Publishing is best effort: if Kafka is down the
API keeps working and the scheduled Airflow sweep still finds abandoned
carts.
"""

import json

from confluent_kafka import Producer
from sqlalchemy import event

from backend.config.settings import CART_EVENTS_TOPIC, KAFKA_BOOTSTRAP_SERVERS
from backend.models.cart_event import CartEvent

PENDING_KEY = "pending_cart_events"

_producer = None


def _get_producer():
    global _producer

    if _producer is None:
        _producer = Producer({
            "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
            "client.id": "smartcart-api",
            # Give up on a message after 10 s instead of retrying for minutes.
            "message.timeout.ms": 10_000,
        })

    return _producer


def _report(error, message):
    if error is not None:
        print(f"[KAFKA ERROR] Could not publish cart event: {error}")


def publish(events):
    producer = _get_producer()

    for payload in events:
        try:
            producer.produce(
                CART_EVENTS_TOPIC,
                # Same key, same partition: a cart's events stay in order.
                key=str(payload["cart_id"]),
                value=json.dumps(payload),
                on_delivery=_report,
            )

        except Exception as exc:
            print(f"[KAFKA ERROR] Could not queue cart event: {exc}")

    # Sends in the background; this only triggers delivery callbacks.
    producer.poll(0)


def flush(timeout=5):
    if _producer is not None:
        _producer.flush(timeout)


def install(session_factory):
    """Publish cart events committed through sessions from this factory."""

    if not KAFKA_BOOTSTRAP_SERVERS:
        print("[KAFKA] KAFKA_BOOTSTRAP_SERVERS not set; cart events not streamed")
        return

    # Registering twice would publish every event twice.
    if event.contains(session_factory, "after_commit", _send):
        return

    event.listen(session_factory, "after_flush", _collect)
    event.listen(session_factory, "after_commit", _send)
    event.listen(session_factory, "after_soft_rollback", _discard)


def _collect(session, flush_context):
    # Read the values now; after commit the objects are expired.
    session.info.setdefault(PENDING_KEY, []).extend(
        {
            "event_id": obj.event_id,
            "cart_id": obj.cart_id,
            "event_type": obj.event_type,
            "event_time": obj.event_time.isoformat(),
        }
        for obj in session.new
        if isinstance(obj, CartEvent)
    )


def _send(session):
    events = session.info.pop(PENDING_KEY, [])

    if events:
        publish(events)


def _discard(session, previous_transaction):
    session.info.pop(PENDING_KEY, None)

