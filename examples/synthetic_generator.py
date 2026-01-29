#!/usr/bin/env python
"""
Synthetic climate data generator for Indonesia
Generates realistic daily temperature and rainfall data with tropical characteristics
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import argparse
import os

def generate_indonesian_climate(
    station_name="JAKARTA",
    lat=-6.2,
    lon=106.8,
    elevation=8,
    start_year=2010,
    end_year=2020,
    seed=42,
    add_missing=True
):
    """
    Generate synthetic daily climate data for Indonesian location.
    
    Parameters
    ----------
    station_name : str
        Station name (e.g., "JAKARTA", "SEMARANG")
    lat, lon : float
        Geographic coordinates
    elevation : float
        Elevation above sea level (meters)
    start_year, end_year : int
        Data period
    seed : int
        Random seed for reproducibility
    add_missing : bool
        Add realistic missing data (5% for temperature, 7% for rainfall)
    
    Returns
    -------
    pd.DataFrame with columns:
        time, station_name, latitude, longitude, elevation,
        TEMPERATURE_AVG_C, TEMP_24H_TX_C, TEMP_24H_TN_C, RAINFALL_24H_MM
    """
    np.random.seed(seed)
    
    # Generate date range
    start_date = datetime(start_year, 1, 1)
    end_date = datetime(end_year, 12, 31)
    dates = []
    current = start_date
    while current <= end_date:
        dates.append(current)
        current += timedelta(days=1)
    
    n_days = len(dates)
    
    # Generate day-of-year array for seasonal cycle
    doy = np.array([d.timetuple().tm_yday for d in dates])
    month = np.array([d.month for d in dates])
    
    # Temperature baseline (tropical: 25-28°C average)
    # Base temperature depends on elevation (~0.6°C per 100m)
    base_tave = 27.0 - (elevation / 100) * 0.6
    
    # Weak seasonal cycle (amplitude 1.5°C for tropics)
    seasonal_cycle = 1.5 * np.sin(2 * np.pi * (doy - 30) / 365.25)  # Peak in Feb
    
    # Small warming trend (0.04°C/year)
    years = np.array([d.year for d in dates])
    trend = (years - start_year) * 0.04
    
    # Daily noise
    daily_noise = np.random.normal(0, 0.8, n_days)
    
    # Generate TAVE
    tave = base_tave + seasonal_cycle + trend + daily_noise
    
    # Generate TMAX and TMIN with realistic diurnal range
    diurnal_range = np.random.uniform(7.0, 10.0, n_days)
    tmax = tave + diurnal_range / 2 + np.random.normal(0, 0.5, n_days)
    tmin = tave - diurnal_range / 2 + np.random.normal(0, 0.5, n_days)
    
    # Ensure physical consistency: Tmin ≤ Tave ≤ Tmax
    mask_fix = tmin > tave
    tmin[mask_fix] = tave[mask_fix] - 0.5
    mask_fix = tave > tmax
    tave[mask_fix] = tmax[mask_fix] - 0.5
    
    # Rainfall generation
    # Wet season: Nov-Apr for most of Indonesia (SH)
    if lat < 0:
        wet_months = [11, 12, 1, 2, 3, 4]
    else:
        wet_months = [5, 6, 7, 8, 9, 10]
    
    is_wet_season = np.isin(month, wet_months)
    
    # Probability of wet day
    wet_prob = np.where(is_wet_season, 0.65, 0.30)
    
    # Generate rainfall amounts
    rain = np.zeros(n_days)
    wet_day_mask = np.random.random(n_days) < wet_prob
    
    # Gamma distribution for wet day amounts (shape varies by season)
    shape = np.where(is_wet_season, 1.4, 1.2)
    scale = np.where(is_wet_season, 8.0, 6.0)
    
    rain[wet_day_mask] = np.random.gamma(
        shape=shape[wet_day_mask],
        scale=scale[wet_day_mask],
        size=wet_day_mask.sum()
    )
    
    # Add extreme events (2% of wet days)
    extreme_mask = wet_day_mask & (np.random.random(n_days) < 0.02)
    rain[extreme_mask] = np.random.uniform(100, 250, extreme_mask.sum())
    
    # Add missing data (realistic for observational data)
    if add_missing:
        # 5% missing for temperature
        missing_tave = np.random.random(n_days) < 0.05
        tave[missing_tave] = np.nan
        tmax[missing_tave] = np.nan
        tmin[missing_tave] = np.nan
        
        # 7% missing for rainfall
        missing_rain = np.random.random(n_days) < 0.07
        rain[missing_rain] = np.nan
    
    # Create DataFrame
    df = pd.DataFrame({
        'time': dates,
        'station_name': station_name,
        'wmo_id': f"synth_{station_name.lower()}",
        'latitude': lat,
        'longitude': lon,
        'elevation': elevation,
        'TEMPERATURE_AVG_C': tave,
        'TEMP_24H_TX_C': tmax,
        'TEMP_24H_TN_C': tmin,
        'RAINFALL_24H_MM': rain
    })
    
    return df

def main():
    parser = argparse.ArgumentParser(
        description='Generate synthetic Indonesian climate data',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('--station', default='JAKARTA', help='Station name')
    parser.add_argument('--lat', type=float, default=-6.2, help='Latitude (decimal degrees)')
    parser.add_argument('--lon', type=float, default=106.8, help='Longitude (decimal degrees)')
    parser.add_argument('--elev', type=float, default=8, help='Elevation (meters)')
    parser.add_argument('--start', type=int, default=2010, help='Start year')
    parser.add_argument('--end', type=int, default=2020, help='End year')
    parser.add_argument('--output', default='synthetic_climate_data.csv', help='Output CSV filename')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    parser.add_argument('--no-missing', action='store_true', help='Disable missing data injection')
    
    args = parser.parse_args()
    
    print(f"Generating synthetic climate data for {args.station}...")
    print(f"  Location: {args.lat}°, {args.lon}°, {args.elev}m")
    print(f"  Period: {args.start} - {args.end}")
    print(f"  Random seed: {args.seed}")
    print(f"  Missing data: {'disabled' if args.no_missing else 'enabled (5-7%)'}")
    
    df = generate_indonesian_climate(
        station_name=args.station,
        lat=args.lat,
        lon=args.lon,
        elevation=args.elev,
        start_year=args.start,
        end_year=args.end,
        seed=args.seed,
        add_missing=not args.no_missing
    )
    
    # Save to CSV
    os.makedirs(os.path.dirname(args.output) if os.path.dirname(args.output) else '.', exist_ok=True)
    df.to_csv(args.output, index=False)
    
    # Print summary statistics
    print(f"\n✓ Data saved to: {args.output}")
    print(f"  Total days: {len(df):,}")
    print(f"\nTemperature statistics:")
    print(f"  TAVE: {df['TEMPERATURE_AVG_C'].min():.1f}°C to {df['TEMPERATURE_AVG_C'].max():.1f}°C (mean: {df['TEMPERATURE_AVG_C'].mean():.1f}°C)")
    print(f"  Missing TAVE: {df['TEMPERATURE_AVG_C'].isna().sum()} days ({df['TEMPERATURE_AVG_C'].isna().sum()/len(df)*100:.1f}%)")
    print(f"\nRainfall statistics:")
    print(f"  Total: {df['RAINFALL_24H_MM'].sum():,.0f} mm")
    print(f"  Max daily: {df['RAINFALL_24H_MM'].max():.1f} mm")
    print(f"  Wet days (>1mm): {(df['RAINFALL_24H_MM'] > 1).sum()} days ({(df['RAINFALL_24H_MM'] > 1).sum()/len(df)*100:.1f}%)")
    print(f"  Missing RAIN: {df['RAINFALL_24H_MM'].isna().sum()} days ({df['RAINFALL_24H_MM'].isna().sum()/len(df)*100:.1f}%)")

if __name__ == "__main__":
    main()