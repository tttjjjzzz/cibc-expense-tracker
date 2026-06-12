from decimal import Decimal
from pathlib import Path

from ingestion.parser_qfx import parse_qfx

FIXTURE = str(Path(__file__).parent / "fixtures" / "sample.qfx")


def test_parse_qfx_count():
    txns = parse_qfx(FIXTURE)
    assert len(txns) == 10


def test_parse_qfx_first_transaction():
    txns = parse_qfx(FIXTURE)
    t = txns[0]
    assert t.fitid == "2025050300001"
    assert str(t.date) == "2025-05-03"
    assert t.amount == Decimal("-4.75")
    assert t.currency == "CAD"
    assert t.account_id == "1234"


def test_parse_qfx_credit_transaction():
    txns = parse_qfx(FIXTURE)
    credits = [t for t in txns if t.amount > 0]
    assert len(credits) == 1
    assert credits[0].amount == Decimal("2500.00")


def test_parse_qfx_merchant_raw_uses_memo():
    txns = parse_qfx(FIXTURE)
    t = txns[0]
    assert "TIM HORTONS" in t.merchant_raw


def test_parse_qfx_source_file():
    txns = parse_qfx(FIXTURE)
    assert all(t.source_file == "sample.qfx" for t in txns)
