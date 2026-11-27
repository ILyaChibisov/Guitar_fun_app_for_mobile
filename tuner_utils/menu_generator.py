# tuner_utils/menu_generator.py
import base64
import io
import math
import os
from PIL import Image, ImageDraw, ImageFilter
from metronome_utils.fader_generator import _add_brushed_metal_grain

from metronome_utils.button_generator import (
    generate_button_well_png,
    generate_keycap_png,
    generate_panel_png,
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "tuner")


def _draw_rotated_rect(canvas, cx, cy, w, h, angle_deg, fill, radius=0):
    pad = int(max(w, h) * 1.6) + 20
    tmp = Image.new("RGBA", (pad * 2, pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(tmp)
    if radius > 0:
        d.rounded_rectangle(
            [pad - w * 0.5, pad - h * 0.5, pad + w * 0.5, pad + h * 0.5],
            radius=radius,
            fill=fill,
        )
    else:
        d.rectangle(
            [pad - w * 0.5, pad - h * 0.5, pad + w * 0.5, pad + h * 0.5],
            fill=fill,
        )
    rot = tmp.rotate(angle_deg, resample=Image.BICUBIC, center=(pad, pad))
    canvas.alpha_composite(rot, (int(cx - pad), int(cy - pad)))


def _draw_rotated_ellipse(canvas, cx, cy, rx, ry, angle_deg, fill):
    pad = int(max(rx, ry) * 2.4) + 20
    tmp = Image.new("RGBA", (pad * 2, pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(tmp)
    d.ellipse([pad - rx, pad - ry, pad + rx, pad + ry], fill=fill)
    rot = tmp.rotate(angle_deg, resample=Image.BICUBIC, center=(pad, pad))
    canvas.alpha_composite(rot, (int(cx - pad), int(cy - pad)))


def generate_tuner_icon_png(icon_name):
    """Генерирует чёткие белые иконки 192x192 через 4x суперсэмплинг (768x768 -> 192x192)."""
    OUT = 192
    SS = 4
    S = OUT * SS
    cx, cy = S // 2, S // 2

    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    W = (255, 255, 255, 255)
    T = (0, 0, 0, 0)

    if icon_name == "play":
        d.polygon(
            [
                (cx - 126, cy - 172),
                (cx - 126, cy + 172),
                (cx + 176, cy),
            ],
            fill=W,
        )

    elif icon_name == "stop":
        r = 148
        d.rounded_rectangle([cx - r, cy - r, cx + r, cy + r], radius=38, fill=W)

    elif icon_name == "reset":
        r_out = 172
        r_in = 120
        d.ellipse([cx - r_out, cy - r_out, cx + r_out, cy + r_out], fill=W)
        d.ellipse([cx - r_in, cy - r_in, cx + r_in, cy + r_in], fill=T)

        d.pieslice(
            [cx - r_out - 16, cy - r_out - 16, cx + r_out + 16, cy + r_out + 16],
            start=-52,
            end=22,
            fill=T,
        )

        r_mid = (r_out + r_in) * 0.5
        thick = (r_out - r_in) * 0.5
        end_rad = math.radians(22)
        ex = cx + r_mid * math.cos(end_rad)
        ey = cy + r_mid * math.sin(end_rad)
        d.ellipse([ex - thick, ey - thick, ex + thick, ey + thick], fill=W)

        tip_rad = math.radians(-52)
        bx = cx + r_mid * math.cos(tip_rad)
        by = cy + r_mid * math.sin(tip_rad)
        tx, ty = -math.sin(tip_rad), math.cos(tip_rad)
        nx, ny = math.cos(tip_rad), math.sin(tip_rad)

        p1 = (bx + tx * 82, by + ty * 82)
        p2 = (bx - tx * 34 + nx * 68, by - ty * 34 + ny * 68)
        p3 = (bx - tx * 34 - nx * 68, by - ty * 34 - ny * 68)
        d.polygon([p1, p2, p3], fill=W)

    elif icon_name == "tune":
        # Три горизонтальных студийных фейдера выбора строя
        rows = [
            (cy - 118, cx - 58),
            (cy, cx + 66),
            (cy + 118, cx - 26),
        ]
        bar_x1, bar_x2 = cx - 168, cx + 168
        bar_h = 14
        knob_w, knob_h = 34, 66
        for ry, kx in rows:
            d.rounded_rectangle(
                [bar_x1, ry - bar_h, bar_x2, ry + bar_h],
                radius=bar_h,
                fill=W,
            )
            # Вырез вокруг ручки для читаемости силуэта
            d.rounded_rectangle(
                [kx - knob_w - 12, ry - knob_h - 8, kx + knob_w + 12, ry + knob_h + 8],
                radius=22,
                fill=T,
            )
            d.rounded_rectangle(
                [kx - knob_w, ry - knob_h, kx + knob_w, ry + knob_h],
                radius=16,
                fill=W,
            )




    elif icon_name == "bass":
        # Силуэт бас-гитары в полный рост под углом (как на референсе)
        angle = 58.0
        rad = math.radians(-angle)
        ux, uy = math.cos(rad), math.sin(rad)  # вдоль грифа (вверх-вправо)
        px, py = -uy, ux  # перпендикулярно (влево-вверх)

        def pt(along, perp=0.0):
            return (cx + ux * along + px * perp, cy + uy * along + py * perp)

        # Нижняя массивная часть асимметричной деки баса
        b1x, b1y = pt(-168, -4)
        _draw_rotated_ellipse(img, b1x, b1y, 76, 86, angle, W)
        # Средняя часть деки
        b2x, b2y = pt(-104, 2)
        _draw_rotated_ellipse(img, b2x, b2y, 66, 72, angle, W)
        # Характерный длинный верхний рог баса
        h1x, h1y = pt(-26, 48)
        _draw_rotated_ellipse(img, h1x, h1y, 58, 22, angle - 8, W)
        # Короткий нижний рог с вырезом (cutaway)
        h2x, h2y = pt(-54, -46)
        _draw_rotated_ellipse(img, h2x, h2y, 38, 19, angle + 14, W)
        # Углубления вырезов между рогами и грифом для чёткого силуэта
        c1x, c1y = pt(-34, 24)
        _draw_rotated_ellipse(img, c1x, c1y, 26, 12, angle, T)
        c2x, c2y = pt(-52, -24)
        _draw_rotated_ellipse(img, c2x, c2y, 24, 12, angle, T)
        # Длинный тонкий гриф баса
        nx, ny = pt(64, 0)
        _draw_rotated_rect(img, nx, ny, 268, 24, angle, W, radius=6)
        # Изогнутая голова грифа Fender-типа 4-в-ряд с закруглённым кончиком
        hx, hy = pt(214, 10)
        _draw_rotated_ellipse(img, hx, hy, 48, 25, angle + 10, W)
        tipx, tipy = pt(252, -4)
        _draw_rotated_ellipse(img, tipx, tipy, 22, 18, angle - 18, W)



    elif icon_name == "guitar":
        # Силуэт акустической гитары под углом 45° (розетка-кольцо, порожек и колки 3x3)
        angle = 45.0
        rad = math.radians(-angle)
        ux, uy = math.cos(rad), math.sin(rad)  # вдоль грифа (вверх-вправо)
        px, py = -uy, ux  # перпендикулярно (влево-вверх)

        def pt(along, perp=0.0):
            return (cx + ux * along + px * perp, cy + uy * along + py * perp)

        # Плавный корпус классической / акустической гитары («восьмёрка»)
        b1x, b1y = pt(-118, 0)
        b2x, b2y = pt(-8, 0)
        mx, my = pt(-64, 0)
        _draw_rotated_ellipse(img, b1x, b1y, 98, 112, angle, W)
        _draw_rotated_ellipse(img, b2x, b2y, 76, 88, angle, W)
        _draw_rotated_ellipse(img, mx, my, 72, 66, angle, W)

        # Бридж в нижней части деки (прозрачный вырез)
        brx, bry = pt(-142, 0)
        _draw_rotated_rect(img, brx, bry, 16, 66, angle, T, radius=6)
        # Розетка в виде кольца с точкой внутри (как на референсе)
        sx, sy = pt(-20, 0)
        _draw_rotated_ellipse(img, sx, sy, 38, 38, angle, T)
        _draw_rotated_ellipse(img, sx, sy, 22, 22, angle, W)
        # Сплошной ровный гриф
        nx, ny = pt(118, 0)
        _draw_rotated_rect(img, nx, ny, 140, 32, angle, W, radius=4)
        # Чёткий зазор верхнего порожка между грифом и головой
        nutx, nuty = pt(186, 0)
        _draw_rotated_rect(img, nutx, nuty, 12, 62, angle, T)
        # Скруглённая голова грифа 3x3
        hx, hy = pt(226, 0)
        _draw_rotated_rect(img, hx, hy, 74, 52, angle, W, radius=18)
        # 6 аккуратных колков по бокам головы грифа (3 сверху, 3 снизу)
        for along_off in (206, 226, 246):
            for side in (-1, 1):
                tx, ty = pt(along_off, side * 34)
                _draw_rotated_rect(img, tx, ty, 10, 18, angle, W, radius=4)



    elif icon_name == "ukulele":
        # Силуэт укулеле под углом 45° с раздельным грифом и головой 2x2 (как на референсе)
        angle = 45.0
        rad = math.radians(-angle)
        ux, uy = math.cos(rad), math.sin(rad)  # вдоль грифа (вверх-вправо)
        px, py = -uy, ux  # перпендикулярно (влево-вверх)

        def pt(along, perp=0.0):
            return (cx + ux * along + px * perp, cy + uy * along + py * perp)

        # Компактный вытянутый корпус укулеле (нижний овал, верхний овал и плавная талия)
        b1x, b1y = pt(-124, 0)
        b2x, b2y = pt(-18, 0)
        mx, my = pt(-72, 0)
        _draw_rotated_ellipse(img, b1x, b1y, 82, 92, angle, W)
        _draw_rotated_ellipse(img, b2x, b2y, 68, 76, angle, W)
        _draw_rotated_ellipse(img, mx, my, 62, 58, angle, W)

        # Бридж и розетка (прозрачные вырезы)
        brx, bry = pt(-142, 0)
        _draw_rotated_rect(img, brx, bry, 16, 52, angle, T, radius=6)
        sx, sy = pt(-28, 0)
        _draw_rotated_ellipse(img, sx, sy, 28, 28, angle, T)

        # V-образный вырез на стыке деки и грифа (как на референсе)
        notch_pts = [
            pt(32, 0),
            pt(60, -34),
            pt(60, 34),
        ]

        d.polygon(notch_pts, fill=T)
        # Раздельный сужающийся гриф
        neck_pts = [
            pt(50, -24),
            pt(178, -17),
            pt(178, 17),
            pt(50, 24),
        ]
        d.polygon(neck_pts, fill=W)

        # Зазор верхнего порожка между грифом и головой
        nutx, nuty = pt(186, 0)
        _draw_rotated_rect(img, nutx, nuty, 16, 60, angle, T)

        # Скруглённая трапециевидная голова грифа
        head_pts = [
            pt(194, -22),
            pt(248, -32),
            pt(256, 0),
            pt(248, 32),
            pt(194, 22),
        ]
        d.polygon(head_pts, fill=W)
        tipx, tipy = pt(244, 0)
        _draw_rotated_ellipse(img, tipx, tipy, 18, 30, angle, W)

        # 4 круглых колка 2x2 на коротких ножках
        for along_off in (208, 234):
            for side in (-1, 1):
                stx, sty = pt(along_off, side * 32)
                _draw_rotated_rect(img, stx, sty, 8, 14, angle, W)
                bx, by = pt(along_off, side * 42)
                _draw_rotated_ellipse(img, bx, by, 10, 10, angle, W)

    return img.resize((OUT, OUT), Image.LANCZOS)

from metronome_utils.fader_generator import _add_brushed_metal_grain


def generate_tuner_card_png(theme="dark"):
    """Генерирует HD-текстуру карточки тюнера для тем 'dark', 'green' и 'light'."""
    W, H = 960, 780
    light_theme = theme == "light"
    green_theme = theme == "green"
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    pad = 8
    x1, y1 = pad, pad
    x2, y2 = W - pad, H - pad
    radius = 34

    # 1. Металлическая плита корпуса (Faceplate)
    plate = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    p_draw = ImageDraw.Draw(plate)
    for y in range(y1, y2 + 1):
        t = (y - y1) / max(1, (y2 - y1))
        if light_theme:
            v = int(228 - 34 * t)
            col = (v, v + 2, v + 4, 248)
        else:
            if t < 0.06:
                k = t / 0.06
                v = int(78 - 26 * k)
            elif t < 0.94:
                k = (t - 0.06) / 0.88
                v = int(52 - 22 * k)
            else:
                k = (t - 0.94) / 0.06
                v = int(30 - 10 * k)
            col = (v, v + 2, v + 4, 248)
        p_draw.line([(x1, y), (x2, y)], fill=col)

    plate = _add_brushed_metal_grain(plate, x1, y1, x2, y2, strength=4)

    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=255)
    canvas.paste(plate, (0, 0), mask)

    # 2. Внешняя двойная фаска плиты
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

    # 3. Утопленная центральная ниша (Recessed Bay)
    bay_x1, bay_y1 = x1 + 48, y1 + 20
    bay_x2, bay_y2 = x2 - 48, y2 - 20
    bay_r = 24

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
        shadow_alpha = 120
    elif green_theme:
        # Полупрозрачный изумрудный тон 1-в-1 как в BottomNav: (0.0, 0.05, 0.03, 0.26)
        bay_fill = (0, 13, 8, 66)
        shadow_alpha = 155
    else:
        bay_fill = (15, 17, 21, 255)
        shadow_alpha = 235

    b_draw.rounded_rectangle([bay_x1, bay_y1, bay_x2, bay_y2], radius=bay_r, fill=bay_fill)

    bay_sh = Image.new("RGBA", (W, H), (0, 0, 0, shadow_alpha))
    ImageDraw.Draw(bay_sh).rounded_rectangle(
        [bay_x1 + 4, bay_y1 + 8, bay_x2 - 2, bay_y2 + 6], radius=bay_r, fill=(0, 0, 0, 0)
    )
    bay.alpha_composite(bay_sh.filter(ImageFilter.GaussianBlur(radius=7)))

    bay_mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(bay_mask).rounded_rectangle([bay_x1, bay_y1, bay_x2, bay_y2], radius=bay_r, fill=255)
    canvas.paste(bay, (0, 0), bay_mask)

    # 4. Четыре аппаратных винта под крест по углам консоли
    screw_r = 10
    screw_positions = [
        (x1 + 24, y1 + 28),
        (x2 - 24, y1 + 28),
        (x1 + 24, y2 - 28),
        (x2 - 24, y2 - 28),
    ]
    for sx, sy in screw_positions:
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
        draw.line([(sx - 5, sy), (sx + 5, sy)], fill=slot_col, width=2)
        draw.line([(sx, sy - 5), (sx, sy + 5)], fill=slot_col, width=2)

    return canvas

def generate_headstock_card_png(theme="dark"):
    """Генерирует HD-текстуру нижней рэковой карточки для блока грифа и кнопок нот."""
    W, H = 960, 480
    light_theme = theme == "light"
    green_theme = theme == "green"
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    pad = 8
    x1, y1 = pad, pad
    x2, y2 = W - pad, H - pad
    radius = 34

    # 1. Металлическая плита корпуса
    plate = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    p_draw = ImageDraw.Draw(plate)
    for y in range(y1, y2 + 1):
        t = (y - y1) / max(1, (y2 - y1))
        if light_theme:
            v = int(228 - 34 * t)
            col = (v, v + 2, v + 4, 248)
        else:
            if t < 0.08:
                k = t / 0.08
                v = int(78 - 26 * k)
            elif t < 0.92:
                k = (t - 0.08) / 0.84
                v = int(52 - 22 * k)
            else:
                k = (t - 0.92) / 0.08
                v = int(30 - 10 * k)
            col = (v, v + 2, v + 4, 248)
        p_draw.line([(x1, y), (x2, y)], fill=col)

    plate = _add_brushed_metal_grain(plate, x1, y1, x2, y2, strength=4)

    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=255)
    canvas.paste(plate, (0, 0), mask)

    # 2. Внешняя двойная фаска плиты
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

    # 3. Утопленная центральная ниша под гриф и кнопки нот
    bay_x1, bay_y1 = x1 + 48, y1 + 18
    bay_x2, bay_y2 = x2 - 48, y2 - 18
    bay_r = 24

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
        shadow_alpha = 120
    elif green_theme:
        bay_fill = (0, 13, 8, 66)
        shadow_alpha = 155
    else:
        bay_fill = (15, 17, 21, 255)
        shadow_alpha = 235

    b_draw.rounded_rectangle([bay_x1, bay_y1, bay_x2, bay_y2], radius=bay_r, fill=bay_fill)

    bay_sh = Image.new("RGBA", (W, H), (0, 0, 0, shadow_alpha))
    ImageDraw.Draw(bay_sh).rounded_rectangle(
        [bay_x1 + 4, bay_y1 + 8, bay_x2 - 2, bay_y2 + 6], radius=bay_r, fill=(0, 0, 0, 0)
    )
    bay.alpha_composite(bay_sh.filter(ImageFilter.GaussianBlur(radius=7)))

    bay_mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(bay_mask).rounded_rectangle([bay_x1, bay_y1, bay_x2, bay_y2], radius=bay_r, fill=255)
    canvas.paste(bay, (0, 0), bay_mask)

    # 4. Четыре аппаратных винта по углам консоли
    screw_r = 10
    screw_positions = [
        (x1 + 24, y1 + 26),
        (x2 - 24, y1 + 26),
        (x1 + 24, y2 - 26),
        (x2 - 24, y2 - 26),
    ]
    for sx, sy in screw_positions:
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
        draw.line([(sx - 5, sy), (sx + 5, sy)], fill=slot_col, width=2)
        draw.line([(sx, sy - 5), (sx, sy + 5)], fill=slot_col, width=2)

    return canvas




def save_tuner_menu_assets():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    panel_dark = generate_panel_png(light_theme=False)
    panel_light = generate_panel_png(light_theme=True)

    card_dark = generate_tuner_card_png(theme="dark")
    card_green = generate_tuner_card_png(theme="green")
    card_light = generate_tuner_card_png(theme="light")

    head_dark = generate_headstock_card_png(theme="dark")
    head_green = generate_headstock_card_png(theme="green")
    head_light = generate_headstock_card_png(theme="light")

    well_dark = generate_button_well_png(light_theme=False)
    up_dark, up_meta = generate_keycap_png(pressed=False, light_theme=False)
    down_dark, down_meta = generate_keycap_png(pressed=True, light_theme=False)

    well_light = generate_button_well_png(light_theme=True)
    up_light, _ = generate_keycap_png(pressed=False, light_theme=True)
    down_light, _ = generate_keycap_png(pressed=True, light_theme=True)

    icon_names = ["play", "stop", "reset", "tune", "guitar", "bass", "ukulele"]
    icons_b64 = {name: generate_tuner_icon_png(name) for name in icon_names}

    def to_b64(img):
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("utf-8")

    out_path = os.path.join(OUTPUT_DIR, "menu_assets.py")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write('"""HD-текстуры рэковой панели, триггер-пэдов и 4x SSAA иконок тюнера."""\n\n')
        f.write(f"PANEL_SIZE = {panel_dark.size}\n")
        f.write(f"BUTTON_SIZE = {well_dark.size}\n")
        f.write(f"UP_META = {repr(up_meta)}\n")
        f.write(f"DOWN_META = {repr(down_meta)}\n\n")
        f.write(f'HEADSTOCK_DARK_B64 = "{to_b64(head_dark)}"\n')
        f.write(f'HEADSTOCK_GREEN_B64 = "{to_b64(head_green)}"\n')
        f.write(f'HEADSTOCK_LIGHT_B64 = "{to_b64(head_light)}"\n\n')
        f.write(f'CARD_DARK_B64 = "{to_b64(card_dark)}"\n')
        f.write(f'CARD_GREEN_B64 = "{to_b64(card_green)}"\n')
        f.write(f'CARD_LIGHT_B64 = "{to_b64(card_light)}"\n\n')
        f.write(f'PANEL_DARK_B64 = "{to_b64(panel_dark)}"\n')
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
    with open(init_path, "w", encoding="utf-8") as f:
        f.write("from . import menu_assets\n")
    print(f"[OK] Сгенерированы ассеты меню тюнера: {out_path}")

if __name__ == "__main__":
    save_tuner_menu_assets()