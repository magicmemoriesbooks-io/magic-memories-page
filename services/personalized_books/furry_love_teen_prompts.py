# Tú y tu Amor Peludo - Teen Story Prompts
# 19 scenes + closing + covers
# Story: "Mi compañero fiel" - A teen rediscovers the bond with their pet
# Ages 10-15 - Emotional reconnection, humor, heartfelt moments
#
# FLUX 2 Dev with TWO reference images:
#   1. Human preview: detailed character description → generates reference image 1
#   2. Pet preview: detailed pet description → generates reference image 2
#   3. Scenes: FLUX 2 Dev takes BOTH references → prompts bind roles explicitly
#
# Schema (same as furry_love):
#   HUMAN CHARACTER → PET CHARACTER → ACTION → SETTING → ATMOSPHERE → STRICT
#
# Rules:
#   - guidance_scale=3.5, num_inference_steps=28, aspect_ratio=3:4
#   - Keep prompts concise - FLUX 2 Dev loses focus with >300 words
#   - Style: Disney Pixar 3D everywhere, NO watercolor
#   - Human is a teenager (10-15 years old)
#   - Pet is a dog or cat (customized breed, color, pattern)
#   - TWO reference images per scene (human + pet)
#   - Text uses {name} for human and {pet_name} for pet

STYLE_BASE = "Disney Pixar 3D style, soft warm lighting, emotional cinematic atmosphere, WIDE SHOT full body from head to feet, characters occupy 40% of frame, modern home and neighborhood environment visible, clean illustration only. STRICT: All teenagers wear casual modern clothes, fully clothed always."

