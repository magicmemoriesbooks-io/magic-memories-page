# Quick Stories PDF Generation
# Digital PDFs + Lulu print PDFs for all quick stories

from io import BytesIO
from PIL import Image


def generate_quick_story_pdf(story_data: dict, output_path: str = None) -> str:
    """
    Generate digital PDF for Quick Stories.
    
    Baby books (0-2): 12 pages, 8.5"x8.5" full-page illustrations with text overlay (cover, title, dedication, 8 scenes, back cover)
    Kids books (3-8): 8.5"x8.5" square, 7 scenes with split text overlay (text above + below illustration)
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
        return create_baby_quick_story_pdf(story_data, images, output_path, format_type='digital', skip_sanitize=True)
    else:
        return create_kids_quick_story_pdf(story_data, images, output_path, format_type='digital', skip_sanitize=True)


def generate_quick_story_lulu_pdfs(story_data: dict, images: list, 
                                    front_cover_path: str, back_cover_path: str,
                                    interior_output: str, cover_output: str,
                                    skip_sanitize: bool = False) -> tuple:
    """
    Generate Lulu-ready PDFs for Quick Story saddle stitch printing.
    8.5" x 8.5" (21.59cm) square format.
    
    Baby (0-2): Uses new full-page illustration layout with text overlay
    Kids (3-8): Uses existing layout
    
    Returns: (interior_path, cover_path)
    """
    from services.pdf_service import (
        create_baby_quick_story_pdf,
        create_kids_quick_story_pdf,
        create_quick_story_lulu_cover,
        QUICK_STORY_BACK_COVER
    )
    
    age_range = story_data.get('age_range', '0-2')
    is_baby = age_range in ['0-1', '0-2']
    
    if is_baby:
        interior_path = create_baby_quick_story_pdf(
            story_data, images, interior_output, 
            format_type='lulu', skip_sanitize=skip_sanitize
        )
    else:
        interior_path = create_kids_quick_story_pdf(
            story_data, images, interior_output,
            format_type='lulu', skip_sanitize=skip_sanitize
        )
    
    if not back_cover_path:
        back_cover_path = QUICK_STORY_BACK_COVER
    
    title = story_data.get('story_name', '')
    author = story_data.get('author_name') or story_data.get('author', '')
    cover_path = create_quick_story_lulu_cover(
        front_cover_path, back_cover_path, cover_output, 
        skip_sanitize=skip_sanitize, title=title, author=author
    )
    
    return interior_path, cover_path


def get_quick_story_pdf_config(story_id: str) -> dict:
    """Get PDF configuration for a quick story."""
    from .stories import QUICK_STORIES
    
    story = QUICK_STORIES.get(story_id, {})
    age_range = story.get('age_range', '0-2')
    is_baby = age_range in ['0-1', '0-2']
    
    if is_baby:
        return {
            'format': 'quick_story_baby',
            'digital_size': '8.5x8.5in',
            'lulu_size': '8.5x8.5in',
            'lulu_binding': 'saddle_stitch',
            'lulu_pod_package_id': '0850X0850FCPRESS080CW444GXX',
            'total_pages': 12,
            'interior_pages': 10,
            'content_scenes': 8,
            'fin_page': False,
            'structure': 'cover, title_page, dedication, (illus+text)x8, back_cover',
            'resolution': 300
        }
    
    return {
        'format': 'quick_story_kids',
        'digital_size': '8.5x8.5in',
        'lulu_size': '8.5x8.5in',
        'lulu_binding': 'saddle_stitch',
        'lulu_pod_package_id': '0850X0850FCPRESS080CW444GXX',
        'total_pages': 12,
        'interior_pages': 10,
        'content_scenes': 7,
        'structure': 'cover, blank, dedication, (illus_with_split_text)x7, blank, back_cover',
        'resolution': 300
    }
