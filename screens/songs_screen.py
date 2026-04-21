# screens/songs_screen.py
"""
Экран песен с алфавитной навигацией, поиском и отображением текста песен
"""
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDButton, MDIconButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.metrics import dp, sp
from kivy.animation import Animation
from kivy.uix.progressbar import ProgressBar
from kivy.clock import Clock
from kivy.utils import rgba
from kivy.graphics import Color, Rectangle
from kivy.core.image import Image as CoreImage
from kivy.uix.behaviors import ButtonBehavior
from io import BytesIO

from config.theme import theme
from config.logger_config import screen_logger
from api.client import api
from utils.notifications import notify

logger = screen_logger('Songs')

# Попытка импорта ассетов
try:
    from data import load_asset_as_bytes

    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False


    def load_asset_as_bytes(name):
        return None


    logger.warning("Модуль data не найден")


# ============ КНОПКА БУКВЫ ============

class LetterButton(ButtonBehavior, MDBoxLayout):
    """Кнопка буквы для клавиатуры"""

    def __init__(self, text, is_active=False, on_press_callback=None, **kwargs):
        super().__init__(**kwargs)
        self.btn_text = text
        self.on_press_callback = on_press_callback
        self.size_hint = (1, 1)
        self.padding = [dp(2), dp(2), dp(2), dp(2)]

        self.main_layout = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            padding=[dp(2), dp(2), dp(2), dp(2)]
        )

        self.label = MDLabel(
            text=text,
            font_size=sp(13),
            halign="center",
            valign="middle",
            theme_text_color="Custom",
            bold=True,
            size_hint=(1, 1),
            text_size=(None, None),
            shorten=False
        )
        self.main_layout.add_widget(self.label)
        self.add_widget(self.main_layout)

        self.is_active = is_active
        self.bind(on_release=self._on_press)
        self.update_style()

    def update_style(self):
        if self.is_active:
            self.label.text_color = [1, 1, 1, 1]
            self.main_layout.md_bg_color = [0.46, 0.70, 0.71, 1]
            self.main_layout.radius = [dp(6), dp(6), dp(6), dp(6)]
        else:
            self.label.text_color = [0, 0, 0, 1]
            self.main_layout.md_bg_color = [0, 0, 0, 0]
            self.main_layout.radius = [0, 0, 0, 0]

    def set_active(self, active):
        self.is_active = active
        self.update_style()

    def _on_press(self, instance):
        if self.on_press_callback:
            self.on_press_callback(self.btn_text)


