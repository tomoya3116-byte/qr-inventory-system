"""FastAPI web application for QR inventory system Ver2.0 Phase 2."""

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
    version="2.0.0-phase2",
    lifespan=lifespan,
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)


NAV_ITEMS = [
    {"label": "トップ", "url": "/"},
    {"label": "品目一覧", "url": "/items"},
    {"label": "品目登録", "url": "/items/new"},
    {"label": "品目検索", "url": "/search"},
    {"label": "入庫", "url": "/stock-in"},
    {"label": "出庫", "url": "/stock-out"},
    {"label": "棚卸修正", "url": "/stock-adjust"},
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


def _parse_non_negative_int(value_text: str, label: str) -> int:
    """Parse a non-negative integer from a form value."""
    try:
        value = int(value_text)
    except ValueError as error:
        raise ValueError(f"{label}は整数で入力してください。") from error
    if value < 0:
        raise ValueError(f"{label}は0以上を指定してください。")
    return value


def _normalize_item_id(item_id: str) -> str:
    """Trim the item id or QR code form value."""
    normalized = item_id.strip()
    if not normalized:
        raise ValueError("品目IDまたはQRコードを入力してください。")
    return normalized


def _normalize_required_text(value: str, label: str) -> str:
    """Trim a required text form value."""
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{label}を入力してください。")
    return normalized


@app.get("/")
async def index(request: Request):
    """Show the Web app top page."""
    items = database.list_items()
    low_stock_items = database.list_low_stock_items()
    return templates.TemplateResponse(
        request,
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
        request,
        "items.html",
        _context(request, items=database.list_items()),
    )


@app.get("/items/new")
async def item_new_form(request: Request):
    """Show the item registration form."""
    return templates.TemplateResponse(
        request,
        "item_new.html",
        _context(request),
    )


@app.post("/items/new")
async def item_new_submit(
    request: Request,
    item_id: str = Form(...),
    item_name: str = Form(...),
    model_number: str = Form(""),
    maker: str = Form(""),
    location: str = Form(""),
    unit: str = Form(""),
    min_stock: str = Form(...),
    initial_stock: str = Form(...),
    note: str = Form(""),
):
    """Create an item from the web form using database.py utilities."""
    form = {
        "item_id": item_id.strip(),
        "item_name": item_name.strip(),
        "model_number": model_number.strip(),
        "maker": maker.strip(),
        "location": location.strip(),
        "unit": unit.strip(),
        "min_stock": min_stock.strip(),
        "initial_stock": initial_stock.strip(),
        "note": note.strip(),
    }
    message = ""
    message_type = "success"
    item = None

    try:
        parsed_item_id = _normalize_required_text(item_id, "品目ID")
        parsed_item_name = _normalize_required_text(item_name, "品名")
        parsed_min_stock = _parse_non_negative_int(min_stock, "最低在庫数")
        parsed_initial_stock = _parse_non_negative_int(initial_stock, "初期在庫数")
        database.create_item(
            item_id=parsed_item_id,
            item_name=parsed_item_name,
            model_number=model_number.strip(),
            maker=maker.strip(),
            location=location.strip(),
            unit=unit.strip(),
            min_stock=parsed_min_stock,
            initial_stock=parsed_initial_stock,
            note=note.strip(),
        )
        item = database.find_item_by_id(parsed_item_id)
        message = f"品目ID '{parsed_item_id}' を登録しました。"
        form = {
            "item_id": "",
            "item_name": "",
            "model_number": "",
            "maker": "",
            "location": "",
            "unit": "",
            "min_stock": "0",
            "initial_stock": "0",
            "note": "",
        }
    except ValueError as error:
        message = str(error)
        message_type = "error"

    return templates.TemplateResponse(
        request,
        "item_new.html",
        _context(
            request,
            message=message,
            message_type=message_type,
            form=form,
            item=item,
        ),
    )


@app.get("/items/{item_id}/edit")
async def item_edit_form(request: Request, item_id: str):
    """Show the item edit form."""
    item = database.find_item_by_id(item_id)
    message = "品目が見つかりません" if item is None else ""
    return templates.TemplateResponse(
        request,
        "item_edit.html",
        _context(request, item=item, message=message, message_type="error"),
    )


@app.post("/items/{item_id}/edit")
async def item_edit_submit(
    request: Request,
    item_id: str,
    item_name: str = Form(...),
    model_number: str = Form(""),
    maker: str = Form(""),
    location: str = Form(""),
    unit: str = Form(""),
    min_stock: str = Form(...),
    note: str = Form(""),
):
    """Update item master fields from the web form using database.py utilities."""
    message = ""
    message_type = "success"
    item = database.find_item_by_id(item_id)

    try:
        if item is None:
            raise LookupError("品目が見つかりません")
        parsed_item_name = _normalize_required_text(item_name, "品名")
        parsed_min_stock = _parse_non_negative_int(min_stock, "最低在庫数")
        database.update_item(
            item_id=item["item_id"],
            item_name=parsed_item_name,
            model_number=model_number.strip(),
            maker=maker.strip(),
            location=location.strip(),
            unit=unit.strip(),
            min_stock=parsed_min_stock,
            note=note.strip(),
        )
        item = database.find_item_by_id(item["item_id"])
        message = "品目情報を更新しました。"
    except (LookupError, ValueError) as error:
        message = str(error)
        message_type = "error"
        if item is not None:
            item = {
                "item_id": item["item_id"],
                "item_name": item_name.strip(),
                "model_number": model_number.strip(),
                "maker": maker.strip(),
                "location": location.strip(),
                "unit": unit.strip(),
                "min_stock": min_stock.strip(),
                "current_stock": item["current_stock"],
                "qr_code": item["qr_code"],
                "note": note.strip(),
            }

    return templates.TemplateResponse(
        request,
        "item_edit.html",
        _context(request, item=item, message=message, message_type=message_type),
    )


@app.get("/items/{item_id}/delete")
async def item_delete_form(request: Request, item_id: str):
    """Show the item delete confirmation form."""
    item = database.find_item_by_id(item_id)
    message = "品目が見つかりません" if item is None else ""
    return templates.TemplateResponse(
        request,
        "item_delete.html",
        _context(request, item=item, message=message, message_type="error"),
    )


@app.post("/items/{item_id}/delete")
async def item_delete_submit(
    request: Request,
    item_id: str,
    confirm_item_id: str = Form(...),
):
    """Delete an item after confirmation using database.py utilities."""
    message = ""
    message_type = "success"
    item = database.find_item_by_id(item_id)

    try:
        if item is None:
            raise LookupError("品目が見つかりません")
        if confirm_item_id.strip() != item["item_id"]:
            raise ValueError("確認入力が一致しないため、削除を中止しました。")
        deleted_item_id = item["item_id"]
        database.delete_item(deleted_item_id)
        item = None
        message = f"品目ID '{deleted_item_id}' を削除しました。"
    except (LookupError, ValueError) as error:
        message = str(error)
        message_type = "error"

    return templates.TemplateResponse(
        request,
        "item_delete.html",
        _context(request, item=item, message=message, message_type=message_type),
    )


@app.get("/search")
async def search(request: Request, q: str = ""):
    """Search an item by item id or QR code."""
    keyword = q.strip()
    item = database.find_item_by_id(keyword) if keyword else None
    message = "品目が見つかりません" if keyword and item is None else ""
    return templates.TemplateResponse(
        request,
        "search.html",
        _context(request, keyword=keyword, item=item, message=message),
    )


@app.get("/stock-in")
async def stock_in_form(request: Request):
    """Show stock-in form."""
    return templates.TemplateResponse(
        request,
        "stock_in.html",
        _context(request),
    )


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
        request,
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
    return templates.TemplateResponse(
        request,
        "stock_out.html",
        _context(request),
    )


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
        request,
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


@app.get("/stock-adjust")
async def stock_adjust_form(request: Request, item_id: str = ""):
    """Show stock adjustment form for cycle counts."""
    normalized_item_id = item_id.strip()
    item = database.find_item_by_id(normalized_item_id) if normalized_item_id else None
    message = "品目が見つかりません" if normalized_item_id and item is None else ""
    return templates.TemplateResponse(
        request,
        "stock_adjust.html",
        _context(
            request,
            item=item,
            message=message,
            message_type="error",
            form={"item_id": normalized_item_id},
        ),
    )


@app.post("/stock-adjust")
async def stock_adjust_submit(
    request: Request,
    item_id: str = Form(...),
    actual_stock: str = Form(...),
    operator: str = Form(""),
    note: str = Form(""),
):
    """Set actual stock from a cycle count using database.py utilities."""
    message = ""
    message_type = "success"
    item = None
    stock_after = None
    difference = None
    normalized_item_id = item_id.strip()

    try:
        normalized_item_id = _normalize_item_id(item_id)
        parsed_actual_stock = _parse_non_negative_int(actual_stock, "実在庫数")
        item = database.find_item_by_id(normalized_item_id)
        if item is None:
            raise LookupError("品目が見つかりません")
        current_stock = int(item["current_stock"])
        difference = parsed_actual_stock - current_stock
        backup_path = database.create_auto_backup("stock_adjust")
        stock_after = database.adjust_stock(
            item["item_id"],
            parsed_actual_stock,
            operator.strip(),
            note.strip(),
        )
        item = database.find_item_by_id(item["item_id"])
        backup_message = f" 自動バックアップ: {backup_path}" if backup_path else ""
        message = (
            f"棚卸修正を記録しました。現在庫は {stock_after} です。"
            f"差異は {difference} です。{backup_message}"
        )
    except (LookupError, ValueError) as error:
        message = str(error)
        message_type = "error"

    return templates.TemplateResponse(
        request,
        "stock_adjust.html",
        _context(
            request,
            message=message,
            message_type=message_type,
            item=item,
            stock_after=stock_after,
            difference=difference,
            form={
                "item_id": normalized_item_id,
                "actual_stock": actual_stock,
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
        request,
        "low_stock.html",
        _context(request, items=low_stock_items, message=message),
    )
