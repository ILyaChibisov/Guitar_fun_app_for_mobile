# screens/term_detail_screen.py
"""
Экран определения термина — в стиле song_detail_screen.
BottomNav всегда виден, панель настроек над текстом.
Адаптирован под 3 темы и 6 языков.
"""
from kivy.metrics import dp, sp
from kivy.graphics import Color, Rectangle
from kivy.core.image import Image as CoreImage
from kivy.clock import Clock
from io import BytesIO
from kivy.utils import platform

from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDIconButton
from kivymd.app import MDApp
from kivy.uix.widget import Widget
from kivymd.uix.scrollview import MDScrollView

from config.logger_config import screen_logger
from config.layout_config import layout_config
from screens.base_screen import BaseScreen
from utils.settings_manager import settings_manager
from utils.localization import get_text

logger = screen_logger('TermDetail')

try:
    from data import load_asset_as_bytes
    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False

    def load_asset_as_bytes(name):
        return None


# ============================================================
# ЦВЕТА ДЛЯ ЭКРАНА
# ============================================================

class DetailColors:
    @staticmethod
    def get_accent(theme_id):
        if theme_id == 'light':
            return [0.1, 0.55, 0.3, 1]
        elif theme_id == 'dark':
            return [1.0, 0.5, 0.0, 1]
        else:
            return [0.46, 0.70, 0.71, 1]

    @staticmethod
    def get_text_primary(theme_id):
        if theme_id == 'light':
            return [0.1, 0.1, 0.1, 0.95]
        return [1, 1, 1, 0.95]

    @staticmethod
    def get_text_secondary(theme_id):
        if theme_id == 'light':
            return [0.4, 0.4, 0.4, 1]
        return [1, 1, 1, 0.7]

    @staticmethod
    def get_panel_bg(theme_id):
        if theme_id == 'light':
            return [1, 1, 1, 0.9]
        elif theme_id == 'dark':
            return [1, 1, 1, 0.08]
        return [0, 0, 0, 0.06]

    @staticmethod
    def get_divider(theme_id):
        if theme_id == 'light':
            return [0, 0, 0, 0.1]
        return [0.5, 0.5, 0.5, 0.3]


class IconActionButton(MDIconButton):
    """Кнопка действия в панели."""

    def __init__(self, icon_name, on_press_callback=None, icon_color=None, **kwargs):
        super().__init__(**kwargs)
        self.on_press_callback = on_press_callback
        self.size_hint = (1, None)
        self.height = dp(40)
        self.theme_icon_color = "Custom"
        self.icon_color = icon_color if icon_color else [0.5, 0.5, 0.5, 0.9]
        self.md_bg_color = [0, 0, 0, 0]
        self.icon = icon_name
        self.bind(on_release=self._on_press)

    def _on_press(self, instance):
        if self.on_press_callback:
            self.on_press_callback()


