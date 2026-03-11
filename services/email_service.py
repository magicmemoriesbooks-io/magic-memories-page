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
    site_url = os.environ.get('REPLIT_DEV_DOMAIN', 'magicmemoriesbooks.com')
    if lang == 'es':
        return f"""
        <div style="background:#f3e8ff;padding:20px;border-radius:12px;margin:20px 0;text-align:center;border:1px solid #e9d5ff;">
            <p style="font-size:15px;color:#7c3aed;font-weight:bold;margin:0 0 8px;">¿Te gustó la experiencia?</p>
            <p style="font-size:13px;color:#374151;margin:0 0 12px;">Únete a nuestra comunidad para enterarte de nuevos cuentos y ofertas exclusivas.</p>
            <a href="https://{site_url}/#newsletter" style="display:inline-block;background-color:#9333ea;background-image:linear-gradient(135deg,#9333ea,#ec4899);color:#ffffff;padding:10px 24px;border-radius:20px;text-decoration:none;font-weight:bold;font-size:13px;">Suscribirme</a>
        </div>"""
    else:
        return f"""
        <div style="background:#f3e8ff;padding:20px;border-radius:12px;margin:20px 0;text-align:center;border:1px solid #e9d5ff;">
            <p style="font-size:15px;color:#7c3aed;font-weight:bold;margin:0 0 8px;">Did you enjoy the experience?</p>
            <p style="font-size:13px;color:#374151;margin:0 0 12px;">Join our community to hear about new stories and exclusive offers.</p>
            <a href="https://{site_url}/#newsletter" style="display:inline-block;background-color:#9333ea;background-image:linear-gradient(135deg,#9333ea,#ec4899);color:#ffffff;padding:10px 24px;border-radius:20px;text-decoration:none;font-weight:bold;font-size:13px;">Subscribe</a>
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
    visor_url: Optional[str] = None
) -> dict:
    child_name = story_data.get('child_name', 'tu pequeño')
    story_name = story_data.get('story_name', 'tu cuento')
    
    if age_group is None:
        age_group = story_data.get('age_group', 'baby')
    
    is_personalized_book = age_group in ['personalized', 'haz_tu_historia']
    safe_name = child_name.replace(' ', '_').replace("'", "")
    
    if age_group == 'haz_tu_historia':
        subject = f"📚 ¡Tu libro de Haz tu Historia para {child_name} está listo!"
    elif age_group == 'personalized':
        subject = f"📚 ¡Tu libro ilustrado para {child_name} está listo!"
    else:
        subject = f"🎉 ¡Tu cuento para {child_name} está listo!"
    
    attachments_list = ""
    if epub_path:
        attachments_list += f'<li style="padding:4px 0;color:#374151;">📖 <strong>{safe_name}.epub</strong> - Tu eBook digital</li>'
    if pdf_digital_path:
        attachments_list += f'<li style="padding:4px 0;color:#374151;">📄 <strong>{safe_name}_digital.pdf</strong> - Tu libro digital de 24 páginas</li>'
    if pdf_printable_path:
        attachments_list += f'<li style="padding:4px 0;color:#374151;">🖨️ <strong>{safe_name}_imprimible.pdf</strong> - Para llevar a imprenta</li>'
    if instructions_path:
        attachments_list += '<li style="padding:4px 0;color:#374151;">📋 <strong>instrucciones_impresion.pdf</strong></li>'
    
    attachments_html = _info_box(f'''
        <h3 style="margin-top:0;color:#7c3aed;">📎 Archivos adjuntos:</h3>
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
    if final_visor_url:
        read_online_html = _cta_button("📖 Leer Cuento Online", final_visor_url)
        read_online_html += '<p style="color:#6b7280;font-size:12px;text-align:center;margin-top:-15px;">Ábrelo en cualquier dispositivo — celular, tablet o computadora</p>'
        read_online_text = f"\n📖 Leer Cuento Online: {final_visor_url}\n"
    elif preview_id:
        ebook_url = f"{base_url}/ebook-preview/{preview_id}"
        read_online_html = _cta_button("📖 Ver Cuento Online", ebook_url)
        read_online_html += '<p style="color:#6b7280;font-size:12px;text-align:center;margin-top:-15px;">Ábrelo en cualquier dispositivo — celular, tablet o computadora</p>'
        read_online_text = f"\n📖 Leer Cuento Online: {ebook_url}\n"

    if is_personalized_book:
        tracking_link = ""
        tracking_link_text = ""
        if preview_id:
            tracking_url = f"{base_url}/track-order/{preview_id}"
            tracking_link = f'<div style="text-align:center;margin-top:15px;"><a href="{tracking_url}" style="display:inline-block;background-color:#9333ea;background-image:linear-gradient(135deg,#9333ea,#ec4899);color:#ffffff;padding:12px 24px;border-radius:25px;text-decoration:none;font-weight:bold;">📍 Ver estado de mi pedido</a></div>'
            tracking_link_text = f"\n\n📍 Ver estado de tu pedido: {tracking_url}"
        
        extra_sections_html = f"""
                {read_online_html}
                {_success_box(f'''
                    <h4 style="margin-top:0;color:#166534;">📦 Tu libro impreso está en camino</h4>
                    <p style="color:#374151;font-size:13px;margin:0;">
                        Hemos enviado tu libro a producción con Lulu Press.<br>
                        Recibirás actualizaciones de seguimiento en esta misma página.<br><br>
                        <strong>Tiempo estimado de entrega:</strong> 14-21 días hábiles (envío estándar)<br>
                        <strong>Formato:</strong> Tapa dura, 24 páginas, impresión premium a color
                    </p>
                    {tracking_link}
                ''')}
        """
        extra_sections_text = f"""
{read_online_text}
📦 TU LIBRO IMPRESO ESTÁ EN CAMINO
Hemos enviado tu libro a producción con Lulu Press.
Recibirás actualizaciones de seguimiento en el link de abajo.

