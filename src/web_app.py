"""FastAPI web application for QR inventory system Ver2.0 Phase 4."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime
import hashlib
import hmac
import os
from pathlib import Path
import secrets
from typing import Any
from urllib.parse import quote

from fastapi import FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src import database, label_utils, qr_utils

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
    version="2.0.0-phase4",
    lifespan=lifespan,
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)


NAV_ITEMS = [
    {"label": "トップ", "url": "/", "requires_admin": False},
    {"label": "品目一覧", "url": "/items", "requires_admin": False},
    {"label": "品目検索", "url": "/search", "requires_admin": False},
    {"label": "入庫", "url": "/stock-in", "requires_admin": False},
    {"label": "出庫", "url": "/stock-out", "requires_admin": False},
    {"label": "最低在庫", "url": "/low-stock", "requires_admin": False},
    {"label": "管理者", "url": "/admin", "requires_admin": True},
    {"label": "品目登録", "url": "/items/new", "requires_admin": True},
    {"label": "棚卸修正", "url": "/stock-adjust", "requires_admin": True},
    {"label": "CSV取込", "url": "/csv-import", "requires_admin": True},
    {"label": "QRコード", "url": "/qr-codes", "requires_admin": True},
    {"label": "ラベル印刷", "url": "/labels", "requires_admin": True},
    {"label": "DBバックアップ", "url": "/db-backup", "requires_admin": True},
    {"label": "DB復旧", "url": "/db-restore", "requires_admin": True},
]

ADMIN_COOKIE_NAME = "qr_inventory_admin"
ADMIN_PASSWORD_ENV = "QR_INVENTORY_ADMIN_PASSWORD"
DEFAULT_ADMIN_PASSWORD = "admin123"
ADMIN_PROTECTED_PREFIXES = (
    "/admin",
    "/stock-adjust",
    "/csv-import",
    "/qr-codes",
    "/labels",
    "/db-backup",
    "/db-restore",
)
ADMIN_PROTECTED_ITEM_SUFFIXES = ("/edit", "/delete")


def _get_session_secret() -> str:
    """Return the secret used to sign the lightweight admin cookie."""
    return os.getenv(
        "QR_INVENTORY_SESSION_SECRET",
        "qr-inventory-system-dev-session-secret",
    )


def _create_admin_cookie_value() -> str:
    """Create a signed cookie value for the logged-in administrator state."""
    signature = hmac.new(
        _get_session_secret().encode("utf-8"),
        b"admin",
        hashlib.sha256,
    ).hexdigest()
    return f"admin.{signature}"


def _is_admin_logged_in(request: Request) -> bool:
    """Return whether the current cookie is authenticated as administrator."""
    cookie_value = request.cookies.get(ADMIN_COOKIE_NAME, "")
    return secrets.compare_digest(cookie_value, _create_admin_cookie_value())


def _get_admin_password() -> str:
    """Return the configured administrator password or the development default."""
    return os.getenv(ADMIN_PASSWORD_ENV) or DEFAULT_ADMIN_PASSWORD


def _is_admin_path(path: str) -> bool:
    """Return whether a path belongs to administrator-only Web functions."""
    if path == "/items/new" or path.startswith("/items/new/"):
        return True
    if path.startswith(ADMIN_PROTECTED_PREFIXES):
        return True
    if path.startswith("/items/") and path.endswith(ADMIN_PROTECTED_ITEM_SUFFIXES):
        return True
    return False


def _login_redirect(request: Request) -> RedirectResponse:
    """Redirect an unauthenticated admin request to the login page."""
    next_url = request.url.path
    if request.url.query:
        next_url = f"{next_url}?{request.url.query}"
    login_url = f"/login?next={quote(next_url, safe='/')}"
    return RedirectResponse(login_url, status_code=303)


def _safe_next_url(next_url: str) -> str:
    """Allow only same-site relative redirects after login."""
    normalized = next_url.strip() or "/admin"
    if not normalized.startswith("/") or normalized.startswith("//"):
        return "/admin"
    if normalized.startswith(("/login", "/logout")):
        return "/admin"
    return normalized


def _context(request: Request, **extra: Any) -> dict[str, Any]:
    """Build common template context."""
    return {
        "request": request,
        "nav_items": NAV_ITEMS,
        "is_admin_logged_in": _is_admin_logged_in(request),
        **extra,
    }


def _format_path(path: Path | None) -> str:
    """Return a repository-relative display path when possible."""
    if path is None:
        return "DB未作成のため作成なし"
    try:
        return str(path.resolve().relative_to(ROOT_DIR.resolve()))
    except ValueError:
        return str(path)


def _format_backup_rows() -> list[dict[str, object]]:
    """Return backup metadata formatted for template display."""
    rows: list[dict[str, object]] = []
    for index, backup in enumerate(database.list_backup_files(), start=1):
        updated_at = backup["updated_at"]
        rows.append(
            {
                "index": index,
                "filename": backup["filename"],
                "path": _format_path(Path(backup["path"])),
                "updated_at": updated_at.strftime("%Y-%m-%d %H:%M:%S"),
                "size": backup["size"],
            }
        )
    return rows


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


@app.middleware("http")
async def admin_lock_middleware(request: Request, call_next):
    """Require administrator login before serving protected Web pages."""
    if _is_admin_path(request.url.path) and not _is_admin_logged_in(request):
        return _login_redirect(request)
    return await call_next(request)


@app.get("/login")
async def login_form(request: Request, next: str = "/admin"):
    """Show the administrator login form."""
    return templates.TemplateResponse(
        request,
        "login.html",
        _context(request, next_url=_safe_next_url(next)),
    )


@app.post("/login")
async def login_submit(
    request: Request,
    password: str = Form(...),
    next: str = Form("/admin"),
):
    """Authenticate administrator password and store login state in session."""
    next_url = _safe_next_url(next)
    if secrets.compare_digest(password, _get_admin_password()):
        response = RedirectResponse(next_url, status_code=303)
        response.set_cookie(
            ADMIN_COOKIE_NAME,
            _create_admin_cookie_value(),
            httponly=True,
            samesite="lax",
        )
        return response

    return templates.TemplateResponse(
        request,
        "login.html",
        _context(
            request,
            next_url=next_url,
            message="管理者パスワードが違います。",
            message_type="error",
        ),
        status_code=401,
    )


@app.get("/logout")
async def logout(request: Request):
    """Clear administrator login state."""
    response = RedirectResponse("/login", status_code=303)
    response.delete_cookie(ADMIN_COOKIE_NAME)
    return response


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


@app.get("/admin")
async def admin_menu(request: Request):
    """Show the Web Phase 2 administrator menu."""
    items = database.list_items()
    low_stock_items = database.list_low_stock_items()
    return templates.TemplateResponse(
        request,
        "admin.html",
        _context(
            request,
            item_count=len(items),
            low_stock_count=len(low_stock_items),
        ),
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
async def create_item(
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
async def update_item(
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
async def delete_item(
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
async def adjust_stock(
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


@app.get("/csv-import")
async def csv_import_form(request: Request):
    """Show the CSV import placeholder form."""
    return templates.TemplateResponse(
        request,
        "csv_import.html",
        _context(request),
    )


@app.post("/csv-import")
async def csv_import_preview_placeholder(request: Request):
    """Accept the CSV import form without importing data yet."""
    return templates.TemplateResponse(
        request,
        "csv_import.html",
        _context(
            request,
            message="CSV取込機能は準備中です。今回はファイル選択フォームのみ利用できます。",
            message_type="info",
        ),
    )

@app.get("/qr-codes")
async def qr_codes_form(request: Request):
    """Show QR code generation form."""
    return templates.TemplateResponse(
        request,
        "qr_codes.html",
        _context(request, item_count=len(database.list_items())),
    )


@app.post("/qr-codes/single")
async def qr_code_single(request: Request, item_id: str = Form(...)):
    """Generate one item QR code using qr_utils.py."""
    message = ""
    message_type = "success"
    saved_path = None
    normalized_item_id = item_id.strip()

    try:
        normalized_item_id = _normalize_item_id(item_id)
        item = database.find_item_by_id(normalized_item_id)
        if item is None:
            raise LookupError("品目が見つかりません")
        saved_path = qr_utils.generate_item_qr_code(item)
        message = "QRコードを生成しました。"
    except (LookupError, ValueError) as error:
        message = str(error)
        message_type = "error"

    return templates.TemplateResponse(
        request,
        "qr_codes.html",
        _context(
            request,
            message=message,
            message_type=message_type,
            saved_path=_format_path(saved_path) if saved_path else "",
            form={"item_id": normalized_item_id},
            item_count=len(database.list_items()),
        ),
    )


@app.post("/qr-codes/all")
async def qr_code_all(request: Request):
    """Generate QR codes for all items using qr_utils.py."""
    message = ""
    message_type = "success"
    result = None

    try:
        items = database.list_items()
        result = qr_utils.generate_all_qr_codes(items)
        message = "全品目のQRコードを生成しました。"
    except ValueError as error:
        message = str(error)
        message_type = "error"

    return templates.TemplateResponse(
        request,
        "qr_codes.html",
        _context(
            request,
            message=message,
            message_type=message_type,
            result=result,
            saved_paths=(
                [_format_path(Path(path)) for path in result["paths"]]
                if result
                else []
            ),
            item_count=len(database.list_items()),
        ),
    )


@app.get("/labels")
async def labels_form(request: Request):
    """Show QR label print HTML generation form."""
    return templates.TemplateResponse(
        request,
        "labels.html",
        _context(request, item_count=len(database.list_items())),
    )


@app.post("/labels/generate")
async def labels_generate(request: Request):
    """Generate printable QR label HTML using label_utils.py."""
    message = ""
    message_type = "success"
    saved_path = None

    try:
        items = database.list_items()
        if not items:
            raise ValueError("品目が登録されていません。")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        saved_path = label_utils.generate_qr_label_sheet(
            items, label_utils.LABEL_DIR / f"qr_labels_{timestamp}.html"
        )
        message = "QRラベル印刷用HTMLを生成しました。"
    except ValueError as error:
        message = str(error)
        message_type = "error"

    return templates.TemplateResponse(
        request,
        "labels.html",
        _context(
            request,
            message=message,
            message_type=message_type,
            saved_path=_format_path(saved_path) if saved_path else "",
            item_count=len(database.list_items()),
        ),
    )


@app.get("/db-backup")
async def db_backup_form(request: Request):
    """Show DB backup form and backup list."""
    return templates.TemplateResponse(
        request,
        "db_backup.html",
        _context(request, backups=_format_backup_rows()),
    )


@app.post("/db-backup")
async def db_backup_create(request: Request):
    """Create a manual database backup using database.py."""
    message = ""
    message_type = "success"
    backup_path = None

    try:
        backup_path = database.backup_database()
        message = "DBバックアップを作成しました。"
    except (FileNotFoundError, ValueError) as error:
        message = str(error)
        message_type = "error"

    return templates.TemplateResponse(
        request,
        "db_backup.html",
        _context(
            request,
            message=message,
            message_type=message_type,
            backup_path=_format_path(backup_path) if backup_path else "",
            backups=_format_backup_rows(),
        ),
    )


@app.get("/db-restore")
async def db_restore_form(request: Request):
    """Show DB restore form with backup list."""
    return templates.TemplateResponse(
        request,
        "db_restore.html",
        _context(request, backups=_format_backup_rows()),
    )


@app.post("/db-restore")
async def db_restore_execute(
    request: Request,
    backup_filename: str = Form(...),
    confirmation: str = Form(...),
):
    """Restore the database after requiring RESTORE confirmation."""
    message = ""
    message_type = "success"
    restore_result = None

    try:
        if confirmation.strip() != "RESTORE":
            raise ValueError("確認文字列が一致しないため、DB復旧を中止しました。")
        backup_names = {
            str(row["filename"]): row for row in database.list_backup_files()
        }
        selected = backup_names.get(backup_filename)
        if selected is None:
            raise ValueError("選択したバックアップが見つかりません。")
        restore_result = database.restore_database_from_backup(selected["path"])
        message = "DBを復旧しました。"
    except (FileNotFoundError, ValueError) as error:
        message = str(error)
        message_type = "error"

    return templates.TemplateResponse(
        request,
        "db_restore.html",
        _context(
            request,
            message=message,
            message_type=message_type,
            restore_result=(
                {key: _format_path(value) for key, value in restore_result.items()}
                if restore_result
                else None
            ),
            backups=_format_backup_rows(),
        ),
    )
