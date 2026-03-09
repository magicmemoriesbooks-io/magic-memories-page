# Plantilla: Cuentos Rápidos Kids (3-8 años)

## Sección
**Quick Stories Kids** - Cuentos cortos personalizados para niños de 3 a 8 años.
**NO aplica para:** Cuentos de bebés (0-2), Libros Personalizados (Dragon Garden, Magic Chef, etc.), ni Haz tu Historia.

## Resumen
Plantilla para crear nuevos Quick Stories de niños 3-8. Incluye modelo de IA, estructura de prompts, estructura PDF, integración Paddle/Lulu, especificaciones de impresión saddle stitch, y checklist de implementación.

---

## 1. Arquitectura de Archivos

```
services/quick_stories/
├── __init__.py           # Exports del módulo
├── checkout.py           # QUICK_STORY_IDS, precios, config checkout
├── pdf_service.py        # PDFs Lulu (interior + cover spread)
└── stories.py            # Catálogo QUICK_STORIES (títulos, age_range)

services/fixed_stories.py         # Definición de páginas, prompts, textos
services/replicate_service.py     # Generación FLUX 2 Dev (imágenes)
services/pdf_service.py           # Funciones PDF principales (create_kids_quick_story_pdf)
services/lulu_api_service.py      # API Lulu para impresión
services/lulu_storage.py          # Almacenamiento PDFs para Lulu
services/email_service.py         # Envío de emails post-pago

templates/
├── story_preview_limited.html    # Preview pre-pago (cover + texto)
├── order_complete.html           # Post-pago (galería + regenerar)
├── checkout_quick_story.html     # Checkout Paddle ($25 digital / $29-$49 impreso)

app.py                            # Rutas principales (generate-fixed-story, etc.)
```

---

## 2. Modelo de Imágenes

### FLUX 2 Dev para todo
**TODAS las imágenes de Quick Stories Kids usan FLUX 2 Dev** (`black-forest-labs/flux-2-dev`):
- Preview de personaje → FLUX 2 Dev (sin imagen de referencia, solo texto)
- Cover (copiada desde preview) → gratis (no genera nueva imagen)
- 7 escenas + 1 cierre = 8 imágenes → FLUX 2 Dev (con imagen de referencia del cover)

### Consistencia visual
- Preview y escenas usan el MISMO modelo (FLUX 2 Dev) para estilo visual idéntico.
- Las escenas usan `reference_images` (el cover_clean.png) para mantener consistencia del personaje.
- El preview NO usa imagen de referencia (es la primera imagen que se genera).

### Costo por Historia
- Character preview: 1 imagen — se genera ANTES del pago
- Cover: Copiada del preview (gratis) — se genera ANTES del pago
- Escenas: 7 escenas + 1 cierre = 8 imágenes — se generan DESPUÉS del pago
- **Total si paga: ~9 llamadas FLUX 2 Dev**
- **Total si NO paga: ~1 llamada (solo character preview)**

### Parámetros FLUX 2 Dev (NUNCA CAMBIAR)
```python
FLUX_2_DEV_PARAMS = {
    "guidance": 3.5,            # SIEMPRE 3.5 - NUNCA subir (causa alucinaciones)
    "num_inference_steps": 28,  # Si falta detalle, subir a 25-30, NO subir guidance
    "output_format": "png",
    "aspect_ratio": "1:1"
}
```
**REGLA**: Si la imagen carece de detalle, subir `num_inference_steps` a 25-30. NUNCA subir `guidance` por encima de 3.5.

---

## 3. Estructura de Prompts (CRÍTICO)

### 3.1 Formato Obligatorio por Secciones
**TODOS los prompts de Kids Quick Stories DEBEN usar esta estructura.** Validada con dragon_friend (Feb 2026). FLUX 2 Dev interpreta mejor cuando las instrucciones están separadas por secciones claras.

