# Magic Chef - Personalized Book Prompts
# 19 scenes + closing + covers with SWEETIE HAT + SWEETIE CAKE companions
# Ages 4-8 - Magical cooking & love theme
#
# FLUX 2 Dev with reference image flow:
#   1. Preview: detailed character description → generates reference image
#   2. Scenes: FLUX 2 Dev takes reference image → prompts use brief hints only
#      Only needs {hair_desc}, {eye_desc}, {skin_tone} as brief hints
#
# Schema (identical to Magic Inventor):
#   CHARACTER → OUTFIT → [COMPANION] → ACTION → SETTING → ATMOSPHERE → STRICT
#
# Special: This book has TWO companion elements:
#   - SWEETIE_HAT: magical chef hat WITH face (worn by child as part of outfit)
#   - SWEETIE_CAKE: living rainbow cake character (separate companion)
#   FLUX 2 Dev supports multiple characters with reference image
#
# Rules:
#   - guidance_scale=3.5, num_inference_steps=28, aspect_ratio=3:4
#   - Keep prompts concise - FLUX 2 Dev loses focus with >300 words
#   - Style: Disney Pixar 3D everywhere, NO watercolor

STYLE_BASE = "Disney Pixar 3D style, soft luminous pastel colors with pink and golden accents, warm kitchen lighting, WIDE SHOT full body from head to feet, characters occupy 40% of frame, environment visible, clean illustration only, NO text, NO watermarks."

SWEETIE_HAT_INLINE = "a magical glowing white chef's hat with cute cartoon eyes and a friendly animated smiling mouth, golden sparkles around it"

SWEETIE_CAKE_INLINE = "SWEETIE: an adorable round rainbow layered cake character with multiple layers of color (pink, blue, yellow, green), big cartoon eyes, a smiling mouth, adorable little arms and legs, NOT a slice but a whole round cake"

