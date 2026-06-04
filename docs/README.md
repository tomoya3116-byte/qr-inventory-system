# ドキュメント一覧

このディレクトリには、Web版の利用手順、運用者向けの設定手順、開発・保守向けの仕様を置きます。
旧CUI版・旧デスクトップGUI版の専用手順や作業メモは削除し、現在のアプリケーションを使うために必要な文書だけを残します。

## 利用者向け

| ドキュメント | 内容 |
| --- | --- |
| [`web_usage.md`](web_usage.md) | Web版の起動方法、管理者ログイン、スマートフォン接続、機能一覧 |

## 運用者向け

| ドキュメント | 内容 |
| --- | --- |
| [`production_setup.md`](production_setup.md) | 環境変数、ローカル運用、VPS / クラウド運用、バックアップ方針 |
| [`schema.md`](schema.md) | SQLite の主要テーブルとカラム |

## 開発・保守向け

| ドキュメント | 内容 |
| --- | --- |
| [`v2_spec.md`](v2_spec.md) | Ver2.0 Web版の目的、実装状況、技術方針、セキュリティ方針 |

## 保管場所のルール

- Python実装は `src/` に集約します。
- Jinja2テンプレートは用途別に `templates/auth/`、`templates/dashboard/`、`templates/inventory/`、`templates/stock/`、`templates/admin/` へ分け、共通レイアウトは `templates/layouts/`、再利用部品は `templates/partials/` に置きます。
- 静的ファイルは種類別に `static/css/` と `static/js/` へ置きます。
- 実行時に生成される `data/`、`backups/`、`qr_codes/`、`labels/` はリポジトリルート基準で自動作成されるため、通常はリポジトリに空ディレクトリを保持しません。
- CSV取込の見本など実装ではないファイルは `examples/` 配下に置きます。

