import base64
import io
import math
import os
import random
from PIL import Image, ImageDraw, ImageFilter

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "grifs")


def _create_wood_texture(width, height, base_rgb, grain_rgb, highlight_rgb=None, seed=42, vignette=True):
    rng = random.Random(seed)
    img = Image.new("RGBA", (width, height), (*base_rgb, 255))
    draw = ImageDraw.Draw(img)

    cx = width * 0.5
    for y in range(height):
        ny = abs((y / max(1, height - 1)) - 0.45)
        v_factor = 1.04 - 0.12 * ny
        r = max(0, min(255, int(base_rgb[0] * v_factor)))
        g = max(0, min(255, int(base_rgb[1] * v_factor)))
        b = max(0, min(255, int(base_rgb[2] * v_factor)))
        draw.line([(0, y), (width, y)], fill=(r, g, b, 255))

    for _ in range(int(width * 2.4)):
        x = rng.randint(0, width - 1)
        alpha = rng.randint(18, 54)
        thickness = rng.choice([1, 1, 2])
        wave_amp = rng.uniform(0.5, 2.0)
        wave_freq = rng.uniform(0.012, 0.03)
        phase = rng.uniform(0, math.pi * 2)

        pts = []
        for y in range(0, height + 6, 6):
            dx = math.sin(y * wave_freq + phase) * wave_amp
            pts.append((x + dx, y))
        if len(pts) > 1:
            draw.line(pts, fill=(*grain_rgb, alpha), width=thickness)

    if highlight_rgb:
        for _ in range(int(width * 0.5)):
            x = rng.randint(0, width - 1)
            alpha = rng.randint(12, 28)
            wave_amp = rng.uniform(0.4, 1.6)
            wave_freq = rng.uniform(0.014, 0.028)
            phase = rng.uniform(0, math.pi * 2)
            pts = [(x + math.sin(y * wave_freq + phase) * wave_amp, y) for y in range(0, height + 8, 8)]
            if len(pts) > 1:
                draw.line(pts, fill=(*highlight_rgb, alpha), width=1)

    blurred = img.filter(ImageFilter.GaussianBlur(radius=0.55))

    if vignette:
        shade = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        s_draw = ImageDraw.Draw(shade)
        max_dx = width * 0.25
        for x in range(width):
            dist = abs(x - cx) / max(1.0, max_dx)
            if dist < 0.45:
                a = int(24 * (1.0 - dist / 0.45))
                s_draw.line([(x, 0), (x, height)], fill=(255, 230, 195, a))
            else:
                a = min(115, int(95 * ((dist - 0.45) / 0.75) ** 1.4))
                s_draw.line([(x, 0), (x, height)], fill=(20, 10, 4, a))
        blurred.alpha_composite(shade)

    solid = Image.new("RGBA", (width, height), (*base_rgb, 255))
    solid.alpha_composite(blurred)
    return solid


