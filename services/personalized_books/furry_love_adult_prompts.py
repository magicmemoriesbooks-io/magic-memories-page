# Tú y tu Amor Peludo - Adult Mountain Adventure Story Prompts
# 19 scenes + closing + covers
# Story: "Nuestra Gran Aventura" - A mountain excursion with their dog
# Ages 18-75 - Nature, hiking, camping, bonding with pet
#
# REFERENCE STRATEGY (Jun 2026 — reference-first, matching furry_love_prompts.py):
#   @image1 = human_preview_path  (Disney Pixar avatar of the adult)
#   @image2 = pet_preview_path    (Disney Pixar avatar of the pet)
#   Prompts trust BOTH references for ALL physical appearance.
#   Character trait text (hair, eyes, skin) removed from scene prompts — references handle it.
#   Only describe: CAST identity, adult age hint, ACTION, SETTING, ATMOSPHERE.
#
# PROMPT RULES:
#   - guidance_scale=3.5, num_inference_steps=28, aspect_ratio=3:4
#   - Positive language only — no "NO X" or "NEVER X" (FLUX reads negations as presence)
#   - Character separation via positive body description:
#       adult  → "fully human body, smooth skin, two arms, two legs, adult proportions"
#       pet    → "animal body, four paws, fur coat"
#   - {age_display} included as hint — reference handles visual age fidelity
#   - {pet_desc} injected in CAST line to reinforce breed/color (by build_scene_prompt)
#   - {pet_name} used in SCENE for action description
#   - {gender_word} used in CAST line

STYLE_BASE = "Disney Pixar 3D style, soft warm lighting, adventurous cinematic atmosphere, WIDE SHOT full body from head to feet, characters occupy 40% of frame, mountain and nature environment visible, clean illustration only. STRICT: All adults wear appropriate outdoor hiking clothes, fully clothed always."

