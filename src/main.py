"""Simple CUI for searching inventory items by item ID."""

from database import find_item_by_id, initialize_database


def main() -> None:
    initialize_database()
    print("=== 貯蔵品管理システム（CUI最小版）===")

    while True:
        item_id = input("品目IDまたはQRコードを入力してください (終了: q): ").strip()
        if item_id.lower() in {"q", "quit", "exit"}:
            print("終了します。")
            break

        if not item_id:
            print("入力が空です。再入力してください。")
            continue

        item = find_item_by_id(item_id)
        if item is None:
            print(f"入力値 '{item_id}' は見つかりませんでした。")
            continue

        print("--- 検索結果 ---")
        print(f"品目ID: {item['item_id']}")
        print(f"品目名: {item['item_name']}")
        print(f"型番: {item['model_number'] or '-'}")
        print(f"メーカー: {item['maker'] or '-'}")
        print(f"保管場所: {item['location'] or '-'}")
        print(f"単位: {item['unit'] or '-'}")
        print(f"最低在庫: {item['min_stock']}")
        print(f"現在庫: {item['current_stock']}")
        print(f"QRコード: {item['qr_code'] or '-'}")
        print(f"備考: {item['note'] or '-'}")


if __name__ == "__main__":
    main()
