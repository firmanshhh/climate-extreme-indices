"""
Unit tests untuk sistem Quality Control (QC) pada modul rainfall.
"""

import pytest
import pandas as pd
import numpy as np
from climate_extremes.qc import determine_baseline_period
from climate_extremes.constants import (
    QC_OK, QC_FALLBACK_1981_2010, QC_FALLBACK_FULL, QC_NO_DATA,
    QC_NO_WET_DAYS, QC_INSUFFICIENT_WET, DEFAULT_BASELINE_START, DEFAULT_BASELINE_END,
    ALTERNATIVE_BASELINE_START, ALTERNATIVE_BASELINE_END, MIN_WET_DAYS_BASELINE,
    WET_DAY_THRESHOLD
)

class TestQualityControl:
    
    def test_qc_valid_baseline(self):
        """Test QC dengan baseline utama valid (>30 hari basah)."""
        # Generate data 1991-2020 dengan 100+ hari basah
        dates = pd.date_range('1991-01-01', '2020-12-31', freq='D')
        rain = np.random.gamma(1.0, 8.0, len(dates))
        rain[np.random.random(len(dates)) < 0.6] = 0  # 60% hari kering → 40% basah (~4380 hari basah)
        
        df = pd.DataFrame({'time': dates, 'RAINFALL_24H_MM': rain})
        df['YEAR'] = pd.to_datetime(df['time']).dt.year
        
        baseline_used, qc_flag, r95p, r99p, period = determine_baseline_period(
            df, 'RAINFALL_24H_MM', DEFAULT_BASELINE_START, DEFAULT_BASELINE_END, 30
        )
        
        assert qc_flag == QC_OK
        assert baseline_used == f"{DEFAULT_BASELINE_START}-{DEFAULT_BASELINE_END}"
        assert not np.isnan(r95p)
        assert not np.isnan(r99p)
    
    def test_qc_fallback_to_alternative(self):
        """Test fallback ke baseline alternatif (1981-2010) ketika utama tidak valid."""
        # Data 1991-2020 hanya memiliki 25 hari basah (<30 required)
        dates_main = pd.date_range('1991-01-01', '2020-12-31', freq='D')
        rain_main = np.zeros(len(dates_main))
        rain_main[:25] = np.random.uniform(5, 20, 25)  # Hanya 25 hari basah
        
        # Tambahkan data 1981-1990 dengan 50+ hari basah untuk alternatif
        dates_alt = pd.date_range('1981-01-01', '1990-12-31', freq='D')
        rain_alt = np.random.gamma(1.0, 7.0, len(dates_alt))
        rain_alt[np.random.random(len(dates_alt)) < 0.5] = 0
        
        # Gabungkan
        dates_all = pd.DatetimeIndex(list(dates_alt) + list(dates_main))
        rain_all = np.concatenate([rain_alt, rain_main])
        
        df = pd.DataFrame({'time': dates_all, 'RAINFALL_24H_MM': rain_all})
        df['YEAR'] = pd.to_datetime(df['time']).dt.year
        
        baseline_used, qc_flag, r95p, r99p, period = determine_baseline_period(
            df, 'RAINFALL_24H_MM', 1991, 2020, 30
        )
        
        assert qc_flag == QC_FALLBACK_1981_2010
        assert '1981-2010' in baseline_used
        assert not np.isnan(r95p)
    
    def test_qc_fallback_to_full_period(self):
        """
        Test fallback ke seluruh periode data ketika KEDUA baseline gagal.
        
        Strategi data:
        - 1981-1990: 28 hari basah (<30) → baseline alternatif TIDAK VALID
        - 1991-2010: 0 hari basah (semua kering) → bagian dari baseline utama TIDAK VALID
        - 2011-2020: 25 hari basah (<30) → bagian dari baseline utama TIDAK VALID
        - Total full period (1981-2020): 53 hari basah (>30) → VALID untuk fallback
        """
        # Data 1981-1990: 28 hari basah (<30)
        dates_1981_1990 = pd.date_range('1981-01-01', '1990-12-31', freq='D')
        rain_1981_1990 = np.zeros(len(dates_1981_1990))
        rain_1981_1990[:28] = np.random.uniform(2, 15, 28)  # Hanya 28 hari basah
        
        # Data 1991-2010: 0 hari basah (semua kering) - KRUSIAL UNTUK MEMASTIKAN 1981-2010 <30
        dates_1991_2010 = pd.date_range('1991-01-01', '2010-12-31', freq='D')
        rain_1991_2010 = np.zeros(len(dates_1991_2010))  # SEMUA 0 mm → 0 hari basah
        
        # Data 2011-2020: 25 hari basah (<30)
        dates_2011_2020 = pd.date_range('2011-01-01', '2020-12-31', freq='D')
        rain_2011_2020 = np.zeros(len(dates_2011_2020))
        rain_2011_2020[:25] = np.random.uniform(2, 15, 25)  # Hanya 25 hari basah
        
        # Gabungkan semua periode
        dates_all = pd.DatetimeIndex(
            list(dates_1981_1990) + list(dates_1991_2010) + list(dates_2011_2020)
        )
        rain_all = np.concatenate([rain_1981_1990, rain_1991_2010, rain_2011_2020])
        
        df = pd.DataFrame({'time': dates_all, 'RAINFALL_24H_MM': rain_all})
        df['YEAR'] = pd.to_datetime(df['time']).dt.year
        
        # Verifikasi jumlah hari basah per periode (debugging)
        wet_1981_2010 = df[(df['YEAR'] >= 1981) & (df['YEAR'] <= 2010)]['RAINFALL_24H_MM']
        wet_1981_2010_count = (wet_1981_2010 > WET_DAY_THRESHOLD).sum()
        
        wet_1991_2020 = df[(df['YEAR'] >= 1991) & (df['YEAR'] <= 2020)]['RAINFALL_24H_MM']
        wet_1991_2020_count = (wet_1991_2020 > WET_DAY_THRESHOLD).sum()
        
        wet_full = df['RAINFALL_24H_MM']
        wet_full_count = (wet_full > WET_DAY_THRESHOLD).sum()
        
        # Pastikan kondisi test terpenuhi
        assert wet_1981_2010_count == 28, f"1981-2010 harus 28 hari basah, tapi dapat {wet_1981_2010_count}"
        assert wet_1991_2020_count == 25, f"1991-2020 harus 25 hari basah, tapi dapat {wet_1991_2020_count}"
        assert wet_full_count == 53, f"Full period harus 53 hari basah, tapi dapat {wet_full_count}"
        
        # Jalankan QC determination
        baseline_used, qc_flag, r95p, r99p, period = determine_baseline_period(
            df, 'RAINFALL_24H_MM', 1991, 2020, 30
        )
        
        # HARUS FALLBACK KE FULL PERIOD karena:
        # - 1991-2020: 25 hari basah (<30) → TIDAK VALID
        # - 1981-2010: 28 hari basah (<30) → TIDAK VALID  
        # - Full period: 53 hari basah (>30) → VALID
        assert qc_flag == QC_FALLBACK_FULL, \
            f"Expected QC_FALLBACK_FULL but got '{qc_flag}'. " \
            f"1981-2010 wet days: {wet_1981_2010_count}, " \
            f"1991-2020 wet days: {wet_1991_2020_count}, " \
            f"Full period wet days: {wet_full_count}"
        assert 'FULL_PERIOD' in baseline_used
        assert not np.isnan(r95p)
    
    def test_qc_insufficient_wet_days(self):
        """Test QC ketika tidak ada cukup hari basah di semua periode."""
        # Hanya 25 hari basah di seluruh dataset (1981-2020)
        dates = pd.date_range('1981-01-01', '2020-12-31', freq='D')
        rain = np.zeros(len(dates))
        rain[:25] = np.random.uniform(2, 10, 25)  # Hanya 25 hari basah
        
        df = pd.DataFrame({'time': dates, 'RAINFALL_24H_MM': rain})
        df['YEAR'] = pd.to_datetime(df['time']).dt.year
        
        baseline_used, qc_flag, r95p, r99p, period = determine_baseline_period(
            df, 'RAINFALL_24H_MM', 1991, 2020, 30
        )
        
        assert QC_INSUFFICIENT_WET in qc_flag
        assert np.isnan(r95p)
        assert np.isnan(r99p)
    
    def test_qc_no_rainfall_data(self):
        """Test QC untuk dataset tanpa data curah hujan."""
        dates = pd.date_range('2010-01-01', '2020-12-31', freq='D')
        df = pd.DataFrame({'time': dates, 'RAINFALL_24H_MM': np.nan})
        df['YEAR'] = pd.to_datetime(df['time']).dt.year
        
        baseline_used, qc_flag, r95p, r99p, period = determine_baseline_period(
            df, 'RAINFALL_24H_MM', 1991, 2020, 30
        )
        
        assert qc_flag == QC_NO_DATA
        assert np.isnan(r95p)
        assert np.isnan(r99p)
    
    def test_qc_no_wet_days(self):
        """Test QC untuk dataset tanpa hari basah (>0 mm)."""
        dates = pd.date_range('2010-01-01', '2020-12-31', freq='D')
        df = pd.DataFrame({'time': dates, 'RAINFALL_24H_MM': 0.0})  # Semua 0 mm
        df['YEAR'] = pd.to_datetime(df['time']).dt.year
        
        baseline_used, qc_flag, r95p, r99p, period = determine_baseline_period(
            df, 'RAINFALL_24H_MM', 1991, 2020, 30
        )
        
        assert qc_flag == QC_NO_WET_DAYS
        assert np.isnan(r95p)
        assert np.isnan(r99p)