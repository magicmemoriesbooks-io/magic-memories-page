# Plantilla: Tú y tu Amor Peludo (furry_love)

## Sección
**Libro Personalizado Ilustrado** - Celebra el vínculo entre una persona y su perro.
**Producto**: Print + Digital ($35 + envío + impuestos)

---

## 1. Concepto del Libro

**Historia**: Un perro ya vive en casa cuando llega un bebé. 19 escenas narran los momentos tiernos desde la llegada del bebé hasta que camina, todo desde la perspectiva del vínculo humano-mascota.

**Protagonistas**:
- **Humano**: Personalizable (nombre, género, edad 0-8+, cabello, ojos, piel). Puede ser bebé, niño, adolescente o adulto.
- **Mascota**: Siempre un perro. Personalizable (nombre, raza, color/patrón, tamaño).

**Diferencia clave vs otros libros**: Usa **DOS imágenes de referencia** (humano + perro) en lugar de una sola. Esto requiere FLUX 2 Dev con entrada dual.

---

## 2. Arquitectura de Archivos

```
services/personalized_books/
├── furry_love_prompts.py          # Prompts de escenas, portadas, funciones build_*
├── preview.py                     # Generación de previews (compartido, con lógica furry_love)
├── generation.py                  # get_personalized_book_id(), is_personalized_book(), get_lulu_title()

services/illustrated_book_service.py  # BOOK_CONFIGS["furry_love"], generación de escenas con 2 refs
templates/personalize_furry_love.html # Formulario dedicado (humano + mascota)
templates/checkout_unified.html       # Checkout compartido (Paddle)
templates/order_complete.html         # Aprobación de escenas + descarga PDF
app.py                                # Rutas: /personalize-furry-love, generate-baby-preview, etc.
```

---

## 3. Formulario de Personalización (`personalize_furry_love.html`)

### Panel Izquierdo: Protagonista Humano
| Campo | Tipo | Valores | Requerido |
|-------|------|---------|-----------|
| Nombre | text | libre | Sí |
| Foto | file (JPG/PNG, max 5MB) | opcional | No |
| Género | select | female, male, neutral | Sí |
| Edad | select | 0 (Bebé) a 8+ | Sí |
| Idioma | select | ES, EN | Sí |
| Color cabello | radio visual | black, brown, blonde, light_blonde, red, gray | Sí |
| Tipo cabello | radio visual | straight, wavy, curly, coily | Sí |
| Longitud cabello | radio | very_little, short, medium, long | Sí |
| Color ojos | radio visual | black, brown, hazel, green, blue, gray | Sí |
| Tono piel | radio visual | light, medium_light, medium, olive, tan, brown, dark | Sí |

### Panel Derecho: Mascota (Perro)
| Campo | Tipo | Valores | Requerido |
|-------|------|---------|-----------|
| Nombre | text | libre | Sí |
| Foto | file (JPG/PNG, max 5MB) | opcional | No |
| Raza | select | 30+ razas comunes | Sí |
| Color/Patrón | select | white, black, brown, golden, etc. | Sí |
| Tamaño | select | small, medium, large | Sí |

### Sección Inferior: Autor y Dedicatoria
| Campo | Tipo | Requerido |
|-------|------|-----------|
| Nombre del autor | text | No |
| Dedicatoria | textarea (máx 200 chars) | No |

---

## 4. Flujo de Generación de Preview

### 4.1 Endpoint: `/api/generate-baby-preview` (POST)

**Para furry_love**: Genera **DOS** previews separados:

1. **Preview Humano**: 
   - Si hay foto: `build_human_preview_prompt_with_photo()` + foto como referencia en FLUX 2 Dev
   - Sin foto: `build_human_preview_prompt()` con descripción textual
   - Modelo: `black-forest-labs/flux-2-dev` (con o sin referencia)
   - Aspecto: `3:4`

2. **Preview Mascota**:
   - Si hay foto: `build_pet_preview_prompt_with_photo()` + foto como referencia en FLUX 2 Dev
   - Sin foto: `build_pet_preview_prompt()` con descripción textual
   - Modelo: `black-forest-labs/flux-2-dev` (con o sin referencia)
   - Aspecto: `3:4`

**Respuesta especial**: Devuelve `human_preview` + `pet_preview` (dos URLs) en vez de un solo `preview_image`.

