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

### Fixed
- NaN handling in spell detection (WSDI/CSDI)
- Baseline fallback logic for insufficient wet days
- Consistent absolute imports across package modules
- Edge case handling for single-year datasets

### Changed
- Renamed package from "Developing_Climate_Indices_Libraries_Point" to "climate-extremes"
- Restructured tests to be outside main package for better isolation