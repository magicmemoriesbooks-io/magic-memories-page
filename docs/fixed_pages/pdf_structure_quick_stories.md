# Estructura PDF - Cuentos Rápidos Kids (Quick Stories Kids)

## Formato
- **Tamaño**: 8.5" × 8.5" (21.59 × 21.59 cm) cuadrado
- **Resolución**: 300 DPI
- **Impresión**: Lulu saddle stitch (grapado)
- **pod_package_id**: `0850X0850FCPRESS080CW444GXX` (FC Premium Saddle Stitch, 80# Coated White, Gloss)

## Estructura de Páginas

### PDF Digital (10 páginas)
| Página | Contenido |
|--------|-----------|
| 1 | Portada (cover_image con título) |
| 2 | Dedicatoria (marco decorativo dorado, texto dinámico) |
| 3-9 | 7 escenas con texto split (text_above + ilustración + text_below) |
| 10 | Contraportada fija (créditos) |

### PDF Print / Lulu (12 páginas saddle stitch)
| Página | Contenido |
|--------|-----------|
| 1 | Portada |
| 2 | Página en blanco |
| 3 | Dedicatoria |
| 4-10 | 7 escenas con texto split |
| 11 | Página en blanco |
| 12 | Contraportada fija |

### Lulu Interior PDF (10 páginas, portadas son separadas)
| Página | Contenido |
|--------|-----------|
| 1 | Página en blanco |
| 2 | Dedicatoria |
| 3-9 | 7 escenas con texto split |
| 10 | Página en blanco |

### Lulu Cover Spread (portada + contraportada)
- **Tamaño**: 17.25" × 8.75" (438.15mm × 222.25mm)
- Layout: [Bleed 0.125"][Back 8.5"][Front 8.5"][Bleed 0.125"] × [Bleed 0.125"][8.5"][Bleed 0.125"]
- Bleed solo en bordes exteriores, sin bleed entre portadas

## Página de Dedicatoria (CRÍTICO)
- **Fondo**: Color crema `#FFFBF5`
- **Marco exterior**: 3cm desde cada borde, bordes redondeados, color `#D4A574`, grosor 2pt
- **Marco interior**: 3cm + 8pt desde cada borde, color `#E8D5B7`, grosor 0.5pt
- **Título**: "Dedicatoria" / "Dedication" en `#6a3d9a`, font dropcap 22pt, centrado a 68% altura
- **Línea ornamental**: color `#D4A574`, de 30% a 70% del ancho, a 66% altura
- **Texto dinámico**:
  - Font body 16pt, color `#5a4a3a`
  - **Márgenes laterales: 3.5cm** de cada lado (word-wrap automático)
  - Posición vertical: comienza a 58% de la altura
  - Interlineado: 28pt
  - Centrado horizontalmente dentro del área de texto

## Layout de Escenas (Split Text)
- Ilustración a página completa como fondo
- **Texto superior (text_above)**: Drop cap 35pt púrpura `#6a3d9a` + cuerpo 14pt gris `#4a4a4a`
- **Texto inferior (text_below)**: Cuerpo 14pt gris `#4a4a4a` (sin drop cap)
- Fondo semi-transparente blanco 75% opacidad
- Márgenes laterales: 5% del ancho
- Ancho máximo texto: 85% del ancho

## Precios
- **$25 USD**: PDF digital + PDF imprimible con instrucciones (entrega por email)
- **$29 USD**: Libro impreso + envío incluido + PDF digital

## Implementación
- `create_kids_quick_story_pdf()` en `services/pdf_service.py`
- `_draw_kids_split_text_overlay()` en `services/pdf_service.py`
- `generate_quick_story_lulu_pdfs()` en `services/quick_stories/pdf_service.py`