```
Disney Pixar 3D style illustration.
CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin,
           [expresión facial específica de la escena].
OUTFIT: [ropa exacta del personaje - consistente en todas las escenas].
ACTION: {gender_word} is [POSE EXACTA] with {companion_desc} [acción del companion].
SETTING: [ESCENARIO] WIDE VIEW, [detalles del entorno, luz, hora].
ATMOSPHERE: [Efectos mágicos, iluminación, emociones].
STRICT: Only ONE {gender_word}, only ONE [companion]. [companion] MUST BE [TAMAÑO] as {gender_word}.
        {gender_word} is 100% human, with a completely normal body, two arms, two legs,
        smooth skin, and normal child anatomy, no duplicates. {style}
```

### 3.2 Reglas del Formato
1. **{hair_desc} y {eye_desc} SIEMPRE separados** - NUNCA concatenar pelo+ojos en una variable.
2. **Companions con NOMBRE fijo** - SPARK (dragón), LILA (unicornio), etc. Definir como constante en fixed_stories.py.
3. **STRICT siempre al final** - Restricciones explícitas: "no duplicates", "100% human", tamaño relativo.
4. **"Disney Pixar 3D style illustration"** como inicio del prompt.
5. **WIDE VIEW** se pone en SETTING, no al inicio.
6. **OUTFIT consistente** - El mismo outfit en TODAS las escenas del cuento.

### 3.3 Variables Disponibles
| Variable | Preview | Cover | Scenes | Closing |
|----------|---------|-------|--------|---------|
| {hair_desc} | ✅ | ✅ | ✅ | ✅ |
| {eye_desc} | ✅ | ✅ | ✅ | ✅ |
| {skin_desc} | ✅ | ❌ | ❌ | ❌ |
| {skin_tone} | ✅ | ✅ | ✅ | ✅ |
| {gender_word} | ✅ | ✅ | ✅ | ✅ |
| {age_display} | ✅ | ✅ | ✅ | ✅ |
| {hair_action} | ✅ | ✅ | ✅ | ✅ |
| {companion_desc} | ✅ | ✅ | ✅ | ❌ |
| {name} | ❌ | ✅ | ✅ | ✅ |
| {style} | ✅ | ✅ | ✅ | ✅ |
| {o_a} | ❌ | ❌ | ✅ (textos) | ❌ |

### 3.4 Preview Prompt (Ejemplo: dragon_friend)
El preview usa el MISMO prompt que la escena 1 para máxima consistencia visual.
```python
"preview_prompt_override": """Disney Pixar 3D style illustration.
CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin,
curious wonder-filled expression, gentle smile.
OUTFIT: Soft blue tunic with gold leaf embroidery, brown pants, small boots.
ACTION: {gender_word} is standing beside a majestic old oak tree, looking UP in amazement
at {spark_desc} who has just stepped out from behind the trunk. Spark stands at FULL HEIGHT
towering over {gender_word}, Spark tilts head curiously looking DOWN at {gender_word},
tiny puff of sparkly smoke coming from Spark's snout.
SETTING: Enchanted garden WIDE VIEW, glowing flowers, butterflies, mushroom circles,
stone path, morning golden sunlight filtering through tree canopy.
ATMOSPHERE: Discovery and wonder, warm golden light, magical sparkles in the air.
STRICT: Only ONE {gender_word}, only ONE baby dragon Spark. Spark MUST BE TWICE AS TALL
as {gender_word}. {gender_word} is 100% human, with a completely normal body, two arms,
two legs, smooth skin, and normal child anatomy, no duplicates. {style}"""
```

### 3.5 Cover Template
La portada se genera reutilizando la imagen del character preview (gratis).
Se le superpone el título en morado pastel con borde blanco fino (sin franja/banner/gradiente).

```python
"cover_template": """Disney Pixar 3D style illustration.
CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin,
warm loving smile, bright eyes full of adventure.
OUTFIT: [mismo outfit del cuento].
ACTION: {gender_word} is [POSE CON COMPANION - interacción cariñosa con {companion_desc}].
SETTING: [Escenario amplio y colorido], WIDE VIEW.
ATMOSPHERE: Magical book cover composition centered, [efectos mágicos].
STRICT: Only ONE {gender_word}, only ONE [companion]. {gender_word} is 100% human. {style}"""
```

