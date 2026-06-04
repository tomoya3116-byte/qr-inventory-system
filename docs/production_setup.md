# 本番運用準備ガイド

このドキュメントは、FastAPI Web版を Windows ローカル、VPS、クラウド環境で運用しやすくするための設定・手順を整理したものです。現時点では SQLite を前提にしつつ、将来的に PostgreSQL へ移行できるように運用上の注意点も記載します。

## 対象範囲

- FastAPI Web版の運用準備
- 環境変数の整理
- Windows ローカル運用の基本手順
- VPS / クラウド運用時の考え方
- バックアップ運用方針
- 管理者パスワード変更方法
- SQLite 運用時の注意点
- 将来 PostgreSQL へ移行する方針

Web版を本番運用するための設定、起動、公開、バックアップ方針を整理します。

## 環境変数一覧

本番運用では、ソースコードへパスワードや環境固有の値を直接書かず、環境変数で指定してください。`.env.example` は設定例のテンプレートです。実際の値は各端末・サーバー上で設定し、秘密情報を Git にコミットしないでください。

| 環境変数 | 必須度 | 既定値 | 用途 |
| --- | --- | --- | --- |
| `QR_INVENTORY_ADMIN_PASSWORD` | 本番必須 | `admin123` | Web版の管理者ログイン用パスワードです。本番では必ず変更してください。 |
| `QR_INVENTORY_ENV` | 推奨 | `development` | 実行環境を表すラベルです。`development`、`staging`、`production` などを想定します。 |
| `QR_INVENTORY_DB_PATH` | 推奨 | `data/inventory.db` | SQLite DBファイルの保存先です。永続化されるディスク上のパスを指定してください。 |
| `QR_INVENTORY_SESSION_SECRET` | 本番推奨 | 開発用固定値 | Web版の管理者ログイン Cookie 署名に使う秘密文字列です。複数人・外部公開環境では長いランダム値を設定してください。 |

`.env.example` の初期値は次のとおりです。

```env
QR_INVENTORY_ADMIN_PASSWORD=change_me
QR_INVENTORY_ENV=development
QR_INVENTORY_DB_PATH=data/inventory.db
```

## Windows ローカル運用手順

Windows PC 1台で小規模に運用する場合は、まずローカルネットワーク内だけで起動し、バックアップ先を明確にしてください。

### 1. 依存ライブラリをインストールする

```powershell
pip install -r requirements.txt
```

### 2. 環境変数を設定する

PowerShell の現在のセッションだけで設定する例です。パスワードとセッション秘密文字列は必ず実運用用の値へ変更してください。

```powershell
$env:QR_INVENTORY_ADMIN_PASSWORD = '任意の強いパスワード'
$env:QR_INVENTORY_ENV = 'production'
$env:QR_INVENTORY_DB_PATH = 'data/inventory.db'
$env:QR_INVENTORY_SESSION_SECRET = '任意の長いランダム文字列'
```

永続化する場合は、Windows の「環境変数」設定画面、または PowerShell の `setx` を利用します。`setx` で設定した値は新しく開いたターミナルから反映されます。

```powershell
setx QR_INVENTORY_ADMIN_PASSWORD "任意の強いパスワード"
setx QR_INVENTORY_ENV "production"
setx QR_INVENTORY_DB_PATH "data/inventory.db"
setx QR_INVENTORY_SESSION_SECRET "任意の長いランダム文字列"
```

### 3. Web版を起動する

同じ PC からだけ利用する場合は `127.0.0.1` で起動します。

```powershell
python -m uvicorn src.web_app:app --host 127.0.0.1 --port 8000
```

同じ Wi-Fi 内のスマートフォンや別 PC から利用する場合は `0.0.0.0` で起動し、Windows ファイアウォールでポート `8000` を許可します。

```powershell
python -m uvicorn src.web_app:app --host 0.0.0.0 --port 8000
```

ブラウザから次の URL にアクセスします。

```text
http://127.0.0.1:8000
```

別端末から接続する場合は、Web版を起動している PC の IP アドレスを使います。

```text
http://PCのIPアドレス:8000
```

## VPS / クラウド運用時の考え方

VPS やクラウド環境で公開する場合は、アプリケーションを直接インターネットへ露出するのではなく、リバースプロキシと HTTPS を前提にしてください。

推奨構成の考え方は次のとおりです。

1. FastAPI / Uvicorn はサーバー内のローカルポートで起動する。
2. Nginx などのリバースプロキシで外部からの HTTPS 通信を受ける。
3. TLS証明書を設定し、管理者ログインや入出庫操作を平文 HTTP で送信しない。
4. `QR_INVENTORY_ADMIN_PASSWORD` と `QR_INVENTORY_SESSION_SECRET` はサーバーの環境変数またはサービス管理設定で注入する。
5. `QR_INVENTORY_DB_PATH` は永続ディスク上のパスにする。
6. DBファイル、バックアップ、ログの保存先を分け、サーバー再起動後も消えない場所へ配置する。
7. OS、Python、依存ライブラリ、Nginx などを定期的に更新する。