class AlphabetKeyboard(MDBoxLayout):
    """Клавиатура с буквами и пагинацией"""

    def __init__(self, on_letter_press=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = dp(70)
        self.spacing = dp(4)
        self.padding = [dp(12), dp(2), dp(12), dp(2)]

        self.on_letter_press = on_letter_press
        self.current_language = 'ru'
        self.current_page = 0

        # Русский алфавит (33 буквы)
        self.ru_letters = ['А', 'Б', 'В', 'Г', 'Д', 'Е', 'Ё', 'Ж', 'З', 'И',
                           'Й', 'К', 'Л', 'М', 'Н', 'О', 'П', 'Р', 'С', 'Т',
                           'У', 'Ф', 'Х', 'Ц', 'Ч', 'Ш', 'Щ', 'Ъ', 'Ы', 'Ь',
                           'Э', 'Ю', 'Я']
        # Английский алфавит (26 букв)
        self.en_letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J',
                           'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T',
                           'U', 'V', 'W', 'X', 'Y', 'Z']
        # Символы и цифры
        self.symbols = ['#', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0']

        self.current_items = self.ru_letters
        self.items_per_page = 5
        self.total_pages = (len(self.current_items) + self.items_per_page - 1) // self.items_per_page
        self.buttons = []

        # Заголовок с пагинацией
        title_layout = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(24),
            spacing=dp(12),
            padding=[dp(4), dp(1), dp(4), dp(1)]
        )

        self.prev_btn = MDIconButton(
            icon="chevron-left",
            size_hint=(None, None),
            size=(dp(28), dp(28)),
            theme_icon_color="Custom",
            icon_color="#FFFFFF",
            on_release=self.prev_page,
            md_bg_color=[0, 0, 0, 0]
        )

        self.title_label = MDLabel(
            text="Русский",
            font_size=sp(12),
            halign="center",
            valign="middle",
            size_hint_x=0.6,
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
            bold=True
        )

        self.next_btn = MDIconButton(
            icon="chevron-right",
            size_hint=(None, None),
            size=(dp(28), dp(28)),
            theme_icon_color="Custom",
            icon_color="#FFFFFF",
            on_release=self.next_page,
            md_bg_color=[0, 0, 0, 0]
        )

        title_layout.add_widget(MDBoxLayout(size_hint_x=0.05))
        title_layout.add_widget(self.prev_btn)
        title_layout.add_widget(self.title_label)
        title_layout.add_widget(self.next_btn)
        title_layout.add_widget(MDBoxLayout(size_hint_x=0.05))

        self.add_widget(title_layout)

        # Серая полоска с буквами
        self.letters_card = MDCard(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(40),
            radius=[theme.CORNER_RADIUS_SMALL, theme.CORNER_RADIUS_SMALL,
                    theme.CORNER_RADIUS_SMALL, theme.CORNER_RADIUS_SMALL],
            md_bg_color="#E8E8E8",
            elevation=0,
            padding=[dp(4), dp(2), dp(4), dp(2)]
        )

        self.buttons_container = MDBoxLayout(
            orientation='horizontal',
            spacing=dp(4),
            size_hint_x=1,
            height=dp(34)
        )

        self.letters_card.add_widget(self.buttons_container)
        self.add_widget(self.letters_card)

        self.update_display()

    def set_language(self, language):
        """Устанавливает язык клавиатуры"""
        self.current_language = language
        self.current_page = 0
        if language == 'ru':
            self.current_items = self.ru_letters
            self.title_label.text = "Русский"
        elif language == 'en':
            self.current_items = self.en_letters
            self.title_label.text = "English"
        else:
            self.current_items = self.symbols
            self.title_label.text = "Символы"
        self.total_pages = (len(self.current_items) + self.items_per_page - 1) // self.items_per_page
        self.update_display()

    def update_display(self):
        self.buttons_container.clear_widgets()
        self.buttons.clear()

        self.prev_btn.icon_color = [1, 1, 1, 1]
        self.next_btn.icon_color = [1, 1, 1, 1]

        start_idx = self.current_page * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, len(self.current_items))
        current_items = self.current_items[start_idx:end_idx]

        for item in current_items:
            btn = LetterButton(
                text=item,
                is_active=False,
                on_press_callback=self.on_letter_press_callback
            )
            self.buttons.append(btn)
            self.buttons_container.add_widget(btn)

        for i in range(self.items_per_page - len(current_items)):
            spacer = MDBoxLayout(size_hint=(1, 1))
            self.buttons_container.add_widget(spacer)

    def on_letter_press_callback(self, letter):
        if self.on_letter_press:
            self.on_letter_press(letter)

    def prev_page(self, instance):
        if self.current_page > 0:
            self.current_page -= 1
        else:
            self.current_page = self.total_pages - 1
        self.update_display()

    def next_page(self, instance):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
        else:
            self.current_page = 0
        self.update_display()


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


