"""Simple CUI for searching inventory items by item ID."""

from database import find_item_by_id, initialize_database


def main() -> None:
    initialize_database()
    print("=== Inventory Item Search ===")

    while True:
        item_id = input("品目IDを入力してください (終了: q): ").strip()
        if item_id.lower() in {"q", "quit", "exit"}:
            print("終了します。")
            break

        if not item_id:
            print("品目IDが空です。再入力してください。")
            continue

        item = find_item_by_id(item_id)
        if item is None:
            print(f"品目ID '{item_id}' は見つかりませんでした。")
            continue

        print("--- 検索結果 ---")
        print(f"ID: {item['id']}")
        print(f"名称: {item['name']}")
        print(f"説明: {item['description'] or '-'}")
        print(f"在庫数: {item['quantity']}")
        print(f"保管場所: {item['location'] or '-'}")
        print(f"更新日時: {item['updated_at']}")


if __name__ == "__main__":
    main()
