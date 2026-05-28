# qr-inventory-system

QR code based inventory management system using Python and SQLite.

## 概要

初期段階ではQRリーダーを利用せず、CUIで品目IDを手入力してSQLiteから品目情報を検索します。
将来的にUSB-HID型QRリーダー入力へ置き換えることを想定した構成です。

## セットアップ手順（Windows想定）

1. Python 3.10 以上をインストール
2. リポジトリのルートへ移動
3. 仮想環境を作成

```powershell
python -m venv .venv
```

4. 仮想環境を有効化

```powershell
.\.venv\Scripts\Activate.ps1
```

5. 依存関係をインストール

```powershell
pip install -r requirements.txt
```

## 実行方法

```powershell
python src/main.py
```

## 動作確認方法

1. アプリ起動後、`品目IDまたはQRコードを入力してください` に `ITEM-0001` を入力
2. 以下の品目情報が表示されることを確認
   - 品目名: ベアリング
   - 型番: ABC-123
   - メーカー: メーカーA
   - 保管場所: 棚A-01
   - 単位: 個
   - 最低在庫: 2
   - 現在庫: 10

初回実行時に `data/inventory.db` が自動作成され、テーブル初期化とサンプルデータ投入が行われます。
