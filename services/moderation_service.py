"""
Content Moderation Service
Uses OpenAI's free moderation API to detect inappropriate content
"""

import os
from openai import OpenAI

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

CATEGORY_LABELS = {
    'sexual': 'contenido sexual',
    'sexual/minors': 'contenido sexual que involucra menores',
    'hate': 'discurso de odio',
    'hate/threatening': 'amenazas de odio',
    'harassment': 'acoso',
    'harassment/threatening': 'acoso amenazante',
    'self-harm': 'autolesión',
    'self-harm/intent': 'intención de autolesión',
    'self-harm/instructions': 'instrucciones de autolesión',
    'violence': 'violencia',
    'violence/graphic': 'violencia gráfica',
}

CATEGORY_LABELS_EN = {
    'sexual': 'sexual content',
    'sexual/minors': 'sexual content involving minors',
    'hate': 'hate speech',
    'hate/threatening': 'hate threats',
    'harassment': 'harassment',
    'harassment/threatening': 'threatening harassment',
    'self-harm': 'self-harm',
    'self-harm/intent': 'self-harm intent',
    'self-harm/instructions': 'self-harm instructions',
    'violence': 'violence',
    'violence/graphic': 'graphic violence',
}


def moderate_content(text: str, lang: str = 'es') -> tuple[bool, str]:
    """
    Check if content is appropriate using OpenAI's moderation API.
    
    Args:
        text: The text to moderate
        lang: Language for error messages ('es' or 'en')
    
    Returns:
        Tuple of (is_safe, error_message)
        - is_safe: True if content is appropriate, False if flagged
        - error_message: Empty string if safe, or description of violation
    """
    if not text or not text.strip():
        return True, ""
    
    try:
        response = client.moderations.create(input=text)
        result = response.results[0]
        
        if not result.flagged:
            return True, ""
        
        flagged_categories = []
        labels = CATEGORY_LABELS if lang == 'es' else CATEGORY_LABELS_EN
        
        categories = result.categories
        for category, is_flagged in vars(categories).items():
            if is_flagged and category in labels:
                flagged_categories.append(labels[category])
        
        if lang == 'es':
            error_msg = f"Tu contenido ha sido rechazado porque contiene: {', '.join(flagged_categories)}. Por favor, modifica tu descripción y elimina cualquier contenido inapropiado."
        else:
            error_msg = f"Your content has been rejected because it contains: {', '.join(flagged_categories)}. Please modify your description and remove any inappropriate content."
        
        return False, error_msg
        
    except Exception as e:
        print(f"[MODERATION] Error calling moderation API: {e}")
        return True, ""


def moderate_story_request(story_data: dict) -> tuple[bool, str]:
    """
    Moderate all text content in a story request.
    
    Args:
        story_data: Dictionary containing story_description, dedication, and characters
    
    Returns:
        Tuple of (is_safe, error_message)
    """
    lang = story_data.get('language', 'es')
    
    texts_to_check = []
    
    if story_data.get('story_description'):
        texts_to_check.append(story_data['story_description'])
    
    if story_data.get('dedication'):
        texts_to_check.append(story_data['dedication'])
    
    for char in story_data.get('characters', []):
        if char.get('special_features'):
            texts_to_check.append(char['special_features'])
    
    combined_text = " ".join(texts_to_check)
    
    return moderate_content(combined_text, lang)
