# favorites_utils/pagination_generator.py
import base64
import io
import os
import random
from PIL import Image, ImageDraw, ImageFilter

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "favorites")


def _add_brushed_metal_grain(img, x1, y1, x2, y2, strength=4):
    """Деликатная горизонтальная шлифовка алюминия."""
    rng = random.Random(204)
    grain = Image.new("RGBA", img.size, (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(grain)
    for y in range(y1, y2 + 1):
        delta = rng.randint(-strength, strength)
        if delta > 0:
            g_draw.line([(x1, y), (x2, y)], fill=(255, 255, 255, delta))
        elif delta < 0:
            g_draw.line([(x1, y), (x2, y)], fill=(0, 0, 0, -delta))
    return Image.alpha_composite(img, grain)


def _draw_screw(draw, sx, sy, r=7, light_theme=False):
    """Рисует аппаратный винт под крест."""
    draw.ellipse(
        [sx - r - 2, sy - r - 2, sx + r + 2, sy + r + 2],
        fill=(115, 121, 127, 220) if light_theme else (8, 10, 12, 240),
    )
    draw.ellipse(
        [sx - r, sy - r, sx + r, sy + r],
        fill=(198, 205, 211, 255) if light_theme else (88, 94, 102, 255),
        outline=(245, 248, 250, 200) if light_theme else (150, 158, 168, 160),
        width=1,
    )
    slot_col = (85, 90, 96, 230) if light_theme else (22, 25, 28, 240)
    draw.line([(sx - 3, sy), (sx + 3, sy)], fill=slot_col, width=2)
    draw.line([(sx, sy - 3), (sx, sy + 3)], fill=slot_col, width=2)


def generate_pagination_panel_png(light_theme=False):
    """Генерирует HD-текстуру студийной мини-консоли пагинации (без внешних теней)."""
    W, H = 640, 116
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    x1, y1 = 2, 2
    x2, y2 = W - 2, H - 2
    radius = 26

    # 1. Металлический корпус консоли
    plate = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    p_draw = ImageDraw.Draw(plate)
    for y in range(y1, y2 + 1):
        t = (y - y1) / max(1, (y2 - y1))
        if light_theme:
            v = int(232 - 32 * t)
            col = (v, v + 2, v + 4, 252)
        else:
            if t < 0.14:
                k = t / 0.14
                v = int(78 - 25 * k)
            elif t < 0.88:
                k = (t - 0.14) / 0.74
                v = int(53 - 23 * k)
            else:
                k = (t - 0.88) / 0.12
                v = int(30 - 8 * k)
            col = (v, v + 2, v + 4, 252)
        p_draw.line([(x1, y), (x2, y)], fill=col)

    plate = _add_brushed_metal_grain(plate, x1, y1, x2, y2, strength=4)

    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=255)
    canvas.paste(plate, (0, 0), mask)

    # 2. Двойная фаска корпуса
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

    # 3. Утопленная ниша под кнопки и центральный дисплей
    bay_x1, bay_y1 = x1 + 36, y1 + 11
    bay_x2, bay_y2 = x2 - 36, y2 - 11
    bay_r = 18

    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle(
        [bay_x1 - 2, bay_y1 - 1, bay_x2 + 2, bay_y2 + 2],
        radius=bay_r + 2,
        outline=(255, 255, 255, 165 if light_theme else 48),
        width=2,
    )

    bay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    b_draw = ImageDraw.Draw(bay)
    bay_fill = (172, 179, 185, 255) if light_theme else (12, 14, 18, 255)
    b_draw.rounded_rectangle([bay_x1, bay_y1, bay_x2, bay_y2], radius=bay_r, fill=bay_fill)

    bay_sh = Image.new("RGBA", (W, H), (0, 0, 0, 125 if light_theme else 235))
    ImageDraw.Draw(bay_sh).rounded_rectangle(
        [bay_x1 + 3, bay_y1 + 6, bay_x2 - 2, bay_y2 + 5], radius=bay_r, fill=(0, 0, 0, 0)
    )
    bay.alpha_composite(bay_sh.filter(ImageFilter.GaussianBlur(radius=5)))

    bay_mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(bay_mask).rounded_rectangle([bay_x1, bay_y1, bay_x2, bay_y2], radius=bay_r, fill=255)
    canvas.paste(bay, (0, 0), bay_mask)

    # 4. Четыре аппаратных винта по бокам консоли
    for sx, sy in [
        (x1 + 18, y1 + 22),
        (x2 - 18, y1 + 22),
        (x1 + 18, y2 - 22),
        (x2 - 18, y2 - 22),
    ]:
        _draw_screw(draw, sx, sy, r=7, light_theme=light_theme)

    return canvas


def generate_pag_keycap_png(pressed=False, light_theme=False):
    """Генерирует металлическую мини-клавишу пагинации со световодным пазом (без внешней тени)."""
    W, H = 128, 112
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    inset_x = 12 if pressed else 9
    inset_y = 12 if pressed else 8
    offset_y = 2 if pressed else -1

    kx1, ky1 = inset_x, inset_y + offset_y
    kx2, ky2 = W - inset_x, H - inset_y + offset_y
    radius = 16

    body = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    b_draw = ImageDraw.Draw(body)
    for y in range(ky1, ky2 + 1):
        t = (y - ky1) / max(1, (ky2 - ky1))
        if light_theme:
            v = int(204 - 22 * t) if pressed else int(244 - 40 * t)
            col = (v, v + 2, v + 4, 255)
        else:
            if pressed:
                v = int(66 - 24 * t)
            else:
                if t < 0.16:
                    k = t / 0.16
                    v = int(188 - 70 * k)
                elif t < 0.85:
                    k = (t - 0.16) / 0.69
                    v = int(118 - 74 * k)
                else:
                    k = (t - 0.85) / 0.15
                    v = int(44 - 16 * k)
            col = (v, v + 2, v + 5, 255)
        b_draw.line([(kx1, y), (kx2, y)], fill=col)

    body = _add_brushed_metal_grain(body, kx1, ky1, kx2, ky2, strength=3)

    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).rounded_rectangle([kx1, ky1, kx2, ky2], radius=radius, fill=255)
    canvas.paste(body, (0, 0), mask)

    bevel = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bv_draw = ImageDraw.Draw(bevel)
    edge_col = (255, 255, 255, 210) if light_theme else (225, 232, 240, 105 if pressed else 175)
    bv_draw.rounded_rectangle([kx1, ky1, kx2, ky2], radius=radius, outline=edge_col, width=2)
    canvas.paste(Image.alpha_composite(canvas, bevel), (0, 0), mask)

    rim_pad = 7
    rx1, ry1 = kx1 + rim_pad, ky1 + rim_pad
    rx2, ry2 = kx2 - rim_pad, ky2 - rim_pad
    rim_r = max(6, radius - rim_pad)

    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle(
        [rx1, ry1, rx2, ry2],
        radius=rim_r,
        outline=(90, 96, 102, 180) if light_theme else (12, 14, 18, 220),
        width=3,
    )

    meta = {
        "rim_box_norm": [
            round(rx1 / W, 4),
            round(1.0 - ry2 / H, 4),
            round((rx2 - rx1) / W, 4),
            round((ry2 - ry1) / H, 4),
        ],
        "rim_radius_norm": round(rim_r / H, 4),
        "center_y_norm": round(1.0 - ((ky1 + ky2) * 0.5) / H, 4),
    }
    return canvas, meta


