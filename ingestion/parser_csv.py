import hashlib
import logging
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import List

import pandas as pd

from ingestion.normaliser import Transaction

logger = logging.getLogger(__name__)


def parse_csv(filepath: str, account_id: str = "") -> List[Transaction]:
    """Parse a CIBC CSV export and return a list of Transactions."""
    transactions = []
    source_file = Path(filepath).name
    now = datetime.now(timezone.utc)

    try:
        df = pd.read_csv(filepath)
    except Exception as e:
        logger.error(f"Failed to read CSV {filepath}: {e}")
        return []

    df.columns = [c.strip() for c in df.columns]
    required = {"Date", "Description", "Debit", "Credit"}
    if not required.issubset(df.columns):
        logger.error(
            f"CSV {filepath} missing expected columns. Found: {list(df.columns)}"
        )
        return []

    for idx, row in df.iterrows():
        try:
            txn_date = datetime.strptime(str(row["Date"]).strip(), "%m/%d/%Y").date()
            desc = str(row["Description"]).strip()
            debit = float(row["Debit"]) if pd.notna(row["Debit"]) else 0.0
            credit = float(row["Credit"]) if pd.notna(row["Credit"]) else 0.0
            # Debit = money out (negative), credit = money in (positive)
            amount = Decimal(str(credit - debit)).quantize(Decimal("0.01"))
            fitid = hashlib.sha256(
                f"{txn_date}{desc}{amount}".encode()
            ).hexdigest()[:16]
            currency = "USD" if "USD" in desc.upper() else "CAD"

            transactions.append(Transaction(
                fitid=fitid,
                date=txn_date,
                merchant_raw=desc,
                merchant=desc,
                amount=amount,
                currency=currency,
                account_id=account_id,
                category="Uncategorised",
                notes="",
                source_file=source_file,
                imported_at=now,
            ))
        except Exception as e:
            logger.warning(f"Skipping row {idx} in {filepath}: {e}")

    return transactions
