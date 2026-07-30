"""
Single reconstruction pipeline for personalized/illustrated books.

rebuild_book(preview_id) is the ONLY function that is allowed to derive
scene_paths / original_scene_paths / images / visor / PDFs / Cloudprinter
artifacts for a book. It is called after ANY event that changes a page or
cover image on disk (initial generation, admin regeneration, customer
regeneration, retry-after-failure). It does not know or care who called it,
whether the book is a gift, a paying customer's book, or a test book —
that distinction is authorization/quota logic that lives in the caller,
never here.

Design contract (see .agents/memory/admin-regen-pipeline-unification.md):
  1. The canonical source of truth for interior pages is the set of
     generated/composed_<preview_id>/page_NN.png files on disk — never an
     incrementally-patched array index.
  2. Every array field consumed anywhere in the app (scene_paths, images,
     original_images, original_scene_paths, all_pages_original,
     all_pages_preview) is rebuilt in full, every time, from that listing.
  3. The eBook (visor), the printable PDF, and the Cloudprinter PDFs are
     rebuilt from that same canonical listing via the exact functions the
     paid flow already uses (no duplicated composition logic).
  4. The cover spread/front/back cover are only regenerated through FLUX
     when the raw cover actually changed (mtime-based, same rule the
     paid flow already used) — never on every call, to avoid needless
     cost/drift when only an interior scene was regenerated.
"""

import os
import re
import json
import glob


PAGE_FILE_RE = re.compile(r'^page_(\d{2})\.png$')


def _fmt(path: str) -> str:
    path = path.replace('\\', '/')
    return path if path.startswith('/') else f'/{path}'


def _enumerate_pages(composed_dir: str):
    """Canonical listing of interior pages, derived ONLY from disk contents.

    Returns (original_paths, preview_paths) sorted by page number, where
    preview_paths uses the watermarked variant if present, else falls back
    to the original (post-payment books have no watermark).
    """
    if not os.path.isdir(composed_dir):
        return [], []

    numbered = []
    for fn in os.listdir(composed_dir):
        m = PAGE_FILE_RE.match(fn)
        if m:
            numbered.append((int(m.group(1)), fn))
    numbered.sort(key=lambda t: t[0])

    original_paths = []
    preview_paths = []
    for _, fn in numbered:
        original_full = os.path.join(composed_dir, fn)
        original_paths.append(original_full)
        preview_variant = os.path.join(composed_dir, fn.replace('.png', '_preview.png'))
        preview_paths.append(preview_variant if os.path.exists(preview_variant) else original_full)

    return original_paths, preview_paths