Tiempo estimado de entrega: 14-21 días hábiles (envío estándar)
Formato: Tapa dura, 24 páginas, impresión premium a color{tracking_link_text}
"""
    else:
        extra_sections_html = f"""
                {read_online_html}
                {_success_box(f'''
                    <h4 style="margin-top:0;color:#166534;">📖 Tu cuento digital está listo</h4>
                    <p style="color:#374151;font-size:13px;margin:0;">
                        También hemos adjuntado tu cuento en formato ePub por si quieres guardarlo.<br><br>
                        📱 <strong>iPhone/iPad:</strong> Ábrelo con Apple Books<br>
                        📱 <strong>Android:</strong> Ábrelo con Google Play Books o cualquier lector de eBooks<br>
                        💻 <strong>Computadora:</strong> Usa Calibre, Adobe Digital Editions, o cualquier lector ePub
                    </p>
                ''')}
        """
        extra_sections_text = f"""
{read_online_text}
📖 TU CUENTO DIGITAL ESTÁ LISTO
También hemos adjuntado tu cuento en formato ePub por si quieres guardarlo.

📱 iPhone/iPad: Ábrelo con Apple Books
📱 Android: Ábrelo con Google Play Books o cualquier lector de eBooks
💻 Computadora: Usa Calibre, Adobe Digital Editions, o cualquier lector ePub
"""
    
    book_type = "Tu libro ilustrado personalizado" if is_personalized_book else "Tu cuento personalizado"
    
    content_inner = f"""
        <h2 style="color:#7c3aed;margin-top:0;">¡Hola!</h2>
        <p style="font-size:16px;color:#374151;">
            {book_type} <strong>"{story_name}"</strong> para <strong>{child_name}</strong> está listo.
        </p>
        {attachments_html}
        {_alert_box('<p style="margin:0;color:#92400e;font-size:14px;"><strong>⚠️ Importante:</strong> Descarga y guarda los archivos adjuntos en tu dispositivo. Estos archivos son tuyos para siempre.</p>')}
        {extra_sections_html}
        {_newsletter_invite_html('es')}
        <p style="color:#7c3aed;font-weight:bold;text-align:center;">¡Gracias por crear recuerdos mágicos! 💜</p>
    """
    
    html_body = _email_wrapper("✨ ¡Tu Cuento Está Listo! ✨", content_inner, to_email)
    
    text_body = f"""
¡Hola!

{book_type} "{story_name}" para {child_name} está listo.

📎 ARCHIVOS ADJUNTOS:
- {safe_name}.epub - {"Tu libro digital" if is_personalized_book else "Tu eBook para leer en cualquier dispositivo"}

