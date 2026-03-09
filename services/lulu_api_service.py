"""
Lulu Print API Service.
Handles authentication and print job creation with Lulu's API.
Supports both production and sandbox environments.
"""

import os
import json
import base64
import requests
from typing import Optional, Tuple
from datetime import datetime


# US State name to code mapping
US_STATE_CODES = {
    "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR",
    "california": "CA", "colorado": "CO", "connecticut": "CT", "delaware": "DE",
    "florida": "FL", "georgia": "GA", "hawaii": "HI", "idaho": "ID",
    "illinois": "IL", "indiana": "IN", "iowa": "IA", "kansas": "KS",
    "kentucky": "KY", "louisiana": "LA", "maine": "ME", "maryland": "MD",
    "massachusetts": "MA", "michigan": "MI", "minnesota": "MN", "mississippi": "MS",
    "missouri": "MO", "montana": "MT", "nebraska": "NE", "nevada": "NV",
    "new hampshire": "NH", "new jersey": "NJ", "new mexico": "NM", "new york": "NY",
    "north carolina": "NC", "north dakota": "ND", "ohio": "OH", "oklahoma": "OK",
    "oregon": "OR", "pennsylvania": "PA", "rhode island": "RI", "south carolina": "SC",
    "south dakota": "SD", "tennessee": "TN", "texas": "TX", "utah": "UT",
    "vermont": "VT", "virginia": "VA", "washington": "WA", "west virginia": "WV",
    "wisconsin": "WI", "wyoming": "WY", "district of columbia": "DC",
    "puerto rico": "PR", "guam": "GU", "virgin islands": "VI"
}


def normalize_state_code(state: str, country_code: str = "US") -> str:
    """
    Normalize state name to 2-letter code for US addresses.
    Returns the original value if already a valid code or not a US address.
    """
    if not state:
        return ""
    
    state_clean = state.strip()
    
    # If already a 2-letter code, return uppercase
    if len(state_clean) <= 3:
        return state_clean.upper()
    
    # Only normalize US states
    if country_code.upper() in ["US", "USA"]:
        state_lower = state_clean.lower()
        if state_lower in US_STATE_CODES:
            return US_STATE_CODES[state_lower]
    
    return state_clean


def get_lulu_base_url() -> str:
    """Get Lulu API base URL based on environment."""
    use_sandbox = os.environ.get("LULU_USE_SANDBOX", "true").lower() == "true"
    if use_sandbox:
        return "https://api.sandbox.lulu.com"
    return "https://api.lulu.com"


LULU_API_BASE = get_lulu_base_url()
LULU_AUTH_URL = f"{LULU_API_BASE}/auth/realms/glasstree/protocol/openid-connect/token"


def is_sandbox_mode() -> bool:
    """Check if using Lulu sandbox environment."""
    return os.environ.get("LULU_USE_SANDBOX", "true").lower() == "true"


def get_lulu_credentials() -> Tuple[str, str]:
    """Get Lulu API credentials from environment.
    Uses sandbox credentials when in sandbox mode, production credentials otherwise.
    """
    if is_sandbox_mode():
        client_key = os.environ.get("LULU_SANDBOX_CLIENT_KEY", "")
        client_secret = os.environ.get("LULU_SANDBOX_CLIENT_SECRET", "")
    else:
        client_key = os.environ.get("LULU_CLIENT_KEY", "")
        client_secret = os.environ.get("LULU_CLIENT_SECRET", "")
    return client_key, client_secret


def get_access_token() -> Optional[str]:
    """
    Authenticate with Lulu API and get access token.
    Returns the access token or None if authentication fails.
    """
    client_key, client_secret = get_lulu_credentials()
    
    env_mode = "SANDBOX" if is_sandbox_mode() else "PRODUCTION"
    print(f"[LULU API] Using {env_mode} environment: {LULU_API_BASE}")
    
    if not client_key or not client_secret:
        print("[LULU API] ERROR: Credentials not configured")
        print("[LULU API] Set LULU_CLIENT_KEY and LULU_CLIENT_SECRET")
        return None
    
    auth_string = base64.b64encode(f"{client_key}:{client_secret}".encode()).decode()
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {auth_string}"
    }
    
    data = {"grant_type": "client_credentials"}
    
    auth_url = f"{LULU_API_BASE}/auth/realms/glasstree/protocol/openid-connect/token"
    
    try:
        response = requests.post(auth_url, headers=headers, data=data, timeout=30)
        
        if response.status_code == 200:
            token_data = response.json()
            print(f"[LULU API] Authentication successful ({env_mode})")
            return token_data.get("access_token")
        else:
            print(f"[LULU API] Authentication failed: {response.status_code}")
            print(f"[LULU API] Response: {response.text[:200]}")
            return None
            
    except Exception as e:
        print(f"[LULU API] Authentication error: {e}")
        return None


