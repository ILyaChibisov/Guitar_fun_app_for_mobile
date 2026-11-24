# metronome_utils/metronome_generator.py
import base64
import io
import math
import os
import random
from PIL import Image, ImageDraw, ImageFilter

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "metronome")


def _create_wood_texture(w, h, base_rgb=(138, 78, 36), dark_rgb=(82, 42, 16), light_rgb=(176, 108, 54), seed=42):
    """Генерирует процедурную текстуру натурального лакированного дерева с волокнами."""
    rng = random.Random(seed)
    img = Image.new("RGBA", (w, h), (*base_rgb, 255))
    draw = ImageDraw.Draw(img)

    # Вертикальный градиент освещения
    for y in range(h):
        t = y / max(1, h - 1)
        shade = 1.06 - 0.18 * t
        r = max(0, min(255, int(base_rgb[0] * shade)))
        g = max(0, min(255, int(base_rgb[1] * shade)))
        b = max(0, min(255, int(base_rgb[2] * shade)))
        draw.line([(0, y), (w, y)], fill=(r, g, b, 255))

    # Волнистые древесные волокна
    grain = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(grain)
    for x0 in range(-20, w + 20, 6):
        freq = rng.uniform(0.008, 0.022)
        amp = rng.uniform(2.5, 7.0)
        phase = rng.uniform(0, math.pi * 2)
        is_dark = rng.random() < 0.65
        col = (*dark_rgb, rng.randint(35, 85)) if is_dark else (*light_rgb, rng.randint(25, 60))
        width = rng.randint(2, 5)

        pts = []
        for y in range(0, h + 16, 16):
            dx = math.sin(y * freq + phase) * amp
            pts.append((x0 + dx, y))
        g_draw.line(pts, fill=col, width=width)

    grain = grain.filter(ImageFilter.GaussianBlur(radius=1.6))
    img.alpha_composite(grain)
    return img


def _draw_gold_emblem(canvas, cx, cy, scale=1.0):
    """Рисует объёмную золотую эмблему на нижней панели."""
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)

    def sc(x, y):
        return (cx + x * scale, cy + y * scale)

    bars = [
        (-22, -16, -13, 18),
        (-9, -4, -1, 16),
        (3, -6, 11, 16),
        (15, -24, 24, 18),
    ]

    sh = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    sh_d = ImageDraw.Draw(sh)
    for x1, y1, x2, y2 in bars:
        sh_d.rounded_rectangle(
            [cx + x1 * scale + 4, cy + y1 * scale + 6, cx + x2 * scale + 4, cy + y2 * scale + 6],
            radius=int(5 * scale),
            fill=(28, 12, 4, 190),
        )
    sh_d.rounded_rectangle(
        [cx - 24 * scale + 4, cy + 4 * scale + 6, cx + 25 * scale + 4, cy + 25 * scale + 6],
        radius=int(11 * scale),
        fill=(28, 12, 4, 190),
    )
    canvas.alpha_composite(sh.filter(ImageFilter.GaussianBlur(radius=5)))

    gold_main = (228, 182, 74, 255)
    gold_light = (255, 236, 155, 255)
    gold_dark = (128, 86, 18, 255)

    for x1, y1, x2, y2 in bars:
        box = [cx + x1 * scale, cy + y1 * scale, cx + x2 * scale, cy + y2 * scale]
        draw.rounded_rectangle(box, radius=int(4.5 * scale), fill=gold_main, outline=gold_dark, width=max(2, int(1.8 * scale)))
        draw.line(
            [sc(x1 + 2, y1 + 3), sc(x1 + 2, y2 - 4)],
            fill=gold_light,
            width=max(2, int(1.8 * scale)),
        )

    palm_box = [cx - 23 * scale, cy + 4 * scale, cx + 24 * scale, cy + 24 * scale]
    draw.rounded_rectangle(palm_box, radius=int(10 * scale), fill=gold_main, outline=gold_dark, width=max(2, int(1.8 * scale)))

    thumb_box = [cx - 18 * scale, cy + 3 * scale, cx + 10 * scale, cy + 12 * scale]
    draw.rounded_rectangle(thumb_box, radius=int(4.5 * scale), fill=gold_light, outline=gold_dark, width=max(1, int(1.4 * scale)))

    canvas.alpha_composite(layer)


