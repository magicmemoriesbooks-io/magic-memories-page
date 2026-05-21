"""
Printable PDF Generator for Magic Memories Books
Produces a 28-page A4 (or Letter) PDF suitable for home printing at a copy shop.

Format  : A4 portrait (210 × 297 mm) at 300 DPI  /  US Letter (215.9 × 279.4 mm)
Margins : 10 mm left/right, 12 mm top/bottom (safe print zone)
Content : 190 × 273 mm — images centred inside the safe area

28-page structure (digital edition — portada + contraportada included):
  Page 1     : portada (visor page_1.jpg or front_cover_path)
  Page 2     : blank
  Page 3     : portadilla (visor page_2.jpg)
  Page 4     : dedicatoria (visor page_3.jpg)
  Pages 5-23 : 19 story scenes (visor page_4.jpg … page_22.jpg)
  Pages 24-25: 2 coloring pages (scenes page_8 and page_17 via FLUX Kontext Pro)
  Page 26    : credits (dynamically generated)
  Page 27    : blank
  Page 28    : contraportada fija
                 A4     → FIXED_BACK_COVER_IMAGES  (static/images/fixed_pages/_backup/)
                 Letter → FIXED_BACK_COVER_IMAGES_LETTER (…/backup_PhotoMagic_carta/)

Coloring pages use FLUX Kontext Pro (via _build_qs_cp_a4_drawing_page_image) for clean
black outlines on white, with "¡Dibuja tu propia historia!" header. PIL fallback if FLUX fails.

Output: generated/cloudprinter/<session_id>/<name>_imprimible.pdf
  (served via /preview-pdf/printable/<session_id>/<filename>)
"""

import os
import gc
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

BLEED_MM     = 3.0

# A4 with 3mm bleed (home printing) — Trim: 210×297mm, with bleed: 216×303mm
A4_TRIM_W_MM  = 210
A4_TRIM_H_MM  = 297
A4_WIDTH_MM   = A4_TRIM_W_MM  + 2 * BLEED_MM  # 216mm
A4_HEIGHT_MM  = A4_TRIM_H_MM + 2 * BLEED_MM  # 303mm
A4_DPI        = 300
A4_PX_W       = int(A4_WIDTH_MM  * A4_DPI / 25.4)   # 2551
A4_PX_H       = int(A4_HEIGHT_MM * A4_DPI / 25.4)   # 3579
A4_PT_W       = A4_WIDTH_MM  * 72 / 25.4             # 612.28
A4_PT_H       = A4_HEIGHT_MM * 72 / 25.4             # 858.90

# Safety content margin (bleed + visible margin from trim edge)
_BLEED_PT     = BLEED_MM * 72 / 25.4                 # 8.50 pt
MARGIN_LR_PT  = _BLEED_PT + 10 * 72 / 25.4          # bleed + 10mm = 36.85 pt
MARGIN_TB_PT  = _BLEED_PT + 12 * 72 / 25.4          # bleed + 12mm = 42.52 pt
CONTENT_W_PT  = A4_PT_W - 2 * MARGIN_LR_PT
CONTENT_H_PT  = A4_PT_H - 2 * MARGIN_TB_PT

# US Letter with 3mm bleed — Trim: 215.9×279.4mm, with bleed: 221.9×285.4mm
LETTER_TRIM_W_MM  = 215.9
LETTER_TRIM_H_MM  = 279.4
LETTER_WIDTH_MM   = LETTER_TRIM_W_MM  + 2 * BLEED_MM   # ≈ 221.9mm
LETTER_HEIGHT_MM  = LETTER_TRIM_H_MM + 2 * BLEED_MM   # ≈ 285.4mm
LETTER_PX_W       = int(LETTER_WIDTH_MM  * A4_DPI / 25.4)
LETTER_PX_H       = int(LETTER_HEIGHT_MM * A4_DPI / 25.4)
LETTER_PT_W       = LETTER_WIDTH_MM  * 72 / 25.4
LETTER_PT_H       = LETTER_HEIGHT_MM * 72 / 25.4
LETTER_MARGIN_LR_PT = _BLEED_PT + 10 * 72 / 25.4
LETTER_MARGIN_TB_PT = _BLEED_PT + 12 * 72 / 25.4
LETTER_CONTENT_W_PT = LETTER_PT_W - 2 * LETTER_MARGIN_LR_PT
LETTER_CONTENT_H_PT = LETTER_PT_H - 2 * LETTER_MARGIN_TB_PT