⚠️ IMPORTANTE: Descarga y guarda los archivos adjuntos en tu dispositivo.
Estos archivos son tuyos para siempre.

{extra_sections_text}

¡Gracias por crear recuerdos mágicos!
Magic Memories Books
    """
    
    if not SMTP_USER or not SMTP_PASSWORD:
        print(f"[EMAIL SERVICE] SMTP not configured. Would send email to: {to_email}")
        print(f"[EMAIL SERVICE] Subject: {subject}")
        if pdf_digital_path:
            print(f"  - Digital PDF: {pdf_digital_path}")
        if pdf_printable_path:
            print(f"  - Printable PDF: {pdf_printable_path}")
        if epub_path:
            print(f"  - ePub: {epub_path}")
        
        with open('email_log.txt', 'a') as f:
            f.write(f"\n{'='*50}\n")
            f.write(f"TO: {to_email}\nSUBJECT: {subject}\n")
            f.write(f"{'='*50}\n")
        
        return {'success': True, 'message': 'Email logged (SMTP not configured)', 'simulated': True}
    
    try:
        msg = MIMEMultipart('mixed')
        msg['Subject'] = subject
        msg['From'] = f"{FROM_NAME} <{FROM_EMAIL}>"
        msg['To'] = to_email
        
        msg_alternative = MIMEMultipart('alternative')
        msg_alternative.attach(MIMEText(text_body, 'plain', 'utf-8'))
        msg_alternative.attach(MIMEText(html_body, 'html', 'utf-8'))
        msg.attach(msg_alternative)
        
        attached_count = 0
        
        if epub_path and os.path.exists(epub_path):
            if attach_file(msg, epub_path, f"{safe_name}.epub"):
                attached_count += 1
        
        if pdf_digital_path and os.path.exists(pdf_digital_path):
            if attach_file(msg, pdf_digital_path, f"{safe_name}_digital.pdf"):
                attached_count += 1
        
        if pdf_printable_path and os.path.exists(pdf_printable_path):
            if attach_file(msg, pdf_printable_path, f"{safe_name}_imprimible.pdf"):
                attached_count += 1
        
        if instructions_path and os.path.exists(instructions_path):
            if attach_file(msg, instructions_path, "instrucciones_impresion.pdf"):
                attached_count += 1
        
        if attached_count == 0 and not final_visor_url:
            return {'success': False, 'message': 'No files could be attached'}
        
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        
        print(f"[EMAIL SERVICE] Email sent successfully to: {to_email} with {attached_count} attachments")
        return {'success': True, 'message': f'Email sent with {attached_count} attachments'}
        
    except Exception as e:
        print(f"[EMAIL SERVICE] Error sending email: {str(e)}")
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


def send_lulu_order_notification(
    order_folder: str,
    lulu_job_id: str,
    title: str,
    customer_email: str,
    shipping_address: dict,
    interior_pdf_path: Optional[str] = None,
    cover_pdf_path: Optional[str] = None,
    interior_url: Optional[str] = None,
    cover_url: Optional[str] = None
) -> dict:
    from datetime import datetime
    
    admin_email = "pay@magicmemoriesbooks.com"
    
    address_name = shipping_address.get('name', 'N/A')
    address_street = shipping_address.get('street1', 'N/A')
    address_city = shipping_address.get('city', 'N/A')
    address_state = shipping_address.get('state_code', 'N/A')
    address_country = shipping_address.get('country_code', 'N/A')
    address_postal = shipping_address.get('postcode', 'N/A')
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    subject = f"📦 Nuevo pedido Lulu - {title} - {lulu_job_id}"
    
    def _admin_info_row(label, value, alt_bg=False):
        bg = 'background:#fef2f2;' if alt_bg else ''
        return f'<tr style="{bg}"><td style="padding:10px 12px;color:#6b7280;font-size:13px;width:140px;">{label}</td><td style="padding:10px 12px;color:#1f2937;font-size:14px;font-weight:600;">{value}</td></tr>'
    
    pdf_links = ""
    if interior_url:
        pdf_links += f'<a href="{interior_url}" style="color:#dc2626;font-weight:600;">📄 Descargar Interior PDF</a><br>'
    if cover_url:
        pdf_links += f'<a href="{cover_url}" style="color:#dc2626;font-weight:600;">📄 Descargar Cover PDF</a>'
    
    content = f"""
        <table style="width:100%;border-collapse:collapse;font-size:14px;margin-bottom:15px;">
            {_admin_info_row('Lulu Job ID', lulu_job_id, True)}
            {_admin_info_row('Título', title)}
            {_admin_info_row('Carpeta', order_folder, True)}
            {_admin_info_row('Cliente', customer_email)}
            {_admin_info_row('Fecha', timestamp, True)}
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
        
        <h3 style="color:#dc2626;margin-top:20px;font-size:16px;">📎 Archivos PDF</h3>
        <div style="background:#fef2f2;padding:15px;border-radius:8px;border-left:4px solid #dc2626;margin:10px 0;">
            <p style="margin:0;">{pdf_links}</p>
            <p style="color:#6b7280;font-size:12px;margin-top:8px;">(Los PDFs son demasiado grandes para adjuntar por email)</p>
        </div>
    """
    
    html_body = _admin_wrapper("📦 Nuevo Pedido Lulu", content)
    
    text_body = f"""
