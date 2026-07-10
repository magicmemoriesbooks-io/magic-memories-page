# Auditoría de Emails de Ciclo de Vida y Marketing — Magic Memories Books
Fecha: 10 julio 2026. Auditoría de solo lectura — ningún archivo fue modificado. Ninguna función fue eliminada, incluso las que parecen sin llamadas directas, hasta confirmar si corren por scheduler/cron/ruta admin.

Este documento complementa `docs/email_system_audit.md` (pipeline transaccional) y `docs/unified_email_delivery_architecture.md` (diseño), cubriendo específicamente la familia de emails de leads, recuperación, seguimiento y venta posterior que se pidió ampliar.

---

## 0. Infraestructura de scheduling encontrada

El proyecto usa **APScheduler** (`BackgroundScheduler`), registrado e iniciado en `app.py` (bloque ~líneas 563-683), protegido por un file-lock (`/tmp/mmb_scheduler.lock`) para que solo corra en un worker de Gunicorn a la vez (evita que múltiples workers dupliquen el disparo de los mismos jobs). Todos los jobs listados abajo están efectivamente registrados con `scheduler.add_job(...)` y el scheduler se inicia con `scheduler.start()` — no son solo funciones definidas y olvidadas.

| Job | Intervalo | Función | Rol |
|---|---|---|---|
| `lead_follow_up_emails` | cada 1h | `scheduled_lead_follow_up_emails` → `process_pending_follow_up_emails` | Feedback 24h + Upsell 48h (post-compra) |
| `isabel_campaign_3h` | cada 1h | `scheduled_isabel_campaign_3h` | Recuperación de leads/previews abandonadas |
| `ebook_expiry_check` | cada 24h | `scheduled_ebook_expiry_check` | Aviso de vencimiento de eBook temporal |
| `photo_cleanup` | cada 6h | `scheduled_photo_cleanup` | Mantenimiento (borrado de fotos, no email) |
| `temp_cleanup` | cada 12h | `scheduled_temp_file_cleanup` | Mantenimiento |
| `log_rotation` | cada 6h | `scheduled_log_rotation` | Mantenimiento |
| `story_backup` | cada 5 min | `scheduled_story_backup` | Mantenimiento |
| `auto_purge_stories` | cada 1h | `auto_purge_old_stories` | Mantenimiento |

**No existe** ningún cron externo (no hay Replit Scheduled Deployments configurado, no hay crontab de sistema) — todo el scheduling vive dentro del proceso Flask vía APScheduler. Esto significa que si el proceso se reinicia, el scheduler se reinicia limpio (sin cola persistente propia) y depende de los timestamps guardados en JSON/DB para saber qué le toca disparar en el próximo ciclo, no de un estado interno del scheduler.

**Script standalone encontrado:** `scripts/backfill_email_log.py` — de ejecución manual únicamente, para reconstruir `data/email_log.jsonl` desde los JSON de historias existentes. No es un disparador de emails nuevos, es una herramienta de reparación de auditoría histórica.

---

## 1. Inventario de cada automatización (formato de 20 campos solicitado)

