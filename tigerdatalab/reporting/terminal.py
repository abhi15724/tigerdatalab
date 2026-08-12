"""Renders an AnalysisResult as clean, aligned ASCII tables for the
terminal - the "professional data analyst printout" view. No extra
dependencies (no tabulate/rich) - pure stdlib string formatting so it
works anywhere pandas does.
"""
from __future__ import annotations

from typing import Sequence

_H, _V = "-", "|"
_TL, _TR, _BL, _BR, _T, _B, _L, _R, _X = "+", "+", "+", "+", "+", "+", "+", "+", "+"


def _fmt_cell(value) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:,.2f}"
    if isinstance(value, int):
        return f"{value:,}"
    return str(value)


def render_table(headers: Sequence[str], rows: Sequence[Sequence], title: str | None = None) -> str:
    """Render a simple bordered ASCII table. Numeric-looking columns are
    right-aligned, everything else left-aligned."""
    str_rows = [[_fmt_cell(c) for c in row] for row in rows]
    widths = [len(h) for h in headers]
    for row in str_rows:
        for i, c in enumerate(row):
            widths[i] = max(widths[i], len(c))
    widths = [max(w, 3) for w in widths]

    def sep(left, mid, right):
        return left + mid.join(_H * (w + 2) for w in widths) + right

    def fmt_row(cells, align):
        parts = []
        for c, w, a in zip(cells, widths, align):
            parts.append(f" {c.rjust(w) if a == 'r' else c.ljust(w)} ")
        return _V + _V.join(parts) + _V

    # right-align columns whose header suggests a number, else left-align
    align = ["r" if any(k in h.lower() for k in
                         ("qty", "quantity", "count", "%", "pct", "price", "revenue",
                          "amount", "profit", "score", "value", "discount", "rows",
                          "columns", "n_", "num", "total"))
             else "l" for h in headers]

    lines = []
    if title:
        lines.append(title)
    lines.append(sep(_TL, _T, _TR))
    lines.append(fmt_row(headers, ["l"] * len(headers)))
    lines.append(sep(_L, _X, _R))
    for row in str_rows:
        lines.append(fmt_row(row, align))
    lines.append(sep(_BL, _B, _BR))
    return "\n".join(lines)


def render_terminal_report(result) -> str:
    """Build the full multi-table terminal report for an AnalysisResult."""
    sections: list[str] = []

    sections.append("=" * 60)
    sections.append(f" TigerDataLab Analysis Report - {result.source}")
    sections.append("=" * 60)

    # --- Dataset overview ---
    p = result.profile
    q = p["quality"]
    overview_rows = [
        ["Rows", p["rows"]],
        ["Columns", p["columns"]],
        ["Memory (KB)", round(p["memory_bytes"] / 1024, 1)],
        ["Missing values", q["missing"]["total_missing"]],
        ["Duplicate rows", q["duplicates"]["duplicate_rows"]],
        ["Numeric columns", len(p["numeric_columns"])],
        ["Categorical columns", len(p["categorical_columns"])],
        ["Date columns", len(p["date_columns"])],
        ["Data quality score", f"{q['quality_score']}/100"],
        ["Encoding used", result.load_meta.get("encoding", "utf-8")],
    ]
    sections.append("\n" + render_table(["Metric", "Value"], overview_rows, "DATASET OVERVIEW"))

    # --- Business KPIs ---
    kpis = result.kpis()
    if kpis:
        kpi_rows = [[k.replace("_", " ").title(), v] for k, v in kpis.items()]
        sections.append("\n" + render_table(["KPI", "Value"], kpi_rows, "BUSINESS KPIs"))
    else:
        sections.append("\nBUSINESS KPIs\nNo recognizable business columns (revenue/quantity/order/etc.) were found.")

    # --- Category breakdown ---
    cat = result.categories()
    if cat.get("available"):
        if cat.get("revenue_by_category"):
            rows = [[c["category"], c["revenue"], f"{c['share_pct']}%"] for c in cat["revenue_by_category"][:10]]
            sections.append("\n" + render_table(["Category", "Revenue", "Share"], rows, "REVENUE BY CATEGORY (Top 10)"))
        else:
            sections.append(
                f"\nCATEGORY\nDetected category column '{cat['category_column']}' "
                f"with {cat['unique_categories']} unique categories. "
                f"(No revenue column found, so revenue-by-category is unavailable.)"
            )

    # --- Product breakdown ---
    prod = result.products()
    if prod.get("available"):
        if prod.get("top_products_by_quantity"):
            rows = [[i + 1, r["product"], r["quantity"]] for i, r in enumerate(prod["top_products_by_quantity"][:10])]
            sections.append("\n" + render_table(["#", "Product", "Total Quantity"], rows, "TOP 10 PRODUCTS BY QUANTITY"))
        if prod.get("highest_discount_products"):
            rows = [[i + 1, r["product"], f"{r['avg_discount']}%"] for i, r in enumerate(prod["highest_discount_products"][:10])]
            sections.append("\n" + render_table(["#", "Product", "Avg Discount"], rows, "TOP 10 HIGHEST-DISCOUNT PRODUCTS"))

    # --- Data quality: outliers by column ---
    outliers = q.get("outliers", {}).get("by_column", {})
    if outliers:
        rows = sorted(outliers.items(), key=lambda kv: -kv[1])
        sections.append("\n" + render_table(["Column", "Outlier Count"], rows, "OUTLIERS BY COLUMN"))

    # --- Insights ---
    insights = result.insights()
    if insights:
        rows = [[ins.get("severity", ""), ins.get("title", "")] for ins in insights[:10]]
        sections.append("\n" + render_table(["Severity", "Insight"], rows, "TOP INSIGHTS"))

    # --- Recommendations ---
    recs = result.recommendations()
    if recs:
        rows = [[i + 1, r] for i, r in enumerate(recs[:10])]
        sections.append("\n" + render_table(["#", "Recommendation"], rows, "RECOMMENDATIONS"))

    sections.append("\n" + "=" * 60)
    return "\n".join(sections)
