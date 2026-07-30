HAIRSTYLE_PROFILE = {
    # Todos los cortes son unisex — cualquier género puede llevar cualquier corte.
    # has_texture: True  → el tipo de pelo (wavy/curly/straight) se incorpora como textura
    # has_texture: False → la textura ya está implícita en el corte (coily, very short, etc.)
    'classic_taper': {
        'display': 'Classic Taper',
        'has_texture': True,
        'prompt': 'classic low taper haircut, gradual taper on sides and back starting low near the nape — NOT a high skin fade, sides short but not shaved, {texture}hair on top kept short (1 to 2 cm) lying close to the head with minimal natural texture, subtle slight lift only, no dramatic height, no pompadour, no strong contrast',
        'block': 'HAIRCUT: Classic Low Taper. Gradual taper on sides and back starting low near the nape — NOT a skin fade, NOT shaved high. Top short (1–2 cm), lying close to head with subtle natural texture and minimal lift. No dramatic height, no strong contrast between top and sides.',
    },
    'layered_medium': {
        'display': 'Short Layered',
        'has_texture': True,
        'prompt': 'short layered scissor cut, hair reaching the nape of the neck with soft natural {texture}layers, clean rounded shape',
        'block': 'HAIRCUT: Short Layered Cut. Scissor-cut, soft layers reaching the nape of the neck, clean rounded shape.',
    },
    'curly_high_fade': {
        'display': 'Curly High Fade',
        'has_texture': False,
        'prompt': 'high skin fade haircut with short coily curls on top and a sharp clean line-up',
        'block': 'HAIRCUT: Curly High Fade. High skin fade, short coily curls on top, sharp line-up.',
    },
    'high_and_tight': {
        'display': 'High & Tight',
        'has_texture': False,
        'prompt': 'high and tight haircut with a very short uniform top, clean high fade and sharp front hairline',
        'block': 'HAIRCUT: High & Tight. Very short uniform top, high fade, sharp front hairline.',
    },
}

HAIR_COLOR_MAP = {
    'black': 'jet black',
    'brown': 'medium brown',
    'light_brown': 'warm light brown (caramel-honey tone)',
    'blonde': 'dark dirty blonde',
    'very_light_blonde': 'pale platinum blonde',
    'red': 'bright red',
    'auburn': 'auburn',
}

HAIR_TYPE_TEXTURE = {
    'straight': '',
    'wavy': 'wavy ',
    'curly': 'curly ',
    'coily': 'coily ',
}

# Sufijo de refuerzo de textura — da movimiento y evita cabello plástico en colores claros
HAIR_TYPE_TEXTURE_SUFFIX = {
    'straight': ', smooth straight hair, clean natural hair flow',
    'wavy': ', soft natural waves, wavy hair catching the light',
    'curly': ', defined natural curls, curly hair with natural bounce',
    'coily': ', tight natural coils, rich coily texture',
}


def get_hairstyle(key: str):
    """Return hairstyle data dict for key, or None if key is empty/unrecognised.
    All cuts are unisex — no gender restriction applied."""
    if not key:
        return None
    return HAIRSTYLE_PROFILE.get(key)


def build_haircut_description(hairstyle_data: dict, traits: dict) -> str:
    """Build the full hair description string when a haircut is selected.

    Rules:
    - hair_length is IGNORED (the cut defines the length/shape)
    - hair_color is always included
    - hair_type is included as texture only when has_texture: True
    - Returns a single descriptive string suitable for the HAIR field in a prompt.
    """
    color = traits.get('hair_color', 'brown')
    hair_color = HAIR_COLOR_MAP.get(color, color)

    if hairstyle_data.get('has_texture'):
        hair_type = traits.get('hair_type', 'straight')
        texture = HAIR_TYPE_TEXTURE.get(hair_type, '')
        suffix = HAIR_TYPE_TEXTURE_SUFFIX.get(hair_type, '')
        prompt = hairstyle_data['prompt'].replace('{texture}', texture)
    else:
        suffix = ''
        prompt = hairstyle_data['prompt'].replace('{texture}', '')

    return f"{hair_color} {prompt}{suffix}"


def get_hair_color_only(traits: dict) -> str:
    """Return just the hair color descriptor (no length/type)."""
    color = traits.get('hair_color', 'brown')
    return HAIR_COLOR_MAP.get(color, color)
