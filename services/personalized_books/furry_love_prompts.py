# Tú y tu Amor Peludo - Baby Story Prompts (REESCRITO May 2026)
# 19 scenes + closing + covers
# Story: A baby arrives home where a dog already lives — newborn to 14 months
#
# FLUX 2 Dev with TWO reference images:
#   1. Human preview: detailed character description → reference image 1
#   2. Pet preview: detailed pet description → reference image 2
#   3. Scenes: FLUX 2 Dev takes BOTH references → prompts bind roles explicitly
#
# Prompt schema (updated May 2026):
#   STRICT (at top) → HUMAN (who + WHERE) → PET (who + WHERE) →
#   TOGETHER (one spatial sentence) → SETTING → ATMOSPHERE → {style}
#
# Rules:
#   - guidance_scale=3.5, num_inference_steps=28, aspect_ratio=3:4
#   - Keep prompts concise — FLUX 2 Dev loses focus beyond ~280 words
#   - Style: Disney Pixar 3D, NO watercolor
#   - Baby grows from newborn (scenes 1-4) to 14 months (scene 19)
#   - STRICT always at the TOP (FLUX weights early tokens more)
#   - NO ACTION section (was causing triple-description → duplicate characters)
#   - Each character described ONCE with a clear spatial anchor
#   -  injected for scenes 10+ via build_scene_prompt()
#   - {baby_bow} injected for girl babies in scenes 14+ via build_scene_prompt()
#   - Age progression: scenes 1-4 newborn → 5-6 two/three months →
#     7-9 four/five months → 10-11 seven/eight months → 12-13 nine/ten months →
#     14-15 eleven months → 16 twelve months (first steps!) →
#     17-18 thirteen months → 19 fourteen months → closing sixteen months
#
# AGE CONTINUITY RULE (scenes 16 onward):
#   Scene 16 = 12 months (first steps, very small toddler, wobbly)
#   Scene 17 = 13 months (slightly more confident, same small build)
#   Scene 18 = 13 months (nap after play, same size as 17)
#   Scene 19 = 14 months (a touch steadier, still small toddler)
#   Closing  = 16 months (sleeping in toddler bed, small toddler)
#   → NEVER skip to a large child and then back to small

STYLE_BASE = "Disney Pixar 3D style, soft warm golden lighting, tender emotional atmosphere, WIDE SHOT full body from head to feet, characters occupy 40% of frame, cozy home environment visible, clean illustration only. STRICT: All babies MUST wear a diaper or onesie or pajamas — NEVER naked, NEVER without clothing."

