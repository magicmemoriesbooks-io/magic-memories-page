# Tú y tu Amor Peludo - Adventure Story Prompts
# 19 scenes + closing + covers
# Story: "Las aventuras de [Mascota] y [Nombre]" - Park adventure with mystery
# Ages 3-8 - Exploration, problem-solving, treasure hunt
#
# FLUX 2 Dev with TWO reference images:
#   1. Human preview: detailed character description → generates reference image 1
#   2. Pet preview: detailed pet description → generates reference image 2
#   3. Scenes: FLUX 2 Dev takes BOTH references → prompts bind roles explicitly
#
# Schema (same as furry_love baby):
#   HUMAN CHARACTER → PET CHARACTER → ACTION → SETTING → ATMOSPHERE → STRICT
#
# Rules:
#   - guidance_scale=3.5, num_inference_steps=28, aspect_ratio=3:4
#   - Keep prompts concise - FLUX 2 Dev loses focus with >300 words
#   - Style: Disney Pixar 3D everywhere, NO watercolor
#   - Human is a child (3-8 years old)
#   - Pet is a dog or cat (customized breed, color, pattern)
#   - TWO reference images per scene (human + pet)
#   - Text uses {name} for human and {pet_name} for pet
#   - OUTFIT CONSISTENCY: Child wears SAME adventure outfit in scenes 2-18.
#     Scene 1 = pajamas (waking up). Scene 19 = clean pajamas (bedtime).
#     Closing = pajamas in bed. {adventure_outfit} is gender-specific.

STYLE_BASE = "Disney Pixar 3D style, soft warm golden lighting, adventurous atmosphere, WIDE SHOT full body from head to feet, characters occupy 40% of frame, outdoor park and nature environment visible, clean illustration only. STRICT: Children wear appropriate outdoor clothes, fully clothed always."

ADVENTURE_OUTFIT_BOY = "light green t-shirt, khaki cargo shorts, white sneakers, small brown backpack"
ADVENTURE_OUTFIT_GIRL = "light green t-shirt, denim shorts, white sneakers, small brown backpack"
PAJAMA_DESC = "cozy soft pajamas"
CLEAN_PAJAMA_DESC = "fresh clean pajamas"

