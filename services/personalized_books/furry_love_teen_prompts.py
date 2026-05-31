# Tú y tu Amor Peludo - Teen Story Prompts
# 19 scenes + closing + covers
# Story: "Mi compañero fiel" - A teen rediscovers the bond with their pet
# Ages 10-17 - Emotional reconnection, humor, heartfelt moments
#
# FLUX 2 Dev with TWO reference images:
#   1. Human preview: detailed character description → reference image 1
#   2. Pet preview: detailed pet description → reference image 2
#   3. Scenes: FLUX 2 Dev takes BOTH references → prompts bind roles explicitly
#
# Prompt schema (updated Feb-May 2026):
#   STRICT (at top) → HUMAN (who + WHERE) → PET (who + WHERE) →
#   TOGETHER (one spatial sentence) → SETTING → ATMOSPHERE → {style}
#
# Rules:
#   - guidance_scale=3.5, num_inference_steps=28, aspect_ratio=3:4
#   - Keep prompts concise - FLUX 2 Dev loses focus with >300 words
#   - Style: Disney Pixar 3D everywhere, NO watercolor
#   - Human is a teenager (10-17 years old)
#   - Pet is a dog or cat (customized breed, color, pattern)
#   - TWO reference images per scene (human + pet)
#   - Text uses {name} for human and {pet_name} for pet
#   - STRICT always at the TOP of each prompt (FLUX weights early tokens more)
#   - NO ACTION section (was causing triple-description → duplicate characters)
#   - Each character described ONCE with a clear spatial anchor in the frame

STYLE_BASE = "Disney Pixar 3D style, soft warm lighting, emotional cinematic atmosphere, WIDE SHOT full body from head to feet, characters occupy 40% of frame, modern home and neighborhood environment visible, clean illustration only. STRICT: The teenager has full adolescent proportions: tall build, long limbs, defined jaw and facial structure, slender young adult frame. Depicted as an actual teenager, not a young child. Casual modern clothes, fully clothed always."

