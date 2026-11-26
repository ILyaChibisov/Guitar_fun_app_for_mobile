# home_utils/card_generator.py
import base64
import io
import os
import random
from PIL import Image, ImageChops, ImageDraw, ImageFilter

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "home")


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


def _draw_phillips_screw(draw, sx, sy, screw_r=9, light_theme=False):
    """Рисует аппаратный винт под крест (1-в-1 как в консоли метронома)."""
    draw.ellipse(
        [sx - screw_r - 2, sy - screw_r - 2, sx + screw_r + 2, sy + screw_r + 2],
        fill=(110, 116, 122, 225) if light_theme else (8, 10, 12, 245),
    )
    draw.ellipse(
        [sx - screw_r, sy - screw_r, sx + screw_r, sy + screw_r],
        fill=(195, 202, 208, 255) if light_theme else (88, 94, 102, 255),
        outline=(245, 248, 250, 205) if light_theme else (150, 158, 168, 165),
        width=1,
    )
    slot_col = (85, 90, 96, 235) if light_theme else (22, 25, 28, 245)
    half = max(3, screw_r // 2)
    draw.line([(sx - half, sy), (sx + half, sy)], fill=slot_col, width=2)
    draw.line([(sx, sy - half), (sx, sy + half)], fill=slot_col, width=2)


def generate_home_rack_frame_png(light_theme=False):
    """
    Генерирует студийную рэковую рамку для карточки главного экрана:
    - широкие боковые планки с 4 винтами под крест (как на консолях метронома)
    - прозрачная внутренняя ниша под цветную заливку раздела
    - без внешних теней.
    """
    W, H = 360, 440
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    x1, y1 = 2, 2
    x2, y2 = W - 2, H - 2
    radius = 38

    # 1. Металлическая плита корпуса (Faceplate)
    plate = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    p_draw = ImageDraw.Draw(plate)
    for y in range(y1, y2 + 1):
        t = (y - y1) / max(1, (y2 - y1))
        if light_theme:
            v = int(230 - 34 * t)
            col = (v, v + 2, v + 4, 255)
        else:
            if t < 0.08:
                k = t / 0.08
                v = int(80 - 26 * k)
            elif t < 0.92:
                k = (t - 0.08) / 0.84
                v = int(54 - 24 * k)
            else:
                k = (t - 0.92) / 0.08
                v = int(30 - 10 * k)
            col = (v, v + 2, v + 5, 255)
        p_draw.line([(x1, y), (x2, y)], fill=col)

    plate = _add_brushed_metal_grain(plate, x1, y1, x2, y2, strength=4)

    outer_mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(outer_mask).rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=255)
    canvas.paste(plate, (0, 0), outer_mask)

    # 2. Внешняя двойная фаска металлической плиты
    bevel = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bv_draw = ImageDraw.Draw(bevel)
    bv_draw.rounded_rectangle(
        [x1, y1, x2, y2],
        radius=radius,
        outline=(255, 255, 255, 195 if light_theme else 90),
        width=2,
    )
    bv_draw.rounded_rectangle(
        [x1 + 2, y1 + 2, x2 - 2, y2 - 2],
        radius=radius - 2,
        outline=(0, 0, 0, 60 if light_theme else 175),
        width=2,
    )
    canvas.paste(Image.alpha_composite(canvas, bevel), (0, 0), outer_mask)

    # 3. Утопленная центральная ниша с широкими боковыми полями под винты
    side_ear_w = 34
    top_bot_h = 16
    bay_x1, bay_y1 = x1 + side_ear_w, y1 + top_bot_h
    bay_x2, bay_y2 = x2 - side_ear_w, y2 - top_bot_h
    bay_r = 24

    # Тёмная окантовка выреза ниши + светлая нижняя фаска
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle(
        [bay_x1 - 3, bay_y1 - 2, bay_x2 + 3, bay_y2 + 4],
        radius=bay_r + 3,
        outline=(255, 255, 255, 170 if light_theme else 52),
        width=2,
    )
    draw.rounded_rectangle(
        [bay_x1 - 2, bay_y1 - 2, bay_x2 + 2, bay_y2 + 2],
        radius=bay_r + 2,
        outline=(115, 122, 128, 220) if light_theme else (8, 10, 13, 245),
        width=3,
    )

    # Вырезаем внутренность ниши прозрачной, чтобы внутри заливался цвет раздела
    cut_mask = Image.new("L", (W, H), 255)
    ImageDraw.Draw(cut_mask).rounded_rectangle([bay_x1, bay_y1, bay_x2, bay_y2], radius=bay_r, fill=0)
    r_ch, g_ch, b_ch, a_ch = canvas.split()
    a_ch = ImageChops.multiply(a_ch, cut_mask)
    canvas = Image.merge("RGBA", (r_ch, g_ch, b_ch, a_ch))

    # Мягкая внутренняя тень по периметру ниши поверх цветной заливки
    inner_sh = Image.new("RGBA", (W, H), (0, 0, 0, 95 if light_theme else 185))
    ImageDraw.Draw(inner_sh).rounded_rectangle(
        [bay_x1 + 4, bay_y1 + 7, bay_x2 - 3, bay_y2 - 2],
        radius=bay_r,
        fill=(0, 0, 0, 0),
    )
    inner_sh = inner_sh.filter(ImageFilter.GaussianBlur(radius=6))

    bay_only_mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(bay_only_mask).rounded_rectangle([bay_x1, bay_y1, bay_x2, bay_y2], radius=bay_r, fill=255)
    sh_clipped = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sh_clipped.paste(inner_sh, (0, 0), bay_only_mask)
    canvas = Image.alpha_composite(canvas, sh_clipped)

    # 4. Четыре аппаратных винта под крест на широких боковых планках
    draw = ImageDraw.Draw(canvas)
    screw_x_offset = x1 + side_ear_w // 2 + 1
    screw_y_offset = y1 + 28
    screw_positions = [
        (screw_x_offset, screw_y_offset),
        (W - screw_x_offset, screw_y_offset),
        (screw_x_offset, H - screw_y_offset),
        (W - screw_x_offset, H - screw_y_offset),
    ]
    for sx, sy in screw_positions:
        _draw_phillips_screw(draw, sx, sy, screw_r=8, light_theme=light_theme)

    meta = {
        "bay_box_norm": [
            round(bay_x1 / W, 4),
            round(1.0 - bay_y2 / H, 4),
            round((bay_x2 - bay_x1) / W, 4),
            round((bay_y2 - bay_y1) / H, 4),
        ],
        "bay_radius_norm": round(bay_r / H, 4),
    }
    return canvas, meta


def save_home_assets():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    frame_dark, frame_meta = generate_home_rack_frame_png(light_theme=False)
    frame_light, _ = generate_home_rack_frame_png(light_theme=True)

    def to_b64(img):
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("utf-8")

    out_path = os.path.join(OUTPUT_DIR, "home_assets.py")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write('"""HD-текстуры студийных рэковых рамок с винтами для главного экрана."""\n\n')
        f.write(f"FRAME_SIZE = {frame_dark.size}\n")
        f.write(f"FRAME_META = {repr(frame_meta)}\n\n")
        f.write(f'FRAME_DARK_B64 = "{to_b64(frame_dark)}"\n')
        f.write(f'FRAME_LIGHT_B64 = "{to_b64(frame_light)}"\n')

    init_path = os.path.join(OUTPUT_DIR, "__init__.py")
    with open(init_path, "w", encoding="utf-8") as f:
        f.write("from . import home_assets\n")

    print(f"[OK] Сгенерированы рэковые рамки с винтами для главного экрана: {out_path}")


if __name__ == "__main__":
    save_home_assets()