### A. Feedback 24h (`send_feedback_email_24h`)
1. **Nombre interno:** `feedback_24h` (mismo nombre en `_EMAIL_TYPE_META` y en `data/lead_follow_ups.json`).
2. **Propósito:** pedir opinión/feedback sobre el cuento recién entregado, tono personal firmado por "Isabel".
3. **Disparador:** scheduler `lead_follow_up_emails` (hourly) → `process_pending_follow_up_emails`.
4. **Tiempo de espera:** 22–30 horas desde la compra (ventana de 8h para tolerar que el job corra cada hora sin perder el disparo).
5. **Condiciones de entrada:** el pedido debe existir como entrada en `data/lead_follow_ups.json`; `email_1_sent == False`; el preview_id no debe empezar con `TEST_`.
6. **Condiciones de exclusión:** `email_1_sent == True` ya (no reenviar); `_is_duplicate_send(preview_id, 'feedback_24h')` en true (ventana 30 días) bloquea el envío como segunda capa.
7. **Usuarios que lo reciben:** cualquier comprador de cualquier producto (QS o PB) que quedó registrado en `lead_follow_ups.json` en el momento de la compra.
8. **Productos/cuentos afectados:** todos — no filtra por tipo de producto.
9. **Plantilla:** inline en `email_service.py`, asunto "¿Cómo resultó la historia de [Nombre]? 💜" / equivalente en inglés.
10. **Idiomas:** ES/EN, rama por `lang` en `story_data`.
11. **Enlaces incluidos:** ninguno transaccional relevante — es una solicitud de respuesta directa (reply-to), no un CTA de compra.
12. **Descuento/oferta:** ninguno.
13. **Estado real: ACTIVO.**
14. **Función que lo ejecuta:** `send_feedback_email_24h` en `email_service.py`.
15. **Scheduler:** `lead_follow_up_emails`, cada 1h.
16. **Cómo evita duplicados:** flag `email_1_sent` en `lead_follow_ups.json` + `_is_duplicate_send` como segunda capa (30 días).
17. **Registro que deja:** entrada en `data/email_log.jsonl` (`email_type='feedback_24h'`) + actualización de `email_1_sent=True` en `lead_follow_ups.json`.
18. **Cómo sabe que compró:** la sola presencia en `lead_follow_ups.json` YA implica que compró (se inserta ahí en el momento de la compra, no antes) — no vuelve a verificar estado de compra en este email porque el trigger de entrada ya lo garantiza.
19. **Cómo sale del flujo:** una vez `email_1_sent=True`, nunca más entra a esta rama para ese pedido.
20. **Respeta bajas/marketing:** **no verificado explícitamente** — no se encontró un chequeo contra `NewsletterSubscriber.is_active` o un unsubscribe general antes de enviar. Al ser un email transaccional-adyacente (relacionado a un pedido real, no a una lista de marketing), es ambiguo si debería respetar el opt-out general de newsletter — **queda como hallazgo a decidir con negocio**, no se asume una respuesta.

### B. Upsell impresión 48h (`send_upsell_print_email`)
1. **Nombre interno:** `upsell_print`.
2. **Propósito:** ofrecer el formato que el cliente no compró (PDF→ofrece impreso, o eBook-only→ofrece PDF+impreso).
3. **Disparador:** mismo scheduler `lead_follow_up_emails`.
4. **Tiempo de espera:** 46–50 horas desde la compra.
5. **Condiciones de entrada:** `email_1_sent == True` (el feedback ya se mandó) y `email_2_sent == False`.
6. **Condiciones de exclusión:** si `want_print == True` o `cp_submitted == True` (ya tiene el físico) se omite; `_is_duplicate_send(preview_id, 'upsell_print')` (30 días) como segunda capa.
7. **Usuarios que lo reciben:** compradores que NO tienen todavía el formato impreso.
8. **Productos/cuentos afectados:** todos los que no incluyan ya impresión — dado que hoy TODO Personalized Book incluye impresión por configuración (ver auditoría anterior), este email en la práctica solo es relevante para Quick Stories digital-only.
9. **Plantilla:** inline, asunto "¿Te imaginas la historia de [Nombre] como libro real? ✨" (variantes EN/ES).
10. **Idiomas:** ES/EN.
11. **Enlaces incluidos:** link a `/formats/{preview_id}`.
12. **Descuento/oferta:** no se detectó cupón automático en esta plantilla — solo el CTA a la página de formatos, cuyo precio es el estándar.
13. **Estado real: ACTIVO** (aunque de alcance reducido para PB desde que `includes_print` quedó fijo en True).
14. **Función:** `send_upsell_print_email`.
15. **Scheduler:** `lead_follow_up_emails`, cada 1h.
16. **Duplicados:** flag `email_2_sent` + `_is_duplicate_send`.
17. **Registro:** `email_log.jsonl` (`upsell_print`) + `email_2_sent=True` en `lead_follow_ups.json`.
18. **Cómo sabe que compró después:** relee `story_previews/{id}.json` en el momento de disparar, no solo el snapshot de `lead_follow_ups.json` — esto es correcto, evita ofrecer impreso a alguien que lo compró en las horas intermedias.
19. **Cómo sale del flujo:** `email_2_sent=True` cierra la secuencia (no hay email 3 programado).
20. **Bajas/marketing:** mismo hallazgo que el anterior — no se encontró chequeo de opt-out general.

