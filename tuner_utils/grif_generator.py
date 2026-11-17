import base64
import io
import math
import os
import random
from PIL import Image, ImageDraw, ImageFilter

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "grifs")


def _create_wood_texture(width, height, base_rgb, grain_rgb, highlight_rgb=None, seed=42):
    rng = random.Random(seed)
    img = Image.new("RGBA", (width, height), (*base_rgb, 255))
    draw = ImageDraw.Draw(img)

    for y in range(height):
        ny = abs((y / max(1, height - 1)) - 0.45)
        factor = 1.04 - 0.14 * ny
        r = max(0, min(255, int(base_rgb[0] * factor)))
        g = max(0, min(255, int(base_rgb[1] * factor)))
        b = max(0, min(255, int(base_rgb[2] * factor)))
        draw.line([(0, y), (width, y)], fill=(r, g, b, 255))

    for _ in range(int(width * 2.2)):
        x = rng.randint(0, width - 1)
        alpha = rng.randint(20, 62)
        thickness = rng.choice([1, 1, 2])
        wave_amp = rng.uniform(0.6, 2.4)
        wave_freq = rng.uniform(0.012, 0.032)
        phase = rng.uniform(0, math.pi * 2)

        pts = []
        for y in range(0, height + 6, 6):
            dx = math.sin(y * wave_freq + phase) * wave_amp
            pts.append((x + dx, y))
        if len(pts) > 1:
            draw.line(pts, fill=(*grain_rgb, alpha), width=thickness)

    if highlight_rgb:
        for _ in range(int(width * 0.45)):
            x = rng.randint(0, width - 1)
            alpha = rng.randint(12, 30)
            wave_amp = rng.uniform(0.5, 1.8)
            wave_freq = rng.uniform(0.015, 0.03)
            phase = rng.uniform(0, math.pi * 2)
            pts = [(x + math.sin(y * wave_freq + phase) * wave_amp, y) for y in range(0, height + 8, 8)]
            if len(pts) > 1:
                draw.line(pts, fill=(*highlight_rgb, alpha), width=1)

    blurred = img.filter(ImageFilter.GaussianBlur(radius=0.55))
    solid = Image.new("RGBA", (width, height), (*base_rgb, 255))
    solid.alpha_composite(blurred)
    return solid


def _draw_chrome_peg(canvas, cx, cy, is_left, scale=1.0, is_bass=False):
    draw = ImageDraw.Draw(canvas)
    direction = -1 if is_left else 1

    c_dark = (52, 56, 64)
    c_mid = (165, 172, 182)
    c_light = (248, 250, 255)

    btn_offset = int((38 if is_bass else 36) * scale)
    btn_w = int((19 if is_bass else 17) * scale)
    btn_h = int((24 if is_bass else 22) * scale)

    bx_center = cx + direction * btn_offset
    bx1, bx2 = bx_center - btn_w, bx_center + btn_w
    by1, by2 = cy - btn_h, cy + btn_h

    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow)
    s_draw.rounded_rectangle([bx1, by1 + 5, bx2, by2 + 5], radius=int(10 * scale), fill=(0, 0, 0, 115))
    canvas.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(radius=4)))

    shaft_x1 = min(cx, bx_center)
    shaft_x2 = max(cx, bx_center)
    sh_h = int(6 * scale)
    draw.rectangle([shaft_x1, cy - sh_h, shaft_x2, cy + sh_h], fill=c_dark)
    draw.rectangle([shaft_x1, cy - int(3 * scale), shaft_x2, cy + int(1 * scale)], fill=c_light)

    for y in range(by1, by2 + 1):
        t = (y - by1) / max(1, (by2 - by1))
        if t < 0.30:
            ratio = t / 0.30
            col = tuple(int(c_mid[i] + (c_light[i] - c_mid[i]) * ratio) for i in range(3))
        elif t < 0.68:
            ratio = (t - 0.30) / 0.38
            col = tuple(int(c_light[i] + (c_dark[i] - c_light[i]) * ratio) for i in range(3))
        else:
            ratio = (t - 0.68) / 0.32
            col = tuple(int(c_dark[i] + (c_mid[i] - c_dark[i]) * ratio) for i in range(3))

        norm_y = abs((t - 0.5) * 2.0)
        inset = int((btn_w * 0.25) * (norm_y ** 3))
        draw.line([(bx1 + inset, y), (bx2 - inset, y)], fill=(*col, 255))

    draw.rounded_rectangle([bx1, by1, bx2, by2], radius=int(10 * scale), outline=(40, 44, 50, 210), width=1)

    r_outer = int((15 if is_bass else 14) * scale)
    r_inner = int((7.5 if is_bass else 7) * scale)
    draw.ellipse([cx - r_outer - 1, cy - r_outer + 2, cx + r_outer + 1, cy + r_outer + 4], fill=(0, 0, 0, 100))
    draw.ellipse([cx - r_outer, cy - r_outer, cx + r_outer, cy + r_outer], fill=c_mid, outline=c_dark, width=2)
    draw.ellipse([cx - r_outer + 3, cy - r_outer + 3, cx + r_outer - 3, cy + r_outer - 3], outline=c_light, width=1)
    draw.ellipse([cx - r_inner, cy - r_inner, cx + r_inner, cy + r_inner], fill=c_dark)
    draw.ellipse([cx - r_inner + 2, cy - r_inner + 1, cx + r_inner - 3, cy + r_inner - 4], fill=c_light)


