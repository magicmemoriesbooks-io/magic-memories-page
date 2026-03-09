import os
import re
import requests
import subprocess
import tempfile
from io import BytesIO
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.units import inch, mm
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from PIL import Image, ImageOps

TEXT_BACKGROUND_PATH = 'static/images/text_background.jpg'
BACK_COVER_PATH = 'static/images/back_cover.jpg'
PRINTABLE_TEXT_BACKGROUND = 'static/images/text_background_printable.jpg'

def sanitize_pdf_with_ghostscript(input_path, output_path=None):
    """
    Post-process PDF with Ghostscript to create a clean PDF that avoids antivirus false positives.
    This linearizes the PDF and produces standard-compliant output.
    """
    if output_path is None:
        output_path = input_path
    
    temp_output = input_path + '.tmp'
    
    try:
        cmd = [
            'gs',
            '-dNOPAUSE',
            '-dBATCH',
            '-dSAFER',
            '-sDEVICE=pdfwrite',
            '-dCompatibilityLevel=1.4',
            '-dPDFSETTINGS=/prepress',
            '-dColorImageResolution=150',
            '-dGrayImageResolution=150',
            '-dMonoImageResolution=150',
            '-dAutoRotatePages=/None',
            '-dEmbedAllFonts=true',
            '-dSubsetFonts=true',
            '-dDetectDuplicateImages=true',
            '-dFastWebView=true',
            '-dHaveTransparency=false',
            f'-sOutputFile={temp_output}',
            input_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0 and os.path.exists(temp_output):
            os.replace(temp_output, output_path)
            print(f"PDF sanitized successfully: {output_path}")
            return output_path
        else:
            print(f"Ghostscript warning: {result.stderr}")
            if os.path.exists(temp_output):
                os.remove(temp_output)
            return input_path
            
    except subprocess.TimeoutExpired:
        print("Ghostscript timeout - using original PDF")
        if os.path.exists(temp_output):
            os.remove(temp_output)
        return input_path
    except FileNotFoundError:
        print("Ghostscript not found - using original PDF")
        return input_path
    except Exception as e:
        print(f"Ghostscript error: {e}")
        if os.path.exists(temp_output):
            os.remove(temp_output)
        return input_path

def set_pdf_metadata(c, title, author="Magic Memories Books"):
    """Set clean PDF metadata to avoid false positives"""
    c.setTitle(title)
    c.setAuthor(author)
    c.setSubject("Children's Personalized Storybook")
    c.setCreator("Magic Memories Books")
    c.setProducer("ReportLab PDF Library")

def register_fonts():
    return 'Helvetica'

def register_baby_book_fonts():
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    
    fonts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'fonts')
    fredoka_path = os.path.join(fonts_dir, 'Fredoka-Regular.ttf')
    titan_path = os.path.join(fonts_dir, 'TitanOne-Regular.ttf')
    abeezee_path = os.path.join(fonts_dir, 'ABeeZee-Regular.ttf')
    bukhari_path = os.path.join(fonts_dir, 'BukhariScript.ttf')
    
    fonts_registered = {'body': 'Helvetica', 'dropcap': 'Helvetica', 'title': 'Helvetica', 'fin': 'Helvetica'}
    
    if os.path.exists(fredoka_path):
        try:
            pdfmetrics.registerFont(TTFont('Fredoka', fredoka_path))
            fonts_registered['body'] = 'Fredoka'
            fonts_registered['dropcap'] = 'Fredoka'
            print(f"[FONTS] Fredoka registered OK (body + dropcap)")
        except Exception as e:
            print(f"[FONTS] Could not register Fredoka: {e}")
    
    if os.path.exists(titan_path):
        try:
            pdfmetrics.registerFont(TTFont('TitanOne', titan_path))
            fonts_registered['title'] = 'TitanOne'
        except Exception as e:
            print(f"[FONTS] Could not register TitanOne: {e}")
    
    if os.path.exists(abeezee_path):
        try:
            pdfmetrics.registerFont(TTFont('ABeeZee', abeezee_path))
        except Exception as e:
            print(f"[FONTS] Could not register ABeeZee: {e}")
    
    if os.path.exists(bukhari_path):
        try:
            pdfmetrics.registerFont(TTFont('BukhariScript', bukhari_path))
            fonts_registered['fin'] = 'BukhariScript'
            print(f"[FONTS] BukhariScript registered OK (fin)")
        except Exception as e:
            print(f"[FONTS] Could not register BukhariScript: {e}")
    
    nunito_sb_path = os.path.join(fonts_dir, 'Nunito-SemiBold.ttf')
    nunito_eb_path = os.path.join(fonts_dir, 'Nunito-ExtraBold.ttf')
    
    if os.path.exists(nunito_sb_path):
        try:
            pdfmetrics.registerFont(TTFont('Nunito-SemiBold', nunito_sb_path))
            print(f"[FONTS] Nunito-SemiBold registered OK")
        except Exception as e:
            print(f"[FONTS] Could not register Nunito-SemiBold: {e}")
    
    if os.path.exists(nunito_eb_path):
        try:
            pdfmetrics.registerFont(TTFont('Nunito-ExtraBold', nunito_eb_path))
            print(f"[FONTS] Nunito-ExtraBold registered OK")
        except Exception as e:
            print(f"[FONTS] Could not register Nunito-ExtraBold: {e}")
    
    return fonts_registered

def parse_story_sections(story_text):
    sections = []
    dedication = ""
    
    section_pattern = r'\*\*(?:ESCENA|SCENE|SECTION)\s*(\d+)[:\s]*([^*]*)\*\*\s*(.*?)(?=\*\*(?:ESCENA|SCENE|SECTION)\s*\d+|DEDICATION:|$)'
    dedication_pattern = r'DEDICATION:\s*(.*?)$'
    
    section_matches = re.findall(section_pattern, story_text, re.DOTALL | re.IGNORECASE)
    for num, title, content in section_matches:
        full_section = content.strip()
        sections.append(full_section)
    
    if not sections:
        section_pattern = r'SECTION\s*(\d+):\s*(.*?)(?=SECTION\s*\d+:|DEDICATION:|$)'
        section_matches = re.findall(section_pattern, story_text, re.DOTALL | re.IGNORECASE)
        for num, content in section_matches:
            sections.append(content.strip())
    
    dedication_match = re.search(dedication_pattern, story_text, re.DOTALL | re.IGNORECASE)
    if dedication_match:
        dedication = dedication_match.group(1).strip()
    
    while len(sections) < 4:
        sections.append("")
    
    return sections[:4], dedication

def draw_wrapped_text(c, text, x, y, max_width, font_name, font_size, line_height, fill_color=None):
    if fill_color:
        c.setFillColor(fill_color)
    c.setFont(font_name, font_size)
    
    paragraphs = text.split('\n')
    current_y = y
    
    for paragraph in paragraphs:
        if not paragraph.strip():
            current_y -= line_height
            continue
            
        words = paragraph.split()
        line = ""
        
        for word in words:
            test_line = line + word + " "
            if c.stringWidth(test_line, font_name, font_size) < max_width:
                line = test_line
            else:
                if line:
                    c.drawString(x, current_y, line.strip())
                    current_y -= line_height
                line = word + " "
        
        if line:
            c.drawString(x, current_y, line.strip())
            current_y -= line_height
    
    return current_y

def draw_centered_text(c, text, y, font_name, font_size, page_width, fill_color=None):
    if fill_color:
        c.setFillColor(fill_color)
    c.setFont(font_name, font_size)
    text_width = c.stringWidth(text, font_name, font_size)
    c.drawString((page_width - text_width) / 2, y, text)

def draw_wrapped_centered_text(c, text, y, max_width, font_name, font_size, line_height, page_width, fill_color=None):
    """Draw text centered and wrapped within max_width, with proper margins."""
    if fill_color:
        c.setFillColor(fill_color)
    c.setFont(font_name, font_size)
    
    paragraphs = text.split('\n')
    current_y = y
    
    for paragraph in paragraphs:
        if not paragraph.strip():
            current_y -= line_height
            continue
        
        words = paragraph.split()
        line = ""
        
        for word in words:
            test_line = line + word + " "
            if c.stringWidth(test_line, font_name, font_size) < max_width:
                line = test_line
            else:
                if line:
                    c.drawCentredString(page_width / 2, current_y, line.strip())
                    current_y -= line_height
                line = word + " "
        
        if line:
            c.drawCentredString(page_width / 2, current_y, line.strip())
            current_y -= line_height
    
    return current_y

def load_image_from_url(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, timeout=30, headers=headers)
        if response.status_code == 200:
            img = Image.open(BytesIO(response.content))
            img = ImageOps.exif_transpose(img)
            
            width, height = img.size
            if width > height:
                print(f"Rotating image: {width}x{height} -> portrait orientation")
                img = img.rotate(90, expand=True)
            
            if img.mode == 'RGBA':
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            img_buffer = BytesIO()
            img.save(img_buffer, format='JPEG', quality=95, optimize=True)
            img_buffer.seek(0)
            return ImageReader(img_buffer)
    except Exception as e:
        print(f"Error loading image: {e}")
    return None

def draw_image_page(c, image_url, page_width, page_height, margin=0):
    c.setFillColor(HexColor('#FFFFFF'))
    c.rect(0, 0, page_width, page_height, fill=True)
    
    img = load_image_from_url(image_url)
    if img:
        c.drawImage(img, 0, 0, width=page_width, height=page_height, 
                   preserveAspectRatio=True, anchor='c')

def draw_text_page_background(c, width, height):
    """Draw the pastel background image on text pages"""
    if os.path.exists(TEXT_BACKGROUND_PATH):
        try:
            img = Image.open(TEXT_BACKGROUND_PATH)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img_buffer = BytesIO()
            img.save(img_buffer, format='JPEG', quality=95)
            img_buffer.seek(0)
            bg_img = ImageReader(img_buffer)
            c.drawImage(bg_img, 0, 0, width=width, height=height, preserveAspectRatio=False)
        except Exception as e:
            print(f"Error loading background: {e}")
            c.setFillColor(HexColor('#F0F7FF'))
            c.rect(0, 0, width, height, fill=True)
    else:
        print(f"Background file not found: {TEXT_BACKGROUND_PATH}")
        c.setFillColor(HexColor('#F0F7FF'))
        c.rect(0, 0, width, height, fill=True)

