"""
Fixed Stories System - "Soñando con Volar"
Only head (hair, eyes) and hands (skin tone) are personalized.
"""

STYLE_BASE = "children's storybook watercolor illustration, soft luminous pastel colors, gentle warm lighting, dreamy magical atmosphere, WIDE PANORAMIC scene composition showing full environment and landscape, full body characters actively participating in scene, camera pulled back to show context. NO text, NO watermark, NO signature, NO logo, NO artist name, NO handwriting, NO calligraphy, clean illustration only"

# DNA-based companion descriptions - character identity defined upfront for FLUX consistency
SPARK_DESC = "SPARK: A massive baby dragon with the proportions of a puppy but the size of a giant. Spark is a huge creature, TOWERING over the {gender_word}. He has shimmering emerald-green scales, a very chubby and round body, large golden eyes, and small translucent wings. He has a soft cream-colored belly and two tiny horns. His mass is five times larger than the {gender_word}"
MAMA_DRAGON_DESC = "MAMA DRAGON: a large majestic adult female dragon with shimmering golden scales covering her entire body, warm amber eyes full of wisdom, large elegant spread wings, long graceful neck, gentle wise maternal expression, crown of small golden horns, cream-colored underbelly - she is THREE TIMES taller than the child, towering and massive"
PUPPY_DESC = "POMPOM: a single small golden plush puppy toy with soft cream-gold fur, big round black button eyes, small floppy ears, pink embroidered nose, sweet embroidered smile - POMPOM is a STUFFED TOY not a real dog, soft and plush like a teddy bear"
KITTEN_DESC = "MISU: a small fluffy black and white tuxedo kitten with soft fluffy fur, bright curious green eyes, tiny pink nose, pure white chest and paws, jet black back and ears - MISU is a REAL baby kitten, adorable and playful"
LILA_DESC = "LILA: a young female zebra with a round cute cartoon face, big gentle dark brown eyes, long black eyelashes, small rounded ears, soft pink nose, short fuzzy black mane along her neck, four slender black hooves. Same height as the {gender_word}. LILA is a REAL four-legged zebra animal"

# Character base description template for consistent child rendering
CHILD_BASE_DESC = """Physical characteristics of {gender_child}:
- Age: {age_display}
- EXACT Hair: {hair_desc}, {hair_color} color, {hair_length} {hair_type}
- EXACT Skin: {skin_tone} skin in all images
- EXACT Eyes: {eye_desc}
- EXACT Face: same facial features, proportions
- HUMAN ONLY: normal human child with two arms, two legs, five fingers per hand
This child must look IDENTICAL across all illustrations. Maintain perfect consistency."""
BUNNY_DESC = "NUBE: a small soft fluffy white bunny plush toy with long floppy ears, pink inner ears, pink nose, gentle black button eyes - NUBE is a STUFFED TOY not a real rabbit, soft and plush"
DOG_FOREVER_DESC = "AMIGO: a friendly medium-sized mixed breed dog with warm golden-brown fur, soft floppy ears, big gentle dark brown eyes, black wet nose, fluffy wagging tail. AMIGO is a REAL dog, loyal and calm, same height as the {gender_word}'s waist"
GUARDIAN_LIGHT_DESC = "a tiny smooth featureless sphere of pure warm golden light, NO face, NO eyes, NO text, NO letters, NO words on it, just a simple round glowing ball of soft golden light with gentle rays, floating gracefully in the air, emanating love and protection - a simple glowing sphere of light, NOT a character, NOT a creature, NO writing anywhere"

NEGATIVE_PROMPT = "text, watermark, signature, logo, artist signature, copyright, words, letters, numbers, writing, stamp, badge, label, banner, handwriting, calligraphy, typography, autograph, signed, initials, monogram, name, credit, tail, animal tail, dragon tail, wings on child, animal features on child, furry, animal ears, extra fingers, missing fingers, fused fingers, too many fingers, six fingers, malformed hands, bad hands anatomy, deformed hands, extra toes, missing toes, malformed feet, extra legs, four legs, extra arms, three arms, four arms, extra limbs, multiple legs, multiple arms, deformed legs, deformed body, mutated, disfigured, bad anatomy, wrong anatomy, extra body parts, missing limbs, floating limbs, disconnected limbs, mutation, mutated hands, poorly drawn hands, poorly drawn feet, poorly drawn face, out of frame, extra bodies, duplicate, cloned face, gross proportions, malformed limbs, missing arms, missing legs, extra leg, extra arm"

