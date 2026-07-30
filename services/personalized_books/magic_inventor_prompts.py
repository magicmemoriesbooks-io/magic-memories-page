# Magic Inventor Workshop - Personalized Book Prompts
# Reference-image flow: @image1 = child character portrait (wearing inventor outfit)
#                       @image2 = BOLT companion (copper robot)
#
# Prompts contain ONLY action + setting — NO character physical descriptions.
# All appearance (face, hair, skin, outfit) comes from reference images.
#
# Reference note is prepended by generate_scene_complete:
#   "@image1 copy exactly.
#    @image2 = BOLT, robot companion — copy @image2 exactly."
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
#   - Scenes without @image2: 1, 2, 19 and CLOSING

STYLE_BASE = (
    "Disney Pixar 3D style. "
    "Environment: soft luminous pastel colors with copper and golden accents. "
    "Characters: preserve original colors from @image1. "
    "LIGHTING: Clean warm neutral cinematic studio lighting to prioritize preservation of original character colors (skin, hair). "
    "Subtle color bounce and accents only from magical elements. No dense global haze. "
    "WIDE SHOT full body from head to feet, characters occupy 40% of frame, "
    "environment visible, clean illustration only."
)

STYLE_BASE_COVER = (
    "Disney Pixar 3D style. "
    "Environment: soft luminous pastel colors with copper and golden accents, golden light in the environment only. "
    "Characters: preserve original colors from @image1 and @image2. "
    "LIGHTING: Clean warm neutral cinematic studio lighting to prioritize preservation of original character colors (skin, hair, metal). "
    "Subtle color bounce and accents only from magical elements. No dense global haze. "
    "WIDE SHOT full body from head to feet, characters occupy 65% of frame, "
    "environment visible, clean illustration only."
)

BOLT_INLINE = (
    "BOLT: a small round copper robot with spherical body, big glowing blue eyes, two short metallic arms, "
    "two stumpy legs, small antenna on top with blinking light, copper patina finish"
)

COMPANION = {
    "name": "BOLT",
    "reference_image": "static/assets/bolt_reference.png",
    "description": BOLT_INLINE,
    "negative_prompt": (
        "fox tail, bunny tail, dragon tail, animal ears on human, animal features on human, "
        "multiple robots, extra robots, robot features on human"
    ),
}