def create_digital_pdf(order, story_text, illustrations, output_path):
    """
    Digital PDF - 12 pages exactly (A4 format):
    1. Cover (title + cover image)
    2. Text page 1
    3. Illustration 1
    4. Text page 2
    5. Illustration 2
    6. Text page 3
    7. Illustration 3
    8. Text page 4
    9. Illustration 4
    10. Dedication (full page)
    11. Final illustration (illustration 5)
    12. Back cover with logo
    """
    font_name = register_fonts()
    
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4
    
    purple = HexColor('#6B46C1')
    white = HexColor('#FFFFFF')
    dark_text = HexColor('#2D3748')
    pink_bg = HexColor('#FDF2F8')
    gray_text = HexColor('#4A5568')
    
    sections, dedication_text = parse_story_sections(story_text)
    
    story_title = ""
    if hasattr(order, 'story_template') and order.story_template:
        story_title = order.story_template.replace('_', ' ').title()
    
    full_title = f"{story_title} de {order.child_name}" if order.language == 'es' else f"{order.child_name}'s {story_title}"
    
    set_pdf_metadata(c, full_title, "Magic Memories Books")
    
    if illustrations and len(illustrations) > 0:
        cover_img = load_image_from_url(illustrations[0])
        if cover_img:
            c.drawImage(cover_img, 0, 0, width=width, height=height, 
                       preserveAspectRatio=True, anchor='c')
            c.setFillColor(HexColor('#00000080'))
            c.rect(0, height - 120, width, 120, fill=True, stroke=False)
    else:
        c.setFillColor(purple)
        c.rect(0, 0, width, height, fill=True)
    
    c.setFillColor(white)
    title_font_size = 28
    
    words = full_title.split()
    lines = []
    current_line = ""
    for word in words:
        test_line = current_line + " " + word if current_line else word
        if c.stringWidth(test_line, font_name, title_font_size) < width - 80:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    
    title_y = height - 50
    for line in lines:
        draw_centered_text(c, line, title_y, font_name, title_font_size, width, white)
        title_y -= 36
    
    c.showPage()
    
    text_font_size = 23
    line_height = 32
    margin_x = 60
    margin_top = 100
    text_area_width = width - (margin_x * 2)
    
    for i in range(4):
        draw_text_page_background(c, width, height)
        
        if i < len(sections) and sections[i]:
            draw_wrapped_text(
                c, sections[i],
                margin_x, height - 80,
                text_area_width,
                font_name, text_font_size, line_height,
                dark_text
            )
        
        c.setFillColor(gray_text)
        page_num = f"- {i * 2 + 2} -"
        draw_centered_text(c, page_num, 30, font_name, 10, width, gray_text)
        
        c.showPage()
        
        illust_index = i + 1
        if illustrations and illust_index < len(illustrations):
            draw_image_page(c, illustrations[illust_index], width, height)
        else:
            c.setFillColor(white)
            c.rect(0, 0, width, height, fill=True)
        
        c.setFillColor(gray_text)
        page_num = f"- {i * 2 + 3} -"
        draw_centered_text(c, page_num, 30, font_name, 10, width, gray_text)
        
        c.showPage()
    
    draw_text_page_background(c, width, height)
    
    c.setFillColor(purple)
    ded_title = "Dedicatoria" if order.language == 'es' else "Dedication"
    draw_centered_text(c, ded_title, height - 180, font_name, 32, width, purple)
    
    c.setStrokeColor(purple)
    c.setLineWidth(2)
    c.line(width/2 - 80, height - 210, width/2 + 80, height - 210)
    
    ded_to_show = (order.dedication if hasattr(order, 'dedication') and order.dedication else "") or dedication_text
    if ded_to_show:
        draw_wrapped_text(
            c, f'"{ded_to_show}"',
            80, height - 280,
            width - 160,
            font_name, 18, 28,
            gray_text
        )
    
    if hasattr(order, 'author_name') and order.author_name:
        author_text = f"— {order.author_name}"
        draw_centered_text(c, author_text, 150, font_name, 14, width, gray_text)
    
    c.showPage()
    
    if illustrations and len(illustrations) > 5:
        draw_image_page(c, illustrations[5], width, height)
    else:
        c.setFillColor(white)
        c.rect(0, 0, width, height, fill=True)
    
    c.showPage()
    
    if os.path.exists(BACK_COVER_PATH):
        try:
            back_img = Image.open(BACK_COVER_PATH)
            if back_img.mode != 'RGB':
                back_img = back_img.convert('RGB')
            img_buffer = BytesIO()
            back_img.save(img_buffer, format='JPEG', quality=95)
            img_buffer.seek(0)
            back_reader = ImageReader(img_buffer)
            c.drawImage(back_reader, 0, 0, width=width, height=height, preserveAspectRatio=True, anchor='c')
        except Exception as e:
            print(f"Error loading back cover: {e}")
            c.setFillColor(purple)
            c.rect(0, 0, width, height, fill=True)
    else:
        c.setFillColor(purple)
        c.rect(0, 0, width, height, fill=True)
    
    c.save()
    
    sanitize_pdf_with_ghostscript(output_path)
    
    return output_path


def create_print_pdf(order, story_text, illustrations, output_path):
    """
    Print PDF for Lulu - 16 pages exactly (A4 format):
    1. Cover
    2. Blank page (behind cover)
    3. Text page 1
    4. Illustration 1
    5. Text page 2
    6. Illustration 2
    7. Text page 3
    8. Illustration 3
    9. Text page 4
    10. Illustration 4
    11. Dedication
    12. Free/transition page (with final illustration)
    13. Interior back cover / logo
    14. NOTES/DRAW page
    15. Blank page
    16. Exterior back cover
    """
    font_name = register_fonts()
    
    c = canvas.Canvas(output_path, pagesize=A4)
    page_width, page_height = A4
    
    purple = HexColor('#6B46C1')
    white = HexColor('#FFFFFF')
    dark_text = HexColor('#2D3748')
    pink_bg = HexColor('#FDF2F8')
    gray_text = HexColor('#4A5568')
    light_gray = HexColor('#E2E8F0')
    
    sections, dedication_text = parse_story_sections(story_text)
    
    story_title = ""
    if hasattr(order, 'story_template') and order.story_template:
        story_title = order.story_template.replace('_', ' ').title()
    
    full_title = f"{story_title} de {order.child_name}" if order.language == 'es' else f"{order.child_name}'s {story_title}"
    
    set_pdf_metadata(c, f"{full_title} - Print Version", "Magic Memories Books")
    
    if illustrations and len(illustrations) > 0:
        cover_img = load_image_from_url(illustrations[0])
        if cover_img:
            c.drawImage(cover_img, 0, 0, width=page_width, height=page_height, 
                       preserveAspectRatio=True, anchor='c')
            c.setFillColor(HexColor('#00000080'))
            c.rect(0, page_height - 100, page_width, 100, fill=True, stroke=False)
    else:
        c.setFillColor(purple)
        c.rect(0, 0, page_width, page_height, fill=True)
    
    c.setFillColor(white)
    title_font_size = 26
    
    words = full_title.split()
    lines = []
    current_line = ""
    for word in words:
        test_line = current_line + " " + word if current_line else word
        if c.stringWidth(test_line, font_name, title_font_size) < page_width - 60:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    
    title_y = page_height - 40
    for line in lines:
        draw_centered_text(c, line, title_y, font_name, title_font_size, page_width, white)
        title_y -= 32
    
    c.showPage()
    
    c.setFillColor(white)
    c.rect(0, 0, page_width, page_height, fill=True)
    c.showPage()
    
    text_font_size = 23
    line_height = 32
    margin_x = 50
    margin_top = 100
    text_area_width = page_width - (margin_x * 2)
    
    for i in range(4):
        draw_text_page_background(c, page_width, page_height)
        
        if i < len(sections) and sections[i]:
            draw_wrapped_text(
                c, sections[i],
                margin_x, page_height - 80,
                text_area_width,
                font_name, text_font_size, line_height,
                dark_text
            )
        
        c.setFillColor(gray_text)
        page_num = f"- {i * 2 + 3} -"
        draw_centered_text(c, page_num, 25, font_name, 9, page_width, gray_text)
        
        c.showPage()
        
        illust_index = i + 1
        if illustrations and illust_index < len(illustrations):
            draw_image_page(c, illustrations[illust_index], page_width, page_height, margin=30)
        else:
            c.setFillColor(white)
            c.rect(0, 0, page_width, page_height, fill=True)
        
        c.setFillColor(gray_text)
        page_num = f"- {i * 2 + 4} -"
        draw_centered_text(c, page_num, 25, font_name, 9, page_width, gray_text)
        
        c.showPage()
    
    draw_text_page_background(c, page_width, page_height)
    
    c.setFillColor(purple)
    ded_title = "Dedicatoria" if order.language == 'es' else "Dedication"
    draw_centered_text(c, ded_title, page_height - 160, font_name, 28, page_width, purple)
    
    c.setStrokeColor(purple)
    c.setLineWidth(2)
    c.line(page_width/2 - 60, page_height - 185, page_width/2 + 60, page_height - 185)
    
    ded_to_show = (order.dedication if hasattr(order, 'dedication') and order.dedication else "") or dedication_text
    if ded_to_show:
        draw_wrapped_text(
            c, f'"{ded_to_show}"',
            60, page_height - 240,
            page_width - 120,
            font_name, 16, 24,
            gray_text
        )
    
    if hasattr(order, 'author_name') and order.author_name:
        author_text = f"— {order.author_name}"
        draw_centered_text(c, author_text, 100, font_name, 12, page_width, gray_text)
    
    c.showPage()
    
    if illustrations and len(illustrations) > 5:
        draw_image_page(c, illustrations[5], page_width, page_height, margin=30)
    else:
        c.setFillColor(white)
        c.rect(0, 0, page_width, page_height, fill=True)
    
    c.showPage()
    
    c.setFillColor(white)
    c.rect(0, 0, page_width, page_height, fill=True)
    
    c.setFillColor(purple)
    draw_centered_text(c, "Magic Memories Books", page_height/2 + 50, font_name, 20, page_width, purple)
    
    draw_centered_text(c, "www.magicmemoriesbooks.com", page_height/2 + 20, font_name, 12, page_width, purple)
    draw_centered_text(c, "info@magicmemoriesbooks.com", page_height/2 - 5, font_name, 12, page_width, purple)
    
    c.setFillColor(gray_text)
    if order.language == 'es':
        love_text = f"Creado con amor para {order.child_name}"
    else:
        love_text = f"Created with love for {order.child_name}"
    draw_centered_text(c, love_text, page_height/2 - 50, font_name, 11, page_width, gray_text)
    
    c.showPage()
    
    c.setFillColor(white)
    c.rect(0, 0, page_width, page_height, fill=True)
    
    c.setFillColor(purple)
    notes_title = "NOTAS / DIBUJA" if order.language == 'es' else "NOTES / DRAW"
    draw_centered_text(c, notes_title, page_height - 50, font_name, 22, page_width, purple)
    
    c.setFillColor(gray_text)
    subtitle = "¡Dibuja tu parte favorita del cuento!" if order.language == 'es' else "Draw your favorite part of the story!"
    draw_centered_text(c, subtitle, page_height - 80, font_name, 11, page_width, gray_text)
    
    c.setStrokeColor(light_gray)
    c.setLineWidth(0.5)
    for y in range(int(page_height - 100), 40, -25):
        c.line(35, y, page_width - 35, y)
    
    c.showPage()
    
    c.setFillColor(white)
    c.rect(0, 0, page_width, page_height, fill=True)
    c.showPage()
    
    if os.path.exists(BACK_COVER_PATH):
        try:
            back_img = Image.open(BACK_COVER_PATH)
            if back_img.mode != 'RGB':
                back_img = back_img.convert('RGB')
            img_buffer = BytesIO()
            back_img.save(img_buffer, format='JPEG', quality=95)
            img_buffer.seek(0)
            back_reader = ImageReader(img_buffer)
            c.drawImage(back_reader, 0, 0, width=page_width, height=page_height, preserveAspectRatio=True, anchor='c')
        except Exception as e:
            print(f"Error loading back cover: {e}")
            c.setFillColor(purple)
            c.rect(0, 0, page_width, page_height, fill=True)
    else:
        c.setFillColor(purple)
        c.rect(0, 0, page_width, page_height, fill=True)
    
    c.save()
    
    sanitize_pdf_with_ghostscript(output_path)
    
    return output_path


BABY_DEDICATION_BG = 'static/images/baby_dedication_bg.jpg'
BABY_BACK_COVER = 'static/images/back_cover.jpg'
QUICK_STORY_BACK_COVER = 'static/images/quick_story_back_cover.png'
NOTES_BACKGROUND = 'static/images/notes_background.jpg'
PRINT_BACK_COVER = 'static/images/back_cover.jpg'

DIGEST_SIZE = (5.5 * inch, 8.5 * inch)
BLEED = 3.18 * mm
BLEED_3MM = 3 * mm

DIGEST_WITH_BLEED = (5.5 * inch + (BLEED * 2), 8.5 * inch + (BLEED * 2))

