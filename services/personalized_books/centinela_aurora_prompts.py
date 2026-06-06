# Centinela Aurora - Personalized Book Prompts
# Reference-image flow: @image1 = child character portrait, @image2 = ASTRO fox companion
#
# Prompts contain ONLY action + setting — NO character physical descriptions.
# All appearance (face, hair, skin, outfit) comes from the reference images.
#
# Reference note is prepended by generate_scene_complete:
#   "@image1=child character — copy face, hair, skin, and outfit exactly.
#    @image2=small electric-blue fox companion ASTRO — copy appearance exactly."
#
# Schema for each scene:
#   ACTION: @image1 does X. @image2 does Y.
#   SETTING: environment description WIDE VIEW.
#   ATMOSPHERE: mood.
#   {style}
#
# Rules:
#   - guidance_scale=3.5, num_inference_steps=28, aspect_ratio=3:4
#   - WIDE SHOT, characters occupy ~40% of frame, environment visible
#   - Scenes 1, 19 and CLOSING have no @image2

STYLE_BASE = "Disney Pixar 3D style, midnight blue aurora tones, electric blue and golden accents, warm magical glow, WIDE SHOT full body from head to feet, characters occupy 40% of frame, environment visible, clean illustration only, NO text, NO watermarks."

ASTRO_INLINE = (
    "ASTRO: small magical fox, kitten-sized, vibrant electric blue fur, "
    "white chest, amber-golden eyes, glowing star-tipped tail, star rope collar"
)

