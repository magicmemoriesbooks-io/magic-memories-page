# Personalized Books PDF Generation
# Digital PDF + Print-ready PDF for Lulu

from io import BytesIO


def generate_personalized_pdf(story_data: dict, output_path: str = None) -> str:
    """
    Generate digital PDF for Personalized Books.
    23 pages: Cover, Dedication, 19 scenes, Closing, Credits
    """
    from services.pdf_service import create_lulu_digital_pdf
    return create_lulu_digital_pdf(story_data, output_path)


def generate_print_pdf(story_data: dict, output_path: str = None) -> str:
    """
    Generate print-ready interior PDF for Lulu.
    24 pages: Cover, Dedication, 19 scenes, Closing, Credits, Blank
    """
    from services.pdf_service import create_lulu_print_interior_pdf
    return create_lulu_print_interior_pdf(story_data, output_path)


def generate_cover_spread(story_data: dict, output_path: str = None) -> str:
    """
    Generate cover spread for Lulu.
    Back Cover + Spine + Front Cover in one spread
    """
    from services.pdf_service import create_lulu_cover_spread
    return create_lulu_cover_spread(story_data, output_path)


def get_personalized_pdf_config() -> dict:
    """Get PDF configuration for personalized books."""
    return {
        'digital': {
            'pages': 23,
            'size': 'A4',
            'resolution': 300
        },
        'print': {
            'pages': 24,
            'size': '216x303mm',
            'resolution': 300,
            'bleed': '3mm'
        },
        'cover': {
            'format': 'spread',
            'spine_width': 'auto',
            'resolution': 300
        }
    }
