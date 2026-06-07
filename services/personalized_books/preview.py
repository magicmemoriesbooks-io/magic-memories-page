# Personalized Books Preview Generation
# All books now use FLUX 2 Dev for consistency
# Each book's preview uses the same schema as scenes: CHARACTER → OUTFIT → COMPANION → ACTION → SETTING → ATMOSPHERE → STRICT
# Preview prompts are brief hints (hair_desc, eye_desc, skin_tone) instead of full character base descriptions
# Preview = Front Cover (centered composition for book cover)

import os
import uuid
import time
import httpx
import replicate
import requests
from io import BytesIO
from PIL import Image

MAX_RETRIES = 5
RETRY_DELAY = 5

RETRYABLE_ERRORS = [
    'CUDA out of memory', 'GPU', 'ServerError', 'q_descale', 'nsfw', 'NSFW', 'Internal',
    'Read timed out', 'timed out', 'timeout', 'Connection', 'RemoteDisconnected', 'ProtocolError',
]

_replicate_client = replicate.Client(
    timeout=httpx.Timeout(connect=30.0, read=300.0, write=120.0, pool=30.0)
)

PULID_VERSION = "8baa7ef2255075b46f4d91cd238c21d31181b3e6a864463f967960bb0112525b"


def generate_with_flux_kontext(prompt: str, photo_path: str, aspect_ratio: str = "3:4") -> str:
    """Generate a character preview using FLUX Kontext Pro.
    Kontext edits/stylizes the entire photo preserving ALL features (face + hair + skin).
    Better than PuLID for children because it doesn't rely on adult face landmark extraction.
    Returns a local file path (Kontext outputs binary FileOutput, not a URL)."""
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with open(photo_path, "rb") as photo_img:
                print(f"[KONTEXT] Calling flux-kontext-pro attempt {attempt}, prompt_len={len(prompt)}")
                output = _replicate_client.run(
                    "black-forest-labs/flux-kontext-pro",
                    input={
                        "prompt": prompt,
                        "input_image": photo_img,
                        "aspect_ratio": aspect_ratio,
                        "output_format": "png",
                    }
                )
            print(f"[KONTEXT] flux-kontext-pro returned successfully on attempt {attempt}")

            image_bytes = None
            if isinstance(output, bytes):
                image_bytes = output
            elif hasattr(output, 'read'):
                image_bytes = output.read()
            elif isinstance(output, list) and len(output) > 0:
                item = output[0]
                if isinstance(item, bytes):
                    image_bytes = item
                elif hasattr(item, 'read'):
                    image_bytes = item.read()
                else:
                    image_bytes = str(item).encode()
            elif hasattr(output, '__iter__'):
                chunks = b""
                for chunk in output:
                    if isinstance(chunk, bytes):
                        chunks += chunk
                    else:
                        chunks += str(chunk).encode()
                if chunks:
                    image_bytes = chunks
                else:
                    raise Exception("Flux Kontext returned empty output")
            else:
                raise Exception(f"Unexpected Kontext output type: {type(output)}")

            os.makedirs("generated/previews", exist_ok=True)
            local_path = f"generated/previews/kontext_{uuid.uuid4().hex[:8]}.png"
            with open(local_path, "wb") as f:
                f.write(image_bytes)
            print(f"[KONTEXT] Generation complete, saved locally: {local_path} ({len(image_bytes)} bytes)")
            return local_path

        except Exception as e:
            error_msg = str(e)
            last_error = e
            print(f"[KONTEXT] Error on attempt {attempt}: {error_msg[:300]}")
            is_retryable = any(err in error_msg for err in RETRYABLE_ERRORS)
            if is_retryable and attempt < MAX_RETRIES:
                wait = RETRY_DELAY + (attempt - 1) * 3
                print(f"[KONTEXT] Retrying in {wait}s...")
                time.sleep(wait)
                continue
            raise

    raise last_error


def generate_with_flux_pulid(prompt: str, face_image_path: str, width: int = 768, height: int = 1024) -> str:
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with open(face_image_path, "rb") as face_img:
                print(f"[PULID] Calling flux-pulid attempt {attempt}, prompt_len={len(prompt)}")
                output = _replicate_client.run(
                    f"zsxkib/flux-pulid:{PULID_VERSION}",
                    input={
                        "prompt": prompt,
                        "main_face_image": face_img,
                        "id_weight": 0.8,
                        "start_step": 0,
                        "num_steps": 20,
                        "width": width,
                        "height": height,
                        "output_format": "png",
                        "num_outputs": 1,
                        "guidance_scale": 4.0,
                    }
                )
            print(f"[PULID] flux-pulid returned successfully on attempt {attempt}")

            if isinstance(output, list) and len(output) > 0:
                image_url = str(output[0])
            elif hasattr(output, '__iter__'):
                items = list(output)
                if items:
                    image_url = str(items[0])
                else:
                    raise Exception("FLUX PuLID returned empty output")
            else:
                image_url = str(output)

            print(f"[PULID] Generation complete!")
            return image_url

        except Exception as e:
            error_msg = str(e)
            last_error = e
            print(f"[PULID] Error on attempt {attempt}: {error_msg[:300]}")
            is_retryable = any(err in error_msg for err in RETRYABLE_ERRORS)
            if is_retryable and attempt < MAX_RETRIES:
                wait = RETRY_DELAY + (attempt - 1) * 3
                print(f"[PULID] Retrying in {wait}s...")
                time.sleep(wait)
                continue
            raise

    raise last_error


def _run_replicate_with_retry(input_params, ref_file_paths=None):
    """Run replicate with automatic retry on transient errors.
    ref_file_paths: list of file paths to reopen on each retry for fresh file handles."""
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        opened_files = []
        try:
            params = dict(input_params)
            if ref_file_paths:
                fresh_refs = []
                for p in ref_file_paths:
                    f = open(p, "rb")
                    opened_files.append(f)
                    fresh_refs.append(f)
                params["input_images"] = fresh_refs
            
            param_keys = list(params.keys())
            ref_count = len(params.get('input_images', []))
            print(f"[PREVIEW] Calling replicate.run attempt {attempt}: params={param_keys}, refs={ref_count}, prompt_len={len(params.get('prompt',''))}")
            output = _replicate_client.run(
                "black-forest-labs/flux-2-dev",
                input=params
            )
            print(f"[PREVIEW] replicate.run returned successfully on attempt {attempt}")
            return output
        except Exception as e:
            error_msg = str(e)
            last_error = e
            print(f"[PREVIEW] Full error on attempt {attempt}: {error_msg[:300]}")
            is_retryable = any(err in error_msg for err in RETRYABLE_ERRORS)
            if is_retryable:
                print(f"[PREVIEW] Transient error on attempt {attempt}/{MAX_RETRIES}: {error_msg[:150]}...")
                if attempt < MAX_RETRIES:
                    wait = RETRY_DELAY + (attempt - 1) * 3
                    print(f"[PREVIEW] Retrying in {wait}s...")
                    time.sleep(wait)
                    continue
            raise
        finally:
            for f in opened_files:
                try:
                    f.close()
                except:
                    pass
    raise last_error