class SongTextCard(MDCard):
    """Карточка с текстом песни"""

    def __init__(self, song_data, on_close=None, **kwargs):
        super().__init__(**kwargs)
        self.song_data = song_data
        self.on_close_callback = on_close

        self.orientation = 'vertical'
        self.size_hint = (1, None)
        self.height = dp(400)
        self.padding = [dp(16), dp(12), dp(16), dp(12)]
        self.radius = [theme.CORNER_RADIUS_SMALL]
        self.md_bg_color = theme.SURFACE
        self.elevation = 4

        # Заголовок с информацией о песне
        header_box = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(80),
            spacing=dp(12)
        )

        # Иконка
        icon_label = MDLabel(
            text="🎵",
            font_size=sp(32),
            size_hint_x=None,
            width=dp(50),
            halign="center"
        )

        # Информация
        info_box = MDBoxLayout(
            orientation='vertical',
            size_hint_x=0.7,
            spacing=dp(4)
        )

        self.title_label = MDLabel(
            text=song_data.get('title', ''),
            font_size=sp(16),
            size_hint_y=None,
            height=dp(28),
            theme_text_color="Custom",
            text_color=theme.TEXT_PRIMARY,
            bold=True
        )

        self.artist_label = MDLabel(
            text=f"🎸 {song_data.get('artist', '')}",
            font_size=sp(13),
            size_hint_y=None,
            height=dp(22),
            theme_text_color="Custom",
            text_color=theme.TEXT_SECONDARY
        )

        info_box.add_widget(self.title_label)
        info_box.add_widget(self.artist_label)

        # Кнопка закрытия
        close_btn = MDIconButton(
            icon="close",
            size_hint_x=None,
            width=dp(40),
            theme_icon_color="Custom",
            icon_color=theme.TEXT_SECONDARY,
            on_release=self.on_close
        )

        header_box.add_widget(icon_label)
        header_box.add_widget(info_box)
        header_box.add_widget(close_btn)

        self.add_widget(header_box)

        # Разделитель
        from kivy.uix.widget import Widget
        divider = Widget(size_hint_y=None, height=dp(1))
        with divider.canvas:
            Color(*rgba(theme.TEXT_SECONDARY, alpha=0.2))
            self.divider_rect = Rectangle(pos=divider.pos, size=divider.size)
        divider.bind(pos=self._update_divider, size=self._update_divider)
        self.add_widget(divider)

        # Текст песни (скроллируемый)
        self.text_scroll = MDScrollView(
            size_hint=(1, 0.8),
            do_scroll_x=False
        )

        self.content_label = MDLabel(
            text=song_data.get('content', 'Текст не загружен'),
            font_size=sp(14),
            size_hint_y=None,
            theme_text_color="Custom",
            text_color=theme.TEXT_PRIMARY,
            markup=True
        )
        self.content_label.bind(texture_size=self.content_label.setter('size'))
        self.text_scroll.add_widget(self.content_label)
        self.add_widget(self.text_scroll)

        # Нижняя панель с кнопками действий
        action_bar = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(50),
            spacing=dp(16),
            padding=[dp(8), dp(8), dp(8), dp(8)]
        )

        # Кнопка лайка
        self.like_btn = MDIconButton(
            icon="heart-outline",
            theme_icon_color="Custom",
            icon_color=theme.TEXT_SECONDARY,
            on_release=self.toggle_like
        )

        # Кнопка избранного
        self.favorite_btn = MDIconButton(
            icon="star-outline",
            theme_icon_color="Custom",
            icon_color=theme.TEXT_SECONDARY,
            on_release=self.toggle_favorite
        )

        # Кнопка копирования
        self.copy_btn = MDIconButton(
            icon="content-copy",
            theme_icon_color="Custom",
            icon_color=theme.TEXT_SECONDARY,
            on_release=self.copy_text
        )

        action_bar.add_widget(self.like_btn)
        action_bar.add_widget(self.favorite_btn)
        action_bar.add_widget(self.copy_btn)

        self.add_widget(action_bar)

    def _update_divider(self, instance, value):
        self.divider_rect.pos = instance.pos
        self.divider_rect.size = instance.size

    def on_close(self, instance):
        if self.on_close_callback:
            self.on_close_callback()

    def toggle_like(self, instance):
        if not api.is_authenticated():
            notify.warning("Войдите, чтобы ставить лайки")
            return
        if self.like_btn.icon == "heart-outline":
            self.like_btn.icon = "heart"
            self.like_btn.icon_color = [0.8, 0.3, 0.3, 1]
            notify.info("❤️ Лайк поставлен")
        else:
            self.like_btn.icon = "heart-outline"
            self.like_btn.icon_color = theme.TEXT_SECONDARY
            notify.info("❤️ Лайк убран")

    def toggle_favorite(self, instance):
        if not api.is_authenticated():
            notify.warning("Войдите, чтобы добавлять в избранное")
            return
        if self.favorite_btn.icon == "star-outline":
            self.favorite_btn.icon = "star"
            self.favorite_btn.icon_color = [0.9, 0.7, 0.2, 1]
            notify.info("⭐ Добавлено в избранное")
        else:
            self.favorite_btn.icon = "star-outline"
            self.favorite_btn.icon_color = theme.TEXT_SECONDARY
            notify.info("⭐ Убрано из избранного")

    def copy_text(self, instance):
        """Копирует текст песни в буфер обмена"""
        try:
            from kivy.core.clipboard import Clipboard
            Clipboard.copy(self.content_label.text)
            notify.success("📋 Текст скопирован")
        except Exception as e:
            logger.error(f"Ошибка копирования: {e}")
            notify.error("Не удалось скопировать")


