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

    # Удаляем HTML теги
    text = re.sub(r'<[^>]+>', '', text)

    # Восстанавливаем HTML сущности
    html_entities = {
        '&amp;': '&',
        '&lt;': '<',
        '&gt;': '>',
        '&quot;': '"',
        '&apos;': "'",
        '&nbsp;': ' ',
        '&#39;': "'",
        '&#34;': '"',
        '&#38;': '&',
        '&#60;': '<',
        '&#62;': '>',
        '&#171;': '«',
        '&#187;': '»',
        '&#169;': '©',
        '&#174;': '®',
        '&#8364;': '€',
        '&#8470;': '№',
        '&#8211;': '–',
        '&#8212;': '—',
        '&#8216;': "'",
        '&#8217;': "'",
        '&#8220;': '"',
        '&#8221;': '"',
        '&#8230;': '…',
    }
    for entity, char in html_entities.items():
        text = text.replace(entity, char)

    # Разбиваем на строки
    lines = text.split('\n')
    cleaned_lines = []

    for i, line in enumerate(lines):
        # Пропускаем первые 4 строки (как было раньше)
        if i < 4:
            continue

        # Пропускаем строки с "источник:" или "source:"
        if 'источник:' in line.lower() or 'source:' in line.lower():
            continue

        cleaned_lines.append(line)

    # Убираем пустые строки в конце
    while cleaned_lines and not cleaned_lines[-1].strip():
        cleaned_lines.pop()

    result = '\n'.join(cleaned_lines)

    # Если после очистки ничего не осталось, возвращаем оригинал без первых 4 строк
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


class SongDetailScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'song_detail'
        self.song_id = None
        self.current_tab_id = None
        self.is_liked = False
        self.is_favorite = False
        self.is_loading = False
        self.loading_spinner = None
        self.bg_image = None
        self.previous_screen = 'artist_songs'
        self.current_tonality = 0
        self.current_font_size = 14
        self.tabs = []
        self.current_tab_index = 0

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
        """Инициализация пользовательского интерфейса"""
        # Основной контейнер
        main_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            padding=[0, 0, 0, 0]
        )

        # Верхний отступ под статус-бар и TopNav
        top_padding = layout_config.get_top_padding()
        main_container.add_widget(Widget(size_hint_y=None, height=top_padding))

        # Карточка с текстом - с отступами по бокам
        card_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            padding=[8, 0, 8, 0]  # Уменьшил боковые отступы
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

        # ============ ВЕРХНЕЕ МЕНЮ ============
        self._create_top_menu()
        self.song_card.add_widget(self.top_menu)

        # Разделитель
        top_separator = MDBoxLayout(
            size_hint=(1, None),
            height=1,
            md_bg_color=[0.85, 0.85, 0.85, 0.8]
        )
        self.song_card.add_widget(top_separator)

        # ============ КОНТЕЙНЕР ДЛЯ ТЕКСТА ============
        self.content_scroll = MDScrollView(
            size_hint=(1, 1),
            do_scroll_x=False,
            bar_width=3,
            bar_color=[0.5, 0.5, 0.5, 0.2],
            bar_inactive_color=[0.5, 0.5, 0.5, 0.1]
        )

        # Контент внутри скролла
        scroll_content = MDBoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=4,
            padding=[12, 8, 12, 8],
            adaptive_height=True
        )

        # Текст песни
        self.content_label = MDLabel(
            text="",
            font_size=self.current_font_size,
            size_hint_y=None,
            theme_text_color="Custom",
            text_color=[0, 0, 0, 0.85],
            markup=True,
            valign="top",
            line_height=1.4
        )
        self.content_label.bind(texture_size=self._update_content_height)
        scroll_content.add_widget(self.content_label)

        # Статистика в конце текста
        self._create_stats_line()
        scroll_content.add_widget(self.stats_line)

        self.content_scroll.add_widget(scroll_content)
        self.song_card.add_widget(self.content_scroll)

        # ============ НИЖНЕЕ МЕНЮ ============
        self._create_bottom_menu()
        self.song_card.add_widget(self.bottom_menu)

        card_container.add_widget(self.song_card)
        main_container.add_widget(card_container)

        # Нижний отступ для BottomNav
        bottom_nav_height = dp(60)
        nav_bar_height = get_navigation_bar_height()
        total_bottom = bottom_nav_height + nav_bar_height + dp(16)
        main_container.add_widget(Widget(size_hint_y=None, height=total_bottom))

        self.add_widget(main_container)

    def _create_top_menu(self):
        """Создаёт верхнее меню: исполнитель крупно, название мелко, иконки справа"""
        self.top_menu = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(60),
            padding=[4, 4, 0, 4],  # Убран правый отступ
            spacing=2,
            md_bg_color=[1, 1, 1, 0]
        )

        # Первая строка
        row1 = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(30),
            spacing=2
        )

        # Иконка песни
        self.song_icon = Image(
            size_hint=(None, None),
            size=(dp(16), dp(16)),
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

        # Исполнитель (уменьшаем шрифт чтобы освободить место)
        self.artist_label = MDLabel(
            text="",
            font_size=sp(11),
            size_hint_x=1,
            theme_text_color="Custom",
            text_color=[0, 0, 0, 0.85],
            bold=True,
            valign="middle",
            shorten=True,
            shorten_from="right"
        )

        # Блок иконок - с минимальными отступами
        actions_box = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, 1),
            width=dp(180),  # 4 иконки по 20dp
            spacing=dp(0),
            pos_hint={'center_y': 0.5}
        )

        # Избранное - уменьшен размер и отступы
        self.favorite_btn = MDIconButton(
            icon="star-outline",
            size_hint=(1, 1),
            size=(dp(15), dp(15)),
            theme_icon_color="Custom",
            icon_color=[0.9, 0.7, 0.2, 0.9],
            md_bg_color=[0, 0, 0, 0],
            ripple_scale=0,
            padding=0,  # Убираем внутренние отступы
            on_release=self.toggle_favorite
        )

        # Лайк
        self.like_btn = MDIconButton(
            icon="heart-outline",
            size_hint=(1, 1),
            size=(dp(15), dp(15)),
            theme_icon_color="Custom",
            icon_color=[0.8, 0.3, 0.3, 0.9],
            md_bg_color=[0, 0, 0, 0],
            ripple_scale=0,
            padding=0,  # Убираем внутренние отступы
            on_release=self.toggle_like
        )

        # Минус
        self.zoom_out_btn = MDIconButton(
            icon="minus-circle-outline",
            size_hint=(1, 1),
            size=(dp(15), dp(15)),
            theme_icon_color="Custom",
            icon_color=[0.4, 0.6, 0.4, 0.8],
            md_bg_color=[0, 0, 0, 0],
            ripple_scale=0,
            padding=0,  # Убираем внутренние отступы
            on_release=self.zoom_out
        )

        # Плюс
        self.zoom_in_btn = MDIconButton(
            icon="plus-circle-outline",
            size_hint=(1, 1),
            size=(dp(15), dp(15)),
            theme_icon_color="Custom",
            icon_color=[0.4, 0.6, 0.4, 0.8],
            md_bg_color=[0, 0, 0, 0],
            ripple_scale=0,
            padding=0,  # Убираем внутренние отступы
            on_release=self.zoom_in
        )

        actions_box.add_widget(self.favorite_btn)
        actions_box.add_widget(self.like_btn)
        actions_box.add_widget(self.zoom_out_btn)
        actions_box.add_widget(self.zoom_in_btn)

        row1.add_widget(self.song_icon)
        row1.add_widget(self.artist_label)
        row1.add_widget(actions_box)

        # Вторая строка
        row2 = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(20),
            padding=[22, 0, 0, 0]
        )

        self.song_title_label = MDLabel(
            text="",
            font_size=sp(10),
            size_hint_x=1,
            theme_text_color="Custom",
            text_color=[0.5, 0.5, 0.5, 0.8],
            valign="middle",
            shorten=True,
            shorten_from="right"
        )

        row2.add_widget(self.song_title_label)

        self.top_menu.add_widget(row1)
        self.top_menu.add_widget(row2)

    def _create_stats_line(self):
        """Создаёт строку статистики - очень мелко, в правом углу"""
        self.stats_line = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(18),
            spacing=dp(4),
            padding=[0, 0, dp(6), 0]
        )

        # Spacer слева
        spacer = Widget(size_hint_x=1)
        self.stats_line.add_widget(spacer)

        # Лайки
        like_icon = MDIconButton(
            icon="heart",
            size_hint=(None, None),
            size=(dp(12), dp(12)),
            theme_icon_color="Custom",
            icon_color=[0.9, 0.3, 0.3, 0.7],
            disabled=True,
            md_bg_color=[0, 0, 0, 0],
            _no_ripple_effect=True,
            pos_hint={'center_y': 0.5}
        )

        self.like_count = MDLabel(
            text="0",
            font_size=sp(8),
            size_hint_x=None,
            width=dp(22),
            halign="left",
            valign="middle",
            theme_text_color="Custom",
            text_color=[0.9, 0.3, 0.3, 0.8],
            bold=True
        )

        # Избранное
        fav_icon = MDIconButton(
            icon="star",
            size_hint=(None, None),
            size=(dp(12), dp(12)),
            theme_icon_color="Custom",
            icon_color=[1, 0.75, 0.1, 0.7],
            disabled=True,
            md_bg_color=[0, 0, 0, 0],
            _no_ripple_effect=True,
            pos_hint={'center_y': 0.5}
        )

        self.favorite_count = MDLabel(
            text="0",
            font_size=sp(8),
            size_hint_x=None,
            width=dp(22),
            halign="left",
            valign="middle",
            theme_text_color="Custom",
            text_color=[1, 0.75, 0.1, 0.8],
            bold=True
        )

        # Просмотры
        views_icon = MDIconButton(
            icon="eye-outline",
            size_hint=(None, None),
            size=(dp(12), dp(12)),
            theme_icon_color="Custom",
            icon_color=[0.5, 0.5, 0.5, 0.6],
            disabled=True,
            md_bg_color=[0, 0, 0, 0],
            _no_ripple_effect=True,
            pos_hint={'center_y': 0.5}
        )

        self.views_count = MDLabel(
            text="0",
            font_size=sp(8),
            size_hint_x=None,
            width=dp(26),
            halign="left",
            valign="middle",
            theme_text_color="Custom",
            text_color=[0.5, 0.5, 0.5, 0.7]
        )

        self.stats_line.add_widget(like_icon)
        self.stats_line.add_widget(self.like_count)
        self.stats_line.add_widget(fav_icon)
        self.stats_line.add_widget(self.favorite_count)
        self.stats_line.add_widget(views_icon)
        self.stats_line.add_widget(self.views_count)

    def _create_bottom_menu(self):
        """Создаёт нижнее меню: тональность + переключение подборов"""
        self.bottom_menu = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=44,
            spacing=4,
            padding=[10, 4, 10, 4],
            md_bg_color=[1, 1, 1, 0]
        )

        # Левая часть: тональность (оптимизировано)
        tonality_box = MDBoxLayout(
            orientation='horizontal',
            size_hint_x=0.5,  # Занимает половину ширины
            spacing=dp(0),  # Минимальный отступ
            pos_hint={'center_y': 0.5}
        )

        tonality_label = MDLabel(
            text="Тональность",  # Сокращено для экономии места
            font_size=sp(10),
            size_hint=(1, 1),
            width=dp(66),  # Фиксированная ширина под "Тон"
            theme_text_color="Custom",
            text_color=[0, 0, 0, 0.6],
            valign="middle"
        )

        self.minus_ton_btn = MDIconButton(
            icon="minus",
            size_hint=(None, None),
            size=(dp(24), dp(24)),  # Чуть меньше
            theme_icon_color="Custom",
            icon_color=[0.46, 0.70, 0.71, 0.8],
            md_bg_color=[0, 0, 0, 0],
            ripple_scale=0,
            padding=0,  # Убираем внутренние отступы
            on_release=self.decrease_tonality
        )

        self.tonality_value = MDLabel(
            text="0",
            font_size=sp(11),
            size_hint=(None, None),
            width=dp(20),  # Узко под число
            theme_text_color="Custom",
            text_color=[0.46, 0.70, 0.71, 1],
            bold=True,
            valign="middle",
            halign="center"
        )

        self.plus_ton_btn = MDIconButton(
            icon="plus",
            size_hint=(None, None),
            size=(dp(24), dp(24)),
            theme_icon_color="Custom",
            icon_color=[0.46, 0.70, 0.71, 0.8],
            md_bg_color=[0, 0, 0, 0],
            ripple_scale=0,
            padding=0,
            on_release=self.increase_tonality
        )

        tonality_box.add_widget(tonality_label)
        tonality_box.add_widget(self.minus_ton_btn)
        tonality_box.add_widget(self.tonality_value)
        tonality_box.add_widget(self.plus_ton_btn)


        # Правая часть: переключение подборов
        tabs_box = MDBoxLayout(
            orientation='horizontal',
            size_hint_x=0.5,
            spacing=2,
            pos_hint={'center_y': 0.5}
        )

        self.prev_tab_btn = MDIconButton(
            icon="chevron-up",
            size_hint=(None, None),
            size=(10, 10),
            theme_icon_color="Custom",
            icon_color=[0.46, 0.70, 0.71, 0.8],
            md_bg_color=[0, 0, 0, 0],
            on_release=self.prev_tab
        )

        self.tab_label = MDLabel(
            text="Подбор",
            font_size=10,
            size_hint=(None, None),
            width=48,
            theme_text_color="Custom",
            text_color=[0, 0, 0, 0.7],
            valign="middle",
            halign="center",
            bold=True
        )

        self.next_tab_btn = MDIconButton(
            icon="chevron-down",
            size_hint=(None, None),
            size=(10, 10),
            theme_icon_color="Custom",
            icon_color=[0.46, 0.70, 0.71, 0.8],
            md_bg_color=[0, 0, 0, 0],
            on_release=self.next_tab
        )

        tabs_box.add_widget(Widget(size_hint_x=1))
        tabs_box.add_widget(self.prev_tab_btn)
        tabs_box.add_widget(self.tab_label)
        tabs_box.add_widget(self.next_tab_btn)

        self.bottom_menu.add_widget(tonality_box)
        self.bottom_menu.add_widget(tabs_box)

    def _update_tab_display(self):
        """Обновляет отображение информации о подборе"""
        if self.tabs and len(self.tabs) > 1:
            self.tab_label.text = f"{self.current_tab_index + 1}/{len(self.tabs)}"
            self.prev_tab_btn.disabled = False
            self.next_tab_btn.disabled = False
        elif self.tabs and len(self.tabs) == 1:
            self.tab_label.text = "Подбор"
            self.prev_tab_btn.disabled = True
            self.next_tab_btn.disabled = True
        else:
            self.tab_label.text = "—"
            self.prev_tab_btn.disabled = True
            self.next_tab_btn.disabled = True

    def prev_tab(self, instance):
        if self.tabs and len(self.tabs) > 1:
            self.current_tab_index = (self.current_tab_index - 1) % len(self.tabs)
            self._load_current_tab()

    def next_tab(self, instance):
        if self.tabs and len(self.tabs) > 1:
            self.current_tab_index = (self.current_tab_index + 1) % len(self.tabs)
            self._load_current_tab()

    def _load_current_tab(self):
        """Загружает текущий подбор"""
        if self.tabs and self.current_tab_index < len(self.tabs):
            tab = self.tabs[self.current_tab_index]
            raw_content = tab.get('content', 'Текст не загружен')
            cleaned = clean_text(raw_content)
            self.content_label.text = cleaned if cleaned else "Текст не загружен"
            self._update_content_height()
            self._update_tab_display()
            Clock.schedule_once(lambda dt: setattr(self.content_scroll, 'scroll_y', 1), 0.1)

    def _update_content_height(self, *args):
        """Обновляет высоту контента с учётом статистики"""
        if not self.content_label.texture:
            Clock.schedule_once(lambda dt: self._update_content_height(), 0.05)
            return

        text_height = self.content_label.texture_size[1]
        stats_height = dp(26)
        self.content_label.height = max(dp(50), text_height + dp(8))

        if self.content_label.parent:
            self.content_label.parent.height = text_height + stats_height + dp(12)

    def zoom_in(self, instance):
        if self.current_font_size < 22:
            self.current_font_size += 2
            self.content_label.font_size = self.current_font_size
            self._update_content_height()

    def zoom_out(self, instance):
        if self.current_font_size > 10:
            self.current_font_size -= 2
            self.content_label.font_size = self.current_font_size
            self._update_content_height()

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
        self.artist = data.get('artist') or 'Неизвестный'
        self.title = data.get('title') or 'Без названия'

        self.tabs = data.get('tabs', [])
        if not self.tabs and data.get('content'):
            self.tabs = [{'content': data.get('content', '')}]

        self.current_tab_index = 0

        # Заполняем верхнее меню
        self.artist_label.text = self.artist.upper()
        self.song_title_label.text = self.title

        if self.tabs:
            raw_content = self.tabs[0].get('content', 'Текст не загружен')
            cleaned = clean_text(raw_content)
            self.content_label.text = cleaned if cleaned else "Текст не загружен"
            self._update_content_height()

        likes = data.get('likes', 0)
        favorites = data.get('favorites_count', 0)
        views = data.get('views', 0)

        self.like_count.text = str(likes)
        self.favorite_count.text = str(favorites)
        self.views_count.text = str(views) if views < 1000 else f"{views / 1000:.1f}K"

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
            new_count = result.get('total_likes', 0)
            self.like_count.text = str(new_count)
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
                current = int(self.favorite_count.text)
                self.favorite_count.text = str(max(0, current - 1))
                notify.success("Удалено")
                self._refresh_favorites_screen()

            def on_failure(req, error):
                notify.error("Ошибка")

            api.remove_from_favorites(song_id=self.song_id, on_success=on_success, on_failure=on_failure)
        else:
            def on_success(result):
                self.is_favorite = True
                self.favorite_btn.icon = "star"
                current = int(self.favorite_count.text)
                self.favorite_count.text = str(current + 1)
                notify.success("Добавлено")
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

    def increase_tonality(self, instance):
        if self.current_tonality < 7:
            self.current_tonality += 1
            self.tonality_value.text = str(self.current_tonality)

    def decrease_tonality(self, instance):
        if self.current_tonality > -7:
            self.current_tonality -= 1
            self.tonality_value.text = str(self.current_tonality)

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