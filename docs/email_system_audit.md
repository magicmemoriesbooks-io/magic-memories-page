# Auditoría del Sistema de Emails y Entregas — Magic Memories Books
Fecha: 10 julio 2026. Auditoría de solo lectura — ningún archivo fue modificado.

## 1. Inventario completo de disparadores

| Disparador | Archivo:línea | Tipo | Product types | Activo | Quién lo invoca | Qué puede producir |
|---|---|---|---|---|---|---|
| `paypal_capture_order` | app.py:4939 (aprox) | Ruta de captura PayPal (cliente) | Todos (carrito, express, PB) | Activo | Frontend PayPal SDK tras aprobación | Dispara `_dispatch_cart_item` / `_process_cart_order`, confirmación de pago |
| `process_payment` | app.py:5596 | Ruta de captura PayPal (cliente, flujo libros personalizados) | quick_story, personalized_book, ebook, personalized_pdf | Activo | Checkout de libros personalizados | `_process_ebook_generation`, `_trigger_background_generation`, `_trigger_personalized_book_composition`, `_process_personalized_book_post_payment`, `_process_quick_story_print`, `_dispatch_printable_pdf_email`, email de recuperación |
| `paypal_capture_print_order` | app.py:14192 | Ruta de captura PayPal | cp_personalized (impresión post-digital) | Activo | Botón "imprimir después" | `_dispatch_cart_item`, confirmación de impresión |
| `paypal_capture_formats_order` | app.py:14525 | Ruta de captura PayPal | ebook/pdf/print (upgrade de formato) | Activo | Página `/formats` | Desbloquea formatos nuevos sobre un preview existente |
| `cloudprinter_webhook` | app.py:2223 | Webhook servidor-a-servidor | Libros impresos (todos) | Activo | Cloudprinter (asíncrono real) | Actualiza estado de envío, `send_cp_tracking_email` |
| `order_complete` (`/order-complete/<id>`) | app.py:5883 | Ruta de recuperación | Todos | Activo | Link de recuperación en email | Puede regenerar PDF si falta |
| `shipping_confirm` | app.py:5968 | Ruta de checkout | cp_personalized | Activo | Formulario de envío del cliente | Puede disparar el pedido final a Cloudprinter |
| `confirm_and_send` (`/api/confirm-and-send/<id>`) | app.py:7194 | Ruta de aprobación del usuario | QS + PB | Activo | Botón "Aprobar y enviar" en review page | Ver sección 7 — reimplementa toda la lógica de negocio |
| `admin_retry_cp_submission` (`/admin/retry-cp/<id>`) | app.py:10162 | Admin | QS | Activo | Panel admin | Reintenta pedido Cloudprinter fallido |
| `admin_resend_qs_pdf` (`/admin/resend-qs-pdf/<id>`) | app.py:9534 | Admin | QS | Activo | Panel admin | Limpia `pdf_email_sent` y vuelve a llamar `_process_ebook_generation` (re-ejecuta reglas) |
| `admin_resend_printable_pdf` | app.py:14298 | Admin | PB | Activo | Panel admin | Reenvía el PDF imprimible del libro |
| `admin_send_cp_resolved` | app.py:10258 | Admin | QS/PB | Activo | Panel admin | Reenvío de plantilla fija (no recalcula reglas) |
| `admin_retry_scenes` / `admin_regenerate_scene` | app.py:11217 / 8699 | Admin | PB/QS | Activo | Panel admin | Regenera escenas, no envía email directamente |
| **PayPal webhook servidor-a-servidor** | — | — | — | **No existe** | — | Confirmado: NO hay webhook de PayPal. Toda confirmación de pago llega solo por el capture-route del cliente. Esto elimina el riesgo de doble-procesamiento webhook-vs-cliente, pero significa que si el cliente cierra el navegador antes de que el capture-route responda, no hay una segunda vía de confirmación (riesgo inverso: pedido pagado sin post-proceso, mitigado por `/order-complete/<id>`). |
| **Stripe** | — | — | — | No usado | — | No hay rutas Stripe activas; la plataforma migró completamente a PayPal (aunque `replit.md` originalmente listaba Stripe como posible, no está implementado). |

## 2. Inventario completo de funciones de email

