from typing import List

from ingestion.normaliser import Transaction

RULES = {
    # Food & drink
    "TIM HORTONS":    "Coffee",
    "STARBUCKS":      "Coffee",
    "MCDONALDS":      "Fast food",
    "SUBWAY":         "Fast food",
    "UBER EATS":      "Delivery",
    "DOORDASH":       "Delivery",
    "LOBLAWS":        "Groceries",
    "METRO":          "Groceries",
    "SOBEYS":         "Groceries",
    "COSTCO":         "Groceries",
    "NO FRILLS":      "Groceries",
    # Transport
    "PETRO CANADA":   "Gas",
    "SHELL":          "Gas",
    "ESSO":           "Gas",
    "IMPARK":         "Parking",
    "GREEN P":        "Parking",
    "PRESTO":         "Transit",
    "UBER":           "Rideshare",
    "LYFT":           "Rideshare",
    # Subscriptions
    "NETFLIX":        "Subscriptions",
    "SPOTIFY":        "Subscriptions",
    "APPLE.COM/BILL": "Subscriptions",
    "GOOGLE":         "Subscriptions",
    "AMAZON PRIME":   "Subscriptions",
    "DISNEY PLUS":    "Subscriptions",
    # Shopping
    "AMAZON.CA":      "Shopping",
    "AMAZON":         "Shopping",
    "WALMART":        "Shopping",
    "BEST BUY":       "Shopping",
    # Health
    "SHOPPERS":       "Pharmacy",
    "REXALL":         "Pharmacy",
    # Utilities & bills
    "ROGERS":         "Phone/Internet",
    "BELL":           "Phone/Internet",
    "TELUS":          "Phone/Internet",
    "HYDRO":          "Utilities",
    "ENBRIDGE":       "Utilities",
    # Finance
    "CIBC":           "Bank fees",
    "INTEREST":       "Bank fees",
}

# Longer (more specific) keywords take priority
_SORTED_RULES = sorted(RULES.items(), key=lambda kv: len(kv[0]), reverse=True)


def categorise(transaction: Transaction) -> Transaction:
    """Assign category based on the first matching keyword in merchant_raw."""
    upper = transaction.merchant_raw.upper()
    for keyword, category in _SORTED_RULES:
        if keyword in upper:
            transaction.category = category
            return transaction
    transaction.category = "Uncategorised"
    return transaction


def categorise_all(transactions: List[Transaction]) -> List[Transaction]:
    return [categorise(t) for t in transactions]
