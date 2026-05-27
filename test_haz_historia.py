"""
Haz tu Historia — Pipeline de Prueba: Un Día en Creta con Alex
===============================================================
Dos pasos de ejecución:
  Paso 1 — Solo textos:   python3 test_haz_historia.py --texts
  Paso 2 — Todo:          python3 test_haz_historia.py --generate
                          python3 test_haz_historia.py --generate --pdf-only  (si imágenes ya están)

Costo estimado: ~$0.60-0.80 en APIs (OpenAI + Replicate)
Tiempo estimado: ~15-20 minutos (solo imágenes ~12 min)
"""

import os
import sys
import json
import time
import textwrap
import argparse
import requests
import httpx
import replicate
from io import BytesIO
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from openai import OpenAI

# ─── DATOS DEL CUENTO ────────────────────────────────────────────────────────

STORY_DATA = {
    "titulo": "Un Día en Creta con Alex",
    "idioma": "es",
    "tipo": "hechos_reales",
    "tono": "calido_tierno",
    "proposito": "valorar_familia",
    "dedicatoria": "Para mi Alex con todo cariño, para que siempres recuerdes que el amor y el compartir en familia, son el mejor regalo. Tu Abu Isa.",

    "escenario": "La isla de Creta, Grecia. Una casita aislada rodeada de olivos cerca del mar, con una playa tranquila, un espigón donde rompen las olas suaves, y un acogedor restaurante junto al mar.",
    "arranque": "Abu Isa fue a buscar a Alex a primera hora de la mañana. Estaba muy emocionada de pasar un día especial a solas con su nieto en una casita rodeada de olivos cerca del mar de Creta. Se pusieron el bañador y bajaron juntos a la playa.",
    "desafio": "En la playa había pequeñas reservas de huevos de tortugas marinas, cercadas con barandas de madera, que llamaron mucho la atención de Alex. Luego, en el espigón donde rompían las olas, Alex tenía miedo de que las olas lo tumbaran, pero cuando llegó la ola, solo cayó como una llovizna y él se rió a carcajadas. De regreso a la casita, en la puerta había dos gatos y Alex les tenía miedo. Abu Isa le explicó: 'Tú eres más grande, si les dices shhhhh, ellos se asustan y se van.' Alex lo intentó y funcionó.",
    "momento_especial": "El momento más emocionante fue en el espigón: Alex cerró los ojos con miedo cuando llegó la ola, pero en lugar de tumbarlos, los mojó apenas como una gotita de lluvia. Alex abrió los ojos sorprendido y soltó una carcajada enorme. Ese instante de miedo convertido en alegría fue mágico. También fue especial cuando Abu Isa y Alex jugaron con sus sombras al atardecer, como si fueran gigantes.",
    "cierre": "Durmieron juntos en la misma cama, como pidió Alex. Al día siguiente, al reencontrarse con papá Elie y su mamá, Alex no podía parar de contar todo: las tortugas, la ola, los gatos y las sombras gigantes. Ese día Alex aprendió que las cosas que dan miedo muchas veces terminan siendo las más divertidas.",
}

CHARACTERS = [
    {
        "id": "char_alex",
        "nombre": "Alex",
        "edad": 3,
        "pelo": "light brown hair, very short crew cut",
        "ojos": "green",
        "piel": "fair white skin",
        "rasgos": "big bright smile, chubby cheeks, sweet and curious expression",
        "outfit_tierra": "red shorts and a superhero t-shirt, white sneakers",
        "outfit_playa": "blue swim trunks",
        "outfit": "red shorts and a superhero t-shirt",
        "personalidad": "curious, intelligent, brave little boy",
        "es_protagonista": True,
        "foto_path": "generated/hth_test/photo_alex_clean.jpg",
    },
    {
        "id": "char_isa",
        "nombre": "Abu Isa",
        "edad": 45,
        "pelo": "medium-length wavy light brown hair with blonde highlights",
        "ojos": "green",
        "piel": "light Mediterranean skin",
        "rasgos": "warm beautiful smile, mature elegant woman, natural graceful aging",
        "outfit_tierra": "floral spaghetti-strap summer dress",
        "outfit_playa": "white one-piece swimsuit",
        "outfit": "floral spaghetti-strap summer dress",
        "personalidad": "loving, warm, adventurous grandmother",
        "es_protagonista": False,
        "foto_path": "generated/hth_test/photo_isa_clean.jpg",
    },
    {
        "id": "char_elie",
        "nombre": "Papá Elie",
        "edad": 37,
        "pelo": "dark brown hair, short",
        "ojos": "brown",
        "piel": "fair white skin",
        "rasgos": "short dark beard, friendly warm smile",
        "outfit": "blue shorts, white t-shirt, black cap",
        "personalidad": "brave, loving father",
        "es_protagonista": False,
        "foto_path": "generated/hth_test/photo_elie_clean.jpg",
    },
]

