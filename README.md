# CIBC Expense Tracker

A local expense tracking tool that ingests CIBC bank statement exports (`.qfx` / `.csv`),
categorises transactions automatically, stores them in a local SQLite database, and
surfaces them in a web dashboard with charts, filters, and budget tracking.

All data stays on your machine — no external API keys or cloud services required.

---

## Requirements

- Python 3.10+
- pip

---

## Installation

```bash
git clone <repo-url>
cd cibc-expense-tracker
pip install -r requirements.txt
```

Optionally copy `.env.example` to `.env` and customise the database path:

```bash
cp .env.example .env
# edit .env if you want a non-default DB location
```

The SQLite database is created automatically at `~/.cibc-tracker/expenses.db` on first use.

---

## Exporting from CIBC Online Banking

1. Log in to CIBC Online Banking
2. Navigate to your account
3. Choose **Download Transactions**
4. Select either:
   - **Quicken** format → saves as `.qfx`
   - **Spreadsheet** format → saves as `.csv`

---

## CLI Usage

### Import a single file

```bash
python cli.py import ~/Downloads/transactions.qfx
python cli.py import ~/Downloads/transactions.csv
```

For CSV files that don't contain an account number, you can tag them manually:

```bash
python cli.py import ~/Downloads/transactions.csv --account-id 1234
```

### Import all files in a folder

```bash
python cli.py import-dir ~/Downloads/cibc-exports/
```

### Show a monthly spending summary

```bash
# Current month
python cli.py summary

# Specific month
python cli.py summary --year 2025 --month 5
```

Example output:

```
Spending summary for 2025-05:
Category                       Total   Txns
---------------------------------------------
Groceries                     -67.42      1
Gas                           -52.30      1
Shopping                      -38.14      1
Subscriptions                 -24.98      2
Delivery                      -23.87      1
Coffee                        -10.00      2
Transit                        -3.50      1
---------------------------------------------
TOTAL                        -220.21
```

### Launch the dashboard

```bash
python cli.py dashboard
# or directly:
streamlit run dashboard/app.py
```

### Watch a folder for new files (auto-import)

```bash
# Watches ./imports/ by default
python cli.py watch

# Custom folder
python cli.py watch --folder ~/Downloads/cibc-exports/
```

Any `.qfx` or `.csv` file dropped into the watched folder is automatically imported.
Running the same file again is safe — duplicates are skipped.

---

## Dashboard

Open `http://localhost:8501` after launching the dashboard.

| Page | Description |
|---|---|
| **Overview** | Monthly KPIs, spending-by-category bar chart, 6-month trend line, top 10 merchants |
| **Transactions** | Filterable full transaction list with inline category editing and file import |
| **Budgets** | Set per-category monthly budget limits; colored progress bars show spend vs budget |

---

## Supported File Formats

### QFX (Quicken export)

OFX 1.x SGML format exported by CIBC. Parsed with `ofxparse`.
Transaction IDs (`FITID`) come directly from the file, guaranteeing idempotent imports.

### CSV (Spreadsheet export)

CIBC CSV with columns: `Date, Description, Debit, Credit, Balance`.
A deterministic `sha256(date + description + amount)` hash is used as the transaction ID,
so importing the same CSV twice never creates duplicates.

---

## Project Structure

```
cibc-expense-tracker/
├── cli.py                     # CLI entry point
├── watcher.py                 # Folder watcher (auto-import)
├── requirements.txt
├── .env.example
│
├── ingestion/
│   ├── detector.py            # Detects QFX vs CSV by extension / content
│   ├── parser_qfx.py          # Parses CIBC QFX exports
│   ├── parser_csv.py          # Parses CIBC CSV exports
│   └── normaliser.py          # Transaction dataclass
│
├── processing/
│   ├── categoriser.py         # Keyword-based merchant → category mapping
│   ├── deduplicator.py        # Skips transactions already in DB
│   └── enricher.py            # Merchant name cleanup, FX detection
│
├── storage/
│   ├── database.py            # SQLite helpers
│   └── schema.sql             # Table definitions
│
├── dashboard/
│   ├── app.py                 # Streamlit entry point
│   ├── pages/
│   │   ├── overview.py
│   │   ├── transactions.py
│   │   └── budgets.py
│   └── components/
│       ├── charts.py          # Altair chart helpers
│       └── filters.py         # Reusable filter widgets
│
└── tests/
    ├── fixtures/
    │   ├── sample.qfx
    │   └── sample.csv
    ├── test_parser_qfx.py
    ├── test_parser_csv.py
    └── test_categoriser.py
```

---

## Running Tests

```bash
pytest tests/ -v
```

---

## Key Constraints

- **Idempotent imports** — running the same file twice never creates duplicate rows
- **Graceful errors** — a bad row is logged and skipped; the rest of the file still imports
- **No cloud** — everything runs locally; the SQLite DB lives at `~/.cibc-tracker/expenses.db`
- **CAD-first** — defaults to CAD; detects USD by checking for "USD" in the transaction description
