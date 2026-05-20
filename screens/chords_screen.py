# screens/chords_screen.py
"""
Экран гитарных аккордов - с 4 карточками селекторами
ТОН, ТИП, АККОРД, ПОЗИЦИЯ в стиле админки
С поиском аккордов
"""
from kivy.uix.behaviors import ButtonBehavior
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

from kivymd.uix.textfield import MDTextField

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


class SearchBar(MDCard):
    """Поисковая строка как в songs_screen.py"""

    def __init__(self, on_search=None, on_clear=None, **kwargs):
        super().__init__(**kwargs)
        self.on_search = on_search
        self.on_clear = on_clear
        self.current_query = ""
        self._search_timer = None

        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = dp(48)
        self.radius = [dp(24), dp(24), dp(24), dp(24)]
        self.md_bg_color = [0.96, 0.96, 0.96, 1]
        self.elevation = 0
        self.padding = [dp(16), dp(6), dp(12), dp(6)]
        self.spacing = dp(8)

        self.search_field = MDTextField(
            hint_text="Поиск аккордов...",
            size_hint_x=1,
            font_size=sp(15),
            height=dp(36),
            on_text_validate=self._on_search,
            mode="fill"
        )

        self.search_field.line_color_normal = [0, 0, 0, 0]
        self.search_field.line_color_focus = [0, 0, 0, 0]
        self.search_field.fill_color_normal = [1, 1, 1, 0]
        self.search_field.fill_color_focus = [1, 1, 1, 0]
        self.search_field.hint_text_color = [0.7, 0.7, 0.7, 1]
        self.search_field.foreground_color = [0.1, 0.1, 0.1, 1]

        self.search_field.bind(text=self._on_text_change)

        self.clear_btn = MDIconButton(
            icon="close-circle",
            size_hint=(None, None),
            size=(dp(24), dp(24)),
            theme_icon_color="Custom",
            icon_color=[0.6, 0.6, 0.6, 1],
            md_bg_color=[0, 0, 0, 0],
            on_release=self._on_clear,
            opacity=0
        )

        self.search_icon = MDIconButton(
            icon="magnify",
            size_hint=(None, None),
            size=(dp(32), dp(32)),
            theme_icon_color="Custom",
            icon_color=[0.46, 0.70, 0.71, 1],
            md_bg_color=[0, 0, 0, 0],
            on_release=self._on_search,
            pos_hint={'center_y': 0.5}
        )

        self.add_widget(self.search_field)
        self.add_widget(self.clear_btn)
        self.add_widget(self.search_icon)

    def _on_text_change(self, instance, text):
        self.clear_btn.opacity = 1 if text else 0
        self.current_query = text

        if self._search_timer:
            Clock.unschedule(self._search_timer)
            self._search_timer = None

        if not text.strip():
            if self.on_clear:
                self.on_clear()
        else:
            self._search_timer = Clock.schedule_once(lambda dt: self._do_search(), 0.3)

    def _do_search(self):
        if self.on_search and self.current_query:
            text = self.current_query.strip()
            if text:
                self.on_search(text)

    def _on_search(self, instance):
        if self._search_timer:
            Clock.unschedule(self._search_timer)
            self._search_timer = None

        if self.on_search:
            text = self.search_field.text.strip()
            if text:
                self.on_search(text)

    def _on_clear(self, instance):
        self.search_field.text = ""
        self.search_field.focus = True
        self.clear_btn.opacity = 0
        if self.on_clear:
            self.on_clear()

    def get_text(self):
        return self.search_field.text.strip()

    def set_text(self, text):
        self.search_field.text = text
        self.clear_btn.opacity = 1 if text else 0

    def clear(self):
        self.search_field.text = ""
        self.clear_btn.opacity = 0

    def focus(self):
        self.search_field.focus = True


