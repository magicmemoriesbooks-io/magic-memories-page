# Tú y tu Amor Peludo - Baby Story Prompts (REESCRITO Jun 2026)
# 19 scenes + closing + covers
# Story: A baby arrives home where a dog/cat already lives — newborn to 16 months
#
# REFERENCE STRATEGY (Jun 2026 — simplified, reference-first):
#   @image1 = human_preview_path  (Disney Pixar avatar of the baby)
#   @image2 = pet_preview_path    (Disney Pixar avatar of the pet)
#   Prompts trust BOTH references for ALL physical appearance.
#   Character trait text (hair, eyes, skin) removed from scene prompts — references handle it.
#   Only describe: CAST identity, baby age/mobility stage, ACTION, SETTING, ATMOSPHERE.
#
# PROMPT RULES:
#   - guidance_scale=3.5, num_inference_steps=28, aspect_ratio=3:4
#   - Positive language only — no "NO X" or "NEVER X" (FLUX reads negations as presence)
#   - Character separation via positive body description:
#       baby  → "fully human body, smooth skin, two arms, two legs"
#       pet   → "animal body, four paws, fur coat"
#   - Baby age/mobility hint included per scene (critical — reference is a static portrait)
#   - {pet_desc} keeps species + size relative to baby (injected by build_scene_prompt)
#   - {baby_bow} injected for girl babies in scenes 14+ via build_scene_prompt()
#   - Animal word (dog/cat) corrected via build_scene_prompt() if pet_species == 'cat'
#
# AGE PROGRESSION:
#   Scenes 1-4   : newborn (lying in bassinet/crib)
#   Scenes 5-6   : 2-3 months (lying on mat, reaching arms)
#   Scenes 7-9   : 4-5 months (propped on pillows, tummy time)
#   Scene  10    : 7 months (first crawl on hands and knees)
#   Scenes 11-13 : 8-10 months (sitting unsupported)
#   Scenes 14-15 : 11 months (sitting, cruising furniture)
#   Scene  16    : 12 months (FIRST STEPS — wobbly, arms out)
#   Scenes 17-18 : 13 months (toddling, playing)
#   Scene  19    : 14 months (confident hug)
#   Closing      : 16 months (sleeping in toddler bed)

STYLE_BASE = "Disney Pixar 3D style, soft warm golden lighting, tender emotional atmosphere, WIDE SHOT full body from head to feet, characters occupy 40% of frame, cozy home environment visible, clean illustration only. All babies wear a diaper, onesie, or pajamas — always clothed from shoulders to feet."

