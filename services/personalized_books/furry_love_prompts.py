# Tú y tu Amor Peludo - Personalized Book Prompts
# 19 scenes + closing + covers
# Story: A baby arrives home where a dog already lives
# Covers newborn to age 2 - tender moments, milestones, open ending
#
# FLUX 2 Dev with TWO reference images:
#   1. Human preview: detailed character description → generates reference image 1
#   2. Pet preview: detailed pet description → generates reference image 2
#   3. Scenes: FLUX 2 Dev takes BOTH references → prompts bind roles explicitly
#
# Schema (adapted from Magic Inventor):
#   HUMAN CHARACTER → PET CHARACTER → ACTION → SETTING → ATMOSPHERE → STRICT
#
# Rules:
#   - guidance_scale=3.5, num_inference_steps=28, aspect_ratio=3:4
#   - Keep prompts concise - FLUX 2 Dev loses focus with >300 words
#   - Style: Disney Pixar 3D everywhere, NO watercolor
#   - Human can be any age (child, teen, adult, elderly)
#   - Pet is always a dog (customized breed, color, pattern)
#   - TWO reference images per scene (human + pet)
#   - Text uses {name} for human and {pet_name} for pet

STYLE_BASE = "Disney Pixar 3D style, soft warm golden lighting, tender emotional atmosphere, WIDE SHOT full body from head to feet, characters occupy 40% of frame, cozy home environment visible, clean illustration only. STRICT: All babies wear onesies or pajamas, fully clothed always."

