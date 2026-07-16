# screens/search_screen_detail.py
"""
Экран просмотра песни ИЗ ОБЩЕГО ПОИСКА (search_screen)
Возврат только в SearchScreen с сохранением результатов поиска
"""
from kivymd.app import MDApp
from kivymd.uix.label import MDLabel
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDIconButton, MDRaisedButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.metrics import dp, sp
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.core.image import Image as CoreImage
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from io import BytesIO
import re

from config.theme import theme
from config.logger_config import screen_logger
from config.layout_config import layout_config
from config.system_bars import get_navigation_bar_height
from screens.base_screen import BaseScreen
from screens.chord_renderer import ChordRenderer
from api.client import api
from utils.notifications import notify
from utils.screen_state import screen_state
from utils.chord_highlighter import (
    ChordTextLabel,
    highlight_chords_in_text,
    extract_chords_from_text_wrapper as extract_chords_from_text,
)
from utils.transposer import transpose_text, transpose_chord_list

logger = screen_logger('SearchScreenDetail')

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
    temp_text = re.sub(r'<[^>]+>', '', text)
    html_entities = {
        '&amp;': '&', '&lt;': '<', '&gt;': '>', '&quot;': '"',
        '&apos;': "'", '&nbsp;': ' ', '&#39;': "'", '&#34;': '"',
        '&#38;': '&', '&#60;': '<', '&#62;': '>', '&#171;': '«',
        '&#187;': '»', '&#169;': '©', '&#174;': '®', '&#8364;': '€',
        '&#8470;': '№', '&#8211;': '–', '&#8212;': '—', '&#8216;': "'",
        '&#8217;': "'", '&#8220;': '"', '&#8221;': '"', '&#8230;': '…',
        '&#35;': '#', '%23': '#',
    }
    for entity, char in html_entities.items():
        temp_text = temp_text.replace(entity, char)

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


