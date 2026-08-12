"""Static HTML analysis report (separate from the interactive dashboard)."""
from __future__ import annotations

from pathlib import Path


def build_html_report(dataset_name: str, profile: dict, kpis: dict, insights: list[dict]) -> str:
    quality = profile.get("quality", {})
    kpi_rows = "".join(f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in kpis.items())
    insight_rows = "".join(
        f"<tr><td>{i['severity']}</td><td>{i['title']}</td><td>{i['evidence']}</td>"
        f"<td>{i['impact']}</td><td>{i['recommendation']}</td></tr>"
        for i in insights
    )
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"/><title>TigerDataLab Report — {dataset_name}</title>
<style>
body{{font-family:Arial,sans-serif;margin:32px;color:#0f172a}}
h1{{margin-bottom:0}} h2{{border-bottom:2px solid #2563eb;padding-bottom:6px;margin-top:32px}}
table{{border-collapse:collapse;width:100%;margin-top:12px}}
td,th{{border:1px solid #e2e8f0;padding:8px;text-align:left;font-size:13px}}
th{{background:#f1f5f9}}
</style></head><body>
<h1>TigerDataLab Analysis Report</h1>
<p>Dataset: {dataset_name}</p>
<h2>Dataset Overview</h2>
<table><tr><th>Metric</th><th>Value</th></tr>
<tr><td>Rows</td><td>{profile.get('rows',0):,}</td></tr>
<tr><td>Columns</td><td>{profile.get('columns',0)}</td></tr>
<tr><td>Memory</td><td>{profile.get('memory_bytes',0)/1024:.1f} KB</td></tr>
<tr><td>Data Quality Score</td><td>{quality.get('quality_score','N/A')}/100</td></tr>
<tr><td>Missing Values</td><td>{quality.get('missing',{}).get('total_missing',0)}</td></tr>
<tr><td>Duplicate Rows</td><td>{quality.get('duplicates',{}).get('duplicate_rows',0)}</td></tr>
</table>
<h2>Business KPIs</h2>
<table><tr><th>KPI</th><th>Value</th></tr>{kpi_rows}</table>
<h2>Business Insights</h2>
<table><tr><th>Severity</th><th>Title</th><th>Evidence</th><th>Impact</th><th>Recommendation</th></tr>{insight_rows}</table>
</body></html>"""


def save_html_report(path: str | Path, html: str) -> Path:
    from ._safe_io import write_with_fallback
    return write_with_fallback(path, lambda p: p.write_text(html, encoding="utf-8"))
