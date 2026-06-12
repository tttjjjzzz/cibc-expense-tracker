from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal


@dataclass
class Transaction:
    fitid: str
    date: date
    merchant_raw: str
    merchant: str
    amount: Decimal
    currency: str
    account_id: str
    category: str
    notes: str
    source_file: str
    imported_at: datetime
