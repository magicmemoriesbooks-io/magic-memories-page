# Skill: Plantilla para Libros Personalizados

## Descripción
Plantilla completa para crear nuevos cuentos personalizados ilustrados con IA (FLUX), integración Paddle/Lulu, y sistema de regeneración.

---

## Arquitectura de Archivos

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
templates/personalize_story.html       # Formulario de personalización
templates/order_complete.html          # Vista previa + regeneración
static/images/cover_[story_id].png     # Portadas de catálogo
```

---

## Flujo Completo de Usuario

```
1. Modal informativo obligatorio (checkbox requerido)
2. /personalized-book/[story_id]     → Formulario de personalización
3. POST /personalized-book/generate  → Genera 24 imágenes + portada
4. /personalized-book/checkout       → Selección de envío + Paddle
5. /order-complete/[preview_id]      → Vista previa con regeneración
6. Confirmar y Enviar                → PDF email + Lulu submission
```

---

## Sistema de Regeneración (CRÍTICO)

### Límite: 2 regeneraciones por página

### Endpoint
```python
@app.route('/api/regenerate-page/<preview_id>/<int:page_num>', methods=['POST'])
```

### Páginas regenerables: 3-21 (escenas del cuento)
- Página 1: Portadilla (NO regenerable)
- Página 2: Dedicatoria (NO regenerable)
- Páginas 3-21: Escenas (regenerables, 2 veces cada una)
- Páginas 22-24: Cierre/Fin/Créditos (NO regenerables)

### CRÍTICO: Actualizar TODAS las listas de imágenes
Cuando se regenera una imagen, DEBEN actualizarse TODAS estas listas:
```python
# Actualizar original_images
original_images = story_data.get('original_images', [])
if page_index < len(original_images):
    original_images[page_index] = f'/{original_path}'
    story_data['original_images'] = original_images

# Actualizar all_pages_original (usado por email PDF)
all_pages_original = story_data.get('all_pages_original', [])
if page_index < len(all_pages_original):
    all_pages_original[page_index] = f'/{original_path}'
    story_data['all_pages_original'] = all_pages_original

# Actualizar original_scene_paths (fallback)
original_scene_paths = story_data.get('original_scene_paths', [])
if page_index < len(original_scene_paths):
    original_scene_paths[page_index] = f'/{original_path}'
    story_data['original_scene_paths'] = original_scene_paths

# Actualizar preview/watermarked images
preview_images = story_data.get('images', [])
if page_index < len(preview_images):
    preview_images[page_index] = f'/{preview_path}'
    story_data['images'] = preview_images

# Actualizar all_pages_preview
all_pages_preview = story_data.get('all_pages_preview', [])
if page_index < len(all_pages_preview):
    all_pages_preview[page_index] = f'/{preview_path}'
    story_data['all_pages_preview'] = all_pages_preview
```

---

## Estructura de Arrays en story_data JSON

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

## Posición del Autor en Portada

### Ubicación: 3cm del borde inferior
```python
# En generate_cover_spread() - illustrated_book_service.py
margin_bottom = int(cover_height_px * 0.03)  # ~3cm from bottom
author_y = cover_height_px - margin_bottom - 60  # 60px for text height

# Sombra para visibilidad
for dx, dy in [(-2, -2), (-2, 2), (2, -2), (2, 2), (-2, 0), (2, 0), (0, -2), (0, 2)]:
    draw.text((x + dx, author_y + dy), author_text, font=author_font, fill="#000000")
draw.text((x, author_y), author_text, font=author_font, fill="#FFFFFF")
```

---

## Modal de Advertencia (Obligatorio)

### Ubicación: templates/personalize_story.html

### Contenido del modal:
1. 🎨 **Ilustraciones con IA** - Son generadas por IA, pueden tener errores
2. 📖 **Revisa el Texto** - Leer bien antes de confirmar
3. 🔄 **Regenerar Ilustraciones** - Hasta 2 veces por página si hay anomalías
4. 📦 **Opciones de Envío** - Estándar incluido (10-20 días)
5. 📧 **PDF Digital** - Se envía por email, convertible a EPUB

### Checkbox obligatorio:
```html
<input type="checkbox" id="acceptTerms">
<span>He leído y entendido esta información</span>
```

---

## Estructura del PDF (26 páginas)

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

---

## Integración Paddle (Sandbox)

### Price IDs por Envío
| Método | Price ID | Precio |
|--------|----------|--------|
| MAIL | pri_01kgppgtvcch7vr9yanhdavebs | $55 |
| PRIORITY_MAIL | pri_01kgpvhztk4m4jzyrxbzxfpqvh | $65 |
| GROUND | pri_01kgpvq67hzjcymjy0z8k31z3v | $70 |
| EXPEDITED | pri_01kgpvsdqbanx08aac1pb5w70w | $75 |
| EXPRESS | pri_01kgpvvhjvgv8d659hba6c83sw | $80 |

---

## Integración Lulu

### Formato: A4 Hardcover (210mm x 297mm)
### Upscale: 300 DPI (2551 x 3579 pixels por página)

### Función de preparación:
```python
def prepare_for_lulu(story_data, for_print=True):
    # Upscale a 300 DPI para calidad de impresión
    dpi = 300
    page_width = 2551  # A4 + 3mm bleed
    page_height = 3579
```

---

## Prompts de Consistencia

### STYLE_BASE
```python
STYLE_BASE = "children's storybook watercolor illustration, soft luminous pastel colors, gentle warm lighting, dreamy magical atmosphere, full body characters shown completely from head to feet, clean illustration only"
```

### NEGATIVE_PROMPT (OBLIGATORIO)
```python
NEGATIVE_PROMPT = """text, watermark, signature, logo, tail, animal tail, dragon tail, 
wings on child, animal features on child, furry, animal ears, extra fingers, 
missing fingers, fused fingers, too many fingers, six fingers, malformed hands, 
bad hands anatomy, deformed hands, extra toes, missing toes, malformed feet, 
extra legs, four legs, extra arms, three arms, mutation, mutated"""
```

### Restricciones para evitar colas
```python
# SIEMPRE incluir en prompts:
"FULLY HUMAN child, NOT a hybrid, regular human body, NO tail whatsoever, NO animal features"
```

---

## Checklist para Nuevo Cuento

- [ ] Crear `services/personalized_books/stories/[nuevo_id].py`
- [ ] Definir STYLE_BASE específico del cuento
- [ ] Definir CHARACTER_TEMPLATE con restricciones de humanidad
- [ ] Definir COMPANION_DESC (mascota/personaje secundario)
- [ ] Escribir 19 escenas + escena de cierre
- [ ] Incluir NEGATIVE_PROMPT en cada prompt de imagen
- [ ] Crear prompts de portada y contraportada
- [ ] Agregar textos bilingües (ES/EN)
- [ ] Registrar en `__init__.py`
- [ ] Agregar imagen de catálogo `static/images/cover_[id].png`
- [ ] Probar flujo completo: form → generation → preview → payment → download
- [ ] Verificar regeneración funciona y se guarda en PDF final
- [ ] Verificar PDF tiene 26 páginas sin watermarks
- [ ] Verificar personaje consistente (sin cola, sin alas)
- [ ] Verificar autor a 3cm del borde inferior en portada

---

## Documentación Visible
Ver `docs/templates/personalized_book_template.md` para versión expandida.
