# Arquitectura Unificada de Emails y Entregas — Diseño Técnico
Fecha: 10 julio 2026 (actualizado tras la auditoría de ciclo de vida/marketing). Documento de **diseño únicamente**. No se modificó código de producción, no se crearon archivos de servicio, no se aplicó ningún parche a `_is_duplicate_send`, no se eliminó código legacy.

Este documento asume como contexto las dos auditorías previas: `docs/email_system_audit.md` (pipeline transaccional) y `docs/lifecycle_marketing_email_audit.md` (pipeline de ciclo de vida y marketing: leads, recuperación, feedback, upsell, newsletter).

---

## -1. Separación formal de dos dominios (actualización tras auditoría de ciclo de vida/marketing)

La auditoría de ciclo de vida confirmó que el sistema ya opera, de facto, con dos lógicas de decisión completamente distintas, aunque compartiendo la misma infraestructura de envío. El diseño que sigue formaliza esa separación en vez de mezclarla:

| | **Pipeline transaccional** | **Pipeline de ciclo de vida y marketing** |
|---|---|---|
| Pregunta que responde | "¿Qué compró y qué le corresponde entregar?" | "¿Sigue siendo elegible para recibir esto ahora mismo?" |
| Depende de un pedido | Sí, siempre | No necesariamente — puede ser un lead que nunca compró (`PreviewLead`) |
| Fuente de verdad de reglas | `resolve_entitlements()` / `build_delivery_plan()` (secciones 1-2 de este documento) | Reglas propias por automatización: ventanas de tiempo desde un evento (compra o creación de lead) + verificación de exclusión en el momento del envío |
| Prioridad de diseño | Garantizar que lo pagado SIEMPRE se entregue | Garantizar que NUNCA se envíe a quien ya no corresponde (ya compró, se dio de baja, ya se le envió) |
| Ejemplos | PDF, eBook permanente, eBook regalo, confirmación de impresión | Campaña Isabel (leads abandonados), feedback 24h, upsell 48h, aviso de vencimiento de eBook, newsletter |
| Estado que consulta | Registro transaccional nuevo (`delivery_id` con escritura atómica, sección 5) | `data/lead_follow_ups.json`, tabla `PreviewLead`, escaneo de `story_previews/*.json`, `NewsletterSubscriber.is_active` |

**Regla de diseño explícita: el pipeline de marketing NO llama a `resolve_order_emails()`/`resolve_entitlements()`.** Puede, como mucho, CONSULTAR de forma read-only si existe un pedido pagado para decidir excluirse (igual que ya hace hoy comprobando `paid=True` o `want_print`), pero nunca participa en la resolución de derechos ni en el plan de entregas transaccional. Esto evita acoplar una lista de reglas comerciales de venta (que cambian con frecuencia, precios, ventanas de tiempo, campañas) a la lógica crítica de "entregar lo que el cliente pagó".

Lo que SÍ comparten ambos dominios, y se mantiene así en el diseño: `email_service.py` como motor de envío y plantillas, el proveedor SMTP, los idiomas, `data/email_log.jsonl` como auditoría común, y el manejo de errores. El registro transaccional nuevo de la sección 5, en cambio, es **exclusivo del pipeline transaccional** — el pipeline de marketing sigue usando sus propios almacenes de estado (`lead_follow_ups.json`, `PreviewLead`, `NewsletterSubscriber`), que ya están diseñados correctamente para su propio propósito y no se tocan en esta migración.

**Hallazgo pendiente de decisión de negocio (no técnico) que quedó documentado en la auditoría de ciclo de vida:** ni la campaña Isabel ni el feedback/upsell verifican hoy el opt-out general de `NewsletterSubscriber.is_active`. Esto es una decisión de negocio (¿un email transaccional-adyacente como "feedback 24h" debe respetar la baja del newsletter general, o son canales independientes?), no algo que se resuelva solo con arquitectura — se deja marcado para que se decida antes de tocar esas funciones.

---

## -0.5. Semántica final de eBook permanente vs. eBook temporal de regalo

Se detectó y corrigió una ambigüedad de nombres real en el código legacy, señalada explícitamente por revisión: el campo `story_data['ebook_is_gift']` se usa en el código para DOS conceptos distintos que nunca deben confundirse:

1. **`admin_gift_book`** (antes escrito parcialmente como `ebook_is_gift=True` en `app.py` ~línea 12942): un libro COMPLETO regalado manualmente por un administrador. No depende de lo que el cliente pagó — se salta email y envío a impresión por diseño.
2. **Elegibilidad calculada de eBook temporal (6 meses)**: el cliente NO compró el eBook permanente, pero SÍ compró PDF y/o impreso, y por eso recibe acceso temporal de cortesía al visor. En el código legacy esto vive disperso bajo nombres distintos según el archivo: `_include_gift` (`_dispatch_printable_pdf_email`), `give_gift_ebook` (composición de libros personalizados), `_visor_is_gift_cs` (`confirm_and_send` para Quick Stories) — nunca se llamó igual dos veces, lo cual dificultaba auditar si eran la misma regla.

`OrderEntitlements` (en `services/shadow_delivery.py`) resuelve esto con nombres inequívocos:

| Campo | Significado | Origen legacy |
|---|---|---|
| `ebook_permanent_purchased` | El cliente compró el eBook permanente | `want_ebook` |
| `admin_gift_book` | Bandera administrativa de regalo total del libro | `admin_gift` |
| `legacy_admin_gift_flag_raw` | Valor crudo de `ebook_is_gift` — **solo diagnóstico**, nunca fuente de decisión | `ebook_is_gift` |
| `temp_gift_ebook_eligible` (calculado, no almacenado) | True solo si: pagado, NO es regalo admin, NO compró el eBook permanente, y SÍ compró PDF y/o impreso | (disperso: `_include_gift` / `give_gift_ebook` / `_visor_is_gift_cs`) |
| `temp_gift_ebook_source` (calculado) | `'pdf'` \| `'print'` \| `'pdf_and_print'` \| `'none'` | no existía antes como campo explícito |

**Regla de diseño:** ninguna función nueva lee `ebook_is_gift` como fuente de verdad para decidir el eBook temporal — se calcula exclusivamente desde `want_ebook`, `admin_gift`, `want_pdf` y `want_print`. El campo legacy solo se transporta para comparación/diagnóstico mientras conviven ambos sistemas.

## -0.4. Sobre `_include_gift` y variables equivalentes (`give_gift_ebook`, `_visor_is_gift_cs`)

Confirmado y aceptado: mientras dure el modo sombra, el shadow SÍ compara temporalmente contra estas variables legacy (es su función: detectar discrepancias). Pero **la arquitectura permanente no debe depender de ellas ni replicarlas como fuente**. Regla de corte para cuando la migración esté validada con datos reales de producción (ver sección "Dependencia crítica" más abajo):

- `_include_gift`, `give_gift_ebook` y `_visor_is_gift_cs` dejan de decidir.
- Las ramas legacy que hoy las calculan (tres implementaciones distintas de la misma regla, en tres archivos/funciones distintas) dejan de calcular el beneficio.
- El derecho a un único eBook temporal de 6 meses proviene EXCLUSIVAMENTE de `OrderEntitlements.temp_gift_ebook_eligible`, resuelto una sola vez por el orquestador común, no recalculado de forma independiente en cada punto de envío.

Esto todavía NO se ha hecho — ver sección "Dependencia crítica que bloquea el corte" al final de este documento.

## 0. Verificación previa: ¿es `_is_duplicate_send` adecuada para uso transaccional? (spoiler de la sección 4)

Antes de diseñar nada, se examinó la implementación real línea por línea (`services/email_service.py:60-137`):

- `log_email(...)`: abre `data/email_log.jsonl` en modo append (`'a'`) y escribe una línea JSON. **Sin lock, sin fsync, sin transacción.** En Linux, un `write()` de una sola línea corta a un archivo abierto en modo append es atómico a nivel de kernel para escrituras que caben en un solo syscall — pero Python bufferiza y no hay garantía documentada de que cada llamada sea un único `write()` del tamaño completo bajo carga concurrente alta. Es "probablemente seguro en la práctica actual", no "diseñado para ser seguro".
- `_is_duplicate_send(preview_id, email_type, days=30)`: **lee todo el archivo línea por línea cada vez**, buscando coincidencia de `preview_id` + `email_type` + `result == 'SENT'` dentro de una ventana de 30 días. No usa índice, no usa hash, no usa lock de lectura.
- **El defecto estructural más importante:** `_is_duplicate_send` se llama ANTES de enviar, y `log_email` se llama DESPUÉS de enviar — son dos operaciones separadas sin exclusión mutua entre ellas. Esto es exactamente el mismo patrón "check → trabajo lento → set" que ya causa las carreras documentadas en la auditoría con las flags de `story_data`. No resuelve el problema, lo traslada a otro archivo.
- Clave de deduplicación actual: `(preview_id, email_type)`, sin distinguir "alcance del derecho" (permanente vs. temporal) ni "pedido" (si el mismo preview_id se paga dos veces por productos distintos, por ejemplo compra el PDF y luego, semanas después, compra el libro impreso, la clave actual bloquearía indebidamente el segundo envío legítimo, porque no incluye ningún identificador de pedido/transacción).
- No maneja: envío exitoso + fallo de registro (quedaría sin loguear = invisible para el chequeo, próximo intento reenvía = falso negativo de duplicado); registro exitoso + fallo de envío real (no ocurre en el orden actual, porque se llama después del envío, pero un futuro mal uso podría invertir el orden); reinicio del servidor (sí sobrevive, es un archivo en disco, correcto en ese aspecto); dos hilos simultáneos (no hay lock, ambos pueden leer "no existe" antes de que ninguno escriba — carrera clásica); reenvío manual legítimo (no hay forma de decir "este reenvío es intencional, no lo cuentes como duplicado ni lo bloquees" — es binario).

**Conclusión de la sección 4 (adelantada aquí porque condiciona todo el diseño): opción C — `_is_duplicate_send`/`log_email_send`/`email_log.jsonl` sirven como capa de AUDITORÍA Y OBSERVABILIDAD (ya cumplen bien ese rol, no se tocan), pero NO son aptas para ser la fuente de verdad de idempotencia transaccional sin rediseño.** Se necesita un registro transaccional nuevo, específico para esto, con clave más rica y con atomicidad real (ver secciones 1, 4 y 5). El archivo actual se mantiene intacto, tal como pediste, y no se reutiliza sin cambios (se descarta la opción A explícitamente).

---

## 1. Resolución de derechos del pedido

