"""
Email Service for Magic Memories Books
Unified email templates with consistent branding
"""

import os
import smtplib
from typing import Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.application import MIMEApplication
from email import encoders

SMTP_HOST = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
SMTP_USER = os.environ.get('SENDER_EMAIL', '')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
FROM_EMAIL = os.environ.get('SENDER_EMAIL', 'info@magicmemoriesbooks.com')
FROM_NAME = os.environ.get('FROM_NAME', 'Magic Memories Books')

LOGO_URL = "https://magicmemoriesbooks.com/static/images/logo.png"
FIRMA_URL = "https://magicmemoriesbooks.com/static/images/firma_isabel.jpg"

import json as _json
import os as _os_el

EMAIL_LOG_FILE = _os_el.path.join(
    _os_el.path.dirname(_os_el.path.abspath(__file__)), '..', 'data', 'email_log.jsonl'
)

_EMAIL_TYPE_META = {
    'payment_confirmation': {'category': 'delivery',   'label': 'Pago confirmado'},
    'recovery_link':        {'category': 'delivery',   'label': 'Recovery link'},
    'story_delivery':       {'category': 'delivery',   'label': 'Historia lista'},
    'ebook_ready':          {'category': 'delivery',   'label': 'eBook listo'},
    'pdf_ready':            {'category': 'delivery',   'label': 'PDF listo'},
    'print_production':     {'category': 'delivery',   'label': 'Libro en producción'},
    'tracking':             {'category': 'delivery',   'label': 'Tracking enviado'},
    'print_failure':        {'category': 'delivery',   'label': 'Error de impresión'},
    'print_resolved':       {'category': 'delivery',   'label': 'Impresión resuelta'},
    'illustrations_ready':  {'category': 'delivery',   'label': 'Ilustraciones listas'},
    'generation_started':   {'category': 'delivery',   'label': 'Generación iniciada'},
    'generation_failed':    {'category': 'delivery',   'label': 'Generación fallida'},
    'feedback_24h':         {'category': 'followup',   'label': 'Feedback 24h'},
    'upsell_print':         {'category': 'followup',   'label': 'Upsell impresión 48h'},
    'coupon':               {'category': 'retention',  'label': 'Cupón'},
    'newsletter':           {'category': 'retention',  'label': 'Newsletter'},
    'ebook_expiry':         {'category': 'retention',  'label': 'Aviso vencimiento eBook'},
    'admin_purchase':       {'category': 'admin',      'label': 'Admin: nueva compra'},
    'admin_cp_order':       {'category': 'admin',      'label': 'Admin: pedido CP'},
    'admin_error':          {'category': 'admin',      'label': 'Admin: error'},
    'admin_other':          {'category': 'admin',      'label': 'Admin: notificación'},
}

def log_email(email_type: str, to_email: str, subject: str, result: str,
              preview_id: str = '', child_name: str = '', lang: str = 'es',
              error: str = '') -> None:
    """Append one email event to the persistent JSONL log (data/email_log.jsonl)."""
    try:
        from datetime import datetime as _dt_el
        meta = _EMAIL_TYPE_META.get(email_type, {'category': 'other', 'label': email_type})
        entry = {
            'ts':         _dt_el.now().isoformat(timespec='seconds'),
            'preview_id': preview_id or '',
            'to_email':   to_email or '',
            'child_name': child_name or '',
            'lang':       lang or 'es',
            'email_type': email_type,
            'category':   meta['category'],
            'label':      meta['label'],
            'subject':    subject or '',
            'result':     result,
            'error':      error or '',
        }
        log_dir = _os_el.path.dirname(EMAIL_LOG_FILE)
        if log_dir:
            _os_el.makedirs(log_dir, exist_ok=True)
        with open(EMAIL_LOG_FILE, 'a', encoding='utf-8') as _f:
            _f.write(_json.dumps(entry, ensure_ascii=False) + '\n')
    except Exception as _e:
        print(f'[EMAIL-LOG] Failed to write log entry: {_e}')


def _isabel_signature_html() -> str:
    """Returns Isabel Ojeda's signature block for user-facing emails."""
    return f"""
    <div style="margin-top:28px;padding-top:20px;border-top:1px solid #ede9f5;">
        <a href="https://magicmemoriesbooks.com/" target="_blank" style="display:block;">
            <img src="{FIRMA_URL}" alt="Isabel Ojeda – Fundadora de Magic Memories Books"
                 style="max-width:420px;width:100%;height:auto;display:block;border:0;" />
        </a>
    </div>"""


def _email_wrapper(title: str, content_html: str, to_email: str = '') -> str:
    footer_email = f"<p style='margin:4px 0;'>Este email fue enviado a {to_email}</p>" if to_email else ""
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;margin:0;padding:0;background-color:#f8f5ff;">
<div style="max-width:600px;margin:0 auto;padding:20px;">
    <div style="background-color:#9333ea;background-image:linear-gradient(135deg,#9333ea,#ec4899);padding:30px;text-align:center;border-radius:20px 20px 0 0;">
        <img src="{LOGO_URL}" alt="Magic Memories Books" style="max-width:80px;height:auto;margin-bottom:12px;border-radius:12px;" />
        <h1 style="color:#ffffff;margin:0;font-size:24px;font-weight:bold;">{title}</h1>
    </div>
    <div style="background:#ffffff;padding:30px;border-radius:0 0 20px 20px;box-shadow:0 4px 6px rgba(0,0,0,0.1);">
        {content_html}
        {_isabel_signature_html()}
    </div>
    <div style="text-align:center;padding:20px;color:#6b7280;font-size:12px;">
        <p style="margin:4px 0;">Magic Memories Books - Cuentos personalizados con IA</p>
        {footer_email}
    </div>
</div>
</body>
</html>"""


def _admin_wrapper(title: str, content_html: str) -> str:
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;margin:0;padding:0;background-color:#fef2f2;">
<div style="max-width:600px;margin:0 auto;padding:20px;">
    <div style="background-color:#dc2626;background-image:linear-gradient(135deg,#dc2626,#b91c1c);padding:25px;text-align:center;border-radius:16px 16px 0 0;">
        <img src="{LOGO_URL}" alt="MMB Admin" style="max-width:50px;height:auto;margin-bottom:8px;border-radius:8px;" />
        <h1 style="color:#ffffff;margin:0;font-size:20px;font-weight:bold;">{title}</h1>
    </div>
    <div style="background:#ffffff;padding:25px;border-radius:0 0 16px 16px;box-shadow:0 4px 6px rgba(0,0,0,0.1);">
        {content_html}
    </div>
    <div style="text-align:center;padding:15px;color:#6b7280;font-size:11px;">
        <p style="margin:0;">Magic Memories Books - Admin Notification</p>
    </div>
</div>
</body>
</html>"""


def _info_box(html_inner: str) -> str:
    return f'<div style="background:#f3e8ff;padding:20px;border-radius:12px;margin:20px 0;border-left:4px solid #9333ea;">{html_inner}</div>'


def _alert_box(html_inner: str) -> str:
    return f'<div style="background:#fef3c7;padding:15px;border-radius:10px;margin:20px 0;border-left:4px solid #f59e0b;">{html_inner}</div>'


def _success_box(html_inner: str) -> str:
    return f'<div style="background:#f0fdf4;padding:20px;border-radius:12px;margin:20px 0;border-left:4px solid #22c55e;">{html_inner}</div>'


def _cta_button(text: str, url: str) -> str:
    return f'<div style="text-align:center;margin:25px 0;"><a href="{url}" style="display:inline-block;background-color:#9333ea;background-image:linear-gradient(135deg,#9333ea,#ec4899);color:#ffffff;padding:14px 30px;border-radius:25px;text-decoration:none;font-weight:bold;font-size:16px;">{text}</a></div>'


def _newsletter_invite_html(lang='es'):
    site_url = 'magicmemoriesbooks.com'
    if lang == 'es':
        return f"""
        <div style="background:#f3e8ff;padding:20px;border-radius:12px;margin:20px 0;text-align:center;border:1px solid #e9d5ff;">
            <p style="font-size:15px;color:#7c3aed;font-weight:bold;margin:0 0 8px;">¿Te gustó la experiencia?</p>
            <p style="font-size:13px;color:#374151;margin:0 0 12px;">Únete a nuestra comunidad para enterarte de nuevos cuentos y ofertas exclusivas.</p>
            <a href="https://{site_url}/suscribirse" style="display:inline-block;background-color:#9333ea;background-image:linear-gradient(135deg,#9333ea,#ec4899);color:#ffffff;padding:10px 24px;border-radius:20px;text-decoration:none;font-weight:bold;font-size:13px;">Suscribirme</a>
        </div>"""
    else:
        return f"""
        <div style="background:#f3e8ff;padding:20px;border-radius:12px;margin:20px 0;text-align:center;border:1px solid #e9d5ff;">
            <p style="font-size:15px;color:#7c3aed;font-weight:bold;margin:0 0 8px;">Did you enjoy the experience?</p>
            <p style="font-size:13px;color:#374151;margin:0 0 12px;">Join our community to hear about new stories and exclusive offers.</p>
            <a href="https://{site_url}/subscribe" style="display:inline-block;background-color:#9333ea;background-image:linear-gradient(135deg,#9333ea,#ec4899);color:#ffffff;padding:10px 24px;border-radius:20px;text-decoration:none;font-weight:bold;font-size:13px;">Subscribe</a>
        </div>"""


def attach_file(msg, file_path: str, filename: Optional[str] = None):
    if not os.path.exists(file_path):
        print(f"[EMAIL] File not found: {file_path}")
        return False
    
    if filename is None:
        filename = os.path.basename(file_path)
    
    try:
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        if filename.endswith('.pdf'):
            part = MIMEApplication(file_data, _subtype='pdf')
        elif filename.endswith('.epub'):
            part = MIMEApplication(file_data, _subtype='epub+zip')
        else:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(file_data)
            encoders.encode_base64(part)
        
        part.add_header('Content-Disposition', 'attachment', filename=filename)
        msg.attach(part)
        
        file_size_mb = len(file_data) / (1024 * 1024)
        print(f"[EMAIL] Attached: {filename} ({file_size_mb:.2f} MB)")
        return True
        
    except Exception as e:
        print(f"[EMAIL] Error attaching file {filename}: {e}")
        return False


def send_story_email_with_attachments(
    to_email: str,
    story_data: dict,
    pdf_digital_path: Optional[str] = None,
    pdf_printable_path: Optional[str] = None,
    epub_path: Optional[str] = None,
    instructions_path: Optional[str] = None,
    age_group: Optional[str] = None,
    preview_id: Optional[str] = None,
    visor_url: Optional[str] = None,
    is_pdf_purchase: bool = False,
    give_gift_ebook: bool = False,
) -> dict:
    child_name = story_data.get('child_name', 'tu pequeño')
    story_name = story_data.get('story_name', 'tu cuento')
    lang = story_data.get('lang', 'es')
    
    if age_group is None:
        age_group = story_data.get('age_group', 'baby')
    
    is_personalized_book = age_group in ['personalized', 'haz_tu_historia']
    safe_name = child_name.replace(' ', '_').replace("'", "")
    
    if lang == 'es':
        if is_personalized_book:
            subject = f"📚 ¡Tu libro ilustrado para {child_name} está listo!"
        else:
            subject = f"🎉 ¡Tu cuento para {child_name} está listo!"
    else:
        if is_personalized_book:
            subject = f"📚 Your illustrated book for {child_name} is ready!"
        else:
            subject = f"🎉 Your story for {child_name} is ready!"
    
    attachments_list = ""
    if pdf_digital_path:
        label = "Tu libro digital de 26 páginas" if lang == 'es' else "Your 26-page digital book"
        attachments_list += f'<li style="padding:4px 0;color:#374151;">📄 <strong>{safe_name}_digital.pdf</strong> - {label}</li>'
    if pdf_printable_path:
        label = "Para llevar a imprenta" if lang == 'es' else "For printing"
        attachments_list += f'<li style="padding:4px 0;color:#374151;">🖨️ <strong>{safe_name}_imprimible.pdf</strong> - {label}</li>'
    if instructions_path:
        label = "Instrucciones de impresión" if lang == 'es' else "Printing instructions"
        attachments_list += f'<li style="padding:4px 0;color:#374151;">📋 <strong>{label}</strong></li>'
    
    attach_title = "📎 Archivos adjuntos:" if lang == 'es' else "📎 Attached files:"
    attachments_html = ""
    if attachments_list:
        attachments_html = _info_box(f'''
            <h3 style="margin-top:0;color:#7c3aed;">{attach_title}</h3>
            <ul style="text-align:left;margin:0.5em auto;max-width:350px;list-style:none;padding-left:0;">{attachments_list}</ul>
        ''')
    
    base_url = os.environ.get('REPLIT_DEV_DOMAIN', '')
    if base_url:
        base_url = f"https://{base_url}"
    else:
        base_url = os.environ.get('PUBLIC_URL', 'https://magicmemoriesbooks.com')
    
    read_online_html = ""
    read_online_text = ""
    final_visor_url = visor_url or story_data.get('visor_url')
    _show_as_gift = is_pdf_purchase or give_gift_ebook
    if _show_as_gift:
        btn_label = "🎁 Ver tu eBook de regalo (6 meses)" if lang == 'es' else "🎁 View your eBook Gift (6 months)"
        device_hint = ("Acceso por 6 meses incluido con tu compra" if lang == 'es'
                       else "6-month access included with your purchase")
    else:
        btn_label = "📖 Leer Cuento Online" if lang == 'es' else "📖 Read Story Online"
        device_hint = ("Ábrelo en cualquier dispositivo — celular, tablet o computadora" if lang == 'es'
                       else "Open on any device — phone, tablet or computer")
    if final_visor_url:
        read_online_html = _cta_button(btn_label, final_visor_url)
        read_online_html += f'<p style="color:#6b7280;font-size:12px;text-align:center;margin-top:-15px;">{device_hint}</p>'
        read_online_text = f"\n{btn_label}: {final_visor_url}\n"
    elif preview_id and not is_pdf_purchase and not pdf_printable_path:
        ebook_url = f"{base_url}/ebook-preview/{preview_id}"
        read_online_html = _cta_button(btn_label, ebook_url)
        read_online_html += f'<p style="color:#6b7280;font-size:12px;text-align:center;margin-top:-15px;">{device_hint}</p>'
        read_online_text = f"\n{btn_label}: {ebook_url}\n"

    if is_personalized_book and (is_pdf_purchase or pdf_printable_path):
        if lang == 'es':
            extra_sections_html = f"""
                {_success_box('''
                    <h4 style="margin-top:0;color:#166534;">🖨️ Tu PDF imprimible está adjunto</h4>
                    <p style="color:#374151;font-size:13px;margin:0;">
                        Descarga el PDF adjunto y llévalo a cualquier imprenta o copy shop.<br>
                        Imprime en A4, color, doble cara (flip on long edge).<br>
                        Para mejor resultado: papel satinado 120–170 g/m².
                    </p>
                ''')}
            """
        else:
            extra_sections_html = f"""
                {_success_box('''
                    <h4 style="margin-top:0;color:#166534;">🖨️ Your printable PDF is attached</h4>
                    <p style="color:#374151;font-size:13px;margin:0;">
                        Download the attached PDF and take it to any print shop.<br>
                        Print on A4, colour, double-sided (flip on long edge).<br>
                        Best results: coated paper 120–170 gsm.
                    </p>
                ''')}
            """
        extra_sections_text = ""
    elif is_personalized_book:
        tracking_link = ""
        tracking_link_text = ""
        if preview_id:
            tracking_url = f"{base_url}/track-order/{preview_id}"
            tracking_link = _cta_button(
                "📍 Ver estado de mi pedido" if lang == 'es' else "📍 Track my order",
                tracking_url
            )
            tracking_link_text = f"\n\n📍 {'Ver estado de tu pedido' if lang == 'es' else 'Track your order'}: {tracking_url}"
        
        if lang == 'es':
            extra_sections_html = f"""
                {read_online_html}
                {_success_box(f'''
                    <h4 style="margin-top:0;color:#166534;">📦 Tu libro impreso está en camino</h4>
                    <p style="color:#374151;font-size:13px;margin:0;">
                        Hemos enviado tu libro a producción con Cloudprinter.<br>
                        Recibirás actualizaciones de seguimiento por email.<br><br>
                        <strong>Tiempo estimado:</strong> 14-21 días hábiles<br>
                        <strong>Formato:</strong> Tapa dura, 26 páginas, impresión premium a color
                    </p>
                    {tracking_link}
                ''')}
            """
        else:
            extra_sections_html = f"""
                {read_online_html}
                {_success_box(f'''
                    <h4 style="margin-top:0;color:#166534;">📦 Your printed book is on its way</h4>
                    <p style="color:#374151;font-size:13px;margin:0;">
                        We've sent your book to production with Cloudprinter.<br>
                        You'll receive tracking updates by email.<br><br>
                        <strong>Estimated delivery:</strong> 14-21 business days<br>
                        <strong>Format:</strong> Hardcover, 26 pages, premium color print
                    </p>
                    {tracking_link}
                ''')}
            """
        extra_sections_text = f"""{read_online_text}{tracking_link_text}"""
    else:
        if lang == 'es':
            extra_sections_html = f"""
                {read_online_html}
                {_success_box('''
                    <h4 style="margin-top:0;color:#166534;">📖 Tu cuento digital está listo</h4>
                    <p style="color:#374151;font-size:13px;margin:0;">
                        Puedes leerlo online en cualquier momento con el botón de arriba.
                    </p>
                ''')}
            """
        else:
            extra_sections_html = f"""
                {read_online_html}
                {_success_box('''
                    <h4 style="margin-top:0;color:#166534;">📖 Your digital story is ready</h4>
                    <p style="color:#374151;font-size:13px;margin:0;">
                        You can read it online anytime using the button above.
                    </p>
                ''')}
            """
        extra_sections_text = f"""{read_online_text}"""
    
    if lang == 'es':
        greeting = "¡Hola!"
        book_type = "Tu libro ilustrado personalizado" if is_personalized_book else "Tu cuento personalizado"
        ready_msg = f'{book_type} <strong>"{story_name}"</strong> para <strong>{child_name}</strong> está listo.'
        save_warning = '<p style="margin:0;color:#92400e;font-size:14px;"><strong>⚠️ Importante:</strong> Descarga y guarda los archivos adjuntos en tu dispositivo.</p>' if attachments_list else ''
        thanks = "¡Gracias por crear recuerdos mágicos! 💜"
    else:
        greeting = "Hello!"
        book_type = "Your personalized illustrated book" if is_personalized_book else "Your personalized story"
        ready_msg = f'{book_type} <strong>"{story_name}"</strong> for <strong>{child_name}</strong> is ready.'
        save_warning = '<p style="margin:0;color:#92400e;font-size:14px;"><strong>⚠️ Important:</strong> Download and save the attached files to your device.</p>' if attachments_list else ''
        thanks = "Thank you for creating magical memories! 💜"
    
    warning_html = _alert_box(save_warning) if save_warning else ''
    
    content_inner = f"""
        <h2 style="color:#7c3aed;text-align:center;margin-top:0;">{greeting}</h2>
        <p style="font-size:16px;color:#374151;text-align:center;">{ready_msg}</p>
        {attachments_html}
        {warning_html}
        {extra_sections_html}
        {_newsletter_invite_html(lang)}
        <p style="color:#7c3aed;font-weight:bold;text-align:center;">{thanks}</p>
    """
    
    html_body = _email_wrapper("✨ Magic Memories Books ✨", content_inner, to_email)
    
    text_body = f"""{greeting}

{book_type} "{story_name}" {"para" if lang == "es" else "for"} {child_name} {"está listo" if lang == "es" else "is ready"}.
{extra_sections_text}

{thanks}
Magic Memories Books
    """
    
    if not SMTP_USER or not SMTP_PASSWORD:
        print(f"[EMAIL SERVICE] SMTP not configured. Would send email to: {to_email}")
        print(f"[EMAIL SERVICE] Subject: {subject}")
        if pdf_digital_path:
            print(f"  - Digital PDF: {pdf_digital_path}")
        if pdf_printable_path:
            print(f"  - Printable PDF: {pdf_printable_path}")
        
        with open('email_log.txt', 'a') as f:
            f.write(f"\n{'='*50}\n")
            f.write(f"TO: {to_email}\nSUBJECT: {subject}\n")
            f.write(f"{'='*50}\n")
        
        return {'success': True, 'message': 'Email logged (SMTP not configured)', 'simulated': True}
    
    try:
        has_attachments = (pdf_digital_path and os.path.exists(pdf_digital_path)) or \
                          (pdf_printable_path and os.path.exists(pdf_printable_path)) or \
                          (instructions_path and os.path.exists(instructions_path))
        
        if has_attachments:
            msg = MIMEMultipart('mixed')
            msg_alternative = MIMEMultipart('alternative')
        else:
            msg = MIMEMultipart('alternative')
            msg_alternative = msg
        
        msg['Subject'] = subject
        msg['From'] = f"{FROM_NAME} <{FROM_EMAIL}>"
        msg['To'] = to_email
        
        msg_alternative.attach(MIMEText(text_body, 'plain', 'utf-8'))
        msg_alternative.attach(MIMEText(html_body, 'html', 'utf-8'))
        
        if has_attachments:
            msg.attach(msg_alternative)
        
        attached_count = 0
        
        if pdf_digital_path and os.path.exists(pdf_digital_path):
            if attach_file(msg, pdf_digital_path, f"{safe_name}_digital.pdf"):
                attached_count += 1
        
        if pdf_printable_path and os.path.exists(pdf_printable_path):
            _pr_fname = os.path.basename(pdf_printable_path)
            _pr_fmt = "_LETTER" if "_LETTER" in _pr_fname else "_A4" if "_A4" in _pr_fname else ""
            if attach_file(msg, pdf_printable_path, f"{safe_name}_imprimible{_pr_fmt}.pdf"):
                attached_count += 1
        
        if instructions_path and os.path.exists(instructions_path):
            if attach_file(msg, instructions_path, "instrucciones_impresion.pdf"):
                attached_count += 1
        
        if attached_count == 0 and not final_visor_url:
            return {'success': False, 'message': 'No files could be attached and no visor URL'}
        
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        
        print(f"[EMAIL SERVICE] Email sent successfully to: {to_email} with {attached_count} attachments")
        _age = story_data.get('age_group', '')
        _etype = 'ebook_ready' if not pdf_printable_path else 'pdf_ready'
        log_email(_etype, to_email, subject,
                  'SENT', preview_id=preview_id or '', child_name=story_data.get('child_name',''), lang=story_data.get('lang','es'))
        return {'success': True, 'message': f'Email sent with {attached_count} attachments'}
        
    except Exception as e:
        print(f"[EMAIL SERVICE] Error sending email: {str(e)}")
        _etype2 = 'ebook_ready' if not pdf_printable_path else 'pdf_ready'
        log_email(_etype2, to_email, subject,
                  'ERROR', preview_id=preview_id or '', child_name=story_data.get('child_name',''), lang=story_data.get('lang','es'), error=str(e))
        return {'success': False, 'message': str(e)}