Todas viven en `services/email_service.py`, sin archivos de plantilla externos — HTML generado con f-strings de Python, envueltos por `_email_wrapper` (cliente) o `_admin_wrapper` (admin interno).

| Función | Uso | Estado |
|---|---|---|
| `send_story_email_with_attachments` | Entrega de PDF imprimible + adjuntos | Activa |
| `send_payment_confirmation_email` | Confirmación de pago | Activa |
| `send_recovery_link_email` | Link de recuperación de pedido | Activa |
| `send_generation_started_email` | "Estamos creando tu cuento" | Activa |
| `send_generation_failed_email` | Aviso de fallo de generación | Activa |
| `send_print_failure_email` / `send_print_resolved_email` | Incidencias de impresión (cliente) | Activas |
| `send_print_failure_admin_email` | Incidencias de impresión (admin) | Activa |
| `send_ebook_email` | Entrega de eBook (permanente o regalo, vía `is_gift`) | Activa — **es la función más sobrecargada, usada por 3 orquestadores distintos con distintas combinaciones de flags** |
| `send_ebook_expiry_warning_email` | Aviso de expiración de acceso 6 meses | Activa |
| `send_ebook_admin_notification` / `send_cp_pb_admin_notification` / `send_personalized_pdf_admin_email` / `send_admin_purchase_notification` | Notificaciones internas de venta | Activas, con solapamiento funcional entre sí (3-4 funciones muy similares para notificar "hubo una venta") |
| `send_cp_order_notification` / `send_cp_tracking_email` / `send_cp_failure_email` / `send_cp_failure_admin_email` | Ciclo de vida Cloudprinter | Activas |
| `send_print_order_confirmation_email` | Confirmación de pedido impreso al cliente | Activa |
| `send_cart_confirmation_email` | Resumen de carrito multi-ítem | Activa |
| `send_newsletter_welcome` / `send_newsletter_blast` | Newsletter | Activas, sin relación con el flujo de pedidos |
| `send_feedback_email_24h` / `send_upsell_print_email` / `send_isabel_campaign_email` | Marketing post-compra | Activas — **únicas que usan `_is_duplicate_send`** |
| `send_coupon_email` | Cupón de descuento | Activa |
| `send_admin_error_email` / `send_admin_notification_email` | Alertas técnicas | Activas |
| `send_lead_abandonment_email` | Marcada explícitamente `DEPRECATED — removed`, retorna `False` de inmediato | **Obsoleta, código muerto conservado a propósito** |
| `_send_lead_abandonment_email_removed` | Implementación vieja de lo anterior | **Muerta** |

## 3. Inventario de plantillas

No existen archivos `.html` de plantilla — todo el HTML vive como strings de Python dentro de `email_service.py`, compuesto con helpers reutilizables: `_email_wrapper`, `_admin_wrapper`, `_info_box`, `_alert_box`, `_success_box`, `_cta_button`, `_isabel_signature_html`, `_newsletter_invite_html`. Todos bilingües (rama `if lang == 'es' / else`) dentro de la misma función — no hay separación es/en en archivos distintos.

**Implicación para el cuento piloto:** no hay "plantilla de email por libro" que copiar — el mismo `send_ebook_email` / `send_story_email_with_attachments` sirve a todos los productos, parametrizado por `story_data`. Esto es positivo: la capa de plantillas YA está unificada. El problema no está aquí, está en la capa de *decisión* (qué función llamar y cuándo), como se documentó en la auditoría anterior.

## 4. Matriz real de productos y entregas

