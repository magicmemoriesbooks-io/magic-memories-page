import os
import base64
from openai import OpenAI
from services.fixed_stories import prepare_story, get_scene_prompts, get_story_text, get_fixed_story, build_illustration_prompt, get_all_scene_keys, FIXED_STORIES

def get_openai_client():
    api_key = os.environ.get('OPENAI_API_KEY')
    if api_key:
        return OpenAI(api_key=api_key)
    else:
        return OpenAI()

def get_character_description(traits, lang='es'):
    hair_colors = {
        'black': 'negro' if lang == 'es' else 'black',
        'brown': 'castaño' if lang == 'es' else 'brown',
        'blonde': 'rubio' if lang == 'es' else 'blonde',
        'light_blonde': 'rubio claro' if lang == 'es' else 'light blonde',
        'red': 'pelirrojo' if lang == 'es' else 'red',
        'gray': 'canoso' if lang == 'es' else 'gray'
    }
    hair_types = {
        'straight': 'liso' if lang == 'es' else 'straight',
        'wavy': 'ondulado' if lang == 'es' else 'wavy',
        'curly': 'rizado' if lang == 'es' else 'curly'
    }
    eye_colors = {
        'black': 'negro' if lang == 'es' else 'black',
        'brown': 'marrón' if lang == 'es' else 'brown',
        'hazel': 'avellana' if lang == 'es' else 'hazel',
        'green': 'verde' if lang == 'es' else 'green',
        'blue': 'azul' if lang == 'es' else 'blue',
        'gray': 'gris' if lang == 'es' else 'gray'
    }
    skin_tones = {
        'very_light': 'muy clara' if lang == 'es' else 'very light',
        'light': 'clara' if lang == 'es' else 'light',
        'medium': 'media' if lang == 'es' else 'medium',
        'tan': 'bronceada' if lang == 'es' else 'tan',
        'dark': 'oscura' if lang == 'es' else 'dark'
    }
    
    hair_color = hair_colors.get(traits.get('hair_color', 'brown'), traits.get('hair_color', 'brown'))
    hair_type = hair_types.get(traits.get('hair_type', 'straight'), traits.get('hair_type', 'straight'))
    eyes = eye_colors.get(traits.get('eye_color', 'brown'), traits.get('eye_color', 'brown'))
    skin = skin_tones.get(traits.get('skin_tone', 'medium'), traits.get('skin_tone', 'medium'))
    
    if lang == 'es':
        return f"cabello {hair_color} {hair_type}, ojos {eyes}, piel {skin}"
    else:
        return f"{hair_color} {hair_type} hair, {eyes} eyes, {skin} skin"

def get_story_outfit(story_theme):
    """Return appropriate outfit based on story theme"""
    outfits = {
        'space_adventure': 'silver and purple ASTRONAUT SUIT with glowing helmet visor, space boots',
        'dragon_friend': 'medieval KNIGHT TUNIC in royal blue with golden dragon emblem, brown boots',
        'underwater_kingdom': 'shimmering MERMAID/MERMAN tail in iridescent turquoise and coral, seashell top, pearl crown and jewelry',
        'enchanted_forest': 'forest GREEN CLOAK with leaf patterns, brown leather boots, flower crown',
        'pirate_treasure': 'RED PIRATE COAT with golden buttons, striped shirt, black boots, pirate hat',
        'dinosaur_land': 'EXPLORER OUTFIT - khaki vest, safari hat, adventure boots',
        'fairy_garden': 'FAIRY DRESS/TUNIC in pastel pink and lavender with sparkly wings',
        'superhero': 'SUPERHERO CAPE in red and blue, matching mask and boots',
        'candy_kingdom': 'CANDY-THEMED outfit in pink and white stripes, lollipop accessories',
        'arctic_expedition': 'WINTER PARKA in white and blue, fuzzy boots, warm mittens',
        'magical_circus': 'CIRCUS PERFORMER outfit in red and gold, top hat, sparkly details',
        'robot_friend': 'FUTURISTIC JUMPSUIT in silver and neon blue, tech gadgets'
    }
    return outfits.get(story_theme, 'colorful ADVENTURE OUTFIT with magical details')