NUEVO PEDIDO LULU
=================

Lulu Job ID: {lulu_job_id}
Título: {title}
Carpeta: {order_folder}
Cliente: {customer_email}
Fecha: {timestamp}

DIRECCIÓN DE ENVÍO:
{address_name}
{address_street}
{address_city}, {address_state} {address_postal}
{address_country}

ARCHIVOS PDF:
Interior: {interior_url or 'N/A'}
Cover: {cover_url or 'N/A'}
    """
    
    if not SMTP_USER or not SMTP_PASSWORD:
        print(f"[LULU NOTIFICATION] SMTP not configured. Would send to: {admin_email}")
        with open('email_log.txt', 'a') as f:
            f.write(f"\n{'='*50}\nLULU ORDER NOTIFICATION\nTO: {admin_email}\nJOB ID: {lulu_job_id}\n{'='*50}\n")
        return {'success': True, 'message': 'Lulu notification logged (SMTP not configured)', 'simulated': True}
    
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
        
        print(f"[LULU NOTIFICATION] Email sent to {admin_email} with PDF download links")
        return {'success': True, 'message': 'Lulu notification sent with download links'}
        
    except Exception as e:
        print(f"[LULU NOTIFICATION] Error sending email: {str(e)}")
        return {'success': False, 'message': str(e)}


def send_admin_purchase_notification(
    preview_id: str,
    product_type: str,
    customer_email: str,
    story_data: dict
) -> dict:
    from datetime import datetime
    
    admin_email = "pay@magicmemoriesbooks.com"
    
    child_name = story_data.get('child_name', 'N/A')
    story_id = story_data.get('story_id', 'N/A')
    story_name = story_data.get('story_name', story_data.get('title', story_id))
    language = story_data.get('language', story_data.get('lang', 'es'))
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    type_labels = {
        'ebook': '📱 eBook Digital',
        'qs_digital': '📱 Quick Story Digital',
        'qs_print': '📦 Quick Story Print',
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
    
    content = f"""
        <p style="color:#6b7280;font-size:13px;text-align:center;margin-top:0;">Nueva compra recibida</p>
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


