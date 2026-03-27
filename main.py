# main.py
"""
Главный файл приложения GuitarFuns
С верхней панелью и нижней навигацией
"""
import os
from kivy.core.window import Window
from kivy.metrics import dp, sp

# Настройка логирования
from config.logger_config import setup_logging, app_logger

setup_logging(level='debug')

# Импорты KivyMD
from kivymd.app import MDApp
from kivymd.uix.label import MDLabel
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDIconButton, MDFlatButton, MDRaisedButton
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.dialog import MDDialog
from kivymd.uix.snackbar import Snackbar
from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem

# Наши модули
from config.app_config import config
from config.theme import theme
from api.client import api

# Настройка окна для разработки
if os.name == 'nt':
    Window.size = (400, 750)
    Window.top = 50
    Window.left = 50

logger = app_logger()


class LanguageSelector(MDBoxLayout):
    """Компонент выбора языка"""

    def __init__(self, current_lang="ru", on_change_callback=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint = (None, 1)
        self.width = dp(100)
        self.spacing = dp(4)
        self.current_lang = current_lang
        self.on_change_callback = on_change_callback

        self.lang_icons = {
            "ru": "language-russian", "en": "alphabet-latin", "de": "alphabet-latin",
            "fr": "alphabet-latin", "it": "alphabet-latin", "pt": "alphabet-latin", "zh": "alphabet-chinese"
        }

        self.lang_codes = {
            "ru": "RU", "en": "EN", "de": "DE", "fr": "FR", "it": "IT", "pt": "PT", "zh": "中文"
        }

        self.button_container = MDBoxLayout(
            orientation='horizontal', size_hint=(1, 1), spacing=dp(4),
            md_bg_color=theme.PRIMARY_LIGHT, radius=[dp(8), dp(8), dp(8), dp(8)],
            padding=[dp(8), dp(4), dp(8), dp(4)]
        )

        self.current_icon = MDIconButton(
            icon=self.lang_icons.get(current_lang, "translate"),
            theme_text_color="Custom", text_color=[1, 1, 1, 1],
            size_hint=(None, 1), width=dp(28), md_bg_color=[0, 0, 0, 0]
        )

        self.current_code = MDLabel(
            text=self.lang_codes[current_lang], font_size=sp(11),
            size_hint=(None, 1), width=dp(36), halign="center", valign="middle",
            bold=True, theme_text_color="Custom", text_color=[1, 1, 1, 1]
        )

        self.arrow = MDIconButton(
            icon="chevron-down", theme_text_color="Custom", text_color=[1, 1, 1, 1],
            size_hint=(None, 1), width=dp(24), md_bg_color=[0, 0, 0, 0]
        )

        self.button_container.add_widget(self.current_icon)
        self.button_container.add_widget(self.current_code)
        self.button_container.add_widget(self.arrow)
        self.add_widget(self.button_container)
        self.button_container.bind(on_touch_down=self.on_click)
        self.create_language_menu()

    def create_language_menu(self):
        languages = [
            {"code": "ru", "name": "Русский", "icon": "language-russian"},
            {"code": "en", "name": "English", "icon": "alphabet-latin"},
            {"code": "de", "name": "Deutsch", "icon": "alphabet-latin"},
            {"code": "fr", "name": "Français", "icon": "alphabet-latin"},
            {"code": "it", "name": "Italiano", "icon": "alphabet-latin"},
            {"code": "pt", "name": "Português", "icon": "alphabet-latin"},
            {"code": "zh", "name": "中文", "icon": "alphabet-chinese"}
        ]
        menu_items = []
        for lang in languages:
            is_current = (lang["code"] == self.current_lang)
            menu_items.append({
                "text": lang["name"], "viewclass": "OneLineListItem",
                "on_release": lambda x=lang["code"]: self.change_language(x),
                "theme_text_color": "Primary" if is_current else "Secondary",
                "left_icon": lang["icon"]
            })
        self.language_menu = MDDropdownMenu(
            caller=self.button_container, items=menu_items, width=dp(180),
            max_height=dp(400), position="bottom", radius=[theme.CORNER_RADIUS_SMALL]
        )

    def on_click(self, instance, touch):
        if self.button_container.collide_point(*touch.pos):
            self.open_language_menu()
            return True
        return False

    def open_language_menu(self):
        self.language_menu.open()

    def change_language(self, lang_code):
        self.current_lang = lang_code
        self.current_icon.icon = self.lang_icons.get(lang_code, "translate")
        self.current_code.text = self.lang_codes.get(lang_code, lang_code.upper())
        self.language_menu.dismiss()
        if self.on_change_callback:
            self.on_change_callback(lang_code)


class GuitarFunsApp(MDApp):
    """Главный класс приложения"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "GuitarFuns"
        self.current_language = "ru"
        self.profile_dialog = None
        self.auth_dialog = None
        self.settings_dialog = None
        self.support_dialog = None
        self.language_selector = None
        self.home_screen = None  # Сохраняем ссылку на HomeScreen

        logger.info('🎸 ' + '=' * 50)
        logger.info(f'🎸 ЗАПУСК GuitarFuns v{config.VERSION}')
        logger.info('🎸 ' + '=' * 50)

    def build(self):
        logger.debug('Создание интерфейса...')

        self.theme_cls.primary_palette = "Teal"
        self.theme_cls.primary_hue = "300"
        self.theme_cls.theme_style = "Light"
        self.theme_cls.material_style = "M3"

        # Создаём нижнюю навигацию
        bottom_nav = self.create_bottom_navigation()

        from kivy.uix.floatlayout import FloatLayout
        root = FloatLayout()

        top_bar = self.create_top_bar()
        root.add_widget(top_bar)

        bottom_nav.size_hint = (1, 0.9)
        bottom_nav.pos_hint = {'y': 0}
        root.add_widget(bottom_nav)

        logger.info('Интерфейс успешно создан')
        return root

    def create_top_bar(self):
        top_bar = MDBoxLayout(
            orientation='horizontal', size_hint=(1, None), height=dp(60),
            padding=[theme.PADDING, 0, theme.PADDING, 0], spacing=theme.PADDING,
            md_bg_color=theme.PRIMARY, pos_hint={'top': 1}
        )

        logo = MDLabel(
            text="GuitarFuns", font_style="H6", size_hint_x=0.4,
            theme_text_color="Custom", text_color=[1, 1, 1, 1], bold=True
        )

        icons_container = MDBoxLayout(orientation='horizontal', size_hint_x=0.6, spacing=dp(8))

        profile_btn = MDIconButton(
            icon="account-circle", theme_text_color="Custom", text_color=[1, 1, 1, 1],
            on_release=self.open_profile
        )

        settings_btn = MDIconButton(
            icon="cog", theme_text_color="Custom", text_color=[1, 1, 1, 1],
            on_release=self.open_settings
        )

        support_btn = MDIconButton(
            icon="help-circle", theme_text_color="Custom", text_color=[1, 1, 1, 1],
            on_release=self.open_support
        )

        self.language_selector = LanguageSelector(
            current_lang="ru", on_change_callback=self.change_language
        )

        icons_container.add_widget(profile_btn)
        icons_container.add_widget(settings_btn)
        icons_container.add_widget(support_btn)
        icons_container.add_widget(self.language_selector)

        top_bar.add_widget(logo)
        top_bar.add_widget(icons_container)
        return top_bar

    def create_bottom_navigation(self):
        bottom_nav = MDBottomNavigation(
            size_hint=(1, 1), panel_color=[1, 1, 1, 1], selected_color_background=theme.PRIMARY
        )

        nav_items = [
            {"icon": "home", "text": "Главная", "screen": "home"},
            {"icon": "music-note", "text": "Песни", "screen": "songs"},
            {"icon": "guitar-acoustic", "text": "Аккорды", "screen": "chords"},
            {"icon": "book", "text": "Словарь", "screen": "dictionary"},
            {"icon": "tune", "text": "Тюнер", "screen": "tuner"},
            {"icon": "heart", "text": "Избранное", "screen": "favorites"}
        ]

        for item in nav_items:
            screen = MDScreen(name=item["screen"])
            if item["screen"] == "home":
                from screens.home_screen import HomeScreen
                self.home_screen = HomeScreen()  # Сохраняем ссылку
                content = self.home_screen
                screen.add_widget(content)
            elif item["screen"] == "songs":
                from screens.songs_screen import SongsScreen
                content = SongsScreen()
                screen.add_widget(content)
            elif item["screen"] == "chords":
                from screens.chords_screen import ChordsScreen
                content = ChordsScreen()
                screen.add_widget(content)
            elif item["screen"] == "dictionary":
                from screens.dictionary_screen import DictionaryScreen
                content = DictionaryScreen()
                screen.add_widget(content)
            elif item["screen"] == "tuner":
                from screens.tuner_screen import TunerScreen
                content = TunerScreen()
                screen.add_widget(content)
            elif item["screen"] == "favorites":
                from screens.favorites_screen import FavoritesScreen
                content = FavoritesScreen()
                screen.add_widget(content)

            nav_item = MDBottomNavigationItem(name=item["screen"], text=item["text"], icon=item["icon"])
            nav_item.add_widget(screen)
            bottom_nav.add_widget(nav_item)

        bottom_nav.switch_tab("home")
        return bottom_nav

    def open_profile(self, instance):
        """Открывает профиль - вызывает метод из HomeScreen"""
        logger.info("Нажата иконка личного кабинета")

        if self.home_screen and hasattr(self.home_screen, 'open_profile'):
            self.home_screen.open_profile()
        else:
            logger.warning("HomeScreen не найден или не имеет метода open_profile")

    def open_settings(self, instance):
        logger.info("Открыты настройки")
        if not self.settings_dialog:
            self.settings_dialog = MDDialog(
                title="⚙️ Настройки", text="Здесь будут настройки приложения",
                buttons=[MDFlatButton(text="ЗАКРЫТЬ", on_release=lambda x: self.settings_dialog.dismiss())]
            )
        self.settings_dialog.open()

    def open_support(self, instance):
        logger.info("Открыта поддержка")
        if not self.support_dialog:
            self.support_dialog = MDDialog(
                title="🆘 Поддержка",
                text="Свяжитесь с нами:\n\n📧 Email: support@guitarfuns.com\n\n📱 Telegram: @guitarfuns_bot",
                buttons=[MDFlatButton(text="ЗАКРЫТЬ", on_release=lambda x: self.support_dialog.dismiss())]
            )
        self.support_dialog.open()

    def change_language(self, lang_code):
        self.current_language = lang_code
        lang_names = {"ru": "Русский", "en": "English", "de": "Deutsch",
                      "fr": "Français", "it": "Italiano", "pt": "Português", "zh": "中文"}
        lang_name = lang_names.get(lang_code, lang_code)
        logger.info(f"Язык изменён на: {lang_name} ({lang_code})")
        Snackbar(text=f"Язык изменён на {lang_name}").open()

    def on_start(self):
        logger.info('Приложение GuitarFuns запущено')

    def on_pause(self):
        logger.debug('Приложение свернуто')
        return True

    def on_resume(self):
        logger.debug('Приложение восстановлено')

    def on_stop(self):
        logger.info('Приложение закрыто')


if __name__ == '__main__':
    GuitarFunsApp().run()