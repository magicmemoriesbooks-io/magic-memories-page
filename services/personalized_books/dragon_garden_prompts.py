# Dragon Garden - Personalized Book Prompts
# Reference-image flow: @image1 = child character portrait, @image2 = SPARK dragon companion
#
# Prompts contain ONLY action + setting — NO character physical descriptions.
# All appearance (face, hair, skin, outfit) comes from the reference images.
#
# Reference note is prepended by generate_scene_complete:
#   "@image1=child character — copy face, hair, skin, and outfit exactly.
#    @image2=small emerald dragon SPARK — copy appearance exactly."
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
#   - Scenes 1, 19 and CLOSING have no @image2

STYLE_BASE = "Disney Pixar 3D style, soft luminous pastel colors with emerald and golden accents, warm lighting, WIDE SHOT full body from head to feet, characters occupy 40% of frame, environment visible, clean illustration only, NO text, NO watermarks."

SPARK_INLINE = "SPARK: an adorable baby dragon with small chubby round body covered in shimmering emerald green scales, large expressive golden eyes, tiny translucent iridescent wings, short stubby tail, small rounded snout with a sweet smile, two tiny curved horns on head, soft cream-colored belly"

DRAGON_GARDEN_SCENES = [
    {
        "id": 1,
        "text_es": "Había una vez, en un lugar donde los sueños cobran vida, un jardín mágico escondido detrás de un viejo roble. Solo los niños de corazón puro podían encontrarlo.",
        "text_en": "Once upon a time, in a place where dreams come alive, there was a magical garden hidden behind an old oak tree. Only children with pure hearts could find it.",
        "prompt": "ACTION: @image1 stands before a magnificent glowing magical door covered in flowering vines, one hand reaching toward the golden handle, eyes wide with wonder and curiosity. SETTING: Ancient oak tree WIDE VIEW, enchanted garden entrance with oversized colorful flowers, magical butterflies and fireflies floating, soft morning golden light. ATMOSPHERE: Discovery and wonder, warm golden glow. STRICT: Only @image1 in this scene. {style}",
        "text_position": "split"
    },
    {
        "id": 2,
        "text_es": "De pronto, {name} escuchó un sonido suave. ¡Era un pequeño dragón con escamas de esmeralda brillante! \"¡Hola! Me llamo Chispa\", dijo el dragoncito con una sonrisa amable.",
        "text_en": "Suddenly, {name} heard a soft sound. It was a tiny dragon with shimmering emerald scales! \"Hello! My name is Spark,\" said the little dragon with a kind smile.",
        "prompt": "ACTION: @image1 looks with wonder and delight as @image2 sits on a giant pink rose waving a tiny paw in greeting with a sweet welcoming smile. SETTING: Magical garden clearing WIDE VIEW, giant colorful flowers, sparkling dewdrops, rainbow light filtering through leaves. ATMOSPHERE: First meeting, wonder and joy, sparkles in the air. {style}",
        "text_position": "split"
    },
    {
        "id": 3,
        "text_es": "\"¿Quieres volar conmigo?\", preguntó Chispa emocionado. {name} subió a su espalda y juntos se elevaron sobre las nubes de algodón, sintiendo el viento suave.",
        "text_en": "\"Would you like to fly with me?\" asked Spark excitedly. {name} climbed on his back and together they soared above the cotton clouds, feeling the gentle wind.",
        "prompt": "ACTION: @image1 sits happily on @image2's back flying through the sky, arms wrapped gently around @image2's neck, @image2's wings spread wide and flapping, golden sparkles trailing behind. SETTING: Beautiful sky WIDE VIEW, fluffy pink and white cotton clouds, golden sunlight, rainbow visible in the distance, magical sparkles. ATMOSPHERE: Freedom and joy, golden sparkles. {style}",
        "text_position": "split"
    },
    {
        "id": 4,
        "text_es": "Volaron sobre un arcoíris brillante que pintaba el cielo con todos los colores imaginables. \"Cada color tiene un poder especial\", explicó Chispa.",
        "text_en": "They flew over a brilliant rainbow that painted the sky with every imaginable color. \"Each color has a special power,\" explained Spark.",
        "prompt": "ACTION: @image1 rides on @image2's back flying through a magnificent magical rainbow, arms spread wide with pure joy and laughter, colors of the rainbow swirling all around them. SETTING: Sky WIDE VIEW, fluffy pastel clouds, golden sparkles everywhere, magical rainbow arching in red orange yellow green blue purple. ATMOSPHERE: Pure wonder, rainbow colors, magical. {style}",
        "text_position": "split"
    },
    {
        "id": 5,
        "text_es": "Aterrizaron junto a flores gigantes de pétalos suaves. Las mariposas danzaban alrededor mientras el aroma dulce llenaba el aire.",
        "text_en": "They landed next to giant flowers with soft petals. Butterflies danced around while the sweet fragrance filled the air.",
        "prompt": "ACTION: @image1 stands among enormous glowing flowers touching a petal gently, @image2 stands beside looking up at the flowers with wide golden eyes. SETTING: Garden of giant flowers WIDE VIEW, giant roses sunflowers and tulips towering above, magical butterflies dancing, bioluminescent glow from petals, sparkles floating. ATMOSPHERE: Dreamy wonder, soft bioluminescent glow. {style}",
        "text_position": "split"
    },
    {
        "id": 6,
        "text_es": "En el corazón del jardín, conocieron a los animalitos mágicos: conejos con alas de cristal, ardillas que brillaban como estrellas y pájaros cantores de plumas doradas.",
        "text_en": "In the heart of the garden, they met the magical little animals: rabbits with crystal wings, squirrels that glowed like stars, and songbirds with golden feathers.",
        "prompt": "ACTION: @image1 kneels down with a warm smile petting cute magical animals — rabbits with crystal wings, glowing squirrels, golden-feathered birds gathered around, @image2 sits nearby watching happily. SETTING: Magical forest heart WIDE VIEW, glowing mushrooms, dappled golden sunlight through trees, colorful butterflies. ATMOSPHERE: Warm friendship, gentle golden light. {style}",
        "text_position": "split"
    },
    {
        "id": 7,
        "text_es": "Chispa llevó a {name} a una cueva secreta llena de cristales brillantes. Los colores bailaban en las paredes como un caleidoscopio mágico.",
        "text_en": "Spark took {name} to a secret cave full of shining crystals. The colors danced on the walls like a magical kaleidoscope.",
        "prompt": "ACTION: @image1 walks inside a crystal cave touching a glowing crystal with one hand, face illuminated by colorful light, @image2 walks beside emitting a soft emerald glow to light the way. SETTING: Beautiful crystal cave WIDE VIEW, colorful crystals in purple blue pink and gold sparkling like a kaleidoscope, ethereal atmosphere. ATMOSPHERE: Magical wonder, colorful reflections. {style}",
        "text_position": "split"
    },
    {
        "id": 8,
        "text_es": "Siguieron un río que brillaba con reflejos de estrellas caídas. Pequeños peces luminosos saltaban felices entre las olas cristalinas.",
        "text_en": "They followed a river that glowed with reflections of fallen stars. Small luminous fish jumped happily among the crystal waves.",
        "prompt": "ACTION: @image1 walks along the enchanted riverbank looking at the luminous fish with delight, @image2 flies beside the child watching the fish jump. SETTING: Magical river WIDE VIEW, glowing with starlight reflections, crystal-clear water, luminous colorful fish jumping, glowing flowers on riverbank, fireflies hovering. ATMOSPHERE: Enchanted forest, magical soft light. {style}",
        "text_position": "split"
    },
    {
        "id": 9,
        "text_es": "Chispa mostró a {name} su nido con huevos dorados. \"Algún día nacerán más dragones mágicos\", dijo con orgullo y ternura en sus ojos.",
        "text_en": "Spark showed {name} his nest with golden eggs. \"Someday more magical dragons will be born,\" he said with pride and tenderness in his eyes.",
        "prompt": "ACTION: @image1 looks in amazement at a cozy nest, @image2 sits proudly beside showing three golden dragon eggs that glow softly with magical light. SETTING: Magical treehouse interior WIDE VIEW, warm golden light, cozy dragon nest made of golden materials with three glowing eggs. ATMOSPHERE: Warmth, pride, tenderness. {style}",
        "text_position": "split"
    },
    {
        "id": 10,
        "text_es": "Descubrieron una cascada de cristal que formaba arcoíris en el aire. El agua brillaba como diamantes líquidos bajo el sol mágico.",
        "text_en": "They discovered a crystal waterfall that formed rainbows in the air. The water sparkled like liquid diamonds under the magical sun.",
        "prompt": "ACTION: @image1 stands at the edge of a pool touching the sparkling water with fingertips, @image2 splashes playfully in the shallow water nearby. SETTING: Crystal waterfall WIDE VIEW, cascading water glowing like liquid diamonds, rainbows forming in the mist, lush tropical flowers surrounding. ATMOSPHERE: Magical splashing fun, rainbow mist. {style}",
        "text_position": "split"
    },
    {
        "id": 11,
        "text_es": "En un círculo de hongos gigantes, las hadas bailaban felices. Invitaron a {name} a unirse a su danza bajo las luces brillantes.",
        "text_en": "In a circle of giant mushrooms, the fairies danced happily. They invited {name} to join their dance under the bright lights.",
        "prompt": "ACTION: @image1 dances with arms raised joyfully, tiny glowing fairies flying around, @image2 dances nearby on hind legs with stubby wings fluttering. SETTING: Circle of giant mushrooms WIDE VIEW, red with white spots purple blue, magical forest clearing, sparkles everywhere. ATMOSPHERE: Whimsical dance, glowing fairy light. {style}",
        "text_position": "split"
    },
    {
        "id": 12,
        "text_es": "Volaron tan alto que llegaron al reino de las nubes, donde los castillos flotaban y los ángeles jugaban entre algodones de colores.",
        "text_en": "They flew so high they reached the kingdom of clouds, where castles floated and angels played among colorful cotton.",
        "prompt": "ACTION: @image1 stands on a fluffy pink cloud with arms spread wide in joy, @image2 bounces on a separate cloud nearby playfully jumping between clouds. SETTING: Kingdom in the sky WIDE VIEW, magnificent crystal cloud castles floating, rainbow bridges, cotton candy clouds in pastel colors, blue sky, golden sunlight. ATMOSPHERE: Paradise wonder, magical sky kingdom. {style}",
        "text_position": "split"
    },
    {
        "id": 13,
        "text_es": "En el centro del jardín encontraron un árbol antiguo donde cada hoja brillaba con un deseo cumplido. {name} tocó una hoja y sintió calidez en el corazón.",
        "text_en": "In the center of the garden they found an ancient tree where each leaf glowed with a fulfilled wish. {name} touched a leaf and felt warmth in their heart.",
        "prompt": "ACTION: @image1 reaches up with eyes closed and a peaceful smile to touch a glowing golden leaf with gentle reverence, @image2 watches beside with wonder and golden light reflecting off scales. SETTING: Enormous wishing tree WIDE VIEW, thousands of glowing leaves in gold pink and blue, ethereal atmosphere, magical sparkles floating. ATMOSPHERE: Peaceful warmth, golden glow. {style}",
        "text_position": "split"
    },
    {
        "id": 14,
        "text_es": "Chispa reveló una sala secreta llena de tesoros mágicos: libros que contaban historias solas, brújulas que señalaban hacia los sueños y llaves de mundos lejanos.",
        "text_en": "Spark revealed a secret room full of magical treasures: books that told stories by themselves, compasses that pointed to dreams, and keys to distant worlds.",
        "prompt": "ACTION: @image1 holds a glowing book with an amazed expression while looking around in wonder, @image2 shows the child around proudly pointing at treasures with a tiny paw. SETTING: Secret treasure room WIDE VIEW, floating glowing books, magical compasses, golden keys, treasure chests, crystals, soft warm magical light. ATMOSPHERE: Wonder and discovery, warm glow. {style}",
        "text_position": "split"
    },
    {
        "id": 15,
        "text_es": "Cruzaron un prado donde miles de mariposas brillantes creaban una danza de colores. Sus alas dejaban estelas de polvo de estrellas.",
        "text_en": "They crossed a meadow where thousands of glowing butterflies created a dance of colors. Their wings left trails of stardust.",
        "prompt": "ACTION: @image1 walks through the meadow with arms gently raised as butterflies land on hands and shoulders, @image2 flies alongside with butterflies resting on head and wings. SETTING: Meadow of wildflowers WIDE VIEW, thousands of colorful glowing butterflies in rainbow colors leaving stardust trails, magical soft light. ATMOSPHERE: Dreamy butterfly dance, stardust trails. {style}",
        "text_position": "split"
    },
    {
        "id": 16,
        "text_es": "\"Quiero que aprendas algo especial\", dijo Chispa. Y le enseñó a {name} que con imaginación y valentía, todos podemos volar en nuestros sueños.",
        "text_en": "\"I want to teach you something special,\" said Spark. And he taught {name} that with imagination and courage, we can all fly in our dreams.",
        "prompt": "ACTION: @image1 floats magically in the air with arms spread wide surrounded by golden sparkles and stardust with a joyful amazed expression, @image2 flies beside encouraging with wings spread wide. SETTING: Magical sky WIDE VIEW, soft clouds, golden sunlight, rainbow in distance, dreamy ethereal atmosphere. ATMOSPHERE: Freedom and magic, golden sparkles. {style}",
        "text_position": "split"
    },
    {
        "id": 17,
        "text_es": "Juntos observaron la puesta de sol más hermosa, donde el cielo se pintó de rosa, naranja y púrpura, mientras las primeras estrellas aparecían.",
        "text_en": "Together they watched the most beautiful sunset, where the sky painted itself pink, orange, and purple, while the first stars appeared.",
        "prompt": "ACTION: @image1 sits peacefully on a grassy hill with a content expression, @image2 sits close beside, both watching the sunset together. SETTING: Grassy hilltop WIDE VIEW, spectacular sunset sky in gorgeous pinks oranges and purples, first stars appearing, fireflies beginning to glow, silhouettes of magical trees. ATMOSPHERE: Serene peace, warm sunset colors. {style}",
        "text_position": "split"
    },
    {
        "id": 18,
        "text_es": "\"Siempre seremos amigos\", prometió Chispa. \"Cada vez que mires las estrellas, estaré pensando en ti.\"",
        "text_en": "\"We will always be friends,\" promised Spark. \"Every time you look at the stars, I will be thinking of you.\"",
        "prompt": "ACTION: @image1 hugs @image2 warmly with a loving tender expression, @image2 nuzzles into the hug with loving golden eyes, sparkles and hearts float around them. SETTING: Magical garden gate WIDE VIEW, beautiful starry night sky, fireflies glowing, warm emotional atmosphere. ATMOSPHERE: Love and friendship, hearts and sparkles. {style}",
        "text_position": "split"
    },
    {
        "id": 19,
        "text_es": "{name} volvió a casa bajo las estrellas, pero el Jardín del Dragón siempre vivirá en su corazón. Y colorín colorado, este cuento mágico ha terminado.",
        "text_en": "{name} returned home under the stars, but the Dragon Garden will always live in their heart. And they lived happily ever after. The End.",
        "prompt": "ACTION: @image1 walks home on a winding path through a meadow with a warm smile, looking back over one shoulder waving goodbye. SETTING: Winding path WIDE VIEW, beautiful starry night sky, cozy cottage with warm lights in windows, fireflies glowing, magical atmosphere. ATMOSPHERE: Peaceful goodbye, warm starlit night. STRICT: Only @image1 in this scene. {style}",
        "text_position": "split"
    }
]

