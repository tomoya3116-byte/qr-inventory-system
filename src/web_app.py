"""FastAPI web application for QR inventory system Ver2.0 Phase 1."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Form, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src import database

ROOT_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = ROOT_DIR / "templates"
STATIC_DIR = ROOT_DIR / "static"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Initialize the SQLite database before serving requests."""
    database.initialize_database()
    yield


app = FastAPI(
    title="QR Inventory System Web",
    description="スマートフォン・PCブラウザ向け在庫管理Webアプリ",
    version="2.0.0-phase1",
    lifespan=lifespan,
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)


NAV_ITEMS = [
    {"label": "トップ", "url": "/"},
    {"label": "品目一覧", "url": "/items"},
    {"label": "品目検索", "url": "/search"},
    {"label": "入庫", "url": "/stock-in"},
    {"label": "出庫", "url": "/stock-out"},
    {"label": "最低在庫", "url": "/low-stock"},
]


def _context(request: Request, **extra: Any) -> dict[str, Any]:
    """Build common template context."""
    return {"request": request, "nav_items": NAV_ITEMS, **extra}


def _parse_quantity(quantity_text: str, label: str) -> int:
    """Parse positive integer quantity from a form value."""
    try:
        quantity = int(quantity_text)
    except ValueError as error:
        raise ValueError(f"{label}は整数で入力してください。") from error
    if quantity <= 0:
        raise ValueError(f"{label}は1以上を指定してください。")
    return quantity


def _normalize_item_id(item_id: str) -> str:
    """Trim the item id or QR code form value."""
    normalized = item_id.strip()
    if not normalized:
        raise ValueError("品目IDまたはQRコードを入力してください。")
    return normalized


@app.get("/")
async def index(request: Request):
    """Show the Web app top page."""
    items = database.list_items()
    low_stock_items = database.list_low_stock_items()
    return templates.TemplateResponse(
        "index.html",
        _context(
            request,
            item_count=len(items),
            low_stock_count=len(low_stock_items),
        ),
    )


@app.get("/items")
async def items(request: Request):
    """Show all registered items."""
    return templates.TemplateResponse(
        "items.html",
        _context(request, items=database.list_items()),
    )


@app.get("/search")
async def search(request: Request, q: str = ""):
    """Search an item by item id or QR code."""
    keyword = q.strip()
    item = database.find_item_by_id(keyword) if keyword else None
    message = "品目が見つかりません" if keyword and item is None else ""
    return templates.TemplateResponse(
        "search.html",
        _context(request, keyword=keyword, item=item, message=message),
    )


@app.get("/stock-in")
async def stock_in_form(request: Request):
    """Show stock-in form."""
    return templates.TemplateResponse("stock_in.html", _context(request))


@app.post("/stock-in")
async def stock_in_submit(
    request: Request,
    item_id: str = Form(...),
    quantity: str = Form(...),
    operator: str = Form(""),
    note: str = Form(""),
):
    """Increase stock from the web form."""
    message = ""
    message_type = "success"
    item = None
    stock_after = None
    normalized_item_id = item_id.strip()

    try:
        normalized_item_id = _normalize_item_id(item_id)
        parsed_quantity = _parse_quantity(quantity, "入庫数量")
        item = database.find_item_by_id(normalized_item_id)
        if item is None:
            raise LookupError("品目が見つかりません")
        stock_after = database.increase_stock(
            normalized_item_id,
            parsed_quantity,
            operator.strip(),
            note.strip(),
        )
        item = database.find_item_by_id(normalized_item_id)
        message = f"入庫しました。現在庫は {stock_after} です。"
    except (LookupError, ValueError) as error:
        message = str(error)
        message_type = "error"

    return templates.TemplateResponse(
        "stock_in.html",
        _context(
            request,
            message=message,
            message_type=message_type,
            item=item,
            stock_after=stock_after,
            form={
                "item_id": normalized_item_id,
                "quantity": quantity,
                "operator": operator.strip(),
                "note": note.strip(),
            },
        ),
    )


@app.get("/stock-out")
async def stock_out_form(request: Request):
    """Show stock-out form."""
    return templates.TemplateResponse("stock_out.html", _context(request))


@app.post("/stock-out")
async def stock_out_submit(
    request: Request,
    item_id: str = Form(...),
    quantity: str = Form(...),
    operator: str = Form(""),
    note: str = Form(""),
):
    """Decrease stock from the web form."""
    message = ""
    message_type = "success"
    item = None
    stock_after = None
    normalized_item_id = item_id.strip()

    try:
        normalized_item_id = _normalize_item_id(item_id)
        parsed_quantity = _parse_quantity(quantity, "出庫数量")
        item = database.find_item_by_id(normalized_item_id)
        if item is None:
            raise LookupError("品目が見つかりません")
        stock_after = database.decrease_stock(
            normalized_item_id,
            parsed_quantity,
            operator.strip(),
            note.strip(),
        )
        item = database.find_item_by_id(normalized_item_id)
        message = f"出庫しました。現在庫は {stock_after} です。"
    except (LookupError, ValueError) as error:
        message = str(error)
        message_type = "error"

    return templates.TemplateResponse(
        "stock_out.html",
        _context(
            request,
            message=message,
            message_type=message_type,
            item=item,
            stock_after=stock_after,
            form={
                "item_id": normalized_item_id,
                "quantity": quantity,
                "operator": operator.strip(),
                "note": note.strip(),
            },
        ),
    )


@app.get("/low-stock")
async def low_stock(request: Request):
    """Show low stock alert list."""
    low_stock_items = database.list_low_stock_items()
    message = "最低在庫を下回っている品目はありません。" if not low_stock_items else ""
    return templates.TemplateResponse(
        "low_stock.html",
        _context(request, items=low_stock_items, message=message),
    )

