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
        connection.execute(
            """
            INSERT OR IGNORE INTO items (
                item_id,
                item_name,
                model_number,
                maker,
                location,
                unit,
                min_stock,
                current_stock,
                qr_code,
                note
            )
            VALUES
                (?, ?, ?, ?, ?, ?, ?, ?, ?, ?),
                (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "ITEM-0001",
                "ベアリング",
                "ABC-123",
                "メーカーA",
                "棚A-01",
                "個",
                2,
                10,
                "QR-ITEM-0001",
                "",
                "ITEM-0002",
                "Vベルト",
                "VB-456",
                "メーカーB",
                "棚B-02",
                "本",
                1,
                5,
                "QR-ITEM-0002",
                "",
            ),
        )
        connection.commit()


def find_item_by_id(item_id: str, db_path: Path = DB_PATH) -> Optional[sqlite3.Row]:
    """Find a single item by item_id or qr_code."""
    with get_connection(db_path) as connection:
        row = connection.execute(
            """
            SELECT
                item_id,
                item_name,
                model_number,
                maker,
                location,
                unit,
                min_stock,
                current_stock,
                qr_code,
                note
            FROM items
            WHERE item_id = ? OR qr_code = ?
            """,
            (item_id, item_id),
        ).fetchone()
    return row