def send_admin_gift_email(
    to_email: str,
    book_title: str,
    child_name: str,
    interior_url: str,
    cover_url: str,
    order_folder: str
) -> dict:
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    subject = f"🎁 Libro Regalo Listo - {book_title}"
    
    content = f"""
        <div style="background:#fef2f2;padding:15px;border-radius:8px;border-left:4px solid #dc2626;margin:15px 0;">
            <p style="margin:0;color:#1f2937;font-size:14px;"><strong>Libro:</strong> {book_title}</p>
            <p style="margin:5px 0 0;color:#1f2937;font-size:14px;"><strong>Protagonista:</strong> {child_name}</p>
            <p style="margin:5px 0 0;color:#1f2937;font-size:14px;"><strong>Carpeta:</strong> {order_folder}</p>
            <p style="margin:5px 0 0;color:#1f2937;font-size:14px;"><strong>Fecha:</strong> {timestamp}</p>
        </div>
        
        <h3 style="color:#dc2626;margin-top:25px;font-size:16px;">Archivos para Lulu</h3>
        <p style="color:#374151;font-size:14px;">Descarga estos archivos y súbelos manualmente a Lulu para imprimir:</p>
        
        <div style="text-align:center;margin:20px 0;">
            <a href="{interior_url}" style="display:inline-block;background-color:#dc2626;background-image:linear-gradient(135deg,#dc2626,#b91c1c);color:#ffffff;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:bold;margin:5px;">📄 Descargar Interior PDF</a>
            <br><br>
            <a href="{cover_url}" style="display:inline-block;background-color:#dc2626;background-image:linear-gradient(135deg,#dc2626,#b91c1c);color:#ffffff;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:bold;margin:5px;">📄 Descargar Cover PDF</a>
        </div>
        
        <div style="background:#fef3c7;padding:15px;border-radius:8px;border-left:4px solid #f59e0b;margin:15px 0;">
            <p style="margin:0;font-size:13px;color:#92400e;">
                <strong>Recuerda:</strong> Sube el interior y la portada por separado en Lulu. 
                El interior es el PDF con todas las páginas del libro. La portada es el spread completo (frente + lomo + contraportada).
            </p>
        </div>
    """
    
    html_body = _admin_wrapper("🎁 Libro Regalo Generado", content)
    
    text_body = f"""LIBRO REGALO GENERADO
====================
Libro: {book_title}
Protagonista: {child_name}
Carpeta: {order_folder}
Fecha: {timestamp}

ARCHIVOS PARA LULU:
Interior: {interior_url}
Cover: {cover_url}
"""
    
    if not SMTP_USER or not SMTP_PASSWORD:
        print(f"[ADMIN GIFT EMAIL] SMTP not configured. Would send to: {to_email}")
        return {'success': True, 'message': 'Admin gift email logged (SMTP not configured)', 'simulated': True}
    
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
        
        print(f"[ADMIN GIFT EMAIL] Sent to {to_email}")
        return {'success': True, 'message': 'Admin gift email sent'}
    except Exception as e:
        print(f"[ADMIN GIFT EMAIL] Error: {str(e)}")
        return {'success': False, 'message': str(e)}


def send_payment_confirmation_email(to_email: str, child_name: str, recovery_url: str, lang: str = 'es'):
    if lang == 'es':
        subject = f"Confirmación de Pago - Cuento de {child_name}"
        content = f"""
                <p style="font-size:16px;color:#374151;">¡Gracias por tu compra! Tu pago ha sido procesado correctamente.</p>
                {_success_box(f'''
                    <h3 style="margin-top:0;color:#166534;">Tu cuento personalizado para {child_name} está siendo creado</h3>
                    <p style="color:#374151;font-size:14px;">Estamos generando las ilustraciones únicas de tu historia. Este proceso toma aproximadamente 3-4 minutos.</p>
                ''')}
                {_alert_box(f'''
                    <h3 style="margin-top:0;color:#92400e;">⚠️ ¿Cerraste la página por error?</h3>
                    <p style="color:#92400e;font-size:14px;">No te preocupes, tu pago está registrado. Usa el siguiente enlace para volver a tu cuento:</p>
                    {_cta_button("Recuperar Mi Cuento", recovery_url)}
                ''')}
                <p style="color:#374151;font-size:14px;">Si tienes algún problema, escríbenos a:</p>
                <p style="color:#374151;"><strong>pay@magicmemoriesbooks.com</strong></p>
                <p style="color:#374151;font-size:14px;">Incluye tu email de compra y te ayudaremos a obtener tu historia.</p>
                {_newsletter_invite_html('es')}"""
        html_content = _email_wrapper("✨ ¡Pago Confirmado! ✨", content, to_email)
    else:
        subject = f"Payment Confirmation - {child_name}'s Story"
        content = f"""
                <p style="font-size:16px;color:#374151;">Thank you for your purchase! Your payment has been processed successfully.</p>
                {_success_box(f'''
                    <h3 style="margin-top:0;color:#166534;">Your personalized story for {child_name} is being created</h3>
                    <p style="color:#374151;font-size:14px;">We're generating the unique illustrations for your story. This process takes approximately 3-4 minutes.</p>
                ''')}
                {_alert_box(f'''
                    <h3 style="margin-top:0;color:#92400e;">⚠️ Did you accidentally close the page?</h3>
                    <p style="color:#92400e;font-size:14px;">Don't worry, your payment is registered. Use the following link to return to your story:</p>
                    {_cta_button("Recover My Story", recovery_url)}
                ''')}
                <p style="color:#374151;font-size:14px;">If you have any issues, email us at:</p>
                <p style="color:#374151;"><strong>pay@magicmemoriesbooks.com</strong></p>
                <p style="color:#374151;font-size:14px;">Include your purchase email and we'll help you get your story.</p>
                {_newsletter_invite_html('en')}"""
        html_content = _email_wrapper("✨ Payment Confirmed! ✨", content, to_email)
    
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
        return True
    except Exception as e:
        print(f"[EMAIL] Failed to send payment confirmation: {e}")
        return False


