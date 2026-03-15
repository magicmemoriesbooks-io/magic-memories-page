import os
import uuid
import json
import atexit
import threading
import time
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory, send_file, abort, flash
import logging
from werkzeug.utils import secure_filename
from config import Config
from models import db, Order, StoryTemplate, RealStoryOrder, RealStoryCharacter, RealStoryPet, NewsletterSubscriber, PreviewLead, PrintOrderRequest, StoryBackup
from translations import TRANSLATIONS, STORY_TEMPLATES, get_translation
from apscheduler.schedulers.background import BackgroundScheduler
from services.task_queue import task_queue, production_logger, get_or_create_tracker

app = Flask(__name__)

from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

preview_rate_limits = {}
PREVIEW_RATE_MAX = 4
_generation_progress = {}
PREVIEW_RATE_WINDOW = 3 * 60 * 60

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

def check_preview_rate_limit(ip):
    now = time.time()
    if ip not in preview_rate_limits:
        preview_rate_limits[ip] = []
    preview_rate_limits[ip] = [t for t in preview_rate_limits[ip] if now - t < PREVIEW_RATE_WINDOW]
    remaining = PREVIEW_RATE_MAX - len(preview_rate_limits[ip])
    return remaining > 0, max(0, remaining)

def record_preview_usage(ip):
    if ip not in preview_rate_limits:
        preview_rate_limits[ip] = []
    preview_rate_limits[ip].append(time.time())

def save_preview_lead(email, ip, story_id):
    try:
        existing = PreviewLead.query.filter_by(email=email, story_id=story_id).first()
        if not existing:
            lead = PreviewLead(email=email, ip_address=ip, story_id=story_id)
            db.session.add(lead)
            db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"[LEAD] Error saving preview lead: {e}")

@app.after_request
def add_no_cache_headers(response):
    if 'text/html' in response.content_type or 'image/' in response.content_type:
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response

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
        now = datetime.now()
        for filepath in glob_module.glob(os.path.join(upload_dir, '*')):
            if os.path.isfile(filepath):
                age_hours = (now - datetime.fromtimestamp(os.path.getmtime(filepath))).total_seconds() / 3600
                if age_hours >= 72:
                    try:
                        os.remove(filepath)
                        deleted += 1
                    except Exception as e:
                        print(f"[PHOTO CLEANUP] Error deleting {filepath}: {e}")
        
        if deleted > 0:
            print(f"[PHOTO CLEANUP] Auto-deleted {deleted} expired photos (>72h)")
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
                        days_left = max(1, (expiry_dt - now).days)
                        result = send_ebook_expiry_warning_email(customer_email, child_name, days_left, renew_url, lang)
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
    """Read admin_config.json to get demo preview IDs that must never be auto-purged."""
    protected = set()
    try:
        with open('admin_config.json', 'r') as f:
            cfg = json.load(f)
        for key in ('demo_preview_id', 'demo_preview_id_b'):
            val = cfg.get(key, '')
            if val:
                protected.add(val)
    except Exception:
        pass
    return protected


def _purge_story_files(preview_id, story_data, include_lulu=False):
    """Delete all files associated with a story (scenes, visor pages, generated images, user photos)."""
    import shutil
    scenes_dir = f'story_previews/{preview_id}'
    if os.path.exists(scenes_dir):
        shutil.rmtree(scenes_dir)
    if include_lulu:
        lulu_folder = story_data.get('lulu_order_folder', '')
        if lulu_folder and os.path.exists(lulu_folder):
            shutil.rmtree(lulu_folder)
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
    for photo_key in ('human_photo_path', 'pet_photo_path'):
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
scheduler.start()

atexit.register(lambda: scheduler.shutdown())

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
    site_domain = os.environ.get('SITE_DOMAIN', 'magicmemoriesbooks.com')
    return f'https://{site_domain}/{visor_type}'

def get_lang():
    return session.get('lang', app.config['DEFAULT_LANGUAGE'])

def t(key):
    return get_translation(get_lang(), key)

def get_story_template_by_id(story_id, child_name=''):
    for template in STORY_TEMPLATES:
        if template['id'] == story_id:
            return template
    
    from services.fixed_stories import STORIES
    if story_id in STORIES:
        story = STORIES[story_id]
        lang = get_lang()
        name_placeholder = child_name if child_name else '[Nombre]'
        return {
            'id': story_id,
            'name_es': story.get('title_es', '').replace('{name}', name_placeholder).replace('{lo_la}', 'lo/la'),
            'name_en': story.get('title_en', '').replace('{name}', name_placeholder),
            'age_range': story.get('age_range', '0-1')
        }
    return None