FURRY_LOVE_TEEN_SCENES = [
    {
        "id": 1,
        "text_es": "Hubo un tiempo en que {name} y {pet_name} eran inseparables. Juntos corrían por el parque, se acurrucaban en el sofá y compartían cada momento del día. {pet_name} era el mejor amigo de {name}... pero eso fue hace tiempo.",
        "text_en": "There was a time when {name} and {pet_name} were inseparable. They ran together in the park, cuddled on the couch, and shared every moment of the day. {pet_name} was {name}'s best friend... but that was a while ago.",
        "prompt": "Disney Pixar 3D style illustration. STRICT: exactly ONE small child at LEFT of frame, exactly ONE pet at RIGHT of frame, no extra characters, memory/flashback scene. HUMAN: A small {gender_word} child around 6 years old with {eye_desc} eyes, short and small, laughing joyfully, running at LEFT side of frame, arms open wide, pure happiness on face. PET: {pet_desc}, young and energetic, running alongside the child at RIGHT side of frame, ears back from running speed, joyful bounding stride. TOGETHER: the child and pet run side by side across the open park, both carefree and inseparable. SETTING: Beautiful sunny park WIDE VIEW, green grass, warm golden afternoon light, soft dreamy hazy edges suggesting this is a childhood memory. ATMOSPHERE: Nostalgic warmth, golden memory glow, bittersweet happiness from the past. {style}",
        "text_position": "split"
    },
    {
        "id": 2,
        "text_es": "Pero {name} ya no era un niño pequeño. Ahora tenía su celular, sus videojuegos y sus amigos del colegio. {pet_name} se acercaba moviendo la cola, pero {name} apenas levantaba la vista de la pantalla. \"Ahora no, {pet_name}\", decía sin mirar.",
        "text_en": "But {name} wasn't a little kid anymore. Now they had their phone, video games, and school friends. {pet_name} would come over wagging their tail, but {name} barely looked up from the screen. \"Not now, {pet_name},\" they'd say without looking.",
        "prompt": "Disney Pixar 3D style illustration. STRICT: exactly ONE teenager at LEFT of frame, exactly ONE pet at RIGHT of frame, no extra characters. HUMAN: A {gender_word} teenager ({age_display}) with {eye_desc} eyes{glasses_desc}, slouched on a beanbag chair at LEFT side of frame, phone glowing on face, headphones around neck, one hand loosely waving the pet away without looking up. PET: {pet_desc}, sitting on the floor at RIGHT side of frame, looking up at the teenager with large hopeful eyes, head tilted, tail wagging gently, patient and hopeful. TOGETHER: the pet sits just within arm's reach of the teen, who stares at the phone ignoring them. SETTING: Modern teenager bedroom WIDE VIEW, gaming posters, desk with computer, warm afternoon light through window. ATMOSPHERE: Gentle sadness, contrast between cold screen glow and warm loyal pet presence, quiet longing. {style}",
        "text_position": "split"
    },
    {
        "id": 3,
        "text_es": "{pet_name} no se rendía fácilmente. Un día, mientras {name} escribía un mensaje importante, {pet_name} se acercó sigilosamente y... ¡ZAS! Le robó el celular de las manos con la boca y salió corriendo a toda velocidad por el pasillo.",
        "text_en": "{pet_name} didn't give up easily. One day, while {name} was typing an important message, {pet_name} crept up silently and... SNAP! Snatched the phone right out of their hands and took off running down the hallway at full speed.",
        "prompt": "Disney Pixar 3D style illustration. STRICT: exactly ONE teenager at BACK of hallway, exactly ONE pet at FRONT of hallway running away, no extra characters, no floating hands. HUMAN: A {gender_word} teenager ({age_display}) with {eye_desc} eyes{glasses_desc}, standing upright at the FAR END of the hallway, mouth open in shock, one arm extended forward in disbelief, feet planted on the ground. PET: {pet_desc}, sprinting at full speed toward the FOREGROUND of the hallway, a smartphone held carefully in its mouth, mischievous triumphant expression, ears back from speed, tail high. TOGETHER: the pet races away from the teenager down the long hallway, a clear distance of several meters between them. SETTING: Home hallway WIDE VIEW, doors along the sides, warm indoor lighting, morning atmosphere. ATMOSPHERE: Hilarious comedic chaos, mischievous energy, bright dynamic lighting. {style}",
        "text_position": "split"
    },
    {
        "id": 4,
        "text_es": "\"¡{pet_name}, devuélveme el celular!\" gritó {name} persiguiéndolo por toda la casa. {pet_name} esquivaba muebles como un profesional, saltaba sobre el sofá y se metía debajo de la mesa. Cuando por fin lo atrapó, el celular estaba lleno de babas. {name} no pudo evitar reírse.",
        "text_en": "\"Give me back my phone, {pet_name}!\" yelled {name}, chasing them through the whole house. {pet_name} dodged furniture like a pro, jumped over the couch, and dove under the table. When {name} finally caught them, the phone was covered in drool. {name} couldn't help but laugh.",
        "prompt": "Disney Pixar 3D style illustration. STRICT: exactly ONE teenager kneeling at LEFT of frame, exactly ONE pet under the table at RIGHT of frame, no extra characters. HUMAN: A {gender_word} teenager ({age_display}) with {eye_desc} eyes{glasses_desc}, kneeling on the floor at LEFT side of frame reaching one arm under the dining table, messy hair, laughing despite themselves, amused expression. PET: {pet_desc}, sitting under the table at RIGHT side of frame, drool-covered phone held between its front paws, playful guilty expression, tail wagging, big happy eyes looking at the teenager. TOGETHER: teen reaches toward the pet who sits smugly under the table with the drool-covered prize. SETTING: Dining room WIDE VIEW, chairs pushed aside, table legs framing the scene, warm home lighting. ATMOSPHERE: Comedic resolution, warm laughter, genuine fun moment. {style}",
        "text_position": "split"
    },
    {
        "id": 5,
        "text_es": "Al día siguiente, {name} estaba haciendo tarea en la computadora. {pet_name} apareció de la nada y se subió directamente encima del teclado. La pantalla se llenó de letras sin sentido: \"asdfjklñ;asdfgh\". {pet_name} se quedó ahí echado, mirando a {name} como si fuera el lugar más cómodo del mundo.",
        "text_en": "The next day, {name} was doing homework on the computer. {pet_name} appeared out of nowhere and climbed right onto the keyboard. The screen filled with gibberish: \"asdfjklñ;asdfgh\". {pet_name} just lay there, looking at {name} as if it were the most comfortable spot in the world.",
        "prompt": "Disney Pixar 3D style illustration. STRICT: exactly ONE teenager seated at LEFT of frame, exactly ONE pet lying across the keyboard at CENTER of frame, no other animals, pure illustration only, zero text. HUMAN: A {gender_word} teenager ({age_display}) with {eye_desc} eyes{glasses_desc}, seated at the LEFT side of the desk, both hands raised in a helpless gesture, exasperated but amused smile, leaning back slightly from the keyboard. PET: {pet_desc}, lying sprawled across the laptop keyboard at CENTER of the desk, completely relaxed, paws draped forward, content satisfied face looking up at the teen, tail hanging off one side. TOGETHER: the pet occupies the entire keyboard directly in front of the teenager, blocking all work. SETTING: Teen study desk WIDE VIEW, laptop with glowing blank screen, school books and notebooks, desk lamp, cozy evening atmosphere. ATMOSPHERE: Comedic frustration turning to amusement, warm desk lamp glow. {style}",
        "text_position": "split"
    },
    {
        "id": 6,
        "text_es": "{name} suspiró y movió a {pet_name} con cuidado. \"Eres imposible\", le dijo, pero le dio una caricia rápida en la cabeza antes de volver a la tarea. {pet_name} meneó la cola. Esa caricia era un pequeño triunfo.",
        "text_en": "{name} sighed and gently moved {pet_name} aside. \"You're impossible,\" they said, but gave a quick pat on the head before going back to homework. {pet_name} wagged their tail. That little pat was a small victory.",
        "prompt": "Disney Pixar 3D style illustration. STRICT: exactly ONE teenager at the desk, exactly ONE pet seated beside the chair, no extra characters. HUMAN: A {gender_word} teenager ({age_display}) with {eye_desc} eyes{glasses_desc}, sitting at the desk facing the laptop, one hand on the keyboard typing, the other arm reaching down beside the chair with a gentle smile. PET: {pet_desc}, sitting on the floor directly beside the desk chair, eyes closed in bliss receiving a head pat, leaning into the touch, tail wagging gently, peaceful expression. TOGETHER: teen's hand rests on the pet's head just beside the chair, an absent-minded but warm gesture. SETTING: Study desk WIDE VIEW, laptop with homework on screen, warm desk lamp light, bedroom in background, evening. ATMOSPHERE: Small tender moment, quiet warmth breaking through distraction, soft lamplight. {style}",
        "text_position": "split"
    },
    {
        "id": 7,
        "text_es": "Pero la Operación Atención no había terminado. A la mañana siguiente, {name} buscaba sus calcetines por toda la habitación. \"¡Juro que los dejé aquí!\" Cuando miró debajo de la cama, encontró un tesoro escondido: tres pares de calcetines, un guante, y la gorra favorita de {name}. Todo en la cama de {pet_name}.",
        "text_en": "But Operation Attention wasn't over. The next morning, {name} searched the whole room for their socks. \"I swear I left them here!\" When they looked under the bed, they found a hidden treasure: three pairs of socks, a glove, and {name}'s favorite cap. All in {pet_name}'s bed.",
        "prompt": "Disney Pixar 3D style illustration. STRICT: exactly ONE teenager on floor at LEFT of frame, exactly ONE pet in its own bed at RIGHT of frame, no duplicate animals, no extra characters. HUMAN: A {gender_word} teenager ({age_display}) with {eye_desc} eyes{glasses_desc}, crouching on the bedroom floor at LEFT of frame, shining a flashlight toward the RIGHT side of the room, eyes wide in shocked amusement, mouth open in disbelief at the discovery. PET: {pet_desc}, lying in its pet bed at RIGHT of frame in the same room, surrounded by a collection of colorful stolen socks, a glove, and a cap piled around it, looking up at the teenager with the most innocent proud expression. TOGETHER: the flashlight beam connects the teen at LEFT to the pet's discovered treasure stash at RIGHT. SETTING: Teenager bedroom floor level WIDE VIEW, morning light from window, scattered personal items. ATMOSPHERE: Hilarious discovery, warm morning light, pure mischief revealed. {style}",
        "text_position": "split"
    },
    {
        "id": 8,
        "text_es": "\"¡{pet_name}!\" exclamó {name}, pero {pet_name} lo miraba con cara de ángel. Esos ojos grandes e inocentes eran su mejor arma. {name} negó con la cabeza, pero una sonrisa se le escapó. Recogió sus cosas y le rascó las orejas a {pet_name}. \"Eres un pequeño ladrón.\"",
        "text_en": "\"Oh, {pet_name}!\" exclaimed {name}, but {pet_name} looked at them with an angel face. Those big innocent eyes were their best weapon. {name} shook their head, but a smile escaped. They gathered their things and scratched {pet_name}'s ears. \"You're a little thief.\"",
        "prompt": "Disney Pixar 3D style illustration. STRICT: exactly ONE teenager kneeling at LEFT of frame, exactly ONE pet sitting at RIGHT of frame, no extra characters. HUMAN: A {gender_word} teenager ({age_display}) with {eye_desc} eyes{glasses_desc}, kneeling on the bedroom floor at LEFT of frame, holding a bunch of recovered socks and a cap in one arm, the other hand scratching the pet's ears, shaking head with a helpless warm grin. PET: {pet_desc}, sitting upright at RIGHT of frame beside the teenager, gazing up with the most angelic innocent expression, huge sparkling eyes, head tilted slightly, ears perked into the scratch, tail gently wagging. TOGETHER: teen scratches the pet's ears while the pet holds its best innocent face. SETTING: Bedroom floor WIDE VIEW, scattered socks around them, morning sunlight, cozy atmosphere. ATMOSPHERE: Loving humor, fake scolding with real affection, warm golden morning light. {style}",
        "text_position": "split"
    },
    {
        "id": 9,
        "text_es": "Pasaron los días y {name} volvió a su rutina: colegio, celular, videojuegos, repetir. {pet_name} empezó a pasar más tiempo solo, echado junto a la puerta del cuarto de {name}, esperando. A veces se quedaba dormido ahí, con la nariz pegada a la rendija de la puerta.",
        "text_en": "Days passed and {name} went back to their routine: school, phone, video games, repeat. {pet_name} started spending more time alone, lying by {name}'s bedroom door, waiting. Sometimes they fell asleep there, nose pressed against the gap under the door.",
        "prompt": "Disney Pixar 3D style illustration. STRICT: exactly ONE pet lying alone in the hallway, teenager barely visible as a silhouette through a door crack, no extra characters. PET: {pet_desc}, lying alone on the hallway floor right against a closed bedroom door, head resting on front paws, nose pressed to the gap under the door, sad lonely eyes, droopy patient posture. HUMAN: A {gender_word} teenager ({age_display}) with {eye_desc} eyes, seen only as a dim silhouette visible through the door crack, sitting at a desk inside with headphones on, absorbed in a screen, unaware. TOGETHER: the pet waits in the dim hallway while warm light leaks from under the closed door separating them. SETTING: Home hallway WIDE VIEW, closed bedroom door, warm light leaking underneath, family photos on walls, evening atmosphere. ATMOSPHERE: Quiet loneliness, loyal devotion, contrast between warm screen light inside and dim hallway. {style}",
        "text_position": "split"
    },
    {
        "id": 10,
        "text_es": "Una tarde, {name} notó que algo era diferente. {pet_name} no vino a saludarlo cuando llegó del colegio. No le robó nada. No se subió a ningún mueble. {name} lo encontró acurrucado en su camita, con los ojos tristes y la nariz caliente. {pet_name} no se sentía bien.",
        "text_en": "One afternoon, {name} noticed something was different. {pet_name} didn't come to greet them when they got home from school. Didn't steal anything. Didn't climb on any furniture. {name} found them curled up in their little bed, with sad eyes and a warm nose. {pet_name} wasn't feeling well.",
        "prompt": "Disney Pixar 3D style illustration. STRICT: exactly ONE teenager kneeling at LEFT of frame, exactly ONE sick pet in a bed at RIGHT of frame, no extra characters. HUMAN: A {gender_word} teenager ({age_display}) with {eye_desc} eyes{glasses_desc}, kneeling on the floor at LEFT of frame, school backpack still on one shoulder, gently touching the pet's head with one hand, worried eyebrows furrowed, fully focused with genuine concern. PET: {pet_desc}, curled up tightly in a small pet bed at RIGHT of frame, looking unwell and tired, droopy sad eyes, subdued still body language, vulnerable. TOGETHER: teen's hand rests gently on the sick pet's head, leaning close with worry. SETTING: Living room corner WIDE VIEW, small pet bed with soft blanket, school backpack on floor, quiet afternoon light, no screens visible. ATMOSPHERE: Worry and concern, sudden emotional shift, soft muted lighting, turning point. {style}",
        "text_position": "split"
    },
    {
        "id": 11,
        "text_es": "El corazón de {name} se encogió. Tomó a {pet_name} en brazos con mucho cuidado y lo llevó al veterinario. En la sala de espera, {name} no soltó a {pet_name} ni un segundo. El celular se quedó olvidado en el fondo de la mochila.",
        "text_en": "{name}'s heart sank. They carefully picked up {pet_name} and took them to the vet. In the waiting room, {name} didn't let go of {pet_name} for a single second. The phone stayed forgotten at the bottom of the backpack.",
        "prompt": "Disney Pixar 3D style illustration. STRICT: exactly ONE teenager seated at CENTER of frame, exactly ONE pet held in their lap, no extra characters. HUMAN: A {gender_word} teenager ({age_display}) with {eye_desc} eyes{glasses_desc}, sitting in a veterinary waiting room chair at CENTER of frame, arms wrapped protectively around the pet in their lap, chin resting on top of the pet's head, worried loving expression, completely focused on the animal. PET: {pet_desc}, cradled in the teenager's lap wrapped in a soft blanket, resting calmly against the teen's chest, tired eyes looking up with trust, feeling safe. TOGETHER: teen holds the pet snugly against their chest, both occupying the same chair, the backpack on the floor beside them with the phone forgotten inside. SETTING: Veterinary waiting room WIDE VIEW, plastic chairs, health posters on walls, clinical warm lighting. ATMOSPHERE: Tender worry, protective love, quiet anxiety, emotional depth. {style}",
        "text_position": "split"
    },
    {
        "id": 12,
        "text_es": "\"Solo necesita descanso y mucho cariño\", dijo la veterinaria con una sonrisa. {name} soltó un enorme suspiro de alivio. Abrazó a {pet_name} con fuerza y le susurró: \"Te prometo que todo va a estar bien.\" Y por primera vez en mucho tiempo, lo dijo de verdad.",
        "text_en": "\"Just needs rest and lots of love,\" said the vet with a smile. {name} let out a huge sigh of relief. They hugged {pet_name} tightly and whispered: \"I promise everything will be okay.\" And for the first time in a long while, they truly meant it.",
        "prompt": "Disney Pixar 3D style illustration. STRICT: exactly ONE teenager hugging at CENTER of frame, exactly ONE pet in their embrace, no extra characters. HUMAN: A {gender_word} teenager ({age_display}) with {eye_desc} eyes{glasses_desc}, kneeling on the floor at CENTER of veterinary office, arms wrapped around the pet in a tight emotional embrace, eyes closed with tears of relief on cheeks, genuine deep emotion on face. PET: {pet_desc}, standing calmly as the teenager wraps both arms around its neck and shoulders, eyes soft with trust, tail wagging gently, feeling the warmth of the embrace. TOGETHER: teen kneels and holds the pet in a full tearful hug of relief, cheek pressed against the pet's head. SETTING: Veterinary examination room WIDE VIEW, examination table and equipment in background, soft overhead lighting, clean clinical space. ATMOSPHERE: Overwhelming relief, deep love realized, tears of joy, emotional catharsis. {style}",
        "text_position": "split"
    },
    {
        "id": 13,
        "text_es": "De vuelta en casa, {name} preparó el lugar más cómodo del mundo para {pet_name}: almohadas, mantas suaves y su camiseta favorita para que tuviera su olor cerca. Se sentó a su lado y le acarició la cabeza durante horas, sin mirar el celular ni una sola vez.",
        "text_en": "Back home, {name} set up the coziest spot in the world for {pet_name}: pillows, soft blankets, and their favorite t-shirt so {pet_name} could have their scent nearby. They sat beside them and stroked their head for hours, without looking at the phone even once.",
        "prompt": "Disney Pixar 3D style illustration. STRICT: exactly ONE teenager sitting at LEFT of frame, exactly ONE pet in a nest at CENTER of frame, no extra characters. HUMAN: A {gender_word} teenager ({age_display}) with {eye_desc} eyes{glasses_desc}, sitting cross-legged on the living room floor at LEFT of frame, one hand gently stroking the pet's head, peaceful devoted expression, no phone visible. PET: {pet_desc}, lying in an elaborate nest of soft pillows and blankets at CENTER of frame, eyes half-closed in peaceful comfort, healing expression, enjoying the gentle petting. TOGETHER: teen sits beside the cozy nest petting the pet softly, phone lying forgotten face-down on the floor far behind them. SETTING: Living room floor WIDE VIEW, pillow and blanket nest, soft warm lamplight, curtains drawn, cozy evening. ATMOSPHERE: Devoted care, healing warmth, quiet peaceful devotion, golden lamplight. {style}",
        "text_position": "split"
    },
    {
        "id": 14,
        "text_es": "Esa noche, {name} no pudo dormir. Se quedó pensando en todos los momentos en que {pet_name} había intentado llamar su atención: el celular robado, el teclado invadido, los calcetines escondidos. No eran travesuras. Eran cartas de amor.",
        "text_en": "That night, {name} couldn't sleep. They lay thinking about all the times {pet_name} had tried to get their attention: the stolen phone, the invaded keyboard, the hidden socks. They weren't pranks. They were love letters.",
        "prompt": "Disney Pixar 3D style illustration. STRICT: exactly ONE teenager in the bed above, exactly ONE pet in a small bed below, no extra characters. HUMAN: A {gender_word} teenager ({age_display}) with {eye_desc} eyes{glasses_desc}, lying in bed at the TOP of frame, staring at the ceiling with glistening emotional eyes, one hand hanging off the edge of the bed reaching downward, expression of deep realization. PET: {pet_desc}, sleeping peacefully in a pet bed on the floor BELOW the hanging hand, one paw stretched upward touching the teen's fingers, peaceful sleeping expression. TOGETHER: teen's hanging hand and pet's raised paw nearly touch in the moonlit darkness, a connection even in sleep. SETTING: Dark bedroom WIDE VIEW, moonlight through window creating soft blue-silver light, serene night atmosphere. ATMOSPHERE: Deep emotional realization, moonlit contemplation, bittersweet understanding, quiet tears, blue-silver night light. {style}",
        "text_position": "split"
    },
    {
        "id": 15,
        "text_es": "A la mañana siguiente, {name} hizo algo que no hacía en meses: se despertó temprano, guardó el celular en un cajón y dijo: \"{pet_name}, hoy es TU día.\" {pet_name} levantó las orejas, ladeó la cabeza y meneó la cola como un helicóptero. ¿Había escuchado bien?",
        "text_en": "The next morning, {name} did something they hadn't done in months: woke up early, put the phone in a drawer, and said: \"{pet_name}, today is YOUR day.\" {pet_name} perked up their ears, tilted their head, and wagged their tail like a helicopter. Had they heard right?",
        "prompt": "Disney Pixar 3D style illustration. STRICT: exactly ONE teenager standing at LEFT of frame, exactly ONE pet sitting at RIGHT of frame, no extra characters, pure illustration only, zero text. HUMAN: A {gender_word} teenager ({age_display}) with {eye_desc} eyes{glasses_desc}, standing energetically at the LEFT side of the bedroom doorway, big genuine smile, both arms spread wide in excitement, wearing casual outdoor clothes, one hand gesturing invitingly toward the pet. PET: {pet_desc}, sitting upright at RIGHT of frame in the hallway looking up at the teenager, head tilted to one side, ears fully perked, tail a blur from wagging so fast, eyes wide with surprised delight. TOGETHER: teen stands in the doorway framed by morning light while the pet sits facing them in joyful disbelief. SETTING: Home hallway morning WIDE VIEW, bright golden morning sunlight flooding through open front door in background, shoes by the door. ATMOSPHERE: Joyful new beginning, bright exciting morning, pure happiness, surprise and delight. {style}",
        "text_position": "split"
    },
    {
        "id": 16,
        "text_es": "Salieron juntos al parque, como en los viejos tiempos. {name} lanzaba la pelota y {pet_name} corría como si volara. Se revolcaron en el pasto, se mojaron en la fuente y se rieron tanto que les dolía la panza. La gente los miraba sonriendo.",
        "text_en": "They went to the park together, just like the old days. {name} threw the ball and {pet_name} ran like they were flying. They rolled in the grass, got soaked at the fountain, and laughed so hard their bellies hurt. People watched them smiling.",
        "prompt": "Disney Pixar 3D style illustration. STRICT: exactly ONE teenager lying on grass at LEFT of frame, exactly ONE pet lying on grass at RIGHT of frame, no extra characters. HUMAN: A {gender_word} teenager ({age_display}) with {eye_desc} eyes{glasses_desc}, lying on green park grass at LEFT of frame, laughing hysterically, clothes grass-stained and slightly wet, arms spread wide, pure uninhibited joy. PET: {pet_desc}, lying on the park grass at RIGHT of frame beside the teenager, panting happily, wet and grass-stained too, a tennis ball nearby, tail wagging, pure happiness. TOGETHER: teen and pet lie side by side on the grass, both messy and joyful, the deep bond fully restored. SETTING: Beautiful park WIDE VIEW, green grass, water fountain in background, blue sky with fluffy clouds, warm golden afternoon. ATMOSPHERE: Pure unbridled joy, deep reconnection, golden afternoon light, happiness restored. {style}",
        "text_position": "split"
    },
    {
        "id": 17,
        "text_es": "De vuelta en casa, {name} se sentó en el suelo con {pet_name} y sacó una caja de fotos viejas. \"Mira, aquí eras un cachorro y yo era un enano\", se rio. {pet_name} olfateó las fotos y le lamió la cara, como diciendo: \"Yo siempre te he querido igual.\"",
        "text_en": "Back home, {name} sat on the floor with {pet_name} and pulled out a box of old photos. \"Look, you were a puppy here and I was tiny,\" they laughed. {pet_name} sniffed the photos and licked their face, as if saying: \"I've always loved you the same.\"",
        "prompt": "Disney Pixar 3D style illustration. STRICT: exactly ONE teenager sitting at CENTER-LEFT of frame, exactly ONE pet sitting close beside them at CENTER-RIGHT, no extra characters. HUMAN: A {gender_word} teenager ({age_display}) with {eye_desc} eyes{glasses_desc}, sitting cross-legged on the living room floor at CENTER-LEFT, holding old printed photos and laughing warmly, face scrunched up from a lick, happy tearful expression. PET: {pet_desc}, sitting right beside the teenager at CENTER-RIGHT, leaning in to lick the teen's cheek affectionately, tail wagging, surrounded by scattered old photos on the floor. TOGETHER: teen and pet sit close together at center frame, photos spread on the floor around them, sharing a warm emotional moment. SETTING: Living room floor WIDE VIEW, scattered old photos showing a puppy and young child, warm lamp light, cozy carpeted floor, photo box beside them. ATMOSPHERE: Warm nostalgia, deep love, happy tears, golden lamplight, beautiful emotional connection. {style}",
        "text_position": "split"
    },
    {
        "id": 18,
        "text_es": "{name} tomó el celular, pero esta vez para algo diferente: le sacó una foto a {pet_name} con una sonrisa enorme. \"Esta va directo a mi fondo de pantalla\", dijo. Y escribió una nueva regla en un papel que pegó en la pared: \"Regla #1: Todos los días, tiempo con {pet_name}.\"",
        "text_en": "{name} picked up the phone, but this time for something different: they took a photo of {pet_name} with a huge smile. \"This is going straight to my wallpaper,\" they said. And they wrote a new rule on paper and stuck it on the wall: \"Rule #1: Every day, time with {pet_name}.\"",
        "prompt": "Disney Pixar 3D style illustration. STRICT: exactly ONE teenager at LEFT of frame holding a phone as camera, exactly ONE pet sitting at RIGHT of frame posing, no extra characters, pure illustration only, zero text. HUMAN: A {gender_word} teenager ({age_display}) with {eye_desc} eyes{glasses_desc}, kneeling at LEFT of frame, holding a phone up as a camera toward the pet, big warm smile, eyes lit with genuine affection. PET: {pet_desc}, sitting nicely at RIGHT of frame facing the camera, looking directly at the phone lens with bright happy eyes, tail wagging, natural adorable pose. TOGETHER: teen frames the pet in their phone camera from a few feet away, both looking at each other through the lens with joy. SETTING: Living room WIDE VIEW, warm golden hour lighting, cozy home atmosphere, colorful small sticky notes on the wall behind them. ATMOSPHERE: Warm transformation, technology used for love, golden light, heartwarming joy. {style}",
        "text_position": "split"
    },
    {
        "id": 19,
        "text_es": "Esa noche, {name} se acostó con {pet_name} acurrucado a sus pies, exactamente como cuando era pequeño. Pero ahora era diferente. Ahora {name} sabía algo que antes no entendía: que el amor de una mascota no pide nada a cambio, solo pide estar cerca. Y {name} prometió no volver a olvidarlo jamás.",
        "text_en": "That night, {name} went to bed with {pet_name} curled up at their feet, just like when they were little. But now it was different. Now {name} understood something they hadn't before: that a pet's love asks for nothing in return, it only asks to be close. And {name} promised never to forget that again.",
        "prompt": "Disney Pixar 3D style illustration. STRICT: exactly ONE teenager lying in bed at TOP of frame, exactly ONE pet curled at their feet at BOTTOM of frame, no extra characters. HUMAN: A {gender_word} teenager ({age_display}) with {eye_desc} eyes{glasses_desc}, lying in bed under a cozy blanket at the TOP of frame, peaceful happy smile, eyes closing with contentment, one hand resting along their side. PET: {pet_desc}, curled up peacefully at the FOOT of the bed at BOTTOM of frame, head resting on the teenager's feet, deeply content expression, eyes half-closed, finally at peace and reconnected. TOGETHER: teen and pet rest in bed together, top to bottom of frame, the phone on the nightstand shows the pet's photo as wallpaper. SETTING: Teenager bedroom at night WIDE VIEW, cozy bed with warm blankets, soft nightlight glow, phone on nightstand, moonlight through window, stars outside. ATMOSPHERE: Perfect peaceful resolution, warm golden nightlight, deep contentment, love fully realized, beautiful serene ending. {style}",
        "text_position": "split"
    }
]

