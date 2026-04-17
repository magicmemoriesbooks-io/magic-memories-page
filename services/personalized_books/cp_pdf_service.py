"""
Cloudprinter Casewrap A4 PDF Generator
Produces two files for photobook_cw_a4_p_fc (26-page hardcover):

  cover.pdf    — full wrap spread (back + spine + front) with 18 mm wrap-around (CP spec)
  content.pdf  — 26 interior pages at A4 + 3 mm bleed (216 × 303 mm)

26-page interior structure (active — verified via CP API quote, €9.73 print cost):
  Page  1 : blank
  Page  2 : portadilla  (visor_pb page_2.jpg)
  Page  3 : dedicatoria (visor_pb page_3.jpg)
  Pages 4-22 : 19 story scenes (visor_pb page_4.jpg … page_22.jpg)
  Page 23 : coloring page A (scene page_8 as outline)
  Page 24 : coloring page B (scene page_17 as outline)
  Page 25 : credits (dynamically generated)
  Page 26 : blank

Cover sources:
  Front: generated/composed_{session_id}/front_cover.png
  Back : generated/composed_{session_id}/back_cover.png

CP specs confirmed via API:
  - Trim: 210×297 mm (A4 standard)
  - Bleed: 3 mm
  - Cover wrap: 18 mm (cover_wrap_in_mm from CP products/info)
  - Cover overlap: 3 mm
  - Cover squeeze: 5 mm
  - Pageblock: 200gsm Machine Coated Gloss (Standard) — pageblock_200mcs
"""

import os
import gc
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageOps

# ─── Content page (interior) dimensions — A4 text block ────────────────────────
TRIM_W_MM  = 210.0
TRIM_H_MM  = 297.0
BLEED_MM   = 3.0
DPI        = 300
MM2PT      = 72.0 / 25.4

PAGE_W_MM  = TRIM_W_MM + 2 * BLEED_MM   # 216 mm
PAGE_H_MM  = TRIM_H_MM + 2 * BLEED_MM   # 303 mm
PAGE_W_PT  = PAGE_W_MM * MM2PT
PAGE_H_PT  = PAGE_H_MM * MM2PT
PAGE_W_PX  = round(PAGE_W_MM * DPI / 25.4)   # 2551 px
PAGE_H_PX  = round(PAGE_H_MM * DPI / 25.4)   # 3579 px
TRIM_PX    = round(TRIM_W_MM * DPI / 25.4)   # 2480 px  (content only)
TRIM_H_PX  = round(TRIM_H_MM * DPI / 25.4)   # 3508 px  (content only)
BLEED_PX   = round(BLEED_MM  * DPI / 25.4)   # 35 px

# ─── Cover board face dimensions — Fotomagic photobook_cw_a4_p_fc ──────────────
# The visible board (punta a punta) is 216×302mm — larger than the text block.
# Bleed and wrap are added on top of these cover-trim dimensions.
COV_TRIM_W_MM = 216.0   # board face width  (confirmed by physical measurement)
COV_TRIM_H_MM = 302.0   # board face height (confirmed by physical measurement)
COV_TRIM_PX   = round(COV_TRIM_W_MM * DPI / 25.4)   # 2551 px
COV_TRIM_H_PX = round(COV_TRIM_H_MM * DPI / 25.4)   # 3567 px

# ─── Cover spread dimensions ────────────────────────────────────────────────────
# Width  = wrap + bleed + cov_trim_W + squeeze + spine + squeeze + cov_trim_W + bleed + wrap
# Height = wrap + bleed + cov_trim_H + bleed + wrap
# Spine formula: (gsm × bulk_MCG × leaves) / 1000 + 2 × board_mm
PAPER_GSM      = 200          # pageblock_200mcg = Machine Coated Gloss (Global default)
PAPER_BULK_MCG = 0.808        # MCG Gloss bulk factor → spine=8.1mm for 26p (CP verified)
BOARD_MM       = 3.0

CW_PAGES       = 24          # Option A (24p — kept for backward compatibility)
CW_PAGES_26    = 26          # Option B (26p — active; verified via CP API quote)
CW_PAGES_SELECTED = CW_PAGES_26  # Active choice — 26 pages (verified €9.73 print cost)

def _calc_spine_mm(page_count: int) -> float:
    """Calculate spine width in mm for a given page count using MCG (Gloss) bulk."""
    leaves = page_count / 2
    return (PAPER_GSM * PAPER_BULK_MCG * leaves) / 1000 + 2 * BOARD_MM

