"""Category-level analytics + Pareto data for chart engine."""
from __future__ import annotations

import pandas as pd


def analyze_categories(df: pd.DataFrame, semantics: dict) -> dict:
    category_col = semantics.get("category")
    if not category_col or category_col not in df.columns:
        return {"available": False, "reason": "No category/segment column was detected."}

    revenue_col = semantics.get("revenue")
    profit_col = semantics.get("profit")

    grouped = df.groupby(category_col)
    result: dict = {"available": True, "category_column": category_col, "unique_categories": int(df[category_col].nunique())}

    if revenue_col and revenue_col in df.columns:
        rev = grouped[revenue_col].apply(lambda s: pd.to_numeric(s, errors="coerce").sum()).sort_values(ascending=False)
        total = rev.sum()
        result["revenue_by_category"] = [{"category": str(k), "revenue": float(v),
                                           "share_pct": round(float(100 * v / total), 2) if total else 0}
                                          for k, v in rev.items()]
        if total:
            result["top_category_revenue_share_pct"] = round(float(100 * rev.iloc[0] / total), 2)
            result["top_category"] = str(rev.index[0])

    if profit_col and profit_col in df.columns:
        profit = grouped[profit_col].apply(lambda s: pd.to_numeric(s, errors="coerce").sum()).sort_values(ascending=False)
        result["profit_by_category"] = [{"category": str(k), "profit": float(v)} for k, v in profit.items()]
        if revenue_col and revenue_col in df.columns:
            rev_by_cat = grouped[revenue_col].apply(lambda s: pd.to_numeric(s, errors="coerce").sum())
            margin = (profit / rev_by_cat.reindex(profit.index) * 100).round(2)
            margin_sorted = margin.sort_values()
            result["worst_margin_category"] = str(margin_sorted.index[0]) if len(margin_sorted) else None
            result["margin_by_category"] = [{"category": str(k), "margin_pct": float(v)} for k, v in margin.items() if pd.notna(v)]

    return result
