# qr-inventory-system

QR code based inventory management system using Python and SQLite.

## 概要

業務用の貯蔵品管理を想定した、CUIベースの在庫管理システムです。
品目IDまたはQRコードを入力して検索し、入庫・出庫・棚卸修正・履歴確認に加えて、品目マスタの一覧・登録・編集・削除を行えます。

## セットアップ

1. Python 3.10 以上をインストール
2. リポジトリのルートで必要ライブラリをインストール

```bash
pip install -r requirements.txt
```

3. リポジトリのルートでCUI版を起動

```bash
python src/main.py
```

4. GUI版を使う場合は、リポジトリのルートで以下を実行

```bash
python src/gui_main.py
```

初回実行時に `data/inventory.db` が自動作成され、テーブル初期化とサンプルデータ投入が行われます。
既存のCUI版は引き続き `python src/main.py` で利用できます。


## GUI版の使い方

CustomTkinterを使ったGUI版は、現場作業者が日常操作を直感的に行えるようにした画面です。
左側のメニューから機能を選び、右側の画面で作業します。

```bash
python src/gui_main.py
```

GUI版 Phase 1 で利用できる機能は以下です。

- 品目検索: 品目IDまたはQRコードで品目情報を確認
- 品目一覧: 全品目の一覧表示と更新
- 入庫: 品目ID・数量・作業者・備考を入力して在庫を追加
- 出庫: 在庫不足を確認しながら在庫を減算
- 最低在庫アラート: `current_stock <= min_stock` の品目を一覧表示

### GUI版の動作確認例

1. `pip install -r requirements.txt` を実行
2. `python src/gui_main.py` を実行
3. 品目検索で `ITEM-0001` を検索
4. 品目一覧を表示
5. `ITEM-0001` を数量 `1` で入庫
6. `ITEM-0001` を数量 `1` で出庫
7. 最低在庫アラートを表示

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
12. QRコード生成（単品）
13. QRコード生成（全件）
14. DBバックアップ
15. DB復旧
16. QRコード印刷用HTML生成
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
6. **QRコード生成（単品）**: `12` → `ITEM-0001`
   - `qr_codes/ITEM-0001.png` が作成される
7. **QRコード生成（全件）**: `13`
   - 全品目分のPNGが `qr_codes/` に作成される
8. **DBバックアップ**: `14`
   - `backups/inventory_YYYYMMDD_HHMMSS.db` が作成される
9. **QRコード印刷用HTML生成**: `16`
   - `labels/qr_labels_YYYYMMDD_HHMMSS.html` が作成される
10. **在庫不足確認**: `3` → `ITEM-0001` → `1000`
   - 在庫不足エラーが表示され、在庫はマイナスにならない


## ライセンス

このプロジェクトは MIT License のもとで公開されています。詳細は `LICENSE` を参照してください。

## 補足

- すべてのファイルは UTF-8 で保存されています。
- DBファイル・バックアップDB・一時CSV・生成済みQRコードPNG・生成済みラベルHTMLはGit管理しません。
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
- 棚卸修正の確定直前に、自動バックアップ `backups/auto_stock_adjust_YYYYMMDD_HHMMSS.db` が作成されます。

#### 棚卸修正の動作確認例

1. `python3 src/main.py` を実行
2. メニュー `11`（棚卸修正）を選択
3. 品目IDに `ITEM-0001`、実在庫数に `11`、必要に応じて作業者・備考を入力
4. 確認画面で差異を確認し、`y` を入力
5. `自動バックアップを作成しました:` の下に表示された `backups/auto_stock_adjust_YYYYMMDD_HHMMSS.db` を確認
6. メニュー `4`（入出庫履歴表示）で `ITEM-0001` を指定し、`ADJUST` 履歴が表示されることを確認

### QRコード生成

- メニュー `12`（QRコード生成（単品））またはメニュー `13`（QRコード生成（全件））で、品目ごとのQRコード画像をPNG形式で生成できます。
- 生成先はリポジトリ直下の `qr_codes/` フォルダです。
- QRコードの中身は基本的に `items.qr_code` カラムの値です。`qr_code` が空欄の場合は `items.item_id` を使用します。
- 現時点ではQRコードに埋め込む内容は品目ID文字列またはQRコード文字列のみです。
- `qr_codes/*.png` はGit管理しません。生成したPNGはローカル環境で保管してください。

#### QRコード生成（単品）の使い方