def _generate_symmetric_headstock(n_strings, head_colors, fret_colors, peg_scale=1.0):
    W, H = 480, 560
    cx = W // 2
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    top_y = 26
    shoulder_y = 68
    waist_y = 365
    nut_y = 415
    fret1_y = 515

    hw_top = 104 if n_strings == 6 else 98
    hw_bot = 82 if n_strings == 6 else 80
    nw = 72 if n_strings == 6 else 70

    head_poly = []
    steps = 28
    for i in range(steps + 1):
        t = i / steps
        angle = math.pi * (1.0 - t)
        px = cx + math.cos(angle) * hw_top
        py = shoulder_y - math.sin(angle) * (shoulder_y - top_y)
        head_poly.append((px, py))

    head_poly.extend([
        (cx + hw_top, shoulder_y + 16),
        (cx + hw_bot + 4, (shoulder_y + waist_y) * 0.5),
        (cx + hw_bot, waist_y),
        (cx + nw, nut_y),
        (cx - nw, nut_y),
        (cx - hw_bot, waist_y),
        (cx - hw_bot - 4, (shoulder_y + waist_y) * 0.5),
        (cx - hw_top, shoulder_y + 16),
    ])

    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow)
    s_draw.polygon([(x, y + 7) for x, y in head_poly], fill=(0, 0, 0, 145))
    s_draw.rectangle([cx - nw, nut_y, cx + nw, H], fill=(0, 0, 0, 145))
    canvas.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(radius=9)))

    fret_tex = _create_wood_texture(W, H, *fret_colors, seed=101)
    fret_mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(fret_mask).rectangle([cx - nw, nut_y, cx + nw, H], fill=255)
    canvas.paste(fret_tex, (0, 0), fret_mask)

    head_tex = _create_wood_texture(W, H, *head_colors, seed=202)
    head_mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(head_mask).polygon(head_poly, fill=255)
    canvas.paste(head_tex, (0, 0), head_mask)

    draw = ImageDraw.Draw(canvas)
    draw.polygon(head_poly, outline=(45, 20, 8, 210))

    draw.rectangle([cx - nw, fret1_y, cx + nw, fret1_y + 4], fill=(198, 162, 76, 255))
    draw.line([(cx - nw, fret1_y + 1), (cx + nw, fret1_y + 1)], fill=(245, 222, 145, 255), width=1)

    draw.rectangle([cx - nw - 1, nut_y - 7, cx + nw + 1, nut_y + 5], fill=(245, 245, 243, 255))
    draw.line([(cx - nw, nut_y - 7), (cx + nw, nut_y - 7)], fill=(255, 255, 255, 255), width=2)
    draw.line([(cx - nw, nut_y + 5), (cx + nw, nut_y + 5)], fill=(35, 18, 10, 230), width=2)

    margin_x = 16 if n_strings == 6 else 22
    nut_xs = [
        cx - nw + margin_x + i * ((2 * (nw - margin_x)) / max(1, n_strings - 1))
        for i in range(n_strings)
    ]

    half = n_strings // 2
    left_ys = [330, 225, 120] if half == 3 else [295, 155]
    right_ys = [120, 225, 330] if half == 3 else [155, 295]

    pegs_meta = []
    for i in range(half):
        py = left_ys[i]
        t = (py - shoulder_y) / max(1, (waist_y - shoulder_y))
        half_w = hw_top + (hw_bot - hw_top) * max(0.0, min(1.0, t))
        px = cx - half_w + 20
        _draw_chrome_peg(canvas, int(px), int(py), is_left=True, scale=peg_scale)
        pegs_meta.append({
            "string_index": i,
            "side": "left",
            "peg_pos": [round(px / W, 4), round(1.0 - py / H, 4)],
            "nut_pos": [round(nut_xs[i] / W, 4), round(1.0 - nut_y / H, 4)],
        })

    for j in range(half):
        s_idx = half + j
        py = right_ys[j]
        t = (py - shoulder_y) / max(1, (waist_y - shoulder_y))
        half_w = hw_top + (hw_bot - hw_top) * max(0.0, min(1.0, t))
        px = cx + half_w - 20
        _draw_chrome_peg(canvas, int(px), int(py), is_left=False, scale=peg_scale)
        pegs_meta.append({
            "string_index": s_idx,
            "side": "right",
            "peg_pos": [round(px / W, 4), round(1.0 - py / H, 4)],
            "nut_pos": [round(nut_xs[s_idx] / W, 4), round(1.0 - nut_y / H, 4)],
        })

    return canvas, pegs_meta


