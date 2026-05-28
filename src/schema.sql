CREATE TABLE IF NOT EXISTS items (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    quantity INTEGER NOT NULL DEFAULT 0,
    location TEXT,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id TEXT NOT NULL,
    transaction_type TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    note TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (item_id) REFERENCES items(id)
);
