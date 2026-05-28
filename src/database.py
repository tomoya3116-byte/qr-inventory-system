"""SQLite database utilities for inventory system."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional

DB_PATH = Path("data/inventory.db")
SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """Create a SQLite connection with row factory enabled."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database(db_path: Path = DB_PATH) -> None:
    """Initialize SQLite database from schema and seed sample data."""
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")

    with get_connection(db_path) as connection:
        connection.executescript(schema_sql)
        _ensure_transactions_columns(connection)
        connection.execute(
            """
            INSERT OR IGNORE INTO items (id, name, description, quantity, location)
            VALUES
                (?, ?, ?, ?, ?),
                (?, ?, ?, ?, ?),
                (?, ?, ?, ?, ?)
            """,
            (
                "ITEM001",
                "Notebook",
                "A5 size notebook",
                50,
                "Shelf-A1",
                "ITEM002",
                "Ballpoint Pen",
                "Blue ink pen",
                120,
                "Shelf-B2",
                "ITEM003",
                "Packing Tape",
                "48mm packing tape",
                35,
                "Shelf-C1",
            ),
        )
        connection.commit()


def _ensure_transactions_columns(connection: sqlite3.Connection) -> None:
    """Ensure transactions table has required columns for stock operations."""
    columns = {
        row["name"]
        for row in connection.execute("PRAGMA table_info(transactions)").fetchall()
    }

    if "operator" not in columns:
        connection.execute(
            "ALTER TABLE transactions ADD COLUMN operator TEXT NOT NULL DEFAULT ''"
        )
    if "stock_after" not in columns:
        connection.execute(
            "ALTER TABLE transactions ADD COLUMN stock_after INTEGER NOT NULL DEFAULT 0"
        )


def find_item_by_id(item_id: str, db_path: Path = DB_PATH) -> Optional[sqlite3.Row]:
    """Find a single item by its ID."""
    with get_connection(db_path) as connection:
        row = connection.execute(
            """
            SELECT id, name, description, quantity, location, updated_at
            FROM items
            WHERE id = ?
            """,
            (item_id,),
        ).fetchone()
    return row


def increase_stock(
    item_id: str,
    quantity: int,
    operator: str = "",
    note: str = "",
    db_path: Path = DB_PATH,
) -> int:
    """Increase item stock and record an IN transaction."""
    if quantity <= 0:
        raise ValueError("入庫数量は1以上を指定してください。")

    with get_connection(db_path) as connection:
        _ensure_transactions_columns(connection)
        item = connection.execute(
            "SELECT id, quantity FROM items WHERE id = ?", (item_id,)
        ).fetchone()
        if item is None:
            raise ValueError(f"品目ID '{item_id}' は存在しません。")

        stock_after = int(item["quantity"]) + quantity
        connection.execute(
            "UPDATE items SET quantity = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (stock_after, item_id),
        )
        connection.execute(
            """
            INSERT INTO transactions
                (item_id, transaction_type, quantity, note, operator, stock_after)
            VALUES
                (?, 'IN', ?, ?, ?, ?)
            """,
            (item_id, quantity, note, operator, stock_after),
        )
        connection.commit()

    return stock_after


def decrease_stock(
    item_id: str,
    quantity: int,
    operator: str = "",
    note: str = "",
    db_path: Path = DB_PATH,
) -> int:
    """Decrease item stock and record an OUT transaction."""
    if quantity <= 0:
        raise ValueError("出庫数量は1以上を指定してください。")

    with get_connection(db_path) as connection:
        _ensure_transactions_columns(connection)
        item = connection.execute(
            "SELECT id, quantity FROM items WHERE id = ?", (item_id,)
        ).fetchone()
        if item is None:
            raise ValueError(f"品目ID '{item_id}' は存在しません。")

        current_stock = int(item["quantity"])
        if quantity > current_stock:
            raise ValueError(
                f"在庫不足です。現在庫: {current_stock}, 出庫要求: {quantity}"
            )

        stock_after = current_stock - quantity
        connection.execute(
            "UPDATE items SET quantity = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (stock_after, item_id),
        )
        connection.execute(
            """
            INSERT INTO transactions
                (item_id, transaction_type, quantity, note, operator, stock_after)
            VALUES
                (?, 'OUT', ?, ?, ?, ?)
            """,
            (item_id, quantity, note, operator, stock_after),
        )
        connection.commit()

    return stock_after


def get_transactions_by_item_id(
    item_id: str, db_path: Path = DB_PATH
) -> list[sqlite3.Row]:
    """Return transactions for an item ordered by newest first."""
    with get_connection(db_path) as connection:
        _ensure_transactions_columns(connection)
        rows = connection.execute(
            """
            SELECT id, item_id, transaction_type, quantity, operator, note, stock_after, created_at
            FROM transactions
            WHERE item_id = ?
            ORDER BY created_at DESC, id DESC
            """,
            (item_id,),
        ).fetchall()
    return rows
