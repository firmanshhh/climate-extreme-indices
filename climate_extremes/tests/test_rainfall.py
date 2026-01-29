"""
Unit tests untuk modul rainfall dengan fokus pada sistem QC robust.
"""

import pytest
import pandas as pd
import numpy as np
from climate_extremes.rainfall import idxRain
from climate_extremes.qc import determine_baseline_period
from climate_extremes.constants import (
    QC_OK, QC_FALLBACK_1981_2010, QC_FALLBACK_FULL, QC_NO_DATA, QC_NO_WET_DAYS,
    WET_DAY_THRESHOLD
)

class TestRainfallIndices:
    
    def test_idxrain_basic_functionality(self, sample_daily_rainfall):
        """Test perhitungan dasar idxRain dengan data valid."""
        df = sample_daily_rainfall.copy()
        result = idxRain(
            df=df,
            ch='RAINFALL_24H_MM',
            ref_start=2010,
            ref_end=2015,
            min_wet_days=20  # Lower threshold for test data
        )
        
        # Validasi struktur output
        assert isinstance(result, pd.DataFrame)
        assert result.index.name == 'YEAR'
        assert len(result) == 11  # 2010-2020
        
        # Validasi kolom wajib ETCCDI
        required_cols = ['PRECTOT', 'HH', 'RX1DAY', 'CDD', 'CWD', 'R95P', 'SDII']
        for col in required_cols:
            assert col in result.columns, f"Kolom {col} tidak ditemukan"
        
        # Validasi metadata QC
        assert 'qc_flag' in result.columns
        assert 'baseline_period' in result.columns
        assert 'R95p_threshold_mm' in result.columns
        
        # Validasi nilai fisik
        assert (result['PRECTOT'] >= 0).all()  # Total hujan tidak negatif
        assert (result['HH'] >= 0).all()       # Hari basah tidak negatif
        assert (result['CDD'] >= 0).all()      # CDD tidak negatif
    
    def test_idxrain_qc_baseline_fallback(self, insufficient_wet_days_rainfall):
        """Test strategi fallback baseline ketika baseline utama tidak valid."""
        df = insufficient_wet_days_rainfall.copy()
        
        # Baseline 1991-2020 hanya memiliki 25 hari basah (<30 required)
        result = idxRain(
            df=df,
            ch='RAINFALL_24H_MM',
            ref_start=1991,
            ref_end=2020,
            min_wet_days=30
        )
        
        # Harus menggunakan fallback (full period atau alternatif)
        qc_flag = result['qc_flag'].iloc[0]
        assert qc_flag != QC_OK, f"QC flag seharusnya bukan OK, tapi {qc_flag}"
        assert 'FALLBACK' in qc_flag or 'INSUFFICIENT' in qc_flag
    
    def test_idxrain_no_rainfall_data(self, no_rainfall_data):
        """Test penanganan dataset tanpa data curah hujan sama sekali."""
        df = no_rainfall_data.copy()
        result = idxRain(df, 'RAINFALL_24H_MM')
        
        # Semua nilai harus NaN kecuali metadata QC
        assert result['PRECTOT'].isna().all()
        assert result['RX1DAY'].isna().all()
        assert (result['qc_flag'] == QC_NO_DATA).all()
    
    def test_idxrain_cdd_cwd_calculation(self):
        """Test perhitungan CDD/CWD dengan pola spell buatan yang eksplisit."""
        # Buat dataset dengan CDD=15 hari dan CWD=8 hari yang pasti
        dates = pd.date_range('2020-01-01', '2020-01-31', freq='D')
        
        # 15 hari kering (0 mm) → CDD=15
        # 8 hari basah (>1.0 mm pasti) → CWD=8
        # 8 hari kering (0 mm) → memutus spell basah
        rain = np.concatenate([
            np.zeros(15),                              # 15 hari kering pasti (<1.0 mm)
            np.full(8, 5.0),                           # 8 hari basah pasti (>1.0 mm)
            np.zeros(8)                                # 8 hari kering pasti (<1.0 mm)
        ])
        
        df = pd.DataFrame({'time': dates, 'RAINFALL_24H_MM': rain})
        
        # Gunakan min_days_per_year=1 secara implisit melalui parameter idxRain
        result = idxRain(df, 'RAINFALL_24H_MM', ref_start=2020, ref_end=2020, min_wet_days=5)
        
        # Validasi CDD dan CWD dengan toleransi eksplisit
        assert result.loc[2020, 'CDD'] == 15  # Max consecutive dry days
        assert result.loc[2020, 'CWD'] == 8   # Max consecutive wet days (pasti 8, bukan 10)
    
    def test_idxrain_r95p_r99p_calculation(self, minimal_valid_rainfall):
        """Test perhitungan R95p/R99p dengan verifikasi manual."""
        df = minimal_valid_rainfall.copy()
        
        # Hitung threshold manual untuk verifikasi
        wet_days = df['RAINFALL_24H_MM'][df['RAINFALL_24H_MM'] > 1.0]
        p95_manual = wet_days.quantile(0.95)
        p99_manual = wet_days.quantile(0.99)
        
        result = idxRain(
            df=df,
            ch='RAINFALL_24H_MM',
            ref_start=1991,
            ref_end=2020,
            min_wet_days=20
        )
        
        # Validasi threshold yang digunakan
        threshold_used = result['R95p_threshold_mm'].iloc[0]
        assert abs(threshold_used - p95_manual) < 0.1  # Toleransi pembulatan
        
        # Validasi R95P > 0 (karena ada hari ekstrem)
        assert result['R95P'].sum() > 0
    
    def test_idxrain_negative_values(self):
        """Test penanganan nilai curah hujan negatif (error instrument)."""
        dates = pd.date_range('2020-01-01', '2020-12-31', freq='D')
        rain = np.random.gamma(1.0, 8.0, len(dates))
        rain[0] = -5.0  # Inject nilai negatif
        
        df = pd.DataFrame({'time': dates, 'RAINFALL_24H_MM': rain})
        
        with pytest.raises(ValueError, match="nilai curah hujan negatif"):
            idxRain(df, 'RAINFALL_24H_MM')
    
    def test_idxrain_edge_case_single_year(self):
        """Test dengan hanya satu tahun data."""
        dates = pd.date_range('2020-01-01', '2020-12-31', freq='D')
        rain = np.random.gamma(1.2, 7.0, len(dates))
        rain[np.random.random(len(dates)) < 0.4] = 0
        
        df = pd.DataFrame({'time': dates, 'RAINFALL_24H_MM': rain})
        
        result = idxRain(df, 'RAINFALL_24H_MM', ref_start=2020, ref_end=2020)
        
        assert len(result) == 1
        assert result.index[0] == 2020
        assert not result['PRECTOT'].isna().all()