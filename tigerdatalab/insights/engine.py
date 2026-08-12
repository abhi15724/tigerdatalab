"""Rule-based business insight engine (no LLM required).

Every insight follows: severity, title, evidence, impact, recommendation.
"""
from __future__ import annotations

from typing import Protocol


class InsightProvider(Protocol):
    """Interface so an optional LLM-backed provider can be swapped in later
    without changing anything else in TigerDataLab."""

    def generate(self, context: dict) -> list[dict]: ...


def _fmt_money(v: float) -> str:
    return f"{v:,.2f}"


class RuleBasedInsightProvider:
    """Deterministic, threshold + evidence based insight generation."""

    def generate(self, context: dict) -> list[dict]:
        insights: list[dict] = []
        kpis = context.get("kpis", {})
        quality = context.get("quality", {})
        category = context.get("category", {})
        product = context.get("product", {})
        trend = context.get("trend")
        customer = context.get("customer")

        # --- Revenue concentration ---
        if category.get("available") and category.get("top_category_revenue_share_pct") is not None:
            share = category["top_category_revenue_share_pct"]
            top_cat = category.get("top_category")
            if share >= 35:
                severity = "HIGH" if share >= 50 else "MEDIUM"
                insights.append({
                    "severity": severity,
                    "title": f"Revenue concentration in '{top_cat}'",
                    "evidence": f"'{top_cat}' contributes {share}% of total revenue.",
                    "impact": (
                        "A supply disruption or demand decline in this category could "
                        "materially reduce total revenue."
                    ),
                    "recommendation": (
                        f"Maintain reliable inventory/availability for '{top_cat}' while "
                        "actively growing the next two highest-potential categories to "
                        "reduce concentration risk."
                    ),
                })

        # --- Loss-making products ---
        if product.get("available") and product.get("loss_making_product_count", 0) > 0:
            n = product["loss_making_product_count"]
            severity = "HIGH" if n >= 10 else ("MEDIUM" if n >= 3 else "LOW")
            insights.append({
                "severity": severity,
                "title": "Loss-making products detected",
                "evidence": f"{n} products generated negative profit.",
                "impact": "These products reduce overall contribution margin and may be silently subsidized by profitable lines.",
                "recommendation": "Review supplier cost, selling price, and discount policy for the affected SKUs; consider repricing or discontinuation.",
            })

        # --- Discount vs margin ---
        discount_pct = kpis.get("average_discount_pct")
        margin_pct = kpis.get("profit_margin_pct")
        if discount_pct is not None:
            severity = "MEDIUM" if discount_pct >= 15 else "LOW"
            impact = "High average discounting compresses margins and can train customers to wait for discounts."
            if margin_pct is not None and margin_pct < 10:
                severity = "HIGH"
                impact += f" Combined with a thin profit margin of {margin_pct}%, this poses a direct profitability risk."
            if discount_pct >= 10:
                insights.append({
                    "severity": severity,
                    "title": "Elevated discounting levels",
                    "evidence": f"Average discount across transactions is {discount_pct}%.",
                    "impact": impact,
                    "recommendation": "Audit discount rules by category/product and tie discounting to inventory-clearance or acquisition goals rather than blanket application.",
                })

        # --- Margin ---
        if margin_pct is not None:
            if margin_pct < 5:
                insights.append({
                    "severity": "HIGH",
                    "title": "Very thin overall profit margin",
                    "evidence": f"Overall profit margin is {margin_pct}%.",
                    "impact": "Small cost increases or discount changes could push the business into a loss.",
                    "recommendation": "Prioritize cost control and pricing review; identify and fix the specific products/categories dragging margin down.",
                })
            elif margin_pct > 30:
                insights.append({
                    "severity": "LOW",
                    "title": "Healthy profit margin",
                    "evidence": f"Overall profit margin is {margin_pct}%.",
                    "impact": "The business has room to invest in growth, discounts, or customer acquisition without immediate margin risk.",
                    "recommendation": "Consider reinvesting a portion of margin into demand generation for underperforming categories.",
                })

        # --- Customer concentration ---
        if customer and customer.get("top5_revenue_concentration_pct") is not None:
            share = customer["top5_revenue_concentration_pct"]
            if share >= 30:
                insights.append({
                    "severity": "MEDIUM" if share < 50 else "HIGH",
                    "title": "Revenue concentrated in top customers",
                    "evidence": f"The top 5 customers contribute {share}% of total revenue.",
                    "impact": "Losing even one or two of these customers could significantly impact revenue.",
                    "recommendation": "Build retention programs for top accounts while actively diversifying the customer base.",
                })

        # --- Trend / growth ---
        if trend and trend.get("growth_pct") is not None:
            g = trend["growth_pct"]
            metric = trend.get("metric_label", "the tracked metric")
            if g <= -10:
                insights.append({
                    "severity": "HIGH",
                    "title": f"Declining {metric.lower()} trend",
                    "evidence": f"{metric} changed by {g}% from the first to the most recent period in the dataset.",
                    "impact": "A sustained decline compounds over time and can be harder to reverse the longer it continues.",
                    "recommendation": f"Investigate the drivers behind the {metric.lower()} decline (mix shift, pricing, demand, churn) and prioritize corrective actions.",
                })
            elif g >= 20:
                insights.append({
                    "severity": "LOW",
                    "title": f"Strong {metric.lower()} growth",
                    "evidence": f"{metric} grew {g}% from the first to the most recent period in the dataset.",
                    "impact": "Growth at this pace may strain inventory, staffing, or fulfillment capacity if unplanned.",
                    "recommendation": "Confirm supply chain and operational capacity can sustain the current growth trajectory.",
                })

        # --- Data quality ---
        q_score = quality.get("quality_score")
        if q_score is not None and q_score < 70:
            severity = "HIGH" if q_score < 50 else "MEDIUM"
            insights.append({
                "severity": severity,
                "title": "Data quality issues detected",
                "evidence": f"Overall data quality score is {q_score}/100, driven by missing values, duplicates, and/or outliers.",
                "impact": "Downstream KPIs and insights may be understated or overstated until the underlying data issues are resolved.",
                "recommendation": "Review the data-quality report for missing values, duplicate rows, and outliers, and fix them at the source system where possible.",
            })

        if not insights:
            insights.append({
                "severity": "LOW",
                "title": "No significant risk patterns detected",
                "evidence": "No thresholds for concentration, loss-making products, thin margins, or data-quality problems were breached.",
                "impact": "The dataset appears healthy on the dimensions TigerDataLab currently evaluates.",
                "recommendation": "Continue monitoring KPIs regularly as new data arrives.",
            })

        severity_rank = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        insights.sort(key=lambda i: severity_rank.get(i["severity"], 3))
        return insights


def generate_insights(context: dict, provider: InsightProvider | None = None) -> list[dict]:
    provider = provider or RuleBasedInsightProvider()
    return provider.generate(context)


def generate_recommendations(insights: list[dict]) -> list[str]:
    seen = set()
    recs = []
    for ins in insights:
        rec = ins.get("recommendation")
        if rec and rec not in seen:
            recs.append(rec)
            seen.add(rec)
    return recs
