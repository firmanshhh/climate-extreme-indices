---
name: Bug Report
about: Create a report to help us improve
title: "[BUG] Short description of the issue"
labels: bug
assignees: ''

---

## Describe the bug

A clear and concise description of what the bug is.

## To Reproduce

Steps to reproduce the behavior:
1. Go to '...'
2. Run '....'
3. See error

```python
# Minimal reproducible example
import pandas as pd
from climate_extremes.rainfall import idxRain

df = pd.DataFrame(...)
result = idxRain(df, 'RAIN')