FURRY_LOVE_ADULT_SCENES = [
    {
        "id": 1,
        "text_es": "{name} abrió el maletero del carro y empezó a cargar la mochila, la tienda de campaña y las botas de montaña. {pet_name} observaba cada movimiento con las orejas levantadas, moviendo la cola sin parar.",
        "text_en": "{name} opened the trunk and started loading the backpack, the tent, and the hiking boots. {pet_name} watched every move with perked ears, tail wagging nonstop.",
        "prompt": "Disney Pixar 3D style illustration. CAST: @image1 = {gender_word} adult ({age_display}), fully human body, smooth skin, two arms, two legs, adult proportions — match reference exactly. @image2 = {pet_name} ({pet_desc}): animal body, four paws, fur coat — match reference exactly. Two distinct separate beings. Exactly ONE adult + ONE pet. SCENE: @image1 stands at the open trunk of an SUV in a driveway, loading hiking gear (backpack, rolled tent, hiking boots) with an excited expression, wearing casual outdoor clothes. @image2 stands beside the car on all four paws, ears perked up, tail wagging, watching every move with eager anticipation. SETTING: Residential driveway WIDE VIEW, SUV with open trunk filled with camping gear, morning sunlight, clear blue sky, suburban neighborhood with trees. ATMOSPHERE: Excitement and anticipation, fresh morning light, the thrill of adventure about to begin. STRICT: @image1 is a fully human adult with two legs. @image2 is an animal standing on its own four paws. {style}",
        "text_position": "split"
    },
    {
        "id": 2,
        "text_es": "\"¡Vamos, {pet_name}!\" dijo {name} abriendo la puerta trasera. {pet_name} saltó al asiento de un brinco y se acomodó junto a la ventanilla. Miraba por el cristal con los ojos bien abiertos mientras el paisaje cambiaba de ciudad a bosque. Cada árbol, cada curva, era una nueva aventura.",
        "text_en": "\"Let's go, {pet_name}!\" said {name}, opening the back door. {pet_name} jumped onto the seat in one leap and settled by the window. They watched through the glass with wide curious eyes as the scenery changed from city to forest. Every tree, every curve was a new adventure.",
        "prompt": "Disney Pixar 3D style illustration. CAST: @image1 = {gender_word} adult ({age_display}), fully human body, smooth skin, two arms, two legs — match reference exactly. @image2 = {pet_name} ({pet_desc}): animal body, four paws, fur coat — match reference exactly. Two distinct separate beings. Exactly ONE adult driving + ONE pet in rear seat. SCENE: EXTERIOR SIDE VIEW of the car on a country road. @image1 sits in the DRIVER SEAT at the front, hands on steering wheel, smiling, looking ahead through the windshield. @image2 is settled in the BACK SEAT beside the closed rear window, body upright and alert, face close to the glass, paws resting on the seat or armrest, watching the passing landscape through the glass with wide curious eyes. SETTING: Country road WIDE VIEW, mountains visible in background, green forest lining the road, blue sky, warm sunlight on the car. ATMOSPHERE: Freedom and excited curiosity, open road adventure, wonder at the passing world. STRICT: @image1 is in the DRIVER SEAT at the front. @image2 is in the REAR SEAT looking through the CLOSED window. Window glass is CLOSED. {style}",
        "text_position": "split"
    },
    {
        "id": 3,
        "text_es": "{name} estacionó el carro al inicio del sendero. El aire olía a pinos y tierra húmeda. {pet_name} bajó de un salto y empezó a olfatear todo a su alrededor, la cola moviéndose como un helicóptero.",
        "text_en": "{name} parked the car at the trailhead. The air smelled of pine and damp earth. {pet_name} jumped out and started sniffing everything around, tail spinning like a helicopter.",
        "prompt": "Disney Pixar 3D style illustration. CAST: @image1 = {gender_word} adult ({age_display}), fully human body, smooth skin, two arms, two legs — match reference exactly. @image2 = {pet_name} ({pet_desc}): animal body, four paws, fur coat — match reference exactly. Two distinct separate beings. Exactly ONE adult + ONE pet. SCENE: @image1 stands at a mountain trailhead beside the parked car, arms stretched wide, taking a deep breath of fresh air, backpack being pulled from the trunk, wearing hiking clothes and boots. @image2 stands on all four paws nearby already exploring, nose pressed to the ground sniffing excitedly, tail wagging rapidly like a helicopter. SETTING: Mountain trailhead parking area WIDE VIEW, tall pine trees, wooden trail sign, gravel lot, mountains in background, morning mist between trees. ATMOSPHERE: Fresh mountain air, sense of arrival and wonder, crisp morning light filtering through pines. STRICT: @image1 is a fully human adult standing on two legs. @image2 is an animal exploring on four paws. {style}",
        "text_position": "split"
    },
    {
        "id": 4,
        "text_es": "El sendero subía entre árboles enormes que dejaban pasar rayos de sol como linternas doradas. {name} respiraba profundo, sintiendo cómo el estrés de la ciudad se quedaba atrás. {pet_name} trotaba a su lado, feliz de estar en territorio nuevo.",
        "text_en": "The trail climbed between enormous trees that let sunlight through like golden lanterns. {name} breathed deeply, feeling the city stress melt away. {pet_name} trotted alongside, happy to be in new territory.",
        "prompt": "Disney Pixar 3D style illustration. CAST: @image1 = {gender_word} adult ({age_display}), fully human body, smooth skin, two arms, two legs — match reference exactly. @image2 = {pet_name} ({pet_desc}): animal body, four paws, fur coat — match reference exactly. Two distinct separate beings. Exactly ONE adult + ONE pet. SCENE: @image1 hikes up a beautiful forest trail, wearing a backpack, looking up at the golden sunbeams filtering through the tall trees, relaxed and peaceful, taking a deep breath of fresh air. @image2 trots beside @image1 on all four paws, happy relaxed expression, tail raised, matching the adult's pace loyally. SETTING: Forest trail WIDE VIEW, towering pine and oak trees, golden sunbeams filtering through the canopy creating magical light rays, ferns and wildflowers along the path, dappled golden light on the trail. ATMOSPHERE: Peace and rejuvenation, cathedral-like forest light, fresh clean air, connection with nature. STRICT: @image1 walks upright on two legs. @image2 trots on its own four paws beside them. {style}",
        "text_position": "split"
    },
    {
        "id": 5,
        "text_es": "{name} se detuvo al ver marcas en el suelo. \"Mira, {pet_name}, huellas de venado.\" {pet_name} olfateó las huellas con concentración profesional, como si estuviera resolviendo un caso de detectives.",
        "text_en": "{name} stopped when they noticed marks on the ground. \"Look, {pet_name}, deer tracks.\" {pet_name} sniffed the tracks with professional concentration, as if solving a detective case.",
        "prompt": "Disney Pixar 3D style illustration. CAST: @image1 = {gender_word} adult ({age_display}), fully human body, smooth skin, two arms, two legs — match reference exactly. @image2 = {pet_name} ({pet_desc}): animal body, four paws, fur coat — match reference exactly. Two distinct separate beings. Exactly ONE adult + ONE pet. SCENE: @image1 kneels on the forest trail, one hand pointing down at clear deer tracks in soft muddy dirt, eyes wide with fascinated curiosity, wearing hiking gear with backpack beside them. @image2 stands with nose pressed to the ground sniffing the tracks intensely, fully focused, tail straight and alert, like a professional detective at work. SETTING: Forest trail WIDE VIEW, clear animal tracks visible in a muddy patch, ferns and fallen leaves around, soft dappled forest light through tall trees. ATMOSPHERE: Discovery and curiosity, nature mystery, soft dappled light, the thrill of wildlife exploration. STRICT: @image1 is kneeling on two knees. @image2 is sniffing on four paws. Two characters only. {style}",
        "text_position": "split"
    },
    {
        "id": 6,
        "text_es": "De pronto, una ardilla apareció en una rama baja. {pet_name} se quedó paralizado, con los ojos enormes y las orejas en punta. La ardilla lo miró sin miedo, como diciendo: \"Este es MI bosque.\" {name} contuvo la risa.",
        "text_en": "Suddenly, a squirrel appeared on a low branch. {pet_name} froze, eyes wide and ears pointed. The squirrel stared back fearlessly as if saying: \"This is MY forest.\" {name} held back a laugh.",
        "prompt": "Disney Pixar 3D style illustration. CAST: @image1 = {gender_word} adult ({age_display}), fully human body, smooth skin, two arms, two legs — match reference exactly. @image2 = {pet_name} ({pet_desc}): animal body, four paws, fur coat — match reference exactly. Two distinct separate beings. Exactly ONE adult + ONE pet + ONE squirrel. SCENE: @image2 stands frozen on the trail, eyes wide, ears fully perked, body tense, staring at a bold chubby squirrel sitting on a low pine branch holding an acorn — a classic standoff. @image1 stands behind @image2, hand over mouth, shoulders shaking with suppressed laughter, watching the comedic standoff with pure amusement. SETTING: Forest trail WIDE VIEW, chubby squirrel on a low branch looking smug and unfazed, warm dappled forest light, pine trees in background. ATMOSPHERE: Comedic tension, wildlife encounter humor, warm playful energy, nature comedy at its best. STRICT: @image1 is standing upright on two legs. @image2 is frozen on four paws. One squirrel on branch above. {style}",
        "text_position": "split"
    },
    {
        "id": 7,
        "text_es": "La ardilla lanzó una bellota que rebotó en la cabeza de {pet_name}. \"¡Plop!\" {pet_name} dio un salto hacia atrás de la sorpresa. {name} soltó una carcajada tan fuerte que los pájaros volaron de los árboles.",
        "text_en": "The squirrel dropped an acorn that bounced off {pet_name}'s head. \"Plop!\" {pet_name} jumped back in surprise. {name} laughed so hard that birds flew from the trees.",
        "prompt": "Disney Pixar 3D style illustration. CAST: @image1 = {gender_word} adult ({age_display}), fully human body, smooth skin, two arms, two legs — match reference exactly. @image2 = {pet_name} ({pet_desc}): animal body, four paws, fur coat — match reference exactly. Two distinct separate beings. Exactly ONE adult + ONE pet + ONE squirrel above. SCENE: @image2 leaps backwards in comical surprise with all four paws off the ground, eyes wide with shock, an acorn bouncing near its head, startled expression. @image1 bends over laughing uncontrollably, holding their stomach with both hands, tears of laughter at the corners of their eyes, pure joy on their face. Birds scatter from the treetops above. SETTING: Forest trail WIDE VIEW, smug squirrel on branch above looking pleased with itself, acorn mid-bounce, birds flying away, bright warm forest light. ATMOSPHERE: Pure hilarious slapstick comedy, joyful laughter echoing through the forest, bright warm energy. STRICT: @image1 is bent over laughing on two legs. @image2 is jumping back on four paws. One squirrel above. {style}",
        "text_position": "split"
    },
    {
        "id": 8,
        "text_es": "El sendero los llevó a un arroyo de aguas cristalinas que saltaba entre piedras. {name} cruzó con cuidado saltando de roca en roca. {pet_name} lo observó un momento, calculando, y luego cruzó chapoteando directo por el agua.",
        "text_en": "The trail led them to a crystal-clear stream jumping over rocks. {name} crossed carefully, hopping from rock to rock. {pet_name} watched for a moment, calculating, then crossed by splashing straight through the water.",
        "prompt": "Disney Pixar 3D style illustration. CAST: @image1 = {gender_word} adult ({age_display}), fully human body, smooth skin, two arms, two legs — match reference exactly. @image2 = {pet_name} ({pet_desc}): animal body, four paws, fur coat — match reference exactly. Two distinct separate beings. Exactly ONE adult + ONE pet crossing the stream. SCENE: @image1 is mid-step on a large river rock, arms stretched out for balance, careful concentrated expression, hiking boots on mossy stones, partway across the crystal stream. @image2 splashes joyfully through the shallow stream water beside them rather than using the rocks, water spraying up around its four paws, happy carefree expression, tail wagging. SETTING: Mountain stream WIDE VIEW, crystal clear water flowing over smooth boulders, wildflowers on the banks, pine trees along the stream, sunlight sparkling on the water surface. ATMOSPHERE: Playful adventure, sparkling water light, fresh mountain energy, joy in the contrast of crossing styles. STRICT: @image1 steps carefully on rocks using two feet. @image2 walks freely through the water on four paws. {style}",
        "text_position": "split"
    },
    {
        "id": 9,
        "text_es": "{pet_name} salió del arroyo y se sacudió con toda la energía del mundo. El agua voló por todos lados y {name} recibió una ducha completa. \"¡Gracias, {pet_name}!\" dijo limpiándose la cara, mientras {pet_name} se echaba al sol.",
        "text_en": "{pet_name} came out of the stream and shook with all the energy in the world. Water flew everywhere and {name} got a full shower. \"Thanks, {pet_name}!\" they said wiping their face, while {pet_name} lay down in the sun.",
        "prompt": "Disney Pixar 3D style illustration. CAST: @image1 = {gender_word} adult ({age_display}), fully human body, smooth skin, two arms, two legs — match reference exactly. @image2 = {pet_name} ({pet_desc}): animal body, four paws, fur coat — match reference exactly. Two distinct separate beings. Exactly ONE adult + ONE pet on the stream bank. SCENE: @image2 stands on the grassy stream bank mid-shake, water flying off its fur in all directions in a dramatic spray, creating a tiny rainbow effect in the sunlight, vigorous full-body shake. @image1 stands nearby with arms raised to shield their face, covered in water droplets, laughing despite being soaked, wiping their face with one hand. SETTING: Stream bank WIDE VIEW, warm sunny grassy spot, water droplets catching sunlight and sparkling, smooth warm rocks, trees framing the scene. ATMOSPHERE: Comedic refreshment, sparkling water droplets in warm sunlight, joyful laughter, golden light. STRICT: @image1 is standing on two legs shielding their face. @image2 is shaking vigorously on four paws. {style}",
        "text_position": "split"
    },
    {
        "id": 10,
        "text_es": "Después de una hora de subida, llegaron a un mirador. El valle se extendía debajo de ellos como una alfombra de verdes infinitos. {name} se sentó en una roca y {pet_name} se echó a sus pies. Por un momento, el silencio fue perfecto.",
        "text_en": "After an hour of climbing, they reached a lookout point. The valley spread below them like an endless carpet of greens. {name} sat on a rock and {pet_name} lay at their feet. For a moment, the silence was perfect.",
        "prompt": "Disney Pixar 3D style illustration. CAST: @image1 = {gender_word} adult ({age_display}), fully human body, smooth skin, two arms, two legs — match reference exactly. @image2 = {pet_name} ({pet_desc}): animal body, four paws, fur coat — match reference exactly. Two distinct separate beings. Exactly ONE adult + ONE pet at the viewpoint. SCENE: @image1 sits on a large flat rock at a mountain viewpoint, gazing out at the vast valley below with a peaceful contemplative expression, backpack set beside them, completely still and serene. @image2 lies comfortably at @image1's feet on the rock, also looking out at the view, relaxed and content, resting after the long climb. SETTING: Mountain viewpoint WIDE VIEW, panoramic valley below with layers of green forests, distant blue mountain ranges, vast sky with wispy clouds, rocky outcrop with wildflowers at the edges. ATMOSPHERE: Serenity and awe, vast open beauty, perfect silence, golden light washing over the valley. STRICT: @image1 is seated upright on the rock. @image2 is lying at their feet. Epic viewpoint scene. {style}",
        "text_position": "split"
    },
    {
        "id": 11,
        "text_es": "{name} sacó sándwiches de la mochila y le dio a {pet_name} sus galletas favoritas. Comieron juntos mirando las montañas, el viento suave trayendo olor a flores silvestres. {pet_name} apoyó su cabeza en la pierna de {name}, pidiendo otro bocado.",
        "text_en": "{name} pulled out sandwiches from the backpack and gave {pet_name} their favorite treats. They ate together watching the mountains, the gentle breeze carrying the scent of wildflowers. {pet_name} rested their head on {name}'s leg, asking for another bite.",
        "prompt": "Disney Pixar 3D style illustration. CAST: @image1 = {gender_word} adult ({age_display}), fully human body, smooth skin, two arms, two legs — match reference exactly. @image2 = {pet_name} ({pet_desc}): animal body, four paws, fur coat — match reference exactly. Two distinct separate beings. Exactly ONE adult + ONE pet sharing lunch. SCENE: @image1 sits cross-legged on the ground eating a sandwich, smiling warmly down at @image2, open backpack beside them with trail food and thermos visible. @image2 sits next to @image1 with its head resting gently on @image1's thigh, looking up with wide pleading hopeful eyes, a small treat on the ground nearby. SETTING: Mountain meadow WIDE VIEW, wildflowers swaying around them, mountains with snow caps in background, open backpack with lunch items, midday golden sun. ATMOSPHERE: Comfort and companionship, peaceful outdoor lunch, warm midday light, gentle breeze, the joy of sharing. STRICT: @image1 sits on two legs crossed. @image2 sits beside them, head on the human's thigh. {style}",
        "text_position": "split"
    },
    {
        "id": 12,
        "text_es": "Cuando encontraron el lugar perfecto entre los pinos, {name} empezó a armar la tienda de campaña. {pet_name} decidió \"ayudar\" llevándose una estaca en la boca cada vez que {name} la ponía en su lugar.",
        "text_en": "When they found the perfect spot among the pines, {name} started setting up the tent. {pet_name} decided to \"help\" by carrying away a tent stake in their mouth every time {name} put one in place.",
        "prompt": "Disney Pixar 3D style illustration. CAST: @image1 = {gender_word} adult ({age_display}), fully human body, smooth skin, two arms, two legs — match reference exactly. @image2 = {pet_name} ({pet_desc}): animal body, four paws, fur coat — match reference exactly. Two distinct separate beings. Exactly ONE adult + ONE pet at the campsite. SCENE: @image1 kneels on the ground attempting to set up the tent, looking at @image2 with an exasperated but amused expression, one hand reaching toward the pet, tent half assembled. @image2 trots away proudly on all four paws with a tent stake held in its mouth, playful mischievous expression, tail held high, glancing back over its shoulder at the frustrated human. SETTING: Forest clearing campsite WIDE VIEW, half-assembled tent with poles sticking out, scattered camping gear, tall pine trees around, warm late afternoon golden light, flat grassy area. ATMOSPHERE: Comedic teamwork, playful mischief, warm late afternoon glow, outdoor comedy. STRICT: @image1 is kneeling on two knees. @image2 is trotting away on four paws with a stake in its mouth. {style}",
        "text_position": "split"
    },
    {
        "id": 13,
        "text_es": "Después de negociar con {pet_name} (dos galletas a cambio de las estacas), la tienda quedó lista. {name} infló el colchón y puso las mantas. {pet_name} inmediatamente se metió a la tienda y se acostó justo en el centro, ocupando todo el espacio.",
        "text_en": "After negotiating with {pet_name} (two treats in exchange for the stakes), the tent was ready. {name} inflated the mattress and laid out the blankets. {pet_name} immediately went inside the tent and lay right in the center, taking up all the space.",
        "prompt": "Disney Pixar 3D style illustration. CAST: @image1 = {gender_word} adult ({age_display}), fully human body, smooth skin, two arms, two legs — match reference exactly. @image2 = {pet_name} ({pet_desc}): animal body, four paws, fur coat — match reference exactly. Two distinct separate beings. Exactly ONE adult + ONE pet at the tent. SCENE: @image1 stands at the tent entrance looking inside with hands on hips, half amused and half resigned, head tilted, staring at @image2 inside. @image2 sprawls in the very CENTER of the tent on the sleeping bag and inflatable mattress, completely taking over all the space, lying on its back with paws up, looking up at @image1 with a perfectly innocent and satisfied expression. SETTING: Campsite WIDE VIEW, properly set-up tent with open flap showing the cozy interior, sleeping bag and inflatable mattress, pine trees around, late afternoon sun. ATMOSPHERE: Domestic comedy in the wild, territorial pet humor, warm camping light, cozy tent interior. STRICT: @image1 is standing at the tent door on two legs. @image2 is sprawled inside the tent. {style}",
        "text_position": "split"
    },
    {
        "id": 14,
        "text_es": "Antes del atardecer, bajaron hasta el río. El agua corría entre piedras grandes formando pequeñas cascadas. {pet_name} metió las patas al agua fría y salpicó de alegría. {name} se quitó las botas y metió los pies, sintiendo cómo el agua fresca le devolvía la vida.",
        "text_en": "Before sunset, they went down to the river. Water flowed between large rocks forming small waterfalls. {pet_name} dipped their paws in the cold water and splashed with joy. {name} took off their boots and dipped their feet, feeling the cool water bring them back to life.",
        "prompt": "Disney Pixar 3D style illustration. CAST: @image1 = {gender_word} adult ({age_display}), fully human body, smooth skin, two arms, two legs — match reference exactly. @image2 = {pet_name} ({pet_desc}): animal body, four paws, fur coat — match reference exactly. Two distinct separate beings. Exactly ONE adult + ONE pet at the river. SCENE: @image1 sits on a large boulder with bare feet dangling in the flowing stream, eyes closed in pure bliss, relaxed peaceful expression, hiking boots set neatly beside them on the rock. @image2 stands in the shallow river on all four paws, splashing joyfully with its front paws, water droplets sparkling in the light, happy energetic expression. SETTING: Mountain river WIDE VIEW, large smooth boulders, small waterfalls cascading between rocks, crystal clear water, forest along the banks, warm golden hour light reflecting and sparkling on the water. ATMOSPHERE: Refreshment and freedom, cool water energy, golden hour warmth, rejuvenation and playful joy. STRICT: @image1 sits on a rock with feet in water. @image2 stands in the shallows on four paws. {style}",
        "text_position": "split"
    },
    {
        "id": 15,
        "text_es": "De vuelta al campamento, el cielo se pintó de naranjas y morados. {name} y {pet_name} se sentaron juntos mirando cómo el sol se escondía detrás de las montañas. \"No hay pantalla en el mundo que muestre algo tan bonito\", susurró {name}.",
        "text_en": "Back at camp, the sky painted itself in oranges and purples. {name} and {pet_name} sat together watching the sun hide behind the mountains. \"No screen in the world can show something this beautiful,\" whispered {name}.",
        "prompt": "Disney Pixar 3D style illustration. CAST: @image1 = {gender_word} adult ({age_display}), fully human body, smooth skin, two arms, two legs — match reference exactly. @image2 = {pet_name} ({pet_desc}): animal body, four paws, fur coat — match reference exactly. Two distinct separate beings. Exactly ONE adult + ONE pet watching the sunset. SCENE: @image1 sits on a log at the campsite, arm resting gently on @image2's back, gazing at the spectacular sunset over the mountains, peaceful awestruck expression, warm golden sunset light on their face. @image2 sits beside @image1 on the ground next to the log, also facing the horizon, calm and content, both silhouetted beautifully against the glowing sky. SETTING: Campsite with mountain backdrop WIDE VIEW, breathtaking sunset with orange, purple and gold gradients, mountain silhouettes on the horizon, tent visible to the side, pine tree silhouettes framing the composition, dramatic sky. ATMOSPHERE: Breathtaking beauty, golden emotional warmth, deep connection between human and pet, peaceful awe. STRICT: @image1 sits on the log on two legs. @image2 sits beside them on the ground on four paws. {style}",
        "text_position": "split"
    },
    {
        "id": 16,
        "text_es": "Cuando oscureció, {name} encendió una fogata. Las llamas bailaban lanzando chispas hacia las estrellas. {pet_name} se acurrucó cerca del fuego, hipnotizado por el movimiento de las llamas. {name} calentó malvaviscos y le dio uno a {pet_name}, que lo atrapó al vuelo.",
        "text_en": "When it got dark, {name} lit a campfire. The flames danced, throwing sparks toward the stars. {pet_name} curled up near the fire, mesmerized by the dancing flames. {name} roasted marshmallows and tossed one to {pet_name}, who caught it mid-air.",
        "prompt": "Disney Pixar 3D style illustration. CAST: @image1 = {gender_word} adult ({age_display}), fully human body, smooth skin, two arms, two legs — match reference exactly. @image2 = {pet_name} ({pet_desc}): animal body, four paws, fur coat — match reference exactly. Two distinct separate beings. Exactly ONE adult + ONE pet at the campfire. SCENE: @image1 sits on a log beside the glowing campfire, holding a stick with a marshmallow over the flames, warm firelight illuminating their face, smiling warmly, one hand offering a roasted marshmallow toward @image2. @image2 lies curled up close to the campfire on the ground, cozy and warm, eyes alert and following the marshmallow with happy anticipation, firelight reflecting in its eyes. SETTING: Campsite at night WIDE VIEW, bright crackling campfire with dancing orange flames and golden sparks rising upward, spectacular starry night sky above, tent silhouetted in background, ring of stones around the fire, pine silhouettes. ATMOSPHERE: Magical campfire warmth, starry night wonder, cozy firelight glow, deep intimate bond between human and pet. STRICT: @image1 sits on the log on two legs. @image2 lies near the fire on four paws. Campfire night scene. {style}",
        "text_position": "split"
    },
    {
        "id": 17,
        "text_es": "{name} se acostó sobre una manta mirando las estrellas. Miles de puntos brillantes llenaban el cielo como nunca los había visto en la ciudad. {pet_name} se acostó a su lado, y {name} sintió el calor de su compañero en la noche fría.",
        "text_en": "{name} lay on a blanket looking at the stars. Thousands of brilliant points filled the sky like they'd never seen in the city. {pet_name} lay beside them, and {name} felt the warmth of their companion in the cold night.",
        "prompt": "Disney Pixar 3D style illustration. CAST: @image1 = {gender_word} adult ({age_display}), fully human body, smooth skin, two arms, two legs — match reference exactly. @image2 = {pet_name} ({pet_desc}): animal body, four paws, fur coat — match reference exactly. Two distinct separate beings. Exactly ONE adult + ONE pet stargazing together. SCENE: @image1 lies on their side on a blanket on the ground, head resting on one arm, face visible in profile gazing up at the Milky Way with an expression of wonder and deep peace. @image2 lies snuggled right beside @image1 on the blanket, pressed close for warmth, peaceful sleepy expression, also looking up at the stars. SETTING: Mountain clearing at night WIDE VIEW, spectacular Milky Way stretching across the entire sky, millions of stars, soft moonlight on the blanket, mountain silhouettes against the starry sky. ATMOSPHERE: Cosmic wonder and infinity, intimate warmth against the cold night, spiritual peace, starlit magic, profound connection. STRICT: @image1 lies on their side on the blanket. @image2 lies snuggled beside them. Stargazing night scene. {style}",
        "text_position": "split"
    },
    {
        "id": 18,
        "text_es": "{name} despertó con el sol entrando por la tienda y algo pesado sobre sus piernas: {pet_name} dormía atravesado, roncando suavemente. Afuera, el bosque cantaba con pájaros y el aire frío olía a rocío. {name} sonrió. No quería estar en ningún otro lugar.",
        "text_en": "{name} woke up with sunlight streaming into the tent and something heavy on their legs: {pet_name} was sleeping sideways across them, snoring softly. Outside, the forest sang with birds and the cold air smelled of dew. {name} smiled. They didn't want to be anywhere else.",
        "prompt": "Disney Pixar 3D style illustration. CAST: @image1 = {gender_word} adult ({age_display}), fully human body, smooth skin, two arms, two legs — match reference exactly. @image2 = {pet_name} ({pet_desc}): animal body, four paws, fur coat — match reference exactly. Two distinct separate beings. Exactly ONE adult + ONE pet inside the tent. SCENE: @image1 lies in a sleeping bag inside the tent, just waking up, propped up on one elbow with a soft sleepy smile, looking down with fond amusement at @image2 on their legs. @image2 is sprawled sideways completely across @image1's legs, all four paws stretched out, totally relaxed and snoring, in an adorably awkward sleeping position. SETTING: Inside the tent WIDE VIEW, warm golden morning light glowing warmly through the tent fabric, cozy sleeping bag and pillow, suggestion of forest and birdsong outside, soft filtered light. ATMOSPHERE: Tender funny morning warmth, cozy camping love, soft filtered tent light, perfect contentment. STRICT: @image1 is propped up in the sleeping bag. @image2 is sprawled across their legs. Morning tent scene. {style}",
        "text_position": "split"
    },
    {
        "id": 19,
        "text_es": "Con la mochila llena de recuerdos y el corazón lleno de paz, {name} emprendió el camino de vuelta. {pet_name} caminaba a su lado con paso firme, como un compañero que dice: \"A donde vayas, voy contigo.\" Porque las mejores aventuras no se miden en kilómetros, sino en quién camina a tu lado.",
        "text_en": "With a backpack full of memories and a heart full of peace, {name} began the journey back. {pet_name} walked beside them with steady steps, like a companion saying: \"Wherever you go, I go with you.\" Because the best adventures aren't measured in miles, but in who walks beside you.",
        "prompt": "Disney Pixar 3D style illustration. CAST: @image1 = {gender_word} adult ({age_display}), fully human body, smooth skin, two arms, two legs — match reference exactly. @image2 = {pet_name} ({pet_desc}): animal body, four paws, fur coat — match reference exactly. Two distinct separate beings. Exactly ONE adult + ONE pet walking home together. SCENE: @image1 walks down a descending mountain trail with a full backpack, peaceful and satisfied expression, looking ahead at the valley below with quiet contentment, morning light warm behind them. @image2 walks steadily beside @image1 on all four paws at a matching pace, loyal confident posture, both looking forward together, side by side as equals. SETTING: Mountain trail descending WIDE VIEW, long morning shadows on the path, valley visible far below, the car small in the distance, panoramic mountain scenery, wildflowers lining the trail, epic golden landscape. ATMOSPHERE: Fulfillment and deep gratitude, the warmth of a journey completed, golden morning light, the unbreakable bond of companions. STRICT: @image1 walks on two legs with backpack. @image2 walks beside them on four paws. Homeward journey, side by side. {style}",
        "text_position": "split"
    }
]

