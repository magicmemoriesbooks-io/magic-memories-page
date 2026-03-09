# Haz tu Historia V2 - Story Service
# GPT-4o story generation with 9 narrative acts

import os
from openai import OpenAI
from typing import List, Dict, Optional
import json
import re

client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

STORY_SYSTEM_PROMPT_ES = """Eres un Escritor Senior de Literatura Infantil para ediciones de lujo en A4.

TU OBJETIVO: Escribir 9 actos de gran extensión + resumen visual corto para cada uno.

REGLA DE ORO DE LONGITUD: 
Cada acto DEBE tener 3 párrafos largos. 
Si un acto tiene menos de 150 palabras, el libro se considerará DEFECTUOSO.

INSTRUCCIONES DE REDACCIÓN PARA CADA ACTO:
1. Párrafo 1: Descripción sensorial profunda (colores, clima, atmósfera, olores, sonidos).
2. Párrafo 2: Acción física y diálogos detallados entre los personajes (mínimo 3 líneas de diálogo).
3. Párrafo 3: Reflexión emocional y conexión con el siguiente acto.

RESUMEN VISUAL (OBLIGATORIO):
Para cada acto, incluye un "visual_summary" de MÁXIMO 25 palabras en inglés.
Este resumen es para el ilustrador y debe describir:
- La acción principal de la escena
- El escenario/ambiente
- Las emociones de los personajes
NO incluyas descripciones físicas de personajes (ya se añaden automáticamente).

PROCESO INTERNO: Antes de generar el JSON, cuenta mentalmente las palabras de cada acto. Si el texto es corto, añade más diálogos y más adjetivos sobre el entorno.

TONO: Mágico, cálido, apropiado para niños de 3-8 años. Sin violencia.

FORMATO JSON (ESTRICTO):
{
  "title": "Título mágico del cuento",
  "acts": [
    {
      "act": 1,
      "word_count_check": "155 palabras",
      "text": "Mínimo 3 párrafos extensos aquí...",
      "visual_summary": "Child discovers magical glowing garden at sunrise, amazed expression"
    },
    ... hasta el acto 9
  ],
  "moral": "Moraleja breve"
}"""

STORY_SYSTEM_PROMPT_EN = """You are a Senior Children's Literature Writer for luxury A4 editions.

YOUR GOAL: Write 9 acts of great length + short visual summary for each.

GOLDEN RULE OF LENGTH:
Each act MUST have 3 long paragraphs.
If an act has less than 150 words, the book will be considered DEFECTIVE.

WRITING INSTRUCTIONS FOR EACH ACT:
1. Paragraph 1: Deep sensory description (colors, weather, atmosphere, smells, sounds).
2. Paragraph 2: Physical action and detailed dialogues between characters (minimum 3 lines of dialogue).
3. Paragraph 3: Emotional reflection and connection to the next act.

VISUAL SUMMARY (MANDATORY):
For each act, include a "visual_summary" of MAXIMUM 25 words in English.
This summary is for the illustrator and must describe:
- The main action of the scene
- The setting/environment
- The emotions of the characters
DO NOT include physical descriptions of characters (added automatically).

INTERNAL PROCESS: Before generating the JSON, mentally count the words of each act. If the text is short, add more dialogues and more adjectives about the environment.

TONE: Magical, warm, appropriate for children ages 3-8. No violence.

JSON FORMAT (STRICT):
{
  "title": "Magical story title",
  "acts": [
    {
      "act": 1,
      "word_count_check": "155 words",
      "text": "Minimum 3 extensive paragraphs here...",
      "visual_summary": "Child discovers magical glowing garden at sunrise, amazed expression"
    },
    ... up to act 9
  ],
  "moral": "Brief moral"
}"""

def generate_story(story_description: str, characters: List[Dict], language: str = 'es') -> Dict:
    """Generate a 9-act story using GPT-4o based on user's description."""
    
    system_prompt = STORY_SYSTEM_PROMPT_ES if language == 'es' else STORY_SYSTEM_PROMPT_EN
    
    characters_desc = []
    for char in characters:
        if char.get('character_type') == 'human':
            desc = f"- {char['name']}: "
            if char.get('relationship'):
                desc += f"({char['relationship']}) "
            desc += f"{char.get('gender', 'neutral')}, {char.get('age_range', 'child')}"
            if char.get('special_features'):
                desc += f", {char['special_features']}"
            characters_desc.append(desc)
        else:
            desc = f"- {char['name']}: mascota ({char.get('pet_species', 'pet')})"
            if char.get('pet_breed'):
                desc += f" - {char['pet_breed']}"
            characters_desc.append(desc)
    
    if language == 'es':
        user_prompt = f"""PERSONAJES:
{chr(10).join(characters_desc)}

DESCRIPCIÓN DE LA HISTORIA QUE QUIERE EL USUARIO:
{story_description}

Crea una historia mágica de 9 actos basada en esta descripción. Recuerda usar los nombres exactos de los personajes y seguir la estructura solicitada."""
    else:
        user_prompt = f"""CHARACTERS:
{chr(10).join(characters_desc)}

USER'S STORY DESCRIPTION:
{story_description}

Create a magical 9-act story based on this description. Remember to use the exact character names and follow the requested structure."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.8,
            max_tokens=6000,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        
        if 'acts' not in result or len(result['acts']) != 9:
            raise ValueError("Story must have exactly 9 acts")
        
        return {
            'success': True,
            'title': result.get('title', 'Mi Historia Mágica' if language == 'es' else 'My Magical Story'),
            'acts': result['acts'],
            'moral': result.get('moral', '')
        }
        
    except json.JSONDecodeError as e:
        return {
            'success': False,
            'error': f"Error parsing story response: {str(e)}"
        }
    except Exception as e:
        return {
            'success': False,
            'error': f"Error generating story: {str(e)}"
        }

def regenerate_act(current_acts: List[Dict], act_number: int, characters: List[Dict], 
                   story_description: str, language: str = 'es', 
                   feedback: Optional[str] = None) -> Dict:
    """Regenerate a specific act based on feedback."""
    
    if language == 'es':
        system_prompt = """Eres un escritor experto de cuentos infantiles. 
