"""
Replicate API Service for FLUX image generation with character consistency.
Uses FLUX 2 Pro for previews and base character, FLUX 2 Pro for scene illustrations.
Updated: All previews now use FLUX 2 Pro for better quality and consistency.
"""
import os
import replicate
import requests
import time
import hashlib

# Configurar el token explícitamente al importar el módulo
_replicate_token = os.environ.get("REPLICATE_API_TOKEN", "")
if _replicate_token:
    replicate.Client.api_token = _replicate_token
    replicate.default_client = replicate.Client(api_token=_replicate_token)

FLUX_DEV_MODEL = "black-forest-labs/flux-dev:6e4a938f85952bdabcc15aa329178c4d681c52bf25a0342403287dc26944661d"
FLUX_2_DEV_MODEL = "black-forest-labs/flux-2-dev:7bba46bdde863cfd7aaee87649a5aa49f39f368495dbea500998d1fcbb262050"
FLUX_KONTEXT_MODEL = "black-forest-labs/flux-kontext-pro"
FLUX_2_PRO_MODEL = "black-forest-labs/flux-2-pro:285631b5656a1839331cd9af0d82da820e2075db12046d1d061c681b2f206bc6"
IDEOGRAM_CHARACTER_MODEL = "ideogram-ai/ideogram-character:1f8e198263a0d8171b76c55907c294e933e1e7d55e2d0c54f319c0e4a42c723d"

BABY_STORY_IDS = ['baby_soft_world', 'baby_puppy_love', 'baby_first_pet', 'baby_guardian_light']

# Reference images for consistency (static assets)
PUPPY_PLUSH_REFERENCE = "static/assets/puppy_plush_reference.png"
KITTEN_REFERENCE = "static/assets/kitten_reference.png"


def get_traits_hash(traits: dict) -> str:
    """Generate hash from traits for caching."""
    trait_str = f"{traits.get('hair_color','')}-{traits.get('skin_tone','')}-{traits.get('eye_color','')}"
    return hashlib.md5(trait_str.encode()).hexdigest()[:8]


def save_image_locally(image_url: str, local_path: str) -> str:
    """Download and save image locally."""
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    
    response = requests.get(image_url)
    if response.status_code == 200:
        with open(local_path, 'wb') as f:
            f.write(response.content)
        print(f"Saved: {local_path}")
        return local_path
    else:
        print(f"Failed to save: {response.status_code}")
        return None


def get_unified_skin_description(skin_tone: str) -> str:
    """Unified skin tone mapping for better AI consistency."""
    skin_map = {
        'light': 'fair light pink skin with soft rosy undertones, clearly light-skinned Caucasian',
        'medium': 'warm olive tan skin with golden undertones, Mediterranean complexion',
        'dark': 'deep rich dark brown skin with warm chocolate undertones, clearly dark-skinned African complexion',
        'very_light': 'very fair pale skin with pink undertones, clearly light-skinned',
        'tan': 'warm golden tan skin, sun-kissed bronze complexion',
        'medium_light': 'light olive skin with warm undertones, lightly tanned European complexion',
        'medium_dark': 'warm brown skin with caramel undertones, Latin or South Asian complexion'
    }
    return skin_map.get(skin_tone, 'warm olive tan skin with golden undertones')


def get_gender_negative_prompt(gender: str) -> str:
    """Get gender-specific negative prompts to avoid inappropriate attributes."""
    base_negative = "text, watermark, signature, logo, letters, words, ugly, deformed, blurry, low quality, distorted face, tail, animal tail, dragon tail, cat tail, bunny tail, wings on child, animal features, furry, animal ears, cat ears, bunny ears, extra limbs, hybrid creature"
    if gender == 'male':
        return f"{base_negative}, earrings, jewelry, bows, ribbons, makeup, lipstick, feminine accessories, girl features, ponytails, pigtails"
    elif gender == 'female':
        return f"{base_negative}, masculine features, boy haircut"
    return base_negative