FURRY_LOVE_ADVENTURE_SCENES = [
    {
        "id": 1,
        "text_es": "Una mañana de sábado, {name} abrió los ojos y sintió algo cálido y suave acurrucado a sus pies. Era {pet_name}, que ya llevaba un rato despierto, esperando con paciencia a que su mejor amigo se levantara.",
        "text_en": "One Saturday morning, {name} opened their eyes and felt something warm and soft curled up at their feet. It was {pet_name}, who had been awake for a while, patiently waiting for their best friend to wake up.",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: A {gender_word} ({age_display}) with {hair_desc}, {eye_desc} eyes{glasses_desc} waking up in bed, stretching with a big smile, wearing {pajama_desc}, looking down at the foot of the bed. PET: {pet_desc}, curled up at the foot of the bed, head raised looking at the child with bright excited eyes, tail starting to wag. ACTION: The child wakes up and discovers their pet waiting at the foot of the bed, both sharing an excited morning look. SETTING: Cozy children's bedroom WIDE VIEW, morning sunlight streaming through window, colorful posters on walls, toys on shelves. ATMOSPHERE: Exciting morning, warm golden sunlight, anticipation of adventure. STRICT: Only ONE child in bed, ONE pet at foot of bed, cozy bedroom scene. {style}",
        "text_position": "split"
    },
    {
        "id": 2,
        "text_es": "\"¡Hoy vamos a tener una aventura!\", dijo {name} saltando de la cama. Después del desayuno, preparó su mochila y {pet_name} ya estaba esperando junto a la puerta, dando vueltas de emoción. El parque los llamaba.",
        "text_en": "\"Today we're going on an adventure!\" said {name}, jumping out of bed. After breakfast, they packed their backpack and {pet_name} was already waiting by the door, spinning with excitement. The park was calling.",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: A {gender_word} ({age_display}) with {hair_desc}, {eye_desc} eyes{glasses_desc} standing at the front door wearing {adventure_outfit}, excited determined expression, one hand on the door handle ready to go. PET: {pet_desc}, standing by the door spinning in circles with excitement, tail wagging fast, looking up at the child eagerly. ACTION: Child opens the front door ready for adventure while the pet spins with excitement beside them, both eager to leave. SETTING: Home entryway WIDE VIEW, front door with sunlight streaming in, coat hooks on wall, shoes lined up, bright cheerful morning outside. ATMOSPHERE: Departure excitement, bright morning energy, adventure awaits. STRICT: Only ONE child, ONE excited pet, doorway departure scene. {style}",
        "text_position": "split"
    },
    {
        "id": 3,
        "text_es": "{pet_name} iba adelante, olisqueando cada rincón del camino. De pronto, se detuvo en seco. Su nariz apuntaba hacia el suelo, donde unas huellas extrañas marcaban el camino de tierra. Eran grandes, redondas y brillaban con un polvo dorado.",
        "text_en": "{pet_name} went ahead, sniffing every corner of the path. Suddenly, they stopped dead. Their nose pointed at the ground, where strange tracks marked the dirt path. They were big, round, and sparkled with golden dust.",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: A {gender_word} ({age_display}) with {hair_desc}, {eye_desc} eyes{glasses_desc} crouching down on a dirt path, wearing {adventure_outfit}, looking at mysterious golden glowing footprints on the ground with wide curious eyes, one hand reaching toward the tracks. PET: {pet_desc}, nose pressed to the ground next to the golden tracks, alert posture, ears perked forward, following the scent intensely. ACTION: Child and pet discover mysterious golden glowing footprints on a park path, both investigating the tracks with curiosity. SETTING: Park dirt path WIDE VIEW, tall trees on both sides, dappled sunlight, mysterious golden glowing paw prints trailing into the distance, fallen leaves around. ATMOSPHERE: Mystery and discovery, magical golden glow from tracks, curious adventurous feeling. STRICT: Only ONE child crouching, ONE pet sniffing tracks, mysterious park path scene. {style}",
        "text_position": "split"
    },
    {
        "id": 4,
        "text_es": "\"¿Qué será eso?\", susurró {name}, agachándose para ver más de cerca. {pet_name} olfateó las huellas con cuidado y luego miró a {name}, como diciendo: \"¿Las seguimos?\" Las huellas doradas los llevaron hasta un arbusto enorme que temblaba.",
        "text_en": "\"What could that be?\" whispered {name}, bending down for a closer look. {pet_name} sniffed the tracks carefully and then looked at {name}, as if saying: \"Should we follow them?\" The golden tracks led them to a huge bush that was trembling.",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: A {gender_word} ({age_display}) with {hair_desc}, {eye_desc} eyes{glasses_desc} standing cautiously in front of a large trembling bush, wearing {adventure_outfit}, one hand reaching to part the branches, face showing excitement mixed with nervousness. PET: {pet_desc}, in alert posture beside the child, ears fully erect, body tense and ready, looking at the shaking bush with intense focus. ACTION: Child and pet approach a mysterious trembling bush, golden tracks leading right to it, both cautious but brave. SETTING: Park clearing WIDE VIEW, one enormous dense bush shaking and rustling, golden footprints ending at the bush, dappled forest light, leaves falling from movement. ATMOSPHERE: Suspense and excitement, dramatic lighting through trees, mysterious rustling. STRICT: Only ONE child, ONE alert pet, one trembling bush, suspenseful moment. {style}",
        "text_position": "split"
    },
    {
        "id": 5,
        "text_es": "Los dos amigos se miraron con valentía. {name} apartó las ramas con cuidado... ¡Era una mariposa enorme, del tamaño de un plato! Sus alas brillaban con todos los colores del arcoíris y dejaba un rastro de polvo dorado.",
        "text_en": "The two friends looked at each other bravely. {name} carefully parted the branches... It was an enormous butterfly, the size of a plate! Its wings shimmered with every color of the rainbow and left a trail of golden dust.",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: A {gender_word} ({age_display}) with {hair_desc}, {eye_desc} eyes{glasses_desc} standing with arms raised in amazement, wearing {adventure_outfit}, mouth open in wonder, looking up at a giant magical rainbow butterfly flying above. PET: {pet_desc}, jumping up trying to catch the butterfly, body stretched mid-leap, playful and excited expression, tail wagging in the air. ACTION: A magical giant rainbow butterfly emerges from a bush, the child watches in awe while the pet leaps trying to catch it, golden dust trailing from the butterfly wings. SETTING: Park clearing WIDE VIEW, bright sunlight, a giant iridescent butterfly with rainbow wings leaving golden sparkle trails, bush behind, flowers and grass around. ATMOSPHERE: Magical wonder, rainbow light from butterfly wings, golden sparkles in the air, pure joy. STRICT: Only ONE child, ONE pet jumping, ONE giant rainbow butterfly, magical discovery scene. {style}",
        "text_position": "split"
    },
    {
        "id": 6,
        "text_es": "{pet_name} saltó intentando atraparla, girando en el aire como un acróbata torpe. {name} se cayó al suelo de la risa. La mariposa los guió hasta un enorme charco que brillaba bajo el sol. ¡{pet_name} saltó directo al agua con un tremendo SPLASH!",
        "text_en": "{pet_name} leaped trying to catch it, spinning in the air like a clumsy acrobat. {name} fell to the ground laughing. The butterfly guided them to a huge puddle glistening under the sun. {pet_name} jumped straight into the water with a tremendous SPLASH!",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: A {gender_word} ({age_display}) with {hair_desc}, {eye_desc} eyes{glasses_desc} standing near a huge mud puddle, wearing {adventure_outfit} now splashed with water, laughing hysterically with eyes squinted, arms up to shield from water. PET: {pet_desc}, mid-leap into the center of a large puddle, all four paws tucked under body, playful excited expression, massive water splash erupting around them. ACTION: The pet makes a playful leap into a giant puddle creating a massive splash that soaks the laughing child standing nearby, comedic joyful moment. SETTING: Park path WIDE VIEW, enormous puddle reflecting the sky, water droplets frozen mid-air catching sunlight, muddy edges, trees in background. ATMOSPHERE: Hilarious chaos, bright sunlight through water droplets creating mini rainbows, pure joyful mess. STRICT: Only ONE child getting splashed, ONE pet leaping into puddle, comedic splash scene. {style}",
        "text_position": "split"
    },
    {
        "id": 7,
        "text_es": "El agua salpicó por todos lados, empapando a {name} de pies a cabeza. Al otro lado del parque, una vieja cerca de madera escondía algo que {name} nunca había visto. La mariposa dorada pasó volando por encima, invitándolos a seguir.",
        "text_en": "Water splashed everywhere, soaking {name} from head to toe. On the other side of the park, an old wooden fence was hiding something {name} had never seen. The golden butterfly flew over it, inviting them to follow.",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: A {gender_word} ({age_display}) with {hair_desc}, {eye_desc} eyes{glasses_desc} crouching down to crawl under a gap in an old wooden fence, wearing {adventure_outfit} now slightly damp and muddy, determined adventurous expression, peeking through to the other side. PET: {pet_desc}, already halfway through the gap in the fence, squeezing under with excited expression, body low to the ground. ACTION: Child and pet sneak under an old wooden fence into a secret area, a golden butterfly visible flying just ahead on the other side. SETTING: Old wooden fence WIDE VIEW, a gap at the bottom big enough to crawl through, wild ivy and flowers growing on the fence, mysterious green glow from the other side, golden butterfly ahead. ATMOSPHERE: Sneaky adventure, forbidden territory excitement, mysterious light from beyond the fence. STRICT: Only ONE child crawling under fence, ONE pet squeezing through, adventure discovery scene. {style}",
        "text_position": "split"
    },
    {
        "id": 8,
        "text_es": "{name} miró a {pet_name}. {pet_name} miró a {name}. Sin decir una palabra, los dos se agacharon y pasaron por debajo de la cerca. Lo que encontraron al otro lado los dejó con la boca abierta: un jardín secreto con flores enormes de todos los colores.",
        "text_en": "{name} looked at {pet_name}. {pet_name} looked at {name}. Without a word, they both ducked under the fence. What they found on the other side left them speechless: a secret garden with enormous flowers of every color.",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: A {gender_word} ({age_display}) with {hair_desc}, {eye_desc} eyes{glasses_desc} standing in amazement in a magical secret garden, wearing {adventure_outfit}, mouth open, head tilted back looking at giant flowers towering above, arms slightly outstretched in wonder. PET: {pet_desc}, sniffing a giant purple flower, sneezing with a cloud of colorful pollen around its face, surprised expression. ACTION: Child and pet discover a magical secret garden filled with oversized colorful flowers, the child is in awe while the pet sniffs a giant flower. SETTING: Secret garden WIDE VIEW, enormous flowers of every color towering overhead, magical light filtering through petals, stone path winding through, butterflies and sparkles. ATMOSPHERE: Magical wonderland, kaleidoscope of colors, warm enchanted light, fairy tale atmosphere. STRICT: Only ONE child, ONE pet, magical oversized garden, fantasy discovery scene. {style}",
        "text_position": "split"
    },
    {
        "id": 9,
        "text_es": "{pet_name} metió la nariz en una flor morada y estornudó, lanzando una nube de polen brillante. {name} recogió un pétalo que cabía en las dos manos. Debajo del árbol más grande del jardín, las raíces formaban un escondite. Y ahí asomaba un viejo cofre.",
        "text_en": "{pet_name} stuck their nose in a purple flower and sneezed, launching a cloud of shimmering pollen. {name} picked up a petal that fit in both hands. Under the biggest tree in the garden, the roots formed a hideaway. And there, peeking out, was an old chest.",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: A {gender_word} ({age_display}) with {hair_desc}, {eye_desc} eyes{glasses_desc} kneeling beside a large tree, wearing {adventure_outfit}, hands digging in dirt around an old wooden chest with golden ornaments, excited discovery expression. PET: {pet_desc}, digging enthusiastically beside the child with front paws, dirt flying behind, helping to unearth the chest, determined expression. ACTION: Child and pet dig together to unearth an old treasure chest found among the roots of a giant tree in the secret garden. SETTING: Base of an enormous ancient tree WIDE VIEW, gnarled roots forming a natural hideaway, an old wooden chest half-buried in soil with golden metal corners visible, magical garden around. ATMOSPHERE: Treasure discovery excitement, warm dappled light through canopy, magical anticipation. STRICT: Only ONE child digging, ONE pet helping dig, one treasure chest, discovery scene. {style}",
        "text_position": "split"
    },
    {
        "id": 10,
        "text_es": "Con manos temblorosas de emoción, {name} abrió la tapa oxidada. Dentro había un mapa viejo, dibujado a mano con tinta azul y roja. Una gran X marcaba un punto al final de un sendero. \"¡Es un mapa del tesoro, {pet_name}!\", exclamó {name} con los ojos brillantes.",
        "text_en": "With hands trembling with excitement, {name} opened the rusty lid. Inside was an old map, hand-drawn with blue and red ink. A big X marked a spot at the end of a trail. \"It's a treasure map, {pet_name}!\" exclaimed {name} with shining eyes.",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: A {gender_word} ({age_display}) with {hair_desc}, {eye_desc} eyes{glasses_desc} holding open an old hand-drawn treasure map with both hands, wearing {adventure_outfit}, eyes wide and sparkling with excitement, the open wooden chest on the ground beside them. PET: {pet_desc}, standing on hind legs with front paws on the child's arm, peering at the map curiously, head tilted, sniffing the old paper. ACTION: Child holds up a treasure map found in the chest while the pet leans in to look at it, both fascinated by the discovery. SETTING: Garden clearing WIDE VIEW, open treasure chest on the ground, the old map clearly visible with drawn paths and a big red X, giant tree behind, magical garden atmosphere. ATMOSPHERE: Treasure hunt excitement, warm golden light on the map, sparkle of adventure. STRICT: Only ONE child holding map, ONE pet looking at it, treasure map discovery scene. {style}",
        "text_position": "split"
    },
    {
        "id": 11,
        "text_es": "{pet_name} olió el mapa y se puso a dar vueltas, como diciendo: \"¿A qué esperamos?\" El mapa los llevó por un sendero estrecho entre los árboles, donde las ramas formaban un túnel verde sobre sus cabezas. La mariposa dorada volaba adelante, mostrándoles el camino.",
        "text_en": "{pet_name} sniffed the map and started circling excitedly, as if saying: \"What are we waiting for?\" The map led them down a narrow path between the trees, where branches formed a green tunnel overhead. The golden butterfly flew ahead, showing them the way.",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: A {gender_word} ({age_display}) with {hair_desc}, {eye_desc} eyes{glasses_desc} walking along a narrow forest path holding a map in one hand, wearing {adventure_outfit}, looking ahead with determination. PET: {pet_desc}, walking close beside the child, alert and protective, ears perked forward, stepping carefully on the path. ACTION: Child and pet walk together through a natural tunnel of tree branches following a treasure map, a golden butterfly glowing ahead of them. SETTING: Forest tunnel path WIDE VIEW, arching tree branches creating a green canopy tunnel, dappled golden light filtering through leaves, narrow dirt path, golden butterfly glowing ahead. ATMOSPHERE: Enchanted forest adventure, green and gold light, mysterious but inviting path ahead. STRICT: Only ONE child walking, ONE pet beside them, forest tunnel path scene. {style}",
        "text_position": "split"
    },
    {
        "id": 12,
        "text_es": "{name} iba adelante con el mapa y {pet_name} caminaba pegado a sus piernas. El sendero terminó frente a un pequeño puente de madera que cruzaba un arroyo de agua cristalina. El puente crujía con el viento. {pet_name} puso una pata y retrocedió asustado.",
        "text_en": "{name} walked ahead with the map and {pet_name} stayed close to their legs. The trail ended at a small wooden bridge crossing a crystal-clear stream. The bridge creaked in the wind. {pet_name} put one paw on it and backed away, scared.",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: A {gender_word} ({age_display}) with {hair_desc}, {eye_desc} eyes{glasses_desc} standing at the start of a small wooden bridge over a stream, wearing {adventure_outfit}, looking back at the scared pet with a reassuring gentle expression, one hand extended toward the pet. PET: {pet_desc}, sitting at the edge of the bridge, one paw pulled back, ears flat, looking at the bridge nervously, body low and hesitant. ACTION: The child tries to encourage the scared pet to cross a creaky wooden bridge over a stream. SETTING: Small wooden bridge WIDE VIEW, clear stream flowing underneath with visible stones, old wooden planks, wildflowers and ferns on the banks, forest around, soft light. ATMOSPHERE: Gentle tension, supportive friendship moment, soft warm forest light. STRICT: Only ONE child on bridge edge, ONE scared pet on the bank, bridge crossing scene. {style}",
        "text_position": "split"
    },
    {
        "id": 13,
        "text_es": "{name} acarició la cabeza de {pet_name} con suavidad. \"No tengas miedo, yo estoy contigo\", le susurró. Entonces tomó a {pet_name} en brazos con cuidado y empezó a cruzar el puente paso a paso. {pet_name} se acurrucó contra su pecho, cerrando los ojos con confianza.",
        "text_en": "{name} gently stroked {pet_name}'s head. \"Don't be afraid, I'm with you,\" they whispered. Then {name} carefully picked up {pet_name} and started crossing the bridge step by step. {pet_name} nestled against their chest, closing their eyes with trust.",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: A {gender_word} ({age_display}) with {hair_desc}, {eye_desc} eyes{glasses_desc} carefully walking across a wooden bridge over a stream, wearing {adventure_outfit}, carrying the pet in their arms, protective loving expression, stepping carefully on the wooden planks. PET: {pet_desc}, being carried in the child's arms, nestled against the child's chest with eyes closed, trusting and calm, paws tucked in. ACTION: Child carries the pet across the bridge, the pet trusts the child completely with eyes closed, a beautiful moment of friendship and courage. SETTING: Middle of wooden bridge WIDE VIEW, crystal stream below with sunlight sparkling on water, green banks on both sides, forest canopy above, golden light rays. ATMOSPHERE: Trust and courage, warm protective love, golden light streaming through trees, emotional bonding moment. STRICT: Only ONE child carrying ONE pet, crossing bridge together, tender brave scene. {style}",
        "text_position": "split"
    },
    {
        "id": 14,
        "text_es": "Cuando llegaron al otro lado, {pet_name} lamió la cara de {name} como diciendo \"gracias\". La X del mapa señalaba una pequeña cueva en la ladera de una colina. La entrada estaba decorada con piedras que brillaban como diamantes.",
        "text_en": "When they reached the other side, {pet_name} licked {name}'s face as if saying \"thank you.\" The X on the map pointed to a small cave in a hillside. The entrance was decorated with stones that sparkled like diamonds.",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: A {gender_word} ({age_display}) with {hair_desc}, {eye_desc} eyes{glasses_desc} standing at the entrance of a small cave in a hillside, wearing {adventure_outfit}, holding the map and comparing it to the location, excited amazed expression, pointing at the cave entrance. PET: {pet_desc}, entering the cave first with brave posture, looking back at the child encouragingly, tail held high. ACTION: Child and pet arrive at a sparkling cave entrance that matches the X on the treasure map, the pet bravely enters first. SETTING: Small hillside cave entrance WIDE VIEW, rocks around the entrance studded with crystals that catch and reflect sunlight like diamonds, green hill, wildflowers, forest behind. ATMOSPHERE: Treasure destination reached, sparkling crystal light, magical excitement, golden afternoon light. STRICT: Only ONE child at cave entrance, ONE pet entering cave, crystal cave discovery scene. {style}",
        "text_position": "split"
    },
    {
        "id": 15,
        "text_es": "{pet_name} entró primero, valiente como nunca. Dentro, las paredes centelleaban con cristales de todos los colores. En el fondo, grabado en una piedra lisa y brillante, había un mensaje: \"Para el explorador más valiente y su mejor compañero.\"",
        "text_en": "{pet_name} went in first, braver than ever. Inside, the walls sparkled with crystals of every color. At the back, carved into a smooth shining stone, was a message: \"For the bravest explorer and their best companion.\"",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: A {gender_word} ({age_display}) with {hair_desc}, {eye_desc} eyes{glasses_desc} inside a crystal cave, wearing {adventure_outfit}, kneeling in front of a smooth glowing stone, reading it with wide emotional eyes, hand touching the stone gently. PET: {pet_desc}, sitting beside the child inside the cave, head tilted as if listening to the words being read, attentive loving expression. ACTION: Child reads an inscription on a glowing stone inside the crystal cave while the pet sits attentively beside them, both moved by the message. SETTING: Inside crystal cave WIDE VIEW, walls covered in multicolored crystals reflecting light everywhere, smooth stone at the back, soft magical glow illuminating the cave. ATMOSPHERE: Magical revelation, rainbow crystal light, emotional discovery, warm awe. STRICT: Only ONE child reading stone, ONE pet beside them, inside crystal cave scene. {style}",
        "text_position": "split"
    },
    {
        "id": 16,
        "text_es": "{name} sonrió y abrazó a {pet_name}. \"Eso somos nosotros\", dijo con orgullo. Detrás de la piedra, escondida en un hueco, había una caja dorada. Dentro encontró un medallón con la forma de una estrella y una bolsita de galletas especiales para {pet_name}.",
        "text_en": "{name} smiled and hugged {pet_name}. \"That's us,\" they said proudly. Behind the stone, hidden in a hollow, was a golden box. Inside was a star-shaped medallion and a little bag of special treats for {pet_name}.",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: A {gender_word} ({age_display}) with {hair_desc}, {eye_desc} eyes{glasses_desc} sitting in the crystal cave, wearing {adventure_outfit}, holding up a shining star-shaped medallion on a chain, beaming with pride and joy. PET: {pet_desc}, happily eating treats from a small bag on the cave floor, tail wagging fast, content and happy expression. ACTION: Child proudly holds a star medallion prize while the pet enjoys special treats, both celebrating their treasure find inside the crystal cave. SETTING: Crystal cave interior WIDE VIEW, golden box open on the floor, star medallion glowing with warm light, treat bag beside the pet, colorful crystals reflecting the golden glow. ATMOSPHERE: Triumph and celebration, warm golden glow from medallion, joy and pride, magical reward. STRICT: Only ONE child with medallion, ONE pet eating treats, treasure reward celebration scene. {style}",
        "text_position": "split"
    },
    {
        "id": 17,
        "text_es": "{name} se puso el medallón al cuello. En el medallón estaban grabadas dos palabras: \"Mejores Amigos\". El sol empezaba a esconderse cuando {name} y {pet_name} tomaron el camino de vuelta a casa. El cielo se pintó de naranja, rosa y morado.",
        "text_en": "{name} put the medallion around their neck. On the medallion were carved two words: \"Best Friends.\" The sun was starting to set when {name} and {pet_name} took the path back home. The sky turned orange, pink, and purple.",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: A {gender_word} ({age_display}) with {hair_desc}, {eye_desc} eyes{glasses_desc} walking along a park path at sunset, wearing {adventure_outfit} now dirty with mud and leaves, slightly tired but with a huge satisfied smile, a star medallion glowing gently on their chest. PET: {pet_desc}, walking beside the child at a relaxed pace, happy and tired, tongue out slightly, matching the child's calm pace. ACTION: Child and pet walk home together at sunset after their big adventure, both tired but deeply happy, the medallion glowing on the child's chest. SETTING: Park path at golden hour WIDE VIEW, dramatic orange pink and purple sunset sky, long shadows stretching across the path, trees silhouetted, golden butterfly visible flying away in the distance. ATMOSPHERE: Peaceful homecoming, warm golden sunset, deep satisfaction, beautiful ending light. STRICT: Only ONE child walking, ONE pet beside them, sunset walk home scene. {style}",
        "text_position": "split"
    },
    {
        "id": 18,
        "text_es": "Cuando abrieron la puerta de casa, mamá se quedó mirándolos con los ojos muy abiertos. {name} estaba cubierto de barro, hojas y polvo dorado. {pet_name} tenía ramitas en el pelo y las patas llenas de tierra.",
        "text_en": "When they opened the front door, mom stared at them with wide eyes. {name} was covered in mud, leaves, and golden dust. {pet_name} had twigs in their fur and paws full of dirt.",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: A {gender_word} ({age_display}) with {hair_desc}, {eye_desc} eyes{glasses_desc} standing in a doorway with an innocent guilty grin, wearing {adventure_outfit} completely covered in dried mud and leaves, golden dust on clothes, hands behind their back, mischievous expression. PET: {pet_desc}, sitting beside the child in the doorway, also covered in dirt with twigs in fur, looking at the camera with big innocent eyes, tail tucked slightly, guilty expression. ACTION: Child and pet stand in the doorway after their adventure, both filthy and disheveled, putting on their best innocent faces. SETTING: Home front doorway WIDE VIEW, warm interior light behind them, evening outside, muddy footprints on the doorstep, contrast between clean house interior and dirty adventurers. ATMOSPHERE: Comedic guilty moment, warm interior light vs evening exterior, mischievous innocence, heartwarming humor. STRICT: Only ONE dirty child, ONE dirty pet, in doorway, only the child and pet visible, comedic arrival scene. {style}",
        "text_position": "split"
    },
    {
        "id": 19,
        "text_es": "\"¡Pero qué les pasó!\", exclamó mamá. \"Solo fuimos a dar un paseo al parque\", dijo {name} con una sonrisa pícara. Después de un buen baño, {name} se acurrucó en el sofá con {pet_name} a su lado. \"Mañana buscaremos otra aventura\", susurró {name} con los ojos cerrándose de sueño. Y así, los dos mejores amigos se quedaron dormidos, soñando con su próxima gran aventura.",
        "text_en": "\"What happened to you two!\" exclaimed mom. \"We just went for a walk in the park,\" said {name} with a mischievous smile. After a good bath, {name} curled up on the couch with {pet_name} beside them. \"Tomorrow we'll find another adventure,\" whispered {name} as their eyes closed with sleep. And so, the two best friends fell asleep, dreaming of their next great adventure.",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: A clean {gender_word} ({age_display}) with {hair_desc}, {eye_desc} eyes{glasses_desc} wearing {clean_pajama_desc}, curled up on a cozy sofa, eyes closing sleepily, one hand resting on the pet, a star medallion visible on the coffee table, peaceful smile. PET: {pet_desc}, clean and fluffy after a bath, curled up right next to the child on the sofa, head resting on the child's lap, eyes already closed, deeply content. ACTION: Clean child and pet fall asleep together on the couch after their adventure, both peaceful and content, dreaming of tomorrow. SETTING: Cozy living room evening WIDE VIEW, soft sofa with blankets, warm lamp light, star medallion on coffee table glowing softly, window showing stars outside, family photos on wall. ATMOSPHERE: Perfect peaceful ending, warm amber lamp light, deep contentment, love and friendship, dreamlike serenity. STRICT: Only ONE child on sofa, ONE pet beside them, cozy evening sleep scene. {style}",
        "text_position": "split"
    }
]

