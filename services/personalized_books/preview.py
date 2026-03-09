# Personalized Books Preview Generation
# All books now use FLUX 2 Dev for consistency
# Each book's preview uses the same schema as scenes: CHARACTER → OUTFIT → COMPANION → ACTION → SETTING → ATMOSPHERE → STRICT
# Preview prompts are brief hints (hair_desc, eye_desc, skin_tone) instead of full character base descriptions
# Preview = Front Cover (centered composition for book cover)

import os
import uuid
import time
import replicate
import requests
from io import BytesIO
from PIL import Image

MAX_RETRIES = 5
RETRY_DELAY = 5

RETRYABLE_ERRORS = ['CUDA out of memory', 'GPU', 'ServerError', 'q_descale', 'nsfw', 'NSFW', 'Internal']

PULID_VERSION = "8baa7ef2255075b46f4d91cd238c21d31181b3e6a864463f967960bb0112525b"


def generate_with_flux_pulid(prompt: str, face_image_path: str, width: int = 768, height: int = 1024) -> str:
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with open(face_image_path, "rb") as face_img:
                print(f"[PULID] Calling flux-pulid attempt {attempt}, prompt_len={len(prompt)}")
                output = replicate.run(
                    f"zsxkib/flux-pulid:{PULID_VERSION}",
                    input={
                        "prompt": prompt,
                        "main_face_image": face_img,
                        "id_weight": 1.2,
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
            output = replicate.run(
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


def generate_with_flux2_dev(prompt: str, aspect_ratio: str = "3:4", photo_ref_path: str = None, photo_ref_paths: list = None) -> str:
    """Generate illustration using FLUX 2 Dev (better consistency for series).
    If photo_ref_path is provided, uses it as single input_images reference.
    If photo_ref_paths is provided, uses multiple input_images references (e.g. human + pet)."""
    input_params = {
        "prompt": prompt,
        "aspect_ratio": aspect_ratio,
        "output_format": "png",
        "go_fast": True
    }
    
    if photo_ref_paths:
        valid_paths = [p for p in photo_ref_paths if p and os.path.exists(p)]
        if valid_paths:
            print(f"[PREVIEW] Generating with FLUX 2 Dev + {len(valid_paths)} photo references: {valid_paths}")
            print(f"[PREVIEW] Prompt ({len(prompt)} chars): {prompt[:200]}...")
            input_params["go_fast"] = False
            if len(valid_paths) >= 2:
                anti_blend = "\n@image1=HUMAN ref, @image2=PET ref. Keep each appearance exactly. Human=human only, pet=animal only, TWO separate beings."
                input_params["prompt"] = prompt + anti_blend
            output = _run_replicate_with_retry(input_params, ref_file_paths=valid_paths)
        else:
            print(f"[PREVIEW] Generating with FLUX 2 Dev (no valid photo references)...")
            output = _run_replicate_with_retry(input_params)
    elif photo_ref_path and os.path.exists(photo_ref_path):
        print(f"[PREVIEW] Generating with FLUX 2 Dev + photo reference (input_images): {photo_ref_path}")
        print(f"[PREVIEW] Prompt ({len(prompt)} chars): {prompt[:200]}...")
        input_params["go_fast"] = False
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


def generate_personalized_preview(story_id: str, child_name: str, gender: str,
                                   child_age: int, traits: dict) -> dict:
    """
    Generate character preview for Personalized Books.
    All books now use FLUX 2 Dev with the same schema: CHARACTER → OUTFIT → COMPANION → ACTION → SETTING → ATMOSPHERE → STRICT
    Brief hints only (hair_desc, eye_desc, skin_tone) - no full char_base descriptions
    Preview = Front Cover with centered composition for book cover
    """
    from services.replicate_service import save_image_locally, get_unified_skin_description
    from services.fixed_stories import get_hair_description, get_eye_description
    
    if story_id == 'dragon_garden_illustrated':
        from services.personalized_books.dragon_garden_prompts import (
            get_outfit_desc, STYLE_BASE, SPARK_INLINE, get_hair_action
        )
        
        outfit_desc = get_outfit_desc(gender)
        hair_action = get_hair_action(traits)
        hair_desc = get_hair_description(traits)
        eye_desc = get_eye_description(traits)
        skin_tone = get_unified_skin_description(traits.get('skin_tone', 'light'))
        gender_word = "boy" if gender == "male" else "girl" if gender == "female" else "child"
        age_display = f"{child_age} year old" if child_age and child_age > 0 else "6 year old"
        
        # Use FRONT_COVER schema, adapted for preview context
        prompt = f"Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, big joyful smile, {hair_action}. OUTFIT: {outfit_desc}. COMPANION: {SPARK_INLINE}. ACTION: {gender_word} sits happily on SPARK's back flying through the clouds, arms gently holding the dragon, SPARK's wings spread wide and flapping. SETTING: Beautiful sky WIDE VIEW, fluffy pink and white cotton clouds, magnificent rainbow arching, golden sunlight, sparkles trailing. ATMOSPHERE: Adventure invitation, joyful flight, magical. STRICT: Only ONE {gender_word}, only ONE small dragon SPARK, {gender_word} is 100% human child, no duplicates. ABSOLUTELY NO rendered text anywhere in the image, no titles, no logos, no words, no letters, no captions, no watermarks, no signatures, pure illustration only. {STYLE_BASE}"
        
        print(f"[PERSONALIZED PREVIEW] {story_id}, age={child_age}")
        print(f"[PERSONALIZED PREVIEW] Using FRONT_COVER schema + FLUX 2 Dev")
        
    elif story_id == 'magic_chef_illustrated':
        from services.personalized_books.magic_chef_prompts import (
            get_outfit_desc as chef_get_outfit_desc,
            STYLE_BASE as CHEF_STYLE_BASE,
            SWEETIE_HAT_INLINE,
            SWEETIE_CAKE_INLINE
        )
        
        outfit_desc = chef_get_outfit_desc(gender)
        hair_desc = get_hair_description(traits)
        eye_desc = get_eye_description(traits)
        skin_tone = get_unified_skin_description(traits.get('skin_tone', 'light'))
        gender_word = "boy" if gender == "male" else "girl" if gender == "female" else "child"
        age_display = f"{child_age} year old" if child_age and child_age > 0 else "6 year old"
        
        # Use FRONT_COVER schema, adapted for preview context
        prompt = f"Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, confident joyful smile. OUTFIT: {SWEETIE_HAT_INLINE}, and an elegant white chef jacket with golden buttons. COMPANION: {SWEETIE_CAKE_INLINE}. ACTION: {gender_word} stands in center of magical kitchen, SWEETIE floats happily beside the child. SETTING: Magical pink kitchen WIDE VIEW, sparkles hearts and golden stars, floating magical desserts everywhere, rainbow cakes, glowing star cookies, swirling colorful ice creams, centered composition for book cover. ATMOSPHERE: Sweet magical invitation, pink and golden warmth. STRICT: Only ONE {gender_word}, only ONE cake character SWEETIE, {gender_word} is 100% human child, no duplicates. ABSOLUTELY NO rendered text anywhere in the image, no titles, no logos, no words, no letters, no captions, no watermarks, no signatures, pure illustration only. {CHEF_STYLE_BASE}"
        
        print(f"[PERSONALIZED PREVIEW] {story_id}, age={child_age}")
        print(f"[PERSONALIZED PREVIEW] Using FRONT_COVER schema + FLUX 2 Dev")
        
    elif story_id == 'magic_inventor_illustrated':
        from services.personalized_books.magic_inventor_prompts import (
            get_outfit_desc as inventor_get_outfit_desc,
            STYLE_BASE as INVENTOR_STYLE_BASE,
            BOLT_INLINE as INVENTOR_BOLT_INLINE
        )
        
        outfit_desc = inventor_get_outfit_desc(gender)
        hair_desc = get_hair_description(traits)
        eye_desc = get_eye_description(traits)
        skin_desc = get_unified_skin_description(traits.get('skin_tone', 'light'))
        gender_word = "boy" if gender == "male" else "girl" if gender == "female" else "child"
        age_display = f"{child_age} year old" if child_age and child_age > 0 else "6 year old"
        
        prompt = f"Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_desc} skin, confident joyful smile, holding a glowing wrench. OUTFIT: {outfit_desc}. COMPANION: {INVENTOR_BOLT_INLINE}. ACTION: {gender_word} and BOLT stand together in center of workshop, facing viewer, centered composition for book cover, BOLT waves with one arm, blue eyes bright. SETTING: Magical inventor workshop WIDE VIEW, floating golden gears, crystal tubes with colorful liquids, warm golden light, sparkles. ATMOSPHERE: Adventure invitation, warm golden, friendship and creativity. STRICT: Only ONE {gender_word}, only ONE small robot BOLT, {gender_word} is 100% human child, no duplicates. ABSOLUTELY NO rendered text anywhere in the image, no titles, no logos, no words, no letters, no captions, no watermarks, no signatures, pure illustration only. {INVENTOR_STYLE_BASE}"
        
        print(f"[PERSONALIZED PREVIEW] {story_id}, age={child_age}")
        print(f"[PERSONALIZED PREVIEW] Using FRONT_COVER schema + FLUX 2 Dev")
        
    elif story_id == 'star_keeper_illustrated':
        from services.personalized_books.star_keeper_prompts import (
            get_outfit_desc as keeper_get_outfit_desc,
            STYLE_BASE as KEEPER_STYLE_BASE,
            LUNA_INLINE as KEEPER_LUNA_INLINE,
            get_hair_action
        )
        
        outfit_desc = keeper_get_outfit_desc(gender)
        hair_action = get_hair_action(traits)
        hair_desc = get_hair_description(traits)
        eye_desc = get_eye_description(traits)
        skin_tone = get_unified_skin_description(traits.get('skin_tone', 'light'))
        gender_word = "boy" if gender == "male" else "girl" if gender == "female" else "child"
        age_display = f"{child_age} year old" if child_age and child_age > 0 else "6 year old"
        
        # Use FRONT_COVER schema, adapted for preview context
        prompt = f"Disney Pixar 3D style illustration. CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, big joyful confident smile, one hand reaching toward the stars. OUTFIT: {outfit_desc}. COMPANION: {KEEPER_LUNA_INLINE}. ACTION: {gender_word} stands confidently at the lighthouse entrance, LUNA hovers beside the child's shoulder glowing brightly, violet eyes warm, wings spread wide, comet tail trailing silver sparkles. SETTING: Old stone lighthouse on dramatic clifftop WIDE VIEW, magnificent starry sky with bright constellations and shooting stars, ocean waves crashing below, warm golden-blue light from lighthouse door, centered composition for book cover. ATMOSPHERE: Adventure invitation, celestial magic. STRICT: Only ONE {gender_word}, only ONE small star LUNA, {gender_word} is 100% human child, no duplicates. ABSOLUTELY NO rendered text anywhere in the image, no titles, no logos, no words, no letters, no captions, no watermarks, no signatures, pure illustration only. {KEEPER_STYLE_BASE}"
        
        print(f"[PERSONALIZED PREVIEW] {story_id}, age={child_age}")
        print(f"[PERSONALIZED PREVIEW] Using FRONT_COVER schema + FLUX 2 Dev")
        
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
            human_prompt = build_human_preview_prompt_with_photo(gender_word, age_display, eye_desc, hair_desc, glasses=glasses_val)
        else:
            human_prompt = build_human_preview_prompt(human_desc)
        
        if pet_photo_path:
            pet_prompt = build_pet_preview_prompt_with_photo(pet_desc, pet_species)
        else:
            pet_prompt = build_pet_preview_prompt(pet_desc)
        
        use_pulid = story_id in ('furry_love_teen_illustrated', 'furry_love_adult_illustrated')
        
        if human_photo_path and use_pulid:
            print(f"[FURRY LOVE PREVIEW] Generating human preview WITH photo using FLUX PuLID (face identity): {human_photo_path}")
            try:
                human_url = generate_with_flux_pulid(human_prompt, human_photo_path, width=768, height=1024)
            except Exception as pulid_err:
                print(f"[FURRY LOVE PREVIEW] PuLID failed ({str(pulid_err)[:150]}), falling back to FLUX 2 Dev...")
                human_url = generate_with_flux2_dev(human_prompt, aspect_ratio="3:4", photo_ref_path=human_photo_path)
        elif human_photo_path:
            print(f"[FURRY LOVE PREVIEW] Generating human preview WITH photo using FLUX 2 Dev (reference): {human_photo_path}")
            human_url = generate_with_flux2_dev(human_prompt, aspect_ratio="3:4", photo_ref_path=human_photo_path)
        else:
            print(f"[FURRY LOVE PREVIEW] Generating human preview (no photo)...")
            human_url = generate_with_flux2_dev(human_prompt, aspect_ratio="3:4")
        
        if pet_photo_path:
            print(f"[FURRY LOVE PREVIEW] Generating pet preview WITH photo reference: {pet_photo_path}")
        else:
            print(f"[FURRY LOVE PREVIEW] Generating pet preview (no photo)...")
        pet_url = generate_with_flux2_dev(pet_prompt, aspect_ratio="3:4", photo_ref_path=pet_photo_path or None)
        
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
    
    image_url = generate_with_flux2_dev(prompt, aspect_ratio="3:4")
    
    output_dir = 'generated/previews'
    os.makedirs(output_dir, exist_ok=True)
    local_path = save_image_locally(image_url, f'{output_dir}/preview_{uuid.uuid4().hex[:8]}.png')
    
    return {
        'success': True,
        'image_url': f'/{local_path}',
        'story_id': story_id,
        'child_age': child_age
    }