class SelectorCard(MDCard):
    """Карточка селектора в стиле админки (как карточки парсеров)"""

    SELECTOR_COLORS = {
        'TON': ('#2196F3', '#1976D2'),
        'TIP': ('#9C27B0', '#7B1FA2'),
        'AKKORD': ('#FF5722', '#E64A19'),
        'POZICIYA': ('#009688', '#00796B'),
    }

    def __init__(self, selector_type, title, value, on_left=None, on_right=None, on_center=None, **kwargs):
        super().__init__(**kwargs)
        self.selector_type = selector_type
        self.title = title
        self.value = value
        self.on_left_callback = on_left
        self.on_right_callback = on_right
        self.on_center_callback = on_center

        colors = self.SELECTOR_COLORS.get(selector_type, ('#757575', '#616161'))
        self.bg_color = colors[0]

        self.orientation = 'vertical'
        self.size_hint = (1, 1)
        self.radius = [dp(16)]
        self.elevation = 0
        self.md_bg_color = self._hex_to_rgba(self.bg_color, 0.3)
        self.line_color = [1, 1, 1, 0.25]
        self.line_width = 0.8
        self.padding = [dp(6), dp(8), dp(6), dp(8)]
        self.spacing = dp(4)
        self.ripple_behavior = True

        self.title_label = MDLabel(
            text=title,
            font_size=sp(10),
            halign="center",
            size_hint_y=None,
            height=dp(20),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.7],
            bold=True
        )

        self.row = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(40),
            spacing=dp(4)
        )

        self.left_btn = self._create_arrow_button('left_arrow_png', '◀')
        if on_left:
            self.left_btn.bind(on_release=on_left)

        self.value_label = MDLabel(
            text=value,
            font_size=sp(16),
            halign="center",
            valign="middle",
            size_hint_x=1,
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.95],
            bold=True
        )

        self.right_btn = self._create_arrow_button('right_arrow_png', '▶')
        if on_right:
            self.right_btn.bind(on_release=on_right)

        self.row.add_widget(self.left_btn)
        self.row.add_widget(self.value_label)
        self.row.add_widget(self.right_btn)

        self.add_widget(self.title_label)
        self.add_widget(self.row)

        self.bind(on_enter=self._on_enter, on_leave=self._on_leave)
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

    def _hex_to_rgba(self, hex_color, alpha=1.0):
        hex_color = hex_color.lstrip('#')
        return [
            int(hex_color[i:i + 2], 16) / 255.0
            for i in (0, 2, 4)
        ] + [alpha]

    def _on_enter(self, *args):
        self.md_bg_color = self._hex_to_rgba(self.bg_color, 0.5)

    def _on_leave(self, *args):
        self.md_bg_color = self._hex_to_rgba(self.bg_color, 0.3)

    def _on_value_click(self, instance, touch):
        if self.value_label.collide_point(*touch.pos):
            if self.on_center_callback:
                self.on_center_callback()
            return True
        return False

    def update_value(self, new_value):
        self.value = new_value
        self.value_label.text = new_value


class ChordActionButton(ButtonBehavior, MDBoxLayout):
    """Кнопка действия с иконкой из ассета (без выделений)"""

    def __init__(self, icon_name, on_press_callback=None, **kwargs):
        super().__init__(**kwargs)
        self.icon_name = icon_name
        self.on_press_callback = on_press_callback
        self.size_hint = (None, None)
        self.size = (dp(42), dp(42))
        self.md_bg_color = [0, 0, 0, 0]
        self.icon = Image(
            size_hint=(None, None),
            size=(dp(24), dp(24)),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            allow_stretch=True
        )
        self.add_widget(self.icon)
        self.bind(on_release=self._on_press)
        self._load_icon()

    def _load_icon(self):
        if HAS_ASSETS:
            try:
                icon_data = load_asset_as_bytes(self.icon_name)
                if icon_data:
                    img = CoreImage(BytesIO(icon_data), ext="png")
                    self.icon.texture = img.texture
                    return
            except Exception as e:
                logger.error(f"Ошибка загрузки иконки {self.icon_name}: {e}")
        self.icon.text = "?"

    def _on_press(self, instance):
        if self.on_press_callback:
            self.on_press_callback(self.icon_name)


