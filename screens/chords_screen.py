# screens/chords_screen.py
"""
Экран гитарных аккордов
"""
from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.textfield import MDTextField
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.button import MDIconButton
from kivymd.uix.card import MDCard
from kivy.metrics import dp, sp
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.utils import rgba
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import Image
from kivy.core.image import Image as CoreImage
from io import BytesIO
import os

from config.theme import theme
from config.logger_config import screen_logger
from utils.notifications import notify
from screens.chord_renderer import ChordRenderer

import importlib.util
import re

logger = screen_logger('Chords')

# Попытка импорта ассетов
try:
    from data import load_asset_as_bytes

    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False


    def load_asset_as_bytes(name):
        return None


    logger.warning("Модуль data не найден")

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


class TitleCard(MDCard):
    """Единый стиль для заголовка (Тон, Тип, Аккорд, Позиция)"""

    def __init__(self, title, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_x = None
        self.width = dp(60)
        self.height = dp(36)
        self.radius = [dp(8)]
        self.md_bg_color = "#E8DCC8"  # Бежевый
        self.elevation = 0
        self.padding = [dp(4), dp(2), dp(4), dp(2)]

        self.title_label = MDLabel(
            text=title,
            font_size=sp(12),
            halign="center",
            valign="middle",
            theme_text_color="Custom",
            text_color=theme.TEXT_PRIMARY,
            bold=True
        )
        self.add_widget(self.title_label)


# screens/chords_screen.py - обновленный класс TonalityRow

class TonalityButton(ButtonBehavior, MDBoxLayout):
    """Кнопка тональности (компактная)"""

    def __init__(self, text, is_active=False, on_press_callback=None, **kwargs):
        super().__init__(**kwargs)
        self.btn_text = text
        self.on_press_callback = on_press_callback
        self.size_hint = (1, 1)  # Растягивается равномерно
        self.padding = [dp(2), dp(2), dp(2), dp(2)]

        self.label = MDLabel(
            text=text,
            font_size=sp(12),
            halign="center",
            valign="middle",
            theme_text_color="Custom"
        )
        self.add_widget(self.label)
        self.set_active(is_active)
        self.bind(on_release=self._on_press)

        self.bg_color = [0, 0, 0, 0]
        with self.canvas.before:
            Color(*self.bg_color)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

    def _update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def set_active(self, is_active):
        if is_active:
            self.label.text_color = [1, 1, 1, 1]
            self.label.bold = True
            self.bg_color = [0.46, 0.70, 0.71, 1]  # Твой мягкий зелёный
        else:
            self.label.text_color = [0, 0, 0, 1]  # Чёрный текст
            self.label.bold = False
            self.bg_color = [0, 0, 0, 0]
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.bg_color)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)

    def _on_press(self, instance):
        if self.on_press_callback:
            self.on_press_callback(self.btn_text)


class TonalityRow(MDBoxLayout):
    """Строка тональностей в стиле Ultimate Guitar"""

    def __init__(self, on_item_selected=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = dp(70)
        self.spacing = dp(6)
        self.padding = [dp(12), dp(4), dp(12), dp(4)]

        self.on_item_selected = on_item_selected
        self.current_selected = "A"

        # Заголовок "Тональность" по центру, белым цветом
        title_layout = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(22),
            spacing=dp(8)
        )

        self.title_label = MDLabel(
            text="Тональность",
            font_size=sp(13),
            halign="center",
            valign="middle",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],  # Белый цвет
            bold=True
        )

        # Центрируем заголовок
        title_layout.add_widget(MDBoxLayout(size_hint_x=1))
        title_layout.add_widget(self.title_label)
        title_layout.add_widget(MDBoxLayout(size_hint_x=1))

        self.add_widget(title_layout)

        # Серая полоска с тональностями (как поиск)
        # Используем MDCard с закруглениями как у поиска
        self.tonality_card = MDCard(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(42),  # Такая же высота как у поиска
            radius=[theme.CORNER_RADIUS_SMALL, theme.CORNER_RADIUS_SMALL,
                    theme.CORNER_RADIUS_SMALL, theme.CORNER_RADIUS_SMALL],
            md_bg_color="#E8E8E8",  # Мягкий серый
            elevation=0,
            padding=[dp(8), dp(4), dp(8), dp(4)]
        )

        # Контейнер для кнопок тональностей (равномерное распределение)
        self.buttons_container = MDBoxLayout(
            orientation='horizontal',
            spacing=dp(2),
            size_hint_x=1,  # Растягивается на всю ширину
            adaptive_width=False
        )

        # Создаем кнопки для всех 12 тональностей с равными отступами
        self.buttons = []
        tonality_list = ['A', 'A#', 'B', 'C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#']

        for tonality in tonality_list:
            btn = TonalityButton(
                text=tonality,
                is_active=(tonality == self.current_selected),
                on_press_callback=self.on_tonality_press
            )
            self.buttons.append(btn)
            self.buttons_container.add_widget(btn)

        self.tonality_card.add_widget(self.buttons_container)
        self.add_widget(self.tonality_card)

    def on_tonality_press(self, tonality):
        """Обработчик нажатия на тональность"""
        self.set_selected(tonality)
        if self.on_item_selected:
            self.on_item_selected(tonality)

    def set_selected(self, tonality):
        """Устанавливает активную тональность"""
        self.current_selected = tonality
        for btn in self.buttons:
            btn.set_active(btn.btn_text == tonality)