def generate_with_flux2_dev(prompt: str, aspect_ratio: str = "3:4", photo_ref_path: str = None, photo_ref_paths: list = None, image_prompt_strength: float = 0.50, negative_prompt: str = None) -> str:
    """Generate illustration using FLUX 2 Dev (better consistency for series).
    If photo_ref_path is provided, uses it as single input_images reference.
    If photo_ref_paths is provided, uses multiple input_images references (e.g. human + pet).
    image_prompt_strength: 0.0=all text, 1.0=all image. Default 0.50 (50/50 balance).
    With 2 refs (human+pet): each ref ~25%, text 50% — better characteristic control.
    With 1 ref (single photo): ref 50%, text 50% — balanced face+trait fidelity.
    negative_prompt: passed as separate FLUX parameter to suppress unwanted features (tails, animal features)."""
    input_params = {
        "prompt": prompt,
        "aspect_ratio": aspect_ratio,
        "output_format": "png",
        "go_fast": True
    }
    if negative_prompt:
        input_params["negative_prompt"] = negative_prompt
    
    if photo_ref_paths:
        valid_paths = [p for p in photo_ref_paths if p and os.path.exists(p)]
        if valid_paths:
            print(f"[PREVIEW] Generating with FLUX 2 Dev + {len(valid_paths)} photo references (strength={image_prompt_strength}): {valid_paths}")
            print(f"[PREVIEW] Prompt ({len(prompt)} chars): {prompt[:200]}...")
            input_params["go_fast"] = False
            input_params["image_prompt_strength"] = image_prompt_strength
            if len(valid_paths) >= 2:
                if "PET" in prompt or "pet" in prompt.lower()[:300]:
                    anti_blend = "\n@image1=HUMAN ref, @image2=PET ref. Keep each appearance exactly. Human=human only, pet=animal only, TWO separate beings."
                    input_params["prompt"] = prompt + anti_blend
            output = _run_replicate_with_retry(input_params, ref_file_paths=valid_paths)
        else:
            print(f"[PREVIEW] Generating with FLUX 2 Dev (no valid photo references)...")
            output = _run_replicate_with_retry(input_params)
    elif photo_ref_path and os.path.exists(photo_ref_path):
        print(f"[PREVIEW] Generating with FLUX 2 Dev + photo reference (strength={image_prompt_strength}): {photo_ref_path}")
        print(f"[PREVIEW] Prompt ({len(prompt)} chars): {prompt[:200]}...")
        input_params["go_fast"] = False
        input_params["image_prompt_strength"] = image_prompt_strength
        output = _run_replicate_with_retry(input_params, ref_file_paths=[photo_ref_path])
    else:
        print(f"[PREVIEW] Generating with FLUX 2 Dev (no photo reference)...")
        output = _run_replicate_with_retry(input_params)
    
    if output:
        if isinstance(output, list) and len(output) > 0:
            image_url = str(output[0])
        else:
            image_url = str(output)
        print(f"[PREVIEW] FLUX 2 Dev generation complete!")
        return image_url
    
    raise Exception("FLUX 2 Dev generation failed")


def _ensure_luna_reference() -> str:
    """Generate LUNA star companion reference image once and cache it as a static asset.
    Returns the file path, or empty string if generation fails.
    LUNA: small cute five-pointed star, silver-white, violet eyes, translucent wings.
    """
    luna_path = 'static/assets/luna_reference.png'
    if os.path.exists(luna_path):
        return luna_path
    print("[STAR KEEPER] Generating LUNA reference image (first time only)...")
    try:
        luna_prompt = (
            "Disney Pixar 3D style illustration. A single cute small five-pointed star shape, "
            "solid shimmering silver-white body, two large expressive bright violet eyes on the star face, "
            "tiny delicate translucent wings on the sides of the star, soft warm silver glow surrounding. "
            "Floating in midair, centered in frame. Plain deep dark navy blue background. "
            "Full character visible, clean studio lighting, pure illustration only, NO text, NO watermarks."
        )
        image_url = generate_with_flux2_dev(luna_prompt, aspect_ratio="1:1")
        from services.replicate_service import save_image_locally as _sil
        result_path = _sil(image_url, luna_path)
        if result_path and os.path.exists(luna_path):
            print(f"[STAR KEEPER] LUNA reference saved: {luna_path}")
            return luna_path
    except Exception as e:
        print(f"[STAR KEEPER] LUNA reference generation failed: {e}")
    return ''


def _ensure_astro_reference() -> str:
    """Generate ASTRO fox companion reference image once and cache it as a static asset.
    Returns the file path, or empty string if generation fails.
    ASTRO: small magical fox, kitten-sized, electric blue fur, amber eyes, glowing star-tipped tail.
    """
    astro_path = 'static/assets/astro_reference.png'
    if os.path.exists(astro_path):
        return astro_path
    print("[CENTINELA AURORA] Generating ASTRO reference image (first time only)...")
    try:
        astro_prompt = (
            "Disney Pixar 3D style illustration. A single small magical fox named ASTRO, "
            "kitten-sized, vibrant electric blue fur covering the entire body, white chest patch, "
            "large expressive amber-golden eyes, a glowing star-tipped tail that emits soft electric blue light, "
            "a star-gem rope collar around the neck. "
            "Sitting pose, centered in frame, full body visible. "
            "Plain deep midnight blue background with faint aurora colors. "
            "Full character visible, clean studio lighting, pure illustration only, NO text, NO watermarks."
        )
        image_url = generate_with_flux2_dev(astro_prompt, aspect_ratio="1:1")
        from services.replicate_service import save_image_locally as _sil
        os.makedirs('static/assets', exist_ok=True)
        result_path = _sil(image_url, astro_path)
        if result_path and os.path.exists(astro_path):
            print(f"[CENTINELA AURORA] ASTRO reference saved: {astro_path}")
            return astro_path
    except Exception as e:
        print(f"[CENTINELA AURORA] ASTRO reference generation failed: {e}")
    return ''


