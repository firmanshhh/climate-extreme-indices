"""
Fixture pytest untuk testing modul indeks ekstrem iklim.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

@pytest.fixture
def sample_daily_temperature():
    """Generate realistic Indonesian temperature time series (2010-2020)."""
    start_date = datetime(2010, 1, 1)
    dates = [start_date + timedelta(days=i) for i in range(365 * 11 + 3)]  # 2010-2020
    
    # Simulasi variasi musiman tropis
    day_of_year = np.array([d.timetuple().tm_yday for d in dates])
    seasonal_cycle = 2.0 * np.sin(2 * np.pi * day_of_year / 365.25)
    
    # Noise harian
    daily_noise = np.random.normal(0, 1.5, len(dates))
    
    # Trend pemanasan global kecil
    years = np.array([d.year for d in dates])
    trend = (years - 2010) * 0.05
    
    # Generate suhu dengan konsistensi fisik
    tmin = 22.0 + seasonal_cycle + daily_noise + trend
    tave = tmin + np.random.uniform(3, 6, len(dates)) + np.random.normal(0, 0.5, len(dates))
    tmax = tave + np.random.uniform(4, 8, len(dates)) + np.random.normal(0, 0.5, len(dates))
    
    # Inject missing data (5%) - TAPI JANGAN DI INDEX 0!
    mask_missing = np.random.random(len(dates)) < 0.05
    mask_missing[0] = False  # ← KRUSIAL: index 0 selalu valid untuk testing
    
    tave[mask_missing] = np.nan
    tmax[mask_missing] = np.nan
    tmin[mask_missing] = np.nan
    
    df = pd.DataFrame({
        'time': dates,
        'TEMPERATURE_AVG_C': tave,
        'TEMP_24H_TX_C': tmax,
        'TEMP_24H_TN_C': tmin
    })
    
    return df


@pytest.fixture
def sample_daily_temperature_negative():
    """Generate temperature data with negative values but physically consistent (pegunungan)."""
    dates = pd.date_range('2020-01-01', '2020-12-31', freq='D')
    
    # Generate TMIN first (bisa negatif di pegunungan)
    tmin = np.random.uniform(-8, 12, len(dates))
    
    # Generate TAVE: harus ≥ TMIN
    tave = tmin + np.random.uniform(2, 8, len(dates))
    
    # Generate TMAX: harus ≥ TAVE
    tmax = tave + np.random.uniform(3, 10, len(dates))
    
    # Inject missing data (5%)
    mask_missing = np.random.random(len(dates)) < 0.05
    tave[mask_missing] = np.nan
    tmax[mask_missing] = np.nan
    tmin[mask_missing] = np.nan
    
    df = pd.DataFrame({
        'time': dates,
        'TEMPERATURE_AVG_C': tave,
        'TEMP_24H_TX_C': tmax,
        'TEMP_24H_TN_C': tmin
    })
    
    return df


@pytest.fixture
def sample_daily_rainfall():
    """Generate realistic Indonesian rainfall time series (2010-2020)."""
    start_date = datetime(2010, 1, 1)
    dates = [start_date + timedelta(days=i) for i in range(365 * 11 + 3)]
    
    # Simulasi pola musim hujan-kemarau tropis
    day_of_year = np.array([d.timetuple().tm_yday for d in dates])
    month = np.array([d.month for d in dates])
    
    # Probabilitas hujan lebih tinggi di musim hujan (Nov-Mar)
    is_wet_season = (month >= 11) | (month <= 3)
    prob_rain = np.where(is_wet_season, 0.65, 0.35)
    
    # Generate curah hujan
    rain = np.zeros(len(dates))
    rain_days = np.random.random(len(dates)) < prob_rain
    
    # Distribusi gamma untuk curah hujan (khas tropis)
    rain[rain_days] = np.random.gamma(shape=1.2, scale=8.0, size=rain_days.sum())
    
    # Tambahkan ekstrem events (1% dari hari hujan)
    extreme_mask = rain_days & (np.random.random(len(dates)) < 0.01)
    rain[extreme_mask] = np.random.uniform(80, 250, extreme_mask.sum())
    
    # Inject missing data (7%)
    mask_missing = np.random.random(len(dates)) < 0.07
    rain[mask_missing] = np.nan
    
    df = pd.DataFrame({
        'time': dates,
        'RAINFALL_24H_MM': rain
    })
    
    return df


@pytest.fixture
def minimal_valid_rainfall():
    """Dataset minimal untuk testing baseline fallback (1991-2020 dengan cukup hari basah)."""
    dates = pd.date_range('1991-01-01', '2020-12-31', freq='D')
    rain = np.random.gamma(1.0, 7.0, len(dates))
    rain[np.random.random(len(dates)) < 0.4] = 0  # 40% hari kering
    
    # Pastikan >30 hari basah (>1mm)
    wet_days = rain > 1.0
    if wet_days.sum() < 30:
        rain[:30] = np.random.uniform(5, 50, 30)  # Force 30 wet days
    
    df = pd.DataFrame({'time': dates, 'RAINFALL_24H_MM': rain})
    return df


@pytest.fixture
def insufficient_wet_days_rainfall():
    """Dataset dengan <30 hari basah untuk testing QC fallback."""
    dates = pd.date_range('1991-01-01', '2020-12-31', freq='D')
    # Hanya 25 hari basah
    rain = np.zeros(len(dates))
    rain_indices = np.random.choice(len(dates), 25, replace=False)
    rain[rain_indices] = np.random.uniform(2, 20, 25)
    
    df = pd.DataFrame({'time': dates, 'RAINFALL_24H_MM': rain})
    return df


@pytest.fixture
def no_rainfall_data():
    """Dataset tanpa data curah hujan sama sekali (semua NaN)."""
    dates = pd.date_range('2010-01-01', '2020-12-31', freq='D')
    df = pd.DataFrame({'time': dates, 'RAINFALL_24H_MM': np.nan})
    # TIDAK PERLU menambahkan kolom 'YEAR' di sini - akan ditambahkan oleh idxRain
    return df