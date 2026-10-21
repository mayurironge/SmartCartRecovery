"""SmartCart Recovery dashboard: how well abandoned-cart reminders work.

In Docker it runs at http://localhost:8501. To run it locally:
    streamlit run dashboard/dashboard.py
"""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st
from sqlalchemy import text

# Streamlit puts only this folder on the import path; add the project root.
sys.path.append(str(Path(__file__).resolve().parents[1]))

from backend.config.settings import CURRENCY_SYMBOL, DISPLAY_TIMEZONE  # noqa: E402
from backend.constants import order_status, recovery_status  # noqa: E402
from backend.database import engine  # noqa: E402

# Colours from the validated reference palette (light mode).
BLUE = "#2a78d6"
ORANGE = "#eb6834"
FUNNEL_RAMP = ["#86b6ef", "#3987e5", "#1c5cab"]
TEXT_SECONDARY = "#52514e"
TEXT_MUTED = "#898781"
GRIDLINE = "#e1e0d9"
AXIS_LINE = "#c3c2b7"

PERIODS = {
    "Last 7 days": 7,
    "Last 30 days": 30,
    "Last 60 days": 60,
    "All time": None,
}

# Every query is scoped to recoveries detected since :start.
PARAMS = {
    "recovered": recovery_status.RECOVERED,
    "cancelled": order_status.CANCELLED,
    "tz": DISPLAY_TIMEZONE,
}


@st.cache_data(ttl=60)
def run_query(sql, start):
    with engine.connect() as connection:
        return pd.read_sql(text(sql), connection, params={**PARAMS, "start": start})


def load_summary(start):
    return run_query(
        """
        WITH r AS (
            SELECT * FROM cart_recovery WHERE detected_at >= :start
        )
        SELECT
            count(*) AS abandoned,
            count(*) FILTER (WHERE notified_at IS NOT NULL) AS reminded,
            count(*) FILTER (WHERE recovery_status = :recovered) AS recovered,
            coalesce((
                SELECT sum(o.total_amount)
                FROM orders o
                JOIN r ON r.cart_id = o.cart_id
                WHERE r.recovery_status = :recovered
                  AND o.status <> :cancelled
            ), 0) AS revenue
        FROM r
        """,
        start,
    ).iloc[0]


def load_daily(start):
    return run_query(
        """
        SELECT
            (detected_at AT TIME ZONE :tz)::date AS day,
            count(*) AS abandoned,
            count(*) FILTER (WHERE recovery_status = :recovered) AS recovered
        FROM cart_recovery
        WHERE detected_at >= :start
        GROUP BY 1
        ORDER BY 1
        """,
        start,
    )


def load_top_products(start):
    return run_query(
        """
        SELECT
            p.product_name AS product,
            count(DISTINCT r.recovery_id) AS carts,
            sum(ci.quantity * p.price) AS value_left
        FROM cart_recovery r
        JOIN cart_items ci ON ci.cart_id = r.cart_id
        JOIN products p ON p.product_id = ci.product_id
        WHERE r.detected_at >= :start
        GROUP BY p.product_name
        ORDER BY carts DESC, value_left DESC
        LIMIT 10
        """,
        start,
    )


def load_statuses(start):
    return run_query(
        """
        SELECT recovery_status AS status, count(*) AS recoveries
        FROM cart_recovery
        WHERE detected_at >= :start
        GROUP BY 1
        ORDER BY 2 DESC
        """,
        start,
    )


def load_recent(start):
    return run_query(
        """
        SELECT
            r.detected_at AT TIME ZONE :tz AS detected,
            c.first_name || ' ' || c.last_name AS customer,
            (
                SELECT sum(ci.quantity * p.price)
                FROM cart_items ci
                JOIN products p ON p.product_id = ci.product_id
                WHERE ci.cart_id = r.cart_id
            ) AS cart_value,
            r.recovery_status AS status,
            n.subject AS email_subject
        FROM cart_recovery r
        JOIN carts ca ON ca.cart_id = r.cart_id
        JOIN customers c ON c.customer_id = ca.customer_id
        LEFT JOIN notifications n ON n.recovery_id = r.recovery_id
        WHERE r.detected_at >= :start
        ORDER BY r.detected_at DESC
        LIMIT 20
        """,
        start,
    )