def test_email_connection() -> dict:
    if not SMTP_USER or not SMTP_PASSWORD:
        return {'success': False, 'message': 'SMTP credentials not configured'}
    
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
        return {'success': True, 'message': 'SMTP connection successful'}
    except Exception as e:
        return {'success': False, 'message': str(e)}






def send_admin_purchase_notification(
    preview_id: str,
    product_type: str,
    customer_email: str,
    story_data: dict,
    line_items: list = None,
    shipping_cost: float = 0.0,
    total_usd: float = 0.0
) -> dict:
    from datetime import datetime
    
    admin_email = "pay@magicmemoriesbooks.com"
    
    child_name = story_data.get('child_name', 'N/A')
    story_id = story_data.get('story_id', 'N/A')
    story_name = story_data.get('story_name', story_data.get('title', story_id))
    language = story_data.get('language', story_data.get('lang', 'es'))
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    type_labels = {
        'ebook': '📱 Cuento Express Digital',
        'qs_digital': '📱 Cuento Express Digital',
        'qs_print': '📦 Cuento Express Impreso',
        'personalized': '📖 Libro Personalizado',
        'personalized_digital': '📱 Libro Personalizado Digital',
    }
    type_label = type_labels.get(product_type, f'🛒 {product_type}')
    
    subject = f"🛒 Nueva compra - {type_label} - {child_name}"
    
    traits_html = ""
    traits = story_data.get('traits', {})
    if traits:
        hair = f"{traits.get('hair_color', '')} {traits.get('hair_type', '')}".strip()
        eyes = traits.get('eye_color', '')
        skin = traits.get('skin_tone', '')
        age = traits.get('child_age', '')
        traits_html = f"""
        <tr><td style="padding:10px 12px;color:#6b7280;font-size:13px;">Cabello</td><td style="padding:10px 12px;color:#1f2937;font-weight:600;">{hair}</td></tr>
        <tr style="background:#fef2f2;"><td style="padding:10px 12px;color:#6b7280;font-size:13px;">Ojos</td><td style="padding:10px 12px;color:#1f2937;font-weight:600;">{eyes}</td></tr>
        <tr><td style="padding:10px 12px;color:#6b7280;font-size:13px;">Piel</td><td style="padding:10px 12px;color:#1f2937;font-weight:600;">{skin}</td></tr>
        <tr style="background:#fef2f2;"><td style="padding:10px 12px;color:#6b7280;font-size:13px;">Edad</td><td style="padding:10px 12px;color:#1f2937;font-weight:600;">{age}</td></tr>
        """
    
    dedication = story_data.get('dedication', '')
    ded_html = f'<tr><td style="padding:10px 12px;color:#6b7280;font-size:13px;">Dedicatoria</td><td style="padding:10px 12px;color:#1f2937;font-style:italic;">{dedication[:100]}</td></tr>' if dedication else ''
    
    base_url = os.environ.get('SITE_DOMAIN', 'magicmemoriesbooks.com')
    admin_url = f"https://{base_url}/admin/preview/{preview_id}"

    purchase_summary_html = ""
    if line_items or total_usd > 0:
        rows = ""
        for i, item in enumerate(line_items or []):
            bg = ' style="background:#f9fafb;"' if i % 2 == 0 else ''
            rows += f'<tr{bg}><td style="padding:8px 12px;color:#374151;font-size:13px;">{item["label"]}</td><td style="padding:8px 12px;color:#111827;font-weight:600;text-align:right;">${item["price"]:.2f}</td></tr>'
        if shipping_cost > 0:
            bg = ' style="background:#f9fafb;"' if len(line_items or []) % 2 == 0 else ''
            rows += f'<tr{bg}><td style="padding:8px 12px;color:#374151;font-size:13px;">Envío</td><td style="padding:8px 12px;color:#111827;font-weight:600;text-align:right;">${shipping_cost:.2f}</td></tr>'
        if total_usd > 0:
            rows += f'<tr style="background:#fef3c7;border-top:2px solid #f59e0b;"><td style="padding:10px 12px;color:#92400e;font-size:14px;font-weight:700;">TOTAL</td><td style="padding:10px 12px;color:#92400e;font-size:15px;font-weight:700;text-align:right;">${total_usd:.2f} USD</td></tr>'
        purchase_summary_html = f"""
        <div style="background:#fffbeb;border:1px solid #fcd34d;border-radius:8px;padding:14px;margin:16px 0;">
            <p style="margin:0 0 10px;color:#92400e;font-weight:700;font-size:13px;">🧾 Resumen de Compra</p>
            <table style="width:100%;border-collapse:collapse;font-size:13px;">{rows}</table>
        </div>"""

    content = f"""
        <p style="color:#6b7280;font-size:13px;text-align:center;margin-top:0;">Nueva compra recibida</p>
        {purchase_summary_html}
        <table style="width:100%;border-collapse:collapse;font-size:14px;margin:15px 0;">
            <tr style="background:#fef2f2;"><td style="padding:10px 12px;color:#6b7280;font-size:13px;width:130px;">Cliente</td><td style="padding:10px 12px;color:#1f2937;font-weight:600;">{customer_email}</td></tr>
            <tr><td style="padding:10px 12px;color:#6b7280;font-size:13px;">Nombre</td><td style="padding:10px 12px;color:#1f2937;font-weight:600;">{child_name}</td></tr>
            <tr style="background:#fef2f2;"><td style="padding:10px 12px;color:#6b7280;font-size:13px;">Cuento</td><td style="padding:10px 12px;color:#1f2937;font-weight:600;">{story_name}</td></tr>
            <tr><td style="padding:10px 12px;color:#6b7280;font-size:13px;">Story ID</td><td style="padding:10px 12px;color:#1f2937;font-weight:600;">{story_id}</td></tr>
            <tr style="background:#fef2f2;"><td style="padding:10px 12px;color:#6b7280;font-size:13px;">Tipo</td><td style="padding:10px 12px;color:#1f2937;font-weight:600;">{type_label}</td></tr>
            <tr><td style="padding:10px 12px;color:#6b7280;font-size:13px;">Idioma</td><td style="padding:10px 12px;color:#1f2937;font-weight:600;">{language}</td></tr>
            {traits_html}
            {ded_html}
            <tr style="background:#fef2f2;"><td style="padding:10px 12px;color:#6b7280;font-size:13px;">Preview ID</td><td style="padding:10px 12px;color:#1f2937;font-size:11px;">{preview_id}</td></tr>
            <tr><td style="padding:10px 12px;color:#6b7280;font-size:13px;">Fecha</td><td style="padding:10px 12px;color:#1f2937;">{timestamp}</td></tr>
        </table>
        <div style="text-align:center;margin-top:16px;">
            <a href="{admin_url}" style="display:inline-block;background-color:#dc2626;background-image:linear-gradient(135deg,#dc2626,#b91c1c);color:#ffffff;text-decoration:none;padding:10px 24px;border-radius:8px;font-weight:600;font-size:13px;">Ver en Admin</a>
        </div>
    """
    
    html_body = _admin_wrapper(f"{type_label}", content)
    
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f'{FROM_NAME} <{FROM_EMAIL}>'
        msg['To'] = admin_email
        msg.attach(MIMEText(html_body, 'html'))
        
        if SMTP_USER and SMTP_PASSWORD:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.send_message(msg)
            print(f"[ADMIN NOTIFY] Purchase notification sent for {preview_id} ({product_type})")
            return {'success': True, 'message': 'Admin notification sent'}
        else:
            print(f"[ADMIN NOTIFY] SMTP not configured, logging purchase: {preview_id} ({product_type}) - {customer_email}")
            return {'success': False, 'message': 'SMTP not configured'}
    except Exception as e:
        print(f"[ADMIN NOTIFY] Error sending notification: {e}")
        return {'success': False, 'message': str(e)}


def _build_receipt_table(line_items: list, shipping_cost: float, total_usd: float, lang: str = 'es'):
    rows = ""
    for item in line_items:
        label = item.get('label', '')
        price = item.get('price', 0)
        rows += f'<tr><td style="padding:8px 12px;color:#374151;font-size:14px;">{label}</td><td style="padding:8px 12px;text-align:right;color:#374151;font-size:14px;">${price:.2f}</td></tr>'

    if shipping_cost and shipping_cost > 0:
        ship_label = 'Envío' if lang == 'es' else 'Shipping'
        rows += f'<tr><td style="padding:8px 12px;color:#374151;font-size:14px;">{ship_label}</td><td style="padding:8px 12px;text-align:right;color:#374151;font-size:14px;">${shipping_cost:.2f}</td></tr>'

    total_label = 'Total' if lang == 'es' else 'Total'
    rows += f'<tr style="border-top:2px solid #9333ea;"><td style="padding:10px 12px;color:#1f2937;font-size:16px;font-weight:bold;">{total_label}</td><td style="padding:10px 12px;text-align:right;color:#1f2937;font-size:16px;font-weight:bold;">${total_usd:.2f} USD</td></tr>'

    title = 'Resumen de Compra' if lang == 'es' else 'Purchase Summary'
    return f'''
    <div style="margin:20px 0;">
        <h3 style="color:#7c3aed;margin-bottom:10px;font-size:16px;">🧾 {title}</h3>
        <table style="width:100%;border-collapse:collapse;background:#faf5ff;border-radius:8px;overflow:hidden;">
            {rows}
        </table>
    </div>'''


def send_payment_confirmation_email(to_email: str, child_name: str, recovery_url: str, lang: str = 'es',
                                    line_items: list = None, shipping_cost: float = 0, total_usd: float = 0):
    receipt_html = _build_receipt_table(line_items or [], shipping_cost, total_usd, lang) if line_items else ''

    if lang == 'es':
        subject = f"Confirmación de Pago - Cuento de {child_name}"
        content = f"""
                <h2 style="color:#7c3aed;text-align:center;margin-top:0;">¡Gracias por tu compra!</h2>
                <p style="font-size:16px;color:#374151;text-align:center;">Tu pago ha sido procesado correctamente.</p>
                {receipt_html}
                {_success_box(f'''
                    <h3 style="margin-top:0;color:#166534;">Tu cuento personalizado para {child_name} está siendo creado</h3>
                    <p style="color:#374151;font-size:14px;">Estamos generando las ilustraciones únicas de tu historia. Recibirás un email cuando esté listo.</p>
                ''')}
                <p style="color:#374151;font-size:14px;text-align:center;">Si tienes algún problema, escríbenos a:</p>
                <p style="color:#374151;text-align:center;"><strong>pay@magicmemoriesbooks.com</strong></p>"""
        html_content = _email_wrapper("✨ Magic Memories Books ✨", content, to_email)
    else:
        subject = f"Payment Confirmation - {child_name}'s Story"
        content = f"""
                <h2 style="color:#7c3aed;text-align:center;margin-top:0;">Thank you for your purchase!</h2>
                <p style="font-size:16px;color:#374151;text-align:center;">Your payment has been processed successfully.</p>
                {receipt_html}
                {_success_box(f'''
                    <h3 style="margin-top:0;color:#166534;">Your personalized story for {child_name} is being created</h3>
                    <p style="color:#374151;font-size:14px;">We're generating the unique illustrations for your story. You'll receive an email when it's ready.</p>
                ''')}
                <p style="color:#374151;font-size:14px;text-align:center;">If you have any issues, email us at:</p>
                <p style="color:#374151;text-align:center;"><strong>pay@magicmemoriesbooks.com</strong></p>"""
        html_content = _email_wrapper("✨ Magic Memories Books ✨", content, to_email)
    
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = f"{FROM_NAME} <{FROM_EMAIL}>"
    msg['To'] = to_email
    
    msg.attach(MIMEText(html_content, 'html'))
    
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(FROM_EMAIL, to_email, msg.as_string())
        print(f"[EMAIL] Payment confirmation sent to {to_email}")
        log_email('payment_confirmation', to_email, subject, 'SENT', child_name=child_name, lang=lang)
        return True
    except Exception as e:
        print(f"[EMAIL] Failed to send payment confirmation: {e}")
        log_email('payment_confirmation', to_email, subject, 'ERROR', child_name=child_name, lang=lang, error=str(e))
        return False


def send_recovery_link_email(to_email: str, child_name: str, recovery_url: str, lang: str = 'es',
                              want_ebook: bool = False, want_pdf: bool = False, want_print: bool = False):
    """Send recovery link email. Content adapts to product type:
    - only_ebook (want_ebook=True, want_pdf=False, want_print=False): no print/approve language
    - pdf (want_pdf=True, no print): mention review and download
    - print or default: full review-and-approve-before-printing flow
    """
    only_ebook = bool(want_ebook) and not bool(want_pdf) and not bool(want_print)
    has_pdf = bool(want_pdf) and not bool(want_print)

    if lang == 'es':
        if only_ebook:
            subject = f"Accede a tu cuento de {child_name}"
            heading = "¡Tu cuento está casi listo!"
            cta_label = "📖 Abrir mi cuento"
            instructions = _info_box(f'''
                    <h3 style="margin-top:0;color:#7c3aed;">📋 ¿Qué pasa ahora?</h3>
                    <ol style="color:#374151;font-size:14px;padding-left:20px;margin:0;">
                        <li style="margin-bottom:8px;"><strong>Espera unos minutos</strong> — estamos generando las ilustraciones de <strong>{child_name}</strong>. 🎨</li>
                        <li style="margin-bottom:0;"><strong>Usa el enlace de abajo</strong> para abrir tu cuento cuando esté listo.</li>
                    </ol>
                ''')
            cta_label_link = "Si el botón no funciona, copia este enlace en tu navegador:"
            wrapper_title = "📖 Accede a tu cuento"
        elif has_pdf:
            subject = f"Tu cuento de {child_name} estará listo en unos minutos"
            heading = "¡Tu cuento está casi listo!"
            cta_label = "🔍 Revisar y descargar"
            instructions = _info_box(f'''
                    <h3 style="margin-top:0;color:#7c3aed;">📋 ¿Qué debes hacer cuando esté listo?</h3>
                    <ol style="color:#374151;font-size:14px;padding-left:20px;margin:0;">
                        <li style="margin-bottom:8px;"><strong>Revisa todas las páginas</strong> — asegúrate de que las ilustraciones y el texto son correctos.</li>
                        <li style="margin-bottom:8px;"><strong>Regenera las imágenes</strong> que no te gusten — puedes hacerlo gratis antes de descargar.</li>
                        <li style="margin-bottom:0;"><strong>Descarga tu PDF</strong> — listo para imprimir en casa o en cualquier copistería.</li>
                    </ol>
                ''')
            cta_label_link = "Si el botón no funciona, copia este enlace en tu navegador:"
            wrapper_title = "🔍 Revisa y Descarga tu Cuento"
        else:
            subject = f"¡Revisa y aprueba el cuento de {child_name} antes de imprimir!"
            heading = "¡Tu cuento está casi listo!"
            cta_label = "🔍 Revisar mi cuento"
            instructions = _info_box(f'''
                    <h3 style="margin-top:0;color:#7c3aed;">📋 ¿Qué debes hacer cuando esté listo?</h3>
                    <ol style="color:#374151;font-size:14px;padding-left:20px;margin:0;">
                        <li style="margin-bottom:8px;"><strong>Revisa todas las páginas</strong> — asegúrate de que las ilustraciones y el texto son correctos.</li>
                        <li style="margin-bottom:8px;"><strong>Regenera las imágenes</strong> que no te gusten — puedes hacerlo gratis antes de aprobar.</li>
                        <li style="margin-bottom:0;"><strong>Aprueba y envía a imprenta</strong> — solo entonces se enviará a imprimir y enviar.</li>
                    </ol>
                ''')
            cta_label_link = "Si el botón no funciona, copia este enlace en tu navegador:"
            wrapper_title = "🔍 Revisa Tu Cuento Antes de Imprimir"

        content = f"""
                <h2 style="color:#7c3aed;margin-top:0;">{heading}</h2>
                <p style="font-size:16px;color:#374151;">
                    Estamos creando el libro personalizado de <strong>{child_name}</strong>. En unos minutos podrás revisarlo. 🎨
                </p>
                {instructions}
                {_success_box(f'''
                    <p style="margin-bottom:15px;color:#374151;font-weight:600;">Usa este enlace para acceder a tu cuento cuando esté listo:</p>
                    {_cta_button(cta_label, recovery_url)}
                    <p style="margin-top:10px;font-size:12px;color:#6b7280;text-align:center;">{cta_label_link}</p>
                    <p style="font-size:11px;color:#374151;word-break:break-all;text-align:center;">{recovery_url}</p>
                ''')}
                {_alert_box(f'''
                    <p style="margin:0;color:#92400e;font-size:14px;">
                        <strong>⏳ La generación tarda entre 5 y 10 minutos.</strong> Guarda este email para volver cuando esté listo.
                    </p>
                ''')}
                <p style="color:#374151;font-size:14px;">¿Tienes alguna duda? Escríbenos a:</p>
                <p style="color:#374151;"><strong>pay@magicmemoriesbooks.com</strong></p>"""
        html_content = _email_wrapper(wrapper_title, content, to_email)
    else:
        if only_ebook:
            subject = f"Access {child_name}'s story"
            heading = "Your story is almost ready!"
            cta_label = "📖 Open my story"
            instructions = _info_box(f'''
                    <h3 style="margin-top:0;color:#7c3aed;">📋 What happens next?</h3>
                    <ol style="color:#374151;font-size:14px;padding-left:20px;margin:0;">
                        <li style="margin-bottom:8px;"><strong>Wait a few minutes</strong> — we are generating the illustrations for <strong>{child_name}</strong>. 🎨</li>
                        <li style="margin-bottom:0;"><strong>Use the link below</strong> to open your story when it is ready.</li>
                    </ol>
                ''')
            cta_label_link = "If the button doesn't work, copy this link into your browser:"
            wrapper_title = "📖 Access your story"
        elif has_pdf:
            subject = f"{child_name}'s story will be ready in a few minutes"
            heading = "Your story is almost ready!"
            cta_label = "🔍 Review and download"
            instructions = _info_box(f'''
                    <h3 style="margin-top:0;color:#7c3aed;">📋 What to do when it's ready?</h3>
                    <ol style="color:#374151;font-size:14px;padding-left:20px;margin:0;">
                        <li style="margin-bottom:8px;"><strong>Review all pages</strong> — make sure the illustrations and text look correct.</li>
                        <li style="margin-bottom:8px;"><strong>Regenerate any images</strong> you don't like — you can do this for free before downloading.</li>
                        <li style="margin-bottom:0;"><strong>Download your PDF</strong> — ready to print at home or at any copy shop.</li>
                    </ol>
                ''')
            cta_label_link = "If the button doesn't work, copy this link into your browser:"
            wrapper_title = "🔍 Review and Download Your Story"
        else:
            subject = f"Review and approve {child_name}'s story before printing!"
            heading = "Your story is almost ready!"
            cta_label = "🔍 Review my story"
            instructions = _info_box(f'''
                    <h3 style="margin-top:0;color:#7c3aed;">📋 What to do when it's ready?</h3>
                    <ol style="color:#374151;font-size:14px;padding-left:20px;margin:0;">
                        <li style="margin-bottom:8px;"><strong>Review all pages</strong> — make sure the illustrations and text look correct.</li>
                        <li style="margin-bottom:8px;"><strong>Regenerate any images</strong> you don't like — you can do this for free before approving.</li>
                        <li style="margin-bottom:0;"><strong>Approve and send to print</strong> — only then will we print and ship your book.</li>
                    </ol>
                ''')
            cta_label_link = "If the button doesn't work, copy this link into your browser:"
            wrapper_title = "🔍 Review Your Story Before Printing"

        content = f"""
                <h2 style="color:#7c3aed;margin-top:0;">{heading}</h2>
                <p style="font-size:16px;color:#374151;">
                    We are creating <strong>{child_name}</strong>'s personalized book. In a few minutes you'll be able to review it. 🎨
                </p>
                {instructions}
                {_success_box(f'''
                    <p style="margin-bottom:15px;color:#374151;font-weight:600;">Use this link to access your story when it is ready:</p>
                    {_cta_button(cta_label, recovery_url)}
                    <p style="margin-top:10px;font-size:12px;color:#6b7280;text-align:center;">{cta_label_link}</p>
                    <p style="font-size:11px;color:#374151;word-break:break-all;text-align:center;">{recovery_url}</p>
                ''')}
                {_alert_box(f'''
                    <p style="margin:0;color:#92400e;font-size:14px;">
                        <strong>⏳ Generation takes 5 to 10 minutes.</strong> Save this email to come back when it's ready.
                    </p>
                ''')}
                <p style="color:#374151;font-size:14px;">Questions? Email us at:</p>
                <p style="color:#374151;"><strong>pay@magicmemoriesbooks.com</strong></p>"""
        html_content = _email_wrapper(wrapper_title, content, to_email)

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = f"{FROM_NAME} <{FROM_EMAIL}>"
    msg['To'] = to_email
    msg.attach(MIMEText(html_content, 'html'))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(FROM_EMAIL, to_email, msg.as_string())
        print(f"[EMAIL] Recovery link sent to {to_email} (only_ebook={only_ebook}, has_pdf={has_pdf})")
        log_email('recovery_link', to_email, subject, 'SENT', child_name=child_name, lang=lang)
        return True
    except Exception as e:
        print(f"[EMAIL] Failed to send recovery link: {e}")
        log_email('recovery_link', to_email, subject, 'ERROR', child_name=child_name, lang=lang, error=str(e))
        return False