def _ensure_spark_reference() -> str:
    """Generate SPARK dragon companion reference image once and cache it as a static asset.
    Returns the file path, or empty string if generation fails.
    SPARK: adorable baby dragon, emerald green scales, golden eyes, tiny iridescent wings.
    """
    spark_path = 'static/assets/spark_reference.png'
    if os.path.exists(spark_path):
        return spark_path
    print("[DRAGON GARDEN] Generating SPARK reference image (first time only)...")
    try:
        spark_prompt = (
            "Disney Pixar 3D style illustration. A single adorable baby dragon named SPARK, "
            "small chubby round body covered in shimmering emerald green scales, large expressive "
            "golden eyes, tiny translucent iridescent wings on the sides, short stubby tail, "
            "small rounded snout with a sweet gentle smile, two tiny curved horns on head, "
            "soft cream-colored belly. Floating in midair, centered in frame, full body visible. "
            "Plain soft green magical background with golden sparkles. "
            "Full character visible, clean studio lighting, pure illustration only, NO text, NO watermarks."
        )
        image_url = generate_with_flux2_dev(spark_prompt, aspect_ratio="1:1")
        from services.replicate_service import save_image_locally as _sil
        os.makedirs('static/assets', exist_ok=True)
        result_path = _sil(image_url, spark_path)
        if result_path and os.path.exists(spark_path):
            print(f"[DRAGON GARDEN] SPARK reference saved: {spark_path}")
            return spark_path
    except Exception as e:
        print(f"[DRAGON GARDEN] SPARK reference generation failed: {e}")
    return ''


