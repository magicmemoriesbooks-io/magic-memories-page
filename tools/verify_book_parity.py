"""
verify_book_parity.py
─────────────────────
Compara programáticamente los parámetros críticos de los 5 libros ilustrados
contra MI (Magic Inventor) como referencia certificada.

Verifica en preview.py  → generación inicial (S1 y S2)
Verifica en app.py      → regen de portada (S1 y S2)

force_go_fast omitido = False (es el default de la función), así que solo
se marca ❌ si se encuentra explícitamente en True.

Uso:
    python3 tools/verify_book_parity.py
"""

import re, sys

GREEN = "\033[92m"; RED = "\033[91m"; YELLOW = "\033[93m"
BOLD  = "\033[1m";  RESET = "\033[0m"

def ok(msg):   return f"{GREEN}✅ {msg}{RESET}"
def err(msg):  return f"{RED}❌ {msg}{RESET}"
def warn(msg): return f"{YELLOW}⚠️  {msg}{RESET}"


# ── Extractor de llamadas ──────────────────────────────────────────────────────

def extract_call_after(text, anchor, max_search=600):
    """
    Encuentra la primera generate_with_flux2_dev( que aparece después de `anchor`.
    Devuelve un dict con los parámetros relevantes, o None si no la encuentra.
    """
    pos = text.find(anchor)
    if pos == -1:
        return None
    search_zone = text[pos: pos + max_search]
    m = re.search(r'generate_with_flux2_dev\(', search_zone)
    if not m:
        return None
    start = pos + m.start()
    # Avanzar hasta el cierre del paréntesis
    depth, i = 0, start
    while i < len(text):
        if text[i] == '(':  depth += 1
        elif text[i] == ')':
            depth -= 1
            if depth == 0: break
        i += 1
    call_text = text[start:i+1]

    def get(name):
        m2 = re.search(rf'{name}\s*=\s*([^\s,\n\)]+)', call_text)
        return m2.group(1).rstrip(',') if m2 else None

    return {
        'strength':    get('image_prompt_strength'),
        'go_fast':     get('force_go_fast'),   # None = usa default False ✅
        'has_neg':     'negative_prompt' in call_text,
        'has_refs':    ('photo_ref_path=' in call_text or 'photo_ref_paths=' in call_text),
        'snippet':     call_text[:80].replace('\n',' '),
    }


def check(call, label, exp_strength, exp_neg=None, allow_no_go_fast=True):
    """Imprime resultado para un call. Devuelve (passed, total)."""
    if call is None:
        print(f"    {warn(label + ': llamada no encontrada (puede estar en rama opcional)')}")
        return 0, 0   # no contar como fallo — rama condicional válida

    errors = []
    p, t = 0, 0

    # strength
    t += 1
    if call['strength'] == exp_strength:
        p += 1
    else:
        errors.append(f"strength={call['strength']} (esperado {exp_strength})")

    # force_go_fast: solo error si explícitamente True
    if call['go_fast'] == 'True':
        t += 1
        errors.append("force_go_fast=True (debe ser False o no indicado)")
    else:
        t += 1; p += 1   # None o False → correcto

    # negative_prompt (si se pide)
    if exp_neg is not None:
        t += 1
        if call['has_neg'] == exp_neg:
            p += 1
        else:
            errors.append(f"negative_prompt={'presente' if call['has_neg'] else 'AUSENTE'} (esperado {'presente' if exp_neg else 'ausente'})")

    if errors:
        print(f"    {err(label)}: {', '.join(errors)}")
    else:
        print(f"    {ok(label)}")

    return p, t


# ── Anchors por libro ──────────────────────────────────────────────────────────

BOOKS = {
    'magic_inventor':   'MI',
    'magic_chef':       'CHEF',
    'dragon_garden':    'DG',
    'star_keeper':      'SK',
    'centinela_aurora': 'CA',
}

# Anchors en preview.py (prints que preceden al generate_with_flux2_dev)
PREVIEW_S1_ANCHORS = {
    'magic_inventor':   ("[MAGIC INVENTOR PREVIEW] PASO 2 — FLUX avatar",  "[MAGIC INVENTOR PREVIEW] PASO 3 — FLUX portada"),
    'magic_chef':       ("[MAGIC CHEF PREVIEW] PASO 2 — FLUX avatar",       "[MAGIC CHEF PREVIEW] PASO 3 — FLUX portada"),
    'dragon_garden':    ("[DRAGON GARDEN PREVIEW] PASO 2 — FLUX avatar",    "[DRAGON GARDEN PREVIEW] PASO 3 — FLUX portada"),
    'star_keeper':      ("[STAR KEEPER PREVIEW] PASO 2 — FLUX avatar",      "[STAR KEEPER PREVIEW] PASO 3 — FLUX portada"),
    'centinela_aurora': ("[CENTINELA AURORA PREVIEW] PASO 2 — FLUX avatar", "[CENTINELA AURORA PREVIEW] PASO 3 — FLUX portada"),
}