def _draw_chrome_peg(canvas, post_x, post_y, edge_x, is_left, scale=1.0, is_bass=False):
    """Рисует колок так, чтобы ось лопасти выходила строго от кромки дерева (edge_x), а втулка стояла на post_x."""
    draw = ImageDraw.Draw(canvas)
    direction = -1 if is_left else 1

    c_dark = (34, 37, 42)
    c_mid = (142, 148, 158)
    c_light = (248, 250, 255)

    # Ось начинается чуть внутри торца (на 2px) и уходит наружу от кромки дерева
    shaft_start_x = edge_x - direction * 2
    shaft_len = int((22 if is_bass else 23) * scale)
    btn_w = int((18 if is_bass else 20) * scale)
    btn_h = int((23 if is_bass else 26) * scale)

    bx_center = edge_x + direction * (shaft_len + btn_w - 4)
    bx1, bx2 = bx_center - btn_w, bx_center + btn_w
    by1, by2 = post_y - btn_h, post_y + btn_h

    # Мягкая тень под лопастью и осью
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow)
    s_draw.rounded_rectangle([bx1, by1 + 6, bx2, by2 + 6], radius=int(13 * scale), fill=(0, 0, 0, 130))
    canvas.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(radius=4.5)))

    # Ось строго от кромки грифа до лопасти
    sh_x1 = min(shaft_start_x, bx_center)
    sh_x2 = max(shaft_start_x, bx_center)
    sh_h = int(5.5 * scale)
    draw.rectangle([sh_x1, post_y - sh_h, sh_x2, post_y + sh_h], fill=c_dark)
    draw.rectangle([sh_x1, post_y - int(3 * scale), sh_x2, post_y + int(1 * scale)], fill=c_light)

    # Небольшое металлическое кольцо-упор у самого торца дерева
    collar_x = edge_x + direction * 2
    draw.rectangle(
        [min(edge_x, collar_x), post_y - sh_h - 2, max(edge_x, collar_x), post_y + sh_h + 2],
        fill=c_mid,
        outline=c_dark,
    )

    # Лопасть колка с бликами
    for y in range(by1, by2 + 1):
        t = (y - by1) / max(1, (by2 - by1))
        if t < 0.28:
            ratio = t / 0.28
            col = tuple(int(c_mid[i] + (c_light[i] - c_mid[i]) * ratio) for i in range(3))
        elif t < 0.72:
            ratio = (t - 0.28) / 0.44
            col = tuple(int(c_light[i] + (c_dark[i] - c_light[i]) * ratio) for i in range(3))
        else:
            ratio = (t - 0.72) / 0.28
            col = tuple(int(c_dark[i] + (c_mid[i] - c_dark[i]) * ratio) for i in range(3))

        norm_y = abs((t - 0.5) * 2.0)
        inset = int((btn_w * 0.34) * (norm_y ** 2.6))
        draw.line([(bx1 + inset, y), (bx2 - inset, y)], fill=(*col, 255))

    draw.rounded_rectangle([bx1, by1, bx2, by2], radius=int(13 * scale), outline=(28, 30, 35, 220), width=1)

    # Лицевая втулка (гайка) и штырь на лицевой стороне головы грифа
    r_outer = int(14 * scale)
    r_inner = int(7 * scale)
    draw.ellipse([post_x - r_outer - 1, post_y - r_outer + 2, post_x + r_outer + 1, post_y + r_outer + 4], fill=(0, 0, 0, 120))
    draw.ellipse([post_x - r_outer, post_y - r_outer, post_x + r_outer, post_y + r_outer], fill=c_mid, outline=c_dark, width=2)
    draw.ellipse([post_x - r_outer + 3, post_y - r_outer + 3, post_x + r_outer - 3, post_y + r_outer - 3], outline=c_light, width=1)
    draw.ellipse([post_x - r_inner, post_y - r_inner, post_x + r_inner, post_y + r_inner], fill=c_dark)
    draw.ellipse([post_x - r_inner + 2, post_y - r_inner + 1, post_x + r_inner - 3, post_y + r_inner - 4], fill=c_light)


def _draw_ukulele_pearl_peg(canvas, post_x, post_y, edge_x, is_left, scale=1.0):
    """Рисует колок укулеле как на 1-м и 2-м скринах: ось от торца дерева + белое овальное перламутровое ушко."""
    draw = ImageDraw.Draw(canvas)
    direction = -1 if is_left else 1

    c_dark = (58, 62, 68)
    c_mid = (182, 188, 196)
    c_light = (250, 252, 255)

    # Короткая металлическая ось от торца грифа (edge_x) наружу (как на 2-м крупном скрине)
    shaft_start = edge_x - direction * 2
    shaft_end = edge_x + direction * int(18 * scale)
    sh_h = int(6.5 * scale)

    sh_x1, sh_x2 = min(shaft_start, shaft_end), max(shaft_start, shaft_end)
    draw.rectangle([sh_x1, post_y - sh_h, sh_x2, post_y + sh_h], fill=c_mid, outline=c_dark, width=1)
    draw.line([(sh_x1, post_y - int(2 * scale)), (sh_x2, post_y - int(2 * scale))], fill=c_light, width=2)

    # Белое овальное ушко (перламутровое)
    rx = int(17 * scale)
    ry = int(23 * scale)
    bx = shaft_end + direction * (rx - 3)
    by = post_y

    # Тень от белого ушка
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow)
    s_draw.ellipse([bx - rx, by - ry + 4, bx + rx, by + ry + 4], fill=(0, 0, 0, 120))
    canvas.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(radius=3.5)))

    # Основной белый овал с лёгким объёмом по нижнему краю
    draw.ellipse([bx - rx, by - ry, bx + rx, by + ry], fill=(246, 246, 244, 255), outline=(145, 148, 154, 230), width=1)
    draw.ellipse([bx - rx + 2, by - ry + 1, bx + rx - 2, by + ry - 3], fill=(255, 255, 255, 255))

    # Лицевая белая втулка с металлическим сердечником (как на 2-м скрине)
    r_outer = int(14 * scale)
    r_inner = int(6 * scale)
    draw.ellipse([post_x - r_outer, post_y - r_outer + 2, post_x + r_outer, post_y + r_outer + 2], fill=(0, 0, 0, 80))
    draw.ellipse(
        [post_x - r_outer, post_y - r_outer, post_x + r_outer, post_y + r_outer],
        fill=(248, 246, 240, 255),
        outline=(165, 155, 140, 230),
        width=2,
    )
    draw.ellipse([post_x - r_inner, post_y - r_inner, post_x + r_inner, post_y + r_inner], fill=(135, 142, 150, 255), outline=c_dark, width=1)
    draw.ellipse([post_x - 2, post_y - 2, post_x + 2, post_y + 2], fill=c_light)


