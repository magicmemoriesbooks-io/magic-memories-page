# Comparación: Dragon Garden vs Magic Chef

## Resumen General

| Aspecto | Dragon Garden | Magic Chef |
|---------|---------------|------------|
| Tema | Aventura mágica en jardín encantado | Aventura culinaria en cocina mágica |
| Compañero | Spark (dragón bebé) | Sweetie/Dulcín (pastel animado) + Gorro parlante |
| Escenarios | Jardín, bosque, cielo, cueva de cristales | Cocina gigante, ingredientes mágicos, dulces |
| Paleta de colores | Verdes, dorados, arcoíris, naturaleza | Rosas, dorados, colores pastel, dulces |
| Mensaje | Amistad, magia de la naturaleza | Creatividad, amor por cocinar |

---

## Estilo Visual

### Dragon Garden
```python
STYLE_BASE = "children's storybook watercolor illustration, soft luminous pastel colors, gentle warm lighting, dreamy magical atmosphere, full body characters shown completely from head to feet, clean illustration only"
```

### Magic Chef
```python
CHEF_STYLE_BASE = "children's storybook watercolor illustration, soft luminous pastel colors, gentle warm lighting, dreamy magical atmosphere, full body characters shown completely from head to feet, clean illustration only"
```

**Nota**: Usan el mismo estilo base para consistencia.

---

## Compañero Principal

### Dragon Garden - Spark
```python
SPARK_DESC = "Spark the small cute baby dragon with shimmering emerald green scales, big round golden eyes, tiny translucent wings, chubby round body, and a friendly smile"
```

### Magic Chef - Sweetie/Dulcín
```python
SWEETIE_DESC = "SWEETIE: an adorable round rainbow layered cake character with multiple layers of color (pink, blue, yellow, and green), big cartoon eyes, a smiling talking mouth, and adorable little arms and legs"
```

### Magic Chef - Gorro Mágico
El gorro del chef también es un personaje:
```python
"a white chef's hat with cute cartoon eyes and animated smiling mouth that appears to be talking sweetly"
```

---

## Estructura de Escenas (19 escenas cada uno)

### Dragon Garden
1. Puerta mágica en roble antiguo
2. Encuentra a Spark el dragón
3. Vuelan juntos sobre nubes
4. Cruzan un arcoíris brillante
5. Flores gigantes con mariposas
6. Animales mágicos del bosque
7. Cueva de cristales brillantes
8. Río de estrellas caídas
9. Claro de hadas danzantes
10. Árbol de deseos
11. Jardín de luciérnagas
12. Cascada mágica
13. Flores que cantan
14. Puente de cristal
15. Valle de los sueños
16. Puesta de sol mágica
17. Estrellas despiertan
18. Despedida con Spark
19. Regreso a casa con recuerdos

### Magic Chef
1. Ático con gorro mágico brillante
2. Se pone el gorro, voz mágica
3. Cocina crece a tamaño gigante
4. Ingredientes mágicos (harina de estrellas)
5. Cuchara que baila sola
6. Nace Sweetie el pastelito
7. Lección: amor y creatividad
8. Galletas musicales de estrella
9. Cocina de hielo (helados mágicos)
10. Pizza voladora
11. Espaguetis que bailan
12. Sopa de arcoíris
13. Vegetales felices
14. Pan que canta
15. Chocolates saltarines
16. Gran banquete mágico
17. Invitados fantásticos
18. Despedida de Sweetie
19. Regreso con recetas mágicas

---

## Vestimenta del Protagonista

### Dragon Garden
```python
# Vestimenta consistente en todas las escenas
"outfit_desc": "a comfortable adventure outfit, light jacket"
# No cambia de ropa durante la historia
```

### Magic Chef
```python
# Escena 1: Ropa casual
"a cozy yellow t-shirt with jeans and sneakers"

# Escenas 2-19: Uniforme de chef
"a white chef's hat with cute cartoon eyes and smile, and white chef jacket with golden buttons"

# Variaciones menores:
"white chef jacket with flour spots" (escena 5)
```

---

## Prompts de Portada

### Dragon Garden
```python
COVER_TEMPLATE = "A beautiful young human {gender_child} with {hair_desc} and {skin_tone} skin wearing {outfit_desc} rides on {spark_desc}'s back, both flying joyfully over a magnificent magical garden filled with giant colorful flowers, sparkling waterfalls, and floating butterflies. Rainbow arches across a golden sunset sky. Magical sparkles trail behind them."
```

### Magic Chef
```python
MAGIC_CHEF_COVER = "A magical pink kitchen background with sparkles, hearts, and golden stars. Floating magical desserts everywhere: rainbow cakes, glowing star cookies, swirling colorful ice creams. SWEETIE: a COMPLETE adorable round rainbow layered cake character floats happily. In the center, {char_base} wearing a glowing white chef's hat with cute cartoon eyes and smile, and an elegant white chef jacket with golden buttons."
```

---

## Prompts de Contraportada

### Dragon Garden
```python
BACK_COVER = "Enchanted magical garden scene: ancient oak tree with glowing door, giant colorful flowers, magical butterflies, sparkles in the air. A small silhouette of baby dragon flying toward the sunset. Dreamy, peaceful atmosphere."
```

### Magic Chef
```python
MAGIC_CHEF_BACK_COVER = "Magical candy castle scene with candy cane towers, chocolate walls, lollipop trees, cotton candy clouds, and a path made of cookies leading to the entrance. Warm sunset colors, sparkles everywhere, dreamy sweet atmosphere."
```

---

## Diferencias Técnicas

| Aspecto | Dragon Garden | Magic Chef |
|---------|---------------|------------|
| book_id | `dragon_garden` | `magic_chef` |
| Escenas | DRAGON_GARDEN_SCENES | MAGIC_CHEF_SCENES |
| Cierre | DRAGON_GARDEN_CLOSING | MAGIC_CHEF_CLOSING |
| Portada | COVER_TEMPLATE | MAGIC_CHEF_COVER |
| Contraportada | BACK_COVER | MAGIC_CHEF_BACK_COVER |
| Cambio de ropa | No | Sí (escena 1 diferente) |

---

## Flujo Compartido

Ambos libros usan exactamente el mismo:
- Sistema de regeneración (2 por página)
- Estructura de PDF (26 páginas)
- Integración Paddle (mismos precios)
- Integración Lulu (mismo formato A4 hardcover)
- Modal de advertencia
- Posición del autor (3cm del borde)

---

## Archivos de Referencia

- Dragon Garden: `services/illustrated_book_service.py` líneas 77-230
- Magic Chef: `services/illustrated_book_service.py` líneas 233-400
- Función load_book_config(): línea 500+
