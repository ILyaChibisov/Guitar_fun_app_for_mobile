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
import os
import sys

# ============ РАСШИРЕННЫЙ ПОИСК SPRITE_IMAGES ============
SPRITE_IMAGES = None
HAS_SPRITES = False

# Способ 1: прямой импорт из корня
try:
    from sprite_images import SPRITE_IMAGES

    HAS_SPRITES = True
    print("✅ Спрайты загружены (прямой импорт)")
except ImportError:
    pass

# Способ 2: через sys.path (добавляем корень проекта)
if not HAS_SPRITES:
    try:
        # Добавляем родительскую директорию в путь
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(current_dir)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        from sprite_images import SPRITE_IMAGES

        HAS_SPRITES = True
        print(f"✅ Спрайты загружены (через sys.path: {parent_dir})")
    except ImportError as e:
        print(f"⚠️ sprite_images.py не найден в {parent_dir}: {e}")

# Способ 3: ищем файл вручную
if not HAS_SPRITES:
    try:
        possible_paths = [
            os.path.join(os.path.dirname(os.path.dirname(__file__)), 'sprite_images.py'),
            os.path.join(os.getcwd(), 'sprite_images.py'),
            '/data/data/com.guitarfuns.guitarfuns/files/app/sprite_images.py',
        ]
        for path in possible_paths:
            if os.path.exists(path):
                print(f"✅ Найден файл спрайтов: {path}")
                import importlib.util

                spec = importlib.util.spec_from_file_location("sprite_images", path)
                sprite_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(sprite_module)
                SPRITE_IMAGES = getattr(sprite_module, 'SPRITE_IMAGES', None)
                if SPRITE_IMAGES:
                    HAS_SPRITES = True
                    print(f"✅ Спрайты загружены из файла: {path}")
                    break
    except Exception as e:
        print(f"⚠️ Ошибка при ручном поиске спрайтов: {e}")

if not HAS_SPRITES:
    print("⚠️ СПРАЙТЫ НЕ ЗАГРУЖЕНЫ! Аккорды не будут отображаться.")


# ===========================================================


class ChordRenderer(RelativeLayout):
    # Реальный размер картинки грифа
    IMAGE_WIDTH = 1376
    IMAGE_HEIGHT = 830

    # ============ КАЛИБРОВКА ДЛЯ ЛАДОВ ============
    FRET_X_OFFSET = 0
    FRET_Y_OFFSET = 790

    # ============ АВТОМАТИЧЕСКАЯ КАЛИБРОВКА ДЛЯ БАРЕ ============
    BARRE_AUTO_OFFSET = True
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
        print(f"🎵 load_chord: {chord_module}")
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
        if not self.current_module:
            print("⚠️ _create_sprites: current_module is None")
            return

        if not HAS_SPRITES:
            print("⚠️ _create_sprites: HAS_SPRITES is False")
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

        # Отладочный вывод
        print(f"🎸 Рендеринг аккорда: {getattr(self.current_module, 'METADATA', {}).get('name', 'Unknown')}")
        print(f"   Ладов: {len(frets)}, Нот: {len(notes)}, Баре: {len(barres)}, Выбрано: {len(selected)}")
        print(f"   Режим: {self.current_mode}, HAS_SPRITES: {HAS_SPRITES}")

        # Лады
        for fret_id, fret_data in frets.items():
            self._add_fret_sprite(fret_data)

        # Баре
        for key in selected:
            if 'BAR' in key and key in barres:
                self._add_barre_sprite(barres[key])

        # Ноты/пальцы
        for key in selected:
            if 'BAR' in key:
                continue
            elif key in notes:
                self._add_note_sprite(notes[key])
            elif key in open_notes:
                self._add_x_sprite(open_notes[key])

    def _get_sprite_texture(self, sprite_name):
        """Безопасное получение текстуры спрайта"""
        if not HAS_SPRITES or sprite_name not in SPRITE_IMAGES:
            return None
        try:
            img_data = base64.b64decode(SPRITE_IMAGES[sprite_name])
            texture = CoreImage(BytesIO(img_data), ext="png").texture
            return texture
        except Exception as e:
            print(f"Ошибка загрузки спрайта {sprite_name}: {e}")
            return None

    def _add_fret_sprite(self, fret_data):
        x = fret_data.get('x', 0)
        y = fret_data.get('y', 0)
        symbol = str(fret_data.get('symbol', ''))
        size = fret_data.get('size', 30)

        if not symbol:
            return

        new_x, new_y, scale = self._transform_coords(
            x, y,
            offset_x=self.FRET_X_OFFSET,
            offset_y=self.FRET_Y_OFFSET,
            invert_y=False
        )
        new_size = size * scale

        sprite_name = f"fret_{symbol}_{size}"
        texture = self._get_sprite_texture(sprite_name)

        if texture:
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
        radius_val = note_data.get('radius', 50)

        if self.current_mode == "finger":
            if finger:
                sprite_name = f"finger_{finger}_{radius_val}"
            elif note_name:
                clean_note = note_name.replace('#', 'sharp')
                sprite_name = f"note_{clean_note}_{radius_val}"
            else:
                return
        else:
            if not note_name:
                return
            clean_note = note_name.replace('#', 'sharp')
            sprite_name = f"note_{clean_note}_{radius_val}"

        texture = self._get_sprite_texture(sprite_name)
        if texture:
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
        texture = self._get_sprite_texture(sprite_name)

        if texture:
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

        if self.BARRE_AUTO_OFFSET:
            auto_offset = -height
        else:
            auto_offset = 0

        total_offset = auto_offset + self.BARRE_EXTRA_OFFSET

        new_x, new_y, scale = self._transform_coords(
            x, y,
            offset_x=0,
            offset_y=total_offset,
            invert_y=True
        )
        new_width = width * scale
        new_height = height * scale

        sprite_name = f"barre_{style}_{width}x{height}"
        texture = self._get_sprite_texture(sprite_name)

        if texture:
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