CLOSING_SCENE = {
    "id": 20,
    "prompt": "ACTION: @image1 sleeps peacefully in a cozy bed with a gentle smile, one hand hugging a small plush dragon toy, on the nightstand a glowing emerald dragon scale shimmers softly. SETTING: Cozy bedroom at night WIDE VIEW, stars through window, soft moonlight, magical sparkles floating gently. ATMOSPHERE: Dreamy peaceful slumber, warm emerald glow. STRICT: Only @image1 in this scene, no companion present. {style}",
    "text_position": "none"
}

FRONT_COVER = {
    "prompt": "ACTION: @image1 sits happily on @image2's back soaring through the sky, arms gently holding @image2, @image2's wings spread wide and flapping, golden sparkles trailing. SETTING: Beautiful sky WIDE VIEW, fluffy pink and white cotton clouds, magnificent rainbow arching, golden sunlight, sparkles trailing, centered composition for book cover. ATMOSPHERE: Adventure invitation, joyful flight, magical. STRICT: ABSOLUTELY NO rendered text, no titles, no logos, no words, no letters, no captions, no watermarks, no signatures, pure illustration only. {style}"
}

BACK_COVER = {
    "prompt": "Disney Pixar 3D style illustration. SETTING: Beautiful magical garden path WIDE VIEW, ancient oak tree, glowing flowers and mushrooms, fireflies, soft ethereal golden light, peaceful dreamy atmosphere. STRICT: NO characters, only scenery. ABSOLUTELY NO rendered text anywhere in the image, no titles, no logos, no words, no letters, no captions, no watermarks, no signatures, pure illustration only. {style}"
}