def _rebuild_cover_artifacts_if_needed(story_data: dict, preview_id: str, composed_dir: str) -> bool:
    """Rebuild front_cover/back_cover/cover_spread ONLY if cover_raw.png is
    newer than the last built cover_spread.png (i.e. a cover regeneration
    actually happened). Reuses generate_cover_spread() — the same function
    the paid flow already calls — instead of duplicating composition logic.

    Returns True if the cover artifacts were rebuilt.
    """
    from services.illustrated_book_service import generate_cover_spread, add_watermark

    cover_raw_path = story_data.get('cover_raw_path', '')
    cover_spread_path = story_data.get('cover_spread_path', '') or os.path.join(composed_dir, 'cover_spread.png')

    needs_rebuild = True
    if cover_raw_path and os.path.exists(cover_raw_path) and os.path.exists(cover_spread_path):
        needs_rebuild = os.path.getmtime(cover_raw_path) > os.path.getmtime(cover_spread_path)
    elif not (cover_raw_path and os.path.exists(cover_raw_path)):
        # No raw cover on disk at all — nothing to rebuild from, leave as-is.
        needs_rebuild = False

    if not needs_rebuild:
        return False

    story_id = story_data.get('story_id', '')
    from services.personalized_books.generation import get_personalized_book_id
    book_id = get_personalized_book_id(story_id)
    traits = story_data.get('traits', {})
    child_name = story_data.get('child_name', '')
    gender = story_data.get('gender', 'neutral')
    lang = story_data.get('lang', story_data.get('language', 'es'))
    author_name = story_data.get('author_name', 'Magic Memories Books')

    ref_path_2 = None
    is_furry = book_id in ('furry_love', 'furry_love_adventure', 'furry_love_teen', 'furry_love_adult')
    if is_furry:
        pet_preview = story_data.get('pet_preview_path', '')
        if pet_preview and os.path.exists(pet_preview.lstrip('/')):
            ref_path_2 = pet_preview.lstrip('/')

    # Single reference (cover_raw_path, no ref_path_2 for non-furry) triggers
    # the "reuse preview as cover" faithful-reproduction mode inside
    # generate_cover_spread — same convention the paid flow relies on.
    cover_spread = generate_cover_spread(
        traits, child_name, gender, lang, book_id, author_name,
        reference_image_path=cover_raw_path,
        reference_image_path_2=ref_path_2 if is_furry else None
    )

    DPI = 300
    MM_TO_INCH = 1 / 25.4
    wrap_px = int(19.05 * MM_TO_INCH * DPI)
    board_w_px = int(213.175 * MM_TO_INCH * DPI)
    spine_px = int(6.35 * MM_TO_INCH * DPI)
    front_x = wrap_px + board_w_px + spine_px

    front_cover = cover_spread.crop((front_x, wrap_px, front_x + board_w_px, wrap_px + int(303.35 * MM_TO_INCH * DPI)))
    back_cover = cover_spread.crop((wrap_px, wrap_px, wrap_px + board_w_px, wrap_px + int(303.35 * MM_TO_INCH * DPI)))

    os.makedirs(composed_dir, exist_ok=True)

    front_cover_path = os.path.join(composed_dir, 'front_cover.png')
    front_cover.save(front_cover_path, 'PNG')
    story_data['front_cover_path'] = _fmt(front_cover_path)

    back_cover_path = os.path.join(composed_dir, 'back_cover.png')
    back_cover.save(back_cover_path, 'PNG')
    story_data['back_cover_path'] = _fmt(back_cover_path)

    cover_preview_path = os.path.join(composed_dir, 'cover_preview.png')
    add_watermark(front_cover).save(cover_preview_path, 'PNG')
    story_data['cover_preview'] = _fmt(cover_preview_path)

    back_cover_preview_path = os.path.join(composed_dir, 'back_cover_preview.png')
    add_watermark(back_cover).save(back_cover_preview_path, 'PNG')
    story_data['back_cover_preview'] = _fmt(back_cover_preview_path)

    cover_spread.save(cover_spread_path, 'PNG')
    story_data['cover_spread_path'] = cover_spread_path

    print(f"[REBUILD] Cover spread rebuilt for {preview_id} (cover_raw.png was newer)")
    return True


