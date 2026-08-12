"""Business KPI calculation from detected semantic columns."""
from __future__ import annotations

import pandas as pd


def calculate_kpis(df: pd.DataFrame, semantics: dict) -> dict:
    kpis: dict = {}

    def col(concept):
        c = semantics.get(concept)
        return pd.to_numeric(df[c], errors="coerce") if c and c in df.columns else None

    revenue = col("revenue")
    cost = col("cost")
    profit = col("profit")
    quantity = col("quantity")
    discount = col("discount")

    if revenue is not None:
        kpis["total_revenue"] = float(revenue.sum())
        kpis["average_selling_price"] = float(revenue.mean())

    if cost is not None:
        kpis["total_cost"] = float(cost.sum())

    if profit is None and revenue is not None and cost is not None:
        profit = revenue - cost
        kpis["profit_derived"] = True

    if profit is not None:
        kpis["total_profit"] = float(profit.sum())
        if revenue is not None and revenue.sum() != 0:
            kpis["profit_margin_pct"] = round(100 * profit.sum() / revenue.sum(), 2)

    if quantity is not None:
        kpis["total_quantity"] = float(quantity.sum())
        if revenue is not None and quantity.sum() != 0:
            kpis["average_selling_price"] = round(float(revenue.sum() / quantity.sum()), 2)

    order_col = semantics.get("order")
    if order_col and order_col in df.columns:
        n_orders = int(df[order_col].nunique())
        kpis["orders"] = n_orders
        if revenue is not None and n_orders:
            kpis["average_order_value"] = round(float(revenue.sum() / n_orders), 2)
    else:
        kpis["orders"] = int(len(df))
        if revenue is not None and len(df):
            kpis["average_order_value"] = round(float(revenue.sum() / len(df)), 2)

    customer_col = semantics.get("customer")
    if customer_col and customer_col in df.columns:
        kpis["customers"] = int(df[customer_col].nunique())

    product_col = semantics.get("product")
    if product_col and product_col in df.columns:
        kpis["products"] = int(df[product_col].nunique())

    if discount is not None:
        kpis["average_discount_pct"] = round(float(discount.mean()), 2)
        if revenue is not None and revenue.sum() != 0:
            kpis["total_discount_value"] = round(float((revenue * discount / 100).sum()), 2) \
                if discount.max() <= 1.5 * 100 and discount.max() > 1 else None

    return kpis
