# screens/components/carousel.py
"""
Карусель для главного экрана
"""
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.carousel import Carousel
from kivy.clock import Clock
from kivy.metrics import dp

from config.carousel_config import CarouselConfig
from config.logger_config import get_logger
from screens.components.carousel_card import CarouselCard

logger = get_logger('UI')


class MainCarousel(BoxLayout):
    """Карусель для главного экрана"""

    def __init__(self, screen_manager, on_item_selected=None, **kwargs):
        super().__init__(**kwargs)
        self.sm = screen_manager
        self.on_item_selected = on_item_selected

        self.orientation = 'vertical'
        self.size_hint = (1, None)
        self.height = dp(CarouselConfig.CAROUSEL_HEIGHT + 30)

        # Создаём карусель
        self.carousel = Carousel(
            direction='right',
            loop=True,
            size_hint=(1, 1)
        )

        # Создаём карточки
        self._create_cards()

        self.add_widget(self.carousel)

        # Автопрокрутка
        self.auto_scroll_event = None
        self.start_auto_scroll()

        logger.info('Карусель создана')

    def _create_cards(self):
        """Создаёт карточки из конфигурации"""
        for item in CarouselConfig.CAROUSEL_ITEMS:
            card = CarouselCard(
                icon_asset=item['icon_asset'],
                title=item['title'],
                screen_name=item['screen'],
                on_click_callback=self._on_card_click
            )
            # Центрируем карточку в карусели
            card.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
            self.carousel.add_widget(card)

    def _on_card_click(self, screen_name):
        """Обработчик клика по карточке"""
        logger.info(f'Выбрана карточка: {screen_name}')

        self.stop_auto_scroll()

        if self.on_item_selected:
            self.on_item_selected(screen_name)
        elif self.sm:
            self.sm.current = screen_name

        Clock.schedule_once(lambda dt: self.start_auto_scroll(), 5)

    def start_auto_scroll(self):
        """Запускает автопрокрутку"""
        if self.auto_scroll_event:
            return
        self.auto_scroll_event = Clock.schedule_interval(self._next_slide, 3.0)

    def stop_auto_scroll(self):
        """Останавливает автопрокрутку"""
        if self.auto_scroll_event:
            self.auto_scroll_event.cancel()
            self.auto_scroll_event = None

    def _next_slide(self, dt):
        """Переключает на следующий слайд"""
        if self.carousel and self.carousel.parent:
            self.carousel.load_next()

    def on_touch_down(self, touch):
        """При касании останавливаем автопрокрутку на время"""
        self.stop_auto_scroll()
        result = super().on_touch_down(touch)
        Clock.schedule_once(lambda dt: self.start_auto_scroll(), 5)
        return result