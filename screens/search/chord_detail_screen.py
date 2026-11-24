# screens/chord_detail_screen.py
"""
Экран просмотра аккорда ИЗ ПОИСКА.
Наследует весь UI и логику от ChordsScreen, но при входе всегда
сбрасывает локальный кеш и грузит аккорд с сервера.
"""
from kivy.clock import Clock
from kivy.logger import Logger
from kivymd.app import MDApp

from screens.chords_screen import ChordsScreen
from state.previous_screen import previous_screen_state
from utils.localization import get_text

logger = Logger.getChild('ChordDetail')


class ChordDetailScreen(ChordsScreen):
    """Полная копия ChordsScreen, но с автозагрузкой аккорда из поиска."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'chord_detail'
        self._chord_to_load = None

    def go_back(self, instance=None):
        """Возврат обратно на экран поиска по жёсткому маршруту."""
        from config.navigation_config import navigate_back
        navigate_back(self.manager, 'chord_detail')

    def on_enter(self):
        self.update_theme_colors()
        self._update_griff_size()

        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            app.top_nav.set_custom_title(get_text('chords', 'Аккорды'))

        pending_chord = previous_screen_state.get_pending_chord()
        if pending_chord:
            logger.info(f"ChordDetail: авто-загрузка '{pending_chord}'")

            if self.swipe_container:
                self.swipe_container.clear_slides()
            self.current_variants = []
            self.current_variant_index = 0

            self._load_chord_from_server(pending_chord)
            previous_screen_state.clear_pending_chord()

    def _load_chord_from_server(self, chord_name):
        """Загружает аккорд напрямую с сервера, минуя локальный кеш."""
        # Нормализуем слеш
        norm_name = chord_name.replace('/', '\\')

        # Показываем заголовок
        if self.swipe_container:
            self.swipe_container.update_chord_name(chord_name.replace('\\', '/'), [])
        if self._info_label:
            self._info_label.text = "Загрузка..."

        def _on_results(items):
            if not items:
                # Пробуем альтернативу
                alt = norm_name.replace('#', 'b') if '#' in norm_name else norm_name.replace('b', '#')
                if alt != norm_name:
                    self._chords_client.search_by_synonym(
                        alt,
                        on_success=lambda items2: self._apply_server_search(items2, alt),
                        on_error=lambda msg: self._on_load_error(chord_name)
                    )
                else:
                    self._on_load_error(chord_name)
                return
            self._apply_server_search(items, norm_name)

        self._chords_client.search_by_synonym(
            norm_name, on_success=_on_results,
            on_error=lambda msg: self._on_load_error(chord_name)
        )

    def _apply_server_search(self, items, query):
        if not items:
            self._on_load_error(query)
            return
        best = items[0]
        main_name = best.get("main_name") or query
        chord_type = best.get("chord_type") or "Major"
        tonality = best.get("tonality") or ""

        if tonality in self.TONALITIES:
            self.current_tonality = tonality
            self.current_tonality_index = self.TONALITIES.index(tonality)
        if chord_type in self.CHORD_TYPES:
            self.current_type = chord_type
            self.current_type_index = self.CHORD_TYPES.index(chord_type)

        self.current_chord_name = main_name

        # Обновляем меню
        self.available_chords = [main_name]
        self._pending_chord_list = [main_name]
        self.current_chord_index = 0
        if self.unified_menu:
            self.unified_menu.update_chord(1)

        # Загружаем варианты
        self._load_variants_from_server(main_name, chord_type)

    def _load_variants_from_server(self, main_name, chord_type):
        """Загружает варианты через ChordsClient.get_chord и строит слайды."""
        self._server_loading = True

        def _on_success(variants):
            self._server_loading = False
            normalized = []
            for v in variants:
                syn = v.get("synonyms") or [v.get("main_name", "?")]
                normalized.append({
                    "name": " | ".join(syn),
                    "short_name": v.get("main_name", "?"),
                    "variant": v.get("variant", 1),
                    "type": v.get("chord_type", ""),
                    "description": v.get("description", ""),
                    "module": None,
                    "server_data": v,
                })
            normalized.sort(key=lambda x: x["variant"])
            self.current_variants = normalized
            self.current_variant_index = 0
            self.current_position = 1

            if self.unified_menu:
                self.unified_menu.update_variants(len(normalized))

            # Строим слайды
            self._rebuild_server_slides()
            self._update_display()

        def _on_error(msg):
            self._server_loading = False
            self._on_load_error(main_name)

        self._chords_client.get_chord(main_name, chord_type,
                                      on_success=_on_success, on_error=_on_error)

    def _on_load_error(self, chord_name):
        if self._info_label:
            self._info_label.text = f"Аккорд {chord_name} не найден"
        if self.swipe_container:
            self.swipe_container.clear_slides()