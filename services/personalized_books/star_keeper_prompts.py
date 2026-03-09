# Star Keeper - Personalized Book Prompts
# 19 scenes + closing + covers with LUNA star companion
# Ages 6-8 - Stars, bravery & light theme
#
# FLUX 2 Dev with reference image flow:
#   1. Preview: detailed character description → generates reference image
#   2. Scenes: FLUX 2 Dev takes reference image → prompts use SAME schema as Magic Inventor
#      Only needs {hair_desc}, {eye_desc}, {skin_tone} as brief hints (NOT full char_base)
#
# Schema (identical to Magic Inventor):
#   CHARACTER → OUTFIT → [COMPANION] → ACTION → SETTING → ATMOSPHERE → STRICT
#
# Rules:
#   - guidance_scale=3.5, num_inference_steps=28, aspect_ratio=3:4
#   - Keep prompts concise - FLUX 2 Dev loses focus with >300 words
#   - Style: Disney Pixar 3D everywhere, NO watercolor
#   - NEVER say child "flies" or "soars" - FLUX gives child wings

STYLE_BASE = "Disney Pixar 3D style, soft luminous deep blue and violet tones with golden and silver sparkles, warm moonlight and starlight glow, WIDE SHOT full body from head to feet, characters occupy 40% of frame, environment visible, clean illustration only, NO text, NO watermarks."

LUNA_INLINE = "LUNA: a small cute five-pointed star shape the size of a child's hand, solid shimmering silver-white, two big expressive violet eyes on the star face, tiny translucent wings on the sides, soft silver glow"

