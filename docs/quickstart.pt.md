# Início rápido

Este guia ajuda você a executar a API e o agendador localmente em modo dry-run.

## 1) Configuração
Crie e ative um ambiente virtual:
  - macOS/Linux (zsh):
    - `python3 -m venv .venv`
    - `source .venv/bin/activate`
  - Instale o projeto e ferramentas de desenvolvimento:
    - `pip install -e .[dev]`

## 2) Ambiente
Copie `.env.example` para `.env` e ajuste conforme necessário, ou exporte variáveis manualmente.

Core (padrão):
  - `DATABASE_URL=sqlite:///pay2slay.db`
  - `SESSION_SECRET=dev-secret` (ALTERE em prod)
  - `P2S_DRY_RUN=true` (defina `false` para usar APIs reais)
  - `P2S_OPERATOR_ACCOUNT=` (necessário apenas quando dry-run=false para verificação de saldo)
  - `P2S_METRICS_PORT=8001`
  - `P2S_INTERVAL_SECONDS=1200` (ciclo do agendador)

Integrações externas (necessárias com dry-run=false):
  - `YUNITE_API_KEY=`
  - `YUNITE_GUILD_ID=`
  - `FORTNITE_API_KEY=`
  - `DISCORD_CLIENT_ID=`
  - `DISCORD_CLIENT_SECRET=`
  - `DISCORD_REDIRECT_URI=http://localhost:3000/auth/discord/callback`

Observabilidade opcional:
  - `OTEL_EXPORTER_OTLP_ENDPOINT=` ou `PAY2SLAY_OTLP_ENDPOINT=`
  - `PAY2SLAY_METRICS_EXEMPLARS=1`

## 3) Executar a API
  - `uvicorn src.api.app:create_app --reload --port 8000`
  - Saúde: http://localhost:8000/healthz

## 4) Executar o agendador
  - Inicia um servidor de métricas Prometheus em `P2S_METRICS_PORT`.
  - Exemplo (dry-run, intervalo 10s, métricas em 8002):
    - `P2S_INTERVAL_SECONDS=10 P2S_DRY_RUN=true P2S_METRICS_PORT=8002 python -m src.jobs`
  - Pare com Ctrl-C.
  - Métricas: http://localhost:8002/

## 5) Ciclos de desenvolvimento
  - Testes: `pytest -q`
  - Lint: `ruff check .`
  - Tipos: `mypy`

## 6) Migrações de banco de dados
Se usar Alembic (Postgres / BD persistente) você pode aplicar migrações:
```
PAY2SLAY_AUTO_MIGRATE=1 python -m src.api.app  # dispara upgrade na inicialização
```
Ou manualmente:
```
alembic upgrade head
```

## 7) Build de imagem e assinatura (cadeia de suprimentos)
Build de imagem de container local:
```
docker build -t pay2slay:local .
```
Gerar SBOM (Syft) e assinar (Cosign) (exemplo):
```
syft packages pay2slay:local -o spdx-json > sbom.json
cosign sign --key cosign.key pay2slay:local
cosign attest --predicate sbom.json --type spdxjson pay2slay:local
```
Verificar:
```
cosign verify pay2slay:local
```

## 8) Deploy (Akash)
Veja a seção **Deploy** em `README.pt.md` para instruções completas. Resumo rápido:
1. Configure todos os segredos e variáveis do GitHub (veja tabelas no README).
2. Atualize a URI de redirecionamento do app Discord para `https://seudominio.com/auth/discord/callback`.
3. Execute: `gh workflow run deploy-akash.yml -f domain_name=seudominio.com -f image_tag=latest`
4. Aponte o CNAME do seu domínio para o hostname do provedor Akash na saída do workflow.

## 9) Atalhos Make
  - `make api` — iniciar API (reload)
  - `make scheduler` — iniciar agendador (lê env)
  - `make test` — executar testes
  - `make lint` — lint
  - `make type` — verificação de tipos
  - `make all` — lint + type + testes

## 10) Notas de arquitetura
- O container executa tanto o servidor API (uvicorn) quanto o agendador como processo em background via `docker-entrypoint.sh`.
- Transações Banano usam o RPC público do Kalium (`https://kaliumapi.appditto.com/api`) — nenhum nó próprio necessário.
- O seed do operador para assinar transações Banano é armazenado criptografado na tabela `SecureConfig` do BD (use o painel admin para configurá-lo).

## 11) Tagging imutável e rollback (workflows CI)
O workflow de build (trigger push) produz uma imagem taggeada com o SHA git completo de 40 caracteres e tag curta de 12 caracteres. Workflows de deploy e rollback aceitam apenas tags de SHA completo (imutáveis) e garantem:
 - Verificação de digest pré/pós push (em tempo de build) para detectar adulteração.
