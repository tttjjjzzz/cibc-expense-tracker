import os
import sys
import tempfile
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

from storage import database
from dashboard.components.filters import (
    date_range_filter,
    category_filter,
    merchant_search_filter,
)


def _run_pipeline(filepath: str, original_name: str, account_id: str = "") -> tuple:
    """Run ingestion pipeline; rename temp file so source_file is correct."""
    # Rename temp file to original name so source_file tracking works
    target = Path(filepath).parent / original_name
    os.rename(filepath, str(target))
    try:
        from cli import run_pipeline
        return run_pipeline(str(target), account_id=account_id)
    finally:
        if target.exists():
            target.unlink()


def render():
    st.title("Transactions")

    # Import section
    with st.expander("Import transactions"):
        uploaded = st.file_uploader(
            "Upload a QFX or CSV file",
            type=["qfx", "ofx", "csv"],
            key="txn_uploader",
        )
        acct_id = st.text_input("Account ID (last 4 digits, for CSV)", value="",
                                  key="txn_acct_id")
        if uploaded and st.button("Import", key="do_import"):
            suffix = Path(uploaded.name).suffix
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uploaded.read())
                tmp_path = tmp.name
            try:
                inserted, skipped = _run_pipeline(tmp_path, uploaded.name, acct_id)
                st.success(f"Imported {inserted} new transaction(s), skipped {skipped} duplicate(s).")
                st.rerun()
            except Exception as e:
                st.error(f"Import failed: {e}")
                if Path(tmp_path).exists():
                    os.unlink(tmp_path)

    st.divider()

    # Filters
    with st.expander("Filters", expanded=True):
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            start, end = date_range_filter(key_prefix="txn")
            search = merchant_search_filter(key="txn_search")
        with col_f2:
            all_cats = database.get_all_transaction_categories()
            selected_cats = category_filter(all_cats, key="txn_cats")

    # Load transactions
    rows = database.get_transactions(
        start_date=start,
        end_date=end,
        categories=selected_cats or None,
        search=search or None,
    )

    if not rows:
        st.info("No transactions match the current filters.")
        return

    df = pd.DataFrame(rows)

    # Columns to display (hide raw fields, keep fitid for keying)
    display_cols = ["date", "merchant", "amount", "currency", "category",
                    "account_id", "source_file"]
    show_df = df[["fitid"] + display_cols].copy()
    show_df = show_df.rename(columns={
        "date": "Date", "merchant": "Merchant", "amount": "Amount",
        "currency": "Currency", "category": "Category",
        "account_id": "Account", "source_file": "Source",
    })

    st.caption(f"{len(df)} transaction(s) shown")

    # Editable table — only Category column is editable
    edited = st.data_editor(
        show_df,
        column_config={
            "fitid": None,   # hide
            "Category": st.column_config.SelectboxColumn(
                "Category",
                options=all_cats,
                required=True,
            ),
            "Amount": st.column_config.NumberColumn(
                "Amount", format="$%.2f"
            ),
        },
        disabled=["Date", "Merchant", "Amount", "Currency", "Account", "Source"],
        hide_index=True,
        use_container_width=True,
        key="txn_editor",
    )

    # Detect and persist category edits
    changed_mask = edited["Category"] != show_df["Category"]
    if changed_mask.any():
        for idx in show_df[changed_mask].index:
            fitid = show_df.loc[idx, "fitid"]
            new_cat = edited.loc[idx, "Category"]
            database.update_transaction_category(fitid, new_cat)
        st.rerun()
