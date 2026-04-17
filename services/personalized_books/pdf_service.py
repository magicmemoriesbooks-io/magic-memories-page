# Personalized Books PDF Generation
# Now handled via Cloudprinter — Lulu functions removed.

from io import BytesIO
import os


def generate_personalized_pdf(story_data: dict, output_path: str = None) -> str:
    """
    Return the already-generated Cloudprinter content PDF if available,
    otherwise raise so the caller's try/except handles it gracefully.
    """
    preview_id = story_data.get('preview_id', '')
    cp_content = f'generations/cloudprinter/{preview_id}/content.pdf'
    if preview_id and os.path.exists(cp_content):
        if output_path and output_path != cp_content:
            import shutil
            shutil.copy2(cp_content, output_path)
            return output_path
        return cp_content
    raise NotImplementedError("Personalized PDF is generated via Cloudprinter — no separate digital PDF needed.")


def generate_print_pdf(story_data: dict, output_path: str = None) -> str:
    """Print PDF now generated directly via Cloudprinter pipeline."""
    return generate_personalized_pdf(story_data, output_path)


def generate_cover_spread(story_data: dict, output_path: str = None) -> str:
    """Cover spread now generated directly via Cloudprinter pipeline."""
    preview_id = story_data.get('preview_id', '')
    cp_cover = f'generations/cloudprinter/{preview_id}/cover.pdf'
    if preview_id and os.path.exists(cp_cover):
        if output_path and output_path != cp_cover:
            import shutil
            shutil.copy2(cp_cover, output_path)
            return output_path
        return cp_cover
    raise NotImplementedError("Cover spread is generated via Cloudprinter — no separate file needed.")


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