CLOSING_SCENE = {
    "id": 20,
    "prompt": "Disney Pixar 3D style illustration. STRICT: exactly ONE teenager at LEFT of frame, exactly ONE pet at RIGHT of frame, sitting together on a hilltop, no extra characters. HUMAN: A {gender_word} teenager ({age_display}) with {eye_desc} eyes{glasses_desc}, sitting on green grass at LEFT side of a hilltop, legs stretched out, leaning back on both hands, head tilted up toward the warm golden sky, peaceful genuine smile, casual modern clothes. PET: {pet_desc}, sitting upright at RIGHT side of the same hilltop spot, leaning gently against the teenager's side, tail resting peacefully, looking up at the golden sky too, content calm expression. TOGETHER: teen and pet sit side by side on the hilltop, their silhouettes framed by warm golden sunset light, sharing a quiet timeless moment. SETTING: Grassy hilltop at golden hour WIDE VIEW, vast warm sunset sky with soft orange and pink clouds, wildflowers in the grass, a large tree with golden leaves behind them, birds in the distant sky, town far below. ATMOSPHERE: Golden hour warmth, deep peaceful friendship, beautiful ending, warm orange and gold tones, timeless bond. {style}",
    "text_position": "none"
}

FRONT_COVER = {
    "prompt": "Disney Pixar 3D style illustration. STRICT: exactly ONE {gender_word} teenager and exactly ONE pet together at CENTER of frame, no other characters, pure illustration only, zero text. HUMAN: A {gender_word} teenager with {eye_desc} eyes, full appearance matching @image1 exactly, sitting on the floor at CENTER-LEFT of frame, knees up, arm around the pet beside them, warm genuine smile, casual modern clothes, relaxed happy posture. PET: {pet_desc}, sitting close beside the teenager at CENTER-RIGHT of frame, leaning against them naturally, happy relaxed expression, tail resting peacefully. TOGETHER: the teenager and pet sit as a pair at center frame, both looking toward the viewer with contentment and warmth. SETTING: Soft warm background WIDE VIEW, hints of a cozy home, warm golden backlighting creating a halo effect, simple clean composition. ATMOSPHERE: Warm connection, modern and genuine, golden backlight, deep friendship, centered book cover composition. {style}"
}

