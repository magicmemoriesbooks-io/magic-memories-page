"""
Cloudprinter API Service.
Handles Quick Stories print-on-demand orders via Cloudprinter.
Product: magazine_sas_a4_p_fc (210×297mm A4 portrait saddle-stitch, 16 pages)
"""

import os
import hashlib
import requests
from typing import Optional

CLOUDPRINTER_API_BASE = "https://api.cloudprinter.com/cloudcore/1.0"

QS_PRODUCT = "magazine_sas_a4_p_fc"
# cp_ground is the standard level for this product (cp_saver not universally available)
QS_SHIPPING_LEVEL = "cp_ground"
# 130gsm Machine Coated Silk + total_pages — verified via API quote (€3.26/book)
# pageblock_200mcs does NOT exist for this product; valid options: 90, 130, 150 gsm
QS_OPTIONS = [
    {"type": "pageblock_130mcs", "count": "16"},
    {"type": "total_pages", "count": "16"},
]

CLOUDPRINTER_AVAILABLE_COUNTRIES = {
    # Europe
    'ES', 'PT', 'FR', 'DE', 'GB', 'IT', 'NL', 'BE', 'CH', 'AT',
    'PL', 'SE', 'NO', 'DK', 'FI', 'IE', 'GR', 'RO', 'CZ', 'HU',
    'HR', 'SK', 'SI', 'BG', 'CY', 'LU', 'EE', 'LV', 'LT', 'MT',
    # Americas (Canada not available for magazine_sas_a4_p_fc)
    'US', 'MX', 'AR', 'BR', 'CO', 'CL', 'PE',
    # Oceania
    'AU', 'NZ',
    # Asia-Pacific
    'SG', 'KR', 'PH', 'TH', 'MY', 'ID', 'VN', 'IN',
    # Middle East
    'AE', 'SA', 'IL',
    # Africa & Eastern Europe
    'ZA', 'EG', 'MA', 'NG', 'GH', 'TZ', 'KE', 'UA',
}

COUNTRIES_NEEDING_STATE = {'US', 'AU'}

# Legacy alias kept for backward compatibility
CLOUDPRINTER_EXCLUDED_COUNTRIES = {
    'VE', 'KP', 'SY', 'IR', 'CU', 'BY', 'MM',
}

STATUS_TRANSLATIONS = {
    "new":           {"es": "Pedido recibido",        "en": "Order received"},
    "confirmed":     {"es": "Confirmado",              "en": "Confirmed"},
    "in_production": {"es": "En impresión",            "en": "In production"},
    "sent":          {"es": "Enviado",                 "en": "Shipped"},
    "shipment_sent": {"es": "Enviado",                 "en": "Shipped"},
    "error":         {"es": "Error en pedido",         "en": "Order error"},
    "canceled":      {"es": "Cancelado",               "en": "Canceled"},
    "deleted":       {"es": "Eliminado",               "en": "Deleted"},
}


def is_sandbox_mode() -> bool:
    return os.environ.get("CLOUDPRINTER_USE_SANDBOX", "true").lower() == "true"


# ─── EUR → USD live exchange rate (cached up to 6 h) ──────────────────────────
import time as _time
_EUR_USD_RATE: float = 1.10          # conservative default
_EUR_USD_FETCHED_AT: float = 0.0
_EUR_USD_TTL: float = 6 * 3600      # 6 hours