**Estilo del título en la portada:**
- Color título: Morado pastel RGB(180, 130, 210)
- Color autor: Morado más oscuro RGB(160, 110, 190)
- Borde: Blanco fino (2px offset en 8 direcciones)
- SIN franja/banner/gradiente de fondo
- Función: `create_cover_from_character()` en `services/replicate_service.py`

### 3.6 Scene Templates
Los `scene_template` contienen TODA la información del personaje. Pasan directo a FLUX 2 Dev con la imagen de referencia del cover.

```python
"scene_template": """Disney Pixar 3D style illustration.
CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin,
[EXPRESIÓN de esta escena].
OUTFIT: [mismo outfit - repetir exacto en cada escena].
ACTION: {gender_word} is [POSE EXACTA] with {companion_desc} [acción del companion].
SETTING: [ESCENARIO] WIDE VIEW, [detalles, luz, hora].
ATMOSPHERE: [Efectos mágicos, emoción].
STRICT: Only ONE {gender_word}, only ONE [companion]. [tamaño relativo].
{gender_word} is 100% human, no duplicates. {style}"""
```

**Reglas de escenas:**
- Cada escena REPITE CHARACTER completo (pelo, ojos, piel, outfit) para consistencia.
- El companion se describe usando la constante ({spark_desc}, {lila_desc}, etc.).
- Para escenas con MÚLTIPLES personajes, usar CHARACTER 1, CHARACTER 2, CHARACTER 3.
- COMPOSITION al final para escenas multi-personaje (escalas y separación clara).

### 3.7 Closing Template
```python
"closing_template": """Disney Pixar 3D style illustration.
CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin,
warm proud smile, eyes sparkling with confidence and joy.
OUTFIT: [mismo outfit].
ACTION: {gender_word} is [POSE SOLITARIA - sin companion], [acción emotiva de cierre].
SETTING: [Escenario hermoso] WIDE VIEW, [sunset/golden hour].
ATMOSPHERE: Triumphant peaceful moment, warm golden light, magical sparkles.
STRICT: Only ONE {gender_word}, NO dragon, NO companion, NO other characters. {style}"""
```
**REGLA**: El closing NUNCA incluye al companion. Es el niño solo, en momento de paz/triunfo.

### 3.8 Closing Message y Firma
Cada cuento tiene un mensaje motivacional personalizado en la página de cierre:
```python
"closing_message_es": "{name}, tu corazón valiente puede hacer florecer la magia en cualquier lugar.",
"closing_message_en": "{name}, your brave heart can make magic bloom anywhere."
```
La firma es dinámica según el idioma **del cuento** (no de la interfaz):
- Español: "tus amigos de Magic Memories Books"
- Inglés: "your friends at Magic Memories Books"

**Implementación de idioma en firma (CRÍTICO)**:
- Templates HTML (`story_preview_full.html`, `order_complete.html`): Usan `story_data.get('lang', story_data.get('language', lang))` para detectar idioma del cuento
- PDF (`pdf_service.py` línea 1534): Usa variable `language` pasada a la función
- **NO usar `lang` del context_processor** (ese es el idioma de la interfaz del navegador, no del cuento)

### 3.9 Companion como Constante
Definir cada companion como constante al inicio de `fixed_stories.py`:
```python
SPARK_DESC = "SPARK: A massive baby dragon with the proportions of a puppy but the size
of a giant. Spark is a huge creature, TOWERING over the {gender_word}. He has shimmering
emerald-green scales, a very chubby and round body, large golden eyes, and small translucent
wings. He has a soft cream-colored belly and two tiny horns. His mass is five times larger
than the {gender_word}"
```
Se formatea al generar: `spark_desc=SPARK_DESC.format(gender_word=gender_word)`