def _draw_clover_peg(canvas, post_x, post_y, edge_x, scale=1.0, angle_deg=-11):
    """Рисует бас-колок в форме трилистника, где шток начинается строго от кромки дерева (edge_x)."""
    c_dark = (42, 46, 52)
    c_mid = (165, 172, 182)
    c_light = (246, 249, 255)

    pad = 120
    peg_img = Image.new("RGBA", (pad * 2, pad * 2), (0, 0, 0, 0))
    p_draw = ImageDraw.Draw(peg_img)

    # Шток начинается в точке (pad, pad), которую мы совместим с edge_x (кромкой грифа)
    shaft_len = int(28 * scale)
    sh_h = int(5 * scale)
    p_draw.rectangle([pad - shaft_len, pad - sh_h, pad + 3, pad + sh_h], fill=c_dark)
    p_draw.rectangle([pad - shaft_len, pad - int(3 * scale), pad + 3, pad], fill=c_light)

    lx = pad - int(40 * scale)
    ly = pad
    r_lobe = int(15 * scale)
    dist = int(13 * scale)

    lobes = [
        (lx, ly - dist),
        (lx, ly + dist),
        (lx - dist, ly),
        (lx + int(6 * scale), ly),
    ]

    sh_img = Image.new("RGBA", (pad * 2, pad * 2), (0, 0, 0, 0))
    sh_draw = ImageDraw.Draw(sh_img)
    for bx, by in lobes:
        sh_draw.ellipse([bx - r_lobe, by - r_lobe + 5, bx + r_lobe, by + r_lobe + 5], fill=(0, 0, 0, 135))
    peg_img.alpha_composite(sh_img.filter(ImageFilter.GaussianBlur(radius=4)))

    for bx, by in lobes:
        p_draw.ellipse([bx - r_lobe - 1, by - r_lobe - 1, bx + r_lobe + 1, by + r_lobe + 1], fill=c_dark)
    for bx, by in lobes:
        p_draw.ellipse([bx - r_lobe + 1, by - r_lobe + 1, bx + r_lobe - 1, by + r_lobe - 1], fill=c_mid)
    for bx, by in lobes[:3]:
        p_draw.ellipse([bx - r_lobe + 4, by - r_lobe + 3, bx + r_lobe - 5, by + r_lobe - 6], fill=c_light)

    rotated = peg_img.rotate(angle_deg, resample=Image.BICUBIC, center=(pad, pad))
    # Совмещаем центр поворота (pad, pad) с кромкой дерева edge_x!
    canvas.alpha_composite(rotated, (int(edge_x - pad), int(post_y - pad)))

    # Лицевая втулка и штырь на лицевой плоскости грифа
    draw = ImageDraw.Draw(canvas)
    r_outer = int(17 * scale)
    r_inner = int(9 * scale)
    draw.ellipse([post_x - r_outer - 1, post_y - r_outer + 2, post_x + r_outer + 1, post_y + r_outer + 5], fill=(0, 0, 0, 120))
    draw.ellipse([post_x - r_outer, post_y - r_outer, post_x + r_outer, post_y + r_outer], fill=c_mid, outline=c_dark, width=2)
    draw.ellipse([post_x - r_outer + 3, post_y - r_outer + 3, post_x + r_outer - 3, post_y + r_outer - 3], outline=c_light, width=1)
    draw.ellipse([post_x - r_inner, post_y - r_inner, post_x + r_inner, post_y + r_inner], fill=c_dark)
    draw.ellipse([post_x - r_inner + 2, post_y - r_inner + 1, post_x + r_inner - 3, post_y + r_inner - 4], fill=c_light)


