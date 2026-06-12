from datetime import date, datetime, timezone
from decimal import Decimal

from ingestion.normaliser import Transaction
from processing.categoriser import categorise


def make_txn(merchant_raw: str) -> Transaction:
    return Transaction(
        fitid="test001",
        date=date.today(),
        merchant_raw=merchant_raw,
        merchant=merchant_raw,
        amount=Decimal("-10.00"),
        currency="CAD",
        account_id="1234",
        category="Uncategorised",
        notes="",
        source_file="test.csv",
        imported_at=datetime.now(timezone.utc),
    )


def test_tim_hortons():
    assert categorise(make_txn("TIM HORTONS #4821 RICHMOND BC")).category == "Coffee"


def test_starbucks():
    assert categorise(make_txn("STARBUCKS #9234 RICHMOND BC")).category == "Coffee"


def test_uber_eats_not_rideshare():
    assert categorise(make_txn("UBER EATS TORONTO ON")).category == "Delivery"


def test_uber_ride():
    assert categorise(make_txn("UBER TRIP TORONTO ON")).category == "Rideshare"


def test_loblaws():
    assert categorise(make_txn("LOBLAWS #1052 RICHMOND BC")).category == "Groceries"


def test_netflix():
    assert categorise(make_txn("NETFLIX.COM")).category == "Subscriptions"


def test_spotify():
    assert categorise(make_txn("SPOTIFY AB")).category == "Subscriptions"


def test_amazon_ca():
    assert categorise(make_txn("AMAZON.CA AMZN.CA/BILL ON")).category == "Shopping"


def test_petro_canada():
    assert categorise(make_txn("PETRO CANADA 00427 RICHMOND BC")).category == "Gas"


def test_presto():
    assert categorise(make_txn("PRESTO AUTOLOAD TORONTO ON")).category == "Transit"


def test_unknown_merchant():
    assert categorise(make_txn("SOME RANDOM MERCHANT XYZ")).category == "Uncategorised"
