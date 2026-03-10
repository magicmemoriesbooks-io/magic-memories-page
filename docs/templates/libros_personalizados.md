# Plantilla: Libros Personalizados

## Sección
**Libros Personalizados** (Personalized Books) - Dragon Garden, Magic Chef, Magic Inventor Workshop.
**NO aplica para:** Quick Stories, Haz tu Historia, ni otras secciones.

## Resumen
Esta plantilla documenta todo el proceso para crear nuevos cuentos personalizados como Dragon Garden, Magic Chef y Magic Inventor Workshop.

---

## 1. Arquitectura de Archivos

```
services/personalized_books/
├── __init__.py                    # Registro de historias disponibles
├── generation.py                  # Lógica de generación
├── stories/
│   ├── dragon_garden.py           # Configuración Dragon Garden
│   ├── magic_chef.py              # Configuración Magic Chef
│   └── [nuevo_cuento].py          # Nuevo cuento aquí

services/illustrated_book_service.py   # Generación de imágenes FLUX
services/pdf_service.py                # Generación de PDFs
templates/personalize_story.html       # Formulario + modal advertencia
templates/order_complete.html          # Vista previa + regeneración
static/images/cover_[story_id].png     # Portadas de catálogo
```

---

## 2. Prompts de Estilo (CRÍTICO para consistencia)

### 2.1 Estilo Base (STYLE_BASE)
```python
STYLE_BASE = "children's storybook watercolor illustration, soft luminous pastel colors, gentle warm lighting, dreamy magical atmosphere, full body characters shown completely from head to feet, clean illustration only"
```

### 2.2 Descripción de Personaje Consistente
```python
# CRÍTICO: Incluir SIEMPRE estas restricciones para evitar colas/alas en el niño
CHARACTER_TEMPLATE = """
A {child_age} year old {gender_child} child with:
- EXACT {hair_color} {hair_length} {hair_type} hair
- EXACT {skin_tone} skin
- EXACT {eye_color} eyes
- EXACT Face: same facial features, proportions
- HUMAN ONLY: normal human child with two arms, two legs, five fingers per hand

This SAME child with IDENTICAL features must appear consistently in ALL illustrations.
"""
```

### 2.3 Prompt de Portada (Evitar Hibridación)
```python
# IMPORTANTE: Incluir estas frases para evitar que el niño parezca dragón
COVER_PROMPT = """
Magical storybook cover illustration: a brave {gender_child} 
(FULLY HUMAN child, NOT a dragon hybrid, regular human body with regular human legs, 
NO reptile features, NO tail whatsoever) with {hair_desc} and {skin_tone}, 
{outfit_desc}, standing in an enchanted garden, next to {companion_desc}. 
WIDE VIEW showing magical garden environment with glowing flowers, ancient oak tree, 
stone path. Soft morning light, sparkles in the air. The child has a warm smile, 
hand gently touching the dragon. Fantasy fairy tale atmosphere, centered composition 
perfect for book cover. {style}
"""
```