STORIES = {
    "baby_soft_world": {
        "title_es": "{name} y el mundo suave",
        "title_en": "{name} and the Soft World",
        "age_range": "0-1",
        "use_ideogram_scenes": True,
        "preview_prompt_override": "Disney 3D Pixar-style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_desc}, extremely chubby cheeks, round baby face, tiny hands, sweet innocent expression looking at the viewer. WEARING: Plain soft white onesie with diaper visible. ACTION: Baby is sitting on a soft fluffy white blanket on the nursery floor. Next to the baby sits a small soft fluffy white bunny plush toy with long floppy ears and pink inner ears, placed separately on the blanket. ENVIRONMENT: Cozy nursery, soft pastel pink walls, gentle floating feathers and golden sparkles. ATMOSPHERE: Warm dreamy magical light, soft pastel colors, innocence and wonder. STRICT: Exactly ONE human baby, exactly ONE plush bunny toy, baby is fully human with human ears only, bunny sits separately on the floor as a stuffed toy, clean illustration only",
        "preview_prompt_override_toddler": "Disney 3D Pixar-style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_desc}, chubby cheeks, round toddler face, small hands, sweet curious expression looking at the viewer. WEARING: Plain soft white onesie. ACTION: Toddler is standing on tiny feet on a soft fluffy white blanket on the nursery floor, holding a small soft fluffy white bunny plush toy with long floppy ears and pink inner ears in one arm. ENVIRONMENT: Cozy nursery, soft pastel pink walls, gentle floating feathers and golden sparkles. ATMOSPHERE: Warm dreamy magical light, soft pastel colors, innocence and wonder. STRICT: Exactly ONE human toddler, exactly ONE plush bunny toy, child is fully human with human ears only, clean illustration only",
        "cover_template": "Disney 3D Pixar-style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, extremely chubby cheeks, round baby face, gentle closed-mouth smile, looking up with wonder. WEARING: Plain soft white onesie. ACTION: Baby is lying peacefully on a fluffy cloud-like white blanket, looking up. ENVIRONMENT: Dreamy pink and lavender background with soft clouds, gentle soap bubbles and soft pastel flower petals floating in the air, golden sparkles. ATMOSPHERE: Magical book cover composition centered, ultra soft textures, warm golden light. STRICT: Exactly ONE human baby alone in frame, baby is fully human with human ears only, soft dreamy background only. {style}",
        "use_preview_as_cover": True,
        "pages": [
            {
                "text_es": "Hola, {name}.\nEl mundo te espera.\nTodo es nuevo.\nTodo es suave.",
                "text_en": "Hello, {name}.\nThe world awaits you.\nEverything is new.\nEverything is soft.",
                "scene_template": "Disney 3D Pixar-style illustration of a baby lying flat on back on a soft fluffy white blanket, wearing a white onesie, tiny legs relaxed, tiny arms resting at sides, looking up with calm curious wonder. Surrounded by fluffy pillows and gentle floating feathers in soft pastel colors. Cozy nursery wide view, warm golden morning light through white curtains, pastel pink walls, soft plush toys on cream shelves, magical sparkles in the air. Warm cozy magical morning atmosphere, innocence and discovery.",
                "scene_template_toddler": "Disney 3D Pixar-style illustration of a toddler standing on tiny feet on a soft fluffy white blanket in the nursery, wearing a white onesie, looking around with calm curious wonder, small hands at sides. Surrounded by fluffy pillows and gentle floating feathers in soft pastel colors. Cozy nursery wide view, warm golden morning light through white curtains, pastel pink walls, soft plush toys on cream shelves, magical sparkles in the air. Warm cozy magical morning atmosphere, innocence and discovery."
            },
            {
                "text_es": "La luz brilla despacio.\nLos colores sonríen.\nEl aire es tranquilo.\nTú estás a salvo.",
                "text_en": "The light shines softly.\nColors are smiling.\nThe air is calm.\nYou are safe.",
                "scene_template": "Disney 3D Pixar-style illustration of a baby sitting on a soft fluffy white blanket on the floor, wearing a white onesie, serene joyful expression with gentle smile. Tiny hands reaching gently toward gentle pastel ribbons in pink, lavender, mint and peach that float and dance softly around the baby. Magical nursery wide view, soft morning light, cream furniture, mobile hanging from ceiling. Serene calm safety atmosphere, soft floating colors, magical warmth.",
                "scene_template_toddler": "Disney 3D Pixar-style illustration of a toddler standing on the nursery floor, wearing a white onesie, serene joyful expression with gentle smile. Small hands reaching up gently toward gentle pastel ribbons in pink, lavender, mint and peach that float and dance softly around the child. Magical nursery wide view, soft morning light, cream furniture, mobile hanging from ceiling. Serene calm safety atmosphere, soft floating colors, magical warmth."
            },
            {
                "text_es": "Escuchas voces dulces.\nSientes un abrazo.\nUn corazón cerca.\nLate contigo.",
                "text_en": "You hear sweet voices.\nYou feel a hug.\nA heart nearby.\nBeats with you.",
                "scene_template": "Disney 3D Pixar-style illustration of a baby sitting on a soft fluffy white blanket, wearing a white onesie, peaceful happy expression. Baby holds a small soft fluffy white bunny plush toy with long floppy ears and pink inner ears in its lap. Soft glowing pink hearts and gentle golden musical notes float in the air around them. Loving nursery wide view, warm golden light through white curtains, soft pink and gold tones, cream crib in background. Pure love atmosphere, warm heartbeats, gentle musical magic.",
                "scene_template_toddler": "Disney 3D Pixar-style illustration of a toddler standing in the nursery, wearing a white onesie, peaceful happy expression. Toddler hugging a small soft fluffy white bunny plush toy with long floppy ears and pink inner ears against chest with both arms. Soft glowing pink hearts and gentle golden musical notes float in the air around them. Loving nursery wide view, warm golden light through white curtains, soft pink and gold tones, cream crib in background. Pure love atmosphere, warm heartbeats, gentle musical magic."
            },
            {
                "text_es": "Tus manos descubren.\nTus ojos miran.\nPoco a poco,\naprendes el mundo.",
                "text_en": "Your hands discover.\nYour eyes look.\nLittle by little,\nyou learn the world.",
                "scene_template": "Disney 3D Pixar-style illustration of a baby sitting on a soft fluffy white blanket, wearing a white onesie, curious wonder-filled expression. Baby gently reaching out tiny hands toward a small soft fluffy white bunny plush toy with long floppy ears that sits on the blanket in front of the baby. Magical golden sparkles appear where baby's fingers reach. Cozy nursery wide view, bright cheerful pastel colors, cream crib in background, soft morning light, pastel pink walls. Discovery and wonder atmosphere, magical sparkles of first touch.",
                "scene_template_toddler": "Disney 3D Pixar-style illustration of a toddler toddling across the nursery floor toward a small soft fluffy white bunny plush toy with long floppy ears, wearing a white onesie, curious wonder-filled expression. Small hands reaching out toward the bunny toy. Magical golden sparkles appear where the child's fingers reach. Cozy nursery wide view, bright cheerful pastel colors, cream crib in background, soft morning light, pastel pink walls. Discovery and wonder atmosphere, magical sparkles of first touch."
            },
            {
                "text_es": "Cada día es mágico.\nCada risa es música.\nCada abrazo es amor.\nCrecerás feliz.",
                "text_en": "Every day is magical.\nEvery laugh is music.\nEvery hug is love.\nYou will grow happy.",
                "scene_template": "Disney 3D Pixar-style illustration of a baby sitting on a soft fluffy white blanket, wearing a white onesie, gentle warm natural smile with lips softly closed, happy content expression. Baby holding a small soft fluffy white bunny plush toy with long floppy ears in baby's arms. Colorful soap bubbles and magical sparkles float all around them. Joyful nursery wide view, warm golden sunlight through window, pastel pink walls with soft cloud decorations, cream furniture, floating hearts and stars. Pure joy and magic atmosphere, celebration of life, warm golden glow. STRICT: natural closed-mouth smile, NO wide open mouth, NO laughing expression. Maintain exact same baby face and features as reference.",
                "scene_template_toddler": "Disney 3D Pixar-style illustration of a toddler standing in the nursery, wearing a white onesie, gentle warm natural smile with lips softly closed, happy content expression. Toddler holding a small soft fluffy white bunny plush toy with long floppy ears in arms against chest. Colorful soap bubbles and magical sparkles float all around them. Joyful nursery wide view, warm golden sunlight through window, pastel pink walls with soft cloud decorations, cream furniture, floating hearts and stars. Pure joy and magic atmosphere, celebration of life, warm golden glow. STRICT: natural closed-mouth smile, NO wide open mouth, NO laughing expression. Maintain exact same child face and features as reference."
            },
            {
                "text_es": "Mira cómo brillas.\nCon cada sonrisa.\nCon cada mirada.\nEres pura magia.",
                "text_en": "Look how you shine.\nWith every smile.\nWith every glance.\nYou are pure magic.",
                "scene_template": "Disney 3D Pixar-style illustration of a baby sitting on a soft fluffy white blanket, wearing a white onesie, wonder-filled eyes, gentle amazed smile. Baby reaching out tiny hands toward floating magical butterflies made of soft light. A small soft fluffy white bunny plush toy with long floppy ears sits on the blanket beside the baby. Enchanted nursery wide view, rainbow light through window creating soft prisms, pastel pink walls, magical butterflies and sparkles in the air, cream furniture. Pure magic and wonder atmosphere, rainbow prisms, ethereal butterflies.",
                "scene_template_toddler": "Disney 3D Pixar-style illustration of a toddler standing in the nursery, wearing a white onesie, wonder-filled eyes, gentle amazed smile. Toddler reaching up small hands toward floating magical butterflies made of soft light. A small soft fluffy white bunny plush toy with long floppy ears sits on the floor beside the child. Enchanted nursery wide view, rainbow light through window creating soft prisms, pastel pink walls, magical butterflies and sparkles in the air, cream furniture. Pure magic and wonder atmosphere, rainbow prisms, ethereal butterflies."
            },
            {
                "text_es": "Sales al jardín.\nTocas una flor.\nHueles la brisa.\nEl mundo es enorme.",
                "text_en": "You go to the garden.\nYou touch a flower.\nYou smell the breeze.\nThe world is enormous.",
                "scene_template": "Disney 3D Pixar-style illustration of a baby sitting on soft green grass in a sunny garden, wearing a white onesie, gentle curious smile, tiny hands reaching toward a bright pink flower. A small soft fluffy white bunny plush toy with long floppy ears sits on the grass beside the baby. Lush garden wide view, colorful flowers blooming around, butterflies gently floating, blue sky with fluffy white clouds, warm golden sunlight, green leaves and soft petals in the air. Discovery of nature atmosphere, wonder and innocence, warm outdoor light.",
                "scene_template_toddler": "Disney 3D Pixar-style illustration of a toddler standing on soft green grass in a sunny garden, wearing a white onesie, gentle curious smile, bending down slightly to touch a bright pink flower with small hands. A small soft fluffy white bunny plush toy with long floppy ears sits on the grass beside the child. Lush garden wide view, colorful flowers blooming around, butterflies gently floating, blue sky with fluffy white clouds, warm golden sunlight, green leaves and soft petals in the air. Discovery of nature atmosphere, wonder and innocence, warm outdoor light."
            },
            {
                "text_es": "Es hora de descansar.\nEl día fue bonito.\nCierra los ojos, {name}.\nTe queremos.",
                "text_en": "Time to rest now.\nThe day was beautiful.\nClose your eyes, {name}.\nWe love you.",
                "scene_template": "Disney 3D Pixar-style illustration of a baby lying in a classic white wooden crib, wearing a white onesie, eyes completely closed in deep peaceful sleep. Covered with cream-colored soft blankets. A small soft fluffy white bunny plush toy with long floppy ears rests beside the baby in the crib. Peaceful bedtime nursery wide view, gentle silver moonlight through white curtains, soft lavender and cream tones, tiny stars twinkling outside window, soft night light glowing, mobile with stars above crib. Serene peaceful moonlit calm atmosphere, dreamy bedtime.",
                "scene_template_toddler": "Disney 3D Pixar-style illustration of a toddler lying in a cozy toddler bed, wearing a white onesie, eyes completely closed in deep peaceful sleep. Covered with cream-colored soft blankets. A small soft fluffy white bunny plush toy with long floppy ears rests beside the child in bed. Peaceful bedtime nursery wide view, gentle silver moonlight through white curtains, soft lavender and cream tones, tiny stars twinkling outside window, soft night light glowing. Serene peaceful moonlit calm atmosphere, dreamy bedtime."
            }
        ],
    },
    "baby_puppy_love": {
        "title_es": "¿Sabes cuánto te quiero, {name}?",
        "title_en": "Do You Know How Much I Love You, {name}?",
        "age_range": "0-1",
        "use_ideogram_scenes": True,
        "use_preview_as_cover": True,
        "preview_prompt_override": "Disney 3D Pixar-style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_desc}, extremely chubby cheeks, round baby face, tiny hands. WEARING: Plain soft white onesie with diaper visible. ACTION: Baby is sitting on a soft pastel blanket, hugging POMPOM (a small golden plush puppy toy with soft cream-gold fur, big round black button eyes, small floppy ears, pink embroidered nose, sweet embroidered smile - this is a STUFFED TOY not a real dog). ENVIRONMENT: Cozy nursery, cream crib in background, soft morning light, pastel pink walls, gentle floating sparkles. ATMOSPHERE: Warm dreamy magical golden light, soft pink hearts floating gently. STRICT: Only ONE baby, only ONE plush puppy toy POMPOM, 100% human baby, no animal ears, no animal features on baby, no duplicates of baby or toy. NO text, NO watermark, NO signature, NO logo",
        "preview_prompt_override_toddler": "Disney 3D Pixar-style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_desc}, chubby cheeks, round toddler face, small hands, sweet loving expression. WEARING: Plain soft white onesie. ACTION: Toddler is standing on tiny feet on a soft pastel blanket, holding POMPOM (a small golden plush puppy toy with soft cream-gold fur, big round black button eyes, small floppy ears, pink embroidered nose, sweet embroidered smile - STUFFED TOY not a real dog) in one arm against chest. ENVIRONMENT: Cozy nursery, cream crib in background, soft morning light, pastel pink walls, gentle floating sparkles. ATMOSPHERE: Warm dreamy magical golden light, soft pink hearts floating gently. STRICT: Only ONE toddler, only ONE plush puppy toy POMPOM, 100% human child, no animal ears, no animal features on child, no duplicates. NO text, NO watermark, NO signature, NO logo",
        "cover_template": "Disney 3D Pixar-style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, extremely chubby cheeks, round baby face. WEARING: Plain soft white onesie. ACTION: Baby is sitting on a soft pastel blanket, hugging {puppy_desc} against chest with sweet loving expression. ENVIRONMENT: Dreamy soft pink, lavender and cream background, no specific room. ATMOSPHERE: Warm golden sparkles, soft floating hearts, magical book cover composition centered. STRICT: Only ONE baby, only ONE plush puppy POMPOM, no duplicates, baby is 100% human, no animal features. {style}",
        "pages": [
            {
                "text_es": "Hola, {name}.\nEste es tu perrito.\nTu perrito favorito.\nSiempre está contigo.",
                "text_en": "Hello, {name}.\nThis is your puppy.\nYour favorite puppy.\nAlways with you.",
                "scene_template": "Disney 3D Pixar-style illustration of a baby sitting on the soft pastel nursery floor, wearing a white onesie, looking with curious loving eyes at POMPOM (a small golden plush puppy toy with soft cream-gold fur, big round button eyes, small floppy ears, pink embroidered nose) sitting on the floor next to the baby. Cozy nursery WIDE VIEW, cream crib, pastel pink walls, soft morning light streaming through curtains, gentle floating sparkles. Warm cozy magical morning light, soft golden sparkles. STRICT: Maintain exact same baby face and features as reference. Only ONE baby, only ONE plush puppy POMPOM, POMPOM is a stuffed toy NOT a real dog.",
                "scene_template_toddler": "Disney 3D Pixar-style illustration of a toddler standing on the soft pastel nursery floor, wearing a white onesie, looking down with curious loving eyes at POMPOM (a small golden plush puppy toy with soft cream-gold fur, big round button eyes, small floppy ears, pink embroidered nose) sitting on the floor beside the child. Cozy nursery WIDE VIEW, cream crib, pastel pink walls, soft morning light streaming through curtains, gentle floating sparkles. Warm cozy magical morning light, soft golden sparkles. STRICT: Maintain exact same child face and features as reference. Only ONE child, only ONE plush puppy POMPOM, POMPOM is a stuffed toy NOT a real dog."
            },
            {
                "text_es": "El perrito mueve la cola.\nTe mira y sonríe.\nParece decir:\n\"Yo te quiero mucho\".",
                "text_en": "The puppy wags its tail.\nIt looks at you and smiles.\nIt seems to say:\n\"I love you so much\".",
                "scene_template": "Disney 3D Pixar-style illustration of a baby sitting on a soft blanket, wearing a white onesie, watching POMPOM (a small golden plush puppy toy with soft cream-gold fur, big round button eyes, small floppy ears) sitting directly in front of the baby. Tiny pink hearts floating between them. Magical nursery WIDE VIEW, pastel pink and cream colors, toys on shelves, dreamy sparkles filling the space. Dreamy magical sparkles, soft warm light, floating pink hearts between baby and POMPOM. STRICT: Maintain exact same baby face and features as reference. Only ONE baby, only ONE plush puppy POMPOM, POMPOM is a stuffed toy.",
                "scene_template_toddler": "Disney 3D Pixar-style illustration of a toddler standing in the nursery, wearing a white onesie, looking down at POMPOM (a small golden plush puppy toy with soft cream-gold fur, big round button eyes, small floppy ears) sitting on the floor in front of the child. Tiny pink hearts floating between them. Magical nursery WIDE VIEW, pastel pink and cream colors, toys on shelves, dreamy sparkles filling the space. Dreamy magical sparkles, soft warm light, floating pink hearts. STRICT: Maintain exact same child face and features as reference. Only ONE child, only ONE plush puppy POMPOM, POMPOM is a stuffed toy."
            },
            {
                "text_es": "Y tú, {name},\nlo abrazas fuerte.\nCon tu corazón dices:\n\"Yo te quiero más\".",
                "text_en": "And you, {name},\nhug it tight.\nWith your heart you say:\n\"I love you more\".",
                "scene_template": "Disney 3D Pixar-style illustration of a baby sitting on a soft blanket, wearing a white onesie, eyes closed with sweet contented smile, hugging POMPOM (a small golden plush puppy toy with soft cream-gold fur, big round button eyes, small floppy ears) tightly against chest with both tiny arms, peaceful loving expression. Cozy nursery WIDE VIEW, warm golden light bathing the room, ultra-soft pastel pink and cream colors. Soft sparkly hearts surrounding baby and POMPOM, warm golden glow, pure love and comfort. STRICT: Maintain exact same baby face and features as reference. Only ONE baby, only ONE plush puppy POMPOM.",
                "scene_template_toddler": "Disney 3D Pixar-style illustration of a toddler standing in the nursery, wearing a white onesie, eyes closed with sweet contented smile, hugging POMPOM (a small golden plush puppy toy with soft cream-gold fur, big round button eyes, small floppy ears) tightly against chest with both arms, peaceful loving expression. Cozy nursery WIDE VIEW, warm golden light bathing the room, ultra-soft pastel pink and cream colors. Soft sparkly hearts surrounding child and POMPOM, warm golden glow, pure love and comfort. STRICT: Maintain exact same child face and features as reference. Only ONE child, only ONE plush puppy POMPOM."
            },
            {
                "text_es": "El perrito salta feliz.\nTe quiere así de grande.\nPero tú respondes:\n\"¡Yo te quiero másssss!\"",
                "text_en": "The puppy jumps happily.\nIt loves you this much.\nBut you reply:\n\"I love you moooore!\"",
                "scene_template": "Disney 3D Pixar-style illustration of a baby sitting on a soft blanket, wearing a white onesie, laughing joyfully with open arms, holding POMPOM (a small golden plush puppy toy with soft cream-gold fur, big round button eyes, small floppy ears) up in the air with both hands, lifting the toy high with affection. Cheerful nursery WIDE VIEW, bright pastel colors, magical sparkles everywhere. Colorful hearts of different sizes floating around the room, pure joy and celebration. STRICT: Maintain exact same baby face and features as reference. Only ONE baby, only ONE plush puppy POMPOM held by baby, no tail on baby, baby is 100% human.",
                "scene_template_toddler": "Disney 3D Pixar-style illustration of a toddler standing in the nursery, wearing a white onesie, laughing joyfully, holding POMPOM (a small golden plush puppy toy with soft cream-gold fur, big round button eyes, small floppy ears) up in the air with both hands, lifting the toy high with affection. Cheerful nursery WIDE VIEW, bright pastel colors, magical sparkles everywhere. Colorful hearts of different sizes floating around the room, pure joy and celebration. STRICT: Maintain exact same child face and features as reference. Only ONE child, only ONE plush puppy POMPOM held by child, no tail on child, child is 100% human."
            },
            {
                "text_es": "¿Sabes cuánto te quiero?\nHasta la luna.\nHasta las estrellas.\nPara siempre jamás.",
                "text_en": "Do you know how much I love you?\nTo the moon.\nTo the stars.\nForever and ever.",
                "scene_template": "Disney 3D Pixar-style illustration of a baby sitting on a soft blanket, wearing a white onesie, sweetest smile, eyes full of wonder, with POMPOM (a small golden plush puppy toy with soft cream-gold fur, big round button eyes, small floppy ears) on lap, both looking up at magical floating hearts and stars that fill the room above them. Magical nursery WIDE VIEW, dreamy pink and golden light, floating hearts in different sizes, tiny stars twinkling, magical sparkles everywhere. Infinite love, dreamy celestial magic, warm golden glow. STRICT: Maintain exact same baby face and features as reference. Only ONE baby, only ONE plush puppy POMPOM on baby's lap.",
                "scene_template_toddler": "Disney 3D Pixar-style illustration of a toddler standing in the nursery, wearing a white onesie, sweetest smile, eyes full of wonder, holding POMPOM (a small golden plush puppy toy with soft cream-gold fur, big round button eyes, small floppy ears) in one arm, looking up at magical floating hearts and stars that fill the room above. Magical nursery WIDE VIEW, dreamy pink and golden light, floating hearts in different sizes, tiny stars twinkling, magical sparkles everywhere. Infinite love, dreamy celestial magic, warm golden glow. STRICT: Maintain exact same child face and features as reference. Only ONE child, only ONE plush puppy POMPOM."
            },
            {
                "text_es": "{name} y Perrito juegan y se divierten.\nRíen juntos toda la tarde.\nHasta que llega la noche.",
                "text_en": "{name} and Puppy play and have fun.\nThey laugh together all afternoon.\nUntil night arrives.",
                "scene_template": "Disney 3D Pixar-style illustration of a baby sitting on soft nursery floor, wearing a white onesie, giggling with pure joy, holding POMPOM (a small golden plush puppy toy with soft cream-gold fur, big round button eyes, small floppy ears) with one hand while reaching for a colorful toy with the other, soft blocks and a rattle and a small ball scattered around. Playful nursery WIDE VIEW, warm golden afternoon sunlight streaming through window, soft pink and cream nursery, toys everywhere, sunset colors visible through window. Warm playful golden light, gentle sparkles, cheerful afternoon energy. STRICT: Maintain exact same baby face and features as reference. Only ONE baby, only ONE plush puppy POMPOM.",
                "scene_template_toddler": "Disney 3D Pixar-style illustration of a toddler sitting on soft nursery floor, wearing a white onesie, giggling with pure joy, holding POMPOM (a small golden plush puppy toy with soft cream-gold fur, big round button eyes, small floppy ears) with one hand while reaching for a colorful toy with the other, soft blocks and a rattle and a small ball scattered around. Playful nursery WIDE VIEW, warm golden afternoon sunlight streaming through window, soft pink and cream nursery, toys everywhere, sunset colors visible through window. Warm playful golden light, gentle sparkles, cheerful afternoon energy. STRICT: Maintain exact same child face and features as reference. Only ONE child, only ONE plush puppy POMPOM."
            },
            {
                "text_es": "Las estrellas salen a brillar.\nLa luna dice buenas noches.\nPerrito bosteza despacito.\nYa casi es hora de dormir.",
                "text_en": "The stars come out to shine.\nThe moon says goodnight.\nPuppy yawns softly.\nIt's almost time to sleep.",
                "scene_template": "Disney 3D Pixar-style illustration of a baby sitting by a nursery window at night, wearing a white onesie, holding POMPOM (a small golden plush puppy toy with soft cream-gold fur, big round button eyes, small floppy ears, pink embroidered nose) in lap, looking at stars and moon through the window with calm wonder. Nursery WIDE VIEW, soft night light glowing warmly, stars visible through window, gentle moonlight streaming in, magical sparkles in the air, soft lavender and cream tones. Peaceful nighttime transition, magical starlight, calm wonder. STRICT: Maintain exact same baby face and features as reference. Only ONE baby, only ONE plush puppy POMPOM.",
                "scene_template_toddler": "Disney 3D Pixar-style illustration of a toddler standing by a nursery window at night, wearing a white onesie, holding POMPOM (a small golden plush puppy toy with soft cream-gold fur, big round button eyes, small floppy ears, pink embroidered nose) in one arm, looking at stars and moon through the window with calm wonder. Nursery WIDE VIEW, soft night light glowing warmly, stars visible through window, gentle moonlight streaming in, magical sparkles in the air, soft lavender and cream tones. Peaceful nighttime transition, magical starlight, calm wonder. STRICT: Maintain exact same child face and features as reference. Only ONE child, only ONE plush puppy POMPOM."
            },
            {
                "text_es": "Juntos descansan.\nPerrito y {name}.\nDos amigos.\nMucho, mucho amor.",
                "text_en": "Together they rest.\nPuppy and {name}.\nTwo friends.\nSo much love.",
                "scene_template": "Disney 3D Pixar-style illustration of a baby peacefully sleeping in a cozy crib, wearing a white onesie, eyes gently closed, cuddling POMPOM (a small golden plush puppy toy with soft cream-gold fur, big round button eyes, small floppy ears) close to chest with tiny arms. Peaceful nursery WIDE VIEW, gentle moonlight streaming through window, soft lavender and cream tones, tiny stars twinkling outside the window. Serene peaceful moonlit glow, dreamy calm, friendship and love. STRICT: Maintain exact same baby face and features as reference. Only ONE baby, only ONE plush puppy POMPOM being cuddled.",
                "scene_template_toddler": "Disney 3D Pixar-style illustration of a toddler peacefully sleeping in a cozy toddler bed, wearing a white onesie, eyes gently closed, cuddling POMPOM (a small golden plush puppy toy with soft cream-gold fur, big round button eyes, small floppy ears) close to chest with small arms. Peaceful nursery WIDE VIEW, gentle moonlight streaming through window, soft lavender and cream tones, tiny stars twinkling outside the window. Serene peaceful moonlit glow, dreamy calm, friendship and love. STRICT: Maintain exact same child face and features as reference. Only ONE child, only ONE plush puppy POMPOM being cuddled."
            }
        ],
    },
    "baby_first_pet": {
        "title_es": "{name} y su Primera Mascota",
        "title_en": "{name} and Their First Pet",
        "age_range": "0-1",
        "use_ideogram_scenes": True,
        "use_preview_as_cover": True,
        "preview_prompt_override": "Disney 3D Pixar-style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_desc}, extremely chubby cheeks, round baby face, tiny hands, innocent sweet expression. WEARING: Plain soft white onesie with diaper visible. ACTION: Baby is sitting on a soft pastel blanket with MISU (a tiny baby kitten with soft fluffy ginger-orange fur with faint tabby stripes, bright curious green eyes, tiny pink nose, fluffy short tail - a REAL baby kitten not a toy) sitting beside the baby. MISU looks up at the baby with curious bright green eyes. ENVIRONMENT: Cozy nursery, soft pastel mint green walls, gentle sparkles floating, warm light. ATMOSPHERE: Warm dreamy magical light, soft luminous colors, gentle wonder of first meeting. STRICT: Only ONE baby, only ONE kitten MISU, no duplicates, baby is 100% human, NO animal ears, NO animal features on baby, baby wearing WHITE onesie. NO text, NO watermark, NO signature, NO logo",
        "preview_prompt_override_toddler": "Disney 3D Pixar-style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_desc}, chubby cheeks, round toddler face, small hands, sweet curious expression. WEARING: Plain soft white onesie. ACTION: Toddler is standing on tiny feet on a soft pastel blanket, looking down at MISU (a tiny baby kitten with soft fluffy ginger-orange fur with faint tabby stripes, bright curious green eyes, tiny pink nose, fluffy short tail - a REAL baby kitten not a toy) sitting at the child's feet, looking up curiously. ENVIRONMENT: Cozy nursery, soft pastel mint green walls, gentle sparkles floating, warm light. ATMOSPHERE: Warm dreamy magical light, soft luminous colors, gentle wonder of first meeting. STRICT: Only ONE toddler, only ONE kitten MISU, no duplicates, child is 100% human, NO animal ears, NO animal features on child. NO text, NO watermark, NO signature, NO logo",
        "reference_image": "static/assets/kitten_reference.png",
        "cover_template": "Disney 3D Pixar-style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, extremely chubby cheeks, round baby face, sweet innocent expression. WEARING: Plain soft white onesie. ACTION: Baby is sitting on a soft pastel blanket with {kitten_desc} sitting next to the baby, MISU looking up at the baby with curious eyes. ENVIRONMENT: Dreamy soft mint green, cream and white background, gentle sparkles, warm golden light. ATMOSPHERE: Magical book cover composition centered, ultra soft textures, warm golden light. STRICT: Only ONE baby, only ONE kitten MISU, no duplicates, baby is 100% human, no animal features, baby wearing WHITE onesie. {style}",
        "pages": [
            {
                "text_es": "Este es mi gatito.\nEs suave y tranquilo.\nEstá cerca de mí.",
                "text_en": "This is my kitten.\nIt's soft and calm.\nIt's close to me.",
                "scene_template": "Disney 3D Pixar-style illustration of a baby sitting on a soft pastel nursery floor, wearing a white onesie, curious loving expression. Next to the baby sits MISU (a tiny baby kitten with soft ginger-orange fur, bright curious green eyes, tiny pink nose, fluffy short tail), sitting calmly on the floor looking at the baby. Cozy nursery WIDE VIEW, soft morning light streaming through curtains, mint green and cream walls, cream-colored furniture, gentle floating sparkles. Warm cozy magical morning, first meeting wonder. STRICT: Maintain exact same baby face and features as reference. Only ONE baby, only ONE kitten MISU, MISU is a real kitten not a toy.",
                "scene_template_toddler": "Disney 3D Pixar-style illustration of a toddler standing on the soft pastel nursery floor, wearing a white onesie, curious loving expression, looking down at MISU (a tiny baby kitten with soft ginger-orange fur, bright curious green eyes, tiny pink nose, fluffy short tail) sitting calmly on the floor looking up at the child. Cozy nursery WIDE VIEW, soft morning light streaming through curtains, mint green and cream walls, cream-colored furniture, gentle floating sparkles. Warm cozy magical morning, first meeting wonder. STRICT: Maintain exact same child face and features as reference. Only ONE child, only ONE kitten MISU, MISU is a real kitten not a toy."
            },
            {
                "text_es": "Mi gatito se acerca despacito.\nCamina con cuidado.\nMe observa curioso.",
                "text_en": "My kitten comes closer slowly.\nIt walks carefully.\nIt watches me curiously.",
                "scene_template": "Disney 3D Pixar-style illustration of a baby sitting on a soft blanket, wearing a white onesie, watching with wonder as MISU (a tiny baby kitten with soft ginger-orange fur, bright green eyes, fluffy short tail) walks slowly and carefully toward the baby. MISU has curious bright green eyes, fluffy tail up. Nursery WIDE VIEW, soft warm light, mint and cream colors, gentle floating sparkles. Gentle curiosity, tender approach, magical sparkles. STRICT: Maintain exact same baby face and features as reference. Only ONE baby, only ONE kitten MISU.",
                "scene_template_toddler": "Disney 3D Pixar-style illustration of a toddler standing in the nursery, wearing a white onesie, watching with wonder as MISU (a tiny baby kitten with soft ginger-orange fur, bright green eyes, fluffy short tail) walks slowly and carefully toward the child. MISU has curious bright green eyes, fluffy tail up. Nursery WIDE VIEW, soft warm light, mint and cream colors, gentle floating sparkles. Gentle curiosity, tender approach, magical sparkles. STRICT: Maintain exact same child face and features as reference. Only ONE child, only ONE kitten MISU."
            },
            {
                "text_es": "Yo miro al gatito.\nEl gatito me mira.\n{name} sonríe.",
                "text_en": "I look at the kitten.\nThe kitten looks at me.\n{name} smiles.",
                "scene_template": "Disney 3D Pixar-style illustration of a baby sitting on a soft blanket, wearing a white onesie, happy smile. Baby and MISU (a tiny baby kitten with soft ginger-orange fur, bright green eyes, tiny pink nose) looking at each other with sweet expressions. MISU sits in front of the baby with curious tilted head, bright green eyes meeting baby's gaze. Loving nursery WIDE VIEW, warm golden light streaming in, soft pastel colors, magical sparkles around them. Sweet connection, first eye contact, warm golden glow. STRICT: Maintain exact same baby face and features as reference. Only ONE baby, only ONE kitten MISU.",
                "scene_template_toddler": "Disney 3D Pixar-style illustration of a toddler kneeling on the nursery floor, wearing a white onesie, happy smile. Child and MISU (a tiny baby kitten with soft ginger-orange fur, bright green eyes, tiny pink nose) looking at each other at eye level with sweet expressions. MISU sits in front of the child with curious tilted head, bright green eyes meeting the child's gaze. Loving nursery WIDE VIEW, warm golden light streaming in, soft pastel colors, magical sparkles around them. Sweet connection, first eye contact, warm golden glow. STRICT: Maintain exact same child face and features as reference. Only ONE child, only ONE kitten MISU."
            },
            {
                "text_es": "Toco al gatito con mi mano.\nSu pelito es blandito.\nMe gusta sentirlo.",
                "text_en": "I touch the kitten with my hand.\nIts fur is so soft.\nI like how it feels.",
                "scene_template": "Disney 3D Pixar-style illustration of a baby sitting on a soft blanket, wearing a white onesie, sweet curious expression, gently reaching out with tiny baby hand to pet MISU (a tiny baby kitten with soft ginger-orange fur, bright green eyes). MISU sits still, eyes closed contentedly, enjoying the gentle touch. Nursery WIDE VIEW, warm soft lighting, mint green and cream tones, gentle sparkles. Tender moment of first touch, warm gentle magic. STRICT: Maintain exact same baby face and features as reference. Only ONE baby, only ONE kitten MISU.",
                "scene_template_toddler": "Disney 3D Pixar-style illustration of a toddler crouching down in the nursery, wearing a white onesie, sweet curious expression, gently reaching out with small hand to pet MISU (a tiny baby kitten with soft ginger-orange fur, bright green eyes). MISU sits still, eyes closed contentedly, enjoying the gentle touch. Nursery WIDE VIEW, warm soft lighting, mint green and cream tones, gentle sparkles. Tender moment of first touch, warm gentle magic. STRICT: Maintain exact same child face and features as reference. Only ONE child, only ONE kitten MISU."
            },
            {
                "text_es": "El gatito salta y juega.\nHace cosas divertidas.\n{name} ríe feliz.",
                "text_en": "The kitten jumps and plays.\nIt does funny things.\n{name} laughs happily.",
                "scene_template": "Disney 3D Pixar-style illustration of a baby sitting on soft nursery floor, wearing a white onesie, laughing joyfully while watching MISU (a tiny baby kitten with soft ginger-orange fur, bright green eyes, fluffy short tail) playing and jumping, chasing a small yarn ball. MISU is mid-leap, fluffy tail excited. Playful nursery WIDE VIEW, bright cheerful afternoon light, colorful toys scattered around, magical sparkles everywhere, warm golden sunset colors visible through window. Pure joy and playfulness, cheerful energy, warm sunset glow. STRICT: Maintain exact same baby face and features as reference. Only ONE baby, only ONE kitten MISU, no extra kittens, no tail on baby.",
                "scene_template_toddler": "Disney 3D Pixar-style illustration of a toddler standing in the nursery, wearing a white onesie, laughing joyfully while watching MISU (a tiny baby kitten with soft ginger-orange fur, bright green eyes, fluffy short tail) playing and jumping, chasing a small yarn ball. MISU is mid-leap, fluffy tail excited. Playful nursery WIDE VIEW, bright cheerful afternoon light, colorful toys scattered around, magical sparkles everywhere, warm golden sunset colors visible through window. Pure joy and playfulness, cheerful energy, warm sunset glow. STRICT: Maintain exact same child face and features as reference. Only ONE child, only ONE kitten MISU, no extra kittens, no tail on child."
            },
            {
                "text_es": "El gatito ronronea feliz.\nHace una bolita a mi lado.\n{name} lo acaricia con cariño.",
                "text_en": "The kitten purrs happily.\nIt curls into a ball beside me.\n{name} pets it lovingly.",
                "scene_template": "Disney 3D Pixar-style illustration of a baby sitting on a soft blanket, wearing a white onesie, gentle smile, baby's tiny hand gently resting on MISU's back. MISU (a tiny baby kitten with soft ginger-orange fur, bright green eyes) curled up as a ball next to the baby, purring contentedly. Cozy nursery WIDE VIEW, warm golden afternoon light streaming through window, peaceful calm atmosphere, mint green and cream tones, soft plush toys nearby. Tender bonding moment, warm afternoon glow. STRICT: Maintain exact same baby face and features as reference. Only ONE baby, only ONE kitten MISU curled up next to baby.",
                "scene_template_toddler": "Disney 3D Pixar-style illustration of a toddler sitting on the nursery floor on a soft blanket, wearing a white onesie, gentle smile, small hand gently resting on MISU's back. MISU (a tiny baby kitten with soft ginger-orange fur, bright green eyes) curled up as a ball next to the child, purring contentedly. Cozy nursery WIDE VIEW, warm golden afternoon light streaming through window, peaceful calm atmosphere, mint green and cream tones, soft plush toys nearby. Tender bonding moment, warm afternoon glow. STRICT: Maintain exact same child face and features as reference. Only ONE child, only ONE kitten MISU curled up next to child."
            },
            {
                "text_es": "La luna sale en el cielo.\nTodo se vuelve tranquilo.\nMISU bosteza despacito.\nYa casi es hora de dormir.",
                "text_en": "The moon rises in the sky.\nEverything becomes quiet.\nMISU yawns softly.\nIt's almost time to sleep.",
                "scene_template": "Disney 3D Pixar-style illustration of a baby sitting by a nursery window at night, wearing a white onesie, watching MISU and the moonlight with calm wonder. MISU (a tiny baby kitten with soft ginger-orange fur, bright green eyes) sitting on the windowsill looking at the moon. Peaceful nursery WIDE VIEW, gentle moonlight streaming through window, stars visible in the night sky, soft lavender and cream tones, gentle sparkles in the air. Peaceful nighttime transition, magical moonlight, calm wonder. STRICT: Maintain exact same baby face and features as reference. Only ONE baby, only ONE kitten MISU on windowsill.",
                "scene_template_toddler": "Disney 3D Pixar-style illustration of a toddler standing by a nursery window at night, wearing a white onesie, watching MISU and the moonlight with calm wonder. MISU (a tiny baby kitten with soft ginger-orange fur, bright green eyes) sitting on the windowsill looking at the moon. Peaceful nursery WIDE VIEW, gentle moonlight streaming through window, stars visible in the night sky, soft lavender and cream tones, gentle sparkles in the air. Peaceful nighttime transition, magical moonlight, calm wonder. STRICT: Maintain exact same child face and features as reference. Only ONE child, only ONE kitten MISU on windowsill."
            },
            {
                "text_es": "Es hora de descansar.\nMISU se acurruca conmigo.\nCierra los ojos, {name}.\nTe queremos.",
                "text_en": "Time to rest now.\nMISU snuggles close to me.\nClose your eyes, {name}.\nWe love you.",
                "scene_template": "Disney 3D Pixar-style illustration of a baby peacefully sleeping in a cozy crib, wearing a white onesie, eyes gently closed. MISU (a tiny baby kitten with soft ginger-orange fur, bright green eyes) curled up sleeping next to the baby, both resting on a cloud-soft blanket. Peaceful nursery WIDE VIEW, gentle moonlight streaming through window, soft lavender and cream tones, tiny stars twinkling outside. Serene peaceful moonlit calm, friendship and love. STRICT: Maintain exact same baby face and features as reference. Only ONE baby, only ONE kitten MISU curled up next to baby.",
                "scene_template_toddler": "Disney 3D Pixar-style illustration of a toddler peacefully sleeping in a cozy toddler bed, wearing a white onesie, eyes gently closed. MISU (a tiny baby kitten with soft ginger-orange fur, bright green eyes) curled up sleeping next to the child, both resting on a cloud-soft blanket. Peaceful nursery WIDE VIEW, gentle moonlight streaming through window, soft lavender and cream tones, tiny stars twinkling outside. Serene peaceful moonlit calm, friendship and love. STRICT: Maintain exact same child face and features as reference. Only ONE child, only ONE kitten MISU curled up next to child."
            }
        ],
    },
    "baby_guardian_light": {
        "title_es": "{name} y la luz que {lo_la} cuida",
        "title_en": "{name} and the Light That Watches Over",
        "age_range": "0-1",
        "use_ideogram_scenes": True,
        "use_preview_as_cover": True,
        "preview_prompt_override": "Disney 3D Pixar-style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_desc}, extremely chubby cheeks, round baby face, tiny hands, innocent sweet expression. WEARING: Plain soft white onesie with diaper visible. ACTION: Baby is sitting on a soft pastel blanket with a tiny smooth featureless sphere of pure warm golden light (NO face, NO eyes, NO text, NO letters, NO words on it, just a simple round glowing ball with gentle rays) floating gently nearby, casting a warm soft protective glow toward the baby. Soft toys visible in background. ENVIRONMENT: Cozy nursery, soft pastel lavender and cream walls, gentle sparkles floating. ATMOSPHERE: Warm dreamy magical golden light, love and protection, soft luminous colors. STRICT: Only ONE baby, baby is 100% human, NO animal ears, NO animal features on baby, baby wearing WHITE onesie. NO text, NO watermark, NO signature, NO logo",
        "preview_prompt_override_toddler": "Disney 3D Pixar-style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_desc}, chubby cheeks, round toddler face, small hands, innocent curious expression. WEARING: Plain soft white onesie. ACTION: Toddler is standing on tiny feet on a soft pastel blanket, looking up with wonder at a tiny smooth featureless sphere of pure warm golden light (NO face, NO eyes, NO text, NO letters, NO words on it, just a simple round glowing ball with gentle rays) floating gently above, casting a warm soft protective glow toward the child. Soft toys visible in background. ENVIRONMENT: Cozy nursery, soft pastel lavender and cream walls, gentle sparkles floating. ATMOSPHERE: Warm dreamy magical golden light, love and protection, soft luminous colors. STRICT: Only ONE toddler, child is 100% human, NO animal ears, NO animal features on child. NO text, NO watermark, NO signature, NO logo",
        "cover_template": "Disney 3D Pixar-style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, extremely chubby cheeks, round baby face, sweet innocent expression. WEARING: Plain soft white onesie. ACTION: Baby is sitting on a soft pastel blanket with {guardian_light_desc} floating gently above, casting a warm protective glow on the baby. Soft plush toys nearby. ENVIRONMENT: Dreamy soft lavender, gold and cream background, gentle sparkles. ATMOSPHERE: Magical book cover composition centered, warm golden light radiating love, ultra soft textures. STRICT: Only ONE baby, baby is 100% human, no animal features, baby wearing WHITE onesie. {style}",
        "pages": [
            {
                "text_es": "Una pequeña luz aparece.\nViene para cuidarte, mi tesoro.\nBrilla suave.",
                "text_en": "A small light appears.\nIt comes to watch over you, my treasure.\nIt glows softly.",
                "scene_template": "Disney 3D Pixar-style illustration of a baby sitting on a soft pastel nursery floor, wearing a white onesie, looking up with wonder as a tiny smooth featureless sphere of pure warm golden light (NO face, NO eyes, NO text, NO letters, NO words on it, just a simple round glowing ball with gentle rays) appears floating gently in the room, casting a warm soft glow. Soft plush toys scattered nearby. Cozy nursery WIDE VIEW, soft evening light, lavender and cream walls, cream-colored furniture, gentle sparkles emanating from the glowing sphere. Warm magical love and protection, soft golden glow. STRICT: Maintain exact same baby face and features as reference. Only ONE baby, baby is 100% human.",
                "scene_template_toddler": "Disney 3D Pixar-style illustration of a toddler standing on the soft pastel nursery floor, wearing a white onesie, looking up with wonder as a tiny smooth featureless sphere of pure warm golden light (NO face, NO eyes, NO text, NO letters, NO words on it, just a simple round glowing ball with gentle rays) appears floating gently in the room, casting a warm soft glow. Soft plush toys scattered nearby. Cozy nursery WIDE VIEW, soft evening light, lavender and cream walls, cream-colored furniture, gentle sparkles emanating from the glowing sphere. Warm magical love and protection, soft golden glow. STRICT: Maintain exact same child face and features as reference. Only ONE child, child is 100% human."
            },
            {
                "text_es": "La luz se mueve despacio.\nNo hace ruido.\nTodo es calma.",
                "text_en": "The light moves slowly.\nIt makes no sound.\nAll is calm.",
                "scene_template": "Disney 3D Pixar-style illustration of a baby sitting on a soft blanket, wearing a white onesie, watching peacefully as a tiny smooth featureless sphere of pure warm golden light (NO face, NO eyes, NO text, NO letters, NO words on it, just a simple round glowing ball) floats slowly and gracefully through the room, leaving a soft trail of golden sparkles behind. Peaceful nursery WIDE VIEW, serene atmosphere, soft lavender and cream tones, plush toys on floor, everything bathed in gentle warm glow. Tranquil magical calm, serene golden warmth. STRICT: Maintain exact same baby face and features as reference. Only ONE baby, baby is 100% human.",
                "scene_template_toddler": "Disney 3D Pixar-style illustration of a toddler standing in the nursery, wearing a white onesie, watching peacefully as a tiny smooth featureless sphere of pure warm golden light (NO face, NO eyes, NO text, NO letters, NO words on it, just a simple round glowing ball) floats slowly and gracefully through the room, leaving a soft trail of golden sparkles behind. Peaceful nursery WIDE VIEW, serene atmosphere, soft lavender and cream tones, plush toys on floor, everything bathed in gentle warm glow. Tranquil magical calm, serene golden warmth. STRICT: Maintain exact same child face and features as reference. Only ONE child, child is 100% human."
            },
            {
                "text_es": "A la luz le encanta verte reír.\nTe observa con ternura.\nTodo es amor.",
                "text_en": "The light loves to see you laugh.\nIt watches you tenderly.\nAll is love.",
                "scene_template": "Disney 3D Pixar-style illustration of a baby sitting on a soft blanket, wearing a white onesie, laughing happily while a tiny smooth featureless sphere of pure warm golden light (NO face, NO eyes, NO text, NO letters, NO words on it, just a simple round glowing ball) floats nearby, glowing brighter with joy, pulsing warmly as if responding to the baby's laughter. Joyful nursery WIDE VIEW, warm golden light filling the room, soft toys around, floating hearts and sparkles. Pure love and happiness, responsive magical glow. STRICT: Maintain exact same baby face and features as reference. Only ONE baby, baby is 100% human.",
                "scene_template_toddler": "Disney 3D Pixar-style illustration of a toddler standing in the nursery, wearing a white onesie, laughing happily while a tiny smooth featureless sphere of pure warm golden light (NO face, NO eyes, NO text, NO letters, NO words on it, just a simple round glowing ball) floats nearby, glowing brighter with joy, pulsing warmly as if responding to the child's laughter. Joyful nursery WIDE VIEW, warm golden light filling the room, soft toys around, floating hearts and sparkles. Pure love and happiness, responsive magical glow. STRICT: Maintain exact same child face and features as reference. Only ONE child, child is 100% human."
            },
            {
                "text_es": "La luz mira a {name}.\nTe cuida mientras juegas.\nSiempre está cerca.",
                "text_en": "The light watches {name}.\nIt cares for you while you play.\nIt's always near.",
                "scene_template": "Disney 3D Pixar-style illustration of a baby sitting on soft nursery floor, wearing a white onesie, playful expression, playing with soft colorful toys while a tiny smooth featureless sphere of pure warm golden light (NO face, NO eyes, NO text, NO letters, NO words on it, just a simple round glowing ball) floats protectively nearby, hovering close, casting a warm protective glow over the baby. Playful nursery WIDE VIEW, cheerful afternoon light, pastel colors, various plush toys scattered, magical sparkles around the glowing sphere, warm golden sunlight through window. Sweet protective warmth, playful guardian energy. STRICT: Maintain exact same baby face and features as reference. Only ONE baby, baby is 100% human.",
                "scene_template_toddler": "Disney 3D Pixar-style illustration of a toddler standing in the nursery, wearing a white onesie, playful expression, playing with soft colorful toys while a tiny smooth featureless sphere of pure warm golden light (NO face, NO eyes, NO text, NO letters, NO words on it, just a simple round glowing ball) floats protectively nearby, hovering close, casting a warm protective glow over the child. Playful nursery WIDE VIEW, cheerful afternoon light, pastel colors, various plush toys scattered, magical sparkles around the glowing sphere, warm golden sunlight through window. Sweet protective warmth, playful guardian energy. STRICT: Maintain exact same child face and features as reference. Only ONE child, child is 100% human."
            },
            {
                "text_es": "Esa luz cuida y protege.\nTodo está bien.\nNada te falta.",
                "text_en": "That light cares and protects.\nAll is well.\nYou need nothing more.",
                "scene_template": "Disney 3D Pixar-style illustration of a baby sitting contentedly on a soft blanket, wearing a white onesie, peaceful expression, surrounded by a tiny smooth featureless sphere of pure warm golden light (NO face, NO eyes, NO text, NO letters, NO words on it, just a simple round glowing ball) that creates a soft warm halo of protection around the baby. The sphere glows steadily, emanating peace and security. Protected nursery WIDE VIEW, soft warm light, lavender and gold tones, floating sparkles forming a gentle protective circle around baby. Serene complete safety and love, warm protective halo. STRICT: Maintain exact same baby face and features as reference. Only ONE baby, baby is 100% human.",
                "scene_template_toddler": "Disney 3D Pixar-style illustration of a toddler standing contentedly in the nursery, wearing a white onesie, peaceful expression, surrounded by a tiny smooth featureless sphere of pure warm golden light (NO face, NO eyes, NO text, NO letters, NO words on it, just a simple round glowing ball) that creates a soft warm halo of protection around the child. The sphere glows steadily, emanating peace and security. Protected nursery WIDE VIEW, soft warm light, lavender and gold tones, floating sparkles forming a gentle protective circle around child. Serene complete safety and love, warm protective halo. STRICT: Maintain exact same child face and features as reference. Only ONE child, child is 100% human."
            },
            {
                "text_es": "La luz baila con las estrellas.\n{name} mira el cielo.\nTodo brilla con amor.",
                "text_en": "The light dances with the stars.\n{name} looks at the sky.\nEverything shines with love.",
                "scene_template": "Disney 3D Pixar-style illustration of a baby sitting on a soft blanket by a nursery window at night, wearing a white onesie, gentle closed-mouth smile, looking up with soft wonder, mouth closed. a tiny smooth featureless sphere of pure warm golden light (NO face, NO eyes, NO text, NO letters, NO words on it, just a simple round glowing ball) floating outside the window among stars, dancing gracefully, creating trails of golden sparkles. Magical night sky visible through window WIDE VIEW, stars twinkling, golden trails of light, soft lavender and cream nursery tones. Magical starlight dance, wonder and love. STRICT: Maintain exact same baby face and features as reference. Only ONE baby, baby is 100% human. Baby has CLOSED MOUTH, gentle smile.",
                "scene_template_toddler": "Disney 3D Pixar-style illustration of a toddler standing by a nursery window at night, wearing a white onesie, gentle closed-mouth smile, looking up with soft wonder, mouth closed. a tiny smooth featureless sphere of pure warm golden light (NO face, NO eyes, NO text, NO letters, NO words on it, just a simple round glowing ball) floating outside the window among stars, dancing gracefully, creating trails of golden sparkles. Magical night sky visible through window WIDE VIEW, stars twinkling, golden trails of light, soft lavender and cream nursery tones. Magical starlight dance, wonder and love. STRICT: Maintain exact same child face and features as reference. Only ONE child, child is 100% human. Child has CLOSED MOUTH, gentle smile."
            },
            {
                "text_es": "La luz se acerca despacio.\nSe posa a tu lado.\nSuave, tranquila.\nYa casi es hora de dormir.",
                "text_en": "The light comes closer slowly.\nIt settles beside you.\nSoft and calm.\nIt's almost time to sleep.",
                "scene_template": "Disney 3D Pixar-style illustration of a baby sitting on a soft blanket, wearing a white onesie, peaceful smile. a tiny smooth featureless sphere of pure warm golden light (NO face, NO eyes, NO text, NO letters, NO words on it, just a simple round glowing ball) floating very close beside the baby at eye level, glowing gently dimmer like a nightlight. Peaceful nursery WIDE VIEW, soft evening light dimming, lavender and cream tones, calm atmosphere, gentle sparkles. Peaceful nighttime transition, gentle calming glow. STRICT: Maintain exact same baby face and features as reference. Only ONE baby, baby is 100% human.",
                "scene_template_toddler": "Disney 3D Pixar-style illustration of a toddler sitting on the edge of a toddler bed, wearing a white onesie, peaceful smile. a tiny smooth featureless sphere of pure warm golden light (NO face, NO eyes, NO text, NO letters, NO words on it, just a simple round glowing ball) floating very close beside the child at eye level, glowing gently dimmer like a nightlight. Peaceful nursery WIDE VIEW, soft evening light dimming, lavender and cream tones, calm atmosphere, gentle sparkles. Peaceful nighttime transition, gentle calming glow. STRICT: Maintain exact same child face and features as reference. Only ONE child, child is 100% human."
            },
            {
                "text_es": "Es hora de descansar.\nLa luz cuida tu sueño.\nCierra los ojos, {name}.\nTe queremos.",
                "text_en": "Time to rest now.\nThe light watches over your dreams.\nClose your eyes, {name}.\nWe love you.",
                "scene_template": "Disney 3D Pixar-style illustration of a baby peacefully sleeping in a cozy crib, wearing a white onesie, eyes gently closed. a tiny smooth featureless sphere of pure warm golden light (NO face, NO eyes, NO text, NO letters, NO words on it, just a simple round glowing ball) floating softly beside the baby like a gentle nightlight, glowing with eternal love. Cloud-soft blanket covering the baby. Peaceful nursery WIDE VIEW, gentle moonlight through window, soft lavender and cream tones, tiny stars twinkling outside, the sphere casting a warm protective glow. Serene eternal love and protection, moonlit dreamtime. STRICT: Maintain exact same baby face and features as reference. Only ONE baby, baby is 100% human.",
                "scene_template_toddler": "Disney 3D Pixar-style illustration of a toddler peacefully sleeping in a cozy toddler bed, wearing a white onesie, eyes gently closed. a tiny smooth featureless sphere of pure warm golden light (NO face, NO eyes, NO text, NO letters, NO words on it, just a simple round glowing ball) floating softly beside the child like a gentle nightlight, glowing with eternal love. Cloud-soft blanket covering the child. Peaceful nursery WIDE VIEW, gentle moonlight through window, soft lavender and cream tones, tiny stars twinkling outside, the sphere casting a warm protective glow. Serene eternal love and protection, moonlit dreamtime. STRICT: Maintain exact same child face and features as reference. Only ONE child, child is 100% human."
            }
        ],
    },
    "dragon_friend": {
        "title_es": "{name} y su Amigo el Dragón",
        "title_en": "{name} and Their Dragon Friend",
        "age_range": "3-8",
        "text_layout": "split",
        "use_preview_as_cover": True,
        "preview_prompt_override": "Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, curious wonder-filled expression, gentle smile. OUTFIT: Soft blue tunic with gold leaf embroidery, brown pants, small boots. ACTION: {gender_word} is standing beside a majestic old oak tree, looking UP in amazement at {spark_desc} who has just stepped out from behind the trunk. Spark stands at FULL HEIGHT towering over {gender_word}, Spark tilts head curiously looking DOWN at {gender_word}, tiny puff of sparkly smoke coming from Spark's snout. SETTING: Enchanted garden WIDE VIEW, glowing flowers, butterflies, mushroom circles, stone path, morning golden sunlight filtering through tree canopy. ATMOSPHERE: Discovery and wonder, warm golden light, magical sparkles in the air. STRICT: Only ONE {gender_word}, only ONE baby dragon Spark. Spark MUST BE TWICE AS TALL as {gender_word}. {gender_word} is 100% human, with a completely normal body, two arms, two legs, smooth skin, and normal child anatomy, no duplicates. {style}",
        "cover_template": "Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, warm loving smile, bright eyes full of adventure. OUTFIT: Comfortable soft blue tunic with gold leaf embroidery. ACTION: {gender_word} is hugging the belly of {spark_desc}, {gender_word} wraps arms around Spark's large round belly, both looking at the viewer with joy, standing in a sunny wildflower meadow. SETTING: Rolling green hills, rainbow arching across blue sky, colorful wildflowers, butterflies flying, golden afternoon light. ATMOSPHERE: Magical book cover composition centered, warm golden sparkles in air, friendship and adventure. STRICT: Only ONE {gender_word}, only ONE baby dragon Spark. Spark MUST BE TWICE AS TALL as {gender_word}. {gender_word} is 100% human, with a completely normal body, two arms, two legs, smooth skin, and normal child anatomy. {style}",
        "pages": [
            {
                "text_above_es": "Una soleada mañana, {name} descubrió algo extraordinario escondido detrás del viejo roble del jardín. ¡Era un pequeño dragón con escamas de esmeralda brillante y grandes ojos dorados!",
                "text_below_es": "El dragoncito parecía asustado y solo. \"No tengas miedo\", susurró {name} suavemente. \"No te haré daño.\"",
                "text_above_en": "One sunny morning, {name} discovered something extraordinary hiding behind the old oak tree in the garden. It was a tiny dragon with shimmering emerald scales and big golden eyes!",
                "text_below_en": "The little dragon looked scared and lonely. \"Don't be afraid,\" {name} whispered softly. \"I won't hurt you.\"",
                "scene_template": "Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, curious wonder-filled expression, gentle smile. OUTFIT: Soft blue tunic with gold leaf embroidery, brown pants, small boots. ACTION: {gender_word} is standing beside a majestic old oak tree, looking UP in amazement at {spark_desc} who has just stepped out from behind the trunk. Spark stands at FULL HEIGHT towering over {gender_word}, Spark tilts head curiously looking DOWN at {gender_word}, tiny puff of sparkly smoke coming from Spark's snout. SETTING: Enchanted garden WIDE VIEW, glowing flowers, butterflies, mushroom circles, stone path, morning golden sunlight filtering through tree canopy. ATMOSPHERE: Discovery and wonder, warm golden light, magical sparkles in the air. STRICT: Only ONE {gender_word}, only ONE baby dragon Spark. Spark MUST BE TWICE AS TALL as {gender_word}. {gender_word} is 100% human, with a completely normal body, two arms, two legs, smooth skin, and normal child anatomy, no duplicates. {style}"
            },
            {
                "text_above_es": "El pequeño dragón inclinó la cabeza con curiosidad y soltó una pequeña bocanada de humo brillante. {name} se arrodilló y extendió la mano con cuidado.",
                "text_below_es": "El dragoncito olisqueó los dedos de {name} y frotó su cabecita contra su palma. En ese momento nació una amistad mágica. {name} decidió llamarlo Chispa.",
                "text_above_en": "The little dragon tilted its head curiously and let out a tiny puff of sparkly smoke. {name} knelt down and reached out a hand carefully.",
                "text_below_en": "The little dragon sniffed {name}'s fingers, then nuzzled its head against the palm. In that moment, a magical friendship was born. {name} decided to call it Spark.",
                "scene_template": "Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, tender loving expression, eyes soft with affection. OUTFIT: Soft blue tunic with gold leaf embroidery, brown pants, small boots. ACTION: {gender_word} is standing on soft grass, reaching UP with one hand to touch Spark's face. {spark_desc} is lowering its large head DOWN to meet {gender_word}'s hand, golden sparkles appearing where they touch, Spark's wings fluttering with happiness. Spark towers over {gender_word}. SETTING: Enchanted garden WIDE VIEW, dappled sunlight through leaves, soft moss, wildflowers, gentle breeze. ATMOSPHERE: Tender first connection, magical golden sparkles at point of touch, warmth and trust. STRICT: Only ONE {gender_word}, only ONE baby dragon Spark. Spark MUST BE TWICE AS TALL as {gender_word}. {gender_word} is 100% human, with a completely normal body, two arms, two legs, smooth skin, and normal child anatomy, no duplicates. {style}"
            },
            {
                "text_above_es": "{name} y Chispa se convirtieron en los mejores amigos. Cada día jugaban juntos en secreto en el jardín encantado.",
                "text_below_es": "Chispa perseguía mariposas soltando chispitas de colores mientras {name} reía sin parar. ¡Nunca se había divertid{o_a} tanto!",
                "text_above_en": "{name} and Spark became the best of friends. Every day they played together in secret in the enchanted garden.",
                "text_below_en": "Spark chased butterflies while releasing tiny colorful sparks as {name} laughed nonstop. Never before had so much fun!",
                "scene_template": "Disney Pixar 3D style illustration. CHARACTER 1: The human {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, laughing with joy. A normal human body, two arms, two legs, smooth skin. OUTFIT: Soft blue tunic with gold leaf embroidery, brown pants, small boots. CHARACTER 2: Spark, the giant baby dragon, TOWERING over the {gender_word}. Spark is three times the {gender_word}'s height, with shimmering emerald-green scales, a very chubby round body, large golden eyes, small translucent wings, cream-colored belly. ACTION: The {gender_word} runs through a wide garden while the massive dragon Spark jumps playfully beside the {gender_word}. Spark releases rainbow sparkles from his snout. SETTING: WIDE ANGLE VIEW of an enchanted garden, lush green lawns, colorful butterflies, and ancient trees. COMPOSITION: The {gender_word} is small and human; Spark is a separate, massive, and giant emerald creature. The scale difference is immense. {style}"
            },
            {
                "text_above_es": "Una noche, Chispa le enseñó a {name} un secreto especial. En lo profundo del jardín crecían flores que brillaban bajo la luz de la luna.",
                "text_below_es": "{name} tocó un pétalo y una lluvia de destellos dorados llenó el aire. \"Esta magia solo aparece para quienes tienen un corazón bondadoso\", dijo Chispa.",
                "text_above_en": "One night, Spark showed {name} a special secret. Deep in the garden grew flowers that glowed under the moonlight.",
                "text_below_en": "{name} touched a petal and a shower of golden sparkles filled the air. \"This magic only appears for those with a kind heart,\" said Spark.",
                "scene_template": "Disney Pixar 3D style illustration. CHARACTER 1: The human {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, kneeling with a look of wonder. A normal human body, two arms, two legs, smooth skin. OUTFIT: Soft blue tunic with gold leaf embroidery, brown pants, small boots. CHARACTER 2: Spark, the giant baby dragon, sitting beside the {gender_word}. Even sitting, Spark is massive and twice as tall as the {gender_word}, with shimmering emerald-green scales, a very chubby round body, large golden eyes, small translucent wings, cream-colored belly. ACTION: The {gender_word}'s human hand touches a glowing flower. Spark watches with a kind smile, his huge emerald body filling the frame next to the {gender_word}. SETTING: WIDE ANGLE moonlit garden, bioluminescent blue flowers, silvery starlight, and soft mist. COMPOSITION: A tiny human child next to a towering, massive giant dragon. Clear physical separation between the child and the creature. {style}"
            },
            {
                "text_above_es": "Una tarde, Chispa se veía triste. Sus alitas estaban caídas. \"Echo de menos a mi familia en las montañas\", dijo con una vocecita.",
                "text_below_es": "El corazón de {name} se llenó de ternura. \"Te ayudaré a encontrar el camino a casa\", prometió {name}, abrazando fuerte al pequeño dragón.",
                "text_above_en": "One afternoon, Spark looked sad. Its little wings drooped low. \"I miss my family in the mountains,\" Spark said with a tiny voice.",
                "text_below_en": "{name}'s heart filled with tenderness. \"I'll help you find your way home,\" {name} promised, hugging the little dragon tightly.",
                "scene_template": "Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, tender compassionate expression, eyes glistening with empathy. OUTFIT: Soft blue tunic with gold leaf embroidery, brown pants, small boots. ACTION: {gender_word} is standing and wrapping both arms around the large round belly of {spark_desc} in a tight hug. Spark is TWICE AS TALL as {gender_word} so {gender_word} only reaches Spark's belly. Spark has drooping wings and sad golden eyes, a single tiny tear on cheek, lowering its large head DOWN to rest gently on top of {gender_word}'s head for comfort. SETTING: Garden at golden hour WIDE VIEW, warm amber sunset light, autumn leaves floating gently, distant mountains visible on horizon. ATMOSPHERE: Bittersweet tenderness, warm golden sunset glow, comfort and promise, emotional depth. STRICT: Only ONE {gender_word}, only ONE baby dragon Spark. Spark MUST BE TWICE AS TALL as {gender_word}. {gender_word} is 100% human, with a completely normal body, two arms, two legs, smooth skin, and normal child anatomy, no duplicates. {style}"
            },
            {
                "text_above_es": "Chispa extendió sus alas, que brillaron con luz dorada. ¡Habían crecido! {name} subió a su espalda y juntos se elevaron sobre las nubes.",
                "text_below_es": "Volaron sobre valles de arcoíris y ríos de cristal que reflejaban las estrellas. El viento suave acariciaba la cara de {name} mientras reía de felicidad.",
                "text_above_en": "Spark spread its wings, which glowed with golden light. They had grown! {name} climbed on its back and together they soared above the clouds.",
                "text_below_en": "They flew over rainbow valleys and crystal rivers that reflected the stars. The gentle wind caressed {name}'s face while laughing with happiness.",
                "scene_template": "Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, face showing pure joy and exhilaration, {hair_action}, laughing with wind in face. OUTFIT: Soft blue tunic with gold leaf embroidery, brown pants, small boots. ACTION: {gender_word} is riding on the back of {spark_desc} who has grown large enough to carry {gender_word} comfortably, both soaring through clouds high in the sky. {gender_word} holding gently onto Spark's back, {gender_word} is FULL SIZE not miniaturized. SETTING: High above the clouds WIDE VIEW, rainbow valleys below, crystal blue rivers, candy-colored forests, tiny villages on rolling green hills, golden sunset clouds. ATMOSPHERE: Freedom and exhilaration, magical flight, golden sparkles trailing behind, wind and wonder. STRICT: Only ONE {gender_word} riding ONE dragon Spark, {gender_word} must be NORMAL CHILD SIZE not tiny, dragon is large enough to carry {gender_word}, {gender_word} is 100% human, with a completely normal body, two arms, two legs, smooth skin, and normal child anatomy. {style}"
            },
            {
                "text_above_es": "En las Montañas de los Dragones, una familia de hermosos dragones dio la bienvenida a Chispa con rugidos alegres. La mamá dragón, una majestuosa dragona de escamas doradas y ojos amables, inclinó su enorme cabeza ante {name}. \"Gracias por cuidar de nuestro pequeño.\"",
                "text_below_es": "Chispa le dio a {name} una escama mágica que brillaba como la luz de las estrellas. \"Cuando la sostengas, recuerda nuestra amistad.\" Y {name} supo que la verdadera magia vive en el corazón.",
                "text_above_en": "At the Dragon Mountains, a family of beautiful dragons welcomed Spark with joyful roars. The mother dragon, a majestic dragoness with golden scales and kind eyes, bowed her enormous head to {name}. \"Thank you for taking care of our little one.\"",
                "text_below_en": "Spark gave {name} a magical scale that glowed like starlight. \"Whenever you hold this, remember our friendship.\" And {name} knew that true magic lives in the heart.",
                "scene_template": "Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, smiling with happy tears, holding a glowing starlight dragon scale. OUTFIT: Soft blue tunic with gold leaf embroidery, brown pants, small boots. ACTION: {gender_word} stands on a mountain cliff edge, holding the glowing scale close, looking UP at {spark_desc} who looks DOWN with grateful joyful eyes. In the far background, a colossal golden dragoness with warm amber eyes and enormous spread wings bows her head gently. SETTING: Majestic Dragon Mountains WIDE VIEW, purple-blue peaks, crystal waterfalls, golden sunset sky with orange and pink clouds. ATMOSPHERE: Emotional farewell, warm golden light, magical sparkles, friendship and gratitude. STRICT: Only ONE {gender_word}, only ONE baby dragon Spark, one golden dragoness in background. {gender_word} is 100% human with normal child anatomy. {style}"
            }
        ],
        "closing_template": """Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, round normal human ears, warm proud smile, eyes sparkling with confidence and joy. A normal human body, two arms, two legs, and smooth skin. OUTFIT: Soft blue tunic with gold leaf embroidery, brown pants, small boots. ACTION: The {gender_word} is standing alone on a hilltop at golden hour, one {skin_tone} hand holding the glowing dragon scale close to heart, looking up at the sky with a peaceful happy expression, {hair_action}. SETTING: Beautiful enchanted garden hilltop WIDE VIEW, wildflowers blooming everywhere, golden sunset painting the sky in warm orange and pink, distant mountains visible, butterflies and magical sparkles floating in the warm breeze. ATMOSPHERE: Triumphant peaceful moment, warm golden light, magical sparkles, sense of accomplishment and inner strength. STRICT: Only ONE {gender_word}, NO dragon, NO companion, NO other characters. {style}""",
        "closing_message_es": "{name}, tu corazón valiente puede hacer florecer la magia en cualquier lugar.",
        "closing_message_en": "{name}, your brave heart can make magic bloom anywhere."
    },
    "dragon_garden_illustrated": {
        "title_es": "{name} y el Jardín del Dragón",
        "title_en": "{name} and the Dragon Garden",
        "age_range": "3-5",
        "book_type": "illustrated",
        "price": 45,
        "page_count": 24,
        "use_fixed_scenes": True,
        "scenes_dir": "static/assets/dragon_garden_scenes",
        "cover_background": "cover_background.png",
        "title_background": "scene_01_entrance.png",
        "dedication_background": "dedication_background.png",
        "back_cover": "back_cover.png",
        "closing_scene": "scene_final_sleeping.png",
        "preview_prompt_override": "Full body portrait of a cheerful {gender_word} (4-5 years old) with {hair_desc}, {eye_desc} and {skin_desc}, {gender_features}, wearing a soft purple tunic with golden star embroidery, standing in an enchanted magical garden with glowing flowers and sparkles, next to a small friendly emerald green baby dragon (Spark) with big kind eyes and tiny wings. The child has a warm smile and one hand gently touching the dragon. Magical fairy tale atmosphere, soft warm golden light filtering through ancient trees, floating sparkles and fireflies in the air. Children's storybook watercolor illustration style, soft luminous colors, dreamy magical atmosphere. NO text, NO watermark, NO signature, NO logo, clean illustration only",
        "cover_template": "Magical storybook cover illustration: a brave {gender_child} with {hair_desc} and {skin_tone} skin standing in an enchanted garden, next to {spark_desc}. WIDE VIEW showing magical garden environment with glowing flowers, ancient oak tree, stone path. Soft morning light, sparkles in the air. The child has a warm smile, hand gently touching the dragon. Fantasy fairy tale atmosphere, centered composition perfect for book cover. {style}",
        "content_pages": [
            {
                "text_es": "Había una vez, en un lugar donde los sueños cobran vida, un jardín mágico escondido detrás de un viejo roble. Solo los niños de corazón puro podían encontrarlo.",
                "text_en": "Once upon a time, in a place where dreams come alive, there was a magical garden hidden behind an old oak tree. Only children with pure hearts could find it.",
                "fixed_scene": "scene_01_entrance.png"
            },
            {
                "text_es": "De pronto, {name} escuchó un sonido suave. ¡Era un pequeño dragón con escamas de esmeralda brillante! \"¡Hola! Me llamo Chispa\", dijo el dragoncito con una sonrisa amable.",
                "text_en": "Suddenly, {name} heard a soft sound. It was a tiny dragon with shimmering emerald scales! \"Hello! My name is Spark,\" said the little dragon with a kind smile.",
                "fixed_scene": "scene_02_meeting_dragon.png"
            },
            {
                "text_es": "\"¿Quieres volar conmigo?\", preguntó Chispa emocionado. {name} subió a su espalda y juntos se elevaron sobre las nubes de algodón, sintiendo el viento suave.",
                "text_en": "\"Would you like to fly with me?\" asked Spark excitedly. {name} climbed on his back and together they soared above the cotton clouds, feeling the gentle wind.",
                "fixed_scene": "scene_03_flying.png"
            },
            {
                "text_es": "Volaron sobre un arcoíris brillante que pintaba el cielo con todos los colores imaginables. \"Cada color tiene un poder especial\", explicó Chispa.",
                "text_en": "They flew over a brilliant rainbow that painted the sky with every imaginable color. \"Each color has a special power,\" explained Spark.",
                "fixed_scene": "scene_04_rainbow.png"
            },
            {
                "text_es": "Aterrizaron junto a flores gigantes de pétalos suaves. Las mariposas danzaban alrededor mientras el aroma dulce llenaba el aire.",
                "text_en": "They landed next to giant flowers with soft petals. Butterflies danced around while the sweet fragrance filled the air.",
                "fixed_scene": "scene_05_giant_flowers.png"
            },
            {
                "text_es": "En el corazón del jardín, conocieron a los animalitos mágicos: conejos con alas de cristal, ardillas que brillaban como estrellas y pájaros cantores de plumas doradas.",
                "text_en": "In the heart of the garden, they met the magical little animals: rabbits with crystal wings, squirrels that glowed like stars, and songbirds with golden feathers.",
                "fixed_scene": "scene_06_forest_friends.png"
            },
            {
                "text_es": "Chispa llevó a {name} a una cueva secreta llena de cristales brillantes. Los colores bailaban en las paredes como un caleidoscopio mágico.",
                "text_en": "Spark took {name} to a secret cave full of shining crystals. The colors danced on the walls like a magical kaleidoscope.",
                "fixed_scene": "scene_07_crystal_cave.png"
            },
            {
                "text_es": "Siguieron un río que brillaba con reflejos de estrellas caídas. Pequeños peces luminosos saltaban felices entre las olas cristalinas.",
                "text_en": "They followed a river that glowed with reflections of fallen stars. Small luminous fish jumped happily among the crystal waves.",
                "fixed_scene": "scene_08_star_river.png"
            },
            {
                "text_es": "Chispa mostró a {name} su nido con huevos dorados. \"Algún día nacerán más dragones mágicos\", dijo con orgullo y ternura en sus ojos.",
                "text_en": "Spark showed {name} his nest with golden eggs. \"Someday more magical dragons will be born,\" he said with pride and tenderness in his eyes.",
                "fixed_scene": "scene_09_dragon_nest.png"
            },
            {
                "text_es": "Descubrieron una cascada de cristal que formaba arcoíris en el aire. El agua brillaba como diamantes líquidos bajo el sol mágico.",
                "text_en": "They discovered a crystal waterfall that formed rainbows in the air. The water sparkled like liquid diamonds under the magical sun.",
                "fixed_scene": "scene_10_waterfall.png"
            },
            {
                "text_es": "En un círculo de hongos gigantes, las hadas bailaban felices. Invitaron a {name} a unirse a su danza bajo las luces brillantes.",
                "text_en": "In a circle of giant mushrooms, the fairies danced happily. They invited {name} to join their dance under the bright lights.",
                "fixed_scene": "scene_11_mushroom_circle.png"
            },
            {
                "text_es": "Volaron tan alto que llegaron al reino de las nubes, donde los castillos flotaban y los ángeles jugaban entre algodones de colores.",
                "text_en": "They flew so high they reached the kingdom of clouds, where castles floated and angels played among colorful cotton.",
                "fixed_scene": "scene_12_cloud_kingdom.png"
            },
            {
                "text_es": "En el centro del jardín encontraron un árbol antiguo donde cada hoja brillaba con un deseo cumplido. {name} tocó una hoja y sintió calidez en el corazón.",
                "text_en": "In the center of the garden they found an ancient tree where each leaf glowed with a fulfilled wish. {name} touched a leaf and felt warmth in their heart.",
                "fixed_scene": "scene_13_wishing_tree.png"
            },
            {
                "text_es": "Chispa reveló una sala secreta llena de tesoros mágicos: libros que contaban historias solas, brújulas que señalaban hacia los sueños y llaves de mundos lejanos.",
                "text_en": "Spark revealed a secret room full of magical treasures: books that told stories by themselves, compasses that pointed to dreams, and keys to distant worlds.",
                "fixed_scene": "scene_14_treasure_room.png"
            },
            {
                "text_es": "Cruzaron un prado donde miles de mariposas brillantes creaban una danza de colores. Sus alas dejaban estelas de polvo de estrellas.",
                "text_en": "They crossed a meadow where thousands of glowing butterflies created a dance of colors. Their wings left trails of stardust.",
                "fixed_scene": "scene_15_butterfly_meadow.png"
            },
            {
                "text_es": "\"Quiero que aprendas algo especial\", dijo Chispa. Y le enseñó a {name} que con imaginación y valentía, todos podemos volar en nuestros sueños.",
                "text_en": "\"I want to teach you something special,\" said Spark. And he taught {name} that with imagination and courage, we can all fly in our dreams.",
                "fixed_scene": "scene_16_flying_lesson.png"
            },
            {
                "text_es": "Juntos observaron la puesta de sol más hermosa, donde el cielo se pintó de rosa, naranja y púrpura, mientras las primeras estrellas aparecían.",
                "text_en": "Together they watched the most beautiful sunset, where the sky painted itself pink, orange, and purple, while the first stars appeared.",
                "fixed_scene": "scene_17_sunset.png"
            },
            {
                "text_es": "\"Siempre seremos amigos\", prometió Chispa. \"Cada vez que mires las estrellas, estaré pensando en ti.\"",
                "text_en": "\"We will always be friends,\" promised Spark. \"Every time you look at the stars, I will be thinking of you.\"",
                "fixed_scene": "scene_18_promise.png"
            },
            {
                "text_es": "{name} volvió a casa bajo las estrellas, pero el Jardín del Dragón siempre vivirá en su corazón. Y colorín colorado, este cuento mágico ha terminado.",
                "text_en": "{name} returned home under the stars, but the Dragon Garden will always live in their heart. And they lived happily ever after. The End.",
                "fixed_scene": "scene_19_going_home.png"
            }
        ]
    },
    "magic_chef_illustrated": {
        "title_es": "{name} El Chef Mágico",
        "title_en": "{name} The Magic Chef",
        "age_range": "3-5",
        "book_type": "illustrated",
        "price": 45,
        "page_count": 24,
        "use_fixed_scenes": True,
        "scenes_dir": "generated",
        "preview_prompt_override": "Full body portrait of a cheerful {gender_word} (4-5 years old) with {hair_desc}, {eye_desc} and {skin_desc}, {gender_features}, wearing an elegant white chef jacket with golden buttons and a cute white chef's hat that has cartoon eyes and a friendly smile on it. The child is standing in a magical pink kitchen with floating cupcakes, cookies and sparkles in the air. Next to the child is Sweetie - a complete full-size rainbow layered cake character (NOT a slice) with cute cartoon eyes, a sweet smile, small arms and tiny legs. The cake has colorful rainbow layers visible. Warm magical kitchen atmosphere with golden light, floating desserts and pastries. Children's storybook watercolor illustration style, soft luminous colors, dreamy magical atmosphere. NO text, NO watermark, NO signature, NO logo, clean illustration only",
        "content_pages": [
            {"text_es": "Había una vez, en una cocina olvidada en el ático de una casa antigua, un gorro de chef muy especial. Brillaba con luz dorada, esperando a alguien con un corazón lleno de creatividad.", "text_en": "Once upon a time, in a forgotten kitchen in the attic of an old house, there was a very special chef's hat. It shimmered with golden light, waiting for someone with a heart full of creativity."},
            {"text_es": "Cuando {name} se puso el gorro mágico, sintió un cosquilleo especial. \"¡Bienvenido al mundo de la cocina mágica!\", susurró una voz dulce desde el gorro.", "text_en": "When {name} put on the magic hat, they felt a special tingle. \"Welcome to the world of magical cooking!\" whispered a sweet voice from the hat."},
            {"text_es": "De pronto, la cocina comenzó a crecer y crecer. ¡Las cucharas eran tan altas como árboles! {name} se había convertido en un pequeño chef en una cocina gigante.", "text_en": "Suddenly, the kitchen began to grow and grow. The spoons were as tall as trees! {name} had become a tiny chef in a giant kitchen."},
            {"text_es": "\"¡Tu primera misión es hacer un pastel de arcoíris!\", dijo el gorro. {name} encontró ingredientes mágicos: harina de estrellas, azúcar de nubes y huevos de sol.", "text_en": "\"Your first mission is to make a rainbow cake!\" said the hat. {name} found magical ingredients: star flour, cloud sugar, and sun eggs."},
            {"text_es": "{name} mezcló los ingredientes con una cuchara mágica que bailaba sola. La masa brillaba con todos los colores del arcoíris mientras se mezclaba.", "text_en": "{name} mixed the ingredients with a magic spoon that danced by itself. The batter glowed with all the colors of the rainbow as it mixed."},
            {"text_es": "Cuando el pastel salió del horno, ¡cobró vida! \"¡Hola, chef {name}!\", dijo el pastelito saltando de alegría. \"¡Soy Dulcín, tu ayudante!\"", "text_en": "When the cake came out of the oven, it came alive! \"Hello, Chef {name}!\" said the little cake, jumping with joy. \"I'm Sweetie, your helper!\""},
            {"text_es": "Dulcín, el pastelito mágico, mostró a {name} el secreto de la cocina: \"Con amor y creatividad, cualquier receta puede ser extraordinaria.\"", "text_en": "Sweetie, the magical cake, showed {name} the secret of cooking: \"With love and creativity, any recipe can be extraordinary.\""},
            {"text_es": "Juntos prepararon galletas con forma de estrella que brillaban en la oscuridad. Al morderlas, ¡hacían música!", "text_en": "Together they made star-shaped cookies that glowed in the dark. When you bit them, they made music!"},
            {"text_es": "Después crearon un helado de nubes que nunca se derretía y cambiaba de sabor con cada lametón: fresa, chocolate, vainilla...", "text_en": "Then they created a cloud ice cream that never melted and changed flavor with each lick: strawberry, chocolate, vanilla..."},
            {"text_es": "\"¡Chef {name}, hay un concurso de cocina mágica hoy!\", anunció Dulcín emocionado. \"¡Los mejores chefs del mundo mágico competirán!\"", "text_en": "\"Chef {name}, there's a magical cooking contest today!\" announced Sweetie excitedly. \"The best chefs from the magical world will compete!\""},
            {"text_es": "El concurso era en un castillo hecho completamente de caramelo y chocolate. Las torres eran bastones de caramelo gigantes.", "text_en": "The contest was in a castle made entirely of candy and chocolate. The towers were giant candy canes."},
            {"text_es": "Había chefs de todas partes: elfos pasteleros, hadas cocineras y hasta un oso de gomita que hacía pasteles de miel.", "text_en": "There were chefs from everywhere: pastry elves, fairy cooks, and even a gummy bear that made honey cakes."},
            {"text_es": "\"El reto es crear el postre más delicioso del mundo\", anunció la juez, una amable abuelita hecha de mazapán con ojos de caramelo.", "text_en": "\"The challenge is to create the most delicious dessert in the world,\" announced the judge, a kind grandmother made of marzipan with candy eyes."},
            {"text_es": "{name} cerró los ojos y pensó en lo que más amaba: su familia, sus amigos, los momentos felices. \"¡Ya sé qué haré!\", exclamó.", "text_en": "{name} closed their eyes and thought about what they loved most: family, friends, happy moments. \"I know what I'll make!\" they exclaimed."},
            {"text_es": "Con ingredientes mágicos y todo su amor, {name} creó el \"Pastel de los Recuerdos Felices\": capas de alegría, relleno de abrazos y glaseado de sonrisas.", "text_en": "With magical ingredients and all their love, {name} created the \"Happy Memories Cake\": layers of joy, filling of hugs, and frosting of smiles."},
            {"text_es": "Cuando los jueces probaron el pastel de {name}, lágrimas de felicidad rodaron por sus mejillas. Cada bocado traía un recuerdo hermoso.", "text_en": "When the judges tasted {name}'s cake, tears of happiness rolled down their cheeks. Each bite brought back a beautiful memory."},
            {"text_es": "\"¡El ganador es Chef {name}!\", anunció la abuelita de mazapán. \"Has descubierto el ingrediente secreto: el amor.\"", "text_en": "\"The winner is Chef {name}!\" announced the marzipan grandmother. \"You discovered the secret ingredient: love.\""},
            {"text_es": "\"Nunca olvides\", susurró el gorro mágico, \"que la verdadera magia está en cocinar con el corazón y compartir con los demás.\"", "text_en": "\"Never forget,\" whispered the magic hat, \"that true magic is cooking with your heart and sharing with others.\""},
            {"text_es": "{name} regresó a casa con su gorro mágico y una receta especial en el corazón. Y colorín colorado, este cuento delicioso ha terminado.", "text_en": "{name} returned home with the magic hat and a special recipe in their heart. And they lived sweetly ever after. The End."}
        ]
    },
    "magic_inventor_illustrated": {
        "title_es": "{name} y el Taller de los Inventos Mágicos",
        "title_en": "{name} and the Magic Inventor Workshop",
        "age_range": "6-8",
        "book_type": "illustrated",
        "price": 45,
        "page_count": 24,
        "use_fixed_scenes": True,
        "scenes_dir": "generated",
        "preview_prompt_override": "Full body portrait of a cheerful {gender_word} (6-8 years old) with {hair_desc}, {eye_desc} and {skin_desc}, {gender_features}, wearing a brown leather inventor apron over a striped shirt with rolled-up sleeves, comfortable pants, sturdy boots, and small goggles pushed up on forehead. The child is standing in a magical inventor workshop with floating golden gears, crystal tubes with colorful glowing liquids, copper pipes, and warm golden light. Next to the child is BOLT - a small round copper-colored robot with a spherical body, two big glowing blue LED eyes, two short articulated metallic arms, two short stumpy metallic legs, a small antenna on top with a blinking light, rivets and gears visible, NO tail. Warm magical workshop atmosphere with copper and golden tones, sparkling metallic particles. Children's storybook watercolor illustration style, soft luminous colors, dreamy magical atmosphere. NO text, NO watermark, NO signature, NO logo, clean illustration only",
        "content_pages": [
            {"text_es": "En lo más alto de una vieja casona, {name} descubrió una puerta secreta detrás de una estantería polvorienta. Al abrirla, una luz dorada y chispas de colores salieron desde el interior.", "text_en": "At the very top of an old manor house, {name} discovered a secret door behind a dusty bookshelf. When they opened it, golden light and colorful sparks burst from inside."},
            {"text_es": "¡Era un taller mágico lleno de inventos asombrosos! Engranajes dorados flotaban por el aire, tubos de cristal brillaban con líquidos de colores y herramientas mágicas se movían solas.", "text_en": "It was a magical workshop full of amazing inventions! Golden gears floated in the air, crystal tubes glowed with colorful liquids, and magical tools moved on their own."},
            {"text_es": "De pronto, una pequeña esfera de cobre rodó hasta los pies de {name}. Se abrió y de ella surgió un simpático robot con ojos azules brillantes. \"¡Hola! Soy BOLT\", dijo con voz metálica y alegre.", "text_en": "Suddenly, a small copper sphere rolled to {name}'s feet. It opened up and out came a friendly little robot with bright blue eyes. \"Hello! I'm BOLT,\" it said with a cheerful metallic voice."},
            {"text_es": "BOLT le mostró a {name} el Mapa de los Inventos Perdidos, un pergamino brillante donde aparecían máquinas fantásticas esperando ser reconstruidas por un inventor valiente.", "text_en": "BOLT showed {name} the Map of Lost Inventions, a glowing scroll where fantastic machines appeared, waiting to be rebuilt by a brave inventor."},
            {"text_es": "\"¡Nuestro primer invento será una Bicicleta Voladora!\", exclamó BOLT. {name} encontró ruedas de cristal, pedales de arcoíris y un manillar que brillaba como una estrella.", "text_en": "\"Our first invention will be a Flying Bicycle!\" exclaimed BOLT. {name} found crystal wheels, rainbow pedals, and handlebars that glowed like a star."},
            {"text_es": "{name} y BOLT construyeron juntos la Bicicleta Voladora. Cada pieza encajaba con un destello de luz y el taller se llenó de música mágica.", "text_en": "{name} and BOLT built the Flying Bicycle together. Each piece clicked into place with a flash of light, and the workshop filled with magical music."},
            {"text_es": "¡La Bicicleta Voladora cobró vida! {name} pedaleó hacia el cielo del taller, que se abrió como un libro mágico revelando un cielo lleno de estrellas y nubes de algodón.", "text_en": "The Flying Bicycle came alive! {name} pedaled into the workshop sky, which opened like a magical book revealing a sky full of stars and cotton candy clouds."},
            {"text_es": "Volaron sobre un océano de nubes hasta llegar a la Isla de las Ideas, un lugar flotante donde las ideas se convertían en burbujas brillantes de todos los colores.", "text_en": "They flew over an ocean of clouds to reach the Island of Ideas, a floating place where ideas turned into brilliant bubbles of every color."},
            {"text_es": "En la Isla encontraron la Caja Musical Infinita, un invento que creaba melodías que podían hacer crecer flores y pintar arcoíris en el cielo.", "text_en": "On the Island they found the Infinite Music Box, an invention that created melodies that could grow flowers and paint rainbows in the sky."},
            {"text_es": "\"¡Necesitamos reparar el Telescopio de Arcoíris!\", dijo BOLT. Era un telescopio mágico que permitía ver los sueños de cualquier persona en cualquier lugar del mundo.", "text_en": "\"We need to fix the Rainbow Telescope!\" said BOLT. It was a magical telescope that let you see anyone's dreams anywhere in the world."},
            {"text_es": "{name} descubrió que la pieza que faltaba era un cristal con forma de corazón. Lo encontraron escondido dentro de un reloj antiguo que marcaba la hora de los sueños.", "text_en": "{name} discovered that the missing piece was a heart-shaped crystal. They found it hidden inside an ancient clock that marked the hour of dreams."},
            {"text_es": "Con el cristal corazón en su lugar, el Telescopio de Arcoíris mostró los sueños más hermosos: ciudades flotantes, jardines submarinos y montañas de caramelo.", "text_en": "With the heart crystal in place, the Rainbow Telescope showed the most beautiful dreams: floating cities, underwater gardens, and candy mountains."},
            {"text_es": "BOLT llevó a {name} al Jardín de los Engranajes, donde flores mecánicas de cobre y cristal abrían y cerraban sus pétalos con suaves chasquidos musicales.", "text_en": "BOLT led {name} to the Garden of Gears, where mechanical flowers made of copper and crystal opened and closed their petals with soft musical clicks."},
            {"text_es": "En el centro del Jardín había un árbol mecánico cuyas hojas eran pequeñas pantallas que mostraban los recuerdos más felices de quienes lo tocaban.", "text_en": "In the center of the Garden stood a mechanical tree whose leaves were tiny screens showing the happiest memories of whoever touched it."},
            {"text_es": "\"¡Es hora de tu propio invento!\", anunció BOLT. {name} imaginó algo increíble: una máquina que convertía los abrazos en estrellas brillantes.", "text_en": "\"It's time for your own invention!\" announced BOLT. {name} imagined something incredible: a machine that turned hugs into brilliant stars."},
            {"text_es": "Juntos construyeron la Máquina de Abrazos Estelares. Cuando {name} abrazó a BOLT para probarla, el taller se llenó de estrellas doradas que bailaban en el aire.", "text_en": "Together they built the Stellar Hug Machine. When {name} hugged BOLT to test it, the workshop filled with golden stars that danced in the air."},
            {"text_es": "Las estrellas de sus abrazos volaron por la ventana del taller e iluminaron el cielo nocturno, creando una nueva constelación con la forma de un niño y su robot.", "text_en": "The stars from their hugs flew out the workshop window and lit up the night sky, creating a new constellation shaped like a child and a robot."},
            {"text_es": "\"Siempre que mires las estrellas, recuerda que un inventor puede cambiar el mundo con imaginación y corazón\", dijo BOLT, con sus ojos azules brillando más que nunca.", "text_en": "\"Whenever you look at the stars, remember that an inventor can change the world with imagination and heart,\" said BOLT, his blue eyes glowing brighter than ever."},
            {"text_es": "{name} volvió a casa con el corazón lleno de ideas y la certeza de que la magia vive en cada invento creado con amor. Y colorín colorado, este cuento de inventores ha terminado.", "text_en": "{name} returned home with a heart full of ideas and the certainty that magic lives in every invention created with love. And they all lived happily ever after. The End."}
        ]
    },
    "furry_love_illustrated": {
        "title_es": "El día que {pet_name} conoció a {name}",
        "title_en": "The Day {pet_name} Met {name}",
        "age_range": "0-2",
        "book_type": "illustrated",
        "price": 65,
        "page_count": 24,
        "use_fixed_scenes": True,
        "scenes_dir": "generated",
        "is_furry_love": True,
        "text_layout": "split",
        "content_pages": [
            {
                "text_above_es": "Algo mágico estaba a punto de suceder. {pet_name} lo sentía en el aire.",
                "text_below_es": "La casa olía diferente: a pintura fresca, a ropa suavecita, a algo que {pet_name} no sabía nombrar pero que hacía que su cola se moviera despacito, como si guardara un secreto.",
                "text_above_en": "Something magical was about to happen. {pet_name} could feel it in the air.",
                "text_below_en": "The house smelled different: of fresh paint, soft fabrics, of something {pet_name} couldn't name but that made their tail wag slowly, as if keeping a secret."
            },
            {
                "text_above_es": "Y entonces, un día, la puerta se abrió. {pet_name} escuchó risas, pasos suaves y... un sonido nuevo. Pequeñito. Dulce.",
                "text_below_es": "Un suspiro diminuto que llenó toda la casa. Los ojos de {pet_name} se abrieron enormes: ¡habían traído a {name} a casa!",
                "text_above_en": "And then, one day, the door opened. {pet_name} heard laughter, soft footsteps and... a new sound. Tiny. Sweet.",
                "text_below_en": "A little sigh that filled the whole house. {pet_name}'s eyes went wide: they had brought {name} home!"
            },
            {
                "text_above_es": "{pet_name} se acercó despacito, con las patitas suaves sobre el suelo. Puso su nariz cerca de {name}, muy cerca, y olió.",
                "text_below_es": "Olía a leche, a talco, a algo que {pet_name} decidió en ese instante que iba a proteger para siempre.",
                "text_above_en": "{pet_name} approached slowly, soft paws on the floor. Nose came close to {name}, very close, and sniffed.",
                "text_below_en": "It smelled of milk, of powder, of something {pet_name} decided in that very instant to protect forever."
            },
            {
                "text_above_es": "Esa primera noche, {pet_name} se echó junto a la cuna de {name}. No se movió ni una vez.",
                "text_below_es": "Cada vez que {name} hacía un ruidito, {pet_name} levantaba una oreja. \"Aquí estoy\", decía su mirada. \"Aquí estaré siempre.\"",
                "text_above_en": "That first night, {pet_name} lay down beside {name}'s crib. Didn't move once.",
                "text_below_en": "Every time {name} made a little sound, {pet_name} raised one ear. \"I'm here,\" said those eyes. \"I'll always be here.\""
            },
            {
                "text_above_es": "Pasaron los días y una mañana, mientras {pet_name} observaba la cuna, sucedió algo increíble.",
                "text_below_es": "{name} abrió bien los ojos, miró directamente a {pet_name}... ¡y sonrió! La primera sonrisa de {name} fue para {pet_name}.",
                "text_above_en": "Days passed and one morning, while {pet_name} watched the crib, something incredible happened.",
                "text_below_en": "{name} opened their eyes wide, looked straight at {pet_name}... and smiled! {name}'s first smile was for {pet_name}."
            },
            {
                "text_above_es": "{pet_name} desapareció un momento y volvió con su juguete más preciado. Lo dejó suavemente junto a {name}.",
                "text_below_es": "\"Esto es lo que más quiero\", parecía decir {pet_name}. \"Y ahora es tuyo también, {name}.\"",
                "text_above_en": "{pet_name} disappeared for a moment and came back with their most treasured toy. Gently placed it next to {name}.",
                "text_below_en": "\"This is what I love most,\" {pet_name} seemed to say. \"And now it's yours too, {name}.\""
            },
            {
                "text_above_es": "Un día, las manitas curiosas de {name} descubrieron algo suave y tibio: ¡el pelaje de {pet_name}!",
                "text_below_es": "{name} agarró un mechón y no quiso soltar. {pet_name} se quedó quieto, feliz, con los ojos entrecerrados de puro gusto.",
                "text_above_en": "One day, {name}'s curious little hands discovered something soft and warm: {pet_name}'s fur!",
                "text_below_en": "{name} grabbed a tuft and wouldn't let go. {pet_name} stayed perfectly still, happy, eyes half-closed with pure contentment."
            },
            {
                "text_above_es": "¡La hora del baño! {name} chapoteaba y reía mientras el agua salpicaba por todos lados.",
                "text_below_es": "{pet_name} observaba desde la puerta con la cabeza ladeada. Una ola de agua le mojó la nariz a {pet_name}. ¡Y las risas de {name} fueron aún más grandes!",
                "text_above_en": "Bath time! {name} splashed and laughed as water went everywhere.",
                "text_below_en": "{pet_name} watched from the doorway with a tilted head. A wave of water splashed {pet_name}'s nose. And {name}'s laughter grew even bigger!"
            },
            {
                "text_above_es": "Durante el tiempo boca abajo, {name} levantó la cabecita por primera vez. ¿Y qué vio?",
                "text_below_es": "A {pet_name}, echado en el suelo, nariz con nariz. {name} y {pet_name} se miraron durante un largo momento mágico, como si se contaran secretos sin palabras.",
                "text_above_en": "During tummy time, {name} lifted their little head for the first time. And what did they see?",
                "text_below_en": "{pet_name}, lying on the floor, nose to nose. {name} and {pet_name} looked at each other for a long magical moment, as if sharing secrets without words."
            },
            {
                "text_above_es": "¡{name} se movió! Primero fue un balanceo torpe, luego las rodillitas empezaron a funcionar.",
                "text_below_es": "¿Hacia dónde fue la primera aventura de {name}? Directo hacia {pet_name}, por supuesto. Siempre hacia {pet_name}.",
                "text_above_en": "{name} moved! First a wobbly rocking, then the little knees started working.",
                "text_below_en": "Where did {name}'s first adventure go? Straight toward {pet_name}, of course. Always toward {pet_name}."
            },
            {
                "text_above_es": "En el jardín, {name} tocó el pasto por primera vez. Era cosquilloso, verde y olía a aventura.",
                "text_below_es": "{pet_name} corrió en círculos de alegría, trayendo palitos y hojas como regalos. {name} reía y reía y reía.",
                "text_above_en": "In the garden, {name} touched grass for the first time. It was tickly, green, and smelled like adventure.",
                "text_below_en": "{pet_name} ran in happy circles, bringing sticks and leaves as gifts. {name} laughed and laughed and laughed."
            },
            {
                "text_above_es": "Los días de lluvia eran especiales. {name} y {pet_name} se sentaban juntos frente a la ventana, viendo las gotas resbalarse por el cristal.",
                "text_below_es": "Afuera todo era gris, pero adentro, juntos, todo era cálido.",
                "text_above_en": "Rainy days were special. {name} and {pet_name} sat together by the window, watching drops slide down the glass.",
                "text_below_en": "Outside everything was gray, but inside, together, everything was warm."
            },
            {
                "text_above_es": "La hora de la comida era la favorita de {pet_name}. {name} comía con las manos, con la cara, con toda el alma.",
                "text_below_es": "Y lo que caía al suelo... bueno, {pet_name} siempre estaba listo para \"ayudar a limpiar\". ¡{name} y {pet_name}, el mejor equipo del mundo!",
                "text_above_en": "Mealtime was {pet_name}'s favorite. {name} ate with hands, with face, with whole heart and soul.",
                "text_below_en": "And what fell to the floor... well, {pet_name} was always ready to \"help clean up.\" {name} and {pet_name}, the best team in the world!"
            },
            {
                "text_above_es": "Por las noches, cuando alguien leía un cuento, {name} se recostaba contra {pet_name}.",
                "text_below_es": "{name} miraba las páginas, {pet_name} miraba a {name}. Y los dos se iban quedando dormidos juntos, en un nido de amor.",
                "text_above_en": "At night, when someone read a story, {name} leaned against {pet_name}.",
                "text_below_en": "{name} looked at the pages, {pet_name} looked at {name}. And they both drifted off to sleep together, in a nest of love."
            },
            {
                "text_above_es": "Una noche, un trueno enorme sacudió la casa. {name} se asustó y empezó a llorar.",
                "text_below_es": "Pero {pet_name} se acurrucó más cerca, pegando su cuerpo tibio contra {name}. \"No tengas miedo\", decía el calor de {pet_name}. Y {name} se calmó.",
                "text_above_en": "One night, a huge thunderclap shook the house. {name} got scared and started crying.",
                "text_below_en": "But {pet_name} snuggled closer, pressing their warm body against {name}. \"Don't be afraid,\" said {pet_name}'s warmth. And {name} calmed down."
            },
            {
                "text_above_es": "Y entonces llegó el día más esperado. {name} se soltó de la mesa, abrió los brazos... ¡y caminó!",
                "text_below_es": "Uno, dos, tres pasitos tambaleantes. ¿Hacia dónde? Hacia {pet_name}. Los primeros pasos de {name} fueron para llegar a {pet_name}.",
                "text_above_en": "And then came the most awaited day. {name} let go of the table, opened their arms... and walked!",
                "text_below_en": "One, two, three wobbly steps. Where to? Toward {pet_name}. {name}'s first steps were to reach {pet_name}."
            },
            {
                "text_above_es": "\"¡Busca, {pet_name}!\" {name} lanzó la pelota con toda su fuerza. La pelota rodó apenas un metro.",
                "text_below_es": "Pero {pet_name} salió corriendo como si fuera el lanzamiento más épico del mundo, la trajo de vuelta y la dejó a los pies de {name}. Una y otra y otra vez.",
                "text_above_en": "\"Fetch, {pet_name}!\" {name} threw the ball with all their might. The ball rolled barely three feet.",
                "text_below_en": "But {pet_name} took off running as if it were the most epic throw in the world, brought it back and placed it at {name}'s feet. Again and again and again."
            },
            {
                "text_above_es": "Después de tanto jugar, llegaba el mejor momento del día: la siesta juntos.",
                "text_below_es": "{name} se acurrucaba contra {pet_name}, una mano sobre su lomo cálido. Y los dos soñaban el mismo sueño: un sueño donde {name} y {pet_name} estaban siempre juntos.",
                "text_above_en": "After all that playing came the best moment of the day: nap time together.",
                "text_below_en": "{name} curled up against {pet_name}, one hand on that warm back. And they both dreamed the same dream: a dream where {name} and {pet_name} were always together."
            },
            {
                "text_above_es": "Hoy {name} y {pet_name} caminan juntos por el parque. {name} ya no es tan bebé: corre, salta, señala las nubes y le cuenta secretos a {pet_name} al oído.",
                "text_below_es": "Y {pet_name} escucha cada palabra como si fuera la más importante del universo. Porque la historia de {name} y {pet_name} no tiene final. Esta historia apenas comienza.",
                "text_above_en": "Today {name} and {pet_name} walk together through the park. {name} isn't such a baby anymore: running, jumping, pointing at clouds and whispering secrets in {pet_name}'s ear.",
                "text_below_en": "And {pet_name} listens to every word as if it were the most important in the universe. Because the story of {name} and {pet_name} has no ending. This story is just beginning."
            }
        ],
    },
    "furry_love_adventure_illustrated": {
        "title_es": "Las aventuras de {pet_name} y {name}",
        "title_en": "The Adventures of {pet_name} and {name}",
        "age_range": "3-8",
        "book_type": "illustrated",
        "price": 65,
        "page_count": 24,
        "use_fixed_scenes": True,
        "scenes_dir": "generated",
        "is_furry_love": True,
        "text_layout": "split",
        "content_pages": [
            {
                "text_above_es": "Una mañana de sábado, {name} abrió los ojos y sintió algo cálido y suave acurrucado a sus pies.",
                "text_below_es": "Era {pet_name}, que ya llevaba un rato despierto, esperando con paciencia a que su mejor amigo se levantara.",
                "text_above_en": "One Saturday morning, {name} opened their eyes and felt something warm and soft curled up at their feet.",
                "text_below_en": "It was {pet_name}, who had been awake for a while, patiently waiting for their best friend to wake up."
            },
            {
                "text_above_es": "\"¡Hoy vamos a tener una aventura!\", dijo {name} saltando de la cama. Después del desayuno, tomó la correa y {pet_name} ya estaba esperando junto a la puerta, dando vueltas de emoción.",
                "text_below_es": "El parque los llamaba.",
                "text_above_en": "\"Today we're going on an adventure!\" said {name}, jumping out of bed. After breakfast, they grabbed the leash and {pet_name} was already waiting by the door, spinning with excitement.",
                "text_below_en": "The park was calling."
            },
            {
                "text_above_es": "{pet_name} tiraba con fuerza, olisqueando cada rincón del camino. De pronto, se detuvo en seco. Su nariz apuntaba hacia el suelo, donde unas huellas extrañas marcaban el camino de tierra.",
                "text_below_es": "Eran grandes, redondas y brillaban con un polvo dorado.",
                "text_above_en": "{pet_name} pulled hard, sniffing every corner of the path. Suddenly, they stopped dead. Their nose pointed at the ground, where strange tracks marked the dirt path.",
                "text_below_en": "They were big, round, and sparkled with golden dust."
            },
            {
                "text_above_es": "\"¿Qué será eso?\", susurró {name}, agachándose para ver más de cerca. {pet_name} olfateó las huellas con cuidado y luego miró a {name}, como diciendo: \"¿Las seguimos?\"",
                "text_below_es": "Las huellas doradas los llevaron hasta un arbusto enorme que temblaba.",
                "text_above_en": "\"What could that be?\" whispered {name}, bending down for a closer look. {pet_name} sniffed the tracks carefully and then looked at {name}, as if saying: \"Should we follow them?\"",
                "text_below_en": "The golden tracks led them to a huge bush that was trembling."
            },
            {
                "text_above_es": "Los dos amigos se miraron con valentía. {name} apartó las ramas con cuidado...",
                "text_below_es": "¡Era una mariposa enorme, del tamaño de un plato! Sus alas brillaban con todos los colores del arcoíris y dejaba un rastro de polvo dorado.",
                "text_above_en": "The two friends looked at each other bravely. {name} carefully parted the branches...",
                "text_below_en": "It was an enormous butterfly, the size of a plate! Its wings shimmered with every color of the rainbow and left a trail of golden dust."
            },
            {
                "text_above_es": "{pet_name} saltó intentando atraparla, girando en el aire como un acróbata torpe. {name} se cayó al suelo de la risa.",
                "text_below_es": "La mariposa los guió hasta un enorme charco que brillaba bajo el sol. ¡{pet_name} saltó directo al agua con un tremendo SPLASH!",
                "text_above_en": "{pet_name} leaped trying to catch it, spinning in the air like a clumsy acrobat. {name} fell to the ground laughing.",
                "text_below_en": "The butterfly guided them to a huge puddle glistening under the sun. {pet_name} jumped straight into the water with a tremendous SPLASH!"
            },
            {
                "text_above_es": "El agua salpicó por todos lados, empapando a {name} de pies a cabeza. Al otro lado del parque, una vieja cerca de madera escondía algo que {name} nunca había visto.",
                "text_below_es": "La mariposa dorada pasó volando por encima, invitándolos a seguir.",
                "text_above_en": "Water splashed everywhere, soaking {name} from head to toe. On the other side of the park, an old wooden fence was hiding something {name} had never seen.",
                "text_below_en": "The golden butterfly flew over it, inviting them to follow."
            },
            {
                "text_above_es": "{name} miró a {pet_name}. {pet_name} miró a {name}. Sin decir una palabra, los dos se agacharon y pasaron por debajo de la cerca.",
                "text_below_es": "Lo que encontraron al otro lado los dejó con la boca abierta: un jardín secreto con flores enormes de todos los colores.",
                "text_above_en": "{name} looked at {pet_name}. {pet_name} looked at {name}. Without a word, they both ducked under the fence.",
                "text_below_en": "What they found on the other side left them speechless: a secret garden with enormous flowers of every color."
            },
            {
                "text_above_es": "{pet_name} metió la nariz en una flor morada y estornudó, lanzando una nube de polen brillante. {name} recogió un pétalo que cabía en las dos manos.",
                "text_below_es": "Debajo del árbol más grande del jardín, las raíces formaban un escondite. Y ahí asomaba un viejo cofre.",
                "text_above_en": "{pet_name} stuck their nose in a purple flower and sneezed, launching a cloud of shimmering pollen. {name} picked up a petal that fit in both hands.",
                "text_below_en": "Under the biggest tree in the garden, the roots formed a hideaway. And there, peeking out, was an old chest."
            },
            {
                "text_above_es": "Con manos temblorosas de emoción, {name} abrió la tapa oxidada. Dentro había un mapa viejo, dibujado a mano con tinta azul y roja. Una gran X marcaba un punto al final de un sendero.",
                "text_below_es": "\"¡Es un mapa del tesoro, {pet_name}!\", exclamó {name} con los ojos brillantes.",
                "text_above_en": "With hands trembling with excitement, {name} opened the rusty lid. Inside was an old map, hand-drawn with blue and red ink. A big X marked a spot at the end of a trail.",
                "text_below_en": "\"It's a treasure map, {pet_name}!\" exclaimed {name} with shining eyes."
            },
            {
                "text_above_es": "{pet_name} olió el mapa y ladró una vez, como diciendo: \"¿A qué esperamos?\" El mapa los llevó por un sendero estrecho entre los árboles, donde las ramas formaban un túnel verde sobre sus cabezas.",
                "text_below_es": "La mariposa dorada volaba adelante, mostrándoles el camino.",
                "text_above_en": "{pet_name} sniffed the map and barked once, as if saying: \"What are we waiting for?\" The map led them down a narrow path between the trees, where branches formed a green tunnel overhead.",
                "text_below_en": "The golden butterfly flew ahead, showing them the way."
            },
            {
                "text_above_es": "{name} iba adelante con el mapa y {pet_name} caminaba pegado a sus piernas. El sendero terminó frente a un pequeño puente de madera que cruzaba un arroyo de agua cristalina.",
                "text_below_es": "El puente crujía con el viento. {pet_name} puso una pata y retrocedió asustado.",
                "text_above_en": "{name} walked ahead with the map and {pet_name} stayed close to their legs. The trail ended at a small wooden bridge crossing a crystal-clear stream.",
                "text_below_en": "The bridge creaked in the wind. {pet_name} put one paw on it and backed away, scared."
            },
            {
                "text_above_es": "{name} acarició la cabeza de {pet_name} con suavidad. \"No tengas miedo, yo estoy contigo\", le susurró.",
                "text_below_es": "Entonces tomó a {pet_name} en brazos con cuidado y empezó a cruzar el puente paso a paso. {pet_name} se acurrucó contra su pecho, cerrando los ojos con confianza.",
                "text_above_en": "{name} gently stroked {pet_name}'s head. \"Don't be afraid, I'm with you,\" they whispered.",
                "text_below_en": "Then {name} carefully picked up {pet_name} and started crossing the bridge step by step. {pet_name} nestled against their chest, closing their eyes with trust."
            },
            {
                "text_above_es": "Cuando llegaron al otro lado, {pet_name} lamió la cara de {name} como diciendo \"gracias\". La X del mapa señalaba una pequeña cueva en la ladera de una colina.",
                "text_below_es": "La entrada estaba decorada con piedras que brillaban como diamantes.",
                "text_above_en": "When they reached the other side, {pet_name} licked {name}'s face as if saying \"thank you.\" The X on the map pointed to a small cave in a hillside.",
                "text_below_en": "The entrance was decorated with stones that sparkled like diamonds."
            },
            {
                "text_above_es": "{pet_name} entró primero, valiente como nunca. Dentro, las paredes centelleaban con cristales de todos los colores.",
                "text_below_es": "En el fondo, grabado en una piedra lisa y brillante, había un mensaje: \"Para el explorador más valiente y su mejor compañero.\"",
                "text_above_en": "{pet_name} went in first, braver than ever. Inside, the walls sparkled with crystals of every color.",
                "text_below_en": "At the back, carved into a smooth shining stone, was a message: \"For the bravest explorer and their best companion.\""
            },
            {
                "text_above_es": "{name} sonrió y abrazó a {pet_name}. \"Eso somos nosotros\", dijo con orgullo. Detrás de la piedra, escondida en un hueco, había una caja dorada.",
                "text_below_es": "Dentro encontró un medallón con la forma de una estrella y una bolsita de galletas especiales para {pet_name}.",
                "text_above_en": "{name} smiled and hugged {pet_name}. \"That's us,\" they said proudly. Behind the stone, hidden in a hollow, was a golden box.",
                "text_below_en": "Inside was a star-shaped medallion and a little bag of special treats for {pet_name}."
            },
            {
                "text_above_es": "{name} se puso el medallón al cuello. En el medallón estaban grabadas dos palabras: \"Mejores Amigos\".",
                "text_below_es": "El sol empezaba a esconderse cuando {name} y {pet_name} tomaron el camino de vuelta a casa. El cielo se pintó de naranja, rosa y morado.",
                "text_above_en": "{name} put the medallion around their neck. On the medallion were carved two words: \"Best Friends.\"",
                "text_below_en": "The sun was starting to set when {name} and {pet_name} took the path back home. The sky turned orange, pink, and purple."
            },
            {
                "text_above_es": "Cuando abrieron la puerta de casa, mamá se quedó mirándolos con los ojos muy abiertos. {name} estaba cubierto de barro, hojas y polvo dorado.",
                "text_below_es": "{pet_name} tenía ramitas en el pelo y las patas llenas de tierra.",
                "text_above_en": "When they opened the front door, mom stared at them with wide eyes. {name} was covered in mud, leaves, and golden dust.",
                "text_below_en": "{pet_name} had twigs in their fur and paws full of dirt."
            },
            {
                "text_above_es": "\"¡Pero qué les pasó!\", exclamó mamá. \"Solo fuimos a dar un paseo al parque\", dijo {name} con una sonrisa pícara. Después de un buen baño, {name} se acurrucó en el sofá con {pet_name} a su lado.",
                "text_below_es": "\"Mañana buscaremos otra aventura\", susurró {name} con los ojos cerrándose de sueño. Y así, los dos mejores amigos se quedaron dormidos, soñando con su próxima gran aventura.",
                "text_above_en": "\"What happened to you two!\" exclaimed mom. \"We just went for a walk in the park,\" said {name} with a mischievous smile. After a good bath, {name} curled up on the couch with {pet_name} beside them.",
                "text_below_en": "\"Tomorrow we'll find another adventure,\" whispered {name} as their eyes closed with sleep. And so, the two best friends fell asleep, dreaming of their next great adventure."
            }
        ],
    },
    "furry_love_teen_illustrated": {
        "title_es": "{name} y su compañero fiel {pet_name}",
        "title_en": "{name} and Their Faithful Companion {pet_name}",
        "age_range": "10-19",
        "book_type": "illustrated",
        "price": 65,
        "page_count": 24,
        "use_fixed_scenes": True,
        "scenes_dir": "generated",
        "is_furry_love": True,
        "text_layout": "split",
        "content_pages": [
            {
                "text_above_es": "Hubo un tiempo en que {name} y {pet_name} eran inseparables. Juntos corrían por el parque, se acurrucaban en el sofá y compartían cada momento del día.",
                "text_below_es": "{pet_name} era el mejor amigo de {name}... pero eso fue hace tiempo.",
                "text_above_en": "There was a time when {name} and {pet_name} were inseparable. They ran together in the park, cuddled on the couch, and shared every moment of the day.",
                "text_below_en": "{pet_name} was {name}'s best friend... but that was a while ago."
            },
            {
                "text_above_es": "Pero {name} ya no era un niño pequeño. Ahora tenía su celular, sus videojuegos y sus amigos del colegio.",
                "text_below_es": "{pet_name} se acercaba moviendo la cola, pero {name} apenas levantaba la vista de la pantalla. \"Ahora no, {pet_name}\", decía sin mirar.",
                "text_above_en": "But {name} wasn't a little kid anymore. Now they had their phone, video games, and school friends.",
                "text_below_en": "{pet_name} would come over wagging their tail, but {name} barely looked up from the screen. \"Not now, {pet_name},\" they'd say without looking."
            },
            {
                "text_above_es": "{pet_name} no se rendía fácilmente. Un día, mientras {name} escribía un mensaje importante, {pet_name} se acercó sigilosamente y...",
                "text_below_es": "¡ZAS! Le robó el celular de las manos con la boca y salió corriendo a toda velocidad por el pasillo.",
                "text_above_en": "{pet_name} didn't give up easily. One day, while {name} was typing an important message, {pet_name} crept up silently and...",
                "text_below_en": "SNAP! Snatched the phone right out of their hands and took off running down the hallway at full speed."
            },
            {
                "text_above_es": "\"¡{pet_name}, devuélveme el celular!\" gritó {name} persiguiéndolo por toda la casa. {pet_name} esquivaba muebles como un profesional, saltaba sobre el sofá y se metía debajo de la mesa.",
                "text_below_es": "Cuando por fin lo atrapó, el celular estaba lleno de babas. {name} no pudo evitar reírse.",
                "text_above_en": "\"Give me back my phone, {pet_name}!\" yelled {name}, chasing them through the whole house. {pet_name} dodged furniture like a pro, jumped over the couch, and dove under the table.",
                "text_below_en": "When {name} finally caught them, the phone was covered in drool. {name} couldn't help but laugh."
            },
            {
                "text_above_es": "Al día siguiente, {name} estaba haciendo tarea en la computadora. {pet_name} apareció de la nada y se subió directamente encima del teclado.",
                "text_below_es": "La pantalla se llenó de letras sin sentido: \"asdfjklñ;asdfgh\". {pet_name} se quedó ahí echado, mirando a {name} como si fuera el lugar más cómodo del mundo.",
                "text_above_en": "The next day, {name} was doing homework on the computer. {pet_name} appeared out of nowhere and climbed right onto the keyboard.",
                "text_below_en": "The screen filled with gibberish: \"asdfjklñ;asdfgh\". {pet_name} just lay there, looking at {name} as if it were the most comfortable spot in the world."
            },
            {
                "text_above_es": "{name} suspiró y movió a {pet_name} con cuidado. \"Eres imposible\", le dijo, pero le dio una caricia rápida en la cabeza antes de volver a la tarea.",
                "text_below_es": "{pet_name} meneó la cola. Esa caricia era un pequeño triunfo.",
                "text_above_en": "{name} sighed and gently moved {pet_name} aside. \"You're impossible,\" they said, but gave a quick pat on the head before going back to homework.",
                "text_below_en": "{pet_name} wagged their tail. That little pat was a small victory."
            },
            {
                "text_above_es": "Pero la Operación Atención no había terminado. A la mañana siguiente, {name} buscaba sus calcetines por toda la habitación. \"¡Juro que los dejé aquí!\"",
                "text_below_es": "Cuando miró debajo de la cama, encontró un tesoro escondido: tres pares de calcetines, un guante, y la gorra favorita de {name}. Todo en la cama de {pet_name}.",
                "text_above_en": "But Operation Attention wasn't over. The next morning, {name} searched the whole room for their socks. \"I swear I left them here!\"",
                "text_below_en": "When they looked under the bed, they found a hidden treasure: three pairs of socks, a glove, and {name}'s favorite cap. All in {pet_name}'s bed."
            },
            {
                "text_above_es": "\"¡{pet_name}!\" exclamó {name}, pero {pet_name} lo miraba con cara de ángel. Esos ojos grandes e inocentes eran su mejor arma.",
                "text_below_es": "{name} negó con la cabeza, pero una sonrisa se le escapó. Recogió sus cosas y le rascó las orejas a {pet_name}. \"Eres un pequeño ladrón.\"",
                "text_above_en": "\"Oh, {pet_name}!\" exclaimed {name}, but {pet_name} looked at them with an angel face. Those big innocent eyes were their best weapon.",
                "text_below_en": "{name} shook their head, but a smile escaped. They gathered their things and scratched {pet_name}'s ears. \"You're a little thief.\""
            },
            {
                "text_above_es": "Pasaron los días y {name} volvió a su rutina: colegio, celular, videojuegos, repetir.",
                "text_below_es": "{pet_name} empezó a pasar más tiempo solo, echado junto a la puerta del cuarto de {name}, esperando. A veces se quedaba dormido ahí, con la nariz pegada a la rendija de la puerta.",
                "text_above_en": "Days passed and {name} went back to their routine: school, phone, video games, repeat.",
                "text_below_en": "{pet_name} started spending more time alone, lying by {name}'s bedroom door, waiting. Sometimes they fell asleep there, nose pressed against the gap under the door."
            },
            {
                "text_above_es": "Una tarde, {name} notó que algo era diferente. {pet_name} no vino a saludarlo cuando llegó del colegio. No le robó nada. No se subió a ningún mueble.",
                "text_below_es": "{name} lo encontró acurrucado en su camita, con los ojos tristes y la nariz caliente. {pet_name} no se sentía bien.",
                "text_above_en": "One afternoon, {name} noticed something was different. {pet_name} didn't come to greet them when they got home from school. Didn't steal anything. Didn't climb on any furniture.",
                "text_below_en": "{name} found them curled up in their little bed, with sad eyes and a warm nose. {pet_name} wasn't feeling well."
            },
            {
                "text_above_es": "El corazón de {name} se encogió. Tomó a {pet_name} en brazos con mucho cuidado y lo llevó al veterinario.",
                "text_below_es": "En la sala de espera, {name} no soltó a {pet_name} ni un segundo. El celular se quedó olvidado en el fondo de la mochila.",
                "text_above_en": "{name}'s heart sank. They carefully picked up {pet_name} and took them to the vet.",
                "text_below_en": "In the waiting room, {name} didn't let go of {pet_name} for a single second. The phone stayed forgotten at the bottom of the backpack."
            },
            {
                "text_above_es": "\"Solo necesita descanso y mucho cariño\", dijo la veterinaria con una sonrisa. {name} soltó un enorme suspiro de alivio.",
                "text_below_es": "Abrazó a {pet_name} con fuerza y le susurró: \"Te prometo que todo va a estar bien.\" Y por primera vez en mucho tiempo, lo dijo de verdad.",
                "text_above_en": "\"Just needs rest and lots of love,\" said the vet with a smile. {name} let out a huge sigh of relief.",
                "text_below_en": "They hugged {pet_name} tightly and whispered: \"I promise everything will be okay.\" And for the first time in a long while, they truly meant it."
            },
            {
                "text_above_es": "De vuelta en casa, {name} preparó el lugar más cómodo del mundo para {pet_name}: almohadas, mantas suaves y su camiseta favorita para que tuviera su olor cerca.",
                "text_below_es": "Se sentó a su lado y le acarició la cabeza durante horas, sin mirar el celular ni una sola vez.",
                "text_above_en": "Back home, {name} set up the coziest spot in the world for {pet_name}: pillows, soft blankets, and their favorite t-shirt so {pet_name} could have their scent nearby.",
                "text_below_en": "They sat beside them and stroked their head for hours, without looking at the phone even once."
            },
            {
                "text_above_es": "Esa noche, {name} no pudo dormir. Se quedó pensando en todos los momentos en que {pet_name} había intentado llamar su atención: el celular robado, el teclado invadido, los calcetines escondidos.",
                "text_below_es": "No eran travesuras. Eran cartas de amor.",
                "text_above_en": "That night, {name} couldn't sleep. They lay thinking about all the times {pet_name} had tried to get their attention: the stolen phone, the invaded keyboard, the hidden socks.",
                "text_below_en": "They weren't pranks. They were love letters."
            },
            {
                "text_above_es": "A la mañana siguiente, {name} hizo algo que no hacía en meses: se despertó temprano, guardó el celular en un cajón y dijo: \"{pet_name}, hoy es TU día.\"",
                "text_below_es": "{pet_name} levantó las orejas, ladeó la cabeza y meneó la cola como un helicóptero. ¿Había escuchado bien?",
                "text_above_en": "The next morning, {name} did something they hadn't done in months: woke up early, put the phone in a drawer, and said: \"{pet_name}, today is YOUR day.\"",
                "text_below_en": "{pet_name} perked up their ears, tilted their head, and wagged their tail like a helicopter. Had they heard right?"
            },
            {
                "text_above_es": "Salieron juntos al parque, como en los viejos tiempos. {name} lanzaba la pelota y {pet_name} corría como si volara.",
                "text_below_es": "Se revolcaron en el pasto, se mojaron en la fuente y se rieron tanto que les dolía la panza. La gente los miraba sonriendo.",
                "text_above_en": "They went to the park together, just like the old days. {name} threw the ball and {pet_name} ran like they were flying.",
                "text_below_en": "They rolled in the grass, got soaked at the fountain, and laughed so hard their bellies hurt. People watched them smiling."
            },
            {
                "text_above_es": "De vuelta en casa, {name} se sentó en el suelo con {pet_name} y sacó una caja de fotos viejas. \"Mira, aquí eras un cachorro y yo era un enano\", se rio.",
                "text_below_es": "{pet_name} olfateó las fotos y le lamió la cara, como diciendo: \"Yo siempre te he querido igual.\"",
                "text_above_en": "Back home, {name} sat on the floor with {pet_name} and pulled out a box of old photos. \"Look, you were a puppy here and I was tiny,\" they laughed.",
                "text_below_en": "{pet_name} sniffed the photos and licked their face, as if saying: \"I've always loved you the same.\""
            },
            {
                "text_above_es": "{name} tomó el celular, pero esta vez para algo diferente: le sacó una foto a {pet_name} con una sonrisa enorme. \"Esta va directo a mi fondo de pantalla\", dijo.",
                "text_below_es": "Y escribió una nueva regla en un papel que pegó en la pared: \"Regla #1: Todos los días, tiempo con {pet_name}.\"",
                "text_above_en": "{name} picked up the phone, but this time for something different: they took a photo of {pet_name} with a huge smile. \"This is going straight to my wallpaper,\" they said.",
                "text_below_en": "And they wrote a new rule on paper and stuck it on the wall: \"Rule #1: Every day, time with {pet_name}.\""
            },
            {
                "text_above_es": "Esa noche, {name} se acostó con {pet_name} acurrucado a sus pies, exactamente como cuando era pequeño. Pero ahora era diferente. Ahora {name} sabía algo que antes no entendía:",
                "text_below_es": "que el amor de una mascota no pide nada a cambio, solo pide estar cerca. Y {name} prometió no volver a olvidarlo jamás.",
                "text_above_en": "That night, {name} went to bed with {pet_name} curled up at their feet, just like when they were little. But now it was different. Now {name} understood something they hadn't before:",
                "text_below_en": "that a pet's love asks for nothing in return, it only asks to be close. And {name} promised never to forget that again."
            }
        ],
    },
    "furry_love_adult_illustrated": {
        "title_es": "La Gran Aventura de {name} y {pet_name}",
        "title_en": "The Great Adventure of {name} and {pet_name}",
        "age_range": "18-75",
        "book_type": "illustrated",
        "price": 65,
        "page_count": 24,
        "use_fixed_scenes": True,
        "scenes_dir": "generated",
        "is_furry_love": True,
        "text_layout": "split",
        "content_pages": [
            {
                "text_above_es": "{name} abrió el maletero del carro y empezó a cargar la mochila, la tienda de campaña y las botas de montaña.",
                "text_below_es": "{pet_name} observaba cada movimiento con las orejas levantadas, moviendo la cola sin parar.",
                "text_above_en": "{name} opened the trunk and started loading the backpack, the tent, and the hiking boots.",
                "text_below_en": "{pet_name} watched every move with perked ears, tail wagging nonstop."
            },
            {
                "text_above_es": "\"¡Vamos, {pet_name}!\" dijo {name} abriendo la puerta trasera. {pet_name} saltó al asiento de un brinco y se asomó por la ventanilla.",
                "text_below_es": "El viento le alborotaba las orejas mientras el paisaje cambiaba de ciudad a bosque.",
                "text_above_en": "\"Let's go, {pet_name}!\" said {name}, opening the back door. {pet_name} jumped onto the seat in one leap and stuck their head out the window.",
                "text_below_en": "The wind ruffled their ears as the scenery changed from city to forest."
            },
            {
                "text_above_es": "{name} estacionó el carro al inicio del sendero. El aire olía a pinos y tierra húmeda.",
                "text_below_es": "{pet_name} bajó de un salto y empezó a olfatear todo a su alrededor, la cola moviéndose como un helicóptero.",
                "text_above_en": "{name} parked the car at the trailhead. The air smelled of pine and damp earth.",
                "text_below_en": "{pet_name} jumped out and started sniffing everything around, tail spinning like a helicopter."
            },
            {
                "text_above_es": "El sendero subía entre árboles enormes que dejaban pasar rayos de sol como linternas doradas. {name} respiraba profundo, sintiendo cómo el estrés de la ciudad se quedaba atrás.",
                "text_below_es": "{pet_name} trotaba a su lado, feliz de estar en territorio nuevo.",
                "text_above_en": "The trail climbed between enormous trees that let sunlight through like golden lanterns. {name} breathed deeply, feeling the city stress melt away.",
                "text_below_en": "{pet_name} trotted alongside, happy to be in new territory."
            },
            {
                "text_above_es": "{name} se detuvo al ver marcas en el suelo. \"Mira, {pet_name}, huellas de venado.\"",
                "text_below_es": "{pet_name} olfateó las huellas con concentración profesional, como si estuviera resolviendo un caso de detectives.",
                "text_above_en": "{name} stopped when they noticed marks on the ground. \"Look, {pet_name}, deer tracks.\"",
                "text_below_en": "{pet_name} sniffed the tracks with professional concentration, as if solving a detective case."
            },
            {
                "text_above_es": "De pronto, una ardilla apareció en una rama baja. {pet_name} se quedó paralizado, con los ojos enormes y las orejas en punta.",
                "text_below_es": "La ardilla lo miró sin miedo, como diciendo: \"Este es MI bosque.\" {name} contuvo la risa.",
                "text_above_en": "Suddenly, a squirrel appeared on a low branch. {pet_name} froze, eyes wide and ears pointed.",
                "text_below_en": "The squirrel stared back fearlessly as if saying: \"This is MY forest.\" {name} held back a laugh."
            },
            {
                "text_above_es": "La ardilla lanzó una bellota que rebotó en la cabeza de {pet_name}. \"¡Plop!\" {pet_name} dio un salto hacia atrás de la sorpresa.",
                "text_below_es": "{name} soltó una carcajada tan fuerte que los pájaros volaron de los árboles.",
                "text_above_en": "The squirrel dropped an acorn that bounced off {pet_name}'s head. \"Plop!\" {pet_name} jumped back in surprise.",
                "text_below_en": "{name} laughed so hard that birds flew from the trees."
            },
            {
                "text_above_es": "El sendero los llevó a un arroyo de aguas cristalinas que saltaba entre piedras. {name} cruzó con cuidado saltando de roca en roca.",
                "text_below_es": "{pet_name} lo observó un momento, calculando, y luego cruzó chapoteando directo por el agua.",
                "text_above_en": "The trail led them to a crystal-clear stream jumping over rocks. {name} crossed carefully, hopping from rock to rock.",
                "text_below_en": "{pet_name} watched for a moment, calculating, then crossed by splashing straight through the water."
            },
            {
                "text_above_es": "{pet_name} salió del arroyo y se sacudió con toda la energía del mundo. El agua voló por todos lados y {name} recibió una ducha completa.",
                "text_below_es": "\"¡Gracias, {pet_name}!\" dijo limpiándose la cara, mientras {pet_name} se echaba al sol.",
                "text_above_en": "{pet_name} came out of the stream and shook with all the energy in the world. Water flew everywhere and {name} got a full shower.",
                "text_below_en": "\"Thanks, {pet_name}!\" they said wiping their face, while {pet_name} lay down in the sun."
            },
            {
                "text_above_es": "Después de una hora de subida, llegaron a un mirador. El valle se extendía debajo de ellos como una alfombra de verdes infinitos.",
                "text_below_es": "{name} se sentó en una roca y {pet_name} se echó a sus pies. Por un momento, el silencio fue perfecto.",
                "text_above_en": "After an hour of climbing, they reached a lookout point. The valley spread below them like an endless carpet of greens.",
                "text_below_en": "{name} sat on a rock and {pet_name} lay at their feet. For a moment, the silence was perfect."
            },
            {
                "text_above_es": "{name} sacó sándwiches de la mochila y le dio a {pet_name} sus galletas favoritas. Comieron juntos mirando las montañas, el viento suave trayendo olor a flores silvestres.",
                "text_below_es": "{pet_name} apoyó su cabeza en la pierna de {name}, pidiendo otro bocado.",
                "text_above_en": "{name} pulled out sandwiches from the backpack and gave {pet_name} their favorite treats. They ate together watching the mountains, the gentle breeze carrying the scent of wildflowers.",
                "text_below_en": "{pet_name} rested their head on {name}'s leg, asking for another bite."
            },
            {
                "text_above_es": "Cuando encontraron el lugar perfecto entre los pinos, {name} empezó a armar la tienda de campaña.",
                "text_below_es": "{pet_name} decidió \"ayudar\" llevándose una estaca en la boca cada vez que {name} la ponía en su lugar.",
                "text_above_en": "When they found the perfect spot among the pines, {name} started setting up the tent.",
                "text_below_en": "{pet_name} decided to \"help\" by carrying away a tent stake in their mouth every time {name} put one in place."
            },
            {
                "text_above_es": "Después de negociar con {pet_name} (dos galletas a cambio de las estacas), la tienda quedó lista. {name} infló el colchón y puso las mantas.",
                "text_below_es": "{pet_name} inmediatamente se metió a la tienda y se acostó justo en el centro, ocupando todo el espacio.",
                "text_above_en": "After negotiating with {pet_name} (two treats in exchange for the stakes), the tent was ready. {name} inflated the mattress and laid out the blankets.",
                "text_below_en": "{pet_name} immediately went inside the tent and lay right in the center, taking up all the space."
            },
            {
                "text_above_es": "Antes del atardecer, bajaron hasta el río. El agua corría entre piedras grandes formando pequeñas cascadas. {pet_name} metió las patas al agua fría y salpicó de alegría.",
                "text_below_es": "{name} se quitó las botas y metió los pies, sintiendo cómo el agua fresca le devolvía la vida.",
                "text_above_en": "Before sunset, they went down to the river. Water flowed between large rocks forming small waterfalls. {pet_name} dipped their paws in the cold water and splashed with joy.",
                "text_below_en": "{name} took off their boots and dipped their feet, feeling the cool water bring them back to life."
            },
            {
                "text_above_es": "De vuelta al campamento, el cielo se pintó de naranjas y morados. {name} y {pet_name} se sentaron juntos mirando cómo el sol se escondía detrás de las montañas.",
                "text_below_es": "\"No hay pantalla en el mundo que muestre algo tan bonito\", susurró {name}.",
                "text_above_en": "Back at camp, the sky painted itself in oranges and purples. {name} and {pet_name} sat together watching the sun hide behind the mountains.",
                "text_below_en": "\"No screen in the world can show something this beautiful,\" whispered {name}."
            },
            {
                "text_above_es": "Cuando oscureció, {name} encendió una fogata. Las llamas bailaban lanzando chispas hacia las estrellas. {pet_name} se acurrucó cerca del fuego, hipnotizado por el movimiento de las llamas.",
                "text_below_es": "{name} calentó malvaviscos y le dio uno a {pet_name}, que lo atrapó al vuelo.",
                "text_above_en": "When it got dark, {name} lit a campfire. The flames danced, throwing sparks toward the stars. {pet_name} curled up near the fire, mesmerized by the dancing flames.",
                "text_below_en": "{name} roasted marshmallows and tossed one to {pet_name}, who caught it mid-air."
            },
            {
                "text_above_es": "{name} se acostó sobre una manta mirando las estrellas. Miles de puntos brillantes llenaban el cielo como nunca los había visto en la ciudad.",
                "text_below_es": "{pet_name} se acostó a su lado, y {name} sintió el calor de su compañero en la noche fría.",
                "text_above_en": "{name} lay on a blanket looking at the stars. Thousands of brilliant points filled the sky like they'd never seen in the city.",
                "text_below_en": "{pet_name} lay beside them, and {name} felt the warmth of their companion in the cold night."
            },
            {
                "text_above_es": "{name} despertó con el sol entrando por la tienda y algo pesado sobre sus piernas: {pet_name} dormía atravesado, roncando suavemente.",
                "text_below_es": "Afuera, el bosque cantaba con pájaros y el aire frío olía a rocío. {name} sonrió. No quería estar en ningún otro lugar.",
                "text_above_en": "{name} woke up with sunlight streaming into the tent and something heavy on their legs: {pet_name} was sleeping sideways across them, snoring softly.",
                "text_below_en": "Outside, the forest sang with birds and the cold air smelled of dew. {name} smiled. They didn't want to be anywhere else."
            },
            {
                "text_above_es": "Con la mochila llena de recuerdos y el corazón lleno de paz, {name} emprendió el camino de vuelta. {pet_name} caminaba a su lado con paso firme, como un compañero que dice: \"A donde vayas, voy contigo.\"",
                "text_below_es": "Porque las mejores aventuras no se miden en kilómetros, sino en quién camina a tu lado.",
                "text_above_en": "With a backpack full of memories and a heart full of peace, {name} began the journey back. {pet_name} walked beside them with steady steps, like a companion saying: \"Wherever you go, I go with you.\"",
                "text_below_en": "Because the best adventures aren't measured in miles, but in who walks beside you."
            }
        ],
    },
    "star_keeper_illustrated": {
        "title_es": "{name} y el Guardián de las Estrellas",
        "title_en": "{name} and the Star Keeper",
        "age_range": "6-7",
        "book_type": "illustrated",
        "price": 55,
        "page_count": 24,
        "use_fixed_scenes": True,
        "scenes_dir": "generated",
        "preview_prompt_override": "Full body portrait of a cheerful {gender_word} (6-7 years old) with {hair_desc}, {eye_desc} and {skin_desc}, {gender_features}, wearing a deep blue explorer jacket with silver star buttons over a white shirt, dark pants and sturdy boots, a small silver compass pendant around neck. The child is standing at the entrance of an old stone lighthouse on a dramatic clifftop at twilight, with a magnificent starry sky above. Next to the child is LUNA - a small five-pointed star the size of a child's hand, made of shimmering silver-white light, two big expressive violet-purple glowing eyes, two tiny translucent iridescent wings that leave a trail of moon dust, a small comet-like tail that softly pulses with warm light. Dreamy celestial atmosphere with deep blue and violet tones, golden and silver sparkles. Children's storybook watercolor illustration style, soft luminous colors, dreamy magical atmosphere. NO text, NO watermark, NO signature, NO logo, clean illustration only",
        "content_pages": [
            {"text_es": "En lo alto de un acantilado frente al mar, {name} descubrió un viejo faro abandonado. Su puerta se abrió sola, invitándole a entrar con un resplandor azul misterioso.", "text_en": "On a clifftop overlooking the sea, {name} discovered an old abandoned lighthouse. Its door opened by itself, inviting them inside with a mysterious blue glow."},
            {"text_es": "Dentro del faro había un telescopio gigante cubierto de polvo de estrellas. Al tocarlo, el techo se abrió revelando un cielo nocturno lleno de constelaciones brillantes.", "text_en": "Inside the lighthouse was a giant telescope covered in stardust. When {name} touched it, the roof opened up revealing a night sky full of brilliant constellations."},
            {"text_es": "De pronto, una pequeña estrella cayó del cielo y aterrizó suavemente en las manos de {name}. \"¡Hola! Soy LUNA\", susurró con voz dulce y cristalina.", "text_en": "Suddenly, a small star fell from the sky and landed softly in {name}'s hands. \"Hello! I'm LUNA,\" it whispered with a sweet, crystal-clear voice."},
            {"text_es": "LUNA le explicó que las estrellas se estaban apagando porque el Gran Reloj Celestial se había detenido. Sin él, la noche perdería toda su luz para siempre.", "text_en": "LUNA explained that the stars were going out because the Great Celestial Clock had stopped. Without it, the night would lose all its light forever."},
            {"text_es": "\"¡Necesito tu ayuda!\", pidió LUNA. El telescopio brilló y se convirtió en un puente de luz que ascendía hacia las nubes. {name} dio el primer paso con valentía.", "text_en": "\"I need your help!\" LUNA pleaded. The telescope glowed and became a bridge of light rising into the clouds. {name} took the first brave step."},
            {"text_es": "El puente los llevó al Jardín de las Luciérnagas, un campo flotante donde miles de luciérnagas gigantes iluminaban flores que crecían entre las nubes.", "text_en": "The bridge led them to the Firefly Garden, a floating meadow where thousands of giant fireflies illuminated flowers that grew among the clouds."},
            {"text_es": "Las luciérnagas les entregaron la primera Llave Estelar, una llave dorada hecha de luz concentrada. \"Necesitan tres llaves para el Gran Reloj\", explicaron.", "text_en": "The fireflies gave them the first Star Key, a golden key made of concentrated light. \"You'll need three keys for the Great Clock,\" they explained."},
            {"text_es": "{name} y LUNA navegaron en un barco hecho de rayos de luna sobre el Río de Estrellas Fugaces. Cada estrella que pasaba dejaba un rastro de deseos brillantes.", "text_en": "{name} and LUNA sailed in a boat made of moonbeams across the River of Shooting Stars. Each passing star left a trail of glowing wishes."},
            {"text_es": "Al final del río encontraron la Cueva de los Ecos de Luz. Dentro, los sonidos se convertían en colores y las palabras amables creaban arcoíris pequeños.", "text_en": "At the end of the river they found the Cave of Light Echoes. Inside, sounds turned into colors and kind words created tiny rainbows."},
            {"text_es": "{name} dijo \"te quiero\" y un arcoíris brillante formó la segunda Llave Estelar. LUNA aplaudió con sus pequeñas alas, dejando un rastro de polvo plateado.", "text_en": "{name} said \"I love you\" and a brilliant rainbow formed the second Star Key. LUNA clapped her tiny wings, leaving a trail of silver dust."},
            {"text_es": "Llegaron al Bosque de Cristal, donde los árboles eran de hielo transparente y reflejaban mil versiones del cielo estrellado en cada rama y hoja.", "text_en": "They reached the Crystal Forest, where the trees were made of transparent ice and reflected a thousand versions of the starry sky in every branch and leaf."},
            {"text_es": "En el centro del bosque, un lobo de constelaciones cuidaba la tercera Llave Estelar. \"Solo quien tenga corazón valiente puede llevarla\", dijo con voz profunda.", "text_en": "In the heart of the forest, a wolf made of constellations guarded the third Star Key. \"Only a brave heart may carry it,\" the wolf said in a deep voice."},
            {"text_es": "{name} caminó hacia el lobo sin miedo y le acarició la cabeza de estrellas. El lobo sonrió y entregó la última llave con una reverencia elegante.", "text_en": "{name} walked up to the wolf without fear and stroked its head of stars. The wolf smiled and handed over the last key with an elegant bow."},
            {"text_es": "Con las tres Llaves Estelares brillando en sus manos, {name} y LUNA volaron hacia la Torre del Cielo, una torre infinita hecha enteramente de luz de luna.", "text_en": "With the three Star Keys glowing in their hands, {name} and LUNA flew toward the Sky Tower, an infinite tower made entirely of moonlight."},
            {"text_es": "En la cima de la torre encontraron el Gran Reloj Celestial. Era enorme, con engranajes de plata y manecillas hechas de rayos de sol y luna entrelazados.", "text_en": "At the top of the tower they found the Great Celestial Clock. It was enormous, with silver gears and hands made of intertwined sun and moonbeams."},
            {"text_es": "{name} colocó las tres llaves en el reloj. Los engranajes comenzaron a girar y una onda de luz dorada y plateada se expandió por todo el cielo nocturno.", "text_en": "{name} placed the three keys into the clock. The gears began to turn and a wave of golden and silver light expanded across the entire night sky."},
            {"text_es": "¡Las estrellas volvieron a brillar! Miles de estrellas se encendieron una por una, y el cielo se llenó de constelaciones más hermosas que nunca, bailando en la oscuridad.", "text_en": "The stars shone again! Thousands of stars lit up one by one, and the sky filled with constellations more beautiful than ever, dancing in the darkness."},
            {"text_es": "\"Siempre que mires al cielo, recuerda que tú salvaste las estrellas\", susurró LUNA, brillando más fuerte que nunca. \"La luz más poderosa vive en tu corazón.\"", "text_en": "\"Whenever you look at the sky, remember that you saved the stars,\" LUNA whispered, shining brighter than ever. \"The most powerful light lives in your heart.\""},
            {"text_es": "{name} volvió a casa abrazando la luz de LUNA en su pecho. Desde esa noche, una estrella nueva brilla en el cielo con el nombre de un guardián muy especial. Y colorín colorado, este cuento estelar ha terminado.", "text_en": "{name} returned home holding LUNA's light close to their heart. From that night on, a new star shines in the sky bearing the name of a very special guardian. And they all lived happily ever after. The End."}
        ]
    },
    "space_astronaut": {
        "title_es": "{name} astronauta",
        "title_en": "{name} the Astronaut",
        "age_range": "3-8",
        "text_layout": "split",
        "use_preview_as_cover": True,
        "preview_prompt_override": """Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, cheerful excited smile. OUTFIT: Cute child-sized white astronaut suit with light blue and silver accents, golden helmet visor open showing happy face. ACTION: The {gender_word} is standing proudly with {skin_tone} hands on hips in a heroic pose, looking up with wonder. SETTING: Soft magical space background with gentle twinkling stars, purple-blue cosmic glow, distant pastel planets. ATMOSPHERE: Warm magical wonder, soft luminous colors, dreamy space adventure. STRICT: Only ONE {gender_word}. The {gender_word} is 100% human, with a completely normal body, two arms, two legs, smooth {skin_tone} skin, and normal child anatomy. {style}""",
        "cover_template": """Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, serene peaceful smile with eyes full of wonder. OUTFIT: Cute child-sized white astronaut suit with light blue and silver accents, golden helmet visor open. ACTION: The {gender_word} is floating peacefully in beautiful cosmic space, arms gently spread, {hair_action}, surrounded by soft stardust. SETTING: Beautiful cosmic space with soft pastel colored planets, gentle twinkling stars, warm glowing moon in the background. Dreamy purple, blue and pink nebula colors. ATMOSPHERE: Magical wonder, peaceful floating, centered composition perfect for book cover. STRICT: Only ONE {gender_word}. The {gender_word} is 100% human, with a completely normal body, two arms, two legs, smooth {skin_tone} skin, and normal child anatomy. {style}""",
        "pages": [
            {
                "text_above_es": "Desde muy temprano, {name} sentía una gran curiosidad por el cielo. Le gustaba mirar hacia arriba e imaginar qué había más allá de las nubes y las estrellas.",
                "text_below_es": "Una noche especial, mientras observaba las estrellas desde su ventana, {name} descubrió que el cielo parecía invitarl{o_a} a un viaje muy especial.",
                "text_above_en": "From very early on, {name} felt a great curiosity about the sky. {name} loved looking up and imagining what lay beyond the clouds and the stars.",
                "text_below_en": "One special night, while watching the stars from the window, {name} discovered that the sky seemed to be inviting a very special journey.",
                "scene_template": """Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, curious wonder-filled expression looking up at the sky. OUTFIT: Cozy pajamas with tiny star patterns in soft blue. ACTION: The {gender_word} is sitting by a large bedroom window at night, chin resting on {skin_tone} hands, gazing up at a magnificent starry sky with wide amazed eyes. SETTING: Cozy bedroom WIDE VIEW with space-themed decorations, telescope by the window, planet posters on walls, star-shaped night light. Through the large window, a VAST starry sky with twinkling stars and a glowing crescent moon. ATMOSPHERE: Warm indoor light contrasting with cool starlit sky, magical sparkles, dreamy wonder. STRICT: Only ONE {gender_word}. The {gender_word} is 100% human, with a completely normal body, two arms, two legs, smooth {skin_tone} skin, and normal child anatomy. {style}"""
            },
            {
                "text_above_es": "{name} se puso su traje de astronauta, no para viajar lejos, sino para soñar despiert{o_a}. Al cerrar los ojos, sintió que flotaba suavemente.",
                "text_below_es": "El espacio l{o_a} estaba invitando. No había ruido, solo calma. Las estrellas brillaban despacio y parecían saludar.",
                "text_above_en": "{name} put on an astronaut suit, not to travel far, but to dream awake. Upon closing both eyes, {name} felt floating gently upward.",
                "text_below_en": "Space was extending a warm invitation. There was no noise, only calm. The stars shone slowly and seemed to wave hello.",
                "scene_template": """Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, eyes closed with a peaceful dreamy smile. OUTFIT: Cute child-sized white astronaut suit with light blue and silver accents, golden helmet visor open. ACTION: The {gender_word} is beginning to float gently above the bedroom floor with arms slightly spread, {hair_action}, a soft golden glow surrounding the body as the magical journey begins. SETTING: Bedroom WIDE VIEW transforming into space, the floor fades into stars, the ceiling dissolves into cosmic purple-blue sky. Half bedroom half cosmos. Gentle sparkles and stardust rising from below. ATMOSPHERE: Magical transition moment, warm golden light mixing with cool cosmic glow, peaceful floating sensation. STRICT: Only ONE {gender_word}. The {gender_word} is 100% human, with a completely normal body, two arms, two legs, smooth {skin_tone} skin, and normal child anatomy. {style}"""
            },
            {
                "text_above_es": "{name} se sentía segur{o_a} y tranquil{o_a}. Entendió que el espacio no era un lugar frío, sino un lugar lleno de silencio amable.",
                "text_below_es": "Cada respiración l{o_a} hacía sentir más valiente, list{o_a} para explorar con el corazón abierto.",
                "text_above_en": "{name} felt safe and peaceful. {name} understood that space was not a cold place, but a place full of gentle silence.",
                "text_below_en": "Each breath made {name} feel braver, ready to explore the universe with an open heart.",
                "scene_template": """Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, serene peaceful smile with eyes half-open in wonder. OUTFIT: Cute child-sized white astronaut suit with light blue and silver accents, golden helmet visor open. ACTION: The {gender_word} is floating peacefully in gentle cosmic space with arms relaxed at sides, {hair_action}, surrounded by softly glowing friendly stars that seem to smile. SETTING: WIDE VIEW of gentle infinite cosmic space with soft purple-blue tones, friendly twinkling stars of different sizes scattered everywhere, soft nebula wisps in pastel colors. ATMOSPHERE: Ultimate peace and safety, warm soft starlight, gentle magical sparkles floating like fireflies, nurturing cosmic embrace. STRICT: Only ONE {gender_word}. The {gender_word} is 100% human, with a completely normal body, two arms, two legs, smooth {skin_tone} skin, and normal child anatomy. {style}"""
            },
            {
                "text_above_es": "Mientras flotaba entre planetas de colores suaves, {name} notó que el espacio también podía escucharse. No con sonidos fuertes, sino con sensaciones.",
                "text_below_es": "Cada estrella transmitía calma y cada planeta compartía una emoción distinta. {name} se detuvo a observar y a sentir.",
                "text_above_en": "While floating among planets of soft colors, {name} noticed that space could also be heard. Not with loud sounds, but with feelings.",
                "text_below_en": "Each star transmitted calm and each planet shared a different emotion. {name} stopped to observe and to feel.",
                "scene_template": """Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, amazed expression with mouth slightly open in awe. OUTFIT: Cute child-sized white astronaut suit with light blue and silver accents, golden helmet visor open. ACTION: The {gender_word} is floating among beautiful pastel-colored planets, one {skin_tone} hand reaching out to touch a nearby soft pink planet, {hair_action}, head turning to look at all the wonders around. SETTING: VAST COSMIC PANORAMA with beautiful pastel-colored planets stretching in all directions, soft pink, lavender, mint green, peach, and baby blue worlds of varying sizes. Some planets have gentle rings, others have soft glowing atmospheres. ATMOSPHERE: Discovery and sensory wonder, each planet radiating a different soft colored glow, musical sparkles floating between planets, cosmic symphony of colors. STRICT: Only ONE {gender_word}. The {gender_word} is 100% human, with a completely normal body, two arms, two legs, smooth {skin_tone} skin, and normal child anatomy. {style}"""
            },
            {
                "text_above_es": "El traje de astronauta brillaba suavemente, protegiendo a {name} como un abrazo invisible. No tenía prisa.",
                "text_below_es": "{name} descubrió que la valentía no siempre significa avanzar rápido, sino saber detenerse y escuchar lo que se siente por dentro.",
                "text_above_en": "The astronaut suit glowed softly, protecting {name} like an invisible hug. There was no hurry at all.",
                "text_below_en": "{name} discovered that bravery does not always mean moving fast, but knowing when to stop and listen to what is felt inside.",
                "scene_template": """Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, thoughtful gentle expression with {skin_tone} hand over heart. OUTFIT: Cute child-sized white astronaut suit glowing with soft golden-blue light, light blue and silver accents, golden helmet visor open. ACTION: The {gender_word} is floating still in deep space, one {skin_tone} hand placed over heart, eyes looking inward with a gentle thoughtful smile. The astronaut suit radiates a warm protective glow around the child like a shield of light. SETTING: WIDE VIEW of deep quiet cosmic space, vast and serene. Distant gentle stars and soft nebula colors in the background. A warm golden aura emanates from the child creating a safe bubble of light. ATMOSPHERE: Inner reflection and quiet courage, warm protective glow contrasting with vast peaceful darkness, contemplative magical moment, soft sparkles. STRICT: Only ONE {gender_word}. The {gender_word} is 100% human, with a completely normal body, two arms, two legs, smooth {skin_tone} skin, and normal child anatomy. {style}"""
            },
            {
                "text_above_es": "El espacio respondía con una luz suave, como si aprobara cada pensamiento. {name} extendió la mano y tocó el polvo de estrellas.",
                "text_below_es": "Las nebulosas de colores giraban a su alrededor y las estrellas fugaces dejaban estelas brillantes. ¡Era la aventura más grande del universo!",
                "text_above_en": "Space responded with gentle light, as if approving each thought. {name} reached out one hand and touched the stardust.",
                "text_below_en": "Colorful nebulas swirled all around and shooting stars left bright trails behind. It was the greatest adventure in the entire universe!",
                "scene_template": """Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, face showing pure joy and amazement, big bright smile. OUTFIT: Cute child-sized white astronaut suit with light blue and silver accents, golden helmet visor open. ACTION: The {gender_word} is soaring joyfully through magnificent cosmic space, one {skin_tone} hand reaching out to touch passing stardust that turns to golden sparkles, {hair_action}, laughing with pure delight. SETTING: EPIC WIDE VIEW of spectacular cosmic landscape with giant colorful nebulas swirling across the entire sky in vibrant purples, blues, pinks and golds. Shooting stars streak across the scene leaving bright trails. Magnificent ringed planets visible in the distance. Stardust and golden sparkles trail behind the child. ATMOSPHERE: Breathtaking cosmic adventure climax, maximum wonder and joy, explosive magical colors, triumphant exploration moment. STRICT: Only ONE {gender_word}. The {gender_word} is 100% human, with a completely normal body, two arms, two legs, smooth {skin_tone} skin, and normal child anatomy. {style}"""
            },
            {
                "text_above_es": "Poco a poco, {name} regresó flotando suavemente hasta sentirse de nuevo en su lugar. Al abrir los ojos, el cielo seguía ahí, brillante y cercano.",
                "text_below_es": "{name} supo que no necesitaba ir lejos para ser astronauta. Bastaba con imaginar, sentir y confiar. Desde ese día, cada vez que mira las estrellas, recuerda que siempre puede viajar con su imaginación.",
                "text_above_en": "Little by little, {name} returned, floating gently until feeling back in place. Upon opening both eyes, the sky was still there, bright and close.",
                "text_below_en": "{name} knew that going far was not needed to be an astronaut. It was enough to imagine, feel and trust. From that day on, every time {name} looks at the stars, the journey continues.",
                "scene_template": """Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, warm content smile with eyes full of happy memories. OUTFIT: Cute child-sized white astronaut suit with light blue and silver accents, helmet off resting beside on the bed. ACTION: The {gender_word} is sitting on a cozy bed, {skin_tone} hands held to heart, looking out a large window at the starry night sky with a peaceful knowing smile. A few magical sparkles still float around the child like fading stardust memories. SETTING: WIDE VIEW of cozy bedroom with space decorations, telescope by window, star-shaped night light glowing warmly. Through the large window, a VAST beautiful starry sky with stars twinkling warmly as if saying goodbye. Soft moonlight streams in through the glass. ATMOSPHERE: Warm peaceful return, nostalgic gentle glow, fading magical sparkles, the wonder of imagination lingering in the air. STRICT: Only ONE {gender_word}. The {gender_word} is 100% human, with a completely normal body, two arms, two legs, smooth {skin_tone} skin, and normal child anatomy. {style}"""
            }
        ],
        "closing_template": """Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, serene confident smile with eyes full of dreams and wonder. OUTFIT: Cute child-sized white astronaut suit with light blue and silver accents, golden helmet visor open. ACTION: The {gender_word} is standing alone on a grassy hilltop under a magnificent starry night sky, one {skin_tone} hand reaching up toward the stars, {hair_action}, looking up with peaceful confidence. SETTING: Beautiful grassy hilltop WIDE VIEW under a vast starry night sky, gentle warm breeze, wildflowers glowing softly, distant city lights twinkling below, shooting star streaking across the sky, crescent moon glowing warmly. ATMOSPHERE: Peaceful dreamy wonder, warm starlight, magical sparkles floating like fireflies, sense of infinite possibility and courage. STRICT: Only ONE {gender_word}, NO companion, NO other characters, NO animals. The {gender_word} is 100% human, with a completely normal body, two arms, two legs, smooth {skin_tone} skin, and normal child anatomy. {style}""",
        "closing_message_es": "{name}, el universo entero cabe en tu imaginación. ¡Sigue soñando en grande!",
        "closing_message_en": "{name}, the entire universe fits inside your imagination. Keep dreaming big!"
    },
    "zebra_stripes": {
        "title_es": "{name} y la aventura en la sabana",
        "title_en": "{name} and the Savanna Adventure",
        "age_range": "3-8",
        "text_layout": "split",
        "use_preview_as_cover": True,
        "preview_prompt_override": """Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, curious surprised expression with wide eyes. OUTFIT: Khaki safari t-shirt, khaki shorts, brown boots. ACTION: The {gender_word} stands on the riverbank watching with curiosity, {hair_action}, one {skin_tone} hand reaching forward. {lila_desc}, happily jumping between smooth river stones, splashing water with her hooves. SETTING: WIDE VIEW savanna river, clear shallow water, smooth stones, green grass banks, acacia trees, golden morning sunlight. ATMOSPHERE: Joyful discovery, sparkling water droplets, warm golden light. STRICT: Only ONE {gender_word}. The {gender_word} is 100% human, two arms, two legs, smooth {skin_tone} skin, NO tail, NO animal features, NO animal ears. {style}""",
        "cover_template": """Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, curious surprised expression with wide eyes. OUTFIT: Khaki safari t-shirt, khaki shorts, brown boots. ACTION: The {gender_word} stands on the riverbank watching with curiosity, {hair_action}, one {skin_tone} hand reaching forward. {lila_desc}, happily jumping between smooth river stones, splashing water with her hooves. SETTING: WIDE VIEW savanna river, clear shallow water, smooth stones, green grass banks, acacia trees, golden morning sunlight. ATMOSPHERE: Joyful discovery, sparkling water droplets, warm golden light. STRICT: Only ONE {gender_word}. The {gender_word} is 100% human, two arms, two legs, smooth {skin_tone} skin, NO tail, NO animal features, NO animal ears. {style}""",
        "pages": [
            {
                "text_above_es": "Una mañana soleada, {name} caminaba por la sabana africana cuando escuchó un chapoteo junto al río.",
                "text_below_es": "Era una cebra joven llamada Lila, que jugaba saltando entre las piedras del agua con mucha alegría. Sus rayas brillaban bajo el sol dorado.",
                "text_above_en": "One sunny morning, {name} was walking through the African savanna when a splashing sound came from the river.",
                "text_below_en": "It was a young zebra named Lila, happily jumping between the river stones. Her stripes sparkled under the golden sun.",
                "scene_template": """Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, curious surprised expression with wide eyes. OUTFIT: Khaki safari t-shirt, khaki shorts, brown boots. ACTION: The {gender_word} stands on the riverbank watching with curiosity, {hair_action}, one {skin_tone} hand reaching forward. {lila_desc}, happily jumping between smooth river stones, splashing water with her hooves. SETTING: WIDE VIEW savanna river, clear shallow water, smooth stones, green grass banks, acacia trees, golden morning sunlight. ATMOSPHERE: Joyful discovery, sparkling water droplets, warm golden light. STRICT: Only ONE {gender_word}. The {gender_word} is 100% human, two arms, two legs, smooth {skin_tone} skin, NO tail, NO animal features, NO animal ears. {style}"""
            },
            {
                "text_above_es": "Lila invitó a {name} a descansar bajo una gran acacia. Compartieron la sombra fresca mientras observaban a los pájaros de colores volar entre las ramas.",
                "text_below_es": "Así comenzó una amistad muy especial. Lila le contó que conocía todos los secretos de la sabana y quería mostrarle cada uno.",
                "text_above_en": "Lila invited {name} to rest under a big acacia tree. They shared the cool shade while watching colorful birds fly between the branches.",
                "text_below_en": "That's how a very special friendship began. Lila told {name} she knew all the secrets of the savanna and wanted to show each one.",
                "scene_template": """Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, relaxed happy smile looking up at birds. OUTFIT: Khaki safari t-shirt, khaki shorts, brown boots. ACTION: The {gender_word} sits leaning against a large acacia tree trunk, {hair_action}, looking up at colorful birds. {lila_desc}, lying comfortably on the grass beside the {gender_word}, looking content. Small colorful birds fly between the branches above. SETTING: Under wide canopy of a massive acacia tree, dappled shade, green grass, bright savanna background. ATMOSPHERE: Peaceful friendship, cool shade, warm afternoon. STRICT: Only ONE {gender_word}. The {gender_word} is 100% human, two arms, two legs, smooth {skin_tone} skin, NO tail, NO animal features, NO animal ears. {style}"""
            },
            {
                "text_above_es": "{name} y Lila exploraron un campo lleno de flores silvestres amarillas y naranjas. Lila olía cada flor con su suave nariz rosada.",
                "text_below_es": "Mientras tanto, {name} hacía un ramo pequeño para llevar de recuerdo. Las mariposas bailaban alrededor de los dos amigos.",
                "text_above_en": "{name} and Lila explored a field full of yellow and orange wildflowers. Lila smelled each flower with her soft pink nose.",
                "text_below_en": "Meanwhile, {name} made a small bouquet to take as a souvenir. Butterflies danced around the two friends.",
                "scene_template": """Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, delighted smile, kneeling among flowers. OUTFIT: Khaki safari t-shirt, khaki shorts, brown boots. ACTION: The {gender_word} kneels in a flower field, {hair_action}, holding a small bouquet of yellow and orange wildflowers. {lila_desc}, lowering her head to smell an orange flower with her soft pink nose. Colorful butterflies flutter around them. SETTING: WIDE VIEW vibrant field of yellow and orange wildflowers, green hills, bright blue sky, warm sunlight. ATMOSPHERE: Joyful exploration, vibrant colors, butterflies everywhere. STRICT: Only ONE {gender_word}. The {gender_word} is 100% human, two arms, two legs, smooth {skin_tone} skin, NO tail, NO animal features, NO animal ears. {style}"""
            },
            {
                "text_above_es": "Junto a un charco de barro encontraron a un elefante bebé que intentaba salpicar agua con su trompa.",
                "text_below_es": "{name} y Lila se acercaron a jugar y los tres se rieron juntos bajo el sol cálido. El elefante los salpicó con barro suave.",
                "text_above_en": "By a mud puddle they found a baby elephant trying to splash water with its trunk.",
                "text_below_en": "{name} and Lila came closer to play, and the three of them laughed together under the warm sun. The elephant splashed them with soft mud.",
                "scene_template": """Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, laughing joyfully with mouth open. OUTFIT: Khaki safari t-shirt, khaki shorts, brown boots, mud splashes on clothes. ACTION: The {gender_word} stands on the LEFT laughing, {hair_action}, shielding face from mud splashes. A chubby grey baby elephant splashes mud with its trunk in the CENTER. {lila_desc}, watching amused from the RIGHT on dry grass. SETTING: Muddy waterhole in savanna, green grass, acacia trees, warm sun. ATMOSPHERE: Playful fun, laughter, warm energy. STRICT: Only ONE {gender_word}. The {gender_word} is 100% human, two arms, two legs, smooth {skin_tone} skin, NO tail, NO animal features, NO animal ears. {style}"""
            },
            {
                "text_above_es": "Una jirafa altísima bajó su largo cuello para conocer a {name}. Lila le presentó con orgullo a su nuevo amigo.",
                "text_below_es": "La jirafa les ofreció hojas frescas de lo más alto del árbol. {name} nunca había visto un animal tan alto y elegante.",
                "text_above_en": "A very tall giraffe lowered her long neck to meet {name}. Lila proudly introduced her new friend.",
                "text_below_en": "The giraffe offered them fresh leaves from the very top of the tree. {name} had never seen such a tall and elegant animal.",
                "scene_template": """Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, looking up with amazement, mouth open in awe. OUTFIT: Khaki safari t-shirt, khaki shorts, brown boots. ACTION: The {gender_word} stands on the LEFT looking up, {hair_action}, one {skin_tone} hand reaching up. A tall spotted giraffe towers on the RIGHT, lowering her long neck to offer green leaves. {lila_desc}, sitting in the BACKGROUND looking proud. SETTING: Under a tall acacia tree in savanna, bright afternoon light, golden grass. ATMOSPHERE: Wonder, gentle kindness, warm light through leaves. STRICT: Only ONE {gender_word}. The {gender_word} is 100% human, two arms, two legs, smooth {skin_tone} skin, NO tail, NO animal features, NO animal ears. {style}"""
            },
            {
                "text_above_es": "Lila guió a {name} hasta una cascada escondida entre rocas grandes. El agua brillaba como diamantes bajo el sol.",
                "text_below_es": "Juntos se sentaron a escuchar el sonido tranquilo del agua cayendo. Era el lugar más bonito que {name} había visto jamás.",
                "text_above_en": "Lila guided {name} to a hidden waterfall between big rocks. The water sparkled like diamonds in the sun.",
                "text_below_en": "Together they sat and listened to the peaceful sound of the falling water. It was the most beautiful place {name} had ever seen.",
                "scene_template": """Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, peaceful amazed expression. OUTFIT: Khaki safari t-shirt, khaki shorts, brown boots. ACTION: The {gender_word} sits on a mossy rock, {hair_action}, both {skin_tone} hands resting on knees, gazing at the waterfall. {lila_desc}, sitting calmly on the grass beside the {gender_word}, looking serene. SETTING: Hidden waterfall cascading down dark rocks into a crystal pool, green ferns, moss, tropical flowers, sunbeams creating rainbow prisms in mist. ATMOSPHERE: Magical serenity, sparkling water, warm sunlight. STRICT: Only ONE {gender_word}. The {gender_word} is 100% human, two arms, two legs, smooth {skin_tone} skin, NO tail, NO animal features, NO animal ears. {style}"""
            },
            {
                "text_above_es": "Al caer la tarde, {name} y Lila caminaron juntos por la sabana dorada. Lila frotó su cabeza suavemente contra {name}.",
                "text_below_es": "Sabían que esta aventura viviría para siempre en sus corazones. La amistad verdadera no conoce distancias.",
                "text_above_en": "As the evening fell, {name} and Lila walked together through the golden savanna. Lila gently rubbed her head against {name}.",
                "text_below_en": "They knew this adventure would live forever in their hearts. True friendship knows no distance.",
                "scene_template": """Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, peaceful warm smile. OUTFIT: Khaki safari t-shirt, khaki shorts, brown boots. ACTION: The {gender_word} walks on the LEFT of a golden path, {hair_action}, one {skin_tone} hand resting gently on Lila's back. {lila_desc}, walking RIGHT BESIDE the {gender_word} at the SAME height, looking back with a warm smile. SETTING: WIDE panoramic savanna at golden sunset, orange and pink sky, silhouetted acacia trees, golden grass, path into the distance. ATMOSPHERE: Warm farewell, deep friendship, golden light, peaceful ending. STRICT: Only ONE {gender_word}. The {gender_word} is 100% human, two arms, two legs, smooth {skin_tone} skin, NO tail, NO animal features, NO animal ears. Lila is the SAME HEIGHT as the {gender_word}. {style}"""
            }
        ],
        "closing_template": """Disney Pixar 3D style illustration. CHARACTER 1: The human {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, looking directly at the camera with a gentle inspiring smile. A normal human body, two arms, two legs, smooth skin. OUTFIT: Khaki safari t-shirt, khaki shorts, small brown explorer boots. ACTION: The {gender_word} stands alone confidently, one {skin_tone} hand placed over the heart, {hair_action}. SETTING: Beautiful African savanna at golden hour, soft warm light, acacia tree silhouette in the background, soft bokeh effect. ATMOSPHERE: Inspirational, adventure, pure heart, warm golden lighting. STRICT: Only ONE {gender_word} alone in the scene. The {gender_word} is 100% human, two arms, two legs, smooth {skin_tone} skin, regular child body. Empty background with only savanna landscape. Super high quality, masterpiece, 8k. {style}""",
        "closing_message_es": "{name}, la amistad verdadera hace que cada aventura sea mágica e inolvidable.",
        "closing_message_en": "{name}, true friendship makes every adventure magical and unforgettable."
    },
    "chronicles_valley": {
        "title_es": "Las Crónicas de {name}",
        "title_en": "The Chronicles of {name}",
        "age_range": "5-7",
        "text_layout": "split",
        "use_preview_as_cover": True,
        "preview_prompt_override": """Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, curious excited expression. A normal human body, two arms, two legs, smooth skin. OUTFIT: Cream medieval-style tunic with brown pants and leather boots, a small pouch at the waist. ACTION: The {gender_word} stands in an enchanted garden, {hair_action}, one {skin_tone} hand holding up a small glowing crystal key that emits golden light. SETTING: Ancient enchanted garden WIDE VIEW, lavender flowers, gnarled trees, magical golden sparkles. ATMOSPHERE: Wonder, discovery, magical morning light. STRICT: Only ONE {gender_word}. {style}""",
        "cover_template": """Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, amazed wondering expression looking at a glowing key. A normal human body, two arms, two legs, smooth skin. OUTFIT: Cream medieval-style tunic with brown pants and leather boots. ACTION: The {gender_word} kneels beside blooming lavender flowers, {hair_action}, one {skin_tone} hand holding up a small glowing crystal key with a constellation pattern. SETTING: Ancient enchanted garden WIDE VIEW, gnarled trees with twisted roots, small mysterious wooden door covered in green ivy visible behind, golden sparkles, warm morning sunlight. ATMOSPHERE: Magical discovery, wonder, adventure beginning, centered composition for book cover. STRICT: Only ONE {gender_word}. {style}""",
        "pages": [
            {
                "text_above_es": "Una mañana, mientras el sol dibujaba siluetas doradas sobre el césped, {name} descubrió algo bajo un arbusto de lavanda.",
                "text_below_es": "Era una llave de cristal que emitía un suave zumbido musical. Tenía grabada una constelación que brillaba con luz propia.",
                "text_above_en": "One morning, while the sun drew golden silhouettes on the grass, {name} discovered something under a lavender bush.",
                "text_below_en": "It was a crystal key that hummed with soft music. It had a constellation engraved that glowed with its own light.",
                "scene_template": """Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, wide-eyed wonder and excitement, mouth slightly open in amazement. A normal human body, two arms, two legs, smooth skin. OUTFIT: Cream medieval-style tunic with brown pants and leather boots. ACTION: The {gender_word} kneels beside blooming lavender flowers, {hair_action}, both {skin_tone} hands gently holding up a small glowing crystal key with a constellation pattern, examining it closely. Golden sparkles emanate from the key. SETTING: Ancient enchanted garden WIDE VIEW, gnarled trees with twisted roots, warm morning sunlight filtering through leaves creating golden rays, purple lavender flowers everywhere. ATMOSPHERE: Magical discovery, warm golden morning light, sparkles, scent of wonder. STRICT: Only ONE {gender_word}. {style}"""
            },
            {
                "text_above_es": "{name} encontró una pequeña puerta de madera oculta tras una cortina de hiedra. Al insertar la llave, la cerradura giró con un sonido de campanas.",
                "text_below_es": "La puerta se abrió, revelando un pasadizo iluminado por luciérnagas de colores que danzaban en la penumbra.",
                "text_above_en": "{name} found a small wooden door hidden behind a curtain of ivy. When inserting the key, the lock turned with a sound of bells.",
                "text_below_en": "The door opened, revealing a passage illuminated by colorful fireflies dancing in the shadows.",
                "scene_template": """Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, brave curious expression, eager smile. A normal human body, two arms, two legs, smooth skin. OUTFIT: Cream medieval-style tunic with brown pants and leather boots. ACTION: The {gender_word} stands before a small ancient wooden door covered in thick green ivy, {hair_action}, one {skin_tone} hand inserting the glowing crystal key into an ornate lock. The key glows as it turns. SETTING: Hidden corner of the enchanted garden WIDE VIEW, thick ivy covering an ancient stone wall, the door slightly ajar revealing colorful fireflies glowing inside a mysterious passage, ancient tree roots around. ATMOSPHERE: Mystery, magical threshold, golden sparkles from the key, warm and cool light mixing. STRICT: Only ONE {gender_word}. {style}"""
            },
            {
                "text_above_es": "Al final del pasadizo, {name} llegó al Valle de los Inventos Olvidados. Los árboles no daban frutas, sino bombillas de cristal que brillaban con cada idea.",
                "text_below_es": "Caminó maravillad{o_a} por senderos de arena plateada, saludando a pequeños robots de hojalata que cuidaban flores de metal.",
                "text_above_en": "At the end of the passage, {name} arrived at the Valley of Forgotten Inventions. The trees didn't bear fruits, but crystal light bulbs that glowed with each idea.",
                "text_below_en": "{name} walked amazed along paths of silver sand, greeting small tin robots that tended metal flowers.",
                "scene_template": """Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, amazed delighted expression looking around with pure wonder. A normal human body, two arms, two legs, smooth skin. OUTFIT: Cream medieval-style tunic with brown pants and leather boots. ACTION: The {gender_word} walks along a shimmering silver sand path, {hair_action}, one {skin_tone} hand waving to a small friendly tin robot nearby, the other hand at side. SETTING: Valley of Forgotten Inventions WIDE VIEW, fantastical trees growing crystal light bulbs instead of fruits glowing brightly, friendly small tin robots with big round eyes tending delicate metal flowers, paths of silver sand, soft violet sky with gear-shaped clouds. ATMOSPHERE: Wonder, imagination, whimsical steampunk fantasy, magical warm light. STRICT: Only ONE {gender_word}. {style}"""
            },
            {
                "text_above_es": "Encontró una bicicleta con alas de seda que parecía averiada. Un cartel decía: «Solo quien posea una imaginación radiante podrá hacerme volar».",
                "text_below_es": "{name} le contó una historia sobre galaxias lejanas. Mientras hablaba, las alas vibraron y la bicicleta se elevó rodeada de luz.",
                "text_above_en": "There was a bicycle with silk wings that seemed broken. A sign read: 'Only one with a radiant imagination can make me fly.'",
                "text_below_en": "{name} told it a story about distant galaxies. While speaking, the wings vibrated and the bicycle rose surrounded by light.",
                "scene_template": """Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, passionate animated expression, mouth open telling a story with gesturing hands. A normal human body, two arms, two legs, smooth skin. OUTFIT: Cream medieval-style tunic with brown pants and leather boots. ACTION: The {gender_word} sits beside a magical bicycle with beautiful butterfly-like silk wings in soft pastel colors, {hair_action}, both {skin_tone} hands gesturing expressively while telling a story. The bicycle's wings begin to glow and vibrate with golden light, starting to lift off the ground. SETTING: Valley clearing WIDE VIEW, violet sky with gear clouds, crystal light bulb trees glowing nearby, silver sand path, small tin robots watching with curious big eyes. ATMOSPHERE: Imagination brought to life, magical golden sparkles from the bicycle, wonder and creativity. STRICT: Only ONE {gender_word}. {style}"""
            },
            {
                "text_above_es": "La bicicleta llevó a {name} hasta una biblioteca circular cuyas estanterías rozaban las estrellas.",
                "text_below_es": "En el centro, sobre un atril de madera tallada, descansaba un libro en blanco con un título dorado: «Las Crónicas de {name}».",
                "text_above_en": "The bicycle carried {name} to a circular library whose shelves touched the stars.",
                "text_below_en": "In the center, on a carved wooden lectern, rested a blank book with a golden title: 'The Chronicles of {name}.'",
                "scene_template": """Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, awed reverent expression, eyes wide looking up at the infinite shelves. A normal human body, two arms, two legs, smooth skin. OUTFIT: Cream medieval-style tunic with brown pants and leather boots. ACTION: The {gender_word} stands ALONE inside the library before a carved wooden lectern, {hair_action}, both {skin_tone} hands touching an open blank book that glows with soft golden light. Looking up in wonder. SETTING: Magnificent circular library with no ceiling WIDE VIEW, bookshelves spiral upward and fade into a beautiful starry night sky, thousands of colorful books, warm candlelight mixed with starlight, carved wooden lectern in center. ATMOSPHERE: Sacred wisdom, cosmic knowledge, wonder at infinite stories, warm candlelight glow. STRICT: Only ONE {gender_word}, NO other children, NO other people, NO duplicates. The {gender_word} is completely alone in the library. {style}"""
            },
            {
                "text_above_es": "{name} tomó una pluma y escribió con cuidado: «la curiosidad es la llave que abre todas las puertas».",
                "text_below_es": "Una lluvia de estrellas de papel cayó del cielo, cada una con una palabra nueva y fascinante para aprender.",
                "text_above_en": "{name} took a quill and carefully wrote: 'curiosity is the key that opens all doors.'",
                "text_below_en": "A rain of paper stars fell from the sky, each one with a new and fascinating word to learn.",
                "scene_template": """Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, peaceful content smile, eyes bright with satisfaction. A normal human body, two arms, two legs, smooth skin. OUTFIT: Cream medieval-style tunic with brown pants and leather boots. ACTION: The {gender_word} writes with a golden quill in the open glowing book on the lectern, {hair_action}, one {skin_tone} hand holding the quill writing golden words. Paper stars with glowing words fall gently from the sky like snow all around. SETTING: Circular library WIDE VIEW, bookshelves reaching to starry sky, paper stars drifting down everywhere, the book glows brightly as words appear, candlelight and starlight. ATMOSPHERE: Magical moment of creation, golden words, wisdom, paper stars falling like gentle snow, warm wonder. STRICT: Only ONE {gender_word}. {style}"""
            },
            {
                "text_above_es": "Al ponerse el sol, {name} apareció de nuevo en su jardín, justo bajo el arbusto de lavanda. Guardó la llave de cristal en su bolsillo.",
                "text_below_es": "Sabía que cada vez que abriera un libro, una nueva aventura estaría esperando a solo una página de distancia.",
                "text_above_en": "When the sun set, {name} appeared again in the garden, right under the lavender bush. The crystal key went safely into a pocket.",
                "text_below_en": "Knowing that every time a book is opened, a new adventure waits just a page away.",
                "scene_template": """Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, peaceful knowing smile, warm contented expression. A normal human body, two arms, two legs, smooth skin. OUTFIT: Cream medieval-style tunic with brown pants and leather boots, a subtle glow from the pocket where the crystal key rests. ACTION: The {gender_word} sits peacefully under the lavender bush in the garden at sunset, {hair_action}, one {skin_tone} hand resting on the pocket that glows with the crystal key inside, looking up at the warm sunset sky. SETTING: The same enchanted garden from scene 1 WIDE VIEW, lavender flowers, ancient gnarled trees, warm sunset sky with orange pink and gold, the small ivy-covered door barely visible in the background, golden afternoon light. ATMOSPHERE: Return home, peaceful wisdom, warm sunset glow, quiet magic within, adventure complete. STRICT: Only ONE {gender_word}. {style}"""
            }
        ],
        "closing_template": """Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, curious confident smile looking directly at the viewer with sparkling eyes. A normal human body, two arms, two legs, smooth skin. OUTFIT: Cream medieval-style tunic with brown pants and leather boots. ACTION: The {gender_word} stands alone in the enchanted garden, {hair_action}, one {skin_tone} hand holding up the glowing crystal key. SETTING: Ancient enchanted garden at golden hour WIDE VIEW, lavender flowers, gnarled trees, warm golden light. ATMOSPHERE: Curiosity, adventure, magical wisdom. STRICT: Only ONE {gender_word}. {style}""",
        "closing_message_es": "{name}, la curiosidad es la llave que abre todas las puertas del mundo.",
        "closing_message_en": "{name}, curiosity is the key that opens all the doors in the world."
    },
    "sunset_map": {
        "title_es": "{name} y el mapa que solo aparecía al atardecer",
        "title_en": "{name} and the Map That Only Appeared at Sunset",
        "age_range": "5-7",
        "text_layout": "split",
        "use_preview_as_cover": True,
        "preview_prompt_override": """Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, curious adventurous expression. A normal human body, two arms, two legs, smooth skin. OUTFIT: Lightweight copper and amber toned vest with many secret pockets over a cream shirt, sturdy brown leather boots, and a magical shimmering scarf in warm sunset colors around the neck. ACTION: The {gender_word} stands holding an ancient glowing parchment map, {hair_action}, examining mysterious symbols with wonder. SETTING: Beautiful sunset sky WIDE VIEW, orange pink and purple colors, ancient stone path. ATMOSPHERE: Adventure, warm sunset glow, magical sparkles from the map. STRICT: Only ONE {gender_word}. {style}""",
        "cover_template": """Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, excited wondering expression looking at a glowing map. A normal human body, two arms, two legs, smooth skin. OUTFIT: Copper and amber toned vest with secret pockets over a cream shirt, brown leather boots, magical sunset-colored scarf around neck. ACTION: The {gender_word} holds up an ancient parchment map glowing with golden invisible ink, {hair_action}, both {skin_tone} hands holding the map, eyes examining the mysterious symbols. SETTING: Breathtaking sunset sky WIDE VIEW with orange pink and purple colors, ancient stone path leading into a mysterious forest, golden sparkles from the map. ATMOSPHERE: Discovery, adventure beginning, warm sunset light, centered composition for book cover. STRICT: Only ONE {gender_word}. {style}""",
        "pages": [
            {
                "text_above_es": "{name} encontró el mapa una tarde en la que el cielo cambiaba de color. Estaba dibujado con tinta invisible sobre una hoja antigua.",
                "text_below_es": "Solo aparecía cuando el sol comenzaba a caer. Al tocarlo, reveló caminos, símbolos y una promesa: un tesoro que no cualquiera podía encontrar.",
                "text_above_en": "{name} found the map one afternoon when the sky was changing color. It was drawn with invisible ink on an ancient leaf.",
                "text_below_en": "It only appeared when the sun began to set. Upon touching it, the map revealed paths, symbols, and a promise: a treasure not just anyone could find.",
                "scene_template": """Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, wide-eyed amazement, mouth slightly open in wonder. A normal human body, two arms, two legs, smooth skin. OUTFIT: Comfortable casual clothes, shirt and pants. ACTION: The {gender_word} kneels on grass in a garden at sunset, {hair_action}, both {skin_tone} hands holding an old parchment that begins to glow with golden invisible ink revealing a mysterious map with paths and symbols. SETTING: Garden at sunset WIDE VIEW, breathtaking sky transitioning from orange to pink to purple, ancient trees framing the scene, golden light. ATMOSPHERE: Magical discovery, warm sunset light, golden sparkles emanating from the map. STRICT: Only ONE {gender_word}. {style}"""
            },
            {
                "text_above_es": "{name} se colocó el traje del explorador del ocaso: un chaleco de tonos cobrizos con bolsillos secretos, botas resistentes y una bufanda mágica.",
                "text_below_es": "El traje no daba fuerza extra, pero ayudaba a observar mejor. Así comenzó la búsqueda, con misterio en el aire y curiosidad en cada paso.",
                "text_above_en": "{name} put on the sunset explorer outfit: a copper-toned vest with secret pockets, sturdy boots, and a magical scarf.",
                "text_below_en": "The outfit didn't give extra strength, but helped observe better. Thus began the search, with mystery in the air and curiosity in every step.",
                "scene_template": """Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, confident determined expression, ready for adventure. A normal human body, two arms, two legs, smooth skin. OUTFIT: Lightweight copper and amber toned vest with many secret pockets over a cream shirt, sturdy brown leather boots, magical shimmering scarf in warm sunset colors wrapping around neck and glowing softly. ACTION: The {gender_word} stands at the beginning of an ancient stone path, {hair_action}, one {skin_tone} hand holding the glowing map, the other hand adjusting the magical scarf. The scarf begins to shimmer. SETTING: Edge of a mysterious forest at sunset WIDE VIEW, ancient stone path leading into golden-lit trees, warm sunset sky with orange and amber colors, magical golden sparkles. ATMOSPHERE: Adventure beginning, brave explorer, warm sunset glow, magical anticipation. STRICT: Only ONE {gender_word}. {style}"""
            },
            {
                "text_above_es": "El mapa cambiaba según las decisiones de {name}. Cuando dudaba, los caminos se movían. Cuando confiaba, se aclaraban.",
                "text_below_es": "La bufanda brillaba suavemente cuando iba en la dirección correcta. El misterio hacía sonreír más que asustar.",
                "text_above_en": "The map changed according to {name}'s decisions. When there was doubt, the paths moved. When there was trust, they became clear.",
                "text_below_en": "The scarf glowed softly when going in the right direction. The mystery made one smile more than fear.",
                "scene_template": """Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, focused thoughtful expression, concentrating carefully. A normal human body, two arms, two legs, smooth skin. OUTFIT: Copper and amber toned vest with secret pockets over cream shirt, brown leather boots, magical sunset scarf GLOWING BRIGHTLY with golden light indicating the right direction. ACTION: The {gender_word} stands at a crossroads of ancient stone paths in a mystical forest, {hair_action}, both {skin_tone} hands holding the glowing map open, studying it with concentration. The paths ahead shimmer and shift magically. SETTING: Mystical forest crossroads WIDE VIEW, ancient stone pillars with carved symbols, floating glowing runes in the air, warm sunset light filtering through tall trees. ATMOSPHERE: Puzzle-solving, intuition, magical mystery, warm amber light, golden sparkles. STRICT: Only ONE {gender_word}. {style}"""
            },
            {
                "text_above_es": "{name} resolvió acertijos e interpretó símbolos antiguos grabados en las piedras del camino.",
                "text_below_es": "Aprendió que la verdadera dificultad no era encontrar el tesoro, sino entender el mapa. Cada prueba exigía pensar, no correr.",
                "text_above_en": "{name} solved riddles and interpreted ancient symbols carved into the stones along the path.",
                "text_below_en": "Learning that the real difficulty wasn't finding the treasure, but understanding the map. Each test required thinking, not running.",
                "scene_template": """Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, clever happy expression, eyes bright with understanding. A normal human body, two arms, two legs, smooth skin. OUTFIT: Copper and amber toned vest with secret pockets over cream shirt, brown leather boots, magical sunset scarf glowing softly. ACTION: The {gender_word} traces ancient symbols carved into a tall stone pillar with one {skin_tone} finger, {hair_action}, the other hand holding the map for reference. The symbols glow golden as the {gender_word} touches them. SETTING: Ancient stone ruins in the forest WIDE VIEW, tall carved stone pillars with mysterious symbols, warm sunset light creating long golden shadows, moss-covered stones, magical atmosphere. ATMOSPHERE: Discovery, ancient wisdom, intellectual adventure, warm golden ruins. STRICT: Only ONE {gender_word}. {style}"""
            },
            {
                "text_above_es": "Al final, el tesoro no fue oro ni joyas, sino una caja luminosa que guardaba recuerdos de quienes habían llegado antes.",
                "text_below_es": "Al abrirla, {name} comprendió que el mapa solo aparecía a quienes estaban list{o_a}s para confiar en su intuición.",
                "text_above_en": "In the end, the treasure wasn't gold or jewels, but a luminous box that held memories of those who arrived before.",
                "text_below_en": "Opening it, {name} understood that the map only appeared to those ready to trust their intuition.",
                "scene_template": """Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, peaceful awed expression, eyes glowing with understanding. A normal human body, two arms, two legs, smooth skin. OUTFIT: Copper and amber toned vest with secret pockets over cream shirt, brown leather boots, magical sunset scarf. ACTION: The {gender_word} kneels before a beautiful glowing treasure chest made of crystal and gold, {hair_action}, both {skin_tone} hands gently opening the lid. Soft golden light from inside reveals floating memory orbs showing silhouettes of previous explorers. SETTING: Ancient clearing surrounded by mystical standing stones WIDE VIEW, warm sunset light bathing everything in golden and amber hues, memory orbs floating around. ATMOSPHERE: Wisdom, peaceful discovery, golden treasure light, floating memories, wonder. STRICT: Only ONE {gender_word}. {style}"""
            },
            {
                "text_above_es": "El traje del explorador del ocaso se guardó, listo para futuras aventuras. Pero la lección permaneció para siempre.",
                "text_below_es": "Algunos tesoros no se miden por lo que valen, sino por lo que enseñan.",
                "text_above_en": "The sunset explorer outfit was put away, ready for future adventures. But the lesson remained forever.",
                "text_below_en": "Some treasures aren't measured by what they're worth, but by what they teach.",
                "scene_template": """Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, content knowing smile, warm peaceful expression. A normal human body, two arms, two legs, smooth skin. OUTFIT: Simple comfortable casual clothes, shirt and pants, barefoot on the grass. ACTION: The {gender_word} sits on a grassy hill at sunset, {hair_action}, one {skin_tone} hand resting on the folded explorer outfit beside, looking at the magnificent sunset sky with a knowing peaceful smile. The map sits folded on top of the outfit, no longer glowing. SETTING: Beautiful grassy hilltop at sunset WIDE VIEW, breathtaking sky with orange, pink, purple and gold, rolling hills and forests visible in the distance, warm golden light. ATMOSPHERE: Peaceful ending, wisdom gained, warm sunset farewell, adventure complete, quiet contentment. STRICT: Only ONE {gender_word}. {style}"""
            },
            {
                "text_above_es": "Y el mapa, aunque invisible la mayor parte del tiempo, sigue esperando el próximo atardecer.",
                "text_below_es": "Porque {name} sabe que siempre habrá nuevos caminos por descubrir.",
                "text_above_en": "And the map, though invisible most of the time, continues waiting for the next sunset.",
                "text_below_en": "Because {name} knows there will always be new paths to discover.",
                "scene_template": """Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, hopeful dreamy expression looking at the horizon, soft smile. A normal human body, two arms, two legs, smooth skin. OUTFIT: Comfortable casual clothes, standing relaxed. ACTION: The {gender_word} stands at a window at home watching the sunset, {hair_action}, one {skin_tone} hand pressed against the window glass. On the windowsill, the ancient folded map starts to glow faintly with golden light as the sun sets. SETTING: Cozy home interior WIDE VIEW, large window showing a magnificent sunset outside, warm interior lamp light, the magical scarf and vest hanging on a hook nearby, books on shelves. ATMOSPHERE: Promise of future adventures, sunset magic, warm glow, quiet anticipation, the map awakening. STRICT: Only ONE {gender_word}. {style}"""
            }
        ],
        "closing_template": """Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, confident adventurous smile looking directly at the viewer. A normal human body, two arms, two legs, smooth skin. OUTFIT: Copper and amber toned vest with secret pockets over cream shirt, brown leather boots, magical sunset scarf. ACTION: The {gender_word} stands alone on a hilltop at sunset, {hair_action}, one {skin_tone} hand holding the glowing map, scarf flowing in the breeze. SETTING: Beautiful hilltop at sunset WIDE VIEW, orange pink and gold sky, rolling hills. ATMOSPHERE: Adventure, confidence, warm sunset light, magical sparkles. STRICT: Only ONE {gender_word}. {style}""",
        "closing_message_es": "{name}, los mejores tesoros son los que se descubren confiando en tu propio corazón.",
        "closing_message_en": "{name}, the best treasures are the ones discovered by trusting your own heart."
    },
    "star_guardian": {
        "title_es": "{name} y el guardián de las estrellas",
        "title_en": "{name} and the Guardian of the Stars",
        "age_range": "5-7",
        "text_layout": "split",
        "use_preview_as_cover": True,
        "preview_prompt_override": """Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, brave determined expression with gentle eyes. A normal human body, two arms, two legs, smooth skin. OUTFIT: Midnight blue flowing cape adorned with glowing silver constellation patterns, elegant silver tunic, soft dark velvet boots, and a shimmering star-shaped medallion glowing golden on the chest. ACTION: The {gender_word} stands confidently on a hilltop, {hair_action}, cape flowing in the wind, one {skin_tone} hand touching the glowing medallion. SETTING: Magnificent starry night sky WIDE VIEW, thousands of stars visible, rolling hills, magical silver sparkles. ATMOSPHERE: Mystical night, cosmic wonder, heroic guardian moment. STRICT: Only ONE {gender_word}. The {gender_word} is 100% human, two arms, two legs, smooth {skin_tone} skin, normal child anatomy. {style}""",
        "cover_template": """Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, brave wondering expression looking up. A normal human body, two arms, two legs, smooth skin. OUTFIT: Midnight blue flowing cape with glowing silver constellation patterns, elegant silver tunic, dark velvet boots, shimmering golden star-shaped medallion on chest. ACTION: The {gender_word} stands on a hilltop, arms slightly raised, {hair_action}, as glowing fallen stars float gently around. The medallion pulses with golden light. SETTING: Breathtaking starry night sky WIDE VIEW, Milky Way visible, rolling hills below, magical silver and gold sparkles everywhere. ATMOSPHERE: Mystical nighttime wonder, cosmic magic, centered composition for book cover. STRICT: Only ONE {gender_word}. {style}""",
        "pages": [
            {
                "text_above_es": "Aquella noche, el cielo estaba extrañamente oscuro. Las estrellas habían comenzado a caer, una a una, como lágrimas de luz.",
                "text_below_es": "Nadie parecía notarlo. Pero {name} sí lo vio. Una voz suave llegó desde el viento: «Solo quienes miran con el corazón pueden ser guardianes».",
                "text_above_en": "That night, the sky was strangely dark. The stars had begun to fall, one by one, like tears of light.",
                "text_below_en": "No one seemed to notice. But {name} saw it. A soft voice came from the wind: 'Only those who look with their heart can be guardians.'",
                "scene_template": """Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, wide-eyed wonder, mouth slightly open in awe. A normal human body, two arms, two legs, smooth skin. OUTFIT: Simple comfortable pajamas, barefoot on the grass. ACTION: The {gender_word} stands on a grassy hilltop at night, {hair_action}, looking up at the sky with pure amazement, one {skin_tone} hand reaching up toward falling stars. Dozens of glowing stars fall like tears of light across the dark sky. SETTING: Vast nighttime hilltop WIDE VIEW, expansive dark sky above with stars falling slowly, rolling green hills below, a cozy house with warm lit windows visible in the distance. ATMOSPHERE: Magical awe, mystical night, silver starlight, sense of cosmic wonder. STRICT: Only ONE {gender_word}. {style}"""
            },
            {
                "text_above_es": "Una capa azul oscuro apareció sobre los hombros de {name}, bordada con constelaciones que brillaban suavemente.",
                "text_below_es": "Una túnica plateada, botas de terciopelo y un medallón en forma de estrella completaron el traje del guardián celestial.",
                "text_above_en": "A dark blue cape appeared over {name}'s shoulders, embroidered with constellations that glowed softly.",
                "text_below_en": "A silver tunic, velvet boots, and a star-shaped medallion completed the celestial guardian outfit.",
                "scene_template": """Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, amazed delighted expression looking down at the new outfit. A normal human body, two arms, two legs, smooth skin. OUTFIT: Midnight blue flowing cape with glowing silver constellation patterns materializing around shoulders, elegant silver tunic, dark velvet boots, golden star-shaped medallion forming on chest and radiating warm light. ACTION: The {gender_word} stands on the hilltop, {hair_action}, looking down at the glowing medallion forming on chest with wonder, both {skin_tone} hands slightly raised as the magical cape wraps around shoulders. Silver sparkles swirl around as the transformation happens. SETTING: Nighttime hilltop WIDE VIEW, starry sky, fallen stars glowing on the meadow grass, moonlight. ATMOSPHERE: Magical transformation, silver and gold sparkles, cosmic destiny, mystical wonder. STRICT: Only ONE {gender_word}. {style}"""
            },
            {
                "text_above_es": "El medallón latía como un segundo corazón, indicando dónde habían caído las estrellas. {name} recogió la primera con delicadeza.",
                "text_below_es": "La estrella brillaba cálida en sus manos. El cielo pareció suspirar de alivio. La misión había comenzado.",
                "text_above_en": "The medallion beat like a second heart, showing where the stars had fallen. {name} picked up the first one gently.",
                "text_below_en": "The star glowed warm in those hands. The sky seemed to sigh with relief. The mission had begun.",
                "scene_template": """Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, gentle caring expression, soft smile. A normal human body, two arms, two legs, smooth skin. OUTFIT: Midnight blue cape with silver constellation patterns, silver tunic, dark velvet boots, golden star medallion glowing on chest. ACTION: The {gender_word} kneels on the grass, {hair_action}, both {skin_tone} hands gently cupping a small glowing fallen star with extreme tenderness. The cape pools around the kneeling figure. The medallion on chest pulses brighter in response. SETTING: Vast nighttime meadow WIDE VIEW, more fallen stars scattered across the grass glowing softly, rolling hills, full moon above. ATMOSPHERE: Tender delicate moment, warm golden glow from the star, silver moonlight, sense of sacred mission. STRICT: Only ONE {gender_word}. {style}"""
            },
            {
                "text_above_es": "{name} caminó por paisajes que solo existen cuando la luna está alta. Cruzó un puente hecho de rayos de luna sobre un río de sueños.",
                "text_below_es": "Las luciérnagas formaban caminos de luz entre árboles que susurraban historias antiguas.",
                "text_above_en": "{name} walked through landscapes that only exist when the moon is high. Crossed a bridge made of moonbeams over a river of dreams.",
                "text_below_en": "Fireflies formed paths of light between trees that whispered ancient stories.",
                "scene_template": """Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, brave adventurous expression, determined smile. A normal human body, two arms, two legs, smooth skin. OUTFIT: Midnight blue cape with silver constellation patterns flowing behind, silver tunic, dark velvet boots, golden star medallion on chest. ACTION: The {gender_word} walks forward on a luminous bridge made of pure moonbeams, {hair_action}, {skin_tone} arms outstretched for balance, cape flowing dramatically behind. SETTING: Expansive magical moonlit landscape WIDE VIEW, the moonbeam bridge arches over a winding silver river, ancient towering trees with glowing bark on both sides, thousands of fireflies creating rivers of golden light, full moon illuminating everything. ATMOSPHERE: Epic adventure, silver and blue magical tones, enchanted forest, cosmic journey. STRICT: Only ONE {gender_word}. {style}"""
            },
            {
                "text_above_es": "Las estrellas caídas simplemente esperaban. Una brillaba entre flores nocturnas, otra flotaba sobre un estanque plateado.",
                "text_below_es": "La más pequeña temblaba en las manos de un búho sabio que la había protegido. El medallón brillaba más fuerte con cada estrella recuperada.",
                "text_above_en": "The fallen stars were simply waiting. One shone among night flowers, another floated over a silver pond.",
                "text_below_en": "The smallest one trembled in the hands of a wise owl who had protected it. The medallion glowed brighter with each star recovered.",
                "scene_template": """Disney Pixar 3D style illustration. CHARACTER 1: The human {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, gentle grateful expression. A normal human body, two arms, two legs, smooth skin. OUTFIT: Midnight blue cape with silver constellation patterns, silver tunic, dark velvet boots, golden star medallion on chest glowing brightly. CHARACTER 2: A wise old owl with soft brown and white feathers, large round golden eyes, perched on a low branch, gently holding a tiny glowing star in its talons. ACTION: The {gender_word} stands on the LEFT, {hair_action}, both {skin_tone} hands gently extended to receive the tiny star from the owl. The owl on the RIGHT offers the star from its branch. The medallion glows intensely. SETTING: Enchanted moonlit clearing WIDE VIEW, night flowers glowing softly on the ground, silver pond reflecting moonlight nearby, ancient trees surrounding, fireflies. ATMOSPHERE: Gentle exchange, trust, sacred moment, warm starlight mixed with cool moonlight. COMPOSITION: The {gender_word} on the LEFT; the wise owl on a branch on the RIGHT. Clear physical separation. {style}"""
            },
            {
                "text_above_es": "Cuando el horizonte comenzó a teñirse de rosa, {name} levantó las manos hacia el cielo. Las estrellas ascendieron como una lluvia invertida.",
                "text_below_es": "Regresaron a sus lugares entre las constelaciones. El cielo volvió a brillar con toda su magia.",
                "text_above_en": "When the horizon began to turn pink, {name} raised hands toward the sky. The stars rose like an inverted rain.",
                "text_below_en": "They returned to their places among the constellations. The sky shone again with all its magic.",
                "scene_template": """Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, powerful joyful expression with eyes sparkling, triumphant smile. A normal human body, two arms, two legs, smooth skin. OUTFIT: Midnight blue cape with silver constellations blazing bright, silver tunic, dark velvet boots, golden star medallion radiating intense light. ACTION: The {gender_word} stands on the highest hilltop, {hair_action}, both {skin_tone} arms raised toward the sky, palms open. Hundreds of glowing stars stream UPWARD from the medallion and hands like an inverted rain of light, returning to the sky. The cape billows dramatically. SETTING: Breathtaking dawn hilltop WIDE VIEW, sky transitioning from deep blue to soft pink and gold, constellations reforming brilliantly above, rolling hills and meadows below. ATMOSPHERE: Epic climax moment, cosmic restoration, brilliant light streaming upward, triumphant wonder. STRICT: Only ONE {gender_word}. {style}"""
            },
            {
                "text_above_es": "El traje del guardián se desvaneció, pero el medallón permaneció invisible dentro del corazón de {name}.",
                "text_below_es": "Desde esa noche, {name} sabe que mirar hacia arriba con ojos de asombro es el mayor regalo que podemos darle al universo.",
                "text_above_en": "The guardian outfit faded, but the medallion remained invisible inside {name}'s heart.",
                "text_below_en": "From that night on, {name} knows that looking up with eyes of wonder is the greatest gift we can give to the universe.",
                "scene_template": """Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, peaceful serene smile, eyes looking up at the stars with quiet wonder. A normal human body, two arms, two legs, smooth skin. OUTFIT: Simple comfortable pajamas, cozy and soft. ACTION: The {gender_word} stands at a bedroom window at night, {hair_action}, one {skin_tone} hand placed gently over heart where a subtle golden glow shines through the pajamas. Looking up at the now-brilliant starry sky through the open window. SETTING: Cozy child bedroom at night WIDE VIEW, window open to a magnificent starry sky with all constellations shining brightly, moonlight streaming in, plush toys and books on shelves, warm bedside lamp. ATMOSPHERE: Inner peace, hidden guardian power, warm golden glow from heart, starry wonder, quiet magic within. STRICT: Only ONE {gender_word}. {style}"""
            }
        ],
        "closing_template": """Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, peaceful proud smile looking directly at the viewer with sparkling eyes. A normal human body, two arms, two legs, smooth skin. OUTFIT: Midnight blue cape with glowing silver constellation patterns, silver tunic, golden star medallion on chest glowing warmly. ACTION: The {gender_word} stands alone on a hilltop under a magnificent starry sky, {hair_action}, one {skin_tone} hand placed over the glowing medallion on chest. SETTING: Beautiful hilltop at night WIDE VIEW, thousands of stars and constellations blazing brilliantly above, full moon, rolling hills below. ATMOSPHERE: Triumphant guardian moment, cosmic wonder, silver and gold light, inner strength. STRICT: Only ONE {gender_word}. {style}""",
        "closing_message_es": "{name}, mientras mires las estrellas con asombro, el cielo nunca estará vacío.",
        "closing_message_en": "{name}, as long as you look at the stars with wonder, the sky will never be empty."
    },
    "superhero_light": {
        "title_es": "{name} superhéroe de la luz",
        "title_en": "{name} Superhero of Light",
        "age_range": "3-5",
        "text_layout": "split",
        "use_preview_as_cover": True,
        "preview_prompt_override": """Disney Pixar 3D style illustration. CHARACTER: A single small {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, calm confident smile, peaceful expression. A normal human body, two arms, two legs, smooth skin. OUTFIT: Deep blue full-body superhero suit with long fitted pants, shimmering golden star patterns, golden boots, a short flowing cape moving gently, and a round glowing golden star symbol on the chest. ACTION: The {gender_word} stands confidently in the LOWER HALF of the image with {skin_tone} hands slightly open at sides, {hair_action}, surrounded by soft magical golden light. SETTING: EXTREME WIDE VIEW, beautiful expansive park at golden hour, vast open green field stretching far, many tall green trees in the distance, dramatic warm sunset sky filling the UPPER HALF of the image with pink and orange clouds, golden sparkles floating in the air. ATMOSPHERE: Peaceful heroic moment, warm golden sparkles floating around, soft magical glow, LOTS OF SKY AND SPACE ABOVE the {gender_word}. STRICT: Only ONE {gender_word}. The {gender_word} is 100% human, two arms, two legs, smooth {skin_tone} skin, normal child anatomy. NO skirt, NO dress. The {gender_word} must be SMALL in the frame, occupying only the BOTTOM THIRD of the image, with expansive sky and scenery above. {style}""",
        "cover_template": """Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, warm confident smile. A normal human body, two arms, two legs, smooth skin. OUTFIT: Deep blue full-body superhero suit with long fitted pants, shimmering golden star patterns, golden boots, a short flowing cape moving gently in the breeze, and a round glowing golden star symbol on the chest. ACTION: The {gender_word} stands on a small green hill with arms slightly open, {hair_action}, golden light radiating from the star on chest. SETTING: Beautiful sunset sky with pink and orange clouds WIDE VIEW, green rolling hills, golden sparkles in the air. ATMOSPHERE: Peaceful heroic moment, warm golden light, magical sparkles, centered composition for book cover. STRICT: Only ONE {gender_word}. The {gender_word} is 100% human, two arms, two legs, smooth {skin_tone} skin, normal child anatomy. NO skirt, NO dress. {style}""",
        "pages": [
            {
                "text_above_es": "{name} tenía algo especial: sabía escuchar con atención y sentir con el corazón. Era diferente a los demás, aunque nadie lo notaba.",
                "text_below_es": "Una tarde, mientras jugaba tranquilamente en el jardín, una luz suave y dorada apareció a su alrededor. Algo mágico estaba por ocurrir.",
                "text_above_en": "{name} had something special: knowing how to listen carefully and feel with the heart. Different from everyone else, though no one noticed.",
                "text_below_en": "One afternoon, while playing peacefully in the garden, a soft golden light appeared all around. Something magical was about to happen.",
                "scene_template": """Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, curious surprised expression with wide eyes and a forming smile. A normal human body, two arms, two legs, smooth skin. OUTFIT: Simple casual t-shirt and comfortable shorts, everyday clothes. ACTION: The {gender_word} kneels on green grass in a garden, {hair_action}, looking up with wonder as golden sparkles begin floating around. Both {skin_tone} hands reach up toward the magical light. SETTING: Beautiful backyard garden WIDE VIEW, colorful flowers, butterflies, green lawn, garden fence, trees in background, bright sunny afternoon. ATMOSPHERE: Magical discovery moment, soft golden sparkles appearing everywhere, warm sunlight, sense of wonder. STRICT: Only ONE {gender_word}. {style}"""
            },
            {
                "text_above_es": "La luz se transformó poco a poco en un traje especial. Era cómodo y ligero, de color azul profundo con detalles dorados que brillaban sin deslumbrar.",
                "text_below_es": "Tenía una capa corta que se movía despacio, como si respirara. En el pecho, una estrella redonda cambiaba de color según cómo se sentía {name}.",
                "text_above_en": "The light slowly transformed into a special suit. It was comfortable and light, deep blue with golden details that glowed gently.",
                "text_below_en": "It had a short cape that moved slowly, as if breathing. On the chest, a round star changed color according to how {name} felt.",
                "scene_template": """Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, amazed delighted smile looking down at the new suit. A normal human body, two arms, two legs, smooth skin. OUTFIT: Deep blue full-body superhero suit with long fitted pants, shimmering golden star patterns, golden boots, a short flowing cape moving gently, and a round glowing golden star symbol on the chest radiating warm light. ACTION: The {gender_word} stands in the garden, {hair_action}, looking down at the glowing star on chest with wonder, both {skin_tone} hands held slightly out at sides. The cape floats gently behind. Golden magical sparkles swirl around. SETTING: Beautiful garden WIDE VIEW, green grass, colorful flowers, trees, warm afternoon sunlight. ATMOSPHERE: Magical transformation moment, golden light radiating from the star, sparkles everywhere, sense of becoming something special. STRICT: Only ONE {gender_word}. NO skirt, NO dress. {style}"""
            },
            {
                "text_above_es": "Al ponerse el traje, {name} sintió calma y confianza. Así nació {el_la} superhéroe de la luz tranquila.",
                "text_below_es": "Caminó despacio por el vecindario, observando y escuchando todo con atención. La estrella brillaba suavemente con cada paso.",
                "text_above_en": "Wearing the suit, {name} felt calm and confidence. Thus was born the superhero of quiet light.",
                "text_below_en": "Walking slowly through the neighborhood, observing and listening to everything carefully. The star glowed softly with every step.",
                "scene_template": """Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, calm serene confident expression, peaceful smile. A normal human body, two arms, two legs, smooth skin. OUTFIT: Deep blue full-body superhero suit with long fitted pants, shimmering golden star patterns, golden boots, short flowing cape, round glowing golden star on chest. ACTION: The {gender_word} walks calmly along a tree-lined neighborhood sidewalk, {hair_action}, cape flowing gently behind. The star on chest pulses with soft golden light. One {skin_tone} hand touches the star gently. SETTING: Beautiful quiet neighborhood street WIDE VIEW, colorful houses, green trees lining the sidewalk, warm afternoon light, birds perched on branches. ATMOSPHERE: Peaceful confidence, soft golden glow from the star, calm magical energy, warm sunlight. STRICT: Only ONE {gender_word}. NO skirt, NO dress. {style}"""
            },
            {
                "text_above_es": "Cuando alguien estaba triste, la estrella del pecho brillaba suave y transmitía tranquilidad. {name} se acercó a alguien que lloraba en el parque.",
                "text_below_es": "La luz dorada envolvió a ese alguien en una ola de calma. Poco a poco dejó de llorar y sonrió. Ayudar era el verdadero poder.",
                "text_above_en": "When someone was sad, the star on the chest glowed softly and sent waves of peace. {name} approached someone crying in the park.",
                "text_below_en": "The golden light wrapped them in a wave of calm. Little by little the tears stopped and a smile appeared. Helping was the true power.",
                "scene_template": """Disney Pixar 3D style illustration. CHARACTER 1: The human {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, gentle caring expression. A normal human body, two arms, two legs, smooth skin. OUTFIT: Deep blue full-body superhero suit with long fitted pants, golden star patterns, golden boots, short cape, glowing golden star on chest sending warm golden light rays outward. CHARACTER 2: A smaller child sitting on the grass, different appearance from CHARACTER 1, tears on cheeks but beginning to smile, wearing simple everyday clothes. ACTION: The {gender_word} kneels on the LEFT beside the smaller child on the RIGHT, one {skin_tone} hand extended gently. Golden warm light rays flow from the star on chest toward the smaller child. The cape extends slightly. SETTING: Beautiful park WIDE VIEW, green grass, playground visible in background, trees, park benches, bright afternoon. ATMOSPHERE: Warm healing moment, golden light spreading, gentle care, emotional connection. COMPOSITION: The {gender_word} is on the LEFT comforting the smaller child on the RIGHT. Clear physical separation between them. STRICT: NO skirt, NO dress on the superhero. {style}"""
            },
            {
                "text_above_es": "Cuando alguien tenía miedo, la capa envolvía el aire como un abrazo invisible. Esa noche, alguien pequeño temblaba bajo un árbol.",
                "text_below_es": "La capa de {name} se extendió suavemente y lo envolvió como una manta de luz cálida. Dejó de temblar y se sintió protegid{o_a}.",
                "text_above_en": "When someone was scared, the cape wrapped the air like an invisible hug. That night, a small child trembled under a tree.",
                "text_below_en": "{name}'s cape extended softly and wrapped them like a blanket of warm light. The trembling stopped and they felt safe.",
                "scene_template": """Disney Pixar 3D style illustration. CHARACTER 1: The human {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, protective caring expression. A normal human body, two arms, two legs, smooth skin. OUTFIT: Deep blue full-body superhero suit with long fitted pants, golden star patterns, golden boots, star on chest glowing brightly, cape EXTENDED wide like a glowing golden blanket of light. CHARACTER 2: A small scared child with different appearance, hugging their own knees, sitting under a large tree, wearing pajamas. ACTION: The {gender_word} stands on the LEFT with arms open wide, the glowing cape stretches toward the scared child on the RIGHT, wrapping around them like a warm protective blanket of golden light. SETTING: Evening park scene WIDE VIEW, large old tree, soft twilight sky with first stars appearing, fireflies glowing softly. ATMOSPHERE: Protective warmth, golden light from cape pushing away the shadows, safe and comforting. COMPOSITION: The superhero {gender_word} on LEFT with cape extending; the smaller child on RIGHT being wrapped in golden light. Clear physical separation. STRICT: NO skirt, NO dress on the superhero. {style}"""
            },
            {
                "text_above_es": "Cada vez que {name} usaba su poder, el traje se iluminaba un poquito más. Un día en la plaza, muchos necesitaban ayuda al mismo tiempo.",
                "text_below_es": "La estrella brilló con todos los colores del arcoíris. La luz se extendió por toda la plaza y todos sintieron paz y alegría.",
                "text_above_en": "Every time {name} used the power, the suit glowed a little brighter. One day in the square, many needed help at the same time.",
                "text_below_en": "The star shone with all the colors of the rainbow. The light spread across the entire square and everyone felt peace and joy.",
                "scene_template": """Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, powerful joyful expression with eyes closed and peaceful smile. A normal human body, two arms, two legs, smooth skin. OUTFIT: Deep blue full-body superhero suit with long fitted pants, golden star patterns glowing intensely, golden boots, cape spread wide and flowing, star on chest radiating brilliant RAINBOW colors outward in all directions. ACTION: The {gender_word} stands in the CENTER of a town square on a small fountain edge, arms raised with {skin_tone} palms open, {hair_action}. Rainbow light beams radiate outward from the star. The cape flows dramatically. Happy children and families visible in the background looking up with joy. SETTING: Beautiful town square WIDE VIEW, cobblestone ground, stone fountain, colorful buildings, trees, warm sunset sky. ATMOSPHERE: Epic climax moment, rainbow light filling the square, magical sparkles everywhere, joy and peace radiating. STRICT: Only ONE superhero {gender_word} in center. Background people are small and distant. NO skirt, NO dress. {style}"""
            },
            {
                "text_above_es": "Al terminar el día, {name} regresó a casa. La luz se desvaneció y el traje se guardó dentro de su corazón.",
                "text_below_es": "La estrella siguió brillando, aunque nadie pudiera verla. El verdadero poder de {name} estaba en la calma y el amor que llevaba dentro.",
                "text_above_en": "At the end of the day, {name} returned home. The light faded and the suit stored itself inside the heart.",
                "text_below_en": "The star kept glowing, though no one could see it. {name}'s true power was in the calm and love carried inside.",
                "scene_template": """Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, peaceful content sleepy smile with gentle eyes. A normal human body, two arms, two legs, smooth skin. OUTFIT: Soft cozy pajamas, comfortable bedtime clothes. ACTION: The {gender_word} lies tucked in a cozy bed under warm blankets, {hair_action}, both {skin_tone} hands placed gently over heart. A bright glowing golden STAR SYMBOL shines through the pajamas from within the heart, radiating warm golden light outward. SETTING: Cozy child bedroom at night WIDE VIEW, moonlight streaming through large window, plush toys on shelves, warm bedside lamp, stars visible outside window. ATMOSPHERE: Inner peace, hidden magic, warm golden glow from heart, peaceful bedtime, love within. STRICT: Only ONE {gender_word}. {style}"""
            }
        ],
        "closing_template": """Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, confident proud peaceful smile looking directly at the viewer. A normal human body, two arms, two legs, smooth skin. OUTFIT: Deep blue full-body superhero suit with long fitted pants, shimmering golden star patterns, golden boots, short flowing cape in the breeze, round glowing golden star on chest. ACTION: The {gender_word} stands alone on a hilltop at golden hour, one {skin_tone} hand placed over the glowing star on chest, {hair_action}. SETTING: Beautiful hilltop at golden sunset WIDE VIEW, pink and orange sky, green rolling hills below, warm light painting everything golden. ATMOSPHERE: Triumphant peaceful moment, warm golden light, magical sparkles, inner strength and confidence. STRICT: Only ONE {gender_word}. NO skirt, NO dress. {style}""",
        "closing_message_es": "{name}, tu verdadero superpoder es la calma y el amor que llevas dentro del corazón.",
        "closing_message_en": "{name}, your true superpower is the calm and love you carry inside your heart."
    },
    "dog_forever": {
        "title_es": "{name} y el perro que llegó para quedarse",
        "title_en": "{name} and the Dog Who Came to Stay",
        "age_range": "5-7",
        "text_layout": "split",
        "use_preview_as_cover": True,
        "preview_prompt_override": """Disney Pixar 3D style illustration. CHARACTER 1: The human {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, warm friendly smile. A normal human body, two arms, two legs, smooth skin. OUTFIT: Soft gray hoodie and blue jeans, comfortable casual clothes. CHARACTER 2: {dog_forever_desc}. ACTION: The {gender_word} stands relaxed in a park, {hair_action}, one {skin_tone} hand gently resting on Amigo's head. Amigo sits beside the {gender_word} looking up with gentle trusting eyes. SETTING: Beautiful green park WIDE VIEW, trees, grass, soft afternoon sunlight. ATMOSPHERE: Warm bond, gentle friendship, peaceful calm. COMPOSITION: The {gender_word} is a human child; Amigo is a separate real golden-brown dog. Clear physical separation. {style}""",
        "cover_template": """Disney Pixar 3D style illustration. CHARACTER 1: The human {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, warm gentle smile. A normal human body, two arms, two legs, smooth skin. OUTFIT: Soft gray hoodie and blue jeans. CHARACTER 2: {dog_forever_desc}, sitting calmly, looking up with gentle trusting dark brown eyes, tail wagging softly. ACTION: The {gender_word} sits on a wooden park bench on the LEFT. Amigo sits on the RIGHT side of the bench next to the child. SETTING: Beautiful neighborhood park WIDE VIEW, green trees, grass, soft golden afternoon sunlight, park path. ATMOSPHERE: Warm emotional bond, gentle friendship, peaceful afternoon, centered composition for book cover. COMPOSITION: The {gender_word} is a human child on the LEFT; Amigo the golden-brown dog sits separately on the RIGHT. Clear physical separation. {style}""",
        "pages": [
            {
                "text_above_es": "Un día {name} salió a pasear como hacía muchas otras veces. Caminaba despacio, mirando los árboles y todo lo que encontraba en el camino.",
                "text_below_es": "Cerca de un banco, vio a un perro que no conocía. Estaba solo, tranquilo, sentado, observando todo a su alrededor.",
                "text_above_en": "One day {name} went out for a walk, just like many other times. Walking slowly, looking at the trees and everything along the way.",
                "text_below_en": "Near a bench, there was a dog {name} didn't know. Alone, calm, sitting, watching everything around.",
                "scene_template": """Disney Pixar 3D style illustration. CHARACTER 1: The human {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, curious gentle expression. A normal human body, two arms, two legs, smooth skin. OUTFIT: Soft gray hoodie and blue jeans, comfortable sneakers. CHARACTER 2: {dog_forever_desc}, sitting calmly near a wooden park bench, looking toward the {gender_word} with gentle dark brown eyes, tail resting on the ground. ACTION: The {gender_word} walks along a park path on the LEFT, {hair_action}, slowing down and turning to look at the dog. Amigo the golden-brown dog sits quietly on the RIGHT near the bench, calm and peaceful. SETTING: Beautiful neighborhood park in the afternoon WIDE VIEW, wooden bench, green trees, grass, fallen leaves, soft warm sunlight. ATMOSPHERE: Quiet discovery, gentle curiosity, peaceful first encounter. COMPOSITION: The {gender_word} is on the LEFT approaching; Amigo the dog sits separately on the RIGHT. Clear physical separation between them. {style}"""
            },
            {
                "text_above_es": "Cuando {name} se acercó un poco más, el perro levantó la cabeza y movió la cola suavemente. No se alejó ni se asustó.",
                "text_below_es": "Simplemente se quedó ahí, esperando. Como si supiera que {name} iba a llegar.",
                "text_above_en": "When {name} got a little closer, the dog raised its head and wagged its tail gently. It didn't run away or get scared.",
                "text_below_en": "It simply stayed there, waiting. As if it knew {name} was going to come.",
                "scene_template": """Disney Pixar 3D style illustration. CHARACTER 1: The human {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, soft surprised smile, eyes showing tenderness. A normal human body, two arms, two legs, smooth skin. OUTFIT: Soft gray hoodie and blue jeans. CHARACTER 2: {dog_forever_desc}, sitting on the grass, head raised looking directly at the {gender_word}, fluffy tail wagging gently on the ground, big gentle dark brown eyes. ACTION: The {gender_word} kneels on the LEFT, {hair_action}, one {skin_tone} hand extended slowly and gently toward Amigo. Amigo sits on the RIGHT looking up with trusting eyes, tail wagging. SETTING: Park near a wooden bench WIDE VIEW, green grass, dappled sunlight through tree canopy, warm afternoon light. ATMOSPHERE: Tender first connection, trust forming, gentle emotional moment, warm light. COMPOSITION: The {gender_word} kneels on the LEFT; Amigo the golden-brown dog sits on the RIGHT. Clear physical separation. {style}"""
            },
            {
                "text_above_es": "{name} decidió llevar al perro a casa. El perro caminó a su lado, deteniéndose cuando {name} se detenía.",
                "text_below_es": "Al llegar, el perro exploró cada rincón con calma. {name} le puso agua fresca y algo de comida.",
                "text_above_en": "{name} decided to take the dog home. The dog walked alongside, stopping when {name} stopped.",
                "text_below_en": "Arriving home, the dog explored every corner calmly. {name} set out fresh water and some food.",
                "scene_template": """Disney Pixar 3D style illustration. CHARACTER 1: The human {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, happy caring expression. A normal human body, two arms, two legs, smooth skin. OUTFIT: Soft gray hoodie and blue jeans. CHARACTER 2: {dog_forever_desc}, standing near a water bowl, drinking water happily, tail wagging, looking content and relaxed. ACTION: The {gender_word} kneels on the LEFT beside a food bowl and water bowl on the floor, {hair_action}, both {skin_tone} hands setting the bowls down gently. Amigo stands on the RIGHT drinking from the water bowl. SETTING: Cozy home entrance and living room WIDE VIEW, warm interior lighting, comfortable couch with cushions, family photos on walls, soft rug on floor. ATMOSPHERE: Welcoming warmth, tender care, new home, gentle love. COMPOSITION: The {gender_word} is on the LEFT near the bowls; Amigo the golden-brown dog is on the RIGHT drinking. Clear physical separation. {style}"""
            },
            {
                "text_above_es": "{name} pensó en cómo llamarlo. Probó varios nombres en voz alta, escuchando con atención cada uno.",
                "text_below_es": "Cuando dijo uno en particular, el perro movió las orejas y lo miró fijamente. Ese sería su nombre.",
                "text_above_en": "{name} thought about what to call the dog. Trying several names out loud, listening carefully to each one.",
                "text_below_en": "When one particular name was said, the dog perked up its ears and looked directly. That would be the name.",
                "scene_template": """Disney Pixar 3D style illustration. CHARACTER 1: The human {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, joyful excited expression with mouth slightly open saying a name. A normal human body, two arms, two legs, smooth skin. OUTFIT: Soft gray hoodie and blue jeans. CHARACTER 2: {dog_forever_desc}, ears perked up high, head tilted to one side, big round dark brown eyes looking directly at the {gender_word} with recognition and excitement, tail wagging fast. ACTION: The {gender_word} sits cross-legged on the floor on the LEFT, {hair_action}, leaning forward with both {skin_tone} hands on knees, speaking a name. Amigo sits on the RIGHT on a soft rug, ears up, alert and attentive, recognizing his name. SETTING: Cozy living room WIDE VIEW, soft warm lamp light, comfortable cushions on floor, bookshelf in background, warm evening atmosphere. ATMOSPHERE: Magical naming moment, connection, recognition, joy and excitement. COMPOSITION: The {gender_word} on the LEFT facing the dog; Amigo on the RIGHT with perked ears. Clear physical separation. {style}"""
            },
            {
                "text_above_es": "Los primeros días juntos fueron de aprendizaje. {name} le enseñó a sentarse y Amigo le enseñó a ser paciente.",
                "text_below_es": "Jugaban en el jardín, corrían por el parque y descansaban juntos bajo los árboles.",
                "text_above_en": "The first days together were about learning. {name} taught Amigo to sit, and Amigo taught {name} to be patient.",
                "text_below_en": "They played in the garden, ran through the park, and rested together under the trees.",
                "scene_template": """Disney Pixar 3D style illustration. CHARACTER 1: The human {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, laughing with pure joy, mouth open in a big happy smile. A normal human body, two arms, two legs, smooth skin. OUTFIT: Soft gray hoodie and blue jeans. CHARACTER 2: {dog_forever_desc}, running playfully with ears flopping, tongue out, joyful expression, a red ball in mouth. ACTION: The {gender_word} runs on the LEFT through a grassy park, {hair_action}, both arms swinging with energy. Amigo runs on the RIGHT a few steps ahead carrying a red ball in his mouth, looking back playfully. SETTING: Beautiful sunny park WIDE VIEW, bright green grass, colorful autumn trees, blue sky, other dogs and families visible far in the background. ATMOSPHERE: Pure happiness, playful energy, joyful friendship, warm bright sunlight. COMPOSITION: The {gender_word} runs on the LEFT; Amigo the golden-brown dog runs ahead on the RIGHT. Clear physical separation, both in motion. {style}"""
            },
            {
                "text_above_es": "Una tarde de lluvia, {name} se sentía triste. Amigo se acercó despacio y apoyó su cabeza en las piernas de {name}.",
                "text_below_es": "Sin decir nada, Amigo le recordó que nunca estaría sol{o_a}. A veces, la mejor compañía es la que está en silencio.",
                "text_above_en": "One rainy afternoon, {name} was feeling sad. Amigo came over slowly and rested his head on {name}'s legs.",
                "text_below_en": "Without a word, Amigo reminded {name} of never being alone. Sometimes, the best company is the one that stays silent.",
                "scene_template": """Disney Pixar 3D style illustration. CHARACTER 1: The human {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, gentle peaceful expression with soft eyes, a small comforted smile forming. A normal human body, two arms, two legs, smooth skin. OUTFIT: Soft gray hoodie and blue jeans. CHARACTER 2: {dog_forever_desc}, lying down with head resting gently on the {gender_word}'s lap, big gentle dark brown eyes looking up with love and devotion, body relaxed and warm. ACTION: The {gender_word} sits on a cozy window seat on the LEFT, {hair_action}, one {skin_tone} hand gently resting on Amigo's head. Amigo lies next to the {gender_word} with head on lap. Rain visible on the window glass behind them. SETTING: Cozy living room with large window WIDE VIEW, rain streaming down the glass, warm interior lamp light, soft blanket, cushions, warm and safe indoor atmosphere. ATMOSPHERE: Comfort, unconditional love, quiet companionship, rainy day warmth, emotional tenderness. COMPOSITION: The {gender_word} sits on the LEFT; Amigo rests his head on the {gender_word}'s lap. Connected but clear forms. {style}"""
            },
            {
                "text_above_es": "Desde ese día, {name} y Amigo fueron inseparables. Compartirían paseos, juegos y ratos tranquilos.",
                "text_below_es": "El perro tendría un hogar y {name} tendría un amigo para siempre. Todo empezó con un encuentro inesperado en el parque.",
                "text_above_en": "From that day on, {name} and Amigo were inseparable. They would share walks, games, and quiet moments together.",
                "text_below_en": "The dog would have a home, and {name} would have a friend forever. It all started with an unexpected encounter in the park.",
                "scene_template": """Disney Pixar 3D style illustration. CHARACTER 1: The human {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, peaceful warm smile seen from the side, content and happy. A normal human body, two arms, two legs, smooth skin. OUTFIT: Soft gray hoodie and blue jeans. CHARACTER 2: {dog_forever_desc}, wearing a simple red collar, trotting happily a few steps ahead on the path, looking back at the {gender_word} with a warm gentle smile, tail wagging. ACTION: The {gender_word} walks on the LEFT side of a golden autumn path, {hair_action}, one {skin_tone} hand swinging gently. Amigo walks a few steps ahead on the RIGHT, looking back warmly. SETTING: WIDE panoramic view of a beautiful park at golden sunset, spectacular orange and pink sky, trees with autumn gold and red leaves, long shadows on the path, birds flying in the sky. ATMOSPHERE: Deep friendship, golden light, emotional peaceful ending, daily happiness, companionship forever. COMPOSITION: The {gender_word} walks on the LEFT; Amigo the golden-brown dog walks ahead on the RIGHT. Visible space between them on the wide path. Cinematic sunset light. {style}"""
            }
        ],
        "closing_template": """Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, peaceful content smile looking directly at the viewer with warm gentle eyes. A normal human body, two arms, two legs, smooth skin. OUTFIT: Soft gray hoodie and blue jeans. ACTION: The {gender_word} stands alone in a park at golden hour, {hair_action}, both {skin_tone} hands held gently over heart. SETTING: Beautiful park at golden sunset WIDE VIEW, warm orange and pink sky, autumn trees, golden light painting everything warm. ATMOSPHERE: Gratitude, love, inner warmth, peaceful happiness. STRICT: Only ONE {gender_word}. {style}""",
        "closing_message_es": "{name}, el amor de un amigo fiel es el tesoro más grande que existe.",
        "closing_message_en": "{name}, the love of a faithful friend is the greatest treasure there is."
    },
    "birthday_celebration_1_3": {
        "title_es": "Feliz Cumpleaños, {name}",
        "title_en": "Happy Birthday, {name}",
        "age_range": "1-3",
        "is_birthday": True,
        "use_preview_as_cover": True,
        "text_layout": "split",
        "page_count": 12,
        "preview_prompt_override": "Children's storybook watercolor illustration, soft luminous colors, magical warm lighting. CHARACTER: A single {gender_child} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, sweet joyful expression, big happy smile. OUTFIT: Cute comfortable birthday outfit, soft pastel colors, age-appropriate party clothes. ACTION: Standing at a colorful birthday party with many soft floating balloons everywhere, arms slightly open in excitement. A large shiny 3D red number {child_age} floats to the right of the child at head height, glossy balloon-like texture, approximately 3cm tall relative to child. SETTING: Birthday party room WIDE VIEW, soft streamers, pastel party decorations, colorful floating balloons, wrapped gifts. ATMOSPHERE: Festive warm celebration, soft golden light, magical birthday sparkles. STRICT: Only ONE child, {gender_child} is 100% human with normal body, no duplicates, the red 3D number {child_age} must be clearly visible. {style}",
        "cover_template": "Children's storybook watercolor illustration, soft luminous colors, magical warm lighting. CHARACTER: A single {gender_child} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, sweet innocent smile, bright tender eyes. OUTFIT: Cute comfortable birthday outfit, soft pastel colors, age-appropriate party clothes. ACTION: Standing surrounded by soft floating balloons, looking at viewer with a warm loving smile. A large shiny 3D red number {child_age} floats to the right of the child at head height, glossy balloon-like texture, approximately 3cm tall relative to child. SETTING: Magical birthday celebration WIDE VIEW, gentle pastel colors, soft floating balloons, warm cozy atmosphere. ATMOSPHERE: Cozy magical tenderness, gentle warm light, soft watercolor glow. STRICT: Only ONE child, {gender_child} is 100% human with normal body, no duplicates, the red 3D number {child_age} must be clearly visible. {style}",
        "pages": [
            {
                "text_above_es": "Hoy es un día muy especial, {name}.",
                "text_below_es": "¡Hoy es tu cumpleaños! Y nuestros corazones están llenos de amor por tenerte con nosotros.",
                "text_above_en": "Today is a very special day, {name}.",
                "text_below_en": "It's your birthday! And our hearts are full of love for having you with us.",
                "scene_template": "Children's storybook watercolor illustration, soft luminous colors, magical warm lighting. CHARACTER: A single {gender_child} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, happy tender expression, gentle smile. OUTFIT: Cozy pastel birthday outfit appropriate for a {gender_child}. ACTION: Sitting in a cozy decorated birthday room, looking around with wonder at the decorations. SETTING: Birthday room WIDE VIEW, soft colorful balloons floating gently, pastel streamers, gentle party decorations, small banner. ATMOSPHERE: Warm loving celebration, soft golden morning light, tender moment. STRICT: Only ONE child, {gender_child} is 100% human with normal body, no duplicates. {style}"
            },
            {
                "text_above_es": "Desde que llegaste a nuestra vida, todo es más bonito.",
                "text_below_es": "Tus sonrisas, tus gestos y tu forma de mirarnos hacen que cada día sea único y lleno de ternura.",
                "text_above_en": "Since you came into our lives, everything is more beautiful.",
                "text_below_en": "Your smiles, your gestures, and the way you look at us make every day unique and full of tenderness.",
                "scene_template": "Children's storybook watercolor illustration, soft luminous colors, magical warm lighting. CHARACTER: A single {gender_child} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, big warm smile, bright loving eyes. OUTFIT: Soft cozy pastel outfit, comfortable and adorable. ACTION: Sitting on a soft cozy blanket, smiling warmly with a tender expression. SETTING: Bright nursery room WIDE VIEW, sunlight streaming through window with curtains, soft toys nearby, warm pastel colors. ATMOSPHERE: Gentle loving tenderness, warm natural light, peaceful nurturing glow. STRICT: Only ONE child, {gender_child} is 100% human with normal body, no duplicates. {style}"
            },
            {
                "text_above_es": "Nos encanta verte descubrir el mundo poquito a poco.",
                "text_below_es": "Cada cosa nueva que tocas, miras y exploras nos llena de orgullo y alegría.",
                "text_above_en": "We love watching you discover the world little by little.",
                "text_below_en": "Every new thing you touch, look at, and explore fills us with pride and joy.",
                "scene_template": "Children's storybook watercolor illustration, soft luminous colors, magical warm lighting. CHARACTER: A single {gender_child} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, curious wide-eyed expression, wonder in eyes. OUTFIT: Comfortable pastel play outfit. ACTION: Exploring gently, touching soft toys and colorful stacking blocks on the floor. SETTING: Cozy playroom WIDE VIEW, soft cushions, birthday balloons visible in background, colorful toys scattered. ATMOSPHERE: Warm nurturing wonder, soft natural light, joyful discovery. STRICT: Only ONE child, {gender_child} is 100% human with normal body, no duplicates. {style}"
            },
            {
                "text_above_es": "¡Mira cuántos regalos hay para ti, {name}!",
                "text_below_es": "Cada lazo y cada papel de colores guarda una sorpresa llena de cariño.",
                "text_above_en": "Look at all the gifts for you, {name}!",
                "text_below_en": "Every ribbon and colorful wrapping hides a surprise full of love.",
                "scene_template": "Children's storybook watercolor illustration, soft luminous colors, magical warm lighting. CHARACTER: A single {gender_child} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, delighted adorable expression, eyes sparkling. OUTFIT: Cute pastel birthday outfit appropriate for a {gender_child}. ACTION: Hugging a soft plush toy, sitting among soft wrapped birthday presents with gentle ribbons and bows. SETTING: Birthday party room WIDE VIEW, floating heart shapes and sparkles around, colorful gift boxes, soft decorations. ATMOSPHERE: Magical loving warmth, soft golden light, tender celebration. STRICT: Only ONE child, {gender_child} is 100% human with normal body, no duplicates. {style}"
            },
            {
                "text_above_es": "Tus amigos peludos también celebran contigo.",
                "text_below_es": "Todos quieren estar cerca de ti en este día tan especial, porque eres muy querido.",
                "text_above_en": "Your fluffy friends are celebrating with you too.",
                "text_below_en": "Everyone wants to be close to you on this special day, because you are so loved.",
                "scene_template": "Children's storybook watercolor illustration, soft luminous colors, magical warm lighting. CHARACTER: A single {gender_child} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, happy giggling expression, warm smile. OUTFIT: Soft pastel party outfit. ACTION: Sitting on a soft rug surrounded by cute stuffed animals wearing tiny party hats, a teddy bear, a bunny, and a small puppy plush. SETTING: Cozy party room WIDE VIEW, birthday decorations, soft balloons in background, warm lighting. ATMOSPHERE: Warm cozy celebration, gentle golden light, loving companionship. STRICT: Only ONE child, {gender_child} is 100% human with normal body, no duplicates. {style}"
            },
            {
                "text_above_es": "Es hora de jugar con los globos de colores.",
                "text_below_es": "¡Vuelan por todas partes y tú ríes sin parar! La fiesta es pura diversión.",
                "text_above_en": "It's time to play with the colorful balloons.",
                "text_below_en": "They fly everywhere and you can't stop laughing! The party is pure fun.",
                "scene_template": "Children's storybook watercolor illustration, soft luminous colors, magical warm lighting. CHARACTER: A single {gender_child} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, laughing joyfully, pure delight. OUTFIT: Playful pastel birthday outfit. ACTION: Playing with many colorful floating balloons, reaching up to touch them, laughing with pure joy. SETTING: Decorated party room WIDE VIEW, streamers and confetti in the air, bright pastel balloons everywhere. ATMOSPHERE: Joyful playful energy, bright warm light, festive fun. STRICT: Only ONE child, {gender_child} is 100% human with normal body, no duplicates. {style}"
            },
            {
                "text_above_es": "¡Llegó la tarta, {name}!",
                "text_below_es": "Tiene {child_age} velita{candle_plural} brillando solo para ti. ¡Pide un deseo y sopla con fuerza!",
                "text_above_en": "Here comes the cake, {name}!",
                "text_below_en": "It has {child_age} shining candle{candle_plural_en} just for you. Make a wish and blow hard!",
                "scene_template": "Children's storybook watercolor illustration, soft luminous colors, magical warm lighting. CHARACTER: A single {gender_child} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, excited expression, puffed cheeks ready to blow. OUTFIT: Adorable pastel birthday outfit. ACTION: Sitting at a small decorated party table, leaning forward with puffed cheeks about to blow out {child_age} candle{candle_plural_en} on a beautiful simple round birthday cake. The cake has ONLY {child_age} colorful candle{candle_plural_en} arranged in a neat row on top, each candle clearly separated. A large shiny 3D red number {child_age} floats to the right of the child at head height, glossy balloon-like texture. SETTING: Birthday party table WIDE VIEW, one simple cake, soft balloons and party decorations around. ATMOSPHERE: Warm magical birthday moment, gentle golden candlelight, celebration anticipation. STRICT: Only ONE child, only ONE cake, cake has EXACTLY {child_age} candle{candle_plural_en} and NO MORE, {gender_child} is 100% human with normal body, no duplicates, the red 3D number {child_age} must be clearly visible. {style}"
            },
            {
                "text_above_es": "Este día ha sido maravilloso, lleno de risas y abrazos.",
                "text_below_es": "Pero lo más bonito de todo es tenerte a ti, {name}. Eres nuestro mayor regalo.",
                "text_above_en": "This day has been wonderful, full of laughter and hugs.",
                "text_below_en": "But the most beautiful thing of all is having you, {name}. You are our greatest gift.",
                "scene_template": "Children's storybook watercolor illustration, soft luminous colors, magical warm lighting. CHARACTER: A single {gender_child} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, peaceful content expression, satisfied warm smile. OUTFIT: Soft pastel birthday outfit. ACTION: Sitting contentedly among opened presents and colorful wrapping paper, holding a favorite new toy close. SETTING: Birthday room WIDE VIEW, soft decorations around, warm evening golden light through window. ATMOSPHERE: Cozy happy warmth, golden evening glow, loving peaceful moment. STRICT: Only ONE child, {gender_child} is 100% human with normal body, no duplicates. {style}"
            }
        ],
        "closing_template": "Children's storybook watercolor illustration, soft luminous colors, magical warm lighting. CHARACTER: A single {gender_child} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, peaceful loving smile, arms open wide. OUTFIT: Soft pastel birthday outfit. ACTION: Standing with arms open, surrounded by floating soft balloons and gentle confetti, feeling loved and cherished. SETTING: Magical birthday finale WIDE VIEW, hearts and stars twinkling softly, soft decorations, dreamy background. ATMOSPHERE: Warm loving celebration, golden soft light enveloping everything, magical tenderness. STRICT: Only ONE child, {gender_child} is 100% human with normal body, no duplicates. {style}",
        "closing_message_es": "Feliz cumpleaños, {name}. Que este nuevo año esté lleno de caricias, juegos, risas y mucho amor. Te queremos hoy y siempre.",
        "closing_message_en": "Happy birthday, {name}. May this new year be full of cuddles, games, laughter, and lots of love. We love you today and always."
    },
    "birthday_celebration_4_6": {
        "title_es": "Feliz Cumpleaños, {name}",
        "title_en": "Happy Birthday, {name}",
        "age_range": "4-6",
        "is_birthday": True,
        "use_preview_as_cover": True,
        "text_layout": "split",
        "page_count": 12,
        "preview_prompt_override": "Children's storybook watercolor illustration, soft luminous colors, magical warm lighting. CHARACTER: A single {gender_child} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, excited expression, puffed cheeks ready to blow. OUTFIT: Cute comfortable birthday outfit, soft pastel colors, age-appropriate party clothes. ACTION: Standing in front of a decorated party table, leaning forward with puffed cheeks ready to blow out {child_age} candle{candle_plural_en} on a beautiful simple round birthday cake. The cake has ONLY {child_age} colorful candle{candle_plural_en} arranged in a neat row on top, each candle clearly separated. A large shiny 3D red number {child_age} floats to the right of the child at head height, glossy balloon-like texture, approximately 3cm tall relative to child. SETTING: Birthday party table WIDE VIEW, one simple cake, colorful cupcakes and treats, balloons and streamers in background. ATMOSPHERE: Warm celebratory moment, golden candlelight glow, magical wish anticipation. STRICT: Only ONE child, only ONE cake, cake has EXACTLY {child_age} candle{candle_plural_en} and NO MORE, {gender_child} is 100% human with normal body, no duplicates, the red 3D number {child_age} must be clearly visible. {style}",
        "cover_template": "Children's storybook watercolor illustration, soft luminous colors, magical warm lighting. CHARACTER: A single {gender_child} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, excited expression, puffed cheeks ready to blow. OUTFIT: Cute comfortable birthday outfit, soft pastel colors, age-appropriate party clothes. ACTION: Standing in front of a decorated party table, leaning forward with puffed cheeks ready to blow out {child_age} candle{candle_plural_en} on a beautiful simple round birthday cake. The cake has ONLY {child_age} colorful candle{candle_plural_en} arranged in a neat row on top, each candle clearly separated. A large shiny 3D red number {child_age} floats to the right of the child at head height, glossy balloon-like texture, approximately 3cm tall relative to child. SETTING: Birthday party table WIDE VIEW, one simple cake, colorful cupcakes and treats, balloons and streamers in background. ATMOSPHERE: Warm celebratory moment, golden candlelight glow, magical wish anticipation. STRICT: Only ONE child, only ONE cake, cake has EXACTLY {child_age} candle{candle_plural_en} and NO MORE, {gender_child} is 100% human with normal body, no duplicates, the red 3D number {child_age} must be clearly visible. {style}",
        "pages": [
            {
                "text_above_es": "¡Hoy es tu cumpleaños, {name}!",
                "text_below_es": "Todo está listo para la fiesta más increíble del mundo. ¡Los globos, los regalos y la diversión te esperan!",
                "text_above_en": "It's your birthday, {name}!",
                "text_below_en": "Everything is ready for the most amazing party in the world. The balloons, the gifts, and the fun are waiting for you!",
                "scene_template": "Children's storybook watercolor illustration, soft luminous colors, magical warm lighting. CHARACTER: A single {gender_child} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, happy excited expression, arms raised in joy. OUTFIT: Colorful festive party outfit. ACTION: Standing in a colorful birthday party room with arms raised in excitement, surrounded by floating balloons. SETTING: Birthday party room WIDE VIEW, colorful floating balloons, beautifully wrapped gift boxes on floor, streamers and party banners. ATMOSPHERE: Festive joyful celebration, warm golden lighting, magical sparkles. STRICT: Only ONE child, {gender_child} is 100% human with normal body, no duplicates. {style}"
            },
            {
                "text_above_es": "Lo primero que haces al despertar es sonreír.",
                "text_below_es": "Porque sabes que hoy es tu día especial y hay muchas sorpresas esperándote.",
                "text_above_en": "The first thing you do when you wake up is smile.",
                "text_below_en": "Because you know today is your special day and there are many surprises waiting for you.",
                "scene_template": "Children's storybook watercolor illustration, soft luminous colors, magical warm lighting. CHARACTER: A single {gender_child} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, joyful morning smile, bright happy eyes. OUTFIT: Cozy pajamas, just woken up. ACTION: Sitting up in a cozy bed with colorful pillows, stretching with a big smile. SETTING: Bright child bedroom WIDE VIEW, sunlight streaming through large window, balloons and birthday decorations in the room. ATMOSPHERE: Happy birthday morning, warm natural light, excited anticipation. STRICT: Only ONE child, {gender_child} is 100% human with normal body, no duplicates. {style}"
            },
            {
                "text_above_es": "¡Hora de abrir los regalos!",
                "text_below_es": "Cada caja guarda algo especial, elegido con mucho cariño. ¡Tus ojos brillan de emoción!",
                "text_above_en": "Time to open the presents!",
                "text_below_en": "Every box holds something special, chosen with lots of love. Your eyes sparkle with excitement!",
                "scene_template": "Children's storybook watercolor illustration, soft luminous colors, magical warm lighting. CHARACTER: A single {gender_child} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, excited wide-eyed expression, sparkling with surprise. OUTFIT: Cute festive party outfit. ACTION: Sitting on the floor opening a beautifully wrapped present, colorful wrapping paper and ribbons scattered around. SETTING: Birthday party room WIDE VIEW, other gift boxes nearby, birthday decorations and balloons in background. ATMOSPHERE: Warm cheerful excitement, bright joyful light, magical surprise moment. STRICT: Only ONE child, {gender_child} is 100% human with normal body, no duplicates. {style}"
            },
            {
                "text_above_es": "La fiesta está llena de juegos divertidos.",
                "text_below_es": "Carreras, risas y muchas travesuras. ¡No puedes parar de divertirte!",
                "text_above_en": "The party is full of fun games.",
                "text_below_en": "Races, laughter, and lots of mischief. You can't stop having fun!",
                "scene_template": "Children's storybook watercolor illustration, soft luminous colors, magical warm lighting. CHARACTER: A single {gender_child} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, laughing playfully, mischievous happy expression. OUTFIT: Comfortable colorful party outfit. ACTION: Playing with colorful building blocks and party games on the floor, having fun. SETTING: Decorated party room WIDE VIEW, confetti and streamers around, balloons everywhere, bright pastel colors. ATMOSPHERE: Happy playful energy, bright warm light, festive fun. STRICT: Only ONE child, {gender_child} is 100% human with normal body, no duplicates. {style}"
            },
            {
                "text_above_es": "Te pones tu corona de cumpleaños y te sientes como la realeza.",
                "text_below_es": "Hoy tú eres la estrella y todos quieren celebrar contigo.",
                "text_above_en": "You put on your birthday crown and feel like royalty.",
                "text_below_en": "Today you are the star and everyone wants to celebrate with you.",
                "scene_template": "Children's storybook watercolor illustration, soft luminous colors, magical warm lighting. CHARACTER: A single {gender_child} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, proud confident expression, standing tall. OUTFIT: Festive party outfit with a sparkling golden paper birthday crown. ACTION: Standing tall with a confident happy pose, wearing a sparkling birthday crown, magical sparkles around. SETTING: Birthday party room WIDE VIEW, colorful decorations everywhere, balloons and streamers, festive environment. ATMOSPHERE: Warm festive royalty, golden magical sparkles, celebratory pride. STRICT: Only ONE child, {gender_child} is 100% human with normal body, no duplicates. {style}"
            },
            {
                "text_above_es": "Los globos de colores llenan toda la fiesta.",
                "text_below_es": "¡Atrapas uno rojo, sueltas uno azul y ríes mientras vuelan por todas partes!",
                "text_above_en": "Colorful balloons fill the whole party.",
                "text_below_en": "You catch a red one, release a blue one, and laugh as they fly everywhere!",
                "scene_template": "Children's storybook watercolor illustration, soft luminous colors, magical warm lighting. CHARACTER: A single {gender_child} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, cheerful laughing expression, pure joy. OUTFIT: Colorful festive party outfit. ACTION: Surrounded by many colorful floating balloons, reaching up to catch balloons, laughing with pure joy. SETTING: Decorated party room WIDE VIEW, streamers and confetti in the air, bright festive colors. ATMOSPHERE: Bright festive joy, warm playful light, balloon-filled celebration. STRICT: Only ONE child, {gender_child} is 100% human with normal body, no duplicates. {style}"
            },
            {
                "text_above_es": "¡Llega la tarta de cumpleaños, {name}!",
                "text_below_es": "Tiene {child_age} velita{candle_plural} brillando solo para ti. Cierra los ojos, pide un deseo... ¡y sopla!",
                "text_above_en": "Here comes the birthday cake, {name}!",
                "text_below_en": "It has {child_age} shining candle{candle_plural_en} just for you. Close your eyes, make a wish... and blow!",
                "scene_template": "Children's storybook watercolor illustration, soft luminous colors, magical warm lighting. CHARACTER: A single {gender_child} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, excited expression, puffed cheeks ready to blow. OUTFIT: Festive party outfit. ACTION: Standing in front of a decorated party table, leaning forward with puffed cheeks ready to blow out {child_age} candle{candle_plural_en} on a beautiful simple round birthday cake. The cake has ONLY {child_age} colorful candle{candle_plural_en} arranged in a neat row on top, each candle clearly separated. A large shiny 3D red number {child_age} floats to the right of the child at head height, glossy balloon-like texture. SETTING: Birthday party table WIDE VIEW, one simple cake, colorful cupcakes and treats, balloons and streamers in background. ATMOSPHERE: Warm celebratory moment, golden candlelight glow, magical wish anticipation. STRICT: Only ONE child, only ONE cake, cake has EXACTLY {child_age} candle{candle_plural_en} and NO MORE, {gender_child} is 100% human with normal body, no duplicates, the red 3D number {child_age} must be clearly visible. {style}"
            },
            {
                "text_above_es": "Ha sido el mejor cumpleaños del mundo.",
                "text_below_es": "Pero lo más bonito de todo es que nos tienes a nosotros, y te queremos con todo el corazón.",
                "text_above_en": "It has been the best birthday in the world.",
                "text_below_en": "But the most beautiful thing of all is that you have us, and we love you with all our hearts.",
                "scene_template": "Children's storybook watercolor illustration, soft luminous colors, magical warm lighting. CHARACTER: A single {gender_child} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, happy content expression, satisfied warm smile. OUTFIT: Festive party outfit. ACTION: Sitting among opened birthday presents and colorful wrapping paper, holding a favorite new toy close with a satisfied smile. SETTING: Birthday room WIDE VIEW, party decorations and balloons in background, warm evening golden light. ATMOSPHERE: Cozy happy warmth, golden evening glow, loving content moment. STRICT: Only ONE child, {gender_child} is 100% human with normal body, no duplicates. {style}"
            }
        ],
        "closing_template": "Children's storybook watercolor illustration, soft luminous colors, magical warm lighting. CHARACTER: A single {gender_child} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, happy celebrated smile, arms open wide. OUTFIT: Festive party outfit. ACTION: Standing in the center with arms open wide, feeling loved and celebrated, surrounded by floating balloons and confetti. SETTING: Magical birthday finale WIDE VIEW, hearts and stars sparkling around, birthday decorations everywhere, dreamy background. ATMOSPHERE: Warm magical celebration, golden festive light, love and joy. STRICT: Only ONE child, {gender_child} is 100% human with normal body, no duplicates. {style}",
        "closing_message_es": "Feliz cumpleaños, {name}. Que este nuevo año esté lleno de juegos, aventuras, abrazos y momentos felices. Te queremos hoy y siempre.",
        "closing_message_en": "Happy birthday, {name}. May this new year be full of games, adventures, hugs, and happy moments. We love you today and always."
    },
    "birthday_celebration_7_9": {
        "title_es": "Feliz Cumpleaños, {name}",
        "title_en": "Happy Birthday, {name}",
        "age_range": "7-9",
        "is_birthday": True,
        "use_preview_as_cover": True,
        "text_layout": "split",
        "page_count": 12,
        "preview_prompt_override": "Children's storybook watercolor illustration, soft luminous colors, magical warm lighting. CHARACTER: A single {gender_child} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, confident joyful expression, big happy smile. OUTFIT: Stylish colorful party outfit, festive and cool. ACTION: Standing at a colorful birthday party celebration, confident pose, surrounded by floating balloons, streamers, and confetti. A large shiny 3D red number {child_age} floats to the right of the child at head height, glossy balloon-like texture, approximately 3cm tall relative to child. SETTING: Birthday party room WIDE VIEW, colorful balloons, streamers, confetti, birthday cake with candles nearby. ATMOSPHERE: Festive cheerful celebration, warm golden light, magical birthday energy. STRICT: Only ONE child, {gender_child} is 100% human with normal body, no duplicates, the red 3D number {child_age} must be clearly visible. {style}",
        "cover_template": "Children's storybook watercolor illustration, soft luminous colors, magical warm lighting. CHARACTER: A single {gender_child} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, confident happy smile, eyes full of adventure. OUTFIT: Stylish festive party outfit. ACTION: Standing surrounded by balloons, smiling confidently at viewer. A large shiny 3D red number {child_age} floats to the right of the child at head height, glossy balloon-like texture, approximately 3cm tall relative to child. SETTING: Magical birthday celebration WIDE VIEW, soft pastel colors, floating balloons, warm cozy atmosphere. ATMOSPHERE: Cozy magical celebration, gentle warm light, whimsical confident glow. STRICT: Only ONE child, {gender_child} is 100% human with normal body, no duplicates, the red 3D number {child_age} must be clearly visible. {style}",
        "pages": [
            {
                "text_above_es": "¡{name}, hoy es tu gran día!",
                "text_below_es": "Otro año más lleno de aventuras, descubrimientos y momentos increíbles. ¡La fiesta acaba de empezar!",
                "text_above_en": "{name}, today is your big day!",
                "text_below_en": "Another year full of adventures, discoveries, and amazing moments. The party has just begun!",
                "scene_template": "Children's storybook watercolor illustration, soft luminous colors, magical warm lighting. CHARACTER: A single {gender_child} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, happy confident expression, arms open in excitement. OUTFIT: Stylish colorful party outfit. ACTION: Standing in a beautifully decorated birthday party room with arms open in excitement, surrounded by floating balloons. SETTING: Birthday party room WIDE VIEW, colorful floating balloons, beautifully wrapped gift boxes, streamers and party banners. ATMOSPHERE: Festive joyful celebration, warm golden lighting, magical sparkles. STRICT: Only ONE child, {gender_child} is 100% human with normal body, no duplicates. {style}"
            },
            {
                "text_above_es": "Cada día nos sorprendes con tus ideas y tus ganas de aprender.",
                "text_below_es": "Verte crecer, hacerte preguntas y descubrir el mundo es una de nuestras mayores alegrías.",
                "text_above_en": "Every day you surprise us with your ideas and your desire to learn.",
                "text_below_en": "Watching you grow, ask questions, and discover the world is one of our greatest joys.",
                "scene_template": "Children's storybook watercolor illustration, soft luminous colors, magical warm lighting. CHARACTER: A single {gender_child} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, curious thoughtful expression, sparkling eyes full of wonder. OUTFIT: Comfortable stylish outfit. ACTION: Reading an adventure book with sparkling eyes, imagination elements floating around like tiny stars and swirls. SETTING: Bright colorful room WIDE VIEW, birthday decorations visible in background with balloons, warm natural light. ATMOSPHERE: Warm curiosity and wonder, natural light, imaginative sparkles. STRICT: Only ONE child, {gender_child} is 100% human with normal body, no duplicates. {style}"
            },
            {
                "text_above_es": "La hora de los regalos es siempre emocionante.",
                "text_below_es": "Abres cada uno con curiosidad, y tu sonrisa crece con cada sorpresa.",
                "text_above_en": "Gift time is always exciting.",
                "text_below_en": "You open each one with curiosity, and your smile grows with every surprise.",
                "scene_template": "Children's storybook watercolor illustration, soft luminous colors, magical warm lighting. CHARACTER: A single {gender_child} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, excited expression of wonder and delight. OUTFIT: Festive stylish party outfit. ACTION: Opening a large beautifully wrapped birthday present, colorful wrapping paper flying around. SETTING: Birthday party room WIDE VIEW, other gift boxes with ribbons nearby, party decorations and balloons in background. ATMOSPHERE: Warm cheerful excitement, bright joyful light, magical surprise. STRICT: Only ONE child, {gender_child} is 100% human with normal body, no duplicates. {style}"
            },
            {
                "text_above_es": "¡Los juegos de la fiesta son lo mejor!",
                "text_below_es": "Carreras, acertijos y mucha diversión. ¡Eres imparable cuando te diviertes!",
                "text_above_en": "The party games are the best!",
                "text_below_en": "Races, puzzles, and lots of fun. You're unstoppable when you're having fun!",
                "scene_template": "Children's storybook watercolor illustration, soft luminous colors, magical warm lighting. CHARACTER: A single {gender_child} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, laughing energetically, dynamic joyful expression. OUTFIT: Comfortable party outfit. ACTION: Playing fun party games, jumping and celebrating, confetti and streamers flying around. SETTING: Decorated party room WIDE VIEW, colorful party games and activities visible, balloons everywhere, bright pastel colors. ATMOSPHERE: Happy energetic celebration, bright warm light, festive excitement. STRICT: Only ONE child, {gender_child} is 100% human with normal body, no duplicates. {style}"
            },
            {
                "text_above_es": "Hoy te sientes como un superhéroe.",
                "text_below_es": "Con tu corona de cumpleaños brillando, todos celebran lo genial que eres.",
                "text_above_en": "Today you feel like a superhero.",
                "text_below_en": "With your birthday crown shining, everyone celebrates how awesome you are.",
                "scene_template": "Children's storybook watercolor illustration, soft luminous colors, magical warm lighting. CHARACTER: A single {gender_child} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, proud confident expression, standing tall. OUTFIT: Party outfit with a sparkling golden birthday crown. ACTION: Striking a fun confident superhero pose, wearing a sparkling birthday crown, magical sparkles around. SETTING: Birthday party room WIDE VIEW, colorful decorations everywhere, balloons and streamers, festive environment. ATMOSPHERE: Warm festive confidence, golden magical sparkles, superhero celebration. STRICT: Only ONE child, {gender_child} is 100% human with normal body, no duplicates. {style}"
            },
            {
                "text_above_es": "¡Llega la piñata de colores!",
                "text_below_es": "Le das con fuerza y llueven dulces y confeti por todas partes. ¡Qué divertido!",
                "text_above_en": "Here comes the colorful piñata!",
                "text_below_en": "You hit it hard and candy and confetti rain down everywhere. How fun!",
                "scene_template": "Children's storybook watercolor illustration, soft luminous colors, magical warm lighting. CHARACTER: A single {gender_child} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, energetic determined expression, having a blast. OUTFIT: Festive party outfit. ACTION: Swinging at a colorful star-shaped piñata hanging from above, candy and confetti bursting out and falling through the air. SETTING: Birthday party area WIDE VIEW, decorations and balloons around, candy raining down, festive environment. ATMOSPHERE: Exciting festive energy, bright warm colors, joyful action moment. STRICT: Only ONE child, {gender_child} is 100% human with normal body, no duplicates. {style}"
            },
            {
                "text_above_es": "¡La tarta de cumpleaños es espectacular, {name}!",
                "text_below_es": "Tiene {child_age} velita{candle_plural} brillando. Cierra los ojos, pide un deseo muy fuerte... ¡y sopla!",
                "text_above_en": "The birthday cake is spectacular, {name}!",
                "text_below_en": "It has {child_age} shining candle{candle_plural_en}. Close your eyes, make a big wish... and blow!",
                "scene_template": "Children's storybook watercolor illustration, soft luminous colors, magical warm lighting. CHARACTER: A single {gender_child} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, excited expression, puffed cheeks ready to blow. OUTFIT: Stylish party outfit. ACTION: Standing in front of a decorated party table, leaning forward with puffed cheeks ready to blow out {child_age} candle{candle_plural_en} on a spectacular simple round birthday cake. The cake has ONLY {child_age} colorful candle{candle_plural_en} arranged in a neat row on top, each candle clearly separated. A large shiny 3D red number {child_age} floats to the right of the child at head height, glossy balloon-like texture. SETTING: Birthday party table WIDE VIEW, one spectacular cake, colorful cupcakes and treats, balloons and streamers in background. ATMOSPHERE: Warm celebratory moment, golden candlelight glow, magical wish anticipation. STRICT: Only ONE child, only ONE cake, cake has EXACTLY {child_age} candle{candle_plural_en} and NO MORE, {gender_child} is 100% human with normal body, no duplicates, the red 3D number {child_age} must be clearly visible. {style}"
            },
            {
                "text_above_es": "Ha sido un cumpleaños increíble, {name}.",
                "text_below_es": "Pero lo mejor no son los regalos ni la fiesta. Lo mejor es que te tenemos a ti.",
                "text_above_en": "It's been an amazing birthday, {name}.",
                "text_below_en": "But the best part isn't the gifts or the party. The best part is having you.",
                "scene_template": "Children's storybook watercolor illustration, soft luminous colors, magical warm lighting. CHARACTER: A single {gender_child} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, happy satisfied expression, warm grateful smile. OUTFIT: Stylish party outfit. ACTION: Sitting comfortably among opened birthday presents and colorful wrapping paper, holding a favorite new gift close. SETTING: Birthday room WIDE VIEW, party decorations and balloons in background, warm evening golden light. ATMOSPHERE: Cozy happy warmth, golden evening glow, grateful loving moment. STRICT: Only ONE child, {gender_child} is 100% human with normal body, no duplicates. {style}"
            }
        ],
        "closing_template": "Children's storybook watercolor illustration, soft luminous colors, magical warm lighting. CHARACTER: A single {gender_child} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, happy confident smile, arms open wide. OUTFIT: Stylish party outfit. ACTION: Standing in the center with arms open wide, feeling celebrated and loved, surrounded by floating balloons and confetti. SETTING: Magical birthday finale WIDE VIEW, hearts and stars sparkling around, birthday decorations everywhere, dreamy background. ATMOSPHERE: Warm magical celebration, golden festive light, confidence and joy. STRICT: Only ONE child, {gender_child} is 100% human with normal body, no duplicates. {style}",
        "closing_message_es": "Feliz cumpleaños, {name}. Que este nuevo año esté lleno de diversión, aprendizajes, abrazos y recuerdos felices. Siempre estaremos aquí para ti.",
        "closing_message_en": "Happy birthday, {name}. May this new year be full of fun, learning, hugs, and happy memories. We will always be here for you."
    }
}


