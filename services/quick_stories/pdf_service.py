# Quick Stories PDF Generation
# Digital PDFs + Cloudprinter print PDFs for all quick stories

from io import BytesIO
from PIL import Image


def generate_quick_story_pdf(story_data: dict, output_path: str = None, print_format: str = 'A4') -> str:
    """
    Generate printable PDF for Quick Stories (home printing / copy shop).

    Baby books (0-2): 16 pages, A4 or Letter portrait with bleed.
    Kids books (3-8): 16 pages, A4 or Letter portrait with bleed.
    Birthday books: dispatched as baby or kids based on age_range.

    print_format: 'A4' (default) or 'LETTER' (US/LATAM)
    """
    from services.pdf_service import (
        create_baby_quick_story_pdf,
        create_kids_quick_story_pdf
    )

    story_id = story_data.get('story_id', '')
    age_range = story_data.get('age_range', '0-2')

    is_baby = age_range in ['0-1', '0-2']

    images = story_data.get('scene_images', [])
    if not images:
        images = story_data.get('scene_paths', [])
    if not images:
        images = story_data.get('images', [])
    if not images:
        images = story_data.get('original_images', [])
    if not images:
        images = [p.get('image_path', '') for p in story_data.get('pages', []) if p.get('image_path')]

    images = [img.lstrip('/') if img else '' for img in images]
    images = [img for img in images if img]

    if is_baby:
        return create_baby_quick_story_pdf(
            story_data, images, output_path,
            format_type='cloudprinter', print_format=print_format, skip_sanitize=True,
            draw_trim_marks=True
        )
    else:
        return create_kids_quick_story_pdf(
            story_data, images, output_path,
            format_type='cloudprinter', print_format=print_format, skip_sanitize=True,
            draw_trim_marks=True
        )


def generate_quick_story_cloudprinter_pdf(
    story_data: dict,
    images: list,
    front_cover_path: str,
    output_path: str,
    back_cover_path: str = None,
    skip_sanitize: bool = False
) -> str:
    """
    Generate a 16-page A4 portrait PDF for Cloudprinter saddle-stitch printing.
    Product: magazine_sas_a4_p_fc — Trim 210×297mm + 3mm bleed each side.

    This function always generates A4 (Cloudprinter spec). Do NOT pass print_format here.
    """
    import os
    from services.pdf_service import (
        create_baby_quick_story_pdf,
        create_kids_quick_story_pdf,
    )

    age_range = story_data.get('age_range', '0-2')
    is_baby = age_range in ['0-1', '0-2']

    enriched = dict(story_data)
    if front_cover_path and os.path.exists(front_cover_path):
        enriched['cover_image'] = front_cover_path
    if back_cover_path and os.path.exists(back_cover_path):
        enriched['cp_back_cover_override'] = back_cover_path

    if is_baby:
        create_baby_quick_story_pdf(
            enriched, images, output_path,
            format_type='cloudprinter', print_format='A4', skip_sanitize=skip_sanitize,
            draw_trim_marks=False
        )
    else:
        create_kids_quick_story_pdf(
            enriched, images, output_path,
            format_type='cloudprinter', print_format='A4', skip_sanitize=skip_sanitize,
            draw_trim_marks=False
        )

    print(f"[CP-PDF] 16-page A4 PDF generated: {output_path}")
    return output_path



def get_quick_story_pdf_config(story_id: str) -> dict:
    """Get PDF configuration for a quick story."""
    from .stories import QUICK_STORIES

    story = QUICK_STORIES.get(story_id, {})
    age_range = story.get('age_range', '0-2')
    is_baby = age_range in ['0-1', '0-2']

    if is_baby:
        return {
            'format': 'quick_story_baby',
            'product_id': 'magazine_sas_a4_p_fc',
            'print_size': '210x297mm',
            'print_binding': 'saddle_stitch',
            'print_provider': 'cloudprinter',
            'total_pages': 16,
            'interior_pages': 14,
            'content_scenes': 8,
            'fin_page': False,
            'structure': 'cover, blank, portadilla, dedication, (illus+text)x8, drawing_page, drawing_page, blank, back_cover',
            'resolution': 300
        }

    return {
        'format': 'quick_story_kids',
        'product_id': 'magazine_sas_a4_p_fc',
        'print_size': '210x297mm',
        'print_binding': 'saddle_stitch',
        'print_provider': 'cloudprinter',
        'total_pages': 16,
        'interior_pages': 14,
        'content_scenes': 7,
        'structure': 'cover, blank, portadilla, dedication, (illus_with_split_text)x7, closing, drawing_page, drawing_page, blank, back_cover',
        'resolution': 300
    }