FURRY_LOVE_TEEN_SCENES = [
    {
        "id": 1,
        "text_es": "Hubo un tiempo en que {name} y {pet_name} eran inseparables. Juntos corrían por el parque, se acurrucaban en el sofá y compartían cada momento del día. {pet_name} era el mejor amigo de {name}... pero eso fue hace tiempo.",
        "text_en": "There was a time when {name} and {pet_name} were inseparable. They ran together in the park, cuddled on the couch, and shared every moment of the day. {pet_name} was {name}'s best friend... but that was a while ago.",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: A younger child version of the teenager ({age_display} but shown as 6 years old in a memory) with {eye_desc} eyes{glasses_desc}, small, laughing, running freely. PET: {pet_desc}, younger and energetic, running alongside the child, both joyful and carefree, matching pace. ACTION: A happy memory scene of the child and pet running together through a sunny park, pure joy and connection between them, motion blur suggesting speed and fun. SETTING: Beautiful sunny park WIDE VIEW, green grass, playground in background, warm golden afternoon light, soft dreamy edges suggesting this is a memory, slightly hazy warm filter. ATMOSPHERE: Nostalgic warmth, golden memory glow, pure happiness from the past, bittersweet beauty. STRICT: Only ONE child, ONE pet, memory/flashback scene with dreamy warm edges. {style}",
        "text_position": "split"
    },
    {
        "id": 2,
        "text_es": "Pero {name} ya no era un niño pequeño. Ahora tenía su celular, sus videojuegos y sus amigos del colegio. {pet_name} se acercaba moviendo la cola, pero {name} apenas levantaba la vista de la pantalla. \"Ahora no, {pet_name}\", decía sin mirar.",
        "text_en": "But {name} wasn't a little kid anymore. Now they had their phone, video games, and school friends. {pet_name} would come over wagging their tail, but {name} barely looked up from the screen. \"Not now, {pet_name},\" they'd say without looking.",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: A teenager ({age_display}) with {eye_desc} eyes{glasses_desc} slouched on a beanbag chair, completely absorbed in a glowing smartphone, headphones around neck, dismissive expression, one hand waving the pet away without looking. PET: {pet_desc}, sitting right next to the teenager looking up with big hopeful pleading eyes, tail gently wagging, head tilted, waiting patiently for attention. ACTION: The teenager ignores the pet while staring at their phone, the pet sits loyally beside them hoping for a moment of attention. SETTING: Modern teenager bedroom WIDE VIEW, gaming posters on walls, desk with computer, clothes on floor, warm afternoon light through window, phone screen glowing on the teen's face. ATMOSPHERE: Gentle sadness, contrast between cold screen light and warm pet presence, quiet longing. STRICT: Only ONE teenager on beanbag, ONE pet beside them, modern bedroom scene. {style}",
        "text_position": "split"
    },
    {
        "id": 3,
        "text_es": "{pet_name} no se rendía fácilmente. Un día, mientras {name} escribía un mensaje importante, {pet_name} se acercó sigilosamente y... ¡ZAS! Le robó el celular de las manos con la boca y salió corriendo a toda velocidad por el pasillo.",
        "text_en": "{pet_name} didn't give up easily. One day, while {name} was typing an important message, {pet_name} crept up silently and... SNAP! Snatched the phone right out of their hands and took off running down the hallway at full speed.",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: A teenager ({age_display}) with {eye_desc} eyes{glasses_desc} jumping up from a chair in shock and surprise, mouth open, arms reaching forward desperately, expression of total disbelief, mid-lunge trying to catch the pet. PET: {pet_desc}, running away at full speed down a hallway with a smartphone carefully held in its mouth, mischievous triumphant expression, ears back from speed, tail held high. ACTION: The pet sprints away with the stolen phone in its mouth while the teenager leaps up in shock trying to chase them, comedic chase beginning. SETTING: Home hallway WIDE VIEW, the pet running ahead, teenager lunging from a doorway behind, blurred motion lines, doors along hallway, warm lighting. ATMOSPHERE: Hilarious chaos, comedic energy, mischievous fun, bright dynamic lighting. STRICT: Only ONE teenager chasing, ONE pet running with phone, comedic chase scene. {style}",
        "text_position": "split"
    },
    {
        "id": 4,
        "text_es": "\"¡{pet_name}, devuélveme el celular!\" gritó {name} persiguiéndolo por toda la casa. {pet_name} esquivaba muebles como un profesional, saltaba sobre el sofá y se metía debajo de la mesa. Cuando por fin lo atrapó, el celular estaba lleno de babas. {name} no pudo evitar reírse.",
        "text_en": "\"Give me back my phone, {pet_name}!\" yelled {name}, chasing them through the whole house. {pet_name} dodged furniture like a pro, jumped over the couch, and dove under the table. When {name} finally caught them, the phone was covered in drool. {name} couldn't help but laugh.",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: A teenager ({age_display}) with {eye_desc} eyes{glasses_desc} on their knees under a dining table, reaching for the pet, messy hair from the chase, breaking into laughter despite trying to look annoyed, one hand extended. PET: {pet_desc}, under the table with the drool-covered phone between its front paws, playful guilty expression, tail wagging, looking at the teenager with bright happy eyes. ACTION: The teenager reaches under the table to retrieve their drool-covered phone from the mischievous pet, both ending up laughing at the situation. SETTING: Dining room WIDE VIEW, chairs pushed aside from the chase, table legs framing the scene, scattered cushions from the couch visible behind, warm home lighting. ATMOSPHERE: Comedic resolution, warm laughter breaking through, genuine fun moment, bright warm tones. STRICT: Only ONE teenager reaching under table, ONE pet with phone, comedic moment. {style}",
        "text_position": "split"
    },
    {
        "id": 5,
        "text_es": "Al día siguiente, {name} estaba haciendo tarea en la computadora. {pet_name} apareció de la nada y se subió directamente encima del teclado. La pantalla se llenó de letras sin sentido: \"asdfjklñ;asdfgh\". {pet_name} se quedó ahí echado, mirando a {name} como si fuera el lugar más cómodo del mundo.",
        "text_en": "The next day, {name} was doing homework on the computer. {pet_name} appeared out of nowhere and climbed right onto the keyboard. The screen filled with gibberish: \"asdfjklñ;asdfgh\". {pet_name} just lay there, looking at {name} as if it were the most comfortable spot in the world.",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: A teenager ({age_display}) with {eye_desc} eyes{glasses_desc} sitting at a desk, exasperated but amused expression, hands raised in a helpless gesture, slight smile forming, looking at the pet on the keyboard. PET: {pet_desc}, lying sprawled comfortably across the laptop keyboard, completely relaxed and content, looking up at the teenager with innocent satisfied eyes, paws draped over the keyboard edges, occupying the entire keyboard. ACTION: The pet lies comfortably across the laptop keyboard blocking the teenager from working, the teenager looks exasperated but can't help smiling. SETTING: Teen study desk WIDE VIEW, laptop with blank glowing screen, school books and notebooks around, desk lamp, bedroom in background, evening study atmosphere. ATMOSPHERE: Comedic frustration turning to amusement, warm desk lamp light, cozy evening, humorous interruption. STRICT: Only ONE teenager at desk, ONE pet sprawled on keyboard, screen glows blank white, comedic study scene. Pure illustration only, zero text or lettering. {style}",
        "text_position": "split"
    },
    {
        "id": 6,
        "text_es": "{name} suspiró y movió a {pet_name} con cuidado. \"Eres imposible\", le dijo, pero le dio una caricia rápida en la cabeza antes de volver a la tarea. {pet_name} meneó la cola. Esa caricia era un pequeño triunfo.",
        "text_en": "{name} sighed and gently moved {pet_name} aside. \"You're impossible,\" they said, but gave a quick pat on the head before going back to homework. {pet_name} wagged their tail. That little pat was a small victory.",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: A teenager ({age_display}) with {eye_desc} eyes{glasses_desc} sitting at a desk, one hand typing on the laptop, the other hand reaching down to gently pet the animal beside the chair, soft genuine smile, eyes still on screen but expression warmer. PET: {pet_desc}, sitting on the floor right beside the desk chair, eyes closed in bliss as it receives a head pat, tail wagging gently, leaning into the touch, peaceful content expression. ACTION: The teenager gives the pet an absent-minded but affectionate head pat while working, the pet savors the small moment of connection, a tiny victory. SETTING: Study desk WIDE VIEW, laptop with homework on screen, warm desk lamp creating a cozy pool of light, bedroom around, evening atmosphere. ATMOSPHERE: Small warm moment, quiet tenderness breaking through distraction, soft warm lamplight, subtle emotional shift. STRICT: Only ONE teenager at desk, ONE pet beside chair, quiet tender moment. {style}",
        "text_position": "split"
    },
    {
        "id": 7,
        "text_es": "Pero la Operación Atención no había terminado. A la mañana siguiente, {name} buscaba sus calcetines por toda la habitación. \"¡Juro que los dejé aquí!\" Cuando miró debajo de la cama, encontró un tesoro escondido: tres pares de calcetines, un guante, y la gorra favorita de {name}. Todo en la cama de {pet_name}.",
        "text_en": "But Operation Attention wasn't over. The next morning, {name} searched the whole room for their socks. \"I swear I left them here!\" When they looked under the bed, they found a hidden treasure: three pairs of socks, a glove, and {name}'s favorite cap. All in {pet_name}'s bed.",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: A teenager ({age_display}) with {eye_desc} eyes{glasses_desc} on hands and knees peering under their bed with a flashlight, expression of shocked amusement discovering a pile of stolen items, eyes wide, mouth open in disbelief. PET: {pet_desc}, lying proudly in a pet bed surrounded by stolen socks, a glove, and a cap, looking at the teenager with proud innocent eyes as if showing off a treasure collection. ACTION: The teenager discovers a stash of stolen personal items in the pet's bed, the pet proudly guards its collection of socks, gloves, and a cap. SETTING: Teenager bedroom floor level WIDE VIEW, under-bed perspective, pet bed visible with pile of colorful socks and accessories, flashlight beam illuminating the stash, morning light from window. ATMOSPHERE: Hilarious discovery, comedic treasure hunt, warm morning light, pure mischief revealed. STRICT: Only ONE teenager looking under bed, ONE pet in its bed with stolen items, comedic discovery scene. {style}",
        "text_position": "split"
    },
    {
        "id": 8,
        "text_es": "\"¡{pet_name}!\" exclamó {name}, pero {pet_name} lo miraba con cara de ángel. Esos ojos grandes e inocentes eran su mejor arma. {name} negó con la cabeza, pero una sonrisa se le escapó. Recogió sus cosas y le rascó las orejas a {pet_name}. \"Eres un pequeño ladrón.\"",
        "text_en": "\"Oh, {pet_name}!\" exclaimed {name}, but {pet_name} looked at them with an angel face. Those big innocent eyes were their best weapon. {name} shook their head, but a smile escaped. They gathered their things and scratched {pet_name}'s ears. \"You're a little thief.\"",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: A teenager ({age_display}) with {eye_desc} eyes{glasses_desc} kneeling on the floor holding a bunch of recovered socks and a cap, shaking their head with a helpless grin, scratching the pet's ears with the free hand, warm affectionate expression despite pretending to be annoyed. PET: {pet_desc}, sitting next to the teenager with the most innocent angelic expression possible, huge sparkling eyes looking up, head tilted slightly, ears perked, the picture of pure innocence. ACTION: The teenager pretends to scold the pet while scratching its ears, the pet puts on its best innocent face, both sharing a warm funny moment. SETTING: Bedroom floor WIDE VIEW, scattered socks around them, pet bed nearby, morning sunlight streaming in, warm cozy atmosphere. ATMOSPHERE: Loving humor, fake scolding with real affection, warm golden morning light, heartwarming comedy. STRICT: Only ONE teenager kneeling, ONE innocent-looking pet, comedic bonding scene. {style}",
        "text_position": "split"
    },
    {
        "id": 9,
        "text_es": "Pasaron los días y {name} volvió a su rutina: colegio, celular, videojuegos, repetir. {pet_name} empezó a pasar más tiempo solo, echado junto a la puerta del cuarto de {name}, esperando. A veces se quedaba dormido ahí, con la nariz pegada a la rendija de la puerta.",
        "text_en": "Days passed and {name} went back to their routine: school, phone, video games, repeat. {pet_name} started spending more time alone, lying by {name}'s bedroom door, waiting. Sometimes they fell asleep there, nose pressed against the gap under the door.",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: A teenager ({age_display}) with {eye_desc} eyes{glasses_desc} visible through a slightly open bedroom door, sitting at their desk with headphones on, completely absorbed in a glowing computer screen, back to the door, unaware. PET: {pet_desc}, lying alone in the hallway right next to the closed bedroom door, head resting on front paws, nose pressed against the gap under the door, sad lonely eyes, waiting patiently, slightly droopy posture. ACTION: The pet waits loyally outside the closed bedroom door while the teenager is absorbed in their screen inside, a poignant scene of quiet devotion and loneliness. SETTING: Home hallway WIDE VIEW, closed bedroom door with warm light leaking from underneath, the pet alone in the darker hallway, family photos on walls, evening atmosphere. ATMOSPHERE: Quiet sadness, lonely devotion, contrast between warm screen light inside and dim hallway, emotional poignancy. STRICT: Only ONE pet lying by door, teenager barely visible through door crack, emotional waiting scene. {style}",
        "text_position": "split"
    },
    {
        "id": 10,
        "text_es": "Una tarde, {name} notó que algo era diferente. {pet_name} no vino a saludarlo cuando llegó del colegio. No le robó nada. No se subió a ningún mueble. {name} lo encontró acurrucado en su camita, con los ojos tristes y la nariz caliente. {pet_name} no se sentía bien.",
        "text_en": "One afternoon, {name} noticed something was different. {pet_name} didn't come to greet them when they got home from school. Didn't steal anything. Didn't climb on any furniture. {name} found them curled up in their little bed, with sad eyes and a warm nose. {pet_name} wasn't feeling well.",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: A teenager ({age_display}) with {eye_desc} eyes{glasses_desc} kneeling beside a pet bed on the floor, backpack still on one shoulder just arrived from school, worried concerned expression, gently touching the pet's head to check temperature, eyebrows furrowed with worry. PET: {pet_desc}, curled up tightly in a small pet bed, looking unwell and tired, droopy sad eyes, nose slightly dry, not moving much, subdued body language, vulnerable and small. ACTION: The teenager kneels beside the sick pet, checking on them with genuine worry, the first time in a long time that the teen is fully focused on the pet. SETTING: Living room corner WIDE VIEW, small pet bed with a soft blanket, school backpack dropped on floor, afternoon light, quiet still atmosphere, no screens visible. ATMOSPHERE: Worry and concern, sudden shift in priorities, quiet serious mood, soft muted lighting, emotional turning point. STRICT: Only ONE worried teenager kneeling, ONE sick pet in bed, emotional concern scene. {style}",
        "text_position": "split"
    },
    {
        "id": 11,
        "text_es": "El corazón de {name} se encogió. Tomó a {pet_name} en brazos con mucho cuidado y lo llevó al veterinario. En la sala de espera, {name} no soltó a {pet_name} ni un segundo. El celular se quedó olvidado en el fondo de la mochila.",
        "text_en": "{name}'s heart sank. They carefully picked up {pet_name} and took them to the vet. In the waiting room, {name} didn't let go of {pet_name} for a single second. The phone stayed forgotten at the bottom of the backpack.",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: A teenager ({age_display}) with {eye_desc} eyes{glasses_desc} sitting in a veterinary waiting room chair, holding the pet protectively in their lap wrapped in a soft blanket, arms wrapped around them, worried loving expression, chin resting on top of the pet's head, completely focused on the animal. PET: {pet_desc}, wrapped in a blanket in the teenager's lap, resting calmly against the teen's chest, tired but comforted eyes, feeling safe in their human's arms. ACTION: The teenager holds the sick pet protectively in the vet waiting room, completely devoted and worried, phone forgotten in the backpack on the floor. SETTING: Veterinary waiting room WIDE VIEW, plastic chairs, pet health posters on walls, backpack on floor with phone forgotten inside, other empty chairs, clinical but warm lighting. ATMOSPHERE: Tender worry, protective love, quiet anxiety, soft clinical light mixed with warmth from the bond, emotional depth. STRICT: Only ONE teenager holding ONE pet, veterinary waiting room, caring protective scene. {style}",
        "text_position": "split"
    },
    {
        "id": 12,
        "text_es": "\"Solo necesita descanso y mucho cariño\", dijo la veterinaria con una sonrisa. {name} soltó un enorme suspiro de alivio. Abrazó a {pet_name} con fuerza y le susurró: \"Te prometo que todo va a estar bien.\" Y por primera vez en mucho tiempo, lo dijo de verdad.",
        "text_en": "\"Just needs rest and lots of love,\" said the vet with a smile. {name} let out a huge sigh of relief. They hugged {pet_name} tightly and whispered: \"I promise everything will be okay.\" And for the first time in a long while, they truly meant it.",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: A teenager ({age_display}) with {eye_desc} eyes{glasses_desc} hugging the pet tightly against their chest in the vet's office, eyes closed with tears of relief, huge emotional sigh visible, squeezing the pet gently, genuine deep emotion on face. PET: {pet_desc}, being hugged by the teenager, nestled against their chest, eyes looking up at the teen with trust and love, small gentle tail movement, feeling the warmth of the embrace. ACTION: The teenager hugs the pet with deep relief after hearing good news from the vet, an emotional embrace full of love and promise, tears of relief. SETTING: Veterinary examination room WIDE VIEW, examination table, vet's equipment in background, soft overhead lighting, clean clinical space with warm emotional moment in center. ATMOSPHERE: Overwhelming relief, deep love realized, emotional catharsis, tears of joy, warm soft lighting contrasting clinical setting. STRICT: Only ONE teenager hugging ONE pet, veterinary office, emotional relief scene. {style}",
        "text_position": "split"
    },
    {
        "id": 13,
        "text_es": "De vuelta en casa, {name} preparó el lugar más cómodo del mundo para {pet_name}: almohadas, mantas suaves y su camiseta favorita para que tuviera su olor cerca. Se sentó a su lado y le acarició la cabeza durante horas, sin mirar el celular ni una sola vez.",
        "text_en": "Back home, {name} set up the coziest spot in the world for {pet_name}: pillows, soft blankets, and their favorite t-shirt so {pet_name} could have their scent nearby. They sat beside them and stroked their head for hours, without looking at the phone even once.",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: A teenager ({age_display}) with {eye_desc} eyes{glasses_desc} sitting cross-legged on the floor next to an elaborate cozy nest of pillows and blankets, gently stroking the pet's head with one hand, peaceful devoted expression, phone lying face-down on the floor far away ignored. PET: {pet_desc}, lying in a nest of soft pillows and blankets with a teenager's t-shirt as a bed, eyes half-closed in comfort, peaceful healing expression, enjoying the gentle petting, beginning to look better. ACTION: The teenager sits devotedly beside the pet's cozy recovery nest, petting them gently for hours, phone abandoned and forgotten on the floor. SETTING: Living room floor WIDE VIEW, elaborate pillow and blanket nest, soft warm lamplight, phone face-down on floor in background, cozy warm evening atmosphere, curtains drawn. ATMOSPHERE: Devoted care, healing warmth, quiet peaceful devotion, soft golden lamplight, love in action. STRICT: Only ONE teenager sitting, ONE pet in cozy nest, caring recovery scene. {style}",
        "text_position": "split"
    },
    {
        "id": 14,
        "text_es": "Esa noche, {name} no pudo dormir. Se quedó pensando en todos los momentos en que {pet_name} había intentado llamar su atención: el celular robado, el teclado invadido, los calcetines escondidos. No eran travesuras. Eran cartas de amor.",
        "text_en": "That night, {name} couldn't sleep. They lay thinking about all the times {pet_name} had tried to get their attention: the stolen phone, the invaded keyboard, the hidden socks. They weren't pranks. They were love letters.",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: A teenager ({age_display}) with {eye_desc} eyes{glasses_desc} lying in bed at night, staring at the ceiling with wet emotional eyes, a tear rolling down one cheek, one hand hanging off the bed touching the sleeping pet below, expression of deep realization and guilt mixed with love. PET: {pet_desc}, sleeping in a pet bed right beside the teenager's bed, one paw stretched up touching the hanging hand, peaceful sleeping expression, the bond visible even in sleep. ACTION: The teenager lies awake at night having an emotional realization about their pet's love, hand reaching down to touch the sleeping pet, a moment of deep understanding. SETTING: Dark bedroom at night WIDE VIEW, moonlight through window creating soft blue light, teenager in bed with hand hanging down, pet in bed below with paw reaching up, serene night atmosphere. ATMOSPHERE: Deep emotional realization, moonlit contemplation, bittersweet understanding, quiet tears, beautiful blue-silver night light. STRICT: Only ONE teenager in bed, ONE pet in pet bed below, nighttime emotional realization scene. {style}",
        "text_position": "split"
    },
    {
        "id": 15,
        "text_es": "A la mañana siguiente, {name} hizo algo que no hacía en meses: se despertó temprano, guardó el celular en un cajón y dijo: \"{pet_name}, hoy es TU día.\" {pet_name} levantó las orejas, ladeó la cabeza y meneó la cola como un helicóptero. ¿Había escuchado bien?",
        "text_en": "The next morning, {name} did something they hadn't done in months: woke up early, put the phone in a drawer, and said: \"{pet_name}, today is YOUR day.\" {pet_name} perked up their ears, tilted their head, and wagged their tail like a helicopter. Had they heard right?",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: A teenager ({age_display}) with {eye_desc} eyes{glasses_desc} standing energetically in their bedroom doorway, big genuine smile, arms spread wide in excitement, wearing casual outdoor clothes with backpack, one hand gesturing toward the pet invitingly. PET: {pet_desc}, sitting in the hallway looking up at the teenager with head tilted, ears fully perked, tail wagging so fast it is a blur, eyes sparkling with surprised excitement. ACTION: The teenager invites the pet for an outdoor adventure, the pet reacts with incredulous joy, tail wagging wildly, ears perked in surprise. SETTING: Home hallway morning WIDE VIEW, bright morning sunlight flooding through open front door, cheerful bright atmosphere, fresh new day energy, shoes by the door ready to go out. ATMOSPHERE: Joyful new beginning, bright exciting morning, pure happiness, surprise and delight, warm golden morning light. STRICT: Only ONE teenager standing excitedly, ONE surprised happy pet, joyful morning scene. Pure illustration only, zero text or lettering. {style}",
        "text_position": "split"
    },
    {
        "id": 16,
        "text_es": "Salieron juntos al parque, como en los viejos tiempos. {name} lanzaba la pelota y {pet_name} corría como si volara. Se revolcaron en el pasto, se mojaron en la fuente y se rieron tanto que les dolía la panza. La gente los miraba sonriendo.",
        "text_en": "They went to the park together, just like the old days. {name} threw the ball and {pet_name} ran like they were flying. They rolled in the grass, got soaked at the fountain, and laughed so hard their bellies hurt. People watched them smiling.",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: A teenager ({age_display}) with {eye_desc} eyes{glasses_desc} lying on green grass laughing hysterically, clothes grass-stained and slightly wet, arms spread wide, pure uninhibited joy, looking at the pet beside them with the biggest happiest smile. PET: {pet_desc}, lying on the grass beside the teenager, also happy and energized, panting with joy, a tennis ball nearby, both of them messy and grass-stained, pure happiness radiating from both. ACTION: The teenager and pet lie together on the park grass after playing hard, both messy, wet, grass-stained, and incredibly happy, laughing together like old times. SETTING: Beautiful park WIDE VIEW, green grass field, water fountain visible in background, blue sky with fluffy clouds, tennis ball on grass, other park visitors smiling in far background. ATMOSPHERE: Pure unbridled joy, reconnection, golden afternoon light, happiness restored, warm nostalgic callback to scene 1. STRICT: Only ONE teenager on grass, ONE pet beside them, joyful park reunion scene. {style}",
        "text_position": "split"
    },
    {
        "id": 17,
        "text_es": "De vuelta en casa, {name} se sentó en el suelo con {pet_name} y sacó una caja de fotos viejas. \"Mira, aquí eras un cachorro y yo era un enano\", se rio. {pet_name} olfateó las fotos y le lamió la cara, como diciendo: \"Yo siempre te he querido igual.\"",
        "text_en": "Back home, {name} sat on the floor with {pet_name} and pulled out a box of old photos. \"Look, you were a puppy here and I was tiny,\" they laughed. {pet_name} sniffed the photos and licked their face, as if saying: \"I've always loved you the same.\"",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: A teenager ({age_display}) with {eye_desc} eyes{glasses_desc} sitting cross-legged on the living room floor, holding old printed photos and showing them to the pet, laughing with warm nostalgic joy, face being licked by the pet, eyes squinted from the lick, happy tearful expression. PET: {pet_desc}, sitting close to the teenager, licking the teen's cheek affectionately, tail wagging, surrounded by scattered old photos on the floor showing younger versions of both of them. ACTION: The teenager shows old photos to the pet who responds with a loving face lick, both sharing a warm emotional moment surrounded by memories of their life together. SETTING: Living room floor WIDE VIEW, scattered old photos showing a puppy/kitten and young child together, warm lamp light, cozy carpeted floor, photo box beside them. ATMOSPHERE: Warm nostalgia, deep love, happy tears, golden warm lamplight, beautiful emotional connection. STRICT: Only ONE teenager on floor, ONE affectionate pet, nostalgic memory scene with photos. {style}",
        "text_position": "split"
    },
    {
        "id": 18,
        "text_es": "{name} tomó el celular, pero esta vez para algo diferente: le sacó una foto a {pet_name} con una sonrisa enorme. \"Esta va directo a mi fondo de pantalla\", dijo. Y escribió una nueva regla en un papel que pegó en la pared: \"Regla #1: Todos los días, tiempo con {pet_name}.\"",
        "text_en": "{name} picked up the phone, but this time for something different: they took a photo of {pet_name} with a huge smile. \"This is going straight to my wallpaper,\" they said. And they wrote a new rule on paper and stuck it on the wall: \"Rule #1: Every day, time with {pet_name}.\"",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: A teenager ({age_display}) with {eye_desc} eyes{glasses_desc} holding up a phone to take a photo of the pet, big warm smile, kneeling down to the pet's level, one hand holding phone as camera, genuine loving expression looking through the phone at the pet. PET: {pet_desc}, posing adorably for the camera, looking directly at the phone with bright happy eyes, sitting nicely, natural cute pose, tail wagging. ACTION: The teenager takes a loving photo of the pet with their phone, using the device to celebrate their friendship instead of ignore it, a beautiful reversal. SETTING: Living room WIDE VIEW, warm golden hour lighting, cozy home atmosphere, colorful small sticky notes on the wall behind. ATMOSPHERE: Warm transformation, technology used for love, golden light, heartwarming joy. STRICT: Only ONE teenager with phone as camera, ONE posing pet, heartwarming photo moment. Pure illustration only, zero text or lettering. {style}",
        "text_position": "split"
    },
    {
        "id": 19,
        "text_es": "Esa noche, {name} se acostó con {pet_name} acurrucado a sus pies, exactamente como cuando era pequeño. Pero ahora era diferente. Ahora {name} sabía algo que antes no entendía: que el amor de una mascota no pide nada a cambio, solo pide estar cerca. Y {name} prometió no volver a olvidarlo jamás.",
        "text_en": "That night, {name} went to bed with {pet_name} curled up at their feet, just like when they were little. But now it was different. Now {name} understood something they hadn't before: that a pet's love asks for nothing in return, it only asks to be close. And {name} promised never to forget that again.",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: A teenager ({age_display}) with {eye_desc} eyes{glasses_desc} lying in bed under a cozy blanket, peaceful happy smile, one hand reaching down to rest on the pet at their feet, eyes closing with contentment, phone on the nightstand with the pet's photo as wallpaper glowing softly. PET: {pet_desc}, curled up at the foot of the bed, head resting on the teenager's feet, deeply content peaceful expression, eyes half-closed with pure happiness, finally at peace and connected. ACTION: The teenager falls asleep peacefully with the pet curled at their feet, the phone showing the pet's photo as wallpaper, a perfect circle from the opening scene, love restored. SETTING: Teenager bedroom at night WIDE VIEW, cozy bed with warm blankets, soft nightlight glow, phone on nightstand showing pet photo wallpaper, moonlight through window, the rule note visible on wall, stars outside. ATMOSPHERE: Perfect peaceful resolution, warm golden nightlight, deep contentment, love fully realized, beautiful serene ending. STRICT: Only ONE teenager in bed, ONE pet at their feet, peaceful nighttime ending scene. {style}",
        "text_position": "split"
    }
]

