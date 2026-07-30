# Magic Chef - Personalized Book Prompts
# Reference-image flow: @image1 = child character portrait (wearing chef hat + jacket)
#                       @image2 = SWEETIE_CAKE companion (rainbow cake character)
#
# Prompts contain ONLY action + setting — NO character physical descriptions.
# All appearance (face, hair, skin, outfit including hat) comes from reference images.
#
# Reference note is prepended by generate_scene_complete:
#   "@image1=child character — copy face, hair, skin, and outfit (including hat) exactly.
#    @image2=SWEETIE the rainbow cake companion — copy appearance exactly."
#
# Schema for each scene:
#   ACTION: @image1 does X. @image2 does Y.
#   SETTING: environment description WIDE VIEW.
#   ATMOSPHERE: mood.
#   {style}
#
# Rules:
#   - guidance_scale=3.5, num_inference_steps=28, aspect_ratio=3:4
#   - WIDE SHOT, characters occupy ~40% of frame, environment visible
#   - SWEETIE_HAT_DESC is always part of @image1 outfit (on head) — NOT a separate @image2
#   - SWEETIE_CAKE = @image2 fixed reference image (rainbow cake character)
#   - Scenes without @image2 in prompt text: 1,2,3,4,5,9,14,15,16,19 and CLOSING

STYLE_BASE = (
    "Disney Pixar 3D style, soft luminous pastel colors with pink and golden accents. "
    "Characters: preserve original colors from @image1. "
    "LIGHTING: Clean warm neutral cinematic studio lighting to prioritize preservation of original character colors (skin, hair). "
    "Subtle color bounce and accents only from magical kitchen elements. No dense global haze. "
    "WIDE SHOT full body from head to feet, characters occupy 40% of frame, environment visible, clean illustration only."
)

STYLE_BASE_COVER = (
    "Disney Pixar 3D style, soft luminous pastel colors with pink and golden accents. "
    "Characters: preserve original colors from @image1 and @image2. "
    "LIGHTING: Clean warm neutral cinematic studio lighting to prioritize preservation of original character colors (skin, hair). "
    "Subtle color bounce and accents only from magical kitchen elements. No dense global haze. "
    "WIDE SHOT full body from head to feet, characters occupy 65% of frame, environment visible, clean illustration only."
)

SWEETIE_HAT_DESC = (
    "a magical glowing white chef's hat with cute animated cartoon eyes and a friendly smiling mouth, "
    "golden sparkles around it"
)

SWEETIE_CAKE_INLINE = (
    "SWEETIE: an adorable round rainbow layered cake character with multiple layers of color "
    "(pink, blue, yellow, green), big cartoon eyes, a smiling mouth, adorable little arms and legs, "
    "whole round cake not a slice"
)

SWEETIE_HAT_INLINE = SWEETIE_HAT_DESC

COMPANION = {
    "name": "SWEETIE",
    "reference_image": "static/assets/sweetie_reference.png",
    "description": SWEETIE_CAKE_INLINE,
    "negative_prompt": (
        "fox tail, dragon tail, bunny tail, animal ears on human, animal features on human, "
        "robot features, mechanical parts on human, extra cake characters, multiple SWEETIE cakes"
    ),
}