# ─── CONFIGURACIÓN TÉCNICA ────────────────────────────────────────────────────

OUTPUT_DIR = "generated/hth_test"
FONT_TEXT   = "static/fonts/EBGaramond-Regular.ttf"
FONT_TITLE  = "static/fonts/BukhariScript.ttf"
FONT_BOLD   = "static/fonts/Nunito-ExtraBold.ttf"

DPI = 150
PAGE_W_PX = round(210 * DPI / 25.4)
PAGE_H_PX = round(297 * DPI / 25.4)

FLUX2_MODEL   = "black-forest-labs/flux-2-dev"
KONTEXT_MODEL = "black-forest-labs/flux-kontext-pro"
PULID_VERSION = "8baa7ef2255075b46f4d91cd238c21d31181b3e6a864463f967960bb0112525b"

MAX_RETRIES = 3
RETRY_DELAY = 8

# ─── CLIENTES ─────────────────────────────────────────────────────────────────

openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
replicate_client = replicate.Client(
    timeout=httpx.Timeout(connect=30.0, read=300.0, write=120.0, pool=30.0)
)

# ─── PASO 1: GPT-4o genera textos ────────────────────────────────────────────

SYSTEM_PROMPT = """Eres un autor experto en libros ilustrados infantiles sobre historias familiares reales y emotivas.
Tu tarea es convertir los datos de esta historia en exactamente 10 escenas cortas, tiernas y aventureras, de entre 80 y 100 palabras cada una.
El tono debe ser cálido, tierno y con toques de aventura. El mensaje central es valorar el compartir en familia.
El protagonista principal es Alex (3 años). Los personajes son Alex, Abu Isa y Papá Elie.

REGLAS OBLIGATORIAS:
- Devuelve ÚNICAMENTE un JSON válido. Sin texto antes ni después.
- Exactamente 10 escenas: escena_1 hasta escena_10.
- Cada escena tiene:
    "texto": string de 80-100 palabras en español, narrado en tercera persona, cálido y adecuado para niños de 3-5 años
    "personajes_presentes": lista de IDs — exactamente los que aparecen activamente en la escena
    "emocion": 3-5 palabras que describen el sentimiento de la escena
    "titulo_escena": título corto de 3-5 palabras para la escena
- IDs de personajes: ["char_alex", "char_isa", "char_elie"]
- Alex (char_alex) aparece en todas las 10 escenas.
- Abu Isa (char_isa) aparece en escenas 1-9.
- Papá Elie (char_elie) aparece solo en escenas 1 y 10.
- Distribuye los momentos así:
    Escena 1: Abu Isa busca a Alex — reencuentro emocionante (con Elie al fondo despidiéndose)
    Escena 2: Llegada a la casita de olivos
    Escena 3: Bajando a la playa con bañador
    Escena 4: Las reservas de huevos de tortugas — asombro de Alex
    Escena 5: El espigón — el miedo de Alex antes de la ola
    Escena 6: La ola llega y solo los moja como llovizna — Alex se ríe a carcajadas (CLÍMAX)
    Escena 7: Los gatos en la puerta — Abu Isa enseña a Alex a no tenerles miedo
    Escena 8: La siesta y salida a explorar — chicharras y juego de sombras
    Escena 9: La cena en el restaurante (había carritos de juguete y una pelota — Alex jugó mucho) y luego de regreso a casa, Alex pidió dormir en la cama de Abu Isa
    Escena 10: Al día siguiente, Alex cuenta toda la aventura a Papá Elie y su mamá"""


USER_PROMPT = f"""Historia: {STORY_DATA['titulo']}

ESCENARIO: {STORY_DATA['escenario']}
ARRANQUE: {STORY_DATA['arranque']}
DESAFÍO: {STORY_DATA['desafio']}
MOMENTO ESPECIAL: {STORY_DATA['momento_especial']}
CIERRE: {STORY_DATA['cierre']}

Personajes:
- char_alex: Alex, 3 años, niño curioso e inteligente con una sonrisa enorme
- char_isa: Abu Isa, abuela cariñosa y aventurera, luce muy joven y radiante
- char_elie: Papá Elie, papá valiente y amoroso

Genera los 10 textos en JSON."""