### 3.10 Negative Prompt (OBLIGATORIO)
```python
NEGATIVE_PROMPT = """text, watermark, signature, logo, artist signature, copyright,
words, letters, numbers, writing, stamp, badge, label, banner, handwriting,
calligraphy, typography, autograph, signed, initials, monogram, name, credit,
tail, animal tail, dragon tail, wings on child, animal features on child, furry,
animal ears, extra fingers, missing fingers, fused fingers, too many fingers,
six fingers, malformed hands, bad hands anatomy, deformed hands, extra toes,
missing toes, malformed feet, extra legs, four legs, extra arms, three arms,
four arms, extra limbs, multiple legs, multiple arms, deformed legs, deformed body,
mutated, disfigured, bad anatomy, wrong anatomy, extra body parts, missing limbs,
floating limbs, disconnected limbs, mutation, mutated hands, poorly drawn hands,
poorly drawn feet, poorly drawn face, out of frame, extra bodies, duplicate,
cloned face, gross proportions, malformed limbs, missing arms, missing legs"""
```

---

## 4. Estructura de una Quick Story Kids

### 4.1 Definición en fixed_stories.py
```python
"story_id": {
    "title_es": "{name} y [título]",
    "title_en": "{name} and [title]",
    "age_range": "3-8",
    "text_layout": "split",
    "use_preview_as_cover": True,
    "preview_prompt_override": "[prompt escena 1]",
    "cover_template": "[prompt cover]",
    "pages": [
        {
            "text_above_es": "Texto superior escena 1...",
            "text_below_es": "Texto inferior escena 1...",
            "text_above_en": "Upper text scene 1...",
            "text_below_en": "Lower text scene 1...",
            "scene_template": "[prompt FLUX 2 Dev]"
        },
        # 7 escenas total
    ],
    "closing_template": "[prompt cierre sin companion]",
    "closing_message_es": "{name}, [mensaje motivacional].",
    "closing_message_en": "{name}, [motivational message]."
}
```

### 4.2 Campos obligatorios
| Campo | Descripción |
|-------|-------------|
| title_es / title_en | Título con {name} |
| age_range | "3-5", "3-8" o "6-8" |
| text_layout | "split" (texto arriba y abajo de la imagen) |
| use_preview_as_cover | True (siempre para Quick Stories) |
| preview_prompt_override | Prompt del preview = prompt escena 1 |
| cover_template | Prompt para cover (solo se usa en PDF, no en generación) |
| pages | Array de 7 escenas con text_above/below en ES/EN + scene_template |
| closing_template | Prompt de cierre (niño solo, sin companion) |
| closing_message_es/en | Mensaje motivacional personalizado |

### 4.3 Textos bilingües
Cada escena tiene 4 campos de texto:
- `text_above_es` / `text_above_en` - Texto superior (con drop cap en primera letra)
- `text_below_es` / `text_below_en` - Texto inferior (sin drop cap)

El idioma se detecta automáticamente y se usa el texto correspondiente.
Variable `{o_a}` disponible en textos para género: "divertido/divertida".

---

## 5. Flujo de Usuario

### Flujo actual (Feb 2026 - Generación post-pago)
```
1. Selección     → Elige cuento en catálogo (/stories-3-5 o /stories-6-8)
2. Formulario    → Nombre, edad, género, rasgos (personalize_story.html)
3. Preview       → Genera character preview con FLUX 2 Dev (1 imagen)
4. Generación    → /api/generate-fixed-story genera SOLO cover desde preview (gratis)
                   Escenas NO se generan aún. scenes_pending=True
5. Pre-pago      → story_preview_limited.html (cover + textos del cuento)
6. Checkout      → checkout_quick_story.html ($25 digital / $29-$49 impreso según envío)
7. Paddle        → Pago procesado, redirige a order_complete
8. Post-pago     → order_complete.html detecta scenes_pending=True
                   Genera 7 escenas + 1 cierre con FLUX 2 Dev + referencia
                   Muestra galería completa + opción de regenerar (max 2 por escena)
9. Confirmar     → /api/confirm-and-send envía email + Lulu
```

### Precios
- **$25 USD**: PDF digital + PDF imprimible con instrucciones (email)
- **$29 USD**: Libro impreso + envío Standard Mail + PDF digital (email + Lulu)
- **$35 USD**: Libro impreso + envío Priority Mail + PDF digital (email + Lulu)
- **$42 USD**: Libro impreso + envío Ground + PDF digital (email + Lulu)
- **$46 USD**: Libro impreso + envío Expedited + PDF digital (email + Lulu)
- **$69 USD**: Libro impreso + envío Express + PDF digital (email + Lulu)

