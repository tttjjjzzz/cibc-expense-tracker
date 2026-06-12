import sys
from pathlib import Path

# Ensure project root is on sys.path regardless of where streamlit is invoked from
_root = Path(__file__).parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

import streamlit as st
from storage import database

st.set_page_config(
    page_title="CIBC Expense Tracker",
    page_icon="$",
    layout="wide",
)

database.init_db()

with st.sidebar:
    st.markdown("## CIBC Expense Tracker")
    st.divider()
    page = st.radio(
        "Navigate",
        ["Overview", "Transactions", "Budgets"],
        label_visibility="collapsed",
    )
    st.divider()
    st.caption("Data stored locally in ~/.cibc-tracker/expenses.db")

if page == "Overview":
    from dashboard._pages.overview import render
    render()
elif page == "Transactions":
    from dashboard._pages.transactions import render
    render()
elif page == "Budgets":
    from dashboard._pages.budgets import render
    render()