def get_hair_description(traits: dict, gender: str = None) -> str:
    """Build natural hair description (hair only, not eyes)."""
    color = traits.get('hair_color', 'brown')
    length = traits.get('hair_length', 'medium')
    hair_type = traits.get('hair_type', 'straight')
    if gender is None:
        gender = traits.get('gender', traits.get('child_gender', ''))
    
    color_map = {
        'black': 'jet black',
        'brown': 'medium brown',
        'light_brown': 'light brown',
        'blonde': 'golden blonde',
        'very_light_blonde': 'very light blonde',
        'red': 'bright red',
        'auburn': 'auburn'
    }
    
    type_map = {
        'straight': 'straight',
        'wavy': 'wavy',
        'curly': 'curly'
    }
    
    c = color_map.get(color, color)
    
    t = type_map.get(hair_type, hair_type)
    
    if length == 'bald':
        return "completely smooth bald head, perfectly round hairless baby head, clean soft scalp"
    
    if length == 'very_little':
        return f"smooth round head with very short thin {c} baby hair, just a soft fine layer of {c} hair visible on head, baby-fine wispy {c} hair"
    
    if length == 'short':
        if gender == 'male':
            return f"{c} short cropped {t} boy haircut, trimmed above ears and neatly tapered"
        else:
            return f"{c} short {t} hair"
    
    length_map = {
        'medium': 'medium-length',
        'long': 'long flowing'
    }
    
    l = length_map.get(length, length)
    
    return f"{c} {l} {t} hair"