def summarize_scene_to_action(client, scene_text, story_theme, child_name):
    """Use GPT-4o to convert narrative text into a visual action scene description"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a children's book illustrator. Convert story text into a brief visual scene description focused on ACTION. Describe what the child is DOING, not standing or posing. Include specific objects they interact with."},
                {"role": "user", "content": f"""Story theme: {story_theme}
Child's name: {child_name}

Story text:
{scene_text[:500]}

Write ONE sentence (max 30 words) describing what {child_name} is ACTIVELY DOING in this scene. Use dynamic verbs like: reaching, climbing, hugging, flying, swimming, catching, opening, discovering. NO standing, walking, or looking."""}
            ],
            temperature=0.7,
            max_tokens=60
        )
        action = response.choices[0].message.content.strip()
        return action
    except Exception as e:
        print(f"Error summarizing scene: {e}")
        return f"{child_name} discovers something magical"

def get_story_environment(story_theme):
    """Return environment description based on story theme"""
    environments = {
        'space_adventure': 'a vast cosmic galaxy with swirling nebulas, distant planets, sparkling stars, and a glowing spaceship',
        'dragon_friend': 'a majestic medieval kingdom with towering castle, rolling green hills, and a friendly dragon flying overhead',
        'underwater_kingdom': 'a magical underwater coral reef kingdom with bioluminescent fish, sea turtles, colorful coral, treasure chests, sunlight streaming through water, and an underwater palace',
        'enchanted_forest': 'a mystical enchanted forest with giant mushrooms, glowing fireflies, talking trees, and hidden fairy homes',
        'pirate_treasure': 'a tropical pirate island with palm trees, a pirate ship, treasure chest, golden coins, and a rainbow over the ocean',
        'dinosaur_land': 'a prehistoric jungle with volcanos, giant ferns, friendly dinosaurs, and misty mountains',
        'fairy_garden': 'a magical fairy garden with giant flowers, tiny mushroom houses, butterflies, and rainbow waterfalls',
        'superhero': 'a colorful cityscape at sunset with tall buildings, flying superhero cape, and sparkly power effects',
        'candy_kingdom': 'a whimsical candy land with lollipop trees, chocolate rivers, gummy bear houses, and cotton candy clouds',
        'arctic_expedition': 'a sparkling arctic wonderland with icebergs, aurora borealis, penguins, polar bears, and snow-covered mountains',
        'magical_circus': 'a magical circus big top with colorful tents, flying acrobats, juggling clowns, and magical fireworks',
        'robot_friend': 'a futuristic city with hovering vehicles, neon lights, friendly robots, and holographic displays'
    }
    return environments.get(story_theme, 'a magical fantasy world with colorful elements and sparkling lights')

def get_detailed_character_prompt(traits, name, gender, story_theme=None):
    hair_colors_en = {
        'black': 'JET BLACK (very dark, almost blue-black)',
        'brown': 'CHESTNUT BROWN (warm medium brown)',
        'blonde': 'BRIGHT GOLDEN BLONDE (yellow-gold, NOT brown)',
        'light_blonde': 'PALE PLATINUM BLONDE / WHITE-BLONDE (very light, almost white, like Elsa from Frozen)',
        'red': 'VIBRANT RED/GINGER (orange-red)',
        'gray': 'SILVER GRAY (white-gray)'
    }
    hair_types_en = {
        'straight': 'straight and silky',
        'wavy': 'wavy and flowing',
        'curly': 'curly and bouncy'
    }
    hair_lengths_en = {
        'short': 'SHORT (above ears, pixie-style)',
        'medium': 'MEDIUM LENGTH (shoulder length)',
        'long': 'LONG (below shoulders, flowing)'
    }
    eye_colors_en = {
        'black': 'deep black/dark brown',
        'brown': 'warm chocolate brown',
        'hazel': 'warm hazel with golden flecks',
        'green': 'sparkling emerald green',
        'blue': 'bright sky blue',
        'gray': 'soft silvery gray'
    }
    skin_tones_en = {
        'very_light': 'very fair porcelain',
        'light': 'light peachy',
        'medium': 'warm olive/medium',
        'tan': 'golden tan',
        'dark': 'rich dark brown'
    }
    
    gender_desc = {
        'male': 'little boy',
        'female': 'little girl',
        'neutral': 'young child'
    }
    
    hair_color = hair_colors_en.get(traits.get('hair_color', 'brown'), 'CHESTNUT BROWN')
    hair_type = hair_types_en.get(traits.get('hair_type', 'straight'), 'straight')
    hair_length = hair_lengths_en.get(traits.get('hair_length', 'medium'), 'MEDIUM LENGTH (shoulder length)')
    eyes = eye_colors_en.get(traits.get('eye_color', 'brown'), 'brown')
    skin = skin_tones_en.get(traits.get('skin_tone', 'medium'), 'medium')
    child_type = gender_desc.get(gender, 'young child')
    outfit = get_story_outfit(story_theme) if story_theme else 'colorful ADVENTURE OUTFIT with magical details'
    
    return f"""=== MANDATORY CHARACTER REFERENCE "{name}" - {child_type.upper()} ===