class SearchScreenDetail(BaseScreen):
    """
    Экран просмотра песни ИЗ ОБЩЕГО ПОИСКА (search_screen)
    Возврат ТОЛЬКО в SearchScreen
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'search_screen_detail'
        self.song_id = None
        self.song_title = None
        self.song_artist = None
        self.is_liked = False
        self.is_favorite = False
        self.is_loading = False
        self.loading_spinner = None
        self.bg_image = None
        self.current_tonality = 0
        self.tabs = []
        self.current_tab_index = 0
        self.content_label = None
        self.content_scroll = None
        self._text_container = None
        self.song_card = None
        self._top_spacer = None

        # Настройки размера шрифта
        from kivy.utils import platform
        if platform == 'android':
            self.STANDARD_FONT_SIZE = 42
            self.MIN_FONT_SIZE = 30
            self.MAX_FONT_SIZE = 60
        else:
            self.STANDARD_FONT_SIZE = 20
            self.MIN_FONT_SIZE = 14
            self.MAX_FONT_SIZE = 32
        self.current_font_size = self.STANDARD_FONT_SIZE

        self.init_ui()
        self.load_background()
        logger.info('Экран просмотра песни из общего поиска создан')

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
        if top_padding < dp(48):
            top_padding = dp(48)
        self._top_spacer = Widget(size_hint_y=None, height=top_padding)
        main_container.add_widget(self._top_spacer)

        bottom_nav_total = layout_config.get_bottom_nav_total_height()
        bottom_padding = bottom_nav_total

        card_container = MDBoxLayout(orientation='vertical', size_hint=(1, 1), padding=[0, 0, 0, 0])

        self.song_card = MDCard(
            orientation='vertical',
            size_hint=(1, 1),
            padding=[0, 0, 0, bottom_padding],
            spacing=0,
            radius=[0, 0, 0, 0],
            md_bg_color=[0, 0, 0, 0],
            elevation=0
        )

        # Верхний разделитель
        top_divider = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(2),
            md_bg_color=[0.5, 0.5, 0.5, 0.3]
        )
        self.song_card.add_widget(top_divider)

        # Скролл для текста
        self.content_scroll = MDScrollView(
            size_hint=(1, 1),
            do_scroll_x=False,
            bar_width=3,
            bar_color=[0.5, 0.5, 0.5, 0.3],
            bar_inactive_color=[0.5, 0.5, 0.5, 0.1]
        )

        self._text_container = MDBoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=4,
            padding=[dp(16), dp(16), dp(16), dp(4)],
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

        # Нижний разделитель
        bottom_divider = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(2),
            md_bg_color=[0.5, 0.5, 0.5, 0.3]
        )
        self.song_card.add_widget(bottom_divider)

        card_container.add_widget(self.song_card)
        main_container.add_widget(card_container)

        self.add_widget(main_container)

        # Кнопки управления в TopNav
        Clock.schedule_once(self._setup_top_nav_buttons, 0.1)

    def _setup_top_nav_buttons(self, dt):
        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            if hasattr(app.top_nav, 'right_container'):
                # Очищаем правую часть
                app.top_nav.right_container.clear_widgets()

                # Кнопка избранного
                self.fav_btn = MDIconButton(
                    icon="star-outline",
                    size_hint=(None, None),
                    size=(dp(40), dp(40)),
                    theme_icon_color="Custom",
                    icon_color=[0.9, 0.7, 0.2, 0.9],
                    md_bg_color=[0, 0, 0, 0],
                    on_release=self.toggle_favorite
                )

                # Кнопка лайка
                self.like_btn = MDIconButton(
                    icon="heart-outline",
                    size_hint=(None, None),
                    size=(dp(40), dp(40)),
                    theme_icon_color="Custom",
                    icon_color=[0.8, 0.3, 0.3, 0.9],
                    md_bg_color=[0, 0, 0, 0],
                    on_release=self.toggle_like
                )

                app.top_nav.right_container.add_widget(self.like_btn)
                app.top_nav.right_container.add_widget(self.fav_btn)

    def _update_content_height(self, *args):
        if not self.content_label.texture:
            Clock.schedule_once(lambda dt: self._update_content_height(), 0.05)
            return

        text_height = self.content_label.texture_size[1]
        self.content_label.height = max(dp(50), text_height + dp(8))
        if self.content_label.parent:
            self.content_label.parent.height = text_height + dp(16)
            if hasattr(self.content_label.parent, 'minimum_height'):
                self.content_label.parent.minimum_height = text_height + dp(16)

        if self.content_scroll:
            self.content_scroll.scroll_y = 1.0

    def set_song(self, song_id, artist="", title=""):
        """Устанавливает песню для просмотра"""
        self.song_id = song_id
        self.song_artist = artist
        self.song_title = title
        self.load_song_data()

    def load_song_data(self):
        self.show_loading()
        api.get_tab(
            song_id=self.song_id,
            on_success=self.on_song_loaded,
            on_failure=self.on_load_failed,
            force_refresh=False
        )

    def show_loading(self):
        if self.is_loading:
            return
        self.is_loading = True
        from screens.components.loading_spinner import LoadingSpinner
        self.loading_spinner = LoadingSpinner(text="Загрузка...")
        self.add_widget(self.loading_spinner)
        self.loading_spinner.start_animation()

    def hide_loading(self):
        self.is_loading = False
        if self.loading_spinner:
            self.loading_spinner.stop_animation()
            self.remove_widget(self.loading_spinner)
            self.loading_spinner = None

    def on_song_loaded(self, data):
        artist = data.get('artist') or self.song_artist or 'Неизвестный'
        title = data.get('title') or self.song_title or 'Без названия'
        self.song_artist = artist
        self.song_title = title
        self.tabs = data.get('tabs', [])
        if not self.tabs and data.get('content'):
            self.tabs = [{'content': data.get('content', '')}]
        self.current_tab_index = 0

        if self.tabs:
            raw_content = self.tabs[0].get('content', 'Текст не загружен')
            cleaned = clean_text(raw_content)
            highlighted_text = highlight_chords_in_text(cleaned)
            self.content_label.text = highlighted_text
            self.content_label.markup = True
            self._update_content_height()

        self.is_liked = data.get('is_liked', False)
        self.is_favorite = data.get('is_favorite', False)

        self.like_btn.icon = "heart" if self.is_liked else "heart-outline"
        self.fav_btn.icon = "star" if self.is_favorite else "star-outline"

        self.update_top_nav_title()
        self.hide_loading()

        for delay in [0.3, 0.5, 0.8, 1.0]:
            Clock.schedule_once(self._wait_for_ready_and_scroll, delay)

    def _wait_for_ready_and_scroll(self, dt):
        if hasattr(self, 'content_label') and self.content_label.text:
            if self.content_label.texture and self.content_label.texture_size[1] > 0:
                self.content_scroll.scroll_y = 1.0
                return
        Clock.schedule_once(self._wait_for_ready_and_scroll, 0.15)

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
                self.fav_btn.icon = "star-outline"
                api._clear_favorites_cache()
                notify.success("Удалено из избранного")

            def on_failure(req, error):
                notify.error("Ошибка")

            api.remove_from_favorites(song_id=self.song_id, on_success=on_success, on_failure=on_failure)
        else:
            def on_success(result):
                self.is_favorite = True
                self.fav_btn.icon = "star"
                api._clear_favorites_cache()
                notify.success("Добавлено в избранное")

            def on_failure(req, error):
                notify.error("Ошибка")

            api.add_to_favorites(song_id=self.song_id, on_success=on_success, on_failure=on_failure)

    def update_top_nav_title(self):
        app = MDApp.get_running_app()
        if not app or not hasattr(app, 'top_nav'):
            return

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

    def go_back(self, instance=None):
        """Возврат ТОЛЬКО в SearchScreen с сохранением результатов поиска"""
        logger.info(f"🔙 Возврат из общего поиска в SearchScreen")

        # Убираем кастомный заголовок
        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            app.top_nav.clear_custom_title_widget()
            if hasattr(app.top_nav, '_update_right_buttons'):
                app.top_nav._update_right_buttons('search')

        # ✅ ВОССТАНАВЛИВАЕМ ПОИСК
        if self.manager and self.manager.has_screen('search'):
            search_screen = self.manager.get_screen('search')
            Clock.schedule_once(lambda dt: search_screen.refresh_search(), 0.2)
            self.manager.current = 'search'
            logger.info("✅ Возврат на SearchScreen")
        else:
            self.manager.current = 'home'
            logger.info("⚠️ SearchScreen не найден, возврат на home")

    def on_enter(self):
        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            # Настраиваем левую кнопку - стрелка назад
            if hasattr(app.top_nav, 'left_container'):
                app.top_nav.left_container.clear_widgets()
                app.top_nav.left_container.add_widget(app.top_nav.back_btn)
                app.top_nav.back_btn.on_release = self.go_back

            # Настраиваем правую кнопку - лайк и избранное
            if hasattr(app.top_nav, 'right_container'):
                app.top_nav.right_container.clear_widgets()
                if hasattr(self, 'like_btn') and hasattr(self, 'fav_btn'):
                    app.top_nav.right_container.add_widget(self.like_btn)
                    app.top_nav.right_container.add_widget(self.fav_btn)

        # Обновляем заголовок
        if self.song_title:
            self.update_top_nav_title()

    def on_leave(self):
        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            app.top_nav.clear_custom_title_widget()
            # Восстанавливаем правую кнопку
            if hasattr(app.top_nav, '_update_right_buttons'):
                app.top_nav._update_right_buttons('search')