BOOK_COLORING_CONFIG = {
    "magic_chef":           {"mode": "dynamic", "scene_indices": [4, 8, 13, 18, 22]},
    "dragon_garden":        {"mode": "dynamic", "scene_indices": [4, 8, 13, 18, 22]},
    "magic_inventor":       {"mode": "dynamic", "scene_indices": [4, 8, 13, 18, 22]},
    "star_keeper":          {"mode": "dynamic", "scene_indices": [4, 8, 13, 18, 22]},
    "centinela_aurora":     {"mode": "dynamic", "scene_indices": [4, 8, 13, 18, 22]},
    "furry_love":           {"mode": "dynamic", "scene_indices": [5, 8, 12, 16, 20]},
    "furry_love_adventure": {"mode": "dynamic", "scene_indices": [5, 8, 12, 16, 20]},
    "furry_love_teen":      {"mode": "dynamic", "scene_indices": [5, 8, 12, 16, 20]},
    "furry_love_adult":     {"mode": "dynamic", "scene_indices": [5, 8, 12, 16, 20]},
}
_DEFAULT_BOOK_ID = "magic_chef"

_BC_A4_DIR    = "static/images/fixed_pages/_backup"
_BC_CARTA_DIR = "static/images/fixed_pages/_backup/backup_PhotoMagic_carta"

FIXED_BACK_COVER_IMAGES = {
    "magic_chef":           f"{_BC_A4_DIR}/magic_chef_back_cover.png",
    "dragon_garden":        f"{_BC_A4_DIR}/dragon_garden_back_cover.png",
    "magic_inventor":       f"{_BC_A4_DIR}/magic_inventor_back_cover.png",
    "star_keeper":          f"{_BC_A4_DIR}/star_keeper_back_cover.png",
    "centinela_aurora":     f"{_BC_A4_DIR}/centinela_aurora_back_cover.png",
    "furry_love":           f"{_BC_A4_DIR}/furry_love_baby_back_cover.png",
    "furry_love_adventure": f"{_BC_A4_DIR}/furry_love_adventure_back_cover.png",
    "furry_love_teen":      f"{_BC_A4_DIR}/furry_love_teen_back_cover.png",
    "furry_love_adult":     f"{_BC_A4_DIR}/furry_love_adult_back_cover.png",
}

FIXED_BACK_COVER_IMAGES_LETTER = {
    "magic_chef":           f"{_BC_CARTA_DIR}/magic_chef_back_cover_letter.png",
    "dragon_garden":        f"{_BC_CARTA_DIR}/dragon_garden_back_cover_letter.png",
    "magic_inventor":       f"{_BC_CARTA_DIR}/magic_inventor_back_cover_letter.png",
    "star_keeper":          f"{_BC_CARTA_DIR}/star_keeper_back_cover_letter.png",
    "centinela_aurora":     f"{_BC_CARTA_DIR}/centinela_aurora_back_cover_letter.png",
    "furry_love":           f"{_BC_CARTA_DIR}/furry_love_baby_back_cover_letter.png",
    "furry_love_adventure": f"{_BC_CARTA_DIR}/furry_love_adventure_back_cover_letter.png",
    "furry_love_teen":      f"{_BC_CARTA_DIR}/furry_love_teen_back_cover_letter.png",
    "furry_love_adult":     f"{_BC_CARTA_DIR}/furry_love_adult_back_cover_letter.png",
}

_GENERIC_BACK_COVER = "static/images/back_cover.jpg"


def _try_font(path: str, size: int):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return None


def _best_font(size: int, bold: bool = False):
    candidates_bold = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    ]
    candidates_reg = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    ]
    candidates = candidates_bold if bold else candidates_reg
    for p in candidates:
        f = _try_font(p, size)
        if f:
            return f
    return ImageFont.load_default()


def _make_blank_page(px_w=None, px_h=None, color="#FFFFFF"):
    return Image.new("RGB", (px_w or A4_PX_W, px_h or A4_PX_H), color)


def _make_blank_a4(color="#FFFFFF"):
    return _make_blank_page(A4_PX_W, A4_PX_H, color)


