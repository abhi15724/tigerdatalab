"""Customer-level analytics. Raises NoCustomerIdentifierError when no
customer identifier column was detected, rather than inventing numbers."""
from __future__ import annotations

import pandas as pd

from ..exceptions import NoCustomerIdentifierError


def analyze_customers(df: pd.DataFrame, semantics: dict) -> dict:
    customer_col = semantics.get("customer")
    if not customer_col or customer_col not in df.columns:
        raise NoCustomerIdentifierError()

    revenue_col = semantics.get("revenue")
    profit_col = semantics.get("profit")
    order_col = semantics.get("order")

    grouped = df.groupby(customer_col)
    n_customers = int(df[customer_col].nunique())

    result: dict = {"customer_column": customer_col, "unique_customers": n_customers}

    if order_col and order_col in df.columns:
        orders_per_customer = grouped[order_col].nunique()
        result["avg_orders_per_customer"] = round(float(orders_per_customer.mean()), 2)
        result["repeat_customers"] = int((orders_per_customer > 1).sum())
        result["one_time_customers"] = int((orders_per_customer == 1).sum())
    else:
        orders_per_customer = grouped.size()
        result["avg_orders_per_customer"] = round(float(orders_per_customer.mean()), 2)
        result["repeat_customers"] = int((orders_per_customer > 1).sum())
        result["one_time_customers"] = int((orders_per_customer == 1).sum())

    if revenue_col and revenue_col in df.columns:
        rev_by_customer = grouped[revenue_col].apply(lambda s: pd.to_numeric(s, errors="coerce").sum())
        total_rev = rev_by_customer.sum()
        result["avg_revenue_per_customer"] = round(float(rev_by_customer.mean()), 2)
        top = rev_by_customer.sort_values(ascending=False).head(10)
        result["top_customers"] = [{"customer": str(k), "revenue": float(v)} for k, v in top.items()]
        bottom = rev_by_customer.sort_values(ascending=True).head(10)
        result["bottom_customers"] = [{"customer": str(k), "revenue": float(v)} for k, v in bottom.items()]
        if total_rev:
            top5_share = top.head(5).sum() / total_rev * 100
            result["top5_revenue_concentration_pct"] = round(float(top5_share), 2)

    if profit_col and profit_col in df.columns:
        profit_by_customer = grouped[profit_col].apply(lambda s: pd.to_numeric(s, errors="coerce").sum())
        result["avg_profit_per_customer"] = round(float(profit_by_customer.mean()), 2)

    return result
