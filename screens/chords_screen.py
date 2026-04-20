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


class TonalityButton(ButtonBehavior, MDBoxLayout):
    def __init__(self, text, is_active=False, on_press_callback=None, **kwargs):
        super().__init__(**kwargs)
        self.btn_text = text
        self.on_press_callback = on_press_callback
        self.size_hint = (None, 1)
        self.width = dp(32)
        self.label = MDLabel(
            text=text,
            font_size=sp(13),
            halign="center",
            valign="middle",
            theme_text_color="Custom"
        )
        self.add_widget(self.label)
        self.set_active(is_active)
        self.bind(on_release=self._on_press)

    def set_active(self, is_active):
        if is_active:
            self.label.text_color = [1, 1, 1, 1]
            self.label.bold = True
        else:
            self.label.text_color = [1, 1, 1, 0.5]
            self.label.bold = False

    def _on_press(self, instance):
        if self.on_press_callback:
            self.on_press_callback(self.btn_text)


class TypeButton(ButtonBehavior, MDBoxLayout):
    def __init__(self, text, is_active=False, on_press_callback=None, **kwargs):
        super().__init__(**kwargs)
        self.btn_text = text
        self.on_press_callback = on_press_callback
        self.size_hint = (None, 1)
        self.width = dp(54)
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

    def set_active(self, is_active):
        if is_active:
            self.label.text_color = [1, 1, 1, 1]
            self.label.bold = True
        else:
            self.label.text_color = [1, 1, 1, 0.7]
            self.label.bold = False

    def _on_press(self, instance):
        if self.on_press_callback:
            self.on_press_callback(self.btn_text)


class ChordButton(ButtonBehavior, MDBoxLayout):
    def __init__(self, text, on_press_callback=None, **kwargs):
        super().__init__(**kwargs)
        self.btn_text = text
        self.on_press_callback = on_press_callback
        self.size_hint = (None, 1)
        self.width = dp(58)
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

    def _on_press(self, instance):
        if self.on_press_callback:
            self.on_press_callback(self.btn_text)


class PaginatedRow(MDBoxLayout):
    def __init__(self, title, items, items_per_page=0, on_item_selected=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = dp(50)
        self.spacing = dp(2)
        self.items = items
        self.items_per_page = items_per_page if items_per_page > 0 else len(items)
        self.current_page = 0
        self.on_item_selected = on_item_selected
        self.item_buttons = {}
        self.current_selected = None

        self.title_label = MDLabel(
            text=title,
            font_size=sp(10),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.6],
            size_hint_y=None,
            height=dp(18),
            halign="center"
        )
        self.add_widget(self.title_label)

        content_row = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(30), spacing=dp(2))

        self.prev_btn = MDIconButton(
            icon="chevron-left",
            size_hint=(None, None),
            size=(dp(26), dp(26)),
            on_release=self.prev_page
        )
        self.prev_btn.theme_icon_color = "Custom"
        self.prev_btn.icon_color = [1, 1, 1, 0.5]

        self.items_container = MDBoxLayout(
            orientation='horizontal',
            size_hint_x=0.82,
            spacing=dp(2)
        )

        self.next_btn = MDIconButton(
            icon="chevron-right",
            size_hint=(None, None),
            size=(dp(26), dp(26)),
            on_release=self.next_page
        )
        self.next_btn.theme_icon_color = "Custom"
        self.next_btn.icon_color = [1, 1, 1, 0.5]

        content_row.add_widget(self.prev_btn)
        content_row.add_widget(self.items_container)
        content_row.add_widget(self.next_btn)

        self.add_widget(content_row)
        self._update_display()

    def _update_display(self):
        self.items_container.clear_widgets()
        self.item_buttons.clear()
        if not self.items:
            empty_label = MDLabel(
                text="—",
                size_hint_x=1,
                theme_text_color="Custom",
                text_color=[1, 1, 1, 0.4],
                font_size=sp(11),
                halign="center"
            )
            self.items_container.add_widget(empty_label)
            self.prev_btn.disabled = True
            self.next_btn.disabled = True
            return

        total_pages = (len(self.items) + self.items_per_page - 1) // self.items_per_page
        if total_pages <= 1:
            self.prev_btn.opacity = 0
            self.next_btn.opacity = 0
            self.prev_btn.disabled = True
            self.next_btn.disabled = True
            self.items_container.size_hint_x = 1
        else:
            self.prev_btn.opacity = 1
            self.next_btn.opacity = 1
            self.items_container.size_hint_x = 0.82

        self.prev_btn.disabled = (self.current_page == 0)
        self.next_btn.disabled = (self.current_page >= total_pages - 1)

        prev_color = [1, 1, 1, 0.2] if self.prev_btn.disabled else [1, 1, 1, 0.5]
        next_color = [1, 1, 1, 0.2] if self.next_btn.disabled else [1, 1, 1, 0.5]
        self.prev_btn.icon_color = prev_color
        self.next_btn.icon_color = next_color

        start_idx = self.current_page * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, len(self.items))

        for i in range(start_idx, end_idx):
            item = self.items[i]
            btn = self._create_item_button(item)
            self.items_container.add_widget(btn)
            self.item_buttons[item] = btn

    def _create_item_button(self, item):
        return TonalityButton(
            text=item,
            is_active=(item == self.current_selected),
            on_press_callback=lambda x: self._on_item_press(x)
        )

    def _on_item_press(self, item):
        self.current_selected = item
        for btn_text, btn in self.item_buttons.items():
            if hasattr(btn, 'set_active'):
                btn.set_active(btn_text == item)
        if self.on_item_selected:
            self.on_item_selected(item)

    def prev_page(self, instance):
        if self.current_page > 0:
            self.current_page -= 1
            self._update_display()

    def next_page(self, instance):
        total_pages = (len(self.items) + self.items_per_page - 1) // self.items_per_page
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self._update_display()

    def set_selected(self, item):
        self.current_selected = item
        self._update_display()

    def set_items(self, items):
        self.items = items
        self.current_page = 0
        self._update_display()


