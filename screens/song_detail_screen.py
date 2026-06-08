# screens/song_detail_screen.py
"""
Экран просмотра песни с текстом и подборами
"""
from kivymd.app import MDApp
from kivymd.uix.label import MDLabel
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDIconButton, MDRaisedButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.dialog import MDDialog
from kivy.metrics import dp, sp
from kivy.animation import Animation
from kivy.uix.progressbar import ProgressBar
from kivy.graphics import Color, Rectangle
from kivy.core.image import Image as CoreImage
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.uix.behaviors import ButtonBehavior
from io import BytesIO
import re
from kivy.clock import Clock

from config.theme import theme
from config.logger_config import screen_logger
from config.layout_config import layout_config
from config.system_bars import get_navigation_bar_height
from screens.base_screen import BaseScreen
from screens.chord_renderer import ChordRenderer
from api.client import api
from utils.notifications import notify
from utils.screen_state import screen_state
# Импорт для подсветки аккордов
from utils.chord_highlighter import (
    ChordTextLabel,
    highlight_chords_in_text,
    extract_chords_from_text,
    init_chord_patterns
)

logger = screen_logger('SongDetail')

try:
    from data import load_asset_as_bytes

    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False


    def load_asset_as_bytes(name):
        return None


def clean_text(text):
    """Очищает текст от HTML тегов и сохраняет специальные символы"""
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', '', text)
    html_entities = {
        '&amp;': '&', '&lt;': '<', '&gt;': '>', '&quot;': '"',
        '&apos;': "'", '&nbsp;': ' ', '&#39;': "'", '&#34;': '"',
        '&#38;': '&', '&#60;': '<', '&#62;': '>', '&#171;': '«',
        '&#187;': '»', '&#169;': '©', '&#174;': '®', '&#8364;': '€',
        '&#8470;': '№', '&#8211;': '–', '&#8212;': '—', '&#8216;': "'",
        '&#8217;': "'", '&#8220;': '"', '&#8221;': '"', '&#8230;': '…',
    }
    for entity, char in html_entities.items():
        text = text.replace(entity, char)
    lines = text.split('\n')
    cleaned_lines = []
    for i, line in enumerate(lines):
        if i < 4:
            continue
        if 'источник:' in line.lower() or 'source:' in line.lower():
            continue
        cleaned_lines.append(line)
    while cleaned_lines and not cleaned_lines[-1].strip():
        cleaned_lines.pop()
    result = '\n'.join(cleaned_lines)
    if not result.strip():
        return '\n'.join(lines[4:])
    return result


