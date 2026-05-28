# qr-inventory-system

QR code based inventory management system using Python and SQLite.

## 概要

初期段階ではQRリーダーを利用せず、CUIで品目IDを手入力してSQLiteから品目情報を検索します。

## セットアップ

1. Python 3.10 以上をインストール
2. リポジトリのルートで以下を実行

```bash
python3 src/main.py
```

## 使い方

1. プログラム起動後、`品目IDを入力してください` のプロンプトにIDを入力
2. 例: `ITEM001`, `ITEM002`, `ITEM003`
3. 終了する場合は `q` を入力

初回実行時に `data/inventory.db` が自動作成され、テーブル初期化とサンプルデータ投入が行われます。
