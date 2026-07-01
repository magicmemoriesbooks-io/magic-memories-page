"""
Community Stories Service — Cuentos Solidarios
Architecture:
  - Stories are identical for all readers. Zero personalization.
  - Images are NEVER modified. No Pillow text composition. No AI calls.
  - PDF: image placed as-is, text drawn ON TOP via ReportLab.
  - Viewer: two absolute-positioned CSS divs (top + bottom) matching PDF coordinates.
  - Coordinate spec: base 1086×1448px (imágenes 3:4 entregadas por la autora).
      TOP    x=80 y=22   w=926 h=183  Nunito ExtraBold 40px  #1A8AB5
      BOTTOM x=80 y=1228 w=926 h=200  Nunito ExtraBold 38px  #1A8AB5
      Alturas FIJAS para todas las páginas — no modificar.
      Si la imagen cambia el difuminado, sólo se ajusta el contenido de la DB,
      nunca las coordenadas del servicio.
  - No backgrounds, no shadows, no dark boxes. Images provide their own blur zones.
Zero commercial integration. No PDF files stored on disk. Zero AI cost.

ESTÁNDAR APROBADO (fijado con ¿Por qué tiembla la Tierra?, jun 2026):
  Color:  #1A8AB5   (azul oscuro, legible sobre franjas claras)
  TOP:    40px ExtraBold  — máx ~2 líneas por zona
  BOTTOM: 38px ExtraBold  — máx ~3 líneas por zona
  Franjas beige detectadas automáticamente por análisis de brillo:
    TOP franja imagen: y=0→223   → zona segura y=22, h=183
    BOT franja imagen: y=1224→1448 → zona segura y=1228, h=200
"""

import os
import io
from typing import Optional

# ── Spec constants (base canvas 1086×1448px — imágenes 3:4) ──────────────────
_BASE_W  = 1086
_BASE_H  = 1448
_TEXT_COLOR = '#1A8AB5'

# Zonas fijas — coordenadas de impresión jul 2026
# TOP: y bajado de 22→65 para margen de seguridad de impresión (~12.6 mm desde borde)
_TOP_SPEC    = dict(x=80, y=65,   w=926, h=183, font='Nunito-ExtraBold',
                    sizes=[40, 38, 36], line_h=1.22)
_BOTTOM_SPEC = dict(x=80, y=1228, w=926, h=200, font='Nunito-ExtraBold',
                    sizes=[38, 36, 34], line_h=1.22)
# Bloque inferior página 10 — subido de 1228→1178 para margen inferior seguro (~9.7 mm desde borde)
_P10_BOT_SPEC = dict(x=80, y=1178, w=926, h=200, font='Nunito-ExtraBold',
                     sizes=[38, 36, 34], line_h=1.22)
# Bloque inferior página 6 (safety_measures) — texto largo 6 líneas; subido 48px respecto a p10
_P6_BOT_SPEC  = dict(x=80, y=1130, w=926, h=278, font='Nunito-ExtraBold',
                     sizes=[38, 36, 34], line_h=1.22)

# CSS percentages for viewer (pre-computed from spec)
_TOP_CSS = dict(
    left   = f"{80/_BASE_W*100:.3f}%",
    top    = f"{22/_BASE_H*100:.3f}%",
    width  = f"{926/_BASE_W*100:.3f}%",
    height = f"{183/_BASE_H*100:.3f}%",
)
_BOT_CSS = dict(
    left   = f"{80/_BASE_W*100:.3f}%",
    top    = f"{1228/_BASE_H*100:.3f}%",
    width  = f"{926/_BASE_W*100:.3f}%",
    height = f"{200/_BASE_H*100:.3f}%",
)


# ── Text helpers ──────────────────────────────────────────────────────────────

def get_page_top_text(page, lang: str = 'es') -> str:
    suffix = '_es' if lang == 'es' else '_en'
    return (getattr(page, f'text_top{suffix}') or '').strip()

def get_page_bottom_text(page, lang: str = 'es') -> str:
    suffix = '_es' if lang == 'es' else '_en'
    return (getattr(page, f'text_bottom{suffix}') or '').strip()

def render_page_text_unified(page, lang: str = 'es') -> str:
    """Legacy combined text — kept for backward compat. Use get_page_top/bottom_text instead."""
    top    = get_page_top_text(page, lang)
    bottom = get_page_bottom_text(page, lang)
    return '\n\n'.join(t for t in (top, bottom) if t)

def page_css_coords(page) -> dict:
    """Legacy single-block coords — kept for backward compat."""
    return {'left': _TOP_CSS['left'], 'top': _TOP_CSS['top'],
            'font_color': _TEXT_COLOR, 'text_align': 'center'}

def page_dual_coords() -> dict:
    """Return CSS coordinates for the two text zones (spec-based, same for all pages)."""
    return {'top': _TOP_CSS, 'bottom': _BOT_CSS, 'color': _TEXT_COLOR}


