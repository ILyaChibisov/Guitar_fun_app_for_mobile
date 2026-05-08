# screens/recycle_artist_card.py
"""
Переиспользуемая карточка исполнителя для RecycleView
"""
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty, NumericProperty, ObjectProperty
from kivy.metrics import dp, sp
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel

# Предзагруженная текстура иконки (ОДНА на все карточки)
_shared_icon_texture = None


def set_shared_icon(texture):
    """Устанавливает общую текстуру для всех карточек"""
    global _shared_icon_texture
    _shared_icon_texture = texture


class RecycleArtistCard(RecycleDataViewBehavior, MDCard):
    """Карточка для RecycleView - переиспользуемая"""

    artist = StringProperty('')
    songs_count = NumericProperty(0)
    on_click = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = dp(64)  # Фиксированная высота - максимальная скорость!
        self.padding = [dp(16), dp(10), dp(12), dp(10)]
        self.spacing = dp(14)
        self.radius = [dp(20), dp(20), dp(20), dp(20)]
        self.elevation = 0
        self.ripple_behavior = True
        self.theme_bg_color = "Custom"
        self.md_bg_color = [1, 1, 1, 0.08]

        self._build_ui()

    def _build_ui(self):
        from kivy.uix.image import Image

        # Иконка - ОДНА на все карточки (ссылка на текстуру)
        self.icon = Image(
            size_hint=(None, None),
            size=(dp(32), dp(32)),
            pos_hint={'center_y': 0.5},
            allow_stretch=True,
            keep_ratio=True
        )
        if _shared_icon_texture:
            self.icon.texture = _shared_icon_texture

        # Текстовая часть
        text_layout = BoxLayout(
            orientation='vertical',
            size_hint_x=1,
            spacing=dp(2),
            pos_hint={'center_y': 0.5}
        )

        self.artist_label = MDLabel(
            font_size=sp(16),
            size_hint_y=None,
            height=dp(26),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.95],
            bold=True,
            shorten=True,
            shorten_from="right"
        )

        self.songs_label = MDLabel(
            font_size=sp(11),
            size_hint_y=None,
            height=dp(22),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.5]
        )

        text_layout.add_widget(self.artist_label)
        text_layout.add_widget(self.songs_label)

        # Стрелка
        arrow = MDLabel(
            text="›",
            font_size=sp(28),
            size_hint_x=None,
            width=dp(28),
            halign="center",
            theme_text_color="Custom",
            text_color=[0.46, 0.70, 0.71, 0.5]
        )

        self.add_widget(self.icon)
        self.add_widget(text_layout)
        self.add_widget(arrow)

    def refresh_view_attrs(self, rv, index, data):
        """Обновляет данные при переиспользовании карточки"""
        self.artist = data.get('artist', '')
        self.songs_count = data.get('songs_count', 0)
        self.on_click = data.get('on_click')

        self.artist_label.text = self.artist

        count = self.songs_count
        if count == 1:
            suffix = "песня"
        elif 2 <= count <= 4:
            suffix = "песни"
        else:
            suffix = "песен"
        self.songs_label.text = f"• {count} {suffix}"

        return super().refresh_view_attrs(rv, index, data)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if self.on_click:
                self.on_click(self.artist, self.songs_count)
            return True
        return super().on_touch_down(touch)


class ArtistRecycleView(RecycleView):
    """Виртуализированный список исполнителей"""

    def __init__(self, on_artist_click=None, **kwargs):
        super().__init__(**kwargs)
        self.on_artist_click = on_artist_click

        # Отключаем анимацию прокрутки для скорости
        self.animate_scroll = False
        self.bar_color = [1, 1, 1, 0.2]
        self.bar_width = dp(3)

        # Создаём layout ПРАВИЛЬНО - без использования minimum_height здесь
        self.layout_manager = RecycleBoxLayout(
            default_size=(None, dp(64)),  # Фиксированная высота!
            default_size_hint=(1, None),
            size_hint_y=None,
            height=dp(64) * 10,  # Временная высота, потом пересчитается автоматически
            orientation='vertical',
            spacing=dp(8)
        )

        # Привязываем обновление высоты
        self.layout_manager.bind(minimum_height=self.layout_manager.setter('height'))

        # Устанавливаем viewclass и layout
        self.viewclass = 'RecycleArtistCard'
        self.add_widget(self.layout_manager)

    def set_artists(self, artists, on_click):
        """Быстрое обновление списка"""
        data = []
        for artist_data in artists:
            artist_name = artist_data.get('artist')
            songs_count = artist_data.get('songs_count', 0)
            if artist_name:
                data.append({
                    'artist': artist_name,
                    'songs_count': songs_count,
                    'on_click': on_click
                })

        # Мгновенное обновление через batch assign
        self.data = data
        self.refresh_from_data()

    def clear(self):
        """Очищает все данные"""
        self.data = []
        self.refresh_from_data()