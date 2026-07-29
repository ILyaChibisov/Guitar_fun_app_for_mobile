# screens/splash_screen.py
"""
Кастомный экран загрузки приложения с фоном из ассетов
"""
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.metrics import dp, sp
from kivy.core.image import Image as CoreImage
from kivy.graphics import Color, Rectangle
from io import BytesIO

from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.spinner import MDSpinner
from kivymd.app import MDApp

from config.app_config import config
from config.logger_config import get_logger

logger = get_logger('SplashScreen')

try:
    from data import load_asset_as_bytes

    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False


    def load_asset_as_bytes(name):
        return None


class SplashScreen(FloatLayout):
    """
    Экран загрузки с фоном из ассетов
    """

    def __init__(self, on_complete=None, **kwargs):
        super().__init__(**kwargs)
        self.on_complete = on_complete
        self.size_hint = (1, 1)
        self._loading_complete = False

        # ============ ФОН ============
        # СНАЧАЛА чёрный фон-заглушка (чтобы не было белого экрана)
        with self.canvas.before:
            Color(0, 0, 0, 1)  # Чёрный фон
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_rect, size=self._update_rect)

        # ПОТОМ загружаем фон из ассета
        self.bg_image = None
        self._load_background()

        # ============ КОНТЕЙНЕР ДЛЯ КОНТЕНТА ============
        self.content = FloatLayout(size_hint=(1, 1))

        # ============ ЛОГОТИП (по центру) ============
        self.logo_image = Image(
            size_hint=(None, None),
            size=(dp(200), dp(100)),
            pos_hint={'center_x': 0.5, 'center_y': 0.58},
            allow_stretch=True,
            keep_ratio=True
        )
        self._load_logo()
        self.content.add_widget(self.logo_image)

        # ============ СПИННЕР (под логотипом) ============
        spinner_container = MDBoxLayout(
            size_hint=(None, None),
            size=(dp(60), dp(60)),
            pos_hint={'center_x': 0.5, 'center_y': 0.35},
            md_bg_color=[0, 0, 0, 0]
        )

        self.spinner = MDSpinner(
            size_hint=(None, None),
            size=(dp(48), dp(48)),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            active=True,
            color=[0.46, 0.70, 0.71, 1]  # Ваш фирменный зелёный
        )
        spinner_container.add_widget(self.spinner)
        self.content.add_widget(spinner_container)

        # ============ ТЕКСТ ЗАГРУЗКИ ============
        self.status_label = MDLabel(
            text="Загрузка...",
            font_size=sp(14),
            halign="center",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.8],
            size_hint=(1, None),
            height=dp(30),
            pos_hint={'center_x': 0.5, 'y': 0.25}
        )
        self.content.add_widget(self.status_label)

        # ============ ПРОГРЕСС-БАР ============
        from kivy.uix.progressbar import ProgressBar
        self.progress = ProgressBar(
            size_hint=(0.7, None),
            height=dp(4),
            pos_hint={'center_x': 0.5, 'y': 0.20},
            value=0,
            max=100
        )
        # Стилизуем прогресс-бар через canvas
        with self.progress.canvas.before:
            Color(0.2, 0.2, 0.2, 0.5)
            self.progress.bg_rect = Rectangle(pos=self.progress.pos, size=self.progress.size)
        with self.progress.canvas.after:
            Color(0.46, 0.70, 0.71, 1)  # Ваш фирменный зелёный
            self.progress.fg_rect = Rectangle(pos=self.progress.pos, size=(0, self.progress.height))

        # Обновляем прогресс-бар при изменении
        self.progress.bind(value=self._update_progress_bar)
        self.progress.bind(pos=self._update_progress_rects, size=self._update_progress_rects)

        self.content.add_widget(self.progress)

        # ============ ВЕРСИЯ ============
        version_label = MDLabel(
            text=f"Версия {config.VERSION}",
            font_size=sp(10),
            halign="center",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.3],
            size_hint=(1, None),
            height=dp(20),
            pos_hint={'center_x': 0.5, 'y': 0.02}
        )
        self.content.add_widget(version_label)

        # ============ ДОБАВЛЯЕМ КОНТЕНТ ============
        self.add_widget(self.content)

        # ============ АНИМАЦИЯ ПОЯВЛЕНИЯ ============
        self.opacity = 0
        anim = Animation(opacity=1, duration=0.5, t='out_quad')
        anim.start(self)

        # Начинаем имитацию загрузки
        Clock.schedule_once(self._start_loading, 0.3)

        logger.info("🚀 SplashScreen создан")

    def _update_rect(self, *args):
        """Обновляет позицию фона-заглушки"""
        if hasattr(self, 'bg_rect'):
            self.bg_rect.pos = self.pos
            self.bg_rect.size = self.size

    def _load_background(self):
        """Загружает фоновое изображение из ассетов"""
        try:
            if HAS_ASSETS:
                asset_names = ["background_jpg", "background", "bg", "BACKGROUND_JPG"]
                bg_data = None
                for name in asset_names:
                    bg_data = load_asset_as_bytes(name)
                    if bg_data:
                        logger.info(f"🖼️ Фон загружен из ассета: {name}")
                        break

                if bg_data:
                    img = CoreImage(BytesIO(bg_data), ext="jpg")
                    with self.canvas.before:
                        Color(1, 1, 1, 1)
                        self.bg_image = Rectangle(texture=img.texture, pos=self.pos, size=self.size)
                    self.bind(pos=self._update_bg, size=self._update_bg)
                    # Убираем чёрный фон-заглушку после загрузки ассета
                    if hasattr(self, 'bg_rect'):
                        self.canvas.before.remove(self.bg_rect)
                    logger.info("✅ Фон загружен из ассета")
                    return
        except Exception as e:
            logger.error(f'❌ Ошибка загрузки фона: {e}')

        # Если ассет не загрузился — оставляем чёрный фон
        logger.info("✅ Используем чёрный фон (ассет не найден)")

    def _update_bg(self, *args):
        """Обновляет позицию фонового изображения"""
        if self.bg_image:
            self.bg_image.pos = self.pos
            self.bg_image.size = self.size

    def _update_progress_rects(self, *args):
        """Обновляет позицию и размеры прогресс-бара"""
        if hasattr(self.progress, 'bg_rect'):
            self.progress.bg_rect.pos = self.progress.pos
            self.progress.bg_rect.size = self.progress.size
        if hasattr(self.progress, 'fg_rect'):
            self.progress.fg_rect.pos = self.progress.pos
            # Ширина зависит от значения
            width = (self.progress.value / self.progress.max) * self.progress.width
            self.progress.fg_rect.size = (width, self.progress.height)

    def _update_progress_bar(self, instance, value):
        """Обновляет визуальное отображение прогресс-бара"""
        if hasattr(self.progress, 'fg_rect'):
            width = (value / self.progress.max) * self.progress.width
            self.progress.fg_rect.size = (width, self.progress.height)

    def _load_logo(self):
        """Загружает логотип из ассетов"""
        if HAS_ASSETS:
            try:
                logo_data = load_asset_as_bytes("logo_name_png")
                if logo_data:
                    img = CoreImage(BytesIO(logo_data), ext="png")
                    self.logo_image.texture = img.texture
                    logger.info("✅ Логотип загружен")
                    return
            except Exception as e:
                logger.error(f"❌ Ошибка загрузки логотипа: {e}")

        # Fallback
        self.logo_image.text = "🎸 GuitarFuns"
        self.logo_image.color = [0.46, 0.70, 0.71, 1]

    def _start_loading(self, dt):
        """Начинает процесс загрузки"""
        self._simulate_loading()

    def _simulate_loading(self):
        """Имитирует загрузку с обновлением прогресса"""

        # Этапы загрузки
        stages = [
            (10, "Инициализация..."),
            (25, "Загрузка данных..."),
            (45, "Настройка интерфейса..."),
            (70, "Подготовка аккордов..."),
            (90, "Почти готово..."),
            (100, "Готово! 🎸")
        ]

        def update_stage(index=0):
            if index >= len(stages):
                self._on_loading_complete()
                return

            progress, text = stages[index]
            self.progress.value = progress
            self.status_label.text = text

            # Анимируем появление текста
            anim = Animation(opacity=1, duration=0.1) + Animation(opacity=1, duration=0.5)
            anim.start(self.status_label)

            # Переход к следующему этапу
            delay = 0.3 if index == len(stages) - 1 else 0.4
            Clock.schedule_once(lambda dt, idx=index + 1: update_stage(idx), delay)

        update_stage()

    def _on_loading_complete(self):
        """Загрузка завершена"""
        self._loading_complete = True
        logger.info("✅ Загрузка завершена")

        # Небольшая задержка для красоты
        Clock.schedule_once(self._finish, 0.5)

    def _finish(self, dt):
        """Завершает показ сплеш-скрина и переходит к приложению"""
        if self.on_complete:
            # Анимация исчезновения
            anim = Animation(opacity=0, duration=0.3, t='out_quad')
            anim.bind(on_complete=lambda *args: self.on_complete())
            anim.start(self)