!!! CRITICAL - THESE FEATURES MUST BE IDENTICAL IN EVERY SINGLE ILLUSTRATION !!!

HAIR (MOST IMPORTANT - MUST BE EXACTLY THE SAME):
- COLOR: {hair_color} hair - THIS IS THE EXACT COLOR, NEVER CHANGE IT
- STYLE: {hair_type} hair texture
- LENGTH: {hair_length} - ALWAYS show hair at this exact length
- REMINDER: If the hair is BLONDE or LIGHT BLONDE, it must be YELLOW/GOLD colored, NOT brown!

FACIAL FEATURES:
- EYES: Large expressive {eyes} eyes with visible iris color
- SKIN: {skin} skin tone with natural rosy cheeks
- FACE: Round, friendly childlike face with button nose, chubby cheeks
- AGE: MUST appear as a TODDLER/PRESCHOOLER (3-4 years old), NOT older. Small body, big head proportions typical of a 4-year-old child.

EXPRESSION & OUTFIT:
- EXPRESSION: Happy, curious, full of wonder
- CLOTHING: {outfit}

!!! ABSOLUTE REQUIREMENT - HAIR COLOR !!!
The character's {hair_color} {hair_length} {hair_type} hair MUST appear EXACTLY the same in this illustration as in all other illustrations. 
If BLONDE: Hair must be YELLOW-GOLD colored.
If LIGHT BLONDE: Hair must be PALE WHITE-BLONDE, almost white like Elsa from Frozen.
DO NOT make blonde hair look brown. DO NOT vary the hair in any way."""

def generate_story_text(order, story_template=None):
    client = get_openai_client()
    lang = order.language or 'es'
    gender = order.child_gender
    age_range = order.child_age_range
    name = order.child_name
    
    gender_info = {
        'male': {
            'es': {'pronoun': 'él', 'article': 'el', 'adj_ending': 'o'},
            'en': {'pronoun': 'he', 'article': 'the', 'adj_ending': ''}
        },
        'female': {
            'es': {'pronoun': 'ella', 'article': 'la', 'adj_ending': 'a'},
            'en': {'pronoun': 'she', 'article': 'the', 'adj_ending': ''}
        },
        'neutral': {
            'es': {'pronoun': 'elle', 'article': 'le', 'adj_ending': 'e'},
            'en': {'pronoun': 'they', 'article': 'the', 'adj_ending': ''}
        }
    }
    
    gender_data = gender_info.get(gender, gender_info['neutral'])[lang]
    
    traits = {
        'hair_color': order.hair_color,
        'hair_type': order.hair_type,
        'eye_color': order.eye_color,
        'skin_tone': order.skin_tone
    }
    character_desc = get_character_description(traits, lang)
    
    age_vocabulary = {
        '0-1': {
            'es': 'frases muy simples y repetitivas adecuadas para bebés, palabras suaves y melódicas',
            'en': 'very simple, repetitive phrases suitable for babies, soft and melodic words'
        },
        '2-4': {
            'es': 'vocabulario simple con frases cortas para niños pequeños, mucha repetición y rimas',
            'en': 'simple vocabulary with short sentences for toddlers, lots of repetition and rhymes'
        },
        '4-6': {
            'es': 'vocabulario atractivo con elementos de aventura para preescolares, algo de suspenso y emoción',
            'en': 'engaging vocabulary with adventure elements for preschoolers, some suspense and excitement'
        },
        '7-8': {
            'es': 'vocabulario más rico con trama más compleja para lectores principiantes, personajes con personalidad',
            'en': 'richer vocabulary with more complex plot for early readers, characters with personality'
        }
    }
    
    vocab_style = age_vocabulary.get(age_range, age_vocabulary['4-6'])[lang]
    
    if order.product_type == 'haz_tu_historia' and order.custom_story_description:
        story_prompt = order.custom_story_description
    else:
        story_prompt = story_template or ("Una aventura mágica" if lang == 'es' else "A magical adventure")
    
    if lang == 'es':
        system_prompt = f"""Eres un autor profesional de libros infantiles. Escribe una historia conmovedora y apropiada para la edad en español.

