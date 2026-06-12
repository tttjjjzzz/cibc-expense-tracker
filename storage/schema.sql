CREATE TABLE IF NOT EXISTS transactions (
    fitid       TEXT PRIMARY KEY,
    date        TEXT NOT NULL,
    merchant_raw TEXT NOT NULL,
    merchant    TEXT NOT NULL,
    amount      REAL NOT NULL,
    currency    TEXT NOT NULL DEFAULT 'CAD',
    account_id  TEXT NOT NULL DEFAULT '',
    category    TEXT NOT NULL DEFAULT 'Uncategorised',
    notes       TEXT NOT NULL DEFAULT '',
    source_file TEXT NOT NULL,
    imported_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS categories (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT NOT NULL UNIQUE,
    budget_limit REAL
);

CREATE TABLE IF NOT EXISTS category_rules (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword  TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS import_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    filename    TEXT NOT NULL,
    row_count   INTEGER NOT NULL,
    imported_at TEXT NOT NULL
);
