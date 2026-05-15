# screens/song_detail_screen.py
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


class IconButton(ButtonBehavior, Image):
    """Кнопка с иконкой из ассета (для тональности)"""

    def __init__(self, asset_name, size=(30, 30), on_release=None, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = size
        self.allow_stretch = True
        self.keep_ratio = True
        self.on_release_callback = on_release
        self._load_icon(asset_name)

    def _load_icon(self, asset_name):
        if HAS_ASSETS:
            try:
                icon_data = load_asset_as_bytes(asset_name)
                if icon_data:
                    img = CoreImage(BytesIO(icon_data), ext="png")
                    self.texture = img.texture
                    return
            except Exception as e:
                logger.error(f"Ошибка загрузки иконки {asset_name}: {e}")
        # Заглушка
        self.text = "●"

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if self.on_release_callback:
                self.on_release_callback(self)
            return True
        return super().on_touch_down(touch)


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return [int(hex_color[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]


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
        # Создаём основной контейнер с отступами для панелей
        main_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            padding=[0, 0, 0, 0]
        )

        # Верхний отступ под статус-бар и TopNav
        top_padding = layout_config.get_top_padding()
        main_container.add_widget(Widget(size_hint_y=None, height=top_padding))

        # Карточка с текстом (белый фон) - растягивается на оставшееся пространство
        self.song_card = MDCard(
            orientation='vertical',
            size_hint=(1, 1),
            padding=[0, 8, 0, 8],
            spacing=8,
            radius=[0, 0, 0, 0],
            md_bg_color=[1, 1, 1, 1],
            elevation=0,
            line_color=[0, 0, 0, 0],
            line_width=0.01
        )

        # Верхняя строка с кнопками
        self._create_tools_row()
        self.song_card.add_widget(self.tools_row)

        # Контейнер для текста песни с прокруткой
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
            spacing=8,
            padding=[16, 8, 16, 16],
            adaptive_height=True
        )

        # Заголовок с иконкой song_png и названием
        self.song_header = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=60,
            spacing=12,
            padding=[0, 8, 0, 8]
        )

        # Иконка песни из ассета
        self.song_icon = Image(
            size_hint=(None, None),
            size=(32, 32),
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
            except Exception as e:
                logger.error(f"Ошибка загрузки song_png: {e}")

        # Текст заголовка
        self.song_title_label = MDLabel(
            text="",
            font_size=16,
            size_hint_x=1,
            theme_text_color="Custom",
            text_color=[0, 0, 0, 0.9],
            bold=True,
            valign="middle"
        )

        self.song_header.add_widget(self.song_icon)
        self.song_header.add_widget(self.song_title_label)

        # Разделитель
        separator = MDBoxLayout(
            size_hint_y=None,
            height=1,
            md_bg_color=[0.8, 0.8, 0.8, 0.5]
        )

        # Основной текст песни (чёрным цветом)
        self.content_label = MDLabel(
            text="",
            font_size=14,
            size_hint_y=None,
            theme_text_color="Custom",
            text_color=[0, 0, 0, 0.85],
            markup=True,
            valign="top",
            line_height=1.5
        )
        self.content_label.bind(texture_size=self._update_content_height)

        scroll_content.add_widget(self.song_header)
        scroll_content.add_widget(separator)
        scroll_content.add_widget(self.content_label)

        self.content_scroll.add_widget(scroll_content)
        self.song_card.add_widget(self.content_scroll)

        # Нижняя строка со счётчиками
        self._create_bottom_stats()
        self.song_card.add_widget(self.bottom_stats)

        # Добавляем карточку в контейнер
        main_container.add_widget(self.song_card)

        # Нижний отступ для BottomNav
        bottom_nav_height = dp(60)
        nav_bar_height = get_navigation_bar_height()
        total_bottom = bottom_nav_height + nav_bar_height + dp(20)
        main_container.add_widget(Widget(size_hint_y=None, height=total_bottom))

        # Добавляем контейнер на экран
        self.add_widget(main_container)

    def _create_tools_row(self):
        """Создаёт строку с кнопками управления"""
        self.tools_row = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=52,
            spacing=8,
            padding=[12, 4, 12, 4]
        )

        # Кнопка избранного (звёздочка из Material Design)
        self.favorite_btn = MDIconButton(
            icon="star-outline",
            size_hint=(None, None),
            size=(36, 36),
            theme_icon_color="Custom",
            icon_color=[0.9, 0.7, 0.2, 0.8],
            on_release=self.toggle_favorite
        )

        # Кнопка лайка (сердечко из Material Design)
        self.like_btn = MDIconButton(
            icon="heart-outline",
            size_hint=(None, None),
            size=(36, 36),
            theme_icon_color="Custom",
            icon_color=[0.8, 0.3, 0.3, 0.8],
            on_release=self.toggle_like
        )

        spacer1 = Widget(size_hint_x=1)

        # Тональность
        tonality_label = MDLabel(
            text="Тональность",
            font_size=13,
            size_hint_x=None,
            width=100,
            theme_text_color="Custom",
            text_color=[0, 0, 0, 0.7],
            valign="middle"
        )

        spacer2 = Widget(size_hint_x=None, width=8)

        # Кнопка минус тон (из ассета)
        self.minus_ton_btn = IconButton(
            asset_name='minus_ton_png',
            size=(30, 30),
            on_release=self.decrease_tonality
        )

        # Значение тональности
        self.tonality_value = MDLabel(
            text="0",
            font_size=14,
            size_hint_x=None,
            width=30,
            theme_text_color="Custom",
            text_color=[0.46, 0.70, 0.71, 1],
            bold=True,
            valign="middle",
            halign="center"
        )

        # Кнопка плюс тон (из ассета)
        self.plus_ton_btn = IconButton(
            asset_name='plus_ton_png',
            size=(30, 30),
            on_release=self.increase_tonality
        )

        self.tools_row.add_widget(self.favorite_btn)
        self.tools_row.add_widget(self.like_btn)
        self.tools_row.add_widget(spacer1)
        self.tools_row.add_widget(tonality_label)
        self.tools_row.add_widget(spacer2)
        self.tools_row.add_widget(self.minus_ton_btn)
        self.tools_row.add_widget(self.tonality_value)
        self.tools_row.add_widget(self.plus_ton_btn)

    def _create_bottom_stats(self):
        """Создаёт нижнюю строку со счётчиками"""
        self.bottom_stats = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=44,
            spacing=20,
            padding=[12, 6, 12, 6]
        )

        # Сердечко для лайков
        like_icon = MDIconButton(
            icon="heart",
            size_hint=(None, None),
            size=(18, 18),
            theme_icon_color="Custom",
            icon_color=[0.8, 0.3, 0.3, 0.7],
            disabled=True
        )
        self.like_count = MDLabel(
            text="0",
            font_size=12,
            size_hint_x=None,
            width=35,
            theme_text_color="Custom",
            text_color=[0.8, 0.3, 0.3, 0.8],
            bold=True,
            valign="middle"
        )
        like_box = MDBoxLayout(orientation='horizontal', spacing=4, size_hint_x=None, width=55)
        like_box.add_widget(like_icon)
        like_box.add_widget(self.like_count)

        # Звёздочка для избранного
        fav_icon = MDIconButton(
            icon="star",
            size_hint=(None, None),
            size=(18, 18),
            theme_icon_color="Custom",
            icon_color=[0.9, 0.7, 0.2, 0.7],
            disabled=True
        )
        self.favorite_count = MDLabel(
            text="0",
            font_size=12,
            size_hint_x=None,
            width=35,
            theme_text_color="Custom",
            text_color=[0.9, 0.7, 0.2, 0.8],
            bold=True,
            valign="middle"
        )
        fav_box = MDBoxLayout(orientation='horizontal', spacing=4, size_hint_x=None, width=55)
        fav_box.add_widget(fav_icon)
        fav_box.add_widget(self.favorite_count)

        # Глазик для просмотров
        views_icon = MDIconButton(
            icon="eye-outline",
            size_hint=(None, None),
            size=(18, 18),
            theme_icon_color="Custom",
            icon_color=[0.5, 0.5, 0.5, 0.6],
            disabled=True
        )
        self.views_count = MDLabel(
            text="0",
            font_size=12,
            size_hint_x=None,
            width=40,
            theme_text_color="Custom",
            text_color=[0.5, 0.5, 0.5, 0.7],
            valign="middle"
        )
        views_box = MDBoxLayout(orientation='horizontal', spacing=4, size_hint_x=None, width=60)
        views_box.add_widget(views_icon)
        views_box.add_widget(self.views_count)

        left_spacer = Widget(size_hint_x=1)
        right_spacer = Widget(size_hint_x=1)

        self.bottom_stats.add_widget(left_spacer)
        self.bottom_stats.add_widget(like_box)
        self.bottom_stats.add_widget(fav_box)
        self.bottom_stats.add_widget(views_box)
        self.bottom_stats.add_widget(right_spacer)

    def _update_content_height(self, *args):
        self.content_label.height = self.content_label.texture_size[1] + 20

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

        # Формируем заголовок
        self.song_title_label.text = f"{self.artist} — {self.title}"

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

        # Прокрутка вверх
        Clock.schedule_once(lambda dt: setattr(self.content_scroll, 'scroll_y', 1), 0.1)
        self.hide_loading()
        logger.info(f"Песня загружена: {self.artist} - {self.title}")

    def on_load_failed(self, req, error):
        self.hide_loading()
        self.content_label.text = "Ошибка загрузки песни"
        notify.error(f"Ошибка загрузки песни: {error}")

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
            self.like_btn.icon = "heart" if self.is_liked else "heart-outline"
            self.favorite_btn.icon = "star" if self.is_favorite else "star-outline"

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

    def go_back(self, instance=None):
        if hasattr(self, 'manager') and self.manager:
            self.manager.current = self.previous_screen

    def on_enter(self):
        """При входе на экран - настраиваем верхнюю панель"""
        logger.info("Вход в экран просмотра песни")

        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            app.top_nav.set_custom_title("Подбор песни")
            app.top_nav._show_back_button()
            app.top_nav.back_btn.on_release = self.go_back

    def on_leave(self):
        """При выходе с экрана - восстанавливаем верхнюю панель"""
        logger.info("Выход из экрана просмотра песни")

        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            app.top_nav.reset_to_default()