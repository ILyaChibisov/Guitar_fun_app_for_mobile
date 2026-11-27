# songs_alfa_utils/menu_generator.py
import base64
import io
import os
from PIL import Image, ImageDraw, ImageFilter

from metronome_utils.button_generator import (
    generate_button_well_png,
    generate_keycap_png,
)
from metronome_utils.fader_generator import _add_brushed_metal_grain

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "songs_alfa")


def generate_songs_header_png(theme="dark"):
    """Генерирует двухъярусную рэковую консоль 960x216: верхний отсек — алфавит, нижний — поиск."""
    W, H = 960, 216
    light_theme = theme == "light"
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    pad = 4
    x1, y1 = pad, pad
    x2, y2 = W - pad, H - pad
    radius = 28

    # 1. Внешняя шлифованная металлическая плита
    plate = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    p_draw = ImageDraw.Draw(plate)
    for y in range(y1, y2 + 1):
        t = (y - y1) / max(1, (y2 - y1))
        if light_theme:
            v = int(228 - 32 * t)
            col = (v, v + 2, v + 4, 255)
        else:
            v = int(74 - 38 * t)
            col = (v, v + 2, v + 4, 255)
        p_draw.line([(x1, y), (x2, y)], fill=col)

    plate = _add_brushed_metal_grain(plate, x1, y1, x2, y2, strength=4)
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=255)
    canvas.paste(plate, (0, 0), mask)

    # 2. Двойная фаска плиты
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

    # 3. Две утопленные ниши, разделённые металлической перемычкой консоли
    # Верхняя ниша (алфавит): y = 14..100, нижняя ниша (поиск): y = 114..202
    bays = [
        (x1 + 36, 14, x2 - 36, 100, (186, 192, 198, 255) if light_theme else (13, 15, 18, 255)),
        (x1 + 36, 114, x2 - 36, 202, (232, 236, 238, 255) if light_theme else (13, 15, 18, 255)),
    ]
    bay_r = 16

    for bx1, by1, bx2, by2, bay_fill in bays:
        draw.rounded_rectangle(
            [bx1 - 2, by1 - 1, bx2 + 2, by2 + 3],
            radius=bay_r + 2,
            outline=(255, 255, 255, 160 if light_theme else 48),
            width=2,
        )

        bay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        b_draw = ImageDraw.Draw(bay)
        b_draw.rounded_rectangle([bx1, by1, bx2, by2], radius=bay_r, fill=bay_fill)

        shadow_alpha = 105 if light_theme else 235
        bay_sh = Image.new("RGBA", (W, H), (0, 0, 0, shadow_alpha))
        ImageDraw.Draw(bay_sh).rounded_rectangle(
            [bx1 + 3, by1 + 5, bx2 - 2, by2 + 4], radius=bay_r, fill=(0, 0, 0, 0)
        )
        bay.alpha_composite(bay_sh.filter(ImageFilter.GaussianBlur(radius=5)))

        bay_mask = Image.new("L", (W, H), 0)
        ImageDraw.Draw(bay_mask).rounded_rectangle([bx1, by1, bx2, by2], radius=bay_r, fill=255)
        canvas.paste(bay, (0, 0), bay_mask)

    # Лёгкий световой блик на центральной металлической перемычке между ярусами
    draw.line([(x1 + 42, 106), (x2 - 42, 106)], fill=(255, 255, 255, 130 if light_theme else 42), width=1)
    draw.line([(x1 + 42, 108), (x2 - 42, 108)], fill=(0, 0, 0, 50 if light_theme else 160), width=1)

    # 4. Четыре аппаратных винта по углам консоли
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


def save_songs_alfa_assets():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    header_dark = generate_songs_header_png(theme="dark")
    header_green = generate_songs_header_png(theme="green")
    header_light = generate_songs_header_png(theme="light")

    well_dark = generate_button_well_png(light_theme=False)
    up_dark, up_meta = generate_keycap_png(pressed=False, light_theme=False)
    down_dark, down_meta = generate_keycap_png(pressed=True, light_theme=False)

    well_light = generate_button_well_png(light_theme=True)
    up_light, _ = generate_keycap_png(pressed=False, light_theme=True)
    down_light, _ = generate_keycap_png(pressed=True, light_theme=True)

    def to_b64(img):
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("utf-8")

    out_path = os.path.join(OUTPUT_DIR, "menu_assets.py")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write('"""HD-текстуры объединенного блока алфавита и поиска экрана песен."""\n\n')
        f.write(f"HEADER_SIZE = {header_dark.size}\n")
        f.write(f"BUTTON_SIZE = {well_dark.size}\n")
        f.write(f"UP_META = {repr(up_meta)}\n")
        f.write(f"DOWN_META = {repr(down_meta)}\n\n")
        f.write(f'HEADER_DARK_B64 = "{to_b64(header_dark)}"\n')
        f.write(f'HEADER_GREEN_B64 = "{to_b64(header_green)}"\n')
        f.write(f'HEADER_LIGHT_B64 = "{to_b64(header_light)}"\n\n')
        f.write(f'WELL_DARK_B64 = "{to_b64(well_dark)}"\n')
        f.write(f'KEY_UP_DARK_B64 = "{to_b64(up_dark)}"\n')
        f.write(f'KEY_DOWN_DARK_B64 = "{to_b64(down_dark)}"\n\n')
        f.write(f'WELL_LIGHT_B64 = "{to_b64(well_light)}"\n')
        f.write(f'KEY_UP_LIGHT_B64 = "{to_b64(up_light)}"\n')
        f.write(f'KEY_DOWN_LIGHT_B64 = "{to_b64(down_light)}"\n')

    init_path = os.path.join(OUTPUT_DIR, "__init__.py")
    if not os.path.exists(init_path):
        with open(init_path, "w", encoding="utf-8") as f:
            f.write("from . import menu_assets\n")

    pkg_init = os.path.join(os.path.dirname(os.path.abspath(__file__)), "__init__.py")
    if not os.path.exists(pkg_init):
        with open(pkg_init, "w", encoding="utf-8") as f:
            f.write("")

    print(f"[OK] Сгенерированы ассеты songs_alfa: {out_path}")


if __name__ == "__main__":
    save_songs_alfa_assets()
