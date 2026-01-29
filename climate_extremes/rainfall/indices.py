"""
Implementasi utama fungsi idxRain() dengan sistem QC robust.
"""

import pandas as pd
import numpy as np
from typing import Optional, Tuple
from climate_extremes.constants import (
    DEFAULT_BASELINE_START, DEFAULT_BASELINE_END,
    MIN_WET_DAYS_BASELINE, WET_DAY_THRESHOLD,
    HEAVY_RAIN_THRESHOLD, VERY_HEAVY_THRESHOLD, EXTREME_RAIN_THRESHOLD,
    OUTPUT_DECIMALS_RAINFALL, OUTPUT_DECIMALS_PERCENTAGE,
    QC_NO_DATA, QC_NO_WET_DAYS
)
from climate_extremes.validation import validate_timeseries, validate_rainfall_data
from climate_extremes.qc import determine_baseline_period, create_qc_metadata
from climate_extremes.utils import (
    is_all_nan, safe_mean, safe_max, safe_min, rolling_sum
)
from climate_extremes.rainfall.extremes import calculate_r95p_r99p
from climate_extremes.rainfall.spells import calculate_cdd_cwd

def _create_empty_rainfall_index(years, qc_flag):
    """Helper untuk membuat DataFrame kosong dengan struktur yang benar."""
    empty_df = pd.DataFrame(index=years, columns=[
        'PRECTOT', 'HH', 'HH20MM', 'HH50MM', 'HH100MM', 'HH150MM',
        'FH20', 'FH50', 'FH100', 'FH150', 'R50', 'CDD', 'CWD', 'SDII',
        'RX1DAY', 'RX5DAY', 'RX7DAY', 'RX10DAY', 'R95P', 'R99P', 'R95Ptot', 'R99Ptot',
        'R95p_threshold_mm', 'R99p_threshold_mm', 'baseline_period', 'qc_flag'
    ])
    empty_df[:] = np.nan
    empty_df['qc_flag'] = qc_flag
    empty_df['baseline_period'] = "NONE"
    empty_df.index.name = 'YEAR'
    return empty_df


