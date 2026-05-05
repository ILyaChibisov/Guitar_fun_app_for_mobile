# screens/admin_screen.py
"""
Экран администратора
"""
from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from kivy.metrics import dp, sp
from kivy.graphics import Color, Rectangle
from kivy.core.image import Image as CoreImage
from kivy.uix.widget import Widget
from io import BytesIO

from config.theme import theme
from config.logger_config import screen_logger
from utils.notifications import notify

logger = screen_logger('AdminScreen')

# Попытка импорта ассетов
try:
    from data import load_asset_as_bytes
    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False
    def load_asset_as_bytes(name):
        return None


class AdminCard(MDCard):
    """Карточка администратора как в artist_songs_screen"""

    def __init__(self, icon_text, title, on_click=None, **kwargs):
        super().__init__(**kwargs)
        self.on_click_callback = on_click

        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = dp(55)
        self.padding = [dp(16), dp(8), dp(16), dp(8)]
        self.spacing = dp(12)
        self.radius = [theme.CORNER_RADIUS_SMALL]
        self.elevation = 2
        self.ripple_behavior = True

        self.theme_bg_color = "Custom"
        self.md_bg_color = [0, 0, 0, 0.15]
        self.line_color = [1, 1, 1, 0.1]
        self.line_width = 1

        self.icon_label = MDLabel(
            text=icon_text,
            font_size=sp(24),
            size_hint_x=None,
            width=dp(40),
            halign="center",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.9]
        )

        self.title_label = MDLabel(
            text=title,
            font_size=sp(15),
            size_hint_x=1,
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.95],
            bold=True,
            valign="middle",
            shorten=True,
            shorten_from="right"
        )

        self.arrow_label = MDLabel(
            text="›",
            font_size=sp(24),
            size_hint_x=None,
            width=dp(32),
            halign="center",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.6]
        )

        self.add_widget(self.icon_label)
        self.add_widget(self.title_label)
        self.add_widget(self.arrow_label)

        self.bind(on_release=self.on_click)

    def on_click(self, instance):
        if self.on_click_callback:
            self.on_click_callback()