MAGIC_CHEF_SCENES = [
    {
        "id": 1,
        "text_es": "Había una vez, en una cocina olvidada en el ático de una casa antigua, un gorro de chef muy especial. Brillaba con luz dorada, esperando a alguien con un corazón lleno de creatividad.",
        "text_en": "Once upon a time, in a forgotten kitchen in the attic of an old house, there was a very special chef's hat. It shimmered with golden light, waiting for someone with a heart full of creativity.",
        "prompt": "Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, expression of enchanting surprise, mouth open in amazement. OUTFIT: a cozy yellow t-shirt with jeans and sneakers. ACTION: {gender_word} stands in an old attic looking at a magical white chef's hat on a table that emits warm golden glow, the hat has friendly cartoon eyes and a kind smile, golden sparkles and stardust float gently. SETTING: Old wooden attic WIDE VIEW, dark beams, warm dusty light, old copper pots and wooden shelves. ATMOSPHERE: Discovery and wonder, warm golden glow. STRICT: Only ONE {gender_word}, {gender_word} is 100% human child, no duplicates, hat is ON the table not on child's head. {style}",
        "text_position": "split"
    },
    {
        "id": 2,
        "text_es": "Cuando {name} se puso el gorro mágico, sintió un cosquilleo especial. \"¡Bienvenido al mundo de la cocina mágica!\", susurró una voz dulce desde el gorro.",
        "text_en": "When {name} put on the magic hat, they felt a special tingle. \"Welcome to the world of magical cooking!\" whispered a sweet voice from the hat.",
        "prompt": "Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, eyes sparkling with excitement, golden sparkles swirling around head. OUTFIT: {sweetie_hat_inline}, and a white chef jacket with golden buttons. ACTION: {gender_word} wears the magical hat on head, the hat's eyes and mouth are animated and talking sweetly, ingredients float around, pots shimmer with golden light. SETTING: Magical kitchen transforming WIDE VIEW, floating ingredients, golden sparkles everywhere. ATMOSPHERE: Magic activation, warm golden shimmer. STRICT: Only ONE {gender_word}, {gender_word} is 100% human child, no duplicates. {style}",
        "text_position": "split"
    },
    {
        "id": 3,
        "text_es": "De pronto, la cocina comenzó a crecer y crecer. ¡Las cucharas eran tan altas como árboles! {name} se había convertido en un pequeño chef en una cocina gigante.",
        "text_en": "Suddenly, the kitchen began to grow and grow. The spoons were as tall as trees! {name} had become a tiny chef in a giant kitchen.",
        "prompt": "Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, looking up in wonder at enormous utensils. OUTFIT: {sweetie_hat_inline}, and a white chef jacket with golden buttons. ACTION: tiny {gender_word} stands looking up at GIANT wooden spoons towering like trees, enormous whisks, massive mixing bowls taller than houses. SETTING: GIANT magical kitchen WIDE VIEW, seen from below, warm kitchen light, sparkles everywhere. ATMOSPHERE: Wonderous scale, magical perspective from below. STRICT: Only ONE {gender_word}, {gender_word} is 100% human child, no duplicates. {style}",
        "text_position": "split"
    },
    {
        "id": 4,
        "text_es": "\"¡Tu primera misión es hacer un pastel de arcoíris!\", dijo el gorro. {name} encontró ingredientes mágicos: harina de estrellas, azúcar de nubes y huevos de sol.",
        "text_en": "\"Your first mission is to make a rainbow cake!\" said the hat. {name} found magical ingredients: star flour, cloud sugar, and sun eggs.",
        "prompt": "Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, holding magical jars with glowing ingredients. OUTFIT: {sweetie_hat_inline} with animated talking mouth, and a white chef jacket with golden buttons. ACTION: {gender_word} holds jars with sparkling star-shaped flour, fluffy white cloud sugar, golden glowing sun eggs, the hat's mouth is animated talking excitedly. SETTING: Magical kitchen WIDE VIEW, floating shelves with glowing ingredient jars, rainbow light effects, sparkles. ATMOSPHERE: Excitement and magic, rainbow sparkles. STRICT: Only ONE {gender_word}, {gender_word} is 100% human child, no duplicates. {style}",
        "text_position": "split"
    },
    {
        "id": 5,
        "text_es": "{name} mezcló los ingredientes con una cuchara mágica que bailaba sola. La masa brillaba con todos los colores del arcoíris mientras se mezclaba.",
        "text_en": "{name} mixed the ingredients with a magic spoon that danced by itself. The batter glowed with all the colors of the rainbow as it mixed.",
        "prompt": "Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, watching in amazement. OUTFIT: {sweetie_hat_inline}, and a white chef jacket with golden buttons and small flour spots. ACTION: {gender_word} watches a magic wooden spoon that stirs itself and dances, rainbow-colored dough swirls and sparkles in a large mixing bowl, musical notes float in the air. SETTING: Magical kitchen WIDE VIEW, large mixing bowl, floating musical notes, sparkles. ATMOSPHERE: Musical magic, rainbow swirls. STRICT: Only ONE {gender_word}, {gender_word} is 100% human child, no duplicates. {style}",
        "text_position": "split"
    },
    {
        "id": 6,
        "text_es": "Cuando el pastel salió del horno, ¡cobró vida! \"¡Hola, chef {name}!\", dijo el pastelito saltando de alegría. \"¡Soy Dulcín, tu ayudante!\"",
        "text_en": "When the cake came out of the oven, it came alive! \"Hello, Chef {name}!\" said the little cake, jumping with joy. \"I'm Sweetie, your helper!\"",
        "prompt": "Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, looking with wonder and joy. OUTFIT: {sweetie_hat_inline}, and a white chef jacket with golden buttons. COMPANION: {SWEETIE_CAKE_INLINE}. ACTION: {gender_word} looks at SWEETIE who jumps with joy near the glowing oven, SWEETIE's arms raised in greeting. SETTING: Warm magical kitchen WIDE VIEW, glowing oven, warm light, sparkles everywhere. ATMOSPHERE: Surprise and delight, warm oven glow. STRICT: Only ONE {gender_word}, only ONE cake character SWEETIE, {gender_word} is 100% human child, no duplicates. {style}",
        "text_position": "split"
    },
    {
        "id": 7,
        "text_es": "Dulcín, el pastelito mágico, mostró a {name} el secreto de la cocina: \"Con amor y creatividad, cualquier receta puede ser extraordinaria.\"",
        "text_en": "Sweetie, the magical cake, showed {name} the secret of cooking: \"With love and creativity, any recipe can be extraordinary.\"",
        "prompt": "Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, kneeling and listening attentively. OUTFIT: {sweetie_hat_inline}, and a white chef jacket with golden buttons. COMPANION: {SWEETIE_CAKE_INLINE}. ACTION: {gender_word} kneels listening to SWEETIE who speaks with wisdom, hearts float in the air between them. SETTING: Warm inviting kitchen WIDE VIEW, pink and red hearts floating, warm golden light. ATMOSPHERE: Love and wisdom, warm kitchen glow. STRICT: Only ONE {gender_word}, only ONE cake character SWEETIE, {gender_word} is 100% human child, no duplicates. {style}",
        "text_position": "split"
    },
    {
        "id": 8,
        "text_es": "Juntos prepararon galletas con forma de estrella que brillaban en la oscuridad. Al morderlas, ¡hacían música!",
        "text_en": "Together they made star-shaped cookies that glowed in the dark. When you bit them, they made music!",
        "prompt": "Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, preparing glittery cookies. OUTFIT: {sweetie_hat_inline}, and a white chef jacket with golden buttons and cookie dough stains. COMPANION: {SWEETIE_CAKE_INLINE}. ACTION: {gender_word} prepares star-shaped cookies that sparkle with golden light, SWEETIE stands on the counter giving instructions. SETTING: Magical kitchen WIDE VIEW, tray of glittery star-shaped cookies, sparkles everywhere. ATMOSPHERE: Creative baking fun, golden sparkles. STRICT: Only ONE {gender_word}, only ONE cake character SWEETIE, {gender_word} is 100% human child, no duplicates. {style}",
        "text_position": "split"
    },
    {
        "id": 9,
        "text_es": "Después crearon un helado de nubes que nunca se derretía y cambiaba de sabor con cada lametón: fresa, chocolate, vainilla...",
        "text_en": "Then they created a cloud ice cream that never melted and changed flavor with each lick: strawberry, chocolate, vanilla...",
        "prompt": "Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, happy with a big smile holding ice cream. OUTFIT: {sweetie_hat_inline}, and a white chef jacket with golden buttons. ACTION: {gender_word} holds a beautiful ice cream cone with soft swirls of strawberry pink, chocolate brown, and vanilla cream. SETTING: Magical cooking station WIDE VIEW, soft pastel colors, golden sparkles floating. ATMOSPHERE: Peaceful sweet magic, pastel warmth. STRICT: Only ONE {gender_word}, {gender_word} is 100% human child, no duplicates. {style}",
        "text_position": "split"
    },
    {
        "id": 10,
        "text_es": "\"¡Chef {name}, hay un concurso de cocina mágica hoy!\", anunció Dulcín emocionado. \"¡Los mejores chefs del mundo mágico competirán!\"",
        "text_en": "\"Chef {name}, there's a magical cooking contest today!\" announced Sweetie excitedly. \"The best chefs from the magical world will compete!\"",
        "prompt": "Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, curiously surprised expression pointing to themselves. OUTFIT: {sweetie_hat_inline}, and a white chef jacket with golden buttons. COMPANION: {SWEETIE_CAKE_INLINE}. ACTION: {gender_word} points to self with surprise, SWEETIE jumps excitedly announcing the news, a golden invitation floats in the air with sparkles. SETTING: Magical kitchen WIDE VIEW, golden invitation floating, sparkles. ATMOSPHERE: Exciting announcement, golden shimmer. STRICT: Only ONE {gender_word}, only ONE cake character SWEETIE, {gender_word} is 100% human child, no duplicates. {style}",
        "text_position": "split"
    },
    {
        "id": 11,
        "text_es": "El concurso era en un castillo hecho completamente de caramelo y chocolate. Las torres eran bastones de caramelo gigantes.",
        "text_en": "The contest was in a castle made entirely of candy and chocolate. The towers were giant candy canes.",
        "prompt": "Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, walking toward the candy castle with wonder. OUTFIT: a fancy white chef's hat with {sweetie_hat_inline} and golden trim, and an elegant white chef jacket with golden buttons. COMPANION: {SWEETIE_CAKE_INLINE}. ACTION: {gender_word} walks toward the candy castle, SWEETIE floats beside the child. SETTING: Magnificent candy castle WIDE VIEW, made of colorful candies and chocolate, candy cane towers, chocolate walls, lollipop decorations, cotton candy clouds. ATMOSPHERE: Sweet fantasy wonder, candy colors. STRICT: Only ONE {gender_word}, only ONE cake character SWEETIE, {gender_word} is 100% human child, no duplicates. {style}",
        "text_position": "split"
    },
    {
        "id": 12,
        "text_es": "Había chefs de todas partes: elfos pasteleros, hadas cocineras y hasta un oso de gomita que hacía pasteles de miel.",
        "text_en": "There were chefs from everywhere: pastry elves, fairy cooks, and even a gummy bear that made honey cakes.",
        "prompt": "Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, at cooking station looking confident. OUTFIT: a fancy white chef's hat with {sweetie_hat_inline} and golden trim, and an elegant white chef jacket with golden buttons. COMPANION: {SWEETIE_CAKE_INLINE}. ACTION: {gender_word} stands at cooking station, SWEETIE stands on the table beside, in background fantasy chef characters: a cute red gummy bear chef, a small fairy chef with wings, a green elf in chef jacket. SETTING: Grand contest kitchen WIDE VIEW, multiple cooking stations. ATMOSPHERE: Exciting competition, warm kitchen glow. STRICT: Only ONE {gender_word}, only ONE cake character SWEETIE, {gender_word} is 100% human child, no duplicates. {style}",
        "text_position": "split"
    },
    {
        "id": 13,
        "text_es": "\"El reto es crear el postre más delicioso del mundo\", anunció la juez, una amable abuelita hecha de mazapán con ojos de caramelo.",
        "text_en": "\"The challenge is to create the most delicious dessert in the world,\" announced the judge, a kind grandmother made of marzipan with candy eyes.",
        "prompt": "Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, looking at the grandmother judge. OUTFIT: a fancy white chef's hat with {sweetie_hat_inline} and golden trim, and an elegant white chef jacket with golden buttons. COMPANION: {SWEETIE_CAKE_INLINE}. ACTION: {gender_word} stands at cooking station, SWEETIE beside, both looking at a kind grandmother judge made entirely of marzipan with candy eyes announcing from a podium. SETTING: Grand contest stage WIDE VIEW, golden decorations, podium. ATMOSPHERE: Dramatic announcement, warm golden light. STRICT: Only ONE {gender_word}, only ONE cake character SWEETIE, {gender_word} is 100% human child, no duplicates. {style}",
        "text_position": "split"
    },
    {
        "id": 14,
        "text_es": "{name} cerró los ojos y pensó en lo que más amaba: su familia, sus amigos, los momentos felices. \"¡Ya sé qué haré!\", exclamó.",
        "text_en": "{name} closed their eyes and thought about what they loved most: family, friends, happy moments. \"I know what I'll make!\" they exclaimed.",
        "prompt": "Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, thoughtful inspired pose with finger on chin. OUTFIT: a fancy white chef's hat with {sweetie_hat_inline} and golden trim, and an elegant white chef jacket with golden buttons. ACTION: {gender_word} stands in thoughtful pose, a thought bubble floats in the air containing a cozy house and loving parent silhouettes, sparkles and hearts surround it. SETTING: Cooking station WIDE VIEW, warm gentle lighting. ATMOSPHERE: Inspiration and love, hearts floating. STRICT: Only ONE {gender_word}, {gender_word} is 100% human child, no duplicates. {style}",
        "text_position": "split"
    },
    {
        "id": 15,
        "text_es": "Con ingredientes mágicos y todo su amor, {name} creó el \"Pastel de los Recuerdos Felices\": capas de alegría, relleno de abrazos y glaseado de sonrisas.",
        "text_en": "With magical ingredients and all their love, {name} created the \"Happy Memories Cake\": layers of joy, filling of hugs, and frosting of smiles.",
        "prompt": "Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, proudly holding a beautiful cake. OUTFIT: {sweetie_hat_inline}, and a white chef jacket with golden buttons and cake stains. ACTION: {gender_word} proudly holds a beautiful whole round cake with multiple layers of bright colors pink blue yellow green purple, heart-shaped sparkles and golden light emanate from it. SETTING: Warm magical kitchen WIDE VIEW, wooden counters, hanging copper pots, floating spoons stirring, glowing brick oven. ATMOSPHERE: Love and creation, heart sparkles. STRICT: Only ONE {gender_word}, {gender_word} is 100% human child, no duplicates. {style}",
        "text_position": "split"
    },
    {
        "id": 16,
        "text_es": "Cuando los jueces probaron el pastel de {name}, lágrimas de felicidad rodaron por sus mejillas. Cada bocado traía un recuerdo hermoso.",
        "text_en": "When the judges tasted {name}'s cake, tears of happiness rolled down their cheeks. Each bite brought back a beautiful memory.",
        "prompt": "Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, standing proudly watching the judges. OUTFIT: a fancy white chef's hat with {sweetie_hat_inline} and golden trim, and an elegant white chef jacket with golden buttons. ACTION: {gender_word} stands proudly while judges taste, beautiful rainbow cake on judging table, in background a fairy chef and elf chef with happy expressions and tears of joy. SETTING: Contest judging table WIDE VIEW, beautiful whole round rainbow cake. ATMOSPHERE: Emotional triumph, warm joy. STRICT: Only ONE {gender_word}, {gender_word} is 100% human child, no duplicates. {style}",
        "text_position": "split"
    },
    {
        "id": 17,
        "text_es": "\"¡El ganador es Chef {name}!\", anunció la abuelita de mazapán. \"Has descubierto el ingrediente secreto: el amor.\"",
        "text_en": "\"The winner is Chef {name}!\" announced the marzipan grandmother. \"You discovered the secret ingredient: love.\"",
        "prompt": "Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, triumphant expression holding rainbow cake. OUTFIT: a fancy white chef's hat with {sweetie_hat_inline}, golden crown on top, and an elegant white chef jacket with golden buttons and a shiny gold winner's medal. COMPANION: {SWEETIE_CAKE_INLINE}. ACTION: {gender_word} stands triumphantly on winner's podium holding the rainbow cake, SWEETIE jumps happily celebrating, confetti and streamers fall from above, magical creatures cheer in background. SETTING: Grand festive celebration hall WIDE VIEW, colorful banners, balloons, twinkling lights, decorated stage. ATMOSPHERE: Victory celebration, confetti and joy. STRICT: Only ONE {gender_word}, only ONE cake character SWEETIE, {gender_word} is 100% human child, no duplicates. {style}",
        "text_position": "split"
    },
    {
        "id": 18,
        "text_es": "\"Nunca olvides\", susurró el gorro mágico, \"que la verdadera magia está en cocinar con el corazón y compartir con los demás.\"",
        "text_en": "\"Never forget,\" whispered the magic hat, \"that true magic is cooking with your heart and sharing with others.\"",
        "prompt": "Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, grateful loving expression. OUTFIT: a glowing magical white chef's hat with {sweetie_hat_inline} speaking wisely with golden sparkles, and a white chef jacket with golden buttons and gold winner's medal. COMPANION: {SWEETIE_CAKE_INLINE}. ACTION: {gender_word} listens to the hat's wisdom, golden words and hearts float in the air, SWEETIE stands nearby watching lovingly. SETTING: Party hall WIDE VIEW, decorated with confetti and streamers. ATMOSPHERE: Warm wisdom, golden hearts and words. STRICT: Only ONE {gender_word}, only ONE cake character SWEETIE, {gender_word} is 100% human child, no duplicates. {style}",
        "text_position": "split"
    },
    {
        "id": 19,
        "text_es": "{name} regresó a casa con su gorro mágico y una receta especial en el corazón. Y colorín colorado, este cuento delicioso ha terminado.",
        "text_en": "{name} returned home with the magic hat and a special recipe in their heart. And they lived sweetly ever after. The End.",
        "prompt": "Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, warm smile, looking peaceful and content, carrying the white chef hat in one hand. OUTFIT: a cozy yellow t-shirt with jeans and sneakers. ACTION: {gender_word} walks along a winding country path toward home, carrying the magical chef's hat in one hand. SETTING: Beautiful sunset scene WIDE VIEW, peaceful meadow with wildflowers, cozy cottage with warm golden lights in distance, sky in warm pastel pinks oranges and purples, golden sparkles and fireflies. ATMOSPHERE: Peaceful goodbye, warm sunset colors. STRICT: Only ONE {gender_word}, NO cake character, {gender_word} is 100% human child, no duplicates. {style}",
        "text_position": "bottom"
    }
]

