# Magic Inventor Workshop - Personalized Book Prompts
# 19 scenes + closing + covers with BOLT robot companion
# Ages 6-8 - Invention & creativity theme
#
# FLUX 2 Dev with reference image flow:
#   1. Preview: detailed character description → generates reference image
#   2. Scenes: FLUX 2 Dev takes reference image → prompts use SAME schema as Dragon Friend
#      Only needs {hair_desc}, {eye_desc}, {skin_tone} as brief hints (NOT full char_base)
#
# Schema (identical to Dragon Friend Quick Stories):
#   CHARACTER → OUTFIT → [COMPANION] → ACTION → SETTING → ATMOSPHERE → STRICT
#
# Rules:
#   - guidance_scale=3.5, num_inference_steps=28, aspect_ratio=3:4
#   - Keep prompts concise - FLUX 2 Dev loses focus with >300 words
#   - Style: Disney Pixar 3D everywhere, NO watercolor

STYLE_BASE = "Disney Pixar 3D style, soft luminous pastel colors with copper and golden accents, warm lighting, WIDE SHOT full body from head to feet, characters occupy 40% of frame, environment visible, clean illustration only, NO text, NO watermarks."

BOLT_INLINE = "BOLT: a small round copper robot with spherical body, big glowing blue eyes, two short metallic arms, two stumpy legs, small antenna on top with blinking light, copper patina finish"

