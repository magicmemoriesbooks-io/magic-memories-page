# Personalized Books Story Definitions
# Dragon Garden Illustrated, Magic Chef Illustrated, Magic Inventor Illustrated, Star Keeper Illustrated
# $55 - Digital + Print

PERSONALIZED_BOOKS = {
    "dragon_garden_illustrated": {
        "title_es": "{name} y el Dragón del Jardín Mágico",
        "title_en": "{name} and the Magic Garden Dragon",
        "age_range": "3-8",
        "category": "personalized",
        "price": 55,
        "includes_print": True,
        "print_pages": 24,
        "illustrations": 19,
        "has_closing_scene": True,
        "use_fixed_scenes": False
    },
    "magic_chef_illustrated": {
        "title_es": "{name} el Chef Mágico",
        "title_en": "{name} the Magic Chef",
        "age_range": "3-8",
        "category": "personalized",
        "price": 55,
        "includes_print": True,
        "print_pages": 24,
        "illustrations": 19,
        "has_closing_scene": True,
        "use_fixed_scenes": False
    },
    "magic_inventor_illustrated": {
        "title_es": "{name} y el Taller de los Inventos Mágicos",
        "title_en": "{name} and the Magic Inventor Workshop",
        "age_range": "6-8",
        "category": "personalized",
        "price": 55,
        "includes_print": True,
        "print_pages": 24,
        "illustrations": 19,
        "has_closing_scene": True,
        "use_fixed_scenes": False
    },
    "star_keeper_illustrated": {
        "title_es": "{name} y el Guardián de Estrellas",
        "title_en": "{name} The Star Keeper",
        "age_range": "6-7",
        "category": "personalized",
        "price": 55,
        "includes_print": True,
        "print_pages": 24,
        "illustrations": 19,
        "has_closing_scene": True,
        "use_fixed_scenes": False
    }
}


def get_personalized_book(story_id: str) -> dict:
    """Get a personalized book by ID."""
    return PERSONALIZED_BOOKS.get(story_id, {})


def get_personalized_book_ids() -> list:
    """Get all personalized book IDs."""
    return list(PERSONALIZED_BOOKS.keys())
