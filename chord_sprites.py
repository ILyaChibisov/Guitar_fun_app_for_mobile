# chord_sprites.py
"""
Централизованное хранилище спрайтов для аккордов
"""
import base64
from kivy.core.image import Image as CoreImage
from io import BytesIO
from kivy.logger import Logger
import traceback

# Импортируем спрайты
try:
    from sprite_images import SPRITE_IMAGES

    Logger.info(f"SpriteLoader: Загружено {len(SPRITE_IMAGES)} спрайтов из sprite_images.py")
except ImportError as e:
    Logger.error(f"SpriteLoader: Ошибка импорта sprite_images.py: {e}")
    SPRITE_IMAGES = {}


class SpriteLoader:
    _instance = None
    _cache = {}
    _missing_sprites = set()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._cache = {}
            cls._instance._missing_sprites = set()
            Logger.info("SpriteLoader: Инициализирован")
        return cls._instance

    def get_texture(self, sprite_name):
        """Возвращает текстуру спрайта по имени"""
        if sprite_name in self._cache:
            return self._cache[sprite_name]

        if sprite_name not in SPRITE_IMAGES:
            if sprite_name not in self._missing_sprites:
                self._missing_sprites.add(sprite_name)
                Logger.warning(f"SpriteLoader: Спрайт не найден: {sprite_name}")
            return None

        try:
            img_data = base64.b64decode(SPRITE_IMAGES[sprite_name])
            img = CoreImage(BytesIO(img_data), ext="png")
            texture = img.texture

            if texture and texture.width > 0:
                self._cache[sprite_name] = texture
                Logger.debug(f"SpriteLoader: Загружен {sprite_name} ({texture.width}x{texture.height})")
                return texture
            else:
                Logger.error(f"SpriteLoader: Пустая текстура для {sprite_name}")
                return None

        except Exception as e:
            Logger.error(f"SpriteLoader: Ошибка загрузки {sprite_name}: {e}")
            return None

    def get_note_sprite(self, note_name, size=50):
        clean_note = note_name.replace('#', 'sharp')
        return self.get_texture(f"note_{clean_note}_{size}")

    def get_finger_sprite(self, finger_num, size=50):
        return self.get_texture(f"finger_{finger_num}_{size}")

    def get_x_sprite(self, size=50):
        return self.get_texture(f"x_{size}")

    def get_barre_sprite(self, style, width, height):
        return self.get_texture(f"barre_{style}_{width}x{height}")

    def get_fret_sprite(self, symbol, size=30, color="white"):
        """
        Возвращает спрайт лада с указанным цветом.

        Args:
            symbol: номер лада (2, 3, 4, 5 и т.д.)
            size: размер спрайта
            color: "black" или "white" (по умолчанию "white")
        """
        # Формируем имя спрайта
        if color == "white":
            sprite_name = f"fret_{symbol}_{size}_white"
        else:
            sprite_name = f"fret_{symbol}_{size}"

        # Если белого нет — пробуем чёрный как fallback
        texture = self.get_texture(sprite_name)
        if texture is None and color == "white":
            # Fallback на чёрный
            fallback_name = f"fret_{symbol}_{size}"
            Logger.warning(f"SpriteLoader: Белый спрайт {sprite_name} не найден, используем {fallback_name}")
            texture = self.get_texture(fallback_name)

        return texture


sprite_loader = SpriteLoader()