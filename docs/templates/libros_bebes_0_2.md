# Especificaciones: Libros para Bebés (0-2 años)
**Última actualización**: Febrero 2026

## Formato del Libro
- **Tamaño**: 8.5" × 8.5" (cuadrado)
- **Total de páginas**: 12
- **Encuadernación**: Saddle stitch (engrapado) para Lulu
- **Lulu POD Package ID**: `0850X0850FCPRESS080CW444GXX`

## Estructura de Páginas (12 páginas)

| Página | Contenido | Notas |
|--------|-----------|-------|
| 1 | Portada (cover) | Preview FLUX 2 Pro con texto overlay del título |
| 2 | Portadilla (title page) | Título del libro + "Magic Memories Books" |
| 3 | Dedicatoria | Marco decorativo doble, texto centrado |
| 4 | Escena 1 | Ilustración Ideogram + texto superpuesto |
| 5 | Escena 2 | Ilustración Ideogram + texto superpuesto |
| 6 | Escena 3 | Ilustración Ideogram + texto superpuesto |
| 7 | Escena 4 | Ilustración Ideogram + texto superpuesto |
| 8 | Escena 5 | Ilustración Ideogram + texto superpuesto |
| 9 | Escena 6 | Ilustración Ideogram + texto superpuesto |
| 10 | Escena 7 | Ilustración Ideogram + texto superpuesto |
| 11 | Escena 8 | Ilustración Ideogram + texto superpuesto |
| 12 | Contraportada fija | Imagen estática de la marca |

## Estructura para Lulu (Saddle Stitch)

### Cover Spread (PDF separado)
- Back cover (izquierda) + Front cover (derecha)
- Sin lomo (saddle stitch no tiene lomo)
- Dimensiones: 438.15mm × 222.25mm
- Generado por `create_quick_story_lulu_cover()`

### Interior PDF (10 páginas)
Páginas 2-11 del libro (covers van en PDF separado):
1. Portadilla
2. Dedicatoria (centrada, con marco decorativo)
3-10. 8 escenas con ilustración + texto

Generado por `create_baby_quick_story_pdf(format_type='lulu')`

## Generación de PDFs

### Función única: `create_baby_quick_story_pdf()`
Ubicación: `services/pdf_service.py`

Genera TODOS los formatos de PDF para bebés:
- `format_type='digital'` → 12 páginas (portada + interior + contraportada)
- `format_type='print'` → 12 páginas (igual que digital)
- `format_type='lulu'` → 10 páginas interior (sin portada ni contraportada)

**IMPORTANTE**: Todos los formatos usan `skip_sanitize=True` (sin Ghostscript) para preservar el degradado transparente del texto overlay.

### Dedicatoria (idéntica en todos los formatos)
- Fondo: `#FFFBF5` (crema)
- Marco decorativo doble (bordes redondeados, color `#D4A574` y `#E8C9A0`)
- Título "Dedicatoria" centrado en Titan One 28pt, color `#8B6914`
- Línea ornamental debajo del título
- Texto de dedicatoria centrado en KACST Decorative 18pt, color `#4A3728`

## Tipografía del Texto Overlay (Escenas)

### En el PDF (`_draw_text_overlay` en `services/pdf_service.py`)
- **Drop cap**: Nunito-ExtraBold, 52pt, color `#5e17eb` (morado)
- **Texto del cuerpo**: Nunito-SemiBold, 24pt, color `#2d2c2c` (gris oscuro)
- **Fondo**: Degradado transparente generado con ReportLab
  - Parte superior (25-40%): completamente transparente
  - Parte inferior: curva a 95% blanco
  - Bordes redondeados solo en la parte inferior
- **Alineación**: Todo el texto alineado a la izquierda
- **Márgenes**: 2cm laterales, contenido centrado horizontalmente en la página
- **Drop cap**: 2 líneas de alto, texto fluye a su derecha

### En el Preview Web (`order_complete.html`)
- **Drop cap**: Nunito ExtraBold, `2.17em` relativo al body, color `#5e17eb`, float left
- **Texto del cuerpo**: Nunito SemiBold, `clamp(8px, 3.2vw, 20px)`, color `#2d2c2c`
- **Alineación**: `text-align: left` — las líneas de continuación quedan debajo del texto body, NO debajo de la letra capital
- **Fondo**: Degradado CSS `linear-gradient` de transparente a 98% blanco
- **Posición**: `bottom: 3%; left: 5%; right: 5%`