FURRY_LOVE_SCENES = [
    {
        "id": 1,
        "text_es": "Algo mágico estaba a punto de suceder. {pet_name} lo sentía en el aire. La casa olía diferente: a pintura fresca, a ropa suavecita, a algo que {pet_name} no sabía nombrar pero que hacía que su cola se moviera despacito, como si guardara un secreto.",
        "text_en": "Something magical was about to happen. {pet_name} could feel it in the air. The house smelled different: of fresh paint, soft fabrics, of something {pet_name} couldn't name but that made their tail wag slowly, as if keeping a secret.",
        "prompt": "Disney Pixar 3D style illustration. STRICT: exactly ONE dog alone in this scene, no human child present, nursery not yet occupied, the {gender_word} has not arrived yet. PET: {pet_desc}, sitting at the nursery doorway at CENTER of frame, head tilted curiously, nose raised sniffing the air, tail slowly wagging, large curious eyes taking in the new room. SETTING: Freshly painted nursery WIDE VIEW, a white crib with a star mobile, pastel walls, soft blankets folded on the mattress, paint cans still nearby, warm sunlight through sheer curtains. ATMOSPHERE: Quiet anticipation, warm golden afternoon light, the house ready and waiting, a secret held in the air. {style}",
        "text_position": "split"
    },
    {
        "id": 2,
        "text_es": "Y entonces, un día, la puerta se abrió. {pet_name} escuchó risas, pasos suaves y... un sonido nuevo. Pequeñito. Dulce. Un suspiro diminuto que llenó toda la casa. Los ojos de {pet_name} se abrieron enormes: ¡habían traído a {name} a casa!",
        "text_en": "And then, one day, the door opened. {pet_name} heard laughter, soft footsteps and... a new sound. Tiny. Sweet. A little sigh that filled the whole house. {pet_name}'s eyes went wide: they had brought {name} home!",
        "prompt": "Disney Pixar 3D style illustration. STRICT: exactly ONE newborn baby in the stroller at CENTER, exactly ONE dog beside the stroller at LEFT, only ONE adult hand visible on the handle above, no full adult body. HUMAN: A tiny newborn {gender_word} with {eye_desc} eyes{glasses_desc}, face barely visible peeking from a soft white blanket inside the stroller at CENTER of frame. PET: {pet_desc}, sitting on the floor at LEFT of the stroller, looking up at the tiny bundle with wide curious eyes, ears perked forward, tail frozen mid-wag. TOGETHER: the dog sits faithfully beside the stroller as it crosses the threshold, only a parent's hand visible on the handle above. SETTING: Home entryway WIDE VIEW, front door wide open with warm sunlight streaming in, cozy living room beyond, welcome mat beneath the stroller. ATMOSPHERE: Emotional first arrival, warm golden doorway light, joy and wonder, a brand new beginning. {style}",
        "text_position": "split"
    },
    {
        "id": 3,
        "text_es": "{pet_name} se acercó despacito, con las patitas suaves sobre el suelo. Puso su nariz cerca de {name}, muy cerca, y olió. Olía a leche, a talco, a algo que {pet_name} decidió en ese instante que iba a proteger para siempre.",
        "text_en": "{pet_name} approached slowly, soft paws on the floor. Nose came close to {name}, very close, and sniffed. It smelled of milk, of powder, of something {pet_name} decided in that very instant to protect forever.",
        "prompt": "Disney Pixar 3D style illustration. STRICT: exactly ONE tiny newborn baby at CENTER of frame in bassinet, exactly ONE dog at LEFT with front paws on the bassinet edge, no extra characters, sacred gentle first meeting. HUMAN: A tiny newborn {gender_word} with {eye_desc} eyes{glasses_desc}, lying in a soft bassinet at CENTER of frame, wrapped in a white blanket, eyes barely open, tiny fingers loosely curled near face. PET: {pet_desc}, standing at LEFT with front paws on the bassinet edge, nose gently approaching the baby's tiny fingers, eyes full of tenderness, completely still. TOGETHER: the dog's nose almost touches the newborn's curled fingers across the bassinet rail, their first gentle wordless meeting. SETTING: Living room WIDE VIEW, soft couch nearby, warm afternoon sunlight filtering through curtains, cozy gentle atmosphere. ATMOSPHERE: Sacred first meeting, tender wonder, warm soft golden light, the start of a lifelong bond. {style}",
        "text_position": "split"
    },
    {
        "id": 4,
        "text_es": "Esa primera noche, {pet_name} se echó junto a la cuna de {name}. No se movió ni una vez. Cada vez que {name} hacía un ruidito, {pet_name} levantaba una oreja. \"Aquí estoy\", decía su mirada. \"Aquí estaré siempre.\"",
        "text_en": "That first night, {pet_name} lay down beside {name}'s crib. Didn't move once. Every time {name} made a little sound, {pet_name} raised one ear. \"I'm here,\" said those eyes. \"I'll always be here.\"",
        "prompt": "Disney Pixar 3D style illustration. STRICT: exactly ONE sleeping newborn in white crib at CENTER, exactly ONE dog lying on the floor directly beside the crib, nighttime nursery, no extra characters, protective vigil scene. HUMAN: A tiny sleeping newborn {gender_word} with {eye_desc} eyes{glasses_desc}, lying in a white crib at CENTER of frame, peaceful face, tiny fists, soft blanket tucked around. PET: {pet_desc}, lying on the nursery floor right beside the crib at FRONT of frame, chin resting on front paws, one ear raised alertly, watchful open eyes, body curled in devoted protective posture. TOGETHER: the dog lies faithfully on the floor beneath the crib rail, maintaining a quiet vigil over the sleeping newborn all through the night. SETTING: Nursery at night WIDE VIEW, soft moonlight through window, star-shaped nightlight glowing warm orange, mobile with stars above the crib, peaceful deep shadows. ATMOSPHERE: Faithful protection, soft blue moonlight and warm nightlight, serene safety, eternal devotion. {style}",
        "text_position": "split"
    },
    {
        "id": 5,
        "text_es": "Pasaron los días y una mañana, mientras {pet_name} observaba la cuna, sucedió algo increíble. {name} abrió bien los ojos, miró directamente a {pet_name}... ¡y sonrió! La primera sonrisa de {name} fue para {pet_name}.",
        "text_en": "Days passed and one morning, while {pet_name} watched the crib, something incredible happened. {name} opened their eyes wide, looked straight at {pet_name}... and smiled! {name}'s first smile was for {pet_name}.",
        "prompt": "Disney Pixar 3D style illustration. STRICT: exactly ONE 2-month-old baby in crib at CENTER of frame, exactly ONE dog at LEFT standing beside the crib, the big gummy smile is the hero of this scene, no extra characters. HUMAN: A 2-month-old {gender_word} with {eye_desc} eyes{glasses_desc}, lying in the crib at CENTER of frame wearing a soft white onesie, eyes wide open locked on the dog, a huge gummy smile spreading across tiny face, arms reaching upward. PET: {pet_desc}, standing at LEFT beside the crib with front paws on the edge, gazing at the smiling baby with pure adoration, tail wagging excitedly, eyes shining with joy. TOGETHER: baby and dog share their first magical smile across the crib rail, eyes locked in mutual delight. SETTING: Nursery morning WIDE VIEW, warm sunlight streaming through window, cheerful pastel walls, mobile turning gently above the crib. ATMOSPHERE: First magical smile, pure joy, warm golden morning light, a milestone written in the heart. {style}",
        "text_position": "split"
    },
    {
        "id": 6,
        "text_es": "{pet_name} desapareció un momento y volvió con su juguete más preciado. Lo dejó suavemente junto a {name}. \"Esto es lo que más quiero\", parecía decir {pet_name}. \"Y ahora es tuyo también, {name}.\"",
        "text_en": "{pet_name} disappeared for a moment and came back with their most treasured toy. Gently placed it next to {name}. \"This is what I love most,\" {pet_name} seemed to say. \"And now it's yours too, {name}.\"",
        "prompt": "Disney Pixar 3D style illustration. STRICT: exactly ONE 3-month-old baby on play mat at CENTER, exactly ONE dog at LEFT having just placed a toy, heartwarming sharing scene, no extra characters. HUMAN: A 3-month-old {gender_word} with {eye_desc} eyes{glasses_desc}, lying on a soft play mat at CENTER of frame, wearing a soft yellow onesie, both hands reaching curiously toward a worn stuffed toy, eyes wide with wonder. PET: {pet_desc}, lying at LEFT of the play mat, having just gently nudged a beloved stuffed toy close to the baby, gazing at the baby with proud satisfied eyes, tail gently wagging. TOGETHER: the dog's nose nudges the toy a final inch closer to the baby's outstretched reaching hands on the mat. SETTING: Living room floor WIDE VIEW, colorful play mat with gentle patterns, toys scattered around the edges, warm afternoon sunlight, cozy home. ATMOSPHERE: Generous tender love, warm soft afternoon light, the gift of sharing, first friendship. {style}",
        "text_position": "split"
    },
    {
        "id": 7,
        "text_es": "Un día, las manitas curiosas de {name} descubrieron algo suave y tibio: ¡el pelaje de {pet_name}! {name} agarró un mechón y no quiso soltar. {pet_name} se quedó quieto, feliz, con los ojos entrecerrados de puro gusto.",
        "text_en": "One day, {name}'s curious little hands discovered something soft and warm: {pet_name}'s fur! {name} grabbed a tuft and wouldn't let go. {pet_name} stayed perfectly still, happy, eyes half-closed with pure contentment.",
        "prompt": "Disney Pixar 3D style illustration. STRICT: exactly ONE 4-month-old baby at CENTER propped on pillows, exactly ONE dog at RIGHT lying very close, intimate gentle tactile scene, no extra characters. HUMAN: A 4-month-old {gender_word} with {eye_desc} eyes{glasses_desc}, propped up on soft pillows at CENTER of frame, wearing a light green onesie, one tiny hand buried in the dog's fur, face wide-eyed with wonder and delight at the texture. PET: {pet_desc}, lying RIGHT beside the baby on the soft surface, eyes half-closed with contentment, completely still and patient, ears relaxed, completely trusting the baby's touch. TOGETHER: the baby's tiny fist clings to the dog's soft fur as both rest side by side, discovering each other through touch. SETTING: Soft couch area WIDE VIEW, plush pillows supporting the baby, warm blanket across their laps, soft afternoon light on both of them. ATMOSPHERE: Discovery and deep trust, warm golden tones, intimate gentle wonder, tactile first connection. {style}",
        "text_position": "split"
    },
    {
        "id": 8,
        "text_es": "¡La hora del baño! {name} chapoteaba y reía mientras el agua salpicaba por todos lados. {pet_name} observaba desde la puerta con la cabeza ladeada. Una ola de agua le mojó la nariz a {pet_name}. ¡Y las risas de {name} fueron aún más grandes!",
        "text_en": "Bath time! {name} splashed and laughed as water went everywhere. {pet_name} watched from the doorway with a tilted head. A wave of water splashed {pet_name}'s nose. And {name}'s laughter grew even bigger!",
        "prompt": "Disney Pixar 3D style illustration. STRICT: exactly ONE 5-month-old baby in the bathtub at CENTER wearing only a diaper, exactly ONE dog at LEFT in the bathroom doorway, chaotic splash scene, no extra characters. HUMAN: A 5-month-old {gender_word} with {eye_desc} eyes{glasses_desc}, sitting in a small baby bathtub at CENTER of frame wearing only a diaper, splashing water with both hands in pure joy, mouth open laughing, water droplets flying in all directions. PET: {pet_desc}, standing in the bathroom doorway at LEFT of frame, head tilted sideways, nose wet from a flying water droplet, one paw raised in surprise, comically startled but amused expression. TOGETHER: a splash of bath water just hit the dog's nose as the laughing baby splashes from the tub across the distance. SETTING: Bright bathroom WIDE VIEW, small baby tub with bubbles, rubber duck on the edge, water droplets catching the light, folded towel on the rack. ATMOSPHERE: Playful explosive joy, bright cheerful bathroom light, water droplets sparkling like diamonds, pure funny chaos. {style}",
        "text_position": "split"
    },
    {
        "id": 9,
        "text_es": "Durante el tiempo boca abajo, {name} levantó la cabecita por primera vez. ¿Y qué vio? A {pet_name}, echado en el suelo, nariz con nariz. {name} y {pet_name} se miraron durante un largo momento mágico, como si se contaran secretos sin palabras.",
        "text_en": "During tummy time, {name} lifted their little head for the first time. And what did they see? {pet_name}, lying on the floor, nose to nose. {name} and {pet_name} looked at each other for a long magical moment, as if sharing secrets without words.",
        "prompt": "Disney Pixar 3D style illustration. STRICT: exactly ONE 4-month-old baby at LEFT doing tummy time, exactly ONE dog at RIGHT lying flat face-to-face on the floor, floor-level intimate moment, no extra characters. HUMAN: A 4-month-old {gender_word} with {eye_desc} eyes{glasses_desc}, doing tummy time on a soft play mat at LEFT of frame, wearing a mint green onesie, head lifted up proudly for the first time, big curious eyes looking directly at the dog with a tiny smile. PET: {pet_desc}, lying completely flat at RIGHT of frame with chin on the mat, face to face with the baby, nose almost touching the baby's nose, gentle loving eyes returning the gaze, completely still. TOGETHER: baby and dog lie face to face inches apart at floor level, sharing a quiet wordless moment of perfect understanding. SETTING: Living room floor WIDE VIEW, soft play mat, warm sunlight pooling on the floor around them, toys scattered at the edges of the mat. ATMOSPHERE: Magical eye-level connection, warm intimate golden light on both faces, quiet understanding between two souls. {style}",
        "text_position": "split"
    },
    {
        "id": 10,
        "text_es": "¡{name} se movió! Primero fue un balanceo torpe, luego las rodillitas empezaron a funcionar. ¿Hacia dónde fue la primera aventura de {name}? Directo hacia {pet_name}, por supuesto. Siempre hacia {pet_name}.",
        "text_en": "{name} moved! First a wobbly rocking, then the little knees started working. Where did {name}'s first adventure go? Straight toward {pet_name}, of course. Always toward {pet_name}.",
        "prompt": "Disney Pixar 3D style illustration. STRICT: exactly ONE 7-month-old baby crawling at LEFT of frame, exactly ONE dog sitting at RIGHT of frame, baby is crawling determinedly toward the dog, no extra characters, first crawl milestone. HUMAN: A 7-month-old {gender_word} with {eye_desc} eyes{glasses_desc}, crawling on hands and knees at LEFT of frame, wearing a soft blue onesie with tiny white stars, face set with happy determination, heading straight toward the dog. PET: {pet_desc}, sitting at RIGHT of frame facing the crawling baby, tail wagging with intense excitement, front paws doing a happy little dance, bright encouraging expression. TOGETHER: the baby crawls steadily across the carpet directly toward the waiting dog, a clear open path of floor between them. SETTING: Living room WIDE VIEW, soft carpet floor, coffee table in background, warm afternoon light casting a golden path across the room. ATMOSPHERE: First crawl milestone, triumphant joy, warm celebratory golden light, a whole new world within reach. {style}",
        "text_position": "split"
    },
    {
        "id": 11,
        "text_es": "En el jardín, {name} tocó el pasto por primera vez. Era cosquilloso, verde y olía a aventura. {pet_name} corrió en círculos de alegría, trayendo palitos y hojas como regalos. {name} reía y reía y reía.",
        "text_en": "In the garden, {name} touched grass for the first time. It was tickly, green, and smelled like adventure. {pet_name} ran in happy circles, bringing sticks and leaves as gifts. {name} laughed and laughed and laughed.",
        "prompt": "Disney Pixar 3D style illustration. STRICT: exactly ONE 8-month-old baby sitting at CENTER on the garden grass, exactly ONE dog running at RIGHT nearby, outdoor bright garden scene, no extra characters. HUMAN: An 8-month-old {gender_word} with {eye_desc} eyes{glasses_desc}, sitting on green grass at CENTER of frame, wearing a cute orange onesie, both hands pressed into the grass blades with wonder, laughing with mouth open, bare feet pressing into the lawn. PET: {pet_desc}, running playfully at RIGHT of frame with a small stick in mouth, mid-joyful-stride, tail high and happy, looping back toward the baby as a gift delivery. TOGETHER: the dog circles back toward the delighted sitting baby with a stick, both sharing the outdoor joy in different ways. SETTING: Beautiful home garden WIDE VIEW, lush green lawn, colorful flowers at the edges, blue sky with soft fluffy clouds, bright golden sunshine, butterflies dancing in the air. ATMOSPHERE: First outdoor adventure, bright sunny joy, nature wonder, pure happiness. {style}",
        "text_position": "split"
    },
    {
        "id": 12,
        "text_es": "Los días de lluvia eran especiales. {name} y {pet_name} se sentaban juntos frente a la ventana, viendo las gotas resbalarse por el cristal. Afuera todo era gris, pero adentro, juntos, todo era cálido.",
        "text_en": "Rainy days were special. {name} and {pet_name} sat together by the window, watching drops slide down the glass. Outside everything was gray, but inside, together, everything was warm.",
        "prompt": "Disney Pixar 3D style illustration. STRICT: exactly ONE 9-month-old baby at LEFT side of the window seat, exactly ONE dog at RIGHT side of the window seat bodies touching, the dog is clearly much larger and taller than the baby, quiet rainy companionship scene, no extra characters. HUMAN: A 9-month-old {gender_word} with {eye_desc} eyes{glasses_desc}, sitting at LEFT of a wide window seat, wearing a cozy lavender onesie, one tiny hand touching the glass where raindrops slide down outside, peaceful curious expression. PET: {pet_desc}, sitting at RIGHT of the same window seat right beside the baby, bodies gently pressed together, also gazing at the rain, calm and content, a warm solid presence. TOGETHER: baby and dog sit shoulder to shoulder on the window seat, their bodies touching, both watching the rain fall outside in quiet companionship. SETTING: Cozy window seat WIDE VIEW, large window with rain streaming down outside, gray sky beyond, warm interior with a soft blanket, a small glowing lamp nearby. ATMOSPHERE: Cozy rainy day, warmth inside against the gray outside, quiet intimate togetherness, soft lamplight. {style}",
        "text_position": "split"
    },
    {
        "id": 13,
        "text_es": "La hora de la comida era la favorita de {pet_name}. {name} comía con las manos, con la cara, con toda el alma. Y lo que caía al suelo... bueno, {pet_name} siempre estaba listo para \"ayudar a limpiar\". ¡{name} y {pet_name}, el mejor equipo del mundo!",
        "text_en": "Mealtime was {pet_name}'s favorite. {name} ate with hands, with face, with whole heart and soul. And what fell to the floor... well, {pet_name} was always ready to \"help clean up.\" {name} and {pet_name}, the best team in the world!",
        "prompt": "Disney Pixar 3D style illustration. STRICT: exactly ONE 10-month-old baby in high chair elevated at CENTER of frame, exactly ONE dog sitting directly BELOW on the kitchen floor looking up, messy mealtime, no extra characters. HUMAN: A 10-month-old {gender_word} with {eye_desc} eyes{glasses_desc}, sitting in a high chair at CENTER of frame (elevated above floor level), wearing a bib over an onesie, face covered in colorful puree, hands gloriously messy, dropping food over the tray edge with a giggle. PET: {pet_desc}, sitting on the kitchen floor directly below the high chair tray, looking straight up with eager happy expression, tongue out, tail wagging fast, in perfect position to catch falling food. TOGETHER: bits of food drop from the high chair tray above as the dog catches them gleefully below, a perfectly synchronized mealtime partnership. SETTING: Kitchen dining area WIDE VIEW, high chair central in the frame, colorful food on tray and baby face, food bits around the dog on the floor, bright cheerful kitchen in background. ATMOSPHERE: Joyful messy hilarious teamwork, bright kitchen light, comedic warmth. {style}",
        "text_position": "split"
    },
    {
        "id": 14,
        "text_es": "Por las noches, cuando alguien leía un cuento, {name} se recostaba contra {pet_name}. {name} miraba las páginas, {pet_name} miraba a {name}. Y los dos se iban quedando dormidos juntos, en un nido de amor.",
        "text_en": "At night, when someone read a story, {name} leaned against {pet_name}. {name} looked at the pages, {pet_name} looked at {name}. And they both drifted off to sleep together, in a nest of love.",
        "prompt": "Disney Pixar 3D style illustration. STRICT: exactly ONE 11-month-old baby at LEFT of couch, exactly ONE dog at RIGHT of the same couch with baby leaning against it, the dog is much larger than the baby — the baby is small and nestled against the dog's big warm body, cozy evening reading scene, no extra characters. HUMAN: An 11-month-old {gender_word} with {eye_desc} eyes{glasses_desc}{baby_bow}, sitting at LEFT of the couch in soft star-print pajamas, leaning sideways against the dog's warm body, one hand resting on an open picture book, eyes growing heavy and sleepy. PET: {pet_desc}, sitting at RIGHT of the same couch, the baby leaning fully against its warm flank, looking down at the baby with tender sleepy eyes, body warm and perfectly still. TOGETHER: the baby leans their full small weight against the dog's side, both drifting peacefully toward sleep over the open colorful picture book. SETTING: Cozy living room evening WIDE VIEW, soft couch with a warm blanket and cushions, amber lamp casting a soft glow, open picture book with bright illustrations. ATMOSPHERE: Bedtime warmth, drowsy coziness, amber lamplight, drifting into dreams together. {style}",
        "text_position": "split"
    },
    {
        "id": 15,
        "text_es": "Una noche, un trueno enorme sacudió la casa. {name} se asustó y empezó a llorar. Pero {pet_name} se acurrucó más cerca, pegando su cuerpo tibio contra {name}. \"No tengas miedo\", decía el calor de {pet_name}. Y {name} se calmó.",
        "text_en": "One night, a huge thunderclap shook the house. {name} got scared and started crying. But {pet_name} snuggled closer, pressing their warm body against {name}. \"Don't be afraid,\" said {pet_name}'s warmth. And {name} calmed down.",
        "prompt": "Disney Pixar 3D style illustration. STRICT: exactly ONE 11-month-old baby sitting up in crib at CENTER of frame, exactly ONE dog pressed against the outside of the crib at RIGHT, stormy night comfort scene, no extra characters. HUMAN: An 11-month-old {gender_word} with {eye_desc} eyes{glasses_desc}{baby_bow}, sitting up in the crib at CENTER of frame in pajamas, face calming after tears, one hand gripping the crib rail, the other hand reaching through the crib bars to touch the dog. PET: {pet_desc}, pressed against the outside of the crib slats at RIGHT of frame, body touching the bars, head resting near the baby's reaching hand, a warm steady reassuring presence, eyes soft and protective. TOGETHER: the baby's small hand reaches through the crib slats to touch the dog's warm fur on the other side, the contact immediately calming the frightened child. SETTING: Nursery during thunderstorm WIDE VIEW, lightning flash visible through the curtain gap outside, soft nightlight casting warm orange glow inside, rain visible on the window, cozy crib blankets around the baby. ATMOSPHERE: Protection and comfort, dramatic storm outside versus warm nightlight inside, tender reassurance, fear dissolving into safety. {style}",
        "text_position": "split"
    },
    {
        "id": 16,
        "text_es": "Y entonces llegó el día más esperado. {name} se soltó de la mesa, abrió los brazos... ¡y caminó! Uno, dos, tres pasitos tambaleantes. ¿Hacia dónde? Hacia {pet_name}. Los primeros pasos de {name} fueron para llegar a {pet_name}.",
        "text_en": "And then came the most awaited day. {name} let go of the table, opened their arms... and walked! One, two, three wobbly steps. Where to? Toward {pet_name}. {name}'s first steps were to reach {pet_name}.",
        "prompt": "Disney Pixar 3D style illustration. STRICT: exactly ONE 12-month-old small toddler at LEFT of frame taking first unaided steps, exactly ONE dog at RIGHT of frame waiting, no one holding the baby's hands, first walking milestone, no extra characters. HUMAN: A 12-month-old {gender_word} with {eye_desc} eyes{glasses_desc}{baby_bow}, standing freely at LEFT of frame wearing a soft light blue onesie, both arms stretched wide for balance, taking wobbly brave first steps, face radiating pure proud joy. PET: {pet_desc}, sitting at RIGHT of frame facing the toddler, body lowered in a welcoming open posture, tail wagging intensely, eyes bright with excitement, ready to receive the walking baby. TOGETHER: the small toddler takes their very first unaided steps across the open floor directly toward the waiting dog, the distance between them closing with each wobbly step. SETTING: Living room WIDE VIEW, clear open floor space, the coffee table behind where baby just let go, warm golden afternoon sunbeams on the floor. ATMOSPHERE: Epic triumphant milestone, golden celebratory light, a moment that changes everything, pure pride and joy. {style}",
        "text_position": "split"
    },
    {
        "id": 17,
        "text_es": "\"¡Busca, {pet_name}!\" {name} lanzó la pelota con toda su fuerza. La pelota rodó apenas un metro. Pero {pet_name} salió corriendo como si fuera el lanzamiento más épico del mundo, la trajo de vuelta y la dejó a los pies de {name}. Una y otra y otra vez.",
        "text_en": "\"Fetch, {pet_name}!\" {name} threw the ball with all their might. The ball rolled barely three feet. But {pet_name} took off running as if it were the most epic throw in the world, brought it back and placed it at {name}'s feet. Again and again and again.",
        "prompt": "Disney Pixar 3D style illustration. STRICT: exactly ONE 13-month-old toddler standing at RIGHT of frame, exactly ONE dog running at LEFT of frame, ONE small ball held in the dog's mouth only, zero other balls anywhere in the scene, outdoor garden play, no extra characters. HUMAN: A 13-month-old {gender_word} with {eye_desc} eyes{glasses_desc}{baby_bow}, standing at RIGHT of frame on grass, wearing a cheerful red shirt and tiny denim shorts, right arm extended outward having just released the throw, beaming with proud excitement, bare feet on the lawn. PET: {pet_desc}, running at full stride at LEFT of frame heading back toward the toddler, ONE small colorful ball held in mouth, tail raised high and happy, eyes bright with enthusiasm. TOGETHER: the dog races back across the garden carrying the single retrieved ball straight toward the toddler whose arm is still outstretched from the throw. SETTING: Home garden WIDE VIEW, bright green grass, sunny blue sky, colorful flowers and fence in background, golden afternoon light. ATMOSPHERE: Joyful outdoor play, bright sunny energy, pure childhood happiness, the most perfect game. {style}",
        "text_position": "split"
    },
    {
        "id": 18,
        "text_es": "Después de tanto jugar, llegaba el mejor momento del día: la siesta juntos. {name} se acurrucaba contra {pet_name}, una mano sobre su lomo cálido. Y los dos soñaban el mismo sueño: un sueño donde {name} y {pet_name} estaban siempre juntos.",
        "text_en": "After all that playing came the best moment of the day: nap time together. {name} curled up against {pet_name}, one hand on that warm back. And they both dreamed the same dream: a dream where {name} and {pet_name} were always together.",
        "prompt": "Disney Pixar 3D style illustration. STRICT: exactly ONE 13-month-old toddler sleeping at LEFT of rug, exactly ONE dog sleeping at RIGHT of rug, both clearly SEPARATE beings with distinct features, the child has smooth human skin and human face, the dog has canine fur and canine face, no merging, no extra characters. HUMAN: A 13-month-old {gender_word} with {eye_desc} eyes{glasses_desc}{baby_bow}, sleeping peacefully at LEFT of a soft rug, wearing a red shirt and tiny shorts, one small hand resting gently on the dog's back, angelic peaceful face with smooth human skin and human features. PET: {pet_desc}, sleeping at RIGHT of the same rug, body curved protectively close to the toddler, head resting near the toddler's head, eyes closed, clearly canine with fur and animal features, a separate beloved animal. TOGETHER: toddler and dog nap side by side on the soft rug in the afternoon sun, the child's small hand draped across the dog's back in peaceful sleep. SETTING: Sunlit living room floor WIDE VIEW, soft rug, warm afternoon sunlight making golden patches through the window, cozy pillows nearby. ATMOSPHERE: Perfect peaceful nap, warm golden afternoon light, serene love, two hearts dreaming the same dream. {style}",
        "text_position": "split"
    },
    {
        "id": 19,
        "text_es": "Hoy {name} y {pet_name} caminan juntos por el jardín. {name} da pasitos seguros, señala las flores, las mariposas, las nubes. Y le cuenta secretos a {pet_name} al oído. {pet_name} escucha cada palabra como si fuera la más importante del universo. Porque la historia de {name} y {pet_name} no tiene final. Esta historia apenas comienza.",
        "text_en": "Today {name} and {pet_name} walk together through the garden. {name} takes steady little steps, pointing at the flowers, the butterflies, the clouds. And whispers secrets in {pet_name}'s ear. {pet_name} listens to every word as if it were the most important in the universe. Because the story of {name} and {pet_name} has no ending. This story is just beginning.",
        "prompt": "Disney Pixar 3D style illustration. STRICT: exactly ONE 14-month-old small toddler walking at CENTER of garden path, exactly ONE dog walking at LEFT beside the toddler matching their pace, outdoor golden hour, no extra characters. HUMAN: A 14-month-old {gender_word} with {eye_desc} eyes{glasses_desc}{baby_bow}, walking with steady small toddler steps at CENTER of a garden path, wearing a cheerful yellow shirt and soft blue pants, one hand resting lightly on the dog's back for balance, looking upward at the sky with a wide joyful smile. PET: {pet_desc}, walking slowly and faithfully at LEFT beside the toddler, matching each small step, looking up at the child with adoring proud eyes, tail wagging gently, a steady loving companion. TOGETHER: toddler and dog walk forward side by side along the garden path into the golden horizon, into a future full of adventures together. SETTING: Beautiful home garden at golden hour WIDE VIEW, lush green grass, colorful flowers in bloom, butterflies around them, a garden path leading forward, warm golden sunset sky with soft pink clouds. ATMOSPHERE: Hopeful open ending, warm golden hour light, endless possibilities ahead, faithful love and companionship, the story just beginning. {style}",
        "text_position": "split"
    }
]

