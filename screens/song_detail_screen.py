# screens/song_detail_screen.py
"""
Экран просмотра песни с текстом и подборами
"""
from kivymd.uix.screen import MDScreen
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
from kivy.uix.floatlayout import FloatLayout
from io import BytesIO
import re

from config.theme import theme
from config.logger_config import screen_logger
from api.client import api
from utils.notifications import notify

logger = screen_logger('SongDetail')

# Попытка импорта ассетов
try:
    from data import load_asset_as_bytes

    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False


    def load_asset_as_bytes(name):
        return None


    logger.warning("Модуль data не найден")


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
        self.bg_image = None

        self.md_bg_color = [0, 0, 0, 0]

        self.init_ui()
        self.load_background()

        logger.info('Экран просмотра песни создан')

    def load_background(self):
        """Загружает фоновое изображение"""
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
        """Загружает иконку из ассетов"""
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
        root_layout = FloatLayout()

        # Основной контейнер
        main_layout = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            spacing=0
        )

        # Отступ сверху для компенсации верхней панели
        top_spacer = Widget(size_hint_y=None, height=dp(65))
        main_layout.add_widget(top_spacer)

        # ============ ВЕРХНЯЯ ПАНЕЛЬ НАВИГАЦИИ ============
        self.nav_row = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(50),
            padding=[dp(16), dp(8), dp(16), dp(8)],
            spacing=dp(12),
            md_bg_color=[0, 0, 0, 0]
        )

        # Кнопка назад (стрелка)
        self.back_btn = MDIconButton(
            icon="arrow-left",
            size_hint=(None, None),
            size=(dp(36), dp(36)),
            theme_icon_color="Custom",
            icon_color=[1, 1, 1, 1],
            md_bg_color=[0, 0, 0, 0],
            on_release=self.go_back
        )

        # Иконка песни из ассетов
        self.song_icon = Image(
            size_hint=(None, None),
            size=(dp(28), dp(28)),
            pos_hint={'center_y': 0.5},
            allow_stretch=True,
            keep_ratio=True
        )
        self._load_icon('song_png', self.song_icon)
        if not self.song_icon.texture:
            self.song_icon.text = "🎵"

        # Название песни и исполнителя
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

        self.nav_row.add_widget(self.back_btn)
        self.nav_row.add_widget(self.song_icon)
        self.nav_row.add_widget(self.title_label)

        # ============ КАРТОЧКА С ТЕКСТОМ ПЕСНИ ============
        # Нижний отступ 85dp - чтобы карточка не заходила под нижнюю навигацию
        card_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            padding=[dp(16), dp(8), dp(16), dp(85)]
        )

        self.song_card = MDCard(
            orientation='vertical',
            size_hint=(1, 1),
            padding=[dp(20), dp(16), dp(20), dp(16)],
            spacing=dp(12),
            radius=[theme.CORNER_RADIUS_SMALL],
            md_bg_color=[1, 1, 1, 0.95],
            elevation=4,
            line_color=[0.8, 0.8, 0.8, 0.5],
            line_width=1
        )

        # ============ ТЕКСТ ПЕСНИ (СКРОЛЛ) ============
        # bar_width=0 - убираем видимость полосы прокрутки (на мобильных не видна, на ПК тоже)
        self.content_scroll = MDScrollView(
            size_hint=(1, 1),
            do_scroll_x=False,
            bar_color=[0.5, 0.5, 0.5, 0],
            bar_width=0,
            bar_inactive_color=[0.5, 0.5, 0.5, 0]
        )

        # Контейнер для текста и нижней панели
        scroll_content = MDBoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=dp(12),
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

        # ============ НИЖНЯЯ ЧАСТЬ КАРТОЧКИ (ЛАЙКИ И СТАТИСТИКА) ============
        # Уменьшенная секция - высота 36dp
        self.bottom_stats = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(36),
            spacing=dp(16),
            padding=[dp(4), dp(0), dp(4), dp(0)]
        )

        # Кнопка лайка
        self.like_btn = MDIconButton(
            icon="heart-outline",
            size_hint=(None, None),
            size=(dp(28), dp(28)),
            theme_icon_color="Custom",
            icon_color=[0.8, 0.3, 0.3, 0.8],
            on_release=self.toggle_like
        )

        self.like_count = MDLabel(
            text="0",
            font_size=sp(12),
            size_hint_x=None,
            width=dp(30),
            theme_text_color="Custom",
            text_color=[0.8, 0.3, 0.3, 0.9],
            bold=True,
            valign="middle"
        )

        # Кнопка избранного
        self.favorite_btn = MDIconButton(
            icon="star-outline",
            size_hint=(None, None),
            size=(dp(28), dp(28)),
            theme_icon_color="Custom",
            icon_color=[0.9, 0.7, 0.2, 0.8],
            on_release=self.toggle_favorite
        )

        self.favorite_count = MDLabel(
            text="0",
            font_size=sp(12),
            size_hint_x=None,
            width=dp(30),
            theme_text_color="Custom",
            text_color=[0.9, 0.7, 0.2, 0.9],
            bold=True,
            valign="middle"
        )

        # Просмотры
        self.views_icon = MDIconButton(
            icon="eye-outline",
            size_hint=(None, None),
            size=(dp(22), dp(22)),
            theme_icon_color="Custom",
            icon_color=[0.5, 0.5, 0.5, 0.7],
            disabled=True
        )

        self.views_count = MDLabel(
            text="0",
            font_size=sp(11),
            size_hint_x=None,
            width=dp(30),
            theme_text_color="Custom",
            text_color=[0.5, 0.5, 0.5, 0.7],
            valign="middle"
        )

        views_box = MDBoxLayout(
            orientation='horizontal',
            spacing=dp(4),
            size_hint_x=None,
            width=dp(55)
        )
        views_box.add_widget(self.views_icon)
        views_box.add_widget(self.views_count)

        self.bottom_stats.add_widget(self.like_btn)
        self.bottom_stats.add_widget(self.like_count)
        self.bottom_stats.add_widget(self.favorite_btn)
        self.bottom_stats.add_widget(self.favorite_count)
        self.bottom_stats.add_widget(views_box)

        # Разделитель перед нижней статистикой (тоньше)
        self.divider = Widget(size_hint_y=None, height=dp(1))
        with self.divider.canvas:
            Color(0.7, 0.7, 0.7, 0.5)
            self.divider_rect = Rectangle(pos=self.divider.pos, size=self.divider.size)
        self.divider.bind(pos=self._update_divider, size=self._update_divider)

        scroll_content.add_widget(self.content_label)
        scroll_content.add_widget(self.divider)
        scroll_content.add_widget(self.bottom_stats)

        self.content_scroll.add_widget(scroll_content)

        self.song_card.add_widget(self.content_scroll)
        card_container.add_widget(self.song_card)

        main_layout.add_widget(self.nav_row)
        main_layout.add_widget(card_container)

        root_layout.add_widget(main_layout)

        self.add_widget(root_layout)

    def _update_divider(self, *args):
        if hasattr(self, 'divider_rect'):
            self.divider_rect.pos = self.divider.pos
            self.divider_rect.size = self.divider.size

    def _update_content_height(self, *args):
        """Обновляет высоту контента при изменении текста"""
        self.content_label.height = self.content_label.texture_size[1] + dp(20)

    def clean_text(self, text: str) -> str:
        """Очищает текст от мета-информации (источник и первые строки)"""
        if not text:
            return "Текст не загружен"

        lines = text.split('\n')

        cleaned_lines = []

        for i, line in enumerate(lines):
            line_lower = line.lower()
            if 'источник:' in line_lower or 'source:' in line_lower:
                continue
            if i < 4:
                continue
            cleaned_lines.append(line)

        while cleaned_lines and not cleaned_lines[-1].strip():
            cleaned_lines.pop()

        result = '\n'.join(cleaned_lines)

        if not result.strip():
            result = '\n'.join(lines[4:])

        return result.strip()

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

        self.title_label.text = f"{self.artist} — {self.title}"
        self.title_label.texture_update()

        raw_content = data.get('content', 'Текст не загружен')
        cleaned_content = self.clean_text(raw_content)
        self.content_label.text = cleaned_content
        self.content_label.texture_update()
        self._update_content_height()

        self.like_count.text = str(data.get('likes', 0))
        self.views_count.text = str(data.get('views', 0))

        self.is_liked = data.get('is_liked', False)
        self.is_favorite = data.get('is_favorite', False)
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
            if self.is_liked:
                self.like_btn.icon = "heart"
                self.like_btn.icon_color = [0.8, 0.3, 0.3, 1]
            else:
                self.like_btn.icon = "heart-outline"
                self.like_btn.icon_color = [0.8, 0.3, 0.3, 0.6]

            if self.is_favorite:
                self.favorite_btn.icon = "star"
                self.favorite_btn.icon_color = [0.9, 0.7, 0.2, 1]
            else:
                self.favorite_btn.icon = "star-outline"
                self.favorite_btn.icon_color = [0.9, 0.7, 0.2, 0.6]
        else:
            self.like_btn.disabled = True
            self.favorite_btn.disabled = True

    def toggle_like(self, instance):
        if not api.is_authenticated():
            notify.warning("Войдите, чтобы ставить лайки")
            return

        if self.is_liked:
            self.is_liked = False
            current = int(self.like_count.text)
            self.like_count.text = str(current - 1)
            self.like_btn.icon = "heart-outline"
            self.like_btn.icon_color = [0.8, 0.3, 0.3, 0.6]
        else:
            self.is_liked = True
            current = int(self.like_count.text)
            self.like_count.text = str(current + 1)
            self.like_btn.icon = "heart"
            self.like_btn.icon_color = [0.8, 0.3, 0.3, 1]

    def toggle_favorite(self, instance):
        if not api.is_authenticated():
            notify.warning("Войдите, чтобы добавлять в избранное")
            return

        if self.is_favorite:
            self.is_favorite = False
            current = int(self.favorite_count.text)
            self.favorite_count.text = str(current - 1)
            self.favorite_btn.icon = "star-outline"
            self.favorite_btn.icon_color = [0.9, 0.7, 0.2, 0.6]
        else:
            self.is_favorite = True
            current = int(self.favorite_count.text)
            self.favorite_count.text = str(current + 1)
            self.favorite_btn.icon = "star"
            self.favorite_btn.icon_color = [0.9, 0.7, 0.2, 1]

    def go_back(self, instance):
        if hasattr(self, 'manager') and self.manager:
            self.manager.current = 'artist_songs'