**IMPORTANTE**: No usar Ghostscript (`skip_sanitize=True`) porque destruye el degradado transparente.

## Prevención de Generación Duplicada

### Problema
Flask en modo debug crea dos procesos (stat reloader). Tras el pago, dos requests GET llegan a `/order-complete/` casi simultáneamente:
1. El redirect de Paddle (con `{transaction_id}` sin resolver)
2. El redirect del `process-payment` POST (con transaction_id real)

Ambas ven `scenes_pending=True` y ambas intentan generar las 8 escenas.

### Solución: Lock basado en archivo
Ubicación: `app.py`, ruta `order-complete`

```
output_dir/.generation.lock
```

**Flujo del lock:**
1. Primera request: crea `.generation.lock` con el PID del proceso
2. Segunda request: detecta el lock, verifica su edad (< 10 min = válido)
3. Segunda request: entra en polling (cada 5 seg lee preview.json)
4. Cuando primera request termina: `scenes_pending=False` en preview.json + elimina lock
5. Segunda request: detecta `scenes_pending=False`, carga resultados
6. Si lock tiene > 10 min (stale): se ignora y se regenera

**Cleanup**: El lock se elimina en el bloque `finally` tras la generación (éxito o error).

**Aplica a**: TODOS los Quick Stories que tengan `scenes_pending=True`, no solo un cuento específico.

## Generación de Imágenes

### Flujo completo
```
FLUX 2 Pro → base_character.png (preview)
           → cover.png (copia de base_character)
           → cover_clean.png (copia sin texto, referencia para Ideogram)
           → cover.png final (cover_clean + texto overlay del título)

Ideogram Character → scene_1.png a scene_8.png (usa cover_clean.png como referencia)
```

### Preview/Portada (FLUX 2 Pro)
- Modelo: FLUX 2 Pro via Replicate
- Prompt incluye descripción completa del personaje: pelo, ojos, piel, ropa
- La preview SE USA como portada (`use_preview_as_cover: True`)
- **Edad 0**: Usa `preview_prompt_override` (bebé sentado)
- **Edad 1-2**: Usa `preview_prompt_override_toddler` (niño parado)
- `adapt_baby_pose_for_age()` agrega restricción "CANNOT stand or walk" solo para edad 0

### Escenas (Ideogram Character)
- Modelo: Ideogram Character via Replicate
- Usa cover_clean.png como `character_reference_image`
- Prompts SIN descripción de personaje (Ideogram lo auto-detecta de la referencia)
- Formato de prompt: [Estilo Disney 3D Pixar] + [Acción/Pose] + [Entorno] + [Ambiente]
- Se añade automáticamente: "STRICT: Maintain exact same baby face..."
- Parámetros: style_type="Fiction", aspect_ratio="1:1", magic_prompt_option="Auto"
- **Edad 0**: Usa `scene_template` (bebé sentado/acostado)
- **Edad 1-2**: Usa `scene_template_toddler` (niño parado/caminando)
- Sin fallback a FLUX (para preservar consistencia del personaje)
- Reintentos: máximo 3 intentos con espera incremental

### Reglas de Nombres de Companions en Prompts (CRÍTICO)

**Companions físicos (animales/peluches)**: POMPOM, MISU, NUBE
- SÍ pueden aparecer en prompts de escena (son objetos/animales donde Ideogram no renderiza texto)
- Sirven para consistencia visual del companion a lo largo del cuento

**Companions abstractos/luminosos**: (anteriormente "LUCERO")
- NUNCA poner nombres propios en los prompts — Ideogram los renderiza como texto visible en superficies lisas
- Usar solo descripciones: "a tiny smooth featureless sphere of pure warm golden light"
- Agregar restricciones explícitas: "(NO face, NO eyes, NO text, NO letters, NO words on it)"

### Selección de prompts por edad (CRÍTICO)
```python
is_toddler = is_baby_story and child_age >= 1

# Preview (FLUX 2 Pro):
if is_toddler and 'preview_prompt_override_toddler' in story_config:
    prompt = story_config['preview_prompt_override_toddler']
else:
    prompt = story_config['preview_prompt_override']

# Escenas (Ideogram Character):
if is_toddler and 'scene_template_toddler' in page:
    template = page['scene_template_toddler']
else:
    template = page['scene_template']
```

