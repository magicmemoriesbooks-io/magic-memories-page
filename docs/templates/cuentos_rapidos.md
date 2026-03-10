# Cuentos Rápidos - Documento Maestro

## Resumen
15 cuentos en total: 4 bebés (0-2), 8 kids (3-8), 3 cumpleaños (0-2, 3-5, 5-7).
Todos comparten el mismo flujo de pago, generación y entrega.

---

## Productos y Precios

| Opción | Precio | Incluye |
|--------|--------|---------|
| eBook Interactivo | $7 USD | Visor flipbook (permanente) |
| Digital + PDF Imprimible | $20 USD | eBook visor (permanente) + PDF 8.5"×8.5" + instrucciones imprenta |
| Libro Impreso | $20 USD + envío | eBook visor (6 meses regalo) + libro impreso Lulu saddle stitch |

---

## Catálogo de Cuentos

### Bebés (0-2 años) — 8 escenas, 12 páginas
| # | story_id | Título ES | Título EN | Portada |
|---|----------|-----------|-----------|---------|
| 1 | `baby_soft_world` | {name} y el mundo suave | {name} and the Soft World | `cover_baby_soft_world.png` |
| 2 | `baby_puppy_love` | ¿Sabes cuánto te quiero, {name}? | Do You Know How Much I Love You, {name}? | `cover_baby_puppy_love.png` |
| 3 | `baby_first_pet` | {name} y su Primera Mascota | {name} and Their First Pet | `cover_baby_first_pet.png` |
| 4 | `baby_guardian_light` | {name} y la Luz Guardiana | {name} and the Guardian Light | `cover_baby_guardian_light.png` |

### Kids (3-8 años) — 7 escenas + 1 closing, 12 páginas
| # | story_id | Título ES | Título EN | Edad | Portada |
|---|----------|-----------|-----------|------|---------|
| 5 | `dragon_friend` | {name} y su Amigo el Dragón | {name} and Their Dragon Friend | 3-8 | `cover_dragon_friend.png` |
| 6 | `zebra_stripes` | {name} y la aventura en la sabana | {name} and the Savanna Adventure | 3-8 | `cover_zebra_stripes.png` |
| 7 | `space_astronaut` | {name} el Astronauta | {name} the Astronaut | 3-8 | `cover_space_astronaut.png` |
| 8 | `superhero_light` | {name} y la Luz del Superhéroe | {name} and the Superhero Light | 3-8 | `cover_superhero_light.png` |
| 9 | `star_guardian` | {name} Guardián de las Estrellas | {name} Guardian of the Stars | 5-7 | `cover_star_guardian.png` |
| 10 | `chronicles_valley` | Las Crónicas de {name} | {name} and the Valley Chronicles | 5-7 | `cover_chronicles_valley.png` |
| 11 | `sunset_map` | {name} y el Mapa del Atardecer | {name} and the Sunset Map | 5-7 | `cover_sunset_map.png` |
| 12 | `dog_forever` | {name} y su Perro para Siempre | {name} and Their Dog Forever | 5-7 | `cover_dog_forever.png` |

### Cumpleaños — 6 escenas, 12 páginas (misma estructura que kids)
| # | story_id | Edad | Portada |
|---|----------|------|---------|
| 13 | `birthday_celebration` | 3-5 | `cover_birthday_celebration.png` |
| 14 | `birthday_celebration_5_7` | 5-7 | `cover_birthday_celebration_5_7.png` |
| 15 | `birthday_celebration_0_2` | 0-2 | `cover_birthday_celebration_0_2.png` |

---

## Contraportada Fija
- **Archivo**: `static/images/quick_story_back_cover.png`
- **Todos los cuentos rápidos y cumpleaños usan la misma contraportada**
- Cuadrada 8.5"×8.5", con logo MMB, frase inspiracional, URL del sitio

---

## Estructura PDF

### PDF Digital (envío por email) — 8.5"×8.5" cuadrado