SPINE_W_MM     = _calc_spine_mm(CW_PAGES)      # ~7.94 mm for 24p (MCG Gloss)
SPINE_W_MM_26  = _calc_spine_mm(CW_PAGES_26)   # ~8.10 mm for 26p (MCG Gloss) — CP verified

WRAP_MM        = 21.0    # CP casewrap turn-in: 21mm
SQUEEZE_MM     = 5.0     # CP cover_squeeze_in_mm: 5mm each side of spine

def _calc_cover_dims(spine_mm: float):
    """Return (cover_w_mm, cover_h_mm, cover_w_pt, cover_h_pt, cover_w_px, cover_h_px, spine_px, wrap_px, squeeze_px)."""
    cw_mm = WRAP_MM + BLEED_MM + COV_TRIM_W_MM + SQUEEZE_MM + spine_mm + SQUEEZE_MM + COV_TRIM_W_MM + BLEED_MM + WRAP_MM
    ch_mm = WRAP_MM + BLEED_MM + COV_TRIM_H_MM + BLEED_MM + WRAP_MM
    return (
        cw_mm, ch_mm,
        cw_mm * MM2PT, ch_mm * MM2PT,
        round(cw_mm * DPI / 25.4), round(ch_mm * DPI / 25.4),
        round(spine_mm   * DPI / 25.4),
        round(WRAP_MM    * DPI / 25.4),
        round(SQUEEZE_MM * DPI / 25.4),
    )

(COVER_W_MM, COVER_H_MM, COVER_W_PT, COVER_H_PT,
 COVER_W_PX, COVER_H_PX, SPINE_PX, WRAP_PX,
 SQUEEZE_PX) = _calc_cover_dims(CW_PAGES_SELECTED and _calc_spine_mm(CW_PAGES_SELECTED))

SPINE_COLOR    = "#2E1A47"
LOGO_PATH      = "static/images/logo_main.jpg"


def _fit_page(img: Image.Image) -> Image.Image:
    return ImageOps.fit(img, (PAGE_W_PX, PAGE_H_PX), Image.Resampling.LANCZOS)


def _blank_page() -> Image.Image:
    return Image.new("RGB", (PAGE_W_PX, PAGE_H_PX), "#FFFFFF")


def _scene_to_coloring_page(img: Image.Image, slot: int = 0) -> Image.Image:
    """Convert a colour scene to a coloring-book outline for Option B (26p).

    Delegates to gelato_pdf_service._scene_to_coloring_page which uses
    FLUX Kontext Pro (Replicate) with PIL CONTOUR fallback, ensuring parity
    with the Gelato product line coloring-page quality.
    """
    try:
        from services.gelato_pdf_service import _scene_to_coloring_page as _gelato_scene_to_coloring
        result = _gelato_scene_to_coloring(img, slot=slot)
        return _fit_page(result) if result.size != (PAGE_W_PX, PAGE_H_PX) else result
    except Exception as _import_err:
        from PIL import ImageFilter
        print(f"[CP PDF] gelato coloring fallback (PIL CONTOUR): {_import_err}")
        gray = img.convert("L")
        contour = gray.filter(ImageFilter.CONTOUR)
        bw = contour.point(lambda p: 0 if p < 180 else 255)
        return _fit_page(bw.convert("RGB"))


def _generate_credits_page(child_name: str, language: str = "es") -> Image.Image:
    """Generate a credits page at A4+bleed resolution."""
    bg_path = "static/images/credits_page_background.png"
    size = (PAGE_W_PX, PAGE_H_PX)

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


def _embed_page(c, img: Image.Image):
    """Write a PIL Image as a JPEG page into a ReportLab canvas."""
    from reportlab.lib.utils import ImageReader
    buf = BytesIO()
    if img.mode != "RGB":
        img = img.convert("RGB")
    img.save(buf, format="JPEG", quality=92, dpi=(DPI, DPI))
    buf.seek(0)
    c.drawImage(ImageReader(buf), 0, 0, width=PAGE_W_PT, height=PAGE_H_PT)