def _fit_image_fullbleed(img: Image.Image, px_w=None, px_h=None, fill_mode: str = 'auto') -> Image.Image:
    """Scale & crop/extend image to fill the ENTIRE page canvas (bleed to bleed).

    fill_mode:
      'auto'   – scale by max(scale_w, scale_h), center-crop any overflow (default).
                 Best for 3:4 scene images: only ~5mm crop top/bottom on Letter.
      'height' – scale to fill HEIGHT exactly, no vertical crop ever.
                 If the scaled image is narrower than the canvas, the missing
                 left/right strips are filled with a heavily-blurred extension of
                 the image so text near the top/bottom edge is never cut.
                 Best for A4-ratio (1.42) visor pages on Letter canvas.
    """
    from PIL import ImageFilter
    _px_w = px_w or A4_PX_W
    _px_h = px_h or A4_PX_H
    src_w, src_h = img.size

    if fill_mode == 'height':
        scale = _px_h / src_h
        new_w = int(src_w * scale)
        resized = img.resize((new_w, _px_h), Image.Resampling.LANCZOS)
        if new_w >= _px_w:
            crop_x = (new_w - _px_w) // 2
            return resized.crop((crop_x, 0, crop_x + _px_w, _px_h))
        # Image is narrower than canvas — fill sides with blurred background
        bg_scale = _px_w / src_w
        bg_h = int(src_h * bg_scale)
        bg = img.resize((_px_w, max(bg_h, _px_h)), Image.Resampling.LANCZOS)
        if bg_h < _px_h:
            bg = bg.resize((_px_w, _px_h), Image.Resampling.LANCZOS)
        else:
            cy = (bg_h - _px_h) // 2
            bg = bg.crop((0, cy, _px_w, cy + _px_h))
        bg = bg.filter(ImageFilter.GaussianBlur(radius=60))
        x_off = (_px_w - new_w) // 2
        bg.paste(resized, (x_off, 0))
        return bg

    # Default 'auto': scale by max, center-crop
    scale = max(_px_w / src_w, _px_h / src_h)
    new_w = int(src_w * scale)
    new_h = int(src_h * scale)
    resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    crop_x = (new_w - _px_w) // 2
    crop_y = (new_h - _px_h) // 2
    return resized.crop((crop_x, crop_y, crop_x + _px_w, crop_y + _px_h))


def _fit_image_in_content(img: Image.Image,
                           px_w=None, px_h=None,
                           content_w_pt=None, content_h_pt=None,
                           margin_lr_pt=None, margin_tb_pt=None) -> Image.Image:
    """Proportional fill: scale so the image covers the full content area,
    then center-crop any overflow (no white bands, no stretch).
    Defaults to A4 dimensions for backward compatibility.
    """
    _px_w   = px_w or A4_PX_W
    _px_h   = px_h or A4_PX_H
    _cw_pt  = content_w_pt  if content_w_pt  is not None else CONTENT_W_PT
    _ch_pt  = content_h_pt  if content_h_pt  is not None else CONTENT_H_PT
    _mlr_pt = margin_lr_pt  if margin_lr_pt  is not None else MARGIN_LR_PT
    _mtb_pt = margin_tb_pt  if margin_tb_pt  is not None else MARGIN_TB_PT

    content_px_w = int(_cw_pt * A4_DPI / 72)
    content_px_h = int(_ch_pt * A4_DPI / 72)

    src_w, src_h = img.size
    # Fill: scale so the image covers the entire content area (max, not min)
    scale = max(content_px_w / src_w, content_px_h / src_h)
    new_w = int(src_w * scale)
    new_h = int(src_h * scale)
    resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

    # Center-crop to content area
    crop_x = (new_w - content_px_w) // 2
    crop_y = (new_h - content_px_h) // 2
    cropped = resized.crop((crop_x, crop_y, crop_x + content_px_w, crop_y + content_px_h))

    page = _make_blank_page(_px_w, _px_h)
    margin_px_lr = int(_mlr_pt * A4_DPI / 72)
    margin_px_tb = int(_mtb_pt * A4_DPI / 72)
    page.paste(cropped, (margin_px_lr, margin_px_tb))
    return page


def _page_to_buffer(img: Image.Image) -> BytesIO:
    buf = BytesIO()
    if img.mode == "RGBA":
        img = img.convert("RGB")
    img.save(buf, format="JPEG", quality=90, dpi=(A4_DPI, A4_DPI))
    buf.seek(0)
    return buf