def send_generation_started_email(to_email: str, child_name: str, recovery_url: str, lang: str = 'es'):
    _recovery_url_line = f'<p style="margin-top:8px;font-size:11px;color:#6b7280;text-align:center;word-break:break-all;">{recovery_url}</p>'
    _recovery_box_es = _success_box(
        '<p style="margin-bottom:10px;color:#374151;font-weight:600;">'
        'Si cierras esta p\u00e1gina, usa este enlace para volver:</p>'
        + _cta_button("\U0001f517 Ver el estado de mi pedido", recovery_url)
        + _recovery_url_line
    )
    _recovery_box_en = _success_box(
        '<p style="margin-bottom:10px;color:#374151;font-weight:600;">'
        'If you close this page, use this link to come back:</p>'
        + _cta_button("\U0001f517 Check my order status", recovery_url)
        + _recovery_url_line
    )
    if lang == 'es':
        subject = f"✨ ¡Estamos generando el cuento de {child_name}!"
        content = f"""
                <h2 style="color:#7c3aed;text-align:center;margin-top:0;">¡Composición en marcha! 🎨</h2>
                <p style="font-size:16px;color:#374151;text-align:center;">
                    ¡Aprobaste el cuento! Ahora estamos componiendo el libro final de <strong>{child_name}</strong>.
                </p>
                {_alert_box('''
                    <p style="margin:0;color:#92400e;font-size:14px;">
                        <strong>⏳ Este proceso toma entre 10 y 20 minutos.</strong><br>
                        Recibirás otro email cuando tu cuento esté completamente listo.
                    </p>
                ''')}
                {_recovery_box_es}
                <p style="color:#374151;font-size:14px;text-align:center;">¿Tienes alguna duda? Escríbenos a:</p>
                <p style="color:#374151;text-align:center;"><strong>pay@magicmemoriesbooks.com</strong></p>"""
        html_content = _email_wrapper("✨ Generando tu Cuento", content, to_email)
    else:
        subject = f"✨ We're generating {child_name}'s story!"
        content = f"""
                <h2 style="color:#7c3aed;text-align:center;margin-top:0;">Composition underway! 🎨</h2>
                <p style="font-size:16px;color:#374151;text-align:center;">
                    You approved the story! We're now composing <strong>{child_name}</strong>'s final book.
                </p>
                {_alert_box('''
                    <p style="margin:0;color:#92400e;font-size:14px;">
                        <strong>⏳ This process takes 10 to 20 minutes.</strong><br>
                        You'll receive another email when your story is completely ready.
                    </p>
                ''')}
                {_recovery_box_en}
                <p style="color:#374151;font-size:14px;text-align:center;">Questions? Email us at:</p>
                <p style="color:#374151;text-align:center;"><strong>pay@magicmemoriesbooks.com</strong></p>"""
        html_content = _email_wrapper("✨ Generating your Story", content, to_email)

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = f"{FROM_NAME} <{FROM_EMAIL}>"
    msg['To'] = to_email
    msg.attach(MIMEText(html_content, 'html'))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(FROM_EMAIL, to_email, msg.as_string())
        print(f"[EMAIL] Generation started email sent to {to_email}")
        return True
    except Exception as e:
        print(f"[EMAIL] Failed to send generation started email: {e}")
        return False


def send_generation_failed_email(to_email: str, child_name: str, retry_url: str, lang: str = 'es'):
    if lang == 'es':
        subject = f"Problema con tu cuento - {child_name}"
        content = f"""
                <h2 style="color:#7c3aed;margin-top:0;">¡Hola!</h2>
                <p style="font-size:16px;color:#374151;">Lamentamos informarte que hubo un problema técnico al generar el cuento de <strong>{child_name}</strong>.</p>
                {_alert_box(f'''
                    <h3 style="margin-top:0;color:#92400e;">⚠️ ¿Qué pasó?</h3>
                    <p style="color:#92400e;font-size:14px;">Nuestro sistema de ilustraciones tuvo un error inesperado. Tu pago está registrado y no se te cobrará nuevamente.</p>
                ''')}
                {_success_box(f'''
                    <h3 style="margin-top:0;color:#166534;">🎁 Solución Sin Costo Adicional</h3>
                    <p style="color:#374151;font-size:14px;">Puedes volver a crear tu historia completamente gratis usando el siguiente enlace:</p>
                    {_cta_button("Crear Mi Cuento Nuevamente", retry_url)}
                ''')}
                <p style="color:#374151;font-size:14px;">Si prefieres un reembolso o tienes alguna duda, escríbenos a:</p>
                <p style="color:#374151;"><strong>pay@magicmemoriesbooks.com</strong></p>
                <p style="color:#374151;font-size:14px;">Incluye tu email de compra y te ayudaremos inmediatamente.</p>
                <p style="color:#7c3aed;font-weight:bold;text-align:center;margin-top:20px;">Pedimos disculpas por las molestias.</p>"""
        html_content = _email_wrapper("✨ Magic Memories Books ✨", content, to_email)
    else:
        subject = f"Issue with your story - {child_name}"
        content = f"""
                <h2 style="color:#7c3aed;margin-top:0;">Hello!</h2>
                <p style="font-size:16px;color:#374151;">We're sorry to inform you that there was a technical issue generating <strong>{child_name}</strong>'s story.</p>
                {_alert_box(f'''
                    <h3 style="margin-top:0;color:#92400e;">⚠️ What happened?</h3>
                    <p style="color:#92400e;font-size:14px;">Our illustration system experienced an unexpected error. Your payment is recorded and you will not be charged again.</p>
                ''')}
                {_success_box(f'''
                    <h3 style="margin-top:0;color:#166534;">🎁 Free Solution</h3>
                    <p style="color:#374151;font-size:14px;">You can recreate your story completely free using this link:</p>
                    {_cta_button("Create My Story Again", retry_url)}
                ''')}
                <p style="color:#374151;font-size:14px;">If you prefer a refund or have questions, email us at:</p>
                <p style="color:#374151;"><strong>pay@magicmemoriesbooks.com</strong></p>
                <p style="color:#374151;font-size:14px;">Include your purchase email and we'll help you immediately.</p>
                <p style="color:#7c3aed;font-weight:bold;text-align:center;margin-top:20px;">We apologize for the inconvenience.</p>"""
        html_content = _email_wrapper("✨ Magic Memories Books ✨", content, to_email)
    
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = f"{FROM_NAME} <{FROM_EMAIL}>"
    msg['To'] = to_email
    msg.attach(MIMEText(html_content, 'html'))
    
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(FROM_EMAIL, to_email, msg.as_string())
        print(f"[EMAIL] Generation failed notification sent to {to_email}")
        return True
    except Exception as e:
        print(f"[EMAIL] Failed to send generation failed email: {e}")
        return False


def send_print_failure_email(to_email: str, child_name: str, error_message: str, lang: str = 'es', preview_id: str = ''):
    is_tax_issue = any(kw in error_message.lower() for kw in ['tax', 'cuit', 'fiscal', 'tax id'])
    is_address_issue = any(kw in error_message.lower() for kw in ['address', 'street', 'city', 'postal'])
    
    if is_tax_issue:
        issue_es = "La identificación fiscal proporcionada no es válida para el país de envío."
        issue_en = "The tax ID provided is not valid for the shipping country."
        action_es = "Necesitamos que nos envíes tu identificación fiscal correcta para reenviar tu libro a impresión."
        action_en = "We need you to send us your correct tax ID so we can resubmit your book for printing."
    elif is_address_issue:
        issue_es = "Hay un problema con la dirección de envío proporcionada."
        issue_en = "There's an issue with the shipping address provided."
        action_es = "Necesitamos que nos envíes tu dirección corregida para reenviar tu libro a impresión."
        action_en = "We need you to send us your corrected address so we can resubmit your book for printing."
    else:
        issue_es = "Hubo un error técnico al enviar tu libro a la imprenta."
        issue_en = "There was a technical error sending your book to the printer."
        action_es = "Nuestro equipo ya fue notificado y resolverá el problema lo antes posible."
        action_en = "Our team has been notified and will resolve this as soon as possible."
    
    if lang == 'es':
        subject = f"Problema con la impresión de tu libro - {child_name}"
        content = f"""
                <h2 style="color:#7c3aed;margin-top:0;">Hola,</h2>
                <p style="font-size:16px;color:#374151;">Tu PDF digital del cuento de <strong>{child_name}</strong> fue generado correctamente y ya lo tienes disponible.</p>
                <p style="color:#374151;">Sin embargo, hubo un problema al enviar tu libro a la imprenta:</p>
                {_alert_box(f'''
                    <h3 style="margin-top:0;color:#92400e;">⚠️ Problema detectado</h3>
                    <p style="color:#92400e;font-size:14px;">{issue_es}</p>
                ''')}
                {_info_box(f'''
                    <h3 style="margin-top:0;color:#7c3aed;">¿Qué hacer?</h3>
                    <p style="color:#374151;font-size:14px;">{action_es}</p>
                    <p style="margin-top:10px;color:#374151;font-size:14px;">Escríbenos a <strong>info@magicmemoriesbooks.com</strong> y resolveremos tu envío lo antes posible.</p>
                ''')}
                <p style="color:#374151;font-size:14px;">Tu PDF digital está disponible en tu página de pedido. No necesitas pagar nada adicional.</p>"""
        html_content = _email_wrapper("✨ Magic Memories Books ✨", content, to_email)
    else:
        subject = f"Issue with your book printing - {child_name}"
        content = f"""
                <h2 style="color:#7c3aed;margin-top:0;">Hello,</h2>
                <p style="font-size:16px;color:#374151;">Your digital PDF for <strong>{child_name}</strong>'s story was generated successfully and is available for download.</p>
                <p style="color:#374151;">However, there was a problem sending your book to the printer:</p>
                {_alert_box(f'''
                    <h3 style="margin-top:0;color:#92400e;">⚠️ Issue detected</h3>
                    <p style="color:#92400e;font-size:14px;">{issue_en}</p>
                ''')}
                {_info_box(f'''
                    <h3 style="margin-top:0;color:#7c3aed;">What to do?</h3>
                    <p style="color:#374151;font-size:14px;">{action_en}</p>
                    <p style="margin-top:10px;color:#374151;font-size:14px;">Email us at <strong>info@magicmemoriesbooks.com</strong> and we'll resolve your shipment as soon as possible.</p>
                ''')}
                <p style="color:#374151;font-size:14px;">Your digital PDF is available on your order page. You don't need to pay anything extra.</p>"""
        html_content = _email_wrapper("✨ Magic Memories Books ✨", content, to_email)
    
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = f"{FROM_NAME} <{FROM_EMAIL}>"
    msg['To'] = to_email
    msg.attach(MIMEText(html_content, 'html'))
    
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(FROM_EMAIL, to_email, msg.as_string())
        print(f"[EMAIL] Print failure notification sent to {to_email}")
        return True
    except Exception as e:
        print(f"[EMAIL] Failed to send print failure email: {e}")
        return False


def send_print_resolved_email(to_email: str, child_name: str, print_job_id: str = '', lang: str = 'es'):
    if lang == 'es':
        subject = f"¡Tu libro está en camino a la imprenta! - {child_name}"
        content = f"""
                <h2 style="color:#7c3aed;margin-top:0;">¡Buenas noticias! 🎉</h2>
                <p style="font-size:16px;color:#374151;">Queremos contarte que el problema con la impresión del libro de <strong>{child_name}</strong> ha sido resuelto.</p>
                {_success_box(f'''
                    <h3 style="margin-top:0;color:#166534;">✅ Problema resuelto</h3>
                    <p style="color:#166534;font-size:14px;">Tu libro ya fue enviado a la imprenta y está siendo procesado.</p>
                    <p style="color:#166534;font-size:13px;">Número de orden de impresión: <strong>{print_job_id}</strong></p>
                ''')}
                {_info_box(f'''
                    <h3 style="margin-top:0;color:#7c3aed;">¿Qué sigue?</h3>
                    <p style="color:#374151;font-size:14px;">Tu libro será impreso y enviado a la dirección que proporcionaste. El tiempo de entrega depende del método de envío seleccionado.</p>
                    <p style="margin-top:10px;color:#374151;font-size:14px;">Si tienes alguna pregunta, escríbenos a <strong>info@magicmemoriesbooks.com</strong>.</p>
                ''')}
                <p style="color:#374151;font-size:14px;">Lamentamos las molestias y agradecemos tu paciencia. ¡Esperamos que disfrutes el libro!</p>"""
        html_content = _email_wrapper("✨ Magic Memories Books ✨", content, to_email)
    else:
        subject = f"Your book is on its way to the printer! - {child_name}"
        content = f"""
                <h2 style="color:#7c3aed;margin-top:0;">Great news! 🎉</h2>
                <p style="font-size:16px;color:#374151;">We wanted to let you know that the printing issue with <strong>{child_name}</strong>'s book has been resolved.</p>
                {_success_box(f'''
                    <h3 style="margin-top:0;color:#166534;">✅ Issue resolved</h3>
                    <p style="color:#166534;font-size:14px;">Your book has been sent to the printer and is now being processed.</p>
                    <p style="color:#166534;font-size:13px;">Print order number: <strong>{print_job_id}</strong></p>
                ''')}
                {_info_box(f'''
                    <h3 style="margin-top:0;color:#7c3aed;">What happens next?</h3>
                    <p style="color:#374151;font-size:14px;">Your book will be printed and shipped to the address you provided. Delivery time depends on the shipping method you selected.</p>
                    <p style="margin-top:10px;color:#374151;font-size:14px;">If you have any questions, email us at <strong>info@magicmemoriesbooks.com</strong>.</p>
                ''')}
                <p style="color:#374151;font-size:14px;">We apologize for the inconvenience and appreciate your patience. We hope you enjoy the book!</p>"""
        html_content = _email_wrapper("✨ Magic Memories Books ✨", content, to_email)

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = f"{FROM_NAME} <{FROM_EMAIL}>"
    msg['To'] = to_email
    msg.attach(MIMEText(html_content, 'html'))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(FROM_EMAIL, to_email, msg.as_string())
        print(f"[EMAIL] Print resolved notification sent to {to_email}")
        return True
    except Exception as e:
        print(f"[EMAIL] Failed to send print resolved email: {e}")
        return False


def send_print_failure_admin_email(preview_id: str, child_name: str, error_message: str, 
                                    customer_email: str = '', shipping_address: dict = None,
                                    story_id: str = '', product_type: str = ''):
    admin_email = FROM_EMAIL
    
    addr_html = ''
    if shipping_address:
        addr_parts = []
        for k in ['name', 'street1', 'street2', 'city', 'state_code', 'postal_code', 'country_code']:
            v = shipping_address.get(k, '')
            if v:
                addr_parts.append(f"<strong>{k}:</strong> {v}")
        addr_html = '<br>'.join(addr_parts)
    
    replit_domain = os.environ.get('REPLIT_DEV_DOMAIN', '')
    if replit_domain:
        rescue_url = f"https://{replit_domain}/admin/rescue-order/{preview_id}"
    else:
        site_domain = os.environ.get('SITE_DOMAIN', 'magicmemoriesbooks.com')
        rescue_url = f"https://{site_domain}/admin/rescue-order/{preview_id}"
    
    subject = f"[ALERTA] Fallo Impresión - {child_name} ({preview_id[:8]})"
    
    address_section = ""
    if addr_html:
        address_section = f"""
        <h3 style="color:#dc2626;margin-top:20px;font-size:16px;">Dirección de envío:</h3>
        <div style="background:#fef2f2;padding:15px;border-radius:8px;border-left:4px solid #dc2626;margin:10px 0;">
            {addr_html}
        </div>
        """
    else:
        address_section = '<p style="color:#6b7280;font-style:italic;">Sin dirección de envío</p>'
    
    content = f"""
        <table style="width:100%;border-collapse:collapse;font-size:14px;margin-bottom:15px;">
            <tr style="background:#fef2f2;"><td style="padding:10px 12px;color:#6b7280;font-size:13px;width:140px;">Preview ID</td><td style="padding:10px 12px;color:#1f2937;font-weight:600;">{preview_id}</td></tr>
            <tr><td style="padding:10px 12px;color:#6b7280;font-size:13px;">Nombre del niño</td><td style="padding:10px 12px;color:#1f2937;font-weight:600;">{child_name}</td></tr>
            <tr style="background:#fef2f2;"><td style="padding:10px 12px;color:#6b7280;font-size:13px;">Email cliente</td><td style="padding:10px 12px;color:#1f2937;font-weight:600;">{customer_email or 'No disponible'}</td></tr>
            <tr><td style="padding:10px 12px;color:#6b7280;font-size:13px;">Producto</td><td style="padding:10px 12px;color:#1f2937;font-weight:600;">{product_type or story_id or 'N/A'}</td></tr>
        </table>
        
        <h3 style="color:#dc2626;margin-top:20px;font-size:16px;">Error de impresión:</h3>
        <div style="background:#fef3c7;border-left:4px solid #f59e0b;border-radius:8px;padding:15px;margin:15px 0;font-family:monospace;font-size:13px;word-break:break-all;color:#92400e;">{error_message}</div>
        
        {address_section}
        
        <div style="text-align:center;margin-top:25px;">
            <a href="{rescue_url}" style="display:inline-block;background-color:#dc2626;background-image:linear-gradient(135deg,#dc2626,#b91c1c);color:#ffffff;padding:12px 28px;border-radius:8px;text-decoration:none;font-weight:700;font-size:15px;">Rescatar Pedido</a>
        </div>
        
        <p style="margin-top:20px;font-size:13px;color:#6b7280;">
            Desde la pagina de rescate puedes ver el libro completo, corregir la direccion y reenviar a la imprenta.
        </p>
    """
    
    html_body = _admin_wrapper("⚠️ Fallo en Envío a Imprenta", content)
    
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = f"{FROM_NAME} <{FROM_EMAIL}>"
    msg['To'] = admin_email
    msg.attach(MIMEText(html_body, 'html'))
    
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(FROM_EMAIL, admin_email, msg.as_string())
        print(f"[EMAIL] Print failure ADMIN notification sent to {admin_email}")
        return True
    except Exception as e:
        print(f"[EMAIL] Failed to send print failure admin email: {e}")
        return False