def _build_classic_headstock_polygon(cx, top_y, shoulder_y, waist_y, nut_y, hw_top, hw_bot, nw):
    pts = []
    crown_steps = 40
    for i in range(crown_steps + 1):
        t = i / crown_steps
        x = cx - hw_top + t * (2 * hw_top)
        center_arch = math.sin(t * math.pi)
        ears = 0.22 * math.sin(t * math.pi * 3.0)
        y = shoulder_y - (shoulder_y - top_y) * (0.68 * center_arch + 0.32 * max(0.0, center_arch + ears))
        pts.append((x, y))

    side_steps = 22
    for i in range(1, side_steps + 1):
        t = i / side_steps
        y = shoulder_y + t * (waist_y - shoulder_y)
        curve = hw_top * (1.0 - t) + hw_bot * t - 6.0 * math.sin(t * math.pi)
        pts.append((cx + curve, y))

    pts.extend([
        (cx + hw_bot - 2, waist_y + 16),
        (cx + nw + 4, nut_y - 14),
        (cx + nw, nut_y),
        (cx - nw, nut_y),
        (cx - nw - 4, nut_y - 14),
        (cx - hw_bot + 2, waist_y + 16),
    ])

    for i in range(side_steps - 1, 0, -1):
        t = i / side_steps
        y = shoulder_y + t * (waist_y - shoulder_y)
        curve = hw_top * (1.0 - t) + hw_bot * t - 6.0 * math.sin(t * math.pi)
        pts.append((cx - curve, y))

    return pts