def get_public_file_url(order_folder: str, filename: str) -> Optional[str]:
    """
    Generate a public URL for a file in the Lulu orders folder.
    This URL should be accessible by Lulu's servers to download the PDF.
    
    Note: In production, you might need to host files on S3, Cloudflare R2, or similar.
    For now, we use the app's own URL to serve the files.
    """
    base_url = os.environ.get('REPLIT_DEV_DOMAIN', '')
    if base_url:
        base_url = f"https://{base_url}"
    else:
        base_url = os.environ.get('PUBLIC_URL', 'http://localhost:5000')
    
    folder_name = os.path.basename(order_folder)
    file_url = f"{base_url}/lulu-files/{folder_name}/{filename}"
    print(f"[LULU API] Generated public URL: {file_url}")
    return file_url


def create_print_job_with_urls(
    interior_url: str,
    cover_url: str,
    title: str,
    quantity: int = 1,
    shipping_address: Optional[dict] = None,
    shipping_level: str = "MAIL",
    access_token: Optional[str] = None,
    pod_package_id: str = "0827X1169FCPRECW080CW444GXX"
) -> Optional[dict]:
    """
    Create a print job with Lulu using public URLs for files.
    
    Args:
        interior_url: Public URL to interior PDF
        cover_url: Public URL to cover PDF
        title: Book title
        quantity: Number of copies
        shipping_address: Shipping address dictionary
        shipping_level: Shipping method (MAIL, PRIORITY_MAIL, GROUND, EXPEDITED, EXPRESS)
        access_token: Lulu API access token
    
    Returns:
        Print job data or None if creation fails
    """
    if not access_token:
        access_token = get_access_token()
        if not access_token:
            return None
    
    url = f"{LULU_API_BASE}/print-jobs/"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    line_item = {
        "title": title,
        "quantity": quantity,
        "cover": {
            "source_url": cover_url
        },
        "interior": {
            "source_url": interior_url
        },
        "pod_package_id": pod_package_id
    }
    
    # Normalize shipping address fields for Lulu API
    lulu_shipping = {}
    if shipping_address:
        country = shipping_address.get("country_code", "US")
        lulu_shipping = {
            "name": shipping_address.get("name", ""),
            "street1": shipping_address.get("street1", ""),
            "street2": shipping_address.get("street2", ""),
            "city": shipping_address.get("city", ""),
            "state_code": normalize_state_code(shipping_address.get("state_code", ""), country),
            "postcode": shipping_address.get("postcode") or shipping_address.get("postal_code", ""),
            "country_code": country,
            "phone_number": shipping_address.get("phone_number", ""),
            "email": shipping_address.get("email", "")
        }
        
        tax_id = shipping_address.get("recipient_tax_id", "")
        if tax_id:
            lulu_shipping["recipient_tax_id"] = tax_id
        
        # Validate and auto-correct address with Lulu (gets ZIP+4 for US addresses)
        try:
            validation_result = validate_shipping_address(lulu_shipping)
            if validation_result.get("suggested_address"):
                suggested = validation_result["suggested_address"]
                print(f"[LULU API] Using suggested address from Lulu (ZIP+4: {suggested.get('postcode')})")
                # Update address fields with Lulu's suggestions, keep name/phone/email
                lulu_shipping["street1"] = suggested.get("street1", lulu_shipping["street1"])
                lulu_shipping["street2"] = suggested.get("street2", lulu_shipping["street2"])
                lulu_shipping["city"] = suggested.get("city", lulu_shipping["city"])
                lulu_shipping["state_code"] = suggested.get("state_code", lulu_shipping["state_code"])
                lulu_shipping["postcode"] = suggested.get("postcode", lulu_shipping["postcode"])
        except Exception as e:
            print(f"[LULU API] Address validation skipped: {e}")
    
    payload = {
        "line_items": [line_item],
        "contact_email": lulu_shipping.get("email", ""),
        "shipping_level": shipping_level,
        "shipping_address": lulu_shipping
    }
    
    print(f"[LULU API] Creating print job with URLs:")
    print(f"[LULU API] Interior: {interior_url}")
    print(f"[LULU API] Cover: {cover_url}")
    print(f"[LULU API] Shipping: {shipping_level}")
    
    levels_to_try = [shipping_level]
    try:
        idx = SHIPPING_FALLBACK_ORDER.index(shipping_level)
        levels_to_try = SHIPPING_FALLBACK_ORDER[idx:]
    except ValueError:
        levels_to_try = [shipping_level] + SHIPPING_FALLBACK_ORDER
    levels_to_try = list(dict.fromkeys(levels_to_try))
    
    for level in levels_to_try:
        payload["shipping_level"] = level
        print(f"[LULU API] Trying shipping level: {level}")
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            
            if response.status_code in [200, 201]:
                job_data = response.json()
                job_id = job_data.get("id")
                if level != shipping_level:
                    print(f"[LULU API] Shipping '{shipping_level}' not available, used '{level}' instead")
                print(f"[LULU API] Print job created: {job_id}")
                
                print(f"[LULU API] Print job full response keys: {list(job_data.keys())}")
                job_status = job_data.get("status", {})
                print(f"[LULU API] Print job status: {json.dumps(job_status, indent=2) if isinstance(job_status, dict) else job_status}")
                job_warnings = []
                if isinstance(job_status, dict):
                    job_warnings = job_status.get("messages", [])
                if not job_warnings:
                    job_warnings = job_data.get("warnings", [])
                if not job_warnings:
                    for key in job_data:
                        val = job_data[key]
                        if isinstance(val, list) and val and isinstance(val[0], dict) and ("address" in str(val[0]).lower() or "suggest" in str(val[0]).lower()):
                            job_warnings = val
                            print(f"[LULU API] Found warnings in key '{key}'")
                            break
                print(f"[LULU API] Print job warnings: {json.dumps(job_warnings, indent=2) if job_warnings else 'none'}")
                
                suggested_addr = None
                for msg in job_warnings:
                    if isinstance(msg, dict) and msg.get("suggested_address"):
                        suggested_addr = msg["suggested_address"]
                        break
                    if isinstance(msg, dict) and "address" in str(msg).lower():
                        sa = msg.get("suggested_address") or msg.get("recommendedAddress")
                        if sa:
                            suggested_addr = sa
                            break
                
                if suggested_addr and job_id:
                    print(f"[LULU API] Lulu suggested a better address, canceling job {job_id} and recreating...")
                    print(f"[LULU API]   Original: {lulu_shipping.get('street1')}, {lulu_shipping.get('postcode')}")
                    print(f"[LULU API]   Suggested: {suggested_addr.get('street1')}, {suggested_addr.get('postcode')}")
                    try:
                        cancel_url = f"{LULU_API_BASE}/print-jobs/{job_id}/status/"
                        requests.put(cancel_url, headers=headers, json={"name": "CANCELED"}, timeout=30)
                        print(f"[LULU API] Job {job_id} canceled, recreating with corrected address...")
                        
                        lulu_shipping["street1"] = suggested_addr.get("street1", lulu_shipping["street1"])
                        lulu_shipping["street2"] = suggested_addr.get("street2", lulu_shipping.get("street2", ""))
                        lulu_shipping["city"] = suggested_addr.get("city", lulu_shipping["city"])
                        lulu_shipping["state_code"] = suggested_addr.get("state_code", lulu_shipping["state_code"])
                        lulu_shipping["postcode"] = suggested_addr.get("postcode", lulu_shipping["postcode"])
                        payload["shipping_address"] = lulu_shipping
                        
                        retry_response = requests.post(url, headers=headers, json=payload, timeout=60)
                        if retry_response.status_code in [200, 201]:
                            retry_data = retry_response.json()
                            retry_id = retry_data.get("id")
                            print(f"[LULU API] Recreated print job with corrected address: {retry_id}")
                            retry_data['_actual_shipping_level'] = level
                            retry_data['_address_corrected'] = True
                            return retry_data
                        else:
                            print(f"[LULU API] Retry failed ({retry_response.status_code}), using original job {job_id}")
                    except Exception as cancel_err:
                        print(f"[LULU API] Cancel/recreate failed: {cancel_err}, keeping original job {job_id}")
                
                job_data['_actual_shipping_level'] = level
                return job_data
            else:
                resp_text = response.text
                if "shipping" in resp_text.lower() and level != levels_to_try[-1]:
                    print(f"[LULU API] Shipping '{level}' not available for this destination, trying next...")
                    continue
                print(f"[LULU API] Print job creation failed: {response.status_code}")
                print(f"[LULU API] Response: {resp_text}")
                return None
                
        except Exception as e:
            print(f"[LULU API] Print job creation error with {level}: {e}")
            continue
    
    print(f"[LULU API] All shipping levels exhausted, print job creation failed")
    return None


