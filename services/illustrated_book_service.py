"""
Illustrated Book Service for Dragon Garden.
Generates complete scenes with character included (like Quick Stories).
Uses same functions and prompt structure as fixed_stories.py.
"""

import os
import json
import math
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO


def add_watermark(image: Image.Image, text: str = "Magic Memories Books") -> Image.Image:
    """
    Add diagonal watermark text across the image to protect preview images.
    The watermark is prominent and covers the image diagonally to prevent theft.
    """
    result = image.copy().convert("RGBA")
    watermark_layer = Image.new("RGBA", result.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(watermark_layer)
    
    img_width, img_height = result.size
    diagonal = math.sqrt(img_width**2 + img_height**2)
    font_size = int(diagonal / 8)
    
    font = None
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    
    for path in font_paths:
        try:
            if os.path.exists(path):
                font = ImageFont.truetype(path, font_size)
                break
        except:
            continue
    
    if font is None:
        try:
            import glob
            matches = glob.glob("/nix/store/*/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
            if matches:
                font = ImageFont.truetype(matches[0], font_size)
        except:
            font = ImageFont.load_default()
    
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    text_img = Image.new("RGBA", (int(text_width * 1.3), int(text_height * 2)), (0, 0, 0, 0))
    text_draw = ImageDraw.Draw(text_img)
    
    shadow_offset = 4
    text_draw.text((int(text_width * 0.15) + shadow_offset, int(text_height * 0.5) + shadow_offset), text, 
                   font=font, fill=(30, 30, 30, 200))
    text_draw.text((int(text_width * 0.15), int(text_height * 0.5)), text, 
                   font=font, fill=(255, 255, 255, 240))
    
    angle = -40
    rotated_text = text_img.rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)
    
    rot_w, rot_h = rotated_text.size
    for y in range(-rot_h, img_height + rot_h, int(rot_h * 0.9)):
        for x in range(-rot_w, img_width + rot_w, int(rot_w * 0.7)):
            watermark_layer.paste(rotated_text, (x, y), rotated_text)
    
    result = Image.alpha_composite(result, watermark_layer)
    return result.convert("RGB")

DRAGON_GARDEN_DIR = "static/assets/dragon_garden_scenes"

from services.personalized_books.dragon_garden_prompts import (
    DRAGON_GARDEN_SCENES,
    CLOSING_SCENE as DG_CLOSING_SCENE,
    FRONT_COVER as DG_FRONT_COVER,
    BACK_COVER as DG_BACK_COVER,
    SPARK_INLINE as SPARK_DESC,
    STYLE_BASE,
    build_scene_prompt as dg_build_scene_prompt,
    get_outfit_desc as dg_get_outfit_desc,
    get_hair_action as dg_get_hair_action,
    get_age_body_description,
    get_hair_texture_description,
)

from services.personalized_books.magic_chef_prompts import (
    MAGIC_CHEF_SCENES,
    CLOSING_SCENE as MC_CLOSING_SCENE,
    FRONT_COVER as MC_FRONT_COVER,
    BACK_COVER as MC_BACK_COVER,
    SWEETIE_HAT_INLINE,
    SWEETIE_CAKE_INLINE,
    STYLE_BASE as MC_STYLE_BASE,
    build_scene_prompt as mc_build_scene_prompt,
    get_outfit_desc as mc_get_outfit_desc,
)


from services.personalized_books.magic_inventor_prompts import (
    MAGIC_INVENTOR_SCENES,
    CLOSING_SCENE as MI_CLOSING_SCENE,
    FRONT_COVER as MI_FRONT_COVER,
    BACK_COVER as MI_BACK_COVER,
    BOLT_INLINE as BOLT_DESC,
    STYLE_BASE as MI_STYLE_BASE,
    build_scene_prompt as mi_build_scene_prompt,
    get_outfit_desc as mi_get_outfit_desc,
)

from services.personalized_books.star_keeper_prompts import (
    STAR_KEEPER_SCENES,
    CLOSING_SCENE as SK_CLOSING_SCENE,
    FRONT_COVER as SK_FRONT_COVER,
    BACK_COVER as SK_BACK_COVER,
    LUNA_INLINE as LUNA_DESC,
    STYLE_BASE as SK_STYLE_BASE,
    build_scene_prompt as sk_build_scene_prompt,
    get_outfit_desc as sk_get_outfit_desc,
)

from services.personalized_books.furry_love_prompts import (
    FURRY_LOVE_SCENES,
    CLOSING_SCENE as FL_CLOSING_SCENE,
    FRONT_COVER as FL_FRONT_COVER,
    BACK_COVER as FL_BACK_COVER,
    STYLE_BASE as FL_STYLE_BASE,
    build_scene_prompt as fl_build_scene_prompt,
)

from services.personalized_books.furry_love_adventure_prompts import (
    FURRY_LOVE_ADVENTURE_SCENES,
    CLOSING_SCENE as FLA_CLOSING_SCENE,
    FRONT_COVER as FLA_FRONT_COVER,
    BACK_COVER as FLA_BACK_COVER,
    STYLE_BASE as FLA_STYLE_BASE,
    build_scene_prompt as fla_build_scene_prompt,
)

from services.personalized_books.furry_love_teen_prompts import (
    FURRY_LOVE_TEEN_SCENES,
    CLOSING_SCENE as FLT_CLOSING_SCENE,
    FRONT_COVER as FLT_FRONT_COVER,
    BACK_COVER as FLT_BACK_COVER,
    STYLE_BASE as FLT_STYLE_BASE,
    build_scene_prompt as flt_build_scene_prompt,
)

from services.personalized_books.furry_love_adult_prompts import (
    FURRY_LOVE_ADULT_SCENES,
    CLOSING_SCENE as FLAD_CLOSING_SCENE,
    FRONT_COVER as FLAD_FRONT_COVER,
    BACK_COVER as FLAD_BACK_COVER,
    STYLE_BASE as FLAD_STYLE_BASE,
    build_scene_prompt as flad_build_scene_prompt,
)

ALL_PERSONALIZED_BOOK_IDS = ['dragon_garden', 'magic_chef', 'magic_inventor', 'star_keeper', 'furry_love', 'furry_love_adventure', 'furry_love_teen', 'furry_love_adult']


def get_hair_description(traits: dict, gender: str = None) -> str:
    """Build natural hair description (same as fixed_stories.py)."""
    color = traits.get('hair_color', 'brown')
    length = traits.get('hair_length', 'medium')
    hair_type = traits.get('hair_type', 'straight')
    if gender is None:
        gender = traits.get('gender', traits.get('child_gender', ''))
    
    color_map = {
        'black': 'jet black',
        'brown': 'medium brown',
        'light_brown': 'light brown',
        'blonde': 'golden blonde',
        'very_light_blonde': 'very light blonde',
        'red': 'bright red',
        'auburn': 'auburn'
    }
    
    type_map = {
        'straight': 'straight',
        'wavy': 'wavy',
        'curly': 'curly'
    }
    
    c = color_map.get(color, color)
    t = type_map.get(hair_type, hair_type)
    
    if length == 'short':
        if gender == 'male':
            return f"{c} short cropped {t} boy haircut, trimmed above ears and neatly tapered"
        else:
            return f"{c} short {t} hair"
    
    length_map = {
        'medium': 'medium-length',
        'long': 'long flowing'
    }
    
    l = length_map.get(length, length)
    
    return f"{c} {l} {t} hair"


def get_eye_description(traits: dict) -> str:
    """Get eye color description (same as fixed_stories.py)."""
    eye_color = traits.get('eye_color', 'brown')
    eye_map = {
        'black': 'deep black',
        'brown': 'warm brown',
        'hazel': 'hazel green-brown',
        'green': 'bright green',
        'blue': 'clear blue',
        'gray': 'soft gray'
    }
    return eye_map.get(eye_color, eye_color) + " eyes"


def get_hair_action(traits: dict) -> str:
    """Get hair movement description (same as fixed_stories.py)."""
    length = traits.get('hair_length', 'medium')
    hair_type = traits.get('hair_type', 'straight')
    
    if length == 'short':
        return "short hair slightly ruffled by wind"
    elif length == 'long':
        if hair_type == 'curly':
            return "long curly hair bouncing in the wind"
        else:
            return "long hair flowing gracefully in the wind"
    else:
        return "hair gently moving in the breeze"


def get_skin_tone(skin: str) -> str:
    """Get detailed skin tone description (same as fixed_stories.py)."""
    skin_map = {
        'very_light': 'very fair porcelain skin with soft pink undertones',
        'light': 'light peach skin with warm rosy undertones',
        'medium_light': 'warm olive skin with golden-beige undertones',
        'medium': 'warm caramel brown skin with rich golden undertones',
        'olive': 'warm olive-toned skin with golden-tan undertones',
        'tan': 'warm caramel tan skin with rich golden-brown undertones',
        'medium_dark': 'deep brown skin with warm mahogany undertones',
        'brown': 'rich brown skin with deep mahogany undertones',
        'dark': 'deep rich dark brown skin with warm chocolate undertones'
    }
    return skin_map.get(skin, skin)


def get_gender_child(gender: str) -> str:
    """Get gender word."""
    if gender == 'female':
        return 'little girl'
    elif gender == 'male':
        return 'little boy'
    return 'young child'


BOOK_CONFIGS = {
    "dragon_garden": {
        "book_id": "dragon_garden",
        "title_es": "El Jardín del Dragón",
        "title_en": "The Dragon Garden",
        "scenes": DRAGON_GARDEN_SCENES,
        "closing": DG_CLOSING_SCENE,
        "front_cover": DG_FRONT_COVER,
        "back_cover": DG_BACK_COVER,
        "style_base": STYLE_BASE,
        "companion_desc": SPARK_DESC,
        "build_scene_prompt": dg_build_scene_prompt,
        "get_outfit_desc": dg_get_outfit_desc,
    },
    "magic_chef": {
        "book_id": "magic_chef",
        "title_es": "{name} El Chef Mágico",
        "title_en": "{name} The Magic Chef",
        "scenes": MAGIC_CHEF_SCENES,
        "closing": MC_CLOSING_SCENE,
        "front_cover": MC_FRONT_COVER,
        "back_cover": MC_BACK_COVER,
        "style_base": MC_STYLE_BASE,
        "companion_desc": SWEETIE_HAT_INLINE,
        "build_scene_prompt": mc_build_scene_prompt,
        "get_outfit_desc": mc_get_outfit_desc,
    },
    "magic_inventor": {
        "book_id": "magic_inventor",
        "title_es": "{name} y el Taller de los Inventos Mágicos",
        "title_en": "{name} and the Magic Inventor Workshop",
        "scenes": MAGIC_INVENTOR_SCENES,
        "closing": MI_CLOSING_SCENE,
        "front_cover": MI_FRONT_COVER,
        "back_cover": MI_BACK_COVER,
        "style_base": MI_STYLE_BASE,
        "companion_desc": BOLT_DESC,
        "build_scene_prompt": mi_build_scene_prompt,
        "get_outfit_desc": mi_get_outfit_desc,
    },
    "star_keeper": {
        "book_id": "star_keeper",
        "title_es": "{name} y el Guardián de Estrellas",
        "title_en": "{name} The Star Keeper",
        "scenes": STAR_KEEPER_SCENES,
        "closing": SK_CLOSING_SCENE,
        "front_cover": SK_FRONT_COVER,
        "back_cover": SK_BACK_COVER,
        "style_base": SK_STYLE_BASE,
        "companion_desc": LUNA_DESC,
        "build_scene_prompt": sk_build_scene_prompt,
        "get_outfit_desc": sk_get_outfit_desc,
    },
    "furry_love": {
        "book_id": "furry_love",
        "title_es": "El día que {pet_name} conoció a {name}",
        "title_en": "The day {pet_name} met {name}",
        "scenes": FURRY_LOVE_SCENES,
        "closing": FL_CLOSING_SCENE,
        "front_cover": FL_FRONT_COVER,
        "back_cover": FL_BACK_COVER,
        "style_base": FL_STYLE_BASE,
        "companion_desc": "",
        "build_scene_prompt": None,
        "get_outfit_desc": None,
        "is_furry_love": True,
    },
    "furry_love_adventure": {
        "book_id": "furry_love_adventure",
        "title_es": "Las aventuras de {pet_name} y {name}",
        "title_en": "The Adventures of {pet_name} and {name}",
        "scenes": FURRY_LOVE_ADVENTURE_SCENES,
        "closing": FLA_CLOSING_SCENE,
        "front_cover": FLA_FRONT_COVER,
        "back_cover": FLA_BACK_COVER,
        "style_base": FLA_STYLE_BASE,
        "companion_desc": "",
        "build_scene_prompt": None,
        "get_outfit_desc": None,
        "is_furry_love": True,
    },
    "furry_love_teen": {
        "book_id": "furry_love_teen",
        "title_es": "{name} y su compañero fiel {pet_name}",
        "title_en": "{name} and Their Faithful Companion {pet_name}",
        "scenes": FURRY_LOVE_TEEN_SCENES,
        "closing": FLT_CLOSING_SCENE,
        "front_cover": FLT_FRONT_COVER,
        "back_cover": FLT_BACK_COVER,
        "style_base": FLT_STYLE_BASE,
        "companion_desc": "",
        "build_scene_prompt": None,
        "get_outfit_desc": None,
        "is_furry_love": True,
    },
    "furry_love_adult": {
        "book_id": "furry_love_adult",
        "title_es": "La Gran Aventura de {name} y {pet_name}",
        "title_en": "The Great Adventure of {name} and {pet_name}",
        "scenes": FURRY_LOVE_ADULT_SCENES,
        "closing": FLAD_CLOSING_SCENE,
        "front_cover": FLAD_FRONT_COVER,
        "back_cover": FLAD_BACK_COVER,
        "style_base": FLAD_STYLE_BASE,
        "companion_desc": "",
        "build_scene_prompt": None,
        "get_outfit_desc": None,
        "is_furry_love": True,
    },
}


def load_book_config(book_id: str) -> dict:
    """Load book configuration."""
    return BOOK_CONFIGS.get(book_id, {})


def generate_scene_complete(
    scene_config: dict,
    traits: dict,
    child_name: str,
    gender: str,
    language: str = "es",
    book_id: str = "dragon_garden",
    reference_image_path: str = None,
    reference_image_path_2: str = None
) -> Image.Image:
    """
    Generate scene using FLUX 2 Dev for all personalized books.
    Each book uses its own build_scene_prompt from its prompts module.
    Requires reference_image_path for character consistency.
    For furry_love: uses TWO reference images (human + pet).
    """
    import replicate
    
    scene_id = scene_config.get("id", 0)
    child_age = traits.get('child_age', '5')
    child_age_int = int(child_age) if str(child_age).isdigit() else 6
    
    is_furry = book_id in ('furry_love', 'furry_love_adventure', 'furry_love_teen', 'furry_love_adult')
    if is_furry:
        if book_id == 'furry_love_teen':
            from services.personalized_books.furry_love_teen_prompts import build_scene_prompt as furry_build_prompt
        elif book_id == 'furry_love_adult':
            from services.personalized_books.furry_love_adult_prompts import build_scene_prompt as furry_build_prompt
        elif book_id == 'furry_love_adventure':
            from services.personalized_books.furry_love_adventure_prompts import build_scene_prompt as furry_build_prompt
        else:
            from services.personalized_books.furry_love_prompts import build_scene_prompt as furry_build_prompt
        human_desc = traits.get('human_desc', '')
        pet_name = traits.get('pet_name', 'Buddy')
        pet_desc = traits.get('pet_desc', '')
        eye_desc = get_eye_description(traits) if traits.get('eye_color') else ''
        gender_word = "boy" if gender == "male" else "girl" if gender == "female" else "person"
        glasses_val = traits.get('glasses', 'none')
        facial_hair_val = traits.get('facial_hair', 'none')
        hair_desc = get_hair_description(traits) if book_id == 'furry_love_adventure' else ''
        prompt = furry_build_prompt(scene_config, human_desc, pet_name, pet_desc, eye_desc=eye_desc, gender_word=gender_word, glasses=glasses_val, facial_hair=facial_hair_val, hair_desc=hair_desc)
    else:
        book_cfg = BOOK_CONFIGS.get(book_id)
        if book_cfg and 'build_scene_prompt' in book_cfg and book_cfg['build_scene_prompt']:
            prompt = book_cfg['build_scene_prompt'](scene_config, child_name, gender, child_age_int, traits)
        else:
            hair_desc = get_hair_description(traits)
            skin_tone = get_skin_tone(traits.get('skin_tone', 'light'))
            gender_child = get_gender_child(gender)
            outfit_desc = "a cozy green tunic with brown pants and small boots" if gender == "male" else "a flowing lavender dress with small boots"
            scene_template = scene_config.get("scene_template", scene_config.get("prompt", ""))
            prompt = scene_template.format(
                gender_child=gender_child,
                hair_desc=hair_desc,
                skin_tone=skin_tone,
                outfit_desc=outfit_desc,
                spark_desc=SPARK_DESC,
                style=STYLE_BASE,
                name=child_name
            )
    
    if not reference_image_path or not os.path.exists(reference_image_path):
        raise ValueError(f"[SCENE {scene_id}] reference_image_path is required for FLUX 2 Dev generation ({book_id})")
    
    print(f"[SCENE {scene_id}] Generating with FLUX 2 Dev + reference ({book_id})...")
    print(f"[SCENE {scene_id}] Prompt: {prompt[:300]}...")
    
    import time
    MAX_RETRIES = 4
    target_size = (1024, 1365)

    if is_furry and reference_image_path_2 and os.path.exists(reference_image_path_2):
        reference_note = "@image1=HUMAN character, @image2=PET animal. Human has smooth skin, human face, human hands. Pet has fur, animal face, four paws. Two distinct separate characters side by side."
        enhanced_prompt = f"{reference_note}\n{prompt}"

        for attempt in range(MAX_RETRIES + 1):
            try:
                print(f"[SCENE {scene_id}] FLUX 2 Dev + 2 refs attempt {attempt + 1}/{MAX_RETRIES + 1}...")
                with open(reference_image_path, "rb") as ref1, open(reference_image_path_2, "rb") as ref2:
                    output = replicate.run(
                        "black-forest-labs/flux-2-dev",
                        input={
                            "prompt": enhanced_prompt,
                            "input_images": [ref1, ref2],
                            "aspect_ratio": "3:4",
                            "output_format": "png",
                            "go_fast": False
                        }
                    )

                if isinstance(output, list) and len(output) > 0:
                    image_url = output[0]
                elif isinstance(output, str):
                    image_url = output
                else:
                    image_url = str(output)

                response = requests.get(image_url)
                image = Image.open(BytesIO(response.content)).convert("RGB")
                image = image.resize(target_size, Image.Resampling.LANCZOS)
                print(f"[SCENE {scene_id}] Generated with FLUX 2 Dev + 2 refs on attempt {attempt + 1}! Size: {image.size}")
                return image
            except Exception as e:
                print(f"[SCENE {scene_id}] Attempt {attempt + 1} failed: {e}")
                if attempt < MAX_RETRIES:
                    wait_time = 5 + attempt * 3
                    print(f"[SCENE {scene_id}] Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    print(f"[SCENE {scene_id}] CRITICAL: All {MAX_RETRIES + 1} attempts failed for FLUX 2 Dev + 2 refs.")
                    raise RuntimeError(f"FLUX 2 Dev failed for scene {scene_id} after {MAX_RETRIES + 1} attempts: {e}")

    gender_word = "boy" if gender == "male" else "girl" if gender == "female" else "child"
    reference_note = f"@image1=the {gender_word} character. Same face, skin tone, and hair as the reference."
    enhanced_prompt = f"{reference_note}\n{prompt}"

    for attempt in range(MAX_RETRIES + 1):
        try:
            print(f"[SCENE {scene_id}] FLUX 2 Dev + 1 ref attempt {attempt + 1}/{MAX_RETRIES + 1}...")
            with open(reference_image_path, "rb") as ref_file:
                output = replicate.run(
                    "black-forest-labs/flux-2-dev",
                    input={
                        "prompt": enhanced_prompt,
                        "input_images": [ref_file],
                        "aspect_ratio": "3:4",
                        "output_format": "png",
                        "go_fast": False
                    }
                )

            if isinstance(output, list) and len(output) > 0:
                image_url = output[0]
            elif isinstance(output, str):
                image_url = output
            else:
                image_url = str(output)

            response = requests.get(image_url)
            image = Image.open(BytesIO(response.content)).convert("RGB")
            image = image.resize(target_size, Image.Resampling.LANCZOS)
            print(f"[SCENE {scene_id}] Generated with FLUX 2 Dev on attempt {attempt + 1}! Size: {image.size}")
            return image
        except Exception as e:
            print(f"[SCENE {scene_id}] Attempt {attempt + 1} failed: {e}")
            if attempt < MAX_RETRIES:
                wait_time = 5 + attempt * 3
                print(f"[SCENE {scene_id}] Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
            else:
                print(f"[SCENE {scene_id}] CRITICAL: All {MAX_RETRIES + 1} attempts failed for FLUX 2 Dev.")
                raise RuntimeError(f"FLUX 2 Dev failed for scene {scene_id} after {MAX_RETRIES + 1} attempts: {e}")


def add_text_split(
    image: Image.Image,
    text: str,
    text_color: str,
    shadow_color: str,
    font_size: int,
    margin_px: int
) -> Image.Image:
    """
    Split text: 2 lines at top, remaining lines at bottom.
    For long texts that would cover too much of the image.
    """
    result = image.copy()
    draw = ImageDraw.Draw(result)
    img_width, img_height = result.size
    
    font = None
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    ]
    for fp in font_paths:
        if os.path.exists(fp):
            font = ImageFont.truetype(fp, font_size)
            break
    if font is None:
        font = ImageFont.load_default()
    
    max_width = img_width - (2 * margin_px)
    
    words = text.split()
    lines = []
    current_line = ""
    for word in words:
        test_line = f"{current_line} {word}".strip()
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    
    if len(lines) <= 2:
        top_lines = lines
        bottom_lines = []
    elif len(lines) == 3:
        top_lines = lines[:1]
        bottom_lines = lines[1:]
    else:
        mid = len(lines) // 2
        top_lines = lines[:mid]
        bottom_lines = lines[mid:]
    
    line_height = font_size + 8
    shadow_offset = max(2, font_size // 20)
    
    if top_lines:
        y = margin_px
        for line in top_lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = (img_width - text_width) // 2
            draw.text((x + shadow_offset, y + shadow_offset), line, font=font, fill=shadow_color)
            draw.text((x, y), line, font=font, fill=text_color)
            y += line_height
    
    if bottom_lines:
        total_height = len(bottom_lines) * line_height
        y = img_height - margin_px - total_height
        for line in bottom_lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = (img_width - text_width) // 2
            draw.text((x + shadow_offset, y + shadow_offset), line, font=font, fill=shadow_color)
            draw.text((x, y), line, font=font, fill=text_color)
            y += line_height
    
    return result


def add_text_to_image(
    image: Image.Image,
    text: str,
    position: str = "bottom",
    text_color: str = "#FFFFFF",
    shadow_color: str = "#000000",
    font_size: int = 52,
    margin_percent: float = 0.05
) -> Image.Image:
    """
    Add text to image with margins as percentage of image size.
    This adapts to any image dimensions.
    
    Font size 52 at 768px width ≈ 14pts at 20cm print width.
    
    Args:
        image: Source image
        text: Text to add (with {name} replaced)
        position: "top", "bottom", or "split" (half top, half bottom)
        text_color: Color of the text
        shadow_color: Color of the shadow
        font_size: Base font size (52 = ~14pts at print size)
        margin_percent: Margin as percentage of image width (5% = 0.05)
    """
    result = image.copy()
    draw = ImageDraw.Draw(result)
    
    img_width, img_height = result.size
    
    scaled_font_size = int(font_size * (img_width / 1024))
    if scaled_font_size < 36:
        scaled_font_size = 36
    margin_px = int(img_width * margin_percent)
    
    if position == "split":
        return add_text_split(result, text, text_color, shadow_color, scaled_font_size, margin_px)
    
    font = None
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    
    for path in font_paths:
        try:
            if os.path.exists(path):
                font = ImageFont.truetype(path, scaled_font_size)
                break
        except:
            continue
    
    if font is None:
        try:
            import glob
            matches = glob.glob("/nix/store/*/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
            if matches:
                font = ImageFont.truetype(matches[0], scaled_font_size)
        except:
            font = ImageFont.load_default()
    
    text_area_width = img_width - (margin_px * 2)
    
    words = text.split()
    lines = []
    current_line_words = []
    
    for word in words:
        test_line = ' '.join(current_line_words + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        test_width = bbox[2] - bbox[0]
        
        if test_width <= text_area_width:
            current_line_words.append(word)
        else:
            if current_line_words:
                lines.append(current_line_words)
            current_line_words = [word]
    
    if current_line_words:
        lines.append(current_line_words)
    
    line_height = int(scaled_font_size * 1.4)
    total_text_height = len(lines) * line_height
    
    if position == "top":
        start_y = margin_px
    else:
        start_y = img_height - total_text_height - margin_px
    
    for line_idx, line_words in enumerate(lines):
        y = start_y + (line_idx * line_height)
        is_last_line = (line_idx == len(lines) - 1)
        
        if is_last_line or len(line_words) == 1:
            line_text = ' '.join(line_words)
            bbox = draw.textbbox((0, 0), line_text, font=font)
            text_width = bbox[2] - bbox[0]
            x = margin_px + (text_area_width - text_width) // 2
            
            for dx in range(-3, 4):
                for dy in range(-3, 4):
                    if dx != 0 or dy != 0:
                        draw.text((x + dx, y + dy), line_text, font=font, fill=shadow_color)
            draw.text((x, y), line_text, font=font, fill=text_color)
        else:
            word_widths = []
            for word in line_words:
                bbox = draw.textbbox((0, 0), word, font=font)
                word_widths.append(bbox[2] - bbox[0])
            
            total_words_width = sum(word_widths)
            total_space = text_area_width - total_words_width
            num_gaps = len(line_words) - 1
            space_per_gap = total_space / num_gaps if num_gaps > 0 else 0
            
            current_x = margin_px
            for word_idx, word in enumerate(line_words):
                for dx in range(-3, 4):
                    for dy in range(-3, 4):
                        if dx != 0 or dy != 0:
                            draw.text((current_x + dx, y + dy), word, font=font, fill=shadow_color)
                draw.text((current_x, y), word, font=font, fill=text_color)
                
                current_x += word_widths[word_idx] + space_per_gap
    
    return result


def generate_dedication_page(dedication_text: str, img_size: tuple = (768, 1024), language: str = "es") -> Image.Image:
    """Generate the dedication page with decorative frame.
    Uses fixed background from docs/fixed_pages/dedication_frame.png (copied to static/images/).
    The background already includes 'Dedicatoria' title, so we only add the user's text.
    """
    bg_path = "static/images/dedication_page_background.png"
    has_fixed_bg = os.path.exists(bg_path)
    
    if has_fixed_bg:
        page = Image.open(bg_path).convert("RGB")
        page = page.resize(img_size, Image.Resampling.LANCZOS)
    else:
        page = Image.new("RGB", img_size, "#FFFEF5")
    
    draw = ImageDraw.Draw(page)
    scale = img_size[0] / 768
    
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(28 * scale))
        text_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(24 * scale))
    except:
        title_font = ImageFont.load_default()
        text_font = title_font
    
    if not has_fixed_bg:
        title = "Dedicatoria" if language == "es" else "Dedication"
        title_bbox = draw.textbbox((0, 0), title, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (img_size[0] - title_width) // 2
        title_y = int(img_size[1] * 0.30)
        draw.text((title_x, title_y), title, font=title_font, fill="#2E1A47")
    
    if not dedication_text:
        return page
    
    # A4 = 21 cm wide, margins = 4.5 cm each side, text area = 12 cm
    # margin = 4.5/21 = 21.4% of width
    left_margin = int(img_size[0] * 0.214)  # 4.5 cm from left
    right_margin = int(img_size[0] * 0.214)  # 4.5 cm from right
    max_width = img_size[0] - left_margin - right_margin  # ~12 cm text area
    
    words = dedication_text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=text_font)
        if bbox[2] - bbox[0] <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    line_height = int(36 * scale)
    
    # Vertical position - user confirmed this is good
    frame_top = int(img_size[1] * 0.32)
    frame_bottom = int(img_size[1] * 0.42)
    frame_center = (frame_top + frame_bottom) // 2
    
    total_text_height = len(lines) * line_height
    start_y = frame_center - (total_text_height // 2)
    
    # Center text horizontally within the 12 cm text area (between margins)
    text_area_center = left_margin + (max_width // 2)
    
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=text_font)
        text_width = bbox[2] - bbox[0]
        x = text_area_center - (text_width // 2)
        y = start_y + (i * line_height)
        draw.text((x, y), line, font=text_font, fill="#2E1A47")
    
    return page


def generate_closing_page(
    traits: dict,
    child_name: str,
    gender: str,
    img_size: tuple = (1024, 1365),
    book_id: str = "dragon_garden",
    reference_image_path: str = None,
    reference_image_path_2: str = None
) -> Image.Image:
    """
    Generate the closing illustration page using FLUX 2 Dev with reference for all books.
    Each book uses its own build_scene_prompt from its prompts module.
    For furry_love: uses TWO reference images (human + pet).
    """
    import replicate
    
    book_config = load_book_config(book_id)
    closing_scene = book_config.get("closing", DG_CLOSING_SCENE)
    child_age = traits.get('child_age', '5')
    child_age_int = int(child_age) if str(child_age).isdigit() else 6
    
    is_furry = book_id in ('furry_love', 'furry_love_adventure', 'furry_love_teen', 'furry_love_adult')
    if is_furry:
        if book_id == 'furry_love_teen':
            from services.personalized_books.furry_love_teen_prompts import build_scene_prompt as furry_build_prompt
        elif book_id == 'furry_love_adult':
            from services.personalized_books.furry_love_adult_prompts import build_scene_prompt as furry_build_prompt
        elif book_id == 'furry_love_adventure':
            from services.personalized_books.furry_love_adventure_prompts import build_scene_prompt as furry_build_prompt
        else:
            from services.personalized_books.furry_love_prompts import build_scene_prompt as furry_build_prompt
        human_desc = traits.get('human_desc', '')
        pet_name = traits.get('pet_name', 'Buddy')
        pet_desc = traits.get('pet_desc', '')
        eye_desc = get_eye_description(traits) if traits.get('eye_color') else ''
        gender_word = "boy" if gender == "male" else "girl" if gender == "female" else "person"
        glasses_val = traits.get('glasses', 'none')
        facial_hair_val = traits.get('facial_hair', 'none')
        hair_desc = get_hair_description(traits) if book_id == 'furry_love_adventure' else ''
        prompt = furry_build_prompt(closing_scene, human_desc, pet_name, pet_desc, eye_desc=eye_desc, gender_word=gender_word, glasses=glasses_val, facial_hair=facial_hair_val, hair_desc=hair_desc)
    elif BOOK_CONFIGS.get(book_id, {}).get('build_scene_prompt'):
        book_cfg = BOOK_CONFIGS.get(book_id)
        prompt = book_cfg['build_scene_prompt'](closing_scene, child_name, gender, child_age_int, traits)
    else:
        hair_desc = get_hair_description(traits)
        skin_tone = get_skin_tone(traits.get('skin_tone', 'light'))
        gender_child = get_gender_child(gender)
        closing_template = closing_scene.get("scene_template", closing_scene.get("prompt", ""))
        prompt = closing_template.format(
            gender_child=gender_child,
            hair_desc=hair_desc,
            skin_tone=skin_tone,
            spark_desc=SPARK_DESC,
            style=STYLE_BASE
        )
    
    if not reference_image_path or not os.path.exists(reference_image_path):
        raise ValueError(f"[CLOSING] reference_image_path is required for FLUX 2 Dev generation ({book_id})")
    
    print(f"[CLOSING] Generating closing for '{book_id}' with FLUX 2 Dev + reference...")
    print(f"[CLOSING] Prompt: {prompt[:300]}...")
    
    if is_furry and reference_image_path_2 and os.path.exists(reference_image_path_2):
        reference_note = "@image1=HUMAN character, @image2=PET animal. Human has smooth skin, human face, human hands. Pet has fur, animal face, four paws. Two distinct separate characters side by side."
        enhanced_prompt = f"{reference_note}\n{prompt}"
        try:
            with open(reference_image_path, "rb") as ref1, open(reference_image_path_2, "rb") as ref2:
                output = replicate.run(
                    "black-forest-labs/flux-2-dev",
                    input={
                        "prompt": enhanced_prompt,
                        "input_images": [ref1, ref2],
                        "aspect_ratio": "3:4",
                        "output_format": "png",
                        "go_fast": False
                    }
                )
            if isinstance(output, list) and len(output) > 0:
                image_url = output[0]
            elif isinstance(output, str):
                image_url = output
            else:
                image_url = str(output)
            response = requests.get(image_url)
            image = Image.open(BytesIO(response.content)).convert("RGB")
            image = image.resize(img_size, Image.Resampling.LANCZOS)
            print(f"[CLOSING] Generated successfully with FLUX 2 Dev + 2 refs! Size: {image.size}")
            return image
        except Exception as e:
            print(f"[CLOSING] Error generating with 2 refs: {e}")
            print(f"[CLOSING] Retrying...")
            try:
                import time
                time.sleep(3)
                with open(reference_image_path, "rb") as ref1, open(reference_image_path_2, "rb") as ref2:
                    output = replicate.run(
                        "black-forest-labs/flux-2-dev",
                        input={
                            "prompt": enhanced_prompt,
                            "input_images": [ref1, ref2],
                            "aspect_ratio": "3:4",
                            "output_format": "png",
                            "go_fast": False
                        }
                    )
                if isinstance(output, list) and len(output) > 0:
                    image_url = output[0]
                elif isinstance(output, str):
                    image_url = output
                else:
                    image_url = str(output)
                response = requests.get(image_url)
                image = Image.open(BytesIO(response.content)).convert("RGB")
                image = image.resize(img_size, Image.Resampling.LANCZOS)
                print(f"[CLOSING] Retry FLUX 2 Dev + 2 refs succeeded!")
                return image
            except Exception as e2:
                print(f"[CLOSING] Retry also failed: {e2}")
            return Image.new("RGB", img_size, "#FFFEF5")
    
    gender_word = "boy" if gender == "male" else "girl" if gender == "female" else "child"
    reference_note = f"@image1=the {gender_word} character. Same face, skin tone, and hair as the reference."
    enhanced_prompt = f"{reference_note}\n{prompt}"
    
    try:
        with open(reference_image_path, "rb") as ref_file:
            output = replicate.run(
                "black-forest-labs/flux-2-dev",
                input={
                    "prompt": enhanced_prompt,
                    "input_images": [ref_file],
                    "aspect_ratio": "3:4",
                    "output_format": "png",
                    "go_fast": False
                }
            )
        
        if isinstance(output, list) and len(output) > 0:
            image_url = output[0]
        elif isinstance(output, str):
            image_url = output
        else:
            image_url = str(output)
        
        response = requests.get(image_url)
        image = Image.open(BytesIO(response.content)).convert("RGB")
        
        image = image.resize(img_size, Image.Resampling.LANCZOS)
        
        print(f"[CLOSING] Generated successfully with FLUX 2 Dev! Size: {image.size}")
        return image
        
    except Exception as e:
        print(f"[CLOSING] Error generating: {e}")
        print(f"[CLOSING] Retrying with FLUX 2 Dev (attempt 2)...")
        try:
            import time
            time.sleep(3)
            with open(reference_image_path, "rb") as ref_file:
                output = replicate.run(
                    "black-forest-labs/flux-2-dev",
                    input={
                        "prompt": enhanced_prompt,
                        "input_images": [ref_file],
                        "aspect_ratio": "3:4",
                        "output_format": "png",
                        "go_fast": False
                    }
                )
            if isinstance(output, list) and len(output) > 0:
                image_url = output[0]
            elif isinstance(output, str):
                image_url = output
            else:
                image_url = str(output)
            response = requests.get(image_url)
            image = Image.open(BytesIO(response.content)).convert("RGB")
            image = image.resize(img_size, Image.Resampling.LANCZOS)
            print(f"[CLOSING] Retry FLUX 2 Dev succeeded!")
            return image
        except Exception as e2:
            print(f"[CLOSING] Retry also failed: {e2}")
        return Image.new("RGB", img_size, "#FFFEF5")


def generate_cover_spread(
    traits: dict,
    child_name: str,
    gender: str,
    language: str = "es",
    book_id: str = "dragon_garden",
    author_name: str = "Magic Memories Books",
    reference_image_path: str = None,
    reference_image_path_2: str = None
) -> Image.Image:
    """
    Generate the complete cover spread for Lulu Casewrap Hardcover.
    Layout: [Wrap] Back Board [Spine] Front Board [Wrap]
    
    Lulu A4 Casewrap Hardcover specifications:
    - Interior trim size: 210mm x 297mm (A4)
    - Board overhang: 3.175mm (1/8") on top, bottom, fore-edge (NOT spine side)
    - Board size: 213.175mm x 303.35mm
    - Wrap area: 19.05mm (3/4") on all edges of the spread
    - Spine width for 24-84 pages casewrap: 6.35mm (1/4")
    - Total spread: 19.05 + 213.175 + 6.35 + 213.175 + 19.05 = 470.8mm
    - Total height: 19.05 + 303.35 + 19.05 = 341.45mm
    
    At 300 DPI: 5560 x 4032 pixels
    
    Required by Lulu: 469.33mm-472.50mm x 339.79mm-342.96mm
    Our dimensions: 470.80mm x 341.45mm (within range)
    """
    import replicate
    
    DPI = 300
    MM_TO_INCH = 1 / 25.4
    
    TRIM_W = 210.0
    TRIM_H = 297.0
    WRAP = 19.05
    OVERHANG = 3.175
    SPINE_MM = 6.35

    board_w_mm = TRIM_W + OVERHANG
    board_h_mm = TRIM_H + (2 * OVERHANG)
    total_w_mm = WRAP + board_w_mm + SPINE_MM + board_w_mm + WRAP
    total_h_mm = WRAP + board_h_mm + WRAP

    board_w_px = int(board_w_mm * MM_TO_INCH * DPI)
    board_h_px = int(board_h_mm * MM_TO_INCH * DPI)
    wrap_px = int(WRAP * MM_TO_INCH * DPI)
    spine_width_px = int(SPINE_MM * MM_TO_INCH * DPI)
    total_width_px = int(total_w_mm * MM_TO_INCH * DPI)
    total_height_px = int(total_h_mm * MM_TO_INCH * DPI)

    cover_width_px = board_w_px
    cover_height_px = board_h_px
    
    print(f"[COVER] Casewrap spread for '{book_id}': {total_width_px}x{total_height_px} px ({total_w_mm:.1f}x{total_h_mm:.1f}mm)")
    print(f"[COVER] Board panel: {board_w_px}x{board_h_px} px | Wrap: {wrap_px} px | Spine: {spine_width_px} px")
    
    child_age = traits.get('child_age', '5')
    child_age_int = int(child_age) if str(child_age).isdigit() else 6
    
    book_cfg = BOOK_CONFIGS.get(book_id)
    is_furry = book_cfg.get('is_furry_love', False) if book_cfg else False
    if is_furry:
        if book_id == 'furry_love_teen':
            from services.personalized_books.furry_love_teen_prompts import build_scene_prompt as furry_build_prompt
        elif book_id == 'furry_love_adult':
            from services.personalized_books.furry_love_adult_prompts import build_scene_prompt as furry_build_prompt
        elif book_id == 'furry_love_adventure':
            from services.personalized_books.furry_love_adventure_prompts import build_scene_prompt as furry_build_prompt
        else:
            from services.personalized_books.furry_love_prompts import build_scene_prompt as furry_build_prompt
        human_desc = traits.get('human_desc', '')
        pet_name = traits.get('pet_name', 'Buddy')
        pet_desc = traits.get('pet_desc', '')
        eye_desc = get_eye_description(traits) if traits.get('eye_color') else ''
        gender_word = "boy" if gender == "male" else "girl" if gender == "female" else "person"
        glasses_val = traits.get('glasses', 'none')
        facial_hair_val = traits.get('facial_hair', 'none')
        hair_desc = get_hair_description(traits) if book_id == 'furry_love_adventure' else ''
        front_cover_cfg = book_cfg.get('front_cover', {})
        front_prompt = furry_build_prompt(front_cover_cfg, human_desc, pet_name, pet_desc, eye_desc=eye_desc, gender_word=gender_word, glasses=glasses_val, facial_hair=facial_hair_val, hair_desc=hair_desc)
    elif book_cfg and book_cfg.get('build_scene_prompt'):
        front_cover_cfg = book_cfg.get('front_cover', {})
        front_prompt = book_cfg['build_scene_prompt'](front_cover_cfg, child_name, gender, child_age_int, traits)
    else:
        hair_desc = get_hair_description(traits)
        skin_tone = get_skin_tone(traits.get('skin_tone', 'light'))
        gender_child = get_gender_child(gender)
        outfit_desc = "a cozy green tunic with brown pants" if gender == "male" else "a flowing lavender dress"
        front_prompt = f"Disney Pixar 3D style illustration. A {gender_child} with {hair_desc} and {skin_tone} skin wearing {outfit_desc} in a magical garden. {STYLE_BASE}"
    
    front_prompt += "\nClean illustration, space for title at top."
    
    reuse_preview_as_cover = reference_image_path and os.path.exists(reference_image_path) and (not is_furry or (is_furry and not reference_image_path_2))
    
    if reuse_preview_as_cover:
        print(f"[COVER] Using {'furry love pre-generated cover' if is_furry else 'character preview'} as front cover for {book_id}")
        try:
            front_cover = Image.open(reference_image_path).convert("RGB")
            front_cover = front_cover.resize((cover_width_px, cover_height_px), Image.Resampling.LANCZOS)
            print(f"[COVER] Cover image loaded as front cover: {front_cover.size}")
        except Exception as e:
            print(f"[COVER] Error loading cover image: {e}")
            front_cover = Image.new("RGB", (cover_width_px, cover_height_px), "#4A90A4")
    else:
        has_refs = is_furry and reference_image_path and reference_image_path_2 and os.path.exists(reference_image_path) and os.path.exists(reference_image_path_2)
        print(f"[COVER] Generating front cover with FLUX 2 Dev{' + references' if has_refs else ''}...")
        ref_files = []
        try:
            flux_input = {
                "prompt": front_prompt,
                "aspect_ratio": "3:4",
                "output_format": "png",
                "go_fast": False
            }
            if has_refs:
                f1 = open(reference_image_path, "rb")
                f2 = open(reference_image_path_2, "rb")
                ref_files = [f1, f2]
                flux_input["input_images"] = [f1, f2]
            output = replicate.run(
                "black-forest-labs/flux-2-dev",
                input=flux_input
            )
            
            if isinstance(output, list) and len(output) > 0:
                image_url = output[0]
            elif isinstance(output, str):
                image_url = output
            else:
                image_url = str(output)
            
            response = requests.get(image_url)
            front_cover = Image.open(BytesIO(response.content)).convert("RGB")
            front_cover = front_cover.resize((cover_width_px, cover_height_px), Image.Resampling.LANCZOS)
            print(f"[COVER] Front cover generated with FLUX 2 Dev: {front_cover.size}")
            
        except Exception as e:
            print(f"[COVER] Error generating front cover: {e}")
            front_cover = Image.new("RGB", (cover_width_px, cover_height_px), "#4A90A4")
        finally:
            for f in ref_files:
                try:
                    f.close()
                except:
                    pass
    
    # Author name will be added AFTER fitting into spread to avoid being cropped by fit_cover_to_area
    
    fixed_back_covers = {
        "dragon_garden": "static/images/fixed_pages/dragon_garden_back_cover.png",
        "magic_chef": "static/images/fixed_pages/magic_chef_back_cover.png",
        "magic_inventor": "static/images/fixed_pages/magic_inventor_back_cover.png",
        "star_keeper": "static/images/fixed_pages/star_keeper_back_cover.png",
        "furry_love": "static/images/fixed_pages/furry_love_baby_back_cover.png",
        "furry_love_adventure": "static/images/fixed_pages/furry_love_adventure_back_cover.png",
        "furry_love_teen": "static/images/fixed_pages/furry_love_teen_back_cover.png",
        "furry_love_adult": "static/images/fixed_pages/furry_love_adult_back_cover.png"
    }
    MMB_GENERIC_BACK_COVER = "static/images/fixed_pages/back_cover.png"
    back_cover_path = fixed_back_covers.get(book_id, None)
    if back_cover_path:
        print(f"[COVER] Using fixed back cover for {book_id}: {back_cover_path}")
        try:
            back_cover = Image.open(back_cover_path).convert("RGB")
            back_cover = back_cover.resize((cover_width_px, cover_height_px), Image.Resampling.LANCZOS)
            print(f"[COVER] Fixed back cover loaded and resized to A4: {back_cover.size}")
        except Exception as e:
            print(f"[COVER] Error loading fixed back cover for {book_id}: {e}, falling back to MMB generic")
            try:
                back_cover = Image.open(MMB_GENERIC_BACK_COVER).convert("RGB")
                back_cover = back_cover.resize((cover_width_px, cover_height_px), Image.Resampling.LANCZOS)
                print(f"[COVER] MMB generic back cover loaded: {back_cover.size}")
            except Exception as e2:
                print(f"[COVER] MMB generic also failed: {e2}")
                back_cover = Image.new("RGB", (cover_width_px, cover_height_px), "#FFE4B5")
    else:
        print(f"[COVER] No specific back cover for {book_id}, using MMB generic back cover")
        try:
            back_cover = Image.open(MMB_GENERIC_BACK_COVER).convert("RGB")
            back_cover = back_cover.resize((cover_width_px, cover_height_px), Image.Resampling.LANCZOS)
            print(f"[COVER] MMB generic back cover loaded: {back_cover.size}")
        except Exception as e:
            print(f"[COVER] Error loading MMB generic back cover: {e}")
            back_cover = Image.new("RGB", (cover_width_px, cover_height_px), "#FFE4B5")
    
    spread = Image.new("RGB", (total_width_px, total_height_px), "#FFFEF5")

    from PIL import ImageOps
    
    def fit_cover_to_area(img, target_w, target_h):
        """Resize and crop image to exactly fill target area (center crop)."""
        return ImageOps.fit(img, (target_w, target_h), Image.Resampling.LANCZOS)

    back_bleed_w = wrap_px + board_w_px
    back_bleed_h = total_height_px
    back_cover_bleed = fit_cover_to_area(back_cover, back_bleed_w, back_bleed_h)
    spread.paste(back_cover_bleed, (0, 0))
    print(f"[COVER] Back cover with bleed: {back_bleed_w}x{back_bleed_h} px, pasted at (0,0)")

    front_x = wrap_px + board_w_px + spine_width_px
    front_bleed_w = total_width_px - front_x
    front_bleed_h = total_height_px
    front_cover_bleed = fit_cover_to_area(front_cover, front_bleed_w, front_bleed_h)
    spread.paste(front_cover_bleed, (front_x, 0))
    print(f"[COVER] Front cover with bleed: {front_bleed_w}x{front_bleed_h} px, pasted at ({front_x},0)")

    if author_name and author_name.strip():
        from PIL import ImageDraw, ImageFont
        draw_spread = ImageDraw.Draw(spread)
        
        try:
            author_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(board_w_px * 0.025))
        except:
            author_font = ImageFont.load_default()
        
        author_text = author_name
        bbox = draw_spread.textbbox((0, 0), author_text, font=author_font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        front_board_left = front_x
        front_board_right = front_x + front_bleed_w
        author_x = front_board_left + (front_bleed_w - text_width) // 2
        
        margin_bottom_px = int(board_h_px * 0.05)
        author_y = wrap_px + board_h_px - margin_bottom_px - text_height
        
        for dx, dy in [(-2, -2), (-2, 2), (2, -2), (2, 2), (-2, 0), (2, 0), (0, -2), (0, 2)]:
            draw_spread.text((author_x + dx, author_y + dy), author_text, font=author_font, fill="#000000")
        draw_spread.text((author_x, author_y), author_text, font=author_font, fill="#FFFFFF")
        print(f"[COVER] Added author name to spread front cover: '{author_name}'")

    spine_x = wrap_px + board_w_px
    spine_img = Image.new("RGB", (spine_width_px, total_height_px), "#2E1A47")
    spread.paste(spine_img, (spine_x, 0))

    if book_id == "magic_chef":
        if language == "es":
            article = "La" if gender == "female" else "El"
            title = f"{child_name} {article} Chef Mágico"
        else:
            title = f"{child_name} The Magic Chef"
    elif book_id == "magic_inventor":
        if language == "es":
            title = f"{child_name} y los Inventos Mágicos"
        else:
            title = f"{child_name} Magic Inventor"
    elif book_id == "star_keeper":
        if language == "es":
            title = f"{child_name} Guardián de Estrellas"
        else:
            title = f"{child_name} The Star Keeper"
    elif book_id == "furry_love":
        pet_name = traits.get('pet_name', '')
        if language == "es":
            title = f"El día que {pet_name} conoció a {child_name}"
        else:
            title = f"The day {pet_name} met {child_name}"
    elif book_id == "furry_love_adventure":
        pet_name = traits.get('pet_name', '')
        if language == "es":
            title = f"Las aventuras de {pet_name} y {child_name}"
        else:
            title = f"The Adventures of {pet_name} and {child_name}"
    elif book_id == "furry_love_teen":
        pet_name = traits.get('pet_name', '')
        if language == "es":
            title = f"{child_name} y su compañero fiel {pet_name}"
        else:
            title = f"{child_name} and Their Faithful Companion {pet_name}"
    elif book_id == "furry_love_adult":
        pet_name = traits.get('pet_name', '')
        if language == "es":
            title = f"La Gran Aventura de {child_name} y {pet_name}"
        else:
            title = f"The Great Adventure of {child_name} and {pet_name}"
    else:
        title = "El Jardín del Dragón" if language == "es" else "The Dragon Garden"
    author = author_name if author_name else "Magic Memories Books"

    try:
        spine_title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(spine_width_px * 0.45))
        spine_author_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(spine_width_px * 0.35))
    except:
        spine_title_font = ImageFont.load_default()
        spine_author_font = spine_title_font

    spine_text_img = Image.new("RGBA", (total_height_px, spine_width_px), (46, 26, 71, 255))
    spine_text_draw = ImageDraw.Draw(spine_text_img)

    title_bbox = spine_text_draw.textbbox((0, 0), title, font=spine_title_font)
    author_bbox = spine_text_draw.textbbox((0, 0), author, font=spine_author_font)
    author_width = author_bbox[2] - author_bbox[0]

    title_x = int(total_height_px * 0.1)
    text_y = (spine_width_px - (title_bbox[3] - title_bbox[1])) // 2
    spine_text_draw.text((title_x, text_y), title, font=spine_title_font, fill="#FFFFFF")

    author_x = total_height_px - author_width - int(total_height_px * 0.1)
    author_y = (spine_width_px - (author_bbox[3] - author_bbox[1])) // 2
    spine_text_draw.text((author_x, author_y), author, font=spine_author_font, fill="#FFD700")

    spine_rotated = spine_text_img.rotate(90, expand=True)
    spread.paste(spine_rotated, (spine_x, 0))

    draw = ImageDraw.Draw(spread)

    safe_margin_px = int(18 * MM_TO_INCH * DPI)

    front_cover_start_x = front_x
    title_center_x = front_cover_start_x + (cover_width_px // 2)
    title_y = wrap_px + safe_margin_px
    
    # 1.5cm margin from each side (in pixels at 300 DPI)
    margin_15cm_px = int(15 * MM_TO_INCH * DPI)  # 15mm = 1.5cm
    max_title_width = cover_width_px - (2 * margin_15cm_px)
    
    try:
        # Reduced font size for better fit
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(cover_width_px * 0.055))
        subtitle_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(cover_width_px * 0.035))
    except:
        title_font = ImageFont.load_default()
        subtitle_font = title_font
    
    if book_id == "magic_chef":
        if language == "es":
            article = "La" if gender == "female" else "El"
            main_title = f"{child_name} {article} Chef Mágico"
        else:
            main_title = f"{child_name} The Magic Chef"
    elif book_id == "magic_inventor":
        if language == "es":
            main_title = f"{child_name} y los Inventos Mágicos"
        else:
            main_title = f"{child_name} and the Magic Inventor Workshop"
    elif book_id == "star_keeper":
        if language == "es":
            main_title = f"El Guardián de Estrellas"
        else:
            main_title = f"The Star Keeper"
    elif book_id == "furry_love":
        pet_name_cover = traits.get('pet_name', '')
        if language == "es":
            main_title = f"El día que {pet_name_cover} conoció a {child_name}"
        else:
            main_title = f"The day {pet_name_cover} met {child_name}"
    elif book_id == "furry_love_adventure":
        pet_name_cover = traits.get('pet_name', '')
        if language == "es":
            main_title = f"Las aventuras de {pet_name_cover} y {child_name}"
        else:
            main_title = f"The Adventures of {pet_name_cover} and {child_name}"
    elif book_id == "furry_love_teen":
        pet_name_cover = traits.get('pet_name', '')
        if language == "es":
            main_title = f"{child_name} y su compañero fiel {pet_name_cover}"
        else:
            main_title = f"{child_name} and Their Faithful Companion {pet_name_cover}"
    elif book_id == "furry_love_adult":
        pet_name_cover = traits.get('pet_name', '')
        if language == "es":
            main_title = f"La Gran Aventura de {child_name} y {pet_name_cover}"
        else:
            main_title = f"The Great Adventure of {child_name} and {pet_name_cover}"
    else:
        main_title = "El Jardín del Dragón" if language == "es" else "The Dragon Garden"
    subtitle = f"Una aventura de {child_name}" if language == "es" else f"An adventure of {child_name}"
    
    # Word wrap function for title if it exceeds max width
    def wrap_text(text, font, max_width):
        words = text.split()
        lines = []
        current_line = ""
        for word in words:
            test_line = f"{current_line} {word}".strip()
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        return lines
    
    title_lines = wrap_text(main_title, title_font, max_title_width)
    line_height = int(cover_width_px * 0.065)
    
    title_color = "#4A1A6B" if book_id in ("furry_love", "furry_love_adventure", "furry_love_teen", "furry_love_adult") else "#C62828"
    
    for i, line in enumerate(title_lines):
        line_y = title_y + (i * line_height)
        bbox = draw.textbbox((0, 0), line, font=title_font)
        tw = bbox[2] - bbox[0]
        line_x = title_center_x - tw // 2
        
        for dx, dy in [(-3,-3),(-3,0),(-3,3),(0,-3),(0,3),(3,-3),(3,0),(3,3)]:
            draw.text((line_x + dx, line_y + dy), line, font=title_font, fill="#FFFFFF")
        draw.text((line_x, line_y), line, font=title_font, fill=title_color)
    
    # Position subtitle after all title lines
    subtitle_y = title_y + (len(title_lines) * line_height) + int(cover_width_px * 0.02)
    for offset in [(2, 2), (-2, -2)]:
        bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
        tw = bbox[2] - bbox[0]
        draw.text((title_center_x - tw//2 + offset[0], subtitle_y + offset[1]), subtitle, font=subtitle_font, fill="#FFFFFF")
    
    bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
    tw = bbox[2] - bbox[0]
    draw.text((title_center_x - tw//2, subtitle_y), subtitle, font=subtitle_font, fill="#1565C0")
    
    if not is_furry:
        try:
            logo_path = "static/images/logo_main.jpg"
            if os.path.exists(logo_path):
                logo = Image.open(logo_path).convert("RGBA")
                logo_size = int(cover_width_px * 0.25)
                logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
                logo_x = wrap_px + cover_width_px - logo_size - safe_margin_px
                logo_y = wrap_px + cover_height_px - logo_size - safe_margin_px
                if logo.mode == 'RGBA':
                    spread.paste(logo, (logo_x, logo_y), logo)
                else:
                    spread.paste(logo, (logo_x, logo_y))
                print(f"[COVER] Logo added to back cover (right side)")
        except Exception as e:
            print(f"[COVER] Could not add logo: {e}")
    else:
        print(f"[COVER] Skipping logo overlay for furry_love (logo already in fixed back cover)")
    
    print(f"[COVER] Cover spread complete: {spread.size}")
    return spread


def save_cover_as_pdf(cover_spread: Image.Image, output_path: str) -> str:
    """Save cover spread as PDF for Lulu printing."""
    cover_spread.save(output_path, "PDF", resolution=300)
    print(f"[COVER] Saved cover PDF: {output_path}")
    return output_path


def generate_credits_page(language: str = "es", img_size: tuple = (768, 1024), child_name: str = "") -> Image.Image:
    """Generate the credits/copyright page.
    Uses fixed background from docs/fixed_pages/credits_background.png (copied to static/images/).
    The child's name is added dynamically.
    """
    bg_path = "static/images/credits_page_background.png"
    if os.path.exists(bg_path):
        page = Image.open(bg_path).convert("RGB")
        page = page.resize(img_size, Image.Resampling.LANCZOS)
    else:
        page = Image.new("RGB", img_size, "#FFFEF5")
    
    draw = ImageDraw.Draw(page)
    scale = img_size[0] / 768
    
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(28 * scale))
        name_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(22 * scale))
        text_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(16 * scale))
    except:
        title_font = ImageFont.load_default()
        name_font = title_font
        text_font = title_font
    
    if language == "es":
        lines = [
            ("Este libro fue creado especialmente para", "text"),
            (child_name if child_name else "ti", "name"),
            ("", "text"),
            ("Magic Memories Books", "title"),
            ("", "text"),
            ("Texto e ilustraciones generados con IA", "text"),
            ("© 2026 Magic Memories Books", "text"),
            ("Todos los derechos reservados.", "text"),
            ("", "text"),
            ("www.magicmemoriesbooks.com", "text"),
        ]
    else:
        lines = [
            ("This book was specially created for", "text"),
            (child_name if child_name else "you", "name"),
            ("", "text"),
            ("Magic Memories Books", "title"),
            ("", "text"),
            ("Text and illustrations generated with AI", "text"),
            ("© 2026 Magic Memories Books", "text"),
            ("All rights reserved.", "text"),
            ("", "text"),
            ("www.magicmemoriesbooks.com", "text"),
        ]
    
    line_height = int(35 * scale)
    start_y = int(img_size[1] * 0.25)
    
    for i, (text, text_type) in enumerate(lines):
        if text_type == "title":
            font = title_font
            fill_color = "#2E1A47"
        elif text_type == "name":
            font = name_font
            fill_color = "#8B4513"
        else:
            font = text_font
            fill_color = "#2E1A47"
        
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        x = (img_size[0] - text_width) // 2
        y = start_y + (i * line_height)
        draw.text((x, y), text, font=font, fill=fill_color)
    
    return page


def generate_full_book(
    book_id: str,
    child_name: str,
    traits: dict,
    gender: str,
    language: str = "es",
    dedication_text: str = "",
    for_print: bool = False,
    author_name: str = "Magic Memories Books",
    reference_image_path: str = None,
    reference_image_path_2: str = None,
    progress_callback=None
) -> list:
    """
    Generate all pages for the illustrated book (Lulu print structure).
    
    PDF Digital (23 pages): Portadilla, Dedicatoria, 19 escenas, Cierre, Créditos
    PDF Impreso (24 pages): Same + blank page at end
    
    Cover is generated separately for print (contraportada + lomo + portada).
    
    Returns list of PIL Images for each page.
    """
    book_config = load_book_config(book_id)
    if not book_config:
        print(f"[BOOK] Error: Unknown book_id '{book_id}'")
        return []
    
    scenes = book_config.get("scenes", [])
    closing_scene = book_config.get("closing", {})
    title_key = f"title_{language}"
    book_title_template = book_config.get(title_key, book_config.get("title_es", ""))
    pet_name = traits.get('pet_name', '') if traits else ''
    book_title = book_title_template.replace("{name}", child_name).replace("{pet_name}", pet_name)
    
    pages = []
    img_size = (1024, 1365)
    
    print(f"[BOOK] Generating illustrated book '{book_id}' for {child_name}...")
    print(f"[BOOK] Title: {book_title}")
    print(f"[BOOK] Author: '{author_name}'")
    print(f"[BOOK] Traits: {traits}")
    print(f"[BOOK] Gender: {gender}, Language: {language}, For print: {for_print}")
    if reference_image_path:
        print(f"[BOOK] Reference image: {reference_image_path}")
    model_label = "FLUX 2 Dev + reference" if reference_image_path else "FLUX 2 Dev"
    print(f"[BOOK] This will generate {len(scenes)} scenes with {model_label} (may take 2-3 minutes)...")
    
    title_page = Image.new("RGB", img_size, "#FFFEF5")
    draw = ImageDraw.Draw(title_page)
    
    subtitle = f"Una aventura de {child_name}" if language == "es" else f"An adventure of {child_name}"
    
    scale = img_size[0] / 1024
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(56 * scale))
        subtitle_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(36 * scale))
    except:
        title_font = ImageFont.load_default()
        subtitle_font = title_font
    
    max_text_width = int(img_size[0] * 0.72)
    title_lines = []
    words = book_title.split()
    current_line = ""
    for word in words:
        test_line = f"{current_line} {word}".strip()
        bbox = draw.textbbox((0, 0), test_line, font=title_font)
        if bbox[2] - bbox[0] <= max_text_width:
            current_line = test_line
        else:
            if current_line:
                title_lines.append(current_line)
            current_line = word
    if current_line:
        title_lines.append(current_line)
    
    title_line_height = int(66 * scale)
    total_title_height = len(title_lines) * title_line_height
    title_start_y = int(380 * scale)
    
    for idx, line in enumerate(title_lines):
        bbox = draw.textbbox((0, 0), line, font=title_font)
        text_width = bbox[2] - bbox[0]
        x = (img_size[0] - text_width) // 2
        y = title_start_y + (idx * title_line_height)
        draw.text((x, y), line, font=title_font, fill="#2E1A47")
    
    subtitle_y = title_start_y + total_title_height + int(20 * scale)
    bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
    text_width = bbox[2] - bbox[0]
    x = (img_size[0] - text_width) // 2
    draw.text((x, subtitle_y), subtitle, font=subtitle_font, fill="#5A4A6A")
    
    print(f"[BOOK] Adding author to title page: '{author_name}'")
    if author_name and author_name.strip():
        author_text = f"Escrito con amor por {author_name}" if language == "es" else f"Written with love by {author_name}"
        try:
            author_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(32 * scale))
        except:
            author_font = subtitle_font
        author_y = subtitle_y + int(60 * scale)
        bbox = draw.textbbox((0, 0), author_text, font=author_font)
        text_width = bbox[2] - bbox[0]
        x = (img_size[0] - text_width) // 2
        draw.text((x, author_y), author_text, font=author_font, fill="#4A2A6A")
    
    pages.append(title_page)
    
    dedication = generate_dedication_page(dedication_text, img_size, language)
    pages.append(dedication)
    
    failed_scene_indices = []
    total_scenes = len(scenes)
    for i, scene_config in enumerate(scenes):
        print(f"[BOOK] Generating scene {i+1}/{total_scenes}...")
        
        try:
            scene_image = generate_scene_complete(
                scene_config,
                traits,
                child_name,
                gender,
                language,
                book_id,
                reference_image_path=reference_image_path,
                reference_image_path_2=reference_image_path_2
            )
        except RuntimeError as gen_err:
            print(f"[BOOK] Scene {i+1} generation failed permanently: {gen_err}. Using placeholder.")
            scene_image = Image.new("RGB", (1024, 1365), "#FFFEF5")
            failed_scene_indices.append(i)
        
        text_key = f"text_{language}"
        text = scene_config.get(text_key, scene_config.get("text_es", ""))
        text = text.replace("{name}", child_name)
        pet_name = traits.get('pet_name', '')
        if pet_name:
            text = text.replace("{pet_name}", pet_name)
        
        position = scene_config.get("text_position", "split")
        
        final_page = add_text_to_image(
            scene_image,
            text,
            position,
            "#FFFFFF",
            "#000000",
            52,
            0.05
        )
        
        pages.append(final_page)
        if progress_callback:
            try:
                progress_callback(i + 1, total_scenes)
            except Exception:
                pass
    
    if failed_scene_indices:
        print(f"[BOOK] WARNING: {len(failed_scene_indices)} scenes failed: {[i+1 for i in failed_scene_indices]}")
    
    print(f"[BOOK] Generating closing illustration (page 20)...")
    closing_page = generate_closing_page(traits, child_name, gender, img_size, book_id, reference_image_path=reference_image_path, reference_image_path_2=reference_image_path_2)
    pages.append(closing_page)
    
    credits_page = generate_credits_page(language, img_size, child_name)
    pages.append(credits_page)
    
    if for_print:
        blank_page = Image.new("RGB", img_size, "#FFFEF5")
        pages.append(blank_page)
    
    print(f"[BOOK] Book generation complete! {len(pages)} pages ({len(failed_scene_indices)} failed)")
    
    return pages, failed_scene_indices