@app.context_processor
def inject_globals():
    lang = get_lang()
    return {
        't': t,
        'lang': lang,
        'translations': TRANSLATIONS.get(lang, TRANSLATIONS['es']),
        'story_templates': STORY_TEMPLATES
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
    demo_visor_url = _get_demo_visor_url()
    demo_visor_url_b = _get_demo_visor_url_b()
    return render_template('index.html', demo_visor_url=demo_visor_url, demo_visor_url_b=demo_visor_url_b)

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

@app.route('/sitemap.xml')
def sitemap():
    from datetime import date
    today = date.today().isoformat()
    domain = 'https://magicmemoriesbooks.com'
    urls = [
        (f'{domain}/',                    '1.0',  'weekly'),
        (f'{domain}/story-selection',     '0.9',  'weekly'),
        (f'{domain}/personalized-books',  '0.9',  'weekly'),
        (f'{domain}/furry-love',          '0.9',  'weekly'),
        (f'{domain}/stories-birthday',    '0.8',  'weekly'),
        (f'{domain}/stories-0-1',         '0.8',  'weekly'),
        (f'{domain}/stories-3-5',         '0.8',  'weekly'),
        (f'{domain}/stories-3-8',         '0.8',  'weekly'),
        (f'{domain}/stories-5-7',         '0.8',  'weekly'),
        (f'{domain}/pricing',              '0.8',  'monthly'),
        (f'{domain}/faq',                 '0.7',  'monthly'),
        (f'{domain}/contact',             '0.6',  'monthly'),
        (f'{domain}/about',               '0.6',  'monthly'),
        (f'{domain}/terms',               '0.3',  'yearly'),
        (f'{domain}/privacy',             '0.3',  'yearly'),
    ]
    xml_parts = ['<?xml version="1.0" encoding="UTF-8"?>',
                 '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, priority, changefreq in urls:
        xml_parts.append(f'  <url><loc>{loc}</loc><lastmod>{today}</lastmod>'
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

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/story-selection')
def story_selection():
    child_name = request.args.get('name', '')
    child_gender = request.args.get('gender', 'female')
    is_change_mode = request.args.get('change') == '1'
    return render_template('story_selection.html', 
                          child_name=child_name, 
                          child_gender=child_gender,
                          is_change_mode=is_change_mode)

@app.route('/stories-0-1')
def stories_0_1():
    return render_template('stories_0_1.html')

@app.route('/stories-3-8')
def stories_3_8():
    return render_template('stories_3_8.html')

@app.route('/stories-3-5')
def stories_3_5():
    return redirect(url_for('stories_3_8'))

@app.route('/stories-5-7')
def stories_5_7():
    return redirect(url_for('stories_3_8'))

@app.route('/personalized-books')
def personalized_books():
    is_change_mode = request.args.get('change') == '1'
    original_preview_id = request.args.get('preview_id', '')
    return render_template('personalized_books.html', 
                          is_change_mode=is_change_mode,
                          original_preview_id=original_preview_id)

@app.route('/stories-birthday')
def stories_birthday():
    return redirect(url_for('birthday_selection'))

@app.route('/birthday')
def birthday_selection():
    return render_template('birthday_selection.html')

@app.route('/birthday-1-3')
def birthday_1_3():
    return render_template('birthday_1_3.html')

@app.route('/birthday-4-6')
def birthday_4_6():
    return render_template('birthday_4_6.html')

@app.route('/birthday-7-9')
def birthday_7_9():
    return render_template('birthday_7_9.html')

@app.route('/furry-love')
def furry_love_catalog():
    lang = get_lang()
    return render_template('furry_love_catalog.html', lang=lang, translations=TRANSLATIONS.get(lang, TRANSLATIONS['es']))

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
    return render_template('personalize_furry_love.html',
        lang=lang,
        translations=TRANSLATIONS.get(lang, TRANSLATIONS['es']),
        story_pages=story_pages,
        story_id=story_id,
        story_variant=story_variant,
        prefill_name=prefill_name,
        prefill_pet=prefill_pet,
        prefill_gender=prefill_gender,
        admin_gift=admin_gift
    )

@app.route('/api/upload-furry-photo', methods=['POST'])
def upload_furry_photo():
    import uuid as uuid_mod
    
    consent = request.form.get('consent', '')
    if consent != 'true':
        return jsonify({'success': False, 'error': 'Photo consent required (COPPA/GDPR)'})
    
    if 'photo' not in request.files:
        return jsonify({'success': False, 'error': 'No photo provided'})
    
    photo = request.files['photo']
    photo_type = request.form.get('type', 'human')
    
    if photo.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'})
    
    allowed_ext = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    ext = photo.filename.rsplit('.', 1)[-1].lower() if '.' in photo.filename else ''
    if ext not in allowed_ext:
        return jsonify({'success': False, 'error': 'Invalid file type. Use JPG, PNG, or WEBP.'})
    
    upload_dir = 'generated/uploads/furry_photos'
    os.makedirs(upload_dir, exist_ok=True)
    
    filename = f"{photo_type}_{uuid_mod.uuid4().hex[:8]}.{ext}"
    filepath = os.path.join(upload_dir, filename)
    photo.save(filepath)
    
    print(f"[FURRY PHOTO UPLOAD] Saved {photo_type} photo: {filepath}")
    
    return jsonify({'success': True, 'path': filepath})

@app.route('/personalize-story')
def personalize_story():
    story_id = request.args.get('story', '')
    child_name = request.args.get('name', '')
    child_gender = request.args.get('gender', 'female')
    
    admin_gift_mode = request.args.get('admin_gift', '')
    if not story_id or (not child_name and not admin_gift_mode):
        return redirect(url_for('index'))
    if not child_name and admin_gift_mode:
        child_name = 'Regalo'
    
    template = get_story_template_by_id(story_id, child_name)
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
                          admin_gift=admin_gift)

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
            'child_age': child_age
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


@app.route('/api/generate-baby-preview', methods=['POST'])
def generate_baby_preview_api():
    """Generate character preview with FLUX via Replicate (supports baby and kids)"""
    try:
        data = request.get_json()

        if not data.get('admin_gift'):
            client_ip = get_client_ip()
            allowed, remaining = check_preview_rate_limit(client_ip)
            if not allowed:
                lang = get_lang()
                msg = '⚠️ Has alcanzado el límite de 3 previsualizaciones gratuitas. Cada ilustración se genera individualmente con inteligencia artificial. Podrás generar nuevas en unas horas. Si ya encontraste el diseño que te gusta, puedes continuar con tu pedido.' if lang == 'es' else "⚠️ You've reached the limit of 3 free previews. Each illustration is individually generated using artificial intelligence. You can generate new ones in a few hours. If you've already found the design you like, you can continue with your order."
                return jsonify({'success': False, 'error': msg, 'rate_limited': True}), 429
            user_email = data.get('user_email', '').strip()
            if user_email:
                save_preview_lead(user_email, client_ip, data.get('story_id', ''))
            record_preview_usage(client_ip)

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
            'gender': child_gender
        }
        from services.quick_stories.checkout import ALL_QUICK_FAMILY_IDS
        
        story_config = STORIES.get(story_id, {})
        age_range = story_config.get('age_range', '0-1')
        is_baby = age_range in ['0-1', '0-2']
        is_quick_story = story_id in ALL_QUICK_FAMILY_IDS
        
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
            return jsonify(result)
        
        if is_baby:
            gender_word = "baby boy" if child_gender == "male" else "baby girl" if child_gender == "female" else "baby"
            age_display = f"{child_age} year old" if child_age > 0 else "baby"
            
            is_toddler = child_age >= 1
            if is_toddler and 'preview_prompt_override_toddler' in story_config:
                preview_override = story_config.get('preview_prompt_override_toddler')
                print(f"[PREVIEW] Using TODDLER preview prompt in app.py (child_age={child_age})")
            else:
                preview_override = story_config.get('preview_prompt_override')
            if preview_override:
                from services.fixed_stories import BUNNY_DESC, PUPPY_DESC, KITTEN_DESC, GUARDIAN_LIGHT_DESC, DOG_FOREVER_DESC
                scene_style = "clean illustration only, pure artwork, professional children's book quality"
                skin_tone = get_skin_tone(traits.get('skin_tone', 'light'))
                gender_child = get_gender_child(child_gender)
                candle_plural = "s" if child_age != 1 else ""
                candle_plural_en = "s" if child_age != 1 else ""
                prompt = preview_override.format(
                    gender_word=gender_word,
                    gender_child=gender_child,
                    age_display=age_display,
                    hair_desc=hair_desc,
                    eye_desc=eye_desc,
                    skin_desc=skin_desc,
                    skin_tone=skin_tone,
                    child_age=child_age,
                    candle_plural=candle_plural,
                    candle_plural_en=candle_plural_en,
                    style=scene_style,
                    bunny_desc=BUNNY_DESC,
                    puppy_desc=PUPPY_DESC,
                    kitten_desc=KITTEN_DESC,
                    guardian_light_desc=GUARDIAN_LIGHT_DESC,
                    dog_forever_desc=DOG_FOREVER_DESC
                )
                from services.fixed_stories import adapt_baby_pose_for_age, enforce_gender_clothing
                prompt = adapt_baby_pose_for_age(prompt, child_age)
                prompt = enforce_gender_clothing(prompt, child_gender)
                
                hair_length_preview = traits.get('hair_length', 'medium')
                if hair_length_preview == 'very_little' and 'STRICT:' in prompt:
                    prompt = prompt.replace('STRICT:', 'STRICT: Baby head is completely smooth and bald-looking with only thin peach fuzz on bare scalp, head shape fully visible and round,')
                
                print(f"Baby preview using DNA override for: {story_id} (age: {age_display}, hair: {hair_desc})")
            else:
                gender_features = "masculine infant features, short wispy hair" if child_gender == "male" else "feminine infant features" if child_gender == "female" else ""
                no_accessories = "No earrings, no jewelry, no bows, no feminine accessories." if child_gender == "male" else ""
                
                if child_age == 0:
                    age_desc = f"VERY TINY NEWBORN INFANT {gender_word} (6-9 months old)"
                    pose_desc = "LYING FLAT ON BACK on a soft blanket, CANNOT SIT UP YET, tiny arms and legs relaxed, looking up at ceiling"
                    body_desc = "extremely small baby body, very chubby round face, short stubby limbs, cannot hold head up well"
                elif child_age == 1:
                    age_desc = f"1 YEAR OLD {gender_word} (12 months old)"
                    pose_desc = "SITTING UPRIGHT on a soft blanket, CAN SIT WITHOUT SUPPORT, holding a soft toy"
                    body_desc = "small baby body, round chubby face, can sit independently, slightly longer limbs than infant"
                else:
                    age_desc = f"2 YEAR OLD TODDLER {gender_word}"
                    pose_desc = "STANDING ON TWO FEET in a cozy nursery, WALKING, taking confident steps"
                    body_desc = "toddler body proportions, less chubby face, longer legs, can walk and run"
                
                prompt = f"Full body illustration of a {age_desc}, {body_desc}, with {hair_desc}, {eye_desc} and {skin_desc}. {gender_features}. The {gender_word} is {pose_desc}. Wearing soft white onesie, innocent sweet expression. Soft pastel nursery background with gentle light. Children's storybook watercolor illustration style, soft luminous colors, gentle warm lighting. Clean illustration only, pure artwork, professional children's book quality"
                print(f"Baby preview fallback: age={child_age}, pose={pose_desc}, body={body_desc}")
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
                    traits=traits
                )
                
                return jsonify(result)
            elif story_id == 'zebra_stripes':
                child_base = f"Physical characteristics of {gender_word}: Age: {age_desc}. EXACT Hair: {hair_desc}. EXACT Skin: {skin_desc}. EXACT Eyes: {eye_desc}. HUMAN ONLY: normal human child with two arms, two legs, five fingers per hand."
                prompt = f"SCENE: Beautiful African savanna at dawn with golden light, acacia trees and tall grass swaying in the breeze. {child_base} This {gender_word} is standing in the savanna, wearing comfortable safari clothing (khaki t-shirt and shorts). {gender_word} is smiling warmly. Separately, Lila the friendly zebra stands nearby with beautiful black and white stripes, gentle dark eyes, smiling warmly. Watercolor illustration from a children's storybook, with soft, luminous colors and warm, magical lighting. {gender_word} and Lila the zebra shown full-body, clean illustration."
                print(f"Using zebra_stripes prompt with LILA and child_base")
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
                    
                    # Build char_base for personalized books
                    char_base = f"a {age_display} {gender_child} with {hair_color} {hair_length} {hair_type} hair, {skin_tone} skin, and {eye_desc}"
                    
                    from services.fixed_stories import BUNNY_DESC, PUPPY_DESC, KITTEN_DESC, GUARDIAN_LIGHT_DESC, DOG_FOREVER_DESC, SPARK_DESC, LILA_DESC, get_hair_action
                    hair_action = get_hair_action(traits)
                    scene_style = "NO text, NO watermark, NO signature, NO logo, NO artist name, NO handwriting, NO calligraphy, clean illustration only"
                    spark_desc_formatted = SPARK_DESC.format(gender_word=gender_word)
                    lila_desc_formatted = LILA_DESC.format(gender_word=gender_word)
                    dog_forever_desc_formatted = DOG_FOREVER_DESC.format(gender_word=gender_word)
                    candle_plural = "s" if child_age != 1 else ""
                    candle_plural_en = "s" if child_age != 1 else ""
                    prompt = preview_override.format(
                        gender_word=gender_word,
                        gender_child=gender_child,
                        hair_desc=hair_desc,
                        eye_desc=eye_desc,
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
                    print(f"Using story-specific preview override for: {story_id} (age: {age_display})")
                    print(f"\n===== PROMPT ENVIADO A FLUX =====\n{prompt}\n===== FIN PROMPT =====")
                else:
                    prompt = f"Full body portrait of a cheerful {gender_word} (4-5 years old) with {hair_desc}, {eye_desc} and {skin_desc}, {gender_features}, wearing adventure clothes (simple shirt and shorts), standing in a magical garden, bright curious expression, happy smile, soft magical background with warm light and floating sparkles, children's storybook watercolor illustration style, soft luminous colors, warm lighting, magical atmosphere. NO text, NO watermark, NO signature, NO logo, clean illustration only"
        
        print(f"Preview prompt: {gender_word} ({age_range}) with {hair_desc}, {eye_desc}, {skin_desc}")
        
        if is_quick_story and is_baby:
            preview_model = None
            print(f"[PREVIEW] Baby Quick Story: using FLUX 2 Pro for better hair/feature accuracy")
        elif is_quick_story:
            preview_model = FLUX_2_DEV_MODEL
        else:
            preview_model = None
        image_url = generate_illustration_replicate(prompt, 0, aspect_ratio="1:1", model=preview_model)
        
        output_dir = f'generated/previews'
        os.makedirs(output_dir, exist_ok=True)
        local_path = save_image_locally(image_url, f'{output_dir}/preview_{uuid.uuid4().hex[:8]}.png')
        
        return jsonify({
            'success': True,
            'image_url': f'/{local_path}'
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/regenerate-furry-preview', methods=['POST'])
def regenerate_furry_preview():
    """Regenerate a single furry_love preview (human OR pet) individually"""
    try:
        data = request.get_json()

        client_ip = get_client_ip()
        allowed, remaining = check_preview_rate_limit(client_ip)
        if not allowed:
            lang = get_lang()
            msg = '⚠️ Has alcanzado el límite de 3 previsualizaciones gratuitas. Cada ilustración se genera individualmente con inteligencia artificial. Podrás generar nuevas en unas horas. Si ya encontraste el diseño que te gusta, puedes continuar con tu pedido.' if lang == 'es' else "⚠️ You've reached the limit of 3 free previews. Each illustration is individually generated using artificial intelligence. You can generate new ones in a few hours. If you've already found the design you like, you can continue with your order."
            return jsonify({'success': False, 'error': msg, 'rate_limited': True}), 429
        user_email = data.get('user_email', '').strip()
        if user_email:
            save_preview_lead(user_email, client_ip, data.get('story_id', ''))
        record_preview_usage(client_ip)

        which = data.get('which', 'human')
        
        from services.replicate_service import save_image_locally, get_unified_skin_description
        from services.fixed_stories import get_hair_description, get_eye_description
        from services.personalized_books.preview import generate_with_flux2_dev, generate_with_flux_pulid
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
                prompt = build_human_preview_prompt_with_photo(gender_word, age_display, eye_desc, hair_desc, glasses=glasses_val)
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
                prompt = build_human_preview_prompt(human_desc)
                photo_ref = None
            
            print(f"[REGEN FURRY] Regenerating HUMAN preview (photo={bool(photo_ref)})")
            if photo_ref:
                use_pulid = story_id_regen in ('furry_love_teen_illustrated', 'furry_love_adult_illustrated')
                if use_pulid:
                    print(f"[REGEN FURRY] Using PuLID for {story_id_regen}")
                    try:
                        image_url = generate_with_flux_pulid(prompt, photo_ref, width=768, height=1024)
                    except Exception as pulid_err:
                        print(f"[REGEN FURRY] PuLID failed ({str(pulid_err)[:150]}), falling back to FLUX 2 Dev...")
                        image_url = generate_with_flux2_dev(prompt, aspect_ratio="3:4", photo_ref_path=photo_ref)
                else:
                    print(f"[REGEN FURRY] Using FLUX 2 Dev for {story_id_regen}")
                    image_url = generate_with_flux2_dev(prompt, aspect_ratio="3:4", photo_ref_path=photo_ref)
            else:
                image_url = generate_with_flux2_dev(prompt, aspect_ratio="3:4")
            local_path = save_image_locally(image_url, f'{output_dir}/preview_human_{uuid.uuid4().hex[:8]}.png')
        else:
            pet_desc = data.get('pet_desc', '')
            pet_species = data.get('pet_species', 'dog')
            pet_photo_path = data.get('pet_photo_path', '')
            upload_prefix = 'generated/uploads/furry_photos/'
            if pet_photo_path and pet_photo_path.startswith(upload_prefix) and os.path.exists(pet_photo_path):
                prompt = build_pet_preview_prompt_with_photo(pet_desc, pet_species)
                photo_ref = pet_photo_path
            else:
                prompt = build_pet_preview_prompt(pet_desc)
                photo_ref = None
            
            print(f"[REGEN FURRY] Regenerating PET preview (photo={bool(photo_ref)})")
            image_url = generate_with_flux2_dev(prompt, aspect_ratio="3:4", photo_ref_path=photo_ref)
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
            gender_word_regen = "boy" if child_gender_regen == "male" else "girl" if child_gender_regen == "female" else "person"
            age_val_regen = int(child_age_regen) if child_age_regen.isdigit() else 5
            if 'furry_love_adventure' in story_id:
                age_display_regen = f"{age_val_regen} year old child"
            elif 'furry_love_teen' in story_id:
                age_display_regen = f"{age_val_regen} year old teenager"
            elif 'furry_love_adult' in story_id:
                age_display_regen = f"{age_val_regen} year old adult"
            else:
                age_display_regen = f"{age_val_regen} month old baby" if age_val_regen < 2 else f"{age_val_regen} year old toddler"
            
            cover_prompt = build_scene_prompt(FRONT_COVER, human_desc, pet_name, pet_desc, age_display=age_display_regen, eye_desc=eye_desc_regen, gender_word=gender_word_regen)
            
            print(f"[REGEN COVER] Regenerating cover for {story_id} with FLUX 2 Dev + references")
            cover_url = generate_with_flux2_dev(
                cover_prompt, 
                aspect_ratio="3:4",
                photo_ref_paths=[human_preview_path, pet_preview_path]
            )
            cover_raw_path = save_image_locally(cover_url, f'{output_dir}/cover_raw.png')
            
            story_lang = story_data.get('story_lang', 'es')
            from services.personalized_books.generation import get_lulu_title
            book_id = story_id.replace('_illustrated', '')
            story_title = get_lulu_title(book_id, child_name, story_lang, pet_name=pet_name)
            author_name = story_data.get('author_name', '')
            
            cover_image_path = create_cover_from_character(
                cover_raw_path, output_dir,
                title=story_title,
                author=author_name if author_name else ''
            )
            
            story_data['cover_image'] = f'/{cover_image_path}'
            story_data['cover_raw_path'] = cover_raw_path
            story_data['original_cover'] = f'/{cover_image_path}'
            
            with open(preview_file, 'w', encoding='utf-8') as f:
                json.dump(story_data, f, ensure_ascii=False, indent=2)
            
            print(f"[REGEN COVER] Cover regenerated successfully: {cover_image_path}")
            return jsonify({
                'success': True,
                'cover_image': f'/{cover_image_path}'
            })
        else:
            return jsonify({'success': False, 'error': 'Cover regeneration only available for furry_love stories'}), 400
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

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
            client_ip = get_client_ip()
            allowed, remaining = check_preview_rate_limit(client_ip)
            if not allowed:
                lang = get_lang()
                msg = '⚠️ Has alcanzado el límite de 3 previsualizaciones gratuitas. Cada ilustración se genera individualmente con inteligencia artificial. Podrás generar nuevas en unas horas. Si ya encontraste el diseño que te gusta, puedes continuar con tu pedido.' if lang == 'es' else "⚠️ You've reached the limit of 3 free previews. Each illustration is individually generated using artificial intelligence. You can generate new ones in a few hours. If you've already found the design you like, you can continue with your order."
                return jsonify({'success': False, 'error': msg, 'rate_limited': True}), 429
            user_email = data.get('user_email', '').strip()
            if user_email:
                save_preview_lead(user_email, client_ip, data.get('story_id', ''))
            record_preview_usage(client_ip)

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
            'gender': child_gender
        }
        
        is_furry_love = (story_id in ('furry_love_illustrated', 'furry_love_adventure_illustrated', 'furry_love_teen_illustrated', 'furry_love_adult_illustrated'))
        if is_furry_love:
            traits['pet_name'] = data.get('pet_name', 'Buddy')
            traits['pet_desc'] = data.get('pet_desc', '')
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
            pet_name_for_title = traits.get('pet_name', '') if is_furry_love else ''
            story_title_pb = story_title_pb.replace('{name}', child_name).replace('{lo_la}', lo_la_pb).replace('{pet_name}', pet_name_for_title)
            
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
                gender_word_cover = "boy" if child_gender == "male" else "girl" if child_gender == "female" else "person"
                age_val = int(child_age) if str(child_age).isdigit() else 5
                if story_id == 'furry_love_illustrated':
                    age_display_cover = f"{age_val} month old baby" if age_val < 2 else f"{age_val} year old toddler"
                elif story_id == 'furry_love_adventure_illustrated':
                    age_display_cover = f"{age_val} year old child"
                elif story_id == 'furry_love_teen_illustrated':
                    age_display_cover = f"{age_val} year old teenager"
                else:
                    age_display_cover = f"{age_val} year old adult"
                
                glasses_cover = traits.get('glasses', 'none')
                cover_prompt = build_scene_prompt(FRONT_COVER, human_desc, pet_name_cover, pet_desc_cover, age_display=age_display_cover, eye_desc=eye_desc_cover, gender_word=gender_word_cover, glasses=glasses_cover)
                
                print(f"[FURRY LOVE COVER] Generating cover with both characters using FLUX 2 Dev + references")
                cover_url = generate_with_flux2_dev(
                    cover_prompt, 
                    aspect_ratio="3:4",
                    photo_ref_paths=[human_preview_path, pet_preview_path]
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
                _clean_img = _clean_img.resize((1024, 1024), PILClean.LANCZOS)
                _clean_img.save(cover_clean_path, "PNG")
                del _clean_img
                
                title_key = f'title_{story_lang}' if story_lang in ['es', 'en'] else 'title_en'
                story_title = story_cfg.get(title_key, story_cfg.get('title_en', ''))
                lo_la = "la" if child_gender == "female" else "lo"
                story_title = story_title.replace('{name}', child_name).replace('{lo_la}', lo_la)
                
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
            'character_preview': character_image if character_image else '',
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
            # For admin gifts, we skip the shipping/payment form by marking it as if it was already processed
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
            
            # Use the existing admin_generate_free logic directly to skip the limited preview
            preview_data['admin_gift_email'] = preview_data['customer_email']
            
            preview_url = f'/order-complete/{preview_id}'
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
        
        if data.get('admin_gift'):
            print(f"[ADMIN-GIFT-AUTO] Triggering free generation for {preview_id}")
            _trigger_background_generation(preview_id)
            
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
    
    # Always use fixed back cover with logo
    fixed_back_cover = '/static/images/fixed_pages/back_cover.png'
    if os.path.exists('static/images/fixed_pages/back_cover.png'):
        full_preview.append(fixed_back_cover)
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
    
    story_id = story_data.get('story_id', '')
    test_mode = request.args.get('test') == '1'
    lang = get_lang()
    
    from services.quick_stories.checkout import ALL_QUICK_FAMILY_IDS
    from services.personalized_books.checkout import PERSONALIZED_BOOK_IDS
    
    ebook_config = {
        'allow_ebook': True,
        'ebook_base_price': Config.EBOOK_BASE_PRICE / 100.0,
        'ebook_product_type': 'ebook',
    }
    
    if story_id in ALL_QUICK_FAMILY_IDS:
        checkout_config = {
            'product_type': 'quick_story',
            'allow_digital': True,
            'allow_print': True,
            'digital_base_price': Config.QS_DIGITAL_BASE_PRICE / 100.0,
            'print_base_price': Config.QS_PRINT_BASE_PRICE / 100.0,
            'digital_product_type': 'qs_digital',
            'print_product_type': 'qs_print',
            'product_description': 'PDF digital + PDF imprimible' if lang == 'es' else 'Digital PDF + printable PDF',
            'print_description_es': 'Libro engrapado a color',
            'print_description_en': 'Color saddle stitch book',
            **ebook_config,
        }
    elif story_id in PERSONALIZED_BOOK_IDS:
        checkout_config = {
            'product_type': 'personalized',
            'allow_digital': True,
            'allow_print': True,
            'digital_base_price': Config.PERSONALIZED_BASE_PRICE / 100.0,
            'print_base_price': Config.PERSONALIZED_BASE_PRICE / 100.0,
            'digital_product_type': 'personalized',
            'print_product_type': 'personalized',
            'product_description': '24 páginas, 19 ilustraciones, PDF digital' if lang == 'es' else '24 pages, 19 illustrations, digital PDF',
            'print_description_es': 'Libro tapa dura A4',
            'print_description_en': 'A4 hardcover book',
            **ebook_config,
        }
    else:
        checkout_config = {
            'product_type': 'personalized',
            'allow_digital': True,
            'allow_print': True,
            'digital_base_price': Config.PERSONALIZED_BASE_PRICE / 100.0,
            'print_base_price': Config.PERSONALIZED_BASE_PRICE / 100.0,
            'digital_product_type': 'personalized',
            'print_product_type': 'personalized',
            'product_description': 'PDF digital' if lang == 'es' else 'Digital PDF',
            'print_description_es': 'Libro tapa dura',
            'print_description_en': 'Hardcover book',
            **ebook_config,
        }
    
    return render_template('checkout_unified.html',
                          preview_id=preview_id,
                          story_data=story_data,
                          paypal_client_id=Config.PAYPAL_CLIENT_ID,
                          checkout_config=checkout_config,
                          test_mode=test_mode)

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
    """Validate shipping address using Lulu API."""
    from services.lulu_api_service import validate_shipping_address
    
    data = request.get_json()
    if not data:
        return jsonify({'valid': False, 'message': 'No address data provided'}), 400
    
    result = validate_shipping_address(data)
    return jsonify(result)


@app.route('/api/shipping-costs', methods=['POST'])
def get_shipping_costs():
    """Get shipping costs for all methods based on country code."""
    from services.lulu_api_service import get_all_shipping_costs
    
    data = request.get_json()
    country_code = data.get('country_code', 'US')
    
    costs = get_all_shipping_costs(country_code)
    return jsonify(costs)


@app.route('/api/qs-shipping-costs', methods=['POST'])
def get_qs_shipping_costs():
    """Get shipping costs for Quick Stories (saddle stitch 8.5x8.5) based on country code."""
    from services.lulu_api_service import get_all_shipping_costs
    
    data = request.get_json()
    country_code = data.get('country_code', 'US')
    
    QS_POD_PACKAGE_ID = '0850X0850FCPRESS080CW444GXX'
    QS_PAGE_COUNT = 10
    
    costs = get_all_shipping_costs(country_code, page_count=QS_PAGE_COUNT, pod_package_id=QS_POD_PACKAGE_ID)
    return jsonify(costs)


@app.route('/api/calculate-dynamic-price', methods=['POST'])
def calculate_dynamic_price():
    """Calculate dynamic price: base_price + Lulu total cost for each shipping method.
    Returns price breakdown for all available shipping options.
    """
    from services.lulu_api_service import get_all_shipping_costs
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    product_type = data.get('product_type', 'personalized')
    country_code = data.get('country_code', 'US')
    
    if product_type == 'qs_print':
        base_price_cents = Config.QS_PRINT_BASE_PRICE
        pod_package_id = '0850X0850FCPRESS080CW444GXX'
        page_count = 10
    else:
        base_price_cents = Config.PERSONALIZED_BASE_PRICE
        pod_package_id = '0827X1169FCPRECW080CW444GXX'
        page_count = 24
    
    base_price_dollars = base_price_cents / 100.0
    
    lulu_costs = get_all_shipping_costs(country_code, page_count=page_count, pod_package_id=pod_package_id)
    
    if isinstance(lulu_costs, dict) and lulu_costs.get('error'):
        return jsonify({'error': lulu_costs['error']}), 500
    
    pricing_options = {}
    for method, cost_data in lulu_costs.items():
        lulu_total = cost_data.get('total_cost', 0)
        customer_total = round(base_price_dollars + lulu_total, 2)
        customer_total_cents = int(customer_total * 100)
        
        net_profit = round(customer_total - base_price_dollars, 2)
        
        pricing_options[method] = {
            'name_es': cost_data.get('name_es', method),
            'name_en': cost_data.get('name_en', method),
            'days': cost_data.get('days', ''),
            'base_price': base_price_dollars,
            'lulu_cost': lulu_total,
            'lulu_shipping': cost_data.get('shipping_cost', 0),
            'customer_total': customer_total,
            'customer_total_cents': customer_total_cents,
            'net_profit': net_profit,

        }
    
    print(f"[DYNAMIC PRICE] {product_type} to {country_code}: {len(pricing_options)} options calculated")
    
    return jsonify({
        'product_type': product_type,
        'base_price': base_price_dollars,
        'country_code': country_code,
        'options': pricing_options
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


@app.route('/api/paypal/create-order', methods=['POST'])
def paypal_create_order():
    import requests as req
    data = request.get_json() or {}
    amount_usd = data.get('amount_usd')
    if not amount_usd:
        return jsonify({'error': 'amount_usd required'}), 400
    try:
        token = _get_paypal_access_token()

        purchase_unit = {
            "amount": {"currency_code": "USD", "value": str(round(float(amount_usd), 2))},
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
        print(f"[PAYPAL] Order {order_id} captured. Payer: {payer_email}")
        return jsonify({'success': True, 'orderID': order_id, 'payer_email': payer_email, 'status': status})
    except Exception as e:
        print(f"[PAYPAL] capture-order error: {e}")
        return jsonify({'error': str(e)}), 500


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
    
    story_data['want_print'] = bool(want_print)
    if email:
        story_data['customer_email'] = email
    
    shipping_method = data.get('shipping_method')
    if shipping_method and shipping_method != 'none':
        story_data['shipping_method'] = shipping_method
    
    if want_print and shipping_address:
        story_data['shipping_address'] = {
            'name': shipping_address.get('name', ''),
            'street1': shipping_address.get('street1', ''),
            'street2': shipping_address.get('street2', ''),
            'city': shipping_address.get('city', ''),
            'state_code': shipping_address.get('state_code', ''),
            'postcode': shipping_address.get('postcode', ''),
            'country_code': shipping_address.get('country_code', ''),
            'phone_number': shipping_address.get('phone_number', ''),
            'email': shipping_address.get('email', email)
        }
    
    with open(preview_file, 'w', encoding='utf-8') as f:
        json.dump(story_data, f, ensure_ascii=False, indent=2)
    
    print(f"[CHECKOUT-DATA] Saved for {preview_id}: want_print={want_print}, email={email}")
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
    
    client_ip = get_client_ip()
    preview_rate_limits.pop(client_ip, None)
    print(f"[RATE LIMIT] Cleared for IP {client_ip} after payment")
    
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

            _format_labels = {
                'digital': (('Cuento Digital (PDF)', 'Digital Story (PDF)'), _digital_price),
                'ebook': (('eBook Interactivo', 'Interactive eBook'), _ebook_price),
                'print': (('Libro Impreso', 'Printed Book'), _print_price),
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
        send_admin_purchase_notification(preview_id, _admin_pt, email, story_data)
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
        t = threading.Thread(
            target=_process_ebook_generation,
            args=(preview_id, email),
            daemon=True
        )
        t.start()
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
        elif not story_data.get('admin_notified', False):
            print(f"[PAYMENT] Pages already composed, launching Lulu post-payment processing...")
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
        elif want_print and not story_data.get('lulu_submitted', False):
            print(f"[PAYMENT] Quick Story with print option - starting Lulu PDF generation...")
            t = threading.Thread(
                target=_process_quick_story_print,
                args=(preview_id, email),
                daemon=True
            )
            t.start()
        elif not want_print and not story_data.get('visor_uploaded', False):
            print(f"[PAYMENT] Quick Story digital - generating visor as gift...")
            t = threading.Thread(
                target=_process_ebook_generation,
                args=(preview_id, email),
                daemon=True
            )
            t.start()
        else:
            print(f"[PAYMENT] Quick Story already processed for {preview_id}, skipping")
    
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
    
    try:
        with open(preview_file, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                print(f"[ORDER-COMPLETE] Empty JSON file for {preview_id}")
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
    
    return render_template('order_complete.html',
                          preview_id=preview_id,
                          story_data=story_data,
                          delivery_email=story_data.get('customer_email', ''),
                          email_sent=story_data.get('email_sent', False),
                          epub_url=epub_url,
                          is_baby=is_baby,
                          is_kids=is_kids,
                          is_furry_love=is_furry_love,
                          lang=story_data.get('lang', story_data.get('language', 'es')))


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
        lang = story_data.get('lang', story_data.get('language', 'es'))
    
    tracking_info = None
    if lulu_job_id:
        from services.lulu_api_service import get_print_job_status
        tracking_info = get_print_job_status(lulu_job_id)
    
    return render_template('track_order.html',
                          preview_id=preview_id,
                          story_data=story_data,
                          lulu_job_id=lulu_job_id,
                          tracking_info=tracking_info,
                          lang=lang)


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
        return jsonify({'success': True, 'message': 'Already composed'})
    
    print(f"[APPROVE] User approved scenes for {preview_id}, launching PDF composition + Lulu...")
    _trigger_personalized_book_composition(preview_id)
    
    return jsonify({'success': True, 'message': 'Composition started'})


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
    expected = len(story_data.get('pages', [])) or len(FS_CHECK.get(story_id, {}).get('pages', [])) or 8
    
    is_qs = not is_illustrated_book and story_id in FS_CHECK
    qs_text_composed = story_data.get('qs_text_composed', False)

    if generated_count >= expected and scenes_pending:
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
        if is_qs and not qs_text_composed:
            status = 'composing_text'
        else:
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

    return jsonify({
        'status': status,
        'generated': generated_count,
        'expected': expected,
        'scene_paths': scene_paths if status == 'complete' else [],
        'error': story_data.get('generation_error', '') if generation_failed else ''
    })

@app.route('/api/track-order/<preview_id>')
def api_track_order(preview_id):
    """API endpoint to get tracking info for a printed book order."""
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
            lulu_job_id = story_data.get('lulu_job_id')
    
    if not lulu_job_id:
        return jsonify({
            'success': False,
            'error': 'No print job ID found for this order'
        }), 404
    
    from services.lulu_api_service import get_print_job_status
    tracking_info = get_print_job_status(lulu_job_id)
    
    if tracking_info:
        return jsonify({
            'success': True,
            'tracking': tracking_info
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Could not retrieve tracking information'
        }), 500


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
    
    if current_count >= 2:
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
        scene_prompts = get_scene_prompts(story_id, child_name, gender, traits)
        scene_index = scene_num - 1
        
        if scene_index >= len(scene_prompts):
            return jsonify({'success': False, 'error': 'Scene prompt not found'}), 400
        
        prompt = scene_prompts[scene_index]
        
        from services.quick_stories.checkout import is_quick_story as check_qs_regen
        is_qs_regen = check_qs_regen(story_id)
        regen_aspect = "1:1" if age_range in ['0-1', '0-2'] or is_qs_regen else "3:4"
        
        print(f"[REGENERATE-QS] Regenerating scene {scene_num} for {preview_id} (attempt {current_count + 1}/2, aspect: {regen_aspect})")
        
        hair_length_regen = traits.get('hair_length', 'medium')
        child_age_regen = int(traits.get('child_age', '1'))
        
        from services.quick_stories.checkout import QUICK_STORY_IDS as QS_REGEN_IDS
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
            from services.quick_stories.checkout import is_quick_story as check_qs_compose, is_birthday_story as check_bday
            if check_qs_compose(story_id) and not check_bday(story_id):
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
            
            if story_data.get('lulu_submitted'):
                story_data['lulu_needs_refresh'] = True
                story_data['lulu_submitted'] = False
                print(f"[REGENERATE-QS] Lulu PDF marked for refresh after scene regeneration")
            
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


@app.route('/api/regenerate-page/<preview_id>/<int:page_num>', methods=['POST'])
def regenerate_page(preview_id, page_num):
    """Regenerate a single page (scene) for the illustrated book. Max 2 regenerations per page."""
    from services.illustrated_book_service import (
        generate_scene_complete, generate_closing_page, add_text_to_image, add_watermark, load_book_config
    )
    from services.personalized_books.generation import get_personalized_book_id
    
    preview_file = f'story_previews/{preview_id}.json'
    if not os.path.exists(preview_file):
        return jsonify({'success': False, 'error': 'Story not found'}), 404
    
    with open(preview_file, 'r', encoding='utf-8') as f:
        story_data = json.load(f)
    
    # Pages 3-21 are scene pages (19 scenes), page 22 is closing
    # Page numbers in array: page 3 = index 2, page 21 = index 20
    if page_num < 3 or page_num > 22:
        return jsonify({'success': False, 'error': 'Solo se pueden regenerar las páginas 3 a 22'}), 400
    
    # Check regeneration limit (max 2 per page)
    regen_counts = story_data.get('page_regenerations', {})
    page_key = str(page_num)
    current_count = regen_counts.get(page_key, 0)
    
    if current_count >= 2:
        return jsonify({
            'success': False, 
            'error': 'Has alcanzado el límite de 2 regeneraciones para esta página'
        }), 400
    
    story_id = story_data.get('story_id', 'dragon_garden_illustrated')
    book_id = get_personalized_book_id(story_id)
    book_config = load_book_config(book_id)
    
    if not book_config:
        return jsonify({'success': False, 'error': f'Book config not found for {book_id}'}), 400
    
    scenes = book_config.get('scenes', [])
    is_closing_page = (page_num == 22)
    
    if not is_closing_page:
        scene_index = page_num - 3  # Page 3 = scene 0, Page 21 = scene 18
        if scene_index < 0 or scene_index >= len(scenes):
            return jsonify({'success': False, 'error': f'Invalid scene index: {scene_index}'}), 400
        scene_config = scenes[scene_index]
    
    child_name = story_data.get('child_name', 'Child')
    gender = story_data.get('gender', 'neutral')
    lang = story_data.get('story_lang', story_data.get('lang', 'es'))
    traits = story_data.get('traits', {})
    
    page_label = "closing" if is_closing_page else f"scene {scene_index + 1}"
    print(f"[REGENERATE] Regenerating page {page_num} ({page_label}) for {preview_id}...")
    print(f"[REGENERATE] Regeneration count for this page: {current_count + 1}/2")
    
    try:
        ref_image_path = None
        ref_image_path_2 = None
        is_furry = book_id in ('furry_love', 'furry_love_adventure', 'furry_love_teen', 'furry_love_adult')
        
        if is_furry:
            human_preview = story_data.get('human_preview_path', '')
            if human_preview:
                human_ref = human_preview.lstrip('/')
                if os.path.exists(human_ref):
                    ref_image_path = human_ref
                    print(f"[REGENERATE] Furry love human reference: {ref_image_path}")
            pet_preview = story_data.get('pet_preview_path', '')
            if pet_preview:
                pet_ref = pet_preview.lstrip('/')
                if os.path.exists(pet_ref):
                    ref_image_path_2 = pet_ref
                    print(f"[REGENERATE] Furry love pet reference: {ref_image_path_2}")
        else:
            character_preview = story_data.get('character_preview', '')
            if character_preview:
                ref_candidate = character_preview.lstrip('/')
                if os.path.exists(ref_candidate):
                    ref_image_path = ref_candidate
                    print(f"[REGENERATE] Using FLUX 2 Dev reference for {book_id}: {ref_image_path}")
        
        if not ref_image_path:
            print(f"[REGENERATE] ERROR: No reference image found for {book_id}")
            return jsonify({'success': False, 'error': 'No se encontró la imagen de referencia. Por favor contacta soporte.'}), 400
        
        if is_closing_page:
            base_image = generate_closing_page(
                traits=traits,
                child_name=child_name,
                gender=gender,
                book_id=book_id,
                reference_image_path=ref_image_path,
                reference_image_path_2=ref_image_path_2
            )
            final_image = base_image
        else:
            base_image = generate_scene_complete(
                scene_config=scene_config,
                traits=traits,
                child_name=child_name,
                gender=gender,
                language=lang,
                book_id=book_id,
                reference_image_path=ref_image_path,
                reference_image_path_2=ref_image_path_2
            )
            
            text_key = f'text_{lang}'
            pet_name_regen = traits.get('pet_name', '') if is_furry else ''
            text = scene_config.get(text_key, scene_config.get('text_es', '')).replace('{name}', child_name).replace('{pet_name}', pet_name_regen)
            text_position = scene_config.get('text_position', 'bottom')
            final_image = add_text_to_image(base_image, text, position=text_position)
        
        # Save to the output directory
        output_dir = story_data.get('output_dir', f'generated/personalized_{preview_id[:8]}')
        os.makedirs(output_dir, exist_ok=True)
        
        # Save original (clean) version
        original_path = os.path.join(output_dir, f'page_{page_num:02d}.png')
        final_image.save(original_path, 'PNG')
        
        # Save preview (watermarked) version
        preview_path = os.path.join(output_dir, f'page_{page_num:02d}_preview.png')
        watermarked = add_watermark(final_image)
        watermarked.save(preview_path, 'PNG')
        
        print(f"[REGENERATE] Saved: {original_path} and {preview_path}")
        
        # Update regeneration count
        regen_counts[page_key] = current_count + 1
        story_data['page_regenerations'] = regen_counts
        
        # Update ALL image path arrays to ensure PDF generation uses new images
        page_index = page_num - 1  # Array index (0-based)
        
        # Update original_images
        original_images = story_data.get('original_images', [])
        if page_index < len(original_images):
            original_images[page_index] = f'/{original_path}'
            story_data['original_images'] = original_images
        
        # Update all_pages_original (used by email PDF)
        all_pages_original = story_data.get('all_pages_original', [])
        if page_index < len(all_pages_original):
            all_pages_original[page_index] = f'/{original_path}'
            story_data['all_pages_original'] = all_pages_original
        
        # Update original_scene_paths (fallback)
        original_scene_paths = story_data.get('original_scene_paths', [])
        if page_index < len(original_scene_paths):
            original_scene_paths[page_index] = f'/{original_path}'
            story_data['original_scene_paths'] = original_scene_paths
        
        # Update preview/watermarked images
        preview_images = story_data.get('images', [])
        if page_index < len(preview_images):
            preview_images[page_index] = f'/{preview_path}'
            story_data['images'] = preview_images
        
        # Update all_pages_preview
        all_pages_preview = story_data.get('all_pages_preview', [])
        if page_index < len(all_pages_preview):
            all_pages_preview[page_index] = f'/{preview_path}'
            story_data['all_pages_preview'] = all_pages_preview
        
        print(f"[REGENERATE] Updated arrays - page_index={page_index}, original_path={original_path}")
        
        story_data['visor_uploaded'] = False
        story_data['visor_url'] = ''
        story_data['pdf_printable_path'] = ''
        if story_data.get('lulu_submitted'):
            story_data['lulu_needs_refresh'] = True
            story_data['lulu_submitted'] = False
        print(f"[REGENERATE] Visor, PDF and Lulu flags reset — will regenerate on next confirm_and_send")
        
        # Save updated story data
        with open(preview_file, 'w', encoding='utf-8') as f:
            json.dump(story_data, f, ensure_ascii=False, indent=2)
        
        return jsonify({
            'success': True, 
            'message': f'Página {page_num} regenerada correctamente',
            'image_path': f'/{preview_path}',
            'regenerations_left': 2 - (current_count + 1)
        })
        
    except Exception as e:
        print(f"[REGENERATE] Error: {e}")
        import traceback
        traceback.print_exc()
        error_msg = 'El servicio de generación de imágenes está temporalmente no disponible. Por favor intenta de nuevo en unos minutos.' if 'FLUX' in str(e) or 'q_descale' in str(e) else str(e)
        return jsonify({'success': False, 'error': error_msg}), 500


@app.route('/api/confirm-and-send/<preview_id>', methods=['POST'])
def confirm_and_send(preview_id):
    """Confirm story review and send email to customer with file attachments"""
    from services.email_service import send_story_email_with_attachments
    
    preview_file = f'story_previews/{preview_id}.json'
    if not os.path.exists(preview_file):
        return jsonify({'success': False, 'error': 'Story not found'}), 404
    
    with open(preview_file, 'r', encoding='utf-8') as f:
        story_data = json.load(f)
    
    if story_data.get('email_sent'):
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
        
        with open(preview_file, 'r', encoding='utf-8') as f:
            story_data = json.load(f)
        visor_url = story_data.get('visor_url', '')
        
        if not visor_url and not story_data.get('scenes_pending', False) and not story_data.get('scenes_generating', False):
            try:
                print(f"[CONFIRM-SEND] No visor_url found, preparing visor for {preview_id}...")
                from services.vps_upload_service import prepare_and_upload
                is_gift = want_print
                visor_result = prepare_and_upload(story_data, preview_id, is_gift=is_gift)
                visor_url = visor_result.get('visor_url', '')
                story_data['visor_url'] = visor_url
                story_data['visor_uploaded'] = True
                with open(preview_file, 'w', encoding='utf-8') as f:
                    json.dump(story_data, f, ensure_ascii=False, indent=2)
                print(f"[CONFIRM-SEND] Visor prepared: {visor_url}")
            except Exception as visor_err:
                print(f"[CONFIRM-SEND] Visor preparation failed: {visor_err}")
        
        pdf_printable_path = story_data.get('pdf_printable_path')
        instructions_path_email = story_data.get('instructions_path')
        
        if visor_url and not pdf_printable_path:
            try:
                from services.quick_stories.checkout import is_quick_story as check_qs_cs
                if check_qs_cs(story_data.get('story_id', '')):
                    output_dir = f'generations/email/{preview_id}'
                    os.makedirs(output_dir, exist_ok=True)
                    from services.quick_stories.pdf_service import generate_quick_story_pdf
                    pdf_printable_path = f'{output_dir}/{safe_name}_imprimible.pdf'
                    generate_quick_story_pdf(story_data, pdf_printable_path)
                    from services.pdf_service import generate_print_instructions_pdf
                    qs_lang = story_data.get('lang', 'es')
                    instructions_path_email = f'{output_dir}/instrucciones_impresion.pdf'
                    generate_print_instructions_pdf(instructions_path_email, language=qs_lang)
                    print(f"[CONFIRM-SEND] PDFs generated: printable + instructions")
            except Exception as pdf_err:
                print(f"[CONFIRM-SEND] PDF generation failed: {pdf_err}")
        
        from services.email_service import send_ebook_email
        if visor_url:
            email_result = send_ebook_email(
                to_email=email,
                story_data=story_data,
                visor_url=visor_url,
                is_gift=want_print,
                pdf_printable_path=pdf_printable_path,
                instructions_path=instructions_path_email
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
        
        lulu_result = None
        is_quick_story = not is_personalized_book
        if want_print and is_quick_story:
            needs_lulu = not story_data.get('lulu_submitted') or story_data.get('lulu_needs_refresh')
            if needs_lulu:
                if story_data.get('lulu_needs_refresh'):
                    print(f"[CONFIRM-SEND] Scenes were regenerated after payment - refreshing Lulu PDFs...")
                    with open(preview_file, 'r', encoding='utf-8') as f:
                        story_data = json.load(f)
                    story_data['lulu_needs_refresh'] = False
                    with open(preview_file, 'w', encoding='utf-8') as f:
                        json.dump(story_data, f, ensure_ascii=False, indent=2)
                else:
                    print(f"[CONFIRM-SEND] Quick Story with want_print=True - launching Lulu print processing...")
                t = threading.Thread(
                    target=_process_quick_story_print,
                    args=(preview_id, email),
                    daemon=True
                )
                t.start()
                lulu_result = {'id': 'processing', 'success': True}
            else:
                print(f"[CONFIRM-SEND] Lulu already submitted for {preview_id}, skipping")
                lulu_result = {'id': story_data.get('lulu_job_id', 'already_submitted'), 'success': True}
        
        if want_print and is_personalized_book:
            needs_lulu = not story_data.get('lulu_submitted') and not story_data.get('lulu_job_id')
            if needs_lulu and story_data.get('pages_composed', False):
                lulu_order_folder = story_data.get('lulu_order_folder', '')
                if lulu_order_folder and os.path.exists(lulu_order_folder):
                    shipping_address = dict(story_data.get('shipping_address', {}))
                    if not shipping_address.get('email'):
                        shipping_address['email'] = story_data.get('customer_email', email)
                    if not shipping_address.get('phone_number') and shipping_address.get('phone'):
                        shipping_address['phone_number'] = shipping_address['phone']
                    is_admin_gift = story_data.get('admin_gift', False)
                    if shipping_address and shipping_address.get('name') and shipping_address.get('street1') and not is_admin_gift:
                        try:
                            from services.lulu_api_service import submit_print_order
                            from services.personalized_books.generation import get_lulu_title
                            
                            pb_book_id = story_data.get('story_id', '')
                            pb_traits = story_data.get('traits', {})
                            pet_name_lulu = pb_traits.get('pet_name', '') if pb_traits else ''
                            pb_lang = story_data.get('lang', story_data.get('language', 'es'))
                            book_title = get_lulu_title(pb_book_id, child_name, pb_lang, pet_name=pet_name_lulu)
                            shipping_level = story_data.get('shipping_method', 'MAIL')
                            
                            print(f"[CONFIRM-SEND] Submitting personalized book to Lulu...")
                            success, message, lulu_job_id = submit_print_order(
                                order_folder=lulu_order_folder,
                                title=book_title,
                                shipping_address=shipping_address,
                                shipping_level=shipping_level
                            )
                            
                            if success:
                                story_data['lulu_job_id'] = lulu_job_id
                                story_data['lulu_status'] = 'sent'
                                story_data['lulu_submitted'] = True
                                lulu_result = {'id': lulu_job_id, 'success': True}
                                print(f"[CONFIRM-SEND] Lulu order submitted: {lulu_job_id}")
                                
                                try:
                                    from services.email_service import send_lulu_order_notification, send_lulu_customer_notification
                                    base_url = os.environ.get('SITE_DOMAIN', os.environ.get('REPLIT_DEV_DOMAIN', 'magicmemoriesbooks.com'))
                                    folder_name = os.path.basename(lulu_order_folder)
                                    interior_url = f"https://{base_url}/lulu-files/{folder_name}/interior.pdf"
                                    cover_url = f"https://{base_url}/lulu-files/{folder_name}/cover.pdf"
                                    send_lulu_order_notification(
                                        order_folder=folder_name,
                                        lulu_job_id=lulu_job_id,
                                        title=book_title,
                                        customer_email=email,
                                        shipping_address=shipping_address,
                                        interior_url=interior_url,
                                        cover_url=cover_url
                                    )
                                    if email:
                                        send_lulu_customer_notification(
                                            to_email=email,
                                            child_name=child_name,
                                            book_title=book_title,
                                            shipping_address=shipping_address,
                                            shipping_method=shipping_level,
                                            lang=pb_lang
                                        )
                                    print(f"[CONFIRM-SEND] Admin + customer notifications sent")
                                except Exception as notif_err:
                                    print(f"[CONFIRM-SEND] Notifications failed: {notif_err}")
                            else:
                                story_data['lulu_status'] = 'failed'
                                story_data['lulu_error'] = message
                                lulu_result = {'id': None, 'success': False}
                                print(f"[CONFIRM-SEND] Lulu submission failed: {message}")
                            
                            with open(preview_file, 'w', encoding='utf-8') as f:
                                json.dump(story_data, f, ensure_ascii=False, indent=2)
                        except Exception as lulu_err:
                            print(f"[CONFIRM-SEND] Personalized book Lulu processing failed: {lulu_err}")
                            import traceback
                            traceback.print_exc()
                    elif is_admin_gift:
                        try:
                            from services.personalized_books.generation import get_lulu_title
                            pb_book_id = story_data.get('story_id', '')
                            pb_traits = story_data.get('traits', {})
                            pet_name_lulu = pb_traits.get('pet_name', '') if pb_traits else ''
                            pb_lang = story_data.get('lang', story_data.get('language', 'es'))
                            book_title = get_lulu_title(pb_book_id, child_name, pb_lang, pet_name=pet_name_lulu)
                            base_url = os.environ.get('SITE_DOMAIN', os.environ.get('REPLIT_DEV_DOMAIN', 'magicmemoriesbooks.com'))
                            folder_name = os.path.basename(lulu_order_folder)
                            interior_url = f"https://{base_url}/lulu-files/{folder_name}/interior.pdf"
                            cover_url = f"https://{base_url}/lulu-files/{folder_name}/cover.pdf"
                            from services.email_service import send_lulu_order_notification
                            send_lulu_order_notification(
                                order_folder=folder_name,
                                lulu_job_id='ADMIN-GIFT (pedido manual)',
                                title=book_title,
                                customer_email=email,
                                shipping_address={'name': child_name, 'street1': 'Pedido manual — sin dirección'},
                                interior_url=interior_url,
                                cover_url=cover_url
                            )
                            print(f"[CONFIRM-SEND] Admin gift: PDF links sent to admin, no Lulu submit")
                            lulu_result = {'id': 'admin_gift', 'success': True}
                        except Exception as gift_err:
                            print(f"[CONFIRM-SEND] Admin gift PDF notification failed: {gift_err}")
            elif story_data.get('lulu_job_id'):
                lulu_result = {'id': story_data.get('lulu_job_id'), 'success': True}
        
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
    
    if story_data.get('regeneration_used'):
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
    redirect_base = '/furry-love' if is_furry else '/story-selection'
    return jsonify({
        'success': True,
        'redirect_url': f'{redirect_base}?change=1&preview_id={preview_id}'
    })

@app.route('/generated/<path:filepath>')
def serve_generated_image(filepath):
    """Serve generated images from any subdirectory"""
    from flask import send_file
    image_path = f'generated/{filepath}'
    if os.path.exists(image_path):
        return send_file(image_path, mimetype='image/png')
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
    
    success = send_recovery_link_email(customer_email, child_name, recovery_url, lang)
    
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
        front_cover = story_data.get('original_cover', story_data.get('front_cover_path'))
        back_cover = story_data.get('back_cover_path')
        if back_cover and back_cover.startswith('/'):
            back_cover = back_cover[1:]
        if not back_cover or not os.path.exists(back_cover):
            _bid = story_data.get('story_id', story_data.get('book_id', ''))
            _fixed_backs = {
                "dragon_garden": "static/images/fixed_pages/dragon_garden_back_cover.png",
                "magic_chef": "static/images/fixed_pages/magic_chef_back_cover.png",
                "magic_inventor": "static/images/fixed_pages/magic_inventor_back_cover.png",
                "star_keeper": "static/images/fixed_pages/star_keeper_back_cover.png",
                "furry_love": "static/images/fixed_pages/furry_love_baby_back_cover.png",
                "furry_love_adventure": "static/images/fixed_pages/furry_love_adventure_back_cover.png",
                "furry_love_teen": "static/images/fixed_pages/furry_love_teen_back_cover.png",
                "furry_love_adult": "static/images/fixed_pages/furry_love_adult_back_cover.png"
            }
            back_cover = _fixed_backs.get(_bid, 'static/images/fixed_pages/back_cover.png')
        
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
            filename = f"{child_name_safe}_{story_template}_lulu_print.pdf"
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
    if format_type not in ('digital', 'print', 'lulu'):
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
    create_baby_quick_story_pdf(story_data, images, output_path, format_type, skip_sanitize=skip_sanitize)
    
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
    
    create_baby_quick_story_pdf(story_data, images, output_path, format_type='print', skip_sanitize=True)
    
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
    
    generate_print_instructions_pdf(output_path, language)
    
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
        download_name=f'{child_name_safe}_cover_spread_lulu.pdf',
        mimetype='application/pdf'
    )

@app.route('/api/check-openai')
def check_openai():
    has_key = bool(os.environ.get('OPENAI_API_KEY'))
    return jsonify({'configured': has_key})

with app.app_context():
    db.create_all()
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
    from services.lulu_storage import cleanup_expired_orders, get_storage_summary
    deleted = cleanup_expired_orders()
    summary = get_storage_summary()
    print(f"[LULU STORAGE] Storage summary: {summary['total_orders']} orders, {summary['total_size_mb']} MB")


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

def _get_demo_visor_url():
    """Get the homepage demo visor URL — uses relative path so it works on any server."""
    config = _load_admin_config()
    preview_id = config.get('demo_preview_id', '')
    if preview_id:
        return f'/visor_pb/?id={preview_id}'
    return ''

def _get_demo_visor_url_b():
    """Get the homepage demo visor URL for Portal B — uses relative path so it works on any server."""
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

ADMIN_PASSWORD = _load_admin_password()

def check_admin_auth():
    """Check if admin is authenticated via session."""
    return session.get('admin_logged_in', False)

@app.route('/admin')
def admin_login_page():
    """Admin login page."""
    if check_admin_auth():
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_login.html')

@app.route('/admin/login', methods=['POST'])
def admin_login():
    """Process admin login."""
    password = request.form.get('password', '')
    if password == _load_admin_password():
        session['admin_logged_in'] = True
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_login.html', error="Contraseña incorrecta")

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
    """Admin dashboard with all files."""
    if not check_admin_auth():
        return redirect(url_for('admin_login_page'))
    
    from services.lulu_storage import list_all_orders, get_storage_summary, cleanup_expired_orders
    import glob
    
    cleanup_expired_orders()
    
    lulu_orders = list_all_orders()
    lulu_summary = get_storage_summary()
    
    story_previews = []
    failed_orders = []
    preview_files = glob.glob('story_previews/*.json')
    for pf in sorted(preview_files, key=os.path.getmtime, reverse=True)[:50]:
        try:
            with open(pf, 'r') as f:
                data = json.load(f)
                pid = os.path.basename(pf).replace('.json', '')
                preview_info = {
                    'filename': os.path.basename(pf),
                    'preview_id': pid,
                    'child_name': data.get('child_name', 'Unknown'),
                    'story_id': data.get('story_id', ''),
                    'created': datetime.fromtimestamp(os.path.getmtime(pf)).strftime('%Y-%m-%d %H:%M'),
                    'has_scenes': len(data.get('scenes', [])) > 0
                }
                story_previews.append(preview_info)
                
                if data.get('lulu_status') == 'failed' and data.get('paid'):
                    failed_orders.append({
                        'preview_id': pid,
                        'child_name': data.get('child_name', 'Unknown'),
                        'story_id': data.get('story_id', ''),
                        'customer_email': data.get('customer_email', ''),
                        'lulu_error': data.get('lulu_error', 'Error desconocido'),
                        'payment_date': data.get('payment_date', ''),
                        'is_illustrated_book': data.get('is_illustrated_book', False),
                    })
        except:
            pass
    
    from models import RealStoryOrder
    try:
        db.session.rollback()
        real_stories_count = RealStoryOrder.query.count()
        preview_leads_count = PreviewLead.query.count()
    except Exception as db_err:
        production_logger.error(f"[ADMIN] DB query failed: {db_err}")
        real_stories_count = 0
        preview_leads_count = 0
        try:
            db.session.rollback()
        except Exception:
            pass
    
    current_demo_url = _get_demo_visor_url()
    current_demo_url_b = _get_demo_visor_url_b()
    _admin_cfg = _load_admin_config()
    current_demo_id = _admin_cfg.get('demo_preview_id', '')
    current_demo_id_b = _admin_cfg.get('demo_preview_id_b', '')
    for p in story_previews:
        try:
            pf = f"story_previews/{p['preview_id']}.json"
            with open(pf, 'r') as f:
                sd = json.load(f)
            p['visor_url'] = sd.get('visor_url', '')
            pid = p.get('preview_id', '')
            p['is_demo'] = bool(pid and (pid == current_demo_id or pid == current_demo_id_b))
            p['paid'] = sd.get('paid', False)
        except Exception:
            p['visor_url'] = ''
            p['is_demo'] = False
            p['paid'] = False

    return render_template('admin_dashboard.html', 
                          lulu_orders=lulu_orders, 
                          lulu_summary=lulu_summary,
                          story_previews=story_previews,
                          failed_orders=failed_orders,
                          real_stories_count=real_stories_count,
                          preview_leads_count=preview_leads_count,
                          current_demo_url=current_demo_url,
                          current_demo_url_b=current_demo_url_b)

@app.route('/admin/set-demo/<preview_id>', methods=['POST'])
def admin_set_demo(preview_id):
    """Set a story as the homepage demo."""
    if not check_admin_auth():
        return jsonify({'error': 'Not authorized'}), 403
    preview_file = f'story_previews/{preview_id}.json'
    if not os.path.exists(preview_file):
        return jsonify({'error': 'Story not found'}), 404
    with open(preview_file, 'r') as f:
        sd = json.load(f)
    visor_url = sd.get('visor_url', '')
    if not visor_url:
        return jsonify({'error': 'This story has no visor URL yet. Generate the ebook first.'}), 400
    _save_admin_config({'demo_visor_url': visor_url, 'demo_preview_id': preview_id})
    return jsonify({'success': True, 'visor_url': visor_url})

@app.route('/admin/reset-rate-limits', methods=['POST'])
def admin_reset_rate_limits():
    """Clear all preview rate limits (useful for testing)."""
    if not check_admin_auth():
        return jsonify({'error': 'Not authorized'}), 403
    preview_rate_limits.clear()
    return jsonify({'success': True, 'message': 'Rate limits cleared'})

@app.route('/admin/clear-demo', methods=['POST'])
def admin_clear_demo():
    """Remove the homepage demo."""
    if not check_admin_auth():
        return jsonify({'error': 'Not authorized'}), 403
    _save_admin_config({'demo_visor_url': '', 'demo_preview_id': ''})
    return jsonify({'success': True})

@app.route('/admin/set-demo-b/<preview_id>', methods=['POST'])
def admin_set_demo_b(preview_id):
    """Set a story as the Portal B homepage demo (dragon/no-photo)."""
    if not check_admin_auth():
        return jsonify({'error': 'Not authorized'}), 403
    preview_file = f'story_previews/{preview_id}.json'
    if not os.path.exists(preview_file):
        return jsonify({'error': 'Story not found'}), 404
    with open(preview_file, 'r') as f:
        sd = json.load(f)
    visor_url = sd.get('visor_url', '')
    if not visor_url:
        return jsonify({'error': 'This story has no visor URL yet. Generate the ebook first.'}), 400
    _save_admin_config({'demo_visor_url_b': visor_url, 'demo_preview_id_b': preview_id})
    return jsonify({'success': True, 'visor_url': visor_url})

@app.route('/admin/clear-demo-b', methods=['POST'])
def admin_clear_demo_b():
    """Remove the Portal B homepage demo."""
    if not check_admin_auth():
        return jsonify({'error': 'Not authorized'}), 403
    _save_admin_config({'demo_visor_url_b': '', 'demo_preview_id_b': ''})
    return jsonify({'success': True})

@app.route('/admin/lulu-orders')
def admin_lulu_orders():
    """Admin page to view Lulu orders storage."""
    if not check_admin_auth():
        return redirect(url_for('admin_login_page'))
    
    from services.lulu_storage import list_all_orders, get_storage_summary, cleanup_expired_orders
    
    cleanup_expired_orders()
    
    orders = list_all_orders()
    summary = get_storage_summary()
    
    return render_template('admin_lulu_orders.html', orders=orders, summary=summary)


@app.route('/admin/lulu-orders/<path:folder_name>/<filename>')
def download_lulu_file(folder_name, filename):
    """Download a file from a Lulu order folder."""
    if not check_admin_auth():
        return redirect(url_for('admin_login_page'))
    
    from flask import send_from_directory
    import os
    
    if filename not in ['interior.pdf', 'cover.pdf', 'metadata.json']:
        return "File not allowed", 403
    
    folder_path = os.path.join('lulu_orders', folder_name)
    if not os.path.exists(folder_path):
        return "Order not found", 404
    
    return send_from_directory(folder_path, filename, as_attachment=True)


@app.route('/lulu-files/<path:folder_name>/<filename>')
def serve_lulu_file_public(folder_name, filename):
    """
    Serve Lulu order files publicly for Lulu API to download.
    This endpoint must be accessible without authentication for Lulu's servers.
    """
    from flask import send_from_directory
    import os
    
    if filename not in ['interior.pdf', 'cover.pdf']:
        return "File not allowed", 403
    
    folder_path = os.path.join('lulu_orders', folder_name)
    if not os.path.exists(folder_path):
        return "Order not found", 404
    
    file_path = os.path.join(folder_path, filename)
    if not os.path.exists(file_path):
        return "File not found", 404
    
    return send_from_directory(folder_path, filename, mimetype='application/pdf')


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
    
    return render_template('admin_preview.html', preview=data, preview_id=preview_id)


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


@app.route('/admin/lulu-order/<folder_name>')
def admin_view_lulu_order(folder_name):
    """View a specific Lulu order with cover preview."""
    if not check_admin_auth():
        return redirect(url_for('admin_login_page'))
    
    from services.lulu_storage import get_order_by_folder
    
    order = get_order_by_folder(folder_name)
    if not order:
        return "Order not found", 404
    
    interior_path = os.path.join(order['folder_path'], 'interior.pdf')
    cover_preview_exists = os.path.exists(os.path.join(order['folder_path'], 'cover_preview.png'))
    interior_exists = os.path.exists(interior_path)
    cover_pdf_exists = os.path.exists(os.path.join(order['folder_path'], 'cover.pdf'))
    
    if interior_exists:
        order['interior_size_mb'] = round(os.path.getsize(interior_path) / 1024 / 1024, 1)
    
    preview_id = order.get('order_id', '')
    shipping_address = {}
    lulu_error = ''
    lulu_status = ''
    if preview_id:
        preview_file = f'story_previews/{preview_id}.json'
        if os.path.exists(preview_file):
            with open(preview_file, 'r', encoding='utf-8') as f:
                story_data = json.load(f)
            shipping_address = story_data.get('shipping_address', {})
            lulu_error = story_data.get('lulu_error', '')
            lulu_status = story_data.get('lulu_status', '')
    
    return render_template('admin_lulu_order_detail.html', 
                          order=order, 
                          cover_preview_exists=cover_preview_exists,
                          interior_exists=interior_exists,
                          cover_pdf_exists=cover_pdf_exists,
                          preview_id=preview_id,
                          shipping_address=shipping_address,
                          lulu_error=lulu_error,
                          lulu_status=lulu_status)


@app.route('/admin/lulu-order/<folder_name>/cover-preview')
def admin_get_cover_preview(folder_name):
    """Serve the cover preview image."""
    if not check_admin_auth():
        return "Unauthorized", 401
    
    folder_path = os.path.join('lulu_orders', folder_name)
    preview_path = os.path.join(folder_path, 'cover_preview.png')
    
    if os.path.exists(preview_path):
        return send_from_directory(folder_path, 'cover_preview.png')
    return "Preview not found", 404


@app.route('/admin/lulu-order/<folder_name>/approve', methods=['POST'])
def admin_approve_lulu_order(folder_name):
    """Approve order and send to Lulu for printing."""
    if not check_admin_auth():
        return jsonify({"error": "Unauthorized"}), 401
    
    from services.lulu_storage import get_order_by_folder, update_order_status
    from services.lulu_api_service import submit_print_order
    
    order = get_order_by_folder(folder_name)
    if not order:
        return jsonify({"error": "Order not found"}), 404
    
    interior_path = os.path.join(order['folder_path'], 'interior.pdf')
    cover_path = os.path.join(order['folder_path'], 'cover.pdf')
    
    if not os.path.exists(interior_path) or not os.path.exists(cover_path):
        return jsonify({"error": "Missing PDF files"}), 400
    
    try:
        result = submit_print_order(
            interior_pdf_path=interior_path,
            cover_pdf_path=cover_path,
            title=f"El Jardín del Dragón - {order.get('child_name', 'Unknown')}",
            quantity=1
        )
        
        if result.get('success'):
            update_order_status(order['folder_path'], 'sent_to_lulu', result.get('print_job_id'))
            return jsonify({"success": True, "message": "Order sent to Lulu!", "job_id": result.get('print_job_id')})
        else:
            update_order_status(order['folder_path'], 'failed')
            return jsonify({"error": result.get('error', 'Unknown error')}), 500
    except Exception as e:
        update_order_status(order['folder_path'], 'failed')
        return jsonify({"error": str(e)}), 500


@app.route('/admin/lulu-order/<folder_name>/regenerate-cover', methods=['POST'])
def admin_regenerate_cover(folder_name):
    """Regenerate the cover for an order."""
    if not check_admin_auth():
        return jsonify({"error": "Unauthorized"}), 401
    
    from services.lulu_storage import get_order_by_folder, save_cover_preview, update_order_status
    from services.illustrated_book_service import generate_cover_spread, save_cover_as_pdf
    from services.personalized_books.generation import get_personalized_book_id
    
    order = get_order_by_folder(folder_name)
    if not order:
        return jsonify({"error": "Order not found"}), 404
    
    try:
        traits = order.get('traits', {
            'hair_color': 'brown',
            'hair_length': 'medium', 
            'hair_type': 'wavy',
            'eye_color': 'brown',
            'skin_tone': 'medium'
        })
        child_name = order.get('child_name', 'Unknown')
        gender = order.get('gender', 'female')
        language = order.get('language', 'es')
        author_name = order.get('author_name', 'Magic Memories Books')
        story_id = order.get('story_id', 'dragon_garden_illustrated')
        book_id = get_personalized_book_id(story_id)
        
        cover_spread = generate_cover_spread(traits, child_name, gender, language, book_id, author_name)
        
        save_cover_preview(order['folder_path'], cover_spread)
        
        cover_pdf_path = os.path.join(order['folder_path'], 'cover.pdf')
        save_cover_as_pdf(cover_spread, cover_pdf_path)
        
        update_order_status(order['folder_path'], 'pending_review')
        
        return jsonify({"success": True, "message": "Cover regenerated successfully!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/admin/test-lulu-connection')
def admin_test_lulu_connection():
    """Test connection to Lulu API (sandbox or production)."""
    if not check_admin_auth():
        return redirect(url_for('admin_login_page'))
    
    from services.lulu_api_service import get_access_token, is_sandbox_mode, LULU_API_BASE
    
    result = {
        'sandbox_mode': is_sandbox_mode(),
        'api_base': LULU_API_BASE,
        'connection_success': False,
        'message': ''
    }
    
    token = get_access_token()
    if token:
        result['connection_success'] = True
        result['message'] = f"Conexión exitosa a Lulu {'SANDBOX' if is_sandbox_mode() else 'PRODUCTION'}"
    else:
        result['message'] = "Error de conexión. Verifica LULU_CLIENT_KEY y LULU_CLIENT_SECRET"
    
    return jsonify(result)


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


@app.route('/admin/retry-lulu/<preview_id>', methods=['POST'])
def admin_retry_lulu_submission(preview_id):
    """Retry Lulu submission for a failed order."""
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
    
    order_folder = story_data.get('lulu_order_folder')
    is_illustrated = story_data.get('is_illustrated_book', False)

    if not order_folder or not os.path.exists(order_folder):
        if is_illustrated:
            return jsonify({"error": "Lulu order folder not found. No se puede regenerar automáticamente para libros ilustrados."}), 400
        try:
            from services.quick_stories.pdf_service import generate_quick_story_lulu_pdfs
            from services.lulu_storage import create_order_folder, save_interior_pdf, save_cover_pdf
            _regen_child = story_data.get('child_name', 'Unknown')
            _regen_scenes = story_data.get('original_scene_paths', story_data.get('scene_paths', []))
            _regen_cover = story_data.get('original_cover', story_data.get('front_cover_path', story_data.get('cover_image', '')))
            if _regen_cover and _regen_cover.startswith('/'):
                _regen_cover = _regen_cover[1:]
            _regen_scenes = [p.lstrip('/') for p in _regen_scenes if p]
            if not _regen_scenes:
                return jsonify({"error": "No se encontraron imágenes para regenerar los PDFs"}), 400
            _back_cover = 'static/images/quick_story_back_cover.png'
            if not os.path.exists(_back_cover):
                _back_cover = 'static/images/fixed_pages/back_cover.png'
            _regen_dir = f'generations/lulu_retry/{preview_id}'
            os.makedirs(_regen_dir, exist_ok=True)
            generate_quick_story_lulu_pdfs(
                story_data=story_data,
                images=_regen_scenes,
                front_cover_path=_regen_cover,
                back_cover_path=_back_cover,
                interior_output=os.path.join(_regen_dir, 'interior.pdf'),
                cover_output=os.path.join(_regen_dir, 'cover.pdf'),
                skip_sanitize=True
            )
            _regen_email = story_data.get('customer_email', '')
            order_folder = create_order_folder(f'qs_retry_{preview_id[:8]}', _regen_child, _regen_email)
            save_interior_pdf(order_folder, os.path.join(_regen_dir, 'interior.pdf'))
            save_cover_pdf(order_folder, os.path.join(_regen_dir, 'cover.pdf'))
            story_data['lulu_order_folder'] = order_folder
            import shutil as _shutil_regen
            _shutil_regen.rmtree(_regen_dir, ignore_errors=True)
            print(f"[RETRY] Regenerated PDFs for {preview_id} → {order_folder}")
        except Exception as _regen_err:
            import traceback
            traceback.print_exc()
            return jsonify({"error": f"Error regenerando PDFs: {_regen_err}"}), 500

    try:
        from services.lulu_api_service import submit_print_order
        from services.lulu_storage import update_order_status
        
        story_id = story_data.get('story_id', '')
        child_name = story_data.get('child_name', 'Unknown')
        lang = story_data.get('lang', 'es')
        
        is_illustrated = story_data.get('is_illustrated_book', False)
        if is_illustrated:
            from services.personalized_books.generation import get_personalized_book_id, get_lulu_title
            book_id = get_personalized_book_id(story_id)
            pet_name_lulu = story_data.get('traits', {}).get('pet_name', '') if story_data.get('traits') else story_data.get('pet_name', '')
            book_title = get_lulu_title(book_id, child_name, lang, pet_name=pet_name_lulu)
        else:
            story_name = story_data.get('story_name', story_data.get('title', 'Quick Story'))
            book_title = f"{story_name} - {child_name}"
        
        shipping_address = dict(shipping_address)
        if not shipping_address.get('email'):
            shipping_address['email'] = story_data.get('customer_email', '')
        if not shipping_address.get('phone_number') and shipping_address.get('phone'):
            shipping_address['phone_number'] = shipping_address['phone']
        shipping_level = story_data.get('shipping_method', 'MAIL')
        success, message, lulu_job_id = submit_print_order(
            order_folder=order_folder,
            title=book_title,
            shipping_address=shipping_address,
            shipping_level=shipping_level
        )
        
        if success and lulu_job_id:
            story_data['lulu_job_id'] = lulu_job_id
            story_data['lulu_status'] = 'sent'
            story_data['lulu_error'] = None
            story_data['lulu_submitted'] = True
            update_order_status(order_folder, 'sent_to_lulu', lulu_job_id)
            import shutil as _shutil_retry
            _shutil_retry.rmtree(order_folder, ignore_errors=True)

            with open(preview_file, 'w', encoding='utf-8') as f:
                json.dump(story_data, f, ensure_ascii=False, indent=2)
            
            try:
                from services.email_service import send_lulu_order_notification, send_lulu_customer_notification
                folder_name = os.path.basename(order_folder) if order_folder else preview_id
                send_lulu_order_notification(
                    order_folder=folder_name,
                    lulu_job_id=lulu_job_id,
                    title=book_title,
                    customer_email=story_data.get('customer_email', ''),
                    shipping_address=shipping_address
                )
                cust_email = story_data.get('customer_email', '')
                if cust_email:
                    send_lulu_customer_notification(
                        to_email=cust_email,
                        child_name=child_name,
                        book_title=book_title,
                        shipping_address=shipping_address,
                        shipping_method=shipping_level,
                        lang=lang
                    )
            except Exception:
                pass
            
            return jsonify({
                "success": True, 
                "message": f"Order sent to Lulu! Job ID: {lulu_job_id}",
                "lulu_job_id": lulu_job_id
            })
        else:
            story_data['lulu_error'] = message or 'Failed to submit'
            with open(preview_file, 'w', encoding='utf-8') as f:
                json.dump(story_data, f, ensure_ascii=False, indent=2)
            return jsonify({"error": message or "Failed to submit to Lulu"}), 500
            
    except Exception as e:
        app.logger.error(f"Error retrying Lulu submission: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/admin/send-lulu-resolved/<preview_id>', methods=['POST'])
def admin_send_lulu_resolved(preview_id):
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
    lulu_job_id = story_data.get('lulu_job_id', '')

    if not customer_email:
        return jsonify({"error": "No customer email found"}), 400
    if not lulu_job_id:
        return jsonify({"error": "No Lulu job ID found"}), 400

    results = {}

    try:
        from services.email_service import send_lulu_resolved_email
        ok = send_lulu_resolved_email(customer_email, child_name, str(lulu_job_id), lang)
        results['customer_email'] = 'sent' if ok else 'failed'
    except Exception as e:
        results['customer_email'] = f'error: {e}'

    try:
        from services.email_service import send_lulu_order_notification, send_lulu_customer_notification
        shipping_address = story_data.get('shipping_address', {})
        story_id = story_data.get('story_id', '')
        is_illustrated = story_data.get('is_illustrated_book', False)
        if is_illustrated:
            from services.personalized_books.generation import get_personalized_book_id, get_lulu_title
            book_id = get_personalized_book_id(story_id)
            pet_name_lulu = story_data.get('traits', {}).get('pet_name', '') if story_data.get('traits') else story_data.get('pet_name', '')
            book_title = get_lulu_title(book_id, child_name, lang, pet_name=pet_name_lulu)
        else:
            story_name = story_data.get('story_name', story_data.get('title', 'Quick Story'))
            book_title = f"{story_name} - {child_name}"
        send_lulu_order_notification(
            order_folder=preview_id,
            lulu_job_id=str(lulu_job_id),
            title=book_title,
            customer_email=customer_email,
            shipping_address=shipping_address
        )
        results['admin_email'] = 'sent'
        shipping_method = story_data.get('shipping_method', 'MAIL')
        send_lulu_customer_notification(
            to_email=customer_email,
            child_name=child_name,
            book_title=book_title,
            shipping_address=shipping_address,
            shipping_method=shipping_method,
            lang=lang
        )
        results['customer_print_email'] = 'sent'
    except Exception as e:
        results['admin_email'] = f'error: {e}'

    story_data['lulu_resolved_email_sent'] = True
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
    
    html = """
    <!DOCTYPE html>
    <html><head><meta charset="UTF-8"><title>Admin - Reintentos Pendientes</title>
    <style>
        body { font-family: Arial, sans-serif; background: #f8f4ff; padding: 20px; }
        .container { max-width: 1000px; margin: 0 auto; }
        h1 { color: #7c3aed; }
        .card { background: white; border-radius: 12px; padding: 20px; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
        .status-retrying { border-left: 4px solid #f59e0b; }
        .status-exhausted { border-left: 4px solid #dc2626; }
        .status-fixed { border-left: 4px solid #22c55e; }
        table { width: 100%%; border-collapse: collapse; }
        td { padding: 6px 10px; }
        .label { font-weight: bold; color: #4b5563; width: 150px; }
        .btn { display: inline-block; padding: 8px 16px; border-radius: 8px; text-decoration: none; color: white; font-weight: bold; margin: 4px; cursor: pointer; border: none; }
        .btn-retry { background: #f59e0b; }
        .btn-view { background: #7c3aed; }
        .btn-back { background: #6b7280; }
        .badge { display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 12px; font-weight: bold; color: white; }
        .badge-retrying { background: #f59e0b; }
        .badge-exhausted { background: #dc2626; }
        .empty { text-align: center; color: #9ca3af; padding: 40px; }
    </style></head><body>
    <div class="container">
        <a href="/admin/dashboard" class="btn btn-back">← Dashboard</a>
        <h1>🔄 Reintentos Pendientes</h1>
    """
    
    if not pending_retries:
        html += '<div class="card empty"><h3>✅ No hay reintentos pendientes</h3><p>Todos los libros se generaron correctamente.</p></div>'
    
    for item in pending_retries:
        status_class = 'status-exhausted' if item['retry_exhausted'] else 'status-retrying'
        badge_class = 'badge-exhausted' if item['retry_exhausted'] else 'badge-retrying'
        badge_text = '🚨 AGOTADO' if item['retry_exhausted'] else '🔄 Reintentando'
        
        html += f"""
        <div class="card {status_class}">
            <span class="badge {badge_class}">{badge_text}</span>
            <table>
                <tr><td class="label">Preview ID:</td><td>{item['preview_id']}</td></tr>
                <tr><td class="label">Nombre:</td><td>{item['child_name']}</td></tr>
                <tr><td class="label">Cuento:</td><td>{item['story_id']}</td></tr>
                <tr><td class="label">Cliente:</td><td>{item['customer_email']}</td></tr>
                <tr><td class="label">Escenas fallidas:</td><td style="color: #dc2626; font-weight: bold;">{', '.join(str(s) for s in item['failed_scenes'])}</td></tr>
                <tr><td class="label">Reintentos:</td><td>{item['retry_count']}/{item['max_retries']}</td></tr>
                <tr><td class="label">Fecha:</td><td>{item['created']}</td></tr>
            </table>
            <div style="margin-top: 10px;">
                <a href="/admin/preview/{item['preview_id']}" class="btn btn-view">Ver Preview</a>
                <form action="/admin/retry-scenes/{item['preview_id']}" method="POST" style="display: inline;">
                    <button type="submit" class="btn btn-retry">🔄 Reintentar Ahora</button>
                </form>
            </div>
        </div>
        """
    
    html += "</div></body></html>"
    return html


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
                    'has_lulu_folder': bool(data.get('lulu_order_folder')) and os.path.exists(data.get('lulu_order_folder', '')),
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
    if not lulu_folder or not os.path.exists(lulu_folder):
        return "PDFs not ready yet. Please wait for composition to finish.", 404
    
    folder_name = os.path.basename(lulu_folder)
    interior_exists = os.path.exists(os.path.join(lulu_folder, 'interior.pdf'))
    cover_exists = os.path.exists(os.path.join(lulu_folder, 'cover.pdf'))
    
    return render_template('admin_gift_download.html',
                          story_data=story_data,
                          preview_id=preview_id,
                          folder_name=folder_name,
                          interior_exists=interior_exists,
                          cover_exists=cover_exists)


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
                          lulu_folder_name=lulu_folder_name,
                          interior_exists=interior_exists,
                          cover_pdf_exists=cover_pdf_exists,
                          interior_size_mb=interior_size_mb)


@app.route('/admin/delete-preview/<preview_id>', methods=['POST'])
def admin_delete_preview(preview_id):
    """Delete a story preview and its associated files."""
    if not check_admin_auth():
        return jsonify({'success': False, 'error': 'Not authorized'}), 403
    
    preview_file = f'story_previews/{preview_id}.json'
    if not os.path.exists(preview_file):
        return jsonify({'success': False, 'error': 'Not found'}), 404
    
    try:
        with open(preview_file, 'r') as f:
            data = json.load(f)
        
        try:
            StoryBackup.query.filter_by(preview_id=preview_id).delete()
            db.session.commit()
            print(f"[ADMIN-DELETE] Removed {preview_id} from story_backups DB")
        except Exception as db_err:
            db.session.rollback()
            print(f"[ADMIN-DELETE] DB cleanup failed for {preview_id}: {db_err}")
        
        _purge_story_files(preview_id, data, include_lulu=True)
        os.remove(preview_file)
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


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
    if not check_admin_auth():
        return redirect(url_for('admin_login_page'))
    leads = PreviewLead.query.order_by(PreviewLead.created_at.desc()).limit(200).all()
    total_leads = PreviewLead.query.count()
    unique_emails = db.session.query(db.func.count(db.distinct(PreviewLead.email))).scalar() or 0
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_leads = PreviewLead.query.filter(PreviewLead.created_at >= today_start).count()
    return render_template('admin_preview_leads.html', leads=leads, total_leads=total_leads, unique_emails=unique_emails, today_leads=today_leads)


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
    return redirect(url_for('admin_preview_leads'))


@app.route('/admin/preview-leads/delete-all', methods=['POST'])
def admin_delete_all_preview_leads():
    if not check_admin_auth():
        return redirect(url_for('admin_login_page'))
    PreviewLead.query.delete()
    db.session.commit()
    return redirect(url_for('admin_preview_leads'))


@app.route('/admin/uploaded-photos')
def admin_uploaded_photos():
    """Admin page to view and manage uploaded user photos (72h retention)."""
    if not check_admin_auth():
        return redirect(url_for('admin_login_page'))
    
    import glob as glob_module
    photos = []
    upload_dir = 'generated/uploads/furry_photos'
    if os.path.exists(upload_dir):
        for filepath in sorted(glob_module.glob(os.path.join(upload_dir, '*')), key=os.path.getmtime, reverse=True):
            if os.path.isfile(filepath):
                stat = os.stat(filepath)
                upload_time = datetime.fromtimestamp(stat.st_mtime)
                age_hours = (datetime.now() - upload_time).total_seconds() / 3600
                hours_remaining = max(0, 72 - age_hours)
                photos.append({
                    'filename': os.path.basename(filepath),
                    'filepath': filepath,
                    'upload_time': upload_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'age_hours': round(age_hours, 1),
                    'hours_remaining': round(hours_remaining, 1),
                    'size_kb': round(stat.st_size / 1024, 1),
                    'expired': hours_remaining <= 0
                })
    
    total_photos = len(photos)
    expired_count = sum(1 for p in photos if p['expired'])
    
    return render_template('admin_photos.html', 
                          photos=photos,
                          total_photos=total_photos,
                          expired_count=expired_count)

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
    if os.path.exists(upload_dir):
        for filepath in glob_module.glob(os.path.join(upload_dir, '*')):
            if os.path.isfile(filepath):
                age_hours = (datetime.now() - datetime.fromtimestamp(os.path.getmtime(filepath))).total_seconds() / 3600
                if age_hours >= 72:
                    os.remove(filepath)
                    deleted += 1
    print(f"[ADMIN] Deleted {deleted} expired photos")
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
    
    pages = data.get('pages', [])
    
    return render_template('admin_quick_story_detail.html', 
                          preview_id=preview_id,
                          story=data,
                          pages=pages)


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
                progress_callback=_scene_progress_cb
            )
            
            if len(pages) < 10:
                raise Exception(f"Only {len(pages)} pages generated, expected at least 10")
            
            composed_dir = f'generated/composed_{preview_id}'
            os.makedirs(composed_dir, exist_ok=True)
            
            saved = save_book_as_images(pages, composed_dir, prefix='page', with_watermark=True)
            original_paths = saved.get('original', [])
            preview_paths = saved.get('preview', [])
            
            formatted_scene_paths = [p if p.startswith('/') else f'/{p}' for p in preview_paths if p]
            formatted_original_paths = [p if p.startswith('/') else f'/{p}' for p in original_paths if p]
            
            cover_ref = ref_path
            cover_ref_2 = ref_path_2
            if book_id in ('furry_love', 'furry_love_adventure', 'furry_love_teen', 'furry_love_adult'):
                cover_raw_saved = story_data.get('cover_raw_path', '')
                if cover_raw_saved:
                    raw_path = cover_raw_saved.lstrip('/')
                    if os.path.exists(raw_path):
                        cover_ref = raw_path
                        cover_ref_2 = None
                        production_logger.info(f"[BG-GEN] Furry love: using RAW pre-generated cover for cover spread: {raw_path}")
                if cover_ref == ref_path:
                    output_dir_check = story_data.get('output_dir', '')
                    if output_dir_check:
                        raw_fallback = os.path.join(output_dir_check, 'cover_raw.png')
                        if os.path.exists(raw_fallback):
                            cover_ref = raw_fallback
                            cover_ref_2 = None
                            production_logger.info(f"[BG-GEN] Furry love: found cover_raw.png on disk: {raw_fallback}")
            
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
        _qs_total = len(story_data.get('pages', [])) or len(_FS_TOTAL.get(story_id, {}).get('pages', [])) or 8
        _generation_progress[preview_id] = {'generated': 0, 'total': _qs_total}

        def _qs_progress_cb(done, total):
            _generation_progress[preview_id] = {'generated': done, 'total': total}
            _write_progress(preview_id, done, total)

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
        
        if scene_paths and pages_data:
            from services.quick_stories.image_composer import compose_baby_text_on_image, compose_kids_text_on_image
            from PIL import Image as PILImage
            
            for idx, sp in enumerate(scene_paths):
                if not sp:
                    continue
                raw_path = sp.lstrip('/')
                if not os.path.exists(raw_path):
                    continue
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
        
        story_data['scene_paths'] = formatted_scene_paths
        story_data['images'] = formatted_scene_paths
        story_data['original_scene_paths'] = formatted_scene_paths
        story_data['original_images'] = formatted_scene_paths
        if closing_image:
            story_data['closing_image'] = closing_image if closing_image.startswith('/') else f'/{closing_image}'
            closing_msg = story_data.get('closing_message', '')
            if closing_msg and not is_birthday_story:
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
        
        is_digital_only = story_data.get('paid', False) and not story_data.get('want_print', False) and not story_data.get('visor_uploaded', False)
        customer_email = story_data.get('customer_email', '')
        if is_qs and is_digital_only and customer_email:
            production_logger.info(f"[BG-GEN] Quick Story Digital - auto-launching visor upload + email for {preview_id}")
            try:
                _process_ebook_generation(preview_id, customer_email)
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

        customer_email = story_data.get('customer_email')
        if is_final_attempt and customer_email:
            try:
                from services.email_service import send_generation_failed_email
                base_url = os.environ.get('SITE_DOMAIN', os.environ.get('REPLIT_DEV_DOMAIN', 'magicmemoriesbooks.com'))
                retry_url = f"https://{base_url}/retry-story/{preview_id}"
                lang = story_data.get('lang', story_data.get('language', 'es'))
                send_generation_failed_email(customer_email, child_name, retry_url, lang)
            except Exception as email_err:
                production_logger.error(f"[BG-GEN] Failed to send error email: {email_err}")

        if is_final_attempt:
            try:
                import traceback as tb
                from services.email_service import send_admin_error_email
                send_admin_error_email('_generate_scenes_background', preview_id, str(e), tb.format_exc())
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
                52,
                0.05
            )
            
            page_index = scene_idx + 3
            original_path = os.path.join(composed_dir, f"page_{page_index:02d}.png")
            final_page.save(original_path, "PNG")
            
            preview_path = os.path.join(composed_dir, f"page_{page_index:02d}_preview.png")
            watermarked = add_watermark(final_page)
            watermarked.save(preview_path, "PNG")
            
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
    
    try:
        from services.illustrated_book_service import generate_full_book, save_book_as_images
        from services.personalized_books.generation import get_personalized_book_id
        
        book_id = get_personalized_book_id(story_id)
        composed_dir = f'generated/composed_{preview_id}'
        os.makedirs(composed_dir, exist_ok=True)
        
        scenes_already_ready = story_data.get('book_scenes_ready', False)
        
        if scenes_already_ready:
            production_logger.info(f"[BG-COMPOSE] Scenes already generated (two-stage flow), loading from disk...")
            from PIL import Image
            
            original_paths_on_disk = story_data.get('original_scene_paths', story_data.get('original_images', []))
            pages = []
            for p in original_paths_on_disk:
                clean_p = p.lstrip('/')
                if os.path.exists(clean_p):
                    pages.append(Image.open(clean_p))
                else:
                    production_logger.warning(f"[BG-COMPOSE] Missing page: {clean_p}")
            
            production_logger.info(f"[BG-COMPOSE] Loaded {len(pages)} pages from disk")
            
            if len(pages) < 10:
                production_logger.warning(f"[BG-COMPOSE] Only {len(pages)} pages loaded from disk, falling back to full generation")
                scenes_already_ready = False
            
            original_paths = [p.lstrip('/') for p in original_paths_on_disk if os.path.exists(p.lstrip('/'))]
            preview_paths_data = story_data.get('scene_paths', story_data.get('images', []))
            preview_paths = [p.lstrip('/') for p in preview_paths_data if os.path.exists(p.lstrip('/'))]
        
        if not scenes_already_ready:
            ref_image_path = None
            ref_image_path_2 = None
            if book_id == "magic_inventor":
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
            pages, _failed = generate_full_book(
                book_id=book_id,
                child_name=child_name,
                traits=traits,
                gender=gender,
                language=lang,
                dedication_text=dedication,
                for_print=True,
                reference_image_path=ref_image_path,
                reference_image_path_2=ref_image_path_2
            )
            
            saved_paths = save_book_as_images(pages, composed_dir, prefix='page', with_watermark=True)
            original_paths = saved_paths['original']
            preview_paths = saved_paths['preview']
        
        content_original = original_paths[2:-2]
        content_preview = preview_paths[2:-2]
        
        formatted_original = [f'/{p}' if not p.startswith('/') else p for p in content_original]
        formatted_preview = [f'/{p}' if not p.startswith('/') else p for p in content_preview]
        
        all_original = [f'/{p}' if not p.startswith('/') else p for p in original_paths]
        all_preview = [f'/{p}' if not p.startswith('/') else p for p in preview_paths]
        
        production_logger.info(f"[BG-COMPOSE] Total pages: {len(original_paths)}, Content pages: {len(content_original)}")
        
        story_data['scene_paths'] = formatted_original
        story_data['images'] = formatted_preview
        story_data['original_images'] = formatted_original
        story_data['all_pages_original'] = all_original
        story_data['all_pages_preview'] = all_preview
        story_data['composed_pages_dir'] = composed_dir
        story_data['pages_composed'] = True
        story_data['scenes_pending'] = False
        story_data['scenes_generating'] = False
        
        from services.illustrated_book_service import generate_cover_spread, add_watermark
        
        existing_cover_spread_path = story_data.get('cover_spread_path', '')
        cover_was_regenerated = False
        if scenes_already_ready and existing_cover_spread_path and os.path.exists(existing_cover_spread_path):
            cover_raw_path_check = story_data.get('cover_raw_path', '')
            if cover_raw_path_check and os.path.exists(cover_raw_path_check):
                spread_mtime = os.path.getmtime(existing_cover_spread_path)
                raw_mtime = os.path.getmtime(cover_raw_path_check)
                if raw_mtime > spread_mtime:
                    cover_was_regenerated = True
                    production_logger.info(f"[BG-COMPOSE] Cover was regenerated after spread creation, regenerating cover spread with new cover...")
        
        if scenes_already_ready and existing_cover_spread_path and os.path.exists(existing_cover_spread_path) and not cover_was_regenerated:
            production_logger.info(f"[BG-COMPOSE] Loading existing cover spread from disk...")
            from PIL import Image
            cover_spread = Image.open(existing_cover_spread_path)
        else:
            ref_image_path = None
            ref_image_path_2_cover = None
            if book_id == "magic_inventor":
                character_preview = story_data.get('character_preview', '')
                if character_preview:
                    ref_candidate = character_preview.lstrip('/')
                    if os.path.exists(ref_candidate):
                        ref_image_path = ref_candidate
            elif book_id in ("furry_love", "furry_love_adventure", "furry_love_teen", "furry_love_adult"):
                cover_raw_saved = story_data.get('cover_raw_path', '')
                if cover_raw_saved:
                    raw_path = cover_raw_saved.lstrip('/')
                    if os.path.exists(raw_path):
                        ref_image_path = raw_path
                        production_logger.info(f"[BG-COMPOSE] Furry love: using RAW pre-generated cover (no text overlay): {raw_path}")
                if not ref_image_path:
                    cover_raw = story_data.get('original_cover', story_data.get('cover_image', ''))
                    if cover_raw:
                        cover_raw_path_fallback = cover_raw.lstrip('/')
                        if os.path.exists(cover_raw_path_fallback):
                            ref_image_path = cover_raw_path_fallback
                            production_logger.info(f"[BG-COMPOSE] Furry love: using pre-generated cover (with overlay) as fallback: {cover_raw_path_fallback}")
                if not ref_image_path:
                    human_preview = story_data.get('human_preview_path', '')
                    if human_preview:
                        human_ref = human_preview.lstrip('/')
                        if os.path.exists(human_ref):
                            ref_image_path = human_ref
                    pet_preview = story_data.get('pet_preview_path', '')
                    if pet_preview:
                        pet_ref = pet_preview.lstrip('/')
                        if os.path.exists(pet_ref):
                            ref_image_path_2_cover = pet_ref
            
            production_logger.info(f"[BG-COMPOSE] Generating cover spread...")
            author_name = story_data.get('author_name', 'Magic Memories Books')
            cover_spread = generate_cover_spread(traits, child_name, gender, lang, book_id, author_name, reference_image_path=ref_image_path, reference_image_path_2=ref_image_path_2_cover)
        
        DPI = 300
        MM_TO_INCH = 1 / 25.4
        wrap_px = int(19.05 * MM_TO_INCH * DPI)
        board_w_px = int(213.175 * MM_TO_INCH * DPI)
        spine_px = int(6.35 * MM_TO_INCH * DPI)
        
        front_x = wrap_px + board_w_px + spine_px
        front_cover = cover_spread.crop((front_x, wrap_px, front_x + board_w_px, wrap_px + int(303.35 * MM_TO_INCH * DPI)))
        back_cover = cover_spread.crop((wrap_px, wrap_px, wrap_px + board_w_px, wrap_px + int(303.35 * MM_TO_INCH * DPI)))
        
        front_cover_original_path = os.path.join(composed_dir, 'front_cover.png')
        front_cover.save(front_cover_original_path, 'PNG')
        story_data['front_cover_path'] = f'/{front_cover_original_path}'
        
        back_cover_original_path = os.path.join(composed_dir, 'back_cover.png')
        back_cover.save(back_cover_original_path, 'PNG')
        story_data['back_cover_path'] = f'/{back_cover_original_path}'
        
        front_cover_preview = add_watermark(front_cover)
        cover_preview_path = os.path.join(composed_dir, 'cover_preview.png')
        front_cover_preview.save(cover_preview_path, 'PNG')
        story_data['cover_preview'] = f'/{cover_preview_path}'
        
        back_cover_preview = add_watermark(back_cover)
        back_cover_preview_path = os.path.join(composed_dir, 'back_cover_preview.png')
        back_cover_preview.save(back_cover_preview_path, 'PNG')
        story_data['back_cover_preview'] = f'/{back_cover_preview_path}'
        
        cover_spread_save_path = os.path.join(composed_dir, 'cover_spread.png')
        cover_spread.save(cover_spread_save_path, 'PNG')
        story_data['cover_spread_path'] = cover_spread_save_path
        
        production_logger.info(f"[BG-COMPOSE] Cover spread saved! Generating Lulu print files...")
        from services.lulu_storage import create_order_folder, save_cover_preview, update_order_status
        from services.illustrated_book_service import generate_illustrated_book_pdf, save_cover_as_pdf
        
        order_folder = create_order_folder(
            order_id=preview_id,
            child_name=child_name,
            email=customer_email
        )
        
        interior_path = os.path.join(order_folder, 'interior.pdf')
        generate_illustrated_book_pdf(pages, interior_path, for_print=True)
        
        cover_path = os.path.join(order_folder, 'cover.pdf')
        save_cover_as_pdf(cover_spread, cover_path)
        
        save_cover_preview(order_folder, cover_spread)
        
        story_data['lulu_order_folder'] = order_folder
        
        is_admin_gift = story_data.get('admin_gift', False)
        
        if is_admin_gift:
            production_logger.info(f"[BG-COMPOSE] ADMIN GIFT book - skipping Lulu submission. PDFs saved for manual download: {order_folder}")
            update_order_status(order_folder, 'admin_gift_ready')
            story_data['lulu_status'] = 'admin_gift'
            
            admin_gift_email = story_data.get('admin_gift_email', '') or story_data.get('customer_email', '')
            if admin_gift_email:
                try:
                    from services.personalized_books.generation import get_lulu_title
                    pet_name_lulu = traits.get('pet_name', '') if traits else ''
                    book_title = get_lulu_title(book_id, child_name, lang, pet_name=pet_name_lulu)
                    
                    base_url = os.environ.get('SITE_DOMAIN', os.environ.get('REPLIT_DEV_DOMAIN', 'magicmemoriesbooks.com'))
                    folder_name = os.path.basename(order_folder)
                    interior_url = f"https://{base_url}/lulu-files/{folder_name}/interior.pdf"
                    cover_url = f"https://{base_url}/lulu-files/{folder_name}/cover.pdf"
                    
                    from services.email_service import send_admin_gift_email
                    send_admin_gift_email(
                        to_email=admin_gift_email,
                        book_title=book_title,
                        child_name=child_name,
                        interior_url=interior_url,
                        cover_url=cover_url,
                        order_folder=folder_name
                    )
                    production_logger.info(f"[BG-COMPOSE] Admin gift email sent to {admin_gift_email}")
                    story_data['admin_gift_email_sent'] = True
                except Exception as email_err:
                    production_logger.error(f"[BG-COMPOSE] Admin gift email failed: {email_err}")
            
            try:
                from services.vps_upload_service import prepare_and_upload
                visor_result = prepare_and_upload(story_data, preview_id, is_gift=True)
                visor_url = visor_result.get('visor_url')
                story_data['visor_url'] = visor_url
                story_data['visor_uuid'] = visor_result.get('book_uuid')
                story_data['visor_uploaded'] = True
                story_data['ebook_is_gift'] = True
                production_logger.info(f"[BG-COMPOSE] Admin gift visor prepared: {visor_url}")
            except Exception as visor_err:
                production_logger.error(f"[BG-COMPOSE] Admin gift visor preparation failed: {visor_err}")
        else:
            shipping_address = story_data.get('shipping_address')
            if shipping_address and shipping_address.get('name') and shipping_address.get('street1'):
                if not shipping_address.get('email'):
                    shipping_address['email'] = customer_email or story_data.get('customer_email', '')
                if not shipping_address.get('phone_number') and shipping_address.get('phone'):
                    shipping_address['phone_number'] = shipping_address['phone']
                production_logger.info(f"[BG-COMPOSE] Sending to Lulu for printing...")
                from services.lulu_api_service import submit_print_order
                from services.personalized_books.generation import get_lulu_title
                
                pet_name_lulu = traits.get('pet_name', '') if traits else ''
                book_title = get_lulu_title(book_id, child_name, lang, pet_name=pet_name_lulu)
                shipping_level = story_data.get('shipping_method', 'MAIL')
                
                success, message, lulu_job_id = submit_print_order(
                    order_folder=order_folder,
                    title=book_title,
                    shipping_address=shipping_address,
                    shipping_level=shipping_level
                )
                
                if success:
                    production_logger.info(f"[BG-COMPOSE] Lulu order submitted! Job ID: {lulu_job_id}")
                    update_order_status(order_folder, 'sent_to_lulu')
                    story_data['lulu_job_id'] = lulu_job_id
                    story_data['lulu_status'] = 'sent'
                    
                    try:
                        from services.email_service import send_lulu_order_notification, send_lulu_customer_notification
                        base_url = os.environ.get('SITE_DOMAIN', os.environ.get('REPLIT_DEV_DOMAIN', 'magicmemoriesbooks.com'))
                        folder_name = os.path.basename(order_folder)
                        interior_url = f"https://{base_url}/lulu-files/{folder_name}/interior.pdf"
                        cover_url = f"https://{base_url}/lulu-files/{folder_name}/cover.pdf"
                        
                        send_lulu_order_notification(
                            order_folder=folder_name,
                            lulu_job_id=lulu_job_id,
                            title=book_title,
                            customer_email=customer_email,
                            shipping_address=shipping_address,
                            interior_url=interior_url,
                            cover_url=cover_url
                        )
                        if customer_email:
                            send_lulu_customer_notification(
                                to_email=customer_email,
                                child_name=child_name,
                                book_title=book_title,
                                shipping_address=shipping_address,
                                shipping_method=shipping_level,
                                lang=lang
                            )
                    except Exception as notif_error:
                        production_logger.error(f"[BG-COMPOSE] Notifications failed: {notif_error}")
                else:
                    production_logger.error(f"[BG-COMPOSE] Lulu submission failed: {message}")
                    update_order_status(order_folder, 'failed')
                    story_data['lulu_status'] = 'failed'
                    story_data['lulu_error'] = message
                    
                    if customer_email:
                        try:
                            from services.email_service import send_lulu_failure_email
                            send_lulu_failure_email(
                                to_email=customer_email,
                                child_name=child_name,
                                error_message=message,
                                lang=lang,
                                preview_id=preview_id
                            )
                            production_logger.info(f"[BG-COMPOSE] Lulu failure notification sent to {customer_email}")
                        except Exception as fail_email_err:
                            production_logger.error(f"[BG-COMPOSE] Failed to send Lulu failure email: {fail_email_err}")
                    
                    try:
                        from services.email_service import send_lulu_failure_admin_email
                        send_lulu_failure_admin_email(
                            preview_id=preview_id,
                            child_name=child_name,
                            error_message=message,
                            customer_email=customer_email or '',
                            shipping_address=shipping_address,
                            story_id=story_data.get('story_id', ''),
                            product_type='personalized'
                        )
                    except Exception as admin_err:
                        production_logger.error(f"[BG-COMPOSE] Failed to send admin failure email: {admin_err}")
            else:
                production_logger.info(f"[BG-COMPOSE] No shipping address - order saved for manual review")
                if order_folder:
                    update_order_status(order_folder, 'pending_review')
        
        if customer_email and not is_admin_gift:
            try:
                visor_url = None
                try:
                    from services.vps_upload_service import prepare_and_upload
                    visor_result = prepare_and_upload(story_data, preview_id, is_gift=True)
                    visor_url = visor_result.get('visor_url')
                    story_data['visor_url'] = visor_url
                    story_data['visor_uuid'] = visor_result.get('book_uuid')
                    story_data['visor_uploaded'] = True
                    story_data['ebook_is_gift'] = True
                    production_logger.info(f"[BG-COMPOSE] Gift visor prepared: {visor_url}")
                except Exception as visor_err:
                    production_logger.error(f"[BG-COMPOSE] Visor preparation failed: {visor_err}")
                
                if visor_url:
                    from services.email_service import send_ebook_email
                    send_ebook_email(
                        to_email=customer_email,
                        story_data=story_data,
                        visor_url=visor_url,
                        is_gift=True
                    )
                else:
                    from services.email_service import send_story_email_with_attachments
                    from services.pdf_service import create_pdf_from_images
                    safe_name = child_name.replace(' ', '_').replace("'", "")
                    os.makedirs(f'generations/email/{preview_id}', exist_ok=True)
                    pdf_digital_path = f'generations/email/{preview_id}/{safe_name}_digital.pdf'
                    pdf_pages = []
                    front_cover_p = story_data.get('front_cover_path', '')
                    if front_cover_p:
                        pdf_pages.append(front_cover_p.lstrip('/'))
                    pdf_pages.extend([p.lstrip('/') for p in formatted_original])
                    back_cover_p = story_data.get('back_cover_path', '')
                    if back_cover_p and os.path.exists(back_cover_p.lstrip('/')):
                        pdf_pages.append(back_cover_p.lstrip('/'))
                    create_pdf_from_images(pdf_pages, pdf_digital_path, skip_sanitize=True)
                    send_story_email_with_attachments(
                        to_email=customer_email,
                        story_data=story_data,
                        pdf_digital_path=pdf_digital_path,
                        pdf_printable_path=None,
                        epub_path=None,
                        instructions_path=None,
                        age_group='personalized',
                        preview_id=preview_id,
                        visor_url=None
                    )
                
                story_data['email_sent'] = True
                story_data['email_sent_date'] = datetime.now().isoformat()
                production_logger.info(f"[BG-COMPOSE] Customer email sent to {customer_email}")
            except Exception as email_err:
                production_logger.error(f"[BG-COMPOSE] Email failed: {email_err}")
        
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
            send_admin_error_email('_compose_personalized_book_background', preview_id, str(e), tb_text)
        except Exception:
            pass

        raise


_post_payment_locks = set()
_post_payment_lock = threading.Lock()
_ebook_processing_locks = set()
_ebook_processing_lock = threading.Lock()

def _process_personalized_book_post_payment(preview_id, customer_email):
    """
    Background thread: generate Lulu PDFs (300 DPI) + send email after payment.
    Called from process_payment (client-side) after PayPal confirmation.
    Uses lock to prevent duplicate concurrent processing.
    """
    with _post_payment_lock:
        if preview_id in _post_payment_locks:
            print(f"[POST-PAYMENT] Already processing {preview_id}, skipping duplicate")
            return
        _post_payment_locks.add(preview_id)

    from services.pdf_service import create_pdf_from_images
    from services.illustrated_book_service import generate_illustrated_book_pdf, save_cover_as_pdf
    from services.lulu_storage import create_order_folder, save_interior_pdf, save_cover_pdf
    from services.email_service import send_story_email_with_attachments
    from PIL import Image

    try:
        preview_file = f'story_previews/{preview_id}.json'
        if not os.path.exists(preview_file):
            print(f"[POST-PAYMENT] Preview file not found: {preview_file}")
            return

        with open(preview_file, 'r', encoding='utf-8') as f:
            story_data = json.load(f)
        
        if story_data.get('admin_notified'):
            print(f"[POST-PAYMENT] Already processed {preview_id}, skipping")
            return

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
        cover_spread_path = story_data.get('cover_spread_path', '')

        if front_cover and front_cover.startswith('/'):
            front_cover = front_cover[1:]
        if back_cover and back_cover.startswith('/'):
            back_cover = back_cover[1:]
        if cover_spread_path and cover_spread_path.startswith('/'):
            cover_spread_path = cover_spread_path[1:]

        if not back_cover or not os.path.exists(back_cover):
            fixed_back_covers = {
                "dragon_garden": "static/images/fixed_pages/dragon_garden_back_cover.png",
                "magic_chef": "static/images/fixed_pages/magic_chef_back_cover.png",
                "magic_inventor": "static/images/fixed_pages/magic_inventor_back_cover.png",
                "star_keeper": "static/images/fixed_pages/star_keeper_back_cover.png",
                "furry_love": "static/images/fixed_pages/furry_love_baby_back_cover.png",
                "furry_love_adventure": "static/images/fixed_pages/furry_love_adventure_back_cover.png",
                "furry_love_teen": "static/images/fixed_pages/furry_love_teen_back_cover.png",
                "furry_love_adult": "static/images/fixed_pages/furry_love_adult_back_cover.png"
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

        lulu_folder = story_data.get('lulu_order_folder', '')
        if not lulu_folder or not os.path.exists(lulu_folder):
            lulu_folder = create_order_folder(preview_id, child_name, customer_email)
            story_data['lulu_order_folder'] = lulu_folder

        if all_pages:
            print(f"[POST-PAYMENT] Creating 300 DPI print interior PDF...")
            clean_interior = [p.lstrip('/') for p in all_pages]
            interior_images = []
            for p in clean_interior:
                if os.path.exists(p):
                    img = Image.open(p).convert('RGB')
                    interior_images.append(img)
                else:
                    print(f"[POST-PAYMENT] Missing interior page: {p}")

            if interior_images:
                interior_pdf_path = os.path.join(lulu_folder, 'interior.pdf')
                generate_illustrated_book_pdf(interior_images, interior_pdf_path, for_print=True)
                print(f"[POST-PAYMENT] Interior PDF saved: {interior_pdf_path} ({len(interior_images)} pages)")

        if cover_spread_path and os.path.exists(cover_spread_path):
            print(f"[POST-PAYMENT] Creating cover spread PDF...")
            cover_img = Image.open(cover_spread_path).convert('RGB')
            cover_pdf_path = os.path.join(lulu_folder, 'cover.pdf')
            save_cover_as_pdf(cover_img, cover_pdf_path)
            print(f"[POST-PAYMENT] Cover PDF saved: {cover_pdf_path}")
        else:
            print(f"[POST-PAYMENT] No cover spread found at: {cover_spread_path}")

        story_data['assets_ready'] = True
        story_data['lulu_order_folder'] = lulu_folder
        story_data['files_generated'] = {
            'pdf_digital': pdf_digital_path,
            'lulu_interior': os.path.join(lulu_folder, 'interior.pdf') if os.path.exists(os.path.join(lulu_folder, 'interior.pdf')) else None,
            'lulu_cover': os.path.join(lulu_folder, 'cover.pdf') if os.path.exists(os.path.join(lulu_folder, 'cover.pdf')) else None,
        }

        with open(preview_file, 'w', encoding='utf-8') as f:
            json.dump(story_data, f, ensure_ascii=False, indent=2)

        print(f"[POST-PAYMENT] Assets prepared for {preview_id}, awaiting user approval")
        print(f"[POST-PAYMENT]   Lulu folder: {lulu_folder}")

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


def _process_ebook_generation(preview_id, customer_email):
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
        
        if story_data.get('visor_uploaded'):
            print(f"[EBOOK] Already uploaded to visor for {preview_id}, skipping")
            return
        
        max_wait = 600
        wait_interval = 10
        waited = 0
        while waited < max_wait:
            with open(preview_file, 'r', encoding='utf-8') as f:
                story_data = json.load(f)
            
            scenes_pending = story_data.get('scenes_pending', False)
            scenes_generating = story_data.get('scenes_generating', False)
            
            if not scenes_pending and not scenes_generating:
                print(f"[EBOOK] Scenes ready for {preview_id} (waited {waited}s)")
                break
            
            print(f"[EBOOK] Waiting for scenes to complete for {preview_id} ({waited}s elapsed, pending={scenes_pending}, generating={scenes_generating})")
            import time
            time.sleep(wait_interval)
            waited += wait_interval
        
        if waited >= max_wait:
            print(f"[EBOOK] WARNING: Timed out waiting for scenes after {max_wait}s for {preview_id}, proceeding anyway")
        
        with open(preview_file, 'r', encoding='utf-8') as f:
            story_data = json.load(f)
        
        if story_data.get('visor_uploaded'):
            print(f"[EBOOK] Already uploaded to visor for {preview_id} (uploaded while waiting), skipping")
            return
        
        is_gift = story_data.get('ebook_is_gift', False)
        product_type = story_data.get('product_type', '')
        story_id = story_data.get('story_id', '')
        
        from services.quick_stories.checkout import is_quick_story as check_qs
        is_qs = check_qs(story_id)
        is_digital_purchase = product_type in ('qs_digital', '') and is_qs and not is_gift
        
        print(f"[EBOOK] Preparing visor upload for {preview_id} (is_gift={is_gift}, is_digital={is_digital_purchase})")
        
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
        
        pdf_printable_path = None
        instructions_path = None
        
        if is_digital_purchase:
            try:
                child_name = story_data.get('child_name', 'Historia')
                safe_name = child_name.replace(' ', '_').replace("'", "")
                output_dir = f'generations/email/{preview_id}'
                os.makedirs(output_dir, exist_ok=True)
                
                from services.quick_stories.pdf_service import generate_quick_story_pdf
                pdf_printable_path = f'{output_dir}/{safe_name}_imprimible.pdf'
                generate_quick_story_pdf(story_data, pdf_printable_path)
                print(f"[EBOOK] Printable PDF generated: {pdf_printable_path}")
                
                from services.pdf_service import generate_print_instructions_pdf
                lang = story_data.get('lang', 'es')
                instructions_path = f'{output_dir}/instrucciones_impresion.pdf'
                generate_print_instructions_pdf(instructions_path, language=lang)
                print(f"[EBOOK] Instructions PDF generated: {instructions_path}")
                
                story_data['pdf_printable_path'] = pdf_printable_path
                story_data['instructions_path'] = instructions_path
                with open(preview_file, 'w', encoding='utf-8') as f:
                    json.dump(story_data, f, ensure_ascii=False, indent=2)
                    
            except Exception as pdf_err:
                print(f"[EBOOK] PDF generation failed (non-fatal): {pdf_err}")
                import traceback
                traceback.print_exc()
        
        story_data['assets_ready'] = True
        with open(preview_file, 'w', encoding='utf-8') as f:
            json.dump(story_data, f, ensure_ascii=False, indent=2)
        
        print(f"[EBOOK] Assets ready for {preview_id}, awaiting user approval to send email")

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
            send_admin_error_email('_process_ebook_generation', preview_id, str(e), tb_text)
        except Exception:
            pass
    finally:
        with _ebook_processing_lock:
            _ebook_processing_locks.discard(preview_id)


def _process_quick_story_print(preview_id, customer_email):
    """
    Background thread: generate Lulu PDFs for Quick Story saddle stitch printing.
    Called when want_print=true after payment.
    """
    from services.quick_stories.pdf_service import generate_quick_story_lulu_pdfs
    from services.lulu_storage import create_order_folder, save_interior_pdf, save_cover_pdf
    try:
        preview_file = f'story_previews/{preview_id}.json'
        if not os.path.exists(preview_file):
            print(f"[QS-PRINT] Preview file not found: {preview_file}")
            return

        with open(preview_file, 'r', encoding='utf-8') as f:
            story_data = json.load(f)

        if story_data.get('lulu_submitted'):
            print(f"[QS-PRINT] Already submitted to Lulu for {preview_id}, skipping")
            return

        child_name = story_data.get('child_name', 'Historia')
        story_name = story_data.get('story_name', 'Quick Story')
        shipping_address = story_data.get('shipping_address', {})

        print(f"[QS-PRINT] Processing Quick Story print for {preview_id} ({child_name})")

        scene_paths = story_data.get('original_scene_paths', story_data.get('scene_paths', []))
        cover_image = story_data.get('original_cover', story_data.get('front_cover_path', story_data.get('cover_image', '')))
        
        if cover_image and cover_image.startswith('/'):
            cover_image = cover_image[1:]

        clean_scenes = []
        for p in scene_paths:
            if p and isinstance(p, str):
                clean_scenes.append(p.lstrip('/'))

        if not clean_scenes:
            print(f"[QS-PRINT] No scene images found for {preview_id}")
            return

        back_cover = 'static/images/quick_story_back_cover.png'
        if not os.path.exists(back_cover):
            back_cover = 'static/images/fixed_pages/back_cover.png'

        lulu_folder = f'generations/lulu/{preview_id}'
        os.makedirs(lulu_folder, exist_ok=True)

        interior_output = os.path.join(lulu_folder, 'interior.pdf')
        cover_output = os.path.join(lulu_folder, 'cover.pdf')

        print(f"[QS-PRINT] Generating Lulu PDFs: {len(clean_scenes)} scenes")
        interior_path, cover_path = generate_quick_story_lulu_pdfs(
            story_data=story_data,
            images=clean_scenes,
            front_cover_path=cover_image,
            back_cover_path=back_cover,
            interior_output=interior_output,
            cover_output=cover_output,
            skip_sanitize=True
        )

        print(f"[QS-PRINT] PDFs generated: interior={interior_path}, cover={cover_path}")

        lulu_folder_name = f'qs_{preview_id[:8]}'
        order_folder = create_order_folder(lulu_folder_name, child_name, customer_email)
        save_interior_pdf(order_folder, interior_path)
        save_cover_pdf(order_folder, cover_path)

        from services.lulu_api_service import get_public_file_url
        interior_url = get_public_file_url(order_folder, 'interior.pdf')
        cover_url = get_public_file_url(order_folder, 'cover.pdf')

        QS_POD_PACKAGE_ID = '0850X0850FCPRESS080CW444GXX'
        
        lulu_job_id = None
        lulu_success = False
        is_admin_gift_qs = story_data.get('admin_gift', False)
        if shipping_address and shipping_address.get('name') and shipping_address.get('street1') and not is_admin_gift_qs:
            from services.lulu_api_service import submit_print_order
            
            lulu_shipping = {
                'name': shipping_address.get('name', ''),
                'street1': shipping_address.get('street1', ''),
                'street2': shipping_address.get('street2', ''),
                'city': shipping_address.get('city', ''),
                'state_code': shipping_address.get('state_code', ''),
                'postal_code': shipping_address.get('postcode', shipping_address.get('postal_code', '')),
                'country_code': shipping_address.get('country_code', 'US'),
                'email': customer_email,
                'phone_number': shipping_address.get('phone_number', '')
            }
            
            shipping_level = story_data.get('shipping_method', 'MAIL')
            print(f"[QS-PRINT] Submitting to Lulu with pod_package_id={QS_POD_PACKAGE_ID}, shipping={shipping_level}")
            lulu_success, lulu_msg, lulu_job_id = submit_print_order(
                order_folder=order_folder,
                title=f"{story_name} - {child_name}",
                shipping_address=lulu_shipping,
                shipping_level=shipping_level,
                pod_package_id=QS_POD_PACKAGE_ID,
                interior_url=interior_url,
                cover_url=cover_url
            )
            print(f"[QS-PRINT] Lulu submit result: success={lulu_success}, msg={lulu_msg}, job_id={lulu_job_id}")
        elif is_admin_gift_qs:
            print(f"[QS-PRINT] Admin gift order — skipping Lulu submission, PDFs will be emailed to admin")
            lulu_job_id = 'ADMIN-GIFT (pedido manual)'
        else:
            print(f"[QS-PRINT] WARNING: No valid shipping address, skipping Lulu submission")

        from services.email_service import send_lulu_order_notification, send_lulu_customer_notification
        qs_book_title = f"{story_name} - {child_name} (Quick Story Print)"
        admin_result = send_lulu_order_notification(
            order_folder=lulu_folder_name,
            lulu_job_id=lulu_job_id or 'N/A',
            title=qs_book_title,
            customer_email=customer_email,
            shipping_address=shipping_address,
            interior_url=interior_url or '',
            cover_url=cover_url or ''
        )
        if customer_email and lulu_success:
            qs_lang = story_data.get('lang', 'es')
            send_lulu_customer_notification(
                to_email=customer_email,
                child_name=child_name,
                book_title=qs_book_title,
                shipping_address=shipping_address,
                shipping_method=shipping_level,
                lang=qs_lang
            )

        with open(preview_file, 'r', encoding='utf-8') as f:
            story_data = json.load(f)
        
        story_data['lulu_submitted'] = lulu_success
        story_data['lulu_submitted_date'] = datetime.now().isoformat()
        story_data['lulu_job_id'] = lulu_job_id
        story_data['lulu_interior_url'] = interior_url
        story_data['lulu_cover_url'] = cover_url
        story_data['lulu_needs_refresh'] = False
        story_data['lulu_order_folder'] = order_folder
        story_data['admin_notified'] = admin_result.get('success', False) or admin_result.get('simulated', False)

        if lulu_success:
            story_data['lulu_status'] = 'sent'
            import shutil as _shutil_qs
            _shutil_qs.rmtree(lulu_folder, ignore_errors=True)
        elif shipping_address and shipping_address.get('name'):
            story_data['lulu_status'] = 'failed'
            story_data['lulu_error'] = lulu_msg or 'Unknown error'
            
            if customer_email:
                try:
                    from services.email_service import send_lulu_failure_email
                    qs_lang = story_data.get('lang', story_data.get('language', 'es'))
                    send_lulu_failure_email(
                        to_email=customer_email,
                        child_name=child_name,
                        error_message=lulu_msg or 'Unknown error',
                        lang=qs_lang,
                        preview_id=preview_id
                    )
                except Exception as fail_email_err:
                    print(f"[QS-PRINT] Failed to send Lulu failure email: {fail_email_err}")
            
            try:
                from services.email_service import send_lulu_failure_admin_email
                send_lulu_failure_admin_email(
                    preview_id=preview_id,
                    child_name=child_name,
                    error_message=lulu_msg or 'Unknown error',
                    customer_email=customer_email or '',
                    shipping_address=shipping_address,
                    story_id=story_data.get('story_id', ''),
                    product_type='quick_story'
                )
            except Exception as admin_err:
                print(f"[QS-PRINT] Failed to send admin failure email: {admin_err}")

        with open(preview_file, 'w', encoding='utf-8') as f:
            json.dump(story_data, f, ensure_ascii=False, indent=2)

        print(f"[QS-PRINT] COMPLETE for {preview_id}")
        print(f"[QS-PRINT]   Interior URL: {interior_url}")
        print(f"[QS-PRINT]   Cover URL: {cover_url}")
        print(f"[QS-PRINT]   Admin notified: {story_data.get('admin_notified')}")

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




# ── Print Order Routes ────────────────────────────────────────────────────────

@app.route('/print-order/<preview_id>')
def print_order_page(preview_id):
    lang = session.get('lang', 'es')
    translations = get_translation(lang)
    preview_file = f'story_previews/{preview_id}.json'
    child_name = 'tu hijo/a'
    email = ''
    if os.path.exists(preview_file):
        with open(preview_file, 'r', encoding='utf-8') as f:
            story_data = json.load(f)
        child_name = story_data.get('child_name', child_name)
        email = story_data.get('customer_email', '')
    from config import Config as C
    base_price = round(C.PERSONALIZED_BASE_PRICE / 100.0, 2)
    return render_template('print_order.html',
        lang=lang,
        translations=translations,
        preview_id=preview_id,
        child_name=child_name,
        email=email,
        base_price=base_price,
        paypal_client_id=Config.PAYPAL_CLIENT_ID
    )

@app.route('/print-order-success')
def print_order_success():
    lang = session.get('lang', 'es')
    translations = get_translation(lang)
    email = request.args.get('email', '')
    return render_template('print_order_success.html', lang=lang, translations=translations, email=email)

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
            'purchase_units': [{'amount': {'currency_code': 'USD', 'value': f'{amount:.2f}'}, 'description': 'Libro Impreso - Magic Memories Books'}],
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
            from services.email_service import send_admin_notification_email
            send_admin_notification_email(
                subject=f'[NUEVO PEDIDO IMPRESO] {pr.child_name} — {pr.customer_email}',
                body=f'Nuevo pedido de libro impreso.\nPedido ID: {pr.id}\nCliente: {pr.customer_email}\nNiño/a: {pr.child_name}\nImporte: ${pr.amount_paid}\nDirección: {pr.shipping_street}, {pr.shipping_city}, {pr.shipping_country}\nPreview ID: {pr.preview_id}'
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
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    pr = PrintOrderRequest.query.get_or_404(req_id)
    try:
        preview_file = f'story_previews/{pr.preview_id}.json'
        story_data = {}
        if os.path.exists(preview_file):
            with open(preview_file, 'r', encoding='utf-8') as f:
                story_data = json.load(f)
        shipping_address = {
            'name': pr.shipping_name,
            'street1': pr.shipping_street,
            'city': pr.shipping_city,
            'state_code': pr.shipping_state,
            'postcode': pr.shipping_postal,
            'country_code': pr.shipping_country,
            'phone_number': pr.shipping_phone or '',
            'email': pr.customer_email
        }
        from services.lulu_api_service import submit_print_order
        lulu_result = submit_print_order(story_data, shipping_address, pr.shipping_method)
        lulu_job_id = lulu_result.get('id') or lulu_result.get('print_job_id')
        pr.lulu_print_job_id = str(lulu_job_id) if lulu_job_id else None
        pr.status = 'sent_to_lulu'
        db.session.commit()
        try:
            from services.email_service import send_admin_notification_email
            send_admin_notification_email(
                subject=f'[PRINT ORDER #{pr.id}] Enviado a Lulu — Job {lulu_job_id}',
                body=f'Pedido #{pr.id} enviado a Lulu. Job ID: {lulu_job_id}'
            )
        except Exception:
            pass
        return jsonify({'success': True, 'lulu_job_id': lulu_job_id})
    except Exception as e:
        print(f"[ADMIN] send-to-lulu error: {e}")
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
