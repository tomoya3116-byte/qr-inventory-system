"""CustomTkinter GUI entry point for the inventory system."""

from __future__ import annotations

import os
import tkinter as tk
import webbrowser
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk
from typing import Callable, Iterable

import customtkinter as ctk

from database import (
    adjust_stock,
    backup_database,
    create_auto_backup,
    create_item,
    decrease_stock,
    delete_item,
    find_item_by_id,
    get_item_for_qr,
    import_items_from_csv,
    increase_stock,
    initialize_database,
    list_backup_files,
    list_items,
    list_low_stock_items,
    preview_import_items_from_csv,
    restore_database_from_backup,
    update_item,
)
from label_utils import LABEL_DIR, generate_qr_label_sheet
from qr_utils import QR_CODE_DIR, generate_all_qr_codes, generate_item_qr_code

APP_TITLE = "貯蔵品管理システム"
WINDOW_SIZE = "1180x760"

COLOR_BACKGROUND = "#f7f9fc"
COLOR_SURFACE = "#ffffff"
COLOR_TEXT = "#1d1d1f"
COLOR_MUTED = "#6e6e73"
COLOR_BORDER = "#d9e2ef"
COLOR_PRIMARY = "#0a84ff"
COLOR_PRIMARY_HOVER = "#006edb"
COLOR_SECONDARY = "#eef5ff"
COLOR_SECONDARY_HOVER = "#dbeaff"
COLOR_SUCCESS = "#168a3a"
COLOR_ERROR = "#c62828"

FONT_FAMILY = "Yu Gothic"
FONT_TITLE = (FONT_FAMILY, 26, "bold")
FONT_SECTION = (FONT_FAMILY, 20, "bold")
FONT_BODY = (FONT_FAMILY, 15)
FONT_BODY_BOLD = (FONT_FAMILY, 15, "bold")
FONT_SMALL = (FONT_FAMILY, 13)


def _value(row: object, key: str, default: str = "") -> object:
    """Return a safe display value from a sqlite Row-like object."""
    try:
        value = row[key]  # type: ignore[index]
    except (IndexError, KeyError, TypeError):
        return default
    if value is None:
        return default
    return value


def _to_positive_int(text: str, action_name: str) -> int:
    """Convert user input to a positive integer with an easy Japanese message."""
    stripped = text.strip()
    if not stripped:
        raise ValueError(f"{action_name}する数量を入力してください。")
    try:
        quantity = int(stripped)
    except ValueError as exc:
        raise ValueError("数量は半角数字で入力してください。") from exc
    if quantity <= 0:
        raise ValueError("数量は1以上で入力してください。")
    return quantity


def _to_non_negative_int(text: str, field_name: str) -> int:
    """Convert user input to a zero-or-positive integer with an easy Japanese message."""
    stripped = text.strip()
    if not stripped:
        raise ValueError(f"{field_name}を入力してください。")
    try:
        value = int(stripped)
    except ValueError as exc:
        raise ValueError(f"{field_name}は半角数字で入力してください。") from exc
    if value < 0:
        raise ValueError(f"{field_name}は0以上で入力してください。")
    return value