def generate_base_character(traits: dict, output_dir: str, gender: str = "neutral", style: str = "", age_range: str = "0-1", story_id: str = "", model: str = None) -> str:
    """
    Generate a base character portrait with specific traits.
    This portrait will be used as reference for all scene illustrations.
    Returns local path to saved image.
    """
    from services.fixed_stories import get_hair_description, get_eye_description, get_skin_tone, get_gender_child, STORIES
    
    print("\n" + "=" * 50)
    print("PHASE 1: Generating Base Character Portrait")
    print("=" * 50)
    
    hair_desc = get_hair_description(traits)
    eye_desc = get_eye_description(traits)
    skin_desc = get_unified_skin_description(traits.get('skin_tone', 'light'))
    skin_tone = get_skin_tone(traits.get('skin_tone', 'light'))
    gender_child = get_gender_child(gender)
    
    hair_color = traits.get('hair_color', 'brown')
    hair_length = traits.get('hair_length', 'medium')
    hair_type = traits.get('hair_type', 'straight')
    child_age = int(traits.get('child_age', '4'))
    age_display = f"{child_age} year old" if child_age > 0 else "baby"
    
    is_baby = age_range in ['0-1', '0-2']
    is_birthday = story_id.startswith('birthday_') if story_id else False
    
    story_config = STORIES.get(story_id, {})
    is_toddler = is_baby and child_age >= 1
    if is_toddler and 'preview_prompt_override_toddler' in story_config:
        preview_prompt_override = story_config.get('preview_prompt_override_toddler', None)
        print(f"[PREVIEW] Using TODDLER preview prompt (child_age={child_age})")
    else:
        preview_prompt_override = story_config.get('preview_prompt_override', None)
    
    if preview_prompt_override:
        if is_baby:
            gender_word = "baby boy" if gender == "male" else "baby girl" if gender == "female" else "baby"
        else:
            gender_word = "little boy" if gender == "male" else "little girl" if gender == "female" else "child"
        gender_features = "young boy features" if gender == "male" else "young girl features, soft round cheeks" if gender == "female" else ""
        
        try:
            from services.fixed_stories import PUPPY_DESC, KITTEN_DESC, BUNNY_DESC, GUARDIAN_LIGHT_DESC, SPARK_DESC, LILA_DESC, DOG_FOREVER_DESC, get_hair_action
            if is_baby:
                scene_style = "clean illustration only, pure artwork, professional children's book quality"
            else:
                scene_style = "NO text, NO watermark, NO signature, NO logo, NO artist name, NO handwriting, NO calligraphy, clean illustration only"
            hair_action = get_hair_action(traits)
            portrait_prompt = preview_prompt_override.format(
                gender_word=gender_word,
                gender_child=gender_child,
                gender_features=gender_features,
                age_display=age_display,
                hair_desc=hair_desc,
                eye_desc=eye_desc,
                skin_desc=skin_desc,
                skin_tone=skin_tone,
                hair_color=hair_color,
                hair_length=hair_length,
                hair_type=hair_type,
                style=scene_style,
                hair_action=hair_action,
                puppy_desc=PUPPY_DESC,
                kitten_desc=KITTEN_DESC,
                bunny_desc=BUNNY_DESC,
                guardian_light_desc=GUARDIAN_LIGHT_DESC,
                spark_desc=SPARK_DESC.format(gender_word=gender_word),
                lila_desc=LILA_DESC.format(gender_word=gender_word),
                dog_forever_desc=DOG_FOREVER_DESC.format(gender_word=gender_word)
            )
            if is_baby:
                from services.fixed_stories import adapt_baby_pose_for_age
                portrait_prompt = adapt_baby_pose_for_age(portrait_prompt, child_age)
            if hair_length == 'very_little' and 'STRICT:' in portrait_prompt:
                portrait_prompt = portrait_prompt.replace('STRICT:', 'STRICT: Baby head is completely smooth and bald-looking with only thin peach fuzz on bare scalp, head shape fully visible and round,')
            print(f"Using preview_prompt_override for story: {story_id}")
        except KeyError as e:
            print(f"Warning: Missing variable {e} in preview_prompt_override, using fallback")
            portrait_prompt = None
    else:
        portrait_prompt = None
    
    if not portrait_prompt and is_birthday:
        gender_word = "little boy" if gender == "male" else "little girl" if gender == "female" else "child"
        gender_features = "young boy features" if gender == "male" else "young girl features" if gender == "female" else ""
        portrait_prompt = f"""Full body illustration of a happy {gender_word} ({age_display}) with {hair_desc}, {eye_desc}, and {skin_desc}.
{gender_features}
The {gender_child} is standing at a birthday party celebration.
Wearing a cute party outfit.
Joyful excited expression, big happy smile.
Colorful birthday background with balloons, streamers, confetti, and a birthday cake with candles.
Festive party atmosphere with warm cheerful lighting.
High quality children's storybook illustration style, soft watercolor textures, magical warm lighting.
Clear view of full body, face clearly visible.
Professional illustration, centered composition.
No text, no watermarks, no signatures."""
    
    if not portrait_prompt and is_baby:
        child_age = int(traits.get('child_age', '1'))
        gender_word = "baby boy" if gender == "male" else "baby girl" if gender == "female" else "baby"
        gender_features = "masculine baby features, short hair" if gender == "male" else "feminine baby features" if gender == "female" else ""
        
        baby_hair_note = ""
        hair_length = traits.get('hair_length', 'medium')
        if child_age == 0:
            age_desc = f"a tiny infant {gender_word} (6-9 months old), very small baby proportions, chubby cheeks, round baby face"
            pose_desc = "lying peacefully on their back on a soft pastel blanket, tiny arms and legs relaxed"
        elif child_age == 1:
            age_desc = f"an adorable {gender_word} (12 months old, 1 year old), baby proportions, chubby cheeks, learning to stand"
            pose_desc = "sitting happily on a soft pastel blanket, holding a soft toy"
        else:
            age_desc = f"a cute toddler {gender_word} (2 years old), small toddler proportions, round face, can walk"
            pose_desc = "standing on tiny feet in a cozy nursery, taking first steps"
        
        if hair_length == 'very_little':
            baby_hair_note = f"IMPORTANT: This baby has very little hair, just a thin soft fuzz of {traits.get('hair_color', 'brown')} hair on the head. Do NOT give this baby thick or long hair."
        
        portrait_prompt = f"""Full body illustration of {age_desc} with {hair_desc}, {eye_desc}, and {skin_desc}.
{gender_features}
{baby_hair_note}
The {gender_word} is {pose_desc} in a cozy nursery setting.
Wearing a simple soft white onesie with no decorations.
Sweet innocent expression, gentle happy smile.
Soft pastel pink, cream and lavender background with gentle floating sparkles.
High quality children's storybook illustration style, soft watercolor textures, magical warm lighting.
Clear view of full body, face clearly visible.
Professional illustration, centered composition.
No accessories, no jewelry, no earrings.
No text, no watermarks, no signatures."""
    elif not portrait_prompt and story_id in ['magic_chef', 'magic_chef_illustrated']:
        child_age = int(traits.get('child_age', '5'))
        gender_word = "little boy" if gender == "male" else "little girl" if gender == "female" else "child"
        gender_features = "young boy features" if gender == "male" else "young girl features" if gender == "female" else ""
        
        if child_age <= 3:
            age_desc = f"a very small toddler exactly {child_age} years old, tiny body proportions, chubby cheeks, round baby face, very short height"
        elif child_age <= 5:
            age_desc = f"a small preschool child exactly {child_age} years old, small body, round childish face, short height"
        elif child_age <= 7:
            age_desc = f"a young child exactly {child_age} years old, slender body, child face losing baby fat, medium-short height"
        else:
            age_desc = f"an older child exactly {child_age} years old, taller slender body, more mature child face, longer limbs, school-age proportions"
        
        portrait_prompt = f"""Full body illustration of {age_desc}, {gender_word} with {hair_desc}, {eye_desc}, and {skin_desc}.
{gender_features}
The {gender_word} is standing in a magical kitchen setting wearing a cute white chef's hat with cartoon eyes and smile, and an elegant white chef jacket with golden buttons.
A cute rainbow layered cake character (Sweetie) with cartoon eyes and smile floats beside them.
Bright joyful expression, happy excited smile.
Magical pink kitchen background with floating desserts, cookies, cupcakes, sparkles and golden stars.
High quality children's storybook illustration style, soft watercolor textures, magical warm lighting.
Clear view of full body, face clearly visible.
Professional illustration, centered composition.
No earrings, no jewelry, no accessories on body.
No text, no watermarks, no signatures."""
    elif not portrait_prompt and story_id in ['dragon_garden', 'dragon_garden_illustrated']:
        child_age = int(traits.get('child_age', '5'))
        gender_word = "little boy" if gender == "male" else "little girl" if gender == "female" else "child"
        gender_features = "young boy features" if gender == "male" else "young girl features" if gender == "female" else ""
        outfit = "cozy green tunic with brown pants and small boots" if gender == "male" else "flowing lavender dress with small boots"
        spark_desc = "SPARK: a cute chubby baby dragon, shimmering emerald green scales, large round golden eyes, small translucent wings, friendly smile, cream belly, two tiny horns - Spark is TWICE AS TALL as the child (2x the child's height), chunky round body bigger than the child"
        
        if child_age <= 1:
            body_desc = "extremely small baby body, very chubby round face, short stubby limbs"
            age_display = "baby"
        elif child_age == 2:
            body_desc = "small toddler body, round chubby cheeks, short limbs"
            age_display = "2 year old toddler"
        elif child_age <= 4:
            body_desc = "toddler body proportions, chubby cheeks, short legs"
            age_display = f"{child_age} year old toddler"
        elif child_age <= 6:
            body_desc = "young child body proportions, slightly chubby face, small stature"
            age_display = f"{child_age} year old young child"
        else:
            body_desc = "child body proportions, longer limbs"
            age_display = f"{child_age} year old child"
        
        portrait_prompt = f"SCENE: Entrance to a magical and enchanted garden with bright flowers, a centuries-old oak tree, floating butterflies, and a soft golden morning light. {gender_word}, appropriate to their {age_display} with {body_desc}, {hair_desc}, {eye_desc}, and {skin_desc}, dressed in {outfit}, stands in the magical garden with a cheerful and curious expression. {gender_word} is standing next to SPARK: a cute, chubby baby dragon TWICE AS TALL as {gender_word} and has shimmering emerald-green scales, large, round, golden eyes, small translucent red wings, a friendly smile, a cream-colored belly, and two small red horns. Spark is TWICE AS TALL as the child (twice the child's height), with a round, thick body larger than {gender_word}. SPARK is standing next to {gender_word}, greeting the viewer with a friendly gesture. Watercolor illustration from a children's storybook, with soft, luminous colors and warm, magical lighting."
    elif not portrait_prompt:
        child_age = int(traits.get('child_age', '5'))
        gender_word = "little boy" if gender == "male" else "little girl" if gender == "female" else "child"
        gender_features = "young boy features" if gender == "male" else "young girl features" if gender == "female" else ""
        
        if child_age <= 3:
            age_desc = f"a very small toddler exactly {child_age} years old, tiny body proportions, chubby cheeks, round baby face, very short height"
        elif child_age <= 5:
            age_desc = f"a small preschool child exactly {child_age} years old, small body, round childish face, short height"
        elif child_age <= 7:
            age_desc = f"a young child exactly {child_age} years old, slender body, child face losing baby fat, medium-short height"
        else:
            age_desc = f"an older child exactly {child_age} years old, taller slender body, more mature child face, longer limbs, school-age proportions"
        
        portrait_prompt = f"""Full body illustration of {age_desc}, {gender_word} with {hair_desc}, {eye_desc}, and {skin_desc}.
{gender_features}
The {gender_word} is standing in a magical garden setting with flowers.
Wearing comfortable adventure clothes - simple shirt and shorts/dress.
Bright curious expression, happy smile.
Soft magical background with gentle warm light and floating sparkles.
High quality children's storybook illustration style, soft watercolor textures, magical warm lighting.
Clear view of full body, face clearly visible.
Professional illustration, centered composition.
No earrings, no jewelry, no accessories on body.
No text, no watermarks, no signatures."""

    use_model = model if model else FLUX_2_PRO_MODEL
    model_name = "FLUX Dev" if "flux-dev" in use_model else "FLUX 2 Pro"
    print(f"Portrait: {gender_word} with {hair_desc}, {eye_desc}, {skin_desc}")
    print(f"[PREVIEW] Using {model_name} for base character generation")
    print(f"\n===== PROMPT ENVIADO A FLUX =====\n{portrait_prompt}\n===== FIN PROMPT =====")
    
    try:
        input_params = {
            "prompt": portrait_prompt,
            "aspect_ratio": "3:4",
            "output_format": "png",
        }
        if "flux-dev" not in use_model:
            input_params["safety_tolerance"] = 5
        
        output = replicate.run(use_model, input=input_params)
        
        if isinstance(output, str):
            image_url = output
        elif isinstance(output, list) and len(output) > 0:
            image_url = str(output[0])
        else:
            image_url = str(output)
        
        os.makedirs(output_dir, exist_ok=True)
        base_path = f"{output_dir}/base_character.png"
        save_image_locally(image_url, base_path)
        
        print(f"Base character portrait generated with {model_name}!")
        return base_path
        
    except Exception as e:
        print(f"Error generating base character: {e}")
        raise


