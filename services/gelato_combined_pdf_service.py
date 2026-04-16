"""
Gelato Combined PDF Generator
Builds the single PDF file required by Gelato's photobook API.

Gelato requires ONE PDF file (submitted via fileUrl) containing:
  Page 1     : Full wraparound cover spread (478×326mm = 1354.96×924.09 pt)
  Page 2     : Blank end paper – inside front cover (210×280mm)
  Pages 3-32 : 30 interior pages (210×280mm)
  Pages 33-34: Blank end papers – inside back cover (210×280mm)
Total: 34 pages

The `pageCount` sent in the order API is 30 (interior only).
Gelato confirms: querying cover-dimensions with pageCount=30 returns pagesCount=34.

Source PDFs:
  Cover : generated/gelato/<session>/cover_wrap.pdf  (1 page, 478×326mm)
  Interior: generated/gelato/<session>/interior_30p.pdf (30 pages, 210×280mm)

Output:
  generated/gelato/<session>/combined_34p.pdf
"""

import os
import gc
import json
from io import BytesIO

INTERIOR_PT_W = 595.28    # 210mm at 72dpi/mm
INTERIOR_PT_H = 793.70    # 280mm
COVER_PT_W    = 1354.96   # 478mm
COVER_PT_H    = 924.09    # 326mm
RENDER_DPI    = 150       # render PDFs at 150dpi (sufficient; originals are 300dpi)


def _count_pdf_pages(pdf_path: str) -> int:
    """Return the number of pages in a PDF."""
    try:
        from PyPDF2 import PdfReader
        return len(PdfReader(pdf_path).pages)
    except Exception:
        return 30   # safe default


def _render_pdf_pages(pdf_path: str, dpi: int = RENDER_DPI) -> list:
    """
    Render all pages of a PDF as PIL Images using pdf2image (poppler).
    Returns list of PIL.Image in RGB mode.
    """
    from pdf2image import convert_from_path
    return convert_from_path(pdf_path, dpi=dpi, fmt="jpeg")


def _embed_pil_image(canvas_obj, pil_img, pt_w: float, pt_h: float) -> None:
    """Embed a PIL image filling the current reportlab canvas page."""
    from reportlab.lib.utils import ImageReader
    from PIL import Image

    if pil_img.mode != "RGB":
        pil_img = pil_img.convert("RGB")
    buf = BytesIO()
    pil_img.save(buf, format="JPEG", quality=90)
    buf.seek(0)
    canvas_obj.drawImage(ImageReader(buf), 0, 0, width=pt_w, height=pt_h)


