# Skill: Libros Personalizados

## Descripción
Plantilla completa para la sección de **Libros Personalizados** (Personalized Books) de Magic Memories Books. 
Cubre: Dragon Garden, Magic Chef, Magic Inventor Workshop, y cualquier libro futuro de esta sección.

**NO aplica para:** Quick Stories, Haz tu Historia, ni otras secciones del sitio.

## Documentación Detallada
La documentación visible con todos los prompts, estructura, y especificaciones está en:
`docs/templates/libros_personalizados.md`

## Archivos Clave de esta Sección

### Servicios (Backend)
- `services/personalized_books/__init__.py` - Registro de historias disponibles
- `services/personalized_books/generation.py` - Lógica de generación de libros
- `services/personalized_books/stories/dragon_garden.py` - Config Dragon Garden
- `services/personalized_books/stories/magic_chef.py` - Config Magic Chef
- `services/personalized_books/stories/magic_inventor.py` - Config Magic Inventor
- `services/personalized_books/magic_inventor_prompts.py` - Prompts Magic Inventor
- `services/illustrated_book_service.py` - Generación de imágenes FLUX + cover spread + PDF
- `services/pdf_service.py` - Generación de PDFs
- `services/lulu_api_service.py` - Envío de órdenes a Lulu
- `services/lulu_storage.py` - Almacenamiento de archivos para Lulu
- `services/email_service.py` - Envío de emails

### Templates (Frontend)
- `templates/personalize_story.html` - Formulario de personalización + modal advertencia
- `templates/order_complete.html` - Vista previa + regeneración de páginas

### Rutas en app.py
- `/personalized-book/<story_id>` - Formulario
- `/personalized-book/generate` - Generación de libro completo
- `/personalized-book/checkout` - Selección de envío + PayPal
- `/order-complete/<preview_id>` - Vista previa + regeneración
- `/api/regenerate-page/<preview_id>/<page_num>` - Regenerar página

## Reglas Críticas

### 1. Modelo de Imágenes: SOLO FLUX Dev
TODAS las imágenes usan `black-forest-labs/flux-dev`:
- Preview de personaje → FLUX Dev
- 19 escenas → FLUX Dev  
- Portada → FLUX Dev
- Contraportada dinámica (Dragon Garden) → FLUX Dev
- Cierre → FLUX Dev
**NUNCA usar FLUX 2 Pro, FLUX Pro, ni DALL-E para esta sección.**

### 2. Lulu Casewrap Hardcover (BLINDADO - No Modificar)
```
Interior trim: 210mm × 297mm (A4)
Board overhang: 3.175mm (1/8") en top, bottom, fore-edge (NO spine side)
Board size: 213.175mm × 303.35mm
Wrap area: 19.05mm (3/4") en TODOS los bordes del spread
Spine width: 6.35mm (1/4") para 24-84 páginas casewrap
Total spread: 470.80mm × 341.45mm = 5560 × 4032 px a 300 DPI
Rango aceptado Lulu: 469.33-472.50mm × 339.79-342.96mm
Layout: [Wrap 19mm][Back Board 213mm][Spine 6.35mm][Front Board 213mm][Wrap 19mm]
```
**ESTAS DIMENSIONES ESTÁN VERIFICADAS Y APROBADAS POR LULU. NO CAMBIAR.**

### 3. Pipeline Unificado (PayPal + Lulu)
Los pagos se procesan via PayPal. La ruta `/api/payment-complete/<preview_id>` maneja la confirmación.
Una sola función `_process_personalized_book_post_payment()` procesa todos los libros.
El `book_id` / `story_id` determina qué libro es. No hay código separado por libro.

### 4. Contraportadas
- Dragon Garden: generada dinámicamente con FLUX Dev
- Magic Chef: imagen fija `static/images/fixed_pages/magic_chef_back_cover.png`
- Magic Inventor: imagen fija `static/images/fixed_pages/magic_inventor_back_cover.png`

### 5. PDF: 26 páginas
1. Portada | 2. Portadilla | 3. Dedicatoria | 4-22. 19 Escenas | 23. Cierre | 24. Créditos | 25. Blanca | 26. Contraportada

### 6. BOLT (Magic Inventor)
Pequeño robot redondo de cobre, cuerpo esférico, ojos LED azules, brazos/piernas metálicos, antena. **SIN COLA.**

### 7. Crear Libro Nuevo: OBLIGATORIO seguir checklist
Al crear un libro nuevo, **LEER Y SEGUIR** el checklist completo en:
`docs/templates/libros_personalizados.md` → Sección 13 "Checklist para Nuevo Cuento"

Resumen de los puntos más críticos (los que han causado errores antes):
1. `generation.py` → Agregar en **3 funciones centralizadas**: `get_personalized_book_id()`, `is_personalized_book()`, `get_lulu_title()` (app.py las importa automáticamente, NO hay que tocar app.py para esto)
2. `preview.py` → Agregar elif para el preview del personaje
3. `checkout.py` → Agregar story_id en `PERSONALIZED_BOOK_IDS`
4. `illustrated_book_service.py` → Agregar en `load_book_config()`, `generate_cover_spread()`, `generate_closing_page()`
5. Si contraportada fija: agregar imagen + elif en `_process_personalized_book_post_payment` de app.py
6. **NO MODIFICAR** las dimensiones de Lulu casewrap (470.80mm × 341.45mm)
