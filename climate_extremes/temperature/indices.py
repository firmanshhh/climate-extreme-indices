"""
Implementasi utama fungsi idxTemp() sesuai standar ETCCDI.
"""

import pandas as pd
import numpy as np
from typing import Optional
from climate_extremes.constants import (  # ← ABSOLUTE IMPORT
    DEFAULT_BASELINE_START, DEFAULT_BASELINE_END,
    OUTPUT_DECIMALS_TEMPERATURE
)
from climate_extremes.validation import validate_timeseries, validate_temperature_data  # ← ABSOLUTE IMPORT
from climate_extremes.temperature.percentiles import (  # ← ABSOLUTE IMPORT
    calculate_percentile_thresholds,
    calculate_percentile_indices
)
from climate_extremes.temperature.spells import calculate_wsdi_csdi  # ← ABSOLUTE IMPORT

def idxTemp(
    df: pd.DataFrame,
    tave: str,
    tmax: str,
    tmin: str,
    ref_start: int = DEFAULT_BASELINE_START,
    ref_end: int = DEFAULT_BASELINE_END
) -> pd.DataFrame:
    """
    Hitung 22 indeks ekstrem suhu harian berdasarkan definisi ETCCDI.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame dengan kolom 'time' (datetime) dan kolom suhu
    tave : str
        Nama kolom suhu rata-rata harian (°C)
    tmax : str
        Nama kolom suhu maksimum harian (°C)
    tmin : str
        Nama kolom suhu minimum harian (°C)
    ref_start : int, optional
        Tahun awal periode baseline (default: 1991)
    ref_end : int, optional
        Tahun akhir periode baseline (default: 2020)
    
    Returns
    -------
    pd.DataFrame
        DataFrame indeks ekstrem suhu agregat tahunan dengan 22 kolom indeks
        
    Raises
    ------
    ValueError
        Jika validasi data gagal atau periode baseline tidak memiliki data valid
    """
    # Validasi input
    valid, msg = validate_timeseries(df)
    if not valid:
        raise ValueError(f"Validasi time series gagal: {msg}")
    
    valid, msg = validate_temperature_data(df, tave, tmax, tmin)
    if not valid:
        raise ValueError(f"Validasi data suhu gagal: {msg}")
    
    # Persiapan data
    df = df.copy()
    df['time'] = pd.to_datetime(df['time'])
    df['YEAR'] = df['time'].dt.year
    df['MONTH'] = df['time'].dt.month
    df['DAY'] = df['time'].dt.day
    
    # Hitung DTR (Diurnal Temperature Range)
    df['DTR'] = df[tmax] - df[tmin]
    
    # === PERHITUNGAN THRESHOLD PERSENTIL ===
    p10_tmin, p90_tmax = calculate_percentile_thresholds(df, tmin, ref_start, ref_end)
    p10_tave, p90_tave = calculate_percentile_thresholds(df, tave, ref_start, ref_end)
    p10_tmax, p90_tmax_existing = calculate_percentile_thresholds(df, tmax, ref_start, ref_end)
    
    # === PERHITUNGAN INDEKS PERSENTIL ===
    # Untuk Tave
    Tm10P, Tm90P, Tm10, Tm90 = calculate_percentile_indices(df, tave, p10_tave, p90_tave)
    # Untuk Tmin
    Tn10P, Tn90P, Tn10, Tn90 = calculate_percentile_indices(df, tmin, p10_tmin, p90_tmax)
    # Untuk Tmax
    Tx10P, Tx90P, Tx10, Tx90 = calculate_percentile_indices(df, tmax, p10_tmax, p90_tmax_existing)
    
    # === PERHITUNGAN SPELL (WSDI/CSDI) ===
    WSDI, CSDI = calculate_wsdi_csdi(df, tmax, tmin, p90_tmax_existing, p10_tmin)
    
    # === PERHITUNGAN INDEKS STATISTIK DASAR ===
    # Helper function untuk agregasi tahunan yang robust terhadap NaN
    def yearly_agg(series, func):
        return series.groupby(df['YEAR']).apply(
            lambda x: np.nan if x.isna().all() else func(x.dropna())
        )
    
    TMm = yearly_agg(df[tave], np.mean)
    TMx = yearly_agg(df[tave], np.max)
    TMn = yearly_agg(df[tave], np.min)
    
    TXm = yearly_agg(df[tmax], np.mean)
    TXx = yearly_agg(df[tmax], np.max)
    TXn = yearly_agg(df[tmax], np.min)
    
    TNm = yearly_agg(df[tmin], np.mean)
    TNx = yearly_agg(df[tmin], np.max)
    TNn = yearly_agg(df[tmin], np.min)
    
    DTR_mean = yearly_agg(df['DTR'], np.mean)
    ETR = TXx - TNn
    
    # === KOMPILASI HASIL ===
    result = pd.DataFrame({
        'TMm': TMm.round(OUTPUT_DECIMALS_TEMPERATURE),
        'TMx': TMx.round(OUTPUT_DECIMALS_TEMPERATURE),
        'TMn': TMn.round(OUTPUT_DECIMALS_TEMPERATURE),
        'TXm': TXm.round(OUTPUT_DECIMALS_TEMPERATURE),
        'TXx': TXx.round(OUTPUT_DECIMALS_TEMPERATURE),
        'TXn': TXn.round(OUTPUT_DECIMALS_TEMPERATURE),
        'TNm': TNm.round(OUTPUT_DECIMALS_TEMPERATURE),
        'TNx': TNx.round(OUTPUT_DECIMALS_TEMPERATURE),
        'TNn': TNn.round(OUTPUT_DECIMALS_TEMPERATURE),
        'DTR': DTR_mean.round(OUTPUT_DECIMALS_TEMPERATURE),
        'ETR': ETR.round(OUTPUT_DECIMALS_TEMPERATURE),
        'Tm10P': Tm10P.round(OUTPUT_DECIMALS_TEMPERATURE),
        'Tm90P': Tm90P.round(OUTPUT_DECIMALS_TEMPERATURE),
        'Tn10P': Tn10P.round(OUTPUT_DECIMALS_TEMPERATURE),
        'Tn90P': Tn90P.round(OUTPUT_DECIMALS_TEMPERATURE),
        'Tx10P': Tx10P.round(OUTPUT_DECIMALS_TEMPERATURE),
        'Tx90P': Tx90P.round(OUTPUT_DECIMALS_TEMPERATURE),
        'Tm10': Tm10.round(OUTPUT_DECIMALS_TEMPERATURE),
        'Tm90': Tm90.round(OUTPUT_DECIMALS_TEMPERATURE),
        'Tn10': Tn10.round(OUTPUT_DECIMALS_TEMPERATURE),
        'Tn90': Tn90.round(OUTPUT_DECIMALS_TEMPERATURE),
        'Tx10': Tx10.round(OUTPUT_DECIMALS_TEMPERATURE),
        'Tx90': Tx90.round(OUTPUT_DECIMALS_TEMPERATURE),
        'WSDI': WSDI,
        'CSDI': CSDI
    })
    
    result.index.name = 'YEAR'
    return result