BACK_COVER = {
    "prompt": "Disney Pixar 3D style illustration. STRICT: zero characters, only objects and scenery. SETTING: A cozy teenager's desk scene at golden hour WIDE VIEW, a phone lying on the desk with a glowing screen, a pair of headphones, scattered old printed photographs of a child and pet growing up together, a tennis ball, a soft blanket draped over the desk chair, warm sunset light streaming through a window onto the objects, a small pet bed visible in the corner, colorful small sticky notes on the wall. ATMOSPHERE: Warm nostalgic, peaceful evening, love expressed through objects, golden warm tones, story told through belongings. Pure illustration only, zero text or lettering. {style}"
}


def build_human_preview_prompt(human_desc: str, **kwargs) -> str:
    return (
        f"High-quality 3D animated children's book illustration. "
        f"CHARACTER: {human_desc}. "
        f"OUTFIT: casual hoodie, jeans and sneakers — modern teen style. "
        f"FULL BODY portrait, standing naturally with relaxed confident smile, "
        f"centered in frame, occupying 60% of frame height. "
        f"NEUTRAL SOLID GRADIENT BACKGROUND (soft cream to warm beige), plain studio. "
        f"Warm lighting. Clean illustration only."
    )


def build_human_preview_prompt_with_photo(gender_word: str, age_display: str, eye_desc: str = "", hair_desc: str = "", glasses: str = "", facial_hair: str = "", skin_tone: str = "") -> str:
    skin_strict = f"Maintain {skin_tone} complexion — do not lighten the skin tone. " if skin_tone else ""
    eye_part = f"{eye_desc} eyes, " if eye_desc else ""
    return (
        f"Disney Pixar 3D style illustration. 3D animated {gender_word} with face shape, skin complexion, hair amount and color, "
        f"and {eye_part}all matching @image1 exactly — do not invent or change any physical feature. "
        f"FULL BODY portrait, centered, relaxed confident expression. "
        f"NEUTRAL SOLID GRADIENT BACKGROUND (soft cream to warm beige). "
        f"{skin_strict}"
        f"Clean illustration only."
    )