FURRY_LOVE_SCENES = [
    {
        "id": 1,
        "text_es": "Algo mágico estaba a punto de suceder. {pet_name} lo sentía en el aire. La casa olía diferente: a pintura fresca, a ropa suavecita, a algo que {pet_name} no sabía nombrar pero que hacía que su cola se moviera despacito, como si guardara un secreto.",
        "text_en": "Something magical was about to happen. {pet_name} could feel it in the air. The house smelled different: of fresh paint, soft fabrics, of something {pet_name} couldn't name but that made their tail wag slowly, as if keeping a secret.",
        "prompt": "Disney Pixar 3D style illustration. CAST: @image2 = {pet_name} ({pet_desc}): animal body, four paws, fur coat — match reference exactly. The {gender_word} baby has not arrived yet, no baby in this scene, exactly ONE pet alone. SCENE: {pet_name} sits at the nursery doorway CENTER of frame, head tilted curiously, nose raised sniffing the air, tail slowly wagging, large curious eyes taking in the new room. SETTING: Freshly painted nursery WIDE VIEW, white crib with star mobile, pastel walls, soft blankets folded on the mattress, paint cans nearby, warm sunlight through sheer curtains. ATMOSPHERE: Quiet anticipation, warm golden afternoon light, a secret held in the air. {style}",
        "text_position": "split"
    },
    {
        "id": 2,
        "text_es": "Y entonces, un día, la puerta se abrió. {pet_name} escuchó risas, pasos suaves y... un sonido nuevo. Pequeñito. Dulce. Un suspiro diminuto que llenó toda la casa. Los ojos de {pet_name} se abrieron enormes: ¡habían traído a {name} a casa!",
        "text_en": "And then, one day, the door opened. {pet_name} heard laughter, soft footsteps and... a new sound. Tiny. Sweet. A little sigh that filled the whole house. {pet_name}'s eyes went wide: they had brought {name} home!",
        "prompt": "Disney Pixar 3D style illustration. CAST: @image1 = {gender_word} newborn (fully human body, smooth skin, two arms, tiny face). @image2 = {pet_name} ({pet_desc}): animal body, four paws, fur coat. Match both references exactly. Two distinct separate beings. Exactly ONE baby in stroller + exactly ONE pet beside it. Only ONE adult hand on the handle — no full adult body in frame. SCENE: Tiny newborn {gender_word} lies wrapped in a soft white blanket inside the stroller at CENTER, face barely visible peeking from the blanket. {pet_name} sits at LEFT beside the stroller, looking up at the tiny bundle with wide curious eyes, ears perked forward, tail frozen mid-wag. SETTING: Home entryway WIDE VIEW, front door wide open with warm sunlight streaming in, cozy living room beyond, welcome mat beneath the stroller. ATMOSPHERE: Emotional first arrival, warm golden doorway light, joy and wonder. {style}",
        "text_position": "split"
    },
    {
        "id": 3,
        "text_es": "{pet_name} se acercó despacito, con las patitas suaves sobre el suelo. Puso su nariz cerca de {name}, muy cerca, y olió. Olía a leche, a talco, a algo que {pet_name} decidió en ese instante que iba a proteger para siempre.",
        "text_en": "{pet_name} approached slowly, soft paws on the floor. Nose came close to {name}, very close, and sniffed. It smelled of milk, of powder, of something {pet_name} decided in that very instant to protect forever.",
        "prompt": "Disney Pixar 3D style illustration. CAST: @image1 = {gender_word} newborn (fully human body, smooth skin, tiny curled fingers). @image2 = {pet_name} ({pet_desc}): animal body, four paws, fur coat. Match both references exactly. Two distinct separate beings. Exactly ONE baby in bassinet + exactly ONE pet at its edge. SCENE: Tiny newborn {gender_word} lies in a soft bassinet at CENTER, wrapped in a white blanket, eyes barely open, tiny fingers loosely curled near face. {pet_name} stands at LEFT with front paws on the bassinet edge, nose gently approaching the baby's tiny fingers, eyes full of tenderness, completely still. SETTING: Living room WIDE VIEW, soft couch nearby, warm afternoon sunlight filtering through curtains, cozy gentle atmosphere. ATMOSPHERE: Sacred first meeting, tender wonder, warm golden light, the start of a lifelong bond. {style}",
        "text_position": "split"
    },
    {
        "id": 4,
        "text_es": "Esa primera noche, {pet_name} se echó junto a la cuna de {name}. No se movió ni una vez. Cada vez que {name} hacía un ruidito, {pet_name} levantaba una oreja. \"Aquí estoy\", decía su mirada. \"Aquí estaré siempre.\"",
        "text_en": "That first night, {pet_name} lay down beside {name}'s crib. Didn't move once. Every time {name} made a little sound, {pet_name} raised one ear. \"I'm here,\" said those eyes. \"I'll always be here.\"",
        "prompt": "Disney Pixar 3D style illustration. CAST: @image1 = {gender_word} newborn (fully human body, smooth skin, tiny peaceful face). @image2 = {pet_name} ({pet_desc}): animal body, four paws, fur coat. Match both references exactly. Two distinct separate beings. Exactly ONE sleeping newborn in crib + exactly ONE pet on floor beside it. SCENE: Tiny sleeping newborn {gender_word} lies in a white crib at CENTER, peaceful face, tiny fists, soft blanket tucked around. {pet_name} lies on the nursery floor right beside the crib at RIGHT, chin resting on front paws, one ear raised alertly, watchful open eyes, body curled in devoted protective posture. SETTING: Nursery at night WIDE VIEW, soft moonlight through window, star-shaped nightlight glowing warm orange, mobile with stars above the crib. ATMOSPHERE: Faithful protection, soft blue moonlight and warm nightlight glow, serene safety, eternal devotion. {style}",
        "text_position": "split"
    },
    {
        "id": 5,
        "text_es": "Pasaron los días y una mañana, mientras {pet_name} observaba la cuna, sucedió algo increíble. {name} abrió bien los ojos, miró directamente a {pet_name}... ¡y sonrió! La primera sonrisa de {name} fue para {pet_name}.",
        "text_en": "Days passed and one morning, while {pet_name} watched the crib, something incredible happened. {name} opened their eyes wide, looked straight at {pet_name}... and smiled! {name}'s first smile was for {pet_name}.",
        "prompt": "Disney Pixar 3D style illustration. CAST: @image1 = {gender_word} baby (fully human body, smooth skin, two arms). @image2 = {pet_name} ({pet_desc}): animal body, four paws, fur coat. Match both references exactly. Two distinct separate beings. Exactly ONE 2-month-old baby in crib + exactly ONE pet beside it. SCENE: 2-month-old {gender_word} lies in the crib at CENTER wearing a soft white onesie, eyes wide open locked on {pet_name}, a huge gummy smile spreading across tiny face, arms reaching upward. {pet_name} stands at LEFT beside the crib with front paws on the edge, gazing at the smiling baby with pure adoration, tail wagging excitedly. SETTING: Nursery morning WIDE VIEW, warm sunlight streaming through window, cheerful pastel walls, mobile turning gently above the crib. ATMOSPHERE: First magical smile, pure joy, warm golden morning light. {style}",
        "text_position": "split"
    },
    {
        "id": 6,
        "text_es": "{pet_name} desapareció un momento y volvió con su juguete más preciado. Lo dejó suavemente junto a {name}. \"Esto es lo que más quiero\", parecía decir {pet_name}. \"Y ahora es tuyo también, {name}.\"",
        "text_en": "{pet_name} disappeared for a moment and came back with their most treasured toy. Gently placed it next to {name}. \"This is what I love most,\" {pet_name} seemed to say. \"And now it's yours too, {name}.\"",
        "prompt": "Disney Pixar 3D style illustration. CAST: @image1 = {gender_word} baby (fully human body, smooth skin, two arms). @image2 = {pet_name} ({pet_desc}): animal body, four paws, fur coat. Match both references exactly. Two distinct separate beings. Exactly ONE 3-month-old baby on play mat + exactly ONE pet beside it. SCENE: 3-month-old {gender_word} lies on a soft play mat at CENTER wearing a yellow onesie, both hands reaching curiously toward a worn stuffed toy, eyes wide with wonder. {pet_name} lies at LEFT of the play mat, having just gently nudged the beloved stuffed toy close to the baby's reaching hands, gazing with proud satisfied eyes, tail gently wagging. SETTING: Living room floor WIDE VIEW, colorful play mat, toys scattered around edges, warm afternoon sunlight. ATMOSPHERE: Generous tender love, soft afternoon light, the gift of sharing, first friendship. {style}",
        "text_position": "split"
    },
    {
        "id": 7,
        "text_es": "Un día, las manitas curiosas de {name} descubrieron algo suave y tibio: ¡el pelaje de {pet_name}! {name} agarró un mechón y no quiso soltar. {pet_name} se quedó quieto, feliz, con los ojos entrecerrados de puro gusto.",
        "text_en": "One day, {name}'s curious little hands discovered something soft and warm: {pet_name}'s fur! {name} grabbed a tuft and wouldn't let go. {pet_name} stayed perfectly still, happy, eyes half-closed with pure contentment.",
        "prompt": "Disney Pixar 3D style illustration. CAST: @image1 = {gender_word} baby (fully human body, smooth skin, two arms). @image2 = {pet_name} ({pet_desc}): animal body, four paws, fur coat. Match both references exactly. Two distinct separate beings. Exactly ONE 4-month-old baby propped on pillows + exactly ONE pet lying close. SCENE: 4-month-old {gender_word} is propped up on soft pillows at CENTER wearing a light green onesie, one tiny hand buried in {pet_name}'s fur, face wide-eyed with wonder and delight. {pet_name} lies RIGHT beside the baby, eyes half-closed with contentment, completely still and patient, ears relaxed, completely trusting the baby's touch. SETTING: Soft couch area WIDE VIEW, plush pillows supporting the baby, warm blanket across their laps, soft afternoon light. ATMOSPHERE: Discovery and deep trust, warm golden tones, intimate tactile wonder. {style}",
        "text_position": "split"
    },
    {
        "id": 8,
        "text_es": "¡La hora del baño! {name} chapoteaba y reía mientras el agua salpicaba por todos lados. {pet_name} observaba desde la puerta con la cabeza ladeada. Una ola de agua le mojó la nariz a {pet_name}. ¡Y las risas de {name} fueron aún más grandes!",
        "text_en": "Bath time! {name} splashed and laughed as water went everywhere. {pet_name} watched from the doorway with a tilted head. A wave of water splashed {pet_name}'s nose. And {name}'s laughter grew even bigger!",
        "prompt": "Disney Pixar 3D style illustration. CAST: @image1 = {gender_word} baby (fully human body, smooth skin, two arms). @image2 = {pet_name} ({pet_desc}): animal body, four paws, fur coat. Match both references exactly. Two distinct separate beings. Exactly ONE 5-month-old baby in bathtub + exactly ONE pet in the doorway. SCENE: 5-month-old {gender_word} sits in a small baby bathtub at CENTER wearing only a diaper, splashing water with both hands in pure joy, mouth open laughing, water droplets flying in all directions. {pet_name} stands in the bathroom doorway at LEFT, head tilted sideways, nose wet from a flying water droplet, one paw raised in comic surprise, amused expression. SETTING: Bright bathroom WIDE VIEW, small baby tub with bubbles, rubber duck on the edge, water droplets catching the light, folded towel on the rack. ATMOSPHERE: Playful explosive joy, bright bathroom light, water droplets sparkling, pure funny chaos. {style}",
        "text_position": "split"
    },
    {
        "id": 9,
        "text_es": "Durante el tiempo boca abajo, {name} levantó la cabecita por primera vez. ¿Y qué vio? A {pet_name}, echado en el suelo, nariz con nariz. {name} y {pet_name} se miraron durante un largo momento mágico, como si se contaran secretos sin palabras.",
        "text_en": "During tummy time, {name} lifted their little head for the first time. And what did they see? {pet_name}, lying on the floor, nose to nose. {name} and {pet_name} looked at each other for a long magical moment, as if sharing secrets without words.",
        "prompt": "Disney Pixar 3D style illustration. CAST: @image1 = {gender_word} baby (fully human body, smooth skin, two arms). @image2 = {pet_name} ({pet_desc}): animal body, four paws, fur coat. Match both references exactly. Two distinct separate beings at floor level. Exactly ONE 4-month-old baby doing tummy time + exactly ONE pet lying flat face-to-face. SCENE: 4-month-old {gender_word} does tummy time on a soft play mat at LEFT wearing a mint green onesie, head lifted up proudly for the first time, big curious eyes looking directly at {pet_name} with a tiny smile. {pet_name} lies completely flat at RIGHT with chin on the mat, face to face with the baby, nose almost touching the baby's nose, gentle loving eyes returning the gaze. SETTING: Living room floor WIDE VIEW, soft play mat, warm sunlight pooling on the floor, toys scattered at the edges. ATMOSPHERE: Magical eye-level connection, warm intimate golden light, quiet understanding. {style}",
        "text_position": "split"
    },
    {
        "id": 10,
        "text_es": "¡{name} se movió! Primero fue un balanceo torpe, luego las rodillitas empezaron a funcionar. ¿Hacia dónde fue la primera aventura de {name}? Directo hacia {pet_name}, por supuesto. Siempre hacia {pet_name}.",
        "text_en": "{name} moved! First a wobbly rocking, then the little knees started working. Where did {name}'s first adventure go? Straight toward {pet_name}, of course. Always toward {pet_name}.",
        "prompt": "Disney Pixar 3D style illustration. CAST: @image1 = {gender_word} baby (fully human body, smooth skin, two arms, two legs on all fours). @image2 = {pet_name} ({pet_desc}): animal body, four paws, fur coat. Match both references exactly. Two distinct separate beings. Exactly ONE 7-month-old baby crawling on hands and knees + exactly ONE pet sitting and waiting. SCENE: 7-month-old {gender_word} crawls on hands and knees at LEFT wearing a soft blue onesie, face set with determined joy, heading straight toward {pet_name}. {pet_name} sits at RIGHT facing the crawling baby, leaning forward with bright eager eyes, tail wagging, welcoming the approaching baby. SETTING: Living room WIDE VIEW, soft carpet, warm afternoon light. ATMOSPHERE: First crawl milestone, triumphant joy, warm golden light. {style}",
        "text_position": "split"
    },
    {
        "id": 11,
        "text_es": "En el jardín, {name} tocó el pasto por primera vez. Era cosquilloso, verde y olía a aventura. {pet_name} corrió en círculos de alegría alrededor de {name}. {name} reía y reía y reía.",
        "text_en": "In the garden, {name} touched grass for the first time. It was tickly, green, and smelled like adventure. {pet_name} ran in happy circles around {name}. {name} laughed and laughed and laughed.",
        "prompt": "Disney Pixar 3D style illustration. CAST: @image1 = {gender_word} baby (fully human body, smooth skin, two arms, two legs). @image2 = {pet_name} ({pet_desc}): animal body, four paws, fur coat. Match both references exactly. Two distinct separate beings. Exactly ONE 8-month-old baby sitting on grass + exactly ONE pet running circles around them. SCENE: 8-month-old {gender_word} sits on green grass at CENTER wearing an orange onesie, both hands pressed into the grass blades with wonder, laughing with mouth open, bare feet on the lawn. {pet_name} runs joyfully at RIGHT in a happy circle around the sitting baby, bounding with pure energy, looping back toward them. SETTING: Beautiful home garden WIDE VIEW, lush green lawn, colorful flowers, blue sky, bright golden sunshine, butterflies in the air. ATMOSPHERE: First outdoor adventure, bright sunny joy, pure happiness. {style}",
        "text_position": "split"
    },
    {
        "id": 12,
        "text_es": "Un día, {name} se puso a llorar sin saber muy bien por qué. Las lágrimas caían una tras otra. Y entonces apareció {pet_name}, se acurrucó justo a su lado y apoyó suavemente su nariz en la mejilla de {name}. Las lágrimas se detuvieron. Y apareció una sonrisa.",
        "text_en": "One day, {name} started crying without quite knowing why. Tears fell one after another. And then {pet_name} appeared, snuggled right beside them, and gently pressed their nose against {name}'s cheek. The tears stopped. And a smile appeared.",
        "prompt": "Disney Pixar 3D style illustration. CAST: @image1 = {gender_word} baby (fully human body, smooth skin, two arms, two legs). @image2 = {pet_name} ({pet_desc}): animal body, four paws, fur coat. Match both references exactly. Two distinct separate beings. Exactly ONE 9-month-old baby sitting + exactly ONE pet pressing nose to baby's cheek. SCENE: 9-month-old {gender_word} sits on a soft rug at CENTER wearing a yellow onesie, face mid-transition from tears to a surprised smile, cheeks slightly wet. {pet_name} sits right beside the baby at RIGHT, head gently tilted with nose pressed softly to the baby's cheek, eyes full of tender concern, body leaning warmly in. SETTING: Cozy living room floor WIDE VIEW, soft rug, afternoon light through curtains. ATMOSPHERE: Tender comfort, tears turning to smiles, unconditional love. {style}",
        "text_position": "split"
    },
    {
        "id": 13,
        "text_es": "La hora de la comida era la favorita de {pet_name}. {name} comía con las manos, con la cara, con toda el alma. Y lo que caía al suelo... bueno, {pet_name} siempre estaba listo para \"ayudar a limpiar\". ¡{name} y {pet_name}, el mejor equipo del mundo!",
        "text_en": "Mealtime was {pet_name}'s favorite. {name} ate with hands, with face, with whole heart and soul. And what fell to the floor... well, {pet_name} was always ready to \"help clean up.\" {name} and {pet_name}, the best team in the world!",
        "prompt": "Disney Pixar 3D style illustration. CAST: @image1 = {gender_word} baby (completely human body, soft skin, two arms, two legs). @image2 = {pet_name} ({pet_desc}): animal's body, four legs, fur coat. Both references match exactly. Two different and separate beings. Exactly ONE 10 month old baby in a raised high chair in the CENTER + exactly ONE pet sitting on the kitchen floor downstairs looking up. SCENE: {gender_word}, 10 months old, is sitting in a high chair in the CENTER (elevated above floor level), wearing a bib over a onesie, face with little stains of colorful puree, hands gloriously dirty, dropping food onto the tray with a giggle. {pet_name} sits on the kitchen floor directly under the high chair tray, looking up with an anxious expression, eating what {gender_word} drops, tongue hanging out and tail wagging rapidly. SETTING: Kitchen dining room WIDE VIEW, high chair in the center, colorful food on the tray and baby's face, pieces of food on the floor around the pet, bright and cheerful kitchen. ATMOSPHERE: Happy, messy teamwork, bright light in the kitchen, comical warmth. {style}",
        "text_position": "split"
    },
    {
        "id": 14,
        "text_es": "Un día, {name} descubrió la camita de {pet_name}. Era suavecita, olía a {pet_name} y era perfecta para sentarse. {pet_name} observó la situación con mucha, mucha paciencia. Aunque su cama era, claramente, la mejor cama del mundo.",
        "text_en": "One day, {name} discovered {pet_name}'s bed. It was so soft, smelled like {pet_name}, and was perfect for sitting in. {pet_name} watched with a great, great deal of patience. Even though the bed was, clearly, the best bed in the world.",
        "prompt": "Disney Pixar 3D style illustration. CAST: @image1 = {gender_word} baby (fully human body, smooth skin, two arms, two legs{baby_bow}). @image2 = {pet_name} ({pet_desc}): animal body, four paws, fur coat. Match both references exactly. Two distinct separate beings. Exactly ONE 11-month-old baby sitting inside a round pet bed + exactly ONE pet watching beside it. SCENE: 11-month-old {gender_word} sits contentedly inside a plush round pet bed at LEFT wearing a soft onesie, big pleased grin, surrounded by the cozy cushioned edges. {pet_name} sits just beside the claimed bed at RIGHT, watching the baby with patient gentle expression, head slightly tilted. SETTING: Cozy living room corner WIDE VIEW, soft warm rug, round plush pet bed, warm afternoon light. ATMOSPHERE: Gentle humor, patient love, cozy warmth. {style}",
        "text_position": "split"
    },
    {
        "id": 15,
        "text_es": "A {name} le encantaba explorar a {pet_name} con sus manitas curiosas. Las orejas, el pelaje suave, la colita. {pet_name} se quedaba perfectamente quieto, con una paciencia infinita. Porque para {pet_name}, las manitas de {name} eran lo más maravilloso del mundo.",
        "text_en": "{name} loved exploring {pet_name} with curious little hands. The ears, the soft fur, the tail. {pet_name} stayed perfectly still with infinite patience. Because for {pet_name}, {name}'s little hands were the most wonderful thing in the world.",
        "prompt": "Disney Pixar 3D style illustration. CAST: @image1 = {gender_word} baby (fully human body, smooth skin, two arms, two legs{baby_bow}). @image2 = {pet_name} ({pet_desc}): animal body, four paws, fur coat. Match both references exactly. Two distinct separate beings. Exactly ONE 11-month-old baby sitting and touching the pet's ear + exactly ONE pet sitting perfectly still. SCENE: 11-month-old {gender_word} sits cross-legged at LEFT on a soft rug wearing a striped onesie, both hands gently touching {pet_name}'s ear, mouth open in wonder. {pet_name} sits completely still directly in front of the baby, eyes soft and patient, one ear gently held by the baby's tiny hands, expression of infinite patience. SETTING: Warm living room floor WIDE VIEW, soft rug, gentle afternoon light. ATMOSPHERE: Curious discovery, infinite patience, deep trust. {style}",
        "text_position": "split"
    },
    {
        "id": 16,
        "text_es": "Y entonces llegó el día más esperado. {name} se soltó de la mesa, abrió los brazos... ¡y caminó! Uno, dos, tres pasitos tambaleantes. ¿Hacia dónde? Hacia {pet_name}. Los primeros pasos de {name} fueron para llegar a {pet_name}.",
        "text_en": "And then came the most awaited day. {name} let go of the table, opened their arms... and walked! One, two, three wobbly steps. Where to? Toward {pet_name}. {name}'s first steps were to reach {pet_name}.",
        "prompt": "Disney Pixar 3D style illustration. CAST: @image1 = {gender_word} baby (fully human body, smooth skin, two arms stretched wide, two legs standing upright{baby_bow}). @image2 = {pet_name} ({pet_desc}): animal body, four paws, fur coat. Match both references exactly. Two distinct separate beings. Exactly ONE 12-month-old toddler taking unaided first steps + exactly ONE pet sitting and waiting to receive them. SCENE: 12-month-old {gender_word} stands freely at LEFT wearing a light blue onesie, both arms stretched wide for balance, taking wobbly first steps forward, face full of proud joy. {pet_name} sits at RIGHT facing the toddler, leaning forward with bright excited eyes, ready to receive the walking baby. SETTING: Living room WIDE VIEW, clear open floor, warm golden afternoon light. ATMOSPHERE: First steps milestone, golden celebratory light, pure pride and joy. {style}",
        "text_position": "split"
    },
    {
        "id": 17,
        "text_es": "Los cubos de colores eran la gran pasión de {name}. ¡Uno encima de otro, más y más alto! Cuando la torre se caía, {pet_name} daba un saltito de susto. Y las carcajadas de {name} eran tan grandes que había que volver a empezar.",
        "text_en": "Colorful stacking cups were {name}'s great passion. One on top of another, higher and higher! When the tower fell, {pet_name} jumped with a startled look. And {name}'s laughter was so big they had to start all over again.",
        "prompt": "Disney Pixar 3D style illustration. CAST: @image1 = {gender_word} baby (fully human body, smooth skin, two arms, two legs{baby_bow}). @image2 = {pet_name} ({pet_desc}): animal body, four paws, fur coat. Match both references exactly. Two distinct separate beings. Exactly ONE 13-month-old toddler playing with stacking cups + exactly ONE pet watching attentively. SCENE: 13-month-old {gender_word} sits on a colorful play mat at LEFT wearing a cheerful shirt and soft pants, both hands placing a bright cup on a small tower, soft smile of concentration, focused eyes. {pet_name} sits at RIGHT watching every move with intense curious eyes, ears perked forward, leaning slightly toward the activity. SETTING: Living room play area WIDE VIEW, soft play mat, bright stacking cups in multiple colors, warm afternoon light. ATMOSPHERE: Playful concentration, quiet indoor joy, companionable focus. {style}",
        "text_position": "split"
    },
    {
        "id": 18,
        "text_es": "Después de tanto jugar, llegó la hora de la siesta. Los ojos de {name} se fueron cerrando despacito... despacito... hasta que llegó el sueño. {pet_name} se acurrucó justo al lado de su cuna y cerró también los ojos. Así era el mejor final del día: dormirse juntos.",
        "text_en": "After so much playing, nap time arrived. {name}'s eyes slowly closed... slowly... until sleep arrived. {pet_name} snuggled right beside the crib and also closed their eyes. That was the best ending to the day: falling asleep together.",
        "prompt": "Disney Pixar 3D style illustration. CAST: @image1 = {gender_word} baby (fully human body, smooth skin{baby_bow}). @image2 = {pet_name} ({pet_desc}): animal body, four paws, fur coat. Match both references exactly. Two distinct separate beings — child in crib above, pet on floor below. Exactly ONE 13-month-old toddler asleep in crib + exactly ONE pet curled asleep on the floor beside it. SCENE: 13-month-old {gender_word} sleeps peacefully inside the crib at CENTER, soft blanket tucked around, angelic face. {pet_name} lies curled into a compact sleeping ball on the floor directly beside the crib at RIGHT, eyes closed, body curved peacefully, faithful even in rest. SETTING: Cozy nursery WIDE VIEW, white crib, soft rug, warm golden afternoon light through curtains. ATMOSPHERE: Perfect shared rest, warm golden afternoon, faithful love. {style}",
        "text_position": "split"
    },
    {
        "id": 19,
        "text_es": "{name} abrió los brazos lo más que pudo y abrazó a {pet_name} con todo el corazón. {pet_name} se quedó quieto, cálido y suave, como si supiera exactamente lo que {name} necesitaba. En ese abrazo estaba todo: la historia de un año entero juntos.",
        "text_en": "{name} opened their arms as wide as they could and held {pet_name} with all their heart. {pet_name} stayed still, warm, and gentle, as if knowing exactly what {name} needed. In that hug was everything: the story of a whole year together.",
        "prompt": "Disney Pixar 3D style illustration. CAST: @image1 = {gender_word} baby (completely human body, soft skin, two arms, two legs{baby_bow}). @image2 = {pet_name} ({pet_desc}): animal's body, four legs, fur coat. It matches both references exactly. Two different beings, both clearly visible in the embrace. Exactly ONE 14 month old hugging + exactly ONE pet receiving the hug. SCENE: 14-month-old {gender_word} is sitting on a soft rug, arms open around {pet_name} in a big, heartfelt hug, eyes closed in pure happiness, cheek pressed against {pet_name}'s body. {pet_name} sits perfectly still receiving the hug, eyes gently closed and body gently leaning into the hug, calm and content. SETTING: Warm sunny living room floor WIDE VIEW, soft carpet, golden afternoon light. ATMOSPHERE: Emotional friendship, warm golden light, love beyond words, a year of memories. {style}",
        "text_position": "split"
    }
]