STAR_KEEPER_SCENES = [
    {
        "id": 1,
        "text_es": "En lo alto de un acantilado frente al mar, {name} descubrió un viejo faro abandonado. Su puerta se abrió sola, invitándole a entrar con un resplandor azul misterioso.",
        "text_en": "On a clifftop overlooking the sea, {name} discovered an old abandoned lighthouse. Its door opened by itself, inviting them inside with a mysterious blue glow.",
        "prompt": "Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, eyes wide with wonder. OUTFIT: {outfit_desc}. ACTION: {gender_word} stands in front of the glowing lighthouse door, one hand reaching toward the handle, golden-blue particles streaming from inside. SETTING: Dramatic clifftop WIDE VIEW, old stone lighthouse, wooden door glowing with mysterious blue light, stars in purple sky, crashing waves far below. ATMOSPHERE: Mystery and discovery, blue magical glow. STRICT: Only ONE {gender_word}, NO star companion, {gender_word} is 100% human child, no duplicates. {style}",
        "text_position": "split"
    },
    {
        "id": 2,
        "text_es": "Dentro del faro había un telescopio gigante cubierto de polvo de estrellas. Al tocarlo, el techo se abrió revelando un cielo nocturno lleno de constelaciones brillantes.",
        "text_en": "Inside the lighthouse was a giant telescope covered in stardust. When {name} touched it, the roof opened up revealing a night sky full of brilliant constellations.",
        "prompt": "Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, mouth open in amazement looking upward. OUTFIT: {outfit_desc}. ACTION: {gender_word} touches a magnificent brass telescope covered in silver stardust, ceiling splits open revealing starry sky with bright constellations. SETTING: Circular lighthouse room WIDE VIEW, old star maps on shelves, stardust particles floating, candlelight mixing with starlight. ATMOSPHERE: Awe and discovery, silver stardust. STRICT: Only ONE {gender_word}, NO star companion, {gender_word} is 100% human child, no duplicates. {style}",
        "text_position": "split"
    },
    {
        "id": 3,
        "text_es": "De pronto, una pequeña estrella cayó del cielo y aterrizó suavemente en las manos de {name}. \"¡Hola! Soy LUNA\", susurró con voz dulce y cristalina.",
        "text_en": "Suddenly, a small star fell from the sky and landed softly in {name}'s hands. \"Hello! I'm LUNA,\" it whispered with a sweet, crystal-clear voice.",
        "prompt": "Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, gentle amazed smile, face lit by silver light. OUTFIT: {outfit_desc}. COMPANION: {LUNA_INLINE}. ACTION: {gender_word} holds cupped hands forward, LUNA rests in the child's cupped hands looking up with violet eyes, trail of silver light from the sky above. SETTING: Inside lighthouse WIDE VIEW, open ceiling showing starry sky, stardust particles settling. ATMOSPHERE: Magical first meeting, warm silver light. STRICT: Only ONE {gender_word}, only ONE small star LUNA, {gender_word} is 100% human child, no duplicates, NO wings on {gender_word}. {style}",
        "text_position": "split"
    },
    {
        "id": 4,
        "text_es": "LUNA le explicó que las estrellas se estaban apagando porque el Gran Reloj Celestial se había detenido. Sin él, la noche perdería toda su luz para siempre.",
        "text_en": "LUNA explained that the stars were going out because the Great Celestial Clock had stopped. Without it, the night would lose all its light forever.",
        "prompt": "Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, concerned and determined expression. OUTFIT: {outfit_desc}. COMPANION: {LUNA_INLINE}. ACTION: {gender_word} looks up at the darkening sky, LUNA floats at eye level beside the child. SETTING: Lighthouse interior WIDE VIEW, through open ceiling several stars visibly dimming and going dark, dark patches in the sky, faint outline of a celestial clock among clouds. ATMOSPHERE: Somber determination, fading starlight. STRICT: Only ONE {gender_word}, only ONE small star LUNA, {gender_word} is 100% human child, no duplicates, NO wings on {gender_word}. {style}",
        "text_position": "split"
    },
    {
        "id": 5,
        "text_es": "\"¡Necesito tu ayuda!\", pidió LUNA. El telescopio brilló y se convirtió en un puente de luz que ascendía hacia las nubes. {name} dio el primer paso con valentía.",
        "text_en": "\"I need your help!\" LUNA pleaded. The telescope glowed and became a bridge of light rising into the clouds. {name} took the first brave step.",
        "prompt": "Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, determined courageous expression. OUTFIT: {outfit_desc}. COMPANION: {LUNA_INLINE}. ACTION: {gender_word} walks onto a magnificent bridge made of golden-silver light, one foot stepping forward bravely, LUNA floats just ahead on the bridge. SETTING: Bridge of light WIDE VIEW, solid glowing bridge curving upward from lighthouse into the clouds, sparkling particles along edges like handrails. ATMOSPHERE: Courage and adventure, dramatic upward perspective. STRICT: Only ONE {gender_word}, only ONE small star LUNA, {gender_word} is 100% human child WALKING on bridge, no duplicates, NO wings on {gender_word}, NO flying. {style}",
        "text_position": "split"
    },
    {
        "id": 6,
        "text_es": "El puente los llevó al Jardín de las Luciérnagas, un campo flotante donde miles de luciérnagas gigantes iluminaban flores que crecían entre las nubes.",
        "text_en": "The bridge led them to the Firefly Garden, a floating meadow where thousands of giant fireflies illuminated flowers that grew among the clouds.",
        "prompt": "Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, expression of pure wonder, face lit by firefly light. OUTFIT: {outfit_desc}. COMPANION: {LUNA_INLINE}. ACTION: {gender_word} walks through floating garden touching a giant glowing flower, LUNA floats among the fireflies nearby. SETTING: Floating meadow WIDE VIEW, suspended among pink and blue clouds, thousands of giant fireflies like lanterns, enormous luminous flowers in purple blue and silver. ATMOSPHERE: Ethereal wonder, warm golden-green light. STRICT: Only ONE {gender_word}, only ONE small star LUNA, {gender_word} is 100% human child, no duplicates, NO wings on {gender_word}. {style}",
        "text_position": "split"
    },
    {
        "id": 7,
        "text_es": "Las luciérnagas les entregaron la primera Llave Estelar, una llave dorada hecha de luz concentrada. \"Necesitan tres llaves para el Gran Reloj\", explicaron.",
        "text_en": "The fireflies gave them the first Star Key, a golden key made of concentrated light. \"You'll need three keys for the Great Clock,\" they explained.",
        "prompt": "Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, face illuminated by golden key light, expression of reverent awe. OUTFIT: {outfit_desc}. COMPANION: {LUNA_INLINE}. ACTION: {gender_word} reaches up with both hands to receive a floating golden key made of concentrated light, LUNA hovers beside the key. SETTING: Firefly garden center WIDE VIEW, circle of giant fireflies forming ring of golden light, magnificent golden key rotating slowly in center, sparkles. ATMOSPHERE: Ceremonial wonder, golden radiance. STRICT: Only ONE {gender_word}, only ONE small star LUNA, {gender_word} is 100% human child, no duplicates, NO wings on {gender_word}. {style}",
        "text_position": "split"
    },
    {
        "id": 8,
        "text_es": "{name} y LUNA navegaron en un barco hecho de rayos de luna sobre el Río de Estrellas Fugaces. Cada estrella que pasaba dejaba un rastro de deseos brillantes.",
        "text_en": "{name} and LUNA sailed in a boat made of moonbeams across the River of Shooting Stars. Each passing star left a trail of glowing wishes.",
        "prompt": "Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, joyful amazed expression, one hand trailing in starlight river. OUTFIT: {outfit_desc}. COMPANION: {LUNA_INLINE}. ACTION: {gender_word} sits in a moonbeam boat, LUNA perches on the bow of the boat. SETTING: Luminous river WIDE VIEW, flowing liquid starlight in deep blue and silver, small elegant boat of solid moonbeams, shooting stars zooming past leaving golden trails. ATMOSPHERE: Celestial sailing, breathtaking starlight. STRICT: Only ONE {gender_word}, only ONE small star LUNA, {gender_word} is 100% human child, no duplicates, NO wings on {gender_word}. {style}",
        "text_position": "split"
    },
    {
        "id": 9,
        "text_es": "Al final del río encontraron la Cueva de los Ecos de Luz. Dentro, los sonidos se convertían en colores y las palabras amables creaban arcoíris pequeños.",
        "text_en": "At the end of the river they found the Cave of Light Echoes. Inside, sounds turned into colors and kind words created tiny rainbows.",
        "prompt": "Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, delighted surprise, hands cupped around mouth speaking. OUTFIT: {outfit_desc}. COMPANION: {LUNA_INLINE}. ACTION: {gender_word} speaks watching colorful ribbons of light emerge from words, LUNA floats nearby surrounded by tiny rainbows. SETTING: Crystal cave interior WIDE VIEW, walls of translucent amethyst and quartz, swirling ribbons of color pink gold blue green, tiny rainbows forming. ATMOSPHERE: Ethereal wonder, prismatic colors. STRICT: Only ONE {gender_word}, only ONE small star LUNA, {gender_word} is 100% human child, no duplicates, NO wings on {gender_word}. {style}",
        "text_position": "split"
    },
    {
        "id": 10,
        "text_es": "{name} dijo \"te quiero\" y un arcoíris brillante formó la segunda Llave Estelar. LUNA aplaudió con sus pequeñas alas, dejando un rastro de polvo plateado.",
        "text_en": "{name} said \"I love you\" and a brilliant rainbow formed the second Star Key. LUNA clapped her tiny wings, leaving a trail of silver dust.",
        "prompt": "Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, expression of love and joy, one hand over heart. OUTFIT: {outfit_desc}. COMPANION: {LUNA_INLINE}. ACTION: {gender_word} reaches toward a rainbow key forming in the air, LUNA floats beside glowing joyfully. SETTING: Crystal cave WIDE VIEW, rainbow spiraling and condensing into a Star Key of rainbow-colored light, cave crystals resonating with rainbow colors. ATMOSPHERE: Love and warmth, emotional magic. STRICT: Only ONE {gender_word}, only ONE small star LUNA, {gender_word} is 100% human child, no duplicates, NO wings on {gender_word}. {style}",
        "text_position": "split"
    },
    {
        "id": 11,
        "text_es": "Llegaron al Bosque de Cristal, donde los árboles eran de hielo transparente y reflejaban mil versiones del cielo estrellado en cada rama y hoja.",
        "text_en": "They reached the Crystal Forest, where the trees were made of transparent ice and reflected a thousand versions of the starry sky in every branch and leaf.",
        "prompt": "Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, mesmerized peaceful expression, touching a crystal tree trunk. OUTFIT: {outfit_desc}. COMPANION: {LUNA_INLINE}. ACTION: {gender_word} walks along crystal path touching a crystal tree, LUNA floats ahead glowing softly. SETTING: Enchanting crystal forest WIDE VIEW, tall trees of transparent crystal ice, each branch a prism refracting starlight, frost-covered ground glittering. ATMOSPHERE: Frozen magical wonder, cool blue and silver. STRICT: Only ONE {gender_word}, only ONE small star LUNA, {gender_word} is 100% human child, no duplicates, NO wings on {gender_word}. {style}",
        "text_position": "split"
    },
    {
        "id": 12,
        "text_es": "En el centro del bosque, un lobo de constelaciones cuidaba la tercera Llave Estelar. \"Solo quien tenga corazón valiente puede llevarla\", dijo con voz profunda.",
        "text_en": "In the heart of the forest, a wolf made of constellations guarded the third Star Key. \"Only a brave heart may carry it,\" the wolf said in a deep voice.",
        "prompt": "Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, mix of awe and determination, standing tall. OUTFIT: {outfit_desc}. COMPANION: {LUNA_INLINE}. ACTION: {gender_word} faces the constellation wolf bravely, LUNA hovers close to the child's shoulder. SETTING: Crystal forest clearing WIDE VIEW, magnificent wolf made of connected constellation stars with lines of starlight, third Star Key floating above its head in silver light. ATMOSPHERE: Dramatic celestial guardian, moonlit. STRICT: Only ONE {gender_word}, only ONE small star LUNA, {gender_word} is 100% human child, no duplicates, NO wings on {gender_word}. {style}",
        "text_position": "split"
    },
    {
        "id": 13,
        "text_es": "{name} caminó hacia el lobo sin miedo y le acarició la cabeza de estrellas. El lobo sonrió y entregó la última llave con una reverencia elegante.",
        "text_en": "{name} walked up to the wolf without fear and stroked its head of stars. The wolf smiled and handed over the last key with an elegant bow.",
        "prompt": "Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, expression of gentle courage and kindness. OUTFIT: {outfit_desc}. COMPANION: {LUNA_INLINE}. ACTION: {gender_word} gently strokes the constellation wolf's forehead, wolf bowing its head, silver Star Key descending, LUNA watches nearby. SETTING: Crystal forest clearing WIDE VIEW, constellation wolf bowing its starry head, warm golden glow where child and wolf connect. ATMOSPHERE: Tender courage, peaceful connection. STRICT: Only ONE {gender_word}, only ONE small star LUNA, {gender_word} is 100% human child, no duplicates, NO wings on {gender_word}. {style}",
        "text_position": "split"
    },
    {
        "id": 14,
        "text_es": "Con las tres Llaves Estelares brillando en sus manos, {name} y LUNA volaron hacia la Torre del Cielo, una torre infinita hecha enteramente de luz de luna.",
        "text_en": "With the three Star Keys glowing in their hands, {name} and LUNA flew toward the Sky Tower, an infinite tower made entirely of moonlight.",
        "prompt": "Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, determined joy and excitement. OUTFIT: {outfit_desc}. COMPANION: {LUNA_INLINE}. ACTION: {gender_word} stands on a rising platform of starlight ascending toward the tower, three glowing keys orbiting around, LUNA floats alongside. SETTING: Impossibly tall moonlight tower WIDE VIEW, stretching into starry sky, glowing silver-white, spiral staircase visible, clouds parting. ATMOSPHERE: Epic cosmic scale, breathtaking adventure. STRICT: Only ONE {gender_word}, only ONE small star LUNA, {gender_word} is 100% human child STANDING on platform, no duplicates, NO wings on {gender_word}, NO flying. {style}",
        "text_position": "split"
    },
    {
        "id": 15,
        "text_es": "En la cima de la torre encontraron el Gran Reloj Celestial. Era enorme, con engranajes de plata y manecillas hechas de rayos de sol y luna entrelazados.",
        "text_en": "At the top of the tower they found the Great Celestial Clock. It was enormous, with silver gears and hands made of intertwined sun and moonbeams.",
        "prompt": "Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, expression of awe looking up. OUTFIT: {outfit_desc}. COMPANION: {LUNA_INLINE}. ACTION: {gender_word} stands at the base of the enormous clock looking up, three Star Keys floating around, LUNA hovers near the clock face. SETTING: Tower top chamber WIDE VIEW, Great Celestial Clock with massive silver gears, clock hands of intertwined golden sunbeams and silver moonbeams, three keyhole slots glowing. ATMOSPHERE: Cosmic majesty, silver and gold. STRICT: Only ONE {gender_word}, only ONE small star LUNA, {gender_word} is 100% human child, no duplicates, NO wings on {gender_word}. {style}",
        "text_position": "split"
    },
    {
        "id": 16,
        "text_es": "{name} colocó las tres llaves en el reloj. Los engranajes comenzaron a girar y una onda de luz dorada y plateada se expandió por todo el cielo nocturno.",
        "text_en": "{name} placed the three keys into the clock. The gears began to turn and a wave of golden and silver light expanded across the entire night sky.",
        "prompt": "Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, expression of triumph and pure joy, arms raised. OUTFIT: {outfit_desc}. COMPANION: {LUNA_INLINE}. ACTION: {gender_word} stands with arms raised having placed the last key, LUNA hovers nearby glowing bright. SETTING: Great Celestial Clock WIDE VIEW, three Star Keys inserted and glowing in keyholes, massive gears turning with golden sparks, wave of golden and silver light radiating outward. ATMOSPHERE: Triumphant cosmic energy burst. STRICT: Only ONE {gender_word}, only ONE small star LUNA, {gender_word} is 100% human child, no duplicates, NO wings on {gender_word}. {style}",
        "text_position": "split"
    },
    {
        "id": 17,
        "text_es": "¡Las estrellas volvieron a brillar! Miles de estrellas se encendieron una por una, y el cielo se llenó de constelaciones más hermosas que nunca, bailando en la oscuridad.",
        "text_en": "The stars shone again! Thousands of stars lit up one by one, and the sky filled with constellations more beautiful than ever, dancing in the darkness.",
        "prompt": "Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, pure happiness, arms spread wide, face turned upward. OUTFIT: {outfit_desc}. COMPANION: {LUNA_INLINE}. ACTION: {gender_word} stands at the tower edge celebrating with arms wide, LUNA beside spinning with joy. SETTING: Tower top WIDE VIEW, spectacular panoramic night sky, thousands of distant stars reigniting in cascading waves, constellations forming, Milky Way blazing. ATMOSPHERE: Joyous cosmic celebration. STRICT: Only ONE {gender_word}, only ONE small star LUNA, {gender_word} is 100% human child, no duplicates, NO wings on {gender_word}. {style}",
        "text_position": "split"
    },
    {
        "id": 18,
        "text_es": "\"Siempre que mires al cielo, recuerda que tú salvaste las estrellas\", susurró LUNA, brillando más fuerte que nunca. \"La luz más poderosa vive en tu corazón.\"",
        "text_en": "\"Whenever you look at the sky, remember that you saved the stars,\" LUNA whispered, shining brighter than ever. \"The most powerful light lives in your heart.\"",
        "prompt": "Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, kneeling, loving grateful eyes. OUTFIT: {outfit_desc}. COMPANION: {LUNA_INLINE}. ACTION: {gender_word} kneels holding cupped hands with LUNA close to chest at heart level, LUNA nestled in hands glowing brightest ever. SETTING: Lighthouse doorway WIDE VIEW, warm golden-silver light from inside, magnificent repaired starry sky above. ATMOSPHERE: Heartfelt farewell, love and gratitude. STRICT: Only ONE {gender_word}, only ONE small star LUNA, {gender_word} is 100% human child, no duplicates, NO wings on {gender_word}. {style}",
        "text_position": "split"
    },
    {
        "id": 19,
        "text_es": "{name} volvió a casa abrazando la luz de LUNA en su pecho. Desde esa noche, una estrella nueva brilla en el cielo con el nombre de un guardián muy especial. Y colorín colorado, este cuento estelar ha terminado.",
        "text_en": "{name} returned home holding LUNA's light close to their heart. From that night on, a new star shines in the sky bearing the name of a very special guardian. And they all lived happily ever after. The End.",
        "prompt": "Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, warm grateful smile, looking back over shoulder waving goodbye. OUTFIT: {outfit_desc}. ACTION: {gender_word} walks along a path toward home, one hand pressed to chest holding a warm silver glow. SETTING: Winding path WIDE VIEW, lighthouse visible on cliff in background, warm sunset-to-night sky, brilliant stars, one special star shining extra bright above, fireflies accompanying. ATMOSPHERE: Peaceful magical homecoming, warm starlit night. STRICT: Only ONE {gender_word}, NO star companion, {gender_word} is 100% human child, no duplicates, NO wings on {gender_word}. {style}",
        "text_position": "bottom"
    }
]

