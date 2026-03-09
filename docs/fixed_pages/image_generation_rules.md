# Reglas de Generación de Imágenes (FLUX)

## Problema Principal
FLUX tiende a inventar personas no autorizadas (adultos, padres, figuras borrosas) que crean problemas legales.

## Solución: Sistema Unificado de Prompts

### 1. EXTREME WIDE SHOT (Obligatorio)
```
EXTREME WIDE SHOT, camera positioned 10 meters away.
{protagonistas_desc} full body visible from head to feet.
Characters are SMALL in the frame occupying only 30% of image.
Entire environment visible.
NO CLOSE-UPS, NO SELFIES, NO PORTRAIT SHOTS.
```

### 2. Anti-Intruder Filter

#### Para 1 personaje:
```
STRICT INSTRUCTION: Illustrate ONLY what is described. ZERO creativity - follow the prompt literally. This scene contains EXACTLY ONE child. NO other humans, NO adults, NO parents, NO siblings, NO background people, NO crowds, NO bystanders. The child is COMPLETELY ALONE. Any human figure not explicitly described must NOT appear.
```

#### Para 2-3 personajes (o con mascota):
```
STRICT INSTRUCTION: Illustrate ONLY what is described. ZERO creativity - follow the prompt literally. This scene contains EXACTLY {N} characters as described. NO additional humans, NO adults, NO parents watching, NO background people, NO crowds. ONLY the described characters appear. Any figure not explicitly in the prompt must NOT appear.
```

### 3. image_represents (Obligatorio en GPT)
GPT debe generar para cada página:
```json
{
  "image_represents": {
    "key_phrase": "Frase clave del texto que la imagen debe mostrar",
    "character_actions": "Qué hacen exactamente los personajes",
    "setting_mood": "Ambiente y lugar específico"
  }
}
```

### 4. Estilo Artístico Fijo
```
Soft, painterly children's book illustration style with gentle watercolor textures. Warm, inviting color palette with soft lighting. Whimsical and magical atmosphere suitable for young children. High quality, detailed background environments.
```

## Orden del Prompt Final
1. EXTREME WIDE SHOT + camera rules
2. Descripción de personajes (PROTAGONISTAS_DESC)
3. Acción de la imagen (de image_represents)
4. Ambiente/setting
5. Estilo artístico
6. Anti-intruder filter
7. Restricciones de edad (si hay bebés)

## Negative Prompts
**NO USAR** - FLUX los ignora. Usar solo instrucciones positivas estrictas.

## Implementación
- `build_skeleton_prompt()` - Función principal
- `sanitize_scene_prompt()` - Fallback con mismas reglas
- Ambas en `services/real_stories_v2/image_service.py`
