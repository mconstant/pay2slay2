# Pay2Slay

<p align="center">
  <img src="static/logo.png" alt="Pay2Slay ロゴ" width="180" />
</p>

<p align="center">
  <strong>Fortniteのキルでバナノを稼ごう。</strong><br/>
  プレイヤーにキルごとにBANで報酬を支払う暗号通貨フォーセット。
</p>

<p align="center">
  https://pay2slay.cc
</p>

<p align="center">
  <a href="README.md">English</a> ·
  <a href="README.uk.md">Українська</a> ·
  <a href="README.es.md">Español</a> ·
  <a href="README.pt.md">Português</a> ·
  <strong>日本語</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.13-blue?style=flat" alt="Python 3.13" />
  <img src="https://img.shields.io/badge/framework-FastAPI-009688?style=flat" alt="FastAPI" />
  <img src="https://img.shields.io/badge/chain-Banano-FBDD11?style=flat" alt="Banano" />
  <img src="https://img.shields.io/badge/deploy-Akash-red?style=flat" alt="Akash" />
</p>

---

## スクリーンショット

| リーダーボード | 寄付 |
|:--------------:|:----:|
| ![リーダーボード](docs/screenshots/leaderboard.png) | ![寄付](docs/screenshots/donations.png) |

## 仕組み

1. **Discordでログイン** — OAuthで認証し、YuniteがDiscordとEpic Gamesアカウントを紐付けします。
2. **Bananoウォレットをリンク** — `ban_` アドレスを貼り付けます（Kalium、Banano Vaultなど）。
3. **Fortniteをプレイ** — スケジューラーがキルを追跡し、キルごとに **0.05 BAN**（基本レート）をウォレットに自動送金します。

報酬は**サステナビリティファクター**と**寄付マイルストーン**により動的に調整されます。日次・週次のキル上限がファンドの健全性を維持します。

## 機能

- **リアルタイムリーダーボード** — キル数、獲得額、アクティビティフィード付き
- **寄付マイルストーン** — フレッシュスポーン（1.0x）からポタシウムシンギュラリティ（1.5x）まで10段階、目標10K BAN
- **サステナビリティファクター** — 寄付対支出比率に基づく動的報酬調整
- **透明な経済システム** — 寄付ページでライブ計算式を公開
- **日次/週次報酬上限**（100 / 500キル）— 不正検知ヒューリスティクス付き
- **管理パネル** — スケジューラー制御、報酬設定、オペレーターシード管理、監査ログ
- **デモモード** — テストデータでのローカル開発用フルドライラン
- **サプライチェーンセキュリティ** — Cosign署名イメージ、SBOM証明、ダイジェスト検証

## フォーセット経済

Pay2Slayはフォーセットの持続可能性を保つため、自己バランス型の報酬計算式を使用します：

```
有効レート = 基本レート × マイルストーン倍率 × サステナビリティファクター
```

| パラメータ | 値 | 備考 |
|-----------|---|------|
| 基本レート | **0.05 BAN/キル** | `payout.yaml`で設定 |
| 日次キル上限 | **100キル**（≈5 BAN/日） | プレイヤーごとの上限 |
| 週次キル上限 | **500キル**（≈25 BAN/週） | プレイヤーごとの上限 |
| シードファンド | **約1,337 BAN** | オペレーター初期バランス |
| 寄付目標 | **10,000 BAN** | 全マイルストーンティアを解放 |

### サステナビリティファクター

サステナビリティファクターは、流入（シードファンド＋寄付）対流出（総支払額）の比率に基づいて自動的に報酬を調整します：

```
サステナビリティ = clamp((シードファンド + 総寄付額) / 総支払額, 0.1, 2.0)
```

- **≥ 1.0x**（緑） — 寄付が追いついているか上回っている；全額またはボーナス報酬
- **0.5–1.0x**（黄） — 支払いが寄付を上回っている；レート低下
- **< 0.5x**（赤） — ファンド枯渇中；寿命延長のため大幅レート低下

### マイルストーンティア

| ティア | 閾値 | 倍率 |
|--------|-----|------|
| 🌱 フレッシュスポーン | 0 BAN | 1.00x |
| 🩸 ファーストブラッド | 100 BAN | 1.05x |
| 📦 ルートドロップ | 500 BAN | 1.10x |
| 🪂 サプライドロップ | 1,000 BAN | 1.15x |
| ⛈️ ストームサージ | 2,500 BAN | 1.20x |
| 🛩️ エアドロップ着信 | 5,000 BAN | 1.25x |
| 👑 ビクトリーロイヤル | 10,000 BAN | 1.30x |
| 💎 ミシックレアリティ | 25,000 BAN | 1.40x |
| 🐒 ザ・モンケ覚醒 | 50,000 BAN | 1.45x |
| 🍌 ポタシウムシンギュラリティ | 100,000 BAN | 1.50x |

すべての経済データは寄付ページで透明に表示されます。ライブ計算式、サステナビリティゲージ、ファンド内訳を含みます。

## クイックスタート

```bash
git clone https://github.com/mconstant/pay2slay2.git && cd pay2slay2
python3 -m venv .venv && source .venv/bin/activate
pip install -e '.[dev]'

# ターミナル1: APIサーバー
make api        # http://localhost:8000

# ターミナル2: スケジューラー
make scheduler  # メトリクス :8001
```

デフォルトで**ドライランモード**で動作 — ローカル開発にはAPIキーやBANは不要です。完全なセットアップは [docs/quickstart.ja.md](docs/quickstart.ja.md) を参照。

## 設定

`configs/` のYAML設定ファイル：

