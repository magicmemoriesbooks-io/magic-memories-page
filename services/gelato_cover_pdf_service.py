"""
Gelato Cover Wrap PDF Generator
Builds the full cover wrap (back + spine + front + bleed) for Gelato's
Hardcover A4 (210×280mm) photobook.

Gelato cover wrap specification (30-page HC A4):
  Total: 478 × 326 mm  →  5645 × 3850 px at 300 DPI
  Layout (left→right):
    Bleed 26mm | Back cover 210mm | Spine 6mm | Front cover 210mm | Bleed 26mm
  Layout (top→bottom):
    Bleed 23mm | Print area 280mm | Bleed 23mm

  PDF points: 1354.96 × 924.09 pt  (= mm × 72/25.4)

Source images:
  Front cover:  visor_pb page_1.jpg   (the AI-generated front cover illustration)
  Back cover:   static/images/fixed_pages/{book_id}_back_cover.png  ← CLEAN (no logo)
                The logo montage is then added once by this service.
  Logo:         static/images/logo_main.jpg  (family reading montage)

NOTE: Do NOT use visor page_24.jpg for the back cover — that image is the back
panel cropped from the Lulu spread, which already has the logo embedded.
Using it here would result in a double logo.
"""

import os
import gc
import json
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont


GELATO_DPI = 300
MM2PX = GELATO_DPI / 25.4

WRAP_W_MM   = 478.0
WRAP_H_MM   = 326.0
BLEED_LR    = 26.0    # left and right bleed
BLEED_TB    = 23.0    # top and bottom bleed
BOARD_W_MM  = 210.0   # single page width
BOARD_H_MM  = 280.0   # single page height
SPINE_W_MM  = 6.0

WRAP_W_PX   = int(WRAP_W_MM  * MM2PX)    # 5645
WRAP_H_PX   = int(WRAP_H_MM  * MM2PX)    # 3850
BLEED_LR_PX = int(BLEED_LR   * MM2PX)    # 307
BLEED_TB_PX = int(BLEED_TB   * MM2PX)    # 272
BOARD_W_PX  = int(BOARD_W_MM * MM2PX)    # 2480
BOARD_H_PX  = int(BOARD_H_MM * MM2PX)    # 3307
SPINE_W_PX  = int(SPINE_W_MM * MM2PX)    # 71

WRAP_PT_W = WRAP_W_MM * 72 / 25.4        # 1354.96
WRAP_PT_H = WRAP_H_MM * 72 / 25.4        # 924.09

SPINE_COLOR   = "#2E1A47"
LOGO_PATH     = "static/images/logo_main.jpg"
LOGO_SIZE_RATIO = 0.22   # logo takes 22% of board width

FIXED_BACK_COVERS = {
    "dragon_garden":       "static/images/fixed_pages/dragon_garden_back_cover.png",
    "magic_chef":          "static/images/fixed_pages/magic_chef_back_cover.png",
    "magic_inventor":      "static/images/fixed_pages/magic_inventor_back_cover.png",
    "star_keeper":         "static/images/fixed_pages/star_keeper_back_cover.png",
    "furry_love":          "static/images/fixed_pages/furry_love_baby_back_cover.png",
    "furry_love_adventure":"static/images/fixed_pages/furry_love_adventure_back_cover.png",
    "furry_love_teen":     "static/images/fixed_pages/furry_love_teen_back_cover.png",
    "furry_love_adult":    "static/images/fixed_pages/furry_love_adult_back_cover.png",
}
GENERIC_BACK_COVER = "static/images/fixed_pages/back_cover.png"

FURRY_BOOK_IDS = {"furry_love", "furry_love_adventure", "furry_love_teen", "furry_love_adult"}


def _get_book_id_from_session(book_session_id: str) -> str:
    """Read metadata.json to determine the book_id for this session."""
    meta_path = os.path.join("generations", "visor_pb", book_session_id, "metadata.json")
    if os.path.exists(meta_path):
        try:
            with open(meta_path) as f:
                meta = json.load(f)
            book_id = meta.get("book_id", "")
            if not book_id:
                title = meta.get("title", "").lower()
                if "chef" in title:
                    book_id = "magic_chef"
                elif "invent" in title:
                    book_id = "magic_inventor"
                elif "estrella" in title or "star" in title:
                    book_id = "star_keeper"
                elif "dragon" in title:
                    book_id = "dragon_garden"
            return book_id
        except Exception:
            pass
    return "magic_chef"