def _generate_guitar_6_headstock():
    """Генерирует 6-струнную гитару с осями колков от кромки грифа."""
    W, H = 480, 560
    cx = W // 2
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    top_y = 22
    shoulder_y = 66
    waist_y = 358
    nut_y = 418
    fret1_y = 516

    hw_top = 108
    hw_bot = 86
    nw = 72

    head_poly = _build_classic_headstock_polygon(cx, top_y, shoulder_y, waist_y, nut_y, hw_top, hw_bot, nw)

    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow)
    s_draw.polygon([(x, y + 8) for x, y in head_poly], fill=(0, 0, 0, 165))
    s_draw.rectangle([cx - nw, nut_y, cx + nw, H], fill=(0, 0, 0, 165))
    canvas.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(radius=10)))

    fret_tex = _create_wood_texture(W, H, (56, 32, 20), (36, 18, 10), (82, 48, 30), seed=101, vignette=True)
    fret_mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(fret_mask).rectangle([cx - nw, nut_y, cx + nw, H], fill=255)
    canvas.paste(fret_tex, (0, 0), fret_mask)

    head_tex = _create_wood_texture(W, H, (126, 62, 30), (88, 40, 18), (168, 92, 48), seed=202, vignette=True)
    head_mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(head_mask).polygon(head_poly, fill=255)
    canvas.paste(head_tex, (0, 0), head_mask)

    draw = ImageDraw.Draw(canvas)

    draw.polygon(head_poly, outline=(242, 238, 228, 235), width=3)
    inner_poly = [
        (cx + (x - cx) * 0.945, shoulder_y + (y - shoulder_y) * 0.965)
        for x, y in head_poly
    ]
    draw.polygon(inner_poly, outline=(32, 14, 6, 190), width=1)

    draw.line([(cx - nw + 1, nut_y), (cx - nw + 1, H)], fill=(235, 230, 220, 210), width=2)
    draw.line([(cx + nw - 1, nut_y), (cx + nw - 1, H)], fill=(235, 230, 220, 210), width=2)

    bell_pts = [
        (cx, nut_y - 118),
        (cx + 12, nut_y - 96),
        (cx + 22, nut_y - 54),
        (cx + 27, nut_y - 10),
        (cx - 27, nut_y - 10),
        (cx - 22, nut_y - 54),
        (cx - 12, nut_y - 96),
    ]
    draw.polygon(bell_pts, fill=(24, 22, 22, 245), outline=(220, 215, 205, 180))
    draw.ellipse([cx - 2.5, nut_y - 102, cx + 2.5, nut_y - 97], fill=(215, 220, 225, 255))
    draw.ellipse([cx - 2.5, nut_y - 22, cx + 2.5, nut_y - 17], fill=(215, 220, 225, 255))

    wave_y = 92
    wave_bars = [10, 18, 28, 16, 36, 22, 14, 30, 18, 10]
    bar_step = 5
    start_wx = cx - ((len(wave_bars) - 1) * bar_step) // 2
    for idx, bh in enumerate(wave_bars):
        bx = start_wx + idx * bar_step
        draw.line([(bx, wave_y - bh // 2), (bx, wave_y + bh // 2)], fill=(232, 212, 188, 205), width=2)

    draw.rectangle([cx - nw + 2, fret1_y, cx + nw - 2, fret1_y + 4], fill=(195, 190, 180, 255))
    draw.line([(cx - nw + 2, fret1_y + 1), (cx + nw - 2, fret1_y + 1)], fill=(250, 248, 244, 255), width=1)

    draw.rectangle([cx - nw - 1, nut_y - 7, cx + nw + 1, nut_y + 5], fill=(244, 240, 232, 255))
    draw.line([(cx - nw, nut_y - 7), (cx + nw, nut_y - 7)], fill=(255, 255, 255, 255), width=2)
    draw.line([(cx - nw, nut_y + 5), (cx + nw, nut_y + 5)], fill=(28, 14, 8, 235), width=2)

    margin_x = 16
    nut_xs = [
        cx - nw + margin_x + i * ((2 * (nw - margin_x)) / 5.0)
        for i in range(6)
    ]
    left_ys = [308, 216, 124]
    right_ys = [124, 216, 308]

    pegs_meta = []
    for i in range(3):
        py = left_ys[i]
        t = (py - shoulder_y) / max(1, (waist_y - shoulder_y))
        half_w = hw_top + (hw_bot - hw_top) * max(0.0, min(1.0, t)) - 6.0 * math.sin(t * math.pi)
        edge_x = cx - half_w
        post_x = edge_x + 22
        _draw_chrome_peg(canvas, int(post_x), int(py), int(edge_x), is_left=True, scale=1.02)
        pegs_meta.append({
            "string_index": i,
            "side": "left",
            "peg_pos": [round(post_x / W, 4), round(1.0 - py / H, 4)],
            "nut_pos": [round(nut_xs[i] / W, 4), round(1.0 - nut_y / H, 4)],
        })

    for j in range(3):
        s_idx = 3 + j
        py = right_ys[j]
        t = (py - shoulder_y) / max(1, (waist_y - shoulder_y))
        half_w = hw_top + (hw_bot - hw_top) * max(0.0, min(1.0, t)) - 6.0 * math.sin(t * math.pi)
        edge_x = cx + half_w
        post_x = edge_x - 22
        _draw_chrome_peg(canvas, int(post_x), int(py), int(edge_x), is_left=False, scale=1.02)
        pegs_meta.append({
            "string_index": s_idx,
            "side": "right",
            "peg_pos": [round(post_x / W, 4), round(1.0 - py / H, 4)],
            "nut_pos": [round(nut_xs[s_idx] / W, 4), round(1.0 - nut_y / H, 4)],
        })

    return canvas, pegs_meta


def _generate_ukulele_4_headstock():
    """Генерирует укулеле по 1-му и 2-му скринам: трапециевидная форма, тёплая коа и белые овальные колки от края дерева."""
    W, H = 480, 560
    cx = W // 2
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    top_y = 32
    shoulder_y = 54
    waist_y = 368
    nut_y = 422
    fret1_y = 516

    hw_top = 104
    hw_bot = 82
    nw = 68

    # Классический силуэт укулеле: плавная волна сверху и прямые трапециевидные бока (как на 1-м скрине)
    head_poly = []
    crown_steps = 36
    for i in range(crown_steps + 1):
        t = i / crown_steps
        x = cx - hw_top + t * (2 * hw_top)
        # Центральный плавный подъём + лёгкие боковые дуги (как на 1-м скрине)
        wave = math.sin(t * math.pi) ** 1.6
        y = shoulder_y - (shoulder_y - top_y) * wave
        head_poly.append((x, y))

    head_poly.extend([
        (cx + hw_bot, waist_y),
        (cx + nw, nut_y),
        (cx - nw, nut_y),
        (cx - hw_bot, waist_y),
    ])

    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow)
    s_draw.polygon([(x, y + 7) for x, y in head_poly], fill=(0, 0, 0, 145))
    s_draw.rectangle([cx - nw, nut_y, cx + nw, H], fill=(0, 0, 0, 145))
    canvas.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(radius=9)))

    # Накладка грифа из тёплого ореха/палисандра
    fret_tex = _create_wood_texture(W, H, (112, 68, 34), (78, 44, 20), (142, 88, 48), seed=505, vignette=True)
    fret_mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(fret_mask).rectangle([cx - nw, nut_y, cx + nw, H], fill=255)
    canvas.paste(fret_tex, (0, 0), fret_mask)

    # Голова грифа из тёплой гавайской коа (как на 1-м и 2-м скринах)
    head_tex = _create_wood_texture(W, H, (176, 98, 42), (132, 66, 24), (206, 124, 62), seed=606, vignette=True)
    head_mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(head_mask).polygon(head_poly, fill=255)
    canvas.paste(head_tex, (0, 0), head_mask)

    draw = ImageDraw.Draw(canvas)
    draw.polygon(head_poly, outline=(92, 46, 18, 210), width=2)

    # Первый лад и верхний порожек (белый)
    draw.rectangle([cx - nw, fret1_y, cx + nw, fret1_y + 4], fill=(215, 205, 190, 255))
    draw.rectangle([cx - nw - 1, nut_y - 7, cx + nw + 1, nut_y + 5], fill=(248, 248, 246, 255))
    draw.line([(cx - nw, nut_y + 5), (cx + nw, nut_y + 5)], fill=(45, 24, 12, 220), width=2)

    # Координаты 4 струн на порожке (с отступом, чтобы струны шли чисто мимо нижних втулок)
    margin_x = 18
    nut_xs = [
        cx - nw + margin_x + i * ((2 * (nw - margin_x)) / 3.0)
        for i in range(4)
    ]
    left_ys = [292, 152]   # 0: G (нижний левый), 1: C (верхний левый)
    right_ys = [152, 292]  # 2: E (верхний правый), 3: A (нижний правый)

    pegs_meta = []
    for i in range(2):
        py = left_ys[i]
        t = (py - shoulder_y) / max(1, (waist_y - shoulder_y))
        half_w = hw_top + (hw_bot - hw_top) * max(0.0, min(1.0, t))
        edge_x = cx - half_w
        post_x = edge_x + 28
        _draw_ukulele_pearl_peg(canvas, int(post_x), int(py), int(edge_x), is_left=True, scale=1.02)
        pegs_meta.append({
            "string_index": i,
            "side": "left",
            "peg_pos": [round(post_x / W, 4), round(1.0 - py / H, 4)],
            "nut_pos": [round(nut_xs[i] / W, 4), round(1.0 - nut_y / H, 4)],
        })

    for j in range(2):
        s_idx = 2 + j
        py = right_ys[j]
        t = (py - shoulder_y) / max(1, (waist_y - shoulder_y))
        half_w = hw_top + (hw_bot - hw_top) * max(0.0, min(1.0, t))
        edge_x = cx + half_w
        post_x = edge_x - 28
        _draw_ukulele_pearl_peg(canvas, int(post_x), int(py), int(edge_x), is_left=False, scale=1.02)
        pegs_meta.append({
            "string_index": s_idx,
            "side": "right",
            "peg_pos": [round(post_x / W, 4), round(1.0 - py / H, 4)],
            "nut_pos": [round(nut_xs[s_idx] / W, 4), round(1.0 - nut_y / H, 4)],
        })

    return canvas, pegs_meta


