# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-01-29

### Added
- Initial release of ETCCDI-compliant climate extremes indices library
- 22 temperature indices including WSDI/CSDI spell detection
- 22 precipitation indices with robust QC system (baseline fallback)
- Comprehensive test suite (27 tests, 98% coverage)
- Tropical climate adaptations (flexible wet-day thresholds)
- Missing data handling with explicit traceability (qc_flag metadata)
- GitHub Actions CI workflow
- Professional documentation (API reference, methodology, tropical adaptations)
- Example notebooks for Jakarta case study (2019 heatwave, 2020 floods)
- Synthetic data generator for Indonesian climate patterns
- Contributor guidelines and code of conduct

### Fixed
- NaN handling in spell detection (WSDI/CSDI returns NaN for all-missing years)
- Baseline fallback logic for insufficient wet days (<30 days)
- Consistent absolute imports across package modules
- Edge case handling for single-year datasets
- KeyError handling for missing 'YEAR' column in QC system
- CWD calculation accuracy with explicit wet/dry day thresholds

### Changed
- Renamed package from "Developing_Climate_Indices_Libraries_Point" to "climate-extremes"
- Restructured tests to be outside main package for better isolation
- Added explicit QC metadata columns (qc_flag, baseline_period) to rainfall output
- Improved validation error messages with actionable feedback
- Enhanced example visualizations with publication-quality styling

### Removed
- Relative imports beyond top-level package (replaced with absolute imports)
- Hard-coded paths in test fixtures (replaced with parameterized generation)