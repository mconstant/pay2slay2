# Pay2Slay

<p align="center">
  <img src="static/logo.png" alt="Logo de Pay2Slay" width="180" />
</p>

<p align="center">
  <strong>Gana Banano por eliminar en Fortnite.</strong><br/>
  Un grifo de criptomonedas que paga a los jugadores en BAN por cada eliminación.
</p>

<p align="center">
  https://pay2slay.cc
</p>

<p align="center">
  <a href="README.md">English</a> ·
  <a href="README.uk.md">Українська</a> ·
  <strong>Español</strong> ·
  <a href="README.pt.md">Português</a> ·
  <a href="README.ja.md">日本語</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.13-blue?style=flat" alt="Python 3.13" />
  <img src="https://img.shields.io/badge/framework-FastAPI-009688?style=flat" alt="FastAPI" />
  <img src="https://img.shields.io/badge/chain-Banano-FBDD11?style=flat" alt="Banano" />
  <img src="https://img.shields.io/badge/deploy-Akash-red?style=flat" alt="Akash" />
</p>

---

## Capturas de pantalla

| Tabla de clasificación | Donaciones |
|:----------------------:|:----------:|
| ![Tabla de clasificación](docs/screenshots/leaderboard.png) | ![Donaciones](docs/screenshots/donations.png) |

## Cómo funciona

1. **Inicia sesión con Discord** — OAuth te autentica, Yunite vincula tu Discord con tu cuenta de Epic Games.
2. **Vincula tu billetera Banano** — Pega tu dirección `ban_` (Kalium, Banano Vault, etc.).
3. **Juega Fortnite** — El planificador rastrea tus eliminaciones y te paga **0.05 BAN por eliminación** (tasa base), liquidado automáticamente en tu billetera.

Los pagos se ajustan dinámicamente mediante un **factor de sostenibilidad** y **hitos de donación**. Los límites diarios y semanales de eliminaciones mantienen el fondo saludable.

## Características

- **Tabla de clasificación en vivo** con conteo de eliminaciones, ganancias y feed de actividad
- **Hitos de donación** — 10 niveles desde Novato (1.0x) hasta Singularidad de Potasio (1.5x) con meta de 10K BAN
- **Factor de sostenibilidad** — ajuste dinámico de pagos basado en la relación donación-gasto
- **Economía transparente** — desglose de fórmulas en vivo en la página de Donaciones
- **Límites diarios/semanales de pago** (100 / 500 eliminaciones) con heurísticas de detección de abuso
- **Panel de administración** — control del planificador, configuración de pagos, gestión de seed del operador, registro de auditoría
- **Modo demo** — ejecución simulada completa con datos de prueba para desarrollo local
- **Seguridad de la cadena de suministro** — imágenes firmadas con Cosign, atestación SBOM, verificación de digest

## Economía del grifo

Pay2Slay usa una fórmula de pago autobalanceada para mantener la sostenibilidad del grifo:

```
tasa_efectiva = tasa_base × multiplicador_de_hito × factor_de_sostenibilidad
```

| Parámetro | Valor | Notas |
|-----------|-------|-------|
| Tasa base | **0.05 BAN/eliminación** | Configurado en `payout.yaml` |
| Límite diario de eliminaciones | **100 eliminaciones** (≈5 BAN/día) | Límite por jugador |
| Límite semanal de eliminaciones | **500 eliminaciones** (≈25 BAN/semana) | Límite por jugador |
| Fondo semilla | **~1,337 BAN** | Balance inicial del operador |
| Meta de donaciones | **10,000 BAN** | Desbloquea todos los niveles de hitos |

### Factor de sostenibilidad

El factor de sostenibilidad ajusta automáticamente los pagos basándose en la relación de ingresos (fondo semilla + donaciones) a egresos (total pagado):

```
sostenibilidad = clamp((fondo_semilla + total_donado) / total_pagado, 0.1, 2.0)
```

- **≥ 1.0x** (verde) — Las donaciones mantienen el ritmo o superan; pagos completos o bonificados
- **0.5–1.0x** (ámbar) — Los pagos superan las donaciones; tasa reducida
- **< 0.5x** (rojo) — Fondo agotándose; reducción significativa para extender la vida

### Niveles de hitos

| Nivel | Umbral | Multiplicador |
|-------|--------|---------------|
| 🌱 Novato | 0 BAN | 1.00x |
| 🩸 Primera sangre | 100 BAN | 1.05x |
| 📦 Botín | 500 BAN | 1.10x |
| 🪂 Suministro | 1,000 BAN | 1.15x |
| ⛈️ Oleada de tormenta | 2,500 BAN | 1.20x |
| 🛩️ Lanzamiento aéreo | 5,000 BAN | 1.25x |
| 👑 Victoria Royale | 10,000 BAN | 1.30x |
| 💎 Rareza mítica | 25,000 BAN | 1.40x |
| 🐒 El mono despierta | 50,000 BAN | 1.45x |
| 🍌 Singularidad de potasio | 100,000 BAN | 1.50x |

Todos los datos económicos se muestran de forma transparente en la página de Donaciones, incluyendo la fórmula en vivo, el indicador de sostenibilidad y el desglose del fondo.

## Inicio rápido

```bash
git clone https://github.com/mconstant/pay2slay2.git && cd pay2slay2
python3 -m venv .venv && source .venv/bin/activate
pip install -e '.[dev]'

# Terminal 1: Servidor API
make api        # http://localhost:8000

# Terminal 2: Planificador
make scheduler  # métricas en :8001
```

Ejecuta en **modo dry-run** por defecto — no se necesitan claves API reales ni BAN para desarrollo local. Ver [docs/quickstart.es.md](docs/quickstart.es.md) para la guía completa.

