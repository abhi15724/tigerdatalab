"""Growth/decline detection per product and per category.

Splits the dataset's date range into an earlier half and a later half,
compares the chosen metric (revenue by default) per group, and tags each
group as growing / declining / flat. Requires a date column; degrades to
`{"available": False, ...}` when one isn't present rather than crashing.
"""
from __future__ import annotations

import pandas as pd

from ..quality.types import parse_date_column

FLAT_BAND_PCT = 5.0


def _growth_by_group(df: pd.DataFrame, group_col: str, date_col: str, metric_col: str) -> dict:
    dates = parse_date_column(df[date_col])
    metric = pd.to_numeric(df[metric_col], errors="coerce")
    work = pd.DataFrame({"group": df[group_col], "date": dates, "value": metric}).dropna()
    if work.empty or work["date"].nunique() < 2:
        return {"available": False, "reason": "Not enough valid date-tagged rows to compute growth."}

    midpoint = work["date"].min() + (work["date"].max() - work["date"].min()) / 2
    first_half = work[work["date"] <= midpoint].groupby("group")["value"].sum()
    second_half = work[work["date"] > midpoint].groupby("group")["value"].sum()

    all_groups = set(first_half.index) | set(second_half.index)
    rows = []
    for g in all_groups:
        f = float(first_half.get(g, 0.0))
        s = float(second_half.get(g, 0.0))
        if f == 0 and s == 0:
            continue
        if f == 0:
            change_pct = 100.0 if s > 0 else 0.0
        else:
            change_pct = round(100 * (s - f) / abs(f), 2)
        if change_pct > FLAT_BAND_PCT:
            status = "growing"
        elif change_pct < -FLAT_BAND_PCT:
            status = "declining"
        else:
            status = "flat"
        rows.append({"group": str(g), "first_half": round(f, 2), "second_half": round(s, 2),
                      "change_pct": change_pct, "status": status})

    rows.sort(key=lambda r: r["change_pct"])
    growing = [r for r in rows if r["status"] == "growing"]
    declining = [r for r in rows if r["status"] == "declining"]

    return {
        "available": True,
        "group_column": group_col,
        "metric_column": metric_col,
        "split_date": midpoint.strftime("%Y-%m-%d"),
        "growing": sorted(growing, key=lambda r: -r["change_pct"])[:10],
        "declining": declining[:10],
        "all": rows,
    }


def analyze_growth(df: pd.DataFrame, semantics: dict) -> dict:
    date_col = semantics.get("date")
    metric_col = semantics.get("revenue") or semantics.get("profit") or semantics.get("quantity")
    result = {"product": {"available": False}, "category": {"available": False}}

    if not date_col or not metric_col:
        result["product"] = {"available": False, "reason": "No date + numeric metric available for growth analysis."}
        result["category"] = result["product"]
        return result

    product_col = semantics.get("product")
    category_col = semantics.get("category")

    if product_col and product_col in df.columns:
        result["product"] = _growth_by_group(df, product_col, date_col, metric_col)
    else:
        result["product"] = {"available": False, "reason": "No product column detected."}

    if category_col and category_col in df.columns:
        result["category"] = _growth_by_group(df, category_col, date_col, metric_col)
    else:
        result["category"] = {"available": False, "reason": "No category column detected."}

    return result