CLOSING_SCENE = {
    "id": 20,
    "prompt": "Disney Pixar 3D style illustration. STRICT: exactly ONE 16-month-old toddler asleep in toddler bed at CENTER of frame, exactly ONE dog asleep on the floor right beside the bed, peaceful nighttime scene, no extra characters. HUMAN: A 16-month-old {gender_word} with {eye_desc} eyes{glasses_desc}{baby_bow}, sleeping peacefully in a small toddler bed at CENTER of frame, a star-patterned blanket tucked snugly around them, one tiny arm dangling over the bed edge reaching down toward the dog, peaceful smile on face. PET: {pet_desc}, sleeping on the floor right beside the bed, head resting close to the dangling hand, one paw touching the bed frame, protective even in sleep. TOGETHER: the toddler's small hand reaches down in sleep toward the dog lying faithfully on the floor below, their bond unbreakable even in dreams. SETTING: Cozy bedroom at night WIDE VIEW, warm nightlight casting a soft golden glow, stars visible through the window, soft pillows, peaceful shadows. ATMOSPHERE: Perfect peaceful ending, warm nightlight glow, eternal faithful love, a story without end. {style}",
    "text_position": "none"
}

FRONT_COVER = {
    "prompt": "Disney Pixar 3D style illustration. STRICT: exactly ONE dog at LEFT of frame, exactly ONE newborn baby at CENTER-RIGHT, centered balanced composition for book cover, pure illustration only, zero text or lettering. PET: {pet_desc}, at LEFT of frame leaning gently forward with nose extended toward the newborn, eyes soft and tender with wonder, tail slightly wagging, completely still and careful, the gentlest possible approach. HUMAN: A {gender_word} newborn with {eye_desc} eyes{glasses_desc}, lying in a bassinet at CENTER-RIGHT of frame, wrapped snugly in a soft white blanket, only the peaceful sleeping face visible above the blanket. TOGETHER: the dog's nose gently approaches the newborn's tiny face for the very first time, a sacred tender first meeting between two souls. SETTING: Warm cozy nursery, soft golden light through sheer curtains, pastel walls, soft bassinet, intimate and peaceful. ATMOSPHERE: Sacred first meeting, pure tenderness and wonder, warm golden glow, a love story beginning, book cover quality. {style}"
}