def generate_personalized_preview(story_id: str, child_name: str, gender: str,
                                   child_age: int, traits: dict,
                                   child_photo_path: str = '') -> dict:
    """
    Generate character preview for Personalized Books.
    All books now use FLUX 2 Dev with the same schema: CHARACTER → OUTFIT → COMPANION → ACTION → SETTING → ATMOSPHERE → STRICT
    Brief hints only (hair_desc, eye_desc, skin_tone) - no full char_base descriptions
    Preview = Front Cover with centered composition for book cover
    """
    from services.replicate_service import save_image_locally, get_unified_skin_description, get_gender_negative_prompt
    from services.fixed_stories import get_hair_description, get_eye_description
    
    # Determine if a photo is provided and build glasses description
    has_photo = bool(child_photo_path and os.path.exists(child_photo_path))
    glasses = traits.get('glasses', '')
    glasses_desc = ", wearing round glasses" if glasses else ""

    if story_id == 'dragon_garden_illustrated':
        from services.personalized_books.dragon_garden_prompts import (
            get_outfit_desc as dg_get_outfit_desc,
            STYLE_BASE as DG_STYLE_BASE,
            FRONT_COVER as DG_FRONT_COVER,
            get_hair_action as dg_get_hair_action
        )
        from services.fixed_stories import get_hair_strict
        from services.replicate_service import get_gender_negative_prompt as _dg_neg_fn

        gender_word = "boy" if gender == "male" else "girl" if gender == "female" else "child"
        age_display = f"{child_age} year old" if child_age and child_age > 0 else "6 year old"
        human_photo_path = traits.get('human_photo_path', child_photo_path or '')
        outfit_desc = dg_get_outfit_desc(gender)

        spark_path = _ensure_spark_reference()
        spark_ok = spark_path and os.path.exists(spark_path)

        output_dir = 'generated/previews'
        os.makedirs(output_dir, exist_ok=True)

        dg_scene = DG_FRONT_COVER.get('prompt', '').replace('{style}', DG_STYLE_BASE)
        dg_neg = _dg_neg_fn(gender)

        if human_photo_path and os.path.exists(human_photo_path):
            kontext_prompt = (
                f"Convert the {age_display} {gender_word} in @image1 into a high-quality 3D animated children's book character. "
                f"Preserve the exact face, eye color, skin tone, and hair — identical likeness. "
                f"OUTFIT: {outfit_desc}. "
                f"BACKGROUND: soft magical garden atmosphere with golden sparkles, plain studio — no dragon, no scenery. "
                f"POSE: standing, full body visible from head to feet, joyful adventurous smile, arms relaxed at sides."
            )
            print(f"[DRAGON GARDEN PREVIEW] Step 1 — Kontext portrait | photo={human_photo_path} | age={child_age}")
            portrait_url = generate_with_flux_kontext(kontext_prompt, human_photo_path, aspect_ratio="3:4")
            portrait_path = save_image_locally(portrait_url, f'{output_dir}/dg_portrait_{uuid.uuid4().hex[:8]}.png')
            print(f"[DRAGON GARDEN PREVIEW] Portrait saved: {portrait_path}")

            dg_ref_note = (
                f"The child in @image1 is {age_display}. "
                f"@image1={gender_word} character — copy face, eye color, hair, skin, and outfit exactly. "
                "@image2=small emerald dragon companion SPARK — copy appearance exactly. "
                f"Two distinct characters: @image1 is a fully human {gender_word}, @image2 is a small baby dragon."
            )
            photo_refs = [portrait_path, spark_path] if spark_ok else [portrait_path]
            print(f"[DRAGON GARDEN PREVIEW] Step 2 — FLUX 2 Dev cover scene | portrait={portrait_path} | spark={spark_ok}")
            cov_url = generate_with_flux2_dev(
                f"{dg_ref_note}\n{dg_scene}",
                aspect_ratio="3:4",
                photo_ref_paths=photo_refs,
                image_prompt_strength=0.95,
                negative_prompt=dg_neg
            )
        else:
            hair_action = dg_get_hair_action(traits)
            hair_desc = get_hair_description(traits)
            hair_strict_text = get_hair_strict(traits)
            eye_desc = get_eye_description(traits)
            skin_tone = get_unified_skin_description(traits.get('skin_tone', 'light'))
            dg_nophoto_prompt = (
                f"@image1 = small emerald dragon companion SPARK — copy @image1 appearance exactly.\n"
                f"Draw a single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, "
                f"big joyful smile, {hair_action}. OUTFIT: {outfit_desc}.\n"
                f"ACTION: The {gender_word} sits happily on @image1's back soaring through the sky, "
                f"arms gently holding the dragon, @image1's wings spread wide and flapping. "
                f"SETTING: Beautiful sky WIDE VIEW, fluffy pink and white cotton clouds, "
                f"magnificent rainbow arching, golden sunlight, sparkles trailing. "
                f"ATMOSPHERE: Adventure invitation, joyful flight, magical. "
                f"STRICT: Only ONE {gender_word}, only ONE small dragon @image1, "
                f"the {gender_word} is a fully human child: no tail, no wings, no scales. {hair_strict_text} "
                f"ABSOLUTELY NO rendered text, no titles, no logos, no words, no letters, no captions, "
                f"no watermarks, no signatures, pure illustration only. {DG_STYLE_BASE}"
            )
            photo_refs = [spark_path] if spark_ok else None
            print(f"[DRAGON GARDEN PREVIEW] FLUX 2 Dev cover scene (no photo) | gender={gender_word} | age={age_display}")
            cov_url = generate_with_flux2_dev(
                dg_nophoto_prompt,
                aspect_ratio="3:4",
                photo_ref_paths=photo_refs,
                image_prompt_strength=0.85,
                negative_prompt=dg_neg
            )

        cover_path = save_image_locally(cov_url, f'{output_dir}/dg_cover_{uuid.uuid4().hex[:8]}.png')
        print(f"[DRAGON GARDEN PREVIEW] Cover scene generated: {cover_path}")
        result = {
            'success': True,
            'image_url': f'/{cover_path}',
            'story_id': story_id,
            'child_age': child_age
        }
        if human_photo_path and os.path.exists(human_photo_path) and 'portrait_path' in dir():
            result['kontext_portrait'] = f'/{portrait_path}'
        return result

    elif story_id == 'magic_chef_illustrated':
        from services.personalized_books.magic_chef_prompts import (
            get_outfit_desc as chef_get_outfit_desc,
            STYLE_BASE as CHEF_STYLE_BASE,
            SWEETIE_HAT_INLINE,
            SWEETIE_CAKE_INLINE
        )
        from services.fixed_stories import get_hair_strict
        
        outfit_desc = chef_get_outfit_desc(gender)
        if has_photo:
            hair_desc = "hair as in the reference photo"
            actual_eye = get_eye_description(traits)
            eye_desc = f"{actual_eye}, face exactly as in the reference photo{glasses_desc}"
            skin_tone = "as in the reference photo"
            char_physical = f"{hair_desc}, {eye_desc}"
            hair_strict_text = "PHOTO REFERENCE: Match the child's exact face, skin, eye color and hair from the reference photo."
        else:
            hair_desc = get_hair_description(traits)
            hair_strict_text = get_hair_strict(traits)
            eye_desc = get_eye_description(traits)
            skin_tone = get_unified_skin_description(traits.get('skin_tone', 'light'))
            char_physical = f"{hair_desc}, {eye_desc}, {skin_tone} skin{glasses_desc}"
        gender_word = "boy" if gender == "male" else "girl" if gender == "female" else "child"
        age_display = f"{child_age} year old" if child_age and child_age > 0 else "6 year old"
        
        # Use FRONT_COVER schema, adapted for preview context
        prompt = f"Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {char_physical}, confident joyful smile. OUTFIT: {SWEETIE_HAT_INLINE}, and an elegant white chef jacket with golden buttons. COMPANION: {SWEETIE_CAKE_INLINE}. ACTION: {gender_word} stands in center of magical kitchen with both hands on hips, smiling proudly. SWEETIE floats happily beside the child, frosting swirling around. SETTING: Magical pink kitchen WIDE VIEW, sparkles hearts and golden stars, floating magical desserts everywhere, rainbow cakes, glowing star cookies, swirling colorful ice creams, centered composition for book cover. ATMOSPHERE: Sweet magical invitation, pink and golden warmth. STRICT: Only ONE {gender_word}, only ONE cake character SWEETIE, the {gender_word} is a fully human child: no animal features, no tail. {hair_strict_text} ABSOLUTELY NO rendered text anywhere in the image, no titles, no logos, no words, no letters, no captions, no watermarks, no signatures, pure illustration only. {CHEF_STYLE_BASE}"
        
        print(f"[PERSONALIZED PREVIEW] {story_id}, age={child_age}, has_photo={has_photo}, glasses={bool(glasses)}")
        print(f"[PERSONALIZED PREVIEW] Using FRONT_COVER schema + FLUX 2 Dev")
        
    elif story_id == 'magic_inventor_illustrated':
        from services.personalized_books.magic_inventor_prompts import (
            get_outfit_desc as inventor_get_outfit_desc,
            STYLE_BASE as INVENTOR_STYLE_BASE,
            BOLT_INLINE as INVENTOR_BOLT_INLINE
        )
        from services.fixed_stories import get_hair_strict
        
        outfit_desc = inventor_get_outfit_desc(gender)
        if has_photo:
            hair_desc = "hair as in the reference photo"
            actual_eye = get_eye_description(traits)
            eye_desc = f"{actual_eye}, face exactly as in the reference photo{glasses_desc}"
            skin_desc = "as in the reference photo"
            char_physical = f"{hair_desc}, {eye_desc}"
            hair_strict_text = "PHOTO REFERENCE: Match the child's exact face, skin, eye color and hair from the reference photo."
        else:
            hair_desc = get_hair_description(traits)
            hair_strict_text = get_hair_strict(traits)
            eye_desc = get_eye_description(traits)
            skin_desc = get_unified_skin_description(traits.get('skin_tone', 'light'))
            char_physical = f"{hair_desc}, {eye_desc}, {skin_desc} skin{glasses_desc}"
        gender_word = "boy" if gender == "male" else "girl" if gender == "female" else "child"
        age_display = f"{child_age} year old" if child_age and child_age > 0 else "6 year old"
        
        prompt = f"Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {char_physical}, confident joyful smile, holding a glowing wrench. OUTFIT: {outfit_desc}. COMPANION: {INVENTOR_BOLT_INLINE}. ACTION: {gender_word} stands in center of workshop facing viewer, holding glowing wrench up with pride. BOLT stands beside the child, waving with one arm, blue eyes bright and friendly. SETTING: Magical inventor workshop WIDE VIEW, floating golden gears, crystal tubes with colorful liquids, warm golden light, sparkles. ATMOSPHERE: Adventure invitation, warm golden, friendship and creativity. STRICT: Only ONE {gender_word}, only ONE small robot BOLT, the {gender_word} is a fully human child: no mechanical parts, no robot features on {gender_word}. {hair_strict_text} ABSOLUTELY NO rendered text anywhere in the image, no titles, no logos, no words, no letters, no captions, no watermarks, no signatures, pure illustration only. {INVENTOR_STYLE_BASE}"
        
        print(f"[PERSONALIZED PREVIEW] {story_id}, age={child_age}, has_photo={has_photo}, glasses={bool(glasses)}")
        print(f"[PERSONALIZED PREVIEW] Using FRONT_COVER schema + FLUX 2 Dev")
        
    elif story_id == 'star_keeper_illustrated':
        from services.personalized_books.star_keeper_prompts import (
            get_outfit_desc as keeper_get_outfit_desc,
            STYLE_BASE as KEEPER_STYLE_BASE,
            FRONT_COVER as SK_FRONT_COVER,
            get_hair_action
        )
        from services.fixed_stories import get_hair_strict
        from services.replicate_service import get_gender_negative_prompt as _sk_neg_fn

        gender_word = "boy" if gender == "male" else "girl" if gender == "female" else "child"
        age_display = f"{child_age} year old" if child_age and child_age > 0 else "6 year old"
        human_photo_path = traits.get('human_photo_path', '')
        outfit_desc = keeper_get_outfit_desc(gender)

        luna_path = _ensure_luna_reference()
        luna_ok = luna_path and os.path.exists(luna_path)

        output_dir = 'generated/previews'
        os.makedirs(output_dir, exist_ok=True)

        sk_scene = SK_FRONT_COVER.get('prompt', '').replace('{style}', KEEPER_STYLE_BASE)
        sk_neg = _sk_neg_fn(gender)

        if human_photo_path and os.path.exists(human_photo_path):
            # Step 1: Kontext — clean portrait (face preserved, Pixar style, plain bg)
            kontext_prompt = (
                f"Convert the {age_display} {gender_word} in @image1 into a high-quality 3D animated children's book character. "
                f"Preserve the exact face, eye color, skin tone, and hair — identical likeness. "
                f"OUTFIT: {outfit_desc}. "
                f"BACKGROUND: deep midnight blue with subtle silver star sparkles, plain studio — no lighthouse, no ocean, no scenery. "
                f"POSE: standing, full body visible from head to feet, brave adventurous smile, arms relaxed at sides."
            )
            print(f"[STAR KEEPER PREVIEW] Step 1 — Kontext portrait | photo={human_photo_path} | age={child_age}")
            portrait_url = generate_with_flux_kontext(kontext_prompt, human_photo_path, aspect_ratio="3:4")
            portrait_path = save_image_locally(portrait_url, f'{output_dir}/sk_portrait_{uuid.uuid4().hex[:8]}.png')
            print(f"[STAR KEEPER PREVIEW] Portrait saved: {portrait_path}")

            # Step 2: FLUX 2 Dev — cover scene (lighthouse + stars) using portrait as @image1 + LUNA as @image2
            sk_ref_note = (
                f"The child in @image1 is {age_display}. "
                f"@image1={gender_word} character — copy face, eye color, hair, skin, and outfit exactly. "
                "@image2=small star companion LUNA — copy appearance exactly. "
                f"Two distinct characters: @image1 is a fully human {gender_word}, @image2 is a small glowing star."
            )
            photo_refs = [portrait_path, luna_path] if luna_ok else [portrait_path]
            print(f"[STAR KEEPER PREVIEW] Step 2 — FLUX 2 Dev cover scene | portrait={portrait_path} | luna={luna_ok}")
            cov_url = generate_with_flux2_dev(
                f"{sk_ref_note}\n{sk_scene}",
                aspect_ratio="3:4",
                photo_ref_paths=photo_refs,
                image_prompt_strength=0.95,
                negative_prompt=sk_neg
            )
        else:
            hair_action = get_hair_action(traits)
            hair_desc = get_hair_description(traits)
            hair_strict_text = get_hair_strict(traits)
            eye_desc = get_eye_description(traits)
            skin_tone = get_unified_skin_description(traits.get('skin_tone', 'light'))
            # No-photo branch: only Luna is available as a reference image.
            # sk_scene uses @image1=child / @image2=Luna — but here @image1 IS Luna.
            # Build a standalone cover prompt: describe the child in text, use @image1 for Luna.
            sk_nophoto_prompt = (
                f"@image1 = small glowing star companion LUNA — copy @image1 appearance exactly.\n"
                f"Draw a single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, "
                f"big joyful confident smile, {hair_action}. OUTFIT: {outfit_desc}.\n"
                f"ACTION: The {gender_word} stands confidently at the lighthouse entrance with one hand "
                f"reaching upward toward the stars, @image1 hovers beside the {gender_word}'s shoulder. "
                f"SETTING: Old stone lighthouse on a dramatic clifftop WIDE VIEW, magnificent starry sky "
                f"with bright constellations and shooting stars, ocean waves crashing below, warm golden-blue "
                f"light from the lighthouse door, centered composition for book cover. "
                f"ATMOSPHERE: Adventure invitation, celestial magic. "
                f"STRICT: Only ONE {gender_word}, fully human child, no wings. {hair_strict_text} "
                f"ABSOLUTELY NO rendered text, no titles, no logos, no words, no letters, no captions, "
                f"no watermarks, no signatures, pure illustration only. {KEEPER_STYLE_BASE}"
            )
            photo_refs = [luna_path] if luna_ok else None
            print(f"[STAR KEEPER PREVIEW] FLUX 2 Dev cover scene (no photo) | gender={gender_word} | age={age_display}")
            cov_url = generate_with_flux2_dev(
                sk_nophoto_prompt,
                aspect_ratio="3:4",
                photo_ref_paths=photo_refs,
                image_prompt_strength=0.85,
                negative_prompt=sk_neg
            )

        cover_path = save_image_locally(cov_url, f'{output_dir}/sk_cover_{uuid.uuid4().hex[:8]}.png')
        print(f"[STAR KEEPER PREVIEW] Cover scene generated: {cover_path}")
        result = {
            'success': True,
            'image_url': f'/{cover_path}',
            'story_id': story_id,
            'child_age': child_age
        }
        if human_photo_path and os.path.exists(human_photo_path) and 'portrait_path' in dir():
            result['kontext_portrait'] = f'/{portrait_path}'
        return result


    elif story_id == 'centinela_aurora_illustrated':
        from services.personalized_books.centinela_aurora_prompts import (
            get_outfit_desc as aurora_get_outfit_desc,
            STYLE_BASE as AURORA_STYLE_BASE,
            FRONT_COVER as CA_FRONT_COVER,
            get_hair_action as aurora_get_hair_action
        )
        from services.fixed_stories import get_hair_strict
        from services.replicate_service import get_gender_negative_prompt as _ca_neg_fn

        gender_word = "boy" if gender == "male" else "girl" if gender == "female" else "child"
        age_display = f"{child_age} year old" if child_age and child_age > 0 else "6 year old"
        human_photo_path = traits.get('human_photo_path', child_photo_path or '')
        outfit_desc = aurora_get_outfit_desc(gender)

        astro_path = _ensure_astro_reference()
        astro_ok = astro_path and os.path.exists(astro_path)

        output_dir = 'generated/previews'
        os.makedirs(output_dir, exist_ok=True)

        ca_scene = CA_FRONT_COVER.get('prompt', '').replace('{style}', AURORA_STYLE_BASE)
        ca_neg = _ca_neg_fn(gender)

        if human_photo_path and os.path.exists(human_photo_path):
            kontext_prompt = (
                f"Convert the {age_display} {gender_word} in @image1 into a high-quality 3D animated children's book character. "
                f"Preserve the exact face, eye color, skin tone, and hair — identical likeness. "
                f"OUTFIT: {outfit_desc}. "
                f"BACKGROUND: deep midnight blue with subtle aurora colors, plain studio — no fox, no compass, no scenery. "
                f"POSE: standing, full body visible from head to feet, brave adventurous smile, arms relaxed at sides."
            )
            print(f"[CENTINELA AURORA PREVIEW] Step 1 — Kontext portrait | photo={human_photo_path} | age={child_age}")
            portrait_url = generate_with_flux_kontext(kontext_prompt, human_photo_path, aspect_ratio="3:4")
            portrait_path = save_image_locally(portrait_url, f'{output_dir}/ca_portrait_{uuid.uuid4().hex[:8]}.png')
            print(f"[CENTINELA AURORA PREVIEW] Portrait saved: {portrait_path}")

            ca_ref_note = (
                f"The child in @image1 is {age_display}. "
                f"@image1={gender_word} character — copy face, eye color, hair, skin, and outfit exactly. ONE child only. "
                "@image2=small electric-blue fox ASTRO — copy appearance exactly. "
                f"CRITICAL: @image1 is the ONLY human. "
                "@image2 is a small four-legged animal fox, electric blue fur, NOT a person. "
                "Two separate characters: one human child, one tiny fox animal."
            )
            photo_refs = [portrait_path, astro_path] if astro_ok else [portrait_path]
            print(f"[CENTINELA AURORA PREVIEW] Step 2 — FLUX 2 Dev cover scene | portrait={portrait_path} | astro={astro_ok}")
            _ca_full_prompt = f"{ca_ref_note}\n{ca_scene}"
            print(f"[CENTINELA AURORA PREVIEW] FULL PROMPT TO FLUX:\n{_ca_full_prompt}")
            cov_url = generate_with_flux2_dev(
                f"{ca_ref_note}\n{ca_scene}",
                aspect_ratio="3:4",
                photo_ref_paths=photo_refs,
                image_prompt_strength=0.95,
                negative_prompt=ca_neg
            )
        else:
            hair_action = aurora_get_hair_action(traits)
            hair_desc = get_hair_description(traits)
            hair_strict_text = get_hair_strict(traits)
            eye_desc = get_eye_description(traits)
            skin_tone = get_unified_skin_description(traits.get('skin_tone', 'light'))
            ca_nophoto_prompt = (
                f"@image1 = small magical electric-blue fox companion ASTRO — copy @image1 appearance exactly.\n"
                f"Draw a single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, "
                f"big joyful brave smile, {hair_action}. OUTFIT: {outfit_desc}.\n"
                f"ACTION: The {gender_word} stands confidently holding the golden compass high with one arm, "
                f"face lit with adventurous excitement. @image1 perches on the {gender_word}'s shoulder, "
                f"glowing tail raised high, electric blue light blazing brilliantly against the aurora sky. "
                f"SETTING: Night sky and aurora WIDE VIEW, magnificent aurora borealis colors filling the sky, "
                f"stars everywhere, magical stardust floating around them, centered composition for book cover. "
                f"ATMOSPHERE: Epic adventure invitation, magical aurora colors, excitement and wonder. "
                f"STRICT: Only ONE {gender_word}, only ONE small electric-blue fox @image1, "
                f"the {gender_word} is a fully human child: no tail, no fox features. {hair_strict_text} "
                f"ABSOLUTELY NO rendered text, no titles, no logos, no words, no letters, no captions, "
                f"no watermarks, no signatures, pure illustration only. {AURORA_STYLE_BASE}"
            )
            photo_refs = [astro_path] if astro_ok else None
            print(f"[CENTINELA AURORA PREVIEW] FLUX 2 Dev cover scene (no photo) | gender={gender_word} | age={age_display}")
            cov_url = generate_with_flux2_dev(
                ca_nophoto_prompt,
                aspect_ratio="3:4",
                photo_ref_paths=photo_refs,
                image_prompt_strength=0.85,
                negative_prompt=ca_neg
            )

        cover_path = save_image_locally(cov_url, f'{output_dir}/ca_cover_{uuid.uuid4().hex[:8]}.png')
        print(f"[CENTINELA AURORA PREVIEW] Cover scene generated: {cover_path}")
        result = {
            'success': True,
            'image_url': f'/{cover_path}',
            'story_id': story_id,
            'child_age': child_age
        }
        if human_photo_path and os.path.exists(human_photo_path) and 'portrait_path' in dir():
            result['kontext_portrait'] = f'/{portrait_path}'
        return result

    elif story_id in ('furry_love_illustrated', 'furry_love_adventure_illustrated', 'furry_love_teen_illustrated', 'furry_love_adult_illustrated'):
        if story_id == 'furry_love_adventure_illustrated':
            from services.personalized_books.furry_love_adventure_prompts import (
                build_human_preview_prompt, build_pet_preview_prompt,
                build_human_preview_prompt_with_photo, build_pet_preview_prompt_with_photo
            )
        elif story_id == 'furry_love_teen_illustrated':
            from services.personalized_books.furry_love_teen_prompts import (
                build_human_preview_prompt, build_pet_preview_prompt,
                build_human_preview_prompt_with_photo, build_pet_preview_prompt_with_photo
            )
        elif story_id == 'furry_love_adult_illustrated':
            from services.personalized_books.furry_love_adult_prompts import (
                build_human_preview_prompt, build_pet_preview_prompt,
                build_human_preview_prompt_with_photo, build_pet_preview_prompt_with_photo
            )
        else:
            from services.personalized_books.furry_love_prompts import (
                build_human_preview_prompt, build_pet_preview_prompt,
                build_human_preview_prompt_with_photo, build_pet_preview_prompt_with_photo
            )
        
        human_desc = traits.get('human_desc', '')
        pet_desc = traits.get('pet_desc', '')
        human_photo_path = traits.get('human_photo_path', '')
        pet_photo_path = traits.get('pet_photo_path', '')
        
        if not human_desc:
            hair_desc = get_hair_description(traits)
            eye_desc = get_eye_description(traits)
            skin_tone = get_unified_skin_description(traits.get('skin_tone', 'light'))
            if child_age is not None and child_age >= 18:
                gender_word = "man" if gender == "male" else "woman" if gender == "female" else "person"
            else:
                gender_word = "boy" if gender == "male" else "girl" if gender == "female" else "person"
            if child_age is not None and child_age == 0:
                age_display = "baby"
            elif child_age is not None and child_age >= 18:
                age_display = f"{child_age} year old adult"
            elif child_age and child_age > 0:
                age_display = f"{child_age} year old"
            else:
                age_display = "adult"
            human_desc = f"a {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin"
            
            facial_hair_map = {'stubble': 'light stubble', 'short_beard': 'short beard', 'full_beard': 'full thick beard', 'mustache': 'mustache'}
            fh = traits.get('facial_hair', 'none')
            if fh and fh != 'none' and fh in facial_hair_map:
                human_desc += f", with {facial_hair_map[fh]}"
            gl = traits.get('glasses', 'none')
            if gl and gl != 'none':
                human_desc += f", wearing {gl}"
            bb = traits.get('body_build', 'average')
            if bb and bb != 'average':
                human_desc += f", {bb} build"
        
        pet_species = traits.get('pet_species', 'dog')
        if not pet_desc:
            if pet_photo_path:
                pet_desc = ""
            else:
                animal_word = "cat" if pet_species == "cat" else "dog"
                pet_desc = f"a friendly {animal_word} with warm expressive eyes"
        
        if human_photo_path:
            gender_word = "baby boy" if gender == "male" else "baby girl" if gender == "female" else "baby"
            if child_age is not None and child_age == 0:
                age_display = "infant baby, few months old"
            elif child_age is not None and child_age >= 18:
                if child_age >= 60:
                    age_display = "mature adult"
                elif child_age >= 40:
                    age_display = "middle-aged adult"
                else:
                    age_display = "young adult"
                gender_word = "man" if gender == "male" else "woman" if gender == "female" else "person"
            elif child_age and child_age > 0:
                age_display = f"{child_age} year old"
                gender_word = "boy" if gender == "male" else "girl" if gender == "female" else "person"
            else:
                age_display = "adult"
                gender_word = "man" if gender == "male" else "woman" if gender == "female" else "person"
            eye_desc = get_eye_description(traits)
            hair_desc = get_hair_description(traits)
            glasses_val = traits.get('glasses', 'none')
            facial_hair_val = traits.get('facial_hair', 'none')
            if human_photo_path and story_id == 'furry_love_adventure_illustrated':
                hair_for_prompt = hair_desc
            elif human_photo_path:
                hair_for_prompt = "hair and scalp naturally matching the reference photo"
            else:
                hair_for_prompt = hair_desc
            # With photo: pass a SHORT skin tone hint only for darker tones where FLUX Pixar style
            # tends to lighten the skin. Light/medium tones are reproduced well from the photo alone.
            # Without photo: use the full verbose description so FLUX respects the form selection.
            _skin_key = traits.get('skin_tone', 'light')
            _short_tone_map = {
                'dark': 'dark brown', 'brown': 'rich brown',
                'medium_dark': 'warm brown', 'medium': 'warm caramel',
                'tan': 'warm tan'
            }
            skin_tone_for_prompt = _short_tone_map.get(_skin_key, '') if human_photo_path else get_unified_skin_description(_skin_key)
            human_prompt = build_human_preview_prompt_with_photo(gender_word, age_display, eye_desc, hair_for_prompt, glasses=glasses_val, facial_hair=facial_hair_val, skin_tone=skin_tone_for_prompt)
        else:
            _is_baby_no_photo = (story_id == 'furry_love_illustrated')
            human_prompt = build_human_preview_prompt(human_desc, is_baby=_is_baby_no_photo)
        
        print(f"[PREVIEW DEBUG] HUMAN PROMPT FULL ({len(human_prompt)} chars): {human_prompt}")
        if pet_photo_path:
            pet_prompt = build_pet_preview_prompt_with_photo(pet_desc, pet_species, pet_size=traits.get('pet_size', 'medium'))
        else:
            pet_prompt = build_pet_preview_prompt(pet_desc, pet_size=traits.get('pet_size', 'medium'))
        
        use_pulid = False
        use_kontext = story_id in ('furry_love_adventure_illustrated', 'furry_love_teen_illustrated', 'furry_love_illustrated', 'furry_love_adult_illustrated')
        
        if human_photo_path and use_kontext:
            print(f"[FURRY LOVE PREVIEW] Generating human preview WITH photo using FLUX Kontext Pro (full identity): {human_photo_path}")
            skin_tone_k = get_unified_skin_description(traits.get('skin_tone', 'light'))
            if story_id == 'furry_love_illustrated':
                # Baby book — minimal prompt: just convert the baby from the photo, no characteristic descriptions
                kontext_prompt = (
                    f"Convert the {gender_word} in @image1 into a high-quality 3D animated children's book character. "
                    f"Preserve the exact face, eye color, skin tone, and hair of the baby — identical likeness. "
                    f"OUTFIT: soft sage-green baby romper with small leaf print, no text on clothing. "
                    f"BACKGROUND: soft cream gradient, plain studio. "
                    f"POSE: baby sitting on the floor, facing camera, warm happy smiling expression, full body visible from head to bare feet, natural baby proportions, face and body balanced."
                )
            elif story_id == 'furry_love_teen_illustrated':
                # Teen — same minimal @image1 approach as baby and adventure: let Kontext read the photo directly
                kontext_prompt = (
                    f"Convert the {gender_word} in @image1 into a high-quality 3D animated children's book character. "
                    f"Preserve the exact face, eye color, skin tone, and hair — identical likeness. "
                    f"OUTFIT: casual hoodie and jeans, sneakers — modern teen style. "
                    f"BACKGROUND: soft cream gradient, plain studio. "
                    f"POSE: standing, full body visible from head to feet, confident friendly smile, arms relaxed at sides."
                )
            elif story_id == 'furry_love_adult_illustrated':
                # Adult — mountain adventure story. Minimalist: let Kontext read @image1 directly.
                kontext_prompt = (
                    f"Convert the adult {gender_word} in @image1 into a high-quality 3D animated storybook character. "
                    f"Preserve the exact face, eye color, hair color, skin tone, and age from the photo — identical adult likeness. "
                    f"OUTFIT: casual outdoor hiking clothes (flannel shirt or fleece, cargo pants, hiking boots). "
                    f"BACKGROUND: soft cream gradient, plain studio. "
                    f"POSE: standing, full body visible from head to feet, relaxed confident smile, arms naturally at sides."
                )
            else:
                # Kids (3-8 años) — minimal prompt like baby: convert from photo, no characteristic descriptions
                kontext_prompt = (
                    f"Convert the {gender_word} in @image1 into a high-quality 3D animated children's book character. "
                    f"Preserve the exact face, eye color, skin tone, and hair — identical likeness. "
                    f"OUTFIT: colorful t-shirt with shorts or pants, sneakers — fun casual children's style. "
                    f"BACKGROUND: soft cream gradient, plain studio. "
                    f"POSE: standing, full body visible from head to feet, big joyful smile, arms relaxed at sides."
                )
            print(f"[PREVIEW DEBUG] story_id={story_id} | gender={gender_word} | age={age_display}")
            print(f"[PREVIEW DEBUG] skin_tone_key={traits.get('skin_tone','?')} | skin_tone_k={skin_tone_k}")
            print(f"[PREVIEW DEBUG] KONTEXT PROMPT FULL: {kontext_prompt}")
            try:
                human_url = generate_with_flux_kontext(kontext_prompt, human_photo_path, aspect_ratio="3:4")
            except Exception as kontext_err:
                print(f"[FURRY LOVE PREVIEW] Kontext failed ({str(kontext_err)[:150]}), falling back to PuLID...")
                try:
                    human_url = generate_with_flux_pulid(human_prompt, human_photo_path, width=768, height=1024)
                except Exception as pulid_err2:
                    print(f"[FURRY LOVE PREVIEW] PuLID also failed, falling back to FLUX 2 Dev...")
                    human_url = generate_with_flux2_dev(human_prompt, aspect_ratio="3:4", photo_ref_path=human_photo_path, image_prompt_strength=0.90)
        elif human_photo_path and use_pulid:
            print(f"[FURRY LOVE PREVIEW] Generating human preview WITH photo using FLUX PuLID (face identity): {human_photo_path}")
            try:
                human_url = generate_with_flux_pulid(human_prompt, human_photo_path, width=768, height=1024)
            except Exception as pulid_err:
                print(f"[FURRY LOVE PREVIEW] PuLID failed ({str(pulid_err)[:150]}), falling back to FLUX 2 Dev...")
                human_url = generate_with_flux2_dev(human_prompt, aspect_ratio="3:4", photo_ref_path=human_photo_path, image_prompt_strength=0.90)
        elif human_photo_path:
            print(f"[FURRY LOVE PREVIEW] Generating human preview WITH photo using FLUX 2 Dev (reference): {human_photo_path}")
            human_url = generate_with_flux2_dev(human_prompt, aspect_ratio="3:4", photo_ref_path=human_photo_path, image_prompt_strength=0.90)
        else:
            print(f"[FURRY LOVE PREVIEW] Generating human preview (no photo)...")
            _hair_neg = "full hair, thick voluminous hair, hair covering entire head, dense hair" if traits.get('hair_length') == 'very_little' else None
            human_url = generate_with_flux2_dev(human_prompt, aspect_ratio="3:4", image_prompt_strength=0.75, negative_prompt=_hair_neg)
        
        if pet_photo_path:
            print(f"[FURRY LOVE PREVIEW] Generating pet preview WITH photo reference: {pet_photo_path}")
        else:
            print(f"[FURRY LOVE PREVIEW] Generating pet preview (no photo)...")
        print(f"[PREVIEW DEBUG] pet_species={traits.get('pet_species','?')} | pet_size={traits.get('pet_size','?')} | pet_desc_raw='{traits.get('pet_desc','')}'")
        print(f"[PREVIEW DEBUG] PET PROMPT FULL: {pet_prompt}")
        pet_url = generate_with_flux2_dev(pet_prompt, aspect_ratio="3:4", photo_ref_path=pet_photo_path or None, image_prompt_strength=0.90)
        
        output_dir = 'generated/previews'
        os.makedirs(output_dir, exist_ok=True)
        
        human_path = save_image_locally(human_url, f'{output_dir}/preview_human_{uuid.uuid4().hex[:8]}.png')
        pet_path = save_image_locally(pet_url, f'{output_dir}/preview_pet_{uuid.uuid4().hex[:8]}.png')
        
        return {
            'success': True,
            'image_url': f'/{human_path}',
            'pet_image_url': f'/{pet_path}',
            'human_preview_path': human_path,
            'pet_preview_path': pet_path,
            'story_id': story_id,
            'child_age': child_age,
            'is_furry_love': True
        }
    
    else:
        gender_child = "boy" if gender == "male" else "girl" if gender == "female" else "child"
        hair_desc = get_hair_description(traits)
        eye_desc = get_eye_description(traits)
        skin_desc = get_unified_skin_description(traits.get('skin_tone', 'light'))
        
        prompt = f"Full body portrait of a {child_age} year old {gender_child} with {hair_desc}, {eye_desc} and {skin_desc}. Happy curious expression. Children's storybook watercolor illustration style, soft luminous colors, warm magical lighting. NO text, NO watermark, clean illustration only"
        
        print(f"[PERSONALIZED PREVIEW] {story_id} (fallback), age={child_age}")
    
    if child_photo_path:
        print(f"[UNIVERSOS PREVIEW] Using photo reference: {child_photo_path}")
    # With photo: 0.90 strength so model prioritises the child's photo appearance
    # Without photo: 0.50 balanced (all traits come from form text description)
    _photo_strength = 0.90 if (child_photo_path and os.path.exists(child_photo_path)) else 0.50
    _neg_prompt = get_gender_negative_prompt(gender)
    image_url = generate_with_flux2_dev(prompt, aspect_ratio="3:4", photo_ref_path=child_photo_path if child_photo_path else None, image_prompt_strength=_photo_strength, negative_prompt=_neg_prompt)
    
    output_dir = 'generated/previews'
    os.makedirs(output_dir, exist_ok=True)
    local_path = save_image_locally(image_url, f'{output_dir}/preview_{uuid.uuid4().hex[:8]}.png')
    
    return {
        'success': True,
        'image_url': f'/{local_path}',
        'story_id': story_id,
        'child_age': child_age
    }
