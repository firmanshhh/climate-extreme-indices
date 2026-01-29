"""
Konstanta global untuk perhitungan indeks ekstrem iklim.
Mengikuti standar ETCCDI dengan penyesuaian untuk wilayah tropis Indonesia.
"""

from typing import Final

# Periode baseline default (sesuai rekomendasi WMO 2023)
DEFAULT_BASELINE_START: Final[int] = 1991
DEFAULT_BASELINE_END: Final[int] = 2020
ALTERNATIVE_BASELINE_START: Final[int] = 1981
ALTERNATIVE_BASELINE_END: Final[int] = 2010

# Threshold curah hujan (mm)
WET_DAY_THRESHOLD: Final[float] = 1.0      # Hari basah (ETCCDI standard)
HEAVY_RAIN_THRESHOLD: Final[float] = 20.0  # Curah hujan lebat
VERY_HEAVY_THRESHOLD: Final[float] = 50.0  # Curah hujan sangat lebat
EXTREME_RAIN_THRESHOLD: Final[float] = 100.0  # Curah hujan ekstrem

# Kriteria spell
MIN_SPELL_DAYS: Final[int] = 6             # Minimal hari berturut-turut untuk spell
MIN_WET_DAYS_BASELINE: Final[int] = 30     # Minimum hari basah untuk baseline valid

# Persentil untuk indeks ekstrem
PERCENTILE_10: Final[float] = 0.10
PERCENTILE_90: Final[float] = 0.90
PERCENTILE_95: Final[float] = 0.95
PERCENTILE_99: Final[float] = 0.99

# QC Flags
QC_OK: Final[str] = "BASELINE_1991_2020"
QC_FALLBACK_1981_2010: Final[str] = "BASELINE_FALLBACK_1981_2010"
QC_FALLBACK_FULL: Final[str] = "BASELINE_FALLBACK_FULL_PERIOD"
QC_NO_DATA: Final[str] = "NO_RAINFALL_DATA"
QC_NO_WET_DAYS: Final[str] = "NO_WET_DAYS_IN_ENTIRE_RECORD"
QC_INSUFFICIENT_WET: Final[str] = "INSUFFICIENT_WET_DAYS"

# Format output
OUTPUT_DECIMALS_TEMPERATURE: Final[int] = 3
OUTPUT_DECIMALS_RAINFALL: Final[int] = 1
OUTPUT_DECIMALS_PERCENTAGE: Final[int] = 2