def _generate_bass_4_fender_headstock():
    """Генерирует 4-струнный бас с колками-трилистниками, выходящими строго от левого торца дерева."""
    W, H = 480, 560
    cx = 266
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    nut_y = 426
    fret1_y = 516
    nw = 62

    x_bot_edge = cx - nw - 44
    y_bot_edge = 344
    x_top_edge = cx - nw + 16
    y_top_edge = 62

    head_poly = [
        (cx - nw, nut_y),
        (cx - nw - 12, 392),
        (x_bot_edge, y_bot_edge),
        (x_top_edge, y_top_edge),
    ]

    arc_cx, arc_cy = cx + 24, 72
    arc_rx, arc_ry = 68, 48
    for i in range(22):
        t = i / 21.0
        angle = math.pi * (1.0 - t)
        head_poly.append((arc_cx + math.cos(angle) * arc_rx, arc_cy - math.sin(angle) * arc_ry))

    head_poly.extend([
        (cx + arc_rx + 22, 106),
        (cx + nw + 12, 178),
        (cx + nw + 28, 286),
        (cx + nw + 22, 316),
        (cx + nw + 4, 368),
        (cx + nw, nut_y),
    ])

    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow)
    s_draw.polygon([(x, y + 8) for x, y in head_poly], fill=(0, 0, 0, 155))
    s_draw.rectangle([cx - nw, nut_y, cx + nw, H], fill=(0, 0, 0, 155))
    canvas.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(radius=9)))

    fret_tex = _create_wood_texture(W, H, (86, 60, 50), (62, 40, 32), (112, 82, 70), seed=303, vignette=True)
    fret_mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(fret_mask).rectangle([cx - nw, nut_y, cx + nw, H], fill=255)
    canvas.paste(fret_tex, (0, 0), fret_mask)

    maple_tex = _create_wood_texture(W, H, (226, 184, 134), (198, 154, 104), (244, 208, 162), seed=404, vignette=True)
    head_mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(head_mask).polygon(head_poly, fill=255)
    canvas.paste(maple_tex, (0, 0), head_mask)

    draw = ImageDraw.Draw(canvas)
    draw.polygon(head_poly, outline=(156, 114, 72, 225), width=2)

    draw.rectangle([cx - nw, fret1_y, cx + nw, fret1_y + 4], fill=(195, 190, 182, 255))
    draw.rectangle([cx - nw - 1, nut_y - 7, cx + nw + 1, nut_y + 5], fill=(246, 246, 244, 255))
    draw.line([(cx - nw, nut_y + 5), (cx + nw, nut_y + 5)], fill=(35, 18, 10, 230), width=2)

    margin_x = 15
    nut_xs = [
        cx - nw + margin_x + i * ((2 * (nw - margin_x)) / 3.0)
        for i in range(4)
    ]

    peg_ys = [336, 254, 172, 90]
    pegs_meta = []
    for i, py in enumerate(peg_ys):
        # Точная координата левой кромки дерева на высоте py
        t = (y_bot_edge - py) / max(1.0, (y_bot_edge - y_top_edge))
        edge_x = x_bot_edge + t * (x_top_edge - x_bot_edge)
        post_x = edge_x + 28
        _draw_clover_peg(canvas, int(post_x), int(py), int(edge_x), scale=0.95, angle_deg=-11)
        pegs_meta.append({
            "string_index": i,
            "side": "left",
            "peg_pos": [round(post_x / W, 4), round(1.0 - py / H, 4)],
            "nut_pos": [round(nut_xs[i] / W, 4), round(1.0 - nut_y / H, 4)],
        })

    # Ретейнер для струн D и G
    ret_x1 = int(nut_xs[2] - 10)
    ret_x2 = int(nut_xs[3] + 10)
    ret_y = 328
    draw.rounded_rectangle([ret_x1, ret_y - 6, ret_x2, ret_y + 6], radius=3, fill=(215, 220, 228, 255), outline=(55, 60, 68, 255))
    draw.ellipse([ret_x1 + 4, ret_y - 3, ret_x1 + 10, ret_y + 3], fill=(45, 48, 54, 255))
    draw.ellipse([ret_x2 - 10, ret_y - 3, ret_x2 - 4, ret_y + 3], fill=(45, 48, 54, 255))

    return canvas, pegs_meta