1. `python3 src/main.py` を実行
2. メニュー `12`（QRコード生成（単品））を選択
3. 品目IDに `ITEM-0001` を入力
4. `QRコードを生成しました:` の下に表示された保存先を確認
5. `qr_codes/ITEM-0001.png` が作成されていることを確認

#### QRコード生成（全件）の使い方

1. `python3 src/main.py` を実行
2. メニュー `13`（QRコード生成（全件））を選択
3. `全品目のQRコードを生成しました。` と生成件数を確認
4. 全品目分のPNGが `qr_codes/` に作成されていることを確認

#### QRコード生成の動作確認例

1. `python3 src/main.py` を実行
2. メニュー `12`（QRコード生成（単品））で `ITEM-0001` を指定
3. `qr_codes/ITEM-0001.png` が作成されることを確認
4. メニュー `13`（QRコード生成（全件））を実行
5. 全品目分のPNGが `qr_codes/` に作成されることを確認
6. `git status --short` に `qr_codes/*.png` が表示されないことを確認

### QRコード印刷用HTML生成

- メニュー `16`（QRコード印刷用HTML生成）を選択すると、登録済み全品目のQRコードをA4縦向きで印刷しやすいHTMLに一覧配置します。
- 出力先はリポジトリ直下の `labels/` フォルダです。ファイル名は `qr_labels_YYYYMMDD_HHMMSS.html` 形式です。
- 各ラベルにはQRコード画像、品目ID、品名、型式、保管場所が表示されます。
- HTMLはブラウザで開いて印刷してください。3列グリッド、枠線付きラベル、印刷用CSSを含んでいます。
- 対象品目のQRコード画像 `qr_codes/{item_id}.png` が未生成の場合は、HTML生成時に自動生成されます。
- `labels/*.html` はGit管理しません。生成した印刷用HTMLはローカル環境で保管してください。

#### QRコード印刷用HTML生成の使い方

1. `python3 src/main.py` を実行
2. メニュー `16`（QRコード印刷用HTML生成）を選択
3. `QRコード印刷用HTMLを生成しました:` の下に表示された保存先を確認
4. `labels` フォルダに `qr_labels_YYYYMMDD_HHMMSS.html` が作成されていることを確認
5. HTMLをブラウザで開き、QRコード・品目ID・品名・型式・保管場所が表示されることを確認
6. ブラウザの印刷機能でA4縦向き印刷プレビューを確認

#### QRコード印刷用HTML生成の動作確認例

1. `python3 src/main.py` を実行
2. メニュー `16`（QRコード印刷用HTML生成）を選択
3. `labels` フォルダに `qr_labels_YYYYMMDD_HHMMSS.html` が作成されることを確認
4. HTMLをブラウザで開き、QRコード・品目ID・品名・型式・保管場所が表示されることを確認
5. 事前にQRコード画像が未生成だった品目は、`qr_codes/{item_id}.png` が自動生成されることを確認
6. `git status --short` に `labels/*.html` が表示されないことを確認

### DBバックアップ

- メニュー `14` を選択すると、`data/inventory.db` を任意のタイミングでバックアップできます。
- バックアップファイルは `backups/inventory_YYYYMMDD_HHMMSS.db` という名前で作成されます。
- DBバックアップは、ユーザーがメニューから任意に作成する手動バックアップです。
- 危険な操作の直前には、別途「自動バックアップ」がシステムにより作成されます。
- `backups/*.db` はGit管理しません。バックアップDBはローカルで保管してください。

#### DBバックアップの使い方

1. `python3 src/main.py` を実行
2. メニュー `14`（DBバックアップ）を選択
3. `バックアップを作成しました:` の下に表示されたバックアップファイルパスを確認
4. `backups` フォルダに `inventory_YYYYMMDD_HHMMSS.db` が作成されていることを確認
5. `git status --short` でバックアップDBがGit管理対象になっていないことを確認


### DB復旧

- メニュー `15` を選択すると、`backups` フォルダ内の `.db` バックアップ一覧から復旧元を選べます。
- 復旧操作は `data/inventory.db` を選択したバックアップDBで上書きします。
- 復旧前に、現在の `data/inventory.db` は `backups/auto_before_restore_YYYYMMDD_HHMMSS.db` として自動バックアップされます。
- CSV品目マスタ取込ミス、棚卸修正ミス、誤操作があった場合に、正常時点のバックアップへ戻す用途で使用します。
- 誤操作防止のため、復旧実行前に確認文字列 `RESTORE` の入力が必要です。
- 復旧後は、メニュー `5`（品目一覧）やメニュー `1`（品目検索）で内容が想定どおり戻っていることを確認してください。

#### DB復旧の使い方

