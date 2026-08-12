"""Deterministic answers to the standard set of business questions,
built entirely from data already computed by core.AnalysisResult
(kpis, category/product/customer analysis, growth, quality).

Every answer that cannot be determined from the data returns a clear
"not available" message instead of guessing.
"""
from __future__ import annotations


def _na(reason: str) -> dict:
    return {"available": False, "answer": None, "reason": reason}


def _ok(answer) -> dict:
    return {"available": True, "answer": answer}


def answer_business_questions(kpis: dict, category: dict, product: dict,
                               customer: dict | None, growth: dict, quality: dict) -> dict:
    q: dict[str, dict] = {}

    q["how_many_customers_bought_products"] = (
        _ok(customer["unique_customers"]) if customer and customer.get("available", True) and "unique_customers" in (customer or {})
        else _na("No customer identifier detected.")
    )
    q["how_many_unique_customers"] = q["how_many_customers_bought_products"]

    q["how_many_orders"] = _ok(kpis["orders"]) if "orders" in kpis else _na("No order/row count available.")

    q["how_many_products_sold"] = (
        _ok(kpis["products"]) if "products" in kpis else _na("No product identifier detected.")
    )

    if product and product.get("available") and product.get("top_products_by_revenue"):
        q["which_product_sells_the_most"] = _ok(
            max(product.get("top_products_by_quantity", product["top_products_by_revenue"]),
                key=lambda r: r.get("quantity", r.get("revenue", 0)))
        )
        q["which_product_generates_the_most_revenue"] = _ok(product["top_products_by_revenue"][0])
    else:
        q["which_product_sells_the_most"] = _na("No product/quantity data available.")
        q["which_product_generates_the_most_revenue"] = _na("No product/revenue data available.")

    if product and product.get("available") and product.get("top_products_by_profit"):
        q["which_product_generates_the_highest_profit"] = _ok(product["top_products_by_profit"][0])
    else:
        q["which_product_generates_the_highest_profit"] = _na("No product/profit data available.")

    if category and category.get("available") and category.get("revenue_by_category"):
        q["which_category_generates_the_most_revenue"] = _ok(category["revenue_by_category"][0])
    else:
        q["which_category_generates_the_most_revenue"] = _na("No category/revenue data available.")

    if category and category.get("available") and category.get("profit_by_category"):
        q["which_category_generates_the_highest_profit"] = _ok(category["profit_by_category"][0])
    else:
        q["which_category_generates_the_highest_profit"] = _na("No category/profit data available.")

    if category and category.get("worst_margin_category"):
        q["which_category_has_the_worst_margin"] = _ok(category["worst_margin_category"])
    else:
        q["which_category_has_the_worst_margin"] = _na("No category margin data available.")

    q["how_much_revenue_was_generated"] = _ok(kpis["total_revenue"]) if "total_revenue" in kpis else _na("No revenue column detected.")
    q["how_much_profit_was_generated"] = _ok(kpis["total_profit"]) if "total_profit" in kpis else _na("No profit column detected.")
    q["what_is_the_profit_margin"] = _ok(kpis["profit_margin_pct"]) if "profit_margin_pct" in kpis else _na("Revenue and profit both required.")
    q["what_is_the_average_order_value"] = _ok(kpis["average_order_value"]) if "average_order_value" in kpis else _na("No order/revenue data available.")
    q["what_is_the_average_selling_price"] = _ok(kpis["average_selling_price"]) if "average_selling_price" in kpis else _na("No revenue data available.")
    q["what_is_the_average_quantity_per_order"] = (
        _ok(round(kpis["total_quantity"] / kpis["orders"], 2))
        if "total_quantity" in kpis and kpis.get("orders") else _na("No quantity/order data available.")
    )
    q["how_much_discount_was_given"] = _ok(kpis.get("total_discount_value") or kpis.get("average_discount_pct")) \
        if ("total_discount_value" in kpis or "average_discount_pct" in kpis) else _na("No discount column detected.")

    if "average_discount_pct" in kpis and "profit_margin_pct" in kpis:
        hurting = kpis["average_discount_pct"] >= 10 and kpis["profit_margin_pct"] < 15
        q["is_discount_hurting_profit"] = _ok(hurting)
    else:
        q["is_discount_hurting_profit"] = _na("Discount and margin data both required.")

    if product and product.get("available") and "loss_making_products" in product:
        q["which_products_are_loss_making"] = _ok(product["loss_making_products"])
    else:
        q["which_products_are_loss_making"] = _na("No product/profit data available.")

    if customer and customer.get("top_customers"):
        q["which_customers_generate_the_most_revenue"] = _ok(customer["top_customers"][:5])
    else:
        q["which_customers_generate_the_most_revenue"] = _na("No customer/revenue data available.")

    g_product = growth.get("product", {})
    g_category = growth.get("category", {})
    q["which_products_are_declining"] = _ok(g_product.get("declining")) if g_product.get("available") else _na(g_product.get("reason", "Not available."))
    q["which_products_are_growing"] = _ok(g_product.get("growing")) if g_product.get("available") else _na(g_product.get("reason", "Not available."))
    q["which_category_is_declining"] = _ok(g_category.get("declining")) if g_category.get("available") else _na(g_category.get("reason", "Not available."))
    q["which_category_is_growing"] = _ok(g_category.get("growing")) if g_category.get("available") else _na(g_category.get("reason", "Not available."))

    if product and product.get("available") and product.get("loss_making_product_count", 0) > 0:
        q["where_is_the_company_losing_money"] = _ok(
            f"{product['loss_making_product_count']} products are loss-making; see which_products_are_loss_making."
        )
    else:
        q["where_is_the_company_losing_money"] = _na("No clear loss-making pattern detected.")

    q_score = quality.get("quality_score")
    q["where_should_the_business_improve"] = _ok(
        "Data quality" if q_score is not None and q_score < 70 else "See business insights for the top severity findings."
    )

    return q
