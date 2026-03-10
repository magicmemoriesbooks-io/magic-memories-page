# Página de Créditos

## Ubicación
- **Página**: Última página interior (antes de contraportada)
- **Aplica a**: Todos los tipos de libros

## Contenido

### Español
```
Este libro fue creado especialmente para
[NOMBRE_NIÑO]

Magic Memories Books

Texto e ilustraciones generados con IA
© 2026 Magic Memories Books
Todos los derechos reservados.

www.magicmemoriesbooks.com
```

### English
```
This book was specially created for
[CHILD_NAME]

Magic Memories Books

Text and illustrations generated with AI
© 2026 Magic Memories Books
All rights reserved.

www.magicmemoriesbooks.com
```

## Diseño Visual
- **Fondo fijo**: `static/images/credits_page_background.png`
- **Marco**: Sencillo, líneas doradas con estrellas en esquinas
- **Tipografía**: 
  - Nombre del niño: Bold, color marrón (#8B4513)
  - Título Magic Memories: Bold grande
  - Texto regular: Normal
- **Alineación**: Centrado

## Imagen de Referencia
![Fondo de créditos](credits_background.png)

## Texto Dinámico
El nombre del niño se añade dinámicamente al generar el PDF.

## Implementación
Ver función `generate_credits_page()` en `services/illustrated_book_service.py`.
