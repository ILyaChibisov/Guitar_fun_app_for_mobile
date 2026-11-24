# screens/chord_detail_screen.py
"""
Экран просмотра аккорда, открытого из глобального поиска.
Наследует весь UI, карусель вариантов, полноэкранный гриф и селекторы от BaseChordsScreen.
"""
from kivy.clock import Clock
from kivymd.app import MDApp

from config.logger_config import screen_logger
from config.navigation_config import navigate_back
from screens.chords.base_chords_screen import BaseChordsScreen
from state.previous_screen import previous_screen_state
from utils.localization import get_text

logger = screen_logger('ChordDetail')


class ChordDetailScreen(BaseChordsScreen):
    SCREEN_NAME = 'chord_detail'
    USE_SHARED_STATE = False
    AUTO_SCAN_ON_INIT = False

    def go_back(self, instance=None):
        """Возврат обратно на экран поиска по жёсткому маршруту."""
        navigate_back(self.manager, self.SCREEN_NAME)

    def on_enter(self):
        super().on_enter()
        if not self.all_chords:
            self.scan_chords()

        self.update_theme_colors()
        self._update_griff_size()

        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            app.top_nav.set_custom_title(get_text('chords', 'Аккорды'))

        self._close_tonality_selector()
        self._close_type_selector()
        self._close_chord_selector()

        pending_chord = previous_screen_state.get_pending_chord()
        if pending_chord:
            logger.info(f"ChordDetail: авто-загрузка '{pending_chord}'")
            if self.swipe_container:
                self.swipe_container.clear_slides()
            self.current_variants = []
            self.current_variant_index = 0

            Clock.schedule_once(lambda dt, ch=pending_chord: self.select_chord_by_name(ch), 0.05)
            previous_screen_state.clear_pending_chord()

