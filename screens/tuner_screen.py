# screens/tuner_screen.py
"""
Экран тюнера (пока заглушка с красивым дизайном)
"""
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.progressbar import ProgressBar
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.metrics import dp, sp
from kivy.graphics import Color, Ellipse, Line

from config.theme import theme
from config.logger_config import screen_logger

logger = screen_logger('Tuner')


class TunerScreen(Screen):
    """Экран тюнера с визуализацией"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'tuner'

        # Основной контейнер
        from kivy.uix.floatlayout import FloatLayout
        root = FloatLayout()

        # Центральный круг с нотой
        self.note_display = BoxLayout(
            orientation='vertical',
            size_hint=(0.6, 0.6),
            pos_hint={'center_x': 0.5, 'center_y': 0.6}
        )

        with self.note_display.canvas.before:
            # Круглый фон
            Color(*theme.PRIMARY, 0.1)
            self.circle = Ellipse(pos=self.note_display.pos, size=self.note_display.size)

        self.note_label = Label(
            text='E',
            font_size=sp(72),
            bold=True,
            color=theme.PRIMARY
        )

        self.string_label = Label(
            text='1-я струна',
            font_size=theme.FONT_SIZE_BODY,
            color=theme.TEXT_SECONDARY,
            size_hint=(1, 0.2)
        )

        self.note_display.add_widget(self.note_label)
        self.note_display.add_widget(self.string_label)

        # Индикатор точности
        self.accuracy_box = BoxLayout(
            orientation='vertical',
            size_hint=(0.8, 0.2),
            pos_hint={'center_x': 0.5, 'y': 0.2},
            spacing=theme.PADDING_SMALL
        )

        self.accuracy_label = Label(
            text='Отклонение: 0 центов',
            font_size=theme.FONT_SIZE_CAPTION,
            color=theme.TEXT_SECONDARY
        )

        self.progress = ProgressBar(
            max=100,
            value=50,
            size_hint=(1, 0.4)
        )

        self.accuracy_box.add_widget(self.accuracy_label)
        self.accuracy_box.add_widget(self.progress)

        # Кнопка включения
        self.tuner_button = Button(
            text='🎤 Включить тюнер',
            size_hint=(0.5, 0.08),
            pos_hint={'center_x': 0.5, 'y': 0.05},
            background_normal='',
            background_color=theme.SECONDARY,
            color=theme.TEXT_ON_PRIMARY,
            font_size=theme.FONT_SIZE_BODY
        )
        self.tuner_button.bind(on_press=self.toggle_tuner)

        # Добавляем всё
        root.add_widget(self.note_display)
        root.add_widget(self.accuracy_box)
        root.add_widget(self.tuner_button)

        self.add_widget(root)

        # Состояние тюнера
        self.is_active = False
        self.current_string = 0
        self.strings = ['E', 'B', 'G', 'D', 'A', 'E']
        self.target_freqs = [329.6, 246.9, 196.0, 146.8, 110.0, 82.4]

        logger.info('Экран тюнера создан')

    def toggle_tuner(self, instance):
        """Включение/выключение тюнера"""
        self.is_active = not self.is_active

        if self.is_active:
            instance.text = '⏹ Остановить'
            instance.background_color = theme.ERROR
            self.start_tuner()
            logger.info('Тюнер запущен')
        else:
            instance.text = '🎤 Включить тюнер'
            instance.background_color = theme.SECONDARY
            self.stop_tuner()
            logger.info('Тюнер остановлен')

    def start_tuner(self):
        """Запуск имитации тюнера"""
        self.current_string = 0
        self.update_string()
        Clock.schedule_interval(self.simulate_tuning, 0.5)

    def stop_tuner(self):
        """Остановка имитации"""
        Clock.unschedule(self.simulate_tuning)

    def update_string(self):
        """Обновляет текущую струну"""
        self.note_label.text = self.strings[self.current_string]
        self.string_label.text = f'{self.current_string + 1}-я струна ({self.target_freqs[self.current_string]} Hz)'

    def simulate_tuning(self, dt):
        """Имитация процесса настройки"""
        import random

        # Переключаемся между струнами
        if random.random() < 0.1:  # 10% шанс смены струны
            self.current_string = (self.current_string + 1) % 6
            self.update_string()

        # Имитация точности настройки
        accuracy = random.uniform(45, 55)  # около 50 = идеально
        self.progress.value = accuracy

        cents = (accuracy - 50) * 2  # -10..10 центов
        if abs(cents) < 2:
            self.accuracy_label.text = '✅ Отлично!'
            self.accuracy_label.color = theme.SUCCESS
        elif abs(cents) < 5:
            self.accuracy_label.text = f'⚠️ Отклонение: {cents:.0f} центов'
            self.accuracy_label.color = theme.WARNING
        else:
            self.accuracy_label.text = f'❌ Отклонение: {cents:.0f} центов'
            self.accuracy_label.color = theme.ERROR

    def on_leave(self):
        """При уходе с экрана выключаем тюнер"""
        if self.is_active:
            self.toggle_tuner(self.tuner_button)