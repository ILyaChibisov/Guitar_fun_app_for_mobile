# screens/term_detail_screen.py
"""
Экран определения термина - упрощённый
"""
from kivy.metrics import dp, sp
from kivy.graphics import Color, Rectangle
from kivy.core.image import Image as CoreImage
from kivy.clock import Clock
from io import BytesIO

from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.app import MDApp
from kivy.uix.widget import Widget
from kivy.uix.scrollview import ScrollView

from config.theme import theme
from config.logger_config import screen_logger
from config.layout_config import layout_config
from config.system_bars import get_navigation_bar_height
from screens.base_screen import BaseScreen

logger = screen_logger('TermDetail')

try:
    from data import load_asset_as_bytes
    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False
    def load_asset_as_bytes(name):
        return None


class TermDetailScreen(BaseScreen):
    """Экран определения термина - упрощённый"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'term_detail'
        self.bg_image = None
        self.term_name = None
        self.term_data = None
        self.previous_screen = 'dictionary'

        self.init_ui()
        self.load_background()

        logger.info('Экран определения термина создан')

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
        """Инициализирует UI"""
        main_layout = MDBoxLayout(orientation='vertical', spacing=0)

        # Верхний отступ (под статус-бар и TopNav)
        top_padding = layout_config.get_top_padding()
        main_layout.add_widget(Widget(size_hint_y=None, height=top_padding))

        # Дополнительный отступ
        main_layout.add_widget(Widget(size_hint_y=None, height=dp(12)))

        # Контейнер с отступами
        content_padding = layout_config.get_content_padding()

        # ScrollView для прокрутки текста
        scroll = ScrollView(
            size_hint=(1, 1),
            do_scroll_x=False,
            bar_width=0,
            bar_color=[0, 0, 0, 0],
            bar_inactive_color=[0, 0, 0, 0],
            bar_margin=0
        )

        # Контент
        content = MDBoxLayout(
            orientation='vertical',
            size_hint_y=None,
            adaptive_height=True,
            padding=[content_padding[0], dp(8), content_padding[2], get_navigation_bar_height() + dp(60)]
        )

        # Название термина - жирное, по центру, с большой буквы
        self.term_name_label = MDLabel(
            text="",
            font_size=sp(28),
            bold=True,
            halign="center",
            valign="top",
            size_hint_y=None,
            height=dp(60),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1]
        )
        content.add_widget(self.term_name_label)

        # Разделитель (пустая строка)
        content.add_widget(Widget(size_hint_y=None, height=dp(16)))

        # Описание термина - белым текстом, обычным шрифтом
        self.term_description_label = MDLabel(
            text="",
            font_size=sp(17),
            halign="left",
            valign="top",
            size_hint_y=None,
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.9],
            line_height=1.6
        )
        content.add_widget(self.term_description_label)

        scroll.add_widget(content)
        main_layout.add_widget(scroll)

        self.add_widget(main_layout)

        logger.info("UI определения термина построен")

    def set_term(self, term_name, term_data, previous_screen='dictionary'):
        """Устанавливает термин для отображения"""
        self.term_name = term_name
        self.term_data = term_data
        self.previous_screen = previous_screen

        logger.info(f"Установлен термин: {term_name}")

        # Название - с большой буквы, жирное
        self.term_name_label.text = term_name.capitalize()

        # Описание
        description = term_data.get('description', 'Описание отсутствует')
        self.term_description_label.text = description

        # Вычисляем высоту для описания
        lines = len(description) // 30 + 1
        self.term_description_label.height = max(dp(40), lines * dp(28))

        # Обновляем TopNav
        self._update_top_nav(term_name)

    def _update_top_nav(self, title):
        """Обновляет заголовок в TopNav"""
        try:
            app = MDApp.get_running_app()
            if app and hasattr(app, 'top_nav'):
                app.top_nav.set_custom_title(title)
                app.top_nav._show_back_button()
                app.top_nav.back_btn.on_release = self.go_back
        except Exception as e:
            logger.error(f"Ошибка обновления TopNav: {e}")

    def go_back(self, instance=None):
        """Возврат на предыдущий экран"""
        logger.info(f"🔙 Возврат на {self.previous_screen}")
        if hasattr(self, 'manager') and self.manager:
            if self.manager.has_screen(self.previous_screen):
                self.manager.current = self.previous_screen
            else:
                self.manager.current = 'dictionary'

    def on_enter(self):
        """При входе на экран"""
        logger.info("Вход в экран определения термина")
        if self.term_name:
            self._update_top_nav(self.term_name)

    def on_leave(self):
        """При выходе с экрана"""
        logger.info("Выход из экрана определения термина")