def render_page_preview(img_path: str, top_text: str, bottom_text: str, out_path: str, bottom_spec=None) -> str:
    """
    Genera preview PNG con texto superpuesto usando las zonas y fuentes estándar.
    Usa las constantes fijas _TOP_SPEC / _BOTTOM_SPEC / _TEXT_COLOR.
    Retorna out_path si éxito, lanza excepción si falla.

    Uso rápido en cualquier sesión futura:
        from services.community_stories_service import render_page_preview
        render_page_preview('static/.../pageNN/scene.png', top_text, bot_text, 'out.png')
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        raise RuntimeError('Pillow no instalado — pip install Pillow')

    BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    FONT_PATH = os.path.join(BASE_DIR, 'static', 'fonts', 'Nunito-ExtraBold.ttf')

    def _wrap_and_draw(draw, text, spec, color):
        if not text:
            return
        chosen_size = spec['sizes'][0]
        chosen_lines = []
        chosen_lh = int(chosen_size * spec['line_h'])
        for size in spec['sizes']:
            font = ImageFont.truetype(FONT_PATH, size)
            lh   = int(size * spec['line_h'])
            lines, cur = [], ''
            for word in text.split():
                test = (cur + ' ' + word).strip()
                if draw.textlength(test, font=font) <= spec['w'] - 4:
                    cur = test
                else:
                    if cur: lines.append(cur)
                    cur = word
            if cur: lines.append(cur)
            chosen_size, chosen_lines, chosen_lh = size, lines, lh
            if len(lines) * lh <= spec['h']:
                break
        font = ImageFont.truetype(FONT_PATH, chosen_size)
        start_y = spec['y'] + 8
        for i, line in enumerate(chosen_lines):
            tw = draw.textlength(line, font=font)
            x  = spec['x'] + (spec['w'] - tw) // 2
            draw.text((x, start_y + i * chosen_lh), line, fill=color, font=font)

    img  = Image.open(img_path).convert('RGBA')
    draw = ImageDraw.Draw(img)
    _wrap_and_draw(draw, top_text,    _TOP_SPEC,    _TEXT_COLOR)
    _wrap_and_draw(draw, bottom_text, bottom_spec or _BOTTOM_SPEC, _TEXT_COLOR)
    img.convert('RGB').save(out_path, 'PNG', dpi=(150, 150))
    return out_path


def get_page_image_path(image_file: str) -> Optional[str]:
    """
    Resolve image_file (relative to /static/) to absolute filesystem path.
    Returns None and logs the exact missing path for admin diagnosis.
    """
    if not image_file:
        print('[COMMUNITY] MISSING RESOURCE: image_file field is empty for a page. '
              'Check CommunityStoryPage.image_file in the DB.')
        return None
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base, 'static', image_file.lstrip('/'))
    if not os.path.exists(path):
        print(
            f'[COMMUNITY] MISSING RESOURCE: image file not found on disk.\n'
            f'  DB field  : {image_file}\n'
            f'  Full path : {path}\n'
            f'  Action    : Upload the file to that path, or update the DB record.'
        )
        return None
    return path


# ── PDF rendering — pure ReportLab, images untouched ─────────────────────────

def _register_nunito_fonts():
    """Register Nunito TTF fonts with ReportLab (safe to call multiple times)."""
    try:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        font_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                'static', 'fonts')
        for name, fname in [('Nunito-ExtraBold', 'Nunito-ExtraBold.ttf'),
                             ('Nunito-SemiBold',  'Nunito-SemiBold.ttf')]:
            try:
                pdfmetrics.registerFont(TTFont(name, os.path.join(font_dir, fname)))
            except Exception:
                pass
    except Exception:
        pass


def _image_rect_on_page(page_w, page_h, img_w=_BASE_W, img_h=_BASE_H):
    """Return (ix,iy,iw,ih) of image as placed by preserveAspectRatio=True anchor='c'."""
    img_ar  = img_w / img_h
    page_ar = page_w / page_h
    if img_ar <= page_ar:
        draw_h = page_h;  draw_w = draw_h * img_ar
    else:
        draw_w = page_w;  draw_h = draw_w / img_ar
    return (page_w - draw_w) / 2, (page_h - draw_h) / 2, draw_w, draw_h


def _wrap_text_rl(text, font_name, font_size, max_width, canvas_obj):
    lines = []
    for para in text.split('\n'):
        words = para.split()
        if not words:
            continue
        cur = ''
        for word in words:
            test = f'{cur} {word}'.strip()
            try:
                w = canvas_obj.stringWidth(test, font_name, font_size)
            except Exception:
                w = len(test) * font_size * 0.55
            if w <= max_width:
                cur = test
            else:
                if cur:
                    lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
    return lines or ['']


def _rl_draw_spec_text(c, text, spec, ix, iy, iw, ih):
    """
    Draw text per spec (TOP or BOTTOM). No backgrounds, no shadows.
    ix,iy,iw,ih: actual image rect on page (ReportLab origin = bottom-left).
    """
    if not text:
        return
    sx = iw / _BASE_W;  sy = ih / _BASE_H
    box_x   = ix + spec['x'] * sx
    box_w   = spec['w'] * sx
    box_h   = spec['h'] * sy
    box_top_rl = iy + ih - spec['y'] * sy
    box_bot_rl = box_top_rl - box_h

    r, g, b = (int(_TEXT_COLOR.lstrip('#')[i:i+2], 16) / 255 for i in (0, 2, 4))

    for fsize_raw in spec['sizes']:
        fsize = max(8, round(fsize_raw * sy))
        fn = spec['font']
        try:
            c.setFont(fn, fsize)
        except Exception:
            fn = 'Helvetica-Bold' if 'Extra' in fn else 'Helvetica'
            c.setFont(fn, fsize)
        lines = _wrap_text_rl(text, fn, fsize, box_w, c)
        lh    = fsize * spec['line_h']
        total = len(lines) * lh
        if total <= box_h or fsize_raw == spec['sizes'][-1]:
            y_top = min(box_top_rl, box_top_rl - (box_h - total) / 2)
            c.saveState()
            c.setFillColorRGB(r, g, b)
            for i, line in enumerate(lines):
                try:
                    lw = c.stringWidth(line, fn, fsize)
                except Exception:
                    lw = len(line) * fsize * 0.55
                lx = box_x + (box_w - lw) / 2
                ly = y_top - (i + 1) * lh
                c.drawString(lx, ly, line)
            c.restoreState()
            break


def get_community_pdf_image_list(slug: str, lang: str) -> list:
    """
    Return an ordered list of absolute image paths for a community story PDF.

    PAGE_CATALOG is the single source of truth for image selection.
    CommunityStoryPage.image_file is intentionally NOT read here — it is
    legacy metadata kept only for admin display and compatibility.

    Args:
        slug: story slug, e.g. 'venezuela-terremoto'
        lang: 'es' or 'en'

    Returns:
        List of absolute filesystem paths (one per page, in order).
    """
    if slug != STORY_SLUG:
        raise ValueError(f'[COMMUNITY PDF] Unknown story slug: {slug!r}')

    _rel_base = os.path.join(
        'static', 'images', 'community_stories',
        slug.replace('-', '_'),
    )

    scene_key = 'scene_es' if lang == 'es' else 'scene_en'
    paths = []
    for entry in sorted(PAGE_CATALOG, key=lambda e: e['num']):
        rel = entry.get(scene_key) or entry.get('scene_es', '')
        if rel:
            paths.append(os.path.join(_rel_base, rel))
        else:
            print(f"[COMMUNITY PDF] Warning: no image for page {entry['num']} ({lang})")
    return paths


# ── PAGE_CATALOG — fuente única de verdad ─────────────────────────────────────
#
# REGLA: Ninguna ruta de archivo de este cuento puede aparecer fuera de esta
# estructura. Si cambia un nombre de archivo, solo se modifica aquí.
#
# Campos por entrada:
#   id        — identificador semántico permanente (no depende del número de página)
#   num       — posición en la secuencia de lectura (puede cambiar sin mover archivos)
#   type      — 'A' fija | 'B' fondo+texto baked | 'C' imagen especial
#   subtype   — portadilla | standard | bottom_wide | pizarra | None
#   label_es/en — etiqueta descriptiva para logs y diagnóstico
#
#   Rutas (relativas a static/images/community_stories/venezuela_terremoto/):
#     base      — fondo limpio para baking y PDF
#     bg_es/bg_en — fondo de portadilla con logo (solo tipo B/portadilla)
#     scene_es  — imagen final ES para el visor
#     scene_en  — imagen final EN para el visor
#     pdf_base  — ruta que usa la BD/PDF (imagen base para ReportLab)
#
#   Textos para baking (tipos B estándar y bottom_wide):
#     top_es/top_en     — texto zona superior
#     bot_es/bot_en     — texto zona inferior
#
#   Narración para TTS (independiente del texto baked):
#     narr_es/narr_en
#
#   bot_spec  — override del BOTTOM_SPEC (solo página 14, zona más amplia)
#   render    — True si el sistema debe generar scene_es/scene_en
#
# Para añadir, eliminar o reordenar una página: editar solo este catálogo.

STORY_SLUG = 'venezuela-terremoto'

# Override de zona inferior para página 14 (mural — zona más amplia)
# y=1048 (+88px = +1.5 cm a 150 DPI respecto al valor original 960)
_P14_BOT_SPEC = dict(x=80, y=1048, w=926, h=370, font='Nunito-ExtraBold',
                     sizes=[38, 36, 34], line_h=1.22)

# Textos de la portadilla EN (párrafos sobre fondo bg_en)
_PORTADILLA_EN_TITLE = 'You know, my love...'
_PORTADILLA_EN_PARAS = [
    ('Inside each person there is an immense light that never stops shining. '
     'Maybe you cannot see it, but if you take a moment and listen calmly, '
     'you will feel it deep in your heart.'),
    ('When we feel afraid, that light reminds us that we can always find calm, '
     'hope, and the strength to keep moving forward. '
     'Many people call this inner strength faith.'),
    ('In moments like this, more than ever, you can take refuge in it, '
     'knowing that it will bring you comfort, serenity and hope.'),
    ('In this story, you will not only discover why the Earth sometimes shakes. '
     'You will also understand that this light lives in every person who helps, '
     'accompanies, protects and lends a hand when we need it most.'),
]

# Textos de la pizarra (tipo C) — coordenadas especiales, hashtag en rojo
_PIZARRA_ES_TEXT = (
    '¡Ahora tú también puedes enviar un mensaje de cariño! '
    'No importa si estás en otro país o si nunca has vivido un terremoto. '
    'Tu dibujo, lleno de alegría, puede ayudar a otros niños que hoy necesitan un abrazo. '
    'Si decides compartirlo, usa el hashtag #niñosvalientes '
    'para que ningún niño se sienta solo.'
)
_PIZARRA_ES_HASHTAG = '#niñosvalientes'
_PIZARRA_ES_MAX_W   = 620

_PIZARRA_EN_TEXT = (
    'Now you can also send a message of love! '
    "It doesn't matter if you live in another country or have never experienced an earthquake. "
    'Your drawing, full of joy, can help other children who need a hug today. '
    'If you decide to share it, use the hashtag #bravechildren '
    'so no child feels alone.'
)
_PIZARRA_EN_HASHTAG = '#bravechildren'
_PIZARRA_EN_MAX_W   = 700

PAGE_CATALOG = [
    # ── Página 01 — Portada (TIPO A) ─────────────────────────────────────────
    # Imagen terminada entregada por la autora. Nunca regenerar.
    {
        'id':       'cover',
        'num':      1,
        'type':     'A',
        'subtype':  None,
        'label_es': 'Portada',
        'label_en': 'Cover',
        'base':     None,
        'bg_es':    None,
        'bg_en':    None,
        'scene_es': 'page01/scene.png',
        'scene_en': 'page01/scene_en.png',
        'pdf_base': 'page01/scene.png',
        'top_es':   None,
        'bot_es':   None,
        'top_en':   None,
        'bot_en':   None,
        'narr_es':  '',
        'narr_en':  '',
        'bot_spec': None,
        'render':   False,
    },

    # ── Página 02 — Portadilla (TIPO B, subtype: portadilla) ─────────────────
    # Fondo con logo proporcionado por la autora. El sistema escribe los párrafos.
    # ES: page02_preview.png ya existe (baked por autora). EN: se genera sobre bg_en.
    {
        'id':       'portadilla',
        'num':      2,
        'type':     'B',
        'subtype':  'portadilla',
        'label_es': 'Portadilla',
        'label_en': 'Title page',
        'base':     None,
        'bg_es':    'page02_preview_bg.png',
        'bg_en':    'page02_preview_bg_en.png',
        'scene_es': 'page02_preview.png',
        'scene_en': 'page02_preview_en.png',
        'pdf_base': 'page02_preview.png',
        'top_es':   None,
        'bot_es':   None,
        'top_en':   None,
        'bot_en':   None,
        'narr_es':  '',
        'narr_en':  '',
        'bot_spec': None,
        'render':   True,
    },

    # ── Páginas 03–13 — Escenas narrativas (TIPO B, subtype: standard) ────────
    # Fondo limpio entregado por la autora. Sistema bake texto arriba y abajo.
    {
        'id':       'earth_puzzle',
        'num':      3,
        'type':     'B',
        'subtype':  'standard',
        'label_es': 'La Tierra como rompecabezas',
        'label_en': 'Earth like a puzzle',
        'base':     'page03/scene.png',
        'bg_es':    None,
        'bg_en':    None,
        'scene_es': 'page03/scene_es.png',
        'scene_en': 'page03/scene_en.png',
        'pdf_base': 'page03/scene.png',
        'top_es':   'Mira profundamente bajo nuestros pies. La Tierra es como un gigantesco rompecabezas.',
        'bot_es':   'Está formada por enormes piezas llamadas placas tectónicas, que encajan unas con otras como un inmenso rompecabezas.',
        'top_en':   'Look deep beneath our feet. The Earth is like one giant puzzle.',
        'bot_en':   'It is made of enormous pieces called tectonic plates, that fit together like a giant jigsaw.',
        'narr_es':  ('Mira profundamente bajo nuestros pies. La Tierra es como un gigantesco rompecabezas. '
                     'Está formada por enormes piezas llamadas placas tectónicas, que encajan unas con otras '
                     'como un inmenso rompecabezas.'),
        'narr_en':  ('Look deep beneath our feet. The Earth is like one giant puzzle. '
                     'It is made of enormous pieces called tectonic plates, '
                     'that fit together like a giant jigsaw.'),
        'bot_spec': None,
        'render':   True,
    },
    {
        'id':       'plates_move',
        'num':      4,
        'type':     'B',
        'subtype':  'standard',
        'label_es': 'Las placas se mueven',
        'label_en': 'The plates move',
        'base':     'page04/scene.png',
        'bg_es':    None,
        'bg_en':    None,
        'scene_es': 'page04/scene_es.png',
        'scene_en': 'page04/scene_en.png',
        'pdf_base': 'page04/scene.png',
        'top_es':   'Aunque no podamos verlo, esas enormes piezas se mueven muy despacito todos los días.',
        'bot_es':   'Así es nuestro planeta. A veces, las placas se empujan unas contra otras muy lentamente, debajo de nuestros pies.',
        'top_en':   "Even though we can't see it, those enormous pieces move very slowly every single day.",
        'bot_en':   'That is what our planet is like. Sometimes the plates push against each other very gently, beneath our feet.',
        'narr_es':  ('Aunque no podamos verlo, esas enormes piezas se mueven muy despacito todos los días. '
                     'Así es nuestro planeta. A veces, las placas se empujan unas contra otras muy lentamente, '
                     'debajo de nuestros pies.'),
        'narr_en':  ('Even though we cannot see it, those enormous pieces move very slowly every single day. '
                     'That is what our planet is like. Sometimes the plates push against each other '
                     'very gently, beneath our feet.'),
        'bot_spec': None,
        'render':   True,
    },
    {
        'id':       'energy_release',
        'num':      5,
        'type':     'B',
        'subtype':  'standard',
        'label_es': 'La energía se libera',
        'label_en': 'Energy is released',
        'base':     'page05/scene.png',
        'bg_es':    None,
        'bg_en':    None,
        'scene_es': 'page05/scene_es.png',
        'scene_en': 'page05/scene_en.png',
        'pdf_base': 'page05/scene.png',
        'top_es':   'Imagina que intentas mover un mueble muy pesado y, de repente, consigue deslizarse de golpe.',
        'bot_es':   'Algo parecido ocurre bajo la Tierra. Cuando las placas logran moverse de repente, la energía se libera y sentimos un temblor o un terremoto.',
        'top_en':   'Imagine trying to move a very heavy piece of furniture and, suddenly, it slides.',
        'bot_en':   'Something similar happens beneath the Earth. When the plates suddenly move, energy is released and we feel a tremor or earthquake.',
        'narr_es':  ('Imagina que intentas mover un mueble muy pesado y, de repente, consigue deslizarse de golpe. '
                     'Algo parecido ocurre bajo la Tierra. Cuando las placas logran moverse de repente, '
                     'la energía se libera y sentimos un temblor o un terremoto.'),
        'narr_en':  ('Imagine trying to move a very heavy piece of furniture and, suddenly, it slides. '
                     'Something similar happens beneath the Earth. When the plates suddenly move, '
                     'energy is released and we feel a tremor or earthquake.'),
        'bot_spec': None,
        'render':   True,
    },
    # ── Página 06 — Tres medidas de seguridad (NUEVA, jul 2026) ────────────────
    {
        'id':       'safety_measures',
        'num':      6,
        'type':     'B',
        'subtype':  'standard',
        'label_es': 'Tu súper poder para protegerte',
        'label_en': 'Your super power to stay safe',
        'base':     'safety_measures/scene.png',
        'bg_es':    None,
        'bg_en':    None,
        'scene_es': 'safety_measures/scene_es.png',
        'scene_en': 'safety_measures/scene_en.png',
        'pdf_base': 'safety_measures/scene.png',
        'top_es':   ('Tu súper poder para protegerte. '
                     'Si alguna vez sientes que la Tierra empieza a temblar, tú tienes un súper poder '
                     'para protegerte. Recuerda estos tres pasos: ¡Agáchate, Cúbrete y Sujétate!'),
        'bot_es':   ('Si estás cerca de una mesa fuerte, métete debajo y sujétate bien a una de sus patas. '
                     'Si estás en la cama, quédate allí, hazte pequeñito y protege tu cabeza con la almohada. '
                     'Cuando el temblor termine, sigue siempre las indicaciones del adulto que te cuida. '
                     '¡Juntos estaréis más seguros!'),
        'top_en':   ('Your Super Power to Stay Safe. '
                     'If you ever feel the Earth begin to shake, you have a super power to help keep yourself safe. '
                     'Remember these three steps: Drop, Cover, and Hold On!'),
        'bot_en':   ('If you are near a sturdy table, get underneath it and hold on tightly to one of its legs. '
                     'If you are in bed, stay there, curl up into a little ball, and protect your head with your pillow. '
                     'When the shaking stops, always follow the instructions of the grown-up who is taking care of you. '
                     "Together, you'll be safer!"),
        'narr_es':  ('Tu súper poder para protegerte. '
                     'Si alguna vez sientes que la Tierra empieza a temblar, tú tienes un súper poder '
                     'para protegerte. Recuerda estos tres pasos: ¡Agáchate, Cúbrete y Sujétate! '
                     'Si estás cerca de una mesa fuerte, métete debajo y sujétate bien a una de sus patas. '
                     'Si estás en la cama, quédate allí, hazte pequeñito y protege tu cabeza con la almohada. '
                     'Cuando el temblor termine, sigue siempre las indicaciones del adulto que te cuida. '
                     '¡Juntos estaréis más seguros!'),
        'narr_en':  ('Your Super Power to Stay Safe. '
                     'If you ever feel the Earth begin to shake, you have a super power to help keep yourself safe. '
                     'Remember these three steps: Drop, Cover, and Hold On! '
                     'If you are near a sturdy table, get underneath it and hold on tightly to one of its legs. '
                     'If you are in bed, stay there, curl up into a little ball, and protect your head with your pillow. '
                     'When the shaking stops, always follow the instructions of the grown-up who is taking care of you. '
                     "Together, you'll be safer!"),
        'bot_spec': _P6_BOT_SPEC,
        'render':   True,
    },
    {
        'id':       'normal_fear',
        'num':      7,
        'type':     'B',
        'subtype':  'standard',
        'label_es': 'Es normal sentir miedo',
        'label_en': 'It is normal to feel afraid',
        'base':     'page06/scene.png',
        'bg_es':    None,
        'bg_en':    None,
        'scene_es': 'page06/scene_es.png',
        'scene_en': 'page06/scene_en.png',
        'pdf_base': 'page06/scene.png',
        'top_es':   'Es normal sentir miedo o confusión cuando la Tierra se mueve con tanta fuerza.',
        'bot_es':   'Nuestro cuerpo reacciona porque siente que el suelo, que siempre parecía tan firme, ha cambiado de repente.',
        'top_en':   'It is normal to feel afraid or confused when the Earth moves with such force.',
        'bot_en':   'Our body reacts because it feels that the ground, which always seemed so firm, has suddenly changed.',
        'narr_es':  ('Es normal sentir miedo o confusión cuando la Tierra se mueve con tanta fuerza. '
                     'Nuestro cuerpo reacciona porque siente que el suelo, que siempre parecía tan firme, '
                     'ha cambiado de repente.'),
        'narr_en':  ('It is normal to feel afraid or confused when the Earth moves with such force. '
                     'Our body reacts because it feels that the ground, which always seemed so firm, '
                     'has suddenly changed.'),
        'bot_spec': None,
        'render':   True,
    },
    {
        'id':       'heart_racing',
        'num':      8,
        'type':     'B',
        'subtype':  'standard',
        'label_es': 'Tu corazón late rápido',
        'label_en': 'Your heart is racing',
        'base':     'page07/scene.png',
        'bg_es':    None,
        'bg_en':    None,
        'scene_es': 'page07/scene_es.png',
        'scene_en': 'page07/scene_en.png',
        'pdf_base': 'page07/scene.png',
        'top_es':   'Tal vez tu corazón late muy rápido, o tienes ganas de llorar o de buscar un abrazo.',
        'bot_es':   'Tu cuerpo solo te está diciendo: "¡Ey! Esto es nuevo y me pone nervioso". ¡Es una respuesta completamente normal!',
        'top_en':   'Maybe your heart is beating fast, or you feel like crying or looking for a hug.',
        'bot_en':   'Your body is simply telling you: "Hey! This is new and it makes me nervous." That is a completely normal response!',
        'narr_es':  ('Tal vez tu corazón late muy rápido, o tienes ganas de llorar o de buscar un abrazo. '
                     'Tu cuerpo solo te está diciendo: ¡Ey! Esto es nuevo y me pone nervioso. '
                     '¡Es una respuesta completamente normal!'),
        'narr_en':  ('Maybe your heart is beating fast, or you feel like crying or looking for a hug. '
                     'Your body is simply telling you: Hey! This is new and it makes me nervous. '
                     'That is a completely normal response!'),
        'bot_spec': None,
        'render':   True,
    },
    {
        'id':       'all_feelings',
        'num':      9,
        'type':     'B',
        'subtype':  'standard',
        'label_es': 'Todo lo que sientes está bien',
        'label_en': 'Everything you feel is okay',
        'base':     'page08/scene.png',
        'bg_es':    None,
        'bg_en':    None,
        'scene_es': 'page08/scene_es.png',
        'scene_en': 'page08/scene_en.png',
        'pdf_base': 'page08/scene.png',
        'top_es':   'Todo lo que sientes —miedo, enojo, angustia o tristeza— está bien.',
        'bot_es':   'Tu cuerpo y tu mente solo están intentando protegerte y decirte que necesitas buscar un lugar seguro.',
        'top_en':   'Everything you feel — fear, anger, worry or sadness — is okay.',
        'bot_en':   'Your body and mind are just trying to protect you and telling you to find a safe place.',
        'narr_es':  ('Todo lo que sientes —miedo, enojo, angustia o tristeza— está bien. '
                     'Tu cuerpo y tu mente solo están intentando protegerte y decirte que necesitas '
                     'buscar un lugar seguro.'),
        'narr_en':  ('Everything you feel — fear, anger, worry or sadness — is okay. '
                     'Your body and mind are just trying to protect you '
                     'and telling you to find a safe place.'),
        'bot_spec': None,
        'render':   True,
    },
    {
        'id':       'breathe',
        'num':      10,
        'type':     'B',
        'subtype':  'standard',
        'label_es': 'Respira profundo',
        'label_en': 'Breathe deeply',
        'base':     'page09/scene.png',
        'bg_es':    None,
        'bg_en':    None,
        'scene_es': 'page09/scene_es.png',
        'scene_en': 'page09/scene_en.png',
        'pdf_base': 'page09/scene.png',
        'top_es':   '¡Escucha bien! Todo lo que sientes es muy válido. No hay nada de malo en estar asustado.',
        'bot_es':   'Respira profundo, como si inflaras un globo muy despacito, hasta que la calma regrese poco a poco.',
        'top_en':   'Listen! Everything you feel is very valid. There is nothing wrong with being scared.',
        'bot_en':   'Breathe deeply, like slowly inflating a balloon, until calm returns little by little.',
        'narr_es':  ('¡Escucha bien! Todo lo que sientes es muy válido. No hay nada de malo en estar asustado. '
                     'Respira profundo, como si inflaras un globo muy despacito, '
                     'hasta que la calma regrese poco a poco.'),
        'narr_en':  ('Listen! Everything you feel is very valid. There is nothing wrong with being scared. '
                     'Breathe deeply, like slowly inflating a balloon, until calm returns little by little.'),
        'bot_spec': None,
        'render':   True,
    },
    {
        'id':       'questions',
        'num':      11,
        'type':     'B',
        'subtype':  'standard',
        'label_es': 'Es normal tener preguntas',
        'label_en': 'It is normal to have questions',
        'base':     'page10/scene.png',
        'bg_es':    None,
        'bg_en':    None,
        'scene_es': 'page10/scene_es.png',
        'scene_en': 'page10/scene_en.png',
        'pdf_base': 'page10/scene.png',
        'top_es':   'También es normal tener muchas preguntas: "¿Estamos bien?", "¿Por qué pasó esto?", "¿Mi familia está bien?" o "¿Y mis amigos?".',
        'bot_es':   'Preguntar nos ayuda a entender mejor lo que está pasando. Y aunque los adultos no siempre tengamos todas las respuestas, puedes preguntar todas las veces que necesites.',
        'top_en':   'It is also normal to have many questions: "Are we okay?", "Why did this happen?", "Is my family safe?" or "What about my friends?"',
        'bot_en':   "Asking helps us better understand what is happening. Even if adults don't always have all the answers, you can ask as many times as you need.",
        'narr_es':  ('También es normal tener muchas preguntas: ¿Estamos bien?, ¿Por qué pasó esto?, '
                     '¿Mi familia está bien? o ¿Y mis amigos? '
                     'Preguntar nos ayuda a entender mejor lo que está pasando. Y aunque los adultos no '
                     'siempre tengamos todas las respuestas, puedes preguntar todas las veces que necesites.'),
        'narr_en':  ('It is also normal to have many questions: Are we okay?, Why did this happen?, '
                     'Is my family safe? or What about my friends? '
                     'Asking helps us better understand what is happening. Even if adults do not always '
                     'have all the answers, you can ask as many times as you need.'),
        'bot_spec': _P10_BOT_SPEC,
        'render':   True,
    },
    {
        'id':       'heroes',
        'num':      12,
        'type':     'B',
        'subtype':  'standard',
        'label_es': 'Hay héroes trabajando',
        'label_en': 'There are heroes at work',
        'base':     'page11/scene.png',
        'bg_es':    None,
        'bg_en':    None,
        'scene_es': 'page11/scene_es.png',
        'scene_en': 'page11/scene_en.png',
        'pdf_base': 'page11/scene.png',
        'top_es':   '¡Recuerda que no estás solo! Hay muchos héroes trabajando para que todo vuelva a estar bien.',
        'bot_es':   'Personas valientes cuidan de nosotros, revisan que las casas sean seguras y ayudan a proteger a todas las familias.',
        'top_en':   'Remember, you are not alone! There are many heroes working to make everything okay again.',
        'bot_en':   'Brave people are taking care of us, checking that homes are safe and helping to protect all families.',
        'narr_es':  ('¡Recuerda que no estás solo! Hay muchos héroes trabajando para que todo vuelva a estar bien. '
                     'Personas valientes cuidan de nosotros, revisan que las casas sean seguras '
                     'y ayudan a proteger a todas las familias.'),
        'narr_en':  ('Remember, you are not alone! There are many heroes working to make everything okay again. '
                     'Brave people are taking care of us, checking that homes are safe '
                     'and helping to protect all families.'),
        'bot_spec': None,
        'render':   True,
    },
    {
        'id':       'rebuild',
        'num':      13,
        'type':     'B',
        'subtype':  'standard',
        'label_es': 'Reconstruimos juntos',
        'label_en': 'We rebuild together',
        'base':     'page13/scene.png',
        'bg_es':    None,
        'bg_en':    None,
        'scene_es': 'page13/scene_es.png',
        'scene_en': 'page13/scene_en.png',
        'pdf_base': 'page13/scene.png',
        'top_es':   'A veces nuestra ciudad pasa por momentos difíciles, pero lo más bonito es ver cómo todos nos unimos.',
        'bot_es':   'Limpiamos, reparamos y nos ayudamos, paso a paso, para que nuestra ciudad y nuestro país vuelvan a ser un lugar seguro.',
        'top_en':   'Sometimes our city goes through difficult moments, but the most beautiful thing is seeing how we all come together.',
        'bot_en':   'We clean, repair and help each other, step by step, so that our city and our country become a safe place again.',
        'narr_es':  ('A veces nuestra ciudad pasa por momentos difíciles, pero lo más bonito es ver cómo '
                     'todos nos unimos. Limpiamos, reparamos y nos ayudamos, paso a paso, para que nuestra '
                     'ciudad y nuestro país vuelvan a ser un lugar seguro.'),
        'narr_en':  ('Sometimes our city goes through difficult moments, but the most beautiful thing is '
                     'seeing how we all come together. We clean, repair and help each other, step by step, '
                     'so that our city and our country become a safe place again.'),
        'bot_spec': None,
        'render':   True,
    },

    # ── Página 14 — Mural de cierre (TIPO B, subtype: bottom_wide) ────────────
    # Solo texto inferior, con zona más amplia que el estándar.
    {
        'id':       'hope_mural',
        'num':      14,
        'type':     'B',
        'subtype':  'bottom_wide',
        'label_es': 'Mural de esperanza',
        'label_en': 'Mural of hope',
        'base':     'page14/scene.png',
        'bg_es':    None,
        'bg_en':    None,
        'scene_es': 'page14/scene_es.png',
        'scene_en': 'page14/scene_en.png',
        'pdf_base': 'page14/scene.png',
        'top_es':   None,
        'bot_es':   ('Aunque el mundo cambie, siempre hay esperanza si nos cuidamos los unos a los otros. '
                     'Siempre encontramos la manera de salir adelante. '
                     'Siempre habrá un mañana y, lo más importante, siempre seguiremos adelante juntos.'),
        'top_en':   None,
        'bot_en':   ('Even when the world changes, there is always hope when we take care of each other. '
                     'We always find a way forward. There will always be a tomorrow and, most importantly, '
                     'we will always move forward together.'),
        'narr_es':  ('Aunque el mundo cambie, siempre hay esperanza si nos cuidamos los unos a los otros. '
                     'Siempre encontramos la manera de salir adelante. Siempre habrá un mañana y, '
                     'lo más importante, siempre seguiremos adelante juntos.'),
        'narr_en':  ('Even when the world changes, there is always hope when we take care of each other. '
                     'We always find a way forward. There will always be a tomorrow and, most importantly, '
                     'we will always move forward together.'),
        'bot_spec': _P14_BOT_SPEC,
        'render':   True,
    },

    # ── Página 15 — Pizarra de niños (TIPO C) ─────────────────────────────────
    # Tablero en blanco entregado por la autora.
    # El sistema escribe texto centrado con hashtag en rojo.
    {
        'id':       'board',
        'num':      15,
        'type':     'C',
        'subtype':  'pizarra',
        'label_es': 'Pizarra de niños',
        'label_en': "Children's board",
        'base':     'page15/scene.png',
        'bg_es':    None,
        'bg_en':    None,
        'scene_es': 'page15/scene_es.png',
        'scene_en': 'page15/scene_en.png',
        'pdf_base': 'page15/scene.png',
        'top_es':   None,
        'bot_es':   None,
        'top_en':   None,
        'bot_en':   None,
        'narr_es':  '',
        'narr_en':  '',
        'bot_spec': None,
        'render':   True,
    },

    # ── Página 16 — Guía para padres (TIPO A) ─────────────────────────────────
    # Imagen terminada entregada por la autora. Nunca regenerar.
    {
        'id':       'parents',
        'num':      16,
        'type':     'A',
        'subtype':  None,
        'label_es': 'Guía para padres',
        'label_en': "Parents' guide",
        'base':     None,
        'bg_es':    None,
        'bg_en':    None,
        'scene_es': 'page16/scene_es.png',
        'scene_en': 'page16/scene_en.png',
        'pdf_base': 'page16/scene_es.png',
        'top_es':   None,
        'bot_es':   None,
        'top_en':   None,
        'bot_en':   None,
        'narr_es':  '',
        'narr_en':  '',
        'bot_spec': None,
        'render':   False,
    },
]


# ── Image baking ──────────────────────────────────────────────────────────────

def bake_page(entry: dict, lang: str) -> None:
    """
    Generate the baked image for one PAGE_CATALOG entry and one language.

    Decision tree by type:
      A          → skip (image provided by author, never regenerate)
      B/portadilla → special paragraph rendering (portadilla logic)
      B/standard   → render_page_preview(base, top, bot)
      B/bottom_wide → render_page_preview(base, None, bot, bot_spec)
      C/pizarra    → special board rendering with hashtag in red

    Idempotent: skips if the output file already exists.
    """
    if not entry.get('render', False):
        return

    _BASE = os.path.abspath('static/images/community_stories/venezuela_terremoto')
    out_rel = entry['scene_es'] if lang == 'es' else entry['scene_en']
    out_abs = os.path.join(_BASE, out_rel)

    if os.path.exists(out_abs):
        return  # already baked — idempotent

    ptype   = entry['type']
    subtype = entry.get('subtype')

    # ── TYPE A: never touch ───────────────────────────────────────────────────
    if ptype == 'A':
        return

    # ── TYPE B: render_page_preview ──────────────────────────────────────────
    if ptype == 'B':
        if subtype == 'portadilla':
            _bake_portadilla(entry, lang, out_abs)
        elif subtype in ('standard', 'bottom_wide'):
            base_abs = os.path.join(_BASE, entry['base'])
            if not os.path.exists(base_abs):
                print(f'[COMMUNITY BAKE] Base image missing: {entry["base"]} (id={entry["id"]}, lang={lang})')
                return
            top = entry[f'top_{lang}']
            bot = entry[f'bot_{lang}']
            render_page_preview(base_abs, top, bot, out_abs, bottom_spec=entry.get('bot_spec'))
            print(f'[COMMUNITY BAKE] {entry["id"]} ({lang}) → {out_rel}')
        return

    # ── TYPE C: pizarra ───────────────────────────────────────────────────────
    if ptype == 'C' and subtype == 'pizarra':
        base_abs = os.path.join(_BASE, entry['base'])
        if not os.path.exists(base_abs):
            print(f'[COMMUNITY BAKE] Base image missing: {entry["base"]} (id={entry["id"]}, lang={lang})')
            return
        _bake_pizarra(base_abs, out_abs, lang)
        print(f'[COMMUNITY BAKE] {entry["id"]} ({lang}) → {out_rel}')


def _bake_portadilla(entry: dict, lang: str, out_abs: str) -> None:
    """Render portadilla: title + 4 paragraphs over the author's background image."""
    _BASE = os.path.abspath('static/images/community_stories/venezuela_terremoto')
    bg_key = f'bg_{lang}'
    bg_rel = entry.get(bg_key)
    if not bg_rel:
        print(f'[COMMUNITY BAKE] Portadilla bg_{lang} missing in catalog')
        return
    bg_abs = os.path.join(_BASE, bg_rel)
    if not os.path.exists(bg_abs):
        print(f'[COMMUNITY BAKE] Portadilla background not found: {bg_rel}')
        return

    if lang == 'en':
        title = _PORTADILLA_EN_TITLE
        paras = _PORTADILLA_EN_PARAS
    else:
        print(f'[COMMUNITY BAKE] Portadilla ES provided by author — skipping regeneration')
        return

    try:
        from PIL import Image, ImageDraw, ImageFont
        BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        FONT_PATH = os.path.join(BASE_DIR, 'static', 'fonts', 'Nunito-ExtraBold.ttf')

        img  = Image.open(bg_abs).convert('RGBA')
        W, H = img.size
        draw = ImageDraw.Draw(img)

        color      = (26, 138, 181)
        font_title = ImageFont.truetype(FONT_PATH, 42)
        font_body  = ImageFont.truetype(FONT_PATH, 30)

        def _centered(text, y, font):
            tw = draw.textlength(text, font=font)
            draw.text(((W - tw) / 2, y), text, fill=color, font=font)

        def _wrapped_centered(text, y_start, font, max_w, line_h):
            words = text.split()
            cur, lines = '', []
            for w in words:
                test = (cur + ' ' + w).strip()
                if draw.textlength(test, font=font) <= max_w:
                    cur = test
                else:
                    if cur:
                        lines.append(cur)
                    cur = w
            if cur:
                lines.append(cur)
            for i, ln in enumerate(lines):
                tw = draw.textlength(ln, font=font)
                draw.text(((W - tw) / 2, y_start + i * line_h), ln, fill=color, font=font)
            return y_start + len(lines) * line_h

        max_w = W - 200
        y = 82
        _centered(title, y, font_title)
        y += 68
        for para in paras:
            y = _wrapped_centered(para, y, font_body, max_w, 38)
            y += 24

        img.convert('RGB').save(out_abs, 'PNG', dpi=(150, 150))
        print(f'[COMMUNITY BAKE] portadilla ({lang}) → {os.path.basename(out_abs)}')
    except Exception as _e:
        print(f'[COMMUNITY BAKE] Error baking portadilla {lang}: {_e}')


