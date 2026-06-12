from typing import List

from ingestion.normaliser import Transaction
from storage import database


def deduplicate(transactions: List[Transaction]) -> List[Transaction]:
    """Return only transactions whose fitid is not already in the database."""
    existing = database.get_existing_fitids()
    return [t for t in transactions if t.fitid not in existing]