1. `python3 src/main.py` を実行
2. メニュー `15`（DB復旧）を選択
3. 表示されたバックアップ一覧から復旧する番号を入力
4. `この操作は現在のDBを上書きします。` の表示を確認
5. 復旧する場合のみ `RESTORE` と入力
6. `DBを復旧しました:` の下に表示された復旧元と復旧前退避ファイルを確認
7. メニュー `5`（品目一覧）またはメニュー `1`（品目検索）で復旧後のデータを確認

#### DB復旧の動作確認例

1. `python3 src/main.py` を実行
2. メニュー `14`（DBバックアップ）でバックアップを作成
3. メニュー `6`（品目登録）でテスト品目 `ITEM-9999` を登録
4. メニュー `5`（品目一覧）で `ITEM-9999` があることを確認
5. メニュー `15`（DB復旧）で直前のバックアップから復旧
6. メニュー `5`（品目一覧）で `ITEM-9999` が消えていることを確認
7. `backups` フォルダに `auto_before_restore_YYYYMMDD_HHMMSS.db` が作成されていることを確認


### 自動バックアップ

- 自動バックアップは、CSV品目マスタ取込・棚卸修正・DB復旧など、在庫データを大きく変更する操作の直前にシステムが自動作成するバックアップです。
- 手動のDBバックアップ（メニュー `14`）はユーザーが任意のタイミングで作成するバックアップ、自動バックアップは危険な操作の直前にシステムが作成するバックアップとして役割を分けています。
- CSV品目マスタ取込前には `backups/auto_csv_import_YYYYMMDD_HHMMSS.db` が作成されます。
- 棚卸修正前には `backups/auto_stock_adjust_YYYYMMDD_HHMMSS.db` が作成されます。
- DB復旧前には `backups/auto_before_restore_YYYYMMDD_HHMMSS.db` が作成されます。
- 自動バックアップファイルは `backups` フォルダに `auto_` から始まるDBファイルとして保存されます。
- `backups/*.db`, `backups/*.sqlite`, `backups/*.sqlite3` はGit管理しません。バックアップDBはローカル環境で保管してください。

#### 自動バックアップの動作確認例

1. `python3 src/main.py` を実行
2. メニュー `10` でCSV品目マスタ取込を実行
3. `backups` に `auto_csv_import_YYYYMMDD_HHMMSS.db` が作成されることを確認
4. メニュー `11` で棚卸修正を実行
5. `backups` に `auto_stock_adjust_YYYYMMDD_HHMMSS.db` が作成されることを確認
6. メニュー `15` でDB復旧を実行
7. `backups` に `auto_before_restore_YYYYMMDD_HHMMSS.db` が作成されることを確認
8. `git status --short` で自動バックアップDBがGit管理対象になっていないことを確認


### CSV品目マスタ取込

- CSV取込は、同一 `item_id` が既存にある場合はCSV内容で**上書き更新**します。
- `current_stock` もCSVの値で上書きされます。
- CSV取込はマスタ初期登録・棚卸後の反映向けです。通常の入出庫は入庫/出庫メニューを使ってください。
- CSV取込の直前に、自動バックアップ `backups/auto_csv_import_YYYYMMDD_HHMMSS.db` が作成されます。

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
4. `CSV取込プレビュー` で、使用文字コード・登録予定件数・更新予定件数・エラー件数を確認
5. エラーがある場合は取込が実行されないため、表示された行番号と内容をもとにCSVを修正
6. エラーがない場合のみ、確認プロンプトに `IMPORT` と入力して取込を実行
7. `自動バックアップを作成しました:` の下に表示された `backups/auto_csv_import_YYYYMMDD_HHMMSS.db` を確認
8. 取込結果（登録件数/更新件数/エラー件数）を確認

#### CSV取込プレビュー

CSV品目マスタ取込では、DBを更新する前にCSV内容を検証し、既存DBの `item_id` と照合して登録予定・更新予定・エラー行を表示します。プレビュー時点ではDBを更新しません。

```text
CSV取込プレビュー:
使用文字コード: cp932
登録予定件数: 3
更新予定件数: 17
エラー件数: 0

取込を実行するには IMPORT と入力してください:
```

エラーがある場合は、以下のようにエラー詳細が表示され、取込は実行できません。

```text
CSVにエラーがあります。取込は実行できません。
3行目: item_id が空です
8行目: current_stock が整数ではありません
```

取込実行直前には、自動バックアップ `backups/auto_csv_import_YYYYMMDD_HHMMSS.db` が作成されます。

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
