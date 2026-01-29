# Climate Extremes Indices Library 🌡️💧

[![Tests](https://github.com/YOUR_USERNAME/climate-extremes/actions/workflows/tests.yml/badge.svg)](https://github.com/YOUR_USERNAME/climate-extremes/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org)

**ETCCDI-compliant library for calculating climate extreme indices with robust quality control for tropical regions**

This Python library implements the [Expert Team on Climate Change Detection and Indices (ETCCDI)](https://etccdi.org/) standard to calculate **44+ climate extreme indices** from daily temperature and precipitation data, with special adaptations for tropical climates like Indonesia.

Developed and validated by **BMKG Climate Center** for research and operational climate monitoring.

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| **🌡️ 22 Temperature Indices** | WSDI, CSDI, DTR, ETR, Tx90p, Tn10p, and more |
| **💧 22 Precipitation Indices** | R95p, R99p, CDD, CWD, RX1DAY-RX10DAY, SDII |
| **🛡️ Robust QC System** | Automatic baseline fallback (1991-2020 → 1981-2010 → full period) with explicit traceability |
| **🌴 Tropical Adaptations** | Flexible wet-day thresholds and spell detection optimized for Indonesian monsoon patterns |
| **🧩 NaN-Safe Operations** | Explicit handling of missing data with QC metadata (`qc_flag`, `baseline_period`) |
| **🔬 Scientific Validation** | 27+ unit tests covering edge cases (98% coverage) |
| **⚡ Production Ready** | Type hints, comprehensive validation, and modular architecture |

---

## 📊 Sample Output

### Temperature Indices (Jakarta 2020)
| YEAR | TMm | TXx | TNn | DTR | WSDI | CSDI | Tx90p |
|------|-----|-----|-----|-----|------|------|-------|
| 2020 | 27.8 | 35.2 | 19.8 | 8.9 | 12 | 0 | 18.4 |

### Precipitation Indices with QC Metadata
| YEAR | PRECTOT | CDD | RX1DAY | R95P | qc_flag | baseline_period |
|------|---------|-----|--------|------|---------|-----------------|
| 2020 | 1842.5 | 42 | 187.3 | 684.2 | OK | 1991-2020 |

![Jakarta Temperature Extremes](examples/figures/jakarta_temperature.png)
*Figure: Annual temperature extremes for Jakarta (2015-2020). WSDI shows increased warm spell duration in 2019.*

---

## ⚙️ Installation

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/climate-extremes.git
cd climate-extremes

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Install package in development mode
pip install -e .

##🚀 Quick Start
```python
import pandas as pd
from climate_extremes.temperature import idxTemp
from climate_extremes.rainfall import idxRain

# Load daily climate data (must have 'time' column as datetime64)
df = pd.read_csv('daily_climate_data.csv')
df['time'] = pd.to_datetime(df['time'])

# Calculate temperature extremes (1991-2020 baseline)
temp_indices = idxTemp(
    df=df,
    tave='TEMPERATURE_AVG_C',
    tmax='TEMP_24H_TX_C',
    tmin='TEMP_24H_TN_C',
    ref_start=1991,
    ref_end=2020
)

# Calculate precipitation extremes with QC
rain_indices = idxRain(
    df=df,
    ch='RAINFALL_24H_MM',
    ref_start=1991,
    ref_end=2020,
    min_wet_days=30
)

# Check QC flags for data quality assessment
print(rain_indices[['qc_flag', 'baseline_period', 'R95p_threshold_mm']].head())
