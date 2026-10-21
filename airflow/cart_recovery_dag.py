"""Runs abandoned-cart detection on a schedule.

The DAG calls the backend API rather than importing its code, so Airflow
needs no project dependencies and the API stays the single place where
recovery logic lives.
"""

import os
from datetime import datetime, timedelta

import requests
from airflow.sdk import dag, task

API_URL = os.getenv("SMART_CART_API_URL", "http://api:8000")


@dag(
    dag_id="cart_recovery",
    schedule="*/15 * * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    # Overlapping runs would compete for the same carts.
    max_active_runs=1,
    default_args={
        "retries": 2,
        "retry_delay": timedelta(minutes=2),
    },
    tags=["cart-recovery"],
)
def cart_recovery():

    @task
    def detect_abandoned_carts():
        response = requests.post(
            f"{API_URL}/cart-recovery/detect",
            timeout=300,
        )
        response.raise_for_status()

        results = response.json()
        notified = sum(1 for r in results if r["notification_sent"])

        print(f"Processed {len(results)} abandoned carts, {notified} notified")

        return {
            "processed": len(results),
            "notified": notified,
        }

    detect_abandoned_carts()


cart_recovery()