class ArtistCard(MDCard):
    """Красивая карточка исполнителя с количеством песен"""

    def __init__(self, artist_data, on_song_click=None, **kwargs):
        super().__init__(**kwargs)
        self.artist_name = artist_data.get('artist', '')
        self.songs_count = artist_data.get('songs_count', 0)
        self.songs = artist_data.get('songs', [])
        self.on_song_click_callback = on_song_click
        self.is_expanded = False

        self.orientation = 'vertical'
        self.size_hint = (1, None)
        self.height = dp(70)
        self.padding = [dp(16), dp(12), dp(12), dp(12)]
        self.radius = [theme.CORNER_RADIUS_SMALL]
        self.md_bg_color = theme.SURFACE
        self.elevation = 2

        # Основной контейнер
        self.main_row = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(46),
            spacing=dp(12)
        )

        # Иконка исполнителя
        self.icon_label = MDLabel(
            text="🎸",
            font_size=sp(24),
            size_hint_x=None,
            width=dp(44),
            halign="center",
            theme_text_color="Custom",
            text_color=theme.PRIMARY
        )

        # Информация об исполнителе
        info_box = MDBoxLayout(
            orientation='vertical',
            size_hint_x=0.7,
            spacing=dp(2)
        )

        self.artist_label = MDLabel(
            text=self.artist_name,
            font_size=sp(15),
            size_hint_y=None,
            height=dp(24),
            theme_text_color="Custom",
            text_color=theme.TEXT_PRIMARY,
            bold=True
        )

        # Склонение слова "песня"
        if self.songs_count % 10 == 1 and self.songs_count % 100 != 11:
            songs_word = "песня"
        elif 2 <= self.songs_count % 10 <= 4 and not (12 <= self.songs_count % 100 <= 14):
            songs_word = "песни"
        else:
            songs_word = "песен"

        self.songs_count_label = MDLabel(
            text=f"🎵 {self.songs_count} {songs_word}",
            font_size=sp(11),
            size_hint_y=None,
            height=dp(20),
            theme_text_color="Custom",
            text_color=theme.TEXT_SECONDARY
        )

        info_box.add_widget(self.artist_label)
        info_box.add_widget(self.songs_count_label)

        # Кнопка раскрытия
        self.expand_btn = MDIconButton(
            icon="chevron-down",
            size_hint_x=None,
            width=dp(40),
            theme_icon_color="Custom",
            icon_color=theme.TEXT_SECONDARY,
            md_bg_color=[0, 0, 0, 0]
        )
        self.expand_btn.bind(on_release=self.toggle_expand)

        self.main_row.add_widget(self.icon_label)
        self.main_row.add_widget(info_box)
        self.main_row.add_widget(self.expand_btn)

        self.add_widget(self.main_row)

        # Контейнер для песен (изначально скрыт)
        self.songs_container = MDBoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=dp(6),
            padding=[dp(56), dp(8), dp(12), dp(8)]
        )
        self.songs_container.height = 0
        self.add_widget(self.songs_container)

        # Заполняем песнями
        if self.songs:
            for song in self.songs:
                song_card = SongItemCard(song=song, on_click=self.on_song_click)
                self.songs_container.add_widget(song_card)
            self.songs_container.height = len(self.songs) * dp(54)

    def toggle_expand(self, instance):
        """Раскрыть/скрыть список песен"""
        self.is_expanded = not self.is_expanded

        if self.is_expanded:
            self.expand_btn.icon = "chevron-up"
            self.songs_container.height = len(self.songs) * dp(54) if self.songs else 0
            self.height = dp(70) + self.songs_container.height
        else:
            self.expand_btn.icon = "chevron-down"
            self.songs_container.height = 0
            self.height = dp(70)

    def on_song_click(self, song):
        """Обработчик клика по песне"""
        if self.on_song_click_callback:
            self.on_song_click_callback(song)


