"""
Implementasi idxTemp dengan graceful degradation yang robust.
Menangani parameter missing tanpa menggagalkan seluruh perhitungan.
"""

import pandas as pd
import numpy as np
from typing import Optional, Union
from climate_extremes.constants import (
    DEFAULT_BASELINE_START, DEFAULT_BASELINE_END,
    OUTPUT_DECIMALS_TEMPERATURE, MIN_SPELL_DAYS, WET_DAY_THRESHOLD
)
from climate_extremes.validation import validate_timeseries
from climate_extremes.temperature.percentiles import (
    calculate_percentile_thresholds,
    calculate_percentile_indices
)
from climate_extremes.temperature.spells import calculate_wsdi_csdi

def idxTemp(
    df: pd.DataFrame,
    tave: Optional[str] = None,
    tmax: Optional[str] = None,
    tmin: Optional[str] = None,
    ref_start: int = DEFAULT_BASELINE_START,
    ref_end: int = DEFAULT_BASELINE_END,
    min_days_per_year: int = 300
) -> pd.DataFrame:
    """
    Hitung indeks ekstrem suhu dengan graceful degradation untuk data tidak lengkap.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame dengan kolom 'time' (datetime)
    tave : str or None
        Nama kolom suhu rata-rata harian (°C). None jika tidak tersedia.
    tmax : str or None
        Nama kolom suhu maksimum harian (°C). None jika tidak tersedia.
    tmin : str or None
        Nama kolom suhu minimum harian (°C). None jika tidak tersedia.
    ref_start : int
        Tahun awal periode baseline (default: 1991)
    ref_end : int
        Tahun akhir periode baseline (default: 2020)
    min_days_per_year : int
        Minimum hari data valid per tahun (default: 300)
    
    Returns
    -------
    pd.DataFrame
        DataFrame dengan:
        - Indeks ETCCDI (NaN jika parameter tidak tersedia)
        - Metadata QC: tmax_available_days, tmin_available_days, tave_available_days, qc_temperature_flag
    
    Examples
    --------
    # Kasus 1: Semua parameter tersedia
    >>> idxTemp(df, 'TAVE', 'TMAX', 'TMIN')
    
    # Kasus 2: Hanya TMAX dan TMIN tersedia (TAVE missing)
    >>> idxTemp(df, None, 'TMAX', 'TMIN')
    
    # Kasus 3: Hanya TMAX tersedia
    >>> idxTemp(df, None, 'TMAX', None)
    """
    # Validasi time series dasar (tanpa threshold ketat)
    valid, msg = validate_timeseries(df, min_days_per_year=1)
    if not valid:
        raise ValueError(f"Validasi time series gagal: {msg}")
    
    # Persiapan data
    df = df.copy()
    df['time'] = pd.to_datetime(df['time'])
    df['YEAR'] = df['time'].dt.year
    years = sorted(df['YEAR'].unique())
    
    # === HITUNG KETERSEDIAAN DATA PER PARAMETER ===
    avail = pd.DataFrame(index=years)
    
    def count_valid_days(param):
        if param is None or param not in df.columns:
            return pd.Series(0, index=years)
        return df.groupby('YEAR')[param].apply(lambda x: x.notna().sum())
    
    avail['tmax_available_days'] = count_valid_days(tmax)
    avail['tmin_available_days'] = count_valid_days(tmin)
    avail['tave_available_days'] = count_valid_days(tave)
    
    # QC flag per tahun
    def get_qc_flag(row):
        flags = []
        if row['tmax_available_days'] >= min_days_per_year:
            flags.append('TMAX')
        if row['tmin_available_days'] >= min_days_per_year:
            flags.append('TMIN')
        if row['tave_available_days'] >= min_days_per_year:
            flags.append('TAVE')
        if not flags:
            return 'NO_DATA'
        return '_'.join(flags) if len(flags) > 1 else f"{flags[0]}_ONLY"
    
    avail['qc_temperature_flag'] = avail.apply(get_qc_flag, axis=1)
    
    # === INISIALISASI RESULT DENGAN NaN ===
    all_index_cols = [
        'TMm', 'TMx', 'TMn', 'TXm', 'TXx', 'TXn', 'TNm', 'TNx', 'TNn',
        'DTR', 'ETR', 'Tm10P', 'Tm90P', 'Tn10P', 'Tn90P', 'Tx10P', 'Tx90P',
        'Tm10', 'Tm90', 'Tn10', 'Tn90', 'Tx10', 'Tx90', 'WSDI', 'CSDI'
    ]
    result = pd.DataFrame(index=years, columns=all_index_cols, dtype=float)
    result[:] = np.nan  # Semua NaN secara default
    
    # Helper untuk agregasi dengan threshold
    def yearly_agg(series, func, min_days=min_days_per_year):
        def agg_func(x):
            valid = x.dropna()
            if len(valid) < min_days:
                return np.nan
            return func(valid)
        return series.groupby(df['YEAR']).apply(agg_func)
    
    # === PERHITUNGAN PER PARAMETER (DENGAN PENANGANAN ERROR EKSPLISIT) ===
    
    # --- TMAX-BASED INDICES ---
    if tmax and tmax in df.columns:
        # Statistik dasar
        result['TXm'] = yearly_agg(df[tmax], np.mean)
        result['TXx'] = yearly_agg(df[tmax], np.max)
        result['TXn'] = yearly_agg(df[tmax], np.min)
        
        # Persentil (dengan try-except untuk baseline yang mungkin gagal)
        try:
            p10_tmax, p90_tmax = calculate_percentile_thresholds(df, tmax, ref_start, ref_end)
            Tx10P, Tx90P, Tx10, Tx90 = calculate_percentile_indices(df, tmax, p10_tmax, p90_tmax)
            result['Tx10P'] = Tx10P.round(OUTPUT_DECIMALS_TEMPERATURE)
            result['Tx90P'] = Tx90P.round(OUTPUT_DECIMALS_TEMPERATURE)
            result['Tx10'] = Tx10.round(OUTPUT_DECIMALS_TEMPERATURE)
            result['Tx90'] = Tx90.round(OUTPUT_DECIMALS_TEMPERATURE)
        except Exception as e:
            # Baseline gagal → biarkan persentil sebagai NaN (aman)
            pass
        
        # WSDI (hanya jika baseline valid)
        if 'p90_tmax' in locals():
            try:
                wsdi = df.groupby('YEAR').apply(
                    lambda g: calculate_wsdi_csdi(
                        g, tmax, tmin if (tmin and tmin in g.columns) else tmax, 
                        p90_tmax, 0
                    )[0].iloc[0] if not g.empty else np.nan
                )
                result['WSDI'] = wsdi.astype(float)
            except:
                pass
    
    # --- TMIN-BASED INDICES ---
    if tmin and tmin in df.columns:
        result['TNm'] = yearly_agg(df[tmin], np.mean)
        result['TNx'] = yearly_agg(df[tmin], np.max)
        result['TNn'] = yearly_agg(df[tmin], np.min)
        
        try:
            p10_tmin, _ = calculate_percentile_thresholds(df, tmin, ref_start, ref_end)
            Tn10P, Tn90P, Tn10, Tn90 = calculate_percentile_indices(df, tmin, p10_tmin, p90_tmax if 'p90_tmax' in locals() else 0)
            result['Tn10P'] = Tn10P.round(OUTPUT_DECIMALS_TEMPERATURE)
            result['Tn90P'] = Tn90P.round(OUTPUT_DECIMALS_TEMPERATURE)
            result['Tn10'] = Tn10.round(OUTPUT_DECIMALS_TEMPERATURE)
            result['Tn90'] = Tn90.round(OUTPUT_DECIMALS_TEMPERATURE)
        except:
            pass
        
        # CSDI
        if 'p10_tmin' in locals():
            try:
                csdi = df.groupby('YEAR').apply(
                    lambda g: calculate_wsdi_csdi(
                        g, tmax if (tmax and tmax in g.columns) else tmin, tmin, 
                        0, p10_tmin
                    )[1].iloc[0] if not g.empty else np.nan
                )
                result['CSDI'] = csdi.astype(float)
            except:
                pass
    
    # --- TAVE-BASED INDICES ---
    if tave and tave in df.columns:
        result['TMm'] = yearly_agg(df[tave], np.mean)
        result['TMx'] = yearly_agg(df[tave], np.max)
        result['TMn'] = yearly_agg(df[tave], np.min)
        
        try:
            p10_tave, p90_tave = calculate_percentile_thresholds(df, tave, ref_start, ref_end)
            Tm10P, Tm90P, Tm10, Tm90 = calculate_percentile_indices(df, tave, p10_tave, p90_tave)
            result['Tm10P'] = Tm10P.round(OUTPUT_DECIMALS_TEMPERATURE)
            result['Tm90P'] = Tm90P.round(OUTPUT_DECIMALS_TEMPERATURE)
            result['Tm10'] = Tm10.round(OUTPUT_DECIMALS_TEMPERATURE)
            result['Tm90'] = Tm90.round(OUTPUT_DECIMALS_TEMPERATURE)
        except:
            pass
    
    # --- MULTI-PARAMETER INDICES (DTR, ETR) ---
    if tmax and tmin and tmax in df.columns and tmin in df.columns:
        # Hitung DTR harian hanya untuk hari dengan kedua parameter valid
        valid_mask = df[tmax].notna() & df[tmin].notna()
        df['DTR_daily'] = np.where(valid_mask, df[tmax] - df[tmin], np.nan)
        result['DTR'] = yearly_agg(df['DTR_daily'], np.mean)
        
        # ETR = TXx - TNn (hanya jika keduanya tersedia)
        if 'TXx' in result.columns and 'TNn' in result.columns:
            result['ETR'] = (result['TXx'] - result['TNn']).round(OUTPUT_DECIMALS_TEMPERATURE)
    
    # === GABUNGKAN DENGAN METADATA QC ===
    result = pd.concat([result, avail], axis=1)
    
    # Cleanup: pastikan semua kolom numerik di-round dengan benar
    for col in all_index_cols:
        if col in result.columns and pd.api.types.is_numeric_dtype(result[col]):
            result[col] = result[col].round(OUTPUT_DECIMALS_TEMPERATURE)
    
    result.index.name = 'YEAR'
    return result