class ChordsScreen(BaseScreen):
    TONALITIES = TONALITIES
    CHORD_TYPES = CHORD_TYPES
    """Экран аккордов с 4 карточками-селекторами и поиском"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'chords'
        self.all_chords = []
        self.current_chord_module = None
        self.is_search_mode = False
        self.search_results = []

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

        self.search_bar = None
        self.tonality_card = None
        self.type_card = None
        self.chord_card = None
        self.position_card = None
        self.chord_name_label = None
        self.chord_desc_label = None
        self.chord_renderer = None
        self.finger_btn = None
        self.note_btn = None
        self.sound_btn = None
        self.chord_icon = None

        self.bg_image = None

        self.init_ui()
        self.load_background()
        self.scan_chords()

        logger.info('Экран аккордов создан с поиском')

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
        content = MDBoxLayout(
            orientation='vertical',
            spacing=dp(12),
            size_hint_y=None,
            adaptive_height=True
        )

        # Верхняя карточка с названием аккорда
        name_card_wrapper = MDCard(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(72),
            radius=[dp(16), dp(16), dp(16), dp(16)],
            md_bg_color=[0, 0, 0, 0.08],
            elevation=0,
            line_color=[1, 1, 1, 0.25],
            line_width=0.8,
            padding=[dp(12), dp(8), dp(12), dp(8)]
        )

        # Горизонтальный контейнер с тремя частями: иконка, центр, пустота
        name_container = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, 1),
            spacing=dp(12)
        )

        # Левая часть - иконка (фиксированная ширина)
        left_box = MDBoxLayout(
            size_hint_x=None,
            width=dp(36),
            pos_hint={'center_y': 0.5}
        )
        self.chord_icon = Image(
            size_hint=(None, None),
            size=(dp(36), dp(36)),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            allow_stretch=True,
            keep_ratio=True
        )
        self._load_chord_icon()
        left_box.add_widget(self.chord_icon)

        # Центральная часть - текст (растягивается)
        center_box = MDBoxLayout(
            orientation='vertical',
            size_hint_x=1,
            spacing=dp(4),
            pos_hint={'center_y': 0.5}
        )

        self.chord_name_label = MDLabel(
            text="A | Amaj",
            font_size=sp(20),
            halign="center",
            bold=True,
            size_hint_y=None,
            height=dp(30),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.95]
        )

        self.chord_desc_label = MDLabel(
            text="",
            font_size=sp(11),
            halign="center",
            size_hint_y=None,
            height=dp(18),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.5],
            shorten=True,
            shorten_from="right"
        )

        center_box.add_widget(self.chord_name_label)
        center_box.add_widget(self.chord_desc_label)

        # Правая часть - пустая для баланса (такой же ширины как левая)
        right_box = MDBoxLayout(
            size_hint_x=None,
            width=dp(36)
        )

        name_container.add_widget(left_box)
        name_container.add_widget(center_box)
        name_container.add_widget(right_box)
        name_card_wrapper.add_widget(name_container)
        content.add_widget(name_card_wrapper)

        # Гриф
        griff_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(240),
            padding=[dp(4), dp(4), dp(4), dp(4)]
        )

        self.chord_renderer = ChordRenderer()
        griff_container.add_widget(self.chord_renderer)
        content.add_widget(griff_container)

        # Иконки действий
        icons_row = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(54),
            spacing=dp(16),
            padding=[dp(16), dp(6), dp(16), dp(6)]
        )

        icons_row.add_widget(Widget(size_hint_x=1))

        self.finger_btn = ChordActionButton(
            icon_name="fingers_png",
            on_press_callback=self.set_mode
        )

        self.note_btn = ChordActionButton(
            icon_name="notes_png",
            on_press_callback=self.set_mode
        )

        self.sound_btn = ChordActionButton(
            icon_name="sound_png",
            on_press_callback=self.on_sound_press
        )

        icons_row.add_widget(self.finger_btn)
        icons_row.add_widget(self.note_btn)
        icons_row.add_widget(self.sound_btn)
        icons_row.add_widget(Widget(size_hint_x=1))

        content.add_widget(icons_row)

        # Поиск
        self.search_bar = SearchBar(
            on_search=self.do_search,
            on_clear=self.clear_search
        )
        content.add_widget(self.search_bar)

        # Ряд 1: ТОН и ТИП
        row1 = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(70),
            spacing=dp(10)
        )

        self.tonality_card = SelectorCard(
            selector_type='TON',
            title="ТОН",
            value=self.current_tonality,
            on_left=self.prev_tonality,
            on_right=self.next_tonality,
            on_center=self.show_tonality_picker
        )

        self.type_card = SelectorCard(
            selector_type='TIP',
            title="ТИП",
            value=self.current_type,
            on_left=self.prev_type,
            on_right=self.next_type,
            on_center=self.show_type_picker
        )

        row1.add_widget(self.tonality_card)
        row1.add_widget(self.type_card)
        content.add_widget(row1)

        # Ряд 2: АККОРД и ПОЗИЦИЯ
        row2 = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(70),
            spacing=dp(10)
        )

        self.chord_card = SelectorCard(
            selector_type='AKKORD',
            title="АККОРД",
            value=self.current_chord_name,
            on_left=self.prev_chord,
            on_right=self.next_chord,
            on_center=self.show_chord_picker
        )

        self.position_card = SelectorCard(
            selector_type='POZICIYA',
            title="ПОЗИЦИЯ",
            value=str(self.current_position),
            on_left=self.prev_position,
            on_right=self.next_position,
            on_center=self.show_position_picker
        )

        row2.add_widget(self.chord_card)
        row2.add_widget(self.position_card)
        content.add_widget(row2)

        content.add_widget(Widget(size_hint_y=None, height=dp(20)))

        self.build_ui(content_widget=content, use_scroll=True)

        try:
            bg_data = load_asset_as_bytes("griff_png")
            if bg_data:
                img = CoreImage(BytesIO(bg_data), ext="png")
                if img and img.texture:
                    self.chord_renderer.set_background(img.texture)
        except Exception as e:
            logger.error(f"Ошибка загрузки фона грифа: {e}")

    def _load_chord_icon(self):
        if HAS_ASSETS:
            try:
                icon_data = load_asset_as_bytes("chord_caption_png")
                if icon_data:
                    img = CoreImage(BytesIO(icon_data), ext="png")
                    self.chord_icon.texture = img.texture
                    return
            except Exception as e:
                logger.error(f"Ошибка загрузки иконки chord_caption_png: {e}")
        self.chord_icon.text = "🎸"

    def do_search(self, query):
        """Поиск аккордов по точному совпадению названия или описания"""
        query_original = query.strip()
        query_lower = query_original.lower()

        if not query_lower:
            if self.is_search_mode:
                self.clear_search()
            return

        self.is_search_mode = True
        self.search_results = []

        # Очищаем запрос от знаков препинания для поиска по описанию
        import string
        query_for_desc = query_lower
        for punct in string.punctuation:
            query_for_desc = query_for_desc.replace(punct, ' ')
        query_for_desc = ' '.join(query_for_desc.split())

        # Карта соответствий для b и # (альтернативные названия)
        alt_map = {
            'bb': 'a#',
            'a#': 'bb',
            'db': 'c#',
            'c#': 'db',
            'eb': 'd#',
            'd#': 'eb',
            'gb': 'f#',
            'f#': 'gb',
            'ab': 'g#',
            'g#': 'ab'
        }

        alt_query = alt_map.get(query_lower, None)

        # Поиск по названию (точное совпадение)
        for chord in self.all_chords:
            short_name_lower = chord['short_name'].lower()

            if short_name_lower == query_lower or (alt_query and short_name_lower == alt_query):
                if chord not in self.search_results:
                    self.search_results.append(chord)

        # Если не нашли по названию - ищем по описанию (точное совпадение всей строки)
        if not self.search_results:
            for chord in self.all_chords:
                description = chord.get('description', '')
                if description:
                    # Очищаем описание от знаков препинания
                    desc_clean = description.lower()
                    for punct in string.punctuation:
                        desc_clean = desc_clean.replace(punct, ' ')
                    desc_clean = ' '.join(desc_clean.split())

                    # ТОЧНОЕ совпадение всей строки описания
                    if desc_clean == query_for_desc:
                        if chord not in self.search_results:
                            self.search_results.append(chord)

        # Убираем дубликаты
        unique_results = []
        seen_names = set()

        for chord in self.search_results:
            if chord['short_name'] not in seen_names:
                seen_names.add(chord['short_name'])
                unique_results.append(chord)

        self.search_results = unique_results

        if self.search_results:
            selected_chord = self.search_results[0]

            self.current_chord_name = selected_chord['short_name']
            self.chord_card.update_value(self.current_chord_name)

            variants = []
            for chord in self.all_chords:
                if chord['short_name'] == self.current_chord_name:
                    variants.append(chord)

            if variants:
                variants.sort(key=lambda x: x['variant'])
                self.current_variants = variants
                self.current_variant_index = 0
                self.current_position = 1
                self.position_card.update_value("1")
                self.load_current_variant()

            notify.info(f"Найдено аккордов: {len(self.search_results)}", duration=1.5)
        else:
            self.search_bar.search_field.hint_text = f"'{query}' не найдено"
            Clock.schedule_once(lambda dt: self._reset_hint(), 2)

    def _reset_hint(self):
        self.search_bar.search_field.hint_text = "Поиск аккордов..."

    def clear_search(self):
        self.is_search_mode = False
        self.search_results = []
        self.search_bar.search_field.hint_text = "Поиск аккордов..."
        self.update_available_chords()

    def on_sound_press(self, icon_name):
        notify.info("🔊 Звук аккорда (будет доступно в следующей версии)")

    def set_mode(self, icon_name):
        if icon_name == "fingers_png":
            self.current_mode = "finger"
        elif icon_name == "notes_png":
            self.current_mode = "note"

        if self.current_chord_module and self.chord_renderer:
            self.chord_renderer.set_mode(self.current_mode)

    # ============ МЕТОДЫ ДЛЯ ТОНАЛЬНОСТИ ============
    def prev_tonality(self, instance):
        if self.is_search_mode:
            self.clear_search()
        self.current_tonality_index = (self.current_tonality_index - 1) % len(TONALITIES)
        self.current_tonality = TONALITIES[self.current_tonality_index]
        self.tonality_card.update_value(self.current_tonality)
        self.update_available_chords()

    def next_tonality(self, instance):
        if self.is_search_mode:
            self.clear_search()
        self.current_tonality_index = (self.current_tonality_index + 1) % len(TONALITIES)
        self.current_tonality = TONALITIES[self.current_tonality_index]
        self.tonality_card.update_value(self.current_tonality)
        self.update_available_chords()

    def show_tonality_picker(self):
        if self.is_search_mode:
            self.clear_search()
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
        if self.is_search_mode:
            self.clear_search()
        self.current_type_index = (self.current_type_index - 1) % len(CHORD_TYPES)
        self.current_type = CHORD_TYPES[self.current_type_index]
        self.type_card.update_value(self.current_type)
        self.update_available_chords()

    def next_type(self, instance):
        if self.is_search_mode:
            self.clear_search()
        self.current_type_index = (self.current_type_index + 1) % len(CHORD_TYPES)
        self.current_type = CHORD_TYPES[self.current_type_index]
        self.type_card.update_value(self.current_type)
        self.update_available_chords()

    def show_type_picker(self):
        if self.is_search_mode:
            self.clear_search()
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
    def _load_variants_for_chord(self, chord_name):
        variants = []
        for chord in self.all_chords:
            if chord['short_name'] == chord_name:
                tonality = self.extract_tonality(chord['name'])
                if tonality == self.current_tonality:
                    chord_types = chord['type'].split('|') if chord['type'] else []
                    if self.current_type in chord_types or self.current_type == chord.get('type', ''):
                        variants.append(chord)

        if variants:
            variants.sort(key=lambda x: x['variant'])
            self.current_variants = variants
            self.current_variant_index = 0
            self.current_position = 1
            self.position_card.update_value("1")
            self.load_current_variant()
        else:
            self.current_variants = []
            self.current_variant_index = 0
            self.current_position = 1

    def prev_chord(self, instance):
        if self.is_search_mode:
            return
        if not self.available_chords:
            return
        self.current_chord_index = (self.current_chord_index - 1) % len(self.available_chords)
        self.current_chord_name = self.available_chords[self.current_chord_index]
        self.chord_card.update_value(self.current_chord_name)
        self._load_variants_for_chord(self.current_chord_name)

    def next_chord(self, instance):
        if self.is_search_mode:
            return
        if not self.available_chords:
            return
        self.current_chord_index = (self.current_chord_index + 1) % len(self.available_chords)
        self.current_chord_name = self.available_chords[self.current_chord_index]
        self.chord_card.update_value(self.current_chord_name)
        self._load_variants_for_chord(self.current_chord_name)

    def show_chord_picker(self):
        if self.is_search_mode:
            return
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
        self._load_variants_for_chord(self.current_chord_name)
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
                text=str(i + 1),
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
        if self.is_search_mode:
            return
        filtered = []
        for chord in self.all_chords:
            tonality = self.extract_tonality(chord['name'])
            if tonality != self.current_tonality:
                continue
            chord_types = chord['type'].split('|') if chord['type'] else []
            if self.current_type not in chord_types and self.current_type != chord.get('type', ''):
                continue
            filtered.append(chord)

        chords_by_name = {}
        for chord in filtered:
            name = chord['short_name']
            if name not in chords_by_name:
                chords_by_name[name] = []
            chords_by_name[name].append(chord)

        self.available_chords = sorted(chords_by_name.keys())

        if self.available_chords:
            if self.current_chord_name not in self.available_chords:
                self.current_chord_index = 0
                self.current_chord_name = self.available_chords[0]
                self.chord_card.update_value(self.current_chord_name)

            chord_data = chords_by_name.get(self.current_chord_name)
            if chord_data:
                self.load_chord_variants(chord_data)
        else:
            self.available_chords = []
            self.current_variants = []
            self.current_chord_data = None

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

        # Форматирование названия
        chord_name = variant['name'].replace('!', ' | ').replace('$', '/')
        name_parts = [p.strip() for p in chord_name.split('|') if p.strip()]

        if len(name_parts) > 1:
            main_name = name_parts[0]
            other_names = []
            for name in name_parts[1:]:
                if name != main_name and name not in other_names:
                    other_names.append(name)

            if other_names:
                display_name = f"{main_name} ({', '.join(other_names)})"
            else:
                display_name = main_name
        else:
            display_name = name_parts[0] if name_parts else "?"

        self.chord_name_label.text = display_name

        # Описание
        description = variant.get('description', '')
        if description:
            desc_parts = [p.strip() for p in description.replace('!', '|').split('|') if p.strip()]

            unique_parts = []
            for part in desc_parts:
                if part not in unique_parts:
                    unique_parts.append(part)

            if len(unique_parts) > 1:
                formatted_desc = self._compact_description(unique_parts)
            else:
                formatted_desc = unique_parts[0] if unique_parts else ""

            main_name = name_parts[0] if name_parts else ""
            if main_name and main_name in formatted_desc:
                formatted_desc = formatted_desc.replace(main_name, '').strip(' |')

            formatted_desc = re.sub(r'\s*\|\s*', ' | ', formatted_desc).strip(' |')
            formatted_desc = re.sub(r'\s+', ' ', formatted_desc)

            if len(formatted_desc) > 50:
                formatted_desc = formatted_desc[:47] + "..."

            self.chord_desc_label.text = formatted_desc
        else:
            self.chord_desc_label.text = TYPE_DISPLAY.get(self.current_type, self.current_type)

        if self.chord_renderer:
            self.chord_renderer.load_chord(self.current_chord_module)
            self.chord_renderer.set_mode(self.current_mode)

    def _compact_description(self, parts):
        if len(parts) == 1:
            return parts[0]

        def find_longest_common_substring(strings):
            if not strings:
                return ""
            shortest = min(strings, key=len)
            longest_common = ""
            for i in range(len(shortest)):
                for j in range(i + 1, len(shortest) + 1):
                    substring = shortest[i:j]
                    if all(substring in s for s in strings):
                        if len(substring) > len(longest_common):
                            longest_common = substring
            return longest_common

        common_substring = find_longest_common_substring(parts)

        if common_substring:
            unique_parts = []
            for part in parts:
                unique = part.replace(common_substring, '').strip()
                if unique:
                    unique_parts.append(unique)

            unique_parts_unique = []
            for up in unique_parts:
                if up not in unique_parts_unique:
                    unique_parts_unique.append(up)

            first_unique = unique_parts_unique[0] if unique_parts_unique else ""
            other_uniques = unique_parts_unique[1:] if len(unique_parts_unique) > 1 else []

            if other_uniques:
                return f"{first_unique} ({', '.join(other_uniques)}) {common_substring}".strip()
            else:
                return f"{first_unique} {common_substring}".strip()
        else:
            return ', '.join(parts)

    def load_chord_by_name(self, chord_name):
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
                            self._load_variants_for_chord(self.current_chord_name)
                break

    def select_chord_by_name(self, chord_name):
        """Выбирает аккорд по точному имени (из поиска) с учётом типа"""
        logger.info(f"🎸 select_chord_by_name: ищем аккорд '{chord_name}'")

        # Ищем аккорд с точным совпадением short_name
        target_chord = None
        for chord in self.all_chords:
            # Сравниваем short_name без учёта регистра
            if chord['short_name'].lower() == chord_name.lower():
                target_chord = chord
                logger.info(f"   Найден аккорд: {chord['short_name']} (тип: {chord.get('type', 'Unknown')})")
                break

        if target_chord:
            # Извлекаем тональность из полного имени (A, Am, C# и т.д.)
            full_name = target_chord['name']
            # Разбираем имя: например "Am" -> тональность "A", тип "Minor"
            tonality = self._extract_tonality(full_name)

            # Определяем тип аккорда из METADATA
            chord_type = target_chord.get('type', 'Major')

            logger.info(f"   Тональность: {tonality}, Тип: {chord_type}")

            # Устанавливаем тональность
            if tonality in self.TONALITIES:
                self.current_tonality = tonality
                self.current_tonality_index = self.TONALITIES.index(tonality)
                self.tonality_card.update_value(self.current_tonality)

                # Устанавливаем тип аккорда
                if chord_type in self.CHORD_TYPES:
                    self.current_type = chord_type
                    self.current_type_index = self.CHORD_TYPES.index(chord_type)
                    self.type_card.update_value(self.current_type)

                # Обновляем список доступных аккордов
                self.update_available_chords()

                # Если аккорд есть в списке, выбираем его
                if chord_name in self.available_chords:
                    self.current_chord_name = chord_name
                    self.current_chord_index = self.available_chords.index(chord_name)
                    self.chord_card.update_value(self.current_chord_name)
                    self._load_variants_for_chord(self.current_chord_name)
                    self.load_current_variant()
                    logger.info(f"✅ Аккорд {chord_name} успешно загружен")
                else:
                    logger.warning(f"⚠️ Аккорд {chord_name} не найден в available_chords")
                    # Пробуем найти вариант в all_chords
                    self._find_and_load_chord_variant(target_chord)
            else:
                logger.warning(f"⚠️ Тональность {tonality} не найдена в списке")
        else:
            logger.warning(f"⚠️ Аккорд {chord_name} не найден в базе")
            notify.warning(f"Аккорд {chord_name} не найден")

    def _find_and_load_chord_variant(self, target_chord):
        """Находит и загружает вариант аккорда напрямую"""
        logger.info(f"🔍 _find_and_load_chord_variant для {target_chord['short_name']}")

        # Собираем все варианты этого аккорда
        variants = []
        for chord in self.all_chords:
            if chord['short_name'] == target_chord['short_name']:
                variants.append(chord)

        if variants:
            variants.sort(key=lambda x: x['variant'])
            self.current_variants = variants
            self.current_variant_index = 0
            self.current_position = 1
            self.position_card.update_value("1")
            self.current_chord_name = target_chord['short_name']
            self.chord_card.update_value(self.current_chord_name)
            self.load_current_variant()
            logger.info(f"✅ Загружен вариант аккорда {target_chord['short_name']}")
        else:
            logger.error(f"❌ Не найдено вариантов для {target_chord['short_name']}")

    def _extract_tonality(self, chord_name):
        """Извлекает тональность из названия аккорда"""
        if not chord_name:
            return ""
        # Ищем букву с возможным диезом/бемолем в начале
        match = re.match(r'^([A-H][#b]?)', chord_name)
        if match:
            return match.group(1)
        # Если не нашли, берём первый символ
        return chord_name[0] if chord_name else ""

