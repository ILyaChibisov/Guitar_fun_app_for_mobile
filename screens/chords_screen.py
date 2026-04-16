# screens/chords_screen.py
"""
Экран гитарных аккордов
Использует спрайты для отображения нот и пальцев
"""
from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.textfield import MDTextField
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.button import MDIconButton
from kivy.animation import Animation
from kivy.metrics import dp, sp
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.utils import rgba
from kivy.uix.gridlayout import GridLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.core.window import Window
from kivy.uix.image import Image
from io import BytesIO

from config.theme import theme
from config.logger_config import screen_logger
from utils.notifications import notify
from utils.kivy_imports import MDRaisedButton
from screens.chord_renderer import ChordRenderer

import os
import importlib.util
import re

logger = screen_logger('Chords')

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


class SquareButton(ButtonBehavior, MDBoxLayout):
    def __init__(self, text, is_active=False, on_press_callback=None, **kwargs):
        super().__init__(**kwargs)
        self.btn_text = text
        self.on_press_callback = on_press_callback
        self.orientation = 'vertical'
        self.size_hint = (None, 1)
        self.width = dp(44)
        self.height = dp(38)
        self.padding = [dp(2), dp(2), dp(2), dp(2)]

        with self.canvas.before:
            self.bg_color = Color(*rgba(theme.SURFACE))
            self.bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(6)])

        self.label = MDLabel(
            text=text,
            font_size=sp(12),
            halign="center",
            valign="middle",
            theme_text_color="Custom",
            bold=True
        )
        self.add_widget(self.label)

        self.bind(pos=self._update_bg, size=self._update_bg)
        self.set_active(is_active)
        self.bind(on_release=self._on_press)

    def _update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def set_active(self, is_active):
        if is_active:
            self.bg_color.rgba = rgba(theme.PRIMARY)
            self.label.text_color = [1, 1, 1, 1]
            self.label.bold = True
        else:
            self.bg_color.rgba = rgba(theme.SURFACE)
            self.label.text_color = theme.TEXT_PRIMARY
            self.label.bold = False

    def _on_press(self, instance):
        if self.on_press_callback:
            self.on_press_callback(self.btn_text)


class TypeButton(ButtonBehavior, MDBoxLayout):
    def __init__(self, text, is_active=False, on_press_callback=None, **kwargs):
        super().__init__(**kwargs)
        self.btn_text = text
        self.on_press_callback = on_press_callback
        self.orientation = 'vertical'
        self.size_hint = (None, 1)
        self.width = dp(85)
        self.padding = [dp(4), dp(4), dp(4), dp(4)]

        with self.canvas.before:
            self.bg_color = Color(*rgba(theme.SURFACE))
            self.bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(6)])

        self.label = MDLabel(
            text=text,
            font_size=sp(10),
            halign="center",
            valign="middle",
            theme_text_color="Custom"
        )
        self.add_widget(self.label)

        self.bind(pos=self._update_bg, size=self._update_bg)
        self.set_active(is_active)
        self.bind(on_release=self._on_press)

    def _update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def set_active(self, is_active):
        if is_active:
            self.bg_color.rgba = rgba(theme.PRIMARY)
            self.label.text_color = [1, 1, 1, 1]
            self.label.bold = True
        else:
            self.bg_color.rgba = rgba(theme.SURFACE)
            self.label.text_color = theme.TEXT_PRIMARY
            self.label.bold = False

    def _on_press(self, instance):
        if self.on_press_callback:
            self.on_press_callback(self.btn_text)


class ChordButton(ButtonBehavior, MDBoxLayout):
    def __init__(self, chord_name, chord_variants, **kwargs):
        super().__init__(**kwargs)
        self.chord_name = chord_name
        self.chord_variants = chord_variants
        self.orientation = 'vertical'
        self.size_hint = (None, 1)
        self.width = dp(60)
        self.padding = [dp(4), dp(4), dp(4), dp(4)]

        print(f"DEBUG BUTTON INIT: {chord_name} получил {len(chord_variants)} вариантов")

        with self.canvas.before:
            self.bg_color = Color(*rgba(theme.SURFACE))
            self.bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(6)])

        self.label = MDLabel(
            text=chord_name.replace('$', '/'),
            font_size=sp(11),
            halign="center",
            theme_text_color="Custom",
            text_color=theme.TEXT_PRIMARY,
            bold=True
        )
        self.add_widget(self.label)

        self.bind(pos=self._update_bg, size=self._update_bg)

    def _update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size


