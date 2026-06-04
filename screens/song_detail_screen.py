# screens/song_detail_screen.py - с классом из chords_screen
"""
Экран просмотра песни с текстом и подборами
"""
from kivymd.app import MDApp
from kivymd.uix.label import MDLabel
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDIconButton
from kivymd.uix.boxlayout import MDBoxLayout
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
from api.client import api
from utils.notifications import notify

logger = screen_logger('SongDetail')

try:
    from data import load_asset_as_bytes

    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False


    def load_asset_as_bytes(name):
        return None


def clean_text(text):
    """Очищает текст от HTML тегов и сохраняет специальные символы"""
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', '', text)
    html_entities = {
        '&amp;': '&', '&lt;': '<', '&gt;': '>', '&quot;': '"',
        '&apos;': "'", '&nbsp;': ' ', '&#39;': "'", '&#34;': '"',
        '&#38;': '&', '&#60;': '<', '&#62;': '>', '&#171;': '«',
        '&#187;': '»', '&#169;': '©', '&#174;': '®', '&#8364;': '€',
        '&#8470;': '№', '&#8211;': '–', '&#8212;': '—', '&#8216;': "'",
        '&#8217;': "'", '&#8220;': '"', '&#8221;': '"', '&#8230;': '…',
    }
    for entity, char in html_entities.items():
        text = text.replace(entity, char)
    lines = text.split('\n')
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
        return '\n'.join(lines[4:])
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


class IconImageButton(ButtonBehavior, Image):
    """Кнопка с иконкой из PNG ассета"""

    def __init__(self, icon_name, on_press_callback=None, size=dp(18), **kwargs):
        super().__init__(**kwargs)
        self.icon_name = icon_name
        self.on_press_callback = on_press_callback
        self.size_hint = (None, None)
        self.size = (size, size)
        self.allow_stretch = True
        self.keep_ratio = True
        self.bind(on_release=self._on_press)
        self._load_icon()

    def _load_icon(self):
        if HAS_ASSETS:
            try:
                icon_data = load_asset_as_bytes(self.icon_name)
                if icon_data:
                    img = CoreImage(BytesIO(icon_data), ext="png")
                    self.texture = img.texture
                    return
            except Exception as e:
                logger.error(f"Ошибка загрузки иконки {self.icon_name}: {e}")
        self.opacity = 0

    def _on_press(self, instance):
        if self.on_press_callback:
            self.on_press_callback(self.icon_name)


class FontSizeButton(MDIconButton):
    """Кнопка изменения размера шрифта (меняет иконку +/ -)"""

    def __init__(self, on_press_callback=None, **kwargs):
        super().__init__(**kwargs)
        self.on_press_callback = on_press_callback
        self.size_hint = (None, None)
        self.size = (dp(28), dp(28))
        self.theme_icon_color = "Custom"
        self.icon_color = [0.46, 0.70, 0.71, 0.9]
        self.md_bg_color = [0, 0, 0, 0]
        self.icon = "magnify-plus"
        self.bind(on_release=self._on_press)

    def set_icon_plus(self):
        self.icon = "magnify-plus"

    def set_icon_minus(self):
        self.icon = "magnify-minus"

    def _on_press(self, instance):
        if self.on_press_callback:
            self.on_press_callback()


class SongDetailScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'song_detail'
        self.song_id = None
        self.is_liked = False
        self.is_favorite = False
        self.is_loading = False
        self.loading_spinner = None
        self.bg_image = None
        self.previous_screen = 'artist_songs'
        self.current_tonality = 0
        self.tabs = []
        self.current_tab_index = 0

        # Настройки размера шрифта
        self.current_font_size = 14
        self.font_size_levels = [10, 12, 14, 16, 18, 20, 22]
        self.font_size_index = 2  # 14

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

        # Дополнительный отступ сверху для эстетики
        main_container.add_widget(Widget(size_hint_y=None, height=dp(8)))

        # Получаем единые боковые отступы из layout_config
        content_padding = layout_config.get_content_padding()

        # Карточка с текстом - с едиными боковыми отступами, растянутая до низа
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
            radius=[12, 12, 12, 12],
            md_bg_color=[1, 1, 1, 0.98],
            elevation=2,
            line_color=[0.8, 0.8, 0.8, 0.3],
            line_width=0.5
        )

        # Верхнее меню (шапка с артистом и песней)
        self._create_top_menu()
        self.song_card.add_widget(self.top_menu)

        # Разделитель
        top_separator = MDBoxLayout(size_hint=(1, None), height=1, md_bg_color=[0.85, 0.85, 0.85, 0.8])
        self.song_card.add_widget(top_separator)

        # Панель управления (тональность, подборы)
        self._create_control_panel()
        self.song_card.add_widget(self.control_panel)

        # Разделитель после панели
        panel_separator = MDBoxLayout(size_hint=(1, None), height=1, md_bg_color=[0.85, 0.85, 0.85, 0.5])
        self.song_card.add_widget(panel_separator)

        # Контейнер для текста
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

        self.content_label = MDLabel(
            text="",
            font_size=self.current_font_size,
            size_hint_y=None,
            theme_text_color="Custom",
            text_color=[0, 0, 0, 0.85],
            valign="top",
            line_height=1.4
        )
        self.content_label.bind(texture_size=self._update_content_height)
        scroll_content.add_widget(self.content_label)

        self.content_scroll.add_widget(scroll_content)
        self.song_card.add_widget(self.content_scroll)

        card_container.add_widget(self.song_card)
        main_container.add_widget(card_container)

        # Нижний отступ для BottomNav
        bottom_nav_height = dp(60)
        nav_bar_height = get_navigation_bar_height()
        total_bottom = bottom_nav_height + nav_bar_height + dp(12)
        main_container.add_widget(Widget(size_hint_y=None, height=total_bottom))

        self.add_widget(main_container)

        logger.info(f"SongDetailScreen: top_padding = {top_padding}dp, side_padding = {content_padding[0]}dp")

    def _create_top_menu(self):
        """Верхнее меню с информацией об артисте и песне, а также кнопками действий"""
        self.top_menu = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(60),
            padding=[dp(12), dp(6), dp(12), dp(2)],
            spacing=dp(2),
            md_bg_color=[1, 1, 1, 0]
        )

        # Первая строка: артист, действия, кнопка изменения шрифта
        row1 = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(28),
            spacing=dp(6)
        )

        # Иконка артиста
        self.artist_icon = Image(
            size_hint=(None, None),
            size=(dp(24), dp(24)),
            pos_hint={'center_y': 0.5},
            allow_stretch=True,
            keep_ratio=True
        )
        if HAS_ASSETS:
            try:
                icon_data = load_asset_as_bytes('artist_png')
                if icon_data:
                    img = CoreImage(BytesIO(icon_data), ext="png")
                    self.artist_icon.texture = img.texture
            except:
                pass

        # Имя артиста (растягивается)
        self.artist_label = MDLabel(
            text="",
            font_size=sp(15),
            size_hint_x=1,
            theme_text_color="Custom",
            text_color=[0, 0, 0, 0.85],
            bold=True,
            valign="middle",
            shorten=False
        )

        # Кнопка "Избранное"
        self.favorite_btn = MDIconButton(
            icon="star-outline",
            size_hint=(None, None),
            size=(dp(28), dp(28)),
            theme_icon_color="Custom",
            icon_color=[0.9, 0.7, 0.2, 0.9],
            md_bg_color=[0, 0, 0, 0],
            on_release=self.toggle_favorite
        )

        # Кнопка "Лайк"
        self.like_btn = MDIconButton(
            icon="heart-outline",
            size_hint=(None, None),
            size=(dp(28), dp(28)),
            theme_icon_color="Custom",
            icon_color=[0.8, 0.3, 0.3, 0.9],
            md_bg_color=[0, 0, 0, 0],
            on_release=self.toggle_like
        )

        # Кнопка изменения размера шрифта (меняет иконку)
        self.font_btn = FontSizeButton(on_press_callback=self.cycle_font_size)

        row1.add_widget(self.artist_icon)
        row1.add_widget(self.artist_label)
        row1.add_widget(self.favorite_btn)
        row1.add_widget(self.like_btn)
        row1.add_widget(self.font_btn)

        # Вторая строка: название песни
        row2 = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(22),
            spacing=dp(6)
        )

        # Иконка песни
        self.song_icon = Image(
            size_hint=(None, None),
            size=(dp(20), dp(20)),
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

        # Название песни
        self.song_title_label = MDLabel(
            text="",
            font_size=sp(12),
            size_hint_x=1,
            theme_text_color="Custom",
            text_color=[0.4, 0.4, 0.4, 0.9],
            valign="middle",
            shorten=False,
            bold=True
        )

        # Пустой виджет для баланса (под 3 кнопки)
        spacer = Widget(size_hint_x=None, width=dp(28 + 28 + 28))

        row2.add_widget(self.song_icon)
        row2.add_widget(self.song_title_label)
        row2.add_widget(spacer)

        self.top_menu.add_widget(row1)
        self.top_menu.add_widget(row2)

    def _create_control_panel(self):
        """Создаёт панель управления: Тональность и Подбор - всё в одну строку по размеру содержимого"""
        self.control_panel = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(32),
            padding=[dp(8), dp(2), dp(8), dp(2)],
            spacing=dp(6),
            md_bg_color=[0.96, 0.96, 0.96, 0.5]
        )

        # Блок 1: Тональность (ширина по содержимому)
        tonality_section = MDBoxLayout(
            orientation='horizontal',
            size_hint_x=None,
            width=dp(110),  # 58(текст) + 18(минус) + 20(цифра) + 18(плюс) + отступы
            spacing=dp(2),
            pos_hint={'center_y': 0.5}
        )

        tonality_label = MDLabel(
            text="Тональность",
            font_size=sp(9),
            size_hint_x=None,
            width=dp(58),
            halign="left",
            valign="middle",
            theme_text_color="Custom",
            text_color=[0.4, 0.4, 0.4, 0.8],
            bold=False
        )

        # Минус
        self.tonality_minus_btn = IconImageButton(
            icon_name='minus_ton_png',
            on_press_callback=self.decrease_tonality,
            size=dp(18)
        )

        self.tonality_value_label = MDLabel(
            text=str(self.current_tonality),
            font_size=sp(12),
            size_hint_x=None,
            width=dp(20),
            halign="center",
            valign="middle",
            theme_text_color="Custom",
            text_color=[0.9, 0.7, 0.2, 1],
            bold=True
        )

        # Плюс
        self.tonality_plus_btn = IconImageButton(
            icon_name='plus_ton_png',
            on_press_callback=self.increase_tonality,
            size=dp(18)
        )

        tonality_section.add_widget(tonality_label)
        tonality_section.add_widget(self.tonality_minus_btn)
        tonality_section.add_widget(self.tonality_value_label)
        tonality_section.add_widget(self.tonality_plus_btn)

        # Разделитель
        divider = MDBoxLayout(size_hint_x=None, width=dp(1), md_bg_color=[0.8, 0.8, 0.8, 0.5])

        # Блок 2: Подбор (ширина по содержимому)
        tabs_section = MDBoxLayout(
            orientation='horizontal',
            size_hint_x=None,
            width=dp(92),  # 38(текст) + 18(стрелка) + 20(цифра) + 18(стрелка) + отступы
            spacing=dp(2),
            pos_hint={'center_y': 0.5}
        )

        tabs_label = MDLabel(
            text="Подбор",
            font_size=sp(9),
            size_hint_x=None,
            width=dp(38),
            halign="left",
            valign="middle",
            theme_text_color="Custom",
            text_color=[0.4, 0.4, 0.4, 0.8],
            bold=False
        )

        # Стрелка влево
        self.tabs_prev_btn = IconImageButton(
            icon_name='left_arrow_png',
            on_press_callback=self.prev_tab,
            size=dp(18)
        )

        self.tabs_value_label = MDLabel(
            text="1",
            font_size=sp(12),
            size_hint_x=None,
            width=dp(20),
            halign="center",
            valign="middle",
            theme_text_color="Custom",
            text_color=[0.46, 0.70, 0.71, 1],
            bold=True
        )

        # Стрелка вправо
        self.tabs_next_btn = IconImageButton(
            icon_name='right_arrow_png',
            on_press_callback=self.next_tab,
            size=dp(18)
        )

        tabs_section.add_widget(tabs_label)
        tabs_section.add_widget(self.tabs_prev_btn)
        tabs_section.add_widget(self.tabs_value_label)
        tabs_section.add_widget(self.tabs_next_btn)

        # Spacer для выравнивания влево
        spacer = Widget(size_hint_x=1)

        self.control_panel.add_widget(tonality_section)
        self.control_panel.add_widget(divider)
        self.control_panel.add_widget(tabs_section)
        self.control_panel.add_widget(spacer)

    def cycle_font_size(self):
        """Циклическое изменение размера шрифта при нажатии на кнопку"""
        self.font_size_index = (self.font_size_index + 1) % len(self.font_size_levels)
        self.current_font_size = self.font_size_levels[self.font_size_index]
        self.content_label.font_size = self.current_font_size
        self._update_content_height()

        # Меняем иконку в зависимости от положения
        if self.font_size_index == len(self.font_size_levels) - 1:
            self.font_btn.set_icon_minus()
        else:
            self.font_btn.set_icon_plus()

        # Визуальная обратная связь
        anim = Animation(opacity=0.5, duration=0.05) + Animation(opacity=1, duration=0.1)
        anim.start(self.font_btn)

        logger.info(f"Размер шрифта: {self.current_font_size}")

    def _update_tab_display(self):
        if self.tabs and len(self.tabs) > 1:
            self.tabs_value_label.text = str(self.current_tab_index + 1)
        elif self.tabs and len(self.tabs) == 1:
            self.tabs_value_label.text = "1"
        else:
            self.tabs_value_label.text = "—"

    def prev_tab(self, *args):
        if self.tabs and len(self.tabs) > 1:
            self.current_tab_index = (self.current_tab_index - 1) % len(self.tabs)
            self._load_current_tab()

    def next_tab(self, *args):
        if self.tabs and len(self.tabs) > 1:
            self.current_tab_index = (self.current_tab_index + 1) % len(self.tabs)
            self._load_current_tab()

    def _load_current_tab(self):
        if self.tabs and self.current_tab_index < len(self.tabs):
            tab = self.tabs[self.current_tab_index]
            raw_content = tab.get('content', 'Текст не загружен')
            cleaned = clean_text(raw_content)
            self.content_label.text = cleaned if cleaned else "Текст не загружен"
            self._update_content_height()
            self._update_tab_display()
            Clock.schedule_once(lambda dt: setattr(self.content_scroll, 'scroll_y', 1), 0.1)

    def _update_content_height(self, *args):
        if not self.content_label.texture:
            Clock.schedule_once(lambda dt: self._update_content_height(), 0.05)
            return
        text_height = self.content_label.texture_size[1]
        self.content_label.height = max(dp(50), text_height + dp(8))
        if self.content_label.parent:
            self.content_label.parent.height = text_height + dp(16)

    def increase_tonality(self, *args):
        if self.current_tonality < 7:
            self.current_tonality += 1
            self.tonality_value_label.text = str(self.current_tonality)

    def decrease_tonality(self, *args):
        if self.current_tonality > -7:
            self.current_tonality -= 1
            self.tonality_value_label.text = str(self.current_tonality)

    def set_song(self, song_id):
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

        self.tabs = data.get('tabs', [])
        if not self.tabs and data.get('content'):
            self.tabs = [{'content': data.get('content', '')}]

        self.current_tab_index = 0

        self.artist_label.text = artist
        self.song_title_label.text = title

        if self.tabs:
            raw_content = self.tabs[0].get('content', 'Текст не загружен')
            cleaned = clean_text(raw_content)
            self.content_label.text = cleaned if cleaned else "Текст не загружен"
            self._update_content_height()

        self.is_liked = data.get('is_liked', False)
        self.is_favorite = data.get('is_favorite', False)

        self.like_btn.icon = "heart" if self.is_liked else "heart-outline"
        self.favorite_btn.icon = "star" if self.is_favorite else "star-outline"

        self._update_tab_display()

        Clock.schedule_once(lambda dt: setattr(self.content_scroll, 'scroll_y', 1), 0.1)
        self.hide_loading()
        logger.info(f"Песня загружена, подборов: {len(self.tabs)}")

    def on_load_failed(self, req, error):
        self.hide_loading()
        self.content_label.text = "Ошибка загрузки\nПроверьте интернет"
        notify.error("Ошибка загрузки песни")

    def toggle_like(self, instance):
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

    def toggle_favorite(self, instance):
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
        if hasattr(self, 'manager') and self.manager:
            self.manager.current = self.previous_screen

    def on_enter(self):
        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            app.top_nav.set_custom_title("Подбор песни")
            app.top_nav._show_back_button()
            app.top_nav.back_btn.on_release = self.go_back

    def on_leave(self):
        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            app.top_nav.reset_to_default()