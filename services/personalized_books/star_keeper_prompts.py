# Star Keeper - Personalized Book Prompts
# Reference-image flow: @image1 = child character portrait, @image2 = LUNA star companion
#
# Prompts contain ONLY action + setting — NO character physical descriptions.
# All appearance (face, hair, skin, outfit) comes from the reference images.
#
# Reference note is prepended by generate_scene_complete:
#   "@image1=child character — copy face, hair, skin, and outfit exactly.
#    @image2=small star companion — copy appearance exactly."
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
#   - NEVER say @image1 "flies" or "soars" (gives wings)
#   - Scenes 1, 2, 19 and CLOSING have no @image2

STYLE_BASE = "Disney Pixar 3D style, soft luminous deep blue and violet tones with golden and silver sparkles, warm moonlight and starlight glow, full body visible from head to feet, character placed prominently in foreground, spectacular environment fills the background, clean illustration only, NO text, NO watermarks."

LUNA_INLINE = "LUNA: a small cute five-pointed star shape the size of a child's hand, solid shimmering silver-white, two big expressive violet eyes on the star face, tiny translucent wings on the sides, soft silver glow"

STAR_KEEPER_SCENES = [
    {
        "id": 1,
        "text_es": "En lo alto de un acantilado frente al mar, {name} descubrió un viejo faro abandonado. Su puerta se abrió sola, invitándole a entrar con un resplandor azul misterioso.",
        "text_en": "On a clifftop overlooking the sea, {name} discovered an old abandoned lighthouse. Its door opened by itself, inviting them inside with a mysterious blue glow.",
        "prompt": "ACTION: @image1 stands before the lighthouse entrance and reaches one hand toward the glowing door handle, eyes wide with wonder. SETTING: Old stone lighthouse on a dramatic clifftop WIDE VIEW, wooden door radiating mysterious blue light from inside, deep purple starry sky, ocean waves crashing far below. ATMOSPHERE: Mystery and discovery, blue magical glow. STRICT: Only @image1 in this scene. {style}",
        "text_position": "split"
    },
    {
        "id": 2,
        "text_es": "Dentro del faro había un telescopio gigante cubierto de polvo de estrellas. Al tocarlo, el techo se abrió revelando un cielo nocturno lleno de constelaciones brillantes.",
        "text_en": "Inside the lighthouse was a giant telescope covered in stardust. When {name} touched it, the roof opened up revealing a night sky full of brilliant constellations.",
        "prompt": "ACTION: @image1 touches a magnificent brass telescope covered in silver stardust as the ceiling splits open above revealing the starry sky. SETTING: Circular lighthouse room WIDE VIEW, old star maps on shelves, stardust particles floating, candlelight mixing with starlight streaming from the open ceiling. ATMOSPHERE: Awe and discovery, silver stardust. STRICT: Only @image1 in this scene. {style}",
        "text_position": "split"
    },
    {
        "id": 3,
        "text_es": "De pronto, una pequeña estrella cayó del cielo y aterrizó suavemente en las manos de {name}. \"¡Hola! Soy LUNA\", susurró con voz dulce y cristalina.",
        "text_en": "Suddenly, a small star fell from the sky and landed softly in {name}'s hands. \"Hello! I'm LUNA,\" it whispered with a sweet, crystal-clear voice.",
        "prompt": "ACTION: @image1 holds cupped hands forward with a look of gentle amazement, @image2 rests in the cupped hands looking upward, trail of silver light descending from the open ceiling above. SETTING: Inside lighthouse WIDE VIEW, open ceiling showing starry sky, silver stardust particles settling around both characters. ATMOSPHERE: Magical first meeting, warm silver light. {style}",
        "text_position": "split"
    },
    {
        "id": 4,
        "text_es": "LUNA le explicó que las estrellas se estaban apagando porque el Gran Reloj Celestial se había detenido. Sin él, la noche perdería toda su luz para siempre.",
        "text_en": "LUNA explained that the stars were going out because the Great Celestial Clock had stopped. Without it, the night would lose all its light forever.",
        "prompt": "ACTION: @image1 looks upward at the darkening sky with a concerned determined expression, @image2 floats at eye level beside @image1. SETTING: Lighthouse interior WIDE VIEW, open ceiling revealing a sky with several stars visibly dimming and going dark, faint outline of a celestial clock among clouds. ATMOSPHERE: Somber determination, fading starlight. {style}",
        "text_position": "split"
    },
    {
        "id": 5,
        "text_es": "\"¡Necesito tu ayuda!\", pidió LUNA. El telescopio brilló y se convirtió en un puente de luz que ascendía hacia las nubes. {name} dio el primer paso con valentía.",
        "text_en": "\"I need your help!\" LUNA pleaded. The telescope glowed and became a bridge of light rising into the clouds. {name} took the first brave step.",
        "prompt": "ACTION: @image1 steps bravely forward onto a shimmering bridge of golden-silver light, @image2 floats just ahead on the bridge leading the way. SETTING: Bridge of light WIDE VIEW, solid glowing bridge of golden-silver particles curving upward from the lighthouse into the clouds, sparkles along the edges like handrails. ATMOSPHERE: Courage and adventure, dramatic upward perspective. {style}",
        "text_position": "split"
    },
    {
        "id": 6,
        "text_es": "El puente los llevó al Jardín de las Luciérnagas, un campo flotante donde miles de luciérnagas gigantes iluminaban flores que crecían entre las nubes.",
        "text_en": "The bridge led them to the Firefly Garden, a floating meadow where thousands of giant fireflies illuminated flowers that grew among the clouds.",
        "prompt": "ACTION: @image1 walks through the floating garden touching a giant glowing flower with one hand, @image2 floats among glowing fireflies nearby. SETTING: Floating meadow WIDE VIEW, suspended among pink and blue clouds, thousands of giant fireflies like golden lanterns, enormous luminous flowers in purple blue and silver. ATMOSPHERE: Ethereal wonder, warm golden-green light. {style}",
        "text_position": "split"
    },
    {
        "id": 7,
        "text_es": "Las luciérnagas les entregaron la primera Llave Estelar, una llave dorada hecha de luz concentrada. \"Necesitan tres llaves para el Gran Reloj\", explicaron.",
        "text_en": "The fireflies gave them the first Star Key, a golden key made of concentrated light. \"You'll need three keys for the Great Clock,\" they explained.",
        "prompt": "ACTION: @image1 reaches up with both hands to receive a floating golden key made of concentrated light, @image2 hovers beside the key. SETTING: Firefly garden center WIDE VIEW, circle of giant fireflies forming a ring of golden light, magnificent golden key rotating slowly in the center surrounded by sparkles. ATMOSPHERE: Ceremonial wonder, golden radiance. {style}",
        "text_position": "split"
    },
    {
        "id": 8,
        "text_es": "{name} y LUNA navegaron en un barco hecho de rayos de luna sobre el Río de Estrellas Fugaces. Cada estrella que pasaba dejaba un rastro de deseos brillantes.",
        "text_en": "{name} and LUNA sailed in a boat made of moonbeams across the River of Shooting Stars. Each passing star left a trail of glowing wishes.",
        "prompt": "ACTION: @image1 sits in a moonbeam boat with one hand trailing in the starlight river, @image2 perches on the bow of the boat. SETTING: Luminous river WIDE VIEW, flowing liquid starlight in deep blue and silver, elegant boat of solid moonbeams, shooting stars zooming past leaving golden trails. ATMOSPHERE: Celestial sailing, breathtaking starlight. {style}",
        "text_position": "split"
    },
    {
        "id": 9,
        "text_es": "Al final del río encontraron la Cueva de los Ecos de Luz. Dentro, los sonidos se convertían en colores y las palabras amables creaban arcoíris pequeños.",
        "text_en": "At the end of the river they found the Cave of Light Echoes. Inside, sounds turned into colors and kind words created tiny rainbows.",
        "prompt": "ACTION: @image1 cups hands around mouth and speaks, watching colorful ribbons of light emerge, @image2 floats nearby surrounded by tiny rainbows. SETTING: Crystal cave interior WIDE VIEW, walls of translucent amethyst and quartz, swirling ribbons of color in pink gold blue and green, tiny rainbows forming everywhere. ATMOSPHERE: Ethereal wonder, prismatic colors. {style}",
        "text_position": "split"
    },
    {
        "id": 10,
        "text_es": "{name} dijo \"te quiero\" y un arcoíris brillante formó la segunda Llave Estelar. LUNA aplaudió con sus pequeñas alas, dejando un rastro de polvo plateado.",
        "text_en": "{name} said \"I love you\" and a brilliant rainbow formed the second Star Key. LUNA clapped her tiny wings, leaving a trail of silver dust.",
        "prompt": "ACTION: @image1 stands with one hand over heart reaching toward a rainbow condensing into a star key in the air, @image2 floats beside glowing with joy. SETTING: Crystal cave WIDE VIEW, rainbow spiraling and condensing into a star key of rainbow-colored light, cave crystals resonating with vibrant colors. ATMOSPHERE: Love and warmth, emotional magic. {style}",
        "text_position": "split"
    },
    {
        "id": 11,
        "text_es": "Llegaron al Bosque de Cristal, donde los árboles eran de hielo transparente y reflejaban mil versiones del cielo estrellado en cada rama y hoja.",
        "text_en": "They reached the Crystal Forest, where the trees were made of transparent ice and reflected a thousand versions of the starry sky in every branch and leaf.",
        "prompt": "ACTION: @image1 walks along a crystal path touching a crystal tree trunk, @image2 floats just ahead glowing softly. SETTING: Enchanting crystal forest WIDE VIEW, tall trees of transparent crystal ice, each branch a prism refracting starlight into rainbow colors, frost-covered ground glittering silver and blue. ATMOSPHERE: Frozen magical wonder, cool blue and silver tones. {style}",
        "text_position": "split"
    },
    {
        "id": 12,
        "text_es": "En el centro del bosque, un lobo de constelaciones cuidaba la tercera Llave Estelar. \"Solo quien tenga corazón valiente puede llevarla\", dijo con voz profunda.",
        "text_en": "In the heart of the forest, a wolf made of constellations guarded the third Star Key. \"Only a brave heart may carry it,\" the wolf said in a deep voice.",
        "prompt": "ACTION: @image1 stands facing a large wolf made of constellation stars with a brave determined expression, @image2 hovers close to @image1's shoulder. SETTING: Crystal forest clearing WIDE VIEW, magnificent wolf formed of connected constellation stars with lines of starlight between them, third star key floating above the wolf's head in silver light. ATMOSPHERE: Dramatic celestial guardian encounter, moonlit. {style}",
        "text_position": "split"
    },
    {
        "id": 13,
        "text_es": "{name} caminó hacia el lobo sin miedo y le acarició la cabeza de estrellas. El lobo sonrió y entregó la última llave con una reverencia elegante.",
        "text_en": "{name} walked up to the wolf without fear and stroked its head of stars. The wolf smiled and handed over the last key with an elegant bow.",
        "prompt": "ACTION: @image1 gently strokes the forehead of the constellation wolf which bows its head, a silver star key descends toward @image1, @image2 watches warmly nearby. SETTING: Crystal forest clearing WIDE VIEW, constellation wolf bowing its starry head, warm golden glow where @image1 and the wolf connect. ATMOSPHERE: Tender courage, peaceful connection. {style}",
        "text_position": "split"
    },
    {
        "id": 14,
        "text_es": "Con las tres Llaves Estelares brillando en sus manos, {name} y LUNA volaron hacia la Torre del Cielo, una torre infinita hecha enteramente de luz de luna.",
        "text_en": "With the three Star Keys glowing in their hands, {name} and LUNA flew toward the Sky Tower, an infinite tower made entirely of moonlight.",
        "prompt": "ACTION: @image1 stands on a rising platform of starlight ascending toward a moonlight tower, three glowing keys orbit around, @image2 floats alongside the platform. SETTING: Impossibly tall tower of moonlight WIDE VIEW, stretching into the starry sky glowing silver-white, spiral staircase visible inside, clouds parting around the base. ATMOSPHERE: Epic cosmic scale, breathtaking adventure. {style}",
        "text_position": "split"
    },
    {
        "id": 15,
        "text_es": "En la cima de la torre encontraron el Gran Reloj Celestial. Era enorme, con engranajes de plata y manecillas hechas de rayos de sol y luna entrelazados.",
        "text_en": "At the top of the tower they found the Great Celestial Clock. It was enormous, with silver gears and hands made of intertwined sun and moonbeams.",
        "prompt": "ACTION: @image1 stands at the base of the enormous clock looking upward in awe, three star keys float around, @image2 hovers near the clock face. SETTING: Tower top chamber WIDE VIEW, Great Celestial Clock with massive silver gears, clock hands of intertwined golden sunbeams and silver moonbeams, three glowing keyhole slots waiting. ATMOSPHERE: Cosmic majesty, silver and gold. {style}",
        "text_position": "split"
    },
    {
        "id": 16,
        "text_es": "{name} colocó las tres llaves en el reloj. Los engranajes comenzaron a girar y una onda de luz dorada y plateada se expandió por todo el cielo nocturno.",
        "text_en": "{name} placed the three keys into the clock. The gears began to turn and a wave of golden and silver light expanded across the entire night sky.",
        "prompt": "ACTION: @image1 stands with arms raised in triumph having just placed the last key in the clock, @image2 hovers nearby glowing intensely bright. SETTING: Great Celestial Clock WIDE VIEW, three star keys inserted and glowing in keyholes, massive gears turning with golden sparks, wave of golden and silver light radiating outward across the sky. ATMOSPHERE: Triumphant cosmic energy burst. {style}",
        "text_position": "split"
    },
    {
        "id": 17,
        "text_es": "¡Las estrellas volvieron a brillar! Miles de estrellas se encendieron una por una, y el cielo se llenó de constelaciones más hermosas que nunca, bailando en la oscuridad.",
        "text_en": "The stars shone again! Thousands of stars lit up one by one, and the sky filled with constellations more beautiful than ever, dancing in the darkness.",
        "prompt": "ACTION: @image1 stands at the tower edge with arms spread wide in pure joy, @image2 spins joyfully beside. SETTING: Tower top WIDE VIEW, spectacular panoramic night sky, thousands of stars reigniting in cascading waves, constellations forming, Milky Way blazing bright. ATMOSPHERE: Joyous cosmic celebration. {style}",
        "text_position": "split"
    },
    {
        "id": 18,
        "text_es": "\"Siempre que mires al cielo, recuerda que tú salvaste las estrellas\", susurró LUNA, brillando más fuerte que nunca. \"La luz más poderosa vive en tu corazón.\"",
        "text_en": "\"Whenever you look at the sky, remember that you saved the stars,\" LUNA whispered, shining brighter than ever. \"The most powerful light lives in your heart.\"",
        "prompt": "ACTION: @image1 kneels holding cupped hands at heart level, @image2 nestled in the cupped hands glowing brightest of all. SETTING: Lighthouse doorway WIDE VIEW, warm golden-silver light spilling from inside the lighthouse, magnificent repaired starry sky filling the view above. ATMOSPHERE: Heartfelt farewell, love and gratitude. {style}",
        "text_position": "split"
    },
    {
        "id": 19,
        "text_es": "{name} volvió a casa abrazando la luz de LUNA en su pecho. Desde esa noche, una estrella nueva brilla en el cielo con el nombre de un guardián muy especial. Y colorín colorado, este cuento estelar ha terminado.",
        "text_en": "{name} returned home holding LUNA's light close to their heart. From that night on, a new star shines in the sky bearing the name of a very special guardian. And they all lived happily ever after. The End.",
        "prompt": "ACTION: @image1 walks along a winding path toward home, one hand pressed to chest holding a soft silver glow, looking back over one shoulder with a warm smile. SETTING: Winding path WIDE VIEW, old lighthouse visible on the cliff in the background, deep night sky full of stars, one special star shining extra bright above, fireflies accompanying. ATMOSPHERE: Peaceful magical homecoming, warm starlit night. STRICT: Only @image1 in this scene. {style}",
        "text_position": "split"
    }
]

