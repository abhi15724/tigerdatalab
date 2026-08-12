"""Profitability derivation: profit = revenue - cost when profit is absent."""
from __future__ import annotations

import pandas as pd


def ensure_profit_column(df: pd.DataFrame, semantics: dict) -> tuple[pd.DataFrame, dict, bool]:
    """Return (df, semantics, derived) - adds a `_tdl_profit` column and
    registers it under semantics['profit'] only if profit is not already
    present but revenue and cost both are. Never overwrites an existing
    business column."""
    if semantics.get("profit"):
        return df, semantics, False

    revenue_col = semantics.get("revenue")
    cost_col = semantics.get("cost")
    if revenue_col and cost_col and revenue_col in df.columns and cost_col in df.columns:
        out = df.copy()
        out["_tdl_profit"] = pd.to_numeric(out[revenue_col], errors="coerce") - pd.to_numeric(out[cost_col], errors="coerce")
        new_semantics = dict(semantics)
        new_semantics["profit"] = "_tdl_profit"
        return out, new_semantics, True

    return df, semantics, False