def _resize_fit_cover(img: Image.Image, width_px: int, height_px: int) -> Image.Image:
    """Resize and center-crop image to exact pixel dimensions."""
    from PIL import ImageOps
    return ImageOps.fit(img, (width_px, height_px), Image.Resampling.LANCZOS)


def _build_spine(book_title: str, spine_color: str = SPINE_COLOR) -> Image.Image:
    """Create a spine panel (SPINE_W_PX × BOARD_H_PX) with title rotated 90°."""
    spine = Image.new("RGB", (SPINE_W_PX, BOARD_H_PX), spine_color)

    font_size = max(12, SPINE_W_PX - 8)
    try:
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size
        )
    except Exception:
        font = ImageFont.load_default()

    text_img = Image.new("RGBA", (BOARD_H_PX, SPINE_W_PX), (0, 0, 0, 0))
    text_draw = ImageDraw.Draw(text_img)
    bbox = text_draw.textbbox((0, 0), book_title, font=font)
    tx = (BOARD_H_PX - (bbox[2] - bbox[0])) // 2
    ty = (SPINE_W_PX - (bbox[3] - bbox[1])) // 2
    text_draw.text((tx, ty), book_title, font=font, fill="#FFFFFF")

    text_rotated = text_img.rotate(90, expand=True)
    spine_rgba = spine.convert("RGBA")
    spine_rgba.paste(text_rotated, (0, 0), text_rotated)
    return spine_rgba.convert("RGB")


def _add_logo_to_back(canvas: Image.Image, back_x: int, board_y: int, book_id: str) -> None:
    """
    Add the MMB logo montage to the bottom-right of the back cover panel.
    """
    if not os.path.exists(LOGO_PATH):
        print(f"[GELATO COVER] Logo not found at {LOGO_PATH}")
        return

    try:
        logo = Image.open(LOGO_PATH).convert("RGBA")
        logo_size = int(BOARD_W_PX * LOGO_SIZE_RATIO)
        logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)

        margin = int(BOARD_W_PX * 0.04)
        logo_x = back_x + BOARD_W_PX - logo_size - margin
        logo_y = board_y + BOARD_H_PX - logo_size - margin

        if logo.mode == "RGBA":
            canvas.paste(logo, (logo_x, logo_y), logo)
        else:
            canvas.paste(logo, (logo_x, logo_y))

        print(f"[GELATO COVER] Logo added at ({logo_x},{logo_y}), size {logo_size}px")
    except Exception as e:
        print(f"[GELATO COVER] Could not add logo: {e}")