CLOSING_SCENE = {
    "id": 20,
    "prompt": "ACTION: @image1 sleeps peacefully in a cozy bed, one hand resting near a glowing star-shaped nightlight on the bedside table. SETTING: Cozy bedroom at night WIDE VIEW, telescope toy on shelf, star and moon decorations hanging from ceiling, magnificent starry sky through a large window with one star shining brighter than all others, warm soft lighting. ATMOSPHERE: Dreamy peaceful slumber, silver-violet glow. STRICT: Only @image1 in this scene, no companion present. {style}",
    "text_position": "none"
}

FRONT_COVER = {
    "prompt": "ACTION: @image1 stands confidently at the lighthouse entrance with one hand reaching upward toward the stars, @image2 hovers beside @image1's shoulder. SETTING: Old stone lighthouse on a dramatic clifftop WIDE VIEW, magnificent starry sky with bright constellations and shooting stars, ocean waves crashing below, warm golden-blue light from the lighthouse door, centered composition for book cover. ATMOSPHERE: Adventure invitation, celestial magic. STRICT: ABSOLUTELY NO rendered text, no titles, no logos, no words, no letters, no captions, no watermarks, no signatures, pure illustration only. {style}"
}

BACK_COVER = {
    "prompt": "SETTING: Old stone lighthouse on clifftop seen from distance at night WIDE VIEW, lighthouse beam sweeping across magnificent starry sky, ocean waves gently crashing on rocks, moonlight path on water surface, fireflies dotting cliff grass, one special star shining brighter above lighthouse. STRICT: NO characters, only scenery. ABSOLUTELY NO rendered text, no titles, no logos, no words, no letters, no captions, no watermarks, no signatures, pure illustration only. {style}"
}


def get_outfit_desc(gender: str) -> str:
    if gender == "male":
        return "a deep blue explorer jacket with silver star buttons over a white shirt, dark pants and sturdy boots, a small silver compass pendant around neck"
    else:
        return "a deep blue explorer jacket with silver star buttons over a lavender shirt, comfortable dark pants and sturdy boots, a small silver compass pendant around neck"


def get_hair_action(traits: dict) -> str:
    hair_length = traits.get('hair_length', 'medium')
    if hair_length in ('bald', 'very_little', 'very_short'):
        return "very short hair neat and still"
    elif hair_length == 'long':
        return "long hair flowing beautifully in the starlight breeze"
    elif hair_length == 'short':
        return "short hair ruffled by the gentle night wind"
    else:
        return "hair gently moving in the celestial breeze"


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


def get_all_scene_prompts(child_name: str, gender: str, age: int, traits: dict) -> list:
    prompts = []
    for scene in STAR_KEEPER_SCENES:
        prompts.append(build_scene_prompt(scene, child_name, gender, age, traits))
    return prompts
