# screens/song_detail_screen.py
"""
Экран просмотра песни с текстом и подборами
"""
from kivymd.app import MDApp
from kivymd.uix.label import MDLabel
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDIconButton, MDRaisedButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.dialog import MDDialog
from kivy.metrics import dp, sp
from kivy.animation import Animation
from kivy.uix.progressbar import ProgressBar
from kivy.graphics import Color, Rectangle
from kivy.core.image import Image as CoreImage
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.uix.behaviors import ButtonBehavior
from io import BytesIO
import re
from kivy.clock import Clock
from kivy.utils import platform

from config.theme import theme
from config.logger_config import screen_logger
from config.layout_config import layout_config
from config.system_bars import get_navigation_bar_height, get_status_bar_height
from screens.base_screen import BaseScreen
from screens.chord_renderer import ChordRenderer
from api.client import api
from utils.notifications import notify
from utils.screen_state import screen_state
# Импорт для подсветки аккордов
from utils.chord_highlighter import (
    ChordTextLabel,
    highlight_chords_in_text,
    extract_chords_from_text_wrapper as extract_chords_from_text,
    init_chord_patterns,
    CHORD_PATTERN
)
from utils.transposer import transpose_text, transpose_chord_list, set_transpose_system

logger = screen_logger('SongDetail')

try:
    from data import load_asset_as_bytes

    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False


    def load_asset_as_bytes(name):
        return None


def clean_text(text):
    """Очищает текст от HTML тегов и специальных символов"""
    if not text:
        return ""

    # Простая очистка от HTML тегов
    temp_text = re.sub(r'<[^>]+>', '', text)

    # Замена HTML сущностей
    html_entities = {
        '&amp;': '&', '&lt;': '<', '&gt;': '>', '&quot;': '"',
        '&apos;': "'", '&nbsp;': ' ', '&#39;': "'", '&#34;': '"',
        '&#38;': '&', '&#60;': '<', '&#62;': '>', '&#171;': '«',
        '&#187;': '»', '&#169;': '©', '&#174;': '®', '&#8364;': '€',
        '&#8470;': '№', '&#8211;': '–', '&#8212;': '—', '&#8216;': "'",
        '&#8217;': "'", '&#8220;': '"', '&#8221;': '"', '&#8230;': '…',
        '&#35;': '#',  # решётка
        '%23': '#',  # решётка URL encoded
    }
    for entity, char in html_entities.items():
        temp_text = temp_text.replace(entity, char)

    # Удаляем первые 4 строки и строки с источником
    lines = temp_text.split('\n')
    cleaned_lines = []
    for i, line in enumerate(lines):
        if i < 4:
            continue
        if 'источник:' in line.lower() or 'source:' in line.lower():
            continue
        cleaned_lines.append(line)

    while cleaned_lines and not cleaned_lines[-1].strip():
        cleaned_lines.pop()

    result = '\n'.join(cleaned_lines)
    if not result.strip():
        result = '\n'.join(lines[4:])

    return result


