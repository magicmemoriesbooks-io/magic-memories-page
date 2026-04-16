"""
Gelato Interior PDF Generator
Produces a 30-page interior PDF for Gelato's hardcover A4 photobook.

Gelato interior format: 210 × 280 mm
At 300 DPI: 2480 × 3307 pixels
PDF points: 595.28 × 793.70 pt

30-page structure:
  Page 1     : blank (front endpaper)
  Page 2     : portadilla (title page)
  Page 3     : blank
  Page 4     : dedicatoria
  Pages 5-23 : 19 story scenes (visor pages 4-22)
  Pages 24-28: 5 coloring silhouettes (gender-matched)
  Page 29    : credits
  Page 30    : blank (back endpaper)
"""

import os
import gc
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont


GELATO_WIDTH_MM = 210
GELATO_HEIGHT_MM = 280
GELATO_DPI = 300
GELATO_PX_W = int(GELATO_WIDTH_MM * GELATO_DPI / 25.4)   # 2480
GELATO_PX_H = int(GELATO_HEIGHT_MM * GELATO_DPI / 25.4)  # 3307
GELATO_PT_W = GELATO_WIDTH_MM * 72 / 25.4                 # 595.28
GELATO_PT_H = GELATO_HEIGHT_MM * 72 / 25.4                # 793.70

BOOK_COLORING_CONFIG = {
    "magic_chef": {
        "mode": "dynamic",
        "scene_indices": [4, 8, 13, 18, 22],
    },
    "dragon_garden": {
        "mode": "dynamic",
        "scene_indices": [4, 8, 13, 18, 22],
    },
    "magic_inventor": {
        "mode": "dynamic",
        "scene_indices": [4, 8, 13, 18, 22],
    },
    "star_keeper": {
        "mode": "dynamic",
        "scene_indices": [4, 8, 13, 18, 22],
    },
    "furry_love": {
        "mode": "dynamic",
        "scene_indices": [5, 8, 12, 16, 20],
    },
    "furry_love_adventure": {
        "mode": "dynamic",
        "scene_indices": [5, 8, 12, 16, 20],
    },
    "furry_love_teen": {
        "mode": "dynamic",
        "scene_indices": [5, 8, 12, 16, 20],
    },
    "furry_love_adult": {
        "mode": "dynamic",
        "scene_indices": [5, 8, 12, 16, 20],
    },
}
_DEFAULT_BOOK_ID = "magic_chef"


def _make_blank(bg_color="#FFFFFF"):
    """Create a blank white page at Gelato resolution."""
    return Image.new("RGB", (GELATO_PX_W, GELATO_PX_H), bg_color)


def _resize_to_gelato(img: Image.Image) -> Image.Image:
    """Resize a PIL image to Gelato interior dimensions, cropping if aspect ratio differs."""
    target_w, target_h = GELATO_PX_W, GELATO_PX_H
    src_w, src_h = img.size

    src_ratio = src_w / src_h
    tgt_ratio = target_w / target_h

    if abs(src_ratio - tgt_ratio) < 0.02:
        return img.resize((target_w, target_h), Image.Resampling.LANCZOS)

    if src_ratio > tgt_ratio:
        scale = target_h / src_h
        new_w = int(src_w * scale)
        resized = img.resize((new_w, target_h), Image.Resampling.LANCZOS)
        left = (new_w - target_w) // 2
        return resized.crop((left, 0, left + target_w, target_h))
    else:
        scale = target_w / src_w
        new_h = int(src_h * scale)
        resized = img.resize((target_w, new_h), Image.Resampling.LANCZOS)
        top = (new_h - target_h) // 2
        return resized.crop((0, top, target_w, top + target_h))


def _load_page(path: str) -> Image.Image:
    """Load a page image and resize it to Gelato dimensions."""
    img = Image.open(path).convert("RGB")
    return _resize_to_gelato(img)


