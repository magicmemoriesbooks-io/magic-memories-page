import os
import json
import uuid
import shutil
from datetime import datetime, timedelta
import paramiko
from PIL import Image
from io import BytesIO

VPS_HOST = os.environ.get('VPS_HOST', '')
VPS_USER = os.environ.get('VPS_USER', '')
VPS_PASSWORD = os.environ.get('VPS_PASSWORD', '')
VPS_KEY_PATH = os.environ.get('VPS_KEY_PATH', '')
VPS_VISOR_PATH = os.environ.get('VPS_VISOR_PATH', '/var/www/magicmemoriesbooks.com/visor/biblioteca')
LOCAL_VISOR_MODE = os.environ.get('LOCAL_VISOR_MODE', '').lower() in ('true', '1', 'yes')

STORY_MUSIC_MAP = {
    'baby_soft_world': 'nana_bebes.mp3',
    'baby_puppy_love': 'nana_bebes.mp3',
    'baby_bunny_love': 'nana_bebes.mp3',
    'baby_kitty_love': 'nana_bebes.mp3',
    'baby_star_keeper': 'nana_bebes.mp3',
    'baby_sweetdreams': 'nana_dormir_2.mp3',
    'baby_lullaby': 'nana_dormir_2.mp3',
    'kids_adventure': 'fantasia.mp3',
    'kids_magic_garden': 'fantasia.mp3',
    'kids_magic_chef': 'fantasia.mp3',
    'kids_magic_inventor': 'fantasia.mp3',
    'kids_dragon_garden': 'fantasia.mp3',
    'kids_star_keeper': 'fantasia.mp3',
    'birthday_celebration_1_3': 'happy_birthday.mp3',
    'birthday_celebration_4_6': 'happy_birthday.mp3',
    'birthday_celebration_7_9': 'happy_birthday.mp3',
    'furry_love_illustrated': 'nana_bebes.mp3',
    'furry_love_adventure_illustrated': 'fantasia.mp3',
    'furry_love_teen_illustrated': 'aventura_ninos.mp3',
    'furry_love_adult_illustrated': 'aventura_adulto.mp3',
    'dragon_garden': 'fantasia.mp3',
    'magic_chef': 'fantasia.mp3',
    'magic_inventor': 'fantasia.mp3',
    'star_keeper': 'fantasia.mp3',
    'haz_tu_historia': 'para_sonar.mp3',
}

def get_music_for_story(story_data):
    story_id = story_data.get('story_id', '')
    if story_id and story_id in STORY_MUSIC_MAP:
        return STORY_MUSIC_MAP[story_id]
    
    age_range = story_data.get('age_range', '')
    is_birthday = 'birthday' in story_id.lower() if story_id else False
    if is_birthday:
        return 'happy_birthday.mp3'
    
    if age_range in ['0-1', '0-2']:
        return 'nana_bebes.mp3'
    elif age_range in ['3-5', '3-8', '6-8']:
        return 'fantasia.mp3'
    elif age_range in ['10-15']:
        return 'aventura_ninos.mp3'
    elif age_range in ['18-75']:
        return 'aventura_adulto.mp3'
    
    return 'fantasia.mp3'


def generate_book_uuid():
    return str(uuid.uuid4())