MAGIC_INVENTOR_SCENES = [
    {
        "id": 1,
        "text_es": "En lo más alto de una vieja casona, {name} descubrió una puerta secreta detrás de una estantería polvorienta. Al abrirla, una luz dorada y chispas de colores salieron desde el interior.",
        "text_en": "At the very top of an old manor house, {name} discovered a secret door behind a dusty bookshelf. When they opened it, golden light and colorful sparks burst from inside.",
        "prompt": "Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, eyes wide with wonder. OUTFIT: {outfit_desc}. ACTION: {gender_word} pushes open a glowing door, golden light on face, colorful sparks from doorway. SETTING: Dusty attic WIDE VIEW, wooden beams, cobwebs, mysterious door behind tilted bookshelf glowing golden, old books on shelves. ATMOSPHERE: Discovery, warm amber lighting, magical particles. STRICT: Only ONE {gender_word}, NO robot, {gender_word} is 100% human child, no duplicates. {style}",
        "text_position": "split"
    },
    {
        "id": 2,
        "text_es": "¡Era un taller mágico lleno de inventos asombrosos! Engranajes dorados flotaban por el aire, tubos de cristal brillaban con líquidos de colores y herramientas mágicas se movían solas.",
        "text_en": "It was a magical workshop full of amazing inventions! Golden gears floated in the air, crystal tubes glowed with colorful liquids, and magical tools moved on their own.",
        "prompt": "Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, mouth open with amazement. OUTFIT: {outfit_desc}. ACTION: {gender_word} stands at workshop entrance, amazed by floating golden gears. SETTING: Magnificent inventor workshop WIDE VIEW, floating golden gears spinning, crystal tubes with colorful glowing liquids, workbenches with blueprints and gadgets. ATMOSPHERE: Copper and golden tones, sparkling magical atmosphere. STRICT: Only ONE {gender_word}, NO robot, {gender_word} is 100% human child, no duplicates. {style}",
        "text_position": "split"
    },
    {
        "id": 3,
        "text_es": "De pronto, una pequeña esfera de cobre rodó hasta los pies de {name}. Se abrió y de ella surgió un simpático robot con ojos azules brillantes. \"¡Hola! Soy BOLT\", dijo con voz metálica y alegre.",
        "text_en": "Suddenly, a small copper sphere rolled to {name}'s feet. It opened up and out came a friendly little robot with bright blue eyes. \"Hello! I'm BOLT,\" it said with a cheerful metallic voice.",
        "prompt": "Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, looking down surprised. OUTFIT: {outfit_desc}. COMPANION: {BOLT_INLINE}. ACTION: {gender_word} looks down at a copper sphere opening like flower petals at their feet, BOLT emerges from sphere, arms up in greeting, blue eyes glowing. SETTING: Workshop floor WIDE VIEW, warm golden light, floating gears in background. ATMOSPHERE: Surprise and first meeting, warm golden light, blue and copper sparks. STRICT: Only ONE {gender_word}, only ONE small robot BOLT, {gender_word} is 100% human child, no duplicates. {style}",
        "text_position": "split"
    },
    {
        "id": 4,
        "text_es": "BOLT le mostró a {name} el Mapa de los Inventos Perdidos, un pergamino brillante donde aparecían máquinas fantásticas esperando ser reconstruidas por un inventor valiente.",
        "text_en": "BOLT showed {name} the Map of Lost Inventions, a glowing scroll where fantastic machines appeared, waiting to be rebuilt by a brave inventor.",
        "prompt": "Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, leaning forward curiously. OUTFIT: {outfit_desc}. COMPANION: {BOLT_INLINE}. ACTION: {gender_word} leans over table examining a glowing golden scroll with animated blueprints, BOLT stands on table pointing at drawings. SETTING: Workshop table WIDE VIEW, large golden scroll unrolled showing fantastical machine drawings, warm amber light from scroll. ATMOSPHERE: Excitement, warm amber glow, magical shimmer. STRICT: Only ONE {gender_word}, only ONE small robot BOLT, {gender_word} is 100% human child, no duplicates. {style}",
        "text_position": "split"
    },
    {
        "id": 5,
        "text_es": "\"¡Nuestro primer invento será una Bicicleta Voladora!\", exclamó BOLT. {name} encontró ruedas de cristal, pedales de arcoíris y un manillar que brillaba como una estrella.",
        "text_en": "\"Our first invention will be a Flying Bicycle!\" exclaimed BOLT. {name} found crystal wheels, rainbow pedals, and handlebars that glowed like a star.",
        "prompt": "Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, excited smile, holding crystal wheel. OUTFIT: {outfit_desc}. COMPANION: {BOLT_INLINE}. ACTION: {gender_word} holds up a sparkling crystal wheel to the light, BOLT on workbench sorts through mechanical parts. SETTING: Workshop corner WIDE VIEW, scattered magical bicycle parts on workbench: crystal wheels, rainbow pedals, star handlebars, copper wings, blueprints on wall. ATMOSPHERE: Creative energy, warm golden light, sparkles. STRICT: Only ONE {gender_word}, only ONE small robot BOLT, {gender_word} is 100% human child, no duplicates. {style}",
        "text_position": "split"
    },
    {
        "id": 6,
        "text_es": "{name} y BOLT construyeron juntos la Bicicleta Voladora. Cada pieza encajaba con un destello de luz y el taller se llenó de música mágica.",
        "text_en": "{name} and BOLT built the Flying Bicycle together. Each piece clicked into place with a flash of light, and the workshop filled with magical music.",
        "prompt": "Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, concentrating happily. OUTFIT: {outfit_desc}. COMPANION: {BOLT_INLINE}. ACTION: {gender_word} uses a glowing wrench to attach a crystal wheel to a half-built magical bicycle, golden sparks flying, BOLT nearby passes gears with both arms, musical notes float in the air. SETTING: Workshop center WIDE VIEW, half-built magical bicycle, golden sparks, floating musical notes. ATMOSPHERE: Joy of creation, warm golden atmosphere, teamwork. STRICT: Only ONE {gender_word}, only ONE small robot BOLT, {gender_word} is 100% human child, no duplicates. {style}",
        "text_position": "split"
    },
    {
        "id": 7,
        "text_es": "¡La Bicicleta Voladora cobró vida! {name} pedaleó hacia el cielo del taller, que se abrió como un libro mágico revelando un cielo lleno de estrellas y nubes de algodón.",
        "text_en": "The Flying Bicycle came alive! {name} pedaled into the workshop sky, which opened like a magical book revealing a sky full of stars and cotton candy clouds.",
        "prompt": "Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, face showing pure joy, {hair_action}. OUTFIT: {outfit_desc}. COMPANION: {BOLT_INLINE}. ACTION: The same {gender_word} child rides a completed flying bicycle, pedaling joyfully, soaring upward through workshop ceiling into starry sky, BOLT sits in bicycle basket, arms raised excited, copper wings extended, golden spark trail behind. SETTING: Workshop ceiling opening WIDE VIEW, starry sky with cotton candy clouds in pink and blue. ATMOSPHERE: Freedom, magical flight, golden sparkles. STRICT: Only ONE {gender_word} child on bicycle, only ONE small robot BOLT in basket, {gender_word} is NORMAL CHILD SIZE, 100% human, NO other people. {style}",
        "text_position": "split"
    },
    {
        "id": 8,
        "text_es": "Volaron sobre un océano de nubes hasta llegar a la Isla de las Ideas, un lugar flotante donde las ideas se convertían en burbujas brillantes de todos los colores.",
        "text_en": "They flew over an ocean of clouds to reach the Island of Ideas, a floating place where ideas turned into brilliant bubbles of every color.",
        "prompt": "Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, expression of wonder. OUTFIT: {outfit_desc}. COMPANION: {BOLT_INLINE}. ACTION: {gender_word} stands on a floating island, reaching toward a giant pink bubble containing a tiny invention, BOLT beside {gender_word} points at a bubble. SETTING: Floating island in sky WIDE VIEW, colorful clouds, giant colorful idea-bubbles floating everywhere, rainbow bridges. ATMOSPHERE: Ethereal wonder, soft pastel colors, dreamy. STRICT: Only ONE {gender_word}, only ONE small robot BOLT, {gender_word} is 100% human child, no duplicates. {style}",
        "text_position": "split"
    },
    {
        "id": 9,
        "text_es": "En la Isla encontraron la Caja Musical Infinita, un invento que creaba melodías que podían hacer crecer flores y pintar arcoíris en el cielo.",
        "text_en": "On the Island they found the Infinite Music Box, an invention that created melodies that could grow flowers and paint rainbows in the sky.",
        "prompt": "Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, peaceful smile, eyes half-closed. OUTFIT: {outfit_desc}. COMPANION: {BOLT_INLINE}. ACTION: {gender_word} kneels beside a golden music box, one hand touching a key, BOLT on other side sways to the music, rainbow musical notes spiral upward, flowers grow around the base. SETTING: Floating island clearing WIDE VIEW, ornate golden music box, rainbow light notes, flowers growing, small rainbow above. ATMOSPHERE: Musical serenity, warm sparkles. STRICT: Only ONE {gender_word}, only ONE small robot BOLT, {gender_word} is 100% human child, no duplicates. {style}",
        "text_position": "split"
    },
    {
        "id": 10,
        "text_es": "\"¡Necesitamos reparar el Telescopio de Arcoíris!\", dijo BOLT. Era un telescopio mágico que permitía ver los sueños de cualquier persona en cualquier lugar del mundo.",
        "text_en": "\"We need to fix the Rainbow Telescope!\" said BOLT. It was a magical telescope that let you see anyone's dreams anywhere in the world.",
        "prompt": "Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, thinking pose with hand on chin. OUTFIT: {outfit_desc}. COMPANION: {BOLT_INLINE}. ACTION: {gender_word} examines a large broken copper telescope with crystal prisms, BOLT holds a broken crystal lens up to the light. SETTING: Workshop platform WIDE VIEW, scattered lenses and gears, faint rainbow light from telescope cracks, starry backdrop. ATMOSPHERE: Problem-solving, soft rainbow refractions, stars. STRICT: Only ONE {gender_word}, only ONE small robot BOLT, {gender_word} is 100% human child, no duplicates. {style}",
        "text_position": "split"
    },
    {
        "id": 11,
        "text_es": "{name} descubrió que la pieza que faltaba era un cristal con forma de corazón. Lo encontraron escondido dentro de un reloj antiguo que marcaba la hora de los sueños.",
        "text_en": "{name} discovered that the missing piece was a heart-shaped crystal. They found it hidden inside an ancient clock that marked the hour of dreams.",
        "prompt": "Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, face lit by crystal glow, careful concentration. OUTFIT: {outfit_desc}. COMPANION: {BOLT_INLINE}. ACTION: {gender_word} reaches into an ancient grandfather clock to take a glowing heart-shaped crystal, BOLT beside {gender_word} shines blue light from eyes. SETTING: Workshop alcove WIDE VIEW, ancient grandfather clock with celestial decorations, moon and star motifs, clock door open showing crystal. ATMOSPHERE: Dreamy purple and gold, golden sparkles. STRICT: Only ONE {gender_word}, only ONE small robot BOLT, {gender_word} is 100% human child, no duplicates. {style}",
        "text_position": "split"
    },
    {
        "id": 12,
        "text_es": "Con el cristal corazón en su lugar, el Telescopio de Arcoíris mostró los sueños más hermosos: ciudades flotantes, jardines submarinos y montañas de caramelo.",
        "text_en": "With the heart crystal in place, the Rainbow Telescope showed the most beautiful dreams: floating cities, underwater gardens, and candy mountains.",
        "prompt": "Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, amazed expression. OUTFIT: {outfit_desc}. COMPANION: {BOLT_INLINE}. ACTION: {gender_word} looks through a repaired rainbow telescope, holographic projections of dreams float above: floating cities, underwater gardens, candy mountains, BOLT watches projections, arms raised. SETTING: Workshop observatory WIDE VIEW, telescope projecting rainbow holographic display, swirling dream images. ATMOSPHERE: Rainbow wonder, magical projections. STRICT: Only ONE {gender_word}, only ONE small robot BOLT, {gender_word} is 100% human child, no duplicates. {style}",
        "text_position": "split"
    },
    {
        "id": 13,
        "text_es": "BOLT llevó a {name} al Jardín de los Engranajes, donde flores mecánicas de cobre y cristal abrían y cerraban sus pétalos con suaves chasquidos musicales.",
        "text_en": "BOLT led {name} to the Garden of Gears, where mechanical flowers made of copper and crystal opened and closed their petals with soft musical clicks.",
        "prompt": "Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, smiling with delight. OUTFIT: {outfit_desc}. COMPANION: {BOLT_INLINE}. ACTION: {gender_word} walks along a cobblestone path, touching a large copper mechanical flower that opens at the touch, BOLT walks beside {gender_word}, a mechanical butterfly on antenna. SETTING: Enchanting garden WIDE VIEW, mechanical copper flowers with crystal stems opening and closing, mechanical butterflies, cobblestone path, copper archways. ATMOSPHERE: Whimsical beauty, warm soft lighting, sparkles. STRICT: Only ONE {gender_word}, only ONE small robot BOLT, {gender_word} is 100% human child, no duplicates. {style}",
        "text_position": "split"
    },
    {
        "id": 14,
        "text_es": "En el centro del Jardín había un árbol mecánico cuyas hojas eran pequeñas pantallas que mostraban los recuerdos más felices de quienes lo tocaban.",
        "text_en": "In the center of the Garden stood a mechanical tree whose leaves were tiny screens showing the happiest memories of whoever touched it.",
        "prompt": "Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, eyes closed, peaceful happy smile. OUTFIT: {outfit_desc}. COMPANION: {BOLT_INLINE}. ACTION: {gender_word} touches trunk of a mechanical tree with one palm, eyes closed peacefully, BOLT at base of tree also touches trunk. SETTING: Garden center WIDE VIEW, mechanical tree with copper pipe trunk and golden gear branches, each leaf a tiny glowing screen, warm golden light. ATMOSPHERE: Warm nostalgia, golden glow, serenity. STRICT: Only ONE {gender_word}, only ONE small robot BOLT, {gender_word} is 100% human child, no duplicates. {style}",
        "text_position": "split"
    },
    {
        "id": 15,
        "text_es": "\"¡Es hora de tu propio invento!\", anunció BOLT. {name} imaginó algo increíble: una máquina que convertía los abrazos en estrellas brillantes.",
        "text_en": "\"It's time for your own invention!\" announced BOLT. {name} imagined something incredible: a machine that turned hugs into brilliant stars.",
        "prompt": "Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, hands raised, eyes sparkling with inspiration. OUTFIT: {outfit_desc}. COMPANION: {BOLT_INLINE}. ACTION: {gender_word} stands with hands raised, a glowing golden blueprint floats from imagination above, BOLT beside {gender_word}, antenna spinning excitedly, golden sparks materialize in the air. SETTING: Workshop creation area WIDE VIEW, inventor workstation, tools on bench, golden sparks and floating blueprints. ATMOSPHERE: Creative inspiration, golden sparks, excitement. STRICT: Only ONE {gender_word}, only ONE small robot BOLT, {gender_word} is 100% human child, no duplicates. {style}",
        "text_position": "split"
    },
    {
        "id": 16,
        "text_es": "Juntos construyeron la Máquina de Abrazos Estelares. Cuando {name} abrazó a BOLT para probarla, el taller se llenó de estrellas doradas que bailaban en el aire.",
        "text_en": "Together they built the Stellar Hug Machine. When {name} hugged BOLT to test it, the workshop filled with golden stars that danced in the air.",
        "prompt": "Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, pure happiness. OUTFIT: {outfit_desc}. COMPANION: {BOLT_INLINE}. ACTION: {gender_word} hugs BOLT warmly with both arms, BOLT hugs back, blue eyes forming hearts, dozens of golden stars burst from a heart-shaped machine in background. SETTING: Workshop center WIDE VIEW, heart-shaped machine visible, golden stars swirling everywhere. ATMOSPHERE: Pure joy and love, warm golden atmosphere. STRICT: Only ONE {gender_word}, only ONE small robot BOLT, {gender_word} is 100% human child, no duplicates. {style}",
        "text_position": "split"
    },
    {
        "id": 17,
        "text_es": "Las estrellas de sus abrazos volaron por la ventana del taller e iluminaron el cielo nocturno, creando una nueva constelación con la forma de un niño y su robot.",
        "text_en": "The stars from their hugs flew out the workshop window and lit up the night sky, creating a new constellation shaped like a child and a robot.",
        "prompt": "Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, face in moonlight, proud wonder, pointing up. OUTFIT: {outfit_desc}. COMPANION: {BOLT_INLINE}. ACTION: {gender_word} stands at a large arched window pointing up at a new constellation shaped like a child and robot, BOLT next to {gender_word} also points up, blue eyes glowing softly, golden stars stream out through window. SETTING: Inside workshop at arched window WIDE VIEW, beautiful night sky, golden constellation, moonlight. ATMOSPHERE: Magical nighttime, moonlight and starlight. STRICT: Only ONE {gender_word}, only ONE small robot BOLT, {gender_word} is 100% human child, no duplicates. {style}",
        "text_position": "split"
    },
    {
        "id": 18,
        "text_es": "\"Siempre que mires las estrellas, recuerda que un inventor puede cambiar el mundo con imaginación y corazón\", dijo BOLT, con sus ojos azules brillando más que nunca.",
        "text_en": "\"Whenever you look at the stars, remember that an inventor can change the world with imagination and heart,\" said BOLT, his blue eyes glowing brighter than ever.",
        "prompt": "Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, kneeling, loving grateful eyes. OUTFIT: {outfit_desc}. COMPANION: {BOLT_INLINE}. ACTION: {gender_word} kneels to BOLT's level, gently holding BOLT's small metallic hands, BOLT faces {gender_word}, blue eyes glowing brightest, antenna pulsing gently, golden sparkles float around them. SETTING: Workshop doorway WIDE VIEW, warm golden light bathing both characters. ATMOSPHERE: Heartfelt farewell, warm golden light, tender friendship. STRICT: Only ONE {gender_word}, only ONE small robot BOLT, {gender_word} is 100% human child, no duplicates. {style}",
        "text_position": "split"
    },
    {
        "id": 19,
        "text_es": "{name} volvió a casa con el corazón lleno de ideas y la certeza de que la magia vive en cada invento creado con amor. Y colorín colorado, este cuento de inventores ha terminado.",
        "text_en": "{name} returned home with a heart full of ideas and the certainty that magic lives in every invention created with love. And they all lived happily ever after. The End.",
        "prompt": "Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, warm smile, looking back over shoulder waving goodbye. OUTFIT: {outfit_desc}. ACTION: {gender_word} walks along a cobblestone path toward home, carrying a small glowing copper box. SETTING: Winding cobblestone path WIDE VIEW, warm sunset sky in golden and purple, workshop in background with chimney puffing golden smoke, fireflies and mechanical butterflies. ATMOSPHERE: Peaceful sunset, warm goodbye, golden and purple tones. STRICT: Only ONE {gender_word}, NO robot, {gender_word} is 100% human child, no duplicates. {style}",
        "text_position": "bottom"
    }
]

