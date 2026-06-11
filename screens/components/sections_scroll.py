# screens/components/sections_scroll.py
"""
Горизонтальный скролл с карточками разделов (аналог парсеров в админке)
"""
from kivy.clock import Clock
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp, sp
from kivy.animation import Animation
from kivy.core.image import Image as CoreImage
from kivy.uix.image import Image
from io import BytesIO

from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.behaviors import CircularRippleBehavior

from config.theme import theme
from config.logger_config import get_logger

logger = get_logger('UI')

try:
    from data import load_asset_as_bytes

    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False


    def load_asset_as_bytes(name):
        return None


class SectionCard(CircularRippleBehavior, MDCard):
    """
    Карточка раздела с иконкой из ассетов
    """

    # Цвета для разных разделов (основной и hover)
    SECTION_COLORS = {
        'songs': ('#E53935', '#C62828'),  # Красный
        'chords': ('#43A047', '#2E7D32'),  # Зеленый
        'tuner': ('#1E88E5', '#1565C0'),  # Синий
        'dictionary': ('#FB8C00', '#EF6C00'),  # Оранжевый
        'favorites': ('#8E24AA', '#6A1B9A'),  # Фиолетовый
    }

    def __init__(self, section_id, title, icon_asset, on_click=None, **kwargs):
        super().__init__(**kwargs)
        self.section_id = section_id
        self.title = title
        self.icon_asset = icon_asset
        self.on_click_callback = on_click

        colors = self.SECTION_COLORS.get(section_id, ('#757575', '#616161'))
        self.bg_color = colors[0]
        self.hover_color = colors[1]

        self.orientation = 'vertical'
        self.size_hint = (None, None)
        self.width = dp(100)
        self.height = dp(120)
        self.radius = [dp(16)]
        self.elevation = 2
        self.ripple_scale = 0.95

        # Фон
        self.md_bg_color = self._hex_to_rgba(self.bg_color, 0.85)

        # Контент
        content = MDBoxLayout(
            orientation='vertical',
            spacing=dp(8),
            padding=[dp(10), dp(12), dp(10), dp(12)],
            size_hint=(1, 1),
            md_bg_color=[0, 0, 0, 0]
        )

        # Иконка из ассета
        self.icon_image = Image(
            size_hint=(None, None),
            size=(dp(48), dp(48)),
            pos_hint={'center_x': 0.5},
            allow_stretch=True,
            keep_ratio=True
        )
        self._load_icon()

        # Название
        self.title_label = MDLabel(
            text=title,
            font_size=sp(12),
            halign="center",
            bold=True,
            size_hint_y=None,
            height=dp(30),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.95],
            shorten=True,
            shorten_from="right"
        )

        content.add_widget(self.icon_image)
        content.add_widget(self.title_label)

        self.add_widget(content)
        self.bind(on_release=self._on_click)

        # Анимация при наведении
        self.bind(on_enter=self._on_enter, on_leave=self._on_leave)

    def _load_icon(self):
        """Загружает иконку из ассета"""
        if HAS_ASSETS and self.icon_asset:
            try:
                icon_data = load_asset_as_bytes(self.icon_asset)
                if icon_data:
                    img = CoreImage(BytesIO(icon_data), ext="png")
                    self.icon_image.texture = img.texture
                    return
            except Exception as e:
                logger.error(f"Ошибка загрузки иконки {self.icon_asset}: {e}")

        # Заглушка для иконки
        self.icon_image.text = "🎸"
        self.icon_image.color = [1, 1, 1, 0.8]

    def _hex_to_rgba(self, hex_color, alpha=1.0):
        hex_color = hex_color.lstrip('#')
        return [
            int(hex_color[i:i + 2], 16) / 255.0
            for i in (0, 2, 4)
        ] + [alpha]

    def _on_enter(self, *args):
        Animation(elevation=6, duration=0.2).start(self)
        self.md_bg_color = self._hex_to_rgba(self.hover_color, 1.0)

    def _on_leave(self, *args):
        Animation(elevation=2, duration=0.2).start(self)
        self.md_bg_color = self._hex_to_rgba(self.bg_color, 0.85)

    def _on_click(self, instance):
        if self.on_click_callback:
            Animation(opacity=0.7, duration=0.05).start(self)
            Clock.schedule_once(lambda dt: Animation(opacity=1, duration=0.1).start(self), 0.05)
            self.on_click_callback(self.section_id)


class SectionsScroll(ScrollView):
    """
    Горизонтальный скролл с карточками разделов
    """

    def __init__(self, screen_manager, on_section_selected=None, **kwargs):
        super().__init__(**kwargs)
        self.sm = screen_manager
        self.on_section_selected = on_section_selected

        self.do_scroll_x = True
        self.do_scroll_y = False
        self.bar_width = dp(0)  # Скрываем скролл-бар
        self.bar_color = [1, 1, 1, 0]
        self.bar_inactive_color = [1, 1, 1, 0]
        self.scroll_type = ['content']

        self.size_hint = (1, None)
        self.height = dp(140)

        # Контейнер для карточек
        self.sections_layout = MDBoxLayout(
            orientation='horizontal',
            spacing=dp(12),
            size_hint_x=None,
            padding=[dp(16), dp(8), dp(16), dp(8)]
        )
        self.sections_layout.bind(minimum_width=self.sections_layout.setter('width'))

        # Создаем карточки разделов
        self._create_sections()

        self.add_widget(self.sections_layout)
        logger.info('SectionsScroll создан')

    def _create_sections(self):
        """Создает все карточки разделов"""

        # Список разделов: (id, название, иконка-ассет)
        sections = [
            ('songs', 'Песни', 'songs_png'),
            ('chords', 'Аккорды', 'chords_png'),
            ('tuner', 'Тюнер', 'tuner_png'),
            ('dictionary', 'Словарь', 'dictionary_png'),
            ('favorites', 'Избранное', 'favorites_png'),
        ]

        for section_id, title, icon_asset in sections:
            card = SectionCard(
                section_id=section_id,
                title=title,
                icon_asset=icon_asset,
                on_click=self._on_card_click
            )
            self.sections_layout.add_widget(card)

    def _on_card_click(self, section_id):
        """Обработчик клика по карточке"""
        logger.info(f'Выбран раздел: {section_id}')

        # Маппинг ID раздела на имя экрана
        screen_map = {
            'songs': 'songs',
            'chords': 'chords',
            'tuner': 'tuner',
            'dictionary': 'dictionary',
            'favorites': 'favorites',
        }

        screen_name = screen_map.get(section_id)

        if self.on_section_selected:
            self.on_section_selected(screen_name)
        elif self.sm and screen_name:
            if self.sm.has_screen(screen_name):
                self.sm.current = screen_name
            else:
                logger.error(f"Экран {screen_name} не найден")