systemd で起動する場合は、サービスファイルの `Environment=` または `EnvironmentFile=` に環境変数を定義し、作業ディレクトリをリポジトリのルートへ合わせます。実際のサービスファイルはサーバー構成に合わせて作成してください。

## バックアップ運用方針

SQLite 運用では `QR_INVENTORY_DB_PATH` で指定した DBファイルが最重要データです。最低限、次の方針でバックアップしてください。

- 手動バックアップ: 管理者ログイン後の DBバックアップ画面から、作業前・棚卸前・CSV取込前などに取得する。
- 自動バックアップ: CSV取込、棚卸修正、DB復旧など影響が大きい操作の前に作成されるバックアップを保管する。
- 定期バックアップ: 1日1回以上、DBファイルと `backups/` ディレクトリを外部ストレージや別サーバーへコピーする。
- 世代管理: 日次7世代、週次4世代、月次12世代など、復旧したい期間に合わせて保持期間を決める。
- 復旧テスト: バックアップファイルから別環境へ復旧できることを定期的に確認する。

バックアップ先は同じディスクだけに置かず、PC故障・VPS障害・誤削除に備えて外部媒体や別環境にも保存してください。

## 管理者パスワード変更方法

管理者パスワードは `QR_INVENTORY_ADMIN_PASSWORD` で変更します。

### Windows PowerShell

```powershell
$env:QR_INVENTORY_ADMIN_PASSWORD = '新しい強いパスワード'
python -m uvicorn src.web_app:app --host 127.0.0.1 --port 8000
```

永続化する場合は次のように設定し、ターミナルを開き直してから起動します。

```powershell
setx QR_INVENTORY_ADMIN_PASSWORD "新しい強いパスワード"
```

### macOS / Linux / VPS

```bash
export QR_INVENTORY_ADMIN_PASSWORD='新しい強いパスワード'
python -m uvicorn src.web_app:app --host 127.0.0.1 --port 8000
```

サービス化している場合は、systemd などのサービス定義に設定してから再起動します。

```bash
sudo systemctl restart qr-inventory
```

パスワード変更後、既存のログインセッションを確実に無効化したい場合は、`QR_INVENTORY_SESSION_SECRET` も新しい値へ変更してください。

## SQLite 運用時の注意

SQLite は小規模運用やローカル運用に適していますが、次の制約を理解して使ってください。

- 同時書き込みが多い運用には向きません。
- DBファイルをネットワーク共有フォルダに置くと、ロックや破損のリスクが上がる場合があります。
- DBファイルをコピーするバックアップでは、書き込み中のタイミングに注意が必要です。業務時間外や操作停止中のバックアップを推奨します。
- DBファイル、`backups/`、QR画像、ラベルHTMLなど、運用に必要な生成物の保存場所を把握してください。
- ディスク容量不足は書き込み失敗やDB破損の原因になるため、空き容量を監視してください。
- 外部公開する場合は HTTPS、強い管理者パスワード、長いセッション秘密文字列、OSファイアウォールを必ず設定してください。

## 将来 PostgreSQL へ移行する方針

利用人数や同時操作が増える場合、または VPS / クラウドで長期運用する場合は PostgreSQL への移行を検討します。

移行時の基本方針は次のとおりです。

1. DB接続設定を `QR_INVENTORY_DATABASE_URL` のような接続文字列で管理できるようにする。
2. SQLite 固有のSQLや型を洗い出し、PostgreSQL で動作する形へ調整する。
3. スキーマ管理を SQL ファイルだけでなく、マイグレーションツールで管理することを検討する。
4. 既存の `items`、`transactions` データをCSVまたは移行スクリプトで移す。
5. 移行前に SQLite の完全バックアップを取得し、別環境でリハーサルを行う。
6. 移行後は PostgreSQL のダンプ、リストア、監視、権限管理を運用手順に追加する。

現時点では SQLite のまま運用準備を整え、データ量・利用人数・同時操作数が増えた段階で PostgreSQL 対応を別フェーズとして実施する想定です。

## 運用前チェックリスト

- [ ] `.env.example` を参考に、本番用の環境変数を設定した。
- [ ] `QR_INVENTORY_ADMIN_PASSWORD` を初期値以外の強いパスワードに変更した。
- [ ] `QR_INVENTORY_SESSION_SECRET` に長いランダム文字列を設定した。
- [ ] `QR_INVENTORY_DB_PATH` が永続化される保存先を指している。
- [ ] バックアップ保存先と世代管理ルールを決めた。
- [ ] バックアップから復旧できることをテストした。
- [ ] 外部公開する場合は HTTPS、ファイアウォール、リバースプロキシを設定した。