def build_pet_preview_prompt(pet_desc: str, pet_size: str = "medium") -> str:
    size_desc_map = {
        "small":  "compact small body, fits fully in frame with space around it",
        "medium": "full body fits naturally and comfortably in frame",
        "large":  "big imposing body fills the frame, broad and tall",
    }
    size_desc = size_desc_map.get(pet_size, size_desc_map["medium"])
    return f"Disney Pixar 3D style illustration. FULL BODY portrait of {pet_desc}, sitting or standing naturally, friendly expression, centered in frame, occupying 50% of frame height, {size_desc}. NEUTRAL SOLID GRADIENT BACKGROUND (soft cream to warm beige), plain studio background. Warm lighting, expressive eyes. Clean professional animation art, clean illustration only."


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


def build_scene_prompt(scene: dict, human_desc: str, pet_name: str, pet_desc: str, age_display: str = "teenager", eye_desc: str = "", gender_word: str = "girl", glasses: str = "", **kwargs) -> str:
    scene_id = scene.get('id', 0)
    pet_species = kwargs.get('pet_species', 'dog')
    animal_word = "cat" if pet_species == "cat" else "dog"

    prompt = scene.get('prompt', '')
    prompt = prompt.replace('{human_desc}', human_desc)
    prompt = prompt.replace('{pet_name}', pet_name)
    prompt = prompt.replace('{pet_desc}', pet_desc)

    # Scene 1 is a childhood flashback — always use "young child around 6 years old"
    # regardless of the teen's actual age_display
    if scene_id == 1:
        prompt = prompt.replace('{age_display}', 'young child around 6 years old')
    else:
        prompt = prompt.replace('{age_display}', age_display)

    eye_color_only = eye_desc.replace(' eyes', '').strip() if eye_desc else ''
    prompt = prompt.replace('{eye_desc}', eye_color_only)
    prompt = prompt.replace('{gender_word}', gender_word)
    glasses_desc = ", wearing glasses" if glasses == "glasses" else ", wearing sunglasses" if glasses == "sunglasses" else ""
    prompt = prompt.replace('{glasses_desc}', glasses_desc)
    prompt = prompt.replace('{style}', STYLE_BASE)
    if gender_word and '{gender_word}' in scene.get('prompt', ''):
        prompt += f" The character is a {gender_word}."

    # Explicitly name the animal type in STRICT so FLUX doesn't default to dog
    # "ONE pet" → "ONE cat" or "ONE dog" based on user's form selection
    prompt = prompt.replace('ONE pet', f'ONE {animal_word}')

    return prompt


