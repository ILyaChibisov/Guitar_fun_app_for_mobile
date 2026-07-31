# config/top_nav_config.py
"""
Конфигурация верхней панели навигации (TopNav)
Централизованное управление поведением для каждого экрана
"""
from kivy.metrics import dp, sp
from kivy.utils import platform
from config.logger_config import get_logger

logger = get_logger('TopNavConfig')


class TopNavConfig:
    """Конфигурация TopNav для всех экранов"""

    # ============ ТИПЫ ЛЕВОЙ КНОПКИ ============
    LEFT_BUTTON_HAMBURGER = 'hamburger'  # Три полоски (открыть Sidebar)
    LEFT_BUTTON_BACK = 'back'  # Стрелка назад
    LEFT_BUTTON_NONE = 'none'  # Без кнопки

    # ============ ТИПЫ ПРАВОЙ КНОПКИ ============
    RIGHT_BUTTON_SEARCH = 'search'  # Лупа (поиск)
    RIGHT_BUTTON_HOME = 'home'  # Домой
    RIGHT_BUTTON_NONE = 'none'  # Без кнопки

    # ============ ТИПЫ ЗАГОЛОВКА ============
    TITLE_TYPE_STATIC = 'static'  # Статический текст
    TITLE_TYPE_CUSTOM = 'custom'  # Кастомный виджет
    TITLE_TYPE_DYNAMIC = 'dynamic'  # Динамический (из экрана)

    # ============ КОНФИГУРАЦИЯ ЭКРАНОВ ============
    SCREENS = {
        # ============ ГЛАВНЫЙ ЭКРАН ============
        'home': {
            'title': 'Главная',
            'title_type': TITLE_TYPE_STATIC,
            'left_button': LEFT_BUTTON_HAMBURGER,
            'right_button': RIGHT_BUTTON_SEARCH,
            'show_back_button': False,
            'custom_back_callback': None,
            'custom_title_widget': None,
        },

        # ============ ОСНОВНЫЕ ЭКРАНЫ (BottomNav) ============
        'songs': {
            'title': 'Песни',
            'title_type': TITLE_TYPE_STATIC,
            'left_button': LEFT_BUTTON_HAMBURGER,
            'right_button': RIGHT_BUTTON_HOME,
            'show_back_button': False,
            'custom_back_callback': None,
            'custom_title_widget': None,
        },

        'chords': {
            'title': 'Аккорды',
            'title_type': TITLE_TYPE_STATIC,
            'left_button': LEFT_BUTTON_HAMBURGER,
            'right_button': RIGHT_BUTTON_HOME,
            'show_back_button': False,
            'custom_back_callback': None,
            'custom_title_widget': None,
        },

        'tuner': {
            'title': 'Тюнер',
            'title_type': TITLE_TYPE_STATIC,
            'left_button': LEFT_BUTTON_HAMBURGER,
            'right_button': RIGHT_BUTTON_HOME,
            'show_back_button': True,
            'custom_back_callback': 'go_back',
            'custom_title_widget': None,
        },

        'metronome': {
            'title': 'Метроном',
            'title_type': TITLE_TYPE_STATIC,
            'left_button': LEFT_BUTTON_HAMBURGER,
            'right_button': RIGHT_BUTTON_HOME,
            'show_back_button': False,
            'custom_back_callback': None,
            'custom_title_widget': None,
        },

        'favorites': {
            'title': 'Избранное',
            'title_type': TITLE_TYPE_STATIC,
            'left_button': LEFT_BUTTON_HAMBURGER,
            'right_button': RIGHT_BUTTON_HOME,
            'show_back_button': True,
            'custom_back_callback': 'go_back',
            'custom_title_widget': None,
        },

        'profile': {
            'title': 'Профиль',
            'title_type': TITLE_TYPE_STATIC,
            'left_button': LEFT_BUTTON_HAMBURGER,
            'right_button': RIGHT_BUTTON_HOME,
            'show_back_button': False,
            'custom_back_callback': None,
            'custom_title_widget': None,
        },

        'dictionary': {
            'title': 'Словарь',
            'title_type': TITLE_TYPE_STATIC,
            'left_button': LEFT_BUTTON_HAMBURGER,
            'right_button': RIGHT_BUTTON_HOME,
            'show_back_button': False,
            'custom_back_callback': None,
            'custom_title_widget': None,
        },

        'admin': {
            'title': 'Админка',
            'title_type': TITLE_TYPE_STATIC,
            'left_button': LEFT_BUTTON_HAMBURGER,
            'right_button': RIGHT_BUTTON_HOME,
            'show_back_button': False,
            'custom_back_callback': None,
            'custom_title_widget': None,
        },

        'search': {
            'title': 'Поиск',
            'title_type': TITLE_TYPE_STATIC,
            'left_button': LEFT_BUTTON_HAMBURGER,
            'right_button': RIGHT_BUTTON_HOME,
            'show_back_button': True,
            'custom_back_callback': 'go_back',
            'custom_title_widget': None,
        },

        # ============ ЭКРАНЫ ДЕТАЛЬНОГО ПРОСМОТРА ============
        'song_detail': {
            'title': '',
            'title_type': TITLE_TYPE_CUSTOM,
            'left_button': LEFT_BUTTON_BACK,
            'right_button': RIGHT_BUTTON_HOME,
            'show_back_button': True,
            'custom_back_callback': 'go_back',
            'custom_title_widget': 'vertical',
        },

        'favorite_detail': {
            'title': '',  # Динамический (название песни)
            'title_type': TITLE_TYPE_CUSTOM,
            'left_button': LEFT_BUTTON_BACK,
            'right_button': RIGHT_BUTTON_HOME,
            'show_back_button': True,
            'custom_back_callback': 'go_back',
            'custom_title_widget': 'vertical',
        },

        'search_detail': {
            'title': '',  # Динамический (название песни)
            'title_type': TITLE_TYPE_CUSTOM,
            'left_button': LEFT_BUTTON_BACK,
            'right_button': RIGHT_BUTTON_HOME,
            'show_back_button': True,
            'custom_back_callback': 'go_back',
            'custom_title_widget': 'vertical',
        },

        'search_screen_detail': {
            'title': '',  # Динамический (название песни)
            'title_type': TITLE_TYPE_CUSTOM,
            'left_button': LEFT_BUTTON_BACK,
            'right_button': RIGHT_BUTTON_HOME,
            'show_back_button': True,
            'custom_back_callback': 'go_back',
            'custom_title_widget': 'vertical',
        },

        'term_detail': {
            'title': 'Термин',
            'title_type': TITLE_TYPE_STATIC,
            'left_button': LEFT_BUTTON_BACK,
            'right_button': RIGHT_BUTTON_HOME,
            'show_back_button': True,
            'custom_back_callback': 'go_back',
            'custom_title_widget': None,
        },

        'search_term_detail': {
            'title': 'Термин',
            'title_type': TITLE_TYPE_STATIC,
            'left_button': LEFT_BUTTON_BACK,
            'right_button': RIGHT_BUTTON_HOME,
            'show_back_button': True,
            'custom_back_callback': 'go_back',
            'custom_title_widget': None,
        },

        'chord_detail': {
            'title': 'Аккорд',
            'title_type': TITLE_TYPE_STATIC,
            'left_button': LEFT_BUTTON_BACK,
            'right_button': RIGHT_BUTTON_HOME,
            'show_back_button': True,
            'custom_back_callback': 'go_back',
            'custom_title_widget': None,
        },

        # ============ ЭКРАНЫ СПИСКОВ ============
        'artist_songs': {
            'title': '',
            'title_type': TITLE_TYPE_CUSTOM,
            'left_button': LEFT_BUTTON_BACK,
            'right_button': RIGHT_BUTTON_HOME,
            'show_back_button': True,
            'custom_back_callback': 'go_back',
            'custom_title_widget': 'vertical',
        },

        # ============ ЭКРАНЫ ЗАДАЧ ============
        'tasks': {
            'title': 'Задачи',
            'title_type': TITLE_TYPE_STATIC,
            'left_button': LEFT_BUTTON_BACK,
            'right_button': RIGHT_BUTTON_HOME,
            'show_back_button': True,
            'custom_back_callback': 'go_back',
            'custom_title_widget': None,
        },

        'task_detail': {
            'title': 'Задача',
            'title_type': TITLE_TYPE_STATIC,
            'left_button': LEFT_BUTTON_BACK,
            'right_button': RIGHT_BUTTON_HOME,
            'show_back_button': True,
            'custom_back_callback': 'go_back',
            'custom_title_widget': None,
        },

        # ============ НОВЫЕ ЭКРАНЫ ============
        'settings': {
            'title': 'Настройки',
            'title_type': TITLE_TYPE_STATIC,
            'left_button': LEFT_BUTTON_HAMBURGER,  # ← БЫЛО BACK, СТАЛО HAMBURGER
            'right_button': RIGHT_BUTTON_HOME,
            'show_back_button': False,  # ← БЫЛО True, СТАЛО False
            'custom_back_callback': None,
            'custom_title_widget': None,
        },

        'help': {
            'title': 'Помощь',
            'title_type': TITLE_TYPE_STATIC,
            'left_button': LEFT_BUTTON_HAMBURGER,  # ← БЫЛО BACK, СТАЛО HAMBURGER
            'right_button': RIGHT_BUTTON_HOME,
            'show_back_button': False,  # ← БЫЛО True, СТАЛО False
            'custom_back_callback': None,
            'custom_title_widget': None,
        },

        'promo': {
            'title': 'Промокод',
            'title_type': TITLE_TYPE_STATIC,
            'left_button': LEFT_BUTTON_HAMBURGER,  # ← БЫЛО BACK, СТАЛО HAMBURGER
            'right_button': RIGHT_BUTTON_HOME,
            'show_back_button': False,  # ← БЫЛО True, СТАЛО False
            'custom_back_callback': None,
            'custom_title_widget': None,
        },

        'feedback': {
            'title': 'Обратная связь',
            'title_type': TITLE_TYPE_STATIC,
            'left_button': LEFT_BUTTON_HAMBURGER,  # ← БЫЛО BACK, СТАЛО HAMBURGER
            'right_button': RIGHT_BUTTON_HOME,
            'show_back_button': False,  # ← БЫЛО True, СТАЛО False
            'custom_back_callback': None,
            'custom_title_widget': None,
        },

        # ============ ЭКРАНЫ ПАРСЕРОВ ============
        'amdm_parser': {
            'title': 'AMDM Парсер',
            'title_type': TITLE_TYPE_STATIC,
            'left_button': LEFT_BUTTON_BACK,
            'right_button': RIGHT_BUTTON_HOME,
            'show_back_button': True,
            'custom_back_callback': 'None',
            'custom_title_widget': None,
        },

        'mytabs_parser': {
            'title': 'MyTabs Парсер',
            'title_type': TITLE_TYPE_STATIC,
            'left_button': LEFT_BUTTON_BACK,
            'right_button': RIGHT_BUTTON_HOME,
            'show_back_button': True,
            'custom_back_callback': 'None',
            'custom_title_widget': None,
        },

        'accord_pro_parser': {
            'title': 'AccordPro Парсер',
            'title_type': TITLE_TYPE_STATIC,
            'left_button': LEFT_BUTTON_BACK,
            'right_button': RIGHT_BUTTON_HOME,
            'show_back_button': True,
            'custom_back_callback': 'None',
            'custom_title_widget': None,
        },

        'akkordus_parser': {
            'title': 'Akkordus Парсер',
            'title_type': TITLE_TYPE_STATIC,
            'left_button': LEFT_BUTTON_BACK,
            'right_button': RIGHT_BUTTON_HOME,
            'show_back_button': True,
            'custom_back_callback': 'None',
            'custom_title_widget': None,
        },

        'muzland_parser': {
            'title': 'Muzland Парсер',
            'title_type': TITLE_TYPE_STATIC,
            'left_button': LEFT_BUTTON_BACK,
            'right_button': RIGHT_BUTTON_HOME,
            'show_back_button': True,
            'custom_back_callback': 'None',
            'custom_title_widget': None,
        },

        'chordie_parser': {
            'title': 'Chordie Парсер',
            'title_type': TITLE_TYPE_STATIC,
            'left_button': LEFT_BUTTON_BACK,
            'right_button': RIGHT_BUTTON_HOME,
            'show_back_button': True,
            'custom_back_callback': 'None',
            'custom_title_widget': None,
        },

        'fivelad_parser': {
            'title': '5Lad Парсер',
            'title_type': TITLE_TYPE_STATIC,
            'left_button': LEFT_BUTTON_BACK,
            'right_button': RIGHT_BUTTON_HOME,
            'show_back_button': True,
            'custom_back_callback': 'None',
            'custom_title_widget': None,
        },

        'akkordbard_parser': {
            'title': 'AkkordBard Парсер',
            'title_type': TITLE_TYPE_STATIC,
            'left_button': LEFT_BUTTON_BACK,
            'right_button': RIGHT_BUTTON_HOME,
            'show_back_button': True,
            'custom_back_callback': 'None',
            'custom_title_widget': None,
        },

        'domhve_parser': {
            'title': 'Domhve Парсер',
            'title_type': TITLE_TYPE_STATIC,
            'left_button': LEFT_BUTTON_BACK,
            'right_button': RIGHT_BUTTON_HOME,
            'show_back_button': True,
            'custom_back_callback': 'None',
            'custom_title_widget': None,
        },

        'rushsound_parser': {
            'title': 'RushSound Парсер',
            'title_type': TITLE_TYPE_STATIC,
            'left_button': LEFT_BUTTON_BACK,
            'right_button': RIGHT_BUTTON_HOME,
            'show_back_button': True,
            'custom_back_callback': 'None',
            'custom_title_widget': None,
        },
    }

    # ============ ДЕФОЛТНАЯ КОНФИГУРАЦИЯ ============
    DEFAULT_CONFIG = {
        'title': 'Экран',
        'title_type': TITLE_TYPE_STATIC,
        'left_button': LEFT_BUTTON_BACK,
        'right_button': RIGHT_BUTTON_HOME,
        'show_back_button': True,
        'custom_back_callback': None,
        'custom_title_widget': None,
    }

    # ============ МЕТОДЫ ============

    @classmethod
    def get_screen_config(cls, screen_name: str) -> dict:
        """
        Возвращает конфигурацию для экрана

        Args:
            screen_name: Имя экрана

        Returns:
            dict: Конфигурация экрана
        """
        config = cls.SCREENS.get(screen_name)
        if config is None:
            logger.warning(f"⚠️ Конфигурация для экрана '{screen_name}' не найдена, используем DEFAULT")
            return cls.DEFAULT_CONFIG.copy()
        return config.copy()

    @classmethod
    def get_title(cls, screen_name: str) -> str:
        """Возвращает заголовок для экрана"""
        config = cls.get_screen_config(screen_name)
        return config.get('title', '')

    @classmethod
    def get_left_button(cls, screen_name: str) -> str:
        """Возвращает тип левой кнопки"""
        config = cls.get_screen_config(screen_name)
        return config.get('left_button', cls.LEFT_BUTTON_BACK)

    @classmethod
    def get_right_button(cls, screen_name: str) -> str:
        """Возвращает тип правой кнопки"""
        config = cls.get_screen_config(screen_name)
        return config.get('right_button', cls.RIGHT_BUTTON_HOME)

    @classmethod
    def show_back_button(cls, screen_name: str) -> bool:
        """Показывать ли кнопку назад"""
        config = cls.get_screen_config(screen_name)
        return config.get('show_back_button', True)

    @classmethod
    def get_custom_back_callback(cls, screen_name: str):
        """Возвращает кастомный callback для кнопки назад"""
        config = cls.get_screen_config(screen_name)
        return config.get('custom_back_callback', None)

    @classmethod
    def get_custom_title_widget_type(cls, screen_name: str):
        """Возвращает тип кастомного виджета заголовка"""
        config = cls.get_screen_config(screen_name)
        return config.get('custom_title_widget', None)

    @classmethod
    def is_title_custom(cls, screen_name: str) -> bool:
        """Является ли заголовок кастомным"""
        config = cls.get_screen_config(screen_name)
        return config.get('title_type') == cls.TITLE_TYPE_CUSTOM

    @classmethod
    def is_title_dynamic(cls, screen_name: str) -> bool:
        """Является ли заголовок динамическим"""
        config = cls.get_screen_config(screen_name)
        return config.get('title_type') == cls.TITLE_TYPE_DYNAMIC

    @classmethod
    def is_left_button_hamburger(cls, screen_name: str) -> bool:
        """Бургер слева?"""
        return cls.get_left_button(screen_name) == cls.LEFT_BUTTON_HAMBURGER

    @classmethod
    def is_left_button_back(cls, screen_name: str) -> bool:
        """Стрелка назад слева?"""
        return cls.get_left_button(screen_name) == cls.LEFT_BUTTON_BACK

    @classmethod
    def is_right_button_search(cls, screen_name: str) -> bool:
        """Лупа справа?"""
        return cls.get_right_button(screen_name) == cls.RIGHT_BUTTON_SEARCH

    @classmethod
    def is_right_button_home(cls, screen_name: str) -> bool:
        """Домой справа?"""
        return cls.get_right_button(screen_name) == cls.RIGHT_BUTTON_HOME

    @classmethod
    def update_config(cls, screen_name: str, updates: dict):
        """
        Обновляет конфигурацию экрана на лету

        Args:
            screen_name: Имя экрана
            updates: Словарь с обновлениями
        """
        if screen_name not in cls.SCREENS:
            cls.SCREENS[screen_name] = cls.DEFAULT_CONFIG.copy()

        for key, value in updates.items():
            if key in cls.SCREENS[screen_name]:
                cls.SCREENS[screen_name][key] = value
                logger.info(f"✅ Обновлена конфигурация '{screen_name}': {key} = {value}")
            else:
                logger.warning(f"⚠️ Неизвестный ключ '{key}' для экрана '{screen_name}'")

    @classmethod
    def register_screen(cls, screen_name: str, config: dict):
        """
        Регистрирует новый экран с конфигурацией

        Args:
            screen_name: Имя экрана
            config: Конфигурация экрана
        """
        if screen_name in cls.SCREENS:
            logger.warning(f"⚠️ Экран '{screen_name}' уже существует, перезаписываем")

        # Проверяем обязательные поля
        required_fields = ['title', 'left_button', 'right_button']
        for field in required_fields:
            if field not in config:
                logger.error(f"❌ Отсутствует обязательное поле '{field}' для экрана '{screen_name}'")
                return

        cls.SCREENS[screen_name] = config.copy()
        logger.info(f"✅ Зарегистрирован новый экран '{screen_name}'")

    @classmethod
    def print_all_configs(cls):
        """Выводит все конфигурации для отладки"""
        logger.info("=" * 70)
        logger.info("📋 ВСЕ КОНФИГУРАЦИИ TOP NAV")
        logger.info("=" * 70)
        for screen_name, config in cls.SCREENS.items():
            logger.info(f"  {screen_name}:")
            logger.info(f"    title: {config.get('title')}")
            logger.info(f"    left: {config.get('left_button')}")
            logger.info(f"    right: {config.get('right_button')}")
            logger.info(f"    back: {config.get('show_back_button')}")
        logger.info("=" * 70)


# Создаём экземпляр для удобного импорта
top_nav_config = TopNavConfig()