CLOSING_SCENE = {
    "id": 20,
    "prompt": "Disney Pixar 3D style illustration. CAST: @image1 = {gender_word} baby (fully human body, smooth skin{baby_bow}). @image2 = {pet_name} ({pet_desc}): animal body, four paws, fur coat. Match both references exactly. Two distinct separate beings — child in toddler bed above, pet on floor below. Exactly ONE 16-month-old toddler asleep in toddler bed + exactly ONE pet asleep on the floor beside it. SCENE: 16-month-old {gender_word} sleeps peacefully in a small toddler bed at CENTER, a star-patterned blanket tucked snugly around, one tiny arm dangling over the bed edge reaching down toward {pet_name}. {pet_name} sleeps on the floor right beside the bed, head resting close to the dangling hand, one paw touching the bed frame, protective even in sleep. SETTING: Cozy bedroom at night WIDE VIEW, warm nightlight casting a soft golden glow, stars visible through the window, soft pillows, peaceful shadows. ATMOSPHERE: Perfect peaceful ending, warm nightlight glow, eternal faithful love, a story without end. {style}",
    "text_position": "none"
}

FRONT_COVER = {
    "prompt": "Disney Pixar 3D style illustration. CAST: @image1 = {gender_word} newborn (fully human body, smooth skin, tiny human face). @image2 = {pet_name} ({pet_desc}): animal body, four paws, fur coat. Match both references exactly. Two distinct separate beings. Exactly ONE newborn baby + exactly ONE pet. Pure illustration only. SCENE: Newborn {gender_word} lies in a bassinet at CENTER-RIGHT, wrapped snugly in a soft white blanket, tiny peaceful face visible above the blanket. {pet_name} stands at LEFT leaning gently forward, nose approaching the newborn's tiny face for the very first time, eyes soft and tender with wonder, tail slightly wagging. SETTING: Warm cozy nursery, soft golden light through sheer curtains, pastel walls, intimate atmosphere. ATMOSPHERE: Sacred first meeting, pure tenderness, warm golden glow, a love story beginning, book cover quality. {style}"
}