FURRY_LOVE_SCENES = [
    {
        "id": 1,
        "text_es": "Algo mágico estaba a punto de suceder. {pet_name} lo sentía en el aire. La casa olía diferente: a pintura fresca, a ropa suavecita, a algo que {pet_name} no sabía nombrar pero que hacía que su cola se moviera despacito, como si guardara un secreto.",
        "text_en": "Something magical was about to happen. {pet_name} could feel it in the air. The house smelled different: of fresh paint, soft fabrics, of something {pet_name} couldn't name but that made their tail wag slowly, as if keeping a secret.",
        "prompt": "Disney Pixar 3D style illustration. PET: {pet_desc}, sitting in a nursery doorway, head tilted curiously, tail slightly wagging. ACTION: The dog sits alone at the threshold of a freshly painted nursery, peeking inside with curiosity, nose raised sniffing the air. SETTING: Nursery doorway WIDE VIEW, pastel walls behind, a crib with mobile, soft blankets, warm sunlight through curtains, paint cans and baby items visible. ATMOSPHERE: Anticipation, warm golden afternoon light, cozy home feeling. STRICT: Only ONE dog alone in the scene, before the baby arrives, peaceful domestic scene. {style}",
        "text_position": "split"
    },
    {
        "id": 2,
        "text_es": "Y entonces, un día, la puerta se abrió. {pet_name} escuchó risas, pasos suaves y... un sonido nuevo. Pequeñito. Dulce. Un suspiro diminuto que llenó toda la casa. Los ojos de {pet_name} se abrieron enormes: ¡habían traído a {name} a casa!",
        "text_en": "And then, one day, the door opened. {pet_name} heard laughter, soft footsteps and... a new sound. Tiny. Sweet. A little sigh that filled the whole house. {pet_name}'s eyes went wide: they had brought {name} home!",
        "prompt": "Disney Pixar 3D style illustration. A baby stroller in a home entryway with a tiny newborn baby with {eye_desc} eyes{glasses_desc} peeking out from a white blanket inside the stroller. Only one adult hand visible resting on the stroller handlebar from above, only the hand visible. PET: {pet_desc}, sitting on the floor next to the stroller, looking up at the baby with huge curious eyes, ears perked forward, tail frozen mid-wag. ACTION: The stroller has just arrived through the open front door, one adult hand rests on the handlebar, the pet sits patiently beside it gazing at the tiny bundle inside. SETTING: Home entryway WIDE VIEW, front door wide open with warm sunlight streaming in, cozy living room visible behind, welcome mat on floor. ATMOSPHERE: Emotional first meeting, warm golden light from doorway, joy and wonder, anticipation. STRICT: Only ONE adult hand visible on stroller handle, ONE baby in stroller, ONE pet sitting beside stroller, heartwarming arrival scene. {style}",
        "text_position": "split"
    },
    {
        "id": 3,
        "text_es": "{pet_name} se acercó despacito, con las patitas suaves sobre el suelo. Puso su nariz cerca de {name}, muy cerca, y olió. Olía a leche, a talco, a algo que {pet_name} decidió en ese instante que iba a proteger para siempre.",
        "text_en": "{pet_name} approached slowly, soft paws on the floor. Nose came close to {name}, very close, and sniffed. It smelled of milk, of powder, of something {pet_name} decided in that very instant to protect forever.",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: A tiny newborn baby with {eye_desc} eyes{glasses_desc}, wrapped in a soft white blanket, lying in a bassinet, eyes barely open, tiny fingers. PET: {pet_desc}, standing on hind legs with front paws on bassinet edge, nose gently touching the baby's tiny hand, eyes soft and tender. ACTION: Close tender moment, the dog gently sniffs the newborn's tiny hand, baby's fingers curling slightly. SETTING: Living room WIDE VIEW, soft couch nearby, warm blankets, afternoon sunlight filtering through curtains. ATMOSPHERE: First meeting, gentle tenderness, soft warm golden light. STRICT: Only ONE newborn baby and ONE dog in the scene, intimate gentle moment. {style}",
        "text_position": "split"
    },
    {
        "id": 4,
        "text_es": "Esa primera noche, {pet_name} se echó junto a la cuna de {name}. No se movió ni una vez. Cada vez que {name} hacía un ruidito, {pet_name} levantaba una oreja. \"Aquí estoy\", decía su mirada. \"Aquí estaré siempre.\"",
        "text_en": "That first night, {pet_name} lay down beside {name}'s crib. Didn't move once. Every time {name} made a little sound, {pet_name} raised one ear. \"I'm here,\" said those eyes. \"I'll always be here.\"",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: A tiny sleeping newborn with {eye_desc} eyes{glasses_desc} in a white crib, peaceful face, tiny fists. PET: {pet_desc}, lying on the floor right beside the crib, head resting on front paws, one ear raised alertly, eyes open and watchful, protective posture. ACTION: The dog guards the sleeping baby, lying faithfully beside the crib in the moonlit nursery. SETTING: Nursery at night WIDE VIEW, soft moonlight through window, star-shaped nightlight glowing, mobile with stars above crib, peaceful darkness. ATMOSPHERE: Protective love, soft blue moonlight mixed with warm nightlight glow, serene safety. STRICT: Only ONE baby in crib, ONE dog on floor beside it, nighttime scene, peaceful. {style}",
        "text_position": "split"
    },
    {
        "id": 5,
        "text_es": "Pasaron los días y una mañana, mientras {pet_name} observaba la cuna, sucedió algo increíble. {name} abrió bien los ojos, miró directamente a {pet_name}... ¡y sonrió! La primera sonrisa de {name} fue para {pet_name}.",
        "text_en": "Days passed and one morning, while {pet_name} watched the crib, something incredible happened. {name} opened their eyes wide, looked straight at {pet_name}... and smiled! {name}'s first smile was for {pet_name}.",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: A 2-month-old baby with {eye_desc} eyes{glasses_desc} lying in a crib wearing a soft white onesie, eyes wide open looking at the dog, a big gummy smile on tiny face, arms reaching out. PET: {pet_desc}, standing beside the crib, front paws on the edge, looking at the smiling baby with an expression of pure love, tail wagging. ACTION: Baby and dog share a magical first smile moment, baby beaming at the dog, dog looking back with adoring eyes. SETTING: Nursery morning WIDE VIEW, bright warm sunlight streaming through window, cheerful pastel nursery, mobile turning gently. ATMOSPHERE: Pure joy, magical connection, warm morning sunlight with golden sparkles. STRICT: Only ONE baby, ONE dog, magical bonding moment, warm and bright. {style}",
        "text_position": "split"
    },
    {
        "id": 6,
        "text_es": "{pet_name} desapareció un momento y volvió con su juguete más preciado. Lo dejó suavemente junto a {name}. \"Esto es lo que más quiero\", parecía decir {pet_name}. \"Y ahora es tuyo también, {name}.\"",
        "text_en": "{pet_name} disappeared for a moment and came back with their most treasured toy. Gently placed it next to {name}. \"This is what I love most,\" {pet_name} seemed to say. \"And now it's yours too, {name}.\"",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: A 3-month-old baby with {eye_desc} eyes{glasses_desc} wearing a soft yellow onesie, lying on a soft play mat, looking at a stuffed toy with curious eyes, tiny hands reaching. PET: {pet_desc}, lying beside the baby on the play mat, having just placed a worn stuffed animal toy next to the baby, looking at baby proudly, tail gently wagging. ACTION: The dog shares its favorite toy with the baby, placing it carefully beside the infant on the play mat. SETTING: Living room floor WIDE VIEW, soft play mat with colorful patterns, warm afternoon light, toys scattered nearby. ATMOSPHERE: Generosity and love, warm soft lighting, tender sharing moment. STRICT: Only ONE baby, ONE dog, ONE toy being shared, heartwarming scene. {style}",
        "text_position": "split"
    },
    {
        "id": 7,
        "text_es": "Un día, las manitas curiosas de {name} descubrieron algo suave y tibio: ¡el pelaje de {pet_name}! {name} agarró un mechón y no quiso soltar. {pet_name} se quedó quieto, feliz, con los ojos entrecerrados de puro gusto.",
        "text_en": "One day, {name}'s curious little hands discovered something soft and warm: {pet_name}'s fur! {name} grabbed a tuft and wouldn't let go. {pet_name} stayed perfectly still, happy, eyes half-closed with pure contentment.",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: A 4-month-old baby with {eye_desc} eyes{glasses_desc} wearing a light green striped onesie, sitting propped up with pillows, tiny hand buried in the dog's fur, face showing delight and wonder. PET: {pet_desc}, lying very close to the baby, eyes half-closed with contentment, completely still and patient, enjoying the baby's touch. ACTION: Baby's tiny hand grabs the dog's soft fur for the first time, both enjoying the connection, baby fascinated by the texture. SETTING: Soft couch area WIDE VIEW, plush pillows supporting baby, warm blanket, soft afternoon light. ATMOSPHERE: Discovery and trust, warm golden tones, gentle intimate moment. STRICT: Only ONE baby, ONE dog, close tender contact, peaceful. {style}",
        "text_position": "split"
    },
    {
        "id": 8,
        "text_es": "¡La hora del baño! {name} chapoteaba y reía mientras el agua salpicaba por todos lados. {pet_name} observaba desde la puerta con la cabeza ladeada. Una ola de agua le mojó la nariz a {pet_name}. ¡Y las risas de {name} fueron aún más grandes!",
        "text_en": "Bath time! {name} splashed and laughed as water went everywhere. {pet_name} watched from the doorway with a tilted head. A wave of water splashed {pet_name}'s nose. And {name}'s laughter grew even bigger!",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: A 5-month-old baby with {eye_desc} eyes{glasses_desc} wearing only a diaper, sitting in a small baby bathtub, splashing water joyfully with both hands, laughing with mouth wide open, bare chest and diaper visible. PET: {pet_desc}, standing in the bathroom doorway, head tilted to one side, water droplets on nose, one paw raised, surprised but amused expression. ACTION: Baby splashes enthusiastically in bathtub sending water flying, a splash hits the dog's nose, both enjoying the chaos. SETTING: Bright bathroom WIDE VIEW, small baby bathtub with bubbles, rubber duck, water splashes in the air, towel on rack, warm lighting. ATMOSPHERE: Playful joy, bright cheerful lighting, water droplets catching light like sparkles. STRICT: Only ONE baby in tub wearing only a diaper, ONE dog at doorway, fun bath scene, joyful chaos. {style}",
        "text_position": "split"
    },
    {
        "id": 9,
        "text_es": "Durante el tiempo boca abajo, {name} levantó la cabecita por primera vez. ¿Y qué vio? A {pet_name}, echado en el suelo, nariz con nariz. {name} y {pet_name} se miraron durante un largo momento mágico, como si se contaran secretos sin palabras.",
        "text_en": "During tummy time, {name} lifted their little head for the first time. And what did they see? {pet_name}, lying on the floor, nose to nose. {name} and {pet_name} looked at each other for a long magical moment, as if sharing secrets without words.",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: A 4-month-old baby with {eye_desc} eyes{glasses_desc} wearing a soft mint green onesie on tummy time on a soft mat, head lifted up for the first time, big curious {eye_desc} eyes looking directly at the dog, tiny smile. PET: {pet_desc}, lying flat on the floor face-to-face with the baby, chin on the mat, nose almost touching baby's nose, gentle loving eyes. ACTION: Baby and dog lie face to face on the floor, noses almost touching, sharing a tender wordless moment of connection. SETTING: Living room floor WIDE VIEW, soft play mat, warm sunlight on the floor, toys scattered around. ATMOSPHERE: Magical connection, warm intimate eye contact, soft golden light on both faces. STRICT: Only ONE baby, ONE dog, face-to-face on floor level, intimate and tender. {style}",
        "text_position": "split"
    },
    {
        "id": 10,
        "text_es": "¡{name} se movió! Primero fue un balanceo torpe, luego las rodillitas empezaron a funcionar. ¿Hacia dónde fue la primera aventura de {name}? Directo hacia {pet_name}, por supuesto. Siempre hacia {pet_name}.",
        "text_en": "{name} moved! First a wobbly rocking, then the little knees started working. Where did {name}'s first adventure go? Straight toward {pet_name}, of course. Always toward {pet_name}.",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: A 7-month-old baby with {eye_desc} eyes{glasses_desc} wearing a soft blue onesie with tiny white stars, crawling on hands and knees across the floor, determined happy face, heading straight toward the dog. PET: {pet_desc}, sitting a few feet away facing the baby, tail wagging excitedly, front paws doing a happy dance, encouraging expression. ACTION: Baby crawls determinedly toward the dog for the first time, the dog waits with excited anticipation, tail wagging fast. SETTING: Living room WIDE VIEW, carpet floor, coffee table in background, warm afternoon light, clear path between baby and dog. ATMOSPHERE: First crawl milestone, excitement and encouragement, warm joyful energy. STRICT: Only ONE crawling baby, ONE excited dog, milestone moment, celebratory mood. {style}",
        "text_position": "split"
    },
    {
        "id": 11,
        "text_es": "En el jardín, {name} tocó el pasto por primera vez. Era cosquilloso, verde y olía a aventura. {pet_name} corrió en círculos de alegría, trayendo palitos y hojas como regalos. {name} reía y reía y reía.",
        "text_en": "In the garden, {name} touched grass for the first time. It was tickly, green, and smelled like adventure. {pet_name} ran in happy circles, bringing sticks and leaves as gifts. {name} laughed and laughed and laughed.",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: An 8-month-old baby with {eye_desc} eyes{glasses_desc} wearing a cute orange onesie with animal print, sitting on green grass, touching the grass blades with wonder, laughing joyfully, bare feet on the lawn. PET: {pet_desc}, running playfully nearby with a small stick in mouth, mid-stride, tail high and happy, bringing the stick to the baby. ACTION: Baby sits on grass fascinated by nature while the dog brings a stick as a gift, both enjoying the garden together. SETTING: Beautiful home garden WIDE VIEW, green lawn, colorful flowers, fence, blue sky with fluffy clouds, warm golden sunlight, butterflies. ATMOSPHERE: Outdoor joy, bright sunny day, nature exploration, pure happiness. STRICT: Only ONE baby sitting on grass, ONE playful dog, outdoor garden scene, cheerful. {style}",
        "text_position": "split"
    },
    {
        "id": 12,
        "text_es": "Los días de lluvia eran especiales. {name} y {pet_name} se sentaban juntos frente a la ventana, viendo las gotas resbalarse por el cristal. Afuera todo era gris, pero adentro, juntos, todo era cálido.",
        "text_en": "Rainy days were special. {name} and {pet_name} sat together by the window, watching drops slide down the glass. Outside everything was gray, but inside, together, everything was warm.",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: A 9-month-old baby with {eye_desc} eyes{glasses_desc} wearing a cozy warm lavender onesie, sitting on a window seat, one tiny hand touching the glass where raindrops slide down, peaceful curious expression. PET: {pet_desc}, sitting right beside the baby on the window seat, also looking at the rain, their bodies touching, cozy and content. ACTION: Baby and dog sit together at a rainy window, watching raindrops slide down the glass, sharing a quiet peaceful moment. SETTING: Cozy window seat WIDE VIEW, large window with rain streaming down, gray sky outside, warm interior with blankets and cushions, soft lamp glowing. ATMOSPHERE: Cozy rainy day, warm interior vs gray outside, intimate quiet companionship. STRICT: Only ONE baby, ONE dog, sitting together at window, rainy day scene. {style}",
        "text_position": "split"
    },
    {
        "id": 13,
        "text_es": "La hora de la comida era la favorita de {pet_name}. {name} comía con las manos, con la cara, con toda el alma. Y lo que caía al suelo... bueno, {pet_name} siempre estaba listo para \"ayudar a limpiar\". ¡{name} y {pet_name}, el mejor equipo del mundo!",
        "text_en": "Mealtime was {pet_name}'s favorite. {name} ate with hands, with face, with whole heart and soul. And what fell to the floor... well, {pet_name} was always ready to \"help clean up.\" {name} and {pet_name}, the best team in the world!",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: A 10-month-old baby with {eye_desc} eyes{glasses_desc} sitting in a high chair, face covered in colorful food, hands messy with puree, giggling, dropping food over the side. PET: {pet_desc}, sitting right under the high chair, looking up with eager happy expression, tongue out, catching a piece of food, tail wagging fast. ACTION: Messy baby in high chair drops food while the dog happily catches it below, both thoroughly enjoying mealtime together. SETTING: Kitchen dining area WIDE VIEW, high chair, colorful baby food on tray and face, food bits on floor, cheerful kitchen background. ATMOSPHERE: Joyful messy fun, bright kitchen lighting, comedic and heartwarming. STRICT: Only ONE baby in high chair, ONE dog underneath, funny mealtime scene. {style}",
        "text_position": "split"
    },
    {
        "id": 14,
        "text_es": "Por las noches, cuando alguien leía un cuento, {name} se recostaba contra {pet_name}. {name} miraba las páginas, {pet_name} miraba a {name}. Y los dos se iban quedando dormidos juntos, en un nido de amor.",
        "text_en": "At night, when someone read a story, {name} leaned against {pet_name}. {name} looked at the pages, {pet_name} looked at {name}. And they both drifted off to sleep together, in a nest of love.",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: An 11-month-old baby with {eye_desc} eyes{glasses_desc} wearing soft star-print pajamas, sitting on a couch, leaning against the dog, sleepy {eye_desc} eyes looking at an open picture book, tiny hands on the pages. PET: {pet_desc}, lying on the couch beside the baby, the baby leaning against their warm body, dog looking at the baby with tender sleepy eyes. ACTION: Baby leans against the dog while looking at a picture book, both getting sleepy, a cozy reading moment together on the couch. SETTING: Cozy living room evening WIDE VIEW, soft couch with blankets, warm lamp light, open picture book with colorful illustrations, pillows around them. ATMOSPHERE: Bedtime coziness, warm amber lamp light, drowsy love, intimate. STRICT: Only ONE baby, ONE dog, on couch together, cozy evening scene. {style}",
        "text_position": "split"
    },
    {
        "id": 15,
        "text_es": "Una noche, un trueno enorme sacudió la casa. {name} se asustó y empezó a llorar. Pero {pet_name} se acurrucó más cerca, pegando su cuerpo tibio contra {name}. \"No tengas miedo\", decía el calor de {pet_name}. Y {name} se calmó.",
        "text_en": "One night, a huge thunderclap shook the house. {name} got scared and started crying. But {pet_name} snuggled closer, pressing their warm body against {name}. \"Don't be afraid,\" said {pet_name}'s warmth. And {name} calmed down.",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: A 10-month-old baby with {eye_desc} eyes{glasses_desc} in pajamas, sitting in a crib, face showing they just stopped crying, tiny hand gripping the dog's fur, calming down. PET: {pet_desc}, having climbed partway into the crib, body pressed protectively against the baby, head resting near the baby's chest, protective and comforting. ACTION: Dog comforts the scared baby during a thunderstorm, pressing close to protect, baby calming down while holding onto the dog. SETTING: Nursery during storm WIDE VIEW, flash of lightning visible through curtain, dark room lit by soft nightlight, cozy crib with blankets. ATMOSPHERE: Protection and comfort, dramatic storm outside vs safety inside, warm protective love. STRICT: Only ONE baby, ONE dog, storm comfort scene, emotional and tender. {style}",
        "text_position": "split"
    },
    {
        "id": 16,
        "text_es": "Y entonces llegó el día más esperado. {name} se soltó de la mesa, abrió los brazos... ¡y caminó! Uno, dos, tres pasitos tambaleantes. ¿Hacia dónde? Hacia {pet_name}. Los primeros pasos de {name} fueron para llegar a {pet_name}.",
        "text_en": "And then came the most awaited day. {name} let go of the table, opened their arms... and walked! One, two, three wobbly steps. Where to? Toward {pet_name}. {name}'s first steps were to reach {pet_name}.",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: A 12-month-old toddler with {eye_desc} eyes{glasses_desc} wearing a soft light blue onesie, taking first steps, arms outstretched for balance, wobbly but determined, huge proud smile, walking toward the dog. PET: {pet_desc}, sitting a few steps away facing the toddler, body low and welcoming, tail wagging intensely, eyes bright with excitement, ready to receive the walking baby. ACTION: Baby takes their magical first steps toward the dog, arms outstretched, wobbly but brave, the dog waits with incredible excitement. SETTING: Living room WIDE VIEW, clear floor space, warm afternoon light, coffee table behind where baby pushed off, golden sunbeams. ATMOSPHERE: Epic milestone moment, warm golden triumphant light, joy and pride, magical sparkles in the air. STRICT: Only ONE toddler walking, ONE dog waiting, first steps milestone, emotional and triumphant. {style}",
        "text_position": "split"
    },
    {
        "id": 17,
        "text_es": "\"¡Busca, {pet_name}!\" {name} lanzó la pelota con toda su fuerza. La pelota rodó apenas un metro. Pero {pet_name} salió corriendo como si fuera el lanzamiento más épico del mundo, la trajo de vuelta y la dejó a los pies de {name}. Una y otra y otra vez.",
        "text_en": "\"Fetch, {pet_name}!\" {name} threw the ball with all their might. The ball rolled barely three feet. But {pet_name} took off running as if it were the most epic throw in the world, brought it back and placed it at {name}'s feet. Again and again and again.",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: A 12-month-old toddler with {eye_desc} eyes{glasses_desc} standing wobbly in the garden, wearing a cute light red t-shirt and tiny denim shorts, arm extended after throwing a small colorful ball, proud excited expression, bare feet on grass. PET: {pet_desc}, running back toward the toddler with a small ball in mouth, tail high, eyes bright and happy, mid-run. ACTION: Toddler plays fetch with the dog in the garden, the dog enthusiastically retrieves the ball that only went a short distance, the toddler claps excitedly. SETTING: Home garden WIDE VIEW, green grass, sunny day, the ball visible near the dog, fence and flowers in background, blue sky. ATMOSPHERE: Playful outdoor fun, bright sunny joyful energy, pure childhood happiness. STRICT: Only ONE toddler standing, ONE running dog with ball, outdoor play scene. {style}",
        "text_position": "split"
    },
    {
        "id": 18,
        "text_es": "Después de tanto jugar, llegaba el mejor momento del día: la siesta juntos. {name} se acurrucaba contra {pet_name}, una mano sobre su lomo cálido. Y los dos soñaban el mismo sueño: un sueño donde {name} y {pet_name} estaban siempre juntos.",
        "text_en": "After all that playing came the best moment of the day: nap time together. {name} curled up against {pet_name}, one hand on that warm back. And they both dreamed the same dream: a dream where {name} and {pet_name} were always together.",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: A 12-month-old toddler with {eye_desc} eyes{glasses_desc}, HUMAN skin and HUMAN face, wearing a soft light red t-shirt and tiny shorts, sleeping peacefully on a soft rug, lying next to the dog with one small hand resting on the dog's back, peaceful angelic face with human features only. PET: {pet_desc}, sleeping on the rug beside the toddler, body curved protectively near the child, head resting near the toddler's head, clearly a separate animal from the child. ACTION: Toddler and dog nap side by side on a soft rug after playing, both peacefully asleep. SETTING: Sunlit living room floor WIDE VIEW, soft rug, warm afternoon sunlight streaming through window making golden patches, cozy pillows nearby. ATMOSPHERE: Perfect peace, warm golden nap light, gentle serenity, love made visible. STRICT: Only ONE sleeping toddler wearing clothes, ONE sleeping dog, the child has smooth human skin, human face, human hands, the dog has canine features, they are clearly TWO separate beings lying next to each other. {style}",
        "text_position": "split"
    },
    {
        "id": 19,
        "text_es": "Hoy {name} y {pet_name} caminan juntos por el jardín. {name} da pasitos seguros, señala las flores, las mariposas, las nubes. Y le cuenta secretos a {pet_name} al oído. {pet_name} escucha cada palabra como si fuera la más importante del universo. Porque la historia de {name} y {pet_name} no tiene final. Esta historia apenas comienza.",
        "text_en": "Today {name} and {pet_name} walk together through the garden. {name} takes steady little steps, pointing at the flowers, the butterflies, the clouds. And whispers secrets in {pet_name}'s ear. {pet_name} listens to every word as if it were the most important in the universe. Because the story of {name} and {pet_name} has no ending. This story is just beginning.",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: A 12-month-old toddler with {eye_desc} eyes{glasses_desc} walking with wobbly confident steps in a beautiful garden, wearing a cheerful yellow t-shirt and soft blue pants, one hand resting on the dog's back for balance, looking up at the sky with wonder and a big smile, bare feet on soft grass. PET: {pet_desc}, walking slowly beside the toddler at the same pace, looking up at the child with adoring eyes, tail wagging gently, happy and proud, being a steady support. ACTION: Toddler and dog walk together through a beautiful garden at golden hour, the child looks up at the sky in wonder while the dog walks faithfully beside them. SETTING: Beautiful home garden at golden hour WIDE VIEW, green grass, colorful flowers, butterflies flying around them, a garden path, golden sunset sky with warm pink clouds, soft warm light. ATMOSPHERE: Open ending, warm golden hour light, endless possibilities ahead, love and companionship, magical and hopeful. STRICT: Only ONE toddler with exactly TWO hands, ONE dog beside them, garden scene at sunset, hopeful and beautiful, exactly two hands and two feet on the toddler. {style}",
        "text_position": "split"
    }
]