def generate_gelato_cover_pdf(
    book_session_id: str,
    book_title: str = None,
    book_id: str = None,
    output_path: str = None,
    spine_color: str = SPINE_COLOR,
) -> str:
    """
    Build the Gelato cover wrap PDF.

    Uses:
      - Front cover: visor_pb page_1.jpg (AI-generated front illustration)
      - Back cover:  fixed_pages/{book_id}_back_cover.png (CLEAN — no logo)
      - Logo:        logo_main.jpg added once to the back cover

    The wrap layout (left→right):
      [bleed 26mm][back cover 210mm][spine 6mm][front cover 210mm][bleed 26mm]

    Args:
        book_session_id: visor_pb session ID (e.g. '2c4b15676b5a')
        book_title:      Title text for the spine (auto-detected from metadata if None)
        book_id:         Book type key (auto-detected from metadata if None)
        output_path:     Output PDF path (auto-generated if None)
        spine_color:     Hex colour for the spine background

    Returns:
        Absolute path to the generated cover wrap PDF
    """
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.lib.utils import ImageReader

    pages_dir = os.path.join("generations", "visor_pb", book_session_id)
    if not os.path.isdir(pages_dir):
        raise FileNotFoundError(f"Session not found: {pages_dir}")

    if book_id is None:
        book_id = _get_book_id_from_session(book_session_id)
        print(f"[GELATO COVER] Auto-detected book_id: {book_id}")

    if book_title is None:
        meta_path = os.path.join(pages_dir, "metadata.json")
        try:
            with open(meta_path) as f:
                meta = json.load(f)
            book_title = meta.get("title", "Magic Memories Books")
        except Exception:
            book_title = "Magic Memories Books"

    back_cover_path = FIXED_BACK_COVERS.get(book_id)
    if not back_cover_path or not os.path.exists(back_cover_path):
        print(f"[GELATO COVER] Fixed back cover not found for {book_id}, using generic")
        back_cover_path = GENERIC_BACK_COVER

    front_path = os.path.join(pages_dir, "page_1.jpg")
    if not os.path.exists(front_path):
        raise FileNotFoundError(f"Front cover image not found: {front_path}")

    if output_path is None:
        out_dir = os.path.join("generated", "gelato", book_session_id)
        os.makedirs(out_dir, exist_ok=True)
        output_path = os.path.join(out_dir, "cover_wrap.pdf")
    else:
        dirpath = os.path.dirname(output_path)
        if dirpath:
            os.makedirs(dirpath, exist_ok=True)

    print(f"[GELATO COVER] Building {WRAP_W_PX}×{WRAP_H_PX}px cover wrap")
    print(f"[GELATO COVER] Front: {front_path}")
    print(f"[GELATO COVER] Back (clean PNG): {back_cover_path}")

    canvas_img = Image.new("RGB", (WRAP_W_PX, WRAP_H_PX), "#FFFFFF")

    front_img = Image.open(front_path).convert("RGB")
    front_panel = _resize_fit_cover(front_img, BOARD_W_PX, BOARD_H_PX)
    del front_img

    back_img = Image.open(back_cover_path).convert("RGB")
    back_panel = _resize_fit_cover(back_img, BOARD_W_PX, BOARD_H_PX)
    del back_img

    spine_panel = _build_spine(book_title, spine_color)

    back_x  = BLEED_LR_PX
    spine_x = back_x + BOARD_W_PX
    front_x = spine_x + SPINE_W_PX
    board_y = BLEED_TB_PX

    canvas_img.paste(back_panel,  (back_x,  board_y))
    canvas_img.paste(spine_panel, (spine_x, board_y))
    canvas_img.paste(front_panel, (front_x, board_y))

    left_strip  = back_panel.crop((0, 0, BLEED_LR_PX, BOARD_H_PX))
    right_strip = front_panel.crop((BOARD_W_PX - BLEED_LR_PX, 0, BOARD_W_PX, BOARD_H_PX))
    canvas_img.paste(left_strip,  (0, board_y))
    canvas_img.paste(right_strip, (front_x + BOARD_W_PX, board_y))

    top_strip = canvas_img.crop((0, board_y, WRAP_W_PX, board_y + BLEED_TB_PX))
    bot_strip = canvas_img.crop((0, board_y + BOARD_H_PX - BLEED_TB_PX, WRAP_W_PX, board_y + BOARD_H_PX))
    canvas_img.paste(top_strip, (0, 0))
    canvas_img.paste(bot_strip, (0, board_y + BOARD_H_PX))

    _add_logo_to_back(canvas_img, back_x, board_y, book_id)

    del back_panel, front_panel, spine_panel, left_strip, right_strip, top_strip, bot_strip
    gc.collect()

    buf = BytesIO()
    if canvas_img.mode == "RGBA":
        canvas_img = canvas_img.convert("RGB")
    canvas_img.save(buf, format="JPEG", quality=92, dpi=(GELATO_DPI, GELATO_DPI))
    buf.seek(0)
    del canvas_img
    gc.collect()

    c = rl_canvas.Canvas(output_path, pagesize=(WRAP_PT_W, WRAP_PT_H))
    c.drawImage(ImageReader(buf), 0, 0, width=WRAP_PT_W, height=WRAP_PT_H)
    c.save()

    size_mb = os.path.getsize(output_path) / 1024 / 1024
    print(f"[GELATO COVER] Done: {output_path} ({size_mb:.1f} MB)")
    return output_path


def get_gelato_cover_specs() -> dict:
    return {
        "format": "Cover wrap — HC A4 Gelato",
        "total_mm": f"{WRAP_W_MM}×{WRAP_H_MM}",
        "total_px": f"{WRAP_W_PX}×{WRAP_H_PX}",
        "pdf_pt": f"{WRAP_PT_W:.2f}×{WRAP_PT_H:.2f}",
        "bleed_lr_mm": BLEED_LR,
        "bleed_tb_mm": BLEED_TB,
        "spine_mm": SPINE_W_MM,
        "board_mm": f"{BOARD_W_MM}×{BOARD_H_MM}",
        "layout": "[bleed 26mm][back 210mm][spine 6mm][front 210mm][bleed 26mm]",
        "back_source": "fixed_pages/{book_id}_back_cover.png (clean, no pre-baked logo)",
        "logo": "logo_main.jpg added once to bottom-right of back cover",
    }