BACK_COVER = {
    "prompt": "Disney Pixar 3D style illustration. SETTING: A beautiful cozy baby nursery room WIDE VIEW, soft pastel walls with tiny paw prints and stars, a wooden crib with a soft blanket and a small plush dog toy inside, a rocking chair with a children's storybook on it, soft carpet on the floor, warm golden light from a star-shaped nightlight, mobile hanging with animal shapes, shelves with children's books and stuffed animals, window showing a starry night sky. ATMOSPHERE: Warm peaceful magical nursery, soft dreamy golden lighting, ready for bedtime stories. Pure illustration only, zero text or lettering. {style}"
}


def build_human_preview_prompt(human_desc: str) -> str:
    return f"Disney Pixar 3D style illustration. FULL BODY portrait of {human_desc}, wearing a white diaper or soft onesie or pajamas (NEVER naked), standing naturally, warm smile, centered in frame, occupying 60% of frame height. NEUTRAL SOLID GRADIENT BACKGROUND (soft cream to warm beige), plain studio background, studio portrait style. Natural friendly expression, relaxed standing pose. Clean professional animation art, clean illustration only. STRICT: Character MUST wear a diaper or onesie — NEVER naked."


def build_human_preview_prompt_with_photo(gender_word: str, age_display: str, eye_desc: str = "", hair_desc: str = "", glasses: str = "", facial_hair: str = "") -> str:
    glasses_desc = " MUST be wearing glasses" if glasses == "glasses" else " MUST be wearing sunglasses" if glasses == "sunglasses" else ""
    facial_hair_map = {'stubble': 'light stubble', 'short_beard': 'short beard', 'full_beard': 'full thick beard', 'mustache': 'mustache'}
    facial_hair_desc = f" MUST have {facial_hair_map[facial_hair]}" if facial_hair and facial_hair != 'none' and facial_hair in facial_hair_map else ""
    accessories = (glasses_desc + facial_hair_desc).strip()
    hair_part = f", {hair_desc}" if hair_desc and "matching the reference" not in hair_desc else ""
    if "baby" in gender_word.lower():
        return (
            f"Disney Pixar 3D style illustration. "
            f"OUTFIT: the baby wears a soft white onesie or a cute white diaper — body fully clothed below the neck. "
            f"CHARACTER: 3D animated {gender_word} with FACE and HEAD matching @image1 exactly, {eye_desc} eyes{hair_part}. "
            f"FULL BODY portrait, centered, warm happy expression. "
            f"NEUTRAL SOLID GRADIENT BACKGROUND (soft cream to warm beige). "
            f"STRICT: body below neck is dressed with onesie or diaper — NEVER bare skin below neck, NEVER naked body. "
            f"Clean illustration only."
        )
    return f"Disney Pixar 3D style illustration. 3D animated character of the {gender_word} from @image1, {eye_desc} eyes{hair_part}, full face and skin matching @image1 exactly.{(' ' + accessories + '.') if accessories else ''} FULL BODY portrait, centered, warm expression. NEUTRAL SOLID GRADIENT BACKGROUND (soft cream to warm beige). Clean illustration only."


