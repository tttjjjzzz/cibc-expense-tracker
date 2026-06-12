from pathlib import Path
from typing import List

from ingestion.normaliser import Transaction


def detect_and_parse(filepath: str, account_id: str = "") -> List[Transaction]:
    """Detect file type by extension (then content) and parse accordingly."""
    path = Path(filepath)
    ext = path.suffix.lower()

    if ext in (".qfx", ".ofx"):
        from ingestion.parser_qfx import parse_qfx
        return parse_qfx(filepath)

    if ext == ".csv":
        from ingestion.parser_csv import parse_csv
        return parse_csv(filepath, account_id=account_id)

    # Fall back to content sniffing
    try:
        with open(filepath, "r", errors="ignore") as f:
            header = f.read(512)
        if "OFXHEADER" in header or "<OFX>" in header:
            from ingestion.parser_qfx import parse_qfx
            return parse_qfx(filepath)
        if "Date" in header and "Description" in header:
            from ingestion.parser_csv import parse_csv
            return parse_csv(filepath, account_id=account_id)
    except Exception:
        pass

    raise ValueError(f"Unsupported file type: {path.suffix!r} for {filepath}")