### 4.2 Regeneración Individual: `/api/regenerate-furry-preview` (POST)

Permite regenerar solo el preview del humano O solo el de la mascota sin regenerar el otro. Recibe `preview_type: "human" | "pet"`.

---

## 5. Sistema de Prompts (`furry_love_prompts.py`)

### 5.1 STYLE_BASE
```python
STYLE_BASE = "Disney Pixar 3D style, soft warm golden lighting, tender emotional atmosphere, 
WIDE SHOT full body from head to feet, characters occupy 40% of frame, cozy home environment 
visible, clean illustration only, NO text, NO watermarks. STRICT: ALL human characters MUST be 
fully clothed at all times, babies must wear onesies or pajamas, NO nudity ever."
```

### 5.2 Esquema de Prompts
```
PET: {pet_desc} → ACTION → SETTING → ATMOSPHERE → STRICT → {style}
```
- Los prompts de escena incluyen `{pet_desc}`, `{name}`, `{pet_name}` y `{style}` como placeholders.
- `build_scene_prompt()` reemplaza estos placeholders con los datos del personaje.

### 5.3 Funciones Clave
| Función | Propósito |
|---------|-----------|
| `build_human_preview_prompt(traits)` | Prompt para preview humano sin foto |
| `build_human_preview_prompt_with_photo(traits)` | Prompt para preview humano con foto referencia |
| `build_pet_preview_prompt(traits)` | Prompt para preview mascota sin foto |
| `build_pet_preview_prompt_with_photo(traits)` | Prompt para preview mascota con foto referencia |
| `build_scene_prompt(scene, traits, style)` | Arma prompt de escena reemplazando placeholders |
| `build_pet_desc(traits)` | Genera descripción textual del perro (raza, color, tamaño) |

### 5.4 Parámetros FLUX 2 Dev
```python
guidance_scale = 3.5    # NUNCA subir a 7.0 (causa alucinaciones)
num_inference_steps = 28
aspect_ratio = "3:4"    # Portrait para páginas interiores
output_format = "png"
```

---

## 6. Generación de Escenas (Post-Pago)

### 6.1 Diferencia clave: DOS referencias

En `illustrated_book_service.py` → `generate_scene_complete()`:

```python
is_furry = book_id == 'furry_love'

if is_furry and reference_image_path_2:
    # FLUX 2 Dev con DOS imágenes de referencia
    output = replicate.run(
        "black-forest-labs/flux-2-dev",
        input={
            "prompt": enhanced_prompt,
            "image": ref1_file,          # @image1 = humano
            "image2": ref2_file,         # @image2 = mascota  
            "aspect_ratio": "3:4",
            "guidance": 3.5,
            "num_inference_steps": 28,
            "output_format": "png",
            "prompt_upsampling": False
        }
    )
```

### 6.2 Nota de Referencia (Anti-Blending)
Se añade a cada prompt:
```
CRITICAL: @image1 is the HUMAN character reference, @image2 is the DOG reference. 
Keep SAME human appearance as @image1 and SAME dog appearance as @image2. 
The human must have ONLY human features, the dog must have ONLY canine features. 
They are TWO separate beings.
```

### 6.3 Escenas (19 + closing)

| Escena | Tema | Edad del bebé |
|--------|------|---------------|
| 1 | Nursery - perro solo, anticipando | Pre-nacimiento |
| 2 | Llegada del bebé en cochecito | Recién nacido |
| 3 | Primera vez que el perro huele al bebé | Recién nacido |
| 4 | Primera noche - perro guarda la cuna | Recién nacido |
| 5 | Primera sonrisa del bebé | ~2 meses |
| 6 | Perro comparte su juguete favorito | ~3 meses |
| 7 | Bebé toca el pelaje por primera vez | ~4 meses |
| 8 | Hora del baño - salpicones | ~5 meses |
| 9 | Tummy time - cara a cara | ~4 meses |
| 10 | Primeros gateos hacia el perro | ~7 meses |
| 11 | Jardín - primer contacto con pasto | ~8 meses |
| 12 | Día de lluvia - juntos en ventana | ~9 meses |
| 13 | Hora de comida - "limpieza" | ~10 meses |
| 14 | Lectura nocturna - se duermen juntos | ~11 meses |
| 15 | Tormenta - perro protege al bebé | ~10 meses |
| 16 | Primeros pasos hacia el perro | ~12 meses |
| 17 | Jugando fetch en jardín | ~15 meses |
| 18 | Siesta juntos (ANTI-BLENDING reforzado) | ~18 meses |
| 19 | Parque - caminan juntos, final abierto | ~2 años |
| Closing | Silueta al atardecer | Atemporal |

