from PyQt5.QtGui import QPainter, QFont, QPen, QBrush, QColor, QLinearGradient, QRadialGradient, QFontMetrics
from PyQt5.QtCore import Qt


class DrawingElements:

    @staticmethod
    def get_color_from_data(color_data):
        if isinstance(color_data, list) and len(color_data) >= 3:
            return QColor(color_data[0], color_data[1], color_data[2])
        return QColor(0, 0, 0)

    @staticmethod
    def get_brush_from_style(style_name, x=0, y=0, radius=0, width=0, height=0):
        # Стили для баре
        if style_name == "wood":
            gradient = QLinearGradient(x, y, x + width, y + height)
            gradient.setColorAt(0, QColor(210, 180, 140))
            gradient.setColorAt(0.5, QColor(160, 120, 80))
            gradient.setColorAt(1, QColor(210, 180, 140))
            return QBrush(gradient)
        elif style_name == "metal":
            gradient = QLinearGradient(x, y, x + width, y + height)
            gradient.setColorAt(0, QColor(200, 200, 200))
            gradient.setColorAt(0.5, QColor(100, 100, 100))
            gradient.setColorAt(1, QColor(200, 200, 200))
            return QBrush(gradient)
        elif style_name == "rubber":
            gradient = QRadialGradient(x + width / 2, y + height / 2, max(width, height))
            gradient.setColorAt(0, QColor(80, 80, 80))
            gradient.setColorAt(1, QColor(40, 40, 40))
            return QBrush(gradient)
        elif style_name == "gradient":
            gradient = QLinearGradient(x, y, x + width, y + height)
            gradient.setColorAt(0, QColor(189, 183, 107))
            lighter = QColor(189, 183, 107).lighter(150)
            gradient.setColorAt(1, QColor(lighter.red(), lighter.green(), lighter.blue()))
            return QBrush(gradient)
        elif style_name == "striped":
            return QBrush(QColor(189, 183, 107))

        # Оранжевые стили для баре
        elif style_name == "orange_gradient":
            gradient = QLinearGradient(x, y, x + width, y + height)
            gradient.setColorAt(0, QColor(255, 200, 100))
            gradient.setColorAt(0.5, QColor(255, 140, 0))
            gradient.setColorAt(1, QColor(255, 100, 0))
            return QBrush(gradient)
        elif style_name == "orange_metal":
            gradient = QLinearGradient(x, y, x + width, y + height)
            gradient.setColorAt(0, QColor(255, 220, 150))
            gradient.setColorAt(0.3, QColor(255, 180, 80))
            gradient.setColorAt(0.7, QColor(255, 140, 40))
            gradient.setColorAt(1, QColor(255, 120, 20))
            return QBrush(gradient)
        elif style_name == "orange_glow":
            gradient = QRadialGradient(x + width / 2, y + height / 2, max(width, height) * 0.8)
            gradient.setColorAt(0, QColor(255, 230, 180))
            gradient.setColorAt(0.5, QColor(255, 180, 80))
            gradient.setColorAt(1, QColor(255, 140, 0))
            return QBrush(gradient)
        elif style_name == "dark_orange":
            gradient = QLinearGradient(x, y, x + width, y + height)
            gradient.setColorAt(0, QColor(255, 150, 50))
            gradient.setColorAt(0.5, QColor(255, 120, 0))
            gradient.setColorAt(1, QColor(220, 100, 0))
            return QBrush(gradient)
        elif style_name == "orange_wood":
            gradient = QLinearGradient(x, y, x + width, y + height)
            gradient.setColorAt(0, QColor(255, 200, 150))
            gradient.setColorAt(0.3, QColor(255, 170, 100))
            gradient.setColorAt(0.7, QColor(255, 140, 60))
            gradient.setColorAt(1, QColor(255, 120, 40))
            return QBrush(gradient)
        elif style_name == "bright_orange":
            gradient = QLinearGradient(x, y, x + width, y + height)
            gradient.setColorAt(0, QColor(255, 230, 100))
            gradient.setColorAt(0.5, QColor(255, 200, 0))
            gradient.setColorAt(1, QColor(255, 160, 0))
            return QBrush(gradient)
        elif style_name == "orange_red":
            gradient = QLinearGradient(x, y, x + width, y + height)
            gradient.setColorAt(0, QColor(255, 180, 100))
            gradient.setColorAt(0.5, QColor(255, 120, 0))
            gradient.setColorAt(1, QColor(255, 80, 0))
            return QBrush(gradient)
        elif style_name == "orange_yellow":
            gradient = QLinearGradient(x, y, x + width, y + height)
            gradient.setColorAt(0, QColor(255, 240, 150))
            gradient.setColorAt(0.5, QColor(255, 200, 50))
            gradient.setColorAt(1, QColor(255, 180, 0))
            return QBrush(gradient)
        elif style_name == "orange_brown":
            gradient = QLinearGradient(x, y, x + width, y + height)
            gradient.setColorAt(0, QColor(255, 190, 130))
            gradient.setColorAt(0.5, QColor(255, 150, 80))
            gradient.setColorAt(1, QColor(210, 120, 60))
            return QBrush(gradient)
        elif style_name == "orange_pastel":
            gradient = QLinearGradient(x, y, x + width, y + height)
            gradient.setColorAt(0, QColor(255, 220, 180))
            gradient.setColorAt(0.5, QColor(255, 190, 140))
            gradient.setColorAt(1, QColor(255, 170, 120))
            return QBrush(gradient)

        # стили для нот
        elif style_name == "note_C":
            grad = QRadialGradient(x, y, radius)
            grad.setColorAt(0, QColor(255, 150, 150))
            grad.setColorAt(0.7, QColor(220, 50, 50))
            grad.setColorAt(1, QColor(180, 0, 0))
            return QBrush(grad)
        elif style_name == "note_C#":
            grad = QRadialGradient(x, y, radius)
            grad.setColorAt(0, QColor(255, 180, 120))
            grad.setColorAt(0.7, QColor(255, 100, 50))
            grad.setColorAt(1, QColor(200, 60, 0))
            return QBrush(grad)
        elif style_name == "note_D":
            grad = QRadialGradient(x, y, radius)
            grad.setColorAt(0, QColor(255, 220, 120))
            grad.setColorAt(0.7, QColor(255, 160, 50))
            grad.setColorAt(1, QColor(220, 100, 0))
            return QBrush(grad)
        elif style_name == "note_D#":
            grad = QRadialGradient(x, y, radius)
            grad.setColorAt(0, QColor(255, 240, 150))
            grad.setColorAt(0.7, QColor(255, 200, 60))
            grad.setColorAt(1, QColor(220, 150, 20))
            return QBrush(grad)
        elif style_name == "note_E":
            grad = QRadialGradient(x, y, radius)
            grad.setColorAt(0, QColor(220, 255, 150))
            grad.setColorAt(0.7, QColor(150, 220, 80))
            grad.setColorAt(1, QColor(80, 160, 40))
            return QBrush(grad)
        elif style_name == "note_F":
            grad = QRadialGradient(x, y, radius)
            grad.setColorAt(0, QColor(180, 255, 180))
            grad.setColorAt(0.7, QColor(80, 200, 80))
            grad.setColorAt(1, QColor(40, 160, 40))
            return QBrush(grad)
        elif style_name == "note_F#":
            grad = QRadialGradient(x, y, radius)
            grad.setColorAt(0, QColor(150, 255, 200))
            grad.setColorAt(0.7, QColor(60, 200, 150))
            grad.setColorAt(1, QColor(30, 140, 100))
            return QBrush(grad)
        elif style_name == "note_G":
            grad = QRadialGradient(x, y, radius)
            grad.setColorAt(0, QColor(180, 220, 255))
            grad.setColorAt(0.7, QColor(80, 160, 240))
            grad.setColorAt(1, QColor(40, 100, 200))
            return QBrush(grad)
        elif style_name == "note_G#":
            grad = QRadialGradient(x, y, radius)
            grad.setColorAt(0, QColor(150, 180, 255))
            grad.setColorAt(0.7, QColor(80, 100, 230))
            grad.setColorAt(1, QColor(40, 60, 180))
            return QBrush(grad)
        elif style_name == "note_A":
            grad = QRadialGradient(x, y, radius)
            grad.setColorAt(0, QColor(200, 170, 255))
            grad.setColorAt(0.7, QColor(130, 90, 220))
            grad.setColorAt(1, QColor(80, 50, 160))
            return QBrush(grad)
        elif style_name == "note_A#":
            grad = QRadialGradient(x, y, radius)
            grad.setColorAt(0, QColor(230, 200, 255))
            grad.setColorAt(0.7, QColor(180, 100, 230))
            grad.setColorAt(1, QColor(140, 60, 200))
            return QBrush(grad)
        elif style_name == "note_B":
            grad = QRadialGradient(x, y, radius)
            grad.setColorAt(0, QColor(255, 180, 220))
            grad.setColorAt(0.7, QColor(220, 80, 160))
            grad.setColorAt(1, QColor(180, 40, 120))
            return QBrush(grad)

        elif style_name == "orange_3d":
            grad = QRadialGradient(x, y, radius)
            grad.setColorAt(0, QColor(255, 220, 120))
            grad.setColorAt(0.7, QColor(255, 160, 50))
            grad.setColorAt(1, QColor(220, 100, 0))
            return QBrush(grad)

        elif style_name == "glass":
            return QBrush(QColor(200, 200, 200, 100))
        else:
            # fallback red_3d
            grad = QRadialGradient(x, y, radius)
            grad.setColorAt(0, QColor(255, 150, 150))
            grad.setColorAt(0.7, QColor(220, 50, 50))
            grad.setColorAt(1, QColor(180, 0, 0))
            return QBrush(grad)



    @staticmethod
    def get_outline_pen(outline_type):
        if outline_type == 'thin':
            return QPen(QColor(0, 0, 0), 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        elif outline_type == 'medium':
            return QPen(QColor(0, 0, 0), 4, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        elif outline_type == 'thick':
            return QPen(QColor(0, 0, 0), 6, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        else:
            return QPen(Qt.NoPen)

    @staticmethod
    def draw_fret(painter, fret_data):
        x = fret_data.get('x', 0)
        y = fret_data.get('y', 0)
        size = fret_data.get('size', 60)
        symbol = fret_data.get('symbol', 'I')
        color = DrawingElements.get_color_from_data(fret_data.get('color'))
        style = fret_data.get('style', 'default')
        font_family = fret_data.get('font_family', 'Arial')

        if style == 'gradient_text':
            gradient = QLinearGradient(x - size, y - size, x + size, y + size)
            gradient.setColorAt(0, QColor(255, 100, 100))
            gradient.setColorAt(0.5, color)
            gradient.setColorAt(1, QColor(100, 100, 255))
            painter.setPen(QPen(gradient, 2))
        elif style == 'shadow':
            painter.setPen(QPen(QColor(0, 0, 0, 100), 3))
        elif style == 'glow':
            painter.setPen(QPen(QColor(255, 255, 255, 80), 4))
        elif style == 'outline':
            painter.setPen(QPen(QColor(255, 255, 255), 4))
        elif style == 'metallic':
            gradient = QLinearGradient(x - size, y - size, x + size, y + size)
            gradient.setColorAt(0, QColor(255, 255, 255))
            gradient.setColorAt(0.3, QColor(200, 200, 200))
            gradient.setColorAt(0.7, QColor(100, 100, 100))
            gradient.setColorAt(1, QColor(150, 150, 150))
            painter.setPen(QPen(gradient, 2))
        elif style == 'gold_embossed':
            gradient = QLinearGradient(x - size, y - size, x + size, y + size)
            gradient.setColorAt(0, QColor(255, 215, 0))
            gradient.setColorAt(0.5, QColor(218, 165, 32))
            gradient.setColorAt(1, QColor(184, 134, 11))
            painter.setPen(QPen(gradient, 3))
        elif style == 'silver_embossed':
            gradient = QLinearGradient(x - size, y - size, x + size, y + size)
            gradient.setColorAt(0, QColor(255, 255, 255))
            gradient.setColorAt(0.5, QColor(192, 192, 192))
            gradient.setColorAt(1, QColor(150, 150, 150))
            painter.setPen(QPen(gradient, 3))
        elif style == 'neon':
            neon_color = QColor(color)
            neon_color.setAlpha(200)
            painter.setPen(QPen(neon_color, 2))
        elif style == 'stamped':
            stamp_color = QColor(color)
            stamp_color.setAlpha(180)
            painter.setPen(QPen(stamp_color, 2))
        else:
            painter.setPen(QPen(color, 2))

        font = QFont(font_family, size, QFont.Bold)
        painter.setFont(font)
        font_metrics = QFontMetrics(font)
        text_width = font_metrics.width(symbol)
        text_height = font_metrics.height()
        text_x = x - text_width // 2
        text_y = y + text_height // 3
        painter.drawText(text_x, text_y, symbol)

    @staticmethod
    def draw_note(painter, note_data):
        x = note_data.get('x', 0)
        y = note_data.get('y', 0)
        radius = note_data.get('radius', 15)
        style = note_data.get('style', 'red_3d')
        text_color = DrawingElements.get_color_from_data(note_data.get('text_color', [255, 255, 255]))
        font_style = note_data.get('font_style', 'normal')
        outline_type = note_data.get('outline', 'none')

        display_text = note_data.get('display_text', 'finger')
        if display_text == 'note_name':
            symbol = note_data.get('note_name', '')
        elif display_text == 'symbol':
            symbol = note_data.get('symbol', '')
        else:
            symbol = note_data.get('finger', '1')

        brush = DrawingElements.get_brush_from_style(style, x, y, radius)
        painter.setPen(Qt.NoPen)
        painter.setBrush(brush)
        painter.drawEllipse(x - radius, y - radius, radius * 2, radius * 2)

        outline_pen = DrawingElements.get_outline_pen(outline_type)
        if outline_pen != Qt.NoPen:
            painter.setPen(outline_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(x - radius, y - radius, radius * 2, radius * 2)

        if symbol:
            painter.setPen(QPen(text_color))
            font_size = max(10, radius)
            font = QFont("Arial", font_size)
            if font_style == 'bold':
                font.setWeight(QFont.Bold)
            elif font_style == 'light':
                font.setWeight(QFont.Light)
            elif font_style == 'italic':
                font.setItalic(True)
            elif font_style == 'bold_italic':
                font.setWeight(QFont.Bold)
                font.setItalic(True)
            painter.setFont(font)

            font_metrics = QFontMetrics(font)
            text_width = font_metrics.width(symbol)
            text_height = font_metrics.height()
            text_x = x - text_width // 2
            text_y = y + text_height // 4

            if text_width > radius * 1.8 or text_height > radius * 1.8:
                font_size = max(8, radius * 3 // 4)
                font.setPointSize(font_size)
                painter.setFont(font)
                font_metrics = QFontMetrics(font)
                text_width = font_metrics.width(symbol)
                text_height = font_metrics.height()
                text_x = x - text_width // 2
                text_y = y + text_height // 4

            painter.drawText(text_x, text_y, symbol)

    @staticmethod
    def draw_open_note(painter, open_note_data):
        x = open_note_data.get('x', 0)
        y = open_note_data.get('y', 0)
        radius = open_note_data.get('radius', 15)
        style = open_note_data.get('style', 'blue_gradient')
        text_color = DrawingElements.get_color_from_data(open_note_data.get('text_color', [255, 255, 255]))
        font_style = open_note_data.get('font_style', 'normal')
        outline_type = open_note_data.get('outline', 'none')

        display_text = open_note_data.get('display_text', 'symbol')
        if display_text == 'note_name':
            symbol = open_note_data.get('note_name', '')
        else:
            symbol = open_note_data.get('symbol', '')

        brush = DrawingElements.get_brush_from_style(style, x, y, radius)
        painter.setPen(Qt.NoPen)
        painter.setBrush(brush)
        painter.drawEllipse(x - radius, y - radius, radius * 2, radius * 2)

        outline_pen = DrawingElements.get_outline_pen(outline_type)
        if outline_pen != Qt.NoPen:
            painter.setPen(outline_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(x - radius, y - radius, radius * 2, radius * 2)

        if symbol:
            painter.setPen(QPen(text_color))
            font_size = max(10, radius)
            font = QFont("Arial", font_size)
            if font_style == 'bold':
                font.setWeight(QFont.Bold)
            elif font_style == 'light':
                font.setWeight(QFont.Light)
            elif font_style == 'italic':
                font.setItalic(True)
            elif font_style == 'bold_italic':
                font.setWeight(QFont.Bold)
                font.setItalic(True)
            painter.setFont(font)

            font_metrics = QFontMetrics(font)
            text_width = font_metrics.width(symbol)
            text_height = font_metrics.height()
            text_x = x - text_width // 2
            text_y = y + text_height // 4

            if text_width > radius * 1.8 or text_height > radius * 1.8:
                font_size = max(8, radius * 3 // 4)
                font.setPointSize(font_size)
                painter.setFont(font)
                font_metrics = QFontMetrics(font)
                text_width = font_metrics.width(symbol)
                text_height = font_metrics.height()
                text_x = x - text_width // 2
                text_y = y + text_height // 4

            painter.drawText(text_x, text_y, symbol)

    @staticmethod
    def draw_barre(painter, barre_data):
        x = barre_data.get('x', 0)
        y = barre_data.get('y', 0)
        width = barre_data.get('width', 100)
        height = barre_data.get('height', 20)
        radius = barre_data.get('radius', 10)
        style = barre_data.get('style', 'wood')
        outline_type = barre_data.get('outline', 'none')

        brush = DrawingElements.get_brush_from_style(style, x, y, 0, width, height)

        painter.setPen(Qt.NoPen)
        painter.setBrush(brush)
        if radius > 0:
            painter.drawRoundedRect(x, y, width, height, radius, radius)
        else:
            painter.drawRect(x, y, width, height)

        outline_pen = DrawingElements.get_outline_pen(outline_type)
        if outline_pen != Qt.NoPen:
            painter.setPen(outline_pen)
            painter.setBrush(Qt.NoBrush)
            if radius > 0:
                painter.drawRoundedRect(x, y, width, height, radius, radius)
            else:
                painter.drawRect(x, y, width, height)