"""Z-score based anomaly detection — distinct from IQR-based `outliers`.

Outliers (profiler.py) flag individual extreme values per column.
Anomalies here flag rows whose combination of numeric business metrics is
statistically unusual (|z-score| > threshold on any numeric column),
which is closer to "this specific transaction looks wrong" than
"this column has a wide spread".
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .types import numeric_columns, detect_all_dtypes

Z_THRESHOLD = 3.0


def detect_anomalies(df: pd.DataFrame, dtypes: dict | None = None, z_threshold: float = Z_THRESHOLD) -> dict:
    dtypes = dtypes or detect_all_dtypes(df)
    numeric_cols = numeric_columns(df, dtypes)
    if not numeric_cols:
        return {"anomaly_count": 0, "by_column": {}, "row_indices": []}

    anomaly_rows = set()
    by_column = {}
    for col in numeric_cols:
        series = pd.to_numeric(df[col], errors="coerce")
        std = series.std()
        if not std or np.isnan(std) or std == 0:
            continue
        mean = series.mean()
        z = (series - mean).abs() / std
        mask = z > z_threshold
        count = int(mask.sum())
        if count > 0:
            by_column[col] = count
            anomaly_rows.update(df.index[mask].tolist())

    return {
        "anomaly_count": len(anomaly_rows),
        "by_column": by_column,
        "row_indices": sorted(anomaly_rows)[:50],
        "z_threshold": z_threshold,
    }
