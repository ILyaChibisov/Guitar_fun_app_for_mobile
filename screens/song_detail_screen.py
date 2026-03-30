# screens/song_detail_screen.py
"""
Экран просмотра песни с текстом и подборами
"""
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDIconButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.snackbar import MDSnackbar
from kivymd.uix.progressbar import MDProgressBar
from kivy.metrics import dp
from kivy.animation import Animation
from kivy.clock import Clock
from config.theme import theme
from config.logger_config import screen_logger
from api.client import api

logger = screen_logger('SongDetail')


def show_snackbar(message, bg_color=None):
    """Показывает уведомление"""
    snack = MDSnackbar()
    snack.text = message
    snack.snackbar_x = "10dp"
    snack.snackbar_y = "10dp"
    snack.radius = [theme.CORNER_RADIUS_SMALL, theme.CORNER_RADIUS_SMALL,
                    theme.CORNER_RADIUS_SMALL, theme.CORNER_RADIUS_SMALL]
    if bg_color:
        snack.md_bg_color = bg_color
    snack.open()


class LoadingSpinner(MDBoxLayout):
    """Индикатор загрузки"""

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
        """Запускает анимацию загрузки"""
        self.anim = Animation(value=100, duration=1) + Animation(value=0, duration=1)
        self.anim.repeat = True
        self.anim.start(self.progress)

    def stop_animation(self):
        """Останавливает анимацию загрузки"""
        if self.anim:
            self.anim.cancel(self.progress)
        self.progress.value = 0


