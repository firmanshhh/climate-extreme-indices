"""
Package untuk perhitungan indeks ekstrem iklim berbasis standar ETCCDI.
Dirancang khusus untuk konteks iklim tropis Indonesia dengan sistem QC robust.
"""

# Import utama untuk public API
from climate_extremes.temperature.indices import idxTemp  # ← ABSOLUTE IMPORT
from climate_extremes.rainfall.indices import idxRain      # ← ABSOLUTE IMPORT

# Konstanta yang sering digunakan
from climate_extremes.constants import (
    DEFAULT_BASELINE_START,
    DEFAULT_BASELINE_END,
    MIN_WET_DAYS_BASELINE,
    WET_DAY_THRESHOLD
)

__version__ = "1.0.0"
__author__ = "Pusat Klimatologi - BMKG"

__all__ = [
    'idxTemp',
    'idxRain',
    'DEFAULT_BASELINE_START',
    'DEFAULT_BASELINE_END',
    'MIN_WET_DAYS_BASELINE',
    'WET_DAY_THRESHOLD'
]

# Logging configuration untuk traceability
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
logger.info(f"Climate Extremes Package v{__version__} initialized")