def build_story_text(scene: dict, child_name: str, pet_name: str, language: str = 'es') -> str:
    text_key = 'text_es' if language == 'es' else 'text_en'
    text = scene.get(text_key, '')
    text = text.replace('{pet_name}', pet_name)
    text = text.replace('{name}', child_name)
    return text


def get_all_scene_prompts(human_desc: str, pet_name: str, pet_desc: str, age_display: str = "13 year old teenager", eye_desc: str = "", gender_word: str = "girl") -> list:
    prompts = []
    for scene in FURRY_LOVE_TEEN_SCENES:
        prompts.append(build_scene_prompt(scene, human_desc, pet_name, pet_desc, age_display, eye_desc, gender_word))
    prompts.append(build_scene_prompt(CLOSING_SCENE, human_desc, pet_name, pet_desc, age_display, eye_desc, gender_word))
    return prompts


def get_all_story_texts(child_name: str, pet_name: str, language: str = 'es') -> list:
    texts = []
    for scene in FURRY_LOVE_TEEN_SCENES:
        texts.append({
            'id': scene['id'],
            'text': build_story_text(scene, child_name, pet_name, language),
            'text_position': scene.get('text_position', 'split')
        })
    return texts


def get_cover_prompts(human_desc: str, pet_name: str, pet_desc: str, age_display: str = "13 year old teenager", eye_desc: str = "", gender_word: str = "girl", glasses: str = "") -> dict:
    return {
        'front': build_scene_prompt(FRONT_COVER, human_desc, pet_name, pet_desc, age_display, eye_desc, gender_word, glasses=glasses),
        'back': build_scene_prompt(BACK_COVER, human_desc, pet_name, pet_desc, age_display, eye_desc, gender_word, glasses=glasses)
    }