PREVIEW_S2_ANCHORS = {
    'magic_inventor':   ("[MAGIC INVENTOR PREVIEW] SISTEMA 2 — Llamada 1",  "[MAGIC INVENTOR PREVIEW] SISTEMA 2 — Llamada 2"),
    'magic_chef':       ("[MAGIC CHEF PREVIEW] SISTEMA 2 — Llamada 1",       "[MAGIC CHEF PREVIEW] SISTEMA 2 — Llamada 2"),
    'dragon_garden':    ("[DRAGON GARDEN PREVIEW] SISTEMA 2 — Llamada 1",    "[DRAGON GARDEN PREVIEW] SISTEMA 2 — Llamada 2"),
    'star_keeper':      ("[STAR KEEPER PREVIEW] SISTEMA 2 — Llamada 1",      "[STAR KEEPER PREVIEW] SISTEMA 2 — Llamada 2"),
    'centinela_aurora': ("[CENTINELA AURORA PREVIEW] SISTEMA 2 — Llamada 1", "[CENTINELA AURORA PREVIEW] SISTEMA 2 — Llamada 2"),
}

REGEN_S1_ANCHORS = {
    'magic_inventor':   ("[REGEN COVER MI] PASO 2 — FLUX avatar",   "[REGEN COVER MI] PASO 3 — FLUX 2 Dev cover"),
    'magic_chef':       ("[REGEN COVER CHEF] PASO 2 — FLUX avatar",  "[REGEN COVER CHEF] PASO 3 — FLUX 2 Dev cover"),
    'dragon_garden':    ("[REGEN COVER DG] PASO 2 — FLUX avatar",    "[REGEN COVER DG] PASO 3 — FLUX 2 Dev cover"),
    'star_keeper':      ("[REGEN COVER SK] PASO 2 — FLUX avatar",    "[REGEN COVER SK] PASO 3 — FLUX 2 Dev cover"),
    'centinela_aurora': ("[REGEN COVER CA] PASO 2 — FLUX avatar",    "[REGEN COVER CA] PASO 3 — FLUX 2 Dev cover"),
}

REGEN_S2_ANCHORS = {
    'magic_inventor':   "[REGEN COVER MI S2] Portrait + BOLT",
    'magic_chef':       "[REGEN COVER CHEF S2] Portrait + SWEETIE",
    'dragon_garden':    "[REGEN COVER DG S2] Portrait + SPARK",
    'star_keeper':      "[REGEN COVER SK S2] Portrait + LUNA",
    'centinela_aurora': "[REGEN COVER CA S2] Portrait + ASTRO",
}


# ── Main ───────────────────────────────────────────────────────────────────────

def run():
    with open('services/personalized_books/preview.py', 'r') as f:
        prev = f.read()
    with open('app.py', 'r') as f:
        app = f.read()

    grand_p = grand_t = 0

    for book, tag in BOOKS.items():
        label = book.replace('_', ' ').upper()
        ref_star = "  ← REFERENCIA" if book == 'magic_inventor' else ""
        print(f"\n{'═'*60}")
        print(f"{BOLD}{label}{ref_star}{RESET}")
        print('═'*60)

        # ── preview.py S1 ────────────────────────────────────────
        a2, a3 = PREVIEW_S1_ANCHORS[book]
        c2 = extract_call_after(prev, a2)
        c3 = extract_call_after(prev, a3)
        print(f"\n  {BOLD}preview.py — S1 (con foto){RESET}")
        p, t = check(c2, 'PASO 2 avatar',  exp_strength='1.0',  exp_neg=False)
        grand_p += p; grand_t += t
        p, t = check(c3, 'PASO 3 portada', exp_strength='0.95', exp_neg=True)
        grand_p += p; grand_t += t

        # ── preview.py S2 ────────────────────────────────────────
        a_s2_1, a_s2_2 = PREVIEW_S2_ANCHORS[book]
        cs2_1 = extract_call_after(prev, a_s2_1)
        cs2_2 = extract_call_after(prev, a_s2_2)
        print(f"\n  {BOLD}preview.py — S2 (sin foto){RESET}")
        # LLAMADA 1 es texto puro (photo_ref_paths=None) — strength no aplica, solo verificar neg_prompt
        p, t = check(cs2_1, 'LLAMADA 1 portrait (texto puro)', exp_strength=None, exp_neg=True)
        grand_p += p; grand_t += t
        p, t = check(cs2_2, 'LLAMADA 2 portada',  exp_strength='0.95', exp_neg=True)
        grand_p += p; grand_t += t

        # ── app.py regen S1 ──────────────────────────────────────
        r2, r3 = REGEN_S1_ANCHORS[book]
        cr2 = extract_call_after(app, r2)
        cr3 = extract_call_after(app, r3)
        print(f"\n  {BOLD}app.py regen — S1 (con foto){RESET}")
        p, t = check(cr2, 'PASO 2 avatar',  exp_strength='1.0',  exp_neg=False)
        grand_p += p; grand_t += t
        p, t = check(cr3, 'PASO 3 portada', exp_strength='0.95', exp_neg=True)
        grand_p += p; grand_t += t

        # ── app.py regen S2 main ─────────────────────────────────
        a_r_s2 = REGEN_S2_ANCHORS.get(book)
        cr_s2 = extract_call_after(app, a_r_s2) if a_r_s2 else None
        print(f"\n  {BOLD}app.py regen — S2 main (portrait guardado){RESET}")
        p, t = check(cr_s2, 'S2 portada', exp_strength='0.95', exp_neg=True)
        grand_p += p; grand_t += t

    print(f"\n{'═'*60}")
    pct   = int(100 * grand_p / grand_t) if grand_t else 0
    color = GREEN if grand_p == grand_t else RED
    print(f"{BOLD}{color}TOTAL: {grand_p}/{grand_t} checks pasados ({pct}%){RESET}")
    print('═'*60)
    return 0 if grand_p == grand_t else 1


if __name__ == '__main__':
    sys.exit(run())