def get_eye_description(traits: dict) -> str:
    """Get eye color description."""
    eye_color = traits.get('eye_color', 'brown')
    eye_map = {
        'black': 'deep black',
        'brown': 'warm brown',
        'hazel': 'hazel green-brown',
        'green': 'bright green',
        'blue': 'clear blue',
        'gray': 'soft gray'
    }
    return eye_map.get(eye_color, eye_color) + " eyes"


def get_hair_action(traits: dict) -> str:
    """Get static hair position description for consistent rendering across scenes."""
    length = traits.get('hair_length', 'medium')
    hair_type = traits.get('hair_type', 'straight')
    
    if length == 'very_little':
        return "thin soft fuzz of hair visible on head"
    elif length == 'short':
        gender = traits.get('gender', traits.get('child_gender', ''))
        if gender == 'male':
            return "short cropped boy hair neatly trimmed"
        return "short hair neatly in place"
    elif length == 'long':
        if hair_type == 'curly':
            return "long curly hair resting naturally on shoulders"
        elif hair_type == 'wavy':
            return "long wavy hair resting naturally over shoulders"
        else:
            return "long straight hair resting naturally over shoulders"
    else:
        if hair_type == 'curly':
            return "medium-length curly hair neatly in place"
        elif hair_type == 'wavy':
            return "medium-length wavy hair neatly in place"
        else:
            return "medium-length hair neatly in place"


