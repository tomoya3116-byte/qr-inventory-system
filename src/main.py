"""Menu-driven CUI for inventory search and stock operations."""

from database import (
    decrease_stock,
    find_item_by_id,
    get_transactions_by_item_id,
    increase_stock,
    initialize_database,
)


def prompt_item_id() -> str:
    return input("品目IDを入力してください: ").strip()


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
    print(f"ID: {item['id']}")
    print(f"名称: {item['name']}")
    print(f"説明: {item['description'] or '-'}")
    print(f"在庫数: {item['quantity']}")
    print(f"保管場所: {item['location'] or '-'}")
    print(f"更新日時: {item['updated_at']}")


def stock_in() -> None:
    item_id = prompt_item_id()
    qty_text = input("入庫数量を入力してください: ").strip()
    operator = input("作業者を入力してください（任意）: ").strip()
    note = input("備考を入力してください（任意）: ").strip()

    try:
        quantity = int(qty_text)
        stock_after = increase_stock(item_id, quantity, operator=operator, note=note)
        print(f"入庫を記録しました。処理後在庫: {stock_after}")
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
        print(f"出庫を記録しました。処理後在庫: {stock_after}")
    except ValueError as error:
        print(f"エラー: {error}")


def show_transactions() -> None:
    item_id = prompt_item_id()
    if not item_id:
        print("品目IDが空です。")
        return

    rows = get_transactions_by_item_id(item_id)
    if not rows:
        print("履歴がありません。")
        return

    print("--- 入出庫履歴（新しい順）---")
    for row in rows:
        print(
            f"[{row['created_at']}] {row['transaction_type']} 数量:{row['quantity']} "
            f"処理後在庫:{row['stock_after']} 作業者:{row['operator'] or '-'} 備考:{row['note'] or '-'}"
        )


def main() -> None:
    initialize_database()
    print("=== Inventory CUI Menu ===")

    while True:
        print("\n1. 品目検索")
        print("2. 入庫")
        print("3. 出庫")
        print("4. 入出庫履歴表示")
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
        else:
            print("無効な選択です。1-4 または q を入力してください。")


if __name__ == "__main__":
    main()
