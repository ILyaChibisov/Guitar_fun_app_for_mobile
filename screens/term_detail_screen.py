# screens/term_detail_screen.py
"""
Экран определения термина - в стиле song_detail_screen
BottomNav всегда виден, панель настроек над текстом
"""
from kivy.metrics import dp, sp
from kivy.graphics import Color, Rectangle
from kivy.core.image import Image as CoreImage
from kivy.clock import Clock
from io import BytesIO

from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDIconButton
from kivymd.app import MDApp
from kivy.uix.widget import Widget
from kivymd.uix.scrollview import MDScrollView
from kivy.utils import platform

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


class IconActionButton(MDIconButton):
    """Кнопка действия в панели"""

    def __init__(self, icon_name, on_press_callback=None, icon_color=None, **kwargs):
        super().__init__(**kwargs)
        self.on_press_callback = on_press_callback
        self.size_hint = (1, None)
        self.height = dp(40)
        self.theme_icon_color = "Custom"
        if icon_color:
            self.icon_color = icon_color
        else:
            self.icon_color = [0.5, 0.5, 0.5, 0.9]
        self.md_bg_color = [0, 0, 0, 0]
        self.icon = icon_name
        self.bind(on_release=self._on_press)

    def _on_press(self, instance):
        if self.on_press_callback:
            self.on_press_callback()


