# Tú y tu Amor Peludo - Kids Story Prompts
# 19 scenes + closing + covers
# Story: "Mi Compañero Fiel" - A child's year of adventures with their beloved pet
# Ages 6-9 - School life, play, comfort, mischief, and magical everyday moments
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
#   - Keep prompts concise - FLUX 2 Dev loses focus with >300 words
#   - Style: Disney Pixar 3D everywhere, NO watercolor
#   - Human is a child (6-9 years old)
#   - Pet is a dog or cat (customized breed, color, pattern)
#   - TWO reference images per scene (human + pet)
#   - Text uses {name} for human and {pet_name} for pet
#   - STRICT always at the TOP of each prompt (FLUX weights early tokens more)
#   - NO ACTION section (was causing triple-description → duplicate characters)
#   - Each character described ONCE with a clear spatial anchor in the frame

STYLE_BASE = "Disney Pixar 3D style, soft warm golden lighting, joyful playful atmosphere, WIDE SHOT full body from head to feet, characters occupy 40% of frame, cozy home and outdoor environment visible, clean illustration only. STRICT: Children wear appropriate clothes, fully clothed always."

FURRY_LOVE_KIDS_SCENES = [
    {
        "id": 1,
        "text_es": "Cada mañana era igual: {name} intentaba dormir cinco minutos más, pero {pet_name} tenía otros planes. Una nariz fría, una lengua caliente y una cola que no paraba. \"¡Buenos días, {pet_name}!\", reía {name} entre las sábanas. Imposible resistirse.",
        "text_en": "Every morning was the same: {name} tried to sleep five more minutes, but {pet_name} had other plans. A cold nose, a warm tongue, and a tail that never stopped. \"Good morning, {pet_name}!\" {name} laughed under the covers. Impossible to resist.",
        "prompt": "Disney Pixar 3D style illustration. STRICT: exactly ONE child at LEFT side of bed, exactly ONE pet at RIGHT side of bed, no extra characters. HUMAN: A {gender_word} ({age_display}) with {eye_desc} eyes{glasses_desc}, lying in a cozy bed at LEFT side of frame, face peeking out from under the covers with a sleepy but delighted grin, arms starting to stretch out. PET: {pet_desc}, standing on the RIGHT side of the bed with front paws on the mattress edge, nose pressing into the child's cheek, tail a joyful blur, ears perked forward with bright eager eyes. TOGETHER: the pet leans across the bed edge toward the child's face, both of them at the same height in a morning greeting. SETTING: Cozy children's bedroom WIDE VIEW, morning sunlight streaming through curtains, colorful posters on walls, toys and books on shelves, a school backpack on the floor. ATMOSPHERE: Joyful wake-up energy, warm golden morning light, pure happiness. {style}",
        "text_position": "split"
    },
    {
        "id": 2,
        "text_es": "Cuando llegaba la hora de ir al colegio, {pet_name} se sentaba junto a la puerta con una mirada que partía el corazón. \"Vuelvo pronto\", prometía {name} cada vez. Y {pet_name} esperaba. Toda la mañana. Sin moverse casi nada. Con la nariz pegada a la rendija de la puerta.",
        "text_en": "When it was time to go to school, {pet_name} would sit by the door with a heartbreaking look. \"I'll be back soon,\" {name} promised every time. And {pet_name} waited. All morning long. Barely moving. Nose pressed against the gap under the door.",
        "prompt": "Disney Pixar 3D style illustration. STRICT: exactly ONE child at the door at CENTER-LEFT of frame, exactly ONE pet sitting at CENTER-RIGHT of frame, no extra characters. HUMAN: A {gender_word} ({age_display}) with {eye_desc} eyes{glasses_desc}, standing at the open front door at CENTER-LEFT of frame, school backpack on shoulders, bending slightly to look back at the pet with a loving goodbye expression, one hand still on the door handle. PET: {pet_desc}, sitting on the floor at CENTER-RIGHT of frame, directly beside the doorway, large sad eyes looking up at the child, head slightly drooping, tail low, the picture of patient loyalty. TOGETHER: child stands at the open doorway saying goodbye while the pet sits beside them looking up with devotion, the outside world visible behind the child. SETTING: Home entryway WIDE VIEW, open front door with morning sunlight beyond, coat hooks on the wall, shoes on the mat, warm interior light. ATMOSPHERE: Bittersweet parting, morning warmth, loyal devotion. {style}",
        "text_position": "split"
    },
    {
        "id": 3,
        "text_es": "El momento más esperado del día llegaba cada tarde: {name} abría la puerta y {pet_name} explotaba de alegría. Saltitos, vueltas, ladridos o maullidos, la cola en modo hélice. \"¡Estuve esperándote todo el día!\", decía ese baile sin palabras. {name} tiraba la mochila y se lanzaba a abrazarlo.",
        "text_en": "The most awaited moment of the day came every afternoon: {name} opened the door and {pet_name} exploded with joy. Little jumps, circles, barks or meows, tail in helicopter mode. \"I've been waiting for you all day!\" that wordless dance said. {name} dropped their backpack and launched into a hug.",
        "prompt": "Disney Pixar 3D style illustration. STRICT: exactly ONE child at LEFT of frame, exactly ONE pet at RIGHT of frame, no extra characters. HUMAN: A {gender_word} ({age_display}) with {eye_desc} eyes{glasses_desc}, standing just inside the front door at LEFT of frame, arms spread wide open, laughing with pure delight, school backpack slipping off one shoulder, leaning forward ready for the reunion. PET: {pet_desc}, leaping with all four paws off the ground at RIGHT of frame, directly facing the child, ears back from the excitement, mouth open in a joyful grin, mid-jump reunion leap. TOGETHER: child opens arms wide as the pet launches toward them in the entryway, just inside the front door. SETTING: Home entryway WIDE VIEW, front door wide open behind the child, afternoon sunlight streaming in, school backpack on the floor, warm cozy interior. ATMOSPHERE: Pure explosive reunion joy, warm afternoon backlight, happiness overflowing. {style}",
        "text_position": "split"
    },
    {
        "id": 4,
        "text_es": "La hora de hacer los deberes era más divertida con {pet_name} al lado. {pet_name} se echaba debajo de la mesa o junto a la silla, y cada vez que {name} suspiraba, asomaba una cabeza peluda a investigar. \"¿También tú tienes deberes de matemáticas?\", le preguntaba {name} con una sonrisa.",
        "text_en": "Homework time was more fun with {pet_name} nearby. {pet_name} would lie under the table or beside the chair, and every time {name} sighed, a fluffy head would pop up to investigate. \"Do you have math homework too?\" {name} would ask with a smile.",
        "prompt": "Disney Pixar 3D style illustration. STRICT: exactly ONE child at the desk at CENTER of frame, exactly ONE pet beneath or beside the chair at BOTTOM of frame, no extra characters. HUMAN: A {gender_word} ({age_display}) with {eye_desc} eyes{glasses_desc}, seated at a desk at CENTER of frame, leaning forward over an open notebook with pencil in hand, looking down at the pet with a grin, one eyebrow raised in a pretend-serious question. PET: {pet_desc}, lying on the floor directly below and beside the desk chair at BOTTOM-CENTER of frame, chin resting on front paws, looking up at the child with curious attentive eyes, one ear perked. TOGETHER: child looks down from the desk while the pet looks up from the floor beneath, their eyes meeting in a shared quiet moment. SETTING: Children's bedroom study corner WIDE VIEW, desk with open books and notebooks, pencil case, warm desk lamp light, afternoon sun through window behind. ATMOSPHERE: Cozy study companionship, warm lamplight, quiet focused comfort. {style}",
        "text_position": "split"
    },
    {
        "id": 5,
        "text_es": "Un día, {name} no encontraba el lápiz por ningún lado. Buscó en el estuche, en la mochila, debajo de la mesa... Hasta que vio a {pet_name} en el rincón, masticando algo con mucha satisfacción. Era el lápiz nuevo. El de los colores bonitos. {name} puso los ojos en blanco... y soltó una carcajada.",
        "text_en": "One day, {name} couldn't find the pencil anywhere. Looked in the pencil case, in the backpack, under the table... Until they spotted {pet_name} in the corner, chewing something very happily. It was the new pencil. The one with the pretty colors. {name} rolled their eyes... and burst out laughing.",
        "prompt": "Disney Pixar 3D style illustration. STRICT: exactly ONE child standing at CENTER-LEFT of frame, exactly ONE pet sitting at RIGHT of frame, no extra characters. HUMAN: A {gender_word} ({age_display}) with {eye_desc} eyes{glasses_desc}, standing at CENTER-LEFT of frame, hands on hips with an exasperated but amused expression, eyes wide at the discovery, mouth curved into a helpless laugh. PET: {pet_desc}, sitting in the corner at RIGHT of frame, a chewed colorful pencil clearly visible between its front paws, gazing up at the child with the most innocent angelic expression, tail wagging slowly. TOGETHER: child stands facing the pet from a few feet away, caught between pretend frustration and real amusement. SETTING: Children's bedroom WIDE VIEW, desk with open books behind the child, scattered pencil case contents, warm afternoon light, cozy room. ATMOSPHERE: Comedic mischief, warm laughing energy, pure innocent trouble. {style}",
        "text_position": "split"
    },
    {
        "id": 6,
        "text_es": "En el jardín, {name} y {pet_name} jugaban hasta quedarse sin aliento. {name} lanzaba la pelota una y otra vez, y {pet_name} corría como si cada lanzamiento fuera el primero. A veces {name} fingía lanzar y {pet_name} salía disparado... y luego volvía mirando a {name} con cara de \"eso no cuenta\".",
        "text_en": "In the garden, {name} and {pet_name} played until they were out of breath. {name} threw the ball again and again, and {pet_name} ran as if each throw were the first. Sometimes {name} pretended to throw and {pet_name} shot off... then returned giving {name} a \"that doesn't count\" look.",
        "prompt": "Disney Pixar 3D style illustration. STRICT: exactly ONE child at LEFT of frame mid-throw, exactly ONE pet at RIGHT of frame mid-run, no extra characters. HUMAN: A {gender_word} ({age_display}) with {eye_desc} eyes{glasses_desc}, standing at LEFT of frame with arm extended in a throwing motion, laughing with eyes crinkled, one foot forward in the follow-through of a throw, casual play clothes. PET: {pet_desc}, at RIGHT of frame running at full speed away from the child, body stretched long in a galloping stride, ears back from speed, tail streaming, completely focused on chasing. TOGETHER: child throws from the LEFT while the pet races to the RIGHT, a colorful ball visible mid-arc between them. SETTING: Home garden WIDE VIEW, green lawn, colorful flowers along the fence, blue sky with a few clouds, warm afternoon sunlight casting short happy shadows. ATMOSPHERE: Energetic outdoor joy, bright golden afternoon light, carefree play. {style}",
        "text_position": "split"
    },
    {
        "id": 7,
        "text_es": "Los días de lluvia eran para construir fortalezas. {name} juntaba todos los cojines del sofá, las mantas más suaves y las sábanas más grandes. {pet_name} se metía dentro antes de que estuviera terminada y se negaba a salir. \"Bien\", decía {name} acomodándose a su lado. \"Tú eres el guardián de la fortaleza.\"",
        "text_en": "Rainy days were for building fortresses. {name} gathered all the sofa cushions, the softest blankets, and the biggest sheets. {pet_name} crawled inside before it was even finished and refused to come out. \"Fine,\" said {name} settling in beside them. \"You're the fortress guardian.\"",
        "prompt": "Disney Pixar 3D style illustration. STRICT: exactly ONE child at LEFT inside the fort, exactly ONE pet at RIGHT inside the fort, no extra characters. HUMAN: A {gender_word} ({age_display}) with {eye_desc} eyes{glasses_desc}, sitting cross-legged at LEFT inside a cozy blanket fort, holding a small flashlight that illuminates the interior, smiling with cozy contentment, a picture book open on the floor. PET: {pet_desc}, sprawled at RIGHT inside the same blanket fort, head up and alert like a true guardian, paws stretched forward, tail resting, looking out the blanket entrance with dignified importance. TOGETHER: child and pet share the snug interior of the blanket fort, the flashlight casting a warm golden glow on both. SETTING: Living room floor WIDE VIEW, the blanket fort constructed from sofa cushions and draped sheets, a flashlight glow within, rain visible through the window outside, grey sky beyond, warm and dry inside. ATMOSPHERE: Cozy rainy-day magic, warm golden flashlight glow vs grey rain outside, snug safe happiness. {style}",
        "text_position": "split"
    },
    {
        "id": 8,
        "text_es": "Cuando el trueno retumbó con fuerza, fue {pet_name} quien se asustó primero. Se metió debajo de la cama, temblando. {name} se tumbó en el suelo y asomó la cabeza. \"Oye, no pasa nada. Estoy aquí\", susurró. Y se quedó ahí tumbado, acariciando a {pet_name} hasta que el miedo se fue.",
        "text_en": "When the thunder rumbled loud, {pet_name} was the first to get scared. They crawled under the bed, trembling. {name} lay down on the floor and peeked under. \"Hey, it's okay. I'm here,\" they whispered. And they stayed there on the floor, stroking {pet_name} until the fear went away.",
        "prompt": "Disney Pixar 3D style illustration. STRICT: exactly ONE child lying on the floor at TOP of frame, exactly ONE pet under the bed at BOTTOM of frame, no extra characters. HUMAN: A {gender_word} ({age_display}) with {eye_desc} eyes{glasses_desc}, lying flat on the bedroom floor at TOP-CENTER of frame, head and one arm reaching under the bed, face showing gentle reassurance and love, speaking softly to the pet below. PET: {pet_desc}, tucked under the bed frame at BOTTOM of frame in the space below, body pressed low, trembling slightly, big worried eyes looking up at the child's hand reaching toward them, just beginning to calm. TOGETHER: child reaches one comforting arm under the bed to gently stroke the scared pet hiding below, their eyes meeting under the bed frame. SETTING: Children's bedroom floor level WIDE VIEW, under-bed space visible, lightning flash through curtains illuminating the room in blue-white, cozy room darkened by the storm. ATMOSPHERE: Protective tenderness, storm drama outside vs quiet comfort inside, soft emotional warmth. {style}",
        "text_position": "split"
    },
    {
        "id": 9,
        "text_es": "{name} había decidido enseñarle un truco nuevo a {pet_name}. Una galleta en la mano, mucha paciencia y una consigna muy seria: \"Dame la pata.\" {pet_name} lo miró, bostezó, se rascó la oreja... y luego, cuando {name} casi se había rendido, levantó la pata. ¡LO HABÍA CONSEGUIDO!",
        "text_en": "{name} had decided to teach {pet_name} a new trick. A treat in hand, lots of patience, and one very serious command: \"Give me your paw.\" {pet_name} looked at them, yawned, scratched their ear... and then, just as {name} was almost giving up, raised their paw. THEY HAD DONE IT!",
        "prompt": "Disney Pixar 3D style illustration. STRICT: exactly ONE child kneeling at LEFT of frame, exactly ONE pet sitting at RIGHT of frame, no extra characters. HUMAN: A {gender_word} ({age_display}) with {eye_desc} eyes{glasses_desc}, kneeling on the floor at LEFT of frame, one hand extended palm-up in a 'give paw' gesture, face lit up with the biggest triumphant grin, eyes wide with excited disbelief. PET: {pet_desc}, sitting upright at RIGHT of frame directly facing the child, one front paw raised and resting in the child's open palm, looking up with a pleased self-satisfied expression, tail wagging. TOGETHER: child's outstretched hand and pet's raised paw connect at CENTER frame, the long-awaited trick finally mastered. SETTING: Living room floor WIDE VIEW, a small treat bag on the floor beside the child, warm afternoon light, cozy rug on the floor, playful home atmosphere. ATMOSPHERE: Triumphant breakthrough joy, warm golden afternoon light, pure shared pride. {style}",
        "text_position": "split"
    },
    {
        "id": 10,
        "text_es": "Un día, {name} llegó del colegio con los hombros caídos. No quería merendar, no quería jugar, no quería hablar. Se tumbó en el sofá y miró el techo. {pet_name} lo vio. Sin hacer ruido, se acercó, se subió al sofá y se acurrucó justo encima de {name}. Calentito. Pesadito. Perfecto.",
        "text_en": "One day, {name} came home from school with slumped shoulders. They didn't want a snack, didn't want to play, didn't want to talk. They lay on the sofa and stared at the ceiling. {pet_name} noticed. Without a sound, they came over, climbed onto the sofa, and curled up right on top of {name}. Warm. Heavy. Perfect.",
        "prompt": "Disney Pixar 3D style illustration. STRICT: exactly ONE child lying on the sofa at CENTER of frame, exactly ONE pet on top of the child also at CENTER of frame, no extra characters. HUMAN: A {gender_word} ({age_display}) with {eye_desc} eyes{glasses_desc}, lying on a sofa at CENTER of frame on their back, staring at the ceiling with a sad tired expression, school clothes still on, arms limp at their sides. PET: {pet_desc}, lying directly on top of the child on the sofa at CENTER of frame, head resting on the child's chest, eyes looking up at the child's face with deep empathy, heavy warm body like a living blanket. TOGETHER: pet lies fully on top of the child on the sofa, a warm weight of comfort and company during a hard moment. SETTING: Cozy living room sofa WIDE VIEW, soft afternoon light through window, school backpack dropped on the floor, quiet empty house. ATMOSPHERE: Quiet emotional comfort, gentle warm light, unspoken loyalty, soft healing tenderness. {style}",
        "text_position": "split"
    },
    {
        "id": 11,
        "text_es": "Llegó el día del baño de {pet_name}. {name} se armó de valor, llenó la bañera y llamó a {pet_name} con su voz más dulce. Lo que siguió fue épico: agua por todas partes, jabón en los ojos de {name}, {pet_name} sacudiéndose en el momento más inoportuno. Pero al final, {pet_name} quedó esponjoso y oloroso... y {name} acabó más mojado que la mascota.",
        "text_en": "Bath day for {pet_name} arrived. {name} steeled themselves, filled the tub, and called {pet_name} in their sweetest voice. What followed was epic: water everywhere, soap in {name}'s eyes, {pet_name} shaking at the worst possible moment. But in the end, {pet_name} came out fluffy and fragrant... and {name} ended up wetter than the pet.",
        "prompt": "Disney Pixar 3D style illustration. STRICT: exactly ONE child kneeling beside the tub at LEFT of frame, exactly ONE pet in the tub at RIGHT of frame, no extra characters. HUMAN: A {gender_word} ({age_display}) with {eye_desc} eyes{glasses_desc}, kneeling on the bathroom floor at LEFT of frame beside a small bathtub, eyes squinted shut against a massive water splash, arms raised in defense, soaked from head to toe, laughing despite the chaos. PET: {pet_desc}, standing in the small bathtub at RIGHT of frame, ears flat, looking betrayed and dignified despite being covered in bubbles, mid-shake sending a wall of water toward the child. TOGETHER: pet shakes a huge spray of water directly at the child who kneels helplessly laughing beside the tub. SETTING: Bright bathroom WIDE VIEW, small bathtub with bubbles overflowing, water droplets suspended in the air catching the bathroom light, towels knocked off the rack, rubber duck floating nearby. ATMOSPHERE: Hilarious wet chaos, bright bathroom light catching every water droplet, pure comedy. {style}",
        "text_position": "split"
    },
    {
        "id": 12,
        "text_es": "Una tarde {name} se quedó dormido en el sofá leyendo un cuento. {pet_name} olfateó el libro, olió a {name}, dio tres vueltas en el cojín de al lado y se acurrucó pegadito. Cuando {name} despertó, el libro había caído al suelo y {pet_name} roncaba suavecito. {name} decidió no moverse para no despertarlo.",
        "text_en": "One afternoon {name} fell asleep on the sofa reading a story. {pet_name} sniffed the book, sniffed {name}, circled three times on the next cushion, and curled up close. When {name} woke up, the book had fallen to the floor and {pet_name} was snoring softly. {name} decided not to move so as not to wake them.",
        "prompt": "Disney Pixar 3D style illustration. STRICT: exactly ONE child on the sofa at LEFT of frame, exactly ONE pet curled beside the child at RIGHT of frame, no extra characters. HUMAN: A {gender_word} ({age_display}) with {eye_desc} eyes{glasses_desc}, sitting on the sofa at LEFT of frame, just woken up with sleepy soft eyes, hair slightly mussed, a half-smile as they look at the sleeping pet beside them, book fallen open on the floor below. PET: {pet_desc}, curled into a tight sleeping ball on the sofa RIGHT beside the child at RIGHT of frame, eyes closed in deep peaceful sleep, chest rising and falling, fully relaxed. TOGETHER: child sits gently awake watching the sleeping pet right beside them on the same sofa, reluctant to move. SETTING: Cozy living room sofa WIDE VIEW, golden late-afternoon light making long soft shadows, an open picture book on the floor, a soft blanket half-draped over both, warm lamplight beginning to glow. ATMOSPHERE: Drowsy golden-hour coziness, warm amber light, perfect peaceful stillness. {style}",
        "text_position": "split"
    },
    {
        "id": 13,
        "text_es": "{name} tuvo una gran idea: hacerle una sesión de fotos a {pet_name}. Le puso una diadema de flores, acomodó unos cojines de fondo y dijo \"¡Sonríe!\" en voz muy seria. {pet_name} aguantó exactamente tres segundos antes de escapar. Pero en esos tres segundos, {name} captó la foto más graciosa del mundo.",
        "text_en": "{name} had a great idea: give {pet_name} a photo session. They put a flower headband on them, arranged some cushions as a backdrop, and said \"Smile!\" in a very serious voice. {pet_name} held still for exactly three seconds before escaping. But in those three seconds, {name} captured the funniest photo in the world.",
        "prompt": "Disney Pixar 3D style illustration. STRICT: exactly ONE child at LEFT of frame as photographer, exactly ONE pet at RIGHT of frame as reluctant subject, no extra characters. HUMAN: A {gender_word} ({age_display}) with {eye_desc} eyes{glasses_desc}, crouching at LEFT of frame holding a phone or small camera up to their face, one eye shut and one eye at the viewfinder, grinning behind the device, clearly delighted by the result. PET: {pet_desc}, sitting at RIGHT of frame on an arrangement of colorful cushions, wearing a small flower crown at a slightly crooked angle, giving the camera the most long-suffering dignified unimpressed stare, sitting still in reluctant compliance. TOGETHER: child photographs the pet from a few feet away, the pet posing reluctantly on the improvised cushion studio backdrop. SETTING: Living room WIDE VIEW, colorful cushions arranged as backdrop, warm home light, a few fallen flower petals on the cushions, cheerful and creative mess. ATMOSPHERE: Comedy and creativity, warm home light, silly sweet fun. {style}",
        "text_position": "split"
    },
    {
        "id": 14,
        "text_es": "Un día {pet_name} no tenía energía. No quería jugar, no quería comer, no hacía ningún ruido. {name} le puso la mano en la frente (aunque no supiese muy bien cómo hacerlo) y declaró: \"Estás enfermo. Me quedo contigo.\" Canceló los planes con los amigos y pasó todo el día al lado de {pet_name}.",
        "text_en": "One day {pet_name} had no energy. Didn't want to play, didn't want to eat, made no noise at all. {name} put a hand on their forehead (even though they weren't sure exactly how to do it) and declared: \"You're sick. I'm staying with you.\" They cancelled plans with friends and spent the whole day by {pet_name}'s side.",
        "prompt": "Disney Pixar 3D style illustration. STRICT: exactly ONE child sitting at LEFT of frame on the floor, exactly ONE pet lying in a bed at RIGHT of frame, no extra characters. HUMAN: A {gender_word} ({age_display}) with {eye_desc} eyes{glasses_desc}, sitting cross-legged on the floor at LEFT of frame beside a small pet bed, leaning forward with one hand gently resting on the pet's head, face showing careful worried concentration, fully devoted expression. PET: {pet_desc}, lying in a cozy small pet bed at RIGHT of frame, body low and tired, eyes half-open and glassy, looking up at the child's hand with a soft grateful expression, clearly unwell but feeling loved. TOGETHER: child sits close on the floor beside the pet's bed, hand on the pet's head in a gentle temperature-check of love and worry. SETTING: Living room corner WIDE VIEW, soft afternoon light, a small bowl of water nearby, a children's medical kit on the floor, quiet and calm room. ATMOSPHERE: Tender worry, quiet devoted care, soft muted warm light, emotional depth. {style}",
        "text_position": "split"
    },
    {
        "id": 15,
        "text_es": "Cuando {pet_name} se recuperó, fue una fiesta. {name} sacó las galletas especiales, le cantó una canción inventada y bailó con {pet_name} por toda la sala. Los vecinos del piso de abajo probablemente escucharon los saltos, pero no importaba. {pet_name} estaba bien. Eso era lo único que importaba.",
        "text_en": "When {pet_name} recovered, it was a celebration. {name} got out the special treats, sang an made-up song, and danced with {pet_name} all around the living room. The downstairs neighbors probably heard the jumping, but it didn't matter. {pet_name} was okay. That was the only thing that mattered.",
        "prompt": "Disney Pixar 3D style illustration. STRICT: exactly ONE child at LEFT of frame dancing, exactly ONE pet at RIGHT of frame jumping, no extra characters. HUMAN: A {gender_word} ({age_display}) with {eye_desc} eyes{glasses_desc}, at LEFT of frame in the middle of an exuberant dance, arms flung wide, legs mid-skip, laughing with pure relief and happiness, eyes bright and joyful. PET: {pet_desc}, at RIGHT of frame leaping and bounding with full healthy energy, all four paws off the ground, mouth open in a joyful grin, ears flying, completely recovered and bursting with life. TOGETHER: child and pet celebrate and dance together across the living room, both in joyful mid-motion, a bag of treats visible on the coffee table behind them. SETTING: Living room WIDE VIEW, furniture pushed to the sides for the dance, warm afternoon sunlight flooding in, a small treat bag on the table, cozy home atmosphere. ATMOSPHERE: Explosive relief and celebration, bright warm sunshine, pure unbridled happiness. {style}",
        "text_position": "split"
    },
    {
        "id": 16,
        "text_es": "Una noche, {name} arrastró una manta al jardín, tumbó a {pet_name} a su lado y los dos miraron el cielo. \"Esa es la Osa Mayor\", explicó {name} señalando las estrellas. {pet_name} miraba el dedo de {name}, no las estrellas. Pero no importaba. Había noches perfectas que no necesitaban que nadie mirara lo correcto.",
        "text_en": "One night, {name} dragged a blanket to the garden, lay {pet_name} down beside them, and the two looked at the sky. \"That's the Big Dipper,\" {name} explained, pointing at the stars. {pet_name} watched {name}'s finger, not the stars. But it didn't matter. There were perfect nights that didn't need anyone to look at the right thing.",
        "prompt": "Disney Pixar 3D style illustration. STRICT: exactly ONE child lying on a blanket at LEFT of frame, exactly ONE pet lying on the blanket at RIGHT of frame, no extra characters. HUMAN: A {gender_word} ({age_display}) with {eye_desc} eyes{glasses_desc}, lying on a soft garden blanket at LEFT of frame, one arm outstretched pointing up at the night sky, face tilted upward, expression of wonder and contentment, relaxed and peaceful. PET: {pet_desc}, lying on the same blanket at RIGHT of frame, head turned sideways looking at the child's pointing finger with curious attentive eyes, rather than the sky, body relaxed and comfortable pressed against the child. TOGETHER: child and pet lie side by side on a garden blanket under the stars, the child pointing at the night sky while the pet pays attention only to their person. SETTING: Home garden at night WIDE VIEW, dark garden around them, a vast star-filled sky above with the Milky Way visible, soft blanket on the grass, warm house windows glowing behind them. ATMOSPHERE: Magical peaceful night, deep blue-silver starlight, quiet wonder, perfect childhood moment. {style}",
        "text_position": "split"
    },
    {
        "id": 17,
        "text_es": "Un sábado {name} organizó un pequeño concurso de talentos con los amigos del barrio. Y {pet_name} fue la estrella. Cuando {pet_name} hizo el truco de la pata, todos aplaudieron. Cuando persiguió su propia cola tres veces seguidas, todos se doblaron de risa. {name} miraba desde un lado, orgulloso/a como nunca.",
        "text_en": "One Saturday {name} organized a little talent show with neighborhood friends. And {pet_name} was the star. When {pet_name} did the paw trick, everyone clapped. When they chased their own tail three times in a row, everyone doubled over with laughter. {name} watched from the side, prouder than ever.",
        "prompt": "Disney Pixar 3D style illustration. STRICT: exactly ONE child at LEFT of frame as proud host, exactly ONE pet at CENTER of frame performing, no extra characters. HUMAN: A {gender_word} ({age_display}) with {eye_desc} eyes{glasses_desc}, standing at LEFT of frame slightly to the side, arms crossed with a huge beaming proud smile, watching the pet perform, eyes crinkled with delight and pride. PET: {pet_desc}, at CENTER of frame in a perfect spotlight moment, sitting upright on hind legs with one paw raised in the learned trick, chest out, expression theatrical and magnificent, as if performing for an audience of thousands. TOGETHER: child stands to the side beaming with pride as the pet performs their best trick in the imaginary spotlight between them. SETTING: Home garden or yard WIDE VIEW, a sunny Saturday afternoon, a simple 'stage' area of flat grass, warm golden afternoon light creating a natural spotlight effect, flowers and garden behind. ATMOSPHERE: Showtime pride and humor, warm golden spotlight light, pure joyful pride and comedy. {style}",
        "text_position": "split"
    },
    {
        "id": 18,
        "text_es": "Llegó el día más especial del año: el cumpleaños de {name}. Había globos, tarta y amigos. Pero lo mejor llegó cuando {pet_name} metió la cara directamente en la tarta. Hubo silencio... y luego risas para siempre. {name} limpió el hocico de {pet_name} con una servilleta y le dio el primer trozo. \"El mejor cumpleaños de mi vida\", dijo de verdad.",
        "text_en": "The most special day of the year arrived: {name}'s birthday. There were balloons, cake, and friends. But the best part came when {pet_name} stuck their face directly into the cake. There was a moment of silence... then laughter forever. {name} wiped {pet_name}'s nose with a napkin and gave them the first slice. \"The best birthday of my life,\" they said sincerely.",
        "prompt": "Disney Pixar 3D style illustration. STRICT: exactly ONE child at LEFT of frame, exactly ONE pet at RIGHT of frame, no extra characters, pure illustration only, zero text. HUMAN: A {gender_word} ({age_display}) with {eye_desc} eyes{glasses_desc}, sitting at a birthday table at LEFT of frame, laughing so hard their eyes are closed, holding a napkin, birthday hat slightly askew, pure uncontrollable birthday joy. PET: {pet_desc}, sitting on the floor at RIGHT of frame beside the table, face completely covered in birthday cake frosting, looking up with big surprised innocent eyes and frosting on their nose, tail wagging despite everything. TOGETHER: child collapses laughing at the table while the pet looks up frosting-faced from below, connected by this perfectly chaotic birthday moment. SETTING: Festive birthday table WIDE VIEW, colorful balloons in the background, a partially destroyed birthday cake on the table, confetti, warm celebration lighting. ATMOSPHERE: Joyful birthday chaos, warm festive glow, laughter and love, unforgettable celebration. {style}",
        "text_position": "split"
    },
    {
        "id": 19,
        "text_es": "Esa noche, cuando todos se habían ido, {name} se sentó en el suelo con {pet_name} y le habló en voz baja. \"Este fue el mejor año de mi vida. Y tú estuviste en todas las partes buenas.\" {pet_name} apoyó la cabeza en las piernas de {name} y suspiró hondo. Como si lo entendiese todo. Porque probablemente lo entendía.",
        "text_en": "That evening, when everyone had gone, {name} sat on the floor with {pet_name} and spoke in a soft voice. \"This was the best year of my life. And you were in every good part of it.\" {pet_name} rested their head on {name}'s legs and sighed deeply. As if they understood everything. Because they probably did.",
        "prompt": "Disney Pixar 3D style illustration. STRICT: exactly ONE child sitting on the floor at CENTER of frame, exactly ONE pet with head on the child's lap also at CENTER of frame, no extra characters. HUMAN: A {gender_word} ({age_display}) with {eye_desc} eyes{glasses_desc}, sitting cross-legged on the floor at CENTER of frame, back against the sofa, speaking softly to the pet, one hand resting gently on the pet's head, peaceful grateful smile, eyes soft and warm. PET: {pet_desc}, lying on the floor at CENTER of frame with head resting completely on the child's crossed legs, eyes looking up at the child's face with complete trust and deep understanding, a long slow blink, perfectly content. TOGETHER: child sits with the pet's head resting in their lap, both of them in the quiet golden after-party stillness, perfectly connected. SETTING: Living room floor WIDE VIEW, some balloon strings and confetti still visible, warm amber lamplight, quiet evening atmosphere, the world outside dark and still. ATMOSPHERE: Quiet profound tenderness, warm golden lamplight, deep mutual understanding, the best kind of stillness. {style}",
        "text_position": "split"
    }
]