def generate_mixer_display_png(light_theme=False):
    """Генерирует чистое утопленное окошко LED-дисплея микшера (без горизонтальных полос)."""
    W, H = 180, 112
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    x1, y1 = 8, 8
    x2, y2 = W - 8, H - 8
    r = 16

    # Металлическая рамка дисплея
    draw.rounded_rectangle(
        [x1 - 2, y1 - 2, x2 + 2, y2 + 2],
        radius=r + 2,
        outline=(255, 255, 255, 190 if light_theme else 75),
        width=2,
    )

    # Чистое тёмное стекло LED-дисплея
    scr = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(scr)
    s_draw.rounded_rectangle([x1, y1, x2, y2], radius=r, fill=(8, 11, 10, 252))

    # Внутренняя тень по верхнему краю стекла
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 220))
    ImageDraw.Draw(sh).rounded_rectangle([x1 + 3, y1 + 6, x2 - 2, y2 + 4], radius=r, fill=(0, 0, 0, 0))
    scr.alpha_composite(sh.filter(ImageFilter.GaussianBlur(radius=4)))

    # Деликатный стеклянный блик в верхней трети
    s_draw.rounded_rectangle(
        [x1 + 6, y1 + 4, x2 - 6, y1 + int((y2 - y1) * 0.34)],
        radius=r - 4,
        fill=(255, 255, 255, 14),
    )

    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).rounded_rectangle([x1, y1, x2, y2], radius=r, fill=255)
    canvas.paste(scr, (0, 0), mask)

    meta = {
        "glass_box_norm": [
            round(x1 / W, 4),
            round(1.0 - y2 / H, 4),
            round((x2 - x1) / W, 4),
            round((y2 - y1) / H, 4),
        ],
        "glass_radius_norm": round(r / H, 4),
    }
    return canvas, meta



