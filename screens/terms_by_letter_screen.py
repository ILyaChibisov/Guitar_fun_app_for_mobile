# screens/terms_by_letter_screen.py
"""
Экран списка терминов по выбранной букве
"""
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard  # ← ДОБАВЛЯЕМ
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.app import MDApp
from kivy.metrics import dp, sp
from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.uix.widget import Widget
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.properties import StringProperty, NumericProperty, ObjectProperty
from kivy.graphics import Color, Rectangle
from io import BytesIO

from config.theme import theme
from config.logger_config import screen_logger
from config.layout_config import layout_config
from config.system_bars import get_navigation_bar_height
from screens.base_screen import BaseScreen

logger = screen_logger('TermsByLetter')

try:
    from data import load_asset_as_bytes
    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False
    def load_asset_as_bytes(name):
        return None


class RecycleTermCard(RecycleDataViewBehavior, MDCard):
    """Переиспользуемая карточка термина"""

    term_name = StringProperty('')
    on_click = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = dp(48)
        self.padding = [dp(16), dp(8), dp(16), dp(8)]
        self.spacing = dp(10)
        self.radius = [theme.CORNER_RADIUS_SMALL] * 4
        self.elevation = 0
        self.ripple_behavior = True
        self.theme_bg_color = "Custom"
        self.md_bg_color = [0, 0, 0, 0.06]
        self.line_color = [1, 1, 1, 0.05]
        self.line_width = 1
        self._build_ui()

    def _build_ui(self):
        # Иконка
        self.icon_label = MDLabel(
            text="📖",
            font_size=sp(18),
            size_hint_x=None,
            width=dp(32),
            halign="center",
            valign="middle",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.6]
        )

        # Термин - жирный
        self.term_label = MDLabel(
            font_size=sp(16),
            size_hint_x=1,
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.95],
            bold=True,
            valign="middle",
            shorten=True,
            shorten_from="right"
        )

        # Стрелка
        arrow = MDLabel(
            text="›",
            font_size=sp(20),
            size_hint_x=None,
            width=dp(24),
            halign="center",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.3]
        )

        self.add_widget(self.icon_label)
        self.add_widget(self.term_label)
        self.add_widget(arrow)

    def refresh_view_attrs(self, rv, index, data):
        self.term_name = data.get('term_name', '')
        self.on_click = data.get('on_click')
        self.term_label.text = self.term_name.capitalize()
        return super().refresh_view_attrs(rv, index, data)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if self.on_click:
                self.on_click(self.term_name)
            return True
        return super().on_touch_down(touch)


class TermRecycleView(RecycleView):
    """Виртуализированный список терминов"""

    def __init__(self, on_term_click=None, **kwargs):
        super().__init__(**kwargs)
        self.on_term_click = on_term_click
        self.animate_scroll = False
        self.bar_width = 0
        self.bar_color = [0, 0, 0, 0]
        self.bar_inactive_color = [0, 0, 0, 0]

        self.layout_manager = RecycleBoxLayout(
            default_size=(None, dp(48)),
            default_size_hint=(1, None),
            size_hint_y=None,
            height=dp(48) * 10,
            orientation='vertical',
            spacing=dp(4)
        )
        self.layout_manager.bind(minimum_height=self.layout_manager.setter('height'))
        self.viewclass = 'RecycleTermCard'
        self.add_widget(self.layout_manager)

    def set_terms(self, terms, on_click):
        data = []
        for term in terms:
            data.append({
                'term_name': term,
                'on_click': on_click
            })
        self.data = data
        self.refresh_from_data()

    def clear(self):
        self.data = []
        self.refresh_from_data()


