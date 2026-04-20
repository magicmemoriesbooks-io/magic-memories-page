"""
Printable PDF Generator for Magic Memories Books
Produces a 26-page A4 PDF suitable for home printing at a copy shop.

Format  : A4 portrait (210 × 297 mm) at 300 DPI
Margins : 10 mm left/right, 12 mm top/bottom (safe print zone)
Content : 190 × 273 mm — images centred inside the safe area

26-page structure (matches the CP casewrap 26p interior):
  Page 1     : blank
  Page 2     : portadilla (visor page_2.jpg)
  Page 3     : dedicatoria (visor page_3.jpg)
  Pages 4-22 : 19 story scenes (visor page_4.jpg … page_22.jpg)
  Pages 23-24: 2 coloring pages (scenes page_8 and page_17 converted to outlines)
  Page 25    : credits (dynamically generated)
  Page 26    : blank

Coloring pages are full illustrations converted to clean outlines (no writing lines).
Uses gelato_pdf_service._scene_to_coloring_page with FLUX Kontext Pro / PIL fallback.

Output: generated/gelato/<session_id>/<name>_imprimible.pdf
  (saved under generated/gelato/ so the existing /preview-pdf/gelato/ route serves it)
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

FIXED_BACK_COVER_IMAGES = {
    "magic_chef":           "static/images/fixed_pages/magic_chef_back_cover.png",
    "dragon_garden":        "static/images/fixed_pages/dragon_garden_back_cover.png",
    "magic_inventor":       "static/images/fixed_pages/magic_inventor_back_cover.png",
    "star_keeper":          "static/images/fixed_pages/star_keeper_back_cover.png",
    "centinela_aurora":     "static/images/fixed_pages/centinela_aurora_back_cover.png",
    "furry_love":           "static/images/fixed_pages/furry_love_baby_back_cover.png",
    "furry_love_adventure": "static/images/fixed_pages/furry_love_adventure_back_cover.png",
    "furry_love_teen":      "static/images/fixed_pages/furry_love_teen_back_cover.png",
    "furry_love_adult":     "static/images/fixed_pages/furry_love_adult_back_cover.png",
}
_GENERIC_BACK_COVER = "static/images/fixed_pages/back_cover.png"


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


def _fit_image_in_content(img: Image.Image,
                           px_w=None, px_h=None,
                           content_w_pt=None, content_h_pt=None,
                           margin_lr_pt=None, margin_tb_pt=None) -> Image.Image:
    """Scale PIL image to fit within the content area, centred on white page.
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
    scale = min(content_px_w / src_w, content_px_h / src_h)
    new_w = int(src_w * scale)
    new_h = int(src_h * scale)
    resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

    page = _make_blank_page(_px_w, _px_h)
    margin_px_lr = int(_mlr_pt * A4_DPI / 72)
    margin_px_tb = int(_mtb_pt * A4_DPI / 72)
    x_offset = margin_px_lr + (content_px_w - new_w) // 2
    y_offset = margin_px_tb + (content_px_h - new_h) // 2
    page.paste(resized, (x_offset, y_offset))
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


def _get_coloring_pages(book_id: str, gender: str, pages_dir: str) -> list:
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
        for visor_n in cfg["scene_indices"]:
            sp = os.path.join(pages_dir, f"page_{visor_n}.jpg")
            if os.path.exists(sp):
                try:
                    from PIL import ImageFilter
                    scene_img = Image.open(sp).convert("RGB")
                    gray = scene_img.convert("L")
                    contour = gray.filter(ImageFilter.CONTOUR)
                    bw = contour.point(lambda p: 0 if p < 200 else 255)
                    images.append(bw.convert("RGB"))
                except Exception as e:
                    print(f"[PRINTABLE PDF] Coloring page error for scene {visor_n}: {e}")
                    images.append(None)
            else:
                print(f"[PRINTABLE PDF] Scene not found for coloring: {sp}")
                images.append(None)

    return images