def get_skin_tone(skin: str) -> str:
    """Get detailed skin tone description for consistent AI generation."""
    skin_map = {
        'very_light': 'very fair porcelain with soft pink undertones',
        'light': 'light peach with warm rosy undertones',
        'medium_light': 'warm olive with golden-beige undertones',
        'medium': 'warm caramel brown with rich golden undertones',
        'olive': 'warm olive-toned with golden-tan undertones',
        'tan': 'warm caramel tan with rich golden-brown undertones',
        'medium_dark': 'deep brown with warm mahogany undertones',
        'brown': 'rich brown with deep mahogany undertones',
        'dark': 'deep rich dark brown with warm chocolate undertones, clearly dark complexion'
    }
    return skin_map.get(skin, skin)


def get_gender_child(gender: str) -> str:
    """Get gender word."""
    if gender == 'female':
        return 'little girl'
    elif gender == 'male':
        return 'little boy'
    return 'young child'


def get_gender_child_es(gender: str) -> str:
    """Get Spanish gender word."""
    if gender == 'female':
        return 'niña'
    elif gender == 'male':
        return 'niño'
    return 'niño'


def get_spanish_gender_endings(gender: str) -> dict:
    """Get Spanish gendered word endings and adjectives."""
    if gender == 'female':
        return {
            'o_a': 'a',
            'el_la': 'la',
            'proud': 'orgullosa',
            'ready': 'lista',
            'happy': 'feliz',
            'safe': 'segura',
            'brave': 'valiente',
        }
    else:
        return {
            'o_a': 'o',
            'el_la': 'el',
            'proud': 'orgulloso',
            'ready': 'listo',
            'happy': 'feliz', 
            'safe': 'seguro',
            'brave': 'valiente',
        }