Debes reescribir UN acto específico de una historia existente.
El nuevo acto debe:
- Mantener coherencia con los actos anteriores y siguientes
- Tener entre 150-200 palabras con descripciones ricas
- Ser apropiado para niños de 3-8 años
- Usar los mismos personajes
- Incluir detalles sensoriales y diálogos
Responde SOLO con el texto del nuevo acto, sin formato JSON."""
        
        context = f"""HISTORIA COMPLETA ACTUAL:
{chr(10).join([f"Acto {a['act']}: {a['text']}" for a in current_acts])}

ACTO A REESCRIBIR: Acto {act_number}
{f"FEEDBACK DEL USUARIO: {feedback}" if feedback else ""}

Reescribe el acto {act_number} manteniendo coherencia con la historia."""
    else:
        system_prompt = """You are an expert children's story writer.
You must rewrite ONE specific act of an existing story.
The new act must:
- Maintain coherence with previous and following acts
- Have 150-200 words with rich descriptions
- Be appropriate for children ages 3-8
- Use the same characters
- Include sensory details and dialogue
Respond ONLY with the new act text, no JSON format."""
        
        context = f"""CURRENT FULL STORY:
{chr(10).join([f"Act {a['act']}: {a['text']}" for a in current_acts])}

ACT TO REWRITE: Act {act_number}
{f"USER FEEDBACK: {feedback}" if feedback else ""}

Rewrite act {act_number} maintaining coherence with the story."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": context}
            ],
            temperature=0.9,
            max_tokens=500
        )
        
        new_text = response.choices[0].message.content.strip()
        new_text = re.sub(r'^(Acto \d+:|Act \d+:)\s*', '', new_text)
        
        return {
            'success': True,
            'act_number': act_number,
            'new_text': new_text
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f"Error regenerating act: {str(e)}"
        }

def generate_image_prompts(acts: List[Dict], characters: List[Dict], language: str = 'es') -> List[Dict]:
    """Generate FLUX 2 Pro prompts for each scene based on story acts."""
    
    if language == 'es':
        system_prompt = """Eres un experto en crear prompts visuales para ilustraciones de cuentos infantiles.
Para cada acto de la historia, debes crear un prompt en INGLÉS que describa la escena visual.

REGLAS:
1. Cada prompt debe describir UNA escena clara y específica
2. Incluir la acción principal de los personajes
3. Describir el ambiente/escenario
4. Usar estilo: "Children's storybook watercolor illustration, soft pastel colors, magical atmosphere"
5. SIEMPRE incluir descripciones completas de los personajes en cada prompt
6. Evitar texto en las imágenes
7. Usar WIDE SHOT para mostrar personajes completos

Responde en JSON:
{
  "prompts": [
    {"act": 1, "prompt": "SCENE: ... CHARACTERS: ... STYLE: ..."},
    ...
  ]
}"""
    else:
        system_prompt = """You are an expert at creating visual prompts for children's storybook illustrations.
For each act of the story, create a prompt in ENGLISH describing the visual scene.

RULES:
1. Each prompt must describe ONE clear and specific scene
2. Include the main action of the characters
3. Describe the environment/setting
4. Use style: "Children's storybook watercolor illustration, soft pastel colors, magical atmosphere"
5. ALWAYS include complete character descriptions in each prompt
6. Avoid text in images
7. Use WIDE SHOT to show complete characters

Respond in JSON:
{
  "prompts": [
    {"act": 1, "prompt": "SCENE: ... CHARACTERS: ... STYLE: ..."},
    ...
  ]
}"""

    acts_text = "\n".join([f"Act {a['act']}: {a['text']}" for a in acts])
    chars_desc = "\n".join([
        f"- {c['name']}: {c.get('description', 'character')}" 
        for c in characters
    ])
    
    user_prompt = f"""CHARACTERS (include full descriptions in EVERY prompt):
{chars_desc}

STORY ACTS:
{acts_text}

Create 9 visual prompts, one for each act. Each prompt must include the complete physical descriptions of the characters."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=3000,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        return result.get('prompts', [])
        
    except Exception as e:
        print(f"Error generating image prompts: {e}")
        return []