class TermsByLetterScreen(BaseScreen):
    """Экран списка терминов по букве"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'terms_by_letter'
        self.current_letter = None
        self.terms = []
        self._pending_letter = None
        self._dictionary_screen = None
        self.bg_image = None
        self.recycle_view = None
        self.count_label = None
        self.empty_label = None

        self.init_ui()
        self.load_background()
        logger.info('Экран терминов по букве создан')

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
        main_layout = MDBoxLayout(orientation='vertical', spacing=0)

        # Верхний отступ
        top_padding = layout_config.get_top_padding()
        main_layout.add_widget(Widget(size_hint_y=None, height=top_padding))

        # Счётчик терминов
        self.count_label = MDLabel(
            text="",
            font_size=sp(13),
            halign="center",
            valign="middle",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.7],
            size_hint_y=None,
            height=dp(32),
            padding=[0, dp(4), 0, dp(4)]
        )
        main_layout.add_widget(self.count_label)

        # Контейнер для карточек
        nav_bar_height = get_navigation_bar_height()
        bottom_nav_height = dp(60)
        total_bottom = bottom_nav_height + nav_bar_height + dp(16)

        cards_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            padding=[dp(12), dp(4), dp(12), total_bottom]
        )

        self.recycle_view = TermRecycleView(on_term_click=self.on_term_selected)
        self.recycle_view.bar_width = 0
        self.recycle_view.bar_color = [0, 0, 0, 0]
        self.recycle_view.bar_inactive_color = [0, 0, 0, 0]

        cards_container.add_widget(self.recycle_view)
        main_layout.add_widget(cards_container)

        self.add_widget(main_layout)

    def on_enter(self):
        """При входе на экран"""
        logger.info(f"on_enter: current_letter={self.current_letter}, pending={self._pending_letter}")

        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            if self.current_letter:
                display = "0-9" if self.current_letter in ("digits", "0-9") else self.current_letter.upper()
                app.top_nav.set_custom_title(f"Буква {display}")
                app.top_nav._show_back_button()
                app.top_nav.back_btn.on_release = self.go_back
            elif self._pending_letter:
                display = "0-9" if self._pending_letter in ("digits", "0-9") else self._pending_letter.upper()
                app.top_nav.set_custom_title(f"Буква {display}")
                app.top_nav._show_back_button()
                app.top_nav.back_btn.on_release = self.go_back

        if self._pending_letter:
            letter = self._pending_letter
            self._pending_letter = None
            self._do_load_letter(letter)
        elif self.current_letter:
            self._do_load_letter(self.current_letter)

    def set_letter(self, letter, dictionary_screen=None):
        """Устанавливает букву для загрузки"""
        logger.info(f"set_letter: {letter}")
        self.current_letter = letter
        self._dictionary_screen = dictionary_screen

        if not self.manager or self.manager.current != self.name:
            logger.info(f"Экран не активен, сохраняем букву {letter} для on_enter")
            self._pending_letter = letter
            return

        self._do_load_letter(letter)

    def go_back(self, instance=None):
        """Возврат на экран словаря"""
        logger.info("🔙 go_back: возврат на dictionary")
        if hasattr(self, 'manager') and self.manager:
            self.manager.current = 'dictionary'

    def _do_load_letter(self, letter):
        """Загружает термины для буквы"""
        logger.info(f"_do_load_letter: {letter}")
        self.current_letter = letter

        if self.recycle_view:
            self.recycle_view.clear()

        # Получаем термины из словаря
        if self._dictionary_screen:
            terms = self._dictionary_screen.terms_by_letter.get(letter, [])
            self.terms = terms
            self._display_terms(terms)
        else:
            # Пытаемся получить через менеджер
            app = MDApp.get_running_app()
            if app and hasattr(app, 'screen_manager'):
                for screen in app.screen_manager.screens:
                    if screen.name == 'dictionary':
                        self._dictionary_screen = screen
                        terms = screen.terms_by_letter.get(letter, [])
                        self.terms = terms
                        self._display_terms(terms)
                        return
            self.terms = []
            self._display_terms([])

    def _display_terms(self, terms):
        """Отображает список терминов"""
        if terms is None:
            terms = []

        logger.info(f"_display_terms: {len(terms)} терминов")

        self._update_count_label(len(terms))

        if not terms:
            self._show_empty()
            if self.recycle_view:
                self.recycle_view.clear()
            return

        if self.recycle_view:
            self.recycle_view.set_terms(terms, self.on_term_selected)

    def _update_count_label(self, total):
        """Обновляет счётчик"""
        if total == 0:
            text = "Нет терминов на эту букву"
        elif total == 1:
            text = "Найден 1 термин"
        elif 2 <= total <= 4:
            text = f"Найдено {total} термина"
        else:
            text = f"Найдено {total} терминов"

        if self.count_label:
            self.count_label.text = text

    def _show_empty(self, text="Нет терминов на эту букву"):
        """Показывает сообщение о пустом списке"""
        if self.empty_label:
            return
        self.empty_label = MDLabel(
            text=text,
            halign="center",
            font_size=sp(14),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.4],
            size_hint_y=None,
            height=dp(60)
        )
        if hasattr(self, 'recycle_view') and self.recycle_view:
            self.recycle_view.add_widget(self.empty_label)

    def on_term_selected(self, term_name):
        """Обработчик выбора термина"""
        logger.info(f"Выбран термин: {term_name}")

        if not self._dictionary_screen:
            app = MDApp.get_running_app()
            if app and hasattr(app, 'screen_manager'):
                for screen in app.screen_manager.screens:
                    if screen.name == 'dictionary':
                        self._dictionary_screen = screen
                        break

        term_data = None
        if self._dictionary_screen:
            term_data = self._dictionary_screen.all_terms.get(term_name)

        if not term_data:
            logger.error(f"Термин не найден: {term_name}")
            return

        if hasattr(self, 'manager') and self.manager:
            if self.manager.has_screen('term_detail'):
                term_detail = self.manager.get_screen('term_detail')
                term_detail.set_term(term_name, term_data, self.name)
                self.manager.current = 'term_detail'