def generate_scene_with_kontext(scene_prompt: str, base_image_path: str, scene_num: int, 
                                 aspect_ratio: str = "3:4", output_dir: str = "generated",
                                 gender: str = "neutral", max_retries: int = 3, age_range: str = "0-1",
                                 additional_references: list = None, hair_length: str = "medium",
                                 child_age: int = None) -> str:
    """
    Generate a scene illustration using FLUX 2 Pro, preserving the base character.
    The base image is used as reference to maintain character consistency.
    Includes retry logic and fallback to FLUX Dev if FLUX 2 Pro fails.
    
    Args:
        additional_references: List of additional image paths to use as references (e.g., plush toy)
        hair_length: Hair length trait ('very_little' for sparse baby hair)
        child_age: Age of the child in years (0, 1, 2, etc.)
    """
    print(f"\n--- Generating Scene {scene_num} with FLUX 2 Pro ---")
    
    is_baby = age_range in ['0-1', '0-2']
    if is_baby:
        gender_word = "baby boy" if gender == "male" else "baby girl" if gender == "female" else "baby"
    else:
        gender_word = "little boy" if gender == "male" else "little girl" if gender == "female" else "child"
    
    baby_notes = ""
    if is_baby:
        if hair_length == 'very_little':
            baby_notes += f"\nCRITICAL HAIR: This {gender_word} has VERY LITTLE HAIR - only thin soft peach fuzz on the head. Do NOT give this baby thick hair, long hair, or styled hair. The head should be mostly visible with barely any hair."
        if child_age is not None and child_age == 0:
            baby_notes += f"\nCRITICAL POSE: This is a 0-12 month old infant. The {gender_word} CANNOT stand or walk. The {gender_word} MUST ONLY be lying down, sitting supported, or crawling on belly. NEVER show the {gender_word} standing upright or walking on feet."
    
    negative_prompt = get_gender_negative_prompt(gender)
    
    if is_baby and child_age is not None and child_age == 0:
        pose_instruction = f"The {gender_word} must follow the POSE described in the scene prompt exactly. This infant can ONLY sit, lie down, or crawl."
    elif is_baby:
        pose_instruction = f"ALLOW the {gender_word} to move, interact, and have different body positions as described in the scene."
    else:
        pose_instruction = f"The {gender_word} should be ACTIVE and DYNAMIC - walking, playing, reaching, celebrating - as the story describes."
    
    enhanced_prompt = f"""{scene_prompt}

CRITICAL CHARACTER CONSISTENCY: This is the SAME {gender_word} from the reference image.
Keep the {gender_word}'s APPEARANCE exactly the same: same face shape, same hair color, same hair style, same eye color, same skin tone.
The {gender_word} must be RECOGNIZABLE as the same child but in a NEW POSE and NEW ACTION as described in the scene.
{pose_instruction}
No accessories, no jewelry, no earrings on the baby.{baby_notes}
Professional children's storybook illustration, soft watercolor style, magical atmosphere.
No text, no watermarks, no signatures."""

    print(f"Scene prompt (first 200 chars): {scene_prompt[:200]}...")
    print(f"Gender: {gender_word}, Child Age: {child_age}, Hair Length: {hair_length}")
    if baby_notes:
        print(f"Baby notes applied: {baby_notes.strip()}")
    
    for attempt in range(max_retries + 1):
        try:
            # Build list of input images - base character + any additional references
            input_image_files = []
            file_handles = []
            
            # Primary reference: the character
            base_file = open(base_image_path, "rb")
            file_handles.append(base_file)
            input_image_files.append(base_file)
            
            # Additional references (e.g., plush toy for consistency)
            if additional_references:
                for ref_path in additional_references:
                    if os.path.exists(ref_path):
                        ref_file = open(ref_path, "rb")
                        file_handles.append(ref_file)
                        input_image_files.append(ref_file)
                        print(f"  Added reference image: {ref_path}")
            
            print(f"  Total reference images: {len(input_image_files)}")
            
            output = replicate.run(
                FLUX_2_PRO_MODEL,
                input={
                    "prompt": enhanced_prompt,
                    "input_images": input_image_files,
                    "aspect_ratio": aspect_ratio,
                    "output_format": "png",
                    "safety_tolerance": 5
                }
            )
            
            # Close all file handles
            for fh in file_handles:
                fh.close()
            
            # Handle different output formats from Replicate
            if isinstance(output, str):
                image_url = output
            elif isinstance(output, list) and len(output) > 0:
                image_url = str(output[0])
            else:
                image_url = str(output)
            
            local_path = f"{output_dir}/scene_{scene_num}.png"
            save_image_locally(image_url, local_path)
            
            print(f"Scene {scene_num}: Complete with FLUX 2 Pro!")
            return local_path
            
        except Exception as e:
            error_msg = str(e).lower()
            print(f"Attempt {attempt + 1} failed for scene {scene_num}: {e}")
            
            is_content_error = any(x in error_msg for x in ["safety", "nsfw", "content", "sensitive", "e005", "flagged"])
            
            if attempt < max_retries and is_content_error:
                print(f"Retrying scene {scene_num} with modified prompt (attempt {attempt + 2})...")
                enhanced_prompt = enhanced_prompt.replace("dragon", "magical creature").replace("fire", "sparkles")
                time.sleep(3 + attempt * 2)
                continue
            elif attempt == max_retries:
                print(f"Falling back to FLUX Dev for scene {scene_num}")
                return generate_scene_fallback_flux_dev(scene_prompt, scene_num, output_dir, gender, age_range)
            else:
                raise


