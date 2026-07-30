# =============================================================================
# AGE_PROFILE — tabla de proporciones para KONTEXT (SISTEMA 1 con foto)
# =============================================================================
#
# Regla de uso:
#   SOLO para PASO 1 (Kontext Pro) del Sistema 1 (con foto).
#   Sistema 2 (sin foto) usa age_profiles_nophoto.py — nunca esta tabla.
#
# El campo 'kontext' va al prompt de Kontext para convertir la foto del niño
# en un personaje 3D animado con las proporciones correctas para su edad.
#
# Perfiles anatómicos certificados — versión final aprobada.
# Descripción únicamente de anatomía objetiva: proporciones corporales,
# estructura ósea y desarrollo facial. Sin pose, expresión ni ropa.
#
# Asignación definitiva por edad (años):
#   0        → newborn
#   1        → infant
#   2        → toddler
#   3–4      → preschool
#   5        → early_childhood
#   6        → young_school
#   7–8      → school_age
#   9–10     → older_child
#   11–12    → preteen
#   13–14    → early_teen
#   15–16    → mid_teen
#   17–18    → late_teen
#   19–29    → young_adult
#   30–39    → adult_30s
#   40–49    → adult_40s
#   50–59    → adult_50s
#   60–69    → senior_60s
#   70–79    → senior_70s
#   80+      → senior_80_plus
#
# =============================================================================

AGE_PROFILE = {

    # ── Bloque 1: Bebés (0–24 meses) ─────────────────────────────────────────

    "newborn": {
        "display": "newborn baby",
        "kontext": (
            "oversized head relative to the body, extremely short neck, very small torso, "
            "short thin limbs, toothless gums, sparse fine baby hair, delicate translucent skin, "
            "minimal subcutaneous fat, proportionally large round eyes, tiny hands and feet"
        ),
    },
    "infant": {
        "display": "infant",
        "kontext": (
            "proportionally large head, well-defined neck, rounded infant body, "
            "reduced but still visible subcutaneous baby fat on limbs, "
            "several visible upper and lower front baby teeth, fuller baby hair, "
            "rounded cheeks, short sturdy arms and legs"
        ),
    },
    "toddler": {
        "display": "toddler",
        "kontext": (
            "proportionally smaller head than an infant, defined neck, elongated torso, "
            "slightly protruding toddler belly, reduced subcutaneous baby fat on limbs, "
            "visible upper and lower baby teeth, full toddler hair, "
            "rounded youthful face, sturdy limbs"
        ),
    },

    # ── Bloque 2: Niños (3–12 años) ──────────────────────────────────────────

    "preschool": {
        "display": "preschool child",
        "kontext": (
            "head width dominating narrow shoulders, short neck, compact square torso, "
            "subtle protruding child abdomen, short limbs, visible soft tissue on arms and legs, "
            "full rounded cheeks with buccal fat, soft undefined jawline"
        ),
    },
    "early_childhood": {
        "display": "early childhood child",
        "kontext": (
            "head resting close to narrow shoulders, short neck, compact rectangular torso, "
            "flat abdomen, short sturdy limbs proportional to a compact frame, "
            "rounded cheeks, soft jawline curve, smooth child skin"
        ),
    },
    "young_school": {
        "display": "young school child",
        "kontext": (
            "shoulders dropping to create separation from the head, elongated neck, narrow torso, "
            "visibly lengthened arms and legs, lean limbs, noticeable loss of cheek fullness, "
            "defined angular jawline, visible collarbones, proportional eyes"
        ),
    },
    "school_age": {
        "display": "school-age child",
        "kontext": (
            "clear separation between head and dropped shoulders, well-defined neck, "
            "elongated straight torso, long lean limbs, sinewy arms and legs, "
            "flat narrow facial structure, clearly defined jawline, "
            "proportional facial features, visible collarbones"
        ),
    },
    "older_child": {
        "display": "older child",
        "kontext": (
            "shoulders visibly broader than the head, elongated neck, long rectangular torso, "
            "long slender limbs, more defined facial planes, structured but smooth jawline, "
            "mature child facial proportions, proportionally smaller eyes relative to the face"
        ),
    },
    "preteen": {
        "display": "pre-teen",
        "kontext": (
            "adult-like head-to-shoulder ratio, elongated defined neck, broadened shoulders, "
            "long limbs, angular facial structure, more defined cheekbones, sharp jawline, "
            "mature pre-teen facial proportions, loss of childhood facial softness"
        ),
    },

    # ── Bloque 3: Adolescentes (13–18 años) ──────────────────────────────────

    "early_teen": {
        "display": "early teenager",
        "kontext": (
            "adult head-to-body ratio, elongated neck, lanky body proportions with limbs "
            "appearing disproportionately long relative to the torso, visible angular joints, "
            "emerging jawline definition with slight lingering childhood softness in the lower cheeks, "
            "smooth adolescent skin"
        ),
    },
    "mid_teen": {
        "display": "mid teenager",
        "kontext": (
            "defined neck, balanced limb-to-torso proportions, elongated torso, "
            "clear loss of lower cheek fullness, well-defined facial planes, "
            "crisp jawline without childhood softness, smooth youthful skin"
        ),
    },
    "late_teen": {
        "display": "late teenager",
        "kontext": (
            "mature adult skeletal proportions, proportionate torso and limb structure, "
            "fully developed facial structure, well-defined cheekbones, sharp adult jawline, "
            "complete absence of childhood facial softness, youthful adult skin"
        ),
    },

    # ── Bloque 4: Adultos (19–59 años) ───────────────────────────────────────

    "young_adult": {
        "display": "young adult",
        "kontext": (
            "fully mature skeletal proportions, balanced adult body structure, "
            "full midface volume, smooth taut skin with high elasticity, "
            "crisp jawline contour, taut neck skin, absence of visible resting facial lines"
        ),
    },
    "adult_30s": {
        "display": "adult",
        "kontext": (
            "fully mature adult proportions, stable facial structure, "
            "natural adult midface volume, firm mature skin texture, "
            "defined jawline contour, firm neck skin, minimal resting facial lines"
        ),
    },
    "adult_40s": {
        "display": "middle-aged adult",
        "kontext": (
            "mature adult proportions, subtle loss of midface volume, "
            "visible mature skin texture with early signs of elasticity loss, "
            "emerging resting nasolabial folds, subtle periorbital resting lines, "
            "softened jawline contour, mild neck skin laxity"
        ),
    },
    "adult_50s": {
        "display": "mature adult",
        "kontext": (
            "mature adult proportions, visible loss of facial volume, defined under-eye hollows, "
            "thin mature skin texture with clear elasticity loss, established nasolabial folds, "
            "visible resting facial lines, soft jawline contour, visible neck skin laxity"
        ),
    },

    # ── Bloque 5: Adultos mayores (60+ años) ─────────────────────────────────

    "senior_60s": {
        "display": "older adult",
        "kontext": (
            "mature adult proportions, visible descent of facial soft tissue, "
            "defined under-eye area, mature skin texture with visible elasticity loss, "
            "established resting facial lines and folds, softened jawline contour, "
            "visible neck skin laxity"
        ),
    },
    "senior_70s": {
        "display": "elderly adult",
        "kontext": (
            "mature older adult proportions, noticeable downward shift of facial soft tissue, "
            "thin aging skin texture, clearly visible resting facial lines, "
            "established nasolabial and marionette folds, loss of jawline definition, "
            "pronounced neck skin laxity"
        ),
    },
    "senior_80_plus": {
        "display": "elderly person",
        "kontext": (
            "advanced descent of facial soft tissue, delicate translucent thin skin, "
            "clearly established resting facial folds, softening of facial contours, "
            "prominent neck skin laxity"
        ),
    },
}