CLOSING_SCENE = {
    "id": 20,
    "prompt": "Disney Pixar 3D style illustration. STRICT: exactly ONE child asleep in bed at CENTER-TOP of frame, exactly ONE pet asleep at the foot of the bed at CENTER-BOTTOM of frame, no extra characters. HUMAN: A {gender_word} ({age_display}) with {eye_desc} eyes{glasses_desc}, sleeping deeply in a cozy bed at CENTER of frame under a star-patterned blanket, peaceful angelic expression, one arm hanging loosely over the side. PET: {pet_desc}, curled up peacefully at the foot of the same bed at BOTTOM of frame, chin resting on the child's ankles, eyes closed in deep contented sleep, tail curled around their body. TOGETHER: child sleeps in bed while the pet rests faithfully at their feet, both deeply asleep and connected, a year of memories on the walls around them. SETTING: Cozy bedroom at night WIDE VIEW, warm nightlight glow, stars visible through the window, colorful drawings and photos pinned to the wall showing moments of the year together, peaceful darkness. ATMOSPHERE: Perfect serene ending, warm nightlight glow, eternal friendship, protective love made visible in sleep. {style}",
    "text_position": "none"
}

FRONT_COVER = {
    "prompt": "Disney Pixar 3D style illustration. STRICT: exactly ONE {gender_word} child and exactly ONE pet together at CENTER of frame, no other characters, pure illustration only, zero text. HUMAN: A {gender_word} with {eye_desc} eyes, full appearance matching @image1 exactly, kneeling at CENTER-LEFT of frame with both arms wrapped around the pet in a warm hug, eyes closed with a smile of pure happiness, casual play clothes. PET: {pet_desc}, at CENTER-RIGHT of frame, leaning fully into the hug with eyes closed too, tail wagging, ears back from the warmth of the embrace, both of them captured in a perfect moment of best-friend love. TOGETHER: child and pet share a heartfelt hug at center frame, both eyes closed, both perfectly happy, in a simple joyful embrace. SETTING: Beautiful sunny garden WIDE VIEW, soft golden afternoon light creating a warm glow around them, green grass, a few wildflowers, warm bokeh background, clean centered book-cover composition. ATMOSPHERE: Pure warm love, golden backlight halo effect, timeless friendship, centered book cover quality. {style}"
}

