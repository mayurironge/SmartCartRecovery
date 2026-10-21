"""Fills the database with about 60 days of realistic demo shop history.

Run inside Docker:
    docker compose exec api python -m backend.scripts.seed_demo_data
    docker compose exec api python -m backend.scripts.seed_demo_data --reset

Every abandoned demo cart gets a closed recovery, so the scheduled
detection never picks one up and never emails anyone. Demo customers
also use the reserved shop.example domain, which cannot receive mail.
"""

import argparse
import random
from datetime import datetime, timedelta, timezone

from faker import Faker
from sqlalchemy import text

from backend.config.settings import CURRENCY_SYMBOL
from backend.constants import (
    cart_events,
    cart_status,
    order_status,
    recovery_status,
)
from backend.database import SessionLocal
from backend.models import (
    Cart,
    CartEvent,
    CartItem,
    CartRecovery,
    Customer,
    Notification,
    Order,
    OrderItem,
    Product,
)
from backend.repositories.cart_recovery_repository import (
    CartRecoveryRepository,
)
from genai.prompt_templates import fallback_email

DEMO_DOMAIN = "shop.example"
DAYS = 60
CUSTOMERS = 400
CARTS = 650

# Share of carts that check out in the same visit; the rest are abandoned.
DIRECT_CHECKOUT_RATE = 0.35
# Share of abandoned carts whose reminder could not be delivered.
SEND_FAILURE_RATE = 0.06
# Share of reminded carts that come back and buy.
RECOVERY_RATE = 0.22
ORDER_CANCEL_RATE = 0.05

PRODUCTS = [
    ("Wireless Mouse", "Electronics", 799),
    ("Mechanical Keyboard", "Electronics", 2499),
    ("USB-C Hub", "Electronics", 1299),
    ("Noise Cancelling Headphones", "Electronics", 5999),
    ("Bluetooth Speaker", "Electronics", 1899),
    ("Smart Watch", "Electronics", 3499),
    ("Laptop Stand", "Accessories", 1199),
    ("Phone Case", "Accessories", 399),
    ("Laptop Sleeve", "Accessories", 899),
    ("Webcam Cover Pack", "Accessories", 199),
    ("Running Shoes", "Fashion", 3299),
    ("Cotton T-Shirt", "Fashion", 599),
    ("Denim Jacket", "Fashion", 2799),
    ("Backpack", "Fashion", 1599),
    ("Sunglasses", "Fashion", 1299),
    ("Yoga Mat", "Fitness", 999),
    ("Dumbbell Set", "Fitness", 2299),
    ("Water Bottle", "Fitness", 449),
    ("Resistance Bands", "Fitness", 699),
    ("Coffee Maker", "Home", 4499),
    ("Desk Lamp", "Home", 1099),
    ("Scented Candles", "Home", 549),
    ("Throw Pillow", "Home", 699),
    ("Notebook Set", "Stationery", 349),
    ("Fountain Pen", "Stationery", 1499),
]

CHECKOUT = "checkout"
RECOVERED = "recovered"
NOTIFIED = "notified"
EXPIRED = "expired"


def _naive(moment):
    # carts, cart_items, orders and notifications store naive UTC times.
    return moment.replace(tzinfo=None)


def _pick_outcome(rng):
    if rng.random() < DIRECT_CHECKOUT_RATE:
        return CHECKOUT

    if rng.random() < SEND_FAILURE_RATE:
        return EXPIRED

    return RECOVERED if rng.random() < RECOVERY_RATE else NOTIFIED


def reset(db):
    db.execute(text(
        "TRUNCATE notifications, cart_recovery, cart_events, order_items, "
        "orders, cart_items, carts, products, customers "
        "RESTART IDENTITY CASCADE"
    ))
    db.commit()


def _create_catalogue(db, fake):
    products = [
        Product(product_name=name, category=category, price=price, stock=500)
        for name, category, price in PRODUCTS
    ]
    db.add_all(products)

    customers = []
    for n in range(CUSTOMERS):
        first, last = fake.first_name(), fake.last_name()
        customers.append(Customer(
            first_name=first,
            last_name=last,
            email=f"{first}.{last}{n}@{DEMO_DOMAIN}".lower(),
            phone=fake.numerify("9#########"),
        ))
    db.add_all(customers)
    db.flush()

    return products, customers


def _add_order(db, rng, now, cart, lines, total, checkout_at, events):
    age_days = (now - checkout_at).days
    status = (
        order_status.DELIVERED if age_days > 7
        else order_status.SHIPPED if age_days > 3
        else order_status.PROCESSING if age_days > 1
        else order_status.PLACED
    )
    cancelled = rng.random() < ORDER_CANCEL_RATE

    order = Order(
        customer_id=cart.customer_id,
        cart_id=cart.cart_id,
        total_amount=total,
        status=order_status.CANCELLED if cancelled else status,
        order_date=_naive(checkout_at),
    )
    db.add(order)
    db.flush()

    for product, quantity in lines:
        db.add(OrderItem(
            order_id=order.order_id,
            product_id=product.product_id,
            quantity=quantity,
            price=product.price,
        ))

    cart.status = cart_status.CHECKED_OUT
    cart.updated_at = _naive(checkout_at)
    events.append((cart_events.CHECKOUT_COMPLETED, checkout_at))

    if cancelled:
        events.append((
            cart_events.ORDER_CANCELLED,
            min(checkout_at + timedelta(hours=rng.uniform(2, 24)), now),
        ))


