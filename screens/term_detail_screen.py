# screens/term_detail_screen.py
"""
Экран определения термина
"""
from kivy.metrics import dp, sp
from kivy.graphics import Color, Rectangle
from kivy.core.image import Image as CoreImage
from kivy.clock import Clock
from io import BytesIO

from kivy.uix.widget import Widget
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDIconButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.app import MDApp

from config.theme import theme
from config.logger_config import screen_logger
from config.layout_config import layout_config
from config.system_bars import get_navigation_bar_height
from screens.base_screen import BaseScreen
from utils.notifications import notify

logger = screen_logger('TermDetail')

try:
    from data import load_asset_as_bytes
    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False
    def load_asset_as_bytes(name):
        return None


class TermDetailScreen(BaseScreen):
    """Экран определения термина"""

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

        # Верхний отступ
        top_padding = layout_config.get_top_padding()
        main_layout.add_widget(Widget(size_hint_y=None, height=top_padding))

        # Контейнер с отступами
        content_padding = layout_config.get_content_padding()

        # Основной контент
        content = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            padding=[content_padding[0], dp(8), content_padding[2], get_navigation_bar_height() + dp(76)]
        )

        # Карточка с определением
        self.term_card = MDCard(
            orientation='vertical',
            size_hint=(1, None),
            padding=[dp(20), dp(20), dp(20), dp(20)],
            spacing=dp(12),
            radius=[theme.CORNER_RADIUS_MEDIUM] * 4,
            md_bg_color=[0, 0, 0, 0.15],
            elevation=2,
            line_color=[1, 1, 1, 0.1],
            line_width=1
        )

        # Название термина
        self.term_name_label = MDLabel(
            text="",
            font_size=sp(28),
            bold=True,
            halign="center",
            size_hint_y=None,
            height=dp(50),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1]
        )

        # Определение
        self.term_description_label = MDLabel(
            text="",
            font_size=sp(17),
            halign="left",
            size_hint_y=None,
            theme_text_color="Custom",
            text_color=[0.9, 0.9, 0.9, 0.95],
            line_height=1.6
        )

        # Синонимы
        self.synonyms_label = MDLabel(
            text="",
            font_size=sp(14),
            halign="left",
            size_hint_y=None,
            height=dp(30),
            theme_text_color="Custom",
            text_color=[0.7, 0.7, 0.7, 0.8]
        )

        # Примеры
        self.examples_label = MDLabel(
            text="",
            font_size=sp(14),
            halign="left",
            size_hint_y=None,
            height=dp(30),
            theme_text_color="Custom",
            text_color=[0.7, 0.7, 0.7, 0.8]
        )

        self.term_card.add_widget(self.term_name_label)
        self.term_card.add_widget(self.term_description_label)
        self.term_card.add_widget(self.synonyms_label)
        self.term_card.add_widget(self.examples_label)

        # Добавляем растягивающийся виджет
        self.term_card.bind(minimum_height=self.term_card.setter('height'))

        content.add_widget(self.term_card)

        # Кнопка возврата
        back_layout = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(48),
            padding=[dp(12), dp(8), dp(12), dp(8)]
        )

        back_btn = MDIconButton(
            icon="arrow-left",
            size_hint=(None, None),
            size=(dp(48), dp(48)),
            theme_icon_color="Custom",
            icon_color=[1, 1, 1, 1],
            md_bg_color=[0, 0, 0, 0.1],
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            on_release=self.go_back
        )

        back_label = MDLabel(
            text="Назад к словарю",
            font_size=sp(14),
            halign="left",
            valign="middle",
            size_hint_x=1,
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.7],
            bold=True
        )

        back_layout.add_widget(back_btn)
        back_layout.add_widget(back_label)

        content.add_widget(back_layout)
        content.add_widget(Widget(size_hint_y=1))

        main_layout.add_widget(content)
        self.add_widget(main_layout)

        logger.info("UI определения термина построен")

    def set_term(self, term_name, term_data, previous_screen='dictionary'):
        """Устанавливает термин для отображения"""
        self.term_name = term_name
        self.term_data = term_data
        self.previous_screen = previous_screen

        logger.info(f"Установлен термин: {term_name}")

        # Обновляем UI
        self.term_name_label.text = term_name

        description = term_data.get('description', 'Описание отсутствует')
        self.term_description_label.text = description
        self.term_description_label.height = max(dp(40), len(description) // 20 * dp(24) + dp(24))

        synonyms = term_data.get('synonyms', [])
        if synonyms:
            self.synonyms_label.text = "🔗 Синонимы: " + ", ".join(synonyms)
            self.synonyms_label.height = dp(30)
        else:
            self.synonyms_label.text = ""
            self.synonyms_label.height = dp(4)

        examples = term_data.get('examples', [])
        if examples:
            self.examples_label.text = "🎯 Примеры: " + ", ".join(examples)
            self.examples_label.height = dp(30)
        else:
            self.examples_label.text = ""
            self.examples_label.height = dp(4)

        # Обновляем высоту карточки
        Clock.schedule_once(self._update_card_height, 0.1)

        # Обновляем TopNav
        self._update_top_nav(term_name)

    def _update_card_height(self, dt):
        """Обновляет высоту карточки"""
        if hasattr(self, 'term_card'):
            self.term_card.height = (
                self.term_name_label.height +
                self.term_description_label.height +
                self.synonyms_label.height +
                self.examples_label.height +
                dp(40)
            )

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