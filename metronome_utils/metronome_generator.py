# metronome_utils/metronome_generator.py
import base64
import io
import math
import os
import random
from PIL import Image, ImageDraw, ImageFilter

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "metronome")


def _rounded_trapezoid(cx, y_top, y_bot, w_top, w_bot, radius, steps=14):
    """Строит полигон трапеции со скруглёнными углами."""
    half_wt = w_top * 0.5
    half_wb = w_bot * 0.5

    corners = [
        (cx - half_wt, y_top, math.pi, 1.5 * math.pi),        # верхний левый
        (cx + half_wt, y_top, 1.5 * math.pi, 2.0 * math.pi),  # верхний правый
        (cx + half_wb, y_bot, 0.0, 0.5 * math.pi),            # нижний правый
        (cx - half_wb, y_bot, 0.5 * math.pi, math.pi),        # нижний левый
    ]

    pts = []
    for ox, oy, a_start, a_end in corners:
        dx = 1 if ox < cx else -1
        dy = 1 if oy < (y_top + y_bot) * 0.5 else -1
        acx = ox + dx * radius
        acy = oy + dy * radius
        for i in range(steps + 1):
            t = i / steps
            ang = a_start + t * (a_end - a_start)
            pts.append((acx + math.cos(ang) * radius, acy + math.sin(ang) * radius))
    return pts


def _apply_matte_grain(img, strength=7, seed=42):
    """Добавляет лёгкую микротекстуру матового софт-тач пластика/металла."""
    rng = random.Random(seed)
    w, h = img.size
    noise = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = noise.load()
    for y in range(0, h, 2):
        for x in range(0, w, 2):
            v = rng.randint(-strength, strength)
            a = abs(v) * 2
            c = 255 if v > 0 else 0
            px[x, y] = (c, c, c, a)
            if x + 1 < w:
                px[x + 1, y] = (c, c, c, a)
            if y + 1 < h:
                px[x, y + 1] = (c, c, c, a)
            if x + 1 < w and y + 1 < h:
                px[x + 1, y + 1] = (c, c, c, a)
    img.alpha_composite(noise)


