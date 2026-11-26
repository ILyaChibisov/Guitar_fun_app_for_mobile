# metronome_utils/button_generator.py
import base64
import io
import math
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


def generate_panel_png(light_theme=False):
    """Генерирует HD-текстуру студийной рэковой панели под 4 триггер-пэда."""
    W, H = 960, 180
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    pad = 8
    x1, y1 = pad, pad
    x2, y2 = W - pad, H - pad
    radius = 34

    # 1. Мягкая падающая тень всей консоли
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle(
        [x1, y1 + 4, x2, y2 + 7],
        radius=radius,
        fill=(0, 0, 0, 110 if light_theme else 210),
    )
    canvas.alpha_composite(sh.filter(ImageFilter.GaussianBlur(radius=5)))

    # 2. Металлическая плита корпуса (Faceplate)
    plate = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    p_draw = ImageDraw.Draw(plate)
    for y in range(y1, y2 + 1):
        t = (y - y1) / max(1, (y2 - y1))
        if light_theme:
            v = int(228 - 34 * t)
            col = (v, v + 2, v + 4, 248)
        else:
            if t < 0.12:
                k = t / 0.12
                v = int(78 - 26 * k)
            elif t < 0.88:
                k = (t - 0.12) / 0.76
                v = int(52 - 22 * k)
            else:
                k = (t - 0.88) / 0.12
                v = int(30 - 10 * k)
            col = (v, v + 2, v + 4, 248)
        p_draw.line([(x1, y), (x2, y)], fill=col)

    plate = _add_brushed_metal_grain(plate, x1, y1, x2, y2, strength=4)

    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=255)
    canvas.paste(plate, (0, 0), mask)

    # 3. Внешняя фаска металлической плиты
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

    # 4. Утопленная центральная ниша под кнопки (Recessed Bay)
    bay_x1, bay_y1 = x1 + 48, y1 + 16
    bay_x2, bay_y2 = x2 - 48, y2 - 16
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
    bay_fill = (165, 172, 178, 255) if light_theme else (12, 14, 17, 255)
    b_draw.rounded_rectangle([bay_x1, bay_y1, bay_x2, bay_y2], radius=bay_r, fill=bay_fill)

    bay_sh = Image.new("RGBA", (W, H), (0, 0, 0, 130 if light_theme else 235))
    ImageDraw.Draw(bay_sh).rounded_rectangle(
        [bay_x1 + 4, bay_y1 + 7, bay_x2 - 2, bay_y2 + 6], radius=bay_r, fill=(0, 0, 0, 0)
    )
    bay.alpha_composite(bay_sh.filter(ImageFilter.GaussianBlur(radius=6)))

    bay_mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(bay_mask).rounded_rectangle([bay_x1, bay_y1, bay_x2, bay_y2], radius=bay_r, fill=255)
    canvas.paste(bay, (0, 0), bay_mask)

    # 5. Тонкие вертикальные ребра-разделители между 4 слотами
    bay_w = bay_x2 - bay_x1
    for i in (1, 2, 3):
        dx = int(bay_x1 + bay_w * (i / 4.0))
        draw.line(
            [(dx, bay_y1 + 14), (dx, bay_y2 - 14)],
            fill=(135, 142, 148, 160) if light_theme else (38, 42, 48, 190),
            width=2,
        )
        draw.line(
            [(dx + 2, bay_y1 + 14), (dx + 2, bay_y2 - 14)],
            fill=(255, 255, 255, 90) if light_theme else (0, 0, 0, 180),
            width=2,
        )

    # 6. Четыре аппаратных винта под крест по углам консоли
    screw_r = 10
    screw_positions = [
        (x1 + 24, y1 + 26),
        (x2 - 24, y1 + 26),
        (x1 + 24, y2 - 26),
        (x2 - 24, y2 - 26),
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


def generate_button_well_png(light_theme=False):
    """Генерирует утопленную шахту триггер-пэда без белёсых ореолов."""
    W, H = 320, 240
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    pad_x, pad_y = 22, 18
    x1, y1 = pad_x, pad_y
    x2, y2 = W - pad_x, H - pad_y
    radius = 34

    outer_col = (140, 148, 155, 235) if light_theme else (6, 8, 10, 245)
    draw.rounded_rectangle(
        [x1 - 2, y1 - 2, x2 + 2, y2 + 2],
        radius=radius + 2,
        fill=outer_col,
    )

    well = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    w_draw = ImageDraw.Draw(well)
    base_fill = (175, 182, 188, 255) if light_theme else (12, 14, 18, 255)
    w_draw.rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=base_fill)

    sh = Image.new("RGBA", (W, H), (0, 0, 0, 140 if light_theme else 245))
    ImageDraw.Draw(sh).rounded_rectangle(
        [x1 + 5, y1 + 8, x2 - 2, y2 + 6], radius=radius, fill=(0, 0, 0, 0)
    )
    well.alpha_composite(sh.filter(ImageFilter.GaussianBlur(radius=6)))

    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=255)
    canvas.paste(well, (0, 0), mask)

    return canvas


