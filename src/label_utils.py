"""HTML label sheet generation utilities for QR code printing."""

from __future__ import annotations

import os
from html import escape
from pathlib import Path
from typing import Any, Iterable, Mapping

from qr_utils import QR_CODE_DIR, generate_item_qr_code

LABEL_DIR = Path("labels")


def _get_item_value(item: Mapping[str, object], key: str) -> Any:
    """Read item data from dict-like mappings such as sqlite3.Row."""
    try:
        return item[key]
    except (KeyError, IndexError):
        return None


def _display_value(item: Mapping[str, object], key: str) -> str:
    """Return an HTML-safe display value for an item field."""
    value = _get_item_value(item, key)
    text = str(value).strip() if value is not None else ""
    return escape(text or "-")


def _ensure_qr_code_image(item: Mapping[str, object]) -> Path:
    """Return the item's QR code image path, generating it when missing."""
    item_id = str(_get_item_value(item, "item_id") or "").strip()
    if not item_id:
        raise ValueError("品目IDが空です。")

    qr_path = QR_CODE_DIR / f"{item_id}.png"
    if not qr_path.exists():
        qr_path = generate_item_qr_code(item)
    return qr_path


def _relative_image_path(image_path: Path, output_path: Path) -> str:
    """Return a browser-friendly relative image path from the HTML file."""
    relative_path = os.path.relpath(image_path, start=output_path.parent)
    return escape(Path(relative_path).as_posix(), quote=True)


def generate_qr_label_sheet(
    items: Iterable[Mapping[str, object]], output_path: str | Path
) -> Path:
    """Generate an A4-friendly printable HTML sheet for QR code labels."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    label_cards: list[str] = []
    for item in items:
        qr_path = _ensure_qr_code_image(item)
        item_id = _display_value(item, "item_id")
        item_name = _display_value(item, "item_name")
        model_number = _display_value(item, "model_number")
        location = _display_value(item, "location")
        image_src = _relative_image_path(qr_path, path)

        label_cards.append(f"""
        <section class="label-card">
          <div class="qr-area">
            <img src="{image_src}" alt="QRコード {item_id}" class="qr-image">
          </div>
          <dl class="item-info">
            <div class="info-row"><dt>品目ID</dt><dd>{item_id}</dd></div>
            <div class="info-row"><dt>品名</dt><dd>{item_name}</dd></div>
            <div class="info-row"><dt>型式</dt><dd>{model_number}</dd></div>
            <div class="info-row"><dt>保管場所</dt><dd>{location}</dd></div>
          </dl>
        </section>""")

    labels_html = "\n".join(label_cards)
    html = f"""<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <title>QRコード印刷用ラベル</title>
  <style>
    @page {{
      size: A4 portrait;
      margin: 10mm;
    }}

    * {{
      box-sizing: border-box;
    }}

    body {{
      margin: 0;
      color: #000;
      background: #fff;
      font-family: "Yu Gothic", "Meiryo", sans-serif;
      font-size: 10.5pt;
      line-height: 1.35;
    }}

    .sheet-title {{
      margin: 0 0 6mm;
      font-size: 16pt;
      font-weight: 700;
      text-align: center;
    }}

    .label-grid {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 4mm;
      align-items: start;
    }}

    .label-card {{
      min-height: 60mm;
      padding: 4mm;
      border: 0.4mm solid #000;
      break-inside: avoid;
      page-break-inside: avoid;
      background: #fff;
    }}

    .qr-area {{
      display: flex;
      justify-content: center;
      margin-bottom: 3mm;
    }}

    .qr-image {{
      width: 32mm;
      height: 32mm;
      object-fit: contain;
    }}

    .item-info {{
      margin: 0;
    }}

    .info-row {{
      display: grid;
      grid-template-columns: 17mm 1fr;
      gap: 2mm;
      margin-bottom: 1.5mm;
    }}

    .info-row dt {{
      font-weight: 700;
      white-space: nowrap;
    }}

    .info-row dd {{
      margin: 0;
      overflow-wrap: anywhere;
    }}

    @media print {{
      body {{
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
      }}

      .sheet-title {{
        margin-bottom: 5mm;
      }}
    }}
  </style>
</head>
<body>
  <h1 class="sheet-title">QRコード印刷用ラベル</h1>
  <main class="label-grid">
{labels_html}
  </main>
</body>
</html>
"""

    path.write_text(html, encoding="utf-8")
    return path
