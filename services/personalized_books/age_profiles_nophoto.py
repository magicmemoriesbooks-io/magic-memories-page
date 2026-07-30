# ============================================================
# SISTEMA 2 — SIN FOTO: Perfiles anatómicos para FLUX
# ============================================================
# Este archivo es EXCLUSIVO del pipeline sin fotografía.
# NO importar ni usar en el pipeline con foto (SISTEMA 1).
# El SISTEMA 1 usa services/age_profiles.py (Kontext).
#
# Arquitectura:
#   Texto → [FLUX portrait — Llamada 1] → portrait_path
#   portrait_path + compañero → [FLUX cover/escenas — Llamada 2]
#
# Llamada 1 usa: proportions + face + hair_note  (descripción completa)
# Llamada 2 usa: display + cover_ref             (solo referencia)
# ============================================================

AGE_PROFILE_NOPHOTO = {

    # ── 1 año — infant baby ─────────────────────────────────────────────────
    # Certificado: prueba visual Jul 2026
    "1": {
        "display": "1 year old infant baby",
        "proportions": (
            "head is one-third of total body height, enormous oversized round skull, "
            "round chubby belly, very short stubby arms and legs, "
            "pudgy chubby wrists and ankles, tiny feet"
        ),
        "face": (
            "enormous round eyes taking up half the face, tiny upturned button nose, "
            "very chubby rounded cheeks, soft smooth skin, soft round chin, "
            "absolutely no jawline, very small soft mouth, "
            "huge full rounded forehead, no neck at all head sits directly on body"
        ),
        "hair_note": (
            "very sparse fine baby hair, soft thin wispy texture, "
            "minimal coverage, very flat with almost no volume, "
            "soft gentle wisps close to scalp"
        ),
        "cover_ref": "preserve infant baby proportions from @image1",
    },

    # ── 2 años — baby toddler ───────────────────────────────────────────────
    # Certificado: prueba visual Jul 2026
    "2": {
        "display": "2 year old baby toddler",
        "proportions": (
            "head is one-third of total body height, oversized round skull, "
            "round chubby belly, very short stubby arms and legs, "
            "chubby wrists and ankles, tiny feet"
        ),
        "face": (
            "enormous round eyes taking up half the face, tiny upturned button nose, "
            "very chubby rounded cheeks, soft smooth skin, soft round chin, "
            "no jawline at all, very small soft mouth, "
            "full rounded forehead, almost no neck head rests directly on round shoulders"
        ),
        "hair_note": (
            "short wavy baby hair, soft wispy texture, "
            "low volume close to scalp, minimal coverage"
        ),
        "cover_ref": "preserve baby toddler proportions from @image1",
    },

    # ── 3-4 años — toddler ──────────────────────────────────────────────────
    # Certificado: prueba visual Jul 2026
    "3-4": {
        "display": "3 year old toddler",
        "proportions": (
            "head is one-quarter of total body height very large relative to body, "
            "compact chubby torso, short legs, chubby knees, pudgy hands, slight belly pouch"
        ),
        "face": (
            "very large round eyes, chubby apple cheeks, soft smooth skin, tiny upturned nose, "
            "soft undefined jawline, round soft chin, small mouth with baby teeth, "
            "prominent rounded forehead, very short neck almost invisible"
        ),
        "hair_note": None,
        "cover_ref": "preserve toddler proportions from @image1",
    },

    # ── 5 años — young child ★ CERTIFICADO ──────────────────────────────────
    # Certificado: mejor resultado de la sesión Jul 2026
    "5": {
        "display": "5 year old kindergarten-age child",
        "proportions": (
            "head is one-fifth of total body height still large for the body, "
            "compact short legs relative to torso, slight belly, small hands"
        ),
        "face": (
            "round pudgy cheeks with baby fat, soft undefined jawline, "
            "no chin point, no cheekbone definition, "
            "small upturned button nose, large round eyes taking up one-third of face, "
            "full baby lips, very short neck barely visible, head rests close to shoulders"
        ),
        "hair_note": None,
        "cover_ref": "preserve young child proportions from @image1",
    },

    # ── 6 años — first grade ────────────────────────────────────────────────
    # Certificado: prueba visual Jul 2026
    "6": {
        "display": "6 year old first grade child",
        "proportions": (
            "head is one-fifth of total body height still large for body, "
            "legs slightly longer than a 5 year old but still short and compact, "
            "small hands, slight belly"
        ),
        "face": (
            "soft rounded cheeks with minimal remaining baby fat, "
            "no defined jawline no sharp angles, small upturned nose, "
            "large round eyes, very soft round chin, full child lips, "
            "very short neck barely visible"
        ),
        "hair_note": None,
        "cover_ref": "preserve young child proportions from @image1",
    },

    # ── 7 años — second grade ───────────────────────────────────────────────
    "7": {
        "display": "7 year old second grade child",
        "proportions": (
            "head slightly under one-fifth of total body height, "
            "legs noticeably longer than a 6 year old but still compact, "
            "slim child torso, small hands, no belly"
        ),
        "face": (
            "soft rounded cheeks with very little remaining baby fat, "
            "no defined jawline no sharp angles, small slightly upturned nose, "
            "large round eyes, soft round chin, child lips, "
            "short neck barely visible"
        ),
        "hair_note": None,
        "cover_ref": "preserve young child proportions from @image1",
    },

    # ── 8-9 años — school-age child ─────────────────────────────────────────
    # Certificado: prueba visual Jul 2026
    "8-9": {
        "display": "8 year old school-age child",
        "proportions": (
            "head still noticeably large for body but less than a young child, "
            "longer legs, short neck just visible, "
            "compact school-age child body, small hands"
        ),
        "face": (
            "cheeks mostly slim but still with soft child roundness, "
            "very soft jaw with no sharp angles at all, small nose, "
            "large round child eyes, youthful child face, "
            "child teeth showing in smile"
        ),
        "hair_note": None,
        "cover_ref": "preserve school-age child proportions from @image1",
    },

    # ── 10-13 años — older child / pre-teen ─────────────────────────────────
    # Derivado de Bloques 2 y 3 certificados — pendiente validación visual
    "10-13": {
        "display": "10 year old older child",
        "proportions": (
            "head proportional to body, shoulders visibly broader than the head, "
            "elongated defined neck, long rectangular torso, long slender limbs, "
            "adult-like head-to-shoulder ratio emerging, lean older child body"
        ),
        "face": (
            "slim cheeks with minimal remaining child softness, "
            "emerging jawline definition without sharp adult angles, "
            "small straight nose, large eyes proportionally smaller than a young child, "
            "youthful pre-teen face, smooth child skin"
        ),
        "hair_note": None,
        "cover_ref": "preserve older child proportions from @image1",
    },

    # ── 14-18 años — teenager ───────────────────────────────────────────────
    # Derivado del Bloque 3 certificado — pendiente validación visual
    "14-18": {
        "display": "teenager",
        "proportions": (
            "adult head-to-body ratio, defined elongated neck, "
            "balanced limb-to-torso proportions, elongated torso, "
            "lanky teenage body with limbs proportionate to frame"
        ),
        "face": (
            "clear loss of childhood facial softness, well-defined facial planes, "
            "crisp jawline without childhood roundness, "
            "smooth adolescent skin, proportional eyes relative to the face"
        ),
        "hair_note": None,
        "cover_ref": "preserve teenage proportions from @image1",
    },
}