CLOSING_SCENE = {
    "id": 20,
    "prompt": "Disney Pixar 3D style illustration. HUMAN: A {gender_word} ({age_display}) with {hair_desc}, {eye_desc} eyes{glasses_desc} sleeping deeply in a cozy bed under a star-patterned blanket, wearing {clean_pajama_desc}, peaceful smile, one arm hanging off the bed. PET: {pet_desc}, sleeping on a pet bed right beside the child's bed, one paw stretched out touching the hanging hand of the child, protective even in sleep, peaceful expression. On the nightstand, a star medallion glows softly beside a framed photo of the child and pet together. ACTION: Child sleeps in bed with hand touching the pet's paw below, connected even in sleep, the star medallion from their adventure glowing on the nightstand. SETTING: Cozy bedroom at night WIDE VIEW, warm nightlight glow, stars visible through window, adventure drawings pinned to wall, star medallion on nightstand, peaceful darkness. ATMOSPHERE: Perfect peaceful ending, warm nightlight glow, eternal friendship, serene protection. STRICT: Only ONE child in bed, ONE pet on floor beside bed, nighttime bedroom scene. {style}",
    "text_position": "none"
}

FRONT_COVER = {
    "prompt": "Disney Pixar 3D style illustration. HUMAN: A {gender_word} ({age_display}) with {hair_desc}, {eye_desc} eyes{glasses_desc} wearing {adventure_outfit}, excited expression, one arm raised pointing forward, the other hand resting on the pet's back, standing on a park path. PET: {pet_desc}, standing beside the child looking in the same direction, alert and excited, tail wagging, ready for adventure. ACTION: Child and pet stand together at the start of a park path, looking ahead toward an adventure, golden butterfly visible in the distance leaving a sparkle trail. SETTING: Beautiful park entrance WIDE VIEW, green trees forming an archway, winding path leading into a magical forest, golden light ahead, wildflowers, a golden butterfly glowing in the distance. ATMOSPHERE: Beginning of an adventure, warm morning light, excitement and wonder, magical invitation. STRICT: Only ONE child, ONE pet, standing together ready for adventure, centered composition for book cover. Pure illustration only, zero text or lettering. {style}"
}