### Principio
La resolución debe operar sobre **el pedido completo** (todo lo que el cliente compró en una misma transacción/preview_id, incluyendo compras posteriores sobre el mismo preview_id — p. ej. "compró PDF hoy, compra impreso el mes que viene"), no producto por producto. Hoy el bug ocurre precisamente porque cada función mira aisladamente "¿este story_data tiene want_pdf?" sin preguntar "¿qué otra cosa ya tiene o va a tener este pedido en total?".

### Estructura propuesta: `OrderEntitlements`

Un objeto explícito, construido una sola vez por una única función `resolve_entitlements(order_context) -> OrderEntitlements`, que NO recibe `story_data` completo como argumento — recibe un contexto mínimo y explícito:

```
OrderContext:
    order_id          # identificador estable del pedido/transacción (ver nota abajo)
    preview_id
    product_family     # 'quick_story' | 'personalized_book' | 'birthday' | 'gift_admin'
    purchased_items     # lista explícita: [{'sku': 'pdf', 'paid_at': ts}, {'sku': 'print', 'paid_at': ts}, {'sku': 'ebook_permanent', 'paid_at': ts}, ...]
    lang
    is_admin_gift        # bool, si viene de regalo administrativo (suprime entregas comerciales)
```

`order_id` no existe hoy como concepto explícito — actualmente todo se indexa por `preview_id`, que representa "una historia", no "un pedido". Si el mismo preview_id recibe dos compras separadas en el tiempo (PDF hoy, impreso el mes que viene), hoy ambas comparten preview_id pero son eventos de pago distintos. **Se propone introducir `order_id` = `f"{preview_id}:{payment_capture_id}"`** (el `capture_id` que ya devuelve PayPal en cada captura, y que hoy se descarta después de procesar el pago) como identificador de cada evento de compra individual, manteniendo `preview_id` como agrupador de "todo lo que pertenece a esta historia". Esto es lo que permite, en la sección 5, distinguir compras futuras del mismo cliente sin bloquearlas.

```
OrderEntitlements:
    order_id
    preview_id
    entitlements: [
        Entitlement(kind='pdf_printable', scope='order', source_order_id=...),
        Entitlement(kind='print_physical', scope='order', source_order_id=...),
        Entitlement(kind='ebook_permanent', scope='preview', source_order_id=...),   # scope='preview' porque es acceso de por vida a ESA historia, no del pedido puntual
        Entitlement(kind='ebook_temporary_gift', scope='preview', duration_days=180, source_order_id=...),
    ]
```

### Reglas de negocio, explícitas y centralizadas (única fuente de verdad)

| Compra | Entitlements resultantes |
|---|---|
| Solo PDF | `pdf_printable` + `ebook_temporary_gift` (180 días) |
| Solo impreso | `print_physical` + `ebook_temporary_gift` (180 días) |
| PDF + impreso (mismo pedido o pedidos distintos sobre el mismo preview_id) | `pdf_printable` + `print_physical` + **un único** `ebook_temporary_gift` |
| eBook permanente comprado (con o sin PDF/impreso) | `ebook_permanent` — **nunca coexiste con `ebook_temporary_gift` para el mismo preview_id**; si ya existe uno temporal y se compra el permanente después, el permanente reemplaza/absorbe al temporal (no se generan dos eBooks) |
| Regalo administrativo (`is_admin_gift=True`) | Ningún entitlement de tipo "entrega comercial" (no PDF, no print, no ebook_temporary) — puede generarse `ebook_permanent` interno si el admin lo marca explícitamente, pero sin pasar por email transaccional de venta |
| Compra futura sobre el mismo preview_id (p. ej. añade impreso después de haber comprado solo PDF) | Se resuelve un NUEVO `order_id`, pero el resolver debe consultar entitlements YA otorgados en `preview_id` antes de decidir si corresponde un nuevo `ebook_temporary_gift` — si ya existe uno vigente (temporal o permanente), NO se emite un segundo regalo. Esta es la razón por la que el resolver opera sobre el pedido completo Y el historial del preview_id, no solo sobre la compra puntual. |

La regla "un único eBook temporal, nunca dos" queda como **invariante de la función `resolve_entitlements`**, no como condicional repetida en cada orquestador — es la corrección estructural que resuelve el bug de origen de forma permanente y para cualquier combinación futura, incluida cualquier variante que agregue el cuento piloto.

---

## 2. Plan de entregas

A partir de `OrderEntitlements`, una segunda función pura, `build_delivery_plan(entitlements: OrderEntitlements) -> DeliveryPlan`, construye una lista de entregas concretas. Esta separación (derechos → plan) importa porque los derechos son "qué tiene permitido recibir el cliente" mientras que el plan es "qué eventos de entrega concretos hay que ejecutar y en qué archivos/canales" — permite, por ejemplo, que un mismo entitlement dispare acciones distintas según idioma o canal sin ensuciar la capa de reglas comerciales.

```
DeliveryItem:
    delivery_id        # identidad estable y única — ver sección 5
    delivery_type       # enum cerrado, ver tabla abajo
    entitlement_ref      # a qué entitlement corresponde
    payload_refs         # rutas de archivo esperadas (pdf_path, ebook_visor_url, etc.) — resueltas en ejecución, no en el plan
    depends_on           # ids de otras DeliveryItems que deben completarse antes (p. ej. print_confirmation depende de cp_order_submitted)
```