SHIPPING_OPTIONS = {
    "MAIL": {"name_es": "Correo Estándar", "name_en": "Standard Mail", "days": "14-21"},
    "PRIORITY_MAIL": {"name_es": "Correo Prioritario", "name_en": "Priority Mail", "days": "7-14"},
    "GROUND": {"name_es": "Terrestre", "name_en": "Ground", "days": "5-10"},
    "EXPEDITED": {"name_es": "Rápido", "name_en": "Expedited", "days": "3-7"},
    "EXPRESS": {"name_es": "Express", "name_en": "Express", "days": "1-3"}
}

SHIPPING_FALLBACK_ORDER = ["EXPEDITED", "PRIORITY_MAIL", "MAIL"]

STATUS_TRANSLATIONS = {
    "CREATED": {"es": "Pedido creado", "en": "Order created"},
    "UNPAID": {"es": "Pendiente de pago", "en": "Awaiting payment"},
    "PAYMENT_IN_PROGRESS": {"es": "Procesando pago", "en": "Processing payment"},
    "PRODUCTION_DELAYED": {"es": "En espera de producción", "en": "Production delayed"},
    "PRODUCTION_READY": {"es": "Listo para producción", "en": "Ready for production"},
    "IN_PRODUCTION": {"es": "En impresión", "en": "In production"},
    "SHIPPED": {"es": "Enviado", "en": "Shipped"},
    "REJECTED": {"es": "Rechazado", "en": "Rejected"},
    "CANCELED": {"es": "Cancelado", "en": "Canceled"},
    "SHIPPED_ERROR": {"es": "Error de envío parcial", "en": "Shipping error"},
    "PARTIALLY_SHIPPED": {"es": "Parcialmente enviado", "en": "Partially shipped"}
}