Lógica implementada en 3 lugares:
1. `generate_base_character()` en `services/replicate_service.py` (preview inicial)
2. Ruta de regeneración de preview en `app.py` (~línea 1280)
3. `get_scene_prompts()` y `get_story_data()` en `services/fixed_stories.py`

### Regeneración de Escenas
- Máximo 2 regeneraciones por escena
- SIEMPRE usa Ideogram Character (nunca FLUX)
- Usa la misma imagen de referencia (cover_clean.png o base_character.png)

## Cuentos Disponibles (0-2 años)

### baby_soft_world - "El Mundo Suave"
- **Flag**: `use_ideogram_scenes: True`
- **Companion**: Conejito de peluche blanco (sin nombre fijo en prompts)
- **8 escenas**: nursery, cintas de colores, voces dulces, descubrimiento, burbujas, mariposas, jardín, descanso

### baby_puppy_love - "¿Sabes cuánto te quiero?"
- **Flag**: `use_ideogram_scenes: True`
- **Companion**: POMPOM (perrito de peluche dorado, ojos negros de botón, nariz rosa bordada)
- **8 escenas**: primer encuentro, cola moviéndose, abrazo fuerte, "te quiero más", luna y estrellas, juegos, estrellas nocturnas, descanso juntos

### baby_first_pet - "Mi primera mascota"
- **Flag**: `use_ideogram_scenes: True`
- **Companion**: MISU (gatito real ginger-naranja, ojos verdes, no peluche)
- **MISU aparece en textos del cuento**: "MISU bosteza despacito", "MISU se acurruca conmigo" — esto es INTENCIONAL
- **8 escenas**: primer encuentro, acercamiento, contacto visual, caricia, juego, ronroneo, luna, descanso

### baby_guardian_light - "La luz que lo cuida"
- **Flag**: `use_ideogram_scenes: True`
- **Companion**: Esfera de luz dorada (SIN NOMBRE en prompts ni en textos)
- **Descripción en prompts**: "a tiny smooth featureless sphere of pure warm golden light (NO face, NO eyes, NO text, NO letters, NO words on it)"
- **En textos del cuento**: Se refiere como "la luz" / "the light" (NUNCA usar nombre propio)
- **8 escenas**: luz aparece, movimiento lento, risa, juegos protegidos, halo protector, baile con estrellas, nightlight, descanso

## Flujo Post-Pago (Generación de Escenas)

```
1. Usuario paga → Paddle checkout.completed
2. JavaScript llama POST /api/process-payment/{preview_id}
   → Valida pago, envía email confirmación
   → Redirige a GET /order-complete/{preview_id}
3. GET /order-complete/{preview_id}
   → Ve scenes_pending=True
   → Crea .generation.lock en output_dir
   → Genera 8 escenas con Ideogram Character (3-5 min, síncrono)
   → Actualiza preview.json: scenes_pending=False
   → Elimina .generation.lock
   → Renderiza página con escenas
4. Segunda request (si llega):
   → Ve .generation.lock activo
   → Espera (polling cada 5s) hasta scenes_pending=False
   → Carga resultados del JSON y renderiza
```

## Costos Estimados por Cuento
- Preview (FLUX 2 Pro): ~$0.05
- 8 escenas (Ideogram Character): ~$0.04-0.06 cada una = ~$0.32-0.48
- **Total**: ~$0.37-0.53 por cuento

## Precios al Cliente
- **$25 USD**: PDF digital + PDF imprimible con instrucciones (entrega por email)
- **$29 USD**: Libro impreso + envío incluido + PDF digital

## Archivos Clave
- `services/fixed_stories.py` - Definición de cuentos, templates de escenas (scene_template + scene_template_toddler)
- `services/replicate_service.py` - Generación de imágenes (FLUX 2 Pro + Ideogram Character)
- `services/pdf_service.py` - Generación de PDFs (`create_baby_quick_story_pdf` para todos los formatos, `_draw_text_overlay` para texto en escenas)
- `services/quick_stories/pdf_service.py` - Wrapper Lulu (`generate_quick_story_lulu_pdfs`)
- `app.py` - Rutas de preview, regeneración, flujo post-pago con lock anti-duplicados
- `templates/order_complete.html` - Preview web con texto overlay responsive
- `docs/templates/libros_bebes_0_2.md` - Esta documentación