MAGIC_INVENTOR_SCENES = [
    {
        "id": 1,
        "text_es": "En lo más alto de una vieja casona, {name} descubrió una puerta secreta detrás de una estantería polvorienta. Al abrirla, una luz dorada y chispas de colores salieron desde el interior.",
        "text_en": "At the very top of an old manor house, {name} discovered a secret door behind a dusty bookshelf. When they opened it, golden light and colorful sparks burst from inside.",
        "prompt": "ACTION: @image1 pushes open a glowing secret door behind a tilted dusty bookshelf, golden light illuminating @image1's face, colorful sparks bursting from the doorway. SETTING: Dusty attic WIDE VIEW, wooden beams, cobwebs, mysterious door behind tilted bookshelf glowing golden, old books on shelves. ATMOSPHERE: Discovery, ambient glow, magical particles. STRICT: Only @image1 in this scene. {style}",
        "text_position": "split"
    },
    {
        "id": 2,
        "text_es": "¡Era un taller mágico lleno de inventos asombrosos! Engranajes dorados flotaban por el aire, tubos de cristal brillaban con líquidos de colores y herramientas mágicas se movían solas.",
        "text_en": "It was a magical workshop full of amazing inventions! Golden gears floated in the air, crystal tubes glowed with colorful liquids, and magical tools moved on their own.",
        "prompt": "ACTION: @image1 stands at the workshop entrance with mouth open in amazement, gazing at floating golden gears spinning all around. SETTING: Magnificent inventor workshop WIDE VIEW, floating golden gears spinning, crystal tubes with colorful glowing liquids, workbenches with blueprints and gadgets. ATMOSPHERE: Copper and golden tones, sparkling magical atmosphere. STRICT: Only @image1 in this scene. {style}",
        "text_position": "split"
    },
    {
        "id": 3,
        "text_es": "De pronto, una pequeña esfera de cobre rodó hasta los pies de {name}. Se abrió y de ella surgió un simpático robot con ojos azules brillantes. \"¡Hola! Soy BOLT\", dijo con voz metálica y alegre.",
        "text_en": "Suddenly, a small copper sphere rolled to {name}'s feet. It opened up and out came a friendly little robot with bright blue eyes. \"Hello! I'm BOLT,\" it said with a cheerful metallic voice.",
        "prompt": "ACTION: @image1 looks down with joyful surprise as a copper sphere opens like flower petals at @image1's feet, @image2 emerges from the sphere with both arms raised in a cheerful greeting, blue eyes glowing. SETTING: Workshop floor WIDE VIEW, floating gears in background, colorful sparks in the air. ATMOSPHERE: Surprise and first meeting, blue and copper sparks. {style}",
        "text_position": "split"
    },
    {
        "id": 4,
        "text_es": "BOLT le mostró a {name} el Mapa de los Inventos Perdidos, un pergamino brillante donde aparecían máquinas fantásticas esperando ser reconstruidas por un inventor valiente.",
        "text_en": "BOLT showed {name} the Map of Lost Inventions, a glowing scroll where fantastic machines appeared, waiting to be rebuilt by a brave inventor.",
        "prompt": "ACTION: @image1 leans over a workshop table examining a glowing golden scroll with animated blueprints, @image2 stands on the table pointing at the drawings with one arm. SETTING: Workshop table WIDE VIEW, large golden scroll unrolled showing fantastical machine drawings, amber glow from scroll. ATMOSPHERE: Excitement, magical amber shimmer. {style}",
        "text_position": "split"
    },
    {
        "id": 5,
        "text_es": "\"¡Nuestro primer invento será una Bicicleta Voladora!\", exclamó BOLT. {name} encontró ruedas de cristal, pedales de arcoíris y un manillar que brillaba como una estrella.",
        "text_en": "\"Our first invention will be a Flying Bicycle!\" exclaimed BOLT. {name} found crystal wheels, rainbow pedals, and handlebars that glowed like a star.",
        "prompt": "ACTION: @image1 holds up a sparkling crystal wheel to the light with excitement, @image2 on the workbench sorts through magical bicycle parts. SETTING: Workshop corner WIDE VIEW, scattered magical bicycle parts: crystal wheels, rainbow pedals, star handlebars, copper wings, blueprints on wall. ATMOSPHERE: Creative energy, sparkles. {style}",
        "text_position": "split"
    },
    {
        "id": 6,
        "text_es": "{name} y BOLT construyeron juntos la Bicicleta Voladora. Cada pieza encajaba con un destello de luz y el taller se llenó de música mágica.",
        "text_en": "{name} and BOLT built the Flying Bicycle together. Each piece clicked into place with a flash of light, and the workshop filled with magical music.",
        "prompt": "ACTION: @image1 uses a glowing wrench to attach a crystal wheel to a half-built magical bicycle, golden sparks flying, @image2 nearby passes gears with both small arms, musical notes float in the air. SETTING: Workshop center WIDE VIEW, half-built magical bicycle, golden sparks, floating musical notes. ATMOSPHERE: Joy of creation, magical atmosphere, teamwork. {style}",
        "text_position": "split"
    },
    {
        "id": 7,
        "text_es": "¡La Bicicleta Voladora cobró vida! {name} pedaleó hacia el cielo del taller, que se abrió como un libro mágico revelando un cielo lleno de estrellas y nubes de algodón.",
        "text_en": "The Flying Bicycle came alive! {name} pedaled into the workshop sky, which opened like a magical book revealing a sky full of stars and cotton candy clouds.",
        "prompt": "ACTION: @image1 rides the completed flying bicycle pedaling joyfully, soaring upward through the workshop ceiling into a starry sky, @image2 sits in the bicycle basket with arms raised and excited, copper wings extended on the bicycle, golden spark trail behind. SETTING: Workshop ceiling opening WIDE VIEW, starry sky with cotton candy clouds in pink and blue. ATMOSPHERE: Freedom, magical flight, golden sparkles. {style}",
        "text_position": "split"
    },
    {
        "id": 8,
        "text_es": "Volaron sobre un océano de nubes hasta llegar a la Isla de las Ideas, un lugar flotante donde las ideas se convertían en burbujas brillantes de todos los colores.",
        "text_en": "They flew over an ocean of clouds to reach the Island of Ideas, a floating place where ideas turned into brilliant bubbles of every color.",
        "prompt": "ACTION: @image1 stands on a floating island reaching toward a giant pink bubble containing a tiny glowing invention, @image2 beside @image1 points at another colorful bubble. SETTING: Floating island in sky WIDE VIEW, colorful clouds, giant colorful idea-bubbles floating everywhere, rainbow bridges. ATMOSPHERE: Ethereal wonder, soft pastel colors, dreamy. {style}",
        "text_position": "split"
    },
    {
        "id": 9,
        "text_es": "En la Isla encontraron la Caja Musical Infinita, un invento que creaba melodías que podían hacer crecer flores y pintar arcoíris en el cielo.",
        "text_en": "On the Island they found the Infinite Music Box, an invention that created melodies that could grow flowers and paint rainbows in the sky.",
        "prompt": "ACTION: @image1 kneels beside a golden music box touching a key gently with one hand, @image2 on the other side sways to the music with tiny arms waving, rainbow musical notes spiral upward, flowers grow around the base. SETTING: Floating island clearing WIDE VIEW, ornate golden music box, rainbow light notes, flowers growing, small rainbow above. ATMOSPHERE: Musical serenity, sparkles. {style}",
        "text_position": "split"
    },
    {
        "id": 10,
        "text_es": "\"¡Necesitamos reparar el Telescopio de Arcoíris!\", dijo BOLT. Era un telescopio mágico que permitía ver los sueños de cualquier persona en cualquier lugar del mundo.",
        "text_en": "\"We need to fix the Rainbow Telescope!\" said BOLT. It was a magical telescope that let you see anyone's dreams anywhere in the world.",
        "prompt": "ACTION: @image1 examines a large broken copper telescope with crystal prisms, @image2 holds a broken crystal lens up to the light with both arms. SETTING: Workshop platform WIDE VIEW, scattered lenses and gears, faint rainbow light from telescope cracks, starry backdrop. ATMOSPHERE: Problem-solving, soft rainbow refractions, stars. {style}",
        "text_position": "split"
    },
    {
        "id": 11,
        "text_es": "{name} descubrió que la pieza que faltaba era un cristal con forma de corazón. Lo encontraron escondido dentro de un reloj antiguo que marcaba la hora de los sueños.",
        "text_en": "{name} discovered that the missing piece was a heart-shaped crystal. They found it hidden inside an ancient clock that marked the hour of dreams.",
        "prompt": "ACTION: @image1 reaches into an ancient grandfather clock to carefully retrieve a glowing heart-shaped crystal, @image2 beside @image1 shines blue light from eyes to illuminate the way. SETTING: Workshop alcove WIDE VIEW, ancient grandfather clock with celestial decorations, moon and star motifs, clock door open showing crystal inside. ATMOSPHERE: Dreamy purple and gold, golden sparkles. {style}",
        "text_position": "split"
    },
    {
        "id": 12,
        "text_es": "Con el cristal corazón en su lugar, el Telescopio de Arcoíris mostró los sueños más hermosos: ciudades flotantes, jardines submarinos y montañas de caramelo.",
        "text_en": "With the heart crystal in place, the Rainbow Telescope showed the most beautiful dreams: floating cities, underwater gardens, and candy mountains.",
        "prompt": "ACTION: @image1 looks through the repaired rainbow telescope with an amazed expression, holographic dream projections float above: floating cities, underwater gardens, candy mountains. @image2 watches the projections with arms raised. SETTING: Workshop observatory WIDE VIEW, telescope projecting rainbow holographic display, swirling dream images. ATMOSPHERE: Rainbow wonder, magical projections. {style}",
        "text_position": "split"
    },
    {
        "id": 13,
        "text_es": "BOLT llevó a {name} al Jardín de los Engranajes, donde flores mecánicas de cobre y cristal abrían y cerraban sus pétalos con suaves chasquidos musicales.",
        "text_en": "BOLT led {name} to the Garden of Gears, where mechanical flowers made of copper and crystal opened and closed their petals with soft musical clicks.",
        "prompt": "ACTION: @image1 walks along a cobblestone path touching a large copper mechanical flower that opens at the touch, @image2 walks beside @image1 with a mechanical butterfly perched on its antenna. SETTING: Enchanting garden WIDE VIEW, mechanical copper flowers with crystal stems opening and closing, mechanical butterflies, cobblestone path, copper archways. ATMOSPHERE: Whimsical beauty, soft lighting, sparkles. {style}",
        "text_position": "split"
    },
    {
        "id": 14,
        "text_es": "En el centro del Jardín había un árbol mecánico cuyas hojas eran pequeñas pantallas que mostraban los recuerdos más felices de quienes lo tocaban.",
        "text_en": "In the center of the Garden stood a mechanical tree whose leaves were tiny screens showing the happiest memories of whoever touched it.",
        "prompt": "ACTION: @image1 touches the trunk of a mechanical tree with one palm, eyes closed in peaceful happiness, @image2 at the base of the tree also touches the trunk, both sharing a tender moment. SETTING: Garden center WIDE VIEW, mechanical tree with copper pipe trunk and golden gear branches, each leaf a tiny glowing screen. ATMOSPHERE: Nostalgia, serenity. {style}",
        "text_position": "split"
    },
    {
        "id": 15,
        "text_es": "\"¡Es hora de tu propio invento!\", anunció BOLT. {name} imaginó algo increíble: una máquina que convertía los abrazos en estrellas brillantes.",
        "text_en": "\"It's time for your own invention!\" announced BOLT. {name} imagined something incredible: a machine that turned hugs into brilliant stars.",
        "prompt": "ACTION: @image1 stands with hands raised and eyes sparkling with inspiration, a glowing golden blueprint floats from @image1's imagination above, @image2 beside @image1 with antenna spinning excitedly, golden sparks materialize in the air. SETTING: Workshop creation area WIDE VIEW, inventor workstation, tools on bench, golden sparks and floating blueprints. ATMOSPHERE: Creative inspiration, golden sparks, excitement. {style}",
        "text_position": "split"
    },
    {
        "id": 16,
        "text_es": "Juntos construyeron la Máquina de Abrazos Estelares. Cuando {name} abrazó a BOLT para probarla, el taller se llenó de estrellas doradas que bailaban en el aire.",
        "text_en": "Together they built the Stellar Hug Machine. When {name} hugged BOLT to test it, the workshop filled with golden stars that danced in the air.",
        "prompt": "ACTION: @image1 hugs @image2 warmly with both arms, @image2 hugs back with blue eyes forming hearts, dozens of golden stars burst from a heart-shaped machine in the background. SETTING: Workshop center WIDE VIEW, heart-shaped machine visible in background, golden stars swirling everywhere. ATMOSPHERE: Pure joy and love, magical atmosphere. {style}",
        "text_position": "split"
    },
    {
        "id": 17,
        "text_es": "Las estrellas de sus abrazos volaron por la ventana del taller e iluminaron el cielo nocturno, creando una nueva constelación con la forma de un niño y su robot.",
        "text_en": "The stars from their hugs flew out the workshop window and lit up the night sky, creating a new constellation shaped like a child and a robot.",
        "prompt": "ACTION: @image1 stands at a large arched window pointing upward at a new constellation shaped like a child and a robot, @image2 next to @image1 also points up with blue eyes glowing softly, golden stars stream out through the window. SETTING: Inside workshop at arched window WIDE VIEW, beautiful night sky, golden constellation, moonlight. ATMOSPHERE: Magical nighttime, moonlight and starlight. {style}",
        "text_position": "split"
    },
    {
        "id": 18,
        "text_es": "\"Siempre que mires las estrellas, recuerda que un inventor puede cambiar el mundo con imaginación y corazón\", dijo BOLT, con sus ojos azules brillando más que nunca.",
        "text_en": "\"Whenever you look at the stars, remember that an inventor can change the world with imagination and heart,\" said BOLT, his blue eyes glowing brighter than ever.",
        "prompt": "ACTION: @image1 kneels to @image2's level and gently holds @image2's small metallic hands, @image2 faces @image1 with blue eyes glowing at their brightest, antenna pulsing gently, golden sparkles float around them both. SETTING: Workshop doorway WIDE VIEW, soft light bathing both characters. ATMOSPHERE: Heartfelt farewell, golden sparkles, tender friendship. {style}",
        "text_position": "split"
    },
    {
        "id": 19,
        "text_es": "{name} volvió a casa con el corazón lleno de ideas y la certeza de que la magia vive en cada invento creado con amor. Y colorín colorado, este cuento de inventores ha terminado.",
        "text_en": "{name} returned home with a heart full of ideas and the certainty that magic lives in every invention created with love. And they all lived happily ever after. The End.",
        "prompt": "ACTION: @image1 walks away from camera along a cobblestone path toward home, back fully facing viewer, carrying a small glowing copper box in one hand, head facing forward toward the house. SETTING: Winding cobblestone path WIDE VIEW, sunset sky in golden and purple, workshop in background with chimney puffing golden smoke, fireflies and mechanical butterflies. ATMOSPHERE: Peaceful sunset, peaceful goodbye, golden and purple tones. STRICT: Only @image1 in this scene. No face visible — character seen from behind. {style}",
        "text_position": "split"
    }
]

