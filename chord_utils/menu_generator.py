# chord_utils/menu_generator.py
import base64
import io
import math
import os
from PIL import Image, ImageDraw, ImageFilter

from metronome_utils.button_generator import (
    generate_button_well_png,
    generate_keycap_png,
)
from metronome_utils.fader_generator import _add_brushed_metal_grain

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "chords")


def generate_chords_panel_png(theme="dark"):
    """Генерирует рэковую металлическую панель 960x148 под крупные кнопки аккордов (чёрная ниша для зелёной темы)."""
    W, H = 960, 148
    light_theme = theme == "light"
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    pad = 4
    x1, y1 = pad, pad
    x2, y2 = W - pad, H - pad
    radius = 28

    # 1. Металлическая плита
    plate = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    p_draw = ImageDraw.Draw(plate)
    for y in range(y1, y2 + 1):
        t = (y - y1) / max(1, (y2 - y1))
        if light_theme:
            v = int(226 - 30 * t)
            col = (v, v + 2, v + 4, 255)
        else:
            v = int(72 - 36 * t)
            col = (v, v + 2, v + 4, 255)
        p_draw.line([(x1, y), (x2, y)], fill=col)

    plate = _add_brushed_metal_grain(plate, x1, y1, x2, y2, strength=4)
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=255)
    canvas.paste(plate, (0, 0), mask)

    # 2. Фаска
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

    # 3. Широкая утопленная ниша под крупные пэды (тёмно-чёрный фон в dark и green темах)
    bay_x1, bay_y1 = x1 + 36, y1 + 9
    bay_x2, bay_y2 = x2 - 36, y2 - 9
    bay_r = 20

    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle(
        [bay_x1 - 2, bay_y1 - 1, bay_x2 + 2, bay_y2 + 3],
        radius=bay_r + 2,
        outline=(255, 255, 255, 160 if light_theme else 48),
        width=2,
    )

    bay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    b_draw = ImageDraw.Draw(bay)
    if light_theme:
        bay_fill = (182, 188, 194, 255)
        shadow_alpha = 115
    else:
        # И для dark, и для green темы — плотный чёрный фон между кнопками, как в тюнере
        bay_fill = (13, 15, 18, 255)
        shadow_alpha = 240

    b_draw.rounded_rectangle([bay_x1, bay_y1, bay_x2, bay_y2], radius=bay_r, fill=bay_fill)
    bay_sh = Image.new("RGBA", (W, H), (0, 0, 0, shadow_alpha))
    ImageDraw.Draw(bay_sh).rounded_rectangle(
        [bay_x1 + 3, bay_y1 + 6, bay_x2 - 2, bay_y2 + 5], radius=bay_r, fill=(0, 0, 0, 0)
    )
    bay.alpha_composite(bay_sh.filter(ImageFilter.GaussianBlur(radius=6)))

    bay_mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(bay_mask).rounded_rectangle([bay_x1, bay_y1, bay_x2, bay_y2], radius=bay_r, fill=255)
    canvas.paste(bay, (0, 0), bay_mask)

    # 4. Четыре аппаратных винта по углам
    screw_r = 8
    screws = [
        (x1 + 18, y1 + 22),
        (x2 - 18, y1 + 22),
        (x1 + 18, y2 - 22),
        (x2 - 18, y2 - 22),
    ]
    for sx, sy in screws:
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
        draw.line([(sx - 4, sy), (sx + 4, sy)], fill=slot_col, width=2)
        draw.line([(sx, sy - 4), (sx, sy + 4)], fill=slot_col, width=2)

    return canvas