### Métodos de Envío (solo libro impreso)
| Método | Precio Paddle | Paddle Price ID Secret | Disponibilidad |
|--------|--------------|----------------------|----------------|
| Standard Mail (MAIL) | $29 | PADDLE_QUICK_STORY_PRINT_PRICE_ID | USA ✅, España ✅ |
| Priority Mail (PRIORITY_MAIL) | $35 | PADDLE_QS_PRIORITY_MAIL_PRICE_ID | USA ✅, España ✅ |
| Ground (GROUND) | $42 | PADDLE_QS_GROUND_PRICE_ID | USA ❌, España ✅ |
| Expedited (EXPEDITED) | $46 | PADDLE_QS_EXPEDITED_PRICE_ID | USA ✅, España ❌ |
| Express (EXPRESS) | $69 | PADDLE_QS_EXPRESS_PRICE_ID | USA ✅, España ✅ |

**IMPORTANTE**: Los precios de Paddle son FIJOS por tier. La API de Lulu solo determina qué métodos están DISPONIBLES por país, NO el precio cobrado al cliente.

### Costos Reales Lulu (referencia interna - NO mostrar al cliente)
| Concepto | Costo Lulu (USA) |
|----------|-----------------|
| Item Subtotal (8.5x8.5, saddle stitch, 10 pgs) | $6.27 |
| Fulfillment Fee | $0.75 |
| Shipping MAIL | ~$3.99 |
| Shipping PRIORITY_MAIL | ~$7.99 |
| Shipping EXPEDITED | ~$20.74 |
| Shipping EXPRESS | ~$39.99 |
| Sales Tax | Variable (~$1.96) |

**Ejemplo margen EXPEDITED a USA**: Cobra $46 - Costo Lulu $29.72 = **Margen $16.28**

### Flujo de Envío Dinámico
1. Usuario selecciona "Libro Impreso" en checkout
2. Aparece formulario de dirección de envío
3. Usuario selecciona país del dropdown
4. Sistema consulta `/api/qs-shipping-costs` → Lulu API determina métodos disponibles
5. Se muestran SOLO los métodos disponibles para ese país con precios Paddle fijos
6. Usuario elige método → se abre checkout Paddle con el Price ID correspondiente
7. El `shipping_method` se guarda en el JSON y se pasa a Lulu al crear la orden

### Advertencia "Revisa tu Cuento" (order_complete.html)
Después del pago, se muestra advertencia amarilla:
```
⚠️ ¡Revisa tu cuento con cuidado!
- Puedes regenerar cada ilustración hasta 2 veces (botón en cada imagen)
- Tienes 1 oportunidad de elegir otro cuento sin costo adicional
- Al hacer clic en "Confirmar", se enviará por email y a imprimir. Sin cambios después.
```

### Flujo de Cambio de Historia (Post-Pago)
Si al usuario no le gusta, puede cambiar UNA VEZ:
```
1. Clic "Quiero otro Cuento Rápido" → POST /api/request-story-change/{preview_id}
2. Redirect → /story-selection?change=1 (banner: "ÚNICA oportunidad de cambio")
3. Elige nuevo cuento → personaliza → genera preview (1 imagen FLUX 2 Dev)
4. generate-fixed-story detecta paid_customer=True → salta checkout
5. order_complete genera escenas del nuevo cuento
6. Botón de cambio ya NO aparece (regeneration_used=True)
```

---

## 6. Estructura PDF

### 6.1 Digital (8.5"×8.5" cuadrado) - 11 páginas
Generado por `create_kids_quick_story_pdf(format_type='digital')`
```
Página 1:    Portada (cover image + título superpuesto)
Página 2:    Portadilla (fondo decorativo + título + subtítulo + autor)
Página 3:    Dedicatoria (marco decorativo dorado)
Páginas 4-10: 7 escenas (ilustración + texto split above/below)
Página 11:   Contraportada
```