FRONT_COVER = {
    "prompt": (
        "Centered wide full body composite illustration.\n"
        "On the left, the human child whose face, skin tone, and hair color and style are preserved exactly from @image1. "
        "He wears a blue striped t-shirt and brown leather apron. "
        "Right arm raised holding a small glowing wrench with soft blue energy. Big joyful smile, beaming happy expression.\n"
        "The robot companion from @image2 stands beside him at knee-height, with its specific blue eyes, waving with one raised arm.\n"
        "SETTING: Magical inventor workshop WIDE VIEW, floating golden gears, crystal tubes with colorful liquids, sparkles, centered composition for book cover.\n"
        "ATMOSPHERE: Adventure invitation, magical, friendship and creativity.\n"
        "STRICT: Only ONE child (@image1), only ONE small robot (@image2). Pure illustration only. Disney Pixar 3D style.\n"
        "LIGHTING: Clean warm neutral cinematic studio lighting to prioritize preservation of original character colors (skin, hair, metal). "
        "Subtle color bounce and accents only from magical elements. No dense global haze."
    )
}

BACK_COVER = {
    "prompt": "SETTING: Magical inventor workshop seen from outside WIDE VIEW, charming old building with chimney puffing golden smoke, mechanical flowers around entrance, copper wind vanes on roof, fireflies and mechanical butterflies, sunset light. STRICT: NO characters, only scenery. Pure illustration only. {style}"
}