def generate_chord_icon_png(icon_name):
    """Генерирует чёткие белые иконки 192x192 через 4x SSAA для кнопок аккордов."""
    OUT = 192
    SS = 4
    S = OUT * SS
    cx, cy = S // 2, S // 2

    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    W = (255, 255, 255, 255)
    T = (0, 0, 0, 0)

    if icon_name == "tonality":
        # Восьмая нота (music-note-eighth)
        d.ellipse([cx - 122, cy + 44, cx + 10, cy + 162], fill=W)
        d.rectangle([cx - 18, cy - 168, cx + 14, cy + 104], fill=W)
        flag = [
            (cx + 10, cy - 168),
            (cx + 124, cy - 92),
            (cx + 108, cy - 16),
            (cx + 14, cy - 82),
        ]
        d.polygon(flag, fill=W)

    elif icon_name == "type":
        # Бирка / тег типа аккорда (tag)
        tag_poly = [
            (cx - 156, cy - 156),
            (cx + 8, cy - 156),
            (cx + 164, cy),
            (cx, cy + 164),
            (cx - 156, cy + 8),
        ]
        d.polygon(tag_poly, fill=W)
        d.ellipse([cx - 110, cy - 110, cx - 54, cy - 54], fill=T)

    elif icon_name == "chord":
        # Круг с нотой (music-circle)
        r_out = 172
        r_in = 136
        d.ellipse([cx - r_out, cy - r_out, cx + r_out, cy + r_out], fill=W)
        d.ellipse([cx - r_in, cy - r_in, cx + r_in, cy + r_in], fill=T)
        # Нота внутри
        d.ellipse([cx - 64, cy + 20, cx + 14, cy + 92], fill=W)
        d.rectangle([cx - 6, cy - 96, cx + 16, cy + 56], fill=W)
        d.polygon(
            [
                (cx + 12, cy - 96),
                (cx + 76, cy - 52),
                (cx + 66, cy - 8),
                (cx + 14, cy - 46),
            ],
            fill=W,
        )

    elif icon_name == "variants":
        # Нумерованный список вариантов аппликатур (format-list-numbered)
        rows = [cy - 112, cy, cy + 112]
        for idx, ry in enumerate(rows):
            # Точка/индикатор номера слева
            d.rounded_rectangle([cx - 164, ry - 20, cx - 114, ry + 20], radius=10, fill=W)
            # Полоса строки справа
            d.rounded_rectangle([cx - 72, ry - 16, cx + 164, ry + 16], radius=12, fill=W)

    elif icon_name == "finger":
        # Ладонь / постановка пальцев (gesture-tap)
        # Концентрическое кольцо тапа сверху
        d.ellipse([cx - 94, cy - 178, cx + 54, cy - 30], outline=W, width=18)
        # Указательный палец
        d.rounded_rectangle([cx - 42, cy - 116, cx + 4, cy + 48], radius=22, fill=W)
        # Соседние пальцы и ладонь
        d.rounded_rectangle([cx + 12, cy - 42, cx + 54, cy + 52], radius=20, fill=W)
        d.rounded_rectangle([cx + 62, cy - 26, cx + 102, cy + 56], radius=18, fill=W)
        d.rounded_rectangle([cx - 96, cy - 14, cx - 50, cy + 72], radius=20, fill=W)
        d.rounded_rectangle([cx - 74, cy + 14, cx + 102, cy + 164], radius=46, fill=W)

    elif icon_name == "notes":
        # Двойная нота (режим показа нот на грифе)
        d.ellipse([cx - 144, cy + 48, cx - 44, cy + 136], fill=W)
        d.ellipse([cx + 28, cy + 28, cx + 128, cy + 116], fill=W)
        d.rectangle([cx - 66, cy - 122, cx - 42, cy + 92], fill=W)
        d.rectangle([cx + 106, cy - 142, cx + 130, cy + 72], fill=W)
        d.polygon(
            [
                (cx - 66, cy - 134),
                (cx + 130, cy - 154),
                (cx + 130, cy - 112),
                (cx - 66, cy - 92),
            ],
            fill=W,
        )

    elif icon_name == "rotate_land":
        # Поворот в ландшафт
        d.rounded_rectangle([cx - 166, cy - 98, cx + 166, cy + 98], radius=26, outline=W, width=22)
        d.ellipse([cx + 128, cy - 14, cx + 152, cy + 14], fill=W)

    elif icon_name == "rotate_port":
        # Поворот в портрет
        d.rounded_rectangle([cx - 98, cy - 166, cx + 98, cy + 166], radius=26, outline=W, width=22)
        d.ellipse([cx - 14, cy + 128, cx + 14, cy + 152], fill=W)

    return img.resize((OUT, OUT), Image.LANCZOS)