| product_type / variante | want_ebook | want_pdf | want_print | includes_print (config) | Qué compra | Qué recibe | Principal | Regalo | Acceso eBook | ¿Dirección? | ¿Cloudprinter? |
|---|---|---|---|---|---|---|---|---|---|---|---|
| QS digital (`qs_digital`) | opcional | opcional | False | False | PDF y/o eBook interactivo | Email con adjunto y/o link visor | El que compró | eBook 6 meses SI compró PDF sin eBook | Permanente si `want_ebook`, si no 6 meses | No | No |
| QS impresa (`qs_print`) | opcional | — | True | True | Libro impreso físico | Libro físico + confirmación + eBook regalo si no compró eBook | Impreso | eBook 6 meses | 6 meses (salvo que también compre eBook) | Sí | Sí |
| PB — Aventuras/Furry Love/Centinela (`cp_personalized` / `personalized_book`) | opcional | opcional | **siempre True** (config fija) | **True siempre** | Libro impreso (obligatorio) + PDF/eBook opcionales | Físico + PDF si compró + eBook regalo o permanente | Impreso | eBook 6 meses si no compró eBook | 6 meses o permanente según compra | Sí, siempre | Sí, siempre |
| PDF imprimible standalone (`personalized_pdf`) | False | True | False (en teoría) | — | Solo el PDF imprimible | PDF + eBook regalo 6 meses | PDF | eBook 6 meses | 6 meses | No | No — **pero puede coexistir con want_print=True si se compra junto con el libro impreso (caso del bug ya corregido)** |
| Cuento piloto | *aún no lanzado — hereda config de PB* | — | — | — | — | — | — | — | — | — | — |
| Cuentos de regalo (`admin_gift`) | N/A | N/A | N/A | N/A | Regalo administrativo, sin cobro | Libro sin emails de venta ni pedido CP | — | — | — | Depende | **No** — `admin_gift=True` suprime explícitamente emails y envío a Cloudprinter |
| Legacy Lulu (`lulu_job_id` presente) | — | — | — | — | Pedidos antiguos pre-Cloudprinter | — | — | — | — | — | **No** — reemplazado, ruta `/api/admin/send-to-lulu` devuelve 410 |

**Nota crítica:** en Personalized Books, `want_print` viene fijo en `True` por configuración de producto, pero el código de `_compose_personalized_book_background` sigue leyendo `story_data.get('want_print', False)` como si pudiera ser opcional. Eso es lo que permite el escenario mixto PDF+Print del bug de hoy: aunque el "libro impreso" siempre viene incluido, el cliente puede ADEMÁS añadir el PDF imprimible como extra — ahí es donde chocan las dos rutas de email.

## 5. Secuencia temporal real

**Quick Story digital:**
```
Pago capturado (process_payment / paypal_capture_order)
→ _process_ebook_generation (hilo)
  → espera generación de escenas
  → prepare_and_upload (visor)
  → si want_pdf: genera PDF + envía send_story_email_with_attachments
  → si want_ebook: send_ebook_email(is_gift=False)
  → si (want_pdf o want_print) y no want_ebook: send_ebook_email(is_gift=True)   ← ya usa condición combinada, correcto
  → marca email_sent=True
```
No hay "email de confirmación de pago" ni "estamos creando tu cuento" en esta ruta salvo lo que envíe `_send_cart_order_email` (resumen de carrito) — el aviso de "generando" (`send_generation_started_email`) existe como función pero no confirmé que se dispare en este camino específico; requiere verificación puntual antes de asumir que se envía siempre.

**Quick Story impresa:**
```
Pago capturado
→ _process_ebook_generation (visor + eBook regalo si aplica)
→ _process_quick_story_print (hilo separado, independiente)
  → genera PDF Cloudprinter
  → envía a Cloudprinter
  → send_cp_order_notification (admin)
  → NO envía confirmación al cliente en esta función — la confirmación al cliente ocurre en otro punto (revisar `send_print_order_confirmation_email`, que en QS aparece en `confirm_and_send`, línea ~14046, no en `_process_quick_story_print`)
```
**Hallazgo:** el orden entre "email de eBook regalo" y "confirmación de impresión" en QS depende de qué hilo termine primero — no hay garantía de secuencia. Ambos hilos se lanzan independientemente desde `_dispatch_cart_item`.

**Libro personalizado (PB):**
```
Pago capturado (process_payment)
→ _trigger_personalized_book_composition (si no compuesto)
→ _compose_personalized_book_background (hilo)
  → recovery email (si primera vez)
  → genera páginas + rebuild_book
  → si cp_personalized: envía a Cloudprinter
  → lanza HILO PARALELO _dispatch_printable_pdf_email (si want_pdf)      ← este hilo es independiente y puede terminar en cualquier momento respecto al resto
  → Email B: confirmación de impresión (si want_print)
  → Email B2: eBook regalo (si want_print y no want_ebook)
  → Email C: eBook permanente (si want_ebook)
```
El hilo de `_dispatch_printable_pdf_email` corre EN PARALELO al resto de la función, no en secuencia — por diseño puede entrelazarse en cualquier orden con Email B/B2/C. Esta es la causa raíz estructural del bug de hoy y de cualquier futuro bug similar: dos ramas de código que deciden lo mismo (el gift eBook) sin coordinarse en tiempo real, solo por flags en disco.