def _generate_credits_page_a4(child_name: str, language: str = "es", px_w=None, px_h=None) -> Image.Image:
    bg_path = "static/images/credits_page_background.png"
    size = (px_w or A4_PX_W, px_h or A4_PX_H)
    if os.path.exists(bg_path):
        page = Image.open(bg_path).convert("RGB")
        page = page.resize(size, Image.Resampling.LANCZOS)
    else:
        page = Image.new("RGB", size, "#FFFEF5")

    draw = ImageDraw.Draw(page)
    scale = size[0] / 768

    title_font = _best_font(int(28 * scale), bold=True)
    name_font  = _best_font(int(22 * scale), bold=True)
    text_font  = _best_font(int(16 * scale), bold=False)

    if language == "es":
        lines = [
            ("Este libro fue creado especialmente para", "text"),
            (child_name or "ti", "name"),
            ("", "text"),
            ("Magic Memories Books", "title"),
            ("", "text"),
            ("Texto e ilustraciones generados con IA", "text"),
            ("© 2026 Magic Memories Books", "text"),
            ("Todos los derechos reservados.", "text"),
            ("", "text"),
            ("www.magicmemoriesbooks.com", "text"),
        ]
    else:
        lines = [
            ("This book was specially created for", "text"),
            (child_name or "you", "name"),
            ("", "text"),
            ("Magic Memories Books", "title"),
            ("", "text"),
            ("Text and illustrations generated with AI", "text"),
            ("© 2026 Magic Memories Books", "text"),
            ("All rights reserved.", "text"),
            ("", "text"),
            ("www.magicmemoriesbooks.com", "text"),
        ]

    line_height = int(35 * scale)
    start_y = int(size[1] * 0.25)

    for i, (text, text_type) in enumerate(lines):
        font = {"title": title_font, "name": name_font}.get(text_type, text_font)
        fill = {"title": "#2E1A47", "name": "#8B4513"}.get(text_type, "#2E1A47")
        if text:
            bbox = draw.textbbox((0, 0), text, font=font)
            x = (size[0] - (bbox[2] - bbox[0])) // 2
            y = start_y + i * line_height
            draw.text((x, y), text, font=font, fill=fill)

    return page


def _get_coloring_pages(book_id: str, gender: str, pages_dir: str, lang: str = 'es') -> list:
    cfg = BOOK_COLORING_CONFIG.get(book_id) or BOOK_COLORING_CONFIG[_DEFAULT_BOOK_ID]
    images = []

    if cfg["mode"] == "static":
        prefix = "nina" if gender in ("nina", "niña", "girl", "female", "f") else "nino"
        for scene in cfg["scenes"]:
            path = os.path.join(cfg["dir"], f"{prefix}_{scene}.png")
            if not os.path.exists(path):
                path = os.path.join(cfg["dir"], f"nino_{scene}.png")
            if os.path.exists(path):
                try:
                    images.append(Image.open(path).convert("RGB"))
                except Exception:
                    images.append(None)
            else:
                images.append(None)
    else:
        from services.pdf_service import _build_qs_cp_a4_drawing_page_image
        for visor_n in cfg["scene_indices"]:
            sp = os.path.join(pages_dir, f"page_{visor_n}.jpg")
            if os.path.exists(sp):
                try:
                    cp_img = _build_qs_cp_a4_drawing_page_image(sp, A4_PX_W * 72 / 300, A4_PX_H * 72 / 300, lang=lang)
                    images.append(cp_img)
                except Exception as e:
                    print(f"[PRINTABLE PDF] Coloring page error for scene {visor_n}: {e}")
                    images.append(None)
            else:
                print(f"[PRINTABLE PDF] Scene not found for coloring: {sp}")
                images.append(None)

    return images


