# utils/settings_manager.py
"""
DEPRECATED: тонкая обёртка над settings_state для обратной совместимости.

Новый код должен использовать:
    from state.settings_state import settings_state

Этот модуль удаляется после перевода всех экранов на settings_state.
"""
from state.settings_state import settings_state


class _SettingsManagerCompat:
    """Совместимость со старым API settings_manager."""

    @property
    def theme(self):
        return settings_state.theme

    @property
    def language(self):
        return settings_state.language

    @property
    def is_authenticated(self):
        return settings_state.is_authenticated

    def set_theme(self, theme_id):
        # Старый API писал в файл синхронно (fsync) → фриз.
        # Теперь — через settings_state (асинхронно, без fsync).
        settings_state.set_theme(theme_id)

    def set_language(self, lang_code):
        settings_state.set_language(lang_code)

    def set_authenticated(self, value):
        settings_state.set_authenticated(value)

    # Быстрые методы — теперь просто алиасы (запись и так асинхронная)
    def set_theme_quick(self, theme_id):
        settings_state.set_theme(theme_id)

    def set_language_quick(self, lang_code):
        settings_state.set_language(lang_code)

    def flush(self):
        settings_state.flush()


settings_manager = _SettingsManagerCompat()