class TypeButton(ButtonBehavior, MDBoxLayout):
    """Кнопка типа аккорда"""

    def __init__(self, text, is_active=False, on_press_callback=None, **kwargs):
        super().__init__(**kwargs)
        self.btn_text = text
        self.on_press_callback = on_press_callback
        self.size_hint = (1, 1)
        self.width = dp(54)
        self.padding = [dp(4), dp(2), dp(4), dp(2)]
        self.radius = [dp(6)]

        self.label = MDLabel(
            text=text,
            font_size=sp(9),
            halign="center",
            valign="middle",
            theme_text_color="Custom"
        )
        self.add_widget(self.label)
        self.set_active(is_active)
        self.bind(on_release=self._on_press)

        self.bg_color = [0, 0, 0, 0]
        with self.canvas.before:
            Color(*self.bg_color)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

    def _update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def set_active(self, is_active):
        if is_active:
            self.label.text_color = [1, 1, 1, 1]
            self.label.bold = True
            self.bg_color = [0.9, 0.6, 0.2, 1]
        else:
            self.label.text_color = [1, 1, 1, 0.7]
            self.label.bold = False
            self.bg_color = [0, 0, 0, 0]
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.bg_color)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)

    def _on_press(self, instance):
        if self.on_press_callback:
            self.on_press_callback(self.btn_text)


class ChordButton(ButtonBehavior, MDBoxLayout):
    """Кнопка аккорда"""

    def __init__(self, text, on_press_callback=None, **kwargs):
        super().__init__(**kwargs)
        self.btn_text = text
        self.on_press_callback = on_press_callback
        self.size_hint = (1, 1)
        self.width = dp(58)
        self.padding = [dp(4), dp(2), dp(4), dp(2)]
        self.radius = [dp(6)]

        self.label = MDLabel(
            text=text,
            font_size=sp(10),
            halign="center",
            valign="middle",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.9],
            bold=True
        )
        self.add_widget(self.label)
        self.bind(on_release=self._on_press)

        self.bg_color = [0, 0, 0, 0]
        with self.canvas.before:
            Color(*self.bg_color)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

    def _update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def set_active(self, is_active):
        if is_active:
            self.bg_color = [0.9, 0.6, 0.2, 1]
            self.label.text_color = [1, 1, 1, 1]
        else:
            self.bg_color = [0, 0, 0, 0]
            self.label.text_color = [1, 1, 1, 0.9]
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.bg_color)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)

    def _on_press(self, instance):
        if self.on_press_callback:
            self.on_press_callback(self.btn_text)