def get_print_job_status(print_job_id: str, access_token: Optional[str] = None) -> Optional[dict]:
    """
    Get the status and tracking info for a print job.
    
    Returns:
        {
            "status": "SHIPPED",
            "status_text": {"es": "Enviado", "en": "Shipped"},
            "tracking_id": "...",
            "tracking_urls": ["..."],
            "carrier_name": "...",
            "created_at": "...",
            "updated_at": "..."
        }
    """
    if not access_token:
        access_token = get_access_token()
        if not access_token:
            return None
    
    url = f"{LULU_API_BASE}/print-jobs/{print_job_id}/"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            job_data = response.json()
            status_info = job_data.get("status", {})
            status_name = status_info.get("name", "UNKNOWN")
            
            result = {
                "status": status_name,
                "status_text": STATUS_TRANSLATIONS.get(status_name, {"es": status_name, "en": status_name}),
                "created_at": job_data.get("date_created"),
                "updated_at": status_info.get("changed"),
                "tracking_id": None,
                "tracking_urls": [],
                "carrier_name": None
            }
            
            line_item_statuses = status_info.get("line_item_statuses", [])
            if line_item_statuses:
                messages = line_item_statuses[0].get("messages", {})
                result["tracking_id"] = messages.get("tracking_id")
                result["tracking_urls"] = messages.get("tracking_urls", [])
                result["carrier_name"] = messages.get("carrier_name")
            
            print(f"[LULU API] Print job {print_job_id} status: {status_name}")
            return result
        else:
            print(f"[LULU API] Failed to get job status: {response.status_code}")
            print(f"[LULU API] Response: {response.text[:500]}")
            return None
            
    except Exception as e:
        print(f"[LULU API] Error getting job status: {e}")
        return None


def get_print_job_cost(
    pod_package_id: str = "0827X1169FCPRECW080CW444GXX",
    page_count: int = 24,
    quantity: int = 1,
    shipping_address: Optional[dict] = None,
    shipping_option: str = "MAIL",
    access_token: Optional[str] = None
) -> Optional[dict]:
    """
    Get cost estimate for a print job.
    
    Pod Package ID breakdown for A4 Hardcover:
        0850X1100 = 8.5" x 11" (A4 portrait)
        FC = Full Color
        PRE = Premium
        CW = Coated White paper
        080 = 80# paper weight
        CW = Coated White (cover)
        444 = 4-color front/back cover, 4-color interior
        G = Glossy laminate
        XX = Case wrap hardcover
    
    Returns cost data or None if request fails.
    """
    if not access_token:
        access_token = get_access_token()
        if not access_token:
            return None
    
    url = f"{LULU_API_BASE}/print-job-cost-calculations/"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "line_items": [{
            "pod_package_id": pod_package_id,
            "page_count": page_count,
            "quantity": quantity
        }],
        "shipping_address": shipping_address or {
            "country_code": "ES"
        },
        "shipping_option": shipping_option
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code in [200, 201]:
            cost_data = response.json()
            print(f"[LULU API] Cost calculation successful for {shipping_option}")
            return cost_data
        else:
            print(f"[LULU API] Cost calculation failed: {response.status_code}")
            print(f"[LULU API] Response: {response.text[:500]}")
            return None
            
    except Exception as e:
        print(f"[LULU API] Cost calculation error: {e}")
        return None