| `delivery_type` | Corresponde a | Depende de |
|---|---|---|
| `payment_confirmation` | Siempre que se confirma un pago | — |
| `generation_started` | Si el producto tiene fase de generación IA visible (actualmente confirmar si se usa en todos los flujos o solo algunos — pendiente de decisión de negocio) | `payment_confirmation` |
| `pdf_printable_delivery` | Si `pdf_printable` en entitlements | generación de PDF completa |
| `ebook_permanent_delivery` | Si `ebook_permanent` en entitlements | visor listo |
| `ebook_temporary_gift_delivery` | Si `ebook_temporary_gift` en entitlements (una sola vez por preview_id, ver sección 1) | visor listo |
| `print_production_confirmation` | Si `print_physical` en entitlements | pedido Cloudprinter enviado con éxito |
| `print_tracking` | Actualización de Cloudprinter vía webhook | pedido en tránsito |
| `admin_purchase_notification` | Siempre (interno) | payment_confirmation |
| `admin_print_order_notification` | Si `print_physical` | pedido Cloudprinter enviado |

Cada `DeliveryItem` tiene una identidad estable (sección 5) para que sea idempotente sin importar cuántas veces se reconstruya el plan (reconstruir el plan debe ser un cálculo puro y repetible, no un efecto secundario).

---

## 3. Orquestación

**Regla de diseño central: ningún punto de ejecución vuelve a decidir "¿corresponde X?" — solo pregunta "¿qué dice el plan que ya fue resuelto?" y ejecuta lo que falte.**

Los orquestadores existentes dejan de calcular reglas de negocio y pasan a ser **ejecutores de un plan ya resuelto**, cada uno responsable únicamente de la parte técnica que ya hace bien (generar el archivo, enviarlo, actualizar el estado):

- **`_compose_personalized_book_background`**: deja de decidir `want_pdf/want_ebook/want_print` internamente. Al iniciar, llama una sola vez a `resolve_entitlements` + `build_delivery_plan`, guarda el plan (ver sección 6, persistencia), y a partir de ahí solo ejecuta los `DeliveryItem` de tipo `print_production_confirmation`, `ebook_permanent_delivery`, `ebook_temporary_gift_delivery` que le correspondan como responsable técnico. Sigue haciendo la composición del libro exactamente igual.
- **`_dispatch_printable_pdf_email`**: deja de tener su propia condición `_include_gift` (la que se corrigió hoy). Solo ejecuta `pdf_printable_delivery` y, si el plan indica que también le toca a él el `ebook_temporary_gift_delivery` (por diseño de threading, puede seguir siendo el hilo que ejecuta esa entrega), verifica contra el registro transaccional (sección 4) si ya fue entregado por otro hilo antes de enviarlo — no vuelve a preguntar "¿corresponde?", solo pregunta "¿ya se hizo?".
- **`_process_ebook_generation`** (Quick Stories): mismo tratamiento — se apoya en el plan ya resuelto para decidir qué `DeliveryItem` ejecutar, no en sus propias condiciones `want_*`.
- **`_process_quick_story_print`**: ejecutor único de `print_production_confirmation` para QS; antes de someter el pedido a Cloudprinter, consulta el registro transaccional para el `delivery_id` de tipo `print_physical` — si ya existe un registro `sent`/`processing` para ese `order_id`, no reenvía a Cloudprinter (esto cierra el riesgo real de doble pedido físico detectado en la auditoría, no solo el de doble email).
- **`/api/confirm-and-send`**: dejará de recalcular reglas de negocio. Su única función pasa a ser: (a) si no existe un plan resuelto para ese `preview_id`/`order_id`, resolverlo; (b) recorrer el plan y ejecutar cualquier `DeliveryItem` que el registro transaccional marque como pendiente/fallido; (c) no tiene ninguna rama propia de "PDF pendiente pero eBook ya enviado" — eso ya lo resuelve el estado del plan.
- **Reenvíos administrativos**: en vez de "limpiar una flag y volver a invocar la función automática completa" (riesgo de carrera con un flujo automático aún corriendo), un reenvío admin se convierte en una operación explícita: "ejecutar de nuevo el `DeliveryItem` con id X, marcado como `manually_resent`" — reutiliza el mismo executor técnico (por ejemplo, la función que arma y envía el email de PDF), pero pasa por el registro transaccional con un flag de "override intencional" en vez de simplemente borrar el estado (ver sección 5, último punto).

**Lo que NO cambia:** las funciones que generan archivos (PDF, visor, composición del libro), que arman el HTML de cada email, y que hablan con Cloudprinter — siguen siendo las mismas, se les extrae solo la lógica de "decidir qué toca" y "verificar si ya se hizo", que se centraliza.

---

## 4. Idempotencia transaccional — conclusión formal

Ya cubierto en la sección 0. Resumen de la matriz de comportamiento evaluada sobre la implementación actual:

| Escenario | Comportamiento actual de `_is_duplicate_send`/`log_email` |
|---|---|
| Clave exacta | `(preview_id, email_type)` — sin `order_id`, sin distinguir alcance permanente/temporal más allá del nombre del `email_type` que se le pase |
| Cuándo se consulta | Antes de enviar, solo en 2 de ~25 funciones |
| Cuándo se registra | Después de enviar (o después de fallar, con `result='ERROR'`) |
| Atomicidad | Ninguna — check y set son dos operaciones separadas sin lock compartido |
| Dos hilos simultáneos | Carrera: ambos pueden leer "no enviado" antes de que cualquiera escriba |
| Dos funciones distintas | Mismo problema — el archivo es compartido pero no hay ninguna sección crítica protegida |
| Envío OK + registro falla | Próxima verificación no encuentra el registro → puede reenviar (falso negativo) |
| Registro OK + envío falla | No aplica en el orden actual (se registra después del envío) — pero es un riesgo si algún día se invierte el orden por error |
| Tras reinicio | Correcto — el archivo persiste en disco |
| Dos pedidos distintos, mismo email_type | Bloquearía indebidamente un envío legítimo si ambos comparten `preview_id` (ver ejemplo de compra futura en sección 1) |
| Reenvío manual legítimo | No hay forma de distinguirlo de un duplicado accidental — es binario |

**Decisión: opción C.** Se diseña un **registro transaccional nuevo** (ver sección 5), y `email_log.jsonl` + `_is_duplicate_send` se conservan sin cambios como lo que ya son: un log de auditoría/observabilidad legible por humanos y por el CRM interno (guarda también el cuerpo HTML para revisión). No se fusionan ni se reemplazan — cumplen roles distintos.

---

## 5. Clave de idempotencia — diseño del registro transaccional

Clave propuesta: **`delivery_id = f"{order_id}:{delivery_type}:{entitlement_scope}"`**, equivalente a lo que pediste evaluar (`order_id + delivery_type + entitlement_scope`), con matices:

- `order_id`: para entregas de alcance `'order'` (PDF, impreso, confirmación de pago) — así una compra futura sobre el mismo `preview_id` genera un `order_id` distinto y por lo tanto un `delivery_id` distinto, sin bloquear la compra nueva.
- Para entregas de alcance `'preview'` (eBook permanente, eBook temporal de regalo — porque el "derecho" es sobre la historia, no sobre la transacción puntual), la clave usa `preview_id` en vez de `order_id`: `delivery_id = f"{preview_id}:{delivery_type}:preview"`. Esto es lo que garantiza estructuralmente que nunca haya dos `ebook_temporary_gift_delivery` para el mismo preview_id, sin importar cuántas veces se recalcule el plan o cuántos pedidos distintos lo disparen.

**Propiedades que esta clave cumple:**
- Impide duplicados dentro del mismo pedido: mismo `order_id` + mismo `delivery_type` = mismo `delivery_id`, se resuelve una sola vez.
- Permite compras futuras del mismo cliente: nuevo `order_id` (por nuevo `payment_capture_id`) = claves nuevas para las entregas de alcance `'order'`.
- Distingue eBook permanente de temporal: son `delivery_type` distintos (`ebook_permanent_delivery` vs `ebook_temporary_gift_delivery`), y la regla de negocio de la sección 1 impide que ambos coexistan activos para el mismo `preview_id` a nivel de entitlement, no a nivel de delivery — dos capas de protección.
- Distingue PDF de impresión: `delivery_type` distintos (`pdf_printable_delivery` vs `print_production_confirmation`).
- Reenvío manual explícito sin alterar el estado automático: se propone que el registro transaccional permita **múltiples intentos por `delivery_id`**, no solo un booleano — cada intento es una fila con `attempt_number`, `trigger` (`'automatic'` | `'manual_admin'` | `'confirm_and_send'`), `status`, `ts`. La pregunta "¿ya se entregó?" se responde mirando si existe algún intento con `status='sent'`, pero un reenvío manual puede registrar un nuevo intento explícitamente marcado como `manually_resent` sin necesitar borrar ni mutar el intento anterior — soluciona el problema actual de "limpiar la flag" que puede chocar con un flujo automático en curso.
- Funciona entre funciones distintas y tras reinicios: al ser un registro persistente consultado con el mismo `delivery_id` sin importar qué función lo consulte, dos ejecutores distintos (p. ej. `_compose_personalized_book_background` y `_dispatch_printable_pdf_email`) que compitan por el mismo `delivery_id` verán el mismo estado.

**Atomicidad real (lo que `email_log.jsonl` no tiene):** se requiere que "verificar si ya existe" + "reservar el intento" sea una operación atómica, no dos pasos separados. Esto exige un almacén con soporte de escritura condicional (insert-if-not-exists / unique constraint), no un archivo JSONL de solo apéndice. Opciones a evaluar en la fase de implementación (no se decide aquí): tabla SQL con constraint único sobre `delivery_id` + intento "en progreso" (si ya existe una fila con `status IN ('processing','sent')`, el segundo intentante falla al insertar y aborta), o un lock distribuido si se prefiere mantener JSON. La recomendación de diseño es una tabla, dado que ya existe uso de SQLAlchemy en el proyecto — se decide en la fase de implementación, no ahora.

---

## 6. Estados de entrega

Sí son necesarios, y deben persistirse en el mismo registro transaccional de la sección 5 (no en `story_data`, que es el JSON de la historia, ni en `email_log.jsonl`, que es solo auditoría). Estados propuestos:

- `pending`: el plan lo incluye pero aún no se ha intentado ejecutar (por ejemplo, esperando a que termine la composición del libro).
- `processing`: un ejecutor tomó la entrega y está trabajando en ella (generando archivo / enviando email) — este es el estado que reemplaza a los locks en memoria actuales, porque persiste y es visible entre procesos/hilos.
- `sent`: completada con éxito.
- `failed`: el intento terminó en error (archivo no generado, SMTP caído, etc.).
- `retryable`: variante de `failed` que indica explícitamente que es seguro reintentar automáticamente (vs. un fallo que requiere intervención humana, como una dirección de email inválida).
- `manually_resent`: se registra como un nuevo intento sobre un `delivery_id` que ya estaba en `sent`, disparado explícitamente por un admin — no sustituye el estado anterior, se agrega como evento nuevo (ver sección 5).

No se implementan ahora — quedan documentados para la fase de implementación.

---

## 7. Diseño de comportamiento ante fallos y reintentos

| Caso | Comportamiento diseñado |
|---|---|
| Archivo generado, email falla | El `delivery_id` queda en `retryable` (el archivo ya existe, no se regenera). Un reintento automático o `/api/confirm-and-send` puede tomar el `delivery_id` en `retryable` y solo reintentar el envío. |
| Email enviado, actualización de estado falla | Se recomienda escribir el estado `processing`→intento de envío→`sent` en ese orden con el registro transaccional como último paso reintentable de forma segura: si falla la escritura del estado final pero el email ya salió, un reintento posterior debe primero verificar (fuera de banda, ej. contra `email_log.jsonl` como respaldo de auditoría) si ya se envió antes de reenviar — este es un caso límite donde la auditoría (sección 0) SÍ sirve como red de seguridad secundaria, aunque no sea la fuente de verdad primaria. |
| Webhook duplicado (Cloudprinter) | El `delivery_id` de `print_tracking` es por evento de estado, no por pedido — se resuelve con un identificador que incluya el estado/timestamp que manda Cloudprinter, evitando reprocesar el mismo evento dos veces. |
| Usuario recarga la página de checkout | El plan se resuelve de forma idempotente (recalcularlo no crea nuevas entregas si el `order_id` es el mismo); el registro transaccional bloquea cualquier segundo intento de ejecución mientras el primero esté en `processing` o ya esté en `sent`. |
| `confirm_and_send` se ejecuta después del flujo automático | Solo actuará sobre `DeliveryItem`s que el registro marque como `pending`/`failed`/`retryable`; los que ya estén en `sent` se omiten sin re-ejecutar nada. |
| Dos hilos intentan la misma entrega | El segundo hilo, al intentar reservar el `delivery_id` en `processing`, encuentra que ya existe una fila activa y aborta su intento (requiere la escritura condicional atómica de la sección 5). |
| Reinicio del servidor durante el envío | Al reiniciar, un proceso de reconciliación (ejecutado al arrancar, similar al scheduler de limpieza de fotos que ya existe) revisa entregas en `processing` con timestamp antiguo (p. ej. >10 min) y las pasa a `retryable` para que puedan reintentarse — evita que una entrega quede "colgada" para siempre por un proceso muerto. |
| Proveedor de email temporalmente no disponible | Se marca `retryable` con motivo `smtp_unavailable`; un job de reintento periódico (nuevo, a diseñar en implementación) reintenta con backoff — hoy no existe backoff automático, tal como se documentó en la auditoría. |
| Reenvío manual solicitado por administración | Se ejecuta como un intento nuevo `trigger='manual_admin'` sobre un `delivery_id` existente, sin alterar el historial de intentos previos — queda auditable quién y cuándo pidió el reenvío. |

---

## 8. Compatibilidad garantizada

Este diseño es deliberadamente una capa de **decisión + registro de estado**, no una capa de presentación ni de integración externa. No toca:
- Las funciones que generan el HTML de cada email (`send_ebook_email`, `send_story_email_with_attachments`, etc.) — se siguen llamando igual, con los mismos textos, asuntos e idiomas.
- Los archivos entregados (PDF, visor) — se siguen generando con el mismo código.
- Los enlaces incluidos en los emails — sin cambios.
- Las reglas comerciales vigentes — se formalizan tal cual están hoy (sección 1), no se alteran precios ni condiciones.
- Cloudprinter — la integración y sus llamadas siguen intactas; solo se le agrega una verificación previa de idempotencia antes de someter un pedido.
- El comportamiento visible para el cliente — mismo número y contenido de emails que hoy, cuando el sistema funciona sin errores; la diferencia solo aparece en los casos borde de duplicado/carrera que hoy fallan silenciosamente.

---

## 9. Migración por fases (segura y reversible, sin borrar legacy)

### Fase 0 — Preparación (sin tocar flujo real)
- Archivos afectados: nuevos únicamente (p. ej. `services/order_entitlements.py`, `services/delivery_plan.py`, tabla/almacén nuevo para el registro transaccional).
- Qué se añade: `resolve_entitlements()`, `build_delivery_plan()`, el almacén de estados, sin que ningún orquestador existente los llame todavía.
- Qué se sustituye: nada.
- Código antiguo: 100% intacto y en producción.
- Pruebas: unitarias sobre `resolve_entitlements`/`build_delivery_plan` con la matriz de combinaciones de la sección 1, corriendo en paralelo sin afectar el flujo real (modo "shadow": se calcula el plan y se loguea, pero no se usa para decidir nada aún).
- Criterio de aprobación: el plan calculado en modo shadow coincide, para pedidos reales recientes, con lo que efectivamente se envió (comparado contra `email_log.jsonl`).
- Rollback: trivial, basta con no llamar a las funciones nuevas.

