"""
Sistem Quality Control terpusat untuk indeks ekstrem curah hujan.
Mengimplementasikan strategi fallback baseline sesuai dokumen teknis.
"""

import pandas as pd
import numpy as np
from typing import Tuple
from climate_extremes.constants import (
    DEFAULT_BASELINE_START, DEFAULT_BASELINE_END,
    ALTERNATIVE_BASELINE_START, ALTERNATIVE_BASELINE_END,
    MIN_WET_DAYS_BASELINE, WET_DAY_THRESHOLD,
    QC_OK, QC_FALLBACK_1981_2010, QC_FALLBACK_FULL,
    QC_NO_DATA, QC_NO_WET_DAYS, QC_INSUFFICIENT_WET
)

def determine_baseline_period(
    df: pd.DataFrame,
    rain_col: str,
    requested_start: int = DEFAULT_BASELINE_START,
    requested_end: int = DEFAULT_BASELINE_END,
    min_wet_days: int = MIN_WET_DAYS_BASELINE
) -> Tuple[str, str, float, float, str]:
    """
    Menentukan periode baseline yang valid dengan strategi fallback 3-tahap.
    
    Returns
    -------
    Tuple containing:
        - baseline_description: str (deskripsi periode untuk output)
        - qc_flag: str (kode QC)
        - r95p_threshold: float (threshold 95th percentile)
        - r99p_threshold: float (threshold 99th percentile)
        - baseline_period: str (periode dalam format "YYYY-YYYY")
    """
    # Validasi dasar: tidak ada data sama sekali
    if df[rain_col].isna().all() or df[rain_col].dropna().empty:
        return "NONE", QC_NO_DATA, np.nan, np.nan, "NONE"
    
    all_valid = df[rain_col].dropna()
    
    # Validasi: tidak ada hari dengan curah hujan > 0 mm
    if (all_valid <= 0).all():
        return "NONE", QC_NO_WET_DAYS, np.nan, np.nan, "NONE"
    
    # Tahap 1: Baseline utama (1991-2020)
    ref_mask = (df['YEAR'] >= requested_start) & (df['YEAR'] <= requested_end)
    ref_data = df.loc[ref_mask, rain_col].dropna()
    wet_days_ref = ref_data[ref_data > WET_DAY_THRESHOLD]  # > 1.0 mm
    
    if len(wet_days_ref) >= min_wet_days:
        r95p = wet_days_ref.quantile(0.95)
        r99p = wet_days_ref.quantile(0.99)
        return (
            f"{requested_start}-{requested_end}", 
            QC_OK, 
            r95p, 
            r99p,
            f"{requested_start}-{requested_end}"
        )
    
    # Tahap 2: Fallback ke 1981-2010 - HANYA jika memenuhi kriteria MINIMAL
    alt_mask = (df['YEAR'] >= ALTERNATIVE_BASELINE_START) & (df['YEAR'] <= ALTERNATIVE_BASELINE_END)
    alt_data = df.loc[alt_mask, rain_col].dropna()
    alt_wet = alt_data[alt_data > WET_DAY_THRESHOLD]
    
    # KRUSIAL: Pastikan benar-benar memenuhi kriteria sebelum fallback
    if len(alt_wet) >= min_wet_days:
        r95p = alt_wet.quantile(0.95)
        r99p = alt_wet.quantile(0.99)
        return (
            f"{ALTERNATIVE_BASELINE_START}-{ALTERNATIVE_BASELINE_END}",
            QC_FALLBACK_1981_2010,
            r95p,
            r99p,
            f"{ALTERNATIVE_BASELINE_START}-{ALTERNATIVE_BASELINE_END}"
        )
    
    # Tahap 3: Fallback ke seluruh periode data - HANYA jika memenuhi kriteria MINIMAL
    all_wet = all_valid[all_valid > WET_DAY_THRESHOLD]
    if len(all_wet) >= min_wet_days:
        r95p = all_wet.quantile(0.95)
        r99p = all_wet.quantile(0.99)
        min_yr, max_yr = df['YEAR'].min(), df['YEAR'].max()
        return (
            f"FULL_PERIOD_{min_yr}_{max_yr}",
            QC_FALLBACK_FULL,
            r95p,
            r99p,
            f"{min_yr}-{max_yr}"
        )
    
    # Gagal semua tahap
    wet_count = len(wet_days_ref)
    qc_flag = f"{QC_INSUFFICIENT_WET}_{wet_count}_OF_{min_wet_days}_REQUIRED"
    return "NONE", qc_flag, np.nan, np.nan, "NONE"


def create_qc_metadata(
    years: pd.Index,
    baseline_used: str,
    qc_flag: str,
    r95p_threshold: float,
    r99p_threshold: float
) -> pd.DataFrame:
    """Buat DataFrame metadata QC untuk output akhir."""
    qc_df = pd.DataFrame(index=years)
    qc_df['baseline_period'] = baseline_used
    qc_df['qc_flag'] = qc_flag
    qc_df['R95p_threshold_mm'] = r95p_threshold
    qc_df['R99p_threshold_mm'] = r99p_threshold
    return qc_df