def rebuild_book(preview_id: str, mark_composed: bool = True) -> dict:
    """The single reconstruction entrypoint. Rebuilds, in order:
      1. All interior-page path arrays, from disk.
      2. Cover artifacts, only if the raw cover changed.
      3. The eBook/visor (prepare_and_upload — same function the paid flow uses).
      4. The printable PDF.
      5. The Cloudprinter cover.pdf + content.pdf (cheap, no external API calls).
      6. Persists everything in ONE json write, with all stale PDF caches cleared.

    Never branches on admin_gift / customer / test — the only per-book
    parameter it reads is data already on story_data (want_ebook, etc.),
    used exactly the way the paid flow already uses it to pick is_gift for
    the visor's expiry policy.

    mark_composed: when True (default), sets the composition/approval state
    flags (pages_composed, book_scenes_ready, scenes_pending,
    scenes_generating) to signal "the book is composed and ready". This is
    correct for the real post-payment composition flow.
    When False, none of those four flags are touched at all — used by
    pre-approval/pre-payment regeneration endpoints (regenerate-cover,
    regenerate-page) so a customer regenerating a preview image can never
    accidentally flip the order's composition/approval state. All visual
    reconstruction (pages, cover, visor, PDFs) still runs unconditionally
    either way.
    """
    preview_path = f'story_previews/{preview_id}.json'
    if not os.path.exists(preview_path):
        raise FileNotFoundError(f'Preview not found: {preview_path}')

    with open(preview_path, 'r', encoding='utf-8') as f:
        story_data = json.load(f)

    composed_dir = f'generated/composed_{preview_id}'
    result = {'preview_id': preview_id, 'steps': []}

    # 1) Canonical interior pages from disk — replaces every manual array patch.
    original_paths, preview_paths = _enumerate_pages(composed_dir)
    if not original_paths:
        raise RuntimeError(f'No page_NN.png files found in {composed_dir} — cannot rebuild')

    # Pages 01-02 = portadilla, dedicatoria — fixed text pages, never scene illustrations.
    # generate_full_book() does NOT prepend cover/blank to the page_NN series; the
    # cover is saved separately as front_cover.png.  Real layout on disk:
    #   page_01 = portadilla, page_02 = dedicatoria,
    #   page_03 = escena 1, page_04 = escena 2, … page_21 = escena 19,
    #   page_22 = créditos, page_23 = blank (for_print=True)
    # Skipping 4 pages was wrong — it silently dropped escenas 1 and 2.
    content_original = original_paths[2:] if len(original_paths) > 2 else original_paths
    content_preview = preview_paths[2:] if len(preview_paths) > 2 else preview_paths

    formatted_original = [_fmt(p) for p in content_original]
    formatted_preview = [_fmt(p) for p in content_preview]
    all_original = [_fmt(p) for p in original_paths]
    all_preview = [_fmt(p) for p in preview_paths]

    story_data['scene_paths'] = formatted_original
    story_data['images'] = formatted_preview
    story_data['original_images'] = formatted_original
    story_data['original_scene_paths'] = all_original
    story_data['all_pages_original'] = all_original
    story_data['all_pages_preview'] = all_preview
    story_data['composed_pages_dir'] = composed_dir
    result['steps'].append(f'pages: {len(original_paths)} total, {len(content_original)} content scenes')

    # 2) Cover artifacts — only regenerated (via FLUX) when the raw cover changed.
    cover_rebuilt = _rebuild_cover_artifacts_if_needed(story_data, preview_id, composed_dir)
    result['steps'].append(f'cover rebuilt: {cover_rebuilt}')

    if mark_composed:
        story_data['pages_composed'] = True
        story_data['book_scenes_ready'] = True
        story_data['scenes_pending'] = False
        story_data['scenes_generating'] = False
        result['steps'].append('composition state flags set (mark_composed=True)')
    else:
        result['steps'].append('composition state flags SKIPPED (mark_composed=False)')

    # 3) eBook/visor — same function used by the paid flow, never duplicated.
    from services.vps_upload_service import prepare_and_upload
    is_gift = not bool(story_data.get('want_ebook', False)) or bool(story_data.get('admin_gift', False))
    visor_result = prepare_and_upload(story_data, preview_id, is_gift=is_gift)
    story_data['visor_url'] = visor_result.get('visor_url', story_data.get('visor_url', ''))
    story_data['visor_uuid'] = visor_result.get('book_uuid', story_data.get('visor_uuid', ''))
    story_data['visor_uploaded'] = True
    result['steps'].append(f"visor rebuilt: {visor_result.get('visor_url')}")

    # 4) Printable PDF — always rebuilt from the freshly-uploaded visor pages.
    try:
        from services.personalized_books.printable_pdf import generate_personalized_printable_pdf
        from services.personalized_books.generation import get_personalized_book_id, get_print_title
        story_id = story_data.get('story_id', '')
        book_id = get_personalized_book_id(story_id)
        lang = story_data.get('lang', story_data.get('language', 'es'))
        child_name = story_data.get('child_name', '')
        gender = story_data.get('gender', 'neutral')
        traits = story_data.get('traits', {})
        pet_name = traits.get('pet_name', '') if traits else ''
        book_title = get_print_title(book_id, child_name, lang, pet_name=pet_name)

        printable_path = generate_personalized_printable_pdf(
            book_session_id=preview_id,
            child_name=child_name,
            gender=gender,
            language=lang,
            book_id=book_id,
            book_title=book_title,
            force_regenerate=True,
        )
        story_data['pdf_printable_path'] = printable_path
        result['steps'].append(f'printable pdf rebuilt: {printable_path}')
    except Exception as e:
        print(f"[REBUILD] Printable PDF rebuild failed for {preview_id}: {e}")
        result['steps'].append(f'printable pdf FAILED: {e}')

    # Any previously-cached PDF must never be served stale again.
    story_data.pop('digital_pdf_path', None)
    story_data.pop('print_pdf_path', None)

    # 5) Cloudprinter PDFs — cheap (PIL/reportlab only, no external API calls),
    #    rebuilt unconditionally so a print submission never uses stale pages.
    try:
        from services.personalized_books.cp_pdf_service import generate_cw_cover_pdf, generate_cw_content_pdf
        from services.cloudprinter_api_service import get_pb_chosen_page_count
        chosen_pages = get_pb_chosen_page_count()
        cp_out_dir = os.path.join('generations', 'cloudprinter', preview_id)
        os.makedirs(cp_out_dir, exist_ok=True)
        cover_pdf_path = os.path.join(cp_out_dir, 'cover.pdf')
        content_pdf_path = os.path.join(cp_out_dir, 'content.pdf')

        generate_cw_cover_pdf(
            session_id=preview_id,
            book_title=book_title,
            output_path=cover_pdf_path,
            page_count=chosen_pages,
            story_id=book_id,
        )
        generate_cw_content_pdf(
            session_id=preview_id,
            child_name=child_name,
            language=lang,
            output_path=content_pdf_path,
            page_count=chosen_pages,
        )
        result['steps'].append('cloudprinter cover.pdf + content.pdf rebuilt')

        if story_data.get('cp_submitted') or story_data.get('lulu_submitted'):
            story_data['cp_needs_refresh'] = True
    except Exception as e:
        print(f"[REBUILD] Cloudprinter PDF rebuild skipped/failed for {preview_id}: {e}")
        result['steps'].append(f'cloudprinter pdf FAILED/skipped: {e}')

    # 6) One single, final, consistent write.
    # Re-read the JSON right before writing to avoid clobbering concurrent
    # updates (e.g. page_regenerations incremented by a second customer
    # regeneration that started while this rebuild was running its ~90s
    # FLUX / PDF generation steps).  Only the fields that rebuild_book
    # actually computed are copied over; everything else is taken from the
    # freshest on-disk state.
    _REBUILD_OWNED_FIELDS = (
        'scene_paths', 'images', 'original_images', 'original_scene_paths',
        'all_pages_original', 'all_pages_preview', 'composed_pages_dir',
        'visor_url', 'visor_uuid', 'visor_uploaded', 'pdf_printable_path',
        'front_cover_path', 'back_cover_path', 'cover_preview', 'back_cover_preview',
        'cover_spread_path', 'cp_needs_refresh',
    )
    # Composition/approval state flags are only "owned" by this write when
    # mark_composed=True. When False, they must be left completely alone —
    # not even re-copied from the (possibly stale) story_data snapshot taken
    # at the start of this call — so a regeneration can never move the
    # order's composition/approval state, in either direction.
    _COMPOSITION_STATE_FIELDS = (
        'pages_composed', 'book_scenes_ready', 'scenes_pending', 'scenes_generating',
    )
    if mark_composed:
        _REBUILD_OWNED_FIELDS = _REBUILD_OWNED_FIELDS + _COMPOSITION_STATE_FIELDS
    try:
        with open(preview_path, 'r', encoding='utf-8') as f:
            fresh_data = json.load(f)
        for _field in _REBUILD_OWNED_FIELDS:
            if _field in story_data:
                fresh_data[_field] = story_data[_field]
        fresh_data.pop('digital_pdf_path', None)
        fresh_data.pop('print_pdf_path', None)
    except Exception:
        fresh_data = story_data
        fresh_data.pop('digital_pdf_path', None)
        fresh_data.pop('print_pdf_path', None)

    with open(preview_path, 'w', encoding='utf-8') as f:
        json.dump(fresh_data, f, ensure_ascii=False, indent=2)

    result['success'] = True
    print(f"[REBUILD] rebuild_book({preview_id}) complete: {result['steps']}")
    return result