CLOSING_SCENE = {
    "id": 20,
    "prompt": "Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, sleeping peacefully with gentle smile. OUTFIT: Cozy dark blue pajamas with tiny star patterns. ACTION: {gender_word} sleeps in a cozy bed, one hand resting near a glowing star-shaped nightlight on the bedside table, telescope toy on shelf, star and moon decorations hanging from ceiling. SETTING: Cozy bedroom at night WIDE VIEW, magnificent starry sky through large window, one star shining brighter than all others, warm soft lighting. ATMOSPHERE: Dreamy peaceful slumber, silver-violet glow. STRICT: Only ONE {gender_word}, NO real star companion, only nightlight, {gender_word} is 100% human child. {style}",
    "text_position": "none"
}

FRONT_COVER = {
    "prompt": "Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, big joyful confident smile, one hand reaching toward the stars. OUTFIT: {outfit_desc}. COMPANION: {LUNA_INLINE}. ACTION: {gender_word} stands confidently at the lighthouse entrance, LUNA hovers beside the child's shoulder glowing brightly. SETTING: Old stone lighthouse on dramatic clifftop WIDE VIEW, magnificent starry sky with bright constellations and shooting stars, ocean waves crashing below, warm golden-blue light from lighthouse door, centered composition for book cover. ATMOSPHERE: Adventure invitation, celestial magic. STRICT: Only ONE {gender_word}, only ONE small star LUNA, {gender_word} is 100% human child, no duplicates, NO wings on {gender_word}. ABSOLUTELY NO rendered text anywhere in the image, no titles, no logos, no words, no letters, no captions, no watermarks, no signatures, pure illustration only. {style}"
}