BACK_COVER = {
    "prompt": "Disney Pixar 3D style illustration. STRICT: zero characters, only objects and scenery. SETTING: A cozy children's bedroom corner WIDE VIEW, a small pet bed on the floor with a few scattered toys, a child's desk with an open notebook and colored pencils, a framed photo on the desk of a child and a pet together, a colorful ball and a chewed pencil on the rug, star-patterned pajamas draped over the desk chair, a small flashlight beside a children's book, warm golden lamplight illuminating the scene, a window with night sky and stars outside. ATMOSPHERE: Warm nostalgic, peaceful evening, a childhood story told entirely through beloved objects, golden warm tones, love made visible in everyday things. Pure illustration only, zero text or lettering. {style}"
}


def build_human_preview_prompt(human_desc: str, **kwargs) -> str:
    return (
        f"Disney Pixar 3D style illustration. FULL BODY portrait of {human_desc}, "
        f"wearing casual play clothes (t-shirt, jeans or shorts, sneakers), standing naturally "
        f"with a big friendly smile, centered in frame, occupying 60% of frame height. "
        f"NEUTRAL SOLID GRADIENT BACKGROUND (soft cream to warm beige), plain studio background. "
        f"Natural happy expression, relaxed standing pose. "
        f"Clean professional animation art, clean illustration only. STRICT: Character fully clothed."
    )


