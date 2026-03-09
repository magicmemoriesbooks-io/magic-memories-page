"""
Task Queue System for VPS Autonomous Operation
Uses threading + database for background job processing.
No external dependencies (Redis/RabbitMQ) required.
"""

import os
import threading
import queue
import time
import traceback
import logging
from datetime import datetime
from enum import Enum
from typing import Callable, Dict, Any, Optional
from functools import wraps

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

production_logger = logging.getLogger('production')
production_logger.setLevel(logging.DEBUG)

log_file_handler = logging.FileHandler(
    os.path.join(LOG_DIR, 'production.log'),
    encoding='utf-8'
)
log_file_handler.setFormatter(logging.Formatter(
    '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
))
production_logger.addHandler(log_file_handler)

console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter(
    '%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
))
production_logger.addHandler(console_handler)


class TaskStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class TaskResult:
    def __init__(self, task_id: str):
        self.task_id = task_id
        self.status = TaskStatus.PENDING
        self.progress = 0
        self.total_steps = 0
        self.current_step = ""
        self.result = None
        self.error = None
        self.started_at = None
        self.completed_at = None
        self.retries = 0
        self.max_retries = 3
        self.failed_items = []
        self.completed_items = []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'task_id': self.task_id,
            'status': self.status.value,
            'progress': self.progress,
            'total_steps': self.total_steps,
            'current_step': self.current_step,
            'result': self.result,
            'error': self.error,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'retries': self.retries,
            'failed_items': self.failed_items,
            'completed_items': self.completed_items
        }


class TaskQueue:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._queue = queue.Queue()
        self._results: Dict[str, TaskResult] = {}
        self._workers: list = []
        self._running = True
        self._num_workers = int(os.environ.get('TASK_WORKERS', 3))
        
        for i in range(self._num_workers):
            worker = threading.Thread(target=self._worker_loop, daemon=True, name=f"TaskWorker-{i}")
            worker.start()
            self._workers.append(worker)
        
        production_logger.info(f"TaskQueue initialized with {self._num_workers} workers (optimized for 4 vCPUs)")
        self._initialized = True
    
    def _worker_loop(self):
        while self._running:
            try:
                task_id, func, args, kwargs = self._queue.get(timeout=1)
                self._execute_task(task_id, func, args, kwargs)
                self._queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                production_logger.error(f"Worker error: {e}")
    
    def _execute_task(self, task_id: str, func: Callable, args: tuple, kwargs: dict):
        result = self._results.get(task_id)
        if not result:
            return
        
        result.status = TaskStatus.PROCESSING
        result.started_at = datetime.utcnow()
        
        try:
            production_logger.info(f"[TASK {task_id}] Starting: {func.__name__}")
            
            kwargs['task_result'] = result
            
            output = func(*args, **kwargs)
            
            result.status = TaskStatus.COMPLETED
            result.result = output
            result.completed_at = datetime.utcnow()
            production_logger.info(f"[TASK {task_id}] Completed successfully")
            
        except Exception as e:
            error_msg = str(e)
            tb = traceback.format_exc()
            production_logger.error(f"[TASK {task_id}] Failed: {error_msg}\n{tb}")
            
            result.retries += 1
            if result.retries < result.max_retries:
                result.status = TaskStatus.RETRYING
                production_logger.info(f"[TASK {task_id}] Retrying ({result.retries}/{result.max_retries})")
                self._queue.put((task_id, func, args, kwargs))
            else:
                result.status = TaskStatus.FAILED
                result.error = error_msg
                result.completed_at = datetime.utcnow()
    
    def enqueue(self, task_id: str, func: Callable, *args, **kwargs) -> TaskResult:
        result = TaskResult(task_id)
        self._results[task_id] = result
        self._queue.put((task_id, func, args, kwargs))
        production_logger.info(f"[QUEUE] Task {task_id} enqueued: {func.__name__}")
        return result
    
    def get_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        result = self._results.get(task_id)
        if result:
            return result.to_dict()
        return None
    
    def update_progress(self, task_id: str, progress: int, total: int, step: str = ""):
        result = self._results.get(task_id)
        if result:
            result.progress = progress
            result.total_steps = total
            result.current_step = step
            production_logger.debug(f"[TASK {task_id}] Progress: {progress}/{total} - {step}")
    
    def mark_item_completed(self, task_id: str, item_id: str):
        result = self._results.get(task_id)
        if result and item_id not in result.completed_items:
            result.completed_items.append(item_id)
    
    def mark_item_failed(self, task_id: str, item_id: str, error: str):
        result = self._results.get(task_id)
        if result:
            result.failed_items.append({'id': item_id, 'error': error})
    
    def cleanup_old_results(self, max_age_hours: int = 24):
        now = datetime.utcnow()
        to_delete = []
        for task_id, result in self._results.items():
            if result.completed_at:
                age = (now - result.completed_at).total_seconds() / 3600
                if age > max_age_hours:
                    to_delete.append(task_id)
        
        for task_id in to_delete:
            del self._results[task_id]
            production_logger.info(f"[CLEANUP] Removed old task result: {task_id}")