### C. Campaña Isabel — recuperación de leads/previews abandonadas (`send_isabel_campaign_email`)
1. **Nombre interno:** `lead_campaign_isabel`.
2. **Propósito:** reenganchar a quien generó una preview (vista personalizada de portada/texto) pero no compró.
3. **Disparador:** scheduler `isabel_campaign_3h`, cada 1h.
4. **Tiempo de espera:** entre 3 horas y 30 días desde la creación del lead (`PreviewLead.created_at`).
5. **Condiciones de entrada:** existe un registro en la tabla `PreviewLead` con email válido, dentro de la ventana de 3h-30 días.
6. **Condiciones de exclusión:** si ese email aparece como `paid=True` en cualquier `story_previews/*.json`, se excluye; `_is_duplicate_send(email, 'lead_campaign_isabel', days=365)` — **la clave de deduplicación aquí es el EMAIL, no el preview_id**, lo cual es relevante para la pregunta de "varias previews con el mismo email" (ver sección 3).
7. **Usuarios que lo reciben:** cualquier visitante que llegó a generar una preview sin comprar, de cualquier producto.
8. **Productos/cuentos afectados:** todos — no distingue tipo de historia.
9. **Plantilla:** inline, asunto "La historia de [Nombre] te está esperando ✨".
10. **Idiomas:** ES/EN.
11. **Enlaces:** a la sección de precios (`#precios`) y a la galería/Instagram.
12. **Descuento/oferta:** menciona un 10% de descuento de lanzamiento.
13. **Estado real: ACTIVO.**
14. **Función:** `send_isabel_campaign_email`.
15. **Scheduler:** `isabel_campaign_3h`, cada 1h.
16. **Duplicados:** `_is_duplicate_send(email, ..., days=365)` — ventana muy larga (1 año), diseñada para que un mismo lead no reciba la campaña más de una vez en todo ese periodo, independientemente de cuántas previews nuevas genere.
17. **Registro:** `email_log.jsonl` (`lead_campaign_isabel`).
18. **Cómo sabe que compró después:** escaneo de TODOS los `story_previews/*.json` buscando `paid=True` para ese email — es una verificación por fuerza bruta sobre archivos, no una consulta indexada; a volumen alto de historias esto podría volverse lento (nota de rendimiento, no de corrección).
19. **Cómo sale del flujo:** al comprar, queda excluido por el chequeo `paid=True`; también sale definitivamente tras el envío por la ventana de 365 días de `_is_duplicate_send`.
20. **Bajas/marketing:** **no se encontró verificación contra unsubscribe/opt-out general** — este es el hallazgo más importante de esta sección: `PreviewLead` no tiene un campo de opt-out propio, y no se vio cruce con `NewsletterSubscriber.is_active`. Un usuario que se dio de baja del newsletter podría seguir recibiendo esta campaña si generó una preview después de darse de baja. **Requiere decisión de negocio antes de la fase de implementación.**

### D. Newsletter — bienvenida (`send_newsletter_welcome`)
Disparo inmediato al suscribirse (`/api/newsletter-subscribe` o `/subscribe`). Tabla `NewsletterSubscriber` (email único, `unsubscribe_token` único). Incluye link de baja funcional (`/unsubscribe/<token>` pone `is_active=False`). **ACTIVO**, sin relación con pedidos.

### E. Newsletter — blast (`send_newsletter_blast`)
Disparo **manual únicamente** desde `/admin/newsletter/send`. Filtra por `is_active=True` antes de cada envío del loop — si respeta bajas correctamente. **ACTIVO pero no automático** (requiere acción humana cada vez).

### F. Recuperación inmediata (`send_recovery_link_email`)
No es marketing — es la bisagra entre "pagó" y "ver su compra" si cerró la pestaña. Se dispara justo tras el pago si `paid=True` y `recovery_email_sent=False`, o manualmente desde admin. Este ya estaba cubierto como transaccional en la auditoría anterior — se repite aquí solo para dejar constancia de que NO se confundió con las campañas de abandono.

