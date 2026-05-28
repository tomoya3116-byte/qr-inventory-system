"""SQLite database utilities for inventory system."""

from __future__ import annotations

import csv
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

DB_PATH = Path("data/inventory.db")
BACKUP_DIR = Path("backups")
SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def backup_database(db_path: Path = DB_PATH, backup_dir: Path = BACKUP_DIR) -> Path:
    """Copy the SQLite database file to the backups directory."""
    if not db_path.exists():
        raise FileNotFoundError(f"バックアップ対象のDBファイルが見つかりません: {db_path}")

    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"inventory_{timestamp}.db"
    shutil.copy2(db_path, backup_path)
    return backup_path


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
                "ITEM-0001",
                "",
                "ITEM-0002",
                "Vベルト",
                "VB-456",
                "メーカーB",
                "棚B-02",
                "本",
                1,
                5,
                "ITEM-0002",
                "",
            ),
        )
        connection.commit()


def create_item(
    item_id: str,
    item_name: str,
    model_number: str = "",
    maker: str = "",
    location: str = "",
    unit: str = "",
    min_stock: int = 0,
    initial_stock: int = 0,
    note: str = "",
    db_path: Path = DB_PATH,
) -> None:
    """Create a new item. item_id and qr_code are registered with the same value."""
    if not item_id:
        raise ValueError("品目IDは必須です。")
    if not item_name:
        raise ValueError("品名は必須です。")
    if min_stock < 0:
        raise ValueError("最低在庫数は0以上を指定してください。")
    if initial_stock < 0:
        raise ValueError("初期在庫数は0以上を指定してください。")

    with get_connection(db_path) as connection:
        exists = connection.execute(
            "SELECT 1 FROM items WHERE item_id = ? OR qr_code = ?",
            (item_id, item_id),
        ).fetchone()
        if exists is not None:
            raise ValueError(f"品目ID '{item_id}' は既に存在します。")

        connection.execute(
            """
            INSERT INTO items (
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
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item_id,
                item_name,
                model_number,
                maker,
                location,
                unit,
                min_stock,
                initial_stock,
                item_id,
                note,
            ),
        )
        connection.commit()


def update_item(
    item_id: str,
    item_name: str,
    model_number: str,
    maker: str,
    location: str,
    unit: str,
    min_stock: int,
    note: str,
    db_path: Path = DB_PATH,
) -> None:
    """Update an existing item master fields."""
    if min_stock < 0:
        raise ValueError("最低在庫数は0以上を指定してください。")

    with get_connection(db_path) as connection:
        current = connection.execute(
            "SELECT item_id FROM items WHERE item_id = ?",
            (item_id,),
        ).fetchone()
        if current is None:
            raise ValueError(f"品目ID '{item_id}' は存在しません。")

        connection.execute(
            """
            UPDATE items
            SET
                item_name = ?,
                model_number = ?,
                maker = ?,
                location = ?,
                unit = ?,
                min_stock = ?,
                note = ?
            WHERE item_id = ?
            """,
            (item_name, model_number, maker, location, unit, min_stock, note, item_id),
        )
        connection.commit()


def delete_item(item_id: str, db_path: Path = DB_PATH) -> None:
    """Delete an item only when it has no transaction history."""
    with get_connection(db_path) as connection:
        current = connection.execute(
            "SELECT item_id FROM items WHERE item_id = ?",
            (item_id,),
        ).fetchone()
        if current is None:
            raise ValueError(f"品目ID '{item_id}' は存在しません。")

        history = connection.execute(
            "SELECT 1 FROM transactions WHERE item_id = ? LIMIT 1",
            (item_id,),
        ).fetchone()
        if history is not None:
            raise ValueError("入出庫履歴があるため削除できません。")

        connection.execute("DELETE FROM items WHERE item_id = ?", (item_id,))
        connection.commit()


def list_items(db_path: Path = DB_PATH) -> list[sqlite3.Row]:
    """Return all items ordered by item_id."""
    with get_connection(db_path) as connection:
        rows = connection.execute(
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
            ORDER BY item_id ASC
            """
        ).fetchall()
    return rows