send_lulu_failure_email = send_print_failure_email
send_lulu_failure_admin_email = send_print_failure_admin_email
send_lulu_resolved_email = send_print_resolved_email

send_cp_failure_email = send_print_failure_email
send_cp_failure_admin_email = send_print_failure_admin_email


def send_cp_order_notification(
    preview_id: str,
    cp_order_ref: str,
    title: str,
    customer_email: str,
    shipping_address: dict,
    pdf_url: str = '',
    cp_cost_eur: float = 0,
    print_cost_eur: float = 0,
    customer_total_usd: float = 0,
    cp_success: bool = True,
    cp_error: str = ''
) -> dict:
    """Admin notification email for a new Cloudprinter order (success or failure)."""
    from datetime import datetime
    admin_email = "pay@magicmemoriesbooks.com"
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    addr = shipping_address or {}
    address_name = addr.get('name', 'N/A')
    address_street = addr.get('street1', 'N/A')
    address_city = addr.get('city', 'N/A')
    address_state = addr.get('state_code', 'N/A')
    address_country = addr.get('country_code', 'N/A')
    address_postal = addr.get('postcode', addr.get('postal_code', 'N/A'))

    if cp_success:
        subject = f"📦 Nuevo pedido Cloudprinter - {title} - {cp_order_ref}"
        email_header = "📦 Nuevo Pedido Cloudprinter"
    else:
        subject = f"⚠️ FALLO Cloudprinter - {title} ({preview_id[:8]})"
        email_header = "⚠️ Fallo en Envío a Cloudprinter"

    pdf_link = f'<a href="{pdf_url}" style="color:#dc2626;font-weight:600;">📄 Descargar PDF Libro</a>' if pdf_url else '(no disponible)'

    cost_row = ''
    if cp_cost_eur or print_cost_eur or customer_total_usd:
        total_cp_eur = (cp_cost_eur or 0) + (print_cost_eur or 0)
        cost_row = f'<tr style="background:#fff7ed;"><td style="padding:10px 12px;color:#6b7280;font-size:13px;width:140px;">💶 Coste CP (impresión + envío)</td><td style="padding:10px 12px;color:#ea580c;font-size:14px;font-weight:700;">€{total_cp_eur:.2f} EUR&nbsp;&nbsp;<span style="font-size:12px;color:#6b7280;">(impresión €{print_cost_eur:.2f} + envío €{cp_cost_eur:.2f})</span></td></tr>'

    def _row(label, value, alt=False):
        bg = 'background:#fef2f2;' if alt else ''
        return f'<tr style="{bg}"><td style="padding:10px 12px;color:#6b7280;font-size:13px;width:140px;">{label}</td><td style="padding:10px 12px;color:#1f2937;font-size:14px;font-weight:600;">{value}</td></tr>'

    status_section = ''
    if cp_success:
        status_section = f"""
        <h3 style="color:#16a34a;margin-top:20px;font-size:16px;">🖨️ Cloudprinter</h3>
        <div style="background:#f0fdf4;padding:15px;border-radius:8px;border-left:4px solid #16a34a;margin:10px 0;">
            <p style="margin:0;color:#1f2937;font-size:14px;">✅ Pedido enviado automáticamente a Cloudprinter.<br>
            Referencia: <strong>{cp_order_ref}</strong></p>
        </div>"""
    else:
        status_section = f"""
        <h3 style="color:#dc2626;margin-top:20px;font-size:16px;">❌ Error Cloudprinter</h3>
        <div style="background:#fef2f2;padding:15px;border-radius:8px;border-left:4px solid #dc2626;margin:10px 0;">
            <p style="margin:0;color:#dc2626;font-size:14px;font-weight:600;">El pedido NO se envió a Cloudprinter.</p>
            <p style="margin:10px 0 0;font-family:monospace;font-size:13px;color:#92400e;background:#fef3c7;padding:10px;border-radius:6px;">{cp_error or 'Error desconocido'}</p>
            <p style="margin:10px 0 0;font-size:13px;color:#6b7280;">El PDF está disponible en el enlace de arriba. Puedes reenviar el pedido a Cloudprinter manualmente desde el panel de admin.</p>
        </div>"""

    content = f"""
        <table style="width:100%;border-collapse:collapse;font-size:14px;margin-bottom:15px;">
            {_row('CP Order Ref', cp_order_ref, True)}
            {_row('Preview ID', preview_id[:12])}
            {_row('Título', title, True)}
            {_row('Cliente', customer_email)}
            {_row('Fecha', timestamp, True)}
            {cost_row}
        </table>
        <h3 style="color:#dc2626;margin-top:20px;font-size:16px;">📍 Dirección de Envío</h3>
        <div style="background:#fef2f2;padding:15px;border-radius:8px;border-left:4px solid #dc2626;margin:10px 0;">
            <p style="margin:0;color:#1f2937;font-size:14px;">
                <strong>{address_name}</strong><br>
                {address_street}<br>
                {address_city}, {address_state} {address_postal}<br>
                {address_country}
            </p>
        </div>
        <h3 style="color:#dc2626;margin-top:20px;font-size:16px;">📎 Archivo PDF</h3>
        <div style="background:#fef2f2;padding:15px;border-radius:8px;border-left:4px solid #dc2626;margin:10px 0;">
            <p style="margin:0;">{pdf_link}</p>
        </div>
        {status_section}
    """

    html_body = _admin_wrapper(email_header, content)
    text_body = f"{'NUEVO PEDIDO' if cp_success else 'FALLO'} CLOUDPRINTER\nRef: {cp_order_ref}\nTítulo: {title}\nCliente: {customer_email}\nFecha: {timestamp}\n\nDirección:\n{address_name}\n{address_street}\n{address_city}, {address_state} {address_postal}\n{address_country}"

    if not SMTP_USER or not SMTP_PASSWORD:
        print(f"[CP NOTIFICATION] SMTP not configured. Order ref: {cp_order_ref}")
        return {'success': True, 'message': 'CP notification logged (SMTP not configured)', 'simulated': True}

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{FROM_NAME} <{FROM_EMAIL}>"
        msg['To'] = admin_email
        msg.attach(MIMEText(text_body, 'plain', 'utf-8'))
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        print(f"[CP NOTIFICATION] Admin email sent: {cp_order_ref}")
        return {'success': True, 'message': 'CP notification sent'}
    except Exception as e:
        print(f"[CP NOTIFICATION] Error sending email: {e}")
        return {'success': False, 'message': str(e)}


def send_cp_tracking_email(
    to_email: str,
    child_name: str,
    book_title: str,
    tracking_code: str,
    tracking_url: str = '',
    shipping_address: dict = None,
    lang: str = 'es'
) -> bool:
    """Send tracking number to customer when Cloudprinter ships their book via FedEx."""
    if not to_email:
        return False

    addr = shipping_address or {}
    addr_name = addr.get('name', child_name)
    addr_street = addr.get('street1', '')
    addr_city = addr.get('city', '')
    addr_postal = addr.get('postcode', addr.get('postal_code', ''))
    addr_country = addr.get('country_code', '')
    addr_html = f"<strong>{addr_name}</strong><br>{addr_street}<br>{addr_city} {addr_postal}<br>{addr_country}"

    tracking_btn = _cta_button("📦 Rastrear mi paquete en FedEx", tracking_url) if tracking_url else \
                   f'<p style="font-size:15px;color:#374151;"><strong>Número de seguimiento:</strong> <code style="background:#f3f4f6;padding:4px 8px;border-radius:4px;">{tracking_code}</code></p>'
    tracking_btn_en = _cta_button("📦 Track my package on FedEx", tracking_url) if tracking_url else \
                   f'<p style="font-size:15px;color:#374151;"><strong>Tracking number:</strong> <code style="background:#f3f4f6;padding:4px 8px;border-radius:4px;">{tracking_code}</code></p>'

    if lang == 'es':
        subject = f"¡Tu libro '{book_title}' para {child_name} está en camino!"
        content = f"""
            <p style="font-size:16px;color:#374151;">¡El cartero está en camino! Tu libro ya ha sido recogido por FedEx y está de camino a casa.</p>
            {_success_box(f'''
                <h3 style="margin-top:0;color:#166534;">🚚 ¡Tu libro "{book_title}" ha salido!</h3>
                <p style="color:#374151;font-size:14px;">El libro de <strong>{child_name}</strong> está siendo enviado a tu dirección.</p>
            ''')}
            {_info_box(f'''
                <h3 style="margin-top:0;color:#7c3aed;">📦 Seguimiento del envío</h3>
                {tracking_btn}
                <p style="color:#374151;font-size:13px;margin-top:12px;">
                    <strong>Dirección de entrega:</strong><br>{addr_html}
                </p>
                <p style="color:#374151;font-size:13px;margin-top:8px;">
                    <strong>Tiempo estimado de entrega:</strong> 3-5 días hábiles
                </p>
            ''')}
            {_alert_box(f'''
                <p style="margin:0;color:#92400e;font-size:14px;">
                    <strong>¿Alguna pregunta sobre el envío?</strong><br>
                    Escríbenos a <strong>print@magicmemoriesbooks.com</strong> y te ayudamos.
                </p>
            ''')}
            {_newsletter_invite_html('es')}"""
        html_content = _email_wrapper("🚚 ¡Tu Libro Está en Camino!", content, to_email)
    else:
        subject = f"Your book '{book_title}' for {child_name} is on its way!"
        content = f"""
            <p style="font-size:16px;color:#374151;">Your book has been picked up by FedEx and is on its way to you!</p>
            {_success_box(f'''
                <h3 style="margin-top:0;color:#166534;">🚚 Your book "{book_title}" has shipped!</h3>
                <p style="color:#374151;font-size:14px;">The book for <strong>{child_name}</strong> is on its way to your address.</p>
            ''')}
            {_info_box(f'''
                <h3 style="margin-top:0;color:#7c3aed;">📦 Shipment tracking</h3>
                {tracking_btn_en}
                <p style="color:#374151;font-size:13px;margin-top:12px;">
                    <strong>Delivery address:</strong><br>{addr_html}
                </p>
                <p style="color:#374151;font-size:13px;margin-top:8px;">
                    <strong>Estimated delivery:</strong> 3-5 business days
                </p>
            ''')}
            {_alert_box(f'''
                <p style="margin:0;color:#92400e;font-size:14px;">
                    <strong>Any questions about your shipment?</strong><br>
                    Email us at <strong>print@magicmemoriesbooks.com</strong> and we'll help.
                </p>
            ''')}
            {_newsletter_invite_html('en')}"""
        html_content = _email_wrapper("🚚 Your Book Is On Its Way!", content, to_email)

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = f"{FROM_NAME} <{FROM_EMAIL}>"
    msg['To'] = to_email
    msg.attach(MIMEText(html_content, 'html'))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(FROM_EMAIL, to_email, msg.as_string())
        print(f"[EMAIL] CP tracking email sent to {to_email} (tracking={tracking_code})")
        return True
    except Exception as e:
        print(f"[EMAIL] Failed to send CP tracking email: {e}")
        return False


def send_illustrations_ready_email(to_email: str, child_name: str, preview_url: str, lang: str = 'es'):
    if not to_email:
        print("[EMAIL] No email address provided")
        return False
    
    if not SMTP_HOST or not SMTP_USER:
        print(f"[EMAIL SERVICE] SMTP not configured. Would send illustrations ready email to: {to_email}")
        return False
    
    try:
        if lang == 'es':
            subject = "¡Tus ilustraciones están listas! - Magic Memories Books"
            content = f"""
                <h2 style="color:#7c3aed;margin-top:0;text-align:center;">🎨 ¡Tus ilustraciones están listas!</h2>
                <p style="color:#374151;font-size:16px;line-height:1.8;">
                    ¡Hola! Las ilustraciones del libro de <strong>{child_name}</strong> ya están listas para que las revises.
                </p>
                <p style="color:#374151;font-size:16px;line-height:1.8;">
                    Hemos creado 20 escenas únicas con los personajes que nos describiste. Cada ilustración 
                    está personalizada para tu historia.
                </p>
                {_cta_button("👀 Ver mis ilustraciones", preview_url)}
                {_alert_box('''
                    <p style="color:#92400e;font-size:14px;margin:0;">
                        💡 <strong>Consejo:</strong> Revisa cada página con calma. Si alguna ilustración no te convence, 
                        puedes solicitar una regeneración sin costo adicional antes de pagar.
                    </p>
                ''')}
                <p style="color:#6b7280;font-size:14px;text-align:center;margin-top:20px;">
                    Tu número de pedido: <strong style="font-family:monospace;">{preview_url.split('/')[-1]}</strong>
                </p>
            """
        else:
            subject = "Your illustrations are ready! - Magic Memories Books"
            content = f"""
                <h2 style="color:#7c3aed;margin-top:0;text-align:center;">🎨 Your illustrations are ready!</h2>
                <p style="color:#374151;font-size:16px;line-height:1.8;">
                    Hello! The illustrations for <strong>{child_name}</strong>'s book are ready for your review.
                </p>
                <p style="color:#374151;font-size:16px;line-height:1.8;">
                    We've created 20 unique scenes with the characters you described. Each illustration 
                    is personalized for your story.
                </p>
                {_cta_button("👀 View my illustrations", preview_url)}
                {_alert_box('''
                    <p style="color:#92400e;font-size:14px;margin:0;">
                        💡 <strong>Tip:</strong> Review each page carefully. If any illustration doesn't look right, 
                        you can request a free regeneration before paying.
                    </p>
                ''')}
                <p style="color:#6b7280;font-size:14px;text-align:center;margin-top:20px;">
                    Your order number: <strong style="font-family:monospace;">{preview_url.split('/')[-1]}</strong>
                </p>
            """
        
        html_content = _email_wrapper("✨ Magic Memories Books ✨", content, to_email)
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{FROM_NAME} <{FROM_EMAIL}>"
        msg['To'] = to_email
        msg.attach(MIMEText(html_content, 'html'))
        
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(FROM_EMAIL, to_email, msg.as_string())
        print(f"[EMAIL] Illustrations ready notification sent to {to_email}")
        return True
    except Exception as e:
        print(f"[EMAIL] Failed to send illustrations ready email: {e}")
        return False


def _ebook_upsell_html(child_name: str, story_name: str, preview_id: str, lang: str = 'es') -> str:
    import urllib.parse
    if lang == 'es':
        body = (
            f"Hola, me gustaría el libro impreso / PDF del cuento:\n"
            f"{child_name} — {story_name}\n"
            f"Referencia: {preview_id}"
        )
        subject = f"Upgrade — {child_name} / {story_name}"
        title = "¿Te ha encantado? También puedes tenerlo impreso"
        desc = "Consigue el libro en tapa dura o el PDF listo para imprimir en casa."
        btn_text = "📬 Quiero el libro impreso o PDF"
        formats_items = """
            <li style="padding:2px 0;color:#374151;">📦 <strong>Libro tapa dura</strong> — enviado a tu casa</li>
            <li style="padding:2px 0;color:#374151;">🖨️ <strong>PDF imprimible</strong> — listo para tu imprenta local</li>
        """
        footnote = "Solo escríbenos. El equipo te mandará el enlace de pago en minutos."
    else:
        body = (
            f"Hello, I'd like the printed book / PDF of the story:\n"
            f"{child_name} — {story_name}\n"
            f"Reference: {preview_id}"
        )
        subject = f"Upgrade — {child_name} / {story_name}"
        title = "Loved it? Get it in print too"
        desc = "Order a hardcover book or a PDF ready to print at home."
        btn_text = "📬 I want the printed book or PDF"
        formats_items = """
            <li style="padding:2px 0;color:#374151;">📦 <strong>Hardcover book</strong> — shipped to your home</li>
            <li style="padding:2px 0;color:#374151;">🖨️ <strong>Printable PDF</strong> — ready for your local print shop</li>
        """
        footnote = "Just write to us and we'll send you the payment link in minutes."

    encoded_subject = urllib.parse.quote(subject)
    encoded_body = urllib.parse.quote(body)
    mailto = f"mailto:contacto@magicmemoriesbooks.com?subject={encoded_subject}&body={encoded_body}"

    return f"""
    <div style="background:linear-gradient(135deg,#fdf4ff,#fce7f3);padding:20px;border-radius:14px;margin:20px 0;border:1.5px solid #e9d5ff;text-align:center;">
        <p style="font-size:16px;font-weight:bold;color:#7c3aed;margin:0 0 6px 0;">✨ {title}</p>
        <p style="font-size:13px;color:#374151;margin:0 0 10px 0;">{desc}</p>
        <ul style="text-align:left;list-style:none;padding-left:0;display:inline-block;margin:0 0 14px 0;">{formats_items}</ul><br>
        <a href="{mailto}" style="display:inline-block;background-color:#7c3aed;background-image:linear-gradient(135deg,#7c3aed,#9333ea);color:#ffffff;padding:12px 24px;border-radius:20px;text-decoration:none;font-weight:bold;font-size:14px;">{btn_text}</a>
        <p style="font-size:11px;color:#9ca3af;margin:10px 0 0 0;">{footnote}</p>
    </div>
    """


