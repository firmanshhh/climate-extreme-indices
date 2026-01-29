"""
Modul indeks ekstrem curah hujan berbasis standar ETCCDI.
Mengimplementasikan 22+ indeks dengan sistem QC robust untuk wilayah tropis.
"""

from .indices import idxRain
from .extremes import calculate_r95p_r99p
from .spells import calculate_cdd_cwd, calculate_cdd_cwd_yearly

__all__ = [
    'idxRain',
    'calculate_r95p_r99p',
    'calculate_cdd_cwd',
    'calculate_cdd_cwd_yearly'
]