def build_pet_preview_prompt(pet_desc: str) -> str:
    return f"Disney Pixar 3D style illustration. FULL BODY portrait of {pet_desc}, sitting or standing naturally, friendly expression, centered in frame, occupying 50% of frame height. NEUTRAL SOLID GRADIENT BACKGROUND (soft cream to warm beige), plain studio background, studio portrait style. Warm lighting, expressive eyes. Clean professional animation art, clean illustration only."


def build_pet_preview_prompt_with_photo(pet_desc: str = "", pet_species: str = "dog") -> str:
    animal = "cat" if pet_species == "cat" else "dog"
    return f"Disney Pixar 3D style. 3D animated character of the {animal} from @image1. FULL BODY portrait, sitting or standing naturally, friendly expression, centered, occupying 50% of frame height. NEUTRAL SOLID GRADIENT BACKGROUND (soft cream to warm beige). Warm lighting. Clean animation art, clean illustration only."


_HAIR_COLOR_MAP = {
    'black': 'jet black',
    'brown': 'medium brown',
    'light_brown': 'warm light brown (caramel-honey tone)',
    'blonde': 'dark dirty blonde',
    'very_light_blonde': 'pale platinum blonde',
    'red': 'bright red',
    'auburn': 'auburn',
}


def _get_hair_growth_desc(scene_id: int, hair_color: str) -> str:
    """Return progressive hair growth description based on baby's age (scene ID).
    Returns a comma-prefixed string ready to insert after eye_desc in the prompt.
    Scenes 1-9: no hair desc (baby too young, reference image covers it).
    Scenes 10-11 (7-8 months): nearly bald smooth scalp.
    Scenes 12-13 (9-10 months): very sparse fine baby hair starting.
    Scenes 14-15 (11 months): short fine colored hair growing in.
    Scenes 16+ (12 months onward): short soft colored baby hair.
    """
    c = _HAIR_COLOR_MAP.get(hair_color, hair_color) if hair_color else ''
    if scene_id in (10, 11):
        return ", nearly bald smooth scalp with barely-there sparse fuzz"
    elif scene_id in (12, 13):
        return ", very sparse fine baby hair just starting to appear"
    elif scene_id in (14, 15):
        return f", short fine {c} baby hair growing in" if c else ", short fine baby hair growing in"
    elif scene_id >= 16:
        return f", short soft {c} baby hair" if c else ", short soft baby hair"
    return ""