task_queue = TaskQueue()


def verify_image_integrity(image_path: str) -> bool:
    """
    Verify that an image file is valid and not corrupted.
    Returns True if valid, False otherwise.
    """
    from PIL import Image
    
    if not os.path.exists(image_path):
        production_logger.error(f"[INTEGRITY] File not found: {image_path}")
        return False
    
    file_size = os.path.getsize(image_path)
    if file_size < 1000:
        production_logger.error(f"[INTEGRITY] File too small ({file_size} bytes): {image_path}")
        return False
    
    try:
        with Image.open(image_path) as img:
            img.verify()
        
        with Image.open(image_path) as img:
            img.load()
            width, height = img.size
            if width < 100 or height < 100:
                production_logger.error(f"[INTEGRITY] Image too small ({width}x{height}): {image_path}")
                return False
        
        production_logger.debug(f"[INTEGRITY] Verified OK: {image_path}")
        return True
        
    except Exception as e:
        production_logger.error(f"[INTEGRITY] Corrupt image {image_path}: {e}")
        return False


def get_absolute_path(*paths) -> str:
    """
    Convert relative paths to absolute paths based on BASE_DIR.
    Works on both Replit and VPS Linux environments.
    """
    if len(paths) == 1 and os.path.isabs(paths[0]):
        return paths[0]
    
    return os.path.join(BASE_DIR, *paths)


def get_media_path(order_id: str, filename: str = "") -> str:
    """
    Get the media storage path for an order.
    Creates the directory if it doesn't exist.
    """
    media_base = os.environ.get('MEDIA_PATH', os.path.join(BASE_DIR, 'generated_stories'))
    order_path = os.path.join(media_base, str(order_id))
    os.makedirs(order_path, exist_ok=True)
    
    if filename:
        return os.path.join(order_path, filename)
    return order_path


def cleanup_temp_files(order_id: str, keep_pdf: bool = True):
    """
    Clean up temporary files after PDF generation.
    Keeps the final PDF but removes intermediate images.
    """
    order_path = get_media_path(order_id)
    
    if not os.path.exists(order_path):
        return
    
    deleted_count = 0
    kept_count = 0
    
    for filename in os.listdir(order_path):
        filepath = os.path.join(order_path, filename)
        
        if keep_pdf and filename.endswith('.pdf'):
            kept_count += 1
            continue
        
        if filename.startswith('temp_') or filename.startswith('watermark_'):
            try:
                os.remove(filepath)
                deleted_count += 1
            except Exception as e:
                production_logger.warning(f"[CLEANUP] Could not delete {filepath}: {e}")
    
    production_logger.info(f"[CLEANUP] Order {order_id}: deleted {deleted_count} temp files, kept {kept_count} files")


def log_api_error(api_name: str, error: Exception, context: Dict[str, Any] = None):
    """
    Log API errors with full context for debugging.
    """
    error_logger = logging.getLogger('api_errors')
    if not error_logger.handlers:
        handler = logging.FileHandler(os.path.join(LOG_DIR, 'api_errors.log'), encoding='utf-8')
        handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
        error_logger.addHandler(handler)
    
    error_logger.error(f"[{api_name}] {type(error).__name__}: {error}")
    if context:
        error_logger.error(f"[{api_name}] Context: {context}")
    error_logger.error(f"[{api_name}] Traceback:\n{traceback.format_exc()}")