MAGIC_CHEF_SCENES = [
    {
        "id": 1,
        "text_es": "Había una vez, en una cocina olvidada en el ático de una casa antigua, un gorro de chef muy especial. Brillaba con luz dorada, esperando a alguien con un corazón lleno de creatividad.",
        "text_en": "Once upon a time, in a forgotten kitchen in the attic of an old house, there was a very special chef's hat. It shimmered with golden light, waiting for someone with a heart full of creativity.",
        "prompt": "ACTION: @image1 steps through a dusty attic doorway into a forgotten magical kitchen, reaching both hands out with wonder as golden magical light pours from a glowing copper oven and swirling enchanted cookbooks. SETTING: Old wooden attic kitchen WIDE VIEW, dark beams, warm dusty golden light, old copper pots and wooden shelves, magical golden glow throughout. ATMOSPHERE: First magical discovery, warm golden glow. STRICT: Only @image1 in this scene. {style}",
        "text_position": "split"
    },
    {
        "id": 2,
        "text_es": "Cuando {name} se puso el gorro mágico, sintió un cosquilleo especial. \"¡Bienvenido al mundo de la cocina mágica!\", susurró una voz dulce desde el gorro.",
        "text_en": "When {name} put on the magic hat, {heshe} felt a special tingle. \"Welcome to the world of magical cooking!\" whispered a sweet voice from the hat.",
        "prompt": "ACTION: @image1 stands with eyes sparkling with excitement as the chef's hat glows and sparkles with golden light, the hat's animated eyes light up and its mouth moves as it whispers magically, ingredients float around @image1. SETTING: Magical kitchen transforming WIDE VIEW, floating ingredients, golden sparkles everywhere. ATMOSPHERE: Magic activation, warm golden shimmer. STRICT: Only @image1 in this scene. {style}",
        "text_position": "split"
    },
    {
        "id": 3,
        "text_es": "De pronto, la cocina comenzó a crecer y crecer. ¡Las cucharas eran tan altas como árboles! {name} se había convertido en un pequeño chef en una cocina gigante.",
        "text_en": "Suddenly, the kitchen began to grow and grow. The spoons were as tall as trees! {name} had become a tiny chef in a giant kitchen.",
        "prompt": "ACTION: @image1 looks upward in wonder at GIANT wooden spoons towering like trees, enormous whisks, massive mixing bowls taller than houses, seen from far below. SETTING: GIANT magical kitchen WIDE VIEW, warm kitchen light, sparkles everywhere, perspective from below. ATMOSPHERE: Wondrous scale, magical perspective. STRICT: Only @image1 in this scene. {style}",
        "text_position": "split"
    },
    {
        "id": 4,
        "text_es": "\"¡Tu primera misión es hacer un pastel de arcoíris!\", dijo el gorro. {name} encontró ingredientes mágicos: harina de estrellas, azúcar de nubes y huevos de sol.",
        "text_en": "\"Your first mission is to make a rainbow cake!\" said the hat. {name} found magical ingredients: star flour, cloud sugar, and sun eggs.",
        "prompt": "ACTION: @image1 holds glowing jars with sparkling star-shaped flour, fluffy white cloud sugar, and golden glowing sun eggs, the animated hat on @image1's head has its mouth moving excitedly. SETTING: Magical kitchen WIDE VIEW, floating shelves with glowing ingredient jars, rainbow light effects, sparkles. ATMOSPHERE: Excitement and magic, rainbow sparkles. STRICT: Only @image1 in this scene. {style}",
        "text_position": "split"
    },
    {
        "id": 5,
        "text_es": "{name} mezcló los ingredientes con una cuchara mágica que bailaba sola. La masa brillaba con todos los colores del arcoíris mientras se mezclaba.",
        "text_en": "{name} mixed the ingredients with a magic spoon that danced by itself. The batter glowed with all the colors of the rainbow as it mixed.",
        "prompt": "ACTION: @image1 watches in amazement as a magic wooden spoon stirs itself and dances, rainbow-colored batter swirls and sparkles in a large mixing bowl, musical notes float in the air. SETTING: Magical kitchen WIDE VIEW, large mixing bowl center, floating musical notes, sparkles. ATMOSPHERE: Musical magic, rainbow swirls. STRICT: Only @image1 in this scene. {style}",
        "text_position": "split"
    },
    {
        "id": 6,
        "text_es": "Cuando el pastel salió del horno, ¡cobró vida! \"¡Hola, chef {name}!\", dijo el pastelito saltando de alegría. \"¡Soy Dulcín, tu ayudante!\"",
        "text_en": "When the cake came out of the oven, it came alive! \"Hello, Chef {name}!\" said the little cake, jumping with joy. \"I'm Sweetie, your helper!\"",
        "prompt": "ACTION: @image1 looks with wonder and joy as @image2 emerges from the glowing oven, jumping happily with arms raised in a cheerful greeting. SETTING: Warm magical kitchen WIDE VIEW, glowing oven center, warm light, sparkles everywhere. ATMOSPHERE: Surprise and delight, warm oven glow. STRICT: @image2 is a round rainbow layered cake character with cartoon eyes and tiny arms — a pastry companion jumping out of the oven. @image1 is the single human chef child. {style}",
        "text_position": "split"
    },
    {
        "id": 7,
        "text_es": "Dulcín, el pastelito mágico, mostró a {name} el secreto de la cocina: \"Con amor y creatividad, cualquier receta puede ser extraordinaria.\"",
        "text_en": "Sweetie, the magical cake, showed {name} the secret of cooking: \"With love and creativity, any recipe can be extraordinary.\"",
        "prompt": "ACTION: @image1 kneels listening attentively as @image2 speaks with wisdom, pink and red hearts floating in the air between them. SETTING: Warm inviting kitchen WIDE VIEW, hearts floating, warm golden light. ATMOSPHERE: Love and wisdom, warm kitchen glow. STRICT: @image2 is a round rainbow layered cake character with cartoon eyes and tiny arms — a pastry companion. @image1 is the single human chef child. {style}",
        "text_position": "split"
    },
    {
        "id": 8,
        "text_es": "Juntos prepararon galletas con forma de estrella que brillaban en la oscuridad. Al morderlas, ¡hacían música!",
        "text_en": "Together they made star-shaped cookies that glowed in the dark. When you bit them, they made music!",
        "prompt": "ACTION: @image1 carefully places star-shaped cookies that sparkle with golden light onto a tray, @image2 stands on the counter giving enthusiastic instructions. SETTING: Magical kitchen WIDE VIEW, tray of glittery star-shaped cookies, sparkles everywhere. ATMOSPHERE: Creative baking fun, golden sparkles. STRICT: @image2 is a round rainbow layered cake character with cartoon eyes and tiny arms — a pastry companion standing on the counter. @image1 is the single human chef child. {style}",
        "text_position": "split"
    },
    {
        "id": 9,
        "text_es": "Después crearon un helado de nubes que nunca se derretía y cambiaba de sabor con cada lametón: fresa, chocolate, vainilla...",
        "text_en": "Then they created a cloud ice cream that never melted and changed flavor with each lick: strawberry, chocolate, vanilla...",
        "prompt": "ACTION: @image1 holds a beautiful ice cream cone with soft swirling layers of strawberry pink, chocolate brown, and vanilla cream that glows softly and never melts, an expression of peaceful delight. SETTING: Magical cooking station WIDE VIEW, soft pastel colors, golden sparkles floating. ATMOSPHERE: Peaceful sweet magic, pastel warmth. STRICT: Only @image1 in this scene. {style}",
        "text_position": "split"
    },
    {
        "id": 10,
        "text_es": "\"¡Chef {name}, hay un concurso de cocina mágica hoy!\", anunció Dulcín emocionado. \"¡Los mejores chefs del mundo mágico competirán!\"",
        "text_en": "\"Chef {name}, there's a magical cooking contest today!\" announced Sweetie excitedly. \"The best chefs from the magical world will compete!\"",
        "prompt": "ACTION: @image1 points to self with surprised delight as @image2 jumps excitedly announcing the news, a golden invitation floats in the air with sparkles. SETTING: Magical kitchen WIDE VIEW, golden invitation floating, sparkles. ATMOSPHERE: Exciting announcement, golden shimmer. STRICT: @image2 is a round rainbow layered cake character with cartoon eyes and tiny arms — a pastry companion. @image1 is the single human chef child. {style}",
        "text_position": "split"
    },
    {
        "id": 11,
        "text_es": "El concurso era en un castillo hecho completamente de caramelo y chocolate. Las torres eran bastones de caramelo gigantes.",
        "text_en": "The contest was in a castle made entirely of candy and chocolate. The towers were giant candy canes.",
        "prompt": "ACTION: @image1 walks toward the magnificent candy castle with eyes wide in wonder, @image2 floats excitedly beside, both looking up at the towering candy cane towers. SETTING: Magnificent candy castle WIDE VIEW, made of colorful candies and chocolate, candy cane towers, chocolate walls, lollipop decorations, cotton candy clouds. ATMOSPHERE: Sweet fantasy wonder, candy colors. STRICT: @image2 is a round rainbow layered cake character with cartoon eyes and tiny arms — a pastry companion floating beside @image1. @image1 is the single human chef child. {style}",
        "text_position": "split"
    },
    {
        "id": 12,
        "text_es": "Había chefs de todas partes: elfos pasteleros, hadas cocineras y hasta un oso de gomita que hacía pasteles de miel.",
        "text_en": "There were chefs from everywhere: pastry elves, fairy cooks, and even a gummy bear that made honey cakes.",
        "prompt": "ACTION: @image1 stands confidently at a cooking station, @image2 on the table beside, in background fantasy chef characters: a cute red gummy bear chef, a small fairy chef with wings, a green elf in chef jacket. SETTING: Grand contest kitchen WIDE VIEW, multiple cooking stations, warm kitchen glow. ATMOSPHERE: Exciting competition, warm kitchen glow. STRICT: @image2 is a round rainbow layered cake character with cartoon eyes and tiny arms — a pastry companion on the table. @image1 is the single human chef child. {style}",
        "text_position": "split"
    },
    {
        "id": 13,
        "text_es": "\"El reto es crear el postre más delicioso del mundo\", anunció la juez, una amable abuelita hecha de mazapán con ojos de caramelo.",
        "text_en": "\"The challenge is to create the most delicious dessert in the world,\" announced the judge, a kind grandmother made of marzipan with candy eyes.",
        "prompt": "ACTION: @image1 stands at cooking station looking attentively, @image2 beside, both facing a kind grandmother judge made entirely of marzipan with candy eyes announcing from a golden podium. SETTING: Grand contest stage WIDE VIEW, golden decorations, judging podium. ATMOSPHERE: Dramatic announcement, warm golden light. STRICT: @image2 is a round rainbow layered cake character with cartoon eyes and tiny arms — a pastry companion beside @image1. @image1 is the single human chef child. {style}",
        "text_position": "split"
    },
    {
        "id": 14,
        "text_es": "{name} cerró los ojos y pensó en lo que más amaba: su familia, sus amigos, los momentos felices. \"¡Ya sé qué haré!\", exclamó.",
        "text_en": "{name} closed {hisher} eyes and thought about what {heshe} loved most: family, friends, happy moments. \"I know what I'll make!\" {heshe} exclaimed.",
        "prompt": "ACTION: @image1 stands in a thoughtful inspired pose with eyes closed and a glowing thought bubble floating in the air containing a cozy house and loving silhouettes, sparkles and hearts surround it. SETTING: Cooking station WIDE VIEW, warm gentle lighting. ATMOSPHERE: Inspiration and love, hearts floating. STRICT: Only @image1 in this scene. {style}",
        "text_position": "split"
    },
    {
        "id": 15,
        "text_es": "Con ingredientes mágicos y todo su amor, {name} creó el \"Pastel de los Recuerdos Felices\": capas de alegría, relleno de abrazos y glaseado de sonrisas.",
        "text_en": "With magical ingredients and all {hisher} love, {name} created the \"Happy Memories Cake\": layers of joy, filling of hugs, and frosting of smiles.",
        "prompt": "ACTION: @image1 holds up proudly a beautiful whole round cake with multiple bright colorful layers, heart-shaped sparkles and golden light emanating from it. SETTING: Warm magical kitchen WIDE VIEW, wooden counters, hanging copper pots, floating spoons stirring, glowing brick oven. ATMOSPHERE: Love and creation, heart sparkles. STRICT: Only @image1 in this scene. {style}",
        "text_position": "split"
    },
    {
        "id": 16,
        "text_es": "Cuando los jueces probaron el pastel de {name}, lágrimas de felicidad rodaron por sus mejillas. Cada bocado traía un recuerdo hermoso.",
        "text_en": "When the judges tasted {name}'s cake, tears of happiness rolled down their cheeks. Each bite brought back a beautiful memory.",
        "prompt": "ACTION: @image1 stands proudly watching as judges taste the beautiful rainbow cake on the judging table, in background a fairy chef and elf chef with happy expressions and tears of joy. SETTING: Contest judging table WIDE VIEW, beautiful whole round rainbow cake. ATMOSPHERE: Emotional triumph, warm joy. STRICT: Only @image1 and background fantasy judges in this scene. {style}",
        "text_position": "split"
    },
    {
        "id": 17,
        "text_es": "\"¡El ganador es Chef {name}!\", anunció la abuelita de mazapán. \"Has descubierto el ingrediente secreto: el amor.\"",
        "text_en": "\"The winner is Chef {name}!\" announced the marzipan grandmother. \"You discovered the secret ingredient: love.\"",
        "prompt": "ACTION: @image1 stands triumphantly on the winner's podium holding the rainbow cake with a gold medal shining on their chest, @image2 jumps happily celebrating beside, confetti and streamers fall from above, magical creatures cheer in background. SETTING: Grand festive celebration hall WIDE VIEW, colorful banners, balloons, twinkling lights, decorated stage. ATMOSPHERE: Victory celebration, confetti and joy. STRICT: @image2 is a round rainbow layered cake character with cartoon eyes and tiny arms — a pastry companion celebrating beside @image1. @image1 is the single human chef child. {style}",
        "text_position": "split"
    },
    {
        "id": 18,
        "text_es": "\"Nunca olvides\", susurró el gorro mágico, \"que la verdadera magia está en cocinar con el corazón y compartir con los demás.\"",
        "text_en": "\"Never forget,\" whispered the magic hat, \"that true magic is cooking with your heart and sharing with others.\"",
        "prompt": "ACTION: @image1 listens with a grateful loving expression as golden words and hearts float in the air from the glowing hat, @image2 stands nearby watching lovingly. SETTING: Party hall WIDE VIEW, decorated with confetti and streamers. ATMOSPHERE: Warm wisdom, golden hearts and words. STRICT: @image2 is a round rainbow layered cake character with cartoon eyes and tiny arms — a pastry companion watching nearby. @image1 is the single human chef child. {style}",
        "text_position": "split"
    },
    {
        "id": 19,
        "text_es": "{name} regresó a casa con su gorro mágico y una receta especial en el corazón. Y colorín colorado, este cuento delicioso ha terminado.",
        "text_en": "{name} returned home with the magic hat and a special recipe in {hisher} heart. And {heshe} lived sweetly ever after. The End.",
        "prompt": "ACTION: @image1 walks away from camera along a winding country path toward home, back fully facing viewer, head facing forward toward the cozy cottage. No face visible — character seen from behind. SETTING: Beautiful sunset scene WIDE VIEW, peaceful meadow with wildflowers, cozy cottage with warm golden lights in the distance, sky in warm pastel pinks oranges and purples, golden sparkles and fireflies. ATMOSPHERE: Peaceful goodbye, warm sunset colors. STRICT: Only @image1 in this scene. {style}",
        "text_position": "split"
    }
]