class SongDetailScreen(MDScreen):
    """Экран просмотра песни"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'song_detail'
        self.song_id = None
        self.current_tab_index = 0
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

        # Пагинация подборов
        self.pagination_layout = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(48),
            spacing=dp(16),
            pos_hint={'center_x': 0.5}
        )

        self.prev_tab_btn = MDIconButton(
            icon="chevron-left",
            theme_text_color="Custom",
            text_color=theme.PRIMARY,
            on_release=self.prev_tab,
            disabled=True
        )

        self.tab_info = MDLabel(
            text="",
            halign="center",
            font_style="Body1",
            theme_text_color="Secondary",
            size_hint_x=0.6
        )

        self.next_tab_btn = MDIconButton(
            icon="chevron-right",
            theme_text_color="Custom",
            text_color=theme.PRIMARY,
            on_release=self.next_tab,
            disabled=True
        )

        self.pagination_layout.add_widget(self.prev_tab_btn)
        self.pagination_layout.add_widget(self.tab_info)
        self.pagination_layout.add_widget(self.next_tab_btn)

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

        # Нижняя панель с кнопками
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
        self.main_layout.add_widget(self.pagination_layout)
        self.main_layout.add_widget(self.content_scroll)
        self.main_layout.add_widget(self.bottom_bar)

        self.add_widget(self.main_layout)

        logger.info('Экран просмотра песни создан')

    def _update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def show_loading(self):
        """Показывает индикатор загрузки"""
        if self.is_loading:
            return

        self.is_loading = True
        self.loading_spinner = LoadingSpinner()
        self.add_widget(self.loading_spinner)
        self.loading_spinner.start_animation()
        self.main_layout.opacity = 0.3
        self.main_layout.disabled = True

    def hide_loading(self):
        """Скрывает индикатор загрузки"""
        self.is_loading = False
        if self.loading_spinner:
            self.loading_spinner.stop_animation()
            self.remove_widget(self.loading_spinner)
            self.loading_spinner = None
        self.main_layout.opacity = 1
        self.main_layout.disabled = False

    def set_song_data(self, song_id: int, artist: str, title: str, tabs: list):
        """Устанавливает данные песни и загружает текст первого подбора"""
        logger.info(f"set_song_data вызван: {artist} - {title}, подборов: {len(tabs)}")
        self.song_id = song_id
        self.artist = artist
        self.title = title
        self.tabs = tabs
        self.current_tab_index = 0

        self.title_label.text = f"🎸 {self.artist} — {self.title}"

        # Загружаем текст для первого подбора
        if tabs and len(tabs) > 0:
            tab = tabs[0]
            self.current_tab_id = tab['id']
            self.in_favorites_count = tab.get('in_favorites_count', 0)
            self.is_liked = tab.get('is_liked', False)
            self.is_favorite = tab.get('is_favorite', False)

            # Обновляем отображение пагинации
            self._update_tab_info()
            self._update_pagination_buttons()
            self.update_stats_display()
            self.update_buttons_state()

            # Загружаем текст подбора
            self.load_tab_content(tab['id'])

        logger.info(f"Экран песни обновлён: {self.title_label.text}")

    def load_tab_content(self, tab_id: int):
        """Загружает текст подбора по ID"""
        self.show_loading()
        api.get_tab(
            song_id=tab_id,
            on_success=self.on_tab_content_loaded,
            on_failure=self.on_tab_content_failed
        )

    def on_tab_content_loaded(self, data):
        """Обработчик загрузки текста подбора"""
        content = data.get('content', 'Текст не загружен')
        self.content_label.text = content
        self.content_label.texture_update()
        self.content_label.height = self.content_label.texture_size[1]

        # Обновляем статистику
        self.views_label.text = f"👁️ {data.get('views', 0)}"
        self.like_count.text = str(data.get('likes', 0))

        self.hide_loading()
        logger.info(f"Текст подбора загружен, длина: {len(content)} символов")

    def on_tab_content_failed(self, req, error):
        """Обработчик ошибки загрузки текста"""
        self.hide_loading()
        self.content_label.text = f"Ошибка загрузки текста: {error}"
        logger.error(f"Ошибка загрузки текста подбора {self.current_tab_id}: {error}")

    def set_song(self, song_id):
        """Загружает песню по ID (для совместимости)"""
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
        self.artist = data.get('artist')
        self.title = data.get('title')
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

        self.update_tab_display()
        self.update_stats_display()
        self.update_buttons_state()

        self.hide_loading()

    def on_load_failed(self, req, error):
        """Обработчик ошибки загрузки"""
        self.hide_loading()
        show_snackbar(f"Ошибка загрузки песни: {error}")
        logger.error(f"Ошибка загрузки песни {self.song_id}: {error}")
        self.go_back(None)

    def _update_tab_info(self):
        """Обновляет информацию о текущем подборе"""
        if not self.tabs:
            return
        tab = self.tabs[self.current_tab_index]
        tab_name = f" ({tab.get('tab_name')})" if tab.get('tab_name') else ""
        self.tab_info.text = f"Подбор {tab['tab_number']} из {len(self.tabs)}{tab_name}"

    def _update_pagination_buttons(self):
        """Обновляет состояние кнопок пагинации"""
        if not self.tabs:
            self.prev_tab_btn.disabled = True
            self.next_tab_btn.disabled = True
            return
        self.prev_tab_btn.disabled = (self.current_tab_index == 0)
        self.next_tab_btn.disabled = (self.current_tab_index == len(self.tabs) - 1)

    def update_stats_display(self):
        """Обновляет отображение статистики"""
        self.favorite_count.text = str(self.in_favorites_count)

    def update_buttons_state(self):
        """Обновляет состояние кнопок лайка и избранного"""
        if api.is_authenticated():
            self.like_btn.icon = "heart" if self.is_liked else "heart-outline"
            self.favorite_btn.icon = "star" if self.is_favorite else "star-outline"
        else:
            self.like_btn.disabled = True
            self.favorite_btn.disabled = True

    def prev_tab(self, instance):
        """Предыдущий подбор"""
        if self.current_tab_index > 0:
            self.current_tab_index -= 1
            tab = self.tabs[self.current_tab_index]
            self.current_tab_id = tab['id']
            self.is_liked = tab.get('is_liked', False)
            self.is_favorite = tab.get('is_favorite', False)
            self.load_tab_content(tab['id'])
            self._update_tab_info()
            self._update_pagination_buttons()
            self.update_stats_display()
            self.update_buttons_state()

    def next_tab(self, instance):
        """Следующий подбор"""
        if self.current_tab_index < len(self.tabs) - 1:
            self.current_tab_index += 1
            tab = self.tabs[self.current_tab_index]
            self.current_tab_id = tab['id']
            self.is_liked = tab.get('is_liked', False)
            self.is_favorite = tab.get('is_favorite', False)
            self.load_tab_content(tab['id'])
            self._update_tab_info()
            self._update_pagination_buttons()
            self.update_stats_display()
            self.update_buttons_state()

    def toggle_like(self, instance):
        """Переключает лайк"""
        if not api.is_authenticated():
            self.show_auth_required()
            return

        self.show_loading()
        api.toggle_like(
            song_id=self.current_tab_id,
            on_success=self.on_like_toggled,
            on_failure=self.on_action_failed
        )

    def on_like_toggled(self, result):
        """Обработчик ответа на лайк"""
        self.is_liked = result.get('liked', False)
        new_likes = result.get('total_likes', 0)

        if self.tabs and self.current_tab_index < len(self.tabs):
            self.tabs[self.current_tab_index]['likes'] = new_likes

        self.like_count.text = str(new_likes)
        self.update_buttons_state()
        self.hide_loading()

        show_snackbar("❤️ +1" if self.is_liked else "❤️ -1")

    def toggle_favorite(self, instance):
        """Переключает избранное"""
        if not api.is_authenticated():
            self.show_auth_required()
            return

        self.show_loading()

        if self.is_favorite:
            api.remove_from_favorites(
                song_id=self.current_tab_id,
                on_success=self.on_favorite_toggled,
                on_failure=self.on_action_failed
            )
        else:
            api.add_to_favorites(
                song_id=self.current_tab_id,
                on_success=self.on_favorite_toggled,
                on_failure=self.on_action_failed
            )

    def on_favorite_toggled(self, result):
        """Обработчик ответа на избранное"""
        self.is_favorite = result.get('favorited', False)
        self.in_favorites_count = result.get('total_favorites', 0)

        self.favorite_count.text = str(self.in_favorites_count)
        self.update_buttons_state()
        self.hide_loading()

        if self.is_favorite:
            show_snackbar("⭐ Добавлено в избранное", theme.WARNING)
        else:
            show_snackbar("❌ Удалено из избранного")

    def on_action_failed(self, req, error):
        """Обработчик ошибки действия"""
        error_msg = str(error)
        self.hide_loading()

        if 'Not authenticated' in error_msg or 'Invalid token' in error_msg:
            show_snackbar("🔐 Сессия истекла. Пожалуйста, войдите снова.")
            api._clear_tokens()
            app = MDApp.get_running_app()
            if hasattr(app, 'home_screen') and app.home_screen:
                app.home_screen.show_auth_modal()
        else:
            show_snackbar(f"Ошибка: {error_msg}")

        logger.error(f"Ошибка действия: {error_msg}")

    def share_song(self, instance):
        """Поделиться песней (заглушка)"""
        show_snackbar("🔄 Функция будет доступна в следующей версии")

    def open_menu(self, instance):
        """Открывает меню (заглушка)"""
        show_snackbar("📋 Меню будет доступно в следующей версии")

    def show_auth_required(self):
        """Показывает сообщение о необходимости авторизации"""
        show_snackbar("🔐 Войдите, чтобы выполнить это действие")

    def go_back(self, instance):
        """Возврат на предыдущий экран"""
        app = MDApp.get_running_app()
        if app and hasattr(app, 'switch_screen'):
            app.switch_screen('songs')