def prepare_story(story_id: str, child_name: str, gender: str, traits: dict, lang: str = 'es') -> dict:
    """
    Prepare complete story with personalized text and scene prompts.
    """
    story = STORIES.get(story_id)
    if not story:
        raise ValueError(f"Story not found: {story_id}")
    
    hair_desc = get_hair_description(traits)
    eye_desc = get_eye_description(traits)
    hair_action = get_hair_action(traits)
    skin_tone = get_skin_tone(traits.get('skin_tone', 'light'))
    gender_child = get_gender_child(gender)
    gender_child_es = get_gender_child_es(gender)
    gender_endings = get_spanish_gender_endings(gender)
    
    # Extract individual hair components for new prompt format
    hair_color = traits.get('hair_color', 'brown')
    hair_length = traits.get('hair_length', 'medium')
    hair_type = traits.get('hair_type', 'straight')
    
    # Age display based on child's age
    child_age = int(traits.get('child_age', '4'))
    age_display = f"{child_age} year old" if child_age > 0 else "baby"
    
    age_range = story.get('age_range', '3-8')
    is_baby_story = age_range in ['0-1', '0-2']
    if is_baby_story:
        gender_word = "baby boy" if gender == "male" else "baby girl" if gender == "female" else "baby"
    else:
        gender_word = gender_child
    
    # Build child base description for consistent character rendering
    # Use story-specific base_character_override if available
    base_template = story.get('base_character_override', CHILD_BASE_DESC)
    gender_features = "soft round cheeks, cute expression" if gender == 'female' else "cute expression"
    
    child_base_desc = base_template.format(
        gender_child=gender_child,
        age_display=age_display,
        hair_desc=hair_desc,
        hair_color=hair_color,
        hair_length=hair_length,
        hair_type=hair_type,
        skin_tone=skin_tone,
        eye_desc=eye_desc,
        gender_features=gender_features
    )
    
    lo_la = "la" if gender == "female" else "lo"
    pet_name = traits.get('pet_name', '') if traits else ''
    extra_format = {'pet_name': pet_name} if pet_name else {}
    title = story['title_es'] if lang == 'es' else story['title_en']
    title = title.format(name=child_name, gender_child=gender_child, gender_child_es=gender_child_es, lo_la=lo_la, **gender_endings, **extra_format)
    
    pages = []
    is_illustrated_book = story.get('use_fixed_scenes', False)
    scenes_dir = story.get('scenes_dir', '')
    
    # Use content_pages for illustrated books, pages for regular stories
    source_pages = story.get('content_pages', []) if is_illustrated_book else story.get('pages', [])
    
    text_layout = story.get('text_layout', 'single')
    
    is_birthday = story.get('is_birthday', False)
    candle_plural = "s" if child_age != 1 else ""
    candle_plural_en = "s" if child_age != 1 else ""
    birthday_format = {'child_age': child_age, 'candle_plural': candle_plural, 'candle_plural_en': candle_plural_en} if is_birthday else {}
    
    for i, page in enumerate(source_pages, 1):
        if text_layout == 'split':
            above_key = f'text_above_{lang}'
            below_key = f'text_below_{lang}'
            text_above = page.get(above_key, '').format(
                name=child_name, gender_child=gender_child, gender_child_es=gender_child_es, **gender_endings, **extra_format, **birthday_format
            ) if page.get(above_key) else ''
            text_below = page.get(below_key, '').format(
                name=child_name, gender_child=gender_child, gender_child_es=gender_child_es, **gender_endings, **extra_format, **birthday_format
            ) if page.get(below_key) else ''
            text = text_above + ' ' + text_below
        else:
            text_key = 'text_es' if lang == 'es' else 'text_en'
            text = page[text_key].format(name=child_name, gender_child=gender_child, gender_child_es=gender_child_es, **gender_endings, **extra_format)
            text_above = ''
            text_below = ''
        
        page_data = {
            'page_num': i,
            'text': text
        }
        
        if text_layout == 'split':
            page_data['text_above'] = text_above
            page_data['text_below'] = text_below
        
        if is_illustrated_book and 'fixed_scene' in page:
            page_data['fixed_scene'] = f"{scenes_dir}/{page['fixed_scene']}"
            page_data['character_pose'] = page.get('character_pose', 'standing')
            page_data['scene_prompt'] = None
        elif 'scene_template' in page:
            is_toddler = is_baby_story and child_age >= 1
            if is_toddler and 'scene_template_toddler' in page:
                active_template = page['scene_template_toddler']
            else:
                active_template = page['scene_template']
            has_eye_desc = '{eye_desc}' in active_template
            scene_hair_desc = hair_desc if has_eye_desc else hair_desc + ", " + eye_desc
            
            scene_style = "NO text, NO watermark, NO signature, NO logo, NO artist name, NO handwriting, NO calligraphy, clean illustration only"
            
            scene_prompt = active_template.format(
                name=child_name,
                gender_child=gender_child,
                gender_child_es=gender_child_es,
                gender_word=gender_word,
                hair_desc=scene_hair_desc,
                hair_color=hair_color,
                hair_length=hair_length,
                hair_type=hair_type,
                eye_desc=eye_desc,
                age_display=age_display,
                hair_action=hair_action,
                skin_tone=skin_tone,
                style=scene_style,
                child_age=child_age,
                candle_plural=candle_plural,
                candle_plural_en=candle_plural_en,
                spark_desc=SPARK_DESC.format(gender_word=gender_word),
                mama_dragon_desc=MAMA_DRAGON_DESC,
                puppy_desc=PUPPY_DESC,
                kitten_desc=KITTEN_DESC,
                lila_desc=LILA_DESC.format(gender_word=gender_word),
                bunny_desc=BUNNY_DESC,
                guardian_light_desc=GUARDIAN_LIGHT_DESC,
                child_base_desc=child_base_desc,
                dog_forever_desc=DOG_FOREVER_DESC.format(gender_word=gender_word),
                **gender_endings
            )
            page_data['scene_prompt'] = scene_prompt
        else:
            page_data['scene_prompt'] = None
        
        pages.append(page_data)
    
    return {
        'story_id': story_id,
        'title': title,
        'child_name': child_name,
        'gender': gender,
        'pages': pages,
        'is_illustrated_book': is_illustrated_book,
        'scenes_dir': scenes_dir,
        'text_layout': text_layout
    }


