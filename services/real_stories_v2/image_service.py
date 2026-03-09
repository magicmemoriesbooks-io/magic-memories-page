# Tú y tu Amor Peludo - Image Service
# FLUX 2 Dev with reference images for character consistency
# Supports TWO reference images: human + pet

import os
import replicate
import requests
import uuid
from typing import Dict, List, Optional
from datetime import datetime

FLUX_2_DEV_MODEL = "black-forest-labs/flux-2-dev"

def generate_character_preview(prompt: str, output_folder: str = "static/uploads") -> Dict:
    """Generate a character preview using FLUX 2 Dev (no reference, first generation)."""

    try:
        output = replicate.run(
            FLUX_2_DEV_MODEL,
            input={
                "prompt": prompt,
                "guidance": 3.5,
                "steps": 28,
                "aspect_ratio": "3:4",
                "safety_tolerance": 2,
                "output_format": "jpg"
            }
        )

        if output:
            image_url = output if isinstance(output, str) else str(output)

            filename = f"preview_{uuid.uuid4().hex[:8]}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
            filepath = os.path.join(output_folder, filename)

            os.makedirs(output_folder, exist_ok=True)

            response = requests.get(image_url)
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    f.write(response.content)

                return {
                    'success': True,
                    'image_path': f"/static/uploads/{filename}",
                    'local_path': filepath,
                    'image_url': image_url
                }

        return {
            'success': False,
            'error': 'No image generated'
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def generate_scene_with_references(prompt: str,
                                    reference_images: List[str],
                                    output_folder: str = "static/uploads",
                                    add_watermark: bool = True) -> Dict:
    """Generate a scene using FLUX 2 Dev with one or two reference images.
    
    Args:
        prompt: Scene prompt text
        reference_images: List of local file paths for reference images (human, pet)
        output_folder: Where to save output
        add_watermark: Whether to add PREVIEW watermark
    """
    
    if not reference_images:
        raise ValueError("At least one reference image is required")

    valid_refs = [r for r in reference_images if r and os.path.exists(r)]
    if not valid_refs:
        raise ValueError("No valid reference images found")

    ref_note_parts = []
    if len(valid_refs) >= 1:
        ref_note_parts.append("CRITICAL: Keep the SAME human appearance as the first reference image - same face, same skin tone, same hair.")
    if len(valid_refs) >= 2:
        ref_note_parts.append("CRITICAL: Keep the SAME dog appearance as the second reference image - same breed, same fur color, same markings.")
    
    enhanced_prompt = f"{prompt}\n{' '.join(ref_note_parts)}"

    try:
        input_params = {
            "prompt": enhanced_prompt,
            "guidance": 3.5,
            "steps": 28,
            "aspect_ratio": "3:4",
            "safety_tolerance": 2,
            "output_format": "jpg"
        }

        ref_files = []
        for ref_path in valid_refs:
            ref_files.append(open(ref_path, "rb"))

        if len(ref_files) == 1:
            input_params["image"] = ref_files[0]
        elif len(ref_files) >= 2:
            input_params["image"] = ref_files[0]
            input_params["image2"] = ref_files[1]

        output = replicate.run(FLUX_2_DEV_MODEL, input=input_params)

        for f in ref_files:
            f.close()

        if output:
            image_url = output if isinstance(output, str) else str(output)

            suffix = "_preview" if add_watermark else ""
            filename = f"scene_{uuid.uuid4().hex[:8]}_{datetime.now().strftime('%Y%m%d%H%M%S')}{suffix}.jpg"
            filepath = os.path.join(output_folder, filename)

            os.makedirs(output_folder, exist_ok=True)

            response = requests.get(image_url)
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    f.write(response.content)

                if add_watermark:
                    add_preview_watermark(filepath)

                return {
                    'success': True,
                    'image_path': f"/static/uploads/{filename}",
                    'local_path': filepath,
                    'image_url': image_url
                }

        return {
            'success': False,
            'error': 'No image generated'
        }

    except Exception as e:
        for f in ref_files:
            try:
                f.close()
            except:
                pass
        return {
            'success': False,
            'error': str(e)
        }


def add_preview_watermark(image_path: str):
    """Add a large diagonal white PREVIEW watermark to images."""
    try:
        from PIL import Image, ImageDraw, ImageFont

        img = Image.open(image_path).convert('RGBA')
        width, height = img.size

        watermark = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(watermark)

        font_size = int(min(width, height) / 6)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
        except:
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
            except:
                font = ImageFont.load_default()

        text = "PREVIEW"

        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        txt_img = Image.new('RGBA', (text_width + 40, text_height + 40), (0, 0, 0, 0))
        txt_draw = ImageDraw.Draw(txt_img)
        txt_draw.text((20, 20), text, font=font, fill=(255, 255, 255, 200))

        rotated = txt_img.rotate(30, expand=True, resample=Image.BICUBIC)

        paste_x = (width - rotated.width) // 2
        paste_y = (height - rotated.height) // 2

        watermark.paste(rotated, (paste_x, paste_y), rotated)

        result = Image.alpha_composite(img, watermark)
        result = result.convert('RGB')
        result.save(image_path, quality=95)

    except Exception as e:
        print(f"Could not add watermark: {e}")