CSV_ENCODINGS = ("utf-8-sig", "utf-8", "cp932", "shift_jis")
CSV_ENCODING_ERROR_MESSAGE = (
    "CSVの文字コードを読み取れませんでした。UTF-8またはShift-JISで保存してください。"
)


def import_items_from_csv(csv_path: str, db_path: Path = DB_PATH) -> dict[str, object]:
    """Import item master from CSV with upsert behavior."""
    path = Path(csv_path)
    if not path.exists():
        raise ValueError(f"CSVファイルが見つかりません: {csv_path}")

    last_decode_error: UnicodeDecodeError | None = None
    for encoding in CSV_ENCODINGS:
        try:
            return _import_items_from_csv_with_encoding(path, encoding, db_path)
        except UnicodeDecodeError as error:
            last_decode_error = error

    raise ValueError(CSV_ENCODING_ERROR_MESSAGE) from last_decode_error


def _import_items_from_csv_with_encoding(
    path: Path,
    encoding: str,
    db_path: Path,
) -> dict[str, object]:
    registered_count = 0
    updated_count = 0
    errors: list[str] = []

    with (
        path.open("r", encoding=encoding, newline="") as csv_file,
        get_connection(db_path) as connection,
    ):
        reader = csv.DictReader(csv_file)
        required_columns = {
            "item_id",
            "item_name",
            "model_number",
            "maker",
            "location",
            "unit",
            "min_stock",
            "current_stock",
            "qr_code",
            "note",
        }
        if reader.fieldnames is None:
            raise ValueError("CSVヘッダーが見つかりません。")

        missing_columns = required_columns - set(reader.fieldnames)
        if missing_columns:
            missing = ", ".join(sorted(missing_columns))
            raise ValueError(f"CSVヘッダーに不足があります: {missing}")

        for row_index, row in enumerate(reader, start=2):
            item_id = (row.get("item_id") or "").strip()
            item_name = (row.get("item_name") or "").strip()

            if not item_id:
                errors.append(f"{row_index}行目: item_id が空です")
                continue
            if not item_name:
                errors.append(f"{row_index}行目: item_name が空です")
                continue

            try:
                min_stock = int((row.get("min_stock") or "0").strip())
            except ValueError:
                errors.append(f"{row_index}行目: min_stock が整数ではありません")
                continue

            try:
                current_stock = int((row.get("current_stock") or "0").strip())
            except ValueError:
                errors.append(f"{row_index}行目: current_stock が整数ではありません")
                continue

            model_number = (row.get("model_number") or "").strip()
            maker = (row.get("maker") or "").strip()
            location = (row.get("location") or "").strip()
            unit = (row.get("unit") or "").strip()
            qr_code = (row.get("qr_code") or "").strip() or item_id
            note = (row.get("note") or "").strip()

            exists = connection.execute(
                "SELECT 1 FROM items WHERE item_id = ?",
                (item_id,),
            ).fetchone()

            if exists is None:
                connection.execute(
                    """
                    INSERT INTO items (
                        item_id, item_name, model_number, maker, location,
                        unit, min_stock, current_stock, qr_code, note
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        item_id,
                        item_name,
                        model_number,
                        maker,
                        location,
                        unit,
                        min_stock,
                        current_stock,
                        qr_code,
                        note,
                    ),
                )
                registered_count += 1
            else:
                connection.execute(
                    """
                    UPDATE items
                    SET
                        item_name = ?,
                        model_number = ?,
                        maker = ?,
                        location = ?,
                        unit = ?,
                        min_stock = ?,
                        current_stock = ?,
                        qr_code = ?,
                        note = ?
                    WHERE item_id = ?
                    """,
                    (
                        item_name,
                        model_number,
                        maker,
                        location,
                        unit,
                        min_stock,
                        current_stock,
                        qr_code,
                        note,
                        item_id,
                    ),
                )
                updated_count += 1

        connection.commit()

    return {
        "registered_count": registered_count,
        "updated_count": updated_count,
        "error_count": len(errors),
        "errors": errors,
        "encoding": encoding,
    }



def list_low_stock_items(db_path: Path = DB_PATH) -> list[sqlite3.Row]:
    """Return items where current stock is less than or equal to minimum stock."""
    with get_connection(db_path) as connection:
        rows = connection.execute(
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
                CASE
                    WHEN current_stock < min_stock THEN min_stock - current_stock
                    ELSE 0
                END AS shortage_quantity
            FROM items
            WHERE current_stock <= min_stock
            ORDER BY shortage_quantity DESC, item_id ASC
            """
        ).fetchall()
    return rows