def generate_scene_fallback_flux_dev(scene_prompt: str, scene_num: int, output_dir: str, gender: str = "neutral", age_range: str = "0-1", aspect_ratio: str = None) -> str:
    """Generate scene with FLUX Dev (standalone, no character reference).
    The scene_prompt already contains all character details (hair, skin, pose, style)
    from the scene_template in fixed_stories.py. We pass it through with minimal additions.
    """
    print(f"--- Generating Scene {scene_num} with FLUX Dev ---")
    
    if aspect_ratio:
        scene_aspect = aspect_ratio
    else:
        is_baby = age_range in ['0-1', '0-2']
        scene_aspect = "1:1" if is_baby else "3:4"
    
    final_prompt = f"""{scene_prompt}
No text, no watermarks, no signatures, no logo."""
    
    print(f"FLUX Dev prompt (first 500 chars): {final_prompt[:500]}...")
    
    try:
        output = replicate.run(
            FLUX_DEV_MODEL,
            input={
                "prompt": final_prompt,
                "aspect_ratio": scene_aspect,
                "output_format": "png",
                "num_inference_steps": 28,
                "guidance": 3.5
            }
        )
        
        if isinstance(output, list) and len(output) > 0:
            image_url = output[0]
        else:
            image_url = str(output)
        
        local_path = f"{output_dir}/scene_{scene_num}.png"
        save_image_locally(image_url, local_path)
        
        print(f"Scene {scene_num}: Generated with fallback!")
        return local_path
        
    except Exception as e:
        print(f"Fallback also failed for scene {scene_num}: {e}")
        raise