def _bake_pizarra(base_abs: str, out_abs: str, lang: str) -> None:
    """
    Render pizarra (board) image: erase any existing text zone, write new text
    centered on the board with the hashtag in red.
    """
    if lang == 'es':
        full_text = _PIZARRA_ES_TEXT
        hashtag   = _PIZARRA_ES_HASHTAG
        max_w     = _PIZARRA_ES_MAX_W
    else:
        full_text = _PIZARRA_EN_TEXT
        hashtag   = _PIZARRA_EN_HASHTAG
        max_w     = _PIZARRA_EN_MAX_W

    try:
        from PIL import Image, ImageDraw, ImageFont
        BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        FONT_PATH = os.path.join(BASE_DIR, 'static', 'fonts', 'Nunito-ExtraBold.ttf')

        img  = Image.open(base_abs).convert('RGB')
        W, H = img.size
        draw = ImageDraw.Draw(img)

        # Sin rectángulo de borrado — el fondo base ya es tablero limpio
        # y=530 es el inicio del área blanca del tablero (los dibujos pegados terminan ~y=510)
        color_main = (26, 138, 181)
        color_hash = (210, 50, 50)
        font       = ImageFont.truetype(FONT_PATH, 40)
        lh         = 54

        words = full_text.split()
        lines, cur = [], ''
        for word in words:
            test = (cur + ' ' + word).strip()
            if draw.textlength(test, font=font) <= max_w:
                cur = test
            else:
                if cur:
                    lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)

        y = 530
        for line in lines:
            if hashtag in line:
                parts = line.split(hashtag)
                full_w = draw.textlength(line, font=font)
                x = (W - full_w) / 2
                if parts[0]:
                    draw.text((x, y), parts[0], fill=color_main, font=font)
                    x += draw.textlength(parts[0], font=font)
                draw.text((x, y), hashtag, fill=color_hash, font=font)
                x += draw.textlength(hashtag, font=font)
                if parts[1]:
                    draw.text((x, y), parts[1], fill=color_main, font=font)
            else:
                tw = draw.textlength(line, font=font)
                draw.text(((W - tw) / 2, y), line, fill=color_main, font=font)
            y += lh

        img.save(out_abs, 'PNG', dpi=(150, 150))
    except Exception as _e:
        print(f'[COMMUNITY BAKE] Error baking pizarra ({lang}): {_e}')