BACK_COVER = {
    "prompt": "Disney Pixar 3D style illustration. SETTING: A beautiful cozy baby nursery room WIDE VIEW, soft pastel walls with tiny paw prints and stars, a wooden crib with a soft blanket and a small plush dog toy inside, a rocking chair with a children's storybook on it, soft carpet on the floor, warm golden light from a star-shaped nightlight, mobile hanging with animal shapes, shelves with children's books and stuffed animals, window showing a starry night sky. ATMOSPHERE: Warm peaceful magical nursery, soft dreamy golden lighting, ready for bedtime stories. Pure illustration only. {style}"
}


def build_human_preview_prompt(human_desc: str, is_baby: bool = False) -> str:
    if is_baby:
        is_girl = 'baby girl' in human_desc.lower()
        is_boy = 'baby boy' in human_desc.lower()
        outfit = "soft pink baby romper, fully clothed from shoulders to ankles" if is_girl else "white or soft blue baby onesie, fully clothed from shoulders to ankles" if is_boy else "soft white baby onesie, fully clothed from shoulders to ankles"
        return (
            f"High-quality 3D animated children's book illustration. "
            f"CHARACTER: {human_desc}. "
            f"OUTFIT: {outfit}. "
            f"FULL BODY portrait, sitting naturally on the floor, warm happy expression, bright eyes, "
            f"chubby baby proportions, centered in frame, occupying 60% of frame height. "
            f"NEUTRAL SOLID GRADIENT BACKGROUND (soft cream to warm beige), plain studio. "
            f"Soft warm lighting. Clean illustration only."
        )
    return f"Disney Pixar 3D style illustration. FULL BODY portrait of {human_desc}, wearing a white diaper or soft onesie or pajamas (always clothed), standing naturally, warm smile, centered in frame, occupying 60% of frame height. NEUTRAL SOLID GRADIENT BACKGROUND (soft cream to warm beige), plain studio background, studio portrait style. Natural friendly expression, relaxed standing pose. Clean professional animation art, clean illustration only. All babies wear a diaper, onesie, or pajamas — always clothed."