### G. Abandono de lead — legacy (`send_lead_abandonment_email` / `_send_lead_abandonment_email_removed`)
1. **Nombre interno:** `lead_abandonment`.
13. **Estado real: OBSOLETO — reemplazado explícitamente.** El propio código retorna `False` de inmediato con un comentario indicando que fue reemplazado por `send_isabel_campaign_email`. No está en ningún scheduler, no tiene ningún call site activo más allá de sí misma. Confirmado: no requiere ninguna acción de eliminación en esta fase (se deja intacta por instrucción explícita), pero se documenta como la respuesta a "qué pasó con la revisión de hace 2 semanas" — el sistema de abandono SÍ fue rediseñado, y el resultado de ese rediseño es la campaña Isabel (C), no esta función.

### H. Aviso de vencimiento de eBook (`send_ebook_expiry_warning_email`)
Aunque no estaba explícitamente en tu lista de términos de búsqueda, aparece en el mismo scheduler de ciclo de vida y es relevante para el "seguimiento posterior a la compra": se dispara diariamente (`ebook_expiry_check`) para eBooks temporales de regalo próximos a expirar, ofreciendo renovarlos a precio. Se documenta aquí para que quede completo el mapa de emails post-compra automatizados. **ACTIVO.**

---

## 2. Secuencias temporales solicitadas

**A. Preview creada y compra abandonada:**
```
Preview creada → INSERT en PreviewLead (email, story_id, ts)
+3h a +30 días → scheduler isabel_campaign_3h evalúa el lead
  → si NO paid y NO enviado antes (365d) → send_isabel_campaign_email
  → si paid=True en cualquier story_previews/*.json → se excluye, no se envía
```

**B. Lead que recibe recuperación y después compra:**
```
Lead recibe send_isabel_campaign_email (ej. a las 5h)
Usuario compra a las 8h → story_previews/{id}.json queda paid=True
Próxima corrida del scheduler (cada 1h) → el chequeo "paid=True" ya lo excluye de futuros envíos de esta campaña
_is_duplicate_send también lo bloquearía por 365 días aunque el chequeo de paid fallara por algún motivo → doble protección, correctamente diseñada para este caso específico
```

**C. Cliente que compra un cuento:**
```
Pago confirmado → (pipeline transaccional, ver otro documento)
+compra → INSERT/actualización en data/lead_follow_ups.json (email_1_sent=False, email_2_sent=False)
+22-30h → send_feedback_email_24h (si no enviado)
+46-50h → send_upsell_print_email (si no tiene impreso todavía)
```

**D. Cliente al que se ofrece otra historia:** **no se encontró ninguna automatización de "cross-sell hacia otro cuento distinto"** (p. ej. "ya compraste Dragon Garden, te sugerimos Magic Chef"). Lo que existe es upsell de FORMATO (PDF→impreso) del MISMO cuento, no cross-sell de catálogo. **Esto es un hallazgo de ausencia, no de omisión de búsqueda** — se buscó explícitamente con términos "another story/next story/otra historia/reorder" y no apareció ninguna función ni scheduler que lo implemente. Si la revisión de hace 2 semanas mencionó esto, quedó **SOLO DOCUMENTADO o descartado**, no implementado — no se puede confirmar cuál sin el registro de esa conversación.

**E. Cliente que compra PDF o impreso y recibe posibles upsells:**
```
Compra PDF solamente → entra a lead_follow_ups.json
+22-30h → feedback_24h
+46-50h → upsell_print (le ofrece el impreso, porque want_print=False)

Compra impreso (PB, que siempre lo incluye) → entra a lead_follow_ups.json
+22-30h → feedback_24h
+46-50h → upsell_print se EVALÚA pero se OMITE porque want_print=True — no se envía nada en su lugar (no hay un "upsell alternativo" para quien ya tiene todo)
```

**F. Cliente que ya compró el producto ofrecido:** confirmado que `send_upsell_print_email` re-verifica el estado real (`want_print`/`cp_submitted`) en el momento del envío, no solo el snapshot original — si compró el impreso en el ínterin (por ejemplo vía `/formats` como upgrade posterior), la condición de exclusión lo detecta y no se envía el email. Correcto.

---

## 3. Verificaciones específicas pedidas

### ¿Un usuario que compra deja de recibir emails de abandono/recuperación?
**Sí, con dos capas de protección independientes:**
1. Exclusión activa por estado real (`paid=True` escaneado en `story_previews/*.json` en cada corrida del scheduler de campaña Isabel; `want_print`/`cp_submitted` en el upsell).
2. Backup por `_is_duplicate_send` con ventana larga (365 días para la campaña Isabel).

