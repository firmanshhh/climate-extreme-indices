"""
Deteksi Consecutive Dry Days (CDD) dan Consecutive Wet Days (CWD)
sesuai definisi ETCCDI dengan penanganan robust terhadap missing data.
Diperbaiki untuk kompatibilitas pandas >=2.1.
"""

import numpy as np
import pandas as pd
from typing import Tuple
from climate_extremes.constants import WET_DAY_THRESHOLD

def calculate_cdd_cwd(
    series: pd.Series,
    wet_threshold: float = WET_DAY_THRESHOLD
) -> Tuple[int, int]:
    """
    Hitung maksimum Consecutive Dry Days (CDD) dan Consecutive Wet Days (CWD).
    
    Parameters
    ----------
    series : pd.Series
        Data curah hujan harian untuk satu tahun
    wet_threshold : float
        Threshold untuk mendefinisikan hari basah (default: 1.0 mm)
    
    Returns
    -------
    Tuple[int, int]
        (CDD, CWD) dalam satuan hari
    """
    if series.isna().all():
        return np.nan, np.nan
    
    values = series.values.astype(float)
    max_cdd = current_cdd = 0
    max_cwd = current_cwd = 0
    
    for val in values:
        if np.isnan(val):
            current_cdd = 0
            current_cwd = 0
            continue
        
        if val < wet_threshold:
            current_cdd += 1
            max_cdd = max(max_cdd, current_cdd)
            current_cwd = 0
        else:
            current_cwd += 1
            max_cwd = max(max_cwd, current_cwd)
            current_cdd = 0
    
    return max_cdd, max_cwd


def calculate_cdd_cwd_yearly(
    df: pd.DataFrame,
    rain_col: str,
    wet_threshold: float = WET_DAY_THRESHOLD
) -> Tuple[pd.Series, pd.Series]:
    """
    Hitung CDD dan CWD untuk seluruh tahun dalam dataset.
    Diperbaiki untuk kompatibilitas pandas >=2.1 (hindari FutureWarning).
    """
    years = sorted(df['YEAR'].unique())
    cdd_series = pd.Series(index=years, dtype=float)
    cwd_series = pd.Series(index=years, dtype=float)
    
    for year in years:
        year_data = df[df['YEAR'] == year][rain_col]
        cdd, cwd = calculate_cdd_cwd(year_data, wet_threshold)
        cdd_series.loc[year] = cdd
        cwd_series.loc[year] = cwd
    
    return cdd_series, cwd_series