class LoadingSpinner(MDBoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint = (1, 1)
        self.spacing = dp(16)
        self.progress = ProgressBar(
            size_hint=(0.8, None),
            height=dp(4),
            pos_hint={'center_x': 0.5},
            value=50,
            max=100
        )
        self.anim = None
        self.label = MDLabel(
            text="Загрузка...",
            halign="center",
            font_size=sp(16),
            theme_text_color="Secondary",
            size_hint_y=None,
            height=dp(30)
        )
        self.add_widget(self.progress)
        self.add_widget(self.label)

    def start_animation(self):
        self.anim = Animation(value=100, duration=1) + Animation(value=0, duration=1)
        self.anim.repeat = True
        self.anim.start(self.progress)

    def stop_animation(self):
        if self.anim:
            self.anim.cancel(self.progress)
        self.progress.value = 0


class IconImageButton(ButtonBehavior, MDBoxLayout):
    """Кнопка с иконкой из PNG ассета с возможностью смещения через padding"""

    def __init__(self, icon_name, on_press_callback=None, size=dp(18), offset_y=0, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint = (None, None)
        self.size = (size, size)
        self.md_bg_color = [0, 0, 0, 0]

        self.offset_y = offset_y

        self.icon_container = MDBoxLayout(
            size_hint=(1, 1),
            padding=[0, offset_y, 0, 0]
        )

        self.icon = Image(
            size_hint=(0.8, 0.8),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            allow_stretch=True,
            keep_ratio=True
        )

        self.icon_container.add_widget(self.icon)
        self.add_widget(self.icon_container)

        self.icon_name = icon_name
        self.on_press_callback = on_press_callback
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
        self.icon.opacity = 0

    def _on_press(self, instance):
        if self.on_press_callback:
            self.on_press_callback(self.icon_name)


class IconActionButton(MDIconButton):
    """Кнопка действия в нижней панели"""

    def __init__(self, icon_name, on_press_callback=None, icon_color=None, **kwargs):
        super().__init__(**kwargs)
        self.on_press_callback = on_press_callback
        # Убираем фиксированный размер, используем size_hint
        self.size_hint = (1, None)  # Равномерное распределение
        self.height = dp(36)  # Фиксированная высота
        self.theme_icon_color = "Custom"
        if icon_color:
            self.icon_color = icon_color
        else:
            self.icon_color = [0.5, 0.5, 0.5, 0.9]
        self.md_bg_color = [0, 0, 0, 0]
        self.icon = icon_name
        self.bind(on_release=self._on_press)

    def _on_press(self, instance):
        if self.on_press_callback:
            self.on_press_callback()


class SongDetailScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'song_detail'
        self.song_id = None
        self.song_title = None
        self.song_artist = None
        self.is_liked = False
        self.is_favorite = False
        self.is_loading = False
        self.loading_spinner = None
        self.bg_image = None
        self.previous_screen = 'artist_songs'
        self.current_tonality = 0
        self.tabs = []
        self.current_tab_index = 0

        # Настройки размера шрифта в зависимости от платформы
        if platform == 'android':
            self.STANDARD_FONT_SIZE = 42
            self.MIN_FONT_SIZE = 30
            self.MAX_FONT_SIZE = 60
        else:
            self.STANDARD_FONT_SIZE = 20
            self.MIN_FONT_SIZE = 14
            self.MAX_FONT_SIZE = 32
        self.current_font_size = self.STANDARD_FONT_SIZE

        # Для смены темы текста
        self.is_light_theme = False  # False - тёмная тема, True - светлая

        # Для меню аккордов
        self._song_chords = []
        self._current_chord_index = 0
        self.chords_section = None
        self.chord_preview_renderer = None
        self.display_mode = "finger"
        self.chord_variants = []
        self.chord_variant_index = 0
        self.is_chords_mode = False
        self.griff_scale = 1.0
        self.original_griff_size = (dp(200), dp(110))
        self.griff_container = None

        # Для кэширования транспонирования
        self.transposed_chords_cache = {}
        self.transposed_text_cache = {}
        self.original_cleaned_text = ""

        # Для панели тональности
        self.normal_bottom_panel = None
        self.tonality_panel = None
        self.is_tonality_mode = False

        # Для панели шрифта
        self.font_panel = None
        self.is_font_mode = False

        # Для автопрокрутки текста
        self.scroll_panel = None
        self.is_scroll_mode = False
        self.scroll_speed = 1.0
        self.scroll_animation = None
        self.is_scrolling = False

        self.init_ui()
        self.load_background()

        logger.info('Экран просмотра песни создан')

    def set_previous_screen(self, screen_name):
        self.previous_screen = screen_name

    def load_background(self):
        """Загружает фоновое изображение для всего экрана"""
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

    def _toggle_theme(self, *args):
        """Переключает темы: зелёная -> светлая -> тёмная -> зелёная"""

        # Определяем текущую тему
        if not hasattr(self, '_current_theme'):
            self._current_theme = 'green'  # По умолчанию зелёная

        # Переключаем на следующую тему
        if self._current_theme == 'green':
            self._set_light_theme()
            self._current_theme = 'light'
        elif self._current_theme == 'light':
            self._set_dark_theme()
            self._current_theme = 'dark'
        else:  # dark -> green
            self._set_green_theme()
            self._current_theme = 'green'

        logger.info(f"🔄 Тема изменена на: {self._current_theme}")

    def _set_green_theme(self):
        """Зелёная тема - фон из ассета, текст белый"""
        self.is_light_theme = False

        # Текст - белый
        self.content_label.text_color = [1, 1, 1, 0.95]
        if hasattr(self, '_text_container') and self._text_container:
            self._text_container.md_bg_color = [0, 0, 0, 0]  # Прозрачный (фон из ассета)

        # Иконка - зелёное солнышко
        if hasattr(self, 'theme_btn'):
            self.theme_btn.icon = "weather-sunny"
            self.theme_btn.icon_color = [0.46, 0.70, 0.71, 1]  # Бирюзово-зелёный

        # Восстанавливаем полупрозрачную полоску для зелёной темы
        if hasattr(self, '_bottom_divider'):
            self._bottom_divider.md_bg_color = [0.5, 0.5, 0.5, 0.3]

    def _set_light_theme(self):
        """Светлая тема - фон белый, текст чёрный"""
        self.is_light_theme = True

        # Текст - чёрный
        self.content_label.text_color = [0, 0, 0, 0.95]
        if hasattr(self, '_text_container') and self._text_container:
            self._text_container.md_bg_color = [1, 1, 1, 1]  # Белый фон

        # Иконка - белое солнышко
        if hasattr(self, 'theme_btn'):
            self.theme_btn.icon = "white-balance-sunny"
            self.theme_btn.icon_color = [1, 1, 1, 1]  # Белый

        # Тёмная полоска для светлого фона
        if hasattr(self, '_bottom_divider'):
            self._bottom_divider.md_bg_color = [0, 0, 0, 0.15]

    def _set_dark_theme(self):
        """Тёмная тема - фон чёрный, текст белый"""
        self.is_light_theme = False

        # Текст - белый
        self.content_label.text_color = [1, 1, 1, 0.95]
        if hasattr(self, '_text_container') and self._text_container:
            self._text_container.md_bg_color = [0.05, 0.05, 0.05, 1]  # Почти чёрный фон

        # Иконка - чёрное солнышко (луна)
        if hasattr(self, 'theme_btn'):
            self.theme_btn.icon = "weather-night"
            self.theme_btn.icon_color = [0.3, 0.3, 0.3, 1]  # Тёмно-серый/чёрный

        # Полу透рачная полоска для тёмной темы
        if hasattr(self, '_bottom_divider'):
            self._bottom_divider.md_bg_color = [0.5, 0.5, 0.5, 0.3]

    def init_ui(self):
        main_container = MDBoxLayout(orientation='vertical', size_hint=(1, 1), padding=[0, 0, 0, 0])

        # ============ ОТСТУП ПОД TOPNAV ============
        top_padding_for_nav = layout_config.get_top_padding()

        if platform == 'android':
            min_top_padding = dp(48)
            if top_padding_for_nav < min_top_padding:
                top_padding_for_nav = min_top_padding
            else:
                top_padding_for_nav = top_padding_for_nav + dp(8)

        self._top_spacer_song = Widget(size_hint_y=None, height=top_padding_for_nav)
        main_container.add_widget(self._top_spacer_song)

        card_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            padding=[0, 0, 0, 0]
        )

        self.song_card = MDCard(
            orientation='vertical',
            size_hint=(1, 1),
            padding=[0, 0, 0, 0],
            spacing=0,
            radius=[0, 0, 0, 0],
            md_bg_color=[0, 0, 0, 0],
            elevation=0,
            line_width=0.5,
            line_color=[0, 0, 0, 0]
        )

        # ============ ВЕРХНЯЯ РАЗДЕЛИТЕЛЬНАЯ ПОЛОСКА ============
        top_divider = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(2),
            md_bg_color=[0.5, 0.5, 0.5, 0.3],
            padding=[0, 0, 0, 0]
        )
        self.song_card.add_widget(top_divider)

        self.content_scroll = MDScrollView(
            size_hint=(1, 1),
            do_scroll_x=False,
            bar_width=3,
            bar_color=[0.5, 0.5, 0.5, 0.3],
            bar_inactive_color=[0.5, 0.5, 0.5, 0.1]
        )

        if platform == 'android':
            nav_bar_height = get_navigation_bar_height()
            bottom_padding = nav_bar_height + dp(20)
        else:
            bottom_padding = dp(64)

        self._text_container = MDBoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=4,
            padding=[dp(16), dp(20), dp(16), bottom_padding],  # ← 40 вместо 20
            adaptive_height=True,
            md_bg_color=[0, 0, 0, 0]
        )

        self.content_label = ChordTextLabel(
            text="",
            font_size=self.current_font_size,
            size_hint_y=None,
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.95],
            valign="top",
            line_height=1.5,
            markup=True
        )
        self.content_label.bind(texture_size=self._update_content_height)
        self._text_container.add_widget(self.content_label)

        self.content_scroll.add_widget(self._text_container)
        self.song_card.add_widget(self.content_scroll)

        # ============ НИЖНЯЯ РАЗДЕЛИТЕЛЬНАЯ ПОЛОСКА ============
        self._bottom_divider = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(2),
            md_bg_color=[0.5, 0.5, 0.5, 0.3],
            padding=[0, 0, 0, 0]
        )
        self.song_card.add_widget(self._bottom_divider)

        self._create_bottom_panel()
        self.bottom_panel = self.normal_bottom_panel
        self.song_card.add_widget(self.bottom_panel)

        card_container.add_widget(self.song_card)
        main_container.add_widget(card_container)

        if platform != 'android':
            main_container.add_widget(Widget(size_hint_y=None, height=dp(48)))

        self.add_widget(main_container)

        if hasattr(self, '_top_spacer') and self._top_spacer:
            self._top_spacer.height = 0
        if hasattr(self, '_bottom_spacer') and self._bottom_spacer:
            self._bottom_spacer.height = 0

        logger.info(
            f"SongDetailScreen: init_ui completed, top_padding={top_padding_for_nav}dp, bottom_padding={bottom_padding}dp")

    def _wait_for_ready_and_scroll(self, *args):
        """Ждёт, пока текст полностью отрисуется, и прокручивает вверх"""
        if not hasattr(self, 'content_scroll'):
            return

        # Проверяем, что текст загружен и отрисован
        if hasattr(self, 'content_label') and self.content_label.text:
            if self.content_label.texture and self.content_label.texture_size[1] > 0:
                # Текст отрисован, делаем прокрутку вверх
                self.content_scroll.scroll_y = 1.0
                logger.info("✅ Текст отрисован, прокрутка вверх")
                return
            else:
                # Текст есть, но ещё не отрисован - ждём
                logger.info("⏳ Текст загружен, но ещё не отрисован, ждём...")
                Clock.schedule_once(self._wait_for_ready_and_scroll, 0.15)
                return
        else:
            # Текст ещё не загружен - ждём
            logger.info("⏳ Текст ещё не загружен, ждём...")
            Clock.schedule_once(self._wait_for_ready_and_scroll, 0.15)

    def _fix_scroll_position(self):
        """Принудительно устанавливает корректную позицию скролла"""
        if not hasattr(self, 'content_scroll'):
            return

        # Просто прокручиваем вверх
        self.content_scroll.scroll_y = 1.0

        logger.info("🔧 Scroll position fixed to top")

    def _create_bottom_panel(self):
        """Создаёт нижнюю панель с 7 кнопками (равномерное распределение)"""
        self.normal_bottom_panel = MDCard(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(52),
            padding=[dp(4), dp(4), dp(4), dp(4)],
            spacing=dp(2),
            radius=[0, 0, 0, 0],
            md_bg_color=[0, 0, 0, 0],
            elevation=0,
            line_width=0.5,
            line_color=[0, 0, 0, 0]
        )

        # 1. Аккорды - бирюзовый
        self.chords_btn = IconActionButton(
            icon_name="music",
            on_press_callback=self.on_chords_press,
            icon_color=[0.46, 0.70, 0.71, 1]
        )
        self.chords_btn.size_hint = (1, None)
        self.chords_btn.size = (dp(36), dp(36))

        # 2. Тональность - золотистый/оранжевый
        self.tonality_btn = IconActionButton(
            icon_name="tune",
            on_press_callback=self.show_tonality_panel,
            icon_color=[0.9, 0.7, 0.2, 0.9]
        )
        self.tonality_btn.size_hint = (1, None)
        self.tonality_btn.size = (dp(36), dp(36))

        # 3. Прокрутка текста (плей) - синий
        self.scroll_btn = IconActionButton(
            icon_name="play-circle",
            on_press_callback=self.show_scroll_panel,
            icon_color=[0.2, 0.5, 0.9, 0.9]
        )
        self.scroll_btn.size_hint = (1, None)
        self.scroll_btn.size = (dp(36), dp(36))

        # 4. Подборы (варианты) - серый
        self.tabs_btn = IconActionButton(
            icon_name="folder-music",
            on_press_callback=self.show_tabs_picker,
            icon_color=[0.5, 0.5, 0.5, 0.8]
        )
        self.tabs_btn.size_hint = (1, None)
        self.tabs_btn.size = (dp(36), dp(36))

        # 5. Настройки (шестерёнка) - ЯРКО БЕЛАЯ
        self.font_btn = IconActionButton(
            icon_name="cog",
            on_press_callback=self.show_font_panel,
            icon_color=[1, 1, 1, 1]
        )
        self.font_btn.size_hint = (1, None)
        self.font_btn.size = (dp(36), dp(36))

        # 6. Звёздочка (избранное) - золотистый
        self.favorite_btn = IconActionButton(
            icon_name="star-outline",
            on_press_callback=self.toggle_favorite,
            icon_color=[0.9, 0.7, 0.2, 0.9]
        )
        self.favorite_btn.size_hint = (1, None)
        self.favorite_btn.size = (dp(36), dp(36))

        # 7. Лайк (сердце) - красный
        self.like_btn = IconActionButton(
            icon_name="heart-outline",
            on_press_callback=self.toggle_like,
            icon_color=[0.8, 0.3, 0.3, 0.9]
        )
        self.like_btn.size_hint = (1, None)
        self.like_btn.size = (dp(36), dp(36))

        # Добавляем все кнопки с равным весом
        self.normal_bottom_panel.add_widget(self.chords_btn)
        self.normal_bottom_panel.add_widget(self.tonality_btn)
        self.normal_bottom_panel.add_widget(self.scroll_btn)
        self.normal_bottom_panel.add_widget(self.tabs_btn)
        self.normal_bottom_panel.add_widget(self.font_btn)
        self.normal_bottom_panel.add_widget(self.favorite_btn)
        self.normal_bottom_panel.add_widget(self.like_btn)

    def _get_font_multiplier(self, font_size):
        """Возвращает строку с множителем размера шрифта"""
        ratio = font_size / self.STANDARD_FONT_SIZE
        # Округляем до 1 десятичного знака
        rounded = round(ratio * 10) / 10
        # Если значение целое, показываем без десятичной части
        if rounded == int(rounded):
            return f"{int(rounded)}x"
        return f"{rounded:.1f}x"

    def show_font_panel(self):
        """Показывает панель шрифта с дополнительной кнопкой смены темы"""
        logger.info("🔍 Открытие панели шрифта")

        if self.is_chords_mode:
            self.close_chords_section()
        if self.is_tonality_mode:
            self.close_tonality_panel()
        if self.is_scroll_mode:
            self.close_scroll_panel()

        # Просто создаём панель MDCard БЕЗ дополнительных полосок
        self.font_panel = MDCard(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(52),
            padding=[dp(8), dp(4), dp(8), dp(4)],
            spacing=dp(4),
            radius=[0, 0, 0, 0],
            md_bg_color=[0, 0, 0, 0],
            elevation=0,
            line_width=0.5,
            line_color=[0, 0, 0, 0]
        )

        center_container = MDBoxLayout(
            orientation='vertical',
            size_hint_x=1,
            spacing=dp(0),
            padding=[dp(0), dp(0), dp(0), dp(0)]
        )

        from kivymd.uix.slider import MDSlider

        # ЯВНЫЙ СПИСОК РАЗМЕРОВ для каждой платформы (без дублирования)
        if platform == 'android':
            font_sizes = [30, 34, 38, 42, 46, 50, 54, 58, 60]
        else:
            font_sizes = [14, 16, 18, 20, 22, 24, 26, 28, 30, 32]

        total_steps = len(font_sizes) - 1

        def size_to_slider(size):
            try:
                return font_sizes.index(size)
            except ValueError:
                closest = min(font_sizes, key=lambda x: abs(x - size))
                return font_sizes.index(closest)

        def slider_to_size(slider_value):
            idx = int(round(slider_value))
            if idx < 0:
                idx = 0
            elif idx > total_steps:
                idx = total_steps
            return font_sizes[idx]

        current_slider_value = size_to_slider(self.current_font_size)

        # Верхний ряд со значением размера
        top_row = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(14),
            spacing=dp(0)
        )

        left_spacer = MDLabel(
            text="",
            size_hint_x=None,
            width=dp(2)
        )

        self.font_value_label = MDLabel(
            text=self._get_font_multiplier(self.current_font_size),
            font_size=sp(10),
            halign="center",
            valign="bottom",
            size_hint_x=1,
            theme_text_color="Custom",
            text_color=[0.46, 0.70, 0.71, 1],
            bold=True
        )

        right_spacer = MDLabel(
            text="",
            size_hint_x=None,
            width=dp(2)
        )

        top_row.add_widget(left_spacer)
        top_row.add_widget(self.font_value_label)
        top_row.add_widget(right_spacer)

        slider_container = MDBoxLayout(
            orientation='horizontal',
            size_hint_x=1,
            size_hint_y=None,
            height=dp(28),
            padding=[dp(2), dp(0), dp(2), dp(0)]
        )

        # Слайдер с min = -0.01 и max = total_steps + 0.01 (как в тональности)
        # Это позволяет избежать серого цвета при достижении 0
        self.font_slider = MDSlider(
            min=-0.01,  # ← КАК В ТОНАЛЬНОСТИ
            max=float(total_steps + 0.01),  # ← КАК В ТОНАЛЬНОСТИ
            value=current_slider_value,
            step=1,
            size_hint_x=1,
            size_hint_y=None,
            height=dp(28),
            hint=False
        )
        self.font_slider.ripple_scale = 0

        # ФИКСИРОВАННЫЙ ЦВЕТ (как в тональности)
        bi_color = [0.46, 0.70, 0.71, 1]

        self.font_slider.thumb_color_active = bi_color
        self.font_slider.thumb_color_inactive = bi_color
        self.font_slider.thumb_color_disabled = bi_color
        self.font_slider.track_color_active = [0.46, 0.70, 0.71, 0.6]
        self.font_slider.track_color_inactive = [1, 1, 1, 0.3]
        self.font_slider.color = bi_color

        def on_slider_change(instance, value):
            # Округляем до ближайшего целого
            int_value = int(round(value))

            # Ограничиваем диапазон (как в тональности)
            if int_value < 0:
                int_value = 0
            elif int_value > total_steps:
                int_value = total_steps

            # Обновляем значение слайдера
            if self.font_slider.value != int_value:
                self.font_slider.value = int_value

            # ПРИНУДИТЕЛЬНО УСТАНАВЛИВАЕМ ЦВЕТ THUMB
            bi_color = [0.46, 0.70, 0.71, 1]
            self.font_slider.thumb_color_active = bi_color
            self.font_slider.thumb_color_inactive = bi_color
            self.font_slider.thumb_color_disabled = bi_color

            # Преобразуем в размер
            new_size = slider_to_size(int_value)

            if self.current_font_size != new_size:
                self.current_font_size = new_size
                self.font_value_label.text = self._get_font_multiplier(new_size)

                if hasattr(self, 'content_label'):
                    self.content_label.font_size = self.current_font_size
                    self._update_content_height()

                    # ПРОСТО ПРОКРУЧИВАЕМ ВВЕРХ
                    delays = [0.0, 0.01, 0.03, 0.05, 0.08, 0.12, 0.2, 0.3, 0.5, 0.8]
                    for delay in delays:
                        Clock.schedule_once(lambda dt, d=delay: setattr(self.content_scroll, 'scroll_y', 1.0), delay)

                if hasattr(self, 'chord_name_label') and self.chord_name_label:
                    Clock.schedule_once(lambda dt: self._auto_scale_chord_font(), 0.1)

                logger.info(f"🔍 Размер шрифта изменён на: {self.current_font_size}")

        self.font_slider.bind(value=on_slider_change)

        slider_container.add_widget(self.font_slider)

        center_container.add_widget(top_row)
        center_container.add_widget(slider_container)

        right_buttons = MDBoxLayout(
            orientation='horizontal',
            size_hint=(None, 1),
            width=dp(80),
            spacing=dp(4)
        )

        self.theme_btn = IconActionButton(
            icon_name="weather-sunny",
            on_press_callback=self._toggle_theme,
            icon_color=[0.46, 0.70, 0.71, 1]
        )

        self.font_apply_btn = IconActionButton(
            icon_name="check",
            on_press_callback=self.close_font_panel,
            icon_color=[0.46, 0.70, 0.71, 1]
        )

        right_buttons.add_widget(self.theme_btn)
        right_buttons.add_widget(self.font_apply_btn)

        self.font_panel.add_widget(center_container)
        self.font_panel.add_widget(right_buttons)

        self.song_card.remove_widget(self.bottom_panel)
        self.bottom_panel = self.font_panel
        self.song_card.add_widget(self.bottom_panel)

        self.is_font_mode = True

        Clock.schedule_once(lambda dt: self._fix_slider_thumb(self.font_slider), 0.1)
        Clock.schedule_once(lambda dt: self._fix_slider_thumb(self.font_slider), 0.3)

    def _fix_slider_thumb(self, slider):
        """Принудительно обновляет слайдер, чтобы появился thumb (шарик) и не менял цвет"""
        if slider:
            # ПРИНУДИТЕЛЬНО УСТАНАВЛИВАЕМ ЦВЕТ THUMB
            bi_color = [0.46, 0.70, 0.71, 1]
            slider.thumb_color_active = bi_color
            slider.thumb_color_inactive = bi_color
            slider.thumb_color_disabled = bi_color

            # Сохраняем текущее значение
            current = slider.value

            # Небольшое изменение значения для перерисовки (как в тональности)
            slider.value = current + 0.01
            # Возвращаем через очень короткий промежуток
            Clock.schedule_once(lambda dt: setattr(slider, 'value', current), 0.01)

            logger.info("🔧 Слайдер обновлён, thumb зафиксирован")

    def close_font_panel(self):
        """Закрывает панель шрифта"""
        logger.info("🔍 Закрытие панели шрифта")
        if self.normal_bottom_panel:
            self.song_card.remove_widget(self.bottom_panel)
            self.bottom_panel = self.normal_bottom_panel
            self.song_card.add_widget(self.bottom_panel)
        self.is_font_mode = False

    # ==================== ВСТРОЕННАЯ СЕКЦИЯ АККОРДОВ ====================

    def show_chords_section(self):
        """Показывает встроенную секцию аккордов над нижним меню"""
        logger.info("🎸 Открытие секции аккордов")

        # Закрываем другие режимы если открыты
        if self.is_tonality_mode:
            self.cancel_tonality()
        if self.is_font_mode:
            self.cancel_font()
        if self.is_scroll_mode:
            self.close_scroll_panel()

        if not self._song_chords:
            notify.info("Аккорды не найдены в тексте песни")
            return

        if self.is_chords_mode:
            self.close_chords_section()
            return

        from kivy.uix.floatlayout import FloatLayout

        # Создаём плавающий слой поверх основного контента
        self.chords_layer = FloatLayout(
            size_hint=(1, 1),
            pos_hint={'x': 0, 'y': 0}
        )

        # Сохраняем оригинальный размер
        self.original_griff_size = (dp(200), dp(110))
        self.griff_scale = 1.0

        # Контейнер для грифа
        self.griff_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(None, None),
            size=self.original_griff_size,
            pos_hint={'center_x': 0.5},
            y=dp(60),
            spacing=dp(0)
        )

        # Рамка вокруг грифа с зелёной полупрозрачной заливкой
        griff_wrapper = MDCard(
            orientation='vertical',
            size_hint=(1, 1),
            radius=[12, 12, 12, 12],
            elevation=2,
            md_bg_color=[0.3, 0.7, 0.3, 0.15],
            line_color=[0.3, 0.7, 0.3, 0.5],
            line_width=0.5,
            padding=[dp(6), dp(6), dp(6), dp(6)]
        )

        # Рендерер грифа
        self.chord_preview_renderer = ChordRenderer()
        griff_wrapper.add_widget(self.chord_preview_renderer)

        try:
            griff_data = load_asset_as_bytes("griff_png")
            if griff_data:
                griff_img = CoreImage(BytesIO(griff_data), ext="png")
                if griff_img and griff_img.texture:
                    self.chord_preview_renderer.set_background(griff_img.texture)
        except Exception as e:
            logger.error(f"Ошибка загрузки фона грифа: {e}")

        self.griff_container.add_widget(griff_wrapper)
        self.chords_layer.add_widget(self.griff_container)

        # Функция для обновления позиции
        def update_griff_position(*args):
            if hasattr(self, 'bottom_panel') and self.bottom_panel:
                panel_y = self.bottom_panel.y
                panel_height = self.bottom_panel.height
                self.griff_container.y = panel_y + panel_height + dp(8)

        self._update_griff_position = update_griff_position

        # Обновляем позицию
        Clock.schedule_once(lambda dt: update_griff_position(), 0.1)
        self.bind(size=update_griff_position)
        if hasattr(self, 'bottom_panel'):
            self.bottom_panel.bind(pos=update_griff_position, size=update_griff_position)

        # Добавляем плавающий слой на экран
        self.add_widget(self.chords_layer)

        # Заменяем нижнюю панель на панель управления аккордами
        self.show_chords_control_panel()

        self.is_chords_mode = True

        # Загружаем первый аккорд
        self._current_chord_index = 0
        self._load_chord_variants(self._song_chords[0])
        self._update_chords_display()

    def show_chords_control_panel(self):
        """Показывает панель управления аккордами вместо обычного меню"""
        logger.info("🎸 Открытие панели управления аккордами")

        self.chords_control_panel = MDCard(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(52),
            padding=[dp(4), dp(4), dp(4), dp(4)],
            spacing=dp(2),
            radius=[0, 0, 0, 0],
            md_bg_color=[0, 0, 0, 0],
            elevation=0,
            line_width=0.5,
            line_color=[0, 0, 0, 0]
        )

        # Все кнопки с равным весом
        self.variant_btn = MDIconButton(
            icon="format-list-bulleted-square",
            size_hint=(1, None),
            height=dp(36),
            theme_icon_color="Custom",
            icon_color=[0.3, 0.5, 0.9, 1],
            md_bg_color=[0, 0, 0, 0],
            on_release=self._next_chord_variant,
            ripple_scale=0
        )

        self.mode_btn = MDIconButton(
            icon="music-note",
            size_hint=(1, None),
            height=dp(36),
            theme_icon_color="Custom",
            icon_color=[1.0, 0.55, 0.0, 1],
            md_bg_color=[0, 0, 0, 0],
            on_release=self._toggle_display_mode,
            ripple_scale=0
        )

        self.chord_prev_btn = MDIconButton(
            icon="chevron-left",
            size_hint=(1, None),
            height=dp(36),
            theme_icon_color="Custom",
            icon_color=[0.46, 0.70, 0.71, 1],
            md_bg_color=[0, 0, 0, 0],
            on_release=self._prev_chord_in_section,
            ripple_scale=0
        )

        self.chord_name_label = MDLabel(
            text="",
            halign="center",
            valign="middle",
            size_hint_x=2,
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
            bold=True,
            shorten=False,
            font_size=sp(16)
        )

        self.chord_name_label.bind(width=self._auto_scale_chord_font)
        self.chord_name_label.bind(text=self._auto_scale_chord_font)

        self.chord_next_btn = MDIconButton(
            icon="chevron-right",
            size_hint=(1, None),
            height=dp(36),
            theme_icon_color="Custom",
            icon_color=[0.46, 0.70, 0.71, 1],
            md_bg_color=[0, 0, 0, 0],
            on_release=self._next_chord_in_section,
            ripple_scale=0
        )

        self.griff_zoom_btn = MDIconButton(
            icon="magnify",
            size_hint=(1, None),
            height=dp(36),
            theme_icon_color="Custom",
            icon_color=[1, 1, 1, 1],
            md_bg_color=[0, 0, 0, 0],
            on_release=self._toggle_griff_zoom,
            ripple_scale=0
        )

        self.chords_close_btn = MDIconButton(
            icon="check",
            size_hint=(1, None),
            height=dp(36),
            theme_icon_color="Custom",
            icon_color=[0.46, 0.70, 0.71, 1],
            md_bg_color=[0, 0, 0, 0],
            on_release=self.close_chords_section,
            ripple_scale=0
        )

        self.chords_control_panel.add_widget(self.variant_btn)
        self.chords_control_panel.add_widget(self.mode_btn)
        self.chords_control_panel.add_widget(self.chord_prev_btn)
        self.chords_control_panel.add_widget(self.chord_name_label)
        self.chords_control_panel.add_widget(self.chord_next_btn)
        self.chords_control_panel.add_widget(self.griff_zoom_btn)
        self.chords_control_panel.add_widget(self.chords_close_btn)

        self.song_card.remove_widget(self.bottom_panel)
        self.bottom_panel = self.chords_control_panel
        self.song_card.add_widget(self.bottom_panel)

        Clock.schedule_once(lambda dt: self._auto_scale_chord_font(), 0.2)

    def _auto_scale_chord_font(self, *args):
        """Автоматическое масштабирование шрифта с учётом реальной ширины"""
        if not hasattr(self, 'chord_name_label') or not self.chord_name_label:
            return

        text = self.chord_name_label.text
        if not text:
            return

        available_width = self.chord_name_label.width

        if available_width <= dp(50):
            Clock.schedule_once(lambda dt: self._auto_scale_chord_font(), 0.1)
            return

        from kivy.core.text import Label as CoreLabel

        for size in range(16, 11, -1):
            test_label = CoreLabel(
                text=text,
                font_size=sp(size),
                font_name=self.chord_name_label.font_name,
                bold=True
            )
            test_label.refresh()
            text_width = test_label.texture.width

            if text_width <= available_width - dp(10):
                if self.chord_name_label.font_size != sp(size):
                    self.chord_name_label.font_size = sp(size)
                return

        if self.chord_name_label.font_size != sp(11):
            self.chord_name_label.font_size = sp(11)

    def _toggle_display_mode(self, *args):
        """Переключает режим отображения"""
        if self.display_mode == "finger":
            self.display_mode = "notes"
            self.mode_btn.icon = "gesture-tap"
            self.mode_btn.icon_color = [1.0, 0.55, 0.0, 1]
            logger.info("Режим отображения: НОТЫ")
        else:
            self.display_mode = "finger"
            self.mode_btn.icon = "music-note"
            self.mode_btn.icon_color = [0.9, 0.2, 0.2, 1]
            logger.info("Режим отображения: ПАЛЬЦЫ")

        if hasattr(self, 'chord_preview_renderer') and self.chord_preview_renderer:
            self.chord_preview_renderer.set_mode(self.display_mode)
            if self.chord_variants:
                self.load_current_variant()

    def _toggle_griff_zoom(self, *args):
        """Переключает масштаб грифа (1.2x -> 1.5x -> 1.7x -> 2.0x -> 1.2x)"""
        current = self.griff_scale

        if current == 1.2:
            new_scale = 1.5
            self.griff_zoom_btn.icon = "magnify-plus"
            self.griff_zoom_btn.icon_color = [1, 1, 1, 1]
        elif current == 1.5:
            new_scale = 1.7
            self.griff_zoom_btn.icon = "magnify-plus"
            self.griff_zoom_btn.icon_color = [1, 1, 1, 1]
        elif current == 1.7:
            new_scale = 2.0
            self.griff_zoom_btn.icon = "magnify-minus"
            self.griff_zoom_btn.icon_color = [1, 1, 1, 1]
        else:
            new_scale = 1.2
            self.griff_zoom_btn.icon = "magnify"
            self.griff_zoom_btn.icon_color = [1, 1, 1, 1]

        self.griff_scale = new_scale
        new_size = (int(self.original_griff_size[0] * new_scale),
                    int(self.original_griff_size[1] * new_scale))
        self.griff_container.size = new_size

        logger.info(f"Гриф изменён: {current} -> {new_scale}")

        if hasattr(self, '_update_griff_position'):
            self._update_griff_position()

    def _update_chords_display(self):
        """Обновляет отображение текущего аккорда в секции"""
        if not self._song_chords:
            return

        chord_name = self._song_chords[self._current_chord_index]
        if hasattr(self, 'chord_name_label'):
            self.chord_name_label.text = chord_name

        self._load_chord_variants(chord_name)

    def _prev_chord_in_section(self, *args):
        """Предыдущий аккорд (циклический переход)"""
        if not self._song_chords:
            return

        total = len(self._song_chords)
        if self._current_chord_index == 0:
            self._current_chord_index = total - 1
        else:
            self._current_chord_index -= 1

        self._update_chords_display()

    def _next_chord_in_section(self, *args):
        """Следующий аккорд (циклический переход)"""
        if not self._song_chords:
            return

        total = len(self._song_chords)
        if self._current_chord_index == total - 1:
            self._current_chord_index = 0
        else:
            self._current_chord_index += 1

        self._update_chords_display()

    def close_chords_section(self, *args):
        """Закрывает секцию аккордов и возвращает обычное меню"""
        logger.info("🔚 Закрытие секции аккордов")

        self.griff_scale = 1.0

        if hasattr(self, 'chords_layer') and self.chords_layer:
            self.remove_widget(self.chords_layer)
            self.chords_layer = None

        if self.normal_bottom_panel:
            self.song_card.remove_widget(self.bottom_panel)
            self.bottom_panel = self.normal_bottom_panel
            self.song_card.add_widget(self.bottom_panel)

        self.is_chords_mode = False

    def _extract_and_cache_chords(self):
        """Извлекает и кэширует аккорды из песни"""
        chords = set()

        for tab in self.tabs:
            content = tab.get('content', '')
            if content:
                cleaned = clean_text(content)
                extracted = extract_chords_from_text(cleaned)
                chords.update(extracted)

        self._song_chords = sorted(list(chords))
        logger.info(f"🎸 Найдено аккордов в песне: {len(self._song_chords)} - {self._song_chords}")

    def _load_chord_variants(self, chord_name):
        """Загружает все варианты аппликатур для аккорда"""
        self.chord_variants = []
        self.chord_variant_index = 0

        if self.manager and self.manager.has_screen('chords'):
            chords_screen = self.manager.get_screen('chords')
            variants = []
            for chord in chords_screen.all_chords:
                if chord['short_name'].lower() == chord_name.lower():
                    variants.append(chord)

            variants.sort(key=lambda x: x['variant'])
            self.chord_variants = variants
            logger.info(f"Загружено вариантов для {chord_name}: {len(self.chord_variants)}")

            self._update_variant_icon()

            if self.chord_variants:
                self.load_current_variant()

    def _update_variant_icon(self):
        """Обновляет видимость кнопки вариантов"""
        total = len(self.chord_variants)
        if hasattr(self, 'variant_btn'):
            if total <= 1:
                self.variant_btn.opacity = 0.5
            else:
                self.variant_btn.opacity = 1

    def load_current_variant(self):
        """Загружает текущий вариант аккорда"""
        if not self.chord_variants:
            return

        variant = self.chord_variants[self.chord_variant_index]
        chord_module = None
        if 'module' in variant:
            chord_module = variant['module']
        elif 'module_1' in variant:
            chord_module = variant['module_1']
        else:
            for key, value in variant.items():
                if 'module' in key.lower() and value:
                    chord_module = value
                    break

        if chord_module and hasattr(self, 'chord_preview_renderer') and self.chord_preview_renderer:
            self.chord_preview_renderer.load_chord(chord_module)
            self.chord_preview_renderer.set_mode(self.display_mode)
            logger.info(f"Загружен вариант {self.chord_variant_index + 1}/{len(self.chord_variants)}")

        self._update_variant_icon()

    def _next_chord_variant(self, *args):
        """Переключает на следующий вариант аккорда"""
        if not self.chord_variants:
            return

        total = len(self.chord_variants)
        self.chord_variant_index = (self.chord_variant_index + 1) % total
        self.load_current_variant()

    # ==================== ПАНЕЛЬ ТОНАЛЬНОСТИ ====================

    def show_tonality_panel(self):
        """Показывает панель выбора тональности вместо обычного меню"""
        logger.info("🎵 Открытие панели тональности")

        if self.is_chords_mode:
            self.close_chords_section()
        if self.is_font_mode:
            self.cancel_font()
        if self.is_scroll_mode:
            self.close_scroll_panel()

        self.tonality_panel = MDCard(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(52),
            padding=[dp(8), dp(4), dp(8), dp(4)],
            spacing=dp(8),
            radius=[0, 0, 0, 0],
            md_bg_color=[0, 0, 0, 0],
            elevation=0,
            line_width=0.5,
            line_color=[0, 0, 0, 0]
        )

        # Заголовок "Тональность" - БЕЛЫЙ
        title_label = MDLabel(
            text="Тональность",
            font_size=sp(12),
            halign="left",
            valign="middle",
            size_hint_x=None,
            width=dp(120),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
            bold=True
        )

        # Центральный контейнер со шкалой - растягивается
        center_container = MDBoxLayout(
            orientation='vertical',
            size_hint_x=1,
            spacing=dp(0),
            padding=[dp(0), dp(0), dp(0), dp(0)]
        )

        from kivymd.uix.slider import MDSlider

        current_slider_value = int(round(self.current_tonality * 2))

        # Верхний ряд с минус/плюс и значением
        top_row = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(14),
            spacing=dp(0)
        )

        # Кнопка "-" (красная)
        minus_label = MDLabel(
            text="-",
            font_size=sp(12),
            halign="center",
            valign="bottom",
            size_hint_x=None,
            width=dp(24),
            theme_text_color="Custom",
            text_color=[0.8, 0.3, 0.3, 0.9],
            bold=True
        )

        # Значение тональности
        self.tonality_value_label = MDLabel(
            text="0" if current_slider_value == 0 else f"{current_slider_value:+d}",
            font_size=sp(10),
            halign="center",
            valign="bottom",
            size_hint_x=1,
            theme_text_color="Custom",
            bold=True
        )
        self._update_tonality_label_color(current_slider_value)

        # Кнопка "+" (зелёная)
        plus_label = MDLabel(
            text="+",
            font_size=sp(12),
            halign="center",
            valign="bottom",
            size_hint_x=None,
            width=dp(24),
            theme_text_color="Custom",
            text_color=[0.3, 0.7, 0.3, 0.9],
            bold=True
        )

        top_row.add_widget(minus_label)
        top_row.add_widget(self.tonality_value_label)
        top_row.add_widget(plus_label)

        # Контейнер для слайдера
        slider_container = MDBoxLayout(
            orientation='horizontal',
            size_hint_x=1,
            size_hint_y=None,
            height=dp(28),
            padding=[dp(4), dp(0), dp(4), dp(0)]
        )

        self.tonality_slider = MDSlider(
            min=-6.01,
            max=6.01,
            value=current_slider_value,
            step=1,
            size_hint_x=1,
            size_hint_y=None,
            height=dp(28),
            hint=False
        )
        self.tonality_slider.ripple_scale = 0

        bi_color = [0.46, 0.70, 0.71, 1]

        self.tonality_slider.thumb_color_active = bi_color
        self.tonality_slider.thumb_color_inactive = bi_color
        self.tonality_slider.thumb_color_disabled = bi_color
        self.tonality_slider.track_color_active = [0.46, 0.70, 0.71, 0.5]
        self.tonality_slider.track_color_inactive = [0.85, 0.85, 0.85, 1]
        self.tonality_slider.color = bi_color

        slider_container.add_widget(self.tonality_slider)

        def on_slider_change(instance, value):
            if value < -6:
                int_value = -6
            elif value > 6:
                int_value = 6
            else:
                int_value = int(round(value))

            if self.tonality_slider.value != int_value:
                self.tonality_slider.value = int_value

            if int_value == 0:
                self.tonality_value_label.text = "0"
            else:
                self.tonality_value_label.text = f"{int_value:+d}"

            self._update_tonality_label_color(int_value)
            step = int_value / 2
            if step != self.current_tonality:
                self.current_tonality = step
                self.apply_tonality(self.current_tonality)
                logger.info(f"🎵 Тональность изменена на: {self.current_tonality:.1f}")

        self.tonality_slider.bind(value=on_slider_change)

        def on_minus(*args):
            new_value = max(-6, self.tonality_slider.value - 1)
            self.tonality_slider.value = new_value

        def on_plus(*args):
            new_value = min(6, self.tonality_slider.value + 1)
            self.tonality_slider.value = new_value

        minus_label.bind(on_touch_down=lambda x, y: on_minus())
        plus_label.bind(on_touch_down=lambda x, y: on_plus())

        center_container.add_widget(top_row)
        center_container.add_widget(slider_container)

        # Кнопка "галочка" - отдельно справа
        self.tonality_apply_btn = IconActionButton(
            icon_name="check",
            on_press_callback=self.close_tonality_panel,
            icon_color=[0.46, 0.70, 0.71, 1]
        )
        self.tonality_apply_btn.size_hint = (None, None)
        self.tonality_apply_btn.size = (dp(36), dp(36))

        # Добавляем всё в панель
        self.tonality_panel.add_widget(title_label)
        self.tonality_panel.add_widget(center_container)
        self.tonality_panel.add_widget(self.tonality_apply_btn)

        self.song_card.remove_widget(self.bottom_panel)
        self.bottom_panel = self.tonality_panel
        self.song_card.add_widget(self.bottom_panel)

        self.is_tonality_mode = True

    def _update_tonality_label_color(self, value):
        if hasattr(self, 'tonality_value_label'):
            if value < 0:
                self.tonality_value_label.text_color = [0.8, 0.3, 0.3, 1]
            elif value > 0:
                self.tonality_value_label.text_color = [0.3, 0.7, 0.3, 1]
            else:
                self.tonality_value_label.text_color = [0.46, 0.70, 0.71, 1]

    def close_tonality_panel(self):
        logger.info("🎵 Закрытие панели тональности")
        if self.normal_bottom_panel:
            self.song_card.remove_widget(self.bottom_panel)
            self.bottom_panel = self.normal_bottom_panel
            self.song_card.add_widget(self.bottom_panel)
        self.is_tonality_mode = False

    def cancel_tonality(self):
        """Отменяет изменение тональности"""
        if self.is_tonality_mode:
            if self.current_tonality != 0:
                self.current_tonality = 0
                self.apply_tonality(0)
                logger.info("Тональность сброшена до оригинальной")
            self.close_tonality_panel()

    # ==================== ПАНЕЛЬ ПРОКРУТКИ ТЕКСТА ====================

    def show_scroll_panel(self):
        logger.info("▶️ Открытие панели прокрутки текста")

        if self.is_chords_mode:
            self.close_chords_section()
        if self.is_tonality_mode:
            self.close_tonality_panel()
        if self.is_font_mode:
            self.close_font_panel()

        self.scroll_panel = MDCard(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(52),
            padding=[dp(8), dp(4), dp(8), dp(4)],
            spacing=dp(8),
            radius=[0, 0, 0, 0],
            md_bg_color=[0, 0, 0, 0],
            elevation=0,
            line_width=0.5,
            line_color=[0, 0, 0, 0]
        )

        # Центральный контейнер со шкалой - увеличиваем
        center_container = MDBoxLayout(
            orientation='vertical',
            size_hint_x=1,
            spacing=dp(0),
            padding=[dp(0), dp(0), dp(0), dp(0)]
        )

        from kivymd.uix.slider import MDSlider

        def speed_to_slider(speed):
            if speed <= 0.5:
                return int(1 + (speed - 0.2) / 0.03)
            else:
                return int(10 + (speed - 0.5) / 0.1)

        def slider_to_speed(slider_value):
            if slider_value <= 10:
                return 0.2 + (slider_value - 1) * 0.03
            else:
                return 0.5 + (slider_value - 10) * 0.1

        current_slider_value = speed_to_slider(self.scroll_speed)

        # Верхний ряд со значением скорости
        top_row = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(14),
            spacing=dp(0)
        )

        # Пустая метка слева для баланса
        left_spacer = MDLabel(
            text="",
            size_hint_x=None,
            width=dp(4)
        )

        self.scroll_speed_value_label = MDLabel(
            text=f"{self.scroll_speed:.1f}x",
            font_size=sp(10),
            halign="center",
            valign="bottom",
            size_hint_x=1,
            theme_text_color="Custom",
            text_color=[0.46, 0.70, 0.71, 1],
            bold=True
        )

        # Пустая метка справа для баланса
        right_spacer = MDLabel(
            text="",
            size_hint_x=None,
            width=dp(4)
        )

        top_row.add_widget(left_spacer)
        top_row.add_widget(self.scroll_speed_value_label)
        top_row.add_widget(right_spacer)

        # Контейнер для слайдера - увеличиваем
        slider_container = MDBoxLayout(
            orientation='horizontal',
            size_hint_x=1,
            size_hint_y=None,
            height=dp(28),
            padding=[dp(4), dp(0), dp(4), dp(0)]
        )

        self.scroll_speed_slider = MDSlider(
            min=0.99,
            max=28.01,
            value=current_slider_value,
            step=1,
            size_hint_x=1,
            size_hint_y=None,
            height=dp(28),
            hint=False
        )
        self.scroll_speed_slider.ripple_scale = 0

        bi_color = [0.46, 0.70, 0.71, 1]
        self.scroll_speed_slider.thumb_color_active = bi_color
        self.scroll_speed_slider.thumb_color_inactive = bi_color
        self.scroll_speed_slider.thumb_color_disabled = bi_color
        self.scroll_speed_slider.track_color_active = [0.46, 0.70, 0.71, 0.6]
        self.scroll_speed_slider.track_color_inactive = [1, 1, 1, 0.3]
        self.scroll_speed_slider.color = bi_color

        def on_slider_change(instance, value):
            if value < 1:
                int_value = 1
            elif value > 28:
                int_value = 28
            else:
                int_value = int(round(value))

            if self.scroll_speed_slider.value != int_value:
                self.scroll_speed_slider.value = int_value

            self.scroll_speed = slider_to_speed(int_value)
            self.scroll_speed_value_label.text = f"{self.scroll_speed:.1f}x"

            logger.info(f"🎚️ Скорость прокрутки изменена: {self.scroll_speed:.1f}x")

            if self.is_scrolling:
                self.stop_scroll()
                self.start_scroll()

        self.scroll_speed_slider.bind(value=on_slider_change)

        slider_container.add_widget(self.scroll_speed_slider)

        center_container.add_widget(top_row)
        center_container.add_widget(slider_container)

        # Контейнер для кнопок - фиксированной ширины, прижат к правому краю
        buttons_container = MDBoxLayout(
            orientation='horizontal',
            size_hint=(None, 1),
            width=dp(100),
            spacing=dp(4)
        )

        self.play_pause_btn = IconActionButton(
            icon_name="play",
            on_press_callback=self.toggle_scroll,
            icon_color=[0.46, 0.70, 0.71, 1]
        )
        self.play_pause_btn.size_hint = (1, None)
        self.play_pause_btn.height = dp(36)

        self.stop_btn = IconActionButton(
            icon_name="stop",
            on_press_callback=self.reset_scroll_position,
            icon_color=[0.8, 0.3, 0.3, 0.9]
        )
        self.stop_btn.size_hint = (1, None)
        self.stop_btn.height = dp(36)

        buttons_container.add_widget(self.play_pause_btn)
        buttons_container.add_widget(self.stop_btn)

        # Кнопка закрытия - отдельно справа
        self.scroll_close_btn = IconActionButton(
            icon_name="check",
            on_press_callback=self.close_scroll_panel,
            icon_color=[0.46, 0.70, 0.71, 1]
        )
        self.scroll_close_btn.size_hint = (None, None)
        self.scroll_close_btn.size = (dp(36), dp(36))

        # Добавляем всё в панель
        self.scroll_panel.add_widget(center_container)
        self.scroll_panel.add_widget(buttons_container)
        self.scroll_panel.add_widget(self.scroll_close_btn)

        self.song_card.remove_widget(self.bottom_panel)
        self.bottom_panel = self.scroll_panel
        self.song_card.add_widget(self.bottom_panel)

        self.is_scroll_mode = True

    def close_scroll_panel(self):
        """Закрывает панель прокрутки"""
        if self.is_scrolling:
            self.stop_scroll()
        if self.normal_bottom_panel:
            self.song_card.remove_widget(self.bottom_panel)
            self.bottom_panel = self.normal_bottom_panel
            self.song_card.add_widget(self.bottom_panel)
        self.is_scroll_mode = False

    def toggle_scroll(self):
        logger.info(f"🎬 Переключение прокрутки: {'СТАРТ' if not self.is_scrolling else 'СТОП'}")
        if not self.is_scrolling and self.content_scroll.scroll_y <= 0.01:
            self.reset_scroll_position()
        if not self.is_scrolling:
            self.start_scroll()
            self.play_pause_btn.icon = "pause"
        else:
            self.stop_scroll()
            self.play_pause_btn.icon = "play"

    def start_scroll(self):
        if self.is_scrolling:
            return
        self.is_scrolling = True

        def update_scroll(dt):
            if not self.is_scrolling:
                return False
            scroll_step = 0.0004 * self.scroll_speed
            new_y = self.content_scroll.scroll_y - scroll_step
            if new_y <= 0:
                self.content_scroll.scroll_y = 0
                self.stop_scroll()
                self.play_pause_btn.icon = "play"
                logger.info("🏁 Достигнут конец текста, прокрутка остановлена")
                return False
            else:
                self.content_scroll.scroll_y = new_y
                return True

        self.scroll_animation = Clock.schedule_interval(update_scroll, 1.0 / 60.0)

    def stop_scroll(self):
        if self.scroll_animation:
            self.scroll_animation.cancel()
            self.scroll_animation = None
        self.is_scrolling = False

    def reset_scroll_position(self):
        logger.info("⏹️ Сброс позиции прокрутки в начало")
        if self.is_scrolling:
            self.stop_scroll()
            self.play_pause_btn.icon = "play"
        self.content_scroll.scroll_y = 1.0

    # ==================== МЕНЮ АККОРДОВ ====================

    def on_chords_press(self):
        logger.info("🎸 Нажата кнопка аккордов")
        self.show_chords_section()

    # ==================== ТРАНСПОНИРОВАНИЕ ====================

    def precompute_transpositions(self, cleaned_text):
        from utils.transposer import transpose_text

        self.original_cleaned_text = cleaned_text
        self.transposed_text_cache[0] = highlight_chords_in_text(cleaned_text)
        self.transposed_chords_cache[0] = self._song_chords.copy()

        steps = [-3, -2.5, -2, -1.5, -1, -0.5, 0.5, 1, 1.5, 2, 2.5, 3]

        for step in steps:
            transposed = transpose_text(cleaned_text, step)
            self.transposed_text_cache[step] = transposed
            transposed_chords = transpose_chord_list(self._song_chords, step)
            self.transposed_chords_cache[step] = transposed_chords

        logger.info(f"✅ Предварительно вычислены транспозиции для {len(steps) + 1} шагов")

    def apply_tonality(self, step):
        transposed_text = self.transposed_text_cache.get(step)
        if transposed_text:
            self.content_label.text = transposed_text
            self.content_label.markup = True
            self._song_chords = self.transposed_chords_cache.get(step, [])
            if self.is_chords_mode and hasattr(self, 'chord_name_label'):
                if self._song_chords:
                    if self._current_chord_index >= len(self._song_chords):
                        self._current_chord_index = 0
                    self._update_chords_display()
            logger.info(f"✅ Применена тональность: {step:.1f}")
        else:
            logger.warning(f"⚠️ Текст для {step} не найден")

    # ==================== ПОДБОРЫ ====================

    def show_tabs_picker(self):
        if not self.tabs or len(self.tabs) <= 1:
            notify.info("Только один подбор")
            return

        content = MDBoxLayout(
            orientation='vertical',
            spacing=dp(8),
            padding=dp(16),
            size_hint_y=None,
            adaptive_height=True
        )

        for i, tab in enumerate(self.tabs):
            btn = MDRaisedButton(
                text=f"Подбор {i + 1}",
                size_hint=(1, None),
                height=dp(48),
                md_bg_color=[0.46, 0.70, 0.71, 1] if i == self.current_tab_index else [0.2, 0.2, 0.2, 0.8],
                text_color=[1, 1, 1, 1],
                on_release=lambda x, idx=i: self._select_tab(idx)
            )
            content.add_widget(btn)

        dialog = MDDialog(
            title="Выберите подбор",
            type="custom",
            content_cls=content,
            buttons=[MDRaisedButton(text="Закрыть", on_release=lambda x: dialog.dismiss())]
        )
        dialog.open()
        self.tabs_dialog = dialog

    def _select_tab(self, index):
        if hasattr(self, 'tabs_dialog'):
            self.tabs_dialog.dismiss()
        self.current_tab_index = index
        self._load_current_tab()

    # ==================== ОСНОВНЫЕ МЕТОДЫ ====================

    def reset_font_size(self):
        self.current_font_size = self.STANDARD_FONT_SIZE
        if hasattr(self, 'content_label'):
            self.content_label.font_size = self.current_font_size
            self._update_content_height()
        logger.info(f"🔍 Размер шрифта сброшен до стандартного: {self.current_font_size}")

    def reset_screen_state(self):
        self.current_tonality = 0
        self.transposed_chords_cache = {}
        self.transposed_text_cache = {}
        self.original_cleaned_text = ""

        if self.is_chords_mode:
            self.close_chords_section()
        if self.is_tonality_mode:
            self.cancel_tonality()
        if self.is_font_mode:
            self.cancel_font()
        if self.is_scroll_mode:
            self.close_scroll_panel()

        # Сброс темы на зелёную (по умолчанию)
        if hasattr(self, '_current_theme') and self._current_theme != 'green':
            self._set_green_theme()
            self._current_theme = 'green'
        elif not hasattr(self, '_current_theme'):
            self._current_theme = 'green'
            self._set_green_theme()

        self._current_chord_index = 0
        self.reset_font_size()
        self.display_mode = "finger"
        self.chord_variants = []
        self.chord_variant_index = 0
        self.scroll_speed = 1.0
        self.is_scrolling = False

        logger.info("🔄 Состояние экрана сброшено")

    def _extract_and_log_chords(self, text):
        chords = extract_chords_from_text(text)
        if chords:
            unique_chords = sorted(set(chords))
            chords_str = ', '.join(unique_chords)
            artist_part = f"{self.song_artist} - " if self.song_artist else ""
            name_part = self.song_title if self.song_title else "Песня"
            logger.info(f"🎸 Найдены аккорды в {artist_part}{name_part}: {chords_str}")
        return chords

    def _load_current_tab(self):
        if self.tabs and self.current_tab_index < len(self.tabs):
            tab = self.tabs[self.current_tab_index]
            raw_content = tab.get('content', 'Текст не загружен')
            cleaned = clean_text(raw_content)
            self._extract_and_log_chords(cleaned)
            if cleaned:
                highlighted_text = highlight_chords_in_text(cleaned)
                self.content_label.text = highlighted_text
                self.content_label.markup = True
            else:
                self.content_label.text = "Текст не загружен"
                self.content_label.markup = False
            self._update_content_height()
            Clock.schedule_once(lambda dt: setattr(self.content_scroll, 'scroll_y', 1), 0.1)

    def _update_content_height(self, *args):
        if not self.content_label.texture:
            Clock.schedule_once(lambda dt: self._update_content_height(), 0.05)
            return

        # Вычисляем высоту
        text_height = self.content_label.texture_size[1]
        self.content_label.height = max(dp(50), text_height + dp(8))

        # ОБНОВЛЯЕМ КОНТЕЙНЕР
        if self.content_label.parent:
            # Устанавливаем высоту контейнера
            self.content_label.parent.height = text_height + dp(16)
            # Принудительно обновляем minimum_height (для adaptive_height)
            if hasattr(self.content_label.parent, 'minimum_height'):
                self.content_label.parent.minimum_height = text_height + dp(16)

        # Принудительно прокручиваем вверх
        self.content_scroll.scroll_y = 1.0

    def _force_scroll_view_update(self, *args):
        """Принудительно обновляет ScrollView, чтобы он пересчитал размеры"""
        if hasattr(self, 'content_scroll'):
            # Принудительно обновляем размер ScrollView
            w, h = self.content_scroll.size
            self.content_scroll.size = (w, h + 1)
            Clock.schedule_once(lambda dt: setattr(self.content_scroll, 'size', (w, h)), 0.01)
            # Прокручиваем вверх
            self.content_scroll.scroll_y = 1.0
            logger.info("🔧 ScrollView обновлён")

    def set_song(self, song_id):
        self.reset_screen_state()
        self.song_id = song_id
        self.load_song_data()

    def load_song_data(self):
        self.show_loading()
        api.get_tab(
            song_id=self.song_id,
            on_success=self.on_song_loaded,
            on_failure=self.on_load_failed
        )

    def show_loading(self):
        if self.is_loading:
            return
        self.is_loading = True
        self.loading_spinner = LoadingSpinner()
        self.add_widget(self.loading_spinner)
        self.loading_spinner.start_animation()

    def hide_loading(self):
        self.is_loading = False
        if self.loading_spinner:
            self.loading_spinner.stop_animation()
            self.remove_widget(self.loading_spinner)
            self.loading_spinner = None

    def on_song_loaded(self, data):
        artist = data.get('artist') or 'Неизвестный'
        title = data.get('title') or 'Без названия'
        self.song_artist = artist
        self.song_title = title
        self.tabs = data.get('tabs', [])
        if not self.tabs and data.get('content'):
            self.tabs = [{'content': data.get('content', '')}]
        self.current_tab_index = 0
        if self.tabs:
            raw_content = self.tabs[0].get('content', 'Текст не загружен')
            cleaned = clean_text(raw_content)
            self._extract_and_cache_chords()
            self.precompute_transpositions(cleaned)
            original_text = self.transposed_text_cache.get(0, cleaned)
            self.content_label.text = original_text
            self.content_label.markup = True
            self._update_content_height()
        self.is_liked = data.get('is_liked', False)
        self.is_favorite = data.get('is_favorite', False)
        self.like_btn.icon = "heart" if self.is_liked else "heart-outline"
        self.favorite_btn.icon = "star" if self.is_favorite else "star-outline"

        self.update_top_nav_title()

        self.hide_loading()
        logger.info(f"Песня загружена, подборов: {len(self.tabs)}")

        # ЗАПУСКАЕМ ПРОВЕРКУ ГОТОВНОСТИ ТЕКСТА С БОЛЬШИМИ ЗАДЕРЖКАМИ
        for delay in [0.3, 0.5, 0.8, 1.0, 1.5, 2.0, 3.0]:
            Clock.schedule_once(self._wait_for_ready_and_scroll, delay)

        # ЗАПАСНОЙ ВАРИАНТ - ПРИНУДИТЕЛЬНАЯ ПРОКРУТКА
        for delay in [0.4, 0.6, 0.9, 1.2, 1.8, 2.5, 3.5]:
            Clock.schedule_once(lambda dt, d=delay: setattr(self.content_scroll, 'scroll_y', 1.0), delay)

    def on_load_failed(self, req, error):
        self.hide_loading()
        self.content_label.text = "Ошибка загрузки\nПроверьте интернет"
        notify.error("Ошибка загрузки песни")

    def toggle_like(self, *args):
        if not api.is_authenticated():
            app = MDApp.get_running_app()
            if app and hasattr(app, 'open_profile'):
                app.open_profile()
            return

        def on_success(result):
            self.is_liked = result.get('liked', not self.is_liked)
            self.like_btn.icon = "heart" if self.is_liked else "heart-outline"
            notify.success("Лайк поставлен!" if self.is_liked else "Лайк убран")

        def on_failure(req, error):
            notify.error("Ошибка")

        api.toggle_like(song_id=self.song_id, on_success=on_success, on_failure=on_failure)

    def toggle_favorite(self, *args):
        if not api.is_authenticated():
            app = MDApp.get_running_app()
            if app and hasattr(app, 'open_profile'):
                app.open_profile()
            return

        if self.is_favorite:
            def on_success(result):
                self.is_favorite = False
                self.favorite_btn.icon = "star-outline"
                notify.success("Удалено из избранного")
                self._refresh_favorites_screen()

            def on_failure(req, error):
                notify.error("Ошибка")

            api.remove_from_favorites(song_id=self.song_id, on_success=on_success, on_failure=on_failure)
        else:
            def on_success(result):
                self.is_favorite = True
                self.favorite_btn.icon = "star"
                notify.success("Добавлено в избранное")
                self._refresh_favorites_screen()

            def on_failure(req, error):
                notify.error("Ошибка")

            api.add_to_favorites(song_id=self.song_id, on_success=on_success, on_failure=on_failure)

    def _refresh_favorites_screen(self):
        if hasattr(self, 'manager') and self.manager:
            if self.manager.has_screen('favorites'):
                fav_screen = self.manager.get_screen('favorites')
                if hasattr(fav_screen, 'load_favorites'):
                    Clock.schedule_once(lambda dt: fav_screen.load_favorites(), 0.5)

    def go_back(self, instance=None):
        logger.info("🔙 Нажата кнопка возврата")
        if self.is_tonality_mode:
            self.cancel_tonality()
        if self.is_font_mode:
            self.cancel_font()
        if self.is_scroll_mode:
            self.close_scroll_panel()
        if self.is_chords_mode:
            self.close_chords_section()
        if self.manager and self.manager.has_screen('song_detail'):
            screen_state.clear_pending_chord()
            self.manager.current = 'song_detail'
            logger.info("✅ Принудительный возврат на song_detail")
        elif self.manager and self.manager.has_screen('home'):
            self.manager.current = 'home'

    def on_size(self, *args):
        """Вызывается при изменении размера экрана (поворот и т.д.)"""
        # Обновляем отступы при изменении размера
        if hasattr(self, '_top_spacer_song'):
            top_padding = layout_config.get_top_padding()
            if platform == 'android':
                top_padding = top_padding + dp(12)
            self._top_spacer_song.height = top_padding

        # Если текст загружен - запускаем проверку готовности
        if self.song_title and hasattr(self, 'content_label') and self.content_label.text:
            Clock.schedule_once(self._wait_for_ready_and_scroll, 0.3)

    def on_enter(self):
        """При входе на экран"""
        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            if hasattr(app, 'hide_bottom_nav'):
                app.hide_bottom_nav()

            app.top_nav._show_back_button()
            app.top_nav.back_btn.on_release = self.go_back

            if self.song_title:
                self.update_top_nav_title()
            else:
                app.top_nav.set_custom_title("Подбор")

        # Если песня уже загружена - запускаем проверку готовности
        if self.song_title and hasattr(self, 'content_label') and self.content_label.text:
            for delay in [0.2, 0.4, 0.6, 0.9, 1.2, 1.8, 2.5]:
                Clock.schedule_once(self._wait_for_ready_and_scroll, delay)
                # Правильный захват переменной для задержки + 0.1
                scroll_delay = delay + 0.1
                Clock.schedule_once(lambda dt, d=scroll_delay: setattr(self.content_scroll, 'scroll_y', 1.0),
                                    scroll_delay)

        # Обновляем отступы при входе
        if hasattr(self, '_top_spacer_song'):
            top_padding = layout_config.get_top_padding()
            if platform == 'android':
                top_padding = top_padding + dp(16)
            self._top_spacer_song.height = top_padding

    def on_leave(self):
        """При выходе с экрана"""
        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            if hasattr(app, 'show_bottom_nav'):
                app.show_bottom_nav()
            app.top_nav.reset_to_default()
        if self.is_tonality_mode:
            self.cancel_tonality()
        if self.is_font_mode:
            self.cancel_font()
        if self.is_scroll_mode:
            self.close_scroll_panel()
        if self.is_chords_mode:
            self.close_chords_section()

    def update_top_nav_title(self):
        """Обновляет заголовок в топ нав с названием песни и артистом"""
        app = MDApp.get_running_app()
        if not app or not hasattr(app, 'top_nav'):
            return

        from kivymd.uix.boxlayout import MDBoxLayout
        from kivymd.uix.label import MDLabel
        from kivy.metrics import sp, dp

        title_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            spacing=dp(2),
            padding=[dp(8), dp(4), dp(8), dp(4)]
        )

        song_name = self.song_title if self.song_title else "Подбор"
        song_title_label = MDLabel(
            text=song_name,
            font_size=sp(18),
            halign="center",
            valign="middle",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
            bold=True,
            shorten=True,
            shorten_from="right"
        )

        artist_name = self.song_artist if self.song_artist else ""
        artist_label = MDLabel(
            text=artist_name,
            font_size=sp(12),
            halign="center",
            valign="middle",
            theme_text_color="Custom",
            text_color=[0.9, 0.9, 0.9, 0.8],
            shorten=True,
            shorten_from="right"
        )

        title_container.add_widget(song_title_label)
        title_container.add_widget(artist_label)

        app.top_nav.set_custom_title_widget(title_container)