def generate_cw_cover_pdf(
    session_id: str,
    book_title: str = "Magic Memories Books",
    output_path: str = None,
    page_count: int = CW_PAGES_SELECTED,
) -> str:
    """
    Build the casewrap cover spread PDF for photobook_cw_a4_p_fc.

    page_count controls the spine width calculation (24p → ~7.94 mm, 26p → ~8.10 mm, MCG Gloss paper).
    Layout (width):  [wrap 21mm][bleed 3mm][back 216mm][squeeze 5mm][spine ~8.10mm][squeeze 5mm][front 216mm][bleed 3mm][wrap 21mm]
    Layout (height): [wrap 21mm][bleed 3mm][board 302mm][bleed 3mm][wrap 21mm]
    Total: ~498.1 × 350.0 mm (cover board face 216×302mm + bleed + wrap)

    Front/back images loaded from generated/composed_{session_id}/.

    Returns the absolute path to the generated cover.pdf.
    """
    from reportlab.pdfgen import canvas as rl_canvas

    composed_dir = os.path.join("generated", f"composed_{session_id}")
    if output_path is None:
        out_dir = os.path.join("generations", "cloudprinter", session_id)
        os.makedirs(out_dir, exist_ok=True)
        output_path = os.path.join(out_dir, "cover.pdf")
    else:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Recalculate dimensions for the chosen page count (spine varies with page count)
    spine_mm = _calc_spine_mm(page_count)
    (cov_w_mm, cov_h_mm, cov_w_pt, cov_h_pt,
     cov_w_px, cov_h_px, spine_px, wrap_px,
     squeeze_px) = _calc_cover_dims(spine_mm)

    print(f"[CP PDF] Building CW cover spread {cov_w_mm:.1f}×{cov_h_mm:.1f}mm "
          f"(spine {spine_mm:.2f}mm, wrap {WRAP_MM:.0f}mm, squeeze {SQUEEZE_MM:.0f}mm, {page_count}p)")

    spread = Image.new("RGB", (cov_w_px, cov_h_px), "#FFFFFF")

    # ── Front cover ────────────────────────────────────────────────────────────
    def _load_cover_image(composed_dir: str, stem: str, fallback_color: str, trim_px: int, trim_h_px: int):
        """Try PNG then JPG for cover; return RGB Image (fallback solid color)."""
        for ext in (".png", ".jpg", ".jpeg"):
            candidate = os.path.join(composed_dir, stem + ext)
            if os.path.exists(candidate):
                print(f"[CP PDF] {stem} loaded from {candidate}")
                return Image.open(candidate).convert("RGB"), candidate
        print(f"[CP PDF] {stem} not found (tried .png/.jpg) — using {fallback_color} fill")
        return Image.new("RGB", (trim_px, trim_h_px), fallback_color), None

    front_img, front_src = _load_cover_image(composed_dir, "front_cover", "#6B46C1", COV_TRIM_PX, COV_TRIM_H_PX)
    front_panel = ImageOps.fit(front_img, (COV_TRIM_PX, COV_TRIM_H_PX), Image.Resampling.LANCZOS)
    front_img.close()

    # ── Back cover ─────────────────────────────────────────────────────────────
    back_img, back_src = _load_cover_image(composed_dir, "back_cover", "#F3E8FF", COV_TRIM_PX, COV_TRIM_H_PX)
    if back_src:
        back_panel = ImageOps.fit(back_img, (COV_TRIM_PX, COV_TRIM_H_PX), Image.Resampling.LANCZOS)
        back_img.close()
    else:
        back_panel = back_img

    # Logo is already embedded in back_cover.png by generate_cover_spread — do not add again.

    # ── Spine ──────────────────────────────────────────────────────────────────
    spine_panel = Image.new("RGB", (spine_px, COV_TRIM_H_PX), SPINE_COLOR)
    try:
        font_size = max(10, spine_px - 6)
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size
        )
    except Exception:
        font = ImageFont.load_default()
    text_canvas = Image.new("RGBA", (COV_TRIM_H_PX, spine_px), (0, 0, 0, 0))
    td = ImageDraw.Draw(text_canvas)
    bbox = td.textbbox((0, 0), book_title, font=font)
    tx = (COV_TRIM_H_PX - (bbox[2] - bbox[0])) // 2
    ty = (spine_px - (bbox[3] - bbox[1])) // 2
    td.text((tx, ty), book_title, font=font, fill="#FFFFFF")
    spine_panel.paste(text_canvas.rotate(90, expand=True).convert("RGB"), (0, 0))
    text_canvas.close()

    # ── Compose spread ─────────────────────────────────────────────────────────
    # Layout (width): [wrap][bleed][back_panel][squeeze][spine][squeeze][front_panel][bleed][wrap]
    # Layout (height): [wrap][bleed][cov_trim_H][bleed][wrap]
    board_y      = wrap_px + BLEED_PX
    back_x       = wrap_px + BLEED_PX
    squeeze_l_x  = back_x + COV_TRIM_PX
    spine_x      = squeeze_l_x + squeeze_px
    squeeze_r_x  = spine_x + spine_px
    front_x      = squeeze_r_x + squeeze_px

    # Squeeze zones — filled with spine color (binding area; must not contain content)
    sq_panel_l = Image.new("RGB", (squeeze_px, COV_TRIM_H_PX), SPINE_COLOR)
    sq_panel_r = Image.new("RGB", (squeeze_px, COV_TRIM_H_PX), SPINE_COLOR)

    spread.paste(back_panel,  (back_x,      board_y))
    spread.paste(sq_panel_l,  (squeeze_l_x, board_y))
    spread.paste(spine_panel, (spine_x,     board_y))
    spread.paste(sq_panel_r,  (squeeze_r_x, board_y))
    spread.paste(front_panel, (front_x,     board_y))

    fill_w = wrap_px + BLEED_PX
    fill_h = wrap_px + BLEED_PX

    # Left wrap strip (mirror of left edge of back panel)
    spread.paste(
        ImageOps.fit(back_panel.crop((0, 0, fill_w, COV_TRIM_H_PX)), (fill_w, COV_TRIM_H_PX)),
        (0, board_y)
    )
    # Right wrap strip (mirror of right edge of front panel)
    spread.paste(
        ImageOps.fit(front_panel.crop((COV_TRIM_PX - fill_w, 0, COV_TRIM_PX, COV_TRIM_H_PX)), (fill_w, COV_TRIM_H_PX)),
        (front_x + COV_TRIM_PX, board_y)
    )
    # Top/bottom wrap strips
    top_strip = spread.crop((0, board_y, cov_w_px, board_y + fill_h))
    spread.paste(top_strip, (0, 0))
    bot_strip = spread.crop((0, board_y + COV_TRIM_H_PX - fill_h, cov_w_px, board_y + COV_TRIM_H_PX))
    spread.paste(bot_strip, (0, board_y + COV_TRIM_H_PX))

    for obj in [back_panel, front_panel, spine_panel, sq_panel_l, sq_panel_r, top_strip, bot_strip]:
        try:
            obj.close()
        except Exception:
            pass
    gc.collect()

    buf = BytesIO()
    spread.save(buf, format="JPEG", quality=92, dpi=(DPI, DPI))
    buf.seek(0)
    spread.close()
    gc.collect()

    c = rl_canvas.Canvas(output_path, pagesize=(cov_w_pt, cov_h_pt))
    from reportlab.lib.utils import ImageReader
    c.drawImage(ImageReader(buf), 0, 0, width=cov_w_pt, height=cov_h_pt)
    c.save()

    size_mb = os.path.getsize(output_path) / 1024 / 1024
    print(f"[CP PDF] Cover done: {output_path} ({size_mb:.1f} MB)")
    return output_path