def generate_chords_search_png(theme="dark"):
    """Генерирует рэковую металлическую панель 960x104 для строки поиска аккордов."""
    W, H = 960, 104
    light_theme = theme == "light"
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    pad = 4
    x1, y1 = pad, pad
    x2, y2 = W - pad, H - pad
    radius = 24

    # 1. Металлическая плита
    plate = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    p_draw = ImageDraw.Draw(plate)
    for y in range(y1, y2 + 1):
        t = (y - y1) / max(1, (y2 - y1))
        if light_theme:
            v = int(226 - 30 * t)
            col = (v, v + 2, v + 4, 255)
        else:
            v = int(72 - 36 * t)
            col = (v, v + 2, v + 4, 255)
        p_draw.line([(x1, y), (x2, y)], fill=col)

    plate = _add_brushed_metal_grain(plate, x1, y1, x2, y2, strength=4)
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=255)
    canvas.paste(plate, (0, 0), mask)

    # 2. Фаска
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

    # 3. Утопленная ниша под поле ввода и кнопку поиска
    bay_x1, bay_y1 = x1 + 34, y1 + 9
    bay_x2, bay_y2 = x2 - 34, y2 - 9
    bay_r = 16

    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle(
        [bay_x1 - 2, bay_y1 - 1, bay_x2 + 2, bay_y2 + 3],
        radius=bay_r + 2,
        outline=(255, 255, 255, 160 if light_theme else 48),
        width=2,
    )

    bay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    b_draw = ImageDraw.Draw(bay)
    if light_theme:
        bay_fill = (232, 236, 238, 255)
        shadow_alpha = 95
    else:
        bay_fill = (13, 15, 18, 255)
        shadow_alpha = 235

    b_draw.rounded_rectangle([bay_x1, bay_y1, bay_x2, bay_y2], radius=bay_r, fill=bay_fill)
    bay_sh = Image.new("RGBA", (W, H), (0, 0, 0, shadow_alpha))
    ImageDraw.Draw(bay_sh).rounded_rectangle(
        [bay_x1 + 3, bay_y1 + 5, bay_x2 - 2, bay_y2 + 4], radius=bay_r, fill=(0, 0, 0, 0)
    )
    bay.alpha_composite(bay_sh.filter(ImageFilter.GaussianBlur(radius=5)))

    bay_mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(bay_mask).rounded_rectangle([bay_x1, bay_y1, bay_x2, bay_y2], radius=bay_r, fill=255)
    canvas.paste(bay, (0, 0), bay_mask)

    # 4. Четыре аппаратных винта по углам
    screw_r = 7
    screws = [
        (x1 + 17, y1 + 19),
        (x2 - 17, y1 + 19),
        (x1 + 17, y2 - 19),
        (x2 - 17, y2 - 19),
    ]
    for sx, sy in screws:
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
        draw.line([(sx - 3, sy), (sx + 3, sy)], fill=slot_col, width=2)
        draw.line([(sx, sy - 3), (sx, sy + 3)], fill=slot_col, width=2)

    return canvas


def generate_chords_griff_card_png(theme="dark"):
    """Генерирует рэковый корпус 960x540 для грифа с посадочными нишами под боковую пагинацию."""
    W, H = 960, 540
    light_theme = theme == "light"
    green_theme = theme == "green"
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    pad = 4
    x1, y1 = pad, pad
    x2, y2 = W - pad, H - pad
    radius = 30

    # 1. Металлическая плита корпуса
    plate = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    p_draw = ImageDraw.Draw(plate)
    for y in range(y1, y2 + 1):
        t = (y - y1) / max(1, (y2 - y1))
        if light_theme:
            v = int(228 - 34 * t)
            col = (v, v + 2, v + 4, 255)
        else:
            if t < 0.08:
                v = int(78 - 26 * (t / 0.08))
            elif t < 0.92:
                v = int(52 - 22 * ((t - 0.08) / 0.84))
            else:
                v = int(30 - 10 * ((t - 0.92) / 0.08))
            col = (v, v + 2, v + 4, 255)
        p_draw.line([(x1, y), (x2, y)], fill=col)

    plate = _add_brushed_metal_grain(plate, x1, y1, x2, y2, strength=4)
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=255)
    canvas.paste(plate, (0, 0), mask)

    # 2. Внешняя двойная фаска
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

    draw = ImageDraw.Draw(canvas)

    # 3. Утопленные пазы в левой и правой боковых стойках под кнопки пагинации
    side_slots = [
        (x1 + 10, y1 + 52, x1 + 66, y2 - 52),
        (x2 - 66, y1 + 52, x2 - 10, y2 - 52),
    ]
    for sx1, sy1, sx2, sy2 in side_slots:
        draw.rounded_rectangle(
            [sx1 - 1, sy1 - 1, sx2 + 1, sy2 + 1],
            radius=15,
            outline=(255, 255, 255, 140 if light_theme else 45),
            width=2,
        )
        draw.rounded_rectangle(
            [sx1, sy1, sx2, sy2],
            radius=14,
            fill=(165, 172, 178, 255) if light_theme else (10, 12, 15, 255),
        )

    # 4. Центральная утопленная ниша под гриф аккорда
    bay_x1, bay_y1 = x1 + 76, y1 + 14
    bay_x2, bay_y2 = x2 - 76, y2 - 14
    bay_r = 22

    draw.rounded_rectangle(
        [bay_x1 - 2, bay_y1 - 1, bay_x2 + 2, bay_y2 + 3],
        radius=bay_r + 2,
        outline=(255, 255, 255, 160 if light_theme else 48),
        width=2,
    )

    bay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    b_draw = ImageDraw.Draw(bay)
    if light_theme:
        bay_fill = (186, 192, 198, 255)
        shadow_alpha = 115
    elif green_theme:
        bay_fill = (0, 13, 8, 95)
        shadow_alpha = 165
    else:
        bay_fill = (14, 16, 20, 255)
        shadow_alpha = 235

    b_draw.rounded_rectangle([bay_x1, bay_y1, bay_x2, bay_y2], radius=bay_r, fill=bay_fill)
    bay_sh = Image.new("RGBA", (W, H), (0, 0, 0, shadow_alpha))
    ImageDraw.Draw(bay_sh).rounded_rectangle(
        [bay_x1 + 4, bay_y1 + 7, bay_x2 - 2, bay_y2 + 6], radius=bay_r, fill=(0, 0, 0, 0)
    )
    bay.alpha_composite(bay_sh.filter(ImageFilter.GaussianBlur(radius=7)))

    bay_mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(bay_mask).rounded_rectangle([bay_x1, bay_y1, bay_x2, bay_y2], radius=bay_r, fill=255)
    canvas.paste(bay, (0, 0), bay_mask)

    # 5. Четыре аппаратных винта по углам рамы
    screw_r = 9
    screws = [
        (x1 + 38, y1 + 24),
        (x2 - 38, y1 + 24),
        (x1 + 38, y2 - 24),
        (x2 - 38, y2 - 24),
    ]
    for sx, sy in screws:
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
        draw.line([(sx - 4, sy), (sx + 4, sy)], fill=slot_col, width=2)
        draw.line([(sx, sy - 4), (sx, sy + 4)], fill=slot_col, width=2)

    return canvas




