# Contributing to Climate Extremes Library

Thank you for your interest in contributing to the Climate Extremes Indices Library! This document outlines our contribution guidelines to ensure a smooth collaboration process.

## 🤝 Code of Conduct

All contributors must adhere to our [Code of Conduct](CODE_OF_CONDUCT.md). We are committed to fostering a welcoming and inclusive environment for everyone.

## 📥 How to Contribute

### 1. Reporting Issues

Before submitting a new issue:
- Search existing issues to avoid duplicates
- Check the [FAQ](docs/faq.md) for common questions
- Include:
  - Clear description of the problem
  - Steps to reproduce
  - Expected vs. actual behavior
  - Python version and OS
  - Sample data (if applicable, use synthetic data)

Use appropriate issue templates:
- [Bug report](.github/ISSUE_TEMPLATE/bug_report.md)
- [Feature request](.github/ISSUE_TEMPLATE/feature_request.md)
- [Data issue](.github/ISSUE_TEMPLATE/data_issue.md)

### 2. Suggesting Enhancements

We welcome suggestions for:
- New ETCCDI indices
- Tropical climate adaptations
- Performance improvements
- Documentation enhancements

Please open a feature request issue first to discuss the proposal before implementation.

### 3. Submitting Pull Requests

#### Workflow
1. Fork the repository
2. Create a new branch: `git checkout -b feature/your-feature-name`
3. Implement your changes
4. Add tests for new functionality
5. Run tests locally: `pytest tests/ -v`
6. Format code: `black climate_extremes/ && isort climate_extremes/`
7. Commit changes with descriptive messages
8. Push to your fork and open a PR

#### PR Requirements
- [ ] Tests pass for all Python versions (3.8-3.12)
- [ ] Code formatted with Black and isort
- [ ] Type hints added for new public functions
- [ ] Documentation updated (docstrings + examples if needed)
- [ ] CHANGELOG.md updated with your changes
- [ ] PR title follows conventional commits:
  - `feat:` for new features
  - `fix:` for bug fixes
  - `docs:` for documentation changes
  - `chore:` for maintenance tasks

## 🧪 Testing Guidelines

### Test Structure
- Unit tests in `tests/` directory
- Test files named `test_<module>.py`
- Use pytest fixtures for test data (`conftest.py`)
- Cover edge cases (missing data, extreme values, single-year datasets)

### Test Coverage
- Aim for >95% coverage for core modules
- 100% coverage required for QC logic
- Use `pytest --cov=climate_extremes` to check coverage

## 📚 Documentation Standards

### Docstrings
Follow Google style docstrings:
```python
def idxTemp(df, tave, tmax, tmin, ref_start=1991, ref_end=2020):
    """
    Calculate 22 ETCCDI temperature extreme indices.
    
    Args:
        df (pd.DataFrame): Daily climate data with 'time' column
        tave (str): Column name for daily mean temperature (°C)
        tmax (str): Column name for daily maximum temperature (°C)
        tmin (str): Column name for daily minimum temperature (°C)
        ref_start (int): Baseline start year (default: 1991)
        ref_end (int): Baseline end year (default: 2020)
    
    Returns:
        pd.DataFrame: Annual extreme indices with YEAR index
    
    Raises:
        ValueError: If input validation fails
    
    Notes:
        - Persentil calculated from full baseline period (not monthly means)
        - Missing data handled with NaN propagation
        - WSDI/CSDI require ≥6 consecutive days
    
    Examples:
        >>> df = pd.read_csv('data.csv')
        >>> indices = idxTemp(df, 'TAVE', 'TMAX', 'TMIN')
        >>> print(indices.head())
    """