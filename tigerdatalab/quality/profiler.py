"""Data-quality profiling: missing values, duplicates, outliers, invalid
values, and an overall 0-100 quality score."""
from __future__ import annotations

import pandas as pd

from .types import detect_all_dtypes, numeric_columns, safe_quantile


def missing_report(df: pd.DataFrame) -> dict:
    total_cells = df.shape[0] * df.shape[1] if df.shape[1] else 0
    per_col = df.isna().sum()
    missing_total = int(per_col.sum())
    return {
        "total_missing": missing_total,
        "missing_pct": round(100 * missing_total / total_cells, 2) if total_cells else 0.0,
        "by_column": {c: int(v) for c, v in per_col.items() if v > 0},
    }


def duplicate_report(df: pd.DataFrame) -> dict:
    dup_mask = df.duplicated()
    return {
        "duplicate_rows": int(dup_mask.sum()),
        "duplicate_pct": round(100 * dup_mask.mean(), 2) if len(df) else 0.0,
    }


def outlier_report(df: pd.DataFrame, dtypes: dict | None = None) -> dict:
    """IQR-based outlier detection on numeric (non-boolean) columns only."""
    dtypes = dtypes or detect_all_dtypes(df)
    result = {}
    total_outliers = 0
    for col in numeric_columns(df, dtypes):
        q1 = safe_quantile(df[col], 0.25)
        q3 = safe_quantile(df[col], 0.75)
        if q1 is None or q3 is None:
            continue
        iqr = q3 - q1
        if iqr == 0:
            continue
        lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        numeric = pd.to_numeric(df[col], errors="coerce")
        mask = (numeric < lower) | (numeric > upper)
        count = int(mask.sum())
        if count > 0:
            result[col] = count
            total_outliers += count
    return {"total_outliers": total_outliers, "by_column": result}


def negative_value_report(df: pd.DataFrame, semantics: dict, dtypes: dict | None = None) -> dict:
    """Flag negative values in columns that should logically never be negative."""
    dtypes = dtypes or detect_all_dtypes(df)
    checks = {}
    for concept in ("revenue", "cost", "quantity"):
        col = semantics.get(concept)
        if col and col in numeric_columns(df, dtypes):
            numeric = pd.to_numeric(df[col], errors="coerce")
            count = int((numeric < 0).sum())
            if count > 0:
                checks[concept] = {"column": col, "negative_rows": count}
    return checks


def invalid_date_report(df: pd.DataFrame, semantics: dict) -> dict:
    from .types import parse_date_column
    col = semantics.get("date")
    if not col:
        return {}
    parsed = parse_date_column(df[col])
    invalid = int(parsed.isna().sum() - df[col].isna().sum())
    invalid = max(invalid, 0)
    return {"column": col, "invalid_dates": invalid} if invalid > 0 else {}


def duplicate_id_report(df: pd.DataFrame, semantics: dict) -> dict:
    col = semantics.get("order")
    if not col or col not in df.columns:
        return {}
    dup = int(df[col].duplicated().sum())
    return {"column": col, "duplicate_ids": dup} if dup > 0 else {}


def quality_score(df: pd.DataFrame, semantics: dict | None = None, dtypes: dict | None = None) -> dict:
    """Compute an overall 0-100 data quality score plus the underlying report."""
    semantics = semantics or {}
    dtypes = dtypes or detect_all_dtypes(df)

    missing = missing_report(df)
    duplicates = duplicate_report(df)
    outliers = outlier_report(df, dtypes)
    negatives = negative_value_report(df, semantics, dtypes)
    invalid_dates = invalid_date_report(df, semantics)
    duplicate_ids = duplicate_id_report(df, semantics)

    score = 100.0
    score -= min(missing["missing_pct"] * 0.6, 30)
    score -= min(duplicates["duplicate_pct"] * 0.8, 20)
    total_rows = max(len(df), 1)
    outlier_pct = 100 * outliers["total_outliers"] / total_rows
    score -= min(outlier_pct * 0.2, 15)
    if negatives:
        score -= min(5 * len(negatives), 15)
    if invalid_dates:
        score -= min(invalid_dates.get("invalid_dates", 0) / total_rows * 100 * 0.3, 10)
    if duplicate_ids:
        score -= min(duplicate_ids.get("duplicate_ids", 0) / total_rows * 100 * 0.3, 10)
    score = max(0.0, min(100.0, round(score, 1)))

    return {
        "quality_score": score,
        "missing": missing,
        "duplicates": duplicates,
        "outliers": outliers,
        "negative_values": negatives,
        "invalid_dates": invalid_dates,
        "duplicate_ids": duplicate_ids,
    }


def full_profile(df: pd.DataFrame, semantics: dict | None = None) -> dict:
    """Complete dataset profile used by summary() and reports."""
    dtypes = detect_all_dtypes(df)
    semantics = semantics if semantics is not None else {}

    numeric_cols = numeric_columns(df, dtypes)
    categorical_cols = [c for c, t in dtypes.items() if t == "categorical"]
    date_cols = [c for c, t in dtypes.items() if t in ("date", "datetime")]
    boolean_cols = [c for c, t in dtypes.items() if t == "boolean"]
    text_cols = [c for c, t in dtypes.items() if t == "text"]
    id_cols = [c for c, t in dtypes.items() if t == "identifier"]

    return {
        "rows": int(len(df)),
        "columns": int(df.shape[1]),
        "memory_bytes": int(df.memory_usage(deep=True).sum()),
        "dtypes": dtypes,
        "numeric_columns": numeric_cols,
        "categorical_columns": categorical_cols,
        "date_columns": date_cols,
        "boolean_columns": boolean_cols,
        "text_columns": text_cols,
        "identifier_columns": id_cols,
        "quality": quality_score(df, semantics, dtypes),
    }
