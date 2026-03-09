"""
Lulu Orders Storage Service.
Manages temporary storage of files sent to Lulu for printing.
Files are automatically cleaned up after 48 hours.
"""

import os
import json
import shutil
from datetime import datetime, timedelta
from typing import Optional


LULU_ORDERS_DIR = "lulu_orders"
RETENTION_HOURS = 48


def ensure_storage_dir():
    """Ensure the lulu_orders directory exists."""
    os.makedirs(LULU_ORDERS_DIR, exist_ok=True)


def create_order_folder(order_id: str, child_name: str, email: str) -> str:
    """
    Create a folder for a new Lulu order.
    Returns the path to the order folder.
    
    Structure: lulu_orders/{order_id}_{timestamp}/
    Contains:
    - interior.pdf (24 pages print interior)
    - cover.pdf (cover spread: back + spine + front)
    - metadata.json (order info)
    """
    ensure_storage_dir()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(c for c in child_name if c.isalnum() or c in " -_")[:20].strip()
    folder_name = f"{safe_name}_{timestamp}"
    folder_path = os.path.join(LULU_ORDERS_DIR, folder_name)
    
    os.makedirs(folder_path, exist_ok=True)
    
    metadata = {
        "order_id": order_id,
        "child_name": child_name,
        "email": email,
        "book_type": "Dragon Garden Illustrated",
        "created_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(hours=RETENTION_HOURS)).isoformat(),
        "status": "pending",
        "lulu_job_id": None,
        "files": {
            "interior": None,
            "cover": None
        }
    }
    
    metadata_path = os.path.join(folder_path, "metadata.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    print(f"[LULU STORAGE] Created order folder: {folder_path}")
    return folder_path


def save_interior_pdf(order_folder: str, pdf_path: str) -> str:
    """
    Copy interior PDF to the order folder.
    Returns the path to the saved file.
    """
    dest_path = os.path.join(order_folder, "interior.pdf")
    shutil.copy2(pdf_path, dest_path)
    
    _update_metadata(order_folder, {"files": {"interior": "interior.pdf"}})
    print(f"[LULU STORAGE] Saved interior PDF: {dest_path}")
    return dest_path


def save_cover_pdf(order_folder: str, pdf_path: str) -> str:
    """
    Copy cover PDF to the order folder.
    Returns the path to the saved file.
    """
    dest_path = os.path.join(order_folder, "cover.pdf")
    shutil.copy2(pdf_path, dest_path)
    
    _update_metadata(order_folder, {"files": {"cover": "cover.pdf"}})
    print(f"[LULU STORAGE] Saved cover PDF: {dest_path}")
    return dest_path


def update_order_status(order_folder: str, status: str, lulu_job_id: Optional[str] = None):
    """Update the order status in metadata."""
    updates = {"status": status, "updated_at": datetime.now().isoformat()}
    if lulu_job_id:
        updates["lulu_job_id"] = lulu_job_id
    _update_metadata(order_folder, updates)
    print(f"[LULU STORAGE] Updated status: {status}")


def _update_metadata(order_folder: str, updates: dict):
    """Update metadata file with new values."""
    metadata_path = os.path.join(order_folder, "metadata.json")
    
    if os.path.exists(metadata_path):
        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)
    else:
        metadata = {}
    
    for key, value in updates.items():
        if isinstance(value, dict) and key in metadata and isinstance(metadata[key], dict):
            metadata[key].update(value)
        else:
            metadata[key] = value
    
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)


def get_order_info(order_folder: str) -> Optional[dict]:
    """Get order metadata."""
    metadata_path = os.path.join(order_folder, "metadata.json")
    if os.path.exists(metadata_path):
        with open(metadata_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def list_all_orders() -> list:
    """List all orders in storage with their metadata."""
    ensure_storage_dir()
    orders = []
    
    for folder_name in os.listdir(LULU_ORDERS_DIR):
        folder_path = os.path.join(LULU_ORDERS_DIR, folder_name)
        if os.path.isdir(folder_path):
            metadata = get_order_info(folder_path)
            if metadata:
                metadata["folder_path"] = folder_path
                metadata["folder_name"] = folder_name
                orders.append(metadata)
    
    orders.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return orders


def cleanup_expired_orders() -> int:
    """
    Delete orders older than RETENTION_HOURS.
    Returns the number of deleted orders.
    """
    ensure_storage_dir()
    deleted_count = 0
    cutoff_time = datetime.now() - timedelta(hours=RETENTION_HOURS)
    
    for folder_name in os.listdir(LULU_ORDERS_DIR):
        folder_path = os.path.join(LULU_ORDERS_DIR, folder_name)
        if not os.path.isdir(folder_path):
            continue
        
        metadata = get_order_info(folder_path)
        if metadata:
            try:
                created_at = datetime.fromisoformat(metadata.get("created_at", ""))
                if created_at < cutoff_time:
                    shutil.rmtree(folder_path)
                    deleted_count += 1
                    print(f"[LULU STORAGE] Deleted expired order: {folder_name}")
            except (ValueError, TypeError):
                pass
    
    if deleted_count > 0:
        print(f"[LULU STORAGE] Cleanup complete: {deleted_count} orders deleted")
    
    return deleted_count


def get_storage_summary() -> dict:
    """Get summary of storage status."""
    orders = list_all_orders()
    
    total_size = 0
    for order in orders:
        folder_path = order.get("folder_path", "")
        if os.path.exists(folder_path):
            for file in os.listdir(folder_path):
                file_path = os.path.join(folder_path, file)
                if os.path.isfile(file_path):
                    total_size += os.path.getsize(file_path)
    
    return {
        "total_orders": len(orders),
        "pending": sum(1 for o in orders if o.get("status") == "pending"),
        "pending_review": sum(1 for o in orders if o.get("status") == "pending_review"),
        "sent": sum(1 for o in orders if o.get("status") == "sent_to_lulu"),
        "completed": sum(1 for o in orders if o.get("status") == "completed"),
        "failed": sum(1 for o in orders if o.get("status") == "failed"),
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "retention_hours": RETENTION_HOURS
    }


def save_cover_preview(order_folder: str, cover_image) -> str:
    """
    Save cover spread image for preview.
    cover_image should be a PIL Image object.
    """
    preview_path = os.path.join(order_folder, "cover_preview.png")
    
    preview = cover_image.copy()
    preview.thumbnail((1200, 900))
    preview.save(preview_path, "PNG", quality=85)
    
    _update_metadata(order_folder, {"files": {"cover_preview": "cover_preview.png"}})
    print(f"[LULU STORAGE] Saved cover preview: {preview_path}")
    return preview_path


def get_order_by_folder(folder_name: str) -> Optional[dict]:
    """Get order by folder name."""
    folder_path = os.path.join(LULU_ORDERS_DIR, folder_name)
    if os.path.isdir(folder_path):
        metadata = get_order_info(folder_path)
        if metadata:
            metadata["folder_path"] = folder_path
            metadata["folder_name"] = folder_name
            return metadata
    return None