def generate_scene_with_flux2dev_no_ref(scene_prompt: str, scene_num: int, output_dir: str = "generated",
                                          aspect_ratio: str = "1:1") -> str:
    """Generate scene with FLUX 2 Dev WITHOUT reference image.
    Used for Quick Stories regeneration when cover_clean.png is not available.
    """
    print(f"--- Generating Scene {scene_num} with FLUX 2 Dev (no reference) ---")

    final_prompt = f"""{scene_prompt}
No text, no watermarks, no signatures, no logo."""

    print(f"FLUX 2 Dev (no ref) prompt (first 500 chars): {final_prompt[:500]}...")

    try:
        output = replicate.run(
            FLUX_2_DEV_MODEL,
            input={
                "prompt": final_prompt,
                "aspect_ratio": aspect_ratio,
                "output_format": "png",
                "go_fast": True
            }
        )

        if isinstance(output, list) and len(output) > 0:
            image_url = output[0]
        else:
            image_url = str(output)

        local_path = f"{output_dir}/scene_{scene_num}.png"
        save_image_locally(image_url, local_path)

        print(f"Scene {scene_num}: Generated with FLUX 2 Dev (no ref)!")
        return local_path

    except Exception as e:
        print(f"FLUX 2 Dev (no ref) failed for scene {scene_num}: {e}")
        raise


