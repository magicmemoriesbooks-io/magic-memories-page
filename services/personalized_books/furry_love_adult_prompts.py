# Tú y tu Amor Peludo - Adult Mountain Adventure Story Prompts
# 19 scenes + closing + covers
# Story: "Nuestra Gran Aventura" - A mountain excursion with their dog
# Ages 18-75 - Nature, hiking, camping, bonding with pet
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
#   - Human is an adult (18-75 years old)
#   - Pet is a dog (customized breed, color, pattern)
#   - TWO reference images per scene (human + pet)
#   - Text uses {name} for human and {pet_name} for pet
#   - The dog is NEVER carried. Always walks beside the human on its own legs.

STYLE_BASE = "Disney Pixar 3D style, soft warm lighting, adventurous cinematic atmosphere, WIDE SHOT full body from head to feet, characters occupy 40% of frame, mountain and nature environment visible, clean illustration only. STRICT: All adults wear appropriate outdoor hiking clothes, fully clothed always."

FURRY_LOVE_ADULT_SCENES = [
    {
        "id": 1,
        "text_es": "{name} abrió el maletero del carro y empezó a cargar la mochila, la tienda de campaña y las botas de montaña. {pet_name} observaba cada movimiento con las orejas levantadas, moviendo la cola sin parar.",
        "text_en": "{name} opened the trunk and started loading the backpack, the tent, and the hiking boots. {pet_name} watched every move with perked ears, tail wagging nonstop.",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: An adult ({age_display}) with {eye_desc} eyes{glasses_desc}{facial_hair_desc} loading hiking gear into the trunk of an SUV parked in a driveway, wearing casual outdoor clothes, excited expression. PET: {pet_desc}, standing beside the car watching eagerly with perked ears and wagging tail, excited body language. ACTION: The human loads camping gear (backpack, rolled tent, boots) into the car trunk while the pet watches with anticipation. SETTING: Residential driveway WIDE VIEW, SUV with open trunk, morning sunlight, suburban neighborhood, clear blue sky. ATMOSPHERE: Excitement and anticipation, fresh morning light, adventure about to begin. STRICT: Only ONE adult, ONE pet standing on its own four legs, the pet always walks on its own four paws. {style}",
        "text_position": "split"
    },
    {
        "id": 2,
        "text_es": "\"¡Vamos, {pet_name}!\" dijo {name} abriendo la puerta trasera. {pet_name} saltó al asiento de un brinco y se asomó por la ventanilla. El viento le alborotaba las orejas mientras el paisaje cambiaba de ciudad a bosque.",
        "text_en": "\"Let's go, {pet_name}!\" said {name}, opening the back door. {pet_name} jumped onto the seat in one leap and stuck their head out the window. The wind ruffled their ears as the scenery changed from city to forest.",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: An adult ({age_display}) with {eye_desc} eyes{glasses_desc}{facial_hair_desc} sitting in the DRIVER SEAT on the LEFT side, hands on the steering wheel, smiling, looking at the road ahead through the windshield. PET: {pet_desc}, sitting in the BACK SEAT BEHIND the driver, head sticking out the rear passenger window, ears flapping in the wind, eyes squinting with joy, tongue out, enjoying the ride from the back. ACTION: FRONT VIEW of the car interior showing the adult driving in the front and the pet in the back seat with head out the window. SETTING: Road through countryside WIDE VIEW, mountains visible ahead through windshield, green trees lining the road, blue sky. ATMOSPHERE: Freedom and excitement, open road adventure, warm sunlight. STRICT: The pet sits in the back seat. The human drives from the front seat. ONE adult in front, ONE pet in back. {style}",
        "text_position": "split"
    },
    {
        "id": 3,
        "text_es": "{name} estacionó el carro al inicio del sendero. El aire olía a pinos y tierra húmeda. {pet_name} bajó de un salto y empezó a olfatear todo a su alrededor, la cola moviéndose como un helicóptero.",
        "text_en": "{name} parked the car at the trailhead. The air smelled of pine and damp earth. {pet_name} jumped out and started sniffing everything around, tail spinning like a helicopter.",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: An adult ({age_display}) with {eye_desc} eyes{glasses_desc}{facial_hair_desc} stepping out of the car at a mountain trailhead, stretching, breathing in the fresh air, wearing hiking clothes and boots, backpack being pulled from the trunk. PET: {pet_desc}, already out of the car sniffing the ground excitedly, tail wagging rapidly, nose to the earth exploring new smells. ACTION: The human arrives at the trailhead and unloads gear while the pet explores the area excitedly by sniffing. SETTING: Mountain trailhead parking area WIDE VIEW, tall pine trees, wooden trail sign, gravel parking lot, mountains in background, morning mist between trees. ATMOSPHERE: Fresh mountain air, sense of arrival and wonder, crisp morning light filtering through pines. STRICT: Only ONE adult, ONE pet on the ground exploring, pet walks on its own. {style}",
        "text_position": "split"
    },
    {
        "id": 4,
        "text_es": "El sendero subía entre árboles enormes que dejaban pasar rayos de sol como linternas doradas. {name} respiraba profundo, sintiendo cómo el estrés de la ciudad se quedaba atrás. {pet_name} trotaba a su lado, feliz de estar en territorio nuevo.",
        "text_en": "The trail climbed between enormous trees that let sunlight through like golden lanterns. {name} breathed deeply, feeling the city stress melt away. {pet_name} trotted alongside, happy to be in new territory.",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: An adult ({age_display}) with {eye_desc} eyes{glasses_desc}{facial_hair_desc} hiking up a forest trail, wearing a backpack, relaxed peaceful expression, looking up at the sunlight filtering through tall trees, taking a deep breath. PET: {pet_desc}, trotting beside the human on the trail at the same pace, happy relaxed expression, tail up, walking confidently on its own legs. ACTION: Both walk together up a beautiful forest trail, the human enjoying nature while the pet trots loyally beside them. SETTING: Forest trail WIDE VIEW, towering pine and oak trees, golden sunbeams filtering through canopy creating light rays, ferns and wildflowers along the path, dappled light. ATMOSPHERE: Peace and rejuvenation, cathedral-like forest light, fresh clean air, connection with nature. STRICT: Only ONE adult hiking, ONE pet walking beside them on its own four legs, the dog always walks on its own four paws, forest trail scene. {style}",
        "text_position": "split"
    },
    {
        "id": 5,
        "text_es": "{name} se detuvo al ver marcas en el suelo. \"Mira, {pet_name}, huellas de venado.\" {pet_name} olfateó las huellas con concentración profesional, como si estuviera resolviendo un caso de detectives.",
        "text_en": "{name} stopped when they noticed marks on the ground. \"Look, {pet_name}, deer tracks.\" {pet_name} sniffed the tracks with professional concentration, as if solving a detective case.",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: An adult ({age_display}) with {eye_desc} eyes{glasses_desc}{facial_hair_desc} kneeling on a forest trail, one hand pointing down at animal tracks in soft dirt, curious fascinated expression, wearing hiking gear with backpack. PET: {pet_desc}, nose pressed to the ground sniffing the tracks intensely, focused concentrated expression, tail straight and alert. ACTION: The human kneels and points at deer tracks in the mud while the pet sniffs them with great focus. SETTING: Forest trail WIDE VIEW, clear animal tracks visible in a muddy patch, ferns and fallen leaves around, filtered forest light through tall trees. ATMOSPHERE: Discovery and curiosity, soft dappled light, nature exploration. STRICT: Only ONE adult kneeling, ONE pet sniffing ground, two characters total in the scene. {style}",
        "text_position": "split"
    },
    {
        "id": 6,
        "text_es": "De pronto, una ardilla apareció en una rama baja. {pet_name} se quedó paralizado, con los ojos enormes y las orejas en punta. La ardilla lo miró sin miedo, como diciendo: \"Este es MI bosque.\" {name} contuvo la risa.",
        "text_en": "Suddenly, a squirrel appeared on a low branch. {pet_name} froze, eyes wide and ears pointed. The squirrel stared back fearlessly as if saying: \"This is MY forest.\" {name} held back a laugh.",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: An adult ({age_display}) with {eye_desc} eyes{glasses_desc}{facial_hair_desc} standing on the trail behind the pet, hand over mouth trying not to laugh, amused watching the standoff between pet and squirrel. PET: {pet_desc}, frozen in a pointing stance on the trail, eyes wide, ears fully alert, body tense, staring at a squirrel on a low branch, completely fixated. ACTION: A comedic standoff between the pet frozen in place and a bold squirrel on a branch who stares back unfazed, while the human watches in amusement. SETTING: Forest trail WIDE VIEW, a bold chubby squirrel sitting on a low pine branch holding an acorn, the pet below frozen mid-step, warm forest light. ATMOSPHERE: Comedic tension, wildlife encounter humor, warm playful energy, nature comedy. STRICT: Only ONE adult, ONE pet standing on ground, ONE squirrel on branch, funny standoff scene. {style}",
        "text_position": "split"
    },
    {
        "id": 7,
        "text_es": "La ardilla lanzó una bellota que rebotó en la cabeza de {pet_name}. \"¡Plop!\" {pet_name} dio un salto hacia atrás de la sorpresa. {name} soltó una carcajada tan fuerte que los pájaros volaron de los árboles.",
        "text_en": "The squirrel dropped an acorn that bounced off {pet_name}'s head. \"Plop!\" {pet_name} jumped back in surprise. {name} laughed so hard that birds flew from the trees.",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: An adult ({age_display}) with {eye_desc} eyes{glasses_desc}{facial_hair_desc} bent over laughing uncontrollably, holding their stomach, eyes crinkled with tears of laughter, pure joy on their face. PET: {pet_desc}, jumping backwards in comical surprise, all four paws off the ground, startled wide-eyed expression, an acorn bouncing near its head. ACTION: The pet recoils in surprise as a squirrel drops an acorn on its head, while the human bursts into uncontrollable laughter, birds scattering from trees. SETTING: Forest trail WIDE VIEW, squirrel on branch above looking smug, birds flying away from treetops, acorn mid-bounce, dappled sunlight. ATMOSPHERE: Pure hilarious comedy, joyful laughter echoing through forest, bright warm light, slapstick humor. STRICT: Only ONE adult laughing, ONE pet jumping back, ONE squirrel above, comedic scene. {style}",
        "text_position": "split"
    },
    {
        "id": 8,
        "text_es": "El sendero los llevó a un arroyo de aguas cristalinas que saltaba entre piedras. {name} cruzó con cuidado saltando de roca en roca. {pet_name} lo observó un momento, calculando, y luego cruzó chapoteando directo por el agua.",
        "text_en": "The trail led them to a crystal-clear stream jumping over rocks. {name} crossed carefully, hopping from rock to rock. {pet_name} watched for a moment, calculating, then crossed by splashing straight through the water.",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: An adult ({age_display}) with {eye_desc} eyes{glasses_desc}{facial_hair_desc} mid-step on a river rock, arms out for balance, careful focused expression, hiking boots on mossy rocks, already partway across the stream. PET: {pet_desc}, splashing joyfully through the shallow stream water rather than using the rocks, water spraying around its legs, happy carefree expression. ACTION: The human carefully crosses a mountain stream by stepping on rocks while the pet splashes straight through the water beside them, both crossing together. SETTING: Mountain stream WIDE VIEW, crystal clear water flowing over smooth river rocks, wildflowers on the banks, pine trees along the stream, sunlight sparkling on water surface. ATMOSPHERE: Playful adventure, sparkling water, fresh mountain stream energy, joy and contrast in crossing styles. STRICT: Only ONE adult on rocks, ONE pet walking through water on its own legs, stream crossing scene. {style}",
        "text_position": "split"
    },
    {
        "id": 9,
        "text_es": "{pet_name} salió del arroyo y se sacudió con toda la energía del mundo. El agua voló por todos lados y {name} recibió una ducha completa. \"¡Gracias, {pet_name}!\" dijo limpiándose la cara, mientras {pet_name} se echaba al sol.",
        "text_en": "{pet_name} came out of the stream and shook with all the energy in the world. Water flew everywhere and {name} got a full shower. \"Thanks, {pet_name}!\" they said wiping their face, while {pet_name} lay down in the sun.",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: An adult ({age_display}) with {eye_desc} eyes{glasses_desc}{facial_hair_desc} standing near the stream bank, arms up shielding face, splashed with water droplets, laughing expression despite being soaked, wiping face with one hand. PET: {pet_desc}, mid-shake on the stream bank, water flying off in all directions in a dramatic spray, creating a rainbow effect in the sunlight, shaking vigorously. ACTION: The pet shakes off water from the stream soaking the human with a spray of droplets, the human laughs while trying to shield themselves. SETTING: Stream bank WIDE VIEW, grassy sunny spot, water droplets catching sunlight creating tiny rainbows, warm rocks for drying, trees framing the scene. ATMOSPHERE: Comedic refreshment, sparkling water droplets in sunlight, joyful laughter, warm golden light. STRICT: Only ONE adult being splashed, ONE pet shaking off water, funny stream bank scene. {style}",
        "text_position": "split"
    },
    {
        "id": 10,
        "text_es": "Después de una hora de subida, llegaron a un mirador. El valle se extendía debajo de ellos como una alfombra de verdes infinitos. {name} se sentó en una roca y {pet_name} se echó a sus pies. Por un momento, el silencio fue perfecto.",
        "text_en": "After an hour of climbing, they reached a lookout point. The valley spread below them like an endless carpet of greens. {name} sat on a rock and {pet_name} lay at their feet. For a moment, the silence was perfect.",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: An adult ({age_display}) with {eye_desc} eyes{glasses_desc}{facial_hair_desc} sitting on a large flat rock at a mountain viewpoint, gazing out at the vast valley below, peaceful contemplative expression, backpack beside them, serene posture. PET: {pet_desc}, lying comfortably at the human's feet on the rock, also looking out at the view, relaxed and content, resting after the climb. ACTION: Both sit quietly at a mountain lookout, sharing a peaceful moment looking out over a breathtaking valley view. SETTING: Mountain viewpoint WIDE VIEW, panoramic valley below with layers of green forests, distant blue mountains, vast sky with wispy clouds, rocky outcrop, wildflowers at edges. ATMOSPHERE: Serenity and awe, vast open beauty, peaceful silence, golden light on the valley, contemplative calm. STRICT: Only ONE adult sitting on rock, ONE pet lying at their feet, epic mountain viewpoint scene. {style}",
        "text_position": "split"
    },
    {
        "id": 11,
        "text_es": "{name} sacó sándwiches de la mochila y le dio a {pet_name} sus galletas favoritas. Comieron juntos mirando las montañas, el viento suave trayendo olor a flores silvestres. {pet_name} apoyó su cabeza en la pierna de {name}, pidiendo otro bocado.",
        "text_en": "{name} pulled out sandwiches from the backpack and gave {pet_name} their favorite treats. They ate together watching the mountains, the gentle breeze carrying the scent of wildflowers. {pet_name} rested their head on {name}'s leg, asking for another bite.",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: An adult ({age_display}) with {eye_desc} eyes{glasses_desc}{facial_hair_desc} sitting on the ground with legs crossed, eating a sandwich, smiling down at the pet, backpack open beside them with food visible. PET: {pet_desc}, sitting next to the human, resting its head on the human's thigh, looking up with pleading hopeful eyes, a small treat on the ground nearby. ACTION: The human shares a mountain lunch break while the pet rests its head on their leg hoping for more treats, a tender bonding moment over food. SETTING: Mountain meadow WIDE VIEW, wildflowers around, mountains in background, open backpack with trail lunch, thermos, soft breeze blowing grass, midday sun. ATMOSPHERE: Comfort and companionship, peaceful outdoor lunch, warm midday light, gentle breeze, sharing moment. STRICT: Only ONE adult sitting, ONE pet beside them on the ground, picnic lunch scene. {style}",
        "text_position": "split"
    },
    {
        "id": 12,
        "text_es": "Cuando encontraron el lugar perfecto entre los pinos, {name} empezó a armar la tienda de campaña. {pet_name} decidió \"ayudar\" llevándose una estaca en la boca cada vez que {name} la ponía en su lugar.",
        "text_en": "When they found the perfect spot among the pines, {name} started setting up the tent. {pet_name} decided to \"help\" by carrying away a tent stake in their mouth every time {name} put one in place.",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: An adult ({age_display}) with {eye_desc} eyes{glasses_desc}{facial_hair_desc} kneeling on the ground trying to set up a tent, looking at the pet with an exasperated amused expression, one hand reaching toward the pet, tent half-assembled. PET: {pet_desc}, trotting away proudly with a tent stake in its mouth, playful mischievous expression, tail high, looking back over its shoulder at the frustrated human. ACTION: The pet steals tent stakes while the human tries to set up camp, creating a comedic obstacle, the pet runs off with a stake while the human reaches for it. SETTING: Forest clearing campsite WIDE VIEW, half-assembled tent, scattered camping gear, pine trees around, late afternoon golden light, flat grassy area. ATMOSPHERE: Comedic teamwork gone wrong, playful mischief, warm late afternoon light, outdoor comedy. STRICT: Only ONE adult setting up tent, ONE pet stealing stake, funny camping scene. {style}",
        "text_position": "split"
    },
    {
        "id": 13,
        "text_es": "Después de negociar con {pet_name} (dos galletas a cambio de las estacas), la tienda quedó lista. {name} infló el colchón y puso las mantas. {pet_name} inmediatamente se metió a la tienda y se acostó justo en el centro, ocupando todo el espacio.",
        "text_en": "After negotiating with {pet_name} (two treats in exchange for the stakes), the tent was ready. {name} inflated the mattress and laid out the blankets. {pet_name} immediately went inside the tent and lay right in the center, taking up all the space.",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: An adult ({age_display}) with {eye_desc} eyes{glasses_desc}{facial_hair_desc} standing at the tent entrance looking inside with a hands-on-hips expression, half amused half resigned, head tilted looking at the pet sprawled inside. PET: {pet_desc}, lying sprawled out in the very center of the tent on the sleeping bag and mattress, taking up all the space, completely comfortable, looking up at the human with innocent satisfied eyes. ACTION: The pet claims the entire tent space by sprawling in the center while the human looks inside wondering where they will sleep. SETTING: Campsite WIDE VIEW, properly set up tent with open flap showing interior, sleeping bag and inflatable mattress inside, pine trees around, late afternoon sun, campsite with gear. ATMOSPHERE: Domestic comedy in the wild, territorial humor, warm camping light, cozy tent interior. STRICT: Only ONE adult at tent entrance, ONE pet inside tent, funny camping scene. {style}",
        "text_position": "split"
    },
    {
        "id": 14,
        "text_es": "Antes del atardecer, bajaron hasta el río. El agua corría entre piedras grandes formando pequeñas cascadas. {pet_name} metió las patas al agua fría y salpicó de alegría. {name} se quitó las botas y metió los pies, sintiendo cómo el agua fresca le devolvía la vida.",
        "text_en": "Before sunset, they went down to the river. Water flowed between large rocks forming small waterfalls. {pet_name} dipped their paws in the cold water and splashed with joy. {name} took off their boots and dipped their feet, feeling the cool water bring them back to life.",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: An adult ({age_display}) with {eye_desc} eyes{glasses_desc}{facial_hair_desc} sitting on a large river rock with bare feet in the flowing water, eyes closed in bliss, relaxed peaceful expression, hiking boots set aside, feeling refreshed. PET: {pet_desc}, standing in the shallow river water splashing playfully with its front paws, joyful energetic expression, water droplets sparkling. ACTION: Both enjoy the mountain river, the human relaxing with feet in the water while the pet plays and splashes in the shallows. SETTING: Mountain river WIDE VIEW, large smooth boulders, small waterfalls between rocks, crystal clear water, forest along the banks, golden hour light reflecting on water surface. ATMOSPHERE: Refreshment and freedom, cool water energy, golden hour warmth, rejuvenation and play. STRICT: Only ONE adult with feet in water, ONE pet standing and splashing in water on its own, river exploration scene. {style}",
        "text_position": "split"
    },
    {
        "id": 15,
        "text_es": "De vuelta al campamento, el cielo se pintó de naranjas y morados. {name} y {pet_name} se sentaron juntos mirando cómo el sol se escondía detrás de las montañas. \"No hay pantalla en el mundo que muestre algo tan bonito\", susurró {name}.",
        "text_en": "Back at camp, the sky painted itself in oranges and purples. {name} and {pet_name} sat together watching the sun hide behind the mountains. \"No screen in the world can show something this beautiful,\" whispered {name}.",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: An adult ({age_display}) with {eye_desc} eyes{glasses_desc}{facial_hair_desc} sitting on a log at the campsite, arm resting gently on the pet beside them, gazing at the sunset, peaceful awestruck expression, warm sunset light on their face. PET: {pet_desc}, sitting beside the human on the ground next to the log, also facing the sunset, calm content expression, silhouetted with the human against the sky. ACTION: Both sit together watching a spectacular mountain sunset, sharing a quiet beautiful moment side by side. SETTING: Campsite with mountain backdrop WIDE VIEW, spectacular sunset with orange purple and gold colors, mountain silhouettes, tent visible to the side, pine tree silhouettes, dramatic sky. ATMOSPHERE: Breathtaking beauty, emotional warmth, sunset gold and purple, peaceful awe, deep connection between human and pet. STRICT: Only ONE adult on log, ONE pet sitting beside them on ground, sunset watching scene. {style}",
        "text_position": "split"
    },
    {
        "id": 16,
        "text_es": "Cuando oscureció, {name} encendió una fogata. Las llamas bailaban lanzando chispas hacia las estrellas. {pet_name} se acurrucó cerca del fuego, hipnotizado por el movimiento de las llamas. {name} calentó malvaviscos y le dio uno a {pet_name}, que lo atrapó al vuelo.",
        "text_en": "When it got dark, {name} lit a campfire. The flames danced, throwing sparks toward the stars. {pet_name} curled up near the fire, mesmerized by the dancing flames. {name} roasted marshmallows and tossed one to {pet_name}, who caught it mid-air.",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: An adult ({age_display}) with {eye_desc} eyes{glasses_desc}{facial_hair_desc} sitting on a log by a campfire, roasting marshmallows on a stick, warm firelight on their face, smiling warmly, one hand offering a marshmallow toward the pet. PET: {pet_desc}, lying near the campfire close to the human, warm firelight reflecting in its eyes, alert happy expression, eyes following the marshmallow, cozy and warm. ACTION: The human roasts marshmallows by the campfire while sharing one with the pet, both warm and cozy in the firelight. SETTING: Campsite at night WIDE VIEW, bright warm campfire with dancing flames and orange sparks rising, starry night sky visible above, tent in background, pine tree silhouettes, ring of stones around fire. ATMOSPHERE: Magical campfire warmth, starry night wonder, cozy firelight glow, intimate connection between human and pet. STRICT: Only ONE adult by fire, ONE pet lying near fire on the ground, campfire night scene. {style}",
        "text_position": "split"
    },
    {
        "id": 17,
        "text_es": "{name} se acostó sobre una manta mirando las estrellas. Miles de puntos brillantes llenaban el cielo como nunca los había visto en la ciudad. {pet_name} se acostó a su lado, y {name} sintió el calor de su compañero en la noche fría.",
        "text_en": "{name} lay on a blanket looking at the stars. Thousands of brilliant points filled the sky like they'd never seen in the city. {pet_name} lay beside them, and {name} felt the warmth of their companion in the cold night.",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: An adult ({age_display}) with {eye_desc} eyes{glasses_desc}{facial_hair_desc} lying on their side on a blanket on the ground, head resting on one arm, face visible in profile gazing up at the starry sky, expression of wonder and peace, relaxed pose. PET: {pet_desc}, lying right beside the human on the blanket, snuggled close for warmth, peaceful sleepy expression. ACTION: Both lie side by side on a blanket stargazing, sharing body warmth under a spectacular starry sky, a deeply peaceful moment. SETTING: Mountain clearing at night WIDE VIEW, spectacular Milky Way and stars above, blanket on grass, mountain silhouettes against starry sky, soft moonlight. ATMOSPHERE: Wonder and infinity, cosmic beauty, intimate warmth against the cold, spiritual peace, starlit magic. STRICT: Only ONE adult lying on side, ONE pet beside them, stargazing scene. {style}",
        "text_position": "split"
    },
    {
        "id": 18,
        "text_es": "{name} despertó con el sol entrando por la tienda y algo pesado sobre sus piernas: {pet_name} dormía atravesado, roncando suavemente. Afuera, el bosque cantaba con pájaros y el aire frío olía a rocío. {name} sonrió. No quería estar en ningún otro lugar.",
        "text_en": "{name} woke up with sunlight streaming into the tent and something heavy on their legs: {pet_name} was sleeping sideways across them, snoring softly. Outside, the forest sang with birds and the cold air smelled of dew. {name} smiled. They didn't want to be anywhere else.",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: An adult ({age_display}) with {eye_desc} eyes{glasses_desc}{facial_hair_desc} lying in a sleeping bag inside the tent, just waking up with a soft sleepy smile, propped up on one elbow, looking down fondly at the pet sleeping across their legs, morning light glowing through tent fabric. PET: {pet_desc}, sleeping sprawled across the human's legs inside the tent, completely relaxed, slightly snoring, paws twitching in a dream, adorable sleeping position. ACTION: The human wakes up in the tent to find the pet sleeping across their legs, a tender funny morning moment. SETTING: Inside the tent WIDE VIEW, warm morning light glowing through orange and green tent fabric, sleeping bag and pillow, cozy camping interior, suggestion of forest and birds outside. ATMOSPHERE: Tender morning warmth, gentle humor, cozy camping morning, soft filtered tent light, love and companionship. STRICT: Only ONE adult waking up in tent, ONE pet sleeping across their legs, morning tent scene. {style}",
        "text_position": "split"
    },
    {
        "id": 19,
        "text_es": "Con la mochila llena de recuerdos y el corazón lleno de paz, {name} emprendió el camino de vuelta. {pet_name} caminaba a su lado con paso firme, como un compañero que dice: \"A donde vayas, voy contigo.\" Porque las mejores aventuras no se miden en kilómetros, sino en quién camina a tu lado.",
        "text_en": "With a backpack full of memories and a heart full of peace, {name} began the journey back. {pet_name} walked beside them with steady steps, like a companion saying: \"Wherever you go, I go with you.\" Because the best adventures aren't measured in miles, but in who walks beside you.",
        "prompt": "Disney Pixar 3D style illustration. HUMAN: An adult ({age_display}) with {eye_desc} eyes{glasses_desc}{facial_hair_desc} walking down a mountain trail toward the valley below, wearing the backpack, peaceful satisfied expression, looking ahead with contentment, morning light behind them. PET: {pet_desc}, walking steadily beside the human on the trail at matching pace, loyal confident posture, looking ahead together, side by side. ACTION: Human and pet walk together down the mountain trail heading home, side by side as equals, a perfect image of companionship on the journey home. SETTING: Mountain trail descending WIDE VIEW, morning sunlight creating long shadows, valley and car visible far below, panoramic mountain scenery, wildflowers along the path, epic landscape. ATMOSPHERE: Fulfillment and gratitude, journey's end warmth, golden morning light, deep bond between human and pet, emotional closure. STRICT: Only ONE adult walking, ONE pet walking beside them on its own four legs, the dog always walks on its own four paws, homeward journey scene. {style}",
        "text_position": "split"
    }
]

