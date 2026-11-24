# screens/chords_screen.py
"""
Корневой экран гитарных аккордов.
Наследует весь UI и логику от BaseChordsScreen.
"""
from kivy.clock import Clock
from config.logger_config import screen_logger
from screens.chords.base_chords_screen import BaseChordsScreen
from state.previous_screen import previous_screen_state
from state.settings_state import settings_state as settings_manager
from utils.perf import perf

logger = screen_logger('Chords')


class ChordsScreen(BaseChordsScreen):
    SCREEN_NAME = 'chords'
    USE_SHARED_STATE = True
    AUTO_SCAN_ON_INIT = True

    def on_enter(self):
        with perf('chords.on_enter.total'):
            super().on_enter()

            with perf('chords.on_enter.update_theme'):
                self.update_theme_colors()

            theme_id = settings_manager.theme
            has_slides = bool(self.swipe_container and self.swipe_container.slides)
            can_reuse = has_slides and self.state_manager.can_reuse_slides(
                theme_id, self.current_chord_name, self.current_variants
            )
            if self.swipe_container and self.current_variants and not can_reuse:
                if self._is_local_pair(self.current_tonality, self.current_type):
                    Clock.schedule_once(lambda dt: self._rebuild_slides_for_current_chord(), 0.05)
                else:
                    Clock.schedule_once(lambda dt: self._rebuild_server_slides(), 0.05)
            elif self.swipe_container and not self.current_variants:
                Clock.schedule_once(lambda dt: self.load_chord_variants(), 0.05)

            Clock.schedule_once(self._update_griff_size, 0.1)
            Clock.schedule_once(self._update_griff_size, 0.3)

            with perf('chords.on_enter.pending_chord', log_every=False):
                pending_chord = previous_screen_state.get_pending_chord()
                if pending_chord:
                    Clock.schedule_once(lambda dt: self.select_chord_by_name(pending_chord), 0.1)
                    previous_screen_state.clear_pending_chord()

            self._close_tonality_selector()
            self._close_type_selector()
            self._close_chord_selector()
            if self.swipe_container and self._current_alt_names:
                self.swipe_container.update_chord_name(self._current_main_name, self._current_alt_names)

            self._save_state()