### 6.4 Problema Conocido: Blending en Escena 18
La escena de la siesta (nap) tiene prompts reforzados porque cuando humano y perro están muy cerca, FLUX tiende a mezclar rasgos. El prompt incluye:
- "HUMAN skin and HUMAN face"
- "clearly a separate animal from the child"
- "child must have ONLY human features (human face, human skin, human hands, NO fur, NO animal traits)"

---

## 7. Portada y Contraportada

### 7.1 Portada (FRONT_COVER)
- Generada con FLUX 2 Dev usando el preview del humano como referencia
- Prompt en `FRONT_COVER` de `furry_love_prompts.py`
- Color de título: `#4A1A6B` (púrpura)
- Subtítulo: "Una aventura de {name}" / "An adventure of {name}"

### 7.2 Contraportada (BACK_COVER)
- **Tipo: Dinámica** (generada con FLUX 2 Dev, igual que Dragon Garden)
- Prompt en `BACK_COVER` de `furry_love_prompts.py`
- NO está en el diccionario `fixed_back_covers` → se genera automáticamente

### 7.3 Título del Libro
- **Con nombre de mascota**: "El día que {pet_name} conoció a {child_name}"
- **Sin nombre (fallback)**: "El día que su Amor Peludo conoció a {child_name}"
- Centralizado en `get_lulu_title()` en `generation.py`

---

## 8. Estructura PDF (26 páginas)

| Página | Contenido |
|--------|-----------|
| 1 | Portada (cover) |
| 2 | Portadilla (título + autor) |
| 3 | Dedicatoria |
| 4-22 | 19 Escenas |
| 23 | Ilustración de cierre |
| 24 | Créditos |
| 25 | Página blanca |
| 26 | Contraportada (dinámica) |

**Formato Lulu**: A4 Casewrap Hardcover, 300 DPI, 2551×3579 px por página.

---

## 9. Puntos de Integración en app.py

| Punto | Función/Ruta | Qué hace para furry_love |
|-------|-------------|--------------------------|
| Formulario | `/personalize-furry-love` | Renderiza `personalize_furry_love.html` |
| Preview | `/api/generate-baby-preview` | Genera 2 previews (humano + mascota) |
| Regen preview | `/api/regenerate-furry-preview` | Regenera 1 preview individual |
| Generar libro | `/api/generate-illustrated-book` | Genera portada + guarda datos con `is_furry_love=True` |
| Escenas bg | `_trigger_personalized_book_composition()` | Detecta `is_furry_love`, usa 2 referencias |
| Order complete | `/order-complete/<id>` | Pasa `is_furry_love` al template |
| Checkout | Checkout unificado | Mismo flujo que otros libros |
| Post-pago | `_process_personalized_book_post_payment()` | Detecta `furry_love`, busca 2 refs para escenas |

---

## 10. Puntos de Integración en illustrated_book_service.py

| Punto | Función | Qué hace para furry_love |
|-------|---------|--------------------------|
| Config | `BOOK_CONFIGS["furry_love"]` | `is_furry_love: True`, scenes, closing, covers |
| Escenas | `generate_scene_complete()` | `is_furry = book_id == 'furry_love'` → 2 refs |
| Closing | `generate_closing_page()` | Misma lógica dual referencia |
| Back cover | `generate_back_cover()` | Misma lógica dual referencia |
| Spine | `generate_cover_spread()` | Título con pet_name, color #4A1A6B |
| Title page | `generate_cover_spread()` | Título con pet_name |

---

## 11. Puntos de Integración en generation.py

```python
# 1. Reconoce el story_id
def get_personalized_book_id(story_id):
    elif 'furry_love' in story_id: return 'furry_love'

# 2. Lo incluye en la lista
def is_personalized_book(story_id):
    return story_id in [..., 'furry_love_illustrated']

# 3. Título para Lulu (con pet_name)
def get_lulu_title(book_id, child_name, lang, pet_name=''):
    if book_id == 'furry_love' and pet_name:
        # Usa pet_name en el título
```