### Fase 1 — Un solo orquestador migrado (el de mayor riesgo, el que ya tuvo el bug)
- Archivos afectados: `app.py` (`_dispatch_printable_pdf_email`, `_compose_personalized_book_background`).
- Qué se añade: llamada a `resolve_entitlements`/`build_delivery_plan` al inicio; verificación contra el registro transaccional antes de cada envío.
- Qué se sustituye: la condición local `_include_gift` y las llamadas directas a `send_ebook_email(is_gift=...)` sin verificación previa.
- Código antiguo: las flags de `story_data` (`gift_ebook_sent`, etc.) se **mantienen en paralelo** durante esta fase como respaldo de compatibilidad y para comparación, no se eliminan.
- Pruebas: casos de la sección 10 específicos a Personalized Books (con impreso, con PDF, con PDF+impreso).
- Criterio de aprobación: cero duplicados y cero omisiones en un lote de pedidos de prueba en sandbox de PayPal + Cloudprinter sandbox, replicando exactamente los combos de la tabla de la sección 1.
- Rollback: revertir el archivo a la versión anterior (las flags de `story_data` seguían siendo escritas en paralelo, así que el estado no queda inconsistente).

### Fase 2 — Quick Stories
- Archivos afectados: `_process_ebook_generation`, `_process_quick_story_print`.
- Mismo patrón que la Fase 1.
- Pruebas: casos de QS digital y QS impresa de la sección 10.

### Fase 3 — Recuperación y reenvíos
- Archivos afectados: `/api/confirm-and-send`, rutas admin de reenvío.
- Qué se añade: lectura del plan + registro transaccional en vez de recalcular reglas.
- Qué se sustituye: las 2-3 ramas de reglas de negocio propias de `confirm_and_send`.
- Código antiguo: se conserva comentado o detrás de un flag de configuración por un ciclo de lanzamiento, no se borra.
- Pruebas: recuperación manual tras fallo simulado, reenvío admin durante flujo automático en curso (prueba de carrera intencional).

### Fase 4 — Retiro de flags legacy (fuera de alcance de esta certificación)
- Solo después de varios ciclos sin incidentes, se evalúa si las flags de `story_data` pueden dejar de escribirse. Requiere aprobación explícita separada — no se hace como parte de esta migración.

---

## 10. Matriz de pruebas obligatorias

| Caso | Emails esperados | Nº exacto | Archivos esperados | Registros esperados | Qué NO debe duplicarse |
|---|---|---|---|---|---|
| QS digital, solo PDF | confirmación de pago, PDF | 2 | PDF imprimible | `delivery_id` order:pdf, order:payment_confirmation en `sent` | eBook regalo (no aplica si no hay want_ebook definido como digital-only sin PDF... verificar con negocio si QS digital sin PDF entrega algo) |
| QS digital, PDF sin eBook | confirmación, PDF, eBook regalo | 3 | PDF | 3 delivery_ids `sent` | Un segundo eBook regalo |
| QS impresa | confirmación, confirmación de impresión, eBook regalo (si no compró eBook), notificación admin | 3-4 | Ninguno al cliente si es 100% impreso sin PDF opcional | delivery_ids de `print_physical` + `ebook_temporary_gift` (preview scope) | Segundo pedido a Cloudprinter si se reintenta |
| PB con impreso solamente | confirmación, confirmación de impresión, eBook regalo | 3 | — | igual que arriba | eBook regalo duplicado si además se agrega PDF después |
| PB con PDF solamente | confirmación, PDF, eBook regalo | 3 | PDF | — | — |
| PB con PDF + impreso | confirmación, PDF, confirmación de impresión, **un único** eBook regalo | 4 | PDF | delivery_id `preview:ebook_temporary_gift` en `sent` una sola vez pese a dos order_ids distintos si se compraron por separado | **Éste es el caso que falló hoy — debe quedar como prueba de regresión permanente** |
| eBook permanente comprado (con o sin PDF/impreso) | confirmación, [PDF/impreso si aplica], eBook permanente | variable | — | `ebook_permanent_delivery` en `sent`, ningún `ebook_temporary_gift_delivery` creado | Que se genere el regalo temporal además del permanente |
| Cuento piloto Centinela | mismo comportamiento que cualquier PB con su combo de compra (usa el mismo `product_family='personalized_book'`) | según combo | — | — | Cualquier discrepancia respecto a los otros 8 libros de PB confirmaría que la unificación funciona igual para libros nuevos sin código especial |
| Webhook duplicado (Cloudprinter reenvía el mismo evento) | tracking una sola vez | 1 | — | delivery_id de tracking con clave que incluya el evento, no solo el pedido | Segundo email de tracking idéntico |
| Ejecución simultánea (dos hilos, mismo `delivery_id`) | El email correspondiente, una sola vez | 1 | El archivo generado una sola vez | Solo un intento pasa a `sent`, el otro debe fallar la reserva atómica | El email o el archivo generándose dos veces en paralelo |
| Recuperación con `/api/confirm-and-send` tras flujo automático completo | Ninguno adicional | 0 | Reutiliza los existentes | Todos los delivery_ids ya en `sent`, ninguno re-ejecutado | Cualquier reenvío |
| Reenvío administrativo explícito | El email solicitado, con trigger `manual_admin` | 1 (adicional, intencional) | Reutiliza archivo existente | Nuevo intento registrado sin alterar el `sent` original | Que el reenvío se confunda con un duplicado automático y quede bloqueado, o que dispare además el resto del plan |
| Fallo simulado del proveedor SMTP | Ninguno hasta que se resuelva | 0 en el intento fallido | Archivo ya generado se conserva | delivery_id en `retryable` | Reintentos infinitos sin backoff |
| Reinicio/reintento del servidor durante un envío en curso | El email se completa una sola vez tras la reconciliación | 1 | — | delivery_id pasa de `processing` colgado a `retryable` tras timeout, luego a `sent` | Que quede en `processing` para siempre, o que se reintente mientras el proceso original seguía vivo |

