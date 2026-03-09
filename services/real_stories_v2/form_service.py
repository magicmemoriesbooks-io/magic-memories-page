# Haz tu Historia V2 - Form Service
# Character form handling with maximum 2 characters (human or pet)

from dataclasses import dataclass
from typing import Optional, List
import uuid

@dataclass
class Character:
    id: str
    name: str
    character_type: str  # 'human' or 'pet'
    gender: str  # 'male', 'female', 'neutral'
    age_range: str  # 'baby', 'toddler', 'child', 'adult' (for humans) or 'young', 'adult' (for pets)
    age_years: int = 5  # Actual age in years
    age_months: int = 0  # Additional months (for babies)
    height: int = 110  # Height in cm
    body_type: str = 'average'  # slim, average, chubby
    skin_tone: Optional[str] = None  # For humans
    hair_color: Optional[str] = None  # For humans
    hair_type: Optional[str] = None  # straight, wavy, curly, coily
    hair_length: Optional[str] = None  # short, medium, long, bald
    hair_style: Optional[str] = None  # Legacy field
    eye_color: Optional[str] = None
    facial_hair: Optional[str] = None  # none, stubble, beard, mustache, goatee
    clothing_style: Optional[str] = None  # casual, formal, sporty, elegant
    accessories: Optional[str] = None  # glasses, hat, etc.
    pet_species: Optional[str] = None  # For pets: dog, cat
    pet_breed: Optional[str] = None  # Breed name
    pet_color: Optional[str] = None  # Base fur color
    pet_pattern: Optional[str] = None  # solid, spotted, tabby
    pet_spot_color: Optional[str] = None  # Color of spots if spotted
    pet_stripe_color: Optional[str] = None  # Color of stripes if tabby
    special_features: Optional[str] = None  # Glasses, freckles, etc.
    relationship: Optional[str] = None  # protagonist, sibling, friend, pet

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'character_type': self.character_type,
            'gender': self.gender,
            'age_range': self.age_range,
            'age_years': self.age_years,
            'age_months': self.age_months,
            'height': self.height,
            'body_type': self.body_type,
            'skin_tone': self.skin_tone,
            'hair_color': self.hair_color,
            'hair_type': self.hair_type,
            'hair_length': self.hair_length,
            'hair_style': self.hair_style,
            'eye_color': self.eye_color,
            'facial_hair': self.facial_hair,
            'clothing_style': self.clothing_style,
            'accessories': self.accessories,
            'pet_species': self.pet_species,
            'pet_breed': self.pet_breed,
            'pet_color': self.pet_color,
            'pet_pattern': self.pet_pattern,
            'pet_spot_color': self.pet_spot_color,
            'pet_stripe_color': self.pet_stripe_color,
            'special_features': self.special_features,
            'relationship': self.relationship
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            name=data.get('name', ''),
            character_type=data.get('character_type', 'human'),
            gender=data.get('gender', 'neutral'),
            age_range=data.get('age_range', 'child'),
            age_years=int(data.get('age_years', 5)),
            age_months=int(data.get('age_months', 0)),
            height=int(data.get('height', 110)),
            body_type=data.get('body_type', 'average'),
            skin_tone=data.get('skin_tone'),
            hair_color=data.get('hair_color'),
            hair_type=data.get('hair_type'),
            hair_length=data.get('hair_length'),
            hair_style=data.get('hair_style'),
            eye_color=data.get('eye_color'),
            facial_hair=data.get('facial_hair'),
            clothing_style=data.get('clothing_style'),
            accessories=data.get('accessories'),
            pet_species=data.get('pet_species'),
            pet_breed=data.get('pet_breed'),
            pet_color=data.get('pet_color'),
            pet_pattern=data.get('pet_pattern'),
            pet_spot_color=data.get('pet_spot_color'),
            pet_stripe_color=data.get('pet_stripe_color'),
            special_features=data.get('special_features'),
            relationship=data.get('relationship')
        )

@dataclass  
class StoryRequest:
    id: str
    title: str
    story_description: str
    characters: List[Character]
    language: str  # 'es' or 'en'
    dedication: Optional[str] = None
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'story_description': self.story_description,
            'characters': [c.to_dict() for c in self.characters],
            'language': self.language,
            'dedication': self.dedication
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            title=data.get('title', ''),
            story_description=data.get('story_description', ''),
            characters=[Character.from_dict(c) for c in data.get('characters', [])],
            language=data.get('language', 'es'),
            dedication=data.get('dedication')
        )

def build_character_description(char: Character, lang: str = 'es') -> str:
    """Build a full text description of the character for FLUX 2 Pro prompts."""
    
    if char.character_type == 'pet':
        return build_pet_description(char, lang)
    else:
        return build_human_description(char, lang)

