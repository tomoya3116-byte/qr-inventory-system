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
