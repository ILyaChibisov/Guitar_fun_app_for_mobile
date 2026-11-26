# top_nav_utils/top_nav_generator.py
import base64
import io
import math
import os
import random
from PIL import Image, ImageChops, ImageDraw, ImageFilter

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "top_nav")


def _add_brushed_metal_grain(img, x1, y1, x2, y2, strength=4):
    """Деликатная горизонтальная шлифовка металла."""
    rng = random.Random(88)
    grain = Image.new("RGBA", img.size, (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(grain)
    for y in range(y1, y2 + 1):
        delta = rng.randint(-strength, strength)
        if delta > 0:
            g_draw.line([(x1, y), (x2, y)], fill=(255, 255, 255, delta))
        elif delta < 0:
            g_draw.line([(x1, y), (x2, y)], fill=(0, 0, 0, -delta))
    return Image.alpha_composite(img, grain)


def generate_bottom_divider_bar_png(light_theme=False):
    """Генерирует нижнюю металлическую планку-разделитель TopNav (зеркально планке BottomNav)."""
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
    """Мягкое радиальное свечение для вспышки при нажатии кнопок."""
    S = 180
    cx, cy = S // 2, S // 2
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([cx - 56, cy - 56, cx + 56, cy + 56], fill=(255, 255, 255, 220))
    return img.filter(ImageFilter.GaussianBlur(radius=24))


def _stylize_metallic_icon(alpha_mask, light_theme=False):
    """Превращает силуэт в объёмный шлифованный металл (1-в-1 как в BottomNav)."""
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
    top_rim = ImageChops.subtract(alpha_mask, shifted_down)

    rim_layer = Image.new("RGBA", (S, S), (255, 255, 255, 225))
    rim_comp = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    rim_comp.paste(rim_layer, (0, 0), top_rim)
    return Image.alpha_composite(out, rim_comp)


def _draw_star_polygon(d, cx, cy, r_out, r_in, fill, outline=None, width=0):
    pts = []
    for i in range(10):
        ang = math.radians(-90 + i * 36)
        r = r_out if i % 2 == 0 else r_in
        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    d.polygon(pts, fill=fill, outline=outline)
    if outline and width > 0:
        d.line(pts + [pts[0]], fill=outline, width=width, joint="curve")


def _draw_top_icon(icon_name):
    """Рисует крупные 4x SSAA иконки для TopNav."""
    OUT = 192
    SS = 4
    S = OUT * SS  # 768x768
    cx, cy = S // 2, S // 2

    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    W = (255, 255, 255, 255)
    T = (0, 0, 0, 0)

    if icon_name == "tune":
        # 3 горизонтальных регулятора (фейдера настроек)
        rows = [(cy - 150, cx - 75), (cy, cx + 85), (cy + 150, cx - 35)]
        for ry, kx in rows:
            d.rounded_rectangle([cx - 210, ry - 18, cx + 210, ry + 18], radius=18, fill=W)
            d.ellipse([kx - 56, ry - 56, kx + 56, ry + 56], fill=T)
            d.ellipse([kx - 42, ry - 42, kx + 42, ry + 42], fill=W)

    elif icon_name == "arrow-left":
        # Стрелка назад
        d.rounded_rectangle([cx - 165, cy - 22, cx + 195, cy + 22], radius=20, fill=W)
        pts = [(cx - 35, cy - 145), (cx - 185, cy), (cx - 35, cy + 145)]
        d.line(pts, fill=W, width=44, joint="curve")
        for px, py in pts:
            d.ellipse([px - 22, py - 22, px + 22, py + 22], fill=W)

    elif icon_name == "magnify":
        # Лупа поиска
        lcx, lcy = cx - 38, cy - 38
        d.ellipse([lcx - 155, lcy - 155, lcx + 155, lcy + 155], fill=W)
        d.ellipse([lcx - 108, lcy - 108, lcx + 108, lcy + 108], fill=T)
        d.line([(lcx + 98, lcy + 98), (cx + 215, cy + 215)], fill=W, width=48)
        d.ellipse([cx + 215 - 24, cy + 215 - 24, cx + 215 + 24, cy + 215 + 24], fill=W)

    elif icon_name == "home":
        # Домик с крышей и дверным проёмом
        d.polygon(
            [(cx, cy - 210), (cx + 225, cy - 18), (cx - 225, cy - 18)],
            fill=W,
        )
        d.rounded_rectangle([cx - 155, cy - 35, cx + 155, cy + 195], radius=24, fill=W)
        d.rounded_rectangle([cx - 48, cy + 52, cx + 48, cy + 195], radius=16, fill=T)

    elif icon_name == "star":
        _draw_star_polygon(d, cx, cy + 8, 215, 96, fill=W)

    elif icon_name == "star-outline":
        _draw_star_polygon(d, cx, cy + 8, 215, 96, fill=W)
        _draw_star_polygon(d, cx, cy + 8, 148, 64, fill=T)

    elif icon_name == "cog":
        # Шестерёнка настроек
        num_teeth = 8
        for i in range(num_teeth):
            ang = math.radians(i * (360 / num_teeth))
            tx = cx + 168 * math.cos(ang)
            ty = cy + 168 * math.sin(ang)
            d.ellipse([tx - 42, ty - 42, tx + 42, ty + 42], fill=W)
        d.ellipse([cx - 158, cy - 158, cx + 158, cy + 158], fill=W)
        d.ellipse([cx - 74, cy - 74, cx + 74, cy + 74], fill=T)

    mask_hi = img.split()[3]
    metal_dark = _stylize_metallic_icon(mask_hi, light_theme=False).resize((OUT, OUT), Image.LANCZOS)
    metal_light = _stylize_metallic_icon(mask_hi, light_theme=True).resize((OUT, OUT), Image.LANCZOS)
    glow_mask = img.resize((OUT, OUT), Image.LANCZOS)
    return metal_dark, metal_light, glow_mask


def save_top_nav_assets():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    bot_bar_dark = generate_bottom_divider_bar_png(light_theme=False)
    bot_bar_light = generate_bottom_divider_bar_png(light_theme=True)
    glow_orb = generate_glow_orb_png()

    icon_names = ["tune", "arrow-left", "magnify", "home", "star", "star-outline", "cog"]
    icons_dark = {}
    icons_light = {}
    icons_mask = {}

    for name in icon_names:
        md, ml, gm = _draw_top_icon(name)
        icons_dark[name] = md
        icons_light[name] = ml
        icons_mask[name] = gm

    def to_b64(img):
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("utf-8")

    out_path = os.path.join(OUTPUT_DIR, "top_nav_assets.py")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write('"""HD-текстуры металлической разделительной планки и иконок TopNav."""\n\n')
        f.write(f'BOT_BAR_DARK_B64 = "{to_b64(bot_bar_dark)}"\n')
        f.write(f'BOT_BAR_LIGHT_B64 = "{to_b64(bot_bar_light)}"\n')
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
        f.write("from . import top_nav_assets\n")

    print(f"[OK] Сгенерированы HD-текстуры TopNav: {out_path}")


if __name__ == "__main__":
    save_top_nav_assets()