BACK_COVER = {
    "prompt": "Disney Pixar 3D style illustration. SETTING: A beautiful park scene at golden hour WIDE VIEW, an old wooden bench under a giant oak tree, a pair of small muddy sneakers and a star medallion left on the bench, a hand-drawn treasure map partly visible sticking out of a small backpack, wildflowers growing around the bench legs, a golden butterfly resting on the backpack, warm sunset light streaming through the tree canopy creating long golden shadows, a winding path leading into the forest in the background. ATMOSPHERE: Warm nostalgic, peaceful sunset, adventure resting, promise of tomorrow, golden warm tones. STRICT: only scenery and adventure props, objects only. Pure illustration only, zero text or lettering. {style}"
}


def build_human_preview_prompt(human_desc: str) -> str:
    return f"Disney Pixar 3D style illustration. FULL BODY portrait of {human_desc}, wearing adventure clothes (t-shirt, shorts, sneakers, small backpack), standing naturally with one hand on hip, adventurous confident smile, centered in frame, occupying 60% of frame height. NEUTRAL SOLID GRADIENT BACKGROUND (soft cream to warm beige), plain studio background. Natural friendly expression, relaxed standing pose. Clean professional animation art, clean illustration only. STRICT: Character fully clothed."


def build_human_preview_prompt_with_photo(gender_word: str, age_display: str, eye_desc: str = "", hair_desc: str = "", glasses: str = "") -> str:
    glasses_part = ", wearing glasses" if glasses == "glasses" else ", wearing sunglasses" if glasses == "sunglasses" else ""
    outfit = ADVENTURE_OUTFIT_BOY if gender_word == "boy" else ADVENTURE_OUTFIT_GIRL
    return f"Disney Pixar 3D style. 3D animated character of the person from @image1 ({age_display} {gender_word}{glasses_part}), {hair_desc}, {eye_desc}, wearing {outfit}. FULL BODY portrait, centered, adventurous confident expression, occupying 60% of frame height. NEUTRAL SOLID GRADIENT BACKGROUND (soft cream to warm beige). Clean animation art, clean illustration only."