def generate_gelato_combined_pdf(
    book_session_id: str,
    book_title: str = None,
    book_id: str = None,
    output_path: str = None,
    force_regenerate: bool = False,
) -> str:
    """
    Build the single combined PDF required by Gelato's photobook API.

    Args:
        book_session_id: visor_pb session ID (e.g. '2c4b15676b5a')
        book_title:      Book title (auto-detected from metadata if None)
        book_id:         Book type key (auto-detected if None)
        output_path:     Output PDF path (auto-generated if None)
        force_regenerate: Regenerate source PDFs even if they already exist

    Returns:
        Absolute path to the combined PDF
    """
    from reportlab.pdfgen import canvas as rl_canvas

    pages_dir = os.path.join("generations", "visor_pb", book_session_id)
    if not os.path.isdir(pages_dir):
        raise FileNotFoundError(f"Session directory not found: {pages_dir}")

    # --- Output path ---
    if output_path is None:
        out_dir = os.path.join("generated", "gelato", book_session_id)
        os.makedirs(out_dir, exist_ok=True)
        output_path = os.path.join(out_dir, "combined_34p.pdf")
    else:
        dirpath = os.path.dirname(output_path)
        if dirpath:
            os.makedirs(dirpath, exist_ok=True)

    # --- Resolve metadata ---
    if book_id is None or book_title is None:
        meta_path = os.path.join(pages_dir, "metadata.json")
        if os.path.exists(meta_path):
            try:
                with open(meta_path) as f:
                    meta = json.load(f)
                if book_id is None:
                    book_id = meta.get("book_id", "magic_chef")
                if book_title is None:
                    book_title = meta.get("title", "Magic Memories Books")
            except Exception:
                pass
        if book_id is None:
            book_id = "magic_chef"
        if book_title is None:
            book_title = "Magic Memories Books"

    # --- Ensure interior PDF exists ---
    interior_path = os.path.join("generated", "gelato", book_session_id, "interior_30p.pdf")
    if not os.path.exists(interior_path) or force_regenerate:
        print(f"[GELATO COMBINED] Generating interior PDF...")
        from services.gelato_pdf_service import generate_gelato_interior_pdf
        gender = "nina"
        child_name_meta = ""
        language_meta = "es"
        meta_path = os.path.join(pages_dir, "metadata.json")
        if os.path.exists(meta_path):
            try:
                with open(meta_path) as f:
                    meta = json.load(f)
                gender = meta.get("gender", "nina")
                child_name_meta = meta.get("child_name", "")
                language_meta = meta.get("language", "es")
            except Exception:
                pass
        generate_gelato_interior_pdf(
            book_session_id,
            child_name=child_name_meta,
            gender=gender,
            language=language_meta,
            book_id=book_id,
        )

    # --- Ensure cover wrap PDF exists ---
    cover_path = os.path.join("generated", "gelato", book_session_id, "cover_wrap.pdf")
    if not os.path.exists(cover_path) or force_regenerate:
        print(f"[GELATO COMBINED] Generating cover wrap PDF...")
        from services.gelato_cover_pdf_service import generate_gelato_cover_pdf
        generate_gelato_cover_pdf(
            book_session_id=book_session_id,
            book_title=book_title,
            book_id=book_id,
        )

    print(f"[GELATO COMBINED] Rendering PDFs at {RENDER_DPI} DPI...")
    print(f"  Cover:    {cover_path}")
    print(f"  Interior: {interior_path}")

    # --- Render source PDFs to PIL images ---
    cover_pages    = _render_pdf_pages(cover_path,    dpi=RENDER_DPI)
    interior_pages = _render_pdf_pages(interior_path, dpi=RENDER_DPI)

    print(f"[GELATO COMBINED] Cover pages rendered:    {len(cover_pages)}")
    print(f"[GELATO COMBINED] Interior pages rendered: {len(interior_pages)}")

    interior_count = len(interior_pages)
    total_pages = 1 + 1 + interior_count + 2  # cover + front endpaper + interior + back endpapers
    print(f"[GELATO COMBINED] Building combined PDF: {total_pages} pages total")

    # --- Build combined PDF ---
    c = rl_canvas.Canvas(output_path)

    # Page 1 — Cover wrap (478×326mm)
    c.setPageSize((COVER_PT_W, COVER_PT_H))
    _embed_pil_image(c, cover_pages[0], COVER_PT_W, COVER_PT_H)
    c.showPage()
    print(f"[GELATO COMBINED] ✓ Page 1: cover wrap ({COVER_PT_W:.1f}×{COVER_PT_H:.1f}pt)")

    del cover_pages
    gc.collect()

    # Page 2 — Blank end paper (inside front cover)
    c.setPageSize((INTERIOR_PT_W, INTERIOR_PT_H))
    c.setFillColorRGB(1, 1, 1)
    c.rect(0, 0, INTERIOR_PT_W, INTERIOR_PT_H, fill=1, stroke=0)
    c.showPage()
    print(f"[GELATO COMBINED] ✓ Page 2: blank end paper (inside front cover)")

    # Pages 3 – (2+interior_count) — 30 interior pages
    for i, page_img in enumerate(interior_pages):
        c.setPageSize((INTERIOR_PT_W, INTERIOR_PT_H))
        _embed_pil_image(c, page_img, INTERIOR_PT_W, INTERIOR_PT_H)
        c.showPage()
        if (i + 1) % 5 == 0:
            print(f"[GELATO COMBINED]   Interior {i+1}/{interior_count}...")
            gc.collect()

    print(f"[GELATO COMBINED] ✓ Pages 3-{2+interior_count}: {interior_count} interior pages")

    del interior_pages
    gc.collect()

    # Pages (3+interior_count) and (4+interior_count) — Blank end papers (inside back cover)
    for ep in range(2):
        c.setPageSize((INTERIOR_PT_W, INTERIOR_PT_H))
        c.setFillColorRGB(1, 1, 1)
        c.rect(0, 0, INTERIOR_PT_W, INTERIOR_PT_H, fill=1, stroke=0)
        c.showPage()
    print(f"[GELATO COMBINED] ✓ Pages {3+interior_count}-{4+interior_count}: blank end papers (inside back cover)")

    c.save()
    gc.collect()

    size_mb = os.path.getsize(output_path) / 1024 / 1024
    print(f"[GELATO COMBINED] Done: {output_path} ({size_mb:.1f} MB, {total_pages} pages)")
    return output_path


def get_combined_pdf_specs() -> dict:
    """Return the spec summary for the combined PDF."""
    return {
        "format": "Single combined PDF for Gelato photobook API",
        "structure": {
            "page_1": "Cover wrap — 478×326mm (1354.96×924.09pt)",
            "page_2": "Blank end paper — 210×280mm (inside front cover)",
            "pages_3_32": "30 interior pages — 210×280mm",
            "pages_33_34": "Blank end papers — 210×280mm (inside back cover)",
        },
        "total_pages": 34,
        "api_pageCount": 30,
        "cover_source": "cover_wrap.pdf (generated by gelato_cover_pdf_service)",
        "interior_source": "interior_30p.pdf (generated by gelato_pdf_service)",
        "render_dpi": RENDER_DPI,
    }
