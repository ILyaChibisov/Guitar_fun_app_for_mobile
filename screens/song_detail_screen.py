# screens/song_detail_screen.py
"""
Экран просмотра песни с текстом и подборами - переведён на BaseScreen
"""
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
from io import BytesIO
import re
from kivy.clock import Clock

from config.theme import theme
from config.logger_config import screen_logger
from config.layout_config import layout_config
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


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return [int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4)]


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


class SongDetailScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'song_detail'
        self.song_id = None
        self.current_tab_id = None
        self.tabs = []
        self.is_liked = False
        self.is_favorite = False
        self.is_loading = False
        self.loading_spinner = None
        self.bg_image = None
        self.previous_screen = 'artist_songs'
        self.current_tonality = 0

        self.init_ui()
        self.load_background()

        logger.info('Экран просмотра песни создан (BaseScreen)')

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

    def _load_icon(self, icon_name, image_widget):
        if HAS_ASSETS:
            try:
                icon_data = load_asset_as_bytes(icon_name)
                if icon_data:
                    img = CoreImage(BytesIO(icon_data), ext="png")
                    image_widget.texture = img.texture
                    return True
            except Exception as e:
                logger.error(f"Ошибка загрузки иконки {icon_name}: {e}")
        return False

    def init_ui(self):
        # Верхняя панель
        top_bar = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(50),
            padding=[dp(16), dp(8), dp(16), dp(8)],
            spacing=dp(12),
            md_bg_color=[0, 0, 0, 0]
        )

        self.back_btn = MDIconButton(
            icon="arrow-left",
            size_hint=(None, None),
            size=(dp(36), dp(36)),
            theme_icon_color="Custom",
            icon_color=[1, 1, 1, 1],
            md_bg_color=[0, 0, 0, 0],
            on_release=self.go_back
        )

        self.song_icon = Image(
            size_hint=(None, None),
            size=(dp(28), dp(28)),
            pos_hint={'center_y': 0.5},
            allow_stretch=True,
            keep_ratio=True
        )
        self._load_icon('song_png', self.song_icon)

        self.title_label = MDLabel(
            text="",
            font_size=sp(14),
            halign="left",
            valign="middle",
            size_hint_x=1,
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.9],
            bold=True,
            shorten=True,
            shorten_from="right"
        )

        top_bar.add_widget(self.back_btn)
        top_bar.add_widget(self.song_icon)
        top_bar.add_widget(self.title_label)

        # Карточка с текстом песни
        card_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            padding=[dp(16), dp(8), dp(16), dp(0)]
        )

        self.song_card = MDCard(
            orientation='vertical',
            size_hint=(1, 1),
            padding=[dp(12), dp(10), dp(12), dp(10)],
            spacing=dp(8),
            radius=[theme.CORNER_RADIUS_SMALL],
            md_bg_color=[1, 1, 1, 0.95],
            elevation=4,
            line_color=[0.8, 0.8, 0.8, 0.5],
            line_width=1
        )

        # Верхняя строка с кнопками
        tools_row = self._build_tools_row()
        self.song_card.add_widget(tools_row)

        # Текст песни
        self.content_scroll = MDScrollView(
            size_hint=(1, 1),
            do_scroll_x=False,
            bar_color=[0.5, 0.5, 0.5, 0],
            bar_width=0
        )

        scroll_content = MDBoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=dp(8),
            adaptive_height=True
        )

        self.content_label = MDLabel(
            text="",
            font_size=sp(14),
            size_hint_y=None,
            theme_text_color="Custom",
            text_color=[0, 0, 0, 0.85],
            markup=True,
            valign="top",
            line_height=1.4
        )
        self.content_label.bind(texture_size=self._update_content_height)
        scroll_content.add_widget(self.content_label)
        self.content_scroll.add_widget(scroll_content)
        self.song_card.add_widget(self.content_scroll)

        # Нижняя строка со счётчиками
        bottom_stats = self._build_bottom_stats()
        self.song_card.add_widget(bottom_stats)

        card_container.add_widget(self.song_card)

        # Строим UI
        self.build_ui(content_widget=card_container, top_widget=top_bar)

    def _build_tools_row(self):
        tools_row = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(38),
            spacing=dp(4),
            padding=[dp(4), dp(4), dp(4), dp(4)]
        )

        self.favorite_btn = MDIconButton(
            icon="star-outline",
            size_hint=(None, None),
            size=(dp(30), dp(30)),
            theme_icon_color="Custom",
            icon_color=[0.9, 0.7, 0.2, 0.8],
            on_release=self.toggle_favorite
        )

        self.like_btn = MDIconButton(
            icon="heart-outline",
            size_hint=(None, None),
            size=(dp(30), dp(30)),
            theme_icon_color="Custom",
            icon_color=[0.8, 0.3, 0.3, 0.8],
            on_release=self.toggle_like
        )

        spacer1 = Widget(size_hint_x=None, width=dp(30))

        tonality_label = MDLabel(
            text="Тональность",
            font_size=sp(12),
            size_hint_x=None,
            width=dp(105),
            theme_text_color="Custom",
            text_color=[0.3, 0.3, 0.3, 0.9],
            valign="middle"
        )

        spacer2 = Widget(size_hint_x=None, width=dp(10))

        self.minus_ton_btn = MDIconButton(
            icon="minus",
            size_hint=(None, None),
            size=(dp(26), dp(26)),
            theme_icon_color="Custom",
            icon_color=[0.5, 0.5, 0.5, 0.8],
            md_bg_color=[0.9, 0.9, 0.9, 0.5],
            on_release=self.decrease_tonality
        )

        self.tonality_value = MDLabel(
            text="0",
            font_size=sp(13),
            size_hint_x=None,
            width=dp(25),
            theme_text_color="Custom",
            text_color=hex_to_rgb(theme.PRIMARY) + [1],
            bold=True,
            valign="middle",
            halign="center"
        )

        self.plus_ton_btn = MDIconButton(
            icon="plus",
            size_hint=(None, None),
            size=(dp(26), dp(26)),
            theme_icon_color="Custom",
            icon_color=[0.5, 0.5, 0.5, 0.8],
            md_bg_color=[0.9, 0.9, 0.9, 0.5],
            on_release=self.increase_tonality
        )

        tools_row.add_widget(self.favorite_btn)
        tools_row.add_widget(self.like_btn)
        tools_row.add_widget(spacer1)
        tools_row.add_widget(tonality_label)
        tools_row.add_widget(spacer2)
        tools_row.add_widget(self.minus_ton_btn)
        tools_row.add_widget(self.tonality_value)
        tools_row.add_widget(self.plus_ton_btn)

        return tools_row

    def _build_bottom_stats(self):
        bottom_stats = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(32),
            spacing=dp(20),
            padding=[dp(8), dp(4), dp(8), dp(4)]
        )

        like_icon = MDIconButton(
            icon="heart",
            size_hint=(None, None),
            size=(dp(20), dp(20)),
            theme_icon_color="Custom",
            icon_color=[0.8, 0.3, 0.3, 0.7],
            disabled=True
        )
        self.like_count = MDLabel(
            text="0",
            font_size=sp(12),
            size_hint_x=None,
            width=dp(35),
            theme_text_color="Custom",
            text_color=[0.8, 0.3, 0.3, 0.8],
            bold=True,
            valign="middle"
        )
        like_box = MDBoxLayout(orientation='horizontal', spacing=dp(4), size_hint_x=None, width=dp(60))
        like_box.add_widget(like_icon)
        like_box.add_widget(self.like_count)

        fav_icon = MDIconButton(
            icon="star",
            size_hint=(None, None),
            size=(dp(20), dp(20)),
            theme_icon_color="Custom",
            icon_color=[0.9, 0.7, 0.2, 0.7],
            disabled=True
        )
        self.favorite_count = MDLabel(
            text="0",
            font_size=sp(12),
            size_hint_x=None,
            width=dp(35),
            theme_text_color="Custom",
            text_color=[0.9, 0.7, 0.2, 0.8],
            bold=True,
            valign="middle"
        )
        fav_box = MDBoxLayout(orientation='horizontal', spacing=dp(4), size_hint_x=None, width=dp(60))
        fav_box.add_widget(fav_icon)
        fav_box.add_widget(self.favorite_count)

        views_icon = MDIconButton(
            icon="eye-outline",
            size_hint=(None, None),
            size=(dp(20), dp(20)),
            theme_icon_color="Custom",
            icon_color=[0.5, 0.5, 0.5, 0.6],
            disabled=True
        )
        self.views_count = MDLabel(
            text="0",
            font_size=sp(12),
            size_hint_x=None,
            width=dp(40),
            theme_text_color="Custom",
            text_color=[0.5, 0.5, 0.5, 0.7],
            valign="middle"
        )
        views_box = MDBoxLayout(orientation='horizontal', spacing=dp(4), size_hint_x=None, width=dp(65))
        views_box.add_widget(views_icon)
        views_box.add_widget(self.views_count)

        left_spacer = Widget(size_hint_x=1)
        right_spacer = Widget(size_hint_x=1)

        bottom_stats.add_widget(left_spacer)
        bottom_stats.add_widget(like_box)
        bottom_stats.add_widget(fav_box)
        bottom_stats.add_widget(views_box)
        bottom_stats.add_widget(right_spacer)

        return bottom_stats

    def _update_content_height(self, *args):
        self.content_label.height = self.content_label.texture_size[1] + dp(20)

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
        self.artist = data.get('artist') or data.get('artist_name') or 'Неизвестный исполнитель'
        self.title = data.get('title') or data.get('song_title') or 'Без названия'
        self.current_tab_id = data.get('id')

        self.title_label.text = f"{self.artist} — {self.title}"

        raw_content = data.get('content', 'Текст не загружен')
        cleaned_content = self.clean_text(raw_content)
        self.content_label.text = cleaned_content
        self._update_content_height()

        self.like_count.text = str(data.get('likes', 0))
        self.favorite_count.text = str(data.get('favorites_count', 0))
        self.views_count.text = str(data.get('views', 0))

        self.is_liked = data.get('is_liked', False)
        self.is_favorite = data.get('is_favorite', False)
        self.update_buttons_state()

        Clock.schedule_once(lambda dt: setattr(self.content_scroll, 'scroll_y', 1), 0.1)
        self.hide_loading()
        logger.info(f"Песня загружена: {self.artist} - {self.title}")

    def on_load_failed(self, req, error):
        self.hide_loading()
        notify.error(f"Ошибка загрузки песни: {error}")
        self.go_back(None)

    def clean_text(self, text):
        if not text:
            return "Текст не загружен"
        lines = text.split('\n')
        cleaned_lines = []
        for i, line in enumerate(lines):
            if 'источник:' in line.lower() or 'source:' in line.lower():
                continue
            if i < 4:
                continue
            cleaned_lines.append(line)
        while cleaned_lines and not cleaned_lines[-1].strip():
            cleaned_lines.pop()
        result = '\n'.join(cleaned_lines)
        return result.strip() if result.strip() else '\n'.join(lines[4:])

    def update_buttons_state(self):
        if api.is_authenticated():
            if self.is_liked:
                self.like_btn.icon = "heart"
            else:
                self.like_btn.icon = "heart-outline"

            if self.is_favorite:
                self.favorite_btn.icon = "star"
            else:
                self.favorite_btn.icon = "star-outline"

    def toggle_like(self, instance):
        if not api.is_authenticated():
            notify.warning("Войдите, чтобы ставить лайки")
            return

        def on_success(result):
            self.is_liked = result.get('liked', not self.is_liked)
            self.like_count.text = str(result.get('total_likes', int(self.like_count.text)))
            self.update_buttons_state()
            notify.success("Лайк поставлен!" if self.is_liked else "Лайк убран")

        def on_failure(req, error):
            notify.error("Ошибка при изменении лайка")

        api.toggle_like(song_id=self.song_id, on_success=on_success, on_failure=on_failure)

    def toggle_favorite(self, instance):
        if not api.is_authenticated():
            notify.warning("Войдите, чтобы добавлять в избранное")
            return

        if self.is_favorite:
            def on_success(result):
                self.is_favorite = False
                self.favorite_btn.icon = "star-outline"
                self.favorite_count.text = str(max(0, int(self.favorite_count.text) - 1))
                notify.success("Удалено из избранного")
                self._refresh_favorites_screen()

            def on_failure(req, error):
                notify.error("Ошибка при удалении из избранного")

            api.remove_from_favorites(song_id=self.song_id, on_success=on_success, on_failure=on_failure)
        else:
            def on_success(result):
                self.is_favorite = True
                self.favorite_btn.icon = "star"
                self.favorite_count.text = str(int(self.favorite_count.text) + 1)
                notify.success("Добавлено в избранное")
                self._refresh_favorites_screen()

            def on_failure(req, error):
                notify.error("Ошибка при добавлении в избранное")

            api.add_to_favorites(song_id=self.song_id, on_success=on_success, on_failure=on_failure)

    def _refresh_favorites_screen(self):
        if hasattr(self, 'manager') and self.manager:
            if self.manager.has_screen('favorites'):
                favorites_screen = self.manager.get_screen('favorites')
                if hasattr(favorites_screen, 'load_favorites'):
                    Clock.schedule_once(lambda dt: favorites_screen.load_favorites(), 0.5)

    def increase_tonality(self, instance):
        self.current_tonality += 1
        self.tonality_value.text = str(self.current_tonality)

    def decrease_tonality(self, instance):
        self.current_tonality -= 1
        self.tonality_value.text = str(self.current_tonality)

    def go_back(self, instance):
        if hasattr(self, 'manager') and self.manager:
            self.manager.current = self.previous_screen