class VariantButton(ButtonBehavior, MDBoxLayout):
    """Кнопка варианта аккорда (компактная, с цифрой)"""

    def __init__(self, text, is_active=False, on_press_callback=None, **kwargs):
        super().__init__(**kwargs)
        self.btn_text = text
        self.on_press_callback = on_press_callback
        self.size_hint = (1, 1)
        self.width = dp(36)
        self.padding = [dp(2), dp(2), dp(2), dp(2)]
        self.radius = [dp(6)]

        self.label = MDLabel(
            text=text,
            font_size=sp(12),
            halign="center",
            valign="middle",
            theme_text_color="Custom"
        )
        self.add_widget(self.label)
        self.set_active(is_active)
        self.bind(on_release=self._on_press)

        self.bg_color = [0, 0, 0, 0]
        with self.canvas.before:
            Color(*self.bg_color)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

    def _update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def set_active(self, is_active):
        if is_active:
            self.label.text_color = [1, 1, 1, 1]
            self.label.bold = True
            self.bg_color = [0.9, 0.6, 0.2, 1]
        else:
            self.label.text_color = [1, 1, 1, 0.7]
            self.label.bold = False
            self.bg_color = [0, 0, 0, 0]
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.bg_color)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)

    def _on_press(self, instance):
        if self.on_press_callback:
            self.on_press_callback(self.btn_text)