def build_human_description(char: Character, lang: str = 'es') -> str:
    """Build description for human character - ALWAYS in English for FLUX 2 Pro."""
    
    skin_tones = {
        'porcelain': 'porcelain',
        'very_light': 'very light',
        'light': 'light',
        'light_medium': 'light medium',
        'medium': 'medium',
        'olive': 'olive',
        'tan': 'tan',
        'brown': 'brown',
        'dark_brown': 'dark brown',
        'dark': 'dark'
    }
    
    eye_colors = {
        'brown': 'brown',
        'dark_brown': 'dark brown',
        'hazel': 'hazel',
        'amber': 'amber',
        'green': 'green',
        'blue': 'blue',
        'gray': 'gray',
        'black': 'black'
    }
    
    hair_colors = {
        'black': 'black',
        'dark_brown': 'dark brown',
        'brown': 'brown',
        'light_brown': 'light brown',
        'blonde': 'blonde',
        'platinum': 'platinum blonde',
        'red': 'red',
        'gray': 'gray',
        'white': 'white'
    }
    
    hair_types = {
        'straight': 'straight',
        'wavy': 'wavy',
        'curly': 'curly',
        'coily': 'coily afro'
    }
    
    hair_lengths = {
        'bald': 'bald',
        'very_short': 'buzz cut',
        'short': 'short',
        'medium': 'medium length',
        'long': 'long',
        'very_long': 'very long'
    }
    
    facial_hair_map = {
        'none': None,
        'stubble': 'light stubble',
        'short_beard': 'short beard',
        'full_beard': 'full beard',
        'mustache': 'mustache',
        'goatee': 'goatee'
    }
    
    clothing_styles = {
        'casual': 'casual',
        'formal': 'formal',
        'sporty': 'sporty athletic',
        'princess': 'princess dress',
        'superhero': 'superhero costume',
        'adventure': 'adventure explorer'
    }
    
    accessory_names = {
        'glasses': 'reading glasses',
        'sunglasses': 'dark sunglasses with black lenses',
        'cap': 'baseball cap',
        'scarf': 'scarf',
        'cowboy_hat': 'cowboy hat',
        'winter_hat': 'winter beanie'
    }
    
    body_types = {
        'slim': 'slim',
        'average': 'average build',
        'chubby': 'chubby'
    }
    
    age_years = char.age_years
    age_months = char.age_months
    
    total_months = (age_years * 12) + age_months
    
    if total_months < 12:
        age_str = f"a {total_months}-month-old baby"
    elif total_months < 24:
        age_str = f"an {total_months}-month-old toddler"
    elif age_years < 4:
        age_str = f"a {age_years}-year-old toddler"
    elif age_years < 13:
        age_str = f"a {age_years}-year-old child"
    elif age_years < 20:
        age_str = f"a {age_years}-year-old teenager"
    else:
        age_str = f"a {age_years}-year-old adult"
    
    gender_word = "girl" if char.gender == 'female' else "boy"
    if age_years >= 18:
        gender_word = "woman" if char.gender == 'female' else "man"
    elif age_years >= 13:
        gender_word = "teenage girl" if char.gender == 'female' else "teenage boy"
    elif total_months < 24:
        gender_word = "baby girl" if char.gender == 'female' else "baby boy"
    
    height = char.height
    body_type = body_types.get(char.body_type, 'average build')
    
    parts = [f"{char.name}: {age_str} {gender_word}, {height}cm tall, {body_type}"]
    
    skin = skin_tones.get(char.skin_tone, 'light')
    parts.append(f"with {skin} skin")
    
    eyes = eye_colors.get(char.eye_color, 'brown')
    parts.append(f"{eyes} eyes")
    
    hair_length = hair_lengths.get(char.hair_length or 'medium', 'medium length')
    hair_type = hair_types.get(char.hair_type or 'straight', 'straight')
    hair_color = hair_colors.get(char.hair_color, 'brown')
    
    if hair_length == 'bald':
        parts.append("completely bald, smooth hairless head, no hair at all")
    else:
        # Add gray/white hair hint for older adults
        if age_years >= 50 and hair_color in ['brown', 'black', 'dark_brown']:
            hair_color_text = hair_colors.get(hair_color, 'brown') + " with gray streaks"
        elif age_years >= 65:
            hair_color_text = "silver gray"
        else:
            hair_color_text = hair_colors.get(hair_color, 'brown')
        parts.append(f"{hair_length} {hair_type} {hair_color_text} hair")
    
    # Add age characteristics for older adults (kawaii style but with subtle age hints)
    if age_years >= 65:
        parts.append("gentle smile lines around eyes, wise kind expression, warm loving smile")
    elif age_years >= 50:
        parts.append("gentle smile lines, kind warm expression")
    elif age_years >= 40:
        parts.append("warm friendly expression")
    
    facial_hair = facial_hair_map.get(char.facial_hair or 'none', None)
    if facial_hair and char.gender == 'male' and age_years >= 16:
        # Add gray hints for older men's facial hair
        if age_years >= 65:
            parts.append(f"silver gray {facial_hair}")
        elif age_years >= 50:
            parts.append(f"{facial_hair} with gray streaks")
        else:
            parts.append(facial_hair)
    
    clothing = clothing_styles.get(char.clothing_style or 'casual', 'casual')
    parts.append(f"wearing {clothing} clothes")
    
    accessories_str = char.accessories or ''
    if accessories_str:
        acc_list = [a.strip() for a in accessories_str.split(',') if a.strip()]
        acc_names = [accessory_names.get(a, a) for a in acc_list]
        if acc_names:
            parts.append(f"with {', '.join(acc_names)}")
    
    return ', '.join(parts) + '.'