No se encontró ningún camino donde ambas protecciones fallen simultáneamente para el caso simple de una sola preview. El riesgo real está en el caso de múltiples previews (ver abajo).

### ¿Varias previews con el mismo email pueden generar emails duplicados?
- Para la **campaña Isabel**: la clave de deduplicación es el **email**, no el `preview_id` — está bien diseñada para este caso específico: aunque el usuario genere 5 previews distintas con el mismo email, `_is_duplicate_send(email, 'lead_campaign_isabel', days=365)` bloquea después del primer envío exitoso, sin importar cuál preview lo disparó. **No hay riesgo de duplicado aquí.**
- Para **feedback_24h / upsell_print**: la clave es `preview_id`, no email — esto es correcto para su propósito (cada preview/pedido es una compra independiente que merece su propio feedback), pero significa que si el mismo email compra 2 historias distintas, legítimamente recibirá 2 emails de feedback y 2 de upsell, uno por cada preview — **esto es el comportamiento deseado, no un bug**, pero vale la pena que quede explícito para que no se confunda con un duplicado real durante pruebas.
- **Riesgo real identificado:** la tabla `PreviewLead` (ver `models.py`) **no tiene constraint de unicidad sobre `email`** — cada preview generada crea una fila nueva aunque sea el mismo email. Esto no genera duplicados de EMAIL gracias a la deduplicación por email en `_is_duplicate_send`, pero sí significa que el scheduler `isabel_campaign_3h` **recorre y evalúa N filas por cada email con N previews**, hace N verificaciones redundantes de "¿ya se le envió?" cada hora — ineficiente pero no incorrecto en el resultado final observable por el cliente.

---

## 4. Clasificación de estado real (resumen ejecutivo)

| Automatización | Estado |
|---|---|
| Feedback 24h | **ACTIVO** |
| Upsell impreso 48h | **ACTIVO** (alcance reducido desde que PB siempre incluye impresión) |
| Campaña Isabel (recuperación de leads) | **ACTIVO** |
| Newsletter bienvenida | **ACTIVO** |
| Newsletter blast | **ACTIVO PERO MANUAL** (no es automatización periódica, requiere click de admin) |
| Aviso vencimiento eBook | **ACTIVO** |
| Recuperación inmediata post-pago | **ACTIVO** (transaccional, no marketing) |
| Abandono de lead (función legacy) | **OBSOLETO — reemplazado explícitamente por Campaña Isabel** |
| Cross-sell hacia OTRA historia del catálogo | **NO IMPLEMENTADO — no se encontró ningún rastro de código, ni activo ni desactivado** |
| Respeto de opt-out/unsubscribe en Feedback 24h, Upsell 48h y Campaña Isabel | **DUDOSO — requiere verificación/decisión de negocio**, no se encontró cruce con `NewsletterSubscriber.is_active` en ninguna de las tres |

---

## 5. Impacto en la arquitectura unificada — separación de dominios

Se confirma con esta auditoría que existen dos dominios de decisión genuinamente distintos, que ya operaban de facto de forma separada en el código (distintos triggers, distintos almacenes de estado, distintas condiciones de exclusión) aunque comparten la misma infraestructura de envío:

- **Pipeline transaccional** (cubierto en `unified_email_delivery_architecture.md`): decide en función de qué compró el cliente. Prioriza SIEMPRE entregar lo pagado.
- **Pipeline de ciclo de vida y marketing** (este documento): decide en función de si el cliente sigue siendo elegible en el momento del envío — no depende de un pedido, puede no existir ningún pedido (lead que nunca compró), y su obligación es la opuesta: verificar antes de cada envío que la persona no haya comprado ya o no se haya dado de baja, para NO enviar.

Ambos comparten: `email_service.py`, el proveedor SMTP, las plantillas base (`_email_wrapper`), los idiomas, `email_log.jsonl` como auditoría, y el manejo de errores por try/except. Pero las reglas de decisión (qué condiciones de entrada/exclusión aplican) deben permanecer completamente separadas — el pipeline comercial **no debe depender de `resolve_order_emails()`/`resolve_entitlements()`** porque puede dispararse sin que exista ningún pedido (caso de `PreviewLead` sin compra).

La sección siguiente actualiza el documento de arquitectura para reflejar esta separación formalmente.
