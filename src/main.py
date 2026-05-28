"""Menu-driven CUI for inventory search and stock operations."""

from database import (
    adjust_stock,
    backup_database,
    create_auto_backup,
    create_item,
    decrease_stock,
    delete_item,
    find_item_by_id,
    get_transactions_by_item_id,
    increase_stock,
    import_items_from_csv,
    initialize_database,
    list_backup_files,
    list_items,
    list_low_stock_items,
    restore_database_from_backup,
    update_item,
)


def prompt_item_id() -> str:
    return input("品目IDまたはQRコードを入力してください: ").strip()


def search_item() -> None:
    item_id = prompt_item_id()
    if not item_id:
        print("品目IDが空です。")
        return

    item = find_item_by_id(item_id)
    if item is None:
        print(f"品目ID '{item_id}' は見つかりませんでした。")
        return

    print("--- 検索結果 ---")
    print(f"品目ID: {item['item_id']}")
    print(f"品名: {item['item_name']}")
    print(f"型番: {item['model_number'] or '-'}")
    print(f"メーカー: {item['maker'] or '-'}")
    print(f"保管場所: {item['location'] or '-'}")
    print(f"単位: {item['unit'] or '-'}")
    print(f"最低在庫: {item['min_stock']}")
    print(f"現在庫: {item['current_stock']}")
    print(f"QRコード: {item['qr_code'] or '-'}")
    print(f"備考: {item['note'] or '-'}")


def show_item_list() -> None:
    rows = list_items()
    if not rows:
        print("品目が登録されていません。")
        return

    print("--- 品目一覧 ---")
    for row in rows:
        print(
            f"{row['item_id']} | {row['item_name']} | 型番:{row['model_number'] or '-'} "
            f"| メーカー:{row['maker'] or '-'} | 保管:{row['location'] or '-'} "
            f"| 単位:{row['unit'] or '-'} | 最低在庫:{row['min_stock']} | 現在庫:{row['current_stock']}"
        )


def show_low_stock_alert() -> None:
    rows = list_low_stock_items()
    if not rows:
        print("最低在庫を下回っている品目はありません。")
        return

    print("--- 最低在庫アラート ---")
    for row in rows:
        print(
            f"{row['item_id']} | {row['item_name']} | 型式:{row['model_number'] or '-'} "
            f"| メーカー:{row['maker'] or '-'} | 保管場所:{row['location'] or '-'} "
            f"| 現在庫:{row['current_stock']} | 最低在庫:{row['min_stock']} "
            f"| 不足数量:{row['shortage_quantity']} | 単位:{row['unit'] or '-'}"
        )


def register_item() -> None:
    print("--- 品目登録 ---")
    item_id = input("品目ID: ").strip()
    item_name = input("品名: ").strip()
    model_number = input("型式: ").strip()
    maker = input("メーカー: ").strip()
    location = input("保管場所: ").strip()
    unit = input("単位: ").strip()
    min_stock_text = input("最低在庫数: ").strip()
    initial_stock_text = input("初期在庫数: ").strip()
    note = input("備考: ").strip()

    try:
        min_stock = int(min_stock_text)
        initial_stock = int(initial_stock_text)
        create_item(
            item_id=item_id,
            item_name=item_name,
            model_number=model_number,
            maker=maker,
            location=location,
            unit=unit,
            min_stock=min_stock,
            initial_stock=initial_stock,
            note=note,
        )
        print("品目を登録しました。")
    except ValueError as error:
        print(f"エラー: {error}")


def edit_item() -> None:
    print("--- 品目編集 ---")
    item_id = input("編集する品目ID: ").strip()
    item = find_item_by_id(item_id)
    if item is None:
        print(f"品目ID '{item_id}' は見つかりませんでした。")
        return

    item_name = input(f"品名 [{item['item_name']}]: ").strip() or item["item_name"]
    model_number = (
        input(f"型式 [{item['model_number'] or ''}]: ").strip() or item["model_number"]
    )
    maker = input(f"メーカー [{item['maker'] or ''}]: ").strip() or item["maker"]
    location = (
        input(f"保管場所 [{item['location'] or ''}]: ").strip() or item["location"]
    )
    unit = input(f"単位 [{item['unit'] or ''}]: ").strip() or item["unit"]
    min_stock_raw = input(f"最低在庫数 [{item['min_stock']}]: ").strip()
    note = input(f"備考 [{item['note'] or ''}]: ").strip() or item["note"]

    try:
        min_stock = int(min_stock_raw) if min_stock_raw else int(item["min_stock"])
        update_item(
            item_id=item["item_id"],
            item_name=item_name,
            model_number=model_number,
            maker=maker,
            location=location,
            unit=unit,
            min_stock=min_stock,
            note=note,
        )
        print("品目を更新しました。")
    except ValueError as error:
        print(f"エラー: {error}")


