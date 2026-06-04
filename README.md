# qr-inventory-system

QR code based inventory management system using Python, SQLite, and FastAPI.

## 概要

業務用の貯蔵品管理を想定した、Webブラウザ対応の在庫管理システムです。
品目IDまたはQRコードを入力して検索し、入庫・出庫・棚卸修正・履歴確認に加えて、品目マスタの一覧・登録・編集・削除を行えます。

## 現在の開発状況

現在は Ver2.0 Web版に開発対象を集約しています。
管理者ログイン、品目マスタ管理、入出庫、棚卸修正、CSV取込・CSV出力、QRコード生成、ラベル印刷、DBバックアップ・復旧、操作ログ、検索・絞り込み・並び替え、QRスキャン運用を追加済みです。

## 主な機能

- **Web版**: スマートフォンやPCブラウザから、品目一覧、品目検索、入庫、出庫、最低在庫アラート、管理者機能を利用できます。
- **実用機能**: CSV取込・CSV出力、QRコード生成、ラベル印刷用HTML生成、DBバックアップ、DB復旧、操作ログ、QRスキャン運用に対応しています。
- **運用機能**: 環境変数によるDB保存先、管理者パスワード、セッション署名キー、QRコードURLの設定に対応しています。

## クイックスタート

1. Python 3.10 以上をインストールします。
2. リポジトリのルートで必要ライブラリをインストールします。

```bash
pip install -r requirements.txt
```

3. Webアプリを起動します。

```bash
python -m uvicorn src.web_app:app --reload --host 127.0.0.1 --port 8000
```

初回実行時に `data/inventory.db` が自動作成され、テーブル初期化とサンプルデータ投入が行われます。
起動後、PCブラウザで `http://127.0.0.1:8000` にアクセスしてください。

## ドキュメント

| ドキュメント | 内容 |
| --- | --- |
| [`docs/README.md`](docs/README.md) | ドキュメント全体の目次と分類 |
| [`docs/web_usage.md`](docs/web_usage.md) | Web版の起動方法、管理者ログイン、スマートフォン接続、Web機能一覧 |
| [`docs/production_setup.md`](docs/production_setup.md) | 環境変数、ローカル運用、VPS / クラウド運用、バックアップ方針 |
| [`docs/schema.md`](docs/schema.md) | SQLite の主要テーブルとカラム |
| [`docs/v2_spec.md`](docs/v2_spec.md) | Ver2.0 Web版の仕様書 |


## リポジトリ構成

用途ごとに保管場所を分け、Web版の実装・画面・静的アセット・運用資料を探しやすくしています。

| パス | 内容 |
| --- | --- |
| `src/` | FastAPIアプリ、SQLite操作、QRコード・ラベル生成などのPython実装 |
| `templates/layouts/` | Jinja2の共通レイアウト |
| `templates/partials/` | 複数画面で再利用するJinja2部品 |
| `templates/auth/` | ログインなど認証関連画面 |
| `templates/dashboard/` | トップページ・ダッシュボード画面 |
| `templates/inventory/` | 品目一覧、検索、品目マスタ管理、最低在庫画面 |
| `templates/stock/` | QRスキャン、入庫、出庫、棚卸修正画面 |
| `templates/admin/` | 管理者機能、CSV、QRコード、ラベル、バックアップ、ログ画面 |
| `static/css/` | CSSファイル |
| `static/js/` | JavaScriptファイル |
| `examples/imports/` | CSV取込のサンプルファイル |
| `docs/` | 利用・運用・仕様ドキュメント |

## 整理方針

環境整備のため、旧CUI版・旧デスクトップGUI版のエントリポイントと専用ドキュメントは削除し、日常利用と運用保守の対象をWeb版に一本化しています。
生成物ディレクトリはアプリケーション実行時に必要に応じて自動作成されるため、空ディレクトリ維持用ファイルは置かない方針です。

## ライセンス

このリポジトリは、将来的な有償販売・商用利用を想定し、MIT License で公開する方針です。
利用ライブラリは、MIT / BSD / PSF / Apache-2.0 など商用利用しやすいライセンスを優先し、GPL / AGPL 系ライブラリは原則として避ける方針です。
詳細は `THIRD_PARTY_NOTICES.md` を参照してください。