def send_ebook_admin_notification(
    preview_id: str,
    child_name: str,
    story_name: str,
    customer_email: str,
    product_type: str,
    pdf_path: Optional[str] = None,
    visor_url: str = '',
    buyer_country: str = ''
) -> dict:
    """Notify admin (pay@) with printable PDF when an eBook purchase completes."""
    admin_email = 'pay@magicmemoriesbooks.com'
    from datetime import datetime

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    product_label = {
        'ebook': 'eBook Cuento Express ($6)',
        'qs_digital': 'eBook Cuento Express ($6)',
        'universo_ebook': 'eBook Universos Ilustrados ($9)',
        'personalized_ebook': 'eBook Libro Personalizado ($9)',
        'illustrated_ebook': 'eBook Libro Ilustrado ($9)',
    }.get(product_type, product_type or 'eBook')

    location_html = ''
    location_text = ''
    if buyer_country:
        location_html = (
            f'<tr><td style="padding:8px 12px;color:#6b7280;">País</td>'
            f'<td style="padding:8px 12px;color:#1f2937;font-weight:600;">🌍 {buyer_country}</td></tr>'
        )
        location_text = f'País: {buyer_country}\n'

    has_pdf = bool(pdf_path and os.path.exists(pdf_path))
    pdf_status_html = (
        "<p style='color:#16a34a;font-size:14px;font-weight:600;'>✅ PDF imprimible adjunto a este email.</p>"
        if has_pdf else
        "<p style='color:#f59e0b;font-size:13px;'>⚠️ PDF no disponible (fallo en generación).</p>"
    )
    visor_html = (
        f"<p style='color:#374151;font-size:14px;'>🔗 <strong>Visor:</strong> "
        f"<a href='{visor_url}' style='color:#9333ea;'>{visor_url}</a></p>"
        if visor_url else ""
    )

    content = f"""
        <h2 style="color:#7c3aed;margin-top:0;">Nuevo pedido eBook recibido</h2>
        <table style="width:100%;border-collapse:collapse;font-size:14px;margin-bottom:15px;">
            <tr><td style="padding:8px 12px;color:#6b7280;width:140px;">Producto</td>
                <td style="padding:8px 12px;color:#1f2937;font-weight:600;">{product_label}</td></tr>
            <tr style="background:#f9fafb;"><td style="padding:8px 12px;color:#6b7280;">Niño/a</td>
                <td style="padding:8px 12px;color:#1f2937;font-weight:600;">{child_name}</td></tr>
            <tr><td style="padding:8px 12px;color:#6b7280;">Cuento</td>
                <td style="padding:8px 12px;color:#1f2937;font-weight:600;">{story_name}</td></tr>
            <tr style="background:#f9fafb;"><td style="padding:8px 12px;color:#6b7280;">Cliente</td>
                <td style="padding:8px 12px;color:#1f2937;">{customer_email or '—'}</td></tr>
            <tr><td style="padding:8px 12px;color:#6b7280;">Referencia</td>
                <td style="padding:8px 12px;color:#1f2937;font-family:monospace;font-size:12px;">{preview_id}</td></tr>
            <tr style="background:#f9fafb;"><td style="padding:8px 12px;color:#6b7280;">Fecha</td>
                <td style="padding:8px 12px;color:#1f2937;">{timestamp}</td></tr>
            {location_html}
        </table>
        {visor_html}
        {pdf_status_html}
        <p style="color:#6b7280;font-size:12px;margin-top:16px;">
            Para compartir upgrade con el cliente:<br>
            <code style="background:#f3f4f6;padding:2px 6px;border-radius:4px;">
                https://magicmemoriesbooks.com/story-checkout/{preview_id}
            </code>
        </p>
    """

    html_body = _admin_wrapper("📧 Nuevo eBook Vendido", content)

    text_body = f"""
NUEVO EBOOK VENDIDO
===================
Producto: {product_label}
Niño/a: {child_name}
Cuento: {story_name}
Cliente: {customer_email or '—'}
Referencia: {preview_id}
Fecha: {timestamp}
{location_text}Visor: {visor_url or 'pendiente'}
PDF: {"adjunto" if has_pdf else "no disponible"}
Upgrade link: https://magicmemoriesbooks.com/story-checkout/{preview_id}
    """

    if not SMTP_USER or not SMTP_PASSWORD:
        print(f"[ADMIN-EBOOK] SMTP no configurado. Notificación para {preview_id} ({child_name})")
        try:
            with open('email_log.txt', 'a') as f:
                f.write(f"\n{'='*50}\nEBOOK ADMIN NOTIFICATION\nTO: {admin_email}\nREF: {preview_id}\n{'='*50}\n")
        except Exception:
            pass
        return {'success': True, 'simulated': True}

    try:
        if has_pdf:
            msg = MIMEMultipart('mixed')
            alt_part = MIMEMultipart('alternative')
        else:
            msg = MIMEMultipart('alternative')
            alt_part = msg

        msg['Subject'] = f"📧 Nuevo eBook: {child_name} — {story_name[:40]} [{preview_id[:8]}]"
        msg['From'] = f"{FROM_NAME} <{FROM_EMAIL}>"
        msg['To'] = admin_email

        alt_part.attach(MIMEText(text_body, 'plain', 'utf-8'))
        alt_part.attach(MIMEText(html_body, 'html', 'utf-8'))

        if has_pdf:
            msg.attach(alt_part)
            safe_name = child_name.replace(' ', '_').replace("'", "")
            _adm_fname = os.path.basename(pdf_path)
            _adm_fmt = "_LETTER" if "_LETTER" in _adm_fname else "_A4" if "_A4" in _adm_fname else ""
            attach_file(msg, pdf_path, f"{safe_name}_imprimible{_adm_fmt}.pdf")

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(FROM_EMAIL, admin_email, msg.as_string())

        print(f"[ADMIN-EBOOK] Notificación enviada a {admin_email} para {preview_id}")
        return {'success': True}
    except Exception as e:
        print(f"[ADMIN-EBOOK] Error enviando notificación: {e}")
        return {'success': False, 'error': str(e)}


def send_ebook_email(to_email: str, story_data: dict, visor_url: str, is_gift: bool = False,
                     pdf_printable_path: str = None, instructions_path: str = None,
                     pdf_download_url: str = None, preview_id: str = '',
                     is_print_order: bool = False):
    try:
        child_name = story_data.get('child_name', 'tu pequeno')
        story_name = story_data.get('story_name', 'tu cuento')
        lang = story_data.get('lang', 'es')
        
        pdf_is_primary = bool(pdf_printable_path) and is_gift

        if pdf_is_primary:
            if lang == 'es':
                subject = f"🖨️ ¡Tu PDF imprimible para {child_name} está listo! + eBook de regalo"
                access_info = "Además, tienes acceso por 6 meses a tu eBook interactivo de regalo."
                access_badge = "🎁 eBook de regalo — 6 meses de acceso"
            else:
                subject = f"🖨️ Your printable PDF for {child_name} is ready! + Gift eBook"
                access_info = "Plus, you have 6 months access to your gift interactive eBook."
                access_badge = "🎁 Gift eBook — 6 months access"
        elif is_gift:
            if lang == 'es':
                subject = f"🎁 ¡Tu eBook de regalo para {child_name} está listo!"
                access_info = "Tienes acceso por 6 meses a tu eBook interactivo."
                access_badge = "🎁 Acceso por 6 meses"
            else:
                subject = f"🎁 Your gift eBook for {child_name} is ready!"
                access_info = "You have 6 months access to your interactive eBook."
                access_badge = "🎁 6 months access"
        else:
            if lang == 'es':
                subject = f"📱 ¡Tu eBook Interactivo para {child_name} está listo!"
                access_info = "Tienes acceso permanente a tu eBook interactivo."
                access_badge = "✨ Acceso permanente"
            else:
                subject = f"📱 Your Interactive eBook for {child_name} is ready!"
                access_info = "You have permanent access to your interactive eBook."
                access_badge = "✨ Permanent access"
        
        if lang == 'es':
            button_text = "📖 Abrir mi eBook Interactivo"
            features_list = """
                    <li style="padding:3px 0;color:#374151;">📖 Flipbook interactivo - pasa las páginas como un libro real</li>
                    <li style="padding:3px 0;color:#374151;">🔊 Narración automática en cada página</li>
                    <li style="padding:3px 0;color:#374151;">🎵 Música de fondo ambiental</li>
                    <li style="padding:3px 0;color:#374151;">📱 Funciona en celular, tablet y computadora</li>
            """
            device_info = "Ábrelo en cualquier dispositivo — celular, tablet o computadora"
            thanks_msg = "¡Gracias por crear recuerdos mágicos!"
            features_title = "Tu eBook incluye:"
            attach_title = "📎 Archivos adjuntos:"
        else:
            button_text = "📖 Open my Interactive eBook"
            features_list = """
                    <li style="padding:3px 0;color:#374151;">📖 Interactive flipbook - turn pages like a real book</li>
                    <li style="padding:3px 0;color:#374151;">🔊 Automatic narration on each page</li>
                    <li style="padding:3px 0;color:#374151;">🎵 Ambient background music</li>
                    <li style="padding:3px 0;color:#374151;">📱 Works on phone, tablet and computer</li>
            """
            device_info = "Open it on any device — phone, tablet or computer"
            thanks_msg = "Thank you for creating magical memories!"
            features_title = "Your eBook includes:"
            attach_title = "📎 Attached files:"
        
        greeting = "¡Hola!" if lang == "es" else "Hello!"
        ebook_label = "Tu eBook interactivo" if lang == "es" else "Your interactive eBook"
        for_word = "para" if lang == "es" else "for"
        ready_word = "está listo." if lang == "es" else "is ready."
        
        attachments_section = ""
        download_section = ""
        if pdf_download_url:
            if lang == 'es':
                dl_title = "📥 Tu libro para imprimir"
                dl_desc = "Descarga el PDF de tu libro personalizado para imprimirlo en tapa dura."
                dl_button = "📄 Descargar PDF del Libro"
                print_title = "🖨️ Instrucciones de impresión"
                print_specs = """
                    <li style="padding:3px 0;color:#374151;">📐 <strong>Formato:</strong> A4 (21 x 29.7 cm)</li>
                    <li style="padding:3px 0;color:#374151;">📖 <strong>Encuadernación:</strong> Tapa dura (hardcover)</li>
                    <li style="padding:3px 0;color:#374151;">🎨 <strong>Interior:</strong> Color premium, papel satinado</li>
                    <li style="padding:3px 0;color:#374151;">📄 <strong>Páginas:</strong> 26 páginas a todo color</li>
                    <li style="padding:3px 0;color:#374151;">💡 También puedes llevar el PDF a tu imprenta local</li>
                """
            else:
                dl_title = "📥 Your book for printing"
                dl_desc = "Download the PDF of your personalized book to print it in hardcover."
                dl_button = "📄 Download Book PDF"
                print_title = "🖨️ Printing instructions"
                print_specs = """
                    <li style="padding:3px 0;color:#374151;">📐 <strong>Format:</strong> A4 (8.27 x 11.69 in)</li>
                    <li style="padding:3px 0;color:#374151;">📖 <strong>Binding:</strong> Hardcover</li>
                    <li style="padding:3px 0;color:#374151;">🎨 <strong>Interior:</strong> Premium color, satin paper</li>
                    <li style="padding:3px 0;color:#374151;">📄 <strong>Pages:</strong> 24 full-color pages</li>
                    <li style="padding:3px 0;color:#374151;">💡 You can also take this PDF to your local print shop</li>
                """
            download_section = f'''
            <div style="background:#f0fdf4;padding:20px;border-radius:12px;margin:20px 0;border:1px solid #bbf7d0;">
                <h4 style="margin-top:0;color:#166534;text-align:center;">{dl_title}</h4>
                <p style="color:#374151;font-size:14px;text-align:center;margin:8px 0 15px;">{dl_desc}</p>
                <div style="text-align:center;">
                    <a href="{pdf_download_url}" style="display:inline-block;background-color:#7c3aed;background-image:linear-gradient(135deg,#7c3aed,#6d28d9);color:#ffffff;padding:14px 28px;border-radius:10px;text-decoration:none;font-weight:bold;font-size:15px;">{dl_button}</a>
                </div>
            </div>
            <div style="background:#fef3c7;padding:15px;border-radius:12px;margin:15px 0;border:1px solid #fde68a;">
                <h4 style="margin-top:0;color:#92400e;">{print_title}</h4>
                <ul style="text-align:left;list-style:none;padding-left:0;margin:0.5em 0;">
                    {print_specs}
                </ul>
            </div>
            '''
        elif pdf_printable_path:
            print_label = "Listo para imprimir en casa o imprenta" if lang == "es" else "Ready to print at home or print shop"
            inst_label = "Instrucciones de impresión" if lang == "es" else "Printing instructions"
            _pf_fname = os.path.basename(pdf_printable_path) if pdf_printable_path else ""
            if "_LETTER" in _pf_fname:
                _pdf_size_label = 'PDF imprimible Carta (8.5×11")' if lang == "es" else 'Printable PDF Letter (8.5×11")'
            else:
                _pdf_size_label = "PDF imprimible A4 (21×29,7 cm)" if lang == "es" else "Printable PDF A4 (21×29.7 cm)"
            items = f'<li style="padding:3px 0;color:#374151;">🖨️ <strong>{_pdf_size_label}</strong> - {print_label}</li>'
            if instructions_path:
                items += f'<li style="padding:3px 0;color:#374151;">📋 <strong>{inst_label}</strong></li>'
            attachments_section = _info_box(f'''
                <h4 style="margin-top:0;color:#7c3aed;">{attach_title}</h4>
                <ul style="text-align:left;list-style:none;padding-left:0;margin:0.5em 0;">{items}</ul>
            ''')
        
        upsell_section = ""
        if not is_gift and preview_id and not is_print_order:
            upsell_section = _ebook_upsell_html(child_name, story_name, preview_id, lang)

        print_production_section = ""
        if is_print_order:
            if lang == 'es':
                print_production_section = _info_box(f'''
                    <h4 style="margin-top:0;color:#166534;">📦 Tu libro está en producción</h4>
                    <p style="color:#374151;font-size:14px;margin:0 0 10px 0;">
                        Hemos enviado tu pedido a imprenta. Cuando tu libro salga en reparto,
                        recibirás otro email con el número de seguimiento y el tiempo estimado
                        de entrega real.
                    </p>
                    <p style="color:#6b7280;font-size:13px;margin:0;">
                        ¿Tienes alguna duda? Escríbenos a <strong>pay@magicmemoriesbooks.com</strong>
                    </p>
                ''')
            else:
                print_production_section = _info_box(f'''
                    <h4 style="margin-top:0;color:#166534;">📦 Your book is in production</h4>
                    <p style="color:#374151;font-size:14px;margin:0 0 10px 0;">
                        We've sent your order to the printer. When your book ships,
                        you'll receive another email with the real tracking number and
                        estimated delivery time.
                    </p>
                    <p style="color:#6b7280;font-size:13px;margin:0;">
                        Questions? Email us at <strong>pay@magicmemoriesbooks.com</strong>
                    </p>
                ''')

        if pdf_is_primary:
            _pdf_intro = ("Tu PDF imprimible está adjunto a este email, listo para llevar a la imprenta."
                          if lang == 'es' else
                          "Your printable PDF is attached to this email, ready to take to a print shop.")
            _ebook_bonus_title = "🎁 Además: tu eBook interactivo de regalo" if lang == 'es' else "🎁 Bonus: your gift interactive eBook"
            content = f"""
            <h2 style="color:#7c3aed;text-align:center;margin-top:0;">{greeting}</h2>
            <p style="font-size:16px;color:#374151;text-align:center;">
                🖨️ <strong>"{story_name}"</strong> {for_word} <strong>{child_name}</strong> — {_pdf_intro}
            </p>

            {attachments_section}

            {download_section}

            {print_production_section}

            <div style="background:#f3e8ff;padding:15px;border-radius:12px;margin:20px 0;">
                <h4 style="margin-top:0;color:#7c3aed;text-align:center;">{_ebook_bonus_title}</h4>
                {_cta_button(button_text, visor_url)}
                <p style="color:#6b7280;font-size:12px;text-align:center;margin-top:-10px;">{device_info}</p>
                <div style="text-align:center;margin-top:8px;">
                    <p style="font-size:13px;font-weight:bold;color:#7c3aed;margin:0 0 3px 0;">{access_badge}</p>
                    <p style="font-size:12px;color:#374151;margin:0;">{access_info}</p>
                </div>
            </div>

            {upsell_section}

            {_newsletter_invite_html(lang)}

            <p style="color:#7c3aed;font-weight:bold;text-align:center;font-size:16px;">{thanks_msg} 💜</p>
        """
        else:
            content = f"""
            <h2 style="color:#7c3aed;text-align:center;margin-top:0;">{greeting}</h2>
            <p style="font-size:16px;color:#374151;text-align:center;">
                {ebook_label} <strong>"{story_name}"</strong> {for_word} <strong>{child_name}</strong> {ready_word}
            </p>
            {_cta_button(button_text, visor_url)}
            <p style="color:#6b7280;font-size:12px;text-align:center;margin-top:-15px;">{device_info}</p>

            <div style="background:#f3e8ff;padding:15px;border-radius:12px;margin:20px 0;text-align:center;">
                <p style="font-size:14px;font-weight:bold;color:#7c3aed;margin:0 0 5px 0;">{access_badge}</p>
                <p style="font-size:13px;color:#374151;margin:0;">{access_info}</p>
            </div>

            {_success_box(f'''
                <h4 style="margin-top:0;color:#166534;">{features_title}</h4>
                <ul style="text-align:left;list-style:none;padding-left:0;margin:0.5em 0;">{features_list}</ul>
            ''')}

            {download_section}

            {attachments_section}

            {print_production_section}
            
            {upsell_section}
            
            {_newsletter_invite_html(lang)}
            
            <p style="color:#7c3aed;font-weight:bold;text-align:center;font-size:16px;">{thanks_msg} 💜</p>
        """
        
        html_content = _email_wrapper("✨ Magic Memories Books ✨", content, to_email)
        
        has_attachments = pdf_printable_path or instructions_path
        if has_attachments:
            msg = MIMEMultipart('mixed')
            alt_part = MIMEMultipart('alternative')
        else:
            msg = MIMEMultipart('alternative')
            alt_part = msg
        
        msg['Subject'] = subject
        msg['From'] = f'{FROM_NAME} <{FROM_EMAIL}>'
        msg['To'] = to_email
        
        safe_name = child_name.replace(' ', '_').replace("'", "")
        
        pdf_download_text = ""
        if pdf_download_url:
            dl_label = "Descargar PDF del libro" if lang == "es" else "Download book PDF"
            pdf_download_text = f"\n{dl_label}: {pdf_download_url}\n"
        
        if pdf_is_primary:
            _pdf_ready = ("Tu PDF imprimible está adjunto a este email." if lang == 'es'
                          else "Your printable PDF is attached to this email.")
            _ebook_bonus_line = ("eBook interactivo de regalo (6 meses): " if lang == 'es'
                                 else "Gift interactive eBook (6 months): ")
            text_body = f"""
{_pdf_ready}

"{story_name}" {for_word} {child_name}

{_ebook_bonus_line}{visor_url}
{pdf_download_text}
{access_info}

{thanks_msg}
Magic Memories Books
        """
        else:
            text_body = f"""
{ebook_label} "{story_name}" {for_word} {child_name} {ready_word}

{button_text}: {visor_url}
{pdf_download_text}
{access_info}

{thanks_msg}
Magic Memories Books
        """
        
        alt_part.attach(MIMEText(text_body, 'plain'))
        alt_part.attach(MIMEText(html_content, 'html'))
        
        if has_attachments:
            msg.attach(alt_part)
            if pdf_printable_path and os.path.exists(pdf_printable_path):
                _pdf_fname = os.path.basename(pdf_printable_path)
                _fmt_label = "_LETTER" if "_LETTER" in _pdf_fname else "_A4" if "_A4" in _pdf_fname else ""
                _pdf_display_name = f"{safe_name}_imprimible{_fmt_label}.pdf"
                if attach_file(msg, pdf_printable_path, _pdf_display_name):
                    print(f"[EMAIL] Attached printable PDF: {pdf_printable_path}")
            if instructions_path and os.path.exists(instructions_path):
                if attach_file(msg, instructions_path, "instrucciones_impresion.pdf"):
                    print(f"[EMAIL] Attached instructions PDF: {instructions_path}")
        
        if not SMTP_USER or not SMTP_PASSWORD:
            print(f"[EMAIL] SMTP not configured. Would send eBook email to: {to_email}")
            return {'success': True, 'message': 'Email logged (SMTP not configured)'}
        
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(FROM_EMAIL, to_email, msg.as_string())
        
        attachments_info = ""
        if pdf_printable_path:
            attachments_info += f", printable_pdf=True"
        if instructions_path:
            attachments_info += f", instructions=True"
        if pdf_download_url:
            attachments_info += f", pdf_download_link=True"
        print(f"[EMAIL] eBook email sent to {to_email} (is_gift={is_gift}{attachments_info})")
        log_email('ebook_ready', to_email, subject, 'SENT',
                  preview_id=preview_id, child_name=story_data.get('child_name',''), lang=story_data.get('lang','es'))
        return {'success': True, 'message': f'eBook email sent to {to_email}'}
        
    except Exception as e:
        print(f"[EMAIL] Failed to send eBook email: {e}")
        log_email('ebook_ready', to_email, subject, 'ERROR',
                  preview_id=preview_id, child_name=story_data.get('child_name',''), lang=story_data.get('lang','es'), error=str(e))
        return {'success': False, 'error': str(e)}


def send_newsletter_welcome(to_email: str, lang: str, unsubscribe_token: str):
    site_url = os.environ.get('REPLIT_DEV_DOMAIN', 'magicmemoriesbooks.com')
    if lang == 'es':
        subject = "¡Bienvenido/a a la familia Magic Memories Books!"
        content = f"""
                <h2 style="color:#7c3aed;text-align:center;margin-top:0;">¡Bienvenido/a a la familia!</h2>
                <p style="color:#374151;font-size:15px;text-align:center;">Gracias por unirte a nuestra comunidad. Te avisaremos cuando lancemos nuevos cuentos, ofertas exclusivas y novedades mágicas.</p>
                <p style="color:#6b7280;font-size:12px;text-align:center;margin-top:20px;">
                    Si en algún momento deseas dejar de recibir estos correos, puedes
                    <a href="https://{site_url}/unsubscribe/{unsubscribe_token}" style="color:#9333ea;">darte de baja aquí</a>.
                </p>"""
        body_html = _email_wrapper("✨ Magic Memories Books ✨", content, to_email)
    else:
        subject = "Welcome to the Magic Memories Books family!"
        content = f"""
                <h2 style="color:#7c3aed;text-align:center;margin-top:0;">Welcome to the family!</h2>
                <p style="color:#374151;font-size:15px;text-align:center;">Thank you for joining our community. We'll let you know about new stories, exclusive offers, and magical updates.</p>
                <p style="color:#6b7280;font-size:12px;text-align:center;margin-top:20px;">
                    If you ever wish to stop receiving these emails, you can
                    <a href="https://{site_url}/unsubscribe/{unsubscribe_token}" style="color:#9333ea;">unsubscribe here</a>.
                </p>"""
        body_html = _email_wrapper("✨ Magic Memories Books ✨", content, to_email)

    if not SMTP_USER or not SMTP_PASSWORD:
        print(f"[NEWSLETTER] Welcome email logged for: {to_email}")
        return {'success': True, 'simulated': True}

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f'{FROM_NAME} <{FROM_EMAIL}>'
        msg['To'] = to_email
        msg.attach(MIMEText(body_html, 'html', 'utf-8'))
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(FROM_EMAIL, to_email, msg.as_string())
        print(f"[NEWSLETTER] Welcome email sent to {to_email}")
        return {'success': True}
    except Exception as e:
        print(f"[NEWSLETTER] Welcome email failed: {e}")
        return {'success': False, 'error': str(e)}