def remove_item() -> None:
    print("--- 品目削除 ---")
    item_id = input("削除する品目ID: ").strip()
    item = find_item_by_id(item_id)
    if item is None:
        print(f"品目ID '{item_id}' は見つかりませんでした。")
        return

    confirmation = input(
        f"削除するには {item['item_id']} をもう一度入力してください: "
    ).strip()
    if confirmation != item["item_id"]:
        print("確認入力が一致しないため、削除を中止しました。")
        return

    try:
        delete_item(item["item_id"])
        print("品目を削除しました。")
    except ValueError as error:
        print(f"エラー: {error}")


def stock_in() -> None:
    item_id = prompt_item_id()
    qty_text = input("入庫数量を入力してください: ").strip()
    operator = input("作業者を入力してください（任意）: ").strip()
    note = input("備考を入力してください（任意）: ").strip()

    try:
        quantity = int(qty_text)
        stock_after = increase_stock(item_id, quantity, operator=operator, note=note)
        print(f"入庫を記録しました。処理後現在庫: {stock_after}")
    except ValueError as error:
        print(f"エラー: {error}")


def stock_out() -> None:
    item_id = prompt_item_id()
    qty_text = input("出庫数量を入力してください: ").strip()
    operator = input("作業者を入力してください（任意）: ").strip()
    note = input("備考を入力してください（任意）: ").strip()

    try:
        quantity = int(qty_text)
        stock_after = decrease_stock(item_id, quantity, operator=operator, note=note)
        print(f"出庫を記録しました。処理後現在庫: {stock_after}")
    except ValueError as error:
        print(f"エラー: {error}")


def stock_adjustment() -> None:
    print("--- 棚卸修正 ---")
    item_id = input("品目IDを入力してください: ").strip()
    if not item_id:
        print("品目IDが空です。")
        return

    item = find_item_by_id(item_id)
    if item is None:
        print(f"品目ID '{item_id}' は見つかりませんでした。")
        return

    actual_stock_text = input("実在庫数を入力してください: ").strip()
    operator = input("作業者を入力してください（任意）: ").strip()
    note = input("備考を入力してください（任意）: ").strip()

    try:
        actual_stock = int(actual_stock_text)
        if actual_stock < 0:
            raise ValueError("実在庫数は0以上を指定してください。")
    except ValueError as error:
        print(f"エラー: {error}")
        return

    current_stock = int(item["current_stock"])
    difference = actual_stock - current_stock

    print("--- 棚卸修正内容確認 ---")
    print(f"品目ID: {item['item_id']}")
    print(f"品名: {item['item_name']}")
    print(f"現在庫: {current_stock}")
    print(f"実在庫: {actual_stock}")
    print(f"差異: {difference}")

    confirmation = input("この内容で棚卸修正しますか？ y/n: ").strip().lower()
    if confirmation != "y":
        print("棚卸修正を中止しました。")
        return

    backup_path = create_auto_backup("stock_adjust")
    if backup_path is not None:
        print("自動バックアップを作成しました:")
        print(backup_path)

    try:
        stock_after = adjust_stock(
            item["item_id"], actual_stock, operator=operator, note=note
        )
        print(f"棚卸修正を記録しました。処理後現在庫: {stock_after}")
    except ValueError as error:
        print(f"エラー: {error}")


def show_transactions() -> None:
    item_id = prompt_item_id()
    if not item_id:
        print("品目IDが空です。")
        return

    item = find_item_by_id(item_id)
    if item is None:
        print(f"品目ID '{item_id}' は見つかりませんでした。")
        return

    rows = get_transactions_by_item_id(item["item_id"])
    if not rows:
        print("履歴がありません。")
        return

    print("--- 入出庫・棚卸履歴（新しい順）---")
    for row in rows:
        print(
            f"[{row['transaction_date']}] {row['transaction_type']} 数量:{row['quantity']} "
            f"処理後在庫:{row['stock_after']} 作業者:{row['operator'] or '-'} 備考:{row['note'] or '-'}"
        )


