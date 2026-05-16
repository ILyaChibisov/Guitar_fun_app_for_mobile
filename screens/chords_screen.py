# screens/chords_screen.py
"""
Экран гитарных аккордов - с 4 карточками селекторами
ТОН, ТИП, АККОРД, ПОЗИЦИЯ в стиле админки
"""
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDIconButton, MDRaisedButton
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivy.metrics import dp, sp
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.uix.scrollview import ScrollView
from kivy.core.image import Image as CoreImage
from io import BytesIO
import pkgutil
import importlib
import re
import traceback

from config.theme import theme
from config.logger_config import screen_logger
from config.layout_config import layout_config
from screens.base_screen import BaseScreen
from screens.chord_renderer import ChordRenderer
from utils.notifications import notify

logger = screen_logger('Chords')

try:
    from data import load_asset_as_bytes

    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False


    def load_asset_as_bytes(name):
        return None

# Константы
TONALITIES = ['A', 'A#', 'B', 'C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#']

CHORD_TYPES = [
    "Major", "Minor", "7", "m7", "Dim", "Dim7", "Aug", "sus2",
    "sus4", "maj7", "7sus4", "maj9", "maj11", "maj13", "maj9#11", "maj13#11",
    "add9", "6add9", "maj7b5", "maj7#5", "m6", "m9", "m11", "m13",
    "madd9", "m6add9", "mmaj7", "mmaj9", "m7b5", "m7#5", "6", "9",
    "11", "13", "7b5", "7#5", "7b9", "7#9", "7(b5,b9)", "7(b5,#9)",
    "7(#5,b9)", "7(#5,#9)", "9b5", "9#5", "13#11", "13b9", "11b9",
    "sus2sus4", "-5", "5"
]

# Для отображения в описании
TYPE_DISPLAY = {
    "Major": "мажор",
    "Minor": "минор",
    "7": "септаккорд",
    "m7": "минорный септ",
    "maj7": "мажорный септ",
    "sus2": "sus2",
    "sus4": "sus4",
    "Dim": "уменьш",
    "Aug": "увелич",
    "Dim7": "ум.7",
    "m7b5": "m7-5",
}


class SelectorCard(MDCard):
    """Карточка селектора в стиле админки (без стрелки вниз)"""

    def __init__(self, title, value, on_left=None, on_right=None, on_center=None, **kwargs):
        super().__init__(**kwargs)
        self.title = title
        self.value = value
        self.on_left_callback = on_left
        self.on_right_callback = on_right
        self.on_center_callback = on_center

        self.orientation = 'vertical'
        self.size_hint = (1, 1)
        self.radius = [dp(16)]
        self.elevation = 2
        self.md_bg_color = [0, 0, 0, 0.15]
        self.line_color = [1, 1, 1, 0.1]
        self.line_width = 0.5
        self.padding = [dp(6), dp(8), dp(6), dp(8)]
        self.spacing = dp(4)
        self.ripple_behavior = True

        # Заголовок
        self.title_label = MDLabel(
            text=title,
            font_size=sp(10),
            halign="center",
            size_hint_y=None,
            height=dp(20),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.6],
            bold=True
        )

        # Строка со стрелками и значением
        self.row = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(40),
            spacing=dp(4)
        )

        # Левая стрелка
        self.left_btn = self._create_arrow_button('left_arrow_png', '◀')
        if on_left:
            self.left_btn.bind(on_release=on_left)

        # Значение (кликабельное)
        self.value_label = MDLabel(
            text=value,
            font_size=sp(16),
            halign="center",
            valign="middle",
            size_hint_x=1,
            theme_text_color="Custom",
            text_color=[0.46, 0.70, 0.71, 1],
            bold=True
        )

        # Правая стрелка
        self.right_btn = self._create_arrow_button('right_arrow_png', '▶')
        if on_right:
            self.right_btn.bind(on_release=on_right)

        self.row.add_widget(self.left_btn)
        self.row.add_widget(self.value_label)
        self.row.add_widget(self.right_btn)

        self.add_widget(self.title_label)
        self.add_widget(self.row)

        # Делаем центральную область кликабельной
        self.value_label.bind(on_touch_down=self._on_value_click)

    def _create_arrow_button(self, icon_name, fallback_text):
        from kivy.uix.behaviors import ButtonBehavior
        from kivy.uix.image import Image

        class ArrowButton(ButtonBehavior, Image):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.allow_stretch = True
                self.keep_ratio = True

        btn = ArrowButton(
            size_hint=(None, None),
            size=(dp(28), dp(28)),
            pos_hint={'center_y': 0.5}
        )

        if HAS_ASSETS:
            try:
                icon_data = load_asset_as_bytes(icon_name)
                if icon_data:
                    img = CoreImage(BytesIO(icon_data), ext="png")
                    btn.texture = img.texture
                    return btn
            except Exception as e:
                logger.error(f"Ошибка загрузки иконки {icon_name}: {e}")

        btn.text = fallback_text
        return btn

    def _on_value_click(self, instance, touch):
        if self.value_label.collide_point(*touch.pos):
            if self.on_center_callback:
                self.on_center_callback()
            return True
        return False

    def update_value(self, new_value):
        self.value = new_value
        self.value_label.text = new_value