def build_human_preview_prompt_with_photo(gender_word: str, age_display: str, eye_desc: str = "", hair_desc: str = "", glasses: str = "", facial_hair: str = "", skin_tone: str = "") -> str:
    glasses_desc = " MUST be wearing glasses" if glasses == "glasses" else " MUST be wearing sunglasses" if glasses == "sunglasses" else ""
    facial_hair_map = {'stubble': 'light stubble', 'short_beard': 'short beard', 'full_beard': 'full thick beard', 'mustache': 'mustache'}
    facial_hair_desc = f" MUST have {facial_hair_map[facial_hair]}" if facial_hair and facial_hair != 'none' and facial_hair in facial_hair_map else ""
    accessories = (glasses_desc + facial_hair_desc).strip()
    hair_part = f", {hair_desc}" if hair_desc and "matching the reference" not in hair_desc else ""
    skin_strict = f"STRICT: maintain {skin_tone} complexion — do not lighten the skin tone. " if skin_tone else ""
    if "baby" in gender_word.lower():
        return (
            f"Disney Pixar 3D style illustration. "
            f"OUTFIT: the baby wears a soft sage-green or forest-green baby romper with a small leaf and tree print — cute unisex style, body fully clothed from shoulders to ankles. "
            f"CHARACTER: 3D animated {gender_word} with face shape, skin complexion, hair amount and color, and eye color all matching @image1 exactly — do not invent or change any physical feature. "
            f"FULL BODY portrait, centered, warm happy expression. "
            f"NEUTRAL SOLID GRADIENT BACKGROUND (soft cream to warm beige). "
            f"Baby is dressed in the green romper — always clothed, shoulders to ankles. "
            f"If the baby in the photo has little or no hair, generate little or no hair — match the reference exactly. "
            f"{skin_strict}"
            f"Clean illustration only."
        )
    return f"Disney Pixar 3D style illustration. 3D animated character of the {gender_word} from @image1, {eye_desc} eyes{hair_part}, full face and skin matching @image1 exactly.{(' ' + accessories + '.') if accessories else ''} FULL BODY portrait, centered, warm expression. NEUTRAL SOLID GRADIENT BACKGROUND (soft cream to warm beige). Clean illustration only."