def import_item_master_csv() -> None:
    print("--- CSV品目マスタ取込 ---")
    csv_path = input("CSVファイルパスを入力してください: ").strip()
    if not csv_path:
        print("CSVファイルパスが空です。")
        return

    backup_path = create_auto_backup("csv_import")
    if backup_path is not None:
        print("自動バックアップを作成しました:")
        print(backup_path)

    try:
        result = import_items_from_csv(csv_path)
    except ValueError as error:
        print(f"エラー: {error}")
        return

    print("CSV取込結果:")
    print(f"使用文字コード: {result['encoding']}")
    print(f"登録件数: {result['registered_count']}")
    print(f"更新件数: {result['updated_count']}")
    print(f"エラー件数: {result['error_count']}")

    errors = result["errors"]
    if errors:
        print("--- エラー詳細 ---")
        for message in errors:
            print(message)


def create_database_backup() -> None:
    print("--- DBバックアップ ---")
    try:
        backup_path = backup_database()
    except FileNotFoundError as error:
        print(f"エラー: {error}")
        return

    print("バックアップを作成しました:")
    print(backup_path)


def restore_database_menu() -> None:
    print("--- DB復旧 ---")
    backup_files = list_backup_files()
    if not backup_files:
        print("backups フォルダに復旧可能な .db バックアップがありません。")
        return

    for index, backup_file in enumerate(backup_files, start=1):
        updated_at = backup_file["updated_at"].strftime("%Y-%m-%d %H:%M:%S")
        size = backup_file["size"]
        print(
            f"{index}. {backup_file['filename']} | 更新日時:{updated_at} | サイズ:{size} bytes"
        )

    selected_text = input("復旧するバックアップ番号を選択してください: ").strip()
    try:
        selected_index = int(selected_text)
    except ValueError:
        print("エラー: バックアップ番号は数値で入力してください。")
        return

    if selected_index < 1 or selected_index > len(backup_files):
        print("エラー: 選択されたバックアップ番号が一覧の範囲外です。")
        return

    selected_backup = backup_files[selected_index - 1]
    print("この操作は現在のDBを上書きします。")
    confirmation = input("復旧するには RESTORE と入力してください: ").strip()
    if confirmation != "RESTORE":
        print("確認入力が一致しないため、DB復旧を中止しました。")
        return

    try:
        result = restore_database_from_backup(selected_backup["path"])
    except (FileNotFoundError, ValueError) as error:
        print(f"エラー: {error}")
        return

    print("DBを復旧しました:")
    print(f"復旧元: {result['source_path']}")
    print(f"復旧前退避: {result['before_restore_path']}")


def main() -> None:
    initialize_database()
    print("=== Inventory CUI Menu ===")

    while True:
        print("\n1. 品目検索")
        print("2. 入庫")
        print("3. 出庫")
        print("4. 入出庫履歴表示")
        print("5. 品目一覧")
        print("6. 品目登録")
        print("7. 品目編集")
        print("8. 品目削除")
        print("9. 最低在庫アラート")
        print("10. CSV品目マスタ取込")
        print("11. 棚卸修正")
        print("12. DBバックアップ")
        print("13. DB復旧")
        print("q. 終了")
        choice = input("メニューを選択してください: ").strip().lower()

        if choice in {"q", "quit", "exit"}:
            print("終了します。")
            break
        if choice == "1":
            search_item()
        elif choice == "2":
            stock_in()
        elif choice == "3":
            stock_out()
        elif choice == "4":
            show_transactions()
        elif choice == "5":
            show_item_list()
        elif choice == "6":
            register_item()
        elif choice == "7":
            edit_item()
        elif choice == "8":
            remove_item()
        elif choice == "9":
            show_low_stock_alert()
        elif choice == "10":
            import_item_master_csv()
        elif choice == "11":
            stock_adjustment()
        elif choice == "12":
            create_database_backup()
        elif choice == "13":
            restore_database_menu()
        else:
            print("無効な選択です。1-13 または q を入力してください。")


if __name__ == "__main__":
    main()