def generate_scene_texts(save_path: str) -> dict:
    if os.path.exists(save_path):
        print(f"[GPT] Cargando textos guardados: {save_path}")
        with open(save_path) as f:
            return json.load(f)

    print("[GPT] Generando 10 textos de escena con GPT-4o...")
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT}
        ]
    )
    result = json.loads(response.choices[0].message.content)
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"[GPT] Textos guardados: {save_path}")
    return result


# ─── PASO 1b: GPT-4o genera descriptores visuales (ACTION + SETTING en inglés) ─

VISUAL_SYSTEM_PROMPT = """You are a professional children's book art director.
Given Spanish story scene texts and a character map, return visual descriptors for each scene so an AI image model can illustrate them.

RULES:
- Return ONLY valid JSON. No text before or after.
- Exactly 10 entries: escena_1 through escena_10.
- Each entry has these fields:
    "action": string — physical action/pose in English, max 20 words, concrete and visual.
              Use generic role labels from the character map (character_1, character_2, etc.) — NEVER use proper names.
              Example: "character_1 crouches and points excitedly at small wooden turtle nest fences on the sand"
    "setting": string — environment in English, max 20 words.
              Example: "sunny Mediterranean beach, golden sand, calm blue sea, olive grove in background"
    "animals_present": list of animal type strings visible in the scene. Use plural lowercase.
              Example: ["cats"] or ["sea turtles"] or [] if none.
    "animals_description": string — if animals are present, describe them visually in English (appearance, position, behavior).
              Example: "two friendly stray cats sitting by the stone doorstep, one orange, one grey"
              Use empty string "" if no animals.
- ACTION must describe ONLY physical actions — never paraphrase the narrative text.
- Characters must always be referenced by their generic label (character_1, character_2, etc.), never by name."""


def generate_visual_descriptors(escenas: dict, save_path: str) -> dict:
    if os.path.exists(save_path):
        print(f"[GPT-V] Cargando descriptores visuales: {save_path}")
        with open(save_path) as f:
            return json.load(f)

    print("[GPT-V] Generando descriptores visuales (Paso 2 — inglés ACTION+SETTING)...")

    # Mapa genérico: char_id → character_N (independiente del nombre real)
    char_map = {char["id"]: f"character_{i+1}" for i, char in enumerate(CHARACTERS)}
    char_map_display = {v: char["nombre"] for char, v in
                        zip(CHARACTERS, char_map.values())}

    scenes_summary = {}
    for i in range(1, 11):
        key = f"escena_{i}"
        esc = escenas.get(key, {})
        # Convertir IDs a etiquetas genéricas
        generic_chars = [char_map.get(cid, cid) for cid in esc.get("personajes_presentes", [])]
        scenes_summary[key] = {
            "titulo": esc.get("titulo_escena", ""),
            "texto": esc.get("texto", ""),
            "characters_present": generic_chars,
        }

    user_msg = (
        f"Character map: {json.dumps(char_map_display, ensure_ascii=False)}\n"
        f"Setting: {STORY_DATA['escenario']}\n\n"
        f"Scenes:\n{json.dumps(scenes_summary, ensure_ascii=False, indent=2)}\n\n"
        "Generate visual descriptors for all 10 scenes."
    )

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": VISUAL_SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ]
    )
    result = json.loads(response.choices[0].message.content)
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"[GPT-V] Descriptores guardados: {save_path}")
    return result


# ─── PASO 2: Generar previews de personajes ───────────────────────────────────

def get_kontext_preview_prompt(char: dict) -> str:
    """Prompt Kontext Pro — convierte la foto real a Disney Pixar 3D."""
    edad_display = f"{char['edad']} years old"
    rasgos = char.get("rasgos", "")
    return (
        f"Disney Pixar 3D CGI style illustration of the exact person in the photo. "
        f"Keep the exact same face, hair color, hair style, eye color, and skin tone from the photo. "
        f"{char['nombre']}, {edad_display}. {rasgos}. "
        f"OUTFIT: {char['outfit']}. "
        f"Friendly warm expression, soft studio lighting. "
        f"Disney Pixar 3D style, high quality, warm colors. "
        f"Pure illustration only, no text, no watermarks."
    )


