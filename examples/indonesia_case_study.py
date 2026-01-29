"""
Studi kasus: Analisis ekstrem iklim di Jakarta (2015-2020)
Menggunakan data sintetis yang mensimulasikan karakteristik iklim tropis
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from climate_extremes.temperature import idxTemp
from climate_extremes.rainfall import idxRain

def simulate_jakarta_climate():
    """
    Simulasi data harian Jakarta dengan karakteristik:
    - Suhu: 25-33°C, variasi musiman kecil
    - Curah hujan: musim hujan Nov-Mar, kemarau Apr-Oct
    - Ekstrem: gelombang panas 2019, banjir Jan 2020
    """
    dates = []
    tmax = []
    tmin = []
    rain = []
    
    start = datetime(2015, 1, 1)
    end = datetime(2020, 12, 31)
    current = start
    
    while current <= end:
        doy = current.timetuple().tm_yday
        month = current.month
        year = current.year
        
        # Suhu maksimum baseline Jakarta
        base_tmax = 32.0 + 1.0 * np.sin(2 * np.pi * doy / 365)
        
        # Gelombang panas 2019 (Juni-Agustus): +2°C
        if year == 2019 and month in [6, 7, 8]:
            base_tmax += 2.0
        
        # Variasi harian
        day_tmax = base_tmax + np.random.normal(0, 1.2)
        day_tmin = day_tmax - np.random.uniform(6, 9)
        
        # Curah hujan baseline
        is_wet_season = month in [11, 12, 1, 2, 3]
        wet_prob = 0.70 if is_wet_season else 0.25
        
        # Banjir besar Januari 2020: 3 hari berturut-turut >150mm
        if year == 2020 and month == 1 and 15 <= current.day <= 17:
            day_rain = np.random.uniform(150, 200)
        elif np.random.random() < wet_prob:
            day_rain = np.random.gamma(1.3, 7.0)
            # Ekstrem events
            if np.random.random() < 0.03:
                day_rain = np.random.uniform(80, 150)
        else:
            day_rain = 0.0
        
        dates.append(current)
        tmax.append(day_tmax)
        tmin.append(day_tmin)
        rain.append(day_rain)
        
        current += timedelta(days=1)
    
    df = pd.DataFrame({
        'time': dates,
        'TEMP_24H_TX_C': tmax,
        'TEMP_24H_TN_C': tmin,
        'RAINFALL_24H_MM': rain
    })
    
    # Hitung TAVE sebagai rata-rata (TMAX + TMIN)/2
    df['TEMPERATURE_AVG_C'] = (df['TEMP_24H_TX_C'] + df['TEMP_24H_TN_C']) / 2
    
    return df

if __name__ == "__main__":
    print("=" * 70)
    print("STUDI KASUS: ANALISIS EKSTREM IKLIM JAKARTA (2015-2020)")
    print("=" * 70)
    
    # Generate data simulasi Jakarta
    print("\n[1/4] Generating simulated Jakarta climate data (2015-2020)...")
    df = simulate_jakarta_climate()
    print(f"✓ Data generated: {len(df)} days")
    print(f"  - Period: {df['time'].min().date()} to {df['time'].max().date()}")
    print(f"  - Max temperature: {df['TEMP_24H_TX_C'].max():.1f}°C (gelombang panas 2019)")
    print(f"  - Max rainfall: {df['RAINFALL_24H_MM'].max():.1f}mm (banjir Jan 2020)")
    
    # Hitung indeks suhu dengan baseline 2015-2018
    print("\n[2/4] Calculating temperature indices (baseline 2015-2018)...")
    temp_idx = idxTemp(
        df=df,
        tave='TEMPERATURE_AVG_C',
        tmax='TEMP_24H_TX_C',
        tmin='TEMP_24H_TN_C',
        ref_start=2015,
        ref_end=2018
    )
    
    # Analisis gelombang panas 2019
    print("\n[3/4] Analisis gelombang panas 2019:")
    print(f"  - WSDI 2019: {temp_idx.loc[2019, 'WSDI']:.0f} hari")
    print(f"  - TXx 2019: {temp_idx.loc[2019, 'TXx']:.1f}°C")
    print(f"  - Tx90p 2019: {temp_idx.loc[2019, 'Tx90P']:.1f}% hari di atas 90th percentile")
    
    if temp_idx.loc[2019, 'WSDI'] > temp_idx.loc[2018, 'WSDI']:
        print("  ✓ Terdeteksi peningkatan durasi spell panas pada 2019")
    
    # Hitung indeks curah hujan
    print("\n[4/4] Calculating rainfall indices (baseline 2015-2018)...")
    rain_idx = idxRain(
        df=df,
        ch='RAINFALL_24H_MM',
        ref_start=2015,
        ref_end=2018,
        min_wet_days=20
    )
    
    # Analisis banjir Jan 2020
    print("\nAnalisis ekstrem curah hujan 2020:")
    print(f"  - RX1DAY 2020: {rain_idx.loc[2020, 'RX1DAY']:.1f}mm")
    print(f"  - R95P 2020: {rain_idx.loc[2020, 'R95P']:.1f}mm ({rain_idx.loc[2020, 'R95Ptot']:.1f}% dari total)")
    print(f"  - CWD 2020: {rain_idx.loc[2020, 'CWD']:.0f} hari basah berturut-turut")
    
    if rain_idx.loc[2020, 'RX1DAY'] > 150:
        print("  ✓ Terdeteksi curah hujan ekstrem (>150mm) pada 2020")
    
    # Simpan hasil untuk analisis lebih lanjut
    temp_idx.to_csv('jakarta_temperature_indices.csv')
    rain_idx.to_csv('jakarta_rainfall_indices.csv')
    
    print("\n" + "=" * 70)
    print("HASIL TERSIMPAN:")
    print("  - jakarta_temperature_indices.csv")
    print("  - jakarta_rainfall_indices.csv")
    print("=" * 70)
    print("\n💡 Insight untuk Jakarta:")
    print("  - Gelombang panas 2019 terdeteksi melalui peningkatan WSDI dan TXx")
    print("  - Banjir Jan 2020 terkait dengan RX1DAY ekstrem dan R95P yang tinggi")
    print("  - Analisis tren jangka panjang memerlukan data observasi aktual BMKG")