CLOSING_SCENE = {
    "id": 20,
    "prompt": "Disney Pixar 3D style illustration. CAST: @image1 = {gender_word} adult ({age_display}), fully human body, smooth skin, two arms, two legs — match reference exactly. @image2 = {pet_name} ({pet_desc}): animal body, four paws, fur coat — match reference exactly. Two distinct separate beings. Exactly ONE adult + ONE pet at the overlook. SCENE: @image1 sits on a rock at a dramatic mountain overlook, seen from a three-quarter angle, face visible with a peaceful and grateful expression, backpack resting beside them, warm golden sunset light on their face. @image2 sits loyally beside @image1, leaning gently against the adult's leg, calm and happy expression, both gazing out together at the vast magnificent landscape below. ACTION: Human and pet share a perfect ending moment together at a dramatic mountain overlook at golden sunset. SETTING: Dramatic mountain overlook WIDE VIEW, golden hour sky with warm orange and purple gradients, vast valley and mountain ranges below, pine trees framing the sides, epic cinematic composition. ATMOSPHERE: Epic emotional finale, golden cinematic light, deep bond and absolute loyalty, adventure and love perfectly captured. STRICT: @image1 sits on the rock on two legs. @image2 sits beside them on four paws. Epic closing scene. {style}",
    "text_position": "none"
}