def save_book_as_images(pages: list, output_dir: str, prefix: str = "page", with_watermark: bool = True) -> dict:
    """
    Save all pages as individual image files.
    Returns dict with 'preview' (watermarked) and 'original' (clean) paths.
    
    Args:
        pages: List of PIL Image objects
        output_dir: Directory to save images
        prefix: Prefix for file names
        with_watermark: If True, also save watermarked versions for preview
        
    Returns:
        dict with 'preview' and 'original' path lists
    """
    os.makedirs(output_dir, exist_ok=True)
    original_paths = []
    preview_paths = []
    
    for i, page in enumerate(pages):
        original_path = os.path.join(output_dir, f"{prefix}_{i+1:02d}.png")
        page.save(original_path, "PNG")
        original_paths.append(original_path)
        
        if with_watermark:
            preview_path = os.path.join(output_dir, f"{prefix}_{i+1:02d}_preview.png")
            watermarked = add_watermark(page)
            watermarked.save(preview_path, "PNG")
            preview_paths.append(preview_path)
        else:
            preview_paths.append(original_path)
    
    return {
        'original': original_paths,
        'preview': preview_paths
    }


def generate_full_book_with_inpainting(
    book_id: str,
    child_name: str,
    child_description: str,
    gender: str,
    language: str = "es",
    dedication_text: str = ""
) -> list:
    """
    Legacy wrapper - converts child_description string to traits dict.
    For new code, use generate_full_book() with traits dict directly.
    """
    traits = parse_description_to_traits(child_description)
    return generate_full_book(book_id, child_name, traits, gender, language, dedication_text)


