# metronome_utils/fader_generator.py
import base64
import io
import os
from PIL import Image, ImageDraw, ImageFilter

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "metronome")


def generate_track_png():
    """Генерирует утопленный паз трека с внутренней тенью и боковыми рисками."""
    W, H = 140, 460
    cx = W // 2
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    slot_w = 24
    pad_y = 34
    x1 = cx - slot_w // 2
    x2 = cx + slot_w // 2
    y1 = pad_y
    y2 = H - pad_y
    radius = slot_w // 2

    # 1. Внешняя лёгкая светлая фаска вокруг выреза (эффект толщины панели)
    draw.rounded_rectangle([x1 - 2, y1 - 2, x2 + 2, y2 + 2], radius=radius + 2, outline=(255, 255, 255, 38), width=2)

    # 2. Тёмная основа канавки
    slot_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(slot_layer)
    s_draw.rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=(18, 20, 23, 245))

    # Глубокая внутренняя тень от верхнего и левого краёв паза
    shadow_src = Image.new("RGBA", (W, H), (0, 0, 0, 230))
    sh_draw = ImageDraw.Draw(shadow_src)
    sh_draw.rounded_rectangle([x1 + 3, y1 + 5, x2 + 4, y2 + 5], radius=radius, fill=(0, 0, 0, 0))
    shadow_blur = shadow_src.filter(ImageFilter.GaussianBlur(radius=4))
    slot_layer.alpha_composite(shadow_blur)

    slot_mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(slot_mask).rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=255)
    canvas.paste(slot_layer, (0, 0), slot_mask)

    # 3. Боковые деления (риски справа и слева от канавки, как на референсе)
    num_ticks = 17
    for i in range(num_ticks):
        t = i / (num_ticks - 1)
        ty = int(y1 + radius + t * (y2 - y1 - 2 * radius))
        is_major = (i % 4 == 0)
        tick_len = 13 if is_major else 8
        tick_h = 2 if is_major else 1
        alpha = 185 if is_major else 105
        gap = 8

        # Левая риска
        draw.rectangle([x1 - gap - tick_len, ty - tick_h // 2, x1 - gap, ty + (tick_h + 1) // 2], fill=(235, 240, 245, alpha))
        # Правая риска
        draw.rectangle([x2 + gap, ty - tick_h // 2, x2 + gap + tick_len, ty + (tick_h + 1) // 2], fill=(235, 240, 245, alpha))

    meta = {
        "slot_x_norm": [round(x1 / W, 4), round(x2 / W, 4)],
        "slot_y_norm": [round(1.0 - y2 / H, 4), round(1.0 - y1 / H, 4)],
        "travel_y_norm": [round(1.0 - (y2 - radius) / H, 4), round(1.0 - (y1 + radius) / H, 4)],
    }
    return canvas, meta


def generate_knob_png():
    """Генерирует компактную объёмную металлическую ручку фейдера с фасками и тенью."""
    W, H = 136, 152
    cx = W // 2
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    # Уменьшенный размер ручки (было 92x102 -> стало 66x72)
    kw, kh = 66, 72
    kx1 = cx - kw // 2
    ky1 = (H - kh) // 2 - 4
    kx2 = kx1 + kw
    ky2 = ky1 + kh
    radius = 12

    # 1. Мягкая падающая тень вниз от ручки
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle(
        [kx1 + 2, ky1 + 10, kx2 + 2, ky2 + 13], radius=radius, fill=(0, 0, 0, 200)
    )
    canvas.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(radius=7)))

    # 2. Основа корпуса ручки (металлический вертикальный градиент)
    body = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    b_draw = ImageDraw.Draw(body)
    for y in range(ky1, ky2 + 1):
        t = (y - ky1) / max(1, (ky2 - ky1))
        if t < 0.14:
            k = t / 0.14
            v = int(195 - 75 * k)
        elif t < 0.52:
            k = (t - 0.14) / 0.38
            v = int(120 - 88 * k)
        elif t < 0.86:
            k = (t - 0.52) / 0.34
            v = int(32 + 78 * k)
        else:
            k = (t - 0.86) / 0.14
            v = int(110 - 85 * k)
        b_draw.line([(kx1, y), (kx2, y)], fill=(v, v + 2, v + 5, 255))

    # Лёгкое затемнение по левому и правому краям для объёма
    side_shade = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ss_draw = ImageDraw.Draw(side_shade)
    for x in range(kx1, kx2 + 1):
        nx = abs((x - cx) / (kw * 0.5))
        if nx > 0.72:
            a = int(65 * ((nx - 0.72) / 0.28))
            ss_draw.line([(x, ky1), (x, ky2)], fill=(0, 0, 0, a))
    body.alpha_composite(side_shade)

    knob_mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(knob_mask).rounded_rectangle([kx1, ky1, kx2, ky2], radius=radius, fill=255)
    canvas.paste(body, (0, 0), knob_mask)

    # 3. Светлая металлическая окантовка-фаска по периметру
    bevel = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bv_draw = ImageDraw.Draw(bevel)
    bv_draw.rounded_rectangle([kx1, ky1, kx2, ky2], radius=radius, outline=(225, 232, 240, 155), width=2)
    bv_draw.rounded_rectangle([kx1 + 2, ky1 + 2, kx2 - 2, ky2 - 2], radius=radius - 2, outline=(255, 255, 255, 65), width=1)
    canvas.paste(Image.alpha_composite(canvas, bevel), (0, 0), knob_mask)

    # 4. Компактное окошко под светодиодный индикатор по центру ручки
    led_w, led_h = 26, 8
    cy_knob = (ky1 + ky2) // 2 - 1
    lx1 = cx - led_w // 2
    ly1 = cy_knob - led_h // 2
    lx2 = cx + led_w // 2
    ly2 = cy_knob + led_h // 2

    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle(
        [lx1 - 2, ly1 - 2, lx2 + 2, ly2 + 2],
        radius=3,
        fill=(10, 12, 14, 240),
        outline=(180, 190, 200, 90),
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



def save_fader_assets():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    track_img, track_meta = generate_track_png()
    knob_img, knob_meta = generate_knob_png()

    buf_t = io.BytesIO()
    track_img.save(buf_t, format="PNG")
    track_b64 = base64.b64encode(buf_t.getvalue()).decode("utf-8")

    buf_k = io.BytesIO()
    knob_img.save(buf_k, format="PNG")
    knob_b64 = base64.b64encode(buf_k.getvalue()).decode("utf-8")

    out_path = os.path.join(OUTPUT_DIR, "fader_assets.py")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write('"""Автоматически сгенерированные текстуры студийного фейдера."""\n\n')
        f.write(f"TRACK_SIZE = {track_img.size}\n")
        f.write(f"TRACK_META = {repr(track_meta)}\n")
        f.write(f'TRACK_PNG_BASE64 = "{track_b64}"\n\n')
        f.write(f"KNOB_SIZE = {knob_img.size}\n")
        f.write(f"KNOB_META = {repr(knob_meta)}\n")
        f.write(f'KNOB_PNG_BASE64 = "{knob_b64}"\n')

    init_path = os.path.join(OUTPUT_DIR, "__init__.py")
    with open(init_path, "w", encoding="utf-8") as f:
        f.write("from . import classic_graphite, fader_assets\n")

    print(f"[OK] Сгенерированы текстуры фейдера: {out_path}")


if __name__ == "__main__":
    save_fader_assets()
