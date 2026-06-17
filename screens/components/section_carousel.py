# screens/components/section_carousel.py
"""
Карусель разделов с горизонтальным скроллом
"""
from kivy.metrics import dp, sp
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.core.window import Window
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.core.image import Image as CoreImage
from kivy.uix.image import Image
from io import BytesIO

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDIconButton
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
    """Карточка раздела с иконкой из ассетов"""

    SECTION_COLORS = {
        'songs': ('#E53935', '#C62828'),
        'chords': ('#43A047', '#2E7D32'),
        'tuner': ('#1E88E5', '#1565C0'),
        'dictionary': ('#FB8C00', '#EF6C00'),
        'favorites': ('#8E24AA', '#6A1B9A'),
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

        self.md_bg_color = self._hex_to_rgba(self.bg_color, 0.85)

        content = MDBoxLayout(
            orientation='vertical',
            spacing=dp(8),
            padding=[dp(10), dp(12), dp(10), dp(12)],
            size_hint=(1, 1),
            md_bg_color=[0, 0, 0, 0]
        )

        self.icon_image = Image(
            size_hint=(None, None),
            size=(dp(48), dp(48)),
            pos_hint={'center_x': 0.5},
            allow_stretch=True,
            keep_ratio=True
        )
        self._load_icon()

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
        self.bind(on_enter=self._on_enter, on_leave=self._on_leave)

    def _load_icon(self):
        if HAS_ASSETS and self.icon_asset:
            try:
                icon_data = load_asset_as_bytes(self.icon_asset)
                if icon_data:
                    img = CoreImage(BytesIO(icon_data), ext="png")
                    self.icon_image.texture = img.texture
                    return
            except Exception as e:
                logger.error(f"Ошибка загрузки иконки {self.icon_asset}: {e}")
        self.icon_image.text = "🎸"
        self.icon_image.color = [1, 1, 1, 0.8]

    def _hex_to_rgba(self, hex_color, alpha=1.0):
        hex_color = hex_color.lstrip('#')
        return [int(hex_color[i:i + 2], 16) / 255.0 for i in (0, 2, 4)] + [alpha]

    def _on_enter(self, *args):
        self.elevation = 0
        self.md_bg_color = self._hex_to_rgba(self.bg_color, 0.92)

    def _on_leave(self, *args):
        self.elevation = 2
        self.md_bg_color = self._hex_to_rgba(self.bg_color, 0.85)

    def _on_click(self, instance):
        if self.on_click_callback:
            Animation(opacity=0.8, duration=0.05).start(self)
            Clock.schedule_once(lambda dt: Animation(opacity=1, duration=0.1).start(self), 0.05)
            self.on_click_callback(self.section_id)


class SectionCarousel(MDBoxLayout):
    """
    Карусель разделов с горизонтальным скроллом
    """

    CARD_WIDTH = dp(100)
    CARD_HEIGHT = dp(120)
    CARD_SPACING = dp(12)
    LEFT_PADDING = dp(8)

    def __init__(self, screen_manager, on_section_selected=None, **kwargs):
        super().__init__(**kwargs)
        self.sm = screen_manager
        self.on_section_selected = on_section_selected

        self.orientation = 'vertical'
        self.size_hint = (1, None)
        self.height = dp(185)
        self.spacing = dp(4)
        self.padding = [dp(4), dp(4), dp(4), dp(4)]

        self.cards_scroll = None
        self.cards_box = None

        self._build_ui()

        logger.info('SectionCarousel создан')

    def _build_ui(self):
        """Строит UI с горизонтальным ScrollView"""

        # ============ ЗАГОЛОВОК ============
        self.header = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(36),
            md_bg_color=[0, 0, 0, 0],
            padding=[dp(4), dp(0), dp(4), dp(0)]
        )

        self.title_label = MDLabel(
            text="РАЗДЕЛЫ",
            font_size=sp(18),
            halign="center",
            valign="middle",
            size_hint_x=1,
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.9],
            bold=True,
            shorten=True
        )

        self.header.add_widget(self.title_label)
        self.add_widget(self.header)

        # ============ ГОРИЗОНТАЛЬНЫЙ СКРОЛЛ ============
        self.cards_scroll = ScrollView(
            size_hint=(1, None),
            height=dp(140),
            bar_width=0,
            bar_color=[0, 0, 0, 0],
            bar_inactive_color=[0, 0, 0, 0],
            scroll_type=['content'],
            effect_cls='ScrollEffect',
            do_scroll_x=True,
            do_scroll_y=False,
            always_overscroll=False,
        )

        # Контейнер с карточками
        self.cards_box = MDBoxLayout(
            orientation='horizontal',
            size_hint=(None, None),
            height=dp(128),
            spacing=self.CARD_SPACING,
            padding=[self.LEFT_PADDING, dp(4), 0, dp(4)],
            md_bg_color=[0, 0, 0, 0]
        )

        # Создаем карточки
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
            self.cards_box.add_widget(card)

        # Рассчитываем ширину контейнера
        total_cards = len(sections)
        cards_width = (
            total_cards * self.CARD_WIDTH
            + (total_cards - 1) * self.CARD_SPACING
            + self.LEFT_PADDING
        )
        self.cards_box.width = cards_width

        logger.info(f'📏 Ширина cards_box: {cards_width}dp, карточек: {total_cards}')

        self.cards_scroll.add_widget(self.cards_box)
        self.add_widget(self.cards_scroll)

    def _on_card_click(self, section_id):
        """Обработчик клика по карточке"""
        logger.info(f'Выбран раздел: {section_id}')

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

    def on_size(self, *args):
        """При изменении размера обновляем скролл"""
        if hasattr(self, 'cards_scroll') and self.cards_scroll:
            self.cards_scroll._update_effect_bounds()