class SongItemCard(MDCard):
    """Карточка песни внутри исполнителя"""

    def __init__(self, song, on_click=None, **kwargs):
        super().__init__(**kwargs)
        self.song = song
        self.on_click_callback = on_click

        self.size_hint = (1, None)
        self.height = dp(48)
        self.padding = [dp(8), dp(6), dp(8), dp(6)]
        self.radius = [theme.CORNER_RADIUS_SMALL]
        self.md_bg_color = "#F8F6F0"
        self.elevation = 0
        self.ripple_behavior = True

        layout = MDBoxLayout(
            orientation='horizontal',
            spacing=dp(12),
            size_hint_y=None,
            height=dp(36)
        )

        # Иконка песни
        icon_label = MDLabel(
            text="🎵",
            font_size=sp(18),
            size_hint_x=None,
            width=dp(32),
            halign="center"
        )

        # Информация о песне
        info_box = MDBoxLayout(
            orientation='vertical',
            spacing=dp(2),
            size_hint_x=0.75
        )

        title_label = MDLabel(
            text=song.get('title', ''),
            font_size=sp(13),
            size_hint_y=None,
            height=dp(20),
            theme_text_color="Custom",
            text_color=theme.TEXT_PRIMARY,
            bold=True
        )

        tabs_count = song.get('tabs_count', 1)
        # Склонение слова "подбор"
        if tabs_count % 10 == 1 and tabs_count % 100 != 11:
            tabs_word = "подбор"
        elif 2 <= tabs_count % 10 <= 4 and not (12 <= tabs_count % 100 <= 14):
            tabs_word = "подбора"
        else:
            tabs_word = "подборов"

        tabs_label = MDLabel(
            text=f"🎸 {tabs_count} {tabs_word}",
            font_size=sp(10),
            size_hint_y=None,
            height=dp(18),
            theme_text_color="Custom",
            text_color=theme.TEXT_SECONDARY
        )

        info_box.add_widget(title_label)
        info_box.add_widget(tabs_label)

        # Стрелка
        arrow_label = MDLabel(
            text="›",
            font_size=sp(22),
            size_hint_x=None,
            width=dp(30),
            halign="center",
            theme_text_color="Custom",
            text_color=theme.PRIMARY
        )

        layout.add_widget(icon_label)
        layout.add_widget(info_box)
        layout.add_widget(arrow_label)

        self.add_widget(layout)
        self.bind(on_release=self.on_click)

    def on_click(self, instance):
        if self.on_click_callback:
            self.on_click_callback(self.song)