def send_recovery_link_email(to_email: str, child_name: str, recovery_url: str, lang: str = 'es'):
    if lang == 'es':
        subject = f"Enlace de Recuperación - Cuento de {child_name}"
        content = f"""
                <h2 style="color:#7c3aed;margin-top:0;">¡Hola!</h2>
                <p style="font-size:16px;color:#374151;">Pedimos disculpas por el inconveniente. Debido a un error técnico inesperado, es posible que hayas tenido dificultades para acceder al cuento de <strong>{child_name}</strong>.</p>
                {_success_box(f'''
                    <p style="margin-bottom:15px;color:#374151;">Tu cuento está listo y te espera:</p>
                    {_cta_button("Ver Mi Cuento", recovery_url)}
                    <p style="margin-top:10px;font-size:12px;color:#6b7280;text-align:center;">Si el botón no funciona, copia este enlace en tu navegador:</p>
                    <p style="font-size:11px;color:#374151;word-break:break-all;text-align:center;">{recovery_url}</p>
                ''')}
                <p style="color:#374151;font-size:14px;">Si tienes algún problema, escríbenos a:</p>
                <p style="color:#374151;"><strong>pay@magicmemoriesbooks.com</strong></p>"""
        html_content = _email_wrapper("✨ Enlace de Recuperación ✨", content, to_email)
    else:
        subject = f"Recovery Link - {child_name}'s Story"
        content = f"""
                <h2 style="color:#7c3aed;margin-top:0;">Hello!</h2>
                <p style="font-size:16px;color:#374151;">We apologize for the inconvenience. Due to an unexpected technical error, you may have had difficulty accessing <strong>{child_name}</strong>'s story.</p>
                {_success_box(f'''
                    <p style="margin-bottom:15px;color:#374151;">Your story is ready and waiting:</p>
                    {_cta_button("View My Story", recovery_url)}
                    <p style="margin-top:10px;font-size:12px;color:#6b7280;text-align:center;">If the button doesn't work, copy this link into your browser:</p>
                    <p style="font-size:11px;color:#374151;word-break:break-all;text-align:center;">{recovery_url}</p>
                ''')}
                <p style="color:#374151;font-size:14px;">If you have any issues, email us at:</p>
                <p style="color:#374151;"><strong>pay@magicmemoriesbooks.com</strong></p>"""
        html_content = _email_wrapper("✨ Recovery Link ✨", content, to_email)
    
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
        print(f"[EMAIL] Recovery link sent to {to_email}")
        return True
    except Exception as e:
        print(f"[EMAIL] Failed to send recovery link: {e}")
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


def send_lulu_failure_email(to_email: str, child_name: str, error_message: str, lang: str = 'es', preview_id: str = ''):
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
        print(f"[EMAIL] Lulu failure notification sent to {to_email}")
        return True
    except Exception as e:
        print(f"[EMAIL] Failed to send Lulu failure email: {e}")
        return False