Requisitos clave:
- El protagonista se llama {name} (usa pronombre {gender_data['pronoun']})
- Descripción física: {character_desc}
- Lenguaje apropiado para la edad: {vocab_style}
- La historia debe dividirse en exactamente 4 secciones principales (para 4 páginas ilustradas)
- Cada sección debe tener 2-3 párrafos cortos
- Incluye una dedicatoria emotiva al final
- Hazla mágica, positiva y empoderadora para el niño

Tema de la historia: {story_prompt}

FORMATO DE SALIDA OBLIGATORIO:
SECTION 1:
[texto de la primera escena - establecer el escenario y presentar al protagonista]

SECTION 2:
[texto de la segunda escena - el desafío o aventura comienza]

SECTION 3:
[texto de la tercera escena - el momento culminante de la aventura]

SECTION 4:
[texto de la cuarta escena - resolución feliz y lección aprendida]

DEDICATION:
[texto emotivo de dedicatoria para {name}]"""
    else:
        system_prompt = f"""You are a professional children's book author. Write a heartwarming, age-appropriate story in English.

Key requirements:
- The protagonist is named {name} (use pronoun {gender_data['pronoun']})
- Physical description: {character_desc}
- Age-appropriate language: {vocab_style}
- The story must be divided into exactly 4 main sections (for 4 illustrated pages)
- Each section should have 2-3 short paragraphs
- Include an emotional dedication at the end
- Make it magical, positive, and empowering for the child

Story theme: {story_prompt}

MANDATORY OUTPUT FORMAT:
SECTION 1:
[text for first scene - set the stage and introduce the protagonist]

SECTION 2:
[text for second scene - the challenge or adventure begins]

SECTION 3:
[text for third scene - the climactic moment of the adventure]

SECTION 4:
[text for fourth scene - happy resolution and lesson learned]

DEDICATION:
[emotional dedication text for {name}]"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Write the complete story for {name} following the exact format specified."}
        ],
        temperature=0.8,
        max_tokens=2500
    )
    
    return response.choices[0].message.content

def generate_cover_illustration(name, gender, traits, story_theme, lang='es'):
    client = get_openai_client()
    
    environment = get_story_environment(story_theme)
    outfit = get_story_outfit(story_theme)
    
    hair_color = traits.get('hair_color', 'brown')
    hair_length = traits.get('hair_length', 'medium')
    hair_type = traits.get('hair_type', 'straight')
    eye_color = traits.get('eye_color', 'brown')
    skin_tone = traits.get('skin_tone', 'medium')
    
    gender_word = 'boy' if gender == 'male' else 'girl' if gender == 'female' else 'child'
    
    prompt = f"""Soft watercolor children's book cover illustration, vertical portrait orientation, upright composition.

A 4-year-old {gender_word} named {name} with {hair_color} {hair_length} {hair_type} hair, {eye_color} eyes, and {skin_tone} skin. Wearing {outfit}.

{name} stands heroically in {environment}, arms open wide with wonder and excitement. Full body visible, small child in a vast magical world.

Soft pastel colors, dreamy golden hour lighting, magical sparkles. Cinematic composition with depth - foreground details, child in middle, magical background. No text or letters."""

    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1792",
        quality="hd",
        n=1
    )
    
    return response.data[0].url

