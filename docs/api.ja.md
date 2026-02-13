# APIリファレンス

FastAPIバックエンド。全セッションはHttpOnly、SameSite=Lax Cookieを使用。

## 認証

| Cookie | 設定元 | 用途 |
|--------|-------|------|
| `p2s_session` | `/auth/discord/callback` | ユーザーセッション |
| `p2s_admin` | `/admin/login` | 管理者セッション |

## ヘルスチェック・インフラ

| メソッド | パス | 説明 |
|---------|------|------|
| GET | `/healthz` | ヘルスチェック → `{ status: "ok" }` |
| GET | `/livez` | ライブネスプローブ |
| GET | `/readyz` | レディネスプローブ |
| GET | `/metrics` | Prometheusメトリクス |

## 認証

| メソッド | パス | 説明 |
|---------|------|------|
| GET | `/auth/discord/login` | Discord OAuthへリダイレクト |
| GET | `/auth/discord/callback` | OAuthコールバック — `p2s_session` Cookieを設定 |

## ユーザーエンドポイント

`p2s_session` Cookieが必要。

| メソッド | パス | 説明 |
|---------|------|------|
| POST | `/link/wallet` | `ban_` アドレスをリンク。ボディ: `{ "banano_address": "ban_..." }` |
| POST | `/me/reverify` | Yunite検証を再トリガー |
| GET | `/me/status` | 現在のユーザーステータス、ウォレット、累計報酬 |
| GET | `/me/payouts` | ユーザーの報酬支払い履歴 |
| GET | `/me/accruals` | ユーザーの報酬蓄積履歴 |

## パブリックAPI

認証不要。

| メソッド | パス | 説明 |
|---------|------|------|
| GET | `/api/leaderboard` | キル数と獲得額によるトッププレイヤー |
| GET | `/api/feed` | 最近のアクティビティフィード（支払い、蓄積） |
| GET | `/api/donate-info` | オペレーターウォレットアドレス＋寄付用バランス |
| GET | `/api/scheduler/countdown` | 次の蓄積/精算サイクルまでの秒数 |
| GET | `/api/donations` | 寄付進捗、マイルストーン、現在の倍率 |
| GET | `/config/product` | 公開プロダクト設定（アプリ名、フィーチャーフラグ） |

## 管理者エンドポイント

`p2s_admin` Cookieが必要。

| メソッド | パス | 説明 |
|---------|------|------|
| POST | `/admin/login` | 管理者ログイン。ボディ: `{ "email": "..." }` |
| POST | `/admin/reverify` | ユーザーの強制再検証。ボディ: `{ "discord_id": "..." }` |
| POST | `/admin/payouts/retry` | 失敗した支払いをリトライ。ボディ: `{ "payout_id": 123 }` |
| GET | `/admin/audit` | 管理者監査ログ |
| GET | `/admin/stats` | システム統計 |
| GET | `/admin/health/extended` | 拡張ヘルスチェック |
| POST | `/admin/config/operator-seed` | 暗号化オペレーターシード設定 |
| GET | `/admin/config/operator-seed/status` | オペレーターシード設定状態確認 |
| GET | `/admin/scheduler/status` | スケジューラー現在状態 |
| POST | `/admin/scheduler/trigger` | スケジューラー実行トリガー |
| POST | `/admin/scheduler/settle` | 精算のみトリガー |
| GET | `/admin/scheduler/config` | スケジューラー設定取得 |
| POST | `/admin/scheduler/config` | スケジューラー設定更新 |
| GET | `/admin/payout/config` | 報酬支払い設定取得（ban_per_kill、上限） |
| POST | `/admin/payout/config` | 報酬支払い設定更新 |

## デモエンドポイント

開発/デモモードで利用可能。

| メソッド | パス | 説明 |
|---------|------|------|
| POST | `/auth/demo-login` | Discord OAuthなしでログイン |
| POST | `/demo/seed` | テストデータでDBをシード |
| POST | `/demo/run-scheduler` | スケジューラーサイクルを即時実行 |
| POST | `/demo/clear` | 全デモデータをクリア |

## デバッグ

| メソッド | パス | 説明 |
|---------|------|------|
| GET | `/debug/yunite` | Yunite API接続テスト |

## 備考

- **ドライランモード**（`P2S_DRY_RUN=true`）: 外部APIコールとブロックチェーン送金をスキップ。
- セッションは `SESSION_SECRET` でHMAC署名され、有効期限を含みます。
- エラーレスポンスは標準HTTPステータスコード（400、401、403、404）を使用。