def money(amount):
    return f"{CURRENCY_SYMBOL}{amount:,.0f}"


def styled(chart, height):
    return (
        chart.properties(height=height, background="transparent")
        .configure_view(stroke=None)
        .configure_axis(
            gridColor=GRIDLINE,
            domainColor=AXIS_LINE,
            tickColor=AXIS_LINE,
            labelColor=TEXT_MUTED,
            titleColor=TEXT_SECONDARY,
            titleFontWeight="normal",
            labelFontSize=12,
            titleFontSize=12,
        )
        .configure_legend(
            labelColor=TEXT_SECONDARY,
            labelFontSize=12,
            orient="top",
            title=None,
        )
    )


def show_chart(chart, table, height):
    st.altair_chart(styled(chart, height), width="stretch", theme=None)

    with st.expander("View data"):
        st.dataframe(table, hide_index=True, width="stretch")


def funnel_chart(summary):
    abandoned = int(summary.abandoned)
    stages = pd.DataFrame({
        "stage": ["Abandoned", "Reminder sent", "Recovered"],
        "carts": [abandoned, int(summary.reminded), int(summary.recovered)],
    })
    stages["share"] = stages.carts / abandoned
    stages["label"] = stages.apply(
        lambda row: f"{row.carts:,}  ({row.share:.0%})", axis=1
    )

    base = alt.Chart(stages).encode(
        y=alt.Y("stage:N", sort=None, title=None),
        # Headroom so the labels beside the longest bar aren't cut off.
        x=alt.X(
            "carts:Q",
            title="Carts",
            scale=alt.Scale(domain=[0, abandoned * 1.3]),
        ),
    )
    bars = base.mark_bar(cornerRadiusEnd=4, size=22).encode(
        color=alt.Color(
            "stage:N",
            sort=None,
            scale=alt.Scale(range=FUNNEL_RAMP),
            legend=None,
        ),
        tooltip=[
            alt.Tooltip("stage:N", title="Stage"),
            alt.Tooltip("carts:Q", title="Carts", format=","),
            alt.Tooltip("share:Q", title="Of abandoned", format=".0%"),
        ],
    )
    labels = base.mark_text(align="left", dx=6, color=TEXT_SECONDARY).encode(
        text="label:N"
    )

    return bars + labels, stages[["stage", "carts", "share"]]


def trend_chart(daily, start):
    first_day = daily.day.min() if start is None else start.date()
    days = pd.date_range(first_day, datetime.now(timezone.utc).date(), freq="D")

    wide = (
        daily.assign(day=pd.to_datetime(daily.day))
        .set_index("day")
        .reindex(days, fill_value=0)
        .rename_axis("day")
        .reset_index()
    )
    long = wide.melt(
        id_vars="day",
        value_vars=["abandoned", "recovered"],
        var_name="series",
        value_name="carts",
    )
    long["series"] = long.series.str.capitalize()

    hover = alt.selection_point(
        fields=["day"],
        nearest=True,
        on="pointerover",
        clear="pointerout",
        empty=False,
    )
    x = alt.X("day:T", title=None, axis=alt.Axis(format="%d %b"))

    lines = alt.Chart(long).mark_line(strokeWidth=2).encode(
        x=x,
        y=alt.Y("carts:Q", title="Carts"),
        color=alt.Color(
            "series:N",
            scale=alt.Scale(
                domain=["Abandoned", "Recovered"],
                range=[BLUE, ORANGE],
            ),
        ),
    )
    points = lines.mark_point(filled=True, size=64).encode(
        opacity=alt.condition(hover, alt.value(1), alt.value(0))
    )
    rule = (
        alt.Chart(wide)
        .mark_rule(color=AXIS_LINE)
        .encode(
            x=x,
            opacity=alt.condition(hover, alt.value(1), alt.value(0)),
            tooltip=[
                alt.Tooltip("day:T", title="Day", format="%d %b %Y"),
                alt.Tooltip("abandoned:Q", title="Abandoned"),
                alt.Tooltip("recovered:Q", title="Recovered"),
            ],
        )
        .add_params(hover)
    )

    return lines + points + rule, wide