def build_pet_preview_prompt(pet_desc: str) -> str:
    return f"Disney Pixar 3D style illustration. FULL BODY portrait of {pet_desc}, sitting or standing naturally, friendly expression, centered in frame, occupying 50% of frame height. NEUTRAL SOLID GRADIENT BACKGROUND (soft cream to warm beige), plain studio background. Warm lighting, expressive eyes. Clean professional animation art, clean illustration only."


def build_pet_preview_prompt_with_photo(pet_desc: str = "", pet_species: str = "dog") -> str:
    animal = "cat" if pet_species == "cat" else "dog"
    return f"Disney Pixar 3D style. 3D animated character of the {animal} from @image1. FULL BODY portrait, sitting or standing naturally, friendly expression, centered, occupying 50% of frame height. NEUTRAL SOLID GRADIENT BACKGROUND (soft cream to warm beige). Warm lighting. Clean animation art, clean illustration only."


def build_scene_prompt(scene: dict, human_desc: str, pet_name: str, pet_desc: str, age_display: str = "3-8 years old", eye_desc: str = "", gender_word: str = "child", glasses: str = "", hair_desc: str = "", **kwargs) -> str:
    adventure_outfit = ADVENTURE_OUTFIT_BOY if gender_word == "boy" else ADVENTURE_OUTFIT_GIRL
    prompt = scene.get('prompt', '')
    prompt = prompt.replace('{human_desc}', human_desc)
    prompt = prompt.replace('{pet_name}', pet_name)
    prompt = prompt.replace('{pet_desc}', pet_desc)
    prompt = prompt.replace('{age_display}', age_display)
    prompt = prompt.replace('{hair_desc}', hair_desc)
    eye_color_only = eye_desc.replace(' eyes', '').strip() if eye_desc else ''
    prompt = prompt.replace('{eye_desc}', eye_color_only)
    prompt = prompt.replace('{gender_word}', gender_word)
    prompt = prompt.replace('{adventure_outfit}', adventure_outfit)
    prompt = prompt.replace('{pajama_desc}', PAJAMA_DESC)
    prompt = prompt.replace('{clean_pajama_desc}', CLEAN_PAJAMA_DESC)
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