### 2.4 Negative Prompt (OBLIGATORIO en cada llamada a FLUX)
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
cloned face, gross proportions, malformed limbs, missing arms, missing legs, 
extra leg, extra arm"""
```

---

## 3. Descripción de Compañero (Personaje Secundario)

### Dragon Garden - Spark
```python
SPARK_DESC = "Spark the small cute baby dragon with shimmering emerald green scales, big round golden eyes, tiny translucent wings, chubby round body, and a friendly smile"
```

### Magic Chef - Whiskers
```python
WHISKERS_DESC = "Whiskers the fluffy orange tabby cat with bright green eyes, wearing a tiny chef's hat, playful expression"
```

---

## 4. Estructura de Escena

```python
SCENE_TEMPLATE = {
    'id': 1,
    'text': {
        'es': "Texto en español con {child_name}...",
        'en': "English text with {child_name}..."
    },
    'outfit': "adventure",  # Clave para cambiar ropa
    'image_prompt': """
        {char_base} (child only, FULLY HUMAN, NO animal features, NO tail) 
        wearing {outfit_desc}, in the magical garden with {companion_desc}. 
        [Descripción de la acción específica de la escena].
        WIDE VIEW, full body visible, {style}
    """
}
```

---

## 5. Estructura del PDF (26 páginas)

| Página | Contenido | Archivo |
|--------|-----------|---------|
| 1 | Portada | cover.png |
| 2 | Portadilla (título + autor) | page_01.png |
| 3 | Dedicatoria | page_02.png |
| 4-22 | 19 Escenas | page_03.png - page_21.png |
| 23 | Ilustración de cierre | page_22.png |
| 24 | Créditos | page_23.png |
| 25 | Página blanca | page_24.png |
| 26 | Contraportada | back_cover.png (fija) |

### Nomenclatura de Archivos
- **Original (sin watermark)**: `page_01.png`, `cover.png`
- **Preview (con watermark)**: `page_01_preview.png`, `cover_preview.png`

---

## 6. Flujo de Usuario

```
1. Modal informativo obligatorio (checkbox requerido)
2. /personalized-book/[story_id]     → Formulario de personalización
3. POST /personalized-book/generate  → Genera 24 imágenes + portada
4. /personalized-book/checkout       → Selección envío + Paddle
5. /order-complete/[preview_id]      → Vista previa + regeneración
6. Confirmar y Enviar               → PDF email + Lulu submission
```

---

## 7. Modal de Advertencia (OBLIGATORIO)

### Ubicación: templates/personalize_story.html (inicio)

### Contenido:
1. 🎨 **Ilustraciones con IA** - Son generadas por IA, pueden tener errores
2. 📖 **Revisa el Texto** - Leer bien antes de confirmar
3. 🔄 **Regenerar Ilustraciones** - Hasta 2 veces por página
4. 📦 **Opciones de Envío** - Estándar incluido (10-20 días)
5. 📧 **PDF Digital** - Se envía por email, convertible a EPUB

### Checkbox obligatorio:
```html
<input type="checkbox" id="acceptTerms" required>
<span>He leído y entendido esta información</span>
```

---

## 8. Sistema de Regeneración (CRÍTICO)

### Límite: 2 regeneraciones por página
### Páginas regenerables: 3-21 (escenas del cuento)

### Endpoint:
```python
@app.route('/api/regenerate-page/<preview_id>/<int:page_num>', methods=['POST'])
```

### CRÍTICO: Actualizar TODAS las listas de imágenes
Cuando se regenera una imagen, DEBEN actualizarse TODAS estas listas en story_data:

```python
# Update regeneration count
regen_counts[page_key] = current_count + 1
story_data['page_regenerations'] = regen_counts

# Update ALL image path arrays to ensure PDF generation uses new images
page_index = page_num - 1  # Array index (0-based)

# Update original_images
original_images = story_data.get('original_images', [])
if page_index < len(original_images):
    original_images[page_index] = f'/{original_path}'
    story_data['original_images'] = original_images

# Update all_pages_original (used by email PDF)
all_pages_original = story_data.get('all_pages_original', [])
if page_index < len(all_pages_original):
    all_pages_original[page_index] = f'/{original_path}'
    story_data['all_pages_original'] = all_pages_original

# Update original_scene_paths (fallback)
original_scene_paths = story_data.get('original_scene_paths', [])
if page_index < len(original_scene_paths):
    original_scene_paths[page_index] = f'/{original_path}'
    story_data['original_scene_paths'] = original_scene_paths

# Update preview/watermarked images
preview_images = story_data.get('images', [])
if page_index < len(preview_images):
    preview_images[page_index] = f'/{preview_path}'
    story_data['images'] = preview_images

# Update all_pages_preview
all_pages_preview = story_data.get('all_pages_preview', [])
if page_index < len(all_pages_preview):
    all_pages_preview[page_index] = f'/{preview_path}'
    story_data['all_pages_preview'] = all_pages_preview

# Save updated story data
with open(preview_file, 'w', encoding='utf-8') as f:
    json.dump(story_data, f, ensure_ascii=False, indent=2)
```

### Estructura de Arrays en story_data JSON:
```python
{
    # Imágenes originales (sin watermark) - para PDF final
    "original_images": ["/path/page_01.png", ...],
    "all_pages_original": ["/path/page_01.png", ...],
    "original_scene_paths": ["/path/page_01.png", ...],
    
    # Imágenes preview (con watermark) - para vista previa
    "images": ["/path/page_01_preview.png", ...],
    "all_pages_preview": ["/path/page_01_preview.png", ...],
    
    # Portadas
    "original_cover": "/path/cover.png",
    "cover_preview": "/path/cover_preview.png",
    "front_cover_path": "/path/cover.png",
    "back_cover_path": "/path/back_cover.png",
    
    # Contadores de regeneración
    "page_regenerations": {"3": 1, "5": 2, ...}
}
```

---

## 9. Posición del Autor en Portada

### Ubicación: 3cm del borde inferior

```python
# En generate_cover_spread() - illustrated_book_service.py
# Add author name to front cover - centered at bottom, 3cm from edge
if author_name and author_name.strip():
    from PIL import ImageDraw, ImageFont
    draw = ImageDraw.Draw(front_cover)
    
    # 3cm from bottom for better visibility and safe print margins
    # Using 3% of height as margin (~3cm on A4)
    margin_bottom = int(cover_height_px * 0.03)  # ~3cm from bottom
    author_y = cover_height_px - margin_bottom - 60  # 60px for text height
    
    try:
        author_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(cover_width_px * 0.025))
    except:
        author_font = ImageFont.load_default()
    
    author_text = author_name
    bbox = draw.textbbox((0, 0), author_text, font=author_font)
    text_width = bbox[2] - bbox[0]
    x = (cover_width_px - text_width) // 2
    
    # Draw with shadow for visibility on any background
    for dx, dy in [(-2, -2), (-2, 2), (2, -2), (2, 2), (-2, 0), (2, 0), (0, -2), (0, 2)]:
        draw.text((x + dx, author_y + dy), author_text, font=author_font, fill="#000000")
    draw.text((x, author_y), author_text, font=author_font, fill="#FFFFFF")
```

---

## 10. Integración de Pagos (Paddle)

### Price IDs por Envío (Sandbox)
| Método | Price ID | Precio |
|--------|----------|--------|
| MAIL | pri_01kgppgtvcch7vr9yanhdavebs | $55 |
| PRIORITY_MAIL | pri_01kgpvhztk4m4jzyrxbzxfpqvh | $65 |
| GROUND | pri_01kgpvq67hzjcymjy0z8k31z3v | $70 |
| EXPEDITED | pri_01kgpvsdqbanx08aac1pb5w70w | $75 |
| EXPRESS | pri_01kgpvvhjvgv8d659hba6c83sw | $80 |

### Código de Checkout
```javascript
Paddle.Checkout.open({
    items: [{ priceId: selectedPriceId, quantity: 1 }],
    customer: { email: customerEmail },
    customData: { preview_id: previewId },
    successCallback: function(data) {
        // Redirigir a /order-complete/{preview_id}
    }
});
```

---

## 11. FLUJO UNIFICADO DE PAGO + LULU (TODOS LOS LIBROS)

**REGLA FUNDAMENTAL**: El proceso de pago y la generación de PDFs para Lulu es **IDÉNTICO** para Dragon Garden, Magic Chef, Magic Inventor y cualquier libro futuro. La **ÚNICA** diferencia es la contraportada.

### 11.1 Flujo Completo Post-Pago (Automático)

```
Usuario completa pago en Paddle
        ↓
┌─────────────────────────────────────────────┐
│  SE DISPARA DESDE 2 FUENTES (con dedup):    │
│  1. process_payment() - callback del cliente │
│  2. paddle_webhook()  - webhook de Paddle    │
│  (Deduplicación via flag admin_notified)     │
└─────────────────────────────────────────────┘
        ↓
_process_personalized_book_post_payment(preview_id, email)
        ↓
┌─────────────────────────────────────────────┐
│  PASO 1: PDF Digital (para email al cliente) │
│  - Portada + 24 páginas interior + contra   │
│  - create_pdf_from_images()                 │
│  - Sin sanitización (skip_sanitize=True)    │
└─────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────┐
│  PASO 2: PDF Interior Lulu (300 DPI)        │
│  - 24 páginas interiores solamente          │
│  - generate_illustrated_book_pdf(for_print) │
│  - Resolución: 2551 x 3579 px por página   │
│  - Se guarda en lulu_orders/{id}/interior   │
└─────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────┐
│  PASO 3: PDF Cover Spread Lulu              │
│  - Cover spread ya generado durante libro   │
│  - save_cover_as_pdf()                      │
│  - Se guarda en lulu_orders/{id}/cover.pdf  │
└─────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────┐
│  PASO 4: Email al cliente                   │
│  - PDF digital adjunto                      │
│  - send_story_email_with_attachments()      │
└─────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────┐
│  PASO 5: Email al admin (Lulu)              │
│  - Links para descargar interior + cover    │
│  - Dirección de envío del cliente           │
│  - send_lulu_order_notification()           │
│  - Se marca admin_notified = True           │
└─────────────────────────────────────────────┘
```

### 11.2 Lo que es IGUAL para todos los libros

| Paso | Función | Archivo |
|------|---------|---------|
| Detección de libro personalizado | `is_personalized_book(story_id)` | `generation.py` |
| Conversión story_id → book_id | `get_personalized_book_id(story_id)` | `generation.py` |
| Título para Lulu | `get_lulu_title(book_id, name, lang)` | `generation.py` |
| PDF digital (email) | `create_pdf_from_images()` | `pdf_service.py` |
| PDF interior Lulu (300 DPI) | `generate_illustrated_book_pdf()` | `illustrated_book_service.py` |
| Cover spread casewrap | `generate_cover_spread()` | `illustrated_book_service.py` |
| Cover spread → PDF | `save_cover_as_pdf()` | `illustrated_book_service.py` |
| Deduplicación post-pago | Flag `admin_notified` en story_data | `app.py` |
| Carpeta Lulu | `create_order_folder()` | `lulu_storage.py` |
| Email al cliente | `send_story_email_with_attachments()` | `email_service.py` |
| Email al admin | `send_lulu_order_notification()` | `email_service.py` |

### 11.3 Lo ÚNICO que cambia: Contraportada

| Libro | Tipo de contraportada | Archivo |
|-------|----------------------|---------|
| Dragon Garden | **Dinámica** - generada con FLUX Dev | Prompt en `BACK_COVER_TEMPLATE` |
| Magic Chef | **Fija** - imagen estática | `static/images/fixed_pages/magic_chef_back_cover.png` |
| Magic Inventor | **Fija** - imagen estática | `static/images/fixed_pages/magic_inventor_back_cover.png` |

La lógica está en 2 lugares (y SOLO en estos 2):
1. **`generate_cover_spread()`** en `illustrated_book_service.py` → línea ~1350
2. **`_process_personalized_book_post_payment()`** en `app.py` → línea ~3963

```python
# En ambos lugares, la lógica es:
fixed_back_covers = {
    "magic_chef": "static/images/fixed_pages/magic_chef_back_cover.png",
    "magic_inventor": "static/images/fixed_pages/magic_inventor_back_cover.png"
}
if book_id in fixed_back_covers:
    # Usar imagen fija
else:
    # Generar con FLUX Dev (como Dragon Garden)
```

**Para un libro nuevo**: Solo agregar a este diccionario si la contraportada es fija.

### 11.4 Deduplicación del Procesamiento Post-Pago

El procesamiento puede dispararse desde 2 fuentes:
- **`process_payment()`**: Se llama cuando el cliente confirma el pago (callback de Paddle.js)
- **`paddle_webhook()`**: Se llama cuando Paddle envía el webhook `transaction.completed`

Para evitar doble procesamiento:
```python
already_processed = story_data.get('admin_notified', False)
if not already_processed:
    # Lanzar hilo background para PDFs + emails
```

En sandbox, el webhook a veces no llega, por eso `process_payment` también lanza el procesamiento.

---

## 12. Especificaciones Lulu Casewrap (BLINDADO - NO MODIFICAR)

### Formato: A4 Casewrap Hardcover (210mm x 297mm)
### Interior: 300 DPI (2551 x 3579 pixels por página)

### Dimensiones Cover Spread Casewrap
```
Interior trim: 210mm × 297mm (A4)
Board overhang: 3.175mm (1/8") en top, bottom, fore-edge (NO spine side)
Board size: 213.175mm × 303.35mm
Wrap area: 19.05mm (3/4") en TODOS los bordes del spread
Spine width: 6.35mm (1/4") para 24-84 páginas casewrap (tabla oficial Lulu)
Total spread: 470.80mm × 341.45mm = 5560 × 4032 px a 300 DPI
Rango aceptado Lulu: 469.33-472.50mm × 339.79-342.96mm

Layout del spread:
[Wrap 19mm] [Back Board 213.175mm] [Spine 6.35mm] [Front Board 213.175mm] [Wrap 19mm]
                                     ↕ altura total: 341.45mm ↕

Wrap area se llena extendiendo/espejando pixels del borde de las imágenes de portada.
Spine se renderiza a altura completa con título + autor rotado 90°.
```

**ESTAS DIMENSIONES ESTÁN VERIFICADAS Y APROBADAS POR LULU. NO CAMBIAR.**

### Upscale Interior
```python
def prepare_for_lulu(story_data, for_print=True):
    dpi = 300
    page_width = 2551  # A4 + 3mm bleed
    page_height = 3579
    
    for page in pages:
        upscaled = page.resize((page_width, page_height), Image.Resampling.LANCZOS)
        upscaled.save(img_buffer, format='JPEG', quality=85, dpi=(dpi, dpi))
```

---

## 13. Llamada a FLUX Dev (Replicate)

**IMPORTANTE**: Todos los libros personalizados usan **FLUX Dev** para todo el proceso:
- Preview de personaje
- 19 escenas
- Portada y contraportada
- Ilustración de cierre

```python
import replicate

# Para preview, escenas y portada (proporción libro)
output = replicate.run(
    "black-forest-labs/flux-dev",
    input={
        "prompt": full_prompt,
        "aspect_ratio": "3:4",  # Portrait para páginas interiores
        "output_format": "png",
        "num_inference_steps": 28,
        "guidance": 3.5
    }
)

# Para contraportada (proporción A4 vertical)
output = replicate.run(
    "black-forest-labs/flux-dev",
    input={
        "prompt": back_prompt,
        "aspect_ratio": "9:16",  # Más alto para A4
        "output_format": "png",
        "num_inference_steps": 28,
        "guidance": 3.5
    }
)
```

---

## 14. Checklist para Nuevo Cuento

### FASE 1: Contenido (Prompts y Escenas)
- [ ] Crear archivo de prompts: `services/personalized_books/[nuevo_id]_prompts.py`
- [ ] Definir `STYLE_BASE` específico del cuento
- [ ] Definir `build_char_base()` con restricciones de humanidad (FULLY HUMAN, NO tail, etc.)
- [ ] Definir `COMPANION_DESC` / companion inline (mascota/personaje secundario)
- [ ] Si el compañero NO es humano: especificar "SIN cola" si aplica (ej: BOLT el robot)
- [ ] Definir `get_outfit_desc(gender)` para ropa del personaje
- [ ] Escribir 19 escenas con prompts + textos bilingües (ES/EN)
- [ ] Escribir escena de cierre (closing)
- [ ] Incluir `NEGATIVE_PROMPT` en cada prompt de imagen
- [ ] Crear prompts de portada (cover) y contraportada (back cover)
- [ ] Definir si contraportada es dinámica (como Dragon Garden) o fija (como Magic Chef/Inventor)

### FASE 2: Registro en el Sistema
- [ ] Registrar en `services/personalized_books/__init__.py`
- [ ] Registrar en `services/personalized_books/stories.py` (config del libro)
- [ ] Registrar story_id en `services/personalized_books/checkout.py` → `PERSONALIZED_BOOK_IDS`
- [ ] Agregar imagen de catálogo: `static/images/cover_[id].png`
- [ ] Si contraportada fija: agregar `static/images/fixed_pages/[id]_back_cover.png`

### FASE 3: Integración en app.py (CRÍTICO - Verificar TODOS estos puntos)
- [ ] **Preview**: Agregar condición en `/api/generate-baby-preview` para el nuevo story_id
- [ ] **Preview module**: Agregar condición en `services/personalized_books/preview.py`
- [ ] **book_id**: Agregar en `get_personalized_book_id()` en `generation.py` para reconocer el nuevo story_id
- [ ] **Título Lulu (CENTRALIZADO)**: Agregar título bilingüe en `get_lulu_title()` en `generation.py` (una sola función, se usa en 3 lugares de app.py automáticamente)
- [ ] **is_personalized_book (CENTRALIZADO)**: Agregar story_id a la lista en `is_personalized_book()` en `generation.py` (se usa en 3 lugares de app.py automáticamente)
- [ ] **Contraportada post-pago**: Agregar en `_process_personalized_book_post_payment` (buscar "back_cover" fija)
- [ ] **Título cover spread**: Verificar que `generate_cover_spread()` en `illustrated_book_service.py` tiene título para el nuevo book_id
- [ ] **Closing page**: Verificar que `generate_closing_page()` tiene prompt para el nuevo book_id
- [ ] **FIXED_STORIES (template JS)**: Agregar story_id en la lista `FIXED_STORIES` en `templates/personalize_story.html` (HAY 2 COPIAS de esta lista en el archivo)

### FASE 4: Verificación Visual
- [ ] Probar flujo completo: form → character preview → generate → preview → checkout → payment → download
- [ ] Verificar que el preview de personaje muestra el compañero correcto
- [ ] Verificar que las 19 escenas usan el compañero correcto (no Spark, no Whiskers, no BOLT de otro libro)
- [ ] Verificar que la portada tiene el título y autor correctos
- [ ] Verificar que la contraportada es la correcta (dinámica o fija según diseño)
- [ ] Verificar que el cover spread tiene las dimensiones Lulu casewrap (470.80mm × 341.45mm)
- [ ] Verificar regeneración funciona y se guarda en PDF final
- [ ] Verificar PDF tiene 26 páginas sin watermarks (portada + 24 interior + contraportada)
- [ ] Verificar personaje consistente (sin cola, sin alas, sin features de animal)
- [ ] Verificar autor a 3cm del borde inferior en portada
- [ ] Verificar modal de advertencia aparece con checkbox obligatorio

### FASE 5: Integración Paddle + Lulu (AUTOMÁTICA - ver sección 11)
**El flujo de pago y Lulu es UNIFICADO para todos los libros. NO hay que tocar app.py para esto.**
**Lo ÚNICO que puede cambiar es la contraportada (ver sección 11.3).**

- [ ] Verificar que el checkout muestra el precio correcto con opciones de envío
- [ ] Verificar que `process_payment()` y `paddle_webhook()` procesan el pago (ya unificado)
- [ ] Verificar que el título en Lulu es el del nuevo libro → agregar en `get_lulu_title()` de `generation.py`
- [ ] Si contraportada fija: agregar en `fixed_back_covers` de `_process_personalized_book_post_payment` y `generate_cover_spread()`
- [ ] Verificar que el email al cliente incluye el PDF digital correcto
- [ ] Verificar que el email al admin incluye los links de Lulu correctos
- [ ] Verificar deduplicación: el procesamiento NO debe ejecutarse 2 veces

### ERRORES PASADOS (para NO repetir)
| Error | Qué pasó | Cómo evitarlo |
|-------|----------|---------------|
| book_id defaulteaba a dragon_garden | Solo se chequeaba magic_chef, todo lo demás caía a dragon_garden | SIEMPRE usar `get_personalized_book_id()` en vez de if/else manual |
| Título de Lulu incorrecto | El else del título ponía "Jardín del Dragón" para todos | Agregar elif para cada libro nuevo en los 2 lugares de app.py |
| Dimensiones cover incorrectas | Se cambiaron specs de casewrap a softcover por error | Las specs de Lulu casewrap están BLINDADAS en la skill, NO modificar |
| Compañero mezclado | Falta condición en preview.py | Agregar elif en preview.py para cada libro nuevo |

---

## 15. Problemas Comunes y Soluciones

| Problema | Causa | Solución |
|----------|-------|----------|
| Niño con cola/alas | Falta restricción en prompt | Agregar "FULLY HUMAN, NO tail, NO animal features" |
| Watermarks en PDF final | Usando scene_paths | Usar original_images |
| Regeneración no se guarda | Solo actualiza un array | Actualizar TODAS las listas (ver sección 8) |
| Personaje inconsistente | Descripción vaga | Usar CHARACTER_TEMPLATE exacto |
| Autor no aparece | Falta author_name | Pasar author_name a generate_full_book() |
| Autor cortado en portada | Posición muy baja | Usar 3cm (0.03) del borde inferior |
| Error Paddle | Pasando address | No pasar address a Paddle.Checkout.open() |
| Usuario no lee advertencias | Modal falta | Añadir modal con checkbox obligatorio |
| Libro nuevo usa prompts de Dragon Garden | book_id no reconoce nuevo story_id | Agregar en `get_personalized_book_id()` + `get_lulu_title()` + `is_personalized_book()` en `generation.py` |
| Cover spread con dimensiones incorrectas | Alguien cambió las specs de Lulu | Specs casewrap están BLINDADAS: 470.80mm × 341.45mm. NO cambiar |
| 404 Not Found después de generar libro | story_id falta en FIXED_STORIES del template JS | Agregar en `FIXED_STORIES` de `personalize_story.html` (2 copias) |
| Preview usa modelo incorrecto (no FLUX Dev) | Fallback usaba otro modelo | SIEMPRE usar `generate_with_flux_dev()`. NUNCA FLUX 2 Pro, DALL-E ni otro modelo para Personalized Books |
| Título portadilla se sale de la página | Texto en una sola línea sin wrapping | Portadilla usa text wrapping automático (max 85% del ancho). Título se centra y divide en múltiples líneas |
| Texto de escena todo abajo | Falta `text_position` en scenes | SIEMPRE agregar `"text_position": "split"` a cada escena. Sin este campo, el default es "split" pero es mejor ser explícito |
| Lulu no recibe el libro / admin no recibe email | Solo el webhook procesaba post-pago | `process_payment` ahora también lanza `_process_personalized_book_post_payment` en hilo background |

---

## 16. Reglas de la Portadilla (Title Page)

La portadilla se genera en `generate_full_book()` dentro de `illustrated_book_service.py`:

- **Título**: Centrado, con text wrapping automático (max 85% del ancho de página)
- **Subtítulo**: "Una aventura de {name}" / "An adventure of {name}" centrado debajo del título
- **Autor**: "Escrito con amor por {author}" / "Written with love by {author}" centrado debajo del subtítulo
- **Posición dinámica**: El subtítulo y autor se posicionan automáticamente según la altura del título (multi-línea)
- **REGLA**: Nunca dibujar texto en una sola línea sin verificar que cabe en el ancho de la página

## 17. Campo `text_position` en Escenas

**OBLIGATORIO**: Cada escena en `[book]_prompts.py` DEBE tener `"text_position"`:

```python
{
    "id": 1,
    "text_es": "...",
    "text_en": "...",
    "prompt": "...",
    "text_position": "split"  # OBLIGATORIO
}
```

| Valor | Efecto | Uso |
|-------|--------|-----|
| `"split"` | Mitad del texto arriba, mitad abajo de la imagen | Escenas 1-18 (todas las escenas de historia) |
| `"bottom"` | Todo el texto al fondo de la imagen | Escena 19 (última escena, cierre narrativo) |
| `"none"` | Sin texto sobre la imagen | CLOSING_SCENE (ilustración de cierre sin texto) |

**Si falta este campo**, el default es `"split"`, pero es mejor ser explícito para evitar confusiones.

---

## 18. Archivos que DEBEN Modificarse al Crear un Libro Nuevo

| # | Archivo | Qué agregar | Centralizado? |
|---|---------|-------------|---------------|
| 1 | `services/personalized_books/[id]_prompts.py` | **CREAR**: Prompts, STYLE_BASE, build_char_base(), companion, scenes. **INCLUIR `text_position` en cada escena** | - |
| 2 | `services/personalized_books/__init__.py` | Registrar nuevo libro (import) | - |
| 3 | `services/personalized_books/stories.py` | Config del libro (title, scenes, age_range) | - |
| 4 | `services/personalized_books/checkout.py` | Agregar story_id a `PERSONALIZED_BOOK_IDS` | - |
| 5 | `services/personalized_books/preview.py` | Agregar elif para preview del personaje | - |
| 6 | `services/personalized_books/generation.py` | **3 funciones**: `get_personalized_book_id()`, `is_personalized_book()`, `get_lulu_title()` | **SÍ - app.py las usa automáticamente** |
| 7 | `services/illustrated_book_service.py` | Agregar en `load_book_config()`, `generate_cover_spread()`, `generate_closing_page()` | - |
| 8 | `templates/personalize_story.html` | Agregar story_id en `FIXED_STORIES` (2 copias en el archivo) | - |
| 9 | `app.py` (post-payment back cover) | Agregar elif para contraportada fija si aplica | - |
| 9 | `static/images/cover_[id].png` | Imagen de catálogo | - |
| 10 | `static/images/fixed_pages/[id]_back_cover.png` | Solo si contraportada es fija | - |

**NOTA**: Ya NO es necesario modificar app.py para títulos Lulu ni listas is_personalized_book.
Esas lógicas están centralizadas en `generation.py` y app.py las importa automáticamente.

---

## 19. Archivos de Referencia

- **Prompts Dragon Garden**: `services/illustrated_book_service.py` líneas 77-230
- **Prompts Magic Chef**: `services/illustrated_book_service.py` líneas 228-500
- **Prompts Magic Inventor**: `services/personalized_books/magic_inventor_prompts.py`
- **Fixed pages**: `docs/fixed_pages/` (créditos, dedicatoria, contraportadas)
- **Skill template**: `~/.agents/skills/libros-personalizados/SKILL.md`
- **Función clave**: `get_personalized_book_id()` en `services/personalized_books/generation.py`
- **Endpoint regeneración**: `app.py` → `/api/regenerate-page`