def _scene_to_coloring_page(img: Image.Image, slot: int = 0) -> Image.Image:
    """Convert a colour scene image into a coloring-book outline.

    Primary method: FLUX Kontext Pro via Replicate — preserves exact characters
    and poses while converting to clean black outlines on white background.
    Fallback: PIL CONTOUR filter if Replicate call fails.
    """
    try:
        import io, httpx, requests, replicate as _replicate
        _client = _replicate.Client(timeout=httpx.Timeout(connect=30.0, read=300.0, write=120.0, pool=30.0))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        output = _client.run(
            "black-forest-labs/flux-kontext-pro",
            input={
                "input_image": buf,
                "prompt": (
                    "Transform this illustration into a children's coloring book page. "
                    "Keep the exact same characters, poses and composition. "
                    "Convert to clean black outlines on pure white background. "
                    "No color, no shading, no gradients. "
                    "Simple thick black outlines suitable for a child to color in."
                ),
                "guidance": 3.5,
                "steps": 20,
                "output_format": "png",
            }
        )
        url = str(output)
        resp = requests.get(url, timeout=60)
        result = Image.open(io.BytesIO(resp.content)).convert("RGB")
        print(f"[COLORING] Slot {slot}: Kontext Pro coloring page generated: {result.size}")
        return result
    except Exception as e:
        print(f"[COLORING] Slot {slot}: Replicate failed ({e}), falling back to PIL CONTOUR")
        from PIL import ImageFilter
        gray = img.convert("L")
        contour = gray.filter(ImageFilter.CONTOUR)
        bw = contour.point(lambda p: 0 if p < 200 else 255)
        return bw.convert("RGB")