def get_all_scene_prompts(human_desc: str, pet_name: str, pet_desc: str, age_display: str = "3-8 years old", eye_desc: str = "") -> list:
    prompts = []
    for scene in FURRY_LOVE_ADVENTURE_SCENES:
        prompts.append(build_scene_prompt(scene, human_desc, pet_name, pet_desc, age_display, eye_desc))
    prompts.append(build_scene_prompt(CLOSING_SCENE, human_desc, pet_name, pet_desc, age_display, eye_desc))
    return prompts


def get_all_story_texts(child_name: str, pet_name: str, language: str = 'es') -> list:
    texts = []
    for scene in FURRY_LOVE_ADVENTURE_SCENES:
        texts.append({
            'id': scene['id'],
            'text': build_story_text(scene, child_name, pet_name, language),
            'text_position': scene.get('text_position', 'split')
        })
    return texts


def get_cover_prompts(human_desc: str, pet_name: str, pet_desc: str, age_display: str = "3-8 years old", eye_desc: str = "", glasses: str = "") -> dict:
    return {
        'front': build_scene_prompt(FRONT_COVER, human_desc, pet_name, pet_desc, age_display, eye_desc, glasses=glasses),
        'back': build_scene_prompt(BACK_COVER, human_desc, pet_name, pet_desc, age_display, eye_desc, glasses=glasses)
    }