CLOSING_SCENE = {
    "id": 20,
    "prompt": "Disney Pixar 3D style illustration. HUMAN: A teenager ({age_display}) with {eye_desc} eyes{glasses_desc} sitting on a grassy hilltop at golden hour, legs stretched out, leaning back on both hands, head tilted up toward the warm sky, peaceful genuine smile, casual modern clothes, relaxed and happy. PET: {pet_desc}, sitting right beside the teenager on the grass, leaning gently against the teenager's side, looking up at the golden sky too, tail resting peacefully, content calm expression. ACTION: The teenager and pet sit side by side on the hilltop watching the golden sunset together, sharing a quiet beautiful moment, their silhouettes framed by warm golden light. SETTING: Grassy hilltop at golden hour WIDE VIEW, vast warm sunset sky with soft orange and pink clouds, wildflowers scattered in the grass, a single large tree behind them with golden leaves, birds flying in the distant sky, the town visible far below. ATMOSPHERE: Golden hour warmth, deep peaceful friendship, beautiful ending moment, warm orange and gold tones, timeless bond between teenager and pet. STRICT: Only ONE teenager and ONE pet sitting together on hilltop, golden sunset scene. {style}",
    "text_position": "none"
}

FRONT_COVER = {
    "prompt": "Disney Pixar 3D style illustration. HUMAN: A single {gender_word} teenager ({age_display}) with {eye_desc} eyes{glasses_desc} sitting on the floor with knees up, arm around the pet beside them, warm genuine smile, casual modern clothes, relaxed happy posture, looking at the camera with contentment. PET: {pet_desc}, sitting close beside the teenager leaning against them, happy relaxed expression, looking at the camera too, tail resting peacefully. ACTION: The {gender_word} teenager and pet sit together ALONE in a relaxed, natural pose showing their deep bond, both looking content and connected, modern and warm composition. SETTING: Soft warm background WIDE VIEW, hints of a cozy home, warm golden backlighting creating a halo effect, simple clean composition focused on the pair. ATMOSPHERE: Warm connection, modern and genuine, golden backlight, deep friendship, centered composition for book cover. STRICT: Only ONE {gender_word} teenager and ONE pet, only the {gender_word} and the pet in the scene, centered composition for book cover. Pure illustration only, zero text or lettering. {style}"
}