CLOSING_SCENE = {
    "id": 20,
    "prompt": "Disney Pixar 3D style illustration. HUMAN: An adult ({age_display}) with {eye_desc} eyes{glasses_desc}{facial_hair_desc} sitting on a rock at a mountain overlook, seen from three-quarter angle, face visible with a peaceful grateful expression, warm golden sunset light on their face, backpack beside them. PET: {pet_desc}, sitting loyally beside the human on the overlook, leaning gently against the human's leg, calm happy expression, both gazing at the vast landscape below. ACTION: Human and pet sit together at a dramatic mountain overlook enjoying a spectacular golden sunset, a perfect ending to their adventure. SETTING: Dramatic mountain overlook WIDE VIEW, golden hour sky with warm orange and purple colors, vast valley and mountains below, pine trees framing the scene, epic cinematic composition. ATMOSPHERE: Epic emotional finale, golden cinematic light, deep bond and loyalty, adventure and love, perfect ending. STRICT: Only ONE adult sitting, ONE pet beside them, epic closing scene. {style}",
    "text_position": "none"
}

FRONT_COVER = {
    "prompt": "Disney Pixar 3D style illustration. HUMAN: A single {gender_word} adult ({age_display}) with {eye_desc} eyes{glasses_desc}{facial_hair_desc} standing at the beginning of a mountain trail, wearing hiking gear and backpack, excited adventurous expression, looking ahead at the mountains, confident posture. PET: {pet_desc}, standing beside the human at the trailhead, alert and ready for adventure, looking ahead, tail up, loyal confident posture. ACTION: Human and pet stand together at the start of a mountain trail ready for their great adventure, both facing the mountains ahead. SETTING: Mountain trailhead WIDE VIEW, epic mountain peaks ahead, dramatic clouds, golden light, lush forest on both sides of the trail, cinematic composition. ATMOSPHERE: Epic adventure beginning, inspirational grandeur, golden morning light, excitement and possibility. STRICT: Only ONE {gender_word} adult and ONE pet, just the {gender_word} and the pet together, centered composition for book cover. Pure illustration only, zero text or lettering. {style}"
}

