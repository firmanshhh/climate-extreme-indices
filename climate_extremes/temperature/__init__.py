"""
Modul indeks ekstrem suhu berbasis standar ETCCDI.
Mengimplementasikan 22 indeks termasuk spell detection (WSDI/CSDI).
"""

from .indices import idxTemp
from .spells import calculate_wsdi_csdi
from .percentiles import calculate_percentile_thresholds, calculate_percentile_indices

__all__ = [
    'idxTemp',
    'calculate_wsdi_csdi',
    'calculate_percentile_thresholds',
    'calculate_percentile_indices'
]