def _generate_bass_5_modern_headstock():
    """Генерирует 5-струнный бас с осями колков строго от боковых кромок грифа."""
    W, H = 480, 560
    cx = W // 2
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    nut_y = 426
    fret1_y = 516
    nw = 72

    head_poly = [
        (cx - nw, nut_y),
        (cx - nw - 12, 378),
        (cx - nw - 34, 336),
        (cx - nw - 14, 238),
        (cx - nw + 6, 134),
        (cx - 58, 34),
    ]

    for i in range(1, 16):
        t = i / 15.0
        px = (cx - 58) + t * 124
        py = 34 + 34 * math.sin(t * math.pi * 0.65)
        head_poly.append((px, py))

    head_poly.extend([
        (cx + 68, 72),
        (cx + nw - 2, 168),
        (cx + nw + 18, 212),
        (cx + nw + 12, 265),
        (cx + nw + 32, 326),
        (cx + nw + 12, 378),
        (cx + nw, nut_y),
    ])

    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow)
    s_draw.polygon([(x, y + 8) for x, y in head_poly], fill=(0, 0, 0, 155))
    s_draw.rectangle([cx - nw, nut_y, cx + nw, H], fill=(0, 0, 0, 155))
    canvas.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(radius=9)))

    fret_tex = _create_wood_texture(W, H, (86, 60, 50), (62, 40, 32), (112, 82, 70), seed=303, vignette=True)
    fret_mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(fret_mask).rectangle([cx - nw, nut_y, cx + nw, H], fill=255)
    canvas.paste(fret_tex, (0, 0), fret_mask)

    maple_tex = _create_wood_texture(W, H, (226, 184, 134), (198, 154, 104), (244, 208, 162), seed=404, vignette=True)
    head_mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(head_mask).polygon(head_poly, fill=255)
    canvas.paste(maple_tex, (0, 0), head_mask)

    draw = ImageDraw.Draw(canvas)
    draw.polygon(head_poly, outline=(156, 114, 72, 225), width=2)

    gloss = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(gloss)
    g_draw.polygon([(cx - 58, 34), (cx + 68, 72), (cx + 68, 135), (cx - 48, 82)], fill=(255, 255, 255, 42))
    g_mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(g_mask).polygon(head_poly, fill=255)
    canvas.paste(Image.alpha_composite(canvas, gloss), (0, 0), g_mask)

    truss_y = nut_y - 34
    draw.ellipse([cx - 17, truss_y - 17, cx + 17, truss_y + 17], fill=(32, 34, 38, 250), outline=(18, 20, 22, 255), width=2)
    draw.ellipse([cx - 13, truss_y - 3, cx - 7, truss_y + 3], fill=(145, 150, 158, 255))
    draw.ellipse([cx + 7, truss_y - 3, cx + 13, truss_y + 3], fill=(145, 150, 158, 255))

    draw.rectangle([cx - nw, fret1_y, cx + nw, fret1_y + 4], fill=(195, 190, 182, 255))
    draw.rectangle([cx - nw - 1, nut_y - 7, cx + nw + 1, nut_y + 5], fill=(246, 246, 244, 255))
    draw.line([(cx - nw, nut_y + 5), (cx + nw, nut_y + 5)], fill=(35, 18, 10, 230), width=2)

    margin_x = 15
    nut_xs = [
        cx - nw + margin_x + i * ((2 * (nw - margin_x)) / 4.0)
        for i in range(5)
    ]

    # (string_index, post_x, post_y, edge_x) — ось начинается строго от edge_x!
    left_pegs = [
        (0, cx - nw + 6, 314, cx - nw - 28),
        (1, cx - nw + 16, 220, cx - nw - 12),
        (2, cx - 22, 118, cx - 64),
    ]
    right_pegs = [
        (3, cx + 44, 212, cx + nw + 16),
        (4, cx + nw - 6, 314, cx + nw + 28),
    ]

    pegs_meta = []
    for s_idx, px, py, ex in left_pegs:
        _draw_chrome_peg(canvas, px, py, ex, is_left=True, scale=0.95, is_bass=True)
        pegs_meta.append({
            "string_index": s_idx,
            "side": "left",
            "peg_pos": [round(px / W, 4), round(1.0 - py / H, 4)],
            "nut_pos": [round(nut_xs[s_idx] / W, 4), round(1.0 - nut_y / H, 4)],
        })

    for s_idx, px, py, ex in right_pegs:
        _draw_chrome_peg(canvas, px, py, ex, is_left=False, scale=0.95, is_bass=True)
        pegs_meta.append({
            "string_index": s_idx,
            "side": "right",
            "peg_pos": [round(px / W, 4), round(1.0 - py / H, 4)],
            "nut_pos": [round(nut_xs[s_idx] / W, 4), round(1.0 - nut_y / H, 4)],
        })

    return canvas, pegs_meta