def get_age_profile(age: int) -> tuple:
    """Return (profile_dict, range_key) for a given age in years.

    Args:
        age: age in whole years (int or coercible to int).

    Returns:
        (profile, range_key) where:
          - profile['kontext']  — proporciones anatómicas para el prompt de Kontext (PASO 1)
          - profile['display']  — etiqueta legible para logs y admin
          - range_key           — clave del dict, e.g. "young_school"

    Asignación definitiva por edad:
        0        → newborn
        1        → infant
        2        → toddler
        3–4      → preschool
        5        → early_childhood
        6        → young_school
        7–8      → school_age
        9–10     → older_child
        11–12    → preteen
        13–14    → early_teen
        15–16    → mid_teen
        17–18    → late_teen
        19–29    → young_adult
        30–39    → adult_30s
        40–49    → adult_40s
        50–59    → adult_50s
        60–69    → senior_60s
        70–79    → senior_70s
        80+      → senior_80_plus
    """
    try:
        age_int = int(age)
    except (TypeError, ValueError):
        age_int = 6

    if age_int <= 0:    key = "newborn"
    elif age_int <= 1:  key = "infant"
    elif age_int <= 2:  key = "toddler"
    elif age_int <= 4:  key = "preschool"
    elif age_int <= 5:  key = "early_childhood"
    elif age_int <= 6:  key = "young_school"
    elif age_int <= 8:  key = "school_age"
    elif age_int <= 10: key = "older_child"
    elif age_int <= 12: key = "preteen"
    elif age_int <= 14: key = "early_teen"
    elif age_int <= 16: key = "mid_teen"
    elif age_int <= 18: key = "late_teen"
    elif age_int <= 29: key = "young_adult"
    elif age_int <= 39: key = "adult_30s"
    elif age_int <= 49: key = "adult_40s"
    elif age_int <= 59: key = "adult_50s"
    elif age_int <= 69: key = "senior_60s"
    elif age_int <= 79: key = "senior_70s"
    else:               key = "senior_80_plus"

    return AGE_PROFILE[key], key
