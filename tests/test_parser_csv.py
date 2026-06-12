from decimal import Decimal
from pathlib import Path

from ingestion.parser_csv import parse_csv

FIXTURE = str(Path(__file__).parent / "fixtures" / "sample.csv")


def test_parse_csv_count():
    txns = parse_csv(FIXTURE)
    assert len(txns) == 10


def test_parse_csv_debit_is_negative():
    txns = parse_csv(FIXTURE)
    t = next(t for t in txns if "TIM HORTONS" in t.merchant_raw)
    assert t.amount == Decimal("-4.75")


def test_parse_csv_credit_is_positive():
    txns = parse_csv(FIXTURE)
    credits = [t for t in txns if t.amount > 0]
    assert len(credits) == 1
    assert credits[0].amount == Decimal("2500.00")


def test_parse_csv_fitid_hex():
    txns = parse_csv(FIXTURE)
    assert all(len(t.fitid) == 16 for t in txns)
    assert all(all(c in "0123456789abcdef" for c in t.fitid) for t in txns)


def test_parse_csv_fitid_deterministic():
    txns1 = parse_csv(FIXTURE)
    txns2 = parse_csv(FIXTURE)
    assert [t.fitid for t in txns1] == [t.fitid for t in txns2]


def test_parse_csv_source_file():
    txns = parse_csv(FIXTURE)
    assert all(t.source_file == "sample.csv" for t in txns)
