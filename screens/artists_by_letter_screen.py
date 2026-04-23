# screens/artists_by_letter_screen.py
"""
Экран списка исполнителей по выбранной букве
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
from io import BytesIO

from config.theme import theme
from config.logger_config import screen_logger
from api.client import api
from utils.notifications import notify

logger = screen_logger('ArtistsByLetter')

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
    """Индикатор загрузки"""

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
            text="Загрузка исполнителей...",
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


class ArtistCard(MDCard):
    """Красивая полупрозрачная карточка исполнителя"""

    def __init__(self, artist, on_click=None, **kwargs):
        super().__init__(**kwargs)
        self.artist = artist
        self.on_click_callback = on_click

        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = dp(60)
        self.padding = [dp(16), dp(8), dp(16), dp(8)]
        self.spacing = dp(12)
        self.radius = [theme.CORNER_RADIUS_SMALL]
        self.elevation = 2
        self.ripple_behavior = True

        # Устанавливаем полупрозрачный фон через theme_bg_color
        self.theme_bg_color = "Custom"
        self.md_bg_color = [1, 1, 1, 0.15]  # Белый с прозрачностью 15%
        self.line_color = [1, 1, 1, 0.1]  # Полупрозрачная граница
        self.line_width = 1

        # Иконка исполнителя из ассетов
        self.icon_image = Image(
            size_hint=(None, None),
            size=(dp(32), dp(32)),
            pos_hint={'center_y': 0.5},
            allow_stretch=True,
            keep_ratio=True
        )
        self._load_icon()

        # Название исполнителя
        self.artist_label = MDLabel(
            text=artist,
            font_size=sp(16),
            size_hint_x=1,
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.95],
            bold=True,
            valign="middle"
        )

        # Стрелка вправо
        self.arrow_label = MDLabel(
            text="›",
            font_size=sp(28),
            size_hint_x=None,
            width=dp(32),
            halign="center",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.6]
        )

        self.add_widget(self.icon_image)
        self.add_widget(self.artist_label)
        self.add_widget(self.arrow_label)

        self.bind(on_release=self.on_click)

    def _load_icon(self):
        """Загружает иконку из ассетов"""
        if HAS_ASSETS:
            try:
                icon_data = load_asset_as_bytes('artist_png')
                if icon_data:
                    img = CoreImage(BytesIO(icon_data), ext="png")
                    self.icon_image.texture = img.texture
                    return
            except Exception as e:
                logger.error(f"Ошибка загрузки иконки artist_png: {e}")

        # Если не загрузилась, показываем эмодзи
        self.icon_image.text = "🎸"

    def on_click(self, instance):
        if self.on_click_callback:
            self.on_click_callback(self.artist)


class ArtistsByLetterScreen(MDScreen):
    """Экран списка исполнителей по букве"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'artists_by_letter'
        self.current_letter = None
        self.is_loading = False
        self.loading_spinner = None
        self.bg_image = None

        # Делаем фон экрана прозрачным для фонового изображения
        self.md_bg_color = [0, 0, 0, 0]

        self.init_ui()
        self.load_background()

        logger.info('Экран исполнителей по букве создан')

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

    def init_ui(self):
        # Основной контейнер
        main_layout = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            spacing=0
        )

        # Отступ сверху для компенсации верхней панели (которая в main.py)
        top_spacer = Widget(size_hint_y=None, height=dp(65))
        main_layout.add_widget(top_spacer)

        # ============ РЯД С НАВИГАЦИЕЙ ============
        self.nav_row = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(56),
            padding=[dp(12), dp(8), dp(12), dp(8)],
            spacing=dp(8),
            md_bg_color=[0, 0, 0, 0]  # Полностью прозрачный фон
        )

        # Кнопка назад (стрелка)
        self.back_btn = MDIconButton(
            icon="arrow-left",
            size_hint=(None, None),
            size=(dp(40), dp(40)),
            theme_icon_color="Custom",
            icon_color=[1, 1, 1, 1],
            md_bg_color=[0, 0, 0, 0],
            on_release=self.go_back
        )

        # Текст "Назад"
        self.back_label = MDLabel(
            text="Назад",
            font_size=sp(14),
            size_hint_x=None,
            width=dp(50),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.8],
            valign="middle"
        )

        # Выбранная буква
        self.letter_title = MDLabel(
            text="",
            font_size=sp(24),
            halign="center",
            valign="middle",
            size_hint_x=0.5,
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
            bold=True
        )

        # Счётчик исполнителей
        self.counter_label = MDLabel(
            text="",
            font_size=sp(12),
            halign="right",
            valign="middle",
            size_hint_x=0.3,
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.6]
        )

        self.nav_row.add_widget(self.back_btn)
        self.nav_row.add_widget(self.back_label)
        self.nav_row.add_widget(self.letter_title)
        self.nav_row.add_widget(self.counter_label)

        # ============ КОНТЕЙНЕР ДЛЯ СПИСКА ИСПОЛНИТЕЛЕЙ ============
        self.content_scroll = MDScrollView(
            size_hint=(1, 1),
            do_scroll_x=False,
            bar_color=[1, 1, 1, 0.3],
            bar_width=dp(4)
        )
        self.content_container = MDBoxLayout(
            orientation='vertical',
            spacing=dp(8),
            size_hint_y=None,
            adaptive_height=True,
            padding=[dp(16), dp(12), dp(16), dp(16)]
        )
        self.content_scroll.add_widget(self.content_container)

        main_layout.add_widget(self.nav_row)
        main_layout.add_widget(self.content_scroll)

        self.add_widget(main_layout)

    def show_loading(self):
        """Показывает индикатор загрузки"""
        if self.is_loading:
            return
        self.is_loading = True
        self.content_container.clear_widgets()
        self.loading_spinner = LoadingSpinner()
        self.content_container.add_widget(self.loading_spinner)
        self.loading_spinner.start_animation()

    def hide_loading(self):
        """Скрывает индикатор загрузки"""
        self.is_loading = False
        if self.loading_spinner:
            self.loading_spinner.stop_animation()
        self.content_container.clear_widgets()

    def set_letter(self, letter):
        """Устанавливает букву и загружает исполнителей"""
        self.current_letter = letter
        self.letter_title.text = letter.upper()
        self.load_artists()

    def update_counter(self, count):
        """Обновляет счётчик исполнителей"""
        # Склонение слова "исполнитель"
        if count % 10 == 1 and count % 100 != 11:
            word = "исполнитель"
        elif 2 <= count % 10 <= 4 and not (12 <= count % 100 <= 14):
            word = "исполнителя"
        else:
            word = "исполнителей"

        self.counter_label.text = f"{count} {word}"

    def load_artists(self):
        """Загружает исполнителей по букве"""
        self.show_loading()

        api.get_artists_by_letter(
            letter=self.current_letter,
            on_success=self.on_artists_loaded,
            on_failure=self.on_load_failed
        )

    def on_artists_loaded(self, artists):
        """Отображает список исполнителей"""
        self.hide_loading()

        if not artists:
            # Обновляем счётчик
            self.update_counter(0)

            # Сообщение об отсутствии исполнителей
            empty_card = MDCard(
                orientation='vertical',
                size_hint=(1, None),
                height=dp(160),
                padding=[dp(24), dp(24), dp(24), dp(24)],
                radius=[theme.CORNER_RADIUS_SMALL],
                md_bg_color=[1, 1, 1, 0.15],
                elevation=2
            )

            icon_label = MDLabel(
                text="🎵",
                font_size=sp(48),
                halign="center",
                size_hint_y=None,
                height=dp(60),
                theme_text_color="Custom",
                text_color=[1, 1, 1, 0.7]
            )

            text_label = MDLabel(
                text=f"Нет исполнителей на букву «{self.current_letter}»",
                halign="center",
                font_size=sp(14),
                theme_text_color="Custom",
                text_color=[1, 1, 1, 0.8],
                size_hint_y=None,
                height=dp(40),
                bold=True
            )

            hint_label = MDLabel(
                text="Попробуйте выбрать другую букву",
                halign="center",
                font_size=sp(12),
                theme_text_color="Custom",
                text_color=[1, 1, 1, 0.5],
                size_hint_y=None,
                height=dp(30)
            )

            empty_card.add_widget(icon_label)
            empty_card.add_widget(text_label)
            empty_card.add_widget(hint_label)
            self.content_container.add_widget(empty_card)
            return

        # Обновляем счётчик
        self.update_counter(len(artists))

        # Отображаем карточки исполнителей
        for artist_data in artists:
            artist = artist_data.get('artist')
            if artist:
                card = ArtistCard(artist=artist, on_click=self.on_artist_selected)
                self.content_container.add_widget(card)

        logger.info(f"Загружено {len(artists)} исполнителей на букву {self.current_letter}")

    def on_artist_selected(self, artist):
        """Выбор исполнителя - переход на экран его песен"""
        logger.info(f"Выбран исполнитель: {artist}")

        # Здесь будет переход на экран песен исполнителя
        if hasattr(self, 'manager') and self.manager:
            # Проверяем наличие экрана artist_songs
            if self.manager.has_screen('artist_songs'):
                artist_songs_screen = self.manager.get_screen('artist_songs')
                if hasattr(artist_songs_screen, 'set_artist'):
                    artist_songs_screen.set_artist(artist)
                    self.manager.current = 'artist_songs'
            else:
                # Временно показываем уведомление
                notify.info(f"Выбран исполнитель: {artist}")

    def on_load_failed(self, req, error):
        """Ошибка загрузки"""
        self.hide_loading()
        notify.error(f"Ошибка загрузки: {error}")
        logger.error(f"Ошибка загрузки: {error}")

        # Показываем сообщение об ошибке
        error_card = MDCard(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(160),
            padding=[dp(24), dp(24), dp(24), dp(24)],
            radius=[theme.CORNER_RADIUS_SMALL],
            md_bg_color=[1, 1, 1, 0.15],
            elevation=2
        )

        icon_label = MDLabel(
            text="⚠️",
            font_size=sp(48),
            halign="center",
            size_hint_y=None,
            height=dp(60),
            theme_text_color="Custom",
            text_color=[1, 0.5, 0.3, 0.9]
        )

        text_label = MDLabel(
            text="Ошибка загрузки",
            halign="center",
            font_size=sp(14),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.8],
            size_hint_y=None,
            height=dp(40),
            bold=True
        )

        hint_label = MDLabel(
            text="Проверьте подключение к интернету",
            halign="center",
            font_size=sp(12),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.5],
            size_hint_y=None,
            height=dp(30)
        )

        error_card.add_widget(icon_label)
        error_card.add_widget(text_label)
        error_card.add_widget(hint_label)
        self.content_container.add_widget(error_card)

    def go_back(self, instance):
        """Возврат на экран выбора буквы"""
        if hasattr(self, 'manager') and self.manager:
            self.manager.current = 'songs'