BACK_COVER = {
    "prompt": "Disney Pixar 3D style illustration. SETTING: Old stone lighthouse on clifftop WIDE VIEW, seen from distance at night, lighthouse beam sweeping across magnificent starry sky, ocean waves gently crashing on rocks, moonlight path on water surface, fireflies dotting cliff grass, one special star shining brighter above lighthouse. STRICT: NO characters, only scenery. ABSOLUTELY NO rendered text anywhere in the image, no titles, no logos, no words, no letters, no captions, no watermarks, no signatures, pure illustration only. {style}"
}


def get_outfit_desc(gender: str) -> str:
    if gender == "male":
        return "a deep blue explorer jacket with silver star buttons over a white shirt, dark pants and sturdy boots, a small silver compass pendant around neck"
    else:
        return "a deep blue explorer jacket with silver star buttons over a lavender shirt, comfortable dark pants and sturdy boots, a small silver compass pendant around neck"


def get_hair_action(traits: dict) -> str:
    hair_length = traits.get('hair_length', 'medium')
    if hair_length == 'long':
        return "long hair flowing beautifully in the starlight breeze"
    elif hair_length == 'short':
        return "short hair ruffled by the gentle night wind"
    else:
        return "hair gently moving in the celestial breeze"


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
    prompt = prompt.replace('{LUNA_INLINE}', LUNA_INLINE)
    prompt = prompt.replace('{style}', STYLE_BASE)
    prompt = prompt.replace('{name}', child_name)
    prompt = prompt.replace('{child_name}', child_name)

    from services.fixed_stories import enforce_gender_clothing
    prompt = enforce_gender_clothing(prompt, gender)

    return prompt


def get_all_scene_prompts(child_name: str, gender: str, age: int, traits: dict) -> list:
    prompts = []
    for scene in STAR_KEEPER_SCENES:
        prompts.append(build_scene_prompt(scene, child_name, gender, age, traits))
    return prompts
