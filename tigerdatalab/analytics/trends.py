"""Time-trend analysis: monthly/daily aggregation, MoM, YoY, rolling avg."""
from __future__ import annotations

import pandas as pd

from ..exceptions import NoTrendDataError
from ..quality.types import parse_date_column, numeric_columns, detect_all_dtypes


def _pick_metric(df: pd.DataFrame, semantics: dict) -> str | None:
    for concept in ("revenue", "profit", "cost", "quantity"):
        col = semantics.get(concept)
        if col and col in df.columns:
            return col
    numeric = numeric_columns(df)
    return numeric[0] if numeric else None


def compute_trend(df: pd.DataFrame, semantics: dict) -> dict:
    date_col = semantics.get("date")
    if not date_col or date_col not in df.columns:
        raise NoTrendDataError(candidates=[])

    metric_col = _pick_metric(df, semantics)
    if not metric_col:
        raise NoTrendDataError(candidates=[date_col])

    dates = parse_date_column(df[date_col])
    metric = pd.to_numeric(df[metric_col], errors="coerce")
    work = pd.DataFrame({"date": dates, "value": metric}).dropna()

    if work.empty or work["date"].nunique() < 2:
        raise NoTrendDataError(candidates=[date_col])

    span_days = (work["date"].max() - work["date"].min()).days
    freq = "D" if span_days <= 62 else "M"

    work = work.set_index("date").sort_index()
    if freq == "D":
        agg = work["value"].resample("D").sum()
        granularity = "daily"
    else:
        agg = work["value"].resample("ME").sum()
        granularity = "monthly"

    agg = agg[agg.index.notna()]
    result_df = agg.reset_index()
    result_df.columns = ["period", "value"]

    growth_pct = None
    if len(agg) >= 2 and agg.iloc[0] != 0:
        growth_pct = round(100 * (agg.iloc[-1] - agg.iloc[0]) / abs(agg.iloc[0]), 2)

    mom_pct = None
    if len(agg) >= 2 and agg.iloc[-2] != 0:
        mom_pct = round(100 * (agg.iloc[-1] - agg.iloc[-2]) / abs(agg.iloc[-2]), 2)

    yoy_pct = None
    if granularity == "monthly" and len(agg) >= 13 and agg.iloc[-13] != 0:
        yoy_pct = round(100 * (agg.iloc[-1] - agg.iloc[-13]) / abs(agg.iloc[-13]), 2)

    rolling = agg.rolling(window=3, min_periods=1).mean()

    label = {"revenue": "Revenue", "profit": "Profit", "cost": "Cost", "quantity": "Quantity"}
    metric_label = next((v for k, v in label.items() if semantics.get(k) == metric_col), metric_col)

    return {
        "date_column": date_col,
        "metric_column": metric_col,
        "metric_label": metric_label,
        "granularity": granularity,
        "title": f"{granularity.capitalize()} {metric_label} Trend",
        "periods": [p.strftime("%Y-%m-%d") for p in result_df["period"]],
        "values": [float(v) for v in result_df["value"]],
        "rolling_average": [float(v) for v in rolling.values],
        "growth_pct": growth_pct,
        "mom_pct": mom_pct,
        "yoy_pct": yoy_pct,
    }
