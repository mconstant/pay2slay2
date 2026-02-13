# Política de Privacidad

Fecha de vigencia: 25-09-2025

Esta Política de Privacidad describe cómo el grifo auto-hospedable Pay2Slay (el "Software") procesa los datos de usuario. El objetivo es la máxima privacidad y la mínima retención de datos. Se espera que los desplegadores ("Operadores") sigan o mejoren estos principios.

## Principios rectores
- Minimización de datos: Solo almacenar lo estrictamente necesario para el cálculo correcto de recompensas, prevención de abuso y auditoría.
- Solo local por defecto: No se emiten telemetría, anuncios ni balizas de rastreo. Todas las métricas/trazas permanecen dentro de la infraestructura del operador a menos que se configure explícitamente.
- Efímero: Los datos volátiles o derivables (ej. estado de sesión, intercambios OAuth transitorios) no se persisten más allá de la necesidad funcional.
- Transparencia al usuario: Las categorías de datos y propósitos están documentados abajo; no hay procesamiento oculto.
- Amigable con la exclusión: Las funciones opcionales (exportación de trazas, analíticas extendidas) están desactivadas a menos que el operador las habilite.

## Categorías de datos
| Categoría | Ejemplos | Propósito | Retención | Notas |
|-----------|----------|-----------|-----------|-------|
| Identidad (Discord) | discord_user_id, username, flag de membresía de gremio | Elegibilidad + atribución de recompensas | Hasta solicitud de eliminación o purga del operador | No se solicitan scopes privilegiados más allá de identidad+verificación de gremio. |
| Identidad (Fortnite) | epic_account_id | Vincular actividad al usuario para deltas de eliminaciones | Hasta eliminación o desvinculación de cuenta | Originado vía mapeo Yunite; no se comparte externamente. |
| Billetera | Dirección Banano (primaria) | Entregar pagos | Hasta desvinculación o eliminación | Múltiples direcciones opcionales; solo la primaria para pagos. |
| Actividad de recompensas | RewardAccrual (kills, monto, epoch_minute) | Calcular pagos / auditar abuso | Hasta liquidación + (ventana de auditoría definida por operador) | Puede podarse después de la finalización del pago. |
| Registros de pago | monto, tx_hash, estado, metadatos de intentos | Responsabilidad financiera / reintento / resolución de disputas | Indefinido o según el operador | tx_hash puede ser público on-chain de todas formas. |
| Eventos de verificación | VerificationRecord (fuente, estado, marcas de tiempo) | Rastrear historial de verificación / resolución de disputas | Ventana rodante o indefinido según operador | Se puede recortar agresivamente (mantener la última exitosa). |
| Flags de abuso | flag_type, severity, detail | Proteger uso justo / integridad | Hasta limpieza o eliminación de usuario | Solo resúmenes heurísticos; sin almacenamiento de IP. |
| Registros de donación | DonationLedger (amount_ban, blocks_received, source) | Rastrear donaciones comunitarias, progreso de hitos | Indefinido o según operador | No se almacena identidad del donante; solo montos. |
| Código de región (aproximado) | ej. "eu", "na" | Analítica de abuso, estadísticas de distribución de pagos | Opcional; se puede desactivar | Derivado de header o mapeo IP aproximado; nunca geo precisa. |
| Logs (estructurados) | nombres de eventos, trace/span IDs (si habilitado) | Depuración y auditoría | Retención corta recomendada (ej. 7–30 días) | Excluir secretos vía helper de enmascaramiento. |
| Sesiones | Token de sesión HMAC (cookie) | Autenticar solicitudes subsiguientes | Solo en memoria / TTL de cookie | Tokens opacos y revocables limpiando cookie. |

## Lo que deliberadamente NO recopilamos
- Sin email, nombre real, fecha de nacimiento, identificación gubernamental, número de teléfono.
- Sin geolocalización precisa, retención de IP o IDs de analítica de terceros.
- Sin perfilado de comportamiento o segmentación de marketing.
- Sin datos biométricos o de categoría sensible.

## Funciones opcionales / controladas por el operador
| Función | Por defecto | Impacto en privacidad | Mitigación |
|---------|-------------|----------------------|------------|
| Exportación OpenTelemetry | Desactivado | Podría exportar spans (incluye nombres de ruta, tiempos) | Mantener endpoint de exportación interno o dejarlo desactivado |
| Middleware regional extendido | Activado (solo aproximado) | Código de región mínimo aproximado | Desactivar vía config si no se desea |
| Endpoint de métricas (/metrics) | Activado | Expone contadores agregados | Proteger vía política de red / gateway de auth |
| IDs de traza en logs | Activado (local) | Correlaciona eventos de solicitud | Evitar exportar logs a terceros sin revisión |

## Controles del sujeto de datos
Los operadores deben proporcionar (a través de su canal de despliegue):
- Derecho de acceso: Endpoint o proceso para que el usuario vea identidad y historial de pagos almacenados (parcialmente cubierto por endpoints existentes `/me/status`, `/me/payouts`).
- Derecho de supresión: Script del operador o acción de admin para eliminar (o anonimizar) usuario, en cascada a vínculos de billetera, acumulaciones (liquidadas), flags, sesiones.
- Derecho de rectificación: Re-disparar verificación para actualizar mapeo Epic (/me/reverify o re-verificación de admin).

## Medidas de seguridad
- Tokens de sesión firmados con secreto HMAC (no adivinables; sin PII dentro).
- Secretos enmascarados en logs estructurados (`safe_dict`).
- Limitación de tasa y heurísticas de abuso reducen scraping/enumeración automatizada.
- Protección opcional de balance del operador previene pagos vacíos no intencionados.

## Guía de retención (recomendada)
| Datos | Retención máx. sugerida | Método de eliminación |
|-------|-------------------------|-----------------------|
| Filas de acumulación sin procesar | 30–90 días post-liquidación | Eliminar o agregar solo estadísticas |
| Registros de verificación (anteriores al último exitoso) | 30 días | Purgar |
| Flags de abuso (resueltos) | 90 días | Purgar |
| Logs | 7–30 días | Rotar + destruir |
| TSDB de métricas | 30–90 días | Política de retención |

## Internacional y transferencias
El Software no transmite datos fuera de la infraestructura del operador a menos que se configure explícitamente (ej. endpoint de trazas externo). Cualquier consideración de transferencia entre regiones recae en las elecciones de hosting del operador. No existe lógica de transferencia automática al extranjero en el código.

## Datos de menores
El Software no está diseñado para recopilar indicadores de edad; los operadores deben restringir la promoción a audiencias apropiadas según su jurisdicción.

## Cambios a esta política
Versionada en control de código fuente. Los cambios materiales deben incrementar la Fecha de vigencia y resumir las diferencias en los mensajes de commit.

## Contacto / Gobernanza
Como proyecto auto-hospedado, las responsabilidades de gobernanza y cumplimiento recaen en cada operador. Las contribuciones de la comunidad para fortalecer la privacidad son bienvenidas vía pull request.

## Checklist rápido del operador
- [ ] Desactivar exportación OTLP a menos que sea necesario
- [ ] Proteger /metrics detrás de auth o política de red
- [ ] Establecer retención de logs ≤30d
- [ ] Proporcionar procedimiento documentado de eliminación de usuario
- [ ] Podar periódicamente acumulaciones liquidadas y registros de verificación obsoletos
- [ ] Revisar configs por exposición accidental de secretos

---
Esta política busca la máxima privacidad con la mínima fricción. Si puedes eliminar o anonimizar más manteniendo las recompensas precisas — hazlo y contribuye mejoras.
