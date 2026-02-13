# Referencia API

Backend FastAPI. Todas las sesiones usan cookies HttpOnly, SameSite=Lax.

## Autenticación

| Cookie | Establecida por | Propósito |
|--------|-----------------|-----------|
| `p2s_session` | `/auth/discord/callback` | Sesión de usuario |
| `p2s_admin` | `/admin/login` | Sesión de administrador |

## Salud e infraestructura

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/healthz` | Verificación de salud → `{ status: "ok" }` |
| GET | `/livez` | Sonda de vida |
| GET | `/readyz` | Sonda de preparación |
| GET | `/metrics` | Métricas Prometheus |

## Autenticación

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/auth/discord/login` | Redirige a Discord OAuth |
| GET | `/auth/discord/callback` | Callback OAuth — establece cookie `p2s_session` |

## Endpoints de usuario

Requieren cookie `p2s_session`.

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/link/wallet` | Vincular una dirección `ban_`. Body: `{ "banano_address": "ban_..." }` |
| POST | `/me/reverify` | Re-disparar verificación Yunite |
| GET | `/me/status` | Estado actual del usuario, billetera, recompensas acumuladas |
| GET | `/me/payouts` | Historial de pagos del usuario |
| GET | `/me/accruals` | Historial de acumulaciones del usuario |

## API pública

No requiere autenticación.

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/leaderboard` | Top jugadores por eliminaciones y ganancias |
| GET | `/api/feed` | Feed de actividad reciente (pagos, acumulaciones) |
| GET | `/api/donate-info` | Dirección de billetera del operador + balance para donaciones |
| GET | `/api/scheduler/countdown` | Segundos hasta el próximo ciclo de acumulación/liquidación |
| GET | `/api/donations` | Progreso de donaciones, hitos, multiplicador actual |
| GET | `/config/product` | Configuración pública del producto (nombre de app, feature flags) |

## Endpoints de administrador

Requieren cookie `p2s_admin`.

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/admin/login` | Login de admin. Body: `{ "email": "..." }` |
| POST | `/admin/reverify` | Forzar re-verificación de usuario. Body: `{ "discord_id": "..." }` |
| POST | `/admin/payouts/retry` | Reintentar pago fallido. Body: `{ "payout_id": 123 }` |
| GET | `/admin/audit` | Registro de auditoría de admin |
| GET | `/admin/stats` | Estadísticas del sistema |
| GET | `/admin/health/extended` | Verificación de salud extendida |
| POST | `/admin/config/operator-seed` | Establecer seed cifrada del operador |
| GET | `/admin/config/operator-seed/status` | Verificar si el seed del operador está configurado |
| GET | `/admin/scheduler/status` | Estado actual del planificador |
| POST | `/admin/scheduler/trigger` | Disparar ejecución del planificador |
| POST | `/admin/scheduler/settle` | Disparar solo liquidación |
| GET | `/admin/scheduler/config` | Obtener configuración del planificador |
| POST | `/admin/scheduler/config` | Actualizar configuración del planificador |
| GET | `/admin/payout/config` | Obtener configuración de pagos (ban_per_kill, límites) |
| POST | `/admin/payout/config` | Actualizar configuración de pagos |

## Endpoints demo

Disponibles en modo desarrollo/demo.

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/auth/demo-login` | Login sin Discord OAuth |
| POST | `/demo/seed` | Sembrar BD con datos de prueba |
| POST | `/demo/run-scheduler` | Ejecutar ciclo del planificador inmediatamente |
| POST | `/demo/clear` | Limpiar todos los datos demo |

## Depuración

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/debug/yunite` | Probar conectividad con Yunite API |

## Notas

- **Modo dry-run** (`P2S_DRY_RUN=true`): omite llamadas a APIs externas y transferencias blockchain.
- Las sesiones están firmadas con HMAC usando `SESSION_SECRET` e incluyen expiración.
- Las respuestas de error usan códigos HTTP estándar (400, 401, 403, 404).