class ModeToggleButton(MDCard):
    """Кнопка переключения режима (ПАЛЬЦЫ/НОТЫ)"""

    def __init__(self, text, icon, is_active=False, on_click=None, **kwargs):
        super().__init__(**kwargs)
        self.btn_text = text
        self.icon = icon
        self.is_active = is_active
        self.on_click_callback = on_click

        self.orientation = 'vertical'
        self.size_hint = (1, 1)
        self.radius = [dp(16)]
        self.elevation = 0
        self.padding = [dp(8), dp(8), dp(8), dp(8)]
        self.spacing = dp(4)
        self.ripple_behavior = True

        # Начальные значения
        self.md_bg_color = [0, 0, 0, 0.08]
        self.line_color = [1, 1, 1, 0.05]
        self.line_width = 0.5

        # Создаём виджеты
        self.icon_label = MDLabel(
            text=icon,
            font_size=sp(24),
            halign="center",
            size_hint_y=None,
            height=dp(36),
            theme_text_color="Custom"
        )

        self.text_label = MDLabel(
            text=text,
            font_size=sp(10),
            halign="center",
            size_hint_y=None,
            height=dp(20),
            theme_text_color="Custom",
            bold=True
        )

        self.add_widget(self.icon_label)
        self.add_widget(self.text_label)

        # Обновляем стиль
        self.update_style()

        self.bind(on_release=self._on_click)

    def update_style(self):
        if self.is_active:
            self.md_bg_color = [0.46, 0.70, 0.71, 0.3]
            self.line_color = [0.46, 0.70, 0.71, 0.5]
            self.line_width = 1
            self.icon_label.text_color = [0.46, 0.70, 0.71, 1]
            self.text_label.text_color = [0.46, 0.70, 0.71, 1]
        else:
            self.md_bg_color = [0, 0, 0, 0.08]
            self.line_color = [1, 1, 1, 0.05]
            self.line_width = 0.5
            self.icon_label.text_color = [1, 1, 1, 0.5]
            self.text_label.text_color = [1, 1, 1, 0.5]

    def set_active(self, active):
        self.is_active = active
        self.update_style()

    def _on_click(self, instance):
        if self.on_click_callback:
            self.on_click_callback(self.btn_text)


