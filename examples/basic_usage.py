#!/usr/bin/env python
"""
Basic usage example for Climate Extremes Library
Demonstrates core functionality with synthetic Indonesian climate data
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
sys.path.insert(0, '..')  # Add parent directory to path for development

from climate_extremes.temperature import idxTemp
from climate_extremes.rainfall import idxRain
from examples.synthetic_generator import generate_indonesian_climate

def main():
    print("=" * 80)
    print("CLIMATE EXTREMES LIBRARY - BASIC USAGE EXAMPLE")
    print("=" * 80)
    
    # Step 1: Generate synthetic data for Jakarta
    print("\n[1/4] Generating synthetic Jakarta climate data (2015-2020)...")
    df = generate_indonesian_climate(
        station_name="JAKARTA",
        lat=-6.2,
        lon=106.8,
        elevation=8,
        start_year=2015,
        end_year=2020,
        seed=42
    )
    print(f"✓ Generated {len(df):,} days of data")
    print(f"  Period: {df['time'].min().date()} to {df['time'].max().date()}")
    print(f"  Temperature range: {df['TEMPERATURE_AVG_C'].min():.1f}°C to {df['TEMPERATURE_AVG_C'].max():.1f}°C")
    print(f"  Rainfall range: {df['RAINFALL_24H_MM'].min():.1f}mm to {df['RAINFALL_24H_MM'].max():.1f}mm")
    
    # Step 2: Calculate temperature indices
    print("\n[2/4] Calculating temperature extreme indices (baseline 2015-2018)...")
    try:
        temp_indices = idxTemp(
            df=df,
            tave='TEMPERATURE_AVG_C',
            tmax='TEMP_24H_TX_C',
            tmin='TEMP_24H_TN_C',
            ref_start=2015,
            ref_end=2018
        )
        print(f"✓ Successfully calculated temperature indices for {len(temp_indices)} years")
        
        # Display sample results
        print("\nSample temperature indices (2020):")
        sample_cols = ['TMm', 'TXx', 'TNn', 'DTR', 'WSDI', 'CSDI', 'Tx90P', 'Tn10P']
        print(temp_indices.loc[2020][sample_cols].round(2).to_string())
        
    except Exception as e:
        print(f"✗ Error calculating temperature indices: {e}")
        return 1
    
    # Step 3: Calculate rainfall indices
    print("\n[3/4] Calculating rainfall extreme indices (baseline 2015-2018)...")
    try:
        rain_indices = idxRain(
            df=df,
            ch='RAINFALL_24H_MM',
            ref_start=2015,
            ref_end=2018,
            min_wet_days=20
        )
        print(f"✓ Successfully calculated rainfall indices for {len(rain_indices)} years")
        
        # Display sample results
        print("\nSample rainfall indices (2020):")
        sample_cols = ['PRECTOT', 'HH', 'CDD', 'CWD', 'RX1DAY', 'R95P', 'SDII']
        print(rain_indices.loc[2020][sample_cols].round(1).to_string())
        
    except Exception as e:
        print(f"✗ Error calculating rainfall indices: {e}")
        return 1
    
    # Step 4: QC metadata analysis
    print("\n[4/4] QC Metadata Analysis:")
    print("Year | QC Flag                          | Baseline Period | R95p Threshold")
    print("-" * 80)
    for year in rain_indices.index:
        qc = rain_indices.loc[year, 'qc_flag']
        bp = rain_indices.loc[year, 'baseline_period']
        r95 = rain_indices.loc[year, 'R95p_threshold_mm']
        print(f"{year} | {qc:<36} | {bp:<15} | {r95:>6.1f} mm")
    
    # Save results
    temp_indices.to_csv('jakarta_temperature_indices.csv')
    rain_indices.to_csv('jakarta_rainfall_indices.csv')
    print("\n✓ Results saved to:")
    print("  - jakarta_temperature_indices.csv")
    print("  - jakarta_rainfall_indices.csv")
    
    print("\n" + "=" * 80)
    print("SUCCESS! Climate extremes library working correctly.")
    print("=" * 80)
    print("\n💡 Next steps:")
    print("  1. Try the Jakarta case study: python examples/jakarta_2015_2020.py")
    print("  2. Generate your own data: python examples/synthetic_generator.py --help")
    print("  3. Run tests: pytest tests/ -v")
    print("  4. Explore API documentation: docs/api_reference.md")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())