def build_human_preview_prompt_with_photo(gender_word: str, age_display: str, eye_desc: str = "", hair_desc: str = "", glasses: str = "", facial_hair: str = "", skin_tone: str = "") -> str:
    skin_strict = f"Maintain {skin_tone} complexion — do not lighten the skin tone. " if skin_tone else ""
    eye_part = f"{eye_desc} eyes, " if eye_desc else ""
    return (
        f"Disney Pixar 3D style illustration. 3D animated {gender_word} with face shape, skin complexion, hair amount and color, "
        f"and {eye_part}all matching @image1 exactly — do not invent or change any physical feature. "
        f"FULL BODY portrait, centered, warm happy expression. "
        f"NEUTRAL SOLID GRADIENT BACKGROUND (soft cream to warm beige). "
        f"{skin_strict}"
        f"Clean illustration only."
    )


def build_pet_preview_prompt(pet_desc: str) -> str:
    return (
        f"Disney Pixar 3D style illustration. FULL BODY portrait of {pet_desc}, "
        f"sitting or standing naturally, friendly expression, centered in frame, occupying 50% of frame height. "
        f"NEUTRAL SOLID GRADIENT BACKGROUND (soft cream to warm beige), plain studio background. "
        f"Warm lighting, expressive eyes. Clean professional animation art, clean illustration only."
    )