def send_lulu_failure_admin_email(preview_id: str, child_name: str, error_message: str, 
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
    
    subject = f"[ALERTA] Fallo Lulu - {child_name} ({preview_id[:8]})"
    
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
        
        <h3 style="color:#dc2626;margin-top:20px;font-size:16px;">Error de Lulu:</h3>
        <div style="background:#fef3c7;border-left:4px solid #f59e0b;border-radius:8px;padding:15px;margin:15px 0;font-family:monospace;font-size:13px;word-break:break-all;color:#92400e;">{error_message}</div>
        
        {address_section}
        
        <div style="text-align:center;margin-top:25px;">
            <a href="{rescue_url}" style="display:inline-block;background-color:#dc2626;background-image:linear-gradient(135deg,#dc2626,#b91c1c);color:#ffffff;padding:12px 28px;border-radius:8px;text-decoration:none;font-weight:700;font-size:15px;">Rescatar Pedido</a>
        </div>
        
        <p style="margin-top:20px;font-size:13px;color:#6b7280;">
            Desde la pagina de rescate puedes ver el libro completo, corregir la direccion y reenviar a Lulu.
        </p>
    """
    
    html_body = _admin_wrapper("⚠️ Fallo en Envío a Lulu", content)
    
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
        print(f"[EMAIL] Lulu failure ADMIN notification sent to {admin_email}")
        return True
    except Exception as e:
        print(f"[EMAIL] Failed to send Lulu failure admin email: {e}")
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
        msg['From'] = FROM_EMAIL
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


def send_ebook_email(to_email: str, story_data: dict, visor_url: str, is_gift: bool = False,
                     pdf_printable_path: str = None, instructions_path: str = None):
    try:
        child_name = story_data.get('child_name', 'tu pequeno')
        story_name = story_data.get('story_name', 'tu cuento')
        lang = story_data.get('lang', 'es')
        
        if is_gift:
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
        if pdf_printable_path:
            print_label = "Listo para imprimir en casa o imprenta" if lang == "es" else "Ready to print at home or print shop"
            inst_label = "Instrucciones de impresión" if lang == "es" else "Printing instructions"
            items = f'<li style="padding:3px 0;color:#374151;">🖨️ <strong>PDF imprimible 8.5x8.5"</strong> - {print_label}</li>'
            if instructions_path:
                items += f'<li style="padding:3px 0;color:#374151;">📋 <strong>{inst_label}</strong></li>'
            attachments_section = _info_box(f'''
                <h4 style="margin-top:0;color:#7c3aed;">{attach_title}</h4>
                <ul style="text-align:left;list-style:none;padding-left:0;margin:0.5em 0;">{items}</ul>
            ''')
        
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
            
            {attachments_section}
            
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
        
        text_body = f"""
{ebook_label} "{story_name}" {for_word} {child_name} {ready_word}

{button_text}: {visor_url}

{access_info}

{thanks_msg}
Magic Memories Books
        """
        
        alt_part.attach(MIMEText(text_body, 'plain'))
        alt_part.attach(MIMEText(html_content, 'html'))
        
        if has_attachments:
            msg.attach(alt_part)
            if pdf_printable_path and os.path.exists(pdf_printable_path):
                if attach_file(msg, pdf_printable_path, f"{safe_name}_imprimible.pdf"):
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
        print(f"[EMAIL] eBook email sent to {to_email} (is_gift={is_gift}{attachments_info})")
        return {'success': True, 'message': f'eBook email sent to {to_email}'}
        
    except Exception as e:
        print(f"[EMAIL] Failed to send eBook email: {e}")
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
        <div style="text-align:center;margin:24px 0;">
            <a href="{renew_url}" style="background:linear-gradient(135deg,#7c3aed,#ec4899);color:#fff;font-weight:800;font-size:15px;padding:14px 32px;border-radius:30px;text-decoration:none;display:inline-block;box-shadow:0 4px 15px rgba(124,58,237,0.3);">
                ✨ Comprar acceso permanente — $7
            </a>
        </div>
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
        <div style="text-align:center;margin:24px 0;">
            <a href="{renew_url}" style="background:linear-gradient(135deg,#7c3aed,#ec4899);color:#fff;font-weight:800;font-size:15px;padding:14px 32px;border-radius:30px;text-decoration:none;display:inline-block;box-shadow:0 4px 15px rgba(124,58,237,0.3);">
                ✨ Buy permanent access — $7
            </a>
        </div>
        <p style="color:#6b7280;font-size:12px;">If you're not interested, no worries. The link will stop working when it expires.</p>
            """
        body_html = _email_wrapper(subject, content, to_email)
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


def send_admin_error_email(process_name: str, preview_id: str, error_message: str, traceback_text: str = ''):
    if not SMTP_USER or not SMTP_PASSWORD:
        print(f"[ADMIN-ERROR] SMTP no configurado - error en {process_name} para {preview_id}: {error_message}")
        return {'success': False}
    try:
        content = f"""
        <h2 style="color:#dc2626;">Error en proceso: {process_name}</h2>
        <table style="width:100%;border-collapse:collapse;margin:12px 0;">
          <tr><td style="padding:6px;font-weight:bold;color:#6b7280;">Preview ID</td>
              <td style="padding:6px;color:#111827;">{preview_id}</td></tr>
          <tr style="background:#fef2f2;"><td style="padding:6px;font-weight:bold;color:#6b7280;">Error</td>
              <td style="padding:6px;color:#dc2626;">{error_message}</td></tr>
        </table>
        """
        if traceback_text:
            content += f"""
        <h3 style="color:#374151;margin-top:16px;">Traceback completo:</h3>
        <pre style="background:#f3f4f6;padding:12px;border-radius:6px;font-size:11px;overflow-x:auto;color:#374151;">{traceback_text}</pre>
            """
        body_html = _admin_wrapper(f"ERROR: {process_name}", content)

        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"[MMB ERROR] {process_name} falló para {preview_id}"
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
            subject = "📦 Tu libro impreso está en camino — Magic Memories Books"
            body_html = f"""
            <div style="text-align:center;padding:32px 0;">
                <p style="font-size:48px;">📦</p>
                <h1 style="color:#7c3aed;font-family:Georgia,serif;">¡Tu libro está en camino!</h1>
                <p style="color:#4b5563;font-size:16px;">Hola {customer_name},</p>
                <p style="color:#4b5563;">Tu libro impreso personalizado ha sido enviado y está en camino hacia ti.</p>
                <div style="background:#f5f3ff;border-radius:12px;padding:20px;margin:24px 0;display:inline-block;">
                    <p style="color:#6b7280;font-size:14px;margin:0;">Número de seguimiento</p>
                    <p style="color:#7c3aed;font-size:24px;font-weight:bold;margin:8px 0;">{tracking_number}</p>
                </div>
                <p style="color:#4b5563;font-size:14px;">Tiempo estimado de entrega: 5-15 días hábiles según tu ubicación.</p>
                <p style="color:#6b7280;font-size:12px;margin-top:24px;">¿Preguntas? <a href="mailto:pay@magicmemoriesbooks.com" style="color:#7c3aed;">pay@magicmemoriesbooks.com</a></p>
            </div>"""
        else:
            subject = "📦 Your printed book is on its way — Magic Memories Books"
            body_html = f"""
            <div style="text-align:center;padding:32px 0;">
                <p style="font-size:48px;">📦</p>
                <h1 style="color:#7c3aed;font-family:Georgia,serif;">Your book is on its way!</h1>
                <p style="color:#4b5563;font-size:16px;">Hello {customer_name},</p>
                <p style="color:#4b5563;">Your personalized printed book has been shipped and is on its way to you.</p>
                <div style="background:#f5f3ff;border-radius:12px;padding:20px;margin:24px 0;display:inline-block;">
                    <p style="color:#6b7280;font-size:14px;margin:0;">Tracking number</p>
                    <p style="color:#7c3aed;font-size:24px;font-weight:bold;margin:8px 0;">{tracking_number}</p>
                </div>
                <p style="color:#4b5563;font-size:14px;">Estimated delivery: 5-15 business days depending on your location.</p>
                <p style="color:#6b7280;font-size:12px;margin-top:24px;">Questions? <a href="mailto:pay@magicmemoriesbooks.com" style="color:#7c3aed;">pay@magicmemoriesbooks.com</a></p>
            </div>"""

        full_html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"></head>
        <body style="font-family:'Segoe UI',sans-serif;background:#f8f5ff;margin:0;padding:20px;">
        <div style="max-width:600px;margin:0 auto;background:white;border-radius:16px;overflow:hidden;padding:32px;">
        {body_html}
        </div></body></html>"""

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{FROM_NAME} <{FROM_EMAIL}>"
        msg['To'] = to_email
        msg.attach(MIMEText(full_html, 'html', 'utf-8'))
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(FROM_EMAIL, [to_email], msg.as_string())
        print(f"[EMAIL] Tracking email sent to {to_email}")
        return {'success': True}
    except Exception as e:
        print(f"[EMAIL] Tracking email error: {e}")
        return {'success': False, 'error': str(e)}
