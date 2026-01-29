"""
Deteksi Consecutive Dry Days (CDD) dan Consecutive Wet Days (CWD)
sesuai definisi ETCCDI dengan penanganan robust terhadap missing data.
"""

import numpy as np
import pandas as pd
from typing import Tuple
from climate_extremes.constants import WET_DAY_THRESHOLD  # ← ABSOLUTE IMPORT

def calculate_cdd_cwd(
    series: pd.Series,
    wet_threshold: float = WET_DAY_THRESHOLD
) -> Tuple[int, int]:
    """
    Hitung maksimum Consecutive Dry Days (CDD) dan Consecutive Wet Days (CWD).
    
    Parameters
    ----------
    series : pd.Series
        Data curah hujan harian untuk satu tahun (dengan index datetime opsional)
    wet_threshold : float
        Threshold untuk mendefinisikan hari basah (default: 1.0 mm)
    
    Returns
    -------
    Tuple[int, int]
        (CDD, CWD) dalam satuan hari
        
    Notes
    -----
    - Missing data (NaN) dianggap MEMUTUS spell (conservative approach sesuai ETCCDI)
    - Hari kering: curah hujan < wet_threshold
    - Hari basah: curah hujan ≥ wet_threshold
    """
    if series.isna().all():
        return np.nan, np.nan
    
    # Konversi ke array numpy untuk efisiensi
    values = series.values.astype(float)
    
    # Inisialisasi counters
    max_cdd = current_cdd = 0
    max_cwd = current_cwd = 0
    
    for val in values:
        # Missing data memutus spell
        if np.isnan(val):
            current_cdd = 0
            current_cwd = 0
            continue
        
        # Update CDD (Consecutive Dry Days)
        if val < wet_threshold:
            current_cdd += 1
            max_cdd = max(max_cdd, current_cdd)
            current_cwd = 0  # Reset CWD
        else:  # Hari basah
            current_cwd += 1
            max_cwd = max(max_cwd, current_cwd)
            current_cdd = 0  # Reset CDD
    
    return max_cdd, max_cwd


def calculate_cdd_cwd_yearly(
    df: pd.DataFrame,
    rain_col: str,
    wet_threshold: float = WET_DAY_THRESHOLD
) -> Tuple[pd.Series, pd.Series]:
    """
    Hitung CDD dan CWD untuk seluruh tahun dalam dataset.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame dengan kolom 'YEAR' dan curah hujan
    rain_col : str
        Nama kolom curah hujan
    wet_threshold : float
        Threshold hari basah (default: 1.0 mm)
    
    Returns
    -------
    Tuple[pd.Series, pd.Series]
        (CDD_series, CWD_series) dengan index YEAR
    """
    def calc_for_year(group):
        cdd, cwd = calculate_cdd_cwd(group[rain_col], wet_threshold)
        return pd.Series({'CDD': cdd, 'CWD': cwd})
    
    result = df.groupby('YEAR').apply(calc_for_year)
    return result['CDD'], result['CWD']