class ScrollableRow(MDBoxLayout):
    """Универсальная скроллируемая строка с заголовком (для типов)"""

    def __init__(self, title, items=[], button_class=None, on_item_selected=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = dp(44)
        self.spacing = dp(8)
        self.padding = [dp(8), dp(4), dp(8), dp(4)]

        self.items = items
        self.button_class = button_class
        self.on_item_selected = on_item_selected
        self.current_selected = None
        self.buttons = []

        self.title_card = TitleCard(title=title)
        self.add_widget(self.title_card)

        self.scroll = MDScrollView(
            size_hint_x=0.8,
            do_scroll_x=True,
            do_scroll_y=False
        )

        self.buttons_container = MDBoxLayout(
            orientation='horizontal',
            size_hint_x=None,
            spacing=dp(6),
            padding=[dp(2), dp(2), dp(2), dp(2)]
        )

        for item in items:
            btn = button_class(
                text=item,
                is_active=False,
                on_press_callback=self.on_button_press
            )
            self.buttons.append(btn)
            self.buttons_container.add_widget(btn)

        self.buttons_container.bind(minimum_width=self.buttons_container.setter('width'))
        self.scroll.add_widget(self.buttons_container)
        self.add_widget(self.scroll)

    def on_button_press(self, item):
        self.current_selected = item
        for btn in self.buttons:
            if hasattr(btn, 'set_active'):
                btn.set_active(btn.btn_text == item)
        if self.on_item_selected:
            self.on_item_selected(item)

    def set_selected(self, item):
        self.current_selected = item
        for btn in self.buttons:
            if hasattr(btn, 'set_active'):
                btn.set_active(btn.btn_text == item)

    def set_items(self, new_items):
        self.buttons_container.clear_widgets()
        self.buttons.clear()

        for item in new_items:
            btn = self.button_class(
                text=item,
                is_active=False,
                on_press_callback=self.on_button_press
            )
            self.buttons.append(btn)
            self.buttons_container.add_widget(btn)

        self.buttons_container.bind(minimum_width=self.buttons_container.setter('width'))


class ChordsRow(MDBoxLayout):
    """Строка аккордов (скроллируемая)"""

    def __init__(self, on_item_selected=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = dp(44)
        self.spacing = dp(8)
        self.padding = [dp(8), dp(4), dp(8), dp(4)]

        self.on_item_selected = on_item_selected
        self.current_selected = None
        self.buttons = []
        self.chords_data = {}

        self.title_card = TitleCard(title="Аккорд")
        self.add_widget(self.title_card)

        self.scroll = MDScrollView(
            size_hint_x=0.8,
            do_scroll_x=True,
            do_scroll_y=False
        )

        self.buttons_container = MDBoxLayout(
            orientation='horizontal',
            size_hint_x=None,
            spacing=dp(6),
            padding=[dp(2), dp(2), dp(2), dp(2)]
        )

        self.buttons_container.bind(minimum_width=self.buttons_container.setter('width'))
        self.scroll.add_widget(self.buttons_container)
        self.add_widget(self.scroll)

    def set_chords(self, chords_list):
        self.buttons_container.clear_widgets()
        self.buttons.clear()
        self.chords_data.clear()

        for chord in chords_list:
            btn = ChordButton(
                text=chord['short_name'],
                on_press_callback=self.on_button_press
            )
            self.buttons.append(btn)
            self.buttons_container.add_widget(btn)
            self.chords_data[chord['short_name']] = chord

        if self.buttons:
            self.buttons[0].set_active(True)
            self.current_selected = self.buttons[0].btn_text
            if self.on_item_selected:
                self.on_item_selected(self.current_selected)

    def on_button_press(self, item):
        self.current_selected = item
        for btn in self.buttons:
            btn.set_active(btn.btn_text == item)
        if self.on_item_selected:
            self.on_item_selected(item)

    def get_chord_data(self, chord_name):
        return self.chords_data.get(chord_name)


class VariantsRow(MDBoxLayout):
    """Строка вариантов аккорда (все варианты в одной строке)"""

    def __init__(self, on_item_selected=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = dp(44)
        self.spacing = dp(4)
        self.padding = [dp(4), dp(4), dp(4), dp(4)]

        self.on_item_selected = on_item_selected
        self.current_selected = None
        self.buttons = []
        self.variants_count = 0

        # Заголовок "Позиция"
        self.title_card = MDCard(
            orientation='vertical',
            size_hint_x=None,
            width=dp(60),
            height=dp(36),
            radius=[dp(8)],
            md_bg_color="#E8DCC8",
            elevation=0,
            padding=[dp(4), dp(2), dp(4), dp(2)]
        )

        self.title_label = MDLabel(
            text="Позиция",
            font_size=sp(11),
            halign="center",
            valign="middle",
            theme_text_color="Custom",
            text_color=theme.TEXT_PRIMARY,
            bold=True
        )
        self.title_card.add_widget(self.title_label)
        self.add_widget(self.title_card)

        # Контейнер для кнопок вариантов
        self.buttons_container = MDBoxLayout(
            orientation='horizontal',
            size_hint_x=0.75,
            spacing=dp(4),
            padding=[dp(2), dp(2), dp(2), dp(2)]
        )

        self.add_widget(self.buttons_container)

    def set_variants(self, count, current_index=0):
        """Обновляет список вариантов"""
        self.buttons_container.clear_widgets()
        self.buttons.clear()
        self.variants_count = count

        for i in range(count):
            btn = VariantButton(
                text=str(i + 1),
                is_active=(i == current_index),
                on_press_callback=self.on_button_press
            )
            self.buttons.append(btn)
            self.buttons_container.add_widget(btn)

        if self.buttons:
            self.current_selected = self.buttons[current_index].btn_text

    def set_current_variant(self, index):
        """Устанавливает текущий выбранный вариант"""
        for i, btn in enumerate(self.buttons):
            btn.set_active(i == index)
        if 0 <= index < len(self.buttons):
            self.current_selected = self.buttons[index].btn_text

    def on_button_press(self, item):
        for i, btn in enumerate(self.buttons):
            if btn.btn_text == item:
                btn.set_active(True)
                self.current_selected = item
                if self.on_item_selected:
                    self.on_item_selected(i)
            else:
                btn.set_active(False)


class ChordActionButton(ButtonBehavior, MDBoxLayout):
    """Кнопка действий (пальцы, ноты, звук)"""

    def __init__(self, icon_name, on_press_callback=None, **kwargs):
        super().__init__(**kwargs)
        self.icon_name = icon_name
        self.on_press_callback = on_press_callback
        self.size_hint = (None, None)
        self.size = (dp(42), dp(42))
        self.icon = Image(
            size_hint=(None, None),
            size=(dp(24), dp(24)),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            allow_stretch=True
        )
        self.add_widget(self.icon)
        self.bind(on_release=self._on_press)
        self.load_icon()

    def load_icon(self):
        icon_data = load_asset_as_bytes(self.icon_name)
        if icon_data:
            img = CoreImage(BytesIO(icon_data), ext="png")
            self.icon.texture = img.texture

    def _on_press(self, instance):
        if self.on_press_callback:
            self.on_press_callback(self.icon_name)


class ChordsScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'chords'

        self.all_chords = []
        self.current_chord_module = None
        self.current_tonality = "A"
        self.current_type = "Major"
        self.current_variants = []
        self.current_variant_index = 0
        self.current_mode = "finger"

        self.md_bg_color = [0, 0, 0, 0]
        self.bg_image = None

        self.init_ui()
        self.load_background()
        self.scan_chords()

        logger.info('Экран аккордов создан')

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
                    self.bind(pos=self._update_bg_image, size=self._update_bg_image)
                    return
        except Exception as e:
            logger.error(f'Ошибка загрузки фона: {e}')

    def _update_bg_image(self, *args):
        if self.bg_image:
            self.bg_image.pos = self.pos
            self.bg_image.size = self.size

    def clean_description(self, description, chord_names):
        """Очищает описание от повторяющихся фраз и заменяет ! на |"""
        if not description:
            return ""

        # Заменяем ! на |
        description = description.replace('!', '|')

        # Разбиваем по разделителю |
        parts = description.split('|')
        unique_parts = []
        seen = set()

        for part in parts:
            part_clean = part.strip()
            if part_clean and part_clean not in seen:
                # Проверяем, не является ли часть названием аккорда
                is_chord_name = False
                for chord_name in chord_names:
                    if part_clean.lower() == chord_name.lower():
                        is_chord_name = True
                        break
                if not is_chord_name:
                    seen.add(part_clean)
                    unique_parts.append(part_clean)

        return ' | '.join(unique_parts)

    def init_ui(self):
        from kivy.uix.scrollview import ScrollView
        from kivy.uix.widget import Widget

        scroll = ScrollView(size_hint=(1, 1))

        main_layout = MDBoxLayout(
            orientation='vertical',
            padding=[dp(12), dp(2), dp(12), dp(8)],
            spacing=dp(8),
            size_hint_y=None
        )
        main_layout.bind(minimum_height=main_layout.setter('height'))

        # Отступ сверху
        top_spacer = Widget(size_hint_y=None, height=dp(65))
        main_layout.add_widget(top_spacer)

        # Поисковая строка
        self.search_card = MDCard(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(42),
            padding=[0, 0, 0, 0],
            radius=[theme.CORNER_RADIUS_SMALL, theme.CORNER_RADIUS_SMALL,
                    theme.CORNER_RADIUS_SMALL, theme.CORNER_RADIUS_SMALL],
            md_bg_color=theme.SURFACE,
            elevation=1
        )

        self.search_layout = MDBoxLayout(
            orientation='horizontal',
            spacing=dp(6),
            size_hint_y=None,
            height=dp(42),
            padding=[dp(8), dp(4), dp(8), dp(4)]
        )

        self.search_field = MDTextField(
            hint_text="Поиск аккорда...",
            mode="filled",
            size_hint_x=0.85,
            font_size=dp(12),
            height=dp(34),
            line_color_normal=theme.PRIMARY_LIGHT,
            line_color_focus=theme.PRIMARY,
            radius=[theme.CORNER_RADIUS_SMALL, theme.CORNER_RADIUS_SMALL,
                    theme.CORNER_RADIUS_SMALL, theme.CORNER_RADIUS_SMALL],
            on_text_validate=self.on_search_submit
        )

        self.clear_search_btn = MDIconButton(
            icon="close-circle",
            size_hint_x=0.05,
            theme_icon_color="Custom",
            icon_color=theme.TEXT_SECONDARY,
            on_release=self.clear_search,
            opacity=0,
            md_bg_color=[0, 0, 0, 0]
        )

        self.search_btn = MDIconButton(
            icon="magnify",
            size_hint_x=None,
            width=dp(36),
            theme_icon_color="Custom",
            icon_color=theme.PRIMARY,
            on_release=self.on_search_submit,
            md_bg_color=[0, 0, 0, 0]
        )

        self.search_layout.add_widget(self.search_field)
        self.search_layout.add_widget(self.clear_search_btn)
        self.search_layout.add_widget(self.search_btn)
        self.search_card.add_widget(self.search_layout)
        main_layout.add_widget(self.search_card)

        # Строка тональностей
        self.tonality_row = TonalityRow(
            on_item_selected=self.on_tonality_selected
        )
        main_layout.add_widget(self.tonality_row)
        self.tonality_row.set_selected("A")

        # Строка типов аккордов
        self.type_row = ScrollableRow(
            title="Тип",
            items=CHORD_TYPES,
            button_class=TypeButton,
            on_item_selected=self.on_type_selected
        )
        main_layout.add_widget(self.type_row)
        self.type_row.set_selected("Major")

        # Строка аккордов
        self.chords_row = ChordsRow(on_item_selected=self.on_chord_selected)
        main_layout.add_widget(self.chords_row)

        # Строка вариантов
        self.variants_row = VariantsRow(on_item_selected=self.on_variant_selected)
        main_layout.add_widget(self.variants_row)

        # ========== БЛОК С ГРИФОМ ==========
        griff_block = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(320),
            spacing=dp(4)
        )

        # Название аккорда (над картинкой)
        self.chord_name_label = MDLabel(
            text="Выберите аккорд",
            halign="center",
            font_size=sp(18),
            bold=True,
            size_hint_y=None,
            height=dp(32),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1]
        )
        griff_block.add_widget(self.chord_name_label)

        # Гриф (картинка)
        griff_container = MDBoxLayout(
            size_hint=(1, None),
            height=dp(220),
            padding=[dp(8), dp(4), dp(8), dp(4)]
        )
        self.chord_renderer = ChordRenderer()
        griff_container.add_widget(self.chord_renderer)
        griff_block.add_widget(griff_container)

        # Описание аккорда (под картинкой)
        self.chord_desc_label = MDLabel(
            text="",
            halign="center",
            font_size=sp(9),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.6],
            size_hint_y=None,
            height=dp(40),
            markup=True
        )
        griff_block.add_widget(self.chord_desc_label)

        # Иконки действий (пальцы, ноты, звук) по центру
        action_icons_layout = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(50),
            spacing=dp(20),
            padding=[dp(8), dp(4), dp(8), dp(4)]
        )

        # Кнопка "пальцы"
        self.finger_btn = ChordActionButton(
            icon_name="fingers_png",
            on_press_callback=lambda x: self.set_mode("finger")
        )
        action_icons_layout.add_widget(self.finger_btn)

        # Кнопка "ноты"
        self.note_btn = ChordActionButton(
            icon_name="notes_png",
            on_press_callback=lambda x: self.set_mode("note")
        )
        action_icons_layout.add_widget(self.note_btn)

        # Кнопка "звук" (заглушка)
        self.sound_btn = ChordActionButton(
            icon_name="sound_png",
            on_press_callback=lambda x: self.on_sound_press()
        )
        action_icons_layout.add_widget(self.sound_btn)

        # Центрируем иконки
        action_icons_layout.add_widget(MDBoxLayout(size_hint_x=1))
        griff_block.add_widget(action_icons_layout)

        main_layout.add_widget(griff_block)

        scroll.add_widget(main_layout)
        self.add_widget(scroll)

        # Загружаем фон грифа
        try:
            bg_data = load_asset_as_bytes("griff_png")
            if bg_data:
                img = CoreImage(BytesIO(bg_data), ext="png")
                self.chord_renderer.set_background(img.texture)
        except Exception as e:
            logger.error(f"Ошибка загрузки фона грифа: {e}")

    def on_sound_press(self):
        """Заглушка для звука - потом добавим логику"""
        notify.info("🔊 Звук аккорда (будет доступно в следующей версии)")

    def on_search_submit(self, instance):
        query = self.search_field.text.strip()
        if not query:
            return
        self.clear_search_btn.opacity = 1
        self.search_chord(query)

    def clear_search(self, instance):
        self.search_field.text = ""
        self.clear_search_btn.opacity = 0
        if self.current_tonality and self.current_type:
            self.update_chords_list()
            if hasattr(self.chords_row, 'buttons') and self.chords_row.buttons:
                self.on_chord_selected(self.chords_row.buttons[0].btn_text)

    def search_chord(self, query):
        search_normalized = query.lower().replace('/', '$')
        found_chord = None
        for chord in self.all_chords:
            name = chord['name'].lower().replace('/', '$')
            if search_normalized == name:
                found_chord = chord
                break
            if '|' in name:
                for alt in name.split('|'):
                    if search_normalized == alt.strip():
                        found_chord = chord
                        break
                if found_chord:
                    break

        if found_chord:
            tonality = self.extract_tonality(found_chord['name'])
            self.on_tonality_selected(tonality)
            chord_types = found_chord['type'].split('|') if found_chord['type'] else []
            if chord_types:
                self.on_type_selected(chord_types[0])
            all_variants = [c for c in self.all_chords if c['short_name'] == found_chord['short_name']]
            all_variants.sort(key=lambda x: x['variant'])
            self.load_chord_variants(all_variants)
        else:
            notify.warning(f"Аккорд '{query}' не найден")

    def scan_chords(self):
        chords_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'chords')
        if not os.path.exists(chords_dir):
            os.makedirs(chords_dir, exist_ok=True)
            return

        self.all_chords = []
        for root, dirs, files in os.walk(chords_dir):
            for f in files:
                if f.endswith('.py') and not f.startswith('__'):
                    full_path = os.path.join(root, f)
                    try:
                        module_name = os.path.splitext(f)[0]
                        spec = importlib.util.spec_from_file_location(module_name, full_path)
                        if spec is None:
                            continue
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        metadata = getattr(module, 'METADATA', {})
                        chord_name = metadata.get('name', module_name)
                        chord_name = chord_name.replace('!', '|')
                        chord_name = chord_name.replace('$', '/')
                        variant_match = re.search(r'_(\d+)\.py$', f)
                        variant_num = int(variant_match.group(1)) if variant_match else metadata.get('variant', 1)
                        self.all_chords.append({
                            'id': f"{chord_name}_v{variant_num}",
                            'name': chord_name,
                            'short_name': chord_name.split('|')[0].replace('$', '/'),
                            'variant': variant_num,
                            'type': metadata.get('type', ''),
                            'description': metadata.get('description', ''),
                            'path': full_path,
                            'module': module
                        })
                    except Exception as e:
                        logger.error(f"Ошибка загрузки {f}: {e}")
        self.update_chords_list()

    def update_chords_list(self):
        filtered = []
        for chord in self.all_chords:
            tonality = self.extract_tonality(chord['name'])
            if tonality != self.current_tonality:
                continue
            chord_types = chord['type'].split('|') if chord['type'] else []
            if self.current_type not in chord_types:
                continue
            filtered.append(chord)

        chords_by_name = {}
        for chord in filtered:
            name = chord['short_name']
            if name not in chords_by_name:
                chords_by_name[name] = []
            chords_by_name[name].append(chord)

        chords_list = []
        for name, variants in chords_by_name.items():
            variants.sort(key=lambda x: x['variant'])
            chords_list.append({'short_name': name, 'variants': variants})
        chords_list.sort(key=lambda x: x['short_name'])
        self.chords_row.set_chords(chords_list)

    def extract_tonality(self, chord_name):
        if not chord_name:
            return ""
        if '|' in chord_name:
            main_name = chord_name.split('|')[0]
        else:
            main_name = chord_name
        match = re.match(r'^([A-H][#b]?)', main_name)
        return match.group(1) if match else (main_name[0] if main_name else "")

    def on_chord_selected(self, chord_name):
        chord_data = self.chords_row.get_chord_data(chord_name)
        if chord_data:
            self.load_chord_variants(chord_data['variants'])

    def load_chord_variants(self, variants):
        if not variants:
            return
        variants.sort(key=lambda x: x['variant'])
        self.current_variants = variants
        self.current_variant_index = 0

        self.variants_row.set_variants(len(variants), 0)
        self.load_current_variant()

    def load_current_variant(self):
        if not self.current_variants:
            return
        variant = self.current_variants[self.current_variant_index]
        self.current_chord_module = variant['module']

        # Название аккорда - убираем дубликаты
        chord_name = variant['name'].replace('!', ' | ')
        chord_name = chord_name.replace('$', '/')

        # Убираем дубликаты в названии
        name_parts = chord_name.split('|')
        unique_names = []
        seen_names = set()
        for part in name_parts:
            part_clean = part.strip()
            if part_clean and part_clean not in seen_names:
                seen_names.add(part_clean)
                unique_names.append(part_clean)
        display_name = ' | '.join(unique_names)

        self.chord_name_label.text = display_name

        # Описание (очищаем от дубликатов)
        description = variant.get('description', '')
        description = self.clean_description(description, unique_names)
        self.chord_desc_label.text = description

        # Выделение варианта
        self.variants_row.set_current_variant(self.current_variant_index)

        if hasattr(self, 'chord_renderer'):
            self.chord_renderer.load_chord(self.current_chord_module)
            self.chord_renderer.set_mode(self.current_mode)

    def on_variant_selected(self, index):
        self.current_variant_index = index
        self.load_current_variant()

    def set_mode(self, mode):
        self.current_mode = mode
        if self.current_chord_module and hasattr(self, 'chord_renderer'):
            self.chord_renderer.set_mode(mode)

    def on_tonality_selected(self, tonality):
        self.current_tonality = tonality
        self.update_chords_list()

    def on_type_selected(self, chord_type):
        self.current_type = chord_type
        self.update_chords_list()

    def on_pre_enter(self):
        self.update_chords_list()
        return super().on_pre_enter()