class ImageGenerationTracker:
    """
    Track image generation progress for a story.
    Ensures all images are generated before proceeding to PDF.
    """
    
    def __init__(self, order_id: str, total_images: int = 20):
        self.order_id = order_id
        self.total_images = total_images
        self.completed_images = {}
        self.failed_images = {}
        self.upscaled_images = {}
        self._lock = threading.Lock()
    
    def mark_generated(self, image_index: int, path: str):
        with self._lock:
            if verify_image_integrity(path):
                self.completed_images[image_index] = path
                production_logger.info(f"[TRACKER {self.order_id}] Image {image_index}/{self.total_images} generated: {path}")
            else:
                self.failed_images[image_index] = "Integrity check failed"
    
    def mark_failed(self, image_index: int, error: str):
        with self._lock:
            self.failed_images[image_index] = error
            production_logger.error(f"[TRACKER {self.order_id}] Image {image_index} failed: {error}")
    
    def mark_upscaled(self, image_index: int, path: str):
        with self._lock:
            self.upscaled_images[image_index] = path
            production_logger.info(f"[TRACKER {self.order_id}] Image {image_index} upscaled to 300 DPI")
    
    def get_pending_images(self) -> list:
        with self._lock:
            completed = set(self.completed_images.keys())
            failed = set(self.failed_images.keys())
            all_indices = set(range(1, self.total_images + 1))
            return list(all_indices - completed - failed)
    
    def get_failed_for_retry(self) -> Dict[int, str]:
        with self._lock:
            return dict(self.failed_images)
    
    def is_generation_complete(self) -> bool:
        with self._lock:
            return len(self.completed_images) == self.total_images
    
    def is_upscale_complete(self) -> bool:
        with self._lock:
            return len(self.upscaled_images) == self.total_images
    
    def can_generate_pdf(self) -> bool:
        return self.is_generation_complete() and self.is_upscale_complete()
    
    def get_progress(self) -> Dict[str, Any]:
        with self._lock:
            completed = set(self.completed_images.keys())
            failed = set(self.failed_images.keys())
            all_indices = set(range(1, self.total_images + 1))
            pending_count = len(all_indices - completed - failed)
            
            gen_complete = len(self.completed_images) == self.total_images
            upscale_complete = len(self.upscaled_images) == self.total_images
            
            return {
                'total': self.total_images,
                'generated': len(self.completed_images),
                'upscaled': len(self.upscaled_images),
                'failed': len(self.failed_images),
                'pending': pending_count,
                'ready_for_pdf': gen_complete and upscale_complete
            }


image_trackers: Dict[str, ImageGenerationTracker] = {}


def get_or_create_tracker(order_id: str, total_images: int = 20) -> ImageGenerationTracker:
    if order_id not in image_trackers:
        image_trackers[order_id] = ImageGenerationTracker(order_id, total_images)
    return image_trackers[order_id]


def retry_failed_images(order_id: str, generate_func: Callable, *args, **kwargs) -> int:
    """
    Retry only the failed images for an order.
    Returns number of successfully retried images.
    """
    tracker = image_trackers.get(order_id)
    if not tracker:
        production_logger.error(f"[RETRY] No tracker found for order {order_id}")
        return 0
    
    failed = tracker.get_failed_for_retry()
    if not failed:
        production_logger.info(f"[RETRY] No failed images to retry for order {order_id}")
        return 0
    
    production_logger.info(f"[RETRY] Retrying {len(failed)} failed images for order {order_id}")
    
    success_count = 0
    for image_index, error in failed.items():
        try:
            result = generate_func(image_index, *args, **kwargs)
            if result:
                tracker.completed_images[image_index] = result
                del tracker.failed_images[image_index]
                success_count += 1
                production_logger.info(f"[RETRY] Image {image_index} succeeded on retry")
        except Exception as e:
            production_logger.error(f"[RETRY] Image {image_index} failed again: {e}")
    
    return success_count