class TermDetailScreen(BaseScreen):
    """Экран определения термина — в стиле song_detail_screen."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'term_detail'
        self._manage_padding_manually = True

        self.bg_image = None
        self.bg_color_inst = None
        self.bg_rect = None
        self.texture = None
        self.term_name = None
        self.term_data = None
        self.previous_screen = 'dictionary'

        if platform == 'android':
            self.STANDARD_FONT_SIZE = 42
            self.MIN_FONT_SIZE = 30
            self.MAX_FONT_SIZE = 60
            self._font_sizes = [30, 34, 38, 42, 46, 50, 54, 58, 60]
        else:
            self.STANDARD_FONT_SIZE = 20
            self.MIN_FONT_SIZE = 14
            self.MAX_FONT_SIZE = 32
            self._font_sizes = [14, 16, 18, 20, 22, 24, 26, 28, 30, 32]
        self.current_font_size = self.STANDARD_FONT_SIZE

        self.panel_container = None
        self.current_panel_type = 'main'

        self.load_background()
        self.init_ui()
        logger.info('Экран определения термина создан')

    # ============ ФОН ============

    def load_background(self):
        with self.canvas.before:
            self.bg_color_inst = Color(0, 0, 0, 0)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_rect, size=self._update_rect)
        try:
            if HAS_ASSETS:
                for name in ["background_jpg", "background", "bg", "BACKGROUND_JPG"]:
                    bg_data = load_asset_as_bytes(name)
                    if bg_data:
                        img = CoreImage(BytesIO(bg_data), ext="jpg")
                        self.texture = img.texture
                        logger.info(f"Фон загружен: {name}")
                        break
        except Exception as e:
            logger.error(f'Ошибка загрузки фона: {e}')
        self.update_screen_background()

    def _update_rect(self, *args):
        if hasattr(self, 'bg_rect') and self.bg_rect:
            self.bg_rect.pos = self.pos
            self.bg_rect.size = self.size

    def update_screen_background(self):
        if not hasattr(self, 'bg_color_inst') or not hasattr(self, 'bg_rect'):
            return
        theme_id = settings_manager.theme
        if theme_id == 'green':
            if self.texture:
                self.bg_rect.texture = self.texture
                self.bg_color_inst.rgba = (1, 1, 1, 1)
            else:
                self.bg_rect.texture = None
                self.bg_color_inst.rgba = (0.1, 0.3, 0.2, 1)
        elif theme_id == 'dark':
            self.bg_rect.texture = None
            self.bg_color_inst.rgba = (0.07, 0.07, 0.07, 1)
        elif theme_id == 'light':
            self.bg_rect.texture = None
            self.bg_color_inst.rgba = (0.969, 0.976, 0.969, 1)

    # ============ ТЕМА / ЯЗЫК ============

    def update_theme_colors(self):
        self.update_screen_background()
        theme_id = settings_manager.theme
        text_p = DetailColors.get_text_primary(theme_id)
        div_color = DetailColors.get_divider(theme_id)
        panel_bg = DetailColors.get_panel_bg(theme_id)

        if hasattr(self, 'content_label'):
            self.content_label.text_color = text_p
        if hasattr(self, 'term_title_label'):
            self.term_title_label.text_color = text_p
        for div in (getattr(self, 'top_divider', None),
                    getattr(self, 'panel_divider', None),
                    getattr(self, 'bottom_divider', None)):
            if div:
                div.md_bg_color = div_color
        if self.panel_container:
            self.panel_container.md_bg_color = panel_bg
        self._create_main_panel()

    def update_language(self):
        self._update_top_nav()

    def _toggle_theme(self, *args):
        """Переключение глобальной темы через settings_manager."""
        order = ['green', 'light', 'dark']
        cur = settings_manager.theme
        try:
            idx = order.index(cur)
        except ValueError:
            idx = 0
        new_theme = order[(idx + 1) % len(order)]
        settings_manager.theme = new_theme
        logger.info(f"Тема изменена на: {new_theme}")
        app = MDApp.get_running_app()
        if app and hasattr(app, 'apply_theme'):
            app.apply_theme()
        else:
            self.update_theme_colors()

    # ============ UI ============

    def init_ui(self):
        main_container = MDBoxLayout(orientation='vertical', size_hint=(1, 1))
        top_padding_for_nav = layout_config.get_top_padding(include_top_nav=True)
        bottom_padding_for_card = layout_config.get_bottom_padding()

        card_container = MDBoxLayout(
            orientation='vertical', size_hint=(1, 1),
            padding=[0, top_padding_for_nav, 0, 0]
        )

        self.term_card = MDCard(
            orientation='vertical', size_hint=(1, 1),
            padding=[0, 0, 0, bottom_padding_for_card], spacing=0,
            radius=[0, 0, 0, 0], md_bg_color=[0, 0, 0, 0], elevation=0
        )

        self.top_divider = MDBoxLayout(
            orientation='horizontal', size_hint=(1, None), height=dp(2)
        )
        self.term_card.add_widget(self.top_divider)

        self.panel_container = MDCard(
            orientation='vertical', size_hint=(1, None), height=dp(52),
            elevation=0, radius=[0, 0, 0, 0], padding=[0, 0, 0, 0], spacing=0
        )
        self.term_card.add_widget(self.panel_container)

        self.panel_divider = MDBoxLayout(
            orientation='horizontal', size_hint=(1, None), height=dp(2)
        )
        self.term_card.add_widget(self.panel_divider)

        self.content_scroll = MDScrollView(
            size_hint=(1, 1), do_scroll_x=False, bar_width=3,
            bar_color=[0.5, 0.5, 0.5, 0.3],
            bar_inactive_color=[0.5, 0.5, 0.5, 0.1]
        )

        self._text_container = MDBoxLayout(
            orientation='vertical', size_hint_y=None, spacing=4,
            padding=[dp(16), dp(16), dp(16), dp(8)],
            adaptive_height=True, md_bg_color=[0, 0, 0, 0]
        )

        self.term_title_label = MDLabel(
            text="", font_size=self.current_font_size + dp(6),
            size_hint_y=None, height=dp(50),
            theme_text_color="Custom", bold=True,
            valign="middle", halign="center", shorten=False
        )
        self._text_container.add_widget(self.term_title_label)

        self.content_label = MDLabel(
            text="", font_size=self.current_font_size,
            size_hint_y=None, theme_text_color="Custom",
            valign="top", halign="left", line_height=1.6
        )
        self.content_label.bind(texture_size=self._update_content_height)
        self._text_container.add_widget(self.content_label)

        self.content_scroll.add_widget(self._text_container)
        self.term_card.add_widget(self.content_scroll)

        self.bottom_divider = MDBoxLayout(
            orientation='horizontal', size_hint=(1, None), height=dp(2)
        )
        self.term_card.add_widget(self.bottom_divider)

        card_container.add_widget(self.term_card)
        main_container.add_widget(card_container)
        self.add_widget(main_container)

        self._create_main_panel()
        Clock.schedule_once(lambda dt: self.update_theme_colors(), 0.2)
        logger.info("TermDetailScreen: init_ui completed")

    # ============ ПАНЕЛЬ ============

    def _create_main_panel(self):
        if not self.panel_container:
            return
        self.panel_container.clear_widgets()
        theme_id = settings_manager.theme
        accent = DetailColors.get_accent(theme_id)

        panel = MDBoxLayout(
            orientation='horizontal', size_hint=(1, 1),
            padding=[dp(4), dp(2), dp(4), dp(2)], spacing=dp(2)
        )

        center_container = MDBoxLayout(
            orientation='vertical', size_hint_x=1, spacing=0
        )
        from kivymd.uix.slider import MDSlider

        total_steps = len(self._font_sizes) - 1
        current_slider_value = self._size_to_slider(self.current_font_size)

        top_row = MDBoxLayout(
            orientation='horizontal', size_hint=(1, None), height=dp(14), spacing=0
        )
        top_row.add_widget(MDLabel(text="", size_hint_x=None, width=dp(2)))
        self.font_value_label = MDLabel(
            text=self._get_font_multiplier(self.current_font_size),
            font_size=sp(10), halign="center", valign="bottom",
            size_hint_x=1, theme_text_color="Custom",
            text_color=accent, bold=True
        )
        top_row.add_widget(self.font_value_label)
        top_row.add_widget(MDLabel(text="", size_hint_x=None, width=dp(2)))

        slider_container = MDBoxLayout(
            orientation='horizontal', size_hint_x=1, size_hint_y=None,
            height=dp(28), padding=[dp(2), 0, dp(2), 0]
        )
        self.font_slider = MDSlider(
            min=-0.01, max=float(total_steps + 0.01),
            value=current_slider_value, step=1,
            size_hint_x=1, size_hint_y=None, height=dp(28), hint=False
        )
        self.font_slider.ripple_scale = 0
        self.font_slider.thumb_color_active = accent
        self.font_slider.thumb_color_inactive = accent
        self.font_slider.thumb_color_disabled = accent
        self.font_slider.track_color_active = accent[:3] + [0.6]
        self.font_slider.track_color_inactive = [1, 1, 1, 0.3]
        self.font_slider.color = accent

        def on_slider_change(instance, value):
            int_value = max(0, min(total_steps, int(round(value))))
            if self.font_slider.value != int_value:
                self.font_slider.value = int_value
            self.font_slider.thumb_color_active = accent
            self.font_slider.thumb_color_inactive = accent
            self.font_slider.thumb_color_disabled = accent
            new_size = self._slider_to_size(int_value)
            if self.current_font_size != new_size:
                self.current_font_size = new_size
                self.font_value_label.text = self._get_font_multiplier(new_size)
                if hasattr(self, 'term_title_label'):
                    self.term_title_label.font_size = self.current_font_size + dp(6)
                if hasattr(self, 'content_label'):
                    self.content_label.font_size = self.current_font_size
                    self._update_content_height()
                for delay in [0.0, 0.01, 0.03, 0.05, 0.08, 0.12, 0.2, 0.3]:
                    Clock.schedule_once(
                        lambda dt: setattr(self.content_scroll, 'scroll_y', 1.0),
                        delay
                    )

        self.font_slider.bind(value=on_slider_change)
        slider_container.add_widget(self.font_slider)
        center_container.add_widget(top_row)
        center_container.add_widget(slider_container)

        self.theme_btn = IconActionButton(
            "weather-sunny", self._toggle_theme, accent
        )
        self.theme_btn.size_hint = (None, None)
        self.theme_btn.size = (dp(36), dp(36))

        panel.add_widget(center_container)
        panel.add_widget(self.theme_btn)

        self.panel_container.add_widget(panel)
        self.current_panel_type = 'main'

        Clock.schedule_once(lambda dt: self._fix_slider_thumb(self.font_slider), 0.1)
        Clock.schedule_once(lambda dt: self._fix_slider_thumb(self.font_slider), 0.3)

    # ============ ХЕЛПЕРЫ ============

    def _size_to_slider(self, size):
        try:
            return self._font_sizes.index(size)
        except ValueError:
            return self._font_sizes.index(
                min(self._font_sizes, key=lambda x: abs(x - size))
            )

    def _slider_to_size(self, slider_value):
        idx = max(0, min(len(self._font_sizes) - 1, int(round(slider_value))))
        return self._font_sizes[idx]

    def _fix_slider_thumb(self, slider):
        if slider:
            accent = DetailColors.get_accent(settings_manager.theme)
            slider.thumb_color_active = accent
            slider.thumb_color_inactive = accent
            slider.thumb_color_disabled = accent
            current = slider.value
            slider.value = current + 0.01
            Clock.schedule_once(lambda dt: setattr(slider, 'value', current), 0.01)

    def _get_font_multiplier(self, font_size):
        ratio = round(font_size / self.STANDARD_FONT_SIZE * 10) / 10
        return f"{int(ratio)}x" if ratio == int(ratio) else f"{ratio:.1f}x"

    def _update_content_height(self, *args):
        if not self.content_label.texture:
            Clock.schedule_once(lambda dt: self._update_content_height(), 0.05)
            return
        text_height = self.content_label.texture_size[1]
        title_height = (
            self.term_title_label.texture_size[1]
            if self.term_title_label.text else dp(20)
        )
        self.content_label.height = max(dp(50), text_height + dp(8))
        self.term_title_label.height = max(dp(40), title_height + dp(8))
        total_height = self.term_title_label.height + self.content_label.height + dp(16)
        if self.content_label.parent:
            self.content_label.parent.height = total_height
            if hasattr(self.content_label.parent, 'minimum_height'):
                self.content_label.parent.minimum_height = total_height
        self.content_scroll.scroll_y = 1.0

    def _reset_to_defaults(self):
        self.current_font_size = self.STANDARD_FONT_SIZE
        if hasattr(self, 'term_title_label'):
            self.term_title_label.font_size = self.current_font_size + dp(6)
        if hasattr(self, 'content_label'):
            self.content_label.font_size = self.current_font_size
            self._update_content_height()
        if hasattr(self, 'font_value_label'):
            self.font_value_label.text = self._get_font_multiplier(self.current_font_size)
        if hasattr(self, 'font_slider'):
            self.font_slider.value = self._size_to_slider(self.current_font_size)
        if hasattr(self, 'term_title_label'):
            self.term_title_label.text = ""

    def _clean_description(self, text):
        if not text:
            return ""
        lines = text.split('\n')
        while lines and not lines[0].strip():
            lines.pop(0)
        while lines and not lines[-1].strip():
            lines.pop()
        return '\n'.join(lines)

    def set_term(self, term_name, term_data, previous_screen='dictionary'):
        """Устанавливает термин для отображения."""
        self._reset_to_defaults()
        self.term_name = term_name
        self.term_data = term_data
        self.previous_screen = previous_screen

        logger.info(f"Установлен термин: {term_name}")

        formatted_title = term_name.capitalize() if term_name else get_text('dictionary')
        self.term_title_label.text = formatted_title

        description = term_data.get('description') or get_text('term_not_found')
        description = self._clean_description(description)
        self.content_label.text = description

        self._update_top_nav()
        Clock.schedule_once(self._scroll_to_top, 0.1)
        Clock.schedule_once(self._scroll_to_top, 0.3)

    def _scroll_to_top(self, dt):
        if hasattr(self, 'content_scroll'):
            self.content_scroll.scroll_y = 1.0

    def _update_top_nav(self):
        try:
            app = MDApp.get_running_app()
            if app and hasattr(app, 'top_nav'):
                app.top_nav.set_custom_title(get_text('dictionary'))
                app.top_nav.back_btn.on_release = self.go_back
                logger.info("TopNav обновлён: Термин")
        except Exception as e:
            logger.error(f"Ошибка обновления TopNav: {e}")

    def go_back(self, instance=None):
        logger.info(f"Возврат на {self.previous_screen}")
        if hasattr(self, 'manager') and self.manager:
            if self.manager.has_screen(self.previous_screen):
                self.manager.current = self.previous_screen
            else:
                self.manager.current = 'dictionary'

    def on_enter(self):
        logger.info("Вход в экран определения термина")
        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            app.top_nav.set_custom_title(get_text('dictionary'))
            app.top_nav.back_btn.on_release = self.go_back
        if self.term_name:
            Clock.schedule_once(self._scroll_to_top, 0.2)
        self.update_theme_colors()

    def on_leave(self):
        logger.info("Выход из экрана определения термина")