CLOSING_SCENE = {
    "id": 20,
    "prompt": "Disney Pixar 3D style illustration. HUMAN: A 12-month-old toddler with {eye_desc} eyes{glasses_desc} wearing soft pajamas, sleeping peacefully in a cozy toddler bed, one tiny arm dangling over the edge of the bed toward the dog, peaceful smile, covered with a star-patterned blanket. PET: {pet_desc}, sleeping on the floor right beside the bed, head resting near the dangling hand, one paw touching the edge of the bed, protective even in sleep. ACTION: Toddler sleeps peacefully in bed with one hand reaching down toward the dog sleeping faithfully on the floor beside the bed, their bond visible even in sleep. SETTING: Cozy bedroom at night WIDE VIEW, warm nightlight glow, stars visible through window, peaceful darkness, soft blankets. ATMOSPHERE: Perfect ending, warm nightlight glow, eternal love, peaceful protection. STRICT: Only ONE toddler in bed, ONE real dog on floor, only real dog on the floor, nighttime bedroom scene, serene. {style}",
    "text_position": "none"
}

FRONT_COVER = {
    "prompt": "Disney Pixar 3D style illustration. PET: The dog from @image2, {pet_desc}, gently pressing its nose against a tiny newborn baby with {eye_desc} eyes{glasses_desc} wrapped in a soft white blanket, eyes wide with tenderness and curiosity, tail slightly wagging, being very gentle and careful. HUMAN: A tiny newborn baby with {eye_desc} eyes{glasses_desc} (0-1 month old) wrapped snugly in a soft white blanket, only the peaceful sleeping face visible, lying in a bassinet. ACTION: The dog leans in and gently sniffs the newborn baby for the first time, nose almost touching the baby's tiny face, a magical tender first meeting moment, centered composition for book cover. SETTING: Warm cozy nursery with soft golden light streaming through curtains, pastel walls, soft blankets, peaceful intimate atmosphere. ATMOSPHERE: First meeting, pure love and tenderness, warm golden light, gentle emotional moment, book cover quality. STRICT: Only ONE dog and ONE tiny newborn baby in blanket, centered composition, only the dog and baby in the scene. Pure illustration only, zero text or lettering. {style}"
}