FRONT_COVER = {
    "prompt": (
        "Centered wide full body composite illustration.\n"
        "The human child whose face, skin tone, and hair color and style are preserved exactly from @image1 stands center of magical kitchen, "
        "both hands on hips, smiling proudly and confidently.\n"
        "The rainbow cake companion from @image2 floats happily beside @image1, frosting swirling around it.\n"
        "SETTING: Magical pink kitchen WIDE VIEW, sparkles hearts and golden stars, floating magical desserts everywhere, rainbow cakes, glowing star cookies, swirling colorful ice creams, centered composition for book cover.\n"
        "ATMOSPHERE: Sweet magical invitation, pink and golden warmth.\n"
        "STRICT: Only ONE child (@image1), only ONE cake character SWEETIE (@image2). Pure illustration only. Disney Pixar 3D style.\n"
        "LIGHTING: Clean warm neutral cinematic studio lighting to prioritize preservation of original character colors (skin, hair). "
        "Subtle color bounce and accents only from magical kitchen elements. No dense global haze."
    )
}

BACK_COVER = {
    "prompt": "SETTING: Warm cozy magical kitchen WIDE VIEW, wooden shelves with colorful ingredient jars, copper pots hanging from ceiling, brick oven with warm golden glow, floating wooden spoons, magical sparkles, steam rising from pots, rainbow cakes and desserts on tables, star-shaped cookies on tray, warm sunset light through window. STRICT: NO characters, NO people, only scenery. Pure illustration only. {style}"
}


