# screens/test_screen.py
from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.metrics import dp
from kivy.clock import Clock
from api.client import api
from config.logger_config import screen_logger

logger = screen_logger('Test')


class TestScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        layout = MDBoxLayout(orientation='vertical', padding=dp(20), spacing=dp(20))

        self.status_label = MDLabel(
            text="🔍 Проверка подключения...",
            halign="center",
            size_hint_y=None,
            height=dp(100),
            theme_text_color="Primary"
        )

        check_btn = MDRaisedButton(
            text="Проверить сервер",
            size_hint=(0.8, None),
            height=dp(50),
            pos_hint={"center_x": 0.5},
            on_release=self.check_server,
            md_bg_color="#76B3B6"
        )

        layout.add_widget(self.status_label)
        layout.add_widget(check_btn)
        self.add_widget(layout)

        # Автоматическая проверка при загрузке
        Clock.schedule_once(lambda dt: self.check_server(None), 1)

    def check_server(self, instance):
        self.status_label.text = "🔄 Проверка соединения..."

        def on_success(result):
            self.status_label.text = f"✅ Сервер работает!\n{result}"
            logger.info(f"Сервер доступен: {result}")

        def on_failure(req, error):
            self.status_label.text = f"❌ Ошибка подключения\n{error}"
            logger.error(f"Сервер недоступен: {error}")

        api.check_health(on_success=on_success, on_failure=on_failure)