def generate_graphite_metronome():
    W, H = 560, 820
    cx = W // 2
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    # Геометрия корпуса
    top_y = 36
    split_y = 548
    bot_y = 758

    w_top = 152
    w_split = 342
    w_bot = 398

    outer_poly = _rounded_trapezoid(cx, top_y, bot_y, w_top, w_bot, radius=32)

    # 1. Мягкая внешняя тень корпуса
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow)
    s_draw.polygon([(x, y + 14) for x, y in outer_poly], fill=(0, 0, 0, 175))
    canvas.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(radius=16)))

    # 2. Резиновые ножки снизу
    draw = ImageDraw.Draw(canvas)
    foot_y1 = bot_y - 6
    foot_y2 = bot_y + 16
    for fx in (cx - 122, cx + 122):
        draw.rounded_rectangle([fx - 26, foot_y1, fx + 26, foot_y2], radius=8, fill=(22, 24, 27, 255))
        draw.line([(fx - 20, foot_y2 - 2), (fx + 20, foot_y2 - 2)], fill=(45, 48, 54, 180), width=2)

    # 3. Основной матовый графитовый корпус с объёмным боковым освещением
    body_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    b_draw = ImageDraw.Draw(body_layer)
    for y in range(top_y, bot_y + 1):
        t = (y - top_y) / max(1, (bot_y - top_y))
        base = int(46 - 11 * t)
        b_draw.line([(0, y), (W, y)], fill=(base, base + 2, base + 5, 255))

    # Объёмная подсветка по краям и лёгкая тень справа
    rim_shade = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    r_draw = ImageDraw.Draw(rim_shade)
    for x in range(W):
        nx = (x - cx) / (w_bot * 0.5)
        if nx < -0.55:
            a = int(34 * min(1.0, (-nx - 0.55) / 0.45))
            r_draw.line([(x, 0), (x, H)], fill=(210, 220, 235, a))
        elif nx > 0.45:
            a = int(42 * min(1.0, (nx - 0.45) / 0.55))
            r_draw.line([(x, 0), (x, H)], fill=(8, 10, 12, a))
    body_layer.alpha_composite(rim_shade)

    # Нижняя база чуть темнее верхней
    base_tint = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(base_tint).rectangle([0, split_y, W, H], fill=(12, 13, 16, 48))
    body_layer.alpha_composite(base_tint)

    _apply_matte_grain(body_layer, strength=5, seed=77)

    body_mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(body_mask).polygon(outer_poly, fill=255)
    canvas.paste(body_layer, (0, 0), body_mask)

    # 4. Внешний светлый блик-фаска по контуру корпуса
    bevel = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bv_draw = ImageDraw.Draw(bevel)
    bv_draw.polygon(outer_poly, outline=(120, 126, 136, 140), width=3)
    bv_draw.polygon(
        _rounded_trapezoid(cx, top_y + 3, bot_y - 3, w_top - 6, w_bot - 6, radius=29),
        outline=(78, 83, 92, 110),
        width=2,
    )
    canvas.paste(Image.alpha_composite(canvas, bevel), (0, 0), body_mask)

    # 5. Глубокая ниша под шкалу и маятник
    recess_top = top_y + 34
    recess_bot = split_y - 6
    recess_wt = 74
    recess_wb = 248
    recess_poly = _rounded_trapezoid(cx, recess_top, recess_bot, recess_wt, recess_wb, radius=18)

    # Светлая скошенная кромка вокруг ниши
    frame_poly = _rounded_trapezoid(cx, recess_top - 5, recess_bot + 2, recess_wt + 10, recess_wb + 10, radius=21)
    draw = ImageDraw.Draw(canvas)
    draw.polygon(frame_poly, fill=(64, 68, 75, 255), outline=(92, 98, 108, 180), width=2)

    # Тёмная внутренняя стенка ниши
    recess_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rc_draw = ImageDraw.Draw(recess_layer)
    for y in range(recess_top, recess_bot + 1):
        t = (y - recess_top) / max(1, (recess_bot - recess_top))
        v = int(20 + 8 * t)
        rc_draw.line([(0, y), (W, y)], fill=(v, v + 1, v + 3, 255))

    # Глубокая внутренняя тень от бортиков ниши
    inner_shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    is_draw = ImageDraw.Draw(inner_shadow)
    is_draw.polygon(frame_poly, fill=(0, 0, 0, 220))
    is_draw.polygon(
        _rounded_trapezoid(cx + 3, recess_top + 10, recess_bot - 4, recess_wt - 14, recess_wb - 18, radius=14),
        fill=(0, 0, 0, 0),
    )
    recess_layer.alpha_composite(inner_shadow.filter(ImageFilter.GaussianBlur(radius=9)))

    recess_mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(recess_mask).polygon(recess_poly, fill=255)
    canvas.paste(recess_layer, (0, 0), recess_mask)

    # 6. Горизонтальный стык между верхней и нижней частью корпуса
    half_w_split = w_top * 0.5 + (w_bot - w_top) * 0.5 * ((split_y - top_y) / (bot_y - top_y))
    x1_sp = int(cx - half_w_split + 4)
    x2_sp = int(cx + half_w_split - 4)
    draw.line([(x1_sp, split_y), (x2_sp, split_y)], fill=(12, 13, 15, 240), width=3)
    draw.line([(x1_sp, split_y + 3), (x2_sp, split_y + 3)], fill=(86, 91, 100, 150), width=2)

    # Нормализованные координаты для живой анимации в Kivy (Y: 0 снизу, 1 сверху)
    pivot_x_px = cx
    pivot_y_px = recess_bot - 26
    scale_top_px = recess_top + 52
    scale_bot_px = pivot_y_px - 34
    rod_len_px = pivot_y_px - (recess_top + 28)

    meta = {
        "pivot": [round(pivot_x_px / W, 4), round(1.0 - pivot_y_px / H, 4)],
        "scale_y_range": [
            round(1.0 - scale_bot_px / H, 4),
            round(1.0 - scale_top_px / H, 4),
        ],
        "rod_length_norm": round(rod_len_px / H, 4),
    }

    return canvas, meta


def save_asset():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    init_path = os.path.join(OUTPUT_DIR, "__init__.py")
    with open(init_path, "w", encoding="utf-8") as f:
        f.write("from . import classic_graphite\n")

    canvas, meta = generate_graphite_metronome()
    buf = io.BytesIO()
    canvas.save(buf, format="PNG")
    b64_str = base64.b64encode(buf.getvalue()).decode("utf-8")

    out_path = os.path.join(OUTPUT_DIR, "classic_graphite.py")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write('"""Автоматически сгенерированный ассет корпуса метронома."""\n\n')
        f.write(f"IMAGE_SIZE = {canvas.size}\n")
        f.write(f"META_DATA = {repr(meta)}\n")
        f.write(f'PNG_BASE64 = "{b64_str}"\n')
    print(f"[OK] Сгенерирован модуль: {out_path}")


if __name__ == "__main__":
    save_asset()