def _generate_text_page(output_path, size, bg_color, title_text, title_color,
                        body_text=None, body_color=None, subtitle_text=None,
                        border=False):
    from PIL import ImageDraw, ImageFont

    img = Image.new('RGB', size, bg_color)
    draw = ImageDraw.Draw(img)
    w, h = size

    try:
        title_font = ImageFont.truetype('static/fonts/Nunito-ExtraBold.ttf', int(h * 0.045))
    except:
        title_font = ImageFont.load_default()
    try:
        body_font = ImageFont.truetype('static/fonts/Nunito-SemiBold.ttf', int(h * 0.03))
    except:
        body_font = ImageFont.load_default()
    try:
        sub_font = ImageFont.truetype('static/fonts/Nunito-SemiBold.ttf', int(h * 0.025))
    except:
        sub_font = ImageFont.load_default()

    if border:
        margin = int(w * 0.08)
        draw.rounded_rectangle(
            [margin, margin, w - margin, h - margin],
            radius=12, outline='#D4A574', width=2
        )
        draw.rounded_rectangle(
            [margin + 8, margin + 8, w - margin - 8, h - margin - 8],
            radius=8, outline='#E8C9A0', width=1
        )

    if title_text:
        bbox = draw.textbbox((0, 0), title_text, font=title_font)
        tw = bbox[2] - bbox[0]
        title_y = int(h * 0.35) if not body_text else int(h * 0.25)
        draw.text(((w - tw) / 2, title_y), title_text, fill=title_color, font=title_font)

    if body_text:
        import textwrap
        margin_x = int(w * 0.12)
        max_text_width = w - 2 * margin_x
        raw_lines = body_text.replace('\n', '|').split('|')
        wrapped_lines = []
        for raw_line in raw_lines:
            raw_line = raw_line.strip()
            if not raw_line:
                wrapped_lines.append('')
                continue
            avg_char_width = body_font.getlength('n') if hasattr(body_font, 'getlength') else int(h * 0.015)
            chars_per_line = max(10, int(max_text_width / avg_char_width))
            for wl in textwrap.wrap(raw_line, width=chars_per_line):
                wrapped_lines.append(wl)
        
        line_h = int(h * 0.04)
        total_text_height = len(wrapped_lines) * line_h
        start_y = int(h * 0.45)
        if total_text_height > h * 0.45:
            start_y = int(h * 0.35)
        
        for j, line in enumerate(wrapped_lines):
            if not line:
                continue
            bbox = draw.textbbox((0, 0), line, font=body_font)
            lw = bbox[2] - bbox[0]
            x = max(margin_x, (w - lw) / 2)
            draw.text((x, start_y + j * line_h), line,
                      fill=body_color or '#4A3728', font=body_font)

    if subtitle_text:
        bbox = draw.textbbox((0, 0), subtitle_text, font=sub_font)
        sw = bbox[2] - bbox[0]
        draw.text(((w - sw) / 2, int(h * 0.62)), subtitle_text,
                  fill='#4A3728', font=sub_font)

    img.save(output_path, 'JPEG', quality=90)


def _resolve_image(path):
    if not path:
        return None
    clean = path.lstrip('/')
    return clean if os.path.exists(clean) else None


def _get_cover_for_visor(story_data, is_illustrated):
    if is_illustrated:
        for key in ['front_cover_path', 'cover_preview', 'cover_raw_path']:
            resolved = _resolve_image(story_data.get(key, ''))
            if resolved:
                return resolved
    for key in ['original_cover', 'cover_image', 'cover_preview']:
        resolved = _resolve_image(story_data.get(key, ''))
        if resolved:
            return resolved
    return None


def _get_scene_images(story_data):
    composed = story_data.get('composed_pages') or []
    if composed:
        return composed
    return story_data.get('original_images') or story_data.get('images') or story_data.get('original_scene_paths') or []


def _get_back_cover(story_data, is_illustrated):
    back = _resolve_image(story_data.get('back_cover_path', ''))
    if back:
        return back
    if is_illustrated:
        fallback = 'static/images/fixed_pages/back_cover.png'
    else:
        fallback = 'static/images/quick_story_back_cover.png'
    if os.path.exists(fallback):
        return fallback
    for candidate in ['static/images/quick_story_back_cover.png', 'static/images/fixed_pages/back_cover.png']:
        if os.path.exists(candidate):
            return candidate
    return None


def _get_scene_text(story_data, text_idx):
    pages_data = story_data.get('pages', [])
    if pages_data and text_idx < len(pages_data):
        return pages_data[text_idx].get('text', '')
    scenes = story_data.get('scenes', [])
    if scenes and text_idx < len(scenes):
        return scenes[text_idx].get('text', '') or scenes[text_idx].get('text_es', '')
    texts = story_data.get('texts', [])
    if texts and text_idx < len(texts):
        return texts[text_idx]
    return ''


