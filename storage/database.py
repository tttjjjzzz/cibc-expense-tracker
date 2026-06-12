import os
import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path
from typing import List

DB_PATH = os.getenv("CIBC_DB_PATH", str(Path.home() / ".cibc-tracker" / "expenses.db"))
SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def get_connection() -> sqlite3.Connection:
    db_path = Path(DB_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(SCHEMA_PATH.read_text())


def get_existing_fitids() -> set:
    with get_connection() as conn:
        rows = conn.execute("SELECT fitid FROM transactions").fetchall()
        return {row["fitid"] for row in rows}


def insert_transactions(transactions) -> int:
    with get_connection() as conn:
        for t in transactions:
            conn.execute(
                """
                INSERT OR IGNORE INTO transactions
                  (fitid, date, merchant_raw, merchant, amount, currency,
                   account_id, category, notes, source_file, imported_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    t.fitid,
                    t.date.isoformat(),
                    t.merchant_raw,
                    t.merchant,
                    float(t.amount),
                    t.currency,
                    t.account_id,
                    t.category,
                    t.notes,
                    t.source_file,
                    t.imported_at.isoformat(),
                ),
            )
    return len(transactions)


def log_import(filename: str, row_count: int) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO import_log (filename, row_count, imported_at) VALUES (?, ?, ?)",
            (filename, row_count, datetime.now(timezone.utc).isoformat()),
        )


def get_monthly_summary(year: int, month: int) -> List[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT category, SUM(amount) AS total, COUNT(*) AS count
            FROM transactions
            WHERE strftime('%Y', date) = ?
              AND strftime('%m', date) = ?
              AND amount < 0
            GROUP BY category
            ORDER BY total ASC
            """,
            (str(year), f"{month:02d}"),
        ).fetchall()
        return [dict(r) for r in rows]


def get_transactions(
    start_date=None,
    end_date=None,
    categories=None,
    min_amount=None,
    max_amount=None,
    search=None,
) -> List[dict]:
    """Return transactions matching all provided filters, newest first."""
    conditions, params = [], []
    if start_date:
        conditions.append("date >= ?")
        params.append(str(start_date))
    if end_date:
        conditions.append("date <= ?")
        params.append(str(end_date))
    if categories:
        placeholders = ",".join("?" * len(categories))
        conditions.append(f"category IN ({placeholders})")
        params.extend(categories)
    if min_amount is not None:
        conditions.append("amount >= ?")
        params.append(float(min_amount))
    if max_amount is not None:
        conditions.append("amount <= ?")
        params.append(float(max_amount))
    if search:
        conditions.append("(merchant LIKE ? OR merchant_raw LIKE ?)")
        params.extend([f"%{search}%", f"%{search}%"])

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    sql = f"SELECT * FROM transactions {where} ORDER BY date DESC, imported_at DESC"
    with get_connection() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


def update_transaction_category(fitid: str, category: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE transactions SET category = ? WHERE fitid = ?",
            (category, fitid),
        )


def get_spending_over_time(months: int = 6) -> List[dict]:
    """Return monthly spend totals for the last N months (debits only)."""
    today = date.today()
    m, y = today.month - months, today.year
    while m <= 0:
        m += 12
        y -= 1
    start = date(y, m, 1)
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT strftime('%Y-%m', date) AS month,
                   SUM(amount) AS total,
                   COUNT(*) AS count
            FROM transactions
            WHERE date >= ? AND amount < 0
            GROUP BY month
            ORDER BY month ASC
            """,
            (start.isoformat(),),
        ).fetchall()
        return [dict(r) for r in rows]


def get_top_merchants(year: int, month: int, limit: int = 10) -> List[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT merchant, SUM(amount) AS total, COUNT(*) AS count
            FROM transactions
            WHERE strftime('%Y', date) = ?
              AND strftime('%m', date) = ?
              AND amount < 0
            GROUP BY merchant
            ORDER BY total ASC
            LIMIT ?
            """,
            (str(year), f"{month:02d}", limit),
        ).fetchall()
        return [dict(r) for r in rows]


def get_all_transaction_categories() -> List[str]:
    """Distinct categories currently present in the transactions table."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT DISTINCT category FROM transactions ORDER BY category"
        ).fetchall()
        return [r["category"] for r in rows]


def get_all_categories_with_budgets() -> List[dict]:
    """All distinct categories from transactions joined with budget limits."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT t.category AS name, c.budget_limit
            FROM (SELECT DISTINCT category FROM transactions) t
            LEFT JOIN categories c ON c.name = t.category
            ORDER BY t.category
            """
        ).fetchall()
        return [dict(r) for r in rows]


def upsert_budget(name: str, budget_limit) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO categories (name, budget_limit) VALUES (?, ?)
            ON CONFLICT(name) DO UPDATE SET budget_limit = excluded.budget_limit
            """,
            (name, float(budget_limit) if budget_limit is not None else None),
        )


def get_budget_vs_actual(year: int, month: int) -> List[dict]:
    """Per-category actual spend vs budget limit for a given month."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT t.category,
                   c.budget_limit,
                   SUM(t.amount) AS actual
            FROM transactions t
            LEFT JOIN categories c ON c.name = t.category
            WHERE strftime('%Y', t.date) = ?
              AND strftime('%m', t.date) = ?
              AND t.amount < 0
            GROUP BY t.category
            ORDER BY actual ASC
            """,
            (str(year), f"{month:02d}"),
        ).fetchall()
        return [dict(r) for r in rows]
