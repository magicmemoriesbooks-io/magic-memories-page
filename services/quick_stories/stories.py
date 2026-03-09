# Quick Stories Definitions
# Baby stories (0-2) and Kids stories (3-8)
# $25 - Digital only

STYLE_BASE = "Children's storybook watercolor illustration style. Soft luminous colors, gentle warm lighting, dreamy magical atmosphere. Consistent character appearance throughout."

QUICK_STORIES = {
    # Baby Stories (0-2 years)
    "baby_soft_world": {
        "title_es": "{name} y el mundo suave",
        "title_en": "{name} and the Soft World",
        "age_range": "0-2",
        "category": "baby",
        "price": 25,
        "includes_print": False
    },
    "baby_puppy_love": {
        "title_es": "¿Sabes cuánto te quiero, {name}?",
        "title_en": "Do You Know How Much I Love You, {name}?",
        "age_range": "0-2",
        "category": "baby",
        "price": 25,
        "includes_print": False
    },
    "baby_first_pet": {
        "title_es": "{name} y su Primera Mascota",
        "title_en": "{name} and Their First Pet",
        "age_range": "0-2",
        "category": "baby",
        "price": 25,
        "includes_print": False
    },
    "baby_guardian_light": {
        "title_es": "{name} y la Luz Guardiana",
        "title_en": "{name} and the Guardian Light",
        "age_range": "0-2",
        "category": "baby",
        "price": 25,
        "includes_print": False
    },
    
    # Magical Adventures (3-5 years)
    "dragon_friend": {
        "title_es": "{name} y su Amigo el Dragón",
        "title_en": "{name} and Their Dragon Friend",
        "age_range": "3-5",
        "category": "magical_adventures",
        "price": 25,
        "includes_print": False
    },
    "zebra_stripes": {
        "title_es": "{name} y la aventura en la sabana",
        "title_en": "{name} and the Savanna Adventure",
        "age_range": "3-8",
        "category": "magical_adventures",
        "price": 25,
        "includes_print": False
    },
    
    # Great Adventures (6-8 years)
    "space_astronaut": {
        "title_es": "{name} el Astronauta",
        "title_en": "{name} the Astronaut",
        "age_range": "3-8",
        "category": "great_adventures",
        "price": 25,
        "includes_print": False
    },
    "superhero_light": {
        "title_es": "{name} y la Luz del Superhéroe",
        "title_en": "{name} and the Superhero Light",
        "age_range": "6-8",
        "category": "great_adventures",
        "price": 25,
        "includes_print": False
    },
    "star_guardian": {
        "title_es": "{name} Guardián de las Estrellas",
        "title_en": "{name} Guardian of the Stars",
        "age_range": "6-8",
        "category": "great_adventures",
        "price": 25,
        "includes_print": False
    },
    "chronicles_valley": {
        "title_es": "{name} y las Crónicas del Valle",
        "title_en": "{name} and the Valley Chronicles",
        "age_range": "5-7",
        "category": "great_adventures",
        "price": 25,
        "includes_print": False
    },
    "sunset_map": {
        "title_es": "{name} y el Mapa del Atardecer",
        "title_en": "{name} and the Sunset Map",
        "age_range": "5-7",
        "category": "great_adventures",
        "price": 25,
        "includes_print": False
    },
    "dog_forever": {
        "title_es": "{name} y su Perro para Siempre",
        "title_en": "{name} and Their Dog Forever",
        "age_range": "6-8",
        "category": "great_adventures",
        "price": 25,
        "includes_print": False
    }
}


def get_quick_story(story_id: str) -> dict:
    """Get a quick story by ID."""
    return QUICK_STORIES.get(story_id, {})


def get_quick_story_prompts(story_id: str, child_name: str, gender: str, traits: dict) -> list:
    """Get scene prompts for a quick story."""
    from services.fixed_stories import get_scene_prompts
    return get_scene_prompts(story_id, child_name, gender, traits)


def is_baby_story(story_id: str) -> bool:
    """Check if story is for babies (0-2)."""
    story = QUICK_STORIES.get(story_id, {})
    return story.get('age_range', '') in ['0-1', '0-2']


def get_story_category(story_id: str) -> str:
    """Get the category of a quick story."""
    story = QUICK_STORIES.get(story_id, {})
    return story.get('category', 'unknown')
