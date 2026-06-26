# screens/songs_screen.py
"""
Экран песен с алфавитной навигацией и современным поиском - результаты на том же экране
"""
import time

from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDIconButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.metrics import dp, sp
from kivy.graphics import Color, Rectangle
from kivy.core.image import Image as CoreImage
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.properties import StringProperty, NumericProperty, ObjectProperty
from kivy.clock import Clock
from io import BytesIO
from kivy.uix.floatlayout import FloatLayout

from config.theme import theme
from config.logger_config import screen_logger
from config.layout_config import layout_config
from config.system_bars import get_navigation_bar_height
from screens.base_screen import BaseScreen
from api.client import api
from utils.notifications import notify

logger = screen_logger('Songs')

try:
    from data import load_asset_as_bytes

    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False


    def load_asset_as_bytes(name):
        return None

# ============ ГЛОБАЛЬНАЯ ИКОНКА ДЛЯ КАРТОЧЕК ============
_shared_song_icon_texture = None


def init_shared_song_icon():
    global _shared_song_icon_texture
    if _shared_song_icon_texture is not None:
        return _shared_song_icon_texture

    if HAS_ASSETS:
        try:
            icon_data = load_asset_as_bytes('song_png')
            if icon_data:
                img = CoreImage(BytesIO(icon_data), ext="png")
                _shared_song_icon_texture = img.texture
                logger.info("✅ Общая иконка песни загружена")
                return _shared_song_icon_texture
        except Exception as e:
            logger.error(f"Ошибка загрузки иконки song_png: {e}")
    return None


class LetterButton(ButtonBehavior, MDBoxLayout):
    """Кнопка буквы для сетки"""

    def __init__(self, text, is_active=False, on_press_callback=None, **kwargs):
        super().__init__(**kwargs)
        self.btn_text = text
        self.on_press_callback = on_press_callback
        self.size_hint = (1, 1)
        self.padding = [dp(1), dp(1), dp(1), dp(1)]

        self.main_layout = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            padding=[dp(4), dp(2), dp(4), dp(2)]
        )

        if text == '09':
            display_text = '0-9'
            font_size = sp(10)
        else:
            display_text = text
            font_size = sp(13)

        self.label = MDLabel(
            text=display_text,
            font_size=font_size,
            halign="center",
            valign="middle",
            theme_text_color="Custom",
            bold=True,
            size_hint=(1, 1),
            text_size=(None, None),
            shorten=False
        )
        self.main_layout.add_widget(self.label)
        self.add_widget(self.main_layout)

        self.is_active = is_active
        self.bind(on_release=self._on_press)
        self.update_style()

    def update_style(self):
        if self.is_active:
            self.label.text_color = [1, 1, 1, 1]
            self.main_layout.md_bg_color = [0.46, 0.70, 0.71, 1]
            self.main_layout.radius = [dp(8), dp(8), dp(8), dp(8)]
        else:
            self.label.text_color = [0.9, 0.95, 0.85, 0.9]
            self.main_layout.md_bg_color = [0.08, 0.22, 0.14, 0.6]
            self.main_layout.radius = [dp(6), dp(6), dp(6), dp(6)]

    def set_active(self, active):
        self.is_active = active
        self.update_style()

    def _on_press(self, instance):
        if self.on_press_callback:
            self.on_press_callback(self.btn_text)