def get_pulid_preview_prompt(char: dict) -> str:
    """Prompt PuLID — para adultos mayores de 12."""
    rasgos = char.get("rasgos", "")
    return (
        f"Disney Pixar 3D CGI style illustration. "
        f"{char['nombre']}, {char['pelo']}, {char['ojos']} eyes, {char['piel']}. "
        f"{rasgos}. "
        f"OUTFIT: {char['outfit']}. "
        f"Friendly warm expression, soft lighting. "
        f"Disney Pixar 3D style, warm colors. "
        f"Pure illustration only."
    )


def download_image(url: str) -> Image.Image:
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    return Image.open(BytesIO(resp.content)).convert("RGB")


def save_image_from_output(output, save_path: str) -> str:
    """Save FLUX/Kontext output to disk.
    FileOutput is both iterable (byte stream) AND has .url — NEVER iterate it, use .url directly.
    """
    from replicate.helpers import FileOutput

    # FileOutput: use .url directly — do NOT iterate (would consume byte stream)
    if isinstance(output, FileOutput):
        url = output.url
        img = download_image(url)
        img.save(save_path, "PNG")
        return save_path

    # List of FileOutput or strings
    if isinstance(output, list):
        item = output[0]
        if isinstance(item, FileOutput):
            img = download_image(item.url)
            img.save(save_path, "PNG")
            return save_path
        url = str(item)
        if url.startswith("http"):
            img = download_image(url)
            img.save(save_path, "PNG")
            return save_path

    # Plain URL string
    url = str(output)
    if url.startswith("http"):
        img = download_image(url)
        img.save(save_path, "PNG")
        return save_path

    raise Exception(f"Cannot save image from output type: {type(output)}")