def build_pet_description(char: Character, lang: str = 'es') -> str:
    """Build description for pet character - ALWAYS in English for FLUX 2 Pro."""
    
    dog_breeds = {
        'mixed': 'mixed breed dog',
        'french_bulldog': 'French Bulldog',
        'labrador': 'Labrador Retriever',
        'golden_retriever': 'Golden Retriever',
        'german_shepherd': 'German Shepherd',
        'poodle': 'Poodle',
        'bulldog': 'English Bulldog',
        'beagle': 'Beagle',
        'rottweiler': 'Rottweiler',
        'dachshund': 'Dachshund',
        'yorkshire': 'Yorkshire Terrier',
        'boxer': 'Boxer',
        'husky': 'Siberian Husky',
        'chihuahua': 'Chihuahua',
        'shih_tzu': 'Shih Tzu',
        'corgi': 'Welsh Corgi',
        'pug': 'Pug',
        'maltese': 'Maltese',
        'schnauzer': 'Schnauzer',
        'cocker_spaniel': 'Cocker Spaniel',
        'border_collie': 'Border Collie'
    }
    
    cat_breeds = {
        'domestic': 'domestic shorthair cat',
        'persian': 'Persian cat',
        'siamese': 'Siamese cat',
        'maine_coon': 'Maine Coon cat',
        'ragdoll': 'Ragdoll cat',
        'british_shorthair': 'British Shorthair cat',
        'bengal': 'Bengal cat',
        'abyssinian': 'Abyssinian cat',
        'scottish_fold': 'Scottish Fold cat',
        'sphynx': 'Sphynx cat'
    }
    
    color_map = {
        'white': 'white',
        'cream': 'cream',
        'black': 'black',
        'brown': 'brown',
        'golden': 'golden',
        'gray': 'gray',
        'orange': 'orange',
        'spotted': 'spotted'
    }
    
    pattern_map = {
        'solid': 'solid colored',
        'spotted': 'spotted with patches',
        'tabby': 'tabby striped'
    }
    
    parts = [f"{char.name}:"]
    
    if char.pet_species == 'dog':
        breed = dog_breeds.get(char.pet_breed, 'dog')
        parts.append(f"a friendly {breed}")
    elif char.pet_species == 'cat':
        breed = cat_breeds.get(char.pet_breed, 'cat')
        parts.append(f"a cute {breed}")
    else:
        parts.append(f"a {char.pet_species}")
    
    if char.pet_color:
        color = color_map.get(char.pet_color, char.pet_color)
        parts.append(f"with {color} fur")
    
    if char.pet_pattern and char.pet_pattern != 'solid':
        if char.pet_pattern == 'spotted':
            spot_color = char.pet_spot_color or 'white'
            spot_color_name = color_map.get(spot_color, spot_color)
            parts.append(f"and {spot_color_name} spots")
        elif char.pet_pattern == 'tabby':
            stripe_color = char.pet_stripe_color or 'black'
            stripe_color_name = color_map.get(stripe_color, stripe_color)
            parts.append(f"with {stripe_color_name} tabby stripes")
    
    if char.special_features:
        parts.append(char.special_features)
    
    return ' '.join(parts)

def validate_story_request(data: dict) -> tuple[bool, str]:
    """Validate the story request form data."""
    
    if not data.get('story_description'):
        return False, "La descripción de la historia es requerida" if data.get('language', 'es') == 'es' else "Story description is required"
    
    if len(data.get('story_description', '')) < 20:
        return False, "La descripción debe tener al menos 20 caracteres" if data.get('language', 'es') == 'es' else "Description must be at least 20 characters"
    
    characters = data.get('characters', [])
    if not characters:
        return False, "Se requiere al menos un personaje" if data.get('language', 'es') == 'es' else "At least one character is required"
    
    if len(characters) > 2:
        return False, "Máximo 2 personajes permitidos" if data.get('language', 'es') == 'es' else "Maximum 2 characters allowed"
    
    for i, char in enumerate(characters):
        if not char.get('name'):
            return False, f"El personaje {i+1} necesita un nombre" if data.get('language', 'es') == 'es' else f"Character {i+1} needs a name"
        
        if char.get('character_type') == 'human':
            if not char.get('skin_tone'):
                return False, f"Selecciona el tono de piel para {char.get('name')}" if data.get('language', 'es') == 'es' else f"Select skin tone for {char.get('name')}"
        elif char.get('character_type') == 'pet':
            if not char.get('pet_species'):
                return False, f"Selecciona la especie de {char.get('name')}" if data.get('language', 'es') == 'es' else f"Select species for {char.get('name')}"
    
    return True, ""
