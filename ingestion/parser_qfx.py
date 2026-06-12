import logging
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import List

from ofxparse import OfxParser

from ingestion.normaliser import Transaction

logger = logging.getLogger(__name__)


def parse_qfx(filepath: str) -> List[Transaction]:
    """Parse a CIBC QFX/OFX file and return a list of Transactions."""
    transactions = []
    source_file = Path(filepath).name
    now = datetime.now(timezone.utc)

    try:
        with open(filepath, "rb") as f:
            ofx = OfxParser.parse(f)
    except Exception as e:
        logger.error(f"Failed to parse QFX file {filepath}: {e}")
        return []

    account_id = ""
    try:
        account_id = ofx.account.account_id[-4:]
    except Exception:
        pass

    try:
        raw_transactions = ofx.account.statement.transactions
    except Exception as e:
        logger.error(f"Could not read transactions from {filepath}: {e}")
        return []

    for raw in raw_transactions:
        try:
            fitid = str(raw.id)
            txn_date = raw.date.date() if isinstance(raw.date, datetime) else raw.date
            # Prefer MEMO (more detailed) over NAME; fall back to NAME
            merchant_raw = str(raw.memo or raw.name or "").strip()
            amount = Decimal(str(raw.amount))
            currency = "USD" if "USD" in merchant_raw.upper() else "CAD"

            transactions.append(Transaction(
                fitid=fitid,
                date=txn_date,
                merchant_raw=merchant_raw,
                merchant=merchant_raw,
                amount=amount,
                currency=currency,
                account_id=account_id,
                category="Uncategorised",
                notes="",
                source_file=source_file,
                imported_at=now,
            ))
        except Exception as e:
            logger.warning(f"Skipping transaction in {filepath}: {e}")

    return transactions