def generate_arrow_icon_png(icon_name):
    """Генерирует чёткие 4x SSAA стрелки ('prev', 'next', 'first', 'last')."""
    OUT = 128
    SS = 4
    S = OUT * SS  # 512x512
    cx, cy = S // 2, S // 2

    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    W = (255, 255, 255, 255)

    def draw_chevron(offset_x, direction=1):
        # direction = -1 (влево), +1 (вправо)
        dx = direction * 68
        dy = 112
        thick = 36
        pts = [
            (cx + offset_x - dx * 0.5, cy - dy),
            (cx + offset_x + dx * 0.5, cy),
            (cx + offset_x - dx * 0.5, cy + dy),
        ]
        d.line(pts, fill=W, width=thick, joint="curve")
        for px, py in pts:
            d.ellipse([px - thick * 0.5, py - thick * 0.5, px + thick * 0.5, py + thick * 0.5], fill=W)

    if icon_name == "prev":
        draw_chevron(0, direction=-1)
    elif icon_name == "next":
        draw_chevron(0, direction=1)
    elif icon_name == "first":
        draw_chevron(-44, direction=-1)
        draw_chevron(48, direction=-1)
    elif icon_name == "last":
        draw_chevron(-48, direction=1)
        draw_chevron(44, direction=1)

    return img.resize((OUT, OUT), Image.LANCZOS)


def save_pagination_assets():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    panel_dark = generate_pagination_panel_png(light_theme=False)
    panel_light = generate_pagination_panel_png(light_theme=True)

    up_dark, up_meta = generate_pag_keycap_png(pressed=False, light_theme=False)
    down_dark, down_meta = generate_pag_keycap_png(pressed=True, light_theme=False)

    up_light, _ = generate_pag_keycap_png(pressed=False, light_theme=True)
    down_light, _ = generate_pag_keycap_png(pressed=True, light_theme=True)

    disp_dark, disp_meta = generate_mixer_display_png(light_theme=False)
    disp_light, _ = generate_mixer_display_png(light_theme=True)

    arrows = {name: generate_arrow_icon_png(name) for name in ("first", "prev", "next", "last")}

    def to_b64(img):
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("utf-8")

    out_path = os.path.join(OUTPUT_DIR, "pagination_assets.py")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write('"""HD-текстуры мини-консоли пагинации, пэдов и LED-дисплея микшера."""\n\n')
        f.write(f"UP_META = {repr(up_meta)}\n")
        f.write(f"DOWN_META = {repr(down_meta)}\n")
        f.write(f"DISP_META = {repr(disp_meta)}\n\n")
        f.write(f'PANEL_DARK_B64 = "{to_b64(panel_dark)}"\n')
        f.write(f'PANEL_LIGHT_B64 = "{to_b64(panel_light)}"\n\n')
        f.write(f'KEY_UP_DARK_B64 = "{to_b64(up_dark)}"\n')
        f.write(f'KEY_DOWN_DARK_B64 = "{to_b64(down_dark)}"\n\n')
        f.write(f'KEY_UP_LIGHT_B64 = "{to_b64(up_light)}"\n')
        f.write(f'KEY_DOWN_LIGHT_B64 = "{to_b64(down_light)}"\n\n')
        f.write(f'DISP_DARK_B64 = "{to_b64(disp_dark)}"\n')
        f.write(f'DISP_LIGHT_B64 = "{to_b64(disp_light)}"\n\n')
        f.write("ARROWS_PNG_BASE64 = {\n")
        for name, img in arrows.items():
            f.write(f'    "{name}": "{to_b64(img)}",\n')
        f.write("}\n")

    init_path = os.path.join(OUTPUT_DIR, "__init__.py")
    with open(init_path, "w", encoding="utf-8") as f:
        f.write("from . import card_assets, pagination_assets\n")

    print(f"[OK] Сгенерированы HD-текстуры мини-консоли пагинации: {out_path}")


if __name__ == "__main__":
    save_pagination_assets()