**Recuperación manual (`/order-complete` o `confirm_and_send`):** puede reentrar en cualquier punto de las secuencias de arriba, revisando flags — ver sección 7.

**Reenvío admin:** generalmente limpia un flag puntual y vuelve a invocar la función automática original (mismo código, mismo riesgo de carrera si se dispara mientras el flujo automático sigue corriendo).

## 6. Idempotencia y duplicados

- **No hay una idempotencia real cruzada entre funciones.** Cada función revisa sus propias flags en el JSON (`email_sent`, `pdf_email_sent`, `ebook_email_sent`, `gift_ebook_sent`, `print_confirmation_sent`, `printable_pdf_sent`, `printable_pdf_admin_sent`, `admin_notified`, `admin_pdf_sent`, `cp_submitted`, `recovery_email_sent`) con el patrón **"leer flag → hacer trabajo lento (IA/PDF/email) → recién ahí escribir flag en True"**. Esto deja una ventana de carrera en TODAS estas flags, no solo en la del bug de hoy.
- Existen locks en memoria (`_post_payment_lock`, `_ebook_processing_lock`, `_pdf_dispatch_lock`) pero **cada uno solo protege contra dos llamadas concurrentes a LA MISMA función** para el mismo preview_id. Ninguno protege contra que dos funciones DISTINTAS (p. ej. `_compose_personalized_book_background` y `_dispatch_printable_pdf_email`) decidan mandar el mismo tipo de email al mismo tiempo — que es exactamente lo que pasó.
- **Hallazgo nuevo e importante:** SÍ existe una capa de deduplicación basada en un log persistente (`_is_duplicate_send`, revisa `data/email_log.jsonl` buscando envíos del mismo `email_type` para el mismo `preview_id` en los últimos 30 días) — **pero solo se usa en 2 de ~25 funciones de email** (`send_feedback_email_24h` y `send_upsell_print_email`, ambos de marketing). Ningún email transaccional (PDF, eBook, eBook regalo, confirmación de impresión, confirmación de pago) pasa por esta protección. Es decir: la plataforma ya tiene la pieza de infraestructura para resolver esto (un log central por tipo de email), simplemente no se aplica donde más importa.
- **Qué pasa en los escenarios que pediste verificar:**
  - Webhook duplicado: no aplica, no hay webhook de pago (solo Cloudprinter, que es de estado de envío, no de dinero).
  - Usuario recarga la página de checkout: puede volver a disparar `process_payment`/`paypal_capture_order` sin nuevo cobro (ya capturado por PayPal), pero si las flags de story_data aún no se escribieron, puede relanzar los mismos hilos → mismo riesgo de duplicado.
  - `/api/confirm-and-send` ejecutado: revisa varias flags combinadas antes de reenviar (ver sección 7), pero el chequeo de "todo ya enviado" se basa en las mismas flags con ventana de carrera.
  - Admin reenvía: generalmente limpia una flag antes de re-invocar — si el flujo automático seguía en curso en background, se puede duplicar.
  - Falla el email tras generar el archivo: la flag de "PDF generado" y la de "email enviado" son distintas, así que un reintento no regenera el PDF (correcto) pero si la primera llamada falló silenciosamente antes de loguear el error, el reintento manual puede coincidir con un reintento automático tardío.
  - Hilo se reinicia (restart del workflow): las flags en disco sí persisten, así que tras un restart el sistema no debería reenviar lo ya marcado como enviado — el riesgo real está en pedidos que quedaron a medias (flag no escrita porque el proceso murió después de enviar el email pero antes de guardar el JSON) — ese caso SÍ puede producir un duplicado real en un reintento posterior.

## 7. Recuperación y reenvío — `/api/confirm-and-send`