def get_outfit_desc(gender: str) -> str:
    if gender == "male":
        return "brown leather inventor apron over blue striped shirt with rolled-up sleeves, brown pants, sturdy boots, small goggles on forehead"
    else:
        return "brown leather inventor apron over purple striped shirt with rolled-up sleeves, comfortable pants, sturdy boots, small goggles on forehead"


def get_hair_action(traits: dict) -> str:
    hair_length = traits.get('hair_length', 'medium')
    if hair_length in ('bald', 'very_little', 'very_short'):
        return "very short hair neat and still"
    elif hair_length == 'long':
        return "long hair flowing beautifully in the wind"
    elif hair_length == 'short':
        return "short hair ruffled by the gentle breeze"
    else:
        return "hair gently moving in the wind"


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
        f"BACKGROUND: deep midnight blue studio background, plain — no robot, no scenery. "
        f"POSE: standing, full body visible from head to feet, curious adventurous smile, arms relaxed at sides."
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
        f"Two distinct characters: @image1 is a fully human {gender_word}, @image2 is the robot companion."
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
    for scene in MAGIC_INVENTOR_SCENES:
        prompts.append(build_scene_prompt(scene, child_name, gender, age, traits))
    return prompts


def get_cover_prompts(child_name: str, gender: str, age: int, traits: dict) -> dict:
    return {
        'front': build_scene_prompt(FRONT_COVER, child_name, gender, age, traits),
        'back': build_scene_prompt(BACK_COVER, child_name, gender, age, traits)
    }