FRONT_COVER = {
    "prompt": "Disney Pixar 3D style illustration. CAST: @image1 = {gender_word} adult ({age_display}), fully human body, smooth skin, two arms, two legs, preserve adult age and mature face proportions — match reference exactly. @image2 = {pet_name} ({pet_desc}): animal body, four paws, fur coat — match reference exactly. Two distinct separate beings. Exactly ONE adult + ONE pet at the campfire. SCENE: @image1 sits by a glowing campfire in a mountain campsite, wearing outdoor hiking clothes, warm happy smile, relaxed and content, enjoying the magical evening. @image2 sits beside @image1 at the campfire, looking up at the adult with adoring and devoted eyes, happy and cozy in the warm firelight. ACTION: Human and pet share a cozy intimate moment together around a crackling campfire, bonded and at peace, the perfect image of friendship and adventure. SETTING: Mountain campsite WIDE VIEW, epic mountain peaks in the background, pine trees around, warm twilight sky, glowing campfire casting warm golden light on both characters, tent visible in the background. ATMOSPHERE: Warm cozy bonding, golden fire light, magical mountain evening, deep friendship and love, adventure and peace together. STRICT: @image1 is a fully human adult on two legs. @image2 is an animal on four paws. Centered composition for book cover. Pure illustration only, zero text or lettering. {style}"
}