class ChordsScreen(BaseScreen):
    """Экран аккордов с 4 карточками-селекторами"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'chords'
        self.all_chords = []
        self.current_chord_module = None

        # Текущие значения
        self.current_tonality = "A"
        self.current_tonality_index = 0

        self.current_type = "Major"
        self.current_type_index = 0

        self.current_chord_name = "A"
        self.current_chord_data = None
        self.current_chord_index = 0
        self.available_chords = []

        self.current_position = 1
        self.current_variants = []
        self.current_variant_index = 0

        self.current_mode = "finger"

        # UI элементы
        self.tonality_card = None
        self.type_card = None
        self.chord_card = None
        self.position_card = None
        self.chord_name_label = None
        self.chord_desc_label = None
        self.chord_renderer = None
        self.finger_btn = None
        self.note_btn = None

        self.bg_image = None

        self.init_ui()
        self.load_background()
        self.scan_chords()

        logger.info('Экран аккордов создан (4 карточки)')

    def load_background(self):
        try:
            if HAS_ASSETS:
                asset_names = ["background_jpg", "background", "bg", "BACKGROUND_JPG"]
                bg_data = None
                for name in asset_names:
                    bg_data = load_asset_as_bytes(name)
                    if bg_data:
                        logger.info(f"Фон загружен из ассета: {name}")
                        break

                if bg_data:
                    img = CoreImage(BytesIO(bg_data), ext="jpg")
                    with self.canvas.before:
                        Color(1, 1, 1, 1)
                        self.bg_image = Rectangle(texture=img.texture, pos=self.pos, size=self.size)
                    self.bind(pos=self._update_bg, size=self._update_bg)
                    return
        except Exception as e:
            logger.error(f'Ошибка загрузки фона: {e}')

    def _update_bg(self, *args):
        if self.bg_image:
            self.bg_image.pos = self.pos
            self.bg_image.size = self.size

    def init_ui(self):
        # Основной контейнер
        main_layout = MDBoxLayout(
            orientation='vertical',
            spacing=dp(12),
            padding=[dp(12), 0, dp(12), 0]
        )

        # Верхний отступ
        top_padding = layout_config.get_top_padding()
        main_layout.add_widget(Widget(size_hint_y=None, height=top_padding))

        # ============ РЯД 1: ТОН и ТИП ============
        row1 = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(76),  # Уменьшено (было 90)
            spacing=dp(12)
        )

        self.tonality_card = SelectorCard(
            title="ТОН",
            value=self.current_tonality,
            on_left=self.prev_tonality,
            on_right=self.next_tonality,
            on_center=self.show_tonality_picker
        )

        self.type_card = SelectorCard(
            title="ТИП",
            value=self.current_type,
            on_left=self.prev_type,
            on_right=self.next_type,
            on_center=self.show_type_picker
        )

        row1.add_widget(self.tonality_card)
        row1.add_widget(self.type_card)
        main_layout.add_widget(row1)

        # ============ РЯД 2: АККОРД и ПОЗИЦИЯ ============
        row2 = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(76),  # Уменьшено (было 90)
            spacing=dp(12)
        )

        self.chord_card = SelectorCard(
            title="АККОРД",
            value=self.current_chord_name,
            on_left=self.prev_chord,
            on_right=self.next_chord,
            on_center=self.show_chord_picker
        )

        self.position_card = SelectorCard(
            title="ПОЗИЦИЯ",
            value=str(self.current_position),
            on_left=self.prev_position,
            on_right=self.next_position,
            on_center=self.show_position_picker
        )

        row2.add_widget(self.chord_card)
        row2.add_widget(self.position_card)
        main_layout.add_widget(row2)

        # ============ НАЗВАНИЕ И ОПИСАНИЕ АККОРДА ============
        info_card = MDCard(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(70),
            radius=[dp(16), dp(16), dp(16), dp(16)],
            md_bg_color=[0, 0, 0, 0.08],
            elevation=0,
            padding=[dp(16), dp(12), dp(16), dp(12)]
        )

        self.chord_name_label = MDLabel(
            text="A",
            font_size=sp(24),
            halign="center",
            bold=True,
            size_hint_y=None,
            height=dp(38),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.95]
        )

        self.chord_desc_label = MDLabel(
            text="",
            font_size=sp(12),
            halign="center",
            size_hint_y=None,
            height=dp(20),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.5]
        )

        info_card.add_widget(self.chord_name_label)
        info_card.add_widget(self.chord_desc_label)
        main_layout.add_widget(info_card)

        # ============ ГРИФ ============
        griff_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(260),
            padding=[dp(4), dp(4), dp(4), dp(4)]
        )

        self.chord_renderer = ChordRenderer()
        griff_container.add_widget(self.chord_renderer)
        main_layout.add_widget(griff_container)

        # ============ ПЕРЕКЛЮЧАТЕЛЬ ПАЛЬЦЫ/НОТЫ ============
        mode_row = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(70),
            spacing=dp(12),
            padding=[dp(20), dp(8), dp(20), dp(8)]
        )

        self.finger_btn = ModeToggleButton(
            text="ПАЛЬЦЫ",
            icon="🖐️",
            is_active=True,
            on_click=self.set_mode
        )

        self.note_btn = ModeToggleButton(
            text="НОТЫ",
            icon="🎵",
            is_active=False,
            on_click=self.set_mode
        )

        mode_row.add_widget(self.finger_btn)
        mode_row.add_widget(self.note_btn)
        main_layout.add_widget(mode_row)

        # Нижний отступ
        bottom_padding = dp(20)
        main_layout.add_widget(Widget(size_hint_y=None, height=bottom_padding))

        # Добавляем в ScrollView
        scroll = ScrollView(
            size_hint=(1, 1),
            do_scroll_x=False,
            bar_width=0,
            bar_color=[0, 0, 0, 0]
        )
        scroll.add_widget(main_layout)
        self.add_widget(scroll)

        # Загружаем фон грифа
        try:
            bg_data = load_asset_as_bytes("griff_png")
            if bg_data:
                img = CoreImage(BytesIO(bg_data), ext="png")
                if img and img.texture:
                    self.chord_renderer.set_background(img.texture)
        except Exception as e:
            logger.error(f"Ошибка загрузки фона грифа: {e}")

    # ============ МЕТОДЫ ДЛЯ ТОНАЛЬНОСТИ ============
    def prev_tonality(self, instance):
        self.current_tonality_index = (self.current_tonality_index - 1) % len(TONALITIES)
        self.current_tonality = TONALITIES[self.current_tonality_index]
        self.tonality_card.update_value(self.current_tonality)
        self.update_available_chords()

    def next_tonality(self, instance):
        self.current_tonality_index = (self.current_tonality_index + 1) % len(TONALITIES)
        self.current_tonality = TONALITIES[self.current_tonality_index]
        self.tonality_card.update_value(self.current_tonality)
        self.update_available_chords()

    def show_tonality_picker(self):
        content = MDBoxLayout(
            orientation='vertical',
            spacing=dp(8),
            padding=dp(16),
            size_hint_y=None,
            adaptive_height=True
        )

        grid = MDBoxLayout(
            orientation='vertical',
            spacing=dp(8),
            size_hint_y=None,
            adaptive_height=True
        )

        for row_idx in range(3):
            row = MDBoxLayout(
                orientation='horizontal',
                spacing=dp(8),
                size_hint_y=None,
                height=dp(48)
            )
            for col_idx in range(4):
                idx = row_idx * 4 + col_idx
                if idx < len(TONALITIES):
                    ton = TONALITIES[idx]
                    btn = MDRaisedButton(
                        text=ton,
                        size_hint=(1, 1),
                        md_bg_color=[0.46, 0.70, 0.71, 1] if ton == self.current_tonality else [0.2, 0.2, 0.2, 0.8],
                        on_release=lambda x, t=ton: self._select_tonality(t)
                    )
                    row.add_widget(btn)
            grid.add_widget(row)

        content.add_widget(grid)

        dialog = MDDialog(
            title="Выберите тональность",
            type="custom",
            content_cls=content,
            buttons=[MDRaisedButton(text="Закрыть", on_release=lambda x: dialog.dismiss())]
        )
        dialog.open()
        self.tonality_dialog = dialog

    def _select_tonality(self, tonality):
        self.current_tonality = tonality
        self.current_tonality_index = TONALITIES.index(tonality)
        self.tonality_card.update_value(self.current_tonality)
        self.update_available_chords()
        if hasattr(self, 'tonality_dialog'):
            self.tonality_dialog.dismiss()

    # ============ МЕТОДЫ ДЛЯ ТИПА ============
    def prev_type(self, instance):
        self.current_type_index = (self.current_type_index - 1) % len(CHORD_TYPES)
        self.current_type = CHORD_TYPES[self.current_type_index]
        self.type_card.update_value(self.current_type)
        self.update_available_chords()

    def next_type(self, instance):
        self.current_type_index = (self.current_type_index + 1) % len(CHORD_TYPES)
        self.current_type = CHORD_TYPES[self.current_type_index]
        self.type_card.update_value(self.current_type)
        self.update_available_chords()

    def show_type_picker(self):
        content = MDBoxLayout(
            orientation='vertical',
            spacing=dp(8),
            padding=dp(16),
            size_hint_y=None,
            adaptive_height=True
        )

        scroll = ScrollView(size_hint=(1, None), height=dp(300))
        grid = MDBoxLayout(
            orientation='vertical',
            spacing=dp(8),
            size_hint_y=None,
            adaptive_height=True
        )

        row = MDBoxLayout(orientation='horizontal', spacing=dp(8), size_hint_y=None, height=dp(44))
        for i, chord_type in enumerate(CHORD_TYPES):
            btn = MDRaisedButton(
                text=chord_type,
                size_hint=(1, 1),
                font_size=sp(10),
                md_bg_color=[0.46, 0.70, 0.71, 1] if chord_type == self.current_type else [0.2, 0.2, 0.2, 0.8],
                on_release=lambda x, t=chord_type: self._select_type(t)
            )
            row.add_widget(btn)
            if (i + 1) % 3 == 0:
                grid.add_widget(row)
                row = MDBoxLayout(orientation='horizontal', spacing=dp(8), size_hint_y=None, height=dp(44))

        if row.children:
            grid.add_widget(row)

        scroll.add_widget(grid)
        content.add_widget(scroll)

        dialog = MDDialog(
            title="Выберите тип аккорда",
            type="custom",
            content_cls=content,
            buttons=[MDRaisedButton(text="Закрыть", on_release=lambda x: dialog.dismiss())]
        )
        dialog.open()
        self.type_dialog = dialog

    def _select_type(self, chord_type):
        self.current_type = chord_type
        self.current_type_index = CHORD_TYPES.index(chord_type)
        self.type_card.update_value(self.current_type)
        self.update_available_chords()
        if hasattr(self, 'type_dialog'):
            self.type_dialog.dismiss()

    # ============ МЕТОДЫ ДЛЯ АККОРДА ============
    def prev_chord(self, instance):
        if not self.available_chords:
            return
        self.current_chord_index = (self.current_chord_index - 1) % len(self.available_chords)
        self.current_chord_name = self.available_chords[self.current_chord_index]
        self.chord_card.update_value(self.current_chord_name)
        self.load_current_variant()

    def next_chord(self, instance):
        if not self.available_chords:
            return
        self.current_chord_index = (self.current_chord_index + 1) % len(self.available_chords)
        self.current_chord_name = self.available_chords[self.current_chord_index]
        self.chord_card.update_value(self.current_chord_name)
        self.load_current_variant()

    def show_chord_picker(self):
        if not self.available_chords:
            notify.info("Нет доступных аккордов")
            return

        content = MDBoxLayout(
            orientation='vertical',
            spacing=dp(8),
            padding=dp(16),
            size_hint_y=None,
            adaptive_height=True
        )

        scroll = ScrollView(size_hint=(1, None), height=dp(250))
        grid = MDBoxLayout(
            orientation='vertical',
            spacing=dp(8),
            size_hint_y=None,
            adaptive_height=True
        )

        row = MDBoxLayout(orientation='horizontal', spacing=dp(8), size_hint_y=None, height=dp(48))
        for i, chord_name in enumerate(self.available_chords):
            btn = MDRaisedButton(
                text=chord_name,
                size_hint=(1, 1),
                md_bg_color=[0.46, 0.70, 0.71, 1] if chord_name == self.current_chord_name else [0.2, 0.2, 0.2, 0.8],
                on_release=lambda x, c=chord_name: self._select_chord(c)
            )
            row.add_widget(btn)
            if (i + 1) % 4 == 0:
                grid.add_widget(row)
                row = MDBoxLayout(orientation='horizontal', spacing=dp(8), size_hint_y=None, height=dp(48))

        if row.children:
            grid.add_widget(row)

        scroll.add_widget(grid)
        content.add_widget(scroll)

        dialog = MDDialog(
            title="Выберите аккорд",
            type="custom",
            content_cls=content,
            buttons=[MDRaisedButton(text="Закрыть", on_release=lambda x: dialog.dismiss())]
        )
        dialog.open()
        self.chord_dialog = dialog

    def _select_chord(self, chord_name):
        self.current_chord_name = chord_name
        self.current_chord_index = self.available_chords.index(chord_name)
        self.chord_card.update_value(self.current_chord_name)
        self.load_current_variant()
        if hasattr(self, 'chord_dialog'):
            self.chord_dialog.dismiss()

    # ============ МЕТОДЫ ДЛЯ ПОЗИЦИИ ============
    def prev_position(self, instance):
        if not self.current_variants:
            return
        self.current_variant_index = (self.current_variant_index - 1) % len(self.current_variants)
        self.current_position = self.current_variant_index + 1
        self.position_card.update_value(str(self.current_position))
        self.load_current_variant()

    def next_position(self, instance):
        if not self.current_variants:
            return
        self.current_variant_index = (self.current_variant_index + 1) % len(self.current_variants)
        self.current_position = self.current_variant_index + 1
        self.position_card.update_value(str(self.current_position))
        self.load_current_variant()

    def show_position_picker(self):
        if not self.current_variants:
            notify.info("Нет доступных позиций")
            return

        content = MDBoxLayout(
            orientation='vertical',
            spacing=dp(8),
            padding=dp(16),
            size_hint_y=None,
            height=dp(150)
        )

        grid = MDBoxLayout(
            orientation='vertical',
            spacing=dp(8),
            size_hint_y=None,
            adaptive_height=True
        )

        row = MDBoxLayout(orientation='horizontal', spacing=dp(8), size_hint_y=None, height=dp(48))
        for i in range(len(self.current_variants)):
            btn = MDRaisedButton(
                text=f"Pos {i + 1}",
                size_hint=(1, 1),
                md_bg_color=[0.46, 0.70, 0.71, 1] if i == self.current_variant_index else [0.2, 0.2, 0.2, 0.8],
                on_release=lambda x, p=i: self._select_position(p)
            )
            row.add_widget(btn)
            if (i + 1) % 4 == 0:
                grid.add_widget(row)
                row = MDBoxLayout(orientation='horizontal', spacing=dp(8), size_hint_y=None, height=dp(48))

        if row.children:
            grid.add_widget(row)

        content.add_widget(grid)

        dialog = MDDialog(
            title="Выберите позицию",
            type="custom",
            content_cls=content,
            buttons=[MDRaisedButton(text="Закрыть", on_release=lambda x: dialog.dismiss())]
        )
        dialog.open()
        self.position_dialog = dialog

    def _select_position(self, position_index):
        self.current_variant_index = position_index
        self.current_position = position_index + 1
        self.position_card.update_value(str(self.current_position))
        self.load_current_variant()
        if hasattr(self, 'position_dialog'):
            self.position_dialog.dismiss()

    # ============ РЕЖИМ ОТОБРАЖЕНИЯ ============
    def set_mode(self, mode):
        if mode == "ПАЛЬЦЫ":
            self.current_mode = "finger"
            self.finger_btn.set_active(True)
            self.note_btn.set_active(False)
        else:
            self.current_mode = "note"
            self.finger_btn.set_active(False)
            self.note_btn.set_active(True)

        if self.current_chord_module and self.chord_renderer:
            self.chord_renderer.set_mode(self.current_mode)

    # ============ ЗАГРУЗКА АККОРДОВ ============
    def scan_chords(self):
        print("\n" + "=" * 60)
        print("SCAN_CHORDS: Начинаю сканирование аккордов")
        self.all_chords = []
        try:
            import chords
            self._scan_module_recursive(chords, 'chords')
        except ImportError as e:
            print(f"❌ Пакет chords не найден: {e}")
        except Exception as e:
            print(f"❌ Непредвиденная ошибка: {e}")
            traceback.print_exc()
        print(f"РЕЗУЛЬТАТ: Загружено {len(self.all_chords)} аккордов")
        self.update_available_chords()

    def _scan_module_recursive(self, module, module_path):
        try:
            if hasattr(module, '__path__'):
                for module_info in pkgutil.iter_modules(module.__path__, f"{module_path}."):
                    try:
                        sub_module = importlib.import_module(module_info.name)
                        if hasattr(sub_module, '__path__'):
                            self._scan_module_recursive(sub_module, module_info.name)
                        else:
                            self._load_chord_module(sub_module, module_info.name)
                    except Exception as e:
                        print(f"    ❌ Ошибка импорта {module_info.name}: {e}")
        except Exception as e:
            print(f"  ❌ Ошибка сканирования {module_path}: {e}")

    def _load_chord_module(self, module, module_name):
        try:
            metadata = getattr(module, 'METADATA', {})
            chord_name = metadata.get('name', module_name.split('.')[-1])
            chord_name = chord_name.replace('!', '|').replace('$', '/')
            path_parts = module_name.split('.')
            chord_type = metadata.get('type', '')
            if not chord_type and len(path_parts) >= 2:
                chord_type = path_parts[-2]
            variant_match = re.search(r'_(\d+)$', path_parts[-1])
            variant_num = int(variant_match.group(1)) if variant_match else metadata.get('variant', 1)
            short_name = chord_name.split('|')[0].replace('$', '/')
            chord_data = {
                'id': f"{short_name}_{chord_type}_v{variant_num}",
                'name': chord_name,
                'short_name': short_name,
                'variant': variant_num,
                'type': chord_type,
                'description': metadata.get('description', ''),
                'module': module,
                'path': module_name
            }
            self.all_chords.append(chord_data)
        except Exception as e:
            print(f"    ❌ Ошибка загрузки модуля {module_name}: {e}")

    def update_available_chords(self):
        """Обновляет список доступных аккордов по текущим ТОН и ТИП"""
        filtered = []
        for chord in self.all_chords:
            tonality = self.extract_tonality(chord['name'])
            if tonality != self.current_tonality:
                continue
            chord_types = chord['type'].split('|') if chord['type'] else []
            if self.current_type not in chord_types and self.current_type != chord.get('type', ''):
                continue
            filtered.append(chord)

        # Группируем по короткому имени
        chords_by_name = {}
        for chord in filtered:
            name = chord['short_name']
            if name not in chords_by_name:
                chords_by_name[name] = []
            chords_by_name[name].append(chord)

        # Сортируем
        self.available_chords = sorted(chords_by_name.keys())

        if self.available_chords:
            # Находим текущий аккорд в новом списке
            if self.current_chord_name not in self.available_chords:
                self.current_chord_index = 0
                self.current_chord_name = self.available_chords[0]
                self.chord_card.update_value(self.current_chord_name)

            # Загружаем данные для текущего аккорда
            chord_data = chords_by_name.get(self.current_chord_name)
            if chord_data:
                self.load_chord_variants(chord_data)
        else:
            self.available_chords = []
            self.current_variants = []
            self.chord_name_label.text = "Нет аккордов"
            self.chord_desc_label.text = ""

    def extract_tonality(self, chord_name):
        if not chord_name:
            return ""
        match = re.match(r'^([A-H][#b]?)', chord_name)
        return match.group(1) if match else (chord_name[0] if chord_name else "")

    def load_chord_variants(self, variants):
        if not variants:
            return
        variants.sort(key=lambda x: x['variant'])
        self.current_variants = variants
        self.current_variant_index = 0
        self.current_position = 1
        self.position_card.update_value("1")
        self.load_current_variant()

    def load_current_variant(self):
        if not self.current_variants:
            return
        variant = self.current_variants[self.current_variant_index]
        self.current_chord_module = variant['module']

        # Название аккорда (короткое имя)
        self.chord_name_label.text = self.current_chord_name

        # Описание из METADATA
        description = variant.get('description', '')
        if description:
            description = description.replace('!', ' | ').replace('$', '/')
        else:
            description = TYPE_DISPLAY.get(self.current_type, self.current_type)

        self.chord_desc_label.text = description

        # Обновляем гриф
        if self.chord_renderer:
            self.chord_renderer.load_chord(self.current_chord_module)
            self.chord_renderer.set_mode(self.current_mode)

    def load_chord_by_name(self, chord_name):
        """Загружает аккорд по имени (из поиска)"""
        for chord in self.all_chords:
            if chord['short_name'].lower() == chord_name.lower():
                tonality = self.extract_tonality(chord['name'])
                if tonality in TONALITIES:
                    self.current_tonality = tonality
                    self.current_tonality_index = TONALITIES.index(tonality)
                    self.tonality_card.update_value(self.current_tonality)
                    self.update_available_chords()

                    if self.current_chord_name != chord_name:
                        if chord_name in self.available_chords:
                            self.current_chord_name = chord_name
                            self.current_chord_index = self.available_chords.index(chord_name)
                            self.chord_card.update_value(self.current_chord_name)

                            chords_by_name = {}
                            for ch in self.all_chords:
                                name = ch['short_name']
                                if name not in chords_by_name:
                                    chords_by_name[name] = []
                                chords_by_name[name].append(ch)

                            chord_data = chords_by_name.get(chord_name)
                            if chord_data:
                                self.load_chord_variants(chord_data)
                    break