def _load_coloring_page_a4(visor_path: str, slot: int = 0,
                            px_w=None, px_h=None,
                            cache_dir: str = None,
                            force_regenerate: bool = False,
                            lang: str = 'es',
                            **_ignored) -> Image.Image:
    """Convert a colour visor scene to a coloring-book drawing page.

    Delegates to _build_qs_cp_a4_drawing_page_image (services/pdf_service.py) which:
    - Uses FLUX Kontext Pro for clean black outlines on white
    - Falls back to PIL brightness/desaturate if FLUX fails
    - Adds '¡Dibuja tu propia historia!' title bar at the top
    Returns a PIL Image at exactly px_w × px_h pixels.

    If cache_dir is provided the generated image is saved to
    {cache_dir}/coloring_page_{scene_num}_{fmt}.png and reused on subsequent
    calls (unless force_regenerate=True).
    """
    import re as _re
    from services.pdf_service import _build_qs_cp_a4_drawing_page_image

    _px_w = px_w or A4_PX_W
    _px_h = px_h or A4_PX_H
    page_w_pt = _px_w * 72 / 300
    page_h_pt = _px_h * 72 / 300

    fmt_suffix = "a4" if _px_w == A4_PX_W else "letter"

    cache_path = None
    if cache_dir:
        m = _re.search(r'(\d+)', os.path.basename(visor_path or ''))
        if m:
            scene_num = m.group(1)
            cache_path = os.path.join(cache_dir, f"coloring_page_{scene_num}_{fmt_suffix}.png")

    if cache_path and os.path.exists(cache_path) and not force_regenerate:
        try:
            cached = Image.open(cache_path).convert("RGB")
            print(f"[PRINTABLE PDF] Coloring page cache HIT (slot={slot}): {cache_path}")
            return cached
        except Exception as ce:
            print(f"[PRINTABLE PDF] Cache read failed ({cache_path}): {ce} — regenerating")

    try:
        print(f"[PRINTABLE PDF] Coloring page slot={slot}: {visor_path}")
        result = _build_qs_cp_a4_drawing_page_image(visor_path, page_w_pt, page_h_pt, lang=lang)
        if cache_path:
            try:
                result.save(cache_path, format="PNG")
                print(f"[PRINTABLE PDF] Coloring page cached: {cache_path}")
            except Exception as se:
                print(f"[PRINTABLE PDF] Cache save failed ({cache_path}): {se}")
        return result
    except Exception as e:
        print(f"[PRINTABLE PDF] Coloring page error (slot {slot}): {e} — using blank")
        return _make_blank_page(_px_w, _px_h)


