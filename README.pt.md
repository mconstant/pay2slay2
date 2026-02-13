# Pay2Slay

<p align="center">
  <img src="static/logo.png" alt="Logo Pay2Slay" width="180" />
</p>

<p align="center">
  <strong>Ganhe Banano por abates no Fortnite.</strong><br/>
  Uma faucet de criptomoedas que paga jogadores em BAN por cada eliminação.
</p>

<p align="center">
  https://pay2slay.cc
</p>

<p align="center">
  <a href="README.md">English</a> ·
  <a href="README.uk.md">Українська</a> ·
  <a href="README.es.md">Español</a> ·
  <strong>Português</strong> ·
  <a href="README.ja.md">日本語</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.13-blue?style=flat" alt="Python 3.13" />
  <img src="https://img.shields.io/badge/framework-FastAPI-009688?style=flat" alt="FastAPI" />
  <img src="https://img.shields.io/badge/chain-Banano-FBDD11?style=flat" alt="Banano" />
  <img src="https://img.shields.io/badge/deploy-Akash-red?style=flat" alt="Akash" />
</p>

---

## Capturas de tela

| Classificação | Doações |
|:-------------:|:-------:|
| ![Classificação](docs/screenshots/leaderboard.png) | ![Doações](docs/screenshots/donations.png) |

## Como funciona

1. **Login com Discord** — OAuth autentica você, Yunite vincula seu Discord à sua conta Epic Games.
2. **Vincule sua carteira Banano** — Cole seu endereço `ban_` (Kalium, Banano Vault, etc.).
3. **Jogue Fortnite** — O agendador rastreia seus abates e paga **0.05 BAN por abate** (taxa base), liquidado automaticamente na sua carteira.

Os pagamentos são ajustados dinamicamente por um **fator de sustentabilidade** e **marcos de doação**. Limites diários e semanais de abates mantêm o fundo saudável.

## Recursos

- **Classificação ao vivo** com contagem de abates, ganhos e feed de atividade
- **Marcos de doação** — 10 níveis do Novato (1.0x) à Singularidade do Potássio (1.5x) com meta de 10K BAN
- **Fator de sustentabilidade** — ajuste dinâmico de pagamentos baseado na relação doação-gasto
- **Economia transparente** — detalhamento de fórmulas ao vivo na página de Doações
- **Limites diários/semanais de pagamento** (100 / 500 abates) com heurísticas de detecção de abuso
- **Painel administrativo** — controle do agendador, configuração de pagamentos, gestão de seed do operador, log de auditoria
- **Modo demo** — simulação completa com dados de teste para desenvolvimento local
- **Segurança da cadeia de suprimentos** — imagens assinadas com Cosign, atestação SBOM, verificação de digest

## Economia da faucet

Pay2Slay usa uma fórmula de pagamento autobalanceada para manter a sustentabilidade da faucet:

```
taxa_efetiva = taxa_base × multiplicador_de_marco × fator_de_sustentabilidade
```

| Parâmetro | Valor | Notas |
|-----------|-------|-------|
| Taxa base | **0.05 BAN/abate** | Configurado em `payout.yaml` |
| Limite diário de abates | **100 abates** (≈5 BAN/dia) | Limite por jogador |
| Limite semanal de abates | **500 abates** (≈25 BAN/semana) | Limite por jogador |
| Fundo inicial | **~1,337 BAN** | Saldo inicial do operador |
| Meta de doações | **10,000 BAN** | Desbloqueia todos os níveis de marcos |

### Fator de sustentabilidade

O fator de sustentabilidade ajusta automaticamente os pagamentos baseado na relação de entrada (fundo inicial + doações) e saída (total pago):

```
sustentabilidade = clamp((fundo_inicial + total_doado) / total_pago, 0.1, 2.0)
```

- **≥ 1.0x** (verde) — Doações acompanhando ou à frente; pagamentos completos ou bonificados
- **0.5–1.0x** (âmbar) — Pagamentos ultrapassando doações; taxa reduzida
- **< 0.5x** (vermelho) — Fundo esgotando; redução significativa para estender a vida útil

### Níveis de marcos

| Nível | Limite | Multiplicador |
|-------|--------|---------------|
| 🌱 Novato | 0 BAN | 1.00x |
| 🩸 Primeiro sangue | 100 BAN | 1.05x |
| 📦 Saque | 500 BAN | 1.10x |
| 🪂 Suprimento | 1,000 BAN | 1.15x |
| ⛈️ Onda de tempestade | 2,500 BAN | 1.20x |
| 🛩️ Lançamento aéreo | 5,000 BAN | 1.25x |
| 👑 Vitória Royale | 10,000 BAN | 1.30x |
| 💎 Raridade mítica | 25,000 BAN | 1.40x |
| 🐒 O macaco desperta | 50,000 BAN | 1.45x |
| 🍌 Singularidade do potássio | 100,000 BAN | 1.50x |

Todos os dados econômicos são exibidos de forma transparente na página de Doações, incluindo a fórmula ao vivo, indicador de sustentabilidade e detalhamento do fundo.

## Início rápido

```bash
git clone https://github.com/mconstant/pay2slay2.git && cd pay2slay2
python3 -m venv .venv && source .venv/bin/activate
pip install -e '.[dev]'

# Terminal 1: Servidor API
make api        # http://localhost:8000

# Terminal 2: Agendador
make scheduler  # métricas em :8001
```

Executa em **modo dry-run** por padrão — não precisa de chaves API reais ou BAN para desenvolvimento local. Veja [docs/quickstart.pt.md](docs/quickstart.pt.md) para o guia completo.