def get_cover_prompt(story_id: str, child_name: str, gender: str, traits: dict) -> str:
    """Get the cover prompt for a story."""
    story = STORIES.get(story_id)
    if not story:
        raise ValueError(f"Story not found: {story_id}")
    
    if 'cover_template' not in story:
        return None
    
    hair_desc = get_hair_description(traits)
    eye_desc = get_eye_description(traits)
    hair_action = get_hair_action(traits)
    skin_tone = get_skin_tone(traits.get('skin_tone', 'light'))
    gender_child = get_gender_child(gender)
    gender_child_es = get_gender_child_es(gender)
    gender_endings = get_spanish_gender_endings(gender)
    
    # Extract individual hair components for new prompt format
    hair_color = traits.get('hair_color', 'brown')
    hair_length = traits.get('hair_length', 'medium')
    hair_type = traits.get('hair_type', 'straight')
    
    # Age display based on child's age
    child_age = int(traits.get('child_age', '4'))
    age_display = f"{child_age} year old" if child_age > 0 else "baby"
    
    age_range = story.get('age_range', '3-8')
    is_baby_story = age_range in ['0-1', '0-2']
    if is_baby_story:
        gender_word = "baby boy" if gender == "male" else "baby girl" if gender == "female" else "baby"
    else:
        gender_word = gender_child
    
    # Build child base description for consistent character rendering
    # Use story-specific base_character_override if available
    base_template = story.get('base_character_override', CHILD_BASE_DESC)
    gender_features = "soft round cheeks, cute expression" if gender == 'female' else "cute expression"
    
    child_base_desc = base_template.format(
        gender_child=gender_child,
        age_display=age_display,
        hair_desc=hair_desc,
        hair_color=hair_color,
        hair_length=hair_length,
        hair_type=hair_type,
        skin_tone=skin_tone,
        eye_desc=eye_desc,
        gender_features=gender_features
    )
    
    cover_tmpl = story['cover_template']
    if '{eye_desc}' in cover_tmpl:
        hair_value = hair_desc
    else:
        hair_value = hair_desc + ", " + eye_desc
    if is_baby_story:
        cover_style = "clean illustration only, pure artwork, professional children's book quality"
    else:
        cover_style = "NO text, NO watermark, NO signature, NO logo, NO artist name, NO handwriting, NO calligraphy, clean illustration only"
    
    prompt = cover_tmpl.format(
        name=child_name,
        gender_child=gender_child,
        gender_child_es=gender_child_es,
        gender_word=gender_word,
        hair_desc=hair_value,
        hair_color=hair_color,
        hair_length=hair_length,
        hair_type=hair_type,
        hair_action=hair_action,
        eye_desc=eye_desc,
        age_display=age_display,
        skin_tone=skin_tone,
        style=cover_style,
        spark_desc=SPARK_DESC.format(gender_word=gender_word),
        mama_dragon_desc=MAMA_DRAGON_DESC,
        puppy_desc=PUPPY_DESC,
        kitten_desc=KITTEN_DESC,
        lila_desc=LILA_DESC.format(gender_word=gender_word),
        bunny_desc=BUNNY_DESC,
        guardian_light_desc=GUARDIAN_LIGHT_DESC,
        dog_forever_desc=DOG_FOREVER_DESC.format(gender_word=gender_word),
        child_base_desc=child_base_desc,
        **gender_endings
    )
    
    if is_baby_story:
        prompt = adapt_baby_pose_for_age(prompt, child_age)
    
    prompt = enforce_gender_clothing(prompt, gender)
    
    if hair_length == 'very_little' and 'STRICT:' in prompt:
        if is_baby_story:
            prompt = prompt.replace('STRICT:', 'STRICT: Baby has very short thin wispy hair visible on smooth round head,')
        else:
            prompt = prompt.replace('STRICT:', 'STRICT: Child has very short thin wispy hair visible on head,')
    
    return prompt


