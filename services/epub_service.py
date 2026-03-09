"""
ePub Service for Magic Memories Books
Generates real .epub files for children's storybooks
"""

import os
import io
import requests
import tempfile
from ebooklib import epub
from PIL import Image


def create_epub_from_story(story_data: dict, output_path: str = None) -> str:
    """
    Create a real .epub file directly from story_data JSON.
    Handles Quick Stories (baby/kids), personalized books, and furry_love.
    
    Args:
        story_data: The full story JSON data
        output_path: Optional path to save the epub file
    
    Returns:
        Path to the generated epub file
    """
    
    child_name = story_data.get('child_name', 'Mi Pequeño')
    story_name = story_data.get('story_name', 'Mi Cuento Mágico')
    language = story_data.get('language', story_data.get('lang', 'es'))
    dedication = story_data.get('dedication', '')
    is_personalized = story_data.get('is_illustrated_book', False)
    
    cover_image = story_data.get('cover_image', story_data.get('original_cover', story_data.get('cover_preview', '')))
    if cover_image and cover_image.startswith('/'):
        cover_image = cover_image[1:]
    
    pages = story_data.get('pages', [])
    scene_paths = story_data.get('scene_paths', story_data.get('images', story_data.get('original_images', story_data.get('original_scene_paths', []))))
    if not scene_paths:
        scene_paths = []
    scene_paths = [p[1:] if p.startswith('/') else p for p in scene_paths]
    
    closing_image = story_data.get('closing_image', '')
    if closing_image and closing_image.startswith('/'):
        closing_image = closing_image[1:]
    closing_message = story_data.get('closing_message', '')
    
    back_cover_path = story_data.get('back_cover_path', story_data.get('back_cover_preview', ''))
    if back_cover_path and back_cover_path.startswith('/'):
        back_cover_path = back_cover_path[1:]
    if not back_cover_path or not os.path.exists(back_cover_path):
        story_id = story_data.get('story_id', '')
        _fixed_backs = {
            "dragon_garden": "static/images/fixed_pages/dragon_garden_back_cover.png",
            "magic_chef": "static/images/fixed_pages/magic_chef_back_cover.png",
            "magic_inventor": "static/images/fixed_pages/magic_inventor_back_cover.png",
            "star_keeper": "static/images/fixed_pages/star_keeper_back_cover.png",
            "furry_love": "static/images/fixed_pages/furry_love_baby_back_cover.png",
            "furry_love_adventure": "static/images/fixed_pages/furry_love_adventure_back_cover.png",
            "furry_love_teen": "static/images/fixed_pages/furry_love_teen_back_cover.png",
            "furry_love_adult": "static/images/fixed_pages/furry_love_adult_back_cover.png",
        }
        back_cover_path = _fixed_backs.get(story_id, 'static/images/quick_story_back_cover.png')
    
    book = epub.EpubBook()
    
    book.set_identifier(f'magicmemories-{child_name.lower().replace(" ", "-")}-{os.urandom(4).hex()}')
    book.set_title(f'{story_name} - {child_name}')
    book.set_language(language)
    book.add_author('Magic Memories Books')
    book.add_metadata('DC', 'publisher', 'Magic Memories Books')
    if language == 'es':
        book.add_metadata('DC', 'description', f'Un cuento personalizado para {child_name}')
    else:
        book.add_metadata('DC', 'description', f'A personalized story for {child_name}')
    
    style = _get_epub_style()
    nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
    book.add_item(nav_css)
    
    chapters = []
    spine = ['nav']
    
    cover_img_data = _load_image_for_epub(cover_image)
    has_cover = False
    if cover_img_data:
        book.set_cover('cover.jpg', cover_img_data, create_page=False)
        cover_item = epub.EpubItem(uid='cover_image', file_name='images/cover.jpg', media_type='image/jpeg', content=cover_img_data)
        book.add_item(cover_item)
        has_cover = True
    
    cover_html = f'''
    <html xmlns="http://www.w3.org/1999/xhtml">
    <head><title>{"Portada" if language == "es" else "Cover"}</title><link rel="stylesheet" type="text/css" href="style/nav.css"/></head>
    <body style="margin: 0; padding: 0;">
        {f'<img src="images/cover.jpg" alt="Portada" style="width: 100%; height: auto;"/>' if has_cover else ''}
    </body>
    </html>
    '''
    cover_chapter = epub.EpubHtml(title='Portada' if language == 'es' else 'Cover', file_name='title_page.xhtml', lang=language)
    cover_chapter.content = cover_html
    cover_chapter.add_item(nav_css)
    book.add_item(cover_chapter)
    chapters.append(cover_chapter)
    spine.append(cover_chapter)
    
    if dedication:
        ded_title = 'Dedicatoria' if language == 'es' else 'Dedication'
        ded_html = f'''
        <html xmlns="http://www.w3.org/1999/xhtml">
        <head><title>{ded_title}</title><link rel="stylesheet" type="text/css" href="style/nav.css"/></head>
        <body style="margin: 0; padding: 60px 50px; background-color: #fef7ff; text-align: center;">
            <h2 style="color: #ec4899; font-size: 2em; margin-bottom: 30px;">{ded_title}</h2>
            <div style="background: #f3e8ff; border-radius: 16px; padding: 40px 50px; max-width: 70%; margin: 0 auto;">
                <p style="font-family: Georgia, serif; font-style: italic; font-size: 1.3em; color: #333; margin: 0; line-height: 1.8;">{dedication}</p>
            </div>
        </body>
        </html>
        '''
        ded_chapter = epub.EpubHtml(title=ded_title, file_name='dedication.xhtml', lang=language)
        ded_chapter.content = ded_html
        ded_chapter.add_item(nav_css)
        book.add_item(ded_chapter)
        chapters.append(ded_chapter)
        spine.append(ded_chapter)
    
    scene_image_items = []
    for i, img_path in enumerate(scene_paths):
        img_data = _load_image_for_epub(img_path)
        if img_data:
            img_item = epub.EpubItem(uid=f'scene_{i}', file_name=f'images/scene_{i}.jpg', media_type='image/jpeg', content=img_data)
            book.add_item(img_item)
            scene_image_items.append((i, img_item))
    
    for i, img_path in enumerate(scene_paths):
        matching = [item for idx, item in scene_image_items if idx == i]
        if matching:
            page_title = f'Página {i+1}' if language == 'es' else f'Page {i+1}'
            img_html = f'''
            <html xmlns="http://www.w3.org/1999/xhtml">
            <head><title>{page_title}</title><link rel="stylesheet" type="text/css" href="style/nav.css"/></head>
            <body style="margin: 0; padding: 0;">
                <img src="images/scene_{i}.jpg" alt="{page_title}" style="width: 100%; height: auto;"/>
            </body>
            </html>
            '''
            chapter = epub.EpubHtml(title=page_title, file_name=f'page_{i}.xhtml', lang=language)
            chapter.content = img_html
            chapter.add_item(nav_css)
            book.add_item(chapter)
            chapters.append(chapter)
            spine.append(chapter)
    
    if closing_image:
        closing_data = _load_image_for_epub(closing_image)
        if closing_data:
            closing_item = epub.EpubItem(uid='closing_img', file_name='images/closing.jpg', media_type='image/jpeg', content=closing_data)
            book.add_item(closing_item)
            
            closing_html = f'''
            <html xmlns="http://www.w3.org/1999/xhtml">
            <head><title>{"Fin" if language == "es" else "The End"}</title><link rel="stylesheet" type="text/css" href="style/nav.css"/></head>
            <body style="margin: 0; padding: 0;">
                <img src="images/closing.jpg" alt="Closing" style="width: 100%; height: auto;"/>
            </body>
            </html>
            '''
            closing_chapter = epub.EpubHtml(title='Fin' if language == 'es' else 'The End', file_name='closing.xhtml', lang=language)
            closing_chapter.content = closing_html
            closing_chapter.add_item(nav_css)
            book.add_item(closing_chapter)
            chapters.append(closing_chapter)
            spine.append(closing_chapter)
    
    if back_cover_path and os.path.exists(back_cover_path):
        bc_data = _load_image_for_epub(back_cover_path)
        if bc_data:
            bc_item = epub.EpubItem(uid='back_cover_img', file_name='images/back_cover.jpg', media_type='image/jpeg', content=bc_data)
            book.add_item(bc_item)
            
            bc_html = f'''
            <html xmlns="http://www.w3.org/1999/xhtml">
            <head><title>{"Contraportada" if language == "es" else "Back Cover"}</title><link rel="stylesheet" type="text/css" href="style/nav.css"/></head>
            <body style="margin: 0; padding: 0;">
                <img src="images/back_cover.jpg" alt="Back Cover" class="back-cover-image"/>
            </body>
            </html>
            '''
            bc_chapter = epub.EpubHtml(title='Contraportada' if language == 'es' else 'Back Cover', file_name='back_cover.xhtml', lang=language)
            bc_chapter.content = bc_html
            bc_chapter.add_item(nav_css)
            book.add_item(bc_chapter)
            chapters.append(bc_chapter)
            spine.append(bc_chapter)
    
    book.toc = tuple(chapters)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = spine
    
    if output_path is None:
        safe_name = child_name.lower().replace(' ', '_').replace("'", "")
        output_path = os.path.join(tempfile.gettempdir(), f'{safe_name}_story.epub')
    
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    
    epub.write_epub(output_path, book, {})
    
    print(f"[EPUB] Created: {output_path} ({len(chapters)} chapters, {len(scene_image_items)} illustrations)")
    return output_path


