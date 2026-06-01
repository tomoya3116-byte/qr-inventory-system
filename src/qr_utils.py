"""QR code image generation utilities for inventory items."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Iterable, Mapping
from urllib.parse import quote

QR_CODE_DIR = Path("qr_codes")
QR_SCAN_BASE_URL_ENV = "QR_INVENTORY_SCAN_BASE_URL"


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


def build_scan_path(item_id: str) -> str:
    """Return the canonical Web QR scan path for an item."""
    normalized_item_id = item_id.strip()
    if not normalized_item_id:
        raise ValueError("品目IDが空です。")
    return f"/scan/{quote(normalized_item_id, safe='')}"


def build_scan_url(item_id: str, base_url: str = "") -> str:
    """Return the QR payload URL for opening the Web scan screen.

    If base_url is blank, the environment variable QR_INVENTORY_SCAN_BASE_URL is
    used. When neither is set, a same-site path such as /scan/ITEM-0001 is
    returned so existing local QR workflows keep working without configuration.
    """
    scan_path = build_scan_path(item_id)
    normalized_base_url = (base_url or os.getenv(QR_SCAN_BASE_URL_ENV, "")).strip()
    if not normalized_base_url:
        return scan_path
    return f"{normalized_base_url.rstrip('/')}{scan_path}"


def generate_item_qr_code(
    item: Mapping[str, object],
    base_url: str = "",
) -> Path:
    """Generate a Web scan QR code PNG for a single item and return the path."""
    item_id = str(_get_item_value(item, "item_id") or "").strip()
    if not item_id:
        raise ValueError("品目IDが空です。")

    qr_data = build_scan_url(item_id, base_url=base_url)
    output_path = QR_CODE_DIR / f"{item_id}.png"
    return generate_qr_image(qr_data, output_path)


def generate_all_qr_codes(
    items: Iterable[Mapping[str, object]],
    base_url: str = "",
) -> dict[str, object]:
    """Generate Web scan QR code PNG files for all given items."""
    saved_paths: list[Path] = []
    for item in items:
        saved_paths.append(generate_item_qr_code(item, base_url=base_url))

    return {
        "count": len(saved_paths),
        "paths": saved_paths,
    }