def _draw_winding_key(canvas, kx, ky, scale=1.0):
    """Рисует объёмный золотой заводной ключ справа от корпуса."""
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)

    gold_main = (222, 176, 70, 255)
    gold_light = (255, 236, 160, 255)
    gold_dark = (120, 78, 16, 255)

    shaft_x1 = kx - int(8 * scale)
    shaft_x2 = kx + int(34 * scale)
    shaft_h = int(7 * scale)
    draw.rounded_rectangle(
        [shaft_x1, ky - shaft_h, shaft_x2, ky + shaft_h],
        radius=int(3 * scale),
        fill=gold_main,
        outline=gold_dark,
        width=max(2, int(1.8 * scale)),
    )
    draw.line([(shaft_x1 + 4, ky - shaft_h + 3), (shaft_x2 - 4, ky - shaft_h + 3)], fill=gold_light, width=max(2, int(2.2 * scale)))

    ring_cx = kx + int(44 * scale)
    rx = int(20 * scale)
    ry = int(30 * scale)

    sh = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse(
        [ring_cx - rx + 5, ky - ry + 7, ring_cx + rx + 5, ky + ry + 7],
        outline=(0, 0, 0, 165),
        width=max(6, int(10 * scale)),
    )
    canvas.alpha_composite(sh.filter(ImageFilter.GaussianBlur(radius=6)))

    draw.ellipse(
        [ring_cx - rx, ky - ry, ring_cx + rx, ky + ry],
        outline=gold_dark,
        width=max(7, int(12 * scale)),
    )
    draw.ellipse(
        [ring_cx - rx, ky - ry, ring_cx + rx, ky + ry],
        outline=gold_main,
        width=max(5, int(9 * scale)),
    )
    draw.arc(
        [ring_cx - rx + 2, ky - ry + 2, ring_cx + rx - 2, ky + ry - 2],
        start=190,
        end=350,
        fill=gold_light,
        width=max(2, int(3.5 * scale)),
    )

    canvas.alpha_composite(layer)


