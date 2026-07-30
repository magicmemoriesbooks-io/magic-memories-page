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
    For calls with image refs, delegates to _create_and_poll_prediction to avoid
    HTTP read timeouts (each timeout would restart a new prediction on Replicate's side).
    ref_file_paths: list of file paths to reopen on each retry for fresh file handles."""
    if ref_file_paths:
        return _create_and_poll_prediction(input_params, ref_file_paths)
    # Text-only calls: fast (<30s), use blocking run()
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            params = dict(input_params)
            param_keys = list(params.keys())
            print(f"[PREVIEW] Calling replicate.run attempt {attempt}: params={param_keys}, refs=0, prompt_len={len(params.get('prompt',''))}")
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
    raise last_error


def _file_to_base64_uri(path: str) -> str:
    """Convert a local image file to a base64 data URI for inline Replicate input.
    Avoids the separate /v1/files upload step that the SDK performs for file handles."""
    import base64, mimetypes
    mime = mimetypes.guess_type(path)[0] or "image/png"
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    return f"data:{mime};base64,{data}"


def _create_and_poll_prediction(input_params, ref_file_paths):
    """Create a Replicate prediction and poll until completion.
    Resilient to HTTP read timeouts — the prediction continues running on Replicate's
    side even if the HTTP connection drops, so we just keep polling the same ID.
    Images are sent as base64 data URIs (inline) to skip the separate /v1/files upload
    step that the SDK performs when receiving open file handles — saves ~2-5s per call.
    If the prediction itself fails (NSFW, CUDA OOM, etc.) we create a new one."""
    import time as _time
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        prediction = None
        try:
            params = dict(input_params)
            t_enc = _time.time()
            b64_refs = [_file_to_base64_uri(p) for p in ref_file_paths]
            params["input_images"] = b64_refs
            ref_count = len(b64_refs)
            print(f"[PREVIEW] Creating prediction attempt {attempt}: refs={ref_count}, encoded in {_time.time()-t_enc:.1f}s, prompt_len={len(params.get('prompt',''))}")
            prediction = _replicate_client.predictions.create(
                model="black-forest-labs/flux-2-dev",
                input=params
            )
            print(f"[PREVIEW] Prediction {prediction.id} created — polling...")
        except Exception as e:
            last_error = e
            print(f"[PREVIEW] Create failed attempt {attempt}: {str(e)[:200]}")

        if prediction is None:
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
                continue
            raise last_error

        # Poll until the prediction finishes (no HTTP timeout risk)
        poll_count = 0
        while prediction.status not in ('succeeded', 'failed', 'canceled'):
            time.sleep(4)
            try:
                prediction.reload()
            except Exception:
                pass  # Transient poll error — keep polling same prediction
            poll_count += 1
            if poll_count % 8 == 0:
                print(f"[PREVIEW] Polling {prediction.id}: {prediction.status} (~{poll_count * 4}s elapsed)")

        if prediction.status == 'succeeded':
            print(f"[PREVIEW] Prediction complete on attempt {attempt}!")
            return prediction.output

        err = str(prediction.error or 'unknown error')
        print(f"[PREVIEW] Prediction failed attempt {attempt}: {err[:200]}")
        last_error = Exception(f"Prediction failed: {err}")
        is_retryable = any(e in err for e in RETRYABLE_ERRORS)
        if is_retryable and attempt < MAX_RETRIES:
            wait = RETRY_DELAY + (attempt - 1) * 3
            print(f"[PREVIEW] Retrying in {wait}s...")
            time.sleep(wait)
            continue
        raise last_error

    raise last_error


def generate_with_flux2_dev(prompt: str, aspect_ratio: str = "3:4", photo_ref_path: str = None, photo_ref_paths: list = None, image_prompt_strength: float = 0.50, negative_prompt: str = None, force_go_fast: bool = False, high_quality: bool = False) -> str:
    """Generate illustration using FLUX 2 Dev (better consistency for series).
    If photo_ref_path is provided, uses it as single input_images reference.
    If photo_ref_paths is provided, uses multiple input_images references (e.g. human + pet).
    image_prompt_strength: 0.0=all text, 1.0=all image. Default 0.50 (50/50 balance).
    With 2 refs (human+pet): each ref ~25%, text 50% — better characteristic control.
    With 1 ref (single photo): ref 50%, text 50% — balanced face+trait fidelity.
    negative_prompt: passed as separate FLUX parameter to suppress unwanted features (tails, animal features).
    force_go_fast: when True, keeps go_fast=True even with photo refs (for previews — faster, slightly lower quality).
    high_quality: when True, sets go_fast=False even without photo refs (portrait SISTEMA 2 — full quality)."""
    input_params = {
        "prompt": prompt,
        "aspect_ratio": aspect_ratio,
        "output_format": "png",
        "go_fast": False if high_quality else True
    }
    if negative_prompt:
        input_params["negative_prompt"] = negative_prompt
    
    if photo_ref_paths:
        valid_paths = [p for p in photo_ref_paths if p and os.path.exists(p)]
        if valid_paths:
            print(f"[PREVIEW] Generating with FLUX 2 Dev + {len(valid_paths)} photo references (strength={image_prompt_strength}): {valid_paths}")
            print(f"[PREVIEW] Prompt ({len(prompt)} chars): {prompt[:200]}...")
            if not force_go_fast:
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
        if not force_go_fast:
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
            "Create the definitive reference design for LUNA, "
            "the recurring companion character of an illustrated children's book series.\n\n"
            "STYLE:\n"
            "Disney Pixar 3D style illustration.\n\n"
            "CHARACTER:\n"
            "LUNA is a small cute five-pointed star shape with a solid shimmering silver-white body. "
            "Two large expressive bright violet eyes on the star face. "
            "Tiny delicate translucent wings on the sides of the star. "
            "Soft warm silver glow surrounding the body.\n\n"
            "The design must be immediately recognizable and remain visually consistent "
            "across every illustration in the book series.\n\n"
            "Preserve:\n"
            "- overall body shape and proportions\n"
            "- facial features\n"
            "- eye shape and eye color\n"
            "- colors and textures\n"
            "- distinctive accessories or markings\n\n"
            "POSE:\n"
            "Floating gently in midair, full character completely visible.\n\n"
            "COMPOSITION:\n"
            "Single character only.\n"
            "Centered in the frame.\n"
            "Full character completely visible.\n"
            "No part of the character may be cropped.\n"
            "Occupy approximately 70% of the frame.\n\n"
            "BACKGROUND:\n"
            "Plain deep midnight blue studio, no scenery, no props, no other characters.\n\n"
            "LIGHTING:\n"
            "Clean warm neutral cinematic studio lighting to prioritize preservation of "
            "original character colors.\n"
            "Clean illustration only.\n"
            "No scenery. No additional characters. No props or external objects.\n"
            "Only elements that are intrinsic to the character design.\n"
            "No text. No logos. No watermarks."
        )
        image_url = generate_with_flux2_dev(luna_prompt, aspect_ratio="1:1", high_quality=True)
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
    Uses Companion Master Prompt v1.0.
    """
    astro_path = 'static/assets/astro_reference.png'
    if os.path.exists(astro_path):
        return astro_path
    print("[CENTINELA AURORA] Generating ASTRO reference image (first time only)...")
    try:
        astro_prompt = (
            "Create the definitive reference design for ASTRO, "
            "the recurring companion character of an illustrated children's book series.\n\n"
            "STYLE:\n"
            "Disney Pixar 3D style illustration.\n\n"
            "CHARACTER:\n"
            "A small magical fox named ASTRO, kitten-sized, vibrant electric blue fur covering the entire body, "
            "white chest patch, large expressive amber-golden eyes, a glowing star-tipped tail that emits soft "
            "electric blue light, a star-gem rope collar around the neck.\n\n"
            "The design must be immediately recognizable and remain visually consistent "
            "across every illustration in the book series.\n\n"
            "Preserve:\n"
            "- overall body shape and proportions\n"
            "- facial features\n"
            "- eye shape and eye color\n"
            "- colors and textures\n"
            "- distinctive accessories or markings\n\n"
            "POSE:\n"
            "Sitting naturally, full character completely visible.\n\n"
            "COMPOSITION:\n"
            "Single character only.\n"
            "Centered in the frame.\n"
            "Full character completely visible.\n"
            "No part of the character may be cropped.\n"
            "Occupy approximately 70% of the frame.\n\n"
            "BACKGROUND:\n"
            "Plain deep midnight blue studio, no scenery, no props, no other characters.\n\n"
            "LIGHTING:\n"
            "Clean warm neutral cinematic studio lighting to prioritize preservation of "
            "original character colors.\n"
            "Clean illustration only.\n"
            "No scenery. No additional characters. No props or external objects.\n"
            "Only elements that are intrinsic to the character design.\n"
            "No text. No logos. No watermarks."
        )
        image_url = generate_with_flux2_dev(astro_prompt, aspect_ratio="1:1", high_quality=True)
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
            "Create the definitive reference design for SPARK, "
            "the recurring companion character of an illustrated children's book series.\n\n"
            "STYLE:\n"
            "Disney Pixar 3D style illustration.\n\n"
            "CHARACTER:\n"
            "SPARK is an adorable baby dragon with a small chubby round body covered in shimmering "
            "emerald green scales, large expressive golden eyes, tiny translucent iridescent wings on "
            "the sides, short stubby tail, small rounded snout with a sweet gentle smile, two tiny "
            "curved horns on head, soft cream-colored belly.\n\n"
            "The design must be immediately recognizable and remain visually consistent "
            "across every illustration in the book series.\n\n"
            "Preserve:\n"
            "- overall body shape and proportions\n"
            "- facial features\n"
            "- eye shape and eye color\n"
            "- colors and textures\n"
            "- distinctive accessories or markings\n\n"
            "POSE:\n"
            "Floating gently in midair, full character completely visible, friendly expression.\n\n"
            "COMPOSITION:\n"
            "Single character only.\n"
            "Centered in the frame.\n"
            "Full character completely visible.\n"
            "No part of the character may be cropped.\n"
            "Occupy approximately 70% of the frame.\n\n"
            "BACKGROUND:\n"
            "Plain deep midnight blue studio, no scenery, no props, no other characters.\n\n"
            "LIGHTING:\n"
            "Clean warm neutral cinematic studio lighting to prioritize preservation of "
            "original character colors.\n"
            "Clean illustration only.\n"
            "No scenery. No additional characters. No props or external objects.\n"
            "Only elements that are intrinsic to the character design.\n"
            "No text. No logos. No watermarks."
        )
        image_url = generate_with_flux2_dev(spark_prompt, aspect_ratio="1:1", high_quality=True)
        from services.replicate_service import save_image_locally as _sil
        os.makedirs('static/assets', exist_ok=True)
        result_path = _sil(image_url, spark_path)
        if result_path and os.path.exists(spark_path):
            print(f"[DRAGON GARDEN] SPARK reference saved: {spark_path}")
            return spark_path
    except Exception as e:
        print(f"[DRAGON GARDEN] SPARK reference generation failed: {e}")
    return ''


