# metronome_utils/fader_generator.py
import base64
import io
import os
import random
from PIL import Image, ImageDraw, ImageFilter

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "metronome")


def _add_brushed_metal_grain(img, x1, y1, x2, y2, strength=4):
    """Деликатная горизонтальная шлифовка алюминия."""
    rng = random.Random(42)
    grain = Image.new("RGBA", img.size, (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(grain)
    for y in range(y1, y2 + 1):
        delta = rng.randint(-strength, strength)
        if delta > 0:
            g_draw.line([(x1, y), (x2, y)], fill=(255, 255, 255, delta))
        elif delta < 0:
            g_draw.line([(x1, y), (x2, y)], fill=(0, 0, 0, -delta))
    return Image.alpha_composite(img, grain)


def generate_fader_panel_png(light_theme=False):
    """Генерирует HD-текстуру студийной рэковой панели под 4 канала фейдеров."""
    W, H = 960, 780
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    pad = 8
    x1, y1 = pad, pad
    x2, y2 = W - pad, H - pad
    radius = 34

    # 1. Падающая тень всей секции
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle(
        [x1, y1 + 4, x2, y2 + 8],
        radius=radius,
        fill=(0, 0, 0, 110 if light_theme else 210),
    )
    canvas.alpha_composite(sh.filter(ImageFilter.GaussianBlur(radius=6)))

    # 2. Металлическая плита корпуса (Faceplate)
    plate = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    p_draw = ImageDraw.Draw(plate)
    for y in range(y1, y2 + 1):
        t = (y - y1) / max(1, (y2 - y1))
        if light_theme:
            v = int(228 - 34 * t)
            col = (v, v + 2, v + 4, 248)
        else:
            if t < 0.06:
                k = t / 0.06
                v = int(78 - 26 * k)
            elif t < 0.94:
                k = (t - 0.06) / 0.88
                v = int(52 - 22 * k)
            else:
                k = (t - 0.94) / 0.06
                v = int(30 - 10 * k)
            col = (v, v + 2, v + 4, 248)
        p_draw.line([(x1, y), (x2, y)], fill=col)

    plate = _add_brushed_metal_grain(plate, x1, y1, x2, y2, strength=4)

    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=255)
    canvas.paste(plate, (0, 0), mask)

    # 3. Внешняя двойная фаска плиты
    bevel = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bv_draw = ImageDraw.Draw(bevel)
    bv_draw.rounded_rectangle(
        [x1, y1, x2, y2],
        radius=radius,
        outline=(255, 255, 255, 190 if light_theme else 85),
        width=2,
    )
    bv_draw.rounded_rectangle(
        [x1 + 2, y1 + 2, x2 - 2, y2 - 2],
        radius=radius - 2,
        outline=(0, 0, 0, 60 if light_theme else 170),
        width=2,
    )
    canvas.paste(Image.alpha_composite(canvas, bevel), (0, 0), mask)

    # 4. Утопленная центральная ниша под 4 фейдера (Recessed Bay)
    bay_x1, bay_y1 = x1 + 48, y1 + 20
    bay_x2, bay_y2 = x2 - 48, y2 - 20
    bay_r = 24

    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle(
        [bay_x1 - 2, bay_y1 - 1, bay_x2 + 2, bay_y2 + 3],
        radius=bay_r + 2,
        outline=(255, 255, 255, 160 if light_theme else 48),
        width=2,
    )

    bay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    b_draw = ImageDraw.Draw(bay)
    bay_fill = (182, 188, 194, 255) if light_theme else (15, 17, 21, 255)
    b_draw.rounded_rectangle([bay_x1, bay_y1, bay_x2, bay_y2], radius=bay_r, fill=bay_fill)

    bay_sh = Image.new("RGBA", (W, H), (0, 0, 0, 120 if light_theme else 235))
    ImageDraw.Draw(bay_sh).rounded_rectangle(
        [bay_x1 + 4, bay_y1 + 8, bay_x2 - 2, bay_y2 + 6], radius=bay_r, fill=(0, 0, 0, 0)
    )
    bay.alpha_composite(bay_sh.filter(ImageFilter.GaussianBlur(radius=7)))

    bay_mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(bay_mask).rounded_rectangle([bay_x1, bay_y1, bay_x2, bay_y2], radius=bay_r, fill=255)
    canvas.paste(bay, (0, 0), bay_mask)

    # 5. Тонкие вертикальные ребра-разделители между 4 каналами фейдеров
    bay_w = bay_x2 - bay_x1
    for i in (1, 2, 3):
        dx = int(bay_x1 + bay_w * (i / 4.0))
        draw.line(
            [(dx, bay_y1 + 24), (dx, bay_y2 - 24)],
            fill=(145, 152, 158, 160) if light_theme else (38, 42, 48, 190),
            width=2,
        )
        draw.line(
            [(dx + 2, bay_y1 + 24), (dx + 2, bay_y2 - 24)],
            fill=(255, 255, 255, 95) if light_theme else (0, 0, 0, 180),
            width=2,
        )

    # 6. Четыре аппаратных винта под крест по углам консоли
    screw_r = 10
    screw_positions = [
        (x1 + 24, y1 + 28),
        (x2 - 24, y1 + 28),
        (x1 + 24, y2 - 28),
        (x2 - 24, y2 - 28),
    ]
    for sx, sy in screw_positions:
        draw.ellipse(
            [sx - screw_r - 2, sy - screw_r - 2, sx + screw_r + 2, sy + screw_r + 2],
            fill=(110, 116, 122, 220) if light_theme else (8, 10, 12, 240),
        )
        draw.ellipse(
            [sx - screw_r, sy - screw_r, sx + screw_r, sy + screw_r],
            fill=(195, 202, 208, 255) if light_theme else (88, 94, 102, 255),
            outline=(245, 248, 250, 200) if light_theme else (150, 158, 168, 160),
            width=1,
        )
        slot_col = (85, 90, 96, 230) if light_theme else (22, 25, 28, 240)
        draw.line([(sx - 5, sy), (sx + 5, sy)], fill=slot_col, width=2)
        draw.line([(sx, sy - 5), (sx, sy + 5)], fill=slot_col, width=2)

    return canvas


def generate_track_png(light_theme=False):
    """Генерирует утопленный паз трека с внутренней тенью и боковыми рисками."""
    W, H = 140, 460
    cx = W // 2
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    slot_w = 24
    pad_y = 34
    x1 = cx - slot_w // 2
    x2 = cx + slot_w // 2
    y1 = pad_y
    y2 = H - pad_y
    radius = slot_w // 2

    rim_col = (255, 255, 255, 130) if light_theme else (255, 255, 255, 38)
    draw.rounded_rectangle([x1 - 2, y1 - 2, x2 + 2, y2 + 2], radius=radius + 2, outline=rim_col, width=2)

    slot_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(slot_layer)
    s_draw.rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=(10, 12, 15, 250))

    shadow_src = Image.new("RGBA", (W, H), (0, 0, 0, 235))
    sh_draw = ImageDraw.Draw(shadow_src)
    sh_draw.rounded_rectangle([x1 + 3, y1 + 5, x2 + 4, y2 + 5], radius=radius, fill=(0, 0, 0, 0))
    shadow_blur = shadow_src.filter(ImageFilter.GaussianBlur(radius=4))
    slot_layer.alpha_composite(shadow_blur)

    slot_mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(slot_mask).rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=255)
    canvas.paste(slot_layer, (0, 0), slot_mask)

    num_ticks = 17
    for i in range(num_ticks):
        t = i / (num_ticks - 1)
        ty = int(y1 + radius + t * (y2 - y1 - 2 * radius))
        is_major = (i % 4 == 0)
        tick_len = 13 if is_major else 8
        tick_h = 2 if is_major else 1
        gap = 8

        if light_theme:
            # Тёмные графитовые риски шкалы для светлой темы
            alpha = 235 if is_major else 155
            tick_color = (28, 33, 38, alpha)
        else:
            alpha = 195 if is_major else 115
            tick_color = (235, 240, 245, alpha)

        draw.rectangle([x1 - gap - tick_len, ty - tick_h // 2, x1 - gap, ty + (tick_h + 1) // 2], fill=tick_color)
        draw.rectangle([x2 + gap, ty - tick_h // 2, x2 + gap + tick_len, ty + (tick_h + 1) // 2], fill=tick_color)

    meta = {
        "slot_x_norm": [round(x1 / W, 4), round(x2 / W, 4)],
        "slot_y_norm": [round(1.0 - y2 / H, 4), round(1.0 - y1 / H, 4)],
        "travel_y_norm": [round(1.0 - (y2 - radius) / H, 4), round(1.0 - (y1 + radius) / H, 4)],
    }
    return canvas, meta


def generate_knob_png(light_theme=False):
    """Генерирует объёмную металлическую ручку фейдера с фасками и тенью."""
    W, H = 136, 152
    cx = W // 2
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    kw, kh = 66, 72
    kx1 = cx - kw // 2
    ky1 = (H - kh) // 2 - 4
    kx2 = kx1 + kw
    ky2 = ky1 + kh
    radius = 12

    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle(
        [kx1 + 2, ky1 + 10, kx2 + 2, ky2 + 13],
        radius=radius,
        fill=(0, 0, 0, 125 if light_theme else 200),
    )
    canvas.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(radius=7)))

    body = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    b_draw = ImageDraw.Draw(body)
    for y in range(ky1, ky2 + 1):
        t = (y - ky1) / max(1, (ky2 - ky1))
        if light_theme:
            # Светло-алюминиевый градиент в стиле клавиш кнопок light-темы
            if t < 0.16:
                k = t / 0.16
                v = int(248 - 14 * k)
            elif t < 0.52:
                k = (t - 0.16) / 0.36
                v = int(234 - 38 * k)
            elif t < 0.86:
                k = (t - 0.52) / 0.34
                v = int(196 + 22 * k)
            else:
                k = (t - 0.86) / 0.14
                v = int(218 - 34 * k)
            col = (v, v + 2, v + 4, 255)
        else:
            if t < 0.14:
                k = t / 0.14
                v = int(195 - 75 * k)
            elif t < 0.52:
                k = (t - 0.14) / 0.38
                v = int(120 - 88 * k)
            elif t < 0.86:
                k = (t - 0.52) / 0.34
                v = int(32 + 78 * k)
            else:
                k = (t - 0.86) / 0.14
                v = int(110 - 85 * k)
            col = (v, v + 2, v + 5, 255)
        b_draw.line([(kx1, y), (kx2, y)], fill=col)

    body = _add_brushed_metal_grain(body, kx1, ky1, kx2, ky2, strength=3 if light_theme else 4)

    side_shade = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ss_draw = ImageDraw.Draw(side_shade)
    for x in range(kx1, kx2 + 1):
        nx = abs((x - cx) / (kw * 0.5))
        if nx > 0.72:
            a = int((38 if light_theme else 65) * ((nx - 0.72) / 0.28))
            ss_draw.line([(x, ky1), (x, ky2)], fill=(0, 0, 0, a))
    body.alpha_composite(side_shade)

    knob_mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(knob_mask).rounded_rectangle([kx1, ky1, kx2, ky2], radius=radius, fill=255)
    canvas.paste(body, (0, 0), knob_mask)

    bevel = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bv_draw = ImageDraw.Draw(bevel)
    if light_theme:
        bv_draw.rounded_rectangle([kx1, ky1, kx2, ky2], radius=radius, outline=(95, 102, 110, 195), width=2)
        bv_draw.rounded_rectangle([kx1 + 2, ky1 + 2, kx2 - 2, ky2 - 2], radius=radius - 2, outline=(255, 255, 255, 210), width=1)
    else:
        bv_draw.rounded_rectangle([kx1, ky1, kx2, ky2], radius=radius, outline=(225, 232, 240, 155), width=2)
        bv_draw.rounded_rectangle([kx1 + 2, ky1 + 2, kx2 - 2, ky2 - 2], radius=radius - 2, outline=(255, 255, 255, 65), width=1)
    canvas.paste(Image.alpha_composite(canvas, bevel), (0, 0), knob_mask)

    led_w, led_h = 26, 8
    cy_knob = (ky1 + ky2) // 2 - 1
    lx1 = cx - led_w // 2
    ly1 = cy_knob - led_h // 2
    lx2 = cx + led_w // 2
    ly2 = cy_knob + led_h // 2

    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle(
        [lx1 - 2, ly1 - 2, lx2 + 2, ly2 + 2],
        radius=3,
        fill=(14, 18, 20, 245) if light_theme else (10, 12, 14, 240),
        outline=(110, 118, 126, 160) if light_theme else (180, 190, 200, 90),
        width=1,
    )

    meta = {
        "knob_center_y_norm": round(1.0 - cy_knob / H, 4),
        "led_box_norm": [
            round(lx1 / W, 4),
            round(1.0 - ly2 / H, 4),
            round((lx2 - lx1) / W, 4),
            round((ly2 - ly1) / H, 4),
        ],
    }
    return canvas, meta


def save_fader_assets():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    panel_dark = generate_fader_panel_png(light_theme=False)
    panel_light = generate_fader_panel_png(light_theme=True)

    track_img, track_meta = generate_track_png(light_theme=False)
    track_light_img, _ = generate_track_png(light_theme=True)

    knob_img, knob_meta = generate_knob_png(light_theme=False)
    knob_light_img, _ = generate_knob_png(light_theme=True)

    def to_b64(img):
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("utf-8")

    out_path = os.path.join(OUTPUT_DIR, "fader_assets.py")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write('"""Автоматически сгенерированные текстуры студийного фейдера и панели."""\n\n')
        f.write(f"PANEL_SIZE = {panel_dark.size}\n")
        f.write(f'PANEL_DARK_B64 = "{to_b64(panel_dark)}"\n')
        f.write(f'PANEL_LIGHT_B64 = "{to_b64(panel_light)}"\n\n')
        f.write(f"TRACK_SIZE = {track_img.size}\n")
        f.write(f"TRACK_META = {repr(track_meta)}\n")
        f.write(f'TRACK_PNG_BASE64 = "{to_b64(track_img)}"\n')
        f.write(f'TRACK_LIGHT_B64 = "{to_b64(track_light_img)}"\n\n')
        f.write(f"KNOB_SIZE = {knob_img.size}\n")
        f.write(f"KNOB_META = {repr(knob_meta)}\n")
        f.write(f'KNOB_PNG_BASE64 = "{to_b64(knob_img)}"\n')
        f.write(f'KNOB_LIGHT_B64 = "{to_b64(knob_light_img)}"\n')

    init_path = os.path.join(OUTPUT_DIR, "__init__.py")
    with open(init_path, "w", encoding="utf-8") as f:
        f.write("from . import classic_graphite, fader_assets, button_assets\n")

    print(f"[OK] Сгенерированы текстуры фейдера и рэковой панели: {out_path}")


if __name__ == "__main__":
    save_fader_assets()