def adapt_baby_pose_for_age(prompt: str, child_age: int) -> str:
    """Adapt baby poses in prompts based on child's age.
    - Age 0 (0-12 months): ONLY lying down, sitting supported, or crawling. NEVER standing/walking.
    - Age 1 (1 year): Can sit, stand, walk unsteadily
    - Age 2 (2 years): Walks and stands confidently
    
    New prompts use 'POSE: The {gender_word} is sitting/lying...' structure.
    """
    if child_age == 0:
        prompt += " CRITICAL: This is a 0-12 month old baby who CANNOT stand or walk. The baby MUST ONLY be lying down, sitting supported, or crawling on belly. NEVER standing upright, NEVER walking, NEVER on feet."
    return prompt


def enforce_gender_clothing(prompt: str, gender: str) -> str:
    if gender == 'male':
        rule = " GENDER-CLOTHING: This is a BOY - MUST wear masculine clothing ONLY (t-shirt, shorts, overalls, pants, suspenders, sneakers). Absolutely NO bows, NO ribbons, NO dresses, NO skirts, NO feminine accessories, NO pink outfits."
    elif gender == 'female':
        rule = " GENDER-CLOTHING: This is a GIRL - should wear feminine clothing (dress, skirt, bow, ribbons, cute accessories allowed). Girly colors and styles appropriate."
    else:
        return prompt
    if 'STRICT:' in prompt:
        prompt = prompt.replace('STRICT:', 'STRICT:' + rule)
    else:
        prompt += rule
    return prompt


def get_scene_prompts(story_id: str, child_name: str, gender: str, traits: dict) -> list:
    """Get only scene prompts for image generation."""
    story = STORIES.get(story_id)
    if not story:
        raise ValueError(f"Story not found: {story_id}")
    
    hair_desc = get_hair_description(traits)
    eye_desc = get_eye_description(traits)
    hair_action = get_hair_action(traits)
    skin_tone = get_skin_tone(traits.get('skin_tone', 'light'))
    gender_child = get_gender_child(gender)
    gender_child_es = get_gender_child_es(gender)
    gender_endings = get_spanish_gender_endings(gender)
    
    age_range = story.get('age_range', '0-1')
    is_baby_story = age_range in ['0-1', '0-2']
    default_age = '1' if is_baby_story else '5'
    child_age = int(traits.get('child_age', default_age))
    
    if is_baby_story:
        gender_word = "baby boy" if gender == "male" else "baby girl" if gender == "female" else "baby"
    else:
        gender_word = gender_child
    
    # Extract individual hair components for new prompt format
    hair_color = traits.get('hair_color', 'brown')
    hair_length = traits.get('hair_length', 'medium')
    hair_type = traits.get('hair_type', 'straight')
    
    # Age display based on child's age
    age_display = f"{child_age} year old" if child_age > 0 else "baby"
    
    # Build child base description for consistent character rendering
    # Use story-specific base_character_override if available
    base_template = story.get('base_character_override', CHILD_BASE_DESC)
    gender_features = "soft round cheeks, cute expression" if gender == 'female' else "cute expression"
    
    child_base_desc = base_template.format(
        gender_child=gender_child,
        age_display=age_display,
        hair_desc=hair_desc,
        hair_color=hair_color,
        hair_length=hair_length,
        hair_type=hair_type,
        skin_tone=skin_tone,
        eye_desc=eye_desc,
        gender_features=gender_features
    )
    
    prompts = []
    is_toddler = is_baby_story and child_age >= 1
    for page in story['pages']:
        if is_toddler and 'scene_template_toddler' in page:
            template = page['scene_template_toddler']
        else:
            template = page['scene_template']
        if '{eye_desc}' in template:
            hair_value = hair_desc
        else:
            hair_value = hair_desc + ", " + eye_desc
        if is_baby_story:
            scene_style = "clean illustration only, pure artwork, professional children's book quality"
        else:
            scene_style = "NO text, NO watermark, NO signature, NO logo, NO artist name, NO handwriting, NO calligraphy, clean illustration only"
        candle_plural = "s" if child_age != 1 else ""
        candle_plural_en = "s" if child_age != 1 else ""
        prompt = template.format(
            name=child_name,
            gender_child=gender_child,
            gender_child_es=gender_child_es,
            gender_word=gender_word,
            hair_desc=hair_value,
            hair_color=hair_color,
            hair_length=hair_length,
            hair_type=hair_type,
            eye_desc=eye_desc,
            age_display=age_display,
            hair_action=hair_action,
            skin_tone=skin_tone,
            style=scene_style,
            child_age=child_age,
            candle_plural=candle_plural,
            candle_plural_en=candle_plural_en,
            spark_desc=SPARK_DESC.format(gender_word=gender_word),
            mama_dragon_desc=MAMA_DRAGON_DESC,
            puppy_desc=PUPPY_DESC,
            kitten_desc=KITTEN_DESC,
            lila_desc=LILA_DESC.format(gender_word=gender_word),
            bunny_desc=BUNNY_DESC,
            guardian_light_desc=GUARDIAN_LIGHT_DESC,
            dog_forever_desc=DOG_FOREVER_DESC.format(gender_word=gender_word),
            child_base_desc=child_base_desc,
            **gender_endings
        )
        
        if is_baby_story:
            prompt = adapt_baby_pose_for_age(prompt, child_age)
        
        prompt = enforce_gender_clothing(prompt, gender)
        
        if hair_length == 'very_little' and 'STRICT:' in prompt:
            if is_baby_story:
                prompt = prompt.replace('STRICT:', 'STRICT: Baby has very short thin wispy hair visible on smooth round head,')
            else:
                prompt = prompt.replace('STRICT:', 'STRICT: Child has very short thin wispy hair visible on head,')
        
        prompts.append(prompt)
    
    return prompts


def get_closing_prompt(story_id: str, child_name: str, gender: str, traits: dict) -> str:
    """Get the closing illustration prompt for stories with closing_template."""
    story = STORIES.get(story_id)
    if not story or 'closing_template' not in story:
        return None
    
    hair_desc = get_hair_description(traits)
    eye_desc = get_eye_description(traits)
    hair_action = get_hair_action(traits)
    skin_tone = get_skin_tone(traits.get('skin_tone', 'light'))
    gender_child = get_gender_child(gender)
    
    age_range = story.get('age_range', '0-1')
    is_baby_story = age_range in ['0-1', '0-2']
    if is_baby_story:
        gender_word = "baby boy" if gender == "male" else "baby girl" if gender == "female" else "baby"
    else:
        gender_word = gender_child
    
    default_age = '1' if is_baby_story else '5'
    child_age = int(traits.get('child_age', default_age))
    age_display = f"{child_age} year old" if child_age > 0 else "baby"
    
    is_toddler = is_baby_story and child_age >= 1
    if is_toddler and 'closing_template_toddler' in story:
        closing_tmpl = story['closing_template_toddler']
    else:
        closing_tmpl = story['closing_template']
    if '{eye_desc}' in closing_tmpl:
        closing_hair_value = hair_desc
    else:
        closing_hair_value = hair_desc + ", " + eye_desc
    closing_style = "NO text, NO watermark, NO signature, NO logo, NO artist name, NO handwriting, NO calligraphy, clean illustration only"
    prompt = closing_tmpl.format(
        name=child_name,
        gender_child=gender_child,
        gender_word=gender_word,
        age_display=age_display,
        hair_desc=closing_hair_value,
        eye_desc=eye_desc,
        hair_action=hair_action,
        skin_tone=skin_tone,
        style=closing_style,
        spark_desc=SPARK_DESC.format(gender_word=gender_word),
        mama_dragon_desc=MAMA_DRAGON_DESC,
        puppy_desc=PUPPY_DESC,
        kitten_desc=KITTEN_DESC,
        lila_desc=LILA_DESC.format(gender_word=gender_word),
        bunny_desc=BUNNY_DESC,
        guardian_light_desc=GUARDIAN_LIGHT_DESC,
        dog_forever_desc=DOG_FOREVER_DESC.format(gender_word=gender_word)
    )
    
    if is_baby_story:
        prompt = adapt_baby_pose_for_age(prompt, child_age)
    
    prompt = enforce_gender_clothing(prompt, gender)
    
    return prompt


def get_closing_message(story_id: str, child_name: str, lang: str = 'es') -> str:
    """Get the closing message for a story."""
    story = STORIES.get(story_id)
    if not story:
        return None
    msg_key = f'closing_message_{lang}'
    msg = story.get(msg_key, story.get('closing_message_es', ''))
    if not msg:
        return None
    return msg.format(name=child_name)


def get_story_text(story_id: str, child_name: str, gender: str = 'neutral', lang: str = 'es', **extra_vars) -> list:
    """Get only the story text pages."""
    story = STORIES.get(story_id)
    if not story:
        raise ValueError(f"Story not found: {story_id}")
    
    gender_child = get_gender_child(gender)
    gender_child_es = get_gender_child_es(gender)
    gender_endings = get_spanish_gender_endings(gender)
    
    is_illustrated_book = story.get('use_fixed_scenes', False)
    source_pages = story.get('content_pages', []) if is_illustrated_book else story.get('pages', [])
    
    text_layout = story.get('text_layout', 'single')
    
    texts = []
    for page in source_pages:
        if text_layout == 'split':
            above_key = f'text_above_{lang}'
            below_key = f'text_below_{lang}'
            text_above = page.get(above_key, '').format(
                name=child_name,
                gender_child=gender_child,
                gender_child_es=gender_child_es,
                **gender_endings,
                **extra_vars
            ) if page.get(above_key) else ''
            text_below = page.get(below_key, '').format(
                name=child_name,
                gender_child=gender_child,
                gender_child_es=gender_child_es,
                **gender_endings,
                **extra_vars
            ) if page.get(below_key) else ''
            texts.append({
                'text_above': text_above,
                'text_below': text_below,
                'text': text_above + ' ' + text_below
            })
        else:
            text_key = 'text_es' if lang == 'es' else 'text_en'
            formatted_text = page[text_key].format(
                name=child_name, 
                gender_child=gender_child,
                gender_child_es=gender_child_es,
                **gender_endings,
                **extra_vars
            )
            texts.append(formatted_text)
    
    return texts


FIXED_STORIES = STORIES

def get_fixed_story(story_key, child_name, child_gender):
    """Legacy function - returns story data for older code."""
    story = STORIES.get(story_key)
    if not story:
        return None
    
    lang = 'es'
    lo_la = "la" if child_gender == "female" else "lo"
    title = story.get('title_es', story.get('title_en', '')).format(name=child_name, lo_la=lo_la)
    
    pages = {}
    for i, page in enumerate(story['pages'], 1):
        text_key = 'text_es' if lang == 'es' else 'text_en'
        pages[f'page_{i}'] = page[text_key].format(name=child_name)
    
    return {
        'title': title,
        'pages': pages,
        'age_range': story.get('age_range', '2-4')
    }


def build_illustration_prompt(story_key, scene_key, traits, gender):
    """Legacy function - builds illustration prompt."""
    story = STORIES.get(story_key)
    if not story:
        return None
    
    scene_num = int(scene_key.split('_')[1]) if '_' in scene_key else 1
    if scene_num > len(story['pages']):
        return None
    
    page = story['pages'][scene_num - 1]
    hair_desc = get_hair_description(traits)
    skin_tone = get_skin_tone(traits.get('skin_tone', 'light'))
    gender_child = get_gender_child(gender)
    
    eye_desc = get_eye_description(traits)
    gender_word = "boy" if gender == "male" else "girl" if gender == "female" else "child"
    child_age = int(traits.get('child_age', '5'))
    age_display = f"{child_age} year old" if child_age and child_age > 0 else "4-5 year old"
    gender_child_es = "niño" if gender == "male" else "niña" if gender == "female" else "niño/a"
    hair_color = traits.get('hair_color', 'brown')
    hair_length = traits.get('hair_length', 'medium')
    hair_type = traits.get('hair_type', 'straight')
    child_name = traits.get('child_name', 'child')

    has_eye_desc = '{eye_desc}' in page['scene_template']
    scene_hair_desc = hair_desc if has_eye_desc else hair_desc + ", " + eye_desc
    legacy_style = "NO text, NO watermark, NO signature, NO logo, NO artist name, NO handwriting, NO calligraphy, clean illustration only"
    gender_endings = get_spanish_gender_endings(gender)
    
    return page['scene_template'].format(
        name=child_name,
        gender_child=gender_child,
        gender_child_es=gender_child_es,
        gender_word=gender_word,
        hair_desc=scene_hair_desc,
        hair_color=hair_color,
        hair_length=hair_length,
        hair_type=hair_type,
        eye_desc=eye_desc,
        age_display=age_display,
        hair_action=get_hair_action(traits),
        skin_tone=skin_tone,
        style=legacy_style,
        spark_desc=SPARK_DESC.format(gender_word=gender_word),
        mama_dragon_desc=MAMA_DRAGON_DESC,
        puppy_desc=PUPPY_DESC,
        kitten_desc=KITTEN_DESC,
        lila_desc=LILA_DESC.format(gender_word=gender_word),
        bunny_desc=BUNNY_DESC,
        guardian_light_desc=GUARDIAN_LIGHT_DESC,
        dog_forever_desc=DOG_FOREVER_DESC.format(gender_word=gender_word),
        skin_desc=f"{skin_tone} skin",
        **gender_endings
    )


def get_all_scene_keys():
    """Legacy function - returns scene keys for 6-scene stories."""
    return ['scene_1', 'scene_2', 'scene_3', 'scene_4', 'scene_5', 'scene_6']


def get_static_illustrations(story_id: str) -> dict:
    """
    Check if static illustrations exist for a story and return their paths.
    Static illustrations are stored in static/story_illustrations/{story_id}/
    
    Returns dict with:
        - has_static: bool - True if static illustrations are available
        - cover: str - path to cover image (or None)
        - scenes: list - paths to scene images
        - character_preview: str - path to character preview (or None)
    """
    import os
    
    base_path = f'static/story_illustrations/{story_id}'
    
    if not os.path.exists(base_path):
        return {'has_static': False, 'cover': None, 'scenes': [], 'character_preview': None}
    
    story_config = STORIES.get(story_id, {})
    pages = story_config.get('pages', [])
    num_scenes = len(pages) if pages else 5
    
    cover_path = f'{base_path}/cover.png'
    if not os.path.exists(cover_path):
        cover_path = f'{base_path}/cover.jpg'
    if not os.path.exists(cover_path):
        cover_path = None
    
    char_preview_path = f'{base_path}/character_preview.png'
    if not os.path.exists(char_preview_path):
        char_preview_path = f'{base_path}/character_preview.jpg'
    if not os.path.exists(char_preview_path):
        char_preview_path = None
    
    scenes = []
    for i in range(1, num_scenes + 1):
        scene_path = f'{base_path}/scene_{i}.png'
        if not os.path.exists(scene_path):
            scene_path = f'{base_path}/scene_{i}.jpg'
        if os.path.exists(scene_path):
            scenes.append(scene_path)
        else:
            scenes.append(None)
    
    all_scenes_exist = all(s is not None for s in scenes)
    has_static = all_scenes_exist and (cover_path is not None or char_preview_path is not None)
    
    return {
        'has_static': has_static,
        'cover': cover_path,
        'scenes': scenes,
        'character_preview': char_preview_path
    }


def use_static_or_generate(story_id: str):
    """
    Determine if we should use static illustrations or generate new ones.
    Returns tuple: (use_static: bool, static_data: dict)
    """
    static_data = get_static_illustrations(story_id)
    return static_data['has_static'], static_data