def _get_coloring_pages(book_id: str, gender: str, pages_dir: str) -> list:
    """Return ordered list of 5 coloring-page PIL Images for the given book and gender.

    - magic_chef: loads static gender-matched PNG assets from disk.
    - Other books: converts configured story-scene images to coloring-page style
                   in parallel (one thread per coloring page).
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    cfg = BOOK_COLORING_CONFIG.get(book_id) or BOOK_COLORING_CONFIG[_DEFAULT_BOOK_ID]

    if cfg["mode"] == "static":
        prefix = "nina" if gender in ("nina", "niña", "girl", "female", "f") else "nino"
        images = []
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
        return images

    scene_indices = cfg["scene_indices"]
    n = len(scene_indices)
    results = [None] * n

    def _generate_one(slot, visor_n):
        clean_sp = os.path.join(pages_dir, f"clean_page_{visor_n}.png")
        sp = clean_sp if os.path.exists(clean_sp) else os.path.join(pages_dir, f"page_{visor_n}.jpg")
        if not os.path.exists(sp):
            print(f"[GELATO PDF] Scene not found for coloring page: {sp}")
            return slot, None
        if clean_sp and os.path.exists(clean_sp):
            print(f"[GELATO PDF] Using clean (text-free) page for slot {slot}: {clean_sp}")
        try:
            scene_img = Image.open(sp).convert("RGB")
            return slot, _scene_to_coloring_page(scene_img, slot=slot)
        except Exception as e:
            print(f"[GELATO PDF] Coloring page error for scene {visor_n}: {e}")
            return slot, None

    print(f"[COLORING] Generating {n} coloring pages in parallel...")
    with ThreadPoolExecutor(max_workers=n) as executor:
        futures = {
            executor.submit(_generate_one, i, visor_n): i
            for i, visor_n in enumerate(scene_indices)
        }
        for future in as_completed(futures):
            slot, img = future.result()
            results[slot] = img

    print(f"[COLORING] Parallel done: {sum(1 for r in results if r is not None)}/{n} succeeded")
    return results


def _generate_credits_page(child_name: str, language: str = "es") -> Image.Image:
    """Generate a credits page at Gelato resolution."""
    bg_path = "static/images/credits_page_background.png"
    size = (GELATO_PX_W, GELATO_PX_H)

    if os.path.exists(bg_path):
        page = Image.open(bg_path).convert("RGB")
        page = page.resize(size, Image.Resampling.LANCZOS)
    else:
        page = Image.new("RGB", size, "#FFFEF5")

    draw = ImageDraw.Draw(page)
    scale = size[0] / 768

    try:
        title_font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(28 * scale)
        )
        name_font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(22 * scale)
        )
        text_font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(16 * scale)
        )
    except Exception:
        title_font = name_font = text_font = ImageFont.load_default()

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


def _page_to_buffer(img: Image.Image, quality: int = 90) -> BytesIO:
    """Convert a PIL Image to a JPEG BytesIO buffer."""
    buf = BytesIO()
    if img.mode == "RGBA":
        img = img.convert("RGB")
    img.save(buf, format="JPEG", quality=quality, dpi=(GELATO_DPI, GELATO_DPI))
    buf.seek(0)
    return buf


def generate_gelato_interior_pdf(
    book_session_id: str,
    child_name: str = "",
    gender: str = "nino",
    language: str = "es",
    output_path: str = None,
    dedication_text: str = "",
    book_id: str = None,
) -> str:
    """
    Build a 30-page interior PDF for Gelato from an existing visor_pb generation.

    30-page structure:
      Page 1     : blank (front endpaper)
      Page 2     : portadilla (visor page_2.jpg)
      Page 3     : blank
      Page 4     : dedicatoria (visor page_3.jpg)
      Pages 5-23 : 19 story scenes (visor pages 4-22)
      Pages 24-28: 5 coloring silhouettes (static for magic_chef, dynamic Pillow for others)
      Page 29    : credits (dynamically generated with child_name)
      Page 30    : blank (back endpaper)

    Args:
        book_session_id: The visor_pb session ID (e.g. '2c4b15676b5a')
        child_name:      Child's name for the credits page
        gender:          'nina'/'niña'/'girl' or 'nino'/'niño'/'boy'
        language:        'es' or 'en'
        output_path:     Where to save the PDF (auto-generated if None)
        dedication_text: Optional custom dedication text (unused; page_3 is used directly)
        book_id:         Book identifier ('magic_chef', 'dragon_garden', etc.)

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

    if output_path is None:
        out_dir = os.path.join("generated", "gelato", book_session_id)
        os.makedirs(out_dir, exist_ok=True)
        output_path = os.path.join(out_dir, "interior_30p.pdf")
    else:
        dirpath = os.path.dirname(output_path)
        if dirpath:
            os.makedirs(dirpath, exist_ok=True)

    coloring_images = _get_coloring_pages(book_id, gender, pages_dir)
    print(f"[GELATO PDF] Session: {book_session_id}, book_id: {book_id}, gender: {gender}")
    print(f"[GELATO PDF] Coloring pages generated: {sum(1 for c in coloring_images if c is not None)}/5")

    def scene_path(n):
        return os.path.join(pages_dir, f"page_{n}.jpg")

    def has_scene(n):
        return os.path.exists(scene_path(n))

    page_spec = [
        ("blank",    None,  None),               # Page 1  — front endpaper
        ("image",    scene_path(2), None),        # Page 2  — portadilla
        ("blank",    None,  None),               # Page 3  — blank
        ("image",    scene_path(3), None),        # Page 4  — dedicatoria
    ]

    for n in range(4, 23):                       # Pages 5-23 — 19 story scenes
        src = scene_path(n) if has_scene(n) else None
        page_spec.append(("image" if src else "blank", src, None))

    for cp_img in coloring_images:               # Pages 24-28 — 5 coloring silhouettes
        if cp_img is not None:
            page_spec.append(("pil", None, cp_img))
        else:
            page_spec.append(("blank", None, None))

    page_spec.append(("credits", None, None))    # Page 29 — credits
    page_spec.append(("blank",   None, None))    # Page 30 — back endpaper

    total = len(page_spec)
    assert total == 30, f"Expected 30 pages, got {total}"

    c = rl_canvas.Canvas(output_path, pagesize=(GELATO_PT_W, GELATO_PT_H))

    for idx, (ptype, psrc, pimg) in enumerate(page_spec):
        page_num = idx + 1
        label = os.path.basename(psrc) if psrc else ("PIL" if pimg is not None else "")
        print(f"[GELATO PDF] Page {page_num:02d}/30: {ptype:<8} {label}")

        if ptype == "blank":
            page_img = _make_blank()
        elif ptype == "credits":
            page_img = _generate_credits_page(child_name, language)
        elif ptype == "pil":
            page_img = _resize_to_gelato(pimg)
        else:
            try:
                page_img = _load_page(psrc)
            except Exception as e:
                print(f"[GELATO PDF] Error loading {psrc}: {e} — using blank")
                page_img = _make_blank()

        buf = _page_to_buffer(page_img)
        img_reader = ImageReader(buf)
        c.drawImage(img_reader, 0, 0, width=GELATO_PT_W, height=GELATO_PT_H)

        if idx < total - 1:
            c.showPage()

        del page_img, buf, img_reader
        gc.collect()

    c.save()
    size_mb = os.path.getsize(output_path) / 1024 / 1024
    print(f"[GELATO PDF] Done: {output_path} ({size_mb:.1f} MB, 30 pages)")
    return output_path


def get_gelato_pdf_specs() -> dict:
    """Return Gelato interior PDF specifications."""
    return {
        "format": "Hardcover A4 (Gelato)",
        "size_mm": f"{GELATO_WIDTH_MM}x{GELATO_HEIGHT_MM}",
        "dpi": GELATO_DPI,
        "pixels": f"{GELATO_PX_W}x{GELATO_PX_H}",
        "pdf_points": f"{GELATO_PT_W:.2f}x{GELATO_PT_H:.2f}",
        "total_pages": 30,
        "structure": {
            1: "blank (front endpaper)",
            2: "portadilla",
            3: "blank",
            4: "dedicatoria",
            "5-23": "19 story scenes",
            "24-28": "5 coloring silhouettes (gender-matched)",
            29: "credits",
            30: "blank (back endpaper)",
        },
        "coloring_config": BOOK_COLORING_CONFIG,
    }