def generate_personalized_printable_pdf(
    book_session_id: str,
    child_name: str = "",
    gender: str = "nino",
    language: str = "es",
    book_id: str = None,
    book_title: str = "",
    output_path: str = None,
    force_regenerate: bool = False,
    front_cover_path: str = None,
    back_cover_path: str = None,
    print_format: str = "A4",
) -> str:
    """
    Build a 28-page A4 (or Letter) printable PDF for home/copy-shop printing.

    28-page structure (digital edition — portada + contraportada included):
      Page 1     : portada (visor page_1.jpg, fallback front_cover_path)
      Page 2     : blank
      Page 3     : portadilla (visor page_2.jpg)
      Page 4     : dedicatoria (visor page_3.jpg)
      Pages 5-23 : 19 story scenes (visor page_4.jpg … page_22.jpg)
      Pages 24-25: 2 coloring pages (scenes page_8 and page_17 as outlines)
      Page 26    : credits (dynamically generated)
      Page 27    : blank
      Page 28    : contraportada fija
                    A4     → FIXED_BACK_COVER_IMAGES
                    Letter → FIXED_BACK_COVER_IMAGES_LETTER

    Args:
        book_session_id : visor_pb session ID (same as preview_id)
        child_name      : Child's name (for credits page)
        gender          : 'nina'/'girl' or 'nino'/'boy'
        language        : 'es' or 'en'
        book_id         : Book type key ('magic_chef', 'dragon_garden', etc.)
        book_title      : Book title
        output_path     : Where to save the PDF (auto-generated if None)
        force_regenerate: Regenerate even if output already exists

    Returns:
        Absolute path to the generated PDF
    """
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.lib.utils import ImageReader

    if book_id is None:
        book_id = _DEFAULT_BOOK_ID

    pages_dir = os.path.join("generations", "visor_pb", book_session_id)
    if not os.path.isdir(pages_dir):
        raise FileNotFoundError(f"Book session not found: {pages_dir}")

    fmt_suffix = "LETTER" if print_format == "LETTER" else "A4"
    if output_path is None:
        out_dir = os.path.join("generated", "cloudprinter", book_session_id)
        os.makedirs(out_dir, exist_ok=True)
        safe_name = "".join(c for c in (child_name or "libro") if c.isalnum() or c in " _-").strip().replace(" ", "_")
        if not safe_name:
            safe_name = "libro"
        output_path = os.path.join(out_dir, f"{safe_name}_imprimible_{fmt_suffix}.pdf")
    else:
        dirpath = os.path.dirname(output_path)
        if dirpath:
            os.makedirs(dirpath, exist_ok=True)

    if os.path.exists(output_path) and not force_regenerate:
        print(f"[PRINTABLE PDF] Already exists, skipping: {output_path}")
        return os.path.abspath(output_path)

    print(f"[PRINTABLE PDF] Session: {book_session_id}, book_id: {book_id}, gender: {gender}")

    def scene_path(n):
        return os.path.join(pages_dir, f"page_{n}.jpg")

    def coloring_scene_path(n):
        """Return clean scene path (no text overlay) when available, else the composed visor page."""
        clean_p = os.path.join(pages_dir, f"clean_page_{n}.png")
        return clean_p if os.path.exists(clean_p) else scene_path(n)

    def has_scene(n):
        return os.path.exists(scene_path(n))

    # 28-page digital structure
    # Page 1  : portada  — visor page_1.jpg preferred; fallback to front_cover_path
    # Page 28 : contraportada — fixed back cover (with logo), format-specific path
    _fc = front_cover_path.lstrip('/') if front_cover_path else None
    _bc = back_cover_path.lstrip('/') if back_cover_path else None
    if _fc and not os.path.exists(_fc):
        _fc = None
    if _bc and not os.path.exists(_bc):
        _bc = None

    # Portada: prefer visor page_1.jpg (already rendered cover art)
    _visor_p1 = scene_path(1)
    _cover_src = _visor_p1 if os.path.exists(_visor_p1) else _fc

    # Contraportada: prefer fixed back cover (contains logo) — format-specific map.
    # A4 → FIXED_BACK_COVER_IMAGES, Letter → FIXED_BACK_COVER_IMAGES_LETTER.
    # Strip '_illustrated' suffix if needed; fallback to generic, then blank.
    _bc_dict = FIXED_BACK_COVER_IMAGES_LETTER if print_format == "LETTER" else FIXED_BACK_COVER_IMAGES
    _fixed_bc_key = book_id if book_id in _bc_dict else (book_id or "").replace("_illustrated", "")
    _fixed_bc = _bc_dict.get(_fixed_bc_key) or _bc_dict.get(book_id)
    if _fixed_bc and os.path.exists(_fixed_bc):
        _bc = _fixed_bc
        print(f"[PRINTABLE PDF] Using fixed back cover ({print_format}): {_bc}")
    elif not _bc and os.path.exists(_GENERIC_BACK_COVER):
        _bc = _GENERIC_BACK_COVER
        print(f"[PRINTABLE PDF] Using generic back cover: {_bc}")

    # Page types:
    #   fullbleed_h – A4-ratio visor pages (portada, portadilla, dedicatoria): scale to height, blur-extend sides
    #   fullbleed   – 3:4 scene pages (5-23): center-crop (~5mm top/bottom on Letter = OK)
    #   coloring    – scene converted to outline, fullbleed
    page_spec = [
        ("fullbleed_h" if _cover_src else "blank", _cover_src, None),  # Page 1  — portada
        ("blank",       None, None),                                     # Page 2  — blank
        ("fullbleed_h", scene_path(2), None),                            # Page 3  — portadilla (A4 ratio)
        ("fullbleed_h", scene_path(3), None),                            # Page 4  — dedicatoria (A4 ratio)
    ]

    for n in range(4, 23):                              # Pages 5-23 — 19 story scenes (3:4)
        src = scene_path(n) if has_scene(n) else None
        page_spec.append(("fullbleed" if src else "blank", src, None))

    page_spec.append(("coloring", coloring_scene_path(8),  0))         # Page 24 — coloring A (scene page_8)
    page_spec.append(("coloring", coloring_scene_path(17), 1))         # Page 25 — coloring B (scene page_17)
    page_spec.append(("credits",  None, None))                          # Page 26 — créditos
    page_spec.append(("blank",    None, None))                          # Page 27 — blank
    page_spec.append(("fullbleed" if _bc else "blank", _bc, None))     # Page 28 — contraportada

    total = len(page_spec)
    assert total == 28, f"Expected 28 pages, got {total}"

    if print_format == "LETTER":
        _px_w, _px_h       = LETTER_PX_W, LETTER_PX_H
        _pt_w, _pt_h       = LETTER_PT_W, LETTER_PT_H
        _cw_pt, _ch_pt     = LETTER_CONTENT_W_PT, LETTER_CONTENT_H_PT
        _mlr_pt, _mtb_pt   = LETTER_MARGIN_LR_PT, LETTER_MARGIN_TB_PT
    else:
        _px_w, _px_h       = A4_PX_W, A4_PX_H
        _pt_w, _pt_h       = A4_PT_W, A4_PT_H
        _cw_pt, _ch_pt     = CONTENT_W_PT, CONTENT_H_PT
        _mlr_pt, _mtb_pt   = MARGIN_LR_PT, MARGIN_TB_PT

    fit_kwargs = dict(px_w=_px_w, px_h=_px_h,
                      content_w_pt=_cw_pt, content_h_pt=_ch_pt,
                      margin_lr_pt=_mlr_pt, margin_tb_pt=_mtb_pt)
    bleed_pt = BLEED_MM * 72 / 25.4
    mark_pt  = 5.0 * 72 / 25.4

    print(f"[PRINTABLE PDF] Format: {print_format} — canvas {_pt_w:.1f}×{_pt_h:.1f}pt, page pixels {_px_w}×{_px_h}")

    c = rl_canvas.Canvas(output_path, pagesize=(_pt_w, _pt_h))

    for idx, (ptype, psrc, pdata) in enumerate(page_spec):
        page_num = idx + 1
        label = os.path.basename(psrc) if psrc else ptype
        print(f"[PRINTABLE PDF] Page {page_num:02d}/28: {ptype:<12} {label}")

        if ptype == "blank":
            page_img = _make_blank_page(_px_w, _px_h)
        elif ptype == "credits":
            page_img = _generate_credits_page_a4(child_name, language, px_w=_px_w, px_h=_px_h)
        elif ptype == "coloring":
            page_img = _load_coloring_page_a4(psrc, slot=pdata,
                                               px_w=_px_w, px_h=_px_h,
                                               cache_dir=pages_dir,
                                               force_regenerate=force_regenerate,
                                               lang=language)
        elif ptype in ("fullbleed", "fullbleed_h"):
            _fm = 'height' if ptype == 'fullbleed_h' else 'auto'
            try:
                raw = Image.open(psrc).convert("RGB")
                page_img = _fit_image_fullbleed(raw, px_w=_px_w, px_h=_px_h, fill_mode=_fm)
            except Exception as e:
                print(f"[PRINTABLE PDF] Error loading {ptype} {psrc}: {e} — using blank")
                page_img = _make_blank_page(_px_w, _px_h)
        else:
            try:
                raw = Image.open(psrc).convert("RGB")
                page_img = _fit_image_fullbleed(raw, px_w=_px_w, px_h=_px_h)
            except Exception as e:
                print(f"[PRINTABLE PDF] Error loading {psrc}: {e} — using blank")
                page_img = _make_blank_page(_px_w, _px_h)

        buf = _page_to_buffer(page_img)
        img_reader = ImageReader(buf)
        c.drawImage(img_reader, 0, 0, width=_pt_w, height=_pt_h)

        # Trim marks (L-shaped, gray, at bleed boundary)
        c.saveState()
        c.setStrokeColorRGB(0.75, 0.75, 0.75)
        c.setLineWidth(0.3)
        for x, y, dx, dy in [
            (bleed_pt, _pt_h - bleed_pt,  mark_pt, 0),
            (bleed_pt, _pt_h - bleed_pt,  0, -mark_pt),
            (_pt_w - bleed_pt, _pt_h - bleed_pt, -mark_pt, 0),
            (_pt_w - bleed_pt, _pt_h - bleed_pt, 0, -mark_pt),
            (bleed_pt, bleed_pt,  mark_pt, 0),
            (bleed_pt, bleed_pt,  0,  mark_pt),
            (_pt_w - bleed_pt, bleed_pt, -mark_pt, 0),
            (_pt_w - bleed_pt, bleed_pt, 0,  mark_pt),
        ]:
            c.line(x, y, x + dx, y + dy)
        c.restoreState()

        if idx < total - 1:
            c.showPage()

        del page_img, buf, img_reader
        gc.collect()

    c.save()
    gc.collect()

    size_mb = os.path.getsize(output_path) / 1024 / 1024
    print(f"[PRINTABLE PDF] Done: {output_path} ({size_mb:.1f} MB, 28 pages, format={print_format})")
    return os.path.abspath(output_path)