- **Reutiliza en vez de regenerar:** para QS reutiliza PDF/visor existentes si los encuentra en disco; solo regenera si faltan. Para PB delega en `_dispatch_printable_pdf_email`, que tiene su propia lógica de reuso.
- **Sí vuelve a ejecutar las reglas de negocio:** recalcula `want_pdf/want_ebook/want_print` desde `story_data` cada vez que corre, en vez de usar un resultado ya decidido — es una tercera implementación de la misma regla que las otras dos.
- **Sí puede crear un NUEVO pedido de Cloudprinter:** si `want_print` es True y `cp_submitted` es False, lanza `_process_quick_story_print` de nuevo — si esta ruta se llama en paralelo con el flujo automático antes de que `cp_submitted` se marque, es técnicamente posible enviar dos pedidos de impresión física del mismo libro (riesgo real, no solo de email).
- **Sí puede duplicar emails:** mismas funciones (`send_ebook_email`, `send_story_email_with_attachments`) que el flujo automático, protegidas solo por las flags con ventana de carrera ya descritas.
- **Usa las mismas plantillas** que el flujo automático (no hay una plantilla "de recuperación" distinta para el contenido, salvo el email de recovery link en sí).
- **No es idéntico al flujo automático:** tiene ramas adicionales para "PDF pendiente pero eBook ya enviado" y "impresión pendiente pero emails completos" que no existen en los orquestadores automáticos — lógica genuinamente distinta, no una copia.

**Reenvíos admin:** `admin_resend_qs_pdf` limpia la flag y re-invoca la función automática completa (mismo riesgo si el proceso automático seguía vivo); `admin_send_cp_resolved` y similares solo reenvían una plantilla fija sin tocar reglas de negocio — más seguros pero limitados.

## 8. Proveedor de email y configuración

- Proveedor: SMTP directo (Gmail, `smtp.gmail.com:587`).
- Variables de entorno referenciadas (solo nombres): `SMTP_SERVER`, `SMTP_PORT`, `SENDER_EMAIL`/`FROM_EMAIL`, `SMTP_PASSWORD`, `FROM_NAME`, `PUBLIC_URL`, `REPLIT_DEV_DOMAIN`, `SITE_DOMAIN`.
- Remitente: `info@magicmemoriesbooks.com` (o valor de `FROM_EMAIL`). Notificaciones internas a `pay@magicmemoriesbooks.com`.
- No hay reply-to distinto configurado.
- Manejo de errores: try/except alrededor de cada envío, logueado en `data/email_log.jsonl` con `result: ERROR` y el texto de la excepción. No hay reintento automático con backoff — el "reintento" depende de que un hilo posterior vuelva a intentar o de una acción manual del admin.
- No se detectaron integraciones de proveedor de email antiguas (SendGrid, Mailgun, etc.) — siempre fue SMTP directo.

## 9. Cloudprinter, Gelato y Lulu — clasificación

| Referencia | Clasificación |
|---|---|
| `submit_pb_print_order`, `cloudprinter_api_service.py`, `/webhooks/cloudprinter` | **ACTIVA** — único partner de impresión real hoy |
| Rutas/paths con la palabra "gelato" (`/preview-pdf/gelato/...`, `generated/gelato/...`, `/admin/gelato-order/...`) | **ALIAS HISTÓRICO** — el nombre de carpeta/ruta quedó de una integración anterior, pero el contenido que sirve es generado y enviado vía Cloudprinter. No hay llamadas activas a la API de Gelato. |
| Variables `lulu_job_id`, `lulu_status`, `lulu_order_folder`, `lulu_submitted`, `lulu_error`, rutas `/admin/gift-book/<id>`, `/admin/rescue-lulu` | **LEGACY PERO TODAVÍA LEÍDA** — el código sigue comprobando estas claves como fallback (`story_data.get('cp_submitted', story_data.get('lulu_submitted', False))`) para no romper pedidos antiguos que aún tienen esos campos en su JSON. No se escriben nuevas desde hoy, solo se leen. |
| `/api/admin/send-to-lulu/<id>` (`admin_send_to_lulu`) | **OBSOLETA SIN USO REAL** — responde HTTP 410 explícitamente, es un stub informativo, no ejecuta nada. |
| `_process_personalized_book_post_payment` | **DUDOSA: REQUIERE VERIFICACIÓN** — sigue siendo invocada desde 3 sitios, pero por dentro solo tiene lógica real para `product_type == 'cp_personalized'`; para cualquier otro tipo actual cae en un bloque llamado "Legacy Lulu/Gelato path" que solo prepara un PDF digital de respaldo sin enviar nada. Vale la pena confirmar si algún producto vivo distinto de `cp_personalized` todavía depende de esta función antes de tocarla. |
| `send_lead_abandonment_email` / `_send_lead_abandonment_email_removed` | **OBSOLETA SIN USO** — deprecada explícitamente en el propio código, retorna `False` de inmediato. |

