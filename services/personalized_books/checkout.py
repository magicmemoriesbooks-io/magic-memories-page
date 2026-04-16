# Personalized Books Checkout Configuration
# Impreso tapa dura: $33 base + Gelato shipping (dynamic pricing)
# PDF Imprimible: $30 fixed (no shipping)

PERSONALIZED_BOOK_PRICE = 33
PERSONALIZED_PDF_PRICE = 30

PERSONALIZED_BOOK_CONFIG = {
    'price': 33,
    'currency': 'USD',
    'includes_shipping': True,
    'includes_print': True,
    'delivery_method': 'email_and_print',
    'pdf_type': 'digital_and_print',
    'print_partner': 'lulu',
    'print_specs': {
        'format': 'A4_vertical',
        'pages': 24,
        'paper': '100lb_premium',
        'finish': 'glossy',
        'binding': 'casewrap_hardcover'
    }
}

PERSONALIZED_BOOK_IDS = [
    'dragon_garden_illustrated',
    'magic_chef_illustrated',
    'magic_inventor_illustrated',
    'star_keeper_illustrated',
    'furry_love_illustrated',
    'furry_love_adventure_illustrated',
    'furry_love_teen_illustrated',
    'furry_love_adult_illustrated',
    'centinela_aurora_illustrated'
]


def is_personalized_book(story_id: str) -> bool:
    """Check if a story ID belongs to Personalized Books category."""
    return story_id in PERSONALIZED_BOOK_IDS


def get_shipping_required() -> bool:
    """Personalized books always require shipping address."""
    return True