| ファイル | 制御内容 |
|---------|---------|
| `payout.yaml` | `ban_per_kill`、`daily_payout_cap`、`weekly_payout_cap`、`seed_fund_ban`、スケジューラー間隔 |
| `integrations.yaml` | Banano RPC、Discord OAuth、Yunite、Fortnite API、不正ヒューリスティクス |
| `product.yaml` | アプリ名、フィーチャーフラグ、Discord招待URL |

主要環境変数：

| 変数 | デフォルト | 備考 |
|-----|----------|------|
| `DATABASE_URL` | `sqlite:///pay2slay.db` | 本番用PostgreSQL対応 |
| `P2S_DRY_RUN` | `true` | 実際の報酬支払いには `false` に設定 |
| `SESSION_SECRET` | `dev-secret` | **本番では必ず変更** |
| `P2S_INTERVAL_SECONDS` | `1200` | スケジューラーループ間隔 |
| `P2S_METRICS_PORT` | `8001` | Prometheusメトリクス |

## Makeターゲット

| ターゲット | アクション |
|-----------|----------|
| `make api` | uvicorn --reloadでAPI起動 |
| `make scheduler` | スケジューラーループ起動 |
| `make test` | pytest実行 |
| `make lint` | ruff実行 |
| `make type` | mypy実行 |
| `make all` | lint + type + test |
| `make ci` | フルCIパイプライン |

## デプロイ（Akash Network）

[Akash](https://akash.network)上の単一コンテナでAPI＋スケジューラーを実行。Bananoトランザクションは公開Kalium RPCを使用 — 自前ノード不要。

### 前提条件

1. AKTを持つAkashウォレット（[Keplrセットアップ](#akashウォレットセットアップ)）
2. GitHub CLI（`gh auth login`）
3. DNS管理可能なドメイン

### GitHubシークレット

| シークレット | 説明 |
|------------|------|
| `AKASH_MNEMONIC` | 24ワードのウォレットニーモニック |
| `AKASH_CERT` | TLSクライアント証明書（`rotate-akash-cert`ワークフロー経由） |
| `GH_PAT` | `repo`スコープ付きGitHub PAT |
| `SESSION_SECRET` | `openssl rand -hex 32` |
| `DISCORD_CLIENT_ID` | Discord OAuthアプリ |
| `DISCORD_CLIENT_SECRET` | Discord OAuthアプリ |
| `DISCORD_REDIRECT_URI` | `https://yourdomain.com/auth/discord/callback` |
| `YUNITE_API_KEY` | Epicアカウント解決 |
| `FORTNITE_API_KEY` | fortnite-api.comキー |

### GitHub変数

| 変数 | 説明 |
|-----|------|
| `AKASH_ACCOUNT_ADDRESS` | あなたの `akash1...` アドレス |
| `AKASH_CERT_ID` | rotate-certワークフローで設定 |
| `YUNITE_GUILD_ID` | DiscordサーバーID |
| `P2S_OPERATOR_ACCOUNT` | オペレーター `ban_` アドレス |
| `ADMIN_DISCORD_USERNAMES` | カンマ区切りの管理者ユーザー名 |

### デプロイ

```bash
gh workflow run deploy-akash.yml -f domain_name=pay2slay.cc -f image_tag=latest
```

ドメインのCNAMEをワークフロー出力のAkashプロバイダーホスト名に向けてください。TLSはLet's Encryptで自動処理されます。

### Docker（ローカル）

```bash
docker build -t pay2slay:dev .
docker run -p 8000:8000 --env-file .env pay2slay:dev
```

起動時にAlembicマイグレーションを実行するには `PAY2SLAY_AUTO_MIGRATE=1` を設定。

### Akashウォレットセットアップ

1. [Keplr](https://www.keplr.app/)をインストールし、24ワードのニーモニックを保存。
2. KeplrでAkash Networkを有効化。
3. 取引所または[Osmosis](https://app.osmosis.zone)のIBCスワップでAKTを入金。

### 証明書ローテーション

```bash
make rotate-akash-cert
```

### サプライチェーンセキュリティ

イメージはCosign（キーレス/Sigstore）で署名され、SBOM（Syft/SPDX）で証明されます。ロールバックワークフローはリビルドなしで既存イメージを再利用します。

## 技術スタック

| レイヤー | 技術 |
|---------|------|
| バックエンド | Python 3.13、FastAPI、SQLAlchemy、Alembic |
| データベース | SQLite（開発）、PostgreSQL（本番） |
| ブロックチェーン | Banano（bananopie / Kalium RPC経由） |
| 認証 | Discord OAuth + Yunite Epic マッピング |
| 統計 | Fortnite API（fortnite-api.com） |
| 可観測性 | Prometheus、OpenTelemetry |
| デプロイ | Docker、Akash Network、Terraform |
| セキュリティ | Cosign、Syft SBOM、ダイジェストガード |

## ドキュメント

| ドキュメント | 説明 |
|-----------|------|
| [クイックスタート](docs/quickstart.ja.md) | ローカルセットアップ完全ガイド |
| [APIリファレンス](docs/api.ja.md) | 全エンドポイント |
| [データモデル](docs/data-model.md) | データベーススキーマ |
| [ランブック](docs/runbook.md) | 本番運用 |
| [プライバシーポリシー](docs/PRIVACY.ja.md) | データ取扱い |
| [セキュリティ](SECURITY.md) | 脆弱性報告、強化対策 |
| [コントリビュート](CONTRIBUTING.md) | 開発ワークフロー、コードスタイル |

## ライセンス

[MIT](LICENSE)
