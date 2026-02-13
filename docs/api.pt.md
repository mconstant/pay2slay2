# Referência API

Backend FastAPI. Todas as sessões usam cookies HttpOnly, SameSite=Lax.

## Autenticação

| Cookie | Definido por | Propósito |
|--------|-------------|-----------|
| `p2s_session` | `/auth/discord/callback` | Sessão do usuário |
| `p2s_admin` | `/admin/login` | Sessão do administrador |

## Saúde e infraestrutura

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/healthz` | Verificação de saúde → `{ status: "ok" }` |
| GET | `/livez` | Sonda de liveness |
| GET | `/readyz` | Sonda de readiness |
| GET | `/metrics` | Métricas Prometheus |

## Autenticação

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/auth/discord/login` | Redireciona para Discord OAuth |
| GET | `/auth/discord/callback` | Callback OAuth — define cookie `p2s_session` |

## Endpoints do usuário

Requerem cookie `p2s_session`.

| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/link/wallet` | Vincular endereço `ban_`. Body: `{ "banano_address": "ban_..." }` |
| POST | `/me/reverify` | Re-disparar verificação Yunite |
| GET | `/me/status` | Status atual do usuário, carteira, recompensas acumuladas |
| GET | `/me/payouts` | Histórico de pagamentos do usuário |
| GET | `/me/accruals` | Histórico de acumulações do usuário |

## API pública

Sem necessidade de autenticação.

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/leaderboard` | Top jogadores por abates e ganhos |
| GET | `/api/feed` | Feed de atividade recente (pagamentos, acumulações) |
| GET | `/api/donate-info` | Endereço da carteira do operador + saldo para doações |
| GET | `/api/scheduler/countdown` | Segundos até o próximo ciclo de acumulação/liquidação |
| GET | `/api/donations` | Progresso de doações, marcos, multiplicador atual |
| GET | `/config/product` | Configuração pública do produto (nome do app, feature flags) |

## Endpoints administrativos

Requerem cookie `p2s_admin`.

| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/admin/login` | Login admin. Body: `{ "email": "..." }` |
| POST | `/admin/reverify` | Forçar re-verificação de usuário. Body: `{ "discord_id": "..." }` |
| POST | `/admin/payouts/retry` | Retentar pagamento falho. Body: `{ "payout_id": 123 }` |
| GET | `/admin/audit` | Log de auditoria admin |
| GET | `/admin/stats` | Estatísticas do sistema |
| GET | `/admin/health/extended` | Verificação de saúde estendida |
| POST | `/admin/config/operator-seed` | Definir seed criptografado do operador |
| GET | `/admin/config/operator-seed/status` | Verificar se seed do operador está configurado |
| GET | `/admin/scheduler/status` | Estado atual do agendador |
| POST | `/admin/scheduler/trigger` | Disparar execução do agendador |
| POST | `/admin/scheduler/settle` | Disparar apenas liquidação |
| GET | `/admin/scheduler/config` | Obter configuração do agendador |
| POST | `/admin/scheduler/config` | Atualizar configuração do agendador |
| GET | `/admin/payout/config` | Obter configuração de pagamentos (ban_per_kill, limites) |
| POST | `/admin/payout/config` | Atualizar configuração de pagamentos |

## Endpoints demo

Disponíveis em modo desenvolvimento/demo.

| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/auth/demo-login` | Login sem Discord OAuth |
| POST | `/demo/seed` | Seed do BD com dados de teste |
| POST | `/demo/run-scheduler` | Executar ciclo do agendador imediatamente |
| POST | `/demo/clear` | Limpar todos os dados demo |

## Depuração

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/debug/yunite` | Testar conectividade com Yunite API |

## Notas

- **Modo dry-run** (`P2S_DRY_RUN=true`): pula chamadas API externas e transferências blockchain.
- Sessões são assinadas com HMAC usando `SESSION_SECRET` e incluem expiração.
- Respostas de erro usam códigos HTTP padrão (400, 401, 403, 404).