CLOSING_SCENE = {
    "id": 20,
    "prompt": "Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, sleeping peacefully with gentle smile, one arm over a small copper BOLT plush toy. OUTFIT: Cozy pajamas with tiny gear patterns. ACTION: {gender_word} sleeps in a cozy bed, on nightstand a small glowing copper box shimmers. SETTING: Cozy bedroom at night WIDE VIEW, warm lighting, stars through window, golden mechanical butterfly mobile above bed. ATMOSPHERE: Dreamy peaceful slumber, warm glow. STRICT: Only ONE {gender_word}, NO real robot, only plush toy, {gender_word} is 100% human child. {style}",
    "text_position": "none"
}

FRONT_COVER = {
    "prompt": "Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, confident joyful smile, holding a glowing wrench. OUTFIT: {outfit_desc}. COMPANION: {BOLT_INLINE}. ACTION: {gender_word} and BOLT stand together in center of workshop, facing viewer, centered composition for book cover, BOLT waves with one arm, blue eyes bright. SETTING: Magical inventor workshop WIDE VIEW, floating golden gears, crystal tubes with colorful liquids, warm golden light, sparkles. ATMOSPHERE: Adventure invitation, warm golden, friendship and creativity. STRICT: Only ONE {gender_word}, only ONE small robot BOLT, {gender_word} is 100% human child, no duplicates. ABSOLUTELY NO rendered text anywhere in the image, no titles, no logos, no words, no letters, no captions, no watermarks, no signatures, pure illustration only. {style}"
}