def generate_scene_illustration(name, gender, traits, scene_description, scene_number, story_theme=None):
    client = get_openai_client()
    
    character_prompt = get_detailed_character_prompt(traits, name, gender, story_theme)
    
    prompt = f"""Children's book interior illustration (page {scene_number}) in VIBRANT WATERCOLOR style.

CHARACTER DESCRIPTION (MUST MATCH EXACTLY):
{character_prompt}

SCENE TO ILLUSTRATE:
{scene_description[:500]}

ARTISTIC STYLE REQUIREMENTS:
- VIBRANT WATERCOLOR technique with soft, dreamy brushstrokes
- Rich, saturated colors (purples, pinks, blues, greens, golds)
- Soft edges and color bleeding typical of watercolor
- Magical atmosphere with subtle sparkles or light effects
- Warm, inviting lighting
- Child-friendly illustration suitable for a picture book
- The child character should be clearly visible in the scene
- NO TEXT or words in the image
- Leave space for text overlay (keep important elements away from bottom third)

The character's physical features MUST be consistent and clearly visible."""

    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1792",
        quality="standard",
        n=1
    )
    
    return response.data[0].url

def generate_character_portrait(name, gender, traits, story_theme):
    client = get_openai_client()
    
    environment = get_story_environment(story_theme)
    outfit = get_story_outfit(story_theme)
    
    hair_color = traits.get('hair_color', 'brown')
    hair_length = traits.get('hair_length', 'medium')
    hair_type = traits.get('hair_type', 'straight')
    eye_color = traits.get('eye_color', 'brown')
    skin_tone = traits.get('skin_tone', 'medium')
    
    gender_word = 'boy' if gender == 'male' else 'girl' if gender == 'female' else 'child'
    
    prompt = f"""Soft watercolor children's book illustration, vertical portrait orientation, upright composition.

A 4-year-old {gender_word} named {name} with {hair_color} {hair_length} {hair_type} hair, {eye_color} eyes, and {skin_tone} skin. Wearing {outfit}. 

{name} stands in {environment}, looking excited and ready for adventure. Full body visible from head to toe, small figure in a big magical world.

Soft pastel colors, gentle lighting, dreamy atmosphere. Simple, clear composition with the child interacting with the environment."""

    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1792",
        quality="hd",
        n=1
    )
    
    return response.data[0].url

