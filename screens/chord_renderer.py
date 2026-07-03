# screens/chord_renderer.py
"""
Рендерер аккордов - с поддержкой цветных ладов
"""
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.image import Image
from kivy.logger import Logger
from chord_sprites import sprite_loader


class ChordRenderer(RelativeLayout):
    # Реальный размер картинки грифа
    IMAGE_WIDTH = 1376
    IMAGE_HEIGHT = 830

    # Цвет ладов: "black" или "white"
    FRET_COLOR = "white"  # ← ВРЕМЕННО БЕЛЫЙ, ПОТОМ БУДЕТ МЕНЯТЬСЯ

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_module = None
        self.current_mode = "finger"
        self.background_texture = None

        # Изображение грифа
        self.griff_image = Image(
            allow_stretch=True,
            keep_ratio=True,
            size_hint=(1, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        self.add_widget(self.griff_image)

        # Слой для спрайтов
        self.sprite_layer = RelativeLayout(size_hint=(1, 1))
        self.add_widget(self.sprite_layer)

        self.bind(size=self._update_positions)
        self.bind(pos=self._update_positions)

    def set_background(self, texture):
        """Устанавливает фон грифа"""
        if texture:
            self.griff_image.texture = texture
            Logger.info("ChordRenderer: Фон грифа установлен")
        else:
            Logger.error("ChordRenderer: Получен пустой texture для фона")

    def set_fret_color(self, color):
        """
        Устанавливает цвет ладов.

        Args:
            color: "black" или "white"
        """
        if color in ("black", "white"):
            self.FRET_COLOR = color
            Logger.info(f"ChordRenderer: Цвет ладов изменён на {color}")
            if self.current_module:
                self._create_sprites()
        else:
            Logger.warning(f"ChordRenderer: Неизвестный цвет {color}, оставляем {self.FRET_COLOR}")

    def load_chord(self, chord_module):
        """Загружает модуль аккорда для отображения"""
        if not chord_module:
            Logger.error("ChordRenderer: load_chord получил None")
            return

        self.current_module = chord_module
        Logger.info(f"ChordRenderer: Загрузка аккорда из модуля {chord_module.__name__}")
        self._create_sprites()

    def set_mode(self, mode):
        """Устанавливает режим отображения: finger или note"""
        self.current_mode = mode
        Logger.info(f"ChordRenderer: Режим изменён на {mode}")
        if self.current_module:
            self._create_sprites()

    def _transform_coords(self, x, y, offset_x=0, offset_y=0, invert_y=False):
        """Преобразует координаты из исходного размера в текущий"""
        if self.width <= 0 or self.height <= 0:
            return x, y, 1.0

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
        """Создает все спрайты для текущего аккорда"""
        if not self.current_module:
            Logger.warning("ChordRenderer: current_module is None")
            return

        self.sprite_layer.clear_widgets()

        # Получаем данные из модуля
        notes = getattr(self.current_module, 'NOTES', {})
        open_notes = getattr(self.current_module, 'OPEN_NOTES', {})
        barres = getattr(self.current_module, 'BARRES', {})
        frets = getattr(self.current_module, 'FRETS', {})

        Logger.info(f"ChordRenderer: Данные модуля - NOTES={len(notes)}, FRETS={len(frets)}, BARRES={len(barres)}")

        # Определяем, что рисовать
        if self.current_mode == "finger":
            selected = getattr(self.current_module, 'SELECTED_FINGER', [])
            Logger.info(f"ChordRenderer: Режим finger, выбрано {len(selected)} элементов")
        else:
            selected = getattr(self.current_module, 'SELECTED_NOTE', [])
            Logger.info(f"ChordRenderer: Режим note, выбрано {len(selected)} элементов")

        # Рисуем лады (ВСЕГДА белые/чёрные в зависимости от темы)
        for fret_id, fret_data in frets.items():
            self._add_fret_sprite(fret_data)

        # Рисуем баре
        for key in selected:
            if 'BAR' in key and key in barres:
                self._add_barre_sprite(barres[key])

        # Рисуем ноты/пальцы
        for key in selected:
            if 'BAR' in key:
                continue
            elif key in notes:
                self._add_note_sprite(notes[key])
            elif key in open_notes:
                self._add_x_sprite(open_notes[key])

    def _add_fret_sprite(self, fret_data):
        """Добавляет спрайт лада с текущим цветом"""
        x = fret_data.get('x', 0)
        y = fret_data.get('y', 0)
        symbol = str(fret_data.get('symbol', ''))
        size = fret_data.get('size', 30)

        if not symbol:
            return

        new_x, new_y, scale = self._transform_coords(x, y, offset_x=0, offset_y=790, invert_y=False)
        new_size = size * scale

        # Загружаем спрайт с нужным цветом
        texture = sprite_loader.get_fret_sprite(symbol, size, self.FRET_COLOR)
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
        """Добавляет спрайт ноты или пальца"""
        x = note_data.get('x', 0)
        y = note_data.get('y', 0)
        radius = note_data.get('radius', 50)
        note_name = note_data.get('note_name', '')
        finger = note_data.get('finger', '')

        new_x, new_y, scale = self._transform_coords(x, y, offset_x=0, offset_y=0, invert_y=True)
        new_radius = max(radius * scale, 6)

        texture = None
        if self.current_mode == "finger" and finger:
            texture = sprite_loader.get_finger_sprite(finger, radius)
        elif note_name:
            texture = sprite_loader.get_note_sprite(note_name, radius)

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
        """Добавляет спрайт X (глушимые струны)"""
        x = note_data.get('x', 0)
        y = note_data.get('y', 0)
        radius = note_data.get('radius', 50)

        new_x, new_y, scale = self._transform_coords(x, y, offset_x=0, offset_y=0, invert_y=True)
        new_radius = max(radius * scale, 6)

        texture = sprite_loader.get_x_sprite(radius)
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
        """Добавляет спрайт баре"""
        x = barre_data.get('x', 0)
        y = barre_data.get('y', 0)
        width = barre_data.get('width', 100)
        height = barre_data.get('height', 20)
        style = barre_data.get('style', 'wood')

        # Корректировка для баре
        total_offset = -height

        new_x, new_y, scale = self._transform_coords(x, y, offset_x=0, offset_y=total_offset, invert_y=True)
        new_width = width * scale
        new_height = height * scale

        texture = sprite_loader.get_barre_sprite(style, width, height)
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
        """Обновляет позиции при изменении размера"""
        if self.current_module:
            self._create_sprites()