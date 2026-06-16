# screens/components/section_carousel.py
"""
Карусель разделов с пагинацией по 3 карточки
Плавный скролл с привязкой к карточкам
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


class SectionCardsContainer(MDBoxLayout):
    """
    Контейнер с карточками разделов для пагинации с шагом 1 карточка
    """

    CARDS_PER_PAGE = 3
    CARD_WIDTH = dp(100)
    CARD_HEIGHT = dp(120)
    CARD_SPACING = dp(12)

    def __init__(self, screen_manager, on_section_selected=None, **kwargs):
        super().__init__(**kwargs)
        self.sm = screen_manager
        self.on_section_selected = on_section_selected

        self.orientation = 'horizontal'
        self.size_hint = (None, None)
        self.spacing = self.CARD_SPACING
        self.padding = [0, dp(4), 0, dp(4)]

        # Все карточки
        self.all_cards = []
        self.current_start_index = 0
        self.total_cards = 0

        # Вычисляем фиксированную ширину для 3 карточек
        self.fixed_width = self.CARDS_PER_PAGE * self.CARD_WIDTH + (self.CARDS_PER_PAGE - 1) * self.CARD_SPACING
        self.width = self.fixed_width
        self.height = self.CARD_HEIGHT + dp(8)

        self._create_sections()

        logger.info(f'SectionCardsContainer создан, ширина={self.fixed_width}dp')

    def _create_sections(self):
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
            self.all_cards.append(card)

        self.total_cards = len(self.all_cards)
        self.current_start_index = 0
        self._update_display(animated=False)

    def _update_display(self, animated=True):
        self.clear_widgets()

        end_index = min(self.current_start_index + self.CARDS_PER_PAGE, self.total_cards)

        for i in range(self.current_start_index, end_index):
            self.add_widget(self.all_cards[i])

        visible_count = end_index - self.current_start_index
        for i in range(visible_count, self.CARDS_PER_PAGE):
            spacer = MDBoxLayout(
                size_hint=(None, None),
                width=self.CARD_WIDTH,
                height=self.CARD_HEIGHT,
                md_bg_color=[0, 0, 0, 0]
            )
            self.add_widget(spacer)

        logger.info(f"📏 Показаны карточки {self.current_start_index}-{end_index - 1} из {self.total_cards}")

    def _on_card_click(self, section_id):
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

    def next_page(self):
        if self.current_start_index + self.CARDS_PER_PAGE < self.total_cards:
            self.current_start_index += 1
            self._update_display(animated=True)
            return True
        return False

    def prev_page(self):
        if self.current_start_index > 0:
            self.current_start_index -= 1
            self._update_display(animated=True)
            return True
        return False

    def has_next(self):
        return self.current_start_index + self.CARDS_PER_PAGE < self.total_cards

    def has_prev(self):
        return self.current_start_index > 0

    def get_current_start(self):
        return self.current_start_index


class SectionCarousel(MDBoxLayout):
    """
    Карусель разделов с плавным скроллом
    """

    def __init__(self, screen_manager, on_section_selected=None, **kwargs):
        super().__init__(**kwargs)
        self.sm = screen_manager
        self.on_section_selected = on_section_selected

        self.orientation = 'vertical'
        self.size_hint = (1, None)
        self.height = dp(185)
        self.spacing = dp(4)
        self.padding = [dp(4), dp(4), dp(4), dp(4)]

        self.cards_container = None
        self._snap_timer = None
        self._is_snapping = False

        self._build_ui()
        self._setup_scroll()

        logger.info('SectionCarousel создан')

    def _build_ui(self):
        """Строит UI"""

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

        # ============ КАРТОЧКИ ============
        self.cards_wrapper = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(140),
            md_bg_color=[0, 0, 0, 0],
            padding=[0, dp(4), 0, dp(4)]
        )

        # Контейнер с фиксированной шириной для 3 карточек
        self.cards_container = SectionCardsContainer(
            screen_manager=self.sm,
            on_section_selected=self.on_section_selected
        )

        # Пустые места для центрирования
        self.left_spacer = Widget(size_hint_x=1)
        self.right_spacer = Widget(size_hint_x=1)

        self.cards_wrapper.add_widget(self.left_spacer)
        self.cards_wrapper.add_widget(self.cards_container)
        self.cards_wrapper.add_widget(self.right_spacer)

        self.add_widget(self.cards_wrapper)

        # Обновляем состояние
        Clock.schedule_once(self._update_state, 0.3)

    def _setup_scroll(self):
        """Настраивает обработку скролла"""
        self.bind(size=self._on_size)

    def _on_size(self, *args):
        """Обновляет при изменении размера"""
        Clock.schedule_once(self._update_state, 0.1)

    def _update_state(self, *args):
        """Обновляет состояние"""
        if self.cards_container:
            self._update_arrows()

    def _on_scroll_stop(self, instance, touch=None):
        """При остановке скролла - привязываем к ближайшей карточке"""
        if not self.cards_container:
            return

        if self._is_snapping:
            return

        if self._snap_timer:
            self._snap_timer.cancel()
            self._snap_timer = None

        self._snap_timer = Clock.schedule_once(self._snap_to_nearest, 0.1)

    def _snap_to_nearest(self, dt):
        """Привязывает к ближайшей карточке"""
        if not self.cards_container:
            return

        if self._is_snapping:
            return

        # Получаем текущий индекс
        current_index = self.cards_container.get_current_start()
        total_cards = self.cards_container.total_cards
        cards_per_page = self.cards_container.CARDS_PER_PAGE

        if total_cards <= cards_per_page:
            self._snap_timer = None
            return

        # Проверяем, нужно ли привязаться
        # Этот метод будет вызван извне при остановке скролла
        self._snap_timer = None

    def _update_arrows(self, *args):
        """Обновляет состояние - заглушка для совместимости"""
        pass

    def on_size(self, *args):
        """Обновляет при изменении размера"""
        Clock.schedule_once(self._update_state, 0.1)