def build_pet_preview_prompt_with_photo(pet_desc: str = "", pet_species: str = "dog", pet_size: str = "medium") -> str:
    animal = "cat" if pet_species == "cat" else "dog"
    size_desc_map = {
        "small":  "a small-sized animal — compact body, fits fully in frame with space around it",
        "medium": "a medium-sized animal — full body fits naturally and comfortably in frame",
        "large":  "a large-sized animal — big imposing body fills the frame, broad and tall",
    }
    size_desc = size_desc_map.get(pet_size, size_desc_map["medium"])
    desc_hint = f" ({pet_desc})" if pet_desc else ""
    return (
        f"High-quality 3D animated children's book illustration. 3D animated character of the {animal} from @image1{desc_hint}. "
        f"FULL BODY portrait, sitting or standing naturally, friendly expression, centered. {size_desc}. "
        f"NEUTRAL SOLID GRADIENT BACKGROUND (soft cream to warm beige). Warm lighting. Clean animation art, clean illustration only."
    )


def build_scene_prompt(scene: dict, human_desc: str, pet_name: str, pet_desc: str, age_display: str = "7 year old child", eye_desc: str = "", gender_word: str = "girl", glasses: str = "", **kwargs) -> str:
    scene_id = scene.get('id', 0)
    pet_species = kwargs.get('pet_species', 'dog')
    animal_word = "cat" if pet_species == "cat" else "dog"

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