def _load_image_for_epub(img_path):
    """Load and process an image for epub."""
    try:
        if not img_path:
            return None
        if img_path.startswith('http'):
            response = requests.get(img_path, timeout=30)
            img_data = response.content
        else:
            if os.path.exists(img_path):
                with open(img_path, 'rb') as f:
                    img_data = f.read()
            else:
                return None
        
        img = Image.open(io.BytesIO(img_data))
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        max_size = (1200, 1600)
        img.thumbnail(max_size, Image.LANCZOS)
        
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='JPEG', quality=85, optimize=True)
        return img_buffer.getvalue()
    except Exception as e:
        print(f"[EPUB] Error processing image {img_path}: {e}")
        return None


def _get_epub_style():
    return '''
    @namespace epub "http://www.idpf.org/2007/ops";
    body {
        font-family: Georgia, serif;
        margin: 5%;
        text-align: center;
        background-color: #fef7ff;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-height: 90vh;
    }
    h1 {
        color: #9333ea;
        font-size: 2em;
        margin-bottom: 0.5em;
        text-align: center;
    }
    h2 {
        color: #ec4899;
        font-size: 1.5em;
        margin-top: 1em;
        text-align: center;
    }
    p {
        font-size: 1.0em;
        line-height: 1.6;
        color: #333;
        margin: 0.8em auto;
        text-align: center;
        max-width: 90%;
    }
    .cover-title {
        font-size: 2.5em;
        color: #9333ea;
        margin-top: 15%;
        text-align: center;
    }
    .cover-subtitle {
        font-size: 1.5em;
        color: #ec4899;
        margin-top: 1em;
        text-align: center;
    }
    .illustration {
        max-width: 100%;
        height: auto;
        margin: 1em auto;
        display: block;
        border-radius: 10px;
    }
    .drop-cap {
        float: left;
        font-size: 2.2em;
        line-height: 0.85;
        font-weight: 800;
        color: #9333ea;
        margin-right: 0.08em;
        padding-top: 0.05em;
    }
    .story-text {
        font-size: 1.1em;
        line-height: 1.7;
        text-align: justify;
        padding: 0.8em;
        margin: 0.5em auto;
        max-width: 90%;
    }
    .back-cover-image {
        width: 100%;
        max-width: 100%;
        height: auto;
        display: block;
        margin: 0 auto;
    }
    '''


def create_epub(story_data: dict, output_path: str = None) -> str:
    """Legacy wrapper - redirects to create_epub_from_story."""
    return create_epub_from_story(story_data, output_path)