def build_pet_preview_prompt(pet_desc: str, pet_size: str = "medium") -> str:
    size_desc_map = {
        "small":  "compact small body, fits fully in frame with space around it",
        "medium": "full body fits naturally and comfortably in frame",
        "large":  "big imposing body fills the frame, broad and tall",
    }
    size_desc = size_desc_map.get(pet_size, size_desc_map["medium"])
    return f"Disney Pixar 3D style illustration. FULL BODY portrait of {pet_desc}, sitting or standing naturally, friendly expression, centered in frame, occupying 50% of frame height, {size_desc}. NEUTRAL SOLID GRADIENT BACKGROUND (soft cream to warm beige), plain studio background, studio portrait style. Warm lighting, expressive eyes. Clean professional animation art, clean illustration only."


def build_pet_preview_prompt_with_photo(pet_desc: str = "", pet_species: str = "dog", pet_size: str = "medium") -> str:
    animal = "cat" if pet_species == "cat" else "dog"
    size_desc_map = {
        "small":  "a small-sized animal — compact body, fits fully in frame with space around it",
        "medium": "a medium-sized animal — full body fits naturally and comfortably in frame",
        "large":  "a large-sized animal — big imposing body fills the frame, broad and tall",
    }
    size_desc = size_desc_map.get(pet_size, size_desc_map["medium"])
    desc_hint = f" ({pet_desc})" if pet_desc else ""
    return f"High-quality 3D animated children's book illustration. 3D animated character of the {animal} from @image1{desc_hint}. FULL BODY portrait, sitting or standing naturally, friendly expression, centered. {size_desc}. NEUTRAL SOLID GRADIENT BACKGROUND (soft cream to warm beige). Warm lighting. Clean animation art, clean illustration only."