def get_outfit_desc(gender: str) -> str:
    if gender == "male":
        return "cozy green tunic with brown belt, brown pants and small adventure boots, tiny leaf pendant around neck"
    else:
        return "cozy green dress with brown belt and leaf patterns, comfortable leggings and small adventure boots, tiny leaf pendant around neck"


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


def get_age_body_description(age: int) -> str:
    if age <= 1:
        return "baby with very small round body, extremely chubby cheeks, short stubby limbs, cannot stand alone"
    elif age == 2:
        return "toddler with small round body, very chubby cheeks, short stubby legs, wobbly stance"
    elif age <= 4:
        return "young toddler with small body, round chubby face, short legs, small stature"
    elif age <= 6:
        return "young child with small body proportions, slightly chubby face, short limbs, small height"
    elif age <= 8:
        return "school-age child with taller body, longer limbs, less chubby face, confident posture"
    else:
        return "older child with tall body, long limbs, mature face proportions, confident stance"


def get_hair_texture_description(hair_type: str) -> str:
    if hair_type == 'coily':
        return "afro-textured tightly coiled voluminous"
    elif hair_type == 'curly':
        return "curly with defined spiral curls"
    elif hair_type == 'wavy':
        return "wavy"
    else:
        return "straight"


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


def get_cover_prompts(child_name: str, gender: str, age: int, traits: dict) -> dict:
    return {
        'front': build_scene_prompt(FRONT_COVER, child_name, gender, age, traits),
        'back': build_scene_prompt(BACK_COVER, child_name, gender, age, traits)
    }


def get_all_scene_prompts(child_name: str, gender: str, age: int, traits: dict) -> list:
    prompts = []
    for scene in DRAGON_GARDEN_SCENES:
        prompts.append(build_scene_prompt(scene, child_name, gender, age, traits))
    return prompts