def generate_character_preview(char: dict, save_path: str) -> str:
    if os.path.exists(save_path):
        print(f"[PREVIEW] Usando guardado: {save_path}")
        return save_path

    edad = char["edad"]
    foto = char["foto_path"]
    print(f"\n[PREVIEW] Generando preview de {char['nombre']} (edad {edad}, {'Kontext' if edad <= 12 else 'PuLID'})...")

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            if edad <= 12:
                prompt = get_kontext_preview_prompt(char)
                with open(foto, "rb") as f:
                    output = replicate_client.run(
                        KONTEXT_MODEL,
                        input={
                            "prompt": prompt,
                            "input_image": f,
                            "aspect_ratio": "3:4",
                            "output_format": "png",
                        }
                    )
            else:
                prompt = get_pulid_preview_prompt(char)
                with open(foto, "rb") as f:
                    output = replicate_client.run(
                        f"zsxkib/flux-pulid:{PULID_VERSION}",
                        input={
                            "prompt": prompt,
                            "main_face_image": f,
                            "id_weight": 0.8,
                            "start_step": 0,
                            "num_steps": 20,
                            "width": 768,
                            "height": 1024,
                            "output_format": "png",
                            "num_outputs": 1,
                            "guidance_scale": 4.0,
                        }
                    )

            save_image_from_output(output, save_path)
            print(f"[PREVIEW] Guardado: {save_path}")
            return save_path

        except Exception as e:
            print(f"[PREVIEW] Error attempt {attempt}: {str(e)[:250]}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY + attempt * 3)
            else:
                raise


# ─── PASO 3: Generar ilustraciones de escena ──────────────────────────────────

# Mapa de outfits por escena (playa vs tierra)
BEACH_SCENES = {3, 4, 5, 6}   # escenas donde están en la playa/bañador

def get_outfit_for_scene(char: dict, scene_num: int) -> str:
    if scene_num in BEACH_SCENES:
        return char.get("outfit_playa", char["outfit"])
    return char.get("outfit_tierra", char["outfit"])


# Negative prompt base — suprimir rasgos animales en personajes humanos
_NEG_BASE = (
    "fox tail, dragon tail, bunny tail, cat tail, animal tail, animal ears, "
    "animal features on human, fur on human, whiskers on human, snout on human, "
    "paws on human, wings on human, multiple heads, extra limbs, deformed, "
    "blurry, watermark, text, logo"
)
_NEG_MALE_EXTRA   = "earrings on male character, hair bows on male character, ribbons in male hair"
_NEG_FEMALE_EXTRA = "boy haircut on female character"

def get_scene_negative_prompt(presentes: list, animals: list = None) -> str:
    parts = [_NEG_BASE]
    ids = {c["id"] for c in presentes}
    if ids & {"char_alex", "char_elie"}:
        parts.append(_NEG_MALE_EXTRA)
    if "char_isa" in ids:
        parts.append(_NEG_FEMALE_EXTRA)
    if animals:
        for animal in animals:
            a = animal.lower().rstrip("s")  # "cats" → "cat"
            parts.append(f"{a} features on humans, {a} tail on humans, {a} ears on humans")
    return ", ".join(parts)


def build_scene_image_prompt(scene_num: int, presentes: list, visual: dict) -> str:
    """Schema maestro: CHARACTER → OUTFIT → ACTION → SETTING → ATMOSPHERE → STRICT
    Los descriptores visuales usan etiquetas genéricas (character_1, character_2, ...).
    Aquí se sustituyen por @image1, @image2, ... para que FLUX identifique las referencias.
    """
    char_blocks = []
    for i, char in enumerate(presentes, 1):
        outfit = get_outfit_for_scene(char, scene_num)
        char_blocks.append(
            f"@image{i} is {char['nombre']}, {char['pelo']}, "
            f"{char['ojos']} eyes, {char['piel']}. "
            f"OUTFIT: {outfit}."
        )

    chars_str = " ".join(char_blocks)
    if len(presentes) > 1:
        chars_str += " These are completely separate and distinct people."

    # Reemplazar etiquetas genéricas por referencias FLUX (@imageN)
    action = visual.get("action", "characters interact in a warm outdoor scene")
    for i, char in enumerate(presentes, 1):
        action = action.replace(f"character_{i}", f"@image{i}")

    setting = visual.get("setting", "sunny Mediterranean landscape")

    # Descripción positiva de animales presentes en la escena
    animals_desc = visual.get("animals_description", "").strip()
    scene_elements = f"SCENE ELEMENTS: {animals_desc}. " if animals_desc else ""

    return (
        f"Disney Pixar 3D CGI style illustration. "
        f"{chars_str} "
        f"ACTION: {action}. "
        f"SETTING: {setting}. WIDE VIEW. "
        f"{scene_elements}"
        f"ATMOSPHERE: warm Mediterranean sunlight, golden hour, vibrant colors, soft shadows. "
        f"STRICT: 100% human characters, pure illustration only."
    )


def generate_scene_image(scene_num: int, escena: dict, visual: dict,
                         preview_paths: dict, save_path: str) -> str:
    if os.path.exists(save_path):
        print(f"[SCENE {scene_num}] Usando guardada: {save_path}")
        return save_path

    presentes_ids = escena.get("personajes_presentes", ["char_alex", "char_isa"])
    presentes = [c for c in CHARACTERS if c["id"] in presentes_ids]
    present_previews = [preview_paths[c["id"]] for c in presentes
                        if c["id"] in preview_paths and os.path.exists(preview_paths[c["id"]])]

    animals = visual.get("animals_present", [])
    prompt   = build_scene_image_prompt(scene_num, presentes, visual)
    neg_prompt = get_scene_negative_prompt(presentes, animals)

    print(f"\n[SCENE {scene_num}/10] {escena.get('titulo_escena','...')} — personajes: {[c['nombre'] for c in presentes]}")
    print(f"  ACTION:  {visual.get('action','—')}")
    print(f"  ANIMALS: {animals or 'ninguno'}")
    print(f"  Prompt ({len(prompt)} chars): {prompt[:100]}...")

    for attempt in range(1, MAX_RETRIES + 1):
        opened = []
        try:
            fresh_refs = []
            for p in present_previews:
                f = open(p, "rb")
                opened.append(f)
                fresh_refs.append(f)

            output = replicate_client.run(
                FLUX2_MODEL,
                input={
                    "prompt": prompt,
                    "negative_prompt": neg_prompt,
                    "input_images": fresh_refs,
                    "image_prompt_strength": 0.85,
                    "aspect_ratio": "3:4",
                    "output_format": "png",
                    "go_fast": True,
                }
            )

            save_image_from_output(output, save_path)
            print(f"[SCENE {scene_num}] Guardada: {save_path}")
            return save_path

        except Exception as e:
            print(f"[SCENE {scene_num}] Error attempt {attempt}: {str(e)[:250]}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY + attempt * 3)
            else:
                raise
        finally:
            for f in opened:
                try:
                    f.close()
                except:
                    pass


# ─── PASO 4: Ensamblar PDF ────────────────────────────────────────────────────

def load_font(path: str, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(path, size)
    except:
        return ImageFont.load_default()


def make_text_page(texto: str, scene_num: int, titulo_escena: str = "") -> Image.Image:
    img = Image.new("RGB", (PAGE_W_PX, PAGE_H_PX), "#FDFAF6")
    draw = ImageDraw.Draw(img)

    margin_x = int(PAGE_W_PX * 0.11)
    text_width = PAGE_W_PX - 2 * margin_x
    top_reserve = int(PAGE_H_PX * 0.14)

    font_header = load_font(FONT_BOLD, int(PAGE_H_PX * 0.019))
    font_subtitle = load_font(FONT_TEXT, int(PAGE_H_PX * 0.022))
    font_body = load_font(FONT_TEXT, int(PAGE_H_PX * 0.030))
    font_page = load_font(FONT_TEXT, int(PAGE_H_PX * 0.018))

    # Header line
    header_y = int(PAGE_H_PX * 0.05)
    draw.text((margin_x, header_y), STORY_DATA["titulo"].upper(),
              font=font_header, fill="#BBBBBB")
    line_y = header_y + int(PAGE_H_PX * 0.042)
    draw.line([(margin_x, line_y), (PAGE_W_PX - margin_x, line_y)],
              fill="#DDDDDD", width=1)

    # Título de escena
    if titulo_escena:
        draw.text((margin_x, line_y + int(PAGE_H_PX * 0.018)),
                  titulo_escena, font=font_subtitle, fill="#777777")

    # Texto del cuento
    chars_per_line = max(30, int(text_width / (font_body.size * 0.52)))
    wrapped = textwrap.wrap(texto, width=chars_per_line)
    y = top_reserve
    line_height = int(font_body.size * 1.75)
    for line in wrapped:
        draw.text((margin_x, y), line, font=font_body, fill="#1A1A1A")
        y += line_height

    # Número de página
    page_num = str(scene_num * 2 + 4)
    draw.text((margin_x, PAGE_H_PX - int(PAGE_H_PX * 0.055)),
              page_num, font=font_page, fill="#BBBBBB")

    return img


def make_title_page() -> Image.Image:
    img = Image.new("RGB", (PAGE_W_PX, PAGE_H_PX), "#FDFAF6")
    draw = ImageDraw.Draw(img)

    font_titulo = load_font(FONT_TITLE, int(PAGE_H_PX * 0.055))
    font_sub = load_font(FONT_TEXT, int(PAGE_H_PX * 0.024))
    font_mmb = load_font(FONT_TEXT, int(PAGE_H_PX * 0.019))

    center_y = int(PAGE_H_PX * 0.36)
    for size_off, color in [(3, "#DDCCFF"), (0, "#2E1A47")]:
        bbox = draw.textbbox((0, 0), STORY_DATA["titulo"], font=font_titulo)
        w = bbox[2] - bbox[0]
        draw.text(((PAGE_W_PX - w) // 2 + size_off, center_y + size_off),
                  STORY_DATA["titulo"], font=font_titulo, fill=color)

    sub = "Alex · Abu Isa · Papá Elie"
    sub_y = center_y + int(PAGE_H_PX * 0.10)
    bbox2 = draw.textbbox((0, 0), sub, font=font_sub)
    w2 = bbox2[2] - bbox2[0]
    draw.text(((PAGE_W_PX - w2) // 2, sub_y), sub, font=font_sub, fill="#888888")

    for lx in [0.25, 0.75]:
        draw.line([(int(PAGE_W_PX * lx), sub_y + int(PAGE_H_PX * 0.055)),
                   (int(PAGE_W_PX * (1 - lx + 0.25 - 0.5 * (lx == 0.75))),
                    sub_y + int(PAGE_H_PX * 0.055))],
                  fill="#DDDDDD", width=1)

    mmb = "Magic Memories Books"
    bbox3 = draw.textbbox((0, 0), mmb, font=font_mmb)
    w3 = bbox3[2] - bbox3[0]
    draw.text(((PAGE_W_PX - w3) // 2, int(PAGE_H_PX * 0.88)),
              mmb, font=font_mmb, fill="#BBBBBB")
    return img


def make_dedication_page() -> Image.Image:
    img = Image.new("RGB", (PAGE_W_PX, PAGE_H_PX), "#FDFAF6")
    draw = ImageDraw.Draw(img)

    font_ded = load_font(FONT_TEXT, int(PAGE_H_PX * 0.030))
    font_label = load_font(FONT_BOLD, int(PAGE_H_PX * 0.018))

    margin_x = int(PAGE_W_PX * 0.15)
    center_y = int(PAGE_H_PX * 0.35)
    text_width = PAGE_W_PX - 2 * margin_x

    draw.line([(int(PAGE_W_PX * 0.28), center_y - int(PAGE_H_PX * 0.065)),
               (int(PAGE_W_PX * 0.72), center_y - int(PAGE_H_PX * 0.065))],
              fill="#DDDDDD", width=1)

    label = "Con todo el amor:"
    bbox = draw.textbbox((0, 0), label, font=font_label)
    w = bbox[2] - bbox[0]
    draw.text(((PAGE_W_PX - w) // 2, center_y - int(PAGE_H_PX * 0.048)),
              label, font=font_label, fill="#AAAAAA")

    chars_per_line = max(30, int(text_width / (font_ded.size * 0.52)))
    wrapped = textwrap.wrap(STORY_DATA["dedicatoria"], width=chars_per_line)
    y = center_y
    for line in wrapped:
        bbox2 = draw.textbbox((0, 0), line, font=font_ded)
        w2 = bbox2[2] - bbox2[0]
        draw.text(((PAGE_W_PX - w2) // 2, y), line, font=font_ded, fill="#333333")
        y += int(font_ded.size * 1.85)

    draw.line([(int(PAGE_W_PX * 0.28), y + int(PAGE_H_PX * 0.03)),
               (int(PAGE_W_PX * 0.72), y + int(PAGE_H_PX * 0.03))],
              fill="#DDDDDD", width=1)
    return img


def make_credits_page() -> Image.Image:
    img = Image.new("RGB", (PAGE_W_PX, PAGE_H_PX), "#FDFAF6")
    draw = ImageDraw.Draw(img)
    font = load_font(FONT_TEXT, int(PAGE_H_PX * 0.022))

    lines = [
        STORY_DATA["titulo"],
        "",
        "Creado con Magic Memories Books",
        "magicmemoriesbooks.com",
        "",
        "Texto e ilustraciones generados con inteligencia artificial",
        "Supervisados y editados con cariño",
        "",
        "© 2026 Magic Memories Books",
        "Todos los derechos reservados.",
    ]
    y = int(PAGE_H_PX * 0.34)
    for line in lines:
        if line:
            bbox = draw.textbbox((0, 0), line, font=font)
            w = bbox[2] - bbox[0]
            draw.text(((PAGE_W_PX - w) // 2, y), line, font=font, fill="#666666")
        y += int(font.size * 1.95)
    return img


def fit_image_to_page(img_path: str) -> Image.Image:
    from PIL import ImageOps
    img = Image.open(img_path).convert("RGB")
    return ImageOps.fit(img, (PAGE_W_PX, PAGE_H_PX), Image.Resampling.LANCZOS)


def assemble_pdf(escenas: dict, scene_image_paths: list, output_path: str):
    print(f"\n[PDF] Ensamblando PDF: {output_path}")
    pages = []

    pages.append(Image.new("RGB", (PAGE_W_PX, PAGE_H_PX), "#F5F0EB"))  # P2 blanco
    pages.append(make_title_page())                                      # P3 portadilla
    pages.append(Image.new("RGB", (PAGE_W_PX, PAGE_H_PX), "#F5F0EB"))  # P4 blanco
    pages.append(make_dedication_page())                                 # P5 dedicatoria

    for i in range(1, 11):
        key = f"escena_{i}"
        escena = escenas.get(key, {})
        texto = escena.get("texto", f"Escena {i}.")
        titulo_escena = escena.get("titulo_escena", "")
        img_path = scene_image_paths[i - 1] if (i - 1) < len(scene_image_paths) else None

        # Pág texto (izquierda)
        pages.append(make_text_page(texto, i, titulo_escena))

        # Pág imagen (derecha)
        if img_path and os.path.exists(img_path):
            pages.append(fit_image_to_page(img_path))
        else:
            ph = Image.new("RGB", (PAGE_W_PX, PAGE_H_PX), "#EEEEEE")
            d = ImageDraw.Draw(ph)
            fnt = load_font(FONT_TEXT, 38)
            d.text((PAGE_W_PX // 2 - 90, PAGE_H_PX // 2),
                   f"[Ilustración {i}]", font=fnt, fill="#BBBBBB")
            pages.append(ph)

    pages.append(make_credits_page())                                    # P26 créditos
    pages.append(Image.new("RGB", (PAGE_W_PX, PAGE_H_PX), "#F5F0EB"))  # P27 blanco

    first = pages[0].convert("RGB")
    rest = [p.convert("RGB") for p in pages[1:]]
    first.save(output_path, save_all=True, append_images=rest, format="PDF")
    print(f"[PDF] ✅ Guardado: {output_path} ({len(pages)+1} págs incluyendo cubierta)")


# ─── FLUJO PRINCIPAL ──────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Haz tu Historia — Pipeline de Prueba")
    parser.add_argument("--texts", action="store_true", help="Solo genera y muestra textos GPT-4o")
    parser.add_argument("--generate", action="store_true", help="Pipeline completo (textos + imágenes + PDF)")
    parser.add_argument("--pdf-only", action="store_true", help="Solo ensambla el PDF con imágenes ya generadas")
    args = parser.parse_args()

    if not args.texts and not args.generate and not args.pdf_only:
        print("Uso:")
        print("  python3 test_haz_historia.py --texts       # Solo textos GPT")
        print("  python3 test_haz_historia.py --generate    # Pipeline completo")
        print("  python3 test_haz_historia.py --pdf-only    # Solo PDF con imágenes existentes")
        sys.exit(0)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    texts_path   = f"{OUTPUT_DIR}/scene_texts.json"
    visuals_path = f"{OUTPUT_DIR}/scene_visuals.json"

    print("=" * 65)
    print(f"  HAZ TU HISTORIA — {STORY_DATA['titulo']}")
    print("=" * 65)

    # Paso 1: Textos en español
    escenas = generate_scene_texts(texts_path)

    # Mostrar textos
    print("\n" + "=" * 65)
    print("  TEXTOS GENERADOS:")
    print("=" * 65)
    for i in range(1, 11):
        key = f"escena_{i}"
        esc = escenas.get(key, {})
        emocion = esc.get("emocion", "")
        if isinstance(emocion, list):
            emocion = ", ".join(emocion)
        print(f"\n[Escena {i}] {esc.get('titulo_escena','')}")
        print(f"  Personajes: {esc.get('personajes_presentes', [])}")
        print(f"  Emoción:    {emocion}")
        print(f"  Texto:      {esc.get('texto','')[:120]}...")

    if args.texts:
        # Paso 1b también en modo --texts para validar descriptores visuales
        visuals = generate_visual_descriptors(escenas, visuals_path)
        print("\n" + "=" * 65)
        print("  DESCRIPTORES VISUALES (inglés — para FLUX):")
        print("=" * 65)
        for i in range(1, 11):
            key = f"escena_{i}"
            v = visuals.get(key, {})
            animals_desc = v.get('animals_description', '')
            print(f"\n[Escena {i}]")
            print(f"  ACTION:  {v.get('action','—')}")
            print(f"  SETTING: {v.get('setting','—')}")
            print(f"  ANIMALS: {v.get('animals_present', [])}")
            if animals_desc:
                print(f"  ANIMALS DESC: {animals_desc}")
        print(f"\n✅ Textos: {texts_path}")
        print(f"✅ Visuals: {visuals_path}")
        print("   Revísalos y ejecuta --generate para continuar con las imágenes.")
        return

    # Paso 1b: Descriptores visuales en inglés
    visuals = generate_visual_descriptors(escenas, visuals_path)

    if args.pdf_only:
        scene_image_paths = [f"{OUTPUT_DIR}/scene_{i:02d}.png" for i in range(1, 11)]
        output_pdf = f"{OUTPUT_DIR}/Un_Dia_en_Creta_con_Alex.pdf"
        assemble_pdf(escenas, scene_image_paths, output_pdf)
        return

    # Pipeline completo
    print("\n[INFO] Generando previews de personajes...")
    preview_paths = {}
    for char in CHARACTERS:
        preview_save = f"{OUTPUT_DIR}/preview_{char['id']}.png"
        preview_paths[char["id"]] = generate_character_preview(char, preview_save)

    print("\n[INFO] Generando 10 ilustraciones de escena...")
    scene_image_paths = []
    for i in range(1, 11):
        key = f"escena_{i}"
        escena = escenas.get(key, {})
        visual = visuals.get(key, {})
        save_path = f"{OUTPUT_DIR}/scene_{i:02d}.png"
        generate_scene_image(i, escena, visual, preview_paths, save_path)
        scene_image_paths.append(save_path)

    output_pdf = f"{OUTPUT_DIR}/Un_Dia_en_Creta_con_Alex.pdf"
    assemble_pdf(escenas, scene_image_paths, output_pdf)

    print("\n" + "=" * 65)
    print(f"  ✅ PIPELINE COMPLETO")
    print(f"  PDF: {output_pdf}")
    print(f"  Imágenes: {OUTPUT_DIR}/scene_*.png")
    print("=" * 65)


if __name__ == "__main__":
    main()