def generate_cw_content_pdf(
    session_id: str,
    child_name: str = "",
    language: str = "es",
    output_path: str = None,
    page_count: int = CW_PAGES_SELECTED,
) -> str:
    """
    Build the interior content PDF for photobook_cw_a4_p_fc.

    page_count=26 (Option B, active default): includes 2 coloring pages.
    page_count=24 (Option A, legacy): standard structure without coloring pages.

    Page structure (26p, active):
      Page  1 : blank
      Page  2 : portadilla  (visor_pb page_2.jpg)
      Page  3 : dedicatoria (visor_pb page_3.jpg)
      Pages 4-22 : 19 scenes (visor_pb page_4.jpg … page_22.jpg)
      Page 23 : credits
      Page 24 : blank

    All pages at 216×303mm (A4 + 3mm bleed) at 300 DPI.

    Returns the absolute path to the generated content.pdf.
    """
    from reportlab.pdfgen import canvas as rl_canvas

    pages_dir = os.path.join("generations", "visor_pb", session_id)
    if not os.path.isdir(pages_dir):
        raise FileNotFoundError(f"Book session not found: {pages_dir}")

    if output_path is None:
        out_dir = os.path.join("generations", "cloudprinter", session_id)
        os.makedirs(out_dir, exist_ok=True)
        output_path = os.path.join(out_dir, "content.pdf")
    else:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

    if page_count not in (CW_PAGES, CW_PAGES_26):
        raise ValueError(f"page_count must be {CW_PAGES} or {CW_PAGES_26}, got {page_count}")

    print(f"[CP PDF] Building CW content {page_count}p interior for session {session_id}")

    def _visor_path(n: int) -> str:
        return os.path.join(pages_dir, f"page_{n}.jpg")

    def _load_visor(n: int) -> Image.Image:
        p = _visor_path(n)
        if os.path.exists(p):
            img = Image.open(p).convert("RGB")
            return _fit_page(img)
        print(f"[CP PDF] visor page_{n}.jpg not found — using blank")
        return _blank_page()

    def _load_coloring(visor_n: int) -> Image.Image:
        """Load visor scene and convert to coloring-page outline (Option B, 26p).

        Prefers clean_page_{n}.png (no text overlay) when available so that
        the FLUX coloring conversion receives a text-free input image.
        Falls back to the composed visor page (page_{n}.jpg) if the clean
        version does not exist.
        """
        clean_p = os.path.join(pages_dir, f"clean_page_{visor_n}.png")
        p = clean_p if os.path.exists(clean_p) else _visor_path(visor_n)
        if os.path.exists(p):
            img = Image.open(p).convert("RGB")
            src_tag = "clean" if p == clean_p else "visor"
            print(f"[CP PDF] coloring source for page_{visor_n}: {src_tag}")
            return _scene_to_coloring_page(img)
        print(f"[CP PDF] coloring source page_{visor_n} not found — using blank")
        return _blank_page()

    # Build page spec according to page_count
    page_spec = []
    page_spec.append(("blank", None))               # Page 1  — blank
    page_spec.append(("visor", 2))                  # Page 2  — portadilla
    page_spec.append(("visor", 3))                  # Page 3  — dedicatoria
    for n in range(4, 23):                           # Pages 4-22 — 19 scenes
        page_spec.append(("visor", n))
    if page_count == CW_PAGES_26:
        # Option B: 2 coloring pages before credits.
        # Source scenes at 0-based indexes [4] and [13] from the 19-scene list (pages 4-22):
        #   index 4  → page_4 + 4 = page_8  (5th  story scene)
        #   index 13 → page_4 + 13 = page_17 (14th story scene)
        page_spec.append(("coloring", 8))           # Page 23 — coloring A (scene index 4 = page_8)
        page_spec.append(("coloring", 17))          # Page 24 — coloring B (scene index 13 = page_17)
    page_spec.append(("credits", None))             # Page 23/25 — credits
    page_spec.append(("blank", None))               # Page 24/26 — blank

    assert len(page_spec) == page_count, f"Expected {page_count} pages, got {len(page_spec)}"

    c = rl_canvas.Canvas(output_path, pagesize=(PAGE_W_PT, PAGE_H_PT))

    for idx, (ptype, pdata) in enumerate(page_spec):
        page_num = idx + 1
        if ptype == "blank":
            img = _blank_page()
            label = "blank"
        elif ptype == "credits":
            img = _generate_credits_page(child_name, language)
            label = "credits"
        elif ptype == "coloring":
            img = _load_coloring(pdata)
            label = f"coloring_from_page_{pdata}.jpg"
        else:
            img = _load_visor(pdata)
            label = f"page_{pdata}.jpg"

        print(f"[CP PDF] Content p{page_num:02d}/{page_count}: {ptype:<8} {label}")
        c.setPageSize((PAGE_W_PT, PAGE_H_PT))
        _embed_page(c, img)
        if idx < page_count - 1:
            c.showPage()
        img.close()

        if page_num % 5 == 0:
            gc.collect()

    c.save()
    gc.collect()

    size_mb = os.path.getsize(output_path) / 1024 / 1024
    print(f"[CP PDF] Content done: {output_path} ({size_mb:.1f} MB, {page_count} pages)")
    return output_path


