import altair as alt
import pandas as pd


def category_bar_chart(data: list) -> alt.Chart:
    """Horizontal bar chart: spending by category (debits only, amounts shown as positive)."""
    df = pd.DataFrame(data)
    if df.empty:
        return None
    df["spend"] = df["total"].abs()
    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("spend:Q", title="Amount (CAD)", axis=alt.Axis(format="$,.2f")),
            y=alt.Y("category:N", sort="-x", title=None),
            color=alt.Color("category:N", legend=None),
            tooltip=[
                alt.Tooltip("category:N", title="Category"),
                alt.Tooltip("spend:Q", title="Amount", format="$,.2f"),
                alt.Tooltip("count:Q", title="Transactions"),
            ],
        )
        .properties(height=max(180, len(df) * 32))
    )
    return chart


def spending_over_time_chart(data: list) -> alt.Chart:
    """Line chart: total monthly spend over time."""
    df = pd.DataFrame(data)
    if df.empty:
        return None
    df["spend"] = df["total"].abs()
    df["month_dt"] = pd.to_datetime(df["month"] + "-01")
    chart = (
        alt.Chart(df)
        .mark_line(point=True, strokeWidth=2)
        .encode(
            x=alt.X("month_dt:T", title="Month", axis=alt.Axis(format="%b %Y")),
            y=alt.Y("spend:Q", title="Total Spend (CAD)", axis=alt.Axis(format="$,.2f")),
            tooltip=[
                alt.Tooltip("month_dt:T", title="Month", format="%B %Y"),
                alt.Tooltip("spend:Q", title="Amount", format="$,.2f"),
                alt.Tooltip("count:Q", title="Transactions"),
            ],
        )
        .properties(height=300)
    )
    return chart
