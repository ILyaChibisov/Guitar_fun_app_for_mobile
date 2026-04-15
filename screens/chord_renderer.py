# screens/chord_renderer.py
"""
Класс для отображения грифа с наложенными изображениями аккордов
"""
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.image import Image
from kivy.graphics import Color, Rectangle
from io import BytesIO


class ChordRenderer(RelativeLayout):
    """Виджет для отображения грифа с наложенными изображениями аккордов"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_image_data = None

        # Картинка грифа (фон)
        self.griff_image = Image(
            allow_stretch=True,
            keep_ratio=True,
            size_hint=(1, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        self.add_widget(self.griff_image)

        # Картинка с элементами аккорда (поверх)
        self.chord_image = Image(
            allow_stretch=True,
            keep_ratio=True,
            size_hint=(1, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        self.add_widget(self.chord_image)

    def set_background(self, texture):
        """Устанавливает текстуру фона грифа"""
        self.griff_image.texture = texture

    def set_chord_image(self, image_data):
        """Устанавливает изображение аккорда поверх грифа"""
        if image_data:
            from kivy.core.image import Image as CoreImage
            img = CoreImage(BytesIO(image_data), ext="png")
            self.chord_image.texture = img.texture
        else:
            self.chord_image.texture = None