def build_scene_prompt(scene: dict, human_desc: str, pet_name: str, pet_desc: str, eye_desc: str = "", gender_word: str = "baby", glasses: str = "", hair_color: str = "", **kwargs) -> str:
    prompt = scene.get('prompt', '')
    scene_id = scene.get('id', 0)

    prompt = prompt.replace('{human_desc}', human_desc)
    prompt = prompt.replace('{pet_name}', pet_name)
    prompt = prompt.replace('{pet_desc}', pet_desc)
    eye_color_only = eye_desc.replace(' eyes', '').strip() if eye_desc else ''
    prompt = prompt.replace('{eye_desc}', eye_color_only)
    prompt = prompt.replace('{gender_word}', gender_word)
    glasses_desc = ", wearing glasses" if glasses == "glasses" else ", wearing sunglasses" if glasses == "sunglasses" else ""
    prompt = prompt.replace('{glasses_desc}', glasses_desc)

    is_girl = gender_word.lower() in ('girl', 'niña', 'baby girl')
    baby_bow = ", a tiny pink bow hair clip" if is_girl and scene_id >= 14 else ""
    prompt = prompt.replace('{baby_bow}', baby_bow)

    prompt = prompt.replace('{style}', STYLE_BASE)
    return prompt


def build_story_text(scene: dict, child_name: str, pet_name: str, language: str = 'es') -> str:
    text_key = 'text_es' if language == 'es' else 'text_en'
    text = scene.get(text_key, '')
    text = text.replace('{pet_name}', pet_name)
    text = text.replace('{name}', child_name)
    return text


def get_all_scene_prompts(human_desc: str, pet_name: str, pet_desc: str, eye_desc: str = "", hair_color: str = "") -> list:
    prompts = []
    for scene in FURRY_LOVE_SCENES:
        prompts.append(build_scene_prompt(scene, human_desc, pet_name, pet_desc, eye_desc, hair_color=hair_color))
    prompts.append(build_scene_prompt(CLOSING_SCENE, human_desc, pet_name, pet_desc, eye_desc, hair_color=hair_color))
    return prompts


def get_all_story_texts(child_name: str, pet_name: str, language: str = 'es') -> list:
    texts = []
    for scene in FURRY_LOVE_SCENES:
        texts.append({
            'id': scene['id'],
            'text': build_story_text(scene, child_name, pet_name, language),
            'text_position': scene.get('text_position', 'split')
        })
    return texts


def get_cover_prompts(human_desc: str, pet_name: str, pet_desc: str, eye_desc: str = "", glasses: str = "") -> dict:
    return {
        'front': build_scene_prompt(FRONT_COVER, human_desc, pet_name, pet_desc, eye_desc, glasses=glasses),
        'back': build_scene_prompt(BACK_COVER, human_desc, pet_name, pet_desc, eye_desc, glasses=glasses)
    }