def find_item_by_id(item_id: str, db_path: Path = DB_PATH) -> Optional[sqlite3.Row]:
    """Find a single item by its item_id or qr_code."""
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
        item = connection.execute(
            "SELECT item_id, current_stock FROM items WHERE item_id = ? OR qr_code = ?",
            (item_id, item_id),
        ).fetchone()
        if item is None:
            raise ValueError(f"品目ID '{item_id}' は存在しません。")

        stock_after = int(item["current_stock"]) + quantity
        connection.execute(
            "UPDATE items SET current_stock = ? WHERE item_id = ?",
            (stock_after, item["item_id"]),
        )
        connection.execute(
            """
            INSERT INTO transactions
                (item_id, transaction_type, quantity, stock_after, operator, note)
            VALUES
                (?, 'IN', ?, ?, ?, ?)
            """,
            (item["item_id"], quantity, stock_after, operator, note),
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
        item = connection.execute(
            "SELECT item_id, current_stock FROM items WHERE item_id = ? OR qr_code = ?",
            (item_id, item_id),
        ).fetchone()
        if item is None:
            raise ValueError(f"品目ID '{item_id}' は存在しません。")

        current_stock = int(item["current_stock"])
        if quantity > current_stock:
            raise ValueError(
                f"在庫不足です。現在庫: {current_stock}, 出庫要求: {quantity}"
            )

        stock_after = current_stock - quantity
        connection.execute(
            "UPDATE items SET current_stock = ? WHERE item_id = ?",
            (stock_after, item["item_id"]),
        )
        connection.execute(
            """
            INSERT INTO transactions
                (item_id, transaction_type, quantity, stock_after, operator, note)
            VALUES
                (?, 'OUT', ?, ?, ?, ?)
            """,
            (item["item_id"], quantity, stock_after, operator, note),
        )
        connection.commit()

    return stock_after


def adjust_stock(
    item_id: str,
    actual_stock: int,
    operator: str = "",
    note: str = "",
    db_path: Path = DB_PATH,
) -> int:
    """Set item stock to the actual counted quantity and record an ADJUST transaction."""
    if actual_stock < 0:
        raise ValueError("実在庫数は0以上を指定してください。")

    with get_connection(db_path) as connection:
        item = connection.execute(
            "SELECT item_id, current_stock FROM items WHERE item_id = ? OR qr_code = ?",
            (item_id, item_id),
        ).fetchone()
        if item is None:
            raise ValueError(f"品目ID '{item_id}' は存在しません。")

        current_stock = int(item["current_stock"])
        difference = actual_stock - current_stock
        connection.execute(
            "UPDATE items SET current_stock = ? WHERE item_id = ?",
            (actual_stock, item["item_id"]),
        )
        connection.execute(
            """
            INSERT INTO transactions
                (item_id, transaction_type, quantity, stock_after, operator, note)
            VALUES
                (?, 'ADJUST', ?, ?, ?, ?)
            """,
            (item["item_id"], difference, actual_stock, operator, note),
        )
        connection.commit()

    return actual_stock


def get_transactions_by_item_id(
    item_id: str, db_path: Path = DB_PATH
) -> list[sqlite3.Row]:
    """Return transactions for an item ordered by newest first."""
    with get_connection(db_path) as connection:
        rows = connection.execute(
            """
            SELECT
                transaction_id,
                item_id,
                transaction_type,
                quantity,
                stock_after,
                operator,
                transaction_date,
                note
            FROM transactions
            WHERE item_id = ?
            ORDER BY transaction_date DESC, transaction_id DESC
            """,
            (item_id,),
        ).fetchall()
    return rows
