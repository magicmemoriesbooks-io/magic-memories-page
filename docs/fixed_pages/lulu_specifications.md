# Especificaciones Lulu - Impresión A4 Hardcover

## Producto
- **Tipo**: Case Laminate Hardcover
- **Tamaño**: A4 (210 x 297 mm)
- **Orientación**: Vertical (Portrait)
- **Color**: Full color interior y exterior
- **Papel interior**: Premium color (80-100 gsm)

## Archivos Requeridos

### 1. Interior PDF
- **Nombre**: `interior.pdf`
- **Tamaño página**: 216 x 303 mm (incluye sangrado 3mm)
- **Área segura**: 210 x 297 mm
- **Resolución**: 300 DPI mínimo
- **Número de páginas**: Debe ser par (24 páginas)
- **Espacio de color**: RGB o CMYK

### 2. Cover PDF (Spread)
- **Nombre**: `cover.pdf`
- **Contenido**: Contraportada + Lomo + Portada (en ese orden, izq a der)
- **Alto**: 303 mm (incluye sangrado)
- **Ancho**: Calculado según fórmula

### Cálculo del Lomo
```
Lomo (mm) = (Número de páginas × 0.0572) + 1.52
```

Ejemplos:
- 24 páginas: (24 × 0.0572) + 1.52 = 2.89 mm
- 32 páginas: (32 × 0.0572) + 1.52 = 3.35 mm

### Ancho Total del Cover
```
Ancho = Contraportada (216mm) + Lomo + Portada (216mm)
```

Para 24 páginas: 216 + 2.89 + 216 = 434.89 mm ≈ 435 mm

## Áreas de Seguridad

### Interior
- **Sangrado**: 3mm en todos los lados (se corta)
- **Margen seguro**: 15mm del borde final
- **Margen de encuadernación**: 20mm adicional en el lado del lomo

### Cubierta
- **Sangrado**: 3mm en todos los lados exteriores
- **Zona segura del lomo**: No poner texto crítico
- **Margen de doblado**: 5mm desde el borde del lomo

## Resolución Mínima
- **Interior**: 300 DPI
- **Cubierta**: 300 DPI
- **Píxeles interior A4**: 2551 x 3579 px (con sangrado)
- **Píxeles cubierta**: Variable según lomo

## Colores
- **Espacio**: sRGB recomendado (Lulu convierte automáticamente)
- **Negro puro**: Usar RGB(0,0,0) no CMYK
- **Blanco**: RGB(255,255,255)

## Restricciones de Contenido
- Sin contenido en zona de sangrado que no pueda cortarse
- Texto a 15mm mínimo del borde
- Imágenes pueden extenderse hasta el sangrado

## API Lulu
- **Endpoint**: `https://api.lulu.com/print-jobs/`
- **Autenticación**: OAuth2 Bearer Token
- **Sandbox**: `https://api.sandbox.lulu.com/`
