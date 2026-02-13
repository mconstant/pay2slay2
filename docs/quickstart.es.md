# Inicio rápido

Esta guía te ayuda a ejecutar la API y el planificador localmente en modo dry-run.

## 1) Configuración
Crea y activa un entorno virtual:
  - macOS/Linux (zsh):
    - `python3 -m venv .venv`
    - `source .venv/bin/activate`
  - Instala el proyecto y herramientas de desarrollo:
    - `pip install -e .[dev]`

## 2) Entorno
Copia `.env.example` a `.env` y ajusta según sea necesario, o exporta variables manualmente.

Core (por defecto):
  - `DATABASE_URL=sqlite:///pay2slay.db`
  - `SESSION_SECRET=dev-secret` (CAMBIAR en prod)
  - `P2S_DRY_RUN=true` (establecer `false` para usar APIs reales)
  - `P2S_OPERATOR_ACCOUNT=` (requerido solo cuando dry-run=false para verificación de balance)
  - `P2S_METRICS_PORT=8001`
  - `P2S_INTERVAL_SECONDS=1200` (ciclo del planificador)

Integraciones externas (requeridas con dry-run=false):
  - `YUNITE_API_KEY=`
  - `YUNITE_GUILD_ID=`
  - `FORTNITE_API_KEY=`
  - `DISCORD_CLIENT_ID=`
  - `DISCORD_CLIENT_SECRET=`
  - `DISCORD_REDIRECT_URI=http://localhost:3000/auth/discord/callback`

Observabilidad opcional:
  - `OTEL_EXPORTER_OTLP_ENDPOINT=` o `PAY2SLAY_OTLP_ENDPOINT=`
  - `PAY2SLAY_METRICS_EXEMPLARS=1`

## 3) Ejecutar la API
  - `uvicorn src.api.app:create_app --reload --port 8000`
  - Salud: http://localhost:8000/healthz

## 4) Ejecutar el planificador
  - Inicia un servidor de métricas Prometheus en `P2S_METRICS_PORT`.
  - Ejemplo (dry-run, intervalo 10s, métricas en 8002):
    - `P2S_INTERVAL_SECONDS=10 P2S_DRY_RUN=true P2S_METRICS_PORT=8002 python -m src.jobs`
  - Detener con Ctrl-C.
  - Métricas: http://localhost:8002/

## 5) Ciclos de desarrollo
  - Tests: `pytest -q`
  - Lint: `ruff check .`
  - Tipos: `mypy`

## 6) Migraciones de base de datos
Si usas Alembic (Postgres / BD persistente) puedes aplicar migraciones:
```
PAY2SLAY_AUTO_MIGRATE=1 python -m src.api.app  # dispara upgrade al iniciar
```
O manualmente:
```
alembic upgrade head
```

## 7) Build de imagen y firma (cadena de suministro)
Construir imagen de contenedor localmente:
```
docker build -t pay2slay:local .
```
Generar SBOM (Syft) y firmar (Cosign) (ejemplo):
```
syft packages pay2slay:local -o spdx-json > sbom.json
cosign sign --key cosign.key pay2slay:local
cosign attest --predicate sbom.json --type spdxjson pay2slay:local
```
Verificar:
```
cosign verify pay2slay:local
```

## 8) Despliegue (Akash)
Ver la sección **Despliegue** en `README.es.md` para instrucciones completas. Resumen rápido:
1. Configura todos los secretos y variables de GitHub (ver tablas en README).
2. Actualiza la URI de redirección de la app Discord a `https://tudominio.com/auth/discord/callback`.
3. Ejecuta: `gh workflow run deploy-akash.yml -f domain_name=tudominio.com -f image_tag=latest`
4. Apunta el CNAME de tu dominio al hostname del proveedor Akash mostrado en la salida del workflow.

## 9) Atajos de Make
  - `make api` — iniciar API (reload)
  - `make scheduler` — iniciar planificador (lee env)
  - `make test` — ejecutar tests
  - `make lint` — lint
  - `make type` — verificación de tipos
  - `make all` — lint + type + tests

## 10) Notas de arquitectura
- El contenedor ejecuta tanto el servidor API (uvicorn) como el planificador como proceso de fondo vía `docker-entrypoint.sh`.
- Las transacciones Banano usan el RPC público de Kalium (`https://kaliumapi.appditto.com/api`) — no se necesita nodo propio.
- El seed del operador para firmar transacciones Banano se almacena cifrado en la tabla `SecureConfig` de la BD (usa el panel de admin para configurarlo).

## 11) Etiquetado inmutable y rollback (workflows CI)
El workflow de build (trigger push) produce una imagen etiquetada con el SHA git completo de 40 caracteres y una etiqueta corta de 12 caracteres. Los workflows de despliegue y rollback solo aceptan etiquetas de SHA completo (inmutables) y garantizan:
 - Verificación de digest pre/post push (en tiempo de build) para detectar manipulación.
