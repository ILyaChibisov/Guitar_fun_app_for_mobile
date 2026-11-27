# tuner_utils/menu_generator.py
import base64
import io
import math
import os
from PIL import Image, ImageDraw

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


def save_tuner_menu_assets():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    panel_dark = generate_panel_png(light_theme=False)
    panel_light = generate_panel_png(light_theme=True)

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