class GoogleSearchBar(MDCard):
    """Поисковая строка - поиск ТОЛЬКО по нажатию на лупу или Enter"""

    def __init__(self, on_search=None, on_clear=None, **kwargs):
        super().__init__(**kwargs)
        self.on_search = on_search
        self.on_clear = on_clear

        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = dp(48)
        self.radius = [dp(24), dp(24), dp(24), dp(24)]
        self.md_bg_color = [0.96, 0.96, 0.96, 1]
        self.elevation = 0
        self.padding = [dp(16), dp(6), dp(12), dp(6)]
        self.spacing = dp(8)

        self.line_color = [0.46, 0.70, 0.71, 0.4]
        self.line_width = 1.0

        self.search_field = MDTextField(
            hint_text="Поиск",
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

    def _on_search(self, instance):
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


class LanguageSelector(MDBoxLayout):
    """Выбор языка - системные иконки стрелок, текст по центру"""

    def __init__(self, on_language_change=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.size_hint_x = 1
        self.height = dp(48)
        self.padding = [0, 0, 0, 0]

        self.on_language_change = on_language_change
        self.current_language = 'ru'

        self.languages = [
            {'code': 'ru', 'name': 'Русский'},
            {'code': 'en', 'name': 'English'}
        ]

        # Используем FloatLayout для точного центрирования
        self.float_layout = FloatLayout(size_hint=(1, 1))

        # --- СИСТЕМНЫЕ ИКОНКИ СТРЕЛОК ---
        self.prev_btn = MDIconButton(
            icon="chevron-left",
            size_hint=(None, None),
            size=(dp(32), dp(32)),
            theme_icon_color="Custom",
            icon_color=[1, 1, 1, 0.9],
            md_bg_color=[0, 0, 0, 0],
            on_release=self.prev_language,
            pos_hint={'center_x': 0.35, 'center_y': 0.5}
        )

        self.language_label = MDLabel(
            text="Русский",
            font_size=sp(18),
            halign="center",
            valign="middle",
            size_hint=(None, None),
            width=dp(120),
            height=dp(48),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
            bold=True,
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )

        self.next_btn = MDIconButton(
            icon="chevron-right",
            size_hint=(None, None),
            size=(dp(32), dp(32)),
            theme_icon_color="Custom",
            icon_color=[1, 1, 1, 0.9],
            md_bg_color=[0, 0, 0, 0],
            on_release=self.next_language,
            pos_hint={'center_x': 0.65, 'center_y': 0.5}
        )

        self.float_layout.add_widget(self.prev_btn)
        self.float_layout.add_widget(self.language_label)
        self.float_layout.add_widget(self.next_btn)

        self.add_widget(self.float_layout)

        self._update_display()

    def _update_display(self):
        for lang in self.languages:
            if lang['code'] == self.current_language:
                self.language_label.text = lang['name']
                break

    def get_current_language(self):
        return self.current_language

    def prev_language(self, instance):
        current_index = 0 if self.current_language == 'ru' else 1
        new_index = (current_index - 1) % len(self.languages)
        self.current_language = self.languages[new_index]['code']
        self._update_display()
        if self.on_language_change:
            self.on_language_change(self.current_language)

    def next_language(self, instance):
        current_index = 0 if self.current_language == 'ru' else 1
        new_index = (current_index + 1) % len(self.languages)
        self.current_language = self.languages[new_index]['code']
        self._update_display()
        if self.on_language_change:
            self.on_language_change(self.current_language)

    def set_language(self, language):
        if self.current_language == language:
            return
        self.current_language = language
        self._update_display()


class AlphabetGrid(MDCard):
    """Сетка с буквами"""

    RU_LETTERS = ['А', 'Б', 'В', 'Г', 'Д', 'Е', 'Ё', 'Ж', 'З', 'И',
                  'Й', 'К', 'Л', 'М', 'Н', 'О', 'П', 'Р', 'С', 'Т',
                  'У', 'Ф', 'Х', 'Ц', 'Ч', 'Ш', 'Щ', 'Ъ', 'Ы', 'Ь',
                  'Э', 'Ю', 'Я', '#', '09']

    EN_LETTERS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J',
                  'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T',
                  'U', 'V', 'W', 'X', 'Y', 'Z', '#', '09']

    def __init__(self, on_letter_press=None, **kwargs):
        super().__init__(**kwargs)
        self.on_letter_press = on_letter_press
        self.current_language = 'ru'
        self.current_selected = None

        self.orientation = 'vertical'
        self.size_hint = (1, None)
        self.padding = [dp(6), dp(6), dp(6), dp(6)]
        self.radius = [dp(16), dp(16), dp(16), dp(16)]
        self.md_bg_color = [0.06, 0.18, 0.12, 0.92]
        self.line_color = [0.9, 0.9, 0.8, 0.15]
        self.line_width = 1
        self.elevation = 0

        self.rows = []
        self.buttons = []

        self._create_all_buttons()
        self._update_height()

    def _create_all_buttons(self):
        for i in range(5):
            row = MDBoxLayout(
                orientation='horizontal',
                spacing=dp(6),
                size_hint_y=None,
                height=dp(34)
            )
            self.rows.append(row)
            self.add_widget(row)

        max_buttons = len(self.RU_LETTERS)
        for i in range(max_buttons):
            btn = LetterButton(
                text="",
                is_active=False,
                on_press_callback=self._on_letter_press
            )
            self.buttons.append(btn)

        self._redistribute_buttons()

    def _redistribute_buttons(self):
        for row in self.rows:
            row.clear_widgets()

        if self.current_language == 'ru':
            items = self.RU_LETTERS
            rows_count = 5
        else:
            items = self.EN_LETTERS
            rows_count = 4

        for i, row in enumerate(self.rows):
            row.height = dp(34) if i < rows_count else 0
            row.opacity = 1 if i < rows_count else 0

        total_items = len(items)
        items_per_row = (total_items + rows_count - 1) // rows_count

        btn_index = 0
        for row_idx in range(rows_count):
            for col_idx in range(items_per_row):
                if btn_index < total_items:
                    btn = self.buttons[btn_index]
                    text = items[btn_index]
                    btn.btn_text = text
                    display_text = '0-9' if text == '09' else text
                    btn.label.text = display_text
                    btn.opacity = 1
                    btn.disabled = False
                    self.rows[row_idx].add_widget(btn)
                    btn_index += 1
                else:
                    spacer = MDBoxLayout(size_hint=(1, 1))
                    self.rows[row_idx].add_widget(spacer)

        for i in range(btn_index, len(self.buttons)):
            self.buttons[i].opacity = 0
            self.buttons[i].disabled = True

        self._update_height()

    def _update_height(self):
        if self.current_language == 'ru':
            self.height = dp(34) * 5 + dp(12)
        else:
            self.height = dp(34) * 4 + dp(12)

    def _on_letter_press(self, letter):
        self.current_selected = letter
        for btn in self.buttons:
            btn.set_active(btn.btn_text == letter)
        if self.on_letter_press:
            if letter == '09':
                self.on_letter_press('0-9')
            else:
                self.on_letter_press(letter)

    def set_language(self, language):
        if self.current_language == language:
            return
        self.current_language = language
        self.current_selected = None
        for btn in self.buttons:
            btn.set_active(False)
        self._redistribute_buttons()

    def clear_selection(self):
        self.current_selected = None
        for btn in self.buttons:
            btn.set_active(False)


# ============ RECYCLEVIEW ДЛЯ РЕЗУЛЬТАТОВ ПОИСКА ============

class SearchSongCard(RecycleDataViewBehavior, MDCard):
    """Карточка песни для RecycleView (результаты поиска)"""

    title = StringProperty('')
    artist = StringProperty('')
    song_id = NumericProperty(0)
    on_click = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = dp(56)
        self.padding = [dp(16), dp(10), dp(12), dp(10)]
        self.spacing = dp(12)
        self.radius = [theme.CORNER_RADIUS_SMALL] * 4
        self.elevation = 0
        self.ripple_behavior = True
        self.theme_bg_color = "Custom"
        self.md_bg_color = [0, 0, 0, 0.06]
        self.line_color = [1, 1, 1, 0.05]
        self.line_width = 0.5
        self._build_ui()

    def _build_ui(self):
        # Иконка
        self.icon = Image(
            size_hint=(None, 1),
            width=dp(30),
            allow_stretch=True,
            keep_ratio=True
        )
        if _shared_song_icon_texture:
            self.icon.texture = _shared_song_icon_texture
        else:
            self.icon.text = "🎵"

        # Текстовая часть
        text_layout = MDBoxLayout(
            orientation='vertical',
            size_hint_x=1,
            spacing=dp(2),
            pos_hint={'center_y': 0.5}
        )

        self.artist_label = MDLabel(
            font_size=sp(16),
            size_hint_y=None,
            height=dp(24),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.95],
            bold=True,
            shorten=True,
            shorten_from="right",
            valign="middle"
        )

        self.title_label = MDLabel(
            font_size=sp(12),
            size_hint_y=None,
            height=dp(18),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.5],
            valign="middle"
        )

        text_layout.add_widget(self.artist_label)
        text_layout.add_widget(self.title_label)

        # Стрелка
        arrow = MDLabel(
            text="›",
            font_size=sp(24),
            size_hint_x=None,
            width=dp(28),
            halign="center",
            valign="middle",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.3]
        )

        self.add_widget(self.icon)
        self.add_widget(text_layout)
        self.add_widget(arrow)

    def refresh_view_attrs(self, rv, index, data):
        self.title = data.get('title', '')
        self.artist = data.get('artist', '')
        self.song_id = data.get('song_id', 0)
        self.on_click = data.get('on_click')
        self.artist_label.text = self.artist
        self.title_label.text = self.title
        return super().refresh_view_attrs(rv, index, data)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if self.on_click:
                self.on_click(self.song_id, self.title)
            return True
        return super().on_touch_down(touch)