class LoadingSpinner(MDBoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint = (1, 1)
        self.spacing = dp(16)
        self.progress = ProgressBar(
            size_hint=(0.8, None),
            height=dp(4),
            pos_hint={'center_x': 0.5},
            value=50,
            max=100
        )
        self.anim = None
        self.label = MDLabel(
            text="Загрузка...",
            halign="center",
            font_size=sp(14),
            theme_text_color="Secondary",
            size_hint_y=None,
            height=dp(30)
        )
        self.add_widget(self.progress)
        self.add_widget(self.label)

    def start_animation(self):
        self.anim = Animation(value=100, duration=1) + Animation(value=0, duration=1)
        self.anim.repeat = True
        self.anim.start(self.progress)

    def stop_animation(self):
        if self.anim:
            self.anim.cancel(self.progress)
        self.progress.value = 0


class IconImageButton(ButtonBehavior, MDBoxLayout):
    """Кнопка с иконкой из PNG ассета с возможностью смещения через padding"""

    def __init__(self, icon_name, on_press_callback=None, size=dp(18), offset_y=0, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint = (None, None)
        self.size = (size, size)
        self.md_bg_color = [0, 0, 0, 0]

        # Смещение через padding (положительное = смещение вниз)
        self.offset_y = offset_y

        # Контейнер для иконки с возможностью смещения
        self.icon_container = MDBoxLayout(
            size_hint=(1, 1),
            padding=[0, offset_y, 0, 0]  # [left, top, right, bottom]
        )

        self.icon = Image(
            size_hint=(0.8, 0.8),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            allow_stretch=True,
            keep_ratio=True
        )

        self.icon_container.add_widget(self.icon)
        self.add_widget(self.icon_container)

        self.icon_name = icon_name
        self.on_press_callback = on_press_callback
        self.bind(on_release=self._on_press)
        self._load_icon()

    def _load_icon(self):
        if HAS_ASSETS:
            try:
                icon_data = load_asset_as_bytes(self.icon_name)
                if icon_data:
                    img = CoreImage(BytesIO(icon_data), ext="png")
                    self.icon.texture = img.texture
                    return
            except Exception as e:
                logger.error(f"Ошибка загрузки иконки {self.icon_name}: {e}")
        self.icon.opacity = 0

    def _on_press(self, instance):
        if self.on_press_callback:
            self.on_press_callback(self.icon_name)


class IconActionButton(MDIconButton):
    """Кнопка действия в нижней панели"""

    def __init__(self, icon_name, on_press_callback=None, icon_color=None, **kwargs):
        super().__init__(**kwargs)
        self.on_press_callback = on_press_callback
        self.size_hint = (None, None)
        self.size = (dp(32), dp(32))
        self.theme_icon_color = "Custom"
        if icon_color:
            self.icon_color = icon_color
        else:
            self.icon_color = [1, 1, 1, 0.85]
        self.md_bg_color = [0, 0, 0, 0]
        self.icon = icon_name
        self.bind(on_release=self._on_press)

    def _on_press(self, instance):
        if self.on_press_callback:
            self.on_press_callback()


class SongDetailScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'song_detail'
        self.song_id = None
        self.song_title = None
        self.song_artist = None
        self.is_liked = False
        self.is_favorite = False
        self.is_loading = False
        self.loading_spinner = None
        self.bg_image = None
        self.previous_screen = 'artist_songs'
        self.current_tonality = 0
        self.tabs = []
        self.current_tab_index = 0

        # Настройки размера шрифта
        self.current_font_size = 14
        self.font_size_levels = [10, 12, 14, 16, 18, 20, 22]
        self.font_size_index = 2  # 14

        # Для меню аккордов
        self._song_chords = []
        self._current_chord_index = 0
        self.chords_dialog = None
        self.chord_preview_renderer = None

        self.init_ui()
        self.load_background()

        logger.info('Экран просмотра песни создан')

    def set_previous_screen(self, screen_name):
        self.previous_screen = screen_name

    def load_background(self):
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
        main_container = MDBoxLayout(orientation='vertical', size_hint=(1, 1), padding=[0, 0, 0, 0])

        top_padding = layout_config.get_top_padding()
        main_container.add_widget(Widget(size_hint_y=None, height=top_padding))

        # Дополнительный отступ сверху для эстетики
        main_container.add_widget(Widget(size_hint_y=None, height=dp(8)))

        # Получаем единые боковые отступы из layout_config
        content_padding = layout_config.get_content_padding()

        # Карточка с текстом - с едиными боковыми отступами
        card_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            padding=[content_padding[0], 0, content_padding[2], content_padding[3]]
        )

        self.song_card = MDCard(
            orientation='vertical',
            size_hint=(1, 1),
            padding=[0, 0, 0, 0],
            spacing=0,
            radius=[18, 18, 18, 18],
            md_bg_color=[1, 1, 1, 0.98],
            elevation=2,
            line_color=[0.8, 0.8, 0.8, 0.3],
            line_width=0.5
        )

        # Верхнее меню - только название песни и артист
        self._create_top_menu()
        self.song_card.add_widget(self.top_menu)

        # Разделитель
        top_separator = MDBoxLayout(size_hint=(1, None), height=1, md_bg_color=[0.85, 0.85, 0.85, 0.8])
        self.song_card.add_widget(top_separator)

        # Контейнер для текста (текст песни)
        self.content_scroll = MDScrollView(
            size_hint=(1, 1),
            do_scroll_x=False,
            bar_width=3,
            bar_color=[0.5, 0.5, 0.5, 0.2],
            bar_inactive_color=[0.5, 0.5, 0.5, 0.1]
        )

        scroll_content = MDBoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=4,
            padding=[12, 8, 12, 8],
            adaptive_height=True
        )

        # Используем ChordTextLabel для кликабельных аккордов
        self.content_label = ChordTextLabel(
            text="",
            font_size=self.current_font_size,
            size_hint_y=None,
            theme_text_color="Custom",
            text_color=[0, 0, 0, 0.85],
            valign="top",
            line_height=1.4,
            on_chord_click=self.on_chord_click,
            markup=True
        )
        self.content_label.bind(texture_size=self._update_content_height)
        scroll_content.add_widget(self.content_label)

        self.content_scroll.add_widget(scroll_content)
        self.song_card.add_widget(self.content_scroll)

        # Нижняя панель управления
        self._create_bottom_panel()
        self.song_card.add_widget(self.bottom_panel)

        card_container.add_widget(self.song_card)
        main_container.add_widget(card_container)

        # Нижний отступ для BottomNav
        bottom_nav_height = dp(60)
        nav_bar_height = get_navigation_bar_height()
        total_bottom = bottom_nav_height + nav_bar_height + dp(12)
        main_container.add_widget(Widget(size_hint_y=None, height=total_bottom))

        self.add_widget(main_container)

        logger.info(f"SongDetailScreen: top_padding = {top_padding}dp, side_padding = {content_padding[0]}dp")

    def _create_top_menu(self):
        """Верхнее меню - только название песни и артист"""
        self.top_menu = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(50),
            padding=[dp(12), dp(8), dp(12), dp(4)],
            spacing=dp(2),
            md_bg_color=[1, 1, 1, 0]
        )

        row = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(34),
            spacing=dp(8),
            pos_hint={'center_y': 0.5}
        )

        # Смайлик (нота)
        self.song_icon = Image(
            size_hint=(None, None),
            size=(dp(28), dp(28)),
            pos_hint={'center_y': 0.5},
            allow_stretch=True,
            keep_ratio=True
        )
        if HAS_ASSETS:
            try:
                icon_data = load_asset_as_bytes('song_png')
                if icon_data:
                    img = CoreImage(BytesIO(icon_data), ext="png")
                    self.song_icon.texture = img.texture
            except:
                pass
        if not self.song_icon.texture:
            self.song_icon.text = "🎵"

        # Название: артист - песня
        self.song_info_label = MDLabel(
            text="",
            font_size=sp(16),
            size_hint_x=1,
            theme_text_color="Custom",
            text_color=[0, 0, 0, 0.85],
            bold=True,
            valign="middle",
            shorten=True,
            shorten_from="right"
        )

        row.add_widget(self.song_icon)
        row.add_widget(self.song_info_label)

        self.top_menu.add_widget(row)

    def _create_bottom_panel(self):
        """Создаёт нижнюю панель с 6 кнопками"""
        self.bottom_panel = MDCard(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(52),
            padding=[dp(8), dp(4), dp(8), dp(4)],
            spacing=dp(4),
            radius=[0, 0, 18, 18],
            md_bg_color=[0.96, 0.96, 0.96, 0.95],
            elevation=0,
            line_color=[0.8, 0.8, 0.8, 0.2],
            line_width=0.5,
            pos_hint={'center_x': 0.5}
        )

        # 1. Аккорды
        self.chords_btn = IconActionButton(
            icon_name="music",
            on_press_callback=self.on_chords_press,
            icon_color=[0.46, 0.70, 0.71, 1]
        )

        # 2. Тональность
        self.tonality_btn = IconActionButton(
            icon_name="tune",
            on_press_callback=self.show_tonality_picker,
            icon_color=[0.9, 0.7, 0.2, 0.9]
        )

        # 3. Подбор
        self.tabs_btn = IconActionButton(
            icon_name="folder-music",
            on_press_callback=self.show_tabs_picker,
            icon_color=[0.46, 0.70, 0.71, 0.9]
        )

        self.bottom_panel.add_widget(self.chords_btn)
        self.bottom_panel.add_widget(self.tonality_btn)
        self.bottom_panel.add_widget(self.tabs_btn)

        spacer = Widget(size_hint_x=1)
        self.bottom_panel.add_widget(spacer)

        # 4. Избранное
        self.favorite_btn = IconActionButton(
            icon_name="star-outline",
            on_press_callback=self.toggle_favorite,
            icon_color=[0.9, 0.7, 0.2, 0.9]
        )

        # 5. Лайк
        self.like_btn = IconActionButton(
            icon_name="heart-outline",
            on_press_callback=self.toggle_like,
            icon_color=[0.8, 0.3, 0.3, 0.9]
        )

        # 6. Лупа
        self.font_btn = IconActionButton(
            icon_name="magnify",
            on_press_callback=self.cycle_font_size,
            icon_color=[0.46, 0.70, 0.71, 0.9]
        )

        self.bottom_panel.add_widget(self.favorite_btn)
        self.bottom_panel.add_widget(self.like_btn)
        self.bottom_panel.add_widget(self.font_btn)

    # ==================== МЕНЮ АККОРДОВ ====================

    def on_chords_press(self):
        """Показывает всплывающее меню с аккордами песни"""
        logger.info("🎸 Нажата кнопка аккордов")

        # Получаем аккорды из текста
        self._extract_and_cache_chords()

        if not self._song_chords:
            notify.info("Аккорды не найдены в тексте песни")
            return

        # Создаём содержимое меню
        content = MDBoxLayout(
            orientation='vertical',
            spacing=dp(4),
            padding=[dp(8), dp(4), dp(8), dp(12)],
            size_hint_y=None,
            adaptive_height=True
        )

        # Отдельная строка только для крестика (самый верхний правый угол)
        close_row = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(28),
            spacing=dp(0),
            padding=[dp(0), dp(0), dp(0), dp(0)]
        )

        # Пустой виджет для отталкивания крестика вправо
        close_row.add_widget(Widget(size_hint_x=1))

        # Крестик в кружочке - в правом верхнем углу
        close_btn = MDIconButton(
            icon="close-circle",
            size_hint=(None, None),
            size=(dp(24), dp(24)),
            theme_icon_color="Custom",
            icon_color=[0.6, 0.6, 0.6, 0.7],
            md_bg_color=[0, 0, 0, 0],
            on_release=lambda x: self.chords_dialog.dismiss(),
            pos_hint={'center_y': 0.5}
        )
        close_row.add_widget(close_btn)

        content.add_widget(close_row)

        # Строка с пагинацией и названием аккорда
        header = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(44),
            spacing=dp(8),
            padding=[dp(4), dp(0), dp(4), dp(0)],
            pos_hint={'center_y': 0.5}
        )

        # Стрелка влево
        self.chord_prev_btn = MDIconButton(
            icon="chevron-left",
            size_hint=(None, None),
            size=(dp(36), dp(36)),
            theme_icon_color="Custom",
            icon_color=[0.46, 0.70, 0.71, 1],
            md_bg_color=[0, 0, 0, 0.08],
            on_release=self._prev_chord_in_menu,
            pos_hint={'center_y': 0.5}
        )

        # Название аккорда
        self.chord_name_label = MDLabel(
            text=self._song_chords[0],
            font_size=sp(18),
            halign="center",
            valign="middle",
            size_hint_x=1,
            theme_text_color="Custom",
            text_color=[0, 0, 0, 0.85],
            bold=True
        )

        # Стрелка вправо
        self.chord_next_btn = MDIconButton(
            icon="chevron-right",
            size_hint=(None, None),
            size=(dp(36), dp(36)),
            theme_icon_color="Custom",
            icon_color=[0.46, 0.70, 0.71, 1],
            md_bg_color=[0, 0, 0, 0.08],
            on_release=self._next_chord_in_menu,
            pos_hint={'center_y': 0.5}
        )

        header.add_widget(self.chord_prev_btn)
        header.add_widget(self.chord_name_label)
        header.add_widget(self.chord_next_btn)

        content.add_widget(header)

        # Описание аккорда
        self.chord_desc_label = MDLabel(
            text="",
            font_size=sp(10),
            halign="center",
            size_hint=(1, None),
            height=dp(20),
            theme_text_color="Custom",
            text_color=[0.5, 0.5, 0.5, 0.7],
            shorten=True,
            shorten_from="right"
        )
        content.add_widget(self.chord_desc_label)

        # Контейнер для грифа
        griff_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(180),
            padding=[dp(4), dp(4), dp(4), dp(4)]
        )

        # Создаём мини-рендерер
        self.chord_preview_renderer = ChordRenderer()
        griff_container.add_widget(self.chord_preview_renderer)

        # Загружаем фон грифа
        try:
            bg_data = load_asset_as_bytes("griff_png")
            if bg_data:
                img = CoreImage(BytesIO(bg_data), ext="png")
                if img and img.texture:
                    self.chord_preview_renderer.set_background(img.texture)
        except Exception as e:
            logger.error(f"Ошибка загрузки фона грифа: {e}")

        content.add_widget(griff_container)

        # Создаём диалог
        self.chords_dialog = MDDialog(
            type="custom",
            content_cls=content,
            size_hint=(0.85, None),
            height=dp(320),
            radius=[18, 18, 18, 18],
            buttons=[]
        )

        # Сохраняем индекс и загружаем первый аккорд
        self._current_chord_index = 0
        self._update_chord_display()
        self._load_chord_for_preview(self._song_chords[0])

        self.chords_dialog.open()

    def _extract_and_cache_chords(self):
        """Извлекает и кэширует аккорды из песни (с сохранением оригинального регистра)"""
        chords = set()

        # Собираем аккорды из всех подборов
        for tab in self.tabs:
            content = tab.get('content', '')
            if content:
                cleaned = clean_text(content)
                extracted = extract_chords_from_text(cleaned)
                # Сохраняем оригинальные названия (с учётом регистра)
                chords.update(extracted)

        # Сортируем по имени
        self._song_chords = sorted(list(chords))
        logger.info(f"🎸 Найдено аккордов в песне: {len(self._song_chords)} - {self._song_chords}")

    def _get_chord_description(self, chord_name):
        """Получает описание аккорда из базы"""
        if self.manager and self.manager.has_screen('chords'):
            chords_screen = self.manager.get_screen('chords')
            chord_normalized = chord_name.replace('B', 'H')

            for chord in chords_screen.all_chords:
                if chord['short_name'] == chord_normalized or chord['short_name'] == chord_name:
                    description = chord.get('description', '')
                    if description:
                        # Берём первую часть описания
                        parts = description.replace('!', '|').split('|')
                        if parts:
                            return parts[0].strip()
                    return chord.get('type', 'Аккорд')

                # Поиск по альтернативным названиям
                name_variants = chord['name'].split('|')
                for variant in name_variants:
                    variant_clean = variant.strip().replace('$', '/')
                    if variant_clean == chord_name:
                        description = chord.get('description', '')
                        if description:
                            parts = description.replace('!', '|').split('|')
                            if parts:
                                return parts[0].strip()
                        return chord.get('type', 'Аккорд')
        return 'Аккорд'

    def _update_chord_display(self):
        """Обновляет отображение текущего аккорда в меню"""
        if not self._song_chords:
            return

        total = len(self._song_chords)
        current = self._current_chord_index
        chord_name = self._song_chords[current]

        # Обновляем название аккорда (сохраняем оригинальный регистр)
        if hasattr(self, 'chord_name_label'):
            self.chord_name_label.text = chord_name

        # Обновляем описание
        if hasattr(self, 'chord_desc_label'):
            desc = self._get_chord_description(chord_name)
            self.chord_desc_label.text = desc

        # Обновляем кнопки пагинации
        if hasattr(self, 'chord_prev_btn'):
            self.chord_prev_btn.disabled = (current == 0)
            self.chord_prev_btn.opacity = 1 if current > 0 else 0.3

        if hasattr(self, 'chord_next_btn'):
            self.chord_next_btn.disabled = (current == total - 1)
            self.chord_next_btn.opacity = 1 if current < total - 1 else 0.3

    def _prev_chord_in_menu(self, *args):
        """Предыдущий аккорд в меню"""
        if self._current_chord_index > 0:
            self._current_chord_index -= 1
            chord = self._song_chords[self._current_chord_index]
            self._update_chord_display()
            self._load_chord_for_preview(chord)

    def _next_chord_in_menu(self, *args):
        """Следующий аккорд в меню"""
        if self._current_chord_index < len(self._song_chords) - 1:
            self._current_chord_index += 1
            chord = self._song_chords[self._current_chord_index]
            self._update_chord_display()
            self._load_chord_for_preview(chord)

    def _load_chord_for_preview(self, chord_name):
        """Загружает аккорд для предпросмотра в мини-рендерере"""
        if not hasattr(self, 'chord_preview_renderer') or not self.chord_preview_renderer:
            return

        # Нормализуем имя аккорда для поиска (B -> H)
        chord_normalized = chord_name.replace('B', 'H')

        # Ищем модуль аккорда
        if self.manager and self.manager.has_screen('chords'):
            chords_screen = self.manager.get_screen('chords')

            target_chord = None
            for chord in chords_screen.all_chords:
                if chord['short_name'] == chord_normalized or chord['short_name'] == chord_name:
                    target_chord = chord
                    break
                # Поиск по альтернативным названиям
                name_variants = chord['name'].split('|')
                for variant in name_variants:
                    variant_clean = variant.strip().replace('$', '/')
                    if variant_clean == chord_name:
                        target_chord = chord
                        break
                if target_chord:
                    break

            if target_chord:
                chord_module = target_chord['module']
                self.chord_preview_renderer.load_chord(chord_module)
                self.chord_preview_renderer.set_mode("finger")
                logger.info(f"✅ Загружен аккорд для превью: {chord_name}")
            else:
                logger.warning(f"⚠️ Аккорд {chord_name} не найден в базе")
                self.chord_preview_renderer.sprite_layer.clear_widgets()

    # ==================== ТОНАЛЬНОСТЬ ====================

    def show_tonality_picker(self):
        """Показывает диалог выбора тональности"""
        content = MDBoxLayout(
            orientation='vertical',
            spacing=dp(8),
            padding=dp(16),
            size_hint_y=None,
            adaptive_height=True
        )

        from kivymd.uix.slider import MDSlider

        self.tonality_slider = MDSlider(
            min=-7,
            max=7,
            value=self.current_tonality,
            step=1,
            size_hint_y=None,
            height=dp(40)
        )

        value_label = MDLabel(
            text=f"Тональность: {self.current_tonality}",
            font_size=sp(16),
            halign="center",
            size_hint_y=None,
            height=dp(30),
            theme_text_color="Custom",
            text_color=[0, 0, 0, 0.7]
        )

        def on_slider_change(instance, value):
            value_label.text = f"Тональность: {int(value)}"

        self.tonality_slider.bind(value=on_slider_change)

        content.add_widget(value_label)
        content.add_widget(self.tonality_slider)

        dialog = MDDialog(
            title="Транспонирование",
            type="custom",
            content_cls=content,
            buttons=[
                MDRaisedButton(text="Отмена", on_release=lambda x: dialog.dismiss()),
                MDRaisedButton(text="Применить", on_release=lambda x: self._apply_tonality(dialog))
            ]
        )
        dialog.open()

    def _apply_tonality(self, dialog):
        """Применяет выбранную тональность"""
        new_tonality = int(self.tonality_slider.value)
        if new_tonality != self.current_tonality:
            self.current_tonality = new_tonality
            logger.info(f"Тональность изменена на {self.current_tonality}")
        dialog.dismiss()

    # ==================== ПОДБОРЫ ====================

    def show_tabs_picker(self):
        """Показывает диалог выбора подбора"""
        if not self.tabs or len(self.tabs) <= 1:
            notify.info("Только один подбор")
            return

        content = MDBoxLayout(
            orientation='vertical',
            spacing=dp(8),
            padding=dp(16),
            size_hint_y=None,
            adaptive_height=True
        )

        for i, tab in enumerate(self.tabs):
            btn = MDRaisedButton(
                text=f"Подбор {i + 1}",
                size_hint=(1, None),
                height=dp(48),
                md_bg_color=[0.46, 0.70, 0.71, 1] if i == self.current_tab_index else [0.2, 0.2, 0.2, 0.8],
                on_release=lambda x, idx=i: self._select_tab(idx)
            )
            content.add_widget(btn)

        dialog = MDDialog(
            title="Выберите подбор",
            type="custom",
            content_cls=content,
            buttons=[MDRaisedButton(text="Закрыть", on_release=lambda x: dialog.dismiss())]
        )
        dialog.open()
        self.tabs_dialog = dialog

    def _select_tab(self, index):
        """Выбирает подбор"""
        if hasattr(self, 'tabs_dialog'):
            self.tabs_dialog.dismiss()
        self.current_tab_index = index
        self._load_current_tab()

    # ==================== ОСНОВНЫЕ МЕТОДЫ ====================

    def cycle_font_size(self):
        """Циклическое изменение размера шрифта при нажатии на лупу"""
        self.font_size_index = (self.font_size_index + 1) % len(self.font_size_levels)
        self.current_font_size = self.font_size_levels[self.font_size_index]
        self.content_label.font_size = self.current_font_size
        self._update_content_height()

        if self.font_size_index == len(self.font_size_levels) - 1:
            self.font_btn.icon = "magnify-minus"
        else:
            self.font_btn.icon = "magnify-plus"

        anim = Animation(opacity=0.5, duration=0.05) + Animation(opacity=1, duration=0.1)
        anim.start(self.font_btn)

        logger.info(f"Размер шрифта: {self.current_font_size}")

    def _extract_and_log_chords(self, text):
        """Извлекает аккорды из текста и логирует их"""
        chords = extract_chords_from_text(text)

        if chords:
            unique_chords = sorted(set(chords))
            chords_str = ', '.join(unique_chords)
            artist_part = f"{self.song_artist} - " if self.song_artist else ""
            name_part = self.song_title if self.song_title else "Песня"
            logger.info(f"🎸 Найдены аккорды в {artist_part}{name_part}: {chords_str}")
        else:
            artist_part = f"{self.song_artist} - " if self.song_artist else ""
            name_part = self.song_title if self.song_title else "Песня"
            logger.info(f"🎸 В {artist_part}{name_part} аккордов не найдено")

        return chords

    def _load_current_tab(self):
        """Загружает текущий подбор с подсветкой аккордов"""
        if self.tabs and self.current_tab_index < len(self.tabs):
            tab = self.tabs[self.current_tab_index]
            raw_content = tab.get('content', 'Текст не загружен')
            cleaned = clean_text(raw_content)

            self._extract_and_log_chords(cleaned)

            if cleaned:
                highlighted_text = highlight_chords_in_text(cleaned)
                self.content_label.text = highlighted_text
                self.content_label.markup = True
            else:
                self.content_label.text = "Текст не загружен"
                self.content_label.markup = False

            self._update_content_height()
            Clock.schedule_once(lambda dt: setattr(self.content_scroll, 'scroll_y', 1), 0.1)

    def on_chord_click(self, chord_name):
        """Обработчик клика по аккорду в тексте"""
        logger.info(f"🎸 Нажат аккорд: {chord_name}")

        screen_state.set_previous_screen(self.name)
        screen_state.set_pending_chord(chord_name)

        if hasattr(self, 'manager') and self.manager:
            if self.manager.has_screen('chords'):
                self.manager.current = 'chords'

    def _update_content_height(self, *args):
        if not self.content_label.texture:
            Clock.schedule_once(lambda dt: self._update_content_height(), 0.05)
            return
        text_height = self.content_label.texture_size[1]
        self.content_label.height = max(dp(50), text_height + dp(8))
        if self.content_label.parent:
            self.content_label.parent.height = text_height + dp(16)

    def set_song(self, song_id):
        self.song_id = song_id
        self.load_song_data()

    def load_song_data(self):
        self.show_loading()
        api.get_tab(
            song_id=self.song_id,
            on_success=self.on_song_loaded,
            on_failure=self.on_load_failed
        )

    def show_loading(self):
        if self.is_loading:
            return
        self.is_loading = True
        self.loading_spinner = LoadingSpinner()
        self.add_widget(self.loading_spinner)
        self.loading_spinner.start_animation()

    def hide_loading(self):
        self.is_loading = False
        if self.loading_spinner:
            self.loading_spinner.stop_animation()
            self.remove_widget(self.loading_spinner)
            self.loading_spinner = None

    def on_song_loaded(self, data):
        artist = data.get('artist') or 'Неизвестный'
        title = data.get('title') or 'Без названия'

        self.song_artist = artist
        self.song_title = title

        self.tabs = data.get('tabs', [])
        if not self.tabs and data.get('content'):
            self.tabs = [{'content': data.get('content', '')}]

        self.current_tab_index = 0

        self.song_info_label.text = f"{artist} - {title}"

        if self.manager and self.manager.has_screen('chords'):
            chords_screen = self.manager.get_screen('chords')
            init_chord_patterns(chords_screen)
            logger.info("🎸 Паттерны аккордов инициализированы из базы")

        if self.tabs:
            raw_content = self.tabs[0].get('content', 'Текст не загружен')
            cleaned = clean_text(raw_content)

            self._extract_and_log_chords(cleaned)

            if cleaned:
                highlighted_text = highlight_chords_in_text(cleaned)
                self.content_label.text = highlighted_text
                self.content_label.markup = True
            else:
                self.content_label.text = "Текст не загружен"
                self.content_label.markup = False

            self._update_content_height()

        self.is_liked = data.get('is_liked', False)
        self.is_favorite = data.get('is_favorite', False)

        self.like_btn.icon = "heart" if self.is_liked else "heart-outline"
        self.favorite_btn.icon = "star" if self.is_favorite else "star-outline"

        Clock.schedule_once(lambda dt: setattr(self.content_scroll, 'scroll_y', 1), 0.1)
        self.hide_loading()
        logger.info(f"Песня загружена, подборов: {len(self.tabs)}")

    def on_load_failed(self, req, error):
        self.hide_loading()
        self.content_label.text = "Ошибка загрузки\nПроверьте интернет"
        notify.error("Ошибка загрузки песни")

    def toggle_like(self, *args):
        if not api.is_authenticated():
            notify.warning("Войдите, чтобы ставить лайки")
            return

        def on_success(result):
            self.is_liked = result.get('liked', not self.is_liked)
            self.like_btn.icon = "heart" if self.is_liked else "heart-outline"
            notify.success("Лайк поставлен!" if self.is_liked else "Лайк убран")

        def on_failure(req, error):
            notify.error("Ошибка")

        api.toggle_like(song_id=self.song_id, on_success=on_success, on_failure=on_failure)

    def toggle_favorite(self, *args):
        if not api.is_authenticated():
            notify.warning("Войдите, чтобы добавлять в избранное")
            return

        if self.is_favorite:
            def on_success(result):
                self.is_favorite = False
                self.favorite_btn.icon = "star-outline"
                notify.success("Удалено из избранного")
                self._refresh_favorites_screen()

            def on_failure(req, error):
                notify.error("Ошибка")

            api.remove_from_favorites(song_id=self.song_id, on_success=on_success, on_failure=on_failure)
        else:
            def on_success(result):
                self.is_favorite = True
                self.favorite_btn.icon = "star"
                notify.success("Добавлено в избранное")
                self._refresh_favorites_screen()

            def on_failure(req, error):
                notify.error("Ошибка")

            api.add_to_favorites(song_id=self.song_id, on_success=on_success, on_failure=on_failure)

    def _refresh_favorites_screen(self):
        if hasattr(self, 'manager') and self.manager:
            if self.manager.has_screen('favorites'):
                fav_screen = self.manager.get_screen('favorites')
                if hasattr(fav_screen, 'load_favorites'):
                    Clock.schedule_once(lambda dt: fav_screen.load_favorites(), 0.5)

    def go_back(self, instance=None):
        """Возврат на предыдущий экран"""
        logger.info("🔙 Нажата кнопка возврата")

        if self.manager and self.manager.has_screen('song_detail'):
            screen_state.clear_pending_chord()
            self.manager.current = 'song_detail'
            logger.info("✅ Принудительный возврат на song_detail")
        elif self.manager and self.manager.has_screen('home'):
            self.manager.current = 'home'

    def on_enter(self):
        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            app.top_nav.set_custom_title("")
            app.top_nav._show_back_button()
            app.top_nav.back_btn.on_release = self.go_back
            app.top_nav.hide_search_button(True)
            app.top_nav.hide_profile_button(True)

    def on_leave(self):
        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            app.top_nav.reset_to_default()
            app.top_nav.hide_search_button(False)
            app.top_nav.hide_profile_button(False)