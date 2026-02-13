# Швидкий старт

Цей посібник допоможе вам запустити API та планувальник локально в режимі dry-run.

## 1) Налаштування
Створіть та активуйте віртуальне оточення:
  - macOS/Linux (zsh):
    - `python3 -m venv .venv`
    - `source .venv/bin/activate`
  - Встановіть проект та інструменти розробки:
    - `pip install -e .[dev]`

## 2) Оточення
Скопіюйте `.env.example` в `.env` та налаштуйте за потреби, або експортуйте змінні вручну.

Основні (за замовчуванням):
  - `DATABASE_URL=sqlite:///pay2slay.db`
  - `SESSION_SECRET=dev-secret` (ЗМІНІТЬ на production)
  - `P2S_DRY_RUN=true` (встановіть `false` для використання реальних API)
  - `P2S_OPERATOR_ACCOUNT=` (потрібен лише коли dry-run=false для перевірки балансу)
  - `P2S_METRICS_PORT=8001`
  - `P2S_INTERVAL_SECONDS=1200` (цикл планувальника)

Зовнішні інтеграції (потрібні після вимкнення dry-run):
  - `YUNITE_API_KEY=`
  - `YUNITE_GUILD_ID=`
  - `FORTNITE_API_KEY=`
  - `DISCORD_CLIENT_ID=`
  - `DISCORD_CLIENT_SECRET=`
  - `DISCORD_REDIRECT_URI=http://localhost:3000/auth/discord/callback`

Опціональна спостережуваність:
  - `OTEL_EXPORTER_OTLP_ENDPOINT=` або `PAY2SLAY_OTLP_ENDPOINT=`
  - `PAY2SLAY_METRICS_EXEMPLARS=1`

## 3) Запуск API
  - `uvicorn src.api.app:create_app --reload --port 8000`
  - Перевірка здоров'я: http://localhost:8000/healthz

## 4) Запуск планувальника
  - Запускає сервер метрик Prometheus на `P2S_METRICS_PORT`.
  - Приклад (dry-run, інтервал 10с, метрики на 8002):
    - `P2S_INTERVAL_SECONDS=10 P2S_DRY_RUN=true P2S_METRICS_PORT=8002 python -m src.jobs`
  - Зупиніть за допомогою Ctrl-C.
  - Метрики: http://localhost:8002/

## 5) Цикли розробки
  - Тести: `pytest -q`
  - Лінтер: `ruff check .`
  - Типи: `mypy`

## 6) Міграції бази даних
Якщо використовуєте Alembic (Postgres / стійка БД), можете застосувати міграції:
```
PAY2SLAY_AUTO_MIGRATE=1 python -m src.api.app  # запускає оновлення при старті
```
Або вручну:
```
alembic upgrade head
```

## 7) Збірка образу та підписання (ланцюг поставок)
Збірка контейнерного образу локально:
```
docker build -t pay2slay:local .
```
Генерація SBOM (Syft) та підписання (Cosign) (приклад):
```
syft packages pay2slay:local -o spdx-json > sbom.json
cosign sign --key cosign.key pay2slay:local
cosign attest --predicate sbom.json --type spdxjson pay2slay:local
```
Перевірка:
```
cosign verify pay2slay:local
```

## 8) Деплой (Akash)
Дивіться розділ **Деплой** в `README.uk.md` для повних інструкцій. Короткий огляд:
1. Встановіть всі секрети та змінні GitHub (дивіться таблиці в README).
2. Оновіть URI перенаправлення Discord додатку на `https://yourdomain.com/auth/discord/callback`.
3. Запустіть: `gh workflow run deploy-akash.yml -f domain_name=yourdomain.com -f image_tag=latest`
4. Направте CNAME вашого домену на хостнейм провайдера Akash з виводу воркфлоу.

## 9) Make-скорочення
  - `make api` — запустити API (reload)
  - `make scheduler` — запустити планувальник (читає env)
  - `make test` — запустити тести
  - `make lint` — лінтер
  - `make type` — перевірка типів
  - `make all` — lint + type + тести

## 10) Нотатки про архітектуру
- Контейнер запускає і API сервер (uvicorn), і планувальник як фоновий процес через `docker-entrypoint.sh`.
- Транзакції Banano використовують публічний Kalium RPC (`https://kaliumapi.appditto.com/api`) — власний вузол не потрібен.
- Seed оператора для підпису транзакцій Banano зберігається зашифрованим у таблиці `SecureConfig` БД (використовуйте панель адміністратора для його встановлення).

## 11) Незмінне тегування та відкат (воркфлоу CI)
Воркфлоу збірки (тригер push) створює образ з тегом повного 40-символьного git SHA та коротким 12-символьним тегом. Воркфлоу деплою та відкату приймають лише теги повного SHA (незмінні) та забезпечують:
 - Перевірку дайджесту до/після push (під час збірки) для виявлення підробки.