def get_eur_usd_rate() -> float:
    """Return live EUR/USD exchange rate, cached for 6 hours."""
    global _EUR_USD_RATE, _EUR_USD_FETCHED_AT
    if _time.time() - _EUR_USD_FETCHED_AT < _EUR_USD_TTL:
        return _EUR_USD_RATE
    try:
        import requests as _req
        resp = _req.get("https://open.er-api.com/v6/latest/EUR", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            rate = float(data["rates"]["USD"])
            _EUR_USD_RATE = rate
            _EUR_USD_FETCHED_AT = _time.time()
            print(f"[CP] EUR/USD rate updated: {rate:.4f}")
    except Exception as _e:
        print(f"[CP] EUR/USD rate fetch failed ({_e}), using {_EUR_USD_RATE:.4f}")
    return _EUR_USD_RATE


def eur_to_usd(amount_eur: float) -> float:
    """Convert EUR amount to USD using live rate, rounded to 2 decimals."""
    return round(amount_eur * get_eur_usd_rate(), 2)


def _get_api_key() -> str:
    # If CLOUDPRINTER_USE_SANDBOX=true → prefer sandbox key (for Replit/testing).
    # Otherwise (VPS/production) → prefer live key first.
    if is_sandbox_mode():
        _candidates = [
            "Cloudprinter_API_KEY",
            "CLOUDPRINTER_API_KEY",
            "CLOUDPRINTER_API_KEY_SANDBOX",
            "CLOUDPRINTER_QS_API_KEY",
        ]
    else:
        _candidates = [
            "CLOUDPRINTER_QS_API_KEY",
            "Cloudprinter_API_KEY",
            "CLOUDPRINTER_API_KEY",
            "CLOUDPRINTER_API_KEY_SANDBOX",
        ]
    for name in _candidates:
        key = os.environ.get(name, "")
        if key:
            return key
    raise RuntimeError(
        "No Cloudprinter API key found. Set CLOUDPRINTER_API_KEY or CLOUDPRINTER_QS_API_KEY env var."
    )


def get_pdf_public_url(preview_id: str, filename: str = "book.pdf") -> str:
    """
    Generate a public URL for a Cloudprinter PDF file.
    Files are served from /cp-files/<preview_id>/<filename>
    """
    if is_sandbox_mode():
        dev_domain = os.environ.get('REPLIT_DEV_DOMAIN', '')
        if dev_domain:
            base_url = f"https://{dev_domain}"
        else:
            site_domain = os.environ.get('SITE_DOMAIN', 'magicmemoriesbooks.com')
            base_url = f"https://{site_domain}"
    else:
        site_domain = os.environ.get('SITE_DOMAIN', 'magicmemoriesbooks.com')
        base_url = f"https://{site_domain}"
    return f"{base_url}/cp-files/{preview_id}/{filename}"


def compute_md5(file_path: str) -> str:
    """Compute MD5 hash of a file for Cloudprinter file integrity check."""
    h = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


_SHIPPING_LEVEL_LABELS = {
    "cp_saver":  {"es": "Envío Prioritario", "en": "Priority Shipping", "days_es": "1-4 días hábiles",  "days_en": "1-4 business days"},
    "cp_ground": {"es": "Envío Económico",   "en": "Economy Shipping",  "days_es": "3-8 días hábiles",  "days_en": "3-8 business days"},
    "cp_fast":   {"es": "Envío Express",     "en": "Express Shipping",  "days_es": "1-2 días hábiles",  "days_en": "1-2 business days"},
}
_PREFERRED_SHIPPING = ["cp_saver", "cp_ground", "cp_fast"]


def _make_shipping_key(level: str, service: str) -> str:
    """Build a unique display key for a shipping option, adding a carrier suffix when multiple carriers share a level."""
    if not service:
        return level
    safe = service.lower().replace(' ', '_').replace('-', '_')
    safe = ''.join(c for c in safe if c.isalnum() or c == '_')[:20].strip('_')
    return f"{level}_{safe}" if safe else level


def resolve_shipping_level(key: str) -> str:
    """Resolve a composite shipping key (e.g. cp_ground_ups) to the CP API level (cp_ground)."""
    for lvl in ['cp_ground', 'cp_saver', 'cp_fast', 'cp_economy', 'cp_standard', 'cp_priority']:
        if key == lvl or key.startswith(lvl + '_'):
            return lvl
    return key


def get_shipping_quote(country_code: str, state_code: str = '') -> dict:
    """
    Get shipping quote from Cloudprinter for QS product to a given country.
    Returns dict of available shipping options with costs, or empty dict on failure.

    For US and AU, state_code is required by the CP API.

    API response format (magazine_sas_a4_p_fc):
      {
        "subtotals": {"items": "3.26", ...},  ← print cost only
        "price": "3.26",                       ← print cost (NOT total)
        "shipments": [{"quotes": [
          {"shipping_level": "cp_ground", "price": "12.88", ...},
          {"shipping_level": "cp_fast",   "price": "18.52", ...},
        ]}]
      }
    """
    api_key = _get_api_key()
    mode = "SANDBOX" if is_sandbox_mode() else "PRODUCTION"
    cc = country_code.upper()
    state = state_code.upper().strip() if state_code else ''
    print(f"[CP API] Shipping quote to {cc}{' state=' + state if state else ''} ({mode})")

    if cc not in CLOUDPRINTER_AVAILABLE_COUNTRIES:
        print(f"[CP API] Country {cc} not in CP available list for magazine_sas_a4_p_fc")
        return {}

    # US and AU require a state code — use a default if not provided
    if cc in COUNTRIES_NEEDING_STATE and not state:
        state = 'CA' if cc == 'US' else 'NSW'
        print(f"[CP API] {cc} needs state_code; defaulting to {state}")

    # Quote without shipping_level to receive all available shipping options
    payload = {
        "apikey": api_key,
        "country": cc,
        "currency": "USD",
        "items": [{
            "reference": "quote-1",
            "product": QS_PRODUCT,
            "count": "1",
            "options": QS_OPTIONS
        }]
    }
    if state:
        payload["state"] = state

    try:
        resp = requests.post(
            f"{CLOUDPRINTER_API_BASE}/orders/quote",
            json=payload,
            timeout=20
        )
        if resp.status_code != 200:
            print(f"[CP API] Quote failed {resp.status_code}: {resp.text[:200]}")
            return {}

        data = resp.json()

        if isinstance(data, dict) and "error" in data:
            err = data["error"]
            print(f"[CP API] Quote error for {country_code}: {err}")
            return {}

        if not isinstance(data, dict) or "subtotals" not in data:
            print(f"[CP API] Unexpected quote response: {data}")
            return {}

        print_cost_usd = float(data["subtotals"].get("items", "3.26"))
        currency = data.get("currency", "USD")

        # Collect all shipping options from all shipments
        shipping_quotes = []
        for shipment in data.get("shipments", []):
            for q in shipment.get("quotes", []):
                shipping_quotes.append(q)

        if not shipping_quotes:
            print(f"[CP API] No shipping options for {country_code}")
            return {}

        # Build result dict keyed by composite "level_carrier" to show all distinct options.
        result = {}
        for q in shipping_quotes:
            level   = q.get("shipping_level", "")
            service = q.get("service", "")
            key     = _make_shipping_key(level, service)
            ship_usd = float(q.get("price", "0"))
            total_usd = round(print_cost_usd + ship_usd, 2)
            labels = _SHIPPING_LEVEL_LABELS.get(level, {
                "es": "Envío", "en": "Shipping",
                "days_es": "7-20 días hábiles", "days_en": "7-20 business days"
            })
            if key in result and result[key]["cp_cost_usd"] <= ship_usd:
                continue
            result[key] = {
                "name_es": labels['es'],
                "name_en": labels['en'],
                "days_es": labels["days_es"],
                "days_en": labels["days_en"],
                "service": service,
                "cp_cost_usd": ship_usd,
                "cp_cost_eur": ship_usd,
                "print_cost_usd": print_cost_usd,
                "print_cost_eur": print_cost_usd,
                "total_usd": total_usd,
                "total_eur": total_usd,
                "shipping_level": level,
                "currency": currency,
            }

        # Log cheapest available option per preferred level
        logged = False
        for preferred in _PREFERRED_SHIPPING:
            for key, opt in result.items():
                if opt["shipping_level"] == preferred and not logged:
                    print(f"[CP API] Cheapest {preferred} to {country_code}: key={key} ${opt['total_usd']:.2f} USD (print ${print_cost_usd:.2f} + ship ${opt['cp_cost_usd']:.2f})")
                    logged = True
            if logged:
                break

        return result

    except Exception as e:
        print(f"[CP API] Quote exception for {country_code}: {e}")
        return {}


def submit_print_order(
    preview_id: str,
    pdf_path: str,
    pdf_url: str,
    customer_data: dict,
    shipping_address: dict,
) -> tuple:
    """
    Submit a print order to Cloudprinter.

    Args:
        preview_id: Story preview ID (used as order reference)
        pdf_path: Local path to the combined PDF (for MD5)
        pdf_url: Public URL to the combined PDF
        customer_data: {"email": "..."}
        shipping_address: {name, street1, street2, city, state, postcode, country_code, phone}

    Returns:
        (success: bool, message: str, order_ref: str or None)
    """
    import time as _t
    api_key = _get_api_key()
    mode = "SANDBOX" if is_sandbox_mode() else "PRODUCTION"
    ts = str(int(_t.time()))[-6:]
    order_ref = f"MM-{preview_id[:10]}-{ts}"

    print(f"[CP API] Submitting order {order_ref} ({mode})")

    try:
        md5sum = compute_md5(pdf_path)
    except Exception as e:
        return False, f"MD5 computation failed: {e}", None

    addr = shipping_address
    raw_name = addr.get("name", "")
    name_parts = raw_name.rsplit(" ", 1) if " " in raw_name else [raw_name, ""]
    firstname = name_parts[0]
    lastname = name_parts[1] if len(name_parts) > 1 else "."

    raw_street1 = (addr.get("street1", "") or "").strip()
    raw_street2 = (addr.get("street2", "") or "").strip()
    # CP limit is 40 chars per line. If both lines fit together, merge so the
    # courier always sees the complete address on the main label line.
    if raw_street2 and len(raw_street1) + 1 + len(raw_street2) <= 40:
        final_street1 = f"{raw_street1} {raw_street2}"
        final_street2 = ""
    else:
        final_street1 = raw_street1[:40]
        final_street2 = raw_street2[:40]
    print(f"[CP API] Address → street1='{final_street1}' street2='{final_street2}' "
          f"city='{addr.get('city','')}' postcode='{addr.get('postcode',addr.get('postal_code',''))}' "
          f"country='{addr.get('country_code','US')}'")

    payload = {
        "apikey": api_key,
        "reference": order_ref,
        "email": "print@magicmemoriesbooks.com",
        "addresses": [{
            "type": "delivery",
            "company": "",
            "firstname": firstname,
            "lastname": lastname or ".",
            "street1": final_street1,
            "street2": final_street2,
            "zip": addr.get("postcode", addr.get("postal_code", "")),
            "city": addr.get("city", ""),
            "state": addr.get("state_code", addr.get("state", "")),
            "country": addr.get("country_code", "US"),
            "phone": addr.get("phone_number", addr.get("phone", "")) or "+10000000000",
            "email": "print@magicmemoriesbooks.com"
        }],
        "items": [{
            "reference": "qs-1",
            "product": QS_PRODUCT,
            "count": "1",
            "shipping_level": QS_SHIPPING_LEVEL,
            "files": [{
                "type": "product",
                "url": pdf_url,
                "md5sum": md5sum
            }],
            "options": QS_OPTIONS
        }]
    }

    try:
        resp = requests.post(
            f"{CLOUDPRINTER_API_BASE}/orders/add",
            json=payload,
            timeout=60
        )
        if resp.status_code in [200, 201]:
            data = resp.json()
            if isinstance(data, dict) and data.get("referenceid"):
                cp_ref = data.get("referenceid", order_ref)
                print(f"[CP API] Order submitted OK: {cp_ref}")
                return True, "Order submitted successfully", cp_ref
            elif isinstance(data, dict) and data.get("order"):
                # Cloudprinter sometimes returns {"order": "reference"} instead of {"referenceid": ...}
                cp_ref = data.get("order", order_ref)
                print(f"[CP API] Order submitted OK (order key): {cp_ref}")
                return True, "Order submitted successfully", cp_ref
            elif isinstance(data, dict) and data.get("error"):
                err = data["error"]
                msg = f"{err.get('type','error')}: {err.get('info','')}" if isinstance(err, dict) else str(err)
                print(f"[CP API] Order error: {msg}")
                return False, msg, None
            print(f"[CP API] Unexpected response: {data}")
            return True, "Order submitted (unexpected response format)", order_ref
        else:
            if resp.status_code == 401:
                msg = ("Cloudprinter rechazó la clave API (401 Unauthorized). "
                       "La clave de producción CLOUDPRINTER_QS_API_KEY puede haber expirado. "
                       "Accede al portal Cloudprinter para regenerar la clave y actualiza el .env del servidor.")
            elif resp.status_code == 422:
                msg = f"Cloudprinter rechazó los datos del pedido (422): {resp.text[:200]}"
            else:
                msg = f"HTTP {resp.status_code}: {resp.text[:300]}"
            print(f"[CP API] Submit failed: {msg}")
            return False, msg, None
    except Exception as e:
        print(f"[CP API] Submit exception: {e}")
        return False, str(e), None


# ─── Personalized Book (Casewrap Hardcover A4) ────────────────────────────────

PB_PRODUCT = "photobook_cw_a4_p_fc"

PB_OPTIONS_24P = [
    {"type": "pageblock_200mcs", "count": "24"},
    {"type": "total_pages",      "count": "24"},
]

PB_OPTIONS_26P = [
    {"type": "pageblock_200mcs", "count": "26"},
    {"type": "total_pages",      "count": "26"},
]


def _build_pb_options(page_count: Optional[int] = None) -> list:
    """
    Build the Cloudprinter options list for a PB order/quote.
    Includes all required options: main paper, cover paper, cover finish, total pages.
    Uses pageblock_200mcg (Global default) + cover_130mcg + cover_finish_gloss.
    """
    n = page_count if page_count is not None else get_pb_chosen_page_count()
    return [
        {"type": "pageblock_200mcg",   "count": str(n)},  # 200gsm Machine Coated Gloss (Global default)
        {"type": "cover_130mcg",       "count": "1"},      # Cover paper 130gsm MCG (default)
        {"type": "cover_finish_gloss", "count": "1"},      # Gloss lamination (default)
        {"type": "total_pages",        "count": str(n)},
    ]

# Verified via /products/info at startup; see verify_pb_page_counts() / get_pb_chosen_page_count()
_PB_VALID_PAGE_COUNTS: Optional[set] = None  # None = not yet probed; set() = probed result
_PB_CHOSEN_PAGE_COUNT: int = 26              # runtime-selected page count (26 default; verified via CP quote)
_PB_CANDIDATE_COUNTS = (24, 26)              # candidates to check, in preference order (26 preferred)


def verify_pb_page_counts() -> int:
    """
    Query /products/info for PB_PRODUCT to determine which page counts are valid
    (24 and/or 26).  Selects the highest supported count (26 if available, else 24).
    Results are cached in-process.

    Returns the chosen page count (24 or 26).
    Gracefully degrades to 24 on network/API error.
    Logs the outcome for audit purposes.
    """
    global _PB_VALID_PAGE_COUNTS, _PB_CHOSEN_PAGE_COUNT
    if _PB_VALID_PAGE_COUNTS is not None:
        return _PB_CHOSEN_PAGE_COUNT

    try:
        api_key = _get_api_key()
        url = f"{CLOUDPRINTER_API_BASE}/products/info"
        payload = {"apikey": api_key, "reference": PB_PRODUCT}
        resp = requests.post(url, json=payload, timeout=15)
        resp.raise_for_status()
        info = resp.json()

        # Extract valid page counts from the total_pages option list.
        # If the values list is empty (CP returns option with no explicit values),
        # treat that as "any count is allowed" and keep the current default.
        valid: set = set()
        for opt in info.get("options", []):
            if opt.get("type") == "total_pages":
                for val in opt.get("values", []):
                    try:
                        valid.add(int(val))
                    except (ValueError, TypeError):
                        pass

        if not valid:
            # No explicit constraints from CP — keep the hardcoded default (26)
            _PB_VALID_PAGE_COUNTS = set(_PB_CANDIDATE_COUNTS)
        else:
            _PB_VALID_PAGE_COUNTS = valid

        # Select best supported count: prefer 26, fall back to 24
        chosen = 24
        for candidate in sorted(_PB_CANDIDATE_COUNTS, reverse=True):
            if candidate in _PB_VALID_PAGE_COUNTS:
                chosen = candidate
                break
        _PB_CHOSEN_PAGE_COUNT = chosen

        print(f"[CP PB VERIFY] Product {PB_PRODUCT}: valid page counts={sorted(_PB_VALID_PAGE_COUNTS)}; "
              f"chosen={_PB_CHOSEN_PAGE_COUNT}")
        return _PB_CHOSEN_PAGE_COUNT

    except Exception as exc:
        # Network or API error — graceful degradation to 26 (verified via CP quote)
        print(f"[CP PB VERIFY] /products/info request failed for {PB_PRODUCT}: {exc}")
        _PB_VALID_PAGE_COUNTS = set(_PB_CANDIDATE_COUNTS)
        _PB_CHOSEN_PAGE_COUNT = 26
        return 26


def verify_pb_page_count(page_count: int = 24) -> bool:
    """
    Backward-compatible wrapper: verify a specific page count and return True/False.
    Also triggers the full capability probe (verify_pb_page_counts) if not yet done.
    """
    verify_pb_page_counts()
    return page_count in (_PB_VALID_PAGE_COUNTS or {24})


def get_pb_chosen_page_count() -> int:
    """Return the runtime-chosen page count for the PB casewrap product (24 or 26)."""
    if _PB_VALID_PAGE_COUNTS is None:
        verify_pb_page_counts()
    return _PB_CHOSEN_PAGE_COUNT


_PB_SHIPPING_LEVEL_LABELS = {
    "cp_saver":  {"es": "Envío Prioritario", "en": "Priority Shipping", "days_es": "1-4 días hábiles",  "days_en": "1-4 business days"},
    "cp_ground": {"es": "Envío Económico",   "en": "Economy Shipping",  "days_es": "3-8 días hábiles",  "days_en": "3-8 business days"},
    "cp_fast":   {"es": "Envío Express",     "en": "Express Shipping",  "days_es": "1-2 días hábiles",  "days_en": "1-2 business days"},
}
_PB_PREFERRED_SHIPPING = ["cp_saver", "cp_ground", "cp_fast"]


def get_pb_shipping_quote(country_code: str, state_code: str = '') -> dict:
    """
    Get shipping quote from Cloudprinter for the PB casewrap product to a given country.
    Returns dict of available shipping options, or empty dict on failure.
    """
    api_key = _get_api_key()
    mode = "SANDBOX" if is_sandbox_mode() else "PRODUCTION"
    cc = country_code.upper()
    state = state_code.upper().strip() if state_code else ''
    print(f"[CP PB API] Shipping quote to {cc}{' state=' + state if state else ''} ({mode})")

    if cc not in CLOUDPRINTER_AVAILABLE_COUNTRIES:
        print(f"[CP PB API] Country {cc} not in CP available list")
        return {}

    if cc in COUNTRIES_NEEDING_STATE and not state:
        state = 'CA' if cc == 'US' else 'NSW'
        print(f"[CP PB API] {cc} needs state_code; defaulting to {state}")

    payload = {
        "apikey": api_key,
        "country": cc,
        "currency": "USD",
        "items": [{
            "reference": "pb-quote-1",
            "product": PB_PRODUCT,
            "count": "1",
            "options": _build_pb_options(),
        }]
    }
    if state:
        payload["state"] = state

    try:
        resp = requests.post(
            f"{CLOUDPRINTER_API_BASE}/orders/quote",
            json=payload,
            timeout=20
        )
        if resp.status_code != 200:
            print(f"[CP PB API] Quote failed {resp.status_code}: {resp.text[:200]}")
            return {}

        data = resp.json()
        if isinstance(data, dict) and "error" in data:
            print(f"[CP PB API] Quote error: {data['error']}")
            return {}
        if not isinstance(data, dict) or "subtotals" not in data:
            print(f"[CP PB API] Unexpected quote response: {data}")
            return {}

        print_cost_usd = float(data["subtotals"].get("items", "12.0"))
        currency = data.get("currency", "USD")

        shipping_quotes = []
        for shipment in data.get("shipments", []):
            for q in shipment.get("quotes", []):
                shipping_quotes.append(q)

        if not shipping_quotes:
            print(f"[CP PB API] No shipping options for {country_code}")
            return {}

        result = {}
        for q in shipping_quotes:
            level   = q.get("shipping_level", "")
            service = q.get("service", "")
            option  = q.get("shipping_option", "")
            ship_usd = float(q.get("price", "0"))
            total_usd = round(print_cost_usd + ship_usd, 2)
            labels = _PB_SHIPPING_LEVEL_LABELS.get(level, {
                "es": "Envío", "en": "Shipping",
                "days_es": "7-20 días hábiles", "days_en": "7-20 business days"
            })
            # Use composite key to show all distinct carriers, even when sharing a level.
            key = _make_shipping_key(level, service)
            if key in result and result[key]["cp_cost_usd"] <= ship_usd:
                continue
            result[key] = {
                "name_es":        labels['es'],
                "name_en":        labels['en'],
                "days_es":        labels["days_es"],
                "days_en":        labels["days_en"],
                "service":        service,
                "carrier":        option,
                "cp_cost_usd":    ship_usd,
                "cp_cost_eur":    ship_usd,
                "print_cost_usd": print_cost_usd,
                "print_cost_eur": print_cost_usd,
                "total_usd":      total_usd,
                "total_eur":      total_usd,
                "shipping_level": level,
                "currency":       currency,
            }

        for preferred in _PB_PREFERRED_SHIPPING:
            for key, opt in result.items():
                if opt["shipping_level"] == preferred:
                    print(f"[CP PB API] Best to {country_code}: {preferred} "
                          f"${opt['total_usd']:.2f} USD "
                          f"(prod ${print_cost_usd:.2f} + ship ${opt['cp_cost_usd']:.2f})")
                    break
            else:
                continue
            break

        return result

    except Exception as e:
        print(f"[CP PB API] Quote exception for {country_code}: {e}")
        return {}


def submit_pb_print_order(
    preview_id: str,
    cover_pdf_path: str,
    cover_pdf_url: str,
    content_pdf_path: str,
    content_pdf_url: str,
    customer_data: dict,
    shipping_address: dict,
    shipping_level: str = "cp_saver",
) -> tuple:
    """
    Submit a 2-file casewrap photobook order to Cloudprinter.

    Args:
        preview_id:       Story preview ID (used as order reference)
        cover_pdf_path:   Local path to cover.pdf (for MD5)
        cover_pdf_url:    Public URL to cover.pdf
        content_pdf_path: Local path to content.pdf (for MD5)
        content_pdf_url:  Public URL to content.pdf
        customer_data:    {"email": "..."}
        shipping_address: {name, street1, street2, city, state_code, postcode, country_code, phone}
        shipping_level:   CP shipping level string (default "cp_saver")

    Returns:
        (success: bool, message: str, order_ref: str or None)
    """
    api_key = _get_api_key()
    mode = "SANDBOX" if is_sandbox_mode() else "PRODUCTION"
    order_ref = f"MMPB-{preview_id[:12]}"

    print(f"[CP PB API] Submitting PB order {order_ref} ({mode}) shipping_level={shipping_level}")

    try:
        cover_md5   = compute_md5(cover_pdf_path)
        content_md5 = compute_md5(content_pdf_path)
    except Exception as e:
        return False, f"MD5 computation failed: {e}", None

    addr = shipping_address
    raw_name = addr.get("name", "")
    name_parts = raw_name.rsplit(" ", 1) if " " in raw_name else [raw_name, ""]
    firstname = name_parts[0]
    lastname = name_parts[1] if len(name_parts) > 1 else "."

    raw_street1 = (addr.get("street1", "") or "").strip()
    raw_street2 = (addr.get("street2", "") or "").strip()
    if raw_street2 and len(raw_street1) + 1 + len(raw_street2) <= 40:
        final_street1 = f"{raw_street1} {raw_street2}"
        final_street2 = ""
    else:
        final_street1 = raw_street1[:40]
        final_street2 = raw_street2[:40]
    print(f"[CP PB API] Address → street1='{final_street1}' street2='{final_street2}' "
          f"city='{addr.get('city','')}' postcode='{addr.get('postcode',addr.get('postal_code',''))}' "
          f"country='{addr.get('country_code','ES')}'")

    payload = {
        "apikey": api_key,
        "reference": order_ref,
        "email": "print@magicmemoriesbooks.com",
        "addresses": [{
            "type": "delivery",
            "company": "",
            "firstname": firstname,
            "lastname": lastname or ".",
            "street1": final_street1,
            "street2": final_street2,
            "zip": addr.get("postcode", addr.get("postal_code", "")),
            "city": addr.get("city", ""),
            "state": addr.get("state_code", addr.get("state", "")),
            "country": addr.get("country_code", "US"),
            "phone": addr.get("phone_number", addr.get("phone", "")) or "+10000000000",
            "email": "print@magicmemoriesbooks.com"
        }],
        "items": [{
            "reference": "pb-1",
            "product": PB_PRODUCT,
            "count": "1",
            "shipping_level": shipping_level,
            "files": [
                {
                    "type": "cover",
                    "url": cover_pdf_url,
                    "md5sum": cover_md5,
                },
                {
                    "type": "book",
                    "url": content_pdf_url,
                    "md5sum": content_md5,
                },
            ],
            "options": _build_pb_options(),
        }]
    }

    try:
        resp = requests.post(
            f"{CLOUDPRINTER_API_BASE}/orders/add",
            json=payload,
            timeout=60
        )
        if resp.status_code in [200, 201]:
            data = resp.json()
            if isinstance(data, dict) and data.get("referenceid"):
                cp_ref = data.get("referenceid", order_ref)
                print(f"[CP PB API] PB order submitted OK: {cp_ref}")
                return True, "PB order submitted successfully", cp_ref
            elif isinstance(data, dict) and data.get("error"):
                err = data["error"]
                msg = f"{err.get('type','error')}: {err.get('info','')}" if isinstance(err, dict) else str(err)
                print(f"[CP PB API] Order error: {msg}")
                return False, msg, None
            print(f"[CP PB API] Unexpected response: {data}")
            return True, "PB order submitted (unexpected response format)", order_ref
        else:
            msg = f"HTTP {resp.status_code}: {resp.text[:300]}"
            print(f"[CP PB API] Submit failed: {msg}")
            return False, msg, None
    except Exception as e:
        print(f"[CP PB API] Submit exception: {e}")
        return False, str(e), None


def get_order_status(cp_order_ref: str) -> Optional[dict]:
    """
    Get Cloudprinter order status and tracking info.

    Returns:
    {
        "status": "sent",
        "status_text": {"es": "Enviado", "en": "Shipped"},
        "tracking_number": "...",
        "tracking_url": "...",
        "carrier": "...",
        "updated_at": "..."
    }
    """
    api_key = _get_api_key()
    payload = {"apikey": api_key, "reference": cp_order_ref}

    try:
        resp = requests.post(
            f"{CLOUDPRINTER_API_BASE}/orders/get",
            json=payload,
            timeout=20
        )
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list) and data:
                order = data[0]
            elif isinstance(data, dict):
                order = data
            else:
                return None

            status = order.get("state", order.get("status", "unknown"))
            status_text = STATUS_TRANSLATIONS.get(status, {"es": status, "en": status})

            tracking_number = None
            tracking_url = None
            carrier = None

            shipments = order.get("shipments", order.get("tracking", []))
            if isinstance(shipments, list) and shipments:
                first = shipments[0]
                tracking_number = first.get("tracking_number") or first.get("trackingcode")
                tracking_url = first.get("tracking_url") or first.get("trackingurl")
                carrier = first.get("carrier_name") or first.get("carrier")

            # Extract delivery address from CP response for verification
            cp_address = None
            addresses = order.get("addresses", [])
            if isinstance(addresses, list):
                for a in addresses:
                    if isinstance(a, dict) and a.get("type") == "delivery":
                        cp_address = {
                            "name": f"{a.get('firstname','')} {a.get('lastname','')}".strip(),
                            "street1": a.get("street1", ""),
                            "street2": a.get("street2", ""),
                            "city": a.get("city", ""),
                            "postcode": a.get("zip", ""),
                            "country": a.get("country", ""),
                        }
                        break

            return {
                "status": status,
                "status_text": status_text,
                "tracking_number": tracking_number,
                "tracking_url": tracking_url,
                "carrier": carrier,
                "updated_at": order.get("updated_at", order.get("date_modified", "")),
                "cp_address": cp_address,
                "raw": order,
            }
        else:
            print(f"[CP API] Status fetch failed {resp.status_code}: {resp.text[:200]}")
            return None
    except Exception as e:
        print(f"[CP API] Status exception: {e}")
        return None