BABY_PRINT_SIZE = 180 * mm  # 18 cm square format for baby books
BABY_PRINT_BLEED = 3 * mm
BABY_PRINT_WITH_BLEED = BABY_PRINT_SIZE + (BABY_PRINT_BLEED * 2)  # 186mm with bleed

QUICK_STORY_LULU_SIZE = 8.5 * inch  # 21.59cm square for Lulu saddle stitch
QUICK_STORY_LULU_BLEED = 0.125 * inch  # 1/8 inch bleed required by Lulu
QUICK_STORY_LULU_WITH_BLEED = QUICK_STORY_LULU_SIZE + (QUICK_STORY_LULU_BLEED * 2)
QUICK_STORY_LULU_SAFETY = 0.5 * inch  # safety margin for text


def generate_baby_cover_spread_pdf(front_cover_path, back_cover_path, output_path, skip_sanitize=False):
    """
    Generate a cover spread PDF for Lulu print-on-demand.
    Combines front cover + spine (0 for saddle-stitch) + back cover into one PDF page.
    
    For Digest size (5.5×8.5") with 3.18mm bleed:
    - Trim size: 5.5×8.5 inches each cover
    - With bleed: Each cover gets +3.18mm on all edges
    - Spine: ~0 for saddle-stitch (12 pages)
    
    Layout (left to right): Back Cover | Spine | Front Cover
    """
    TRIM_W = 5.5 * inch
    TRIM_H = 8.5 * inch
    SPINE_W = 0
    
    cover_w_with_bleed = TRIM_W + (BLEED * 2)
    cover_h_with_bleed = TRIM_H + (BLEED * 2)
    
    total_w = (cover_w_with_bleed * 2) + SPINE_W
    total_h = cover_h_with_bleed
    
    print(f"Cover spread PDF dimensions: {total_w/inch}\" x {total_h/inch}\"")
    
    c = canvas.Canvas(output_path, pagesize=(total_w, total_h))
    
    set_pdf_metadata(c, "Cover Spread - Magic Memories Books")
    
    if back_cover_path and os.path.exists(back_cover_path):
        try:
            back_img = Image.open(back_cover_path)
            if back_img.mode != 'RGB':
                back_img = back_img.convert('RGB')
            back_buffer = BytesIO()
            back_img.save(back_buffer, format='JPEG', quality=95)
            back_buffer.seek(0)
            c.drawImage(ImageReader(back_buffer), 0, 0, 
                       width=cover_w_with_bleed, height=cover_h_with_bleed,
                       preserveAspectRatio=True, anchor='c')
        except Exception as e:
            print(f"Error loading back cover: {e}")
    
    front_x = cover_w_with_bleed + SPINE_W
    
    if front_cover_path and os.path.exists(front_cover_path):
        try:
            front_img = Image.open(front_cover_path)
            if front_img.mode != 'RGB':
                front_img = front_img.convert('RGB')
            front_buffer = BytesIO()
            front_img.save(front_buffer, format='JPEG', quality=95)
            front_buffer.seek(0)
            c.drawImage(ImageReader(front_buffer), front_x, 0, 
                       width=cover_w_with_bleed, height=cover_h_with_bleed,
                       preserveAspectRatio=True, anchor='c')
        except Exception as e:
            print(f"Error loading front cover: {e}")
    
    c.save()
    
    if not skip_sanitize:
        sanitize_pdf_with_ghostscript(output_path)
    
    print(f"Cover spread PDF saved: {output_path}")
    
    return output_path


def create_quick_story_lulu_cover(front_cover_path, back_cover_path, output_path, skip_sanitize=False, title='', author=''):
    """
    Quick Story COVER SPREAD PDF for Lulu saddle stitch printing.
    No spine for saddle stitch - back cover + front cover side by side.
    
    Lulu template specs for 8.5" x 8.5" saddle stitch:
    - Trim size per cover: 8.5" x 8.5"
    - Bleed: 0.125" on outer edges only (no bleed between covers at fold)
    - Total spread: 17.25" x 8.75" (438.15mm x 222.25mm)
    - Safety margin: 0.5" from trim edge
    
    Layout: [Bleed 0.125"] [Back Cover 8.5"] [Front Cover 8.5"] [Bleed 0.125"]
    Height:  [Bleed 0.125"] [Cover 8.5"] [Bleed 0.125"]
    """
    cover_trim = QUICK_STORY_LULU_SIZE
    bleed = QUICK_STORY_LULU_BLEED
    
    total_w = bleed + cover_trim + cover_trim + bleed
    total_h = bleed + cover_trim + bleed
    
    back_w = bleed + cover_trim
    front_w = cover_trim + bleed
    
    print(f"[LULU QS COVER] Spread: {total_w/inch:.2f}\" x {total_h/inch:.2f}\" ({total_w:.1f} x {total_h:.1f} pt)")
    print(f"[LULU QS COVER] Expected: 17.25\" x 8.75\" (1242.0 x 630.0 pt)")
    
    c = canvas.Canvas(output_path, pagesize=(total_w, total_h))
    set_pdf_metadata(c, "Cover Spread - Magic Memories Books")
    
    back_dpi_w = int(back_w * 300 / 72)
    back_dpi_h = int(total_h * 300 / 72)
    front_dpi_w = int(front_w * 300 / 72)
    front_dpi_h = int(total_h * 300 / 72)
    
    if back_cover_path and os.path.exists(back_cover_path):
        try:
            back_img = Image.open(back_cover_path)
            if back_img.mode != 'RGB':
                back_img = back_img.convert('RGB')
            back_fitted = ImageOps.fit(back_img, (back_dpi_w, back_dpi_h), Image.Resampling.LANCZOS)
            back_buffer = BytesIO()
            back_fitted.save(back_buffer, format='JPEG', quality=95)
            back_buffer.seek(0)
            c.drawImage(ImageReader(back_buffer), 0, 0,
                       width=back_w, height=total_h)
        except Exception as e:
            print(f"[LULU QS COVER] Error loading back cover: {e}")
            c.setFillColor(HexColor('#FEF3C7'))
            c.rect(0, 0, back_w, total_h, fill=True)
    else:
        c.setFillColor(HexColor('#FEF3C7'))
        c.rect(0, 0, back_w, total_h, fill=True)
        font_name = register_fonts()
        c.setFillColor(HexColor('#D97706'))
        c.setFont(font_name, 16)
        c.drawCentredString(back_w / 2, total_h / 2, "Magic Memories Books")
    
    front_x = back_w
    
    if front_cover_path and os.path.exists(front_cover_path):
        try:
            front_img = Image.open(front_cover_path)
            if front_img.mode != 'RGB':
                front_img = front_img.convert('RGB')
            front_fitted = ImageOps.fit(front_img, (front_dpi_w, front_dpi_h), Image.Resampling.LANCZOS)
            front_buffer = BytesIO()
            front_fitted.save(front_buffer, format='JPEG', quality=95)
            front_buffer.seek(0)
            c.drawImage(ImageReader(front_buffer), front_x, 0,
                       width=front_w, height=total_h)
        except Exception as e:
            print(f"[LULU QS COVER] Error loading front cover: {e}")
            c.setFillColor(HexColor('#E8F4FD'))
            c.rect(front_x, 0, front_w, total_h, fill=True)
    else:
        c.setFillColor(HexColor('#E8F4FD'))
        c.rect(front_x, 0, front_w, total_h, fill=True)
    
    c.save()
    
    if not skip_sanitize:
        sanitize_pdf_with_ghostscript(output_path)
    
    print(f"[LULU QS COVER] Cover spread PDF saved: {output_path}")
    return output_path


QUICK_STORY_DIGITAL_SIZE = 8.5 * inch

def _draw_full_page_image(c, image_path, page_width, page_height):
    if image_path and os.path.exists(image_path):
        try:
            img = Image.open(image_path)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img_fitted = ImageOps.fit(img, (int(page_width * 300 / 72), int(page_height * 300 / 72)), Image.Resampling.LANCZOS)
            img_buffer = BytesIO()
            img_fitted.save(img_buffer, format='JPEG', quality=95)
            img_buffer.seek(0)
            c.drawImage(ImageReader(img_buffer), 0, 0, width=page_width, height=page_height)
            return True
        except Exception as e:
            print(f"[QS PDF] Error loading image {image_path}: {e}")
    return False


def _draw_cover_title_overlay(c, title, author, page_width, page_height, fonts):
    from reportlab.lib.colors import Color
    
    if not title:
        return
    
    title_font = fonts.get('title', fonts.get('dropcap', 'Helvetica'))
    author_font = fonts.get('body', 'Helvetica')
    
    title_size = 28
    title_y = page_height - 40
    
    pastel_purple = Color(0.71, 0.51, 0.82, alpha=1.0)
    white_border = Color(1, 1, 1, alpha=1.0)
    
    border_offsets = [(-2,0),(2,0),(0,-2),(0,2),(-1,-1),(1,-1),(-1,1),(1,1)]
    for dx, dy in border_offsets:
        c.saveState()
        c.setFillColor(white_border)
        c.setFont(title_font, title_size)
        c.drawCentredString(page_width / 2 + dx, title_y + dy, title)
        c.restoreState()
    
    c.setFillColor(pastel_purple)
    c.setFont(title_font, title_size)
    c.drawCentredString(page_width / 2, title_y, title)
    
    if author and author.strip():
        author_text = f"Autor: {author}"
        author_size = 14
        cm2_pts = 2 * 28.35
        author_y = cm2_pts
        author_purple = Color(0.63, 0.43, 0.75, alpha=0.9)
        
        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
            c.saveState()
            c.setFillColor(white_border)
            c.setFont(author_font, author_size)
            c.drawCentredString(page_width / 2 + dx, author_y + dy, author_text)
            c.restoreState()
        
        c.setFillColor(author_purple)
        c.setFont(author_font, author_size)
        c.drawCentredString(page_width / 2, author_y, author_text)


