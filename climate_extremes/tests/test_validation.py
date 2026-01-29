"""
Unit tests untuk modul validasi data input.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from climate_extremes.validation import (
    validate_timeseries, validate_temperature_data, validate_rainfall_data,
    check_data_completeness
)

class TestValidation:
    
    def test_validate_timeseries_valid(self):
        """Test validasi time series dengan data harian lengkap."""
        dates = pd.date_range('2020-01-01', '2020-12-31', freq='D')
        df = pd.DataFrame({'time': dates, 'value': np.random.rand(len(dates))})
        
        valid, msg = validate_timeseries(df)
        assert valid
        assert msg == "OK"
    
    def test_validate_timeseries_missing_time_col(self):
        """Test validasi gagal jika kolom waktu tidak ada."""
        # Gunakan panjang yang sama untuk semua kolom
        dates = pd.date_range('2020-01-01', '2020-01-03', freq='D')
        df = pd.DataFrame({
            'date': dates,  # Kolom 'date' bukan 'time'
            'value': [1, 2, 3]  # Panjang 3 sesuai dates
        })
        
        valid, msg = validate_timeseries(df, time_col='time')
        assert not valid
        assert 'tidak ditemukan' in msg
    
    def test_validate_timeseries_invalid_dtype(self):
        """Test validasi gagal jika kolom waktu bukan datetime."""
        df = pd.DataFrame({'time': ['2020-01-01', '2020-01-02', '2020-01-03'], 'value': [1, 2, 3]})
        
        valid, msg = validate_timeseries(df)
        assert not valid
        assert 'datetime' in msg.lower()
    
    def test_validate_temperature_data_valid(self):
        """Test validasi data suhu dengan konsistensi Tmin ≤ Tave ≤ Tmax."""
        dates = pd.date_range('2020-01-01', '2020-12-31', freq='D')
        tmin = np.random.uniform(22, 25, len(dates))
        tave = tmin + np.random.uniform(2, 5, len(dates))
        tmax = tave + np.random.uniform(3, 7, len(dates))
        
        df = pd.DataFrame({
            'time': dates,
            'TAVE': tave,
            'TMAX': tmax,
            'TMIN': tmin
        })
        
        valid, msg = validate_temperature_data(df, 'TAVE', 'TMAX', 'TMIN')
        assert valid
        assert msg == "OK"
    
    def test_validate_temperature_data_inconsistent(self):
        """Test validasi gagal jika Tmin > Tave atau Tave > Tmax."""
        dates = pd.date_range('2020-01-01', '2020-01-10', freq='D')
        df = pd.DataFrame({
            'time': dates,
            'TAVE': [27, 27, 27, 27, 27, 27, 27, 27, 27, 27],
            'TMAX': [30, 30, 30, 30, 30, 30, 30, 30, 30, 30],
            'TMIN': [28, 26, 26, 26, 26, 26, 26, 26, 26, 26]  # Hari pertama: Tmin(28) > Tave(27)
        })
        
        valid, msg = validate_temperature_data(df, 'TAVE', 'TMAX', 'TMIN')
        assert not valid
        assert 'ketidakkonsistenan' in msg
    
    def test_validate_rainfall_data_valid(self):
        """Test validasi data curah hujan valid."""
        dates = pd.date_range('2020-01-01', '2020-12-31', freq='D')
        df = pd.DataFrame({
            'time': dates,
            'RAIN': np.random.gamma(1.0, 8.0, len(dates))
        })
        
        valid, msg = validate_rainfall_data(df, 'RAIN')
        assert valid
        assert msg == "OK"
    
    def test_validate_rainfall_data_negative(self):
        """Test validasi gagal jika terdapat nilai negatif."""
        dates = pd.date_range('2020-01-01', '2020-01-10', freq='D')
        df = pd.DataFrame({
            'time': dates,
            'RAIN': [0, 5, 10, -2, 15, 0, 3, 8, 12, 0]  # Ada nilai -2
        })
        
        valid, msg = validate_rainfall_data(df, 'RAIN')
        assert not valid
        assert 'negatif' in msg
    
    def test_validate_rainfall_data_no_wet_days_check_removed(self):
        """Test bahwa validasi TIDAK lagi menolak data tanpa hari basah (>0 mm)."""
        dates = pd.date_range('2020-01-01', '2020-12-31', freq='D')
        df = pd.DataFrame({'time': dates, 'RAIN': 0.0})  # Semua 0 mm
        
        # SEKARANG INI HARUS VALID karena pengecekan hari basah dipindah ke QC system
        valid, msg = validate_rainfall_data(df, 'RAIN')
        assert valid  # <-- BERUBAH DARI SEBELUMNYA
        assert msg == "OK"
    
    def test_check_data_completeness(self):
        """Test perhitungan kelengkapan data per tahun."""
        # Buat data 2020 dengan 300 hari dan 2021 dengan 365 hari
        dates_2020 = pd.date_range('2020-01-01', '2020-12-31', freq='D')
        dates_2021 = pd.date_range('2021-01-01', '2021-12-31', freq='D')
        
        # 2020: 300 hari data valid + 66 missing
        rain_2020 = np.random.gamma(1.0, 8.0, 300)
        rain_2020 = np.concatenate([rain_2020, np.full(66, np.nan)])
        
        # 2021: lengkap 365 hari
        rain_2021 = np.random.gamma(1.0, 8.0, 365)
        
        dates_all = pd.DatetimeIndex(list(dates_2020) + list(dates_2021))
        rain_all = np.concatenate([rain_2020, rain_2021])
        
        df = pd.DataFrame({'time': dates_all, 'RAIN': rain_all})
        
        completeness = check_data_completeness(df, 'RAIN', min_completeness=0.80)
        
        # 2020: 300/366 = 81.97% → lolos
        # 2021: 365/365 = 100% → lolos
        assert 2020 in completeness.index
        assert 2021 in completeness.index
        assert completeness.loc[2020] >= 80.0
        assert completeness.loc[2021] == 100.0