def generate_full_story_with_illustrations(child_name, child_gender, child_age_range, traits, story_theme, lang='es'):
    client = get_openai_client()
    
    character_desc = get_character_description(traits, lang)
    
    gender_info = {
        'male': {
            'es': {'pronoun': 'él', 'article': 'el', 'adj_ending': 'o'},
            'en': {'pronoun': 'he', 'article': 'the', 'adj_ending': ''}
        },
        'female': {
            'es': {'pronoun': 'ella', 'article': 'la', 'adj_ending': 'a'},
            'en': {'pronoun': 'she', 'article': 'the', 'adj_ending': ''}
        },
        'neutral': {
            'es': {'pronoun': 'elle', 'article': 'le', 'adj_ending': 'e'},
            'en': {'pronoun': 'they', 'article': 'the', 'adj_ending': ''}
        }
    }
    
    gender_data = gender_info.get(child_gender, gender_info['neutral'])[lang]
    
    age_vocabulary = {
        '0-1': {
            'es': 'frases muy simples y repetitivas adecuadas para bebés',
            'en': 'very simple, repetitive phrases suitable for babies'
        },
        '2-4': {
            'es': 'vocabulario simple con frases cortas para niños pequeños',
            'en': 'simple vocabulary with short sentences for toddlers'
        },
        '4-6': {
            'es': 'vocabulario atractivo con elementos de aventura',
            'en': 'engaging vocabulary with adventure elements'
        },
        '7-8': {
            'es': 'vocabulario más rico con trama más compleja',
            'en': 'richer vocabulary with more complex plot'
        }
    }
    
    vocab_style = age_vocabulary.get(child_age_range, age_vocabulary['4-6'])[lang]
    
    if lang == 'es':
        system_prompt = f"""Eres un autor profesional de libros infantiles. Escribe una historia mágica en español.

REQUISITOS ESTRICTOS:
- Protagonista: {child_name} (usa pronombre {gender_data['pronoun']})
- Descripción física: {character_desc}
- Tema: {story_theme}
- Lenguaje: {vocab_style}
- Divide la historia en 4 SECCIONES (para 4 páginas de texto)
- IMPORTANTE: Cada sección debe tener EXACTAMENTE entre 90-100 palabras (ni más, ni menos)
- NO incluyas dedicatoria, el cliente la escribirá

FORMATO OBLIGATORIO:
SECTION 1:
[Texto de 90-100 palabras - introducción del personaje {child_name} y el mundo mágico]

SECTION 2:
[Texto de 90-100 palabras - aparece el desafío o aventura, {child_name} debe tomar una decisión]

SECTION 3:
[Texto de 90-100 palabras - momento culminante, {child_name} supera el desafío con valentía]

SECTION 4:
[Texto de 90-100 palabras - final feliz, lección aprendida, {child_name} regresa a casa]"""
    else:
        system_prompt = f"""You are a professional children's book author. Write a magical story in English.

STRICT REQUIREMENTS:
- Protagonist: {child_name} (use pronoun {gender_data['pronoun']})
- Physical description: {character_desc}
- Theme: {story_theme}
- Language: {vocab_style}
- Divide the story into 4 SECTIONS (for 4 text pages)
- IMPORTANT: Each section must have EXACTLY 90-100 words (no more, no less)
- DO NOT include a dedication, the client will write their own

MANDATORY FORMAT:
SECTION 1:
[90-100 words - introduce character {child_name} and the magical world]

SECTION 2:
[90-100 words - the challenge appears, {child_name} must make a decision]

SECTION 3:
[90-100 words - climactic moment, {child_name} overcomes the challenge with bravery]

SECTION 4:
[90-100 words - happy ending, lesson learned, {child_name} returns home]"""

    story_response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Write the complete story for {child_name} about {story_theme}."}
        ],
        temperature=0.8,
        max_tokens=3000
    )
    story_text = story_response.choices[0].message.content
    
    scene_descriptions = extract_scene_descriptions(story_text, lang)
    
    illustrations = []
    character_prompt = get_detailed_character_prompt(traits, child_name, child_gender, story_theme)
    
    for i, scene_desc in enumerate(scene_descriptions[:6]):
        try:
            img_url = generate_story_illustration(child_name, child_gender, traits, scene_desc, i + 1, story_theme)
            illustrations.append(img_url)
        except Exception as e:
            print(f"Error generating illustration {i+1}: {e}")
            illustrations.append(None)
    
    return {
        'story_text': story_text,
        'illustrations': illustrations
    }

