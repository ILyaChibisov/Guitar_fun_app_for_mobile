# settings_utils/flag_generator.py
import base64
import io
import math
import os
from PIL import Image, ImageDraw, ImageFilter

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "settings")


def _draw_star(draw, cx, cy, r_outer, r_inner, angle_deg=-90, fill=(255, 255, 255, 255)):
    """Рисует пятиконечную звезду с заданным поворотом."""
    pts = []
    for i in range(10):
        r = r_outer if i % 2 == 0 else r_inner
        ang = math.radians(angle_deg + i * 36)
        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    draw.polygon(pts, fill=fill)


def _draw_uk_flat(w, h):
    """Флаг Великобритании (Union Jack)."""
    img = Image.new("RGBA", (w, h), (1, 33, 105, 255))
    draw = ImageDraw.Draw(img)

    w_diag = int(h * 0.20)
    draw.line([(0, 0), (w, h)], fill=(255, 255, 255, 255), width=w_diag)
    draw.line([(0, h), (w, 0)], fill=(255, 255, 255, 255), width=w_diag)

    r_diag = int(h * 0.08)
    off = int(h * 0.032)
    cx, cy = w // 2, h // 2
    draw.line([(0, -off), (cx, cy - off)], fill=(200, 16, 46, 255), width=r_diag)
    draw.line([(cx, cy + off), (w, h + off)], fill=(200, 16, 46, 255), width=r_diag)
    draw.line([(0, h - off), (cx, cy - off)], fill=(200, 16, 46, 255), width=r_diag)
    draw.line([(cx, cy + off), (w, off)], fill=(200, 16, 46, 255), width=r_diag)

    w_cross = int(h * 0.30)
    draw.rectangle([0, cy - w_cross // 2, w, cy + w_cross // 2], fill=(255, 255, 255, 255))
    draw.rectangle([cx - w_cross // 2, 0, cx + w_cross // 2, h], fill=(255, 255, 255, 255))

    r_cross = int(h * 0.18)
    draw.rectangle([0, cy - r_cross // 2, w, cy + r_cross // 2], fill=(200, 16, 46, 255))
    draw.rectangle([cx - r_cross // 2, 0, cx + r_cross // 2, h], fill=(200, 16, 46, 255))
    return img


def _draw_portugal_emblem(draw, cx, cy, r):
    draw.ellipse(
        [cx - r, cy - r, cx + r, cy + r],
        fill=(255, 204, 0, 255),
        outline=(180, 130, 0, 255),
        width=max(2, int(r * 0.12)),
    )
    sw, sh = int(r * 0.68), int(r * 0.78)
    draw.rounded_rectangle(
        [cx - sw, cy - sh, cx + sw, cy + sh],
        radius=max(3, int(r * 0.2)),
        fill=(218, 41, 28, 255),
        outline=(255, 220, 80, 255),
        width=max(2, int(r * 0.1)),
    )
    iw, ih = int(r * 0.40), int(r * 0.48)
    draw.rounded_rectangle(
        [cx - iw, cy - ih, cx + iw, cy + ih],
        radius=max(2, int(r * 0.12)),
        fill=(255, 255, 255, 255),
    )


def _draw_spain_emblem(draw, cx, cy, r):
    col_off = int(r * 0.95)
    col_w = max(3, int(r * 0.22))
    draw.rectangle([cx - col_off - col_w, cy - r, cx - col_off + col_w, cy + r], fill=(210, 215, 220, 255))
    draw.rectangle([cx + col_off - col_w, cy - r, cx + col_off + col_w, cy + r], fill=(210, 215, 220, 255))
    sw, sh = int(r * 0.62), int(r * 0.75)
    draw.rounded_rectangle(
        [cx - sw, cy - sh, cx + sw, cy + sh],
        radius=max(3, int(r * 0.2)),
        fill=(198, 11, 30, 255),
        outline=(255, 196, 0, 255),
        width=max(2, int(r * 0.12)),
    )
    draw.ellipse([cx - int(sw * 0.7), cy - sh - int(r * 0.35), cx + int(sw * 0.7), cy - sh], fill=(255, 196, 0, 255))


def _draw_kazakhstan_flat(w, h):
    """Флаг Казахстана: бирюзово-голубой фон, золотое солнце с лучами, парящий орёл и орнамент слева."""
    sky = (0, 175, 202, 255)
    gold = (254, 197, 12, 255)
    img = Image.new("RGBA", (w, h), sky)
    draw = ImageDraw.Draw(img)

    # Вертикальный орнамент у древка (слева)
    orn_x = int(w * 0.08)
    orn_w = max(4, int(w * 0.024))
    step = int(h * 0.11)
    for y in range(int(h * 0.08), int(h * 0.92), step):
        draw.polygon(
            [(orn_x, y - step // 3), (orn_x + orn_w, y), (orn_x, y + step // 3), (orn_x - orn_w, y)],
            fill=gold,
        )

    # Золотое солнце по центру
    cx, cy = int(w * 0.52), int(h * 0.45)
    sun_r = int(h * 0.15)
    for i in range(32):
        ang = math.radians(i * (360.0 / 32.0))
        x1 = cx + (sun_r + 2) * math.cos(ang)
        y1 = cy + (sun_r + 2) * math.sin(ang)
        x2 = cx + int(sun_r * 1.48) * math.cos(ang)
        y2 = cy + int(sun_r * 1.48) * math.sin(ang)
        draw.line([(x1, y1), (x2, y2)], fill=gold, width=max(2, int(h * 0.012)))
    draw.ellipse([cx - sun_r, cy - sun_r, cx + sun_r, cy + sun_r], fill=gold)

    # Стилизованный парящий беркут под солнцем
    ey = cy + int(h * 0.24)
    wing_span = int(w * 0.20)
    wing_h = int(h * 0.07)
    draw.pieslice([cx - wing_span, ey - wing_h, cx + wing_span, ey + wing_h], start=15, end=165, fill=gold)
    draw.polygon([(cx - int(w * 0.03), ey), (cx + int(w * 0.03), ey), (cx, ey + int(h * 0.08))], fill=gold)
    return img


def _draw_korea_flat(w, h):
    """Флаг Южной Кореи (Тхэгыкки)."""
    img = Image.new("RGBA", (w, h), (255, 255, 255, 255))
    draw = ImageDraw.Draw(img)
    cx, cy = w // 2, h // 2
    r = int(h * 0.25)

    # Круг Инь-Ян (красный верх, синий низ)
    draw.pieslice([cx - r, cy - r, cx + r, cy + r], start=180, end=360, fill=(205, 46, 58, 255))
    draw.pieslice([cx - r, cy - r, cx + r, cy + r], start=0, end=180, fill=(0, 71, 160, 255))
    r2 = r // 2
    draw.ellipse([cx - r, cy - r2, cx, cy + r2], fill=(205, 46, 58, 255))
    draw.ellipse([cx, cy - r2, cx + r, cy + r2], fill=(0, 71, 160, 255))

    # 4 угловые триграммы (чёрные полоски)
    bar_w = max(3, int(h * 0.026))
    bar_len = int(h * 0.16)
    offsets = [(-1, -1), (1, -1), (-1, 1), (1, 1)]
    for sx, sy in offsets:
        bx = cx + sx * int(r * 1.48)
        by = cy + sy * int(r * 1.25)
        ang = math.atan2(sy, sx) + math.pi / 2
        dx = math.cos(ang) * (bar_len / 2)
        dy = math.sin(ang) * (bar_len / 2)
        nx = math.cos(ang - math.pi / 2)
        ny = math.sin(ang - math.pi / 2)
        for k in (-1, 0, 1):
            px = bx + nx * k * (bar_w * 1.7)
            py = by + ny * k * (bar_w * 1.7)
            draw.line([(px - dx, py - dy), (px + dx, py + dy)], fill=(20, 20, 20, 255), width=bar_w)
    return img


def _draw_india_flat(w, h):
    """Флаг Индии: шафрановый, белый, зелёный и синяя чакра по центру."""
    img = Image.new("RGBA", (w, h), (255, 255, 255, 255))
    draw = ImageDraw.Draw(img)
    h3 = h // 3
    draw.rectangle([0, 0, w, h3], fill=(255, 153, 51, 255))
    draw.rectangle([0, h3, w, h3 * 2], fill=(255, 255, 255, 255))
    draw.rectangle([0, h3 * 2, w, h], fill=(19, 136, 8, 255))

    cx, cy = w // 2, h // 2
    r = int(h3 * 0.42)
    navy = (0, 0, 128, 255)
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=navy, width=max(2, int(r * 0.14)))
    for i in range(12):
        ang = math.radians(i * 30)
        draw.line(
            [(cx - r * math.cos(ang), cy - r * math.sin(ang)), (cx + r * math.cos(ang), cy + r * math.sin(ang))],
            fill=navy,
            width=max(1, int(r * 0.08)),
        )
    return img


def _create_flat_flag(lang_code, w, h):
    """Создаёт плоское полотнище высокого разрешения для заданного языка."""
    img = Image.new("RGBA", (w, h), (255, 255, 255, 255))
    draw = ImageDraw.Draw(img)

    if lang_code == "ru":
        h3 = h // 3
        draw.rectangle([0, 0, w, h3], fill=(244, 245, 247, 255))
        draw.rectangle([0, h3, w, h3 * 2], fill=(0, 57, 166, 255))
        draw.rectangle([0, h3 * 2, w, h], fill=(213, 43, 30, 255))

    elif lang_code == "en":
        img = _draw_uk_flat(w, h)

    elif lang_code == "fr":
        w3 = w // 3
        draw.rectangle([0, 0, w3, h], fill=(0, 38, 84, 255))
        draw.rectangle([w3, 0, w3 * 2, h], fill=(244, 245, 247, 255))
        draw.rectangle([w3 * 2, 0, w, h], fill=(237, 41, 57, 255))

    elif lang_code == "it":
        w3 = w // 3
        draw.rectangle([0, 0, w3, h], fill=(0, 146, 70, 255))
        draw.rectangle([w3, 0, w3 * 2, h], fill=(244, 245, 247, 255))
        draw.rectangle([w3 * 2, 0, w, h], fill=(206, 43, 55, 255))

    elif lang_code == "es":
        q = h // 4
        draw.rectangle([0, 0, w, q], fill=(170, 21, 27, 255))
        draw.rectangle([0, q, w, h - q], fill=(241, 191, 0, 255))
        draw.rectangle([0, h - q, w, h], fill=(170, 21, 27, 255))
        _draw_spain_emblem(draw, int(w * 0.34), h // 2, int(h * 0.16))

    elif lang_code == "pt":
        split_x = int(w * 0.40)
        draw.rectangle([0, 0, split_x, h], fill=(0, 102, 0, 255))
        draw.rectangle([split_x, 0, w, h], fill=(255, 0, 0, 255))
        _draw_portugal_emblem(draw, split_x, h // 2, int(h * 0.21))

    elif lang_code == "de":
        # Германия: чёрный, красный, золотой
        h3 = h // 3
        draw.rectangle([0, 0, w, h3], fill=(20, 20, 20, 255))
        draw.rectangle([0, h3, w, h3 * 2], fill=(221, 0, 0, 255))
        draw.rectangle([0, h3 * 2, w, h], fill=(255, 206, 0, 255))

    elif lang_code == "pl":
        # Польша: белый верх, красный низ
        h2 = h // 2
        draw.rectangle([0, 0, w, h2], fill=(244, 245, 247, 255))
        draw.rectangle([0, h2, w, h], fill=(220, 20, 60, 255))

    elif lang_code == "hu":
        # Венгрия: красный, белый, зелёный
        h3 = h // 3
        draw.rectangle([0, 0, w, h3], fill=(206, 41, 57, 255))
        draw.rectangle([0, h3, w, h3 * 2], fill=(244, 245, 247, 255))
        draw.rectangle([0, h3 * 2, w, h], fill=(71, 112, 80, 255))

    elif lang_code == "uk":
        # Украина: синий верх, жёлтый низ
        h2 = h // 2
        draw.rectangle([0, 0, w, h2], fill=(0, 87, 183, 255))
        draw.rectangle([0, h2, w, h], fill=(255, 215, 0, 255))

    elif lang_code == "kk":
        img = _draw_kazakhstan_flat(w, h)

    elif lang_code == "tr":
        # Турция: красный фон + белый полумесяц и звезда
        red = (227, 10, 23, 255)
        white = (255, 255, 255, 255)
        draw.rectangle([0, 0, w, h], fill=red)
        cx, cy = int(w * 0.38), h // 2
        r_out = int(h * 0.25)
        r_in = int(h * 0.20)
        draw.ellipse([cx - r_out, cy - r_out, cx + r_out, cy + r_out], fill=white)
        off_x = int(h * 0.065)
        draw.ellipse([cx + off_x - r_in, cy - r_in, cx + off_x + r_in, cy + r_in], fill=red)
        _draw_star(draw, cx + int(h * 0.27), cy, int(h * 0.125), int(h * 0.048), angle_deg=-18, fill=white)

    elif lang_code == "ar":
        # Саудовская Аравия / Арабский: насыщенный зелёный + белая каллиграфия и меч
        green = (0, 108, 53, 255)
        white = (255, 255, 255, 255)
        draw.rectangle([0, 0, w, h], fill=green)
        # Стилизованная арабская вязь
        tx1, tx2 = int(w * 0.24), int(w * 0.76)
        ty = int(h * 0.40)
        stroke = max(3, int(h * 0.032))
        draw.line([(tx1, ty), (tx2, ty)], fill=white, width=stroke)
        for i in range(6):
            vx = tx1 + int((tx2 - tx1) * (i + 0.5) / 6.0)
            vh = int(h * (0.14 if i % 2 == 0 else 0.09))
            draw.line([(vx, ty - vh), (vx, ty)], fill=white, width=stroke)
        # Горизонтальный меч снизу
        sy = int(h * 0.64)
        draw.line([(int(w * 0.28), sy), (int(w * 0.72), sy)], fill=white, width=max(2, int(h * 0.025)))
        draw.line([(int(w * 0.67), sy - int(h * 0.05)), (int(w * 0.67), sy + int(h * 0.05))], fill=white, width=max(2, int(h * 0.022)))

    elif lang_code == "hi":
        img = _draw_india_flat(w, h)

    elif lang_code == "zh":
        # Китай: красный фон + большая золотая звезда и 4 малых по дуге
        red = (222, 41, 16, 255)
        gold = (255, 222, 0, 255)
        draw.rectangle([0, 0, w, h], fill=red)
        bx, by = int(w * 0.18), int(h * 0.28)
        _draw_star(draw, bx, by, int(h * 0.14), int(h * 0.055), angle_deg=-90, fill=gold)
        small_stars = [
            (0.33, 0.13, -65),
            (0.39, 0.24, -40),
            (0.39, 0.38, -90),
            (0.33, 0.49, -65),
        ]
        for sx, sy, ang in small_stars:
            _draw_star(draw, int(w * sx), int(h * sy), int(h * 0.048), int(h * 0.019), angle_deg=ang, fill=gold)

    elif lang_code == "ja":
        # Япония: белый фон + красный солнечный диск по центру
        draw.rectangle([0, 0, w, h], fill=(255, 255, 255, 255))
        cx, cy = w // 2, h // 2
        r = int(h * 0.28)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(188, 0, 45, 255))

    elif lang_code == "ko":
        img = _draw_korea_flat(w, h)

    return img


def generate_waving_flag_png(lang_code, out_w=240, out_h=160):
    """Генерирует развевающийся 3D-флаг в 2x суперсэмплинге с мягкой тенью."""
    SS = 2
    W, H = out_w * SS, out_h * SS
    pad_x = int(16 * SS)
    pad_y = int(22 * SS)
    flag_w = W - pad_x * 2
    flag_h = H - pad_y * 2

    flat = _create_flat_flag(lang_code, flag_w, flag_h)
    flat_px = flat.load()

    waved = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    waved_px = waved.load()

    amp = 11.5 * SS

    def wave_offset(t):
        return -amp * math.sin(2.0 * math.pi * t) + (2.5 * SS) * math.sin(4.0 * math.pi * t)

    def lighting_factor(t):
        left_edge = 0.62 + 0.38 * min(1.0, t / 0.10)
        right_edge = 0.68 + 0.32 * min(1.0, (1.0 - t) / 0.08)
        crest1 = 0.14 * math.exp(-((t - 0.21) / 0.09) ** 2)
        valley = -0.24 * math.exp(-((t - 0.50) / 0.10) ** 2)
        crest2 = 0.12 * math.exp(-((t - 0.78) / 0.10) ** 2)
        return left_edge * right_edge + crest1 + valley + crest2

    for x in range(flag_w):
        t = x / max(1, flag_w - 1)
        dy = wave_offset(t)
        light = lighting_factor(t)
        dst_x = pad_x + x
        for y in range(flag_h):
            r, g, b, a = flat_px[x, y]
            if light >= 1.0:
                boost = (light - 1.0) * 255.0
                r = min(255, int(r * light + boost * 0.22))
                g = min(255, int(g * light + boost * 0.22))
                b = min(255, int(b * light + boost * 0.22))
            else:
                r = max(0, int(r * light))
                g = max(0, int(g * light))
                b = max(0, int(b * light))

            exact_y = pad_y + y + dy
            y0 = int(math.floor(exact_y))
            frac = exact_y - y0

            if 0 <= y0 < H:
                old = waved_px[dst_x, y0]
                w0 = 1.0 - frac
                waved_px[dst_x, y0] = (
                    int(old[0] * (1 - w0) + r * w0),
                    int(old[1] * (1 - w0) + g * w0),
                    int(old[2] * (1 - w0) + b * w0),
                    min(255, int(old[3] + a * w0)),
                )
            if 0 <= y0 + 1 < H and frac > 0:
                old1 = waved_px[dst_x, y0 + 1]
                w1 = frac
                waved_px[dst_x, y0 + 1] = (
                    int(old1[0] * (1 - w1) + r * w1),
                    int(old1[1] * (1 - w1) + g * w1),
                    int(old1[2] * (1 - w1) + b * w1),
                    min(255, int(old1[3] + a * w1)),
                )

    alpha_mask = waved.split()[3]
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    shadow_fill = Image.new("RGBA", (W, H), (0, 0, 0, 130))
    shadow.paste(shadow_fill, (int(3 * SS), int(5 * SS)), alpha_mask)
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=5 * SS))

    result = Image.alpha_composite(shadow, waved)
    return result.resize((out_w, out_h), Image.Resampling.LANCZOS)


def save_flag_assets():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    lang_codes = [
        "ru", "en", "es", "pt", "de", "fr",
        "it", "pl", "hu", "uk", "kk", "tr",
    ]

    flags_b64 = {}
    for code in lang_codes:
        img = generate_waving_flag_png(code, out_w=240, out_h=160)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        flags_b64[code] = base64.b64encode(buf.getvalue()).decode("utf-8")

    out_path = os.path.join(OUTPUT_DIR, "flag_assets.py")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write('"""Автоматически сгенерированные развевающиеся 3D-флаги языков."""\n\n')
        f.write("FLAG_SIZE = (240, 160)\n")
        f.write("FLAGS_PNG_BASE64 = {\n")
        for code, b64 in flags_b64.items():
            f.write(f'    "{code}": "{b64}",\n')
        f.write("}\n")

    init_path = os.path.join(OUTPUT_DIR, "__init__.py")
    with open(init_path, "w", encoding="utf-8") as f:
        f.write("from . import flag_assets\n")

    print(f"[OK] Сгенерированы 3D-флаги ({len(flags_b64)} шт.): {out_path}")


if __name__ == "__main__":
    save_flag_assets()