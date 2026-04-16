# screens/chord_renderer.py
"""
Рендерер аккордов с раздельной калибровкой для каждого типа элементов
"""
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.image import Image
from kivy.core.image import Image as CoreImage
from kivy.graphics import Color, Rectangle
from io import BytesIO
import base64

try:
    from sprite_images import SPRITE_IMAGES

    HAS_SPRITES = True
except ImportError:
    HAS_SPRITES = False
    print("⚠️ sprite_images.py не найден")


class ChordRenderer(RelativeLayout):
    # Реальный размер картинки грифа
    IMAGE_WIDTH = 1376
    IMAGE_HEIGHT = 830

    # ============ КАЛИБРОВКА ДЛЯ ЛАДОВ (цифры над грифом) ============
    # Если лады внизу - УВЕЛИЧЬ FRET_Y_OFFSET (положительное значение)
    # Если лады вверху - УМЕНЬШИ (отрицательное)
    FRET_X_OFFSET = 0
    FRET_Y_OFFSET = 790  # ← ПРОБУЙ: 50, 100, 150, 200

    # ============ АВТОМАТИЧЕСКАЯ КАЛИБРОВКА ДЛЯ БАРЕ ============
    # Включить/выключить автоматическое смещение
    BARRE_AUTO_OFFSET = True

    # Дополнительное ручное смещение (если нужно)
    BARRE_EXTRA_OFFSET = 0

    # ============ КАЛИБРОВКА ДЛЯ НОТ И ПАЛЬЦЕВ ============
    NOTE_X_OFFSET = 0
    NOTE_Y_OFFSET = 0

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_module = None
        self.current_mode = "finger"
        self.background_texture = None

        self.griff_image = Image(
            allow_stretch=True,
            keep_ratio=True,
            size_hint=(1, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        self.add_widget(self.griff_image)

        self.sprite_layer = RelativeLayout(size_hint=(1, 1))
        self.add_widget(self.sprite_layer)

        self.bind(size=self._update_positions)
        self.bind(pos=self._update_positions)

    def set_background(self, texture):
        self.griff_image.texture = texture

    def load_chord(self, chord_module):
        self.current_module = chord_module
        self._create_sprites()

    def set_mode(self, mode):
        self.current_mode = mode
        self._create_sprites()

    def _transform_coords(self, x, y, offset_x=0, offset_y=0, invert_y=False):
        """Базовое преобразование координат"""
        if self.width <= 0 or self.height <= 0:
            return x, y

        scale_x = self.width / self.IMAGE_WIDTH
        scale_y = self.height / self.IMAGE_HEIGHT
        scale = min(scale_x, scale_y)

        img_width = self.IMAGE_WIDTH * scale
        img_height = self.IMAGE_HEIGHT * scale
        offset_x_img = (self.width - img_width) / 2
        offset_y_img = (self.height - img_height) / 2

        if invert_y:
            y = self.IMAGE_HEIGHT - y

        new_x = (x + offset_x) * scale + offset_x_img
        new_y = (y + offset_y) * scale + offset_y_img

        return new_x, new_y, scale

    def _create_sprites(self):
        if not self.current_module or not HAS_SPRITES:
            return

        self.sprite_layer.clear_widgets()

        notes = getattr(self.current_module, 'NOTES', {})
        open_notes = getattr(self.current_module, 'OPEN_NOTES', {})
        barres = getattr(self.current_module, 'BARRES', {})
        frets = getattr(self.current_module, 'FRETS', {})

        if self.current_mode == "finger":
            selected = getattr(self.current_module, 'SELECTED_FINGER', [])
        else:
            selected = getattr(self.current_module, 'SELECTED_NOTE', [])

        # Лады - БЕЗ инверсии, со своим смещением
        for fret_id, fret_data in frets.items():
            self._add_fret_sprite(fret_data)

        # Баре - С инверсией, со своим смещением
        for key in selected:
            if 'BAR' in key and key in barres:
                self._add_barre_sprite(barres[key])

        # Ноты/пальцы - С инверсией
        for key in selected:
            if 'BAR' in key:
                continue
            elif key in notes:
                self._add_note_sprite(notes[key])
            elif key in open_notes:
                self._add_x_sprite(open_notes[key])

    def _add_fret_sprite(self, fret_data):
        x = fret_data.get('x', 0)
        y = fret_data.get('y', 0)
        symbol = str(fret_data.get('symbol', ''))
        size = fret_data.get('size', 30)

        if not symbol:
            return

        # Лады: БЕЗ инверсии, со своим смещением
        new_x, new_y, scale = self._transform_coords(
            x, y,
            offset_x=self.FRET_X_OFFSET,
            offset_y=self.FRET_Y_OFFSET,
            invert_y=False
        )
        new_size = size * scale

        sprite_name = f"fret_{symbol}_{size}"

        if sprite_name in SPRITE_IMAGES:
            img_data = base64.b64decode(SPRITE_IMAGES[sprite_name])
            texture = CoreImage(BytesIO(img_data), ext="png").texture

            sprite = Image(
                texture=texture,
                size_hint=(None, None),
                size=(new_size * 2, new_size),
                pos=(new_x - new_size, new_y - new_size / 2),
                allow_stretch=True
            )
            self.sprite_layer.add_widget(sprite)

    def _add_note_sprite(self, note_data):
        x = note_data.get('x', 0)
        y = note_data.get('y', 0)
        radius = note_data.get('radius', 50)

        # Ноты: С инверсией
        new_x, new_y, scale = self._transform_coords(
            x, y,
            offset_x=self.NOTE_X_OFFSET,
            offset_y=self.NOTE_Y_OFFSET,
            invert_y=True
        )
        new_radius = radius * scale

        if new_radius < 6:
            new_radius = 6

        note_name = note_data.get('note_name', '')
        finger = note_data.get('finger', '')

        if self.current_mode == "finger":
            if finger:
                sprite_name = f"finger_{finger}_{radius}"
            elif note_name:
                clean_note = note_name.replace('#', 'sharp')
                sprite_name = f"note_{clean_note}_{radius}"
            else:
                return
        else:
            if not note_name:
                return
            clean_note = note_name.replace('#', 'sharp')
            sprite_name = f"note_{clean_note}_{radius}"

        if sprite_name in SPRITE_IMAGES:
            img_data = base64.b64decode(SPRITE_IMAGES[sprite_name])
            texture = CoreImage(BytesIO(img_data), ext="png").texture

            sprite = Image(
                texture=texture,
                size_hint=(None, None),
                size=(new_radius * 2, new_radius * 2),
                pos=(new_x - new_radius, new_y - new_radius),
                allow_stretch=True
            )
            self.sprite_layer.add_widget(sprite)

    def _add_x_sprite(self, note_data):
        x = note_data.get('x', 0)
        y = note_data.get('y', 0)
        radius = note_data.get('radius', 50)

        new_x, new_y, scale = self._transform_coords(
            x, y,
            offset_x=self.NOTE_X_OFFSET,
            offset_y=self.NOTE_Y_OFFSET,
            invert_y=True
        )
        new_radius = radius * scale

        if new_radius < 6:
            new_radius = 6

        sprite_name = f"x_{radius}"

        if sprite_name in SPRITE_IMAGES:
            img_data = base64.b64decode(SPRITE_IMAGES[sprite_name])
            texture = CoreImage(BytesIO(img_data), ext="png").texture

            sprite = Image(
                texture=texture,
                size_hint=(None, None),
                size=(new_radius * 2, new_radius * 2),
                pos=(new_x - new_radius, new_y - new_radius),
                allow_stretch=True
            )
            self.sprite_layer.add_widget(sprite)

    def _add_barre_sprite(self, barre_data):
        x = barre_data.get('x', 0)
        y = barre_data.get('y', 0)
        width = barre_data.get('width', 100)
        height = barre_data.get('height', 20)
        style = barre_data.get('style', 'wood')

        # АВТОМАТИЧЕСКОЕ СМЕЩЕНИЕ: смещаем на высоту баре
        if self.BARRE_AUTO_OFFSET:
            auto_offset = -height  # отрицательное = вверх
        else:
            auto_offset = 0

        total_offset = auto_offset + self.BARRE_EXTRA_OFFSET

        # Баре: С инверсией, с автоматическим смещением
        new_x, new_y, scale = self._transform_coords(
            x, y,
            offset_x=0,
            offset_y=total_offset,
            invert_y=True
        )
        new_width = width * scale
        new_height = height * scale

        sprite_name = f"barre_{style}_{width}x{height}"

        if sprite_name in SPRITE_IMAGES:
            img_data = base64.b64decode(SPRITE_IMAGES[sprite_name])
            texture = CoreImage(BytesIO(img_data), ext="png").texture

            sprite = Image(
                texture=texture,
                size_hint=(None, None),
                size=(new_width, new_height),
                pos=(new_x, new_y),
                allow_stretch=True
            )
            self.sprite_layer.add_widget(sprite)

    def _update_positions(self, *args):
        self._create_sprites()