def parse_description_to_traits(description: str) -> dict:
    """Parse free-form description to traits dict."""
    desc_lower = description.lower()
    
    traits = {
        'hair_color': 'brown',
        'hair_length': 'medium',
        'hair_type': 'straight',
        'eye_color': 'brown',
        'skin_tone': 'light'
    }
    
    if 'blonde' in desc_lower or 'rubia' in desc_lower or 'rubio' in desc_lower:
        traits['hair_color'] = 'blonde'
    elif 'black' in desc_lower or 'negro' in desc_lower:
        traits['hair_color'] = 'black'
    elif 'red' in desc_lower or 'rojo' in desc_lower or 'pelirroj' in desc_lower:
        traits['hair_color'] = 'red'
    elif 'auburn' in desc_lower or 'castaño' in desc_lower:
        traits['hair_color'] = 'auburn'
    
    if 'curly' in desc_lower or 'rizado' in desc_lower:
        traits['hair_type'] = 'curly'
    elif 'wavy' in desc_lower or 'ondulado' in desc_lower:
        traits['hair_type'] = 'wavy'
    
    if 'long' in desc_lower or 'largo' in desc_lower:
        traits['hair_length'] = 'long'
    elif 'short' in desc_lower or 'corto' in desc_lower:
        traits['hair_length'] = 'short'
    
    if 'green' in desc_lower or 'verde' in desc_lower:
        traits['eye_color'] = 'green'
    elif 'blue' in desc_lower or 'azul' in desc_lower:
        traits['eye_color'] = 'blue'
    elif 'hazel' in desc_lower or 'avellana' in desc_lower:
        traits['eye_color'] = 'hazel'
    
    if 'dark' in desc_lower or 'oscura' in desc_lower:
        traits['skin_tone'] = 'dark'
    elif 'tan' in desc_lower or 'morena' in desc_lower:
        traits['skin_tone'] = 'tan'
    elif 'olive' in desc_lower or 'oliva' in desc_lower:
        traits['skin_tone'] = 'olive'
    
    return traits