def bake_community_en_images():
    """
    Bake all community story images that need rendering (both ES and EN).
    Called by prepare_community_visor_qs() on every startup.
    Idempotent: bake_page() skips files that already exist.
    """
    for entry in PAGE_CATALOG:
        if entry.get('render'):
            bake_page(entry, 'es')
            bake_page(entry, 'en')


# ── Visor builder ─────────────────────────────────────────────────────────────

def prepare_community_visor_qs():
    """
    Create generations/visor_qs/venezuela-terremoto-{es,en}/ so the story
    plays in the MMB visor_qs viewer (music + TTS narration + page-flip).
    Uses symlinks to raw scene images — no copies, no Pillow.
    Safe to call on every startup; skips when already current.
    """
    import json

    _BASE      = os.path.abspath('static/images/community_stories/venezuela_terremoto')
    _VISOR_DIR = os.path.abspath('generations/visor_qs')
    _MUSIC     = 'venezuela_terremoto_bg.mp3'
    _VERSION   = '8'  # jul 2026: safety_measures page added, calm_returns removed

    bake_community_en_images()

    # Build image map and narration arrays from PAGE_CATALOG
    # Fallback: if scene_es/scene_en doesn't exist on disk, use base image
    _sorted = sorted(PAGE_CATALOG, key=lambda e: e['num'])

    _IMGS = []
    for entry in _sorted:
        pnum    = entry['num']
        es_rel  = entry['scene_es']
        en_rel  = entry['scene_en']
        es_abs  = os.path.join(_BASE, es_rel)
        en_abs  = os.path.join(_BASE, en_rel)
        base    = entry.get('base')

        # Use baked image if it exists; otherwise fall back to base (clean background)
        img_es = es_rel if os.path.exists(es_abs) else (base or es_rel)
        img_en = en_rel if os.path.exists(en_abs) else (base or en_rel)

        _IMGS.append((pnum, img_es, img_en))

    _NARR_ES = [e['narr_es'] for e in _sorted]
    _NARR_EN = [e['narr_en'] for e in _sorted]

    def _build(lang, narr, title):
        visor_id  = f'venezuela-terremoto-{lang}'
        visor_dir = os.path.join(_VISOR_DIR, visor_id)
        vfile     = os.path.join(visor_dir, '.version')
        if os.path.exists(vfile):
            with open(vfile) as f:
                if f.read().strip() == _VERSION:
                    return
        os.makedirs(visor_dir, exist_ok=True)
        pages = []
        for i, (pnum, img_es, img_en) in enumerate(_IMGS):
            img_rel  = img_en if lang == 'en' else img_es
            img_abs  = os.path.join(_BASE, img_rel)
            ext      = os.path.splitext(img_rel)[1]
            fname    = f'page_{pnum:02d}{ext}'
            lpath    = os.path.join(visor_dir, fname)
            if os.path.lexists(lpath):
                os.remove(lpath)
            if os.path.exists(img_abs):
                os.symlink(img_abs, lpath)
            narr_text = narr[i] if i < len(narr) else ''
            pages.append({'image': fname,
                          'text':      '',
                          'narration': narr_text})
        meta = {
            'title': title, 'child_name': '', 'language': lang,
            'pages': pages,
            'aspect_ratio': round(1086 / 1448, 4),
            'visor_type': 'visor_qs', 'download_pdf': None,
            'music': _MUSIC, 'created': visor_id,
            'expires_at': None, 'is_gift': False,
            'site_url': 'https://magicmemoriesbooks.com', 'is_birthday': False,
        }
        with open(os.path.join(visor_dir, 'metadata.json'), 'w', encoding='utf-8') as fh:
            json.dump(meta, fh, ensure_ascii=False, indent=2)
        with open(vfile, 'w') as fh:
            fh.write(_VERSION)
        print(f'[COMMUNITY VISOR] Ready: visor_qs/{visor_id} (v{_VERSION})')

    os.makedirs(_VISOR_DIR, exist_ok=True)
    _build('es', _NARR_ES, '¿Por qué tiembla la Tierra?')
    _build('en', _NARR_EN, 'Why Does the Earth Shake?')