class InventoryApp(ctk.CTk):
    """Main CustomTkinter application."""

    def __init__(self) -> None:
        super().__init__()
        initialize_database()

        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self.title(APP_TITLE)
        self.geometry(WINDOW_SIZE)
        self.minsize(1040, 680)
        self.configure(fg_color=COLOR_BACKGROUND)

        self.menu_buttons: dict[str, ctk.CTkButton] = {}
        self.current_screen = ""
        self.admin_mode = False
        # このパスワード方式は簡易ロックです。本格運用では環境変数、設定ファイルのハッシュ化、OSアカウント権限などを検討してください。
        self.admin_password = os.getenv("QR_INVENTORY_ADMIN_PASSWORD", "admin123")
        self.menu_frame: ctk.CTkFrame | None = None

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_menu()
        self.content = ctk.CTkFrame(
            self,
            fg_color=COLOR_SURFACE,
            corner_radius=26,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        self.content.grid(row=0, column=1, sticky="nsew", padx=(0, 24), pady=24)
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(1, weight=1)

        self.show_search_screen()

    def _build_menu(self) -> None:
        if self.menu_frame is not None:
            self.menu_frame.destroy()
        self.menu_buttons = {}

        menu = ctk.CTkFrame(self, width=250, fg_color=COLOR_BACKGROUND, corner_radius=0)
        menu.grid(row=0, column=0, sticky="ns", padx=(24, 18), pady=24)
        menu.grid_propagate(False)
        menu.grid_columnconfigure(0, weight=1)
        self.menu_frame = menu

        title = "貯蔵品\n管理システム"
        if self.admin_mode:
            title += "\n管理者モード"
        ctk.CTkLabel(
            menu,
            text=title,
            font=FONT_TITLE,
            text_color=COLOR_TEXT,
            justify="left",
        ).grid(row=0, column=0, sticky="w", pady=(4, 24))

        if self.admin_mode:
            menu_items: list[tuple[str, str, Callable[[], None]]] = [
                ("create", "品目登録", self.show_item_create_screen),
                ("edit", "品目編集", self.show_item_edit_screen),
                ("delete", "品目削除", self.show_item_delete_screen),
                ("adjust", "棚卸修正", self.show_stock_adjust_screen),
                ("csv", "CSV品目マスタ取込", self.show_csv_import_screen),
                ("csv_preview", "CSV取込プレビュー", self.show_csv_import_screen),
                ("qr", "QRコード生成", self.show_qr_generation_screen),
                ("labels", "QRコード印刷HTML", self.show_label_html_screen),
                ("backup", "DBバックアップ", self.show_db_backup_screen),
                ("restore", "DB復旧", self.show_db_restore_screen),
            ]
        else:
            menu_items = [
                ("search", "品目検索", self.show_search_screen),
                ("list", "品目一覧", self.show_list_screen),
                ("in", "入庫", self.show_stock_in_screen),
                ("out", "出庫", self.show_stock_out_screen),
                ("alert", "最低在庫アラート", self.show_low_stock_screen),
            ]

        button_height = 38 if self.admin_mode else 42
        button_pady = 3 if self.admin_mode else 4
        for row, (key, label, command) in enumerate(menu_items, start=1):
            button = ctk.CTkButton(
                menu,
                text=label,
                command=command,
                height=button_height,
                corner_radius=16,
                border_width=1,
                border_color=COLOR_BORDER,
                fg_color=COLOR_SURFACE,
                hover_color=COLOR_SECONDARY_HOVER,
                text_color=COLOR_TEXT,
                font=FONT_BODY_BOLD,
                anchor="w",
            )
            button.grid(row=row, column=0, sticky="ew", pady=button_pady)
            self.menu_buttons[key] = button

        bottom_row = len(menu_items) + 2
        if self.admin_mode:
            self._secondary_button(menu, "管理者モード終了", self.exit_admin_mode).grid(
                row=bottom_row, column=0, sticky="ew", pady=(18, 0)
            )
            note = "危険操作・管理操作は\n確認してから実行してください。"
        else:
            self._primary_button(menu, "管理者メニュー", self.request_admin_login).grid(
                row=bottom_row, column=0, sticky="ew", pady=(18, 0)
            )
            note = "日常操作だけをまとめた\n現場向け画面です。"

        ctk.CTkLabel(
            menu,
            text=note,
            font=FONT_SMALL,
            text_color=COLOR_MUTED,
            justify="left",
        ).grid(row=99, column=0, sticky="sw", pady=(36, 0))
        menu.grid_rowconfigure(98, weight=1)

    def request_admin_login(self) -> None:
        password = simpledialog.askstring(
            "管理者パスワード",
            "管理者パスワードを入力してください。",
            show="*",
            parent=self,
        )
        if password is None:
            return
        if password != self.admin_password:
            messagebox.showerror("認証エラー", "パスワードが違います", parent=self)
            return
        self.admin_mode = True
        self._build_menu()
        self.show_admin_home_screen()

    def exit_admin_mode(self) -> None:
        self.admin_mode = False
        self._build_menu()
        self.show_search_screen()

    def _require_admin(self) -> bool:
        if self.admin_mode:
            return True
        messagebox.showwarning("管理者ロック", "管理者メニューからログインしてください。", parent=self)
        return False

    def show_admin_home_screen(self) -> None:
        if not self._require_admin():
            return
        self._set_active_menu("")
        self._clear_content()
        self._screen_header("管理者メニュー", "管理者モードです。危険操作・管理操作を実行できます。")
        body = self._body_frame()
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=1)
        actions = [
            ("品目登録", self.show_item_create_screen),
            ("品目編集", self.show_item_edit_screen),
            ("品目削除", self.show_item_delete_screen),
            ("棚卸修正", self.show_stock_adjust_screen),
            ("CSV品目マスタ取込", self.show_csv_import_screen),
            ("CSV取込プレビュー", self.show_csv_import_screen),
            ("QRコード生成", self.show_qr_generation_screen),
            ("QRコード印刷HTML", self.show_label_html_screen),
            ("DBバックアップ", self.show_db_backup_screen),
            ("DB復旧", self.show_db_restore_screen),
        ]
        for index, (label, command) in enumerate(actions):
            self._secondary_button(body, label, command).grid(
                row=index // 2, column=index % 2, sticky="ew", padx=8, pady=8
            )

    def _set_active_menu(self, key: str) -> None:
        self.current_screen = key
        for button_key, button in self.menu_buttons.items():
            if button_key == key:
                button.configure(
                    fg_color=COLOR_PRIMARY,
                    hover_color=COLOR_PRIMARY_HOVER,
                    text_color="white",
                    border_color=COLOR_PRIMARY,
                )
            else:
                button.configure(
                    fg_color=COLOR_SURFACE,
                    hover_color=COLOR_SECONDARY_HOVER,
                    text_color=COLOR_TEXT,
                    border_color=COLOR_BORDER,
                )

    def _clear_content(self) -> None:
        for widget in self.content.winfo_children():
            widget.destroy()

    def _screen_header(self, title: str, description: str) -> ctk.CTkFrame:
        header = ctk.CTkFrame(self.content, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=34, pady=(30, 20))
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            header,
            text=title,
            font=FONT_TITLE,
            text_color=COLOR_TEXT,
            anchor="w",
        ).grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(
            header,
            text=description,
            font=FONT_BODY,
            text_color=COLOR_MUTED,
            anchor="w",
        ).grid(row=1, column=0, sticky="ew", pady=(8, 0))
        return header

    def _body_frame(self) -> ctk.CTkFrame:
        body = ctk.CTkFrame(self.content, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew", padx=34, pady=(0, 30))
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(0, weight=1)
        return body

    def _primary_button(self, parent: ctk.CTkBaseClass, text: str, command: Callable[[], None]) -> ctk.CTkButton:
        return ctk.CTkButton(
            parent,
            text=text,
            command=command,
            height=46,
            corner_radius=16,
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            text_color="white",
            font=FONT_BODY_BOLD,
        )

    def _secondary_button(self, parent: ctk.CTkBaseClass, text: str, command: Callable[[], None]) -> ctk.CTkButton:
        return ctk.CTkButton(
            parent,
            text=text,
            command=command,
            height=44,
            corner_radius=16,
            border_width=1,
            border_color=COLOR_BORDER,
            fg_color=COLOR_SECONDARY,
            hover_color=COLOR_SECONDARY_HOVER,
            text_color=COLOR_TEXT,
            font=FONT_BODY_BOLD,
        )

    def _entry(self, parent: ctk.CTkBaseClass, placeholder: str = "") -> ctk.CTkEntry:
        return ctk.CTkEntry(
            parent,
            placeholder_text=placeholder,
            height=44,
            corner_radius=14,
            border_width=1,
            border_color=COLOR_BORDER,
            fg_color=COLOR_SURFACE,
            text_color=COLOR_TEXT,
            font=FONT_BODY,
        )

    def _label(self, parent: ctk.CTkBaseClass, text: str) -> ctk.CTkLabel:
        return ctk.CTkLabel(parent, text=text, font=FONT_BODY_BOLD, text_color=COLOR_TEXT, anchor="w")

    def _message_label(self, parent: ctk.CTkBaseClass) -> ctk.CTkLabel:
        return ctk.CTkLabel(parent, text="", font=FONT_BODY_BOLD, text_color=COLOR_MUTED, anchor="w")

    def _set_message(self, label: ctk.CTkLabel, text: str, is_error: bool = False) -> None:
        label.configure(text=text, text_color=COLOR_ERROR if is_error else COLOR_SUCCESS)

    def _form_frame(self, parent: ctk.CTkBaseClass) -> ctk.CTkFrame:
        form = ctk.CTkFrame(
            parent,
            fg_color=COLOR_BACKGROUND,
            corner_radius=22,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        form.grid_columnconfigure(1, weight=1)
        return form

    def _fill_entry(self, entry: ctk.CTkEntry, value: object) -> None:
        entry.delete(0, tk.END)
        entry.insert(0, str(value or ""))

    def _create_entry_grid(
        self,
        form: ctk.CTkFrame,
        fields: list[tuple[str, str, str]],
    ) -> dict[str, ctk.CTkEntry]:
        entries: dict[str, ctk.CTkEntry] = {}
        for row_index, (key, label, placeholder) in enumerate(fields):
            self._label(form, label).grid(
                row=row_index, column=0, sticky="w", padx=(24, 18), pady=10
            )
            entry = self._entry(form, placeholder)
            entry.grid(row=row_index, column=1, sticky="ew", padx=(0, 24), pady=10)
            entries[key] = entry
        return entries

    def show_search_screen(self) -> None:
        self._set_active_menu("search")
        self._clear_content()
        self._screen_header("品目検索", "品目IDまたはQRコードを入力して、保管場所や在庫を確認できます。")
        body = self._body_frame()
        body.grid_rowconfigure(2, weight=1)

        form = ctk.CTkFrame(body, fg_color="transparent")
        form.grid(row=0, column=0, sticky="ew")
        form.grid_columnconfigure(1, weight=1)

        self._label(form, "品目ID").grid(row=0, column=0, padx=(0, 14), sticky="w")
        item_entry = self._entry(form, "例: ITEM-0001")
        item_entry.grid(row=0, column=1, sticky="ew")

        result_frame = ctk.CTkFrame(
            body,
            fg_color=COLOR_BACKGROUND,
            corner_radius=22,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        result_frame.grid(row=2, column=0, sticky="nsew", pady=(24, 0))
        result_frame.grid_columnconfigure(1, weight=1)

        message = self._message_label(body)
        message.grid(row=1, column=0, sticky="ew", pady=(16, 0))

        def clear_result() -> None:
            for child in result_frame.winfo_children():
                child.destroy()

        def search() -> None:
            item_id = item_entry.get().strip()
            clear_result()
            if not item_id:
                self._set_message(message, "品目IDを入力してください。", True)
                return
            item = find_item_by_id(item_id)
            if item is None:
                self._set_message(message, "該当する品目が見つかりません。入力内容を確認してください。", True)
                return

            self._set_message(message, "品目が見つかりました。")
            fields = [
                ("品目ID", "item_id"),
                ("品名", "item_name"),
                ("型式", "model_number"),
                ("メーカー", "maker"),
                ("保管場所", "location"),
                ("現在庫", "current_stock"),
                ("最低在庫", "min_stock"),
                ("単位", "unit"),
                ("備考", "note"),
            ]
            for row_index, (label, key) in enumerate(fields):
                ctk.CTkLabel(
                    result_frame,
                    text=label,
                    font=FONT_BODY_BOLD,
                    text_color=COLOR_MUTED,
                    anchor="w",
                ).grid(row=row_index, column=0, sticky="nw", padx=(24, 18), pady=12)
                ctk.CTkLabel(
                    result_frame,
                    text=str(_value(item, key, "-")) or "-",
                    font=FONT_SECTION if key == "item_name" else FONT_BODY,
                    text_color=COLOR_TEXT,
                    anchor="w",
                    justify="left",
                    wraplength=700,
                ).grid(row=row_index, column=1, sticky="ew", padx=(0, 24), pady=12)

        self._primary_button(form, "検索", search).grid(row=0, column=2, padx=(14, 0))
        item_entry.bind("<Return>", lambda _event: search())
        item_entry.focus_set()

    def show_list_screen(self) -> None:
        self._set_active_menu("list")
        self._clear_content()
        header = self._screen_header("品目一覧", "登録されている品目をまとめて確認できます。")
        body = self._body_frame()

        table_holder = ctk.CTkFrame(body, fg_color="transparent")
        table_holder.grid(row=0, column=0, sticky="nsew")
        table_holder.grid_columnconfigure(0, weight=1)
        table_holder.grid_rowconfigure(0, weight=1)

        def refresh() -> None:
            self._render_table(
                table_holder,
                list_items(),
                [
                    ("品目ID", "item_id", 120),
                    ("品名", "item_name", 180),
                    ("型式", "model_number", 130),
                    ("メーカー", "maker", 130),
                    ("保管場所", "location", 120),
                    ("現在庫", "current_stock", 85),
                    ("最低在庫", "min_stock", 85),
                    ("単位", "unit", 70),
                ],
                "登録品目がありません。",
            )

        self._secondary_button(header, "更新", refresh).grid(row=0, column=1, rowspan=2, padx=(16, 0))
        refresh()

    def show_item_create_screen(self) -> None:
        if not self._admin_screen_guard("create"):
            return
        self._screen_header(
            "品目登録",
            "新しい品目マスタを登録します。QRコード値は品目IDと同じ値で保存されます。",
        )
        body = self._body_frame()
        body.grid_rowconfigure(1, weight=1)

        form = self._form_frame(body)
        form.grid(row=0, column=0, sticky="ew")

        fields = [
            ("item_id", "品目ID", "例: ITEM-0003"),
            ("item_name", "品名", "例: 六角ボルト"),
            ("model_number", "型式", "例: M6-20"),
            ("maker", "メーカー", "例: メーカーC"),
            ("location", "保管場所", "例: 棚C-03"),
            ("unit", "単位", "例: 個"),
            ("min_stock", "最低在庫数", "例: 5"),
            ("initial_stock", "初期在庫数", "例: 20"),
            ("note", "備考", "必要な場合だけ入力"),
        ]
        entries = self._create_entry_grid(form, fields)

        message = self._message_label(body)
        message.grid(row=1, column=0, sticky="new", pady=(18, 0))

        def register() -> None:
            item_id = entries["item_id"].get().strip()
            item_name = entries["item_name"].get().strip()
            if not item_id:
                self._set_message(message, "品目IDを入力してください。", True)
                return
            if not item_name:
                self._set_message(message, "品名を入力してください。", True)
                return
            try:
                min_stock = _to_non_negative_int(entries["min_stock"].get(), "最低在庫数")
                initial_stock = _to_non_negative_int(entries["initial_stock"].get(), "初期在庫数")
                create_item(
                    item_id=item_id,
                    item_name=item_name,
                    model_number=entries["model_number"].get().strip(),
                    maker=entries["maker"].get().strip(),
                    location=entries["location"].get().strip(),
                    unit=entries["unit"].get().strip(),
                    min_stock=min_stock,
                    initial_stock=initial_stock,
                    note=entries["note"].get().strip(),
                )
            except ValueError as exc:
                self._set_message(message, str(exc), True)
                return

            self._set_message(message, f"品目ID '{item_id}' を登録しました。品目一覧で確認できます。")
            for entry in entries.values():
                entry.delete(0, tk.END)
            entries["item_id"].focus_set()

        self._primary_button(form, "登録", register).grid(
            row=len(fields), column=1, sticky="e", padx=(0, 24), pady=(10, 24)
        )
        for entry in entries.values():
            entry.bind("<Return>", lambda _event: register())
        entries["item_id"].focus_set()

    def show_item_edit_screen(self) -> None:
        if not self._admin_screen_guard("edit"):
            return
        self._screen_header("品目編集", "品目IDで検索し、品名・型式・保管場所などのマスタ情報を更新します。")
        body = self._body_frame()
        body.grid_rowconfigure(2, weight=1)

        search_form = ctk.CTkFrame(body, fg_color="transparent")
        search_form.grid(row=0, column=0, sticky="ew")
        search_form.grid_columnconfigure(1, weight=1)
        self._label(search_form, "品目ID").grid(row=0, column=0, padx=(0, 14), sticky="w")
        search_entry = self._entry(search_form, "例: ITEM-0001")
        search_entry.grid(row=0, column=1, sticky="ew")

        form = self._form_frame(body)
        form.grid(row=2, column=0, sticky="new", pady=(20, 0))
        fields = [
            ("item_name", "品名", "検索後に表示されます"),
            ("model_number", "型式", "検索後に表示されます"),
            ("maker", "メーカー", "検索後に表示されます"),
            ("location", "保管場所", "検索後に表示されます"),
            ("unit", "単位", "検索後に表示されます"),
            ("min_stock", "最低在庫数", "検索後に表示されます"),
            ("note", "備考", "検索後に表示されます"),
        ]
        entries = self._create_entry_grid(form, fields)

        message = self._message_label(body)
        message.grid(row=1, column=0, sticky="ew", pady=(16, 0))
        current_item_id = ""

        def search() -> None:
            nonlocal current_item_id
            item_id = search_entry.get().strip()
            if not item_id:
                self._set_message(message, "品目IDを入力してください。", True)
                return
            item = find_item_by_id(item_id)
            if item is None:
                current_item_id = ""
                self._set_message(message, "該当する品目が見つかりません。入力内容を確認してください。", True)
                return
            current_item_id = str(item["item_id"])
            for key, _label, _placeholder in fields:
                self._fill_entry(entries[key], _value(item, key, ""))
            self._set_message(message, f"品目ID '{current_item_id}' の情報を表示しました。編集後に更新してください。")
            entries["item_name"].focus_set()

        def update() -> None:
            if not current_item_id:
                self._set_message(message, "先に品目IDを検索してください。", True)
                return
            item_name = entries["item_name"].get().strip()
            if not item_name:
                self._set_message(message, "品名を入力してください。", True)
                return
            try:
                min_stock = _to_non_negative_int(entries["min_stock"].get(), "最低在庫数")
                update_item(
                    current_item_id,
                    item_name,
                    entries["model_number"].get().strip(),
                    entries["maker"].get().strip(),
                    entries["location"].get().strip(),
                    entries["unit"].get().strip(),
                    min_stock,
                    entries["note"].get().strip(),
                )
            except ValueError as exc:
                self._set_message(message, str(exc), True)
                return
            self._set_message(message, f"品目ID '{current_item_id}' を更新しました。品目一覧を開いて更新結果を確認できます。")

        self._primary_button(search_form, "検索", search).grid(row=0, column=2, padx=(14, 0))
        button_frame = ctk.CTkFrame(form, fg_color="transparent")
        button_frame.grid(row=len(fields), column=1, sticky="e", padx=(0, 24), pady=(10, 24))
        self._secondary_button(button_frame, "品目一覧を開く", self.show_list_screen).grid(row=0, column=0, padx=(0, 12))
        self._primary_button(button_frame, "更新", update).grid(row=0, column=1)
        search_entry.bind("<Return>", lambda _event: search())
        for entry in entries.values():
            entry.bind("<Return>", lambda _event: update())
        search_entry.focus_set()

    def show_stock_adjust_screen(self) -> None:
        if not self._admin_screen_guard("adjust"):
            return
        self._screen_header("棚卸修正", "実在庫数を入力し、確認後にADJUST履歴として在庫差異を記録します。")
        body = self._body_frame()
        body.grid_rowconfigure(2, weight=1)

        form = self._form_frame(body)
        form.grid(row=0, column=0, sticky="ew")
        fields = [
            ("item_id", "品目ID", "例: ITEM-0001"),
            ("actual_stock", "実在庫数", "例: 8"),
            ("operator", "作業者", "例: 山田"),
            ("note", "備考", "必要な場合だけ入力"),
        ]
        entries = self._create_entry_grid(form, fields)

        current_label = ctk.CTkLabel(
            form,
            text="現在庫: - / 差異: -",
            font=FONT_BODY_BOLD,
            text_color=COLOR_MUTED,
            anchor="w",
        )
        current_label.grid(row=len(fields), column=1, sticky="ew", padx=(0, 24), pady=(4, 10))

        message = self._message_label(body)
        message.grid(row=1, column=0, sticky="ew", pady=(16, 0))
        loaded_item: object | None = None

        def refresh_difference() -> None:
            if loaded_item is None:
                current_label.configure(text="現在庫: - / 差異: -", text_color=COLOR_MUTED)
                return
            current_stock = int(_value(loaded_item, "current_stock", 0))
            actual_text = entries["actual_stock"].get().strip()
            if not actual_text:
                current_label.configure(text=f"現在庫: {current_stock} / 差異: -", text_color=COLOR_MUTED)
                return
            try:
                actual_stock = int(actual_text)
            except ValueError:
                current_label.configure(text=f"現在庫: {current_stock} / 差異: 入力値を確認してください", text_color=COLOR_ERROR)
                return
            difference = actual_stock - current_stock
            current_label.configure(text=f"現在庫: {current_stock} / 差異: {difference}", text_color=COLOR_TEXT)

        def load_item() -> None:
            nonlocal loaded_item
            item_id = entries["item_id"].get().strip()
            if not item_id:
                loaded_item = None
                refresh_difference()
                self._set_message(message, "品目IDを入力してください。", True)
                return
            item = find_item_by_id(item_id)
            if item is None:
                loaded_item = None
                refresh_difference()
                self._set_message(message, "該当する品目が見つかりません。入力内容を確認してください。", True)
                return
            loaded_item = item
            refresh_difference()
            self._set_message(message, f"{item['item_name']} の現在庫を表示しました。実在庫数を入力してください。")
            entries["actual_stock"].focus_set()

        def execute() -> None:
            nonlocal loaded_item
            entered_item_id = entries["item_id"].get().strip()
            loaded_item_id = str(_value(loaded_item, "item_id", "")) if loaded_item is not None else ""
            if loaded_item is None or entered_item_id != loaded_item_id:
                load_item()
                if loaded_item is None:
                    return
            item_id = str(_value(loaded_item, "item_id", entries["item_id"].get().strip()))
            item_name = str(_value(loaded_item, "item_name", ""))
            current_stock = int(_value(loaded_item, "current_stock", 0))
            try:
                actual_stock = _to_non_negative_int(entries["actual_stock"].get(), "実在庫数")
            except ValueError as exc:
                self._set_message(message, str(exc), True)
                return
            difference = actual_stock - current_stock
            ok = messagebox.askyesno(
                "棚卸修正の確認",
                (
                    f"以下の内容で棚卸修正しますか？\n\n"
                    f"品目ID: {item_id}\n"
                    f"品名: {item_name}\n"
                    f"現在庫: {current_stock}\n"
                    f"実在庫: {actual_stock}\n"
                    f"差異: {difference}"
                ),
                parent=self,
            )
            if not ok:
                self._set_message(message, "棚卸修正を中止しました。", True)
                return
            try:
                backup_path = create_auto_backup("stock_adjust")
                stock_after = adjust_stock(
                    item_id,
                    actual_stock,
                    operator=entries["operator"].get().strip(),
                    note=entries["note"].get().strip(),
                )
            except ValueError as exc:
                self._set_message(message, str(exc), True)
                return
            backup_message = f" 自動バックアップ: {backup_path}" if backup_path is not None else ""
            self._set_message(message, f"棚卸修正を記録しました。処理後現在庫: {stock_after}.{backup_message}")
            loaded_item = find_item_by_id(item_id)
            refresh_difference()

        self._secondary_button(form, "現在庫を表示", load_item).grid(
            row=0, column=2, padx=(0, 24), pady=10
        )
        self._primary_button(form, "棚卸修正を実行", execute).grid(
            row=len(fields) + 1, column=1, sticky="e", padx=(0, 24), pady=(10, 24)
        )
        entries["item_id"].bind("<Return>", lambda _event: load_item())
        entries["actual_stock"].bind("<KeyRelease>", lambda _event: refresh_difference())
        for key in ("actual_stock", "operator", "note"):
            entries[key].bind("<Return>", lambda _event: execute())
        entries["item_id"].focus_set()

    def show_stock_in_screen(self) -> None:
        self._show_stock_operation_screen("in", "入庫", "入庫する品目と数量を入力してください。", increase_stock)

    def show_stock_out_screen(self) -> None:
        self._show_stock_operation_screen("out", "出庫", "出庫する品目と数量を入力してください。", decrease_stock)

    def _show_stock_operation_screen(
        self,
        menu_key: str,
        action_name: str,
        description: str,
        stock_function: Callable[[str, int, str, str], int],
    ) -> None:
        self._set_active_menu(menu_key)
        self._clear_content()
        self._screen_header(action_name, description)
        body = self._body_frame()
        body.grid_rowconfigure(1, weight=1)

        form = ctk.CTkFrame(
            body,
            fg_color=COLOR_BACKGROUND,
            corner_radius=22,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        form.grid(row=0, column=0, sticky="ew")
        form.grid_columnconfigure(1, weight=1)

        entries: dict[str, ctk.CTkEntry] = {}
        fields = [
            ("item_id", "品目ID", "例: ITEM-0001"),
            ("quantity", "数量", "例: 1"),
            ("operator", "作業者", "例: 山田"),
            ("note", "備考", "必要な場合だけ入力"),
        ]
        for row_index, (key, label, placeholder) in enumerate(fields):
            self._label(form, label).grid(row=row_index, column=0, sticky="w", padx=(24, 18), pady=12)
            entry = self._entry(form, placeholder)
            entry.grid(row=row_index, column=1, sticky="ew", padx=(0, 24), pady=12)
            entries[key] = entry

        message = self._message_label(body)
        message.grid(row=1, column=0, sticky="new", pady=(18, 0))

        def execute() -> None:
            item_id = entries["item_id"].get().strip()
            if not item_id:
                self._set_message(message, "品目IDを入力してください。", True)
                return
            try:
                quantity = _to_positive_int(entries["quantity"].get(), action_name)
                stock_after = stock_function(
                    item_id,
                    quantity,
                    entries["operator"].get().strip(),
                    entries["note"].get().strip(),
                )
            except ValueError as exc:
                self._set_message(message, str(exc), True)
                return
            self._set_message(message, f"{action_name}しました。現在庫: {stock_after}")
            entries["quantity"].delete(0, tk.END)
            entries["note"].delete(0, tk.END)

        button_text = f"{action_name}実行"
        self._primary_button(form, button_text, execute).grid(
            row=len(fields), column=1, sticky="e", padx=(0, 24), pady=(10, 24)
        )
        for entry in entries.values():
            entry.bind("<Return>", lambda _event: execute())
        entries["item_id"].focus_set()

    def _format_item_details(self, item: object) -> str:
        fields = [
            ("品目ID", "item_id"),
            ("品名", "item_name"),
            ("型式", "model_number"),
            ("メーカー", "maker"),
            ("保管場所", "location"),
            ("現在庫", "current_stock"),
            ("最低在庫", "min_stock"),
            ("単位", "unit"),
            ("備考", "note"),
        ]
        return "\n".join(f"{label}: {_value(item, key, '-')}" for label, key in fields)

    def _admin_screen_guard(self, menu_key: str) -> bool:
        if not self._require_admin():
            return False
        self._set_active_menu(menu_key)
        self._clear_content()
        return True

    def show_item_delete_screen(self) -> None:
        if not self._admin_screen_guard("delete"):
            return
        self._screen_header("品目削除", "入出庫履歴がない品目だけ削除できます。削除前に二重確認します。")
        body = self._body_frame()
        body.grid_rowconfigure(2, weight=1)
        form = ctk.CTkFrame(body, fg_color="transparent")
        form.grid(row=0, column=0, sticky="ew")
        form.grid_columnconfigure(1, weight=1)
        self._label(form, "品目ID").grid(row=0, column=0, padx=(0, 14), sticky="w")
        item_entry = self._entry(form, "例: ITEM-0003")
        item_entry.grid(row=0, column=1, sticky="ew")
        message = self._message_label(body)
        message.grid(row=1, column=0, sticky="ew", pady=(16, 0))
        detail = ctk.CTkTextbox(body, height=260, corner_radius=18, border_width=1, border_color=COLOR_BORDER)
        detail.grid(row=2, column=0, sticky="nsew", pady=(20, 0))
        detail.configure(state="disabled")
        loaded_item: object | None = None

        def set_detail(text: str) -> None:
            detail.configure(state="normal")
            detail.delete("1.0", tk.END)
            detail.insert("1.0", text)
            detail.configure(state="disabled")

        def search() -> None:
            nonlocal loaded_item
            item_id = item_entry.get().strip()
            if not item_id:
                loaded_item = None
                set_detail("")
                self._set_message(message, "品目IDを入力してください。", True)
                return
            loaded_item = find_item_by_id(item_id)
            if loaded_item is None:
                set_detail("")
                self._set_message(message, "該当する品目が見つかりません。", True)
                return
            set_detail(self._format_item_details(loaded_item))
            self._set_message(message, "削除対象品目を表示しました。内容を確認してください。")

        def execute_delete() -> None:
            nonlocal loaded_item
            entered = item_entry.get().strip()
            if loaded_item is None or entered != str(_value(loaded_item, "item_id", "")):
                search()
                if loaded_item is None:
                    return
            item_id = str(_value(loaded_item, "item_id", ""))
            if not messagebox.askyesno("品目削除の確認", f"以下の品目を削除しますか？\n\n{self._format_item_details(loaded_item)}", parent=self):
                self._set_message(message, "品目削除を中止しました。", True)
                return
            confirmation = simpledialog.askstring("最終確認", f"誤削除防止のため、品目ID {item_id} を再入力してください。", parent=self)
            if confirmation != item_id:
                self._set_message(message, "確認入力が一致しないため、削除を中止しました。", True)
                return
            try:
                delete_item(item_id)
            except ValueError as exc:
                self._set_message(message, str(exc), True)
                return
            loaded_item = None
            set_detail("")
            item_entry.delete(0, tk.END)
            self._set_message(message, f"品目ID '{item_id}' を削除しました。")

        self._primary_button(form, "検索", search).grid(row=0, column=2, padx=(14, 0))
        self._secondary_button(form, "削除実行", execute_delete).grid(row=0, column=3, padx=(12, 0))
        item_entry.bind("<Return>", lambda _event: search())
        item_entry.focus_set()

    def show_csv_import_screen(self) -> None:
        if not self._admin_screen_guard("csv"):
            return
        self._screen_header("CSV品目マスタ取込", "CSVをプレビューし、エラーがない場合のみ自動バックアップ後に取り込みます。")
        body = self._body_frame()
        body.grid_rowconfigure(2, weight=1)
        form = ctk.CTkFrame(body, fg_color="transparent")
        form.grid(row=0, column=0, sticky="ew")
        form.grid_columnconfigure(1, weight=1)
        self._label(form, "CSVファイル").grid(row=0, column=0, padx=(0, 14), sticky="w")
        path_entry = self._entry(form, "imports/items_sample.csv")
        path_entry.grid(row=0, column=1, sticky="ew")
        result_box = ctk.CTkTextbox(body, height=320, corner_radius=18, border_width=1, border_color=COLOR_BORDER)
        result_box.grid(row=2, column=0, sticky="nsew", pady=(20, 0))
        result_box.configure(state="disabled")
        message = self._message_label(body)
        message.grid(row=1, column=0, sticky="ew", pady=(16, 0))
        last_preview: dict[str, object] | None = None

        button_frame = ctk.CTkFrame(form, fg_color="transparent")
        button_frame.grid(row=0, column=2, padx=(14, 0))

        def set_result(text: str) -> None:
            result_box.configure(state="normal")
            result_box.delete("1.0", tk.END)
            result_box.insert("1.0", text)
            result_box.configure(state="disabled")

        def choose_file() -> None:
            selected = filedialog.askopenfilename(parent=self, title="CSVファイルを選択", filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
            if selected:
                self._fill_entry(path_entry, selected)

        def preview() -> None:
            nonlocal last_preview
            import_button.configure(state="disabled")
            try:
                last_preview = preview_import_items_from_csv(path_entry.get().strip())
            except ValueError as exc:
                last_preview = None
                set_result(str(exc))
                self._set_message(message, "CSVプレビューでエラーが発生しました。", True)
                return
            errors = last_preview["errors"]
            lines = [
                f"使用文字コード: {last_preview['encoding']}",
                f"登録予定件数: {last_preview['registered_count']}",
                f"更新予定件数: {last_preview['updated_count']}",
                f"エラー件数: {last_preview['error_count']}",
                "",
                "エラー詳細:",
            ]
            lines.extend(errors if errors else ["なし"])
            set_result("\n".join(str(line) for line in lines))
            if int(last_preview["error_count"]) == 0:
                import_button.configure(state="normal")
                self._set_message(message, "エラーはありません。取込実行できます。")
            else:
                self._set_message(message, "エラーがあるため取込実行できません。", True)

        def execute_import() -> None:
            if last_preview is None or int(last_preview["error_count"]) != 0:
                self._set_message(message, "先にエラーなしのプレビューを実行してください。", True)
                return
            if not messagebox.askyesno("CSV取込の確認", "CSV品目マスタを取り込みます。実行直前に自動バックアップを作成しますか？", parent=self):
                self._set_message(message, "CSV取込を中止しました。", True)
                return
            try:
                backup_path = create_auto_backup("csv_import")
                result = import_items_from_csv(path_entry.get().strip())
            except ValueError as exc:
                self._set_message(message, str(exc), True)
                return
            set_result(
                "取込結果\n"
                f"使用文字コード: {result['encoding']}\n"
                f"登録件数: {result['registered_count']}\n"
                f"更新件数: {result['updated_count']}\n"
                f"エラー件数: {result['error_count']}\n"
                f"自動バックアップ: {backup_path if backup_path is not None else 'DB未作成のためなし'}"
            )
            import_button.configure(state="disabled")
            self._set_message(message, "CSV取込が完了しました。")

        self._secondary_button(button_frame, "参照", choose_file).grid(row=0, column=0, padx=(0, 8))
        self._secondary_button(button_frame, "プレビュー", preview).grid(row=0, column=1, padx=(0, 8))
        import_button = self._primary_button(button_frame, "取込実行", execute_import)
        import_button.grid(row=0, column=2)
        import_button.configure(state="disabled")

    def show_qr_generation_screen(self) -> None:
        if not self._admin_screen_guard("qr"):
            return
        self._screen_header("QRコード生成", "単品または全件のQRコードPNGを qr_codes フォルダへ保存します。")
        body = self._body_frame()
        body.grid_rowconfigure(2, weight=1)
        form = self._form_frame(body)
        form.grid(row=0, column=0, sticky="ew")
        self._label(form, "単品 品目ID").grid(row=0, column=0, sticky="w", padx=(24, 18), pady=12)
        item_entry = self._entry(form, "例: ITEM-0001")
        item_entry.grid(row=0, column=1, sticky="ew", padx=(0, 24), pady=12)
        message = self._message_label(body)
        message.grid(row=1, column=0, sticky="ew", pady=(16, 0))
        output_label = ctk.CTkLabel(body, text="保存先: -\n生成件数: -", font=FONT_BODY_BOLD, text_color=COLOR_TEXT, anchor="nw", justify="left")
        output_label.grid(row=2, column=0, sticky="new", pady=(20, 0))

        def generate_single() -> None:
            item_id = item_entry.get().strip()
            if not item_id:
                self._set_message(message, "品目IDを入力してください。", True)
                return
            item = get_item_for_qr(item_id)
            if item is None:
                self._set_message(message, "該当する品目が見つかりません。", True)
                return
            try:
                path = generate_item_qr_code(item)
            except ValueError as exc:
                self._set_message(message, str(exc), True)
                return
            output_label.configure(text=f"保存先: {path}\n生成件数: 1")
            self._set_message(message, "QRコードを生成しました。")

        def generate_all() -> None:
            try:
                result = generate_all_qr_codes(list_items())
            except ValueError as exc:
                self._set_message(message, str(exc), True)
                return
            output_label.configure(text=f"保存先: {QR_CODE_DIR}/\n生成件数: {result['count']}")
            self._set_message(message, "全件のQRコードを生成しました。")

        button_frame = ctk.CTkFrame(form, fg_color="transparent")
        button_frame.grid(row=1, column=1, sticky="e", padx=(0, 24), pady=(10, 24))
        self._primary_button(button_frame, "単品生成", generate_single).grid(row=0, column=0, padx=(0, 12))
        self._secondary_button(button_frame, "全件生成", generate_all).grid(row=0, column=1)

    def show_label_html_screen(self) -> None:
        if not self._admin_screen_guard("labels"):
            return
        self._screen_header("QRコード印刷用HTML生成", "labels/qr_labels_YYYYMMDD_HHMMSS.html を作成します。")
        body = self._body_frame()
        saved_path: Path | None = None
        message = self._message_label(body)
        message.grid(row=1, column=0, sticky="ew", pady=(16, 0))
        output = ctk.CTkLabel(body, text="保存先: -", font=FONT_BODY_BOLD, text_color=COLOR_TEXT, anchor="w")
        output.grid(row=2, column=0, sticky="ew", pady=(20, 0))

        def generate() -> None:
            nonlocal saved_path
            items = list_items()
            if not items:
                self._set_message(message, "品目が登録されていません。", True)
                return
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            try:
                saved_path = generate_qr_label_sheet(items, LABEL_DIR / f"qr_labels_{timestamp}.html")
            except ValueError as exc:
                self._set_message(message, str(exc), True)
                return
            output.configure(text=f"保存先: {saved_path}")
            open_button.configure(state="normal")
            self._set_message(message, "QRコード印刷用HTMLを生成しました。")

        def open_html() -> None:
            if saved_path is not None:
                webbrowser.open(saved_path.resolve().as_uri())

        buttons = ctk.CTkFrame(body, fg_color="transparent")
        buttons.grid(row=0, column=0, sticky="w")
        self._primary_button(buttons, "HTML生成", generate).grid(row=0, column=0, padx=(0, 12))
        open_button = self._secondary_button(buttons, "HTMLを開く", open_html)
        open_button.grid(row=0, column=1)
        open_button.configure(state="disabled")

    def show_db_backup_screen(self) -> None:
        if not self._admin_screen_guard("backup"):
            return
        self._screen_header("DBバックアップ", "現在のDBを backups フォルダへコピーします。")
        body = self._body_frame()
        message = self._message_label(body)
        message.grid(row=1, column=0, sticky="ew", pady=(16, 0))
        output = ctk.CTkLabel(body, text="バックアップファイル: -", font=FONT_BODY_BOLD, text_color=COLOR_TEXT, anchor="w")
        output.grid(row=2, column=0, sticky="ew", pady=(20, 0))

        def create_backup() -> None:
            try:
                path = backup_database()
            except FileNotFoundError as exc:
                self._set_message(message, str(exc), True)
                return
            output.configure(text=f"バックアップファイル: {path}")
            self._set_message(message, "DBバックアップを作成しました。")

        self._primary_button(body, "バックアップ作成", create_backup).grid(row=0, column=0, sticky="w")

    def show_db_restore_screen(self) -> None:
        if not self._admin_screen_guard("restore"):
            return
        self._screen_header("DB復旧", "backups フォルダのバックアップを選択し、RESTORE 確認後にDBを復旧します。")
        body = self._body_frame()
        body.grid_rowconfigure(1, weight=1)
        backups = list_backup_files()
        message = self._message_label(body)
        message.grid(row=2, column=0, sticky="ew", pady=(16, 0))
        table_holder = ctk.CTkFrame(body, fg_color="transparent")
        table_holder.grid(row=1, column=0, sticky="nsew", pady=(20, 0))
        table_holder.grid_columnconfigure(0, weight=1)
        table_holder.grid_rowconfigure(0, weight=1)
        selector = ctk.CTkFrame(body, fg_color="transparent")
        selector.grid(row=0, column=0, sticky="ew")
        self._label(selector, "復旧元番号").grid(row=0, column=0, padx=(0, 14), sticky="w")
        index_entry = self._entry(selector, "例: 1")
        index_entry.grid(row=0, column=1, sticky="ew")
        selector.grid_columnconfigure(1, weight=1)

        display_rows = [
            {"number": i, "filename": b["filename"], "updated_at": b["updated_at"].strftime("%Y-%m-%d %H:%M:%S"), "size": b["size"]}
            for i, b in enumerate(backups, start=1)
        ]
        self._render_table(table_holder, display_rows, [("番号", "number", 70), ("ファイル名", "filename", 260), ("更新日時", "updated_at", 160), ("サイズ", "size", 100)], "復旧可能な .db バックアップがありません。")

        def restore() -> None:
            if not backups:
                self._set_message(message, "復旧可能なバックアップがありません。", True)
                return
            try:
                index = int(index_entry.get().strip())
            except ValueError:
                self._set_message(message, "バックアップ番号は半角数字で入力してください。", True)
                return
            if index < 1 or index > len(backups):
                self._set_message(message, "選択された番号が一覧の範囲外です。", True)
                return
            selected = backups[index - 1]
            if not messagebox.askyesno("DB復旧の強い確認", f"現在のDBを上書きします。\n復旧元: {selected['filename']}\n続行しますか？", parent=self):
                self._set_message(message, "DB復旧を中止しました。", True)
                return
            confirmation = simpledialog.askstring("最終確認", "復旧するには RESTORE と入力してください。", parent=self)
            if confirmation != "RESTORE":
                self._set_message(message, "確認入力が一致しないため、DB復旧を中止しました。", True)
                return
            try:
                result = restore_database_from_backup(selected["path"])
            except (FileNotFoundError, ValueError) as exc:
                self._set_message(message, str(exc), True)
                return
            self._set_message(message, f"DBを復旧しました。復旧元: {result['source_path']} / 復旧前退避: {result['before_restore_path']}")

        self._primary_button(selector, "DB復旧実行", restore).grid(row=0, column=2, padx=(14, 0))
        self._secondary_button(selector, "品目一覧を再読み込み", self.show_list_screen).grid(row=0, column=3, padx=(12, 0))

    def show_low_stock_screen(self) -> None:
        self._set_active_menu("alert")
        self._clear_content()
        header = self._screen_header("最低在庫アラート", "在庫が少なくなった品目を確認できます。")
        body = self._body_frame()

        table_holder = ctk.CTkFrame(body, fg_color="transparent")
        table_holder.grid(row=0, column=0, sticky="nsew")
        table_holder.grid_columnconfigure(0, weight=1)
        table_holder.grid_rowconfigure(0, weight=1)

        def refresh() -> None:
            self._render_table(
                table_holder,
                list_low_stock_items(),
                [
                    ("品目ID", "item_id", 120),
                    ("品名", "item_name", 190),
                    ("保管場所", "location", 130),
                    ("現在庫", "current_stock", 85),
                    ("最低在庫", "min_stock", 85),
                    ("不足数量", "shortage_quantity", 95),
                    ("単位", "unit", 70),
                ],
                "最低在庫を下回っている品目はありません。",
            )

        self._secondary_button(header, "更新", refresh).grid(row=0, column=1, rowspan=2, padx=(16, 0))
        refresh()

    def _render_table(
        self,
        parent: ctk.CTkFrame,
        rows: Iterable[object],
        columns: list[tuple[str, str, int]],
        empty_message: str,
    ) -> None:
        for child in parent.winfo_children():
            child.destroy()

        row_list = list(rows)
        if not row_list:
            ctk.CTkLabel(
                parent,
                text=empty_message,
                font=FONT_BODY_BOLD,
                text_color=COLOR_MUTED,
            ).grid(row=0, column=0, sticky="nsew", pady=40)
            return

        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "Inventory.Treeview",
            background=COLOR_SURFACE,
            foreground=COLOR_TEXT,
            rowheight=38,
            fieldbackground=COLOR_SURFACE,
            borderwidth=0,
            font=FONT_SMALL,
        )
        style.configure(
            "Inventory.Treeview.Heading",
            background=COLOR_SECONDARY,
            foreground=COLOR_TEXT,
            relief="flat",
            font=FONT_BODY_BOLD,
        )
        style.map("Inventory.Treeview", background=[("selected", COLOR_SECONDARY_HOVER)])

        frame = ctk.CTkFrame(
            parent,
            fg_color=COLOR_SURFACE,
            corner_radius=20,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        frame.grid(row=0, column=0, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)

        tree = ttk.Treeview(
            frame,
            columns=[key for _label_text, key, _width in columns],
            show="headings",
            style="Inventory.Treeview",
        )
        for label_text, key, width in columns:
            tree.heading(key, text=label_text)
            tree.column(key, width=width, minwidth=70, anchor="w")

        for row in row_list:
            tree.insert("", tk.END, values=[_value(row, key, "") for _label_text, key, _width in columns])

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.grid(row=0, column=0, sticky="nsew", padx=(18, 0), pady=18)
        scrollbar.grid(row=0, column=1, sticky="ns", padx=(0, 18), pady=18)


def main() -> None:
    app = InventoryApp()
    app.mainloop()


if __name__ == "__main__":
    main()