**Huecos de información cerrados tras verificación de código (10 julio 2026):**

- **`generation_started`**: el nombre real en el código es `generation_started_at` (timestamp, no email). Se usa únicamente para calcular timeouts de composición en `check_generation_status` (`app.py` ~líneas 6363 y 6469-6470: 20 y 25 minutos respectivamente). **No dispara ningún email.** Existe una función `send_generation_started_email` definida en `services/email_service.py`, pero **no tiene ningún call site activo** en los flujos de pago actuales — es código muerto/no conectado, no una automatización desactivada a propósito. Se deja tal cual (no se elimina, siguiendo la instrucción de no borrar código sin auditoría de limpieza previa).
- **QS digital sin PDF (Quick Story 100% digital, sin PDF ni impreso)**: usa los mismos campos `want_pdf`/`want_print`/`want_ebook` que Personalized Books. El envío final NO ocurre en `_dispatch_cart_item` (que solo dispara generación en background + el email de recuperación) sino en `/api/confirm-and-send` (`app.py:7194`), tras la aprobación manual del cliente en la pantalla de revisión. Si `want_pdf=False` y `want_print=False`, la única entrega es el visor — con el mismo cálculo de eBook temporal (`_visor_is_gift_cs = not want_ebook`) que en cualquier otro producto. Esta fila de la matriz queda: **1 email (visor, gift o permanente según `want_ebook`), 0 adjuntos PDF**.
- Ambos hallazgos ya están reflejados en el modo shadow (`services/shadow_delivery.py`), que ahora también instrumenta el punto `confirm_and_send`, cubriendo el caso de Quick Story digital sin PDF.

---

## Resumen de decisiones tomadas en este diseño

- **No se reutiliza `_is_duplicate_send` tal cual** (descartada la opción A) — se diseña un registro transaccional nuevo con clave `order_id`/`preview_id` + `delivery_type` + `entitlement_scope`, atomicidad real, y estados explícitos.
- **`email_log.jsonl` se mantiene sin cambios** como capa de auditoría/CRM, con un rol claramente distinto del registro transaccional.
- **La resolución de derechos ocurre sobre el pedido completo**, no por producto aislado, y es la única fuente de verdad para la regla "un único eBook temporal de regalo".
- **Ningún orquestador existente vuelve a decidir reglas de negocio** tras la migración — todos pasan a ser ejecutores de un plan ya resuelto, verificando contra el registro transaccional antes de actuar.
- **Migración en 4 fases, reversible, sin borrar código legacy**, con el caso "PDF + impreso" (el que falló hoy) como prueba de regresión obligatoria y permanente.

Este documento no implementa nada por sí solo salvo la Fase 0 (modo shadow, ya en curso — ver siguiente sección).

---

## 11. Dependencia crítica que bloquea el corte a Fase 1+ (legítimo punto de pausa)

El criterio de aprobación de la Fase 0, definido en este mismo documento (sección 9), es: *"el plan calculado en modo shadow coincide, para pedidos reales recientes, con lo que efectivamente se envió"*. Esa validación requiere, por definición, **tráfico real de producción** (pedidos pagados reales pasando por `confirm_and_send` / `_dispatch_printable_pdf_email` con el shadow activo, comparando contra lo que el código legacy decidió de verdad).

Esto entra en conflicto directo con dos restricciones explícitas de este trabajo:
- "No enviar emails reales."
- "No usar datos de prueba reales" (no se debe simular producción con pedidos falsos para forzar la validación).

Por lo tanto, **avanzar a la Fase 1 (migrar el primer orquestador para que decida en base al plan, no solo lo registre) sin datos reales de shadow validados sería exactamente el tipo de "parche improvisado sin evidencia" que este trabajo tiene prohibido**. No es una limitación de esfuerzo — es una dependencia real: no existe manera segura de certificar que el nuevo cálculo coincide con el legacy sin observar tráfico real, y no se puede generar tráfico real en este entorno sandbox sin violar las reglas del encargo.

**Estado dejado en este repositorio**: el modo shadow (Fase 0) queda completo, corriendo en paralelo sin alterar ningún envío real, instrumentado en los dos puntos de entrega que importan (`_dispatch_printable_pdf_email` y `confirm_and_send`), con semántica de entitlements corregida y con pruebas unitarias que fijan el comportamiento esperado (`tests/test_shadow_delivery.py`, 26/26 OK). Cuando el usuario decida activar esto en el VPS real (fuera del alcance de este trabajo, que es solo GitHub), el log `data/shadow_delivery_log.jsonl` acumulará comparaciones reales; a partir de un volumen razonable de coincidencias sin mismatches inesperados, la Fase 1 puede aprobarse con evidencia real en vez de supuestos.
