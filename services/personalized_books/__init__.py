# Personalized Books Module ($55 - Digital + Print)
# Dragon Garden, Magic Chef, Magic Inventor, Star Keeper

from .stories import PERSONALIZED_BOOKS, get_personalized_book, get_personalized_book_ids
from .preview import generate_personalized_preview
from .pdf_service import generate_personalized_pdf, generate_print_pdf, generate_cover_spread
from .lulu_service import submit_to_lulu, get_lulu_specs
from .checkout import PERSONALIZED_BOOK_PRICE, PERSONALIZED_BOOK_CONFIG, PERSONALIZED_BOOK_IDS, is_personalized_book
from .generation import generate_full_book_preview, get_personalized_book_id, is_personalized_book as is_personalized_story
from .dragon_garden_prompts import (
    DRAGON_GARDEN_SCENES, CLOSING_SCENE, FRONT_COVER, BACK_COVER,
    SPARK_INLINE, STYLE_BASE,
    get_outfit_desc, get_hair_action,
    build_scene_prompt, get_all_scene_prompts, get_cover_prompts
)
from .magic_inventor_prompts import (
    MAGIC_INVENTOR_SCENES,
    BOLT_INLINE,
    STYLE_BASE as INVENTOR_STYLE_BASE,
    CLOSING_SCENE as INVENTOR_CLOSING_SCENE,
    FRONT_COVER as INVENTOR_FRONT_COVER,
    BACK_COVER as INVENTOR_BACK_COVER
)
from .star_keeper_prompts import (
    STAR_KEEPER_SCENES,
    LUNA_INLINE,
    STYLE_BASE as STAR_KEEPER_STYLE_BASE,
    CLOSING_SCENE as STAR_KEEPER_CLOSING_SCENE,
    FRONT_COVER as STAR_KEEPER_FRONT_COVER,
    BACK_COVER as STAR_KEEPER_BACK_COVER
)
from .magic_chef_prompts import (
    MAGIC_CHEF_SCENES,
    SWEETIE_HAT_INLINE, SWEETIE_CAKE_INLINE,
    STYLE_BASE as CHEF_STYLE_BASE,
    CLOSING_SCENE as CHEF_CLOSING_SCENE,
    FRONT_COVER as CHEF_FRONT_COVER,
    BACK_COVER as CHEF_BACK_COVER
)
from .furry_love_prompts import (
    FURRY_LOVE_SCENES,
    STYLE_BASE as FURRY_LOVE_STYLE_BASE,
    CLOSING_SCENE as FURRY_LOVE_CLOSING_SCENE,
    FRONT_COVER as FURRY_LOVE_FRONT_COVER,
    BACK_COVER as FURRY_LOVE_BACK_COVER,
    build_scene_prompt as fl_build_scene_prompt,
    build_human_preview_prompt,
    build_pet_preview_prompt
)
