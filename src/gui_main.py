"""CustomTkinter GUI entry point for the inventory system."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Iterable

import customtkinter as ctk

from database import (
    decrease_stock,
    find_item_by_id,
    increase_stock,
    initialize_database,
    list_items,
    list_low_stock_items,
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
        ]

        for row, (key, label, command) in enumerate(menu_items, start=1):
            button = ctk.CTkButton(
                menu,
                text=label,
                command=command,
                height=50,
                corner_radius=16,
                border_width=1,
                border_color=COLOR_BORDER,
                fg_color=COLOR_SURFACE,
                hover_color=COLOR_SECONDARY_HOVER,
                text_color=COLOR_TEXT,
                font=FONT_BODY_BOLD,
                anchor="w",
            )
            button.grid(row=row, column=0, sticky="ew", pady=7)
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