def _load_coloring_page_a4(visor_path: str, slot: int = 0,
                            px_w=None, px_h=None,
                            content_w_pt=None, content_h_pt=None,
                            margin_lr_pt=None, margin_tb_pt=None) -> Image.Image:
    """Convert a colour visor scene to a coloring-book outline, scaled to the given page size."""
    fit_kwargs = dict(px_w=px_w, px_h=px_h,
                      content_w_pt=content_w_pt, content_h_pt=content_h_pt,
                      margin_lr_pt=margin_lr_pt, margin_tb_pt=margin_tb_pt)
    if not os.path.exists(visor_path):
        print(f"[PRINTABLE PDF] Coloring source not found: {visor_path} — using blank")
        return _make_blank_page(px_w, px_h)
    try:
        from services.gelato_pdf_service import _scene_to_coloring_page as _gelato_coloring
        scene_img = Image.open(visor_path).convert("RGB")
        coloring = _gelato_coloring(scene_img, slot=slot)
        scene_img.close()
        return _fit_image_in_content(coloring, **fit_kwargs)
    except Exception as e:
        print(f"[PRINTABLE PDF] Coloring page error (slot {slot}): {e} — using PIL CONTOUR fallback")
        from PIL import ImageFilter
        try:
            scene_img = Image.open(visor_path).convert("RGB")
            gray = scene_img.convert("L")
            contour = gray.filter(ImageFilter.CONTOUR)
            bw = contour.point(lambda p: 0 if p < 200 else 255)
            scene_img.close()
            return _fit_image_in_content(bw.convert("RGB"), **fit_kwargs)
        except Exception as e2:
            print(f"[PRINTABLE PDF] PIL CONTOUR also failed: {e2} — using blank")
            return _make_blank_page(px_w, px_h)


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
    Build a 26-page A4 printable PDF for home/copy-shop printing.

    26-page structure (mirrors the CP casewrap 26p interior):
      Page 1     : blank
      Page 2     : portadilla (visor page_2.jpg)
      Page 3     : dedicatoria (visor page_3.jpg)
      Pages 4-22 : 19 story scenes (visor page_4.jpg … page_22.jpg)
      Pages 23-24: 2 coloring pages (scenes page_8 and page_17 as outlines)
      Page 25    : credits (dynamically generated)
      Page 26    : blank

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
        out_dir = os.path.join("generated", "gelato", book_session_id)
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

    # 26-page structure (mirrors CP casewrap interior)
    # Page 1: portada (AI-generated front cover) or blank if not available
    # Page 26: contraportada — prefer fixed back cover (with logo) when available
    _fc = front_cover_path.lstrip('/') if front_cover_path else None
    _bc = back_cover_path.lstrip('/') if back_cover_path else None
    if _fc and not os.path.exists(_fc):
        _fc = None
    if _bc and not os.path.exists(_bc):
        _bc = None

    # Prefer the pre-designed fixed back cover (contains logo) over the AI-generated scene.
    # Match on exact book_id or strip the '_illustrated' suffix used internally.
    _fixed_bc_key = book_id if book_id in FIXED_BACK_COVER_IMAGES else (book_id or "").replace("_illustrated", "")
    _fixed_bc = FIXED_BACK_COVER_IMAGES.get(_fixed_bc_key) or FIXED_BACK_COVER_IMAGES.get(book_id)
    if _fixed_bc and os.path.exists(_fixed_bc):
        _bc = _fixed_bc
        print(f"[PRINTABLE PDF] Using fixed back cover (with logo): {_bc}")
    elif not _bc and os.path.exists(_GENERIC_BACK_COVER):
        _bc = _GENERIC_BACK_COVER
        print(f"[PRINTABLE PDF] Using generic back cover: {_bc}")

    page_spec = [
        ("image" if _fc else "blank", _fc, None),       # Page 1  — portada (AI cover) or blank
        ("image",  scene_path(2), None),                 # Page 2  — portadilla
        ("image",  scene_path(3), None),                 # Page 3  — dedicatoria
    ]

    for n in range(4, 23):                              # Pages 4-22 — 19 story scenes
        src = scene_path(n) if has_scene(n) else None
        page_spec.append(("image" if src else "blank", src, None))

    page_spec.append(("coloring", coloring_scene_path(8),  0))   # Page 23 — coloring A (scene page_8)
    page_spec.append(("coloring", coloring_scene_path(17), 1))   # Page 24 — coloring B (scene page_17)
    page_spec.append(("credits",  None, None))           # Page 25 — credits
    page_spec.append(("image" if _bc else "blank", _bc, None))  # Page 26 — contraportada or blank

    total = len(page_spec)
    assert total == 26, f"Expected 26 pages, got {total}"

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
        print(f"[PRINTABLE PDF] Page {page_num:02d}/26: {ptype:<12} {label}")

        if ptype == "blank":
            page_img = _make_blank_page(_px_w, _px_h)
        elif ptype == "credits":
            page_img = _generate_credits_page_a4(child_name, language, px_w=_px_w, px_h=_px_h)
        elif ptype == "coloring":
            page_img = _load_coloring_page_a4(psrc, slot=pdata, **fit_kwargs)
        else:
            try:
                raw = Image.open(psrc).convert("RGB")
                page_img = _fit_image_in_content(raw, **fit_kwargs)
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
    print(f"[PRINTABLE PDF] Done: {output_path} ({size_mb:.1f} MB, 26 pages, format={print_format})")
    return os.path.abspath(output_path)