def get_all_scene_prompts(human_desc: str, pet_name: str, pet_desc: str, age_display: str = "7 year old child", eye_desc: str = "", gender_word: str = "girl") -> list:
    prompts = []
    for scene in FURRY_LOVE_KIDS_SCENES:
        prompts.append(build_scene_prompt(scene, human_desc, pet_name, pet_desc, age_display, eye_desc, gender_word))
    prompts.append(build_scene_prompt(CLOSING_SCENE, human_desc, pet_name, pet_desc, age_display, eye_desc, gender_word))
    return prompts


def get_all_story_texts(child_name: str, pet_name: str, language: str = 'es') -> list:
    texts = []
    for scene in FURRY_LOVE_KIDS_SCENES:
        texts.append({
            'id': scene['id'],
            'text': build_story_text(scene, child_name, pet_name, language),
            'text_position': scene.get('text_position', 'split')
        })
    return texts


def get_cover_prompts(human_desc: str, pet_name: str, pet_desc: str, age_display: str = "7 year old child", eye_desc: str = "", gender_word: str = "girl", glasses: str = "") -> dict:
    return {
        'front': build_scene_prompt(FRONT_COVER, human_desc, pet_name, pet_desc, age_display, eye_desc, gender_word, glasses=glasses),
        'back': build_scene_prompt(BACK_COVER, human_desc, pet_name, pet_desc, age_display, eye_desc, gender_word, glasses=glasses)
    }