BACK_COVER = {
    "prompt": "Disney Pixar 3D style illustration. SETTING: A beautiful cozy baby nursery room WIDE VIEW, soft pastel walls with tiny paw prints and stars stickers, wooden crib with a soft blanket and a small plush dog toy inside, a rocking chair with a children's storybook on it, soft carpet on the floor, warm golden light from a star-shaped nightlight, mobile hanging with animal shapes, shelves with children's books and stuffed animals, window showing a starry night sky. ATMOSPHERE: Warm, peaceful, magical nursery ready for bedtime stories, soft dreamy lighting. STRICT: Only scenery, plush toys, and objects visible. Pure illustration only, zero text or lettering. {style}"
}


def build_human_preview_prompt(human_desc: str) -> str:
    return f"Disney Pixar 3D style illustration. FULL BODY portrait of {human_desc}, wearing cute comfortable clothes, standing naturally, warm smile, centered in frame, occupying 60% of frame height. NEUTRAL SOLID GRADIENT BACKGROUND (soft cream to warm beige), plain studio background, studio portrait style. Natural friendly expression, relaxed standing pose. Clean professional animation art, clean illustration only. STRICT: Character fully clothed."


def build_human_preview_prompt_with_photo(gender_word: str, age_display: str, eye_desc: str = "", hair_desc: str = "", glasses: str = "") -> str:
    glasses_part = ", wearing glasses" if glasses == "glasses" else ", wearing sunglasses" if glasses == "sunglasses" else ""
    return f"Disney Pixar 3D style illustration. 3D animated character of the {gender_word} from @image1 ({age_display}), {hair_desc}, {eye_desc}{glasses_part}, wearing cute comfortable baby clothes. FULL BODY portrait, centered, warm expression. NEUTRAL SOLID GRADIENT BACKGROUND (soft cream to warm beige). Clean illustration only."