def get_outfit_desc(gender: str) -> str:
    hat = SWEETIE_HAT_DESC
    if gender == "male":
        return f"{hat} on head, white chef jacket with golden buttons over blue striped shirt, comfortable pants and sneakers"
    else:
        return f"{hat} on head, white chef jacket with golden buttons over pink striped shirt, comfortable pants and sneakers"


def get_hair_action(traits: dict) -> str:
    hair_length = traits.get('hair_length', 'medium')
    if hair_length in ('bald', 'very_little', 'very_short'):
        return "very short hair neat and clean"
    elif hair_length == 'long':
        return "long hair flowing gently"
    elif hair_length == 'short':
        return "short hair neatly styled"
    else:
        return "hair gently styled"


def build_scene_prompt(scene: dict, child_name: str, gender: str, age: int, traits: dict, has_photo: bool = False) -> str:
    """Build scene prompt using @image1/@image2 reference format.
    Prompts contain only action + setting — no character descriptions.
    Physical appearance comes entirely from reference images.
    """
    raw_prompt = scene.get('prompt', '')
    prompt = raw_prompt.replace('{style}', STYLE_BASE)
    prompt = prompt.replace('{name}', child_name)
    prompt = prompt.replace('{child_name}', child_name)
    return prompt


def build_kontext_prompt(age_display: str, gender_word: str, age_body_desc: str,
                         eye_desc: str, outfit_desc: str) -> str:
    """PASO 1 — Kontext Pro (SISTEMA 1). Official portrait prompt from photo."""
    return (
        f"Convert the {age_display} {gender_word} in @image1 into a high-quality 3D animated children's book character. "
        f"Body proportions: {age_body_desc}. Do not use toddler proportions. "
        f"Preserve the exact face, skin tone, and hair — identical likeness. "
        f"If the person in @image1 wears glasses, preserve the glasses exactly in the animated character. "
        f"Eye color: {eye_desc} — render this exact eye color. "
        f"OUTFIT: {outfit_desc}. "
        f"BACKGROUND: deep midnight blue studio background, plain — no kitchen, no scenery. "
        f"POSE: standing, full body visible from head to feet, confident joyful smile, both hands on hips."
    )


