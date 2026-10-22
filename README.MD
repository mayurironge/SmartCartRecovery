# SmartCart Recovery

An end-to-end data engineering and GenAI system that finds abandoned shopping
carts, emails customers a personalised, AI-written reminder, and measures how
many sales those reminders win back.

**Python · FastAPI · PostgreSQL · SQLAlchemy · Kafka · Airflow · Gemini · Streamlit · Docker**

![SmartCart Recovery dashboard](docs/dashboard.png)

## What it does

1. **Tracks carts.** A FastAPI backend manages customers, products, carts and
   orders, and records every cart action as an event.
2. **Detects abandonment.** A cart with items and no activity for 30 minutes
   counts as abandoned. Kafka streaming catches it within seconds of the
   threshold; a scheduled Airflow sweep catches anything streaming missed.
3. **Writes the reminder.** Google Gemini writes a short email naming the
   customer and the products they left. If the AI is unavailable, a template
   email is sent instead, so reminders never stop.
4. **Measures results.** Each abandonment moves through
   `PENDING → NOTIFIED → RECOVERED` (or `EXPIRED`), and a Streamlit dashboard
   shows the recovery rate and revenue recovered.

## Architecture

```
Customer ──▶ FastAPI ──saves──▶ PostgreSQL ◀──reads (read-only)── Streamlit dashboard
               │  ▲
     publishes │  │ "recover cart 42"          "recover any abandoned carts" (every 15 min)
  cart events  ▼  │                                   ▲
            Kafka topic ──▶ Abandonment consumer       Airflow DAG (safety net)
            "cart-events"   (timer per cart)

  On recovery: Gemini writes the email (template fallback) ──▶ Gmail SMTP
```

| Component | Role |
|---|---|
| **FastAPI** (`backend/`) | REST API; layered as routes → services → repositories → models |
| **PostgreSQL** | Source of truth for carts, orders, events, recoveries and notifications |
| **Kafka** (`streaming/`) | Cart events are published after each commit; a consumer keeps a timer per cart and triggers recovery when it runs out |
| **Airflow** (`airflow/`) | 15-minute batch sweep, a safety net for anything streaming missed |
| **Gemini** (`genai/`) | Writes each reminder as structured JSON (subject + body), with guardrails and a template fallback |
| **Streamlit** (`dashboard/`) | KPIs, recovery funnel, daily trend and most-abandoned products, read through a read-only database role |
| **Docker Compose** (`docker/`) | Runs all six services with one command |

## Engineering decisions

- **Never email a customer twice.** One open recovery per cart (partial
  unique index), one notification per recovery, and the recovery row is
  locked with `SELECT … FOR UPDATE SKIP LOCKED` while sending, so concurrent
  runs skip it instead of sending a duplicate.
- **Atomic changes.** Repositories only flush; each service commits once, so
  a cart change and its event are saved together or not at all.
- **Streaming for speed, batch for completeness.** Kafka reacts as events
  happen; Airflow's sweep covers events lost while Kafka or the consumer was
  down.
- **Dual writes handled deliberately.** Events are published only *after*
  the database commit, so a rolled-back change is never announced. A crash
  between commit and publish is covered by the Airflow sweep; the full fix
  would be the transactional outbox pattern.
- **The API decides; schedulers only ask.** Airflow and the Kafka consumer
  just say "check this cart". The API re-checks every condition, so a late or
  duplicate trigger can't send a wrong email.
- **AI that can fail safely.** The email is generated once and stored, so
  retries don't call the model again. Any AI failure (timeout, quota,
  retired model, malformed output) falls back to a template.
- **Least privilege.** The dashboard uses a read-only database role and gets
  no email or AI secrets; the consumer gets no database access at all.
- **Retries with a limit.** A failed email is retried on the next runs and
  marked `EXPIRED` after 3 attempts.

## Run it locally

Requires [Docker Desktop](https://www.docker.com/products/docker-desktop/).

1. Create a `.env` file in the project root:

   ```
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=you@gmail.com
   SMTP_PASSWORD=your-gmail-app-password
   GEMINI_API_KEY=your-gemini-key        # optional; without it a template email is used
   ```

   Emails are sent with a [Gmail app password](https://myaccount.google.com/apppasswords);
   a free Gemini key comes from [Google AI Studio](https://aistudio.google.com/apikey).

2. Start everything:

   ```
   cd docker
   docker compose up -d --build
   ```

| Service | Address |
|---|---|
| API docs (Swagger) | http://localhost:8000/docs |
| Dashboard | http://localhost:8501 |
| Airflow | http://localhost:8080 |
| Kafka | `localhost:9094` |
| PostgreSQL | `localhost:5433` (user/password `postgres`) |

**Demo data.** Load about 60 days of realistic shop history for the
dashboard. Demo customers use the reserved `shop.example` domain and are
never emailed:

```
docker compose exec api python -m backend.scripts.seed_demo_data
```

Add `--reset` to delete **all** existing data first.

**Quick demo.** A cart counts as abandoned after 30 minutes. To see a
reminder within minutes, start with a shorter threshold:

```
RECOVERY_THRESHOLD_MINUTES=2 docker compose up -d       # bash
$env:RECOVERY_THRESHOLD_MINUTES=2; docker compose up -d # PowerShell
```

**Watch events stream in:**

```
docker compose exec kafka /opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic cart-events
```

Stop with `docker compose down`. Data is kept in a Docker volume;
`docker compose down -v` deletes it, and the database is recreated from
`database/schema.sql` on the next start. Existing databases are upgraded with
the scripts in `database/migrations/`.

## API

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/customers` | Create a customer |
| `POST` | `/products` | Create a product |
| `POST` | `/carts` | Create a cart (or return the customer's active one) |
| `GET` | `/carts/{cart_id}` | View a cart with totals |
| `POST` | `/carts/{cart_id}/items` | Add a product |
| `PUT` | `/carts/{cart_id}/items/{product_id}` | Set a quantity |
| `DELETE` | `/carts/{cart_id}/items/{product_id}` | Remove one unit |
| `DELETE` | `/carts/{cart_id}/items` | Empty the cart |
| `POST` | `/orders/checkout/{cart_id}` | Check out |
| `GET` | `/orders`, `/orders/{order_id}`, `/orders/customer/{customer_id}` | View orders |
| `GET` | `/orders/history` | Filter orders by customer, status and dates |
| `PUT` | `/orders/{order_id}/status` | Move an order along its lifecycle |
| `PUT` | `/orders/{order_id}/cancel` | Cancel and restore stock |
| `POST` | `/cart-recovery/detect` | Recover abandoned carts (all, or one with `?cart_id=`) |

## Project structure

```
backend/      FastAPI app: api, services, repositories, models, schemas
streaming/    Kafka producer (session hooks) and abandonment consumer
genai/        Gemini email generator and prompt templates
airflow/      cart_recovery DAG
dashboard/    Streamlit dashboard
database/     schema.sql and migrations
docker/       Dockerfile, docker-compose.yml, Postgres init script
docs/         Screenshots
```
