# main.py
"""
Главный файл приложения GuitarApp
С простой навигацией без сложных компонентов KivyMD
"""
import os
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, SlideTransition
from kivy.metrics import dp, sp
from kivy.graphics import Color, Rectangle

# Настройка логирования
from config.logger_config import setup_logging, app_logger

setup_logging(level='debug')

# Импорты KivyMD (только базовые)
from kivymd.app import MDApp
from kivymd.uix.label import MDLabel
from kivymd.uix.screen import MDScreen

# Наши модули
from config.app_config import config
from config.theme import theme
from screens.manager import setup_screen_manager

# Настройка окна для разработки
if os.name == 'nt':
    Window.size = (400, 750)
    Window.top = 50
    Window.left = 50

logger = app_logger()


class NavButton(Button):
    """Кнопка навигации"""

    def __init__(self, text, screen_name, **kwargs):
        super().__init__(**kwargs)
        self.text = text
        self.screen_name = screen_name
        self.size_hint = (1, 1)
        self.background_normal = ''
        self.background_color = (1, 1, 1, 0)  # Прозрачный
        self.color = theme.TEXT_SECONDARY
        self.font_size = sp(14)
        self.bold = False

    def set_active(self, active):
        """Устанавливает активное состояние"""
        if active:
            self.color = theme.PRIMARY
            self.bold = True
        else:
            self.color = theme.TEXT_SECONDARY
            self.bold = False


class BottomNavButton(NavButton):
    """Кнопка нижней навигации с иконкой и текстом"""

    def __init__(self, icon, text, screen_name, **kwargs):
        super().__init__(text, screen_name, **kwargs)
        self.icon = icon
        self.text = f"{icon}\n{text}"
        self.font_size = sp(12)
        self.valign = 'middle'
        self.halign = 'center'


class GuitarApp(MDApp):
    """Главный класс приложения"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = config.APP_NAME

        logger.info('🎸 ' + '=' * 50)
        logger.info(f'🎸 ЗАПУСК {config.APP_NAME} v{config.VERSION}')
        logger.info('🎸 ' + '=' * 50)

    def build(self):
        """Создаёт интерфейс приложения"""
        logger.debug('Создание интерфейса...')

        # Настройка темы KivyMD
        self.theme_cls.primary_palette = "Teal"
        self.theme_cls.theme_style = "Light"

        # Главный контейнер
        root = BoxLayout(orientation='vertical')

        # Создаём менеджер экранов
        self.screen_manager = setup_screen_manager()

        # Верхняя навигация
        self.top_nav_buttons = []
        top_nav = self.create_top_navigation()
        root.add_widget(top_nav)

        # Менеджер экранов
        root.add_widget(self.screen_manager)

        # Нижняя навигация
        self.bottom_nav_buttons = []
        bottom_nav = self.create_bottom_navigation()
        root.add_widget(bottom_nav)

        # Подписываемся на изменение экрана
        self.screen_manager.bind(current=self.on_screen_change)

        logger.info('Интерфейс успешно создан')
        return root

    def create_top_navigation(self):
        """Создаёт верхнюю панель навигации"""

        top_nav = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(48),
            padding=[dp(8), 0, dp(8), 0],
            spacing=dp(4)
        )

        # Белый фон
        with top_nav.canvas.before:
            Color(1, 1, 1, 1)
            top_nav.bg_rect = Rectangle(pos=top_nav.pos, size=top_nav.size)

        def update_bg(instance, value):
            top_nav.bg_rect.pos = instance.pos
            top_nav.bg_rect.size = instance.size

        top_nav.bind(pos=update_bg, size=update_bg)

        # Кнопки разделов
        nav_items = [
            {"text": "Главная", "screen": "home"},
            {"text": "Песни", "screen": "songs"},
            {"text": "Аккорды", "screen": "chords"},
            {"text": "Словарь", "screen": "dictionary"},
            {"text": "Избранное", "screen": "favorites"}
        ]

        for item in nav_items:
            btn = NavButton(
                text=item["text"],
                screen_name=item["screen"]
            )
            btn.bind(on_press=self.on_top_nav_press)
            top_nav.add_widget(btn)
            self.top_nav_buttons.append(btn)

        return top_nav

    def create_bottom_navigation(self):
        """Создаёт нижнюю панель навигации"""

        bottom_nav = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(70),
            padding=[theme.PADDING, dp(5), theme.PADDING, dp(5)],
            spacing=dp(5)
        )

        # Белый фон с тенью сверху
        with bottom_nav.canvas.before:
            Color(1, 1, 1, 1)
            bottom_nav.bg_rect = Rectangle(pos=bottom_nav.pos, size=bottom_nav.size)
            Color(0, 0, 0, 0.05)
            bottom_nav.shadow = Rectangle(
                pos=(bottom_nav.x, bottom_nav.y + bottom_nav.height - dp(1)),
                size=(bottom_nav.width, dp(1))
            )

        def update_bg(instance, value):
            bottom_nav.bg_rect.pos = instance.pos
            bottom_nav.bg_rect.size = instance.size
            bottom_nav.shadow.pos = (instance.x, instance.y + instance.height - dp(1))
            bottom_nav.shadow.size = (instance.width, dp(1))

        bottom_nav.bind(pos=update_bg, size=update_bg)

        # Элементы навигации
        nav_items = [
            {"icon": "🏠", "text": "Главная", "screen": "home"},
            {"icon": "🎵", "text": "Песни", "screen": "songs"},
            {"icon": "🎸", "text": "Аккорды", "screen": "chords"},
            {"icon": "📚", "text": "Словарь", "screen": "dictionary"},
            {"icon": "❤️", "text": "Избранное", "screen": "favorites"}
        ]

        for item in nav_items:
            btn = BottomNavButton(
                icon=item["icon"],
                text=item["text"],
                screen_name=item["screen"]
            )
            btn.bind(on_press=self.on_bottom_nav_press)
            bottom_nav.add_widget(btn)
            self.bottom_nav_buttons.append(btn)

        return bottom_nav

    def on_top_nav_press(self, instance):
        """Обработчик нажатия на верхнюю навигацию"""
        if self.screen_manager.current != instance.screen_name:
            self.screen_manager.current = instance.screen_name
            logger.debug(f'Верхняя навигация: переключение на {instance.screen_name}')

    def on_bottom_nav_press(self, instance):
        """Обработчик нажатия на нижнюю навигацию"""
        if self.screen_manager.current != instance.screen_name:
            self.screen_manager.current = instance.screen_name
            logger.debug(f'Нижняя навигация: переключение на {instance.screen_name}')

    def on_screen_change(self, instance, value):
        """Обновляет активные кнопки при смене экрана"""
        # Обновляем верхнюю навигацию
        for btn in self.top_nav_buttons:
            btn.set_active(btn.screen_name == value)

        # Обновляем нижнюю навигацию
        for btn in self.bottom_nav_buttons:
            btn.set_active(btn.screen_name == value)

        logger.debug(f'Активный экран: {value}')

    def on_start(self):
        """Вызывается после запуска"""
        # Устанавливаем начальное состояние кнопок
        self.on_screen_change(self.screen_manager, 'home')
        logger.info('Приложение запущено и готово к работе')

    def on_pause(self):
        logger.debug('Приложение свернуто')
        return True

    def on_resume(self):
        logger.debug('Приложение восстановлено')

    def on_stop(self):
        logger.info('Приложение закрыто')


if __name__ == '__main__':
    GuitarApp().run()