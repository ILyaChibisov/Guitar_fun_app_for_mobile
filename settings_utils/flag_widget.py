# settings_utils/flag_widget.py
import base64
import io
from kivy.core.image import Image as CoreImage
from kivy.metrics import dp
from kivy.uix.image import Image

from data.settings import flag_assets

_FLAG_TEXTURES_CACHE = {}


def get_waving_flag_texture(lang_code):
    """Возвращает закэшированную текстуру развевающегося 3D-флага для lang_code."""
    if lang_code in _FLAG_TEXTURES_CACHE:
        return _FLAG_TEXTURES_CACHE[lang_code]

    b64_str = flag_assets.FLAGS_PNG_BASE64.get(lang_code)
    if not b64_str:
        return None

    raw_bytes = base64.b64decode(b64_str)
    tex = CoreImage(io.BytesIO(raw_bytes), ext="png").texture
    _FLAG_TEXTURES_CACHE[lang_code] = tex
    return tex


class WavingFlagImage(Image):
    """Готовый виджет развевающегося флага с пропорциями 3:2."""

    def __init__(self, lang_code, flag_width=dp(52), flag_height=dp(35), **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (flag_width, flag_height)
        self.pos_hint = {"center_x": 0.5}
        self.allow_stretch = True
        self.keep_ratio = True

        tex = get_waving_flag_texture(lang_code)
        if tex:
            self.texture = tex