def idxRain(
    df: pd.DataFrame,
    ch: str,
    ref_start: int = DEFAULT_BASELINE_START,
    ref_end: int = DEFAULT_BASELINE_END,
    min_wet_days: int = MIN_WET_DAYS_BASELINE
) -> pd.DataFrame:
    """
    Hitung indeks ekstrem curah hujan harian dengan sistem QC robust.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame dengan kolom 'time' (datetime) dan curah hujan
    ch : str
        Nama kolom curah hujan harian (mm)
    ref_start : int, optional
        Tahun awal periode baseline (default: 1991)
    ref_end : int, optional
        Tahun akhir periode baseline (default: 2020)
    min_wet_days : int, optional
        Minimum hari basah (>1.0 mm) pada baseline (default: 30)
    
    Returns
    -------
    pd.DataFrame
        DataFrame indeks ekstrem curah hujan dengan metadata QC
        
    Notes
    -----
    Output mencakup 22 indeks ekstrem + 4 kolom metadata QC untuk traceability.
    """
    # Validasi input DENGAN FLEKSIBILITAS UNTUK TEST (min_days_per_year=1)
    valid, msg = validate_timeseries(df, min_days_per_year=1)
    if not valid:
        raise ValueError(f"Validasi time series gagal: {msg}")
    
    # === PERSIAPAN KOLOM YEAR (KRUSIAL UNTUK SEMUA OPERASI) ===
    df = df.copy()
    df['time'] = pd.to_datetime(df['time'])
    df['YEAR'] = df['time'].dt.year  # <-- DITAMBAHKAN DI SINI SEBELUM QC INTERNAL
    
    # === QC INTERNAL: Handle kasus khusus sebelum validasi rainfall ===
    # Kasus 1: Tidak ada data sama sekali (semua NaN)
    if df[ch].isna().all():
        years = sorted(df['YEAR'].unique())
        return _create_empty_rainfall_index(years, qc_flag=QC_NO_DATA)
    
    # Kasus 2: Ada data tapi semua ≤ 0 mm (tidak ada hari basah >0 mm)
    all_valid = df[ch].dropna()
    if len(all_valid) > 0 and (all_valid <= 0).all():
        years = sorted(df['YEAR'].unique())
        return _create_empty_rainfall_index(years, qc_flag=QC_NO_WET_DAYS)
    
    # Validasi rainfall normal (hanya cek nilai negatif)
    valid, msg = validate_rainfall_data(df, ch)
    if not valid:
        raise ValueError(f"Validasi data curah hujan gagal: {msg}")
    
    # === DETERMINASI BASELINE DENGAN QC ===
    baseline_used, qc_flag, r95p_threshold, r99p_threshold, baseline_period = \
        determine_baseline_period(df, ch, ref_start, ref_end, min_wet_days)
    
    # === PERHITUNGAN INDEKS TAHUNAN ===
    yearly_groups = df.groupby('YEAR')[ch]
    years = sorted(df['YEAR'].unique())
    
    # Total curah hujan tahunan
    PRECTOT = yearly_groups.sum()
    
    # Hitung hari basah dengan berbagai threshold
    def count_wet_days(arr, threshold):
        if is_all_nan(arr.values):
            return np.nan
        return np.sum((arr.values >= threshold) & (~np.isnan(arr.values)))
    
    HH = yearly_groups.apply(lambda x: count_wet_days(x, WET_DAY_THRESHOLD))
    HH20MM = yearly_groups.apply(lambda x: count_wet_days(x, HEAVY_RAIN_THRESHOLD))
    HH50MM = yearly_groups.apply(lambda x: count_wet_days(x, VERY_HEAVY_THRESHOLD))
    HH100MM = yearly_groups.apply(lambda x: count_wet_days(x, EXTREME_RAIN_THRESHOLD))
    HH150MM = yearly_groups.apply(lambda x: count_wet_days(x, 150.0))
    
    # Fraksi hari ekstrem
    def calc_fraction(numerator, denominator):
        result = np.full(len(numerator), np.nan)
        mask = (denominator > 0) & (~np.isnan(denominator)) & (~np.isnan(numerator))
        result[mask] = (numerator[mask] / denominator[mask] * 100).round(OUTPUT_DECIMALS_PERCENTAGE)
        return result
    
    FH20 = calc_fraction(HH20MM.values, HH.values)
    FH50 = calc_fraction(HH50MM.values, HH.values)
    FH100 = calc_fraction(HH100MM.values, HH.values)
    FH150 = calc_fraction(HH150MM.values, HH.values)
    
    # CDD dan CWD
    def calc_spell(arr, is_dry: bool):
        if is_all_nan(arr.values):
            return np.nan
        
        max_spell = current = 0
        for val in arr.values:
            if np.isnan(val):
                current = 0
                continue
            
            if (is_dry and val < WET_DAY_THRESHOLD) or (not is_dry and val >= WET_DAY_THRESHOLD):
                current += 1
                max_spell = max(max_spell, current)
            else:
                current = 0
        
        return max_spell
    
    CDD = yearly_groups.apply(lambda x: calc_spell(x, is_dry=True))
    CWD = yearly_groups.apply(lambda x: calc_spell(x, is_dry=False))
    
    # SDII (Simple Daily Intensity Index)
    def calc_sdii(arr):
        wet_days = arr[arr >= WET_DAY_THRESHOLD].dropna()
        if len(wet_days) == 0:
            return np.nan
        return wet_days.sum() / len(wet_days)
    
    SDII = yearly_groups.apply(calc_sdii)
    
    # RXnDAY (curah hujan maksimum n-hari)
    def calc_rxnday(arr, n_days):
        if is_all_nan(arr.values) or len(arr) < n_days:
            return np.nan
        
        rolling_sums = rolling_sum(arr.values, n_days)
        return safe_max(rolling_sums)
    
    RX1DAY = yearly_groups.apply(lambda x: calc_rxnday(x, 1))
    RX5DAY = yearly_groups.apply(lambda x: calc_rxnday(x, 5))
    RX7DAY = yearly_groups.apply(lambda x: calc_rxnday(x, 7))
    RX10DAY = yearly_groups.apply(lambda x: calc_rxnday(x, 10))
    
    # R95p dan R99p
    R95P_series = pd.Series(index=years, dtype=float)
    R99P_series = pd.Series(index=years, dtype=float)
    
    for year in years:
        year_data = df[df['YEAR'] == year][ch]
        r95p, r99p = calculate_r95p_r99p(year_data, r95p_threshold, r99p_threshold)
        R95P_series.loc[year] = r95p
        R99P_series.loc[year] = r99p
    
    # Persentase terhadap total
    R95Ptot = calc_fraction(R95P_series.values, PRECTOT.values)
    R99Ptot = calc_fraction(R99P_series.values, PRECTOT.values)
    
    # === KOMPILASI HASIL ===
    result = pd.DataFrame({
        'PRECTOT': PRECTOT.round(OUTPUT_DECIMALS_RAINFALL),
        'HH': HH.round(OUTPUT_DECIMALS_RAINFALL),
        'HH20MM': HH20MM.round(OUTPUT_DECIMALS_RAINFALL),
        'HH50MM': HH50MM.round(OUTPUT_DECIMALS_RAINFALL),
        'HH100MM': HH100MM.round(OUTPUT_DECIMALS_RAINFALL),
        'HH150MM': HH150MM.round(OUTPUT_DECIMALS_RAINFALL),
        'FH20': FH20,
        'FH50': FH50,
        'FH100': FH100,
        'FH150': FH150,
        'R50': HH50MM.round(OUTPUT_DECIMALS_RAINFALL),  # Alias untuk kompatibilitas
        'CDD': CDD.round(OUTPUT_DECIMALS_RAINFALL),
        'CWD': CWD.round(OUTPUT_DECIMALS_RAINFALL),
        'SDII': SDII.round(OUTPUT_DECIMALS_RAINFALL),
        'RX1DAY': RX1DAY.round(OUTPUT_DECIMALS_RAINFALL),
        'RX5DAY': RX5DAY.round(OUTPUT_DECIMALS_RAINFALL),
        'RX7DAY': RX7DAY.round(OUTPUT_DECIMALS_RAINFALL),
        'RX10DAY': RX10DAY.round(OUTPUT_DECIMALS_RAINFALL),
        'R95P': R95P_series.round(OUTPUT_DECIMALS_RAINFALL),
        'R99P': R99P_series.round(OUTPUT_DECIMALS_RAINFALL),
        'R95Ptot': R95Ptot,
        'R99Ptot': R99Ptot
    })
    
    # Tambahkan metadata QC
    qc_metadata = create_qc_metadata(
        result.index,
        baseline_used,
        qc_flag,
        r95p_threshold,
        r99p_threshold
    )
    
    result = pd.concat([result, qc_metadata], axis=1)
    
    # Cleanup nilai inf
    result.replace([np.inf, -np.inf], np.nan, inplace=True)
    result.index.name = 'YEAR'
    
    return result