BACK_COVER = {
    "prompt": "Disney Pixar 3D style illustration. SETTING: Magical inventor workshop seen from outside WIDE VIEW, charming old building with chimney puffing golden smoke, mechanical flowers around entrance, copper wind vanes on roof, fireflies and mechanical butterflies, warm sunset light. STRICT: NO characters, only scenery. ABSOLUTELY NO rendered text anywhere in the image, no titles, no logos, no words, no letters, no captions, no watermarks, no signatures, pure illustration only. {style}"
}


def get_outfit_desc(gender: str) -> str:
    if gender == "male":
        return "brown leather inventor apron over blue striped shirt with rolled-up sleeves, brown pants, sturdy boots, small goggles on forehead"
    else:
        return "brown leather inventor apron over purple striped shirt with rolled-up sleeves, comfortable pants, sturdy boots, small goggles on forehead"


def get_hair_action(traits: dict) -> str:
    hair_length = traits.get('hair_length', 'medium')
    if hair_length == 'long':
        return "long hair flowing beautifully in the wind"
    elif hair_length == 'short':
        return "short hair ruffled by the gentle breeze"
    else:
        return "hair gently moving in the wind"


def build_scene_prompt(scene: dict, child_name: str, gender: str, age: int, traits: dict) -> str:
    from services.fixed_stories import get_hair_description, get_eye_description
    from services.replicate_service import get_unified_skin_description

    outfit_desc = get_outfit_desc(gender)
    hair_action = get_hair_action(traits)
    hair_desc = get_hair_description(traits)
    eye_desc = get_eye_description(traits)
    skin_tone = get_unified_skin_description(traits.get('skin_tone', 'light'))
    gender_word = "boy" if gender == "male" else "girl" if gender == "female" else "child"
    age_display = f"{age} year old" if age and age > 0 else "6 year old"

    prompt = scene.get('prompt', '')
    prompt = prompt.replace('{outfit_desc}', outfit_desc)
    prompt = prompt.replace('{hair_action}', hair_action)
    prompt = prompt.replace('{hair_desc}', hair_desc)
    prompt = prompt.replace('{eye_desc}', eye_desc)
    prompt = prompt.replace('{skin_tone}', skin_tone)
    prompt = prompt.replace('{gender_word}', gender_word)
    prompt = prompt.replace('{age_display}', age_display)
    prompt = prompt.replace('{BOLT_INLINE}', BOLT_INLINE)
    prompt = prompt.replace('{style}', STYLE_BASE)
    prompt = prompt.replace('{name}', child_name)
    prompt = prompt.replace('{child_name}', child_name)

    from services.fixed_stories import enforce_gender_clothing
    prompt = enforce_gender_clothing(prompt, gender)

    return prompt


def get_all_scene_prompts(child_name: str, gender: str, age: int, traits: dict) -> list:
    prompts = []
    for scene in MAGIC_INVENTOR_SCENES:
        prompts.append(build_scene_prompt(scene, child_name, gender, age, traits))
    prompts.append(build_scene_prompt(CLOSING_SCENE, child_name, gender, age, traits))
    return prompts


def get_cover_prompts(child_name: str, gender: str, age: int, traits: dict) -> dict:
    return {
        'front': build_scene_prompt(FRONT_COVER, child_name, gender, age, traits),
        'back': build_scene_prompt(BACK_COVER, child_name, gender, age, traits)
    }