## Configuração

Arquivos YAML em `configs/`:

| Arquivo | Controla |
|---------|----------|
| `payout.yaml` | `ban_per_kill`, `daily_payout_cap`, `weekly_payout_cap`, `seed_fund_ban`, intervalo do agendador |
| `integrations.yaml` | Banano RPC, Discord OAuth, Yunite, Fortnite API, heurísticas de abuso |
| `product.yaml` | Nome do app, feature flags, URL de convite Discord |

Variáveis de ambiente chave:

| Variável | Padrão | Notas |
|----------|--------|-------|
| `DATABASE_URL` | `sqlite:///pay2slay.db` | PostgreSQL suportado para prod |
| `P2S_DRY_RUN` | `true` | Defina `false` para pagamentos reais |
| `SESSION_SECRET` | `dev-secret` | **Altere em produção** |
| `P2S_INTERVAL_SECONDS` | `1200` | Intervalo do ciclo do agendador |
| `P2S_METRICS_PORT` | `8001` | Métricas Prometheus |

## Alvos Make

| Alvo | Ação |
|------|------|
| `make api` | Iniciar API com uvicorn --reload |
| `make scheduler` | Iniciar ciclo do agendador |
| `make test` | Executar pytest |
| `make lint` | Executar ruff |
| `make type` | Executar mypy |
| `make all` | lint + type + test |
| `make ci` | Pipeline CI completo |

## Deploy (Akash Network)

Container único no [Akash](https://akash.network) executando API + agendador. Transações Banano usam o RPC público do Kalium — nenhum nó próprio necessário.

### Pré-requisitos

1. Carteira Akash com AKT ([configuração Keplr](#configuração-da-carteira-akash))
2. GitHub CLI (`gh auth login`)
3. Domínio com DNS sob seu controle

### Segredos do GitHub

| Segredo | Descrição |
|---------|-----------|
| `AKASH_MNEMONIC` | Mnemônica de 24 palavras da carteira |
| `AKASH_CERT` | Certificado TLS do cliente (via workflow `rotate-akash-cert`) |
| `GH_PAT` | GitHub PAT com scope `repo` |
| `SESSION_SECRET` | `openssl rand -hex 32` |
| `DISCORD_CLIENT_ID` | App Discord OAuth |
| `DISCORD_CLIENT_SECRET` | App Discord OAuth |
| `DISCORD_REDIRECT_URI` | `https://seudominio.com/auth/discord/callback` |
| `YUNITE_API_KEY` | Resolução de contas Epic |
| `FORTNITE_API_KEY` | Chave fortnite-api.com |

### Variáveis do GitHub

| Variável | Descrição |
|----------|-----------|
| `AKASH_ACCOUNT_ADDRESS` | Seu endereço `akash1...` |
| `AKASH_CERT_ID` | Definido pelo workflow rotate-cert |
| `YUNITE_GUILD_ID` | ID do servidor Discord |
| `P2S_OPERATOR_ACCOUNT` | Endereço do operador `ban_` |
| `ADMIN_DISCORD_USERNAMES` | Nomes de admin separados por vírgula |

### Deploy

```bash
gh workflow run deploy-akash.yml -f domain_name=pay2slay.cc -f image_tag=latest
```

Aponte o CNAME do seu domínio para o hostname do provedor Akash na saída do workflow. TLS é tratado automaticamente via Let's Encrypt.

### Docker (local)

```bash
docker build -t pay2slay:dev .
docker run -p 8000:8000 --env-file .env pay2slay:dev
```

Defina `PAY2SLAY_AUTO_MIGRATE=1` para executar migrações Alembic na inicialização.

### Configuração da carteira Akash

1. Instale [Keplr](https://www.keplr.app/) e salve sua mnemônica de 24 palavras.
2. Habilite Akash Network no Keplr.
3. Financie com AKT via exchange ou swap IBC no [Osmosis](https://app.osmosis.zone).

### Rotação de certificados

```bash
make rotate-akash-cert
```

### Segurança da cadeia de suprimentos

Imagens são assinadas com Cosign (sem chave/Sigstore) e atestadas com SBOM (Syft/SPDX). Workflow de rollback reutiliza imagens existentes sem rebuild.

## Stack tecnológico

| Camada | Tecnologia |
|--------|-----------|
| Backend | Python 3.13, FastAPI, SQLAlchemy, Alembic |
| Banco de dados | SQLite (dev), PostgreSQL (prod) |
| Blockchain | Banano via bananopie / Kalium RPC |
| Autenticação | Discord OAuth + mapeamento Epic via Yunite |
| Estatísticas | Fortnite API (fortnite-api.com) |
| Observabilidade | Prometheus, OpenTelemetry |
| Deploy | Docker, Akash Network, Terraform |
| Segurança | Cosign, Syft SBOM, guardas de digest |

## Documentação

| Documento | Descrição |
|-----------|-----------|
| [Início rápido](docs/quickstart.pt.md) | Guia completo de configuração local |
| [Referência API](docs/api.pt.md) | Todos os endpoints |
| [Modelo de dados](docs/data-model.md) | Esquema do banco de dados |
| [Runbook](docs/runbook.md) | Operações em produção |
| [Política de privacidade](docs/PRIVACY.pt.md) | Tratamento de dados |
| [Segurança](SECURITY.md) | Relato de vulnerabilidades, hardening |
| [Contribuir](CONTRIBUTING.md) | Fluxo de trabalho, estilo de código |

## Licença

[MIT](LICENSE)
