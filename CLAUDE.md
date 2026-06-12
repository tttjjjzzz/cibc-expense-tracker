# CIBC Expense Tracker — Claude Code Project Spec

## Project goal

Build a personal expense tracking system that ingests CIBC bank statement exports
(`.qfx` and `.csv`), processes and categorises transactions, stores them in a local
SQLite database, and surfaces them in a web dashboard with charts, filters, and
budget tracking.

---

## Repository structure to create

```
cibc-expense-tracker/
├── CLAUDE.md                  ← this file
├── README.md
├── requirements.txt
├── .env.example
│
├── ingestion/
│   ├── __init__.py
│   ├── detector.py            ← detects file type (qfx vs csv)
│   ├── parser_qfx.py          ← parses CIBC Quicken .qfx exports
│   ├── parser_csv.py          ← parses CIBC Spreadsheet .csv exports
│   └── normaliser.py          ← maps parsed rows → common Transaction schema
│
├── processing/
│   ├── __init__.py
│   ├── deduplicator.py        ← skips transactions already in DB (by fitid or hash)
│   ├── categoriser.py         ← rules-based merchant → category mapping
│   └── enricher.py            ← FX detection, merchant name cleanup
│
├── storage/
│   ├── __init__.py
│   ├── database.py            ← SQLite connection, migrations, query helpers
│   └── schema.sql             ← CREATE TABLE statements
│
├── dashboard/
│   ├── app.py                 ← Streamlit entry point
│   ├── pages/
│   │   ├── overview.py        ← monthly summary + category breakdown
│   │   ├── transactions.py    ← filterable transaction list
│   │   └── budgets.py         ← budget vs actual per category
│   └── components/
│       ├── charts.py          ← reusable Altair/Plotly chart helpers
│       └── filters.py         ← date range, category, amount filter widgets
│
├── cli.py                     ← CLI entry point: `python cli.py import <file>`
├── watcher.py                 ← folder watcher: auto-imports new files dropped in /imports
│
└── tests/
    ├── fixtures/
    │   ├── sample.qfx         ← minimal valid QFX fixture
    │   └── sample.csv         ← minimal valid CIBC CSV fixture
    ├── test_parser_qfx.py
    ├── test_parser_csv.py
    └── test_categoriser.py
```

---

## Data model

### Transaction (normalised schema — all parsers output this)

```python
@dataclass
class Transaction:
    fitid: str           # unique ID — from <FITID> in QFX, or hash for CSV
    date: date           # transaction date
    merchant_raw: str    # original description from bank
    merchant: str        # cleaned display name
    amount: Decimal      # negative = debit (spending), positive = credit (income)
    currency: str        # "CAD" default, "USD" if detected
    account_id: str      # last 4 digits of card/account
    category: str        # assigned by categoriser, editable
    notes: str           # user-editable notes field
    source_file: str     # filename it was imported from
    imported_at: datetime
```

### SQLite tables (see storage/schema.sql)

- `transactions` — one row per transaction (unique on `fitid`)
- `categories` — user-defined category list with budget limits
- `category_rules` — keyword → category mapping used by categoriser
- `import_log` — record of every file imported (filename, row count, timestamp)

---

## CIBC file format notes

### QFX (Quicken export)

- OFX 1.x format — SGML-like, NOT valid XML
- Key tags: `<STMTTRN>`, `<TRNTYPE>`, `<DTPOSTED>`, `<TRNAMT>`, `<FITID>`, `<NAME>`, `<MEMO>`
- Date format: `YYYYMMDD` (e.g. `20250312`)
- Amounts: negative = debit (money out), positive = credit (money in)
- Use `ofxparse` library for parsing — do NOT attempt to parse as XML

### CSV (Spreadsheet export)

- CIBC CSV columns (order may vary, detect by header):
  `Date, Description, Debit, Credit, Balance`
- Date format: `MM/DD/YYYY`
- Debit column = money spent (positive number, represents outflow)
- Credit column = money received (positive number, represents inflow)
- Normalise to signed amount: debit → negative, credit → positive
- No built-in transaction ID — generate `fitid` as `sha256(date+description+amount)[:16]`

---

## Categorisation rules (starter set — expand in category_rules table)

