"""
Unit tests untuk modul temperature sesuai standar ETCCDI.
"""

import pytest
import pandas as pd
import numpy as np
from climate_extremes.temperature import idxTemp, calculate_wsdi_csdi
from climate_extremes.constants import DEFAULT_BASELINE_START, DEFAULT_BASELINE_END

class TestTemperatureIndices:
    
    def test_idxtemp_basic_functionality(self, sample_daily_temperature):
        """Test perhitungan dasar idxTemp dengan data valid."""
        df = sample_daily_temperature.copy()
        result = idxTemp(
            df=df,
            tave='TEMPERATURE_AVG_C',
            tmax='TEMP_24H_TX_C',
            tmin='TEMP_24H_TN_C',
            ref_start=2010,
            ref_end=2015
        )
        
        # Validasi struktur output
        assert isinstance(result, pd.DataFrame)
        assert result.index.name == 'YEAR'
        assert len(result) == 11  # 2010-2020
        
        # Validasi kolom wajib ETCCDI
        required_cols = ['TMm', 'TXx', 'TNn', 'DTR', 'WSDI', 'CSDI', 'Tx90P', 'Tn10P']
        for col in required_cols:
            assert col in result.columns, f"Kolom {col} tidak ditemukan"
        
        # Validasi rentang nilai fisik
        assert (result['TMm'] > 20).all() and (result['TMm'] < 32).all()
        assert (result['DTR'] > 0).all() and (result['DTR'] < 15).all()
    
    def test_idxtemp_missing_data_handling(self, sample_daily_temperature):
        """Test penanganan missing data (>30% missing pada satu tahun)."""
        df = sample_daily_temperature.copy()
        
        # Force 50% missing pada tahun 2015 untuk TAVE saja
        mask_2015 = pd.to_datetime(df['time']).dt.year == 2015
        df.loc[mask_2015, 'TEMPERATURE_AVG_C'] = np.nan
        
        result = idxTemp(
            df=df,
            tave='TEMPERATURE_AVG_C',
            tmax='TEMP_24H_TX_C',
            tmin='TEMP_24H_TN_C',
            ref_start=2010,
            ref_end=2015
        )
        
        # Tahun 2015 harus memiliki nilai NaN untuk TMm (karena TAVE missing)
        assert pd.isna(result.loc[2015, 'TMm'])
        # WSDI/CSDI mungkin tidak NaN karena menggunakan TMAX/TMIN yang masih ada
        # Tapi untuk indeks yang bergantung pada TAVE yang missing, harus NaN
    
    def test_idxtemp_spell_detection(self, sample_daily_temperature):
        """Test deteksi WSDI/CSDI dengan spell buatan."""
        # Buat dataset dengan spell panas 10 hari berturut-turut di 2018
        df = sample_daily_temperature.copy()
        mask_july_2018 = (pd.to_datetime(df['time']).dt.year == 2018) & \
                         (pd.to_datetime(df['time']).dt.month == 7) & \
                         (pd.to_datetime(df['time']).dt.day.between(10, 19))
        
        # Hitung threshold 90p dari baseline 2010-2015
        baseline_mask = (pd.to_datetime(df['time']).dt.year.between(2010, 2015))
        p90 = df.loc[baseline_mask, 'TEMP_24H_TX_C'].quantile(0.90)
        
        # Force spell panas (> p90)
        df.loc[mask_july_2018, 'TEMP_24H_TX_C'] = p90 + 3.0
        
        result = idxTemp(
            df=df,
            tave='TEMPERATURE_AVG_C',
            tmax='TEMP_24H_TX_C',
            tmin='TEMP_24H_TN_C',
            ref_start=2010,
            ref_end=2015
        )
        
        # WSDI 2018 harus ≥10 hari (spell 10 hari valid)
        assert result.loc[2018, 'WSDI'] >= 10
    
    def test_idxtemp_negative_values_handling(self, sample_daily_temperature_negative):
        """Test penanganan suhu negatif (kasus pegunungan tinggi) dengan data konsisten."""
        df = sample_daily_temperature_negative.copy()
        
        result = idxTemp(
            df=df,
            tave='TEMPERATURE_AVG_C',
            tmax='TEMP_24H_TX_C',
            tmin='TEMP_24H_TN_C',
            ref_start=2020,
            ref_end=2020
        )
        
        assert len(result) == 1
        assert result.index[0] == 2020
        assert not result.isna().all().all()  # Tidak semua NaN
    
    def test_idxtemp_invalid_input(self, sample_daily_temperature):
        """Test error handling untuk input tidak valid."""
        df = sample_daily_temperature.copy()
        
        # Kolom tidak ada
        with pytest.raises(ValueError, match="Kolom suhu tidak lengkap"):
            idxTemp(df, 'TAVE', 'TMAX', 'TMIN_INVALID')
        
        # Data tidak konsisten (Tmin > Tmax) - akan ditangkap oleh validasi
        df_invalid = df.copy()
        # Force ketidakkonsistenan yang jelas
        df_invalid.loc[0, 'TEMP_24H_TN_C'] = df_invalid.loc[0, 'TEMP_24H_TX_C'] + 10.0
        with pytest.raises(ValueError, match="ketidakkonsistenan"):
            idxTemp(df_invalid, 'TEMPERATURE_AVG_C', 'TEMP_24H_TX_C', 'TEMP_24H_TN_C')