def _generate_fender_bass_headstock(n_strings):
    W, H = 480, 560
    cx = 276
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    nut_y = 425
    fret1_y = 515
    nw = 66 if n_strings == 4 else 74

    x_bot_left = cx - nw - 10
    x_top_left = cx - nw + 12

    head_poly = [
        (cx - nw, nut_y),
        (x_bot_left, 385),
        (x_top_left, 76),
    ]

    arc_cx, arc_cy = cx + 10, 76
    arc_rx, arc_ry = nw - 6, 38
    for i in range(18):
        t = i / 17.0
        angle = math.pi * (1.0 - t)
        head_poly.append((arc_cx + math.cos(angle) * arc_rx, arc_cy - math.sin(angle) * arc_ry))

    head_poly.extend([
        (cx + arc_rx + 12, 102),
        (cx + nw - 2, 175),
        (cx + nw - 8, 270),
        (cx + nw, 370),
        (cx + nw, nut_y),
    ])

    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow)
    s_draw.polygon([(x, y + 7) for x, y in head_poly], fill=(0, 0, 0, 145))
    s_draw.rectangle([cx - nw, nut_y, cx + nw, H], fill=(0, 0, 0, 145))
    canvas.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(radius=9)))

    fret_tex = _create_wood_texture(W, H, (72, 40, 24), (48, 24, 14), (96, 56, 36), seed=303)
    fret_mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(fret_mask).rectangle([cx - nw, nut_y, cx + nw, H], fill=255)
    canvas.paste(fret_tex, (0, 0), fret_mask)

    maple_tex = _create_wood_texture(W, H, (226, 156, 72), (194, 122, 44), (246, 186, 104), seed=404)
    head_mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(head_mask).polygon(head_poly, fill=255)
    canvas.paste(maple_tex, (0, 0), head_mask)

    draw = ImageDraw.Draw(canvas)
    draw.polygon(head_poly, outline=(128, 74, 22, 220))

    draw.rectangle([cx - nw, fret1_y, cx + nw, fret1_y + 4], fill=(205, 195, 175, 255))
    draw.rectangle([cx - nw - 1, nut_y - 7, cx + nw + 1, nut_y + 5], fill=(246, 246, 244, 255))
    draw.line([(cx - nw, nut_y + 5), (cx + nw, nut_y + 5)], fill=(35, 18, 10, 230), width=2)

    margin_x = 16
    nut_xs = [
        cx - nw + margin_x + i * ((2 * (nw - margin_x)) / max(1, n_strings - 1))
        for i in range(n_strings)
    ]

    peg_ys = [355, 272, 189, 106] if n_strings == 4 else [365, 298, 231, 164, 98]
    pegs_meta = []

    for i in range(n_strings):
        py = peg_ys[i]
        t = (385 - py) / (385 - 76)
        edge_x = x_bot_left + t * (x_top_left - x_bot_left)
        px = edge_x + 22 + i * (5 if n_strings == 4 else 4)
        _draw_chrome_peg(canvas, int(px), int(py), is_left=True, scale=1.0 if n_strings == 4 else 0.88, is_bass=True)
        pegs_meta.append({
            "string_index": i,
            "side": "left",
            "peg_pos": [round(px / W, 4), round(1.0 - py / H, 4)],
            "nut_pos": [round(nut_xs[i] / W, 4), round(1.0 - nut_y / H, 4)],
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

    c_g6, p_g6 = _generate_symmetric_headstock(
        n_strings=6,
        head_colors=((154, 78, 36), (116, 54, 22), (186, 102, 50)),
        fret_colors=((78, 44, 26), (54, 28, 16), (102, 60, 38)),
        peg_scale=1.0,
    )
    _save_module("guitar_6", c_g6, p_g6)

    c_uk, p_uk = _generate_symmetric_headstock(
        n_strings=4,
        head_colors=((172, 92, 42), (132, 66, 26), (204, 118, 60)),
        fret_colors=((82, 46, 28), (58, 30, 18), (108, 64, 40)),
        peg_scale=0.95,
    )
    _save_module("ukulele_4", c_uk, p_uk)

    c_b4, p_b4 = _generate_fender_bass_headstock(n_strings=4)
    _save_module("bass_4", c_b4, p_b4)

    c_b5, p_b5 = _generate_fender_bass_headstock(n_strings=5)
    _save_module("bass_5", c_b5, p_b5)


if __name__ == "__main__":
    generate_all()