def get_cp_pb_specs() -> dict:
    """Return CP casewrap photobook specifications."""
    spine_mm_26 = _calc_spine_mm(CW_PAGES_26)
    (cov_w_mm_26, cov_h_mm_26, cov_w_pt_26, cov_h_pt_26, _, _, _, _, _) = _calc_cover_dims(spine_mm_26)
    return {
        "product": "photobook_cw_a4_p_fc",
        "pages": CW_PAGES_SELECTED,
        "page_mm": f"{PAGE_W_MM}×{PAGE_H_MM}",
        "page_px": f"{PAGE_W_PX}×{PAGE_H_PX}",
        "page_pt": f"{PAGE_W_PT:.2f}×{PAGE_H_PT:.2f}",
        "cover_board_mm": f"{COV_TRIM_W_MM}×{COV_TRIM_H_MM}",
        "cover_spread_mm": f"{cov_w_mm_26:.1f}×{cov_h_mm_26:.1f}",
        "cover_pt": f"{cov_w_pt_26:.2f}×{cov_h_pt_26:.2f}",
        "spine_mm": round(spine_mm_26, 2),
        "wrap_mm": WRAP_MM,
        "bleed_mm": BLEED_MM,
        "dpi": DPI,
        "structure": {
            1: "blank",
            2: "portadilla (visor page_2)",
            3: "dedicatoria (visor page_3)",
            "4-22": "19 story scenes (visor page_4..page_22)",
            23: "coloring page A (scene page_8)",
            24: "coloring page B (scene page_17)",
            25: "credits",
            26: "blank",
        },
    }
