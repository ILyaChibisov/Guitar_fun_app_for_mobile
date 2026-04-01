# screens/song_detail_screen.py
"""
Экран просмотра песни с текстом и подборами
"""
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivymd.uix.scrollview import MDScrollView
from kivy.metrics import dp
from kivy.animation import Animation
from config.theme import theme
from config.logger_config import screen_logger
from api.client import api
from utils.notifications import notify
from utils.kivy_imports import MDIconButton, MDBoxLayout, MDProgressBar

logger = screen_logger('SongDetail')


class LoadingSpinner(MDBoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint = (1, 1)
        self.spacing = dp(16)

        self.progress = MDProgressBar(
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
            font_style="Body1",
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


class SongDetailScreen(MDScreen):
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

        from kivy.graphics import Color, Rectangle
        from kivy.utils import rgba
        with self.canvas.before:
            Color(*rgba(theme.BACKGROUND))
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

        # Верхняя панель
        self.top_bar = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(56),
            padding=[dp(8), dp(8), dp(8), dp(8)],
            spacing=dp(8)
        )

        self.back_btn = MDIconButton(
            icon="arrow-left",
            theme_text_color="Custom",
            text_color=theme.TEXT_PRIMARY,
            on_release=self.go_back
        )

        self.menu_btn = MDIconButton(
            icon="dots-vertical",
            theme_text_color="Custom",
            text_color=theme.TEXT_PRIMARY,
            on_release=self.open_menu
        )

        self.top_bar.add_widget(self.back_btn)
        spacer = MDBoxLayout()
        self.top_bar.add_widget(spacer)
        self.top_bar.add_widget(self.menu_btn)

        # Название песни
        self.title_label = MDLabel(
            text="",
            font_style="H5",
            halign="center",
            size_hint_y=None,
            height=dp(60),
            theme_text_color="Primary",
            bold=True
        )

        # Текст песни
        self.content_scroll = MDScrollView(size_hint=(1, 1))
        self.content_label = MDLabel(
            text="",
            font_style="Body1",
            size_hint_y=None,
            theme_text_color="Primary",
            markup=True
        )
        self.content_label.bind(texture_size=self.content_label.setter('size'))
        self.content_scroll.add_widget(self.content_label)

        # Нижняя панель
        self.bottom_bar = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(70),
            padding=[dp(16), dp(8), dp(16), dp(8)],
            spacing=dp(24),
            md_bg_color=theme.SURFACE
        )

        self.like_btn = MDIconButton(
            icon="heart-outline",
            theme_text_color="Custom",
            text_color=theme.TEXT_SECONDARY,
            on_release=self.toggle_like
        )
        self.like_count = MDLabel(
            text="0",
            font_style="Caption",
            size_hint_x=0.1,
            theme_text_color="Secondary"
        )

        self.favorite_btn = MDIconButton(
            icon="star-outline",
            theme_text_color="Custom",
            text_color=theme.TEXT_SECONDARY,
            on_release=self.toggle_favorite
        )
        self.favorite_count = MDLabel(
            text="0",
            font_style="Caption",
            size_hint_x=0.1,
            theme_text_color="Secondary"
        )

        self.share_btn = MDIconButton(
            icon="share-variant",
            theme_text_color="Custom",
            text_color=theme.TEXT_SECONDARY,
            on_release=self.share_song
        )

        self.views_label = MDLabel(
            text="👁️ 0",
            font_style="Caption",
            size_hint_x=0.2,
            theme_text_color="Secondary",
            halign="right"
        )

        like_box = MDBoxLayout(orientation='vertical', size_hint_x=0.15, spacing=dp(2))
        like_box.add_widget(self.like_btn)
        like_box.add_widget(self.like_count)

        fav_box = MDBoxLayout(orientation='vertical', size_hint_x=0.15, spacing=dp(2))
        fav_box.add_widget(self.favorite_btn)
        fav_box.add_widget(self.favorite_count)

        self.bottom_bar.add_widget(like_box)
        self.bottom_bar.add_widget(fav_box)
        self.bottom_bar.add_widget(self.share_btn)
        self.bottom_bar.add_widget(self.views_label)

        self.main_layout = MDBoxLayout(orientation='vertical')
        self.main_layout.add_widget(self.top_bar)
        self.main_layout.add_widget(self.title_label)
        self.main_layout.add_widget(self.content_scroll)
        self.main_layout.add_widget(self.bottom_bar)

        self.add_widget(self.main_layout)

        logger.info('Экран просмотра песни создан')

    def _update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def show_loading(self):
        if self.is_loading:
            return
        self.is_loading = True
        self.loading_spinner = LoadingSpinner()
        self.add_widget(self.loading_spinner)
        self.loading_spinner.start_animation()
        self.main_layout.opacity = 0.3
        self.main_layout.disabled = True

    def hide_loading(self):
        self.is_loading = False
        if self.loading_spinner:
            self.loading_spinner.stop_animation()
            self.remove_widget(self.loading_spinner)
            self.loading_spinner = None
        self.main_layout.opacity = 1
        self.main_layout.disabled = False

    def set_song(self, song_id):
        """Устанавливает ID песни и загружает данные"""
        logger.info(f"set_song called with id: {song_id}")
        self.song_id = song_id
        self.load_song_data()

    def load_song_data(self):
        """Загружает данные о песне с сервера"""
        self.show_loading()
        api.get_tab(
            song_id=self.song_id,
            on_success=self.on_song_loaded,
            on_failure=self.on_load_failed
        )

    def on_song_loaded(self, data):
        """Отображает загруженные данные"""
        logger.info(f"on_song_loaded called")

        self.artist = data.get('artist')
        self.title = data.get('title')
        self.current_tab_id = data.get('id')

        self.tabs = [{
            "id": data.get('id'),
            "tab_number": data.get('tab_number', 1),
            "tab_name": data.get('tab_name'),
            "content": data.get('content', ''),
            "views": data.get('views', 0),
            "likes": data.get('likes', 0)
        }]
        self.in_favorites_count = data.get('in_favorites_count', 0)
        self.is_liked = data.get('is_liked', False)
        self.is_favorite = data.get('is_favorite', False)

        self.title_label.text = f"🎸 {self.artist} — {self.title}"

        # Обновляем текст песни
        content = data.get('content', 'Текст не загружен')
        self.content_label.text = content
        self.content_label.texture_update()
        self.content_label.height = self.content_label.texture_size[1]

        # Обновляем статистику
        self.like_count.text = str(data.get('likes', 0))
        self.views_label.text = f"👁️ {data.get('views', 0)}"
        self.favorite_count.text = str(self.in_favorites_count)

        self.update_buttons_state()
        self.hide_loading()

        logger.info(f"Песня загружена: {self.artist} - {self.title}")

    def on_load_failed(self, req, error):
        """Обработчик ошибки загрузки"""
        self.hide_loading()
        notify.error(f"Ошибка загрузки песни: {error}")
        logger.error(f"Ошибка загрузки песни {self.song_id}: {error}")
        self.go_back(None)

    def update_buttons_state(self):
        """Обновляет состояние кнопок лайка и избранного"""
        if api.is_authenticated():
            self.like_btn.icon = "heart" if self.is_liked else "heart-outline"
            self.like_btn.text_color = theme.ERROR if self.is_liked else theme.TEXT_SECONDARY
            self.favorite_btn.icon = "star" if self.is_favorite else "star-outline"
            self.favorite_btn.text_color = theme.WARNING if self.is_favorite else theme.TEXT_SECONDARY
        else:
            self.like_btn.disabled = True
            self.favorite_btn.disabled = True

    def toggle_like(self, instance):
        if not api.is_authenticated():
            notify.warning("Войдите, чтобы ставить лайки")
            return
        notify.info("❤️ +1 (заглушка)")

    def toggle_favorite(self, instance):
        if not api.is_authenticated():
            notify.warning("Войдите, чтобы добавлять в избранное")
            return
        notify.info("⭐ Добавлено в избранное (заглушка)")

    def share_song(self, instance):
        notify.info("🔄 Функция будет доступна в следующей версии")

    def open_menu(self, instance):
        notify.info("📋 Меню будет доступно в следующей версии")

    def go_back(self, instance):
        if hasattr(self, 'manager') and self.manager:
            self.manager.current = 'artist_songs'