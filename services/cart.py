"""
Shopping cart helpers.  Operates on Flask session['cart'] — no database.
"""
import uuid
import os
import json

EU_AND_FREE_SHIPPING_COUNTRIES = {
    'US',
    'GB',
    'DE', 'FR', 'ES', 'IT', 'PT', 'NL', 'BE', 'AT', 'SE', 'DK', 'FI',
    'PL', 'CZ', 'SK', 'HU', 'RO', 'BG', 'HR', 'SI', 'EE', 'LV', 'LT', 'LU',
    'GR', 'CY', 'MT', 'IE',
}

PHYSICAL_PRODUCT_TYPES = {'qs_print', 'cp_personalized'}

_CP_TYPES = {'qs_print', 'cp_personalized'}


def _get_cart(session) -> list:
    if 'cart' not in session:
        session['cart'] = []
    if 'cart_session_id' not in session:
        session['cart_session_id'] = uuid.uuid4().hex
    return session['cart']


def cart_get_items(session) -> list:
    return list(_get_cart(session))


def cart_count(session) -> int:
    return len(_get_cart(session))


def cart_add_item(session, preview_id: str, product_type: str, child_name: str,
                  story_name: str, price: float, cover_image: str = None,
                  lang: str = 'es', item_type: str = None, story_id: str = None,
                  ebook_session_id: str = None) -> str:
    _get_cart(session)
    cart = session['cart']
    item_id = uuid.uuid4().hex[:12]
    is_physical = product_type in PHYSICAL_PRODUCT_TYPES
    cart.append({
        'id': item_id,
        'preview_id': preview_id,
        'product_type': product_type,
        'item_type': item_type or _infer_item_type(product_type),
        'story_id': story_id or '',
        'child_name': child_name,
        'story_name': story_name,
        'price': round(float(price), 2),
        'cover_image': cover_image or '',
        'lang': lang,
        'is_physical': is_physical,
        'ebook_session_id': ebook_session_id or preview_id,
        'cart_session_id': session.get('cart_session_id', ''),
    })
    session.modified = True
    return item_id


def cart_remove_item(session, item_id: str) -> bool:
    cart = _get_cart(session)
    original_len = len(cart)
    session['cart'] = [i for i in cart if i['id'] != item_id]
    session.modified = True
    return len(session['cart']) < original_len


def cart_clear(session):
    session['cart'] = []
    session.modified = True


def _infer_item_type(product_type: str) -> str:
    if product_type in ('cp_personalized', 'personalized_pdf', 'personalized'):
        return 'personalized'
    if product_type in ('universo_ebook',):
        return 'universo'
    if product_type in ('qs_digital', 'qs_print'):
        return 'qs'
    return 'other'


def get_cart_shipping_estimate(country_code: str, physical_items: list) -> float:
    """
    Estimate shipping cost for the cart by calling the appropriate shipping API
    once for the highest-price physical item (single authoritative call).
    Multiple physical books share a single shipment, so we charge shipping once.
    """
    if not physical_items or not country_code:
        return 0.0
    cc = country_code.upper()
    lead_item = max(physical_items, key=lambda i: i.get('price', 0))
    lead_type = lead_item.get('product_type', '')
    if lead_type in _CP_TYPES:
        try:
            from services.cloudprinter_api_service import get_shipping_quote
            cp_options = get_shipping_quote(cc)
            if cp_options:
                return round(min(float(opt.get('total_eur', 99)) for opt in cp_options.values()), 2)
            return _fallback_shipping(cc)
        except Exception:
            return _fallback_shipping(cc)
    return _fallback_shipping(cc)


def _fallback_shipping(country_code: str) -> float:
    cc = country_code.upper()
    if cc == 'US':
        return 5.99
    if cc in EU_AND_FREE_SHIPPING_COUNTRIES:
        return 7.99
    return 12.99


def cart_summary(session, country_code: str = '') -> dict:
    raw_items = cart_get_items(session)
    subtotal = sum(i['price'] for i in raw_items)
    physical_items = [i for i in raw_items if i.get('is_physical')]
    physical_count = len(physical_items)
    cc = country_code.upper()
    free_shipping = (
        physical_count >= 2
        and cc in EU_AND_FREE_SHIPPING_COUNTRIES
    )
    has_physical = physical_count > 0
    shipping_est = 0.0
    shipping_original = 0.0
    if has_physical:
        raw_shipping = get_cart_shipping_estimate(cc, physical_items)
        shipping_original = raw_shipping
        if not free_shipping:
            shipping_est = raw_shipping

    upsell_show = (
        physical_count == 1
        and cc in EU_AND_FREE_SHIPPING_COUNTRIES
    )

    total = round(subtotal + shipping_est, 2)
    return {
        'items': raw_items,
        'item_count': len(raw_items),
        'subtotal': round(subtotal, 2),
        'shipping': shipping_est,
        'shipping_original': shipping_original,
        'free_shipping': free_shipping,
        'has_physical': has_physical,
        'physical_count': physical_count,
        'upsell_show': upsell_show,
        'total': total,
        'country_code': cc,
    }


def enrich_item_from_preview(item: dict) -> dict:
    """Try to fill in missing fields by loading the preview JSON."""
    if item.get('story_name') and item.get('child_name'):
        return item
    preview_file = f'story_previews/{item["preview_id"]}.json'
    if not os.path.exists(preview_file):
        return item
    try:
        with open(preview_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        item.setdefault('story_name', data.get('story_name', ''))
        item.setdefault('child_name', data.get('child_name', ''))
        item.setdefault('cover_image', data.get('cover_image', ''))
        item.setdefault('lang', data.get('lang', 'es'))
        item.setdefault('ebook_session_id', data.get('preview_id', item.get('preview_id', '')))
    except Exception:
        pass
    return item