BACK_COVER = {
    "prompt": "Disney Pixar 3D style illustration. SETTING: A peaceful mountain campsite scene at golden hour WIDE VIEW, an empty tent with an open flap, a pair of hiking boots beside the tent entrance, a backpack leaning against a log, a campfire with dying embers, a blanket spread on the grass, a thermos and a trail map, warm sunset light streaming through pine trees onto the objects, mountains visible in the background. ATMOSPHERE: Warm nostalgic, peaceful evening, adventure told through objects, golden warm tones, story told through belongings left behind. STRICT: Only scenery and meaningful props, pure illustration only, zero text or lettering. {style}"
}


def build_human_preview_prompt(human_desc: str) -> str:
    return f"Disney Pixar 3D style illustration. FULL BODY portrait of {human_desc}, wearing casual outdoor hiking clothes (flannel shirt, cargo pants, hiking boots), standing naturally with one hand on backpack strap, relaxed confident smile, centered in frame, occupying 60% of frame height. NEUTRAL SOLID GRADIENT BACKGROUND (soft cream to warm beige), plain studio background. Natural friendly expression, relaxed standing pose. Clean professional animation art, clean illustration only. STRICT: Character fully clothed."


def build_human_preview_prompt_with_photo(gender_word: str, age_display: str, eye_desc: str = "", hair_desc: str = "", glasses: str = "") -> str:
    glasses_part = ", wearing glasses" if glasses == "glasses" else ", wearing sunglasses" if glasses == "sunglasses" else ""
    return f"Stylized digital illustration, semi-realistic. Character of the person from @image1 ({age_display} {gender_word}{glasses_part}), {hair_desc}, {eye_desc}, wearing casual outdoor hiking clothes (flannel shirt, cargo pants, hiking boots). FULL BODY portrait, centered, relaxed confident expression, occupying 60% of frame height. NEUTRAL SOLID GRADIENT BACKGROUND (soft cream to warm beige). Clean illustration only."


def build_pet_preview_prompt(pet_desc: str) -> str:
    return f"Disney Pixar 3D style illustration. FULL BODY portrait of {pet_desc}, sitting or standing naturally, friendly expression, centered in frame, occupying 50% of frame height. NEUTRAL SOLID GRADIENT BACKGROUND (soft cream to warm beige), plain studio background. Warm lighting, expressive eyes. Clean professional animation art, clean illustration only."


def build_pet_preview_prompt_with_photo(pet_desc: str = "", pet_species: str = "dog") -> str:
    animal = "cat" if pet_species == "cat" else "dog"
    return f"Disney Pixar 3D style. 3D animated character of the {animal} from @image1. FULL BODY portrait, sitting or standing naturally, friendly expression, centered, occupying 50% of frame height. NEUTRAL SOLID GRADIENT BACKGROUND (soft cream to warm beige). Warm lighting. Clean animation art, clean illustration only."


def build_scene_prompt(scene: dict, human_desc: str, pet_name: str, pet_desc: str, age_display: str = "30 year old adult", eye_desc: str = "", gender_word: str = "person", glasses: str = "", facial_hair: str = "", **kwargs) -> str:
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