def build_pet_preview_prompt(pet_desc: str) -> str:
    return f"Disney Pixar 3D style illustration. FULL BODY portrait of {pet_desc}, sitting or standing naturally, friendly expression, centered in frame, occupying 50% of frame height. NEUTRAL SOLID GRADIENT BACKGROUND (soft cream to warm beige), plain studio background, studio portrait style. Warm lighting, expressive eyes. Clean professional animation art, clean illustration only."


def build_pet_preview_prompt_with_photo(pet_desc: str = "", pet_species: str = "dog") -> str:
    animal = "cat" if pet_species == "cat" else "dog"
    return f"Disney Pixar 3D style. 3D animated character of the {animal} from @image1. FULL BODY portrait, sitting or standing naturally, friendly expression, centered, occupying 50% of frame height. NEUTRAL SOLID GRADIENT BACKGROUND (soft cream to warm beige). Warm lighting. Clean animation art, clean illustration only."


def build_scene_prompt(scene: dict, human_desc: str, pet_name: str, pet_desc: str, eye_desc: str = "", gender_word: str = "baby", glasses: str = "", **kwargs) -> str:
    prompt = scene.get('prompt', '')
    prompt = prompt.replace('{human_desc}', human_desc)
    prompt = prompt.replace('{pet_name}', pet_name)
    prompt = prompt.replace('{pet_desc}', pet_desc)
    eye_color_only = eye_desc.replace(' eyes', '').strip() if eye_desc else ''
    prompt = prompt.replace('{eye_desc}', eye_color_only)
    prompt = prompt.replace('{gender_word}', gender_word)
    glasses_desc = ", wearing glasses" if glasses == "glasses" else ", wearing sunglasses" if glasses == "sunglasses" else ""
    prompt = prompt.replace('{glasses_desc}', glasses_desc)
    prompt = prompt.replace('{style}', STYLE_BASE)
    return prompt


def build_story_text(scene: dict, child_name: str, pet_name: str, language: str = 'es') -> str:
    text_key = 'text_es' if language == 'es' else 'text_en'
    text = scene.get(text_key, '')
    text = text.replace('{pet_name}', pet_name)
    text = text.replace('{name}', child_name)
    return text


def get_all_scene_prompts(human_desc: str, pet_name: str, pet_desc: str, eye_desc: str = "") -> list:
    prompts = []
    for scene in FURRY_LOVE_SCENES:
        prompts.append(build_scene_prompt(scene, human_desc, pet_name, pet_desc, eye_desc))
    prompts.append(build_scene_prompt(CLOSING_SCENE, human_desc, pet_name, pet_desc, eye_desc))
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
