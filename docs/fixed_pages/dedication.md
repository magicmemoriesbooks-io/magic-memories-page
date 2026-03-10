# Página de Dedicatoria

## Aplica a
- **Libros Personalizados** (Dragon Garden, Magic Chef, etc.) - formato A4
- **Quick Stories Kids** (dragon_friend, etc.) - formato 8.5"×8.5" cuadrado

## Quick Stories Kids (8.5"×8.5")

### Ubicación
- **Página**: Página 3 (después de portada y blanco)

### Especificaciones del Marco
- **Fondo**: Color crema `#FFFBF5`
- **Marco exterior**: 3cm desde cada borde, esquinas redondeadas (radio 12), color `#D4A574`, grosor 2pt
- **Marco interior**: 3cm + 8pt desde cada borde, esquinas redondeadas (radio 8), color `#E8D5B7`, grosor 0.5pt

### Título
- **Texto**: "Dedicatoria" / "Dedication"
- **Color**: `#6a3d9a` (púrpura)
- **Font**: dropcap, 22pt
- **Posición**: Centrado a 68% de la altura de la página

### Línea Ornamental
- **Color**: `#D4A574` (dorado)
- **Posición**: De 30% a 70% del ancho, a 66% de la altura

### Texto Dinámico (CRÍTICO)
- **Márgenes laterales**: 3.5cm de cada lado (con word-wrap automático)
- **Font**: body, 16pt
- **Color**: `#5a4a3a` (marrón oscuro)
- **Posición vertical**: Comienza a 58% de la altura
- **Interlineado**: 28pt
- **Alineación**: Centrado horizontalmente dentro del área delimitada por los márgenes

### Implementación
```python
# Márgenes correctos para Quick Stories Kids:
ded_text_margin = 3.5 * 28.3465  # 3.5cm en puntos
max_ded_width = page_width - (ded_text_margin * 2)
# Word-wrap: dividir texto largo en líneas que quepan en max_ded_width
```

Ver función `create_kids_quick_story_pdf()` en `services/pdf_service.py`

---

## Libros Personalizados (A4)

### Ubicación
- **Página**: Página 2 (después de portadilla)

### Especificaciones de Márgenes
- **Márgenes laterales**: 4.5 cm cada lado (21.4% del ancho A4)
- **Área de texto**: 12 cm de ancho (centrado)
- **Posición vertical**: 36.7% desde arriba (frame_top=32%, frame_bottom=42%)
- **Alineación horizontal**: Centrado dentro del área de 12 cm

### Implementación
```python
# Márgenes correctos para Libros Personalizados:
left_margin = int(img_size[0] * 0.214)  # 4.5 cm
right_margin = int(img_size[0] * 0.214)  # 4.5 cm
max_width = img_size[0] - left_margin - right_margin  # ~12 cm
```

Ver función `generate_dedication_page()` en `services/illustrated_book_service.py`

---

## Contenido
Texto personalizado por el cliente. Si no proporciona texto:

### Español (por defecto)
```
Para [NOMBRE_NIÑO],
con todo nuestro amor.
```

### English (por defecto)
```
For [CHILD_NAME],
with all our love.
```

## Límites
- **Máximo**: 200 caracteres
- **Validación**: Frontend y backend

## Diseño Visual
- **Fondo (Personalized Books)**: `static/images/dedication_page_background.png`
- **Fondo (Quick Stories Kids)**: Marco dibujado por código (no imagen de fondo)
- **Color texto**: #2E1A47 (personalized) / #5a4a3a (kids quick stories)
