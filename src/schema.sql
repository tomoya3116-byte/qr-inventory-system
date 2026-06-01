CREATE TABLE IF NOT EXISTS items (
    item_id TEXT PRIMARY KEY,
    item_name TEXT NOT NULL,
    model_number TEXT,
    maker TEXT,
    location TEXT,
    unit TEXT,
    min_stock INTEGER DEFAULT 0,
    current_stock INTEGER DEFAULT 0,
    qr_code TEXT UNIQUE,
    note TEXT
);

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id TEXT NOT NULL,
    transaction_type TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    stock_after INTEGER NOT NULL,
    operator TEXT,
    transaction_date TEXT DEFAULT CURRENT_TIMESTAMP,
    note TEXT,
    FOREIGN KEY (item_id) REFERENCES items(item_id)
);

CREATE TABLE IF NOT EXISTS audit_logs (
    audit_log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    operation_date TEXT DEFAULT CURRENT_TIMESTAMP,
    operation_type TEXT NOT NULL,
    target_item_id TEXT,
    target_item_name TEXT,
    quantity INTEGER,
    message TEXT
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_operation_date
ON audit_logs (operation_date DESC, audit_log_id DESC);