## 10. Dependencias del cuento piloto

Cuando el cuento piloto esté listo, copiarlo NO debe significar solo copiar `_compose_personalized_book_background`. Necesita, como mínimo:
- **`product_type`** correcto en `PERSONALIZED_BOOK_IDS`/`PERSONALIZED_BOOK_CONFIG` (o su propia entrada de config) para que `is_personalized_book()` lo reconozca y `includes_print`/`get_shipping_required()` se apliquen bien.
- **Las 3 implementaciones de reglas de negocio** (`_compose_personalized_book_background`, `_dispatch_printable_pdf_email`, la rama PB de `confirm_and_send`) deben quedar sincronizadas — hoy ya están, porque son funciones genéricas parametrizadas por `story_data`, NO específicas por libro. Es decir, el cuento piloto **hereda automáticamente** esta capa sin copiar nada, siempre que use el `book_id` correcto en `illustrated_book_service.py` y estén en `ALL_PERSONALIZED_BOOK_IDS`.
- **Plantillas de email:** no hay nada que copiar, son genéricas.
- **Generación de archivos / impresión / eBook:** heredado automáticamente vía `generate_full_book`, `rebuild_book`, `submit_pb_print_order` — no específico por libro salvo los prompts de escena.
- **Campos de story_data necesarios:** `want_ebook`, `want_pdf`, `want_print`, `story_id`, `traits`, `gender`, `dedication`, y para libros que usan referencia de foto: `child_photo_path` o `human_preview_path`/`pet_preview_path` según el patrón de furry_love.
- **Riesgo real de copy-paste:** el riesgo NO está en la capa de email (ya es genérica) sino en (a) usar un `book_id` no listado en `ALL_PERSONALIZED_BOOK_IDS` o `PERSONALIZED_BOOK_IDS` — rompería la detección de categoría — y (b) el bug de hoy, que es un problema de LA FUNCIÓN GENÉRICA, no del libro — por eso arreglarlo una vez en el orquestador beneficia a todos los libros, presentes y futuros, sin que el piloto necesite ningún tratamiento especial.

## 11. Diagramas de llamadas

**Quick Story digital:**
```
PAGO CAPTURADO (process_payment)
→ _dispatch_cart_item
→ _process_ebook_generation (hilo)
  → prepare_and_upload (visor)
  → DECISIÓN: want_pdf? want_ebook? want_print?
  → generar PDF (si aplica) → send_story_email_with_attachments
  → send_ebook_email(is_gift=False) (si want_ebook)
  → send_ebook_email(is_gift=True) (si (want_pdf o want_print) y no want_ebook)
  → escribir flags → email_sent=True
```

**Quick Story impresa:**
```
PAGO CAPTURADO
→ _dispatch_cart_item
  ├─→ _process_ebook_generation (hilo A: visor + eBook regalo)
  └─→ _process_quick_story_print (hilo B: PDF Cloudprinter + envío + notificación admin)
       (A y B corren en paralelo, sin orden garantizado)
```

**Libro personalizado:**
```
PAGO CAPTURADO (process_payment)
→ _trigger_personalized_book_composition
→ _compose_personalized_book_background (hilo)
  → recovery email
  → generate_full_book + rebuild_book
  → DECISIÓN want_pdf → lanza _dispatch_printable_pdf_email EN HILO PARALELO
       → genera PDF, envía email PDF
       → DECISIÓN interna: include_gift? (repite la pregunta del hilo padre)
  → si cp_personalized: submit_pb_print_order (Cloudprinter)
  → Email B: confirmación de impresión (want_print)
  → Email B2: eBook regalo (want_print y no want_ebook)
  → Email C: eBook permanente (want_ebook)
  (el hilo paralelo de PDF puede completarse antes, durante o después de B/B2/C)
```