CENTINELA_AURORA_SCENES = [
    # ── SCENE 1 — Brújula bajo la cama (solo child) ─────────────────────────
    {
        "id": 1,
        "text_es": (
            "Una noche, mientras el mundo dormía, {name} descubrió algo asombroso bajo su cama: "
            "una brújula de oro que vibraba con un suave murmullo. Su flecha no señalaba el norte, "
            "sino que apuntaba con insistencia hacia la ventana."
        ),
        "text_en": (
            "One night, while the world slept, {name} discovered something amazing under the bed: "
            "a golden compass vibrating with a soft hum. Its arrow didn't point north—"
            "it pointed insistently toward the window."
        ),
        "prompt": (
            "ACTION: @image1 reaches under the bed and lifts a glowing golden compass, its arrow spinning and "
            "glowing with magical light, pointing toward the window, the compass illuminating @image1's amazed face. "
            "SETTING: Cozy child's bedroom at night WIDE VIEW, soft moonlight through window, books on shelves, "
            "stars visible outside, magical golden glow from the compass. "
            "ATMOSPHERE: Mystery and wonder, warm golden compass glow in the dark room. "
            "STRICT: Only @image1 in this scene. {style}"
        ),
        "text_position": "split",
    },
    # ── SCENE 2 — ASTRO aparece en el jardín ────────────────────────────────
    {
        "id": 2,
        "text_es": (
            "Al saltar al jardín, una luz azulada iluminó las flores. Era Astro, un pequeño zorro "
            "con cola de estrellas que necesitaba ayuda urgentemente. «Los sueños se están apagando, "
            "{name}», susurró con voz cristalina."
        ),
        "text_en": (
            "Jumping into the garden, a blue light lit up the flowers. It was Astro, a tiny fox "
            "with a star tail who urgently needed help. 'The dreams are fading, {name},' "
            "they whispered in a crystal-clear voice."
        ),
        "prompt": (
            "ACTION: @image1 kneels in the moonlit garden, eyes wide with surprise and delight. "
            "@image2 sits among the glowing blue flowers, star-tipped tail casting a soft electric blue glow "
            "across the garden path, meeting @image1's eyes for the very first time. "
            "SETTING: Garden at night WIDE VIEW, flowers glowing blue in @image2's magical light, "
            "moonlit garden path, magical fireflies floating. "
            "ATMOSPHERE: Magical first encounter, soft electric blue glow, wonder and excitement. {style}"
        ),
        "text_position": "split",
    },
    # ── SCENE 3 — Portal en el roble ────────────────────────────────────────
    {
        "id": 3,
        "text_es": (
            "Astro tocó el viejo roble del jardín y la corteza se transformó en un portal de nubes irisadas. "
            "{name} sintió un cosquilleo de emoción en el estómago y, sin dudarlo, "
            "tomó la pata de su nuevo amigo y saltaron juntos."
        ),
        "text_en": (
            "Astro touched the old oak tree and the bark transformed into a portal of iridescent clouds. "
            "{name} felt a tingle of excitement and, without hesitation, "
            "took their new friend's paw and they jumped together."
        ),
        "prompt": (
            "ACTION: @image1 steps bravely forward into a swirling iridescent portal in the oak tree bark, "
            "face lit with excitement, arms reaching into the swirling light. "
            "@image2 leaps through the portal entrance separately, electric blue fur blazing brilliantly "
            "in the swirling purple-blue light. "
            "SETTING: Garden at night WIDE VIEW, ancient oak tree with an open swirling iridescent portal "
            "glowing in its bark, fireflies scatter, moonlight and aurora colors. "
            "ATMOSPHERE: Brave leap of faith, magical swirling portal light, anticipation and excitement. {style}"
        ),
        "text_position": "split",
    },
    # ── SCENE 4 — Valle de los Objetos Olvidados ─────────────────────────────
    {
        "id": 4,
        "text_es": (
            "Aparecieron en el Valle de los Objetos Olvidados: un lugar inmenso donde los balones rebotaban "
            "al ritmo de una música invisible y los osos de peluche saludaban con cortesía. "
            "«Aquí descansan las cosas que los niños ya no usan», explicó Astro."
        ),
        "text_en": (
            "They arrived at the Valley of Forgotten Objects: a vast place where balls bounced to invisible music "
            "and teddy bears waved politely. 'This is where the things children no longer use come to rest,' "
            "explained Astro."
        ),
        "prompt": (
            "ACTION: @image1 walks through the vast whimsical valley, turning with a wide smile as bouncing balls "
            "and waving teddy bears greet them. "
            "@image2 trots beside @image1, electric blue tail swishing, watching the old toys wave cheerfully in welcome. "
            "SETTING: Valley of Forgotten Objects WIDE VIEW, thousands of old colorful toys everywhere, "
            "floating balloons, bouncing balls, teddy bears raising paws in greeting, soft warm golden magical light. "
            "ATMOSPHERE: Whimsical wonder, warm magical light, cheerful nostalgic surprise. {style}"
        ),
        "text_position": "split",
    },
    # ── SCENE 5 — Río de tinta + puente de tiza ──────────────────────────────
    {
        "id": 5,
        "text_es": (
            "De pronto, un río de tinta negra bloqueó su camino. {name} cerró los ojos y visualizó un puente "
            "firme con fuerza. Bajo sus pies surgió un puente de tiza blanca brillante, y cruzaron a toda prisa "
            "mientras la tinta intentaba atrapar sus sombras."
        ),
        "text_en": (
            "Suddenly, a river of black ink blocked their path. {name} closed their eyes and imagined a sturdy "
            "bridge with all their strength. A white glowing chalk bridge appeared beneath their feet, "
            "and they raced across while the ink tried to catch their shadows."
        ),
        "prompt": (
            "ACTION: @image1 sprints across a glowing chalk-white bridge that materializes beneath each running step, "
            "face set with determination, a river of thick swirling black ink churning far below. "
            "@image2 races across the glowing chalk bridge, electric blue tail streaming behind, "
            "paws barely touching the bright chalk surface. "
            "SETTING: Dark void WIDE VIEW, glowing white chalk bridge appearing from imagination above a black ink river, "
            "the bridge bright and firm, the ink dramatic below. "
            "ATMOSPHERE: Thrilling escape, imagination conquers darkness, magical white vs. dramatic black contrast. {style}"
        ),
        "text_position": "split",
    },
    # ── SCENE 6 — Bosque de páginas de libros ────────────────────────────────
    {
        "id": 6,
        "text_es": (
            "Entraron en un bosque donde las hojas de los árboles eran páginas de libros antiguos. "
            "Al caminar, {name} escuchaba los susurros de miles de historias esperando ser vividas, "
            "y el aire olía a papel y a aventura."
        ),
        "text_en": (
            "They entered a forest where the tree leaves were pages from ancient books. "
            "Walking through, {name} heard the whispers of thousands of stories waiting to be lived, "
            "and the air smelled of paper and adventure."
        ),
        "prompt": (
            "ACTION: @image1 walks through the enchanted forest, tilting their head to hear whispered stories "
            "from the glowing page-leaves, one hand reaching gently toward a floating page. "
            "@image2 pads quietly along the forest path, electric blue ears perked, listening to the rustling stories. "
            "SETTING: Enchanted book-forest WIDE VIEW, tall trees whose every leaf is a written page, "
            "loose glowing pages floating softly, warm amber light filtering through the pages. "
            "ATMOSPHERE: Mystical literary wonder, whispered stories in the air, warm amber dreamy glow. {style}"
        ),
        "text_position": "split",
    },
    # ── SCENE 7 — Biblioteca de Cristal ─────────────────────────────────────
    {
        "id": 7,
        "text_es": (
            "En el centro del bosque se alzaba la Biblioteca de Cristal, una torre que tocaba las nubes. "
            "Dentro, el Mapa de los Sueños estaba custodiado tras una vitrina que solo reaccionaba a la luz pura. "
            "Había que encontrar la manera de abrirla."
        ),
        "text_en": (
            "At the heart of the forest stood the Crystal Library, a tower touching the clouds. "
            "Inside, the Dream Map was kept behind glass that only responded to pure light. "
            "They had to find a way to open it."
        ),
        "prompt": (
            "ACTION: @image1 stands inside the Crystal Library, gazing upward in reverence, one hand pointing "
            "toward the glowing glass vitrine at the center that holds the rolled magical Dream Map. "
            "@image2 perches beside @image1 on four paws, electric-blue fox, large amber eyes reflecting rainbow light from every surrounding crystal surface. "
            "SETTING: Crystal Library interior WIDE VIEW, soaring crystal walls with glowing book shelves, "
            "central glass vitrine glowing blue with Dream Map inside, rainbow light reflections everywhere. "
            "ATMOSPHERE: Sacred wonder, crystalline magical light, mystery and reverence. {style}"
        ),
        "text_position": "split",
    },
    # ── SCENE 8 — La brújula abre la vitrina ────────────────────────────────
    {
        "id": 8,
        "text_es": (
            "{name} levantó la brújula dorada y su brillo se intensificó, proyectando colores mágicos sobre "
            "las paredes de cristal. Los cristales giraron con un sonido musical y la vitrina se abrió lentamente: "
            "¡el Mapa de los Sueños era suyo!"
        ),
        "text_en": (
            "{name} raised the golden compass and its glow intensified, projecting magical colors across the "
            "crystal walls. The crystals turned with a musical sound and the vitrine slowly opened: "
            "the Dream Map was theirs!"
        ),
        "prompt": (
            "ACTION: @image1 holds the golden compass aloft, brilliant rainbow light beams shooting from it "
            "to unlock the glowing glass vitrine, the Dream Map floating out and beginning to unroll "
            "with golden magical light. "
            "@image2 crouches on four paws a step behind, electric-blue fox, wide amber eyes watching the whole scene, glowing star-tipped tail raised with excitement. "
            "SETTING: Crystal Library WIDE VIEW, rainbow compass light beams filling the space, "
            "vitrine opening magically, dream map unfurling in mid-air. "
            "ATMOSPHERE: Triumphant discovery, brilliant colorful light, joyful victory. {style}"
        ),
        "text_position": "split",
    },
    # ── SCENE 9 — Alfombra voladora sobre el Mar de Estrellas ────────────────
    {
        "id": 9,
        "text_es": (
            "El mapa se desenrolló y se transformó en una alfombra voladora. {name} y Astro subieron de un salto "
            "y se elevaron sobre el Mar de Estrellas, donde las olas no eran de agua, sino de un polvo plateado "
            "que iluminaba el cielo nocturno."
        ),
        "text_en": (
            "The map unrolled and transformed into a flying carpet. {name} and Astro jumped on and soared above "
            "the Star Sea, where the waves were not of water but of silver dust illuminating the night sky."
        ),
        "prompt": (
            "ACTION: @image1 stands on the magical flying carpet with arms spread wide, laughing with pure joy "
            "as silver stardust waves shimmer far below. "
            "@image2 sits at the carpet's edge, glowing tail leaving a brilliant blue streak through the night air. "
            "SETTING: Night sky WIDE VIEW, magic flying carpet at altitude, below a sea of silver stardust waves "
            "glittering like the Milky Way, aurora colors in the sky, breathtaking. "
            "ATMOSPHERE: Pure freedom and joy, silver and golden magical light, breathtaking starry expanse. {style}"
        ),
        "text_position": "split",
    },
    # ── SCENE 10 — Las Pesadillas atacan ─────────────────────────────────────
    {
        "id": 10,
        "text_es": (
            "Unas nubes grises y frías, las Pesadillas, los rodearon y la alfombra empezó a tambalearse. "
            "«¡No tengas miedo!», gritó Astro. {name} recordó su momento más feliz y, al compartirlo en voz alta, "
            "una luz cálida disolvió toda la oscuridad."
        ),
        "text_en": (
            "Grey cold clouds—the Nightmares—surrounded them and the carpet began to wobble. "
            "'Don't be afraid!' shouted Astro. {name} remembered their happiest moment and, sharing it aloud, "
            "a warm light dissolved all the darkness."
        ),
        "prompt": (
            "ACTION: @image1 stands brave on the flying carpet, arms flung wide open, a burst of warm golden light "
            "radiating outward from @image1 and dissolving the menacing grey Nightmare clouds. "
            "@image2 crouches on four paws behind @image1, electric-blue fox body alert, glowing star-tipped tail blazing, ears back, amber eyes fierce. "
            "SETTING: Night sky WIDE VIEW, grey Nightmare clouds dissolving under golden light burst from @image1, "
            "magic carpet visible, aurora colors returning. "
            "ATMOSPHERE: Courage and warmth triumphing over darkness, golden light vs. grey clouds, heroic. {style}"
        ),
        "text_position": "split",
    },
    # ── SCENE 11 — Isla de la Memoria, faro parpadeante ─────────────────────
    {
        "id": 11,
        "text_es": (
            "A lo lejos apareció la Isla de la Memoria, coronada por un faro cuya luz parpadeaba débilmente. "
            "Astro bajó las orejas con tristeza. Si esa luz se apagaba, los sueños de todos los niños del mundo "
            "morirían para siempre."
        ),
        "text_en": (
            "In the distance appeared the Island of Memory, crowned by a lighthouse whose light flickered weakly. "
            "Astro lowered its ears sadly. If that light went out, the dreams of all children in the world "
            "would die forever."
        ),
        "prompt": (
            "ACTION: @image1 stands at the carpet's edge, fists clenched, eyes fixed on the distant island "
            "where a lighthouse flickers and dims dangerously, expression fierce with determination. "
            "@image2 sits beside @image1, ears drooping sadly, amber eyes reflecting the faint flickering lighthouse beam. "
            "SETTING: Night sky WIDE VIEW, distant Island of Memory with flickering lighthouse beam barely visible, "
            "starlit sea below, aurora colors, dramatic emotional stakes. "
            "ATMOSPHERE: Urgency and determination, faint flickering light in the distance, emotional weight. {style}"
        ),
        "text_position": "split",
    },
    # ── SCENE 12 — Gigante de piedra llorando ────────────────────────────────
    {
        "id": 12,
        "text_es": (
            "Un gigante de piedra bloqueaba la entrada al faro. No era malvado, sino que lloraba con amargura "
            "porque había perdido su tesoro más preciado. Sus lágrimas formaban charcos de roca líquida "
            "que bloqueaban el camino."
        ),
        "text_en": (
            "A stone giant blocked the entrance to the lighthouse. He wasn't evil, but wept bitterly because "
            "he had lost his most precious treasure. His tears formed puddles of liquid rock that blocked the path."
        ),
        "prompt": (
            "ACTION: @image1 stands at the lighthouse entrance, looking up with compassionate eyes "
            "at the weeping stone giant whose tears stream down rocky cheeks forming glowing liquid rock puddles. "
            "@image2 sits on four paws close to @image1's side, electric-blue fox, head tilted with curious amber eyes watching the giant. "
            "SETTING: Lighthouse island entrance WIDE VIEW, large stone giant, lighthouse tower behind, "
            "liquid rock pools from tears, moonlit island. "
            "ATMOSPHERE: Empathy and compassion, sad but not threatening, emotional and heartfelt. {style}"
        ),
        "text_position": "split",
    },
    # ── SCENE 13 — El dibujo, el gigante se encoge ───────────────────────────
    {
        "id": 13,
        "text_es": (
            "{name} buscó en su mochila y encontró un dibujo que había hecho esa mañana. "
            "Se lo entregó al gigante con una sonrisa sincera. El coloso, al sentirse querido, "
            "dejó de llorar y fue haciéndose cada vez más pequeño, permitiendo el paso."
        ),
        "text_en": (
            "{name} searched their backpack and found a drawing from that morning. "
            "They offered it to the giant with a sincere smile. The giant, feeling loved, "
            "stopped crying and shrank smaller and smaller, letting them through."
        ),
        "prompt": (
            "ACTION: @image1 offers a colorful crayon drawing to the shrinking stone giant who smiles through tears, "
            "warm golden light spreading from the gift. "
            "@image2 crouches on four paws nearby, electric-blue fox, star-tipped tail swishing with joy, amber eyes bright. "
            "SETTING: Lighthouse island entrance WIDE VIEW, giant now shorter as they shrink, "
            "lighthouse entrance opening behind, warm golden magical glow. "
            "ATMOSPHERE: Kindness and empathy triumphant, warm golden glow, heartwarming transformation. {style}"
        ),
        "text_position": "split",
    },
    # ── SCENE 14 — Escaleras de piano flotantes ──────────────────────────────
    {
        "id": 14,
        "text_es": (
            "Dentro del faro, las escaleras eran teclas de piano gigante que flotaban en el aire. "
            "Para subir, {name} debía saltar sobre ellas siguiendo una melodía de valentía. "
            "Cada paso emitía una nota perfecta que hacía vibrar la torre entera de alegría."
        ),
        "text_en": (
            "Inside the lighthouse, the stairs were floating giant piano keys. "
            "To climb, {name} had to jump on them following a melody of courage. "
            "Each step produced a perfect note that made the whole tower vibrate with joy."
        ),
        "prompt": (
            "ACTION: @image1 leaps joyfully between giant floating piano keys spiraling upward through the lighthouse, "
            "musical notes glowing gold in the air with each landing. "
            "@image2 bounds from piano key to piano key just ahead, glowing tail trailing a ribbon of electric blue "
            "sparkles with every leap. "
            "SETTING: Lighthouse interior WIDE VIEW, magical floating piano keys spiraling upward, "
            "glowing musical notes floating through the air, lighthouse windows showing night sky, joyful and bright. "
            "ATMOSPHERE: Playful musical magic, upward momentum, joyful energy, musical notes glowing golden. {style}"
        ),
        "text_position": "split",
    },
    # ── SCENE 15 — El Reloj de la Aurora atascado ────────────────────────────
    {
        "id": 15,
        "text_es": (
            "Al llegar a la cima, encontraron el gran Reloj de la Aurora. Sus engranajes estaban atascados "
            "por una arena gris y pesada: el aburrimiento. El tiempo de los sueños se había detenido "
            "y el silencio en la sala era absoluto."
        ),
        "text_en": (
            "Reaching the top, they found the great Aurora Clock. Its gears were stuck with grey heavy sand: "
            "boredom. Dream-time had stopped and the silence in the room was absolute."
        ),
        "prompt": (
            "ACTION: @image1 stands before the enormous Aurora Clock, leaning in with focused eyes "
            "to examine the grey sand clogging its gears, one hand reaching carefully toward a stuck gear. "
            "@image2 sits on four paws beside @image1, electric-blue fox, small snout sniffing the grey sand, large amber eyes puzzled by the silence. "
            "SETTING: Lighthouse top room WIDE VIEW, enormous Aurora Clock with gears covered in grey sand, "
            "aurora glass windows dim, night sky outside, the room beautiful but broken. "
            "ATMOSPHERE: Concerned urgency, eerie silence, broken magic, dim light needing restoration. {style}"
        ),
        "text_position": "split",
    },
    # ── SCENE 16 — Astro ilumina, el niño limpia los engranajes ─────────────
    {
        "id": 16,
        "text_es": (
            "Astro usó su cola brillante para iluminar los rincones más oscuros mientras {name}, "
            "con mucha paciencia, limpiaba los engranajes usando el cristal de su brújula. "
            "Cada uno sabía que el descanso de todos los niños del mundo dependía de ellos."
        ),
        "text_en": (
            "Astro used their glowing tail to light the darkest corners while {name}, with great patience, "
            "cleaned the gears using the compass crystal. Both knew that the rest of all the world's children "
            "depended on them."
        ),
        "prompt": (
            "ACTION: @image1 carefully removes grey sand from giant clock gears using the glowing compass "
            "crystal as a delicate tool, fingers working with quiet precision. "
            "@image2 holds its glowing tail high to light the dark corners, electric blue light steady. "
            "SETTING: Lighthouse top WIDE VIEW, massive clock gears being carefully cleaned, "
            "@image2's electric blue tail-light illuminating the space, compass crystal glowing golden, "
            "grey sand falling from the gears. "
            "ATMOSPHERE: Careful focused teamwork, intimate warm-blue light, delicate important work, "
            "quiet concentration. {style}"
        ),
        "text_position": "split",
    },
    # ── SCENE 17 — Los engranajes giran, destello multicolor ─────────────────
    {
        "id": 17,
        "text_es": (
            "Con un último esfuerzo, los engranajes empezaron a girar. El Reloj de la Aurora emitió un destello "
            "multicolor que cruzó el espacio y devolvió el color y la magia a cada rincón del universo. "
            "¡Lo habían logrado!"
        ),
        "text_en": (
            "With one final push, the gears began to turn. The Aurora Clock released a multicolored flash "
            "that crossed space, returning color and magic to every corner of the universe. They had done it!"
        ),
        "prompt": (
            "ACTION: @image1 throws both arms up in triumph as the Aurora Clock's gears spin magnificently "
            "back to life, multicolor aurora light exploding through every lighthouse window. "
            "@image2 leaps with tail raised high, electric blue fur blazing in the multicolor burst, eyes wide with jubilation. "
            "SETTING: Lighthouse top and sky WIDE VIEW, clock gears spinning with aurora colors, "
            "multicolor light burst exploding outward through all the windows, universe lighting up outside. "
            "ATMOSPHERE: Pure triumph and euphoric celebration, explosive multicolor aurora light, absolute victory. {style}"
        ),
        "text_position": "split",
    },
    # ── SCENE 18 — Despedida en el jardín ────────────────────────────────────
    {
        "id": 18,
        "text_es": (
            "El portal apareció de nuevo en el jardín de casa. {name} abrazó a Astro con fuerza, "
            "sintiendo el calor de su pelaje mágico. «Gracias, guardián», susurró el zorro. "
            "«Siempre que mires las estrellas, recuerda que tú tienes el poder de crear mundos maravillosos»."
        ),
        "text_en": (
            "The portal appeared again in the home garden. {name} hugged Astro tightly, "
            "feeling the warmth of their magical fur. 'Thank you, guardian,' whispered the fox. "
            "'Whenever you look at the stars, remember you have the power to create wonderful worlds.'"
        ),
        "prompt": (
            "ACTION: @image1 kneels in the garden giving a warm farewell embrace to @image2, "
            "eyes glistening with happy tears, the iridescent portal slowly closing behind. "
            "@image2 sits on four paws before @image1, electric-blue fox, glowing star-tipped tail bright, amber eyes full of warmth and gratitude. "
            "SETTING: Garden at night WIDE VIEW, moonlit flowers glowing softly, closing portal of iridescent "
            "clouds behind them, aurora sky above, magical and bittersweet beautiful. "
            "ATMOSPHERE: Emotional farewell, warm golden-blue glow, deep friendship and gratitude. {style}"
        ),
        "text_position": "split",
    },
    # ── SCENE 19 — El despertar (solo child) ─────────────────────────────────
    {
        "id": 19,
        "text_es": (
            "{name} despertó en su habitación mientras los primeros rayos de sol entraban por la ventana. "
            "Parecía un sueño, pero al abrir la mano, encontró una pequeña pizca de polvo de estrellas azul "
            "que brillaba suavemente. Sonrió, sabiendo que Astro siempre estaría cerca."
        ),
        "text_en": (
            "{name} woke in their room as the first rays of sun came through the window. "
            "It seemed like a dream, but opening their hand, they found a tiny pinch of glowing blue stardust. "
            "They smiled, knowing Astro would always be close."
        ),
        "prompt": (
            "ACTION: @image1 sits up in bed with first morning sunlight streaming through the window, "
            "opens their hand to reveal a tiny pinch of glowing electric blue stardust on their palm, "
            "smiling with wonder, the golden compass glowing softly on the nightstand beside them. "
            "SETTING: Child's cozy bedroom at dawn WIDE VIEW, warm golden morning light through curtains, "
            "compass glowing on nightstand, pale morning sky outside, cozy warm bed. "
            "ATMOSPHERE: Morning wonder and warmth, golden dawn light with traces of blue magic, peaceful happiness. "
            "STRICT: Only @image1 in this scene. {style}"
        ),
        "text_position": "split",
    },
]