BACK_COVER = {
    "prompt": "Disney Pixar 3D style illustration. SETTING: A cozy teenager's desk scene at golden hour WIDE VIEW, a phone lying on the desk with a glowing screen, a pair of headphones, scattered old printed photographs of a child and pet growing up together, a tennis ball, a soft blanket draped over the desk chair, warm sunset light streaming through a window onto the objects, a small pet bed visible in the corner, colorful small sticky notes on the wall. ATMOSPHERE: Warm nostalgic, peaceful evening, love expressed through objects, golden warm tones, story told through belongings. STRICT: Only scenery and meaningful props, zero characters. Pure illustration only, zero text or lettering. {style}"
}


def build_human_preview_prompt(human_desc: str) -> str:
    return f"Disney Pixar 3D style illustration. FULL BODY portrait of {human_desc}, wearing casual modern teenager clothes (hoodie, jeans, sneakers), standing naturally with one hand in pocket, relaxed confident smile, centered in frame, occupying 60% of frame height. NEUTRAL SOLID GRADIENT BACKGROUND (soft cream to warm beige), plain studio background. Natural friendly expression, relaxed standing pose. Clean professional animation art, clean illustration only. STRICT: Character fully clothed."


def build_human_preview_prompt_with_photo(gender_word: str, age_display: str, eye_desc: str = "", hair_desc: str = "", glasses: str = "") -> str:
    glasses_part = ", wearing glasses" if glasses == "glasses" else ", wearing sunglasses" if glasses == "sunglasses" else ""
    return f"Stylized digital illustration, semi-realistic. Character of the person from @image1 ({age_display} {gender_word}{glasses_part}), {hair_desc}, {eye_desc}, wearing casual modern teenager clothes (hoodie, jeans, sneakers). FULL BODY portrait, centered, relaxed confident expression, occupying 60% of frame height. NEUTRAL SOLID GRADIENT BACKGROUND (soft cream to warm beige). Clean illustration only."


