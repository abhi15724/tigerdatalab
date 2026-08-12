"""Product-level analytics."""
from __future__ import annotations

import pandas as pd


def analyze_products(df: pd.DataFrame, semantics: dict) -> dict:
    product_col = semantics.get("product")
    if not product_col or product_col not in df.columns:
        return {"available": False, "reason": "No product identifier/name column was detected."}

    revenue_col = semantics.get("revenue")
    profit_col = semantics.get("profit")
    quantity_col = semantics.get("quantity")
    discount_col = semantics.get("discount")

    grouped = df.groupby(product_col)
    result: dict = {"available": True, "product_column": product_col, "unique_products": int(df[product_col].nunique())}

    if revenue_col and revenue_col in df.columns:
        rev = grouped[revenue_col].apply(lambda s: pd.to_numeric(s, errors="coerce").sum()).sort_values(ascending=False)
        result["top_products_by_revenue"] = [{"product": str(k), "revenue": float(v)} for k, v in rev.head(10).items()]

    if quantity_col and quantity_col in df.columns:
        qty = grouped[quantity_col].apply(lambda s: pd.to_numeric(s, errors="coerce").sum()).sort_values(ascending=False)
        result["top_products_by_quantity"] = [{"product": str(k), "quantity": float(v)} for k, v in qty.head(10).items()]

    if profit_col and profit_col in df.columns:
        profit = grouped[profit_col].apply(lambda s: pd.to_numeric(s, errors="coerce").sum()).sort_values(ascending=False)
        result["top_products_by_profit"] = [{"product": str(k), "profit": float(v)} for k, v in profit.head(10).items()]
        result["worst_products_by_profit"] = [{"product": str(k), "profit": float(v)} for k, v in profit.tail(10).items()]
        negative = profit[profit < 0]
        result["loss_making_products"] = [{"product": str(k), "profit": float(v)} for k, v in negative.items()]
        result["loss_making_product_count"] = int(len(negative))

    if discount_col and discount_col in df.columns:
        disc = grouped[discount_col].apply(lambda s: pd.to_numeric(s, errors="coerce").mean()).sort_values(ascending=False)
        result["highest_discount_products"] = [{"product": str(k), "avg_discount": float(v)} for k, v in disc.head(10).items()]

    return result