def build_avatar_prompt(age_display: str, gender_word: str) -> str:
    """PASO 2 — FLUX 2 Dev avatar (SISTEMA 1). Minimal prompt at strength=1.0 — copies everything from @image1."""
    return (
        "@image1 copy exactly.\n"
        "Standing upright, full body from head to feet, arms relaxed at sides, facing forward.\n"
        "BACKGROUND: plain deep midnight blue studio, no scenery, no props, no other characters."
    )


def build_ref_note(age_display: str, gender_word: str, cover_ref: str,
                   eye_desc: str, outfit_desc: str) -> str:
    """PASO 3 — REF_NOTE. Prompt Maestro for cover and all scenes. SISTEMA 1 and SISTEMA 2."""
    return (
        "@image1 copy exactly.\n"
        "@image2 copy exactly.\n"
        f"Copy face, skin tone, hair color and style, eye color and outfit from @image1 exactly.\n"
        f"Two distinct characters: @image1 is a fully human {gender_word}, @image2 is the cake companion."
    )


def build_nophoto_portrait_prompt(age_display: str, gender_word: str, nophoto_profile: dict,
                                   skin_tone: str, eye_desc: str, hair_line: str,
                                   haircut_block: str, outfit_desc: str, glasses_desc: str) -> str:
    """SISTEMA 2 PASO 1 — FLUX portrait from text only (no photo). Single source of truth."""
    return (
        "Disney Pixar 3D style illustration, clean full-body character reference sheet.\n\n"
        f"CHARACTER: A single {gender_word}.\n"
        f"AGE: Exactly {age_display}, {nophoto_profile['display']}.\n"
        f"PROPORTIONS: {nophoto_profile['proportions']}\n"
        f"FACE: {nophoto_profile['face']}\n"
        f"SKIN: {skin_tone}.\n"
        f"EYES: {eye_desc} — render this exact eye color.\n"
        f"HAIR: {hair_line}.\n"
        f"{haircut_block}"
        f"OUTFIT: {outfit_desc}{glasses_desc}. "
        "Standing upright, full body from head to feet, arms relaxed at sides, facing forward.\n"
        "BACKGROUND: plain deep midnight blue studio, no scenery, no props, no other characters."
    )


def get_all_scene_prompts(child_name: str, gender: str, age: int, traits: dict) -> list:
    prompts = []
    for scene in MAGIC_CHEF_SCENES:
        prompts.append(build_scene_prompt(scene, child_name, gender, age, traits))
    return prompts


def get_cover_prompts(child_name: str, gender: str, age: int, traits: dict) -> dict:
    return {
        'front': build_scene_prompt(FRONT_COVER, child_name, gender, age, traits),
        'back': build_scene_prompt(BACK_COVER, child_name, gender, age, traits)
    }
