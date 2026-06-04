# スキーマ（主要カラム）

## items

- `item_id` (TEXT, PK)
- `item_name` (TEXT, NOT NULL)
- `model_number` (TEXT)
- `maker` (TEXT)
- `location` (TEXT)
- `unit` (TEXT)
- `min_stock` (INTEGER, DEFAULT 0)
- `current_stock` (INTEGER, DEFAULT 0)
- `qr_code` (TEXT, UNIQUE)
- `note` (TEXT)

## transactions

- `transaction_id` (INTEGER, PK AUTOINCREMENT)
- `item_id` (TEXT, NOT NULL)
- `transaction_type` (TEXT, NOT NULL) ※ IN / OUT / ADJUST
- `quantity` (INTEGER, NOT NULL)
- `stock_after` (INTEGER, NOT NULL)
- `operator` (TEXT)
- `transaction_date` (TEXT, DEFAULT CURRENT_TIMESTAMP)
- `note` (TEXT)

## audit_logs

- `audit_log_id` (INTEGER, PK AUTOINCREMENT)
- `operation_date` (TEXT, DEFAULT CURRENT_TIMESTAMP)
- `operation_type` (TEXT, NOT NULL) ※ 入庫 / 出庫 / 棚卸修正 / 品目登録 / 品目編集 / 品目削除 / CSV取込 / CSV出力 / QRコード生成 / ラベル印刷 / DBバックアップ / DB復旧 / ログイン成功 / ログイン失敗 / ログアウト
- `target_item_id` (TEXT)
- `target_item_name` (TEXT)
- `quantity` (INTEGER)
- `message` (TEXT)