def build_pet_preview_prompt(pet_desc: str) -> str:
    return f"Disney Pixar 3D style illustration. FULL BODY portrait of {pet_desc}, sitting or standing naturally, friendly expression, centered in frame, occupying 50% of frame height. NEUTRAL SOLID GRADIENT BACKGROUND (soft cream to warm beige), plain studio background. Warm lighting, expressive eyes. Clean professional animation art, clean illustration only."


def build_pet_preview_prompt_with_photo(pet_desc: str = "", pet_species: str = "dog") -> str:
    animal = "cat" if pet_species == "cat" else "dog"
    return f"Disney Pixar 3D style. 3D animated character of the {animal} from @image1. FULL BODY portrait, sitting or standing naturally, friendly expression, centered, occupying 50% of frame height. NEUTRAL SOLID GRADIENT BACKGROUND (soft cream to warm beige). Warm lighting. Clean animation art, clean illustration only."


def build_scene_prompt(scene: dict, human_desc: str, pet_name: str, pet_desc: str, age_display: str = "13 year old teenager", eye_desc: str = "", gender_word: str = "girl", glasses: str = "", **kwargs) -> str:
    prompt = scene.get('prompt', '')
    prompt = prompt.replace('{human_desc}', human_desc)
    prompt = prompt.replace('{pet_name}', pet_name)
    prompt = prompt.replace('{pet_desc}', pet_desc)
    prompt = prompt.replace('{age_display}', age_display)
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
