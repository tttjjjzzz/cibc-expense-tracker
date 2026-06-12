from datetime import date

import pandas as pd
import streamlit as st

from storage import database
from storage.database import get_connection
from dashboard.components.charts import category_bar_chart, spending_over_time_chart


def _get_income(year: int, month: int) -> float:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT COALESCE(SUM(amount), 0) AS total
            FROM transactions
            WHERE strftime('%Y', date) = ? AND strftime('%m', date) = ? AND amount > 0
            """,
            (str(year), f"{month:02d}"),
        ).fetchone()
    return float(row["total"]) if row else 0.0


def render():
    st.title("Overview")

    # Month / year selector — defaults to the most recent month with data
    default_year, default_month = database.get_latest_transaction_month()
    today = date.today()
    col_y, col_m, _ = st.columns([1, 1, 4])
    year = col_y.number_input("Year", min_value=2000, max_value=today.year + 1,
                               value=default_year, step=1, key="ov_year")
    month = col_m.number_input("Month", min_value=1, max_value=12,
                                value=default_month, step=1, key="ov_month")
    year, month = int(year), int(month)

    st.divider()

    # KPI metrics
    summary = database.get_monthly_summary(year, month)
    total_spent = sum(r["total"] for r in summary)   # sum of negatives
    total_income = _get_income(year, month)

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Spent", f"${abs(total_spent):,.2f}")
    c2.metric("Total Income", f"${total_income:,.2f}")
    c3.metric("Net", f"${total_income + total_spent:+,.2f}")

    st.divider()

    # Spending by category — bar chart
    st.subheader("Spending by Category")
    if summary:
        chart = category_bar_chart(summary)
        if chart:
            st.altair_chart(chart, use_container_width=True)
    else:
        st.info(f"No spending data for {year}-{month:02d}.")

    # Spending over time — line chart
    st.subheader("Spending Over Time (last 6 months)")
    over_time = database.get_spending_over_time(months=6)
    chart2 = spending_over_time_chart(over_time)
    if chart2:
        st.altair_chart(chart2, use_container_width=True)
    else:
        st.info("Not enough historical data yet.")

    # Top 10 merchants
    st.subheader(f"Top 10 Merchants — {year}-{month:02d}")
    top = database.get_top_merchants(year, month, limit=10)
    if top:
        df = pd.DataFrame(top)
        df["total"] = df["total"].abs()
        df = df.rename(columns={"merchant": "Merchant",
                                 "total": "Amount (CAD)",
                                 "count": "Transactions"})
        df["Amount (CAD)"] = df["Amount (CAD)"].map("${:,.2f}".format)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No merchant data for this period.")