### 6.2 Imprimible (8.5"×8.5" cuadrado) - 12 páginas
Generado por `create_kids_quick_story_pdf(format_type='print')`
```
Página 1:    Portada (cover image + título superpuesto)
Página 2:    Portadilla
Página 3:    Dedicatoria
Páginas 4-10: 7 escenas (ilustración + texto split above/below)
Página 11:   Cierre (protagonista solo + mensaje motivacional + firma dinámica)
Página 12:   Contraportada
```

### 6.3 Lulu Saddle Stitch (8.5"×8.5")
Interior PDF: 10 páginas (pág 2-11, portadas son separadas)
```
Página 1 (interior): Blanco
Página 2:            Dedicatoria
Páginas 3-9:         7 escenas con texto split
Página 10:           Blanco
```

Cover Spread separado:
```
Tamaño: 17.25" × 8.75" (438.15mm × 222.25mm)
Layout: [Bleed 0.125"][Back 8.5"][Front 8.5"][Bleed 0.125"]
Bleed solo en bordes exteriores, sin bleed entre portadas
Sin lomo (saddle stitch no necesita lomo)
```

### 6.4 Especificaciones Lulu
```
pod_package_id: 0850X0850FCPRESS080CW444GXX
(FC Premium Saddle Stitch, 80# Coated White, Gloss)

Interior:
- Tamaño: 8.5"×8.5" (21.59cm × 21.59cm)
- 10 páginas (pág 2-11)
- Bleed: 0.125" en todos los bordes
- Safety margin: 0.5" desde el borde de corte
- 12 total divisible por 4 ✓

Cover Spread:
- Tamaño: 17.25"×8.75" (438.15mm × 222.25mm)
- Sin lomo (saddle stitch)
- Resolución: 300 DPI
```

### 6.5 Layout de Escenas (Split Text)
- Ilustración a página completa como fondo
- **Texto superior (text_above)**: Drop cap 35pt púrpura `#6a3d9a` + cuerpo 14pt gris `#4a4a4a`
- **Texto inferior (text_below)**: Cuerpo 14pt gris `#4a4a4a` (sin drop cap)
- Fondo semi-transparente blanco 75% opacidad
- Márgenes laterales: 5% del ancho
- Ancho máximo texto: 85% del ancho

### 6.6 Página de Cierre
- Ilustración de fondo: closing_template (protagonista solo)
- Mensaje motivacional centrado en caja semi-transparente
- Firma dinámica según idioma **del cuento** (`story_data.lang`): ES → "tus amigos de Magic Memories Books" / EN → "your friends at Magic Memories Books"
- Color firma: Morado `#6a3d9a`
- Función: `_draw_kids_closing_page()` en `services/pdf_service.py`

### 6.7 Dedicatoria
- Fondo: Color crema `#FFFBF5`
- Marco exterior: 3cm desde cada borde, redondeado, color `#D4A574`, grosor 2pt
- Marco interior: 3cm + 8pt, color `#E8D5B7`, grosor 0.5pt
- Título: "Dedicatoria"/"Dedication" en `#6a3d9a`, font dropcap 22pt
- Línea ornamental: `#D4A574`, de 30% a 70% del ancho
- Texto dinámico: font body 16pt, color `#5a4a3a`, márgenes 3.5cm

---

## 7. Acciones Post-Pago

### 7.1 Email al Usuario (vía confirm-and-send)
- PDF digital adjunto (siempre)
- Si $25 (want_print=False): También PDF imprimible + instrucciones de impresión casera
- Si $29-$69 (want_print=True): Solo PDF digital (Lulu maneja la impresión)

### 7.2 Lulu API (solo si want_print=True)
- Genera PDFs para impresión (interior + cover spread)
- Sube archivos a almacenamiento Lulu
- Envía orden con shipping level según `shipping_method` guardado: MAIL, PRIORITY_MAIL, GROUND, EXPEDITED o EXPRESS
- Disponibilidad de métodos varía por país (consultada dinámicamente via `/api/qs-shipping-costs`)
- El `shipping_method` se pasa desde el checkout → save-checkout-data → webhook customData → Lulu API
- Ejecutado en thread background (`_process_quick_story_print`)
- pod_package_id: `0850X0850FCPRESS080CW444GXX`

