# Personalized Books Full Generation
# Generates all pages with watermarks before payment

import os
import uuid
from PIL import Image


def generate_full_book_preview(book_id: str, child_name: str, gender: str, 
                                traits: dict, language: str = 'es',
                                dedication_text: str = '',
                                author_name: str = 'Magic Memories Books') -> dict:
    """
    Generate complete personalized book with watermarked previews.
    Called BEFORE payment to show customer all illustrations.
    
    Returns:
        dict with 'preview_pages' (watermarked), 'original_pages' (clean),
        'cover_preview', 'original_cover', and paths
    """
    from services.illustrated_book_service import generate_full_book, add_watermark
    
    output_dir = f'generated/personalized_{uuid.uuid4().hex[:8]}'
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"[PERSONALIZED BOOK] Generating full preview for {book_id}")
    print(f"[PERSONALIZED BOOK] Child: {child_name}, Gender: {gender}")
    
    pages, _failed = generate_full_book(
        book_id=book_id,
        child_name=child_name,
        traits=traits,
        gender=gender,
        language=language,
        dedication_text=dedication_text,
        for_print=True,
        author_name=author_name
    )
    
    print(f"[PERSONALIZED BOOK] Generated {len(pages)} pages")
    
    original_paths = []
    preview_paths = []
    
    for i, page in enumerate(pages):
        original_path = os.path.join(output_dir, f'page_{i+1:02d}.png')
        page.save(original_path, 'PNG')
        original_paths.append(original_path)
        
        preview_path = os.path.join(output_dir, f'page_{i+1:02d}_preview.png')
        watermarked = add_watermark(page)
        watermarked.save(preview_path, 'PNG')
        preview_paths.append(preview_path)
        
        print(f"[PERSONALIZED BOOK] Page {i+1}: saved original + watermarked")
    
    from services.illustrated_book_service import generate_cover_spread
    from PIL import Image
    
    print(f"[PERSONALIZED BOOK] Generating cover spread...")
    cover_spread = generate_cover_spread(traits, child_name, gender, language, book_id, author_name)
    
    DPI = 300
    MM_TO_INCH = 1 / 25.4
    wrap_px = int(19.05 * MM_TO_INCH * DPI)
    board_w_px = int(213.175 * MM_TO_INCH * DPI)
    board_h_px = int(303.35 * MM_TO_INCH * DPI)
    spine_px = int(6.35 * MM_TO_INCH * DPI)

    front_x = wrap_px + board_w_px + spine_px
    front_cover = cover_spread.crop((front_x, wrap_px, front_x + board_w_px, wrap_px + board_h_px))
    back_cover = cover_spread.crop((wrap_px, wrap_px, wrap_px + board_w_px, wrap_px + board_h_px))
    
    logo_path = 'static/images/logo_magic_memories.png'
    if os.path.exists(logo_path):
        logo = Image.open(logo_path).convert('RGBA')
        logo_size = int(back_cover.width * 0.15)
        logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
        
        margin = int(back_cover.width * 0.05)
        logo_x = margin
        logo_y = back_cover.height - logo_size - margin
        
        if back_cover.mode != 'RGBA':
            back_cover = back_cover.convert('RGBA')
        back_cover.paste(logo, (logo_x, logo_y), logo)
        back_cover = back_cover.convert('RGB')
        print(f"[PERSONALIZED BOOK] Logo added to back cover")
    
    original_cover_path = os.path.join(output_dir, 'cover.png')
    front_cover.save(original_cover_path, 'PNG')
    
    cover_preview_path = os.path.join(output_dir, 'cover_preview.png')
    cover_preview = add_watermark(front_cover)
    cover_preview.save(cover_preview_path, 'PNG')
    
    back_cover_path = os.path.join(output_dir, 'back_cover.png')
    back_cover.save(back_cover_path, 'PNG')
    
    back_cover_preview_path = os.path.join(output_dir, 'back_cover_preview.png')
    back_cover_preview = add_watermark(back_cover)
    back_cover_preview.save(back_cover_preview_path, 'PNG')
    
    full_cover_path = os.path.join(output_dir, 'cover_spread.png')
    cover_spread.save(full_cover_path, 'PNG')
    
    print(f"[PERSONALIZED BOOK] Covers saved: front + back + spread")
    
    content_original = original_paths[2:-2] if len(original_paths) > 4 else original_paths
    content_preview = preview_paths[2:-2] if len(preview_paths) > 4 else preview_paths
    
    return {
        'success': True,
        'output_dir': output_dir,
        'all_pages': pages,
        'original_paths': original_paths,
        'preview_paths': preview_paths,
        'content_original': content_original,
        'content_preview': content_preview,
        'cover_path': original_cover_path,
        'cover_preview_path': cover_preview_path,
        'back_cover_path': back_cover_path,
        'back_cover_preview_path': back_cover_preview_path,
        'cover_spread_path': full_cover_path,
        'page_count': len(pages)
    }


