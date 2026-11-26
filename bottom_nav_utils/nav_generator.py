# bottom_nav_utils/nav_generator.py
import base64
import io
import math
import os
import random
from PIL import Image, ImageDraw, ImageFilter

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "bottom_nav")


def _add_brushed_metal_grain(img, x1, y1, x2, y2, strength=4):
    """Деликатная горизонтальная шлифовка металла."""
    rng = random.Random(77)
    grain = Image.new("RGBA", img.size, (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(grain)
    for y in range(y1, y2 + 1):
        delta = rng.randint(-strength, strength)
        if delta > 0:
            g_draw.line([(x1, y), (x2, y)], fill=(255, 255, 255, delta))
        elif delta < 0:
            g_draw.line([(x1, y), (x2, y)], fill=(0, 0, 0, -delta))
    return Image.alpha_composite(img, grain)


def generate_top_divider_bar_png(light_theme=False):
    """Генерирует только верхнюю металлическую рамку-разделитель (без нижней)."""
    W, H = 1080, 14
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    b_draw = ImageDraw.Draw(canvas)

    for dy in range(H):
        t = dy / max(1, H - 1)
        if light_theme:
            v = int(236 - 34 * t)
            col = (v, v + 2, v + 4, 255)
        else:
            if t < 0.25:
                k = t / 0.25
                v = int(94 - 26 * k)
            elif t < 0.78:
                k = (t - 0.25) / 0.53
                v = int(68 - 24 * k)
            else:
                k = (t - 0.78) / 0.22
                v = int(44 - 14 * k)
            col = (v, v + 2, v + 5, 255)
        b_draw.line([(0, dy), (W - 1, dy)], fill=col)

    canvas = _add_brushed_metal_grain(canvas, 0, 0, W - 1, H - 1, strength=4)

    d = ImageDraw.Draw(canvas)
    d.line([(0, 0), (W - 1, 0)], fill=(255, 255, 255, 215 if light_theme else 115), width=2)
    d.line([(0, H - 1), (W - 1, H - 1)], fill=(0, 0, 0, 75 if light_theme else 210), width=2)
    return canvas


def generate_glow_orb_png():
    """Генерирует мягкое радиальное свечение (180x180) для подсветки при нажатии."""
    S = 180
    cx, cy = S // 2, S // 2
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([cx - 56, cy - 56, cx + 56, cy + 56], fill=(255, 255, 255, 220))
    return img.filter(ImageFilter.GaussianBlur(radius=24))


def _stylize_metallic_icon(alpha_mask, light_theme=False):
    """Превращает силуэт иконки в объёмный шлифованный хром-металл с фаской и бликом."""
    S = alpha_mask.size[0]
    metal = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    m_draw = ImageDraw.Draw(metal)

    for y in range(S):
        t = y / max(1, S - 1)
        if light_theme:
            if t < 0.35:
                k = t / 0.35
                v = int(132 - 48 * k)
            elif t < 0.65:
                k = (t - 0.35) / 0.30
                v = int(84 - 44 * k)
            else:
                k = (t - 0.65) / 0.35
                v = int(40 + 44 * k)
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
        m_draw.line([(0, y), (S, y)], fill=(v, v + 2, v + 5, 255))

    metal = _add_brushed_metal_grain(metal, 0, 0, S - 1, S - 1, strength=6)

    out = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    out.paste(metal, (0, 0), alpha_mask)

    shifted_down = Image.new("L", (S, S), 0)
    shifted_down.paste(alpha_mask, (0, 8))
    top_rim = Image.new("L", (S, S), 0)
    p_orig = alpha_mask.load()
    p_down = shifted_down.load()
    p_rim = top_rim.load()
    for y in range(S):
        for x in range(S):
            diff = p_orig[x, y] - p_down[x, y]
            if diff > 0:
                p_rim[x, y] = min(255, int(diff * 0.88))

    rim_layer = Image.new("RGBA", (S, S), (255, 255, 255, 225))
    out_with_rim = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    out_with_rim.paste(rim_layer, (0, 0), top_rim)
    out = Image.alpha_composite(out, out_with_rim)

    return out


def _draw_acoustic_guitar_silhouette(S):
    """Рисует классическую акустическую гитару под 45° (как на референсе: восьмёрка, бридж, розетка, колки)."""
    cx, cy = S // 2, S // 2
    g = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    gd = ImageDraw.Draw(g)
    W = (255, 255, 255, 255)
    T = (0, 0, 0, 0)

    # Рисуем гитару строго вертикально по центру, затем поворачиваем на -42°
    # 1. Нижний овал деки
    gd.ellipse([cx - 154, cy + 16, cx + 154, cy + 292], fill=W)
    # 2. Верхний овал деки
    gd.ellipse([cx - 118, cy - 112, cx + 118, cy + 110], fill=W)
    # 3. Плавная талия корпуса (заполняем середину и вырезаем боковые выемки)
    gd.rectangle([cx - 104, cy - 12, cx + 104, cy + 126], fill=W)
    gd.ellipse([cx - 196, cy - 30, cx - 94, cy + 78], fill=T)
    gd.ellipse([cx + 94, cy - 30, cx + 196, cy + 78], fill=T)

    # 4. Гриф и голова грифа с колками
    gd.rectangle([cx - 24, cy - 310, cx + 24, cy - 95], fill=W)
    gd.rounded_rectangle([cx - 38, cy - 392, cx + 38, cy - 296], radius=16, fill=W)

    # 6 колков по 3 с каждой стороны головы грифа
    for peg_y in (cy - 370, cy - 342, cy - 314):
        gd.rounded_rectangle([cx - 60, peg_y - 8, cx - 34, peg_y + 8], radius=5, fill=W)
        gd.rounded_rectangle([cx + 34, peg_y - 8, cx + 60, peg_y + 8], radius=5, fill=W)

    # 5. Резонаторное отверстие (розетка) и струнодержатель (бридж) как прорези для металлического рельефа
    gd.ellipse([cx - 46, cy - 42, cx + 46, cy + 50], fill=T)
    gd.rounded_rectangle([cx - 72, cy + 156, cx + 72, cy + 184], radius=10, fill=T)

    # Поворачиваем гитару на -42° (гриф в правый верхний угол, дека в левый нижний)
    rotated = g.rotate(-42, resample=Image.BICUBIC, center=(cx, cy))
    return rotated


def _draw_icon_silhouette(icon_name):
    """Рисует крупные 4x SSAA силуэты иконок."""
    OUT = 192
    SS = 4
    S = OUT * SS  # 768x768
    cx, cy = S // 2, S // 2

    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    W = (255, 255, 255, 255)
    T = (0, 0, 0, 0)

    if icon_name == "songs":
        img = _draw_acoustic_guitar_silhouette(S)

    elif icon_name == "chords":
        for ox, oy in [(-112, 124), (88, 90)]:
            head = Image.new("RGBA", (S, S), (0, 0, 0, 0))
            hd = ImageDraw.Draw(head)
            hd.ellipse([cx - 78, cy - 54, cx + 78, cy + 54], fill=W)
            head = head.rotate(22, resample=Image.BICUBIC, center=(cx, cy))
            img.alpha_composite(head, (ox, oy))

        d.rounded_rectangle([cx - 76, cy - 196, cx - 34, cy + 122], radius=12, fill=W)
        d.rounded_rectangle([cx + 124, cy - 234, cx + 166, cy + 88], radius=12, fill=W)
        d.polygon(
            [
                (cx - 76, cy - 206),
                (cx + 166, cy - 248),
                (cx + 166, cy - 182),
                (cx - 76, cy - 140),
            ],
            fill=W,
        )

    elif icon_name == "tuner":
        heights = [110, 210, 320, 420, 320, 210, 110]
        bar_w = 34
        gap = 28
        total_w = len(heights) * bar_w + (len(heights) - 1) * gap
        start_x = cx - total_w // 2
        for idx, bh in enumerate(heights):
            bx1 = start_x + idx * (bar_w + gap)
            bx2 = bx1 + bar_w
            by1 = cy - bh // 2
            by2 = cy + bh // 2
            d.rounded_rectangle([bx1, by1, bx2, by2], radius=bar_w // 2, fill=W)

    elif icon_name == "metronome":
        d.polygon(
            [
                (cx - 66, cy - 224),
                (cx + 66, cy - 224),
                (cx + 178, cy + 224),
                (cx - 178, cy + 224),
            ],
            fill=W,
        )
        d.polygon(
            [
                (cx - 40, cy - 166),
                (cx + 40, cy - 166),
                (cx + 110, cy + 128),
                (cx - 110, cy + 128),
            ],
            fill=T,
        )
        d.line([(cx, cy + 124), (cx + 118, cy - 182)], fill=W, width=32)
        d.ellipse([cx + 102, cy - 198, cx + 134, cy - 166], fill=W)
        d.rounded_rectangle([cx + 38, cy - 114, cx + 108, cy - 60], radius=14, fill=W)

    elif icon_name == "favorites":
        r = 98
        d.ellipse([cx - 182, cy - 170, cx - 182 + r * 2, cy - 170 + r * 2], fill=W)
        d.ellipse([cx + 182 - r * 2, cy - 170, cx + 182, cy - 170 + r * 2], fill=W)
        d.polygon(
            [
                (cx - 175, cy - 40),
                (cx + 175, cy - 40),
                (cx, cy + 206),
            ],
            fill=W,
        )
        d.polygon(
            [
                (cx - 88, cy - 118),
                (cx + 88, cy - 118),
                (cx, cy - 26),
            ],
            fill=W,
        )

    mask_hi = img.split()[3]
    metal_dark = _stylize_metallic_icon(mask_hi, light_theme=False).resize((OUT, OUT), Image.LANCZOS)
    metal_light = _stylize_metallic_icon(mask_hi, light_theme=True).resize((OUT, OUT), Image.LANCZOS)
    glow_mask = img.resize((OUT, OUT), Image.LANCZOS)
    return metal_dark, metal_light, glow_mask


def save_nav_assets():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    top_bar_dark = generate_top_divider_bar_png(light_theme=False)
    top_bar_light = generate_top_divider_bar_png(light_theme=True)
    glow_orb = generate_glow_orb_png()

    icon_names = ["songs", "chords", "tuner", "metronome", "favorites"]
    icons_dark = {}
    icons_light = {}
    icons_mask = {}

    for name in icon_names:
        md, ml, gm = _draw_icon_silhouette(name)
        icons_dark[name] = md
        icons_light[name] = ml
        icons_mask[name] = gm

    def to_b64(img):
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("utf-8")

    out_path = os.path.join(OUTPUT_DIR, "nav_assets.py")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write('"""HD-текстуры верхней планки BottomNav и металлизированных иконок."""\n\n')
        f.write(f'TOP_BAR_DARK_B64 = "{to_b64(top_bar_dark)}"\n')
        f.write(f'TOP_BAR_LIGHT_B64 = "{to_b64(top_bar_light)}"\n')
        f.write(f'GLOW_ORB_B64 = "{to_b64(glow_orb)}"\n\n')
        f.write("ICONS_METAL_DARK_B64 = {\n")
        for name, img in icons_dark.items():
            f.write(f'    "{name}": "{to_b64(img)}",\n')
        f.write("}\n\n")
        f.write("ICONS_METAL_LIGHT_B64 = {\n")
        for name, img in icons_light.items():
            f.write(f'    "{name}": "{to_b64(img)}",\n')
        f.write("}\n\n")
        f.write("ICONS_GLOW_MASK_B64 = {\n")
        for name, img in icons_mask.items():
            f.write(f'    "{name}": "{to_b64(img)}",\n')
        f.write("}\n")

    init_path = os.path.join(OUTPUT_DIR, "__init__.py")
    with open(init_path, "w", encoding="utf-8") as f:
        f.write("from . import nav_assets\n")

    print(f"[OK] Сгенерированы верхняя планка и металлические иконки BottomNav: {out_path}")


if __name__ == "__main__":
    save_nav_assets()