def generate_illustrated_book_pdf(
    pages: list = None,
    output_path: str = "",
    for_print: bool = False,
    page_paths: list = None
) -> str:
    """
    Convert images to PDF file. Accepts either PIL Images or file paths.
    When page_paths is provided, images are loaded and released one at a time
    to keep peak RAM low (~30 MB instead of ~700 MB for 24 pages at 300 DPI).

    Args:
        pages: List of PIL Image objects (used when page_paths is None)
        output_path: Path to save the PDF
        for_print: If True, upscale to print quality (300 DPI for A4)
        page_paths: List of file path strings (preferred for memory efficiency)

    Returns:
        Path to the generated PDF
    """
    import gc
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    if for_print:
        page_width = 2551
        page_height = 3579
        dpi = 300
        pdf_width = 612.28
        pdf_height = 858.90
    else:
        page_width = 595
        page_height = 842
        dpi = 72
        pdf_width = 595
        pdf_height = 842

    c = canvas.Canvas(output_path, pagesize=(pdf_width, pdf_height))

    source = page_paths if page_paths else (pages or [])
    total = len(source)

    for i, item in enumerate(source):
        if page_paths:
            path = item.lstrip('/') if isinstance(item, str) else item
            page = Image.open(path)
        else:
            page = item

        if for_print:
            upscaled = page.resize((page_width, page_height), Image.Resampling.LANCZOS)
        else:
            upscaled = page.resize((int(pdf_width), int(pdf_height)), Image.Resampling.LANCZOS)

        img_buffer = BytesIO()
        if upscaled.mode == 'RGBA':
            upscaled = upscaled.convert('RGB')
        upscaled.save(img_buffer, format='JPEG', quality=85, dpi=(dpi, dpi))
        img_buffer.seek(0)

        img_reader = ImageReader(img_buffer)
        c.drawImage(img_reader, 0, 0, width=pdf_width, height=pdf_height)

        if i < total - 1:
            c.showPage()

        if page_paths:
            del upscaled, page, img_buffer, img_reader
            gc.collect()

    c.save()
    print(f"[PDF] Generated PDF with {total} pages: {output_path}")

    return output_path


