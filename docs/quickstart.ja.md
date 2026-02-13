# クイックスタート

このガイドでは、APIとスケジューラーをドライランモードでローカル実行する方法を説明します。

## 1) セットアップ
仮想環境を作成して有効化：
  - macOS/Linux (zsh)：
    - `python3 -m venv .venv`
    - `source .venv/bin/activate`
  - プロジェクトと開発ツールをインストール：
    - `pip install -e .[dev]`

## 2) 環境設定
`.env.example` を `.env` にコピーして必要に応じて調整するか、環境変数を手動でエクスポート。

コア（デフォルト）：
  - `DATABASE_URL=sqlite:///pay2slay.db`
  - `SESSION_SECRET=dev-secret`（本番では必ず変更）
  - `P2S_DRY_RUN=true`（実APIを使用するには `false` に設定）
  - `P2S_OPERATOR_ACCOUNT=`（dry-run=false時のバランスチェックにのみ必要）
  - `P2S_METRICS_PORT=8001`
  - `P2S_INTERVAL_SECONDS=1200`（スケジューラーループ）

外部連携（dry-run=false時に必要）：
  - `YUNITE_API_KEY=`
  - `YUNITE_GUILD_ID=`
  - `FORTNITE_API_KEY=`
  - `DISCORD_CLIENT_ID=`
  - `DISCORD_CLIENT_SECRET=`
  - `DISCORD_REDIRECT_URI=http://localhost:3000/auth/discord/callback`

オプションの可観測性：
  - `OTEL_EXPORTER_OTLP_ENDPOINT=` または `PAY2SLAY_OTLP_ENDPOINT=`
  - `PAY2SLAY_METRICS_EXEMPLARS=1`

## 3) APIの実行
  - `uvicorn src.api.app:create_app --reload --port 8000`
  - ヘルスチェック: http://localhost:8000/healthz

## 4) スケジューラーの実行
  - `P2S_METRICS_PORT` でPrometheusメトリクスサーバーを起動。
  - 例（ドライラン、10秒間隔、メトリクス8002番ポート）：
    - `P2S_INTERVAL_SECONDS=10 P2S_DRY_RUN=true P2S_METRICS_PORT=8002 python -m src.jobs`
  - Ctrl-Cで停止。
  - メトリクス: http://localhost:8002/

## 5) 開発サイクル
  - テスト: `pytest -q`
  - リント: `ruff check .`
  - 型チェック: `mypy`

## 6) データベースマイグレーション
Alembic使用時（Postgres / 永続DB）マイグレーションを適用：
```
PAY2SLAY_AUTO_MIGRATE=1 python -m src.api.app  # 起動時にアップグレードをトリガー
```
手動の場合：
```
alembic upgrade head
```

## 7) イメージビルドと署名（サプライチェーン）
コンテナイメージをローカルビルド：
```
docker build -t pay2slay:local .
```
SBOM生成（Syft）と署名（Cosign）（例）：
```
syft packages pay2slay:local -o spdx-json > sbom.json
cosign sign --key cosign.key pay2slay:local
cosign attest --predicate sbom.json --type spdxjson pay2slay:local
```
検証：
```
cosign verify pay2slay:local
```

## 8) デプロイ（Akash）
完全な手順は `README.ja.md` の**デプロイ**セクションを参照。クイックサマリー：
1. GitHubのシークレットと変数をすべて設定（READMEの表を参照）。
2. DiscordアプリのリダイレクトURIを `https://yourdomain.com/auth/discord/callback` に更新。
3. 実行: `gh workflow run deploy-akash.yml -f domain_name=yourdomain.com -f image_tag=latest`
4. ワークフロー出力のAkashプロバイダーホスト名にドメインのCNAMEを向ける。

## 9) Makeショートカット
  - `make api` — API起動（リロード付き）
  - `make scheduler` — スケジューラー起動（env読み込み）
  - `make test` — テスト実行
  - `make lint` — リント
  - `make type` — 型チェック
  - `make all` — lint + type + test

## 10) アーキテクチャノート
- コンテナは `docker-entrypoint.sh` 経由でAPIサーバー（uvicorn）とスケジューラーの両方をバックグラウンドプロセスとして実行。
- Bananoトランザクションは公開Kalium RPC（`https://kaliumapi.appditto.com/api`）を使用 — 自前ノード不要。
- Bananoトランザクション署名用のオペレーターシードは、DBの `SecureConfig` テーブルに暗号化して保存（管理パネルで設定）。

## 11) イミュータブルタグ付けとロールバック（CIワークフロー）
ビルドワークフロー（pushトリガー）は完全な40文字のgit SHAと短い12文字タグでイメージを生成。デプロイとロールバックワークフローはフルSHAタグ（イミュータブル）のみを受け付け、以下を保証：
 - ビルド時のプッシュ前後のダイジェスト検証で改ざんを検出。