def send_newsletter_blast(to_email: str, subject: str, content: str, unsubscribe_token: str, lang: str = 'es'):
    site_url = os.environ.get('REPLIT_DEV_DOMAIN', 'magicmemoriesbooks.com')
    unsub_text = "Darte de baja" if lang == 'es' else "Unsubscribe"
    inner_content = f"""{content}
        <p style="text-align:center;margin-top:20px;font-size:12px;color:#6b7280;">
            <a href="https://{site_url}/unsubscribe/{unsubscribe_token}" style="color:#9333ea;">{unsub_text}</a>
        </p>"""
    body_html = _email_wrapper("✨ Magic Memories Books ✨", inner_content, to_email)

    if not SMTP_USER or not SMTP_PASSWORD:
        print(f"[NEWSLETTER] Blast email logged for: {to_email} | Subject: {subject}")
        return {'success': True, 'simulated': True}

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f'{FROM_NAME} <{FROM_EMAIL}>'
        msg['To'] = to_email
        msg.attach(MIMEText(body_html, 'html', 'utf-8'))
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(FROM_EMAIL, to_email, msg.as_string())
        return {'success': True}
    except Exception as e:
        print(f"[NEWSLETTER] Blast failed for {to_email}: {e}")
        return {'success': False, 'error': str(e)}


def send_ebook_expiry_warning_email(to_email: str, child_name: str, days_remaining: int, renew_url: str, lang: str = 'es'):
    if not SMTP_USER or not SMTP_PASSWORD:
        return {'success': False}
    try:
        if lang == 'es':
            subject = f"📖 Tu eBook de {child_name} vence en {days_remaining} día{'s' if days_remaining != 1 else ''}"
            content = f"""
        <h2 style="color:#7c3aed;">¡Tu eBook vence pronto!</h2>
        <p style="color:#374151;font-size:15px;line-height:1.6;">
            Hola, tu acceso de regalo al eBook de <strong>{child_name}</strong> vence en 
            <strong style="color:#dc2626;">{days_remaining} día{'s' if days_remaining != 1 else ''}</strong>.
        </p>
        <p style="color:#374151;font-size:14px;line-height:1.6;margin-top:8px;">
            Para seguir disfrutando del cuento interactivo con música y narración, puedes comprar acceso permanente por solo <strong>$7 USD</strong>.
        </p>
        {_cta_button("✨ Comprar acceso permanente — $7", renew_url)}
        <p style="color:#6b7280;font-size:12px;">Si ya no te interesa, no hay problema. El link del cuento dejará de funcionar cuando expire.</p>
            """
        else:
            subject = f"📖 Your {child_name}'s eBook expires in {days_remaining} day{'s' if days_remaining != 1 else ''}"
            content = f"""
        <h2 style="color:#7c3aed;">Your eBook is expiring soon!</h2>
        <p style="color:#374151;font-size:15px;line-height:1.6;">
            Hello, your gift access to <strong>{child_name}</strong>'s eBook expires in 
            <strong style="color:#dc2626;">{days_remaining} day{'s' if days_remaining != 1 else ''}</strong>.
        </p>
        <p style="color:#374151;font-size:14px;line-height:1.6;margin-top:8px;">
            To keep enjoying the interactive storybook with music and narration, you can buy permanent access for just <strong>$7 USD</strong>.
        </p>
        {_cta_button("✨ Buy permanent access — $7", renew_url)}
        <p style="color:#6b7280;font-size:12px;">If you're not interested, no worries. The link will stop working when it expires.</p>
            """
        body_html = _email_wrapper("✨ Magic Memories Books ✨", content, to_email)
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{FROM_NAME} <{FROM_EMAIL}>"
        msg['To'] = to_email
        msg.attach(MIMEText(body_html, 'html', 'utf-8'))
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(FROM_EMAIL, to_email, msg.as_string())
        print(f"[EMAIL] Expiry warning sent to {to_email} ({days_remaining} days)")
        return {'success': True}
    except Exception as e:
        print(f"[EMAIL] Expiry warning failed: {e}")
        return {'success': False, 'error': str(e)}


def _classify_error(error_message: str, traceback_text: str = '') -> tuple:
    """Classify error as transient (API/network) or code bug. Returns (category, action_es)."""
    combined = (error_message + ' ' + traceback_text).lower()
    transient_keywords = [
        'timeout', 'timed out', 'timeouterror', 'connectionerror', 'connectionrefused',
        'rate limit', 'ratelimit', 'too many requests', '429', '503', '502', '504',
        'apiconnectionerror', 'connecttimeout', 'readtimeout', 'remotedisconnected',
        'connection reset', 'eof occurred', 'ssl', 'network unreachable', 'socket',
        'broken pipe', 'incomplete read', 'server disconnected', 'service unavailable',
        'bad gateway', 'gateway timeout', 'overloaded',
    ]
    code_bug_keywords = [
        'keyerror', 'attributeerror', 'filenotfounderror', 'typeerror', 'indexerror',
        'assertionerror', 'nameerror', 'importerror', 'syntaxerror', 'zerodivisionerror',
        'recursionerror', 'memoryerror', 'notimplementederror',
    ]
    for kw in transient_keywords:
        if kw in combined:
            return ('transient', '⚡ <strong>Probable fallo temporal de API.</strong> Usa el botón de admin para reintentar antes de intervenir.')
    for kw in code_bug_keywords:
        if kw in combined:
            return ('code_bug', '🐛 <strong>Error de código detectado.</strong> Requiere revisión en Replit — el cliente ya fue notificado y recibirá su libro en 24 h.')
    return ('unknown', '❓ <strong>Causa desconocida.</strong> Intenta el reinicio desde el panel de admin primero; si falla de nuevo, revisa el código en Replit.')


def send_admin_error_email(process_name: str, preview_id: str, error_message: str, traceback_text: str = '', story_data: dict = None, is_retry_failure: bool = False):
    if not SMTP_USER or not SMTP_PASSWORD:
        print(f"[ADMIN-ERROR] SMTP no configurado - error en {process_name} para {preview_id}: {error_message}")
        return {'success': False}
    try:
        base_url = os.environ.get('SITE_DOMAIN', 'magicmemoriesbooks.com')
        if not base_url.startswith('http'):
            base_url = f'https://{base_url}'

        error_category, action_html = _classify_error(error_message, traceback_text)

        urgency_label = '🔴 REINTENTO FALLIDO — ACCIÓN URGENTE' if is_retry_failure else '🟡 Primer fallo — revisar'
        urgency_color = '#dc2626' if is_retry_failure else '#d97706'

        client_section = ''
        if story_data:
            customer_name = story_data.get('customer_name') or story_data.get('child_name', 'Desconocido')
            customer_email = story_data.get('customer_email') or story_data.get('email', 'No disponible')
            child_name = story_data.get('child_name', '')
            story_id = story_data.get('story_id', '')
            story_name = story_data.get('story_name', '')
            book_type = 'FotoMágico' if story_data.get('is_illustrated_book') else 'Cuentos Express'
            product_desc = f'{book_type} — {story_name}' if story_name else book_type

            client_section = f"""
        <div style="background:#f0f9ff;border:1px solid #bae6fd;border-radius:10px;padding:16px;margin:16px 0;">
          <h3 style="margin:0 0 10px 0;color:#0369a1;font-size:15px;">👤 Datos del Cliente</h3>
          <table style="width:100%;border-collapse:collapse;">
            <tr><td style="padding:4px 8px;color:#6b7280;font-weight:bold;width:130px;">Cliente</td><td style="padding:4px 8px;color:#111827;">{customer_name}</td></tr>
            <tr style="background:#e0f2fe;"><td style="padding:4px 8px;color:#6b7280;font-weight:bold;">Email</td><td style="padding:4px 8px;"><a href="mailto:{customer_email}" style="color:#0369a1;">{customer_email}</a></td></tr>
            <tr><td style="padding:4px 8px;color:#6b7280;font-weight:bold;">Niño/a</td><td style="padding:4px 8px;color:#111827;">{child_name or '—'}</td></tr>
            <tr style="background:#e0f2fe;"><td style="padding:4px 8px;color:#6b7280;font-weight:bold;">Producto</td><td style="padding:4px 8px;color:#111827;">{product_desc}</td></tr>
          </table>
        </div>"""

        order_url = f'{base_url}/order-complete/{preview_id}'
        reset_url = f'{base_url}/admin/reset-compose/{preview_id}'

        content = f"""
        <div style="background:{urgency_color};color:#fff;padding:10px 16px;border-radius:8px;margin-bottom:16px;font-weight:bold;font-size:14px;">
            {urgency_label}
        </div>

        {client_section}

        <table style="width:100%;border-collapse:collapse;margin:12px 0;">
          <tr><td style="padding:6px;font-weight:bold;color:#6b7280;width:130px;">Proceso</td>
              <td style="padding:6px;color:#111827;font-family:monospace;font-size:12px;">{process_name}</td></tr>
          <tr style="background:#fef2f2;"><td style="padding:6px;font-weight:bold;color:#6b7280;">Preview ID</td>
              <td style="padding:6px;color:#111827;font-family:monospace;font-size:12px;">{preview_id}</td></tr>
          <tr><td style="padding:6px;font-weight:bold;color:#6b7280;">Error</td>
              <td style="padding:6px;color:#dc2626;font-size:13px;">{error_message}</td></tr>
        </table>

        <div style="background:#fef9c3;border:1px solid #fde047;border-radius:10px;padding:14px;margin:16px 0;">
          <p style="margin:0;font-size:14px;color:#713f12;">{action_html}</p>
        </div>

        <div style="display:flex;gap:12px;flex-wrap:wrap;margin:20px 0;">
          <a href="{order_url}" style="display:inline-block;background:#7c3aed;color:#fff;padding:10px 20px;border-radius:8px;text-decoration:none;font-weight:bold;font-size:13px;">
            Ver Pedido del Cliente
          </a>
          <a href="{reset_url}" style="display:inline-block;background:#059669;color:#fff;padding:10px 20px;border-radius:8px;text-decoration:none;font-weight:bold;font-size:13px;">
            Reiniciar Composición (Admin)
          </a>
        </div>
        """
        if traceback_text:
            content += f"""
        <details style="margin-top:16px;">
          <summary style="color:#374151;font-size:13px;font-weight:bold;cursor:pointer;">Ver Traceback completo</summary>
          <pre style="background:#f3f4f6;padding:12px;border-radius:6px;font-size:11px;overflow-x:auto;color:#374151;margin-top:8px;">{traceback_text}</pre>
        </details>
            """

        subject_prefix = '[MMB ERROR CRÍTICO]' if is_retry_failure else '[MMB ERROR]'
        body_html = _admin_wrapper(f"{'🔴' if is_retry_failure else '⚠️'} Error: {process_name}", content)

        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"{subject_prefix} {process_name} — {preview_id}"
        msg['From'] = f"{FROM_NAME} <{FROM_EMAIL}>"
        msg['To'] = FROM_EMAIL
        msg.attach(MIMEText(body_html, 'html', 'utf-8'))
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(FROM_EMAIL, FROM_EMAIL, msg.as_string())
        print(f"[ADMIN-ERROR] Email enviado para {process_name}/{preview_id}")
        return {'success': True}
    except Exception as e:
        print(f"[ADMIN-ERROR] No se pudo enviar email de error: {e}")
        return {'success': False, 'error': str(e)}


def send_admin_notification_email(subject: str, body: str) -> dict:
    """Send a plain text notification email to the admin."""
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{FROM_NAME} <{FROM_EMAIL}>"
        msg['To'] = FROM_EMAIL
        html = f"""<html><body style="font-family:sans-serif;padding:20px;">
            <pre style="background:#f3f4f6;padding:16px;border-radius:8px;white-space:pre-wrap;">{body}</pre>
        </body></html>"""
        msg.attach(MIMEText(html, 'html', 'utf-8'))
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(FROM_EMAIL, FROM_EMAIL, msg.as_string())
        return {'success': True}
    except Exception as e:
        print(f"[EMAIL] Admin notification error: {e}")
        return {'success': False, 'error': str(e)}


def send_tracking_email(to_email: str, tracking_number: str, customer_name: str, lang: str = 'es') -> dict:
    """Send tracking number email to customer for their printed book."""
    try:
        if lang == 'es':
            subject = "📦 Tu libro impreso está en camino"
            content = f"""
                <h2 style="color:#7c3aed;text-align:center;margin-top:0;">¡Tu libro está en camino!</h2>
                <p style="font-size:16px;color:#374151;text-align:center;">Hola {customer_name}, tu libro impreso personalizado ha sido enviado.</p>
                <div style="background:#f3e8ff;padding:20px;border-radius:12px;margin:20px 0;text-align:center;">
                    <p style="color:#6b7280;font-size:14px;margin:0 0 8px;">Número de seguimiento</p>
                    <p style="color:#7c3aed;font-size:24px;font-weight:bold;margin:0;letter-spacing:1px;">{tracking_number}</p>
                </div>
                <p style="color:#374151;font-size:14px;text-align:center;">Tiempo estimado de entrega: 5-15 días hábiles según tu ubicación.</p>
                <p style="color:#6b7280;font-size:12px;text-align:center;margin-top:20px;">¿Preguntas? <a href="mailto:pay@magicmemoriesbooks.com" style="color:#7c3aed;">pay@magicmemoriesbooks.com</a></p>
            """
        else:
            subject = "📦 Your printed book is on its way"
            content = f"""
                <h2 style="color:#7c3aed;text-align:center;margin-top:0;">Your book is on its way!</h2>
                <p style="font-size:16px;color:#374151;text-align:center;">Hello {customer_name}, your personalized printed book has been shipped.</p>
                <div style="background:#f3e8ff;padding:20px;border-radius:12px;margin:20px 0;text-align:center;">
                    <p style="color:#6b7280;font-size:14px;margin:0 0 8px;">Tracking number</p>
                    <p style="color:#7c3aed;font-size:24px;font-weight:bold;margin:0;letter-spacing:1px;">{tracking_number}</p>
                </div>
                <p style="color:#374151;font-size:14px;text-align:center;">Estimated delivery: 5-15 business days depending on your location.</p>
                <p style="color:#6b7280;font-size:12px;text-align:center;margin-top:20px;">Questions? <a href="mailto:pay@magicmemoriesbooks.com" style="color:#7c3aed;">pay@magicmemoriesbooks.com</a></p>
            """

        html_content = _email_wrapper("✨ Magic Memories Books ✨", content, to_email)

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{FROM_NAME} <{FROM_EMAIL}>"
        msg['To'] = to_email
        msg.attach(MIMEText(html_content, 'html', 'utf-8'))
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(FROM_EMAIL, [to_email], msg.as_string())
        print(f"[EMAIL] Tracking email sent to {to_email}")
        return {'success': True}
    except Exception as e:
        print(f"[EMAIL] Tracking email error: {e}")
        return {'success': False, 'error': str(e)}


def send_coupon_email(name: str, email: str, code: str = 'MAGIC15', discount_pct: int = 15, lang: str = 'es') -> bool:
    try:
        if lang == 'es':
            greeting = f"Hola <strong>{name}</strong>! 🎉"
            intro = f"Aquí está tu código exclusivo de <strong>{discount_pct}% de descuento</strong> para tu primer cuento mágico personalizado:"
            code_label = "Tu código"
            discount_label = f"{discount_pct}% de descuento"
            instructions = f"Introduce este código en el checkout <strong>antes de pagar con PayPal</strong>."
            cta_text = "✨ Crear mi cuento ahora ✨"
            footer_note = "Este código es válido para una compra. No lo compartas."
            email_title = "🎟️ Tu Código de Descuento"
            subject = f"🎟️ Tu {discount_pct}% de descuento — Magic Memories Books"
        else:
            greeting = f"Hi <strong>{name}</strong>! 🎉"
            intro = f"Here is your exclusive <strong>{discount_pct}% discount code</strong> for your first personalized magic story:"
            code_label = "Your code"
            discount_label = f"{discount_pct}% discount"
            instructions = f"Enter this code at checkout <strong>before paying with PayPal</strong>."
            cta_text = "✨ Create my story now ✨"
            footer_note = "This code is valid for one purchase. Do not share it."
            email_title = "🎟️ Your Discount Code"
            subject = f"🎟️ Your {discount_pct}% discount — Magic Memories Books"

        content = f"""
        <p style="font-size:16px;color:#374151;margin:0 0 14px 0;">{greeting}</p>
        <p style="font-size:15px;color:#374151;margin:0 0 20px 0;">
            {intro}
        </p>
        <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:20px 0;">
          <tr>
            <td align="center">
              <table cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td align="center" style="background-color:#B8860B;border-radius:10px;padding:18px 40px;">
                    <p style="margin:0 0 4px 0;font-size:11px;font-weight:700;color:#FFE88A;letter-spacing:1px;text-transform:uppercase;">{code_label}</p>
                    <p style="margin:0;font-size:32px;font-weight:900;color:#ffffff;letter-spacing:5px;font-family:Courier,monospace;">{code}</p>
                    <p style="margin:6px 0 0 0;font-size:13px;font-weight:700;color:#FFE88A;">{discount_label}</p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
        </table>
        <p style="font-size:14px;color:#6B7280;text-align:center;margin:0 0 24px 0;">
            {instructions}
        </p>
        {_cta_button(cta_text, "https://magicmemoriesbooks.com")}
        <p style="font-size:12px;color:#9CA3AF;text-align:center;margin:20px 0 0 0;">
            {footer_note}
        </p>
        """
        html_body = _email_wrapper(email_title, content, email)
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{FROM_NAME} <{FROM_EMAIL}>"
        msg['To'] = email
        msg.attach(MIMEText(html_body, 'html'))
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(FROM_EMAIL, email, msg.as_string())
        print(f"[COUPON EMAIL] Sent {code} to {email}")
        return True
    except Exception as e:
        print(f"[COUPON EMAIL] Error sending to {email}: {e}")
        return False


