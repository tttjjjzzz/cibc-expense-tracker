from datetime import date, timedelta

import streamlit as st


def date_range_filter(key_prefix: str = "") -> tuple:
    """Render start/end date pickers. Returns (start_date, end_date)."""
    col1, col2 = st.columns(2)
    default_start = date.today().replace(day=1)
    default_end = date.today()
    start = col1.date_input("From", value=default_start, key=f"{key_prefix}_start")
    end = col2.date_input("To", value=default_end, key=f"{key_prefix}_end")
    return start, end


def category_filter(all_categories: list, key: str = "cat_filter") -> list:
    """Multi-select for categories. Returns list of selected categories (empty = all)."""
    return st.multiselect("Categories", options=all_categories, default=[], key=key)


def amount_range_filter(key_prefix: str = "") -> tuple:
    """Min/max amount sliders. Returns (min_amount, max_amount) as floats or None."""
    col1, col2 = st.columns(2)
    min_val = col1.number_input(
        "Min amount", value=None, step=1.0,
        placeholder="No min", key=f"{key_prefix}_min"
    )
    max_val = col2.number_input(
        "Max amount", value=None, step=1.0,
        placeholder="No max", key=f"{key_prefix}_max"
    )
    return min_val, max_val


def merchant_search_filter(key: str = "merchant_search") -> str:
    """Text input for merchant search. Returns search string or empty string."""
    return st.text_input("Search merchant", value="", key=key)