```python
RULES = {
    # Food & drink
    "TIM HORTONS":      "Coffee",
    "STARBUCKS":        "Coffee",
    "MCDONALDS":        "Fast food",
    "SUBWAY":           "Fast food",
    "UBER EATS":        "Delivery",
    "DOORDASH":         "Delivery",
    "LOBLAWS":          "Groceries",
    "METRO":            "Groceries",
    "SOBEYS":           "Groceries",
    "COSTCO":           "Groceries",
    "NO FRILLS":        "Groceries",

    # Transport
    "PETRO CANADA":     "Gas",
    "SHELL":            "Gas",
    "ESSO":             "Gas",
    "IMPARK":           "Parking",
    "GREEN P":          "Parking",
    "PRESTO":           "Transit",
    "UBER":             "Rideshare",
    "LYFT":             "Rideshare",

    # Subscriptions
    "NETFLIX":          "Subscriptions",
    "SPOTIFY":          "Subscriptions",
    "APPLE.COM/BILL":   "Subscriptions",
    "GOOGLE":           "Subscriptions",
    "AMAZON PRIME":     "Subscriptions",
    "DISNEY PLUS":      "Subscriptions",

    # Shopping
    "AMAZON":           "Shopping",
    "AMAZON.CA":        "Shopping",
    "WALMART":          "Shopping",
    "BEST BUY":         "Shopping",

    # Health
    "SHOPPERS":         "Pharmacy",
    "REXALL":           "Pharmacy",

    # Utilities & bills
    "ROGERS":           "Phone/Internet",
    "BELL":             "Phone/Internet",
    "TELUS":            "Phone/Internet",
    "HYDRO":            "Utilities",
    "ENBRIDGE":         "Utilities",

    # Finance
    "CIBC":             "Bank fees",
    "INTEREST":         "Bank fees",
}
```

Match by checking if the rule key appears anywhere in `merchant_raw.upper()`.
Unknown merchants → category `"Uncategorised"`.

---

## Dashboard pages

### 1. Overview (default page)
- Month selector (default: current month)
- Total spent this month (big number)
- Spending by category — horizontal bar chart
- Spending over time — line chart (last 6 months)
- Top 10 merchants this month — table

### 2. Transactions
- Full transaction list, newest first
- Filters: date range, category (multi-select), amount range, search by merchant
- Inline category edit (dropdown) — saves back to DB immediately
- Import button — triggers file picker → runs ingestion pipeline

### 3. Budgets
- Per-category monthly budget limits (editable inline)
- Budget vs actual — progress bars (green < 80%, amber 80–100%, red > 100%)
- Month selector

---

## CLI usage

```bash
# Import a single file
python cli.py import ~/Downloads/transactions.qfx
python cli.py import ~/Downloads/transactions.csv

# Import all files in a folder
python cli.py import-dir ~/Downloads/cibc-exports/

# Show summary for current month
python cli.py summary

# Launch dashboard
python cli.py dashboard

# Start folder watcher (auto-imports files dropped into ./imports/)
python cli.py watch
```

---

## Tech stack

| Layer        | Library              | Notes                                      |
|--------------|----------------------|--------------------------------------------|
| QFX parsing  | `ofxparse`           | Handles OFX 1.x SGML format                |
| CSV parsing  | `pandas`             | Column detection + type coercion           |
| Storage      | `sqlite3` (stdlib)   | No ORM — raw SQL via helper functions      |
| Dashboard    | `streamlit`          | Run with `streamlit run dashboard/app.py`  |
| Charts       | `altair`             | Declarative, works well with Streamlit     |
| CLI          | `click`              | Subcommand routing                         |
| File watcher | `watchdog`           | Monitors ./imports/ folder                 |
| Testing      | `pytest`             |                                            |

---

## requirements.txt to generate

```
ofxparse>=0.21
pandas>=2.0
streamlit>=1.35
altair>=5.0
click>=8.1
watchdog>=4.0
pytest>=8.0
python-dotenv>=1.0
```

---

## Build order for Claude Code

Work through these phases in order. Complete and test each before moving on.

### Phase 1 — Ingestion + storage (no UI)
1. Create `storage/schema.sql` and `storage/database.py`
2. Create `ingestion/parser_qfx.py` — parse QFX, return list of `Transaction`
3. Create `ingestion/parser_csv.py` — parse CIBC CSV, return list of `Transaction`
4. Create `ingestion/detector.py` — sniff file extension + header to pick parser
5. Create `ingestion/normaliser.py` — dataclass + field mapping
6. Create `processing/deduplicator.py` — check fitid against DB before insert
7. Create `processing/categoriser.py` — keyword rules → category
8. Create `cli.py` with `import` subcommand
9. Write tests using fixtures in `tests/fixtures/`
10. Verify: `python cli.py import tests/fixtures/sample.qfx` inserts rows, re-running skips dupes

### Phase 2 — Dashboard
11. Create `dashboard/app.py` with sidebar navigation
12. Build `pages/overview.py` — monthly totals + charts
13. Build `pages/transactions.py` — filterable list + inline category edit
14. Build `pages/budgets.py` — budget limits + progress bars
15. Verify: `streamlit run dashboard/app.py` loads with real data

### Phase 3 — Automation
16. Create `watcher.py` — watches `./imports/` folder, auto-runs ingestion on new files
17. Add `watch` subcommand to `cli.py`
18. Add `README.md` with setup + usage instructions

---

## Key constraints

- **No external API keys required** for core functionality
- **All data stays local** — SQLite file at `~/.cibc-tracker/expenses.db` by default
- **Idempotent imports** — running the same file twice must never create duplicate rows
- **Graceful errors** — if a row fails to parse, log a warning and continue; never crash the whole import
- **CAD-first** — assume CAD; detect USD transactions by checking `<CURRENCY>` tag in QFX or "USD" in CSV description