---

## 12. Puntos de Integración en fixed_stories.py

```python
"furry_love_illustrated": {
    "title_es": "El día que {pet_name} conoció a {name}",
    "title_en": "The Day {pet_name} Met {name}",
    "age_range": "0-2",
    "book_type": "illustrated",
    "is_furry_love": True,
    "text_layout": "split",
    "content_pages": [...]  # 19 escenas con texto bilingüe
}
```

---

## 13. Datos Especiales en story_data (JSON)

Además de los campos estándar de libros personalizados, furry_love agrega:

```python
{
    "is_furry_love": True,
    "pet_name": "Julie",
    "human_preview_path": "previews/xxx/human_preview.png",  # Referencia 1
    "pet_preview_path": "previews/xxx/pet_preview.png",       # Referencia 2
    "human_desc": "...",  # Descripción textual del humano
    "pet_desc": "...",    # Descripción textual del perro
    "traits": {
        "pet_name": "Julie",
        "pet_breed": "poodle",
        "pet_color": "white",
        "pet_size": "medium",
        "human_desc": "...",
        ...
    }
}
```

---

## 14. Checklist para Replicar (Nuevo Libro con 2 Protagonistas)

### FASE 1: Archivo de Prompts
- [ ] Crear `services/personalized_books/[nuevo_id]_prompts.py`
- [ ] Definir `STYLE_BASE`
- [ ] Definir `SCENES` (lista de 19 escenas con id, text_es, text_en, prompt)
- [ ] Definir `CLOSING_SCENE`
- [ ] Definir `FRONT_COVER` y `BACK_COVER`
- [ ] Implementar `build_scene_prompt(scene, traits, style)`
- [ ] Implementar `build_*_preview_prompt()` (con y sin foto, para cada protagonista)
- [ ] Implementar `build_*_desc(traits)` para cada protagonista

### FASE 2: Formulario
- [ ] Crear `templates/personalize_[nuevo_id].html` (basarse en `personalize_furry_love.html`)
- [ ] Panel izquierdo: protagonista 1
- [ ] Panel derecho: protagonista 2
- [ ] Sección inferior: autor + dedicatoria
- [ ] Modal informativo con checkbox

### FASE 3: Registro en el Sistema
- [ ] `generation.py` → `get_personalized_book_id()`: agregar elif
- [ ] `generation.py` → `is_personalized_book()`: agregar story_id a la lista
- [ ] `generation.py` → `get_lulu_title()`: agregar título bilingüe
- [ ] `illustrated_book_service.py` → `BOOK_CONFIGS`: agregar entrada con `is_[tipo]: True`
- [ ] `illustrated_book_service.py` → importar prompts del nuevo libro
- [ ] `illustrated_book_service.py` → `ALL_PERSONALIZED_BOOK_IDS`: agregar id
- [ ] `fixed_stories.py` → agregar config con textos bilingües

### FASE 4: Rutas en app.py
- [ ] Ruta del formulario: `/personalize-[nuevo-id]`
- [ ] Preview: agregar elif en `/api/generate-baby-preview` para el nuevo story_id
- [ ] Regeneración de preview individual (si aplica)
- [ ] Generar libro: agregar detección en `/api/generate-illustrated-book`
- [ ] Order complete: pasar flag `is_[tipo]` al template
- [ ] Post-pago: detectar en `_trigger_personalized_book_composition()` para usar 2 refs
- [ ] Escenas background: detectar en `_process_personalized_book_post_payment()` para buscar 2 refs

### FASE 5: Catálogo
- [ ] Imagen de catálogo en `static/images/`
- [ ] Link en `templates/index.html`

### FASE 6: Verificación
- [ ] Flujo completo: form → preview doble → portada → texto → checkout → pago → escenas → aprobación → PDF → Lulu
- [ ] Anti-blending en escenas con contacto cercano
- [ ] Título correcto en portada, spine, y Lulu
- [ ] 26 páginas en PDF final
- [ ] Contraportada generada (dinámica) o fija según diseño

---

## 15. Costos por Generación

