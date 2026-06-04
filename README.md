# qr-inventory-system

QR code based inventory management system using Python and SQLite.

## 概要

業務用の貯蔵品管理を想定した、CUI / GUI / Web対応の在庫管理システムです。
品目IDまたはQRコードを入力して検索し、入庫・出庫・棚卸修正・履歴確認に加えて、品目マスタの一覧・登録・編集・削除を行えます。

## 現在の開発状況

現在は Ver2.0 Web Phase 11 相当まで進んでいます。
CUI版・GUI版を継続利用できる状態を保ちながら、FastAPIベースのWeb版に管理者ログイン、品目マスタ管理、入出庫、棚卸修正、CSV取込・CSV出力、QRコード生成、ラベル印刷、DBバックアップ・復旧、操作ログ、検索・絞り込み・並び替え、QRスキャン運用を追加しています。

## 主な機能

- **CUI版**: 品目検索、入庫、出庫、品目一覧、履歴確認、品目マスタ管理、棚卸修正、CSV取込などをターミナルから操作できます。
- **GUI版**: 現場作業者向けの通常メニューと、危険操作・管理操作をまとめた管理者メニューを分離しています。
- **Web版**: スマートフォンやPCブラウザから、品目一覧、品目検索、入庫、出庫、最低在庫アラート、管理者機能を利用できます。
- **実用機能**: CSV取込・CSV出力、QRコード生成、ラベル印刷用HTML生成、DBバックアップ、DB復旧、操作ログ、QRスキャン運用に対応しています。

## クイックスタート

1. Python 3.10 以上をインストールします。
2. リポジトリのルートで必要ライブラリをインストールします。

```bash
pip install -r requirements.txt
```

3. 使いたい画面に合わせて起動します。

```bash
# CUI版
python src/main.py

# GUI版
python src/gui_main.py

# Web版（PCローカル確認）
python -m uvicorn src.web_app:app --reload --host 127.0.0.1 --port 8000
```

初回実行時に `data/inventory.db` が自動作成され、テーブル初期化とサンプルデータ投入が行われます。
Web版を起動した場合は、PCブラウザで `http://127.0.0.1:8000` にアクセスしてください。

## ドキュメント

| ドキュメント | 内容 |
| --- | --- |
| [`docs/cui_usage.md`](docs/cui_usage.md) | CUI版のサンプルデータ、基本操作、動作確認例 |
| [`docs/gui_usage.md`](docs/gui_usage.md) | GUI版の起動方法、通常メニュー、管理者メニュー、動作確認例 |
| [`docs/web_usage.md`](docs/web_usage.md) | Web版の起動方法、管理者ログイン、スマートフォン接続、Web機能一覧 |
| [`docs/feature_usage.md`](docs/feature_usage.md) | 品目マスタ管理、最低在庫、棚卸修正、QR、ラベル、バックアップ、CSV取込などの機能別手順 |
| [`docs/schema.md`](docs/schema.md) | SQLite の主要テーブルとカラム |
| [`docs/v2_spec.md`](docs/v2_spec.md) | Ver2.0 Web版の仕様書 |
| [`docs/web_external_access.md`](docs/web_external_access.md) | Ver2.0 Web Phase 5 の外部公開テスト手順 |
| [`docs/production_setup.md`](docs/production_setup.md) | Ver2.0 Web Phase 6 の本番運用準備ガイド |
| [`docs/deployment_plan.md`](docs/deployment_plan.md) | Ver2.0 Web Phase 7 のVPS / クラウド公開設計 |

## バージョン方針

- Ver1.0 は、既存のCUI版およびGUI版を中心としたデスクトップ版です。
- Ver2.0 は、スマートフォンやPCブラウザから利用できるWebアプリ版として開発中です。
- Ver2.0 Web Phase 8 では、Web操作の操作ログ・監査ログを管理者向けに追加しています。
- Ver2.0 Web Phase 9 では、在庫データや入出庫履歴をExcelで確認・保管・報告しやすいCSV出力機能を追加しています。
- Ver2.0 Web Phase 10 では、品目一覧と品目検索の検索・絞り込み・並び替え機能を強化しています。
- Ver2.0 Web Phase 11 では、スマートフォンでQRコードを読み取って品目確認・入庫・出庫へ進めるQRスキャン運用を追加しています。

## ライセンス

このリポジトリは、将来的な有償販売・商用利用を想定し、MIT License で公開する方針です。
利用ライブラリは、MIT / BSD / PSF / Apache-2.0 など商用利用しやすいライセンスを優先し、GPL / AGPL 系ライブラリは原則として避ける方針です。
詳細は `THIRD_PARTY_NOTICES.md` を参照してください。
