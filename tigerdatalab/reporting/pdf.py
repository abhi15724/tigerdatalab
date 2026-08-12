"""Professional PDF business report using reportlab."""
from __future__ import annotations

from pathlib import Path


def build_pdf_report(path: str | Path, dataset_name: str, profile: dict, kpis: dict,
                      insights: list[dict], recommendations: list[str],
                      customer: dict | None = None, product: dict | None = None,
                      category: dict | None = None, trend: dict | None = None,
                      growth: dict | None = None, anomalies: dict | None = None) -> Path:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                     TableStyle, PageBreak)

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TDLTitle", parent=styles["Title"], textColor=colors.HexColor("#0f172a"))
    h2 = ParagraphStyle("TDLH2", parent=styles["Heading2"], textColor=colors.HexColor("#2563eb"),
                         spaceBefore=14, spaceAfter=6)
    body = styles["BodyText"]

    quality = profile.get("quality", {})
    story = []

    story.append(Paragraph("TigerDataLab Business Insights Report", title_style))
    story.append(Paragraph(f"Dataset: {dataset_name}", body))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Executive Summary", h2))
    summary_text = (
        f"This report covers {profile.get('rows', 0):,} rows across {profile.get('columns', 0)} columns, "
        f"with an overall data quality score of {quality.get('quality_score', 'N/A')}/100. "
    )
    if kpis.get("total_revenue") is not None:
        summary_text += (
            f"Total revenue of {kpis['total_revenue']:,.2f} was recorded"
            + (f" with a profit margin of {kpis.get('profit_margin_pct')}%." if kpis.get("profit_margin_pct") is not None else ".")
        )
    story.append(Paragraph(summary_text, body))

    story.append(Paragraph("Dataset Overview", h2))
    overview_data = [["Metric", "Value"],
                      ["Rows", f"{profile.get('rows', 0):,}"],
                      ["Columns", str(profile.get("columns", 0))],
                      ["Numeric columns", str(len(profile.get("numeric_columns", [])))],
                      ["Categorical columns", str(len(profile.get("categorical_columns", [])))],
                      ["Date columns", str(len(profile.get("date_columns", [])))]]
    story.append(_table(overview_data))

    story.append(Paragraph("Data Quality", h2))
    dq = [["Check", "Result"],
          ["Quality score", f"{quality.get('quality_score', 'N/A')}/100"],
          ["Missing values", str(quality.get("missing", {}).get("total_missing", 0))],
          ["Duplicate rows", str(quality.get("duplicates", {}).get("duplicate_rows", 0))],
          ["Outliers", str(quality.get("outliers", {}).get("total_outliers", 0))]]
    story.append(_table(dq))

    story.append(Paragraph("Business KPIs", h2))
    if kpis:
        kpi_data = [["KPI", "Value"]] + [[k.replace("_", " ").title(), _fmt_val(v)] for k, v in kpis.items()]
        story.append(_table(kpi_data))
    else:
        story.append(Paragraph("No business KPIs could be detected from the column names in this dataset.", body))

    if trend:
        story.append(Paragraph("Trend Analysis", h2))
        story.append(Paragraph(
            f"{trend['title']} across {len(trend['periods'])} periods "
            f"({trend['granularity']} granularity). "
            + (f"Growth from first to last period: {trend['growth_pct']}%." if trend.get('growth_pct') is not None else ""), body))

    if category and category.get("available"):
        story.append(Paragraph("Category Analysis", h2))
        rows = category.get("revenue_by_category", [])[:8]
        if rows:
            data = [["Category", "Revenue", "Share %"]] + [[r["category"], _fmt_val(r["revenue"]), f"{r['share_pct']}%"] for r in rows]
            story.append(_table(data))

    if product and product.get("available"):
        story.append(Paragraph("Product Analysis", h2))
        top = product.get("top_products_by_revenue", [])[:8]
        if top:
            data = [["Product", "Revenue"]] + [[r["product"], _fmt_val(r["revenue"])] for r in top]
            story.append(_table(data))
        if product.get("loss_making_product_count"):
            story.append(Paragraph(
                f"{product['loss_making_product_count']} products were identified as loss-making "
                "and should be reviewed for pricing or cost issues.", body))

    if customer:
        story.append(Paragraph("Customer Analysis", h2))
        story.append(Paragraph(
            f"{customer.get('unique_customers', 'N/A')} unique customers detected, with "
            f"{customer.get('repeat_customers', 'N/A')} repeat customers and "
            f"{customer.get('one_time_customers', 'N/A')} one-time customers.", body))

    if growth and (growth.get("category", {}).get("available") or growth.get("product", {}).get("available")):
        story.append(Paragraph("Growth & Decline Analysis", h2))
        for label, g in [("Category", growth.get("category", {})), ("Product", growth.get("product", {}))]:
            if not g.get("available"):
                continue
            growing = g.get("growing", [])[:5]
            declining = g.get("declining", [])[:5]
            if growing:
                story.append(Paragraph(
                    f"<b>{label} — growing:</b> " + ", ".join(f"{r['group']} ({r['change_pct']:+.1f}%)" for r in growing), body))
            if declining:
                story.append(Paragraph(
                    f"<b>{label} — declining:</b> " + ", ".join(f"{r['group']} ({r['change_pct']:+.1f}%)" for r in declining), body))

    if anomalies and anomalies.get("anomaly_count", 0) > 0:
        story.append(Paragraph("Anomaly Detection", h2))
        story.append(Paragraph(
            f"{anomalies['anomaly_count']} rows contain at least one statistically anomalous value "
            f"(|z-score| &gt; {anomalies.get('z_threshold', 3.0)}) in: "
            + ", ".join(anomalies.get("by_column", {}).keys()) + ".", body))

    story.append(PageBreak())
    story.append(Paragraph("Risk Areas & Business Opportunities", h2))
    for ins in insights:
        story.append(Paragraph(f"<b>[{ins['severity']}] {ins['title']}</b>", body))
        story.append(Paragraph(f"Evidence: {ins['evidence']}", body))
        story.append(Paragraph(f"Impact: {ins['impact']}", body))
        story.append(Paragraph(f"Recommendation: {ins['recommendation']}", body))
        story.append(Spacer(1, 8))

    story.append(Paragraph("Recommendations", h2))
    for i, rec in enumerate(recommendations, 1):
        story.append(Paragraph(f"{i}. {rec}", body))

    story.append(Paragraph("Appendix", h2))
    story.append(Paragraph("Generated automatically by TigerDataLab using deterministic, rule-based analysis. No data was transmitted externally.", body))

    from ._safe_io import write_with_fallback

    def _write(p: Path) -> None:
        doc = SimpleDocTemplate(str(p), pagesize=A4, topMargin=1.5 * cm, bottomMargin=1.5 * cm)
        doc.build(list(story))  # reportlab consumes/mutates story - use a fresh copy per attempt

    return write_with_fallback(path, _write)


def _fmt_val(v):
    if isinstance(v, float):
        return f"{v:,.2f}"
    return str(v)


def _table(data):
    from reportlab.platypus import Table, TableStyle
    from reportlab.lib import colors
    t = Table(data, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t