BACK_COVER = {
    "prompt": "Disney Pixar 3D style illustration. SETTING: A peaceful mountain campsite scene at golden hour WIDE VIEW, an empty tent with an open flap, a pair of hiking boots beside the tent entrance, a backpack leaning against a log, a campfire with dying embers, a blanket spread on the grass, a thermos and a trail map, warm sunset light streaming through pine trees onto the objects, mountains visible in the background. ATMOSPHERE: Warm nostalgic, peaceful evening, adventure told through objects, golden warm tones, story told through belongings left behind. STRICT: Only scenery and meaningful props, pure illustration only, zero text or lettering. {style}"
}


def build_human_preview_prompt(human_desc: str, **kwargs) -> str:
    return f"Disney Pixar 3D style illustration. FULL BODY portrait of {human_desc}, wearing casual outdoor hiking clothes (flannel shirt, cargo pants, hiking boots), standing naturally with one hand on backpack strap, relaxed confident smile, centered in frame, occupying 60% of frame height. NEUTRAL SOLID GRADIENT BACKGROUND (soft cream to warm beige), plain studio background. Natural friendly expression, relaxed standing pose. Clean professional animation art, clean illustration only. STRICT: Character fully clothed."


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
    size_label_map = {
        "small":  "small and compact (puppy or small breed proportions — short legs, rounded face, small body)",
        "medium": "medium-sized adult (standard proportions — balanced body, not too big not too small)",
        "large":  "large and imposing (big adult proportions — tall, broad, long legs, big head)",
    }
    frame_map = {
        "small":  "compact small body, fits fully in frame with space around it",
        "medium": "full body fits naturally and comfortably in frame",
        "large":  "big imposing body fills the frame, broad and tall",
    }
    size_label = size_label_map.get(pet_size, size_label_map["medium"])
    frame_desc = frame_map.get(pet_size, frame_map["medium"])
    desc_hint = f" ({pet_desc})" if pet_desc else ""
    return (
        f"High-quality Disney Pixar 3D animated illustration. "
        f"Convert the {animal} from @image1 into a 3D animated children's book character.{desc_hint} "
        f"Preserve the exact breed, coat color, markings and body proportions from @image1 — body size: {size_label}. "
        f"FULL BODY portrait, sitting or standing naturally, friendly expression, centered, {frame_desc}. "
        f"NEUTRAL SOLID GRADIENT BACKGROUND (soft cream to warm beige). "
        f"Warm lighting, expressive eyes. Clean animation art, clean illustration only."
    )


