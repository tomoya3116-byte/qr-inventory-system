# qr-inventory-system

QR code based inventory management system using Python and SQLite.

## 概要

業務用の貯蔵品管理を想定した、CUIベースの在庫管理システムです。
品目IDまたはQRコードを入力して検索し、入庫・出庫・棚卸修正・履歴確認に加えて、品目マスタの一覧・登録・編集・削除を行えます。

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
- `transaction_type` (TEXT, NOT NULL) ※ IN / OUT / ADJUST
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
10. CSV品目マスタ取込
11. 棚卸修正
12. DBバックアップ
q. 終了

## 動作確認例

`python3 src/main.py` 実行後、以下を順に入力して確認できます。

1. **品目検索**: `1` → `ITEM-0001`
   - ベアリング（`item_name`）が表示される
2. **入庫**: `2` → `ITEM-0001` → `3`（任意で作業者・備考入力）
   - `current_stock` が 10 → 13 に増える
3. **出庫**: `3` → `ITEM-0001` → `4`（任意で作業者・備考入力）
   - `current_stock` が 13 → 9 に減る
4. **棚卸修正**: `11` → `ITEM-0001` → `11` → 作業者・備考入力 → 確認画面で `y`
   - `current_stock` が実在庫数 `11` に更新され、差異数量の `ADJUST` 履歴が記録される
5. **履歴表示**: `4` → `ITEM-0001`
   - `IN` / `OUT` / `ADJUST` の履歴が表示される
6. **DBバックアップ**: `12`
   - `backups/inventory_YYYYMMDD_HHMMSS.db` が作成される
7. **在庫不足確認**: `3` → `ITEM-0001` → `1000`
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


### 棚卸修正

- メニュー `11` を選択すると、実在庫数を入力してシステム在庫を修正できます。
- 入力項目: 品目ID / 実在庫数 / 作業者 / 備考
- 修正前に、品目ID / 品名 / 現在庫 / 実在庫 / 差異 が表示されます。
- `この内容で棚卸修正しますか？ y/n` で `y` を入力した場合のみ、`items.current_stock` が実在庫数に更新されます。
- 棚卸修正は `transactions.transaction_type = ADJUST` として履歴に保存されます。
- `transactions.quantity` には差異数量が保存されます。例: 現在庫 `13` を実在庫 `11` に修正した場合、`quantity = -2` です。
- `transactions.stock_after` には修正後在庫（実在庫数）が保存され、作業者と備考も履歴に残ります。

#### 棚卸修正の動作確認例

1. `python3 src/main.py` を実行
2. メニュー `11`（棚卸修正）を選択
3. 品目IDに `ITEM-0001`、実在庫数に `11`、必要に応じて作業者・備考を入力
4. 確認画面で差異を確認し、`y` を入力
5. メニュー `4`（入出庫履歴表示）で `ITEM-0001` を指定し、`ADJUST` 履歴が表示されることを確認

### DBバックアップ

- メニュー `12` を選択すると、`data/inventory.db` を任意のタイミングでバックアップできます。
- バックアップファイルは `backups/inventory_YYYYMMDD_HHMMSS.db` という名前で作成されます。
- CSV品目マスタ取込前にバックアップすることを推奨します。
- 棚卸修正前にバックアップすることを推奨します。
- `backups/*.db` はGit管理しません。バックアップDBはローカルで保管してください。

#### DBバックアップの使い方

1. `python3 src/main.py` を実行
2. メニュー `12`（DBバックアップ）を選択
3. `バックアップを作成しました:` の下に表示されたバックアップファイルパスを確認
4. `backups` フォルダに `inventory_YYYYMMDD_HHMMSS.db` が作成されていることを確認
5. `git status --short` でバックアップDBがGit管理対象になっていないことを確認


### CSV品目マスタ取込

- CSV取込は、同一 `item_id` が既存にある場合はCSV内容で**上書き更新**します。
- `current_stock` もCSVの値で上書きされます。
- CSV取込はマスタ初期登録・棚卸後の反映向けです。通常の入出庫は入庫/出庫メニューを使ってください。

#### CSVテンプレート

- サンプル: `imports/items_sample.csv`
- ヘッダー（列順）:

```csv
item_id,item_name,model_number,maker,location,unit,min_stock,current_stock,qr_code,note
```

#### CSV取込方法

1. `python3 src/main.py` を実行
2. メニュー `10`（CSV品目マスタ取込）を選択
3. 例: `imports/items_sample.csv` を入力
4. 取込結果（登録件数/更新件数/エラー件数）を確認

#### ExcelでCSV保存する場合の注意

- Excelで作成したCSVは、環境や保存方法によって Shift-JIS/CP932 になる場合があります。
- 本アプリは `utf-8-sig`, `utf-8`, `cp932`, `shift_jis` のCSV読込に対応しています。
- 文字化けする場合は、Excelの保存形式で **CSV UTF-8** を選択して保存してください。

#### CSV取込後の確認方法

1. メニュー `5`（品目一覧）で `ITEM-0003` など取込品目が表示されることを確認
2. メニュー `1`（品目検索）で `ITEM-0003` を検索して詳細が表示されることを確認

#### 動作確認例（CSV取込）

1. `python3 src/main.py` を実行
2. メニュー `10` を選択
3. `imports/items_sample.csv` を指定
4. メニュー `5` の品目一覧で `ITEM-0003` が追加されていることを確認
5. メニュー `1` で `ITEM-0003` を検索できることを確認
