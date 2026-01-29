"""
Perhitungan persentil dan indeks berbasis persentil untuk data suhu.
"""

import pandas as pd
import numpy as np
from typing import Tuple
from climate_extremes.constants import PERCENTILE_10, PERCENTILE_90  # ← ABSOLUTE IMPORT

def calculate_percentile_thresholds(
    df: pd.DataFrame,
    var_col: str,
    ref_start: int,
    ref_end: int
) -> Tuple[float, float]:
    """
    Hitung threshold 10th dan 90th percentile dari periode baseline.
    
    Returns
    -------
    Tuple[float, float] : (p10, p90)
    """
    ref_mask = (df['YEAR'] >= ref_start) & (df['YEAR'] <= ref_end)
    ref_data = df.loc[ref_mask, var_col].dropna()
    
    if len(ref_data) == 0:
        raise ValueError(f"Tidak ada data valid pada periode baseline {ref_start}-{ref_end} untuk kolom {var_col}")
    
    p10 = ref_data.quantile(PERCENTILE_10)
    p90 = ref_data.quantile(PERCENTILE_90)
    return p10, p90


def calculate_percentile_indices(
    df: pd.DataFrame,
    var_col: str,
    p10: float,
    p90: float
) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
    """
    Hitung indeks persentil untuk satu variabel suhu.
    
    Returns
    -------
    Tuple containing:
        - percent_below_10: Persentase hari < p10 (%)
        - percent_above_90: Persentase hari > p90 (%)
        - count_below_10: Jumlah absolut hari < p10
        - count_above_90: Jumlah absolut hari > p90
    """
    def calc_percent(arr):
        if np.isnan(arr).all():
            return np.nan
        valid = arr[~np.isnan(arr)]
        if len(valid) == 0:
            return np.nan
        below = (valid < p10).sum()
        above = (valid > p90).sum()
        return below / len(valid) * 100, above / len(valid) * 100, below, above
    
    # Group by year dan hitung
    grouped = df.groupby('YEAR')[var_col].apply(calc_percent)
    
    # Ekstrak komponen
    percent_below_10 = grouped.apply(lambda x: x[0] if not pd.isna(x) else np.nan)
    percent_above_90 = grouped.apply(lambda x: x[1] if not pd.isna(x) else np.nan)
    count_below_10 = grouped.apply(lambda x: x[2] if not pd.isna(x) else np.nan)
    count_above_90 = grouped.apply(lambda x: x[3] if not pd.isna(x) else np.nan)
    
    return percent_below_10, percent_above_90, count_below_10, count_above_90