def ranked_bar_chart(data, category, value, value_title, tooltip):
    chart = alt.Chart(data).mark_bar(
        cornerRadiusEnd=4,
        size=16,
        color=BLUE,
    ).encode(
        y=alt.Y(f"{category}:N", sort="-x", title=None),
        x=alt.X(f"{value}:Q", title=value_title),
        tooltip=tooltip,
    )

    return chart, data


st.set_page_config(page_title="SmartCart Recovery", layout="wide")

st.title("SmartCart Recovery")
st.caption("How many abandoned carts our reminder emails win back.")

filter_col, refresh_col = st.columns([4, 1], vertical_alignment="bottom")
with filter_col:
    period = st.segmented_control(
        "Period",
        list(PERIODS),
        default="Last 30 days",
    ) or "Last 30 days"
with refresh_col:
    if st.button("Refresh data", width="stretch"):
        st.cache_data.clear()

days = PERIODS[period]
# Whole minutes, so reruns within a minute reuse the cached queries.
now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
start = None if days is None else now - timedelta(days=days)
query_start = start or datetime(1970, 1, 1, tzinfo=timezone.utc)

summary = load_summary(query_start)
# The row mixes counts with a decimal total, so pandas hands back floats.
abandoned = int(summary.abandoned)
reminded = int(summary.reminded)
recovered = int(summary.recovered)

if not abandoned:
    st.info("No abandoned carts in this period yet.")
    st.stop()

rate = recovered / reminded if reminded else 0

tiles = st.columns(5)
tiles[0].metric("Carts abandoned", f"{abandoned:,}", border=True)
tiles[1].metric("Reminders sent", f"{reminded:,}", border=True)
tiles[2].metric("Carts recovered", f"{recovered:,}", border=True)
tiles[3].metric(
    "Recovery rate",
    f"{rate:.1%}",
    help="Recovered carts ÷ reminders sent",
    border=True,
)
tiles[4].metric(
    "Revenue recovered",
    money(float(summary.revenue)),
    help="Orders from recovered carts, excluding cancelled orders",
    border=True,
)

left, right = st.columns(2)

with left:
    st.subheader("Recovery funnel")
    show_chart(*funnel_chart(summary), height=180)

with right:
    st.subheader("Recovery status")
    statuses = load_statuses(query_start)
    statuses["status"] = statuses.status.str.capitalize()
    show_chart(
        *ranked_bar_chart(
            statuses,
            "status",
            "recoveries",
            "Recoveries",
            tooltip=[
                alt.Tooltip("status:N", title="Status"),
                alt.Tooltip("recoveries:Q", title="Recoveries"),
            ],
        ),
        height=180,
    )

st.subheader("Abandoned vs recovered per day")
st.caption("Recovered carts are counted on the day they were abandoned.")
show_chart(*trend_chart(load_daily(query_start), start), height=280)

st.subheader("Most abandoned products")
products = load_top_products(query_start)
products["value_left"] = products.value_left.astype(float)
show_chart(
    *ranked_bar_chart(
        products,
        "product",
        "carts",
        "Abandoned carts containing the product",
        tooltip=[
            alt.Tooltip("product:N", title="Product"),
            alt.Tooltip("carts:Q", title="Abandoned carts"),
            alt.Tooltip(
                "value_left:Q",
                title=f"Value left ({CURRENCY_SYMBOL})",
                format=",.0f",
            ),
        ],
    ),
    height=320,
)

st.subheader("Latest recoveries")
recent = load_recent(query_start)
recent["status"] = recent.status.str.capitalize()
# Emails sent before subjects were stored have none.
recent["email_subject"] = recent.email_subject.fillna("—")
st.dataframe(
    recent,
    hide_index=True,
    width="stretch",
    column_config={
        "detected": st.column_config.DatetimeColumn(
            "Abandoned at",
            format="D MMM YYYY, h:mm a",
        ),
        "customer": "Customer",
        "cart_value": st.column_config.NumberColumn(
            f"Cart value ({CURRENCY_SYMBOL})",
            format="localized",
        ),
        "status": "Status",
        "email_subject": "Email subject",
    },
)