def prepare_book_for_visor(story_data, preview_id, book_uuid=None, is_gift=False):
    if not book_uuid:
        book_uuid = generate_book_uuid()

    is_illustrated = story_data.get('is_illustrated_book', False)
    visor_type = 'visor_pb' if is_illustrated else 'visor_qs'

    child_name = story_data.get('child_name', '')
    story_name = story_data.get('story_name', '')
    language = story_data.get('lang', 'es')
    dedication = story_data.get('dedication', '')
    if not dedication:
        dedication = f'Para {child_name},\ncon todo nuestro amor.' if language == 'es' else f'For {child_name},\nwith all our love.'

    front_cover = _get_cover_for_visor(story_data, is_illustrated)
    scene_images = _get_scene_images(story_data)
    closing_image = _resolve_image(story_data.get('closing_image', ''))
    back_cover = _get_back_cover(story_data, is_illustrated)
    closing_message = story_data.get('closing_message', '')

    local_dir = f'generations/{visor_type}/{book_uuid}'
    os.makedirs(local_dir, exist_ok=True)

    print(f"[VISOR-{visor_type.upper()}] Preparing {preview_id}: cover={front_cover}, scenes={len(scene_images)}")

    ref_size = (1024, 1024)
    if front_cover:
        try:
            ref_size = Image.open(front_cover).size
        except:
            pass

    pages = []
    page_num = 0

    def add_image_page(img_path, text='', narration=''):
        nonlocal page_num
        clean_path = img_path.lstrip('/')
        if not os.path.exists(clean_path):
            print(f"[VISOR] Image not found: {clean_path}")
            return
        page_num += 1
        output_filename = f'page_{page_num}.jpg'
        output_path = os.path.join(local_dir, output_filename)
        try:
            img = Image.open(clean_path)
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            img.save(output_path, 'JPEG', quality=85, optimize=True)
        except Exception as e:
            print(f"[VISOR] Error converting image {clean_path}: {e}")
            return
        page_entry = {'image': output_filename, 'text': text}
        if narration:
            page_entry['narration'] = narration
        pages.append(page_entry)

    def add_text_page(filename, **kwargs):
        nonlocal page_num
        page_num += 1
        output_path = os.path.join(local_dir, filename)
        _generate_text_page(output_path, ref_size, **kwargs)
        pages.append({'image': filename, 'text': ''})

    if front_cover:
        add_image_page(front_cover)

    ded_title = "Dedicatoria" if language == 'es' else "Dedication"
    add_text_page(f'page_{page_num + 1}.jpg',
                  bg_color='#FFFBF5', title_text=ded_title, title_color='#8B6914',
                  body_text=dedication, body_color='#4A3728', border=True)

    add_text_page(f'page_{page_num + 1}.jpg',
                  bg_color='#FFFBF5', title_text=story_name, title_color='#8B6914',
                  subtitle_text='Magic Memories Books')

    text_composed = story_data.get('qs_text_composed', False)

    text_idx = 0
    for img_path in scene_images:
        if not img_path or img_path == front_cover:
            continue
        if '_preview' in str(img_path):
            continue
        raw_text = _get_scene_text(story_data, text_idx)
        text_idx += 1
        if is_illustrated or text_composed:
            add_image_page(img_path, narration=raw_text)
        else:
            add_image_page(img_path, text=raw_text)

    if closing_image:
        if text_composed:
            add_image_page(closing_image, narration=closing_message)
        else:
            add_image_page(closing_image, closing_message)

    if back_cover:
        add_image_page(back_cover)

    aspect_ratio = 1.0
    if len(pages) > 3:
        scene_page = os.path.join(local_dir, 'page_4.jpg')
        if not os.path.exists(scene_page):
            scene_page = os.path.join(local_dir, 'page_3.jpg')
    else:
        scene_page = os.path.join(local_dir, 'page_1.jpg')
    if os.path.exists(scene_page):
        try:
            img = Image.open(scene_page)
            aspect_ratio = round(img.width / img.height, 4)
        except:
            pass

    safe_name = child_name.replace(' ', '_').replace("'", "")
    pdf_filename = None
    pdf_digital_path = f'generations/email/{preview_id}/{safe_name}_digital.pdf'
    if os.path.exists(pdf_digital_path):
        pdf_filename = 'original.pdf'
        try:
            import shutil
            shutil.copy2(pdf_digital_path, os.path.join(local_dir, pdf_filename))
        except Exception as e:
            print(f"[VISOR] Error copying PDF: {e}")
            pdf_filename = None

    music_file = story_data.get('visor_music', None) or get_music_for_story(story_data)

    expires_at = None
    if is_gift:
        expiry_days = int(os.environ.get('EBOOK_EXPIRY_DAYS', '180'))
        expires_at = (datetime.now() + timedelta(days=expiry_days)).isoformat()

    site_domain = os.environ.get('SITE_DOMAIN', 'magicmemoriesbooks.com')
    site_url = f'https://{site_domain}'

    metadata = {
        'title': story_name,
        'child_name': child_name,
        'language': language,
        'pages': pages,
        'aspect_ratio': aspect_ratio,
        'visor_type': visor_type,
        'download_pdf': pdf_filename,
        'music': music_file,
        'created': preview_id,
        'expires_at': expires_at,
        'is_gift': is_gift,
        'site_url': site_url,
        'is_birthday': 'birthday' in story_data.get('story_id', '').lower(),
        'created_date': datetime.now().isoformat()
    }

    metadata_path = os.path.join(local_dir, 'metadata.json')
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print(f"[VISOR-{visor_type.upper()}] Ready: {local_dir} ({len(pages)} pages, ar={aspect_ratio})")
    return book_uuid, local_dir


