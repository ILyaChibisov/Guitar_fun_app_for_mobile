# favorites_utils/card_generator.py
import base64
import io
import os
import random
from PIL import Image, ImageDraw, ImageFilter

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "favorites")


def _add_brushed_metal_grain(img, x1, y1, x2, y2, strength=4):
    """Деликатная горизонтальная шлифовка алюминия."""
    rng = random.Random(108)
    grain = Image.new("RGBA", img.size, (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(grain)
    for y in range(y1, y2 + 1):
        delta = rng.randint(-strength, strength)
        if delta > 0:
            g_draw.line([(x1, y), (x2, y)], fill=(255, 255, 255, delta))
        elif delta < 0:
            g_draw.line([(x1, y), (x2, y)], fill=(0, 0, 0, -delta))
    return Image.alpha_composite(img, grain)


def generate_song_card_panel_png(light_theme=False, green_theme=False):
    """Генерирует студийную металлическую рамку-консоль карточки песни (без внешних теней и разделителя)."""
    W, H = 960, 148
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    x1, y1 = 2, 2
    x2, y2 = W - 2, H - 2
    radius = 28

    # 1. Металлический корпус карточки
    plate = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    p_draw = ImageDraw.Draw(plate)
    for y in range(y1, y2 + 1):
        t = (y - y1) / max(1, (y2 - y1))
        if light_theme:
            v = int(234 - 30 * t)
            col = (v, v + 2, v + 4, 252)
        else:
            if t < 0.14:
                k = t / 0.14
                v = int(76 - 24 * k)
            elif t < 0.88:
                k = (t - 0.14) / 0.74
                v = int(52 - 22 * k)
            else:
                k = (t - 0.88) / 0.12
                v = int(30 - 8 * k)
            col = (v, v + 2, v + 4, 252)
        p_draw.line([(x1, y), (x2, y)], fill=col)

    plate = _add_brushed_metal_grain(plate, x1, y1, x2, y2, strength=4)

    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=255)
    canvas.paste(plate, (0, 0), mask)

    # 2. Внешняя двойная фаска корпуса
    bevel = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bv_draw = ImageDraw.Draw(bevel)
    bv_draw.rounded_rectangle(
        [x1, y1, x2, y2],
        radius=radius,
        outline=(255, 255, 255, 200 if light_theme else 90),
        width=2,
    )
    bv_draw.rounded_rectangle(
        [x1 + 2, y1 + 2, x2 - 2, y2 - 2],
        radius=radius - 2,
        outline=(0, 0, 0, 55 if light_theme else 175),
        width=2,
    )
    canvas.paste(Image.alpha_composite(canvas, bevel), (0, 0), mask)

    # 3. Утопленная внутренняя ниша (Recessed Bay)
    bay_x1, bay_y1 = x1 + 14, y1 + 11
    bay_x2, bay_y2 = x2 - 14, y2 - 11
    bay_r = 20

    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle(
        [bay_x1 - 2, bay_y1 - 1, bay_x2 + 2, bay_y2 + 2],
        radius=bay_r + 2,
        outline=(255, 255, 255, 165 if light_theme else 48),
        width=2,
    )

    bay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    b_draw = ImageDraw.Draw(bay)
    if light_theme:
        bay_fill = (196, 202, 208, 255)
    elif green_theme:
        bay_fill = (0, 13, 8, 66)
    else:
        bay_fill = (15, 18, 22, 255)
    b_draw.rounded_rectangle([bay_x1, bay_y1, bay_x2, bay_y2], radius=bay_r, fill=bay_fill)

    if not green_theme:
        bay_sh = Image.new("RGBA", (W, H), (0, 0, 0, 110 if light_theme else 235))
        ImageDraw.Draw(bay_sh).rounded_rectangle(
            [bay_x1 + 4, bay_y1 + 6, bay_x2 - 2, bay_y2 + 5], radius=bay_r, fill=(0, 0, 0, 0)
        )
        bay.alpha_composite(bay_sh.filter(ImageFilter.GaussianBlur(radius=5)))

    bay_mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(bay_mask).rounded_rectangle([bay_x1, bay_y1, bay_x2, bay_y2], radius=bay_r, fill=255)
    canvas.paste(bay, (0, 0), bay_mask)

    meta = {
        "rim_box_norm": [
            round(bay_x1 / W, 4),
            round(1.0 - bay_y2 / H, 4),
            round((bay_x2 - bay_x1) / W, 4),
            round((bay_y2 - bay_y1) / H, 4),
        ],
        "rim_radius_norm": round(bay_r / H, 4),
    }
    return canvas, meta


def _stylize_metallic_sprite(alpha_mask, light_theme=False):
    """Окрашивает маску иконки в объёмный шлифованный хром/титан с верхней фаской."""
    W, H = alpha_mask.size
    metal = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    m_draw = ImageDraw.Draw(metal)

    for y in range(H):
        t = y / max(1, H - 1)
        if light_theme:
            if t < 0.35:
                k = t / 0.35
                v = int(126 - 46 * k)
            elif t < 0.65:
                k = (t - 0.35) / 0.30
                v = int(80 - 40 * k)
            else:
                k = (t - 0.65) / 0.35
                v = int(40 + 42 * k)
        else:
            if t < 0.34:
                k = t / 0.34
                v = int(254 - 34 * k)
            elif t < 0.54:
                k = (t - 0.34) / 0.20
                v = int(220 - 84 * k)
            elif t < 0.78:
                k = (t - 0.54) / 0.24
                v = int(136 + 70 * k)
            else:
                k = (t - 0.78) / 0.22
                v = int(206 - 42 * k)
        m_draw.line([(0, y), (W, y)], fill=(v, v + 2, v + 5, 255))

    metal = _add_brushed_metal_grain(metal, 0, 0, W - 1, H - 1, strength=6)

    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    out.paste(metal, (0, 0), alpha_mask)

    shifted_down = Image.new("L", (W, H), 0)
    shifted_down.paste(alpha_mask, (0, 7))
    top_rim = Image.new("L", (W, H), 0)
    p_orig = alpha_mask.load()
    p_down = shifted_down.load()
    p_rim = top_rim.load()
    for y in range(H):
        for x in range(W):
            diff = p_orig[x, y] - p_down[x, y]
            if diff > 0:
                p_rim[x, y] = min(255, int(diff * 0.88))

    rim_layer = Image.new("RGBA", (W, H), (255, 255, 255, 225))
    out_with_rim = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    out_with_rim.paste(rim_layer, (0, 0), top_rim)
    return Image.alpha_composite(out, out_with_rim)


def generate_song_guitar_icon_png():
    """Генерирует 4x SSAA иконку акустической гитары с нотками (как на референсе) в металле."""
    OUT = 192
    SS = 4
    S = OUT * SS  # 768x768
    cx, cy = S // 2, S // 2

    W = (255, 255, 255, 255)
    T = (0, 0, 0, 0)

    # 1. Рисуем гитару вертикально и поворачиваем на -42°
    g = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    gd = ImageDraw.Draw(g)

    # Нижний и верхний овалы деки
    gd.ellipse([cx - 148, cy + 16, cx + 148, cy + 284], fill=W)
    gd.ellipse([cx - 114, cy - 108, cx + 114, cy + 106], fill=W)
    # Талия деки
    gd.rectangle([cx - 100, cy - 12, cx + 100, cy + 122], fill=W)
    gd.ellipse([cx - 190, cy - 28, cx - 90, cy + 76], fill=T)
    gd.ellipse([cx + 90, cy - 28, cx + 190, cy + 76], fill=T)

    # Гриф и голова грифа с колками
    gd.rectangle([cx - 22, cy - 302, cx + 22, cy - 92], fill=W)
    gd.rounded_rectangle([cx - 36, cy - 380, cx + 36, cy - 288], radius=14, fill=W)
    for peg_y in (cy - 360, cy - 332, cy - 304):
        gd.rounded_rectangle([cx - 56, peg_y - 7, cx - 32, peg_y + 7], radius=4, fill=W)
        gd.rounded_rectangle([cx + 32, peg_y - 7, cx + 56, peg_y + 7], radius=4, fill=W)

    # Розетка с кольцом-окантовкой и струнодержатель (бридж)
    gd.ellipse([cx - 46, cy - 40, cx + 46, cy + 48], fill=T)
    gd.ellipse([cx - 32, cy - 26, cx + 32, cy + 34], fill=W)
    gd.ellipse([cx - 22, cy - 16, cx + 22, cy + 24], fill=T)
    gd.rounded_rectangle([cx - 68, cy + 150, cx + 68, cy + 178], radius=9, fill=T)

    canvas = g.rotate(-42, resample=Image.BICUBIC, center=(cx - 10, cy + 10))
    d = ImageDraw.Draw(canvas)

    # 2. Парящая двойная нотка сверху слева от гитары (как на скрине 2)
    n1x, n1y = cx - 235, cy - 135
    d.ellipse([n1x - 28, n1y - 20, n1x + 28, n1y + 20], fill=W)
    d.ellipse([n1x + 56 - 28, n1y - 14 - 20, n1x + 56 + 28, n1y - 14 + 20], fill=W)
    d.rounded_rectangle([n1x + 12, n1y - 98, n1x + 28, n1y + 4], radius=6, fill=W)
    d.rounded_rectangle([n1x + 68, n1y - 112, n1x + 84, n1y - 10], radius=6, fill=W)
    d.polygon(
        [
            (n1x + 12, n1y - 102),
            (n1x + 84, n1y - 118),
            (n1x + 84, n1y - 90),
            (n1x + 12, n1y - 74),
        ],
        fill=W,
    )

    # 3. Парящая двойная нотка снизу справа от гитары (как на скрине 2)
    n2x, n2y = cx + 145, cy + 235
    d.ellipse([n2x - 28, n2y - 20, n2x + 28, n2y + 20], fill=W)
    d.ellipse([n2x + 58 - 28, n2y + 12 - 20, n2x + 58 + 28, n2y + 12 + 20], fill=W)
    d.rounded_rectangle([n2x + 12, n2y - 98, n2x + 28, n2y + 4], radius=6, fill=W)
    d.rounded_rectangle([n2x + 70, n2y - 86, n2x + 86, n2y + 16], radius=6, fill=W)
    d.polygon(
        [
            (n2x + 12, n2y - 102),
            (n2x + 86, n2y - 90),
            (n2x + 86, n2y - 62),
            (n2x + 12, n2y - 74),
        ],
        fill=W,
    )

    mask_hi = canvas.split()[3]
    metal_dark = _stylize_metallic_sprite(mask_hi, light_theme=False).resize((OUT, OUT), Image.LANCZOS)
    metal_light = _stylize_metallic_sprite(mask_hi, light_theme=True).resize((OUT, OUT), Image.LANCZOS)
    glow_mask = canvas.resize((OUT, OUT), Image.LANCZOS)
    return metal_dark, metal_light, glow_mask


def save_favorites_assets():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    card_dark, card_meta = generate_song_card_panel_png(light_theme=False, green_theme=False)
    card_green, _ = generate_song_card_panel_png(light_theme=False, green_theme=True)
    card_light, _ = generate_song_card_panel_png(light_theme=True, green_theme=False)
    guitar_dark, guitar_light, guitar_mask = generate_song_guitar_icon_png()

    def to_b64(img):
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("utf-8")

    out_path = os.path.join(OUTPUT_DIR, "card_assets.py")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write('"""HD-текстуры студийной карточки песни и металлической иконки гитары."""\n\n')
        f.write(f"CARD_SIZE = {card_dark.size}\n")
        f.write(f"CARD_META = {repr(card_meta)}\n\n")
        f.write(f'CARD_DARK_B64 = "{to_b64(card_dark)}"\n')
        f.write(f'CARD_GREEN_B64 = "{to_b64(card_green)}"\n')
        f.write(f'CARD_LIGHT_B64 = "{to_b64(card_light)}"\n\n')
        f.write(f'GUITAR_DARK_B64 = "{to_b64(guitar_dark)}"\n')
        f.write(f'GUITAR_LIGHT_B64 = "{to_b64(guitar_light)}"\n')
        f.write(f'GUITAR_MASK_B64 = "{to_b64(guitar_mask)}"\n')

    init_path = os.path.join(OUTPUT_DIR, "__init__.py")
    with open(init_path, "w", encoding="utf-8") as f:
        f.write("from . import card_assets\n")

    print(f"[OK] Сгенерированы HD-текстуры карточки избранного: {out_path}")



if __name__ == "__main__":
    save_favorites_assets()