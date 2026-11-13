# chord_utils/renderer.py
"""
Рендерер аккордов - с поддержкой цветных ладов.

ОПТИМИЗАЦИЯ:
  - Спрайты разбиты на 3 независимых слоя: fret_layer, barre_layer, note_layer.
    Это позволяет пересобирать только ту часть, которая реально изменилась:
      * set_fret_color → только fret_layer
      * set_mode       → только barre_layer + note_layer
      * load_chord     → все три
  - _update_positions() больше НЕ пересоздаёт спрайты: только пересчитывает
    pos/size уже существующих виджетов по сохранённым метаданным.
    Раньше bind(size/pos) вызывал _create_sprites на каждом кадре layout —
    это была главная причина лагов при свайпе.
  - set_mode / set_fret_color — no-op, если значение не изменилось.
  - load_chord — no-op, если модуль тот же (по id + имя).
"""
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.image import Image
from kivy.logger import Logger
from chord_utils.sprites import sprite_loader


class ChordRenderer(RelativeLayout):
    # Реальный размер картинки грифа
    IMAGE_WIDTH = 1376
    IMAGE_HEIGHT = 830

    # Цвет ладов: "black" или "white"
    FRET_COLOR = "white"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_module = None
        self.current_mode = "finger"
        self.background_texture = None
        self._last_module_id = None  # для no-op load_chord

        # ===== Слои =====
        # griff_image — фон (создаётся один раз, меняется только texture)
        self.griff_image = Image(
            allow_stretch=True,
            keep_ratio=True,
            size_hint=(1, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        self.add_widget(self.griff_image)

        # Слой ладов (цифры под грифом) — меняется только при смене цвета/аккорда
        self.fret_layer = RelativeLayout(size_hint=(1, 1))
        self.add_widget(self.fret_layer)

        # Слой баре — зависит от mode + аккорда
        self.barre_layer = RelativeLayout(size_hint=(1, 1))
        self.add_widget(self.barre_layer)

        # Слой нот/пальцев/X — зависит от mode + аккорда
        self.note_layer = RelativeLayout(size_hint=(1, 1))
        self.add_widget(self.note_layer)

        # Метаданные спрайтов для быстрого _update_positions.
        # Элемент: dict(layer, kind, widget, x, y, ...)
        # kind ∈ {'fret', 'note', 'x', 'barre'}
        self._sprites_meta = []

        self.bind(size=self._update_positions)
        self.bind(pos=self._update_positions)

    # ============================================================
    # Публичный API
    # ============================================================

    def set_background(self, texture):
        """Устанавливает фон грифа"""
        if texture:
            self.griff_image.texture = texture
            self.background_texture = texture
            Logger.info("ChordRenderer: Фон грифа установлен")
        else:
            Logger.error("ChordRenderer: Получен пустой texture для фона")

    def set_fret_color(self, color):
        """Устанавливает цвет ладов. No-op, если цвет не изменился."""
        if color not in ("black", "white"):
            Logger.warning(f"ChordRenderer: Неизвестный цвет {color}, оставляем {self.FRET_COLOR}")
            return
        if color == self.FRET_COLOR:
            return  # no-op
        self.FRET_COLOR = color
        Logger.info(f"ChordRenderer: Цвет ладов изменён на {color}")
        # Пересобираем только лады
        if self.current_module:
            self._build_fret_layer()

    def load_chord(self, chord_module):
        """Загружает модуль аккорда для отображения."""
        if not chord_module:
            Logger.error("ChordRenderer: load_chord получил None")
            return
        # no-op, если тот же модуль
        module_key = (id(chord_module), getattr(chord_module, '__name__', ''))
        if module_key == self._last_module_id and self.current_module is not None:
            return
        self._last_module_id = module_key
        self.current_module = chord_module
        Logger.info(f"ChordRenderer: Загрузка аккорда из модуля {chord_module.__name__}")
        self._rebuild_all_layers()

    def set_mode(self, mode):
        """Устанавливает режим: finger / note. No-op, если не изменился."""
        if mode == self.current_mode:
            return
        self.current_mode = mode
        Logger.info(f"ChordRenderer: Режим изменён на {mode}")
        if self.current_module:
            # Лады не зависят от mode — пересобираем только ноты + баре
            self._build_barre_layer()
            self._build_note_layer()

    # ============================================================
    # Внутренняя сборка слоёв
    # ============================================================

    def _rebuild_all_layers(self):
        """Полная пересборка: лады + баре + ноты."""
        self._build_fret_layer()
        self._build_barre_layer()
        self._build_note_layer()

    def _build_fret_layer(self):
        """Собирает слой ладов (цифры). Зависит от FRETS + FRET_COLOR."""
        self.fret_layer.clear_widgets()
        self._clear_meta_for_layer(self.fret_layer)

        frets = getattr(self.current_module, 'FRETS', {}) if self.current_module else {}
        for fret_id, fret_data in frets.items():
            self._add_fret_sprite(fret_data)

    def _build_barre_layer(self):
        """Собирает слой баре. Зависит от mode + BARRES + selected."""
        self.barre_layer.clear_widgets()
        self._clear_meta_for_layer(self.barre_layer)

        if not self.current_module:
            return
        barres = getattr(self.current_module, 'BARRES', {})
        if self.current_mode == "finger":
            selected = getattr(self.current_module, 'SELECTED_FINGER', [])
        else:
            selected = getattr(self.current_module, 'SELECTED_NOTE', [])

        for key in selected:
            if 'BAR' in key and key in barres:
                self._add_barre_sprite(barres[key])

    def _build_note_layer(self):
        """Собирает слой нот/пальцев/X. Зависит от mode + NOTES/OPEN_NOTES + selected."""
        self.note_layer.clear_widgets()
        self._clear_meta_for_layer(self.note_layer)

        if not self.current_module:
            return
        notes = getattr(self.current_module, 'NOTES', {})
        open_notes = getattr(self.current_module, 'OPEN_NOTES', {})

        if self.current_mode == "finger":
            selected = getattr(self.current_module, 'SELECTED_FINGER', [])
        else:
            selected = getattr(self.current_module, 'SELECTED_NOTE', [])

        for key in selected:
            if 'BAR' in key:
                continue
            elif key in notes:
                self._add_note_sprite(notes[key])
            elif key in open_notes:
                self._add_x_sprite(open_notes[key])

    def _clear_meta_for_layer(self, layer):
        self._sprites_meta = [m for m in self._sprites_meta if m['layer'] is not layer]

    # ============================================================
    # Создание спрайтов
    # ============================================================

    def _add_fret_sprite(self, fret_data):
        """Добавляет спрайт лада с текущим цветом"""
        x = fret_data.get('x', 0)
        y = fret_data.get('y', 0)
        symbol = str(fret_data.get('symbol', ''))
        size = fret_data.get('size', 30)

        if not symbol:
            return

        texture = sprite_loader.get_fret_sprite(symbol, size, self.FRET_COLOR)
        if not texture:
            return

        new_x, new_y, scale = self._transform_coords(
            x, y, offset_x=0, offset_y=770, invert_y=False
        )
        new_size = size * scale

        sprite = Image(
            texture=texture,
            size_hint=(None, None),
            size=(new_size * 2, new_size),
            pos=(new_x - new_size, new_y - new_size / 2),
            allow_stretch=True,
        )
        self.fret_layer.add_widget(sprite)
        self._sprites_meta.append({
            'layer': self.fret_layer,
            'kind': 'fret',
            'widget': sprite,
            'x': x, 'y': y, 'size': size,
        })

    def _add_note_sprite(self, note_data):
        """Добавляет спрайт ноты или пальца"""
        x = note_data.get('x', 0)
        y = note_data.get('y', 0)
        radius = note_data.get('radius', 50)
        note_name = note_data.get('note_name', '')
        finger = note_data.get('finger', '')

        texture = None
        if self.current_mode == "finger" and finger:
            texture = sprite_loader.get_finger_sprite(finger, radius)
        elif note_name:
            texture = sprite_loader.get_note_sprite(note_name, radius)
        if not texture:
            return

        new_x, new_y, scale = self._transform_coords(
            x, y, offset_x=0, offset_y=0, invert_y=True
        )
        new_radius = max(radius * scale, 6)

        sprite = Image(
            texture=texture,
            size_hint=(None, None),
            size=(new_radius * 2, new_radius * 2),
            pos=(new_x - new_radius, new_y - new_radius),
            allow_stretch=True,
        )
        self.note_layer.add_widget(sprite)
        self._sprites_meta.append({
            'layer': self.note_layer,
            'kind': 'note',
            'widget': sprite,
            'x': x, 'y': y, 'radius': radius,
        })

    def _add_x_sprite(self, note_data):
        """Добавляет спрайт X (глушимые струны)"""
        x = note_data.get('x', 0)
        y = note_data.get('y', 0)
        radius = note_data.get('radius', 50)

        texture = sprite_loader.get_x_sprite(radius)
        if not texture:
            return

        new_x, new_y, scale = self._transform_coords(
            x, y, offset_x=0, offset_y=0, invert_y=True
        )
        new_radius = max(radius * scale, 6)

        sprite = Image(
            texture=texture,
            size_hint=(None, None),
            size=(new_radius * 2, new_radius * 2),
            pos=(new_x - new_radius, new_y - new_radius),
            allow_stretch=True,
        )
        self.note_layer.add_widget(sprite)
        self._sprites_meta.append({
            'layer': self.note_layer,
            'kind': 'x',
            'widget': sprite,
            'x': x, 'y': y, 'radius': radius,
        })

    def _add_barre_sprite(self, barre_data):
        """Добавляет спрайт баре"""
        x = barre_data.get('x', 0)
        y = barre_data.get('y', 0)
        width = barre_data.get('width', 100)
        height = barre_data.get('height', 20)
        style = barre_data.get('style', 'wood')

        texture = sprite_loader.get_barre_sprite(style, width, height)
        if not texture:
            return

        total_offset = -height
        new_x, new_y, scale = self._transform_coords(
            x, y, offset_x=0, offset_y=total_offset, invert_y=True
        )
        new_width = width * scale
        new_height = height * scale

        sprite = Image(
            texture=texture,
            size_hint=(None, None),
            size=(new_width, new_height),
            pos=(new_x, new_y),
            allow_stretch=True,
        )
        self.barre_layer.add_widget(sprite)
        self._sprites_meta.append({
            'layer': self.barre_layer,
            'kind': 'barre',
            'widget': sprite,
            'x': x, 'y': y, 'width': width, 'height': height,
        })

    # ============================================================
    # Обновление позиций (БЕЗ пересоздания спрайтов)
    # ============================================================

    def _update_positions(self, *args):
        """
        Обновляет pos/size у уже существующих спрайтов.
        НЕ вызывает _create_sprites — это было главной причиной лагов.
        """
        if not self._sprites_meta:
            return
        if self.width <= 0 or self.height <= 0:
            return

        for meta in self._sprites_meta:
            widget = meta.get('widget')
            if widget is None or widget.parent is None:
                continue

            kind = meta['kind']
            x = meta['x']
            y = meta['y']

            if kind == 'fret':
                size = meta['size']
                new_x, new_y, scale = self._transform_coords(
                    x, y, offset_x=0, offset_y=770, invert_y=False
                )
                new_size = size * scale
                widget.size = (new_size * 2, new_size)
                widget.pos = (new_x - new_size, new_y - new_size / 2)

            elif kind in ('note', 'x'):
                radius = meta['radius']
                new_x, new_y, scale = self._transform_coords(
                    x, y, offset_x=0, offset_y=0, invert_y=True
                )
                new_radius = max(radius * scale, 6)
                widget.size = (new_radius * 2, new_radius * 2)
                widget.pos = (new_x - new_radius, new_y - new_radius)

            elif kind == 'barre':
                width = meta['width']
                height = meta['height']
                total_offset = -height
                new_x, new_y, scale = self._transform_coords(
                    x, y, offset_x=0, offset_y=total_offset, invert_y=True
                )
                widget.size = (width * scale, height * scale)
                widget.pos = (new_x, new_y)

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