CLOSING_SCENE = {
    "id": 20,
    "prompt": (
        "ACTION: @image1 sleeps peacefully in a cozy bed with a gentle smile, one hand open on the pillow "
        "with a faint electric blue stardust glow. "
        "SETTING: Cozy bedroom at night WIDE VIEW, soft aurora colors through window, golden compass glowing "
        "on nightstand, tiny blue fox plush toy beside it, magical and peaceful. "
        "ATMOSPHERE: Deep peaceful magical sleep, soft aurora glow, warmth and safety. "
        "STRICT: Only @image1 in this scene, no companion present. {style}"
    ),
    "text_position": "none",
}


FRONT_COVER = {
    "prompt": (
        "ACTION: @image1 stands confidently holding the golden compass high with one arm, "
        "face lit with adventurous excitement. "
        "@image2 perches on @image1's shoulder, glowing tail raised high, "
        "electric blue light blazing brilliantly against the aurora sky. "
        "SETTING: Night sky and aurora WIDE VIEW, magnificent aurora borealis colors filling the sky, "
        "stars everywhere, magical stardust floating around them, centered composition for book cover. "
        "ATMOSPHERE: Epic adventure invitation, magical aurora colors, excitement and wonder. "
        "STRICT: ABSOLUTELY NO rendered text, no titles, no logos, no words, no letters, no captions, "
        "no watermarks, no signatures, pure illustration only. {style}"
    )
}