def _ensure_sweetie_reference() -> str:
    """Generate SWEETIE cake companion reference image once and cache it as a static asset.
    SWEETIE: adorable round rainbow layered cake character with eyes, mouth, arms and legs.
    """
    sweetie_path = 'static/assets/sweetie_reference.png'
    if os.path.exists(sweetie_path):
        return sweetie_path
    print("[MAGIC CHEF] Generating SWEETIE reference image (first time only)...")
    try:
        sweetie_prompt = (
            "Create the definitive reference design for SWEETIE, "
            "the recurring companion character of an illustrated children's book series.\n\n"
            "STYLE:\n"
            "Disney Pixar 3D style illustration.\n\n"
            "CHARACTER:\n"
            "SWEETIE is an adorable round whole rainbow layered cake character (not a slice). "
            "Multiple colorful layers: pink, blue, yellow, and green. "
            "Big expressive cartoon eyes on the front face of the cake. "
            "A friendly wide smiling mouth. "
            "Small adorable chubby arms and legs sticking out from the sides. "
            "Colorful frosting swirls on top with a single cherry. "
            "Bouncy cheerful round shape.\n\n"
            "The design must be immediately recognizable and remain visually consistent "
            "across every illustration in the book series.\n\n"
            "Preserve:\n"
            "- overall body shape and proportions\n"
            "- facial features\n"
            "- eye shape and eye color\n"
            "- colors and textures\n"
            "- distinctive accessories or markings\n\n"
            "POSE:\n"
            "Standing upright, full character completely visible from top to bottom. "
            "Bouncy cheerful pose with both arms slightly raised in excitement.\n\n"
            "COMPOSITION:\n"
            "Single character only.\n"
            "Centered in the frame.\n"
            "Full character completely visible.\n"
            "No part of the character may be cropped.\n"
            "Occupy approximately 70% of the frame.\n\n"
            "BACKGROUND:\n"
            "Plain deep midnight blue studio, no scenery, no props, no other characters.\n\n"
            "LIGHTING:\n"
            "Clean warm neutral cinematic studio lighting to prioritize preservation of "
            "original character colors.\n"
            "Clean illustration only.\n"
            "No scenery. No additional characters. No props or external objects.\n"
            "Only elements that are intrinsic to the character design.\n"
            "No text. No logos. No watermarks."
        )
        image_url = generate_with_flux2_dev(sweetie_prompt, aspect_ratio="1:1", high_quality=True)
        from services.replicate_service import save_image_locally as _sil
        os.makedirs('static/assets', exist_ok=True)
        result_path = _sil(image_url, sweetie_path)
        if result_path and os.path.exists(sweetie_path):
            print(f"[MAGIC CHEF] SWEETIE reference saved: {sweetie_path}")
            return sweetie_path
    except Exception as e:
        print(f"[MAGIC CHEF] SWEETIE reference generation failed: {e}")
    return ''