### 7.3 Email Admin (solo si want_print=True)
- Notificación a pay@magicmemoriesbooks.com
- Links a PDFs de Lulu
- Datos de envío del cliente
- Método de envío seleccionado

---

## 8. Cuentos Kids Actuales

### 8.1 Cuentos 3-5 (catálogo /stories-3-5)
| Story ID | Título ES | Age Range | Companion | Escenas |
|----------|-----------|-----------|-----------|---------|
| dragon_friend | {name} y su Amigo el Dragón | 3-8 | Spark (dragón) | 7+1 cierre |
| space_astronaut | {name} el Astronauta | 3-8 | — | 7+1 cierre |
| zebra_stripes | {name} y la Aventura de la Sabana | 3-8 | — | 7+1 cierre |
| superhero_light | {name} Superhéroe de la Luz | 3-5 | — | 7+1 cierre |

### 8.2 Cuentos 6-8 (catálogo /stories-5-7)
| Story ID | Título ES | Age Range | Companion | Escenas |
|----------|-----------|-----------|-----------|---------|
| chronicles_valley | Las Crónicas de {name} | 5-7 | — | 7+1 cierre |
| sunset_map | {name} y el Mapa del Atardecer | 5-7 | — | 7+1 cierre |
| star_guardian | {name} y el Guardián de las Estrellas | 5-7 | — | 7+1 cierre |
| dog_forever | {name} y el Perro que Llegó para Quedarse | 5-7 | Amigo (perro) | 7+1 cierre |

**Nota**: Todos los cuentos permiten seleccionar edad 3-8 en el formulario de personalización, independientemente del age_range recomendado en el catálogo. El age_range solo afecta en qué catálogo aparece el cuento.

---

## 9. Cómo Agregar un Nuevo Quick Story Kids

### Paso 1: Definir companion (si aplica) en `services/fixed_stories.py`
```python
COMPANION_DESC = "COMPANION_NAME: [descripción completa del companion con tamaño relativo al {gender_word}]"
```

### Paso 2: Definir la historia en `services/fixed_stories.py`
```python
STORIES["new_story_id"] = {
    "title_es": "{name} y [título]",
    "title_en": "{name} and [title]",
    "age_range": "3-8",
    "text_layout": "split",
    "use_preview_as_cover": True,
    "preview_prompt_override": "[prompt = escena 1]",
    "cover_template": "[prompt cover con companion]",
    "pages": [
        {
            "text_above_es": "...", "text_below_es": "...",
            "text_above_en": "...", "text_below_en": "...",
            "scene_template": "[prompt FLUX 2 Dev con estructura por secciones]"
        },
        # 7 escenas total
    ],
    "closing_template": "[prompt cierre - niño solo, sin companion]",
    "closing_message_es": "{name}, [mensaje].",
    "closing_message_en": "{name}, [message]."
}
```

### Paso 3: Registrar en `services/quick_stories/stories.py`
```python
QUICK_STORIES["new_story_id"] = {
    "title_es": "{name} y [título]",
    "title_en": "{name} and [title]",
    "age_range": "3-8",
    "category": "magical_adventures",  # o "great_adventures"
    "price": 25,
    "includes_print": False
}
```

### Paso 4: Agregar a `services/quick_stories/checkout.py`
```python
QUICK_STORY_IDS = [
    # ... existentes ...
    'new_story_id',
]
```

### Paso 5: Agregar imagen de catálogo
- Guardar en `static/images/cover_new_story_id.png`
- Tamaño recomendado: 800×800px cuadrado

### Paso 6: Agregar al catálogo en templates
- Buscar la sección correspondiente (stories-3-5 o stories-6-8)
- Agregar card con imagen, título, edad, precio

### Paso 7: Pasar companion_desc en app.py (si aplica)
En la ruta `/api/generate-baby-preview` (genérica para todos), agregar el formateo:
```python
companion_desc=COMPANION_DESC.format(gender_word=gender_word)
```

