import re
from typing import List

from ingestion.normaliser import Transaction

# Trailing "CITY PROVINCE" pattern, e.g. "RICHMOND BC", "TORONTO ON"
_LOCATION_RE = re.compile(
    r'\s+\S+\s+(?:AB|BC|MB|NB|NL|NS|NT|NU|ON|PE|QC|SK|YT)\s*$',
    re.IGNORECASE,
)


def clean_merchant(raw: str) -> str:
    """Strip store numbers and trailing city/province from a merchant name."""
    name = re.sub(r'\s*#\d+', '', raw)        # remove #1234
    name = _LOCATION_RE.sub('', name)          # remove trailing location
    name = ' '.join(name.split()).strip()
    return name or raw


def enrich(transaction: Transaction) -> Transaction:
    """Clean the merchant display name and confirm currency."""
    transaction.merchant = clean_merchant(transaction.merchant_raw)
    if "USD" in transaction.merchant_raw.upper():
        transaction.currency = "USD"
    return transaction


def enrich_all(transactions: List[Transaction]) -> List[Transaction]:
    return [enrich(t) for t in transactions]