| Etapa | Modelo | Costo estimado |
|-------|--------|---------------|
| Preview humano | FLUX 2 Dev | ~$0.03 |
| Preview mascota | FLUX 2 Dev | ~$0.03 |
| Portada | FLUX 2 Dev | ~$0.03 |
| 19 escenas | FLUX 2 Dev × 19 | ~$0.57 |
| Closing | FLUX 2 Dev | ~$0.03 |
| Contraportada | FLUX 2 Dev | ~$0.03 |
| **Total** | | **~$0.72** |

---

## 16. Notas Importantes

1. **NUNCA subir guidance a 7.0** - Causa alucinaciones (colas rojas, elementos inventados). Si falta detalle, subir steps a 25-30.
2. **Escenas de contacto cercano** necesitan instrucciones explícitas anti-blending.
3. **El preview del humano se reutiliza como portada** (ahorro de costos).
4. **Texto usa `{name}` para humano y `{pet_name}` para mascota** en todos los templates.
5. **`text_position: "split"`** en todas las escenas = texto arriba y abajo de la imagen.
6. **Ropa del bebé**: Los prompts especifican "onesies or pajamas" para evitar desnudez.
7. **El flujo de pago y Lulu es IDÉNTICO** a los demás libros personalizados (ver `libros_personalizados.md` sección 11).

---

## 17. Integración Paddle - Cálculo de Impuestos (Feb 2026)

### Flujo de Transacción Server-Side
El checkout usa **precios dinámicos** calculados en el servidor:
1. Frontend envía `country_code` + `postal_code` + `shipping_method` a `/api/create-paddle-transaction`
2. Servidor calcula precio real: `base_price ($35) + Lulu shipping cost`
3. Servidor crea **customer** + **address** en Paddle API antes de crear la transacción
4. Transaction se crea con `customer_id` + `address_id` adjuntos → Paddle calcula IVA correcto por dirección

### Manejo de Customer Existente (409 Conflict)
- Si el email ya existe en Paddle, se recibe 409 al crear customer
- Se busca el customer existente por email via `GET /customers?email=...`
- Se crea nueva address bajo ese customer existente
- Se adjuntan ambos IDs a la transacción

### Paddle.Checkout.open() - Parámetros de Dirección
```javascript
Paddle.Checkout.open({
    transactionId: txnResult.transaction_id,
    customer: {
        email: checkoutData.email,
        address: {
            countryCode: document.getElementById('shippingCountry').value,
            postalCode: document.getElementById('shippingPostal').value
        }
    },
    settings: { displayMode: "overlay", theme: "light", locale: CFG.lang }
});
```

### Bug Corregido (Feb 2026)
- **Problema**: `checkout_unified.html` usaba `shippingZip` como ID del campo postal, pero el campo real es `shippingPostal`. Esto enviaba código postal vacío a Paddle.
- **Efecto**: Paddle rechazaba la dirección y caía a geolocalización por IP → IVA incorrecto.
- **Solución**: Corregido `shippingZip` → `shippingPostal` en 2 lugares (payload del servidor + `Paddle.Checkout.open()`).
- **Prevención**: Todos los checkouts (`checkout_unified.html`, `checkout.html`, `checkout_quick_story.html`) ahora pasan `customer.address` con `countryCode` + `postalCode` al abrir el overlay de Paddle.

### IDs de Campos por Template
| Template | Campo País | Campo Postal |
|----------|-----------|-------------|
| `checkout_unified.html` | `shippingCountry` | `shippingPostal` |
| `checkout.html` | `country_code` | `postcode` |
| `checkout_quick_story.html` | `shippingCountry` | `shippingPostal` |

### Variables de Entorno Paddle
- `PADDLE_API_KEY`: API key del servidor (nota: usar `PADDLE_SERVER_API_KEY` como workaround si hay corrupción en secrets)
- `PADDLE_CLIENT_TOKEN`: Token del cliente para el overlay
- `PADDLE_PERSONALIZED_PRODUCT_ID`: ID de producto para libros personalizados
- `PADDLE_QS_PRINT_PRODUCT_ID`: ID de producto para Quick Stories impresos
- `PADDLE_SELLER_ID`: ID del vendedor
- `PADDLE_WEBHOOK_SECRET`: Secret para validar webhooks