def get_personalized_book_id(story_id: str) -> str:
    """Convert story_id to book_id for generation."""
    if 'magic_chef' in story_id:
        return 'magic_chef'
    elif 'magic_inventor' in story_id:
        return 'magic_inventor'
    elif 'star_keeper' in story_id:
        return 'star_keeper'
    elif 'furry_love_teen' in story_id:
        return 'furry_love_teen'
    elif 'furry_love_adult' in story_id:
        return 'furry_love_adult'
    elif 'furry_love_adventure' in story_id:
        return 'furry_love_adventure'
    elif 'furry_love' in story_id:
        return 'furry_love'
    else:
        return 'dragon_garden'


def is_personalized_book(story_id: str) -> bool:
    """Check if story is a personalized illustrated book."""
    return story_id in ['dragon_garden_illustrated', 'magic_chef_illustrated', 'magic_inventor_illustrated', 'star_keeper_illustrated', 'furry_love_illustrated', 'furry_love_adventure_illustrated', 'furry_love_teen_illustrated', 'furry_love_adult_illustrated']


def get_lulu_title(book_id: str, child_name: str, lang: str = 'es', pet_name: str = '') -> str:
    """Get the Lulu book title for a given book_id. Centralized to avoid duplication."""
    if book_id == 'furry_love' and pet_name:
        titles_furry = {
            'es': f"El día que {pet_name} conoció a {child_name}",
            'en': f"The day {pet_name} met {child_name}"
        }
        return titles_furry.get(lang, titles_furry['en'])
    
    if book_id == 'furry_love_adventure' and pet_name:
        titles_adventure = {
            'es': f"Las aventuras de {pet_name} y {child_name}",
            'en': f"The Adventures of {pet_name} and {child_name}"
        }
        return titles_adventure.get(lang, titles_adventure['en'])
    
    if book_id == 'furry_love_teen' and pet_name:
        titles_teen = {
            'es': f"{child_name} y su compañero fiel {pet_name}",
            'en': f"{child_name} and Their Faithful Companion {pet_name}"
        }
        return titles_teen.get(lang, titles_teen['en'])
    
    if book_id == 'furry_love_adult' and pet_name:
        titles_adult = {
            'es': f"La Gran Aventura de {child_name} y {pet_name}",
            'en': f"The Great Adventure of {child_name} and {pet_name}"
        }
        return titles_adult.get(lang, titles_adult['en'])
    
    titles = {
        'magic_chef': {
            'es': f"{child_name} El Chef Mágico",
            'en': f"{child_name} The Magic Chef"
        },
        'magic_inventor': {
            'es': f"El Taller del Inventor Mágico - {child_name}",
            'en': f"The Magic Inventor Workshop - {child_name}"
        },
        'dragon_garden': {
            'es': f"El Jardín del Dragón - {child_name}",
            'en': f"The Dragon's Garden - {child_name}"
        },
        'star_keeper': {
            'es': f"El Guardián de Estrellas - {child_name}",
            'en': f"The Star Keeper - {child_name}"
        },
        'furry_love': {
            'es': f"El día que su Amor Peludo conoció a {child_name}",
            'en': f"The day their Furry Love met {child_name}"
        },
        'furry_love_adventure': {
            'es': f"Las aventuras de su Amor Peludo y {child_name}",
            'en': f"The Adventures of their Furry Love and {child_name}"
        },
        'furry_love_teen': {
            'es': f"{child_name} y su compañero fiel",
            'en': f"{child_name} and Their Faithful Companion"
        }
    }
    book_titles = titles.get(book_id, titles['dragon_garden'])
    return book_titles.get(lang, book_titles['en'])
