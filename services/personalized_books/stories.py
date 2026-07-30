# Personalized Books Story Definitions
# Universos Ilustrados (8 books) — 30 pages, 22 illustrations, Cloudprinter hardcover A4
# $30 base + Cloudprinter shipping

PERSONALIZED_BOOKS = {
    "dragon_garden_illustrated": {
        "title_es": "{name} y el Dragón del Jardín Mágico",
        "title_en": "{name} and the Magic Garden Dragon",
        "age_range": "3-8",
        "category": "personalized",
        "price": 30,
        "includes_print": True,
        "fulfillment": "cloudprinter",
        "print_pages": 30,
        "illustrations": 22,
        "use_fixed_scenes": False
    },
    "magic_chef_illustrated": {
        "title_es": "{name} el Chef Mágico",
        "title_en": "{name} the Magic Chef",
        "age_range": "3-8",
        "category": "personalized",
        "price": 30,
        "includes_print": True,
        "fulfillment": "cloudprinter",
        "print_pages": 30,
        "illustrations": 22,
        "use_fixed_scenes": False
    },
    "magic_inventor_illustrated": {
        "title_es": "{name} y el Taller de los Inventos Mágicos",
        "title_en": "{name} and the Magic Inventor Workshop",
        "age_range": "6-8",
        "category": "personalized",
        "price": 30,
        "includes_print": True,
        "fulfillment": "cloudprinter",
        "print_pages": 30,
        "illustrations": 22,
        "use_fixed_scenes": False
    },
    "star_keeper_illustrated": {
        "title_es": "{name} y el Guardián de Estrellas",
        "title_en": "{name} The Star Keeper",
        "age_range": "6-7",
        "category": "personalized",
        "price": 30,
        "includes_print": True,
        "fulfillment": "cloudprinter",
        "print_pages": 30,
        "illustrations": 22,
        "use_fixed_scenes": False
    },
    "furry_love_illustrated": {
        "title_es": "Tú y tu Amor Peludo",
        "title_en": "You and Your Furry Love",
        "age_range": "18+",
        "category": "personalized",
        "price": 30,
        "includes_print": True,
        "fulfillment": "cloudprinter",
        "print_pages": 30,
        "illustrations": 22,
        "use_fixed_scenes": False
    },
    "furry_love_adventure_illustrated": {
        "title_es": "Tú y tu Amor Peludo: La Gran Aventura",
        "title_en": "You and Your Furry Love: The Big Adventure",
        "age_range": "18+",
        "category": "personalized",
        "price": 30,
        "includes_print": True,
        "fulfillment": "cloudprinter",
        "print_pages": 30,
        "illustrations": 22,
        "use_fixed_scenes": False
    },
    "furry_love_teen_illustrated": {
        "title_es": "Tú y tu Amor Peludo: Aventura Teen",
        "title_en": "You and Your Furry Love: Teen Adventure",
        "age_range": "12-17",
        "category": "personalized",
        "price": 30,
        "includes_print": True,
        "fulfillment": "cloudprinter",
        "print_pages": 30,
        "illustrations": 22,
        "use_fixed_scenes": False
    },
    "centinela_aurora_illustrated": {
        "title_es": "{name} y el Centinela de la Aurora",
        "title_en": "{name} and the Aurora Sentinel",
        "age_range": "4-8",
        "category": "personalized",
        "price": 26,
        "includes_print": True,
        "fulfillment": "cloudprinter",
        "print_pages": 26,
        "illustrations": 19,
        "use_fixed_scenes": False
    },
    "furry_love_adult_illustrated": {
        "title_es": "Tú y tu Amor Peludo: Edición Adultos",
        "title_en": "You and Your Furry Love: Adult Edition",
        "age_range": "18+",
        "category": "personalized",
        "price": 30,
        "includes_print": True,
        "fulfillment": "cloudprinter",
        "print_pages": 30,
        "illustrations": 22,
        "use_fixed_scenes": False
    }
}


def get_personalized_book(story_id: str) -> dict:
    """Get a personalized book by ID."""
    return PERSONALIZED_BOOKS.get(story_id, {})


def get_personalized_book_ids() -> list:
    """Get all personalized book IDs."""
    return list(PERSONALIZED_BOOKS.keys())