## Configuración

Archivos YAML en `configs/`:

| Archivo | Controla |
|---------|----------|
| `payout.yaml` | `ban_per_kill`, `daily_payout_cap`, `weekly_payout_cap`, `seed_fund_ban`, intervalo del planificador |
| `integrations.yaml` | Banano RPC, Discord OAuth, Yunite, Fortnite API, heurísticas de abuso |
| `product.yaml` | Nombre de la app, feature flags, URL de invitación Discord |

Variables de entorno clave:

| Variable | Por defecto | Notas |
|----------|-------------|-------|
| `DATABASE_URL` | `sqlite:///pay2slay.db` | PostgreSQL soportado para prod |
| `P2S_DRY_RUN` | `true` | Establecer `false` para pagos reales |
| `SESSION_SECRET` | `dev-secret` | **Cambiar en producción** |
| `P2S_INTERVAL_SECONDS` | `1200` | Intervalo del ciclo del planificador |
| `P2S_METRICS_PORT` | `8001` | Métricas Prometheus |

## Objetivos Make

| Objetivo | Acción |
|----------|--------|
| `make api` | Iniciar API con uvicorn --reload |
| `make scheduler` | Iniciar ciclo del planificador |
| `make test` | Ejecutar pytest |
| `make lint` | Ejecutar ruff |
| `make type` | Ejecutar mypy |
| `make all` | lint + type + test |
| `make ci` | Pipeline CI completo |

## Despliegue (Akash Network)

Contenedor único en [Akash](https://akash.network) ejecutando API + planificador. Las transacciones Banano usan el RPC público de Kalium — no se requiere nodo propio.

### Requisitos previos

1. Billetera Akash con AKT ([configuración de Keplr](#configuración-de-billetera-akash))
2. GitHub CLI (`gh auth login`)
3. Dominio con DNS bajo tu control

### Secretos de GitHub

| Secreto | Descripción |
|---------|-------------|
| `AKASH_MNEMONIC` | Mnemónica de 24 palabras de la billetera |
| `AKASH_CERT` | Certificado TLS de cliente (vía workflow `rotate-akash-cert`) |
| `GH_PAT` | GitHub PAT con scope `repo` |
| `SESSION_SECRET` | `openssl rand -hex 32` |
| `DISCORD_CLIENT_ID` | App Discord OAuth |
| `DISCORD_CLIENT_SECRET` | App Discord OAuth |
| `DISCORD_REDIRECT_URI` | `https://tudominio.com/auth/discord/callback` |
| `YUNITE_API_KEY` | Resolución de cuentas Epic |
| `FORTNITE_API_KEY` | Clave fortnite-api.com |

### Variables de GitHub

| Variable | Descripción |
|----------|-------------|
| `AKASH_ACCOUNT_ADDRESS` | Tu dirección `akash1...` |
| `AKASH_CERT_ID` | Establecida por el workflow rotate-cert |
| `YUNITE_GUILD_ID` | ID del servidor Discord |
| `P2S_OPERATOR_ACCOUNT` | Dirección del operador `ban_` |
| `ADMIN_DISCORD_USERNAMES` | Nombres de usuario admin separados por coma |

### Desplegar

```bash
gh workflow run deploy-akash.yml -f domain_name=pay2slay.cc -f image_tag=latest
```

Apunta tu CNAME de dominio al hostname del proveedor Akash de la salida del workflow. TLS se maneja automáticamente vía Let's Encrypt.

### Docker (local)

```bash
docker build -t pay2slay:dev .
docker run -p 8000:8000 --env-file .env pay2slay:dev
```

Establecer `PAY2SLAY_AUTO_MIGRATE=1` para ejecutar migraciones Alembic al iniciar.

### Configuración de billetera Akash

1. Instala [Keplr](https://www.keplr.app/) y guarda tu mnemónica de 24 palabras.
2. Habilita Akash Network en Keplr.
3. Fondea con AKT vía exchange o swap IBC en [Osmosis](https://app.osmosis.zone).

### Rotación de certificados

```bash
make rotate-akash-cert
```

### Seguridad de la cadena de suministro

Las imágenes están firmadas con Cosign (sin clave/Sigstore) y atestadas con SBOM (Syft/SPDX). El workflow de rollback reutiliza imágenes existentes sin reconstruir.

## Stack tecnológico

| Capa | Tecnología |
|------|-----------|
| Backend | Python 3.13, FastAPI, SQLAlchemy, Alembic |
| Base de datos | SQLite (dev), PostgreSQL (prod) |
| Blockchain | Banano vía bananopie / Kalium RPC |
| Autenticación | Discord OAuth + mapeo Epic vía Yunite |
| Estadísticas | Fortnite API (fortnite-api.com) |
| Observabilidad | Prometheus, OpenTelemetry |
| Despliegue | Docker, Akash Network, Terraform |
| Seguridad | Cosign, Syft SBOM, guardas de digest |

## Documentación

| Documento | Descripción |
|-----------|-------------|
| [Inicio rápido](docs/quickstart.es.md) | Guía completa de configuración local |
| [Referencia API](docs/api.es.md) | Todos los endpoints |
| [Modelo de datos](docs/data-model.md) | Esquema de base de datos |
| [Runbook](docs/runbook.md) | Operaciones en producción |
| [Política de privacidad](docs/PRIVACY.es.md) | Manejo de datos |
| [Seguridad](SECURITY.md) | Reporte de vulnerabilidades, endurecimiento |
| [Contribuir](CONTRIBUTING.md) | Flujo de trabajo, estilo de código |

## Licencia

[MIT](LICENSE)
