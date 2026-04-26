# screens/components/search_dialog.py
"""
Универсальный диалог поиска (аккорды и песни)
"""
from kivy.metrics import dp, sp
from kivy.clock import Clock
from kivy.uix.popup import Popup
import re

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDButton, MDButtonText, MDIconButton
from kivymd.uix.card import MDCard
from kivymd.uix.scrollview import MDScrollView

from config.theme import theme
from config.logger_config import get_logger
from api.client import api
from utils.notifications import notify

logger = get_logger('SearchDialog')


class SearchDialog:
    """Универсальный диалог поиска"""

    _instance = None
    _popup = None
    _search_input = None
    _results_container = None
    _chords_screen = None
    _screen_manager = None

    @classmethod
    def show(cls, screen_manager, chords_screen):
        """Показывает диалог поиска"""
        cls._screen_manager = screen_manager
        cls._chords_screen = chords_screen

        if cls._popup is None:
            cls._create_popup()

        # Очищаем поле ввода
        if cls._search_input:
            cls._search_input.text = ""

        # Открываем popup
        cls._popup.open()
        # Фокусируемся на поле ввода
        Clock.schedule_once(lambda dt: setattr(cls._search_input, 'focus', True) if cls._search_input else None, 0.1)

    @classmethod
    def _create_popup(cls):
        """Создаёт popup с поиском"""
        # Основной контейнер
        content = MDBoxLayout(
            orientation='vertical',
            spacing=dp(8),
            padding=dp(16),
            size_hint=(None, None),
            width=dp(340),
            height=dp(200)
        )

        # Заголовок
        title = MDLabel(
            text="Поиск",
            font_size=sp(20),
            halign="center",
            size_hint_y=None,
            height=dp(40),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
            bold=True
        )

        # Поле ввода
        cls._search_input = MDTextField(
            hint_text="Введите название аккорда или песни...",
            mode="filled",
            size_hint_x=1,
            height=dp(56),
            radius=[dp(12), dp(12), dp(12), dp(12)],
            on_text_validate=cls._perform_search,
            theme_line_color="Custom",
            line_color_normal=[0, 0, 0, 0],
            line_color_focus=[0, 0, 0, 0],
            theme_bg_color="Custom",
            fill_color_normal=[1, 1, 1, 0.15],
            fill_color_focus=[1, 1, 1, 0.2],
            text_color_normal=[1, 1, 1, 1],
            text_color_focus=[1, 1, 1, 1],
            hint_text_color=[0.7, 0.7, 0.7, 1]
        )

        # Кнопка поиска (лупа в поле ввода)
        search_btn = MDIconButton(
            icon="magnify",
            size_hint=(None, None),
            size=(dp(36), dp(36)),
            theme_icon_color="Custom",
            icon_color=[1, 1, 1, 1],
            md_bg_color=[0, 0, 0, 0],
            on_release=cls._perform_search,
            pos_hint={'center_y': 0.5}
        )
        cls._search_input.add_widget(search_btn)

        # Кнопки действий
        button_row = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(48),
            spacing=dp(12)
        )

        # Кнопка Отмена
        cancel_btn = MDButton(
            style="text",
            size_hint=(1, 1),
            on_release=cls._close_popup
        )
        cancel_btn_text = MDButtonText(text="Отмена")
        cancel_btn.add_widget(cancel_btn_text)

        button_row.add_widget(cancel_btn)

        content.add_widget(title)
        content.add_widget(cls._search_input)
        content.add_widget(button_row)

        cls._popup = Popup(
            title="",
            content=content,
            size_hint=(None, None),
            size=(dp(360), dp(200)),
            background_color=[0.08, 0.08, 0.08, 0.95],
            separator_color=[0, 0, 0, 0],
            auto_dismiss=True
        )

    @classmethod
    def _normalize_chord_name(cls, name):
        """Нормализует имя аккорда для поиска (заменяет $ на /)"""
        return name.replace('$', '/')

    @classmethod
    def _perform_search(cls, instance=None):
        """Выполняет поиск"""
        query = cls._search_input.text.strip()
        if len(query) < 2:
            notify.warning("Введите минимум 2 символа для поиска")
            return

        logger.info(f"🔍 Универсальный поиск: {query}")
        cls._close_popup(None)

        # 1. Сначала ищем точное совпадение аккорда
        chord_found = cls._find_exact_chord(query)

        if chord_found:
            # Переходим на экран аккордов
            if cls._screen_manager and cls._screen_manager.has_screen('chords'):
                cls._screen_manager.current = 'chords'
                if cls._chords_screen and hasattr(cls._chords_screen, 'load_chord_by_name'):
                    cls._chords_screen.load_chord_by_name(chord_found)
                    notify.success(f"Аккорд '{query}' найден")
            return

        # 2. Если аккорд не найден - ищем песни
        cls._search_and_show_songs(query)

    @classmethod
    def _find_exact_chord(cls, query):
        """Ищет точное совпадение аккорда (учитывая разделитель !)"""
        if not cls._chords_screen or not hasattr(cls._chords_screen, 'all_chords'):
            return None

        query_lower = query.lower()

        for chord in cls._chords_screen.all_chords:
            # Получаем имя аккорда и нормализуем
            chord_name = chord.get('name', '')
            chord_short = chord.get('short_name', '')

            # Проверяем по короткому имени
            if query_lower == chord_short.lower():
                return chord_short

            # Разбиваем полное имя по разделителю '!'
            # Пример: "A#7!Bb7" -> ["A#7", "Bb7"]
            if '!' in chord_name:
                alternatives = chord_name.split('!')
                for alt in alternatives:
                    alt_clean = cls._normalize_chord_name(alt).strip().lower()
                    if query_lower == alt_clean:
                        # Возвращаем короткое имя (первое из альтернатив)
                        return chord_short

        return None

    @classmethod
    def _search_and_show_songs(cls, query):
        """Ищет песни и переходит на экран результатов"""
        if not cls._screen_manager:
            notify.error("Ошибка навигации")
            return

        # Переходим на экран результатов поиска
        if cls._screen_manager.has_screen('search_results'):
            search_results = cls._screen_manager.get_screen('search_results')
            search_results.do_search(query)
            cls._screen_manager.current = 'search_results'
        else:
            # Если экрана нет, просто ищем и показываем уведомление
            try:
                results = api.search_songs_sync(query, "general", 20)
                if results:
                    notify.info(f"Найдено {len(results)} песен по запросу '{query}'")
                else:
                    notify.warning(f"Ничего не найдено по запросу '{query}'")
            except Exception as e:
                logger.error(f"Ошибка поиска: {e}")
                notify.error("Ошибка поиска")

    @classmethod
    def _close_popup(cls, instance):
        """Закрывает popup"""
        if cls._popup:
            cls._popup.dismiss()