def save_chords_menu_assets():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    panel_dark = generate_chords_panel_png(theme="dark")
    panel_green = generate_chords_panel_png(theme="green")
    panel_light = generate_chords_panel_png(theme="light")

    search_dark = generate_chords_search_png(theme="dark")
    search_green = generate_chords_search_png(theme="green")
    search_light = generate_chords_search_png(theme="light")

    griff_dark = generate_chords_griff_card_png(theme="dark")
    griff_green = generate_chords_griff_card_png(theme="green")
    griff_light = generate_chords_griff_card_png(theme="light")


    well_dark = generate_button_well_png(light_theme=False)
    up_dark, up_meta = generate_keycap_png(pressed=False, light_theme=False)
    down_dark, down_meta = generate_keycap_png(pressed=True, light_theme=False)

    well_light = generate_button_well_png(light_theme=True)
    up_light, _ = generate_keycap_png(pressed=False, light_theme=True)
    down_light, _ = generate_keycap_png(pressed=True, light_theme=True)

    icon_names = [
        "tonality", "type", "chord", "variants",
        "finger", "notes", "rotate_land", "rotate_port",
    ]
    icons_b64 = {name: generate_chord_icon_png(name) for name in icon_names}

    def to_b64(img):
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("utf-8")

    out_path = os.path.join(OUTPUT_DIR, "menu_assets.py")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write('"""HD-текстуры рэковой панели и кнопок меню аккордов."""\n\n')
        f.write(f"PANEL_SIZE = {panel_dark.size}\n")
        f.write(f"BUTTON_SIZE = {well_dark.size}\n")
        f.write(f"UP_META = {repr(up_meta)}\n")
        f.write(f"DOWN_META = {repr(down_meta)}\n\n")
        f.write(f'GRIFF_DARK_B64 = "{to_b64(griff_dark)}"\n')
        f.write(f'GRIFF_GREEN_B64 = "{to_b64(griff_green)}"\n')
        f.write(f'GRIFF_LIGHT_B64 = "{to_b64(griff_light)}"\n\n')
        f.write(f'SEARCH_DARK_B64 = "{to_b64(search_dark)}"\n')
        f.write(f'SEARCH_GREEN_B64 = "{to_b64(search_green)}"\n')
        f.write(f'SEARCH_LIGHT_B64 = "{to_b64(search_light)}"\n\n')
        f.write(f'PANEL_DARK_B64 = "{to_b64(panel_dark)}"\n')
        f.write(f'PANEL_GREEN_B64 = "{to_b64(panel_green)}"\n')
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
    if not os.path.exists(init_path):
        with open(init_path, "w", encoding="utf-8") as f:
            f.write("from . import menu_assets\n")

    print(f"[OK] Сгенерированы ассеты меню аккордов: {out_path}")

if __name__ == "__main__":
    save_chords_menu_assets()



