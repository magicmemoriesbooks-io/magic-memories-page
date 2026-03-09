# Personalized Books Lulu Integration
# Handles submission to Lulu for printing

import os
import json
from datetime import datetime


def submit_to_lulu(story_data: dict, interior_pdf: str, cover_pdf: str,
                   shipping_address: dict) -> dict:
    """
    Submit a personalized book to Lulu for printing.
    """
    from services.lulu_service import (
        create_print_job,
        upload_interior,
        upload_cover,
        get_shipping_options
    )
    
    try:
        interior_url = upload_interior(interior_pdf)
        cover_url = upload_cover(cover_pdf)
        
        print_job = create_print_job(
            title=story_data.get('title', 'Personalized Book'),
            interior_url=interior_url,
            cover_url=cover_url,
            shipping_address=shipping_address,
            quantity=1
        )
        
        return {
            'success': True,
            'job_id': print_job.get('id'),
            'status': print_job.get('status'),
            'tracking_url': print_job.get('tracking_url')
        }
        
    except Exception as e:
        print(f"[LULU ERROR] Personalized book submission failed: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def get_lulu_specs() -> dict:
    """Get Lulu print specifications for personalized books."""
    return {
        'pod_package_id': '0850X1100FCSTDLW060UW444GXX',
        'page_count': 24,
        'binding': 'case_wrap',
        'interior_color': 'standard_color',
        'paper': 'premium_100lb',
        'finish': 'glossy',
        'size': {
            'width': 216,
            'height': 303,
            'unit': 'mm'
        }
    }