def _draw_gradient_box(c, x, y, w, h, radius=35):
    from PIL import Image, ImageDraw, ImageChops
    from reportlab.lib.utils import ImageReader
    import io
    
    scale = 4
    pw = int(w * scale)
    ph = int(h * scale)
    pr = int(radius * scale)
    
    rounded = Image.new('L', (pw, ph), 0)
    rd = ImageDraw.Draw(rounded)
    rd.rounded_rectangle([0, 0, pw - 1, ph - 1], radius=pr, fill=255)
    
    mask = Image.new('L', (pw, ph), 255)
    mask.paste(rounded.crop((0, ph // 2, pw, ph)), (0, ph // 2))
    
    white = Image.new('RGBA', (pw, ph), (255, 255, 255, 255))
    
    grad_strip = Image.new('L', (1, ph), 0)
    for row in range(ph):
        frac = row / ph
        if frac < 0.25:
            alpha = 0
        elif frac < 0.45:
            t = (frac - 0.25) / 0.20
            alpha = int(255 * 0.55 * (t ** 1.2))
        else:
            t = (frac - 0.45) / 0.55
            alpha = int(255 * (0.55 + 0.40 * (t ** 0.7)))
        grad_strip.putpixel((0, row), min(int(alpha), 242))
    grad_full = grad_strip.resize((pw, ph), Image.BILINEAR)
    
    alpha_gradient = ImageChops.multiply(grad_full, mask)
    
    white.putalpha(alpha_gradient)
    
    buf = io.BytesIO()
    white.save(buf, format='PNG')
    buf.seek(0)
    
    c.saveState()
    c.drawImage(ImageReader(buf), x, y, width=w, height=h, mask='auto')
    c.restoreState()


def _draw_text_overlay(c, text, page_width, page_height, fonts, language='es'):
    if not text or not text.strip():
        return
    
    from reportlab.lib.colors import Color
    
    body_font = 'Nunito-SemiBold'
    dropcap_font = 'Nunito-ExtraBold'
    try:
        c.stringWidth('T', body_font, 24)
    except Exception:
        body_font = fonts.get('body', 'Helvetica')
        dropcap_font = fonts.get('dropcap', 'Helvetica')
    
    body_size = 24
    dropcap_size = 52
    line_height = body_size * 1.3
    
    body_color = HexColor('#2d2c2c')
    dropcap_color = HexColor('#5e17eb')
    
    clean_text = text.replace('\n', ' ').strip()
    while '  ' in clean_text:
        clean_text = clean_text.replace('  ', ' ')
    
    if not clean_text:
        return
    
    first_char = clean_text[0].upper()
    rest_text = clean_text[1:]
    
    cm2 = 2 * 28.3465
    margin_side = cm2
    box_padding_h = 0.5 * 28.3465
    box_padding_v = 0.4 * 28.3465
    
    available_content_width = page_width - (margin_side * 2) - (box_padding_h * 2)
    
    dropcap_margin_right = dropcap_size * 0.05
    dropcap_width = c.stringWidth(first_char, dropcap_font, dropcap_size) + dropcap_margin_right
    dropcap_visual_height = dropcap_size * 0.8
    
    available_width_cap = available_content_width - dropcap_width
    available_width_full = available_content_width
    
    words = rest_text.split()
    
    dropcap_lines = max(2, int(dropcap_visual_height / line_height))
    
    cap_lines = []
    below_lines = []
    current_line = ""
    word_idx = 0
    
    while word_idx < len(words) and len(cap_lines) < dropcap_lines:
        word = words[word_idx]
        test = current_line + " " + word if current_line else word
        if c.stringWidth(test, body_font, body_size) < available_width_cap:
            current_line = test
            word_idx += 1
        else:
            if current_line:
                cap_lines.append(current_line)
                current_line = ""
            else:
                current_line = word
                word_idx += 1
    if current_line and len(cap_lines) < dropcap_lines:
        cap_lines.append(current_line)
        current_line = ""
    elif current_line:
        words_remaining = current_line.split() + [words[i] for i in range(word_idx, len(words))]
        current_line = ""
        for w in words_remaining:
            test = current_line + " " + w if current_line else w
            if c.stringWidth(test, body_font, body_size) < available_width_full:
                current_line = test
            else:
                if current_line:
                    below_lines.append(current_line)
                current_line = w
        if current_line:
            below_lines.append(current_line)
        word_idx = len(words)
    
    while word_idx < len(words):
        word = words[word_idx]
        test = current_line + " " + word if current_line else word
        if c.stringWidth(test, body_font, body_size) < available_width_cap:
            current_line = test
            word_idx += 1
        else:
            if current_line:
                below_lines.append(current_line)
            current_line = word
            word_idx += 1
    if current_line:
        below_lines.append(current_line)
    
    cap_area_height = max(dropcap_visual_height, len(cap_lines) * line_height)
    total_text_height = cap_area_height + len(below_lines) * line_height
    
    fade_extra = total_text_height * 0.9
    box_text_height = total_text_height + (box_padding_v * 2)
    box_height = box_text_height + fade_extra
    box_width = page_width - (margin_side * 2)
    
    box_x = margin_side
    box_y = cm2
    
    _draw_gradient_box(c, box_x, box_y, box_width, box_height, radius=35)
    
    text_left = box_x + box_padding_h
    text_center_x = box_x + box_width / 2
    
    text_top_y = box_y + box_text_height - box_padding_v
    first_line_y = text_top_y - body_size
    
    dropcap_x = text_left
    dropcap_y = first_line_y
    c.setFillColor(dropcap_color)
    c.setFont(dropcap_font, dropcap_size)
    c.drawString(dropcap_x, dropcap_y, first_char)
    
    c.setFillColor(body_color)
    c.setFont(body_font, body_size)
    
    for i, line in enumerate(cap_lines):
        line_x = text_left + dropcap_width
        line_y = first_line_y - (i * line_height)
        c.drawString(line_x, line_y, line.strip())
    
    below_left_x = text_left + dropcap_width
    below_start_y = first_line_y - cap_area_height
    for i, line in enumerate(below_lines):
        line_y = below_start_y - (i * line_height)
        c.drawString(below_left_x, line_y, line.strip())


def create_baby_quick_story_pdf(story_data, images, output_path, format_type='digital', skip_sanitize=False):
    """
    Create PDF for baby Quick Stories (0-2 years) - 12 PAGE LAYOUT.
    
    8.5" x 8.5" square format.
    Full-page illustrations with organic cloud-shaped text overlay (85% white).
    Drop cap in Nunito ExtraBold 60pt (#935efb lilac), body in Nunito SemiBold 25pt (#545454 gray).
    2cm margins, centered text below drop cap area.
    
    12 pages total (all formats):
    1. Cover (portada)
    2. Title page (portadilla)
    3. Dedication with decorative frame
    4-11. 8 scene illustrations with text overlay
    12. Back cover (contraportada fija)
    
    Lulu Interior PDF (10 pages, covers are separate):
    Saddle stitch covers go in separate cover spread PDF.
    Interior = pages 2-11 of the 12-page book:
    1. Title page (portadilla)
    2. Dedication with decorative frame
    3-10. 8 scene illustrations with text overlay
    """
    page_size = QUICK_STORY_DIGITAL_SIZE
    if format_type == 'lulu':
        page_size = QUICK_STORY_LULU_WITH_BLEED
    
    page_width = page_height = page_size
    c = canvas.Canvas(output_path, pagesize=(page_width, page_height))
    
    fonts = register_baby_book_fonts()
    child_name = story_data.get('child_name', 'Bebé')
    title = story_data.get('story_name', f'{child_name} y el mundo suave')
    language = story_data.get('lang', story_data.get('language', 'es'))
    dedication = story_data.get('dedication', '')
    if not dedication:
        dedication = f'Para {child_name},\ncon todo nuestro amor.' if language == 'es' else f'For {child_name},\nwith all our love.'
    
    set_pdf_metadata(c, f"{title} - {child_name}")
    
    if format_type != 'lulu':
        cover_image = story_data.get('cover_image', '')
        if cover_image and cover_image.startswith('/'):
            cover_image = cover_image[1:]
        
        if not _draw_full_page_image(c, cover_image, page_width, page_height):
            c.setFillColor(HexColor('#E8F4FD'))
            c.rect(0, 0, page_width, page_height, fill=True)
        
        c.showPage()
    
    c.setFillColor(HexColor('#FFFBF5'))
    c.rect(0, 0, page_width, page_height, fill=True)
    c.setFillColor(HexColor('#8B6914'))
    c.setFont(fonts.get('dropcap', 'Helvetica'), 32)
    c.drawCentredString(page_width / 2, page_height * 0.55, title)
    c.setFillColor(HexColor('#4A3728'))
    c.setFont(fonts.get('body', 'Helvetica'), 16)
    c.drawCentredString(page_width / 2, page_height * 0.42, "Magic Memories Books")
    c.showPage()
    
    c.setFillColor(HexColor('#FFFBF5'))
    c.rect(0, 0, page_width, page_height, fill=True)
    
    border_margin = page_width * 0.08
    border_width = page_width - (border_margin * 2)
    border_height = page_height - (border_margin * 2)
    
    c.saveState()
    c.setStrokeColor(HexColor('#D4A574'))
    c.setLineWidth(2)
    c.roundRect(border_margin, border_margin, border_width, border_height, 12, fill=False, stroke=True)
    
    inner_margin = border_margin + 8
    inner_w = border_width - 16
    inner_h = border_height - 16
    c.setStrokeColor(HexColor('#E8C9A0'))
    c.setLineWidth(1)
    c.roundRect(inner_margin, inner_margin, inner_w, inner_h, 8, fill=False, stroke=True)
    c.restoreState()
    
    ded_title = "Dedicatoria" if language == 'es' else "Dedication"
    c.setFillColor(HexColor('#8B6914'))
    c.setFont(fonts.get('dropcap', 'Helvetica'), 28)
    c.drawCentredString(page_width / 2, page_height * 0.72, ded_title)
    
    c.saveState()
    c.setStrokeColor(HexColor('#D4A574'))
    c.setLineWidth(1)
    ornament_y = page_height * 0.68
    c.line(page_width * 0.3, ornament_y, page_width * 0.7, ornament_y)
    c.restoreState()
    
    c.setFillColor(HexColor('#4A3728'))
    ded_lines = dedication.replace('\n', '|').split('|')
    ded_y = page_height * 0.58
    ded_line_height = 26
    ded_margin = 20 * mm
    ded_body_font = fonts.get('body', 'Helvetica')
    ded_font_size = 18
    ded_max_width = page_width - (ded_margin * 2)
    
    from reportlab.lib.utils import simpleSplit
    for line in ded_lines:
        stripped = line.strip()
        if not stripped:
            ded_y -= ded_line_height
            continue
        wrapped = simpleSplit(stripped, ded_body_font, ded_font_size, ded_max_width)
        for wline in wrapped:
            c.setFont(ded_body_font, ded_font_size)
            c.drawCentredString(page_width / 2, ded_y, wline)
            ded_y -= ded_line_height
    
    c.showPage()
    
    pages = story_data.get('pages', [])
    num_scenes = len(pages) if pages else 6
    
    for i in range(num_scenes):
        page = pages[i]
        
        img_path = None
        if i < len(images) and images[i]:
            img_path = images[i]
        
        if not _draw_full_page_image(c, img_path, page_width, page_height):
            c.setFillColor(HexColor('#FFFBF5'))
            c.rect(0, 0, page_width, page_height, fill=True)
        
        pass
        
        c.showPage()
    
    if format_type != 'lulu':
        back_cover = QUICK_STORY_BACK_COVER
        if not _draw_full_page_image(c, back_cover, page_width, page_height):
            c.setFillColor(HexColor('#FDF6E3'))
            c.rect(0, 0, page_width, page_height, fill=True)
            c.setFillColor(HexColor('#374151'))
            c.setFont(fonts.get('body', 'Helvetica'), 18)
            c.drawCentredString(page_width / 2, page_height / 2, "Magic Memories Books")
        c.showPage()
    
    c.save()
    
    if not skip_sanitize:
        sanitize_pdf_with_ghostscript(output_path)
    
    if format_type == 'lulu':
        page_count = 10
    else:
        page_count = 12
    print(f"[QS BABY PDF] Created {format_type} PDF: {output_path} ({page_count} pages, {num_scenes} scenes)")
    return output_path


KIDS_TEXT_BACKGROUND = 'static/images/text_background.jpg'


def _draw_kids_split_text_overlay(c, text_above, text_below, page_width, page_height, fonts, language='es'):
    from reportlab.lib.colors import Color
    
    body_font = fonts.get('body', 'Helvetica')
    dropcap_font = fonts.get('dropcap', 'Helvetica')
    body_size = 14
    dropcap_size = int(body_size * 2.5)
    line_height = body_size * 1.35
    
    padding_h = 18
    padding_v = 8
    margin_x = page_width * 0.06
    max_text_width = page_width * 0.82
    
    dropcap_margin_right = 4
    
    text_color = HexColor('#4a4a4a')
    dropcap_color = HexColor('#6a3d9a')
    bg_color = Color(1, 1, 1, alpha=0.75)
    
    def wrap_text(text, max_w, font, fsize):
        words = text.replace('\n', ' ').strip().split()
        lines = []
        current = ""
        for word in words:
            if not word.strip():
                continue
            test = current + " " + word if current else word
            if c.stringWidth(test, font, fsize) < max_w:
                current = test
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines
    
    def wrap_text_with_dropcap(text, max_w, font, fsize, dc_font, dc_size, dc_margin):
        clean = text.replace('\n', ' ').strip()
        if not clean:
            return [], [], ''
        
        first_char = clean[0].upper()
        rest = clean[1:]
        
        dc_width = c.stringWidth(first_char, dc_font, dc_size) + dc_margin
        available_cap = max_w - dc_width
        
        dc_visual_h = dc_size * 0.75
        dc_lines_count = max(int(dc_visual_h / fsize / 1.35), 1)
        
        words = rest.split()
        cap_lines = []
        below_lines = []
        current = ""
        idx = 0
        
        while idx < len(words) and len(cap_lines) < dc_lines_count:
            word = words[idx]
            test = current + " " + word if current else word
            if c.stringWidth(test, font, fsize) < available_cap:
                current = test
                idx += 1
            else:
                if current:
                    cap_lines.append(current)
                    current = ""
                else:
                    current = word
                    idx += 1
        if current and len(cap_lines) < dc_lines_count:
            cap_lines.append(current)
            current = ""
        elif current:
            remaining = current.split() + [words[i] for i in range(idx, len(words))]
            current = ""
            for w in remaining:
                test = current + " " + w if current else w
                if c.stringWidth(test, font, fsize) < max_w:
                    current = test
                else:
                    if current:
                        below_lines.append(current)
                    current = w
            if current:
                below_lines.append(current)
            idx = len(words)
        
        while idx < len(words):
            word = words[idx]
            test = current + " " + word if current else word
            if c.stringWidth(test, font, fsize) < max_w:
                current = test
                idx += 1
            else:
                if current:
                    below_lines.append(current)
                current = word
                idx += 1
        if current:
            below_lines.append(current)
        
        return cap_lines, below_lines, first_char
    
    if text_above and text_above.strip():
        cap_lines, extra_lines, first_char = wrap_text_with_dropcap(
            text_above, max_text_width, body_font, body_size, dropcap_font, dropcap_size, dropcap_margin_right
        )
        
        dc_width = c.stringWidth(first_char, dropcap_font, dropcap_size) + dropcap_margin_right
        total_lines = len(cap_lines) + len(extra_lines)
        box_content_h = total_lines * line_height + padding_v
        box_h = box_content_h + (padding_v * 2)
        box_w_content = max_text_width + (padding_h * 2)
        
        box_x = margin_x
        cm_1_5_top = 1.5 * 28.3465
        box_y = page_height - box_h - cm_1_5_top
        
        c.saveState()
        c.setFillColor(bg_color)
        c.roundRect(box_x, box_y, box_w_content, box_h, 8, fill=True, stroke=False)
        c.restoreState()
        
        text_left = box_x + padding_h
        first_line_y = box_y + box_h - padding_v - body_size
        
        dropcap_y = first_line_y
        c.setFillColor(dropcap_color)
        c.setFont(dropcap_font, dropcap_size)
        c.drawString(text_left, dropcap_y, first_char)
        
        c.setFillColor(text_color)
        c.setFont(body_font, body_size)
        for i, line in enumerate(cap_lines):
            line_x = text_left + dc_width
            line_y = first_line_y - (i * line_height)
            c.drawString(line_x, line_y, line.strip())
        
        extra_start_y = first_line_y - (len(cap_lines) * line_height)
        for i, line in enumerate(extra_lines):
            line_y = extra_start_y - (i * line_height)
            c.drawString(text_left, line_y, line.strip())
    
    if text_below and text_below.strip():
        below_lines = wrap_text(text_below, max_text_width, body_font, body_size)
        
        total_lines = len(below_lines)
        box_content_h = total_lines * line_height + padding_v
        box_h = box_content_h + (padding_v * 2)
        box_w_content = max_text_width + (padding_h * 2)
        
        cm_1_5 = 1.5 * 28.3465
        box_x = margin_x
        box_y = cm_1_5
        
        c.saveState()
        c.setFillColor(bg_color)
        c.roundRect(box_x, box_y, box_w_content, box_h, 8, fill=True, stroke=False)
        c.restoreState()
        
        text_left = box_x + padding_h
        first_line_y = box_y + box_h - padding_v - body_size
        
        c.setFillColor(text_color)
        c.setFont(body_font, body_size)
        for i, line in enumerate(below_lines):
            line_y = first_line_y - (i * line_height)
            c.drawString(text_left, line_y, line.strip())


def _draw_kids_title_page(c, title, child_name, page_width, page_height, fonts, language, author_name=''):
    """Draw portadilla (title page) using the decorative background frame."""
    title_bg_square = 'static/images/title_page_background_square.png'
    title_bg_fallback = 'static/images/title_page_background.png'
    if os.path.exists(title_bg_square):
        _draw_full_page_image(c, title_bg_square, page_width, page_height)
    elif os.path.exists(title_bg_fallback):
        _draw_full_page_image(c, title_bg_fallback, page_width, page_height)
    else:
        c.setFillColor(HexColor('#FFFEF5'))
        c.rect(0, 0, page_width, page_height, fill=True)

    title_font = fonts.get('dropcap', 'Helvetica')
    body_font = fonts.get('body', 'Helvetica')

    margin = 3 * 28.3465
    max_w = page_width - (margin * 2)

    title_size = 26
    while c.stringWidth(title, title_font, title_size) > max_w and title_size > 14:
        title_size -= 1

    c.setFillColor(HexColor('#2E1A47'))
    c.setFont(title_font, title_size)
    c.drawCentredString(page_width / 2, page_height * 0.55, title)

    subtitle = f"Una aventura de {child_name}" if language == 'es' else f"An adventure of {child_name}"
    c.setFillColor(HexColor('#8B4513'))
    sub_size = 16
    while c.stringWidth(subtitle, body_font, sub_size) > max_w and sub_size > 10:
        sub_size -= 1
    c.setFont(body_font, sub_size)
    c.drawCentredString(page_width / 2, page_height * 0.55 - title_size * 1.8, subtitle)

    if author_name:
        author_label = f"Autor: {author_name}" if language == 'es' else f"By: {author_name}"
    else:
        return
    c.setFillColor(HexColor('#6a3d9a'))
    author_size = 13
    while c.stringWidth(author_label, body_font, author_size) > max_w and author_size > 9:
        author_size -= 1
    c.setFont(body_font, author_size)
    c.drawCentredString(page_width / 2, page_height * 0.55 - title_size * 1.8 - sub_size * 2.5, author_label)


def _draw_kids_closing_page(c, closing_image, closing_message, page_width, page_height, fonts, language='es'):
    """Draw closing page with protagonist image and positive message."""
    if closing_image:
        img_path = closing_image
        if img_path.startswith('/'):
            img_path = img_path[1:]
        if os.path.exists(img_path):
            _draw_full_page_image(c, img_path, page_width, page_height)
        else:
            c.setFillColor(HexColor('#E8F4FD'))
            c.rect(0, 0, page_width, page_height, fill=True)
    else:
        c.setFillColor(HexColor('#E8F4FD'))
        c.rect(0, 0, page_width, page_height, fill=True)

    if closing_message:
        body_font = fonts.get('body', 'Helvetica')
        dropcap_font = fonts.get('dropcap', 'Helvetica')
        msg_size = 14
        sig_size = 10
        margin = 2.5 * 28.3465
        max_w = page_width - (margin * 2)

        words = closing_message.split()
        lines = []
        current_line = ""
        for word in words:
            test = current_line + " " + word if current_line else word
            if c.stringWidth(test, dropcap_font, msg_size) <= max_w:
                current_line = test
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)

        signature = "tus amigos de Magic Memories Books" if language == 'es' else "your friends at Magic Memories Books"
        sig_line_h = sig_size * 2.2

        total_text_h = len(lines) * (msg_size * 1.4) + sig_line_h
        box_padding = 14
        box_h = total_text_h + box_padding * 2
        box_y = page_height * 0.06
        box_x = margin - 10

        from reportlab.lib.colors import Color
        c.saveState()
        c.setFillColor(Color(1, 1, 1, alpha=0.75))
        c.roundRect(box_x, box_y, page_width - (box_x * 2), box_h, 10, fill=True, stroke=False)
        c.restoreState()

        c.setFillColor(HexColor('#2E1A47'))
        c.setFont(dropcap_font, msg_size)
        text_y = box_y + box_h - box_padding - msg_size * 0.3
        for line in lines:
            c.drawCentredString(page_width / 2, text_y, line)
            text_y -= msg_size * 1.4

        c.setFillColor(HexColor('#6a3d9a'))
        c.setFont(body_font, sig_size)
        sig_x = page_width - margin
        c.drawRightString(sig_x, text_y - sig_size * 0.3, signature)


def create_kids_quick_story_pdf(story_data, images, output_path, format_type='digital', skip_sanitize=False):
    """
    Create PDF for kids Quick Stories (3-8 years) - NEW LAYOUT.
    
    8.5" x 8.5" square format.
    Full-page illustrations with split text overlay (above + below).
    Drop cap aligned with first line top, 14pt body, Fredoka font.
    
    Digital PDF (12 pages - for email/download):
    1. Cover (portada - full image, no text overlay)
    2. Portadilla (title page with decorative frame)
    3. Dedication with decorative frame
    4-10. 7 scene illustrations with split text overlay
    11. Closing (protagonist image + message)
    12. Back cover (contraportada)
    
    Print PDF (12 pages - standard 8.5x8.5, with covers):
    1. Cover (portada - full image)
    2. Portadilla (title page)
    3. Dedication
    4-10. 7 scene illustrations with split text overlay
    11. Closing (protagonist image + message)
    12. Back cover (contraportada)
    
    Lulu Interior PDF (10 pages, covers are separate, with bleed):
    1. Portadilla (title page)
    2. Dedication
    3-9. 7 scene illustrations with split text overlay
    10. Closing (protagonist image + message)
    """
    page_size = QUICK_STORY_DIGITAL_SIZE
    if format_type == 'lulu':
        page_size = QUICK_STORY_LULU_WITH_BLEED
    
    page_width = page_height = page_size
    c = canvas.Canvas(output_path, pagesize=(page_width, page_height))
    
    fonts = register_baby_book_fonts()
    child_name = story_data.get('child_name', 'Niño')
    title = story_data.get('story_name', f'La Aventura de {child_name}')
    language = story_data.get('lang', story_data.get('language', 'es'))
    dedication = story_data.get('dedication', '')
    closing_image = story_data.get('closing_image', '')
    closing_message = story_data.get('closing_message', '')
    if not dedication:
        dedication = f'Para {child_name},\ncon todo nuestro amor.' if language == 'es' else f'For {child_name},\nwith all our love.'
    
    set_pdf_metadata(c, f"{title} - {child_name}")
    
    if format_type in ('digital', 'print'):
        cover_image = story_data.get('cover_image', '')
        if cover_image and cover_image.startswith('/'):
            cover_image = cover_image[1:]
        
        if not _draw_full_page_image(c, cover_image, page_width, page_height):
            c.setFillColor(HexColor('#E8F4FD'))
            c.rect(0, 0, page_width, page_height, fill=True)
        
        c.showPage()
    
    author_name = story_data.get('author_name', '')
    _draw_kids_title_page(c, title, child_name, page_width, page_height, fonts, language, author_name=author_name)
    c.showPage()
    
    c.setFillColor(HexColor('#FFFBF5'))
    c.rect(0, 0, page_width, page_height, fill=True)
    
    border_margin = 3 * 28.3465
    border_width = page_width - (border_margin * 2)
    border_height = page_height - (border_margin * 2)
    
    c.saveState()
    c.setStrokeColor(HexColor('#D4A574'))
    c.setLineWidth(2)
    c.roundRect(border_margin, border_margin, border_width, border_height, 12, fill=False, stroke=True)
    
    inner_margin = border_margin + 8
    inner_w = border_width - 16
    inner_h = border_height - 16
    c.setStrokeColor(HexColor('#E8D5B7'))
    c.setLineWidth(0.5)
    c.roundRect(inner_margin, inner_margin, inner_w, inner_h, 8, fill=False, stroke=True)
    c.restoreState()
    
    ded_font = fonts.get('body', 'Helvetica')
    ded_title_font = fonts.get('dropcap', 'Helvetica')
    
    ded_title = "Dedicatoria" if language == 'es' else "Dedication"
    c.setFillColor(HexColor('#6a3d9a'))
    c.setFont(ded_title_font, 22)
    c.drawCentredString(page_width / 2, page_height * 0.68, ded_title)
    
    c.setStrokeColor(HexColor('#D4A574'))
    c.setLineWidth(1)
    ornament_y = page_height * 0.66
    c.line(page_width * 0.3, ornament_y, page_width * 0.7, ornament_y)
    
    c.setFillColor(HexColor('#5a4a3a'))
    ded_text_margin = 3.5 * 28.3465
    max_ded_width = page_width - (ded_text_margin * 2)
    
    raw_lines = dedication.split('\n')
    wrapped_lines = []
    for raw_line in raw_lines:
        line_text = raw_line.strip()
        if not line_text:
            wrapped_lines.append('')
            continue
        words = line_text.split()
        current = ""
        for word in words:
            test = current + " " + word if current else word
            if c.stringWidth(test, ded_font, 16) <= max_ded_width:
                current = test
            else:
                if current:
                    wrapped_lines.append(current)
                current = word
        if current:
            wrapped_lines.append(current)
    
    ded_y = page_height * 0.58
    for line in wrapped_lines:
        c.setFont(ded_font, 16)
        c.drawCentredString(page_width / 2, ded_y, line)
        ded_y -= 28
    
    c.showPage()
    
    pages = story_data.get('pages', [])
    num_scenes = len(pages)
    
    for i in range(num_scenes):
        page = pages[i]
        
        if i < len(images) and os.path.exists(images[i]):
            _draw_full_page_image(c, images[i], page_width, page_height)
        else:
            c.setFillColor(HexColor('#FEFEFE'))
            c.rect(0, 0, page_width, page_height, fill=True)
        
        pass
        
        c.showPage()
    
    if closing_image:
        closing_img_path = closing_image
        if closing_img_path.startswith('/'):
            closing_img_path = closing_img_path[1:]
        if os.path.exists(closing_img_path):
            _draw_full_page_image(c, closing_img_path, page_width, page_height)
        c.showPage()
    
    if format_type in ('digital', 'print'):
        back_cover_path = story_data.get('back_cover_image', '')
        if not back_cover_path or not os.path.exists(back_cover_path):
            back_cover_path = QUICK_STORY_BACK_COVER
        if os.path.exists(back_cover_path):
            _draw_full_page_image(c, back_cover_path, page_width, page_height)
            c.showPage()
    
    c.save()
    
    if not skip_sanitize:
        sanitized = sanitize_pdf_with_ghostscript(output_path)
        if sanitized:
            output_path = sanitized
    
    return output_path


def create_birthday_pdf(story_data, images, output_path, format_type='digital', skip_sanitize=False):
    """
    Create PDF for birthday stories (0-2 years).
    
    Digital format (8 pages):
    1. Cover with illustration + title
    2-7. 6 illustrations with text (centered on page)
    7. Dedication page
    8. Back cover
    """
    page_width, page_height = A4
    c = canvas.Canvas(output_path, pagesize=A4)
    
    font_name = register_fonts()
    child_name = story_data.get('child_name', 'Bebé')
    title = story_data.get('story_name', f'Feliz Cumpleaños, {child_name}')
    author = story_data.get('author_name', '')
    dedication = story_data.get('dedication', f'Para {child_name},\ncon todo nuestro amor.')
    
    set_pdf_metadata(c, f"{title} - {child_name}")
    
    dark_blue = HexColor('#1E3A5F')
    dark_text = HexColor('#374151')
    white = HexColor('#FFFFFF')
    
    cover_image = story_data.get('cover_image', '')
    if cover_image and cover_image.startswith('/'):
        cover_image = cover_image[1:]
    
    if cover_image and os.path.exists(cover_image):
        try:
            img = Image.open(cover_image)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img_buffer = BytesIO()
            img.save(img_buffer, format='JPEG', quality=95)
            img_buffer.seek(0)
            c.drawImage(ImageReader(img_buffer), 0, 0, width=page_width, height=page_height, preserveAspectRatio=True, anchor='c')
        except Exception as e:
            print(f"Error loading cover image: {e}")
            c.setFillColor(HexColor('#FDF2F8'))
            c.rect(0, 0, page_width, page_height, fill=True)
    else:
        c.setFillColor(HexColor('#FDF2F8'))
        c.rect(0, 0, page_width, page_height, fill=True)
    
    title_font_size = 32
    c.setFont(font_name, title_font_size)
    
    title_lines = []
    max_title_width = page_width - 80
    words = title.split()
    current_line = ""
    
    for word in words:
        test_line = current_line + " " + word if current_line else word
        if c.stringWidth(test_line, font_name, title_font_size) < max_title_width:
            current_line = test_line
        else:
            if current_line:
                title_lines.append(current_line)
            current_line = word
    if current_line:
        title_lines.append(current_line)
    
    title_y = page_height - 50
    line_spacing = 38
    title_bg_height = len(title_lines) * line_spacing + 30
    title_bg_y = title_y - title_bg_height + line_spacing + 10
    
    c.setFillColor(HexColor('#FFFFFF'))
    c.setFillAlpha(0.85)
    c.roundRect(30, title_bg_y, page_width - 60, title_bg_height, 15, fill=True, stroke=False)
    c.setFillAlpha(1.0)
    
    c.setFillColor(dark_blue)
    c.setFont(font_name, title_font_size)
    for line in title_lines:
        c.drawCentredString(page_width / 2, title_y, line)
        title_y -= line_spacing
    
    if author:
        c.setFillColor(HexColor('#FFFFFF'))
        c.setFillAlpha(0.85)
        c.roundRect(page_width/2 - 120, 30, 240, 50, 10, fill=True, stroke=False)
        c.setFillAlpha(1.0)
        
        c.setFillColor(dark_text)
        c.setFont(font_name, 16)
        c.drawCentredString(page_width / 2, 50, author)
    
    c.showPage()
    
    pages = story_data.get('pages', [])
    
    for i in range(min(6, len(pages))):
        page = pages[i]
        
        c.setFillColor(HexColor('#FFFBF5'))
        c.rect(0, 0, page_width, page_height, fill=True)
        
        if i < len(images) and os.path.exists(images[i]):
            try:
                img = Image.open(images[i])
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                img_width = page_width - 60
                img_height = page_height * 0.50
                
                img_buffer = BytesIO()
                img.save(img_buffer, format='JPEG', quality=95)
                img_buffer.seek(0)
                
                img_x = (page_width - img_width) / 2
                img_y = page_height - img_height - 40
                
                c.drawImage(ImageReader(img_buffer), img_x, img_y, 
                           width=img_width, height=img_height, 
                           preserveAspectRatio=True, anchor='c')
            except Exception as e:
                print(f"Error loading image {images[i]}: {e}")
        
        text = page.get('text', '')
        text_lines = text.replace('\n', ' ').split(' ')
        c.setFillColor(dark_text)
        c.setFont(font_name, 16)
        
        wrapped_lines = []
        current_line = ""
        max_width = page_width - 80
        
        for word in text_lines:
            if not word.strip():
                continue
            test_line = current_line + " " + word if current_line else word
            if c.stringWidth(test_line, font_name, 16) < max_width:
                current_line = test_line
            else:
                if current_line:
                    wrapped_lines.append(current_line)
                current_line = word
        if current_line:
            wrapped_lines.append(current_line)
        
        line_height = 24
        num_lines = len(wrapped_lines)
        text_block_height = num_lines * line_height
        text_area_center = page_height * 0.22
        text_start_y = text_area_center + (text_block_height / 2) - line_height / 2
        
        for j, line in enumerate(wrapped_lines):
            c.drawCentredString(page_width / 2, text_start_y - j * line_height, line.strip())
        
        c.showPage()
    
    if os.path.exists(BABY_DEDICATION_BG):
        try:
            bg = Image.open(BABY_DEDICATION_BG)
            if bg.mode != 'RGB':
                bg = bg.convert('RGB')
            bg_buffer = BytesIO()
            bg.save(bg_buffer, format='JPEG', quality=95)
            bg_buffer.seek(0)
            c.drawImage(ImageReader(bg_buffer), 0, 0, width=page_width, height=page_height)
        except:
            c.setFillColor(HexColor('#FDF2F8'))
            c.rect(0, 0, page_width, page_height, fill=True)
    else:
        c.setFillColor(HexColor('#FDF2F8'))
        c.rect(0, 0, page_width, page_height, fill=True)
    
    c.setFillColor(dark_blue)
    c.setFont(font_name, 36)
    c.drawCentredString(page_width / 2, page_height * 0.75, "DEDICATORIA")
    
    c.setFillColor(dark_text)
    max_ded_width = page_width - 80
    draw_wrapped_centered_text(c, dedication, page_height / 2 + 30, max_ded_width, font_name, 18, 30, page_width, dark_text)
    
    c.showPage()
    
    if os.path.exists(BABY_BACK_COVER):
        try:
            back = Image.open(BABY_BACK_COVER)
            if back.mode != 'RGB':
                back = back.convert('RGB')
            back_buffer = BytesIO()
            back.save(back_buffer, format='JPEG', quality=95)
            back_buffer.seek(0)
            c.drawImage(ImageReader(back_buffer), 0, 0, width=page_width, height=page_height, preserveAspectRatio=True, anchor='c')
        except:
            c.setFillColor(HexColor('#FDF2F8'))
            c.rect(0, 0, page_width, page_height, fill=True)
    else:
        c.setFillColor(HexColor('#FDF2F8'))
        c.rect(0, 0, page_width, page_height, fill=True)
        c.setFillColor(dark_blue)
        c.setFont(font_name, 24)
        c.drawCentredString(page_width / 2, page_height / 2, "Magic Memories Books")
    
    c.save()
    
    if not skip_sanitize:
        sanitize_pdf_with_ghostscript(output_path)
    
    print(f"Birthday PDF created: {output_path}")
    return output_path


def create_birthday_printable_pdf(story_data, images, output_path, skip_sanitize=False):
    """
    Birthday story PRINTABLE PDF - 216mm x 216mm square format with 3mm bleed - 12 pages:
    
    1. Cover (portada with title and cover illustration)
    2. Blank page
    3-8. 6 illustrations with text (centered)
    9. Dedication page
    10. Blank page
    11. Notes page
    12. Back cover (contraportada)
    """
    page_size_with_bleed = BABY_PRINT_WITH_BLEED
    page_size = (page_size_with_bleed, page_size_with_bleed)
    
    c = canvas.Canvas(output_path, pagesize=page_size)
    
    page_width = page_size_with_bleed
    page_height = page_size_with_bleed
    
    safe_margin = BABY_PRINT_BLEED
    content_margin = safe_margin + 10 * mm
    
    font_name = register_fonts()
    child_name = story_data.get('child_name', 'Bebé')
    title = story_data.get('story_name', f'Feliz Cumpleaños, {child_name}')
    dedication = story_data.get('dedication', f'Para {child_name},\ncon todo nuestro amor.')
    language = story_data.get('lang', story_data.get('language', 'es'))
    
    set_pdf_metadata(c, f"{title} - Versión Imprimible")
    
    dark_blue = HexColor('#1E3A5F')
    dark_text = HexColor('#374151')
    white = HexColor('#FFFFFF')
    light_pink = HexColor('#FDF2F8')
    gray_text = HexColor('#6B7280')
    cream = HexColor('#FFFBF5')
    
    cover_image = story_data.get('cover_image', '')
    if cover_image and cover_image.startswith('/'):
        cover_image = cover_image[1:]
    
    if cover_image and os.path.exists(cover_image):
        try:
            img = Image.open(cover_image)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img_buffer = BytesIO()
            img.save(img_buffer, format='JPEG', quality=95)
            img_buffer.seek(0)
            c.drawImage(ImageReader(img_buffer), 0, 0, width=page_width, height=page_height, preserveAspectRatio=True, anchor='c')
        except Exception as e:
            print(f"Error loading cover image: {e}")
            c.setFillColor(light_pink)
            c.rect(0, 0, page_width, page_height, fill=True)
    else:
        c.setFillColor(light_pink)
        c.rect(0, 0, page_width, page_height, fill=True)
    
    c.setFont(font_name, 24)
    title_lines = []
    words = title.split()
    current_line = ""
    for word in words:
        test_line = current_line + " " + word if current_line else word
        if c.stringWidth(test_line, font_name, 24) < page_width - 40:
            current_line = test_line
        else:
            if current_line:
                title_lines.append(current_line)
            current_line = word
    if current_line:
        title_lines.append(current_line)
    
    line_spacing = 28
    title_bg_height = len(title_lines) * line_spacing + 20
    title_bg_y = page_height - title_bg_height - 15
    
    c.setFillColor(HexColor('#FFFFFF'))
    c.setFillAlpha(0.85)
    c.roundRect(20, title_bg_y, page_width - 40, title_bg_height, 12, fill=True, stroke=False)
    c.setFillAlpha(1.0)
    
    c.setFillColor(dark_blue)
    title_y = page_height - 35
    for line in title_lines:
        c.drawCentredString(page_width / 2, title_y, line)
        title_y -= line_spacing
    
    c.showPage()
    
    c.setFillColor(white)
    c.rect(0, 0, page_width, page_height, fill=True)
    c.showPage()
    
    pages = story_data.get('pages', [])
    
    for i in range(6):
        if os.path.exists(PRINTABLE_TEXT_BACKGROUND):
            try:
                bg = Image.open(PRINTABLE_TEXT_BACKGROUND)
                if bg.mode != 'RGB':
                    bg = bg.convert('RGB')
                bg_buffer = BytesIO()
                bg.save(bg_buffer, format='JPEG', quality=95)
                bg_buffer.seek(0)
                c.drawImage(ImageReader(bg_buffer), 0, 0, width=page_width, height=page_height, preserveAspectRatio=False)
            except Exception as e:
                print(f"Error loading printable background: {e}")
                c.setFillColor(cream)
                c.rect(0, 0, page_width, page_height, fill=True)
        else:
            c.setFillColor(cream)
            c.rect(0, 0, page_width, page_height, fill=True)
        
        if i < len(images):
            img_path = images[i]
            if img_path and os.path.exists(img_path):
                try:
                    img = Image.open(img_path)
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    
                    img_size = page_width - (content_margin * 2) - 20
                    img_height = page_height * 0.50
                    
                    img_buffer = BytesIO()
                    img.save(img_buffer, format='JPEG', quality=95)
                    img_buffer.seek(0)
                    
                    img_x = (page_width - img_size) / 2
                    img_y = page_height - img_height - content_margin - 30
                    
                    c.drawImage(ImageReader(img_buffer), img_x, img_y, 
                               width=img_size, height=img_height, 
                               preserveAspectRatio=True, anchor='c')
                except Exception as e:
                    print(f"[PRINTABLE PDF] Error loading image {img_path}: {e}")
            else:
                print(f"[PRINTABLE PDF] Image not found for page {i}: {img_path if img_path else 'empty path'}")
        else:
            print(f"[PRINTABLE PDF] No image in list for page {i}, images count: {len(images)}")
        
        if i < len(pages):
            text = pages[i].get('text', '')
            text_words = text.replace('\n', ' ').split()
            c.setFillColor(dark_text)
            c.setFont(font_name, 14)
            
            wrapped_lines = []
            current_line = ""
            max_width = page_width - (content_margin * 2)
            
            for word in text_words:
                if not word.strip():
                    continue
                test_line = current_line + " " + word if current_line else word
                if c.stringWidth(test_line, font_name, 14) < max_width:
                    current_line = test_line
                else:
                    if current_line:
                        wrapped_lines.append(current_line)
                    current_line = word
            if current_line:
                wrapped_lines.append(current_line)
            
            line_height = 20
            num_lines = min(len(wrapped_lines), 6)
            text_block_height = num_lines * line_height
            text_area_center = page_height * 0.20
            text_start_y = text_area_center + (text_block_height / 2) - line_height / 2
            
            for j, line in enumerate(wrapped_lines[:6]):
                c.drawCentredString(page_width / 2, text_start_y - j * line_height, line.strip())
        
        c.setFillColor(gray_text)
        c.setFont(font_name, 10)
        c.drawCentredString(page_width / 2, safe_margin + 10, str(i + 3))
        
        c.showPage()
    
    if os.path.exists(BABY_DEDICATION_BG):
        try:
            bg = Image.open(BABY_DEDICATION_BG)
            if bg.mode != 'RGB':
                bg = bg.convert('RGB')
            bg_buffer = BytesIO()
            bg.save(bg_buffer, format='JPEG', quality=95)
            bg_buffer.seek(0)
            c.drawImage(ImageReader(bg_buffer), 0, 0, width=page_width, height=page_height, preserveAspectRatio=False)
        except:
            c.setFillColor(light_pink)
            c.rect(0, 0, page_width, page_height, fill=True)
    else:
        c.setFillColor(light_pink)
        c.rect(0, 0, page_width, page_height, fill=True)
    
    c.setFillColor(dark_blue)
    c.setFont(font_name, 26)
    ded_title = "Dedicatoria" if language == 'es' else "Dedication"
    c.drawCentredString(page_width / 2, page_height * 0.75, ded_title)
    
    c.setStrokeColor(dark_blue)
    c.setLineWidth(1.5)
    c.line(page_width/2 - 50, page_height * 0.71, page_width/2 + 50, page_height * 0.71)
    
    c.setFillColor(dark_text)
    max_ded_width = page_width - 100
    draw_wrapped_centered_text(c, dedication, page_height * 0.55, max_ded_width, font_name, 14, 22, page_width, dark_text)
    
    c.setFillColor(gray_text)
    c.setFont(font_name, 10)
    c.drawCentredString(page_width / 2, safe_margin + 10, "9")
    
    c.showPage()
    
    if os.path.exists(NOTES_BACKGROUND):
        try:
            bg = Image.open(NOTES_BACKGROUND)
            if bg.mode != 'RGB':
                bg = bg.convert('RGB')
            bg_buffer = BytesIO()
            bg.save(bg_buffer, format='JPEG', quality=95)
            bg_buffer.seek(0)
            c.drawImage(ImageReader(bg_buffer), 0, 0, width=page_width, height=page_height, preserveAspectRatio=False)
        except:
            c.setFillColor(cream)
            c.rect(0, 0, page_width, page_height, fill=True)
    else:
        c.setFillColor(cream)
        c.rect(0, 0, page_width, page_height, fill=True)
    
    c.setFillColor(dark_blue)
    c.setFont(font_name, 28)
    notes_title = "Notas" if language == 'es' else "Notes"
    c.drawCentredString(page_width / 2, page_height - content_margin - 20, notes_title)
    
    c.setStrokeColor(HexColor('#E5E7EB'))
    c.setLineWidth(0.5)
    line_start_y = page_height - content_margin - 60
    line_spacing = 25
    line_width = page_width - (content_margin * 2)
    for i in range(12):
        y = line_start_y - (i * line_spacing)
        c.line(content_margin, y, content_margin + line_width, y)
    
    c.setFillColor(gray_text)
    c.setFont(font_name, 10)
    c.drawCentredString(page_width / 2, safe_margin + 10, "10")
    
    c.showPage()
    
    c.setFillColor(white)
    c.rect(0, 0, page_width, page_height, fill=True)
    c.setFillColor(gray_text)
    c.setFont(font_name, 10)
    c.drawCentredString(page_width / 2, safe_margin + 10, "11")
    c.showPage()
    
    if os.path.exists(PRINT_BACK_COVER):
        try:
            back = Image.open(PRINT_BACK_COVER)
            if back.mode != 'RGB':
                back = back.convert('RGB')
            back_buffer = BytesIO()
            back.save(back_buffer, format='JPEG', quality=95)
            back_buffer.seek(0)
            c.drawImage(ImageReader(back_buffer), 0, 0, width=page_width, height=page_height, preserveAspectRatio=True, anchor='c')
        except Exception as e:
            print(f"Error loading back cover: {e}")
            c.setFillColor(light_pink)
            c.rect(0, 0, page_width, page_height, fill=True)
    else:
        c.setFillColor(light_pink)
        c.rect(0, 0, page_width, page_height, fill=True)
        c.setFillColor(dark_text)
        c.setFont(font_name, 20)
        c.drawCentredString(page_width / 2, page_height / 2, "Magic Memories Books")
    
    c.save()
    
    if not skip_sanitize:
        sanitize_pdf_with_ghostscript(output_path)
    
    print(f"Birthday printable PDF created: {output_path}")
    return output_path


def generate_print_instructions_pdf(output_path, language='es'):
    """
    Generate a unified PDF with printing instructions for all Quick Stories
    and Birthday books (8.5" x 8.5" / 21.59 cm x 21.59 cm square format).
    """
    from reportlab.lib.pagesizes import A4
    
    page_width, page_height = A4
    c = canvas.Canvas(output_path, pagesize=A4)
    
    font_name = register_fonts()
    
    set_pdf_metadata(c, "Instrucciones de Impresión - Magic Memories Books")
    
    dark_text = HexColor('#374151')
    purple = HexColor('#7C3AED')
    gray = HexColor('#6B7280')
    
    c.setFillColor(HexColor('#F5F3FF'))
    c.rect(0, 0, page_width, page_height, fill=True)
    
    c.setFillColor(purple)
    c.setFont(font_name, 24)
    if language == 'es':
        c.drawCentredString(page_width / 2, page_height - 60, "Instrucciones de Impresión")
    else:
        c.drawCentredString(page_width / 2, page_height - 60, "Printing Instructions")
    
    c.setFillColor(dark_text)
    y = page_height - 120
    
    if language == 'es':
        instructions = [
            ("Especificaciones del Libro:", True),
            ("", False),
            ("• Tamaño final: 8.5\" x 8.5\" (21.59 cm x 21.59 cm) - Formato cuadrado", False),
            ("• Total de páginas: 12 páginas (incluye portada y contraportada)", False),
            ("• Formato: Cuadrado", False),
            ("• Encuadernación: Grapado (saddle stitch)", False),
            ("", False),
            ("Recomendaciones para la Imprenta:", True),
            ("", False),
            ("• Papel interior: Estucado brillante o mate 80# (120 g/m²)", False),
            ("• Portada y contraportada: Cartulina más gruesa (200-250 g/m²)", False),
            ("• Encuadernación: Grapado (saddle stitch)", False),
            ("• Perfil de color: CMYK", False),
            ("• Resolución: 300 DPI mínimo", False),
            ("• Imprimir a sangre completa (sin márgenes blancos)", False),
            ("", False),
            ("Estructura del PDF (12 páginas):", True),
            ("", False),
            ("Página 1: Portada (imagen de cubierta)", False),
            ("Página 2: Portadilla (página de título)", False),
            ("Página 3: Dedicatoria", False),
            ("Páginas 4-10: 7 escenas ilustradas con texto", False),
            ("Página 11: Ilustración de cierre con mensaje", False),
            ("Página 12: Contraportada", False),
            ("", False),
            ("Instrucciones de Armado:", True),
            ("", False),
            ("1. Imprima la página 1 (portada) y la página 12 (contraportada)", False),
            ("   en cartulina gruesa de 8.5\" x 8.5\"", False),
            ("2. Imprima las páginas 2-11 (interiores) a doble cara", False),
            ("   en papel 8.5\" x 8.5\"", False),
            ("3. Apile las páginas en orden numérico", False),
            ("4. Grape por el lomo (2-3 grapas en el centro)", False),
            ("5. Doble por la línea del lomo", False),
            ("", False),
            ("Notas Importantes:", True),
            ("", False),
            ("• Si su impresora no admite papel cuadrado, imprima en papel", False),
            ("  8.5\" x 11\" (carta) y recorte a 8.5\" x 8.5\"", False),
            ("• Para mejor calidad, use una imprenta profesional", False),
        ]
    else:
        instructions = [
            ("Book Specifications:", True),
            ("", False),
            ("• Final size: 8.5\" x 8.5\" (21.59 cm x 21.59 cm) - Square format", False),
            ("• Total pages: 12 pages (includes front and back covers)", False),
            ("• Format: Square", False),
            ("• Binding: Saddle stitch (stapled)", False),
            ("", False),
            ("Print Shop Recommendations:", True),
            ("", False),
            ("• Interior paper: Glossy or matte coated 80# (120 gsm)", False),
            ("• Covers: Heavier cardstock (200-250 gsm)", False),
            ("• Binding: Saddle stitch (stapled)", False),
            ("• Color profile: CMYK", False),
            ("• Resolution: 300 DPI minimum", False),
            ("• Print full bleed (no white margins)", False),
            ("", False),
            ("PDF Structure (12 pages):", True),
            ("", False),
            ("Page 1: Front cover", False),
            ("Page 2: Title page", False),
            ("Page 3: Dedication", False),
            ("Pages 4-10: 7 illustrated scenes with text", False),
            ("Page 11: Closing illustration with message", False),
            ("Page 12: Back cover", False),
            ("", False),
            ("Assembly Instructions:", True),
            ("", False),
            ("1. Print page 1 (front cover) and page 12 (back cover)", False),
            ("   on heavy cardstock, 8.5\" x 8.5\"", False),
            ("2. Print pages 2-11 (interiors) double-sided", False),
            ("   on 8.5\" x 8.5\" paper", False),
            ("3. Stack pages in numerical order", False),
            ("4. Staple along the spine (2-3 staples in the center)", False),
            ("5. Fold along the spine line", False),
            ("", False),
            ("Important Notes:", True),
            ("", False),
            ("• If your printer doesn't support square paper, print on", False),
            ("  8.5\" x 11\" (letter) paper and trim to 8.5\" x 8.5\"", False),
            ("• For best quality, use a professional print shop", False),
        ]
    
    for text, is_header in instructions:
        if is_header:
            c.setFont(font_name, 14)
            c.setFillColor(purple)
        else:
            c.setFont(font_name, 11)
            c.setFillColor(dark_text)
        
        if text:
            c.drawString(50, y, text)
        y -= 18
        
        if y < 50:
            c.showPage()
            c.setFillColor(HexColor('#F5F3FF'))
            c.rect(0, 0, page_width, page_height, fill=True)
            y = page_height - 50
    
    c.setFillColor(gray)
    c.setFont(font_name, 10)
    c.drawCentredString(page_width / 2, 30, "Magic Memories Books - www.magicmemoriesbooks.com")
    
    c.save()
    
    sanitize_pdf_with_ghostscript(output_path)
    
    print(f"Kids print instructions PDF created: {output_path}")
    return output_path


def create_pdf_from_images(image_paths, output_path, skip_sanitize=False):
    """
    Create PDF directly from pre-generated image files.
    
    This function simply converts images to PDF without any reconstruction.
    Use this when you have complete page images (including title, dedication, etc.)
    already generated as PNG/JPG files.
    
    Args:
        image_paths: List of paths to image files (in page order)
        output_path: Output PDF path
        skip_sanitize: If True, skip Ghostscript sanitization
    
    Returns:
        Output path
    """
    from PIL import Image
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    page_width, page_height = A4
    c = canvas.Canvas(output_path, pagesize=A4)
    
    set_pdf_metadata(c, "Magic Memories Book")
    
    for i, img_path in enumerate(image_paths):
        path = img_path.lstrip('/') if img_path.startswith('/') else img_path
        
        if not os.path.exists(path):
            print(f"[PDF] Warning: Image not found: {path}")
            c.setFillColor(HexColor('#FFFEF5'))
            c.rect(0, 0, page_width, page_height, fill=True)
        else:
            try:
                img = Image.open(path)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                img_buffer = BytesIO()
                img.save(img_buffer, format='JPEG', quality=95)
                img_buffer.seek(0)
                c.drawImage(ImageReader(img_buffer), 0, 0, width=page_width, height=page_height, preserveAspectRatio=True, anchor='c')
            except Exception as e:
                print(f"[PDF] Error loading image {path}: {e}")
                c.setFillColor(HexColor('#FFFEF5'))
                c.rect(0, 0, page_width, page_height, fill=True)
        
        if i < len(image_paths) - 1:
            c.showPage()
    
    c.save()
    
    if not skip_sanitize:
        sanitize_pdf_with_ghostscript(output_path)
    
    print(f"[PDF] Created from {len(image_paths)} images: {output_path}")
    return output_path


def create_illustrated_book_pdf(story_data, scene_paths, output_path, format_type='digital', skip_sanitize=False):
    """
    Create PDF for illustrated book (dragon_garden_illustrated) using fixed scene images.
    
    Structure (24 pages for print):
    1. Title page
    2. Dedication
    3-21. 19 content pages (illustration + text overlay)
    22. Closing page
    23. Credits
    24. Blank (print only)
    """
    page_width, page_height = A4
    c = canvas.Canvas(output_path, pagesize=A4)
    
    font_name = register_fonts()
    child_name = story_data.get('child_name', 'Niño')
    title = story_data.get('title', story_data.get('story_name', f'El Jardín del Dragón'))
    author = story_data.get('author_name', 'Tu familia')
    dedication = story_data.get('dedication', f'Para {child_name}, con todo el amor del mundo.\nQue cada página te recuerde lo especial que eres.')
    lang = story_data.get('lang', 'es')
    
    set_pdf_metadata(c, f"{title} - {child_name}")
    
    from services.fixed_stories import STORIES
    story_id = story_data.get('story_id', 'dragon_garden_illustrated')
    story_config = STORIES.get(story_id, {})
    content_pages = story_config.get('content_pages', [])
    scenes_dir = story_config.get('scenes_dir', 'static/assets/dragon_garden_scenes')
    
    dark_blue = HexColor('#2E1A47')
    cream = HexColor('#FFFEF5')
    
    c.setFillColor(cream)
    c.rect(0, 0, page_width, page_height, fill=True)
    
    c.setFillColor(dark_blue)
    c.setFont(font_name, 48)
    c.drawCentredString(page_width / 2, page_height / 2 + 50, title.replace('{name}', child_name))
    c.setFont(font_name, 24)
    subtitle = f"Una aventura de {child_name}" if lang == 'es' else f"An adventure of {child_name}"
    c.drawCentredString(page_width / 2, page_height / 2 - 10, subtitle)
    if author:
        c.setFont(font_name, 18)
        by_text = "Por" if lang == 'es' else "By"
        c.drawCentredString(page_width / 2, 80, f"{by_text} {author}")
    c.showPage()
    
    # Dedication page with decorative frame
    dedication_bg = 'static/images/dedication_page_background.png'
    if os.path.exists(dedication_bg):
        try:
            ded_img = Image.open(dedication_bg)
            if ded_img.mode != 'RGB':
                ded_img = ded_img.convert('RGB')
            ded_buffer = BytesIO()
            ded_img.save(ded_buffer, format='JPEG', quality=95)
            ded_buffer.seek(0)
            c.drawImage(ImageReader(ded_buffer), 0, 0, width=page_width, height=page_height)
        except Exception as e:
            print(f"Error loading dedication background: {e}")
            c.setFillColor(cream)
            c.rect(0, 0, page_width, page_height, fill=True)
    else:
        c.setFillColor(cream)
        c.rect(0, 0, page_width, page_height, fill=True)
    
    # Draw dedication title
    c.setFillColor(dark_blue)
    c.setFont(font_name, 28)
    ded_title = "Dedicatoria" if lang == 'es' else "Dedication"
    c.drawCentredString(page_width / 2, page_height * 0.68, ded_title)
    
    # Draw dedication text with word wrap
    max_ded_width = page_width - (4.5 * 28.3465 * 2)
    draw_wrapped_centered_text(c, dedication, page_height * 0.58, max_ded_width, font_name, 18, 30, page_width, dark_blue)
    c.showPage()
    
    # Use dynamic scene_paths if available, otherwise fall back to fixed scenes
    use_dynamic_scenes = scene_paths and len(scene_paths) > 0
    num_scenes = len(scene_paths) if use_dynamic_scenes else len(content_pages)
    
    for i in range(num_scenes):
        # Get scene path - prefer dynamic paths
        if use_dynamic_scenes and i < len(scene_paths):
            scene_path = scene_paths[i]
            if scene_path.startswith('/'):
                scene_path = scene_path[1:]
        else:
            page_config = content_pages[i] if i < len(content_pages) else {}
            scene_file = page_config.get('fixed_scene', '')
            scene_path = f"{scenes_dir}/{scene_file}"
            if scene_path.startswith('/'):
                scene_path = scene_path[1:]
        
        if os.path.exists(scene_path):
            try:
                img = Image.open(scene_path)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                img_buffer = BytesIO()
                img.save(img_buffer, format='JPEG', quality=95)
                img_buffer.seek(0)
                c.drawImage(ImageReader(img_buffer), 0, 0, width=page_width, height=page_height, preserveAspectRatio=True, anchor='c')
            except Exception as e:
                print(f"Error loading scene {i+1}: {e}")
                c.setFillColor(cream)
                c.rect(0, 0, page_width, page_height, fill=True)
        else:
            print(f"Scene not found: {scene_path}")
            c.setFillColor(cream)
            c.rect(0, 0, page_width, page_height, fill=True)
        
        # Images already have text embedded from add_text_split() during generation
        # No additional text overlay needed here
        
        c.showPage()
    
    # Only add separate closing page if scene_paths doesn't already include it (< 20 elements)
    if num_scenes < 20:
        closing_scene = story_config.get('closing_scene', 'scene_final_sleeping.png')
        closing_path = f"{scenes_dir}/{closing_scene}"
        if os.path.exists(closing_path):
            try:
                img = Image.open(closing_path)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                img_buffer = BytesIO()
                img.save(img_buffer, format='JPEG', quality=95)
                img_buffer.seek(0)
                c.drawImage(ImageReader(img_buffer), 0, 0, width=page_width, height=page_height, preserveAspectRatio=True, anchor='c')
            except Exception as e:
                print(f"Error loading closing scene: {e}")
        c.showPage()
    
    c.setFillColor(cream)
    c.rect(0, 0, page_width, page_height, fill=True)
    c.setFillColor(dark_blue)
    c.setFont(font_name, 14)
    credits_text = "Creado con amor por Magic Memories Books" if lang == 'es' else "Created with love by Magic Memories Books"
    c.drawCentredString(page_width / 2, page_height / 2, credits_text)
    c.setFont(font_name, 10)
    c.drawCentredString(page_width / 2, page_height / 2 - 30, "www.magicmemoriesbooks.com")
    c.showPage()
    
    if format_type == 'print':
        c.setFillColor(cream)
        c.rect(0, 0, page_width, page_height, fill=True)
        c.showPage()
    
    c.save()
    
    if not skip_sanitize:
        sanitize_pdf_with_ghostscript(output_path)
    
    print(f"Illustrated book PDF created: {output_path} ({format_type})")
    return output_path