def build_scene_prompt(scene: dict, human_desc: str, pet_name: str, pet_desc: str, age_display: str = "30 year old adult", eye_desc: str = "", gender_word: str = "person", glasses: str = "", facial_hair: str = "", hair_color: str = "", hair_desc: str = "", **kwargs) -> str:
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
    facial_hair_desc = ", with light stubble" if facial_hair == "stubble" else ", with short beard" if facial_hair == "short_beard" else ", with full thick beard" if facial_hair == "full_beard" else ", with a mustache" if facial_hair == "mustache" else ""
    prompt = prompt.replace('{facial_hair_desc}', facial_hair_desc)
    prompt = prompt.replace('{style}', STYLE_BASE)
    hair_color_label = hair_color if hair_color else (hair_desc.split()[0] if hair_desc else "brown")
    prompt = prompt.replace('{hair_color}', hair_color_label)
    prompt = prompt.replace('{hair_desc}', hair_desc if hair_desc else hair_color_label)
    # Explicitly name the animal type in CAST so FLUX doesn't default to dog
    prompt = prompt.replace('ONE pet', f'ONE {animal_word}')
    return prompt


def build_story_text(scene: dict, child_name: str, pet_name: str, language: str = 'es') -> str:
    text_key = 'text_es' if language == 'es' else 'text_en'
    text = scene.get(text_key, '')
    text = text.replace('{pet_name}', pet_name)
    text = text.replace('{name}', child_name)
    return text


