# songs_utils/fader_generator.py
import base64
import io
import os
import random
from PIL import Image, ImageDraw, ImageFilter

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "songs")


def generate_panel_track_png():
    """Генерирует узкий утопленный паз трека с внутренней тенью и боковыми рисками для выезжающей панели."""
    W, H = 110, 480
    cx = W // 2
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    slot_w = 18
    pad_y = 26
    x1 = cx - slot_w // 2
    x2 = cx + slot_w // 2
    y1 = pad_y
    y2 = H - pad_y
    radius = slot_w // 2

    # 1. Внешняя лёгкая светлая фаска вокруг канавки
    draw.rounded_rectangle(
        [x1 - 2, y1 - 2, x2 + 2, y2 + 2],
        radius=radius + 2,
        outline=(255, 255, 255, 42),
        width=2,
    )

    # 2. Глубокая тёмная канавка с внутренней тенью
    slot_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(slot_layer)
    s_draw.rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=(14, 16, 18, 248))

    shadow_src = Image.new("RGBA", (W, H), (0, 0, 0, 235))
    ImageDraw.Draw(shadow_src).rounded_rectangle(
        [x1 + 2, y1 + 4, x2 + 3, y2 + 4],
        radius=radius,
        fill=(0, 0, 0, 0),
    )
    slot_layer.alpha_composite(shadow_src.filter(ImageFilter.GaussianBlur(radius=3.5)))

    slot_mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(slot_mask).rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=255)
    canvas.paste(slot_layer, (0, 0), slot_mask)

    # 3. Боковые деления (13 рисок: крупные на краях и в центре, мелкие промежуточные)
    num_ticks = 13
    for i in range(num_ticks):
        t = i / (num_ticks - 1)
        ty = int(y1 + radius + t * (y2 - y1 - 2 * radius))
        is_major = (i % 6 == 0)
        tick_len = 13 if is_major else 8
        tick_h = 2 if is_major else 1
        alpha = 200 if is_major else 115
        gap = 7

        draw.rectangle(
            [x1 - gap - tick_len, ty - tick_h // 2, x1 - gap, ty + (tick_h + 1) // 2],
            fill=(235, 242, 245, alpha),
        )
        draw.rectangle(
            [x2 + gap, ty - tick_h // 2, x2 + gap + tick_len, ty + (tick_h + 1) // 2],
            fill=(235, 242, 245, alpha),
        )

    meta = {
        "slot_x_norm": [round(x1 / W, 4), round(x2 / W, 4)],
        "slot_y_norm": [round(1.0 - y2 / H, 4), round(1.0 - y1 / H, 4)],
        "travel_y_norm": [round(1.0 - (y2 - radius) / H, 4), round(1.0 - (y1 + radius) / H, 4)],
    }
    return canvas, meta


def generate_panel_knob_png():
    """Генерирует компактную металлическую ручку со шлифованным градиентом и тенью (как на фото 1)."""
    W, H = 112, 124
    cx = W // 2
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    kw, kh = 62, 68
    kx1 = cx - kw // 2
    ky1 = (H - kh) // 2 - 3
    kx2 = kx1 + kw
    ky2 = ky1 + kh
    radius = 10

    # 1. Мягкая падающая тень вниз от ручки
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle(
        [kx1 + 2, ky1 + 8, kx2 + 2, ky2 + 12],
        radius=radius,
        fill=(0, 0, 0, 210),
    )
    canvas.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(radius=6)))

    # 2. Металлический корпус кнопки (светлый верхний блик -> тёмная середина -> серебристый низ)
    body = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    b_draw = ImageDraw.Draw(body)
    for y in range(ky1, ky2 + 1):
        t = (y - ky1) / max(1, (ky2 - ky1))
        if t < 0.16:
            k = t / 0.16
            v = int(235 - 75 * k)
        elif t < 0.50:
            k = (t - 0.16) / 0.34
            v = int(160 - 115 * k)
        elif t < 0.85:
            k = (t - 0.50) / 0.35
            v = int(45 + 145 * k)
        else:
            k = (t - 0.85) / 0.15
            v = int(190 - 95 * k)
        b_draw.line([(kx1, y), (kx2, y)], fill=(v, v + 2, v + 5, 255))

    # Лёгкая текстура шлифованного металла
    rng = random.Random(108)
    grain = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(grain)
    for x in range(kx1, kx2 + 1, 2):
        delta = rng.randint(-18, 18)
        col = (255, 255, 255, delta) if delta > 0 else (0, 0, 0, -delta)
        g_draw.line([(x, ky1), (x, ky2)], fill=col, width=1)
    body.alpha_composite(grain)

    # Лёгкое затемнение по левому и правому краям для объёма
    side_shade = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ss_draw = ImageDraw.Draw(side_shade)
    for x in range(kx1, kx2 + 1):
        nx = abs((x - cx) / (kw * 0.5))
        if nx > 0.72:
            a = int(70 * ((nx - 0.72) / 0.28))
            ss_draw.line([(x, ky1), (x, ky2)], fill=(0, 0, 0, a))
    body.alpha_composite(side_shade)

    knob_mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(knob_mask).rounded_rectangle([kx1, ky1, kx2, ky2], radius=radius, fill=255)
    canvas.paste(body, (0, 0), knob_mask)

    # 3. Светлая металлическая окантовка по периметру
    bevel = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bv_draw = ImageDraw.Draw(bevel)
    bv_draw.rounded_rectangle([kx1, ky1, kx2, ky2], radius=radius, outline=(235, 240, 246, 170), width=2)
    bv_draw.rounded_rectangle([kx1 + 2, ky1 + 2, kx2 - 2, ky2 - 2], radius=radius - 2, outline=(255, 255, 255, 70), width=1)
    canvas.paste(Image.alpha_composite(canvas, bevel), (0, 0), knob_mask)

    # 4. Углублённое окошко под светодиод в центре кнопки
    led_w, led_h = 26, 7
    cy_knob = (ky1 + ky2) // 2 - 1
    lx1 = cx - led_w // 2
    ly1 = cy_knob - led_h // 2
    lx2 = cx + led_w // 2
    ly2 = cy_knob + led_h // 2

    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle(
        [lx1 - 2, ly1 - 2, lx2 + 2, ly2 + 2],
        radius=3,
        fill=(12, 14, 16, 240),
        outline=(190, 198, 206, 100),
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


def save_panel_fader_assets():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    track_img, track_meta = generate_panel_track_png()
    knob_img, knob_meta = generate_panel_knob_png()

    buf_t = io.BytesIO()
    track_img.save(buf_t, format="PNG")
    track_b64 = base64.b64encode(buf_t.getvalue()).decode("utf-8")

    buf_k = io.BytesIO()
    knob_img.save(buf_k, format="PNG")
    knob_b64 = base64.b64encode(buf_k.getvalue()).decode("utf-8")

    out_path = os.path.join(OUTPUT_DIR, "panel_fader_assets.py")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write('"""Автоматически сгенерированные текстуры фейдера для выезжающих панелей."""\n\n')
        f.write(f"TRACK_SIZE = {track_img.size}\n")
        f.write(f"TRACK_META = {repr(track_meta)}\n")
        f.write(f'TRACK_PNG_BASE64 = "{track_b64}"\n\n')
        f.write(f"KNOB_SIZE = {knob_img.size}\n")
        f.write(f"KNOB_META = {repr(knob_meta)}\n")
        f.write(f'KNOB_PNG_BASE64 = "{knob_b64}"\n')

    init_path = os.path.join(OUTPUT_DIR, "__init__.py")
    with open(init_path, "w", encoding="utf-8") as f:
        f.write("from . import panel_fader_assets\n")

    print(f"[OK] Сгенерированы ассеты фейдера для песен/словаря: {out_path}")


if __name__ == "__main__":
    save_panel_fader_assets()
