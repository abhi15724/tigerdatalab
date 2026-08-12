"""Conservative, logged data cleaning."""
from __future__ import annotations

import pandas as pd

from .types import detect_all_dtypes, parse_date_column


def clean(df: pd.DataFrame, semantics: dict | None = None) -> tuple[pd.DataFrame, list[dict]]:
    """Return a cleaned copy of df plus a list of logged operations.

    Conservative by design: never drops columns, never imputes numeric
    business values (revenue/profit/etc.) silently, only:
      - strips whitespace from text/categorical columns
      - normalizes obvious date columns to real datetimes
      - removes exact duplicate rows
      - converts numeric-looking object columns to numeric dtype
    """
    semantics = semantics or {}
    out = df.copy()
    log: list[dict] = []

    # Whitespace normalization on object columns.
    obj_cols = out.select_dtypes(include=["object", "string"]).columns
    changed_cols = []
    for col in obj_cols:
        before = out[col].copy()
        out[col] = out[col].apply(lambda v: v.strip() if isinstance(v, str) else v)
        if not before.equals(out[col]):
            changed_cols.append(col)
    if changed_cols:
        log.append({"operation": "strip_whitespace", "columns": changed_cols})

    # Date normalization.
    date_col = semantics.get("date")
    if date_col and date_col in out.columns:
        parsed = parse_date_column(out[date_col])
        n_before_valid = out[date_col].notna().sum()
        out[date_col] = parsed
        n_after_valid = out[date_col].notna().sum()
        log.append({
            "operation": "normalize_date",
            "column": date_col,
            "valid_before": int(n_before_valid),
            "valid_after": int(n_after_valid),
        })

    # Numeric coercion for business-numeric semantic columns stored as text.
    for concept in ("revenue", "profit", "cost", "quantity", "discount", "price"):
        col = semantics.get(concept)
        if col and col in out.columns and out[col].dtype == object:
            coerced = pd.to_numeric(
                out[col].astype(str).str.replace(r"[,\u20b9$%]", "", regex=True).str.strip(),
                errors="coerce",
            )
            if coerced.notna().sum() > 0:
                out[col] = coerced
                log.append({"operation": "coerce_numeric", "column": col})

    # Infinite values (+inf/-inf) are treated as invalid/missing, not as
    # real numbers. Left unhandled they silently poison downstream sums
    # and means (e.g. inf + -inf = NaN corrupts a whole KPI total without
    # any warning), so they're replaced with NaN here - same as any other
    # missing value - and the count is logged so it stays visible rather
    # than disappearing quietly.
    import numpy as np
    numeric_cols = out.select_dtypes(include="number").columns
    inf_counts = {}
    for col in numeric_cols:
        mask = np.isinf(out[col])
        n_inf = int(mask.sum())
        if n_inf > 0:
            out.loc[mask, col] = pd.NA
            inf_counts[col] = n_inf
    if inf_counts:
        log.append({"operation": "remove_infinite_values", "by_column": inf_counts})

    # Duplicate removal.
    before_rows = len(out)
    out = out.drop_duplicates()
    removed = before_rows - len(out)
    if removed > 0:
        log.append({"operation": "remove_duplicates", "rows_removed": int(removed)})

    return out.reset_index(drop=True), log