class PaginatedTypeSelector(MDBoxLayout):
    def __init__(self, items, items_per_page=4, on_item_selected=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = dp(65)
        self.spacing = dp(5)

        self.items = items
        self.items_per_page = items_per_page
        self.current_page = 0
        self.on_item_selected = on_item_selected
        self.type_buttons = {}
        self.current_selected = None

        self._setup_ui()
        self._update_display()

    def _setup_ui(self):
        pagination_bar = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(28), spacing=dp(8))

        self.prev_btn = MDIconButton(icon="chevron-left", on_release=self.prev_page, size_hint=(None, None),
                                     size=(dp(28), dp(28)))
        self.prev_btn.icon_color = theme.PRIMARY
        self.prev_btn.theme_icon_color = "Custom"

        self.page_indicator = MDLabel(text="", halign="center", font_size=sp(10), size_hint_x=0.5,
                                      theme_text_color="Secondary")

        self.next_btn = MDIconButton(icon="chevron-right", on_release=self.next_page, size_hint=(None, None),
                                     size=(dp(28), dp(28)))
        self.next_btn.icon_color = theme.PRIMARY
        self.next_btn.theme_icon_color = "Custom"

        pagination_bar.add_widget(self.prev_btn)
        pagination_bar.add_widget(self.page_indicator)
        pagination_bar.add_widget(self.next_btn)
        self.add_widget(pagination_bar)

        self.buttons_container = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(34), spacing=dp(5),
                                             padding=[dp(4), 0, dp(4), 0])
        self.add_widget(self.buttons_container)

    def _update_display(self):
        self.buttons_container.clear_widgets()

        total_pages = (len(self.items) + self.items_per_page - 1) // self.items_per_page
        self.page_indicator.text = f"{self.current_page + 1} / {total_pages}"

        self.prev_btn.disabled = (self.current_page == 0)
        self.next_btn.disabled = (self.current_page >= total_pages - 1)

        self.prev_btn.icon_color = theme.TEXT_SECONDARY if self.prev_btn.disabled else theme.PRIMARY
        self.next_btn.icon_color = theme.TEXT_SECONDARY if self.next_btn.disabled else theme.PRIMARY

        start_idx = self.current_page * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, len(self.items))

        for i in range(start_idx, end_idx):
            item = self.items[i]
            btn = TypeButton(text=item, is_active=(item == self.current_selected),
                             on_press_callback=self._on_item_press)
            self.buttons_container.add_widget(btn)
            self.type_buttons[item] = btn

        items_on_page = end_idx - start_idx
        for _ in range(self.items_per_page - items_on_page):
            self.buttons_container.add_widget(MDBoxLayout(size_hint_x=1))

    def _on_item_press(self, item):
        self.current_selected = item
        for btn_text, btn in self.type_buttons.items():
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

        self.init_ui()
        self.scan_chords()

        logger.info('Экран аккордов создан')

    def init_ui(self):
        from kivy.uix.scrollview import ScrollView

        with self.canvas.before:
            Color(*rgba(theme.BACKGROUND))
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

        scroll = ScrollView(size_hint=(1, 1))
        main_layout = MDBoxLayout(orientation='vertical', padding=dp(8), spacing=dp(6), size_hint_y=None)
        main_layout.bind(minimum_height=main_layout.setter('height'))

        # ===== Поиск =====
        search_layout = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(44), spacing=dp(8))
        self.search_field = MDTextField(hint_text="Поиск аккорда (например: A, C#m, Bb...)", mode="filled",
                                        size_hint_x=0.8, font_size=dp(12))
        self.search_btn = MDRaisedButton(text="Найти", size_hint_x=0.2, on_release=self.on_search)
        self.search_btn.radius = [theme.CORNER_RADIUS_SMALL] * 4
        search_layout.add_widget(self.search_field)
        search_layout.add_widget(self.search_btn)
        main_layout.add_widget(search_layout)

        # ===== Тональности =====
        tonality_label = MDLabel(text="Выберите тональность", halign="center", size_hint_y=None, height=dp(24),
                                 font_size=sp(12), bold=True, theme_text_color="Primary")
        main_layout.add_widget(tonality_label)

        tonality_scroll = ScrollView(size_hint_y=None, height=dp(46), do_scroll_x=True, do_scroll_y=False)
        self.tonality_container = MDBoxLayout(orientation='horizontal', size_hint_x=None, spacing=dp(4),
                                              padding=[dp(6), 0, dp(6), 0])
        self.tonality_container.bind(minimum_width=self.tonality_container.setter('width'))

        self.tonality_buttons = {}
        for tonality in TONALITIES:
            btn = SquareButton(text=tonality, is_active=(tonality == self.current_tonality),
                               on_press_callback=self.on_tonality_selected)
            self.tonality_container.add_widget(btn)
            self.tonality_buttons[tonality] = btn

        tonality_scroll.add_widget(self.tonality_container)
        main_layout.add_widget(tonality_scroll)

        # ===== Типы аккордов =====
        type_label = MDLabel(text="Выберите тип аккорда", halign="center", size_hint_y=None, height=dp(24),
                             font_size=sp(12), bold=True, theme_text_color="Primary")
        main_layout.add_widget(type_label)

        self.type_selector = PaginatedTypeSelector(items=CHORD_TYPES, items_per_page=4,
                                                   on_item_selected=self.on_type_selected)
        main_layout.add_widget(self.type_selector)

        # ===== Название аккорда =====
        self.chord_name_label = MDLabel(text="Выберите аккорд", halign="center", font_size=sp(16), bold=True,
                                        size_hint_y=None, height=dp(36), theme_text_color="Primary")
        main_layout.add_widget(self.chord_name_label)

        # ===== Описание аккорда =====
        self.chord_desc_label = MDLabel(text="", halign="center", font_size=sp(10), theme_text_color="Secondary",
                                        size_hint_y=None, height=dp(30))
        main_layout.add_widget(self.chord_desc_label)

        # ===== ГРИФ С НОТАМИ =====
        griff_container = MDBoxLayout(
            size_hint=(1, None),
            height=dp(280),
            padding=[dp(8), dp(8), dp(8), dp(8)]
        )

        self.chord_renderer = ChordRenderer()
        griff_container.add_widget(self.chord_renderer)
        main_layout.add_widget(griff_container)

        # Загружаем фон грифа
        try:
            from data import load_asset_as_bytes
            from kivy.core.image import Image as CoreImage

            bg_data = load_asset_as_bytes("griff_png")
            if bg_data:
                img = CoreImage(BytesIO(bg_data), ext="png")
                self.chord_renderer.set_background(img.texture)
                logger.info("Фон грифа загружен")
            else:
                logger.warning("Фон грифа не найден")
        except Exception as e:
            logger.error(f"Ошибка загрузки фона: {e}")

        # ===== Панель управления =====
        bottom_layout = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50), spacing=dp(8),
                                    padding=[dp(4), dp(4), dp(4), dp(4)])

        # Кнопки режима
        self.finger_btn = MDRaisedButton(text="🖐 Пальцы", on_release=lambda x: self.set_mode("finger"))
        self.finger_btn.radius = [theme.CORNER_RADIUS_SMALL] * 4
        self.finger_btn.md_bg_color = theme.PRIMARY
        bottom_layout.add_widget(self.finger_btn)

        self.note_btn = MDRaisedButton(text="♪ Ноты", on_release=lambda x: self.set_mode("note"))
        self.note_btn.radius = [theme.CORNER_RADIUS_SMALL] * 4
        self.note_btn.md_bg_color = theme.TEXT_SECONDARY
        bottom_layout.add_widget(self.note_btn)

        # Кнопки навигации по вариантам
        self.prev_btn = MDIconButton(
            icon="chevron-left",
            on_release=self.prev_variant,
            size_hint=(None, None),
            size=(dp(40), dp(40))
        )
        bottom_layout.add_widget(self.prev_btn)

        self.variant_label = MDLabel(
            text="Вариант 1",
            halign="center",
            size_hint_x=0.25,
            font_size=sp(12),
            bold=True
        )
        bottom_layout.add_widget(self.variant_label)

        self.next_btn = MDIconButton(
            icon="chevron-right",
            on_release=self.next_variant,
            size_hint=(None, None),
            size=(dp(40), dp(40))
        )
        bottom_layout.add_widget(self.next_btn)

        main_layout.add_widget(bottom_layout)

        # ===== Список аккордов =====
        chords_label = MDLabel(text="Доступные аккорды:", halign="center", size_hint_y=None, height=dp(24),
                               font_size=sp(11), bold=True, theme_text_color="Primary")
        main_layout.add_widget(chords_label)

        self.chords_scroll = ScrollView(size_hint_y=None, height=dp(46), do_scroll_x=True, do_scroll_y=False)
        self.chords_container = MDBoxLayout(orientation='horizontal', size_hint_x=None, spacing=dp(6),
                                            padding=[dp(6), 0, dp(6), 0])
        self.chords_container.bind(minimum_width=self.chords_container.setter('width'))
        self.chords_scroll.add_widget(self.chords_container)
        main_layout.add_widget(self.chords_scroll)

        scroll.add_widget(main_layout)
        self.add_widget(scroll)

    def _update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def scan_chords(self):
        """Сканирует папку chords и загружает аккорды"""
        chords_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'chords')
        if not os.path.exists(chords_dir):
            os.makedirs(chords_dir, exist_ok=True)
            logger.warning(f"Папка аккордов создана: {chords_dir}")
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

                        # Извлекаем номер варианта из имени файла
                        import re
                        variant_match = re.search(r'_(\d+)\.py$', f)
                        if variant_match:
                            variant_num = int(variant_match.group(1))
                        else:
                            variant_num = metadata.get('variant', 1)

                        chord_id = f"{chord_name}_v{variant_num}"

                        self.all_chords.append({
                            'id': chord_id,
                            'name': chord_name,
                            'variant': variant_num,
                            'type': metadata.get('type', ''),
                            'description': metadata.get('description', ''),
                            'path': full_path,
                            'module': module
                        })
                        print(f"DEBUG SCAN: Загружен {chord_name} вариант {variant_num} из {f}")
                    except Exception as e:
                        logger.error(f"Ошибка загрузки {f}: {e}")

        print(f"DEBUG SCAN: Всего загружено аккордов: {len(self.all_chords)}")
        self.update_chords_list()
        self.load_first_chord()

    def update_chords_list(self):
        """Обновляет список кнопок аккордов по текущим фильтрам"""
        self.chords_container.clear_widgets()

        filtered = []
        for chord in self.all_chords:
            tonality = self.extract_tonality(chord['name'])
            if tonality != self.current_tonality:
                continue
            chord_types = chord['type'].split('|') if chord['type'] else []
            if self.current_type not in chord_types:
                continue
            filtered.append(chord)

        print(f"DEBUG UPDATE: Найдено аккордов для {self.current_tonality}/{self.current_type}: {len(filtered)}")

        if not filtered:
            no_chords = MDLabel(text="Нет аккордов", size_hint_x=None, width=dp(100))
            self.chords_container.add_widget(no_chords)
            return

        # Группируем по имени аккорда
        chords_by_name = {}
        for chord in filtered:
            name = chord['name']
            if name not in chords_by_name:
                chords_by_name[name] = []
            chords_by_name[name].append(chord)

        for name, variants in chords_by_name.items():
            variants.sort(key=lambda x: x['variant'])
            print(f"DEBUG UPDATE: {name} - {len(variants)} вариантов")

            short_name = name.split('|')[0]
            btn = ChordButton(
                chord_name=short_name,
                chord_variants=variants
            )
            # ВАЖНО: используем bind с фиксацией variants
            btn.bind(on_release=lambda x, v=variants: self.load_chord_variants(v))
            self.chords_container.add_widget(btn)

        self.chords_container.add_widget(MDBoxLayout(size_hint_x=None, width=dp(8)))

    def on_chord_button_press(self, instance):
        """Обработчик нажатия на кнопку аккорда"""
        print(f"DEBUG PRESS: Нажата кнопка {instance.chord_name}")
        print(f"DEBUG PRESS: variants_data = {getattr(instance, 'variants_data', None)}")
        if hasattr(instance, 'variants_data'):
            variants = instance.variants_data
            print(f"DEBUG PRESS: передаю {len(variants)} вариантов")
            self.load_chord_variants(variants)
        else:
            print("DEBUG PRESS: Нет variants_data!")

    def extract_tonality(self, chord_name):
        if not chord_name:
            return ""
        if '|' in chord_name:
            main_name = chord_name.split('|')[0]
        else:
            main_name = chord_name
        match = re.match(r'^([A-H][#b]?)', main_name)
        if match:
            return match.group(1)
        return main_name[0] if main_name else ""

    def load_first_chord(self):
        """Загружает первый аккорд из текущего списка со ВСЕМИ вариантами"""
        # Находим первое имя аккорда, подходящее под фильтры
        first_chord_name = None

        for chord in self.all_chords:
            tonality = self.extract_tonality(chord['name'])
            if tonality != self.current_tonality:
                continue
            chord_types = chord['type'].split('|') if chord['type'] else []
            if self.current_type not in chord_types:
                continue
            first_chord_name = chord['name']
            break

        if first_chord_name is None:
            print("DEBUG FIRST: Не найдено подходящих аккордов")
            return

        # Собираем ВСЕ варианты этого аккорда
        all_variants = []
        for chord in self.all_chords:
            if chord['name'] == first_chord_name:
                all_variants.append(chord)

        all_variants.sort(key=lambda x: x['variant'])
        print(f"DEBUG FIRST: Загружаю первый аккорд {first_chord_name} с {len(all_variants)} вариантами")
        self.load_chord_variants(all_variants)

    def load_chord_variants(self, variants):
        """Загружает варианты аккорда"""
        print(f"DEBUG LOAD: Получено variants типа {type(variants)}")
        print(f"DEBUG LOAD: Длина: {len(variants) if variants else 0}")

        if not variants:
            print("DEBUG LOAD: variants пуст!")
            return

        # Если variants - список, и первый элемент - тоже список
        if isinstance(variants, list) and len(variants) > 0:
            if isinstance(variants[0], list):
                variants = variants[0]
                print(f"DEBUG LOAD: Распакован вложенный список, теперь {len(variants)} вариантов")

        # Если variants - это не список, а словарь
        if isinstance(variants, dict):
            # Преобразуем значения словаря в список
            variants = list(variants.values())
            print(f"DEBUG LOAD: Преобразован словарь в список, {len(variants)} вариантов")

        # Проверяем, что все элементы - словари с ключом 'variant'
        if isinstance(variants, list) and len(variants) > 0:
            if not isinstance(variants[0], dict):
                print(f"DEBUG LOAD: Ошибка! Первый элемент не словарь, а {type(variants[0])}")
                return

        variants.sort(key=lambda x: x['variant'])
        self.current_variants = variants
        self.current_variant_index = 0
        print(f"DEBUG LOAD: Загружено {len(variants)} вариантов")
        for v in variants:
            print(f"  - {v['name']} вариант {v['variant']}")
        self.load_current_variant()

    def load_current_variant(self):
        """Загружает текущий вариант аккорда"""
        if not self.current_variants:
            return

        variant = self.current_variants[self.current_variant_index]
        self.current_chord_module = variant['module']

        full_name = variant['name']
        display_name = full_name.replace('|', ' | ')
        self.chord_name_label.text = display_name
        self.chord_desc_label.text = variant.get('description', '')
        self.variant_label.text = f"Вариант {variant['variant']}"

        print(f"DEBUG CURRENT: Загружен вариант {variant['variant']} для {full_name}")
        print(f"DEBUG CURRENT: Индекс {self.current_variant_index} из {len(self.current_variants)}")

        if hasattr(self, 'chord_renderer'):
            self.chord_renderer.load_chord(self.current_chord_module)
            self.chord_renderer.set_mode(self.current_mode)
        else:
            print("DEBUG: chord_renderer не найден!")

    def prev_variant(self, instance):
        """Предыдущий вариант"""
        if self.current_variants and len(self.current_variants) > 1:
            old_index = self.current_variant_index
            self.current_variant_index = (self.current_variant_index - 1) % len(self.current_variants)
            print(f"DEBUG PREV: Переключение с варианта {old_index + 1} на {self.current_variant_index + 1}")
            self.load_current_variant()
        else:
            print(
                f"DEBUG PREV: Нет других вариантов (всего {len(self.current_variants) if self.current_variants else 0})")

    def next_variant(self, instance):
        """Следующий вариант"""
        if self.current_variants and len(self.current_variants) > 1:
            old_index = self.current_variant_index
            self.current_variant_index = (self.current_variant_index + 1) % len(self.current_variants)
            print(f"DEBUG NEXT: Переключение с варианта {old_index + 1} на {self.current_variant_index + 1}")
            self.load_current_variant()
        else:
            print(
                f"DEBUG NEXT: Нет других вариантов (всего {len(self.current_variants) if self.current_variants else 0})")

    def set_mode(self, mode):
        """Устанавливает режим отображения"""
        print(f"DEBUG: Смена режима на {mode}")
        self.current_mode = mode
        if mode == "finger":
            self.finger_btn.md_bg_color = theme.PRIMARY
            self.note_btn.md_bg_color = theme.TEXT_SECONDARY
        else:
            self.finger_btn.md_bg_color = theme.TEXT_SECONDARY
            self.note_btn.md_bg_color = theme.PRIMARY

        # Обновляем отображение для текущего аккорда
        if self.current_chord_module and hasattr(self, 'chord_renderer'):
            self.chord_renderer.set_mode(mode)

    def on_tonality_selected(self, tonality):
        print(f"DEBUG: Выбрана тональность {tonality}")
        self.current_tonality = tonality
        for t, btn in self.tonality_buttons.items():
            btn.set_active(t == tonality)
        self.update_chords_list()
        self.load_first_chord()

    def on_type_selected(self, chord_type):
        print(f"DEBUG: Выбран тип {chord_type}")
        self.current_type = chord_type
        self.type_selector.set_selected(chord_type)
        self.update_chords_list()
        self.load_first_chord()

    def on_search(self, instance):
        search_text = self.search_field.text.strip()
        if not search_text:
            return
        search_normalized = search_text.lower().replace('/', '$')

        found_chord = None
        for chord in self.all_chords:
            name = chord['name'].lower()
            name_normalized = name.replace('/', '$')
            if search_normalized == name_normalized:
                found_chord = chord
                break
            if '|' in name:
                for alt in name.split('|'):
                    alt_normalized = alt.strip().replace('/', '$')
                    if search_normalized == alt_normalized:
                        found_chord = chord
                        break
                if found_chord:
                    break

        if found_chord:
            print(f"DEBUG SEARCH: Найден аккорд {found_chord['name']}")

            # Собираем ВСЕ варианты найденного аккорда
            all_variants = []
            for chord in self.all_chords:
                if chord['name'] == found_chord['name']:
                    all_variants.append(chord)

            all_variants.sort(key=lambda x: x['variant'])

            tonality = self.extract_tonality(found_chord['name'])
            self.on_tonality_selected(tonality)
            chord_types = found_chord['type'].split('|') if found_chord['type'] else []
            if chord_types:
                self.on_type_selected(chord_types[0])

            self.load_chord_variants(all_variants)  # ← передаём ВСЕ варианты
            self.search_field.text = ""
        else:
            notify.warning(f"Аккорд '{search_text}' не найден")

    def on_pre_enter(self):
        self.update_chords_list()
        self.load_first_chord()
        return super().on_pre_enter()