"""
Deteksi spell panas (WSDI) dan spell dingin (CSDI) untuk data suhu.
"""

import pandas as pd
import numpy as np
from typing import Tuple
from climate_extremes.utils import count_consecutive_days
from climate_extremes.constants import MIN_SPELL_DAYS

def calculate_wsdi_csdi(
    df: pd.DataFrame,
    tmax_col: str,
    tmin_col: str,
    p90_tmax: float,
    p10_tmin: float
) -> Tuple[pd.Series, pd.Series]:
    """
    Hitung Warm Spell Duration Index (WSDI) dan Cold Spell Duration Index (CSDI).
    
    Parameters
    ----------
    df : pd.DataFrame
        Data harian dengan kolom YEAR dan suhu
    tmax_col : str
        Nama kolom suhu maksimum
    tmin_col : str
        Nama kolom suhu minimum
    p90_tmax : float
        Threshold 90th percentile untuk Tmax
    p10_tmin : float
        Threshold 10th percentile untuk Tmin
    
    Returns
    -------
    Tuple[pd.Series, pd.Series] : (WSDI, CSDI) dalam hari per tahun (float type untuk konsistensi NaN)
    """
    # Buat boolean mask untuk spell
    df = df.copy()
    df['_warm_day'] = df[tmax_col] > p90_tmax
    df['_cold_day'] = df[tmin_col] < p10_tmin
    
    # Hitung WSDI per tahun
    wsdi = df.groupby('YEAR').apply(
        lambda g: count_consecutive_days(
            g['_warm_day'], 
            lambda x: x,  # identity function untuk boolean series
            min_spell_length=MIN_SPELL_DAYS
        )
    )
    
    # Hitung CSDI per tahun
    csdi = df.groupby('YEAR').apply(
        lambda g: count_consecutive_days(
            g['_cold_day'],
            lambda x: x,
            min_spell_length=MIN_SPELL_DAYS
        )
    )
    
    # Pastikan tipe data float untuk konsistensi NaN
    wsdi = wsdi.astype(float)
    csdi = csdi.astype(float)
    
    # Cleanup temporary columns
    df.drop(columns=['_warm_day', '_cold_day'], inplace=True, errors='ignore')
    
    return wsdi, csdi