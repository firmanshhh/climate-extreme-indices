"""
Generator data sintetis untuk testing dan demo
Menghasilkan file CSV yang bisa langsung digunakan dengan library
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import argparse

def generate_station_data(
    station_name="JAKARTA",
    lat=-6.2,
    lon=106.8,
    start_year=2010,
    end_year=2020,
    seed=42
):
    """
    Generate synthetic daily climate data untuk satu stasiun.
    
    Parameters
    ----------
    station_name : str
        Nama stasiun
    lat, lon : float
        Koordinat geografis
    start_year, end_year : int
        Periode data
    seed : int
        Random seed untuk reproducibility
    
    Returns
    -------
    pd.DataFrame dengan kolom:
        time, station_name, latitude, longitude, 
        TEMPERATURE_AVG_C, TEMP_24H_TX_C, TEMP_24H_TN_C, RAINFALL_24H_MM
    """
    np.random.seed(seed)
    
    dates = []
    tave = []
    tmax = []
    tmin = []
    rain = []
    
    current = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    
    while current <= end:
        doy = current.timetuple().tm_yday
        
        # Suhu rata-rata berdasarkan latitude (tropis: ~27°C)
        base_tave = 27.0 + 0.5 * lat  # Koreksi kecil berdasarkan latitude
        
        # Variasi musiman lemah (amplitudo 1-2°C untuk tropis)
        seasonal = 1.5 * np.sin(2 * np.pi * doy / 365)
        
        # Trend pemanasan global kecil (0.03°C/tahun)
        trend = (current.year - start_year) * 0.03
        
        # Noise harian
        noise = np.random.normal(0, 1.0)
        
        day_tave = base_tave + seasonal + trend + noise
        day_tmin = day_tave - np.random.uniform(5.5, 8.5)
        day_tmax = day_tave + np.random.uniform(6.0, 9.0)
        
        # Curah hujan: pola musim berdasarkan hemisphere
        month = current.month
        if lat < 0:  # Belahan selatan (Indonesia)
            is_wet_season = month in [11, 12, 1, 2, 3, 4]
        else:  # Belahan utara
            is_wet_season = month in [5, 6, 7, 8, 9, 10]
        
        wet_prob = 0.65 if is_wet_season else 0.30
        
        if np.random.random() < wet_prob:
            # Distribusi gamma untuk curah hujan tropis
            day_rain = np.random.gamma(1.4, 7.5)
            # Ekstrem events (2% dari hari hujan)
            if np.random.random() < 0.02:
                day_rain = np.random.uniform(100, 300)
        else:
            day_rain = 0.0
        
        # Inject missing data (5%)
        if np.random.random() < 0.05:
            day_tave = np.nan
        if np.random.random() < 0.05:
            day_rain = np.nan
        
        dates.append(current)
        tave.append(day_tave)
        tmax.append(day_tmax)
        tmin.append(day_tmin)
        rain.append(day_rain)
        
        current += timedelta(days=1)
    
    df = pd.DataFrame({
        'time': dates,
        'station_name': station_name,
        'latitude': lat,
        'longitude': lon,
        'TEMPERATURE_AVG_C': tave,
        'TEMP_24H_TX_C': tmax,
        'TEMP_24H_TN_C': tmin,
        'RAINFALL_24H_MM': rain
    })
    
    return df

def main():
    parser = argparse.ArgumentParser(description='Generate synthetic climate data')
    parser.add_argument('--station', default='JAKARTA', help='Station name')
    parser.add_argument('--lat', type=float, default=-6.2, help='Latitude')
    parser.add_argument('--lon', type=float, default=106.8, help='Longitude')
    parser.add_argument('--start', type=int, default=2010, help='Start year')
    parser.add_argument('--end', type=int, default=2020, help='End year')
    parser.add_argument('--output', default='synthetic_climate_data.csv', help='Output CSV file')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    
    args = parser.parse_args()
    
    print(f"Generating synthetic climate data for {args.station}...")
    print(f"  Period: {args.start} - {args.end}")
    print(f"  Location: {args.lat}°, {args.lon}°")
    print(f"  Output: {args.output}")
    
    df = generate_station_data(
        station_name=args.station,
        lat=args.lat,
        lon=args.lon,
        start_year=args.start,
        end_year=args.end,
        seed=args.seed
    )
    
    df.to_csv(args.output, index=False)
    print(f"\n✓ Data saved to {args.output}")
    print(f"  Total days: {len(df)}")
    print(f"  Temperature range: {df['TEMPERATURE_AVG_C'].min():.1f}°C - {df['TEMPERATURE_AVG_C'].max():.1f}°C")
    print(f"  Rainfall range: {df['RAINFALL_24H_MM'].min():.1f}mm - {df['RAINFALL_24H_MM'].max():.1f}mm")
    print(f"  Missing TAVE: {df['TEMPERATURE_AVG_C'].isna().sum()} days ({df['TEMPERATURE_AVG_C'].isna().sum()/len(df)*100:.1f}%)")
    print(f"  Missing RAIN: {df['RAINFALL_24H_MM'].isna().sum()} days ({df['RAINFALL_24H_MM'].isna().sum()/len(df)*100:.1f}%)")

if __name__ == "__main__":
    main()