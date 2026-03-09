# Quick Stories Checkout Configuration
# $20 - Digital Only (PDF digital + PDF imprimible con instrucciones)
# $20 base + Lulu dynamic pricing for Printed Book

QUICK_STORY_PRICE_DIGITAL = 20
QUICK_STORY_PRICE_PRINT = 20

QUICK_STORY_CONFIG = {
    'digital': {
        'price': 20,
        'currency': 'USD',
        'includes_shipping': False,
        'includes_print': False,
        'delivery_method': 'email_only',
        'pdf_type': 'digital',
    },
    'print': {
        'price': 20,
        'currency': 'USD',
        'includes_shipping': True,
        'includes_print': True,
        'delivery_method': 'email_and_print',
        'pdf_type': 'digital_and_print',
        'shipping_method': 'MAIL',
    },
    'age_ranges': {
        'baby': '0-2',
        'magical_adventures': '3-5', 
        'great_adventures': '6-8'
    }
}

QUICK_STORY_IDS = [
    'baby_soft_world',
    'baby_puppy_love', 
    'baby_first_pet',
    'baby_guardian_light',
    'dragon_friend',
    'space_astronaut',
    'zebra_stripes',
    'superhero_light',
    'chronicles_valley',
    'sunset_map',
    'star_guardian',
    'dog_forever'
]

BIRTHDAY_STORY_IDS = [
    'birthday_celebration_1_3',
    'birthday_celebration_4_6',
    'birthday_celebration_7_9'
]

ALL_QUICK_FAMILY_IDS = QUICK_STORY_IDS + BIRTHDAY_STORY_IDS

def is_quick_story(story_id: str) -> bool:
    """Check if a story ID belongs to Quick Stories or Birthday category (same payment flow)."""
    return story_id in ALL_QUICK_FAMILY_IDS

def is_birthday_story(story_id: str) -> bool:
    """Check if a story ID belongs to Birthday Stories category."""
    return story_id in BIRTHDAY_STORY_IDS

def get_quick_story_age_range(story_id: str) -> str:
    """Get the age range for a quick story."""
    from .stories import QUICK_STORIES
    story = QUICK_STORIES.get(story_id, {})
    return story.get('age_range', '0-2')
