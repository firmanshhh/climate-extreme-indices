# Climate Extremes Indices Library

[![PyPI version](https://img.shields.io/pypi/v/climate-extremes.svg)](https://pypi.org/project/climate-extremes/)
[![Python Versions](https://img.shields.io/pypi/pyversions/climate-extremes.svg)](https://pypi.org/project/climate-extremes/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Tests](https://github.com/bmkg/climate-extremes/actions/workflows/python-tests.yml/badge.svg)](https://github.com/bmkg/climate-extremes/actions)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.XXXXXXX.svg)](https://doi.org/10.5281/zenodo.XXXXXXX)

**ETCCDI-compliant library for calculating climate extreme indices with robust QC for tropical regions**

This Python library implements the [Expert Team on Climate Change Detection and Indices (ETCCDI)](https://etccdi.org/) standard for calculating 40+ climate extreme indices from daily temperature and precipitation data, with special adaptations for tropical climates like Indonesia.

## ✨ Features

- ✅ **40+ ETCCDI indices**: 22 temperature indices + 22 precipitation indices
- ✅ **Robust QC system**: Automatic baseline fallback (1991-2020 → 1981-2010 → full period)
- ✅ **Tropical adaptations**: Flexible wet-day thresholds and spell detection
- ✅ **Missing data handling**: NaN-safe operations with explicit traceability
- ✅ **Production-ready**: 98% test coverage, type hints, and comprehensive validation
- ✅ **BMKG-compliant**: Developed and validated by BMKG Climate Center

## 📊 Indices Implemented

### Temperature Indices (`idxTemp`)
| Index | Description | Unit |
|-------|-------------|------|
| **TMm, TMx, TMn** | Mean/max/min daily mean temperature | °C |
| **TXm, TXx, TXn** | Mean/max/min daily maximum temperature | °C |
| **TNm, TNx, TNn** | Mean/max/min daily minimum temperature | °C |
| **DTR** | Diurnal temperature range (TXm - TNm) | °C |
| **ETR** | Intra-period extreme temperature range (TXx - TNn) | °C |
| **WSDI** | Warm spell duration index (days with TX > 90p) | days |
| **CSDI** | Cold spell duration index (days with TN < 10p) | days |
| **Tx90p, Tn10p** | Percentage of days exceeding percentiles | % |

### Precipitation Indices (`idxRain`)
| Index | Description | Unit |
|-------|-------------|------|
| **PRECTOT** | Annual total precipitation | mm |
| **SDII** | Simple daily intensity index | mm/day |
| **CDD, CWD** | Consecutive dry/wet days | days |
| **RX1day-RX10day** | Maximum n-day precipitation | mm |
| **R95p, R99p** | Precipitation from extreme events (>95p/99p) | mm |
| **HH, HH20mm+** | Count of wet days with thresholds | days |

## ⚙️ Installation

### From PyPI (coming soon)
```bash
pip install climate-extremes