#### Bebés (0-2): 12 páginas
| Pág | Contenido |
|-----|-----------|
| 1 | Portada (cover con título superpuesto) |
| 2 | Portadilla (título + "Una aventura de {name}" + estrella decorativa + MagicMemoriesBooks) |
| 3 | Dedicatoria (marco dorado, fondo crema #FFFBF5, texto dinámico) |
| 4-11 | 8 escenas con texto overlay (cloud-shaped, drop cap 60pt #935efb, body 25pt #545454) |
| 12 | Contraportada fija |

#### Kids (3-8): 10 páginas
| Pág | Contenido |
|-----|-----------|
| 1 | Portada (cover con título) |
| 2 | Dedicatoria (marco dorado) |
| 3-9 | 7 escenas con texto split (text_above + ilustración + text_below) |
| 10 | Contraportada fija |

#### Cumpleaños: Misma estructura que su rango de edad
- `birthday_celebration_0_2`: Estructura de bebés (8 escenas → 12 págs) — **NOTA: solo tiene 6 escenas, pendiente ajustar**
- `birthday_celebration`: Estructura de kids (6 escenas → 10 págs)
- `birthday_celebration_5_7`: Estructura de kids (6 escenas → 10 págs)

### PDF Imprimible (Lulu saddle stitch) — 8.5"×8.5"
- **pod_package_id**: `0850X0850FCPRESS080CW444GXX`
- Interior: 10 páginas (sin portada/contraportada)
- Cover spread: 17.25"×8.75" (438.15mm×222.25mm), back+front side by side

---

## Flujo Post-Pago

### Digital ($20)
1. Pago → `process_payment()` → `_trigger_background_generation()`
2. Escenas se generan en background (TaskQueue)
3. Al completar → `_process_ebook_generation()`:
   - Prepara visor en `generations/visor/{preview_id}/` (12 págs JPG + metadata.json)
   - Genera PDF imprimible 8.5"×8.5" + instrucciones de impresión
   - Envía email con: botón visor + PDF adjunto + instrucciones adjuntas
4. `confirm-and-send` como fallback si la generación automática falla

### Impreso ($20 + envío)
1. Pago → escenas en background
2. Al completar → `_process_quick_story_print()`:
   - Genera PDFs Lulu (interior + cover spread)
   - Sube a Lulu para impresión
   - Prepara visor como regalo (6 meses)
   - Envía email con: botón visor + notificación de envío

### eBook ($7)
1. Pago → escenas en background (si pendientes)
2. Al completar → `_process_ebook_generation()`:
   - Prepara visor (acceso permanente)
   - Envía email con botón visor
   - NO genera PDF imprimible, NO Lulu

---

## Visor Interactivo (eBook)

### Estructura de archivos
```
generations/visor/{preview_id}/
├── metadata.json      (título, páginas, textos, música, expiración)
├── page_1.jpg         (portada)
├── page_2.jpg         (dedicatoria - generada con Pillow)
├── page_3.jpg         (portadilla - generada con Pillow)
├── page_4.jpg         (escena 1 con texto overlay)
├── ...
├── page_11.jpg        (escena 8 / closing)
└── page_12.jpg        (contraportada MMB)
```

### Música por tipo
| Tipo | Archivo |
|------|---------|
| Bebés (0-2) | `nana_bebes.mp3` |
| Kids (3-8) | `fantasia.mp3` |
| Cumpleaños | `happy_birthday.mp3` |
| Teens | `aventura_ninos.mp3` |

### Expiración
| Tipo compra | Expiración |
|-------------|------------|
| eBook $7 | Permanente (`expires_at: null`) |
| Digital $20 | Permanente (`expires_at: null`) |
| Impreso $20+ | 6 meses regalo (`expires_at: fecha + 180 días`) |

---

## Archivos de Código Relevantes

| Archivo | Responsabilidad |
|---------|----------------|
| `services/quick_stories/stories.py` | Definiciones de cuentos (títulos, age_range, categoría) |
| `services/quick_stories/checkout.py` | IDs, precios, config de checkout, `is_quick_story()` |
| `services/quick_stories/pdf_service.py` | Generación PDF digital + Lulu |
| `services/fixed_stories.py` | Escenas, textos, prompts de cada cuento |
| `services/pdf_service.py` | `create_baby_quick_story_pdf()`, `create_kids_quick_story_pdf()`, `generate_print_instructions_pdf()` |
| `services/vps_upload_service.py` | Preparación visor + upload SFTP |
| `services/email_service.py` | `send_ebook_email()` con PDFs adjuntos |
| `app.py` | `_process_ebook_generation()`, `_process_quick_story_print()`, `confirm_and_send()` |

---

## Datos del Story (JSON)

Campos relevantes en `story_previews/{preview_id}.json`:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `story_id` | string | ID del cuento (e.g. `dragon_friend`) |
| `child_name` | string | Nombre del niño |
| `age_range` | string | `0-1`, `0-2`, `3-5`, `3-8`, `5-7`, `6-8` |
| `scene_paths` | array | Rutas de escenas generadas: `["/generated/story_XXX/scene_1.png", ...]` |
| `images` | array | Alias de scene_paths |
| `original_images` | array | Copia de seguridad de scene_paths |
| `original_cover` | string | Ruta de portada: `/generated/story_XXX/cover.png` |
| `cover_image` | string | Alias de original_cover |
| `closing_image` | string | Ruta de ilustración de cierre |
| `texts` | array | Textos de cada escena (puede estar vacío si están en fixed_stories) |
| `scenes` | array | Objetos con text_es/text_en de fixed_stories |
| `dedication` | string | Texto de dedicatoria personalizado |
| `visor_url` | string | URL del visor: `https://domain/visor/?id={preview_id}` |
| `visor_uploaded` | bool | Si el visor ya fue preparado |
| `pdf_printable_path` | string | Ruta del PDF imprimible generado |
| `instructions_path` | string | Ruta del PDF de instrucciones |
| `paid` | bool | Si ya se completó el pago |
| `want_print` | bool | Si eligió opción impresa |
| `product_type` | string | `qs_digital`, `qs_print`, `ebook` |
| `email_sent` | bool | Si se envió el email final |

---

## Problemas Conocidos (Pendientes)

1. **Cumpleaños**: Los 3 cuentos tienen solo 6 escenas (no 7-8 como los demás). Necesitan ajuste en estructura PDF.
2. **PDF Imprimible**: Las imágenes no se incluyen porque `generate_quick_story_pdf()` busca `scene_images` que no existe en story_data. Debe usar `scene_paths` o `images`.
3. **Visor dedicatoria**: El texto largo se corta horizontalmente. Necesita word-wrap con márgenes.