def get_all_scene_prompts(human_desc: str, pet_name: str, pet_desc: str, age_display: str = "30 year old adult", eye_desc: str = "", gender_word: str = "person") -> list:
    prompts = []
    for scene in FURRY_LOVE_ADULT_SCENES:
        prompts.append(build_scene_prompt(scene, human_desc, pet_name, pet_desc, age_display, eye_desc, gender_word))
    prompts.append(build_scene_prompt(CLOSING_SCENE, human_desc, pet_name, pet_desc, age_display, eye_desc, gender_word))
    return prompts


def get_all_story_texts(child_name: str, pet_name: str, language: str = 'es') -> list:
    texts = []
    for scene in FURRY_LOVE_ADULT_SCENES:
        texts.append({
            'id': scene['id'],
            'text': build_story_text(scene, child_name, pet_name, language),
            'text_position': scene.get('text_position', 'split')
        })
    return texts


def get_cover_prompts(human_desc: str, pet_name: str, pet_desc: str, age_display: str = "30 year old adult", eye_desc: str = "", gender_word: str = "person", glasses: str = "") -> dict:
    return {
        'front': build_scene_prompt(FRONT_COVER, human_desc, pet_name, pet_desc, age_display, eye_desc, gender_word, glasses=glasses),
        'back': build_scene_prompt(BACK_COVER, human_desc, pet_name, pet_desc, age_display, eye_desc, gender_word, glasses=glasses)
    }