def send_cart_confirmation_email(to_email: str, items: list, total_usd: float, lang: str = 'es') -> dict:
    """Send a single confirmation email for a multi-item cart purchase."""
    if not to_email:
        return {'success': False, 'message': 'No email provided'}

    subject = (
        f"🛒 ¡Tu pedido de {len(items)} {'libro' if len(items)==1 else 'libros'} fue confirmado! — Magic Memories Books"
        if lang == 'es' else
        f"🛒 Your order of {len(items)} {'book' if len(items)==1 else 'books'} is confirmed! — Magic Memories Books"
    )

    product_type_labels = {
        'personalized_pdf': ('PDF Imprimible 🖨️', 'Printable PDF 🖨️'),
        'cp_personalized': ('Libro Impreso 📖', 'Printed Book 📖'),
        'qs_digital': ('PDF Digital 💻', 'Digital PDF 💻'),
        'qs_print': ('Libro Impreso 📦', 'Printed Book 📦'),
        'universo_ebook': ('eBook Interactivo 📱', 'Interactive eBook 📱'),
        'ebook': ('eBook Interactivo 📱', 'Interactive eBook 📱'),
        'personalized': ('Libro Personalizado 📖', 'Personalised Book 📖'),
    }

    rows_html = ''
    rows_text = ''
    access_links_html = ''
    access_links_text = ''
    for item in items:
        name = item.get('story_name') or item.get('child_name') or '—'
        child = item.get('child_name', '')
        pt = item.get('product_type', '')
        lbl_pair = product_type_labels.get(pt, (pt, pt))
        lbl = lbl_pair[0] if lang == 'es' else lbl_pair[1]
        price = item.get('price', 0)
        for_str = ('para' if lang == 'es' else 'for')
        rows_html += (
            f'<tr style="border-bottom:1px solid #e5e7eb;">'
            f'<td style="padding:10px 8px;font-weight:600;color:#374151;">{name} <span style="color:#6b7280;font-size:12px;">— {for_str} {child}</span></td>'
            f'<td style="padding:10px 8px;color:#7c3aed;white-space:nowrap;">{lbl}</td>'
            f'<td style="padding:10px 8px;text-align:right;font-weight:600;color:#374151;">${price:.2f}</td>'
            f'</tr>'
        )
        rows_text += f'  • {name} ({for_str} {child}): {lbl} — ${price:.2f}\n'
        visor_url = item.get('visor_url', '')
        pdf_url = item.get('pdf_download_url', '')
        tracking = item.get('tracking_number', '')
        lulu_submitted = item.get('lulu_submitted', False)
        item_links = []
        if visor_url:
            view_lbl = 'Ver eBook' if lang == 'es' else 'View eBook'
            item_links.append(f'<a href="{visor_url}" style="color:#7c3aed;text-decoration:underline;">📖 {view_lbl}</a>')
            access_links_text += f'    {view_lbl}: {visor_url}\n'
        if pdf_url:
            dl_lbl = 'Descargar PDF' if lang == 'es' else 'Download PDF'
            item_links.append(f'<a href="{pdf_url}" style="color:#7c3aed;text-decoration:underline;">⬇️ {dl_lbl}</a>')
            access_links_text += f'    {dl_lbl}: {pdf_url}\n'
        if tracking:
            tk_lbl = 'Seguimiento' if lang == 'es' else 'Tracking'
            item_links.append(f'<span style="color:#059669;">📦 {tk_lbl}: {tracking}</span>')
            access_links_text += f'    {tk_lbl}: {tracking}\n'
        elif lulu_submitted:
            pr_lbl = 'En producción — recibirás número de seguimiento por email' if lang == 'es' else 'In production — tracking number will be emailed'
            item_links.append(f'<span style="color:#d97706;">🔄 {pr_lbl}</span>')
            access_links_text += f'    {pr_lbl}\n'
        if item_links:
            access_links_html += (
                f'<div style="margin-bottom:10px;padding:8px 12px;background:#f5f3ff;border-left:3px solid #7c3aed;border-radius:0 6px 6px 0;">'
                f'<p style="margin:0 0 4px 0;font-weight:600;color:#374151;font-size:13px;">{name}</p>'
                f'<p style="margin:0;font-size:13px;">' + ' &nbsp;·&nbsp; '.join(item_links) + '</p>'
                f'</div>'
            )

    total_row = (
        f'<tr style="background:#f5f3ff;">'
        f'<td colspan="2" style="padding:12px 8px;font-weight:700;color:#374151;">Total</td>'
        f'<td style="padding:12px 8px;text-align:right;font-weight:700;color:#7c3aed;">${total_usd:.2f} USD</td>'
        f'</tr>'
    )

    table_html = f'''
        <table style="width:100%;border-collapse:collapse;border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;font-size:14px;">
            <thead>
                <tr style="background:#7c3aed;color:white;">
                    <th style="padding:10px 8px;text-align:left;">{"Libro" if lang=="es" else "Book"}</th>
                    <th style="padding:10px 8px;text-align:left;">{"Formato" if lang=="es" else "Format"}</th>
                    <th style="padding:10px 8px;text-align:right;">{"Precio" if lang=="es" else "Price"}</th>
                </tr>
            </thead>
            <tbody>{rows_html}</tbody>
            <tfoot>{total_row}</tfoot>
        </table>
    '''

    if lang == 'es':
        intro = f"<p style='font-size:16px;color:#374151;text-align:center;'>¡Hemos recibido tu pedido de <strong>{len(items)}</strong> {'libro' if len(items)==1 else 'libros'}! Estamos procesando todo ahora mismo.</p>"
        next_steps = _success_box('''
            <h4 style="margin-top:0;color:#166534;">📬 Próximos pasos</h4>
            <ul style="color:#374151;font-size:13px;margin:0;padding-left:1em;">
                <li>Los libros digitales y PDFs llegarán a tu email en los próximos minutos.</li>
                <li>Los libros impresos se enviarán en 10–20 días hábiles.</li>
                <li>Guarda este email como referencia de tu pedido.</li>
            </ul>
        ''')
        thanks = "¡Gracias por crear recuerdos mágicos! 💜"
    else:
        intro = f"<p style='font-size:16px;color:#374151;text-align:center;'>We've received your order of <strong>{len(items)}</strong> {'book' if len(items)==1 else 'books'}! We're processing everything right now.</p>"
        next_steps = _success_box('''
            <h4 style="margin-top:0;color:#166534;">📬 Next steps</h4>
            <ul style="color:#374151;font-size:13px;margin:0;padding-left:1em;">
                <li>Digital books and PDFs will arrive in your email within minutes.</li>
                <li>Printed books will ship within 10–20 business days.</li>
                <li>Save this email as your order reference.</li>
            </ul>
        ''')
        thanks = "Thank you for creating magical memories! 💜"

    access_section = ''
    if access_links_html:
        access_heading = '🔑 Accede a tus libros' if lang == 'es' else '🔑 Access your books'
        access_section = f'''
            <div style="margin-top:20px;">
                <h3 style="color:#374151;font-size:15px;margin-bottom:12px;">{access_heading}</h3>
                {access_links_html}
            </div>
        '''
    access_text_section = ''
    if access_links_text:
        access_heading_txt = 'Accede a tus libros:' if lang == 'es' else 'Access your books:'
        access_text_section = f"\n{access_heading_txt}\n{access_links_text}\n"

    content_inner = f"""
        <h2 style="color:#7c3aed;text-align:center;margin-top:0;">{"¡Pedido Confirmado!" if lang=="es" else "Order Confirmed!"} 🎉</h2>
        {intro}
        {table_html}
        {access_section}
        {next_steps}
        {_newsletter_invite_html(lang)}
        <p style="color:#7c3aed;font-weight:bold;text-align:center;">{thanks}</p>
    """

    html_body = _email_wrapper("✨ Magic Memories Books ✨", content_inner, to_email)
    text_body = (
        f"{'¡Pedido Confirmado!' if lang=='es' else 'Order Confirmed!'}\n\n"
        f"{'Tus libros:' if lang=='es' else 'Your books:'}\n{rows_text}\n"
        f"Total: ${total_usd:.2f} USD\n{access_text_section}\n{thanks}\nMagic Memories Books"
    )

    if not SMTP_USER or not SMTP_PASSWORD:
        print(f"[CART EMAIL] SMTP not configured. Would send to {to_email}: {subject}")
        return {'success': True, 'message': 'Logged (SMTP not configured)', 'simulated': True}

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{FROM_NAME} <{FROM_EMAIL}>"
        msg['To'] = to_email
        msg.attach(MIMEText(text_body, 'plain', 'utf-8'))
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        print(f"[CART EMAIL] Sent cart confirmation to {to_email} ({len(items)} items)")
        return {'success': True, 'message': 'Cart confirmation sent'}
    except Exception as e:
        print(f"[CART EMAIL] Error: {e}")
        return {'success': False, 'message': str(e)}


def send_personalized_pdf_customer_email(
    to_email: str,
    child_name: str,
    book_title: str,
    pdf_url: str,
    visor_url: str = '',
    lang: str = 'es',
) -> dict:
    """
    Send the delivery email for a personalized_pdf purchase ($30 home-print PDF).
    Delivers a download link (not an attachment) plus clear print instructions.
    """

    if lang == 'es':
        subject = f"🎉 ¡Tu libro imprimible para {child_name} está listo!"
        greeting = f"¡Hola! Tu cuento personalizado <strong>«{book_title}»</strong> para <strong>{child_name}</strong> está listo para descargar e imprimir."
        dl_title = "📄 Descargar tu PDF imprimible"
        dl_btn   = "Descargar PDF (31 páginas A4)"
        dl_note  = ("El archivo puede tardar unos segundos en abrir. "
                    "Guárdalo en tu dispositivo antes de llevarlo a imprimir.")
        steps_title = "🖨️ Cómo imprimirlo"
        steps = [
            "<strong>Imprime en A4</strong> — cualquier papelería o copy shop.",
            "Selecciona <strong>impresión a color, doble cara</strong> (flip on long edge).",
            "Para mejor calidad: papel satinado 120–170 g/m².",
            "Encuadernado a tu gusto: espiral, grapa tipo revista o rústica pegada.",
        ]
        ebook_title = ""
        ebook_body  = ""
        ebook_btn   = ""
        alert_text  = "¿Problemas para abrir el PDF o necesitas ayuda con la impresión? Escríbenos a <strong>pay@magicmemoriesbooks.com</strong>."
        thanks_text = "¡Gracias por confiar en Magic Memories Books! 💜"
    else:
        subject = f"🎉 Your printable book for {child_name} is ready!"
        greeting = f"Hello! Your personalized story <strong>«{book_title}»</strong> for <strong>{child_name}</strong> is ready to download and print."
        dl_title = "📄 Download your printable PDF"
        dl_btn   = "Download PDF (31 A4 pages)"
        dl_note  = ("The file may take a few seconds to open. "
                    "Save it to your device before taking it to print.")
        steps_title = "🖨️ How to print it"
        steps = [
            "<strong>Print on A4</strong> — any copy shop or print shop.",
            "Select <strong>colour printing, double-sided</strong> (flip on long edge).",
            "For best quality: coated paper 120–170 gsm.",
            "Bind as you prefer: spiral, saddle-stitch, or perfect binding.",
        ]
        ebook_title = ""
        ebook_body  = ""
        ebook_btn   = ""
        alert_text  = "Problems opening the PDF or need help printing? Email us at <strong>pay@magicmemoriesbooks.com</strong>."
        thanks_text = "Thank you for trusting Magic Memories Books! 💜"

    steps_html = "".join(
        f'<li style="padding:6px 0;font-size:14px;color:#374151;">{s}</li>'
        for s in steps
    )

    visor_section = ""
    if visor_url:
        visor_section = f"""
        <h3 style="color:#9333ea;font-size:16px;margin:24px 0 8px;">{ebook_title}</h3>
        <p style="color:#374151;font-size:14px;margin:0 0 12px;">{ebook_body}</p>
        {_cta_button(ebook_btn, visor_url)}
        """

    content = f"""
        <p style="color:#374151;font-size:15px;line-height:1.6;">{greeting}</p>

        <h3 style="color:#9333ea;font-size:16px;margin:24px 0 10px;">{dl_title}</h3>
        <div style="background:#f3e8ff;padding:20px;border-radius:12px;border-left:4px solid #9333ea;margin:10px 0 20px;">
            <div style="text-align:center;margin-bottom:12px;">
                <a href="{pdf_url}" style="display:inline-block;background:linear-gradient(135deg,#9333ea,#ec4899);color:#fff;padding:14px 32px;border-radius:25px;text-decoration:none;font-weight:bold;font-size:16px;">{dl_btn}</a>
            </div>
            <p style="margin:0;color:#6b7280;font-size:12px;text-align:center;">{dl_note}</p>
        </div>

        <h3 style="color:#9333ea;font-size:16px;margin:24px 0 10px;">{steps_title}</h3>
        <ol style="margin:0 0 20px;padding-left:20px;">{steps_html}</ol>

        {_alert_box(f'<p style="margin:0;font-size:13px;color:#92400e;">{alert_text}</p>')}

        {visor_section}

        <p style="color:#7c3aed;font-weight:bold;text-align:center;margin-top:24px;">{thanks_text}</p>
    """

    html_body = _email_wrapper("✨ Magic Memories Books ✨", content, to_email)
    text_body = (
        f"{'¡Tu libro imprimible está listo!' if lang == 'es' else 'Your printable book is ready!'}\n\n"
        f"{book_title} — {child_name}\n\n"
        f"Descargar PDF: {pdf_url}\n"
        f"{'eBook:' if lang == 'es' else 'eBook:'} {visor_url or 'N/A'}\n\n"
        f"Magic Memories Books\n"
        f"pay@magicmemoriesbooks.com\n"
        f"www.magicmemoriesbooks.com\n"
    )

    if not SMTP_USER or not SMTP_PASSWORD:
        print(f"[PDF EMAIL] SMTP not configured. Would send to: {to_email}")
        return {'success': True, 'message': 'PDF email logged (SMTP not configured)', 'simulated': True}

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{FROM_NAME} <{FROM_EMAIL}>"
        msg['To'] = to_email
        msg.attach(MIMEText(text_body, 'plain', 'utf-8'))
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        print(f"[PDF EMAIL] Customer email sent to {to_email}")
        return {'success': True, 'message': 'Customer PDF email sent'}
    except Exception as e:
        print(f"[PDF EMAIL] Error sending to {to_email}: {e}")
        return {'success': False, 'message': str(e)}


def send_personalized_pdf_admin_email(
    preview_id: str,
    customer_email: str,
    book_title: str,
    pdf_url: str,
    visor_url: str = '',
    child_name: str = '',
    book_id: str = '',
    customer_email_sent: bool = True,
) -> dict:
    """
    Send admin notification to pay@ when a personalized_pdf order is delivered.
    """
    from datetime import datetime
    admin_email = "pay@magicmemoriesbooks.com"
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    subject = f"🖨️ PDF Imprimible entregado - {book_title} - {preview_id}"

    def _row(label, value, alt_bg=False):
        bg = 'background:#f3e8ff;' if alt_bg else ''
        return (
            f'<tr style="{bg}">'
            f'<td style="padding:10px 12px;color:#6b7280;font-size:13px;width:140px;">{label}</td>'
            f'<td style="padding:10px 12px;color:#1f2937;font-size:14px;font-weight:600;">{value}</td>'
            f'</tr>'
        )

    pdf_link   = f'<a href="{pdf_url}" style="color:#9333ea;font-weight:600;">📄 Descargar PDF imprimible</a>'
    visor_link = (f'<br><a href="{visor_url}" style="color:#9333ea;font-weight:600;">📖 Ver eBook en visor</a>'
                  if visor_url else '')

    content = f"""
        <table style="width:100%;border-collapse:collapse;font-size:14px;margin-bottom:15px;">
            {_row('Preview ID', preview_id, True)}
            {_row('Título', book_title)}
            {_row('Nombre niño/a', child_name or 'N/A', True)}
            {_row('Book ID', book_id or 'N/A')}
            {_row('Cliente', customer_email, True)}
            {_row('Fecha', timestamp)}
        </table>

        <h3 style="color:#9333ea;margin-top:20px;font-size:16px;">📎 Archivos PDF</h3>
        <div style="background:#f3e8ff;padding:15px;border-radius:8px;border-left:4px solid #9333ea;margin:10px 0;">
            <p style="margin:0;">{pdf_link}{visor_link}</p>
            <p style="color:#6b7280;font-size:12px;margin-top:8px;">(Enlace de descarga directo — PDF entregado al cliente por email)</p>
        </div>

        <h3 style="color:#16a34a;margin-top:20px;font-size:16px;">✅ Estado</h3>
        <div style="background:#f0fdf4;padding:15px;border-radius:8px;border-left:4px solid #16a34a;margin:10px 0;">
            <p style="margin:0;font-size:14px;color:#1f2937;">PDF generado (31 páginas A4) correctamente.</p>
            <p style="margin:6px 0 0;font-size:14px;color:{'#16a34a' if customer_email_sent else '#dc2626'};">
                {'✅ Email al cliente enviado.' if customer_email_sent else '⚠️ Email al cliente NO enviado — verificar SMTP o dirección.'}
            </p>
            <p style="margin:6px 0 0;font-size:12px;color:#6b7280;">Producto: PDF Imprimible $30 · Entrega digital · Sin envío físico</p>
        </div>
    """

    html_body = _admin_wrapper("🖨️ PDF Imprimible Entregado", content)
    text_body = (
        f"PDF IMPRIMIBLE ENTREGADO\n"
        f"========================\n\n"
        f"Preview ID : {preview_id}\n"
        f"Título     : {book_title}\n"
        f"Nombre     : {child_name or 'N/A'}\n"
        f"Book ID    : {book_id or 'N/A'}\n"
        f"Cliente    : {customer_email}\n"
        f"Fecha      : {timestamp}\n\n"
        f"PDF URL    : {pdf_url}\n"
        f"eBook URL  : {visor_url or 'N/A'}\n"
    )

    if not SMTP_USER or not SMTP_PASSWORD:
        print(f"[PDF ADMIN] SMTP not configured. Would send to: {admin_email}")
        return {'success': True, 'message': 'Admin PDF email logged (SMTP not configured)', 'simulated': True}

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{FROM_NAME} <{FROM_EMAIL}>"
        msg['To'] = admin_email
        msg.attach(MIMEText(text_body, 'plain', 'utf-8'))
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        print(f"[PDF ADMIN] Admin email sent to {admin_email} for {preview_id}")
        return {'success': True, 'message': 'Admin PDF email sent'}
    except Exception as e:
        print(f"[PDF ADMIN] Error: {e}")
        return {'success': False, 'message': str(e)}


def send_print_order_confirmation_email(
    to_email: str,
    story_data: dict,
    preview_id: str = '',
) -> dict:
    """Send a dedicated 'libro en imprenta' email when the customer bought Print+eBook.
    This is separate from the eBook email so each product gets its own clear confirmation."""
    try:
        child_name = story_data.get('child_name', 'tu pequeño')
        story_name = story_data.get('story_name', 'tu cuento')
        lang = story_data.get('lang', 'es')
        cp_ref = story_data.get('cp_pb_order_ref', '') or story_data.get('cp_order_ref', '')

        if lang == 'es':
            subject = f"📦 Tu libro impreso '{story_name}' está en producción"
            h1 = f"¡Tu libro está en camino, {child_name}!"
            body_p1 = (
                f"Hemos recibido tu pedido del libro impreso <strong>\"{story_name}\"</strong> "
                f"y ya está en manos de nuestra imprenta. Lo fabricarán con la más alta calidad "
                f"especialmente para ti."
            )
            timeline_title = "⏱️ Tiempo estimado"
            timeline_body = "Tu libro tardará aproximadamente <strong>7–14 días hábiles</strong> en llegar una vez fabricado. Cuando salga en reparto te enviaremos el número de seguimiento."
            ref_label = "Referencia de pedido"
            contact_msg = "¿Tienes alguna duda? Escríbenos a <strong>pay@magicmemoriesbooks.com</strong> indicando tu referencia de pedido."
            thanks_msg = "¡Gracias por tu confianza!"
        else:
            subject = f"📦 Your printed book '{story_name}' is in production"
            h1 = f"Your book is on its way, {child_name}!"
            body_p1 = (
                f"We've received your order for the printed book <strong>\"{story_name}\"</strong> "
                f"and it's now with our printer. It will be manufactured with premium quality "
                f"finish specially for you."
            )
            timeline_title = "⏱️ Estimated time"
            timeline_body = "Your book will take approximately <strong>7–14 business days</strong> to arrive once manufactured. When it ships, we'll send you the tracking number."
            ref_label = "Order reference"
            contact_msg = "Questions? Email us at <strong>pay@magicmemoriesbooks.com</strong> with your order reference."
            thanks_msg = "Thank you for your trust!"

        ref_row = (
            f'<p style="color:#6b7280;font-size:13px;margin:8px 0 0 0;">'
            f'{ref_label}: <strong style="color:#374151;">{cp_ref}</strong></p>'
        ) if cp_ref else ''

        base_url_print = os.environ.get('REPLIT_DEV_DOMAIN', '')
        if base_url_print:
            base_url_print = f"https://{base_url_print}"
        else:
            base_url_print = os.environ.get('PUBLIC_URL', 'https://magicmemoriesbooks.com')

        tracking_btn = ''
        if preview_id:
            track_url = f"{base_url_print}/track-order/{preview_id}"
            tracking_btn = _cta_button(
                "📍 Ver estado de mi pedido" if lang == 'es' else "📍 Track my order",
                track_url
            )

        content = f"""
            <h2 style="color:#166534;text-align:center;margin-top:0;">{h1}</h2>
            <p style="font-size:16px;color:#374151;text-align:center;">{body_p1}</p>

            <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:12px;padding:20px;margin:20px 0;">
                <h4 style="margin-top:0;color:#166534;">{timeline_title}</h4>
                <p style="color:#374151;font-size:14px;margin:0;">{timeline_body}</p>
                {ref_row}
            </div>

            {tracking_btn}

            <p style="color:#6b7280;font-size:13px;text-align:center;">{contact_msg}</p>
            <p style="color:#7c3aed;font-weight:bold;text-align:center;font-size:16px;">{thanks_msg} 💜</p>
        """
        html_content = _email_wrapper("✨ Magic Memories Books ✨", content, to_email)

        if lang == 'es':
            text_body = f"{h1}\n\n{story_name} está en producción.\n\n{timeline_body}\n\n{contact_msg}\n\n{thanks_msg}\nMagic Memories Books"
        else:
            text_body = f"{h1}\n\n{story_name} is in production.\n\n{timeline_body}\n\n{contact_msg}\n\n{thanks_msg}\nMagic Memories Books"

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f'{FROM_NAME} <{FROM_EMAIL}>'
        msg['To'] = to_email
        msg.attach(MIMEText(text_body, 'plain'))
        msg.attach(MIMEText(html_content, 'html'))

        if not SMTP_USER or not SMTP_PASSWORD:
            print(f"[EMAIL] SMTP not configured. Would send print order email to: {to_email}")
            return {'success': True, 'message': 'Email logged (SMTP not configured)'}

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(FROM_EMAIL, to_email, msg.as_string())

        print(f"[EMAIL] Print order confirmation sent to {to_email} (ref={cp_ref})")
        return {'success': True, 'message': f'Print order email sent to {to_email}'}

    except Exception as e:
        print(f"[EMAIL] Failed to send print order email: {e}")
        return {'success': False, 'error': str(e)}


