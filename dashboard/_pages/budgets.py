from datetime import date

import pandas as pd
import streamlit as st

from storage import database


def _progress_bar(label: str, actual_abs: float, budget) -> None:
    """Render a colored HTML progress bar for one category."""
    if budget is None or budget <= 0:
        st.markdown(
            f"**{label}** — ${actual_abs:,.2f} spent *(no budget set)*"
        )
        return

    pct = actual_abs / budget
    fill = min(pct, 1.0) * 100
    color = "#28a745" if pct < 0.8 else ("#ffc107" if pct <= 1.0 else "#dc3545")
    over = " — OVER BUDGET" if pct > 1.0 else ""
    status = f"${actual_abs:,.2f} / ${budget:,.2f} ({pct * 100:.0f}%{over})"

    st.markdown(
        f"""
        <div style="margin-bottom:14px">
            <div style="display:flex;justify-content:space-between;margin-bottom:2px">
                <span style="font-weight:600">{label}</span>
                <span style="font-size:0.85em;color:#555">{status}</span>
            </div>
            <div style="background:#e9ecef;border-radius:4px;height:18px;overflow:hidden">
                <div style="width:{fill:.1f}%;background:{color};height:100%;
                            border-radius:4px;transition:width 0.3s"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render():
    st.title("Budgets")

    # Month selector
    today = date.today()
    col_y, col_m, _ = st.columns([1, 1, 4])
    year = int(col_y.number_input("Year", min_value=2000, max_value=today.year + 1,
                                   value=today.year, step=1, key="bud_year"))
    month = int(col_m.number_input("Month", min_value=1, max_value=12,
                                    value=today.month, step=1, key="bud_month"))

    st.divider()

    cats_with_budgets = database.get_all_categories_with_budgets()
    if not cats_with_budgets:
        st.info("No transactions imported yet. Import some transactions first.")
        return

    # --- Editable budget table ---
    st.subheader("Set Monthly Budgets")
    bdf = pd.DataFrame(cats_with_budgets)  # columns: name, budget_limit
    bdf = bdf.rename(columns={"name": "Category", "budget_limit": "Budget (CAD)"})

    edited = st.data_editor(
        bdf,
        column_config={
            "Category": st.column_config.TextColumn("Category", disabled=True),
            "Budget (CAD)": st.column_config.NumberColumn(
                "Budget (CAD)",
                min_value=0.0,
                step=10.0,
                format="$%.2f",
            ),
        },
        hide_index=True,
        use_container_width=True,
        key="budget_editor",
    )

    changed = edited["Budget (CAD)"] != bdf["Budget (CAD)"]
    if changed.any():
        for idx in bdf[changed].index:
            database.upsert_budget(
                edited.loc[idx, "Category"],
                edited.loc[idx, "Budget (CAD)"],
            )
        st.rerun()

    st.divider()

    # --- Budget vs actual progress bars ---
    st.subheader(f"Budget vs Actual — {year}-{month:02d}")
    actuals = database.get_budget_vs_actual(year, month)

    if not actuals:
        st.info(f"No spending recorded for {year}-{month:02d}.")
        return

    # Build a budget lookup from the (possibly just-edited) data
    budget_map = {
        row["name"]: row["budget_limit"] for row in cats_with_budgets
    }

    for row in actuals:
        cat = row["category"]
        actual_abs = abs(row["actual"])
        budget = budget_map.get(cat)
        _progress_bar(cat, actual_abs, budget)
