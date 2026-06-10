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

from config.theme import theme
from config.logger_config import screen_logger
from config.layout_config import layout_config
from config.system_bars import get_navigation_bar_height
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
            font_size=sp(14),
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
        self.size_hint = (None, None)
        self.size = (dp(32), dp(32))
        self.theme_icon_color = "Custom"
        if icon_color:
            self.icon_color = icon_color
        else:
            self.icon_color = [1, 1, 1, 0.85]
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

        # Настройки размера шрифта (стандартный 16, от 11 до 21)
        self.STANDARD_FONT_SIZE = 18
        self.current_font_size = self.STANDARD_FONT_SIZE

        # Для меню аккордов
        self._song_chords = []
        self._current_chord_index = 0
        self.chords_card = None
        self.chord_preview_renderer = None
        self.display_mode = "finger"
        self.chord_variants = []
        self.chord_variant_index = 0

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

        self.init_ui()
        self.load_background()

        logger.info('Экран просмотра песни создан')

    def set_previous_screen(self, screen_name):
        self.previous_screen = screen_name

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
        main_container = MDBoxLayout(orientation='vertical', size_hint=(1, 1), padding=[0, 0, 0, 0])

        top_padding = layout_config.get_top_padding()
        main_container.add_widget(Widget(size_hint_y=None, height=top_padding))

        main_container.add_widget(Widget(size_hint_y=None, height=dp(4)))

        content_padding = layout_config.get_content_padding()

        card_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            padding=[content_padding[0], 0, content_padding[2], content_padding[3]]
        )

        self.song_card = MDCard(
            orientation='vertical',
            size_hint=(1, 1),
            padding=[0, 0, 0, 0],
            spacing=0,
            radius=[18, 18, 18, 18],
            md_bg_color=[1, 1, 1, 0.98],
            elevation=2,
            line_color=[0.8, 0.8, 0.8, 0.3],
            line_width=0.5
        )

        self._create_top_menu()
        self.song_card.add_widget(self.top_menu)

        # Разделитель между шапкой и текстом
        top_separator = MDBoxLayout(size_hint=(1, None), height=1, md_bg_color=[0.8, 0.8, 0.8, 0.5])
        self.song_card.add_widget(top_separator)

        self.content_scroll = MDScrollView(
            size_hint=(1, 1),
            do_scroll_x=False,
            bar_width=3,
            bar_color=[0.5, 0.5, 0.5, 0.2],
            bar_inactive_color=[0.5, 0.5, 0.5, 0.1]
        )

        scroll_content = MDBoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=4,
            padding=[12, 8, 12, 8],
            adaptive_height=True
        )

        self.content_label = ChordTextLabel(
            text="",
            font_size=self.current_font_size,
            size_hint_y=None,
            theme_text_color="Custom",
            text_color=[0, 0, 0, 0.85],
            valign="top",
            line_height=1.4,
            markup=True
        )
        self.content_label.bind(texture_size=self._update_content_height)
        scroll_content.add_widget(self.content_label)

        self.content_scroll.add_widget(scroll_content)
        self.song_card.add_widget(self.content_scroll)

        self._create_bottom_panel()
        self.bottom_panel = self.normal_bottom_panel
        self.song_card.add_widget(self.bottom_panel)

        card_container.add_widget(self.song_card)
        main_container.add_widget(card_container)

        bottom_nav_height = dp(60)
        nav_bar_height = get_navigation_bar_height()
        total_bottom = bottom_nav_height + nav_bar_height + dp(12)
        main_container.add_widget(Widget(size_hint_y=None, height=total_bottom))

        self.add_widget(main_container)

        logger.info(f"SongDetailScreen: top_padding = {top_padding}dp, side_padding = {content_padding[0]}dp")

    def _create_top_menu(self):
        """Верхнее меню - название песни и артист (с серым фоном)"""
        self.top_menu = MDCard(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(50),
            padding=[dp(12), dp(8), dp(12), dp(4)],
            spacing=dp(2),
            radius=[18, 18, 0, 0],
            md_bg_color=[0.96, 0.96, 0.96, 0.95],
            elevation=0,
            line_color=[0.8, 0.8, 0.8, 0.2],
            line_width=0.5
        )

        row = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(34),
            spacing=dp(8),
            pos_hint={'center_y': 0.5}
        )

        self.song_icon = Image(
            size_hint=(None, None),
            size=(dp(28), dp(28)),
            pos_hint={'center_y': 0.5},
            allow_stretch=True,
            keep_ratio=True
        )
        if HAS_ASSETS:
            try:
                icon_data = load_asset_as_bytes('song_png')
                if icon_data:
                    img = CoreImage(BytesIO(icon_data), ext="png")
                    self.song_icon.texture = img.texture
            except:
                pass
        if not self.song_icon.texture:
            self.song_icon.text = "🎵"

        self.song_info_label = MDLabel(
            text="",
            font_size=sp(16),
            size_hint_x=1,
            theme_text_color="Custom",
            text_color=[0, 0, 0, 0.85],
            bold=True,
            valign="middle",
            shorten=True,
            shorten_from="right"
        )

        row.add_widget(self.song_icon)
        row.add_widget(self.song_info_label)

        self.top_menu.add_widget(row)

    def _create_bottom_panel(self):
        """Создаёт нижнюю панель с 6 кнопками (обычный режим)"""
        self.normal_bottom_panel = MDCard(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(52),
            padding=[dp(8), dp(4), dp(8), dp(4)],
            spacing=dp(4),
            radius=[0, 0, 18, 18],
            md_bg_color=[0.96, 0.96, 0.96, 0.95],
            elevation=0,
            line_color=[0.8, 0.8, 0.8, 0.2],
            line_width=0.5,
            pos_hint={'center_x': 0.5}
        )

        self.chords_btn = IconActionButton(
            icon_name="music",
            on_press_callback=self.on_chords_press,
            icon_color=[0.46, 0.70, 0.71, 1]
        )

        self.tonality_btn = IconActionButton(
            icon_name="tune",
            on_press_callback=self.show_tonality_panel,
            icon_color=[0.9, 0.7, 0.2, 0.9]
        )

        self.tabs_btn = IconActionButton(
            icon_name="folder-music",
            on_press_callback=self.show_tabs_picker,
            icon_color=[0.46, 0.70, 0.71, 0.9]
        )

        self.normal_bottom_panel.add_widget(self.chords_btn)
        self.normal_bottom_panel.add_widget(self.tonality_btn)
        self.normal_bottom_panel.add_widget(self.tabs_btn)

        spacer = Widget(size_hint_x=1)
        self.normal_bottom_panel.add_widget(spacer)

        self.favorite_btn = IconActionButton(
            icon_name="star-outline",
            on_press_callback=self.toggle_favorite,
            icon_color=[0.9, 0.7, 0.2, 0.9]
        )

        self.like_btn = IconActionButton(
            icon_name="heart-outline",
            on_press_callback=self.toggle_like,
            icon_color=[0.8, 0.3, 0.3, 0.9]
        )

        self.font_btn = IconActionButton(
            icon_name="magnify",
            on_press_callback=self.show_font_panel,
            icon_color=[0.46, 0.70, 0.71, 0.9]
        )

        self.normal_bottom_panel.add_widget(self.favorite_btn)
        self.normal_bottom_panel.add_widget(self.like_btn)
        self.normal_bottom_panel.add_widget(self.font_btn)

    # ==================== ПАНЕЛЬ ТОНАЛЬНОСТИ ====================

    def show_tonality_panel(self):
        """Показывает панель выбора тональности вместо обычного меню"""
        logger.info("🎵 Открытие панели тональности")

        # Закрываем другие меню если открыты
        if hasattr(self, 'chords_card') and self.chords_card:
            self._close_chords_card()
        if hasattr(self, 'tonality_card') and self.tonality_card:
            self._close_tonality_card(self.tonality_card, apply=False)
        if self.is_font_mode:
            self.close_font_panel()

        # Создаём панель тональности
        self.tonality_panel = MDCard(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(52),
            padding=[dp(8), dp(4), dp(8), dp(4)],
            spacing=dp(6),
            radius=[0, 0, 18, 18],
            md_bg_color=[0.96, 0.96, 0.96, 0.95],
            elevation=0,
            line_color=[0.8, 0.8, 0.8, 0.2],
            line_width=0.5,
            pos_hint={'center_x': 0.5}
        )

        title_label = MDLabel(
            text="Тональность",
            font_size=dp(8),
            halign="left",
            valign="middle",
            size_hint_x=None,
            width=dp(95),
            theme_text_color="Custom",
            text_color=[0, 0, 0, 0.85],
            bold=True
        )

        center_container = MDBoxLayout(
            orientation='horizontal',
            size_hint_x=1,
            spacing=dp(6),
            padding=[dp(2), dp(0), dp(2), dp(0)]
        )

        from kivymd.uix.slider import MDSlider

        current_slider_value = int(round(self.current_tonality * 2))

        self.tonality_slider = MDSlider(
            min=-6,
            max=6,
            value=current_slider_value,
            step=1,
            size_hint_x=1,
            height=dp(38),
            hint=False
        )

        self.tonality_slider_value_label = MDLabel(
            text=f"{current_slider_value:+d}" if current_slider_value != 0 else "0",
            font_size=sp(13),
            halign="center",
            size_hint_x=None,
            width=dp(28),
            theme_text_color="Custom",
            bold=True
        )

        self._update_tonality_label_color(current_slider_value)

        def on_slider_change(instance, value):
            int_value = int(round(value))
            self.tonality_slider.value = int_value

            if int_value == 0:
                self.tonality_slider_value_label.text = "0"
            else:
                self.tonality_slider_value_label.text = f"{int_value:+d}"

            self._update_tonality_label_color(int_value)

            step = int_value / 2
            if step != self.current_tonality:
                self.current_tonality = step
                self.apply_tonality(self.current_tonality)
                logger.info(f"🎵 Тональность изменена на: {self.current_tonality:.1f}")

        self.tonality_slider.bind(value=on_slider_change)

        center_container.add_widget(self.tonality_slider)
        center_container.add_widget(self.tonality_slider_value_label)

        self.tonality_apply_btn = IconActionButton(
            icon_name="check",
            on_press_callback=self.close_tonality_panel,
            icon_color=[0.46, 0.70, 0.71, 1]
        )

        self.tonality_panel.add_widget(title_label)
        self.tonality_panel.add_widget(center_container)
        self.tonality_panel.add_widget(self.tonality_apply_btn)

        self.song_card.remove_widget(self.bottom_panel)
        self.bottom_panel = self.tonality_panel
        self.song_card.add_widget(self.bottom_panel)

        self.is_tonality_mode = True

    def _update_tonality_label_color(self, value):
        """Обновляет цвет метки тональности"""
        if hasattr(self, 'tonality_slider_value_label'):
            if value < 0:
                self.tonality_slider_value_label.text_color = [0.8, 0.3, 0.3, 1]
            elif value > 0:
                self.tonality_slider_value_label.text_color = [0.3, 0.7, 0.3, 1]
            else:
                self.tonality_slider_value_label.text_color = [0, 0, 0, 0.85]

    def close_tonality_panel(self):
        """Закрывает панель тональности"""
        logger.info("🎵 Закрытие панели тональности")

        if self.normal_bottom_panel:
            self.song_card.remove_widget(self.bottom_panel)
            self.bottom_panel = self.normal_bottom_panel
            self.song_card.add_widget(self.bottom_panel)

        self.is_tonality_mode = False

    def cancel_tonality(self):
        """Отмена выбора тональности"""
        logger.info("🎵 Отмена изменения тональности")

        if self.is_tonality_mode:
            if self.current_tonality != 0:
                self.current_tonality = 0
                self.apply_tonality(0)
                logger.info("Тональность сброшена до оригинальной")

        self.close_tonality_panel()

    # ==================== ПАНЕЛЬ ШРИФТА ====================

    def show_font_panel(self):
        """Показывает панель выбора размера шрифта вместо обычного меню"""
        logger.info("🔍 Открытие панели шрифта")

        # Закрываем другие меню если открыты
        if hasattr(self, 'chords_card') and self.chords_card:
            self._close_chords_card()
        if hasattr(self, 'tonality_card') and self.tonality_card:
            self._close_tonality_card(self.tonality_card, apply=False)
        if self.is_tonality_mode:
            self.close_tonality_panel()

        # Создаём панель шрифта
        self.font_panel = MDCard(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(52),
            padding=[dp(8), dp(4), dp(8), dp(4)],
            spacing=dp(6),
            radius=[0, 0, 18, 18],
            md_bg_color=[0.96, 0.96, 0.96, 0.95],
            elevation=0,
            line_color=[0.8, 0.8, 0.8, 0.2],
            line_width=0.5,
            pos_hint={'center_x': 0.5}
        )

        title_label = MDLabel(
            text="Размер",
            font_size=dp(8),
            halign="left",
            valign="middle",
            size_hint_x=None,
            width=dp(65),
            theme_text_color="Custom",
            text_color=[0, 0, 0, 0.85],
            bold=True
        )

        # Знак минус
        minus_label = MDLabel(
            text="-",
            font_size=sp(16),
            halign="center",
            valign="middle",
            size_hint_x=None,
            width=dp(24),
            theme_text_color="Custom",
            text_color=[0.8, 0.3, 0.3, 0.9],
            bold=True
        )

        center_container = MDBoxLayout(
            orientation='horizontal',
            size_hint_x=1,
            spacing=dp(6),
            padding=[dp(2), dp(0), dp(2), dp(0)]
        )

        from kivymd.uix.slider import MDSlider

        # Значение слайдера = текущий размер минус стандартный
        current_slider_value = self.current_font_size - self.STANDARD_FONT_SIZE

        self.font_slider = MDSlider(
            min=-5,
            max=5,
            value=current_slider_value,
            step=1,
            size_hint_x=1,
            height=dp(38),
            hint=False
        )

        # Значение увеличения (например, 1.5x)
        self.font_slider_value_label = MDLabel(
            text=self._get_font_multiplier(self.current_font_size),
            font_size=sp(12),
            halign="center",
            size_hint_x=None,
            width=dp(40),
            theme_text_color="Custom",
            text_color=[0.46, 0.70, 0.71, 1],
            bold=True
        )

        # Знак плюс
        plus_label = MDLabel(
            text="+",
            font_size=sp(16),
            halign="center",
            valign="middle",
            size_hint_x=None,
            width=dp(24),
            theme_text_color="Custom",
            text_color=[0.3, 0.7, 0.3, 0.9],
            bold=True
        )

        def on_slider_change(instance, value):
            int_value = int(round(value))
            self.font_slider.value = int_value

            new_size = self.STANDARD_FONT_SIZE + int_value
            new_size = max(11, min(23, new_size))

            # Обновляем отображение множителя
            self.font_slider_value_label.text = self._get_font_multiplier(new_size)

            if new_size != self.current_font_size:
                self.current_font_size = new_size
                if hasattr(self, 'content_label'):
                    self.content_label.font_size = self.current_font_size
                    self._update_content_height()
                logger.info(
                    f"🔍 Размер шрифта изменён на: {self.current_font_size} ({self._get_font_multiplier(new_size)})")

        self.font_slider.bind(value=on_slider_change)

        center_container.add_widget(minus_label)
        center_container.add_widget(self.font_slider)
        center_container.add_widget(plus_label)
        center_container.add_widget(self.font_slider_value_label)

        self.font_apply_btn = IconActionButton(
            icon_name="check",
            on_press_callback=self.close_font_panel,
            icon_color=[0.46, 0.70, 0.71, 1]
        )

        self.font_panel.add_widget(title_label)
        self.font_panel.add_widget(center_container)
        self.font_panel.add_widget(self.font_apply_btn)

        self.song_card.remove_widget(self.bottom_panel)
        self.bottom_panel = self.font_panel
        self.song_card.add_widget(self.bottom_panel)

        self.is_font_mode = True

    def _get_font_multiplier(self, font_size):
        """Возвращает множитель увеличения шрифта с шагом 0.1x"""
        ratio = font_size / self.STANDARD_FONT_SIZE
        # Округляем до одного знака после запятой
        rounded = round(ratio * 10) / 10
        return f"{rounded:.1f}x"

    def close_font_panel(self):
        """Закрывает панель шрифта и возвращает обычное меню"""
        logger.info("🔍 Закрытие панели шрифта")

        if self.normal_bottom_panel:
            self.song_card.remove_widget(self.bottom_panel)
            self.bottom_panel = self.normal_bottom_panel
            self.song_card.add_widget(self.bottom_panel)

        self.is_font_mode = False

    def cancel_font(self):
        """Отмена выбора размера шрифта"""
        logger.info("🔍 Отмена изменения размера шрифта")

        if self.is_font_mode and self.current_font_size != self.STANDARD_FONT_SIZE:
            self.current_font_size = self.STANDARD_FONT_SIZE
            if hasattr(self, 'content_label'):
                self.content_label.font_size = self.current_font_size
                self._update_content_height()
            logger.info("Размер шрифта сброшен до стандартного")

        self.close_font_panel()

    # ==================== МЕНЮ АККОРДОВ ====================

    def on_chords_press(self):
        """Показывает всплывающую карточку с аккордами песни"""
        logger.info("🎸 Нажата кнопка аккордов")

        # Если в режиме тональности или шрифта, сначала выходим из них
        if self.is_tonality_mode:
            self.cancel_tonality()
        if self.is_font_mode:
            self.cancel_font()

        if not self._song_chords:
            notify.info("Аккорды не найдены в тексте песни")
            return

        if hasattr(self, 'chords_card') and self.chords_card:
            self._close_chords_card()
            return

        self._open_chords_card_with_chord(0)

    def _open_chords_card_with_chord(self, chord_index=0):
        """Открывает карточку аккордов с указанским индексом"""
        if not self._song_chords:
            return

        if chord_index >= len(self._song_chords):
            chord_index = 0

        self.chords_card = MDCard(
            orientation='vertical',
            size_hint=(None, None),
            size=(dp(320), dp(200)),
            spacing=dp(4),
            padding=[dp(8), dp(2), dp(8), dp(8)],
            radius=[20, 20, 20, 20],
            elevation=6,
            pos_hint={'center_x': 0.5},
            md_bg_color=[0.95, 0.95, 0.95, 0.95],
            adaptive_height=True
        )

        def update_card_position(*args):
            if not self.chords_card or not self.chords_card.parent:
                return

            screen_height = self.height

            if hasattr(self, 'bottom_panel'):
                bottom_panel_y = self.bottom_panel.y if self.bottom_panel.y > 0 else 0
                bottom_panel_height = self.bottom_panel.height
                panel_top = bottom_panel_y + bottom_panel_height
            else:
                panel_top = dp(60)

            target_y = panel_top + dp(8)

            if screen_height > 0:
                y_rel = target_y / screen_height
                self.chords_card.pos_hint = {'center_x': 0.5, 'y': y_rel}
                self.chords_card.pos = (self.chords_card.pos[0], target_y)

        # Верхняя строка
        top_row = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(32),
            spacing=dp(0),
            padding=[dp(0), dp(0), dp(0), dp(0)]
        )

        left_container = MDBoxLayout(
            size_hint_x=None,
            width=dp(56),
            spacing=dp(6),
            pos_hint={'center_y': 0.5}
        )

        self.variant_btn = IconImageButton(
            icon_name="variant_png",
            on_press_callback=self._next_chord_variant,
            size=dp(24),
            offset_y=0
        )
        left_container.add_widget(self.variant_btn)

        self.mode_btn = IconImageButton(
            icon_name="fingers_png" if self.display_mode == "finger" else "notes_png",
            on_press_callback=self._toggle_display_mode,
            size=dp(24),
            offset_y=0
        )
        left_container.add_widget(self.mode_btn)
        top_row.add_widget(left_container)

        self.chord_name_label = MDLabel(
            text=self._song_chords[chord_index] if self._song_chords else "",
            font_size=sp(18),
            halign="center",
            valign="middle",
            size_hint_x=1,
            theme_text_color="Custom",
            text_color=[0, 0, 0, 0.85],
            bold=True
        )
        top_row.add_widget(self.chord_name_label)

        right_container = MDBoxLayout(
            size_hint_x=None,
            width=dp(56),
            pos_hint={'center_y': 0.5}
        )

        close_container = MDBoxLayout(
            orientation='horizontal',
            size_hint_x=1,
            spacing=dp(0),
            padding=[dp(0), dp(0), dp(0), dp(0)]
        )
        close_container.add_widget(Widget(size_hint_x=1))
        self.close_btn = IconImageButton(
            icon_name="close_png",
            on_press_callback=lambda x: self._close_chords_card(),
            size=dp(22),
            offset_y=0,
            size_hint_x=None,
            width=dp(22)
        )
        close_container.add_widget(self.close_btn)
        right_container.add_widget(close_container)

        top_row.add_widget(right_container)

        self.chords_card.add_widget(top_row)

        # Основной контейнер для грифа и кнопок пагинации
        main_row = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(120),
            spacing=dp(4),
            padding=[dp(2), dp(0), dp(2), dp(0)]
        )

        self.chord_prev_btn = MDIconButton(
            icon="chevron-left",
            size_hint=(None, None),
            size=(dp(34), dp(34)),
            theme_icon_color="Custom",
            icon_color=[0.46, 0.70, 0.71, 1],
            md_bg_color=[0, 0, 0, 0],
            on_release=self._prev_chord_in_card,
            ripple_scale=0,
            pos_hint={'center_y': 0.5}
        )

        griff_container = MDBoxLayout(
            orientation='vertical',
            size_hint_x=1,
            padding=[dp(1), dp(0), dp(1), dp(0)]
        )

        self.chord_preview_renderer = ChordRenderer()
        griff_container.add_widget(self.chord_preview_renderer)

        try:
            griff_data = load_asset_as_bytes("griff_png")
            if griff_data:
                griff_img = CoreImage(BytesIO(griff_data), ext="png")
                if griff_img and griff_img.texture:
                    self.chord_preview_renderer.set_background(griff_img.texture)
        except Exception as e:
            logger.error(f"Ошибка загрузки фона грифа: {e}")

        self.chord_next_btn = MDIconButton(
            icon="chevron-right",
            size_hint=(None, None),
            size=(dp(34), dp(34)),
            theme_icon_color="Custom",
            icon_color=[0.46, 0.70, 0.71, 1],
            md_bg_color=[0, 0, 0, 0],
            on_release=self._next_chord_in_card,
            ripple_scale=0,
            pos_hint={'center_y': 0.5}
        )

        main_row.add_widget(self.chord_prev_btn)
        main_row.add_widget(griff_container)
        main_row.add_widget(self.chord_next_btn)

        self.chords_card.add_widget(main_row)

        self.chord_desc_label = MDLabel(
            text="",
            font_size=sp(10),
            halign="center",
            size_hint=(1, None),
            height=dp(20),
            theme_text_color="Custom",
            text_color=[0.5, 0.5, 0.5, 0.7],
            shorten=True,
            shorten_from="right"
        )
        self.chords_card.add_widget(self.chord_desc_label)

        self.add_widget(self.chords_card)

        Clock.schedule_once(lambda dt: update_card_position(), 0.1)
        self.bind(size=update_card_position)

        self._current_chord_index = chord_index
        self._update_chord_display()

        self._load_chord_variants(self._song_chords[chord_index])

    def _update_chord_description(self, chord_name):
        desc = self._get_chord_description(chord_name)
        if hasattr(self, 'chord_desc_label'):
            self.chord_desc_label.text = desc

    def _load_chord_variants(self, chord_name):
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

            if self.chord_variants:
                self.load_current_variant()

        if hasattr(self, 'variant_btn'):
            self.variant_btn.opacity = 1 if len(self.chord_variants) > 1 else 0.5

    def load_current_variant(self):
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

        if self.chord_variants and self.chord_variant_index < len(self.chord_variants):
            variant_data = self.chord_variants[self.chord_variant_index]
            description = variant_data.get('description', '')
            if description:
                parts = description.replace('!', '|').split('|')
                if parts and hasattr(self, 'chord_desc_label'):
                    self.chord_desc_label.text = parts[0].strip()

    def _next_chord_variant(self, *args):
        if not self.chord_variants:
            return

        total = len(self.chord_variants)
        self.chord_variant_index = (self.chord_variant_index + 1) % total
        self.load_current_variant()

    def _toggle_display_mode(self, *args):
        if self.display_mode == "finger":
            self.display_mode = "notes"
            if hasattr(self, 'mode_btn'):
                self.mode_btn.icon_name = "notes_png"
                self.mode_btn._load_icon()
        else:
            self.display_mode = "finger"
            if hasattr(self, 'mode_btn'):
                self.mode_btn.icon_name = "fingers_png"
                self.mode_btn._load_icon()

        if hasattr(self, 'chord_preview_renderer') and self.chord_preview_renderer:
            self.chord_preview_renderer.set_mode(self.display_mode)
            if self.chord_variants:
                self.load_current_variant()
        logger.info(f"Режим отображения изменён на: {self.display_mode}")

    def _close_chords_card(self):
        if hasattr(self, 'chords_card') and self.chords_card:
            self.remove_widget(self.chords_card)
            self.chords_card = None

    def _extract_and_cache_chords(self):
        chords = set()

        for tab in self.tabs:
            content = tab.get('content', '')
            if content:
                cleaned = clean_text(content)
                extracted = extract_chords_from_text(cleaned)
                chords.update(extracted)

        self._song_chords = sorted(list(chords))
        logger.info(f"🎸 Найдено аккордов в песне: {len(self._song_chords)} - {self._song_chords}")

    def _get_chord_description(self, chord_name):
        if self.manager and self.manager.has_screen('chords'):
            chords_screen = self.manager.get_screen('chords')
            for chord in chords_screen.all_chords:
                if chord['short_name'].lower() == chord_name.lower():
                    description = chord.get('description', '')
                    if description:
                        parts = description.replace('!', '|').split('|')
                        if parts:
                            return parts[0].strip()
                    return chord.get('type', 'Аккорд')
        return 'Аккорд'

    def _update_chord_display(self):
        if not self._song_chords:
            return

        chord_name = self._song_chords[self._current_chord_index]

        if hasattr(self, 'chord_name_label'):
            self.chord_name_label.text = chord_name

        self._update_chord_description(chord_name)

        if hasattr(self, 'chord_prev_btn'):
            self.chord_prev_btn.disabled = False
            self.chord_prev_btn.opacity = 1

        if hasattr(self, 'chord_next_btn'):
            self.chord_next_btn.disabled = False
            self.chord_next_btn.opacity = 1

    def _prev_chord_in_card(self, *args):
        if not self._song_chords:
            return

        total = len(self._song_chords)
        if self._current_chord_index == 0:
            self._current_chord_index = total - 1
        else:
            self._current_chord_index -= 1

        chord = self._song_chords[self._current_chord_index]
        self._update_chord_display()
        self._load_chord_variants(chord)

    def _next_chord_in_card(self, *args):
        if not self._song_chords:
            return

        total = len(self._song_chords)
        if self._current_chord_index == total - 1:
            self._current_chord_index = 0
        else:
            self._current_chord_index += 1

        chord = self._song_chords[self._current_chord_index]
        self._update_chord_display()
        self._load_chord_variants(chord)

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

            if hasattr(self, 'chords_card') and self.chords_card:
                if self._song_chords:
                    if self._current_chord_index >= len(self._song_chords):
                        self._current_chord_index = 0
                    self.chord_name_label.text = self._song_chords[self._current_chord_index]
                    self._load_chord_variants(self._song_chords[self._current_chord_index])

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

        if hasattr(self, 'chords_card') and self.chords_card:
            self._close_chords_card()

        if self.is_tonality_mode:
            self.cancel_tonality()
        if self.is_font_mode:
            self.cancel_font()

        self._current_chord_index = 0
        self.reset_font_size()
        self.display_mode = "finger"
        self.chord_variants = []
        self.chord_variant_index = 0

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
        text_height = self.content_label.texture_size[1]
        self.content_label.height = max(dp(50), text_height + dp(8))
        if self.content_label.parent:
            self.content_label.parent.height = text_height + dp(16)

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

        self.song_info_label.text = f"{artist} - {title}"

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

        Clock.schedule_once(lambda dt: setattr(self.content_scroll, 'scroll_y', 1), 0.1)
        self.hide_loading()
        logger.info(f"Песня загружена, подборов: {len(self.tabs)}")

    def on_load_failed(self, req, error):
        self.hide_loading()
        self.content_label.text = "Ошибка загрузки\nПроверьте интернет"
        notify.error("Ошибка загрузки песни")

    def toggle_like(self, *args):
        if not api.is_authenticated():
            notify.warning("Войдите, чтобы ставить лайки")
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
            notify.warning("Войдите, чтобы добавлять в избранное")
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

        if self.manager and self.manager.has_screen('song_detail'):
            screen_state.clear_pending_chord()
            self.manager.current = 'song_detail'
            logger.info("✅ Принудительный возврат на song_detail")
        elif self.manager and self.manager.has_screen('home'):
            self.manager.current = 'home'

    def on_enter(self):
        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            app.top_nav.set_custom_title("Подбор")
            app.top_nav._show_back_button()
            app.top_nav.back_btn.on_release = self.go_back

    def on_leave(self):
        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            app.top_nav.reset_to_default()

        if self.is_tonality_mode:
            self.cancel_tonality()
        if self.is_font_mode:
            self.cancel_font()

        if hasattr(self, 'chords_card') and self.chords_card:
            self._close_chords_card()
        if hasattr(self, 'tonality_card') and self.tonality_card:
            self._close_tonality_card(self.tonality_card, apply=False)