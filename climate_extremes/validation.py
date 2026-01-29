"""
Validasi data input untuk memastikan kualitas sebelum perhitungan indeks ekstrem.
"""

import pandas as pd
import numpy as np
from typing import Tuple

def validate_timeseries(
    df: pd.DataFrame, 
    time_col: str = 'time',
    min_days_per_year: int = 300
) -> Tuple[bool, str]:
    """Validasi struktur time series harian."""
    if time_col not in df.columns:
        return False, f"Kolom waktu '{time_col}' tidak ditemukan"
    
    if not pd.api.types.is_datetime64_any_dtype(df[time_col]):
        return False, f"Kolom '{time_col}' harus bertipe datetime"
    
    if df[time_col].isna().any():
        return False, "Terdapat missing values pada kolom waktu"
    
    # Cek resolusi harian (minimal hari/tahun)
    years = df[time_col].dt.year.unique()
    for year in years:
        days_in_year = df[df[time_col].dt.year == year].shape[0]
        if days_in_year < min_days_per_year:
            return False, f"Tahun {year} hanya memiliki {days_in_year} hari data (<{min_days_per_year})"
    
    return True, "OK"

def validate_temperature_data(
    df: pd.DataFrame, 
    tave_col: str, 
    tmax_col: str, 
    tmin_col: str
) -> Tuple[bool, str]:
    """Validasi konsistensi data suhu."""
    required_cols = [tave_col, tmax_col, tmin_col]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        return False, f"Kolom suhu tidak lengkap: {missing}"
    
    # Cek konsistensi logis: Tmin ≤ Tave ≤ Tmax
    invalid_mask = (
        (df[tmin_col] > df[tave_col] + 1e-6) |  # Toleransi floating point
        (df[tave_col] > df[tmax_col] + 1e-6)
    )
    invalid_count = invalid_mask.sum()
    if invalid_count > 0:
        return False, f"Terdapat {invalid_count} record dengan ketidakkonsistenan Tmin ≤ Tave ≤ Tmax"
    
    return True, "OK"

def validate_rainfall_data(df: pd.DataFrame, rain_col: str) -> Tuple[bool, str]:
    """Validasi data curah hujan untuk analisis ekstrem (tanpa pengecekan hari basah)."""
    if rain_col not in df.columns:
        return False, f"Kolom curah hujan '{rain_col}' tidak ditemukan"
    
    # Cek nilai negatif (tidak fisik)
    negative_count = (df[rain_col] < 0).sum()
    if negative_count > 0:
        return False, f"Terdapat {negative_count} nilai curah hujan negatif"
    
    # TIDAK ADA pengecekan "tidak ada hari basah" di sini - akan di-handle oleh QC system
    return True, "OK"

def check_data_completeness(
    df: pd.DataFrame, 
    col: str, 
    min_completeness: float = 0.80
) -> pd.Series:
    """
    Hitung persentase kelengkapan data per tahun.
    
    Returns
    -------
    pd.Series dengan index YEAR dan nilai persentase kelengkapan (0-100)
    """
    df = df.copy()
    df['YEAR'] = pd.to_datetime(df['time']).dt.year
    yearly_counts = df.groupby('YEAR')[col].count()
    expected_days = df.groupby('YEAR')['time'].apply(lambda x: x.dt.dayofyear.max() - x.dt.dayofyear.min() + 1)
    completeness = (yearly_counts / expected_days * 100).round(1)
    return completeness[completeness >= min_completeness * 100]