def generate_graphite_metronome():
    # Рендерим в 2x (1280x1680) для идеально гладких диагоналей без пунктира
    SS = 2
    W, H = 640 * SS, 840 * SS
    cx = 288 * SS
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    apex = (cx + 12 * SS, 34 * SS)
    tl_top = (cx - 72 * SS, 64 * SS)
    tr_top = (cx + 76 * SS, 62 * SS)
    side_top = (cx + 106 * SS, 76 * SS)

    fl_split = (cx - 148 * SS, 540 * SS)
    fr_split = (cx + 132 * SS, 544 * SS)
    side_split = (cx + 178 * SS, 524 * SS)

    fl_bot = (cx - 186 * SS, 756 * SS)
    fr_bot = (cx + 162 * SS, 762 * SS)
    side_bot = (cx + 214 * SS, 728 * SS)

    front_poly = [apex, tr_top, fr_split, fr_bot, fl_bot, fl_split, tl_top]
    side_poly = [tr_top, side_top, side_split, side_bot, fr_bot, fr_split]
    full_poly = [apex, tr_top, side_top, side_split, side_bot, fr_bot, fl_bot, fl_split, tl_top]

    # 1. Мягкая тень под корпусом
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).polygon([(x + 6 * SS, y + 18 * SS) for x, y in full_poly], fill=(0, 0, 0, 180))
    canvas.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(radius=16 * SS)))

    # 2. Три ножки снизу
    draw = ImageDraw.Draw(canvas)
    feet = [
        (fl_bot[0] + 46 * SS, fl_bot[1] - 4 * SS, 24 * SS, 16 * SS),
        (fr_bot[0] - 42 * SS, fr_bot[1] - 4 * SS, 24 * SS, 16 * SS),
        (side_bot[0] - 24 * SS, side_bot[1] - 6 * SS, 18 * SS, 13 * SS),
    ]
    for fx, fy, fw, fh in feet:
        draw.rounded_rectangle(
            [fx - fw, fy, fx + fw, fy + fh],
            radius=7 * SS,
            fill=(26, 16, 10, 255),
            outline=(110, 72, 42, 160),
            width=2,
        )

    # 3. Заводной ключ справа
    _draw_winding_key(canvas, kx=cx + 184 * SS, ky=634 * SS, scale=1.18 * SS)

    # 4. Правая объёмная 3D-грань (тёмный орех в тени)
    side_layer = _create_wood_texture(
        W, H,
        base_rgb=(92, 48, 20),
        dark_rgb=(54, 26, 10),
        light_rgb=(124, 68, 30),
        seed=19,
    )
    s_gloss = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(s_gloss).polygon(
        [(cx + 95 * SS, 220 * SS), (cx + 195 * SS, 340 * SS), (cx + 215 * SS, 520 * SS), (cx + 135 * SS, 420 * SS)],
        fill=(255, 225, 185, 42),
    )
    side_layer.alpha_composite(s_gloss.filter(ImageFilter.GaussianBlur(radius=14 * SS)))

    side_mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(side_mask).polygon(side_poly, fill=255)
    canvas.paste(side_layer, (0, 0), side_mask)

    # 5. Передний фасад (тёплое лакированное дерево — орех / махагон)
    front_layer = _create_wood_texture(
        W, H,
        base_rgb=(146, 82, 36),
        dark_rgb=(88, 44, 16),
        light_rgb=(188, 114, 56),
        seed=42,
    )

    # Лёгкий лаковый отсвет на передней панели
    gloss = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(gloss)
    g_draw.polygon(
        [(cx - 190 * SS, 540 * SS), (cx - 35 * SS, 542 * SS), (cx - 115 * SS, 762 * SS), (cx - 195 * SS, 760 * SS)],
        fill=(255, 232, 198, 44),
    )
    g_draw.polygon(
        [(cx - 95 * SS, 60 * SS), (cx - 45 * SS, 60 * SS), (cx - 125 * SS, 540 * SS), (cx - 155 * SS, 540 * SS)],
        fill=(255, 236, 205, 36),
    )
    front_layer.alpha_composite(gloss.filter(ImageFilter.GaussianBlur(radius=10 * SS)))

    front_mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(front_mask).polygon(front_poly, fill=255)
    canvas.paste(front_layer, (0, 0), front_mask)

    # 6. Глубокая ниша внутри деревянного корпуса
    recess_poly = [
        (cx - 48 * SS, 94 * SS),
        (cx + 50 * SS, 94 * SS),
        (cx + 104 * SS, 524 * SS),
        (cx - 116 * SS, 524 * SS),
    ]
    frame_poly = [
        (cx - 54 * SS, 88 * SS),
        (cx + 56 * SS, 88 * SS),
        (cx + 111 * SS, 530 * SS),
        (cx - 123 * SS, 530 * SS),
    ]

    draw = ImageDraw.Draw(canvas)
    draw.polygon(frame_poly, fill=(68, 34, 14, 255), outline=(212, 152, 86, 190), width=2 * SS)

    recess_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rc_draw = ImageDraw.Draw(recess_layer)
    for y in range(94 * SS, 526 * SS):
        t = (y - 94 * SS) / (432.0 * SS)
        r = int(28 + 14 * t)
        g = int(16 + 8 * t)
        b = int(10 + 5 * t)
        rc_draw.line([(0, y), (W, y)], fill=(r, g, b, 255))

    in_sh = Image.new("RGBA", (W, H), (0, 0, 0, 225))
    ImageDraw.Draw(in_sh).polygon(
        [(cx - 38 * SS, 108 * SS), (cx + 44 * SS, 108 * SS), (cx + 96 * SS, 518 * SS), (cx - 104 * SS, 518 * SS)],
        fill=(0, 0, 0, 0),
    )
    recess_layer.alpha_composite(in_sh.filter(ImageFilter.GaussianBlur(radius=9 * SS)))

    recess_mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(recess_mask).polygon(recess_poly, fill=255)
    canvas.paste(recess_layer, (0, 0), recess_mask)

    # 7. Глубокие тёмно-коричневые грани и фаски (вместо резких белых линий)
    edge_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ed_draw = ImageDraw.Draw(edge_layer)

    # Мягкие глубокие тени по контуру, чтобы придать объём (цвет тёмного ореха)
    shadow_color = (32, 12, 4, 220)
    # Обводка правой и нижней грани
    ed_draw.line([tr_top, side_top, side_split, side_bot, fr_bot], fill=shadow_color, width=5 * SS, joint="curve")
    # Обводка левой грани
    ed_draw.line([fl_bot, fl_split, tl_top, apex], fill=shadow_color, width=4 * SS, joint="curve")

    # Ребро между передней панелью и правой боковой гранью (тень перехода)
    ed_draw.line([tl_top, tr_top, fr_split, fr_bot], fill=(28, 10, 2, 255), width=4 * SS)

    # Горизонтальный стык между верхней крышкой и основанием (тёмный паз)
    ed_draw.line([fl_split, fr_split, side_split], fill=(24, 8, 0, 255), width=6 * SS)
    # Светлый микро-блик чуть выше стыка, чтобы создать эффект 3D-фаски
    ed_draw.line(
        [(fl_split[0], fl_split[1] - 2 * SS), (fr_split[0], fr_split[1] - 2 * SS),
         (side_split[0], side_split[1] - 2 * SS)],
        fill=(255, 185, 130, 120),
        width=2 * SS,
    )

    # Легкий блик по верхней левой грани, чтобы дерево «играло» на свету
    ed_draw.line([tl_top, apex], fill=(255, 210, 160, 90), width=2 * SS)

    # Накладываем размытие, чтобы линии не были резкими, как в Paint
    edge_layer = edge_layer.filter(ImageFilter.GaussianBlur(radius=1.5 * SS))
    canvas.alpha_composite(edge_layer)

    # 8. Золотая эмблема на нижней панели
    _draw_gold_emblem(canvas, cx - 8 * SS, 646 * SS, scale=1.35 * SS)

    # Уменьшаем с LANCZOS-фильтром до целевого 640x840 (идеальное сглаживание всех диагоналей)
    out_w, out_h = 640, 840
    final_canvas = canvas.resize((out_w, out_h), Image.Resampling.LANCZOS)

    pivot_x_px = 288 - 4
    pivot_y_px = 514
    scale_top_px = 148
    scale_bot_px = 472
    rod_len_px = 452

    meta = {
        "pivot": [round(pivot_x_px / out_w, 4), round(1.0 - pivot_y_px / out_h, 4)],
        "scale_y_range": [
            round(1.0 - scale_bot_px / out_h, 4),
            round(1.0 - scale_top_px / out_h, 4),
        ],
        "rod_length_norm": round(rod_len_px / out_h, 4),
    }

    return final_canvas, meta


def save_asset():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    init_path = os.path.join(OUTPUT_DIR, "__init__.py")
    with open(init_path, "w", encoding="utf-8") as f:
        f.write("from . import classic_graphite, fader_assets\n")

    canvas, meta = generate_graphite_metronome()
    buf = io.BytesIO()
    canvas.save(buf, format="PNG")
    b64_str = base64.b64encode(buf.getvalue()).decode("utf-8")

    out_path = os.path.join(OUTPUT_DIR, "classic_graphite.py")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write('"""Автоматически сгенерированный 3D-ассет деревянного корпуса метронома."""\n\n')
        f.write(f"IMAGE_SIZE = {canvas.size}\n")
        f.write(f"META_DATA = {repr(meta)}\n")
        f.write(f'PNG_BASE64 = "{b64_str}"\n')

    print(f"[OK] Сгенерирован деревянный корпус: {out_path}")


if __name__ == "__main__":
    save_asset()