def generate_complete_lulu_files(
    book_id: str,
    child_name: str,
    email: str,
    traits: dict,
    gender: str,
    language: str,
    dedication_text: str
) -> dict:
    """
    Generate all files needed for Lulu printing:
    1. Generate full book (23/24 pages)
    2. Generate cover spread (front + spine + back)
    3. Create PDFs for both
    4. Save to lulu_orders folder
    
    Returns dict with paths to all generated files.
    """
    from services.lulu_storage import create_order_folder, save_interior_pdf, save_cover_pdf
    
    print(f"[LULU] Starting complete book generation for {child_name}...")
    
    order_folder = create_order_folder(book_id, child_name, email)
    
    print(f"[LULU] Generating interior pages (24 pages for print)...")
    pages, _failed = generate_full_book(
        book_id=book_id,
        child_name=child_name,
        traits=traits,
        gender=gender,
        language=language,
        dedication_text=dedication_text,
        for_print=True
    )
    
    interior_path = os.path.join(order_folder, "interior.pdf")
    generate_illustrated_book_pdf(pages, interior_path, for_print=True)
    
    print(f"[LULU] Generating cover spread...")
    cover_spread = generate_cover_spread(traits, child_name, gender, language, book_id)
    
    cover_path = os.path.join(order_folder, "cover.pdf")
    save_cover_as_pdf(cover_spread, cover_path)
    
    print(f"[LULU] All files generated and saved to: {order_folder}")
    
    return {
        "order_folder": order_folder,
        "interior_pdf": interior_path,
        "cover_pdf": cover_path,
        "pages": pages,
        "cover_spread": cover_spread
    }
