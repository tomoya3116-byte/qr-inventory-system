# Ver2.0 Web Phase 5 外部公開テスト手順

この手順書は、ローカルPCで起動している Ver2.0 Web アプリを、同一Wi-Fi外のスマートフォンから一時的に確認するためのものです。
本番運用や販売環境ではなく、短時間の外部公開テストだけを対象にしています。

## 前提

- Windows PowerShell で操作します。
- リポジトリのルートディレクトリでコマンドを実行します。
- Python の依存ライブラリは事前にインストール済みとします。

```powershell
pip install -r requirements.txt
```

## 1. ローカルPCだけで起動して確認する

同じPCのブラウザだけで確認する場合は、`127.0.0.1` で起動します。

```powershell
python -m uvicorn src.web_app:app --reload --host 127.0.0.1 --port 8000
```

起動後、同じPCのブラウザで以下にアクセスします。

```text
http://127.0.0.1:8000
```

`127.0.0.1` は自分自身のPCだけを指すため、この起動方法ではスマートフォンや別PCからは接続できません。

## 2. 同一Wi-Fi内のスマートフォンから確認する

同じWi-Fiに接続しているスマートフォンから確認する場合は、外部端末からの接続を受け付けるために `0.0.0.0` で起動します。

```powershell
python -m uvicorn src.web_app:app --reload --host 0.0.0.0 --port 8000
```

別のPowerShellを開き、PCのIPv4アドレスを確認します。

```powershell
ipconfig
```

スマートフォンをPCと同じWi-Fiに接続し、スマートフォンのブラウザで以下の形式のURLにアクセスします。

```text
http://PCのIPv4アドレス:8000
```

例: PCのIPv4アドレスが `192.168.1.10` の場合

```text
http://192.168.1.10:8000
```

Windows Defender ファイアウォールなどでポート `8000` がブロックされている場合は、PC側で許可してください。

## 3. Cloudflare Tunnelで一時公開する考え方

Cloudflare Tunnel を使うと、ルーターのポート開放を行わずに、ローカルPCで動いているWebアプリへ一時的な公開URLからアクセスできます。
同一Wi-Fi外のスマートフォンで確認したい場合は、原則としてこの方法を推奨します。

### 基本手順

1. 管理者ログイン用の環境変数を設定します。`admin123` のまま外部公開しないでください。

```powershell
$env:QR_INVENTORY_ADMIN_PASSWORD = '任意の強いパスワード'
$env:QR_INVENTORY_SESSION_SECRET = '任意の長いランダム文字列'
```

2. WebアプリをローカルPCで起動します。

```powershell
python -m uvicorn src.web_app:app --reload --host 127.0.0.1 --port 8000
```

3. 別のPowerShellを開き、Cloudflare Tunnel を起動して `http://127.0.0.1:8000` に転送します。

```powershell
cloudflared tunnel --url http://127.0.0.1:8000
```

4. PowerShellに表示された一時公開URLを、同一Wi-Fi外のスマートフォンのブラウザで開きます。

Cloudflare Tunnel の一時公開URLは、テストが終わったらPowerShellで `Ctrl + C` を押して停止してください。停止後は、そのURLからローカルWebアプリへ接続できなくなります。

## 4. ngrokで一時公開する考え方

ngrok でも、ローカルPCの `http://127.0.0.1:8000` を一時的な公開URLへ転送できます。
Cloudflare Tunnel が使えない場合の補足手段として利用してください。

### 基本手順

1. 管理者ログイン用の環境変数を設定します。`admin123` のまま外部公開しないでください。

```powershell
$env:QR_INVENTORY_ADMIN_PASSWORD = '任意の強いパスワード'
$env:QR_INVENTORY_SESSION_SECRET = '任意の長いランダム文字列'
```

2. WebアプリをローカルPCで起動します。

```powershell
python -m uvicorn src.web_app:app --reload --host 127.0.0.1 --port 8000
```

3. 別のPowerShellを開き、ngrok で `8000` 番ポートを公開します。

```powershell
ngrok http 8000
```

4. PowerShellに表示された `https://...` の転送URLを、同一Wi-Fi外のスマートフォンのブラウザで開きます。

ngrok の公開URLも、テストが終わったらPowerShellで `Ctrl + C` を押して停止してください。停止後は、そのURLからローカルWebアプリへ接続できなくなります。

## 5. 外部公開時のセキュリティ注意事項

外部公開URLは、インターネット経由でアクセスできるURLです。短時間のテストでも、以下を必ず守ってください。

- 外部公開時は必ずログイン機能を有効にし、管理者ログインが必要な操作を保護してください。
- 開発用の初期パスワード `admin123` のまま外部公開しないでください。
- `QR_INVENTORY_ADMIN_PASSWORD` には、推測されにくい強いパスワードを設定してください。
- `QR_INVENTORY_SESSION_SECRET` には、長くランダムな文字列を設定してください。
- Cloudflare Tunnel や ngrok の公開URLを第三者に共有しないでください。
- SNS、チャット、公開リポジトリ、スクリーンショットなどに公開URLを載せないでください。
- テストが終わったら、Cloudflare Tunnel または ngrok のPowerShellを `Ctrl + C` で必ず停止してください。
- 外部公開中は、個人情報、顧客情報、本番在庫データなどを含むデータベースを使わないでください。
- 不審なアクセスや想定外の挙動があった場合は、すぐにトンネルを停止してください。

## 6. 本番販売時の方針

Cloudflare Tunnel や ngrok による一時公開は、外部公開テストのための簡易的な方法です。
本番販売や継続運用では、ローカルPCを直接公開するのではなく、VPSやクラウド環境へ移行する方針とします。

本番環境では、少なくとも以下を別途検討してください。

- HTTPSを前提にした正式なドメイン運用
- アプリケーションサーバーとリバースプロキシの構成
- 強固な認証、認可、パスワード管理
- ファイアウォール、アクセス制限、ログ監視
- データベースのバックアップ、復旧、保全手順
- 障害対応、アップデート、脆弱性対応の運用ルール