def extract_scene_descriptions(story_text, lang='es'):
    """Extract scene descriptions from story text to use as illustration prompts.
    Story uses SECTION markers, we extract the actual text content to create scene-specific illustrations."""
    scenes = []
    
    markers = ['SECTION 1:', 'SECTION 2:', 'SECTION 3:', 'SECTION 4:']
    
    for i, marker in enumerate(markers):
        start = story_text.find(marker)
        if start != -1:
            if i < len(markers) - 1:
                end = story_text.find(markers[i + 1])
                if end == -1:
                    end = len(story_text)
            else:
                end = len(story_text)
            
            scene_text = story_text[start + len(marker):end].strip()
            scenes.append(scene_text[:500])
    
    if len(scenes) < 4:
        lines = story_text.split('\n')
        content_lines = [l.strip() for l in lines if l.strip() and not l.strip().startswith('SECTION')]
        chunk_size = max(1, len(content_lines) // 4)
        for i in range(4):
            start_idx = i * chunk_size
            end_idx = min(start_idx + chunk_size, len(content_lines))
            if start_idx < len(content_lines):
                chunk = ' '.join(content_lines[start_idx:end_idx])
                if len(scenes) <= i:
                    scenes.append(chunk[:500])
    
    cover_scene = f"The main character in full {get_story_environment(None)} ready for adventure"
    final_scene = "The character happy and triumphant, celebrating the end of the adventure"
    
    result = [cover_scene]
    result.extend(scenes[:4])
    result.append(final_scene)
    
    while len(result) < 6:
        result.append(f"A magical scene from the story")
    
    return result[:6]

def generate_story_illustration(name, gender, traits, scene_description, scene_number, story_theme):
    client = get_openai_client()
    
    environment = get_story_environment(story_theme)
    outfit = get_story_outfit(story_theme)
    
    hair_color = traits.get('hair_color', 'brown')
    hair_length = traits.get('hair_length', 'medium')
    hair_type = traits.get('hair_type', 'straight')
    eye_color = traits.get('eye_color', 'brown')
    skin_tone = traits.get('skin_tone', 'medium')
    
    gender_word = 'boy' if gender == 'male' else 'girl' if gender == 'female' else 'child'
    
    action_scene = summarize_scene_to_action(client, scene_description, story_theme, name)
    print(f"Scene {scene_number} action: {action_scene}")
    
    prompt = f"""Soft watercolor children's book illustration, vertical portrait orientation, upright composition.

A 4-year-old {gender_word} with {hair_color} {hair_length} {hair_type} hair, {eye_color} eyes, {skin_tone} skin. Wearing {outfit}.

ACTION: {action_scene}

Show the child ACTIVELY DOING this action in {environment}. Dynamic pose, movement, interaction with objects. Full body visible, small figure in a big magical world. NOT standing still, NOT walking, NOT looking at camera.

Soft pastel colors, gentle dreamy lighting. Wide shot with depth."""

    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1792",
        quality="hd",
        n=1
    )
    
    return response.data[0].url

def generate_fixed_story_illustration(story_key, scene_key, traits, gender):
    """Generate illustration using fixed predefined prompts"""
    client = get_openai_client()
    
    prompt = build_illustration_prompt(story_key, scene_key, traits, gender)
    
    if not prompt:
        print(f"Error: No prompt found for {story_key}/{scene_key}")
        return None
    
    print(f"Generating fixed illustration for {scene_key}")
    print(f"Prompt: {prompt[:200]}...")
    
    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1792",
        quality="hd",
        n=1
    )
    
    return response.data[0].url

def generate_grid_storyboard(traits, gender, story_key="baby_soft_world"):
    """Generate all 6 scenes in a single grid image for better character consistency"""
    import requests
    from PIL import Image
    from io import BytesIO
    import os
    
    client = get_openai_client()
    
    hair_color = traits.get('hair_color', 'brown')
    hair_length = traits.get('hair_length', 'medium')
    hair_type = traits.get('hair_type', 'straight')
    eye_color = traits.get('eye_color', 'brown')
    skin_tone = traits.get('skin_tone', 'medium')
    
    gender_word = 'boy' if gender == 'male' else 'girl'
    
    character_desc = f"a small {gender_word} with {hair_color} {hair_length} {hair_type} hair, {eye_color} eyes, {skin_tone} skin"
    
    prompt = f"""Children's storybook page divided into 6 equal panels arranged in 2 rows and 3 columns. 
Soft watercolor illustration style, luminous pastel colors, gentle light, dreamy atmosphere.

THE SAME CHARACTER appears in ALL 6 panels: {character_desc}. 
IMPORTANT: Same child in every panel, no glasses, no changes.

Panel 1 (top-left): {character_desc} looking through a window at a starry night sky, dreamy bedroom scene
Panel 2 (top-center): {character_desc} sleeping peacefully in bed, moonlight streaming in
Panel 3 (top-right): {character_desc} floating joyfully above a colorful meadow with butterflies
Panel 4 (bottom-left): {character_desc} sitting on a fluffy cloud in a pink and blue sunset sky
Panel 5 (bottom-center): {character_desc} gently descending on a cloud toward a village below
Panel 6 (bottom-right): {character_desc} walking happily in a sunny park looking up at the sky

All panels: same child, same features, watercolor storybook style, soft pastel colors, no text."""

    print(f"Generating 6-panel grid storyboard...")
    print(f"Character: {character_desc}")
    
    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1792x1024",
        quality="hd",
        n=1
    )
    
    image_url = response.data[0].url
    print(f"Grid image generated: {image_url[:50]}...")
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    img_response = requests.get(image_url, timeout=60, headers=headers)
    img = Image.open(BytesIO(img_response.content))
    
    width, height = img.size
    panel_width = width // 3
    panel_height = height // 2
    
    os.makedirs('generated/panels', exist_ok=True)
    
    panels = []
    panel_positions = [
        (0, 0), (1, 0), (2, 0),
        (0, 1), (1, 1), (2, 1)
    ]
    
    for i, (col, row) in enumerate(panel_positions):
        left = col * panel_width
        top = row * panel_height
        right = left + panel_width
        bottom = top + panel_height
        
        panel = img.crop((left, top, right, bottom))
        
        panel_path = f'generated/panels/panel_{i+1}.png'
        panel.save(panel_path, 'PNG', quality=95)
        panels.append(panel_path)
        print(f"Saved panel {i+1}: {panel_path}")
    
    return panels, image_url