def _ensure_bolt_reference() -> str:
    """Generate BOLT robot companion reference image once and cache it as a static asset.
    Uses certified companion prompt template (Jul 2026): Disney Pixar 3D, plain midnight blue bg.
    """
    bolt_path = 'static/assets/bolt_reference.png'
    if os.path.exists(bolt_path):
        return bolt_path
    print("[MAGIC INVENTOR] Generating BOLT reference image (first time only)...")
    try:
        bolt_prompt = (
            "Create the definitive reference design for BOLT, "
            "the recurring companion character of an illustrated children's book series.\n\n"
            "STYLE:\n"
            "Disney Pixar 3D style illustration.\n\n"
            "CHARACTER:\n"
            "BOLT is a small chubby round robot with a perfectly spherical copper-patina body. "
            "Big round glowing bright blue LED eyes set in a flat face panel. "
            "Two short articulated metallic arms with rounded hands. "
            "Two short stumpy metallic legs with round feet. "
            "Small antenna on top of head with a blinking blue light at the tip. "
            "Rivets and small gear details visible on the body surface. "
            "Warm copper-brown metallic finish with natural patina.\n\n"
            "The design must be immediately recognizable and remain visually consistent "
            "across every illustration in the book series.\n\n"
            "Preserve:\n"
            "- overall body shape and proportions\n"
            "- facial features\n"
            "- eye shape and eye color\n"
            "- colors and textures\n"
            "- distinctive accessories or markings\n\n"
            "POSE:\n"
            "Standing upright, full body completely visible from top to bottom. "
            "Friendly cheerful pose with one arm raised in a gentle wave. "
            "Sweet gentle expression with eyes lit up bright blue.\n\n"
            "COMPOSITION:\n"
            "Single character only.\n"
            "Centered in the frame.\n"
            "Full character completely visible.\n"
            "No part of the character may be cropped.\n"
            "Occupy approximately 70% of the frame.\n\n"
            "BACKGROUND:\n"
            "Plain deep midnight blue studio, no scenery, no props, no other characters.\n\n"
            "LIGHTING:\n"
            "Clean warm neutral cinematic studio lighting to prioritize preservation of original character colors.\n"
            "Clean illustration only.\n"
            "No scenery. No additional characters. No props or external objects.\n"
            "Only elements that are intrinsic to the character design.\n"
            "No text. No logos. No watermarks."
        )
        image_url = generate_with_flux2_dev(bolt_prompt, aspect_ratio="1:1", high_quality=True)
        from services.replicate_service import save_image_locally as _sil
        os.makedirs('static/assets', exist_ok=True)
        result_path = _sil(image_url, bolt_path)
        if result_path and os.path.exists(bolt_path):
            print(f"[MAGIC INVENTOR] BOLT reference saved: {bolt_path}")
            return bolt_path
    except Exception as e:
        print(f"[MAGIC INVENTOR] BOLT reference generation failed: {e}")
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
    from services.age_profiles import get_age_profile
    
    # Determine if a photo is provided and build glasses description
    has_photo = bool(child_photo_path and os.path.exists(child_photo_path))
    glasses = traits.get('glasses', '')
    glasses_desc = ", wearing round glasses" if glasses else ""

    if story_id == 'dragon_garden_illustrated':
        from services.personalized_books.dragon_garden_prompts import (
            get_outfit_desc as dg_get_outfit_desc,
            STYLE_BASE as DG_STYLE_BASE,
            STYLE_BASE_COVER as DG_STYLE_BASE_COVER,
            FRONT_COVER as DG_FRONT_COVER,
            build_kontext_prompt as dg_build_kontext_prompt,
            build_avatar_prompt as dg_build_avatar_prompt,
            build_ref_note as dg_build_ref_note,
            build_nophoto_portrait_prompt as dg_build_nophoto_portrait,
        )

        gender_word = "boy" if gender == "male" else "girl" if gender == "female" else "child"
        age_display = f"{child_age} year old" if child_age and child_age > 0 else "6 year old"
        human_photo_path = traits.get('human_photo_path', child_photo_path or '')
        outfit_desc = dg_get_outfit_desc(gender)

        spark_path = _ensure_spark_reference()
        spark_ok = spark_path and os.path.exists(spark_path)

        output_dir = 'generated/previews'
        os.makedirs(output_dir, exist_ok=True)

        # Custom negative: no suprimir alas/escamas/cola de SPARK
        _dg_neg_base = (
            "text, watermark, signature, logo, letters, words, ugly, deformed, blurry, low quality, "
            "distorted face, wings on child, animal features on human, furry child, animal ears, extra limbs, "
            "dragon tail on human, scales on human"
        )
        dg_neg = (
            (_dg_neg_base + ", masculine features, boy haircut") if gender == 'female'
            else (_dg_neg_base + ", earrings, jewelry, bows, ribbons, makeup, lipstick, feminine accessories, girl features, ponytails, pigtails") if gender == 'male'
            else _dg_neg_base
        )
        eye_desc = get_eye_description(traits)
        profile, range_key = get_age_profile(child_age)
        print(f"[DRAGON GARDEN PREVIEW] age={child_age} range={range_key} display={profile['display']}")

        if human_photo_path and os.path.exists(human_photo_path):
            # ── SISTEMA 1 — con foto ──────────────────────────────────────────
            # REGEN: si ya existe un avatar aprobado, saltar PASO 1+2 completamente.
            # El avatar FLUX es fijo para toda la sesión — regenerar = nueva portada con el mismo avatar.
            _reuse = traits.get('reuse_portrait_path', '')
            if _reuse and os.path.exists(_reuse):
                avatar_path = _reuse
                print(f"[DRAGON GARDEN PREVIEW] REGEN — avatar fijo reutilizado, PASO 1+2 omitidos: {avatar_path}")
            else:
                # PASO 1: Kontext portrait
                kontext_prompt = dg_build_kontext_prompt(
                    age_display, gender_word, profile['kontext'], eye_desc, outfit_desc
                )
                print(f"[DRAGON GARDEN PREVIEW] PASO 1 KONTEXT PROMPT: {kontext_prompt}")
                print(f"[DRAGON GARDEN PREVIEW] PASO 1 — Kontext portrait | photo={human_photo_path}")
                portrait_url = generate_with_flux_kontext(kontext_prompt, human_photo_path, aspect_ratio="3:4")
                portrait_path = save_image_locally(portrait_url, f'{output_dir}/dg_kontext_{uuid.uuid4().hex[:8]}.png')
                print(f"[DRAGON GARDEN PREVIEW] PASO 1 — Kontext guardado: {portrait_path}")

                # PASO 2: FLUX 2 Dev Avatar
                avatar_prompt = dg_build_avatar_prompt(age_display, gender_word)
                print(f"[DRAGON GARDEN PREVIEW] PASO 2 — FLUX avatar | kontext={portrait_path}")
                avatar_url = generate_with_flux2_dev(
                    avatar_prompt,
                    aspect_ratio="3:4",
                    photo_ref_path=portrait_path,
                    image_prompt_strength=1.0,
                    force_go_fast=False,
                )
                avatar_path = save_image_locally(avatar_url, f'{output_dir}/dg_avatar_{uuid.uuid4().hex[:8]}.png')
                print(f"[DRAGON GARDEN PREVIEW] PASO 2 — Avatar guardado: {avatar_path}")

            # PASO 3: FLUX 2 Dev Portada
            from services.personalized_books.age_profiles_nophoto import get_age_profile_nophoto as _get_dg_nophoto
            _s1_nophoto_profile, _ = _get_dg_nophoto(child_age)
            dg_ref_note = dg_build_ref_note(
                age_display, gender_word, _s1_nophoto_profile['cover_ref'], eye_desc, outfit_desc
            )
            dg_cover_scene = DG_FRONT_COVER.get('prompt', '').replace('{style}', DG_STYLE_BASE_COVER)
            dg_cover_prompt = f"{dg_ref_note}\n{dg_cover_scene}"
            photo_refs = [avatar_path, spark_path] if spark_ok else [avatar_path]
            dg_cover_neg = dg_neg + ", multiple dragons, two dragons, extra dragon"
            print(f"[DRAGON GARDEN PREVIEW] PASO 3 — FLUX portada | avatar={avatar_path} | spark={spark_ok}")
            cov_url = generate_with_flux2_dev(
                dg_cover_prompt,
                aspect_ratio="3:4",
                photo_ref_paths=photo_refs,
                image_prompt_strength=0.95,
                negative_prompt=dg_cover_neg,
                force_go_fast=False,
            )
        else:
            # ══════════════════════════════════════════════════════════════════
            # SISTEMA 2 — SIN FOTO: dos llamadas FLUX independientes
            # Llamada 1: portrait del niño (solo texto, sin refs)
            # Llamada 2: portada (portrait @image1 + SPARK @image2)
            # ══════════════════════════════════════════════════════════════════
            from services.personalized_books.age_profiles_nophoto import (
                get_age_profile_nophoto, NOPHOTO_NEGATIVE_BY_AGE, NOPHOTO_PORTRAIT_NEGATIVE_BASE
            )
            from services.personalized_books.hairstyles import get_hairstyle, build_haircut_description

            nophoto_profile, nophoto_range_key = get_age_profile_nophoto(child_age)
            _nophoto_skin_map = {
                'light': 'warm light skin', 'very_light': 'pale light skin',
                'medium_light': 'light olive skin', 'medium': 'warm olive skin',
                'tan': 'warm tan skin', 'medium_dark': 'warm brown skin', 'dark': 'deep brown skin',
            }
            skin_tone = _nophoto_skin_map.get(traits.get('skin_tone', 'light'), 'warm light skin')
            hairstyle_data = get_hairstyle(traits.get('hairstyle', ''))
            if nophoto_profile.get('hair_note'):
                hair_line = nophoto_profile['hair_note']
                haircut_block = ""
            elif hairstyle_data:
                hair_line = build_haircut_description(hairstyle_data, traits)
                haircut_block = f"{hairstyle_data['block']}\n"
            else:
                hair_line = get_hair_description(traits, gender=gender)
                haircut_block = ""
            _glasses_s2 = ", wearing prescription glasses" if traits.get('glasses') == 'yes' else ""

            dg_portrait_prompt = dg_build_nophoto_portrait(
                age_display, gender_word, nophoto_profile, skin_tone, eye_desc, hair_line, haircut_block, outfit_desc, _glasses_s2
            )
            _neg_base = (
                "text, watermark, signature, logo, letters, words, ugly, deformed, blurry, low quality, "
                "distorted face, defined jawline, visible cheekbones, mature face, adult face, teenager, "
                "wings on child, animal features on human, furry child, animal ears, extra limbs"
            )
            _neg_gender = (
                "masculine features, boy haircut, flat chest strapped down, male jawline" if gender == "female"
                else "girl features, ponytails, pigtails, feminine accessories, earrings, jewelry, bows, ribbons, makeup, lipstick"
            )
            _neg_age_specific = NOPHOTO_NEGATIVE_BY_AGE.get(nophoto_range_key, '')
            dg_portrait_neg = (
                _neg_base + ", " + _neg_gender
                + ", " + NOPHOTO_PORTRAIT_NEGATIVE_BASE
                + (", " + _neg_age_specific if _neg_age_specific else "")
            )
            _reuse_s2 = traits.get('reuse_portrait_path', '')
            if _reuse_s2 and os.path.exists(_reuse_s2):
                nophoto_portrait_path = _reuse_s2
                print(f"[DRAGON GARDEN PREVIEW] REGEN S2 — portrait fijo reutilizado, Llamada 1 omitida: {nophoto_portrait_path}")
            else:
                print(f"[DRAGON GARDEN PREVIEW] SISTEMA 2 — Llamada 1: Portrait | age={child_age} range={nophoto_range_key}")
                portrait_url_s2 = generate_with_flux2_dev(
                    dg_portrait_prompt,
                    aspect_ratio="3:4",
                    photo_ref_paths=None,
                    negative_prompt=dg_portrait_neg,
                    high_quality=True
                )
                nophoto_portrait_path = save_image_locally(
                    portrait_url_s2, f'{output_dir}/dg_portrait_{uuid.uuid4().hex[:8]}.png'
                )
                print(f"[DRAGON GARDEN PREVIEW] SISTEMA 2 — Portrait guardado: {nophoto_portrait_path}")

            dg_nophoto_cover_ref = dg_build_ref_note(
                nophoto_profile['display'], gender_word, nophoto_profile['cover_ref'], eye_desc, outfit_desc
            )
            dg_nophoto_cover_scene = DG_FRONT_COVER.get('prompt', '').replace('{style}', DG_STYLE_BASE_COVER)
            dg_nophoto_cover_prompt = f"{dg_nophoto_cover_ref}\n{dg_nophoto_cover_scene}"
            cover_refs_s2 = [nophoto_portrait_path, spark_path] if spark_ok else [nophoto_portrait_path]
            dg_nophoto_cover_neg = dg_neg + ", multiple dragons, two dragons, extra dragon"
            print(f"[DRAGON GARDEN PREVIEW] SISTEMA 2 — Llamada 2: Portada")
            cov_url = generate_with_flux2_dev(
                dg_nophoto_cover_prompt,
                aspect_ratio="3:4",
                photo_ref_paths=cover_refs_s2,
                image_prompt_strength=0.95,
                negative_prompt=dg_nophoto_cover_neg,
                force_go_fast=False,
            )

        cover_path = save_image_locally(cov_url, f'{output_dir}/dg_cover_{uuid.uuid4().hex[:8]}.png')
        print(f"[DRAGON GARDEN PREVIEW] Cover scene generated: {cover_path}")
        result = {
            'success': True,
            'image_url': f'/{cover_path}',
            'story_id': story_id,
            'child_age': child_age
        }
        if human_photo_path and os.path.exists(human_photo_path) and 'avatar_path' in dir():
            result['kontext_portrait'] = f'/{avatar_path}'
        elif 'nophoto_portrait_path' in dir() and nophoto_portrait_path and os.path.exists(nophoto_portrait_path):
            result['kontext_portrait'] = f'/{nophoto_portrait_path}'
            result['nophoto_portrait'] = f'/{nophoto_portrait_path}'
        return result

    elif story_id == 'magic_chef_illustrated':
        from services.personalized_books.magic_chef_prompts import (
            get_outfit_desc as chef_get_outfit_desc,
            STYLE_BASE as CHEF_STYLE_BASE,
            STYLE_BASE_COVER as CHEF_STYLE_BASE_COVER,
            FRONT_COVER as MC_FRONT_COVER,
            build_kontext_prompt as mc_build_kontext_prompt,
            build_avatar_prompt as mc_build_avatar_prompt,
            build_ref_note as mc_build_ref_note,
            build_nophoto_portrait_prompt as mc_build_nophoto_portrait,
        )

        gender_word = "boy" if gender == "male" else "girl" if gender == "female" else "child"
        age_display = f"{child_age} year old" if child_age and child_age > 0 else "6 year old"
        human_photo_path = traits.get('human_photo_path', child_photo_path or '')
        outfit_desc = chef_get_outfit_desc(gender)

        sweetie_path = _ensure_sweetie_reference()
        sweetie_ok = sweetie_path and os.path.exists(sweetie_path)

        output_dir = 'generated/previews'
        os.makedirs(output_dir, exist_ok=True)

        # Custom negative: SWEETIE es un personaje animado (no humano), no suprimir globalmente
        _chef_neg_base = (
            "text, watermark, signature, logo, letters, words, ugly, deformed, blurry, low quality, "
            "distorted face, wings on child, animal features on human, furry child, animal ears, extra limbs"
        )
        chef_neg = (
            (_chef_neg_base + ", masculine features, boy haircut") if gender == 'female'
            else (_chef_neg_base + ", earrings, jewelry, bows, ribbons, makeup, lipstick, feminine accessories, girl features, ponytails, pigtails") if gender == 'male'
            else _chef_neg_base
        )
        eye_desc = get_eye_description(traits)
        profile, range_key = get_age_profile(child_age)
        print(f"[MAGIC CHEF PREVIEW] age={child_age} range={range_key} display={profile['display']}")

        if human_photo_path and os.path.exists(human_photo_path):
            # ── SISTEMA 1 — con foto ──────────────────────────────────────────
            # REGEN: si ya existe un avatar aprobado, saltar PASO 1+2 completamente.
            # El avatar FLUX es fijo para toda la sesión — regenerar = nueva portada con el mismo avatar.
            _reuse = traits.get('reuse_portrait_path', '')
            if _reuse and os.path.exists(_reuse):
                avatar_path = _reuse
                print(f"[MAGIC CHEF PREVIEW] REGEN — avatar fijo reutilizado, PASO 1+2 omitidos: {avatar_path}")
            else:
                # PASO 1: Kontext portrait
                kontext_prompt = mc_build_kontext_prompt(
                    age_display, gender_word, profile['kontext'], eye_desc, outfit_desc
                )
                print(f"[MAGIC CHEF PREVIEW] PASO 1 — Kontext portrait | photo={human_photo_path}")
                portrait_url = generate_with_flux_kontext(kontext_prompt, human_photo_path, aspect_ratio="3:4")
                portrait_path = save_image_locally(portrait_url, f'{output_dir}/chef_kontext_{uuid.uuid4().hex[:8]}.png')
                print(f"[MAGIC CHEF PREVIEW] PASO 1 — Kontext guardado: {portrait_path}")

                # PASO 2: FLUX 2 Dev Avatar
                avatar_prompt = mc_build_avatar_prompt(age_display, gender_word)
                print(f"[MAGIC CHEF PREVIEW] PASO 2 — FLUX avatar | kontext={portrait_path}")
                avatar_url = generate_with_flux2_dev(
                    avatar_prompt,
                    aspect_ratio="3:4",
                    photo_ref_path=portrait_path,
                    image_prompt_strength=1.0,
                    force_go_fast=False,
                )
                avatar_path = save_image_locally(avatar_url, f'{output_dir}/chef_avatar_{uuid.uuid4().hex[:8]}.png')
                print(f"[MAGIC CHEF PREVIEW] PASO 2 — Avatar guardado: {avatar_path}")

            from services.personalized_books.age_profiles_nophoto import get_age_profile_nophoto as _get_mc_nophoto
            _s1_nophoto_profile, _ = _get_mc_nophoto(child_age)
            mc_ref_note = mc_build_ref_note(
                age_display, gender_word, _s1_nophoto_profile['cover_ref'], eye_desc, outfit_desc
            )
            mc_cover_scene = MC_FRONT_COVER.get('prompt', '').replace('{style}', CHEF_STYLE_BASE_COVER)
            mc_cover_prompt = f"{mc_ref_note}\n{mc_cover_scene}"
            photo_refs = [avatar_path, sweetie_path] if sweetie_ok else [avatar_path]
            mc_cover_neg = chef_neg + ", multiple cakes, extra SWEETIE, duplicate cake"
            print(f"[MAGIC CHEF PREVIEW] PASO 3 — FLUX portada | avatar={avatar_path} | sweetie={sweetie_ok}")
            cov_url = generate_with_flux2_dev(
                mc_cover_prompt,
                aspect_ratio="3:4",
                photo_ref_paths=photo_refs,
                image_prompt_strength=0.95,
                negative_prompt=mc_cover_neg,
                force_go_fast=False,
            )
        else:
            # ══════════════════════════════════════════════════════════════════
            # SISTEMA 2 — SIN FOTO
            # ══════════════════════════════════════════════════════════════════
            from services.personalized_books.age_profiles_nophoto import (
                get_age_profile_nophoto, NOPHOTO_NEGATIVE_BY_AGE, NOPHOTO_PORTRAIT_NEGATIVE_BASE
            )
            from services.personalized_books.hairstyles import get_hairstyle, build_haircut_description

            nophoto_profile, nophoto_range_key = get_age_profile_nophoto(child_age)
            _nophoto_skin_map = {
                'light': 'warm light skin', 'very_light': 'pale light skin',
                'medium_light': 'light olive skin', 'medium': 'warm olive skin',
                'tan': 'warm tan skin', 'medium_dark': 'warm brown skin', 'dark': 'deep brown skin',
            }
            skin_tone = _nophoto_skin_map.get(traits.get('skin_tone', 'light'), 'warm light skin')
            hairstyle_data = get_hairstyle(traits.get('hairstyle', ''))
            if nophoto_profile.get('hair_note'):
                hair_line = nophoto_profile['hair_note']
                haircut_block = ""
            elif hairstyle_data:
                hair_line = build_haircut_description(hairstyle_data, traits)
                haircut_block = f"{hairstyle_data['block']}\n"
            else:
                hair_line = get_hair_description(traits, gender=gender)
                haircut_block = ""
            _glasses_s2 = ", wearing prescription glasses" if traits.get('glasses') == 'yes' else ""

            mc_portrait_prompt = mc_build_nophoto_portrait(
                age_display, gender_word, nophoto_profile, skin_tone, eye_desc, hair_line, haircut_block, outfit_desc, _glasses_s2
            )
            _neg_base = (
                "text, watermark, signature, logo, letters, words, ugly, deformed, blurry, low quality, "
                "distorted face, defined jawline, visible cheekbones, mature face, adult face, teenager, "
                "wings on child, animal features on human, furry child, animal ears, extra limbs"
            )
            _neg_gender = (
                "masculine features, boy haircut, flat chest strapped down, male jawline" if gender == "female"
                else "girl features, ponytails, pigtails, feminine accessories, earrings, jewelry, bows, ribbons, makeup, lipstick"
            )
            _neg_age_specific = NOPHOTO_NEGATIVE_BY_AGE.get(nophoto_range_key, '')
            mc_portrait_neg = (
                _neg_base + ", " + _neg_gender
                + ", " + NOPHOTO_PORTRAIT_NEGATIVE_BASE
                + (", " + _neg_age_specific if _neg_age_specific else "")
            )
            _reuse_s2 = traits.get('reuse_portrait_path', '')
            if _reuse_s2 and os.path.exists(_reuse_s2):
                nophoto_portrait_path = _reuse_s2
                print(f"[MAGIC CHEF PREVIEW] REGEN S2 — portrait fijo reutilizado, Llamada 1 omitida: {nophoto_portrait_path}")
            else:
                print(f"[MAGIC CHEF PREVIEW] SISTEMA 2 — Llamada 1: Portrait | age={child_age} range={nophoto_range_key}")
                portrait_url_s2 = generate_with_flux2_dev(
                    mc_portrait_prompt,
                    aspect_ratio="3:4",
                    photo_ref_paths=None,
                    negative_prompt=mc_portrait_neg,
                    high_quality=True
                )
                nophoto_portrait_path = save_image_locally(
                    portrait_url_s2, f'{output_dir}/chef_portrait_{uuid.uuid4().hex[:8]}.png'
                )
                print(f"[MAGIC CHEF PREVIEW] SISTEMA 2 — Portrait guardado: {nophoto_portrait_path}")

            mc_nophoto_cover_ref = mc_build_ref_note(
                nophoto_profile['display'], gender_word, nophoto_profile['cover_ref'], eye_desc, outfit_desc
            )
            mc_nophoto_cover_scene = MC_FRONT_COVER.get('prompt', '').replace('{style}', CHEF_STYLE_BASE_COVER)
            mc_nophoto_cover_prompt = f"{mc_nophoto_cover_ref}\n{mc_nophoto_cover_scene}"
            cover_refs_s2 = [nophoto_portrait_path, sweetie_path] if sweetie_ok else [nophoto_portrait_path]
            mc_nophoto_cover_neg = chef_neg + ", multiple cakes, extra SWEETIE, duplicate cake"
            print(f"[MAGIC CHEF PREVIEW] SISTEMA 2 — Llamada 2: Portada")
            cov_url = generate_with_flux2_dev(
                mc_nophoto_cover_prompt,
                aspect_ratio="3:4",
                photo_ref_paths=cover_refs_s2,
                image_prompt_strength=0.95,
                negative_prompt=mc_nophoto_cover_neg,
                force_go_fast=False,
            )

        cover_path = save_image_locally(cov_url, f'{output_dir}/chef_cover_{uuid.uuid4().hex[:8]}.png')
        print(f"[MAGIC CHEF PREVIEW] Cover generated: {cover_path}")
        result = {
            'success': True,
            'image_url': f'/{cover_path}',
            'story_id': story_id,
            'child_age': child_age
        }
        if human_photo_path and os.path.exists(human_photo_path) and 'avatar_path' in dir():
            result['kontext_portrait'] = f'/{avatar_path}'
        elif 'nophoto_portrait_path' in dir() and nophoto_portrait_path and os.path.exists(nophoto_portrait_path):
            result['kontext_portrait'] = f'/{nophoto_portrait_path}'
            result['nophoto_portrait'] = f'/{nophoto_portrait_path}'
        return result

    elif story_id == 'magic_inventor_illustrated':
        from services.personalized_books.magic_inventor_prompts import (
            get_outfit_desc as inventor_get_outfit_desc,
            STYLE_BASE as INVENTOR_STYLE_BASE,
            STYLE_BASE_COVER as INVENTOR_STYLE_BASE_COVER,
            FRONT_COVER as MI_FRONT_COVER,
            build_kontext_prompt as mi_build_kontext_prompt,
            build_avatar_prompt as mi_build_avatar_prompt,
            build_ref_note as mi_build_ref_note,
            build_nophoto_portrait_prompt as mi_build_nophoto_portrait,
        )

        gender_word = "boy" if gender == "male" else "girl" if gender == "female" else "child"
        age_display = f"{child_age} year old" if child_age and child_age > 0 else "6 year old"
        human_photo_path = traits.get('human_photo_path', child_photo_path or '')
        outfit_desc = inventor_get_outfit_desc(gender)

        bolt_path = _ensure_bolt_reference()
        bolt_ok = bolt_path and os.path.exists(bolt_path)

        output_dir = 'generated/previews'
        os.makedirs(output_dir, exist_ok=True)

        _inv_neg_base = (
            "text, watermark, signature, logo, letters, words, ugly, deformed, blurry, low quality, "
            "distorted face, wings on child, animal features on human, furry child, animal ears, extra limbs, "
            "mechanical parts on human, robot features on human"
        )
        inv_neg = (
            (_inv_neg_base + ", masculine features, boy haircut") if gender == 'female'
            else (_inv_neg_base + ", earrings, jewelry, bows, ribbons, makeup, lipstick, feminine accessories, girl features, ponytails, pigtails") if gender == 'male'
            else _inv_neg_base
        )
        eye_desc = get_eye_description(traits)
        profile, range_key = get_age_profile(child_age)
        print(f"[MAGIC INVENTOR PREVIEW] age={child_age} range={range_key} display={profile['display']}")

        if human_photo_path and os.path.exists(human_photo_path):
            # ── SISTEMA 1 — con foto ──────────────────────────────────────────
            # REGEN: si ya existe un avatar aprobado, saltar PASO 1+2 completamente.
            # El avatar FLUX es fijo para toda la sesión — regenerar = nueva portada con el mismo avatar.
            _reuse = traits.get('reuse_portrait_path', '')
            if _reuse and os.path.exists(_reuse):
                avatar_path = _reuse
                print(f"[MAGIC INVENTOR PREVIEW] REGEN — avatar fijo reutilizado, PASO 1+2 omitidos: {avatar_path}")
            else:
                # PASO 1: Kontext portrait
                kontext_prompt = mi_build_kontext_prompt(
                    age_display, gender_word, profile['kontext'], eye_desc, outfit_desc
                )
                print(f"[MAGIC INVENTOR PREVIEW] PASO 1 — Kontext portrait | photo={human_photo_path}")
                portrait_url = generate_with_flux_kontext(kontext_prompt, human_photo_path, aspect_ratio="3:4")
                portrait_path = save_image_locally(portrait_url, f'{output_dir}/inventor_kontext_{uuid.uuid4().hex[:8]}.png')
                print(f"[MAGIC INVENTOR PREVIEW] PASO 1 — Kontext guardado: {portrait_path}")

                # PASO 2: FLUX 2 Dev Avatar
                avatar_prompt = mi_build_avatar_prompt(age_display, gender_word)
                print(f"[MAGIC INVENTOR PREVIEW] PASO 2 — FLUX avatar | kontext={portrait_path}")
                avatar_url = generate_with_flux2_dev(
                    avatar_prompt,
                    aspect_ratio="3:4",
                    photo_ref_path=portrait_path,
                    image_prompt_strength=1.0,
                    force_go_fast=False,
                )
                avatar_path = save_image_locally(avatar_url, f'{output_dir}/inventor_avatar_{uuid.uuid4().hex[:8]}.png')
                print(f"[MAGIC INVENTOR PREVIEW] PASO 2 — Avatar guardado: {avatar_path}")

            from services.personalized_books.age_profiles_nophoto import get_age_profile_nophoto as _get_mi_nophoto
            _s1_nophoto_profile, _ = _get_mi_nophoto(child_age)
            mi_ref_note = mi_build_ref_note(
                age_display, gender_word, _s1_nophoto_profile['cover_ref'], eye_desc, outfit_desc
            )
            mi_cover_scene = MI_FRONT_COVER.get('prompt', '').replace('{style}', INVENTOR_STYLE_BASE_COVER)
            mi_cover_prompt = f"{mi_ref_note}\n{mi_cover_scene}"
            photo_refs = [avatar_path, bolt_path] if bolt_ok else [avatar_path]
            mi_cover_neg = inv_neg + ", multiple robots, extra robots, two robots"
            print(f"[MAGIC INVENTOR PREVIEW] PASO 3 — FLUX portada | avatar={avatar_path} | bolt={bolt_ok}")
            cov_url = generate_with_flux2_dev(
                mi_cover_prompt,
                aspect_ratio="3:4",
                photo_ref_paths=photo_refs,
                image_prompt_strength=0.95,
                negative_prompt=mi_cover_neg,
                force_go_fast=False,
            )
        else:
            # ══════════════════════════════════════════════════════════════════
            # SISTEMA 2 — SIN FOTO
            # ══════════════════════════════════════════════════════════════════
            from services.personalized_books.age_profiles_nophoto import (
                get_age_profile_nophoto, NOPHOTO_NEGATIVE_BY_AGE, NOPHOTO_PORTRAIT_NEGATIVE_BASE
            )
            from services.personalized_books.hairstyles import get_hairstyle, build_haircut_description

            nophoto_profile, nophoto_range_key = get_age_profile_nophoto(child_age)
            _nophoto_skin_map = {
                'light': 'warm light skin', 'very_light': 'pale light skin',
                'medium_light': 'light olive skin', 'medium': 'warm olive skin',
                'tan': 'warm tan skin', 'medium_dark': 'warm brown skin', 'dark': 'deep brown skin',
            }
            skin_tone = _nophoto_skin_map.get(traits.get('skin_tone', 'light'), 'warm light skin')
            hairstyle_data = get_hairstyle(traits.get('hairstyle', ''))
            if nophoto_profile.get('hair_note'):
                hair_line = nophoto_profile['hair_note']
                haircut_block = ""
            elif hairstyle_data:
                hair_line = build_haircut_description(hairstyle_data, traits)
                haircut_block = f"{hairstyle_data['block']}\n"
            else:
                hair_line = get_hair_description(traits, gender=gender)
                haircut_block = ""
            _glasses_s2 = ", wearing prescription glasses" if traits.get('glasses') == 'yes' else ""

            mi_portrait_prompt = mi_build_nophoto_portrait(
                age_display, gender_word, nophoto_profile, skin_tone, eye_desc, hair_line, haircut_block, outfit_desc, _glasses_s2
            )
            _neg_base = (
                "text, watermark, signature, logo, letters, words, ugly, deformed, blurry, low quality, "
                "distorted face, defined jawline, visible cheekbones, mature face, adult face, teenager, "
                "wings on child, animal features on human, furry child, animal ears, extra limbs"
            )
            _neg_gender = (
                "masculine features, boy haircut, flat chest strapped down, male jawline" if gender == "female"
                else "girl features, ponytails, pigtails, feminine accessories, earrings, jewelry, bows, ribbons, makeup, lipstick"
            )
            _neg_age_specific = NOPHOTO_NEGATIVE_BY_AGE.get(nophoto_range_key, '')
            mi_portrait_neg = (
                _neg_base + ", " + _neg_gender
                + ", " + NOPHOTO_PORTRAIT_NEGATIVE_BASE
                + (", " + _neg_age_specific if _neg_age_specific else "")
            )
            _reuse_s2 = traits.get('reuse_portrait_path', '')
            if _reuse_s2 and os.path.exists(_reuse_s2):
                nophoto_portrait_path = _reuse_s2
                print(f"[MAGIC INVENTOR PREVIEW] REGEN S2 — portrait fijo reutilizado, Llamada 1 omitida: {nophoto_portrait_path}")
            else:
                print(f"[MAGIC INVENTOR PREVIEW] SISTEMA 2 — Llamada 1: Portrait | age={child_age} range={nophoto_range_key}")
                portrait_url_s2 = generate_with_flux2_dev(
                    mi_portrait_prompt,
                    aspect_ratio="3:4",
                    photo_ref_paths=None,
                    negative_prompt=mi_portrait_neg,
                    high_quality=True
                )
                nophoto_portrait_path = save_image_locally(
                    portrait_url_s2, f'{output_dir}/inventor_portrait_{uuid.uuid4().hex[:8]}.png'
                )
                print(f"[MAGIC INVENTOR PREVIEW] SISTEMA 2 — Portrait guardado: {nophoto_portrait_path}")

            mi_nophoto_cover_ref = mi_build_ref_note(
                nophoto_profile['display'], gender_word, nophoto_profile['cover_ref'], eye_desc, outfit_desc
            )
            mi_nophoto_cover_scene = MI_FRONT_COVER.get('prompt', '').replace('{style}', INVENTOR_STYLE_BASE_COVER)
            mi_nophoto_cover_prompt = f"{mi_nophoto_cover_ref}\n{mi_nophoto_cover_scene}"
            cover_refs_s2 = [nophoto_portrait_path, bolt_path] if bolt_ok else [nophoto_portrait_path]
            mi_nophoto_cover_neg = inv_neg + ", multiple robots, extra robots, two robots"
            print(f"[MAGIC INVENTOR PREVIEW] SISTEMA 2 — Llamada 2: Portada")
            cov_url = generate_with_flux2_dev(
                mi_nophoto_cover_prompt,
                aspect_ratio="3:4",
                photo_ref_paths=cover_refs_s2,
                image_prompt_strength=0.95,
                negative_prompt=mi_nophoto_cover_neg,
                force_go_fast=False,
            )

        cover_path = save_image_locally(cov_url, f'{output_dir}/inventor_cover_{uuid.uuid4().hex[:8]}.png')
        print(f"[MAGIC INVENTOR PREVIEW] Cover generated: {cover_path}")
        result = {
            'success': True,
            'image_url': f'/{cover_path}',
            'story_id': story_id,
            'child_age': child_age
        }
        if human_photo_path and os.path.exists(human_photo_path) and 'avatar_path' in dir():
            result['kontext_portrait'] = f'/{avatar_path}'
        elif 'nophoto_portrait_path' in dir() and nophoto_portrait_path and os.path.exists(nophoto_portrait_path):
            result['kontext_portrait'] = f'/{nophoto_portrait_path}'
            result['nophoto_portrait'] = f'/{nophoto_portrait_path}'
        return result

    elif story_id == 'star_keeper_illustrated':
        from services.personalized_books.star_keeper_prompts import (
            get_outfit_desc as keeper_get_outfit_desc,
            STYLE_BASE as KEEPER_STYLE_BASE,
            STYLE_BASE_COVER as KEEPER_STYLE_BASE_COVER,
            FRONT_COVER as SK_FRONT_COVER,
            build_kontext_prompt as sk_build_kontext_prompt,
            build_avatar_prompt as sk_build_avatar_prompt,
            build_ref_note as sk_build_ref_note,
            build_nophoto_portrait_prompt as sk_build_nophoto_portrait,
        )

        gender_word = "boy" if gender == "male" else "girl" if gender == "female" else "child"
        age_display = f"{child_age} year old" if child_age and child_age > 0 else "6 year old"
        human_photo_path = traits.get('human_photo_path', child_photo_path or '')
        outfit_desc = keeper_get_outfit_desc(gender)

        luna_path = _ensure_luna_reference()
        luna_ok = luna_path and os.path.exists(luna_path)

        output_dir = 'generated/previews'
        os.makedirs(output_dir, exist_ok=True)

        # Custom negative: LUNA es estrella legítima, no suprimir "star glow"
        _sk_neg_base = (
            "text, watermark, signature, logo, letters, words, ugly, deformed, blurry, low quality, "
            "distorted face, wings on child, animal features on human, furry child, animal ears, extra limbs"
        )
        sk_neg = (
            (_sk_neg_base + ", masculine features, boy haircut") if gender == 'female'
            else (_sk_neg_base + ", earrings, jewelry, bows, ribbons, makeup, lipstick, feminine accessories, girl features, ponytails, pigtails") if gender == 'male'
            else _sk_neg_base
        )
        eye_desc = get_eye_description(traits)
        profile, range_key = get_age_profile(child_age)
        print(f"[STAR KEEPER PREVIEW] age={child_age} range={range_key} display={profile['display']}")

        if human_photo_path and os.path.exists(human_photo_path):
            # ── SISTEMA 1 — con foto ──────────────────────────────────────────
            _reuse = traits.get('reuse_portrait_path', '')
            if _reuse and os.path.exists(_reuse):
                portrait_path = _reuse
                print(f"[STAR KEEPER PREVIEW] Kontext SKIPPED — reutilizando portrait: {portrait_path}")
            else:
                kontext_prompt = sk_build_kontext_prompt(
                    age_display, gender_word, profile['kontext'], eye_desc, outfit_desc
                )
                print(f"[STAR KEEPER PREVIEW] PASO 1 — Kontext portrait | photo={human_photo_path}")
                portrait_url = generate_with_flux_kontext(kontext_prompt, human_photo_path, aspect_ratio="3:4")
                portrait_path = save_image_locally(portrait_url, f'{output_dir}/sk_kontext_{uuid.uuid4().hex[:8]}.png')
                print(f"[STAR KEEPER PREVIEW] PASO 1 — Kontext guardado: {portrait_path}")

            _avatar_neg_base = (
                "text, watermark, signature, logo, letters, words, ugly, deformed, blurry, low quality, "
                "distorted face, defined jawline, visible cheekbones, mature face, adult face, teenager, "
                "wings on child, animal features on human, furry child, animal ears, extra limbs"
            )
            _avatar_neg_gender = (
                "masculine features, boy haircut, male jawline" if gender == "female"
                else "girl features, ponytails, pigtails, feminine accessories, earrings, jewelry, bows, ribbons, makeup, lipstick"
            )
            avatar_prompt = sk_build_avatar_prompt(age_display, gender_word)
            print(f"[STAR KEEPER PREVIEW] PASO 2 — FLUX avatar | kontext={portrait_path}")
            avatar_url = generate_with_flux2_dev(
                avatar_prompt,
                aspect_ratio="3:4",
                photo_ref_path=portrait_path,
                image_prompt_strength=1.0,
                force_go_fast=False,
            )
            avatar_path = save_image_locally(avatar_url, f'{output_dir}/sk_avatar_{uuid.uuid4().hex[:8]}.png')
            print(f"[STAR KEEPER PREVIEW] PASO 2 — Avatar guardado: {avatar_path}")

            from services.personalized_books.age_profiles_nophoto import get_age_profile_nophoto as _get_sk_nophoto
            _s1_nophoto_profile, _ = _get_sk_nophoto(child_age)
            sk_ref_note = sk_build_ref_note(
                age_display, gender_word, _s1_nophoto_profile['cover_ref'], eye_desc, outfit_desc
            )
            sk_cover_scene = SK_FRONT_COVER.get('prompt', '').replace('{style}', KEEPER_STYLE_BASE_COVER)
            sk_cover_prompt = f"{sk_ref_note}\n{sk_cover_scene}"
            photo_refs = [avatar_path, luna_path] if luna_ok else [avatar_path]
            sk_cover_neg = sk_neg + ", multiple stars, extra star companions, two LUNAs"
            print(f"[STAR KEEPER PREVIEW] PASO 3 — FLUX portada | avatar={avatar_path} | luna={luna_ok}")
            cov_url = generate_with_flux2_dev(
                sk_cover_prompt,
                aspect_ratio="3:4",
                photo_ref_paths=photo_refs,
                image_prompt_strength=0.95,
                negative_prompt=sk_cover_neg,
                force_go_fast=False,
            )
        else:
            # ══════════════════════════════════════════════════════════════════
            # SISTEMA 2 — SIN FOTO
            # ══════════════════════════════════════════════════════════════════
            from services.personalized_books.age_profiles_nophoto import (
                get_age_profile_nophoto, NOPHOTO_NEGATIVE_BY_AGE, NOPHOTO_PORTRAIT_NEGATIVE_BASE
            )
            from services.personalized_books.hairstyles import get_hairstyle, build_haircut_description

            nophoto_profile, nophoto_range_key = get_age_profile_nophoto(child_age)
            _nophoto_skin_map = {
                'light': 'warm light skin', 'very_light': 'pale light skin',
                'medium_light': 'light olive skin', 'medium': 'warm olive skin',
                'tan': 'warm tan skin', 'medium_dark': 'warm brown skin', 'dark': 'deep brown skin',
            }
            skin_tone = _nophoto_skin_map.get(traits.get('skin_tone', 'light'), 'warm light skin')
            hairstyle_data = get_hairstyle(traits.get('hairstyle', ''))
            if nophoto_profile.get('hair_note'):
                hair_line = nophoto_profile['hair_note']
                haircut_block = ""
            elif hairstyle_data:
                hair_line = build_haircut_description(hairstyle_data, traits)
                haircut_block = f"{hairstyle_data['block']}\n"
            else:
                hair_line = get_hair_description(traits, gender=gender)
                haircut_block = ""
            _glasses_s2 = ", wearing prescription glasses" if traits.get('glasses') == 'yes' else ""

            sk_portrait_prompt = sk_build_nophoto_portrait(
                age_display, gender_word, nophoto_profile, skin_tone, eye_desc, hair_line, haircut_block, outfit_desc, _glasses_s2
            )
            _neg_base = (
                "text, watermark, signature, logo, letters, words, ugly, deformed, blurry, low quality, "
                "distorted face, defined jawline, visible cheekbones, mature face, adult face, teenager, "
                "wings on child, animal features on human, furry child, animal ears, extra limbs"
            )
            _neg_gender = (
                "masculine features, boy haircut, flat chest strapped down, male jawline" if gender == "female"
                else "girl features, ponytails, pigtails, feminine accessories, earrings, jewelry, bows, ribbons, makeup, lipstick"
            )
            _neg_age_specific = NOPHOTO_NEGATIVE_BY_AGE.get(nophoto_range_key, '')
            sk_portrait_neg = (
                _neg_base + ", " + _neg_gender
                + ", " + NOPHOTO_PORTRAIT_NEGATIVE_BASE
                + (", " + _neg_age_specific if _neg_age_specific else "")
            )
            _reuse_s2 = traits.get('reuse_portrait_path', '')
            if _reuse_s2 and os.path.exists(_reuse_s2):
                nophoto_portrait_path = _reuse_s2
                print(f"[STAR KEEPER PREVIEW] REGEN S2 — portrait fijo reutilizado, Llamada 1 omitida: {nophoto_portrait_path}")
            else:
                print(f"[STAR KEEPER PREVIEW] SISTEMA 2 — Llamada 1: Portrait | age={child_age} range={nophoto_range_key}")
                portrait_url_s2 = generate_with_flux2_dev(
                    sk_portrait_prompt,
                    aspect_ratio="3:4",
                    photo_ref_paths=None,
                    negative_prompt=sk_portrait_neg,
                    high_quality=True
                )
                nophoto_portrait_path = save_image_locally(
                    portrait_url_s2, f'{output_dir}/sk_portrait_{uuid.uuid4().hex[:8]}.png'
                )
                print(f"[STAR KEEPER PREVIEW] SISTEMA 2 — Portrait guardado: {nophoto_portrait_path}")

            sk_nophoto_cover_ref = sk_build_ref_note(
                nophoto_profile['display'], gender_word, nophoto_profile['cover_ref'], eye_desc, outfit_desc
            )
            sk_nophoto_cover_scene = SK_FRONT_COVER.get('prompt', '').replace('{style}', KEEPER_STYLE_BASE_COVER)
            sk_nophoto_cover_prompt = f"{sk_nophoto_cover_ref}\n{sk_nophoto_cover_scene}"
            cover_refs_s2 = [nophoto_portrait_path, luna_path] if luna_ok else [nophoto_portrait_path]
            sk_nophoto_cover_neg = sk_neg + ", multiple stars, extra star companions, two LUNAs"
            print(f"[STAR KEEPER PREVIEW] SISTEMA 2 — Llamada 2: Portada")
            cov_url = generate_with_flux2_dev(
                sk_nophoto_cover_prompt,
                aspect_ratio="3:4",
                photo_ref_paths=cover_refs_s2,
                image_prompt_strength=0.95,
                negative_prompt=sk_nophoto_cover_neg,
                force_go_fast=False,
            )

        cover_path = save_image_locally(cov_url, f'{output_dir}/sk_cover_{uuid.uuid4().hex[:8]}.png')
        print(f"[STAR KEEPER PREVIEW] Cover scene generated: {cover_path}")
        result = {
            'success': True,
            'image_url': f'/{cover_path}',
            'story_id': story_id,
            'child_age': child_age
        }
        if human_photo_path and os.path.exists(human_photo_path) and 'avatar_path' in dir():
            result['kontext_portrait'] = f'/{avatar_path}'
        elif 'nophoto_portrait_path' in dir() and nophoto_portrait_path and os.path.exists(nophoto_portrait_path):
            result['kontext_portrait'] = f'/{nophoto_portrait_path}'
            result['nophoto_portrait'] = f'/{nophoto_portrait_path}'
        return result


    elif story_id == 'centinela_aurora_illustrated':
        from services.personalized_books.centinela_aurora_prompts import (
            get_outfit_desc as aurora_get_outfit_desc,
            STYLE_BASE as AURORA_STYLE_BASE,
            STYLE_BASE_COVER as AURORA_STYLE_BASE_COVER,
            FRONT_COVER as CA_FRONT_COVER,
            get_hair_action as aurora_get_hair_action,
            build_kontext_prompt as ca_build_kontext_prompt,
            build_avatar_prompt as ca_build_avatar_prompt,
            build_ref_note as ca_build_ref_note,
            build_nophoto_portrait_prompt as ca_build_nophoto_portrait,
        )
        from services.replicate_service import get_gender_negative_prompt as _ca_neg_fn

        gender_word = "boy" if gender == "male" else "girl" if gender == "female" else "child"
        age_display = f"{child_age} year old" if child_age and child_age > 0 else "6 year old"
        human_photo_path = traits.get('human_photo_path', child_photo_path or '')
        outfit_desc = aurora_get_outfit_desc(gender)

        astro_path = _ensure_astro_reference()
        astro_ok = astro_path and os.path.exists(astro_path)

        output_dir = 'generated/previews'
        os.makedirs(output_dir, exist_ok=True)

        # Custom negative_prompt for Centinela: tail terms removed because ASTRO legitimately has a tail.
        # Using get_gender_negative_prompt would suppress fox/fluffy tail globally and fight @image2 reference.
        _ca_neg_base = "text, watermark, signature, logo, letters, words, ugly, deformed, blurry, low quality, distorted face, wings on child, animal features on human, furry child, animal ears, cat ears, bunny ears, fox ears, extra limbs, hybrid creature, animal body parts on human"
        ca_neg = (_ca_neg_base + ", masculine features, boy haircut") if gender == 'female' else (_ca_neg_base + ", earrings, jewelry, bows, ribbons, makeup, lipstick, feminine accessories, girl features, ponytails, pigtails") if gender == 'male' else _ca_neg_base
        eye_desc = get_eye_description(traits)
        profile, range_key = get_age_profile(child_age)
        print(f"[CENTINELA AURORA PREVIEW] age={child_age} range={range_key} display={profile['display']}")

        if human_photo_path and os.path.exists(human_photo_path):
            # ── SISTEMA 1 — con foto ──────────────────────────────────────────
            # REGEN: si ya existe un avatar aprobado, saltar PASO 1+2 completamente.
            # El avatar FLUX es fijo para toda la sesión — regenerar = nueva portada con el mismo avatar.
            _reuse = traits.get('reuse_portrait_path', '')
            if _reuse and os.path.exists(_reuse):
                avatar_path = _reuse
                print(f"[CENTINELA AURORA PREVIEW] REGEN — avatar fijo reutilizado, PASO 1+2 omitidos: {avatar_path}")
            else:
                # PASO 1: Kontext portrait
                kontext_prompt = ca_build_kontext_prompt(
                    age_display, gender_word, profile['kontext'], eye_desc, outfit_desc
                )
                print(f"[CENTINELA AURORA PREVIEW] PASO 1 — Kontext portrait | photo={human_photo_path} | age={child_age}")
                portrait_url = generate_with_flux_kontext(kontext_prompt, human_photo_path, aspect_ratio="3:4")
                portrait_path = save_image_locally(portrait_url, f'{output_dir}/ca_kontext_{uuid.uuid4().hex[:8]}.png')
                print(f"[CENTINELA AURORA PREVIEW] PASO 1 — Kontext guardado: {portrait_path}")

                # PASO 2: FLUX 2 Dev Avatar
                avatar_prompt = ca_build_avatar_prompt(age_display, gender_word)
                print(f"[CENTINELA AURORA PREVIEW] PASO 2 — FLUX avatar | kontext={portrait_path}")
                avatar_url = generate_with_flux2_dev(
                    avatar_prompt,
                    aspect_ratio="3:4",
                    photo_ref_path=portrait_path,
                    image_prompt_strength=1.0,
                    force_go_fast=False,
                )
                avatar_path = save_image_locally(avatar_url, f'{output_dir}/ca_avatar_{uuid.uuid4().hex[:8]}.png')
                print(f"[CENTINELA AURORA PREVIEW] PASO 2 — Avatar guardado: {avatar_path}")

            # ── PASO 3: FLUX 2 Dev Portada — avatar + ASTRO → portada ────────────
            from services.personalized_books.age_profiles_nophoto import get_age_profile_nophoto as _get_ca_nophoto
            _s1_nophoto_profile, _ = _get_ca_nophoto(child_age)
            ca_ref_note = ca_build_ref_note(
                age_display, gender_word, _s1_nophoto_profile['cover_ref'], eye_desc, outfit_desc
            )
            ca_cover_scene = CA_FRONT_COVER.get('prompt', '').replace('{style}', AURORA_STYLE_BASE_COVER)
            ca_cover_prompt = f"{ca_ref_note}\n{ca_cover_scene}"
            photo_refs = [avatar_path, astro_path] if astro_ok else [avatar_path]
            ca_cover_neg = ca_neg + ", two tails, multiple tails, double tail, split tail, extra tail, floating star, detached star, star beside tail, star separate from tail"
            print(f"[CENTINELA AURORA PREVIEW] PASO 3 — FLUX portada | avatar={avatar_path} | astro={astro_ok}")
            cov_url = generate_with_flux2_dev(
                ca_cover_prompt,
                aspect_ratio="3:4",
                photo_ref_paths=photo_refs,
                image_prompt_strength=0.95,
                negative_prompt=ca_cover_neg,
                force_go_fast=False,
            )
        else:
            # ══════════════════════════════════════════════════════════════════
            # SISTEMA 2 — SIN FOTO: pipeline de dos llamadas FLUX independiente
            # NO usa AGE_PROFILE (SISTEMA 1). NO usa Kontext.
            # Llamada 1: portrait del niño (solo texto, sin refs)
            # Llamada 2: portada (portrait + ASTRO)
            # Las escenas también usarán portrait_path como @image1.
            # ══════════════════════════════════════════════════════════════════
            from services.personalized_books.age_profiles_nophoto import (
                get_age_profile_nophoto, NOPHOTO_NEGATIVE_BY_AGE, NOPHOTO_PORTRAIT_NEGATIVE_BASE
            )
            from services.personalized_books.hairstyles import get_hairstyle, build_haircut_description

            nophoto_profile, nophoto_range_key = get_age_profile_nophoto(child_age)
            hair_action = aurora_get_hair_action(traits)
            # SISTEMA 2: skin descriptor simple — sin "rosy", "pink" ni "undertones"
            # para evitar que FLUX pinte nariz/cachetes rojos
            _nophoto_skin_map = {
                'light':        'warm light skin',
                'very_light':   'pale light skin',
                'medium_light': 'light olive skin',
                'medium':       'warm olive skin',
                'tan':          'warm tan skin',
                'medium_dark':  'warm brown skin',
                'dark':         'deep brown skin',
            }
            skin_tone = _nophoto_skin_map.get(traits.get('skin_tone', 'light'), 'warm light skin')
            # Todos los cortes son unisex: si hay un corte seleccionado se aplica sin importar género.
            # Si no hay corte (o es bebé), se usa descripción natural (color + largo + tipo).
            hairstyle_data = get_hairstyle(traits.get('hairstyle', ''))

            if nophoto_profile.get('hair_note'):
                # Bebé (1-2 años): ignorar hairstyle seleccionado, usar descripción de pelo de bebé
                hair_line = nophoto_profile['hair_note']
                haircut_block = ""
            elif hairstyle_data:
                # Corte seleccionado: color + textura (si aplica) + forma del corte. El largo NO se usa.
                hair_line = build_haircut_description(hairstyle_data, traits)
                haircut_block = f"{hairstyle_data['block']}\n"
            else:
                # Sin corte → descripción natural completa: color + largo + tipo
                hair_line = get_hair_description(traits, gender=gender)
                haircut_block = ""

            # ── Llamada 1: Portrait del niño ─────────────────────────────────
            # Prompt estructura: CHARACTER → AGE → PROPORTIONS → FACE → SKIN
            #                    → EYES → HAIR → HAIRCUT → OUTFIT → POSE
            #                    → BACKGROUND → STRICT → STYLE
            _glasses_s2 = ", wearing prescription glasses" if traits.get('glasses') == 'yes' else ""
            ca_portrait_prompt = ca_build_nophoto_portrait(
                age_display, gender_word, nophoto_profile, skin_tone, eye_desc, hair_line, haircut_block, outfit_desc, _glasses_s2
            )
            # Negative: gender-specific (NUNCA poner "girl features" para niñas)
            # Niño: suprimir rasgos femeninos. Niña: suprimir rasgos masculinos.
            _neg_base = (
                "text, watermark, signature, logo, letters, words, ugly, deformed, blurry, low quality, "
                "distorted face, defined jawline, visible cheekbones, mature face, adult face, teenager, "
                "wings on child, animal features on human, furry child, animal ears, extra limbs"
            )
            if gender == "female":
                _neg_gender = "masculine features, boy haircut, flat chest strapped down, male jawline"
            else:
                _neg_gender = (
                    "girl features, ponytails, pigtails, feminine accessories, "
                    "earrings, jewelry, bows, ribbons, makeup, lipstick"
                )
            _neg_age_specific = NOPHOTO_NEGATIVE_BY_AGE.get(nophoto_range_key, '')
            ca_portrait_neg = (
                _neg_base + ", " + _neg_gender
                + ", " + NOPHOTO_PORTRAIT_NEGATIVE_BASE
                + (", " + _neg_age_specific if _neg_age_specific else "")
            )

            _reuse_s2 = traits.get('reuse_portrait_path', '')
            if _reuse_s2 and os.path.exists(_reuse_s2):
                nophoto_portrait_path = _reuse_s2
                print(f"[CENTINELA AURORA PREVIEW] REGEN S2 — portrait fijo reutilizado, Llamada 1 omitida: {nophoto_portrait_path}")
            else:
                print(f"[CENTINELA AURORA PREVIEW] SISTEMA 2 — Llamada 1: Portrait del niño | "
                      f"age={child_age} range={nophoto_range_key} display={nophoto_profile['display']}")
                portrait_url_s2 = generate_with_flux2_dev(
                    ca_portrait_prompt,
                    aspect_ratio="3:4",
                    photo_ref_paths=None,
                    negative_prompt=ca_portrait_neg,
                    high_quality=True
                )
                nophoto_portrait_path = save_image_locally(
                    portrait_url_s2, f'{output_dir}/ca_portrait_{uuid.uuid4().hex[:8]}.png'
                )
                print(f"[CENTINELA AURORA PREVIEW] SISTEMA 2 — Portrait guardado: {nophoto_portrait_path}")

            # ── Llamada 2: Portada (portrait @image1 + ASTRO @image2) ─────────
            ca_nophoto_cover_ref = ca_build_ref_note(
                nophoto_profile['display'], gender_word, nophoto_profile['cover_ref'], eye_desc, outfit_desc
            )
            ca_nophoto_cover_scene = CA_FRONT_COVER.get('prompt', '').replace('{style}', AURORA_STYLE_BASE_COVER)
            ca_nophoto_cover_prompt = f"{ca_nophoto_cover_ref}\n{ca_nophoto_cover_scene}"
            cover_refs_s2 = [nophoto_portrait_path, astro_path] if astro_ok else [nophoto_portrait_path]

            ca_nophoto_cover_neg = ca_neg + ", two tails, multiple tails, double tail, split tail, extra tail"
            print(f"[CENTINELA AURORA PREVIEW] SISTEMA 2 — Llamada 2: Portada (portrait + ASTRO)")
            cov_url = generate_with_flux2_dev(
                ca_nophoto_cover_prompt,
                aspect_ratio="3:4",
                photo_ref_paths=cover_refs_s2,
                image_prompt_strength=0.95,
                negative_prompt=ca_nophoto_cover_neg,
                force_go_fast=False,
            )

        cover_path = save_image_locally(cov_url, f'{output_dir}/ca_cover_{uuid.uuid4().hex[:8]}.png')
        print(f"[CENTINELA AURORA PREVIEW] Cover scene generated: {cover_path}")
        result = {
            'success': True,
            'image_url': f'/{cover_path}',
            'story_id': story_id,
            'child_age': child_age
        }
        # SISTEMA 1 (con foto): avatar FLUX (Paso 2) → fluye a character_preview → @image1 en escenas
        if human_photo_path and os.path.exists(human_photo_path) and 'avatar_path' in dir():
            result['kontext_portrait'] = f'/{avatar_path}'
        # SISTEMA 2 (sin foto): portrait de FLUX → fluye a character_preview → @image1 en escenas
        # Usa el mismo key 'kontext_portrait' para que el pipeline de app.py lo recoja sin cambios
        elif 'nophoto_portrait_path' in dir() and nophoto_portrait_path and os.path.exists(nophoto_portrait_path):
            result['kontext_portrait'] = f'/{nophoto_portrait_path}'
            result['nophoto_portrait'] = f'/{nophoto_portrait_path}'  # key semántico para diagnóstico
        return result

    elif story_id in ('furry_love_illustrated', 'furry_love_adventure_illustrated', 'furry_love_teen_illustrated', 'furry_love_adult_illustrated'):
        if story_id == 'furry_love_adventure_illustrated':
            from services.personalized_books.furry_love_adventure_prompts import (
                build_human_preview_prompt, build_pet_preview_prompt,
                build_human_preview_prompt_with_photo, build_pet_preview_prompt_with_photo,
                ADVENTURE_OUTFIT_BOY, ADVENTURE_OUTFIT_GIRL
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
            _gender_word_for_outfit = "girl" if gender == "female" else "boy"
            human_prompt = build_human_preview_prompt(human_desc, is_baby=_is_baby_no_photo, gender_word=_gender_word_for_outfit)
        
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
                    f"Preserve the exact face, hair, and skin tone of the baby — identical likeness. "
                    f"Change the baby's eye color to {eye_desc}, regardless of the baby's actual eye color in @image1. "
                    f"OUTFIT: change the baby's clothing to a soft sage-green baby romper with small leaf print, no text on clothing, regardless of what the baby is wearing in @image1. "
                    f"BACKGROUND: soft cream gradient, plain studio. "
                    f"POSE: baby sitting on the floor, facing camera, warm happy smiling expression, full body visible from head to bare feet, natural baby proportions, face and body balanced."
                )
            elif story_id == 'furry_love_teen_illustrated':
                # Teen — same minimal @image1 approach as baby and adventure: let Kontext read the photo directly
                kontext_prompt = (
                    f"Convert the {age_display} {gender_word} in @image1 into a high-quality 3D animated children's book character. "
                    f"Preserve the exact face, skin tone, and hair — identical likeness. "
                    f"Change their eye color to {eye_desc}, regardless of their actual eye color in @image1. "
                    f"OUTFIT: change their clothing to a casual hoodie and jeans, sneakers — modern teen style, regardless of what they are wearing in @image1. "
                    f"BACKGROUND: soft cream gradient, plain studio. "
                    f"POSE: standing, full body visible from head to feet, confident friendly smile, arms relaxed at sides."
                )
            elif story_id == 'furry_love_adult_illustrated':
                # Adult — mountain adventure story. Minimalist: let Kontext read @image1 directly.
                kontext_prompt = (
                    f"Convert the {age_display} {gender_word} in @image1 into a high-quality 3D animated storybook character. "
                    f"Preserve the exact face, hair color, skin tone, and age from the photo — identical adult likeness. "
                    f"Change their eye color to {eye_desc}, regardless of their actual eye color in @image1. "
                    f"OUTFIT: change their clothing to casual outdoor hiking clothes (flannel shirt or fleece, cargo pants, hiking boots), regardless of what they are wearing in @image1. "
                    f"BACKGROUND: soft cream gradient, plain studio. "
                    f"POSE: standing, full body visible from head to feet, relaxed confident smile, arms naturally at sides."
                )
            else:
                # Kids (3-8 años) — Furry Love Adventure: use the SAME adventure outfit worn in every
                # scene, so preview/cover/scenes never diverge into a random generic outfit.
                _adv_outfit_k = ADVENTURE_OUTFIT_GIRL if gender == "female" else ADVENTURE_OUTFIT_BOY
                kontext_prompt = (
                    f"Convert the {age_display} {gender_word} in @image1 into a high-quality 3D animated children's book character. "
                    f"Preserve the exact face, skin tone, and hair — identical likeness. "
                    f"Change their eye color to {eye_desc}, regardless of their actual eye color in @image1. "
                    f"OUTFIT: change their clothing to {_adv_outfit_k}, regardless of what they are wearing in @image1. "
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