def _copy_visor_local(book_uuid, local_dir):
    dest_dir = os.path.join(VPS_VISOR_PATH, book_uuid)
    try:
        os.makedirs(dest_dir, exist_ok=True)
        for filename in os.listdir(local_dir):
            src = os.path.join(local_dir, filename)
            dst = os.path.join(dest_dir, filename)
            shutil.copy2(src, dst)
        print(f"[VISOR] LOCAL MODE: copiado a {dest_dir} ({len(os.listdir(local_dir))} archivos)")
        return True
    except Exception as e:
        print(f"[VISOR] LOCAL MODE: error al copiar a {dest_dir}: {e}")
        return False


def upload_to_vps(book_uuid, local_dir):
    if LOCAL_VISOR_MODE:
        print(f"[VISOR] LOCAL MODE activo - copiando sin SFTP")
        return _copy_visor_local(book_uuid, local_dir)

    if not VPS_HOST or not VPS_USER:
        print("[VISOR] VPS credentials not configured - usando copia local como fallback")
        return _copy_visor_local(book_uuid, local_dir)

    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        connect_kwargs = {
            'hostname': VPS_HOST,
            'username': VPS_USER,
            'port': int(os.environ.get('VPS_PORT', 22))
        }

        if VPS_KEY_PATH and os.path.exists(VPS_KEY_PATH):
            connect_kwargs['key_filename'] = VPS_KEY_PATH
        elif VPS_PASSWORD:
            connect_kwargs['password'] = VPS_PASSWORD
        else:
            print("[VISOR] No VPS authentication method configured - usando copia local como fallback")
            return _copy_visor_local(book_uuid, local_dir)

        ssh.connect(**connect_kwargs)
        sftp = ssh.open_sftp()

        remote_dir = f'{VPS_VISOR_PATH}/{book_uuid}'

        try:
            sftp.mkdir(remote_dir)
        except IOError:
            pass

        for filename in os.listdir(local_dir):
            local_file = os.path.join(local_dir, filename)
            remote_file = f'{remote_dir}/{filename}'
            sftp.put(local_file, remote_file)
            print(f"[VISOR] SFTP subido: {filename}")

        sftp.close()
        ssh.close()
        print(f"[VISOR] SFTP completo: {remote_dir}")
        return True

    except Exception as e:
        print(f"[VISOR] SFTP fallido: {e} - intentando copia local como fallback")
        return _copy_visor_local(book_uuid, local_dir)


def _get_visor_base_url(visor_type='visor'):
    replit_domain = os.environ.get('REPLIT_DEV_DOMAIN', '')
    if replit_domain:
        return f'https://{replit_domain}/{visor_type}'
    site_domain = os.environ.get('SITE_DOMAIN', 'magicmemoriesbooks.com')
    return f'https://{site_domain}/{visor_type}'


def prepare_and_upload(story_data, preview_id, is_gift=False):
    book_uuid, local_dir = prepare_book_for_visor(story_data, preview_id, book_uuid=preview_id, is_gift=is_gift)

    is_illustrated = story_data.get('is_illustrated_book', False)
    visor_type = 'visor_pb' if is_illustrated else 'visor_qs'

    uploaded = upload_to_vps(book_uuid, local_dir)

    visor_base = _get_visor_base_url(visor_type)
    visor_url = f'{visor_base}/?id={book_uuid}'

    if not uploaded:
        print(f"[VISOR] Upload skipped - manual upload needed from: {local_dir}")
        print(f"[VISOR] Local visor URL: {visor_url}")

    return {
        'book_uuid': book_uuid,
        'local_dir': local_dir,
        'visor_url': visor_url,
        'uploaded': uploaded,
        'is_gift': is_gift
    }