def generate_fixed_story_with_illustrations(child_name, child_gender, traits, story_key, lang='es'):
    """Generate a complete story using fixed text and fixed illustration prompts"""
    client = get_openai_client()
    
    story_data = get_fixed_story(story_key, child_name, child_gender)
    
    if not story_data:
        print(f"Error: Fixed story '{story_key}' not found")
        return None
    
    story_text = f"SECTION 1:\n{story_data['pages']['page_1']}\n\n"
    story_text += f"SECTION 2:\n{story_data['pages']['page_2']}\n\n"
    story_text += f"SECTION 3:\n{story_data['pages']['page_3']}\n\n"
    story_text += f"SECTION 4:\n{story_data['pages']['page_4']}"
    
    illustrations = []
    scene_keys = get_all_scene_keys()
    
    for scene_key in scene_keys:
        print(f"Generating illustration: {scene_key}")
        image_url = generate_fixed_story_illustration(story_key, scene_key, traits, child_gender)
        if image_url:
            illustrations.append(image_url)
        else:
            illustrations.append(None)
    
    return {
        'title': story_data['title'],
        'story_text': story_text,
        'illustrations': illustrations,
        'age_range': story_data['age_range']
    }

def generate_preview(child_name, child_gender, child_age_range, hair_color, hair_type, eye_color, skin_tone, story_template, lang='es', hair_length='medium'):
    client = get_openai_client()
    
    traits = {
        'hair_color': hair_color,
        'hair_type': hair_type,
        'hair_length': hair_length,
        'eye_color': eye_color,
        'skin_tone': skin_tone
    }
    
    character_desc = get_character_description(traits, lang)
    
    gender_info = {
        'male': {'es': 'él', 'en': 'he'},
        'female': {'es': 'ella', 'en': 'she'},
        'neutral': {'es': 'elle', 'en': 'they'}
    }
    pronoun = gender_info.get(child_gender, gender_info['neutral'])[lang]
    
    if lang == 'es':
        text_prompt = f"""Escribe el PRIMER PÁRRAFO de un cuento infantil mágico sobre {child_name}.
Protagonista: {child_name} ({pronoun}), con {character_desc}.
Tema: {story_template}
Escribe solo 3-4 oraciones introductorias que capturen la magia del cuento. Estilo apropiado para niños de {child_age_range} años."""
    else:
        text_prompt = f"""Write the FIRST PARAGRAPH of a magical children's story about {child_name}.
Protagonist: {child_name} ({pronoun}), with {character_desc}.
Theme: {story_template}
Write only 3-4 introductory sentences that capture the magic of the story. Style appropriate for children aged {child_age_range} years."""
    
    text_response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": text_prompt}
        ],
        temperature=0.8,
        max_tokens=300
    )
    preview_text = text_response.choices[0].message.content
    
    image_url = generate_cover_illustration(child_name, child_gender, traits, story_template, lang)
    
    return {
        'text': preview_text,
        'image_url': image_url
    }
