"""Robust column type + business-semantic detection.

Fixes previous bugs:
 - never runs .quantile() on boolean columns
 - never blindly runs pd.to_datetime() on every column
"""
from __future__ import annotations

import re
import warnings

import numpy as np
import pandas as pd

from ..config import SEMANTIC_KEYWORDS, SEMANTIC_PRIORITY

DATE_PARSE_SUCCESS_THRESHOLD = 0.85


def _normalize(name: str) -> str:
    s = str(name).strip()
    # Split camelCase / PascalCase boundaries (e.g. "discountedSellingPrice"
    # -> "discounted_Selling_Price") BEFORE lower-casing, so that keyword
    # matching (e.g. "selling_price") works on real-world API-style column
    # names, not just already-snake_case ones.
    s = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", s)
    s = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", "_", s)
    s = re.sub(r"[\s\-]+", "_", s)
    return s.lower()


def detect_dtype(series: pd.Series) -> str:
    """Classify a single column into one of:
    boolean, integer, float, numeric, date, datetime, categorical, text, identifier
    """
    s = series.dropna()
    if s.empty:
        return "unknown"

    if pd.api.types.is_bool_dtype(series):
        return "boolean"

    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"

    if pd.api.types.is_numeric_dtype(series):
        if pd.api.types.is_integer_dtype(series):
            unique_ratio = series.nunique(dropna=True) / max(len(series), 1)
            if unique_ratio > 0.95 and series.nunique() > 20:
                return "identifier"
            return "integer"
        return "float"

    # Object / string columns: decide between date, categorical, text, identifier.
    if pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series):
        name_hint = _normalize(series.name or "")
        looks_date_by_name = any(k in name_hint for k in SEMANTIC_KEYWORDS["date"])

        sample = s.astype(str).head(200)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            parsed = pd.to_datetime(sample, errors="coerce", format="mixed")
        success_ratio = parsed.notna().mean() if len(sample) else 0

        if success_ratio >= DATE_PARSE_SUCCESS_THRESHOLD or (
            looks_date_by_name and success_ratio >= 0.5
        ):
            return "date"

        unique_ratio = series.nunique(dropna=True) / max(len(series), 1)
        if unique_ratio > 0.9 and series.nunique() > 20:
            return "identifier"

        avg_len = s.astype(str).str.len().mean()
        if unique_ratio < 0.5 or (avg_len is not None and avg_len < 30):
            return "categorical"
        return "text"

    return "text"


def detect_all_dtypes(df: pd.DataFrame) -> dict[str, str]:
    return {col: detect_dtype(df[col]) for col in df.columns}


def numeric_columns(df: pd.DataFrame, dtypes: dict[str, str] | None = None) -> list[str]:
    """Numeric columns, explicitly EXCLUDING booleans."""
    dtypes = dtypes or detect_all_dtypes(df)
    return [c for c, t in dtypes.items() if t in ("integer", "float")]


def boolean_columns(df: pd.DataFrame, dtypes: dict[str, str] | None = None) -> list[str]:
    dtypes = dtypes or detect_all_dtypes(df)
    return [c for c, t in dtypes.items() if t == "boolean"]


def categorical_columns(df: pd.DataFrame, dtypes: dict[str, str] | None = None) -> list[str]:
    dtypes = dtypes or detect_all_dtypes(df)
    return [c for c, t in dtypes.items() if t == "categorical"]


def date_columns(df: pd.DataFrame, dtypes: dict[str, str] | None = None) -> list[str]:
    dtypes = dtypes or detect_all_dtypes(df)
    return [c for c, t in dtypes.items() if t in ("date", "datetime")]


def identifier_columns(df: pd.DataFrame, dtypes: dict[str, str] | None = None) -> list[str]:
    dtypes = dtypes or detect_all_dtypes(df)
    return [c for c, t in dtypes.items() if t == "identifier"]


def safe_quantile(series: pd.Series, q: float) -> float | None:
    """Quantile that refuses to operate on boolean/non-numeric data."""
    if pd.api.types.is_bool_dtype(series):
        return None
    numeric = pd.to_numeric(series, errors="coerce").dropna()
    if numeric.empty:
        return None
    return float(numeric.quantile(q))


def parse_date_column(series: pd.Series) -> pd.Series:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return pd.to_datetime(series, errors="coerce", format="mixed")


def detect_semantics(df: pd.DataFrame, dtypes: dict[str, str] | None = None) -> dict[str, str]:
    """Map business concept -> column name, for the single best-matching
    column per concept. Returns only concepts that were actually detected."""
    dtypes = dtypes or detect_all_dtypes(df)
    normalized = {col: _normalize(col) for col in df.columns}
    result: dict[str, str] = {}
    used_cols: set[str] = set()

    for concept in SEMANTIC_PRIORITY:
        keywords = SEMANTIC_KEYWORDS[concept]
        best_col, best_score = None, -1
        for col, norm in normalized.items():
            if col in used_cols:
                continue
            for kw in keywords:
                if norm == kw:
                    score = 100
                elif norm.endswith("_" + kw) or norm.startswith(kw + "_"):
                    score = 80
                elif kw in norm:
                    score = 50
                else:
                    continue
                if score > best_score:
                    best_score, best_col = score, col
        if best_col is not None and best_score >= 50:
            # sanity-check against detected dtype where it matters
            dtype = dtypes.get(best_col)
            if concept == "date" and dtype not in ("date", "datetime"):
                continue
            if concept in ("revenue", "profit", "cost", "quantity", "discount", "price") and dtype == "categorical":
                continue
            result[concept] = best_col
            used_cols.add(best_col)

    return result