# ── Story seeding ─────────────────────────────────────────────────────────────

def seed_venezuela_story():
    """
    Create the Venezuela earthquake community story if it doesn't exist.
    Slug: 'venezuela-terremoto' (hyphen). Safe to call on every startup.
    Reads all page data from PAGE_CATALOG.
    """
    from models import db, CommunityStory, CommunityStoryPage

    _CURRENT_VERSION = 3  # bump when pages or texts change

    # Legacy seed fields stored in DB (used by older CSS overlay renderer)
    _SEED_FONT_SIZE  = 18
    _SEED_FONT_COLOR = _TEXT_COLOR
    _SEED_ALIGN      = 'center'
    _SEED_BOX        = (0.07, 0.02, 0.86, 0.13)  # x, y, w, h as percentages

    base_img = 'images/community_stories/venezuela_terremoto/'

    def _insert_pages(story_id):
        for entry in sorted(PAGE_CATALOG, key=lambda e: e['num']):
            page = CommunityStoryPage(
                story_id=story_id,
                page_number=entry['num'],
                image_file=base_img + entry['pdf_base'],
                text_top_es=entry.get('top_es'),
                text_top_en=entry.get('top_en'),
                text_center_es=None,
                text_center_en=None,
                text_bottom_es=entry.get('bot_es'),
                text_bottom_en=entry.get('bot_en'),
                font='Nunito-ExtraBold',
                font_size=_SEED_FONT_SIZE,
                font_color=_SEED_FONT_COLOR,
                text_alignment=_SEED_ALIGN,
                text_box_x=_SEED_BOX[0],
                text_box_y=_SEED_BOX[1],
                text_box_width=_SEED_BOX[2],
                text_box_height=_SEED_BOX[3],
            )
            db.session.add(page)

    existing = CommunityStory.query.filter_by(slug=STORY_SLUG).first()
    if existing:
        existing.title_es = '¿Por qué tiembla la Tierra?'
        existing.title_en = 'Why Does the Earth Shake?'
        existing.description_es = 'Un cuento solidario sobre terremotos y esperanza'
        existing.description_en = 'A solidarity story about earthquakes and hope'
        existing.cover_image = 'images/community_stories/venezuela_terremoto/cover.jpg'
        existing.status = 'published'
        if (existing.content_version or 0) < _CURRENT_VERSION:
            CommunityStoryPage.query.filter_by(story_id=existing.id).delete()
            _insert_pages(existing.id)
            existing.content_version = _CURRENT_VERSION
            print(f'[COMMUNITY] Pages re-seeded to v{_CURRENT_VERSION} for "{STORY_SLUG}".')
        db.session.commit()
        return existing

    story = CommunityStory(
        slug=STORY_SLUG,
        title_es='¿Por qué tiembla la Tierra?',
        title_en='Why Does the Earth Shake?',
        description_es='Un cuento solidario sobre terremotos y esperanza',
        description_en='A solidarity story about earthquakes and hope',
        cause='earthquake',
        status='published',
        content_version=_CURRENT_VERSION,
        cover_image='images/community_stories/venezuela_terremoto/cover.jpg',
    )
    db.session.add(story)
    db.session.flush()
    _insert_pages(story.id)
    db.session.commit()
    print(f'[COMMUNITY] Story "{STORY_SLUG}" seeded (v{_CURRENT_VERSION}).')
    return story
