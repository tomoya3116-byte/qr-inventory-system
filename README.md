# qr-inventory-system

QR code based inventory management system using Python and SQLite.

## 概要

業務用の貯蔵品管理を想定した、CUIベースの在庫管理システムです。
品目IDまたはQRコードを入力して検索し、入庫・出庫・履歴確認に加えて、品目マスタの一覧・登録・編集・削除を行えます。

## セットアップ

1. Python 3.10 以上をインストール
2. リポジトリのルートで以下を実行

```bash
python3 src/main.py
```

初回実行時に `data/inventory.db` が自動作成され、テーブル初期化とサンプルデータ投入が行われます。

## スキーマ（主要カラム）

### items

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

### transactions

- `transaction_id` (INTEGER, PK AUTOINCREMENT)
- `item_id` (TEXT, NOT NULL)
- `transaction_type` (TEXT, NOT NULL) ※ IN / OUT
- `quantity` (INTEGER, NOT NULL)
- `stock_after` (INTEGER, NOT NULL)
- `operator` (TEXT)
- `transaction_date` (TEXT, DEFAULT CURRENT_TIMESTAMP)
- `note` (TEXT)

## サンプルデータ

- `ITEM-0001` / ベアリング / `ABC-123` / メーカーA / 棚A-01 / 個 / 最低在庫2 / 現在庫10 / `qr_code=ITEM-0001`
- `ITEM-0002` / Vベルト / `VB-456` / メーカーB / 棚B-02 / 本 / 最低在庫1 / 現在庫5 / `qr_code=ITEM-0002`

## 使い方

起動後、以下のメニューが表示されます。

1. 品目検索
2. 入庫
3. 出庫
4. 入出庫履歴表示
5. 品目一覧
6. 品目登録
7. 品目編集
8. 品目削除
9. 最低在庫アラート
q. 終了

## 動作確認例

`python3 src/main.py` 実行後、以下を順に入力して確認できます。

1. **品目検索**: `1` → `ITEM-0001`
   - ベアリング（`item_name`）が表示される
2. **入庫**: `2` → `ITEM-0001` → `3`（任意で作業者・備考入力）
   - `current_stock` が 10 → 13 に増える
3. **出庫**: `3` → `ITEM-0001` → `4`（任意で作業者・備考入力）
   - `current_stock` が 13 → 9 に減る
4. **履歴表示**: `4` → `ITEM-0001`
   - `IN` と `OUT` の履歴が表示される
5. **在庫不足確認**: `3` → `ITEM-0001` → `1000`
   - 在庫不足エラーが表示され、在庫はマイナスにならない

## 補足

- すべてのファイルは UTF-8 で保存されています。
- `find_item_by_id` は `item_id` または `qr_code` で検索できます。


### 品目マスタ管理

- **品目一覧**: 登録済み品目を全件表示します。
- **品目登録**: 品目ID / 品名 / 型式 / メーカー / 保管場所 / 単位 / 最低在庫数 / 初期在庫数 / 備考 を入力して新規登録します。
  - 品目IDとQRコード文字列は同じ値で登録されます。
- **品目編集**: 品名・型式・メーカー・保管場所・単位・最低在庫数・備考を更新できます。
  - 空欄で入力した項目は既存値を維持します。
- **品目削除**: 確認のため `削除するには item_id をもう一度入力してください` が表示されます。
  - 入出庫履歴が存在する品目は削除できません。


### 最低在庫アラート

- メニュー `9` を選択すると、`現在庫 <= 最低在庫` の品目が表示されます。
- 表示項目: 品目ID / 品名 / 型式 / メーカー / 保管場所 / 現在庫 / 最低在庫 / 不足数量 / 単位
- 不足数量は `最低在庫 - 現在庫` で計算し、現在庫が最低在庫と同じ場合は `0` です。
- 該当品目がない場合は `最低在庫を下回っている品目はありません。` と表示されます。

#### 最低在庫アラートの動作確認例

1. `python3 src/main.py` を起動
2. `3`（出庫）→ `ITEM-0001` → `8` を入力して、`ITEM-0001` の現在庫を `10` から `2` 以下にする
3. `9`（最低在庫アラート）を選択
4. `ITEM-0001` がアラート一覧に表示されることを確認