def generate_scene_with_flux2dev(scene_prompt: str, reference_image_path: str, scene_num: int,
                                  aspect_ratio: str = "1:1", output_dir: str = "generated",
                                  gender: str = "neutral", max_retries: int = 7, age_range: str = "0-1",
                                  hair_length: str = "medium", child_age: int = None) -> str:
    """
    Generate a scene using FLUX 2 Dev with native reference_images for character consistency.
    The reference image (preview/cover) is passed so FLUX 2 Dev maintains the character's appearance.
    Retries up to max_retries on transient errors (q_descale, timeout, etc.) with exponential backoff.
    NEVER falls back to a different model — raises exception if all retries exhausted.
    """
    print(f"\n--- Generating Scene {scene_num} with FLUX 2 Dev (reference_images) ---")

    is_baby = age_range in ['0-1', '0-2']
    if is_baby:
        gender_word = "baby boy" if gender == "male" else "baby girl" if gender == "female" else "baby"
    else:
        gender_word = "little boy" if gender == "male" else "little girl" if gender == "female" else "child"

    reference_note = f"CRITICAL: Keep the SAME {gender_word} appearance as the reference image - same face, same skin tone, same head/hair."
    if is_baby and hair_length == 'very_little':
        reference_note += f" This {gender_word} has a nearly bald smooth scalp with minimal fuzz - do NOT add hair volume, buns, or ponytails."

    enhanced_prompt = f"""{scene_prompt}

{reference_note}"""

    print(f"Scene prompt (first 300 chars): {scene_prompt[:300]}...")
    print(f"Gender: {gender_word}, Child Age: {child_age}, Hair Length: {hair_length}")
    print(f"Reference image: {reference_image_path}")

    if not os.path.exists(reference_image_path):
        raise Exception(f"Reference image not found at {reference_image_path}. Cannot generate scene without reference.")

    from PIL import Image as PILSanitize
    _ref_img = PILSanitize.open(reference_image_path)
    w, h = _ref_img.size
    needs_sanitize = _ref_img.mode != "RGB" or w % 64 != 0 or h % 64 != 0
    if needs_sanitize:
        _ref_img = _ref_img.convert("RGB")
        new_w = (w // 64) * 64 or 1024
        new_h = (h // 64) * 64 or 1024
        _ref_img = _ref_img.resize((new_w, new_h), PILSanitize.LANCZOS)
        _ref_img.save(reference_image_path, "PNG")
        print(f"Sanitized reference image: {w}x{h} {_ref_img.mode} → {new_w}x{new_h} RGB")
    _ref_img.close()
    del _ref_img

    for attempt in range(max_retries + 1):
        try:
            with open(reference_image_path, "rb") as ref_file:
                output = replicate.run(
                    FLUX_2_DEV_MODEL,
                    input={
                        "prompt": enhanced_prompt,
                        "input_images": [ref_file],
                        "aspect_ratio": aspect_ratio,
                        "output_format": "png",
                        "go_fast": False
                    }
                )

            if isinstance(output, str):
                image_url = output
            elif isinstance(output, list) and len(output) > 0:
                image_url = str(output[0])
            else:
                image_url = str(output)

            local_path = f"{output_dir}/scene_{scene_num}.png"
            save_image_locally(image_url, local_path)

            print(f"Scene {scene_num}: Complete with FLUX 2 Dev + reference!")
            return local_path

        except Exception as e:
            error_msg = str(e).lower()
            print(f"FLUX 2 Dev attempt {attempt + 1}/{max_retries + 1} failed for scene {scene_num}: {e}")

            is_content_error = any(x in error_msg for x in ["safety", "nsfw", "content", "sensitive", "e005", "flagged"])
            is_transient_error = any(x in error_msg for x in ["q_descale", "shape", "timeout", "overloaded", "503", "502"])

            if attempt < max_retries:
                if is_content_error:
                    print(f"Content error, retrying with modified prompt (attempt {attempt + 2})...")
                    enhanced_prompt = enhanced_prompt.replace("dragon", "magical creature").replace("fire", "sparkles")
                    time.sleep(3 + attempt * 2)
                elif is_transient_error:
                    wait_time = min(10 * (2 ** attempt), 60)
                    print(f"Transient error, retrying FLUX 2 Dev in {wait_time}s (attempt {attempt + 2}/{max_retries + 1})...")
                    time.sleep(wait_time)
                else:
                    print(f"Unknown error, retrying FLUX 2 Dev (attempt {attempt + 2})...")
                    time.sleep(5)
                continue
            else:
                raise Exception(f"FLUX 2 Dev temporarily unavailable after {max_retries + 1} attempts for scene {scene_num}. Service error: {str(e)[:100]}")


def generate_scene_with_ideogram(scene_prompt: str, reference_image_path: str, scene_num: int,
                                   aspect_ratio: str = "1:1", output_dir: str = "generated",
                                   max_retries: int = 2) -> str:
    """
    Generate a scene using Ideogram Character model for character consistency.
    Uses the preview/base_character image as reference - Ideogram auto-detects
    facial features and maintains identity across all scenes.
    
    Prompts should NOT describe the character (Ideogram gets it from the reference).
    Prompts should focus on: [Style] + [Action/Pose] + [Environment] + [Mood/Lighting]
    """
    consistency_suffix = " STRICT: Maintain exact same baby face, same head shape, same facial features as reference image. Same baby character throughout."
    if "STRICT:" in scene_prompt:
        enhanced_prompt = scene_prompt
    else:
        enhanced_prompt = scene_prompt + consistency_suffix

    print(f"\n--- Generating Scene {scene_num} with Ideogram Character ---")
    print(f"Reference: {reference_image_path}")
    print(f"Prompt (first 300 chars): {enhanced_prompt[:300]}...")

    for attempt in range(max_retries + 1):
        ref_file = None
        try:
            ref_file = open(reference_image_path, "rb")

            output = replicate.run(
                IDEOGRAM_CHARACTER_MODEL,
                input={
                    "prompt": enhanced_prompt,
                    "character_reference_image": ref_file,
                    "style_type": "Fiction",
                    "aspect_ratio": aspect_ratio,
                    "magic_prompt_option": "Auto",
                    "resolution": "None"
                }
            )

            ref_file.close()

            if isinstance(output, str):
                image_url = output
            elif hasattr(output, 'url'):
                image_url = output.url
            elif isinstance(output, list) and len(output) > 0:
                image_url = str(output[0])
            else:
                image_url = str(output)

            local_path = f"{output_dir}/scene_{scene_num}.png"
            save_image_locally(image_url, local_path)

            print(f"Scene {scene_num}: Complete with Ideogram Character!")
            return local_path

        except Exception as e:
            if ref_file and not ref_file.closed:
                ref_file.close()
            print(f"Attempt {attempt + 1} failed for scene {scene_num} (Ideogram): {e}")
            if attempt < max_retries:
                print(f"Retrying in {5 + attempt * 3}s...")
                time.sleep(5 + attempt * 3)
                continue
            else:
                print(f"Ideogram failed after {max_retries + 1} attempts. No fallback to FLUX to preserve character consistency.")
                raise Exception(f"Ideogram Character failed for scene {scene_num} after {max_retries + 1} attempts: {e}")


def generate_illustration_replicate(scene_prompt: str, scene_num: int, aspect_ratio: str = "3:4", model: str = None) -> str:
    """
    Generate illustration standalone (no character reference).
    Uses specified model or defaults to FLUX 2 Pro.
    Pass model=FLUX_DEV_MODEL for Quick Stories.
    Returns URL of generated image.
    """
    use_model = model or FLUX_2_PRO_MODEL
    is_dev_model = "flux-dev" in use_model or "flux-2-dev" in use_model
    model_name = "FLUX 2 Dev" if "flux-2-dev" in use_model else "FLUX Dev" if "flux-dev" in use_model else "FLUX 2 Pro"
    print(f"\n--- Generating Preview/Scene {scene_num} with {model_name} ---")
    print(f"Prompt: {scene_prompt[:150]}...")
    
    try:
        enhanced_prompt = scene_prompt + ". Clean professional illustration, no artist signature, no watermarks, no text overlays, no logos, no letters, no words."
        
        input_params = {
            "prompt": enhanced_prompt,
            "aspect_ratio": aspect_ratio,
            "output_format": "png",
        }
        if not is_dev_model:
            input_params["safety_tolerance"] = 5
        
        output = replicate.run(use_model, input=input_params)
        
        if isinstance(output, str):
            image_url = output
        elif isinstance(output, list) and len(output) > 0:
            image_url = str(output[0])
        else:
            image_url = str(output)
        
        print(f"Scene {scene_num}: Image ready with {model_name}!")
        return image_url
        
    except Exception as e:
        print(f"Error generating scene {scene_num}: {e}")
        raise




def create_cover_from_character(character_image_path: str, output_dir: str,
                                title: str = '', author: str = '') -> str:
    """
    Create a cover image by overlaying title + author text on the character preview image.
    Saves $0.03 per story by avoiding a separate FLUX Dev API call.
    Returns the path to the generated cover image.
    """
    from PIL import Image, ImageDraw, ImageFont
    
    os.makedirs(output_dir, exist_ok=True)
    cover_path = f"{output_dir}/cover.png"
    
    img = Image.open(character_image_path).convert('RGBA')
    
    if img.size[0] != img.size[1]:
        size = max(img.size)
        square = Image.new('RGBA', (size, size), (255, 255, 255, 255))
        x = (size - img.size[0]) // 2
        y = (size - img.size[1]) // 2
        square.paste(img, (x, y))
        img = square
    
    if img.size[0] < 1024:
        img = img.resize((1024, 1024), Image.LANCZOS)
    
    draw = ImageDraw.Draw(img)
    w, h = img.size
    
    fonts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'fonts')
    titan_path = os.path.join(fonts_dir, 'TitanOne-Regular.ttf')
    fredoka_path = os.path.join(fonts_dir, 'Fredoka-Regular.ttf')
    
    title_word_count = len(title.split()) if title else 0
    if title_word_count > 6:
        title_font_size = int(w * 0.045)
    elif title_word_count > 4:
        title_font_size = int(w * 0.05)
    else:
        title_font_size = int(w * 0.06)
    author_font_size = max(14, int(w * 0.035))
    
    try:
        title_font = ImageFont.truetype(titan_path, title_font_size) if os.path.exists(titan_path) else ImageFont.load_default()
    except:
        title_font = ImageFont.load_default()
    
    try:
        author_font = ImageFont.truetype(fredoka_path, author_font_size) if os.path.exists(fredoka_path) else ImageFont.load_default()
    except:
        author_font = ImageFont.load_default()
    
    title_color = (180, 130, 210, 255)
    border_color = (255, 255, 255, 255)
    author_color = (160, 110, 190, 230)
    
    if title:
        margin_px = int(w * 0.12)
        max_title_w = w - 2 * margin_px
        
        def wrap_title(font):
            title_bbox = draw.textbbox((0, 0), title, font=font)
            title_w = title_bbox[2] - title_bbox[0]
            if title_w > max_title_w:
                words = title.split()
                lines = []
                current = ""
                for word in words:
                    test = f"{current} {word}".strip() if current else word
                    tw = draw.textbbox((0, 0), test, font=font)[2] - draw.textbbox((0, 0), test, font=font)[0]
                    if tw <= max_title_w:
                        current = test
                    else:
                        if current:
                            lines.append(current)
                        current = word
                if current:
                    lines.append(current)
                return lines
            return [title]
        
        lines = wrap_title(title_font)
        
        if len(lines) > 4:
            title_font_size = int(title_font_size * 0.85)
            try:
                title_font = ImageFont.truetype(titan_path, title_font_size) if os.path.exists(titan_path) else ImageFont.load_default()
            except:
                title_font = ImageFont.load_default()
            lines = wrap_title(title_font)
        
        title_y = int(h * 0.06)
        line_spacing = int(title_font_size * 1.3)
        border_offset = 2
        
        max_lines = 5
        for line in lines[:max_lines]:
            line_bbox = draw.textbbox((0, 0), line, font=title_font)
            line_w = line_bbox[2] - line_bbox[0]
            line_x = (w - line_w) // 2
            if line_x < margin_px:
                line_x = margin_px
            for dx in range(-border_offset, border_offset + 1):
                for dy in range(-border_offset, border_offset + 1):
                    if dx != 0 or dy != 0:
                        draw.text((line_x + dx, title_y + dy), line, fill=border_color, font=title_font)
            draw.text((line_x, title_y), line, fill=title_color, font=title_font)
            title_y += line_spacing
    
    if author and author.strip():
        author_text = f"Autor: {author}"
        author_bbox = draw.textbbox((0, 0), author_text, font=author_font)
        author_w = author_bbox[2] - author_bbox[0]
        author_h = author_bbox[3] - author_bbox[1]
        author_x = (w - author_w) // 2
        cm2_pixels = int(w * 2.0 / 21.59) if w > 0 else 60
        author_y = h - cm2_pixels - author_h
        
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                if dx != 0 or dy != 0:
                    draw.text((author_x + dx, author_y + dy), author_text, fill=border_color, font=author_font)
        draw.text((author_x, author_y), author_text, fill=author_color, font=author_font)
    
    img = img.convert('RGB')
    img.save(cover_path, 'PNG', quality=95)
    print(f"[COVER] Created cover from character preview: {cover_path}")
    
    return cover_path


def generate_cover_only(story_id: str, gender: str, traits: dict, 
                        output_dir: str, base_character_path: str = None,
                        child_name: str = "the child", use_flux_dev: bool = False) -> dict:
    """
    Generate ONLY the cover image (Phase 1 - before payment).
    Returns dict with cover_path and base_character path for later scene generation.
    When use_flux_dev=True, uses FLUX 2 Dev with reference_images for character consistency.
    """
    from services.fixed_stories import get_cover_prompt, get_hair_description, STORIES
    import shutil
    
    story_config = STORIES.get(story_id, {})
    age_range = story_config.get('age_range', '0-1')
    hair_length = traits.get('hair_length', 'medium')
    child_age = int(traits.get('child_age', '1'))
    use_preview_as_cover = story_config.get('use_preview_as_cover', False)
    use_ideogram = story_config.get('use_ideogram_scenes', False) and age_range in ['0-1', '0-2']
    
    if use_preview_as_cover:
        model_name = "Preview Copy (FLUX 2 Pro)"
    elif use_ideogram:
        model_name = "Ideogram Character"
    elif use_flux_dev:
        model_name = "FLUX 2 Dev"
    else:
        model_name = "FLUX 2 Pro"
    
    print("=" * 60)
    print(f"COVER ONLY Generation - {model_name}")
    print(f"Story: {story_id} (Age: {age_range}, Child Age: {child_age})")
    print(f"Hair length: {hair_length}")
    print("=" * 60)
    
    os.makedirs(output_dir, exist_ok=True)
    
    if base_character_path and os.path.exists(base_character_path):
        print(f"Using existing character preview: {base_character_path}")
        base_path = f"{output_dir}/base_character.png"
        shutil.copy(base_character_path, base_path)
    else:
        print("Generating new base character...")
        base_path = generate_base_character(traits, output_dir, gender=gender, age_range=age_range,
                                            model=FLUX_DEV_MODEL if use_flux_dev else None)
        time.sleep(10)
    
    additional_refs = None
    if not use_flux_dev:
        if story_id == 'baby_puppy_love' and os.path.exists(PUPPY_PLUSH_REFERENCE):
            additional_refs = [PUPPY_PLUSH_REFERENCE]
        elif story_id == 'baby_first_pet' and os.path.exists(KITTEN_REFERENCE):
            additional_refs = [KITTEN_REFERENCE]
    
    cover_path = None
    use_preview_as_cover = story_config.get('use_preview_as_cover', False)
    
    if use_preview_as_cover and base_path and os.path.exists(base_path):
        print(f"\n[COVER] Using preview image directly as cover (use_preview_as_cover=True)")
        cover_path = f"{output_dir}/cover.png"
        shutil.copy(base_path, cover_path)
        print(f"Cover copied from preview: {cover_path}")
    else:
        cover_prompt = get_cover_prompt(story_id, child_name, gender, traits)
        if cover_prompt:
            from services.quick_stories.checkout import is_quick_story as check_qs_cover
            is_baby = age_range in ['0-1', '0-2']
            is_qs_cover = check_qs_cover(story_id)
            cover_aspect = "1:1" if is_baby or is_qs_cover else "3:4"
            print(f"\nGenerating Cover with {model_name} (aspect: {cover_aspect})...")
            try:
                cover_scene_prompt = f"BOOK COVER: {cover_prompt}"
                if use_flux_dev:
                    cover_path = generate_scene_with_flux2dev(cover_scene_prompt, base_path, 0, cover_aspect, output_dir, gender=gender, age_range=age_range, hair_length=hair_length, child_age=child_age)
                    os.rename(f"{output_dir}/scene_0.png", f"{output_dir}/cover.png")
                    cover_path = f"{output_dir}/cover.png"
                else:
                    cover_path = generate_scene_with_kontext(cover_scene_prompt, base_path, 0, cover_aspect, output_dir, gender=gender, age_range=age_range, additional_references=additional_refs, hair_length=hair_length, child_age=child_age)
                    os.rename(f"{output_dir}/scene_0.png", f"{output_dir}/cover.png")
                    cover_path = f"{output_dir}/cover.png"
            except Exception as e:
                print(f"Error generating cover: {e}")
    
    print(f"Cover generated: {cover_path}")
    
    return {
        'base_character': base_path,
        'cover': cover_path,
        'output_dir': output_dir
    }


def generate_scenes_only(story_id: str, gender: str, traits: dict,
                         output_dir: str, cover_path: str,
                         child_name: str = "the child", use_flux_dev: bool = False,
                         progress_callback=None) -> dict:
    """
    Generate ONLY the scene illustrations (Phase 2 - after payment).
    Uses the cover image as reference for consistency.
    For baby stories: Uses Ideogram Character with preview as reference for character consistency.
    For other stories: Uses FLUX 2 Pro or FLUX 2 Dev.
    For baby stories with closing_template, also generates a closing illustration.
    """
    from services.fixed_stories import get_scene_prompts, get_closing_prompt, STORIES
    
    story_config = STORIES.get(story_id, {})
    age_range = story_config.get('age_range', '0-1')
    is_baby = age_range in ['0-1', '0-2']
    hair_length = traits.get('hair_length', 'medium')
    child_age = int(traits.get('child_age', '1'))
    
    use_ideogram = story_config.get('use_ideogram_scenes', False) and is_baby
    
    if use_ideogram:
        model_name = "Ideogram Character"
    elif use_flux_dev:
        model_name = "FLUX 2 Dev"
    else:
        model_name = "FLUX 2 Pro"
    
    print("=" * 60)
    print(f"SCENES ONLY Generation - {model_name}")
    print(f"Story: {story_id} (Age: {age_range}, Child Age: {child_age})")
    print(f"Hair length: {hair_length}")
    print(f"Using cover as reference: {cover_path}")
    if use_ideogram:
        print("MODE: Ideogram Character (auto-detects face from reference)")
    print("=" * 60)
    
    from services.quick_stories.checkout import is_quick_story as check_qs
    is_qs = check_qs(story_id)
    scene_prompts = get_scene_prompts(story_id, child_name, gender, traits)
    scene_aspect = "1:1" if is_baby or is_qs else "3:4"
    total = len(scene_prompts)
    scene_paths = [None] * total
    _qs_completed = 0
    _qs_workers = 2 if use_ideogram else 3

    def _gen_one_qs(args):
        _i, _prompt = args
        print(f"\n[{_i}/{total}] Generating scene {_i} with {model_name}...")
        try:
            if use_ideogram:
                _path = generate_scene_with_ideogram(_prompt, cover_path, _i, scene_aspect, output_dir)
            elif use_flux_dev:
                _path = generate_scene_with_flux2dev(_prompt, cover_path, _i, scene_aspect, output_dir, gender=gender, age_range=age_range, hair_length=hair_length, child_age=child_age)
            else:
                _path = generate_scene_with_kontext(_prompt, cover_path, _i, scene_aspect, output_dir, gender=gender, age_range=age_range, additional_references=additional_refs, hair_length=hair_length, child_age=child_age)
            return _i, _path
        except Exception as _e:
            print(f"Error generating scene {_i}: {_e}")
            return _i, None

    from concurrent.futures import ThreadPoolExecutor, as_completed as _qs_as_completed
    with ThreadPoolExecutor(max_workers=_qs_workers) as _qs_executor:
        _qs_futures = {_qs_executor.submit(_gen_one_qs, (i, p)): i for i, p in enumerate(scene_prompts, 1)}
        for _qs_future in _qs_as_completed(_qs_futures):
            _i, _path = _qs_future.result()
            scene_paths[_i - 1] = _path
            _qs_completed += 1
            if progress_callback:
                try:
                    progress_callback(_qs_completed, total)
                except Exception:
                    pass
    
    closing_path = None
    closing_prompt = get_closing_prompt(story_id, child_name, gender, traits)
    if closing_prompt:
        print(f"\n[CLOSING] Generating closing illustration with {model_name}...")
        try:
            closing_num = total + 1
            if use_ideogram:
                closing_path = generate_scene_with_ideogram(closing_prompt, cover_path, closing_num, scene_aspect, output_dir)
            elif use_flux_dev:
                closing_path = generate_scene_with_flux2dev(closing_prompt, cover_path, closing_num, scene_aspect, output_dir, gender=gender, age_range=age_range, hair_length=hair_length, child_age=child_age)
            else:
                closing_path = generate_scene_with_kontext(closing_prompt, cover_path, closing_num, scene_aspect, output_dir, gender=gender, age_range=age_range, additional_references=additional_refs, hair_length=hair_length, child_age=child_age)
            os.rename(closing_path, f"{output_dir}/closing.png")
            closing_path = f"{output_dir}/closing.png"
            print(f"[CLOSING] Closing illustration saved: {closing_path}")
        except Exception as e:
            print(f"[CLOSING] Error generating closing: {e}")
    
    print(f"\nScenes generated: {len([p for p in scene_paths if p])}/{total}")
    
    result = {'scenes': scene_paths}
    if closing_path:
        result['closing'] = closing_path
    return result




def test_replicate_connection() -> dict:
    """Test if Replicate API is working."""
    try:
        client = replicate.Client()
        account = client.accounts.current()
        return {
            'success': True,
            'username': account.username,
            'type': account.type
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
