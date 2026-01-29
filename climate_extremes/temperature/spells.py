"""
Deteksi spell panas (WSDI) dan spell dingin (CSDI) untuk data suhu.
Diperbaiki untuk kompatibilitas pandas >=2.1 (hilangkan FutureWarning).
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
    Tuple[pd.Series, pd.Series] : (WSDI, CSDI) dalam hari per tahun (float type)
    """
    # Buat boolean mask untuk spell
    df = df.copy()
    df['_warm_day'] = df[tmax_col] > p90_tmax
    df['_cold_day'] = df[tmin_col] < p10_tmin
    
    # === PERBAIKAN: GANTI groupby().apply() DENGAN LOOP EKSPLISIT ===
    # Hindari FutureWarning di pandas >=2.1 dengan tidak menggunakan apply pada grouping columns
    years = sorted(df['YEAR'].unique())
    wsdi = pd.Series(index=years, dtype=float)
    csdi = pd.Series(index=years, dtype=float)
    
    for year in years:
        year_data = df[df['YEAR'] == year]
        
        # Hitung WSDI untuk tahun ini
        wsdi_val = count_consecutive_days(
            year_data['_warm_day'], 
            lambda x: x,
            min_spell_length=MIN_SPELL_DAYS
        )
        wsdi.loc[year] = wsdi_val
        
        # Hitung CSDI untuk tahun ini
        csdi_val = count_consecutive_days(
            year_data['_cold_day'],
            lambda x: x,
            min_spell_length=MIN_SPELL_DAYS
        )
        csdi.loc[year] = csdi_val
    
    # Pastikan tipe data float untuk konsistensi NaN
    wsdi = wsdi.astype(float)
    csdi = csdi.astype(float)
    
    # Cleanup temporary columns
    df.drop(columns=['_warm_day', '_cold_day'], inplace=True, errors='ignore')
    
    return wsdi, csdi