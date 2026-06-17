# dicts/en/__init__.py
"""
Английские термины по буквам
"""
from .en_01_a import TERMS as A_TERMS
from .en_02_b import TERMS as B_TERMS
from .en_03_c import TERMS as C_TERMS
from .en_04_d import TERMS as D_TERMS
from .en_05_e import TERMS as E_TERMS
from .en_06_f import TERMS as F_TERMS
from .en_07_g import TERMS as G_TERMS
from .en_08_h import TERMS as H_TERMS
from .en_09_i import TERMS as I_TERMS
from .en_10_j import TERMS as J_TERMS
from .en_11_k import TERMS as K_TERMS
from .en_12_l import TERMS as L_TERMS
from .en_13_m import TERMS as M_TERMS
from .en_14_n import TERMS as N_TERMS
from .en_15_o import TERMS as O_TERMS
from .en_16_p import TERMS as P_TERMS
from .en_17_q import TERMS as Q_TERMS
from .en_18_r import TERMS as R_TERMS
from .en_19_s import TERMS as S_TERMS
from .en_20_t import TERMS as T_TERMS
from .en_21_u import TERMS as U_TERMS
from .en_22_v import TERMS as V_TERMS
from .en_23_w import TERMS as W_TERMS
from .en_24_x import TERMS as X_TERMS
from .en_25_y import TERMS as Y_TERMS
from .en_26_z import TERMS as Z_TERMS

# Словарь для быстрого доступа по букве
EN_TERMS_BY_LETTER = {
    'a': A_TERMS,
    'b': B_TERMS,
    'c': C_TERMS,
    'd': D_TERMS,
    'e': E_TERMS,
    'f': F_TERMS,
    'g': G_TERMS,
    'h': H_TERMS,
    'i': I_TERMS,
    'j': J_TERMS,
    'k': K_TERMS,
    'l': L_TERMS,
    'm': M_TERMS,
    'n': N_TERMS,
    'o': O_TERMS,
    'p': P_TERMS,
    'q': Q_TERMS,
    'r': R_TERMS,
    's': S_TERMS,
    't': T_TERMS,
    'u': U_TERMS,
    'v': V_TERMS,
    'w': W_TERMS,
    'x': X_TERMS,
    'y': Y_TERMS,
    'z': Z_TERMS,
}

def get_all_en_terms():
    """Возвращает все английские термины"""
    all_terms = {}
    for letter, terms in EN_TERMS_BY_LETTER.items():
        if terms:
            all_terms.update(terms)
    return all_terms
