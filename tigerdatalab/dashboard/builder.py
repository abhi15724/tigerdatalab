"""Interactive, responsive HTML dashboard builder (Plotly-based)."""
from __future__ import annotations

from pathlib import Path

import plotly.io as pio


def _kpi_card(label: str, value: str) -> str:
    return f"""
    <div class="kpi-card">
      <div class="kpi-label">{label}</div>
      <div class="kpi-value">{value}</div>
    </div>"""


def _fmt(v, prefix="", suffix="", decimals=0):
    if v is None:
        return "N/A"
    try:
        return f"{prefix}{v:,.{decimals}f}{suffix}"
    except (TypeError, ValueError):
        return str(v)


def build_dashboard_html(dataset_name: str, profile: dict, kpis: dict,
                          insights: list[dict], chart_specs: list) -> str:
    quality = profile.get("quality", {})

    kpi_cards = "".join([
        _kpi_card("Revenue", _fmt(kpis.get("total_revenue"), prefix="₹", decimals=0)),
        _kpi_card("Profit", _fmt(kpis.get("total_profit"), prefix="₹", decimals=0)),
        _kpi_card("Profit Margin", _fmt(kpis.get("profit_margin_pct"), suffix="%", decimals=2)),
        _kpi_card("Orders", _fmt(kpis.get("orders"), decimals=0)),
        _kpi_card("Customers", _fmt(kpis.get("customers"), decimals=0)),
        _kpi_card("Quantity", _fmt(kpis.get("total_quantity"), decimals=0)),
    ])

    chart_blocks = []
    for spec in chart_specs:
        chart_html = pio.to_html(spec.fig, include_plotlyjs=False, full_html=False,
                                  config={"responsive": True, "displaylogo": False})
        meta_bits = []
        if spec.x_axis:
            meta_bits.append(f"X-axis: {spec.x_axis}")
        if spec.y_axis:
            meta_bits.append(f"Y-axis: {spec.y_axis}")
        if spec.metric:
            meta_bits.append(f"Metric: {spec.metric}")
        if spec.aggregation:
            meta_bits.append(f"Aggregation: {spec.aggregation}")
        meta_line = " &middot; ".join(meta_bits)
        chart_blocks.append(f"""
        <div class="chart-card">
          <div class="chart-title">{spec.title}</div>
          {f'<div class="chart-meta">{meta_line}</div>' if meta_line else ''}
          {chart_html}
        </div>""")

    severity_colors = {"HIGH": "#dc2626", "MEDIUM": "#f59e0b", "LOW": "#16a34a"}
    insight_blocks = []
    for ins in insights:
        color = severity_colors.get(ins["severity"], "#64748b")
        insight_blocks.append(f"""
        <div class="insight-card" style="border-left-color:{color}">
          <div class="insight-header">
            <span class="badge" style="background:{color}">{ins['severity']}</span>
            <span class="insight-title">{ins['title']}</span>
          </div>
          <div class="insight-row"><b>Evidence:</b> {ins['evidence']}</div>
          <div class="insight-row"><b>Impact:</b> {ins['impact']}</div>
          <div class="insight-row"><b>Recommendation:</b> {ins['recommendation']}</div>
        </div>""")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>TigerDataLab Dashboard — {dataset_name}</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
  :root {{
    --bg:#f8fafc; --card:#ffffff; --text:#0f172a; --muted:#64748b; --accent:#2563eb; --border:#e2e8f0;
  }}
  * {{ box-sizing: border-box; }}
  body {{ margin:0; font-family: -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
          background: var(--bg); color: var(--text); }}
  header {{ background: linear-gradient(135deg, #0f172a, #1e293b); color: white; padding: 28px 32px; }}
  header h1 {{ margin:0; font-size: 22px; }}
  header p {{ margin: 4px 0 0; color:#cbd5e1; font-size: 13px; }}
  .section {{ padding: 24px 32px; }}
  .section h2 {{ font-size: 15px; text-transform: uppercase; letter-spacing: .06em; color: var(--muted);
                 margin: 0 0 14px; border-bottom: 1px solid var(--border); padding-bottom: 8px; }}
  .kpi-grid {{ display:grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 14px; }}
  .kpi-card {{ background: var(--card); border:1px solid var(--border); border-radius: 12px; padding: 16px; }}
  .kpi-label {{ font-size:12px; color: var(--muted); text-transform: uppercase; letter-spacing:.04em; }}
  .kpi-value {{ font-size: 22px; font-weight: 700; margin-top: 6px; color: var(--text); }}
  .chart-grid {{ display:grid; grid-template-columns: repeat(auto-fit, minmax(420px, 1fr)); gap: 18px; }}
  .chart-card {{ background: var(--card); border:1px solid var(--border); border-radius: 12px; padding: 14px; }}
  .chart-title {{ font-weight: 600; font-size: 14px; margin-bottom: 2px; }}
  .chart-meta {{ font-size: 11px; color: var(--muted); margin-bottom: 6px; }}
  .insight-card {{ background: var(--card); border:1px solid var(--border); border-left: 5px solid #ccc;
                    border-radius: 10px; padding: 14px 16px; margin-bottom: 12px; }}
  .insight-header {{ display:flex; align-items:center; gap:10px; margin-bottom: 8px; }}
  .badge {{ color:white; font-size: 11px; font-weight:700; padding: 2px 8px; border-radius: 999px; }}
  .insight-title {{ font-weight: 700; font-size: 14px; }}
  .insight-row {{ font-size: 13px; color:#334155; margin-top: 4px; line-height:1.5; }}
  footer {{ text-align:center; color: var(--muted); font-size:12px; padding: 24px; }}
  @media (max-width: 640px) {{
    .section {{ padding: 16px; }}
    header {{ padding: 20px; }}
  }}
</style>
</head>
<body>
<header>
  <h1>TigerDataLab Interactive Dashboard</h1>
  <p>Dataset: {dataset_name} &middot; Rows: {profile.get('rows', 0):,} &middot; Columns: {profile.get('columns', 0)} &middot; Data Quality: {quality.get('quality_score', 'N/A')}%</p>
</header>

<div class="section">
  <h2>Key Performance Indicators</h2>
  <div class="kpi-grid">{kpi_cards}</div>
</div>

<div class="section">
  <h2>Charts &amp; Analysis</h2>
  <div class="chart-grid">{''.join(chart_blocks)}</div>
</div>

<div class="section">
  <h2>Business Insights &amp; Recommendations</h2>
  {''.join(insight_blocks)}
</div>

<footer>Generated by TigerDataLab &middot; All analysis performed locally.</footer>
</body>
</html>"""
    return html


def save_dashboard(path: str | Path, html: str) -> Path:
    from ..reporting._safe_io import write_with_fallback
    return write_with_fallback(path, lambda p: p.write_text(html, encoding="utf-8"))