class SongRecycleView(RecycleView):
    """Виртуализированный список песен для поиска"""

    def __init__(self, on_song_click=None, **kwargs):
        super().__init__(**kwargs)
        self.on_song_click = on_song_click
        self.animate_scroll = False
        self.bar_width = 0
        self.bar_color = [0, 0, 0, 0]
        self.bar_inactive_color = [0, 0, 0, 0]

        self.layout_manager = RecycleBoxLayout(
            default_size=(None, dp(56)),
            default_size_hint=(1, None),
            size_hint_y=None,
            height=dp(56) * 10,
            orientation='vertical',
            spacing=dp(6)
        )
        self.layout_manager.bind(minimum_height=self.layout_manager.setter('height'))
        self.viewclass = 'SearchSongCard'
        self.add_widget(self.layout_manager)

    def set_songs(self, songs, on_click):
        data = []
        for song in songs:
            data.append({
                'song_id': song.get('song_id', 0),
                'title': song.get('title', ''),
                'artist': song.get('artist', ''),
                'on_click': on_click
            })
        self.data = data
        self.refresh_from_data()

    def clear(self):
        """Очищает список"""
        self.data = []
        self.refresh_from_data()


class SongsScreen(BaseScreen):
    """Экран песен с алфавитной навигацией - результаты поиска на том же экране"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'songs'
        self.current_letter = None
        self.is_search_mode = False
        self.search_results = []

        self.language_selector = None
        self.alphabet_grid = None
        self.hint_label = None
        self.top_container = None
        self.keyboard_container = None
        self._keyboard_height = 0
        self.cards_container = None

        self.init_ui()
        Clock.schedule_once(lambda dt: init_shared_song_icon(), 0.1)

        logger.info('Экран песен создан')

    def init_ui(self):
        """Инициализирует UI с едиными отступами через layout_config"""

        # Основной контейнер
        main_layout = MDBoxLayout(orientation='vertical', spacing=0)

        # Верхний отступ (под статус-бар и TopNav)
        top_padding = layout_config.get_top_padding()
        main_layout.add_widget(Widget(size_hint_y=None, height=top_padding))

        # Дополнительный отступ сверху для эстетики
        main_layout.add_widget(Widget(size_hint_y=None, height=dp(8)))

        # Получаем стандартные боковые отступы из layout_config
        content_padding = layout_config.get_content_padding()

        # ============ КОНТЕЙНЕР ДЛЯ ВЕРХНЕЙ ЧАСТИ (поиск + клавиатура) ============
        self.top_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            adaptive_height=True,
            padding=[content_padding[0], 0, content_padding[2], 0]
        )

        # Поисковая строка (всегда видна)
        self.search_bar = GoogleSearchBar(
            on_search=self.do_search,
            on_clear=self._on_clear_search
        )
        self.top_container.add_widget(self.search_bar)

        # Отступ после поиска
        self.top_container.add_widget(Widget(size_hint_y=None, height=dp(16)))

        # ============ КЛАВИАТУРА (выбор языка + сетка букв) ============
        self.keyboard_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            adaptive_height=True,
            spacing=dp(8)
        )

        # Выбор языка (центрирован)
        self.language_selector = LanguageSelector(
            on_language_change=self.on_language_changed
        )
        self.keyboard_container.add_widget(self.language_selector)

        # Сетка букв
        self.alphabet_grid = AlphabetGrid(on_letter_press=self.on_letter_press)
        self.keyboard_container.add_widget(self.alphabet_grid)

        # Подсказка
        self.hint_label = MDLabel(
            text="Нажмите на букву для просмотра исполнителей",
            halign="center",
            font_size=sp(13),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.4],
            size_hint_y=None,
            height=dp(32)
        )
        self.keyboard_container.add_widget(self.hint_label)

        self.top_container.add_widget(self.keyboard_container)

        main_layout.add_widget(self.top_container)

        # ============ КОНТЕЙНЕР ДЛЯ РЕЗУЛЬТАТОВ ============
        nav_bar_height = get_navigation_bar_height()
        bottom_nav_height = dp(60)
        total_bottom = bottom_nav_height + nav_bar_height + dp(16)

        self.cards_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            padding=[content_padding[0], dp(4), content_padding[2], total_bottom]
        )

        self.search_recycle_view = SongRecycleView(on_song_click=self.on_song_selected)
        self.search_recycle_view.bar_width = 0
        self.search_recycle_view.bar_color = [0, 0, 0, 0]
        self.search_recycle_view.bar_inactive_color = [0, 0, 0, 0]

        self.cards_container.add_widget(self.search_recycle_view)
        main_layout.add_widget(self.cards_container)

        self.add_widget(main_layout)

        # Сохраняем высоту клавиатуры для анимации
        Clock.schedule_once(self._save_keyboard_height, 0.5)

        logger.info(f"SongsScreen: top_padding = {top_padding}dp, side_padding = {content_padding[0]}dp")

    def _save_keyboard_height(self, dt):
        """Сохраняет высоту клавиатуры для последующего использования"""
        if self.keyboard_container:
            self._keyboard_height = self.keyboard_container.height
            logger.info(f"📏 Высота клавиатуры: {self._keyboard_height}dp")

    def _show_keyboard(self):
        """Показывает клавиатуру (выбор языка + сетка букв)"""
        if self.keyboard_container:
            self.keyboard_container.opacity = 1
            self.keyboard_container.disabled = False
            self.keyboard_container.height = self._keyboard_height

    def _hide_keyboard(self):
        """Скрывает клавиатуру (выбор языка + сетка букв) - схлопывает контейнер"""
        if self.keyboard_container:
            self.keyboard_container.opacity = 0
            self.keyboard_container.disabled = True
            self.keyboard_container.height = 0

    def _on_clear_search(self):
        """Обработчик нажатия на крестик в поиске"""
        logger.info("🧹 Очистка поиска (крестик)")
        self.clear_search()
        # Показываем клавиатуру обратно
        self._show_keyboard()

    def _show_search_results(self):
        """Показывает результаты поиска в RecycleView"""
        if not self.search_results:
            self.search_recycle_view.clear()
            return

        self.search_recycle_view.set_songs(self.search_results, self.on_song_selected)

    def _clear_search_results(self):
        """Очищает результаты поиска"""
        self.search_recycle_view.clear()

    def on_language_changed(self, language):
        start = time.time()
        logger.info(f"🔤 Язык изменён на: {language}")
        self.alphabet_grid.set_language(language)
        self.alphabet_grid.clear_selection()
        self.current_letter = None
        self.clear_search()
        self._clear_search_results()
        # Показываем клавиатуру после смены языка
        self._show_keyboard()
        logger.info(f"  ⏱ ВСЕГО: {(time.time() - start) * 1000:.2f}мс")

    def on_letter_press(self, letter):
        logger.info(f"Выбрана буква/группа: {letter}")
        self.current_letter = letter
        self.alphabet_grid.clear_selection()
        self.clear_search()
        self._clear_search_results()

        if hasattr(self, 'manager') and self.manager:
            if self.manager.has_screen('artists_by_letter'):
                artists_screen = self.manager.get_screen('artists_by_letter')
                artists_screen.set_letter(letter)
                self.manager.current = 'artists_by_letter'
            else:
                logger.error("Экран artists_by_letter не найден")
                notify.error("Ошибка навигации")

    def do_search(self, query):
        """Выполняет поиск песен"""
        if len(query) < 2:
            notify.warning("Введите минимум 2 символа для поиска")
            return

        logger.info(f"🔍 Поиск: {query}")

        self.is_search_mode = True
        self.current_letter = None
        self.alphabet_grid.clear_selection()

        # Скрываем клавиатуру при поиске (схлопываем контейнер)
        self._hide_keyboard()

        # Очищаем список перед поиском
        self.search_recycle_view.clear()

        api.search_songs(
            query=query,
            limit=50,
            on_success=self._on_search_success,
            on_failure=self._on_search_failed
        )

    def _on_search_success(self, results):
        """Обработчик успешного поиска"""
        if isinstance(results, dict):
            raw_results = results.get('results', [])
        elif isinstance(results, list):
            raw_results = results
        else:
            raw_results = []

        formatted_results = []
        for item in raw_results:
            if isinstance(item, dict):
                formatted_results.append({
                    'song_id': item.get('song_id', 0),
                    'artist': item.get('artist', ''),
                    'title': item.get('title', '')
                })

        self.search_results = formatted_results
        self._show_search_results()
        logger.info(f"Найдено {len(self.search_results)} результатов")

        if not self.search_results:
            notify.info("Ничего не найдено")
            # Если ничего не найдено, показываем клавиатуру обратно
            self._show_keyboard()

    def _on_search_failed(self, req, error):
        """Обработчик ошибки поиска"""
        self.search_results = []
        self._show_search_results()
        notify.error(f"Ошибка поиска: {error}")
        logger.error(f"Ошибка поиска: {error}")
        # Показываем клавиатуру при ошибке
        self._show_keyboard()

    def clear_search(self):
        """Очищает поиск"""
        self.is_search_mode = False
        self.search_results = []
        self.search_bar.clear()
        self._clear_search_results()

    def on_song_selected(self, song_id, title):
        logger.info(f"Выбрана песня: {title}, id: {song_id}")
        if not song_id:
            notify.error("Ошибка: не удалось загрузить песню")
            return
        if hasattr(self, 'manager') and self.manager:
            if self.manager.has_screen('song_detail'):
                song_detail_screen = self.manager.get_screen('song_detail')
                song_detail_screen.set_previous_screen('songs')
                song_detail_screen.set_song(song_id)
                self.manager.current = 'song_detail'

    def on_enter(self):
        """При входе на экран"""
        logger.info("Вход в экран песен")
        # Показываем клавиатуру при входе
        self._show_keyboard()

    def on_leave(self):
        """При выходе с экрана"""
        logger.info("Выход из экрана песен")
        self.clear_search()
        self.current_letter = None
        self.alphabet_grid.clear_selection()
        # Показываем клавиатуру при выходе
        self._show_keyboard()