def send_cp_pb_admin_notification(
    preview_id: str,
    cp_order_ref: str,
    title: str,
    customer_email: str,
    shipping_address: dict,
    cover_pdf_url: str = '',
    content_pdf_url: str = '',
    visor_url: str = '',
    paid_amount: str = '',
    cp_cost_eur: float = 0,
    print_cost_eur: float = 0,
) -> dict:
    """Send admin email to pay@ when a CP casewrap PB order is submitted."""
    from datetime import datetime

    admin_email = "pay@magicmemoriesbooks.com"

    address_name    = shipping_address.get('name', 'N/A')
    address_street  = shipping_address.get('street1', 'N/A')
    address_city    = shipping_address.get('city', 'N/A')
    address_state   = shipping_address.get('state_code', 'N/A')
    address_country = shipping_address.get('country_code', 'N/A')
    address_postal  = shipping_address.get('postcode', 'N/A')

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    subject = f"📦 Nuevo pedido CP Casewrap - {title} - {preview_id}"

    def _row(label, value, alt_bg=False):
        bg = 'background:#f0fdf4;' if alt_bg else ''
        return f'<tr style="{bg}"><td style="padding:10px 12px;color:#6b7280;font-size:13px;width:140px;">{label}</td><td style="padding:10px 12px;color:#1f2937;font-size:14px;font-weight:600;">{value}</td></tr>'

    cover_link   = f'<a href="{cover_pdf_url}" style="color:#16a34a;font-weight:600;">📄 Descargar cover.pdf</a><br>' if cover_pdf_url else ''
    content_link = f'<a href="{content_pdf_url}" style="color:#16a34a;font-weight:600;">📄 Descargar content.pdf</a><br>' if content_pdf_url else ''
    visor_link   = f'<a href="{visor_url}" style="color:#16a34a;font-weight:600;">📖 Ver cuento en el visor</a>' if visor_url else ''

    paid_row = _row('Precio Pagado', paid_amount, True) if paid_amount else ''
    cost_row = ''
    if cp_cost_eur or print_cost_eur:
        from services.cloudprinter_api_service import get_eur_usd_rate as _get_rate
        _rate = _get_rate()
        total_cp_eur = cp_cost_eur + print_cost_eur
        total_cp_usd = round(total_cp_eur * _rate, 2)
        print_usd = round(print_cost_eur * _rate, 2)
        ship_usd  = round(cp_cost_eur * _rate, 2)
        cost_row = f'<tr style="background:#fff7ed;"><td style="padding:10px 12px;color:#6b7280;font-size:13px;width:140px;">💶 Nuestro coste CP<br><span style="font-size:11px;color:#9ca3af;">(lo que pagamos a Cloudprinter)</span></td><td style="padding:10px 12px;color:#ea580c;font-size:14px;font-weight:700;">${total_cp_usd:.2f} USD&nbsp;&nbsp;<span style="font-size:12px;color:#6b7280;">(producción ${print_usd:.2f} + envío ${ship_usd:.2f}) · €{total_cp_eur:.2f} EUR × {_rate:.4f}</span></td></tr>'
    content = f"""
        <table style="width:100%;border-collapse:collapse;font-size:14px;margin-bottom:15px;">
            {_row('Preview ID', preview_id, True)}
            {_row('CP Order Ref', cp_order_ref)}
            {_row('Producto', 'photobook_cw_a4_p_fc — 26p HC', True)}
            {_row('Título', title)}
            {_row('Cliente', customer_email, True)}
            {paid_row}
            {cost_row}
            {_row('Fecha', timestamp)}
        </table>

        <h3 style="color:#16a34a;margin-top:20px;font-size:16px;">📍 Dirección de Envío</h3>
        <div style="background:#f0fdf4;padding:15px;border-radius:8px;border-left:4px solid #16a34a;margin:10px 0;">
            <p style="margin:0;color:#1f2937;font-size:14px;">
                <strong>{address_name}</strong><br>
                {address_street}<br>
                {address_city}, {address_state} {address_postal}<br>
                {address_country}
            </p>
        </div>

        <h3 style="color:#16a34a;margin-top:20px;font-size:16px;">📎 Archivos PDF</h3>
        <div style="background:#f0fdf4;padding:15px;border-radius:8px;border-left:4px solid #16a34a;margin:10px 0;">
            <p style="margin:0;">{cover_link}{content_link}{visor_link}</p>
        </div>

        <h3 style="color:#16a34a;margin-top:20px;font-size:16px;">🖨️ Ver pedido en Cloudprinter</h3>
        <div style="background:#f0fdf4;padding:15px;border-radius:8px;border-left:4px solid #16a34a;margin:10px 0;">
            <a href="https://app.cloudprinter.com/orders" style="display:inline-block;background:#16a34a;color:#fff;padding:10px 20px;border-radius:8px;text-decoration:none;font-weight:600;font-size:14px;">🖨️ Ver pedidos en Cloudprinter</a>
            <p style="margin:10px 0 0;color:#6b7280;font-size:12px;">Ref a buscar: <strong>{cp_order_ref}</strong></p>
        </div>
    """

    html_body = _admin_wrapper("📦 Nuevo Pedido CP Casewrap", content)

    text_body = f"""
NUEVO PEDIDO CLOUDPRINTER CASEWRAP
===================================

Preview ID: {preview_id}
CP Order Ref: {cp_order_ref}
Producto: photobook_cw_a4_p_fc — 26 páginas tapa dura
Título: {title}
Cliente: {customer_email}
Fecha: {timestamp}

DIRECCIÓN DE ENVÍO:
{address_name}
{address_street}
{address_city}, {address_state} {address_postal}
{address_country}

ARCHIVOS PDF:
Cover: {cover_pdf_url or 'N/A'}
Content: {content_pdf_url or 'N/A'}
Visor: {visor_url or 'N/A'}

Ver pedido: https://app.cloudprinter.com/orders
    """

    if not SMTP_USER or not SMTP_PASSWORD:
        print(f"[CP PB ADMIN] SMTP not configured. Would send to: {admin_email}")
        return {'success': True, 'message': 'CP PB admin notification logged (SMTP not configured)', 'simulated': True}

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{FROM_NAME} <{FROM_EMAIL}>"
        msg['To'] = admin_email
        msg.attach(MIMEText(text_body, 'plain', 'utf-8'))
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        print(f"[CP PB ADMIN] Email sent to {admin_email} for {preview_id}")
        return {'success': True, 'message': 'CP PB admin notification sent'}
    except Exception as e:
        print(f"[CP PB ADMIN] Error: {e}")
        return {'success': False, 'message': str(e)}


# ---------------------------------------------------------------------------
# Lead follow-up email sequence
# ---------------------------------------------------------------------------

import json as _json

FOLLOW_UPS_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'lead_follow_ups.json')


def register_purchase_for_follow_up(preview_id: str, email: str, child_name: str, lang: str = 'es'):
    """Record a real purchase so the 24h follow-up email can be scheduled."""
    if not email or '@' not in email:
        return
    try:
        os.makedirs(os.path.dirname(FOLLOW_UPS_FILE), exist_ok=True)
        data = {}
        if os.path.exists(FOLLOW_UPS_FILE):
            with open(FOLLOW_UPS_FILE, 'r', encoding='utf-8') as f:
                data = _json.load(f)
        if preview_id in data and data[preview_id].get('email_1_sent'):
            return
        data[preview_id] = {
            'email': email,
            'child_name': child_name or '',
            'lang': lang or 'es',
            'purchased_at': __import__('datetime').datetime.now().isoformat(),
            'email_1_sent': False,
        }
        with open(FOLLOW_UPS_FILE, 'w', encoding='utf-8') as f:
            _json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[LEAD] Registered 24h follow-up for {email} (preview: {preview_id})")
    except Exception as e:
        print(f"[LEAD] Error registering follow-up: {e}")


def send_feedback_email_24h(to_email: str, child_name: str = '', lang: str = 'es') -> bool:
    """Send the 24h post-purchase feedback / thank-you email from Isabel."""
    if lang == 'es':
        subject = "Tu cuento de ayer - Magic Memories Books"
        content = """
        <p style="font-size:16px;color:#374151;line-height:1.8;margin-top:0;">Hola,</p>
        <p style="font-size:16px;color:#374151;line-height:1.8;">
            Ayer creaste un cuento personalizado en Magic Memories Books y
            quer&iacute;amos darte las gracias por probar nuestra plataforma.
        </p>
        <p style="font-size:16px;color:#374151;line-height:1.8;">
            Estamos empezando y cada opini&oacute;n cuenta much&iacute;simo para nosotros.
        </p>
        <p style="font-size:18px;color:#7c3aed;font-weight:bold;line-height:1.8;">
            &iquest;Te gust&oacute; el resultado?<br>
            &iquest;D&oacute;nde nos conociste?
        </p>
        <p style="font-size:16px;color:#374151;line-height:1.8;">
            Si tienes un minuto, simplemente responde a este correo y
            cu&eacute;ntanos qu&eacute; te pareci&oacute; la experiencia.
        </p>
        <p style="font-size:16px;color:#374151;line-height:1.8;">
            Nos encantar&aacute; leer tu opini&oacute;n y seguir mejorando
            para las familias que conf&iacute;an en nosotros.
        </p>
        <p style="font-size:16px;color:#374151;line-height:1.8;margin-bottom:0;">Muchas gracias,</p>"""
    else:
        subject = "Your story from yesterday - Magic Memories Books"
        content = """
        <p style="font-size:16px;color:#374151;line-height:1.8;margin-top:0;">Hello,</p>
        <p style="font-size:16px;color:#374151;line-height:1.8;">
            Yesterday you created a personalized story on Magic Memories Books and
            we wanted to thank you for trying our platform.
        </p>
        <p style="font-size:16px;color:#374151;line-height:1.8;">
            We&#39;re just getting started and every opinion matters enormously to us.
        </p>
        <p style="font-size:18px;color:#7c3aed;font-weight:bold;line-height:1.8;">
            Did you like the result?<br>
            Where did you hear about us?
        </p>
        <p style="font-size:16px;color:#374151;line-height:1.8;">
            If you have a minute, just reply to this email and
            tell us what you thought of the experience.
        </p>
        <p style="font-size:16px;color:#374151;line-height:1.8;">
            We&#39;d love to read your feedback and keep improving
            for the families who trust us.
        </p>
        <p style="font-size:16px;color:#374151;line-height:1.8;margin-bottom:0;">Thank you so much,</p>"""

    html_body = _email_wrapper("Magic Memories Books", content, to_email)

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = f"{FROM_NAME} <{FROM_EMAIL}>"
    msg['To'] = to_email
    msg['Reply-To'] = FROM_EMAIL
    msg.attach(MIMEText(html_body, 'html', 'utf-8'))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(FROM_EMAIL, to_email, msg.as_string())
        print(f"[LEAD] 24h feedback email sent to {to_email}")
        log_email('feedback_24h', to_email, subject, 'SENT', child_name=child_name, lang=lang)
        return True
    except Exception as e:
        print(f"[LEAD] Failed to send 24h feedback email to {to_email}: {e}")
        log_email('feedback_24h', to_email, subject, 'ERROR', child_name=child_name, lang=lang, error=str(e))
        return False


def send_upsell_print_email(preview_id: str, to_email: str, child_name: str = '', lang: str = 'es') -> bool:
    """Send the 48h post-purchase upsell email offering PDF + printed book formats."""
    formats_url = f"https://magicmemoriesbooks.com/formats/{preview_id}"
    name_str = child_name.strip() if child_name.strip() else ''

    if lang == 'es':
        subject = f"El cuento de {name_str} — ¿quieres tenerlo en papel?" if name_str else "Tu cuento de Magic Memories Books — ¿quieres tenerlo en papel?"
        btn_label = "Ver opciones para mi cuento"
        if name_str:
            intro_line = f"Hace d&iacute;as creaste el cuento de <strong>{name_str}</strong> en Magic Memories Books y saber que qued&oacute; muy bonito nos llena de alegr&iacute;a."
        else:
            intro_line = "Hace d&iacute;as creaste un cuento personalizado en Magic Memories Books y saber que qued&oacute; muy bonito nos llena de alegr&iacute;a."
        content = f"""
        <p style="font-size:16px;color:#374151;line-height:1.8;margin-top:0;">Hola,</p>
        <p style="font-size:16px;color:#374151;line-height:1.8;">
            {intro_line}
        </p>
        <p style="font-size:16px;color:#374151;line-height:1.8;">
            Quer&iacute;a contarte que puedes tener el cuento tambi&eacute;n en formato f&iacute;sico —
            ya sea como <strong>PDF imprimible</strong> para imprimir en casa o en cualquier copister&iacute;a,
            o como un <strong>libro impreso de verdad</strong>, con tapa dura, que puedas sostener en tus manos
            y regalar.
        </p>
        <p style="font-size:16px;color:#374151;line-height:1.8;">
            El cuento ya est&aacute; generado, as&iacute; que no hay espera. Solo elige el formato
            que prefieras y nosotros nos encargamos del resto.
        </p>
        <table role="presentation" cellspacing="0" cellpadding="0" border="0" align="center" style="margin:32px auto;">
            <tr>
                <td align="center" bgcolor="#7c3aed" style="border-radius:12px;background-color:#7c3aed;">
                    <a href="{formats_url}" target="_blank"
                       style="display:inline-block;padding:14px 32px;font-family:sans-serif;font-size:16px;
                              font-weight:bold;color:#ffffff;text-decoration:none;border-radius:12px;
                              mso-padding-alt:14px 32px;">
                        {btn_label} &#8594;
                    </a>
                </td>
            </tr>
        </table>
        <p style="font-size:16px;color:#374151;line-height:1.8;margin-bottom:0;">Un abrazo,</p>"""
    else:
        subject = f"{name_str}'s story — would you like it in print?" if name_str else "Your Magic Memories Books story — would you like it in print?"
        btn_label = "See options for my story"
        if name_str:
            intro_line = f"A few days ago you created <strong>{name_str}</strong>&#39;s story on Magic Memories Books and knowing it turned out beautifully fills us with joy."
        else:
            intro_line = "A few days ago you created a personalized story on Magic Memories Books and knowing it turned out beautifully fills us with joy."
        content = f"""
        <p style="font-size:16px;color:#374151;line-height:1.8;margin-top:0;">Hello,</p>
        <p style="font-size:16px;color:#374151;line-height:1.8;">
            {intro_line}
        </p>
        <p style="font-size:16px;color:#374151;line-height:1.8;">
            I wanted to let you know that you can also have the story in a physical format —
            either as a <strong>printable PDF</strong> to print at home or at any copy shop,
            or as a <strong>real printed book</strong>, hardcover, that you can hold in your hands
            and give as a gift.
        </p>
        <p style="font-size:16px;color:#374151;line-height:1.8;">
            The story is already generated, so there&#39;s no wait. Just choose the format
            you prefer and we&#39;ll take care of the rest.
        </p>
        <table role="presentation" cellspacing="0" cellpadding="0" border="0" align="center" style="margin:32px auto;">
            <tr>
                <td align="center" bgcolor="#7c3aed" style="border-radius:12px;background-color:#7c3aed;">
                    <a href="{formats_url}" target="_blank"
                       style="display:inline-block;padding:14px 32px;font-family:sans-serif;font-size:16px;
                              font-weight:bold;color:#ffffff;text-decoration:none;border-radius:12px;
                              mso-padding-alt:14px 32px;">
                        {btn_label} &#8594;
                    </a>
                </td>
            </tr>
        </table>
        <p style="font-size:16px;color:#374151;line-height:1.8;margin-bottom:0;">Warm regards,</p>"""

    html_body = _email_wrapper("Magic Memories Books", content, to_email)

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = f"{FROM_NAME} <{FROM_EMAIL}>"
    msg['To'] = to_email
    msg['Reply-To'] = FROM_EMAIL
    msg.attach(MIMEText(html_body, 'html', 'utf-8'))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(FROM_EMAIL, to_email, msg.as_string())
        print(f"[LEAD] 48h upsell email sent to {to_email} (preview: {preview_id})")
        log_email('upsell_print', to_email, subject, 'SENT', preview_id=preview_id, child_name=child_name, lang=lang)
        return True
    except Exception as e:
        print(f"[LEAD] Failed to send 48h upsell email to {to_email}: {e}")
        log_email('upsell_print', to_email, subject, 'ERROR', preview_id=preview_id, child_name=child_name, lang=lang, error=str(e))
        return False


def process_pending_follow_up_emails():
    """Check the follow-ups file and send emails that are due.
    - Email 1: 22–30h after purchase (feedback / thank-you)
    - Email 2: 46–50h after purchase (upsell: PDF imprimible + libro impreso)
    Called by the hourly APScheduler job in app.py.
    """
    try:
        if not os.path.exists(FOLLOW_UPS_FILE):
            return
        with open(FOLLOW_UPS_FILE, 'r', encoding='utf-8') as f:
            data = _json.load(f)

        from datetime import datetime as _dt
        now = _dt.now()
        changed = False

        for preview_id, entry in data.items():
            try:
                purchased_at = _dt.fromisoformat(entry.get('purchased_at', ''))
            except ValueError:
                continue
            elapsed_hours = (now - purchased_at).total_seconds() / 3600

            # --- Email 1: 24h feedback (22–30h window) ---
            if not entry.get('email_1_sent'):
                if 22 <= elapsed_hours <= 30:
                    ok = send_feedback_email_24h(
                        entry.get('email', ''),
                        entry.get('child_name', ''),
                        entry.get('lang', 'es'),
                    )
                    if ok:
                        entry['email_1_sent'] = True
                        entry['email_1_sent_at'] = now.isoformat()
                        changed = True

            # --- Email 2: 48h upsell (46–50h window, only after email 1 sent) ---
            elif entry.get('email_1_sent') and not entry.get('email_2_sent'):
                if 46 <= elapsed_hours <= 50:
                    # Skip if customer already bought PDF or print
                    _already_upgraded = False
                    try:
                        import os as _os
                        _pf = _os.path.join(_os.path.dirname(_os.path.dirname(__file__)),
                                            'story_previews', f'{preview_id}.json')
                        if _os.path.exists(_pf):
                            with open(_pf, 'r', encoding='utf-8') as _f:
                                _sd = _json.load(_f)
                            _already_upgraded = bool(_sd.get('want_print') or _sd.get('want_pdf') or _sd.get('pdf_email_sent'))
                    except Exception:
                        pass
                    if _already_upgraded:
                        entry['email_2_sent'] = True
                        entry['email_2_sent_at'] = now.isoformat()
                        entry['email_2_skipped'] = 'already_upgraded'
                        changed = True
                        print(f"[LEAD] Skipped 48h upsell for {preview_id} — customer already upgraded")
                    else:
                        ok = send_upsell_print_email(
                            preview_id,
                            entry.get('email', ''),
                            entry.get('child_name', ''),
                            entry.get('lang', 'es'),
                        )
                        if ok:
                            entry['email_2_sent'] = True
                            entry['email_2_sent_at'] = now.isoformat()
                            changed = True

        if changed:
            with open(FOLLOW_UPS_FILE, 'w', encoding='utf-8') as f:
                _json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[LEAD] Error in process_pending_follow_up_emails: {e}")
