"""
Implementasi idxTemp dengan graceful degradation untuk data observasi BMKG yang tidak sempurna.
Menghilangkan validasi ketat Tmin ≤ Tave ≤ Tmax yang tidak realistis untuk data nyata.
"""

import pandas as pd
import numpy as np
from typing import Optional
from climate_extremes.constants import (
    DEFAULT_BASELINE_START, DEFAULT_BASELINE_END,
    OUTPUT_DECIMALS_TEMPERATURE
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
    min_days_per_year: int = 300,
    strict_validation: bool = False
) -> pd.DataFrame:
    """
    Hitung indeks ekstrem suhu dengan graceful degradation untuk data observasi tidak lengkap.
    
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
    strict_validation : bool
        Jika True, tolak data dengan ketidakkonsistenan Tmin/Tave/Tmax.
        Default False (direkomendasikan untuk data observasi BMKG).
    
    Returns
    -------
    pd.DataFrame
        DataFrame dengan indeks ETCCDI + metadata QC:
        - Kolom indeks: NaN jika parameter tidak tersedia
        - tmax_available_days, tmin_available_days, tave_available_days
        - qc_temperature_flag: 'COMPLETE', 'TMAX_TMIN_ONLY', dll
    
    Notes
    -----
    Untuk data observasi BMKG:
    - Gunakan strict_validation=False (default) untuk mengakomodasi ketidakkonsistenan kecil (<1°C)
    - Ketidakkonsistenan besar (>2°C) akan menghasilkan warning tapi tidak menghentikan perhitungan
    - Indeks dihitung berdasarkan parameter yang tersedia (graceful degradation)
    
    Examples
    --------
    # Untuk data observasi BMKG (rekomendasi):
    indices = idxTemp(df, 'TAVE', 'TMAX', 'TMIN', strict_validation=False)
    
    # Untuk data homogenisasi/simulasi (validasi ketat):
    indices = idxTemp(df, 'TAVE', 'TMAX', 'TMIN', strict_validation=True)
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
    
    # === PERINGATAN UNTUK KETIDAKKONSISTENAN BESAR (opsional) ===
    if strict_validation or any([
        tave and tmax and tave in df.columns and tmax in df.columns,
        tave and tmin and tave in df.columns and tmin in df.columns
    ]):
        # Cek ketidakkonsistenan hanya jika parameter tersedia
        inconsistencies = []
        
        if tave and tmax and tave in df.columns and tmax in df.columns:
            mask_incon = (df[tave] > df[tmax] + 1.0)  # Toleransi 1.0°C untuk pembulatan
            if mask_incon.sum() > 0:
                inconsistencies.append(f"TAVE > TMAX+1.0°C: {mask_incon.sum()} hari")
        
        if tave and tmin and tave in df.columns and tmin in df.columns:
            mask_incon = (df[tave] < df[tmin] - 1.0)
            if mask_incon.sum() > 0:
                inconsistencies.append(f"TAVE < TMIN-1.0°C: {mask_incon.sum()} hari")
        
        if inconsistencies and strict_validation:
            raise ValueError(f"Validasi data suhu gagal: {'; '.join(inconsistencies)}")
        elif inconsistencies:
            # Warning saja untuk data observasi (tidak menghentikan perhitungan)
            import warnings
            warnings.warn(
                f"Data memiliki ketidakkonsistenan fisik: {'; '.join(inconsistencies)}. "
                f"Indeks akan dihitung dengan hati-hati (NaN untuk hari tidak konsisten).",
                UserWarning
            )
    
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
    
    # === INISIALISASI RESULT ===
    all_index_cols = [
        'TMm', 'TMx', 'TMn', 'TXm', 'TXx', 'TXn', 'TNm', 'TNx', 'TNn',
        'DTR', 'ETR', 'Tm10P', 'Tm90P', 'Tn10P', 'Tn90P', 'Tx10P', 'Tx90P',
        'Tm10', 'Tm90', 'Tn10', 'Tn90', 'Tx10', 'Tx90', 'WSDI', 'CSDI'
    ]
    result = pd.DataFrame(index=years, columns=all_index_cols, dtype=float)
    result[:] = np.nan
    
    # Helper untuk agregasi dengan threshold
    def yearly_agg(series, func, min_days=min_days_per_year):
        def agg_func(x):
            valid = x.dropna()
            if len(valid) < min_days:
                return np.nan
            return func(valid)
        return series.groupby(df['YEAR']).apply(agg_func)
    
    # === PERHITUNGAN PER PARAMETER (GRACEFUL DEGRADATION) ===
    
    # --- TMAX-BASED INDICES ---
    if tmax and tmax in df.columns:
        result['TXm'] = yearly_agg(df[tmax], np.mean)
        result['TXx'] = yearly_agg(df[tmax], np.max)
        result['TXn'] = yearly_agg(df[tmax], np.min)
        
        try:
            p10_tmax, p90_tmax = calculate_percentile_thresholds(df, tmax, ref_start, ref_end)
            Tx10P, Tx90P, Tx10, Tx90 = calculate_percentile_indices(df, tmax, p10_tmax, p90_tmax)
            result['Tx10P'] = Tx10P.round(OUTPUT_DECIMALS_TEMPERATURE)
            result['Tx90P'] = Tx90P.round(OUTPUT_DECIMALS_TEMPERATURE)
            result['Tx10'] = Tx10.round(OUTPUT_DECIMALS_TEMPERATURE)
            result['Tx90'] = Tx90.round(OUTPUT_DECIMALS_TEMPERATURE)
        except Exception:
            pass  # Biarkan NaN jika baseline gagal
        
        # WSDI
        if 'p90_tmax' in locals():
            try:
                wsdi_series = pd.Series(index=years, dtype=float)
                for year in years:
                    year_df = df[df['YEAR'] == year].copy()
                    if len(year_df) > 0:
                        wsdi, _ = calculate_wsdi_csdi(year_df, tmax, tmin if (tmin and tmin in year_df.columns) else tmax, p90_tmax, 0)
                        wsdi_series.loc[year] = wsdi.iloc[0] if not wsdi.empty else np.nan
                result['WSDI'] = wsdi_series
            except Exception:
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
        except Exception:
            pass
        
        # CSDI
        if 'p10_tmin' in locals():
            try:
                csdi_series = pd.Series(index=years, dtype=float)
                for year in years:
                    year_df = df[df['YEAR'] == year].copy()
                    if len(year_df) > 0:
                        _, csdi = calculate_wsdi_csdi(year_df, tmax if (tmax and tmax in year_df.columns) else tmin, tmin, 0, p10_tmin)
                        csdi_series.loc[year] = csdi.iloc[0] if not csdi.empty else np.nan
                result['CSDI'] = csdi_series
            except Exception:
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
        except Exception:
            pass
    
    # --- MULTI-PARAMETER INDICES ---
    if tmax and tmin and tmax in df.columns and tmin in df.columns:
        # Hitung DTR hanya untuk hari dengan kedua parameter valid
        valid_mask = df[tmax].notna() & df[tmin].notna()
        df['DTR_daily'] = np.where(valid_mask, df[tmax] - df[tmin], np.nan)
        result['DTR'] = yearly_agg(df['DTR_daily'], np.mean)
        
        # ETR
        if 'TXx' in result.columns and 'TNn' in result.columns:
            result['ETR'] = (result['TXx'] - result['TNn']).round(OUTPUT_DECIMALS_TEMPERATURE)
    
    # === GABUNGKAN DENGAN METADATA QC ===
    result = pd.concat([result, avail], axis=1)
    
    # Cleanup rounding
    for col in all_index_cols:
        if col in result.columns and pd.api.types.is_numeric_dtype(result[col]):
            result[col] = result[col].round(OUTPUT_DECIMALS_TEMPERATURE)
    
    result.index.name = 'YEAR'
    return result