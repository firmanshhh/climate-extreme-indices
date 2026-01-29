"""
Perhitungan indeks ekstrem berbasis persentil (R95p, R99p) untuk curah hujan.
"""

import numpy as np
import pandas as pd
from typing import Tuple

def calculate_r95p_r99p(
    series: pd.Series,
    r95p_threshold: float,
    r99p_threshold: float,
    wet_day_threshold: float = 1.0
) -> Tuple[float, float]:
    """
    Hitung total curah hujan dari hari ekstrem (>95p/99p percentile).
    
    Parameters
    ----------
    series : pd.Series
        Data curah hujan harian untuk satu tahun
    r95p_threshold : float
        Threshold 95th percentile dari baseline
    r99p_threshold : float
        Threshold 99th percentile dari baseline
    wet_day_threshold : float
        Threshold hari basah (>1.0 mm)
    
    Returns
    -------
    Tuple[float, float] : (R95P, R99P) dalam mm
    """
    if series.isna().all():
        return np.nan, np.nan
    
    # Filter hanya hari basah (> wet_day_threshold)
    wet_days = series[series > wet_day_threshold].dropna()
    
    if len(wet_days) == 0:
        return np.nan, np.nan
    
    # Hitung total curah hujan dari hari ekstrem
    r95p = wet_days[wet_days > r95p_threshold].sum() if not np.isnan(r95p_threshold) else np.nan
    r99p = wet_days[wet_days > r99p_threshold].sum() if not np.isnan(r99p_threshold) else np.nan
    
    return r95p, r99p