class TypeRow(PaginatedRow):
    def __init__(self, items, on_item_selected=None, **kwargs):
        super().__init__(
            title="Тип аккорда",
            items=items,
            items_per_page=6,
            on_item_selected=on_item_selected,
            **kwargs
        )

    def _create_item_button(self, item):
        return TypeButton(
            text=item,
            is_active=(item == self.current_selected),
            on_press_callback=lambda x: self._on_item_press(x)
        )


class ChordsRow(PaginatedRow):
    def __init__(self, on_item_selected=None, **kwargs):
        super().__init__(
            title="Аккорды",
            items=[],
            items_per_page=6,
            on_item_selected=on_item_selected,
            **kwargs
        )
        self.chords_data = {}

    def _create_item_button(self, item):
        return ChordButton(
            text=item,
            on_press_callback=lambda x: self._on_item_press(x)
        )

    def set_chords(self, chords_list):
        self.items = [chord['short_name'] for chord in chords_list]
        self.chords_data = {chord['short_name']: chord for chord in chords_list}
        self.current_page = 0
        self._update_display()

    def get_chord_data(self, chord_name):
        return self.chords_data.get(chord_name)


class ModeButton(ButtonBehavior, MDBoxLayout):
    def __init__(self, icon_name, is_active=False, on_press_callback=None, **kwargs):
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

        # Делаем фон экрана прозрачным
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

    def init_ui(self):
        from kivy.uix.scrollview import ScrollView
        from kivy.uix.widget import Widget

        scroll = ScrollView(size_hint=(1, 1))

        # Основной контейнер
        main_layout = MDBoxLayout(
            orientation='vertical',
            padding=[dp(12), dp(2), dp(12), dp(8)],
            spacing=dp(6),
            size_hint_y=None
        )
        main_layout.bind(minimum_height=main_layout.setter('height'))

        # Отступ сверху (чтобы не перекрывать верхние иконки)
        top_spacer = Widget(size_hint_y=None, height=dp(65))
        main_layout.add_widget(top_spacer)

        # Поисковая строка (как в songs_screen)
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

        # Тональности
        self.tonality_row = PaginatedRow(
            title="Тональность",
            items=TONALITIES,
            items_per_page=12,
            on_item_selected=self.on_tonality_selected
        )
        main_layout.add_widget(self.tonality_row)

        # Типы аккордов
        self.type_row = TypeRow(
            items=CHORD_TYPES,
            on_item_selected=self.on_type_selected
        )
        main_layout.add_widget(self.type_row)

        # Доступные аккорды
        self.chords_row = ChordsRow(on_item_selected=self.on_chord_selected)
        main_layout.add_widget(self.chords_row)

        # Название аккорда
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
        main_layout.add_widget(self.chord_name_label)

        # Гриф
        griff_container = MDBoxLayout(
            size_hint=(1, None),
            height=dp(260),
            padding=[dp(8), dp(4), dp(8), dp(4)]
        )
        self.chord_renderer = ChordRenderer()
        griff_container.add_widget(self.chord_renderer)
        main_layout.add_widget(griff_container)

        # Описание аккорда
        self.chord_desc_label = MDLabel(
            text="",
            halign="center",
            font_size=sp(8),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.6],
            size_hint_y=None,
            height=dp(20)
        )
        main_layout.add_widget(self.chord_desc_label)

        # Нижняя панель управления
        bottom_layout = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(52),
            spacing=dp(12),
            padding=[dp(16), dp(4), dp(16), dp(4)]
        )

        self.finger_btn = ModeButton(
            icon_name="fingers_png",
            on_press_callback=lambda x: self.set_mode("finger")
        )
        bottom_layout.add_widget(self.finger_btn)

        self.note_btn = ModeButton(
            icon_name="notes_png",
            on_press_callback=lambda x: self.set_mode("note")
        )
        bottom_layout.add_widget(self.note_btn)

        bottom_layout.add_widget(MDBoxLayout(size_hint_x=0.25))

        self.prev_variant_btn = MDIconButton(
            icon="chevron-left",
            on_release=self.prev_variant,
            size_hint=(None, None),
            size=(dp(36), dp(36))
        )
        self.prev_variant_btn.theme_icon_color = "Custom"
        self.prev_variant_btn.icon_color = [1, 1, 1, 0.7]
        bottom_layout.add_widget(self.prev_variant_btn)

        self.variant_label = MDLabel(
            text="1/1",
            halign="center",
            size_hint_x=0.18,
            font_size=sp(11),
            bold=True,
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1]
        )
        bottom_layout.add_widget(self.variant_label)

        self.next_variant_btn = MDIconButton(
            icon="chevron-right",
            on_release=self.next_variant,
            size_hint=(None, None),
            size=(dp(36), dp(36))
        )
        self.next_variant_btn.theme_icon_color = "Custom"
        self.next_variant_btn.icon_color = [1, 1, 1, 0.7]
        bottom_layout.add_widget(self.next_variant_btn)

        main_layout.add_widget(bottom_layout)

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

    def on_search_submit(self, instance):
        """Обработчик поиска"""
        query = self.search_field.text.strip()
        if not query:
            return
        self.clear_search_btn.opacity = 1
        self.search_chord(query)

    def clear_search(self, instance):
        """Очищает поиск"""
        self.search_field.text = ""
        self.clear_search_btn.opacity = 0
        # Возвращаемся к текущему аккорду
        if self.current_tonality and self.current_type:
            self.update_chords_list()
            if self.chords_row.items:
                self.on_chord_selected(self.chords_row.items[0])

    def search_chord(self, query):
        """Поиск аккорда"""
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
        self.load_current_variant()

    def load_current_variant(self):
        if not self.current_variants:
            return
        variant = self.current_variants[self.current_variant_index]
        self.current_chord_module = variant['module']
        self.chord_name_label.text = variant['name'].replace('|', ' | ')
        self.chord_desc_label.text = variant.get('description', '')
        self.variant_label.text = f"{self.current_variant_index + 1}/{len(self.current_variants)}"
        if hasattr(self, 'chord_renderer'):
            self.chord_renderer.load_chord(self.current_chord_module)
            self.chord_renderer.set_mode(self.current_mode)

    def prev_variant(self, instance):
        if self.current_variants and len(self.current_variants) > 1:
            self.current_variant_index = (self.current_variant_index - 1) % len(self.current_variants)
            self.load_current_variant()

    def next_variant(self, instance):
        if self.current_variants and len(self.current_variants) > 1:
            self.current_variant_index = (self.current_variant_index + 1) % len(self.current_variants)
            self.load_current_variant()

    def set_mode(self, mode):
        self.current_mode = mode
        if self.current_chord_module and hasattr(self, 'chord_renderer'):
            self.chord_renderer.set_mode(mode)

    def on_tonality_selected(self, tonality):
        self.current_tonality = tonality
        self.tonality_row.set_selected(tonality)
        self.update_chords_list()
        if self.chords_row.items:
            self.on_chord_selected(self.chords_row.items[0])

    def on_type_selected(self, chord_type):
        self.current_type = chord_type
        self.type_row.set_selected(chord_type)
        self.update_chords_list()
        if self.chords_row.items:
            self.on_chord_selected(self.chords_row.items[0])

    def on_pre_enter(self):
        self.update_chords_list()
        if self.chords_row.items:
            self.on_chord_selected(self.chords_row.items[0])
        return super().on_pre_enter()