### Paso 8: Verificar
- [ ] Historia aparece en catálogo
- [ ] Formulario carga correctamente
- [ ] Preview genera con FLUX 2 Dev (sin referencia)
- [ ] Cover se copia del preview (gratis)
- [ ] Preview y escenas usan el mismo modelo (FLUX 2 Dev)
- [ ] Escenas generan correctamente con referencia del cover
- [ ] Textos bilingües (ES/EN) correctos
- [ ] Preview pre-pago muestra cover + texto
- [ ] Checkout funciona con todos los precios ($25/$29/$39/$49)
- [ ] Selector de método de envío aparece al elegir "Libro Impreso"
- [ ] Post-pago muestra galería completa sin duplicados
- [ ] Regeneración funciona (max 2 por escena)
- [ ] Botón "Quiero otro Cuento Rápido" visible
- [ ] Botón desaparece si regeneration_used=True o email_sent=True
- [ ] Flujo de cambio: pago se mantiene, salta checkout
- [ ] Firma dinámica en closing (ES/EN)
- [ ] Email se envía con PDFs correctos
- [ ] PDF digital tiene 11 páginas
- [ ] PDF imprimible tiene 12 páginas (con cierre)
- [ ] PDF Lulu interior tiene 10 páginas
- [ ] Cover spread Lulu tiene dimensiones correctas (sin lomo)
- [ ] Lulu submission funciona con método de envío correcto (MAIL/PRIORITY_MAIL/EXPEDITED)

---

## 10. Variables de Entorno Requeridas

```
REPLICATE_API_TOKEN=r8_...              # Para FLUX 2 Dev
PADDLE_CLIENT_TOKEN=...                 # Frontend Paddle.js
PADDLE_QUICK_STORY_PRICE_ID=...         # $25 digital
PADDLE_QUICK_STORY_PRINT_PRICE_ID=...   # $29 impreso (Standard Mail)
PADDLE_QS_PRIORITY_MAIL_PRICE_ID=...    # $39 impreso (Priority Mail)
PADDLE_QS_EXPEDITED_PRICE_ID=...        # $49 impreso (Expedited)
PADDLE_WEBHOOK_SECRET=...               # Verificación webhook
LULU_CLIENT_KEY=...                     # API Lulu (producción)
LULU_CLIENT_SECRET=...                  # API Lulu (producción)
SMTP_EMAIL=...                          # Email sender
SMTP_PASSWORD=...                       # Email auth
```

---

## 11. Reglas de Consistencia de Personaje

### Anti-hibridación
- SIEMPRE incluir "100% human child" en prompts con animales/companions
- "NO animal features, NO tail, NO wings on child"
- Companion como personaje SEPARADO, no fusionado con el niño

### Outfit consistente
- Definir UN outfit por cuento y repetirlo en TODAS las escenas
- Ejemplo dragon_friend: "Soft blue tunic with gold leaf embroidery, brown pants, small boots"

### Tamaño relativo
- Si el companion es grande (dragón): "MUST BE TWICE AS TALL as {gender_word}"
- Si el companion es pequeño (mascota): especificar tamaño relativo
- SIEMPRE incluir la relación de tamaño en STRICT

---

## 12. Diferencias con Otros Productos

| Aspecto | Quick Stories Kids | Cuentos Bebés (0-2) | Libros Personalizados |
|---------|-------------------|---------------------|----------------------|
| Escenas | 7 + 1 cierre | 6-7 + 1 cierre | 19 |
| Formato | 8.5"×8.5" cuadrado | 8.5"×8.5" cuadrado | A4 (210×297mm) |
| Encuadernación | Saddle stitch | Saddle stitch | Casewrap hardcover |
| Precio | $25/$29 | $25/$29 | $55 |
| Modelo IA | FLUX 2 Dev | FLUX 2 Pro + Ideogram | FLUX Dev |
| Cover | Desde preview (gratis) | Desde preview (gratis) | FLUX generada |
| Referencia | cover_clean.png | preview como referencia | character preview |
| Text layout | Split (above/below) | Overlay (sobre imagen) | Split (above/below) |
| Closing | Niño solo + mensaje | Mandala top-down + "Fin" | Ilustración final |
| Lomo | No (saddle stitch) | No (saddle stitch) | Sí (hardcover) |