_HAIR_COLOR_MAP = {
    'black': 'jet black',
    'brown': 'medium brown',
    'light_brown': 'warm light brown (caramel-honey tone)',
    'blonde': 'dark dirty blonde',
    'very_light_blonde': 'pale platinum blonde',
    'red': 'bright red',
    'auburn': 'auburn',
}

_PET_SIZE_RELATIVE = {
    "small":  "smaller than the baby",
    "medium": "similar in size to the baby",
    "large":  "larger than the baby",
}


def build_scene_prompt(scene: dict, human_desc: str, pet_name: str, pet_desc: str, eye_desc: str = "", gender_word: str = "baby", glasses: str = "", hair_color: str = "", **kwargs) -> str:
    prompt = scene.get('prompt', '')
    scene_id = scene.get('id', 0)
    pet_species = kwargs.get('pet_species', 'dog')
    animal_word = "cat" if pet_species == "cat" else "dog"

    # Enrich pet_desc with relative size so FLUX knows the animal's scale next to the baby
    pet_size = kwargs.get('pet_size', 'medium')
    size_rel = _PET_SIZE_RELATIVE.get(pet_size, '')
    if size_rel and pet_desc:
        pet_desc_for_prompt = f"{pet_desc}, {size_rel}"
    elif size_rel:
        pet_desc_for_prompt = size_rel
    else:
        pet_desc_for_prompt = pet_desc

    prompt = prompt.replace('{human_desc}', human_desc)
    prompt = prompt.replace('{pet_name}', pet_name)
    prompt = prompt.replace('{pet_desc}', pet_desc_for_prompt)
    prompt = prompt.replace('{gender_word}', gender_word)

    # baby_bow: tiny pink bow for girl babies in scenes 14+ (not in reference — appears as baby grows)
    is_girl = gender_word.lower() in ('girl', 'niña', 'baby girl')
    baby_bow = ", a tiny pink bow hair clip" if is_girl and scene_id >= 14 else ""
    prompt = prompt.replace('{baby_bow}', baby_bow)

    # Replace hardcoded "dog" references with the actual animal from the user's form
    if pet_species == 'cat':
        prompt = prompt.replace('ONE pet', 'ONE cat')
        prompt = prompt.replace('the dog', 'the cat')
        prompt = prompt.replace("dog's", "cat's")
        prompt = prompt.replace(' dog ', ' cat ')
        prompt = prompt.replace(' dog,', ' cat,')
        prompt = prompt.replace(' dog.', ' cat.')

    # Handle generic "ONE pet" patterns
    prompt = prompt.replace('ONE pet', f'ONE {animal_word}')

    prompt = prompt.replace('{style}', STYLE_BASE)

    # Reinforce eye color explicitly (references alone are unreliable for FLUX fidelity)
    eye_color_only = eye_desc.replace(' eyes', '').strip() if eye_desc else ''
    if eye_color_only:
        prompt += f" EYES: the {gender_word} baby has {eye_color_only} eyes, matching @image1 exactly."

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