def _save_module(name, canvas, pegs_meta):
    buf = io.BytesIO()
    canvas.save(buf, format="PNG")
    b64_str = base64.b64encode(buf.getvalue()).decode("utf-8")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, f"{name}.py")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write('"""Автоматически сгенерированный ассет головы грифа."""\n\n')
        f.write(f"IMAGE_SIZE = {canvas.size}\n")
        f.write(f"PEGS_DATA = {repr(pegs_meta)}\n")
        f.write(f'PNG_BASE64 = "{b64_str}"\n')
    print(f"[OK] Сгенерирован модуль: {out_path}")


def generate_all():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    init_path = os.path.join(OUTPUT_DIR, "__init__.py")
    with open(init_path, "w", encoding="utf-8") as f:
        f.write("from . import guitar_6, bass_4, bass_5, ukulele_4\n")

    c_g6, p_g6 = _generate_guitar_6_headstock()
    _save_module("guitar_6", c_g6, p_g6)

    c_uk, p_uk = _generate_ukulele_4_headstock()
    _save_module("ukulele_4", c_uk, p_uk)

    c_b4, p_b4 = _generate_bass_4_fender_headstock()
    _save_module("bass_4", c_b4, p_b4)

    c_b5, p_b5 = _generate_bass_5_modern_headstock()
    _save_module("bass_5", c_b5, p_b5)


if __name__ == "__main__":
    generate_all()