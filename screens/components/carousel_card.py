# screens/components/carousel_card.py
"""
Карточка для карусели главного экрана - увеличенный шрифт подписи
"""
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.metrics import dp, sp
from kivy.core.image import Image as CoreImage
from kivy.animation import Animation
from io import BytesIO

from config.theme import theme
from config.carousel_config import CarouselConfig
from config.logger_config import get_logger

logger = get_logger('UI')

try:
    from data import load_asset_as_bytes
    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False
    def load_asset_as_bytes(name):
        return None


class CarouselCard(ButtonBehavior, BoxLayout):
    """Карточка для карусели с увеличенным шрифтом"""

    def __init__(self, icon_asset, title, screen_name, on_click_callback=None, **kwargs):
        super().__init__(**kwargs)
        self.icon_asset = icon_asset
        self.title = title
        self.screen_name = screen_name
        self.on_click_callback = on_click_callback

        self.orientation = 'vertical'
        self.size_hint = (None, None)
        self.size = (dp(CarouselConfig.CAROUSEL_WIDTH), dp(CarouselConfig.CAROUSEL_HEIGHT))
        self.padding = [dp(12), dp(12), dp(12), dp(12)]
        self.spacing = dp(4)  # Уменьшен отступ между иконкой и текстом (было 8)

        # Делаем фон полностью прозрачным
        self.background_color = [0, 0, 0, 0]
        self.background_normal = ''

        # Контейнер для иконки
        self.icon_container = BoxLayout(
            size_hint=(1, CarouselConfig.ICON_CONTAINER_HEIGHT),
            orientation='vertical'
        )

        # Иконка
        self.icon_image = Image(
            size_hint=(CarouselConfig.ICON_SIZE, CarouselConfig.ICON_SIZE),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            allow_stretch=True,
            keep_ratio=True
        )

        # Название - увеличенный шрифт, ближе к иконке
        self.title_label = Label(
            text=title,
            font_size=sp(16),  # Увеличен с 14 до 16
            size_hint=(1, 1 - CarouselConfig.ICON_CONTAINER_HEIGHT),
            color=CarouselConfig.TEXT_COLOR,
            bold=True,
            halign='center',
            valign='top'  # Выравнивание по верху, чтобы быть ближе к иконке
        )

        self.icon_container.add_widget(self.icon_image)
        self.add_widget(self.icon_container)
        self.add_widget(self.title_label)

        self.bind(on_release=self._on_press)
        self._load_icon()

        # Анимация появления
        self.opacity = 0
        anim = Animation(opacity=1, duration=0.3, t='out_quad')
        anim.start(self)

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
                logger.error(f'Ошибка загрузки иконки {self.icon_asset}: {e}')

        # Заглушка
        self.icon_image.text = "?"
        self.icon_image.color = [0.5, 0.5, 0.5, 1]

    def _on_press(self, instance):
        """Обработчик нажатия"""
        if self.on_click_callback:
            self.on_click_callback(self.screen_name)

        # Анимация нажатия
        anim = Animation(opacity=0.7, duration=0.05)
        anim += Animation(opacity=1, duration=0.1)
        anim.start(self)

    def on_touch_down(self, touch):
        """Эффект при касании"""
        if self.collide_point(*touch.pos):
            self.scale = 0.97
            anim = Animation(scale=1, duration=0.2, t='out_elastic')
            anim.start(self)
        return super().on_touch_down(touch)