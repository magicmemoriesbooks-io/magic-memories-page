import os
import re
import uuid
import json
import atexit
import threading
import time
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory, send_file, abort, flash, make_response
import logging
from werkzeug.utils import secure_filename
from config import Config
from models import db, Order, StoryTemplate, RealStoryOrder, RealStoryCharacter, RealStoryPet, NewsletterSubscriber, PreviewLead, PrintOrderRequest, StoryBackup, Coupon, CouponLead, CouponUsage, PhotoUploadLog, CommunityStory, CommunityDownload, CommunitySubscriber, CommunityStoryPage
from translations import TRANSLATIONS, STORY_TEMPLATES, get_translation
from apscheduler.schedulers.background import BackgroundScheduler
from services.task_queue import task_queue, production_logger, get_or_create_tracker

app = Flask(__name__)

from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

preview_rate_limits = {}
email_rate_limits = {}
STORY_GEN_MAX    = 9999   # max generations per email+story = 1 initial + 3 regens; the 4th regen attempt (5th total) is blocked
STORY_GEN_WINDOW_HOURS = 3  # rolling window for character-preview regenerations (excludes free stories)
EMAIL_STORY_MAX  = 9999   # max different stories per email/24h
IP_ABUSE_MAX     = 9999  # anti-abuse threshold per IP/24h
# Legacy aliases kept so existing references don't break
PREVIEW_IP_MAX   = STORY_GEN_MAX
PREVIEW_EMAIL_MAX = EMAIL_STORY_MAX
PREVIEW_EMAIL_WINDOW = 24 * 60 * 60
_generation_progress = {}

import threading as _threading
_active_gen_lock = _threading.Lock()
_active_generations = {}  # gen_key → {'token': str, 'started': float}

def _save_gen_state(gen_token, status, image_url=None, kontext_portrait=None, error=None):
    """Persist preview generation state to disk for recovery on page reload (🔴 production fix)."""
    try:
        os.makedirs('data/preview_gen', exist_ok=True)
        from datetime import datetime as _dt
        with open(f'data/preview_gen/{gen_token}.json', 'w') as _gf:
            json.dump({
                'gen_token': gen_token,
                'status': status,
                'image_url': image_url,
                'kontext_portrait': kontext_portrait,
                'error': error,
                'updated_at': _dt.utcnow().isoformat()
            }, _gf)
    except Exception:
        pass

def _write_progress(preview_id, done, total):
    """Write generation progress to disk so all Gunicorn workers can read it."""
    try:
        path = f'story_previews/{preview_id}_progress.json'
        with open(path, 'w') as _pf:
            json.dump({'generated': done, 'total': total}, _pf)
    except Exception:
        pass

def _read_progress(preview_id):
    """Read progress from disk (fallback when in-memory dict is in another worker)."""
    try:
        path = f'story_previews/{preview_id}_progress.json'
        if os.path.exists(path):
            with open(path, 'r') as _pf:
                return json.load(_pf)
    except Exception:
        pass
    return {}

def _clear_progress(preview_id):
    """Remove progress file on completion or failure."""
    try:
        path = f'story_previews/{preview_id}_progress.json'
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass

def get_client_ip():
    forwarded = request.headers.get('X-Forwarded-For', '')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.remote_addr or '0.0.0.0'

def _is_testing_mode():
    try:
        import json as _j, os as _o, time as _t
        if _o.path.exists('data/testing_mode.json'):
            with open('data/testing_mode.json') as _f:
                _d = _j.load(_f)
            return _d.get('expires_at', 0) > _t.time()
    except Exception:
        pass
    return False

def check_generation_allowed(email, story_id, ip):
    """
    Returns (allowed: bool, reason: str)
    reason: 'ok' | 'story_limit' | 'new_story_limit' | 'ip_abuse'

    Rule 1 — per story:   max STORY_GEN_MAX   generations per email+story/24h
    Rule 2 — per email:   max EMAIL_STORY_MAX  different stories per email/24h
    Rule 3 — anti-abuse:  max IP_ABUSE_MAX     generations per IP/24h
    """
    if _is_testing_mode():
        return True, 'ok'

    cutoff = datetime.utcnow() - timedelta(hours=24)
    story_cutoff = datetime.utcnow() - timedelta(hours=STORY_GEN_WINDOW_HOURS)

    # Rule 3 — IP anti-abuse (no email required)
    if ip and ip != '0.0.0.0':
        try:
            ip_count = PreviewLead.query.filter(
                PreviewLead.ip_address == ip,
                PreviewLead.created_at >= cutoff
            ).count()
            if ip_count >= IP_ABUSE_MAX:
                return False, 'ip_abuse'
        except Exception:
            pass

    if not email:
        return True, 'ok'

    email_key = email.strip().lower()

    try:
        # Rule 1 — max generations for this specific story (rolling window, see STORY_GEN_WINDOW_HOURS)
        if story_id:
            story_count = PreviewLead.query.filter(
                db.func.lower(PreviewLead.email) == email_key,
                PreviewLead.story_id == story_id,
                PreviewLead.created_at >= story_cutoff
            ).count()
            if story_count >= STORY_GEN_MAX:
                return False, 'story_limit'

        # Rule 2 — max different stories today
        distinct_rows = db.session.query(PreviewLead.story_id).filter(
            db.func.lower(PreviewLead.email) == email_key,
            PreviewLead.created_at >= cutoff
        ).distinct().all()
        distinct_story_ids = {r[0] for r in distinct_rows if r[0]}

        if story_id not in distinct_story_ids:
            # Attempting a NEW story
            if len(distinct_story_ids) >= EMAIL_STORY_MAX:
                return False, 'new_story_limit'
    except Exception:
        pass

    return True, 'ok'

# Legacy wrappers kept for any remaining references
def check_preview_rate_limit(ip):
    allowed, _ = check_generation_allowed('', '', ip)
    return allowed, IP_ABUSE_MAX

def record_preview_usage(ip):
    pass

def check_email_rate_limit(email):
    return True, EMAIL_STORY_MAX

def record_email_usage(email):
    pass

def save_preview_lead(email, ip, story_id):
    """Save one row per generation attempt (no deduplication — each call counts)."""
    try:
        email_key = (email or '').strip().lower()
        lead = PreviewLead(email=email_key, ip_address=ip, story_id=story_id)
        db.session.add(lead)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"[LEAD] Error saving preview lead: {e}")

@app.after_request
def add_security_headers(response):
    if 'text/html' in response.content_type or 'image/' in response.content_type:
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    return response

import secrets as _secrets_mod

def _get_csrf_token():
    """Return a per-session CSRF token, generating one if needed."""
    if '_csrf_token' not in session:
        session['_csrf_token'] = _secrets_mod.token_hex(32)
    return session['_csrf_token']

def _verify_csrf():
    """Verify CSRF token on POST for admin routes. Returns True if valid."""
    token = request.form.get('_csrf_token') or request.headers.get('X-CSRFToken', '')
    return token and token == session.get('_csrf_token')

app.jinja_env.globals['csrf_token'] = _get_csrf_token

STORY_STORAGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'temp_stories')
os.makedirs(STORY_STORAGE_DIR, exist_ok=True)

def save_story_to_file(story_id: str, story_data: dict):
    """Save story data to a JSON file to avoid session size limits."""
    filepath = os.path.join(STORY_STORAGE_DIR, f"{story_id}.json")
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(story_data, f, ensure_ascii=False)

def load_story_from_file(story_id: str) -> dict:
    """Load story data from JSON file."""
    filepath = os.path.join(STORY_STORAGE_DIR, f"{story_id}.json")
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def get_or_create_story_id():
    """Get existing story ID from session or create new one."""
    if 'haz_tu_historia_story_id' not in session:
        session['haz_tu_historia_story_id'] = uuid.uuid4().hex
    return session['haz_tu_historia_story_id']
app.config.from_object(Config)

db.init_app(app)

def scheduled_photo_cleanup():
    """Automatic cleanup of uploaded user photos older than 72 hours (COPPA/GDPR compliance)."""
    try:
        import glob as glob_module
        upload_dir = 'generated/uploads/furry_photos'
        if not os.path.exists(upload_dir):
            return
        
        deleted = 0
        deleted_fns = []
        now = datetime.now()
        for filepath in glob_module.glob(os.path.join(upload_dir, '*')):
            if os.path.isfile(filepath):
                age_hours = (now - datetime.fromtimestamp(os.path.getmtime(filepath))).total_seconds() / 3600
                if age_hours >= 72:
                    try:
                        os.remove(filepath)
                        deleted_fns.append(os.path.basename(filepath))
                        deleted += 1
                    except Exception as e:
                        print(f"[PHOTO CLEANUP] Error deleting {filepath}: {e}")
        
        if deleted > 0:
            print(f"[PHOTO CLEANUP] Auto-deleted {deleted} expired photos (>72h)")
            try:
                with app.app_context():
                    _now_utc = datetime.utcnow()
                    for _fn in deleted_fns:
                        _log = PhotoUploadLog.query.filter_by(filename=_fn, deleted_at=None).first()
                        if _log:
                            _log.deleted_at = _now_utc
                    db.session.commit()
            except Exception as _le:
                print(f"[PHOTO CLEANUP] Log update error: {_le}")
    except Exception as e:
        print(f"[PHOTO CLEANUP ERROR] {str(e)}")


def scheduled_temp_file_cleanup():
    """Clean up temporary files older than 48 hours to prevent disk filling on VPS"""
    with app.app_context():
        try:
            from services.task_queue import cleanup_temp_files, production_logger
            import shutil
            
            base_dir = os.path.dirname(os.path.abspath(__file__))
            temp_dirs = [
                os.path.join(base_dir, 'static', 'generated', 'haz_tu_historia'),
                os.path.join(base_dir, 'static', 'generated', 'personalized'),
                os.path.join(base_dir, 'uploads', 'haz_tu_historia'),
            ]
            
            cutoff = datetime.utcnow() - timedelta(hours=48)
            cleaned_count = 0
            
            for temp_dir in temp_dirs:
                if not os.path.exists(temp_dir):
                    continue
                    
                for order_folder in os.listdir(temp_dir):
                    folder_path = os.path.join(temp_dir, order_folder)
                    if not os.path.isdir(folder_path):
                        continue
                    
                    try:
                        mtime = datetime.fromtimestamp(os.path.getmtime(folder_path))
                        if mtime < cutoff:
                            order = RealStoryOrder.query.filter_by(order_number=order_folder).first()
                            if order and order.status in ['DELIVERED', 'COMPLETED']:
                                for filename in os.listdir(folder_path):
                                    if filename.startswith('temp_') or filename.startswith('watermark_'):
                                        filepath = os.path.join(folder_path, filename)
                                        os.remove(filepath)
                                        cleaned_count += 1
                    except Exception as e:
                        production_logger.warning(f"[CLEANUP] Error cleaning {folder_path}: {e}")
            
            if cleaned_count > 0:
                production_logger.info(f"[SCHEDULER] Temp file cleanup: {cleaned_count} files removed")
            else:
                production_logger.debug("[SCHEDULER] Temp file cleanup: no files to clean")
                
        except Exception as e:
            print(f"[SCHEDULER ERROR] Temp file cleanup failed: {str(e)}")


def scheduled_log_rotation():
    """Rotate production logs to prevent disk filling"""
    try:
        from services.task_queue import LOG_DIR
        import gzip
        
        max_log_size = 50 * 1024 * 1024
        
        for log_file in ['production.log', 'api_errors.log']:
            log_path = os.path.join(LOG_DIR, log_file)
            if os.path.exists(log_path) and os.path.getsize(log_path) > max_log_size:
                archive_path = f"{log_path}.{datetime.now().strftime('%Y%m%d_%H%M%S')}.gz"
                with open(log_path, 'rb') as f_in:
                    with gzip.open(archive_path, 'wb') as f_out:
                        f_out.writelines(f_in)
                with open(log_path, 'w') as f:
                    f.write(f"# Log rotated at {datetime.now().isoformat()}\n")
                print(f"[SCHEDULER] Log rotated: {log_file}")
    except Exception as e:
        print(f"[SCHEDULER ERROR] Log rotation failed: {str(e)}")


def scheduled_ebook_expiry_check():
    try:
        from datetime import datetime, timedelta
        now = datetime.now()
        warning_window_start = now + timedelta(days=6, hours=12)
        warning_window_end = now + timedelta(days=7, hours=12)
        scanned = 0
        warned = 0
        for folder in ('story_previews', 'generations/previews'):
            if not os.path.exists(folder):
                continue
            for fname in os.listdir(folder):
                if not fname.endswith('.json'):
                    continue
                fpath = os.path.join(folder, fname)
                try:
                    with open(fpath, 'r', encoding='utf-8') as f:
                        sd = json.load(f)
                    scanned += 1
                    expires_at = sd.get('ebook_expires_at')
                    customer_email = sd.get('customer_email', '')
                    if not expires_at or expires_at == 'null' or not customer_email:
                        continue
                    if sd.get('expiry_warning_sent'):
                        continue
                    expiry_dt = datetime.fromisoformat(expires_at)
                    if warning_window_start <= expiry_dt <= warning_window_end:
                        child_name = sd.get('child_name', 'tu hijo')
                        lang = sd.get('lang', sd.get('language', 'es'))
                        preview_id = sd.get('preview_id', fname.replace('.json', ''))
                        base_url = os.environ.get('SITE_DOMAIN', 'magicmemoriesbooks.com')
                        renew_url = f'https://{base_url}/renew-ebook/{preview_id}'
                        from services.email_service import send_ebook_expiry_warning_email
                        from config import Config as _Cfg
                        # Price: use what was offered at purchase time, or fall back to story-type default
                        _fp = sd.get('format_prices') or {}
                        _ebook_price = float(_fp.get('ebook') or 0)
                        if not _ebook_price:
                            _is_universos = sd.get('story_id', '').startswith(('universo', 'illustrated', 'haz_tu_historia'))
                            _ebook_price = _Cfg.UNIVERSOS_EBOOK_PRICE / 100.0 if _is_universos else _Cfg.EBOOK_BASE_PRICE / 100.0
                        days_left = max(1, (expiry_dt - now).days)
                        result = send_ebook_expiry_warning_email(customer_email, child_name, days_left, renew_url, lang,
                                                                        preview_id=preview_id, ebook_price=_ebook_price)
                        if result.get('success'):
                            sd['expiry_warning_sent'] = True
                            with open(fpath, 'w', encoding='utf-8') as f:
                                json.dump(sd, f, ensure_ascii=False, indent=2)
                            warned += 1
                except Exception as e:
                    print(f"[EXPIRY-CHECK] Error processing {fname}: {e}")
        print(f"[EXPIRY-CHECK] Scanned {scanned} stories, sent {warned} expiry warnings")
    except Exception as e:
        print(f"[EXPIRY-CHECK] Failed: {e}")


def restore_stories_from_backup():
    """On startup: restore any story_previews/*.json that are missing but exist in PostgreSQL backup."""
    try:
        with app.app_context():
            os.makedirs('story_previews', exist_ok=True)
            backups = StoryBackup.query.all()
            restored = 0
            for backup in backups:
                path = f'story_previews/{backup.preview_id}.json'
                if not os.path.exists(path):
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(backup.data)
                    restored += 1
            if restored > 0:
                print(f"[STORY-BACKUP] Restored {restored} story preview(s) from database after restart")
            else:
                print(f"[STORY-BACKUP] All {len(backups)} story previews already on disk — no restore needed")
    except Exception as e:
        print(f"[STORY-BACKUP] Restore failed: {e}")


def scheduled_story_backup():
    """Every 5 min: sync story_previews/*.json to PostgreSQL and remove orphaned DB records."""
    try:
        with app.app_context():
            os.makedirs('story_previews', exist_ok=True)
            saved = 0
            disk_ids = set()
            for fname in os.listdir('story_previews'):
                if not fname.endswith('.json'):
                    continue
                preview_id = fname[:-5]
                disk_ids.add(preview_id)
                path = f'story_previews/{preview_id}.json'
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        raw = f.read()
                    backup = StoryBackup.query.filter_by(preview_id=preview_id).first()
                    if backup:
                        if backup.data != raw:
                            backup.data = raw
                            backup.updated_at = datetime.utcnow()
                            db.session.commit()
                            saved += 1
                    else:
                        db.session.add(StoryBackup(preview_id=preview_id, data=raw))
                        db.session.commit()
                        saved += 1
                except Exception as e:
                    print(f"[STORY-BACKUP] Error backing up {preview_id}: {e}")
            orphans_removed = 0
            for backup in StoryBackup.query.all():
                if backup.preview_id not in disk_ids:
                    db.session.delete(backup)
                    orphans_removed += 1
            if orphans_removed > 0:
                db.session.commit()
                print(f"[STORY-BACKUP] Removed {orphans_removed} orphaned DB record(s)")
            if saved > 0:
                print(f"[STORY-BACKUP] Backed up {saved} story preview(s) to database")
    except Exception as e:
        print(f"[STORY-BACKUP] Scheduled backup failed: {e}")


def _get_protected_preview_ids():
    """Returns an empty set — demo protection no longer needed."""
    return set()


def _has_committed_ebook(data):
    """Return True if this story has an eBook committed to a customer.

    Covers: paid purchases, 6-month licenses, permanent licenses, gift books,
    and any story where the eBook email was already sent.
    These must NEVER be deleted automatically or via the generic delete button.
    """
    if not data.get('visor_url'):
        return False
    return bool(
        data.get('paid') or
        data.get('ebook_expires_at') or
        data.get('ebook_permanent') or
        data.get('ebook_email_sent') or
        data.get('admin_gift') or
        data.get('payment_status') == 'admin_gift'
    )


def _purge_story_files(preview_id, story_data, include_lulu=False, include_print=False, skip_visor=False):
    """Delete all files associated with a story (scenes, visor pages, generated images, user photos).

    skip_visor=True preserves the visor/eBook directory so customers keep access.
    """
    import shutil
    scenes_dir = f'story_previews/{preview_id}'
    if os.path.exists(scenes_dir):
        shutil.rmtree(scenes_dir)
    if include_lulu or include_print:
        lulu_folder = story_data.get('lulu_order_folder', '')
        if lulu_folder and os.path.exists(lulu_folder):
            shutil.rmtree(lulu_folder)
        cp_folder = f'generations/cloudprinter/{preview_id}'
        if os.path.exists(cp_folder):
            shutil.rmtree(cp_folder)
    if not skip_visor:
        for visor_type in ('visor_qs', 'visor_pb'):
            visor_dir = f'generations/{visor_type}/{preview_id}'
            if os.path.exists(visor_dir):
                shutil.rmtree(visor_dir)
    output_dir = story_data.get('output_dir', '') or story_data.get('image_dir', '')
    if output_dir and os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    character_preview = story_data.get('character_preview', '')
    if character_preview:
        cp_path = character_preview.lstrip('/')
        if os.path.exists(cp_path):
            try:
                os.remove(cp_path)
            except Exception:
                pass
    upload_prefix = 'generated/uploads/furry_photos/'
    for photo_key in ('human_photo_path', 'pet_photo_path', 'child_photo_path'):
        photo_path = story_data.get('traits', {}).get(photo_key, '') or story_data.get(photo_key, '')
        if photo_path and photo_path.startswith(upload_prefix) and os.path.exists(photo_path):
            try:
                os.remove(photo_path)
            except Exception:
                pass


def auto_purge_old_stories():
    """Every hour: delete stories older than 72h. Protects demo stories from admin_config.json."""
    try:
        with app.app_context():
            protected = _get_protected_preview_ids()
            os.makedirs('story_previews', exist_ok=True)
            purged = 0
            now = datetime.utcnow()
            cutoff = now - timedelta(hours=72)
            for fname in os.listdir('story_previews'):
                if not fname.endswith('.json'):
                    continue
                preview_id = fname[:-5]
                if preview_id in protected:
                    continue
                path = f'story_previews/{preview_id}.json'
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    payment_date_str = data.get('payment_date', '')
                    if not payment_date_str:
                        continue
                    try:
                        story_date = datetime.fromisoformat(payment_date_str.replace('Z', '+00:00').replace('+00:00', ''))
                    except Exception:
                        continue
                    if story_date > cutoff:
                        continue
                    # NEVER purge paid orders — only unpaid previews age out
                    if data.get('paid'):
                        continue
                    if _has_committed_ebook(data):
                        print(f"[AUTO-PURGE] Skipping {preview_id} — has committed eBook")
                        continue
                    _purge_story_files(preview_id, data)
                    os.remove(path)
                    try:
                        StoryBackup.query.filter_by(preview_id=preview_id).delete()
                        db.session.commit()
                    except Exception:
                        db.session.rollback()
                    purged += 1
                    print(f"[AUTO-PURGE] Purged story {preview_id}")
                except Exception as e:
                    print(f"[AUTO-PURGE] Error purging {preview_id}: {e}")
            if purged > 0:
                print(f"[AUTO-PURGE] Purged {purged} story/stories older than 72h")
    except Exception as e:
        print(f"[AUTO-PURGE] Failed: {e}")


scheduler = BackgroundScheduler()
scheduler.add_job(func=scheduled_photo_cleanup, trigger="interval", hours=6, id='photo_cleanup')
scheduler.add_job(func=scheduled_temp_file_cleanup, trigger="interval", hours=12, id='temp_cleanup')
scheduler.add_job(func=scheduled_log_rotation, trigger="interval", hours=6, id='log_rotation')
scheduler.add_job(func=scheduled_ebook_expiry_check, trigger="interval", hours=24, id='ebook_expiry_check')
scheduler.add_job(func=scheduled_story_backup, trigger="interval", minutes=5, id='story_backup')
scheduler.add_job(func=auto_purge_old_stories, trigger="interval", hours=1, id='auto_purge_stories')


def scheduled_lead_follow_up_emails():
    """Hourly job: send 24h post-purchase feedback emails that are due."""
    try:
        from services.email_service import process_pending_follow_up_emails
        process_pending_follow_up_emails()
    except Exception as e:
        print(f"[LEAD] Scheduler error: {e}")


scheduler.add_job(func=scheduled_lead_follow_up_emails, trigger="interval", hours=1, id='lead_follow_up_emails')



def scheduled_isabel_campaign_3h():
    """Hourly job: send Isabel's campaign email to leads 3h–30d old who haven't purchased."""
    try:
        with app.app_context():
            from datetime import datetime as _dt3, timedelta as _td3
            from services.email_service import send_isabel_campaign_email, _is_duplicate_send
            import json as _j3, glob as _g3, os as _o3

            now = _dt3.utcnow()
            window_start = now - _td3(days=30)
            window_end   = now - _td3(hours=3)

            candidates = (
                PreviewLead.query
                .filter(PreviewLead.email != '',
                        PreviewLead.created_at >= window_start,
                        PreviewLead.created_at <= window_end)
                .order_by(PreviewLead.created_at.desc())
                .all()
            )

            story_dir = _o3.path.join(_o3.path.dirname(__file__), 'story_previews')

            # Build purchased set
            purchased_emails = set()
            if _o3.path.isdir(story_dir):
                for jf in _g3.glob(_o3.path.join(story_dir, '*.json')):
                    try:
                        with open(jf, 'r', encoding='utf-8') as _f:
                            sd = _j3.load(_f)
                        if (sd.get('paid') or sd.get('ebook_paid') or sd.get('pdf_paid')
                                or sd.get('payment_status') == 'completed'
                                or float(sd.get('amount_paid') or sd.get('customer_total_usd') or 0) > 0):
                            em = (sd.get('customer_email') or '').strip().lower()
                            if em:
                                purchased_emails.add(em)
                    except Exception:
                        pass

            # Build story info index (child_name + lang) keyed by email and story_id
            info_by_email, info_by_sid = {}, {}
            if _o3.path.isdir(story_dir):
                for jf in _g3.glob(_o3.path.join(story_dir, '*.json')):
                    try:
                        with open(jf, 'r', encoding='utf-8') as _f:
                            sd = _j3.load(_f)
                        entry = {'child_name': sd.get('child_name', ''),
                                 'lang': sd.get('lang', 'es')}
                        em = (sd.get('customer_email') or '').strip().lower()
                        if em and em not in info_by_email:
                            info_by_email[em] = entry
                        sid = sd.get('story_id', '')
                        if sid and sid not in info_by_sid:
                            info_by_sid[sid] = entry
                    except Exception:
                        pass

            seen, sent_count = set(), 0
            for lead in candidates:
                em = (lead.email or '').strip().lower()
                if not em or '@' not in em or em in seen:
                    continue
                seen.add(em)
                if em in purchased_emails:
                    continue
                if _is_duplicate_send(preview_id=em, email_type='lead_campaign_isabel', days=365):
                    continue
                info = info_by_email.get(em) or info_by_sid.get(lead.story_id or '', {})
                ok = send_isabel_campaign_email(em, info.get('child_name', ''), info.get('lang', 'es'))
                if ok:
                    sent_count += 1

            if sent_count:
                print(f"[ISABEL-3H] ✅ Sent to {sent_count} leads")
    except Exception as _e:
        print(f"[ISABEL-3H] ❌ Error: {_e}")



# Only start the scheduler in ONE Gunicorn worker using an exclusive file lock.
# Without this, each of the N workers starts its own scheduler → N duplicate emails/jobs.
import fcntl as _fcntl
_SCHEDULER_LOCK_PATH = '/tmp/mmb_scheduler.lock'
_scheduler_lock_fd = None
try:
    _scheduler_lock_fd = open(_SCHEDULER_LOCK_PATH, 'w')
    _fcntl.flock(_scheduler_lock_fd, _fcntl.LOCK_EX | _fcntl.LOCK_NB)
    scheduler.start()
    # Isabel 3h campaign — always ON
    scheduler.add_job(func=scheduled_isabel_campaign_3h,
                      trigger="interval", hours=1,
                      id='isabel_campaign_3h',
                      replace_existing=True)
    print(f"[SCHEDULER] Started in worker PID {os.getpid()} — Isabel 3h campaign ACTIVE")
    atexit.register(lambda: scheduler.shutdown())
except IOError:
    print(f"[SCHEDULER] Skipped in worker PID {os.getpid()} (another worker owns the lock)")
except Exception as _sched_err:
    print(f"[SCHEDULER] Could not start: {_sched_err}")

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['GENERATED_FOLDER'], exist_ok=True)
os.makedirs('story_previews', exist_ok=True)
os.makedirs('logs', exist_ok=True)
os.makedirs('generated/uploads/furry_photos', exist_ok=True)

scheduled_photo_cleanup()
restore_stories_from_backup()
scheduled_story_backup()
auto_purge_old_stories()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def get_visor_base_url(visor_type='visor'):
    site_domain = os.environ.get('SITE_DOMAIN') or os.environ.get('REPLIT_DEV_DOMAIN', 'magicmemoriesbooks.com')
    return f'https://{site_domain}/{visor_type}'

def get_lang():
    return session.get('lang', app.config['DEFAULT_LANGUAGE'])

def t(key):
    return get_translation(get_lang(), key)

def get_story_template_by_id(story_id, child_name='', child_gender='neutral'):
    for template in STORY_TEMPLATES:
        if template['id'] == story_id:
            return template
    
    from services.fixed_stories import STORIES
    if story_id in STORIES:
        story = STORIES[story_id]
        lang = get_lang()
        name_placeholder = child_name if child_name else '[Nombre]'
        lo_la = 'la' if child_gender == 'female' else 'lo'
        hisher = 'her' if child_gender == 'female' else ('his' if child_gender == 'male' else 'their')
        return {
            'id': story_id,
            'name_es': story.get('title_es', '').replace('{name}', name_placeholder).replace('{lo_la}', lo_la).replace('{pet_name}', 'tu mascota'),
            'name_en': story.get('title_en', '').replace('{name}', name_placeholder).replace('{pet_name}', 'your pet').replace('{hisher}', hisher),
            'age_range': story.get('age_range', '0-1')
        }
    return None

@app.context_processor
def inject_globals():
    from services.cart import cart_count as _cart_count
    lang = get_lang()
    return {
        't': t,
        'lang': lang,
        'translations': TRANSLATIONS.get(lang, TRANSLATIONS['es']),
        'story_templates': STORY_TEMPLATES,
        'cart_count': _cart_count(session),
    }

@app.before_request
def before_request():
    if 'lang' not in session:
        session['lang'] = app.config['DEFAULT_LANGUAGE']

@app.route('/set-language/<lang>')
def set_language(lang):
    if lang in app.config['SUPPORTED_LANGUAGES']:
        session['lang'] = lang
    return redirect(request.referrer or url_for('index'))

@app.route('/')
def index():
    try:
        from sqlalchemy import text as _sql_text
        import glob as _glob
        paid_orders = db.session.execute(_sql_text("SELECT COUNT(*) FROM orders WHERE amount_paid > 0")).scalar() or 0
        paid_real = db.session.execute(_sql_text("SELECT COUNT(*) FROM real_story_orders WHERE amount_paid > 0")).scalar() or 0
        paid_json = 0
        _preview_dir = os.path.join(os.path.dirname(__file__), 'story_previews')
        for _jf in _glob.glob(os.path.join(_preview_dir, '*.json')):
            if '_progress' in _jf:
                continue
            try:
                with open(_jf) as _f:
                    _d = json.load(_f)
                if _d.get('paid'):
                    paid_json += 1
            except Exception:
                pass
        stories_count = 500 + paid_orders + paid_real + paid_json
        stories_display = f"{stories_count}+"
    except Exception:
        stories_display = "500+"
    # Testimonials keyed by filename — add new ones here to grow the gallery
    # Each entry: es/en text + author_es/author_en for bilingual display
    GALLERY_TESTIMONIALS = {
        '00_sofia_mom_reading.jpg': {
            'es': 'No podía creer que ella fuera la protagonista', 'en': "She couldn't believe she was the main character",
            'author_es': 'Mamá de Sofía', 'author_en': "Sofia's mom",
        },
        '00a_lifestyle_mama_leyendo.jpg': {
            'es': 'Un momento mágico para recordar siempre', 'en': 'A magical moment to remember forever',
            'author_es': '', 'author_en': '',
        },
        '02_maria_painting.jpg': {
            'es': 'María está feliz con su cuento: cuando no se lo estoy leyendo, ¡está pintando! Qué buena idea la de las hojas de pintar.',
            'en': 'María loves her book — when I\'m not reading it to her, she\'s painting it! The coloring pages were a brilliant idea.',
            'author_es': 'Mamá de María', 'author_en': "María's mom",
        },
        '04_alex_mom_pink.jpg': {
            'es': 'Lo leyó tres veces el mismo día', 'en': 'He read it three times the same day',
            'author_es': 'Mamá de Alex', 'author_en': "Alex's mom",
        },
        '05_maria_mom_reading.jpg': {
            'es': 'Fue el regalo favorito de su cumpleaños', 'en': 'It was her favorite birthday gift',
            'author_es': '', 'author_en': '',
        },
        '06_alex_chef_cover.jpg': {
            'es': 'La cara de mi nieto habla por sí sola, es el cuento que más le gusta.',
            'en': "My grandson's face says it all — it's the book he loves the most.",
            'author_es': 'Abu Isa', 'author_en': 'Grandma Isa',
        },
        '07_maria_together.jpg': {
            'es': '«¡Soy yo, soy yo!» — al verlo por primera vez', 'en': '"It\'s me, it\'s me!" — seeing it for the first time',
            'author_es': '', 'author_en': '',
        },
        '07a_lifestyle_bebe_papa.png': {
            'es': 'Este libro, cuando mi perrita Katty conoció a nuestra pequeña Anna, es lo más bello que he tenido. Pude personalizar no solo a mi bebé, ¡sino a mi perrita también!',
            'en': 'This book about when our dog Katty first met our little Anna is the most beautiful thing I own. I could personalize not just my baby, but my dog too!',
            'author_es': 'Mamá de Anna', 'author_en': "Anna's mom",
        },
        '11a_lifestyle_nina_tablet.png': {
            'es': 'No quería que se acabara el cuento', 'en': "She didn't want the story to end",
            'author_es': '', 'author_en': '',
        },
        '05a_lifestyle_nino_piscina.png': {
            'es': 'Lo llevó hasta la piscina para leerlo', 'en': 'He took it to the pool just to read it',
            'author_es': '', 'author_en': '',
        },
    }
    gallery_items = []
    try:
        gallery_img_dir = os.path.join(app.static_folder, 'images', 'gallery')
        gallery_vid_dir = os.path.join(app.static_folder, 'videos')
        img_exts = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
        vid_exts = {'.mp4', '.webm', '.mov'}
        imgs, vids = [], []
        if os.path.isdir(gallery_img_dir):
            for f in sorted(os.listdir(gallery_img_dir)):
                if os.path.splitext(f)[1].lower() in img_exts:
                    t = GALLERY_TESTIMONIALS.get(f, {})
                    imgs.append({
                        'type': 'image',
                        'url': url_for('static', filename=f'images/gallery/{f}'),
                        'is_lifestyle': 'lifestyle' in f,
                        'testimonial_es': t.get('es', ''),
                        'testimonial_en': t.get('en', ''),
                        'author_es': t.get('author_es', ''),
                        'author_en': t.get('author_en', ''),
                    })
        posters_dir = os.path.join(app.static_folder, 'images', 'posters')
        if os.path.isdir(gallery_vid_dir):
            for f in sorted(os.listdir(gallery_vid_dir)):
                if os.path.splitext(f)[1].lower() in vid_exts:
                    base = os.path.splitext(f)[0]
                    poster_file = f'{base}.jpg'
                    poster_url = url_for('static', filename=f'images/posters/{poster_file}') \
                        if os.path.exists(os.path.join(posters_dir, poster_file)) else ''
                    vids.append({'type': 'video', 'url': url_for('static', filename=f'videos/{f}'), 'poster': poster_url,
                                 'is_lifestyle': False, 'testimonial_es': '', 'testimonial_en': ''})
        # Interleave videos at positions 2 and 7 (visible early)
        gallery_items = imgs[:]
        for i, vid in enumerate(vids):
            pos = [2, 7][i] if i < 2 else len(gallery_items)
            gallery_items.insert(pos + i, vid)
    except Exception:
        gallery_items = []
    return render_template('index.html', stories_count=stories_display, gallery_items=gallery_items)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/faq')
def faq():
    return render_template('faq.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/api/contact', methods=['POST'])
def contact_submit():
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    data = request.get_json()
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    subject = data.get('subject', '').strip()
    message = data.get('message', '').strip()
    dept = data.get('dept', 'contacto').strip()
    if not name or not email or not message:
        return jsonify({'error': 'Missing required fields'}), 400
    dept_emails = {
        'info': 'info@magicmemoriesbooks.com',
        'pay': 'pay@magicmemoriesbooks.com',
        'contacto': 'contacto@magicmemoriesbooks.com'
    }
    recipient = dept_emails.get(dept, 'contacto@magicmemoriesbooks.com')
    try:
        msg = MIMEMultipart()
        msg['From'] = os.environ.get('SENDER_EMAIL', 'info@magicmemoriesbooks.com')
        msg['To'] = recipient
        msg['Subject'] = f'[Contact Form] {subject or "New message"} - from {name}'
        msg['Reply-To'] = email
        body = f"""New contact form submission:\n\nDepartment: {dept}\nName: {name}\nEmail: {email}\nSubject: {subject}\n\nMessage:\n{message}"""
        msg.attach(MIMEText(body, 'plain'))
        smtp_host = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        smtp_user = os.environ.get('SENDER_EMAIL', '')
        smtp_pass = os.environ.get('SMTP_PASSWORD', '')
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        print(f"[CONTACT] Message sent from {email} ({name}) to {recipient}: {subject}")
        return jsonify({'success': True})
    except Exception as e:
        print(f"[CONTACT] Error sending: {e}")
        return jsonify({'error': 'Failed to send message'}), 500

SITEMAP_PERSONALIZED_STORIES = [
    # (story_id_or_variant, route, is_furry_love)
    ('baby_soft_world', 'personalize_story'),
    ('baby_puppy_love', 'personalize_story'),
    ('baby_first_pet', 'personalize_story'),
    ('baby_guardian_light', 'personalize_story'),
    ('dragon_friend', 'personalize_story'),
    ('zebra_stripes', 'personalize_story'),
    ('space_astronaut', 'personalize_story'),
    ('superhero_light', 'personalize_story'),
    ('star_guardian', 'personalize_story'),
    ('chronicles_valley', 'personalize_story'),
    ('sunset_map', 'personalize_story'),
    ('dog_forever', 'personalize_story'),
    ('birthday_celebration_1_3', 'personalize_story'),
    ('birthday_celebration_4_6', 'personalize_story'),
    ('birthday_celebration_7_9', 'personalize_story'),
    ('dragon_garden_illustrated', 'personalize_story'),
    ('magic_chef_illustrated', 'personalize_story'),
    ('magic_inventor_illustrated', 'personalize_story'),
    ('star_keeper_illustrated', 'personalize_story'),
    ('centinela_aurora_illustrated', 'personalize_story'),
    ('furry_love', 'personalize_furry_love'),
    ('furry_love_adventure', 'personalize_furry_love'),
    ('furry_love_teen', 'personalize_furry_love'),
    ('furry_love_adult', 'personalize_furry_love'),
]


@app.route('/sitemap.xml')
def sitemap():
    from datetime import date
    today = date.today().isoformat()
    domain = 'https://magicmemoriesbooks.com'

    def bilingual_urls(path, priority, changefreq, lastmod=today, query=''):
        """Return a list of (loc, alternates, lastmod, changefreq, priority) for a
        bilingual page, where `query` is an extra query string fragment such as
        '?story=xxx' (no lang param included)."""
        join = '&amp;' if query else '?'
        loc_default = f'{domain}{path}{query}'
        loc_en = f'{domain}{path}{query}{join}lang=en'
        loc_es = f'{domain}{path}{query}{join}lang=es'
        alternates = [
            ('x-default', loc_default),
            ('es', loc_es),
            ('en', loc_en),
        ]
        return [(loc_default, alternates, lastmod, changefreq, priority)]

    entries = []

    # ---- Core pages ----
    entries += bilingual_urls('/', '1.0', 'weekly')
    entries += bilingual_urls('/express-catalog', '0.9', 'weekly')
    entries += bilingual_urls('/universos-catalog', '0.9', 'weekly')
    entries += bilingual_urls('/birthday-stories', '0.9', 'weekly')
    entries += bilingual_urls('/pricing', '0.8', 'monthly')
    entries += bilingual_urls('/faq', '0.7', 'monthly')
    entries += bilingual_urls('/contact', '0.6', 'monthly')
    entries += bilingual_urls('/about', '0.6', 'monthly')
    entries += bilingual_urls('/cuentos-solidarios', '0.8', 'weekly')
    entries += bilingual_urls('/terms', '0.3', 'yearly')
    entries += bilingual_urls('/privacy', '0.3', 'yearly')

    # ---- Personalized stories (24 books) ----
    for story_key, route_name in SITEMAP_PERSONALIZED_STORIES:
        path = '/personalize-story' if route_name == 'personalize_story' else '/personalize-furry-love'
        entries += bilingual_urls(path, '0.6', 'weekly', query=f'?story={story_key}')

    # ---- Cuentos Solidarios (published stories) ----
    try:
        published_stories = CommunityStory.query.filter_by(status='published').all()
        for story in published_stories:
            lastmod_story = (story.updated_at or story.created_at)
            lastmod_story = lastmod_story.date().isoformat() if lastmod_story else today
            entries += bilingual_urls(f'/cuentos-solidarios/{story.slug}', '0.7', 'monthly',
                                       lastmod=lastmod_story)
    except Exception:
        pass

    xml_parts = ['<?xml version="1.0" encoding="UTF-8"?>',
                 '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
                 'xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for loc, alternates, lastmod, changefreq, priority in entries:
        xml_parts.append(f'  <url><loc>{loc}</loc>')
        for hreflang, alt_loc in alternates:
            xml_parts.append(f'    <xhtml:link rel="alternate" hreflang="{hreflang}" href="{alt_loc}"/>')
        xml_parts.append(f'    <lastmod>{lastmod}</lastmod>'
                          f'<changefreq>{changefreq}</changefreq><priority>{priority}</priority></url>')
    xml_parts.append('</urlset>')
    return '\n'.join(xml_parts), 200, {'Content-Type': 'application/xml; charset=utf-8'}

@app.route('/robots.txt')
def robots_txt():
    content = (
        'User-agent: *\n'
        'Allow: /\n'
        'Disallow: /admin\n'
        'Disallow: /api/\n'
        'Disallow: /story-preview/\n'
        'Disallow: /order-complete/\n'
        '\n'
        'Sitemap: https://magicmemoriesbooks.com/sitemap.xml\n'
    )
    return content, 200, {'Content-Type': 'text/plain; charset=utf-8'}

@app.route('/pricing')
def pricing():
    return render_template('pricing.html')


# ── Redirecciones 301 desde URLs antiguas (WordPress) ──────────────────────
@app.route('/comprar/')
@app.route('/comprar')
def redirect_comprar():
    return redirect('/pricing', code=301)

@app.route('/en/comprar/')
@app.route('/en/comprar')
def redirect_comprar_en():
    return redirect('/pricing', code=301)

@app.route('/producto/cuento-personalizado/')
@app.route('/producto/cuento-personalizado')
def redirect_producto():
    return redirect('/personalized-books', code=301)

@app.route('/en/producto/cuento-personalizado/')
@app.route('/en/producto/cuento-personalizado')
def redirect_producto_en():
    return redirect('/personalized-books', code=301)

@app.route('/en/')
@app.route('/en')
def redirect_en():
    return redirect('/', code=301)

@app.route('/author/grupodotcom/')
@app.route('/author/grupodotcom')
@app.route('/author/<string:name>/')
@app.route('/author/<string:name>')
def redirect_author(name=None):
    return redirect('/', code=301)

@app.route('/wp-content/<path:subpath>')
def redirect_wp_content(subpath):
    return redirect('/', code=301)

@app.route('/wp-admin/<path:subpath>')
def redirect_wp_admin(subpath):
    return redirect('/', code=301)
# ── Fin redirecciones 301 ───────────────────────────────────────────────────

# Redirect WordPress ?page_id= and ?p= query params at root
@app.before_request
def redirect_wp_query_params():
    from flask import request as req
    if req.path == '/' and (req.args.get('page_id') or req.args.get('p')):
        return redirect('/', code=301)


@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/story-selection')
def story_selection():
    return redirect('/#precios', code=301)

@app.route('/express-catalog')
def express_catalog():
    lang = get_lang()
    return render_template('express_catalog.html', lang=lang, translations=TRANSLATIONS.get(lang, TRANSLATIONS['es']))

@app.route('/story-selection/express')
def story_selection_express():
    return redirect(url_for('express_catalog'))

@app.route('/universos-catalog')
def universos_catalog():
    lang = get_lang()
    return render_template('universos_catalog.html', lang=lang, translations=TRANSLATIONS.get(lang, TRANSLATIONS['es']))

@app.route('/story-selection/universos')
def story_selection_universos():
    return redirect(url_for('universos_catalog'))

@app.route('/stories-0-1')
def stories_0_1():
    return redirect(url_for('express_catalog'))

@app.route('/stories-3-8')
def stories_3_8():
    return redirect(url_for('express_catalog'))

@app.route('/stories-3-5')
def stories_3_5():
    return redirect(url_for('express_catalog'))

@app.route('/stories-5-7')
def stories_5_7():
    return redirect(url_for('express_catalog'))

@app.route('/personalized-books')
def personalized_books():
    is_change_mode = request.args.get('change') == '1'
    if not is_change_mode:
        return redirect(url_for('universos_catalog'))
    original_preview_id = request.args.get('preview_id', '')
    return render_template('personalized_books.html',
                          is_change_mode=is_change_mode,
                          original_preview_id=original_preview_id)

@app.route('/birthday-stories')
def birthday_stories():
    lang = get_lang()
    return render_template('birthday_stories.html', lang=lang,
                           translations=TRANSLATIONS.get(lang, TRANSLATIONS['es']))

@app.route('/stories-birthday')
def stories_birthday():
    return redirect('/birthday-stories', code=301)

@app.route('/birthday')
def birthday_selection():
    return redirect('/birthday-stories', code=301)

@app.route('/birthday-1-3')
def birthday_1_3():
    return redirect('/personalize-story?story=birthday_celebration_1_3')

@app.route('/birthday-4-6')
def birthday_4_6():
    return redirect('/personalize-story?story=birthday_celebration_4_6')

@app.route('/birthday-7-9')
def birthday_7_9():
    return redirect('/personalize-story?story=birthday_celebration_7_9')

@app.route('/furry-love')
def furry_love_catalog():
    return redirect(url_for('universos_catalog'))

@app.route('/personalize-furry-love')
def personalize_furry_love():
    lang = get_lang()
    from services.fixed_stories import STORIES
    story_variant = request.args.get('story', 'furry_love')
    story_id = f'{story_variant}_illustrated'
    if story_id not in STORIES:
        story_id = 'furry_love_illustrated'
        story_variant = 'furry_love'
    story_config = STORIES.get(story_id, {})
    story_pages = []
    source_pages = story_config.get('content_pages', [])
    import re
    for page in source_pages:
        if 'text_es' in page:
            text_es = page['text_es']
            text_en = page.get('text_en', '')
        else:
            parts_es = [page.get('text_above_es', ''), page.get('text_below_es', '')]
            parts_en = [page.get('text_above_en', ''), page.get('text_below_en', '')]
            text_es = '\n'.join(p for p in parts_es if p)
            text_en = '\n'.join(p for p in parts_en if p)
        text_es = text_es.replace('{name}', '[NOMBRE]').replace('{pet_name}', '[MASCOTA]')
        text_en = text_en.replace('{name}', '[NAME]').replace('{pet_name}', '[PET]')
        text_es = re.sub(r'\{[a-z_]+\}', '', text_es)
        text_en = re.sub(r'\{[a-z_]+\}', '', text_en)
        story_pages.append({'text_es': text_es, 'text_en': text_en})
    prefill_name = request.args.get('name', '')
    prefill_pet = request.args.get('pet_name', '')
    prefill_gender = request.args.get('gender', '')
    admin_gift = request.args.get('admin_gift', '')

    og_meta = STORY_OG_META.get(story_id, {})
    og_title = og_meta.get('title_es' if lang == 'es' else 'title_en', 'Magic Memories Books')
    og_description = og_meta.get('desc_es' if lang == 'es' else 'desc_en', '')
    og_image_file = og_meta.get('image', 'og/og_universos_catalog.jpg')
    og_image_url = f'https://magicmemoriesbooks.com/static/images/{og_image_file}'

    return render_template('personalize_furry_love.html',
        lang=lang,
        translations=TRANSLATIONS.get(lang, TRANSLATIONS['es']),
        story_pages=story_pages,
        story_id=story_id,
        story_variant=story_variant,
        prefill_name=prefill_name,
        prefill_pet=prefill_pet,
        prefill_gender=prefill_gender,
        admin_gift=admin_gift,
        og_title=og_title,
        og_description=og_description,
        og_image_url=og_image_url
    )

@app.route('/api/upload-furry-photo', methods=['POST'])
def upload_furry_photo():
    import uuid as uuid_mod
    
    consent = request.form.get('consent', '')
    lang = request.form.get('lang', 'es')
    if consent != 'true':
        msg = 'Se requiere consentimiento para fotos (COPPA/GDPR)' if lang == 'es' else 'Photo consent required (COPPA/GDPR)'
        return jsonify({'success': False, 'error': msg})
    
    if 'photo' not in request.files:
        msg = 'No se recibió ninguna foto' if lang == 'es' else 'No photo provided'
        return jsonify({'success': False, 'error': msg})
    
    photo = request.files['photo']
    photo_type = request.form.get('type', 'human')
    
    if photo.filename == '':
        msg = 'No se seleccionó ningún archivo' if lang == 'es' else 'No file selected'
        return jsonify({'success': False, 'error': msg})
    
    allowed_ext = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    ext = photo.filename.rsplit('.', 1)[-1].lower() if '.' in photo.filename else ''
    if ext not in allowed_ext:
        msg = 'Tipo de archivo no válido. Usa JPG, PNG o WEBP.' if lang == 'es' else 'Invalid file type. Use JPG, PNG, or WEBP.'
        return jsonify({'success': False, 'error': msg})
    
    upload_dir = 'generated/uploads/furry_photos'
    os.makedirs(upload_dir, exist_ok=True)
    
    filename = f"{photo_type}_{uuid_mod.uuid4().hex[:8]}.{ext}"
    filepath = os.path.join(upload_dir, filename)
    photo.save(filepath)
    
    print(f"[FURRY PHOTO UPLOAD] Saved {photo_type} photo: {filepath}")
    
    # Log upload permanently (record survives 72h deletion)
    try:
        _story_id_log = (request.form.get('story_id') or '').strip()[:100]
        _fsize = round(os.path.getsize(filepath) / 1024, 1)
        _log_entry = PhotoUploadLog(
            filename=filename,
            story_id=_story_id_log,
            photo_type=photo_type,
            ip_address=request.remote_addr,
            file_size_kb=_fsize,
        )
        db.session.add(_log_entry)
        db.session.commit()
    except Exception as _le:
        print(f"[PHOTO LOG] Could not log upload: {_le}")
        db.session.rollback()
    
    return jsonify({'success': True, 'path': filepath})

STORY_OG_META = {
    "baby_soft_world": {
        "title_es": "El Mundo Suave | Magic Memories Books",
        "title_en": "The Soft World | Magic Memories Books",
        "desc_es": "Cuento mágico para bebés 0-2 años. Tu pequeño/a es el protagonista. Ilustraciones únicas con IA, amor y colores suaves.",
        "desc_en": "Magical personalized story for babies 0-2. Your little one is the star of a soft colorful world. Unique AI illustrations.",
        "image": "og/og_baby_soft_world.jpg",
    },
    "baby_puppy_love": {
        "title_es": "¿Sabes cuánto te quiero? | Magic Memories Books",
        "title_en": "How Much I Love You | Magic Memories Books",
        "desc_es": "Cuento personalizado lleno de amor para bebés de 0 a 2 años. Ilustraciones únicas con IA. El regalo perfecto de nacimiento.",
        "desc_en": "Personalized story full of love for babies 0-2. Unique AI illustrations. The perfect newborn or first birthday gift.",
        "image": "og/og_baby_puppy_love.jpg",
    },
    "baby_first_pet": {
        "title_es": "La Primera Mascota | Magic Memories Books",
        "title_en": "Baby's First Pet | Magic Memories Books",
        "desc_es": "Cuento donde tu bebé conoce a su primera mascota. Historia tierna con ilustraciones únicas generadas con IA.",
        "desc_en": "Personalized story where your baby meets their first pet. A tender AI-illustrated tale for the family's tiniest member.",
        "image": "og/og_baby_first_pet.jpg",
    },
    "baby_guardian_light": {
        "title_es": "La Luz Guardiana | Magic Memories Books",
        "title_en": "The Guardian Light | Magic Memories Books",
        "desc_es": "Cuento mágico donde la luz guarda los sueños de tu bebé. Ilustraciones suaves con IA e historia completamente única.",
        "desc_en": "A guardian light watches over your baby's dreams. Soft AI illustrations and a completely unique personalized narrative.",
        "image": "og/og_baby_guardian_light.jpg",
    },
    "dragon_friend": {
        "title_es": "El Amigo Dragón | Magic Memories Books",
        "title_en": "The Dragon Friend | Magic Memories Books",
        "desc_es": "Tu hijo/a se convierte en el héroe junto a su amigo dragón. Cuento con IA e ilustraciones únicas para niños de 3-5.",
        "desc_en": "Your child is the hero alongside their dragon friend. AI-personalized story with unique illustrations for kids 3-5.",
        "image": "og/og_dragon_friend.jpg",
    },
    "zebra_stripes": {
        "title_es": "Aventura en la Sabana | Magic Memories Books",
        "title_en": "Savanna Adventure | Magic Memories Books",
        "desc_es": "Tu pequeño/a explora la sabana africana en esta aventura personalizada. Cuento con IA e ilustraciones únicas. Niños 3-8.",
        "desc_en": "Your little one explores the African savanna in this personalized adventure. AI-illustrated story for kids 3-8.",
        "image": "og/og_zebra_stripes.jpg",
    },
    "space_astronaut": {
        "title_es": "El Astronauta | Magic Memories Books",
        "title_en": "Junior Astronaut | Magic Memories Books",
        "desc_es": "Tu hijo/a viaja al espacio como astronauta en este cuento con IA. Aventura galáctica única para niños de 3-8 años.",
        "desc_en": "Your child travels to space as an astronaut in this AI-personalized book. A unique galactic adventure for kids 3-8.",
        "image": "og/og_space_astronaut.jpg",
    },
    "superhero_light": {
        "title_es": "El Superhéroe de la Luz | Magic Memories Books",
        "title_en": "Superhero of Light | Magic Memories Books",
        "desc_es": "Tu hijo/a descubre sus superpoderes en este cuento personalizado. Historia de valentía y magia con IA para niños de 6-8 años.",
        "desc_en": "Your child discovers their superpowers in this personalized story. A tale of bravery and magic, AI-generated for kids 6-8.",
        "image": "og/og_superhero_light.jpg",
    },
    "star_guardian": {
        "title_es": "El Secreto de las Estrellas | Magic Memories Books",
        "title_en": "Secret of the Stars | Magic Memories Books",
        "desc_es": "Tu hijo/a guarda el secreto de las estrellas en una aventura nocturna con IA. Ilustraciones mágicas para niños de 6-8 años.",
        "desc_en": "Your child holds the secret of the stars in an AI-personalized nighttime adventure. Magical illustrations for kids 6-8.",
        "image": "og/og_star_guardian.jpg",
    },
    "chronicles_valley": {
        "title_es": "El Mundo Secreto | Magic Memories Books",
        "title_en": "The Secret World | Magic Memories Books",
        "desc_es": "Tu hijo/a descubre un mundo secreto lleno de magia en este cuento con IA e ilustraciones únicas para niños de 5-7.",
        "desc_en": "Your child discovers a secret world full of magic in this AI-personalized story with unique illustrations. For kids 5-7.",
        "image": "og/og_chronicles_valley.jpg",
    },
    "sunset_map": {
        "title_es": "El Mapa del Atardecer | Magic Memories Books",
        "title_en": "The Sunset Map | Magic Memories Books",
        "desc_es": "Un mapa misterioso lleva a tu hijo/a a una aventura al atardecer. Cuento con IA e ilustraciones únicas para niños 5-7.",
        "desc_en": "A mysterious map takes your child on a stunning sunset adventure. AI story with unique illustrations for kids 5-7.",
        "image": "og/og_sunset_map.jpg",
    },
    "dog_forever": {
        "title_es": "Su Perro para Siempre | Magic Memories Books",
        "title_en": "Their Dog Forever | Magic Memories Books",
        "desc_es": "La historia de amor entre tu hijo/a y su fiel perro. Cuento con IA e ilustraciones únicas para niños de 6-8 años.",
        "desc_en": "Your child and their loyal dog companion. AI-personalized book with unique illustrations for kids 6-8.",
        "image": "og/og_dog_forever.jpg",
    },
    "birthday_celebration_1_3": {
        "title_es": "Cuento de Cumpleaños 1-3 Años | Magic Memories Books",
        "title_en": "Birthday Book Ages 1-3 | Magic Memories Books",
        "desc_es": "Celebra el cumpleaños con un cuento mágico personalizado. Ilustraciones únicas con IA. El regalo perfecto para los primeros.",
        "desc_en": "Celebrate your baby's birthday with a magical personalized story. Unique AI illustrations. The perfect early years gift.",
        "image": "og/og_birthday_celebration_1_3.jpg",
    },
    "birthday_celebration_4_6": {
        "title_es": "Cuento de Cumpleaños 4-6 Años | Magic Memories Books",
        "title_en": "Birthday Book Ages 4-6 | Magic Memories Books",
        "desc_es": "El regalo más especial: un cuento donde tu hijo/a protagoniza su propia celebración mágica con ilustraciones IA.",
        "desc_en": "The most special birthday gift: your child stars in their own magical celebration. AI-generated illustrations.",
        "image": "og/og_birthday_celebration_4_6.jpg",
    },
    "birthday_celebration_7_9": {
        "title_es": "Cuento de Cumpleaños 7-9 Años | Magic Memories Books",
        "title_en": "Birthday Book Ages 7-9 | Magic Memories Books",
        "desc_es": "Cuento de cumpleaños único y personalizado para niños de 7-9 años. La aventura de su día especial contada con magia e IA.",
        "desc_en": "A unique personalized birthday story for kids 7-9. The adventure of their special day told with magic and AI illustrations.",
        "image": "og/og_birthday_celebration_7_9.jpg",
    },
    "dragon_garden_illustrated": {
        "title_es": "El Dragón del Jardín Mágico | Magic Memories Books",
        "title_en": "The Magic Garden Dragon | Magic Memories Books",
        "desc_es": "Libro hardcover con fotos reales de tu hijo/a. 22 ilustraciones con IA. Tu niño/a es el protagonista. Para niños 3-8.",
        "desc_en": "Hardcover book with real photos of your child. 22 unique AI illustrations. Your child as the hero. For kids 3-8.",
        "image": "og/og_dragon_garden_illustrated.jpg",
    },
    "magic_chef_illustrated": {
        "title_es": "El Chef Mágico | Magic Memories Books",
        "title_en": "The Magic Chef | Magic Memories Books",
        "desc_es": "Tu hijo/a como chef mágico en un libro ilustrado con fotos reales. 22 ilustraciones únicas con IA. Hardcover para niños 3-8.",
        "desc_en": "Your child as a magic chef in an illustrated book with real photos. 22 unique AI illustrations. Hardcover for kids 3-8.",
        "image": "og/og_magic_chef_illustrated.jpg",
    },
    "magic_inventor_illustrated": {
        "title_es": "El Taller de los Inventos Mágicos | Magic Memories Books",
        "title_en": "The Magic Inventor Workshop | Magic Memories Books",
        "desc_es": "Tu hijo/a como inventor genial en un libro ilustrado con fotos reales. 22 ilustraciones únicas con IA para niños de 6-8.",
        "desc_en": "Your child as a brilliant inventor in an illustrated book with real photos. 22 unique AI illustrations for kids 6-8.",
        "image": "og/og_magic_inventor_illustrated.jpg",
    },
    "star_keeper_illustrated": {
        "title_es": "El Guardián de Estrellas | Magic Memories Books",
        "title_en": "The Star Keeper | Magic Memories Books",
        "desc_es": "Tu hijo/a como guardián de estrellas en libro hardcover con fotos reales. 22 ilustraciones mágicas generadas con IA.",
        "desc_en": "Your child as keeper of the stars in a hardcover book with real photos. 22 magical AI-generated illustrations.",
        "image": "og/og_star_keeper_illustrated.jpg",
    },
    "furry_love_illustrated": {
        "title_es": "Tú y tu Amor Peludo | Magic Memories Books",
        "title_en": "You and Your Furry Love | Magic Memories Books",
        "desc_es": "Libro ilustrado del amor entre tú y tu mascota. Tu foto real en 22 escenas únicas generadas con IA. Impreso en hardcover.",
        "desc_en": "Illustrated book about you and your pet. Your real photo in 22 unique AI-generated scenes. Printed in hardcover.",
        "image": "og/og_furry_love_illustrated.jpg",
    },
    "furry_love_adventure_illustrated": {
        "title_es": "Amor Peludo: La Gran Aventura | Magic Memories Books",
        "title_en": "Furry Love: The Big Adventure | Magic Memories Books",
        "desc_es": "Vive una aventura junto a tu mascota con tu foto real en 22 ilustraciones generadas con IA. Impreso en hardcover.",
        "desc_en": "Live an adventure with your pet. Your real photo in 22 AI-generated scenes. Printed in hardcover.",
        "image": "og/og_furry_love_adventure_illustrated.jpg",
    },
    "furry_love_teen_illustrated": {
        "title_es": "Amor Peludo: Aventura Teen | Magic Memories Books",
        "title_en": "Furry Love: Teen Adventure | Magic Memories Books",
        "desc_es": "El regalo perfecto para adolescentes que aman a su mascota. Libro con foto real y 22 ilustraciones generadas con IA.",
        "desc_en": "The perfect gift for teens who love their pet. Personalized book with real photo and 22 AI-generated illustrations.",
        "image": "og/og_furry_love_teen_illustrated.jpg",
    },
    "centinela_aurora_illustrated": {
        "title_es": "El Centinela de la Aurora | Magic Memories Books",
        "title_en": "The Aurora Sentinel | Magic Memories Books",
        "desc_es": "Tu hijo/a como guardián en un mundo de auroras mágicas. Libro ilustrado con fotos reales y 19 ilustraciones únicas con IA.",
        "desc_en": "Your child as a guardian in a world of magical auroras. Illustrated book with real photos and 19 unique AI illustrations.",
        "image": "og/og_centinela_aurora_illustrated.jpg",
    },
    "furry_love_adult_illustrated": {
        "title_es": "Amor Peludo: Edición Adultos | Magic Memories Books",
        "title_en": "Furry Love: Adult Edition | Magic Memories Books",
        "desc_es": "Libro ilustrado para adultos que aman a su mascota. Tu foto real en cada una de las 22 ilustraciones generadas con IA.",
        "desc_en": "Personalized illustrated book for adults who love their pet. Your real photo in each of the 22 AI-generated illustrations.",
        "image": "og/og_furry_love_adult_illustrated.jpg",
    },
}

@app.route('/personalize-story')
def personalize_story():
    story_id = request.args.get('story', '')
    child_name = request.args.get('name', '')
    child_gender = request.args.get('gender', 'female')
    
    admin_gift_mode = request.args.get('admin_gift', '')
    if not story_id:
        return redirect(url_for('express_catalog'))
    if not child_name and admin_gift_mode:
        child_name = 'Regalo'
    
    template = get_story_template_by_id(story_id, child_name, child_gender)
    if not template:
        return redirect(url_for('story_selection', name=child_name, gender=child_gender))
    
    lang = get_lang()
    story_name = template['name_es'] if lang == 'es' else template['name_en']
    
    # Get story pages text for preview (both languages)
    from services.fixed_stories import STORIES
    story_pages = []
    story_config = STORIES.get(story_id, {})
    is_illustrated_book = story_config.get('use_fixed_scenes', False)
    page_count = story_config.get('page_count', 12)
    
    source_pages = story_config.get('content_pages', []) if is_illustrated_book else story_config.get('pages', [])
    text_layout = story_config.get('text_layout', 'single')
    for page in source_pages:
        if text_layout == 'split':
            above_es = page.get('text_above_es', '')
            below_es = page.get('text_below_es', '')
            above_en = page.get('text_above_en', '')
            below_en = page.get('text_below_en', '')
            text_es = (above_es + ' ' + below_es).strip().replace('{name}', '[NOMBRE]')
            text_en = (above_en + ' ' + below_en).strip().replace('{name}', '[NAME]')
        else:
            text_es = page.get('text_es', '').replace('{name}', '[NOMBRE]')
            text_en = page.get('text_en', '').replace('{name}', '[NAME]')
        import re
        text_es = re.sub(r'\{[a-z_]+\}', '', text_es)
        text_en = re.sub(r'\{[a-z_]+\}', '', text_en)
        story_pages.append({'text_es': text_es, 'text_en': text_en})
    
    age_range = story_config.get('age_range', '3-5')
    is_baby = age_range in ['0-1', '0-2']
    is_birthday = story_config.get('is_birthday', False)
    
    scene_count = len(story_config.get('pages', [])) if not is_illustrated_book else 0
    has_closing = 'closing_template' in story_config
    illustration_count = scene_count + (1 if has_closing else 0)
    
    admin_gift = request.args.get('admin_gift', '')

    og_meta = STORY_OG_META.get(story_id, {})
    og_title = og_meta.get('title_es' if lang == 'es' else 'title_en', story_name)
    og_description = og_meta.get('desc_es' if lang == 'es' else 'desc_en', '')
    og_image_file = og_meta.get('image', 'logo_main.jpg')
    og_image_url = f'https://magicmemoriesbooks.com/static/images/{og_image_file}'

    return render_template('personalize_story.html',
                          story_id=story_id,
                          story_name=story_name,
                          child_name=child_name,
                          child_gender=child_gender,
                          story_pages=story_pages,
                          is_illustrated_book=is_illustrated_book,
                          page_count=page_count,
                          is_baby=is_baby,
                          is_birthday=is_birthday,
                          age_range=age_range,
                          illustration_count=illustration_count,
                          admin_gift=admin_gift,
                          og_title=og_title,
                          og_description=og_description,
                          og_image_url=og_image_url)

@app.route('/story-preview/<preview_id>')
def story_preview(preview_id):
    """Redirect old route to the full preview page"""
    return redirect(url_for('story_preview_full', preview_id=preview_id))

@app.route('/checkout-story/<preview_id>')
def checkout_story(preview_id):
    """Legacy route - redirect to unified checkout"""
    return redirect(url_for('story_checkout', preview_id=preview_id))

@app.route('/checkout/<product>')
def checkout(product):
    """Legacy route - redirect to index"""
    return redirect(url_for('index'))

@app.route('/payment-success')
def payment_success():
    order_id = session.get('current_order_id')
    order = None
    if order_id:
        order = Order.query.get(order_id)
    return render_template('success.html', order=order)



@app.route('/haz-tu-historia')
def haz_tu_historia_terms():
    """Haz tu Historia V2 - Terms and conditions page (must accept before continuing)"""
    lang = request.args.get('lang', session.get('lang', 'es'))
    return render_template('haz_tu_historia/terms.html', lang=lang, translations=TRANSLATIONS.get(lang, TRANSLATIONS['es']))

@app.route('/haz-tu-historia/accept', methods=['POST'])
def haz_tu_historia_accept():
    """Haz tu Historia V2 - Accept terms and show form"""
    lang = request.form.get('language', 'es')
    session['haz_tu_historia_terms_accepted'] = True
    return render_template('haz_tu_historia/form.html', lang=lang, translations=TRANSLATIONS.get(lang, TRANSLATIONS['es']))

@app.route('/haz-tu-historia/form')
def haz_tu_historia_form():
    """Haz tu Historia V2 - Page 1: Author info, story description, dedication"""
    if not session.get('haz_tu_historia_terms_accepted'):
        return redirect(url_for('haz_tu_historia_terms'))
    lang = request.args.get('lang', session.get('lang', 'es'))
    return render_template('haz_tu_historia/form.html', lang=lang, translations=TRANSLATIONS.get(lang, TRANSLATIONS['es']))

@app.route('/haz-tu-historia/step2', methods=['GET', 'POST'])
def haz_tu_historia_step2():
    """Haz tu Historia V2 - Page 2: Character selection with visual form"""
    if request.method == 'GET':
        lang = request.args.get('lang', 'es')
        story_description = ''
        dedication = ''
        author_signature = ''
        author_name = ''
        author_email = ''
    else:
        lang = request.form.get('language', 'es')
        story_description = request.form.get('story_description', '')
        dedication = request.form.get('dedication', '')
        author_signature = request.form.get('author_signature', '')
        author_name = request.form.get('author_name', '')
        author_email = request.form.get('author_email', '')
    
    return render_template('haz_tu_historia/form_characters.html',
        lang=lang,
        translations=TRANSLATIONS.get(lang, TRANSLATIONS['es']),
        story_description=story_description,
        dedication=dedication,
        author_signature=author_signature,
        author_name=author_name,
        author_email=author_email
    )

@app.route('/haz-tu-historia/submit', methods=['POST'])
def haz_tu_historia_submit():
    """Process the visual character form and save to session"""
    from services.real_stories_v2.form_service import validate_story_request, Character, StoryRequest
    import uuid
    
    lang = request.form.get('language', 'es')
    
    characters = []
    
    char1_name = request.form.get('char1_name', '').strip()
    if char1_name:
        age_years = int(request.form.get('char1_age_years', 4))
        age_months = int(request.form.get('char1_age_months', 0))
        total_age = age_years + (age_months / 12.0)
        
        if total_age < 2:
            age_range = 'baby'
        elif total_age < 4:
            age_range = 'toddler'
        elif total_age < 8:
            age_range = 'child'
        elif total_age < 12:
            age_range = 'preteen'
        elif total_age < 18:
            age_range = 'teen'
        elif total_age < 30:
            age_range = 'young_adult'
        elif total_age < 50:
            age_range = 'adult'
        elif total_age < 65:
            age_range = 'middle_aged'
        else:
            age_range = 'senior'
        
        char1 = {
            'id': str(uuid.uuid4()),
            'name': char1_name,
            'character_type': 'human',
            'gender': request.form.get('char1_gender', 'female'),
            'age_years': age_years,
            'age_months': age_months,
            'age_range': age_range,
            'height': int(request.form.get('char1_height', 110)),
            'body_type': request.form.get('char1_body_type', 'average'),
            'skin_tone': request.form.get('char1_skin', 'light'),
            'hair_color': request.form.get('char1_hair_color', 'brown'),
            'hair_type': request.form.get('char1_hair_type', 'straight'),
            'hair_length': request.form.get('char1_hair_length', 'medium'),
            'eye_color': request.form.get('char1_eyes', 'brown'),
            'facial_hair': request.form.get('char1_facial_hair', 'none'),
            'clothing_style': request.form.get('char1_clothing', 'casual'),
            'accessories': request.form.get('char1_accessories', ''),
            'relationship': 'protagonist'
        }
        characters.append(char1)
    
    char_count = int(request.form.get('character_count', 1))
    if char_count == 2:
        char2_name = request.form.get('char2_name', '').strip()
        if char2_name:
            age_years = int(request.form.get('char2_age_years', 35))
            
            if age_years < 2:
                age_range2 = 'baby'
            elif age_years < 4:
                age_range2 = 'toddler'
            elif age_years < 8:
                age_range2 = 'child'
            elif age_years < 12:
                age_range2 = 'preteen'
            elif age_years < 18:
                age_range2 = 'teen'
            elif age_years < 30:
                age_range2 = 'young_adult'
            elif age_years < 50:
                age_range2 = 'adult'
            elif age_years < 65:
                age_range2 = 'middle_aged'
            else:
                age_range2 = 'senior'
            
            age_months2 = int(request.form.get('char2_age_months', 0))
            
            char2 = {
                'id': str(uuid.uuid4()),
                'name': char2_name,
                'character_type': 'human',
                'gender': request.form.get('char2_gender', 'female'),
                'age_years': age_years,
                'age_months': age_months2,
                'age_range': age_range2,
                'height': int(request.form.get('char2_height', 165)),
                'body_type': request.form.get('char2_body_type', 'average'),
                'skin_tone': request.form.get('char2_skin', 'light'),
                'hair_color': request.form.get('char2_hair_color', 'black'),
                'hair_type': request.form.get('char2_hair_type', 'straight'),
                'hair_length': request.form.get('char2_hair_length', 'medium'),
                'eye_color': request.form.get('char2_eyes', 'brown'),
                'facial_hair': request.form.get('char2_facial_hair', 'none'),
                'clothing_style': request.form.get('char2_clothing', 'casual'),
                'accessories': request.form.get('char2_accessories', ''),
                'relationship': request.form.get('char2_relationship', 'mother')
            }
            characters.append(char2)
    
    has_pet = request.form.get('has_pet') == '1'
    if has_pet:
        pet_name = request.form.get('pet_name', '').strip()
        if pet_name:
            pet_species = request.form.get('pet_species', 'dog')
            pet_breed = request.form.get(f'pet_{pet_species}_breed', 'mixed')
            
            pet = {
                'id': str(uuid.uuid4()),
                'name': pet_name,
                'character_type': 'pet',
                'pet_species': pet_species,
                'pet_breed': pet_breed,
                'pet_color': request.form.get('pet_color', 'golden'),
                'pet_pattern': request.form.get('pet_pattern', 'solid'),
                'pet_spot_color': request.form.get('pet_spot_color', 'white'),
                'pet_stripe_color': request.form.get('pet_stripe_color', 'black'),
                'pet_size': request.form.get('pet_size', 'medium'),
                'special_features': request.form.get('pet_features', ''),
                'relationship': 'pet'
            }
            characters.append(pet)
    
    story_data = {
        'id': str(uuid.uuid4()),
        'story_description': request.form.get('story_description', ''),
        'characters': characters,
        'language': lang,
        'dedication': request.form.get('dedication', ''),
        'author_signature': request.form.get('author_signature', ''),
        'author_name': request.form.get('author_name', ''),
        'author_email': request.form.get('author_email', '')
    }
    
    is_valid, error_msg = validate_story_request(story_data)
    if not is_valid:
        flash(error_msg, 'error')
        return redirect(url_for('haz_tu_historia_form'))
    
    from services.moderation_service import moderate_story_request
    is_safe, moderation_error = moderate_story_request(story_data)
    if not is_safe:
        flash(moderation_error, 'error')
        return redirect(url_for('haz_tu_historia_form'))
    
    session['haz_tu_historia'] = story_data
    
    return redirect(url_for('haz_tu_historia_portraits'))

@app.route('/haz-tu-historia/portraits')
def haz_tu_historia_portraits():
    """Show character portraits for approval"""
    from services.real_stories_v2.form_service import build_character_description, Character
    
    if 'haz_tu_historia' not in session:
        return redirect(url_for('haz_tu_historia_form'))
    
    story_data = session['haz_tu_historia']
    lang = story_data.get('language', 'es')
    
    characters_for_template = []
    for char_data in story_data.get('characters', []):
        char = Character.from_dict(char_data)
        description = build_character_description(char, lang)
        
        char_data['description'] = description
        char_data['portrait_path'] = session.get(f"portrait_{char_data['id']}")
        characters_for_template.append(char_data)
    
    return render_template('haz_tu_historia/portraits.html', 
                          lang=lang, 
                          translations=TRANSLATIONS.get(lang, TRANSLATIONS['es']),
                          characters=characters_for_template)

@app.route('/haz-tu-historia/regenerate-portrait', methods=['POST'])
def haz_tu_historia_regenerate_portrait():
    """Regenerate a character portrait"""
    from services.real_stories_v2.form_service import build_character_description, Character
    from services.real_stories_v2.image_service import generate_character_portrait
    
    if 'haz_tu_historia' not in session:
        return jsonify({'success': False, 'error': 'Session expired'})
    
    data = request.get_json()
    char_id = data.get('character_id')
    
    story_data = session['haz_tu_historia']
    lang = story_data.get('language', 'es')
    
    char_data = None
    for c in story_data.get('characters', []):
        if c['id'] == char_id:
            char_data = c
            break
    
    if not char_data:
        return jsonify({'success': False, 'error': 'Character not found'})
    
    char = Character.from_dict(char_data)
    description = build_character_description(char, 'en')
    
    result = generate_character_portrait(description)
    
    if result['success']:
        session[f"portrait_{char_id}"] = result['image_path']
        session.modified = True
        return jsonify({'success': True, 'portrait_path': result['image_path']})
    else:
        return jsonify({'success': False, 'error': result.get('error', 'Generation failed')})

@app.route('/haz-tu-historia/text-preview')
def haz_tu_historia_text_preview():
    """Show text preview with book typography"""
    if 'haz_tu_historia' not in session:
        return redirect(url_for('haz_tu_historia_form'))
    
    story_data = session['haz_tu_historia']
    lang = story_data.get('language', 'es')
    
    # Check if force regenerate is requested
    force_regenerate = request.args.get('regenerate', '0') == '1'
    story_id = get_or_create_story_id()
    
    if force_regenerate:
        filepath = os.path.join(STORY_STORAGE_DIR, f"{story_id}.json")
        if os.path.exists(filepath):
            os.remove(filepath)
    
    story_text = load_story_from_file(story_id)
    
    return render_template('haz_tu_historia/text_preview.html',
                          lang=lang,
                          translations=TRANSLATIONS.get(lang, TRANSLATIONS['es']),
                          story_data=story_data,
                          story_text=story_text)

@app.route('/haz-tu-historia/generate-text', methods=['POST'])
def haz_tu_historia_generate_text():
    """Generate the story text using GPT-4o"""
    from services.real_stories_v2.story_service import generate_story
    
    if 'haz_tu_historia' not in session:
        return jsonify({'success': False, 'error': 'Session expired'})
    
    story_data = session['haz_tu_historia']
    lang = story_data.get('language', 'es')
    
    result = generate_story(
        story_description=story_data.get('story_description', ''),
        characters=story_data.get('characters', []),
        language=lang
    )
    
    if result['success']:
        story_id = get_or_create_story_id()
        story_content = {
            'title': result['title'],
            'acts': result['acts'],
            'moral': result.get('moral', '')
        }
        save_story_to_file(story_id, story_content)
        return jsonify({'success': True, 'story': story_content})
    else:
        return jsonify({'success': False, 'error': result.get('error', 'Generation failed')})

@app.route('/haz-tu-historia/regenerate-act', methods=['POST'])
def haz_tu_historia_regenerate_act():
    """Regenerate a specific act"""
    from services.real_stories_v2.story_service import regenerate_act
    
    if 'haz_tu_historia' not in session:
        return jsonify({'success': False, 'error': 'Session expired'})
    
    story_id = get_or_create_story_id()
    story_text = load_story_from_file(story_id)
    
    if not story_text:
        return jsonify({'success': False, 'error': 'Story not found'})
    
    data = request.get_json()
    act_number = data.get('act_number')
    feedback = data.get('feedback', '')
    
    story_data = session['haz_tu_historia']
    lang = story_data.get('language', 'es')
    
    result = regenerate_act(
        current_acts=story_text['acts'],
        act_number=act_number,
        characters=story_data.get('characters', []),
        story_description=story_data.get('story_description', ''),
        language=lang,
        feedback=feedback
    )
    
    if result['success']:
        for act in story_text['acts']:
            if act['act'] == act_number:
                act['text'] = result['new_text']
                break
        save_story_to_file(story_id, story_text)
        return jsonify({'success': True, 'new_text': result['new_text']})
    else:
        return jsonify({'success': False, 'error': result.get('error', 'Regeneration failed')})

@app.route('/haz-tu-historia/illustrations')
def haz_tu_historia_illustrations():
    """Show illustrations preview page"""
    if 'haz_tu_historia' not in session:
        return redirect(url_for('haz_tu_historia_form'))
    
    story_id = get_or_create_story_id()
    story_text = load_story_from_file(story_id)
    
    if not story_text:
        return redirect(url_for('haz_tu_historia_text_preview'))
    
    story_data = session['haz_tu_historia']
    lang = story_data.get('language', 'es')
    
    return render_template('haz_tu_historia/illustrations.html',
                          lang=lang,
                          translations=TRANSLATIONS.get(lang, TRANSLATIONS['es']),
                          story_data=story_data,
                          story_text=story_text)

@app.route('/haz-tu-historia/generate-illustration', methods=['POST'])
def haz_tu_historia_generate_illustration():
    """Generate illustration for a specific act with full character DNA"""
    from services.real_stories_v2.image_service import generate_scene_illustration
    
    if 'haz_tu_historia' not in session:
        return jsonify({'success': False, 'error': 'Session expired'})
    
    story_id = get_or_create_story_id()
    story_text = load_story_from_file(story_id)
    
    if not story_text:
        return jsonify({'success': False, 'error': 'Story not found'})
    
    data = request.get_json()
    act_number = data.get('act_number')
    
    story_data = session['haz_tu_historia']
    characters = story_data.get('characters', [])
    
    visual_summary = None
    for act in story_text['acts']:
        if act['act'] == act_number:
            visual_summary = act.get('visual_summary', '')
            if not visual_summary:
                visual_summary = act['text'][:100]
            break
    
    if not visual_summary:
        return jsonify({'success': False, 'error': 'Act not found'})
    
    scene_prompt = visual_summary
    
    result = generate_scene_illustration(scene_prompt, characters)
    
    if result['success']:
        if 'haz_tu_historia_illustrations' not in session:
            session['haz_tu_historia_illustrations'] = {}
        session['haz_tu_historia_illustrations'][str(act_number)] = result['image_path']
        session.modified = True
        return jsonify({'success': True, 'image_path': result['image_path']})
    else:
        return jsonify({'success': False, 'error': result.get('error', 'Generation failed')})

@app.route('/haz-tu-historia/generate-closing', methods=['POST'])
def haz_tu_historia_generate_closing():
    """Generate closing illustration (Climax or Resolution)"""
    from services.real_stories_v2.image_service import generate_closing_illustrations
    
    if 'haz_tu_historia' not in session:
        return jsonify({'success': False, 'error': 'Session expired'})
    
    data = request.get_json()
    closing_number = data.get('closing_number', 1)
    
    story_data = session['haz_tu_historia']
    
    # Pass full character dicts for DNA building
    characters = story_data.get('characters', [])
    
    results = generate_closing_illustrations(characters)
    
    if results and len(results) >= closing_number:
        result = results[closing_number - 1]
        if result['success']:
            return jsonify({'success': True, 'image_path': result['image_path']})
    
    return jsonify({'success': False, 'error': 'Generation failed'})

@app.route('/haz-tu-historia/generate-cover', methods=['POST'])
def haz_tu_historia_generate_cover():
    """Generate book cover with Movie Poster style"""
    from services.real_stories_v2.image_service import generate_cover_image
    
    if 'haz_tu_historia' not in session:
        return jsonify({'success': False, 'error': 'Session expired'})
    
    story_id = get_or_create_story_id()
    story_text = load_story_from_file(story_id) or {}
    
    story_data = session['haz_tu_historia']
    
    # Pass full character dicts for DNA building
    characters = story_data.get('characters', [])
    
    result = generate_cover_image(story_text.get('title', ''), characters)
    
    if result['success']:
        session['haz_tu_historia_cover'] = result['image_path']
        session.modified = True
        return jsonify({'success': True, 'image_path': result['image_path']})
    else:
        return jsonify({'success': False, 'error': result.get('error', 'Generation failed')})

@app.route('/haz-tu-historia/generate-back-cover', methods=['POST'])
def haz_tu_historia_generate_back_cover():
    """Generate back cover - landscape only, no people"""
    from services.real_stories_v2.image_service import generate_back_cover
    
    if 'haz_tu_historia' not in session:
        return jsonify({'success': False, 'error': 'Session expired'})
    
    story_id = get_or_create_story_id()
    story_text = load_story_from_file(story_id) or {}
    
    # Use story setting or extract from story description
    story_data = session['haz_tu_historia']
    scenario = story_data.get('story_description', 'magical forest at sunset')
    result = generate_back_cover(scenario)
    
    if result['success']:
        session['haz_tu_historia_back_cover'] = result['image_path']
        session.modified = True
        return jsonify({'success': True, 'image_path': result['image_path']})
    else:
        return jsonify({'success': False, 'error': result.get('error', 'Generation failed')})

@app.route('/haz-tu-historia/shipping')
def haz_tu_historia_shipping():
    """Shipping address form"""
    if 'haz_tu_historia' not in session:
        return redirect(url_for('haz_tu_historia_form'))
    
    story_data = session['haz_tu_historia']
    lang = story_data.get('language', 'es')
    
    return render_template('haz_tu_historia/shipping.html',
                          lang=lang,
                          translations=TRANSLATIONS.get(lang, TRANSLATIONS['es']),
                          story_data=story_data)

@app.route('/haz-tu-historia/checkout', methods=['POST'])
def haz_tu_historia_checkout():
    """Process shipping and proceed to payment"""
    if 'haz_tu_historia' not in session:
        return jsonify({'success': False, 'error': 'Session expired'})
    
    story_data = session['haz_tu_historia']
    
    shipping_data = {
        'name': request.form.get('shipping_name'),
        'email': request.form.get('email'),
        'address_line1': request.form.get('address_line1'),
        'address_line2': request.form.get('address_line2', ''),
        'city': request.form.get('city'),
        'state': request.form.get('state'),
        'postal_code': request.form.get('postal_code'),
        'country': request.form.get('country')
    }
    
    session['haz_tu_historia_shipping'] = shipping_data
    session.modified = True
    
    return jsonify({
        'success': True,
        'redirect': url_for('haz_tu_historia_payment')
    })

@app.route('/haz-tu-historia/payment')
def haz_tu_historia_payment():
    """Payment page with PayPal"""
    if 'haz_tu_historia' not in session or 'haz_tu_historia_shipping' not in session:
        return redirect(url_for('haz_tu_historia_form'))
    
    story_data = session['haz_tu_historia']
    shipping_data = session['haz_tu_historia_shipping']
    lang = story_data.get('language', 'es')
    
    return render_template('haz_tu_historia/payment.html',
                          lang=lang,
                          translations=TRANSLATIONS.get(lang, TRANSLATIONS['es']),
                          story_data=story_data,
                          shipping_data=shipping_data,
                          paypal_client_id=Config.PAYPAL_CLIENT_ID,
                          personalized_base_price=Config.PERSONALIZED_BASE_PRICE / 100.0)

@app.route('/haz-tu-historia/success')
def haz_tu_historia_success():
    """Success page after payment"""
    transaction_id = request.args.get('transaction_id')
    
    story_data = session.get('haz_tu_historia', {})
    lang = story_data.get('language', 'es')
    
    pdf_url = session.get('haz_tu_historia_pdf_url')
    
    return render_template('haz_tu_historia/success.html',
                          lang=lang,
                          translations=TRANSLATIONS.get(lang, TRANSLATIONS['es']),
                          transaction_id=transaction_id,
                          pdf_url=pdf_url)


@app.route('/api/create-order', methods=['POST'])
def create_order():
    if 'pending_order' not in session:
        return jsonify({'error': 'No pending order'}), 400
    
    order_data = session['pending_order']
    order_number = f"MMB-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
    
    price = Config.PRODUCT_A_PRICE if order_data['product_type'] == 'quick_story' else Config.PRODUCT_B_PRICE
    
    order = Order(
        order_number=order_number,
        product_type=order_data['product_type'],
        child_name=order_data['child_name'],
        child_gender=order_data['child_gender'],
        child_age_range=order_data['child_age_range'],
        hair_color=order_data.get('hair_color'),
        hair_type=order_data.get('hair_type'),
        eye_color=order_data.get('eye_color'),
        skin_tone=order_data.get('skin_tone'),
        story_template=order_data.get('story_template'),
        custom_story_description=order_data.get('custom_story_description'),
        photos=order_data.get('photos'),
        customer_email=order_data['customer_email'],
        customer_name=order_data.get('customer_name'),
        terms_accepted=order_data.get('terms_accepted', False),
        photo_consent=order_data.get('photo_consent', False),
        language=order_data.get('language', 'es'),
        amount_paid=price,
        status='paid'
    )
    
    db.session.add(order)
    db.session.commit()
    
    session['current_order_id'] = order.id
    session.pop('pending_order', None)
    
    return jsonify({'success': True, 'order_number': order_number, 'order_id': order.id})

@app.route('/api/generate-story/<int:order_id>', methods=['POST'])
def generate_story(order_id):
    order = Order.query.get_or_404(order_id)
    
    if order.status == 'completed':
        return jsonify({'success': True, 'message': 'Story already generated'})
    
    try:
        from services.ai_service import generate_story_text
        from services.pdf_service import create_digital_pdf, create_print_pdf
        
        story_template_name = None
        if order.story_template:
            for template in STORY_TEMPLATES:
                if template['id'] == order.story_template:
                    story_template_name = template['name_en'] if order.language == 'en' else template['name_es']
                    break
        
        story_text = generate_story_text(order, story_template_name)
        
        digital_filename = f"{order.order_number}_digital.pdf"
        print_filename = f"{order.order_number}_print.pdf"
        
        digital_path = os.path.join(app.config['GENERATED_FOLDER'], digital_filename)
        print_path = os.path.join(app.config['GENERATED_FOLDER'], print_filename)
        
        create_digital_pdf(order, story_text, [], digital_path)
        create_print_pdf(order, story_text, [], print_path)
        
        order.digital_pdf_path = digital_filename
        order.print_pdf_path = print_filename
        order.status = 'completed'
        order.completed_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'digital_pdf': digital_filename,
            'print_pdf': print_filename
        })
    except Exception as e:
        order.status = 'error'
        db.session.commit()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['GENERATED_FOLDER'], filename, as_attachment=True)


@app.route('/preview-pdf/printable/<session_id>/<filename>')
def preview_printable_pdf(session_id, filename):
    """Serve a printable PDF file for browser preview (personalized_pdf orders)."""
    import re
    if not re.match(r'^[a-zA-Z0-9_\-]+$', session_id):
        abort(400)
    if not filename.endswith('.pdf') or '/' in filename or '..' in filename:
        abort(400)
    pdf_path = os.path.join('generated', 'cloudprinter', session_id, filename)
    if not os.path.exists(pdf_path):
        abort(404)
    return send_file(os.path.abspath(pdf_path), mimetype='application/pdf')



@app.route('/webhooks/cloudprinter', methods=['POST'])
def cloudprinter_webhook():
    """
    Receive Cloudprinter order status signals (webhooks).
    Configure in app.cloudprinter.com → Development → Signals → Webhooks
    Protocol: HTTPS, Endpoint: magicmemoriesbooks.com/webhooks/cloudprinter
    """
    try:
        data = request.get_json(force=True) or {}
    except Exception:
        return jsonify({'error': 'invalid JSON'}), 400

    webhook_secret = os.environ.get('CLOUDPRINTER_WEBHOOK_API_KEY', '')
    if webhook_secret:
        incoming_key = (
            request.headers.get('X-Cloudsignal-Apikey') or
            request.headers.get('X-Api-Key') or
            data.get('apikey', '')
        )
        if incoming_key != webhook_secret:
            print(f'[CP WEBHOOK] Invalid API key — rejected (got: {incoming_key[:8]}...)')
            return jsonify({'error': 'unauthorized'}), 401

    # CP sends reference in 'order_reference' or 'reference'
    reference  = data.get('order_reference', data.get('reference', ''))
    state_code = data.get('state_code', data.get('state', ''))
    state_num  = data.get('status', data.get('state_num', ''))
    # CP sends the event type in 'type' field
    event_type = data.get('type', data.get('event_type', data.get('event', '')))
    print(f'[CP WEBHOOK] reference={reference} event_type={event_type} state={state_code}({state_num}) payload={str(data)[:300]}')

    try:
        from services.email_service import send_admin_notification_email

        shipped_events  = ('ItemShipped', 'ItemDeliveryStarted',
                           'order_state_distributed', 'order_state_shipped', 'order_state_in_transit',
                           'CloudprinterOrderShipped', 'order_shipped')
        delivered_events = ('ItemDeliveryCompleted', 'order_state_delivered',
                            'CloudprinterOrderDelivered', 'order_delivered')
        problem_events  = ('ItemError', 'ItemCanceled', 'CloudprinterOrderCanceled',
                           'ItemDeliveryFailed', 'order_state_error', 'order_state_canceled',
                           'order_state_payment_error', 'order_state_on_hold')

        tracking_code = data.get('trackingCode', data.get('tracking_code', ''))
        tracking_url  = data.get('trackingUrl',  data.get('tracking_url', ''))
        if not tracking_code:
            items = data.get('items', [])
            if items and isinstance(items, list):
                t = items[0].get('tracking', {})
                if isinstance(t, dict):
                    tracking_code = t.get('code', '')
                    tracking_url  = t.get('url', '')
                else:
                    tracking_code = t or ''

        event_key = event_type or state_code

        if event_key in shipped_events:
            tracking_line = f'  Tracking: {tracking_code}\n  URL: {tracking_url}\n' if tracking_code else ''
            subject = f'[Cloudprinter] Pedido enviado — {reference}'
            body = (
                f'Un pedido de Cloudprinter ha sido despachado:\n\n'
                f'  Referencia: {reference}\n'
                f'  Evento: {event_key}\n'
                f'{tracking_line}'
                f'\nRevisa app.cloudprinter.com para más detalles.'
            )
            send_admin_notification_email(subject=subject, body=body)
            print(f'[CP WEBHOOK] Admin shipping notification sent for {reference}')

            if tracking_code:
                try:
                    from services.email_service import send_cp_tracking_email
                    parts = reference.split('-')
                    preview_prefix = parts[1] if len(parts) >= 2 else ''
                    story_data = None
                    story_file = None
                    if preview_prefix:
                        import glob as _glob
                        matches = _glob.glob(f'story_previews/{preview_prefix}*.json')
                        if matches:
                            story_file = matches[0]
                            with open(story_file, 'r', encoding='utf-8') as _f:
                                story_data = json.load(_f)
                    if story_data:
                        # Persist tracking info into the story JSON so track-order page shows it without API call
                        story_data['cp_tracking_code'] = tracking_code
                        story_data['cp_tracking_url'] = tracking_url
                        story_data['cp_order_status'] = 'shipped'
                        story_data['cp_shipped_at'] = data.get('timestamp', '')
                        if story_file:
                            with open(story_file, 'w', encoding='utf-8') as _fw:
                                json.dump(story_data, _fw, ensure_ascii=False, indent=2)
                            print(f'[CP WEBHOOK] Tracking saved to {story_file}')
                        customer_email = story_data.get('customer_email', '')
                        child_name = story_data.get('child_name', '')
                        story_name = story_data.get('story_name', story_data.get('title', 'Tu Cuento Mágico'))
                        lang = story_data.get('lang', story_data.get('language', 'es'))
                        shipping_address = story_data.get('shipping_address', {})
                        if customer_email:
                            sent = send_cp_tracking_email(
                                to_email=customer_email,
                                child_name=child_name,
                                book_title=story_name,
                                tracking_code=tracking_code,
                                tracking_url=tracking_url,
                                shipping_address=shipping_address,
                                lang=lang
                            )
                            print(f'[CP WEBHOOK] Customer tracking email sent={sent} to {customer_email}')
                        else:
                            print(f'[CP WEBHOOK] No customer email found in story for {reference}')
                    else:
                        print(f'[CP WEBHOOK] Story not found for prefix={preview_prefix}')
                except Exception as track_err:
                    print(f'[CP WEBHOOK] Error sending customer tracking email: {track_err}')

        elif event_key in delivered_events:
            subject = f'[Cloudprinter] Pedido entregado — {reference}'
            body = (
                f'Un pedido de Cloudprinter ha sido entregado:\n\n'
                f'  Referencia: {reference}\n'
                f'  Evento: {event_key}\n\n'
                f'El cliente ha recibido su cuento.'
            )
            send_admin_notification_email(subject=subject, body=body)
            print(f'[CP WEBHOOK] Delivery notification sent for {reference}')

        elif event_key in problem_events:
            subject = f'[Cloudprinter] PROBLEMA en pedido — {reference}'
            body = (
                f'Un pedido de Cloudprinter tiene un problema:\n\n'
                f'  Referencia: {reference}\n'
                f'  Evento: {event_key}\n'
                f'  Datos: {str(data)[:500]}\n\n'
                f'Revisa app.cloudprinter.com urgentemente.'
            )
            send_admin_notification_email(subject=subject, body=body)
            print(f'[CP WEBHOOK] Problem notification sent for {reference}')

    except Exception as e:
        print(f'[CP WEBHOOK] Notification error: {e}')

    return jsonify({'received': True}), 200


@app.route('/api/orders')
def list_orders():
    orders = Order.query.order_by(Order.created_at.desc()).limit(50).all()
    return jsonify([{
        'id': o.id,
        'order_number': o.order_number,
        'child_name': o.child_name,
        'product_type': o.product_type,
        'status': o.status,
        'customer_email': o.customer_email,
        'created_at': o.created_at.isoformat() if o.created_at else None,
        'digital_pdf': o.digital_pdf_path,
        'print_pdf': o.print_pdf_path
    } for o in orders])

@app.route('/api/generate-character-preview', methods=['POST'])
def generate_character_preview_api():
    try:
        data = request.get_json()
        
        child_name = data.get('child_name')
        child_gender = data.get('child_gender')
        child_age = data.get('child_age', '5')
        hair_color = data.get('hair_color')
        hair_type = data.get('hair_type')
        hair_length = data.get('hair_length', 'medium')
        eye_color = data.get('eye_color')
        skin_tone = data.get('skin_tone')
        story_template = data.get('story_template')
        
        if not all([child_name, child_gender, hair_color, hair_type, eye_color, skin_tone]):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        traits = {
            'hair_color': hair_color,
            'hair_type': hair_type,
            'hair_length': hair_length,
            'eye_color': eye_color,
            'skin_tone': skin_tone,
            'child_age': child_age,
            'glasses': data.get('glasses', '')
        }
        
        story_theme = story_template if story_template else 'magical_adventure'
        
        from services.fixed_stories import STORIES
        story_config = STORIES.get(story_template, {})
        age_range = story_config.get('age_range', child_age if child_age else '5')
        
        if story_template in STORIES:
            from services.replicate_service import generate_base_character
            import os
            import time
            
            preview_dir = f"generated/previews/{child_name}_{story_template}_{int(time.time())}"
            os.makedirs(preview_dir, exist_ok=True)
            
            image_path = generate_base_character(
                traits=traits,
                output_dir=preview_dir,
                gender=child_gender,
                age_range=age_range,
                story_id=story_template
            )
            
            image_url = f"/{image_path}"
        else:
            from services.ai_service import generate_character_portrait
            image_url = generate_character_portrait(child_name, child_gender, traits, story_theme)
        
        return jsonify({
            'success': True,
            'image_url': image_url
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/generate-full-story', methods=['POST'])
def generate_full_story_api():
    try:
        data = request.get_json()
        
        child_name = data.get('child_name')
        child_gender = data.get('child_gender')
        child_age_range = data.get('child_age_range')
        hair_color = data.get('hair_color')
        hair_type = data.get('hair_type')
        hair_length = data.get('hair_length', 'medium')
        eye_color = data.get('eye_color')
        skin_tone = data.get('skin_tone')
        story_template = data.get('story_template')
        story_name = data.get('story_name')
        dedication = data.get('dedication')
        author_name = data.get('author_name')
        story_lang = data.get('story_lang', get_lang())
        character_image = data.get('character_image')
        
        from services.ai_service import generate_full_story_with_illustrations
        
        traits = {
            'hair_color': hair_color,
            'hair_type': hair_type,
            'hair_length': hair_length,
            'eye_color': eye_color,
            'skin_tone': skin_tone
        }
        
        template = get_story_template_by_id(story_template)
        story_theme = story_template if story_template else 'magical_adventure'
        
        result = generate_full_story_with_illustrations(
            child_name=child_name,
            child_gender=child_gender,
            child_age_range=child_age_range,
            traits=traits,
            story_theme=story_theme,
            lang=story_lang
        )
        
        preview_id = uuid.uuid4().hex[:12]
        
        story_data = {
            'child_name': child_name,
            'child_gender': child_gender,
            'child_age_range': child_age_range,
            'traits': traits,
            'story_template': story_template,
            'story_name': story_name,
            'story_theme': story_theme,
            'dedication': dedication,
            'author_name': author_name,
            'story_lang': story_lang,
            'story_text': result['story_text'],
            'illustrations': result['illustrations'],
            'character_image': character_image,
            'created_at': datetime.utcnow().isoformat()
        }
        
        with open(f'story_previews/{preview_id}.json', 'w', encoding='utf-8') as f:
            json.dump(story_data, f, ensure_ascii=False, indent=2)
        
        return jsonify({
            'success': True,
            'preview_id': preview_id
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


STORY_EVENTS_FILE = os.path.join('data', 'story_events.jsonl')


@app.route('/api/story-open', methods=['POST'])
def api_story_open():
    """Record FIRST_STORY_OPEN event — called by visor on first load, fire-and-forget."""
    data = request.get_json(silent=True) or {}
    preview_id = (data.get('preview_id') or '').strip()
    story_type = (data.get('story_type') or 'qs').strip()
    if not preview_id:
        return jsonify({'ok': False}), 400
    if os.path.exists(STORY_EVENTS_FILE):
        with open(STORY_EVENTS_FILE, 'r', encoding='utf-8') as _f:
            for _line in _f:
                try:
                    _ev = json.loads(_line)
                    if _ev.get('event_type') == 'FIRST_STORY_OPEN' and _ev.get('preview_id') == preview_id:
                        return jsonify({'ok': True, 'already': True})
                except Exception:
                    continue
    customer_email = ''
    _sj = os.path.join('story_previews', f'{preview_id}.json')
    if os.path.exists(_sj):
        try:
            with open(_sj, 'r', encoding='utf-8') as _f:
                _sd = json.load(_f)
            customer_email = (_sd.get('customer_email') or '').strip().lower()
        except Exception:
            pass
    event = {
        'event_type': 'FIRST_STORY_OPEN',
        'preview_id': preview_id,
        'customer_email': customer_email,
        'story_type': story_type,
        'ts': datetime.utcnow().isoformat(),
        'ip': request.remote_addr or '',
    }
    os.makedirs('data', exist_ok=True)
    with open(STORY_EVENTS_FILE, 'a', encoding='utf-8') as _f:
        _f.write(json.dumps(event) + '\n')
    return jsonify({'ok': True})


@app.route('/api/story-completed', methods=['POST'])
def api_story_completed():
    """Record STORY_COMPLETED event — called by visor when user reaches last page for first time."""
    data = request.get_json(silent=True) or {}
    preview_id = (data.get('preview_id') or '').strip()
    story_type = (data.get('story_type') or 'qs').strip()
    if not preview_id:
        return jsonify({'ok': False}), 400
    if os.path.exists(STORY_EVENTS_FILE):
        with open(STORY_EVENTS_FILE, 'r', encoding='utf-8') as _f:
            for _line in _f:
                try:
                    _ev = json.loads(_line)
                    if _ev.get('event_type') == 'STORY_COMPLETED' and _ev.get('preview_id') == preview_id:
                        return jsonify({'ok': True, 'already': True})
                except Exception:
                    continue
    customer_email = ''
    _sj = os.path.join('story_previews', f'{preview_id}.json')
    if os.path.exists(_sj):
        try:
            with open(_sj, 'r', encoding='utf-8') as _f:
                _sd = json.load(_f)
            customer_email = (_sd.get('customer_email') or '').strip().lower()
        except Exception:
            pass
    event = {
        'event_type': 'STORY_COMPLETED',
        'preview_id': preview_id,
        'customer_email': customer_email,
        'story_type': story_type,
        'ts': datetime.utcnow().isoformat(),
        'ip': request.remote_addr or '',
    }
    os.makedirs('data', exist_ok=True)
    with open(STORY_EVENTS_FILE, 'a', encoding='utf-8') as _f:
        _f.write(json.dumps(event) + '\n')
    return jsonify({'ok': True})


@app.route('/api/reserve-gen-token', methods=['POST'])
def reserve_gen_token():
    """Pre-register a generation token so the browser can persist it BEFORE the long Kontext+FLUX call."""
    try:
        data = request.get_json(force=True) or {}
        client_ip = get_client_ip()
        story_id = data.get('story_id', '').strip()
        if not story_id:
            return jsonify({'success': False, 'error': 'missing story_id'}), 400
        gen_key = f"{client_ip}:{story_id}"
        with _active_gen_lock:
            if gen_key in _active_generations:
                existing_token = _active_generations[gen_key]['token']
                return jsonify({'success': True, 'gen_token': existing_token, 'already_running': True})
        gen_token = uuid.uuid4().hex[:12]
        _save_gen_state(gen_token, 'pending')
        return jsonify({'success': True, 'gen_token': gen_token, 'already_running': False})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/generate-baby-preview', methods=['POST'])
def generate_baby_preview_api():
    """Generate character preview with FLUX via Replicate (supports baby and kids)"""
    _ctx = {}
    try:
        try:
            data = request.get_json(force=True)
            if data is None:
                raise ValueError("empty body")
        except Exception:
            from werkzeug.exceptions import ClientDisconnected
            client_ip = get_client_ip()
            matching_token = None
            with _active_gen_lock:
                for key, info in _active_generations.items():
                    if key.startswith(client_ip + ':'):
                        matching_token = info.get('token')
                        break
            if matching_token:
                return jsonify({'success': False, 'error': 'generating_in_progress', 'gen_token': matching_token}), 200
            return jsonify({'success': False, 'error': 'bad_request'}), 400

        if not data.get('admin_gift'):
            client_ip = get_client_ip()
            user_email = data.get('user_email', '').strip()
            story_id   = data.get('story_id', '')
            allowed, reason = check_generation_allowed(user_email, story_id, client_ip)
            if not allowed:
                return jsonify({'success': False, 'error': 'rate_limited', 'rate_limited': True, 'reason': reason}), 429
            pre_token = data.get('pre_token', '').strip()
            gen_token = pre_token if (pre_token and len(pre_token) == 12 and pre_token.isalnum()) else uuid.uuid4().hex[:12]
            gen_key = f"{client_ip}:{story_id}"
            with _active_gen_lock:
                if gen_key in _active_generations:
                    existing_token = _active_generations[gen_key]['token']
                    return jsonify({'success': False, 'error': 'generating_in_progress', 'gen_token': existing_token})
                _active_generations[gen_key] = {'token': gen_token, 'started': time.time()}
                _ctx['gen_key'] = gen_key
            _ctx['gen_token'] = gen_token
            _save_gen_state(gen_token, 'generating')
            save_preview_lead(user_email, client_ip, story_id)
        else:
            gen_token = uuid.uuid4().hex[:12]
            _ctx['gen_token'] = gen_token

        from services.replicate_service import generate_illustration_replicate, save_image_locally, get_unified_skin_description, get_gender_negative_prompt, FLUX_DEV_MODEL, FLUX_2_DEV_MODEL
        from services.fixed_stories import get_hair_description, get_eye_description, get_skin_tone, get_gender_child, STORIES
        
        child_name = data.get('child_name', 'Child')
        child_gender = data.get('gender', 'neutral')
        story_id = data.get('story_id', '')
        story_age_range = STORIES.get(story_id, {}).get('age_range', '0-1') if story_id else '0-1'
        default_age = '5' if story_age_range in ['3-5', '3-8', '5-7', '5-8', '6-7', '6-8'] else '1'
        child_age = int(data.get('child_age', default_age))
        traits = {
            'hair_color': data.get('hair_color', 'brown'),
            'hair_type': data.get('hair_type', 'straight'),
            'hair_length': data.get('hair_length', 'medium'),
            'eye_color': data.get('eye_color', 'brown'),
            'skin_tone': data.get('skin_tone', 'light'),
            'child_age': str(child_age),
            'gender': child_gender,
            'glasses': data.get('glasses', ''),
            'hairstyle': data.get('hairstyle', '')
        }
        from services.quick_stories.checkout import ALL_QUICK_FAMILY_IDS
        
        story_config = STORIES.get(story_id, {})
        age_range = story_config.get('age_range', '0-1')
        is_baby = age_range in ['0-1', '0-2']
        is_quick_story = story_id in ALL_QUICK_FAMILY_IDS
        _child_photo_raw = data.get('child_photo_path', '')
        _upload_prefix = 'generated/uploads/furry_photos/'
        child_photo_path = _child_photo_raw if (_child_photo_raw and _child_photo_raw.startswith(_upload_prefix) and os.path.exists(_child_photo_raw)) else ''
        _reuse_portrait_raw = data.get('reuse_portrait_path', '')
        _preview_prefix = 'generated/previews/'
        reuse_portrait_path = _reuse_portrait_raw if (_reuse_portrait_raw and _reuse_portrait_raw.startswith(_preview_prefix) and os.path.exists(_reuse_portrait_raw)) else ''
        if reuse_portrait_path:
            traits['reuse_portrait_path'] = reuse_portrait_path
        
        if is_baby:
            traits['is_baby_story'] = True
        
        hair_desc = get_hair_description(traits)
        eye_desc = get_eye_description(traits)
        skin_desc = get_unified_skin_description(traits.get('skin_tone', 'light'))
        
        if story_id in ('furry_love_illustrated', 'furry_love_adventure_illustrated', 'furry_love_teen_illustrated', 'furry_love_adult_illustrated'):
            if story_id == 'furry_love_illustrated':
                gender_word = "baby boy" if child_gender == "male" else "baby girl" if child_gender == "female" else "baby"
            elif story_id == 'furry_love_teen_illustrated':
                gender_word = "teenage boy" if child_gender == "male" else "teenage girl" if child_gender == "female" else "teenager"
            elif story_id == 'furry_love_adult_illustrated':
                gender_word = "man" if child_gender == "male" else "woman" if child_gender == "female" else "person"
            else:
                gender_word = "boy" if child_gender == "male" else "girl" if child_gender == "female" else "child"
            traits['pet_name'] = data.get('pet_name', 'Buddy')
            traits['pet_desc'] = data.get('pet_desc', '')
            traits['pet_species'] = data.get('pet_species', 'dog')
            traits['pet_size'] = data.get('pet_size', 'medium')
            if story_id == 'furry_love_illustrated':
                _age_str = f"{child_age} month old" if child_age == 1 else f"{child_age} months old"
                human_desc = f"a {gender_word}, {_age_str}, {hair_desc}, {eye_desc}, {skin_desc}"
            else:
                human_desc = f"a {gender_word} ({child_age} year old), {hair_desc}, {eye_desc}, {skin_desc}"
            traits['facial_hair'] = data.get('facial_hair', 'none')
            traits['glasses'] = data.get('glasses', 'none')
            traits['body_build'] = data.get('body_build', 'average')
            facial_hair_map = {'stubble': 'light stubble', 'short_beard': 'short beard', 'full_beard': 'full thick beard', 'mustache': 'mustache'}
            fh = traits['facial_hair']
            if fh and fh != 'none' and fh in facial_hair_map:
                human_desc += f", with {facial_hair_map[fh]}"
            gl = traits['glasses']
            if gl and gl != 'none':
                human_desc += f", wearing {gl}"
            bb = traits['body_build']
            if bb and bb != 'average':
                human_desc += f", {bb} build"
            traits['human_desc'] = human_desc
            human_photo = data.get('human_photo_path', '')
            pet_photo = data.get('pet_photo_path', '')
            upload_prefix = 'generated/uploads/furry_photos/'
            traits['human_photo_path'] = human_photo if human_photo and human_photo.startswith(upload_prefix) and os.path.exists(human_photo) else ''
            traits['pet_photo_path'] = pet_photo if pet_photo and pet_photo.startswith(upload_prefix) and os.path.exists(pet_photo) else ''
            from services.personalized_books.preview import generate_personalized_preview
            result = generate_personalized_preview(
                story_id=story_id,
                child_name=child_name,
                gender=child_gender,
                child_age=child_age,
                traits=traits
            )
            if result.get('success') and _ctx.get('gen_token'):
                _save_gen_state(_ctx['gen_token'], 'completed', result.get('image_url'), result.get('kontext_portrait'))
                result['gen_token'] = _ctx['gen_token']
            return jsonify(result)

        if story_id == 'star_keeper_illustrated':
            gender_word = "boy" if child_gender == "male" else "girl" if child_gender == "female" else "child"
            human_desc = f"a {gender_word} ({child_age} year old), {hair_desc}, {eye_desc}, {skin_desc}"
            traits['glasses'] = data.get('glasses', 'none')
            gl = traits['glasses']
            if gl and gl != 'none':
                human_desc += f", wearing {gl}"
            traits['human_desc'] = human_desc
            traits['pet_desc'] = ''
            traits['pet_photo_path'] = ''
            human_photo = data.get('child_photo_path', '') or data.get('human_photo_path', '')
            upload_prefix = 'generated/uploads/furry_photos/'
            traits['human_photo_path'] = human_photo if human_photo and human_photo.startswith(upload_prefix) and os.path.exists(human_photo) else ''
            from services.personalized_books.preview import generate_personalized_preview
            result = generate_personalized_preview(
                story_id=story_id,
                child_name=child_name,
                gender=child_gender,
                child_age=child_age,
                traits=traits
            )
            if result.get('success') and _ctx.get('gen_token'):
                _save_gen_state(_ctx['gen_token'], 'completed', result.get('image_url'), result.get('kontext_portrait'))
                result['gen_token'] = _ctx['gen_token']
            return jsonify(result)

        if is_baby:
            gender_word = "baby boy" if child_gender == "male" else "baby girl" if child_gender == "female" else "baby"
            _months = child_age
            if _months <= 3:    age_display = "1-3 month old"
            elif _months <= 7:  age_display = "4-7 month old"
            elif _months <= 12: age_display = "8-12 month old"
            elif _months <= 18: age_display = "12-18 month old"
            else:               age_display = "18-24 month old"

            from services.fixed_stories import (
                BABY_MASTER_PROMPT,
                get_baby_gender_face_desc, get_baby_hair_desc,
                get_baby_hair_mandate, get_baby_hair_strict, get_baby_pose_desc,
                get_baby_clothing_desc, get_baby_anatomy_strict,
            )
            skin_tone = get_skin_tone(traits.get('skin_tone', 'light'))
            _hair_length   = traits.get('hair_length', 'medium')
            gender_face_desc = get_baby_gender_face_desc(child_gender)
            baby_hair_desc   = get_baby_hair_desc(
                _hair_length,
                traits.get('hair_color', 'brown'),
                traits.get('hair_type', 'straight'),
                child_gender
            )
            hair_mandate   = get_baby_hair_mandate(_hair_length)
            hair_strict    = get_baby_hair_strict(_hair_length)
            pose_desc      = get_baby_pose_desc(child_age)
            clothing_desc  = get_baby_clothing_desc(child_gender)
            anatomy_strict = get_baby_anatomy_strict(child_gender, child_age)

            _gl_baby  = traits.get('glasses', '')
            _eye_baby = eye_desc
            if _gl_baby and _gl_baby not in ('none', ''):
                _eye_baby = eye_desc + ", wearing round glasses"

            prompt = BABY_MASTER_PROMPT.format(
                hair_mandate     = hair_mandate,
                gender_face_desc = gender_face_desc,
                age_display      = age_display,
                hair_desc        = baby_hair_desc,
                eye_desc         = _eye_baby,
                skin_desc        = skin_desc,
                clothing_desc    = clothing_desc,
                pose_desc        = pose_desc,
                companion_action = story_config.get('companion_action', ''),
                env_desc         = story_config.get('env_desc', 'Cozy nursery, soft pastel colors'),
                atm_desc         = story_config.get('atm_desc', 'Warm dreamy magical light'),
                hair_strict      = hair_strict,
                anatomy_strict   = anatomy_strict,
                companion_strict = story_config.get('companion_strict', 'Exactly ONE human baby in frame.'),
            )
            print(f"[BABY MASTER PROMPT] story={story_id} | age={age_display} | hair={traits.get('hair_length')} | gender={child_gender}")
            print(f"\n===== BABY MASTER PROMPT =====\n{prompt}\n===== FIN =====")
        else:
            gender_word = "little boy" if child_gender == "male" else "little girl" if child_gender == "female" else "child"
            gender_features = "young boy features, 4-5 years old" if child_gender == "male" else "young girl features, 4-5 years old" if child_gender == "female" else "4-5 years old"
            age_desc = f"{child_age} years old" if child_age else "4-5 years old"
            outfit = "cozy green tunic with brown pants and small boots" if child_gender == "male" else "flowing lavender dress with small boots"
            
            from services.personalized_books.generation import is_personalized_book as check_personalized
            if check_personalized(story_id):
                if story_id in ('furry_love_illustrated', 'furry_love_adventure_illustrated', 'furry_love_teen_illustrated', 'furry_love_adult_illustrated'):
                    traits['pet_name'] = data.get('pet_name', 'Buddy')
                    traits['pet_desc'] = data.get('pet_desc', '')
                    traits['facial_hair'] = data.get('facial_hair', 'none')
                    traits['glasses'] = data.get('glasses', 'none')
                    traits['body_build'] = data.get('body_build', 'average')
                    human_desc = f"a {gender_word} ({child_age} year old), {hair_desc}, {eye_desc}, {skin_desc}"
                    facial_hair_map = {'stubble': 'light stubble', 'short_beard': 'short beard', 'full_beard': 'full thick beard', 'mustache': 'mustache'}
                    fh = traits['facial_hair']
                    if fh and fh != 'none' and fh in facial_hair_map:
                        human_desc += f", with {facial_hair_map[fh]}"
                    gl = traits['glasses']
                    if gl and gl != 'none':
                        human_desc += f", wearing {gl}"
                    bb = traits['body_build']
                    if bb and bb != 'average':
                        human_desc += f", {bb} build"
                    traits['human_desc'] = human_desc
                from services.personalized_books.preview import generate_personalized_preview
                
                result = generate_personalized_preview(
                    story_id=story_id,
                    child_name=child_name,
                    gender=child_gender,
                    child_age=child_age,
                    traits=traits,
                    child_photo_path=child_photo_path
                )
                if result.get('success') and _ctx.get('gen_token'):
                    _save_gen_state(_ctx['gen_token'], 'completed', result.get('image_url'), result.get('kontext_portrait'))
                    result['gen_token'] = _ctx['gen_token']
                return jsonify(result)
            else:
                preview_override = story_config.get('preview_prompt_override')
                if preview_override:
                    # Calculate all required variables for preview_prompt_override
                    age_display = f"{child_age} year old" if child_age and child_age > 0 else "4-5 year old"
                    gender_child = get_gender_child(child_gender)
                    skin_tone = get_skin_tone(traits.get('skin_tone', 'light'))
                    hair_color = traits.get('hair_color', 'brown')
                    hair_length = traits.get('hair_length', 'medium')
                    hair_type = traits.get('hair_type', 'straight')
                    
                    # Build char_base using the proper hair_desc (handles bald/very_little/very_short correctly)
                    char_base = f"a {age_display} {gender_child} with {hair_desc}, {skin_tone} skin, and {eye_desc}"
                    
                    from services.fixed_stories import BUNNY_DESC, PUPPY_DESC, KITTEN_DESC, GUARDIAN_LIGHT_DESC, DOG_FOREVER_DESC, SPARK_DESC, LILA_DESC, get_hair_action
                    hair_action = get_hair_action(traits)
                    scene_style = "NO text, NO watermark, NO signature, NO logo, NO artist name, NO handwriting, NO calligraphy, clean illustration only"
                    spark_desc_formatted = SPARK_DESC.format(gender_word=gender_word)
                    lila_desc_formatted = LILA_DESC.format(gender_word=gender_word)
                    dog_forever_desc_formatted = DOG_FOREVER_DESC.format(gender_word=gender_word)
                    candle_plural = "s" if child_age != 1 else ""
                    candle_plural_en = "s" if child_age != 1 else ""
                    _eye_desc_qs = eye_desc
                    _gl_qs = traits.get('glasses', '')
                    if _gl_qs and _gl_qs not in ('none', ''):
                        _eye_desc_qs = eye_desc + ", wearing round glasses"
                        char_base = f"a {age_display} {gender_child} with {hair_desc}, {skin_tone} skin, {eye_desc}, wearing round glasses"
                    prompt = preview_override.format(
                        gender_word=gender_word,
                        gender_child=gender_child,
                        hair_desc=hair_desc,
                        eye_desc=_eye_desc_qs,
                        skin_desc=skin_desc,
                        skin_tone=skin_tone,
                        gender_features=gender_features,
                        age_display=age_display,
                        child_age=child_age,
                        candle_plural=candle_plural,
                        candle_plural_en=candle_plural_en,
                        hair_color=hair_color,
                        hair_length=hair_length,
                        hair_type=hair_type,
                        hair_action=hair_action,
                        char_base=char_base,
                        style=scene_style,
                        bunny_desc=BUNNY_DESC,
                        puppy_desc=PUPPY_DESC,
                        kitten_desc=KITTEN_DESC,
                        guardian_light_desc=GUARDIAN_LIGHT_DESC,
                        dog_forever_desc=dog_forever_desc_formatted,
                        spark_desc=spark_desc_formatted,
                        lila_desc=lila_desc_formatted
                    )
                    from services.fixed_stories import enforce_gender_clothing as egc
                    prompt = egc(prompt, child_gender)
                    # Reinforce short/bald hair in STRICT section for all Express stories
                    _hl_qs = traits.get('hair_length', '')
                    _age_qs = int(traits.get('child_age', 1) or 1)
                    if 'STRICT:' in prompt:
                        if _hl_qs == 'bald':
                            prompt = prompt.replace('STRICT:', 'STRICT: Child has completely smooth bald head, zero hair,', 1)
                        elif _hl_qs == 'very_little':
                            _is_baby_qs = story_config.get('age_range', '') in ['0-1', '0-2']
                            if _is_baby_qs:
                                prompt = prompt.replace(
                                    'STRICT:',
                                    'STRICT: Baby head is nearly bald, smooth scalp with only very sparse fine downy fuzz, '
                                    'appearing almost completely bald, no hair volume, scalp shape clearly visible,',
                                    1
                                )
                            else:
                                prompt = prompt.replace('STRICT:', 'STRICT: Child has extremely short buzz cut or tight pixie, hair barely covers scalp, does not extend past ears,', 1)
                    print(f"Using story-specific preview override for: {story_id} (age: {age_display})")
                    print(f"\n===== PROMPT ENVIADO A FLUX =====\n{prompt}\n===== FIN PROMPT =====")

                else:
                    prompt = f"Full body portrait of a cheerful {gender_word} (4-5 years old) with {hair_desc}, {eye_desc} and {skin_desc}, {gender_features}, wearing adventure clothes (simple shirt and shorts), standing in a magical garden, bright curious expression, happy smile, soft magical background with warm light and floating sparkles, children's storybook watercolor illustration style, soft luminous colors, warm lighting, magical atmosphere. NO text, NO watermark, NO signature, NO logo, clean illustration only"
        
        # Reinforce dark/medium-dark skin for ALL Express story previews
        _skin_raw = traits.get('skin_tone', 'light')
        _dark_skin_map = {
            'dark':        'Child has VERY DARK brown skin, clearly dark African complexion, deep dark chocolate skin tone — NOT light, NOT medium, NOT olive skin',
            'medium_dark': 'Child has warm dark brown skin, medium-dark complexion, distinctly darker than average — NOT light skin',
            'brown':       'Child has rich brown skin with dark mahogany undertones, clearly brown-skinned — NOT light skin',
        }
        if _skin_raw in _dark_skin_map:
            _skin_note = _dark_skin_map[_skin_raw]
            if 'STRICT:' in prompt:
                prompt = prompt.replace('STRICT:', f'STRICT: {_skin_note},', 1)
            else:
                prompt += f' STRICT SKIN: {_skin_note}.'

        print(f"Preview prompt: {gender_word} ({age_range}) with {hair_desc}, {eye_desc}, {skin_desc}")

        output_dir = f'generated/previews'
        os.makedirs(output_dir, exist_ok=True)

        reference_image = data.get('reference_image', '')
        ref_local = reference_image.lstrip('/') if reference_image else ''

        if is_baby and not is_quick_story and ref_local and os.path.exists(ref_local):
            from services.replicate_service import generate_scene_with_flux2dev
            print(f"[PREVIEW REGEN] Using FLUX 2 Dev with reference: {ref_local}")
            local_path = generate_scene_with_flux2dev(
                prompt, ref_local, 0, "3:4", output_dir,
                gender=child_gender, age_range=age_range,
                hair_length=traits.get('hair_length', 'medium'),
                child_age=child_age,
                hair_color=traits.get('hair_color', 'brown')
            )
        else:
            if is_quick_story and is_baby:
                preview_model = FLUX_2_DEV_MODEL
                print(f"[PREVIEW] Baby Quick Story: using FLUX 2 Dev with negative_prompt")
            elif is_quick_story:
                preview_model = FLUX_2_DEV_MODEL
                print(f"[PREVIEW] Non-baby Quick Story: using FLUX 2 Dev")
            else:
                preview_model = None
            _baby_neg = (
                "hair tuft, hair spike, topknot, single curl on head, baby hair curl, "
                "hair wisp sticking up, raised hair, hair protrusion, hair bump, "
                "pointed hair, hair flick, forelock, cowlick, hair sticking up, "
                "large ears, big ears, prominent ears, protruding ears, oversized ears, "
                "elf ears, elephant ears, floppy ears, wide ears"
            ) if is_baby else None
            image_url = generate_illustration_replicate(prompt, 0, aspect_ratio="3:4", model=preview_model, negative_prompt=_baby_neg)
            local_path = save_image_locally(image_url, f'{output_dir}/preview_{uuid.uuid4().hex[:8]}.png')

        _final_url = f'/{local_path}'
        if _ctx.get('gen_token'):
            _save_gen_state(_ctx['gen_token'], 'completed', _final_url)
        return jsonify({
            'success': True,
            'image_url': _final_url,
            'gen_token': _ctx.get('gen_token', '')
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        if _ctx.get('gen_token'):
            _save_gen_state(_ctx['gen_token'], 'failed', error=str(e))
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if _ctx.get('gen_key'):
            with _active_gen_lock:
                _active_generations.pop(_ctx['gen_key'], None)


@app.route('/api/preview-gen-status', methods=['GET'])
def preview_gen_status():
    """Return persisted state of a preview generation by token (for page-reload recovery)."""
    token = request.args.get('token', '').strip()
    if not token or len(token) > 40 or not token.isalnum():
        return jsonify({'status': 'expired'}), 200
    path = f'data/preview_gen/{token}.json'
    try:
        if not os.path.exists(path):
            return jsonify({'status': 'expired'}), 200
        with open(path, 'r') as _gf:
            state = json.load(_gf)
        from datetime import datetime as _dt
        updated = state.get('updated_at', '')
        if updated:
            age_seconds = (_dt.utcnow() - _dt.fromisoformat(updated)).total_seconds()
            if age_seconds > 7200:
                return jsonify({'status': 'expired'}), 200
        return jsonify(state), 200
    except Exception:
        return jsonify({'status': 'expired'}), 200


@app.route('/api/regenerate-furry-preview', methods=['POST'])
def regenerate_furry_preview():
    """Regenerate a single furry_love preview (human OR pet) individually"""
    try:
        data = request.get_json()

        client_ip  = get_client_ip()
        user_email = data.get('user_email', '').strip()
        story_id   = data.get('story_id', '')
        allowed, reason = check_generation_allowed(user_email, story_id, client_ip)
        if not allowed:
            return jsonify({'success': False, 'error': 'rate_limited', 'rate_limited': True, 'reason': reason}), 429
        if user_email:
            save_preview_lead(user_email, client_ip, story_id)

        which = data.get('which', 'human')
        
        from services.replicate_service import save_image_locally, get_unified_skin_description
        from services.fixed_stories import get_hair_description, get_eye_description
        from services.personalized_books.preview import generate_with_flux2_dev, generate_with_flux_pulid, generate_with_flux_kontext
        story_id_regen = data.get('story_id', 'furry_love_illustrated')
        if story_id_regen == 'furry_love_adventure_illustrated':
            from services.personalized_books.furry_love_adventure_prompts import (
                build_human_preview_prompt, build_pet_preview_prompt,
                build_human_preview_prompt_with_photo, build_pet_preview_prompt_with_photo
            )
        elif story_id_regen == 'furry_love_teen_illustrated':
            from services.personalized_books.furry_love_teen_prompts import (
                build_human_preview_prompt, build_pet_preview_prompt,
                build_human_preview_prompt_with_photo, build_pet_preview_prompt_with_photo
            )
        elif story_id_regen == 'furry_love_adult_illustrated':
            from services.personalized_books.furry_love_adult_prompts import (
                build_human_preview_prompt, build_pet_preview_prompt,
                build_human_preview_prompt_with_photo, build_pet_preview_prompt_with_photo
            )
        else:
            from services.personalized_books.furry_love_prompts import (
                build_human_preview_prompt, build_pet_preview_prompt,
                build_human_preview_prompt_with_photo, build_pet_preview_prompt_with_photo
            )
        
        child_gender = data.get('gender', 'neutral')
        try:
            child_age = int(data.get('child_age', '1'))
        except (ValueError, TypeError):
            child_age = 1
        traits = {
            'hair_color': data.get('hair_color', 'brown'),
            'hair_type': data.get('hair_type', 'straight'),
            'hair_length': data.get('hair_length', 'medium'),
            'eye_color': data.get('eye_color', 'brown'),
            'skin_tone': data.get('skin_tone', 'light'),
            'child_age': str(child_age),
            'gender': child_gender
        }
        
        hair_desc = get_hair_description(traits)
        eye_desc = get_eye_description(traits)
        skin_tone = get_unified_skin_description(traits.get('skin_tone', 'light'))
        
        output_dir = 'generated/previews'
        os.makedirs(output_dir, exist_ok=True)
        
        if which == 'human':
            human_photo_path = data.get('human_photo_path', '')
            upload_prefix = 'generated/uploads/furry_photos/'
            if human_photo_path and human_photo_path.startswith(upload_prefix) and os.path.exists(human_photo_path):
                gender_word = "baby boy" if child_gender == "male" else "baby girl" if child_gender == "female" else "baby"
                if child_age == 0:
                    age_display = "infant baby, few months old"
                elif child_age >= 60:
                    age_display = "mature adult"
                    gender_word = "man" if child_gender == "male" else "woman" if child_gender == "female" else "person"
                elif child_age >= 40:
                    age_display = "middle-aged adult"
                    gender_word = "man" if child_gender == "male" else "woman" if child_gender == "female" else "person"
                elif child_age >= 18:
                    age_display = "young adult"
                    gender_word = "man" if child_gender == "male" else "woman" if child_gender == "female" else "person"
                elif child_age > 0:
                    age_display = f"{child_age} year old"
                    gender_word = "boy" if child_gender == "male" else "girl" if child_gender == "female" else "person"
                else:
                    age_display = "adult"
                    gender_word = "man" if child_gender == "male" else "woman" if child_gender == "female" else "person"
                glasses_val = data.get('glasses', 'none')
                if human_photo_path and story_id_regen == 'furry_love_adventure_illustrated':
                    hair_for_prompt = hair_desc
                elif human_photo_path:
                    hair_for_prompt = "hair and scalp naturally matching the reference photo"
                else:
                    hair_for_prompt = hair_desc
                prompt = build_human_preview_prompt_with_photo(gender_word, age_display, eye_desc, hair_for_prompt, glasses=glasses_val)
                print(f"[REGEN FURRY] WITH PHOTO prompt: {prompt[:200]}...")
                print(f"[REGEN FURRY] gender_word={gender_word}, age_display={age_display}, child_age={child_age}, story_id={story_id_regen}")
                photo_ref = human_photo_path
            else:
                if child_age >= 18:
                    gender_word = "man" if child_gender == "male" else "woman" if child_gender == "female" else "person"
                else:
                    gender_word = "boy" if child_gender == "male" else "girl" if child_gender == "female" else "person"
                if child_age == 0:
                    age_display = "baby"
                elif child_age >= 18:
                    age_display = f"{child_age} year old adult"
                elif child_age > 0:
                    age_display = f"{child_age} year old"
                else:
                    age_display = "adult"
                human_desc = f"a {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin"
                facial_hair_map = {'stubble': 'light stubble', 'short_beard': 'short beard', 'full_beard': 'full thick beard', 'mustache': 'mustache'}
                fh_r = data.get('facial_hair', 'none')
                if fh_r and fh_r != 'none' and fh_r in facial_hair_map:
                    human_desc += f", with {facial_hair_map[fh_r]}"
                gl_r = data.get('glasses', 'none')
                if gl_r and gl_r != 'none':
                    human_desc += f", wearing {gl_r}"
                bb_r = data.get('body_build', 'average')
                if bb_r and bb_r != 'average':
                    human_desc += f", {bb_r} build"
                _is_baby_regen = (story_id_regen == 'furry_love_illustrated')
                prompt = build_human_preview_prompt(human_desc, is_baby=_is_baby_regen)
                photo_ref = None
            
            print(f"[REGEN FURRY] Regenerating HUMAN preview (photo={bool(photo_ref)})")
            print(f"[REGEN FURRY DEBUG] HUMAN PROMPT FULL ({len(prompt)} chars): {prompt}")
            if photo_ref:
                use_pulid = story_id_regen in ('furry_love_teen_illustrated',)
                use_kontext = story_id_regen in ('furry_love_adventure_illustrated', 'furry_love_adult_illustrated')
                if use_kontext:
                    print(f"[REGEN FURRY] Using Kontext Pro for {story_id_regen}")
                    if story_id_regen == 'furry_love_adult_illustrated':
                        kontext_prompt = (
                            f"Convert the adult {gender_word} in @image1 into a high-quality 3D animated storybook character. "
                            f"Preserve the exact face, hair color, skin tone, and age from the photo — identical adult likeness. "
                            f"OUTFIT: casual outdoor hiking clothes (flannel shirt or fleece, cargo pants, hiking boots). "
                            f"BACKGROUND: soft cream gradient, plain studio. "
                            f"POSE: standing, full body visible from head to feet, relaxed confident smile, arms naturally at sides."
                        )
                    else:
                        kontext_prompt = (
                            f"Transform this child into a Disney Pixar 3D animated character. "
                            f"FULL BODY from head to toe, standing confidently, big joyful smile, arms relaxed at sides. "
                            f"{gender_word} ({age_display}), {hair_desc}, {eye_desc}. "
                            f"Wearing a colorful adventure outfit with a small explorer backpack. "
                            f"NEUTRAL SOLID GRADIENT BACKGROUND, soft cream to warm beige, plain studio portrait. "
                            f"Disney Pixar 3D animation style, big expressive eyes, smooth skin, warm cinematic lighting. "
                            f"Clean professional illustration only. ABSOLUTELY NO text, no watermarks, no logos anywhere."
                        )
                    try:
                        image_url = generate_with_flux_kontext(kontext_prompt, photo_ref, aspect_ratio="3:4")
                    except Exception as kontext_err:
                        print(f"[REGEN FURRY] Kontext failed ({str(kontext_err)[:150]}), falling back to FLUX 2 Dev...")
                        image_url = generate_with_flux2_dev(prompt, aspect_ratio="3:4", photo_ref_path=photo_ref, image_prompt_strength=0.90)
                elif use_pulid:
                    print(f"[REGEN FURRY] Using PuLID for {story_id_regen}")
                    try:
                        image_url = generate_with_flux_pulid(prompt, photo_ref, width=768, height=1024)
                    except Exception as pulid_err:
                        print(f"[REGEN FURRY] PuLID failed ({str(pulid_err)[:150]}), falling back to FLUX 2 Dev...")
                        image_url = generate_with_flux2_dev(prompt, aspect_ratio="3:4", photo_ref_path=photo_ref, image_prompt_strength=0.90)
                else:
                    print(f"[REGEN FURRY] Using FLUX 2 Dev for {story_id_regen}")
                    image_url = generate_with_flux2_dev(prompt, aspect_ratio="3:4", photo_ref_path=photo_ref, image_prompt_strength=0.90)
            else:
                _hair_neg_regen = "full hair, thick voluminous hair, hair covering entire head, dense hair" if data.get('hair_length') == 'very_little' else None
                image_url = generate_with_flux2_dev(prompt, aspect_ratio="3:4", image_prompt_strength=0.75, negative_prompt=_hair_neg_regen)
            local_path = save_image_locally(image_url, f'{output_dir}/preview_human_{uuid.uuid4().hex[:8]}.png')
        else:
            pet_desc = data.get('pet_desc', '')
            pet_species = data.get('pet_species', 'dog')
            pet_photo_path = data.get('pet_photo_path', '')
            upload_prefix = 'generated/uploads/furry_photos/'
            if pet_photo_path and pet_photo_path.startswith(upload_prefix) and os.path.exists(pet_photo_path):
                pet_size_regen = data.get('pet_size', 'medium')
                prompt = build_pet_preview_prompt_with_photo(pet_desc, pet_species, pet_size=pet_size_regen)
                photo_ref = pet_photo_path
            else:
                prompt = build_pet_preview_prompt(pet_desc)
                photo_ref = None
            
            print(f"[REGEN FURRY] Regenerating PET preview (photo={bool(photo_ref)})")
            image_url = generate_with_flux2_dev(prompt, aspect_ratio="3:4", photo_ref_path=photo_ref, image_prompt_strength=0.90)
            local_path = save_image_locally(image_url, f'{output_dir}/preview_pet_{uuid.uuid4().hex[:8]}.png')
        
        return jsonify({
            'success': True,
            'image_url': f'/{local_path}',
            'preview_path': local_path
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/regenerate-cover/<preview_id>', methods=['POST'])
def regenerate_cover(preview_id):
    """Regenerate the cover image for a personalized book preview"""
    try:
        preview_file = f'story_previews/{preview_id}.json'
        if not os.path.exists(preview_file):
            return jsonify({'success': False, 'error': 'Preview not found'}), 404
        
        with open(preview_file, 'r', encoding='utf-8') as f:
            story_data = json.load(f)
        
        story_id = story_data.get('story_template') or story_data.get('story_id', '')
        traits = story_data.get('traits', {})
        output_dir = story_data.get('output_dir', f'generated/previews/{preview_id}')
        os.makedirs(output_dir, exist_ok=True)

        # Cover regeneration limit: max 2 per preview (all paid personalized books).
        cover_regen_count = story_data.get('cover_regenerations') or 0
        if cover_regen_count >= 2 and not is_testing_mode_active():
            return jsonify({
                'success': False,
                'error': 'Has alcanzado el límite de 2 regeneraciones para la portada'
            }), 400

        is_furry = 'furry_love' in story_id
        
        if is_furry:
            human_preview_path = story_data.get('human_preview_path', '')
            pet_preview_path = story_data.get('pet_preview_path', '')
            
            if not human_preview_path or not os.path.exists(human_preview_path):
                for f_name in os.listdir(output_dir):
                    if f_name.startswith('preview_human_') and f_name.endswith('.png'):
                        human_preview_path = os.path.join(output_dir, f_name)
                        break
            if not pet_preview_path or not os.path.exists(pet_preview_path):
                for f_name in os.listdir(output_dir):
                    if f_name.startswith('preview_pet_') and f_name.endswith('.png'):
                        pet_preview_path = os.path.join(output_dir, f_name)
                        break
            
            if not human_preview_path or not pet_preview_path:
                return jsonify({'success': False, 'error': 'Reference images not found. Please regenerate character previews first.'}), 400
            
            if story_id == 'furry_love_adventure_illustrated':
                from services.personalized_books.furry_love_adventure_prompts import FRONT_COVER, build_scene_prompt
            elif story_id == 'furry_love_teen_illustrated':
                from services.personalized_books.furry_love_teen_prompts import FRONT_COVER, build_scene_prompt
            elif story_id == 'furry_love_adult_illustrated':
                from services.personalized_books.furry_love_adult_prompts import FRONT_COVER, build_scene_prompt
            else:
                from services.personalized_books.furry_love_prompts import FRONT_COVER, build_scene_prompt
            
            from services.personalized_books.preview import generate_with_flux2_dev
            from services.replicate_service import save_image_locally, create_cover_from_character
            from services.fixed_stories import get_eye_description
            
            human_desc = traits.get('human_desc', '')
            pet_desc = traits.get('pet_desc', '')
            pet_name = traits.get('pet_name', 'Buddy')
            child_name = story_data.get('child_name', '')
            child_gender_regen = story_data.get('gender', 'neutral')
            child_age_regen = str(traits.get('child_age', '5'))
            eye_desc_regen = get_eye_description(traits) if traits.get('eye_color') else ''
            age_val_regen = int(child_age_regen) if child_age_regen.isdigit() else 5
            if 'furry_love_adult' in story_id:
                gender_word_regen = "man" if child_gender_regen == "male" else "woman" if child_gender_regen == "female" else "adult"
                age_display_regen = f"{age_val_regen} year old adult"
            elif 'furry_love_teen' in story_id:
                gender_word_regen = "boy" if child_gender_regen == "male" else "girl" if child_gender_regen == "female" else "teenager"
                age_display_regen = f"{age_val_regen} year old teenager"
            elif 'furry_love_adventure' in story_id:
                gender_word_regen = "boy" if child_gender_regen == "male" else "girl" if child_gender_regen == "female" else "person"
                age_display_regen = f"{age_val_regen} year old child"
            else:
                gender_word_regen = "baby boy" if child_gender_regen == "male" else "baby girl" if child_gender_regen == "female" else "baby"
                age_display_regen = f"{age_val_regen} month old baby" if age_val_regen < 2 else f"{age_val_regen} year old toddler"
            _hair_color_map_regen = {'black': 'jet black', 'brown': 'medium brown', 'light_brown': 'warm light brown (caramel-honey tone)', 'blonde': 'dark dirty blonde', 'very_light_blonde': 'pale platinum blonde', 'red': 'bright red', 'auburn': 'auburn'}
            hair_color_regen = _hair_color_map_regen.get(traits.get('hair_color', 'brown'), traits.get('hair_color', 'brown'))
            glasses_regen = traits.get('glasses', 'none')
            facial_hair_regen = traits.get('facial_hair', 'none')
            
            cover_prompt = build_scene_prompt(FRONT_COVER, human_desc, pet_name, pet_desc, age_display=age_display_regen, eye_desc=eye_desc_regen, gender_word=gender_word_regen, hair_color=hair_color_regen, glasses=glasses_regen, facial_hair=facial_hair_regen)
            
            _eye_color_raw_regen = traits.get('eye_color', '')
            _eye_color_map_regen = {
                'blue': 'bright blue', 'green': 'green', 'brown': 'brown',
                'hazel': 'hazel', 'gray': 'gray', 'dark_brown': 'dark brown',
            }
            _eye_note_regen = ''
            if _eye_color_raw_regen:
                _eye_label_regen = _eye_color_map_regen.get(_eye_color_raw_regen, _eye_color_raw_regen)
                _eye_note_regen = f" The human has {_eye_label_regen} eyes — preserve this exactly."
            reference_note_regen = (
                "@image1=HUMAN character (approved avatar), @image2=PET animal. "
                "Copy the EXACT skin complexion, eye color, and hair appearance from @image1 — "
                f"replicate the avatar faithfully.{_eye_note_regen} "
                "Human has human face and human hands. Pet has fur, animal face, four paws. "
                "Two distinct separate characters side by side."
            )
            cover_prompt = f"{reference_note_regen}\n{cover_prompt}"
            
            print(f"[REGEN COVER] Regenerating cover for {story_id} with FLUX 2 Dev + references")
            cover_url = generate_with_flux2_dev(
                cover_prompt, 
                aspect_ratio="3:4",
                photo_ref_paths=[human_preview_path, pet_preview_path],
                image_prompt_strength=0.90
            )
            cover_raw_path = save_image_locally(cover_url, f'{output_dir}/cover_raw.png')
            
            story_lang = story_data.get('lang', story_data.get('story_lang', 'es'))
            from services.personalized_books.generation import get_print_title
            book_id = story_id.replace('_illustrated', '')
            story_title = get_print_title(book_id, child_name, story_lang, pet_name=pet_name)
            author_name = story_data.get('author_name', '')
            
            cover_image_path = create_cover_from_character(
                cover_raw_path, output_dir,
                title=story_title,
                author=author_name if author_name else ''
            )
            
            story_data['cover_image'] = f'/{cover_image_path}'
            story_data['cover_raw_path'] = cover_raw_path
            story_data['original_cover'] = f'/{cover_image_path}'
            story_data['cover_regenerations'] = cover_regen_count + 1
            
            with open(preview_file, 'w', encoding='utf-8') as f:
                json.dump(story_data, f, ensure_ascii=False, indent=2)
            
            print(f"[REGEN COVER] Cover regenerated successfully: {cover_image_path}")

            # Single reconstruction pipeline: cover_raw.png is now newer than the
            # existing cover_spread, so rebuild_book will rebuild the spread,
            # visor, printable PDF and Cloudprinter PDFs from it.
            # mark_composed=False: this is a pre/post-approval cover regeneration,
            # never a composition-completion event — must not touch the order's
            # composition/approval state flags.
            if os.path.exists(f'generated/composed_{preview_id}'):
                import threading
                from services.personalized_books.rebuild import rebuild_book
                threading.Thread(target=rebuild_book, args=(preview_id,), kwargs={'mark_composed': False}, daemon=True).start()

            return jsonify({
                'success': True,
                'cover_image': f'/{cover_image_path}',
                'regenerations_left': max(0, 2 - (cover_regen_count + 1))
            })
        elif story_id == 'star_keeper_illustrated':
            from services.personalized_books.star_keeper_prompts import (
                FRONT_COVER as SK_FRONT_COVER,
                STYLE_BASE as SK_STYLE_BASE,
                STYLE_BASE_COVER as SK_STYLE_BASE_COVER,
                get_outfit_desc as sk_get_outfit_desc,
                build_ref_note as sk_build_ref_note_fn,
            )
            from services.personalized_books.preview import generate_with_flux2_dev, generate_with_flux_kontext
            from services.replicate_service import save_image_locally, create_cover_from_character, get_gender_negative_prompt
            from services.personalized_books.preview import _ensure_luna_reference

            gender_regen = story_data.get('gender', 'neutral')
            child_name_regen = story_data.get('child_name', '')
            child_age_regen = int(traits.get('child_age', 5))
            gender_word_regen = "boy" if gender_regen == "male" else "girl" if gender_regen == "female" else "child"
            outfit_desc_regen = sk_get_outfit_desc(gender_regen)
            age_display_regen = f"{child_age_regen} year old"
            human_photo_path_regen = traits.get('human_photo_path', '')
            luna_path_regen = _ensure_luna_reference()
            luna_ok_regen = luna_path_regen and os.path.exists(luna_path_regen)
            _sk_neg_base_regen = (
                "text, watermark, signature, logo, letters, words, ugly, deformed, blurry, low quality, "
                "distorted face, wings on child, animal features on human, furry child, "
                "animal ears, cat ears, bunny ears, fox ears, extra limbs"
            )
            sk_neg_regen = (_sk_neg_base_regen + ", masculine features, boy haircut") if gender_regen == 'female' else (_sk_neg_base_regen + ", earrings, jewelry, bows, ribbons, makeup, lipstick, feminine accessories, girl features, ponytails, pigtails") if gender_regen == 'male' else _sk_neg_base_regen
            sk_scene_regen = SK_FRONT_COVER.get('prompt', '').replace('{style}', SK_STYLE_BASE_COVER)

            if human_photo_path_regen and os.path.exists(human_photo_path_regen):
                # Step 1: Reuse saved Kontext portrait if available, otherwise regenerate
                portrait_path_regen = None
                saved_portrait = story_data.get('character_preview', '')
                if saved_portrait:
                    saved_portrait_path = saved_portrait.lstrip('/')
                    if os.path.exists(saved_portrait_path):
                        portrait_path_regen = saved_portrait_path
                        print(f"[REGEN COVER SK] Reusing saved Kontext portrait: {portrait_path_regen}")
                if not portrait_path_regen:
                    kontext_prompt_regen = (
                        f"The child in @image1 is {child_age_regen} years old. "
                        f"Convert @image1 into a Disney Pixar 3D animated children's book character. "
                        f"Copy the face, hair colour, skin tone, and eye colour from @image1 exactly — identical likeness. "
                        f"Replace all clothing with: {outfit_desc_regen}. "
                        f"Full body visible from head to feet, standing pose, brave adventurous smile. "
                        f"Background: deep midnight blue with subtle silver star sparkles, plain studio — "
                        f"no lighthouse, no ocean, no scenery."
                    )
                    print(f"[REGEN COVER SK] Step 1 — Kontext portrait | photo={human_photo_path_regen} | age={child_age_regen}")
                    portrait_url_regen = generate_with_flux_kontext(kontext_prompt_regen, human_photo_path_regen, aspect_ratio="3:4")
                    portrait_path_regen = save_image_locally(portrait_url_regen, f'{output_dir}/sk_portrait_regen_{uuid.uuid4().hex[:8]}.png')

                # Step 2 — PASO 3: FLUX 2 Dev cover scene — ref_note from prompt file (single source of truth)
                sk_ref_note_regen = sk_build_ref_note_fn(age_display_regen, gender_word_regen, '', '', '')
                photo_refs_regen = [portrait_path_regen, luna_path_regen] if luna_ok_regen else [portrait_path_regen]
                print(f"[REGEN COVER SK] PASO 3 — FLUX 2 Dev cover | portrait={portrait_path_regen} | luna={luna_ok_regen}")
                cover_url_regen = generate_with_flux2_dev(
                    f"{sk_ref_note_regen}\n{sk_scene_regen}",
                    aspect_ratio="3:4",
                    photo_ref_paths=photo_refs_regen,
                    image_prompt_strength=0.95,
                    negative_prompt=sk_neg_regen
                )
            else:
                # No-photo: scan for existing portrait or regenerate standalone
                portrait_path_regen = None
                for f_name in os.listdir(output_dir):
                    if f_name.startswith('sk_portrait_') and f_name.endswith('.png'):
                        portrait_path_regen = os.path.join(output_dir, f_name)
                        break
                if portrait_path_regen and os.path.exists(portrait_path_regen) and luna_ok_regen:
                    sk_ref_note_regen = sk_build_ref_note_fn(age_display_regen, gender_word_regen, '', '', '')
                    cover_url_regen = generate_with_flux2_dev(
                        f"{sk_ref_note_regen}\n{sk_scene_regen}",
                        aspect_ratio="3:4",
                        photo_ref_paths=[portrait_path_regen, luna_path_regen],
                        image_prompt_strength=0.95,
                        negative_prompt=sk_neg_regen
                    )
                else:
                    # Fallback: no references, text-only prompt
                    from services.fixed_stories import get_hair_description, get_eye_description, get_hair_strict
                    from services.replicate_service import get_unified_skin_description
                    from services.personalized_books.star_keeper_prompts import get_hair_action as sk_get_hair_action
                    hair_desc_regen = get_hair_description(traits)
                    eye_desc_regen = get_eye_description(traits)
                    skin_regen = get_unified_skin_description(traits.get('skin_tone', 'light'))
                    hair_action_regen = sk_get_hair_action(traits)
                    hair_strict_regen = get_hair_strict(traits)
                    age_display_regen = f"{child_age_regen} year old"
                    sk_nophoto_regen = (
                        f"@image1 = small glowing star companion LUNA — copy @image1 appearance exactly.\n"
                        f"Draw a single {gender_word_regen} ({age_display_regen}), {hair_desc_regen}, {eye_desc_regen}, {skin_regen} skin, "
                        f"big joyful confident smile, {hair_action_regen}. OUTFIT: {outfit_desc_regen}.\n"
                        f"ACTION: The {gender_word_regen} stands confidently at the lighthouse entrance with one hand "
                        f"reaching upward toward the stars, @image1 hovers beside the {gender_word_regen}'s shoulder. "
                        f"SETTING: Old stone lighthouse on a dramatic clifftop WIDE VIEW, magnificent starry sky "
                        f"with bright constellations and shooting stars, ocean waves crashing below, warm golden-blue "
                        f"light from the lighthouse door, centered composition for book cover. "
                        f"ATMOSPHERE: Adventure invitation, celestial magic. "
                        f"STRICT: Only ONE {gender_word_regen}, fully human child, no wings. {hair_strict_regen} "
                        f"ABSOLUTELY NO rendered text, no titles, no logos, no words, no letters, no captions, "
                        f"no watermarks, no signatures, pure illustration only. {SK_STYLE_BASE}"
                    )
                    photo_refs_regen = [luna_path_regen] if luna_ok_regen else None
                    cover_url_regen = generate_with_flux2_dev(
                        sk_nophoto_regen,
                        aspect_ratio="3:4",
                        photo_ref_paths=photo_refs_regen,
                        image_prompt_strength=0.85,
                        negative_prompt=sk_neg_regen
                    )

            cover_raw_path_regen = save_image_locally(cover_url_regen, f'{output_dir}/cover_raw.png')
            story_lang_regen = story_data.get('lang', story_data.get('story_lang', 'es'))
            from services.personalized_books.generation import get_print_title
            story_title_regen = get_print_title('star_keeper', child_name_regen, story_lang_regen)
            author_name_regen = story_data.get('author_name', '')
            cover_image_path_regen = create_cover_from_character(
                cover_raw_path_regen, output_dir,
                title=story_title_regen,
                author=author_name_regen if author_name_regen else ''
            )
            story_data['cover_image'] = f'/{cover_image_path_regen}'
            story_data['cover_raw_path'] = cover_raw_path_regen
            story_data['original_cover'] = f'/{cover_image_path_regen}'
            story_data['cover_regenerations'] = cover_regen_count + 1
            with open(preview_file, 'w', encoding='utf-8') as f:
                json.dump(story_data, f, ensure_ascii=False, indent=2)
            print(f"[REGEN COVER SK] Cover regenerated: {cover_image_path_regen}")

            # mark_composed=False: regeneration only, never a composition-
            # completion event — must not touch composition/approval state.
            if os.path.exists(f'generated/composed_{preview_id}'):
                import threading
                from services.personalized_books.rebuild import rebuild_book
                threading.Thread(target=rebuild_book, args=(preview_id,), kwargs={'mark_composed': False}, daemon=True).start()

            return jsonify({'success': True, 'cover_image': f'/{cover_image_path_regen}', 'regenerations_left': max(0, 2 - (cover_regen_count + 1))})

        elif story_id == 'dragon_garden_illustrated':
            from services.personalized_books.dragon_garden_prompts import (
                FRONT_COVER as DG_FRONT_COVER,
                STYLE_BASE as DG_STYLE_BASE,
                STYLE_BASE_COVER as DG_STYLE_BASE_COVER,
                get_outfit_desc as dg_get_outfit_desc,
                build_ref_note as dg_build_ref_note_fn,
                build_kontext_prompt as dg_build_kontext_prompt,
                build_avatar_prompt as dg_build_avatar_prompt,
            )
            from services.personalized_books.preview import generate_with_flux2_dev, generate_with_flux_kontext
            from services.replicate_service import save_image_locally, create_cover_from_character, get_gender_negative_prompt
            from services.personalized_books.preview import _ensure_spark_reference

            gender_regen = story_data.get('gender', 'neutral')
            child_name_regen = story_data.get('child_name', '')
            child_age_regen = int(traits.get('child_age', 5))
            gender_word_regen = "boy" if gender_regen == "male" else "girl" if gender_regen == "female" else "child"
            outfit_desc_regen = dg_get_outfit_desc(gender_regen)
            age_display_regen = f"{child_age_regen} year old"
            human_photo_path_regen = traits.get('human_photo_path', '')
            spark_path_regen = _ensure_spark_reference()
            spark_ok_regen = spark_path_regen and os.path.exists(spark_path_regen)
            _dg_neg_base_regen = (
                "text, watermark, signature, logo, letters, words, ugly, deformed, blurry, low quality, "
                "distorted face, wings on child, animal features on human, furry child, "
                "animal ears, cat ears, bunny ears, fox ears, extra limbs"
            )
            dg_neg_regen = (_dg_neg_base_regen + ", masculine features, boy haircut") if gender_regen == 'female' else (_dg_neg_base_regen + ", earrings, jewelry, bows, ribbons, makeup, lipstick, feminine accessories, girl features, ponytails, pigtails") if gender_regen == 'male' else _dg_neg_base_regen
            dg_scene_regen = DG_FRONT_COVER.get('prompt', '').replace('{style}', DG_STYLE_BASE_COVER)
            from services.age_profiles import get_age_profile as _dg_regen_age_fn
            _dg_regen_profile, _dg_regen_range_key = _dg_regen_age_fn(child_age_regen)
            _dg_regen_age_body_desc = _dg_regen_profile['kontext']
            print(f"[REGEN COVER DG] age={child_age_regen} range={_dg_regen_range_key} display={_dg_regen_profile['display']}")
            _dg_regen_eye_raw = traits.get('eye_color', '')
            from services.fixed_stories import get_eye_description as _dg_regen_eye_fn
            eye_desc_regen = _dg_regen_eye_fn(traits) if _dg_regen_eye_raw else ''

            if human_photo_path_regen and os.path.exists(human_photo_path_regen):
                portrait_path_regen = None
                saved_portrait = story_data.get('character_preview', '')
                if saved_portrait:
                    saved_portrait_path = saved_portrait.lstrip('/')
                    if os.path.exists(saved_portrait_path):
                        portrait_path_regen = saved_portrait_path
                        print(f"[REGEN COVER DG] Reusing saved Kontext portrait: {portrait_path_regen}")
                if not portrait_path_regen:
                    kontext_prompt_regen = dg_build_kontext_prompt(
                        age_display_regen, gender_word_regen,
                        _dg_regen_age_body_desc, eye_desc_regen, outfit_desc_regen
                    )
                    print(f"[REGEN COVER DG] PASO 1 — Kontext | photo={human_photo_path_regen} | age={child_age_regen}")
                    portrait_url_regen = generate_with_flux_kontext(kontext_prompt_regen, human_photo_path_regen, aspect_ratio="3:4")
                    _kontext_path_regen = save_image_locally(portrait_url_regen, f'{output_dir}/dg_kontext_regen_{uuid.uuid4().hex[:8]}.png')
                    # ── PASO 2: FLUX Avatar — traduce Kontext al lenguaje visual FLUX nativo ──
                    _av_neg_base = (
                        "text, watermark, signature, logo, letters, words, ugly, deformed, blurry, low quality, "
                        "distorted face, defined jawline, visible cheekbones, mature face, adult face, teenager, "
                        "wings on child, animal features on human, furry child, animal ears, extra limbs"
                    )
                    _av_neg_gender = (
                        "masculine features, boy haircut, male jawline" if gender_regen == "female"
                        else "girl features, ponytails, pigtails, feminine accessories, earrings, jewelry, bows, ribbons, makeup, lipstick"
                    )
                    avatar_prompt_regen = dg_build_avatar_prompt(age_display_regen, gender_word_regen)
                    print(f"[REGEN COVER DG] PASO 2 — FLUX avatar | kontext={_kontext_path_regen}")
                    avatar_url_regen = generate_with_flux2_dev(
                        avatar_prompt_regen,
                        aspect_ratio="3:4",
                        photo_ref_path=_kontext_path_regen,
                        image_prompt_strength=1.0,
                        negative_prompt=_av_neg_base + ", " + _av_neg_gender,
                        force_go_fast=False,
                    )
                    portrait_path_regen = save_image_locally(avatar_url_regen, f'{output_dir}/dg_avatar_regen_{uuid.uuid4().hex[:8]}.png')
                    print(f"[REGEN COVER DG] PASO 2 — Avatar guardado: {portrait_path_regen}")

                # PASO 3: FLUX 2 Dev cover scene — ref_note from prompt file (single source of truth)
                dg_ref_note_regen = dg_build_ref_note_fn(age_display_regen, gender_word_regen, '', '', '')
                photo_refs_regen = [portrait_path_regen, spark_path_regen] if spark_ok_regen else [portrait_path_regen]
                print(f"[REGEN COVER DG] PASO 3 — FLUX 2 Dev cover | portrait={portrait_path_regen} | spark={spark_ok_regen}")
                cover_url_regen = generate_with_flux2_dev(
                    f"{dg_ref_note_regen}\n{dg_scene_regen}",
                    aspect_ratio="3:4",
                    photo_ref_paths=photo_refs_regen,
                    image_prompt_strength=0.95,
                    negative_prompt=dg_neg_regen
                )
            else:
                from services.fixed_stories import get_hair_description, get_eye_description, get_hair_strict
                from services.replicate_service import get_unified_skin_description
                from services.personalized_books.dragon_garden_prompts import get_hair_action as dg_get_hair_action
                hair_desc_regen = get_hair_description(traits)
                eye_desc_regen = get_eye_description(traits)
                skin_regen = get_unified_skin_description(traits.get('skin_tone', 'light'))
                hair_action_regen = dg_get_hair_action(traits)
                hair_strict_regen = get_hair_strict(traits)
                age_display_regen = f"{child_age_regen} year old"
                dg_nophoto_regen = (
                    f"@image1 = small emerald dragon companion SPARK — copy @image1 appearance exactly.\n"
                    f"Draw a single {gender_word_regen} ({age_display_regen}), {hair_desc_regen}, {eye_desc_regen}, {skin_regen} skin, "
                    f"big joyful smile, {hair_action_regen}. OUTFIT: {outfit_desc_regen}.\n"
                    f"ACTION: The {gender_word_regen} sits happily on @image1's back soaring through the sky, "
                    f"arms gently holding the dragon, @image1's wings spread wide and flapping. "
                    f"SETTING: Beautiful sky WIDE VIEW, fluffy pink and white cotton clouds, "
                    f"magnificent rainbow arching, golden sunlight, sparkles trailing. "
                    f"ATMOSPHERE: Adventure invitation, joyful flight, magical. "
                    f"STRICT: Only ONE {gender_word_regen}, only ONE small dragon @image1, "
                    f"the {gender_word_regen} is a fully human child: no tail, no wings, no scales. {hair_strict_regen} "
                    f"ABSOLUTELY NO rendered text, no titles, no logos, no words, no letters, no captions, "
                    f"no watermarks, no signatures, pure illustration only. {DG_STYLE_BASE}"
                )
                photo_refs_regen = [spark_path_regen] if spark_ok_regen else None
                cover_url_regen = generate_with_flux2_dev(
                    dg_nophoto_regen,
                    aspect_ratio="3:4",
                    photo_ref_paths=photo_refs_regen,
                    image_prompt_strength=0.85,
                    negative_prompt=dg_neg_regen
                )

            cover_raw_path_regen = save_image_locally(cover_url_regen, f'{output_dir}/cover_raw.png')
            story_lang_regen = story_data.get('lang', story_data.get('story_lang', 'es'))
            from services.personalized_books.generation import get_print_title
            story_title_regen = get_print_title('dragon_garden', child_name_regen, story_lang_regen)
            author_name_regen = story_data.get('author_name', '')
            cover_image_path_regen = create_cover_from_character(
                cover_raw_path_regen, output_dir,
                title=story_title_regen,
                author=author_name_regen if author_name_regen else ''
            )
            story_data['cover_image'] = f'/{cover_image_path_regen}'
            story_data['cover_raw_path'] = cover_raw_path_regen
            story_data['original_cover'] = f'/{cover_image_path_regen}'
            story_data['cover_regenerations'] = cover_regen_count + 1
            with open(preview_file, 'w', encoding='utf-8') as f:
                json.dump(story_data, f, ensure_ascii=False, indent=2)
            print(f"[REGEN COVER DG] Cover regenerated: {cover_image_path_regen}")

            # mark_composed=False: regeneration only, never a composition-
            # completion event — must not touch composition/approval state.
            if os.path.exists(f'generated/composed_{preview_id}'):
                import threading
                from services.personalized_books.rebuild import rebuild_book
                threading.Thread(target=rebuild_book, args=(preview_id,), kwargs={'mark_composed': False}, daemon=True).start()

            return jsonify({'success': True, 'cover_image': f'/{cover_image_path_regen}', 'regenerations_left': max(0, 2 - (cover_regen_count + 1))})

        elif story_id == 'centinela_aurora_illustrated':
            from services.personalized_books.centinela_aurora_prompts import (
                FRONT_COVER as CA_FRONT_COVER,
                STYLE_BASE as CA_STYLE_BASE,
                STYLE_BASE_COVER as CA_STYLE_BASE_COVER,
                get_outfit_desc as ca_get_outfit_desc,
                build_ref_note as ca_build_ref_note_fn,
            )
            from services.personalized_books.preview import generate_with_flux2_dev, generate_with_flux_kontext
            from services.replicate_service import save_image_locally, create_cover_from_character, get_gender_negative_prompt
            from services.personalized_books.preview import _ensure_astro_reference

            gender_regen = story_data.get('gender', 'neutral')
            child_name_regen = story_data.get('child_name', '')
            child_age_regen = int(traits.get('child_age', 5))
            gender_word_regen = "boy" if gender_regen == "male" else "girl" if gender_regen == "female" else "child"
            outfit_desc_regen = ca_get_outfit_desc(gender_regen)
            human_photo_path_regen = traits.get('human_photo_path') or story_data.get('child_photo_path', '')
            astro_path_regen = _ensure_astro_reference()
            astro_ok_regen = astro_path_regen and os.path.exists(astro_path_regen)
            # Custom negative_prompt for Centinela: sin supresión de cola (ASTRO tiene cola legítima).
            # Sí suprime: multi-cola, rasgos animales en el niño, género incorrecto.
            _ca_neg_base_regen = (
                "text, watermark, signature, logo, letters, words, ugly, deformed, blurry, low quality, "
                "distorted face, wings on child, animal features on human, furry child, "
                "animal ears, cat ears, bunny ears, fox ears, extra limbs, hybrid creature, "
                "animal body parts on human, two tails, multiple tails, double tail, split tail, extra tail"
            )
            ca_neg_regen = (_ca_neg_base_regen + ", masculine features, boy haircut") if gender_regen == 'female' else (_ca_neg_base_regen + ", earrings, jewelry, bows, ribbons, makeup, lipstick, feminine accessories, girl features, ponytails, pigtails") if gender_regen == 'male' else _ca_neg_base_regen
            ca_scene_regen = CA_FRONT_COVER.get('prompt', '').replace('{style}', CA_STYLE_BASE_COVER)
            from services.age_profiles import get_age_profile as _ca_regen_age_fn
            _ca_regen_profile, _ca_regen_range_key = _ca_regen_age_fn(child_age_regen)
            _ca_regen_age_body_desc = _ca_regen_profile['kontext']
            print(f"[REGEN COVER CA] age={child_age_regen} range={_ca_regen_range_key} display={_ca_regen_profile['display']}")
            age_display_regen = f"{child_age_regen} year old"
            _ca_regen_eye_raw = traits.get('eye_color', '')
            from services.fixed_stories import get_eye_description as _ca_regen_eye_fn
            eye_desc_regen = _ca_regen_eye_fn(traits) if _ca_regen_eye_raw else ''

            if human_photo_path_regen and os.path.exists(human_photo_path_regen):
                portrait_path_regen = None
                saved_portrait = story_data.get('character_preview', '')
                if saved_portrait:
                    saved_portrait_path = saved_portrait.lstrip('/')
                    if os.path.exists(saved_portrait_path):
                        portrait_path_regen = saved_portrait_path
                        print(f"[REGEN COVER CA] Reusing saved FLUX avatar: {portrait_path_regen}")
                if not portrait_path_regen:
                    # ── PASO 1: Kontext — convierte foto → personaje 3D animado ──
                    from services.personalized_books.centinela_aurora_prompts import (
                        build_kontext_prompt as _ca_bk_regen,
                        build_avatar_prompt as _ca_ba_regen,
                    )
                    kontext_prompt_regen = _ca_bk_regen(
                        age_display_regen, gender_word_regen, _ca_regen_age_body_desc, eye_desc_regen, outfit_desc_regen
                    )
                    print(f"[REGEN COVER CA] PASO 1 — Kontext | photo={human_photo_path_regen} | age={child_age_regen}")
                    portrait_url_regen = generate_with_flux_kontext(kontext_prompt_regen, human_photo_path_regen, aspect_ratio="3:4")
                    _kontext_path_regen = save_image_locally(portrait_url_regen, f'{output_dir}/ca_kontext_regen_{uuid.uuid4().hex[:8]}.png')
                    # ── PASO 2: FLUX Avatar — traduce Kontext al lenguaje visual FLUX nativo ──
                    _av_neg_base = (
                        "text, watermark, signature, logo, letters, words, ugly, deformed, blurry, low quality, "
                        "distorted face, defined jawline, visible cheekbones, mature face, adult face, teenager, "
                        "wings on child, animal features on human, furry child, animal ears, extra limbs"
                    )
                    _av_neg_gender = (
                        "masculine features, boy haircut, male jawline" if gender_regen == "female"
                        else "girl features, ponytails, pigtails, feminine accessories, earrings, jewelry, bows, ribbons, makeup, lipstick"
                    )
                    avatar_prompt_regen = _ca_ba_regen(age_display_regen, gender_word_regen)
                    print(f"[REGEN COVER CA] PASO 2 — FLUX avatar | kontext={_kontext_path_regen}")
                    avatar_url_regen = generate_with_flux2_dev(
                        avatar_prompt_regen,
                        aspect_ratio="3:4",
                        photo_ref_path=_kontext_path_regen,
                        image_prompt_strength=0.95,
                        negative_prompt=_av_neg_base + ", " + _av_neg_gender,
                        force_go_fast=False,
                    )
                    portrait_path_regen = save_image_locally(avatar_url_regen, f'{output_dir}/ca_avatar_regen_{uuid.uuid4().hex[:8]}.png')
                    print(f"[REGEN COVER CA] PASO 2 — Avatar guardado: {portrait_path_regen}")

                # ── FLUX 2 Dev Cover — mismo prompt que preview PASO 3 ──
                from services.personalized_books.age_profiles_nophoto import get_age_profile_nophoto as _ca_regen_nophoto_fn
                _ca_regen_nophoto_profile, _ = _ca_regen_nophoto_fn(child_age_regen)
                ca_ref_note_regen = ca_build_ref_note_fn(
                    _ca_regen_nophoto_profile['display'], gender_word_regen,
                    _ca_regen_nophoto_profile['cover_ref'],
                    eye_desc_regen, outfit_desc_regen
                )
                photo_refs_regen = [portrait_path_regen, astro_path_regen] if astro_ok_regen else [portrait_path_regen]
                print(f"[REGEN COVER CA] PASO 3 — FLUX 2 Dev cover | portrait={portrait_path_regen} | astro={astro_ok_regen} | prompt_len={len(ca_ref_note_regen)+len(ca_scene_regen)}")
                cover_url_regen = generate_with_flux2_dev(
                    f"{ca_ref_note_regen}\n{ca_scene_regen}",
                    aspect_ratio="3:4",
                    photo_ref_paths=photo_refs_regen,
                    image_prompt_strength=0.95,
                    negative_prompt=ca_neg_regen
                )
            else:
                # ── SISTEMA 2 (sin foto): usar portrait guardado como @image1 + ASTRO como @image2 ──
                _s2_portrait_regen = story_data.get('character_preview', '').lstrip('/')
                if _s2_portrait_regen and os.path.exists(_s2_portrait_regen) and astro_ok_regen:
                    # Portrait FLUX disponible → mismo flujo que preview PASO 3
                    from services.personalized_books.age_profiles_nophoto import get_age_profile_nophoto as _ca_s2_nophoto_fn
                    _ca_s2_nophoto_profile, _ = _ca_s2_nophoto_fn(child_age_regen)
                    ca_s2_ref_note_regen = ca_build_ref_note_fn(
                        _ca_s2_nophoto_profile['display'], gender_word_regen,
                        _ca_s2_nophoto_profile['cover_ref'],
                        eye_desc_regen, outfit_desc_regen
                    )
                    photo_refs_regen = [_s2_portrait_regen, astro_path_regen]
                    print(f"[REGEN COVER CA S2] Portrait + ASTRO | portrait={_s2_portrait_regen} | astro={astro_ok_regen} | prompt_len={len(ca_s2_ref_note_regen)+len(ca_scene_regen)}")
                    cover_url_regen = generate_with_flux2_dev(
                        f"{ca_s2_ref_note_regen}\n{ca_scene_regen}",
                        aspect_ratio="3:4",
                        photo_ref_paths=photo_refs_regen,
                        image_prompt_strength=0.95,
                        negative_prompt=ca_neg_regen
                    )
                else:
                    # Fallback: sin portrait guardado → generación basada en texto + ASTRO como @image1
                    from services.fixed_stories import get_hair_description
                    from services.replicate_service import get_unified_skin_description
                    from services.personalized_books.centinela_aurora_prompts import get_hair_action as ca_get_hair_action
                    hair_desc_regen = get_hair_description(traits)
                    skin_regen = get_unified_skin_description(traits.get('skin_tone', 'light'))
                    hair_action_regen = ca_get_hair_action(traits)
                    ca_nophoto_ref_note_regen = (
                        "REFERENCE\n\n"
                        f"@image1 is the approved companion ASTRO — copy @image1 appearance exactly.\n\n"
                        f"MAIN CHARACTER\n\n"
                        f"Draw a single {gender_word_regen} of exactly {age_display_regen}.\n"
                        f"Maintain these exact age-specific anatomical proportions: {_ca_regen_age_body_desc}\n"
                        f"{hair_desc_regen}, {eye_desc_regen}, {skin_regen} skin, big joyful brave smile, {hair_action_regen}.\n"
                        f"OUTFIT: {outfit_desc_regen}."
                    )
                    ca_nophoto_regen = f"{ca_nophoto_ref_note_regen}\n{ca_scene_regen}"
                    photo_refs_regen = [astro_path_regen] if astro_ok_regen else None
                    print(f"[REGEN COVER CA S2 FALLBACK] Sin portrait guardado | astro={astro_ok_regen}")
                    cover_url_regen = generate_with_flux2_dev(
                        ca_nophoto_regen,
                        aspect_ratio="3:4",
                        photo_ref_paths=photo_refs_regen,
                        image_prompt_strength=0.85,
                        negative_prompt=ca_neg_regen
                    )

            cover_raw_path_regen = save_image_locally(cover_url_regen, f'{output_dir}/cover_raw.png')
            story_lang_regen = story_data.get('lang', story_data.get('story_lang', 'es'))
            from services.personalized_books.generation import get_print_title
            story_title_regen = get_print_title('centinela_aurora', child_name_regen, story_lang_regen)
            author_name_regen = story_data.get('author_name', '')
            cover_image_path_regen = create_cover_from_character(
                cover_raw_path_regen, output_dir,
                title=story_title_regen,
                author=author_name_regen if author_name_regen else ''
            )
            story_data['cover_image'] = f'/{cover_image_path_regen}'
            story_data['cover_raw_path'] = cover_raw_path_regen
            story_data['original_cover'] = f'/{cover_image_path_regen}'
            story_data['cover_regenerations'] = cover_regen_count + 1
            with open(preview_file, 'w', encoding='utf-8') as f:
                json.dump(story_data, f, ensure_ascii=False, indent=2)
            print(f"[REGEN COVER CA] Cover regenerated: {cover_image_path_regen}")

            # mark_composed=False: regeneration only, never a composition-
            # completion event — must not touch composition/approval state.
            if os.path.exists(f'generated/composed_{preview_id}'):
                import threading
                from services.personalized_books.rebuild import rebuild_book
                threading.Thread(target=rebuild_book, args=(preview_id,), kwargs={'mark_composed': False}, daemon=True).start()

            return jsonify({'success': True, 'cover_image': f'/{cover_image_path_regen}', 'regenerations_left': max(0, 2 - (cover_regen_count + 1))})

        elif story_id == 'magic_chef_illustrated':
            from services.personalized_books.magic_chef_prompts import (
                STYLE_BASE_COVER as CHEF_STYLE_BASE_COVER,
                FRONT_COVER as MC_REGEN_FRONT_COVER,
                get_outfit_desc as chef_get_outfit_desc,
                build_ref_note as chef_build_ref_note_fn,
                build_kontext_prompt as mc_build_kontext_regen,
                build_avatar_prompt as mc_build_avatar_regen,
            )
            from services.personalized_books.preview import generate_with_flux2_dev, generate_with_flux_kontext, _ensure_sweetie_reference
            from services.replicate_service import save_image_locally, create_cover_from_character, get_gender_negative_prompt

            gender_regen = story_data.get('gender', 'neutral')
            child_name_regen = story_data.get('child_name', '')
            child_age_regen = int(traits.get('child_age', 6))
            gender_word_regen = "boy" if gender_regen == "male" else "girl" if gender_regen == "female" else "child"
            age_display_regen = f"{child_age_regen} year old"
            outfit_desc_regen = chef_get_outfit_desc(gender_regen)
            human_photo_path_regen = traits.get('human_photo_path', '') or story_data.get('child_photo_path', '')
            sweetie_path_regen = _ensure_sweetie_reference()
            sweetie_ok_regen = sweetie_path_regen and os.path.exists(sweetie_path_regen)
            chef_neg_regen = get_gender_negative_prompt(gender_regen)
            from services.fixed_stories import get_eye_description as _mc_regen_eye_fn
            eye_desc_regen = _mc_regen_eye_fn(traits) if traits.get('eye_color') else ''
            chef_scene_regen = MC_REGEN_FRONT_COVER.get('prompt', '').replace('{style}', CHEF_STYLE_BASE_COVER)
            from services.age_profiles import get_age_profile as _mc_regen_age_fn
            _mc_regen_profile, _mc_regen_range_key = _mc_regen_age_fn(child_age_regen)
            _mc_regen_age_body_desc = _mc_regen_profile['kontext']
            print(f"[REGEN COVER CHEF] age={child_age_regen} range={_mc_regen_range_key} display={_mc_regen_profile['display']}")

            if human_photo_path_regen and os.path.exists(human_photo_path_regen):
                portrait_path_regen = None
                saved_portrait = story_data.get('character_preview', '')
                if saved_portrait:
                    saved_portrait_path = saved_portrait.lstrip('/')
                    if os.path.exists(saved_portrait_path):
                        portrait_path_regen = saved_portrait_path
                        print(f"[REGEN COVER CHEF] Reusing saved FLUX avatar: {portrait_path_regen}")
                if not portrait_path_regen:
                    kontext_prompt_regen = mc_build_kontext_regen(
                        age_display_regen, gender_word_regen, _mc_regen_age_body_desc, eye_desc_regen, outfit_desc_regen
                    )
                    print(f"[REGEN COVER CHEF] PASO 1 — Kontext | photo={human_photo_path_regen} | age={child_age_regen}")
                    portrait_url_regen = generate_with_flux_kontext(kontext_prompt_regen, human_photo_path_regen, aspect_ratio="3:4")
                    _kontext_path_regen = save_image_locally(portrait_url_regen, f'{output_dir}/chef_kontext_regen_{uuid.uuid4().hex[:8]}.png')
                    _av_neg_base = (
                        "text, watermark, signature, logo, letters, words, ugly, deformed, blurry, low quality, "
                        "distorted face, defined jawline, visible cheekbones, mature face, adult face, teenager, "
                        "wings on child, animal features on human, furry child, animal ears, extra limbs"
                    )
                    _av_neg_gender = (
                        "masculine features, boy haircut, male jawline" if gender_regen == "female"
                        else "girl features, ponytails, pigtails, feminine accessories, earrings, jewelry, bows, ribbons, makeup, lipstick"
                    )
                    avatar_prompt_regen = mc_build_avatar_regen(age_display_regen, gender_word_regen)
                    print(f"[REGEN COVER CHEF] PASO 2 — FLUX avatar | kontext={_kontext_path_regen}")
                    avatar_url_regen = generate_with_flux2_dev(
                        avatar_prompt_regen,
                        aspect_ratio="3:4",
                        photo_ref_path=_kontext_path_regen,
                        image_prompt_strength=0.95,
                        negative_prompt=_av_neg_base + ", " + _av_neg_gender,
                        force_go_fast=False,
                    )
                    portrait_path_regen = save_image_locally(avatar_url_regen, f'{output_dir}/chef_avatar_regen_{uuid.uuid4().hex[:8]}.png')
                    print(f"[REGEN COVER CHEF] PASO 2 — Avatar guardado: {portrait_path_regen}")

                from services.personalized_books.age_profiles_nophoto import get_age_profile_nophoto as _mc_regen_nophoto_fn
                _mc_regen_nophoto_profile, _ = _mc_regen_nophoto_fn(child_age_regen)
                chef_ref_note_regen = chef_build_ref_note_fn(
                    _mc_regen_nophoto_profile['display'], gender_word_regen,
                    _mc_regen_nophoto_profile['cover_ref'],
                    eye_desc_regen, outfit_desc_regen
                )
                photo_refs_regen = [portrait_path_regen, sweetie_path_regen] if sweetie_ok_regen else [portrait_path_regen]
                print(f"[REGEN COVER CHEF] PASO 3 — FLUX 2 Dev cover | portrait={portrait_path_regen} | sweetie={sweetie_ok_regen}")
                _chef_cover_neg = chef_neg_regen + ", text, watermark, logo, letters, words, title card, Disney logo, Pixar logo, branded text"
                cover_url_regen = generate_with_flux2_dev(
                    f"{chef_ref_note_regen}\n{chef_scene_regen}",
                    aspect_ratio="3:4",
                    photo_ref_paths=photo_refs_regen,
                    image_prompt_strength=0.95,
                    negative_prompt=_chef_cover_neg
                )
            else:
                _s2_portrait_regen = story_data.get('character_preview', '').lstrip('/')
                if _s2_portrait_regen and os.path.exists(_s2_portrait_regen) and sweetie_ok_regen:
                    from services.personalized_books.age_profiles_nophoto import get_age_profile_nophoto as _mc_s2_nophoto_fn
                    _mc_s2_nophoto_profile, _ = _mc_s2_nophoto_fn(child_age_regen)
                    mc_s2_ref_note_regen = chef_build_ref_note_fn(
                        _mc_s2_nophoto_profile['display'], gender_word_regen,
                        _mc_s2_nophoto_profile['cover_ref'],
                        eye_desc_regen, outfit_desc_regen
                    )
                    photo_refs_regen = [_s2_portrait_regen, sweetie_path_regen]
                    print(f"[REGEN COVER CHEF S2] Portrait + SWEETIE | portrait={_s2_portrait_regen} | sweetie={sweetie_ok_regen}")
                    _chef_cover_neg_s2 = chef_neg_regen + ", text, watermark, logo, letters, words, title card, Disney logo, Pixar logo, branded text"
                    cover_url_regen = generate_with_flux2_dev(
                        f"{mc_s2_ref_note_regen}\n{chef_scene_regen}",
                        aspect_ratio="3:4",
                        photo_ref_paths=photo_refs_regen,
                        image_prompt_strength=0.95,
                        negative_prompt=_chef_cover_neg_s2
                    )
                else:
                    from services.fixed_stories import get_hair_description as _mc_regen_hair_fn
                    from services.replicate_service import get_unified_skin_description as _mc_regen_skin_fn
                    hair_desc_regen = _mc_regen_hair_fn(traits)
                    skin_regen = _mc_regen_skin_fn(traits.get('skin_tone', 'light'))
                    mc_nophoto_ref_note_regen = (
                        f"@image1 = the rainbow cake companion — copy @image1 appearance exactly.\n\n"
                        f"Draw a single {gender_word_regen} of exactly {age_display_regen}.\n"
                        f"{hair_desc_regen}" + (f", {eye_desc_regen}" if eye_desc_regen else "") + f", {skin_regen} skin, confident joyful smile.\n"
                        f"OUTFIT: {outfit_desc_regen}."
                    )
                    photo_refs_regen = [sweetie_path_regen] if sweetie_ok_regen else None
                    print(f"[REGEN COVER CHEF S2 FALLBACK] Sin portrait guardado | sweetie={sweetie_ok_regen}")
                    _chef_cover_neg_fb = chef_neg_regen + ", text, watermark, logo, letters, words, title card, Disney logo, Pixar logo, branded text"
                    cover_url_regen = generate_with_flux2_dev(
                        f"{mc_nophoto_ref_note_regen}\n{chef_scene_regen}",
                        aspect_ratio="3:4",
                        photo_ref_paths=photo_refs_regen,
                        image_prompt_strength=0.85,
                        negative_prompt=_chef_cover_neg_fb
                    )

            cover_raw_path_regen = save_image_locally(cover_url_regen, f'{output_dir}/cover_raw.png')
            story_lang_regen = story_data.get('lang', story_data.get('story_lang', 'es'))
            from services.personalized_books.generation import get_print_title
            story_title_regen = get_print_title('magic_chef', child_name_regen, story_lang_regen)
            author_name_regen = story_data.get('author_name', '')
            cover_image_path_regen = create_cover_from_character(
                cover_raw_path_regen, output_dir,
                title=story_title_regen,
                author=author_name_regen if author_name_regen else ''
            )
            story_data['cover_image'] = f'/{cover_image_path_regen}'
            story_data['cover_raw_path'] = cover_raw_path_regen
            story_data['original_cover'] = f'/{cover_image_path_regen}'
            story_data['cover_regenerations'] = cover_regen_count + 1
            with open(preview_file, 'w', encoding='utf-8') as f:
                json.dump(story_data, f, ensure_ascii=False, indent=2)
            print(f"[REGEN COVER CHEF] Cover regenerated: {cover_image_path_regen}")

            if os.path.exists(f'generated/composed_{preview_id}'):
                import threading
                from services.personalized_books.rebuild import rebuild_book
                threading.Thread(target=rebuild_book, args=(preview_id,), kwargs={'mark_composed': False}, daemon=True).start()

            return jsonify({'success': True, 'cover_image': f'/{cover_image_path_regen}', 'regenerations_left': max(0, 2 - (cover_regen_count + 1))})

        elif story_id == 'magic_inventor_illustrated':
            from services.personalized_books.magic_inventor_prompts import (
                FRONT_COVER as MI_FRONT_COVER,
                STYLE_BASE as MI_STYLE_BASE,
                STYLE_BASE_COVER as MI_STYLE_BASE_COVER,
                get_outfit_desc as mi_get_outfit_desc,
                build_ref_note as mi_build_ref_note_fn,
                build_kontext_prompt as mi_build_kontext_fn,
                build_avatar_prompt as mi_build_avatar_fn,
            )
            from services.personalized_books.preview import generate_with_flux2_dev, generate_with_flux_kontext, _ensure_bolt_reference
            from services.replicate_service import save_image_locally, create_cover_from_character, get_gender_negative_prompt

            gender_regen = story_data.get('gender', 'neutral')
            child_name_regen = story_data.get('child_name', '')
            child_age_regen = int(traits.get('child_age', 5))
            gender_word_regen = "boy" if gender_regen == "male" else "girl" if gender_regen == "female" else "child"
            outfit_desc_regen = mi_get_outfit_desc(gender_regen)
            age_display_regen = f"{child_age_regen} year old"
            human_photo_path_regen = traits.get('human_photo_path') or story_data.get('child_photo_path', '')
            bolt_path_regen = _ensure_bolt_reference()
            bolt_ok_regen = bolt_path_regen and os.path.exists(bolt_path_regen)
            _mi_neg_base_regen = (
                "text, watermark, signature, logo, letters, words, ugly, deformed, blurry, low quality, "
                "distorted face, wings on child, animal features on human, furry child, "
                "animal ears, cat ears, bunny ears, fox ears, extra limbs"
            )
            mi_neg_regen = (_mi_neg_base_regen + ", masculine features, boy haircut") if gender_regen == 'female' else (_mi_neg_base_regen + ", earrings, jewelry, bows, ribbons, makeup, lipstick, feminine accessories, girl features, ponytails, pigtails") if gender_regen == 'male' else _mi_neg_base_regen
            mi_scene_regen = MI_FRONT_COVER.get('prompt', '').replace('{style}', MI_STYLE_BASE_COVER)
            from services.fixed_stories import get_eye_description as _mi_regen_eye_fn
            _mi_regen_eye_raw = traits.get('eye_color', '')
            eye_desc_regen = _mi_regen_eye_fn(traits) if _mi_regen_eye_raw else ''
            from services.age_profiles import get_age_profile as _mi_regen_age_fn
            _mi_regen_profile, _mi_regen_range_key = _mi_regen_age_fn(child_age_regen)
            _mi_regen_age_body_desc = _mi_regen_profile['kontext']
            print(f"[REGEN COVER MI] age={child_age_regen} range={_mi_regen_range_key}")

            if human_photo_path_regen and os.path.exists(human_photo_path_regen):
                portrait_path_regen = None
                saved_portrait = story_data.get('character_preview', '')
                if saved_portrait:
                    saved_portrait_path = saved_portrait.lstrip('/')
                    if os.path.exists(saved_portrait_path):
                        portrait_path_regen = saved_portrait_path
                        print(f"[REGEN COVER MI] Reusing saved FLUX avatar: {portrait_path_regen}")
                if not portrait_path_regen:
                    # ── PASO 1: Kontext — convierte foto → personaje 3D animado ──
                    kontext_prompt_regen = mi_build_kontext_fn(
                        age_display_regen, gender_word_regen, _mi_regen_age_body_desc, eye_desc_regen, outfit_desc_regen
                    )
                    print(f"[REGEN COVER MI] PASO 1 — Kontext | photo={human_photo_path_regen} | age={child_age_regen}")
                    portrait_url_regen = generate_with_flux_kontext(kontext_prompt_regen, human_photo_path_regen, aspect_ratio="3:4")
                    _kontext_path_regen = save_image_locally(portrait_url_regen, f'{output_dir}/mi_kontext_regen_{uuid.uuid4().hex[:8]}.png')
                    # ── PASO 2: FLUX Avatar — traduce Kontext al lenguaje visual FLUX nativo ──
                    _av_neg_base = (
                        "text, watermark, signature, logo, letters, words, ugly, deformed, blurry, low quality, "
                        "distorted face, defined jawline, visible cheekbones, mature face, adult face, teenager, "
                        "wings on child, animal features on human, furry child, animal ears, extra limbs"
                    )
                    _av_neg_gender = (
                        "masculine features, boy haircut, male jawline" if gender_regen == "female"
                        else "girl features, ponytails, pigtails, feminine accessories, earrings, jewelry, bows, ribbons, makeup, lipstick"
                    )
                    avatar_prompt_regen = mi_build_avatar_fn(age_display_regen, gender_word_regen)
                    print(f"[REGEN COVER MI] PASO 2 — FLUX avatar | kontext={_kontext_path_regen}")
                    avatar_url_regen = generate_with_flux2_dev(
                        avatar_prompt_regen,
                        aspect_ratio="3:4",
                        photo_ref_path=_kontext_path_regen,
                        image_prompt_strength=0.95,
                        negative_prompt=_av_neg_base + ", " + _av_neg_gender,
                        force_go_fast=False,
                    )
                    portrait_path_regen = save_image_locally(avatar_url_regen, f'{output_dir}/mi_avatar_regen_{uuid.uuid4().hex[:8]}.png')
                    print(f"[REGEN COVER MI] PASO 2 — Avatar guardado: {portrait_path_regen}")

                # ── PASO 3: FLUX 2 Dev Cover — ref_note from prompt file (single source of truth) ──
                mi_ref_note_regen = mi_build_ref_note_fn(age_display_regen, gender_word_regen, '', '', '')
                photo_refs_regen = [portrait_path_regen, bolt_path_regen] if bolt_ok_regen else [portrait_path_regen]
                print(f"[REGEN COVER MI] PASO 3 — FLUX 2 Dev cover | portrait={portrait_path_regen} | bolt={bolt_ok_regen}")
                cover_url_regen = generate_with_flux2_dev(
                    f"{mi_ref_note_regen}\n{mi_scene_regen}",
                    aspect_ratio="3:4",
                    photo_ref_paths=photo_refs_regen,
                    image_prompt_strength=0.95,
                    negative_prompt=mi_neg_regen
                )
            else:
                # ── SISTEMA 2 (sin foto): portrait guardado + BOLT como @image2 ──
                _s2_portrait_regen = story_data.get('character_preview', '').lstrip('/')
                if _s2_portrait_regen and os.path.exists(_s2_portrait_regen) and bolt_ok_regen:
                    mi_s2_ref_note_regen = mi_build_ref_note_fn(age_display_regen, gender_word_regen, '', '', '')
                    photo_refs_regen = [_s2_portrait_regen, bolt_path_regen]
                    print(f"[REGEN COVER MI S2] Portrait + BOLT | portrait={_s2_portrait_regen} | bolt={bolt_ok_regen}")
                    cover_url_regen = generate_with_flux2_dev(
                        f"{mi_s2_ref_note_regen}\n{mi_scene_regen}",
                        aspect_ratio="3:4",
                        photo_ref_paths=photo_refs_regen,
                        image_prompt_strength=0.95,
                        negative_prompt=mi_neg_regen
                    )
                else:
                    # Fallback: texto + BOLT como @image1
                    from services.fixed_stories import get_hair_description, get_eye_description, get_hair_strict
                    from services.replicate_service import get_unified_skin_description
                    from services.personalized_books.magic_inventor_prompts import get_hair_action as mi_get_hair_action
                    hair_desc_regen = get_hair_description(traits)
                    eye_desc_regen = get_eye_description(traits)
                    skin_regen = get_unified_skin_description(traits.get('skin_tone', 'light'))
                    hair_action_regen = mi_get_hair_action(traits)
                    hair_strict_regen = get_hair_strict(traits)
                    mi_nophoto_regen = (
                        f"@image1 = small copper robot companion BOLT — copy @image1 appearance exactly.\n"
                        f"Draw a single {gender_word_regen} ({age_display_regen}), {hair_desc_regen}, {eye_desc_regen}, {skin_regen} skin, "
                        f"big joyful curious smile, {hair_action_regen}. OUTFIT: {outfit_desc_regen}.\n"
                        f"ACTION: The {gender_word_regen} stands at the workshop entrance with mouth open in amazement, "
                        f"holding a glowing wrench up proudly. @image1 stands beside the {gender_word_regen} waving. "
                        f"SETTING: Magical inventor workshop WIDE VIEW, floating golden gears spinning, "
                        f"crystal tubes with colorful glowing liquids, workbenches with blueprints and gadgets, "
                        f"copper and golden tones, sparkles, centered composition for book cover. "
                        f"ATMOSPHERE: Adventure invitation, warm golden friendship and creativity. "
                        f"STRICT: Only ONE {gender_word_regen}, fully human child, no wings. {hair_strict_regen} "
                        f"Pure illustration only. {MI_STYLE_BASE}"
                    )
                    photo_refs_regen = [bolt_path_regen] if bolt_ok_regen else None
                    print(f"[REGEN COVER MI S2 FALLBACK] Sin portrait guardado | bolt={bolt_ok_regen}")
                    cover_url_regen = generate_with_flux2_dev(
                        mi_nophoto_regen,
                        aspect_ratio="3:4",
                        photo_ref_paths=photo_refs_regen,
                        image_prompt_strength=0.85,
                        negative_prompt=mi_neg_regen
                    )

            cover_raw_path_regen = save_image_locally(cover_url_regen, f'{output_dir}/cover_raw.png')
            story_lang_regen = story_data.get('lang', story_data.get('story_lang', 'es'))
            from services.personalized_books.generation import get_print_title
            story_title_regen = get_print_title('magic_inventor', child_name_regen, story_lang_regen)
            author_name_regen = story_data.get('author_name', '')
            cover_image_path_regen = create_cover_from_character(
                cover_raw_path_regen, output_dir,
                title=story_title_regen,
                author=author_name_regen if author_name_regen else ''
            )
            story_data['cover_image'] = f'/{cover_image_path_regen}'
            story_data['cover_raw_path'] = cover_raw_path_regen
            story_data['original_cover'] = f'/{cover_image_path_regen}'
            story_data['cover_regenerations'] = cover_regen_count + 1
            with open(preview_file, 'w', encoding='utf-8') as f:
                json.dump(story_data, f, ensure_ascii=False, indent=2)
            print(f"[REGEN COVER MI] Cover regenerated: {cover_image_path_regen}")

            if os.path.exists(f'generated/composed_{preview_id}'):
                import threading
                from services.personalized_books.rebuild import rebuild_book
                threading.Thread(target=rebuild_book, args=(preview_id,), kwargs={'mark_composed': False}, daemon=True).start()

            return jsonify({'success': True, 'cover_image': f'/{cover_image_path_regen}', 'regenerations_left': max(0, 2 - (cover_regen_count + 1))})

        else:
            return jsonify({'success': False, 'error': 'Cover regeneration only available for furry_love, star_keeper, dragon_garden, centinela_aurora, magic_chef and magic_inventor stories'}), 400
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/regenerate-cover/<preview_id>', methods=['POST'])
def admin_regenerate_cover(preview_id):
    """Admin-only: regenerate the cover for a preview/paid book. No regen limit. Reuses regenerate_cover() logic."""
    if not check_admin_auth():
        return jsonify({'success': False, 'error': 'No autorizado'}), 401
    return regenerate_cover(preview_id)

@app.route('/baby-story-preview/<preview_id>')
def baby_story_preview(preview_id):
    """Redirect to unified story preview flow"""
    return redirect(f'/story-preview-limited/{preview_id}')

@app.route('/api/generate-fixed-story', methods=['POST'])
def generate_fixed_story_api():
    """Generate fixed story (baby 0-1 or kids 3-5) - uses static illustrations if available"""
    try:
        data = request.get_json()

        if not data.get('admin_gift'):
            pass  # Story generation is always free — no rate limit, no lead save here

        from services.fixed_stories import prepare_story, STORIES, get_static_illustrations
        
        story_id = data.get('story_id', 'baby_soft_world')
        child_name = data.get('child_name', 'Child')
        child_gender = data.get('gender', 'neutral')
        story_age_range_gen = STORIES.get(story_id, {}).get('age_range', '0-1')
        default_age_gen = '5' if story_age_range_gen in ['3-5', '3-8', '5-7', '5-8', '6-7', '6-8'] else '1'
        child_age = data.get('child_age', default_age_gen)
        author_name = data.get('author_name', '')
        dedication = data.get('dedication', f'For {child_name},\nwith all our love.')
        story_lang = data.get('story_lang', get_lang())
        traits = {
            'hair_color': data.get('hair_color', 'brown'),
            'hair_type': data.get('hair_type', 'straight'),
            'hair_length': data.get('hair_length', 'medium'),
            'eye_color': data.get('eye_color', 'brown'),
            'skin_tone': data.get('skin_tone', 'light'),
            'child_age': str(child_age),
            'gender': child_gender,
            'glasses': data.get('glasses', '')
        }
        
        is_furry_love = (story_id in ('furry_love_illustrated', 'furry_love_adventure_illustrated', 'furry_love_teen_illustrated', 'furry_love_adult_illustrated'))
        if is_furry_love:
            traits['pet_name'] = data.get('pet_name', 'Buddy')
            traits['pet_desc'] = data.get('pet_desc', '')
            traits['pet_species'] = data.get('pet_species', 'dog')
            traits['facial_hair'] = data.get('facial_hair', 'none')
            traits['glasses'] = data.get('glasses', 'none')
            traits['body_build'] = data.get('body_build', 'average')
            raw_human_desc = data.get('human_desc', '')
            if not raw_human_desc:
                from services.fixed_stories import get_hair_description as ghd_fl, get_eye_description as ged_fl
                from services.replicate_service import get_unified_skin_description as gusd_fl
                hd_hair = ghd_fl(traits)
                hd_eye = ged_fl(traits)
                hd_skin = gusd_fl(traits.get('skin_tone', 'light'))
                age_val_hd = int(child_age) if str(child_age).isdigit() else 5
                if story_id == 'furry_love_illustrated':
                    gw_hd = "baby boy" if child_gender == "male" else "baby girl" if child_gender == "female" else "baby"
                elif story_id == 'furry_love_teen_illustrated':
                    gw_hd = "teenage boy" if child_gender == "male" else "teenage girl" if child_gender == "female" else "teenager"
                elif story_id == 'furry_love_adult_illustrated':
                    gw_hd = "man" if child_gender == "male" else "woman" if child_gender == "female" else "person"
                else:
                    gw_hd = "boy" if child_gender == "male" else "girl" if child_gender == "female" else "child"
                raw_human_desc = f"a {gw_hd} ({age_val_hd} year old), {hd_hair}, {hd_eye}, {hd_skin} skin"
            facial_hair_map = {'stubble': 'light stubble', 'short_beard': 'short beard', 'full_beard': 'full thick beard', 'mustache': 'mustache'}
            fh = traits['facial_hair']
            if fh and fh != 'none' and fh in facial_hair_map:
                raw_human_desc += f", with {facial_hair_map[fh]}"
            gl = traits['glasses']
            if gl and gl != 'none':
                raw_human_desc += f", wearing {gl}"
            bb = traits['body_build']
            if bb and bb != 'average':
                raw_human_desc += f", {bb} build"
            traits['human_desc'] = raw_human_desc
        
        character_image = data.get('character_image', '')
        if character_image and character_image.startswith('/'):
            character_image = character_image[1:]
        kontext_portrait = data.get('kontext_portrait', '')
        if kontext_portrait and kontext_portrait.startswith('/'):
            kontext_portrait = kontext_portrait[1:]
        
        pet_image = data.get('pet_image', '') if is_furry_love else ''
        if pet_image and pet_image.startswith('/'):
            pet_image = pet_image[1:]
        
        human_preview_path = data.get('human_preview_path', '') if is_furry_love else ''
        if human_preview_path and human_preview_path.startswith('/'):
            human_preview_path = human_preview_path[1:]
        pet_preview_path = data.get('pet_preview_path', '') if is_furry_love else ''
        if pet_preview_path and pet_preview_path.startswith('/'):
            pet_preview_path = pet_preview_path[1:]
        
        story_config = STORIES.get(story_id, {})
        age_range = story_config.get('age_range', '0-1')
        is_illustrated_book = story_config.get('use_fixed_scenes', False)
        
        static_data = get_static_illustrations(story_id)
        
        if is_illustrated_book:
            from services.personalized_books.generation import get_personalized_book_id
            book_id = get_personalized_book_id(story_id)
            
            print(f"[PERSONALIZED BOOK MODE] Preview-only flow for {story_id} (scenes after payment)")
            
            output_dir = f'generated/personalized_{uuid.uuid4().hex[:8]}'
            os.makedirs(output_dir, exist_ok=True)
            
            from services.replicate_service import create_cover_from_character
            from services.fixed_stories import STORIES as FIXED_STORIES_COVER_PB
            story_cfg_pb = FIXED_STORIES_COVER_PB.get(story_id, {})
            title_key_pb = f'title_{story_lang}' if story_lang in ['es', 'en'] else 'title_en'
            story_title_pb = story_cfg_pb.get(title_key_pb, story_cfg_pb.get('title_en', ''))
            lo_la_pb = "la" if child_gender == "female" else "lo"
            hisher_pb = "her" if child_gender == "female" else ("his" if child_gender == "male" else "their")
            pet_name_for_title = traits.get('pet_name', '') if is_furry_love else ''
            story_title_pb = story_title_pb.replace('{name}', child_name).replace('{lo_la}', lo_la_pb).replace('{hisher}', hisher_pb).replace('{pet_name}', pet_name_for_title)
            
            if is_furry_love and human_preview_path and pet_preview_path:
                if story_id == 'furry_love_adventure_illustrated':
                    from services.personalized_books.furry_love_adventure_prompts import FRONT_COVER, build_scene_prompt
                elif story_id == 'furry_love_teen_illustrated':
                    from services.personalized_books.furry_love_teen_prompts import FRONT_COVER, build_scene_prompt
                elif story_id == 'furry_love_adult_illustrated':
                    from services.personalized_books.furry_love_adult_prompts import FRONT_COVER, build_scene_prompt
                else:
                    from services.personalized_books.furry_love_prompts import FRONT_COVER, build_scene_prompt
                from services.personalized_books.preview import generate_with_flux2_dev
                from services.replicate_service import save_image_locally
                from services.fixed_stories import get_hair_description, get_eye_description
                
                human_desc = traits.get('human_desc', '')
                pet_desc_cover = traits.get('pet_desc', '')
                pet_name_cover = traits.get('pet_name', 'Buddy')
                eye_desc_cover = get_eye_description(traits) if traits.get('eye_color') else ''
                age_val = int(child_age) if str(child_age).isdigit() else 5
                if story_id == 'furry_love_illustrated':
                    gender_word_cover = "baby boy" if child_gender == "male" else "baby girl" if child_gender == "female" else "baby"
                    age_display_cover = f"{age_val} month old baby" if age_val < 2 else f"{age_val} year old toddler"
                elif story_id == 'furry_love_adventure_illustrated':
                    gender_word_cover = "boy" if child_gender == "male" else "girl" if child_gender == "female" else "person"
                    age_display_cover = f"{age_val} year old child"
                elif story_id == 'furry_love_teen_illustrated':
                    gender_word_cover = "boy" if child_gender == "male" else "girl" if child_gender == "female" else "teenager"
                    age_display_cover = f"{age_val} year old teenager"
                else:
                    gender_word_cover = "man" if child_gender == "male" else "woman" if child_gender == "female" else "adult"
                    age_display_cover = f"{age_val} year old adult"
                
                glasses_cover = traits.get('glasses', 'none')
                _hair_color_map_cv = {'black': 'jet black', 'brown': 'medium brown', 'light_brown': 'warm light brown (caramel-honey tone)', 'blonde': 'dark dirty blonde', 'very_light_blonde': 'pale platinum blonde', 'red': 'bright red', 'auburn': 'auburn'}
                hair_color_cover = _hair_color_map_cv.get(traits.get('hair_color', 'brown'), traits.get('hair_color', 'brown'))
                cover_prompt = build_scene_prompt(FRONT_COVER, human_desc, pet_name_cover, pet_desc_cover, age_display=age_display_cover, eye_desc=eye_desc_cover, gender_word=gender_word_cover, glasses=glasses_cover, hair_color=hair_color_cover)
                
                print(f"[FURRY LOVE COVER] Generating cover with both characters using FLUX 2 Dev + references")
                cover_url = generate_with_flux2_dev(
                    cover_prompt, 
                    aspect_ratio="3:4",
                    photo_ref_paths=[human_preview_path, pet_preview_path],
                    image_prompt_strength=0.90
                )
                cover_raw_path = save_image_locally(cover_url, f'{output_dir}/cover_raw.png')
                
                cover_image_path = create_cover_from_character(
                    cover_raw_path, output_dir,
                    title=story_title_pb,
                    author=author_name if author_name else ''
                )
                print(f"[FURRY LOVE COVER] Cover with both characters generated: {cover_image_path}")
            elif character_image and os.path.exists(character_image):
                cover_image_path = create_cover_from_character(
                    character_image, output_dir,
                    title=story_title_pb,
                    author=author_name if author_name else ''
                )
                print(f"[PERSONALIZED BOOK] Added title+author overlay to cover preview: {cover_image_path}")
                if story_id == 'centinela_aurora_illustrated':
                    cover_raw_path = character_image
                    print(f"[CENTINELA AURORA PREVIEW] cover_raw_path saved: {cover_raw_path}")
                elif story_id == 'magic_chef_illustrated':
                    cover_raw_path = character_image
                    print(f"[MAGIC CHEF PREVIEW] cover_raw_path saved: {cover_raw_path}")
                elif story_id == 'dragon_garden_illustrated':
                    cover_raw_path = character_image
                    print(f"[DRAGON GARDEN PREVIEW] cover_raw_path saved: {cover_raw_path}")
            else:
                cover_image_path = character_image if character_image else ''
            scene_paths = []
            scenes_pending = True
            is_illustrated_book_mode = True
        elif static_data['has_static']:
            print(f"[STATIC MODE] Using pre-generated illustrations for {story_id}")
            scene_paths = static_data['scenes']
            cover_image_path = static_data['cover'] or static_data['character_preview']
            is_illustrated_book_mode = False
            output_dir = f'static/story_illustrations/{story_id}'
            scenes_pending = False
        else:
            from services.replicate_service import generate_cover_only, create_cover_from_character
            from services.quick_stories.checkout import ALL_QUICK_FAMILY_IDS as QS_IDS
            
            is_qs = story_id in QS_IDS
            
            from services.fixed_stories import STORIES as FIXED_STORIES_COVER
            story_cfg_cover = FIXED_STORIES_COVER.get(story_id, {})
            cover_age_range = story_cfg_cover.get('age_range', '0-1')
            is_baby_cover = cover_age_range in ['0-1', '0-2']
            has_ideogram = story_cfg_cover.get('use_ideogram_scenes', False) and is_baby_cover
            use_flux_dev_cover = is_qs and not has_ideogram
            
            output_dir = f'generated/story_{uuid.uuid4().hex[:8]}'
            os.makedirs(output_dir, exist_ok=True)
            
            result = generate_cover_only(
                story_id, child_gender, traits, output_dir,
                base_character_path=character_image if character_image else None,
                child_name=child_name,
                use_flux_dev=use_flux_dev_cover
            )
            cover_image_path = result.get('cover')
            
            if is_qs and cover_image_path and os.path.exists(cover_image_path):
                import shutil
                from services.fixed_stories import STORIES as FIXED_STORIES
                story_cfg = FIXED_STORIES.get(story_id, {})
                use_preview_as_cover = story_cfg.get('use_preview_as_cover', False)
                
                cover_clean_path = f"{output_dir}/cover_clean.png"
                from PIL import Image as PILClean
                _clean_img = PILClean.open(cover_image_path).convert("RGB")
                _clean_img.save(cover_clean_path, "PNG")
                del _clean_img
                
                title_key = f'title_{story_lang}' if story_lang in ['es', 'en'] else 'title_en'
                story_title = story_cfg.get(title_key, story_cfg.get('title_en', ''))
                lo_la = "la" if child_gender == "female" else "lo"
                hisher = "her" if child_gender == "female" else ("his" if child_gender == "male" else "their")
                story_title = story_title.replace('{name}', child_name).replace('{lo_la}', lo_la).replace('{hisher}', hisher)
                
                cover_image_path = create_cover_from_character(
                    cover_clean_path, output_dir,
                    title=story_title,
                    author=author_name if author_name else ''
                )
                if use_preview_as_cover:
                    print(f"[COVER] Preview used directly as cover with text overlay: {cover_image_path}")
                else:
                    print(f"[COVER] Added text overlay to FLUX 2 Dev cover: {cover_image_path}")
            
            print(f"[POST-PAYMENT FLOW] Quick Story {story_id}: cover only, scenes will generate after payment")
            scene_paths = []
            scenes_pending = True
            is_illustrated_book_mode = False
        
        # Prepare story data
        from services.fixed_stories import prepare_story, get_story_text, get_closing_message
        story_data = prepare_story(story_id, child_name, child_gender, traits, lang=story_lang)
        
        extra_text_vars = {}
        if is_furry_love:
            extra_text_vars['pet_name'] = traits.get('pet_name', '')
        if story_id.startswith('birthday_celebration'):
            child_age_val = int(traits.get('child_age', '3'))
            extra_text_vars['child_age'] = child_age_val
            extra_text_vars['candle_plural'] = 's' if child_age_val != 1 else ''
            extra_text_vars['candle_plural_en'] = 's' if child_age_val != 1 else ''
        story_texts = get_story_text(story_id, child_name, gender=child_gender, lang=story_lang, **extra_text_vars)
        
        closing_message = get_closing_message(story_id, child_name, lang=story_lang) or ''
        
        # Check if this is a paid regeneration
        is_paid_regeneration = session.get('paid_customer', False)
        original_preview_id = session.get('original_preview_id', '')
        
        # Generate preview ID
        preview_id = uuid.uuid4().hex[:12]
        
        # Format image paths for templates (ensure they start with /)
        # For watermarked preview mode, use preview_scene_paths for display
        if 'preview_scene_paths' in dir() and preview_scene_paths:
            formatted_preview_paths = []
            formatted_original_paths = []
            for p in preview_scene_paths:
                if p:
                    path = p if p.startswith('/') else f'/{p}'
                    formatted_preview_paths.append(path)
            for p in scene_paths:
                if p:
                    path = p if p.startswith('/') else f'/{p}'
                    formatted_original_paths.append(path)
            formatted_scene_paths = formatted_preview_paths
            original_scene_paths_formatted = formatted_original_paths
        else:
            formatted_scene_paths = []
            for p in scene_paths:
                if p:
                    path = p if p.startswith('/') else f'/{p}'
                    formatted_scene_paths.append(path)
            original_scene_paths_formatted = formatted_scene_paths
        
        # Cover paths - use watermarked for preview if available
        formatted_cover = None
        original_cover = None
        if 'cover_preview_path' in dir() and cover_preview_path:
            formatted_cover = cover_preview_path if cover_preview_path.startswith('/') else f'/{cover_preview_path}'
            original_cover = cover_image_path if cover_image_path.startswith('/') else f'/{cover_image_path}'
        elif cover_image_path:
            formatted_cover = cover_image_path if cover_image_path.startswith('/') else f'/{cover_image_path}'
            original_cover = formatted_cover
        elif character_image:
            formatted_cover = character_image if character_image.startswith('/') else f'/{character_image}'
            original_cover = formatted_cover
        
        # Prepare preview data
        story_title = story_data.get('title', '')
        preview_data = {
            'story_id': story_id,
            'title': story_title,
            'story_name': story_title,
            'child_name': child_name,
            'gender': child_gender,
            'author_name': author_name,
            'dedication': dedication,
            'traits': traits,
            'pages': story_data.get('pages', []),
            'story_texts': story_texts,
            'scene_paths': formatted_scene_paths,
            'images': formatted_scene_paths,
            'original_scene_paths': original_scene_paths_formatted,
            'original_images': original_scene_paths_formatted,
            'cover_image': formatted_cover,
            'original_cover': original_cover,
            'output_dir': output_dir,
            'image_dir': output_dir,
            'age_range': age_range,
            'lang': story_lang,
            'scenes_pending': scenes_pending,
            'is_illustrated_book': is_illustrated_book_mode,
            'scenes_dir': story_config.get('scenes_dir', '') if is_illustrated_book_mode else '',
            'character_preview': (kontext_portrait if (story_id in ('star_keeper_illustrated', 'dragon_garden_illustrated', 'centinela_aurora_illustrated', 'magic_chef_illustrated', 'magic_inventor_illustrated') and kontext_portrait and os.path.exists(kontext_portrait)) else character_image) if (kontext_portrait or character_image) else '',
            'closing_image': (f'/{closing_image_path}' if closing_image_path and not closing_image_path.startswith('/') else closing_image_path) if 'closing_image_path' in dir() and closing_image_path else '',
            'text_layout': story_data.get('text_layout', 'single'),
            'closing_message': closing_message
        }
        
        if is_furry_love:
            preview_data['is_furry_love'] = True
            preview_data['pet_name'] = traits.get('pet_name', '')
            preview_data['pet_desc'] = traits.get('pet_desc', '')
            preview_data['human_desc'] = traits.get('human_desc', '')
            if 'cover_raw_path' in dir() and cover_raw_path and os.path.exists(cover_raw_path):
                preview_data['cover_raw_path'] = cover_raw_path
            if human_preview_path:
                preview_data['human_preview_path'] = human_preview_path
        if story_id in ('centinela_aurora_illustrated', 'magic_chef_illustrated'):
            if 'cover_raw_path' in dir() and cover_raw_path and os.path.exists(cover_raw_path):
                preview_data['cover_raw_path'] = cover_raw_path
                print(f"[{story_id.upper()} PREVIEW] cover_raw_path stored in story_data: {cover_raw_path}")
        if is_furry_love:
            if pet_preview_path:
                preview_data['pet_preview_path'] = pet_preview_path
            if pet_image:
                preview_data['pet_preview'] = pet_image if pet_image.startswith('/') else f'/{pet_image}'
            upload_prefix_fl = 'generated/uploads/furry_photos/'
            human_photo = data.get('human_photo_path', '')
            pet_photo = data.get('pet_photo_path', '')
            if human_photo and human_photo.startswith(upload_prefix_fl) and os.path.exists(human_photo):
                preview_data['human_photo_path'] = human_photo
            if pet_photo and pet_photo.startswith(upload_prefix_fl) and os.path.exists(pet_photo):
                preview_data['pet_photo_path'] = pet_photo
        
        if is_illustrated_book_mode:
            upload_prefix_ub = 'generated/uploads/furry_photos/'
            child_photo = data.get('child_photo_path', '')
            if child_photo and child_photo.startswith(upload_prefix_ub) and os.path.exists(child_photo):
                preview_data['child_photo_path'] = child_photo
                print(f"[FIXED-STORY] Universos child photo uploaded: {child_photo}")
        
        if 'personalized_book_generated' in dir() and personalized_book_generated:
            preview_data['pages_composed'] = True
            preview_data['personalized_book_generated'] = True
            if 'cover_spread_path' in dir() and cover_spread_path:
                preview_data['cover_spread_path'] = cover_spread_path
            if 'back_cover_path' in dir() and back_cover_path:
                preview_data['back_cover_path'] = f'/{back_cover_path}'
            if 'back_cover_preview_path' in dir() and back_cover_preview_path:
                preview_data['back_cover_preview'] = f'/{back_cover_preview_path}'
        
        if is_paid_regeneration:
            preview_data['paid'] = True
            preview_data['regeneration_used'] = True
            preview_data['original_preview_id'] = original_preview_id
            preview_data['customer_email'] = session.get('customer_email', '')
            preview_data['customer_phone'] = session.get('customer_phone', '')
            preview_data['want_print'] = session.get('want_print', False)
            session.pop('paid_customer', None)
            session.pop('original_preview_id', None)
        
        if data.get('admin_gift'):
            preview_data['admin_gift'] = True
            preview_data['paid'] = True
            preview_data['payment_status'] = 'admin_gift'
            preview_data['generation_complete'] = True
            preview_data['scenes_pending'] = True
            preview_data['want_print'] = True
            preview_data['shipping_address'] = {
                'name': data.get('child_name', 'Admin Gift'),
                'street1': 'Admin Office',
                'city': 'Digital',
                'state': 'MM',
                'postcode': '00000',
                'country': 'US'
            }
            preview_data['shipping_method'] = 'MAIL'
            preview_data['customer_email'] = data.get('admin_gift_email', 'admin@magicmemoriesbooks.com')
            preview_data['admin_gift_email'] = preview_data['customer_email']
            # Show cover+text preview first — admin enters email and clicks "Generar Libro Gratis"
            # which calls /admin/generate-free/ to trigger scene generation
            preview_url = f'/story-preview-limited/{preview_id}'
        else:
            preview_url = f'/story-preview-limited/{preview_id}'
        
        # Ensure we don't have double slashes if the domain already ends with one
        base_url = os.environ.get('SITE_DOMAIN', os.environ.get('REPLIT_DEV_DOMAIN', 'magicmemoriesbooks.com'))
        if base_url.endswith('/'):
            base_url = base_url[:-1]
            
        os.makedirs('story_previews', exist_ok=True)
        with open(f'story_previews/{preview_id}.json', 'w', encoding='utf-8') as f:
            json.dump(preview_data, f, ensure_ascii=False, indent=2)
        
        if is_paid_regeneration:
            return jsonify({
                'success': True,
                'preview_url': f'/order-complete/{preview_id}',
                'preview_id': preview_id
            })
        
        return jsonify({
            'success': True,
            'preview_url': preview_url,
            'preview_id': preview_id
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        error_str = str(e)
        if 'q_descale' in error_str or 'FLUX' in error_str or 'CUDA' in error_str or 'ModelError' in error_str:
            lang = request.form.get('language', request.form.get('lang', 'es'))
            if lang == 'es':
                user_error = 'El servicio de ilustraciones está temporalmente ocupado. Por favor intenta de nuevo en unos minutos.'
            else:
                user_error = 'The illustration service is temporarily busy. Please try again in a few minutes.'
        else:
            user_error = error_str
        return jsonify({'success': False, 'error': user_error}), 500

@app.route('/fixed-story-preview/<preview_id>')
def fixed_story_preview(preview_id):
    """Redirect to unified story preview flow"""
    return redirect(f'/story-preview-limited/{preview_id}')

@app.route('/story-preview-limited/<preview_id>')
def story_preview_limited(preview_id):
    """Limited preview page - shows cover + text only, before payment"""
    preview_file = f'story_previews/{preview_id}.json'
    if not os.path.exists(preview_file):
        return redirect(url_for('index'))
    
    with open(preview_file, 'r', encoding='utf-8') as f:
        story_data = json.load(f)
    
    # If story is already paid and scenes aren't still generating, go straight to order-complete
    _already_paid = story_data.get('paid', False) or story_data.get('payment_status') == 'admin_gift'
    _scenes_pending = story_data.get('scenes_pending', False) or story_data.get('scenes_generating', False)
    if _already_paid and not _scenes_pending:
        return redirect(url_for('order_complete', preview_id=preview_id))
    
    return render_template('story_preview_limited.html',
                          preview_id=preview_id,
                          story_data=story_data)

@app.route('/ebook-preview/<preview_id>')
def ebook_preview(preview_id):
    """Redirect old ebook preview to new visor"""
    preview_file = f'story_previews/{preview_id}.json'
    if os.path.exists(preview_file):
        with open(preview_file, 'r', encoding='utf-8') as f:
            story_data = json.load(f)
        visor_url = story_data.get('visor_url', '')
        if visor_url:
            return redirect(visor_url)
    return redirect(url_for('index'))

@app.route('/story-preview-full/<preview_id>')
def story_preview_full(preview_id):
    """Full preview page - shows all pages with front cover, interior, and back cover"""
    preview_file = f'story_previews/{preview_id}.json'
    if not os.path.exists(preview_file):
        return redirect(url_for('index'))
    
    with open(preview_file, 'r', encoding='utf-8') as f:
        story_data = json.load(f)
    
    full_preview = []
    is_paid_val = story_data.get('paid', False) or story_data.get('payment_status') == 'admin_gift' or story_data.get('admin_gift') == True
    
    if is_paid_val:
        front_cover = story_data.get('original_cover') or story_data.get('front_cover_path') or story_data.get('cover_preview')
        interior_pages = story_data.get('original_images') or story_data.get('original_scene_paths') or story_data.get('all_pages_original') or story_data.get('images', [])
    else:
        front_cover = story_data.get('cover_preview') or story_data.get('cover_image') or story_data.get('original_cover')
        interior_pages = story_data.get('all_pages_preview') or story_data.get('images', [])
    
    if front_cover:
        full_preview.append(front_cover)
    
    full_preview.extend(interior_pages)
    
    # Use book-specific fixed back cover if available, otherwise fall back to dynamic or generic
    _bid_preview = story_data.get('story_id', story_data.get('book_id', ''))
    _fixed_back_covers_preview = {
        "dragon_garden": "static/images/fixed_pages/_backup/dragon_garden_back_cover.png",
        "magic_chef": "static/images/fixed_pages/magic_chef_back_cover.png",
        "magic_inventor": "static/images/fixed_pages/magic_inventor_back_cover.png",
        "star_keeper": "static/images/fixed_pages/_backup/star_keeper_back_cover.png",
        "furry_love": "static/images/fixed_pages/_backup/furry_love_baby_back_cover.png",
        "furry_love_adventure": "static/images/fixed_pages/_backup/furry_love_adventure_back_cover.png",
        "furry_love_teen": "static/images/fixed_pages/_backup/furry_love_teen_back_cover.png",
        "furry_love_adult": "static/images/fixed_pages/_backup/furry_love_adult_back_cover.png",
        "centinela_aurora": "static/images/fixed_pages/_backup/centinela_aurora_back_cover.png",
        "centinela_aurora_illustrated": "static/images/fixed_pages/_backup/centinela_aurora_back_cover.png",
    }
    _book_specific_back = _fixed_back_covers_preview.get(_bid_preview)
    if _book_specific_back and os.path.exists(_book_specific_back):
        full_preview.append('/' + _book_specific_back)
        has_back_cover = True
    elif os.path.exists('static/images/fixed_pages/back_cover.png'):
        full_preview.append('/static/images/fixed_pages/back_cover.png')
        has_back_cover = True
    else:
        back_cover = story_data.get('back_cover_preview') or story_data.get('back_cover_path')
        if back_cover:
            full_preview.append(back_cover)
        has_back_cover = back_cover is not None
    
    has_front_cover = front_cover is not None
    
    story_data['images'] = full_preview
    story_data['total_pages'] = len(full_preview)
    story_data['has_front_cover'] = has_front_cover
    story_data['has_back_cover'] = has_back_cover
    
    return render_template('story_preview_full.html',
                          preview_id=preview_id,
                          story_data=story_data)

@app.route('/story-checkout/<preview_id>')
def story_checkout(preview_id):
    """Unified checkout page for all product types"""
    preview_file = f'story_previews/{preview_id}.json'
    if not os.path.exists(preview_file):
        return redirect(url_for('index'))
    
    with open(preview_file, 'r', encoding='utf-8') as f:
        story_data = json.load(f)
    
    # If story is already paid, redirect directly to order-complete
    _already_paid = story_data.get('paid', False) or story_data.get('payment_status') == 'admin_gift'
    if _already_paid:
        return redirect(url_for('order_complete', preview_id=preview_id))
    
    story_id = story_data.get('story_id', '')
    test_mode = request.args.get('test') == '1'
    lang = get_lang()
    
    from services.quick_stories.checkout import ALL_QUICK_FAMILY_IDS
    from services.personalized_books.checkout import PERSONALIZED_BOOK_IDS
    
    _is_universos = story_id in PERSONALIZED_BOOK_IDS
    ebook_config = {
        'allow_ebook': True,
        'ebook_base_price': Config.UNIVERSOS_EBOOK_PRICE // 100 if _is_universos else Config.EBOOK_BASE_PRICE // 100,
        'ebook_product_type': 'ebook',
    }
    
    if story_id in ALL_QUICK_FAMILY_IDS:
        checkout_config = {
            'product_type': 'quick_story',
            'allow_digital': True,
            'allow_print': True,
            'digital_base_price': Config.QS_DIGITAL_BASE_PRICE // 100,
            'print_base_price': Config.QS_PRINT_BASE_PRICE // 100,
            'digital_product_type': 'qs_digital',
            'print_product_type': 'qs_print',
            'product_description': 'PDF digital + PDF imprimible' if lang == 'es' else 'Digital PDF + printable PDF',
            'print_description_es': 'Libro engrapado a color',
            'print_description_en': 'Color saddle stitch book',
            'print_book_image': '/static/images/book_express_real.jpg',
            'print_book_spec_es': 'Tapa blanda · 16 páginas (incluye 2 de pintar)',
            'print_book_spec_en': 'Softcover · 16 pages (includes 2 coloring)',
            **ebook_config,
        }
    elif story_id in PERSONALIZED_BOOK_IDS:
        checkout_config = {
            'product_type': 'personalized',
            'allow_digital': False,
            'allow_pdf': True,
            'allow_print': True,
            'pdf_base_price': Config.PERSONALIZED_PDF_PRICE // 100,
            'pdf_product_type': 'personalized_pdf',
            'pdf_description_es': 'PDF de alta resolución para imprimir en casa o copistería (28 págs). Entrega por email.',
            'pdf_description_en': 'High-res PDF to print at home or a copy shop (28 pages). Email delivery.',
            'print_base_price': Config.CP_PB_BASE_PRICE // 100,
            'print_product_type': 'cp_personalized',
            'product_description': '28 páginas, 19 ilustraciones, tapa dura' if lang == 'es' else '28 pages, 19 illustrations, hardcover',
            'print_description_es': 'Libro tapa dura A4 (impreso y enviado por Cloudprinter)',
            'print_description_en': 'A4 hardcover book (printed & shipped by Cloudprinter)',
            'print_book_image': '/static/images/book_fotomagic_real.jpg',
            'print_book_spec_es': 'Tapa dura · 24 páginas (incluye 2 de pintar)',
            'print_book_spec_en': 'Hardcover · 24 pages (includes 2 coloring)',
            **ebook_config,
        }
    else:
        checkout_config = {
            'product_type': 'personalized',
            'allow_digital': True,
            'allow_print': True,
            'digital_base_price': Config.PERSONALIZED_BASE_PRICE // 100,
            'print_base_price': Config.PERSONALIZED_BASE_PRICE // 100,
            'digital_product_type': 'personalized',
            'print_product_type': 'personalized_print',
            'product_description': 'PDF digital' if lang == 'es' else 'Digital PDF',
            'print_description_es': 'Libro tapa dura',
            'print_description_en': 'Hardcover book',
            **ebook_config,
        }
    
    from services.cloudprinter_api_service import CLOUDPRINTER_AVAILABLE_COUNTRIES
    _cp_countries = sorted(CLOUDPRINTER_AVAILABLE_COUNTRIES)

    return render_template('checkout_unified.html',
                          preview_id=preview_id,
                          story_data=story_data,
                          paypal_client_id=Config.PAYPAL_CLIENT_ID,
                          checkout_config=checkout_config,
                          test_mode=test_mode,
                          excluded_countries=[],
                          cp_countries=_cp_countries)

def correct_spelling(text: str, language: str = 'es') -> str:
    """
    Correct spelling and grammar in dedication text using OpenAI.
    Preserves the original meaning and tone.
    """
    if not text or len(text.strip()) < 3:
        return text
    
    try:
        from openai import OpenAI
        client = OpenAI()
        
        lang_name = "Spanish" if language == 'es' else "English"
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"You are a spelling and grammar corrector for {lang_name} text. "
                               f"Fix only spelling mistakes and obvious grammar errors. "
                               f"Keep the original meaning, tone, and style exactly the same. "
                               f"Do not add or remove content. Do not translate. "
                               f"Return ONLY the corrected text, nothing else."
                },
                {
                    "role": "user",
                    "content": text
                }
            ],
            temperature=0,
            max_tokens=500
        )
        
        corrected = response.choices[0].message.content.strip()
        print(f"[SPELLING] Original: {text[:50]}...")
        print(f"[SPELLING] Corrected: {corrected[:50]}...")
        return corrected
        
    except Exception as e:
        print(f"[SPELLING] Error correcting text: {e}")
        return text


@app.route('/api/update-story-data/<preview_id>', methods=['POST'])
def update_story_data(preview_id):
    """Update dedication and author for a story"""
    preview_file = f'story_previews/{preview_id}.json'
    if not os.path.exists(preview_file):
        return jsonify({'success': False, 'error': 'Story not found'}), 404
    
    data = request.get_json()
    
    with open(preview_file, 'r', encoding='utf-8') as f:
        story_data = json.load(f)
    
    lang = story_data.get('lang', 'es')
    
    if 'dedication' in data:
        original_dedication = data['dedication']
        corrected_dedication = correct_spelling(original_dedication, lang)
        story_data['dedication'] = corrected_dedication
        story_data['dedication_original'] = original_dedication
    if 'author' in data:
        story_data['author_name'] = data['author']
    
    with open(preview_file, 'w', encoding='utf-8') as f:
        json.dump(story_data, f, ensure_ascii=False, indent=2)
    
    return jsonify({'success': True, 'corrected_dedication': story_data.get('dedication', '')})


@app.route('/api/validate-address', methods=['POST'])
def validate_address():
    """Address validation. For US addresses verifies ZIP via zippopotam.us and auto-corrects city/state."""
    import requests as _req
    data = request.get_json()
    if not data:
        return jsonify({'valid': False, 'message': 'No address data provided'}), 400

    cc = (data.get('country_code') or '').upper()
    postal = (data.get('postcode') or '').strip()
    data = dict(data)

    required_fields = ['name', 'street1', 'city', 'country_code']
    missing = [f for f in required_fields if not data.get(f)]
    if missing:
        return jsonify({'valid': False, 'message': f'Missing required fields: {", ".join(missing)}'})

    # ── Unified Nominatim (OpenStreetMap) validation — US + international ──────
    city = (data.get('city') or '').strip()
    _nm_headers = {'User-Agent': 'MagicMemoriesBooks/1.0 (checkout-address-validation)'}
    if city and postal:
        try:
            if cc == 'US':
                zip5 = ''.join(filter(str.isdigit, postal))[:5]
                if len(zip5) == 5:
                    rn = _req.get('https://nominatim.openstreetmap.org/search',
                                  params={'postalcode': zip5, 'country': 'US',
                                          'format': 'json', 'limit': 1, 'addressdetails': 1},
                                  headers=_nm_headers, timeout=6)
                    if rn.status_code == 200:
                        results = rn.json()
                        if results:
                            addr = results[0].get('address', {})
                            canon_city  = addr.get('city') or addr.get('town') or addr.get('village') or addr.get('county') or ''
                            iso_state   = addr.get('ISO3166-2-lvl4', '')
                            canon_state = iso_state.split('-')[-1] if '-' in iso_state else addr.get('state', '')
                            if canon_city:
                                data['postcode'] = zip5
                                if not (data.get('city') or '').strip():
                                    data['city'] = canon_city
                                if not (data.get('state_code') or '').strip():
                                    data['state_code'] = canon_state
                                city_ok  = (data.get('city') or '').lower() == canon_city.lower()
                                state_ok = (data.get('state_code') or '').upper() == canon_state.upper()
                                if not city_ok or not state_ok:
                                    suggested = dict(data)
                                    suggested['city']       = canon_city
                                    suggested['state_code'] = canon_state
                                    print(f'[VALIDATE-ADDRESS] Nominatim US: ZIP {zip5} → {canon_city}, {canon_state} (input: {data.get("city")}, {data.get("state_code")})')
                                    return jsonify({
                                        'valid': True,
                                        'auto_corrected': False,
                                        'suggested_address': suggested,
                                        'zip_city': canon_city,
                                        'zip_state': canon_state,
                                    })
                        else:
                            print(f'[VALIDATE-ADDRESS] Nominatim: ZIP {zip5} not found in US')
                            return jsonify({
                                'valid': True,
                                'warning': True,
                                'message': f'ZIP code {zip5} could not be verified. Please double-check.',
                                'message_es': f'El código postal {zip5} no pudo verificarse. Por favor revisa.',
                            })
            else:
                rn = _req.get('https://nominatim.openstreetmap.org/search',
                              params={'postalcode': postal, 'city': city, 'country': cc,
                                      'format': 'json', 'limit': 1, 'addressdetails': 0},
                              headers=_nm_headers, timeout=6)
                if rn.status_code == 200:
                    results = rn.json()
                    if isinstance(results, list) and len(results) == 0:
                        rp = _req.get('https://nominatim.openstreetmap.org/search',
                                      params={'postalcode': postal, 'country': cc,
                                              'format': 'json', 'limit': 1},
                                      headers=_nm_headers, timeout=5)
                        if rp.status_code == 200 and isinstance(rp.json(), list) and len(rp.json()) == 0:
                            print(f'[VALIDATE-ADDRESS] Nominatim: postal {postal} not found in {cc}')
                            return jsonify({
                                'valid': True, 'warning': True,
                                'message': f'Postal code {postal} may not be valid for {cc}. Please double-check.',
                                'message_es': f'El código postal {postal} puede no ser válido para {cc}. Por favor verifica.',
                            })
                        else:
                            print(f'[VALIDATE-ADDRESS] Nominatim: city "{city}" may not match postal {postal} in {cc}')
                            return jsonify({
                                'valid': True, 'warning': True,
                                'message': f'City "{city}" may not match postal code {postal}. Please verify your address.',
                                'message_es': f'La ciudad "{city}" puede no corresponder al código postal {postal}. Por favor verifica.',
                            })
                    else:
                        print(f'[VALIDATE-ADDRESS] Nominatim: {cc} {postal} {city} → OK')
        except Exception as _ne:
            print(f'[VALIDATE-ADDRESS] Nominatim lookup failed (fail-open): {_ne}')

    return jsonify({'valid': True, 'message': 'Address looks valid'})


@app.route('/api/qs-shipping-costs', methods=['POST'])
def get_qs_shipping_costs():
    """Get Cloudprinter shipping options for Quick Stories (A4 saddle-stitch, magazine_sas_a4_p_fc)."""
    from services.cloudprinter_api_service import get_shipping_quote
    data = request.get_json() or {}
    country_code = data.get('country_code', 'ES')
    state_code = data.get('state_code', '')
    options = get_shipping_quote(country_code, state_code=state_code)
    return jsonify(options)


@app.route('/api/calculate-dynamic-price', methods=['POST'])
def calculate_dynamic_price():
    """Calculate dynamic price for all product types.
    qs_print → Cloudprinter; cp_personalized → Cloudprinter casewrap; pdf → fixed price.
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    product_type = data.get('product_type', 'personalized')
    country_code = data.get('country_code', 'US')

    if product_type == 'qs_print':
        from services.cloudprinter_api_service import (
            get_shipping_quote, CLOUDPRINTER_AVAILABLE_COUNTRIES, COUNTRIES_NEEDING_STATE
        )
        base_price_dollars = Config.QS_PRINT_BASE_PRICE / 100.0
        state_code = data.get('state_code', '').strip().upper()
        cc = country_code.upper()

        if cc not in CLOUDPRINTER_AVAILABLE_COUNTRIES:
            return jsonify({
                'error': 'no_shipping_to_country',
                'message_es': 'No podemos enviar a este país. Puedes elegir el PDF imprimible.',
                'message_en': 'We cannot ship to this country. You can choose the printable PDF.',
                'options': {}
            }), 422

        if cc in COUNTRIES_NEEDING_STATE and state_code and len(state_code) > 3:
            return jsonify({
                'error': 'invalid_state_code',
                'message_es': 'Introduce el código de estado de 2 letras (ej: GA para Georgia, TX para Texas, CA para California).',
                'message_en': 'Please enter the 2-letter state code (e.g. GA for Georgia, TX for Texas, CA for California).',
                'options': {}
            }), 422

        cp_options = get_shipping_quote(cc, state_code=state_code)
        if not cp_options:
            return jsonify({
                'error': 'no_shipping_options',
                'message_es': 'No hay opciones de envío disponibles para este destino.',
                'message_en': 'No shipping options available for this destination.',
                'options': {}
            }), 422

        pricing_options = {}
        for uid, opt in cp_options.items():
            ship_usd = round(float(opt.get('cp_cost_usd', opt.get('total_usd', 15.0))), 2)
            total_usd = round(base_price_dollars + ship_usd, 2)
            pricing_options[uid] = {
                'name_es': opt.get('name_es', 'Envío Estándar'),
                'name_en': opt.get('name_en', 'Standard Shipping'),
                'days': opt.get('days_es', '7-15 días hábiles'),
                'days_es': opt.get('days_es', '7-15 días hábiles'),
                'days_en': opt.get('days_en', '7-15 business days'),
                'base_price': base_price_dollars,
                'cp_cost': ship_usd,
                'cp_cost_usd': ship_usd,
                'print_cost_usd': float(opt.get('print_cost_usd', 0)),
                'customer_total': total_usd,
                'customer_total_cents': int(total_usd * 100),
                'shipping_level': uid,
            }
        print(f"[DYNAMIC PRICE] qs_print (CP) to {cc}{' state=' + state_code if state_code else ''}: {list(pricing_options.keys())}")
        return jsonify({
            'product_type': product_type,
            'base_price': base_price_dollars,
            'country_code': cc,
            'options': pricing_options
        })
    elif product_type == 'personalized_pdf':
        pdf_price = Config.PERSONALIZED_PDF_PRICE / 100.0
        print(f"[DYNAMIC PRICE] personalized_pdf: fixed ${pdf_price}")
        return jsonify({
            'product_type': product_type,
            'base_price': pdf_price,
            'no_shipping': True,
            'options': {
                'pdf': {
                    'name_es': 'PDF Imprimible',
                    'name_en': 'Printable PDF',
                    'days_es': 'Entrega inmediata por email',
                    'days_en': 'Immediate email delivery',
                    'total': pdf_price,
                    'total_cents': int(pdf_price * 100),
                }
            }
        })
    elif product_type == 'cp_personalized':
        from services.cloudprinter_api_service import (
            get_pb_shipping_quote, CLOUDPRINTER_AVAILABLE_COUNTRIES, COUNTRIES_NEEDING_STATE
        )
        base_price_dollars = Config.CP_PB_BASE_PRICE / 100.0
        state_code = data.get('state_code', '').strip().upper()
        cc = country_code.upper()

        if cc not in CLOUDPRINTER_AVAILABLE_COUNTRIES:
            return jsonify({
                'error': 'no_shipping_to_country',
                'message_es': 'No podemos enviar a este país. Puedes elegir el PDF imprimible.',
                'message_en': 'We cannot ship to this country. You can choose the printable PDF.',
                'options': {}
            }), 422

        if cc in COUNTRIES_NEEDING_STATE and state_code and len(state_code) > 3:
            return jsonify({
                'error': 'invalid_state_code',
                'message_es': 'Introduce el código de estado de 2 letras (ej: GA para Georgia, TX para Texas, CA para California).',
                'message_en': 'Please enter the 2-letter state code (e.g. GA for Georgia, TX for Texas, CA for California).',
                'options': {}
            }), 422

        cp_options = get_pb_shipping_quote(cc, state_code=state_code)
        if not cp_options:
            return jsonify({
                'error': 'no_shipping_options',
                'message_es': 'No hay opciones de envío disponibles para este destino.',
                'message_en': 'No shipping options available for this destination.',
                'options': {}
            }), 422

        pricing_options = {}
        for uid, opt in cp_options.items():
            ship_usd   = round(float(opt.get('cp_cost_usd', opt.get('cp_cost_eur', 15.0))), 2)
            print_usd  = float(opt.get('print_cost_usd', opt.get('print_cost_eur', 0)))
            total_usd  = round(base_price_dollars + ship_usd, 2)
            pricing_options[uid] = {
                'name_es':             opt.get('name_es', 'Envío Estándar'),
                'name_en':             opt.get('name_en', 'Standard Shipping'),
                'days':                opt.get('days_es', '7-15 días hábiles'),
                'days_es':             opt.get('days_es', '7-15 días hábiles'),
                'days_en':             opt.get('days_en', '7-15 business days'),
                'service':             opt.get('service', ''),
                'carrier':             opt.get('carrier', ''),
                'base_price':          base_price_dollars,
                'cp_cost':             ship_usd,
                'cp_cost_usd':         ship_usd,
                'print_cost_usd':      print_usd,
                'customer_total':      total_usd,
                'customer_total_cents': int(total_usd * 100),
                'shipping_level':      opt.get('shipping_level', uid),
            }
        print(f"[DYNAMIC PRICE] cp_personalized (CP) to {cc}: {list(pricing_options.keys())}")
        return jsonify({
            'product_type': product_type,
            'base_price': base_price_dollars,
            'country_code': cc,
            'options': pricing_options
        })
    else:
        return jsonify({'error': f'Unknown product_type: {product_type}'}), 400




@app.route('/api/cp-pb-quote', methods=['POST'])
def cp_pb_quote():
    """
    Return real-time Cloudprinter shipping options for the casewrap hardcover book.
    Accepts: {country_code: str}
    Returns: {book_base_price, country_code, options: {level: {name_es, name_en, days_es, days_en, ship_cost, total, total_cents}}}
    On failure: {error: str, options: {}}
    """
    from services.cloudprinter_api_service import get_pb_shipping_quote
    data = request.get_json() or {}
    country_code = (data.get('country_code') or 'US').upper().strip()

    book_base_price = Config.CP_PB_BASE_PRICE / 100.0
    cp_options = get_pb_shipping_quote(country_code)

    if not cp_options:
        print(f"[CP-PB QUOTE API] No options for {country_code}")
        return jsonify({
            'book_base_price': book_base_price,
            'country_code': country_code,
            'options': {},
            'error': 'no_options',
        }), 200

    options = {}
    for level, opt in cp_options.items():
        # cp_cost_eur is the shipping component returned by get_pb_shipping_quote()
        ship_cost = round(float(opt.get('cp_cost_eur', opt.get('ship_cost', 0))), 2)
        total = round(book_base_price + ship_cost, 2)
        options[level] = {
            'name_es': opt.get('name_es', level),
            'name_en': opt.get('name_en', level),
            'days_es': opt.get('days_es', ''),
            'days_en': opt.get('days_en', ''),
            'cp_cost_eur': ship_cost,
            'ship_cost': ship_cost,
            'book_base_price': book_base_price,
            'total': total,
            'total_cents': int(total * 100),
        }

    print(f"[CP-PB QUOTE API] {country_code}: {list(options.keys())}")
    return jsonify({
        'book_base_price': book_base_price,
        'country_code': country_code,
        'options': options,
    })


def _get_paypal_access_token():
    import requests as req
    import base64
    credentials = base64.b64encode(f"{Config.PAYPAL_CLIENT_ID}:{Config.PAYPAL_CLIENT_SECRET}".encode()).decode()
    resp = req.post(
        f"{Config.PAYPAL_API_BASE}/v1/oauth2/token",
        headers={"Authorization": f"Basic {credentials}", "Content-Type": "application/x-www-form-urlencoded"},
        data="grant_type=client_credentials",
        timeout=15
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


@app.route('/api/request-coupon', methods=['POST'])
def api_request_coupon():
    from services.email_service import send_coupon_email
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    lang = data.get('lang') or session.get('lang', 'es')
    if not name or not email:
        return jsonify({'error': 'name and email required'}), 400
    try:
        existing = CouponLead.query.filter_by(email=email).first()
        if existing:
            return jsonify({'success': True, 'already_sent': True})
        lead = CouponLead(name=name, email=email, ip_address=request.remote_addr)
        db.session.add(lead)
        db.session.commit()
        send_coupon_email(name=name, email=email, code='MAGIC15', discount_pct=15, lang=lang)
        return jsonify({'success': True, 'already_sent': False})
    except Exception as e:
        print(f"[COUPON] request-coupon error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/validate-coupon', methods=['POST'])
def api_validate_coupon():
    data = request.get_json() or {}
    code = data.get('code', '').strip().upper()
    buyer_email = data.get('buyer_email', '').strip().lower()
    lang = data.get('lang', 'es')
    if not code:
        return jsonify({'valid': False, 'error': 'No code provided'}), 400
    try:
        coupon = Coupon.query.filter_by(code=code, is_active=True).first()
        if not coupon:
            return jsonify({'valid': False, 'error': 'Invalid or inactive code'})
        max_uses = coupon.max_uses or 0
        use_count = coupon.use_count or 0
        if max_uses > 0 and use_count >= max_uses:
            return jsonify({'valid': False, 'error': 'Code has reached maximum uses'})
        if buyer_email:
            if coupon.coupon_type == 'open':
                # Open/public promotional codes: no lead required, no per-email restriction
                pass
            elif coupon.coupon_type in ('influencer', 'referral'):
                # Block if any usage exists (pending or paid)
                already_used = CouponUsage.query.filter_by(coupon_code=code, buyer_email=buyer_email).first()
                if already_used:
                    msg = ('This code has already been used with this email' if lang == 'en' else 'Este código ya fue utilizado con este email')
                    return jsonify({'valid': False, 'error': msg})
                # Pre-register now to lock the email before payment completes
                pending = CouponUsage(
                    coupon_code=code,
                    buyer_email=buyer_email,
                    paypal_order_id=None,
                    discount_pct=coupon.discount_pct or 0
                )
                coupon.use_count = (coupon.use_count or 0) + 1
                db.session.add(pending)
                db.session.commit()
                print(f"[COUPON] Pre-registered usage: {code} by {buyer_email}")
            else:
                # General coupon (e.g. MAGIC15): must have been requested from homepage first
                lead = CouponLead.query.filter_by(email=buyer_email).first()
                if not lead:
                    msg = ('This coupon is exclusive for those who requested it on our homepage. Get it free at magicmemoriesbooks.com'
                           if lang == 'en' else
                           'Este cupón es exclusivo para quienes lo solicitaron en nuestra página principal. Pídelo gratis en magicmemoriesbooks.com')
                    return jsonify({'valid': False, 'error': msg})
                # Block if a completed purchase already exists with this email
                already_purchased = CouponUsage.query.filter(
                    CouponUsage.coupon_code == code,
                    CouponUsage.buyer_email == buyer_email,
                    CouponUsage.paypal_order_id != None  # noqa
                ).first()
                if already_purchased:
                    msg = ('You have already used this coupon for a purchase' if lang == 'en' else 'Ya compraste un cuento con este cupón')
                    return jsonify({'valid': False, 'error': msg})
        return jsonify({'valid': True, 'discount_pct': coupon.discount_pct or 0, 'code': coupon.code})
    except Exception as e:
        print(f"[COUPON] validate-coupon error: {e}")
        return jsonify({'valid': False, 'error': str(e)}), 500


@app.route('/api/paypal/create-order', methods=['POST'])
def paypal_create_order():
    import requests as req
    data = request.get_json() or {}

    is_cart_mode = data.get('source') == 'cart'

    if is_cart_mode:
        from services.cart import cart_summary, cart_get_items
        country_code = data.get('country_code', session.get('cart_country', ''))
        summary = cart_summary(session, country_code)
        if not summary['item_count']:
            return jsonify({'error': 'Cart is empty'}), 400
        if summary.get('has_physical') and not country_code:
            return jsonify({'error': 'shipping_country_required'}), 400
        final_amount = summary['total']
        if final_amount < 0.01:
            return jsonify({'error': 'Invalid cart total'}), 400
        cart_snapshot = [dict(it) for it in cart_get_items(session)]
        session['cart_expected_total'] = final_amount
        session['cart_order_country'] = country_code
        session['cart_snapshot'] = cart_snapshot
        session.modified = True
        try:
            token = _get_paypal_access_token()
            final_amount = round(float(final_amount), 2)  # Force exactly 2 decimals — PayPal rejects more
            purchase_unit = {
                "amount": {"currency_code": "USD", "value": f"{final_amount:.2f}"},
                "description": f"Magic Memories Books — {summary['item_count']} item(s)"
            }
            order_payload = {
                "intent": "CAPTURE",
                "purchase_units": [purchase_unit],
                "application_context": {
                    "brand_name": "Magic Memories Books",
                    "shipping_preference": "NO_SHIPPING"
                }
            }
            resp = req.post(
                f"{Config.PAYPAL_API_BASE}/v2/checkout/orders",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json=order_payload,
                timeout=15
            )
            resp_data = resp.json()
            print(f"[PAYPAL-CART] create-order: ${final_amount} for {summary['item_count']} items ({country_code})")
            resp.raise_for_status()
            session['cart_paypal_order_id'] = resp_data['id']
            session.modified = True
            return jsonify({'id': resp_data['id']})
        except Exception as e:
            print(f"[PAYPAL-CART] create-order error: {e}")
            return jsonify({'error': str(e)}), 500

    amount_usd = data.get('amount_usd')
    if not amount_usd:
        return jsonify({'error': 'amount_usd required'}), 400
    try:
        token = _get_paypal_access_token()

        total_amount = round(float(amount_usd), 2)
        # base_price_usd = platform fee only (excludes Lulu printing/shipping)
        # If not provided, fall back to full amount (backwards compat)
        base_price_usd = data.get('base_price_usd')
        platform_fee = round(float(base_price_usd), 2) if base_price_usd else total_amount
        lulu_cost = max(round(total_amount - platform_fee, 2), 0.0)

        coupon_code = data.get('coupon_code', '').strip().upper()
        if coupon_code:
            coupon = Coupon.query.filter_by(code=coupon_code, is_active=True).first()
            if coupon:
                _max = coupon.max_uses or 0
                _used = coupon.use_count or 0
                if _max == 0 or _used < _max:
                    # Apply discount ONLY to platform fee, never to Lulu printing/shipping
                    discount = round(platform_fee * (coupon.discount_pct or 0) / 100, 2)
                    discounted_platform = max(round(platform_fee - discount, 2), 1.0)
                    total_amount = discounted_platform + lulu_cost

        final_amount = round(total_amount, 2)  # Force exactly 2 decimals — PayPal rejects more

        purchase_unit = {
            "amount": {"currency_code": "USD", "value": f"{final_amount:.2f}"},
            "description": "Magic Memories Books"
        }

        order_payload = {
            "intent": "CAPTURE",
            "purchase_units": [purchase_unit],
            "application_context": {
                "brand_name": "Magic Memories Books",
                "shipping_preference": "NO_SHIPPING"
            }
        }

        resp = req.post(
            f"{Config.PAYPAL_API_BASE}/v2/checkout/orders",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json=order_payload,
            timeout=15
        )
        resp_data = resp.json()
        print(f"[PAYPAL] create-order payload: {order_payload}")
        print(f"[PAYPAL] create-order response ({resp.status_code}): {resp_data}")
        resp.raise_for_status()
        return jsonify({'id': resp_data['id']})
    except Exception as e:
        print(f"[PAYPAL] create-order error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/paypal/capture-order', methods=['POST'])
def paypal_capture_order():
    import requests as req
    data = request.get_json() or {}
    order_id = data.get('orderID')
    if not order_id:
        return jsonify({'error': 'orderID required'}), 400
    if data.get('source') == 'cart':
        from services.cart import cart_get_items
        stored_order_id = session.get('cart_paypal_order_id')
        if stored_order_id and order_id != stored_order_id:
            print(f"[CART-SECURITY] Pre-capture order ID mismatch: submitted={order_id}, stored={stored_order_id}")
            session.pop('cart_paypal_order_id', None)
            session.pop('cart_snapshot', None)
            session.pop('cart_expected_total', None)
            session.modified = True
            return jsonify({'error': 'Order ID does not match initiated payment', 'code': 'ORDER_MISMATCH'}), 409
        cart_snapshot_pre = session.get('cart_snapshot')
        if cart_snapshot_pre is not None:
            current_ids_pre = {it['id'] for it in cart_get_items(session)}
            snapshot_ids_pre = {it['id'] for it in cart_snapshot_pre}
            if current_ids_pre != snapshot_ids_pre:
                print(f"[CART-SECURITY] Pre-capture cart mismatch: snapshot={snapshot_ids_pre}, current={current_ids_pre}")
                session.pop('cart_paypal_order_id', None)
                session.pop('cart_snapshot', None)
                session.pop('cart_expected_total', None)
                session.modified = True
                return jsonify({'error': 'Cart changed since payment was initiated', 'code': 'CART_MISMATCH'}), 409
    try:
        token = _get_paypal_access_token()
        resp = req.post(
            f"{Config.PAYPAL_API_BASE}/v2/checkout/orders/{order_id}/capture",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            timeout=15
        )
        resp.raise_for_status()
        capture_data = resp.json()
        status = capture_data.get('status')
        if status != 'COMPLETED':
            return jsonify({'error': f'Payment not completed: {status}'}), 400
        payer_email = capture_data.get('payer', {}).get('email_address', '')
        # Extract the actual captured amount from PayPal response
        try:
            _cap_pu = capture_data.get('purchase_units', [{}])[0]
            _cap_captures = _cap_pu.get('payments', {}).get('captures', [{}])
            captured_amount_usd = float(_cap_captures[0].get('amount', {}).get('value', 0)) if _cap_captures else 0.0
        except Exception:
            captured_amount_usd = 0.0
        try:
            _captured_capture_id = _cap_captures[0].get('id', '') if _cap_captures else ''
            _captured_payer_country = capture_data.get('payer', {}).get('address', {}).get('country_code', '')
        except Exception:
            _captured_capture_id = ''
            _captured_payer_country = ''
        print(f"[PAYPAL] Order {order_id} captured. Payer: {payer_email}. Amount: ${captured_amount_usd:.2f}")
        coupon_code = data.get('coupon_code', '').strip().upper()
        buyer_email = data.get('buyer_email', '').strip().lower() or payer_email
        if coupon_code:
            try:
                coupon = Coupon.query.filter_by(code=coupon_code).first()
                if coupon:
                    # For influencer/referral: usage was pre-registered at validate time,
                    # just update the paypal_order_id on the existing pending record
                    if coupon.coupon_type in ('influencer', 'referral') and buyer_email:
                        existing = CouponUsage.query.filter_by(
                            coupon_code=coupon_code,
                            buyer_email=buyer_email,
                            paypal_order_id=None
                        ).first()
                        if existing:
                            existing.paypal_order_id = order_id
                            db.session.commit()
                            print(f"[COUPON] Updated pre-registered usage: {coupon_code} by {buyer_email}")
                        else:
                            # Fallback: create new record
                            db.session.add(CouponUsage(
                                coupon_code=coupon_code, buyer_email=buyer_email,
                                paypal_order_id=order_id, discount_pct=coupon.discount_pct or 0
                            ))
                            db.session.commit()
                    else:
                        # General coupon: create usage record now
                        usage = CouponUsage(
                            coupon_code=coupon_code,
                            buyer_email=buyer_email,
                            paypal_order_id=order_id,
                            discount_pct=coupon.discount_pct or 0
                        )
                        coupon.use_count = (coupon.use_count or 0) + 1
                        db.session.add(usage)
                        db.session.commit()
                    print(f"[COUPON] Usage confirmed: {coupon_code} by {buyer_email} order={order_id}")
            except Exception as ce:
                print(f"[COUPON] Error recording usage: {ce}")

        if data.get('source') == 'cart':
            from services.cart import cart_get_items, cart_clear, cart_summary
            country_code = session.get('cart_order_country', data.get('country_code', ''))
            shipping_address = data.get('shipping_address') or None
            expected_total = session.get('cart_expected_total')
            cart_snapshot = session.get('cart_snapshot')
            if not cart_snapshot and not cart_get_items(session):
                print(f"[CART-SECURITY] Cart empty and no snapshot at capture — possible session loss, order_id={order_id}")
                return jsonify({'error': 'Cart session not found. Please try again or contact support.', 'code': 'SESSION_MISSING'}), 409
            integrity_warnings = []
            if expected_total is not None:
                captured_amount = 0.0
                try:
                    pu = capture_data.get('purchase_units', [{}])[0] if capture_data else {}
                    captured_amount = float(pu.get('amount', {}).get('value', 0))
                except Exception:
                    pass
                if captured_amount > 0 and abs(captured_amount - float(expected_total)) > 0.05:
                    msg = f"[CART-SECURITY] Amount mismatch: captured ${captured_amount}, expected ${expected_total} — order_id={order_id}"
                    print(msg)
                    integrity_warnings.append(msg)
            if cart_snapshot is not None:
                current_ids_post = {it['id'] for it in cart_get_items(session)}
                snapshot_ids_post = {it['id'] for it in cart_snapshot}
                if current_ids_post != snapshot_ids_post:
                    msg = f"[CART-SECURITY] Post-capture cart mismatch: snapshot={snapshot_ids_post}, current={current_ids_post} — order_id={order_id}"
                    print(msg)
                    integrity_warnings.append(msg)
            cart_items_for_fulfillment = cart_snapshot if cart_snapshot else cart_get_items(session)
            amount_mismatch_warning = "; ".join(integrity_warnings) if integrity_warnings else None
            summary = cart_summary(session, country_code)
            total_usd = expected_total if expected_total else summary['total']
            try:
                _c0 = capture_data.get('purchase_units', [{}])[0].get('payments', {}).get('captures', [{}])[0]
                _cart_payment_data = {
                    'amount_paid': captured_amount_usd,
                    'currency': _c0.get('amount', {}).get('currency_code', 'USD'),
                    'capture_id': _c0.get('id', ''),
                    'payer_country': capture_data.get('payer', {}).get('address', {}).get('country_code', ''),
                }
            except Exception:
                _cart_payment_data = {'amount_paid': captured_amount_usd, 'currency': 'USD'}
            # Enriquecer con datos económicos para persistencia en JSON
            _fmt_type_map = {
                'ebook': 'ebook', 'universo_ebook': 'ebook',
                'qs_digital': 'digital',
                'qs_print': 'print', 'cp_personalized': 'print',
                'personalized_pdf': 'pdf',
            }
            _fp_cart = {}
            for _ci in cart_items_for_fulfillment:
                _fk = _fmt_type_map.get(_ci.get('product_type', ''))
                if _fk:
                    _fp_cart[_fk] = round(float(_ci.get('price', 0)), 2)
            _cart_subtotal = round(summary.get('subtotal', 0), 2)
            _cart_shipping = round(summary.get('shipping', 0), 2)
            _cart_disc_raw = round(_cart_subtotal + _cart_shipping - captured_amount_usd, 2) if captured_amount_usd > 0 else 0.0
            _cart_disc = _cart_disc_raw if _cart_disc_raw > 0.015 else 0.0
            _cart_payment_data['format_prices'] = _fp_cart
            _cart_payment_data['shipping_cost_usd'] = _cart_shipping
            _cart_payment_data['discount_amount'] = _cart_disc
            _cart_payment_data['coupon_code'] = coupon_code or ''
            fulfilled_items = []
            failed_items = []
            for item in cart_items_for_fulfillment:
                try:
                    _item_payment_data = {**_cart_payment_data, 'product_type': item.get('product_type', '')}
                    dispatched = _dispatch_cart_item(item, buyer_email, order_id, shipping_address=shipping_address, payment_data=_item_payment_data)
                    if dispatched:
                        fulfilled_items.append({**item, 'paypal_order_id': order_id})
                    else:
                        print(f"[CART] Item {item.get('id')} dispatch returned False — skipping from fulfilled list")
                        failed_items.append({'id': item.get('id'), 'product_type': item.get('product_type'), 'reason': 'dispatch_false'})
                except Exception as item_err:
                    print(f"[CART] Error dispatching item {item.get('id')}: {item_err}")
                    failed_items.append({'id': item.get('id'), 'product_type': item.get('product_type'), 'reason': str(item_err)})
            if failed_items or amount_mismatch_warning:
                try:
                    from services.email_service import send_admin_notification_email
                    lines = [f"PayPal Order: {order_id}", f"Buyer: {buyer_email}", ""]
                    if amount_mismatch_warning:
                        lines.append(f"WARNING: {amount_mismatch_warning}")
                        lines.append("")
                    if failed_items:
                        lines.append(f"FULFILLMENT FAILURES ({len(failed_items)} items):")
                        for fi in failed_items:
                            lines.append(f"  - id={fi['id']} type={fi['product_type']} reason={fi['reason']}")
                    send_admin_notification_email(subject=f"[CART ALERT] Fulfillment issue order {order_id}", body="\n".join(lines))
                except Exception as notify_err:
                    print(f"[CART] Admin notification failed: {notify_err}")
            session['last_cart_order'] = {
                'items': fulfilled_items,
                'buyer_email': buyer_email,
                'paypal_order_id': order_id,
                'total_usd': total_usd,
                'lang': session.get('lang', 'es'),
            }
            session.pop('cart_expected_total', None)
            session.pop('cart_order_country', None)
            session.pop('cart_snapshot', None)
            session.pop('cart_paypal_order_id', None)
            session.modified = True
            cart_clear(session)
            t_email = threading.Thread(
                target=_send_cart_order_email,
                args=(buyer_email, fulfilled_items, total_usd, session.get('lang', 'es')),
                daemon=True
            )
            t_email.start()
            lang = session.get('lang', 'es')
            return jsonify({'success': True, 'redirect_url': f'/cart/success?lang={lang}'})

        return jsonify({'success': True, 'orderID': order_id, 'payer_email': payer_email, 'status': status, 'captured_amount_usd': captured_amount_usd, 'capture_id': _captured_capture_id, 'payer_country': _captured_payer_country})
    except Exception as e:
        print(f"[PAYPAL] capture-order error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/cart')
def cart_page():
    from services.cart import cart_summary
    lang = get_lang()
    country_code = request.args.get('country', session.get('cart_country', ''))
    if country_code:
        session['cart_country'] = country_code
    summary = cart_summary(session, country_code)
    countries = [
        ('AL', 'Albania', 'Albania'), ('DE', 'Alemania', 'Germany'), ('AR', 'Argentina', 'Argentina'),
        ('AU', 'Australia', 'Australia'), ('AT', 'Austria', 'Austria'), ('BE', 'Bélgica', 'Belgium'),
        ('BO', 'Bolivia', 'Bolivia'), ('BR', 'Brasil', 'Brazil'), ('BG', 'Bulgaria', 'Bulgaria'),
        ('CA', 'Canadá', 'Canada'), ('CL', 'Chile', 'Chile'), ('CO', 'Colombia', 'Colombia'),
        ('CR', 'Costa Rica', 'Costa Rica'), ('HR', 'Croacia', 'Croatia'), ('CY', 'Chipre', 'Cyprus'),
        ('CZ', 'República Checa', 'Czech Republic'), ('DK', 'Dinamarca', 'Denmark'),
        ('EC', 'Ecuador', 'Ecuador'), ('SV', 'El Salvador', 'El Salvador'),
        ('ES', 'España', 'Spain'), ('US', 'Estados Unidos', 'United States'),
        ('EE', 'Estonia', 'Estonia'), ('FI', 'Finlandia', 'Finland'),
        ('FR', 'Francia', 'France'), ('GR', 'Grecia', 'Greece'), ('GT', 'Guatemala', 'Guatemala'),
        ('HN', 'Honduras', 'Honduras'), ('HU', 'Hungría', 'Hungary'), ('IE', 'Irlanda', 'Ireland'),
        ('IT', 'Italia', 'Italy'), ('JP', 'Japón', 'Japan'), ('LV', 'Letonia', 'Latvia'),
        ('LT', 'Lituania', 'Lithuania'), ('LU', 'Luxemburgo', 'Luxembourg'),
        ('MT', 'Malta', 'Malta'), ('MX', 'México', 'Mexico'), ('NO', 'Noruega', 'Norway'),
        ('NZ', 'Nueva Zelanda', 'New Zealand'), ('NL', 'Países Bajos', 'Netherlands'),
        ('PA', 'Panamá', 'Panama'), ('PY', 'Paraguay', 'Paraguay'), ('PE', 'Perú', 'Peru'),
        ('PL', 'Polonia', 'Poland'), ('PT', 'Portugal', 'Portugal'),
        ('GB', 'Reino Unido', 'United Kingdom'), ('DO', 'República Dominicana', 'Dominican Republic'),
        ('RO', 'Rumania', 'Romania'), ('SK', 'Eslovaquia', 'Slovakia'), ('SI', 'Eslovenia', 'Slovenia'),
        ('SE', 'Suecia', 'Sweden'), ('CH', 'Suiza', 'Switzerland'), ('TR', 'Turquía', 'Turkey'),
        ('UY', 'Uruguay', 'Uruguay'), ('VE', 'Venezuela', 'Venezuela'),
    ]
    cart_items = summary.pop('items', [])
    return render_template('cart.html',
        lang=lang,
        translations=TRANSLATIONS.get(lang, TRANSLATIONS['es']),
        summary=summary,
        cart_items=cart_items,
        countries=countries,
        paypal_client_id=Config.PAYPAL_CLIENT_ID,
    )


@app.route('/cart/success')
def cart_success():
    lang = request.args.get('lang', get_lang())
    order_data = session.get('last_cart_order', {})
    items = order_data.get('items', [])
    buyer_email = order_data.get('buyer_email', '')
    total_usd = order_data.get('total_usd', 0)
    return render_template('cart_success.html',
        lang=lang,
        translations=TRANSLATIONS.get(lang, TRANSLATIONS['es']),
        items=items,
        buyer_email=buyer_email,
        total_usd=total_usd,
    )


_CART_CANONICAL_PRICES = {
    'qs_digital': lambda _sid='': Config.QS_DIGITAL_BASE_PRICE / 100.0,
    'qs_print': lambda _sid='': Config.QS_PRINT_BASE_PRICE / 100.0,
    'personalized_pdf': lambda _sid='': Config.PERSONALIZED_PDF_PRICE / 100.0,
    'personalized': lambda _sid='': Config.PERSONALIZED_BASE_PRICE / 100.0,
    'universo_ebook': lambda _sid='': Config.UNIVERSOS_EBOOK_PRICE / 100.0,
    'ebook': None,  # price determined dynamically from story type — see api_cart_add
}


_PREVIEW_ID_RE = re.compile(r'^[A-Za-z0-9_-]{4,120}$')


@app.route('/api/cart/add', methods=['POST'])
def api_cart_add():
    from services.cart import cart_add_item, cart_count
    data = request.get_json() or {}
    preview_id = data.get('preview_id', '')
    product_type = data.get('product_type', '')
    if not preview_id or not product_type:
        return jsonify({'success': False, 'error': 'preview_id and product_type required'}), 400
    if not _PREVIEW_ID_RE.match(preview_id):
        return jsonify({'success': False, 'error': 'Invalid preview_id format'}), 400
    if product_type not in _CART_CANONICAL_PRICES:
        return jsonify({'success': False, 'error': f'Unknown product_type: {product_type}'}), 400
    preview_file = f'story_previews/{preview_id}.json'
    if not os.path.exists(preview_file):
        return jsonify({'success': False, 'error': 'Story preview not found'}), 404
    child_name = ''
    story_name = ''
    cover_image = ''
    story_id = ''
    lang = get_lang()
    story_data = {}
    try:
        with open(preview_file, 'r', encoding='utf-8') as f:
            story_data = json.load(f)
        child_name = story_data.get('child_name', '')
        story_name = story_data.get('story_name', '')
        cover_image = story_data.get('cover_image', '') or story_data.get('character_preview', '')
        story_id = story_data.get('story_id', '')
        lang = story_data.get('lang', lang)
    except Exception as e:
        return jsonify({'success': False, 'error': 'Could not read story preview'}), 500
    if product_type == 'ebook':
        from services.personalized_books.checkout import PERSONALIZED_BOOK_IDS as _PB_IDS
        base_price = Config.UNIVERSOS_EBOOK_PRICE / 100.0 if story_id in _PB_IDS else Config.EBOOK_BASE_PRICE / 100.0
    else:
        price_fn = _CART_CANONICAL_PRICES[product_type]
        base_price = price_fn()
    ebook_session_id = story_data.get('preview_id', preview_id) if story_data else preview_id
    item_id = cart_add_item(
        session, preview_id=preview_id, product_type=product_type,
        child_name=child_name, story_name=story_name, price=base_price,
        cover_image=cover_image, lang=lang, story_id=story_id,
        ebook_session_id=ebook_session_id
    )
    print(f"[CART] Added item {item_id}: {product_type} @ ${base_price} for preview {preview_id}")
    return jsonify({'success': True, 'item_id': item_id, 'item_count': cart_count(session)})


@app.route('/api/cart/remove/<item_id>', methods=['DELETE'])
def api_cart_remove(item_id):
    from services.cart import cart_remove_item, cart_count
    removed = cart_remove_item(session, item_id)
    return jsonify({'success': removed, 'item_count': cart_count(session)})


@app.route('/api/cart/summary')
def api_cart_summary():
    from services.cart import cart_summary
    country = request.args.get('country', session.get('cart_country', ''))
    if country:
        session['cart_country'] = country
    summary = cart_summary(session, country)
    discounts_applied = []
    if summary['free_shipping']:
        discounts_applied.append({'type': 'free_shipping', 'description': 'Envío gratis (2+ libros físicos en EU/USA/UK)', 'amount': summary.get('shipping_original', summary.get('shipping', 0))})
    return jsonify({
        'subtotal': summary['subtotal'],
        'shipping': summary['shipping'],
        'total': summary['total'],
        'free_shipping': summary['free_shipping'],
        'has_physical': summary['has_physical'],
        'item_count': summary['item_count'],
        'upsell_show': summary['upsell_show'],
        'country_code': summary['country_code'],
        'discounts_applied': discounts_applied,
    })


def _normalize_cart_shipping_address(addr: dict) -> dict:
    """Normalize cart-form shipping address keys to the canonical schema used
    by Lulu / Gelato pipelines (street1, postcode, phone_number, etc.)."""
    if not addr:
        return {}
    return {
        'name': addr.get('name', '').strip(),
        'street1': addr.get('street1', '') or addr.get('address_line_1', ''),
        'street2': addr.get('street2', '') or addr.get('address_line_2', ''),
        'city': addr.get('city', '').strip(),
        'state_code': addr.get('state_code', '') or addr.get('state', ''),
        'postcode': addr.get('postcode', '') or addr.get('postal_code', ''),
        'country_code': addr.get('country_code', '').strip().upper(),
        'phone_number': addr.get('phone_number', '') or addr.get('phone', ''),
    }


def _dispatch_cart_item(item: dict, buyer_email: str, paypal_order_id: str, shipping_address: dict = None, payment_data: dict = None):
    """Dispatch post-payment processing for a single cart item."""
    preview_id = item.get('preview_id', '')
    product_type = item.get('product_type', '')
    lang = item.get('lang', 'es')
    if not _PREVIEW_ID_RE.match(preview_id):
        print(f"[CART-DISPATCH] Rejected invalid preview_id: {preview_id!r}")
        return False
    preview_file = f'story_previews/{preview_id}.json'
    abs_previews = os.path.abspath('story_previews')
    abs_file = os.path.abspath(preview_file)
    if not abs_file.startswith(abs_previews + os.sep):
        print(f"[CART-DISPATCH] Path traversal attempt blocked: {preview_id!r}")
        return False
    if not os.path.exists(preview_file):
        print(f"[CART-DISPATCH] Preview not found: {preview_id}")
        return False
    with open(preview_file, 'r', encoding='utf-8') as f:
        story_data = json.load(f)
    from datetime import timedelta
    story_data['paid'] = True
    story_data['paypal_order_id'] = paypal_order_id
    story_data['payment_date'] = datetime.now().isoformat()
    story_data['payment_status'] = 'completed'
    story_data['customer_email'] = buyer_email
    story_data['cart_purchase'] = True
    if payment_data:
        _amt = payment_data.get('amount_paid')
        if _amt is not None:
            story_data['amount_paid'] = _amt
        _cur = payment_data.get('currency')
        if _cur:
            story_data['currency'] = _cur
        _cap = payment_data.get('capture_id')
        if _cap:
            story_data['capture_id'] = _cap
        _country = payment_data.get('payer_country')
        if _country:
            story_data['payer_country'] = _country
        _pt = payment_data.get('product_type')
        if _pt:
            story_data['product_type'] = _pt
        _fp_d = payment_data.get('format_prices', {})
        if _fp_d:
            story_data['format_prices'] = _fp_d
        story_data['shipping_cost_usd'] = round(float(payment_data.get('shipping_cost_usd', 0) or 0), 2)
        story_data['discount_amount'] = round(float(payment_data.get('discount_amount', 0) or 0), 2)
        story_data['coupon_code'] = payment_data.get('coupon_code', '') or ''
    _PHYSICAL_PRODUCT_TYPES = ('qs_print', 'cp_personalized')
    is_physical = product_type in _PHYSICAL_PRODUCT_TYPES
    if shipping_address and is_physical:
        story_data['shipping_address'] = _normalize_cart_shipping_address(shipping_address)
    if product_type == 'personalized_pdf':
        story_data['pdf_paid'] = True
        story_data['pdf_order'] = True
        story_data['want_pdf'] = True
        story_data['want_print'] = False
    elif product_type == 'cp_personalized':
        story_data['want_print'] = True
    elif product_type == 'qs_print':
        story_data['want_print'] = True
    else:
        story_data['want_print'] = False
        story_data['ebook_paid'] = True
        story_data['ebook_expires_at'] = (datetime.utcnow() + timedelta(days=Config.EBOOK_EXPIRY_DAYS)).isoformat()
    with open(preview_file, 'w', encoding='utf-8') as f:
        json.dump(story_data, f, ensure_ascii=False, indent=2)
    try:
        from services.email_service import register_purchase_for_follow_up as _reg_fu
        _reg_fu(preview_id, buyer_email, story_data.get('child_name', ''), story_data.get('lang', 'es'),
                story_name=story_data.get('story_name', story_data.get('title', '')))
    except Exception as _fu_err:
        print(f"[LEAD] register_purchase_for_follow_up error: {_fu_err}")
    print(f"[CART-DISPATCH] Processing cart item: {product_type} for {preview_id}")
    from services.personalized_books.generation import is_personalized_book as _check_pb
    from services.quick_stories.checkout import is_quick_story as _check_qs
    story_id = story_data.get('story_id', '')
    if _check_pb(story_id):
        if story_data.get('scenes_pending') and not story_data.get('scenes_generating'):
            _trigger_background_generation(preview_id)
        elif not story_data.get('pages_composed', False) and not story_data.get('book_composing', False):
            _trigger_personalized_book_composition(preview_id)
        elif story_data.get('pages_composed', False):
            if product_type == 'cp_personalized':
                already_done = story_data.get('admin_notified', False) or (
                    product_type == 'cp_personalized' and story_data.get('cp_pdfs_ready', False)
                )
                if not already_done:
                    print(f"[CART-DISPATCH] {product_type} — already composed, starting post-payment for {preview_id}")
                    t = threading.Thread(target=_process_personalized_book_post_payment, args=(preview_id, buyer_email), daemon=True)
                    t.start()
        if product_type == 'personalized_pdf':
            t_pdf = threading.Thread(target=_dispatch_printable_pdf_email, args=(preview_id, buyer_email, lang), daemon=True)
            t_pdf.start()
    elif _check_qs(story_id):
        if story_data.get('scenes_pending'):
            _trigger_background_generation(preview_id)
        elif product_type == 'qs_print' and not story_data.get('cp_submitted', story_data.get('lulu_submitted', False)):
            print(f"[CART-DISPATCH] qs_print — starting Cloudprinter print for {preview_id}")
            t = threading.Thread(target=_process_quick_story_print, args=(preview_id, buyer_email), daemon=True)
            t.start()
        # /formats PDF purchase uses product_type='personalized_pdf' → send email immediately
        _send_ebook_email = (product_type == 'personalized_pdf')
        if not story_data.get('visor_uploaded', False):
            print(f"[CART-DISPATCH] Quick Story — generating visor/ebook ({'with' if _send_ebook_email else 'no'} email) for {preview_id}")
            t = threading.Thread(target=_process_ebook_generation, args=(preview_id, buyer_email, _send_ebook_email), daemon=True)
            t.start()
        elif _send_ebook_email:
            print(f"[CART-DISPATCH] Quick Story visor ready — dispatching PDF email for {preview_id}")
            t = threading.Thread(target=_process_ebook_generation, args=(preview_id, buyer_email, True), daemon=True)
            t.start()
    else:
        t = threading.Thread(target=_process_ebook_generation, args=(preview_id, buyer_email), daemon=True)
        t.start()
    return True


def _send_cart_order_email(buyer_email: str, items: list, total_usd: float, lang: str = 'es'):
    """Send cart confirmation email with per-item access/tracking links."""
    if not buyer_email:
        return
    import time as _t
    _t.sleep(3)
    enriched = []
    for item in items:
        item_copy = dict(item)
        preview_id = item_copy.get('preview_id', '')
        preview_file = f'story_previews/{preview_id}.json'
        if preview_id and os.path.exists(preview_file):
            try:
                with open(preview_file, 'r', encoding='utf-8') as f:
                    sd = json.load(f)
                item_copy['visor_url'] = sd.get('visor_url', '')
                item_copy['pdf_download_url'] = sd.get('pdf_printable_path', '') or sd.get('pdf_download_url', '')
                item_copy['cp_submitted'] = sd.get('cp_submitted', sd.get('lulu_submitted', False))
                item_copy['tracking_number'] = sd.get('tracking_number', '')
            except Exception:
                pass
        enriched.append(item_copy)
    try:
        from services.email_service import send_cart_confirmation_email
        send_cart_confirmation_email(buyer_email, enriched, total_usd, lang)
    except Exception as e:
        print(f"[CART-EMAIL] Error sending cart confirmation: {e}")


@app.route('/api/save-checkout-data/<preview_id>', methods=['POST'])
def save_checkout_data(preview_id):
    """Save want_print, email and shipping data before PayPal checkout"""
    preview_file = f'story_previews/{preview_id}.json'
    if not os.path.exists(preview_file):
        return jsonify({'success': False, 'error': 'Story not found'}), 404
    
    data = request.get_json()
    
    with open(preview_file, 'r', encoding='utf-8') as f:
        story_data = json.load(f)
    
    want_print = data.get('want_print', False)
    email = data.get('email', '')
    shipping_address = data.get('shipping_address')
    formats = data.get('formats', [])
    want_ebook = 'ebook' in formats
    want_pdf = 'pdf' in formats or 'digital' in formats

    story_data['want_print'] = bool(want_print)
    story_data['want_ebook'] = bool(want_ebook)
    story_data['want_pdf'] = bool(want_pdf)
    if email:
        story_data['customer_email'] = email
    
    buyer_country = data.get('buyer_country', '').strip().upper()
    if buyer_country:
        story_data['buyer_country'] = buyer_country

    print_format = (data.get('print_format') or data.get('pdf_format') or '').strip().upper()
    if print_format in ('CARTA', 'LETTER'):
        print_format = 'LETTER'
    elif print_format != 'A4':
        print_format = ''
    if print_format:
        story_data['print_format'] = print_format
    
    shipping_method = data.get('shipping_method')
    if shipping_method and shipping_method != 'none':
        story_data['shipping_method'] = shipping_method

    product_type_incoming = data.get('product_type')
    if product_type_incoming and not story_data.get('product_type'):
        story_data['product_type'] = product_type_incoming
    print_product_type_incoming = data.get('print_product_type')
    if print_product_type_incoming and not story_data.get('print_product_type'):
        story_data['print_product_type'] = print_product_type_incoming

    cp_cost_eur = data.get('cp_cost_eur')
    print_cost_eur = data.get('print_cost_eur')
    customer_total_usd = data.get('customer_total_usd')
    if cp_cost_eur is not None:
        story_data['cp_cost_eur'] = float(cp_cost_eur)
    if print_cost_eur is not None:
        story_data['print_cost_eur'] = float(print_cost_eur)
    if customer_total_usd is not None:
        story_data['customer_total_usd'] = float(customer_total_usd)

    if want_print and shipping_address:
        story_data['shipping_address'] = {
            'name': shipping_address.get('name', ''),
            'street1': shipping_address.get('street1', ''),
            'street2': shipping_address.get('street2', ''),
            'city': shipping_address.get('city', ''),
            'state_code': shipping_address.get('state_code', ''),
            'postcode': shipping_address.get('postcode', ''),
            'country_code': shipping_address.get('country_code', ''),
            'phone_number': shipping_address.get('phone_number', '') or shipping_address.get('phone', '') or data.get('phone', ''),
            'email': shipping_address.get('email', email)
        }
    
    with open(preview_file, 'w', encoding='utf-8') as f:
        json.dump(story_data, f, ensure_ascii=False, indent=2)
    
    print(f"[CHECKOUT-DATA] Saved for {preview_id}: want_print={want_print}, email={email}")

    # If email was already sent but print is still pending (checkout data arrived late), launch print now
    _print_email = story_data.get('customer_email', email or '')
    _qs_print_done = not story_data.get('want_print') or story_data.get('cp_submitted') or story_data.get('print_confirmation_sent')
    if (story_data.get('email_sent') and want_print and not _qs_print_done
            and story_data.get('paid') and story_data.get('shipping_address')
            and not story_data.get('admin_gift')):
        print(f"[CHECKOUT-DATA] Email already sent but CP print pending for {preview_id} — launching print job now")
        import threading
        t = threading.Thread(target=_process_quick_story_print, args=(preview_id, _print_email), daemon=True)
        t.start()

    return jsonify({'success': True, 'want_print': want_print})


@app.route('/api/save-shipping-data/<preview_id>', methods=['POST'])
def save_shipping_data(preview_id):
    """Save shipping data before checkout"""
    preview_file = f'story_previews/{preview_id}.json'
    if not os.path.exists(preview_file):
        return jsonify({'success': False, 'error': 'Story not found'}), 404
    
    data = request.get_json()
    email = data.get('email')
    phone = data.get('phone')
    shipping_data = data.get('shipping_address', {})
    shipping_method = data.get('shipping_method', 'MAIL')
    extra_shipping_cost = float(data.get('extra_shipping_cost', 0))
    
    with open(preview_file, 'r', encoding='utf-8') as f:
        story_data = json.load(f)
    
    story_data['customer_email'] = email
    story_data['customer_phone'] = phone
    story_data['want_print'] = True
    story_data['shipping_method'] = shipping_method
    story_data['extra_shipping_cost'] = extra_shipping_cost
    
    if shipping_data:
        story_data['shipping_address'] = {
            'name': shipping_data.get('name', ''),
            'street1': shipping_data.get('street1', ''),
            'street2': shipping_data.get('street2', ''),
            'city': shipping_data.get('city', ''),
            'state_code': shipping_data.get('state_code', ''),
            'postcode': shipping_data.get('postcode', ''),
            'country_code': shipping_data.get('country_code', ''),
            'phone_number': shipping_data.get('phone_number', phone),
            'email': shipping_data.get('email', email)
        }
        print(f"[SHIPPING] Saved: {shipping_method} to {story_data['shipping_address']['city']}, {story_data['shipping_address']['country_code']}")
    
    with open(preview_file, 'w', encoding='utf-8') as f:
        json.dump(story_data, f, ensure_ascii=False, indent=2)
    
    return jsonify({'success': True})


@app.route('/api/process-payment/<preview_id>', methods=['POST'])
def process_payment(preview_id):
    """Process payment after PayPal confirmation.
    Triggers post-payment processing for personalized books (Lulu PDFs + admin email).
    """
    preview_file = f'story_previews/{preview_id}.json'
    if not os.path.exists(preview_file):
        return jsonify({'success': False, 'error': 'Story not found'}), 404
    
    data = request.get_json()
    paypal_order_id = data.get('paypal_order_id', '')
    customer_email = data.get('customer_email', '') or data.get('email', '')
    want_print = data.get('want_print', False)
    shipping_address = data.get('shipping_address')
    product_type = data.get('product_type', '')
    
    with open(preview_file, 'r', encoding='utf-8') as f:
        story_data = json.load(f)
    
    story_data['paid'] = True
    story_data['paypal_order_id'] = paypal_order_id
    story_data['payment_date'] = datetime.now().isoformat()
    story_data['generation_complete'] = True
    story_data['payment_status'] = 'completed'
    _amt_d = float(data.get('amount_usd', 0) or 0)
    if _amt_d > 0:
        story_data['amount_paid'] = round(_amt_d, 2)
    story_data['currency'] = data.get('currency', 'USD') or 'USD'
    if data.get('capture_id'):
        story_data['capture_id'] = data['capture_id']
    if data.get('payer_country'):
        story_data['payer_country'] = data['payer_country']
    _pt_d = product_type or data.get('product_type', '') or story_data.get('product_type', '')
    if _pt_d:
        story_data['product_type'] = _pt_d

    client_ip = get_client_ip()
    try:
        cutoff = datetime.utcnow() - timedelta(hours=24)
        PreviewLead.query.filter(
            PreviewLead.ip_address == client_ip,
            PreviewLead.created_at >= cutoff
        ).delete(synchronize_session=False)
        db.session.commit()
        print(f"[RATE LIMIT] Cleared DB records for IP {client_ip} after payment")
    except Exception:
        db.session.rollback()
    
    story_data['want_print'] = bool(want_print)
    formats = data.get('formats', [])
    if formats:
        story_data['formats'] = formats
    shipping_method = data.get('shipping_method')
    if shipping_method and shipping_method != 'none':
        story_data['shipping_method'] = shipping_method
    if want_print and shipping_address:
        story_data['shipping_address'] = shipping_address
    
    if customer_email:
        story_data['customer_email'] = customer_email
    
    email = story_data.get('customer_email', '')
    story_id = story_data.get('story_id', '')

    try:
        from services.email_service import register_purchase_for_follow_up as _reg_fu
        _reg_fu(preview_id, email, story_data.get('child_name', ''), story_data.get('lang', 'es'),
                story_name=story_data.get('story_name', story_data.get('title', '')))
    except Exception as _fu_err:
        print(f"[LEAD] register_purchase_for_follow_up error: {_fu_err}")

    print(f"[PAYMENT] PayPal order: {paypal_order_id}")
    print(f"[PAYMENT] Story ID: {story_id}")
    print(f"[PAYMENT] Email: {email}")
    
    if paypal_order_id:
        try:
            real_order = RealStoryOrder.query.filter_by(order_number=preview_id).first()
            if real_order:
                real_order.paypal_order_id = paypal_order_id
                real_order.amount_paid = int(float(data.get('amount_usd', 0)) * 100) if data.get('amount_usd') else None
                real_order.paid_at = datetime.utcnow()
                real_order.status = 'PAID'
                db.session.commit()
                print(f"[PAYMENT] Updated RealStoryOrder {preview_id} with paypal_order_id={paypal_order_id}")
        except Exception as db_err:
            print(f"[PAYMENT] DB update for RealStoryOrder failed (non-blocking): {db_err}")
            db.session.rollback()
    
    # --- Persistir datos económicos (format_prices, discount, shipping, cupón) ---
    _eco_fp_raw = data.get('format_prices', {})
    if _eco_fp_raw:
        story_data['format_prices'] = {k: round(float(v), 2) for k, v in _eco_fp_raw.items() if v}
    _eco_sc = round(float(data.get('shipping_cost', 0) or 0), 2)
    story_data['shipping_cost_usd'] = _eco_sc
    _eco_cc = (data.get('coupon_code') or '').strip().upper()
    story_data['coupon_code'] = _eco_cc
    _eco_total = round(float(data.get('amount_usd', 0) or 0), 2)
    _eco_fp_vals = story_data.get('format_prices', {})
    _eco_subtotal = round(sum(_eco_fp_vals.values()), 2) if _eco_fp_vals else 0.0
    _eco_disc = round(_eco_subtotal + _eco_sc - _eco_total, 2) if (_eco_subtotal > 0 and _eco_total > 0 and (_eco_subtotal + _eco_sc - _eco_total) > 0.015) else 0.0
    story_data['discount_amount'] = _eco_disc

    with open(preview_file, 'w', encoding='utf-8') as f:
        json.dump(story_data, f, ensure_ascii=False, indent=2)
    
    if email:
        try:
            from services.email_service import send_payment_confirmation_email
            lang = story_data.get('lang', 'es')
            child_name = story_data.get('child_name', 'tu hijo/a')
            base_url = os.environ.get('SITE_DOMAIN', os.environ.get('REPLIT_DEV_DOMAIN', 'magicmemoriesbooks.com'))
            recovery_url = f"https://{base_url}/order-complete/{preview_id}"

            _formats = data.get('formats', [])
            _shipping_cost = float(data.get('shipping_cost', 0))
            _total = float(data.get('amount_usd', 0))
            _fp = data.get('format_prices', {})

            _is_qs = product_type in ('', 'quick_story', 'qs_digital', 'qs_print')
            _digital_price = float(_fp.get('digital', 0)) or (Config.QS_DIGITAL_BASE_PRICE if _is_qs else Config.PERSONALIZED_BASE_PRICE) / 100.0
            _print_price = float(_fp.get('print', 0)) or (Config.QS_PRINT_BASE_PRICE if _is_qs else Config.PERSONALIZED_BASE_PRICE) / 100.0
            _ebook_price = float(_fp.get('ebook', 0)) or Config.EBOOK_BASE_PRICE / 100.0
            _pdf_price = float(_fp.get('pdf', 0)) or Config.PERSONALIZED_PDF_PRICE / 100.0

            _format_labels = {
                'digital': (('Cuento Digital (PDF)', 'Digital Story (PDF)'), _digital_price),
                'ebook': (('eBook Interactivo', 'Interactive eBook'), _ebook_price),
                'print': (('Libro Impreso', 'Printed Book'), _print_price),
                'pdf': (('PDF Imprimible', 'Printable PDF'), _pdf_price),
            }
            _line_items = []
            for fmt in _formats:
                info = _format_labels.get(fmt)
                if info:
                    label = info[0][0] if lang == 'es' else info[0][1]
                    _line_items.append({'label': label, 'price': info[1]})

            if not _line_items and _total > 0:
                _fallback_label = ('Cuento Personalizado', 'Personalized Story')
                _line_items = [{'label': _fallback_label[0] if lang == 'es' else _fallback_label[1], 'price': _total - _shipping_cost}]

            if _total <= 0 and _line_items:
                _total = sum(item['price'] for item in _line_items) + _shipping_cost

            _subtotal = sum(item['price'] for item in _line_items)
            if _subtotal > 0 and _total > 0 and (_subtotal + _shipping_cost - _total) > 0.015:
                _discount_amount = round(_subtotal + _shipping_cost - _total, 2)
                _coupon = data.get('coupon_code') or story_data.get('coupon_code', '')
                if _coupon:
                    _disc_label = f'Descuento ({_coupon})' if lang == 'es' else f'Discount ({_coupon})'
                else:
                    _disc_pct = round(_discount_amount / _subtotal * 100)
                    _disc_label = f'Descuento ({_disc_pct}%)' if lang == 'es' else f'Discount ({_disc_pct}%)'
                _line_items.append({'label': _disc_label, 'price': -_discount_amount})

            send_payment_confirmation_email(
                email, child_name, recovery_url, lang,
                line_items=_line_items if _line_items else None,
                shipping_cost=_shipping_cost,
                total_usd=_total
            )
            print(f"[PAYMENT] Confirmation email sent to {email}")
        except Exception as e:
            print(f"[PAYMENT] Failed to send confirmation email: {e}")
    
    try:
        from services.email_service import send_admin_purchase_notification
        _admin_pt = product_type
        if product_type in ('', 'quick_story'):
            _admin_pt = 'qs_print' if want_print else 'qs_digital'
        elif product_type == 'personalized_book':
            _admin_pt = 'personalized'
        send_admin_purchase_notification(
            preview_id, _admin_pt, email, story_data,
            line_items=_line_items if _line_items else None,
            shipping_cost=_shipping_cost,
            total_usd=_total
        )
        print(f"[PAYMENT] Admin purchase notification sent ({_admin_pt})")
    except Exception as _adm_err:
        print(f"[PAYMENT] Admin notification failed: {_adm_err}")

    if product_type == 'ebook':
        print(f"[PAYMENT] eBook purchase detected for {preview_id}")
        story_data['ebook_paid'] = True
        story_data['ebook_expires_at'] = None
        story_data['product_type'] = 'ebook'
        with open(preview_file, 'w', encoding='utf-8') as f:
            json.dump(story_data, f, ensure_ascii=False, indent=2)
        try:
            from services.vps_upload_service import make_ebook_permanent
            make_ebook_permanent(preview_id)
        except Exception as _perm_err:
            print(f"[PAYMENT] make_ebook_permanent failed (non-fatal): {_perm_err}")
        from services.quick_stories.checkout import is_quick_story as _check_qs_ebook
        _ebook_send_email = not _check_qs_ebook(story_id)
        t = threading.Thread(
            target=_process_ebook_generation,
            args=(preview_id, email, _ebook_send_email),
            daemon=True
        )
        t.start()
        return jsonify({
            'success': True,
            'redirect_url': f'/order-complete/{preview_id}'
        })

    if product_type == 'personalized_pdf':
        print(f"[PAYMENT] PDF Imprimible purchase detected for {preview_id}")
        story_data['pdf_paid'] = True
        story_data['pdf_paid_at'] = datetime.now().isoformat()
        story_data['product_type'] = 'personalized_pdf'
        story_data['want_print'] = False
        story_data['pdf_order'] = True
        with open(preview_file, 'w', encoding='utf-8') as f:
            json.dump(story_data, f, ensure_ascii=False, indent=2)
        from services.personalized_books.generation import is_personalized_book as _check_pb
        if _check_pb(story_id):
            if story_data.get('scenes_pending') and not story_data.get('scenes_generating'):
                print(f"[PAYMENT] personalized_pdf — scenes pending, launching scene generation...")
                _trigger_background_generation(preview_id)
            elif not story_data.get('pages_composed', False) and not story_data.get('book_composing', False):
                print(f"[PAYMENT] personalized_pdf — launching book composition (no Gelato order)...")
                _trigger_personalized_book_composition(preview_id)
        lang_for_pdf = story_data.get('lang', 'es')
        t_pdf = threading.Thread(
            target=_dispatch_printable_pdf_email,
            args=(preview_id, email, lang_for_pdf),
            daemon=True
        )
        t_pdf.start()
        return jsonify({
            'success': True,
            'redirect_url': f'/order-complete/{preview_id}'
        })
    
    from services.personalized_books.generation import is_personalized_book as check_personalized
    if check_personalized(story_id):
        if story_data.get('scenes_pending') and not story_data.get('scenes_generating'):
            print(f"[PAYMENT] Personalized book scenes pending - launching background scene generation with FLUX 2 Dev...")
            _trigger_background_generation(preview_id)
        elif not story_data.get('pages_composed', False) and not story_data.get('book_composing', False):
            print(f"[PAYMENT] Personalized book detected - launching background composition + Lulu...")
            _trigger_personalized_book_composition(preview_id)
        elif not story_data.get('admin_notified', False) and not story_data.get('cp_pdfs_ready', False):
            _pt_check = story_data.get('product_type', '')
            print(f"[PAYMENT] Pages already composed, launching post-payment processing ({_pt_check})...")
            t = threading.Thread(
                target=_process_personalized_book_post_payment,
                args=(preview_id, email),
                daemon=True
            )
            t.start()
        else:
            print(f"[PAYMENT] Post-payment already processed for {preview_id}, skipping")
    
    from services.quick_stories.checkout import is_quick_story as check_quick_story
    if check_quick_story(story_id):
        if story_data.get('scenes_pending'):
            print(f"[PAYMENT] Quick Story scenes pending - launching background generation")
            _trigger_background_generation(preview_id)
        elif want_print and not story_data.get('cp_submitted', story_data.get('lulu_submitted', False)):
            print(f"[PAYMENT] Quick Story with print option - starting Cloudprinter PDF generation...")
            t = threading.Thread(
                target=_process_quick_story_print,
                args=(preview_id, email),
                daemon=True
            )
            t.start()
        if not story_data.get('visor_uploaded', False):
            print(f"[PAYMENT] Quick Story - generating visor (no email yet, waiting for user approval)...")
            t = threading.Thread(
                target=_process_ebook_generation,
                args=(preview_id, email, False),
                daemon=True
            )
            t.start()
        else:
            print(f"[PAYMENT] Quick Story visor already generated for {preview_id}, skipping")
    
    return jsonify({
        'success': True,
        'redirect_url': f'/order-complete/{preview_id}'
    })

@app.route('/order-complete/<preview_id>')
def order_complete(preview_id):
    """Order complete page with full story view"""
    preview_file = f'story_previews/{preview_id}.json'
    if not os.path.exists(preview_file):
        return redirect(url_for('index'))
    
    import time as _oc_time
    try:
        content = ''
        for _attempt in range(5):
            with open(preview_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            if content:
                break
            print(f"[ORDER-COMPLETE] Empty JSON file for {preview_id} (attempt {_attempt+1}/5), retrying...")
            _oc_time.sleep(0.4)
        if not content:
            print(f"[ORDER-COMPLETE] Empty JSON file for {preview_id} after retries, redirecting home")
            return redirect(url_for('index'))
        story_data = json.loads(content)
    except (json.JSONDecodeError, ValueError) as e:
        print(f"[ORDER-COMPLETE] Corrupt JSON file for {preview_id}: {e}")
        return redirect(url_for('index'))
    
    email_from_url = request.args.get('email', '')
    if email_from_url and not story_data.get('customer_email'):
        story_data['customer_email'] = email_from_url
        with open(preview_file, 'w', encoding='utf-8') as f:
            json.dump(story_data, f, ensure_ascii=False, indent=2)
    
    story_id = story_data.get('story_id', '')
    
    output_dir = story_data.get('output_dir', '')
    
    is_illustrated_book = story_data.get('is_illustrated_book', False)
    
    if story_data.get('scenes_pending') or story_data.get('scenes_generating'):
        _trigger_background_generation(preview_id)
        print(f"[ORDER-COMPLETE] Scenes generating in background for {preview_id}, page will poll for status")
    elif is_illustrated_book and story_data.get('book_scenes_ready') and not story_data.get('pages_composed', False) and not story_data.get('book_composing', False):
        print(f"[ORDER-COMPLETE] Personalized book scenes ready, waiting for user approval before composing PDF")
    elif is_illustrated_book and not story_data.get('pages_composed', False) and not story_data.get('book_scenes_ready', False):
        print(f"[ORDER-COMPLETE] Personalized book scenes not ready for {preview_id}, awaiting scene generation")
    elif is_illustrated_book and story_data.get('pages_composed', False) and not story_data.get('email_sent', False):
        print(f"[ORDER-COMPLETE] Pages composed but email not sent for {preview_id}, awaiting user confirmation")
    
    age_range = story_data.get('age_range', '0-1')
    if is_illustrated_book:
        is_baby = False
        is_kids = False
    else:
        is_baby = age_range in ['0-1', '0-2']
        is_kids = not is_baby
    
    epub_url = f'/api/download-epub/{preview_id}'
    
    is_furry_love = story_data.get('is_furry_love', False)
    
    buyer_country = story_data.get('buyer_country', '').strip().upper()
    try:
        from services.cloudprinter_api_service import CLOUDPRINTER_AVAILABLE_COUNTRIES
        cp_available = (not buyer_country) or (buyer_country in CLOUDPRINTER_AVAILABLE_COUNTRIES)
    except Exception:
        cp_available = True

    _addr = story_data.get('shipping_address') or {}
    _shipping_confirmed = bool(_addr.get('name') and _addr.get('street1'))
    _needs_shipping = _story_needs_physical_shipping(story_data)

    # Gallery source of truth: derived FRESH from the page_NN.png files on
    # disk (same canonical listing rebuild_book() uses), never from
    # story_data['images'] — that field is intentionally a TRIMMED
    # (content-only, [2:-2]) array used for PDF/print composition and its
    # length/order can legitimately differ from the full on-disk page set.
    # Reusing it for the gallery caused row/label/button drift whenever a
    # regeneration ran rebuild_book() and re-trimmed it (Página 1/2 buttons
    # "disappearing", wrong page regenerated, wrong regen counter hit).
    # See .agents/memory/order-complete-gallery-array-mismatch.md
    gallery_pages = []
    if is_illustrated_book:
        composed_dir_gallery = f'generated/composed_{preview_id}'
        try:
            from services.personalized_books.rebuild import _enumerate_pages, _fmt
            _orig_paths, _prev_paths = _enumerate_pages(composed_dir_gallery)
        except Exception:
            _orig_paths, _prev_paths = [], []
        if _orig_paths:
            import re as _gallery_re
            _page_num_re = _gallery_re.compile(r'page_(\d{2})\.png$')
            n_total = len(_prev_paths)
            # Same convention rebuild.py uses to define "content" (regenerable
            # scene) pages: everything except the first 2 and last 2 files.
            content_start_pos = 2 if n_total > 4 else 0
            content_end_pos = n_total - 2 if n_total > 4 else n_total
            for _pos, _p in enumerate(_prev_paths):
                _m = _page_num_re.search(_p)
                _real_num = int(_m.group(1)) if _m else (_pos + 1)
                gallery_pages.append({
                    'pos': _pos,
                    'num': _real_num,
                    'src': _fmt(_p),
                    'is_content': content_start_pos <= _pos < content_end_pos,
                })

    return render_template('order_complete.html',
                          preview_id=preview_id,
                          story_data=story_data,
                          gallery_pages=gallery_pages,
                          delivery_email=story_data.get('customer_email', ''),
                          email_sent=story_data.get('email_sent', False),
                          epub_url=epub_url,
                          is_baby=is_baby,
                          is_kids=is_kids,
                          is_furry_love=is_furry_love,
                          cp_available=cp_available,
                          needs_shipping=_needs_shipping,
                          shipping_confirmed=_shipping_confirmed,
                          lang=story_data.get('lang', story_data.get('language', 'es')))


@app.route('/shipping-confirm/<preview_id>', methods=['GET', 'POST'])
def shipping_confirm(preview_id):
    """POST-approval shipping address confirmation for physical books."""
    preview_file = f'story_previews/{preview_id}.json'
    if not os.path.exists(preview_file):
        return redirect(url_for('index'))

    with open(preview_file, 'r', encoding='utf-8') as f:
        story_data = json.load(f)

    lang = story_data.get('lang', story_data.get('language', 'es'))

    if request.method == 'POST':
        data = request.get_json(silent=True) or request.form.to_dict()
        name = (data.get('name') or '').strip()
        street1 = (data.get('street1') or '').strip()
        street2 = (data.get('street2') or '').strip()
        city = (data.get('city') or '').strip()
        state_code = (data.get('state_code') or '').strip()
        postcode = (data.get('postcode') or '').strip()
        country_code = (data.get('country_code') or '').strip().upper()
        phone = (data.get('phone') or '').strip()

        if not (name and street1 and city and postcode and country_code):
            msg = 'Todos los campos obligatorios son requeridos.' if lang == 'es' else 'All required fields must be filled.'
            if request.is_json:
                return jsonify({'success': False, 'error': msg}), 400
            return redirect(url_for('shipping_confirm', preview_id=preview_id, error=msg))

        shipping_address = {
            'name': name,
            'street1': street1,
            'street2': street2,
            'city': city,
            'state_code': state_code,
            'postcode': postcode,
            'country_code': country_code,
            'phone': phone,
        }
        story_data['shipping_address'] = shipping_address

        # If PDF already composed but CP order not yet dispatched — dispatch now
        _pt = story_data.get('product_type', '')
        _is_cp_pb = (_pt == 'cp_personalized') or (story_data.get('print_product_type') == 'cp_personalized')
        if (story_data.get('pages_composed') or story_data.get('cp_pdfs_ready')) and not story_data.get('cp_pb_order_ref') and _is_cp_pb:
            try:
                from services.personalized_books.cp_pdf_service import generate_cw_cover_pdf, generate_cw_content_pdf
                from services.cloudprinter_api_service import submit_pb_print_order, get_pdf_public_url
                from services.personalized_books.generation import get_print_title
                traits = story_data.get('traits', {})
                book_id = story_data.get('story_id', '')
                child_name = story_data.get('child_name', '')
                customer_email = story_data.get('customer_email', '')
                pet_name_g = traits.get('pet_name', '') if traits else ''
                book_title_g = get_print_title(book_id, child_name, lang, pet_name=pet_name_g)
                from services.cloudprinter_api_service import resolve_shipping_level
                cp_shipping_level = resolve_shipping_level(story_data.get('shipping_method', 'cp_saver'))

                from services.cloudprinter_api_service import get_pb_chosen_page_count
                _chosen_pages = get_pb_chosen_page_count()
                print(f"[SHIPPING-CONFIRM] Generating CP casewrap PDFs for {preview_id} "
                      f"(page_count={_chosen_pages})...")
                cp_out_dir = os.path.join("generations", "cloudprinter", preview_id)
                os.makedirs(cp_out_dir, exist_ok=True)
                cover_pdf_path   = os.path.join(cp_out_dir, "cover.pdf")
                content_pdf_path = os.path.join(cp_out_dir, "content.pdf")

                generate_cw_cover_pdf(
                    session_id=preview_id,
                    book_title=book_title_g,
                    output_path=cover_pdf_path,
                    page_count=_chosen_pages,
                    story_id=book_id,
                )
                generate_cw_content_pdf(
                    session_id=preview_id,
                    child_name=child_name,
                    language=lang,
                    output_path=content_pdf_path,
                    page_count=_chosen_pages,
                )
                cover_pdf_url   = get_pdf_public_url(preview_id, "cover.pdf")
                content_pdf_url = get_pdf_public_url(preview_id, "content.pdf")
                story_data['cp_cover_pdf_url']   = cover_pdf_url
                story_data['cp_content_pdf_url'] = content_pdf_url

                cp_ok, cp_msg, cp_ref = submit_pb_print_order(
                    preview_id=preview_id,
                    cover_pdf_path=cover_pdf_path,
                    cover_pdf_url=cover_pdf_url,
                    content_pdf_path=content_pdf_path,
                    content_pdf_url=content_pdf_url,
                    customer_data={"email": customer_email or ""},
                    shipping_address=shipping_address,
                    shipping_level=cp_shipping_level,
                )
                if cp_ok:
                    story_data['cp_pb_order_ref'] = cp_ref
                    story_data['cp_order_status'] = 'submitted'
                    print(f"[SHIPPING-CONFIRM] CP PB order submitted for {preview_id}: {cp_ref}")
                    try:
                        from services.email_service import send_cp_pb_admin_notification
                        send_cp_pb_admin_notification(
                            preview_id=preview_id,
                            cp_order_ref=cp_ref or '',
                            title=book_title_g,
                            customer_email=customer_email or '',
                            shipping_address=shipping_address,
                            cover_pdf_url=cover_pdf_url,
                            content_pdf_url=content_pdf_url,
                            visor_url=story_data.get('visor_url', ''),
                            paid_amount=f"${story_data.get('customer_total_usd', 0):.2f} USD" if story_data.get('customer_total_usd') else '',
                            cp_cost_eur=float(story_data.get('cp_cost_eur', 0)),
                            print_cost_eur=float(story_data.get('print_cost_eur', 0)),
                        )
                    except Exception as admin_notif_err:
                        print(f"[SHIPPING-CONFIRM] CP admin notification error: {admin_notif_err}")
                else:
                    story_data['cp_order_status'] = 'failed'
                    story_data['cp_order_error']  = cp_msg
                    print(f"[SHIPPING-CONFIRM] CP PB order failed for {preview_id}: {cp_msg}")
            except Exception as dispatch_err:
                print(f"[SHIPPING-CONFIRM] CP PB dispatch error: {dispatch_err}")

        with open(preview_file, 'w', encoding='utf-8') as f:
            json.dump(story_data, f, ensure_ascii=False, indent=2)

        if request.is_json:
            return jsonify({'success': True, 'redirect': url_for('shipping_confirm_success', preview_id=preview_id)})
        return redirect(url_for('shipping_confirm_success', preview_id=preview_id))

    error_msg = request.args.get('error', '')
    from services.cart import EU_AND_FREE_SHIPPING_COUNTRIES
    return render_template('shipping_confirm.html',
                           preview_id=preview_id,
                           story_data=story_data,
                           error_msg=error_msg,
                           free_shipping_countries=list(EU_AND_FREE_SHIPPING_COUNTRIES),
                           lang=lang)


@app.route('/shipping-confirm/<preview_id>/success')
def shipping_confirm_success(preview_id):
    preview_file = f'story_previews/{preview_id}.json'
    story_data = {}
    if os.path.exists(preview_file):
        with open(preview_file, 'r', encoding='utf-8') as f:
            story_data = json.load(f)
    lang = story_data.get('lang', story_data.get('language', 'es'))
    return render_template('shipping_confirm_success.html',
                           preview_id=preview_id,
                           story_data=story_data,
                           lang=lang)


@app.route('/track-order/<preview_id>')
def track_order(preview_id):
    """Page for tracking printed book order status."""
    story_data = {}
    lulu_job_id = None
    lang = 'es'
    
    if preview_id.startswith('haz_tu_historia_'):
        order_number = preview_id.replace('haz_tu_historia_', '')
        order = RealStoryOrder.query.filter_by(order_number=order_number).first()
        if not order:
            return redirect(url_for('index'))

        lulu_job_id = order.lulu_job_id
        cp_order_ref = None
        lang = order.language or 'es'

        protagonist = order.characters[0].name if order.characters else 'Hero'
        if order.theme_type == 'preset' and order.theme_preset:
            theme_name = order.theme_preset.replace('_', ' ').title()
        else:
            theme_name = 'Nuestra Historia Especial' if lang == 'es' else 'Our Special Story'

        story_data = {
            'child_name': protagonist,
            'story_name': f"{theme_name} de {protagonist}" if lang == 'es' else f"{protagonist}'s {theme_name}"
        }
    else:
        preview_file = f'story_previews/{preview_id}.json'
        if not os.path.exists(preview_file):
            return redirect(url_for('index'))

        with open(preview_file, 'r', encoding='utf-8') as f:
            story_data = json.load(f)

        lulu_job_id = story_data.get('lulu_job_id')
        cp_order_ref = story_data.get('cp_order_ref')
        lang = story_data.get('lang', story_data.get('language', 'es'))

    tracking_info = None
    if cp_order_ref:
        try:
            from services.cloudprinter_api_service import get_order_status
            tracking_info = get_order_status(cp_order_ref)
        except Exception as e:
            print(f"[TRACK-ORDER] Cloudprinter tracking error: {e}")
        # Fallback: use cached data from webhook/story JSON when API call fails
        if not tracking_info:
            cp_order_status = story_data.get('cp_order_status')
            # 'sent' is our internal flag (submitted to CP), not CP's "shipped" status
            if cp_order_status == 'shipped':
                fallback_status = 'shipped'
                fallback_text = {'es': 'En camino', 'en': 'On its way'}
            elif story_data.get('cp_submitted'):
                fallback_status = 'in_production'
                fallback_text = {'es': 'En proceso de impresión', 'en': 'Being printed'}
            else:
                fallback_status = None
                fallback_text = None
            if fallback_status:
                tracking_info = {
                    'status': fallback_status,
                    'status_text': fallback_text,
                    'tracking_number': story_data.get('cp_tracking_code'),
                    'tracking_url': story_data.get('cp_tracking_url'),
                    'carrier': None,
                    'updated_at': story_data.get('cp_submitted_date', ''),
                    'from_cache': True,
                }
                print(f"[TRACK-ORDER] Using cached status={fallback_status} for {cp_order_ref}")
    elif lulu_job_id:
        tracking_info = {
            'status': 'historical',
            'status_text': {'es': 'Procesado por imprenta anterior', 'en': 'Processed by previous printer'},
            'tracking_number': None, 'tracking_url': None, 'carrier': None
        }

    buyer_country_tr = story_data.get('buyer_country', '').strip().upper()
    try:
        from services.cloudprinter_api_service import CLOUDPRINTER_AVAILABLE_COUNTRIES
        cp_available_tr = (not buyer_country_tr) or (buyer_country_tr in CLOUDPRINTER_AVAILABLE_COUNTRIES)
    except Exception:
        cp_available_tr = True

    return render_template('track_order.html',
                          preview_id=preview_id,
                          story_data=story_data,
                          lulu_job_id=lulu_job_id or cp_order_ref,
                          cp_order_ref=cp_order_ref,
                          tracking_info=tracking_info,
                          cp_available=cp_available_tr,
                          lang=lang)


_PHYSICAL_PRINT_TYPES_APPROVE = {'qs_print', 'cp_personalized'}

def _story_needs_physical_shipping(story_data: dict) -> bool:
    """Returns True if this story has a physical print component that needs a shipping address."""
    if not story_data.get('want_print'):
        return False
    pt = story_data.get('print_product_type', '') or story_data.get('product_type', '')
    return pt in _PHYSICAL_PRINT_TYPES_APPROVE


@app.route('/api/approve-scenes/<preview_id>', methods=['POST'])
def approve_scenes(preview_id):
    preview_file = f'story_previews/{preview_id}.json'
    if not os.path.exists(preview_file):
        return jsonify({'success': False, 'error': 'Not found'}), 404
    
    with open(preview_file, 'r', encoding='utf-8') as f:
        story_data = json.load(f)
    
    if not story_data.get('book_scenes_ready', False):
        return jsonify({'success': False, 'error': 'Scenes not ready'}), 400
    
    if story_data.get('pages_composed', False):
        needs_shipping = _story_needs_physical_shipping(story_data)
        addr = story_data.get('shipping_address') or {}
        shipping_confirmed = bool(addr.get('name') and addr.get('street1'))
        return jsonify({
            'success': True,
            'message': 'Already composed',
            'requires_shipping_address': needs_shipping and not shipping_confirmed,
            'shipping_confirm_url': f'/shipping-confirm/{preview_id}',
        })
    
    print(f"[APPROVE] User approved scenes for {preview_id}, launching PDF composition + Lulu...")
    _trigger_personalized_book_composition(preview_id)

    needs_shipping = _story_needs_physical_shipping(story_data)
    addr = story_data.get('shipping_address') or {}
    shipping_confirmed = bool(addr.get('name') and addr.get('street1'))
    
    return jsonify({
        'success': True,
        'message': 'Composition started',
        'requires_shipping_address': needs_shipping and not shipping_confirmed,
        'shipping_confirm_url': f'/shipping-confirm/{preview_id}',
    })


@app.route('/api/retry-compose/<preview_id>', methods=['POST'])
def retry_compose(preview_id):
    """Allow a single user-initiated retry when book composition has failed."""
    preview_file = f'story_previews/{preview_id}.json'
    if not os.path.exists(preview_file):
        return jsonify({'success': False, 'error': 'Not found'}), 404

    with open(preview_file, 'r', encoding='utf-8') as f:
        story_data = json.load(f)

    if not story_data.get('generation_failed', False):
        return jsonify({'success': False, 'error': 'No failed composition to retry'}), 400

    if story_data.get('retry_attempted', False):
        return jsonify({'success': False, 'error': 'Retry already attempted'}), 400

    if story_data.get('pages_composed', False):
        return jsonify({'success': False, 'error': 'Book already composed'}), 400

    production_logger.info(f"[RETRY-COMPOSE] User-initiated retry for {preview_id}")

    story_data['retry_attempted'] = True
    story_data['generation_failed'] = False
    story_data['book_composing'] = False
    story_data['generation_error'] = ''
    with open(preview_file, 'w', encoding='utf-8') as f:
        json.dump(story_data, f, ensure_ascii=False, indent=2)

    _trigger_personalized_book_composition(preview_id)

    return jsonify({'success': True, 'message': 'Retry started'})


@app.route('/api/generation-status/<preview_id>')
def api_generation_status(preview_id):
    preview_file = f'story_previews/{preview_id}.json'
    if not os.path.exists(preview_file):
        return jsonify({'status': 'not_found'}), 404
    
    with open(preview_file, 'r', encoding='utf-8') as f:
        story_data = json.load(f)
    
    scenes_pending = story_data.get('scenes_pending', False)
    scenes_generating = story_data.get('scenes_generating', False)
    generation_failed = story_data.get('generation_failed', False)
    book_composing = story_data.get('book_composing', False)
    is_illustrated_book = story_data.get('is_illustrated_book', False)
    scene_paths = story_data.get('scene_paths', [])
    
    if is_illustrated_book and (scenes_pending or scenes_generating):
        # PB uses "book_compose_" task ID; QS uses "scene_gen_"
        scene_task = task_queue.get_status(f"scene_gen_{preview_id}") or \
                     task_queue.get_status(f"book_compose_{preview_id}")
        if scene_task and scene_task.get('status') == 'completed':
            with open(preview_file, 'r', encoding='utf-8') as f:
                story_data = json.load(f)
            scene_paths = story_data.get('scene_paths', [])
            if story_data.get('book_scenes_ready', False):
                return jsonify({
                    'status': 'scenes_ready',
                    'generated': len(scene_paths),
                    'expected': len(scene_paths),
                    'scene_paths': scene_paths,
                    'error': ''
                })
            prog = _generation_progress.get(preview_id) or _read_progress(preview_id)
            total = max(prog.get('total', 1), 1)
            generated = prog.get('generated', total)
            return jsonify({
                'status': 'generating',
                'generated': min(generated, total),
                'expected': total,
                'scene_paths': [],
                'error': ''
            })
        elif scene_task and scene_task.get('status') == 'failed':
            # Task failed — reset flags in JSON so the book doesn't stay stuck forever
            try:
                with open(preview_file, 'r', encoding='utf-8') as f:
                    _sd = json.load(f)
                if _sd.get('scenes_pending') or _sd.get('scenes_generating'):
                    _sd['scenes_pending'] = False
                    _sd['scenes_generating'] = False
                    _sd['generation_failed'] = True
                    _sd['generation_error'] = _sd.get('generation_error', 'Book generation task failed')
                    with open(preview_file, 'w', encoding='utf-8') as f:
                        json.dump(_sd, f, ensure_ascii=False, indent=2)
            except Exception:
                pass
            return jsonify({
                'status': 'failed',
                'generated': 0,
                'expected': 1,
                'scene_paths': [],
                'error': story_data.get('generation_error', 'Scene generation failed')
            })
        # No task found in queue at all — book may be stuck if app restarted mid-generation
        # Check if it's been too long without progress (>20 min) and mark as failed
        import time as _time
        gen_started = story_data.get('generation_started_at', 0)
        if gen_started and (_time.time() - gen_started) > 1200:
            try:
                with open(preview_file, 'r', encoding='utf-8') as f:
                    _sd = json.load(f)
                if _sd.get('scenes_pending') or _sd.get('scenes_generating'):
                    _sd['scenes_pending'] = False
                    _sd['scenes_generating'] = False
                    _sd['generation_failed'] = True
                    _sd['generation_error'] = 'Generation timed out - please contact support'
                    with open(preview_file, 'w', encoding='utf-8') as f:
                        json.dump(_sd, f, ensure_ascii=False, indent=2)
            except Exception:
                pass
            return jsonify({
                'status': 'failed',
                'generated': 0,
                'expected': 1,
                'scene_paths': [],
                'error': 'Generation timed out'
            })
        prog = _generation_progress.get(preview_id) or _read_progress(preview_id)
        return jsonify({
            'status': 'generating',
            'generated': prog.get('generated', 0),
            'expected': max(prog.get('total', 1), 1),
            'scene_paths': [],
            'error': ''
        })
    
    if is_illustrated_book and story_data.get('scenes_retrying', False):
        failed_scenes = story_data.get('failed_scenes', [])
        retry_count = story_data.get('retry_count', 0)
        max_retries = story_data.get('max_retries', 6)
        return jsonify({
            'status': 'retrying',
            'generated': len(scene_paths),
            'expected': len(scene_paths),
            'scene_paths': scene_paths,
            'error': '',
            'failed_scenes': [i+1 for i in failed_scenes],
            'retry_count': retry_count,
            'max_retries': max_retries
        })
    
    if is_illustrated_book and story_data.get('book_scenes_ready') and not story_data.get('pages_composed', False) and not book_composing:
        return jsonify({
            'status': 'scenes_ready',
            'generated': len(scene_paths),
            'expected': len(scene_paths),
            'scene_paths': scene_paths,
            'error': ''
        })
    
    if is_illustrated_book and book_composing:
        compose_task = task_queue.get_status(f"book_compose_{preview_id}")
        if compose_task and compose_task.get('status') == 'completed':
            with open(preview_file, 'r', encoding='utf-8') as f:
                story_data = json.load(f)
            scene_paths = story_data.get('scene_paths', [])
            if story_data.get('pages_composed', False):
                # Clear the composing flag so the template stops polling on reload
                if story_data.get('book_composing', False):
                    story_data['book_composing'] = False
                    with open(preview_file, 'w', encoding='utf-8') as f:
                        json.dump(story_data, f, ensure_ascii=False, indent=2)
                lulu_status = story_data.get('lulu_status', '')
                lulu_error = story_data.get('lulu_error', '')
                return jsonify({
                    'status': 'complete',
                    'generated': len(scene_paths),
                    'expected': len(scene_paths),
                    'scene_paths': scene_paths,
                    'error': '',
                    'lulu_status': lulu_status,
                    'lulu_error': lulu_error
                })
        elif compose_task and compose_task.get('status') == 'failed':
            return jsonify({
                'status': 'failed',
                'generated': 0,
                'expected': 1,
                'scene_paths': [],
                'error': story_data.get('generation_error', 'Book composition failed')
            })
        else:
            # Task not found in queue (app may have restarted) — if pages already composed, return complete
            if story_data.get('pages_composed', False):
                with open(preview_file, 'r', encoding='utf-8') as f:
                    story_data = json.load(f)
                story_data['book_composing'] = False
                with open(preview_file, 'w', encoding='utf-8') as f:
                    json.dump(story_data, f, ensure_ascii=False, indent=2)
                scene_paths = story_data.get('scene_paths', [])
                lulu_status = story_data.get('lulu_status', '')
                lulu_error = story_data.get('lulu_error', '')
                return jsonify({
                    'status': 'complete',
                    'generated': len(scene_paths),
                    'expected': len(scene_paths),
                    'scene_paths': scene_paths,
                    'error': '',
                    'lulu_status': lulu_status,
                    'lulu_error': lulu_error
                })
            import time as _st
            generation_started = story_data.get('generation_started_at', 0)
            elapsed = _st.time() - generation_started if generation_started else 0
            COMPOSE_TIMEOUT_SEC = 25 * 60
            task_alive = compose_task and compose_task.get('status') in ('pending', 'processing')
            if not task_alive and elapsed > COMPOSE_TIMEOUT_SEC:
                production_logger.warning(
                    f"[STATUS] book_compose_{preview_id} timed out after {elapsed/60:.1f}min — marking failed"
                )
                story_data['book_composing'] = False
                story_data['generation_error'] = (
                    'La composición del libro tardó demasiado. Por favor, contacta con soporte o reinténtalo.'
                )
                with open(preview_file, 'w', encoding='utf-8') as _pf:
                    json.dump(story_data, _pf, ensure_ascii=False, indent=2)
                return jsonify({
                    'status': 'failed',
                    'generated': 0,
                    'expected': 1,
                    'scene_paths': [],
                    'error': story_data['generation_error']
                })
        return jsonify({
            'status': 'composing',
            'generated': 0,
            'expected': 1,
            'scene_paths': [],
            'error': ''
        })
    
    if is_illustrated_book and story_data.get('pages_composed', False):
        return jsonify({
            'status': 'complete',
            'generated': len(scene_paths),
            'expected': len(scene_paths),
            'scene_paths': scene_paths,
            'error': ''
        })
    
    output_dir = story_data.get('output_dir', '')
    generated_count = 0
    if output_dir and os.path.exists(output_dir):
        generated_count = len([
            f for f in os.listdir(output_dir) 
            if f.startswith('scene_') and f.endswith('.png') and f != 'scene_0.png'
            and os.path.getsize(os.path.join(output_dir, f)) > 1000
        ])
    
    from services.fixed_stories import STORIES as FS_CHECK
    story_id = story_data.get('story_id', '')
    _fs_story_cfg = FS_CHECK.get(story_id, {})
    _has_closing_img = bool(story_data.get('closing_message') or _fs_story_cfg.get('closing_message_es') or _fs_story_cfg.get('closing_message_en'))
    expected = (len(story_data.get('pages', [])) or len(_fs_story_cfg.get('pages', [])) or 8) + (1 if _has_closing_img else 0)
    
    is_qs = not is_illustrated_book and story_id in FS_CHECK
    qs_text_composed = story_data.get('qs_text_composed', False)

    if generated_count >= expected and scenes_pending:
        if is_qs:
            # For Quick Stories: NEVER auto-write to JSON here.
            # Only BG-GEN has authority to set scenes_pending=False and qs_text_composed=True.
            # Premature writes here cause a race condition that breaks the ebook flow.
            qs_task = task_queue.get_status(f"scene_gen_{preview_id}")
            if qs_task and qs_task.get('status') == 'completed':
                with open(preview_file, 'r', encoding='utf-8') as f:
                    story_data = json.load(f)
                scene_paths = story_data.get('scene_paths', [])
                qs_text_composed = story_data.get('qs_text_composed', False)
                status = 'complete' if qs_text_composed else 'composing_text'
            elif qs_task and qs_task.get('status') == 'failed':
                status = 'failed'
            else:
                prog = _generation_progress.get(preview_id) or _read_progress(preview_id)
                if prog:
                    generated_count = prog.get('generated', generated_count)
                    expected = max(prog.get('total', expected), expected)
                status = 'generating'
        else:
            formatted = []
            sorted_scenes = sorted([
                fn for fn in os.listdir(output_dir)
                if fn.startswith('scene_') and fn.endswith('.png') and fn != 'scene_0.png'
                and os.path.getsize(os.path.join(output_dir, fn)) > 1000
            ])
            for fn in sorted_scenes[:expected]:
                formatted.append(f'/{output_dir}/{fn}')
            scene_paths = formatted
            story_data['scene_paths'] = formatted
            story_data['images'] = formatted
            story_data['original_scene_paths'] = formatted
            story_data['original_images'] = formatted
            story_data['scenes_pending'] = False
            story_data['scenes_generating'] = False
            story_data['generation_failed'] = False
            with open(preview_file, 'w', encoding='utf-8') as f:
                json.dump(story_data, f, ensure_ascii=False, indent=2)
            status = 'complete'
    elif generation_failed:
        status = 'failed'
    elif not scenes_pending and len(scene_paths) > 0:
        if is_qs and not qs_text_composed:
            with open(preview_file, 'r', encoding='utf-8') as f:
                story_data = json.load(f)
            qs_text_composed = story_data.get('qs_text_composed', False)
            status = 'complete' if qs_text_composed else 'composing_text'
        else:
            status = 'complete'
    elif scenes_generating:
        status = 'generating'
    elif scenes_pending:
        task_status = task_queue.get_status(f"scene_gen_{preview_id}")
        if task_status and task_status.get('status') in ['pending', 'processing']:
            status = 'generating'
        else:
            _trigger_background_generation(preview_id)
            status = 'generating'
    else:
        if is_qs and not qs_text_composed:
            with open(preview_file, 'r', encoding='utf-8') as f:
                story_data = json.load(f)
            qs_text_composed = story_data.get('qs_text_composed', False)
            status = 'complete' if qs_text_composed else 'composing_text'
        else:
            status = 'complete'
    
    if status == 'generating':
        prog = _generation_progress.get(preview_id) or _read_progress(preview_id)
        if prog:
            generated_count = prog.get('generated', generated_count)
            expected = max(prog.get('total', expected), expected)

    _es_email_sent = story_data.get('email_sent', False) or story_data.get('pdf_email_sent', False) or story_data.get('ebook_email_sent', False)
    return jsonify({
        'status': status,
        'generated': generated_count,
        'expected': expected,
        'scene_paths': scene_paths if status == 'complete' else [],
        'error': story_data.get('generation_error', '') if generation_failed else '',
        'email_sent': _es_email_sent
    })

@app.route('/api/story-status/<preview_id>')
def api_story_status(preview_id):
    """Lightweight endpoint to check visor/ebook readiness for post-payment polling."""
    preview_file = f'story_previews/{preview_id}.json'
    if not os.path.exists(preview_file):
        return jsonify({'error': 'not_found'}), 404
    try:
        with open(preview_file, 'r', encoding='utf-8') as f:
            story_data = json.load(f)
    except Exception:
        return jsonify({'error': 'read_error'}), 500
    visor_url = story_data.get('visor_url', '')
    visor_uploaded = story_data.get('visor_uploaded', False)
    email_sent = (story_data.get('email_sent', False)
                  or story_data.get('ebook_email_sent', False)
                  or story_data.get('pdf_email_sent', False))
    scenes_pending = (story_data.get('scenes_pending', False)
                      or story_data.get('scenes_generating', False))
    return jsonify({
        'visor_ready': bool(visor_uploaded and visor_url),
        'visor_url': visor_url,
        'email_sent': email_sent,
        'scenes_pending': scenes_pending,
    })


@app.route('/api/track-order/<preview_id>')
def api_track_order(preview_id):
    """API endpoint to get tracking info for a printed book order."""
    cp_order_ref = None
    lulu_job_id = None

    if preview_id.startswith('haz_tu_historia_'):
        order_number = preview_id.replace('haz_tu_historia_', '')
        order = RealStoryOrder.query.filter_by(order_number=order_number).first()
        if order:
            lulu_job_id = order.lulu_job_id
    else:
        preview_file = f'story_previews/{preview_id}.json'
        if os.path.exists(preview_file):
            with open(preview_file, 'r', encoding='utf-8') as f:
                story_data = json.load(f)
            cp_order_ref = story_data.get('cp_order_ref')
            lulu_job_id = story_data.get('lulu_job_id')

    if cp_order_ref:
        from services.cloudprinter_api_service import get_order_status
        tracking_info = get_order_status(cp_order_ref)
        if tracking_info:
            return jsonify({'success': True, 'tracking': tracking_info})
        return jsonify({'success': False, 'error': 'Could not retrieve tracking information'}), 500
    elif lulu_job_id:
        return jsonify({
            'success': True,
            'tracking': {
                'status': 'historical',
                'status_text': {'es': 'Procesado por imprenta anterior', 'en': 'Processed by previous printer'},
                'tracking_number': None, 'tracking_url': None, 'carrier': None
            }
        })
    else:
        return jsonify({'success': False, 'error': 'No print job ID found for this order'}), 404


@app.route('/api/regenerate-quick-scene/<preview_id>/<int:scene_num>', methods=['POST'])
def regenerate_quick_scene(preview_id, scene_num):
    """Regenerate a single scene image for a quick story. Max 2 regenerations per scene."""
    from services.replicate_service import generate_scene_with_ideogram
    from services.fixed_stories import get_scene_prompts, STORIES
    
    preview_file = f'story_previews/{preview_id}.json'
    if not os.path.exists(preview_file):
        return jsonify({'success': False, 'error': 'Story not found'}), 404
    
    with open(preview_file, 'r', encoding='utf-8') as f:
        story_data = json.load(f)
    
    scene_paths = story_data.get('images', [])
    original_paths = story_data.get('original_images', story_data.get('original_scene_paths', []))
    
    if scene_num < 1 or scene_num > len(scene_paths):
        return jsonify({'success': False, 'error': 'Invalid scene number'}), 400
    
    regen_counts = story_data.get('scene_regenerations', {})
    scene_key = str(scene_num)
    current_count = regen_counts.get(scene_key, 0)
    
    if current_count >= 2 and not is_testing_mode_active():
        lang = story_data.get('lang', 'es')
        error_msg = 'Has alcanzado el límite de 2 regeneraciones para esta escena' if lang == 'es' else 'You have reached the limit of 2 regenerations for this scene'
        return jsonify({'success': False, 'error': error_msg}), 400
    
    story_id = story_data.get('story_id', '')
    child_name = story_data.get('child_name', 'Child')
    gender = story_data.get('gender', 'neutral')
    traits = story_data.get('traits', {})
    output_dir = story_data.get('output_dir', story_data.get('image_dir', ''))
    
    if not output_dir:
        output_dir = f'story_previews/{preview_id}_images'
    
    os.makedirs(output_dir, exist_ok=True)
    
    story_config = STORIES.get(story_id, {})
    age_range = story_config.get('age_range', '0-1')
    
    try:
        from services.quick_stories.checkout import is_quick_story as check_qs_regen
        from services.replicate_service import KONTEXT_STORY_IDS as _KSI
        is_qs_regen = check_qs_regen(story_id)
        _use_kontext_real_regen = story_id in _KSI
        # Kontext strips CAST: at runtime; FLUX 2 Dev needs use_reference_image=True for @image1 tokens
        scene_prompts = get_scene_prompts(story_id, child_name, gender, traits, use_reference_image=(is_qs_regen and not _use_kontext_real_regen))
        scene_index = scene_num - 1
        
        if scene_index >= len(scene_prompts):
            return jsonify({'success': False, 'error': 'Scene prompt not found'}), 400
        
        prompt = scene_prompts[scene_index]
        regen_aspect = "3:4"
        
        print(f"[REGENERATE-QS] Regenerating scene {scene_num} for {preview_id} (attempt {current_count + 1}/2, aspect: {regen_aspect})")
        
        hair_length_regen = traits.get('hair_length', 'medium')
        child_age_regen = int(traits.get('child_age', '1'))
        
        from services.quick_stories.checkout import ALL_QUICK_FAMILY_IDS as QS_REGEN_IDS
        is_qs_regen_model = story_id in QS_REGEN_IDS
        
        ref_image_regen = None
        if is_qs_regen_model and output_dir:
            clean_cover = f"{output_dir}/cover_clean.png"
            base_char = f"{output_dir}/base_character.png"
            cover_file = f"{output_dir}/cover.png"
            if os.path.exists(clean_cover):
                ref_image_regen = clean_cover
            elif os.path.exists(base_char):
                ref_image_regen = base_char
            elif os.path.exists(cover_file):
                ref_image_regen = cover_file
        
        is_baby_regen = age_range in ['0-1', '0-2']
        use_ideogram = story_config.get('use_ideogram_scenes', False) and is_baby_regen

        if use_ideogram and ref_image_regen:
            print(f"[REGENERATE-QS] Using Ideogram Character (ONLY) with reference: {ref_image_regen}")
            new_scene_path = generate_scene_with_ideogram(
                prompt, ref_image_regen, scene_num, regen_aspect, output_dir
            )
        elif use_ideogram and not ref_image_regen:
            return jsonify({'success': False, 'error': 'No reference image found for Ideogram regeneration'}), 400
        elif _use_kontext_real_regen and ref_image_regen:
            from services.replicate_service import generate_scene_with_real_kontext
            print(f"[REGENERATE-QS] Using FLUX Kontext Pro with reference: {ref_image_regen}")
            try:
                new_scene_path = generate_scene_with_real_kontext(
                    prompt, ref_image_regen, scene_num, regen_aspect, output_dir,
                    gender=gender, age_range=age_range,
                    hair_length=hair_length_regen, child_age=child_age_regen,
                    story_id=story_id
                )
            except Exception as kontext_err:
                error_str = str(kontext_err)
                print(f"[REGENERATE-QS] Kontext Pro failed for scene {scene_num}: {error_str}")
                is_service_error = any(x in error_str.lower() for x in ["temporarily unavailable", "q_descale", "timeout", "overloaded", "503", "502"])
                if is_service_error:
                    lang = story_data.get('lang', 'es')
                    service_msg = 'El servicio de imágenes está temporalmente ocupado. Por favor intenta regenerar en unos minutos.' if lang == 'es' else 'Image service is temporarily busy. Please try regenerating in a few minutes.'
                    return jsonify({'success': False, 'error': service_msg, 'service_error': True}), 503
                raise
        elif _use_kontext_real_regen and not ref_image_regen:
            return jsonify({'success': False, 'error': 'No reference image found for Kontext regeneration'}), 400
        elif ref_image_regen:
            from services.replicate_service import generate_scene_with_flux2dev
            print(f"[REGENERATE-QS] Using FLUX 2 Dev with reference: {ref_image_regen}")
            try:
                new_scene_path = generate_scene_with_flux2dev(
                    prompt, ref_image_regen, scene_num, regen_aspect, output_dir,
                    gender=gender, age_range=age_range,
                    hair_length=hair_length_regen, child_age=child_age_regen
                )
            except Exception as flux_err:
                error_str = str(flux_err)
                print(f"[REGENERATE-QS] FLUX 2 Dev failed for scene {scene_num}: {error_str}")
                is_service_error = any(x in error_str.lower() for x in ["temporarily unavailable", "q_descale", "timeout", "overloaded", "503", "502"])
                if is_service_error:
                    lang = story_data.get('lang', 'es')
                    service_msg = 'El servicio de imágenes está temporalmente ocupado. Por favor intenta regenerar en unos minutos.' if lang == 'es' else 'Image service is temporarily busy. Please try regenerating in a few minutes.'
                    return jsonify({'success': False, 'error': service_msg, 'service_error': True}), 503
                raise
        else:
            from services.replicate_service import generate_scene_with_flux2dev_no_ref
            print(f"[REGENERATE] Using FLUX 2 Dev WITHOUT reference (no cover_clean found) for {story_id}")
            new_scene_path = generate_scene_with_flux2dev_no_ref(
                prompt, scene_num, output_dir, aspect_ratio=regen_aspect
            )
        
        if new_scene_path and os.path.exists(new_scene_path):
            from services.quick_stories.checkout import is_quick_story as check_qs_compose
            if check_qs_compose(story_id):
                try:
                    from services.quick_stories.image_composer import compose_baby_text_on_image, compose_kids_text_on_image
                    from PIL import Image as PILImage
                    pages_data_regen = story_data.get('pages', [])
                    text_layout_regen = story_config.get('text_layout', 'single')
                    lang_regen = story_data.get('lang', story_data.get('language', 'es'))
                    if scene_index < len(pages_data_regen):
                        page_regen = pages_data_regen[scene_index]
                        img_regen = PILImage.open(new_scene_path)
                        if text_layout_regen == 'split':
                            ta = page_regen.get('text_above', '')
                            tb = page_regen.get('text_below', '')
                            if not ta and not tb:
                                ta = page_regen.get('text', '')
                            composed_regen = compose_kids_text_on_image(img_regen, ta, tb, lang_regen)
                        else:
                            txt = page_regen.get('text', '')
                            composed_regen = compose_baby_text_on_image(img_regen, txt, lang_regen)
                        composed_regen.save(new_scene_path, 'PNG')
                        print(f"[REGENERATE-QS] Composed text on regenerated scene {scene_num}")
                except Exception as comp_err:
                    print(f"[REGENERATE-QS] Text composition failed: {comp_err}")
            
            is_paid = story_data.get('paid', False)
            formatted_original = new_scene_path if new_scene_path.startswith('/') else f'/{new_scene_path}'
            
            if is_paid:
                print(f"[REGENERATE-QS] Customer has paid - NO watermark applied")
                formatted_preview = formatted_original
            else:
                from services.illustrated_book_service import add_watermark
                from PIL import Image as PILImage
                img = PILImage.open(new_scene_path)
                watermarked = add_watermark(img)
                preview_path = new_scene_path.replace('.png', '_preview.png')
                watermarked.save(preview_path, 'PNG')
                formatted_preview = preview_path if preview_path.startswith('/') else f'/{preview_path}'
            
            while len(scene_paths) <= scene_index:
                scene_paths.append('')
            while len(original_paths) <= scene_index:
                original_paths.append('')
            
            scene_paths[scene_index] = formatted_preview
            original_paths[scene_index] = formatted_original
            
            story_data['images'] = scene_paths
            story_data['scene_paths'] = scene_paths
            story_data['original_images'] = original_paths
            story_data['original_scene_paths'] = original_paths
            
            if story_data.get('cp_submitted') or story_data.get('lulu_submitted'):
                story_data['cp_needs_refresh'] = True
                story_data['cp_submitted'] = False
                story_data['lulu_submitted'] = False
                print(f"[REGENERATE-QS] Print PDF marked for refresh after scene regeneration")
            
            story_data['visor_uploaded'] = False
            story_data['visor_url'] = ''
            story_data['pdf_printable_path'] = ''
            print(f"[REGENERATE-QS] Visor and PDF flags reset — will regenerate on next confirm_and_send")
            
            if 'scene_regenerations' not in story_data:
                story_data['scene_regenerations'] = {}
            story_data['scene_regenerations'][scene_key] = current_count + 1
            
            with open(preview_file, 'w', encoding='utf-8') as f:
                json.dump(story_data, f, ensure_ascii=False, indent=2)
            
            print(f"[REGENERATE-QS] Scene {scene_num} regenerated successfully")
            
            return jsonify({
                'success': True,
                'image_url': formatted_preview,
                'remaining': 2 - (current_count + 1)
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to generate new image'}), 500
    
    except Exception as e:
        print(f"[REGENERATE-QS] Error: {e}")
        import traceback
        traceback.print_exc()
        error_msg = 'El servicio de generación de imágenes está temporalmente no disponible. Por favor intenta de nuevo en unos minutos.' if 'FLUX' in str(e) or 'q_descale' in str(e) or 'Ideogram' in str(e) else str(e)
        return jsonify({'success': False, 'error': error_msg}), 500


@app.route('/api/regenerate-quick-closing/<preview_id>', methods=['POST'])
def regenerate_quick_closing(preview_id):
    """Regenerate the closing illustration for a quick story. Max 2 regenerations."""
    from services.fixed_stories import get_closing_prompt, STORIES
    from services.replicate_service import generate_scene_with_flux2dev, generate_scene_with_flux2dev_no_ref

    preview_file = f'story_previews/{preview_id}.json'
    if not os.path.exists(preview_file):
        return jsonify({'success': False, 'error': 'Story not found'}), 404

    with open(preview_file, 'r', encoding='utf-8') as f:
        story_data = json.load(f)

    lang = story_data.get('lang', 'es')
    regen_counts = story_data.get('scene_regenerations', {})
    current_count = regen_counts.get('closing', 0)

    if current_count >= 2 and not is_testing_mode_active():
        error_msg = 'Has alcanzado el límite de 2 regeneraciones para la página de cierre' if lang == 'es' else 'You have reached the limit of 2 regenerations for the closing page'
        return jsonify({'success': False, 'error': error_msg}), 400

    story_id = story_data.get('story_id', '')
    child_name = story_data.get('child_name', 'Child')
    gender = story_data.get('gender', 'neutral')
    traits = story_data.get('traits', {})
    output_dir = story_data.get('output_dir', story_data.get('image_dir', ''))
    if not output_dir:
        output_dir = f'story_previews/{preview_id}_images'
    os.makedirs(output_dir, exist_ok=True)

    story_config = STORIES.get(story_id, {})
    age_range = story_config.get('age_range', '0-1')
    hair_length = traits.get('hair_length', 'medium')
    hair_color = traits.get('hair_color', 'brown')
    child_age = int(traits.get('child_age', '1'))

    try:
        closing_prompt = get_closing_prompt(story_id, child_name, gender, traits, use_reference_image=True)
        if not closing_prompt:
            return jsonify({'success': False, 'error': 'No closing template for this story'}), 400

        print(f"[REGEN-CLOSING] Regenerating closing for {preview_id} (attempt {current_count + 1}/2)")

        ref_image = None
        clean_cover = f"{output_dir}/cover_clean.png"
        base_char = f"{output_dir}/base_character.png"
        cover_file = f"{output_dir}/cover.png"
        if os.path.exists(clean_cover):
            ref_image = clean_cover
        elif os.path.exists(base_char):
            ref_image = base_char
        elif os.path.exists(cover_file):
            ref_image = cover_file

        aspect = "3:4"
        closing_num = 99

        if ref_image:
            new_closing_path = generate_scene_with_flux2dev(
                closing_prompt, ref_image, closing_num, aspect, output_dir,
                gender=gender, age_range=age_range, hair_length=hair_length,
                child_age=child_age, hair_color=hair_color
            )
        else:
            new_closing_path = generate_scene_with_flux2dev_no_ref(
                closing_prompt, closing_num, output_dir, aspect_ratio=aspect
            )

        if new_closing_path and os.path.exists(new_closing_path):
            final_path = f"{output_dir}/closing.png"
            import shutil
            shutil.copy2(new_closing_path, final_path)
            if new_closing_path != final_path and os.path.exists(new_closing_path):
                os.remove(new_closing_path)

            qs_text_composed = story_data.get('qs_text_composed', False)
            closing_msg = story_data.get('closing_message', '')
            if qs_text_composed and closing_msg:
                try:
                    from services.quick_stories.image_composer import compose_kids_text_on_image
                    from PIL import Image as _PILRegen
                    _ci = _PILRegen.open(final_path).convert('RGBA')
                    _composed = compose_kids_text_on_image(_ci, '', closing_msg, lang)
                    _ci.close()
                    _composed.save(final_path, 'PNG')
                    _composed.close()
                    print(f"[REGEN-CLOSING] Closing message recomposed on regenerated image")
                except Exception as _ce:
                    print(f"[REGEN-CLOSING] Could not recompose closing message: {_ce}")

            is_paid = story_data.get('paid', False)
            formatted = f'/{final_path}' if not final_path.startswith('/') else final_path

            if not is_paid:
                from services.illustrated_book_service import add_watermark
                from PIL import Image as PILImage
                img = PILImage.open(final_path)
                watermarked = add_watermark(img)
                preview_path = final_path.replace('.png', '_preview.png')
                watermarked.save(preview_path, 'PNG')
                formatted = f'/{preview_path}' if not preview_path.startswith('/') else preview_path

            story_data['closing_image'] = formatted
            story_data['visor_uploaded'] = False
            story_data['visor_url'] = ''
            story_data['pdf_printable_path'] = ''

            if 'scene_regenerations' not in story_data:
                story_data['scene_regenerations'] = {}
            story_data['scene_regenerations']['closing'] = current_count + 1

            with open(preview_file, 'w', encoding='utf-8') as f:
                json.dump(story_data, f, ensure_ascii=False, indent=2)

            print(f"[REGEN-CLOSING] Closing regenerated successfully")
            return jsonify({'success': True, 'image_url': formatted, 'remaining': 2 - (current_count + 1)})
        else:
            return jsonify({'success': False, 'error': 'Failed to generate closing image'}), 500

    except Exception as e:
        print(f"[REGEN-CLOSING] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


def _regenerate_page_task(preview_id, page_num, scene_config, is_closing_page,
                           child_name, gender, lang, traits, book_id,
                           ref_image_path, ref_image_path_2, current_count,
                           preview_file, task_result=None):
    """Background task: FLUX generation + text + save + counter. Runs in TaskQueue worker.
    Ends immediately after saving page_NN.png and persisting the counter.
    rebuild_book() is NOT called here — it runs only when the user approves
    via approve_scenes() → _trigger_personalized_book_composition().
    """
    from services.illustrated_book_service import (
        generate_scene_complete, generate_closing_page, add_text_to_image, load_book_config
    )

    is_furry = book_id in ('furry_love', 'furry_love_adventure', 'furry_love_teen', 'furry_love_adult')
    page_label = "closing" if is_closing_page else f"scene {scene_config.get('id', '?') + 1}"
    print(f"[REGENERATE] Regenerating page {page_num} ({page_label}) for {preview_id}...")
    print(f"[REGENERATE] Regeneration count for this page: {current_count + 1}/2")

    if is_closing_page:
        base_image = generate_closing_page(
            traits=traits, child_name=child_name, gender=gender, book_id=book_id,
            reference_image_path=ref_image_path, reference_image_path_2=ref_image_path_2
        )
        final_image = base_image
    else:
        base_image = generate_scene_complete(
            scene_config=scene_config, traits=traits, child_name=child_name,
            gender=gender, language=lang, book_id=book_id,
            reference_image_path=ref_image_path, reference_image_path_2=ref_image_path_2
        )
        text_key = f'text_{lang}'
        pet_name_regen = traits.get('pet_name', '') if is_furry else ''
        text = scene_config.get(text_key, scene_config.get('text_es', '')).replace('{name}', child_name).replace('{pet_name}', pet_name_regen)
        text_position = scene_config.get('text_position', 'bottom')
        final_image = add_text_to_image(base_image, text, position=text_position)

    composed_dir = f'generated/composed_{preview_id}'
    os.makedirs(composed_dir, exist_ok=True)
    original_path = os.path.join(composed_dir, f'page_{page_num:02d}.png')
    final_image.save(original_path, 'PNG')
    print(f"[REGENERATE] Saved: {original_path} (no watermark, post-payment)")

    with open(preview_file, 'r', encoding='utf-8') as f:
        story_data = json.load(f)
    regen_counts = story_data.get('page_regenerations') or {}
    regen_counts[str(page_num)] = current_count + 1
    story_data['page_regenerations'] = regen_counts
    with open(preview_file, 'w', encoding='utf-8') as f:
        json.dump(story_data, f, ensure_ascii=False, indent=2)

    return {
        'success': True,
        'image_path': f'/{original_path}',
        'regenerations_left': 2 - (current_count + 1)
    }


@app.route('/api/regenerate-page/<preview_id>/<int:page_num>', methods=['POST'])
def regenerate_page(preview_id, page_num):
    """Enqueue async page regeneration. Returns job_id immediately; client polls /api/regen-page-status/<job_id>."""
    from services.illustrated_book_service import load_book_config
    from services.personalized_books.generation import get_personalized_book_id

    preview_file = f'story_previews/{preview_id}.json'
    if not os.path.exists(preview_file):
        return jsonify({'success': False, 'error': 'Story not found'}), 404

    with open(preview_file, 'r', encoding='utf-8') as f:
        story_data = json.load(f)

    if page_num < 3 or page_num > 21:
        return jsonify({'success': False, 'error': 'Solo se pueden regenerar las páginas 3 a 21'}), 400

    regen_counts = story_data.get('page_regenerations') or {}
    page_key = str(page_num)
    current_count = regen_counts.get(page_key, 0)

    if current_count >= 2 and not is_testing_mode_active():
        return jsonify({'success': False, 'error': 'Has alcanzado el límite de 2 regeneraciones para esta página'}), 400

    story_id = story_data.get('story_id', 'dragon_garden_illustrated')
    book_id = get_personalized_book_id(story_id)
    book_config = load_book_config(book_id)
    if not book_config:
        return jsonify({'success': False, 'error': f'Book config not found for {book_id}'}), 400

    scenes = book_config.get('scenes', [])
    is_closing_page = (page_num == 22)
    scene_config = {}
    if not is_closing_page:
        scene_index = page_num - 3
        if scene_index < 0 or scene_index >= len(scenes):
            return jsonify({'success': False, 'error': f'Invalid scene index: {scene_index}'}), 400
        scene_config = scenes[scene_index]

    child_name = story_data.get('child_name', 'Child')
    gender = story_data.get('gender', 'neutral')
    lang = story_data.get('story_lang', story_data.get('lang', 'es'))
    traits = story_data.get('traits', {})

    is_furry = book_id in ('furry_love', 'furry_love_adventure', 'furry_love_teen', 'furry_love_adult')
    ref_image_path = None
    ref_image_path_2 = None

    if is_furry:
        human_preview = story_data.get('human_preview_path', '')
        if human_preview:
            hr = human_preview.lstrip('/')
            if os.path.exists(hr):
                ref_image_path = hr
        pet_preview = story_data.get('pet_preview_path', '')
        if pet_preview:
            pr = pet_preview.lstrip('/')
            if os.path.exists(pr):
                ref_image_path_2 = pr
    else:
        character_preview = story_data.get('character_preview', '')
        if character_preview:
            rc = character_preview.lstrip('/')
            if os.path.exists(rc):
                ref_image_path = rc
        companion_map = {
            'star_keeper': 'static/assets/luna_reference.png',
            'dragon_garden': 'static/assets/spark_reference.png',
            'centinela_aurora': 'static/assets/astro_reference.png',
        }
        companion = companion_map.get(book_id)
        if companion and os.path.exists(companion):
            ref_image_path_2 = companion

    if not ref_image_path:
        return jsonify({'success': False, 'error': 'No se encontró la imagen de referencia. Por favor contacta soporte.'}), 400

    # Prevent duplicate concurrent jobs for the same page
    job_id = f"regen_page_{preview_id}_{page_num}"
    existing = task_queue.get_status(job_id)
    if existing and existing.get('status') in ('pending', 'processing'):
        return jsonify({'success': True, 'job_id': job_id, 'status': 'pending'})

    task_queue.enqueue(
        job_id, _regenerate_page_task,
        preview_id, page_num, scene_config, is_closing_page,
        child_name, gender, lang, traits, book_id,
        ref_image_path, ref_image_path_2, current_count, preview_file
    )

    return jsonify({'success': True, 'job_id': job_id, 'status': 'pending'})


@app.route('/api/regen-page-status/<job_id>', methods=['GET'])
def regen_page_status(job_id):
    """Poll the status of a page regeneration job."""
    status = task_queue.get_status(job_id)
    if not status:
        return jsonify({'status': 'not_found'})

    task_status = status.get('status', 'unknown')

    if task_status == 'completed':
        result = status.get('result') or {}
        return jsonify({
            'status': 'completed',
            'success': result.get('success', True),
            'image_path': result.get('image_path', ''),
            'regenerations_left': result.get('regenerations_left', 0)
        })
    elif task_status == 'failed':
        error = status.get('error', 'Error desconocido')
        error_msg = 'El servicio de generación de imágenes está temporalmente no disponible. Por favor intenta de nuevo.' if 'FLUX' in error or 'timeout' in error.lower() else error
        return jsonify({'status': 'failed', 'error': error_msg})
    else:
        return jsonify({'status': task_status})


@app.route('/api/confirm-and-send/<preview_id>', methods=['POST'])
def confirm_and_send(preview_id):
    """Confirm story review and send email to customer with file attachments"""
    from services.email_service import send_story_email_with_attachments
    
    preview_file = f'story_previews/{preview_id}.json'
    if not os.path.exists(preview_file):
        return jsonify({'success': False, 'error': 'Story not found'}), 404
    
    with open(preview_file, 'r', encoding='utf-8') as f:
        story_data = json.load(f)
    
    from services.quick_stories.checkout import is_quick_story as _check_qs_confirm
    _is_qs_confirm = _check_qs_confirm(story_data.get('story_id', ''))
    from services.personalized_books.generation import is_personalized_book as _check_pb_confirm
    _is_pb_confirm = _check_pb_confirm(story_data.get('story_id', ''))
    if _is_qs_confirm:
        with _ebook_processing_lock:
            _qs_bg_active = preview_id in _ebook_processing_locks
        if _qs_bg_active:
            print(f"[CONFIRM-SEND] Background ebook processing active for {preview_id}, skipping to avoid duplicate")
            return jsonify({'success': True, 'processing': True, 'message': 'Processing in background'})
        _qs_print_done = not story_data.get('want_print') or story_data.get('cp_submitted') or story_data.get('print_confirmation_sent')
        if story_data.get('email_sent') and _qs_print_done:
            return jsonify({'success': True, 'message': 'Email already sent'})
        if story_data.get('email_sent') and not _qs_print_done:
            print(f"[CONFIRM-SEND] QS emails done but CP print pending for {preview_id} — launching print only")
            if not story_data.get('visor_uploaded', False):
                print(f"[CONFIRM-SEND] visor_uploaded=False after scene regen — regenerating visor before print for {preview_id}")
                try:
                    from services.vps_upload_service import prepare_and_upload
                    _visor_is_gift = not story_data.get('want_ebook', False)
                    visor_result = prepare_and_upload(story_data, preview_id, is_gift=_visor_is_gift)
                    story_data['visor_url'] = visor_result.get('visor_url', story_data.get('visor_url', ''))
                    story_data['visor_uploaded'] = True
                    with open(preview_file, 'w', encoding='utf-8') as f:
                        json.dump(story_data, f, ensure_ascii=False, indent=2)
                    print(f"[CONFIRM-SEND] Visor regenerated after scene regen: {story_data['visor_url']}")
                except Exception as _visor_regen_err:
                    print(f"[CONFIRM-SEND] Visor regen error (non-fatal): {_visor_regen_err}")
            _print_email = story_data.get('customer_email', '')
            t = threading.Thread(
                target=_process_quick_story_print,
                args=(preview_id, _print_email),
                daemon=True
            )
            t.start()
            return jsonify({'success': True, 'already_sent': True, 'print_launched': True, 'message': 'Print job launched'})
        _qs_pdf_done   = not story_data.get('want_pdf')   or story_data.get('pdf_email_sent')
        _qs_ebook_done = not story_data.get('want_ebook') or story_data.get('ebook_email_sent')
        _qs_gift_done  = not (story_data.get('want_pdf') or story_data.get('want_print')) or story_data.get('gift_ebook_sent')
        if _qs_pdf_done and _qs_ebook_done and _qs_gift_done and _qs_print_done:
            print(f"[CONFIRM-SEND] QS emails already sent in background for {preview_id}, skipping resend")
            return jsonify({'success': True, 'already_sent': True, 'message': 'Emails already delivered'})
        if _qs_pdf_done and _qs_ebook_done and _qs_gift_done and not _qs_print_done:
            print(f"[CONFIRM-SEND] QS emails done but CP print pending for {preview_id} — launching print only")
            if not story_data.get('visor_uploaded', False):
                print(f"[CONFIRM-SEND] visor_uploaded=False after scene regen — regenerating visor before print for {preview_id}")
                try:
                    from services.vps_upload_service import prepare_and_upload
                    _visor_is_gift = not story_data.get('want_ebook', False)
                    visor_result = prepare_and_upload(story_data, preview_id, is_gift=_visor_is_gift)
                    story_data['visor_url'] = visor_result.get('visor_url', story_data.get('visor_url', ''))
                    story_data['visor_uploaded'] = True
                    with open(preview_file, 'w', encoding='utf-8') as f:
                        json.dump(story_data, f, ensure_ascii=False, indent=2)
                    print(f"[CONFIRM-SEND] Visor regenerated after scene regen: {story_data['visor_url']}")
                except Exception as _visor_regen_err:
                    print(f"[CONFIRM-SEND] Visor regen error (non-fatal): {_visor_regen_err}")
            _print_email = story_data.get('customer_email', '')
            t = threading.Thread(
                target=_process_quick_story_print,
                args=(preview_id, _print_email),
                daemon=True
            )
            t.start()
            return jsonify({'success': True, 'already_sent': True, 'print_launched': True, 'message': 'Print job launched'})
    elif _is_pb_confirm:
        if story_data.get('email_sent'):
            # Ebook email was sent but check if printable PDF is still pending
            _want_pdf_e = story_data.get('want_pdf') or story_data.get('pdf_paid') or story_data.get('pdf_order')
            if _want_pdf_e and not (story_data.get('pdf_email_sent') or story_data.get('printable_pdf_sent')):
                _lang_e = story_data.get('lang', 'es')
                _email_e = story_data.get('customer_email', '')
                print(f"[CONFIRM-SEND] PB ebook sent but PDF pending — dispatching PDF email for {preview_id}")
                t_pdf_e = threading.Thread(
                    target=_dispatch_printable_pdf_email,
                    args=(preview_id, _email_e, _lang_e),
                    daemon=True
                )
                t_pdf_e.start()
            return jsonify({'success': True, 'message': 'Email already sent'})
        _pb_want_pdf   = story_data.get('want_pdf') or story_data.get('pdf_paid') or story_data.get('pdf_order')
        _pb_want_ebook = story_data.get('want_ebook')
        _pb_want_print = story_data.get('want_print')
        _pb_pdf_done   = not _pb_want_pdf   or story_data.get('pdf_email_sent') or story_data.get('printable_pdf_sent')
        _pb_ebook_done = not _pb_want_ebook or story_data.get('ebook_email_sent')
        _pb_gift_done  = not (_pb_want_print and not _pb_want_ebook) or story_data.get('gift_ebook_sent')
        _pb_print_done = not _pb_want_print or story_data.get('print_confirmation_sent')
        if _pb_pdf_done and _pb_ebook_done and _pb_gift_done and _pb_print_done:
            print(f"[CONFIRM-SEND] PB emails already sent in background for {preview_id}, skipping resend")
            return jsonify({'success': True, 'already_sent': True, 'message': 'Emails already delivered'})
    elif story_data.get('email_sent'):
        return jsonify({'success': True, 'message': 'Email already sent'})

    if story_data.get('is_illustrated_book', False) and not story_data.get('pages_composed', False):
        return jsonify({'success': False, 'error': 'This book requires illustration approval before sending. Please use the Approve Illustrations button.'}), 400
    
    data = request.get_json() or {}
    email = story_data.get('customer_email') or data.get('email', '')
    if email and not story_data.get('customer_email'):
        story_data['customer_email'] = email
        with open(preview_file, 'w', encoding='utf-8') as f:
            json.dump(story_data, f, ensure_ascii=False, indent=2)
    if not email:
        return jsonify({'success': False, 'error': 'No email address found'}), 400
    
    age_range = story_data.get('age_range', '0-1')
    is_baby = age_range in ['0-1', '0-2']
    story_id = story_data.get('story_id', '')
    is_birthday = 'birthday' in story_id.lower()
    text_layout = story_data.get('text_layout', 'single')
    from services.personalized_books.generation import is_personalized_book as check_personalized
    is_personalized_book = check_personalized(story_id)
    
    os.makedirs(f'generations/email/{preview_id}', exist_ok=True)
    
    child_name = story_data.get('child_name', 'Historia')
    safe_name = child_name.replace(' ', '_').replace("'", "")
    
    try:
        want_print = story_data.get('want_print', False)
        want_ebook = story_data.get('want_ebook', False)
        # Visor is gift (6-month) when customer didn't buy the ebook
        _visor_is_gift_cs = not want_ebook
        
        with open(preview_file, 'r', encoding='utf-8') as f:
            story_data = json.load(f)
        visor_url = story_data.get('visor_url', '')
        
        if not visor_url:
            for _visor_attempt in range(2):
                try:
                    print(f"[CONFIRM-SEND] No visor_url — uploading visor (attempt {_visor_attempt + 1}/2) for {preview_id}...")
                    from services.vps_upload_service import prepare_and_upload
                    visor_result = prepare_and_upload(story_data, preview_id, is_gift=_visor_is_gift_cs)
                    visor_url = visor_result.get('visor_url', '')
                    if visor_url:
                        story_data['visor_url'] = visor_url
                        story_data['visor_uploaded'] = True
                        with open(preview_file, 'w', encoding='utf-8') as f:
                            json.dump(story_data, f, ensure_ascii=False, indent=2)
                        print(f"[CONFIRM-SEND] Visor uploaded OK: {visor_url}")
                        break
                    else:
                        print(f"[CONFIRM-SEND] Visor upload returned empty URL (attempt {_visor_attempt + 1}/2)")
                except Exception as visor_err:
                    print(f"[CONFIRM-SEND] Visor upload failed (attempt {_visor_attempt + 1}/2): {visor_err}")
        
        pdf_printable_path = story_data.get('pdf_printable_path')
        instructions_path_email = story_data.get('instructions_path')
        personalized_pdf_url = None

        if want_print and not (story_data.get('want_pdf') or story_data.get('pdf_paid')):
            pdf_printable_path = None
            instructions_path_email = None

        if is_personalized_book:
            pdf_printable_path = None
            instructions_path_email = None
        elif visor_url and not pdf_printable_path and (story_data.get('want_pdf') or story_data.get('pdf_paid')):
            try:
                from services.quick_stories.checkout import is_quick_story as check_qs_cs
                if check_qs_cs(story_data.get('story_id', '')):
                    output_dir = f'generations/email/{preview_id}'
                    os.makedirs(output_dir, exist_ok=True)
                    from services.quick_stories.pdf_service import generate_quick_story_pdf
                    _qs_fmt = story_data.get('print_format', 'A4')
                    if _qs_fmt and _qs_fmt.upper() in ('CARTA', 'LETTER'):
                        _qs_fmt = 'LETTER'
                    elif _qs_fmt:
                        _qs_fmt = 'A4'
                    else:
                        _qs_fmt = 'A4'
                    _fmt_sfx = 'LETTER' if _qs_fmt == 'LETTER' else 'A4'
                    pdf_printable_path = f'{output_dir}/{safe_name}_imprimible_{_fmt_sfx}.pdf'
                    if os.path.exists(pdf_printable_path):
                        print(f"[CONFIRM-SEND] Reusing existing printable PDF: {pdf_printable_path}")
                    else:
                        generate_quick_story_pdf(story_data, pdf_printable_path, print_format=_qs_fmt, format_type='digital')
                        print(f"[CONFIRM-SEND] Printable PDF generated ({_qs_fmt})")
                    story_data['pdf_printable_path'] = pdf_printable_path
                    from services.pdf_service import generate_print_instructions_pdf
                    qs_lang = story_data.get('lang', 'es')
                    instructions_path_email = f'{output_dir}/instrucciones_impresion.pdf'
                    if not os.path.exists(instructions_path_email):
                        generate_print_instructions_pdf(instructions_path_email, language=qs_lang, print_format=_qs_fmt)
                    print(f"[CONFIRM-SEND] PDFs ready: printable + instructions")
            except Exception as pdf_err:
                print(f"[CONFIRM-SEND] PDF generation failed: {pdf_err}")
        
        # --- SHADOW MODE (solo lectura/registro, no afecta el envio real) ---
        try:
            from services.shadow_delivery import run_shadow_comparison_safe
            _actual_planned_cs = []
            if want_print:
                _actual_planned_cs.append('pdf_ready')
            elif story_data.get('want_pdf') or story_data.get('pdf_paid'):
                _actual_planned_cs.append('pdf_ready')
            if want_ebook:
                _actual_planned_cs.append('ebook_permanent_delivery')
            if _visor_is_gift_cs:
                _actual_planned_cs.append('gift_ebook_temp_6mo')
            run_shadow_comparison_safe(
                stage='confirm_and_send',
                story_data=story_data,
                preview_id=preview_id,
                actual_decision={'planned_emails': _actual_planned_cs, 'visor_is_gift': _visor_is_gift_cs},
            )
        except Exception as _shadow_call_err_cs:
            print(f"[SHADOW-DELIVERY] WARNING: shadow hook failed non-fatally in confirm_and_send: {_shadow_call_err_cs}")
        # --- FIN SHADOW MODE ---

        # ── MODO PRUEBA: si is_test_payment=True, omitir envío de email real ──
        if story_data.get('is_test_payment'):
            print(f"[CONFIRM-SEND] TEST PAYMENT — skipping real email for {preview_id} (is_test_payment=True)")
            story_data['email_sent'] = True
            story_data['pdf_email_sent'] = True
            story_data['pages_composed'] = True
            with open(preview_file, 'w', encoding='utf-8') as f:
                json.dump(story_data, f, ensure_ascii=False, indent=2)
            return jsonify({
                'success': True,
                'test_mode': True,
                'message': 'MODO PRUEBA: email omitido. El libro está finalizado en modo test.'
            })
        # ── FIN MODO PRUEBA ──

        from services.email_service import send_ebook_email
        if visor_url:
            email_result = send_ebook_email(
                to_email=email,
                story_data=story_data,
                visor_url=visor_url,
                is_gift=_visor_is_gift_cs,
                pdf_printable_path=pdf_printable_path,
                instructions_path=instructions_path_email,
                pdf_download_url=personalized_pdf_url,
                preview_id=preview_id,
                is_print_order=bool(want_print)
            )
        else:
            email_result = send_story_email_with_attachments(
                to_email=email,
                story_data=story_data,
                pdf_digital_path=None,
                pdf_printable_path=None,
                epub_path=None,
                instructions_path=None,
                age_group='personalized' if is_personalized_book else ('baby' if is_baby else 'kids'),
                preview_id=preview_id,
                visor_url=None
            )
        
        story_data['email_sent'] = True
        story_data['email_sent_date'] = datetime.now().isoformat()
        with open(preview_file, 'w', encoding='utf-8') as f:
            json.dump(story_data, f, ensure_ascii=False, indent=2)

        # For personalized books: if customer purchased printable PDF, dispatch it now
        if is_personalized_book:
            _want_pdf_pb = story_data.get('want_pdf') or story_data.get('pdf_paid') or story_data.get('pdf_order')
            if _want_pdf_pb and not story_data.get('pdf_email_sent') and not story_data.get('printable_pdf_sent'):
                print(f"[CONFIRM-SEND] PB want_pdf=True — launching PDF dispatch for {preview_id}")
                _lang_pb = story_data.get('lang', 'es')
                t_pdf_pb = threading.Thread(
                    target=_dispatch_printable_pdf_email,
                    args=(preview_id, email, _lang_pb),
                    daemon=True
                )
                t_pdf_pb.start()

        lulu_result = None
        is_quick_story = not is_personalized_book
        if want_print and is_quick_story:
            already_submitted = story_data.get('cp_submitted') or story_data.get('lulu_submitted')
            needs_refresh = story_data.get('cp_needs_refresh') or story_data.get('lulu_needs_refresh')
            needs_print = not already_submitted or needs_refresh
            if needs_print:
                if needs_refresh:
                    print(f"[CONFIRM-SEND] Scenes were regenerated after payment - refreshing Cloudprinter PDF...")
                    with open(preview_file, 'r', encoding='utf-8') as f:
                        story_data = json.load(f)
                    story_data['cp_needs_refresh'] = False
                    story_data['lulu_needs_refresh'] = False
                    with open(preview_file, 'w', encoding='utf-8') as f:
                        json.dump(story_data, f, ensure_ascii=False, indent=2)
                else:
                    print(f"[CONFIRM-SEND] Quick Story with want_print=True - launching Cloudprinter print processing...")
                t = threading.Thread(
                    target=_process_quick_story_print,
                    args=(preview_id, email),
                    daemon=True
                )
                t.start()
                lulu_result = {'id': 'processing', 'success': True}
            else:
                print(f"[CONFIRM-SEND] Already submitted for {preview_id}, skipping")
                lulu_result = {'id': story_data.get('cp_order_ref', story_data.get('lulu_job_id', 'already_submitted')), 'success': True}
        
        
        visor_url_resp = story_data.get('visor_url', '')
        
        return jsonify({
            'success': True,
            'email_sent': email_result.get('success', False),
            'email_simulated': email_result.get('simulated', False),
            'lulu_submitted': bool(lulu_result and lulu_result.get('id')) if lulu_result else False,
            'visor_url': visor_url_resp
        })
        
    except Exception as e:
        import traceback
        print(f"[CONFIRM-SEND] Error: {e}")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/request-story-change/<preview_id>', methods=['POST'])
def request_story_change(preview_id):
    """Handle request to change story - marks regeneration as used"""
    preview_file = f'story_previews/{preview_id}.json'
    if not os.path.exists(preview_file):
        return jsonify({'success': False, 'error': 'Story not found'}), 404
    
    with open(preview_file, 'r', encoding='utf-8') as f:
        story_data = json.load(f)
    
    if story_data.get('email_sent'):
        return jsonify({'success': False, 'error': 'Cannot change story after email has been sent'}), 400
    
    if story_data.get('regeneration_used') and not is_testing_mode_active():
        return jsonify({'success': False, 'error': 'You have already used your change opportunity'}), 400
    
    story_data['regeneration_used'] = True
    story_data['original_preview_id'] = preview_id
    
    with open(preview_file, 'w', encoding='utf-8') as f:
        json.dump(story_data, f, ensure_ascii=False, indent=2)
    
    session['paid_customer'] = True
    session['original_preview_id'] = preview_id
    session['customer_email'] = story_data.get('customer_email', '')
    session['customer_phone'] = story_data.get('customer_phone', '')
    session['want_print'] = story_data.get('want_print', False)
    session['child_name'] = story_data.get('child_name', '')
    session['child_gender'] = story_data.get('gender', '')
    
    is_furry = 'furry_love' in story_data.get('story_id', '')
    is_illustrated = story_data.get('is_illustrated_book', False)
    if is_furry:
        redirect_base = '/furry-love'
    elif is_illustrated:
        redirect_base = '/universos-catalog'
    else:
        redirect_base = '/story-selection'
    return jsonify({
        'success': True,
        'redirect_url': f'{redirect_base}?change=1&preview_id={preview_id}'
    })

@app.route('/generated/<path:filepath>')
def serve_generated_image(filepath):
    """Serve generated images from any subdirectory"""
    from flask import send_file, make_response
    image_path = f'generated/{filepath}'
    if os.path.exists(image_path):
        resp = make_response(send_file(image_path, mimetype='image/png'))
        resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        resp.headers['Pragma'] = 'no-cache'
        return resp
    return "Image not found", 404

@app.route('/replicate-image/<filename>')
def serve_replicate_image(filename):
    """Serve a generated Replicate image"""
    from flask import send_file
    image_path = f'generated/replicate/{filename}'
    if os.path.exists(image_path):
        return send_file(image_path, mimetype='image/png')
    return "Image not found", 404


@app.route('/retry-story/<preview_id>')
def retry_story(preview_id):
    """Allow user to retry story generation without additional cost"""
    preview_file = f'story_previews/{preview_id}.json'
    if not os.path.exists(preview_file):
        flash('Story not found. Please contact support at pay@magicmemoriesbooks.com', 'error')
        return redirect(url_for('index'))
    
    with open(preview_file, 'r', encoding='utf-8') as f:
        story_data = json.load(f)
    
    story_data['scenes_pending'] = True
    story_data['scenes_generating'] = False
    story_data['generation_failed'] = False
    story_data.pop('generation_error', None)
    
    with open(preview_file, 'w', encoding='utf-8') as f:
        json.dump(story_data, f, ensure_ascii=False, indent=2)
    
    print(f"[RETRY] Story {preview_id} reset for retry")
    return redirect(url_for('order_complete', preview_id=preview_id))


@app.route('/api/resend-recovery-email/<preview_id>', methods=['POST'])
def resend_recovery_email(preview_id):
    """Resend recovery email with correct link"""
    preview_file = f'story_previews/{preview_id}.json'
    if not os.path.exists(preview_file):
        return jsonify({'success': False, 'error': 'Story not found'}), 404
    
    with open(preview_file, 'r', encoding='utf-8') as f:
        story_data = json.load(f)
    
    customer_email = story_data.get('customer_email')
    if not customer_email:
        return jsonify({'success': False, 'error': 'No email found'}), 400
    
    from services.email_service import send_recovery_link_email
    base_url = os.environ.get('SITE_DOMAIN', os.environ.get('REPLIT_DEV_DOMAIN', 'magicmemoriesbooks.com'))
    recovery_url = f"https://{base_url}/order-complete/{preview_id}"
    child_name = story_data.get('child_name', 'Historia')
    lang = story_data.get('lang', story_data.get('language', 'es'))
    
    success = send_recovery_link_email(
        customer_email, child_name, recovery_url, lang,
        want_ebook=story_data.get('want_ebook', False),
        want_pdf=story_data.get('want_pdf', False),
        want_print=story_data.get('want_print', False),
    )

    if success:
        return jsonify({'success': True, 'message': 'Recovery email sent'})
    else:
        return jsonify({'success': False, 'error': 'Failed to send email'}), 500

@app.route('/api/generate-preview', methods=['POST'])
def generate_preview_api():
    try:
        data = request.get_json()
        
        child_name = data.get('child_name')
        child_gender = data.get('child_gender')
        child_age_range = data.get('child_age_range')
        hair_color = data.get('hair_color')
        hair_type = data.get('hair_type')
        hair_length = data.get('hair_length', 'medium')
        eye_color = data.get('eye_color')
        skin_tone = data.get('skin_tone')
        story_template = data.get('story_template')
        
        if not all([child_name, child_gender, child_age_range, hair_color, hair_type, eye_color, skin_tone, story_template]):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        story_name = story_template
        for template in STORY_TEMPLATES:
            if template['id'] == story_template:
                story_name = template['name_en'] if get_lang() == 'en' else template['name_es']
                break
        
        from services.ai_service import generate_preview
        
        result = generate_preview(
            child_name=child_name,
            child_gender=child_gender,
            child_age_range=child_age_range,
            hair_color=hair_color,
            hair_type=hair_type,
            hair_length=hair_length,
            eye_color=eye_color,
            skin_tone=skin_tone,
            story_template=story_name,
            lang=get_lang()
        )
        
        return jsonify({
            'success': True,
            'preview_text': result['text'],
            'preview_image': result['image_url']
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/renew-ebook/<preview_id>')
def renew_ebook(preview_id):
    preview_file = f'story_previews/{preview_id}.json'
    if not os.path.exists(preview_file):
        preview_file = f'generations/previews/{preview_id}.json'
    if not os.path.exists(preview_file):
        return render_template('base.html'), 404
    with open(preview_file, 'r', encoding='utf-8') as f:
        story_data = json.load(f)
    lang = story_data.get('lang', story_data.get('language', 'es'))
    return render_template(
        'renew_ebook.html',
        preview_id=preview_id,
        child_name=story_data.get('child_name', ''),
        story_name=story_data.get('story_name', ''),
        lang=lang,
        paypal_client_id=Config.PAYPAL_CLIENT_ID,
    )


@app.route('/ebook/<preview_id>')
def ebook(preview_id):
    """Redirect old ebook view to visor"""
    return redirect(url_for('ebook_preview', preview_id=preview_id))

@app.route('/api/generate-pdf/<preview_id>')
def generate_pdf(preview_id):
    format_type = request.args.get('format', 'digital')
    preview_file = f'story_previews/{preview_id}.json'
    
    if not os.path.exists(preview_file):
        return jsonify({'success': False, 'error': 'Preview not found'}), 404
    
    with open(preview_file, 'r', encoding='utf-8') as f:
        story_data = json.load(f)
    
    os.makedirs('generations/pdfs', exist_ok=True)
    
    child_name_safe = "".join(c for c in story_data.get('child_name', 'story') if c.isalnum() or c in ' _-').strip()
    story_template = story_data.get('story_template', story_data.get('story_id', 'story'))
    
    story_id = story_data.get('story_id', '')
    from services.personalized_books.generation import is_personalized_book as check_personalized
    is_personalized_book = check_personalized(story_id)
    
    filename = f"{child_name_safe}_{story_template}_digital.pdf"
    output_path = f'generations/pdfs/{preview_id}_digital.pdf'
    
    if is_personalized_book:
        from services.pdf_service import create_pdf_from_images
        # Use original images (without watermark) - check multiple possible keys
        all_pages = story_data.get('original_images', story_data.get('all_pages_original', story_data.get('original_scene_paths', [])))
        # Use original cover (without watermark)
        front_cover = story_data.get('original_cover', story_data.get('front_cover_path', story_data.get('cover_preview', story_data.get('cover_image'))))
        if front_cover and front_cover.startswith('/'):
            front_cover = front_cover[1:]
        back_cover = story_data.get('back_cover_path')
        if back_cover and back_cover.startswith('/'):
            back_cover = back_cover[1:]
        if not back_cover or not os.path.exists(back_cover):
            _bid = story_data.get('story_id', story_data.get('book_id', ''))
            _fixed_backs = {
                "dragon_garden": "static/images/fixed_pages/_backup/dragon_garden_back_cover.png",
                "magic_chef": "static/images/fixed_pages/magic_chef_back_cover.png",
                "magic_inventor": "static/images/fixed_pages/magic_inventor_back_cover.png",
                "star_keeper": "static/images/fixed_pages/_backup/star_keeper_back_cover.png",
                "furry_love": "static/images/fixed_pages/_backup/furry_love_baby_back_cover.png",
                "furry_love_illustrated": "static/images/fixed_pages/_backup/furry_love_baby_back_cover.png",
                "furry_love_adventure": "static/images/fixed_pages/_backup/furry_love_adventure_back_cover.png",
                "furry_love_teen": "static/images/fixed_pages/_backup/furry_love_teen_back_cover.png",
                "furry_love_adult": "static/images/fixed_pages/_backup/furry_love_adult_back_cover.png",
                "centinela_aurora_illustrated": "static/images/fixed_pages/_backup/centinela_aurora_back_cover.png",
                "centinela_aurora": "static/images/fixed_pages/_backup/centinela_aurora_back_cover.png"
            }
            back_cover = _fixed_backs.get(_bid, '')
        
        if all_pages:
            pdf_pages = []
            if front_cover:
                pdf_pages.append(front_cover)
            pdf_pages.extend(all_pages)
            # Add back cover if exists
            if back_cover and os.path.exists(back_cover):
                pdf_pages.append(back_cover)
            print(f"[PDF DOWNLOAD] Using {len(pdf_pages)} pages (front + {len(all_pages)} interior + back cover)")
            create_pdf_from_images(pdf_pages, output_path, skip_sanitize=True)
        else:
            from services.pdf_service import create_illustrated_book_pdf
            scene_paths = story_data.get('original_images', story_data.get('scene_paths', []))
            create_illustrated_book_pdf(story_data, scene_paths, output_path, format_type='digital', skip_sanitize=True)
    else:
        from services.pdf_service import create_digital_pdf, create_print_pdf
        
        class OrderData:
            def __init__(self, data):
                self.child_name = data.get('child_name', 'Child')
                self.story_template = data.get('story_template', data.get('story_id', ''))
                self.custom_story_description = None
                self.language = data.get('story_lang', data.get('language', 'es'))
                self.author_name = data.get('author_name', '')
                self.dedication = data.get('dedication', '')
        
        order = OrderData(story_data)
        story_text = story_data.get('story_text', '')
        illustrations = story_data.get('illustrations', [])
        
        if format_type == 'print':
            filename = f"{child_name_safe}_{story_template}_print.pdf"
            output_path = f'generations/pdfs/{preview_id}_print.pdf'
            create_print_pdf(order, story_text, illustrations, output_path)
        else:
            create_digital_pdf(order, story_text, illustrations, output_path)
    
    response = send_file(
        output_path,
        as_attachment=False,
        download_name=filename,
        mimetype='application/pdf'
    )
    response.headers['Content-Disposition'] = f'inline; filename="{filename}"'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response

@app.route('/api/generate-baby-pdf/<preview_id>')
def generate_baby_pdf(preview_id):
    """Generate PDF for baby story or birthday story"""
    format_type = request.args.get('format', 'digital')
    if format_type not in ('digital', 'print', 'lulu', 'cloudprinter'):
        format_type = 'digital'
    force_download = request.args.get('download', '0') == '1'
    skip_sanitize = True
    preview_file = f'story_previews/{preview_id}.json'
    
    if not os.path.exists(preview_file):
        return jsonify({'success': False, 'error': 'Preview not found'}), 404
    
    with open(preview_file, 'r', encoding='utf-8') as f:
        story_data = json.load(f)
    
    from services.pdf_service import create_baby_quick_story_pdf, create_birthday_pdf
    
    os.makedirs('generations/pdfs', exist_ok=True)
    
    child_name_safe = "".join(c for c in story_data.get('child_name', 'story') if c.isalnum() or c in ' _-').strip()
    story_name_safe = "".join(c for c in story_data.get('story_name', 'story') if c.isalnum() or c in ' _-').strip()
    
    images = story_data.get('original_images', story_data.get('original_scene_paths', story_data.get('images', [])))
    if not images:
        image_dir = story_data.get('image_dir', story_data.get('output_dir', ''))
        images = [f"{image_dir}/scene_{i+1}.png" for i in range(len(story_data.get('pages', [])))]
    images = [p.lstrip('/') if p.startswith('/') else p for p in images]
    images = [p.replace('_preview.png', '.png') for p in images]
    
    original_cover = story_data.get('original_cover', '')
    if original_cover:
        if original_cover.startswith('/'):
            original_cover = original_cover[1:]
        if os.path.exists(original_cover):
            story_data['cover_image'] = original_cover
    
    story_id = story_data.get('story_id', '')
    
    filename = f"{child_name_safe}_{story_name_safe}_{format_type}.pdf"
    output_path = f'generations/pdfs/{preview_id}_{format_type}.pdf'
    create_baby_quick_story_pdf(story_data, images, output_path, 'cloudprinter', skip_sanitize=skip_sanitize)
    
    as_attachment = format_type == 'print' or force_download
    response = send_file(
        output_path,
        as_attachment=as_attachment,
        download_name=filename,
        mimetype='application/pdf'
    )
    if as_attachment:
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    else:
        response.headers['Content-Disposition'] = f'inline; filename="{filename}"'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response

@app.route('/api/generate-baby-printable/<preview_id>')
def generate_baby_printable(preview_id):
    """Generate printable PDF for baby story or birthday story (216mm x 216mm with 3mm bleed)"""
    preview_file = f'story_previews/{preview_id}.json'
    
    if not os.path.exists(preview_file):
        return jsonify({'success': False, 'error': 'Preview not found'}), 404
    
    with open(preview_file, 'r', encoding='utf-8') as f:
        story_data = json.load(f)
    
    from services.pdf_service import create_baby_quick_story_pdf
    
    os.makedirs('generations/pdfs', exist_ok=True)
    
    child_name_safe = "".join(c for c in story_data.get('child_name', 'story') if c.isalnum() or c in ' _-').strip()
    story_name_safe = "".join(c for c in story_data.get('story_name', 'story') if c.isalnum() or c in ' _-').strip()
    
    images = story_data.get('images', [])
    if not images:
        image_dir = story_data.get('image_dir', story_data.get('output_dir', ''))
        images = [f"{image_dir}/scene_{i+1}.png" for i in range(len(story_data.get('pages', [])))]
    images = [p.lstrip('/') if p.startswith('/') else p for p in images]
    
    filename = f"{child_name_safe}_{story_name_safe}_imprimible.pdf"
    output_path = f'generations/pdfs/{preview_id}_printable.pdf'
    
    create_baby_quick_story_pdf(story_data, images, output_path, format_type='cloudprinter', skip_sanitize=True)
    
    response = send_file(
        output_path,
        as_attachment=True,
        download_name=filename,
        mimetype='application/pdf'
    )
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response

@app.route('/api/print-instructions/<preview_id>')
def generate_print_instructions(preview_id):
    """Generate printing instructions PDF - auto-detects baby or kids format"""
    preview_file = f'story_previews/{preview_id}.json'
    
    if not os.path.exists(preview_file):
        return jsonify({'success': False, 'error': 'Preview not found'}), 404
    
    with open(preview_file, 'r', encoding='utf-8') as f:
        story_data = json.load(f)
    
    from services.pdf_service import generate_print_instructions_pdf
    
    os.makedirs('generations/pdfs', exist_ok=True)
    
    language = story_data.get('language', 'es')
    
    filename = f"instrucciones_impresion.pdf" if language == 'es' else "printing_instructions.pdf"
    output_path = f'generations/pdfs/{preview_id}_instructions.pdf'
    
    _instr_fmt = story_data.get('print_format', 'A4')
    generate_print_instructions_pdf(output_path, language, print_format=_instr_fmt)
    
    response = send_file(
        output_path,
        as_attachment=True,
        download_name=filename,
        mimetype='application/pdf'
    )
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response

@app.route('/api/download-epub/<preview_id>')
def download_epub(preview_id):
    """Download ePub file for story"""
    from services.epub_service import create_epub_from_story
    
    preview_file = f'story_previews/{preview_id}.json'
    if not os.path.exists(preview_file):
        return jsonify({'success': False, 'error': 'Preview not found'}), 404
    
    with open(preview_file, 'r', encoding='utf-8') as f:
        story_data = json.load(f)
    
    os.makedirs('generations/epubs', exist_ok=True)
    
    child_name = story_data.get('child_name', 'Story')
    language = story_data.get('language', story_data.get('lang', 'es'))
    safe_name = "".join(c for c in child_name if c.isalnum() or c in ' -_').strip()
    
    story_name = story_data.get('story_name', '')
    safe_story = "".join(c for c in story_name if c.isalnum() or c in ' -_').strip().replace(' ', '_')
    
    if language == 'es':
        filename = f"{safe_story}_{safe_name}.epub" if safe_story else f"Cuento_de_{safe_name}.epub"
    else:
        filename = f"{safe_story}_{safe_name}.epub" if safe_story else f"{safe_name}_Story.epub"
    
    output_path = f'generations/epubs/{preview_id}.epub'
    
    try:
        create_epub_from_story(story_data, output_path)
        
        response = send_file(
            output_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/epub+zip'
        )
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return response
    except Exception as e:
        logging.error(f"Error generating ePub: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/visor/')
@app.route('/visor_qs/')
def visor_index():
    return send_from_directory('visor_qs', 'index.html')

@app.route('/visor/<path:filename>')
@app.route('/visor_qs/<path:filename>')
def visor_static(filename):
    if filename.startswith('biblioteca/'):
        gen_path = os.path.join('generations/visor_qs', filename[len('biblioteca/'):])
        if os.path.exists(gen_path):
            return send_from_directory('generations/visor_qs', filename[len('biblioteca/'):])
    return send_from_directory('visor_qs', filename)

@app.route('/visor_pb/')
def visor_pb_index():
    return send_from_directory('visor_pb', 'index.html')

@app.route('/visor_pb/<path:filename>')
def visor_pb_static(filename):
    if filename.startswith('biblioteca/'):
        gen_path = os.path.join('generations/visor_pb', filename[len('biblioteca/'):])
        if os.path.exists(gen_path):
            return send_from_directory('generations/visor_pb', filename[len('biblioteca/'):])
    return send_from_directory('visor_pb', filename)

@app.route('/api/generate-kids-cover-spread/<preview_id>')
def generate_kids_cover_spread(preview_id):
    """Generate cover spread for kids story - uses same logic as baby"""
    return generate_baby_cover_spread_endpoint(preview_id)



@app.route('/api/generate-baby-cover-spread/<preview_id>')
def generate_baby_cover_spread_endpoint(preview_id):
    """Generate cover spread PDF for a specific baby story"""
    from services.pdf_service import generate_baby_cover_spread_pdf, BABY_BACK_COVER
    
    skip_sanitize = True
    preview_file = f'story_previews/{preview_id}.json'
    
    if not os.path.exists(preview_file):
        return jsonify({'success': False, 'error': 'Preview not found'}), 404
    
    with open(preview_file, 'r', encoding='utf-8') as f:
        story_data = json.load(f)
    
    os.makedirs('generations/covers', exist_ok=True)
    
    cover_image = story_data.get('cover_image', '')
    if cover_image.startswith('/'):
        cover_image = cover_image[1:]
    
    if not cover_image or not os.path.exists(cover_image):
        image_dir = story_data.get('image_dir', '')
        cover_image = f"{image_dir}/cover.png"
        if not os.path.exists(cover_image):
            cover_image = f"{image_dir}/scene_1.png"
    
    child_name_safe = "".join(c for c in story_data.get('child_name', 'story') if c.isalnum() or c in ' _-').strip()
    
    output_path = f'generations/covers/{preview_id}_cover_spread.pdf'
    generate_baby_cover_spread_pdf(cover_image, BABY_BACK_COVER, output_path, skip_sanitize=skip_sanitize)
    
    return send_file(
        output_path,
        as_attachment=True,
        download_name=f'{child_name_safe}_cover_spread_print.pdf',
        mimetype='application/pdf'
    )

@app.route('/api/check-openai')
def check_openai():
    has_key = bool(os.environ.get('OPENAI_API_KEY'))
    return jsonify({'configured': has_key})

with app.app_context():
    db.create_all()
    # Ensure coupons/coupon_leads/coupon_usages schema is up to date
    # Each statement uses its own connection to avoid aborted-transaction state
    def _safe_ddl(sql):
        try:
            from sqlalchemy import text as _st
            with db.engine.connect() as _c:
                _c.execute(_st(sql))
                _c.commit()
            return True
        except Exception as _e:
            pass
        return False

    _safe_ddl("ALTER TABLE coupons RENAME COLUMN active TO is_active")
    _safe_ddl("ALTER TABLE coupons ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE")
    _safe_ddl("ALTER TABLE coupon_leads ADD COLUMN IF NOT EXISTS ip_address VARCHAR(50)")
    _safe_ddl("ALTER TABLE coupon_leads ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW()")
    _safe_ddl("ALTER TABLE coupon_usages ADD COLUMN IF NOT EXISTS buyer_email VARCHAR(120)")
    _safe_ddl("ALTER TABLE coupon_usages ADD COLUMN IF NOT EXISTS paypal_order_id VARCHAR(100)")
    _safe_ddl("ALTER TABLE coupon_usages ADD COLUMN IF NOT EXISTS discount_pct INTEGER DEFAULT 0")
    _safe_ddl("ALTER TABLE coupon_usages ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW()")
    _safe_ddl("ALTER TABLE coupon_usages ALTER COLUMN email DROP NOT NULL")
    _safe_ddl("ALTER TABLE community_stories ADD COLUMN IF NOT EXISTS description_es TEXT")
    _safe_ddl("ALTER TABLE community_stories ADD COLUMN IF NOT EXISTS cover_image_en VARCHAR(255)")
    _safe_ddl("ALTER TABLE community_stories ADD COLUMN IF NOT EXISTS description_en TEXT")
    print("[MIGRATION] Coupon table columns ensured")
    # Seed MAGIC15 coupon on startup if it doesn't exist
    try:
        existing = Coupon.query.filter_by(code='MAGIC15').first()
        if not existing:
            magic15 = Coupon(
                code='MAGIC15',
                coupon_type='general',
                discount_pct=15,
                owner_name='Magic Memories Books',
                max_uses=0,
                use_count=0,
                is_active=True
            )
            db.session.add(magic15)
            db.session.commit()
            print("[COUPON] MAGIC15 coupon seeded")
    except Exception as _se:
        print(f"[COUPON] Seed warning: {_se}")
    # Seed APERTURA10 — public inauguration promo (10% off, open to all users)
    try:
        existing_a10 = Coupon.query.filter_by(code='APERTURA10').first()
        if not existing_a10:
            apertura10 = Coupon(
                code='APERTURA10',
                coupon_type='open',
                discount_pct=10,
                owner_name='Magic Memories Books',
                max_uses=0,
                use_count=0,
                is_active=True
            )
            db.session.add(apertura10)
            db.session.commit()
            print("[COUPON] APERTURA10 inauguration coupon seeded")
    except Exception as _se2:
        print(f"[COUPON] APERTURA10 seed warning: {_se2}")
    # Seed community stories (no-op if already present)
    try:
        from services.community_stories_service import (
            seed_venezuela_story, prepare_community_visor_qs)
        seed_venezuela_story()
        prepare_community_visor_qs()
    except Exception as _cs_seed_e:
        print(f"[COMMUNITY] Seed warning: {_cs_seed_e}")
    # Hide old underscore-slug duplicate if both exist
    try:
        _old = CommunityStory.query.filter_by(slug='venezuela_terremoto').first()
        _new = CommunityStory.query.filter_by(slug='venezuela-terremoto').first()
        if _old and _new:
            # Reassign any downloads from old to new, then hide old
            db.session.execute(
                db.text('UPDATE community_downloads SET story_id=:nid WHERE story_id=:oid'),
                {'nid': _new.id, 'oid': _old.id}
            )
            _old.status = 'hidden'
            db.session.commit()
            print(f'[COMMUNITY] Hid old duplicate id={_old.id}, downloads moved to id={_new.id}')
        elif _old and not _new:
            _old.slug = 'venezuela-terremoto'
            db.session.commit()
            print('[COMMUNITY] Migrated slug: venezuela_terremoto → venezuela-terremoto')
    except Exception as _slug_e:
        db.session.rollback()
        print(f'[COMMUNITY] Slug migration warning: {_slug_e}')
    # Add new columns to community_downloads if missing
    _safe_ddl("ALTER TABLE community_downloads ADD COLUMN IF NOT EXISTS adult_name VARCHAR(100)")
    _safe_ddl("ALTER TABLE community_downloads ADD COLUMN IF NOT EXISTS pdf_format VARCHAR(10) DEFAULT 'A4'")
    # Runtime migration: add columns that may be missing on older VPS databases
    try:
        from sqlalchemy import text as _sa_text
        with db.engine.connect() as _conn:
            _missing = {
                'real_story_orders': [
                    ('paypal_order_id', 'VARCHAR(100)'),
                    ('amount_paid', 'INTEGER'),
                    ('paid_at', 'DATETIME'),
                ],
                'preview_leads': [
                    ('paypal_order_id', 'VARCHAR(100)'),
                ],
            }
            for _table, _cols in _missing.items():
                _existing = [row[1] for row in _conn.execute(_sa_text(f"PRAGMA table_info({_table})")).fetchall()]
                for _col, _type in _cols:
                    if _col not in _existing:
                        _conn.execute(_sa_text(f"ALTER TABLE {_table} ADD COLUMN {_col} {_type}"))
                        print(f"[MIGRATION] Added missing column {_table}.{_col}")
            _conn.commit()
    except Exception as _me:
        print(f"[MIGRATION] Warning (non-blocking): {_me}")
    pass  # lulu_storage removed

    # ── Limpieza de tokens de generación atascados (pending/generating → failed) ──
    # Si el servidor se reinicia mientras hay una generación en curso, los JSON quedan
    # en estado "pending"/"generating" para siempre. Los marcamos como "failed" aquí
    # para que el poll del frontend los detecte y limpie el spinner inmediatamente.
    try:
        import glob as _glob, json as _json_startup, datetime as _dt_startup
        _gen_dir = 'data/preview_gen'
        if os.path.isdir(_gen_dir):
            _stale = 0
            for _tok_path in _glob.glob(os.path.join(_gen_dir, '*.json')):
                try:
                    with open(_tok_path) as _tf:
                        _td = _json_startup.load(_tf)
                    if _td.get('status') in ('pending', 'generating'):
                        _td['status'] = 'failed'
                        _td['error'] = 'Server restarted — generation interrupted'
                        _td['updated_at'] = _dt_startup.datetime.utcnow().isoformat()
                        with open(_tok_path, 'w') as _tf:
                            _json_startup.dump(_td, _tf)
                        _stale += 1
                except Exception:
                    pass
            if _stale:
                print(f"[STARTUP] Marked {_stale} stale gen token(s) as failed after restart")
    except Exception as _ste:
        print(f"[STARTUP] Gen token cleanup warning: {_ste}")

    # Verify CP casewrap page count against /products/info in background (non-blocking)
    def _bg_verify_cp_pb():
        try:
            from services.cloudprinter_api_service import verify_pb_page_counts
            chosen = verify_pb_page_counts()
            print(f"[STARTUP] CP PB page count verification complete: chosen={chosen}")
        except Exception as _ve:
            print(f"[STARTUP] CP PB page count verification warning: {_ve}")
    import threading as _th
    _th.Thread(target=_bg_verify_cp_pb, daemon=True).start()


import uuid as uuid_module

@app.route('/api/newsletter-subscribe', methods=['POST'])
def newsletter_subscribe():
    data = request.get_json() or {}
    email = (data.get('email') or '').strip().lower()
    language = data.get('language', 'es')
    consent = data.get('consent', False)

    if not email or '@' not in email or '.' not in email.split('@')[-1]:
        return jsonify({'success': False, 'error': 'invalid_email'}), 400
    if not consent:
        return jsonify({'success': False, 'error': 'consent_required'}), 400

    existing = NewsletterSubscriber.query.filter_by(email=email).first()
    if existing:
        if existing.is_active:
            return jsonify({'success': True, 'message': 'already_subscribed'})
        existing.is_active = True
        existing.consented = True
        existing.language = language
        existing.unsubscribed_at = None
        existing.subscribed_at = datetime.utcnow()
        db.session.commit()
        return jsonify({'success': True, 'message': 'resubscribed'})

    token = uuid_module.uuid4().hex
    subscriber = NewsletterSubscriber(
        email=email,
        language=language,
        consented=True,
        unsubscribe_token=token
    )
    db.session.add(subscriber)
    db.session.commit()

    try:
        from services.email_service import send_newsletter_welcome
        send_newsletter_welcome(email, language, token)
    except Exception as e:
        print(f"[NEWSLETTER] Welcome email failed: {e}")

    return jsonify({'success': True, 'message': 'subscribed'})


@app.route('/unsubscribe/<token>')
def newsletter_unsubscribe(token):
    lang = request.args.get('lang', session.get('lang', 'es'))
    subscriber = NewsletterSubscriber.query.filter_by(unsubscribe_token=token).first()
    if subscriber and subscriber.is_active:
        subscriber.is_active = False
        subscriber.unsubscribed_at = datetime.utcnow()
        db.session.commit()
    title = "Te has desuscrito" if lang == 'es' else "You have been unsubscribed"
    msg = "Ya no recibirás correos de nuestra comunidad. ¡Siempre serás bienvenido/a de vuelta!" if lang == 'es' else "You will no longer receive community emails. You're always welcome back!"
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>{title}</title>
    <style>body{{font-family:'Quicksand',sans-serif;display:flex;justify-content:center;align-items:center;min-height:100vh;background:#F9F9FB;margin:0;}}
    .card{{text-align:center;padding:40px;max-width:400px;}}</style></head>
    <body><div class="card"><h2 style="color:#B8860B;">{title}</h2><p style="color:#666;">{msg}</p>
    <a href="/" style="color:#B8860B;">Magic Memories Books</a></div></body></html>"""


@app.route('/suscribirse')
@app.route('/subscribe')
def subscribe_page():
    lang = request.args.get('lang', session.get('lang', 'es'))
    return render_template('suscribirse.html', lang=lang)


_ADMIN_CONFIG_FILE = 'admin_config.json'

def _load_admin_config():
    """Load full admin config dict."""
    if os.path.exists(_ADMIN_CONFIG_FILE):
        try:
            with open(_ADMIN_CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def _save_admin_config(data):
    """Save full admin config dict."""
    existing = _load_admin_config()
    existing.update(data)
    with open(_ADMIN_CONFIG_FILE, 'w') as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)

def _get_demo_visor_url_b():
    """Kept for backward compat — returns empty string."""
    config = _load_admin_config()
    preview_id = config.get('demo_preview_id_b', '')
    if preview_id:
        return f'/visor_qs/?id={preview_id}'
    return ''

def _load_admin_password():
    """Load admin password from config file, then env, then default."""
    if os.path.exists(_ADMIN_CONFIG_FILE):
        try:
            with open(_ADMIN_CONFIG_FILE, 'r') as f:
                data = json.load(f)
                if data.get('admin_password'):
                    return data['admin_password']
        except Exception:
            pass
    return os.environ.get('ADMIN_PASSWORD', 'magicadmin2026')

def _save_admin_password(new_password):
    """Save admin password to persistent config file."""
    data = {}
    if os.path.exists(_ADMIN_CONFIG_FILE):
        try:
            with open(_ADMIN_CONFIG_FILE, 'r') as f:
                data = json.load(f)
        except Exception:
            pass
    data['admin_password'] = new_password
    with open(_ADMIN_CONFIG_FILE, 'w') as f:
        json.dump(data, f)

_ADMIN_LOCKOUT_FILE = os.path.join(os.path.dirname(_ADMIN_CONFIG_FILE), 'admin_lockout.json')
_MAX_LOGIN_ATTEMPTS = 3

def _load_lockout():
    if os.path.exists(_ADMIN_LOCKOUT_FILE):
        try:
            with open(_ADMIN_LOCKOUT_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def _save_lockout(data):
    try:
        with open(_ADMIN_LOCKOUT_FILE, 'w') as f:
            json.dump(data, f)
    except Exception:
        pass

def _get_client_ip():
    return request.headers.get('X-Forwarded-For', request.remote_addr or '').split(',')[0].strip()

def _is_ip_locked(ip):
    data = _load_lockout()
    info = data.get(ip, {})
    return info.get('locked', False), info.get('attempts', 0)

def _record_failed_attempt(ip):
    data = _load_lockout()
    info = data.get(ip, {'attempts': 0, 'locked': False})
    info['attempts'] = info.get('attempts', 0) + 1
    if info['attempts'] >= _MAX_LOGIN_ATTEMPTS:
        info['locked'] = True
    data[ip] = info
    _save_lockout(data)
    return info['attempts'], info.get('locked', False)

def _reset_ip_lockout(ip):
    data = _load_lockout()
    data.pop(ip, None)
    _save_lockout(data)

ADMIN_PASSWORD = _load_admin_password()

def check_admin_auth():
    """Check if admin is authenticated via session."""
    return session.get('admin_logged_in', False)

_TESTING_MODE_FILE = 'data/testing_mode.json'

def is_testing_mode_active():
    """Return True if admin has enabled 4-hour testing mode (no regen limits)."""
    try:
        if not os.path.exists(_TESTING_MODE_FILE):
            return False
        with open(_TESTING_MODE_FILE, 'r') as f:
            d = json.load(f)
        import time
        return d.get('expires_at', 0) > time.time()
    except Exception:
        return False

@app.route('/admin')
def admin_login_page():
    """Admin login page."""
    if check_admin_auth():
        return redirect(url_for('admin_dashboard'))
    ip = _get_client_ip()
    locked, attempts = _is_ip_locked(ip)
    if locked:
        return render_template('admin_login.html', locked=True)
    return render_template('admin_login.html')

@app.route('/admin/login', methods=['POST'])
def admin_login():
    """Process admin login — max 3 attempts before IP lockout."""
    ip = _get_client_ip()
    locked, attempts = _is_ip_locked(ip)
    if locked:
        return render_template('admin_login.html', locked=True)
    if not _verify_csrf():
        return render_template('admin_login.html', error="Petición inválida. Recarga e inténtalo de nuevo.")
    password = request.form.get('password', '')
    if password == _load_admin_password():
        _reset_ip_lockout(ip)
        session['admin_logged_in'] = True
        return redirect(url_for('admin_dashboard'))
    attempts_done, now_locked = _record_failed_attempt(ip)
    remaining = _MAX_LOGIN_ATTEMPTS - attempts_done
    if now_locked:
        return render_template('admin_login.html', locked=True)
    return render_template('admin_login.html',
                           error=f"Contraseña incorrecta. Intentos restantes: {remaining}")

@app.route('/admin/logout')
def admin_logout():
    """Logout from admin."""
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login_page'))

@app.route('/admin/settings', methods=['GET', 'POST'])
def admin_settings():
    """Admin settings page — change admin password from the web."""
    if not check_admin_auth():
        return redirect(url_for('admin_login_page'))
    success = None
    error = None
    if request.method == 'POST':
        if not _verify_csrf():
            error = 'Petición inválida. Recarga e inténtalo de nuevo.'
            return render_template('admin_settings.html', success=success, error=error)
        current = request.form.get('current_password', '')
        new_pw = request.form.get('new_password', '')
        confirm_pw = request.form.get('confirm_password', '')
        if current != _load_admin_password():
            error = 'La contraseña actual no es correcta.'
        elif len(new_pw) < 8:
            error = 'La nueva contraseña debe tener al menos 8 caracteres.'
        elif new_pw != confirm_pw:
            error = 'Las contraseñas nuevas no coinciden.'
        else:
            _save_admin_password(new_pw)
            success = 'Contraseña actualizada correctamente.'
    return render_template('admin_settings.html', success=success, error=error)

@app.route('/admin/dashboard')
def admin_dashboard():
    """Admin dashboard v3 — executive summary with 2 KPI rows + activity feed."""
    if not check_admin_auth():
        return redirect(url_for('admin_login_page'))

    import glob
    from collections import Counter
    from services.email_service import EMAIL_LOG_FILE

    _INTERNAL = {'magicmemoriesbooks.com', 'pay@', 'admin@', 'info@', 'contacto@'}
    def _is_internal(email):
        return any(x in email for x in _INTERNAL)

    THIS_MONTH = datetime.utcnow().strftime('%Y-%m')

    # ── Story JSONs — buyers + failed orders + preview list ──────────
    story_previews = []
    failed_orders = []
    buyer_emails = set()
    total_revenue = 0.0
    month_revenue = 0.0
    month_sales = 0
    activity_events = []

    preview_files = glob.glob('story_previews/*.json')
    for pf in sorted(preview_files, key=os.path.getmtime, reverse=True):
        try:
            pid = os.path.basename(pf).replace('.json', '')
            if pid.upper().startswith('TEST_'):
                continue
            if '_progress' in pid:
                continue
            with open(pf, 'r') as f:
                data = json.load(f)
            email = (data.get('customer_email') or '').strip().lower()
            is_admin_gift = data.get('admin_gift', False) or data.get('payment_status') == 'admin_gift'
            _raw_amount = float(data.get('amount_paid') or data.get('customer_total_usd') or 0)
            is_paid = (data.get('payment_status') == 'completed' or _raw_amount > 0
                       or data.get('paid', False) or bool(data.get('paypal_order_id')))

            if len(story_previews) < 50:
                story_previews.append({
                    'filename': os.path.basename(pf),
                    'preview_id': pid,
                    'child_name': data.get('child_name', 'Unknown'),
                    'story_id': data.get('story_id', ''),
                    'created': datetime.fromtimestamp(os.path.getmtime(pf)).strftime('%Y-%m-%d %H:%M'),
                    'has_scenes': len(data.get('scenes', [])) > 0,
                    'visor_url': data.get('visor_url', ''),
                    'is_demo': False,
                    'paid': data.get('paid', False),
                })

            # Failed print orders
            _print_failed = (data.get('cp_status') == 'failed' or data.get('lulu_status') == 'failed')
            if _print_failed and data.get('paid') and not data.get('cp_dismissed'):
                failed_orders.append({
                    'preview_id': pid,
                    'child_name': data.get('child_name', 'Unknown'),
                    'story_id': data.get('story_id', ''),
                    'customer_email': email,
                    'cp_error': data.get('cp_error', data.get('lulu_error', 'Error desconocido')),
                    'payment_date': data.get('payment_date', ''),
                    'is_illustrated_book': data.get('is_illustrated_book', False),
                })

            # Buyer KPIs
            if is_paid and not is_admin_gift and email and not _is_internal(email):
                buyer_emails.add(email)
                total_revenue += _raw_amount
                pd_str = (data.get('payment_date') or '')[:7]
                if pd_str == THIS_MONTH:
                    month_revenue += _raw_amount
                    month_sales += 1
                # Activity: purchase
                pd_full = data.get('payment_date')
                if pd_full:
                    try:
                        _ts = datetime.fromisoformat(str(pd_full)[:19])
                        child = data.get('child_name', 'Cliente')
                        activity_events.append({'ts': _ts, 'icon': '💳',
                            'text': f'{child} compró un eBook',
                            'link': f'/admin/cuentos?search={pid}'})
                    except Exception:
                        pass
                # Activity: Cloudprinter
                if data.get('cp_submitted') and data.get('cp_submitted_at'):
                    try:
                        _ts2 = datetime.fromisoformat(str(data['cp_submitted_at'])[:19])
                        activity_events.append({'ts': _ts2, 'icon': '📦',
                            'text': f'Libro de {data.get("child_name","")} enviado a Cloudprinter',
                            'link': ''})
                    except Exception:
                        pass
        except Exception:
            pass

    # ── Story events ───────────────────────────────────────────────────
    cuentos_abiertos = 0
    cuentos_completados = 0
    if os.path.exists(STORY_EVENTS_FILE):
        with open(STORY_EVENTS_FILE, 'r', encoding='utf-8') as _sf:
            for _line in _sf:
                try:
                    _ev = json.loads(_line)
                    _etype = _ev.get('event_type', '')
                    _em = (_ev.get('customer_email') or '')
                    _pid = _ev.get('preview_id', '')
                    _ts = datetime.fromisoformat(_ev['ts'][:19])
                    if _etype == 'FIRST_STORY_OPEN':
                        cuentos_abiertos += 1
                        activity_events.append({'ts': _ts, 'icon': '👀',
                            'text': f'Primera apertura — {_em}',
                            'link': f'/admin/crm/timeline/{_em}'})
                    elif _etype == 'STORY_COMPLETED':
                        cuentos_completados += 1
                        activity_events.append({'ts': _ts, 'icon': '📚',
                            'text': f'Cuento completado — {_em}',
                            'link': f'/admin/crm/timeline/{_em}'})
                except Exception:
                    pass

    # ── Email log ──────────────────────────────────────────────────────
    if os.path.exists(EMAIL_LOG_FILE):
        with open(EMAIL_LOG_FILE, 'r', encoding='utf-8') as _ef:
            for _line in _ef:
                try:
                    _e = json.loads(_line)
                    _to = (_e.get('to_email') or '').strip().lower()
                    if not _to or _is_internal(_to):
                        continue
                    _ts_str = (_e.get('ts') or '')[:19]
                    if not _ts_str:
                        continue
                    _ts = datetime.fromisoformat(_ts_str)
                    _label = _e.get('label') or _e.get('email_type', '')
                    activity_events.append({'ts': _ts, 'icon': '📧',
                        'text': f'Email → {_to}: {_label}',
                        'link': f'/admin/crm/timeline/{_to}'})
                except Exception:
                    pass

    # ── Lead counts from DB ────────────────────────────────────────────
    leads_emails_unicos = 0
    leads_previews = 0
    real_stories_count = 0
    try:
        db.session.rollback()
        from models import RealStoryOrder
        real_stories_count = RealStoryOrder.query.count()
        _all_leads = PreviewLead.query.order_by(PreviewLead.created_at.desc()).limit(500).all()
        _lead_email_set = set()
        for _lead in _all_leads:
            _lem = (_lead.email or '').strip().lower()
            if not _lem or _lem in buyer_emails:
                continue
            _lead_email_set.add(_lem)
            leads_previews += 1
            # Activity: new lead (only recent ones)
            if _lead.created_at:
                activity_events.append({'ts': _lead.created_at, 'icon': '🎯',
                    'text': f'Nuevo lead: {_lem}',
                    'link': '/admin/crm/leads'})
        leads_emails_unicos = len(_lead_email_set)
    except Exception as _db_err:
        production_logger.error(f"[ADMIN] DB query failed: {_db_err}")
        try:
            db.session.rollback()
        except Exception:
            pass

    # ── Conversion ────────────────────────────────────────────────────
    _total_unique = len(buyer_emails) + leads_emails_unicos
    conversion_pct = round(len(buyer_emails) / _total_unique * 100, 1) if _total_unique else 0

    # ── Activity feed: sort, format, limit 10 ─────────────────────────
    activity_events.sort(key=lambda x: x['ts'], reverse=True)
    # Deduplicate consecutive identical texts
    _seen_texts = set()
    activity_deduped = []
    for _ev in activity_events:
        _key = (_ev['icon'], _ev['text'])
        if _key not in _seen_texts:
            _seen_texts.add(_key)
            _ev['ts_str'] = _ev['ts'].strftime('%d %b %H:%M')
            activity_deduped.append(_ev)
    activity_recent = activity_deduped[:10]

    return render_template('admin_dashboard.html',
        story_previews=story_previews,
        failed_orders=failed_orders,
        real_stories_count=real_stories_count,
        # Fila 1 — Negocio
        num_clientes=len(buyer_emails),
        ingresos_mes=round(month_revenue, 2),
        ventas_mes=month_sales,
        conversion_pct=conversion_pct,
        leads_previews=leads_previews,
        leads_emails_unicos=leads_emails_unicos,
        # Fila 2 — Producto
        cuentos_generados=len(story_previews),
        cuentos_abiertos=cuentos_abiertos,
        cuentos_completados=cuentos_completados,
        # Activity
        activity_recent=activity_recent,
        # Legacy compat
        preview_leads_count=leads_emails_unicos,
        current_demo_url='',
        current_demo_url_b='')

@app.route('/admin/reset-rate-limits', methods=['POST'])
def admin_reset_rate_limits():
    """Clear all preview rate limits from DB (useful for testing)."""
    if not check_admin_auth():
        return jsonify({'error': 'Not authorized'}), 403
    try:
        data = request.get_json() or {}
        ip_filter = data.get('ip')  # optional: only clear a specific IP
        cutoff = datetime.utcnow() - timedelta(hours=24)
        q = PreviewLead.query.filter(PreviewLead.created_at >= cutoff)
        if ip_filter:
            q = q.filter(PreviewLead.ip_address == ip_filter)
        deleted = q.delete(synchronize_session=False)
        db.session.commit()
        scope = f'IP {ip_filter}' if ip_filter else 'todos'
        return jsonify({'success': True, 'message': f'Rate limits borrados en DB ({scope}): {deleted} registros'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/admin/send-test-feedback-email', methods=['POST'])
def admin_send_test_feedback_email():
    """Send the 24h feedback email to a specific address for testing."""
    if not check_admin_auth():
        return jsonify({'error': 'Not authorized'}), 403
    data = request.get_json() or {}
    to_email = data.get('email', '')
    child_name = data.get('child_name', '')
    lang = data.get('lang', 'es')
    if not to_email or '@' not in to_email:
        return jsonify({'error': 'Valid email required'}), 400
    from services.email_service import send_feedback_email_24h
    ok = send_feedback_email_24h(to_email, child_name, lang)
    if ok:
        return jsonify({'success': True, 'message': f'Test feedback email sent to {to_email}'})
    return jsonify({'success': False, 'error': 'Failed to send email'}), 500


@app.route('/cp-files/<preview_id>/<filename>')
def serve_cp_file_public(preview_id, filename):
    """
    Serve Cloudprinter PDF files publicly so Cloudprinter can download them.
    This endpoint must be accessible without authentication.
    Files are stored in generations/cloudprinter/<preview_id>/
    """
    import re
    if not re.match(r'^[a-zA-Z0-9_\-]+$', preview_id):
        return "Invalid preview ID", 400
    if filename not in ['book.pdf', 'cover.pdf', 'content.pdf']:
        return "File not allowed", 403
    folder_path = os.path.join('generations', 'cloudprinter', preview_id)
    if not os.path.exists(folder_path):
        return "Order not found", 404
    file_path = os.path.join(folder_path, filename)
    if not os.path.exists(file_path):
        return "File not found", 404
    return send_file(os.path.abspath(file_path), mimetype='application/pdf')


@app.route('/cp-test-files/<session_id>/<filename>')
def serve_cp_test_file(session_id, filename):
    """
    Serve Cloudprinter simulation PDFs from generated/cp_test/<session_id>/.
    Used by cp_simulation_cw.py so Cloudprinter can download test files.
    Secured by session_id pattern validation and strict filename allowlist.
    """
    import re
    if not re.match(r'^[a-zA-Z0-9_\-]+$', session_id):
        return "Invalid session ID", 400
    if filename not in ['cover.pdf', 'content.pdf', 'qs_product.pdf', 'qs_cover.pdf', 'qs_book.pdf']:
        return "File not allowed", 403
    file_path = os.path.join('generated', 'cp_test', session_id, filename)
    if not os.path.exists(file_path):
        return "File not found", 404
    return send_file(os.path.abspath(file_path), mimetype='application/pdf')


@app.route('/admin/preview/<preview_id>')
def admin_view_preview(preview_id):
    """View a story preview from admin."""
    if not check_admin_auth():
        return redirect(url_for('admin_login_page'))
    
    preview_path = f'story_previews/{preview_id}.json'
    if not os.path.exists(preview_path):
        return "Preview not found", 404
    
    with open(preview_path, 'r') as f:
        data = json.load(f)
    
    back_from = request.args.get('from', '')
    return render_template('admin_preview.html', preview=data, preview_id=preview_id, back_from=back_from)


@app.route('/admin/regenerate-scene/<preview_id>/<int:scene_num>', methods=['POST'])
def admin_regenerate_scene(preview_id, scene_num):
    """Admin-only: regenerate a single scene with FLUX 2 Dev + reference image. No regen limit."""
    if not check_admin_auth():
        return jsonify({'success': False, 'error': 'No autorizado'}), 401

    preview_path = f'story_previews/{preview_id}.json'
    if not os.path.exists(preview_path):
        return jsonify({'success': False, 'error': 'Story not found'}), 404

    with open(preview_path, 'r', encoding='utf-8') as f:
        story_data = json.load(f)

    story_id = story_data.get('story_id', '')
    gender = story_data.get('gender', 'neutral')
    traits = story_data.get('traits', {})
    lang = story_data.get('lang', story_data.get('language', 'es'))
    output_dir = story_data.get('output_dir', story_data.get('image_dir', f'generated/{preview_id}'))

    # Illustrated/personalized books (furry_love, etc.) use a different generation path
    from services.personalized_books.generation import is_personalized_book
    if is_personalized_book(story_id):
        # scene_num (1-based) maps to pages[]: pages[0]=title, pages[1]=ded, pages[2]=scene1...
        page_idx = scene_num + 1
        # Delegate to illustrated page regeneration (reuse the logic from admin_regenerate_page)
        try:
            from services.personalized_books.generation import get_personalized_book_id
            from services.illustrated_book_service import generate_scene_complete, load_book_config

            book_id = get_personalized_book_id(story_id)
            book_cfg = load_book_config(book_id)
            scenes = book_cfg.get('scenes', [])
            scene_cfg_idx = page_idx - 2

            # Resolve reference images (shared for both regular scenes and closing)
            ref_path = None
            ref_path_2 = None
            is_furry = book_id in ('furry_love', 'furry_love_adventure', 'furry_love_teen', 'furry_love_adult')
            if is_furry:
                human_preview = story_data.get('human_preview_path', story_data.get('character_preview', ''))
                if human_preview:
                    hr = human_preview.lstrip('/')
                    if os.path.exists(hr):
                        ref_path = hr
                pet_preview = story_data.get('pet_preview_path', '')
                if pet_preview:
                    pr = pet_preview.lstrip('/')
                    if os.path.exists(pr):
                        ref_path_2 = pr
            elif book_id == 'star_keeper':
                character_preview = story_data.get('character_preview', '') or story_data.get('cover_image', '')
                if character_preview:
                    cp_ref = character_preview.lstrip('/')
                    if os.path.exists(cp_ref):
                        ref_path = cp_ref
                luna_static = 'static/assets/luna_reference.png'
                if os.path.exists(luna_static):
                    ref_path_2 = luna_static
            elif book_id == 'centinela_aurora':
                character_preview = story_data.get('character_preview', '') or story_data.get('cover_image', '')
                if character_preview:
                    cp_ref = character_preview.lstrip('/')
                    if os.path.exists(cp_ref):
                        ref_path = cp_ref
                from services.personalized_books.preview import _ensure_astro_reference
                astro_regen_path = _ensure_astro_reference()
                if astro_regen_path and os.path.exists(astro_regen_path):
                    ref_path_2 = astro_regen_path
            elif book_id == 'dragon_garden':
                character_preview = story_data.get('character_preview', '') or story_data.get('cover_image', '')
                if character_preview:
                    cp_ref = character_preview.lstrip('/')
                    if os.path.exists(cp_ref):
                        ref_path = cp_ref
                spark_static = 'static/assets/spark_reference.png'
                if os.path.exists(spark_static):
                    ref_path_2 = spark_static
            elif book_id == 'magic_chef':
                character_preview = story_data.get('character_preview', '') or story_data.get('cover_image', '')
                if character_preview:
                    cp_ref = character_preview.lstrip('/')
                    if os.path.exists(cp_ref):
                        ref_path = cp_ref
                sweetie_static = 'static/assets/sweetie_reference.png'
                if os.path.exists(sweetie_static):
                    ref_path_2 = sweetie_static
            elif book_id == 'magic_inventor':
                character_preview = story_data.get('character_preview', '') or story_data.get('cover_image', '')
                if character_preview:
                    cp_ref = character_preview.lstrip('/')
                    if os.path.exists(cp_ref):
                        ref_path = cp_ref
                from services.personalized_books.preview import _ensure_bolt_reference
                bolt_regen_path = _ensure_bolt_reference()
                if bolt_regen_path and os.path.exists(bolt_regen_path):
                    ref_path_2 = bolt_regen_path
            else:
                reference_image = story_data.get('character_preview', '') or story_data.get('cover_image', '')
                if reference_image:
                    reference_image = reference_image.lstrip('/')
                    if os.path.exists(reference_image):
                        ref_path = reference_image

            # Closing scene: scene_num == len(scenes)+1 (e.g. scene 20 for 19-scene books)
            is_closing = (scene_cfg_idx >= len(scenes))
            if is_closing:
                from services.illustrated_book_service import generate_closing_page
                print(f"[ADMIN-REGEN] Closing scene detected (scene_num={scene_num}), calling generate_closing_page for {book_id}")
                img = generate_closing_page(
                    traits=traits,
                    child_name=story_data.get('child_name', ''),
                    gender=gender,
                    img_size=(1024, 1365),
                    book_id=book_id,
                    reference_image_path=ref_path,
                    reference_image_path_2=ref_path_2
                )
                final_img = img
            else:
                if scene_cfg_idx < 0:
                    return jsonify({'success': False, 'error': f'Escena {scene_num} fuera del rango (libro tiene {len(scenes)} escenas)'}), 400

                scene_config = scenes[scene_cfg_idx]

                print(f"[ADMIN-REGEN] Illustrated book: regenerating scene {scene_num} (page_idx={page_idx}) for {preview_id} ({book_id})")
                img = generate_scene_complete(scene_config, traits, story_data.get('child_name', ''), gender, lang, book_id,
                                              reference_image_path=ref_path, reference_image_path_2=ref_path_2)

            # Compose text — closing scene has no text (text_position="none")
            if not is_closing:
                try:
                    from services.illustrated_book_service import add_text_to_image
                    child_name_for_text = story_data.get('child_name', '')
                    pet_name_for_text = traits.get('pet_name', '')

                    # Prefer the ORIGINAL saved text for this book (may differ from the
                    # current shared prompt template if the template was edited later,
                    # or if pronouns/wording were customized at generation time).
                    # Only fall back to the generic template when no saved text exists.
                    # NOTE: story_data['pages'] for illustrated/furry_love books is a FLAT
                    # array of just the 19 scene texts, indexed directly by scene_cfg_idx
                    # (0-based scene number) — it does NOT include title/dedication/credits
                    # entries, despite what page_idx (used for composed_dir filenames) implies.
                    # Indexing it with page_idx instead of scene_cfg_idx silently pairs each
                    # illustration with a DIFFERENT scene's caption. Always use scene_cfg_idx here.
                    raw_text = None
                    _pages_for_text = story_data.get('pages', [])
                    if 0 <= scene_cfg_idx < len(_pages_for_text):
                        raw_text = _pages_for_text[scene_cfg_idx].get('text')
                    if not raw_text:
                        _story_texts_for_text = story_data.get('story_texts') or []
                        if 0 <= scene_cfg_idx < len(_story_texts_for_text):
                            raw_text = _story_texts_for_text[scene_cfg_idx].get('text')
                    if raw_text:
                        print(f"[ADMIN-REGEN] Using ORIGINAL saved text for scene {scene_num}")
                    else:
                        raw_text = scene_config.get(f'text_{lang}', scene_config.get('text_es', ''))
                        raw_text = raw_text.replace('{name}', child_name_for_text)
                        if pet_name_for_text:
                            raw_text = raw_text.replace('{pet_name}', pet_name_for_text)
                        print(f"[ADMIN-REGEN] No saved text found, falling back to template for scene {scene_num}")

                    position = scene_config.get('text_position', 'split')
                    final_img = add_text_to_image(img, raw_text, position, '#FFFFFF', '#000000', 38, 0.103)
                    print(f"[ADMIN-REGEN] Text composed (position={position}): {raw_text[:40]!r}")
                except Exception as _ce:
                    print(f"[ADMIN-REGEN] Text composition skipped: {_ce}")
                    final_img = img

            # Save path: use canonical composed_dir/page_NN.png — same location as background gen
            composed_dir = f'generated/composed_{preview_id}'
            os.makedirs(composed_dir, exist_ok=True)
            save_path = os.path.join(composed_dir, f'page_{page_idx+1:02d}.png')
            # Also save preview (watermarked) to keep both files in sync
            final_img.save(save_path, 'PNG')
            try:
                from services.illustrated_book_service import add_watermark
                wm = add_watermark(final_img)
                wm.save(save_path.replace('.png', '_preview.png'), 'PNG')
            except Exception:
                pass

            url_path = f'/{save_path}'

            # Update pages_data scene_path → clean path (kept for the admin text-editor UI)
            pages_data = story_data.get('pages', [])
            if 0 <= page_idx < len(pages_data):
                if pages_data[page_idx].get('scene_path') is not None:
                    pages_data[page_idx]['scene_path'] = url_path
                elif pages_data[page_idx].get('fixed_scene') is not None:
                    pages_data[page_idx]['fixed_scene'] = url_path
                else:
                    pages_data[page_idx]['scene_path'] = url_path
                story_data['pages'] = pages_data
                with open(preview_path, 'w', encoding='utf-8') as f:
                    json.dump(story_data, f, ensure_ascii=False, indent=2)

            # Single reconstruction pipeline: rebuilds path arrays, visor,
            # printable PDF and Cloudprinter PDFs from the page files on disk.
            # Runs in a background thread so the HTTP response returns immediately
            # with the new image URL — rebuild (incl. PDF generation) can take
            # several minutes and would otherwise time out the connection.
            # mark_composed=False: admin scene regeneration only, never a
            # composition-completion event — must not touch composition/
            # approval state flags.
            import threading
            from services.personalized_books.rebuild import rebuild_book
            def _rebuild_bg():
                try:
                    rebuild_book(preview_id, mark_composed=False)
                    production_logger.info(f"[ADMIN-REGEN] Background rebuild done for {preview_id} scene {scene_num}")
                except Exception as _rb_e:
                    print(f"[ADMIN-REGEN] Background rebuild error for {preview_id}: {_rb_e}")
            threading.Thread(target=_rebuild_bg, daemon=True).start()

            production_logger.info(f"[ADMIN-REGEN] Illustrated scene {scene_num} OK for {preview_id}: {save_path}")
            return jsonify({'success': True, 'image_url': url_path})

        except Exception as e:
            print(f"[ADMIN-REGEN] Illustrated regen error: {e}")
            import traceback; traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)[:300]}), 500

    from services.fixed_stories import get_scene_prompts, FIXED_STORIES
    from services.replicate_service import generate_scene_with_flux2dev

    try:
        scene_prompts = get_scene_prompts(story_id, story_data.get('child_name', ''), gender, traits, use_reference_image=True)
        scene_index = scene_num - 1
        if scene_index < 0 or scene_index >= len(scene_prompts):
            return jsonify({'success': False, 'error': f'Scene {scene_num} not found (story has {len(scene_prompts)} scenes)'}), 400

        prompt = scene_prompts[scene_index]

        ref_image = None
        for candidate in ['cover_clean.png', 'base_character.png', 'cover.png']:
            candidate_path = os.path.join(output_dir, candidate)
            if os.path.exists(candidate_path):
                ref_image = candidate_path
                break

        if not ref_image:
            return jsonify({'success': False, 'error': 'No reference image found (cover_clean.png missing)'}), 400

        story_config = FIXED_STORIES.get(story_id, {})
        age_range = story_config.get('age_range', '3-8')
        is_baby = age_range in ['0-1', '0-2']
        aspect = '1:1' if is_baby else '3:4'
        hair_length = traits.get('hair_length', 'medium')
        child_age = int(traits.get('child_age', '5'))

        print(f"[ADMIN-REGEN] Regenerating scene {scene_num} for {preview_id} (story: {story_id})")

        new_scene_path = generate_scene_with_flux2dev(
            prompt, ref_image, scene_num, aspect, output_dir,
            gender=gender, age_range=age_range,
            hair_length=hair_length, child_age=child_age
        )

        if new_scene_path and os.path.exists(new_scene_path):
            story_config_full = FIXED_STORIES.get(story_id, {})
            text_layout = story_config_full.get('text_layout', 'single')
            pages_data = story_data.get('pages', [])

            if pages_data and scene_index < len(pages_data):
                try:
                    from services.quick_stories.image_composer import compose_baby_text_on_image, compose_kids_text_on_image
                    from PIL import Image as PILImg
                    page = pages_data[scene_index]
                    img_obj = PILImg.open(new_scene_path)
                    if text_layout == 'split':
                        ta = page.get(f'text_above_{lang}', page.get('text_above', page.get('text', '')))
                        tb = page.get(f'text_below_{lang}', page.get('text_below', ''))
                        composed = compose_kids_text_on_image(img_obj, ta, tb, lang)
                    else:
                        txt = page.get(f'text_{lang}', page.get('text', ''))
                        composed = compose_baby_text_on_image(img_obj, txt, lang)
                    composed.save(new_scene_path, 'PNG')
                    print(f"[ADMIN-REGEN] Text recomposed on scene {scene_num}")
                except Exception as comp_err:
                    print(f"[ADMIN-REGEN] Text composition skipped: {comp_err}")

            image_url = f'/{new_scene_path}' if not new_scene_path.startswith('/') else new_scene_path
            print(f"[ADMIN-REGEN] Scene {scene_num} regenerated OK: {new_scene_path}")
            return jsonify({'success': True, 'image_url': image_url})
        else:
            return jsonify({'success': False, 'error': 'Generation returned no file'}), 500

    except Exception as e:
        print(f"[ADMIN-REGEN] Error: {e}")
        return jsonify({'success': False, 'error': str(e)[:200]}), 500


@app.route('/admin/regenerate-page/<preview_id>/<int:page_idx>', methods=['POST'])
def admin_regenerate_page(preview_id, page_idx):
    """Admin: regenerate any page in illustrated/furry_love books. No regen limit."""
    if not check_admin_auth():
        return jsonify({'success': False, 'error': 'No autorizado'}), 401

    preview_path = f'story_previews/{preview_id}.json'
    if not os.path.exists(preview_path):
        return jsonify({'success': False, 'error': 'Preview not found'}), 404

    with open(preview_path, 'r', encoding='utf-8') as f:
        story_data = json.load(f)

    pages_data = story_data.get('pages', [])
    if page_idx < 0 or page_idx >= len(pages_data):
        return jsonify({'success': False, 'error': f'Índice {page_idx} no válido (total: {len(pages_data)} páginas)'}), 400

    page = pages_data[page_idx]
    if not (page.get('scene_path') or page.get('fixed_scene')):
        return jsonify({'success': False, 'error': 'Esta página no tiene escena regenerable (es portada, dedicatoria o créditos)'}), 400

    story_id = story_data.get('story_id', '')
    gender = story_data.get('gender', 'neutral')
    traits = story_data.get('traits', {})
    lang = story_data.get('lang', story_data.get('language', 'es'))
    child_name = story_data.get('child_name', '')
    output_dir = story_data.get('output_dir', story_data.get('image_dir', f'generated/{preview_id}'))

    try:
        from services.personalized_books.generation import get_personalized_book_id
        from services.illustrated_book_service import generate_scene_complete, load_book_config

        book_id = get_personalized_book_id(story_id)
        book_cfg = load_book_config(book_id)
        scenes = book_cfg.get('scenes', [])

        # pages[0]=title, pages[1]=dedication, pages[2..N]=scenes, last pages=credits
        scene_cfg_idx = page_idx - 2
        if scene_cfg_idx < 0 or scene_cfg_idx >= len(scenes):
            return jsonify({'success': False, 'error': f'Página {page_idx+1} fuera del rango de escenas (escenas disponibles: {len(scenes)})'}), 400

        scene_config = scenes[scene_cfg_idx]

        # Reference images
        ref_path = None
        ref_path_2 = None
        is_furry = book_id in ('furry_love', 'furry_love_adventure', 'furry_love_teen', 'furry_love_adult')
        if is_furry:
            human_preview = story_data.get('human_preview_path', story_data.get('character_preview', ''))
            if human_preview:
                hr = human_preview.lstrip('/')
                if os.path.exists(hr):
                    ref_path = hr
            pet_preview = story_data.get('pet_preview_path', '')
            if pet_preview:
                pr = pet_preview.lstrip('/')
                if os.path.exists(pr):
                    ref_path_2 = pr
        elif book_id == 'star_keeper':
            character_preview = story_data.get('character_preview', '') or story_data.get('cover_image', '')
            if character_preview:
                cp_ref = character_preview.lstrip('/')
                if os.path.exists(cp_ref):
                    ref_path = cp_ref
            luna_static = 'static/assets/luna_reference.png'
            if os.path.exists(luna_static):
                ref_path_2 = luna_static
        elif book_id == 'centinela_aurora':
            character_preview = story_data.get('character_preview', '') or story_data.get('cover_image', '')
            if character_preview:
                cp_ref = character_preview.lstrip('/')
                if os.path.exists(cp_ref):
                    ref_path = cp_ref
            from services.personalized_books.preview import _ensure_astro_reference
            astro_regen_path = _ensure_astro_reference()
            if astro_regen_path and os.path.exists(astro_regen_path):
                ref_path_2 = astro_regen_path
        elif book_id == 'dragon_garden':
            character_preview = story_data.get('character_preview', '') or story_data.get('cover_image', '')
            if character_preview:
                cp_ref = character_preview.lstrip('/')
                if os.path.exists(cp_ref):
                    ref_path = cp_ref
            spark_static = 'static/assets/spark_reference.png'
            if os.path.exists(spark_static):
                ref_path_2 = spark_static
        elif book_id == 'magic_chef':
            character_preview = story_data.get('character_preview', '') or story_data.get('cover_image', '')
            if character_preview:
                cp_ref = character_preview.lstrip('/')
                if os.path.exists(cp_ref):
                    ref_path = cp_ref
            sweetie_static = 'static/assets/sweetie_reference.png'
            if os.path.exists(sweetie_static):
                ref_path_2 = sweetie_static
        elif book_id == 'magic_inventor':
            character_preview = story_data.get('character_preview', '') or story_data.get('cover_image', '')
            if character_preview:
                cp_ref = character_preview.lstrip('/')
                if os.path.exists(cp_ref):
                    ref_path = cp_ref
            from services.personalized_books.preview import _ensure_bolt_reference
            bolt_regen_path = _ensure_bolt_reference()
            if bolt_regen_path and os.path.exists(bolt_regen_path):
                ref_path_2 = bolt_regen_path
        else:
            reference_image = story_data.get('character_preview', '') or story_data.get('cover_image', '')
            if reference_image:
                reference_image = reference_image.lstrip('/')
                if os.path.exists(reference_image):
                    ref_path = reference_image

        print(f"[ADMIN-REGEN-PAGE] Regenerating page {page_idx} (scene {scene_cfg_idx}) for {preview_id} ({book_id}), ref={bool(ref_path)}, ref2={bool(ref_path_2)}")

        img = generate_scene_complete(
            scene_config, traits, child_name, gender, lang, book_id,
            reference_image_path=ref_path,
            reference_image_path_2=ref_path_2
        )

        # Compose text using add_text_to_image — same as generate_full_book, NOT QS composer
        try:
            from services.illustrated_book_service import add_text_to_image

            # Prefer the ORIGINAL saved text for this book (may differ from the
            # current shared prompt template if the template was edited later,
            # or if pronouns/wording were customized at generation time).
            # Only fall back to the generic template when no saved text exists.
            # NOTE: story_data['pages'] for illustrated/furry_love books is a FLAT
            # array of just the 19 scene texts, indexed directly by scene_cfg_idx
            # (0-based scene number) — it does NOT include title/dedication/credits
            # entries, despite what page_idx (used for composed_dir filenames) implies.
            # Indexing it with page_idx instead of scene_cfg_idx silently pairs each
            # illustration with a DIFFERENT scene's caption. Always use scene_cfg_idx here.
            raw_text = None
            if 0 <= scene_cfg_idx < len(pages_data):
                raw_text = pages_data[scene_cfg_idx].get('text')
            if not raw_text:
                _story_texts_for_text = story_data.get('story_texts') or []
                if 0 <= scene_cfg_idx < len(_story_texts_for_text):
                    raw_text = _story_texts_for_text[scene_cfg_idx].get('text')
            if raw_text:
                print(f"[ADMIN-REGEN-PAGE] Using ORIGINAL saved text for page {page_idx}")
            else:
                raw_text = scene_config.get(f'text_{lang}', scene_config.get('text_es', ''))
                raw_text = raw_text.replace('{name}', child_name)
                pet_name_val = traits.get('pet_name', '')
                if pet_name_val:
                    raw_text = raw_text.replace('{pet_name}', pet_name_val)
                print(f"[ADMIN-REGEN-PAGE] No saved text found, falling back to template for page {page_idx}")

            position = scene_config.get('text_position', 'split')
            final_img = add_text_to_image(img, raw_text, position, '#FFFFFF', '#000000', 38, 0.103)
            print(f"[ADMIN-REGEN-PAGE] Text composed (position={position}): {raw_text[:40]!r}")
        except Exception as comp_err:
            print(f"[ADMIN-REGEN-PAGE] Text composition skipped: {comp_err}")
            final_img = img

        # Save to canonical composed_dir path — same location as background generation
        composed_dir = f'generated/composed_{preview_id}'
        os.makedirs(composed_dir, exist_ok=True)
        save_path = os.path.join(composed_dir, f'page_{page_idx+1:02d}.png')
        final_img.save(save_path, 'PNG')
        try:
            from services.illustrated_book_service import add_watermark
            wm = add_watermark(final_img)
            wm.save(save_path.replace('.png', '_preview.png'), 'PNG')
        except Exception:
            pass

        url_path = f'/{save_path}'

        # Update pages_data (kept for the admin text-editor UI)
        if pages_data[page_idx].get('scene_path') is not None:
            pages_data[page_idx]['scene_path'] = url_path
        elif pages_data[page_idx].get('fixed_scene') is not None:
            pages_data[page_idx]['fixed_scene'] = url_path
        else:
            pages_data[page_idx]['scene_path'] = url_path

        story_data['pages'] = pages_data
        with open(preview_path, 'w', encoding='utf-8') as f:
            json.dump(story_data, f, ensure_ascii=False, indent=2)

        # Single reconstruction pipeline: rebuilds path arrays, visor,
        # printable PDF and Cloudprinter PDFs from the page files on disk.
        # mark_composed=False: admin page regeneration only, never a
        # composition-completion event — must not touch composition/
        # approval state flags.
        from services.personalized_books.rebuild import rebuild_book
        rebuild_book(preview_id, mark_composed=False)

        production_logger.info(f"[ADMIN-REGEN-PAGE] Page {page_idx} OK for {preview_id}: {save_path}")
        return jsonify({'success': True, 'image_url': url_path})

    except Exception as e:
        print(f"[ADMIN-REGEN-PAGE] Error: {e}")
        import traceback; traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)[:300]}), 500


@app.route('/admin/rebuild-visor/<preview_id>', methods=['POST'])
def admin_rebuild_visor(preview_id):
    """Rebuild visor/eBook from scratch using page_NN.png files on disk.
    Fixes corrupted original_scene_paths and re-uploads fresh visor pages."""
    if not check_admin_auth():
        return jsonify({'success': False, 'error': 'No autorizado'}), 401

    preview_path = f'story_previews/{preview_id}.json'
    if not os.path.exists(preview_path):
        return jsonify({'success': False, 'error': 'Preview not found'}), 404

    with open(preview_path, 'r', encoding='utf-8') as f:
        story_data = json.load(f)

    try:
        # Use original_scene_paths from JSON — these point to the ACTUAL current images
        # (may be in personalized_XXXX/ after user regens, or composed_XXXX/ after admin regen)
        # DO NOT glob the composed_dir: that ignores regenerated pages stored elsewhere.
        orig_paths = story_data.get('original_scene_paths', story_data.get('original_images', []))
        if not orig_paths:
            return jsonify({'success': False, 'error': 'No hay original_scene_paths en el JSON'}), 404

        # Verify all source files exist
        missing = [p for p in orig_paths if p and not os.path.exists(p.lstrip('/'))]
        if missing:
            print(f"[REBUILD-VISOR] WARNING: {len(missing)} rutas no encontradas: {missing[:3]}")

        print(f"[REBUILD-VISOR] Usando original_scene_paths del JSON: {len(orig_paths)} páginas")

        # Convert each source image → visor JPG (page_2.jpg … page_N+1.jpg)
        from PIL import Image as _PilImage
        import stat as _stat
        visor_dir = f'generations/visor_pb/{preview_id}'
        os.makedirs(visor_dir, exist_ok=True)
        converted = 0
        for i, src_path in enumerate(orig_paths):
            src = src_path.lstrip('/') if src_path else None
            if not src or not os.path.exists(src):
                print(f"[REBUILD-VISOR] Saltar página {i}: ruta no encontrada ({src_path})")
                continue
            dst = os.path.join(visor_dir, f'page_{i+2}.jpg')   # visor starts at page_2
            # Remove existing file to avoid permission errors
            if os.path.exists(dst):
                try:
                    os.remove(dst)
                except OSError:
                    os.chmod(dst, _stat.S_IRUSR | _stat.S_IWUSR | _stat.S_IRGRP | _stat.S_IWGRP)
                    os.remove(dst)
            img = _PilImage.open(src).convert('RGB')
            _VISOR_MAX_DIM = 1200  # cap web viewer images; print PDF still uses original 300 DPI source
            if img.width > _VISOR_MAX_DIM or img.height > _VISOR_MAX_DIM:
                img.thumbnail((_VISOR_MAX_DIM, _VISOR_MAX_DIM), _PilImage.LANCZOS)
            img.save(dst, 'JPEG', quality=82, optimize=True, progressive=True)
            img.close()
            converted += 1
            print(f"[REBUILD-VISOR] [{i}] {os.path.basename(src)} → page_{i+2}.jpg")

        story_data['visor_uploaded'] = True
        # Invalidate PDF cache so next download uses fresh visor
        _cp_pdf = f'generations/cloudprinter/{preview_id}/content.pdf'
        if os.path.exists(_cp_pdf):
            try:
                os.remove(_cp_pdf)
                print(f"[REBUILD-VISOR] PDF cache invalidado")
            except Exception:
                pass
        print(f"[REBUILD-VISOR] Done for {preview_id}: {converted}/{len(orig_paths)} páginas convertidas")

        with open(preview_path, 'w', encoding='utf-8') as f:
            json.dump(story_data, f, ensure_ascii=False, indent=2)

        production_logger.info(f"[REBUILD-VISOR] Done for {preview_id}: {converted}/{len(orig_paths)} pages re-uploaded")
        return jsonify({'success': True, 'pages': converted,
                        'message': f'eBook reconstruido con {converted}/{len(orig_paths)} páginas'})
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)[:300]}), 500


@app.route('/admin/reset-pdf/<preview_id>', methods=['POST'])
def admin_reset_pdf(preview_id):
    """Reset PDF, eBook and compose flags so everything regenerates on next confirmation."""
    if not check_admin_auth():
        return jsonify({'success': False, 'error': 'No autorizado'}), 401

    preview_file = f'story_previews/{preview_id}.json'
    if not os.path.exists(preview_file):
        return jsonify({'success': False, 'error': 'Preview not found'}), 404

    with open(preview_file, 'r', encoding='utf-8') as f:
        story_data = json.load(f)

    story_data['book_composing'] = False
    story_data['generation_error'] = ''
    story_data['pages_composed'] = False
    story_data['visor_uploaded'] = False
    story_data.pop('digital_pdf_path', None)
    story_data.pop('print_pdf_path', None)

    with open(preview_file, 'w', encoding='utf-8') as f:
        json.dump(story_data, f, ensure_ascii=False, indent=2)

    production_logger.info(f"[ADMIN] PDF/eBook reset for {preview_id}")
    return jsonify({'success': True, 'message': 'PDF y eBook reseteados correctamente.'})


@app.route('/admin/preview/<preview_id>/pdf')
def admin_download_pdf(preview_id):
    """Download PDF for a story from admin."""
    if not check_admin_auth():
        return redirect(url_for('admin_login_page'))
    
    preview_path = f'story_previews/{preview_id}.json'
    if not os.path.exists(preview_path):
        return "Preview not found", 404
    
    with open(preview_path, 'r') as f:
        data = json.load(f)
    
    pdf_path = None
    candidates = []
    
    lulu_folder = data.get('lulu_order_folder', '')
    if lulu_folder:
        candidates.append(os.path.join(lulu_folder, 'interior.pdf'))
    
    if data.get('digital_pdf_path'):
        candidates.append(data['digital_pdf_path'])
    if data.get('pdf_printable_path'):
        candidates.append(data['pdf_printable_path'])
    if data.get('pdf_path'):
        candidates.append(data['pdf_path'])
    if data.get('print_pdf_path'):
        candidates.append(data['print_pdf_path'])
    
    for candidate in candidates:
        if candidate and os.path.exists(candidate):
            pdf_path = candidate
            break
    
    if not pdf_path:
        return "PDF not found. Available keys: " + str([k for k in data.keys() if 'pdf' in k.lower() or 'lulu' in k.lower()]), 404
    
    child_name = data.get('child_name', 'story').replace(' ', '_')
    return send_file(pdf_path, as_attachment=True, download_name=f'{child_name}_{preview_id[:8]}.pdf')


@app.route('/download-book/<preview_id>')
def download_book_pdf(preview_id):
    """Public user-facing route: serves the imprimible PDF (28p, bleed+crop marks).
    Used by the visor download button and any direct link.
    Generates the PDF on demand if not yet cached."""
    import re as _re
    if not _re.match(r'^[a-zA-Z0-9_\-]+$', preview_id):
        abort(400)

    preview_path = f'story_previews/{preview_id}.json'
    story_data = {}
    child_name = 'libro'
    lang = 'es'

    if os.path.exists(preview_path):
        with open(preview_path, 'r') as f:
            try:
                story_data = json.load(f)
                child_name = story_data.get('child_name', 'libro').replace(' ', '_').replace("'", '')
                lang = story_data.get('lang', 'es')
            except Exception:
                pass

    # 1) Already generated — serve immediately
    pdf_printable = story_data.get('pdf_printable_path', '')
    if pdf_printable and os.path.exists(pdf_printable):
        fmt = 'LETTER' if 'LETTER' in pdf_printable else 'A4'
        return send_file(os.path.abspath(pdf_printable), as_attachment=True,
                         download_name=f'{child_name}_imprimible_{fmt}.pdf')

    # 2) Not yet cached — generate on demand from visor pages
    visor_dir = os.path.join('generations', 'visor_pb', preview_id)
    if os.path.exists(visor_dir) and os.path.exists(os.path.join(visor_dir, 'page_1.jpg')):
        try:
            from services.personalized_books.printable_pdf import generate_personalized_printable_pdf
            from services.personalized_books.generation import get_print_title
            book_id = story_data.get('story_id', '')
            gender = story_data.get('gender', 'nino')
            print_format = story_data.get('print_format', 'A4')
            traits = story_data.get('traits') or {}
            pet_name = traits.get('pet_name', '')
            book_title = get_print_title(book_id, child_name.replace('_', ' '), lang, pet_name=pet_name)
            pdf_path = generate_personalized_printable_pdf(
                book_session_id=preview_id,
                child_name=child_name.replace('_', ' '),
                gender=gender,
                language=lang,
                book_id=book_id,
                book_title=book_title,
                print_format=print_format,
                front_cover_path=story_data.get('front_cover_path') or None,
                back_cover_path=story_data.get('back_cover_path') or None,
            )
            if pdf_path and os.path.exists(pdf_path):
                # Cache for next time
                story_data['pdf_printable_path'] = pdf_path
                if os.path.exists(preview_path):
                    with open(preview_path, 'w') as fw:
                        json.dump(story_data, fw, ensure_ascii=False, indent=2)
                fmt = 'LETTER' if print_format == 'LETTER' else 'A4'
                return send_file(os.path.abspath(pdf_path), as_attachment=True,
                                 download_name=f'{child_name}_imprimible_{fmt}.pdf')
        except Exception as e:
            print(f'[DOWNLOAD-BOOK] Error generating imprimible on demand: {e}')

    abort(404)


@app.route('/admin/gelato-order/<preview_id>/download-pdf')
@app.route('/admin/order/<preview_id>/download-pdf')
def admin_download_gelato_pdf(preview_id):
    """Download the print PDF for a personalized book order (Cloudprinter)."""
    if not check_admin_auth():
        return redirect(url_for('admin_login_page'))
    import re
    if not re.match(r'^[a-zA-Z0-9_\-]+$', preview_id):
        abort(400)

    preview_path = f'story_previews/{preview_id}.json'
    child_name = 'libro'
    lang = 'es'
    story_data = {}
    if os.path.exists(preview_path):
        with open(preview_path, 'r') as f:
            try:
                story_data = json.load(f)
                child_name = story_data.get('child_name', 'libro').replace(' ', '_')
                lang = story_data.get('lang', 'es')
            except Exception:
                pass

    # 0) Printable PDF (28-page, 3mm bleed + crop marks)
    pdf_printable = story_data.get('pdf_printable_path', '')
    if pdf_printable and os.path.exists(pdf_printable):
        fmt = 'LETTER' if 'LETTER' in pdf_printable else 'A4'
        return send_file(os.path.abspath(pdf_printable), as_attachment=True,
                         download_name=f'{child_name}_{preview_id[:8]}_imprimible_{fmt}.pdf')

    # 1) Personalized illustrated book with visor pages ready — always (re)generate the
    # complete 28-page PDF (portada + contenido + contraportada), regardless of whether a
    # stale Cloudprinter content.pdf (interior-only, no covers) happens to exist on disk.
    _visor_dir_chk = os.path.join('generations', 'visor_pb', preview_id)
    _has_visor_pages = os.path.exists(os.path.join(_visor_dir_chk, 'page_1.jpg'))
    if _has_visor_pages:
        try:
            from services.personalized_books.printable_pdf import generate_personalized_printable_pdf
            from services.personalized_books.generation import get_personalized_book_id
            _gender_dl = story_data.get('gender', 'nino')
            _book_id_dl = get_personalized_book_id(story_data.get('story_id', ''))
            _fmt_dl = story_data.get('print_format', 'A4')
            _fmt_sfx_dl = 'LETTER' if _fmt_dl == 'LETTER' else 'A4'
            _out_dl = os.path.join('generated', 'cloudprinter', preview_id)
            os.makedirs(_out_dl, exist_ok=True)
            _safe_dl = child_name.replace(' ', '_').replace("'", '')
            _full_pdf = os.path.join(_out_dl, f'{_safe_dl}_completo_{_fmt_sfx_dl}.pdf')
            generate_personalized_printable_pdf(
                book_session_id=preview_id,
                child_name=child_name,
                gender=_gender_dl,
                language=lang,
                book_id=_book_id_dl,
                output_path=_full_pdf,
                force_regenerate=True,
                print_format=_fmt_dl,
                front_cover_path=story_data.get('front_cover_path') or None,
                back_cover_path=story_data.get('back_cover_path') or None,
            )
            if os.path.exists(_full_pdf):
                print(f"[ADMIN PDF] Serving 28-page complete PDF for {preview_id}")
                return send_file(os.path.abspath(_full_pdf), as_attachment=True,
                                 download_name=f'{child_name}_{preview_id[:8]}_completo_{_fmt_sfx_dl}.pdf')
        except Exception as _full_pdf_err:
            print(f"[ADMIN PDF] Complete PDF generation failed ({_full_pdf_err}), falling back to content.pdf")

    # 1b) Fallback: legacy/cached Cloudprinter content PDF (26-page interior, no covers)
    cp_content = os.path.join('generations', 'cloudprinter', preview_id, 'content.pdf')
    if os.path.exists(cp_content):
        return send_file(os.path.abspath(cp_content), as_attachment=True,
                         download_name=f'{child_name}_{preview_id[:8]}_libro.pdf')

    # 1.5) Quick Story CP book.pdf already generated — serve directly without regenerating
    qs_book = os.path.join('generations', 'cloudprinter', preview_id, 'book.pdf')
    if os.path.exists(qs_book):
        return send_file(os.path.abspath(qs_book), as_attachment=True,
                         download_name=f'{child_name}_{preview_id[:8]}_cuento.pdf')

    # 3) CP book with scenes ready but PDF not yet generated — generate on demand
    visor_dir = os.path.join('generations', 'visor_pb', preview_id)
    composed_dir = os.path.join('generated', f'composed_{preview_id}')
    has_visor = os.path.exists(visor_dir) and os.path.exists(os.path.join(visor_dir, 'page_1.jpg'))
    has_composed = os.path.exists(composed_dir)
    if has_visor or has_composed:
        try:
            from services.personalized_books.cp_pdf_service import generate_cw_content_pdf, generate_cw_cover_pdf
            from services.cloudprinter_api_service import get_pb_chosen_page_count
            out_dir = os.path.join('generations', 'cloudprinter', preview_id)
            os.makedirs(out_dir, exist_ok=True)
            page_count = get_pb_chosen_page_count()
            content_path = os.path.join(out_dir, 'content.pdf')
            generate_cw_content_pdf(
                session_id=preview_id,
                child_name=child_name,
                language=lang,
                output_path=content_path,
                page_count=page_count,
            )
            if os.path.exists(content_path):
                # Also generate cover PDF in background
                try:
                    visor_meta = os.path.join(visor_dir, 'metadata.json')
                    book_title = child_name
                    if os.path.exists(visor_meta):
                        with open(visor_meta) as _mf:
                            _md = json.load(_mf)
                            book_title = _md.get('title', child_name)
                    cover_path = os.path.join(out_dir, 'cover.pdf')
                    if not os.path.exists(cover_path):
                        import threading as _t
                        _t.Thread(target=generate_cw_cover_pdf,
                                  kwargs={'session_id': preview_id, 'book_title': book_title,
                                          'output_path': cover_path, 'page_count': page_count,
                                          'story_id': story_data.get('story_id', '')},
                                  daemon=True).start()
                except Exception:
                    pass
                return send_file(os.path.abspath(content_path), as_attachment=True,
                                 download_name=f'{child_name}_{preview_id[:8]}_libro.pdf')
        except Exception as gen_err:
            return f"Error generando PDF para {preview_id}: {gen_err}", 500

    # 4) Quick story — generate CP book.pdf on demand
    story_texts = story_data.get('story_texts', [])
    has_qs_images = bool(
        story_data.get('scene_paths') or story_data.get('images') or
        story_data.get('original_scene_paths') or story_data.get('original_images')
    )
    if story_texts or has_qs_images:
        try:
            from services.quick_stories.pdf_service import generate_quick_story_pdf
            from services.cloudprinter_api_service import get_pdf_public_url
            cp_out_dir = os.path.join('generations', 'cloudprinter', preview_id)
            os.makedirs(cp_out_dir, exist_ok=True)
            book_pdf_path = os.path.join(cp_out_dir, 'book.pdf')
            generate_quick_story_pdf(story_data, book_pdf_path, print_format='A4')
            if os.path.exists(book_pdf_path):
                # Persist cp_pdf_url in story JSON so the page shows "Descargar PDF Cloudprinter"
                try:
                    preview_path = f'story_previews/{preview_id}.json'
                    if os.path.exists(preview_path):
                        with open(preview_path, 'r') as _rf:
                            _sd = json.load(_rf)
                        _sd['cp_pdf_url'] = get_pdf_public_url(preview_id, 'book.pdf')
                        if not _sd.get('cp_order_ref'):
                            _sd['cp_order_ref'] = 'ADMIN-GIFT'
                        with open(preview_path, 'w') as _wf:
                            json.dump(_sd, _wf, ensure_ascii=False)
                except Exception:
                    pass
                return send_file(os.path.abspath(book_pdf_path), as_attachment=True,
                                 download_name=f'{child_name}_{preview_id[:8]}_cuento.pdf')
        except Exception as qs_err:
            return f"Error generando PDF del cuento: {qs_err}", 500

    return f"PDF no encontrado para el pedido {preview_id}. Las escenas aún pueden estar generándose.", 404




@app.route('/admin/test-pdf-delivery/<preview_id>')
def admin_test_pdf_delivery(preview_id):
    """
    Manual test: trigger full printable-PDF generation + email for a given preview_id.
    Accessible only by pay@ admin. Useful to re-send or verify a PDF delivery.
    """
    if not check_admin_auth():
        return redirect(url_for('admin_login_page'))

    import re as _re
    if not _re.match(r'^[a-zA-Z0-9_\-]{4,64}$', preview_id):
        return jsonify({'success': False, 'error': 'Invalid preview_id'}), 400

    preview_file = f'story_previews/{preview_id}.json'
    if not os.path.exists(preview_file):
        return jsonify({'success': False, 'error': f'Preview not found: {preview_id}'}), 404

    with open(preview_file, 'r', encoding='utf-8') as f:
        story_data = json.load(f)

    lang           = story_data.get('lang', 'es')
    customer_email = request.args.get('to') or story_data.get('customer_email', '')

    import threading
    t = threading.Thread(
        target=_dispatch_printable_pdf_email,
        args=(preview_id, customer_email, lang),
        daemon=True
    )
    t.start()

    return jsonify({
        'success': True,
        'message': f'PDF delivery triggered for {preview_id} → {customer_email}',
        'preview_id': preview_id,
        'customer_email': customer_email,
        'lang': lang,
        'tip': 'Pass ?to=pay@magicmemoriesbooks.com to override recipient for QA testing.',
    })


@app.route('/admin/resend-qs-pdf/<preview_id>', methods=['POST'])
def admin_resend_qs_pdf(preview_id):
    """Re-trigger PDF email for a Quick Story (want_pdf=True path via _process_ebook_generation)."""
    if not check_admin_auth():
        return jsonify({'success': False, 'error': 'No autorizado'}), 401
    import re as _re
    if not _re.match(r'^[a-zA-Z0-9_\-]{4,64}$', preview_id):
        return jsonify({'success': False, 'error': 'Invalid preview_id'}), 400
    preview_file = f'story_previews/{preview_id}.json'
    if not os.path.exists(preview_file):
        return jsonify({'success': False, 'error': f'Preview not found: {preview_id}'}), 404
    with open(preview_file, 'r', encoding='utf-8') as f:
        story_data = json.load(f)
    customer_email = request.args.get('to') or story_data.get('customer_email', '')
    # Ensure want_pdf=True and pdf_email_sent=False so the function proceeds
    story_data['want_pdf'] = True
    story_data['pdf_email_sent'] = False
    with open(preview_file, 'w', encoding='utf-8') as f:
        json.dump(story_data, f, ensure_ascii=False, indent=2)
    # Clear the in-flight lock if it's stuck
    with _ebook_processing_lock:
        _ebook_processing_locks.discard(preview_id)
    t = threading.Thread(
        target=_process_ebook_generation,
        args=(preview_id, customer_email, True),
        daemon=True
    )
    t.start()
    return jsonify({
        'success': True,
        'message': f'QS PDF email re-triggered for {preview_id} → {customer_email}',
        'preview_id': preview_id,
        'customer_email': customer_email,
    })


@app.route('/admin/test-cp-connection')
def admin_test_cp_connection():
    """Test connection to Cloudprinter API (sandbox or production)."""
    if not check_admin_auth():
        return redirect(url_for('admin_login_page'))

    from services.cloudprinter_api_service import is_sandbox_mode as cp_sandbox, _get_api_key, CLOUDPRINTER_API_BASE
    import requests as _r

    sandbox = cp_sandbox()
    api_key = _get_api_key()
    result = {
        'sandbox_mode': sandbox,
        'api_base': CLOUDPRINTER_API_BASE,
        'connection_success': False,
        'message': ''
    }
    try:
        resp = _r.post(
            f"{CLOUDPRINTER_API_BASE}/orders/quote",
            json={"apikey": api_key, "country": "ES",
                  "items": [{"reference": "test", "product": "magazine_sas_a4_p_fc",
                              "count": "1",
                              "options": [{"type": "pageblock_130mcs", "count": "16"},
                                          {"type": "total_pages", "count": "16"}]}]},
            timeout=15
        )
        if resp.status_code == 200:
            result['connection_success'] = True
            result['message'] = f"Conexión exitosa a Cloudprinter {'SANDBOX' if sandbox else 'PRODUCTION'}"
        else:
            result['message'] = f"HTTP {resp.status_code}: {resp.text[:200]}"
    except Exception as e:
        result['message'] = f"Error: {e}"

    return render_template('admin_test_cp_connection.html', result=result)


@app.route('/admin/cp-order-lookup', methods=['GET', 'POST'])
def admin_cp_order_lookup():
    """Admin: look up any Cloudprinter order by reference and see address + tracking."""
    if not check_admin_auth():
        return redirect(url_for('admin_login_page'))

    result = None
    ref = ''
    if request.method == 'POST':
        ref = (request.form.get('reference') or '').strip()
        if ref:
            from services.cloudprinter_api_service import get_order_status
            result = get_order_status(ref)
            if result:
                print(f'[ADMIN CP LOOKUP] {ref} → status={result.get("status")} '
                      f'addr={result.get("cp_address")} tracking={result.get("tracking_number")}')
            else:
                result = {'error': f'No se encontró el pedido {ref} en Cloudprinter'}

    return render_template('admin_cp_order_lookup.html', result=result, ref=ref)


@app.route('/admin/update-shipping/<preview_id>', methods=['POST'])
def admin_update_shipping(preview_id):
    """Update shipping address for a failed order."""
    if not check_admin_auth():
        return jsonify({"error": "Unauthorized"}), 401
    
    preview_file = f'story_previews/{preview_id}.json'
    if not os.path.exists(preview_file):
        return jsonify({"error": "Preview not found"}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data"}), 400
    
    with open(preview_file, 'r', encoding='utf-8') as f:
        story_data = json.load(f)
    
    shipping_address = story_data.get('shipping_address', {})
    for field in ['name', 'street1', 'street2', 'city', 'state_code', 'postcode', 'country_code', 'phone_number', 'email']:
        if field in data:
            shipping_address[field] = data[field]
    
    story_data['shipping_address'] = shipping_address
    
    with open(preview_file, 'w', encoding='utf-8') as f:
        json.dump(story_data, f, ensure_ascii=False, indent=2)
    
    return jsonify({"success": True, "message": "Dirección actualizada", "address": shipping_address})


@app.route('/admin/enable-testing-mode', methods=['POST'])
def admin_enable_testing_mode():
    """Enable 4-hour testing mode: skip all regeneration limits globally."""
    if not check_admin_auth():
        return jsonify({'error': 'Unauthorized'}), 401
    import time
    hours = int(request.json.get('hours', 4)) if request.json else 4
    expires_at = time.time() + hours * 3600
    os.makedirs('data', exist_ok=True)
    with open(_TESTING_MODE_FILE, 'w') as f:
        json.dump({'expires_at': expires_at, 'hours': hours}, f)
    import datetime
    expire_str = datetime.datetime.fromtimestamp(expires_at).strftime('%H:%M')
    production_logger.info(f"[ADMIN] Testing mode enabled for {hours}h (expires {expire_str})")
    return jsonify({'success': True, 'expires_at': expires_at, 'expire_str': expire_str})


@app.route('/admin/testing-mode-status', methods=['GET'])
def admin_testing_mode_status():
    """Check if testing mode is currently active."""
    if not check_admin_auth():
        return jsonify({'error': 'Unauthorized'}), 401
    import time
    active = is_testing_mode_active()
    remaining = 0
    if active:
        try:
            with open(_TESTING_MODE_FILE, 'r') as f:
                d = json.load(f)
            remaining = max(0, int(d.get('expires_at', 0) - time.time()))
        except Exception:
            pass
    return jsonify({'active': active, 'remaining_seconds': remaining})


@app.route('/admin/simulate-payment/<preview_id>', methods=['GET', 'POST'])
def admin_simulate_payment(preview_id):
    """Simula un pago completado para pruebas del flujo completo sin PayPal.
    Marca el libro como pagado, activa modo testing (8h), resetea contadores de
    regeneración, lanza generación de escenas si están pendientes, y redirige
    a order-complete.
    """
    if not check_admin_auth():
        return redirect(url_for('admin_login_page'))

    preview_file = f'story_previews/{preview_id}.json'
    if not os.path.exists(preview_file):
        return f"Story {preview_id} no encontrada", 404

    with open(preview_file, 'r', encoding='utf-8') as f:
        story_data = json.load(f)

    # Marcar como pago completado (tipo personalized_pdf = digital + PDF imprimible)
    story_data['pdf_paid'] = True
    story_data['pdf_paid_at'] = datetime.now().isoformat()
    story_data['product_type'] = 'personalized_pdf'
    story_data['want_print'] = False
    story_data['pdf_order'] = True
    story_data['is_test_payment'] = True  # flag para omitir email real al finalizar

    # Resetear contadores de regeneración para prueba limpia
    story_data['cover_regenerations'] = 0
    story_data['regeneration_used'] = False
    story_data['scene_regenerations'] = {}
    story_data['page_regenerations'] = {}
    story_data['email_sent'] = False
    story_data['pages_composed'] = False

    with open(preview_file, 'w', encoding='utf-8') as f:
        json.dump(story_data, f, ensure_ascii=False, indent=2)

    # Activar testing mode por 8 horas (sin límites de regeneración)
    import time as _sp_time
    _sp_expires = _sp_time.time() + 8 * 3600
    os.makedirs('data', exist_ok=True)
    with open(_TESTING_MODE_FILE, 'w') as _sp_f:
        json.dump({'expires_at': _sp_expires, 'hours': 8}, _sp_f)

    # Lanzar generación de escenas si están pendientes
    if story_data.get('scenes_pending') and not story_data.get('scenes_generating'):
        _trigger_background_generation(preview_id)
        print(f"[SIMULATE-PAYMENT] Launched background scene generation for {preview_id}")

    production_logger.info(f"[ADMIN] Pago simulado para {preview_id} — testing mode 8h activo")
    print(f"[SIMULATE-PAYMENT] Payment simulated for {preview_id}, testing mode enabled 8h")

    return redirect(url_for('order_complete', preview_id=preview_id))


@app.route('/admin/reset-regen-counts/<preview_id>', methods=['POST'])
def admin_reset_regen_counts(preview_id):
    """Reset all regeneration counters so testing can proceed without limits."""
    if not check_admin_auth():
        return jsonify({'error': 'Unauthorized'}), 401
    preview_file = f'story_previews/{preview_id}.json'
    if not os.path.exists(preview_file):
        preview_file = f'generations/previews/{preview_id}.json'
    if not os.path.exists(preview_file):
        return jsonify({'success': False, 'error': 'Preview not found'}), 404
    with open(preview_file, 'r', encoding='utf-8') as f:
        story_data = json.load(f)
    story_data['regeneration_used']  = False
    story_data['scene_regenerations'] = {}
    story_data['page_regenerations']  = {}
    with open(preview_file, 'w', encoding='utf-8') as f:
        json.dump(story_data, f, ensure_ascii=False, indent=2)
    production_logger.info(f"[ADMIN] Regen counts reset for {preview_id}")
    return jsonify({'success': True})


@app.route('/admin/reset-compose/<preview_id>', methods=['POST'])
def admin_reset_compose(preview_id):
    """Reset book_composing flag so a stuck compose task can be re-triggered."""
    if not check_admin_auth():
        return jsonify({'error': 'Unauthorized'}), 401

    preview_file = f'story_previews/{preview_id}.json'
    if not os.path.exists(preview_file):
        return jsonify({'error': 'Preview not found'}), 404

    with open(preview_file, 'r', encoding='utf-8') as f:
        story_data = json.load(f)

    was_composing = story_data.get('book_composing', False)
    story_data['book_composing'] = False
    story_data['generation_error'] = ''
    story_data['pages_composed'] = False

    with open(preview_file, 'w', encoding='utf-8') as f:
        json.dump(story_data, f, ensure_ascii=False, indent=2)

    production_logger.info(f"[ADMIN] Compose state reset for {preview_id} (was_composing={was_composing})")
    return jsonify({'success': True, 'message': f'Compose state reset. was_composing={was_composing}. Now refresh the order page to re-trigger.'})


@app.route('/admin/recompose-text/<preview_id>', methods=['POST'])
def admin_recompose_text(preview_id):
    """Reapply text overlay to existing clean scene images using the current algorithm.
    Does NOT regenerate AI images. Does NOT send emails or change order status."""
    if not check_admin_auth():
        return jsonify({'error': 'Unauthorized'}), 401

    import re as _re
    if not _re.match(r'^[a-zA-Z0-9_\-]+$', preview_id):
        return jsonify({'error': 'Invalid preview ID'}), 400

    preview_file = f'story_previews/{preview_id}.json'
    if not os.path.exists(preview_file):
        return jsonify({'error': 'Preview not found'}), 404

    with open(preview_file, 'r', encoding='utf-8') as f:
        story_data = json.load(f)

    if not story_data.get('is_illustrated_book', False):
        return jsonify({'error': 'Solo para libros ilustrados'}), 400

    story_id = story_data.get('story_id', '')
    child_name = story_data.get('child_name', 'Child')
    lang = story_data.get('lang', 'es')
    traits = story_data.get('traits', {})
    composed_dir = story_data.get('composed_pages_dir', f'generated/composed_{preview_id}')
    pet_name = traits.get('pet_name', '')

    from services.illustrated_book_service import BOOK_CONFIGS, add_text_to_image
    from services.personalized_books.generation import get_personalized_book_id
    from PIL import Image as _PIL_Image

    book_id = get_personalized_book_id(story_id)
    book_config = BOOK_CONFIGS.get(book_id, {})
    scenes = book_config.get('scenes', [])

    if not scenes:
        return jsonify({'error': f'No se encontró config de escenas para {book_id}'}), 400

    original_paths = story_data.get('original_scene_paths', story_data.get('original_images', []))

    recomposed = 0
    skipped = 0
    errors = []

    for scene_idx, scene_config in enumerate(scenes):
        clean_path = os.path.join(composed_dir, f'clean_scene_{scene_idx}.png')
        if not os.path.exists(clean_path):
            skipped += 1
            continue

        text_key = f'text_{lang}'
        text = scene_config.get(text_key, scene_config.get('text_es', ''))
        text = text.replace('{name}', child_name)
        if pet_name:
            text = text.replace('{pet_name}', pet_name)

        position = scene_config.get('text_position', 'split')

        try:
            img = _PIL_Image.open(clean_path).convert('RGBA')
            final_img = add_text_to_image(img, text, position, '#FFFFFF', '#000000', 38, 0.103)

            page_list_idx = scene_idx + 4
            if page_list_idx < len(original_paths):
                page_path = original_paths[page_list_idx].lstrip('/')
            else:
                page_path = os.path.join(composed_dir, f'page_{scene_idx + 5:02d}.png')

            final_img.save(page_path, 'PNG')
            recomposed += 1
        except Exception as e:
            errors.append(f'scene_{scene_idx}: {str(e)}')
            production_logger.warning(f'[RECOMPOSE-TEXT] Error on scene {scene_idx}: {e}')

    if recomposed == 0:
        return jsonify({
            'success': False,
            'error': f'No se encontraron clean_scene files en {composed_dir}. '
                     'Solo funciona si el libro fue generado con el flujo de dos etapas.',
            'skipped': skipped
        }), 400

    def _rebuild_in_bg(pid, **kwargs):
        try:
            from services.personalized_books.rebuild import rebuild_book
            rebuild_book(pid)
            production_logger.info(f'[RECOMPOSE-TEXT] Background rebuild complete for {pid}')
        except Exception as _rb_err:
            production_logger.warning(f'[RECOMPOSE-TEXT] Background rebuild failed for {pid}: {_rb_err}')

    task_queue.enqueue(f'recompose_rebuild_{preview_id}', _rebuild_in_bg, preview_id)

    production_logger.info(f'[RECOMPOSE-TEXT] {preview_id}: recomposed={recomposed}, skipped={skipped}, rebuild=background')
    return jsonify({
        'success': True,
        'recomposed': recomposed,
        'skipped': skipped,
        'rebuild': 'background',
        'errors': errors
    })


@app.route('/admin/generate-cp-pdfs/<preview_id>', methods=['POST'])
def admin_generate_cp_pdfs(preview_id):
    """Generate cover.pdf + content.pdf for Cloudprinter WITHOUT submitting the order.
    Lets admin review both PDFs before committing to print."""
    if not check_admin_auth():
        return jsonify({'error': 'Unauthorized'}), 401
    import re
    if not re.match(r'^[a-zA-Z0-9_\-]+$', preview_id):
        return jsonify({'error': 'Invalid preview ID'}), 400

    preview_file = f'story_previews/{preview_id}.json'
    if not os.path.exists(preview_file):
        return jsonify({'error': 'Preview no encontrado'}), 404

    with open(preview_file, 'r', encoding='utf-8') as f:
        story_data = json.load(f)

    is_illustrated = story_data.get('is_illustrated_book', False)

    if is_illustrated:
        try:
            from services.personalized_books.cp_pdf_service import generate_cw_cover_pdf, generate_cw_content_pdf
            from services.cloudprinter_api_service import get_pb_chosen_page_count

            # Re-upload visor to pick up any regenerated scenes
            try:
                from services.vps_upload_service import prepare_and_upload
                prepare_and_upload(story_data, preview_id)
            except Exception as _vu_err:
                print(f"[GEN-CP-PDF] Visor re-upload skipped: {_vu_err}")

            out_dir = os.path.join('generations', 'cloudprinter', preview_id)
            os.makedirs(out_dir, exist_ok=True)
            page_count = get_pb_chosen_page_count()

            cover_pdf_path   = os.path.join(out_dir, 'cover.pdf')
            content_pdf_path = os.path.join(out_dir, 'content.pdf')

            child_name  = story_data.get('child_name', '')
            story_name  = story_data.get('story_name', story_data.get('story_id', ''))
            lang        = story_data.get('lang', 'es')
            gender      = story_data.get('gender', 'nino')
            book_id     = story_data.get('story_id', '')
            traits      = story_data.get('traits') or {}
            pet_name    = traits.get('pet_name', '')
            visor_dir   = os.path.join('generations', 'visor_pb', preview_id)

            from services.personalized_books.generation import get_book_title
            book_title = get_book_title(book_id, child_name, lang, pet_name=pet_name) or story_name or child_name

            generate_cw_cover_pdf(
                session_id=preview_id,
                book_title=book_title,
                output_path=cover_pdf_path,
                page_count=page_count,
                story_id=book_id,
            )
            generate_cw_content_pdf(
                session_id=preview_id,
                child_name=child_name,
                language=lang,
                output_path=content_pdf_path,
                page_count=page_count,
            )

            cover_url   = f'/cp-files/{preview_id}/cover.pdf'
            content_url = f'/cp-files/{preview_id}/content.pdf'

            cover_ok   = os.path.exists(cover_pdf_path)
            content_ok = os.path.exists(content_pdf_path)
            cover_size   = round(os.path.getsize(cover_pdf_path)   / 1024) if cover_ok   else 0
            content_size = round(os.path.getsize(content_pdf_path) / 1024) if content_ok else 0

            return jsonify({
                'success': True,
                'cover_url':    cover_url,
                'content_url':  content_url,
                'cover_size_kb':   cover_size,
                'content_size_kb': content_size,
                'message': f'PDFs generados — Portada: {cover_size} KB · Interior: {content_size} KB',
            })
        except Exception as e:
            import traceback; traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500

    # Quick Story
    try:
        from services.cloudprinter_api_service import get_pdf_public_url
        from services.quick_stories.pdf_service import generate_quick_story_cloudprinter_pdf

        cp_folder = f'generations/cloudprinter/{preview_id}'
        os.makedirs(cp_folder, exist_ok=True)
        pdf_output = os.path.join(cp_folder, 'book.pdf')

        _scenes = story_data.get('original_scene_paths', story_data.get('scene_paths', []))
        _cover  = story_data.get('original_cover', story_data.get('front_cover_path', story_data.get('cover_image', '')))
        if _cover and _cover.startswith('/'):
            _cover = _cover[1:]
        _scenes = [p.lstrip('/') for p in _scenes if p]
        if not _scenes:
            return jsonify({'error': 'No se encontraron imágenes del cuento.'}), 400

        generate_quick_story_cloudprinter_pdf(
            story_data=story_data,
            output_path=pdf_output,
        )
        book_ok   = os.path.exists(pdf_output)
        book_size = round(os.path.getsize(pdf_output) / 1024) if book_ok else 0
        return jsonify({
            'success': True,
            'book_url': f'/cp-files/{preview_id}/book.pdf',
            'book_size_kb': book_size,
            'message': f'PDF generado — {book_size} KB',
        })
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/admin/set-pdf-format/<preview_id>', methods=['POST'])
def admin_set_pdf_format(preview_id):
    """Admin: set the downloadable printable PDF format (A4 or LETTER/Carta) for a
    preview and clear any cached PDF so the next download regenerates in the new format."""
    if not check_admin_auth():
        return jsonify({'error': 'Unauthorized'}), 401
    import re
    if not re.match(r'^[a-zA-Z0-9_\-]+$', preview_id):
        return jsonify({'error': 'Invalid preview ID'}), 400

    data = request.get_json() or {}
    print_format = 'LETTER' if data.get('print_format') == 'LETTER' else 'A4'

    preview_file = f'story_previews/{preview_id}.json'
    if not os.path.exists(preview_file):
        return jsonify({'error': 'Preview no encontrado'}), 404

    with open(preview_file, 'r', encoding='utf-8') as f:
        story_data = json.load(f)

    story_data['print_format'] = print_format
    # Clear cached printable PDF path so it regenerates in the newly chosen format
    story_data.pop('pdf_printable_path', None)

    with open(preview_file, 'w', encoding='utf-8') as f:
        json.dump(story_data, f, ensure_ascii=False, indent=2)

    return jsonify({
        'success': True,
        'print_format': print_format,
        'download_url': f'/download-book/{preview_id}',
        'message': f'Formato actualizado a {"Carta" if print_format == "LETTER" else "A4"}. El PDF se regenerará al descargar.',
    })


@app.route('/admin/gift-check-shipping/<preview_id>', methods=['POST'])
def admin_gift_check_shipping(preview_id):
    """Admin: check Cloudprinter shipping availability/price BEFORE submitting a gift
    print order, so the admin can warn the client and offer the PDF instead if there
    is no printing coverage or quote for that country."""
    if not check_admin_auth():
        return jsonify({'error': 'Unauthorized'}), 401
    import re
    if not re.match(r'^[a-zA-Z0-9_\-]+$', preview_id):
        return jsonify({'error': 'Invalid preview ID'}), 400

    preview_file = f'story_previews/{preview_id}.json'
    if not os.path.exists(preview_file):
        return jsonify({'error': 'Preview no encontrado'}), 404

    with open(preview_file, 'r', encoding='utf-8') as f:
        story_data = json.load(f)

    data = request.get_json() or {}
    country_code = (data.get('country_code') or '').strip().upper()
    state_code = (data.get('state_code') or '').strip().upper()
    if not country_code:
        return jsonify({'error': 'Falta country_code'}), 400

    is_illustrated = story_data.get('is_illustrated_book', False)

    from services.cloudprinter_api_service import (
        CLOUDPRINTER_AVAILABLE_COUNTRIES, get_shipping_quote, get_pb_shipping_quote
    )

    if country_code not in CLOUDPRINTER_AVAILABLE_COUNTRIES:
        return jsonify({
            'available': False,
            'error': 'no_shipping_to_country',
            'message_es': f'⚠️ Cloudprinter NO imprime/envía a {country_code}. Recomendamos enviar el PDF imprimible en su lugar.',
        })

    quote_fn = get_pb_shipping_quote if is_illustrated else get_shipping_quote
    try:
        options = quote_fn(country_code, state_code=state_code)
    except Exception as e:
        return jsonify({
            'available': False,
            'error': 'quote_failed',
            'message_es': f'⚠️ No se pudo obtener cotización de Cloudprinter ({e}). Recomendamos enviar el PDF imprimible en su lugar.',
        })

    if not options:
        return jsonify({
            'available': False,
            'error': 'no_shipping_options',
            'message_es': f'⚠️ Cloudprinter no devolvió opciones de envío para {country_code}{" / " + state_code if state_code else ""}. NO se puede confirmar precio ni entrega — recomendamos enviar el PDF imprimible en su lugar de imprimir sin cotización.',
        })

    cheapest = min(options.values(), key=lambda o: float(o.get('cp_cost_usd', o.get('total_usd', 9e9))))
    return jsonify({
        'available': True,
        'country_code': country_code,
        'options_count': len(options),
        'cheapest_shipping_usd': round(float(cheapest.get('cp_cost_usd', cheapest.get('total_usd', 0))), 2),
        'print_cost_usd': round(float(cheapest.get('print_cost_usd', 0)), 2),
        'message_es': f'✅ Cloudprinter SÍ imprime y envía a {country_code}. Costo estimado de envío: ${round(float(cheapest.get("cp_cost_usd", cheapest.get("total_usd", 0))), 2)} USD.',
    })


@app.route('/admin/gift-send-to-cp/<preview_id>', methods=['POST'])
def admin_gift_send_to_cp(preview_id):
    """Submit an admin gift book to Cloudprinter. Handles both Quick Story and illustrated PB books."""
    if not check_admin_auth():
        return jsonify({'error': 'Unauthorized'}), 401

    preview_file = f'story_previews/{preview_id}.json'
    if not os.path.exists(preview_file):
        return jsonify({'error': 'Preview not found'}), 404

    with open(preview_file, 'r', encoding='utf-8') as f:
        story_data = json.load(f)

    data = request.get_json() or {}
    name = data.get('name', '').strip()
    street1 = data.get('street1', '').strip()
    city = data.get('city', '').strip()
    postal_code = data.get('postal_code', '').strip()
    if not name or not street1 or not city or not postal_code:
        return jsonify({'error': 'Nombre, dirección, ciudad y código postal son obligatorios'}), 400

    shipping_address = {
        'name': name,
        'street1': street1,
        'street2': data.get('street2', '').strip(),
        'city': city,
        'state_code': data.get('state_code', '').strip(),
        'postcode': postal_code,
        'country_code': data.get('country_code', 'ES').strip().upper(),
        'phone_number': data.get('phone_number', '').strip(),
        'email': data.get('email', story_data.get('customer_email', '')).strip(),
    }

    child_name = story_data.get('child_name', '')
    lang = story_data.get('lang', 'es')
    story_name = story_data.get('story_name', '')
    customer_email = story_data.get('customer_email', story_data.get('admin_gift_email', ''))
    shipping_level = data.get('shipping_level', 'cp_saver')

    is_illustrated = story_data.get('is_illustrated_book', False)

    # ── Illustrated Personalized Book (centinela_aurora, dragon_garden, etc.) ──
    if is_illustrated:
        try:
            from services.personalized_books.cp_pdf_service import generate_cw_cover_pdf, generate_cw_content_pdf
            from services.cloudprinter_api_service import submit_pb_print_order, get_pdf_public_url, get_pb_chosen_page_count
            from services.cloudprinter_api_service import resolve_shipping_level

            # Always re-upload visor before building Cloudprinter PDF so any
            # admin-regenerated scenes are reflected in page_N.jpg
            try:
                from services.vps_upload_service import prepare_and_upload
                print(f"[ADMIN-CP] Re-uploading visor for {preview_id} to pick up regenerated images…")
                prepare_and_upload(story_data, preview_id)
                story_data['visor_uploaded'] = True
                print(f"[ADMIN-CP] Visor re-upload done for {preview_id}")
            except Exception as _vu_err:
                print(f"[ADMIN-CP] Visor re-upload failed (continuing anyway): {_vu_err}")

            out_dir = os.path.join('generations', 'cloudprinter', preview_id)
            os.makedirs(out_dir, exist_ok=True)
            page_count = get_pb_chosen_page_count()

            # Get book title from visor metadata or fallback
            book_title = story_name or child_name
            visor_meta = os.path.join('generations', 'visor_pb', preview_id, 'metadata.json')
            if os.path.exists(visor_meta):
                with open(visor_meta) as _mf:
                    _md = json.load(_mf)
                    book_title = _md.get('title', book_title)

            cover_pdf_path   = os.path.join(out_dir, 'cover.pdf')
            content_pdf_path = os.path.join(out_dir, 'content.pdf')

            generate_cw_content_pdf(
                session_id=preview_id,
                child_name=child_name,
                language=lang,
                output_path=content_pdf_path,
                page_count=page_count,
            )
            generate_cw_cover_pdf(
                session_id=preview_id,
                book_title=book_title,
                output_path=cover_pdf_path,
                page_count=page_count,
                story_id=story_data.get('story_id', ''),
            )

            cover_pdf_url   = get_pdf_public_url(preview_id, 'cover.pdf')
            content_pdf_url = get_pdf_public_url(preview_id, 'content.pdf')
            cp_shipping_level = resolve_shipping_level(shipping_level)

            cp_ok, cp_msg, cp_ref = submit_pb_print_order(
                preview_id=preview_id,
                cover_pdf_path=cover_pdf_path,
                cover_pdf_url=cover_pdf_url,
                content_pdf_path=content_pdf_path,
                content_pdf_url=content_pdf_url,
                customer_data={'email': customer_email},
                shipping_address=shipping_address,
                shipping_level=cp_shipping_level,
            )
            if cp_ok:
                story_data['cp_pb_order_ref'] = cp_ref
                story_data['cp_order_status'] = 'submitted'
                story_data['cp_cover_pdf_url'] = cover_pdf_url
                story_data['cp_content_pdf_url'] = content_pdf_url
                story_data['shipping_address'] = shipping_address
                story_data['want_print'] = True
                with open(preview_file, 'w', encoding='utf-8') as f:
                    json.dump(story_data, f, ensure_ascii=False, indent=2)
                try:
                    from services.email_service import send_cp_pb_admin_notification
                    send_cp_pb_admin_notification(
                        preview_id=preview_id,
                        cp_order_ref=cp_ref or '',
                        title=book_title,
                        customer_email=customer_email,
                        shipping_address=shipping_address,
                        cover_pdf_url=cover_pdf_url,
                        content_pdf_url=content_pdf_url,
                        visor_url=story_data.get('visor_url', ''),
                        paid_amount='Admin Gift',
                        cp_cost_eur=0,
                        print_cost_eur=0,
                    )
                except Exception as email_err:
                    print(f"[ADMIN-CP PB] Email error (non-fatal): {email_err}")
                return jsonify({'success': True, 'cp_order_ref': cp_ref, 'message': cp_msg})
            else:
                return jsonify({'success': False, 'error': cp_msg})
        except Exception as e:
            import traceback; traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500

    # ── Quick Story (single-PDF flow) ───────────────────────────────────────────
    from services.cloudprinter_api_service import submit_print_order as cp_submit, get_pdf_public_url
    from services.quick_stories.pdf_service import generate_quick_story_cloudprinter_pdf

    cp_folder = f'generations/cloudprinter/{preview_id}'
    os.makedirs(cp_folder, exist_ok=True)
    pdf_output = os.path.join(cp_folder, 'book.pdf')

    _scenes = story_data.get('original_scene_paths', story_data.get('scene_paths', []))
    _cover = story_data.get('original_cover', story_data.get('front_cover_path', story_data.get('cover_image', '')))
    if _cover and _cover.startswith('/'):
        _cover = _cover[1:]
    _scenes = [p.lstrip('/') for p in _scenes if p]
    if not _scenes:
        return jsonify({'error': 'No se encontraron imágenes del cuento. Asegúrate de que el cuento esté completamente generado.'}), 400

    try:
        pdf_path = generate_quick_story_cloudprinter_pdf(
            story_data=story_data,
            images=_scenes,
            front_cover_path=_cover,
            output_path=pdf_output
        )
    except Exception as pdf_err:
        import traceback; traceback.print_exc()
        return jsonify({'error': f'Error generando PDF: {str(pdf_err)[:200]}'}), 500

    pdf_url = get_pdf_public_url(preview_id, 'book.pdf')

    try:
        cp_success, cp_msg, cp_order_ref = cp_submit(
            preview_id=preview_id,
            pdf_path=pdf_path,
            pdf_url=pdf_url,
            customer_data={'email': customer_email},
            shipping_address=shipping_address
        )
        if cp_success:
            story_data['cp_submitted'] = True
            story_data['cp_order_ref'] = cp_order_ref
            story_data['cp_pdf_url'] = pdf_url
            story_data['shipping_address'] = shipping_address
            story_data['want_print'] = True
            with open(preview_file, 'w', encoding='utf-8') as f:
                json.dump(story_data, f, ensure_ascii=False, indent=2)
            try:
                from services.email_service import send_cp_order_notification
                _title = f"{story_name} - {child_name} (Admin Gift)"
                send_cp_order_notification(
                    preview_id=preview_id,
                    cp_order_ref=cp_order_ref or 'N/A',
                    title=_title,
                    customer_email=customer_email,
                    shipping_address=shipping_address,
                    pdf_url=pdf_url
                )
            except Exception as email_err:
                print(f"[ADMIN-CP] Email error (non-fatal): {email_err}")
            return jsonify({'success': True, 'cp_order_ref': cp_order_ref, 'message': cp_msg})
        else:
            return jsonify({'success': False, 'error': cp_msg})
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/admin/retry-cp/<preview_id>', methods=['POST'])
def admin_retry_cp_submission(preview_id):
    """Retry Cloudprinter submission for a failed Quick Story order."""
    if not check_admin_auth():
        return jsonify({"error": "Unauthorized"}), 401

    preview_file = f'story_previews/{preview_id}.json'
    if not os.path.exists(preview_file):
        return jsonify({"error": "Preview not found"}), 404

    with open(preview_file, 'r', encoding='utf-8') as f:
        story_data = json.load(f)

    if not story_data.get('paid'):
        return jsonify({"error": "Order not paid"}), 400

    shipping_address = story_data.get('shipping_address')
    if not shipping_address:
        return jsonify({"error": "No shipping address"}), 400

    from services.cloudprinter_api_service import submit_print_order as cp_submit, get_pdf_public_url
    from services.quick_stories.pdf_service import generate_quick_story_cloudprinter_pdf

    child_name = story_data.get('child_name', 'Unknown')
    story_name = story_data.get('story_name', story_data.get('title', 'Quick Story'))
    customer_email = story_data.get('customer_email', '')
    lang = story_data.get('lang', 'es')

    cp_folder = f'generations/cloudprinter/{preview_id}'
    os.makedirs(cp_folder, exist_ok=True)
    pdf_output = os.path.join(cp_folder, 'book.pdf')

    if not os.path.exists(pdf_output):
        _regen_scenes = story_data.get('original_scene_paths', story_data.get('scene_paths', []))
        _regen_cover = story_data.get('original_cover', story_data.get('front_cover_path', story_data.get('cover_image', '')))
        if _regen_cover and _regen_cover.startswith('/'):
            _regen_cover = _regen_cover[1:]
        _regen_scenes = [p.lstrip('/') for p in _regen_scenes if p]
        if not _regen_scenes:
            return jsonify({"error": "No se encontraron imágenes para regenerar el PDF"}), 400
        try:
            generate_quick_story_cloudprinter_pdf(
                story_data=story_data,
                images=_regen_scenes,
                front_cover_path=_regen_cover,
                output_path=pdf_output
            )
            print(f"[RETRY-CP] PDF regenerated → {pdf_output}")
        except Exception as _regen_err:
            import traceback; traceback.print_exc()
            return jsonify({"error": f"Error regenerando PDF: {_regen_err}"}), 500

    pdf_url = get_pdf_public_url(preview_id, 'book.pdf')

    try:
        cp_success, cp_msg, cp_order_ref = cp_submit(
            preview_id=preview_id,
            pdf_path=pdf_output,
            pdf_url=pdf_url,
            customer_data={'email': customer_email},
            shipping_address=shipping_address
        )

        if cp_success:
            story_data['cp_submitted'] = True
            story_data['cp_order_ref'] = cp_order_ref
            story_data['cp_status'] = 'sent'
            story_data['cp_error'] = None
            story_data['cp_pdf_url'] = pdf_url
            with open(preview_file, 'w', encoding='utf-8') as f:
                json.dump(story_data, f, ensure_ascii=False, indent=2)
            try:
                from services.email_service import send_cp_order_notification
                book_title = f"{story_name} - {child_name}"
                send_cp_order_notification(
                    preview_id=preview_id,
                    cp_order_ref=cp_order_ref or 'N/A',
                    title=book_title,
                    customer_email=customer_email,
                    shipping_address=shipping_address,
                    pdf_url=pdf_url
                )
            except Exception:
                pass
            return jsonify({"success": True, "message": f"Order submitted to Cloudprinter! Ref: {cp_order_ref}", "cp_order_ref": cp_order_ref})
        else:
            story_data['cp_error'] = cp_msg or 'Failed to submit'
            with open(preview_file, 'w', encoding='utf-8') as f:
                json.dump(story_data, f, ensure_ascii=False, indent=2)
            return jsonify({"error": cp_msg or "Failed to submit to Cloudprinter"}), 500

    except Exception as e:
        app.logger.error(f"Error retrying CP submission: {e}")
        import traceback; traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/admin/send-cp-resolved/<preview_id>', methods=['POST'])
def admin_send_cp_resolved(preview_id):
    """Manually notify a customer that their Cloudprinter order issue has been resolved."""
    if not check_admin_auth():
        return jsonify({"error": "Unauthorized"}), 401

    preview_file = os.path.join('story_previews', f'{preview_id}.json')
    if not os.path.exists(preview_file):
        return jsonify({"error": "Preview not found"}), 404

    with open(preview_file, 'r', encoding='utf-8') as f:
        story_data = json.load(f)

    customer_email = story_data.get('customer_email', '')
    child_name = story_data.get('child_name', 'Unknown')
    lang = story_data.get('lang', 'es')
    cp_order_ref = story_data.get('cp_order_ref', story_data.get('lulu_job_id', ''))

    if not customer_email:
        return jsonify({"error": "No customer email found"}), 400

    results = {}

    try:
        from services.email_service import send_cp_order_notification
        shipping_address = story_data.get('shipping_address', {})
        pdf_url = story_data.get('cp_pdf_url', '')
        story_name = story_data.get('story_name', story_data.get('title', 'Quick Story'))
        book_title = f"{story_name} - {child_name}"
        send_cp_order_notification(
            preview_id=preview_id,
            cp_order_ref=str(cp_order_ref) if cp_order_ref else 'manual',
            title=book_title,
            customer_email=customer_email,
            shipping_address=shipping_address,
            pdf_url=pdf_url
        )
        results['admin_email'] = 'sent'
    except Exception as e:
        results['admin_email'] = f'error: {e}'

    story_data['cp_resolved_email_sent'] = True
    with open(preview_file, 'w', encoding='utf-8') as f:
        json.dump(story_data, f, ensure_ascii=False, indent=2)

    return jsonify({"success": True, "results": results})


# ============================================================
# ADMIN: PENDING RETRIES PANEL (Feb 2026)
# ============================================================

@app.route('/admin/pending-retries')
def admin_pending_retries():
    if not check_admin_auth():
        return redirect(url_for('admin_login_page'))
    
    import glob as glob_mod
    pending_retries = []
    preview_files = glob_mod.glob('story_previews/*.json')
    
    for pf in sorted(preview_files, key=os.path.getmtime, reverse=True):
        try:
            with open(pf, 'r') as f:
                data = json.load(f)
            
            failed_scenes = data.get('failed_scenes', [])
            scenes_retrying = data.get('scenes_retrying', False)
            retry_exhausted = data.get('retry_exhausted', False)
            
            if failed_scenes or scenes_retrying or retry_exhausted:
                pid = os.path.basename(pf).replace('.json', '')
                pending_retries.append({
                    'preview_id': pid,
                    'child_name': data.get('child_name', 'Unknown'),
                    'story_id': data.get('story_id', ''),
                    'customer_email': data.get('customer_email', ''),
                    'failed_scenes': [i+1 for i in failed_scenes],
                    'retry_count': data.get('retry_count', 0),
                    'max_retries': data.get('max_retries', 6),
                    'scenes_retrying': scenes_retrying,
                    'retry_exhausted': retry_exhausted,
                    'created': datetime.fromtimestamp(os.path.getmtime(pf)).strftime('%Y-%m-%d %H:%M'),
                })
        except:
            pass
    
    return render_template('admin_pending_retries.html', pending_retries=pending_retries)


@app.route('/admin/cuentos')
def admin_cuentos():
    """Admin: dedicated page listing all story previews."""
    if not check_admin_auth():
        return redirect(url_for('admin_login_page'))
    import glob as glob_mod
    story_previews = []
    preview_files = glob_mod.glob('story_previews/*.json')

    def _real_date(data, filepath):
        """Return the real meaningful date: payment_date for paid, ctime for previews."""
        pd = data.get('payment_date')
        if pd:
            try:
                return pd[:16].replace('T', ' ')
            except Exception:
                pass
        return datetime.fromtimestamp(os.path.getctime(filepath)).strftime('%Y-%m-%d %H:%M')

    # Two-pass: read all, then sort by real date desc
    _all_previews = []
    for pf in preview_files:
        try:
            pid = os.path.basename(pf).replace('.json', '')
            if pid.upper().startswith('TEST_'):
                continue
            if '_progress' in pid:
                continue
            with open(pf, 'r', encoding='utf-8') as f:
                data = json.load(f)
            _pd = data.get('payment_date')
            if _pd:
                try:
                    _sort_ts = datetime.fromisoformat(_pd[:19]).timestamp()
                except Exception:
                    _sort_ts = os.path.getctime(pf)
            else:
                _sort_ts = os.path.getctime(pf)
            _all_previews.append((_sort_ts, pf, data, pid))
        except Exception:
            pass

    _all_previews.sort(key=lambda x: x[0], reverse=True)

    for _sort_ts, pf, data, pid in _all_previews[:100]:
        story_previews.append({
            'preview_id': pid,
            'child_name': data.get('child_name', 'Unknown'),
            'story_id': data.get('story_id', ''),
            'customer_email': data.get('customer_email', ''),
            'paid': data.get('paid', False) or data.get('payment_status') == 'completed'
                    or float(data.get('amount_paid') or 0) > 0,
            'has_scenes': len(data.get('scenes', [])) > 0,
            'created': _real_date(data, pf),
        })
    return render_template('admin_cuentos.html', story_previews=story_previews)


def _build_compra_codes(d):
    """Return ordered list of purchase codes like ['QS_EBOOK', 'QS_PDF', 'QS_PRINT']."""
    product_type = d.get('product_type', '') or ''
    _PB_TYPES = ('cp_personalized', 'personalized_pdf', 'personalized_book', 'personalized')
    # Also treat illustrated books as PB regardless of product_type field
    is_pb = product_type in _PB_TYPES or bool(d.get('is_illustrated_book'))
    familia = 'PB' if is_pb else 'QS'
    parts = []
    fp = d.get('format_prices', {}) or {}
    fmts = d.get('formats', []) or []
    want_ebook = d.get('want_ebook', False)
    want_pdf = d.get('want_pdf', False) or d.get('pdf_paid', False)
    want_print = d.get('want_print', False)
    if fp:
        if 'ebook' in fp:
            parts.append(f'{familia}_EBOOK')
        if 'digital' in fp or 'pdf' in fp:
            parts.append(f'{familia}_PDF')
        if 'print' in fp:
            parts.append(f'{familia}_PRINT')
    elif fmts:
        if 'ebook' in fmts:
            parts.append(f'{familia}_EBOOK')
        if 'digital' in fmts or 'pdf' in fmts:
            parts.append(f'{familia}_PDF')
        if 'print' in fmts:
            parts.append(f'{familia}_PRINT')
    else:
        if want_ebook:
            parts.append(f'{familia}_EBOOK')
        if want_pdf:
            parts.append(f'{familia}_PDF')
        if want_print:
            parts.append(f'{familia}_PRINT')
        if not parts:
            _fallback = {
                'qs_digital': ['QS_EBOOK'], 'ebook': ['QS_EBOOK'],
                'qs_print': ['QS_PRINT'],
                'personalized_pdf': ['PB_PDF'],
                'cp_personalized': ['PB_PRINT'],
            }
            parts = _fallback.get(product_type, [])
    return parts


_COMPRA_CODE_LABELS = {
    'QS_EBOOK': 'eBook interactivo',
    'QS_PDF': 'PDF imprimible',
    'QS_PRINT': 'Libro impreso tapa blanda',
    'PB_EBOOK': 'eBook interactivo',
    'PB_PDF': 'PDF imprimible',
    'PB_PRINT': 'Libro impreso tapa dura',
}


@app.route('/admin/negocio')
def admin_negocio():
    """Admin: business control panel — real sales data from story_previews/*.json."""
    if not check_admin_auth():
        return redirect(url_for('admin_login_page'))
    import glob as _glob
    sales = []
    for fpath in _glob.glob('story_previews/*.json'):
        try:
            with open(fpath, 'r', encoding='utf-8') as _f:
                _d = json.load(_f)
            if not _d.get('paid'):
                continue
            _pid = os.path.basename(fpath).replace('.json', '')
            _cp_pb_ref = _d.get('cp_pb_order_ref', '') or ''
            _cp_qs_ref = _d.get('cp_order_ref', '') or ''
            _cp_ref = _cp_pb_ref or _cp_qs_ref
            _cp_os = _d.get('cp_order_status', '') or ''
            _cp_st = _d.get('cp_status', '') or ''
            _cp_sub = bool(_d.get('cp_submitted'))
            if _cp_os == 'delivered':
                _cp_estado = 'Entregado'
            elif _cp_os == 'shipped' or _d.get('cp_tracking_code'):
                _cp_estado = 'En tránsito'
            elif _cp_os in ('submitted',) or _cp_st == 'sent' or _cp_sub:
                _cp_estado = 'Enviado'
            elif _cp_os == 'failed':
                _cp_estado = 'Error'
            else:
                _cp_estado = ''
            _compra_codes = _build_compra_codes(_d)
            _compra_label = ' + '.join(_compra_codes) if _compra_codes else (_d.get('product_type', '') or 'desconocido')
            _compra_key = _compra_label
            sales.append({
                'preview_id': _pid,
                'amount_paid': _d.get('amount_paid') or _d.get('customer_total_usd') or None,
                'currency': _d.get('currency', 'USD') or 'USD',
                'payer_country': _d.get('payer_country', '') or _d.get('buyer_country', '') or '',
                'product_type': _d.get('product_type', '') or '',
                'payment_date': _d.get('payment_date', '') or '',
                'customer_email': _d.get('customer_email', '') or '',
                'paypal_order_id': _d.get('paypal_order_id', '') or '',
                'capture_id': _d.get('capture_id', '') or '',
                'generation_complete': bool(_d.get('generation_complete')),
                'email_sent': bool(_d.get('email_sent')),
                'cp_submitted': _cp_sub,
                'cp_ref': _cp_ref,
                'cp_estado': _cp_estado,
                'cp_tracking_code': _d.get('cp_tracking_code', '') or '',
                'cp_tracking_url': _d.get('cp_tracking_url', '') or '',
                'child_name': _d.get('child_name', '') or '',
                'story_id': _d.get('story_id', '') or '',
                'compra_codes': _compra_codes,
                'compra_label': _compra_label,
                'compra_key': _compra_key,
                'format_prices': _d.get('format_prices', {}) or {},
                'discount_amount': _d.get('discount_amount'),
                'discount_pct': _d.get('discount_pct'),
                'shipping_cost_usd': _d.get('shipping_cost_usd'),
                'coupon_code': _d.get('coupon_code', '') or '',
            })
        except Exception:
            continue
    sales.sort(key=lambda x: x['payment_date'], reverse=True)

    # Emails internos de prueba — excluidos del panel de ventas reales
    _INTERNAL_DOMAINS = ('@magicmemoriesbooks.com',)
    _is_internal = lambda em: em and any(em.strip().lower().endswith(d) for d in _INTERNAL_DOMAINS)

    # Ventas válidas = importe > 0 O paypal_order_id presente, Y email no interno
    valid_sales = [
        s for s in sales
        if ((s['amount_paid'] and s['amount_paid'] > 0) or s['paypal_order_id'])
        and not _is_internal(s['customer_email'])
    ]

    known_revenue = round(sum(s['amount_paid'] or 0 for s in valid_sales), 2)
    valid_count = len(valid_sales)

    # Países — solo de ventas válidas, sin "(desconocido)"
    _countries = {}
    for s in valid_sales:
        c = s['payer_country']
        if not c:
            continue
        if c not in _countries:
            _countries[c] = {'count': 0, 'revenue': 0.0}
        _countries[c]['count'] += 1
        _countries[c]['revenue'] += s['amount_paid'] or 0
    countries_valid_list = sorted(_countries.items(), key=lambda x: x[1]['revenue'], reverse=True)
    total_valid_countries = len(countries_valid_list)

    # Productos individuales vendidos — cada código por separado
    # Revenue: solo desde format_prices por línea (no el total del pedido)
    _ALL_CODES = ['QS_EBOOK', 'QS_PDF', 'QS_PRINT', 'PB_EBOOK', 'PB_PDF', 'PB_PRINT']
    # Mapeo código → clave en format_prices
    _CODE_TO_FP = {
        'QS_EBOOK': ('ebook',), 'PB_EBOOK': ('ebook',),
        'QS_PDF':   ('digital', 'pdf'), 'PB_PDF': ('digital', 'pdf'),
        'QS_PRINT': ('print',), 'PB_PRINT': ('print',),
    }
    _prod_units = {c: 0 for c in _ALL_CODES}
    _prod_revenue = {c: [] for c in _ALL_CODES}  # lista de precios individuales
    for s in valid_sales:
        fp = s.get('format_prices') or {}
        for code in s['compra_codes']:
            if code not in _prod_units:
                continue
            _prod_units[code] += 1
            # Buscar precio real de ese formato en format_prices
            price = None
            for fp_key in _CODE_TO_FP.get(code, ()):
                if fp_key in fp and fp[fp_key] is not None:
                    price = fp[fp_key]
                    break
            if price is not None:
                _prod_revenue[code].append(price)
    # Mostrar SIEMPRE las 6 tarjetas — se llenan con ventas conforme llegan
    products_individual = []
    for c in _ALL_CODES:
        prices = _prod_revenue[c]
        products_individual.append((c, {
            'count': _prod_units[c],
            'prices': prices,
            'has_revenue': len(prices) > 0,
            'revenue_total': sum(prices),
            'price_min': min(prices) if prices else None,
            'price_max': max(prices) if prices else None,
        }))

    # Combinaciones de compra — solo pedidos con 2+ tipos de producto juntos
    _combos = {}
    for s in valid_sales:
        if len(s['compra_codes']) < 2:
            continue  # pedido de un solo producto — no es combinación
        ck = s['compra_key'] or 'desconocido'
        if ck not in _combos:
            _combos[ck] = {'count': 0, 'revenue': 0.0, 'codes': s['compra_codes']}
        _combos[ck]['count'] += 1
        _combos[ck]['revenue'] += s['amount_paid'] or 0
    combinations_list = sorted(_combos.items(), key=lambda x: x[1]['revenue'], reverse=True)

    # Clientes — solo de ventas válidas
    _customers = {}
    for s in valid_sales:
        em = s['customer_email'] or '(sin email)'
        if em not in _customers:
            _customers[em] = {'count': 0, 'revenue': 0.0, 'last_date': '', 'last_country': '', 'purchases': []}
        _customers[em]['count'] += 1
        _customers[em]['revenue'] += s['amount_paid'] or 0
        if s['payment_date'] > _customers[em]['last_date']:
            _customers[em]['last_date'] = s['payment_date']
            _customers[em]['last_country'] = s['payer_country']
        _customers[em]['purchases'].append(s)
    customers_list = sorted(_customers.items(), key=lambda x: x[1]['revenue'], reverse=True)

    # Auditoría de cobertura — sobre ventas válidas
    with_capture = sum(1 for s in valid_sales if s['capture_id'])
    with_cp_ref = sum(1 for s in valid_sales if s['cp_ref'])

    return render_template('admin_negocio.html',
        sales=valid_sales,
        known_revenue=known_revenue,
        valid_count=valid_count,
        total_valid_countries=total_valid_countries,
        products_individual=products_individual,
        combinations_list=combinations_list,
        countries_valid_list=countries_valid_list,
        customers_list=customers_list,
        with_capture=with_capture,
        with_cp_ref=with_cp_ref,
        code_labels=_COMPRA_CODE_LABELS,
    )


@app.route('/admin/crm')
def admin_crm():
    """Admin: CRM — Historial de emails enviados."""
    if not check_admin_auth():
        return redirect(url_for('admin_login_page'))

    from services.email_service import EMAIL_LOG_FILE

    entries = []
    if os.path.exists(EMAIL_LOG_FILE):
        with open(EMAIL_LOG_FILE, 'r', encoding='utf-8') as _f:
            for line in _f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(json.loads(line))
                except Exception:
                    pass

    entries.sort(key=lambda x: x.get('ts', ''), reverse=True)

    # Filter params
    q_email    = request.args.get('email', '').strip().lower()
    q_cat      = request.args.get('cat', '').strip()
    q_pid      = request.args.get('pid', '').strip().lower()
    q_result   = request.args.get('result', '').strip()

    filtered = entries
    if q_email:
        filtered = [e for e in filtered if q_email in (e.get('to_email') or '').lower()]
    if q_cat:
        filtered = [e for e in filtered if e.get('category') == q_cat]
    if q_pid:
        filtered = [e for e in filtered if q_pid in (e.get('preview_id') or '').lower()]
    if q_result:
        filtered = [e for e in filtered if e.get('result') == q_result]

    total     = len(entries)
    sent_ct   = sum(1 for e in entries if e.get('result') == 'SENT')
    error_ct  = sum(1 for e in entries if e.get('result') == 'ERROR')
    cats      = {}
    for e in entries:
        c = e.get('category','other')
        cats[c] = cats.get(c, 0) + 1

    return render_template('admin_crm.html',
        entries=filtered,
        total=total, sent_ct=sent_ct, error_ct=error_ct,
        cats=cats,
        q_email=q_email, q_cat=q_cat, q_pid=q_pid, q_result=q_result,
    )


@app.route('/admin/crm/email-preview/<path:filename>')
def admin_crm_email_preview(filename):
    """Serve the stored HTML body of a logged email for CRM preview."""
    if not check_admin_auth():
        return redirect(url_for('admin_login_page'))
    import re
    safe = re.sub(r'[^a-zA-Z0-9_\-\.]', '', filename)
    body_path = os.path.join('data', 'email_bodies', safe)
    if not os.path.exists(body_path):
        return '<p style="font-family:sans-serif;padding:40px;color:#dc2626;">Vista previa no disponible para este email (generado antes de esta función).</p>', 404
    with open(body_path, 'r', encoding='utf-8') as _f:
        html = _f.read()
    return html, 200, {'Content-Type': 'text/html; charset=utf-8'}


@app.route('/admin/crm/clientes')
def admin_crm_clientes():
    """CRM: clientes agrupados por email. Usa payment_date del JSON, nunca mtime."""
    if not check_admin_auth():
        return redirect(url_for('admin_login_page'))
    import glob as _glob
    from datetime import datetime as _dt

    def _parse_date(s):
        if not s:
            return None
        try:
            return _dt.fromisoformat(str(s)[:19])
        except Exception:
            return None

    # Load engagement events for opened/completed badges
    _opened_ids = set()
    _completed_ids = set()
    if os.path.exists(STORY_EVENTS_FILE):
        try:
            with open(STORY_EVENTS_FILE, 'r', encoding='utf-8') as _ef:
                for _line in _ef:
                    try:
                        _ev = json.loads(_line.strip())
                        _etype = _ev.get('event_type', '')
                        _pid = _ev.get('preview_id', '')
                        if _pid:
                            if _etype == 'FIRST_STORY_OPEN':
                                _opened_ids.add(_pid)
                            elif _etype == 'STORY_COMPLETED':
                                _completed_ids.add(_pid)
                    except Exception:
                        pass
        except Exception:
            pass

    customers = {}
    for pf in _glob.glob('story_previews/*.json'):
        try:
            pid = os.path.basename(pf).replace('.json', '')
            if pid.upper().startswith('TEST_'):
                continue
            with open(pf, 'r', encoding='utf-8') as _f:
                d = json.load(_f)
            email = (d.get('customer_email') or '').strip().lower()
            if not email or '@' not in email:
                continue
            is_admin_gift = d.get('admin_gift', False) or d.get('payment_status') == 'admin_gift'
            if is_admin_gift:
                continue
            _raw_amount = d.get('amount_paid') or d.get('customer_total_usd') or 0
            is_paid = (d.get('payment_status') == 'completed' or
                       float(_raw_amount) > 0 or
                       d.get('paid', False) or
                       bool(d.get('paypal_order_id')))
            if not is_paid:
                continue
            purchase_date = _parse_date(d.get('payment_date'))
            amount = float(_raw_amount)
            child_name = d.get('child_name', '')
            story_name = d.get('story_name') or d.get('title', '')
            want_print = d.get('want_print', False)
            want_pdf = d.get('want_pdf', False) or d.get('pdf_paid', False)
            ebook_paid = d.get('ebook_paid', False) or d.get('want_ebook', False)
            if email not in customers:
                customers[email] = {
                    'email': email,
                    'stories': [],
                    'total_amount': 0.0,
                    'first_date': purchase_date,
                    'last_date': purchase_date,
                }
            c = customers[email]
            c['stories'].append({
                'preview_id': pid,
                'child_name': child_name,
                'story_name': story_name,
                'amount': amount,
                'date': purchase_date,
                'want_print': want_print,
                'want_pdf': want_pdf,
                'ebook_paid': ebook_paid,
                'opened': pid in _opened_ids,
                'completed': pid in _completed_ids,
            })
            c['total_amount'] += amount
            if purchase_date:
                if c['first_date'] is None or purchase_date < c['first_date']:
                    c['first_date'] = purchase_date
                if c['last_date'] is None or purchase_date > c['last_date']:
                    c['last_date'] = purchase_date
        except Exception:
            pass

    def _sort_key(x):
        return x['last_date'] or _dt.min

    customers_list = sorted(customers.values(), key=_sort_key, reverse=True)
    for c in customers_list:
        c['num_stories'] = len(c['stories'])
        c['total_amount'] = round(c['total_amount'], 2)
        c['first_date_str'] = c['first_date'].strftime('%d %b %Y') if c['first_date'] else 'desconocida'
        c['last_date_str'] = c['last_date'].strftime('%d %b %Y') if c['last_date'] else 'desconocida'
    return render_template('admin_crm_clientes.html', customers=customers_list, total=len(customers_list))


@app.route('/admin/crm/timeline/<path:email>')
def admin_crm_timeline(email):
    """CRM: timeline de eventos para un cliente. Usa payment_date del JSON; nunca mtime."""
    if not check_admin_auth():
        return redirect(url_for('admin_login_page'))
    import glob as _glob
    from datetime import datetime as _dt
    from services.email_service import EMAIL_LOG_FILE
    email = email.strip().lower()

    def _parse_date(s):
        if not s:
            return None
        try:
            return _dt.fromisoformat(str(s)[:19])
        except Exception:
            return None

    _EPOCH = _dt(2020, 1, 1)  # sentinel for unknown-date events

    events = []

    # ── 1. Story JSON events ──────────────────────────────────────────────────
    for pf in _glob.glob('story_previews/*.json'):
        try:
            pid = os.path.basename(pf).replace('.json', '')
            if pid.upper().startswith('TEST_'):
                continue
            with open(pf, 'r', encoding='utf-8') as _f:
                d = json.load(_f)
            if (d.get('customer_email') or '').strip().lower() != email:
                continue
            if d.get('admin_gift', False) or d.get('payment_status') == 'admin_gift':
                continue
            purchase_date = _parse_date(d.get('payment_date'))
            has_date = purchase_date is not None
            _ts = purchase_date or _EPOCH
            child_name = d.get('child_name', '')
            story_name = d.get('story_name') or d.get('title', '')
            amount = float(d.get('amount_paid') or d.get('customer_total_usd') or 0)
            fp = d.get('format_prices') or {}
            # Determine formats purchased
            ebook_amt = float(fp.get('ebook', 0) or 0)
            pdf_amt   = float(fp.get('digital', 0) or fp.get('pdf', 0) or 0)
            print_amt = float(fp.get('print', 0) or 0)
            has_ebook = bool(d.get('ebook_paid') or d.get('want_ebook') or ebook_amt > 0)
            has_pdf   = bool(d.get('want_pdf') or d.get('pdf_paid') or pdf_amt > 0)
            has_print = bool(d.get('want_print') or print_amt > 0)

            label_title = story_name or (f'Cuento de {child_name}' if child_name else pid[:8])

            # Compra inicial
            events.append({
                'ts': _ts, 'icon': '💳',
                'label': f'Compra: {label_title}',
                'detail': '', 'preview_id': pid,
                'approx': not has_date, 'result': '',
            })
            # Ingreso total
            if amount > 0:
                events.append({
                    'ts': _ts, 'icon': '💵',
                    'label': f'Ingreso: ${amount:.2f} USD',
                    'detail': '', 'preview_id': pid,
                    'approx': not has_date, 'result': '',
                })
            # Formato eBook entregado
            if has_ebook:
                _ebook_detail = f'${ebook_amt:.2f}' if ebook_amt > 0 else ''
                events.append({
                    'ts': _ts, 'icon': '📱',
                    'label': 'eBook entregado',
                    'detail': _ebook_detail, 'preview_id': pid,
                    'approx': not has_date, 'result': '',
                })
            # Venta adicional PDF
            if has_pdf:
                events.append({
                    'ts': _ts, 'icon': '🛒',
                    'label': 'PDF comprado',
                    'detail': f'${pdf_amt:.2f}' if pdf_amt > 0 else '', 'preview_id': pid,
                    'approx': not has_date, 'result': '',
                })
            # Venta adicional impreso + envío a imprenta
            if has_print:
                events.append({
                    'ts': _ts, 'icon': '🛒',
                    'label': 'Libro impreso comprado',
                    'detail': f'${print_amt:.2f}' if print_amt > 0 else '', 'preview_id': pid,
                    'approx': not has_date, 'result': '',
                })
            if d.get('cp_submitted'):
                _cp_ts = _parse_date(d.get('cp_submitted_at')) or _ts
                events.append({
                    'ts': _cp_ts, 'icon': '📦',
                    'label': 'Pedido enviado a imprenta',
                    'detail': d.get('cp_order_id', '') or d.get('cp_pb_order_id', ''),
                    'preview_id': pid, 'approx': not has_date, 'result': '',
                })
            if d.get('cp_tracking_code') or d.get('cp_tracking'):
                events.append({
                    'ts': _ts, 'icon': '🚚',
                    'label': 'Tracking recibido',
                    'detail': d.get('cp_tracking_code') or str(d.get('cp_tracking', '')),
                    'preview_id': pid, 'approx': not has_date, 'result': '',
                })
        except Exception:
            pass

    # ── 2. Email log events (fechas exactas) ─────────────────────────────────
    _icon_cat = {'delivery': '📧', 'followup': '💌', 'retention': '🔁', 'admin': '🔧'}
    if os.path.exists(EMAIL_LOG_FILE):
        with open(EMAIL_LOG_FILE, 'r', encoding='utf-8') as _ef:
            for line in _ef:
                line = line.strip()
                if not line:
                    continue
                try:
                    e = json.loads(line)
                    if (e.get('to_email') or '').strip().lower() != email:
                        continue
                    ts_str = (e.get('ts') or '')[:19]
                    if not ts_str:
                        continue
                    ts = _dt.fromisoformat(ts_str)
                    label = e.get('label') or e.get('email_type', '')
                    events.append({
                        'ts': ts, 'icon': _icon_cat.get(e.get('category', ''), '📧'),
                        'label': f'Email: {label}',
                        'detail': e.get('subject', ''),
                        'preview_id': e.get('preview_id', ''),
                        'approx': False, 'result': e.get('result', ''),
                    })
                except Exception:
                    pass

    # ── 3. Visor engagement events (FIRST_STORY_OPEN, STORY_COMPLETED) ─────────
    _story_event_icons = {
        'FIRST_STORY_OPEN': ('👀', 'Primera apertura del cuento'),
        'STORY_COMPLETED':  ('📚', 'Cuento completado'),
    }
    if os.path.exists(STORY_EVENTS_FILE):
        with open(STORY_EVENTS_FILE, 'r', encoding='utf-8') as _sf:
            for line in _sf:
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                    if (ev.get('customer_email') or '').strip().lower() != email:
                        continue
                    _ev_type = ev.get('event_type', '')
                    if _ev_type not in _story_event_icons:
                        continue
                    _icon, _label = _story_event_icons[_ev_type]
                    ts = _dt.fromisoformat(ev['ts'][:19])
                    events.append({
                        'ts': ts, 'icon': _icon,
                        'label': _label,
                        'detail': '',
                        'preview_id': ev.get('preview_id', ''),
                        'approx': False, 'result': '',
                    })
                except Exception:
                    pass

    # ── 4. PreviewLead events (lead activity before purchase) ────────────────
    _pl_records = PreviewLead.query.filter(
        db.func.lower(PreviewLead.email) == email
    ).order_by(PreviewLead.created_at).all()
    for _lr in _pl_records:
        if _lr.created_at:
            events.append({
                'ts': _lr.created_at, 'icon': '🎨',
                'label': f'Preview generada: {_lr.story_id or "cuento"}',
                'detail': '', 'preview_id': '',
                'approx': False, 'result': 'LEAD',
            })

    # ── 5. Photo upload events ────────────────────────────────────────────────
    _ph_logs = PhotoUploadLog.query.filter(
        db.func.lower(PhotoUploadLog.email) == email
    ).order_by(PhotoUploadLog.uploaded_at).all()
    _ptype_map = {'human': 'humana', 'pet': 'mascota', 'child': 'niño'}
    for _pl2 in _ph_logs:
        if _pl2.uploaded_at:
            _ptype_lbl = _ptype_map.get(_pl2.photo_type or '', _pl2.photo_type or '')
            events.append({
                'ts': _pl2.uploaded_at, 'icon': '📸',
                'label': f'Subió foto ({_ptype_lbl})',
                'detail': _pl2.story_id or '',
                'preview_id': _pl2.preview_id or '',
                'approx': False,
                'result': 'DELETED' if _pl2.deleted_at else '',
            })

    # ── 6. Regen exhausted events (from lead JSONs matched by story_id) ───────
    if _pl_records:
        _lead_sids = {lr.story_id for lr in _pl_records if lr.story_id}
        _first_visit_ts = min(
            (lr.created_at.timestamp() for lr in _pl_records if lr.created_at), default=0
        )
        for _pf2 in _glob.glob('story_previews/*.json'):
            try:
                _pid2 = os.path.basename(_pf2).replace('.json', '')
                _jd2 = json.load(open(_pf2))
                _jem2 = (_jd2.get('customer_email') or '').strip().lower()
                _js2 = _jd2.get('story_id', '')
                _ct2 = os.path.getctime(_pf2)
                _match = (_jem2 == email) or (
                    _js2 in _lead_sids and abs(_ct2 - _first_visit_ts) < 86400 * 14
                )
                if not _match:
                    continue
                # Pre-payment preview regeneration
                if _jd2.get('regeneration_used'):
                    events.append({
                        'ts': _dt.utcfromtimestamp(_ct2), 'icon': '🔄',
                        'label': 'Usó regeneración de preview',
                        'detail': '', 'preview_id': _pid2, 'approx': True, 'result': '',
                    })
                # Post-payment scene regens (Quick Stories)
                for _sk, _sv in (_jd2.get('scene_regenerations') or {}).items():
                    if int(_sv) >= 2:
                        events.append({
                            'ts': _EPOCH, 'icon': '🔄',
                            'label': f'Agotó intentos: escena {_sk}',
                            'detail': f'{_sv} regeneraciones (límite 2)',
                            'preview_id': _pid2, 'approx': True, 'result': '',
                        })
                # Post-payment page regens (Illustrated books)
                for _pk, _pv in (_jd2.get('page_regenerations') or {}).items():
                    if int(_pv) >= 2:
                        events.append({
                            'ts': _EPOCH, 'icon': '🔄',
                            'label': f'Agotó intentos: página {_pk}',
                            'detail': f'{_pv} regeneraciones (límite 2)',
                            'preview_id': _pid2, 'approx': True, 'result': '',
                        })
            except Exception:
                pass

    back_from = request.args.get('from', 'clientes')
    events.sort(key=lambda x: x['ts'])
    for ev in events:
        _d = ev['ts']
        if _d == _EPOCH:
            ev['ts_str'] = 'Fecha desconocida'
        else:
            ev['ts_str'] = _d.strftime('%d %b %Y   %H:%M')
    return render_template('admin_crm_timeline.html', email=email, events=events, back_from=back_from)


@app.route('/admin/crm/leads')
def admin_crm_leads():
    """CRM: Leads — agrupados por email, excluye compradores."""
    if not check_admin_auth():
        return redirect(url_for('admin_login_page'))
    import glob as _glob
    from collections import Counter as _Counter

    # Build buyer set
    buyer_emails = set()
    for pf in _glob.glob('story_previews/*.json'):
        try:
            pid = os.path.basename(pf).replace('.json', '')
            if pid.upper().startswith('TEST_'):
                continue
            with open(pf, 'r', encoding='utf-8') as _f:
                d = json.load(_f)
            if d.get('admin_gift') or d.get('payment_status') == 'admin_gift':
                continue
            _amt = float(d.get('amount_paid') or d.get('customer_total_usd') or 0)
            is_paid = (d.get('payment_status') == 'completed' or _amt > 0
                       or d.get('paid', False) or bool(d.get('paypal_order_id')))
            if is_paid:
                em = (d.get('customer_email') or '').strip().lower()
                if em:
                    buyer_emails.add(em)
        except Exception:
            pass

    # Load all leads from DB
    total_leads_db = PreviewLead.query.count()
    leads_all = PreviewLead.query.order_by(PreviewLead.created_at.desc()).limit(1000).all()

    # Group by email, exclude buyers
    _grouped = {}
    for lead in leads_all:
        em = (lead.email or '').strip().lower()
        if not em or em in buyer_emails:
            continue
        if em not in _grouped:
            _grouped[em] = {'email': em, 'previews': [], 'ips': [],
                            'first_visit': None, 'last_visit': None}
        g = _grouped[em]
        g['previews'].append(lead)
        if lead.ip_address:
            g['ips'].append(lead.ip_address)
        if lead.created_at:
            if g['first_visit'] is None or lead.created_at < g['first_visit']:
                g['first_visit'] = lead.created_at
            if g['last_visit'] is None or lead.created_at > g['last_visit']:
                g['last_visit'] = lead.created_at

    # ── Enrich from story_previews JSONs ──────────────────────────────
    # Many lead JSONs have no customer_email (email only in DB).
    # Strategy: index by email (when present) AND by story_id (for fallback match).
    _json_by_email = {}   # email → [info, ...]
    _json_by_sid = {}     # story_id → [info, ...]
    for _pf in _glob.glob('story_previews/*.json'):
        try:
            _pid = os.path.basename(_pf).replace('.json', '')
            if _pid.upper().startswith('TEST_'):
                continue
            with open(_pf, 'r', encoding='utf-8') as _jf:
                _jd = json.load(_jf)
            # Skip paid / buyer stories
            _jamt = float(_jd.get('amount_paid') or _jd.get('customer_total_usd') or 0)
            _jpaid = (_jd.get('payment_status') == 'completed' or _jamt > 0
                      or _jd.get('paid') or bool(_jd.get('paypal_order_id')))
            _jem = (_jd.get('customer_email') or '').strip().lower()
            if _jpaid and not _jd.get('admin_gift'):
                continue
            if _jem and _jem in buyer_emails:
                continue
            _jstory = _jd.get('story_id', '')
            _ctime = os.path.getctime(_pf)
            _jdate = datetime.fromtimestamp(_ctime).strftime('%Y-%m-%d')
            _info = {
                'preview_id': _pid,
                'child_name': (_jd.get('child_name') or '').strip(),
                'story_id': _jstory,
                'date_str': _jdate,
                'ctime': _ctime,
            }
            # Index by email if present
            if _jem and _jem not in buyer_emails:
                _json_by_email.setdefault(_jem, []).append(_info)
            # Always index by story_id for fallback
            if _jstory:
                _json_by_sid.setdefault(_jstory, []).append(_info)
        except Exception:
            pass

    # Build photo-upload email set for badge
    _photo_emails = set()
    try:
        for _pe in PhotoUploadLog.query.with_entities(PhotoUploadLog.email).distinct().all():
            if _pe.email:
                _photo_emails.add(_pe.email.strip().lower())
    except Exception:
        pass

    # Build display list sorted by last_visit desc
    leads_grouped = []
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_count = 0
    for em, g in sorted(_grouped.items(),
                        key=lambda x: x[1]['last_visit'] or datetime.min, reverse=True):
        ip_counter = _Counter(g['ips'])
        main_ip = ip_counter.most_common(1)[0][0] if ip_counter else '—'
        story_ids = []
        for _lead in g['previews']:
            if _lead.story_id and _lead.story_id not in story_ids:
                story_ids.append(_lead.story_id)
        lv = g['last_visit']
        if lv and lv >= today_start:
            today_count += 1
        # Merge JSON enrichment — email first, fallback to story_id + timestamp proximity
        _json_cuentos = []
        if em in _json_by_email:
            # Email found in JSON: use directly
            _json_cuentos = sorted(_json_by_email[em], key=lambda x: x['ctime'], reverse=True)
        else:
            # No email in JSON — match each story_id by closest ctime to DB lead timestamp
            _fv_ts = g['first_visit'].timestamp() if g['first_visit'] else 0
            _seen_pids = set()
            for _sid in story_ids:
                _candidates = _json_by_sid.get(_sid, [])
                if not _candidates:
                    continue
                # Pick candidate with ctime closest to first_visit
                _best = min(_candidates, key=lambda x: abs(x['ctime'] - _fv_ts))
                if _best['preview_id'] not in _seen_pids:
                    _seen_pids.add(_best['preview_id'])
                    _json_cuentos.append(_best)
        leads_grouped.append({
            'email': em,
            'num_previews': len(g['previews']),
            'story_ids': story_ids,
            'first_visit_str': g['first_visit'].strftime('%d %b %Y') if g['first_visit'] else '—',
            'last_visit_str': lv.strftime('%d %b %Y') if lv else '—',
            'main_ip': main_ip,
            'cuentos': _json_cuentos,  # enriched: preview_id, child_name, story_id, date_str
            'has_photo': em in _photo_emails,
        })

    return render_template('admin_crm_leads.html',
        leads_grouped=leads_grouped,
        total_leads_db=total_leads_db,
        unique_emails=len(leads_grouped),
        today_leads=today_count,
        buyer_count=len(buyer_emails),
    )


@app.route('/admin/retry-scenes/<preview_id>', methods=['POST'])
def admin_retry_scenes(preview_id):
    if not check_admin_auth():
        return redirect(url_for('admin_login_page'))
    
    preview_file = f'story_previews/{preview_id}.json'
    if not os.path.exists(preview_file):
        return "Preview not found", 404
    
    with open(preview_file, 'r', encoding='utf-8') as f:
        story_data = json.load(f)
    
    failed_scenes = story_data.get('failed_scenes', [])
    if not failed_scenes:
        return redirect(url_for('admin_pending_retries'))
    
    story_data['retry_count'] = max(0, story_data.get('retry_count', 0) - 1)
    story_data['scenes_retrying'] = True
    story_data['retry_exhausted'] = False
    with open(preview_file, 'w', encoding='utf-8') as f:
        json.dump(story_data, f, ensure_ascii=False, indent=2)
    
    retry_thread = threading.Thread(target=_retry_failed_scenes_background, args=(preview_id,), daemon=True)
    retry_thread.start()
    
    production_logger.info(f"[ADMIN] Manual retry triggered for {preview_id}")
    return redirect(url_for('admin_pending_retries'))


# ============================================================
# ADMIN: GIFT BOOK GENERATOR (Feb 2026)
# ============================================================

@app.route('/admin/gift-book')
def admin_gift_book():
    """Admin page to generate books for free (influencer collaborations, gifts)."""
    if not check_admin_auth():
        return redirect(url_for('admin_login_page'))
    
    import glob as glob_mod
    gift_previews = []
    preview_files = glob_mod.glob('story_previews/*.json')
    for pf in sorted(preview_files, key=os.path.getmtime, reverse=True):
        try:
            with open(pf, 'r') as f:
                data = json.load(f)
            if data.get('admin_gift'):
                pid = os.path.basename(pf).replace('.json', '')
                gift_previews.append({
                    'preview_id': pid,
                    'child_name': data.get('child_name', 'Unknown'),
                    'story_id': data.get('story_id', ''),
                    'scenes_generating': data.get('scenes_generating', False),
                    'book_scenes_ready': data.get('book_scenes_ready', False),
                    'pages_composed': data.get('pages_composed', False),
                    'has_pdf_access': (
                        (bool(data.get('lulu_order_folder')) and os.path.exists(data.get('lulu_order_folder', '')))
                        or data.get('book_scenes_ready', False)
                        or data.get('pages_composed', False)
                        or data.get('cp_pdfs_ready', False)
                    ),
                    'created': datetime.fromtimestamp(os.path.getmtime(pf)).strftime('%Y-%m-%d %H:%M'),
                })
        except:
            pass
    
    return render_template('admin_gift_book.html', gift_previews=gift_previews[:20])


@app.route('/admin/generate-free/<preview_id>', methods=['POST'])
def admin_generate_free(preview_id):
    """Admin-only: trigger scene generation for a gift book (no payment needed)."""
    if not check_admin_auth():
        return jsonify({'success': False, 'error': 'Not authorized'}), 403
    
    preview_file = f'story_previews/{preview_id}.json'
    if not os.path.exists(preview_file):
        return jsonify({'success': False, 'error': 'Preview not found'}), 404
    
    data = request.get_json(silent=True) or {}
    admin_email = data.get('admin_email', '').strip()
    
    with open(preview_file, 'r', encoding='utf-8') as f:
        story_data = json.load(f)
    
    story_data['admin_gift'] = True
    story_data['paid'] = True
    story_data['payment_status'] = 'admin_gift'
    story_data['payment_date'] = datetime.now().isoformat()
    story_data['generation_complete'] = True
    story_data['scenes_pending'] = True
    story_data['want_print'] = True
    if admin_email:
        story_data['admin_gift_email'] = admin_email
        story_data['customer_email'] = admin_email
    
    with open(preview_file, 'w', encoding='utf-8') as f:
        json.dump(story_data, f, ensure_ascii=False, indent=2)
    
    print(f"[ADMIN-GIFT] Triggering free generation for {preview_id} (email: {admin_email})")
    _trigger_background_generation(preview_id)
    
    return jsonify({'success': True, 'redirect_url': f'/order-complete/{preview_id}'})


@app.route('/admin/gift-download/<preview_id>')
def admin_gift_download(preview_id):
    """Admin page to download Lulu PDFs for a gift book."""
    if not check_admin_auth():
        return redirect(url_for('admin_login_page'))
    
    preview_file = f'story_previews/{preview_id}.json'
    if not os.path.exists(preview_file):
        return "Book not found", 404
    
    with open(preview_file, 'r', encoding='utf-8') as f:
        story_data = json.load(f)
    
    lulu_folder = story_data.get('lulu_order_folder', '')
    folder_name = os.path.basename(lulu_folder) if lulu_folder else ''
    interior_exists = bool(lulu_folder) and os.path.exists(os.path.join(lulu_folder, 'interior.pdf'))
    cover_exists = bool(lulu_folder) and os.path.exists(os.path.join(lulu_folder, 'cover.pdf'))
    
    return render_template('admin_gift_download.html',
                          story_data=story_data,
                          preview_id=preview_id,
                          folder_name=folder_name,
                          interior_exists=interior_exists,
                          cover_exists=cover_exists)


@app.route('/admin/pb-files/<folder_name>/<filename>')
def admin_pb_files(folder_name, filename):
    """Serve PB (personalized book) PDF files for admin download."""
    if not check_admin_auth():
        return "Unauthorized", 401
    if filename not in ('interior.pdf', 'cover.pdf'):
        return "Not found", 404
    folder_path = os.path.join('generations', 'pb_orders', folder_name)
    file_path = os.path.join(folder_path, filename)
    if not os.path.exists(file_path):
        return "File not found", 404
    return send_file(os.path.abspath(file_path), mimetype='application/pdf',
                     as_attachment=True, download_name=filename)


# ============================================================
# ADMIN: REAL STORIES QUALITY CONTROL PANEL (Feb 2026)
# ============================================================

@app.route('/admin/rescue-order/<preview_id>')
def admin_rescue_order(preview_id):
    """Admin rescue page for failed Lulu orders - shows full book, address, error, retry."""
    if not check_admin_auth():
        return redirect(url_for('admin_login_page'))
    
    preview_file = f'story_previews/{preview_id}.json'
    if not os.path.exists(preview_file):
        return "Pedido no encontrado", 404
    
    with open(preview_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    scenes = data.get('scenes', [])
    pages = data.get('pages', [])
    shipping_address = data.get('shipping_address', {})
    lulu_error = data.get('lulu_error', '')
    lulu_status = data.get('lulu_status', '')
    cp_error = data.get('cp_error', '')
    cp_status = data.get('cp_status', '')
    lulu_order_folder = data.get('lulu_order_folder', '')
    
    lulu_folder_name = ''
    interior_exists = False
    cover_pdf_exists = False
    interior_size_mb = 0
    if lulu_order_folder and os.path.exists(lulu_order_folder):
        lulu_folder_name = os.path.basename(lulu_order_folder)
        interior_path = os.path.join(lulu_order_folder, 'interior.pdf')
        interior_exists = os.path.exists(interior_path)
        cover_pdf_exists = os.path.exists(os.path.join(lulu_order_folder, 'cover.pdf'))
        if interior_exists:
            interior_size_mb = round(os.path.getsize(interior_path) / 1024 / 1024, 1)
    
    return render_template('admin_rescue_order.html',
                          preview_id=preview_id,
                          book=data,
                          scenes=scenes,
                          pages=pages,
                          shipping_address=shipping_address,
                          lulu_error=lulu_error,
                          lulu_status=lulu_status,
                          cp_error=cp_error,
                          cp_status=cp_status,
                          lulu_folder_name=lulu_folder_name,
                          interior_exists=interior_exists,
                          cover_pdf_exists=cover_pdf_exists,
                          interior_size_mb=interior_size_mb)


@app.route('/admin/delete-preview/<preview_id>', methods=['POST'])
def admin_delete_preview(preview_id):
    """Delete a story preview and its files.
    If the story has a committed eBook (paid + visor_url), the visor is preserved
    automatically so the customer keeps access. Only the heavy source files are removed.
    """
    if not check_admin_auth():
        return jsonify({'success': False, 'error': 'Not authorized'}), 403

    preview_file = f'story_previews/{preview_id}.json'
    if not os.path.exists(preview_file):
        return jsonify({'success': False, 'error': 'Not found'}), 404

    try:
        with open(preview_file, 'r') as f:
            data = json.load(f)

        has_committed_ebook = _has_committed_ebook(data)

        try:
            StoryBackup.query.filter_by(preview_id=preview_id).delete()
            db.session.commit()
            print(f"[ADMIN-DELETE] Removed {preview_id} from story_backups DB")
        except Exception as db_err:
            db.session.rollback()
            print(f"[ADMIN-DELETE] DB cleanup failed for {preview_id}: {db_err}")

        if has_committed_ebook:
            _purge_story_files(preview_id, data, include_lulu=True, skip_visor=True)
            data['story_files_deleted'] = True
            data['cp_dismissed'] = True  # hide from failed-orders panel on next load
            with open(preview_file, 'w') as f:
                json.dump(data, f, ensure_ascii=False)
            print(f"[ADMIN-DELETE] {preview_id}: archivos liberados, eBook preservado")
            return jsonify({'success': True, 'ebook_preserved': True,
                            'message': 'Archivos liberados. El eBook del cliente fue preservado.'})
        else:
            _purge_story_files(preview_id, data, include_lulu=True, skip_visor=False)
            os.remove(preview_file)
            print(f"[ADMIN-DELETE] {preview_id}: eliminado completamente")
            return jsonify({'success': True, 'ebook_preserved': False})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/admin/delete-story-keep-ebook/<preview_id>', methods=['POST'])
def admin_delete_story_keep_ebook(preview_id):
    """Delete story files (scenes, photos, PDFs) but preserve visor/eBook directory."""
    if not check_admin_auth():
        return jsonify({'success': False, 'error': 'Not authorized'}), 403
    preview_file = f'story_previews/{preview_id}.json'
    if not os.path.exists(preview_file):
        return jsonify({'success': False, 'error': 'Not found'}), 404
    try:
        with open(preview_file, 'r') as f:
            data = json.load(f)
        _purge_story_files(preview_id, data, include_lulu=True, skip_visor=True)
        try:
            data['story_files_deleted'] = True
            data['story_files_deleted_at'] = datetime.utcnow().isoformat()
            with open(preview_file, 'w') as f:
                json.dump(data, f)
            try:
                import stat
                os.chmod(preview_file, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH)
            except Exception:
                pass
        except Exception as flag_err:
            print(f"[LIBERAR] Warning: no se pudo marcar {preview_id} como liberado: {flag_err}")
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/admin/ebook-library')
def admin_ebook_library():
    """Admin page listing all delivered eBooks (permanent and 6-month)."""
    if not check_admin_auth():
        return redirect(url_for('admin_login_page'))
    ebooks = []
    try:
        for fname in sorted(os.listdir('story_previews'), reverse=True):
            if not fname.endswith('.json'):
                continue
            preview_id = fname[:-5]
            path = f'story_previews/{fname}'
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
            except Exception:
                continue
            has_visor = bool(data.get('visor_url'))
            is_ebook = (data.get('ebook_email_sent') or data.get('want_ebook')
                        or (data.get('paid') and has_visor))
            if not is_ebook:
                continue
            expires_at = data.get('ebook_expires_at')
            is_permanent = (expires_at is None)
            is_gift = bool(data.get('admin_gift') or data.get('payment_status') == 'admin_gift')
            days_remaining = None
            expires_at_display = None
            if expires_at:
                try:
                    exp_dt = datetime.fromisoformat(expires_at)
                    days_remaining = (exp_dt - datetime.utcnow()).days
                    expires_at_display = exp_dt.strftime('%d/%m/%Y')
                except Exception:
                    pass
            payment_date_raw = data.get('payment_date', '')
            payment_date_display = ''
            if payment_date_raw:
                try:
                    pd_dt = datetime.fromisoformat(payment_date_raw.replace('Z', '').replace('+00:00', ''))
                    payment_date_display = pd_dt.strftime('%d/%m/%Y')
                except Exception:
                    payment_date_display = payment_date_raw[:10]
            visor_qs = os.path.exists(f'generations/visor_qs/{preview_id}')
            visor_pb = os.path.exists(f'generations/visor_pb/{preview_id}')
            visor_exists = visor_qs or visor_pb
            story_files_deleted = data.get('story_files_deleted', False)
            ebooks.append({
                'preview_id': preview_id,
                'child_name': data.get('child_name', 'Unknown'),
                'story_id': data.get('story_id', ''),
                'is_permanent': is_permanent,
                'is_gift': is_gift,
                'expires_at': expires_at,
                'expires_at_display': expires_at_display,
                'days_remaining': days_remaining,
                'expiry_warning_sent': data.get('expiry_warning_sent', False),
                'visor_url': data.get('visor_url', ''),
                'visor_exists': visor_exists,
                'story_files_deleted': story_files_deleted,
                'payment_date': payment_date_display,
                'customer_email': data.get('customer_email', data.get('buyer_email', '')),
            })
    except Exception as e:
        print(f"[EBOOK-LIBRARY] Error: {e}")
    return render_template('admin_ebook_library.html', ebooks=ebooks)


@app.route('/admin/personalized-books/<preview_id>')
def admin_personalized_book_detail(preview_id):
    """Admin detail view for a personalized book with scene grid."""
    if not check_admin_auth():
        return redirect(url_for('admin_login_page'))
    
    preview_file = f'story_previews/{preview_id}.json'
    if not os.path.exists(preview_file):
        return "Book not found", 404
    
    with open(preview_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    scenes = data.get('scenes', [])
    
    return render_template('admin_personalized_book_detail.html', 
                          preview_id=preview_id,
                          book=data,
                          scenes=scenes)


@app.route('/admin/newsletter')
def admin_newsletter():
    if not check_admin_auth():
        return redirect(url_for('admin_login_page'))
    subscribers = NewsletterSubscriber.query.order_by(NewsletterSubscriber.subscribed_at.desc()).all()
    active_count = sum(1 for s in subscribers if s.is_active)
    return render_template('admin_newsletter.html', subscribers=subscribers, active_count=active_count)


@app.route('/admin/coupons', methods=['GET', 'POST'])
def admin_coupons():
    if not check_admin_auth():
        return redirect(url_for('admin_login_page'))
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'create':
            code = request.form.get('code', '').strip().upper()
            coupon_type = request.form.get('coupon_type', 'general')
            discount_pct = int(request.form.get('discount_pct', 20))
            owner_name = request.form.get('owner_name', '').strip()
            owner_email = request.form.get('owner_email', '').strip()
            commission_pct = int(request.form.get('commission_pct', 0))
            max_uses = int(request.form.get('max_uses', 0))
            if code and not Coupon.query.filter_by(code=code).first():
                c = Coupon(code=code, coupon_type=coupon_type, discount_pct=discount_pct,
                           owner_name=owner_name, owner_email=owner_email,
                           commission_pct=commission_pct, max_uses=max_uses)
                db.session.add(c)
                db.session.commit()
        elif action == 'toggle':
            coupon_id = int(request.form.get('coupon_id', 0))
            c = Coupon.query.get(coupon_id)
            if c:
                c.is_active = not c.is_active
                db.session.commit()
        return redirect(url_for('admin_coupons'))
    coupons = Coupon.query.order_by(Coupon.created_at.desc()).all()
    leads = CouponLead.query.order_by(CouponLead.created_at.desc()).limit(50).all()
    usages = CouponUsage.query.order_by(CouponUsage.created_at.desc()).limit(50).all()
    return render_template('admin_coupons.html', coupons=coupons, leads=leads, usages=usages)


@app.route('/admin/newsletter/send', methods=['POST'])
def admin_newsletter_send():
    if not check_admin_auth():
        return jsonify({'success': False}), 403
    subject = request.form.get('subject', '').strip()
    content = request.form.get('content', '').strip()
    target_lang = request.form.get('language', 'all')
    if not subject or not content:
        return redirect(url_for('admin_newsletter'))

    query = NewsletterSubscriber.query.filter_by(is_active=True)
    if target_lang in ('es', 'en'):
        query = query.filter_by(language=target_lang)
    recipients = query.all()

    from services.email_service import send_newsletter_blast
    sent = 0
    for sub in recipients:
        try:
            send_newsletter_blast(sub.email, subject, content, sub.unsubscribe_token, sub.language)
            sent += 1
        except Exception as e:
            print(f"[NEWSLETTER] Failed to send to {sub.email}: {e}")

    flash(f"Correo enviado a {sent} suscriptores." if sent > 0 else "No se envió ningún correo.", "info")
    return redirect(url_for('admin_newsletter'))


@app.route('/admin/preview-leads')
def admin_preview_leads():
    return redirect('/admin/crm/leads', 301)


@app.route('/admin/preview-leads/csv')
def admin_preview_leads_csv():
    if not check_admin_auth():
        return redirect(url_for('admin_login_page'))
    import csv
    import io
    leads = PreviewLead.query.order_by(PreviewLead.created_at.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Email', 'IP', 'Story ID', 'Date'])
    for lead in leads:
        writer.writerow([lead.email, lead.ip_address or '', lead.story_id or '', lead.created_at.strftime('%Y-%m-%d %H:%M') if lead.created_at else ''])
    output.seek(0)
    from flask import Response
    return Response(output.getvalue(), mimetype='text/csv', headers={'Content-Disposition': 'attachment;filename=preview_leads.csv'})


@app.route('/admin/preview-leads/delete/<int:lead_id>', methods=['POST'])
def admin_delete_preview_lead(lead_id):
    if not check_admin_auth():
        return redirect(url_for('admin_login_page'))
    lead = PreviewLead.query.get(lead_id)
    if lead:
        db.session.delete(lead)
        db.session.commit()
    return redirect('/admin/crm/leads')


@app.route('/admin/preview-leads/delete-all', methods=['POST'])
def admin_delete_all_preview_leads():
    if not check_admin_auth():
        return redirect(url_for('admin_login_page'))
    PreviewLead.query.delete()
    db.session.commit()
    return redirect('/admin/crm/leads')


@app.route('/admin/uploaded-photos')
def admin_uploaded_photos():
    """Admin page to view and manage uploaded user photos (72h retention) + permanent log."""
    if not check_admin_auth():
        return redirect(url_for('admin_login_page'))
    
    import glob as glob_module
    import json as _json_mod

    # Active files on disk
    photos = []
    upload_dir = 'generated/uploads/furry_photos'
    active_files = set()
    if os.path.exists(upload_dir):
        for filepath in sorted(glob_module.glob(os.path.join(upload_dir, '*')), key=os.path.getmtime, reverse=True):
            if os.path.isfile(filepath):
                stat = os.stat(filepath)
                upload_time = datetime.fromtimestamp(stat.st_mtime)
                age_hours = (datetime.now() - upload_time).total_seconds() / 3600
                hours_remaining = max(0, 72 - age_hours)
                fn = os.path.basename(filepath)
                active_files.add(fn)
                photos.append({
                    'filename': fn,
                    'upload_time': upload_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'age_hours': round(age_hours, 1),
                    'hours_remaining': round(hours_remaining, 1),
                    'size_kb': round(stat.st_size / 1024, 1),
                    'expired': hours_remaining <= 0
                })

    total_photos = len(photos)
    expired_count = sum(1 for p in photos if p['expired'])

    # Build cross-reference map: filename → {email, child_name, preview_id} from story JSONs
    _json_photo_map = {}
    for _pf in glob_module.glob('story_previews/*.json'):
        try:
            _pid = os.path.basename(_pf).replace('.json', '')
            _jd = _json_mod.load(open(_pf))
            _jem = (_jd.get('customer_email') or '').strip()
            _jcn = (_jd.get('child_name') or '').strip()
            _traits = _jd.get('traits') or {}
            for _pk in ('human_photo_path', 'pet_photo_path', 'child_photo_path'):
                _pp = _jd.get(_pk) or _traits.get(_pk, '')
                if _pp:
                    _fn2 = os.path.basename(_pp)
                    if _fn2 and _fn2 not in _json_photo_map:
                        _json_photo_map[_fn2] = {
                            'email': _jem, 'child_name': _jcn, 'preview_id': _pid
                        }
        except Exception:
            pass

    # Persist enrichment into DB for new matches
    try:
        _commit_needed = False
        for _fn2, _info in _json_photo_map.items():
            if _info.get('email') or _info.get('child_name'):
                _entry = PhotoUploadLog.query.filter_by(filename=_fn2).first()
                if _entry:
                    if _info.get('email') and not _entry.email:
                        _entry.email = _info['email']
                        _commit_needed = True
                    if _info.get('child_name') and not _entry.child_name:
                        _entry.child_name = _info['child_name']
                        _commit_needed = True
                    if _info.get('preview_id') and not _entry.preview_id:
                        _entry.preview_id = _info['preview_id']
                        _commit_needed = True
        if _commit_needed:
            db.session.commit()
    except Exception:
        db.session.rollback()

    # Full upload history log
    _raw_log = PhotoUploadLog.query.order_by(PhotoUploadLog.uploaded_at.desc()).limit(500).all()
    upload_log = []
    for _e in _raw_log:
        _ji = _json_photo_map.get(_e.filename, {})
        upload_log.append({
            'id': _e.id,
            'filename': _e.filename,
            'story_id': _e.story_id or '',
            'photo_type': _e.photo_type or 'human',
            'ip': _e.ip_address or '',
            'size_kb': _e.file_size_kb or 0,
            'uploaded_at': _e.uploaded_at.strftime('%Y-%m-%d %H:%M') if _e.uploaded_at else '',
            'deleted_at': _e.deleted_at.strftime('%Y-%m-%d %H:%M') if _e.deleted_at else None,
            'active': _e.filename in active_files and not _e.deleted_at,
            'email': _e.email or _ji.get('email', ''),
            'child_name': _e.child_name or _ji.get('child_name', ''),
            'preview_id': _e.preview_id or _ji.get('preview_id', ''),
        })

    return render_template('admin_photos.html',
                          photos=photos,
                          total_photos=total_photos,
                          expired_count=expired_count,
                          upload_log=upload_log,
                          log_total=len(upload_log))

@app.route('/admin/uploaded-photos/delete/<filename>', methods=['POST'])
def admin_delete_photo(filename):
    """Admin: manually delete an uploaded photo."""
    if not check_admin_auth():
        return jsonify({'success': False, 'error': 'Not authorized'}), 401
    
    import re
    if not re.match(r'^[a-zA-Z0-9_\-\.]+$', filename):
        return jsonify({'success': False, 'error': 'Invalid filename'}), 400
    
    filepath = os.path.join('generated/uploads/furry_photos', filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        print(f"[ADMIN] Manually deleted photo: {filename}")
        try:
            _log = PhotoUploadLog.query.filter_by(filename=filename, deleted_at=None).first()
            if _log:
                _log.deleted_at = datetime.utcnow()
                db.session.commit()
        except Exception:
            db.session.rollback()
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'File not found'}), 404

@app.route('/admin/uploaded-photos/delete-expired', methods=['POST'])
def admin_delete_expired_photos():
    """Admin: delete all expired photos (older than 72h)."""
    if not check_admin_auth():
        return jsonify({'success': False, 'error': 'Not authorized'}), 401
    
    import glob as glob_module
    upload_dir = 'generated/uploads/furry_photos'
    deleted = 0
    deleted_fns = []
    if os.path.exists(upload_dir):
        for filepath in glob_module.glob(os.path.join(upload_dir, '*')):
            if os.path.isfile(filepath):
                age_hours = (datetime.now() - datetime.fromtimestamp(os.path.getmtime(filepath))).total_seconds() / 3600
                if age_hours >= 72:
                    os.remove(filepath)
                    deleted_fns.append(os.path.basename(filepath))
                    deleted += 1
    print(f"[ADMIN] Deleted {deleted} expired photos")
    try:
        _now_utc = datetime.utcnow()
        for _fn in deleted_fns:
            _log = PhotoUploadLog.query.filter_by(filename=_fn, deleted_at=None).first()
            if _log:
                _log.deleted_at = _now_utc
        if deleted_fns:
            db.session.commit()
    except Exception:
        db.session.rollback()
    return jsonify({'success': True, 'deleted': deleted})

@app.route('/admin/uploaded-photos/serve/<filename>')
def admin_serve_photo(filename):
    """Admin: serve an uploaded photo for preview."""
    if not check_admin_auth():
        return "Not authorized", 401
    
    import re
    if not re.match(r'^[a-zA-Z0-9_\-\.]+$', filename):
        return "Invalid filename", 400
    
    filepath = os.path.join('generated/uploads/furry_photos', filename)
    if os.path.exists(filepath):
        return send_file(filepath)
    return "File not found", 404

@app.route('/admin/quick-stories/<preview_id>')
def admin_quick_story_detail(preview_id):
    """Admin detail view for a quick story."""
    if not check_admin_auth():
        return redirect(url_for('admin_login_page'))

    preview_file = f'story_previews/{preview_id}.json'
    if not os.path.exists(preview_file):
        return "Story not found", 404

    with open(preview_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    raw_pages = data.get('pages', [])

    # Images are stored separately from the text pages array.
    # Prefer scene_paths (PIL-composed with text) for text_composed stories,
    # otherwise use original_scene_paths (clean), falling back to images/original_images.
    text_composed = data.get('qs_text_composed', False)
    if text_composed:
        scene_imgs = (data.get('scene_paths') or data.get('images') or
                      data.get('original_scene_paths') or data.get('original_images') or [])
    else:
        scene_imgs = (data.get('original_scene_paths') or data.get('original_images') or
                      data.get('scene_paths') or data.get('images') or [])

    # Strip _preview paths so admin sees clean images
    scene_imgs = [p for p in scene_imgs if p and '_preview' not in str(p)]

    # Also capture regen counts so the template can show remaining slots
    regen_counts = data.get('scene_regenerations', {})

    # Combine text pages with their corresponding images into a single list
    pages = []
    for i, page in enumerate(raw_pages):
        entry = dict(page)
        entry['scene_num'] = i + 1
        img = scene_imgs[i] if i < len(scene_imgs) else ''
        entry['img_url'] = ('/' + img.lstrip('/')) if img else ''
        entry['regen_used'] = regen_counts.get(str(i + 1), 0)
        pages.append(entry)

    # If no pages array but we have images (edge case), build minimal entries
    if not pages and scene_imgs:
        for i, img in enumerate(scene_imgs):
            pages.append({
                'scene_num': i + 1,
                'text': '',
                'img_url': ('/' + img.lstrip('/')) if img else '',
                'regen_used': regen_counts.get(str(i + 1), 0),
            })

    cover_img = (data.get('cover_image') or data.get('original_cover') or
                 data.get('cover_preview') or '')
    if cover_img:
        cover_img = '/' + cover_img.lstrip('/')

    return render_template('admin_quick_story_detail.html',
                           preview_id=preview_id,
                           story=data,
                           pages=pages,
                           cover_img=cover_img)


def _generate_scenes_background(preview_id, **kwargs):
    """
    Background task: generate scenes for a Quick Story after payment.
    Runs in TaskQueue so it continues even if the user closes the page.
    The task_result kwarg is injected by TaskQueue automatically.
    """
    task_result = kwargs.get('task_result')
    preview_file = f'story_previews/{preview_id}.json'
    
    if not os.path.exists(preview_file):
        raise Exception(f"Preview file not found: {preview_file}")
    
    with open(preview_file, 'r', encoding='utf-8') as f:
        story_data = json.load(f)
    
    story_id = story_data.get('story_id', '')
    output_dir = story_data.get('output_dir', '')
    _qs_lang = story_data.get('lang', 'es')
    _qs_child_name = story_data.get('child_name', '')
    _qs_email = story_data.get('customer_email', '')

    if _qs_email and story_data.get('paid', False) and not story_data.get('recovery_email_sent', False):
        try:
            _qs_base = os.environ.get('SITE_DOMAIN', '') or os.environ.get('REPLIT_DEV_DOMAIN', 'magicmemoriesbooks.com')
            _qs_recovery_url = f"https://{_qs_base}/order-complete/{preview_id}"
            from services.email_service import send_recovery_link_email
            send_recovery_link_email(
                to_email=_qs_email,
                child_name=_qs_child_name,
                recovery_url=_qs_recovery_url,
                lang=_qs_lang,
                want_ebook=story_data.get('want_ebook', False),
                want_pdf=story_data.get('want_pdf', False),
                want_print=story_data.get('want_print', False),
            )
            story_data['recovery_email_sent'] = True
            with open(preview_file, 'w', encoding='utf-8') as _qsf:
                json.dump(story_data, _qsf, ensure_ascii=False, indent=2)
            production_logger.info(f"[BG-GEN] Recovery email sent to {_qs_email}")
        except Exception as _qs_rec_err:
            production_logger.warning(f"[BG-GEN] Recovery email failed: {_qs_rec_err}")

    if not story_data.get('scenes_pending', False):
        production_logger.info(f"[BG-GEN] {preview_id} scenes already generated, skipping")
        return {'status': 'already_done'}
    
    existing_scenes = []
    if output_dir and os.path.exists(output_dir):
        existing_scenes = sorted([
            fn for fn in os.listdir(output_dir)
            if fn.startswith('scene_') and fn.endswith('.png') and fn != 'scene_0.png'
            and os.path.getsize(os.path.join(output_dir, fn)) > 1000
        ])
    
    from services.fixed_stories import STORIES as FIXED_STORIES_BG
    story_pages_count = len(story_data.get('pages', []))
    config_scenes = len(FIXED_STORIES_BG.get(story_id, {}).get('pages', []))
    expected_scenes = story_pages_count or config_scenes or 8
    
    if len(existing_scenes) >= expected_scenes:
        production_logger.info(f"[BG-GEN] {preview_id} scenes already on disk ({len(existing_scenes)}/{expected_scenes})")
        formatted = [f'/{output_dir}/{fn}' for fn in existing_scenes[:expected_scenes]]
        story_data['scene_paths'] = formatted
        story_data['images'] = formatted
        story_data['original_scene_paths'] = formatted
        story_data['original_images'] = formatted
        story_data['scenes_pending'] = False
        story_data['scenes_generating'] = False
        story_data['generation_failed'] = False
        with open(preview_file, 'w', encoding='utf-8') as f:
            json.dump(story_data, f, ensure_ascii=False, indent=2)
        return {'status': 'already_on_disk', 'scenes': len(formatted)}
    
    lock_file = os.path.join(output_dir, '.generation.lock') if output_dir else None
    if lock_file:
        if os.path.exists(lock_file):
            lock_age = time.time() - os.path.getmtime(lock_file)
            if lock_age < 600:
                production_logger.info(f"[BG-GEN] {preview_id} generation already in progress (lock {lock_age:.0f}s)")
                return {'status': 'already_running'}
            else:
                production_logger.info(f"[BG-GEN] {preview_id} stale lock ({lock_age:.0f}s), proceeding")
        os.makedirs(os.path.dirname(lock_file) if os.path.dirname(lock_file) else '.', exist_ok=True)
        with open(lock_file, 'w') as lf:
            lf.write(str(os.getpid()))
    
    story_data['scenes_generating'] = True
    with open(preview_file, 'w', encoding='utf-8') as f:
        json.dump(story_data, f, ensure_ascii=False, indent=2)
    
    try:
        child_name = story_data.get('child_name', 'Child')
        gender = story_data.get('gender', 'neutral')
        traits = story_data.get('traits', {})
        
        is_illustrated_book = story_data.get('is_illustrated_book', False)
        
        if is_illustrated_book:
            from services.illustrated_book_service import generate_full_book, save_book_as_images, generate_cover_spread
            from services.personalized_books.generation import get_personalized_book_id
            
            book_id = get_personalized_book_id(story_id)
            
            ref_path = None
            ref_path_2 = None
            
            if book_id in ('furry_love', 'furry_love_adventure', 'furry_love_teen', 'furry_love_adult'):
                human_preview = story_data.get('human_preview_path', story_data.get('character_preview', ''))
                if human_preview:
                    human_ref = human_preview.lstrip('/')
                    if os.path.exists(human_ref):
                        ref_path = human_ref
                pet_preview = story_data.get('pet_preview_path', '')
                if pet_preview:
                    pet_ref = pet_preview.lstrip('/')
                    if os.path.exists(pet_ref):
                        ref_path_2 = pet_ref
            elif book_id == 'star_keeper':
                reference_image = story_data.get('character_preview', '') or story_data.get('cover_image', '')
                if reference_image and reference_image.startswith('/'):
                    reference_image = reference_image[1:]
                ref_path = reference_image if reference_image and os.path.exists(reference_image) else None
                luna_static = 'static/assets/luna_reference.png'
                if os.path.exists(luna_static):
                    ref_path_2 = luna_static
                production_logger.info(f"[BG-GEN] Star keeper refs: character_preview={bool(ref_path)}, LUNA={bool(ref_path_2)}")
            elif book_id == 'dragon_garden':
                reference_image = story_data.get('character_preview', '') or story_data.get('cover_image', '')
                if reference_image and reference_image.startswith('/'):
                    reference_image = reference_image[1:]
                ref_path = reference_image if reference_image and os.path.exists(reference_image) else None
                spark_static = 'static/assets/spark_reference.png'
                if os.path.exists(spark_static):
                    ref_path_2 = spark_static
                production_logger.info(f"[BG-GEN] Dragon garden refs: character_preview={bool(ref_path)}, SPARK={bool(ref_path_2)}")
            elif book_id == 'magic_chef':
                reference_image = story_data.get('character_preview', '') or story_data.get('cover_image', '')
                if reference_image and reference_image.startswith('/'):
                    reference_image = reference_image[1:]
                ref_path = reference_image if reference_image and os.path.exists(reference_image) else None
                sweetie_static = 'static/assets/sweetie_reference.png'
                if os.path.exists(sweetie_static):
                    ref_path_2 = sweetie_static
                production_logger.info(f"[BG-GEN] Magic chef refs: character_preview={bool(ref_path)}, SWEETIE={bool(ref_path_2)}")
            elif book_id == 'magic_inventor':
                reference_image = story_data.get('character_preview', '') or story_data.get('cover_image', '')
                if reference_image and reference_image.startswith('/'):
                    reference_image = reference_image[1:]
                ref_path = reference_image if reference_image and os.path.exists(reference_image) else None
                from services.personalized_books.preview import _ensure_bolt_reference
                bolt_regen_path = _ensure_bolt_reference()
                if bolt_regen_path and os.path.exists(bolt_regen_path):
                    ref_path_2 = bolt_regen_path
                production_logger.info(f"[BG-GEN] Magic inventor refs: character_preview={bool(ref_path)}, BOLT={bool(ref_path_2)}")
            elif book_id == 'centinela_aurora':
                reference_image = story_data.get('character_preview', '') or story_data.get('cover_image', '')
                if reference_image and reference_image.startswith('/'):
                    reference_image = reference_image[1:]
                ref_path = reference_image if reference_image and os.path.exists(reference_image) else None
                astro_static = 'static/assets/astro_reference.png'
                if os.path.exists(astro_static):
                    ref_path_2 = astro_static
                production_logger.info(f"[BG-GEN] Centinela aurora refs: character_preview={bool(ref_path)}, ASTRO={bool(ref_path_2)}")
            else:
                reference_image = story_data.get('character_preview', '') or story_data.get('cover_image', '')
                if reference_image and reference_image.startswith('/'):
                    reference_image = reference_image[1:]
                ref_path = reference_image if reference_image and os.path.exists(reference_image) else None
            
            production_logger.info(f"[BG-GEN] Starting personalized book scene generation for {preview_id} (book={book_id}, ref={bool(ref_path)}, ref2={bool(ref_path_2)})")
            
            lang = story_data.get('lang', 'es')
            dedication = story_data.get('dedication', '')
            author_name = story_data.get('author_name', 'Magic Memories Books')
            
            from services.illustrated_book_service import load_book_config as _load_bcfg
            _bcfg = _load_bcfg(book_id) or {}
            _total_scenes = len(_bcfg.get('scenes', [])) or 1
            _generation_progress[preview_id] = {'generated': 0, 'total': _total_scenes}
            
            def _scene_progress_cb(done, total):
                _generation_progress[preview_id] = {'generated': done, 'total': total}
                _write_progress(preview_id, done, total)
            
            _clean_scenes = []
            pages, failed_scene_indices = generate_full_book(
                book_id=book_id,
                child_name=child_name,
                traits=traits,
                gender=gender,
                language=lang,
                dedication_text=dedication,
                for_print=True,
                author_name=author_name,
                reference_image_path=ref_path,
                reference_image_path_2=ref_path_2,
                progress_callback=_scene_progress_cb,
                clean_scenes_collector=_clean_scenes
            )
            
            if len(pages) < 10:
                raise Exception(f"Only {len(pages)} pages generated, expected at least 10")
            
            composed_dir = f'generated/composed_{preview_id}'
            os.makedirs(composed_dir, exist_ok=True)
            
            for _cs_idx, _cs_img in _clean_scenes:
                try:
                    _cs_path = os.path.join(composed_dir, f'clean_scene_{_cs_idx}.png')
                    _cs_img.save(_cs_path, format='PNG')
                    _cs_img.close()
                except Exception as _cs_err:
                    print(f'[BG-GEN] WARNING: could not save clean_scene_{_cs_idx}: {_cs_err}')

            saved = save_book_as_images(pages, composed_dir, prefix='page', with_watermark=False)
            original_paths = saved.get('original', [])
            preview_paths = saved.get('preview', [])
            
            formatted_scene_paths = [p if p.startswith('/') else f'/{p}' for p in preview_paths if p]
            formatted_original_paths = [p if p.startswith('/') else f'/{p}' for p in original_paths if p]
            
            cover_ref = ref_path
            cover_ref_2 = ref_path_2
            _cover_raw_books = ('furry_love', 'furry_love_adventure', 'furry_love_teen', 'furry_love_adult', 'centinela_aurora', 'magic_chef', 'dragon_garden')
            if book_id in _cover_raw_books:
                _log_prefix = 'Furry love' if 'furry' in book_id else ('Magic Chef' if book_id == 'magic_chef' else ('Dragon Garden' if book_id == 'dragon_garden' else 'Centinela aurora'))
                cover_raw_saved = story_data.get('cover_raw_path', '')
                if cover_raw_saved:
                    raw_path = cover_raw_saved.lstrip('/')
                    if os.path.exists(raw_path):
                        cover_ref = raw_path
                        cover_ref_2 = None
                        production_logger.info(f"[BG-GEN] {_log_prefix}: using RAW pre-generated cover for cover spread: {raw_path}")
                if cover_ref == ref_path:
                    output_dir_check = story_data.get('output_dir', '')
                    if output_dir_check:
                        raw_fallback = os.path.join(output_dir_check, 'cover_raw.png')
                        if os.path.exists(raw_fallback):
                            cover_ref = raw_fallback
                            cover_ref_2 = None
                            production_logger.info(f"[BG-GEN] {_log_prefix}: found cover_raw.png on disk: {raw_fallback}")
            
            cover_spread = generate_cover_spread(traits, child_name, gender, lang, book_id, author_name, reference_image_path=cover_ref, reference_image_path_2=cover_ref_2)
            
            DPI = 300
            MM_TO_INCH = 1 / 25.4
            wrap_px = int(19.05 * MM_TO_INCH * DPI)
            board_w_px = int(213.175 * MM_TO_INCH * DPI)
            board_h_px = int(303.35 * MM_TO_INCH * DPI)
            spine_px = int(6.35 * MM_TO_INCH * DPI)
            
            front_x = wrap_px + board_w_px + spine_px
            front_cover = cover_spread.crop((front_x, wrap_px, front_x + board_w_px, wrap_px + board_h_px))
            
            cover_spread_path = os.path.join(composed_dir, 'cover_spread.png')
            cover_spread.save(cover_spread_path, 'PNG')
            
            front_cover_path = os.path.join(composed_dir, 'front_cover.png')
            front_cover.save(front_cover_path, 'PNG')
            
            story_data['scene_paths'] = formatted_scene_paths
            story_data['images'] = formatted_scene_paths
            story_data['original_scene_paths'] = formatted_original_paths
            story_data['original_images'] = formatted_original_paths
            story_data['cover_image'] = f'/{front_cover_path}'
            if book_id not in ('furry_love', 'furry_love_adventure', 'furry_love_teen', 'furry_love_adult') or not story_data.get('original_cover'):
                story_data['original_cover'] = f'/{front_cover_path}'
            else:
                production_logger.info(f"[BG-GEN] Preserving original_cover for furry_love (not overwriting with spread-extracted cover)")
            story_data['cover_spread_path'] = cover_spread_path
            story_data['scenes_pending'] = False
            story_data['scenes_generating'] = False
            story_data['generation_failed'] = False
            story_data['pages_composed'] = False
            
            if failed_scene_indices:
                page_indices = [i + 3 for i in failed_scene_indices]
                story_data['failed_scenes'] = failed_scene_indices
                story_data['failed_page_indices'] = page_indices
                story_data['retry_count'] = 0
                story_data['max_retries'] = 6
                story_data['scenes_retrying'] = True
                story_data['book_scenes_ready'] = False
                
                with open(preview_file, 'w', encoding='utf-8') as f:
                    json.dump(story_data, f, ensure_ascii=False, indent=2)
                
                production_logger.warning(f"[BG-GEN] {preview_id} has {len(failed_scene_indices)} failed scenes: {[i+1 for i in failed_scene_indices]}. Scheduling retry in 10 min.")
                
                _send_admin_scene_failure_notification(preview_id, story_data, failed_scene_indices)
                
                _schedule_scene_retry(preview_id, delay_seconds=600)
                
                return {'status': 'partial', 'scenes': len(pages), 'failed': len(failed_scene_indices)}
            
            story_data['book_scenes_ready'] = True
            
            with open(preview_file, 'w', encoding='utf-8') as f:
                json.dump(story_data, f, ensure_ascii=False, indent=2)
            
            production_logger.info(f"[BG-GEN] {preview_id} personalized book scenes completed: {len(pages)} pages + cover")
            return {'status': 'completed', 'scenes': len(pages)}
        
        from services.replicate_service import generate_scenes_only
        from services.quick_stories.checkout import ALL_QUICK_FAMILY_IDS as QS_BG_IDS
        
        cover_image = story_data.get('cover_image', '')
        if cover_image and cover_image.startswith('/'):
            cover_image = cover_image[1:]
        
        is_qs = story_id in QS_BG_IDS
        
        story_cfg = FIXED_STORIES_BG.get(story_id, {})
        age_range = story_cfg.get('age_range', '0-1')
        is_baby = age_range in ['0-1', '0-2']
        has_ideogram = story_cfg.get('use_ideogram_scenes', False) and is_baby
        use_flux_dev = is_qs and not has_ideogram
        
        scene_ref_image = cover_image
        if is_qs and output_dir:
            clean_cover = f"{output_dir}/cover_clean.png"
            base_char = f"{output_dir}/base_character.png"
            if os.path.exists(clean_cover):
                scene_ref_image = clean_cover
            elif os.path.exists(base_char):
                scene_ref_image = base_char
        
        production_logger.info(f"[BG-GEN] Starting scene generation for {preview_id} (story={story_id}, flux_dev={use_flux_dev})")
        
        from services.fixed_stories import STORIES as _FS_TOTAL
        _qs_story_cfg = _FS_TOTAL.get(story_id, {})
        _qs_has_closing = bool(story_data.get('closing_message') or _qs_story_cfg.get('closing_message_es') or _qs_story_cfg.get('closing_message_en'))
        _qs_total = (len(story_data.get('pages', [])) or len(_qs_story_cfg.get('pages', [])) or 8) + (1 if _qs_has_closing else 0)
        _generation_progress[preview_id] = {'generated': 0, 'total': _qs_total}

        def _qs_progress_cb(done, _ignored_total):
            _generation_progress[preview_id] = {'generated': done, 'total': _qs_total}
            _write_progress(preview_id, done, _qs_total)

        scenes_result = generate_scenes_only(
            story_id, gender, traits, output_dir, scene_ref_image, child_name,
            use_flux_dev=use_flux_dev,
            progress_callback=_qs_progress_cb
        )
        
        scene_paths = scenes_result.get('scenes', [])
        closing_image = scenes_result.get('closing', None)
        
        text_layout = story_cfg.get('text_layout', 'single')
        pages_data = story_data.get('pages', [])
        lang = story_data.get('lang', story_data.get('language', 'es'))
        is_birthday_story = story_cfg.get('is_birthday', False)
        
        import shutil as _shutil
        original_raw_paths = []
        if scene_paths and pages_data:
            from services.quick_stories.image_composer import compose_baby_text_on_image, compose_kids_text_on_image
            from PIL import Image as PILImage
            
            for idx, sp in enumerate(scene_paths):
                if not sp:
                    original_raw_paths.append(None)
                    continue
                raw_path = sp.lstrip('/')
                if not os.path.exists(raw_path):
                    original_raw_paths.append(None)
                    continue
                orig_copy_path = raw_path.replace('.png', '_orig.png')
                try:
                    _shutil.copy2(raw_path, orig_copy_path)
                    original_raw_paths.append(orig_copy_path)
                except Exception:
                    original_raw_paths.append(raw_path)
                if idx >= len(pages_data):
                    continue
                    
                page = pages_data[idx]
                try:
                    img = PILImage.open(raw_path)
                    if text_layout == 'split':
                        text_above = page.get('text_above', '')
                        text_below = page.get('text_below', '')
                        if not text_above and not text_below:
                            text_above = page.get('text', '')
                        composed = compose_kids_text_on_image(img, text_above, text_below, lang)
                    else:
                        text = page.get('text', '')
                        composed = compose_baby_text_on_image(img, text, lang)
                    composed.save(raw_path, 'PNG')
                    production_logger.info(f"[BG-GEN] Composed text on scene {idx} for {preview_id}")
                except Exception as comp_err:
                    production_logger.error(f"[BG-GEN] Text composition failed for scene {idx}: {comp_err}")
            story_data['qs_text_composed'] = True
        
        successful_count = len([p for p in scene_paths if p])
        failed_indices = [i for i, p in enumerate(scene_paths) if not p]
        
        if successful_count < 3:
            raise Exception(f"Only {successful_count} scenes generated, expected at least 3")
        
        if failed_indices:
            from PIL import Image as PILImage_placeholder
            for fi in failed_indices:
                placeholder = PILImage_placeholder.new('RGB', (1024, 1024), (240, 230, 255))
                from PIL import ImageDraw, ImageFont
                draw = ImageDraw.Draw(placeholder)
                try:
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
                    small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
                except:
                    font = ImageFont.load_default()
                    small_font = font
                draw.text((512, 440), "⚠️", fill=(147, 51, 234), anchor="mm", font=font)
                draw.text((512, 500), "Illustration failed", fill=(147, 51, 234), anchor="mm", font=font)
                draw.text((512, 550), "Use regenerate button below", fill=(100, 100, 100), anchor="mm", font=small_font)
                placeholder_path = os.path.join(output_dir, f"scene_{fi + 1}.png")
                placeholder.save(placeholder_path, 'PNG')
                scene_paths[fi] = placeholder_path
                production_logger.warning(f"[BG-GEN] Created placeholder for failed scene {fi + 1}")
            story_data['failed_scenes'] = failed_indices
        
        formatted_scene_paths = []
        for p in scene_paths:
            if p:
                path = p if p.startswith('/') else f'/{p}'
                formatted_scene_paths.append(path)
        
        formatted_original_paths = []
        for p in original_raw_paths:
            if p:
                path = p if p.startswith('/') else f'/{p}'
                formatted_original_paths.append(path)
        if not formatted_original_paths:
            formatted_original_paths = formatted_scene_paths
        
        story_data['scene_paths'] = formatted_scene_paths
        story_data['images'] = formatted_scene_paths
        story_data['original_scene_paths'] = formatted_original_paths
        story_data['original_images'] = formatted_original_paths
        if closing_image:
            story_data['closing_image'] = closing_image if closing_image.startswith('/') else f'/{closing_image}'
            closing_msg = story_data.get('closing_message', '')
            if closing_msg:
                try:
                    from services.quick_stories.image_composer import compose_kids_text_on_image
                    from PIL import Image as PILImage
                    closing_raw = closing_image.lstrip('/')
                    if os.path.exists(closing_raw):
                        closing_img = PILImage.open(closing_raw)
                        composed_closing = compose_kids_text_on_image(closing_img, '', closing_msg, lang)
                        composed_closing.save(closing_raw, 'PNG')
                        production_logger.info(f"[BG-GEN] Composed closing message on closing image for {preview_id}")
                except Exception as closing_err:
                    production_logger.error(f"[BG-GEN] Closing text composition failed: {closing_err}")
        story_data['scenes_pending'] = False
        story_data['scenes_generating'] = False
        story_data['generation_failed'] = False
        
        with open(preview_file, 'w', encoding='utf-8') as f:
            json.dump(story_data, f, ensure_ascii=False, indent=2)
        
        _generation_progress.pop(preview_id, None)
        _clear_progress(preview_id)
        production_logger.info(f"[BG-GEN] {preview_id} completed: {len(scene_paths)} scenes, closing={bool(closing_image)}")
        
        customer_email = story_data.get('customer_email', '')
        qs_needs_ebook = story_data.get('paid', False) and not story_data.get('visor_uploaded', False) and not story_data.get('admin_gift', False)
        if is_qs and qs_needs_ebook and customer_email:
            production_logger.info(f"[BG-GEN] Quick Story - auto-launching visor upload (no email - waiting for user approval) for {preview_id}")
            try:
                _process_ebook_generation(preview_id, customer_email, send_email=False)
            except Exception as visor_err:
                production_logger.error(f"[BG-GEN] Visor auto-upload failed for {preview_id}: {visor_err}")
        
        return {'status': 'completed', 'scenes': len(scene_paths)}
        
    except Exception as e:
        production_logger.error(f"[BG-GEN] {preview_id} FAILED: {e}")
        import traceback
        production_logger.error(traceback.format_exc())
        
        story_data['scenes_generating'] = False
        story_data['generation_failed'] = True
        story_data['generation_error'] = str(e)
        with open(preview_file, 'w', encoding='utf-8') as f:
            json.dump(story_data, f, ensure_ascii=False, indent=2)
        
        _generation_progress.pop(preview_id, None)
        _clear_progress(preview_id)
        is_final_attempt = task_result is None or task_result.retries >= task_result.max_retries - 1

        if is_final_attempt:
            try:
                import traceback as tb
                from services.email_service import send_admin_error_email
                send_admin_error_email('_generate_scenes_background', preview_id, str(e), tb.format_exc(),
                                       story_data=story_data, is_retry_failure=bool(story_data.get('retry_attempted', False)))
            except Exception:
                pass

        raise
    finally:
        if lock_file and os.path.exists(lock_file):
            try:
                os.remove(lock_file)
            except:
                pass


def _trigger_background_generation(preview_id):
    """Helper to enqueue scene generation if needed. Safe to call multiple times."""
    preview_file = f'story_previews/{preview_id}.json'
    if not os.path.exists(preview_file):
        return
    
    with open(preview_file, 'r', encoding='utf-8') as f:
        story_data = json.load(f)
    
    if not story_data.get('scenes_pending', False):
        return
    if story_data.get('scenes_generating', False):
        return
    
    task_id = f"scene_gen_{preview_id}"
    existing = task_queue.get_status(task_id)
    if existing and existing.get('status') in ['pending', 'processing']:
        production_logger.info(f"[BG-GEN] Task {task_id} already queued, skipping")
        return
    
    story_data['scenes_generating'] = True
    with open(preview_file, 'w', encoding='utf-8') as f:
        json.dump(story_data, f, ensure_ascii=False, indent=2)
    
    production_logger.info(f"[BG-GEN] Enqueueing background generation for {preview_id}")
    task_queue.enqueue(task_id, _generate_scenes_background, preview_id)


def _send_admin_scene_failure_notification(preview_id, story_data, failed_scene_indices):
    try:
        from services.email_service import FROM_EMAIL, FROM_NAME, SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        
        child_name = story_data.get('child_name', 'Unknown')
        story_id = story_data.get('story_id', '')
        customer_email = story_data.get('customer_email', '')
        failed_list = ', '.join([str(i+1) for i in failed_scene_indices])
        retry_count = story_data.get('retry_count', 0)
        
        base_url = os.environ.get('SITE_DOMAIN', os.environ.get('REPLIT_DEV_DOMAIN', 'magicmemoriesbooks.com'))
        admin_url = f"https://{base_url}/admin/preview/{preview_id}"
        
        subject = f"⚠️ Escenas fallidas - {child_name} ({len(failed_scene_indices)} escenas)"
        
        html_content = f"""
        <html><body style="font-family: Arial, sans-serif; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background: #fff; border-radius: 12px; border: 2px solid #f59e0b; padding: 20px;">
            <h2 style="color: #d97706;">⚠️ Escenas Fallidas en Libro</h2>
            <table style="width: 100%; border-collapse: collapse; margin: 15px 0;">
                <tr><td style="padding: 8px; font-weight: bold;">Preview ID:</td><td style="padding: 8px;">{preview_id}</td></tr>
                <tr><td style="padding: 8px; font-weight: bold;">Nombre:</td><td style="padding: 8px;">{child_name}</td></tr>
                <tr><td style="padding: 8px; font-weight: bold;">Cuento:</td><td style="padding: 8px;">{story_id}</td></tr>
                <tr><td style="padding: 8px; font-weight: bold;">Cliente:</td><td style="padding: 8px;">{customer_email}</td></tr>
                <tr><td style="padding: 8px; font-weight: bold;">Escenas fallidas:</td><td style="padding: 8px; color: #dc2626; font-weight: bold;">{failed_list}</td></tr>
                <tr><td style="padding: 8px; font-weight: bold;">Reintentos:</td><td style="padding: 8px;">{retry_count}/6</td></tr>
            </table>
            <p style="color: #4b5563;">El sistema reintentará automáticamente cada 10 minutos (máx. 6 veces = 1 hora).</p>
            <p style="color: #4b5563;">Si después de 1 hora no se resuelve, recibirás otra alerta.</p>
            <p style="margin-top: 15px;">
                <a href="{admin_url}" style="display: inline-block; background: #7c3aed; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: bold;">Ver en Admin Panel</a>
            </p>
        </div>
        </body></html>
        """
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{FROM_NAME} <{FROM_EMAIL}>"
        msg['To'] = FROM_EMAIL
        msg.attach(MIMEText(html_content, 'html'))
        
        if SMTP_USER and SMTP_PASSWORD:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.send_message(msg)
            production_logger.info(f"[RETRY] Admin notification sent for {preview_id}")
        else:
            production_logger.info(f"[RETRY] Admin notification (no SMTP): {subject}")
    except Exception as e:
        production_logger.error(f"[RETRY] Failed to send admin notification: {e}")


def _schedule_scene_retry(preview_id, delay_seconds=600):
    def _delayed_retry():
        time.sleep(delay_seconds)
        _retry_failed_scenes_background(preview_id)
    
    retry_thread = threading.Thread(target=_delayed_retry, daemon=True)
    retry_thread.start()
    production_logger.info(f"[RETRY] Scheduled retry for {preview_id} in {delay_seconds}s")


def _retry_failed_scenes_background(preview_id):
    from services.illustrated_book_service import generate_scene_complete, add_text_to_image, save_book_as_images, add_watermark
    from services.personalized_books.generation import get_personalized_book_id
    from PIL import Image
    
    preview_file = f'story_previews/{preview_id}.json'
    if not os.path.exists(preview_file):
        production_logger.error(f"[RETRY] Preview file not found: {preview_file}")
        return
    
    with open(preview_file, 'r', encoding='utf-8') as f:
        story_data = json.load(f)
    
    failed_scenes = story_data.get('failed_scenes', [])
    if not failed_scenes:
        production_logger.info(f"[RETRY] No failed scenes for {preview_id}, skipping")
        return
    
    retry_count = story_data.get('retry_count', 0) + 1
    max_retries = story_data.get('max_retries', 6)
    
    production_logger.info(f"[RETRY] Starting retry {retry_count}/{max_retries} for {preview_id} - {len(failed_scenes)} scenes")
    
    story_id = story_data.get('story_id', '')
    child_name = story_data.get('child_name', 'Child')
    gender = story_data.get('gender', 'neutral')
    traits = story_data.get('traits', {})
    lang = story_data.get('lang', 'es')
    book_id = get_personalized_book_id(story_id)
    
    ref_path = None
    ref_path_2 = None
    if book_id in ('furry_love', 'furry_love_adventure', 'furry_love_teen', 'furry_love_adult'):
        human_preview = story_data.get('human_preview_path', story_data.get('character_preview', ''))
        if human_preview:
            human_ref = human_preview.lstrip('/')
            if os.path.exists(human_ref):
                ref_path = human_ref
        pet_preview = story_data.get('pet_preview_path', '')
        if pet_preview:
            pet_ref = pet_preview.lstrip('/')
            if os.path.exists(pet_ref):
                ref_path_2 = pet_ref
    elif book_id == 'star_keeper':
        character_preview = story_data.get('character_preview', '') or story_data.get('cover_image', '')
        if character_preview:
            cp_ref = character_preview.lstrip('/')
            if os.path.exists(cp_ref):
                ref_path = cp_ref
        luna_static = 'static/assets/luna_reference.png'
        if os.path.exists(luna_static):
            ref_path_2 = luna_static
    else:
        reference_image = story_data.get('character_preview', '') or story_data.get('cover_image', '')
        if reference_image and reference_image.startswith('/'):
            reference_image = reference_image[1:]
        ref_path = reference_image if reference_image and os.path.exists(reference_image) else None
    
    from services.illustrated_book_service import BOOK_CONFIGS
    book_config = BOOK_CONFIGS.get(book_id, {})
    scenes = book_config.get("scenes", [])
    
    composed_dir = f'generated/composed_{preview_id}'
    os.makedirs(composed_dir, exist_ok=True)
    
    still_failed = []
    fixed_count = 0
    
    for scene_idx in failed_scenes:
        if scene_idx >= len(scenes):
            production_logger.warning(f"[RETRY] Scene index {scene_idx} out of range for {book_id}")
            continue
        
        scene_config = scenes[scene_idx]
        scene_num = scene_idx + 1
        production_logger.info(f"[RETRY] Retrying scene {scene_num} for {preview_id}...")
        
        try:
            scene_image = generate_scene_complete(
                scene_config,
                traits,
                child_name,
                gender,
                lang,
                book_id,
                reference_image_path=ref_path,
                reference_image_path_2=ref_path_2
            )
            
            text_key = f"text_{lang}"
            text = scene_config.get(text_key, scene_config.get("text_es", ""))
            text = text.replace("{name}", child_name)
            pet_name = traits.get('pet_name', '')
            if pet_name:
                text = text.replace("{pet_name}", pet_name)
            
            position = scene_config.get("text_position", "split")
            
            final_page = add_text_to_image(
                scene_image,
                text,
                position,
                "#FFFFFF",
                "#000000",
                38,
                0.103
            )
            
            page_index = scene_idx + 3
            original_path = os.path.join(composed_dir, f"page_{page_index:02d}.png")
            final_page.save(original_path, "PNG")
            preview_path = original_path

            formatted_original = f'/{original_path}'
            formatted_preview = f'/{preview_path}'
            
            original_paths_list = story_data.get('original_scene_paths', story_data.get('original_images', []))
            preview_paths_list = story_data.get('scene_paths', story_data.get('images', []))
            
            path_idx = page_index - 1
            if path_idx < len(original_paths_list):
                original_paths_list[path_idx] = formatted_original
            if path_idx < len(preview_paths_list):
                preview_paths_list[path_idx] = formatted_preview
            
            story_data['original_scene_paths'] = original_paths_list
            story_data['original_images'] = original_paths_list
            story_data['scene_paths'] = preview_paths_list
            story_data['images'] = preview_paths_list
            
            fixed_count += 1
            production_logger.info(f"[RETRY] Scene {scene_num} fixed successfully!")
            
        except RuntimeError as e:
            production_logger.warning(f"[RETRY] Scene {scene_num} still failing: {e}")
            still_failed.append(scene_idx)
        except Exception as e:
            production_logger.error(f"[RETRY] Scene {scene_num} unexpected error: {e}")
            still_failed.append(scene_idx)
    
    story_data['retry_count'] = retry_count
    
    if still_failed:
        story_data['failed_scenes'] = still_failed
        story_data['failed_page_indices'] = [i + 3 for i in still_failed]
        
        if retry_count < max_retries:
            story_data['scenes_retrying'] = True
            with open(preview_file, 'w', encoding='utf-8') as f:
                json.dump(story_data, f, ensure_ascii=False, indent=2)
            
            production_logger.warning(f"[RETRY] {preview_id}: {fixed_count} fixed, {len(still_failed)} still failing. Retry {retry_count}/{max_retries}. Next in 10 min.")
            _schedule_scene_retry(preview_id, delay_seconds=600)
        else:
            story_data['scenes_retrying'] = False
            story_data['retry_exhausted'] = True
            story_data['book_scenes_ready'] = True
            with open(preview_file, 'w', encoding='utf-8') as f:
                json.dump(story_data, f, ensure_ascii=False, indent=2)
            
            production_logger.error(f"[RETRY] {preview_id}: EXHAUSTED all {max_retries} retries. {len(still_failed)} scenes still failed: {[i+1 for i in still_failed]}")
            
            _send_admin_retry_exhausted_notification(preview_id, story_data, still_failed)
    else:
        story_data['failed_scenes'] = []
        story_data['failed_page_indices'] = []
        story_data['scenes_retrying'] = False
        story_data['retry_exhausted'] = False
        story_data['book_scenes_ready'] = True
        with open(preview_file, 'w', encoding='utf-8') as f:
            json.dump(story_data, f, ensure_ascii=False, indent=2)
        
        production_logger.info(f"[RETRY] {preview_id}: ALL {fixed_count} scenes fixed on retry {retry_count}! Book ready.")


def _send_admin_retry_exhausted_notification(preview_id, story_data, still_failed):
    try:
        from services.email_service import FROM_EMAIL, FROM_NAME, SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        
        child_name = story_data.get('child_name', 'Unknown')
        story_id = story_data.get('story_id', '')
        customer_email = story_data.get('customer_email', '')
        failed_list = ', '.join([str(i+1) for i in still_failed])
        
        base_url = os.environ.get('SITE_DOMAIN', os.environ.get('REPLIT_DEV_DOMAIN', 'magicmemoriesbooks.com'))
        admin_url = f"https://{base_url}/admin/preview/{preview_id}"
        
        subject = f"🚨 URGENTE: Reintentos agotados - {child_name} ({len(still_failed)} escenas)"
        
        html_content = f"""
        <html><body style="font-family: Arial, sans-serif; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background: #fff; border-radius: 12px; border: 2px solid #dc2626; padding: 20px;">
            <h2 style="color: #dc2626;">🚨 Reintentos Agotados - Acción Manual Requerida</h2>
            <p style="color: #4b5563;">El sistema intentó regenerar las escenas 6 veces durante 1 hora sin éxito. Se requiere intervención manual.</p>
            <table style="width: 100%; border-collapse: collapse; margin: 15px 0;">
                <tr><td style="padding: 8px; font-weight: bold;">Preview ID:</td><td style="padding: 8px;">{preview_id}</td></tr>
                <tr><td style="padding: 8px; font-weight: bold;">Nombre:</td><td style="padding: 8px;">{child_name}</td></tr>
                <tr><td style="padding: 8px; font-weight: bold;">Cuento:</td><td style="padding: 8px;">{story_id}</td></tr>
                <tr><td style="padding: 8px; font-weight: bold;">Cliente:</td><td style="padding: 8px;">{customer_email}</td></tr>
                <tr><td style="padding: 8px; font-weight: bold;">Escenas fallidas:</td><td style="padding: 8px; color: #dc2626; font-weight: bold;">{failed_list}</td></tr>
            </table>
            <p style="color: #4b5563;"><strong>Opciones:</strong></p>
            <ul style="color: #4b5563;">
                <li>Esperar a que Replicate se estabilice y reintentar desde admin</li>
                <li>Contactar al cliente para ofrecer regeneración gratuita</li>
            </ul>
            <p style="margin-top: 15px;">
                <a href="{admin_url}" style="display: inline-block; background: #dc2626; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: bold;">Ver en Admin Panel</a>
            </p>
        </div>
        </body></html>
        """
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{FROM_NAME} <{FROM_EMAIL}>"
        msg['To'] = FROM_EMAIL
        msg.attach(MIMEText(html_content, 'html'))
        
        if SMTP_USER and SMTP_PASSWORD:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.send_message(msg)
            production_logger.info(f"[RETRY] URGENT admin notification sent for {preview_id}")
        else:
            production_logger.info(f"[RETRY] URGENT admin notification (no SMTP): {subject}")
    except Exception as e:
        production_logger.error(f"[RETRY] Failed to send urgent notification: {e}")


def _trigger_personalized_book_composition(preview_id):
    """Helper to enqueue personalized book page composition if needed. Safe to call multiple times."""
    preview_file = f'story_previews/{preview_id}.json'
    if not os.path.exists(preview_file):
        return
    
    with open(preview_file, 'r', encoding='utf-8') as f:
        story_data = json.load(f)
    
    if story_data.get('pages_composed', False):
        return
    if story_data.get('book_composing', False):
        return
    if not story_data.get('is_illustrated_book', False):
        return
    
    task_id = f"book_compose_{preview_id}"
    existing = task_queue.get_status(task_id)
    if existing and existing.get('status') in ['pending', 'processing']:
        production_logger.info(f"[BG-COMPOSE] Task {task_id} already queued, skipping")
        return
    
    import time as _compose_time
    story_data['book_composing'] = True
    story_data['generation_started_at'] = _compose_time.time()
    if not story_data.get('book_scenes_ready', False):
        story_data['scenes_pending'] = True
        story_data['scenes_generating'] = True
    with open(preview_file, 'w', encoding='utf-8') as f:
        json.dump(story_data, f, ensure_ascii=False, indent=2)
    
    production_logger.info(f"[BG-COMPOSE] Enqueueing personalized book composition for {preview_id}")
    task_queue.enqueue(task_id, _compose_personalized_book_background, preview_id)


def _compose_personalized_book_background(preview_id, **kwargs):
    """
    Background task: compose personalized book pages + Lulu PDFs after payment.
    Runs in TaskQueue so it continues even if the user closes the page.
    """
    preview_file = f'story_previews/{preview_id}.json'
    
    if not os.path.exists(preview_file):
        raise Exception(f"Preview file not found: {preview_file}")
    
    with open(preview_file, 'r', encoding='utf-8') as f:
        story_data = json.load(f)
    
    if story_data.get('pages_composed', False):
        production_logger.info(f"[BG-COMPOSE] {preview_id} pages already composed, skipping")
        return {'status': 'already_done'}
    
    story_id = story_data.get('story_id', '')
    child_name = story_data.get('child_name', 'Child')
    lang = story_data.get('lang', 'es')
    dedication = story_data.get('dedication', '')
    gender = story_data.get('gender', 'neutral')
    traits = story_data.get('traits', {})
    customer_email = story_data.get('customer_email', '')

    if customer_email and not story_data.get('recovery_email_sent', False):
        try:
            _base = os.environ.get('SITE_DOMAIN', '') or os.environ.get('REPLIT_DEV_DOMAIN', 'magicmemoriesbooks.com')
            _recovery_url = f"https://{_base}/order-complete/{preview_id}"
            from services.email_service import send_recovery_link_email
            send_recovery_link_email(
                to_email=customer_email,
                child_name=child_name,
                recovery_url=_recovery_url,
                lang=lang,
                want_ebook=story_data.get('want_ebook', False),
                want_pdf=story_data.get('want_pdf', False),
                want_print=story_data.get('want_print', False),
            )
            story_data['recovery_email_sent'] = True
            with open(preview_file, 'w', encoding='utf-8') as _f:
                json.dump(story_data, _f, ensure_ascii=False, indent=2)
            production_logger.info(f"[BG-COMPOSE] Recovery email sent to {customer_email}")
        except Exception as _rec_err:
            production_logger.warning(f"[BG-COMPOSE] Recovery email failed: {_rec_err}")

    try:
        from services.illustrated_book_service import generate_full_book, save_book_as_images
        from services.personalized_books.generation import get_personalized_book_id
        
        book_id = get_personalized_book_id(story_id)
        composed_dir = f'generated/composed_{preview_id}'
        os.makedirs(composed_dir, exist_ok=True)
        
        scenes_already_ready = story_data.get('book_scenes_ready', False)
        
        if scenes_already_ready:
            production_logger.info(f"[BG-COMPOSE] Scenes already generated (two-stage flow), verifying files on disk...")
            
            original_paths_on_disk = story_data.get('original_scene_paths', story_data.get('original_images', []))
            original_paths = [p.lstrip('/') for p in original_paths_on_disk if os.path.exists(p.lstrip('/'))]
            
            production_logger.info(f"[BG-COMPOSE] Found {len(original_paths)} of {len(original_paths_on_disk)} pages on disk")
            
            if len(original_paths) < 10:
                production_logger.warning(f"[BG-COMPOSE] Only {len(original_paths)} pages found on disk, falling back to full generation")
                scenes_already_ready = False
            else:
                preview_paths_data = story_data.get('scene_paths', story_data.get('images', []))
                preview_paths = [p.lstrip('/') for p in preview_paths_data if os.path.exists(p.lstrip('/'))]
        
        if not scenes_already_ready:
            ref_image_path = None
            ref_image_path_2 = None
            
            child_photo_path = story_data.get('child_photo_path', '')
            if child_photo_path and os.path.exists(child_photo_path):
                ref_image_path = child_photo_path
                production_logger.info(f"[BG-COMPOSE] Using child photo reference for FLUX 2 Dev: {ref_image_path}")
            elif book_id == "magic_inventor":
                character_preview = story_data.get('character_preview', '')
                if character_preview:
                    ref_candidate = character_preview.lstrip('/')
                    if os.path.exists(ref_candidate):
                        ref_image_path = ref_candidate
                        production_logger.info(f"[BG-COMPOSE] Using reference image for FLUX 2 Dev: {ref_image_path}")
                    else:
                        production_logger.warning(f"[BG-COMPOSE] Reference image not found: {ref_candidate}")
            
            if book_id in ("furry_love", "furry_love_adventure", "furry_love_teen", "furry_love_adult"):
                human_preview = story_data.get('human_preview_path', story_data.get('character_preview', ''))
                if human_preview:
                    human_ref = human_preview.lstrip('/')
                    if os.path.exists(human_ref):
                        ref_image_path = human_ref
                        production_logger.info(f"[BG-COMPOSE] Furry love human reference: {ref_image_path}")
                pet_preview = story_data.get('pet_preview_path', '')
                if pet_preview:
                    pet_ref = pet_preview.lstrip('/')
                    if os.path.exists(pet_ref):
                        ref_image_path_2 = pet_ref
                        production_logger.info(f"[BG-COMPOSE] Furry love pet reference: {ref_image_path_2}")
            
            production_logger.info(f"[BG-COMPOSE] Generating personalized book pages for '{book_id}'...")
            _clean_scenes_compose = []
            pages, _failed = generate_full_book(
                book_id=book_id,
                child_name=child_name,
                traits=traits,
                gender=gender,
                language=lang,
                dedication_text=dedication,
                for_print=True,
                reference_image_path=ref_image_path,
                reference_image_path_2=ref_image_path_2,
                clean_scenes_collector=_clean_scenes_compose
            )
            for _cs_idx, _cs_img in _clean_scenes_compose:
                try:
                    _cs_path = os.path.join(composed_dir, f'clean_scene_{_cs_idx}.png')
                    _cs_img.save(_cs_path, format='PNG')
                    _cs_img.close()
                except Exception as _cs_err:
                    production_logger.warning(f'[BG-COMPOSE] Could not save clean_scene_{_cs_idx}: {_cs_err}')

            saved_paths = save_book_as_images(pages, composed_dir, prefix='page', with_watermark=False)
            original_paths = saved_paths['original']
            preview_paths = saved_paths['preview']
            
            if child_photo_path and os.path.exists(child_photo_path):
                try:
                    os.remove(child_photo_path)
                    story_data['child_photo_path'] = ''
                    production_logger.info(f"[BG-COMPOSE] Child photo deleted after composition: {child_photo_path}")
                except Exception as photo_del_err:
                    production_logger.warning(f"[BG-COMPOSE] Could not delete child photo: {photo_del_err}")
        
        production_logger.info(f"[BG-COMPOSE] Pages generated for {preview_id}: {len(original_paths)} page files on disk")
        story_data['composed_pages_dir'] = composed_dir
        with open(preview_file, 'w', encoding='utf-8') as f:
            json.dump(story_data, f, ensure_ascii=False, indent=2)

        # Single reconstruction pipeline: builds every path array from the
        # page_NN.png files on disk, rebuilds the cover spread only if the
        # raw cover changed, rebuilds the visor/eBook, the printable PDF and
        # the Cloudprinter cover.pdf/content.pdf. Identical for a first-time
        # composition and for any later admin/customer regeneration.
        from services.personalized_books.rebuild import rebuild_book
        rebuild_book(preview_id)

        with open(preview_file, 'r', encoding='utf-8') as f:
            story_data = json.load(f)
        formatted_original = story_data.get('scene_paths', [])
        visor_url = story_data.get('visor_url', '')

        is_admin_gift = story_data.get('admin_gift', False)
        # is_gift for the visor's expiry policy was already handled inside
        # rebuild_book (want_ebook / admin_gift). Only the DECISION of
        # whether to email the customer and submit a print order (a
        # permission concern, not reconstruction) differs by book type here.
        if is_admin_gift:
            production_logger.info(f"[BG-COMPOSE] ADMIN GIFT book — skipping customer email/print submission")
            story_data['ebook_is_gift'] = True

        if customer_email and not is_admin_gift:
            try:
                want_print = bool(story_data.get('want_print', False))
                want_ebook = bool(story_data.get('want_ebook', False))
                want_pdf = (story_data.get('product_type') == 'personalized_pdf') or bool(story_data.get('pdf_order')) or bool(story_data.get('want_pdf', False))

                # Gift ebook: customer didn't buy the ebook → receives 6-month gift visor
                give_gift_ebook = not want_ebook

                # Gift email placement (1 gift ebook max per order):
                # PDF+Print (no ebook): gift goes in libro impreso email (comes later)
                # PDF-only (no print, no ebook): gift goes in PDF email
                # All ebook combos: no gift (they paid for permanent access)
                _pdf_include_gift = give_gift_ebook and want_pdf and not want_print
                _print_include_gift = give_gift_ebook and want_print

                base_url = os.environ.get('SITE_DOMAIN', os.environ.get('REPLIT_DEV_DOMAIN', 'magicmemoriesbooks.com'))
                recovery_url = f"https://{base_url}/order-complete/{preview_id}"

                story_data['pdf_include_gift_ebook'] = _pdf_include_gift
                with open(preview_file, 'w', encoding='utf-8') as _vf:
                    json.dump(story_data, _vf, ensure_ascii=False, indent=2)
                production_logger.info(f"[BG-COMPOSE] Visor ready (want_ebook={want_ebook}, want_pdf={want_pdf}, want_print={want_print}): {visor_url}")

                _bg_product_type = story_data.get('product_type', '') or ''
                _print_product_type_bg = story_data.get('print_product_type', '') or ''
                _is_cp_pb_bg = (_bg_product_type == 'cp_personalized') or \
                               (_print_product_type_bg == 'cp_personalized') or \
                               (want_print and story_data.get('is_illustrated_book', False) and not _bg_product_type)
                if want_print and _is_cp_pb_bg:
                    shipping_address_g = story_data.get('shipping_address')
                    if shipping_address_g and shipping_address_g.get('name') and shipping_address_g.get('street1'):
                        try:
                            from services.personalized_books.generation import get_print_title
                            from services.cloudprinter_api_service import submit_pb_print_order, get_pdf_public_url, resolve_shipping_level
                            pet_name_g = traits.get('pet_name', '') if traits else ''
                            book_title_g = get_print_title(book_id, child_name, lang, pet_name=pet_name_g)
                            cp_shipping_level = resolve_shipping_level(story_data.get('shipping_method', 'cp_saver'))

                            # cover.pdf and content.pdf were already produced by
                            # rebuild_book() above (single reconstruction pipeline) —
                            # reuse those files instead of regenerating them here.
                            cp_out_dir = os.path.join("generations", "cloudprinter", preview_id)
                            cover_pdf_path   = os.path.join(cp_out_dir, "cover.pdf")
                            content_pdf_path = os.path.join(cp_out_dir, "content.pdf")
                            if not (os.path.exists(cover_pdf_path) and os.path.exists(content_pdf_path)):
                                raise RuntimeError(f"CP PDFs missing after rebuild_book for {preview_id}: {cover_pdf_path}, {content_pdf_path}")

                            cover_pdf_url   = get_pdf_public_url(preview_id, "cover.pdf")
                            content_pdf_url = get_pdf_public_url(preview_id, "content.pdf")
                            story_data['cp_cover_pdf_url']   = cover_pdf_url
                            story_data['cp_content_pdf_url'] = content_pdf_url
                            production_logger.info(f"[BG-COMPOSE] CP PDFs ready: cover={cover_pdf_url} content={content_pdf_url}")

                            cp_ok, cp_msg, cp_ref = submit_pb_print_order(
                                preview_id=preview_id,
                                cover_pdf_path=cover_pdf_path,
                                cover_pdf_url=cover_pdf_url,
                                content_pdf_path=content_pdf_path,
                                content_pdf_url=content_pdf_url,
                                customer_data={"email": customer_email or ""},
                                shipping_address=shipping_address_g,
                                shipping_level=cp_shipping_level,
                            )
                            if cp_ok:
                                story_data['cp_pb_order_ref'] = cp_ref
                                story_data['cp_order_status'] = 'submitted'
                                production_logger.info(f"[BG-COMPOSE] CP PB order submitted! Ref: {cp_ref}")
                                try:
                                    from services.email_service import send_cp_pb_admin_notification
                                    send_cp_pb_admin_notification(
                                        preview_id=preview_id,
                                        cp_order_ref=cp_ref or '',
                                        title=book_title_g,
                                        customer_email=customer_email or '',
                                        shipping_address=shipping_address_g,
                                        cover_pdf_url=cover_pdf_url,
                                        content_pdf_url=content_pdf_url,
                                        visor_url=story_data.get('visor_url', ''),
                                        paid_amount=f"${story_data.get('customer_total_usd', 0):.2f} USD" if story_data.get('customer_total_usd') else '',
                                        cp_cost_eur=float(story_data.get('cp_cost_eur', 0)),
                                        print_cost_eur=float(story_data.get('print_cost_eur', 0)),
                                    )
                                    production_logger.info(f"[BG-COMPOSE] Admin notification sent for CP order {cp_ref}")
                                except Exception as admin_notif_err:
                                    production_logger.error(f"[BG-COMPOSE] CP PB admin notification failed: {admin_notif_err}")
                            else:
                                story_data['cp_order_status'] = 'failed'
                                story_data['cp_order_error']  = cp_msg
                                production_logger.error(f"[BG-COMPOSE] CP PB order failed: {cp_msg}")
                        except Exception as cp_submit_err:
                            production_logger.error(f"[BG-COMPOSE] CP PB submission error: {cp_submit_err}")
                            story_data['cp_order_status'] = 'error'

                # Email A: PDF imprimible (if ordered) — pdf_dispatch handles it
                if (want_pdf or story_data.get('pdf_paid') or story_data.get('pdf_order')) and not story_data.get('pdf_email_sent'):
                    try:
                        production_logger.info(f"[BG-COMPOSE] PDF imprimible — lanzando dispatch para {preview_id} (pdf_include_gift={_pdf_include_gift})")
                        import threading as _threading_pdf
                        _t_pdf = _threading_pdf.Thread(
                            target=_dispatch_printable_pdf_email,
                            args=(preview_id, customer_email, lang),
                            daemon=True
                        )
                        _t_pdf.start()
                    except Exception as _pdf_bg_err:
                        production_logger.error(f"[BG-COMPOSE] PDF dispatch error: {_pdf_bg_err}")

                _email_b_sent = False
                _email_c_sent = False

                # Email B: Libro impreso — todos los pedidos de print reciben confirmación dedicada
                if want_print and not story_data.get('print_confirmation_sent'):
                    try:
                        from services.email_service import send_print_order_confirmation_email
                        send_print_order_confirmation_email(
                            to_email=customer_email,
                            story_data=story_data,
                            preview_id=preview_id,
                        )
                        _email_b_sent = True
                        story_data['print_confirmation_sent'] = True
                        with open(preview_file, 'w', encoding='utf-8') as _bf:
                            json.dump(story_data, _bf, ensure_ascii=False, indent=2)
                        production_logger.info(f"[BG-COMPOSE] Print order confirmation email sent to {customer_email}")
                    except Exception as _print_conf_err:
                        production_logger.error(f"[BG-COMPOSE] Print order confirmation email failed: {_print_conf_err}")
                elif want_print and story_data.get('print_confirmation_sent'):
                    production_logger.info(f"[BG-COMPOSE] Print order confirmation already sent for {preview_id} — skipping")
                    _email_b_sent = True

                # Email B2: eBook de regalo 6 meses — solo para pedidos print sin ebook
                if want_print and not want_ebook and visor_url and not story_data.get('gift_ebook_sent'):
                    try:
                        from services.email_service import send_ebook_email
                        send_ebook_email(
                            to_email=customer_email,
                            story_data=story_data,
                            visor_url=visor_url,
                            is_gift=True,
                            preview_id=preview_id,
                            is_print_order=False,
                        )
                        story_data['gift_ebook_sent'] = True
                        with open(preview_file, 'w', encoding='utf-8') as _gf:
                            json.dump(story_data, _gf, ensure_ascii=False, indent=2)
                        production_logger.info(f"[BG-COMPOSE] Gift eBook email sent to {customer_email} (6-month visor)")
                    except Exception as _gift_email_err:
                        production_logger.error(f"[BG-COMPOSE] Gift eBook email failed: {_gift_email_err}")
                elif want_print and not want_ebook and story_data.get('gift_ebook_sent'):
                    production_logger.info(f"[BG-COMPOSE] Gift eBook already sent for {preview_id} — skipping")

                # Email C: eBook interactivo permanente (if ebook purchased)
                # is_print_order=False because print info already sent in Email B above
                if want_ebook and not story_data.get('ebook_email_sent'):
                    if visor_url:
                        try:
                            from services.email_service import send_ebook_email
                            send_ebook_email(
                                to_email=customer_email,
                                story_data=story_data,
                                visor_url=visor_url,
                                is_gift=False,
                                preview_id=preview_id,
                                is_print_order=False,
                            )
                            _email_c_sent = True
                            story_data['ebook_email_sent'] = True
                            with open(preview_file, 'w', encoding='utf-8') as _ef:
                                json.dump(story_data, _ef, ensure_ascii=False, indent=2)
                            production_logger.info(f"[BG-COMPOSE] eBook permanente email sent to {customer_email}")
                        except Exception as _ebook_email_err:
                            production_logger.error(f"[BG-COMPOSE] eBook email failed: {_ebook_email_err}")
                    else:
                        production_logger.warning(f"[BG-COMPOSE] eBook email skipped — visor_url not ready for {customer_email}")
                elif want_ebook and story_data.get('ebook_email_sent'):
                    production_logger.info(f"[BG-COMPOSE] eBook email already sent for {preview_id} — skipping")
                    _email_c_sent = True

                # Admin: ALWAYS gets printable PDF (even if customer didn't buy it)
                if not story_data.get('admin_pdf_sent'):
                    try:
                        safe_name_admin = child_name.replace(' ', '_').replace("'", "")
                        admin_pdf_dir = f'generations/email/{preview_id}'
                        os.makedirs(admin_pdf_dir, exist_ok=True)
                        admin_pdf_path = f'{admin_pdf_dir}/{safe_name_admin}_imprimible.pdf'
                        if not os.path.exists(admin_pdf_path):
                            from services.personalized_books.printable_pdf import generate_personalized_printable_pdf
                            _admin_gender   = story_data.get('gender', story_data.get('child_gender', 'nino'))
                            _admin_lang     = story_data.get('lang', 'es')
                            _admin_book_id  = story_data.get('story_id', story_data.get('book_id', ''))
                            _admin_fmt      = story_data.get('print_format', 'A4')
                            from services.personalized_books.generation import get_print_title
                            _admin_pet      = (story_data.get('traits') or {}).get('pet_name', '')
                            _admin_title    = get_print_title(_admin_book_id, child_name, _admin_lang, pet_name=_admin_pet)
                            generate_personalized_printable_pdf(
                                book_session_id=preview_id,
                                child_name=child_name,
                                gender=_admin_gender,
                                language=_admin_lang,
                                book_id=_admin_book_id,
                                book_title=_admin_title,
                                output_path=admin_pdf_path,
                                print_format=_admin_fmt,
                                front_cover_path=story_data.get('front_cover_path') or None,
                                back_cover_path=story_data.get('back_cover_path') or None,
                            )
                            story_data['printable_pdf_path'] = admin_pdf_path
                            with open(preview_file, 'w', encoding='utf-8') as _f:
                                json.dump(story_data, _f, ensure_ascii=False, indent=2)
                            production_logger.info(f"[BG-COMPOSE] Admin PDF generado: {admin_pdf_path}")
                        from services.email_service import send_ebook_admin_notification
                        send_ebook_admin_notification(
                            preview_id=preview_id,
                            child_name=child_name,
                            story_name=story_data.get('story_name', ''),
                            customer_email=customer_email,
                            product_type=story_data.get('product_type', 'universo_ebook'),
                            pdf_path=admin_pdf_path,
                            visor_url=visor_url or '',
                            buyer_country=story_data.get('buyer_country', ''),
                        )
                        story_data['admin_pdf_sent'] = True
                        production_logger.info(f"[BG-COMPOSE] Admin PDF email sent")
                    except Exception as admin_pdf_err:
                        production_logger.error(f"[BG-COMPOSE] Admin PDF/notificación fallida (no crítico): {admin_pdf_err}")

                if want_ebook or want_print:
                    if _email_b_sent or _email_c_sent:
                        story_data['email_sent'] = True
                        story_data['email_sent_date'] = datetime.now().isoformat()
                        production_logger.info(f"[BG-COMPOSE] Customer emails dispatched to {customer_email} (B={_email_b_sent}, C={_email_c_sent})")
                    else:
                        production_logger.error(f"[BG-COMPOSE] No customer email was sent for {customer_email} — email_sent NOT set")
                elif want_pdf:
                    production_logger.info(f"[BG-COMPOSE] PDF-only order — customer email sent by PDF dispatch")
            except Exception as email_err:
                production_logger.error(f"[BG-COMPOSE] Email routing failed: {email_err}")
        
        story_data['scenes_pending'] = False
        story_data['scenes_generating'] = False
        story_data['book_composing'] = False
        story_data['generation_failed'] = False
        story_data['admin_notified'] = True
        
        with open(preview_file, 'w', encoding='utf-8') as f:
            json.dump(story_data, f, ensure_ascii=False, indent=2)
        
        production_logger.info(f"[BG-COMPOSE] COMPLETE for {preview_id}")
        return {'status': 'completed', 'pages': len(formatted_original)}
        
    except Exception as e:
        import traceback as tb
        tb_text = tb.format_exc()
        production_logger.error(f"[BG-COMPOSE] {preview_id} FAILED: {e}")
        production_logger.error(tb_text)

        story_data['scenes_generating'] = False
        story_data['book_composing'] = False
        story_data['generation_failed'] = True
        story_data['generation_error'] = str(e)
        with open(preview_file, 'w', encoding='utf-8') as f:
            json.dump(story_data, f, ensure_ascii=False, indent=2)

        try:
            from services.email_service import send_admin_error_email
            _is_retry_fail = story_data.get('retry_attempted', False)
            send_admin_error_email('_compose_personalized_book_background', preview_id, str(e), tb_text,
                                   story_data=story_data, is_retry_failure=_is_retry_fail)
        except Exception:
            pass

        raise


_post_payment_locks = set()
_post_payment_lock = threading.Lock()
_ebook_processing_locks = set()
_ebook_processing_lock = threading.Lock()
_pdf_dispatch_locks = set()
_pdf_dispatch_lock = threading.Lock()

def _process_personalized_book_post_payment(preview_id, customer_email):
    """
    Background thread: post-payment processing for personalized books.

    For cp_personalized: pre-generates cover.pdf + content.pdf so they are ready
    when the customer submits their shipping address via /shipping-confirm.
    Does NOT submit the CP order here — that happens in shipping_confirm.

    Uses lock to prevent duplicate concurrent processing.
    """
    with _post_payment_lock:
        if preview_id in _post_payment_locks:
            print(f"[POST-PAYMENT] Already processing {preview_id}, skipping duplicate")
            return
        _post_payment_locks.add(preview_id)

    try:
        preview_file = f'story_previews/{preview_id}.json'
        if not os.path.exists(preview_file):
            print(f"[POST-PAYMENT] Preview file not found: {preview_file}")
            return

        with open(preview_file, 'r', encoding='utf-8') as f:
            story_data = json.load(f)

        product_type = story_data.get('product_type', '')

        # ── CP Personalized Book path (photobook_cw_a4_p_fc) ──────────────────
        if product_type == 'cp_personalized':
            if story_data.get('cp_pdfs_ready') or story_data.get('cp_pb_order_ref'):
                reason = 'PDFs already ready' if story_data.get('cp_pdfs_ready') else 'order already submitted'
                print(f"[POST-PAYMENT] CP PB — {reason} for {preview_id}, skipping")
                with _post_payment_lock:
                    _post_payment_locks.discard(preview_id)
                return
            try:
                from services.personalized_books.cp_pdf_service import generate_cw_cover_pdf, generate_cw_content_pdf
                from services.personalized_books.generation import get_print_title
                lang = story_data.get('lang', story_data.get('language', 'es'))
                traits = story_data.get('traits', {})
                book_id = story_data.get('story_id', '')
                child_name = story_data.get('child_name', '')
                pet_name_g = traits.get('pet_name', '') if traits else ''
                book_title_g = get_print_title(book_id, child_name, lang, pet_name=pet_name_g)

                from services.cloudprinter_api_service import get_pb_chosen_page_count
                _chosen_pages = get_pb_chosen_page_count()
                print(f"[POST-PAYMENT] CP PB: pre-generating PDFs for {preview_id} "
                      f"(page_count={_chosen_pages})...")
                cp_out_dir = os.path.join("generations", "cloudprinter", preview_id)
                os.makedirs(cp_out_dir, exist_ok=True)
                cover_pdf_path   = os.path.join(cp_out_dir, "cover.pdf")
                content_pdf_path = os.path.join(cp_out_dir, "content.pdf")

                generate_cw_cover_pdf(
                    session_id=preview_id,
                    book_title=book_title_g,
                    output_path=cover_pdf_path,
                    page_count=_chosen_pages,
                )
                generate_cw_content_pdf(
                    session_id=preview_id,
                    child_name=child_name,
                    language=lang,
                    output_path=content_pdf_path,
                    page_count=_chosen_pages,
                )

                story_data['cp_pdfs_ready']       = True
                story_data['cp_cover_pdf_path']   = cover_pdf_path
                story_data['cp_content_pdf_path'] = content_pdf_path
                print(f"[POST-PAYMENT] CP PB PDFs pre-generated for {preview_id}.")

                # Submit CP order immediately if shipping address is already available
                existing_shipping = story_data.get('shipping_address')
                if existing_shipping and not story_data.get('cp_pb_order_ref'):
                    try:
                        from services.cloudprinter_api_service import submit_pb_print_order, get_pdf_public_url, resolve_shipping_level
                        cp_shipping_level = resolve_shipping_level(story_data.get('shipping_method', 'cp_saver'))
                        cover_pdf_url   = get_pdf_public_url(preview_id, "cover.pdf")
                        content_pdf_url = get_pdf_public_url(preview_id, "content.pdf")
                        story_data['cp_cover_pdf_url']   = cover_pdf_url
                        story_data['cp_content_pdf_url'] = content_pdf_url
                        cp_ok, cp_msg, cp_ref = submit_pb_print_order(
                            preview_id=preview_id,
                            cover_pdf_path=cover_pdf_path,
                            cover_pdf_url=cover_pdf_url,
                            content_pdf_path=content_pdf_path,
                            content_pdf_url=content_pdf_url,
                            customer_data={"email": customer_email or ""},
                            shipping_address=existing_shipping,
                            shipping_level=cp_shipping_level,
                        )
                        if cp_ok:
                            story_data['cp_pb_order_ref']  = cp_ref
                            story_data['cp_order_status']  = 'submitted'
                            print(f"[POST-PAYMENT] CP PB order submitted for {preview_id}: {cp_ref}")
                            try:
                                from services.email_service import send_cp_pb_admin_notification
                                send_cp_pb_admin_notification(
                                    preview_id=preview_id,
                                    cp_order_ref=cp_ref,
                                    title=book_title_g,
                                    customer_email=customer_email,
                                    shipping_address=existing_shipping,
                                    cover_pdf_url=cover_pdf_url,
                                    content_pdf_url=content_pdf_url,
                                    visor_url=story_data.get('visor_url', ''),
                                    paid_amount=f"${story_data.get('customer_total_usd', 0):.2f} USD" if story_data.get('customer_total_usd') else '',
                                    cp_cost_eur=float(story_data.get('cp_cost_eur', 0)),
                                    print_cost_eur=float(story_data.get('print_cost_eur', 0)),
                                )
                            except Exception as adm_err:
                                print(f"[POST-PAYMENT] CP admin notification error: {adm_err}")
                        else:
                            print(f"[POST-PAYMENT] CP PB order submission failed: {cp_msg}")
                            story_data['cp_order_error'] = cp_msg
                    except Exception as sub_err:
                        print(f"[POST-PAYMENT] CP PB order submission exception: {sub_err}")
                        import traceback; traceback.print_exc()
                else:
                    print(f"[POST-PAYMENT] CP PB shipping address not yet available for {preview_id}; "
                          f"order will be submitted at shipping-confirm step.")
            except Exception as cp_pdf_err:
                print(f"[POST-PAYMENT] CP PB PDF pre-generation failed for {preview_id}: {cp_pdf_err}")
                import traceback
                traceback.print_exc()
                story_data['cp_pdf_error'] = str(cp_pdf_err)
            finally:
                with open(preview_file, 'w', encoding='utf-8') as f:
                    json.dump(story_data, f, ensure_ascii=False, indent=2)
                with _post_payment_lock:
                    _post_payment_locks.discard(preview_id)
            return

        # ── Legacy Lulu / Gelato path ──────────────────────────────────────────
        if story_data.get('admin_notified'):
            print(f"[POST-PAYMENT] Already processed {preview_id}, skipping")
            return

    except Exception as early_err:
        print(f"[POST-PAYMENT] Early error for {preview_id}: {early_err}")
        with _post_payment_lock:
            _post_payment_locks.discard(preview_id)
        return

    from services.pdf_service import create_pdf_from_images
    from services.email_service import send_story_email_with_attachments

    try:
        with open(preview_file, 'r', encoding='utf-8') as f:
            story_data = json.load(f)

        child_name = story_data.get('child_name', 'Historia')
        safe_name = child_name.replace(' ', '_').replace("'", "")
        book_id = story_data.get('story_id', '')
        language = story_data.get('lang', story_data.get('language', 'es'))

        print(f"[POST-PAYMENT] Processing {preview_id} for {child_name} ({customer_email})")

        all_pages = (
            story_data.get('original_images')
            or story_data.get('all_pages_original')
            or story_data.get('original_scene_paths', [])
        )
        front_cover = story_data.get('original_cover', story_data.get('front_cover_path', ''))
        back_cover = story_data.get('back_cover_path', '')

        if front_cover and front_cover.startswith('/'):
            front_cover = front_cover[1:]
        if back_cover and back_cover.startswith('/'):
            back_cover = back_cover[1:]

        if not back_cover or not os.path.exists(back_cover):
            fixed_back_covers = {
                "dragon_garden": "static/images/fixed_pages/_backup/dragon_garden_back_cover.png",
                "magic_chef": "static/images/fixed_pages/magic_chef_back_cover.png",
                "magic_inventor": "static/images/fixed_pages/magic_inventor_back_cover.png",
                "star_keeper": "static/images/fixed_pages/_backup/star_keeper_back_cover.png",
                "furry_love": "static/images/fixed_pages/_backup/furry_love_baby_back_cover.png",
                "furry_love_adventure": "static/images/fixed_pages/_backup/furry_love_adventure_back_cover.png",
                "furry_love_teen": "static/images/fixed_pages/_backup/furry_love_teen_back_cover.png",
                "furry_love_adult": "static/images/fixed_pages/_backup/furry_love_adult_back_cover.png",
                "centinela_aurora": "static/images/fixed_pages/_backup/centinela_aurora_back_cover.png"
            }
            back_cover = fixed_back_covers.get(book_id, 'static/images/fixed_pages/back_cover.png')

        os.makedirs(f'generations/email/{preview_id}', exist_ok=True)

        pdf_digital_path = f'generations/email/{preview_id}/{safe_name}_digital.pdf'
        if all_pages:
            pdf_pages = []
            if front_cover and os.path.exists(front_cover):
                pdf_pages.append(front_cover)
            pdf_pages.extend(all_pages)
            if back_cover and os.path.exists(back_cover):
                pdf_pages.append(back_cover)

            clean_pages = []
            for p in pdf_pages:
                p = p.lstrip('/')
                clean_pages.append(p)

            print(f"[POST-PAYMENT] Creating digital PDF with {len(clean_pages)} pages")
            create_pdf_from_images(clean_pages, pdf_digital_path, skip_sanitize=True)
        else:
            print(f"[POST-PAYMENT] WARNING: No original images found for {preview_id}")
            pdf_digital_path = None

        story_data['assets_ready'] = True
        story_data['files_generated'] = {
            'pdf_digital': pdf_digital_path,
        }

        with open(preview_file, 'w', encoding='utf-8') as f:
            json.dump(story_data, f, ensure_ascii=False, indent=2)

        print(f"[POST-PAYMENT] Assets prepared for {preview_id} — digital PDF (visor): {pdf_digital_path}")

    except Exception as e:
        print(f"[POST-PAYMENT] ERROR for {preview_id}: {e}")
        import traceback
        traceback.print_exc()
        try:
            with open(preview_file, 'r', encoding='utf-8') as f:
                story_data = json.load(f)
            story_data['post_payment_error'] = str(e)
            story_data['post_payment_error_date'] = datetime.now().isoformat()
            with open(preview_file, 'w', encoding='utf-8') as f:
                json.dump(story_data, f, ensure_ascii=False, indent=2)
        except:
            pass
    finally:
        with _post_payment_lock:
            _post_payment_locks.discard(preview_id)


def _dispatch_printable_pdf_email(preview_id, customer_email, lang='es'):
    """
    Background thread: wait for book composition to complete,
    generate an A4 printable PDF + instructions PDF, and deliver
    them as email attachments to the customer. Also notifies pay@ admin.
    """
    import time as _pdf_time
    with _pdf_dispatch_lock:
        if preview_id in _pdf_dispatch_locks:
            print(f"[PDF-DISPATCH] Duplicate call suppressed (in-flight) for {preview_id}")
            return
        _pdf_dispatch_locks.add(preview_id)
    preview_file = f'story_previews/{preview_id}.json'
    if os.path.exists(preview_file):
        try:
            with open(preview_file, 'r', encoding='utf-8') as _f:
                _sd = json.load(_f)
            if _sd.get('printable_pdf_sent') and _sd.get('printable_pdf_admin_sent'):
                print(f"[PDF-DISPATCH] Already delivered for {preview_id} — skipping (persisted idempotency)")
                with _pdf_dispatch_lock:
                    _pdf_dispatch_locks.discard(preview_id)
                return
        except Exception:
            pass
    print(f"[PDF-DISPATCH] Starting PDF delivery for {preview_id} → {customer_email}")

    max_wait = 900
    wait_interval = 5
    waited = 0
    while waited < max_wait:
        if not os.path.exists(preview_file):
            _pdf_time.sleep(wait_interval)
            waited += wait_interval
            continue
        with open(preview_file, 'r', encoding='utf-8') as f:
            story_data = json.load(f)
        if story_data.get('pages_composed', False):
            print(f"[PDF-DISPATCH] Composition done for {preview_id}, continuing...")
            break
        _pdf_time.sleep(wait_interval)
        waited += wait_interval
    else:
        print(f"[PDF-DISPATCH] Timed out waiting for composition for {preview_id}")
        with _pdf_dispatch_lock:
            _pdf_dispatch_locks.discard(preview_id)
        return

    try:
        with open(preview_file, 'r', encoding='utf-8') as f:
            story_data = json.load(f)

        book_id    = story_data.get('story_id', '')
        child_name = story_data.get('child_name', '')
        gender     = story_data.get('gender', story_data.get('child_gender', 'nino'))
        lang       = story_data.get('lang', lang)

        from services.personalized_books.generation import get_print_title
        pet_name   = (story_data.get('traits') or {}).get('pet_name', '')
        book_title = get_print_title(book_id, child_name, lang, pet_name=pet_name)

        _fc_path = story_data.get('front_cover_path', '') or ''
        _bc_path = story_data.get('back_cover_path', '') or ''

        from services.personalized_books.printable_pdf import generate_personalized_printable_pdf
        printable_pdf_path = None
        for _attempt in range(2):
            try:
                printable_pdf_path = generate_personalized_printable_pdf(
                    book_session_id=preview_id,
                    child_name=child_name,
                    gender=gender,
                    language=lang,
                    book_id=book_id,
                    book_title=book_title,
                    force_regenerate=(_attempt > 0),
                    front_cover_path=_fc_path or None,
                    back_cover_path=_bc_path or None,
                    print_format=story_data.get('print_format', 'A4'),
                )
                print(f"[PDF-DISPATCH] Printable PDF generated (attempt {_attempt + 1}, format={story_data.get('print_format','A4')}): {printable_pdf_path}")
                break
            except Exception as _pdf_err:
                print(f"[PDF-DISPATCH] PDF generation attempt {_attempt + 1} failed for {preview_id}: {_pdf_err}")
                if _attempt == 0:
                    _pdf_time.sleep(10)
        if not printable_pdf_path:
            raise RuntimeError(f"Failed to generate printable PDF after 2 attempts for {preview_id}")

        base_url  = (os.environ.get('SITE_DOMAIN')
                     or os.environ.get('REPLIT_DEV_DOMAIN')
                     or 'magicmemoriesbooks.com')
        pdf_filename = os.path.basename(printable_pdf_path)
        visor_url = story_data.get('visor_url', '')
        # Include gift eBook only when the customer did NOT separately purchase the eBook
        # AND did NOT also buy the printed book — if want_print is true, the print
        # confirmation flow (Email B2) owns sending the single gift eBook email to
        # avoid sending two "gift eBook" emails for the same story when PDF + print
        # are bought together.
        _include_gift = not story_data.get('want_ebook', False) and not story_data.get('want_print', False)

        local_pdf_path = printable_pdf_path
        if not os.path.exists(local_pdf_path):
            raise FileNotFoundError(f"[PDF-DISPATCH] PDF not found at expected path: {local_pdf_path}")

        instructions_path = None
        try:
            instructions_dir = os.path.join('generated', 'gelato', preview_id)
            os.makedirs(instructions_dir, exist_ok=True)
            instructions_path = os.path.join(instructions_dir, f'{preview_id}_instrucciones.pdf')
            from services.pdf_service import generate_print_instructions_pdf
            generate_print_instructions_pdf(instructions_path, language=lang, print_format=story_data.get('print_format', 'A4'))
            print(f"[PDF-DISPATCH] Print instructions PDF generated: {instructions_path}")
        except Exception as _instr_err:
            print(f"[PDF-DISPATCH] WARNING: could not generate instructions PDF: {_instr_err}")
            instructions_path = None

        pdf_url = f"https://{base_url}/preview-pdf/printable/{preview_id}/{pdf_filename}"

        story_data['printable_pdf_path'] = printable_pdf_path
        story_data['pdf_printable_path'] = printable_pdf_path   # alias usado por download-book route
        story_data['printable_pdf_url']  = pdf_url
        with open(preview_file, 'w', encoding='utf-8') as f:
            json.dump(story_data, f, ensure_ascii=False, indent=2)

        from services.email_service import (
            send_story_email_with_attachments,
            send_personalized_pdf_admin_email,
        )
        customer_sent = False
        if customer_email:
            customer_result = send_story_email_with_attachments(
                to_email=customer_email,
                story_data=story_data,
                pdf_printable_path=local_pdf_path,
                instructions_path=instructions_path,
                age_group='personalized',
                preview_id=preview_id,
                visor_url=visor_url if _include_gift else None,
                is_pdf_purchase=_include_gift,
                give_gift_ebook=_include_gift,
            )
            customer_sent = customer_result.get('success', False)
            print(f"[PDF-DISPATCH] Customer PDF email {'sent' if customer_sent else 'FAILED'} for {customer_email} (gift_ebook={_include_gift})")

            # --- SHADOW MODE (Fase 0, solo lectura/registro, no afecta el envio real) ---
            try:
                from services.shadow_delivery import run_shadow_comparison_safe
                _actual_planned = ['pdf_ready']
                if _include_gift:
                    _actual_planned.append('gift_ebook_temp_6mo')
                run_shadow_comparison_safe(
                    stage='dispatch_printable_pdf_email',
                    story_data=story_data,
                    preview_id=preview_id,
                    actual_decision={'planned_emails': _actual_planned, 'include_gift': _include_gift},
                )
            except Exception as _shadow_call_err:
                print(f"[SHADOW-DELIVERY] WARNING: shadow hook failed non-fatally: {_shadow_call_err}")
            # --- FIN SHADOW MODE ---

            # Dedicated gift eBook email so customer gets a standalone visor-access email
            if _include_gift and visor_url and not story_data.get('gift_ebook_sent'):
                try:
                    from services.email_service import send_ebook_email
                    send_ebook_email(
                        to_email=customer_email,
                        story_data=story_data,
                        visor_url=visor_url,
                        is_gift=True,
                        preview_id=preview_id,
                        is_print_order=False,
                    )
                    story_data['gift_ebook_sent'] = True
                    print(f"[PDF-DISPATCH] Dedicated gift eBook email sent to {customer_email}")
                except Exception as _ebook_err:
                    print(f"[PDF-DISPATCH] Dedicated gift eBook email failed: {_ebook_err}")
            elif _include_gift and story_data.get('gift_ebook_sent'):
                print(f"[PDF-DISPATCH] Gift eBook already sent for {preview_id} — skipping")

        admin_result = send_personalized_pdf_admin_email(
            preview_id=preview_id,
            customer_email=customer_email or '(unknown)',
            book_title=book_title,
            pdf_url=pdf_url,
            visor_url=visor_url,
            child_name=child_name,
            book_id=book_id,
            customer_email_sent=customer_sent,
        )
        admin_sent = admin_result.get('success', False)
        print(f"[PDF-DISPATCH] Admin notification {'sent' if admin_sent else 'FAILED'} for {preview_id}")

        story_data['printable_pdf_sent']       = customer_sent
        story_data['printable_pdf_admin_sent'] = admin_sent
        if customer_sent:
            story_data['pdf_email_sent'] = True
            story_data['email_sent'] = True
            story_data['email_sent_date'] = datetime.now().isoformat()
            print(f"[PDF-DISPATCH] email_sent + pdf_email_sent flags set for {preview_id}")
        with open(preview_file, 'w', encoding='utf-8') as f:
            json.dump(story_data, f, ensure_ascii=False, indent=2)

    except Exception as e:
        print(f"[PDF-DISPATCH] Error generating/sending printable PDF for {preview_id}: {e}")
        import traceback
        print(traceback.format_exc())
    finally:
        with _pdf_dispatch_lock:
            _pdf_dispatch_locks.discard(preview_id)


def _process_ebook_generation(preview_id, customer_email, send_email=True):
    """
    Background thread: prepare visor files, generate printable PDF + instructions,
    and send email with visor link + PDF attachments.
    Waits for scene generation to complete before uploading visor and sending email.
    Uses lock to prevent duplicate processing from process_payment + webhook race condition.
    """
    with _ebook_processing_lock:
        if preview_id in _ebook_processing_locks:
            print(f"[EBOOK] Already being processed by another thread for {preview_id}, skipping")
            return
        _ebook_processing_locks.add(preview_id)
    
    try:
        preview_file = f'story_previews/{preview_id}.json'
        if not os.path.exists(preview_file):
            print(f"[EBOOK] Preview file not found: {preview_file}")
            return
        
        with open(preview_file, 'r', encoding='utf-8') as f:
            story_data = json.load(f)
        
        _story_id_early = story_data.get('story_id', '')
        from services.quick_stories.checkout import is_quick_story as _check_qs_early
        _is_qs_for_retry = _check_qs_early(_story_id_early)

        def _qs_emails_pending(sd):
            return (
                (sd.get('want_pdf')   and not sd.get('pdf_email_sent'))   or
                (sd.get('want_ebook') and not sd.get('ebook_email_sent')) or
                ((sd.get('want_pdf') or sd.get('want_print')) and not sd.get('gift_ebook_sent'))
            )

        if story_data.get('visor_uploaded'):
            if _is_qs_for_retry and _qs_emails_pending(story_data):
                print(f"[EBOOK] QS visor uploaded but emails pending for {preview_id} — continuing to email dispatch")
            else:
                print(f"[EBOOK] Already uploaded to visor for {preview_id}, skipping")
                return

        import time as _ebook_time
        max_wait = 600
        wait_interval = 3
        waited = 0
        while waited < max_wait:
            qs_task = task_queue.get_status(f"scene_gen_{preview_id}")
            if qs_task and qs_task.get('status') == 'completed':
                print(f"[EBOOK] Scene generation task completed for {preview_id} (waited {waited}s)")
                break
            if qs_task and qs_task.get('status') == 'failed':
                print(f"[EBOOK] Scene generation task failed for {preview_id} (waited {waited}s), proceeding anyway")
                break
            with open(preview_file, 'r', encoding='utf-8') as f:
                story_data = json.load(f)
            scenes_pending = story_data.get('scenes_pending', False)
            scenes_generating = story_data.get('scenes_generating', False)
            qs_text_composed = story_data.get('qs_text_composed', False)
            if not scenes_pending and not scenes_generating and qs_text_composed:
                print(f"[EBOOK] Scenes ready (flags) for {preview_id} (waited {waited}s)")
                break
            if not qs_task and not scenes_pending and not scenes_generating and waited > 30:
                print(f"[EBOOK] No task found and no pending flags for {preview_id} (waited {waited}s), proceeding")
                break
            task_state = qs_task.get('status') if qs_task else 'not_found'
            print(f"[EBOOK] Waiting for {preview_id} ({waited}s elapsed, task={task_state}, pending={scenes_pending}, text_composed={qs_text_composed})")
            _ebook_time.sleep(wait_interval)
            waited += wait_interval

        if waited >= max_wait:
            print(f"[EBOOK] WARNING: Timed out waiting after {max_wait}s for {preview_id}, proceeding anyway")
        
        with open(preview_file, 'r', encoding='utf-8') as f:
            story_data = json.load(f)
        
        if story_data.get('visor_uploaded'):
            if _is_qs_for_retry and _qs_emails_pending(story_data):
                print(f"[EBOOK] QS visor uploaded while waiting, emails still pending for {preview_id} — continuing")
            else:
                print(f"[EBOOK] Already uploaded to visor for {preview_id} (uploaded while waiting), skipping")
                return

        is_gift = story_data.get('ebook_is_gift', False)
        product_type = story_data.get('product_type', '')
        story_id = story_data.get('story_id', '')

        from services.quick_stories.checkout import is_quick_story as check_qs
        is_qs = check_qs(story_id)

        if story_data.get('visor_uploaded'):
            visor_url = story_data.get('visor_url', '')
            book_uuid = story_data.get('visor_book_uuid', '')
            print(f"[EBOOK] Using existing visor URL for {preview_id}: {visor_url}")
        else:
            print(f"[EBOOK] Preparing visor upload for {preview_id} (is_gift={is_gift}, is_qs={is_qs})")
            from services.vps_upload_service import prepare_and_upload
            result = prepare_and_upload(story_data, preview_id, is_gift=is_gift)
            visor_url = result.get('visor_url', '')
            book_uuid = result.get('book_uuid', '')
            story_data['visor_url'] = visor_url
            story_data['visor_book_uuid'] = book_uuid
            story_data['visor_uploaded'] = True
            story_data['visor_upload_date'] = datetime.now().isoformat()
            with open(preview_file, 'w', encoding='utf-8') as f:
                json.dump(story_data, f, ensure_ascii=False, indent=2)
            print(f"[EBOOK] Visor uploaded: {visor_url}")
        
        if is_qs and not send_email:
            print(f"[EBOOK] Visor uploaded for {preview_id} — skipping email (waiting for user approval)")
            return

        if is_qs and send_email:
            with open(preview_file, 'r', encoding='utf-8') as f:
                story_data = json.load(f)
            
            _want_pdf   = story_data.get('want_pdf', False)
            _want_ebook = story_data.get('want_ebook', False)
            _want_print = story_data.get('want_print', False)
            _lang       = story_data.get('lang', 'es')
            _child_name = story_data.get('child_name', 'Historia')
            _safe_name  = _child_name.replace(' ', '_').replace("'", "")
            _email      = customer_email or story_data.get('customer_email', '')

            print(f"[EBOOK] QS atomic emails — want_pdf={_want_pdf}, want_ebook={_want_ebook}, want_print={_want_print}, email={bool(_email)}")

            if _want_pdf and _email:
                try:
                    _qs_fmt = story_data.get('print_format', 'A4')
                    if _qs_fmt and _qs_fmt.upper() in ('CARTA', 'LETTER'):
                        _qs_fmt = 'LETTER'
                    else:
                        _qs_fmt = 'A4'
                    _fmt_sfx = 'LETTER' if _qs_fmt == 'LETTER' else 'A4'
                    _output_dir = f'generations/email/{preview_id}'
                    os.makedirs(_output_dir, exist_ok=True)
                    _pdf_path = f'{_output_dir}/{_safe_name}_imprimible_{_fmt_sfx}.pdf'
                    # Reuse existing PDF rather than regenerating from FLUX
                    _existing = story_data.get('pdf_printable_path', '')
                    if _existing and os.path.exists(_existing):
                        _pdf_path = _existing
                        print(f"[EBOOK] Reusing existing PDF: {_pdf_path}")
                    elif os.path.exists(_pdf_path):
                        print(f"[EBOOK] Reusing existing PDF at expected path: {_pdf_path}")
                    else:
                        from services.quick_stories.pdf_service import generate_quick_story_pdf
                        generate_quick_story_pdf(story_data, _pdf_path, print_format=_qs_fmt, format_type='digital')
                        print(f"[EBOOK] Printable PDF generated ({_qs_fmt})")
                    from services.pdf_service import generate_print_instructions_pdf
                    _instr_path = f'{_output_dir}/instrucciones_impresion.pdf'
                    if not os.path.exists(_instr_path):
                        generate_print_instructions_pdf(_instr_path, language=_lang, print_format=_qs_fmt)
                    print(f"[EBOOK] Printable PDF generated ({_qs_fmt}): {_pdf_path}")
                    from services.email_service import send_story_email_with_attachments
                    send_story_email_with_attachments(
                        to_email=_email,
                        story_data=story_data,
                        pdf_printable_path=_pdf_path,
                        instructions_path=_instr_path,
                        preview_id=preview_id,
                    )
                    print(f"[EBOOK] PDF imprimible email sent to {_email}")
                    try:
                        from services.email_service import send_ebook_admin_notification
                        send_ebook_admin_notification(
                            preview_id=preview_id,
                            child_name=_child_name,
                            story_name=story_data.get('story_name', ''),
                            customer_email=_email,
                            product_type=product_type or 'qs_digital',
                            pdf_path=_pdf_path,
                            visor_url=visor_url,
                            buyer_country=story_data.get('buyer_country', ''),
                        )
                    except Exception as _adm_err:
                        print(f"[EBOOK] Admin notification failed (non-fatal): {_adm_err}")
                    with open(preview_file, 'r', encoding='utf-8') as f:
                        story_data = json.load(f)
                    story_data['pdf_printable_path'] = _pdf_path
                    story_data['instructions_path'] = _instr_path
                    story_data['pdf_email_sent'] = True
                    with open(preview_file, 'w', encoding='utf-8') as f:
                        json.dump(story_data, f, ensure_ascii=False, indent=2)
                except Exception as _pdf_err:
                    print(f"[EBOOK] PDF email failed (non-fatal): {_pdf_err}")
                    import traceback
                    traceback.print_exc()

            if _want_ebook and visor_url and _email and not story_data.get('ebook_email_sent'):
                try:
                    from services.email_service import send_ebook_email
                    send_ebook_email(
                        to_email=_email,
                        story_data=story_data,
                        visor_url=visor_url,
                        is_gift=False,
                        preview_id=preview_id,
                    )
                    print(f"[EBOOK] Permanent eBook email sent to {_email}")
                    with open(preview_file, 'r', encoding='utf-8') as f:
                        story_data = json.load(f)
                    story_data['ebook_email_sent'] = True
                    with open(preview_file, 'w', encoding='utf-8') as f:
                        json.dump(story_data, f, ensure_ascii=False, indent=2)
                except Exception as _ebook_err:
                    print(f"[EBOOK] Permanent eBook email failed (non-fatal): {_ebook_err}")

            if (_want_pdf or _want_print) and visor_url and _email and not story_data.get('gift_ebook_sent') and not story_data.get('ebook_email_sent'):
                try:
                    from services.email_service import send_ebook_email
                    send_ebook_email(
                        to_email=_email,
                        story_data=story_data,
                        visor_url=visor_url,
                        is_gift=True,
                        preview_id=preview_id,
                    )
                    print(f"[EBOOK] Gift eBook email sent to {_email}")
                    with open(preview_file, 'r', encoding='utf-8') as f:
                        story_data = json.load(f)
                    story_data['gift_ebook_sent'] = True
                    with open(preview_file, 'w', encoding='utf-8') as f:
                        json.dump(story_data, f, ensure_ascii=False, indent=2)
                except Exception as _gift_err:
                    print(f"[EBOOK] Gift eBook email failed (non-fatal): {_gift_err}")

            with open(preview_file, 'r', encoding='utf-8') as f:
                story_data = json.load(f)
            if not _qs_emails_pending(story_data):
                story_data['email_sent'] = True
                with open(preview_file, 'w', encoding='utf-8') as f:
                    json.dump(story_data, f, ensure_ascii=False, indent=2)
                print(f"[EBOOK] All QS emails delivered, email_sent=True for {preview_id}")

        with open(preview_file, 'r', encoding='utf-8') as f:
            story_data = json.load(f)
        story_data['assets_ready'] = True
        with open(preview_file, 'w', encoding='utf-8') as f:
            json.dump(story_data, f, ensure_ascii=False, indent=2)

        print(f"[EBOOK] Processing complete for {preview_id}")

    except Exception as e:
        import traceback as tb
        tb_text = tb.format_exc()
        print(f"[EBOOK] ERROR for {preview_id}: {e}")
        print(tb_text)
        try:
            preview_file = os.path.join('generations', 'previews', f'{preview_id}.json')
            with open(preview_file, 'r', encoding='utf-8') as f:
                sd = json.load(f)
            sd['visor_error'] = str(e)
            with open(preview_file, 'w', encoding='utf-8') as f:
                json.dump(sd, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
        try:
            from services.email_service import send_admin_error_email
            _sd_err = locals().get('story_data', None)
            _is_retry_ebook = bool(_sd_err.get('retry_attempted', False)) if _sd_err else False
            send_admin_error_email('_process_ebook_generation', preview_id, str(e), tb_text,
                                   story_data=_sd_err, is_retry_failure=_is_retry_ebook)
        except Exception:
            pass
    finally:
        with _ebook_processing_lock:
            _ebook_processing_locks.discard(preview_id)


def _process_quick_story_print(preview_id, customer_email):
    """
    Background thread: generate Cloudprinter PDF for Quick Story saddle-stitch printing.
    Called when want_print=true after payment.
    Product: magazine_sas_a4_p_fc (210×297mm A4, 16 pages saddle-stitch)
    """
    from services.quick_stories.pdf_service import generate_quick_story_cloudprinter_pdf
    from services.cloudprinter_api_service import submit_print_order as cp_submit, get_pdf_public_url
    from services.email_service import send_cp_order_notification, send_cp_failure_email, send_cp_failure_admin_email

    preview_file = f'story_previews/{preview_id}.json'
    cp_folder = f'generations/cloudprinter/{preview_id}'

    try:
        if not os.path.exists(preview_file):
            print(f"[QS-PRINT] Preview file not found: {preview_file}")
            return

        with open(preview_file, 'r', encoding='utf-8') as f:
            story_data = json.load(f)

        if story_data.get('cp_submitted'):
            print(f"[QS-PRINT] Already submitted to Cloudprinter for {preview_id}, skipping")
            return

        child_name = story_data.get('child_name', 'Historia')
        story_name = story_data.get('story_name', 'Quick Story')
        shipping_address = story_data.get('shipping_address', {})
        qs_lang = story_data.get('lang', story_data.get('language', 'es'))
        is_admin_gift_qs = story_data.get('admin_gift', False)
        story_id = story_data.get('story_id', '')
        is_birthday = story_id.startswith('birthday_celebration_')
        log_prefix = "[QS-PRINT-BIRTHDAY]" if is_birthday else "[QS-PRINT]"

        print(f"{log_prefix} Processing Quick Story print for {preview_id} ({child_name})")

        scene_paths = story_data.get('scene_paths', story_data.get('images', story_data.get('original_scene_paths', [])))
        cover_image = story_data.get('original_cover', story_data.get('front_cover_path', story_data.get('cover_image', '')))

        if cover_image and cover_image.startswith('/'):
            cover_image = cover_image[1:]

        clean_scenes = []
        for p in scene_paths:
            if p and isinstance(p, str):
                clean_scenes.append(p.lstrip('/'))

        if not clean_scenes:
            print(f"{log_prefix} No scene images found for {preview_id}")
            return

        os.makedirs(cp_folder, exist_ok=True)
        pdf_output = os.path.join(cp_folder, 'book.pdf')

        print(f"{log_prefix} Generating Cloudprinter PDF: {len(clean_scenes)} scenes")
        pdf_path = generate_quick_story_cloudprinter_pdf(
            story_data=story_data,
            images=clean_scenes,
            front_cover_path=cover_image,
            output_path=pdf_output
        )
        print(f"{log_prefix} PDF generated: {pdf_path}")

        pdf_url = get_pdf_public_url(preview_id, 'book.pdf')
        print(f"{log_prefix} PDF URL: {pdf_url}")

        cp_success = False
        cp_order_ref = None
        cp_msg = ''

        if shipping_address and shipping_address.get('name') and shipping_address.get('street1') and not is_admin_gift_qs:
            print(f"{log_prefix} Submitting to Cloudprinter for {preview_id}")
            cp_success, cp_msg, cp_order_ref = cp_submit(
                preview_id=preview_id,
                pdf_path=pdf_path,
                pdf_url=pdf_url,
                customer_data={'email': customer_email or ''},
                shipping_address=shipping_address
            )
            print(f"{log_prefix} CP result: success={cp_success}, ref={cp_order_ref}, msg={cp_msg}")
        elif is_admin_gift_qs:
            print(f"{log_prefix} Admin gift order — skipping CP submission, PDF available at {pdf_url}")
            cp_order_ref = 'ADMIN-GIFT'
            cp_success = True
        else:
            print(f"{log_prefix} WARNING: No valid shipping address, skipping CP submission")

        qs_book_title = f"{story_name} - {child_name} (Quick Story Print)"
        cp_cost_eur = story_data.get('cp_cost_eur', 0)
        print_cost_eur = story_data.get('print_cost_eur', 0)
        customer_total_usd = story_data.get('customer_total_usd', 0)
        if is_admin_gift_qs:
            admin_result = {'success': True, 'simulated': True}
            print(f"{log_prefix} Admin gift — skipping CP notification emails")
        else:
            admin_result = send_cp_order_notification(
                preview_id=preview_id,
                cp_order_ref=cp_order_ref or 'N/A',
                title=qs_book_title,
                customer_email=customer_email,
                shipping_address=shipping_address,
                pdf_url=pdf_url,
                cp_cost_eur=cp_cost_eur,
                print_cost_eur=print_cost_eur,
                customer_total_usd=customer_total_usd,
                cp_success=cp_success,
                cp_error=cp_msg if not cp_success else ''
            )
        with open(preview_file, 'r', encoding='utf-8') as f:
            story_data = json.load(f)

        story_data['cp_submitted'] = cp_success
        story_data['cp_submitted_date'] = datetime.now().isoformat()
        story_data['cp_order_ref'] = cp_order_ref
        story_data['cp_pdf_url'] = pdf_url
        story_data['cp_needs_refresh'] = False
        story_data['admin_notified'] = admin_result.get('success', False) or admin_result.get('simulated', False)

        if cp_success:
            story_data['cp_status'] = 'sent'
            story_data['cp_order_ref'] = cp_order_ref
            if customer_email and not is_admin_gift_qs:
                try:
                    from services.email_service import send_print_order_confirmation_email
                    send_print_order_confirmation_email(
                        to_email=customer_email,
                        story_data=story_data,
                        preview_id=preview_id,
                    )
                    story_data['print_confirmation_sent'] = True
                    print(f"{log_prefix} Customer print confirmation email sent to {customer_email}")
                except Exception as _cust_email_err:
                    print(f"{log_prefix} Customer print email failed: {_cust_email_err}")
        elif shipping_address and shipping_address.get('name'):
            story_data['cp_status'] = 'failed'
            story_data['cp_error'] = cp_msg or 'Unknown error'
            if customer_email:
                try:
                    send_cp_failure_email(
                        to_email=customer_email,
                        child_name=child_name,
                        error_message=cp_msg or 'Unknown error',
                        lang=qs_lang,
                        preview_id=preview_id
                    )
                except Exception as fail_email_err:
                    print(f"[QS-PRINT] Failed to send CP failure email: {fail_email_err}")
            try:
                send_cp_failure_admin_email(
                    preview_id=preview_id,
                    child_name=child_name,
                    error_message=cp_msg or 'Unknown error',
                    customer_email=customer_email or '',
                    shipping_address=shipping_address,
                    story_id=story_id,
                    product_type='Quick Story Print'
                )
            except Exception as admin_fail_err:
                print(f"[QS-PRINT] Failed to send CP failure ADMIN email: {admin_fail_err}")

        with open(preview_file, 'w', encoding='utf-8') as f:
            json.dump(story_data, f, ensure_ascii=False, indent=2)

        print(f"{log_prefix} COMPLETE for {preview_id}")
        print(f"{log_prefix}   CP order ref: {cp_order_ref}")
        print(f"{log_prefix}   PDF URL: {pdf_url}")
        print(f"{log_prefix}   Admin notified: {story_data.get('admin_notified')}")

    except Exception as e:
        print(f"[QS-PRINT] ERROR for {preview_id}: {e}")
        import traceback
        traceback.print_exc()
        try:
            with open(preview_file, 'r', encoding='utf-8') as f:
                story_data = json.load(f)
            story_data['qs_print_error'] = str(e)
            story_data['qs_print_error_date'] = datetime.now().isoformat()
            with open(preview_file, 'w', encoding='utf-8') as f:
                json.dump(story_data, f, ensure_ascii=False, indent=2)
        except:
            pass
        try:
            from services.email_service import send_cp_failure_admin_email as _admin_fail
            _admin_fail(
                preview_id=preview_id,
                child_name=story_data.get('child_name', preview_id) if isinstance(story_data, dict) else preview_id,
                error_message=f"Error crítico en generación/envío: {e}",
                customer_email=customer_email or '',
                shipping_address=story_data.get('shipping_address', {}) if isinstance(story_data, dict) else {},
                product_type='Quick Story Print - ERROR CRÍTICO'
            )
        except Exception as notify_err:
            print(f"[QS-PRINT] Failed to send critical error admin email: {notify_err}")




# ── Print Order Routes ────────────────────────────────────────────────────────

@app.route('/print-order/<preview_id>')
def print_order_page(preview_id):
    lang = session.get('lang', 'es')
    preview_file = f'story_previews/{preview_id}.json'
    child_name = 'tu hijo/a'
    email = ''
    is_qs = False
    print_product_type = 'cp_personalized'
    if os.path.exists(preview_file):
        with open(preview_file, 'r', encoding='utf-8') as f:
            story_data = json.load(f)
        child_name = story_data.get('child_name', child_name)
        email = story_data.get('customer_email', '')
        is_qs = not story_data.get('is_illustrated_book', False)
        print_product_type = story_data.get('print_product_type', 'cp_personalized' if not is_qs else 'qs_print')
    from config import Config as C
    if is_qs:
        base_price = round(C.QS_PRINT_BASE_PRICE / 100.0, 2)
        print_product_type = 'qs_print'
    elif print_product_type == 'cp_personalized':
        base_price = round(C.CP_PB_BASE_PRICE / 100.0, 2)
    else:
        base_price = round(C.PERSONALIZED_BASE_PRICE / 100.0, 2)
    return render_template('print_order.html',
        lang=lang,
        preview_id=preview_id,
        child_name=child_name,
        email=email,
        base_price=base_price,
        is_qs=is_qs,
        print_product_type=print_product_type,
        paypal_client_id=Config.PAYPAL_CLIENT_ID
    )

@app.route('/print-order-success')
def print_order_success():
    lang = session.get('lang', 'es')
    email = request.args.get('email', '')
    return render_template('print_order_success.html', lang=lang, email=email)

@app.route('/api/paypal/create-print-order', methods=['POST'])
def paypal_create_print_order():
    try:
        data = request.get_json()
        amount = round(float(data.get('amount_usd', 0)), 2)
        if amount <= 0:
            return jsonify({'error': 'Invalid amount'}), 400
        token = _get_paypal_access_token()
        import requests as req_lib
        order_payload = {
            'intent': 'CAPTURE',
            'purchase_units': [{'amount': {'currency_code': 'USD', 'value': f'{amount:.2f}'}, 'description': 'Libro Impreso 21×21 cm - Magic Memories Books'}],
            'application_context': {
                'brand_name': 'Magic Memories Books',
                'shipping_preference': 'NO_SHIPPING'
            }
        }
        resp = req_lib.post(
            f"{Config.PAYPAL_API_BASE}/v2/checkout/orders",
            headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
            json=order_payload,
            timeout=15
        )
        order = resp.json()
        if 'id' not in order:
            return jsonify({'error': order.get('message', 'PayPal error')}), 400
        return jsonify({'id': order['id']})
    except Exception as e:
        print(f"[PAYPAL] create-print-order error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/paypal/capture-print-order', methods=['POST'])
def paypal_capture_print_order():
    try:
        data = request.get_json()
        order_id = data.get('orderID')
        if not order_id:
            return jsonify({'error': 'Missing orderID'}), 400
        token = _get_paypal_access_token()
        import requests as req_lib
        resp = req_lib.post(
            f"{Config.PAYPAL_API_BASE}/v2/checkout/orders/{order_id}/capture",
            headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
            timeout=15
        )
        result = resp.json()
        status = result.get('status', '')
        if status != 'COMPLETED':
            return jsonify({'error': f'Payment not completed: {status}'}), 400
        capture = result.get('purchase_units', [{}])[0].get('payments', {}).get('captures', [{}])[0]
        amount_paid = float(capture.get('amount', {}).get('value', 0))
        payer_email = result.get('payer', {}).get('email_address', data.get('email', ''))
        pr = PrintOrderRequest(
            preview_id=data.get('preview_id', ''),
            child_name=data.get('child_name', ''),
            customer_email=data.get('email', payer_email),
            paypal_order_id=order_id,
            amount_paid=amount_paid,
            shipping_name=data.get('shipping_name', ''),
            shipping_street=data.get('shipping_street', ''),
            shipping_city=data.get('shipping_city', ''),
            shipping_state=data.get('shipping_state', ''),
            shipping_postal=data.get('shipping_postal', ''),
            shipping_country=data.get('shipping_country', 'ES'),
            shipping_phone=data.get('shipping_phone', ''),
            shipping_method=data.get('shipping_method', 'MAIL'),
            shipping_cost=round(float(data.get('shipping_cost', 0)), 2),
            status='payment_confirmed'
        )
        db.session.add(pr)
        db.session.commit()
        try:
            from services.email_service import register_purchase_for_follow_up as _reg_fu
            _prf_lang = 'es'
            _prf_story_name = ''
            _prf_file = f'story_previews/{pr.preview_id}.json'
            if os.path.exists(_prf_file):
                with open(_prf_file, 'r', encoding='utf-8') as _f:
                    _prf_sd = json.load(_f)
                    _prf_lang = _prf_sd.get('lang', 'es')
                    _prf_story_name = _prf_sd.get('story_name', _prf_sd.get('title', ''))
            _reg_fu(pr.preview_id, pr.customer_email, pr.child_name, _prf_lang,
                    story_name=_prf_story_name)
        except Exception as _fu_err:
            print(f"[LEAD] register_purchase_for_follow_up error: {_fu_err}")
        _po_is_qs = data.get('is_qs', False)
        _po_type_label = 'Cuento Mágico Express (16p, magazine A4)' if _po_is_qs else 'Cuento FotoMágico (26p, tapa dura A4)'
        try:
            from services.email_service import send_admin_notification_email
            send_admin_notification_email(
                subject=f'[NUEVO PEDIDO IMPRESO] {pr.child_name} — {pr.customer_email}',
                body=f'Nuevo pedido de libro impreso.\nTipo: {_po_type_label}\nPedido ID: {pr.id}\nCliente: {pr.customer_email}\nNiño/a: {pr.child_name}\nImporte: ${pr.amount_paid}\nDirección: {pr.shipping_street}, {pr.shipping_city}, {pr.shipping_country}\nPreview ID: {pr.preview_id}\nMétodo envío: {pr.shipping_method}'
            )
        except Exception:
            pass
        redirect_url = f'/print-order-success?email={payer_email}'
        return jsonify({'success': True, 'redirect': redirect_url})
    except Exception as e:
        print(f"[PAYPAL] capture-print-order error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/admin/print-requests')
def admin_print_requests():
    if not session.get('admin_logged_in'):
        return redirect('/admin')
    requests_list = PrintOrderRequest.query.order_by(PrintOrderRequest.created_at.desc()).all()
    return render_template('admin_print_requests.html', requests=requests_list)

@app.route('/api/admin/send-to-lulu/<int:req_id>', methods=['POST'])
def admin_send_to_lulu(req_id):
    """Legacy route — Lulu has been replaced by Cloudprinter for QS and Gelato for Universos."""
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify({'error': 'Lulu has been replaced. Use Cloudprinter for Quick Stories (/admin/retry-cp/<preview_id>) or Gelato for personalized books.'}), 410

@app.route('/api/admin/send-tracking/<int:req_id>', methods=['POST'])
def admin_send_tracking(req_id):
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    pr = PrintOrderRequest.query.get_or_404(req_id)
    data = request.get_json()
    tracking_number = data.get('tracking_number', '').strip()
    if not tracking_number:
        return jsonify({'error': 'Missing tracking number'}), 400
    try:
        from services.email_service import send_tracking_email
        send_tracking_email(pr.customer_email, tracking_number, pr.shipping_name, session.get('lang', 'es'))
        pr.tracking_number = tracking_number
        pr.tracking_email_sent = True
        pr.status = 'shipped'
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        print(f"[ADMIN] send-tracking error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/resend-printable-pdf/<preview_id>', methods=['POST'])
def admin_resend_printable_pdf(preview_id):
    """Admin endpoint: delete cached PDF and re-trigger the full PDF dispatch (regenerate + email customer)."""
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    preview_file = f'story_previews/{preview_id}.json'
    if not os.path.exists(preview_file):
        return jsonify({'error': 'Order not found'}), 404
    with open(preview_file, 'r', encoding='utf-8') as f:
        story_data = json.load(f)
    customer_email = story_data.get('customer_email', '')
    lang = story_data.get('lang', 'es')
    child_name = story_data.get('child_name', '')
    print_format = story_data.get('print_format', 'A4')
    # Delete cached PDFs so they get regenerated with latest code
    import glob as _glob
    deleted = []
    for _pattern in [
        f'generated/gelato/{preview_id}/*.pdf',
        f'generations/email/{preview_id}/*.pdf',
    ]:
        for _f in _glob.glob(_pattern):
            try:
                os.remove(_f)
                deleted.append(_f)
                print(f"[ADMIN RESEND] Deleted cached PDF: {_f}")
            except Exception:
                pass
    # Clear sent flags so dispatch runs again
    story_data['printable_pdf_sent'] = None
    story_data['printable_pdf_admin_sent'] = None
    with open(preview_file, 'w', encoding='utf-8') as f:
        json.dump(story_data, f, ensure_ascii=False, indent=2)
    # Remove from in-flight lock set in case it's stuck
    with _pdf_dispatch_lock:
        _pdf_dispatch_locks.discard(preview_id)
    # Fire dispatch in background thread
    t = threading.Thread(
        target=_dispatch_printable_pdf_email,
        args=(preview_id, customer_email, lang),
        daemon=True
    )
    t.start()
    print(f"[ADMIN RESEND] Dispatch thread started for {preview_id} → {customer_email} (format={print_format})")
    return jsonify({
        'success': True,
        'message': f'PDF dispatch started for {preview_id}',
        'customer_email': customer_email,
        'print_format': print_format,
        'deleted_cached': deleted,
    })


@app.route('/formats/<preview_id>')
def formats_page(preview_id):
    lang = session.get('lang', 'es')
    preview_file = f'story_previews/{preview_id}.json'
    child_name = ''
    email = ''
    generation_complete = False
    already_has_pdf = False
    already_has_print = False
    if os.path.exists(preview_file):
        with open(preview_file, 'r', encoding='utf-8') as f:
            story_data = json.load(f)
        child_name = story_data.get('child_name', '')
        email = story_data.get('customer_email', '')
        generation_complete = bool(
            story_data.get('pages_composed') or
            story_data.get('generation_complete') or
            story_data.get('qs_text_composed')
        )
        already_has_pdf = bool(
            story_data.get('want_pdf') or story_data.get('pdf_email_sent')
        )
        already_has_print = bool(
            story_data.get('want_print') or story_data.get('cp_submitted')
        )
    if already_has_pdf and already_has_print:
        return redirect('/')
    from config import Config as C
    disc = 1.0 - (C.LAUNCH_DISCOUNT_PCT / 100.0)
    pdf_price_orig = round(C.PERSONALIZED_PDF_PRICE / 100.0, 2)
    print_price_orig = round(C.CP_PB_BASE_PRICE / 100.0, 2)
    pdf_price = round(pdf_price_orig * disc, 2)
    print_price = round(print_price_orig * disc, 2)
    discount_pct = C.LAUNCH_DISCOUNT_PCT
    return render_template('formats.html',
        lang=lang,
        preview_id=preview_id,
        child_name=child_name,
        email=email,
        generation_complete=generation_complete,
        already_has_pdf=already_has_pdf,
        already_has_print=already_has_print,
        pdf_price=pdf_price,
        pdf_price_orig=pdf_price_orig,
        print_price=print_price,
        print_price_orig=print_price_orig,
        discount_pct=discount_pct,
        paypal_client_id=Config.PAYPAL_CLIENT_ID,
    )


@app.route('/formats-success')
def formats_success():
    lang = session.get('lang', 'es')
    email = request.args.get('email', '')
    want_pdf = request.args.get('want_pdf', 'false') == 'true'
    want_print = request.args.get('want_print', 'false') == 'true'
    pdf_format = request.args.get('pdf_format', 'carta')
    return render_template('formats_success.html',
        lang=lang,
        email=email,
        want_pdf=want_pdf,
        want_print=want_print,
        pdf_format=pdf_format,
    )


def _quote_pb_shipping_for_method(country: str, state: str, shipping_method: str):
    """
    Re-quote Cloudprinter shipping server-side for a specific method.
    Returns (authoritative_ship_cost_usd, error_str).
    error_str is None on success, or a human-readable message on failure.
    """
    from services.cloudprinter_api_service import get_pb_shipping_quote
    cc = (country or '').strip().upper()
    sc = (state or '').strip().upper()
    if not cc:
        return 0.0, 'Missing shipping country'
    options = get_pb_shipping_quote(cc, state_code=sc)
    if not options:
        return 0.0, 'No shipping options available for this country'
    if shipping_method not in options:
        # Fallback: pick the cheapest available option if method no longer exists
        ship_usd = min(
            float(o.get('cp_cost_usd', o.get('cp_cost_eur', 999))) for o in options.values()
        )
        print(f"[FORMATS] shipping_method {shipping_method!r} not in quote; using cheapest ${ship_usd:.2f}")
    else:
        opt = options[shipping_method]
        ship_usd = round(float(opt.get('cp_cost_usd', opt.get('cp_cost_eur', 0))), 2)
    return ship_usd, None


def _compute_formats_order_total(want_pdf: bool, want_print: bool, verified_ship_usd: float, coupon_discount_pct: float = 0.0) -> float:
    """Compute expected order total from authoritative Config prices + verified shipping.
    Launch discount applies to product prices only; shipping is never discounted.
    coupon_discount_pct is an additional % discount on the platform fee (after launch disc)."""
    launch_disc = 1.0 - (Config.LAUNCH_DISCOUNT_PCT / 100.0)
    platform_fee = 0.0
    if want_pdf:
        platform_fee += round(Config.PERSONALIZED_PDF_PRICE / 100.0 * launch_disc, 2)
    if want_print:
        platform_fee += round(Config.CP_PB_BASE_PRICE / 100.0 * launch_disc, 2)
    if coupon_discount_pct > 0:
        coupon_disc = round(platform_fee * coupon_discount_pct / 100, 2)
        platform_fee = max(round(platform_fee - coupon_disc, 2), 0.01)
    total = platform_fee + (verified_ship_usd if want_print else 0.0)
    return round(total, 2)


@app.route('/api/paypal/create-formats-order', methods=['POST'])
def paypal_create_formats_order():
    try:
        data = request.get_json()
        want_pdf = bool(data.get('want_pdf', False))
        want_print = bool(data.get('want_print', False))
        if not want_pdf and not want_print:
            return jsonify({'error': 'Select at least one format'}), 400

        # Re-quote shipping server-side — never trust client shipping_cost
        verified_ship_usd = 0.0
        if want_print:
            shipping_method = str(data.get('shipping_method', '')).strip()
            if not shipping_method:
                return jsonify({'error': 'Missing shipping method for physical book'}), 400
            ship_usd, err = _quote_pb_shipping_for_method(
                data.get('shipping_country', ''),
                data.get('shipping_state', ''),
                shipping_method,
            )
            if err:
                return jsonify({'error': err}), 400
            verified_ship_usd = ship_usd

        # Coupon validation (server-side)
        coupon_code = (data.get('coupon_code') or '').strip().upper()
        coupon_discount_pct = 0.0
        if coupon_code:
            _cpn = Coupon.query.filter_by(code=coupon_code, is_active=True).first()
            if _cpn:
                _max = _cpn.max_uses or 0
                _used = _cpn.use_count or 0
                if _max == 0 or _used < _max:
                    coupon_discount_pct = float(_cpn.discount_pct or 0)

        # Server-side authoritative total
        amount = _compute_formats_order_total(want_pdf, want_print, verified_ship_usd, coupon_discount_pct)
        if amount <= 0:
            return jsonify({'error': 'Invalid computed amount'}), 400

        token = _get_paypal_access_token()
        import requests as req_lib
        order_payload = {
            'intent': 'CAPTURE',
            'purchase_units': [{'amount': {'currency_code': 'USD', 'value': f'{amount:.2f}'}, 'description': 'Formatos adicionales — Magic Memories Books'}],
            'application_context': {
                'brand_name': 'Magic Memories Books',
                'shipping_preference': 'NO_SHIPPING'
            }
        }
        resp = req_lib.post(
            f"{Config.PAYPAL_API_BASE}/v2/checkout/orders",
            headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
            json=order_payload,
            timeout=15
        )
        order = resp.json()
        if 'id' not in order:
            return jsonify({'error': order.get('message', 'PayPal error')}), 400
        return jsonify({'id': order['id'], 'expected_total': amount, 'verified_ship_usd': verified_ship_usd})
    except Exception as e:
        print(f"[PAYPAL] create-formats-order error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/paypal/capture-formats-order', methods=['POST'])
def paypal_capture_formats_order():
    try:
        data = request.get_json()
        order_id = data.get('orderID')
        if not order_id:
            return jsonify({'error': 'Missing orderID'}), 400

        want_pdf = bool(data.get('want_pdf', False))
        want_print = bool(data.get('want_print', False))
        pdf_format = data.get('pdf_format', 'carta') if want_pdf else None

        # --- Server-side product validation ---
        if not want_pdf and not want_print:
            return jsonify({'error': 'No products selected'}), 400

        shipping_method = ''
        verified_ship_usd = 0.0
        if want_print:
            required_ship = ['shipping_name', 'shipping_street', 'shipping_city', 'shipping_postal', 'shipping_country']
            for field in required_ship:
                if not str(data.get(field, '')).strip():
                    return jsonify({'error': f'Missing required shipping field: {field}'}), 400
            shipping_method = str(data.get('shipping_method', '')).strip()
            if not shipping_method:
                return jsonify({'error': 'Missing shipping method'}), 400
            # Re-quote shipping from Cloudprinter — authoritative, not from client
            ship_usd, err = _quote_pb_shipping_for_method(
                data.get('shipping_country', ''),
                data.get('shipping_state', ''),
                shipping_method,
            )
            if err:
                return jsonify({'error': err}), 400
            verified_ship_usd = ship_usd

        # Coupon validation (server-side re-check at capture)
        coupon_code_cap = (data.get('coupon_code') or '').strip().upper()
        coupon_discount_pct_cap = 0.0
        if coupon_code_cap:
            _cpn_cap = Coupon.query.filter_by(code=coupon_code_cap, is_active=True).first()
            if _cpn_cap:
                _max_c = _cpn_cap.max_uses or 0
                _used_c = _cpn_cap.use_count or 0
                if _max_c == 0 or _used_c < _max_c:
                    coupon_discount_pct_cap = float(_cpn_cap.discount_pct or 0)

        # --- Server-side expected total (authoritative) ---
        expected_total = _compute_formats_order_total(want_pdf, want_print, verified_ship_usd, coupon_discount_pct_cap)

        preview_id = data.get('preview_id', '')
        if not _PREVIEW_ID_RE.match(preview_id):
            return jsonify({'error': 'Invalid preview_id'}), 400
        preview_file = f'story_previews/{preview_id}.json'
        abs_previews = os.path.abspath('story_previews')
        if not os.path.abspath(preview_file).startswith(abs_previews + os.sep):
            return jsonify({'error': 'Invalid preview_id'}), 400
        if not os.path.exists(preview_file):
            return jsonify({'error': 'Order not found'}), 404

        # --- Capture PayPal payment ---
        token = _get_paypal_access_token()
        import requests as req_lib
        resp = req_lib.post(
            f"{Config.PAYPAL_API_BASE}/v2/checkout/orders/{order_id}/capture",
            headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
            timeout=15
        )
        result = resp.json()
        status = result.get('status', '')
        if status != 'COMPLETED':
            return jsonify({'error': f'Payment not completed: {status}'}), 400
        capture = result.get('purchase_units', [{}])[0].get('payments', {}).get('captures', [{}])[0]
        amount_paid = float(capture.get('amount', {}).get('value', 0))
        payer_email = result.get('payer', {}).get('email_address', data.get('email', ''))
        buyer_email = data.get('email', payer_email) or payer_email
        _fmt_currency = capture.get('amount', {}).get('currency_code', 'USD')
        _fmt_capture_id = capture.get('id', '')
        _fmt_payer_country = result.get('payer', {}).get('address', {}).get('country_code', '')
        _fmt_payment_data_base = {
            'amount_paid': amount_paid,
            'currency': _fmt_currency,
            'capture_id': _fmt_capture_id,
            'payer_country': _fmt_payer_country,
        }
        # Datos económicos para persistencia — /formats no usa cupones ni descuentos
        _fmt_pdf_price = round(Config.PERSONALIZED_PDF_PRICE / 100.0, 2)
        _fmt_print_price = round(Config.CP_PB_BASE_PRICE / 100.0, 2)
        _fmt_fp = {}
        if want_pdf:
            _fmt_fp['pdf'] = _fmt_pdf_price
        if want_print:
            _fmt_fp['print'] = _fmt_print_price
        _fmt_payment_data_base['format_prices'] = _fmt_fp
        _fmt_payment_data_base['shipping_cost_usd'] = round(verified_ship_usd, 2)
        _fmt_disc_amt = 0.0
        if coupon_code_cap and coupon_discount_pct_cap > 0:
            _platform_before = _compute_formats_order_total(want_pdf, want_print, 0.0, 0.0)
            _platform_after  = _compute_formats_order_total(want_pdf, want_print, 0.0, coupon_discount_pct_cap)
            _fmt_disc_amt = round(_platform_before - _platform_after, 2)
        _fmt_payment_data_base['discount_amount'] = _fmt_disc_amt
        _fmt_payment_data_base['coupon_code'] = coupon_code_cap or ''

        # --- Record coupon usage ---
        if coupon_code_cap and coupon_discount_pct_cap > 0:
            try:
                _cpn_rec = Coupon.query.filter_by(code=coupon_code_cap).first()
                if _cpn_rec:
                    _buyer_email_cpn = data.get('email', payer_email) or payer_email
                    if _cpn_rec.coupon_type in ('influencer', 'referral') and _buyer_email_cpn:
                        _existing = CouponUsage.query.filter_by(
                            coupon_code=coupon_code_cap, buyer_email=_buyer_email_cpn, paypal_order_id=None
                        ).first()
                        if _existing:
                            _existing.paypal_order_id = order_id
                            db.session.commit()
                        else:
                            db.session.add(CouponUsage(coupon_code=coupon_code_cap, buyer_email=_buyer_email_cpn,
                                paypal_order_id=order_id, discount_pct=_cpn_rec.discount_pct or 0))
                            db.session.commit()
                    else:
                        db.session.add(CouponUsage(coupon_code=coupon_code_cap,
                            buyer_email=data.get('email', payer_email) or payer_email,
                            paypal_order_id=order_id, discount_pct=_cpn_rec.discount_pct or 0))
                        _cpn_rec.use_count = (_cpn_rec.use_count or 0) + 1
                        db.session.commit()
                    print(f"[COUPON][FORMATS] Usage confirmed: {coupon_code_cap} order={order_id}")
            except Exception as _cpn_err:
                print(f"[COUPON][FORMATS] Error recording usage: {_cpn_err}")

        # --- Verify captured amount matches authoritative server total (tolerance $0.05) ---
        if abs(amount_paid - expected_total) > 0.05:
            print(f"[FORMATS] PAYMENT MISMATCH for {preview_id}: expected ${expected_total:.2f}, paid ${amount_paid:.2f}")
            return jsonify({'error': 'Payment amount mismatch. Please contact support.'}), 400

        with open(preview_file, 'r', encoding='utf-8') as f:
            story_data = json.load(f)
        lang = story_data.get('lang', 'es')
        child_name = story_data.get('child_name', '')

        try:
            from services.email_service import register_purchase_for_follow_up as _reg_fu
            _reg_fu(preview_id, buyer_email, child_name, lang,
                    story_name=story_data.get('story_name', story_data.get('title', '')))
        except Exception as _fu_err:
            print(f"[LEAD] register_purchase_for_follow_up error: {_fu_err}")

        # --- Dispatch PDF via _dispatch_cart_item for consistent handling ---
        if want_pdf:
            story_data['print_format'] = pdf_format
            with open(preview_file, 'w', encoding='utf-8') as f:
                json.dump(story_data, f, ensure_ascii=False, indent=2)
            _dispatch_cart_item(
                {'preview_id': preview_id, 'product_type': 'personalized_pdf', 'lang': lang},
                buyer_email,
                order_id,
                payment_data={**_fmt_payment_data_base, 'product_type': 'personalized_pdf'},
            )

        # --- Create PrintOrderRequest for physical book ---
        if want_print:
            # Reload from disk to preserve any flags written by _dispatch_cart_item
            # (e.g. want_pdf=True, pdf_paid=True) — avoids race condition overwrite
            with open(preview_file, 'r', encoding='utf-8') as f:
                story_data = json.load(f)
            _ship_addr_canonical = {
                'name': data.get('shipping_name', '').strip(),
                'street1': data.get('shipping_street', '').strip(),
                'city': data.get('shipping_city', '').strip(),
                'state_code': data.get('shipping_state', '').strip(),
                'postcode': data.get('shipping_postal', '').strip(),
                'country_code': data.get('shipping_country', 'ES').strip().upper(),
                'phone_number': data.get('shipping_phone', '').strip(),
            }
            story_data['shipping_address'] = _ship_addr_canonical
            story_data['want_print'] = True
            story_data['shipping_method'] = shipping_method
            story_data['paid'] = True
            story_data['paypal_order_id'] = order_id
            story_data['payment_date'] = datetime.now().isoformat()
            story_data['payment_status'] = 'completed'
            story_data['customer_email'] = buyer_email
            story_data['amount_paid'] = amount_paid
            story_data['currency'] = _fmt_currency
            if _fmt_capture_id:
                story_data['capture_id'] = _fmt_capture_id
            if _fmt_payer_country:
                story_data['payer_country'] = _fmt_payer_country
            story_data['product_type'] = 'cp_personalized'
            story_data['format_prices'] = _fmt_fp
            story_data['shipping_cost_usd'] = round(verified_ship_usd, 2)
            story_data['discount_amount'] = _fmt_disc_amt
            story_data['coupon_code'] = coupon_code_cap or ''
            with open(preview_file, 'w', encoding='utf-8') as f:
                json.dump(story_data, f, ensure_ascii=False, indent=2)

            pr = PrintOrderRequest(
                preview_id=preview_id,
                child_name=child_name,
                customer_email=buyer_email,
                paypal_order_id=order_id,
                amount_paid=amount_paid,
                shipping_name=data.get('shipping_name', '').strip(),
                shipping_street=data.get('shipping_street', '').strip(),
                shipping_city=data.get('shipping_city', '').strip(),
                shipping_state=data.get('shipping_state', '').strip(),
                shipping_postal=data.get('shipping_postal', '').strip(),
                shipping_country=data.get('shipping_country', 'ES').strip().upper(),
                shipping_phone=data.get('shipping_phone', '').strip(),
                shipping_method=shipping_method,
                shipping_cost=round(verified_ship_usd, 2),
                status='payment_confirmed'
            )
            db.session.add(pr)
            db.session.commit()
            try:
                from services.email_service import send_admin_notification_email
                send_admin_notification_email(
                    subject=f'[NUEVO PEDIDO IMPRESO via /formats] {child_name} — {buyer_email}',
                    body=(
                        f'Pedido de libro impreso desde /formats.\n'
                        f'Pedido ID: {pr.id}\nCliente: {buyer_email}\nNi\u00f1o/a: {child_name}\n'
                        f'Importe: ${pr.amount_paid}\n'
                        f'Direcci\u00f3n: {pr.shipping_street}, {pr.shipping_city}, {pr.shipping_country}\n'
                        f'Preview ID: {preview_id}\nM\u00e9todo env\u00edo: {pr.shipping_method}'
                    )
                )
            except Exception:
                pass
            # --- Dispatch to Cloudprinter ---
            from services.quick_stories.checkout import is_quick_story as _check_qs_print
            from services.personalized_books.generation import is_personalized_book as _check_pb_print
            _print_story_id = story_data.get('story_id', '')
            if _check_qs_print(_print_story_id):
                print(f"[FORMATS] Dispatching QS Cloudprinter for {preview_id}")
                _t_cp = threading.Thread(target=_process_quick_story_print, args=(preview_id, buyer_email), daemon=True)
                _t_cp.start()
            elif _check_pb_print(_print_story_id):
                print(f"[FORMATS] Dispatching PB post-payment for {preview_id}")
                _t_cp = threading.Thread(target=_process_personalized_book_post_payment, args=(preview_id, buyer_email), daemon=True)
                _t_cp.start()

        what_pdf = 'true' if want_pdf else 'false'
        what_print = 'true' if want_print else 'false'
        redirect_url = (
            f'/formats-success?email={payer_email}'
            f'&want_pdf={what_pdf}&want_print={what_print}'
            f'&pdf_format={pdf_format or ""}'
        )
        return jsonify({'success': True, 'redirect': redirect_url})
    except Exception as e:
        print(f"[PAYPAL] capture-formats-order error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/admin/send-test-lead-email', methods=['POST'])
def admin_send_test_lead_email():
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json()
    email = data.get('email', '')
    preview_id = data.get('preview_id', '')
    sequence = int(data.get('sequence', 1))
    child_name = data.get('child_name', 'Test')
    lang = data.get('lang', 'es')
    if not email or '@' not in email:
        return jsonify({'error': 'Missing or invalid email'}), 400
    try:
        from services.email_service import send_feedback_email_24h, send_upsell_print_email
        if sequence == 1:
            ok = send_feedback_email_24h(email, child_name, lang)
        elif sequence == 2:
            if not preview_id:
                return jsonify({'error': 'Missing preview_id for sequence 2'}), 400
            ok = send_upsell_print_email(preview_id, email, child_name, lang)
        else:
            return jsonify({'error': f'Unknown sequence: {sequence}'}), 400
        return jsonify({'success': ok, 'sequence': sequence, 'email': email})
    except Exception as e:
        print(f"[ADMIN] send-test-lead-email error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/admin/self-update', methods=['POST'])
def admin_self_update():
    """Download updated files from GitHub and restart. Auth: session OR deploy token."""
    _DEPLOY_TOKEN = os.environ.get('DEPLOY_TOKEN', 'mmb-deploy-2026-xK9p')
    provided = request.headers.get('X-Deploy-Token', '') or request.form.get('deploy_token', '')
    if not session.get('admin_logged_in') and provided != _DEPLOY_TOKEN:
        return jsonify({'error': 'Unauthorized'}), 401

    import subprocess, threading, urllib.request

    GH_RAW = "https://raw.githubusercontent.com/magicmemoriesbooks-io/magic-memories-page/main"
    APP = "/home/magicbooks/app"
    FILES = [
        "app.py",
        "services/email_service.py",
        "templates/formats.html",
        "templates/formats_success.html",
        "static/images/firma_isabel.jpg",
    ]

    def _do_update():
        import time
        errors = []
        for rel in FILES:
            url = f"{GH_RAW}/{rel}"
            dest = f"{APP}/{rel}"
            try:
                urllib.request.urlretrieve(url, dest)
                print(f"[SELF-UPDATE] ✅ {rel}")
            except Exception as e:
                errors.append(rel)
                print(f"[SELF-UPDATE] ❌ {rel}: {e}")
        time.sleep(1)
        subprocess.Popen(['systemctl', 'restart', 'magicbooks'])
        print(f"[SELF-UPDATE] Restart triggered. Errors: {errors or 'none'}")

    threading.Thread(target=_do_update, daemon=True).start()
    return jsonify({'ok': True, 'msg': 'Descargando archivos de GitHub y reiniciando en ~10s'})




# ───────────────────────────────────────────────
# ISABEL CAMPAIGN — bulk send + status
# ───────────────────────────────────────────────

@app.route('/admin/lead-campaign/isabel/send-one', methods=['POST'])
def admin_isabel_campaign_send_one():
    """Send Isabel's campaign email to one specific address. Admin only."""
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json() or {}
    to_email   = (data.get('email') or '').strip().lower()
    child_name = (data.get('child_name') or '').strip()
    lang       = (data.get('lang') or 'es').strip()
    if not to_email or '@' not in to_email:
        return jsonify({'error': 'Email inválido'}), 400
    from services.email_service import send_isabel_campaign_email
    ok = send_isabel_campaign_email(to_email, child_name, lang)
    return jsonify({'ok': ok, 'email': to_email})


@app.route('/admin/lead-campaign/isabel/send-all', methods=['POST'])
def admin_isabel_campaign_send_all():
    """Bulk-send Isabel's one-time campaign to all unconverted leads. Admin only."""
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    import glob as _g, json as _j
    from services.email_service import send_isabel_campaign_email, _is_duplicate_send

    story_dir = os.path.join(os.path.dirname(__file__), 'story_previews')
    _ET = 'lead_campaign_isabel'

    # Build purchased set
    purchased_emails = set()
    if os.path.isdir(story_dir):
        for pf in _g.glob(os.path.join(story_dir, '*.json')):
            try:
                with open(pf, 'r', encoding='utf-8') as _f:
                    sd = _j.load(_f)
                if sd.get('paid') or sd.get('ebook_paid') or sd.get('pdf_paid') \
                   or sd.get('payment_status') == 'completed' \
                   or float(sd.get('amount_paid') or sd.get('customer_total_usd') or 0) > 0:
                    em = (sd.get('customer_email') or '').strip().lower()
                    if em:
                        purchased_emails.add(em)
            except Exception:
                pass

    # Build story info index (lang + child_name) by email and story_id
    info_by_email = {}   # email → {child_name, lang}
    info_by_sid   = {}   # story_id → {child_name, lang}
    if os.path.isdir(story_dir):
        for pf in _g.glob(os.path.join(story_dir, '*.json')):
            try:
                with open(pf, 'r', encoding='utf-8') as _f:
                    sd = _j.load(_f)
                entry = {'child_name': sd.get('child_name', ''),
                         'lang': sd.get('lang', 'es')}
                em = (sd.get('customer_email') or '').strip().lower()
                if em and em not in info_by_email:
                    info_by_email[em] = entry
                sid = sd.get('story_id', '')
                if sid and sid not in info_by_sid:
                    info_by_sid[sid] = entry
            except Exception:
                pass

    # Query all leads with email
    leads_all = PreviewLead.query.filter(PreviewLead.email != '').all()
    seen_emails = set()
    sent, skipped_purchased, skipped_dupe, failed = 0, 0, 0, 0
    recipients = []

    for lead in leads_all:
        em = (lead.email or '').strip().lower()
        if not em or '@' not in em or em in seen_emails:
            continue
        seen_emails.add(em)

        if em in purchased_emails:
            skipped_purchased += 1
            continue
        if _is_duplicate_send(preview_id=em, email_type=_ET, days=365):
            skipped_dupe += 1
            continue

        info = info_by_email.get(em) or info_by_sid.get(lead.story_id or '', {})
        child_name = info.get('child_name', '')
        lang       = info.get('lang', 'es')

        ok = send_isabel_campaign_email(em, child_name, lang)
        if ok:
            sent += 1
            recipients.append({'email': em, 'name': child_name, 'lang': lang})
        else:
            failed += 1

    return jsonify({
        'ok': True,
        'sent': sent,
        'skipped_purchased': skipped_purchased,
        'skipped_already_sent': skipped_dupe,
        'failed': failed,
        'recipients': recipients
    })


@app.route('/admin/lead-campaign/isabel/stats')
def admin_isabel_campaign_stats():
    """Return per-recipient open/click/purchase stats for the Isabel campaign."""
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    import json as _j, glob as _g
    log_path = os.path.join('data', 'email_log.jsonl')
    _ET = 'lead_campaign_isabel'

    # ── Parse log into per-recipient buckets ──────────────────────────────
    by_email = {}   # email → {sent_at, opened_at, clicks:[{link,ts}], child_name, lang}
    if os.path.exists(log_path):
        with open(log_path, 'r', encoding='utf-8') as _f:
            for line in _f:
                try:
                    e = _j.loads(line)
                    if e.get('email_type') != _ET:
                        continue
                    em = (e.get('to_email') or '').strip().lower()
                    if not em:
                        continue
                    if em not in by_email:
                        by_email[em] = {
                            'email': em,
                            'child_name': e.get('child_name', ''),
                            'lang': e.get('lang', 'es'),
                            'sent_at': None,
                            'opened_at': None,
                            'clicks': [],
                            'purchased': False,
                            'purchased_at': None,
                        }
                    rec = by_email[em]
                    ev = e.get('event', '')
                    cat = e.get('category', '')
                    ts = e.get('ts', '')
                    if ev == 'open':
                        if rec['opened_at'] is None:
                            rec['opened_at'] = ts
                    elif ev == 'click':
                        rec['clicks'].append({'link': e.get('link_name', ''), 'ts': ts})
                    elif cat == 'other' and not ev:
                        # sent entry (logged via log_email)
                        if rec['sent_at'] is None:
                            rec['sent_at'] = ts
                        if not rec['child_name'] and e.get('child_name'):
                            rec['child_name'] = e['child_name']
                        if e.get('lang'):
                            rec['lang'] = e['lang']
                except Exception:
                    pass

    # ── Cross-reference purchases ──────────────────────────────────────────
    # An email counts as "purchased after campaign" if they have a paid story
    # AND their purchase timestamp is after their campaign send_at.
    story_dir = os.path.join(os.path.dirname(__file__), 'story_previews')
    if os.path.isdir(story_dir):
        for pf in _g.glob(os.path.join(story_dir, '*.json')):
            try:
                with open(pf, 'r', encoding='utf-8') as _f:
                    sd = _j.load(_f)
                em = (sd.get('customer_email') or '').strip().lower()
                if em not in by_email:
                    continue
                is_paid = (sd.get('paid') or sd.get('ebook_paid') or sd.get('pdf_paid')
                           or sd.get('payment_status') == 'completed'
                           or float(sd.get('amount_paid') or sd.get('customer_total_usd') or 0) > 0)
                if is_paid:
                    paid_at = sd.get('paid_at') or sd.get('created_at') or ''
                    rec = by_email[em]
                    sent_at = rec.get('sent_at') or ''
                    # Mark as purchased-after-campaign if paid_at >= sent_at (or no timestamps to compare)
                    if not rec['purchased'] and (not sent_at or not paid_at or paid_at >= sent_at):
                        rec['purchased'] = True
                        rec['purchased_at'] = paid_at
            except Exception:
                pass

    # ── Aggregate totals ───────────────────────────────────────────────────
    recipients = list(by_email.values())
    sent_count  = sum(1 for r in recipients if r['sent_at'])
    opens_count = sum(1 for r in recipients if r['opened_at'])
    # Deduplicate bots: ignore opens that fired <5s after send (email preview bots)
    real_opens  = 0
    for r in recipients:
        if r['opened_at'] and r['sent_at']:
            try:
                from datetime import datetime as _dtt
                diff = (_dtt.fromisoformat(r['opened_at']) - _dtt.fromisoformat(r['sent_at'])).total_seconds()
                if diff > 5:
                    real_opens += 1
            except Exception:
                real_opens += 1
        elif r['opened_at']:
            real_opens += 1
    click_total  = sum(len(r['clicks']) for r in recipients)
    clicks_cta   = sum(sum(1 for c in r['clicks'] if c['link'] == 'continuar') for r in recipients)
    clicks_gal   = sum(sum(1 for c in r['clicks'] if c['link'] == 'galeria') for r in recipients)
    clicks_ig    = sum(sum(1 for c in r['clicks'] if c['link'] == 'instagram') for r in recipients)
    purchased    = sum(1 for r in recipients if r['purchased'])

    # Sort: purchased first, then opened, then clicked, then sent
    def _sort_key(r):
        return (not r['purchased'], not r['opened_at'], not r['clicks'], not r['sent_at'])
    recipients.sort(key=_sort_key)

    return jsonify({
        'sent': sent_count,
        'opens': opens_count,
        'real_opens': real_opens,
        'open_rate': round(real_opens / sent_count * 100, 1) if sent_count else 0,
        'clicks_total': click_total,
        'clicks_cta': clicks_cta,
        'clicks_gallery': clicks_gal,
        'clicks_instagram': clicks_ig,
        'ctr': round(click_total / sent_count * 100, 1) if sent_count else 0,
        'purchased': purchased,
        'conversion_rate': round(purchased / sent_count * 100, 1) if sent_count else 0,
        'recipients': recipients,
    })


# ───────────────────────────────────────────────
# EMAIL TRACKING — open pixel + click redirect
# ───────────────────────────────────────────────
import base64 as _b64

@app.route('/email/open/<email_b64>/<email_type>')
def email_open_pixel(email_b64, email_type):
    """1×1 transparent GIF pixel for email open tracking."""
    try:
        padding = 4 - len(email_b64) % 4
        to_email = _b64.urlsafe_b64decode(email_b64 + '=' * (padding % 4)).decode('utf-8')
        import json as _j, os as _o
        from datetime import datetime as _dt
        log_path = _o.path.join('data', 'email_log.jsonl')
        _o.makedirs('data', exist_ok=True)
        entry = {
            'ts': _dt.now().isoformat(timespec='seconds'),
            'to_email': to_email,
            'email_type': email_type,
            'category': 'tracking',
            'label': 'Apertura de email',
            'result': 'opened',
            'event': 'open',
        }
        with open(log_path, 'a', encoding='utf-8') as _f:
            _f.write(_j.dumps(entry, ensure_ascii=False) + '\n')
    except Exception:
        pass
    # 1×1 transparent GIF
    pixel = (b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00'
             b'\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x00\x00\x00\x00\x00'
             b'\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b')
    from flask import Response as _Resp
    return _Resp(pixel, mimetype='image/gif', headers={
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0',
    })


@app.route('/email/click/<email_b64>/<email_type>/<link_name>')
def email_click_tracker(email_b64, email_type, link_name):
    """Log email click and redirect to destination."""
    dest = request.args.get('dest', 'https://magicmemoriesbooks.com')
    try:
        padding = 4 - len(email_b64) % 4
        to_email = _b64.urlsafe_b64decode(email_b64 + '=' * (padding % 4)).decode('utf-8')
        import json as _j, os as _o
        from datetime import datetime as _dt
        log_path = _o.path.join('data', 'email_log.jsonl')
        _o.makedirs('data', exist_ok=True)
        entry = {
            'ts': _dt.now().isoformat(timespec='seconds'),
            'to_email': to_email,
            'email_type': email_type,
            'category': 'tracking',
            'label': 'Clic en email',
            'result': 'clicked',
            'event': 'click',
            'link_name': link_name,
            'dest': dest,
        }
        with open(log_path, 'a', encoding='utf-8') as _f:
            _f.write(_j.dumps(entry, ensure_ascii=False) + '\n')
    except Exception:
        pass
    return redirect(dest)


# ══════════════════════════════════════════════════════════════════════════════
# COMMUNITY STORIES — Cuentos Solidarios
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/cuentos-solidarios')
def community_stories_list():
    lang = request.args.get('lang', session.get('lang', 'es'))
    stories = CommunityStory.query.filter_by(status='published').order_by(CommunityStory.created_at.desc()).all()
    return render_template('community_stories_list.html', stories=stories, lang=lang)


@app.route('/cuentos-solidarios/<slug>')
def community_story_detail(slug):
    story = CommunityStory.query.filter_by(slug=slug).first_or_404()
    if story.status not in ('published', 'hidden'):
        abort(404)
    lang = session.get('lang', 'es')
    preview_pages = list(story.pages.filter(CommunityStoryPage.page_number <= 4))
    return render_template('community_story_detail.html',
                           story=story, lang=lang,
                           preview_pages=preview_pages)


@app.route('/api/community-story/<slug>/generate', methods=['POST'])
def api_community_story_generate(slug):
    """
    JSON API: validate form data, create download record, send email with PDF attached.
    Returns: {success: true, token, redirect_url} or {error: key} with HTTP 400.
    """
    story = CommunityStory.query.filter_by(slug=slug, status='published').first_or_404()

    data = request.get_json(silent=True) or {}

    email_raw        = (data.get('email') or '').strip().lower()
    adult_name_raw   = (data.get('adult_name') or '').strip()[:80]
    pdf_format_raw   = (data.get('pdf_format') or 'A4').strip().upper().replace('CARTA', 'LETTER')
    if pdf_format_raw not in ('A4', 'LETTER'):
        pdf_format_raw = 'A4'
    story_lang       = (data.get('story_lang') or 'es')
    how_found_us     = (data.get('how_found_us') or '').strip()
    downloader_type  = (data.get('downloader_type') or '').strip()
    subscribe_future = bool(data.get('subscribe_future', False))
    utm_source   = (data.get('utm_source') or '').strip() or None
    utm_medium   = (data.get('utm_medium') or '').strip() or None
    utm_campaign = (data.get('utm_campaign') or '').strip() or None
    utm_content  = (data.get('utm_content') or '').strip() or None

    _ALLOWED_HOW_FOUND = {
        'instagram', 'tiktok', 'facebook', 'whatsapp', 'google',
        'amigo_familiar', 'escuela', 'colegio', 'iglesia',
        'psicologo', 'ong', 'noticias', 'otro',
    }
    _ALLOWED_DL_TYPE = {
        'padre_madre', 'abuelo_abuela', 'tio_tia', 'hermano_hermana',
        'docente', 'voluntario_ong',
        'trabajador_social', 'psicologo', 'periodista', 'otro', '',
    }

    # Server-side validation
    if not email_raw or '@' not in email_raw:
        return jsonify({'error': 'email_invalid'}), 400
    if not how_found_us or how_found_us not in _ALLOWED_HOW_FOUND:
        return jsonify({'error': 'how_found_us_required'}), 400
    if downloader_type and downloader_type not in _ALLOWED_DL_TYPE:
        return jsonify({'error': 'invalid_downloader_type'}), 400

    token = str(uuid.uuid4())
    dl = CommunityDownload(
        story_id=story.id,
        email=email_raw,
        adult_name=adult_name_raw or None,
        pdf_format=pdf_format_raw,
        download_token=token,
        language=story_lang,
        ip=get_client_ip(),
        user_agent=request.headers.get('User-Agent', '')[:499],
        how_found_us=how_found_us or None,
        downloader_type=downloader_type or None,
        campaign_source=utm_campaign or utm_source or 'unknown',
        utm_source=utm_source,
        utm_medium=utm_medium,
        utm_campaign=utm_campaign,
        utm_content=utm_content,
        referrer_url=request.referrer or '',
        completed_download=False,
        pdf_generated=False,
    )
    try:
        db.session.add(dl)
        db.session.commit()
    except Exception as _e:
        db.session.rollback()
        print(f'[COMMUNITY] DB error: {_e}')
        return jsonify({'error': 'generic'}), 500

    # Upsert subscriber ONLY when opt-in checkbox checked
    if subscribe_future:
        try:
            existing_sub = CommunitySubscriber.query.filter_by(email=email_raw).first()
            if not existing_sub:
                sub = CommunitySubscriber(
                    email=email_raw,
                    language=story_lang,
                    source_story=story.slug,
                    source_campaign=dl.campaign_source,
                    consent_version=1,
                )
                db.session.add(sub)
                db.session.commit()
        except Exception:
            db.session.rollback()

    base_url     = request.host_url.rstrip('/')
    viewer_url   = f"{base_url}{url_for('community_viewer', token=token)}"
    pdf_url      = f"{base_url}{url_for('community_download_pdf', token=token)}"
    download_url = f"{base_url}{url_for('community_download_page', token=token)}"
    story_title  = story.title_es if story_lang == 'es' else story.title_en
    safe_title   = re.sub(r'[^\w\s-]', '', story.title_es).strip().replace(' ', '_')
    pdf_filename = f"cuento_solidario_{safe_title}.pdf"

    # Send email with PDF attached in background thread
    _story_id   = story.id
    _story_lang = story_lang
    _story_slug = story.slug

    _adult_name_thread = adult_name_raw
    _pdf_format_thread = pdf_format_raw

    def _send_with_pdf():
        try:
            import traceback
            from services.community_stories_service import get_community_pdf_image_list
            from services.pdf_service import create_print_pdf_from_images, generate_print_instructions_pdf
            from services.email_service import send_story_email_with_attachments

            _out_dir = os.path.join('generations', 'community_pdfs', token)
            os.makedirs(_out_dir, exist_ok=True)

            _fmt_sfx = 'LETTER' if (_pdf_format_thread or '').upper() in ('LETTER', 'CARTA') else 'A4'
            _pdf_path   = os.path.join(_out_dir, f'cuento_{_story_lang}_{_fmt_sfx}.pdf')
            _instr_path = os.path.join(_out_dir, f'instrucciones_{_story_lang}_{_fmt_sfx}.pdf')

            _img_list = get_community_pdf_image_list(_story_slug, _story_lang)
            create_print_pdf_from_images(_img_list, _pdf_path,
                                         print_format=_pdf_format_thread,
                                         draw_trim_marks=True)
            generate_print_instructions_pdf(_instr_path, language=_story_lang,
                                            print_format=_pdf_format_thread)

            _recipient = (_adult_name_thread or '').strip() or \
                         ('ti' if _story_lang == 'es' else 'you')
            send_story_email_with_attachments(
                to_email=email_raw,
                story_data={
                    'child_name': _recipient,
                    'story_name': story_title,
                    'lang':       _story_lang,
                    'age_group':  'community',
                },
                pdf_digital_path=_pdf_path,
                instructions_path=_instr_path,
                visor_url=viewer_url,
            )

            with app.app_context():
                _dl = CommunityDownload.query.filter_by(download_token=token).first()
                if _dl:
                    _dl.pdf_generated = True
                    try:
                        db.session.commit()
                    except Exception:
                        db.session.rollback()
        except Exception as _e:
            import traceback as _tb
            print(f'[COMMUNITY EMAIL] Error sending with PDF: {_e}')
            _tb.print_exc()

    threading.Thread(target=_send_with_pdf, daemon=True).start()

    return jsonify({
        'success': True,
        'token': token,
        'redirect_url': download_url,
    })


@app.route('/community-download/<token>')
def community_download_page(token):
    """Access page: shows viewer + PDF links. noindex to protect personal tokens."""
    dl = CommunityDownload.query.filter_by(download_token=token).first_or_404()
    story = CommunityStory.query.get_or_404(dl.story_id)
    if story.status not in ('published', 'hidden'):
        abort(404)

    lang        = dl.language
    story_title = story.title_es if lang == 'es' else story.title_en
    base_url    = request.host_url.rstrip('/')
    viewer_url  = f"{base_url}{url_for('community_viewer', token=token)}"
    pdf_url     = f"{base_url}{url_for('community_download_pdf', token=token)}"

    pdf_format  = getattr(dl, 'pdf_format', None) or 'A4'
    adult_name  = getattr(dl, 'adult_name', None) or ''
    resp = make_response(render_template(
        'community_download.html',
        story=story, story_title=story_title,
        email=dl.email,
        viewer_url=viewer_url, pdf_url=pdf_url,
        token=token, lang=lang,
        pdf_format=pdf_format,
        adult_name=adult_name,
    ))
    resp.headers['X-Robots-Tag'] = 'noindex, nofollow'
    return resp


@app.route('/community-viewer/<token>')
def community_viewer(token):
    dl = CommunityDownload.query.filter_by(download_token=token).first_or_404()
    story = CommunityStory.query.get_or_404(dl.story_id)
    lang = dl.language

    if story.status not in ('published', 'hidden'):
        abort(404)

    if not dl.completed_download:
        dl.completed_download = True
        dl.times_downloaded = (dl.times_downloaded or 0) + 1
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()

    # Redirect to the MMB visor_qs (music + TTS narration + page-flip)
    visor_id = f'venezuela-terremoto-{lang}'
    return redirect(f'/visor_qs/?id={visor_id}')


@app.route('/community-download/<token>/pdf')
def community_download_pdf(token):
    dl = CommunityDownload.query.filter_by(download_token=token).first_or_404()
    story = CommunityStory.query.get_or_404(dl.story_id)

    if story.status not in ('published', 'hidden'):
        abort(404)

    from services.community_stories_service import get_community_pdf_image_list
    from services.pdf_service import create_print_pdf_from_images

    lang       = dl.language
    pdf_format = getattr(dl, 'pdf_format', None) or 'A4'
    _fmt_sfx   = 'LETTER' if (pdf_format or '').upper() in ('LETTER', 'CARTA') else 'A4'

    _out_dir  = os.path.join('generations', 'community_pdfs', token)
    os.makedirs(_out_dir, exist_ok=True)
    _pdf_path = os.path.join(_out_dir, f'cuento_{lang}_{_fmt_sfx}.pdf')

    try:
        if not os.path.exists(_pdf_path):
            _img_list = get_community_pdf_image_list(story.slug, lang)
            create_print_pdf_from_images(_img_list, _pdf_path, skip_sanitize=True,
                                         print_format=pdf_format,
                                         draw_trim_marks=True)
    except Exception as _pdf_e:
        print(f'[COMMUNITY PDF] Error: {_pdf_e}')
        abort(500)

    try:
        dl.pdf_generated = True
        dl.completed_download = True
        dl.times_downloaded = (dl.times_downloaded or 0) + 1
        db.session.commit()
    except Exception:
        db.session.rollback()

    story_title = story.title_en if lang == 'en' else story.title_es
    safe_title  = re.sub(r'[^\w\s-]', '', story_title).strip().replace(' ', '_')
    filename    = f"solidarity_story_{safe_title}.pdf" if lang == 'en' else f"cuento_solidario_{safe_title}.pdf"

    resp = make_response(send_file(
        _pdf_path,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename,
    ))
    resp.headers['X-Robots-Tag'] = 'noindex, nofollow'
    return resp


# ── Admin: Community Stories ──────────────────────────────────────────────────

def _require_admin():
    """Returns True if the current session is authenticated as admin."""
    return session.get('admin_logged_in', False)


@app.route('/admin/community-stories')
def admin_community_stories():
    if not _require_admin():
        return redirect(url_for('admin_login'))

    from datetime import timedelta
    now = datetime.utcnow()
    today = now.date()
    cutoff_7d  = now - timedelta(days=7)
    cutoff_30d = now - timedelta(days=30)

    stories = CommunityStory.query.order_by(CommunityStory.created_at.desc()).all()
    recent_downloads = (CommunityDownload.query
                        .order_by(CommunityDownload.created_at.desc())
                        .limit(50).all())
    subscribers = (CommunitySubscriber.query
                   .order_by(CommunitySubscriber.created_at.desc())
                   .limit(100).all())

    total_downloads    = CommunityDownload.query.count()
    downloads_today    = CommunityDownload.query.filter(
        db.func.date(CommunityDownload.created_at) == today).count()
    downloads_7d       = CommunityDownload.query.filter(
        CommunityDownload.created_at >= cutoff_7d).count()
    downloads_30d      = CommunityDownload.query.filter(
        CommunityDownload.created_at >= cutoff_30d).count()
    unique_emails      = db.session.query(
        db.func.count(db.func.distinct(CommunityDownload.email))).scalar() or 0
    completed_count    = CommunityDownload.query.filter_by(completed_download=True).count()
    pdf_count          = CommunityDownload.query.filter_by(pdf_generated=True).count()

    stats = {
        'total_stories':     len(stories),
        'total_downloads':   total_downloads,
        'total_subscribers': CommunitySubscriber.query.count(),
        'downloads_today':   downloads_today,
        'downloads_7d':      downloads_7d,
        'downloads_30d':     downloads_30d,
        'unique_emails':     unique_emails,
        'completed_count':   completed_count,
        'pdf_count':         pdf_count,
    }

    return render_template('admin_community_stories.html',
                           stories=stories,
                           recent_downloads=recent_downloads,
                           subscribers=subscribers,
                           stats=stats)


@app.route('/admin/community-stories/<slug>/preview')
def admin_community_story_preview(slug):
    if not _require_admin():
        return redirect(url_for('admin_login'))
    story = CommunityStory.query.filter_by(slug=slug).first_or_404()

    from services.community_stories_service import resolve_child_name
    child_name = resolve_child_name('', story.default_child_name_es)
    token = str(uuid.uuid4())
    dl = CommunityDownload(
        story_id=story.id,
        email='admin-preview@magicmemoriesbooks.com',
        child_name=child_name,
        download_token=token,
        language='es',
        campaign_source='admin_preview',
    )
    db.session.add(dl)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
    return redirect(url_for('community_viewer', token=token))


@app.route('/admin/community-stories/export-csv')
def admin_community_stories_export_csv():
    if not _require_admin():
        return redirect(url_for('admin_login'))
    import csv as _csv
    import io as _io
    downloads = CommunityDownload.query.order_by(CommunityDownload.created_at.desc()).all()
    buf = _io.StringIO()
    writer = _csv.writer(buf)
    writer.writerow([
        'id', 'email', 'child_name', 'story_slug', 'language',
        'how_found_us', 'downloader_type', 'campaign_source',
        'utm_source', 'utm_medium', 'utm_campaign',
        'subscribe_future', 'completed_download', 'times_downloaded',
        'pdf_generated', 'created_at',
    ])
    for dl in downloads:
        _story = CommunityStory.query.get(dl.story_id)
        writer.writerow([
            dl.id, dl.email, dl.child_name or '',
            _story.slug if _story else dl.story_id,
            dl.language, dl.how_found_us or '', dl.downloader_type or '',
            dl.campaign_source or '',
            dl.utm_source or '', dl.utm_medium or '', dl.utm_campaign or '',
            '', dl.completed_download, dl.times_downloaded, dl.pdf_generated,
            dl.created_at.isoformat() if dl.created_at else '',
        ])
    buf.seek(0)
    from flask import Response
    return Response(
        buf.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=community_downloads.csv'},
    )


@app.route('/admin/preview-cuento/<slug>')
def admin_preview_cuento(slug):
    """Admin flipbook preview — no token needed."""
    import os, re
    base = f'static/images/community_stories/{slug.replace("-", "_")}'
    if not os.path.isdir(base):
        abort(404)
    # Collect pageNN_preview.png or pageNN/scene.png as fallback
    pages = []
    for d in sorted(os.listdir(base)):
        m = re.match(r'^page(\d+)$', d)
        if not m:
            continue
        n = int(m.group(1))
        preview = f'{base}/page{m.group(1)}_preview.png'
        scene   = f'{base}/{d}/scene.png'
        if os.path.exists(preview):
            pages.append((n, '/' + preview))
        elif os.path.exists(scene):
            pages.append((n, '/' + scene))
    pages.sort()
    return render_template('admin_story_flipbook.html', slug=slug, pages=pages)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