class AdminScreen(MDScreen):
    """Экран администратора"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'admin'
        self.bg_image = None
        self.md_bg_color = [0, 0, 0, 0]
        self.init_ui()
        self.load_background()
        logger.info('Экран администратора создан')

    def load_background(self):
        """Загружает фоновое изображение"""
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
        scroll = MDScrollView(size_hint=(1, 1), do_scroll_x=False)

        # Основной контейнер
        main_layout = MDBoxLayout(
            orientation='vertical',
            padding=[dp(16), dp(2), dp(16), dp(16)],
            spacing=dp(8),
            size_hint_y=None
        )
        main_layout.bind(minimum_height=main_layout.setter('height'))

        # Отступ сверху для компенсации верхней панели
        top_spacer = Widget(size_hint_y=None, height=dp(65))
        main_layout.add_widget(top_spacer)

        # Заголовок
        title_label = MDLabel(
            text="Админ панель",
            font_size=sp(24),
            halign="center",
            size_hint_y=None,
            height=dp(50),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
            bold=True
        )
        main_layout.add_widget(title_label)

        # ============ КАРТОЧКА СТАТИСТИКИ ============
        stats_card = MDCard(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(110),
            padding=[dp(16), dp(12), dp(16), dp(12)],
            spacing=dp(8),
            radius=[theme.CORNER_RADIUS_SMALL],
            md_bg_color=[0, 0, 0, 0.15],
            elevation=2,
            line_color=[1, 1, 1, 0.1],
            line_width=1
        )

        # Заголовок карточки статистики
        stats_header = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(40),
            spacing=dp(12)
        )

        stats_icon = MDLabel(
            text="📊",
            font_size=sp(24),
            size_hint_x=None,
            width=dp(40),
            halign="center",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.9]
        )

        stats_title = MDLabel(
            text="Статистика",
            font_size=sp(16),
            size_hint_x=1,
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.95],
            bold=True,
            valign="middle"
        )

        stats_header.add_widget(stats_icon)
        stats_header.add_widget(stats_title)

        # Разделитель
        divider = Widget(size_hint_y=None, height=dp(1))
        with divider.canvas:
            Color(1, 1, 1, 0.1)
            divider_rect = Rectangle(pos=divider.pos, size=divider.size)
        divider.bind(pos=self._update_divider, size=self._update_divider)
        divider.rect = divider_rect

        # Контент статистики
        stats_content = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(36),
            spacing=dp(16)
        )

        users_label = MDLabel(
            text="Зарегистрировано пользователей:",
            font_size=sp(13),
            size_hint_x=0.7,
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.8]
        )

        self.stats_count_label = MDLabel(
            text="123",
            font_size=sp(22),
            size_hint_x=0.3,
            theme_text_color="Custom",
            text_color=[0.46, 0.70, 0.71, 1],
            bold=True,
            halign="right"
        )

        stats_content.add_widget(users_label)
        stats_content.add_widget(self.stats_count_label)

        stats_card.add_widget(stats_header)
        stats_card.add_widget(divider)
        stats_card.add_widget(stats_content)

        main_layout.add_widget(stats_card)

        # ============ КАРТОЧКИ ПАРСЕРОВ ============

        # 1. AmDm парсер
        amdm_card = AdminCard(
            icon_text="🎵",
            title="AmDm парсер",
            on_click=self.open_amdm_parser
        )
        main_layout.add_widget(amdm_card)

        # 2. MyTabs парсер
        mytabs_card = AdminCard(
            icon_text="🎸",
            title="MyTabs парсер",
            on_click=self.open_mytabs_parser
        )
        main_layout.add_widget(mytabs_card)

        # 3. Akkords.Pro парсер
        accordpro_card = AdminCard(
            icon_text="🎹",
            title="Akkords.Pro парсер",
            on_click=self.open_accord_pro_parser
        )
        main_layout.add_widget(accordpro_card)

        # 4. Akkordus.Ru парсер
        akkordus_card = AdminCard(
            icon_text="🎤",
            title="Akkordus.Ru парсер",
            on_click=self.open_akkordus_parser
        )
        main_layout.add_widget(akkordus_card)

        # 5. Muzland.Ru парсер
        muzland_card = AdminCard(
            icon_text="🎻",
            title="Muzland.Ru парсер",
            on_click=self.open_muzland_parser
        )
        main_layout.add_widget(muzland_card)

        # 6. Chordie.com парсер
        chordie_card = AdminCard(
            icon_text="🎼",
            title="Chordie.com парсер",
            on_click=self.open_chordie_parser
        )
        main_layout.add_widget(chordie_card)

        # 7. 5Lad.Net парсер
        fivelad_card = AdminCard(
            icon_text="🎸",
            title="5Lad.Net парсер",
            on_click=self.open_fivelad_parser
        )
        main_layout.add_widget(fivelad_card)

        # 8. AkkordBard.Ru парсер
        akkordbard_card = AdminCard(
            icon_text="🎵",
            title="AkkordBard.Ru парсер",
            on_click=self.open_akkordbard_parser
        )
        main_layout.add_widget(akkordbard_card)

        # 9. Domhve.com парсер (христианские)
        domhve_card = AdminCard(
            icon_text="⛪",
            title="Domhve.com парсер",
            on_click=self.open_domhve_parser
        )
        main_layout.add_widget(domhve_card)

        # 10. Rush-Sound.ru парсер
        rushsound_card = AdminCard(
            icon_text="⚡",
            title="Rush-Sound.ru парсер",
            on_click=self.open_rushsound_parser
        )
        main_layout.add_widget(rushsound_card)

        # ============ КАРТОЧКА ОЧИСТКИ КЭША ============
        clear_cache_card = AdminCard(
            icon_text="🗑️",
            title="Очистить кэш",
            on_click=self.clear_cache
        )
        main_layout.add_widget(clear_cache_card)

        # Нижний отступ
        bottom_spacer = Widget(size_hint_y=None, height=dp(80))
        main_layout.add_widget(bottom_spacer)

        scroll.add_widget(main_layout)
        self.add_widget(scroll)

        self.divider = divider

    def _update_divider(self, instance, *args):
        """Обновляет позицию разделителя"""
        if hasattr(instance, 'rect'):
            instance.rect.pos = instance.pos
            instance.rect.size = instance.size

    # ============ НАВИГАЦИЯ К ПАРСЕРАМ ============

    def open_amdm_parser(self):
        """Открывает экран парсера AmDm"""
        try:
            self.manager.current = 'amdm_parser'
            logger.info("Переход на экран AmDm парсера")
        except Exception as e:
            logger.error(f"Ошибка перехода на AmDm парсер: {e}")
            notify.error("Ошибка перехода")

    def open_mytabs_parser(self):
        """Открывает экран парсера MyTabs"""
        try:
            self.manager.current = 'mytabs_parser'
            logger.info("Переход на экран MyTabs парсера")
            notify.success("MyTabs парсер")
        except Exception as e:
            logger.error(f"Ошибка перехода на MyTabs парсер: {e}")
            notify.error("Ошибка перехода")

    def open_accord_pro_parser(self):
        """Открывает экран парсера Akkords.Pro"""
        try:
            self.manager.current = 'accord_pro_parser'
            logger.info("Переход на экран Akkords.Pro парсера")
            notify.success("Akkords.Pro парсер")
        except Exception as e:
            logger.error(f"Ошибка перехода на Akkords.Pro парсер: {e}")
            notify.error("Ошибка перехода")

    def open_akkordus_parser(self):
        """Открывает экран парсера Akkordus.Ru"""
        try:
            self.manager.current = 'akkordus_parser'
            logger.info("Переход на экран Akkordus.Ru парсера")
            notify.success("Akkordus.Ru парсер")
        except Exception as e:
            logger.error(f"Ошибка перехода на Akkordus.Ru парсер: {e}")
            notify.error("Ошибка перехода")

    def open_muzland_parser(self):
        """Открывает экран парсера Muzland.Ru"""
        try:
            self.manager.current = 'muzland_parser'
            logger.info("Переход на экран Muzland.Ru парсера")
            notify.success("Muzland.Ru парсер")
        except Exception as e:
            logger.error(f"Ошибка перехода на Muzland.Ru парсер: {e}")
            notify.error("Ошибка перехода")

    def open_chordie_parser(self):
        """Открывает экран парсера Chordie.com"""
        try:
            self.manager.current = 'chordie_parser'
            logger.info("Переход на экран Chordie.com парсера")
            notify.success("Chordie.com парсер")
        except Exception as e:
            logger.error(f"Ошибка перехода на Chordie.com парсер: {e}")
            notify.error("Ошибка перехода")

    def open_fivelad_parser(self):
        """Открывает экран парсера 5Lad.Net"""
        try:
            self.manager.current = 'fivelad_parser'
            logger.info("Переход на экран 5Lad.Net парсера")
            notify.success("5Lad.Net парсер")
        except Exception as e:
            logger.error(f"Ошибка перехода на 5Lad.Net парсер: {e}")
            notify.error("Ошибка перехода")

    def open_akkordbard_parser(self):
        """Открывает экран парсера AkkordBard.Ru"""
        try:
            self.manager.current = 'akkordbard_parser'
            logger.info("Переход на экран AkkordBard.Ru парсера")
            notify.success("AkkordBard.Ru парсер")
        except Exception as e:
            logger.error(f"Ошибка перехода на AkkordBard.Ru парсер: {e}")
            notify.error("Ошибка перехода")

    def open_domhve_parser(self):
        """Открывает экран парсера Domhve.com"""
        try:
            self.manager.current = 'domhve_parser'
            logger.info("Переход на экран Domhve.com парсера")
            notify.success("Domhve.com парсер")
        except Exception as e:
            logger.error(f"Ошибка перехода на Domhve.com парсер: {e}")
            notify.error("Ошибка перехода")

    def open_rushsound_parser(self):
        """Открывает экран парсера Rush-Sound.ru"""
        try:
            self.manager.current = 'rushsound_parser'
            logger.info("Переход на экран Rush-Sound.ru парсера")
            notify.success("Rush-Sound.ru парсер")
        except Exception as e:
            logger.error(f"Ошибка перехода на Rush-Sound.ru парсер: {e}")
            notify.error("Ошибка перехода")

    def clear_cache(self):
        """Очищает кэш API"""
        try:
            from api.client import api
            api.clear_cache()
            logger.info("Кэш очищен")
            notify.success("Кэш очищен")
        except Exception as e:
            logger.error(f"Ошибка очистки кэша: {e}")
            notify.error("Ошибка очистки кэша")

    def on_enter(self):
        """При входе на экран"""
        logger.info("Вход в админ панель")
        self._load_stats()

    def _load_stats(self):
        """Загружает статистику пользователей"""
        try:
            from api.client import api
            api.get_current_user(
                on_success=self._on_user_data,
                on_failure=self._on_stats_error
            )
        except Exception as e:
            logger.error(f"Ошибка загрузки статистики: {e}")

    def _on_user_data(self, data):
        """Обновляет отображение статистики"""
        if data and isinstance(data, dict):
            try:
                from api.client import api
                api.get_all_users(
                    limit=1,
                    on_success=self._on_users_count,
                    on_failure=self._on_stats_error
                )
            except:
                self.stats_count_label.text = "admin"
        else:
            self.stats_count_label.text = "—"

    def _on_users_count(self, data):
        """Обновляет счетчик пользователей"""
        try:
            if data and isinstance(data, dict):
                total = data.get('total', data.get('count', len(data.get('users', []))))
                if total > 0:
                    self.stats_count_label.text = str(total)
                else:
                    self.stats_count_label.text = "—"
            else:
                self.stats_count_label.text = "—"
        except Exception as e:
            logger.error(f"Ошибка обновления статистики: {e}")
            self.stats_count_label.text = "—"

    def _on_stats_error(self, req, error):
        """Обработка ошибки загрузки статистики"""
        logger.error(f"Ошибка загрузки статистики: {error}")
        self.stats_count_label.text = "—"