CLOSING_SCENE = {
    "id": 20,
    "prompt": "Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, sleeping peacefully with gentle smile. OUTFIT: Cozy pajamas with cupcake patterns, magical chef's hat resting on head. ACTION: {gender_word} sleeps in a cozy bed, a gold winner's medal on the nightstand, a small plush rainbow cake toy (SWEETIE plush) snuggled beside. SETTING: Cozy bedroom at night WIDE VIEW, stars through window, soft moonlight, magical sparkles floating gently. ATMOSPHERE: Dreamy peaceful slumber, warm glow. STRICT: Only ONE {gender_word}, NO real cake character, only plush toy, {gender_word} is 100% human child. {style}",
    "text_position": "none"
}

FRONT_COVER = {
    "prompt": "Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, confident joyful smile. OUTFIT: {sweetie_hat_inline}, and an elegant white chef jacket with golden buttons. COMPANION: {SWEETIE_CAKE_INLINE}. ACTION: {gender_word} stands in center of magical kitchen, SWEETIE floats happily beside the child. SETTING: Magical pink kitchen WIDE VIEW, sparkles hearts and golden stars, floating magical desserts everywhere, rainbow cakes, glowing star cookies, swirling colorful ice creams, centered composition for book cover. ATMOSPHERE: Sweet magical invitation, pink and golden warmth. STRICT: Only ONE {gender_word}, only ONE cake character SWEETIE, {gender_word} is 100% human child, no duplicates. ABSOLUTELY NO rendered text anywhere in the image, no titles, no logos, no words, no letters, no captions, no watermarks, no signatures, pure illustration only. {style}"
}