# Negative base universal para TODOS los portraits del SISTEMA 2
# Se combina con ca_neg (género) + NOPHOTO_NEGATIVE_BY_AGE (edad) en preview.py
NOPHOTO_PORTRAIT_NEGATIVE_BASE = (
    "oversized ears, exaggerated ears, large protruding ears, caricature, "
    "cartoon exaggeration, anime, manga, chibi"
)

# Negative prompts adicionales por rango de edad
# Se combinan con el negative base de género (ca_neg) en preview.py
NOPHOTO_NEGATIVE_BY_AGE = {
    "1":    "defined jawline, cheekbones, mature face, adult face, teenager, long legs, slim body, defined neck, visible neck",
    "2":    "defined jawline, cheekbones, mature face, adult face, teenager, long legs, slim body, defined neck, visible neck",
    "3-4":  "defined jawline, cheekbones, mature face, adult face, teenager, school-age child, long legs, slim body",
    "5":    "defined jawline, sharp chin, cheekbones, mature face, adult face, teenager, 9 year old, 10 year old, long legs, slim body, defined neck",
    "6":    "defined jawline, sharp chin, cheekbones, slim face, mature face, adult face, teenager, 9 year old, 10 year old, tall, long legs, defined neck",
    "7":    "defined jawline, sharp chin, cheekbones, slim face, mature face, adult face, teenager, 9 year old, 10 year old, tall, long legs, defined neck",
    "8-9":  "very chubby cheeks, extreme baby fat, toddler, defined sharp jawline, prominent cheekbones, mature face, adult face, teenager, 11 year old, 12 year old, pre-teen",
    "10-13": "baby fat, toddler, very chubby cheeks, adult face, defined sharp jawline, prominent cheekbones, mature adult, fully defined adult jaw",
    "14-18": "adult face, very mature, elderly, baby fat, toddler, very young child, chubby cheeks, undefined jaw",
}


def get_age_profile_nophoto(age: int) -> tuple[dict, str]:
    """
    Devuelve (profile_dict, range_key) del SISTEMA 2 (sin foto).
    NUNCA usar en el pipeline con foto — ese usa age_profiles.get_age_profile().

    Llamada 1 (FLUX portrait): usa proportions + face + hair_note
    Llamada 2 (FLUX cover/escenas): usa display + cover_ref
    """
    if age <= 1:
        key = "1"
    elif age <= 2:
        key = "2"
    elif age <= 4:
        key = "3-4"
    elif age <= 5:
        key = "5"
    elif age <= 6:
        key = "6"
    elif age <= 7:
        key = "7"
    elif age <= 9:
        key = "8-9"
    elif age <= 13:
        key = "10-13"
    else:
        key = "14-18"
    return AGE_PROFILE_NOPHOTO[key], key
