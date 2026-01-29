---
name: Data Issue
about: Report issues with climate data processing
title: "[DATA] Short description of data issue"
labels: data
assignees: ''

---

## Describe the data issue

A clear description of the data problem (e.g., unexpected QC flag, incorrect index value).

## Input data characteristics

- **Station/location**: [e.g., Jakarta, WMO ID 96001]
- **Period**: [e.g., 2010-2020]
- **Data source**: [e.g., BMKG observations, reanalysis]
- **Completeness**: [e.g., 95% available days]
- **Known issues**: [e.g., instrument change in 2015]

## Steps to reproduce

```python
import pandas as pd
from climate_extremes.rainfall import idxRain

df = pd.read_csv('your_data.csv')
df['time'] = pd.to_datetime(df['time'])
result = idxRain(df, 'RAINFALL_24H_MM')
print(result[['qc_flag', 'PRECTOT', 'R95P']].head())