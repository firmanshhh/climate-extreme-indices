"""
Contoh visualisasi hasil indeks ekstrem menggunakan matplotlib
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from climate_extremes.temperature import idxTemp
from climate_extremes.rainfall import idxRain

# Set style untuk publikasi
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 10
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 12

def generate_sample_data():
    """Generate quick sample data."""
    dates = pd.date_range('2015-01-01', '2020-12-31', freq='D')
    np.random.seed(42)
    
    # Suhu Jakarta-like
    doy = np.array([d.timetuple().tm_yday for d in dates])
    tave = 27.0 + 1.5 * np.sin(2 * np.pi * doy / 365) + np.random.normal(0, 1.0, len(dates))
    tmax = tave + np.random.uniform(6, 9, len(dates))
    tmin = tave - np.random.uniform(5, 8, len(dates))
    
    # Curah hujan dengan pola musim
    month = np.array([d.month for d in dates])
    is_wet = (month >= 11) | (month <= 3)
    rain = np.zeros(len(dates))
    rain[is_wet & (np.random.random(len(dates)) < 0.65)] = np.random.gamma(1.5, 8.0, is_wet.sum())
    rain[~is_wet & (np.random.random(len(dates)) < 0.30)] = np.random.gamma(1.2, 6.0, (~is_wet).sum())
    
    df = pd.DataFrame({
        'time': dates,
        'TEMPERATURE_AVG_C': tave,
        'TEMP_24H_TX_C': tmax,
        'TEMP_24H_TN_C': tmin,
        'RAINFALL_24H_MM': rain
    })
    
    return df

def plot_temperature_indices(temp_idx):
    """Plot indeks suhu tahunan."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # TXx dan TNn
    ax = axes[0, 0]
    ax.plot(temp_idx.index, temp_idx['TXx'], 'ro-', label='TXx (max Tmax)', linewidth=2)
    ax.plot(temp_idx.index, temp_idx['TNn'], 'bo-', label='TNn (min Tmin)', linewidth=2)
    ax.set_title('Ekstrem Suhu Tahunan', fontsize=14, fontweight='bold')
    ax.set_ylabel('Suhu (°C)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # DTR
    ax = axes[0, 1]
    ax.bar(temp_idx.index, temp_idx['DTR'], color='goldenrod', alpha=0.7)
    ax.set_title('Diurnal Temperature Range (DTR)', fontsize=14, fontweight='bold')
    ax.set_ylabel('DTR (°C)')
    ax.axhline(temp_idx['DTR'].mean(), color='red', linestyle='--', label=f'Rata-rata: {temp_idx["DTR"].mean():.1f}°C')
    ax.legend()
    
    # WSDI dan CSDI
    ax = axes[1, 0]
    ax.plot(temp_idx.index, temp_idx['WSDI'], 'r^-', label='WSDI (spell panas)', linewidth=2, markersize=8)
    ax.plot(temp_idx.index, temp_idx['CSDI'], 'b^-', label='CSDI (spell dingin)', linewidth=2, markersize=8)
    ax.set_title('Durasi Spell Ekstrem', fontsize=14, fontweight='bold')
    ax.set_ylabel('Durasi (hari)')
    ax.set_xlabel('Tahun')
    ax.legend()
    
    # Tx90p dan Tn10p
    ax = axes[1, 1]
    ax.plot(temp_idx.index, temp_idx['Tx90P'], 'r*-', label='Tx90p (%)', linewidth=2, markersize=10)
    ax.plot(temp_idx.index, temp_idx['Tn10P'], 'b*-', label='Tn10p (%)', linewidth=2, markersize=10)
    ax.set_title('Persentase Hari Ekstrem', fontsize=14, fontweight='bold')
    ax.set_ylabel('Persentase (%)')
    ax.set_xlabel('Tahun')
    ax.legend()
    
    plt.tight_layout()
    plt.savefig('temperature_extremes.png', dpi=300, bbox_inches='tight')
    print("✓ Visualisasi suhu tersimpan: temperature_extremes.png")
    plt.show()

def plot_rainfall_indices(rain_idx):
    """Plot indeks curah hujan tahunan."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # PRECTOT
    ax = axes[0, 0]
    bars = ax.bar(rain_idx.index, rain_idx['PRECTOT'], color='skyblue', edgecolor='navy', linewidth=1.5)
    ax.set_title('Total Curah Hujan Tahunan', fontsize=14, fontweight='bold')
    ax.set_ylabel('Curah Hujan (mm)')
    ax.axhline(rain_idx['PRECTOT'].mean(), color='red', linestyle='--', 
               label=f'Rata-rata: {rain_idx["PRECTOT"].mean():.0f} mm')
    ax.legend()
    
    # CDD dan CWD
    ax = axes[0, 1]
    ax.plot(rain_idx.index, rain_idx['CDD'], 'ro-', label='CDD (hari kering)', linewidth=2, markersize=8)
    ax.plot(rain_idx.index, rain_idx['CWD'], 'bo-', label='CWD (hari basah)', linewidth=2, markersize=8)
    ax.set_title('Consecutive Dry/Wet Days', fontsize=14, fontweight='bold')
    ax.set_ylabel('Durasi (hari)')
    ax.legend()
    
    # RX1DAY dan R95P
    ax = axes[1, 0]
    ax.plot(rain_idx.index, rain_idx['RX1DAY'], 'g^-', label='RX1DAY (max 1-hari)', linewidth=2, markersize=8)
    ax.plot(rain_idx.index, rain_idx['R95P'], 'm^-', label='R95P (total >95p)', linewidth=2, markersize=8)
    ax.set_title('Curah Hujan Ekstrem', fontsize=14, fontweight='bold')
    ax.set_ylabel('Curah Hujan (mm)')
    ax.set_xlabel('Tahun')
    ax.legend()
    
    # QC Flags
    ax = axes[1, 1]
    qc_flags = rain_idx['qc_flag'].value_counts()
    colors = ['green' if 'OK' in str(flag) else 'orange' if 'FALLBACK' in str(flag) else 'red' 
              for flag in qc_flags.index]
    ax.barh([str(f) for f in qc_flags.index], qc_flags.values, color=colors)
    ax.set_title('Distribusi QC Flags', fontsize=14, fontweight='bold')
    ax.set_xlabel('Jumlah Tahun')
    ax.set_ylabel('QC Flag')
    
    plt.tight_layout()
    plt.savefig('rainfall_extremes.png', dpi=300, bbox_inches='tight')
    print("✓ Visualisasi curah hujan tersimpan: rainfall_extremes.png")
    plt.show()

if __name__ == "__main__":
    print("=" * 70)
    print("VISUALISASI INDEKS EKSTREM IKLIM")
    print("=" * 70)
    
    # Generate data
    print("\n[1/3] Generating sample climate data...")
    df = generate_sample_data()
    
    # Hitung indeks
    print("[2/3] Calculating extreme indices...")
    temp_idx = idxTemp(df, 'TEMPERATURE_AVG_C', 'TEMP_24H_TX_C', 'TEMP_24H_TN_C', 2015, 2018)
    rain_idx = idxRain(df, 'RAINFALL_24H_MM', 2015, 2018, min_wet_days=20)
    
    # Plot
    print("[3/3] Generating visualizations...")
    plot_temperature_indices(temp_idx)
    plot_rainfall_indices(rain_idx)
    
    print("\n" + "=" * 70)
    print("VISUALISASI SELESAI")
    print("File output:")
    print("  - temperature_extremes.png")
    print("  - rainfall_extremes.png")
    print("=" * 70)
    print("\n💡 Tips visualisasi:")
    print("  - Untuk publikasi ilmiah, gunakan dpi=300 dan format PDF/PNG")
    print("  - Tambahkan garis tren dengan scipy.stats.linregress()")
    print("  - Untuk peta spasial, integrasikan dengan geopandas + xarray")