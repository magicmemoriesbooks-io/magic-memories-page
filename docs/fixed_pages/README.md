# Páginas Fijas - Magic Memories Books

Esta carpeta contiene la documentación de todas las páginas y elementos fijos para todos los tipos de libros.

## Estructura de Archivos

### Documentación
| Archivo | Descripción |
|---------|-------------|
| `title_page.md` | Portadilla (fondo fijo + título/frase dinámico) |
| `dedication.md` | Página de dedicatoria |
| `credits.md` | Página de créditos |
| `back_cover_quick_stories.md` | Contraportada para Cuentos Rápidos |
| `back_cover_books.md` | Contraportada para Libros Personalizados e Haz tu Historia |
| `pdf_structure_quick_stories.md` | Estructura PDF de Cuentos Rápidos |
| `pdf_structure_books.md` | Estructura PDF de Libros Personalizados e Haz tu Historia |
| `image_generation_rules.md` | Reglas FLUX anti-intrusos |
| `lulu_specifications.md` | Especificaciones técnicas Lulu |

### Imágenes Fijas
| Archivo | Uso |
|---------|-----|
| `dedication_frame.png` | Marco de dedicatoria con título "Dedicatoria" |
| `credits_background.png` | Fondo de página de créditos |
| `title_page_background.png` | Fondo de portadilla |
| `magic_memories_logo.png` | Logo para contraportadas |

## Tipos de Libros

1. **Quick Stories (Cuentos Rápidos)**: Solo digital, formato cuadrado 18x18cm
2. **Personalized Books (Libros Personalizados)**: Digital + Impreso Lulu, A4 vertical
3. **Haz tu Historia (Make Your Story)**: Digital + Impreso Lulu, A4 vertical

## Páginas Fijas vs Dinámicas

| Página | Fondo | Texto |
|--------|-------|-------|
| Portadilla | FIJO | Dinámico (título + frase) |
| Dedicatoria | FIJO (con título) | Dinámico (texto usuario) |
| Créditos | FIJO | Dinámico (nombre niño) |
| Contraportada | DINÁMICO (FLUX) | Logo fijo |

## Nota Importante

Libros Personalizados e Haz tu Historia comparten el mismo formato de PDF ya que ambos se imprimen en Lulu con especificaciones A4.