BACK_COVER = {
    "prompt": (
        "SETTING: A magical garden at night WIDE VIEW, an ancient oak tree with a closed portal glowing softly "
        "in its bark, flowers glowing blue in the moonlight, fireflies floating, aurora colors painting the sky "
        "above, a golden compass resting on the garden path leading to the tree, magical peaceful atmosphere. "
        "STRICT: Pure scenic landscape only, no characters. "
        "ABSOLUTELY NO rendered text anywhere in the image, no titles, no logos, no words, no letters, "
        "no captions, no watermarks, no signatures, pure illustration only. {style}"
    )
}


def get_outfit_desc(gender: str) -> str:
    if gender == "male":
        return "dark navy explorer jacket, dark cargo pants, white sneakers, golden compass on cord"
    else:
        return "dark navy explorer jacket, dark leggings, white sneakers, golden compass on cord"


def get_hair_action(traits: dict) -> str:
    hair_length = traits.get("hair_length", "medium")
    hair_type = traits.get("hair_type", "straight")
    if hair_length in ("bald", "very_little", "very_short"):
        return "short hair neat and still"
    if hair_type == "curly":
        return "curly hair bouncing"
    if hair_type == "wavy":
        return "wavy hair catching the light"
    return "hair gently lifted by the breeze"


def build_scene_prompt(scene: dict, child_name: str, gender: str, age: int, traits: dict, has_photo: bool = False) -> str:
    """Build scene prompt using @image1/@image2 reference format.
    Prompts contain only action + setting — no character descriptions.
    Physical appearance comes entirely from reference images.
    """
    raw_prompt = scene.get('prompt', '')
    prompt = raw_prompt.replace('{style}', STYLE_BASE)
    prompt = prompt.replace('{name}', child_name)
    prompt = prompt.replace('{child_name}', child_name)
    return prompt


def get_cover_prompts(child_name: str, gender: str, age: int, traits: dict) -> dict:
    return {
        'front': build_scene_prompt(FRONT_COVER, child_name, gender, age, traits),
        'back': build_scene_prompt(BACK_COVER, child_name, gender, age, traits)
    }


def get_all_scene_prompts(child_name: str, gender: str, age: int, traits: dict) -> list:
    prompts = []
    for scene in CENTINELA_AURORA_SCENES:
        prompts.append(build_scene_prompt(scene, child_name, gender, age, traits))
    return prompts
