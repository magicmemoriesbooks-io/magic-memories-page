import os
import math
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

FONT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'static', 'fonts')

def _load_font(name, size):
    font_map = {
        'nunito_semibold': 'Nunito-SemiBold.ttf',
        'nunito_extrabold': 'Nunito-ExtraBold.ttf',
        'fredoka': 'Fredoka-Regular.ttf',
        'garamond': 'EBGaramond-Regular.ttf',
    }
    filename = font_map.get(name, name)
    path = os.path.join(FONT_DIR, filename)
    if os.path.exists(path):
        return ImageFont.truetype(path, size)
    for fallback in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]:
        if os.path.exists(fallback):
            return ImageFont.truetype(fallback, size)
    return ImageFont.load_default()


def _wrap_text(draw, text, font, max_width):
    words = text.replace('\n', ' ').strip().split()
    lines = []
    current = ""
    for word in words:
        if not word.strip():
            continue
        test = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _draw_rounded_rect_alpha(img, x, y, w, h, radius, color, alpha):
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    r, g, b = color
    od.rounded_rectangle([x, y, x + w, y + h], radius=radius, fill=(r, g, b, alpha))
    return Image.alpha_composite(img, overlay)


def compose_baby_text_on_image(image, text, language='es'):
    if not text or not text.strip():
        return image

    result = image.convert('RGBA')
    img_w, img_h = result.size

    body_font = _load_font('nunito_semibold', int(img_h * 0.032))
    dropcap_font = _load_font('nunito_extrabold', int(img_h * 0.07))

    body_size = int(img_h * 0.032)
    dropcap_size = int(img_h * 0.07)
    line_height = int(body_size * 1.3)

    body_color = (45, 44, 44)
    dropcap_color = (94, 23, 235)

    clean_text = text.replace('\n', ' ').strip()
    while '  ' in clean_text:
        clean_text = clean_text.replace('  ', ' ')
    if not clean_text:
        return image

    first_char = clean_text[0].upper()
    rest_text = clean_text[1:]

    margin_side = int(img_w * 0.093)
    box_padding_h = int(img_w * 0.023)
    box_padding_v = int(img_h * 0.019)

    available_content_width = img_w - (margin_side * 2) - (box_padding_h * 2)

    temp_draw = ImageDraw.Draw(result)
    dc_bbox = temp_draw.textbbox((0, 0), first_char, font=dropcap_font)
    dropcap_width = (dc_bbox[2] - dc_bbox[0]) + int(dropcap_size * 0.05)
    dropcap_visual_height = int(dropcap_size * 0.8)

    available_width_cap = available_content_width - dropcap_width

    words = rest_text.split()
    dropcap_lines_count = max(2, int(dropcap_visual_height / line_height))

    cap_lines = []
    below_lines = []
    current_line = ""
    word_idx = 0

    while word_idx < len(words) and len(cap_lines) < dropcap_lines_count:
        word = words[word_idx]
        test = f"{current_line} {word}".strip()
        bbox = temp_draw.textbbox((0, 0), test, font=body_font)
        tw = bbox[2] - bbox[0]
        if tw < available_width_cap:
            current_line = test
            word_idx += 1
        else:
            if current_line:
                cap_lines.append(current_line)
                current_line = ""
            else:
                current_line = word
                word_idx += 1
    if current_line and len(cap_lines) < dropcap_lines_count:
        cap_lines.append(current_line)
        current_line = ""
    elif current_line:
        remaining = current_line.split() + [words[i] for i in range(word_idx, len(words))]
        current_line = ""
        for w in remaining:
            test = f"{current_line} {w}".strip()
            bbox = temp_draw.textbbox((0, 0), test, font=body_font)
            if bbox[2] - bbox[0] < available_content_width:
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
        test = f"{current_line} {word}".strip()
        bbox = temp_draw.textbbox((0, 0), test, font=body_font)
        if bbox[2] - bbox[0] < available_width_cap:
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

    fade_extra = int(total_text_height * 0.9)
    box_text_height = total_text_height + (box_padding_v * 2)
    box_height = box_text_height + fade_extra
    box_width = img_w - (margin_side * 2)

    box_x = margin_side
    box_y = img_h - int(img_h * 0.093) - box_height

    gradient = Image.new('RGBA', (img_w, img_h), (0, 0, 0, 0))
    grad_draw = ImageDraw.Draw(gradient)

    radius = int(img_w * 0.034)

    mask = Image.new('L', (box_width, box_height), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([0, 0, box_width - 1, box_height - 1], radius=radius, fill=255)

    for row in range(box_height):
        frac = row / box_height
        if frac < 0.25:
            alpha = 0
        elif frac < 0.45:
            t = (frac - 0.25) / 0.20
            alpha = int(255 * 0.55 * (t ** 1.2))
        else:
            t = (frac - 0.45) / 0.55
            alpha = int(255 * (0.55 + 0.40 * (t ** 0.7)))
        alpha = min(alpha, 242)

        for col in range(box_width):
            if mask.getpixel((col, row)) > 0:
                gradient.putpixel((box_x + col, box_y + row), (255, 255, 255, alpha))

    result = Image.alpha_composite(result, gradient)
    draw = ImageDraw.Draw(result)

    text_left = box_x + box_padding_h
    text_top_y = box_y + box_height - box_text_height + box_padding_v
    first_line_y = text_top_y

    draw.text((text_left, first_line_y), first_char, font=dropcap_font, fill=dropcap_color)

    for i, line in enumerate(cap_lines):
        line_x = text_left + dropcap_width
        line_y = first_line_y + int(dropcap_size * 0.15) + (i * line_height)
        draw.text((line_x, line_y), line.strip(), font=body_font, fill=body_color)

    below_start_y = first_line_y + int(dropcap_size * 0.15) + cap_area_height
    below_left_x = text_left + dropcap_width
    for i, line in enumerate(below_lines):
        line_y = below_start_y + (i * line_height)
        draw.text((below_left_x, line_y), line.strip(), font=body_font, fill=body_color)

    return result.convert('RGB')


def _generate_deckled_mask(width, height, seed=42):
    rng = random.Random(seed)
    mask = Image.new('L', (width, height), 255)
    draw = ImageDraw.Draw(mask)

    edge_depth = max(4, int(min(width, height) * 0.015))
    freq = max(3, int(min(width, height) * 0.008))

    for edge_side in range(4):
        if edge_side == 0:
            length = width
        elif edge_side == 1:
            length = width
        elif edge_side == 2:
            length = height
        else:
            length = height

        points = []
        num_points = max(8, length // freq)
        for i in range(num_points + 1):
            t = i / num_points
            offset = rng.gauss(0, edge_depth * 0.5)
            offset = max(-edge_depth, min(edge_depth, offset))
            points.append((t, offset))

        for i in range(len(points) - 1):
            t1, o1 = points[i]
            t2, o2 = points[i + 1]
            steps = max(2, int((t2 - t1) * length))
            for s in range(steps):
                frac = s / steps
                t = t1 + (t2 - t1) * frac
                o = o1 + (o2 - o1) * frac

                if edge_side == 0:
                    px = int(t * (width - 1))
                    clear_depth = max(0, int(abs(o)))
                    for dy in range(clear_depth):
                        if 0 <= px < width and dy < height:
                            mask.putpixel((px, dy), 0)
                elif edge_side == 1:
                    px = int(t * (width - 1))
                    clear_depth = max(0, int(abs(o)))
                    for dy in range(clear_depth):
                        py = height - 1 - dy
                        if 0 <= px < width and 0 <= py:
                            mask.putpixel((px, py), 0)
                elif edge_side == 2:
                    py = int(t * (height - 1))
                    clear_depth = max(0, int(abs(o)))
                    for dx in range(clear_depth):
                        if dx < width and 0 <= py < height:
                            mask.putpixel((dx, py), 0)
                else:
                    py = int(t * (height - 1))
                    clear_depth = max(0, int(abs(o)))
                    for dx in range(clear_depth):
                        px_val = width - 1 - dx
                        if 0 <= px_val and 0 <= py < height:
                            mask.putpixel((px_val, py), 0)

    mask = mask.filter(ImageFilter.GaussianBlur(radius=1))
    return mask


def _generate_parchment_texture(width, height, seed=42):
    rng = random.Random(seed)

    target_alpha = 128

    base_r, base_g, base_b = 255, 253, 230
    texture = Image.new('RGBA', (width, height), (base_r, base_g, base_b, 255))

    noise = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    noise_draw = ImageDraw.Draw(noise)
    step = max(2, int(min(width, height) * 0.008))
    for y_pos in range(0, height, step):
        for x_pos in range(0, width, step):
            variation = rng.randint(-8, 8)
            nr = max(0, min(255, base_r + variation))
            ng = max(0, min(255, base_g + variation - 2))
            nb = max(0, min(255, base_b + variation - 4))
            noise_draw.rectangle([x_pos, y_pos, x_pos + step, y_pos + step], fill=(nr, ng, nb, 255))

    noise = noise.filter(ImageFilter.GaussianBlur(radius=step))
    texture = Image.alpha_composite(texture, noise)

    stain_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    stain_draw = ImageDraw.Draw(stain_layer)
    num_stains = rng.randint(2, 4)
    for _ in range(num_stains):
        sx = rng.randint(int(width * 0.1), int(width * 0.9))
        sy = rng.randint(int(height * 0.1), int(height * 0.9))
        sr = rng.randint(int(min(width, height) * 0.05), int(min(width, height) * 0.15))
        stain_draw.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=(200, 175, 120, 18))
    stain_layer = stain_layer.filter(ImageFilter.GaussianBlur(radius=sr // 2))
    texture = Image.alpha_composite(texture, stain_layer)

    mask = _generate_deckled_mask(width, height, seed=seed)
    r, g, b, a = texture.split()
    uniform_alpha = Image.new('L', (width, height), target_alpha)
    a = ImageChops.multiply(uniform_alpha, mask.convert('L'))
    texture = Image.merge('RGBA', (r, g, b, a))

    return texture


def _draw_parchment_with_texture(img, x, y, w, h, shadow_offset_px, blur_radius_px, seed=42):
    parchment_tex = _generate_parchment_texture(w, h, seed=seed)

    _, _, _, parch_alpha = parchment_tex.split()

    shadow_base = Image.new('L', img.size, 0)
    shadow_base.paste(parch_alpha, (x + shadow_offset_px, y + shadow_offset_px))
    shadow_base = shadow_base.filter(ImageFilter.GaussianBlur(radius=blur_radius_px))

    shadow_layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
    shadow_color = Image.new('RGBA', img.size, (0, 0, 0, 38))
    shadow_layer = Image.composite(shadow_color, shadow_layer, shadow_base)
    img = Image.alpha_composite(img, shadow_layer)

    parchment_layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
    parchment_layer.paste(parchment_tex, (x, y))
    img = Image.alpha_composite(img, parchment_layer)

    return img


def compose_kids_text_on_image(image, text_above, text_below, language='es'):
    if (not text_above or not text_above.strip()) and (not text_below or not text_below.strip()):
        return image

    result = image.convert('RGBA')
    img_w, img_h = result.size

    scale = img_w / 2550.0

    body_size = max(12, int(66 * scale))
    line_height = int(body_size * 1.4)

    body_font = _load_font('fredoka', body_size)

    padding_inner = max(6, int(35 * scale))
    margin_safe = max(8, int(150 * scale))

    parchment_w = img_w - (margin_safe * 2)
    parchment_x = margin_safe
    content_w = parchment_w - (padding_inner * 2)

    shadow_offset = max(2, int(5 * scale))
    blur_radius = max(2, int(12 * scale))

    text_color = (44, 44, 44)

    temp_draw = ImageDraw.Draw(result)

    if text_above and text_above.strip():
        clean = text_above.replace('\n', ' ').strip()
        while '  ' in clean:
            clean = clean.replace('  ', ' ')

        first_char = clean[0].upper()
        rest = clean[1:]

        all_lines_full = _wrap_text(temp_draw, clean, body_font, content_w)
        total_lines = len(all_lines_full)

        dc_lines_count = min(total_lines, 3)
        dc_font_size = max(body_size, int(dc_lines_count * line_height * 0.85))
        dropcap_font = _load_font('fredoka', dc_font_size)

        dc_bbox = temp_draw.textbbox((0, 0), first_char, font=dropcap_font)
        dc_render_w = dc_bbox[2] - dc_bbox[0]
        dc_render_h = dc_bbox[3] - dc_bbox[1]
        dc_top_bearing = dc_bbox[1]

        dc_target_h = dc_lines_count * line_height
        if dc_render_h < dc_target_h * 0.7 or dc_render_h > dc_target_h * 1.1:
            dc_font_size = int(dc_font_size * dc_target_h / max(dc_render_h, 1))
            dropcap_font = _load_font('fredoka', dc_font_size)
            dc_bbox = temp_draw.textbbox((0, 0), first_char, font=dropcap_font)
            dc_render_w = dc_bbox[2] - dc_bbox[0]
            dc_render_h = dc_bbox[3] - dc_bbox[1]
            dc_top_bearing = dc_bbox[1]

        dc_margin_right = max(4, int(15 * scale))
        dc_total_w = dc_render_w + dc_margin_right

        available_cap_w = content_w - dc_total_w

        words = rest.split()
        cap_lines = []
        extra_lines = []
        current = ""
        idx = 0

        while idx < len(words) and len(cap_lines) < dc_lines_count:
            word = words[idx]
            test = f"{current} {word}".strip()
            bbox = temp_draw.textbbox((0, 0), test, font=body_font)
            if bbox[2] - bbox[0] <= available_cap_w:
                current = test
                idx += 1
            else:
                if current:
                    cap_lines.append(current)
                    current = ""
                else:
                    cap_lines.append(word)
                    idx += 1
        if current:
            if len(cap_lines) < dc_lines_count:
                cap_lines.append(current)
            else:
                for w in current.split():
                    extra_lines_temp = w
                    break
                remaining_words = current.split() + [words[i] for i in range(idx, len(words))]
                current = ""
                for w in remaining_words:
                    test = f"{current} {w}".strip()
                    bbox = temp_draw.textbbox((0, 0), test, font=body_font)
                    if bbox[2] - bbox[0] <= content_w:
                        current = test
                    else:
                        if current:
                            extra_lines.append(current)
                        current = w
                if current:
                    extra_lines.append(current)
                idx = len(words)
            current = ""

        while idx < len(words):
            word = words[idx]
            test = f"{current} {word}".strip()
            bbox = temp_draw.textbbox((0, 0), test, font=body_font)
            if bbox[2] - bbox[0] <= content_w:
                current = test
                idx += 1
            else:
                if current:
                    extra_lines.append(current)
                current = word
                idx += 1
        if current:
            extra_lines.append(current)

        actual_dc_lines = len(cap_lines)
        if actual_dc_lines < dc_lines_count:
            dc_lines_count = actual_dc_lines
            dc_target_h = dc_lines_count * line_height
            dc_font_size = max(body_size, int(dc_target_h * 0.85))
            dropcap_font = _load_font('fredoka', dc_font_size)
            dc_bbox = temp_draw.textbbox((0, 0), first_char, font=dropcap_font)
            dc_render_w = dc_bbox[2] - dc_bbox[0]
            dc_render_h = dc_bbox[3] - dc_bbox[1]
            dc_top_bearing = dc_bbox[1]

        cap_area_h = dc_lines_count * line_height
        total_text_h = cap_area_h + len(extra_lines) * line_height
        parchment_h = total_text_h + (padding_inner * 2)

        parchment_y = margin_safe

        result = _draw_parchment_with_texture(
            result, parchment_x, parchment_y, parchment_w, parchment_h,
            shadow_offset, blur_radius, seed=42
        )
        draw = ImageDraw.Draw(result)

        text_left = parchment_x + padding_inner
        text_top = parchment_y + padding_inner

        dc_y = text_top - dc_top_bearing
        draw.text((text_left, dc_y), first_char, font=dropcap_font, fill=text_color)

        body_bbox_sample = temp_draw.textbbox((0, 0), 'Ay', font=body_font)
        body_top_bearing = body_bbox_sample[1]

        for i, line in enumerate(cap_lines):
            lx = text_left + dc_total_w
            ly = text_top + (i * line_height) - body_top_bearing
            draw.text((lx, ly), line.strip(), font=body_font, fill=text_color)

        extra_start_y = text_top + cap_area_h
        for i, line in enumerate(extra_lines):
            ly = extra_start_y + (i * line_height) - body_top_bearing
            draw.text((text_left, ly), line.strip(), font=body_font, fill=text_color)

    if text_below and text_below.strip():
        clean_below = text_below.replace('\n', ' ').strip()
        while '  ' in clean_below:
            clean_below = clean_below.replace('  ', ' ')

        below_lines = _wrap_text(temp_draw, clean_below, body_font, content_w)
        total_lines_below = len(below_lines)

        parchment_h_b = (total_lines_below * line_height) + (padding_inner * 2)
        parchment_y_b = img_h - margin_safe - parchment_h_b

        result = _draw_parchment_with_texture(
            result, parchment_x, parchment_y_b, parchment_w, parchment_h_b,
            shadow_offset, blur_radius, seed=99
        )
        draw = ImageDraw.Draw(result)

        text_left_b = parchment_x + padding_inner
        text_top_b = parchment_y_b + padding_inner

        body_bbox_sample = temp_draw.textbbox((0, 0), 'Ay', font=body_font)
        body_top_bearing = body_bbox_sample[1]

        sc_font_size = max(10, int(body_size * 0.78))
        sc_font = _load_font('fredoka', sc_font_size)

        words_below = clean_below.split()
        sc_words = words_below[:3]
        rest_words = words_below[3:]

        sc_text = ' '.join(w.upper() for w in sc_words)
        rest_first = ' '.join(rest_words)

        sc_bbox = temp_draw.textbbox((0, 0), sc_text, font=sc_font)
        sc_width = sc_bbox[2] - sc_bbox[0]

        if rest_first:
            first_line_combined = sc_text + ' ' + rest_first
        else:
            first_line_combined = sc_text

        first_line_words = first_line_combined.split()
        built_first_line = ""
        first_line_idx = 0
        for w in first_line_words:
            test = f"{built_first_line} {w}".strip()
            bbox = temp_draw.textbbox((0, 0), test, font=body_font)
            if bbox[2] - bbox[0] <= content_w:
                built_first_line = test
                first_line_idx += 1
            else:
                break

        remaining_text = ' '.join(first_line_words[first_line_idx:])
        remaining_lines = []
        if remaining_text:
            remaining_lines = _wrap_text(temp_draw, remaining_text, body_font, content_w)

        all_render_lines = [built_first_line] + remaining_lines

        parchment_h_b = (len(all_render_lines) * line_height) + (padding_inner * 2)
        parchment_y_b = img_h - margin_safe - parchment_h_b

        result_clean = result.copy()
        result = _draw_parchment_with_texture(
            result_clean, parchment_x, parchment_y_b, parchment_w, parchment_h_b,
            shadow_offset, blur_radius, seed=99
        )
        draw = ImageDraw.Draw(result)
        text_top_b = parchment_y_b + padding_inner

        for i, line in enumerate(all_render_lines):
            ly = text_top_b + (i * line_height) - body_top_bearing
            if i == 0 and sc_words:
                sc_part = ' '.join(w.upper() for w in sc_words)
                sc_bbox_r = draw.textbbox((0, 0), sc_part, font=sc_font)
                sc_top_bearing = sc_bbox_r[1]
                sc_baseline_offset = int((body_size - sc_font_size) * 0.5)
                draw.text((text_left_b, ly + sc_baseline_offset - sc_top_bearing + body_top_bearing), sc_part, font=sc_font, fill=text_color)
                sc_w = sc_bbox_r[2] - sc_bbox_r[0]
                rest_of_line = line[len(sc_part):].strip()
                if rest_of_line:
                    space_w = draw.textbbox((0, 0), ' ', font=body_font)[2]
                    draw.text((text_left_b + sc_w + space_w, ly), rest_of_line, font=body_font, fill=text_color)
            else:
                draw.text((text_left_b, ly), line.strip(), font=body_font, fill=text_color)

    return result.convert('RGB')