class SongsScreen(MDScreen):
    """Объединенный экран песен с исполнителями и текстами"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'songs'
        self.current_letter = None
        self.current_language = 'ru'
        self.search_mode = False
        self.is_loading = False
        self.loading_spinner = None
        self.artists_data = []
        self.current_song_card = None
        self.bg_image = None

        # Делаем фон экрана прозрачным
        self.md_bg_color = [0, 0, 0, 0]

        self.init_ui()
        self.load_background()

        logger.info('Объединенный экран песен создан')

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

    def on_text_change(self, instance, value):
        """Показывает/скрывает кнопку очистки при вводе текста"""
        self.clear_search_btn.opacity = 1 if value else 0

    def init_ui(self):
        from kivy.uix.scrollview import ScrollView
        from kivy.uix.widget import Widget

        scroll = ScrollView(size_hint=(1, 1))

        # Основной контейнер
        main_layout = MDBoxLayout(
            orientation='vertical',
            padding=[dp(12), dp(2), dp(12), dp(8)],
            spacing=dp(6),
            size_hint_y=None
        )
        main_layout.bind(minimum_height=main_layout.setter('height'))

        # Отступ сверху (чтобы не перекрывать верхние иконки)
        top_spacer = Widget(size_hint_y=None, height=dp(65))
        main_layout.add_widget(top_spacer)

        # Поисковая строка
        self.search_card = MDCard(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(46),
            radius=[dp(24), dp(24), dp(24), dp(24)],
            md_bg_color=[0, 0, 0, 0],
            elevation=0,
            padding=[dp(0), dp(0), dp(0), dp(0)]
        )

        self.search_field = MDTextField(
            hint_text="Поиск исполнителей и песен",
            mode="filled",
            size_hint_x=0.99,
            font_size=dp(46),
            height=dp(48),
            radius=[dp(24), dp(24), dp(24), dp(24)],
            on_text_validate=self.do_search,
            theme_line_color="Custom",
            line_color_normal=[0, 0, 0, 0],
            line_color_focus=[0, 0, 0, 0],
            theme_bg_color="Custom",
            fill_color_normal=[0, 0, 0, 0],
            fill_color_focus=[0, 0, 0, 0],
            text_color_normal=[0, 0, 0, 0],  # Цвет введённого текста
            text_color_focus=[0, 0, 0, 0],
            hint_text_color=[0.5, 0.5, 0.5, 1]  # Серый цвет подсказки (50% серый)
        )

        # Кнопка очистки
        self.clear_search_btn = MDIconButton(
            icon="close-circle",
            size_hint=(None, None),
            size=(dp(32), dp(32)),
            theme_icon_color="Custom",
            icon_color=theme.TEXT_SECONDARY,
            on_release=self.clear_search,
            opacity=0,
            md_bg_color=[0, 0, 0, 0]
        )

        # Кнопка поиска
        self.search_btn = MDIconButton(
            icon="magnify",
            size_hint=(None, None),
            size=(dp(40), dp(40)),
            theme_icon_color="Custom",
            icon_color=theme.PRIMARY,
            on_release=self.do_search,
            md_bg_color=[0, 0, 0, 0]
        )

        self.search_card.add_widget(self.search_field)
        self.search_card.add_widget(self.clear_search_btn)
        self.search_card.add_widget(self.search_btn)
        main_layout.add_widget(self.search_card)

        # Клавиатура с буквами
        self.keyboard = AlphabetKeyboard(on_letter_press=self.on_letter_press)
        main_layout.add_widget(self.keyboard)

        # Контейнер для контента
        self.content_scroll = MDScrollView(
            size_hint=(1, 1),
            do_scroll_x=False
        )
        self.content_container = MDBoxLayout(
            orientation='vertical',
            spacing=dp(8),
            size_hint_y=None,
            adaptive_height=True,
            padding=[dp(8), dp(8), dp(8), dp(80)]
        )
        self.content_scroll.add_widget(self.content_container)
        main_layout.add_widget(self.content_scroll)

        scroll.add_widget(main_layout)
        self.add_widget(scroll)

        # Загружаем приветственный экран
        self.show_welcome_screen()

    def show_welcome_screen(self):
        """Показывает приветственный экран с предложением выбрать букву"""
        self.content_container.clear_widgets()
        self.current_song_card = None

        welcome_card = MDCard(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(240),
            padding=[dp(24), dp(24), dp(24), dp(24)],
            radius=[theme.CORNER_RADIUS_SMALL],
            md_bg_color=theme.SURFACE,
            elevation=2
        )

        icon_label = MDLabel(
            text="🎸",
            font_size=sp(56),
            halign="center",
            size_hint_y=None,
            height=dp(70)
        )

        title_label = MDLabel(
            text="Добро пожаловать!",
            font_size=sp(20),
            halign="center",
            size_hint_y=None,
            height=dp(40),
            theme_text_color="Custom",
            text_color=theme.TEXT_PRIMARY,
            bold=True
        )

        subtitle_label = MDLabel(
            text="Выберите букву алфавита выше,\nчтобы увидеть список исполнителей",
            font_size=sp(13),
            halign="center",
            theme_text_color="Custom",
            text_color=theme.TEXT_SECONDARY,
            size_hint_y=None,
            height=dp(60)
        )

        hint_label = MDLabel(
            text="👇 Нажмите на любую букву",
            font_size=sp(11),
            halign="center",
            theme_text_color="Custom",
            text_color=theme.PRIMARY,
            size_hint_y=None,
            height=dp(30)
        )

        welcome_card.add_widget(icon_label)
        welcome_card.add_widget(title_label)
        welcome_card.add_widget(subtitle_label)
        welcome_card.add_widget(hint_label)
        self.content_container.add_widget(welcome_card)

    def show_loading(self):
        """Показывает индикатор загрузки"""
        if self.is_loading:
            return

        self.is_loading = True
        self.content_container.clear_widgets()
        self.current_song_card = None
        self.loading_spinner = LoadingSpinner()
        self.content_container.add_widget(self.loading_spinner)
        self.loading_spinner.start_animation()

    def hide_loading(self):
        """Скрывает индикатор загрузки"""
        self.is_loading = False
        if self.loading_spinner:
            self.loading_spinner.stop_animation()
        self.content_container.clear_widgets()

    def on_letter_press(self, letter):
        """Обработчик нажатия на букву - загружаем исполнителей и их песни"""
        logger.info(f"Выбрана буква: {letter}")
        self.current_letter = letter
        self.search_mode = False
        self.clear_search_btn.opacity = 0
        self.search_field.text = ""
        self.close_song_card()
        self.load_artists_with_songs(letter)

    def load_artists_with_songs(self, letter):
        """Загружает исполнителей и их песни по букве"""
        self.show_loading()

        api.get_artists_by_letter(
            letter=letter,
            on_success=self.on_artists_loaded,
            on_failure=self.on_load_failed
        )

    def on_artists_loaded(self, artists):
        """Отображает список исполнителей с их песнями"""
        self.hide_loading()
        self.artists_data = artists

        if not artists:
            no_data_card = MDCard(
                orientation='vertical',
                size_hint=(1, None),
                height=dp(180),
                padding=[dp(24), dp(24), dp(24), dp(24)],
                radius=[theme.CORNER_RADIUS_SMALL],
                md_bg_color=theme.SURFACE,
                elevation=2
            )

            icon_label = MDLabel(
                text="😢",
                font_size=sp(48),
                halign="center",
                size_hint_y=None,
                height=dp(60)
            )

            text_label = MDLabel(
                text=f"Нет исполнителей на букву «{self.current_letter}»",
                halign="center",
                font_size=sp(14),
                theme_text_color="Custom",
                text_color=theme.TEXT_PRIMARY,
                size_hint_y=None,
                height=dp(40),
                bold=True
            )

            hint_label = MDLabel(
                text="Попробуйте выбрать другую букву",
                halign="center",
                font_size=sp(12),
                theme_text_color="Custom",
                text_color=theme.TEXT_SECONDARY,
                size_hint_y=None,
                height=dp(30)
            )

            no_data_card.add_widget(icon_label)
            no_data_card.add_widget(text_label)
            no_data_card.add_widget(hint_label)
            self.content_container.add_widget(no_data_card)
            return

        for artist_data in artists:
            artist_info = {
                'artist': artist_data.get('artist'),
                'songs_count': artist_data.get('songs_count', 0),
                'songs': artist_data.get('songs', [])
            }

            card = ArtistCard(
                artist_data=artist_info,
                on_song_click=self.on_song_selected
            )
            self.content_container.add_widget(card)

        logger.info(f"Загружено {len(artists)} исполнителей на букву {self.current_letter}")

    def on_song_selected(self, song):
        """Выбор песни - загружаем и показываем текст на этом же экране"""
        song_id = song.get('song_id')
        song_title = song.get('title', '')
        song_artist = song.get('artist', '')

        logger.info(f"🎵 Выбрана песня: {song_artist} - {song_title}, song_id: {song_id}")

        if not song_id:
            logger.error(f"Нет song_id для песни: {song}")
            notify.error("Ошибка: не удалось загрузить песню")
            return

        self.close_song_card()
        self.show_loading()

        api.get_tab(
            song_id=song_id,
            on_success=lambda data: self.on_song_text_loaded(data, song),
            on_failure=self.on_song_load_failed
        )

    def on_song_text_loaded(self, data, original_song):
        """Отображает текст песни в карточке поверх списка"""
        self.hide_loading()

        song_data = {
            'song_id': data.get('id'),
            'title': data.get('title', original_song.get('title', '')),
            'artist': data.get('artist', original_song.get('artist', '')),
            'content': data.get('content', 'Текст не загружен'),
            'tabs_count': original_song.get('tabs_count', 1),
            'likes': data.get('likes', 0),
            'views': data.get('views', 0)
        }

        self.current_song_card = SongTextCard(
            song_data=song_data,
            on_close=self.close_song_card
        )

        self.content_container.insert(0, self.current_song_card)
        Clock.schedule_once(lambda dt: self.scroll_to_card(), 0.1)

        logger.info(f"✅ Текст песни загружен: {song_data['artist']} - {song_data['title']}")

    def scroll_to_card(self):
        """Прокручивает к открытой карточке песни"""
        if self.current_song_card:
            self.content_scroll.scroll_to(self.current_song_card)

    def close_song_card(self):
        """Закрывает карточку с текстом песни"""
        if self.current_song_card and self.current_song_card.parent:
            self.content_container.remove_widget(self.current_song_card)
            self.current_song_card = None
            logger.info("Карточка песни закрыта")

    def on_song_load_failed(self, req, error):
        """Ошибка загрузки текста песни"""
        self.hide_loading()
        notify.error(f"Ошибка загрузки текста: {error}")
        logger.error(f"Ошибка загрузки текста: {error}")

    def do_search(self, instance):
        """Выполняет поиск"""
        query = self.search_field.text.strip()
        if len(query) < 2:
            notify.warning("Введите минимум 2 символа для поиска")
            return

        logger.info(f"🔍 Поиск: {query}")
        self.search_mode = True
        self.clear_search_btn.opacity = 1
        self.close_song_card()
        self.search_results(query)

    def clear_search(self, instance):
        """Очищает поиск и возвращается к алфавитному просмотру"""
        self.search_field.text = ""
        self.clear_search_btn.opacity = 0
        self.search_mode = False
        self.close_song_card()

        if self.current_letter:
            self.load_artists_with_songs(self.current_letter)
        else:
            self.show_welcome_screen()

    def search_results(self, query):
        """Выполняет поиск и отображает результаты"""
        self.show_loading()
        api.search_songs(
            query=query,
            search_type="general",
            limit=50,
            on_success=self.on_search_results,
            on_failure=self.on_load_failed
        )

    def on_search_results(self, results):
        """Отображает результаты поиска в виде карточек"""
        self.hide_loading()

        if not results:
            no_results_card = MDCard(
                orientation='vertical',
                size_hint=(1, None),
                height=dp(180),
                padding=[dp(24), dp(24), dp(24), dp(24)],
                radius=[theme.CORNER_RADIUS_SMALL],
                md_bg_color=theme.SURFACE,
                elevation=2
            )

            icon_label = MDLabel(
                text="🔍",
                font_size=sp(48),
                halign="center",
                size_hint_y=None,
                height=dp(60)
            )

            text_label = MDLabel(
                text="Ничего не найдено",
                halign="center",
                font_size=sp(14),
                theme_text_color="Custom",
                text_color=theme.TEXT_PRIMARY,
                size_hint_y=None,
                height=dp(40),
                bold=True
            )

            hint_label = MDLabel(
                text="Попробуйте изменить поисковый запрос",
                halign="center",
                font_size=sp(12),
                theme_text_color="Custom",
                text_color=theme.TEXT_SECONDARY,
                size_hint_y=None,
                height=dp(30)
            )

            no_results_card.add_widget(icon_label)
            no_results_card.add_widget(text_label)
            no_results_card.add_widget(hint_label)
            self.content_container.add_widget(no_results_card)
            return

        # Группируем результаты по исполнителям
        artists_dict = {}
        for song in results:
            artist = song.get('artist', '')
            if artist not in artists_dict:
                artists_dict[artist] = {
                    'artist': artist,
                    'songs_count': 0,
                    'songs': []
                }
            artists_dict[artist]['songs'].append(song)
            artists_dict[artist]['songs_count'] += 1

        # Отображаем сгруппированные результаты
        for artist_name, artist_data in sorted(artists_dict.items()):
            card = ArtistCard(
                artist_data=artist_data,
                on_song_click=self.on_song_selected
            )
            self.content_container.add_widget(card)

        logger.info(f"Найдено {len(results)} песен, сгруппировано в {len(artists_dict)} исполнителей")

    def on_load_failed(self, req, error):
        """Обработчик ошибки загрузки"""
        self.hide_loading()
        notify.error(f"Ошибка загрузки: {error}")
        logger.error(f"Ошибка загрузки: {error}")
        self.show_welcome_screen()