**Recuperación manual (`/order-complete`, `confirm_and_send`):**
```
USUARIO ENTRA A LA RUTA
→ leer story_data
→ recalcular want_pdf/want_ebook/want_print (RE-IMPLEMENTACIÓN #3 de la misma regla)
→ revisar flags de envío ya realizados
→ si falta algo: generar/reusar archivo → enviar con la misma función que el flujo automático
→ puede relanzar _process_quick_story_print (nuevo pedido CP) si want_print y no cp_submitted
```

**Reenvío admin:**
```
ADMIN HACE CLIC EN "REENVIAR"
→ limpiar una flag puntual (ej. pdf_email_sent=False)
→ re-invocar la función automática original (mismo código)
   (sin lock cruzado contra un flujo automático que siga corriendo en background)
```

## 12. Conclusión

**A. Qué está activo:** todo el catálogo actual (QS digital, QS impresa, y los 9 libros de Personalized Books) usa las mismas funciones genéricas de `email_service.py`; no hay plantillas por libro que mantener por separado.

**B. Qué está duplicado:** la regla de negocio "qué emails corresponden según want_pdf/want_ebook/want_print" existe reimplementada de forma independiente en al menos 3 lugares (`_compose_personalized_book_background`, `_dispatch_printable_pdf_email`, la rama PB de `confirm_and_send`) y una 4ª variante paralela para QS (`_process_ebook_generation` + su propia rama en `confirm_and_send`). También hay 3-4 funciones de "notificar venta al admin" con propósito casi idéntico.

**C. Qué está parcialmente activo:** `_process_personalized_book_post_payment` — vigente solo para `cp_personalized`, vestigial para el resto.

**D. Qué está obsoleto:** `send_lead_abandonment_email` y su implementación `_removed`; la ruta `/api/admin/send-to-lulu` (stub 410); los paths con nombre "gelato" (alias sin integración real detrás).

**E. Qué es legacy pero todavía necesario:** las claves `lulu_*` como fallback de lectura para pedidos antiguos — no se pueden borrar sin migrar esos registros primero.

**F. Qué puede causar emails duplicados:** cualquier flag de las 11 listadas en la sección 6, porque todas comparten el patrón "verificar → trabajo lento → recién marcar". El caso más expuesto es el gift eBook en PB (ya parcheado hoy), pero el patrón de riesgo sigue existiendo igual de intacto para PDF, eBook permanente, confirmación de impresión y confirmación de pago — simplemente no se ha disparado un caso reportado todavía.

**G. Qué puede provocar que un cliente NO reciba un producto:** si el proceso muere entre "generar el archivo" y "marcar el flag" tras enviar el email exitosamente, un reintento futuro no reenviará (cree que ya se hizo) mientras que si muere ANTES de enviar pero el archivo ya se generó, ningún disparador automático vuelve a intentar salvo que el admin o el cliente entren manualmente a `/order-complete` o `/confirm-and-send`.

**H. Qué reglas de negocio están implementadas distinto según el flujo:** el propio caso de hoy — "gift eBook solo si no se compró el eBook Y no se compró el libro impreso" estaba correcto en `_compose_personalized_book_background` (usa `want_print` explícitamente) pero llegó incompleta a `_dispatch_printable_pdf_email` hasta el parche de hoy. Es la prueba viva de que mantener la regla en 3-4 sitios es lo que produce estas discrepancias.

**I. Qué información falta para diseñar una arquitectura unificada con seguridad:** (1) confirmar con el negocio si algún producto vivo aparte de `cp_personalized` todavía depende de `_process_personalized_book_post_payment`; (2) decidir si el objetivo de unificación es solo la DECISIÓN (qué emails tocan) o también el ENVÍO (que todo pase por un único punto con lock cruzado real, no solo flags); (3) definir si conviene extender `_is_duplicate_send` (ya existe y funciona) a los emails transaccionales, lo cual sería la corrección de menor riesgo y mayor impacto inmediato, independiente de si se hace la refactorización mayor de `resolve_order_emails()`.

---
*Auditoría de solo lectura. No se modificó ningún archivo, función, ruta, plantilla, base de datos ni configuración.*