class TermDetailScreen(BaseScreen):
    """Экран определения термина - в стиле song_detail_screen"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'term_detail'
        self.bg_image = None
        self.term_name = None
        self.term_data = None
        self.previous_screen = 'dictionary'

        # Настройки размера шрифта (как в song_detail_screen)
        if platform == 'android':
            self.STANDARD_FONT_SIZE = 42
            self.MIN_FONT_SIZE = 30
            self.MAX_FONT_SIZE = 60
        else:
            self.STANDARD_FONT_SIZE = 20
            self.MIN_FONT_SIZE = 14
            self.MAX_FONT_SIZE = 32
        self.current_font_size = self.STANDARD_FONT_SIZE

        # Размеры шрифта для слайдера
        if platform == 'android':
            self._font_sizes = [30, 34, 38, 42, 46, 50, 54, 58, 60]
        else:
            self._font_sizes = [14, 16, 18, 20, 22, 24, 26, 28, 30, 32]

        # Для смены темы текста
        self.is_light_theme = False

        # Панель-контейнер
        self.panel_container = None
        self.current_panel_type = 'main'

        self.init_ui()
        self.load_background()

        logger.info('Экран определения термина создан')

    def _size_to_slider(self, size):
        """Преобразует размер шрифта в значение слайдера"""
        try:
            return self._font_sizes.index(size)
        except ValueError:
            closest = min(self._font_sizes, key=lambda x: abs(x - size))
            return self._font_sizes.index(closest)

    def _slider_to_size(self, slider_value):
        """Преобразует значение слайдера в размер шрифта"""
        idx = int(round(slider_value))
        if idx < 0:
            idx = 0
        elif idx > len(self._font_sizes) - 1:
            idx = len(self._font_sizes) - 1
        return self._font_sizes[idx]

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

    def _toggle_theme(self, *args):
        """Переключает темы: зелёная -> светлая -> тёмная -> зелёная"""
        if not hasattr(self, '_current_theme'):
            self._current_theme = 'green'

        if self._current_theme == 'green':
            self._set_light_theme()
            self._current_theme = 'light'
        elif self._current_theme == 'light':
            self._set_dark_theme()
            self._current_theme = 'dark'
        else:
            self._set_green_theme()
            self._current_theme = 'green'

        # Обновляем иконку темы
        if hasattr(self, 'theme_btn'):
            if self._current_theme == 'green':
                self.theme_btn.icon = "weather-sunny"
                self.theme_btn.icon_color = [0.46, 0.70, 0.71, 1]
            elif self._current_theme == 'light':
                self.theme_btn.icon = "white-balance-sunny"
                self.theme_btn.icon_color = [1, 1, 1, 1]
            else:
                self.theme_btn.icon = "weather-night"
                self.theme_btn.icon_color = [0.3, 0.3, 0.3, 1]

        logger.info(f"🔄 Тема изменена на: {self._current_theme}")

    def _set_green_theme(self):
        """Зелёная тема - фон из ассета, текст белый"""
        self.is_light_theme = False
        self.content_label.text_color = [1, 1, 1, 0.95]
        if hasattr(self, '_text_container') and self._text_container:
            self._text_container.md_bg_color = [0, 0, 0, 0]
        if hasattr(self, 'theme_btn'):
            self.theme_btn.icon = "weather-sunny"
            self.theme_btn.icon_color = [0.46, 0.70, 0.71, 1]

    def _set_light_theme(self):
        """Светлая тема - фон белый, текст чёрный"""
        self.is_light_theme = True
        self.content_label.text_color = [0, 0, 0, 0.95]
        if hasattr(self, '_text_container') and self._text_container:
            self._text_container.md_bg_color = [1, 1, 1, 1]
        if hasattr(self, 'theme_btn'):
            self.theme_btn.icon = "white-balance-sunny"
            self.theme_btn.icon_color = [1, 1, 1, 1]

    def _set_dark_theme(self):
        """Тёмная тема - фон чёрный, текст белый"""
        self.is_light_theme = False
        self.content_label.text_color = [1, 1, 1, 0.95]
        if hasattr(self, '_text_container') and self._text_container:
            self._text_container.md_bg_color = [0.05, 0.05, 0.05, 1]
        if hasattr(self, 'theme_btn'):
            self.theme_btn.icon = "weather-night"
            self.theme_btn.icon_color = [0.3, 0.3, 0.3, 1]

    def init_ui(self):
        """Инициализирует UI как в song_detail_screen"""
        main_container = MDBoxLayout(orientation='vertical', size_hint=(1, 1), padding=[0, 0, 0, 0])

        # ============ ОТСТУП ПОД TOPNAV ============
        top_padding_for_nav = layout_config.get_top_padding()
        if platform == 'android':
            min_top_padding = dp(48)
            if top_padding_for_nav < min_top_padding:
                top_padding_for_nav = min_top_padding
            else:
                top_padding_for_nav = top_padding_for_nav + dp(8)

        self._top_spacer_term = Widget(size_hint_y=None, height=top_padding_for_nav)
        main_container.add_widget(self._top_spacer_term)

        # ============ КОНТЕЙНЕР ДЛЯ КАРТОЧКИ ============
        card_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            padding=[0, 0, 0, 0]
        )

        # ============ ОТСТУП СНИЗУ ============
        nav_bar_height = get_navigation_bar_height()
        bottom_padding_for_card = layout_config.get_bottom_padding()

        self.term_card = MDCard(
            orientation='vertical',
            size_hint=(1, 1),
            padding=[0, 0, 0, bottom_padding_for_card],
            spacing=0,
            radius=[0, 0, 0, 0],
            md_bg_color=[0, 0, 0, 0],
            elevation=0
        )

        # ============ ВЕРХНЯЯ РАЗДЕЛИТЕЛЬНАЯ ПОЛОСКА ============
        self.top_divider = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(2),
            md_bg_color=[0.5, 0.5, 0.5, 0.3],
            padding=[0, 0, 0, 0]
        )
        self.term_card.add_widget(self.top_divider)

        # ============ ПАНЕЛЬ-КОНТЕЙНЕР (НАД КОНТЕНТОМ) ============
        self.panel_container = MDCard(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(52),
            md_bg_color=[0, 0, 0, 0.06],
            elevation=0,
            radius=[0, 0, 0, 0],
            padding=[0, 0, 0, 0],
            spacing=0
        )
        self.term_card.add_widget(self.panel_container)

        # ============ РАЗДЕЛИТЕЛЬНАЯ ПОЛОСКА ПОД ПАНЕЛЬЮ ============
        self.panel_divider = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(2),
            md_bg_color=[0.5, 0.5, 0.5, 0.3],
            padding=[0, 0, 0, 0]
        )
        self.term_card.add_widget(self.panel_divider)

        # ============ СКРОЛЛ ДЛЯ ТЕКСТА ============
        self.content_scroll = MDScrollView(
            size_hint=(1, 1),
            do_scroll_x=False,
            bar_width=3,
            bar_color=[0.5, 0.5, 0.5, 0.3],
            bar_inactive_color=[0.5, 0.5, 0.5, 0.1]
        )

        # ============ КОНТЕЙНЕР ДЛЯ ТЕКСТА ============
        self._text_container = MDBoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=4,
            padding=[dp(16), dp(16), dp(16), dp(8)],
            adaptive_height=True,
            md_bg_color=[0, 0, 0, 0]
        )

        # ============ ОПИСАНИЕ ТЕРМИНА ============
        self.content_label = MDLabel(
            text="",
            font_size=self.current_font_size,
            size_hint_y=None,
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.95],
            valign="top",
            line_height=1.6
        )
        self.content_label.bind(texture_size=self._update_content_height)
        self._text_container.add_widget(self.content_label)

        self.content_scroll.add_widget(self._text_container)
        self.term_card.add_widget(self.content_scroll)

        # ============ НИЖНЯЯ РАЗДЕЛИТЕЛЬНАЯ ПОЛОСКА ============
        self.bottom_divider = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(2),
            md_bg_color=[0.5, 0.5, 0.5, 0.3],
            padding=[0, 0, 0, 0]
        )
        self.term_card.add_widget(self.bottom_divider)

        card_container.add_widget(self.term_card)
        main_container.add_widget(card_container)

        self.add_widget(main_container)

        if hasattr(self, '_top_spacer') and self._top_spacer:
            self._top_spacer.height = 0
        if hasattr(self, '_bottom_spacer') and self._bottom_spacer:
            self._bottom_spacer.height = 0

        # ============ СОЗДАЁМ НАЧАЛЬНУЮ ПАНЕЛЬ ============
        self._create_main_panel()

        logger.info(f"TermDetailScreen: init_ui completed")
        logger.info(f"  top_padding={top_padding_for_nav}dp")
        logger.info(f"  bottom_padding_for_card={bottom_padding_for_card}dp")

    def _create_main_panel(self):
        """Создаёт основную панель с настройками шрифта и темы"""
        self.panel_container.clear_widgets()

        panel = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, 1),
            padding=[dp(4), dp(2), dp(4), dp(2)],
            spacing=dp(2)
        )

        center_container = MDBoxLayout(
            orientation='vertical',
            size_hint_x=1,
            spacing=dp(0),
            padding=[dp(0), dp(0), dp(0), dp(0)]
        )

        from kivymd.uix.slider import MDSlider

        total_steps = len(self._font_sizes) - 1
        current_slider_value = self._size_to_slider(self.current_font_size)

        # Верхний ряд со значением размера
        top_row = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(14),
            spacing=dp(0)
        )

        left_spacer = MDLabel(
            text="",
            size_hint_x=None,
            width=dp(2)
        )

        self.font_value_label = MDLabel(
            text=self._get_font_multiplier(self.current_font_size),
            font_size=sp(10),
            halign="center",
            valign="bottom",
            size_hint_x=1,
            theme_text_color="Custom",
            text_color=[0.46, 0.70, 0.71, 1],
            bold=True
        )

        right_spacer = MDLabel(
            text="",
            size_hint_x=None,
            width=dp(2)
        )

        top_row.add_widget(left_spacer)
        top_row.add_widget(self.font_value_label)
        top_row.add_widget(right_spacer)

        # Слайдер
        slider_container = MDBoxLayout(
            orientation='horizontal',
            size_hint_x=1,
            size_hint_y=None,
            height=dp(28),
            padding=[dp(2), dp(0), dp(2), dp(0)]
        )

        self.font_slider = MDSlider(
            min=-0.01,
            max=float(total_steps + 0.01),
            value=current_slider_value,
            step=1,
            size_hint_x=1,
            size_hint_y=None,
            height=dp(28),
            hint=False
        )
        self.font_slider.ripple_scale = 0

        bi_color = [0.46, 0.70, 0.71, 1]

        self.font_slider.thumb_color_active = bi_color
        self.font_slider.thumb_color_inactive = bi_color
        self.font_slider.thumb_color_disabled = bi_color
        self.font_slider.track_color_active = [0.46, 0.70, 0.71, 0.6]
        self.font_slider.track_color_inactive = [1, 1, 1, 0.3]
        self.font_slider.color = bi_color

        def on_slider_change(instance, value):
            int_value = int(round(value))
            if int_value < 0:
                int_value = 0
            elif int_value > total_steps:
                int_value = total_steps

            if self.font_slider.value != int_value:
                self.font_slider.value = int_value

            bi_color = [0.46, 0.70, 0.71, 1]
            self.font_slider.thumb_color_active = bi_color
            self.font_slider.thumb_color_inactive = bi_color
            self.font_slider.thumb_color_disabled = bi_color

            new_size = self._slider_to_size(int_value)

            if self.current_font_size != new_size:
                self.current_font_size = new_size
                self.font_value_label.text = self._get_font_multiplier(new_size)

                if hasattr(self, 'content_label'):
                    self.content_label.font_size = self.current_font_size
                    self._update_content_height()

                    # Прокручиваем вверх после изменения шрифта
                    delays = [0.0, 0.01, 0.03, 0.05, 0.08, 0.12, 0.2, 0.3]
                    for delay in delays:
                        Clock.schedule_once(lambda dt, d=delay: setattr(self.content_scroll, 'scroll_y', 1.0), delay)

                logger.info(f"🔍 Размер шрифта изменён на: {self.current_font_size}")

        self.font_slider.bind(value=on_slider_change)

        slider_container.add_widget(self.font_slider)

        center_container.add_widget(top_row)
        center_container.add_widget(slider_container)

        # Кнопка смены темы
        self.theme_btn = IconActionButton(
            icon_name="weather-sunny",
            on_press_callback=self._toggle_theme,
            icon_color=[0.46, 0.70, 0.71, 1]
        )
        self.theme_btn.size_hint = (None, None)
        self.theme_btn.size = (dp(36), dp(36))

        panel.add_widget(center_container)
        panel.add_widget(self.theme_btn)

        self.panel_container.add_widget(panel)
        self.current_panel_type = 'main'
        logger.info("✅ Создана основная панель")

        Clock.schedule_once(lambda dt: self._fix_slider_thumb(self.font_slider), 0.1)
        Clock.schedule_once(lambda dt: self._fix_slider_thumb(self.font_slider), 0.3)

    def _fix_slider_thumb(self, slider):
        """Принудительно обновляет слайдер"""
        if slider:
            bi_color = [0.46, 0.70, 0.71, 1]
            slider.thumb_color_active = bi_color
            slider.thumb_color_inactive = bi_color
            slider.thumb_color_disabled = bi_color

            current = slider.value
            slider.value = current + 0.01
            Clock.schedule_once(lambda dt: setattr(slider, 'value', current), 0.01)

    def _get_font_multiplier(self, font_size):
        """Возвращает строку с множителем размера шрифта"""
        ratio = font_size / self.STANDARD_FONT_SIZE
        rounded = round(ratio * 10) / 10
        if rounded == int(rounded):
            return f"{int(rounded)}x"
        return f"{rounded:.1f}x"

    def _update_content_height(self, *args):
        """Обновляет высоту контейнера с текстом"""
        if not self.content_label.texture:
            Clock.schedule_once(lambda dt: self._update_content_height(), 0.05)
            return

        text_height = self.content_label.texture_size[1]
        self.content_label.height = max(dp(50), text_height + dp(8))

        if self.content_label.parent:
            self.content_label.parent.height = text_height + dp(16)
            if hasattr(self.content_label.parent, 'minimum_height'):
                self.content_label.parent.minimum_height = text_height + dp(16)

        self.content_scroll.scroll_y = 1.0

    def _reset_to_defaults(self):
        """Сбрасывает настройки к стандартным"""
        # Сброс шрифта
        self.current_font_size = self.STANDARD_FONT_SIZE
        if hasattr(self, 'content_label'):
            self.content_label.font_size = self.current_font_size
            self._update_content_height()
        if hasattr(self, 'font_value_label'):
            self.font_value_label.text = self._get_font_multiplier(self.current_font_size)
        if hasattr(self, 'font_slider'):
            self.font_slider.value = self._size_to_slider(self.current_font_size)

        # Сброс темы на зелёную
        if hasattr(self, '_current_theme') and self._current_theme != 'green':
            self._set_green_theme()
            self._current_theme = 'green'
        elif not hasattr(self, '_current_theme'):
            self._current_theme = 'green'
            self._set_green_theme()

        # Обновляем иконку темы
        if hasattr(self, 'theme_btn'):
            self.theme_btn.icon = "weather-sunny"
            self.theme_btn.icon_color = [0.46, 0.70, 0.71, 1]

        logger.info("🔄 Настройки сброшены к стандартным")

    def _clean_description(self, text):
        """Убирает пустые строки в начале и конце текста"""
        if not text:
            return ""
        lines = text.split('\n')
        while lines and not lines[0].strip():
            lines.pop(0)
        while lines and not lines[-1].strip():
            lines.pop()
        return '\n'.join(lines)

    def set_term(self, term_name, term_data, previous_screen='dictionary'):
        """Устанавливает термин для отображения"""
        # Сбрасываем настройки при каждом новом термине
        self._reset_to_defaults()

        self.term_name = term_name
        self.term_data = term_data
        self.previous_screen = previous_screen

        logger.info(f"Установлен термин: {term_name}")

        # Описание - очищаем от пустых строк в начале/конце
        description = term_data.get('description', 'Описание отсутствует')
        description = self._clean_description(description)
        self.content_label.text = description

        # Обновляем TopNav
        self._update_top_nav(term_name)

        # Прокручиваем вверх после загрузки
        Clock.schedule_once(self._scroll_to_top, 0.1)
        Clock.schedule_once(self._scroll_to_top, 0.3)

    def _scroll_to_top(self, dt):
        """Прокручивает вверх"""
        if hasattr(self, 'content_scroll'):
            self.content_scroll.scroll_y = 1.0

    def _update_top_nav(self, title):
        """Обновляет заголовок в TopNav с переносом длинных названий"""
        try:
            app = MDApp.get_running_app()
            if app and hasattr(app, 'top_nav'):
                # Форматируем название: первая буква заглавная, остальные строчные
                formatted_title = title.capitalize() if title else "Термин"

                from kivymd.uix.boxlayout import MDBoxLayout
                from kivymd.uix.label import MDLabel
                from kivy.metrics import dp, sp

                title_container = MDBoxLayout(
                    orientation='vertical',
                    size_hint=(1, 1),
                    spacing=dp(2),
                    padding=[dp(8), dp(4), dp(8), dp(4)]
                )

                # Для длинных терминов (больше 20 символов) уменьшаем шрифт
                font_size = sp(18) if len(formatted_title) <= 20 else sp(15)

                title_label = MDLabel(
                    text=formatted_title,
                    font_size=font_size,
                    halign="center",
                    valign="middle",
                    theme_text_color="Custom",
                    text_color=[1, 1, 1, 1],
                    bold=True,
                    text_size=(dp(250), None),  # ← ПЕРЕНОС ПО ШИРИНЕ
                    shorten=False,  # ← ОТКЛЮЧАЕМ ОБРЕЗАНИЕ
                    size_hint_y=None,
                    height=dp(60)  # ← ДОСТАТОЧНО МЕСТА ДЛЯ 2 СТРОК
                )

                title_container.add_widget(title_label)

                app.top_nav.set_custom_title_widget(title_container)
                app.top_nav._show_back_button()
                app.top_nav.back_btn.on_release = self.go_back

                logger.info(f"✅ TopNav обновлён: {formatted_title}")
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

        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            app.top_nav._show_back_button()
            if self.term_name:
                self._update_top_nav(self.term_name)
            else:
                app.top_nav.set_custom_title("Термин")

        if self.term_name:
            Clock.schedule_once(self._scroll_to_top, 0.2)

        if hasattr(self, '_top_spacer_term'):
            top_padding = layout_config.get_top_padding()
            if platform == 'android':
                top_padding = top_padding + dp(16)
            self._top_spacer_term.height = top_padding

    def on_leave(self):
        """При выходе с экрана"""
        logger.info("Выход из экрана определения термина")

        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            app.top_nav.reset_to_default()