#!/usr/bin/env python3
"""
backfill_email_log.py — genera entradas históricas en email_log.jsonl
a partir de los flags guardados en cada story_previews JSON.

Ejecutar desde /home/magicbooks/app/:
  python3 scripts/backfill_email_log.py
"""

import json
import os
import glob

APP_DIR      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PREVIEWS_DIR = os.path.join(APP_DIR, 'data', 'story_previews')
LOG_FILE     = os.path.join(APP_DIR, 'data', 'email_log.jsonl')

_EMAIL_TYPE_META = {
    'payment_confirmation': {'category': 'delivery',  'label': 'Pago confirmado'},
    'recovery_link':        {'category': 'delivery',  'label': 'Recovery link'},
    'story_delivery':       {'category': 'delivery',  'label': 'Historia lista'},
    'ebook_ready':          {'category': 'delivery',  'label': 'eBook listo'},
    'pdf_ready':            {'category': 'delivery',  'label': 'PDF listo'},
    'print_production':     {'category': 'delivery',  'label': 'Libro en producción'},
    'tracking':             {'category': 'delivery',  'label': 'Tracking enviado'},
    'admin_purchase':       {'category': 'admin',     'label': 'Admin: nueva compra'},
    'admin_other':          {'category': 'admin',     'label': 'Admin: notificación'},
    'feedback_24h':         {'category': 'followup',  'label': 'Feedback 24h'},
    'upsell_print':         {'category': 'followup',  'label': 'Upsell impresión 48h'},
}


def make_entry(email_type, to_email, subject, ts, preview_id='',
               child_name='', lang='es'):
    meta = _EMAIL_TYPE_META.get(email_type, {'category': 'other', 'label': email_type})
    return {
        'ts':         ts,
        'preview_id': preview_id,
        'to_email':   to_email,
        'child_name': child_name,
        'lang':       lang,
        'email_type': email_type,
        'category':   meta['category'],
        'label':      meta['label'],
        'subject':    subject,
        'result':     'BACKFILL',
        'error':      '',
    }


def load_existing_log():
    """Return set of (preview_id, email_type) already in the log."""
    seen = set()
    if not os.path.exists(LOG_FILE):
        return seen
    with open(LOG_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
                if e.get('result') == 'BACKFILL':
                    seen.add((e.get('preview_id',''), e.get('email_type','')))
            except Exception:
                pass
    return seen


def backfill_story(sd, preview_id, existing):
    entries = []
    to_email   = sd.get('email') or sd.get('to_email', '')
    child_name = sd.get('child_name', '')
    lang       = sd.get('lang', 'es')

    def maybe(email_type, subject, ts):
        key = (preview_id, email_type)
        if key not in existing:
            entries.append(make_entry(email_type, to_email, subject, ts,
                                      preview_id=preview_id, child_name=child_name, lang=lang))
        else:
            print(f'  SKIP (already in log): {email_type}')

    # Pago confirmado
    if sd.get('paid') and sd.get('payment_date'):
        ts = sd.get('payment_date', '2026-01-01T00:00:00')
        subj = f"Confirmación de Pago - Cuento de {child_name}" if lang == 'es' \
               else f"Payment Confirmation - {child_name}'s Story"
        maybe('payment_confirmation', subj, ts)

    # Recovery link
    if sd.get('recovery_email_sent'):
        ts = sd.get('email_sent_date') or sd.get('payment_date', '2026-01-01T00:00:00')
        subj = f"Tu enlace de acceso — {child_name}" if lang == 'es' \
               else f"Your access link — {child_name}"
        maybe('recovery_link', subj, ts)

    # eBook / story delivery (main send_story_email_with_attachments)
    if sd.get('email_sent'):
        ts = sd.get('email_sent_date', sd.get('payment_date', '2026-01-01T00:00:00'))
        want_print = sd.get('want_print', False)
        want_pdf   = sd.get('want_pdf', False)
        if want_print:
            subj = f"📚 ¡Tu libro personalizado para {child_name} está listo para imprimir!" if lang == 'es' \
                   else f"📚 Your personalized book for {child_name} is ready to print!"
            maybe('pdf_ready', subj, ts)
        else:
            subj = f"📚 ¡Tu eBook para {child_name} está listo!" if lang == 'es' \
                   else f"📚 Your eBook for {child_name} is ready!"
            maybe('ebook_ready', subj, ts)

    # eBook email (send_ebook_email)
    if sd.get('ebook_email_sent') and not sd.get('email_sent'):
        ts = sd.get('ebook_email_sent_date') or sd.get('email_sent_date', '2026-01-01T00:00:00')
        subj = f"📖 ¡Tu eBook de {child_name} está listo!" if lang == 'es' \
               else f"📖 {child_name}'s eBook is ready!"
        maybe('ebook_ready', subj, ts)

    # Admin notificado (compra)
    if sd.get('admin_notified'):
        ts = sd.get('payment_date', '2026-01-01T00:00:00')
        subj = f"[Admin] Nueva compra — {child_name} ({preview_id})"
        key = (preview_id, 'admin_purchase')
        if key not in existing:
            entries.append(make_entry('admin_purchase', 'info@magicmemoriesbooks.com',
                                      subj, ts, preview_id=preview_id, child_name=child_name, lang=lang))
        else:
            print(f'  SKIP (already in log): admin_purchase')

    # Libro en producción (CP order)
    if sd.get('cp_order_placed') or sd.get('cp_order_id'):
        ts = sd.get('cp_order_date') or sd.get('payment_date', '2026-01-01T00:00:00')
        subj = f"¡Tu libro de {child_name} ya está en producción!" if lang == 'es' \
               else f"{child_name}'s book is now in production!"
        maybe('print_production', subj, ts)

    return entries


def main():
    if not os.path.isdir(PREVIEWS_DIR):
        print(f'ERROR: story_previews dir not found at {PREVIEWS_DIR}')
        return

    existing = load_existing_log()
    print(f'Existing BACKFILL entries in log: {len(existing)}')

    all_entries = []
    json_files  = glob.glob(os.path.join(PREVIEWS_DIR, '*.json'))
    print(f'Found {len(json_files)} story preview files\n')

    paid_count = 0
    for fpath in sorted(json_files):
        preview_id = os.path.splitext(os.path.basename(fpath))[0]
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                sd = json.load(f)
        except Exception as e:
            print(f'  SKIP {preview_id}: {e}')
            continue

        if not sd.get('paid'):
            continue

        paid_count += 1
        to_email = sd.get('email') or sd.get('to_email', '')
        print(f'Processing [{preview_id}] {sd.get("child_name","")} <{to_email}>')
        entries = backfill_story(sd, preview_id, existing)
        for ent in entries:
            print(f'  + {ent["email_type"]:30s} {ent["ts"]}')
        all_entries.extend(entries)

    print(f'\nPaid stories processed: {paid_count}')
    print(f'New entries to write:   {len(all_entries)}')

    if not all_entries:
        print('Nothing to write.')
        return

    all_entries.sort(key=lambda x: x['ts'])

    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        for ent in all_entries:
            f.write(json.dumps(ent, ensure_ascii=False) + '\n')

    print(f'\nDone. Written {len(all_entries)} entries to {LOG_FILE}')


if __name__ == '__main__':
    main()
