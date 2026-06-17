# dicts/ru/__init__.py
"""
Русские термины по буквам
"""
from .ru_01_a import TERMS as А_TERMS
from .ru_02_b import TERMS as Б_TERMS
from .ru_03_v import TERMS as В_TERMS
from .ru_04_g import TERMS as Г_TERMS
from .ru_05_d import TERMS as Д_TERMS
from .ru_06_e import TERMS as Е_TERMS
from .ru_07_yo import TERMS as YO_TERMS
from .ru_08_zh import TERMS as Ж_TERMS
from .ru_09_z import TERMS as З_TERMS
from .ru_10_i import TERMS as И_TERMS
from .ru_11_y import TERMS as Y_TERMS
from .ru_12_k import TERMS as К_TERMS
from .ru_13_l import TERMS as Л_TERMS
from .ru_14_m import TERMS as М_TERMS
from .ru_15_n import TERMS as Н_TERMS
from .ru_16_o import TERMS as О_TERMS
from .ru_17_p import TERMS as П_TERMS
from .ru_18_r import TERMS as Р_TERMS
from .ru_19_s import TERMS as С_TERMS
from .ru_20_t import TERMS as Т_TERMS
from .ru_21_u import TERMS as У_TERMS
from .ru_22_f import TERMS as Ф_TERMS
from .ru_23_kh import TERMS as Х_TERMS
from .ru_24_ts import TERMS as Ц_TERMS
from .ru_25_ch import TERMS as Ч_TERMS
from .ru_26_sh import TERMS as Ш_TERMS
from .ru_27_shch import TERMS as Щ_TERMS
from .ru_28_hard import TERMS as HARD_TERMS
from .ru_29_y import TERMS as Y_TERMS2
from .ru_30_soft import TERMS as SOFT_TERMS
from .ru_31_e import TERMS as E_TERMS2
from .ru_32_yu import TERMS as Ю_TERMS
from .ru_33_ya import TERMS as Я_TERMS

# Словарь для быстрого доступа по букве
RU_TERMS_BY_LETTER = {
    'а': А_TERMS,
    'б': Б_TERMS,
    'в': В_TERMS,
    'г': Г_TERMS,
    'д': Д_TERMS,
    'е': Е_TERMS,
    'ё': YO_TERMS,
    'ж': Ж_TERMS,
    'з': З_TERMS,
    'и': И_TERMS,
    'й': Y_TERMS,
    'к': К_TERMS,
    'л': Л_TERMS,
    'м': М_TERMS,
    'н': Н_TERMS,
    'о': О_TERMS,
    'п': П_TERMS,
    'р': Р_TERMS,
    'с': С_TERMS,
    'т': Т_TERMS,
    'у': У_TERMS,
    'ф': Ф_TERMS,
    'х': Х_TERMS,
    'ц': Ц_TERMS,
    'ч': Ч_TERMS,
    'ш': Ш_TERMS,
    'щ': Щ_TERMS,
    'ъ': HARD_TERMS,
    'ы': Y_TERMS2,
    'ь': SOFT_TERMS,
    'э': E_TERMS2,
    'ю': Ю_TERMS,
    'я': Я_TERMS,
}

def get_all_ru_terms():
    """Возвращает все русские термины"""
    all_terms = {}
    for letter, terms in RU_TERMS_BY_LETTER.items():
        if terms:
            all_terms.update(terms)
    return all_terms