def get_all_shipping_costs(
    country_code: str,
    page_count: int = 24,
    pod_package_id: str = "0827X1169FCPRECW080CW444GXX"
) -> dict:
    """
    Get shipping costs for all available methods for a given country.
    Returns dict with shipping options and their costs.
    """
    access_token = get_access_token()
    if not access_token:
        return {"error": "Could not authenticate with Lulu API"}
    
    # Lulu requires full address for cost calculation - use default addresses per country
    default_addresses = {
        "US": {"city": "New York", "state_code": "NY", "postcode": "10001", "street1": "123 Main St", "phone_number": "+1-555-000-0000"},
        "ES": {"city": "Madrid", "state_code": "MD", "postcode": "28001", "street1": "Calle Mayor 1", "phone_number": "+34-555-000-000"},
        "MX": {"city": "Ciudad de México", "state_code": "CMX", "postcode": "06600", "street1": "Av. Reforma 1", "phone_number": "+52-555-000-0000", "recipient_tax_id": "XAXX010101000"},
        "CO": {"city": "Bogotá", "state_code": "DC", "postcode": "110111", "street1": "Calle 1", "phone_number": "+57-555-000-0000"},
        "AR": {"city": "Buenos Aires", "state_code": "C", "postcode": "C1000", "street1": "Av. 9 de Julio 1", "phone_number": "+54-555-000-0000", "recipient_tax_id": "20000000001"},
        "CL": {"city": "Santiago", "state_code": "RM", "postcode": "8320000", "street1": "Av. Libertador 1", "phone_number": "+56-555-000-0000", "recipient_tax_id": "11111111-1"},
        "PE": {"city": "Lima", "state_code": "LIM", "postcode": "15001", "street1": "Av. Arequipa 1", "phone_number": "+51-555-000-0000", "recipient_tax_id": "10000000001"},
        "GB": {"city": "London", "postcode": "SW1A 1AA", "street1": "10 Downing St", "phone_number": "+44-555-000-0000"},
        "CA": {"city": "Toronto", "state_code": "ON", "postcode": "M5H 2N2", "street1": "100 Queen St", "phone_number": "+1-555-000-0000"},
        "DE": {"city": "Berlin", "postcode": "10115", "street1": "Unter den Linden 1", "phone_number": "+49-555-000-0000"},
        "FR": {"city": "Paris", "postcode": "75001", "street1": "1 Rue de Rivoli", "phone_number": "+33-555-000-000"},
        "BR": {"city": "São Paulo", "state_code": "SP", "postcode": "01000-000", "street1": "Av. Paulista 1", "phone_number": "+55-555-000-0000", "recipient_tax_id": "00000000000"},
    }
    
    addr_data = default_addresses.get(country_code, {"city": "New York", "state_code": "NY", "postcode": "10001", "street1": "123 Main St", "phone_number": "+1-555-000-0000"})
    shipping_address = {"country_code": country_code, **addr_data}
    
    results = {}
    base_cost = None
    
    for option_code, option_info in SHIPPING_OPTIONS.items():
        cost_data = get_print_job_cost(
            shipping_address=shipping_address,
            shipping_option=option_code,
            page_count=page_count,
            access_token=access_token,
            pod_package_id=pod_package_id
        )
        
        if cost_data:
            total = float(cost_data.get("total_cost_incl_tax", 0))
            shipping = float(cost_data.get("shipping_cost", {}).get("total_cost_incl_tax", 0))
            
            if option_code == "MAIL":
                base_cost = total
            
            results[option_code] = {
                "name_es": option_info["name_es"],
                "name_en": option_info["name_en"],
                "days": option_info["days"],
                "total_cost": total,
                "shipping_cost": shipping,
                "extra_cost": round(total - base_cost, 2) if base_cost else 0
            }
    
    return results


