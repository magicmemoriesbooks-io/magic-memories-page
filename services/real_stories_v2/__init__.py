# Tú y tu Amor Peludo - Service Module
#
# Personalized book: human + pet (dog/cat) story
# FLUX 2 Dev with TWO reference images for character consistency
# Pre-written bilingual story (ES/EN), no AI text generation
#
# Structure:
# - form_service.py: Character form handling (1 human + 1 pet)
# - image_service.py: FLUX 2 Dev image generation with dual references
#
# Flow:
# 1. Character form (human + pet customization)
# 2. Preview both characters → Approve/Regenerate
# 3. Preview story text with book typography
# 4. Payment (PayPal) → Background scene generation
# 5. Approve illustrations → PDF composition → Lulu/ebook

__version__ = "3.0.0"

from .form_service import (
    Character,
    StoryRequest,
    build_character_description,
    build_human_description,
    build_pet_description,
    validate_story_request
)

from .image_service import (
    generate_character_preview,
    generate_scene_with_references,
    add_preview_watermark
)
