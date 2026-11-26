# home_utils/logo_generator.py
import base64
import io
import os
import random
from PIL import Image, ImageChops, ImageDraw, ImageFilter

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "home")


def _add_brushed_metal_grain(img, strength=5):
    """Горизонтальная шлифовка металла."""
    w, h = img.size
    rng = random.Random(909)
    grain = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(grain)
    for y in range(h):
        delta = rng.randint(-strength, strength)
        if delta > 0:
            g_draw.line([(0, y), (w - 1, y)], fill=(255, 255, 255, delta))
        elif delta < 0:
            g_draw.line([(0, y), (w - 1, y)], fill=(0, 0, 0, -delta))
    return Image.alpha_composite(img, grain)


def _draw_futuristic_glyphs(draw, x0, y0, char_w, char_h, stroke, word="GUITAR"):
    """Рисует футуристичные геометрические буквы со скошенными углами (4x SSAA)."""
    W = 255
    c = int(stroke * 0.72)  # размер скоса угла
    mid_y = y0 + char_h // 2
    x1 = x0 + char_w
    y1 = y0 + char_h


    def seg(pts):
        draw.polygon(pts, fill=W)

    if word == "G":
        # Верх, левая стойка, низ, правый подъём и перекладина внутрь
        seg([(x0 + c, y0), (x1 - c, y0), (x1, y0 + c), (x1, y0 + stroke), (x0 + stroke, y0 + stroke), (x0 + c, y0)])
        seg([(x0, y0 + c), (x0 + stroke, y0 + stroke), (x0 + stroke, y1 - stroke), (x0, y1 - c)])
        seg([(x0 + c, y1), (x0 + stroke, y1 - stroke), (x1 - stroke, y1 - stroke), (x1 - c, y1)])
        seg([(x1 - stroke, mid_y), (x1, mid_y), (x1, y1 - c), (x1 - c, y1), (x1 - stroke, y1 - stroke)])
        seg([(x0 + char_w * 0.46, mid_y - stroke // 2), (x1, mid_y - stroke // 2), (x1, mid_y + stroke // 2), (x0 + char_w * 0.46, mid_y + stroke // 2)])

    elif word == "U":
        seg([(x0, y0), (x0 + stroke, y0), (x0 + stroke, y1 - stroke), (x0, y1 - c)])
        seg([(x1 - stroke, y0), (x1, y0), (x1, y1 - c), (x1 - stroke, y1 - stroke)])
        seg([(x0 + c, y1), (x0 + stroke, y1 - stroke), (x1 - stroke, y1 - stroke), (x1 - c, y1)])

    elif word == "I":
        cx = x0 + char_w // 2
        seg([(cx - stroke // 2, y0), (cx + stroke // 2, y0), (cx + stroke // 2, y1), (cx - stroke // 2, y1)])
        # Засечки в стиле киберпанк
        seg([(x0 + c, y0), (x1 - c, y0), (x1 - c, y0 + int(stroke * 0.65)), (x0 + c, y0 + int(stroke * 0.65))])
        seg([(x0 + c, y1 - int(stroke * 0.65)), (x1 - c, y1 - int(stroke * 0.65)), (x1 - c, y1), (x0 + c, y1)])

    elif word == "T":
        cx = x0 + char_w // 2
        seg([(x0, y0), (x1, y0), (x1 - c // 2, y0 + stroke), (x0 + c // 2, y0 + stroke)])
        seg([(cx - stroke // 2, y0 + stroke // 2), (cx + stroke // 2, y0 + stroke // 2), (cx + stroke // 2, y1), (cx - stroke // 2, y1)])

    elif word == "A":
        seg([(x0, y1), (x0, y0 + c), (x0 + c, y0), (x0 + stroke, y0 + stroke), (x0 + stroke, y1)])
        seg([(x1 - stroke, y1), (x1 - stroke, y0 + stroke), (x1 - c, y0), (x1, y0 + c), (x1, y1)])
        seg([(x0 + c, y0), (x1 - c, y0), (x1 - stroke, y0 + stroke), (x0 + stroke, y0 + stroke)])
        seg([(x0 + stroke // 2, mid_y), (x1 - stroke // 2, mid_y), (x1 - stroke // 2, mid_y + int(stroke * 0.85)), (x0 + stroke // 2, mid_y + int(stroke * 0.85))])

    elif word == "R":
        seg([(x0, y0), (x0 + stroke, y0), (x0 + stroke, y1), (x0, y1)])
        seg([(x0 + stroke, y0), (x1 - c, y0), (x1, y0 + c), (x1, mid_y - c // 2), (x1 - c, mid_y), (x0 + stroke, mid_y), (x0 + stroke, mid_y - stroke), (x1 - stroke, mid_y - stroke), (x1 - stroke, y0 + stroke), (x0 + stroke, y0 + stroke)])
        # Диагональная нога R
        seg([(x0 + char_w * 0.46, mid_y), (x0 + char_w * 0.46 + stroke, mid_y), (x1, y1), (x1 - stroke * 1.1, y1)])

    elif word == "F":
        seg([(x0, y0), (x0 + stroke, y0), (x0 + stroke, y1), (x0, y1)])
        seg([(x0 + stroke, y0), (x1, y0), (x1 - c // 2, y0 + stroke), (x0 + stroke, y0 + stroke)])
        seg([(x0 + stroke, mid_y - stroke // 2), (x1 - c, mid_y - stroke // 2), (x1 - c, mid_y + stroke // 2), (x0 + stroke, mid_y + stroke // 2)])

    elif word == "N":
        seg([(x0, y0), (x0 + stroke, y0), (x0 + stroke, y1), (x0, y1)])
        seg([(x1 - stroke, y0), (x1, y0), (x1, y1), (x1 - stroke, y1)])
        seg([(x0 + stroke * 0.4, y0), (x0 + stroke * 1.35, y0), (x1 - stroke * 0.4, y1), (x1 - stroke * 1.35, y1)])

    elif word == "S":
        seg([(x0 + c, y0), (x1, y0), (x1 - c // 2, y0 + stroke), (x0 + stroke, y0 + stroke), (x0 + c, y0)])
        seg([(x0, y0 + c), (x0 + stroke, y0 + stroke), (x0 + stroke, mid_y - stroke // 2), (x0, mid_y - c // 2)])
        seg([(x0 + c // 2, mid_y - stroke // 2), (x1 - c // 2, mid_y - stroke // 2), (x1, mid_y), (x1 - c // 2, mid_y + stroke // 2), (x0 + c // 2, mid_y + stroke // 2), (x0, mid_y)])
        seg([(x1 - stroke, mid_y + stroke // 2), (x1, mid_y + c // 2), (x1, y1 - c), (x1 - stroke, y1 - stroke)])
        seg([(x0, y1), (x0 + c // 2, y1 - stroke), (x1 - stroke, y1 - stroke), (x1 - c, y1)])


def _build_word_masks(W, H):
    """Строит 4x SSAA маски отдельно для 'GUITAR' и 'FANS'."""
    guitar_mask = Image.new("L", (W, H), 0)
    fans_mask = Image.new("L", (W, H), 0)
    dg = ImageDraw.Draw(guitar_mask)
    df = ImageDraw.Draw(fans_mask)

    letters = ["G", "U", "I", "T", "A", "R", "F", "A", "N", "S"]
    widths = [185, 175, 115, 170, 185, 180, 165, 185, 185, 175]
    gap = 34
    char_h = 230
    stroke = 44

    total_w = sum(widths) + gap * (len(letters) - 1)
    cur_x = (W - total_w) // 2
    y0 = (H - char_h) // 2 - 12

    for idx, (ch, cw) in enumerate(zip(letters, widths)):
        target_draw = dg if idx < 6 else df
        _draw_futuristic_glyphs(target_draw, cur_x, y0, cw, char_h, stroke, word=ch)
        cur_x += cw + gap

    return guitar_mask, fans_mask


def _render_3d_metallic_logo(guitar_mask, fans_mask, theme_mode="dark"):
    """
    Создаёт 3D-экструзию, шлифованную лицевую грань и скошенную фаску (bevel)
    под выбранную тему ('green', 'dark', 'light').
    """
    W, H = guitar_mask.size
    combined = ImageChops.lighter(guitar_mask, fans_mask)
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    # 1. 3D-экструзия (объёмная толщина букв уходящая вниз-вправо)
    depth = 26
    for step in range(depth, 0, -2):
        t = step / depth
        if theme_mode == "light":
            v = int(65 + 45 * (1.0 - t))
            col = (v, v + 6, v + 4, 235)
        elif theme_mode == "dark":
            v = int(18 + 26 * (1.0 - t))
            col = (v + 12, v + 4, v, 245)
        else:  # green
            v = int(10 + 28 * (1.0 - t))
            col = (v, v + 18, v + 12, 245)

        layer = Image.new("RGBA", (W, H), col)
        shifted = Image.new("L", (W, H), 0)
        shifted.paste(combined, (int(step * 0.45), step))
        tmp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        tmp.paste(layer, (0, 0), shifted)
        canvas = Image.alpha_composite(canvas, tmp)

    # 2. Лицевая грань 'GUITAR' (шлифованный хром / тёмный титан в light-теме)
    face_g = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fg_draw = ImageDraw.Draw(face_g)
    for y in range(H):
        t = y / max(1, H - 1)
        if theme_mode == "light":
            # Тёмный полированный титан/графит для контраста на светлом фоне
            if t < 0.45:
                v = int(88 - 36 * (t / 0.45))
            else:
                v = int(52 + 34 * ((t - 0.45) / 0.55))
            col = (v, v + 6, v + 5, 255)
        else:
            # Светлый зеркальный хром
            if t < 0.42:
                v = int(252 - 38 * (t / 0.42))
            elif t < 0.56:
                v = int(214 - 86 * ((t - 0.42) / 0.14))
            else:
                v = int(128 + 84 * ((t - 0.56) / 0.44))
            col = (v, v + 2, v + 5, 255)
        fg_draw.line([(0, y), (W - 1, y)], fill=col)

    face_g = _add_brushed_metal_grain(face_g, strength=5)
    g_part = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    g_part.paste(face_g, (0, 0), guitar_mask)
    canvas = Image.alpha_composite(canvas, g_part)

    # 3. Лицевая грань 'FANS' (фирменный акцентный металл темы)
    face_f = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ff_draw = ImageDraw.Draw(face_f)
    for y in range(H):
        t = y / max(1, H - 1)
        if theme_mode == "light":
            # Изумрудный металлик
            k = abs(t - 0.48) * 1.8
            r, g, b = int(18 + 18 * k), int(155 - 45 * k), int(84 - 25 * k)
        elif theme_mode == "dark":
            # Янтарно-оранжевый металлик
            k = abs(t - 0.48) * 1.8
            r, g, b = 255, int(158 - 55 * k), int(24 - 16 * k)
        else:
            # Неоново-изумрудный металлик
            k = abs(t - 0.48) * 1.8
            r, g, b = int(60 - 25 * k), int(248 - 65 * k), int(135 - 45 * k)
        ff_draw.line([(0, y), (W - 1, y)], fill=(r, g, b, 255))

    face_f = _add_brushed_metal_grain(face_f, strength=5)
    f_part = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    f_part.paste(face_f, (0, 0), fans_mask)
    canvas = Image.alpha_composite(canvas, f_part)

    # 4. Внутренний световой блик по верхней фаске всех букв (Bevel Rim)
    shifted_down = Image.new("L", (W, H), 0)
    shifted_down.paste(combined, (0, 7))
    top_rim = ImageChops.subtract(combined, shifted_down)

    rim_layer = Image.new("RGBA", (W, H), (255, 255, 255, 225 if theme_mode != "light" else 185))
    rim_comp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rim_comp.paste(rim_layer, (0, 0), top_rim)
    canvas = Image.alpha_composite(canvas, rim_comp)

    return canvas


def generate_scan_beam_png():
    """Генерирует диагональный световой луч для периодической анимации блика."""
    W, H = 260, 140
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # Наклонная полоса света
    d.polygon([(70, 0), (145, 0), (190, H), (115, H)], fill=(255, 255, 255, 210))
    d.polygon([(158, 0), (180, 0), (225, H), (203, H)], fill=(255, 255, 255, 130))
    return img.filter(ImageFilter.GaussianBlur(radius=14))


def save_logo_assets():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 4x SSAA холст -> финальный размер 620x124
    W_HI, H_HI = 2480, 496
    OUT_W, OUT_H = 620, 124

    g_mask, f_mask = _build_word_masks(W_HI, H_HI)
    combined_mask = ImageChops.lighter(g_mask, f_mask).resize((OUT_W, OUT_H), Image.LANCZOS)

    logo_green = _render_3d_metallic_logo(g_mask, f_mask, "green").resize((OUT_W, OUT_H), Image.LANCZOS)
    logo_dark = _render_3d_metallic_logo(g_mask, f_mask, "dark").resize((OUT_W, OUT_H), Image.LANCZOS)
    logo_light = _render_3d_metallic_logo(g_mask, f_mask, "light").resize((OUT_W, OUT_H), Image.LANCZOS)

    beam_img = generate_scan_beam_png()

    def to_b64(img):
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("utf-8")

    out_path = os.path.join(OUTPUT_DIR, "logo_assets.py")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write('"""3D футуристичный логотип GUITARFANS (green/dark/light) + маска свечения."""\n\n')
        f.write(f"LOGO_SIZE = {(OUT_W, OUT_H)}\n")
        f.write(f'LOGO_GREEN_B64 = "{to_b64(logo_green)}"\n')
        f.write(f'LOGO_DARK_B64 = "{to_b64(logo_dark)}"\n')
        f.write(f'LOGO_LIGHT_B64 = "{to_b64(logo_light)}"\n')
        f.write(f'LOGO_MASK_B64 = "{to_b64(combined_mask)}"\n')
        f.write(f'SCAN_BEAM_B64 = "{to_b64(beam_img)}"\n')

    init_path = os.path.join(OUTPUT_DIR, "__init__.py")
    with open(init_path, "w", encoding="utf-8") as f:
        f.write("from . import home_assets, logo_assets\n")

    print(f"[OK] Сгенерирован 3D футуристичный логотип GUITARFANS: {out_path}")


if __name__ == "__main__":
    save_logo_assets()