def verify_url_accessible(url: str, max_retries: int = 3) -> bool:
    """Verify a URL is publicly accessible before sending to Lulu."""
    import time
    for attempt in range(max_retries):
        try:
            resp = requests.head(url, timeout=10, allow_redirects=True)
            if resp.status_code == 200:
                print(f"[LULU API] URL verified accessible: {url}")
                return True
            print(f"[LULU API] URL check attempt {attempt+1}: status {resp.status_code}")
        except Exception as e:
            print(f"[LULU API] URL check attempt {attempt+1} failed: {e}")
        if attempt < max_retries - 1:
            time.sleep(2)
    print(f"[LULU API] WARNING: URL may not be accessible: {url}")
    return False


def submit_print_order(
    order_folder: str,
    title: str,
    shipping_address: dict,
    shipping_level: str = "MAIL",
    pod_package_id: str = "0827X1169FCPRECW080CW444GXX"
) -> Tuple[bool, str, Optional[str]]:
    """
    Complete workflow to submit a print order to Lulu using public URLs.
    
    Args:
        order_folder: Path to folder containing interior.pdf and cover.pdf
        title: Book title
        shipping_address: Shipping address with keys:
            - name, street1, city, state_code, postal_code, country_code, email, phone_number
        shipping_level: Shipping method (MAIL, PRIORITY_MAIL, GROUND, EXPEDITED, EXPRESS)
    
    Returns:
        Tuple of (success, message, lulu_job_id)
    """
    interior_path = os.path.join(order_folder, "interior.pdf")
    cover_path = os.path.join(order_folder, "cover.pdf")
    
    if not os.path.exists(interior_path):
        return False, "Interior PDF not found", None
    
    if not os.path.exists(cover_path):
        return False, "Cover PDF not found", None
    
    interior_size = os.path.getsize(interior_path)
    cover_size = os.path.getsize(cover_path)
    print(f"[LULU API] PDF sizes: interior={interior_size/1024:.1f}KB, cover={cover_size/1024:.1f}KB")
    
    if interior_size < 1000 or cover_size < 1000:
        return False, f"PDF files too small (interior={interior_size}B, cover={cover_size}B) - likely corrupted", None
    
    access_token = get_access_token()
    if not access_token:
        return False, "Failed to authenticate with Lulu API", None
    
    interior_url = get_public_file_url(order_folder, "interior.pdf")
    cover_url = get_public_file_url(order_folder, "cover.pdf")
    
    if not interior_url or not cover_url:
        return False, "Failed to generate public URLs for PDFs", None
    
    verify_url_accessible(interior_url)
    verify_url_accessible(cover_url)
    
    print(f"[LULU API] Creating print job with public URLs...")
    job_data = create_print_job_with_urls(
        interior_url=interior_url,
        cover_url=cover_url,
        title=title,
        quantity=1,
        shipping_address=shipping_address,
        shipping_level=shipping_level,
        access_token=access_token,
        pod_package_id=pod_package_id
    )
    
    if not job_data:
        return False, "Failed to create print job", None
    
    job_id = job_data.get("id")
    status = job_data.get("status", {}).get("name", "CREATED")
    actual_shipping = job_data.get('_actual_shipping_level', shipping_level)
    
    print(f"[LULU API] Print job submitted successfully!")
    print(f"[LULU API] Job ID: {job_id}")
    print(f"[LULU API] Status: {status}")
    if actual_shipping != shipping_level:
        print(f"[LULU API] Shipping fallback: {shipping_level} -> {actual_shipping}")
    
    return True, f"Print job created: {job_id}", job_id


def test_lulu_connection() -> dict:
    """
    Test connection to Lulu API.
    Returns status information.
    """
    client_key, client_secret = get_lulu_credentials()
    
    result = {
        "timestamp": datetime.now().isoformat(),
        "credentials_configured": bool(client_key and client_secret),
        "authentication": False,
        "message": ""
    }
    
    if not result["credentials_configured"]:
        result["message"] = "Lulu credentials not configured"
        return result
    
    access_token = get_access_token()
    
    if access_token:
        result["authentication"] = True
        result["message"] = "Connection successful"
    else:
        result["message"] = "Authentication failed"
    
    return result


EXCLUDED_COUNTRIES = {
    'BY': 'Belarus',
    'CU': 'Cuba', 
    'IR': 'Iran',
    'MM': 'Myanmar',
    'KP': 'North Korea',
    'RU': 'Russia',
    'SS': 'South Sudan',
    'SD': 'Sudan',
    'SY': 'Syria',
    'TM': 'Turkmenistan',
    'UA': 'Ukraine',
    'VE': 'Venezuela',
    'YE': 'Yemen'
}

