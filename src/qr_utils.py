"""QR code image generation utilities for inventory items."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Mapping

QR_CODE_DIR = Path("qr_codes")


def generate_qr_image(data: str, output_path: str | Path) -> Path:
    """Generate a QR code PNG from data and save it to output_path."""
    if not data:
        raise ValueError("QRコード化するデータが空です。")

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    import qrcode

    image = qrcode.make(data)
    image.save(path)
    return path


def _get_item_value(item: Mapping[str, object], key: str) -> Any:
    """Read item data from dict-like mappings such as sqlite3.Row."""
    try:
        return item[key]
    except (KeyError, IndexError):
        return None


def generate_item_qr_code(item: Mapping[str, object]) -> Path:
    """Generate a QR code PNG for a single item and return the saved path."""
    item_id = str(_get_item_value(item, "item_id") or "").strip()
    if not item_id:
        raise ValueError("品目IDが空です。")

    qr_code = str(_get_item_value(item, "qr_code") or "").strip()
    qr_data = qr_code or item_id
    output_path = QR_CODE_DIR / f"{item_id}.png"
    return generate_qr_image(qr_data, output_path)


def generate_all_qr_codes(items: Iterable[Mapping[str, object]]) -> dict[str, object]:
    """Generate QR code PNG files for all given items."""
    saved_paths: list[Path] = []
    for item in items:
        saved_paths.append(generate_item_qr_code(item))

    return {
        "count": len(saved_paths),
        "paths": saved_paths,
    }