def generate_keycap_png(pressed=False, light_theme=False):
    """Генерирует корпус пэда с утопленным пазом световода по периметру."""
    W, H = 320, 240
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    inset_x = 34 if pressed else 30
    inset_y = 30 if pressed else 24
    offset_y = 3 if pressed else -2

    kx1, ky1 = inset_x, inset_y + offset_y
    kx2, ky2 = W - inset_x, H - inset_y + offset_y
    radius = 26

    if not pressed:
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle(
            [kx1 + 1, ky1 + 8, kx2 - 1, ky2 + 11],
            radius=radius,
            fill=(0, 0, 0, 120 if light_theme else 225),
        )
        canvas.alpha_composite(sh.filter(ImageFilter.GaussianBlur(radius=6)))

    body = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    b_draw = ImageDraw.Draw(body)
    for y in range(ky1, ky2 + 1):
        t = (y - ky1) / max(1, (ky2 - ky1))
        if light_theme:
            if pressed:
                v = int(205 - 25 * t)
            else:
                v = int(242 - 42 * t)
            col = (v, v + 2, v + 4, 255)
        else:
            if pressed:
                v = int(66 - 26 * t)
            else:
                if t < 0.14:
                    k = t / 0.14
                    v = int(190 - 72 * k)
                elif t < 0.85:
                    k = (t - 0.14) / 0.71
                    v = int(118 - 74 * k)
                else:
                    k = (t - 0.85) / 0.15
                    v = int(44 - 18 * k)
            col = (v, v + 2, v + 5, 255)
        b_draw.line([(kx1, y), (kx2, y)], fill=col)

    body = _add_brushed_metal_grain(body, kx1, ky1, kx2, ky2, strength=4)

    cx = W * 0.5
    half_w = (kx2 - kx1) * 0.5
    side_shade = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ss_draw = ImageDraw.Draw(side_shade)
    for x in range(kx1, kx2 + 1):
        nx = abs((x - cx) / max(1.0, half_w))
        if nx > 0.76:
            a = int((35 if light_theme else 60) * ((nx - 0.76) / 0.24))
            ss_draw.line([(x, ky1), (x, ky2)], fill=(0, 0, 0, a))
    body.alpha_composite(side_shade)

    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).rounded_rectangle([kx1, ky1, kx2, ky2], radius=radius, fill=255)
    canvas.paste(body, (0, 0), mask)

    bevel = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bv_draw = ImageDraw.Draw(bevel)
    edge_col = (255, 255, 255, 210) if light_theme else (225, 232, 240, 105 if pressed else 175)
    bv_draw.rounded_rectangle(
        [kx1, ky1, kx2, ky2],
        radius=radius,
        outline=edge_col,
        width=2,
    )
    canvas.paste(Image.alpha_composite(canvas, bevel), (0, 0), mask)

    rim_pad = 12
    rx1, ry1 = kx1 + rim_pad, ky1 + rim_pad
    rx2, ry2 = kx2 - rim_pad, ky2 - rim_pad
    rim_r = max(8, radius - rim_pad)

    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle(
        [rx1, ry1, rx2, ry2],
        radius=rim_r,
        outline=(90, 96, 102, 180) if light_theme else (12, 14, 18, 220),
        width=5,
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


def generate_icon_png(icon_name):
    """Генерирует крупные и чёткие иконки 192x192 через 4x суперсэмплинг (768x768 -> 192x192)."""
    OUT = 192
    SS = 4
    S = OUT * SS
    cx, cy = S // 2, S // 2

    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    W = (255, 255, 255, 255)
    T = (0, 0, 0, 0)

    if icon_name == "play":
        d.polygon(
            [
                (cx - 126, cy - 172),
                (cx - 126, cy + 172),
                (cx + 176, cy),
            ],
            fill=W,
        )

    elif icon_name == "stop":
        r = 148
        d.rounded_rectangle([cx - r, cy - r, cx + r, cy + r], radius=38, fill=W)

    elif icon_name == "reset":
        r_out = 172
        r_in = 120
        d.ellipse([cx - r_out, cy - r_out, cx + r_out, cy + r_out], fill=W)
        d.ellipse([cx - r_in, cy - r_in, cx + r_in, cy + r_in], fill=T)

        d.pieslice(
            [cx - r_out - 16, cy - r_out - 16, cx + r_out + 16, cy + r_out + 16],
            start=-52,
            end=22,
            fill=T,
        )

        r_mid = (r_out + r_in) * 0.5
        thick = (r_out - r_in) * 0.5
        end_rad = math.radians(22)
        ex = cx + r_mid * math.cos(end_rad)
        ey = cy + r_mid * math.sin(end_rad)
        d.ellipse([ex - thick, ey - thick, ex + thick, ey + thick], fill=W)

        tip_rad = math.radians(-52)
        bx = cx + r_mid * math.cos(tip_rad)
        by = cy + r_mid * math.sin(tip_rad)
        tx, ty = -math.sin(tip_rad), math.cos(tip_rad)
        nx, ny = math.cos(tip_rad), math.sin(tip_rad)

        p1 = (bx + tx * 82, by + ty * 82)
        p2 = (bx - tx * 34 + nx * 68, by - ty * 34 + ny * 68)
        p3 = (bx - tx * 34 - nx * 68, by - ty * 34 - ny * 68)
        d.polygon([p1, p2, p3], fill=W)

    elif icon_name == "accent":
        head = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        hd = ImageDraw.Draw(head)
        hd.ellipse([cx - 84, cy - 58, cx + 84, cy + 58], fill=W)
        head = head.rotate(24, resample=Image.BICUBIC, center=(cx, cy))
        img.alpha_composite(head, (-52, 114))

        stem_x1 = cx + 4
        stem_x2 = cx + 48
        top_y = cy - 182
        bot_y = cy + 108
        d.rounded_rectangle([stem_x1, top_y, stem_x2, bot_y], radius=14, fill=W)

        d.polygon(
            [
                (stem_x1 + 8, top_y),
                (cx + 156, top_y + 66),
                (cx + 156, top_y + 122),
                (stem_x1 + 8, top_y + 56),
            ],
            fill=W,
        )

    elif icon_name == "accent_off":
        base_note = generate_icon_png("accent").resize((S, S), Image.LANCZOS)
        img.alpha_composite(base_note)
        d.line([(cx - 160, cy + 160), (cx + 160, cy - 160)], fill=T, width=66)
        d.line([(cx - 150, cy + 150), (cx + 150, cy - 150)], fill=W, width=36)
        for px, py in [(cx - 150, cy + 150), (cx + 150, cy - 150)]:
            d.ellipse([px - 18, py - 18, px + 18, py + 18], fill=W)

    elif icon_name == "tone":
        d.rounded_rectangle([cx - 172, cy - 64, cx - 94, cy + 64], radius=18, fill=W)
        d.polygon(
            [
                (cx - 112, cy - 64),
                (cx - 10, cy - 144),
                (cx - 10, cy + 144),
                (cx - 112, cy + 64),
            ],
            fill=W,
        )
        for r_arc in (98, 164):
            arc_layer = Image.new("RGBA", (S, S), (0, 0, 0, 0))
            ad = ImageDraw.Draw(arc_layer)
            thick = 36
            ad.pieslice(
                [cx - 20 - r_arc, cy - r_arc, cx - 20 + r_arc, cy + r_arc],
                start=-44,
                end=44,
                fill=W,
            )
            r_in = r_arc - thick
            ad.pieslice(
                [cx - 20 - r_in - 3, cy - r_in - 3, cx - 20 + r_in + 3, cy + r_in + 3],
                start=-50,
                end=50,
                fill=T,
            )
            r_m = r_arc - thick * 0.5
            cap_r = thick * 0.5
            for deg in (-44, 44):
                rad = math.radians(deg)
                px = (cx - 20) + r_m * math.cos(rad)
                py = cy + r_m * math.sin(rad)
                ad.ellipse([px - cap_r, py - cap_r, px + cap_r, py + cap_r], fill=W)
            img.alpha_composite(arc_layer)

    return img.resize((OUT, OUT), Image.LANCZOS)


def save_button_assets():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    panel_dark = generate_panel_png(light_theme=False)
    panel_light = generate_panel_png(light_theme=True)

    well_dark = generate_button_well_png(light_theme=False)
    up_dark, up_meta = generate_keycap_png(pressed=False, light_theme=False)
    down_dark, down_meta = generate_keycap_png(pressed=True, light_theme=False)

    well_light = generate_button_well_png(light_theme=True)
    up_light, _ = generate_keycap_png(pressed=False, light_theme=True)
    down_light, _ = generate_keycap_png(pressed=True, light_theme=True)

    icon_names = ["play", "stop", "reset", "accent", "accent_off", "tone"]
    icons_b64 = {name: generate_icon_png(name) for name in icon_names}

    def to_b64(img):
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("utf-8")

    out_path = os.path.join(OUTPUT_DIR, "button_assets.py")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write('"""HD-текстуры рэковой панели, триггер-пэдов (dark/light) и 4x SSAA иконок."""\n\n')
        f.write(f"PANEL_SIZE = {panel_dark.size}\n")
        f.write(f"BUTTON_SIZE = {well_dark.size}\n")
        f.write(f"UP_META = {repr(up_meta)}\n")
        f.write(f"DOWN_META = {repr(down_meta)}\n\n")
        f.write(f'PANEL_DARK_B64 = "{to_b64(panel_dark)}"\n')
        f.write(f'PANEL_LIGHT_B64 = "{to_b64(panel_light)}"\n\n')
        f.write(f'WELL_DARK_B64 = "{to_b64(well_dark)}"\n')
        f.write(f'KEY_UP_DARK_B64 = "{to_b64(up_dark)}"\n')
        f.write(f'KEY_DOWN_DARK_B64 = "{to_b64(down_dark)}"\n\n')
        f.write(f'WELL_LIGHT_B64 = "{to_b64(well_light)}"\n')
        f.write(f'KEY_UP_LIGHT_B64 = "{to_b64(up_light)}"\n')
        f.write(f'KEY_DOWN_LIGHT_B64 = "{to_b64(down_light)}"\n\n')
        f.write("ICONS_PNG_BASE64 = {\n")
        for name, img in icons_b64.items():
            f.write(f'    "{name}": "{to_b64(img)}",\n')
        f.write("}\n")

    init_path = os.path.join(OUTPUT_DIR, "__init__.py")
    with open(init_path, "w", encoding="utf-8") as f:
        f.write("from . import classic_graphite, fader_assets, button_assets\n")

    print(f"[OK] Сгенерированы HD-текстуры рэковой панели и триггер-пэдов: {out_path}")


if __name__ == "__main__":
    save_button_assets()