def validate_tax_id(country_code: str, tax_id: str) -> str:
    """
    Validate tax ID format for countries that require it.
    Returns error message string if invalid, or empty string if valid.
    """
    import re
    if not tax_id:
        return ""
    
    clean = re.sub(r'[\s\-\.\/]', '', tax_id)
    
    if country_code == 'AR':
        if len(clean) != 11 or not clean.isdigit():
            return "CUIT/CUIL must have exactly 11 digits"
        prefix = clean[:2]
        if prefix not in ('20', '23', '24', '25', '26', '27', '30', '33', '34'):
            return "Invalid CUIT/CUIL: must start with 20, 23-27, 30, 33 or 34"
        multipliers = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
        s = sum(int(clean[i]) * multipliers[i] for i in range(10))
        check = 11 - (s % 11)
        expected = 0 if check == 11 else (9 if check == 10 else check)
        if int(clean[10]) != expected:
            return "Invalid CUIT/CUIL: check digit is incorrect"
    elif country_code == 'MX':
        clean_upper = re.sub(r'[\s\-]', '', tax_id).upper()
        if len(clean_upper) not in (12, 13):
            return "RFC must be 12 or 13 characters"
    elif country_code == 'BR':
        if len(clean) not in (11, 14) or not clean.isdigit():
            return "CPF must have 11 digits or CNPJ 14 digits"
    elif country_code == 'CL':
        clean_upper = re.sub(r'[\s\.\-]', '', tax_id).upper()
        if len(clean_upper) < 8 or len(clean_upper) > 9:
            return "RUT must be 8-9 characters"
    elif country_code == 'PE':
        if len(clean) not in (8, 11) or not clean.isdigit():
            return "DNI must have 8 digits or RUC 11 digits"
    
    return ""


