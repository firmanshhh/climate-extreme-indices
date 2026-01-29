"""
Helper functions umum untuk perhitungan indeks ekstrem.
"""

import numpy as np
import pandas as pd
from typing import Callable

def is_all_nan(arr: np.ndarray) -> bool:
    """Cek apakah array seluruhnya NaN."""
    return np.isnan(arr).all()

def count_consecutive_days(
    series: pd.Series, 
    condition_func: Callable[[pd.Series], pd.Series],
    min_spell_length: int = 6
) -> float:
    """
    Hitung total hari dalam spell yang memenuhi kriteria minimal panjang.
    
    Parameters
    ----------
    series : pd.Series
        Data time series harian
    condition_func : Callable
        Fungsi yang mengembalikan boolean mask (True = memenuhi kriteria)
    min_spell_length : int
        Minimal panjang spell berturut-turut (default: 6 hari)
    
    Returns
    -------
    float : Total hari dalam spell yang valid, atau np.nan jika semua data missing
    """
    if series.isna().all():
        return np.nan  # <-- KRUSIAL: return NaN bukan 0
    
    # Buat boolean mask dengan penanganan NaN
    mask = condition_func(series).fillna(False).astype(bool)
    
    # Deteksi spell menggunakan cumulative sum pada inverse mask
    groups = (~mask).cumsum()
    
    # Hitung panjang setiap spell
    spell_lengths = mask.groupby(groups).transform('sum')
    
    # Filter hanya spell yang memenuhi kriteria minimal
    valid_spell_mask = spell_lengths >= min_spell_length
    
    return float(valid_spell_mask.sum())  # Pastikan return float untuk konsistensi NaN


def rolling_sum(arr: np.ndarray, window: int) -> np.ndarray:
    """
    Hitung rolling sum dengan penanganan NaN yang robust.
    Mengembalikan array dengan nilai maksimum pada window yang valid.
    """
    if is_all_nan(arr) or len(arr) < window:
        return np.full(len(arr) - window + 1, np.nan)
    
    result = []
    for i in range(len(arr) - window + 1):
        window_data = arr[i:i+window]
        if np.isnan(window_data).any():
            result.append(np.nan)
        else:
            result.append(np.sum(window_data))
    
    return np.array(result)

def safe_mean(arr: np.ndarray) -> float:
    """Hitung rata-rata dengan penanganan NaN."""
    valid = arr[~np.isnan(arr)]
    return np.nan if len(valid) == 0 else valid.mean()

def safe_max(arr: np.ndarray) -> float:
    """Hitung maksimum dengan penanganan NaN."""
    valid = arr[~np.isnan(arr)]
    return np.nan if len(valid) == 0 else valid.max()

def safe_min(arr: np.ndarray) -> float:
    """Hitung minimum dengan penanganan NaN."""
    valid = arr[~np.isnan(arr)]
    return np.nan if len(valid) == 0 else valid.min()