def _add_recovery(
    db, rng, now, cart, customer, lines, total, last_activity, outcome
):
    detected = last_activity + timedelta(minutes=rng.uniform(30, 45))

    subject, body = fallback_email(
        customer.first_name,
        [
            {
                "product_name": p.product_name,
                "quantity": q,
                "subtotal": float(p.price) * q,
            }
            for p, q in lines
        ],
        total,
        CURRENCY_SYMBOL,
    )

    recovery = CartRecovery(
        cart_id=cart.cart_id,
        recovery_status=recovery_status.NOTIFIED,
        attempts=0,
        detected_at=detected,
    )
    sent = outcome != EXPIRED

    if outcome == EXPIRED:
        recovery.recovery_status = recovery_status.EXPIRED
        recovery.attempts = 3

    else:
        recovery.notified_at = detected + timedelta(minutes=rng.uniform(0, 15))

    if outcome == RECOVERED:
        recovery.recovery_status = recovery_status.RECOVERED

    db.add(recovery)
    db.flush()

    db.add(Notification(
        customer_id=customer.customer_id,
        recovery_id=recovery.recovery_id,
        channel="EMAIL",
        subject=subject,
        message=body,
        sent=sent,
        created_at=_naive(detected),
    ))

    if outcome != RECOVERED:
        return None

    # Customers come back between an hour and two days later, never in
    # the future.
    return min(
        recovery.notified_at + timedelta(hours=rng.uniform(1, 48)),
        now - timedelta(hours=1),
    )


def seed(db, rng, fake):
    now = datetime.now(timezone.utc)
    products, customers = _create_catalogue(db, fake)

    # Expensive items get left behind more often.
    weights = [1 + p.price / 2000 for p in products]

    # A customer may hold only one ACTIVE cart, like in the real app.
    free_customers = list(customers)
    counts = {CHECKOUT: 0, RECOVERED: 0, NOTIFIED: 0, EXPIRED: 0}

    for _ in range(CARTS):
        outcome = _pick_outcome(rng)
        stays_active = outcome in (NOTIFIED, EXPIRED)

        if stays_active and not free_customers:
            outcome, stays_active = CHECKOUT, False

        if stays_active:
            customer = free_customers.pop(rng.randrange(len(free_customers)))
        else:
            customer = rng.choice(customers)

        # Keep the newest cart a few hours old so it is fully played out.
        started = now - timedelta(
            days=rng.uniform(0, DAYS),
            hours=rng.uniform(6, 10),
        )

        cart = Cart(
            customer_id=customer.customer_id,
            status=cart_status.ACTIVE,
            created_at=_naive(started),
            updated_at=_naive(started),
        )
        db.add(cart)
        db.flush()

        events = [(cart_events.CART_CREATED, started)]
        moment = started
        lines = []

        picked = set(rng.choices(products, weights, k=rng.randint(1, 4)))
        for product in sorted(picked, key=lambda p: p.product_id):
            moment += timedelta(minutes=rng.uniform(1, 8))
            quantity = rng.choice([1, 1, 1, 2, 2, 3])
            db.add(CartItem(
                cart_id=cart.cart_id,
                product_id=product.product_id,
                quantity=quantity,
                added_at=_naive(moment),
            ))
            events.append((cart_events.PRODUCT_ADDED, moment))
            lines.append((product, quantity))

        total = sum(float(p.price) * q for p, q in lines)

        if outcome == CHECKOUT:
            checkout_at = moment + timedelta(minutes=rng.uniform(2, 15))
        else:
            checkout_at = _add_recovery(
                db, rng, now, cart, customer, lines, total, moment, outcome
            )

        if checkout_at:
            _add_order(db, rng, now, cart, lines, total, checkout_at, events)

        db.add_all(
            CartEvent(cart_id=cart.cart_id, event_type=kind, event_time=at)
            for kind, at in events
        )
        counts[outcome] += 1

    db.commit()
    return counts


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--reset",
        action="store_true",
        help="delete ALL existing data first",
    )
    args = parser.parse_args()

    rng = random.Random(42)
    fake = Faker("en_IN")
    fake.seed_instance(42)

    db = SessionLocal()

    try:
        if args.reset:
            reset(db)

        already = db.execute(
            text("SELECT count(*) FROM customers WHERE email LIKE :d"),
            {"d": f"%@{DEMO_DOMAIN}"},
        ).scalar()

        if already:
            raise SystemExit(
                "Demo data already exists. Use --reset to start over."
            )

        counts = seed(db, rng, fake)

        # Safety check: no demo cart may be waiting for a reminder.
        waiting = CartRecoveryRepository.get_abandoned_carts(
            db=db,
            threshold_minutes=0,
        )
        demo_waiting = [
            entry for entry in waiting
            if entry["cart"].customer.email.endswith(f"@{DEMO_DOMAIN}")
        ]
        assert not demo_waiting, "demo carts would be emailed"

        print(
            f"Seeded {CUSTOMERS} customers, {len(PRODUCTS)} products and "
            f"{CARTS} carts: {counts[CHECKOUT]} direct checkouts, "
            f"{counts[RECOVERED]} recovered, {counts[NOTIFIED]} reminded but "
            f"not back, {counts[EXPIRED]} expired."
        )

    finally:
        db.close()


if __name__ == "__main__":
    main()