def validate_shipping_address(shipping_address: dict) -> dict:
    """
    Validate a shipping address using Lulu's cost calculation endpoint.
    Returns validation result with suggested address if available.
    
    Returns:
        {
            "valid": bool,
            "original_address": dict,
            "suggested_address": dict or None,
            "message": str,
            "warnings": list,
            "country_not_supported": bool
        }
    """
    country_code = shipping_address.get('country_code', '').upper()
    
    tax_id = shipping_address.get('recipient_tax_id', '')
    tax_id_countries = {'AR', 'MX', 'BR', 'CL', 'PE'}
    if country_code in tax_id_countries:
        if not tax_id:
            country_names = {'AR': 'CUIT/CUIL', 'MX': 'RFC', 'BR': 'CPF/CNPJ', 'CL': 'RUT', 'PE': 'DNI/RUC'}
            return {
                "valid": False,
                "original_address": shipping_address,
                "suggested_address": None,
                "message": f"{country_names[country_code]} is required for shipping to this country",
                "warnings": [],
                "tax_id_error": True
            }
        tax_error = validate_tax_id(country_code, tax_id)
        if tax_error:
            return {
                "valid": False,
                "original_address": shipping_address,
                "suggested_address": None,
                "message": tax_error,
                "warnings": [],
                "tax_id_error": True
            }
    
    if country_code in EXCLUDED_COUNTRIES:
        country_name = EXCLUDED_COUNTRIES[country_code]
        return {
            "valid": False,
            "original_address": shipping_address,
            "suggested_address": None,
            "message": f"Lo sentimos, no enviamos a {country_name}. / Sorry, we don't ship to {country_name}.",
            "warnings": [],
            "country_not_supported": True
        }
    
    access_token = get_access_token()
    if not access_token:
        return {
            "valid": False,
            "original_address": shipping_address,
            "suggested_address": None,
            "message": "Could not authenticate with Lulu API",
            "warnings": []
        }
    
    url = f"{LULU_API_BASE}/print-job-cost-calculations/"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Normalize address fields
    country = shipping_address.get("country_code", "US")
    normalized_address = {
        "name": shipping_address.get("name", ""),
        "street1": shipping_address.get("street1", ""),
        "street2": shipping_address.get("street2", ""),
        "city": shipping_address.get("city", ""),
        "state_code": normalize_state_code(shipping_address.get("state_code", ""), country),
        "postcode": shipping_address.get("postcode") or shipping_address.get("postal_code", ""),
        "country_code": country,
        "phone_number": shipping_address.get("phone_number", ""),
        "email": shipping_address.get("email", "")
    }
    tax_id = shipping_address.get("recipient_tax_id", "")
    if tax_id:
        normalized_address["recipient_tax_id"] = tax_id
    
    payload = {
        "line_items": [{
            "pod_package_id": "0827X1169FCPRECW080CW444GXX",
            "page_count": 24,
            "quantity": 1
        }],
        "shipping_address": normalized_address,
        "shipping_option": "MAIL"
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        data = response.json()
        
        print(f"[LULU API] Full validation response status: {response.status_code}")
        
        shipping_resp = data.get("shipping_address", {})
        addr_warnings = shipping_resp.get("warnings", []) if isinstance(shipping_resp, dict) else []
        addr_suggested = shipping_resp.get("suggested_address") if isinstance(shipping_resp, dict) else None
        
        top_warnings = data.get("warnings", [])
        all_warnings = addr_warnings + top_warnings
        print(f"[LULU API] Address warnings: {json.dumps(addr_warnings, indent=2) if addr_warnings else 'none'}")
        print(f"[LULU API] Suggested address: {json.dumps(addr_suggested, indent=2) if addr_suggested else 'none'}")
        
        address_warnings = [w for w in all_warnings if "address" in str(w).lower() or w.get("type") in ("ADDRESS_VALIDATION", "validation_warning") or w.get("suggested_address")]
        
        result = {
            "valid": True,
            "original_address": normalized_address,
            "suggested_address": None,
            "message": "Address is valid",
            "warnings": address_warnings
        }
        
        if addr_suggested:
            corrected_address = {
                "name": normalized_address.get("name", ""),
                "street1": addr_suggested.get("street1", normalized_address.get("street1", "")),
                "street2": (addr_suggested.get("street2") or "") if "street2" in addr_suggested else normalized_address.get("street2", ""),
                "city": addr_suggested.get("city", normalized_address.get("city", "")),
                "state_code": addr_suggested.get("state_code", normalized_address.get("state_code", "")),
                "postcode": addr_suggested.get("postcode", normalized_address.get("postcode", "")),
                "country_code": addr_suggested.get("country_code", normalized_address.get("country_code", "")),
                "phone_number": normalized_address.get("phone_number", ""),
                "email": normalized_address.get("email", "")
            }
            
            orig_street = normalized_address.get("street1", "").upper().strip()
            sugg_street = corrected_address.get("street1", "").upper().strip()
            orig_street2 = normalized_address.get("street2", "").upper().strip()
            sugg_street2 = corrected_address.get("street2", "").upper().strip()
            orig_city = normalized_address.get("city", "").upper().strip()
            sugg_city = corrected_address.get("city", "").upper().strip()
            orig_state = normalized_address.get("state_code", "").upper().strip()
            sugg_state = corrected_address.get("state_code", "").upper().strip()
            orig_country = normalized_address.get("country_code", "").upper().strip()
            sugg_country = corrected_address.get("country_code", "").upper().strip()
            orig_zip = normalized_address.get("postcode", "").strip().split("-")[0]
            sugg_zip = corrected_address.get("postcode", "").strip().split("-")[0]
            
            state_matters = orig_country in ("US", "CA", "AU")
            is_trivial = (orig_street == sugg_street and 
                          orig_street2 == sugg_street2 and
                          orig_city == sugg_city and 
                          (orig_state == sugg_state or not state_matters) and 
                          orig_country == sugg_country and
                          orig_zip == sugg_zip)
            
            if is_trivial:
                print(f"[LULU API] Auto-accepting trivial correction (ZIP+4/capitalization):")
                print(f"[LULU API]   Original ZIP: {normalized_address.get('postcode', '')} -> Corrected: {corrected_address.get('postcode', '')}")
                result["valid"] = True
                result["suggested_address"] = corrected_address
                result["original_address"] = corrected_address
                result["message"] = "Address auto-corrected"
                result["auto_corrected"] = True
            else:
                print(f"[LULU API] Significant address change detected - requires user confirmation:")
                print(f"[LULU API]   Original: {normalized_address.get('street1', '')}, {normalized_address.get('city', '')}")
                print(f"[LULU API]   Suggested: {corrected_address.get('street1', '')}, {corrected_address.get('city', '')}")
                result["valid"] = False
                result["suggested_address"] = corrected_address
                result["message"] = addr_warnings[0].get("message", "Address correction suggested") if addr_warnings else "Address correction suggested"
        
        for warning in address_warnings:
            if warning.get("code") == "INCOMPLETE_ADDRESS":
                result["valid"] = False
                result["message"] = "Incomplete address - please check all fields"
                break
        
        print(f"[LULU API] Address validation: valid={result['valid']}, message={result['message']}")
        return result
        
    except Exception as e:
        print(f"[LULU API] Address validation error: {e}")
        return {
            "valid": False,
            "original_address": shipping_address,
            "suggested_address": None,
            "message": f"Validation error: {str(e)}",
            "warnings": []
        }