BACK_COVER = {
    "prompt": "Disney Pixar 3D style illustration. SETTING: Warm cozy magical kitchen WIDE VIEW, wooden shelves with colorful ingredient jars, copper pots hanging from ceiling, brick oven with warm golden glow, floating wooden spoons, magical sparkles, steam rising from pots, rainbow cakes and desserts on tables, star-shaped cookies on tray, warm sunset light through window. STRICT: NO characters, NO people, only scenery. ABSOLUTELY NO rendered text anywhere in the image, no titles, no logos, no words, no letters, no captions, no watermarks, no signatures, pure illustration only. {style}"
}


def get_outfit_desc(gender: str) -> str:
    if gender == "male":
        return "a white chef jacket with golden buttons over blue striped shirt, comfortable pants and sneakers"
    else:
        return "a white chef jacket with golden buttons over pink striped shirt, comfortable pants and sneakers"


def get_hair_action(traits: dict) -> str:
    hair_length = traits.get('hair_length', 'medium')
    if hair_length == 'long':
        return "long hair flowing gently"
    elif hair_length == 'short':
        return "short hair neatly styled"
    else:
        return "hair gently styled"


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
    prompt = prompt.replace('{sweetie_hat_inline}', SWEETIE_HAT_INLINE)
    prompt = prompt.replace('{SWEETIE_CAKE_INLINE}', SWEETIE_CAKE_INLINE)
    prompt = prompt.replace('{style}', STYLE_BASE)
    prompt = prompt.replace('{name}', child_name)
    prompt = prompt.replace('{child_name}', child_name)

    from services.fixed_stories import enforce_gender_clothing
    prompt = enforce_gender_clothing(prompt, gender)

    return prompt


def get_all_scene_prompts(child_name: str, gender: str, age: int, traits: dict) -> list:
    prompts = []
    for scene in MAGIC_CHEF_SCENES:
        prompts.append(build_scene_prompt(scene, child_name, gender, age, traits))
    prompts.append(build_scene_prompt(CLOSING_SCENE, child_name, gender, age, traits))
    return prompts


def get_cover_prompts(child_name: str, gender: str, age: int, traits: dict) -> dict:
    return {
        'front': build_scene_prompt(FRONT_COVER, child_name, gender, age, traits),
        'back': build_scene_prompt(BACK_COVER, child_name, gender, age, traits)
    }
