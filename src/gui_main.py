"""CustomTkinter GUI entry point for the inventory system."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable, Iterable

import customtkinter as ctk

from database import (
    adjust_stock,
    create_auto_backup,
    create_item,
    decrease_stock,
    find_item_by_id,
    increase_stock,
    initialize_database,
    list_items,
    list_low_stock_items,
    update_item,
)

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
        menu = ctk.CTkFrame(self, width=250, fg_color=COLOR_BACKGROUND, corner_radius=0)
        menu.grid(row=0, column=0, sticky="ns", padx=(24, 18), pady=24)
        menu.grid_propagate(False)
        menu.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            menu,
            text="貯蔵品\n管理システム",
            font=FONT_TITLE,
            text_color=COLOR_TEXT,
            justify="left",
        ).grid(row=0, column=0, sticky="w", pady=(4, 30))

        menu_items: list[tuple[str, str, Callable[[], None]]] = [
            ("search", "品目検索", self.show_search_screen),
            ("list", "品目一覧", self.show_list_screen),
            ("in", "入庫", self.show_stock_in_screen),
            ("out", "出庫", self.show_stock_out_screen),
            ("alert", "最低在庫アラート", self.show_low_stock_screen),
            ("create", "品目登録", self.show_item_create_screen),
            ("edit", "品目編集", self.show_item_edit_screen),
            ("adjust", "棚卸修正", self.show_stock_adjust_screen),
        ]

        for row, (key, label, command) in enumerate(menu_items, start=1):
            button = ctk.CTkButton(
                menu,
                text=label,
                command=command,
                height=44,
                corner_radius=16,
                border_width=1,
                border_color=COLOR_BORDER,
                fg_color=COLOR_SURFACE,
                hover_color=COLOR_SECONDARY_HOVER,
                text_color=COLOR_TEXT,
                font=FONT_BODY_BOLD,
                anchor="w",
            )
            button.grid(row=row, column=0, sticky="ew", pady=5)
            self.menu_buttons[key] = button

        ctk.CTkLabel(
            menu,
            text="日常操作だけをまとめた\n現場向け画面です。",
            font=FONT_SMALL,
            text_color=COLOR_MUTED,
            justify="left",
        ).grid(row=99, column=0, sticky="sw", pady=(36, 0))
        menu.grid_rowconfigure(98, weight=1)

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
        self._set_active_menu("create")
        self._clear_content()
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
        self._set_active_menu("edit")
        self._clear_content()
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
        self._set_active_menu("adjust")
        self._clear_content()
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
