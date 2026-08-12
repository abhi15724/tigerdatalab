# TigerDataLab

**TigerDataLab** is an automated Data Analytics + Data Quality + Visualization
+ Business Intelligence + DataOps layer built **on top of** pandas, numpy,
duckdb and plotly — not a replacement for them.

```python
import pandas as pd
import numpy as np           # still there when you want low-level control

import tigerdatalab as tdl

result = tdl.analyze("sales.xlsx")
print(result.summary())
result.report("analysis")     # dashboard + PDF + HTML + JSON, all in one call
```

For very large data:

```python
data = tdl.large("sales.parquet")
data.count()
data.aggregate("category", "SUM(revenue) AS revenue", "SUM(profit) AS profit")
```

## Install

```bash
pip install tigerdatalab            # core (pandas, numpy, openpyxl, plotly)
pip install "tigerdatalab[all]"     # + duckdb, pyarrow, reportlab (large data + PDF)
```

Local development:

```bash
git clone <repo>
cd tigerdatalab
pip install -e ".[all,dev]"
```

## What `analyze()` does automatically

1. Loads CSV / Excel (.xlsx, .xlsm) / JSON / Parquet / SQL / SQLite / DuckDB files.
2. Detects column data types (never runs `.quantile()` on boolean columns).
3. Detects business semantics (revenue, cost, profit, quantity, customer,
   product, category, date, discount, order, price) from column names,
   dtypes and value patterns.
4. Profiles data quality (missing values, duplicates, outliers, invalid
   dates, negative values where they shouldn't occur) into a 0–100 score.
5. Cleans conservatively (whitespace, date normalization, numeric coercion,
   duplicate removal) — every operation is logged, nothing is silently
   destroyed.
6. Calculates business KPIs (revenue, profit, margin, AOV, ASP, customers,
   orders, products, discounts).
7. Computes a performance trend (daily/monthly, MoM/YoY/rolling average)
   when a date + numeric metric pair exists — and degrades gracefully
   (never crashes) when it doesn't.
8. Runs category, product, and customer analysis (each degrades gracefully
   with a clear message if the relevant identifier column isn't present —
   it never invents numbers).
9. Generates a rule-based, evidence-backed business insight engine
   (finding → evidence → impact → recommendation), with no LLM required.
10. Builds 11 chart types (column, bar, line, pie, donut, histogram,
    scatter, box plot, heatmap, pareto, KPI cards) — each with explicit
    title/x-axis/y-axis/metric/aggregation metadata.
11. Renders a responsive, interactive Plotly dashboard, a static HTML
    report, a professional PDF business report, and JSON exports.

## Public API

```python
result = tdl.analyze("sales.xlsx")

result.summary()          # str
result.kpis()              # dict
result.quality()           # dict
result.statistics()        # dict
result.trends()            # dict
result.customers()         # dict
result.products()          # dict
result.categories()        # dict
result.insights()          # list[dict] — severity/title/evidence/impact/recommendation
result.recommendations()   # list[str]
result.visualize()         # list[ChartSpec] — 12 chart types incl. KPI Cards
result.growth()             # dict — growing/declining products & categories
result.anomalies()          # dict — z-score anomaly rows/columns
result.ask()                 # dict — answers to the standard business-question set
result.ask("which_category_generates_the_most_revenue")  # single answer

result.dashboard("analysis/dashboard.html")
result.export("analysis")   # cleaned_data.xlsx, insights/quality/statistics/kpis.json
result.report("analysis")   # export() + dashboard.html + analysis_report.html
                             #   + business_insights.pdf + charts/*.html
```

## DataOps — controlled, audited writes

```python
data = tdl.open("sales.xlsx")

data.update(where={"product_id": "SKU-1"}, values={"price": 499})
data.insert({"product_id": "SKU-99", "product": "Mouse", "price": 399})
data.delete(where={"product_id": "SKU-99"})
data.upsert({"product_id": "SKU-1", "price": 509}, key="product_id")

data.rollback()          # undo the last operation
data.save()               # write back to the original file
data.save_audit_log("analysis/audit.json")
```

`update()`/`delete()` raise a clear error (`UpdateMatchedZeroRowsError`,
`DeleteMatchedZeroRowsError`) instead of silently doing nothing.

## Large data (DuckDB-backed, lazy)

```python
data = tdl.large("large_sales.parquet")   # CSV/Parquet, no full pandas load
data.count()
data.aggregate("category", "SUM(revenue) AS revenue")
data.query("SELECT category, AVG(revenue) FROM data GROUP BY category")  # destructive SQL is refused
```

## CLI

```bash
tigerdatalab analyze sales.csv
tigerdatalab dashboard sales.csv -o analysis/dashboard.html
tigerdatalab profile sales.csv
tigerdatalab quality sales.csv
tigerdatalab clean sales.csv -o cleaned.xlsx
tigerdatalab report sales.csv -o analysis
```

## SQL files

```python
result = tdl.analyze("sales.sql")   # CREATE TABLE / INSERT INTO / SELECT
```

Executed via DuckDB (falls back to sqlite3 if duckdb isn't installed).
`DROP` / `TRUNCATE` / `DELETE` / `ALTER` are always refused — use the
DataOps API for explicit, audited writes instead.

## Privacy & security

Everything runs **locally**. TigerDataLab never uploads your data, never
calls an external API by default, and never executes arbitrary shell
commands from a dataset. The business-insight engine is fully deterministic
and rule-based — no LLM key required. An `InsightProvider` interface exists
for anyone who wants to plug in an optional LLM-backed provider later.

## Project layout

```
tigerdatalab/
├── core.py                 # AnalysisResult, analyze(), open(), large()
├── config.py
├── exceptions.py
├── io/loaders.py           # csv/excel/json/parquet/sql/sqlite/duckdb loading
├── quality/                # types.py, profiler.py, cleaning.py
├── analytics/               # kpi.py, trends.py, customer.py, product.py, category.py, profitability.py
├── insights/engine.py       # rule-based insight generation
├── visualization/charts.py  # chart engine (11 chart types)
├── dashboard/builder.py     # interactive HTML dashboard
├── reporting/               # html.py, pdf.py, exporters.py
├── dataops/asset.py         # update/insert/delete/upsert/merge/rollback/audit
├── scale/duckdb_engine.py   # lazy large-data aggregation
└── cli/main.py
```

## Testing

```bash
python -m pytest
python examples/sales_analysis.py
python examples/dataops_example.py
python examples/large_data_example.py
```

31 tests cover CSV/Excel/Parquet/SQL loading, boolean-safe type detection,
missing-date/no-trend handling, empty/one-column/categorical-only datasets,
DataOps (insert/update/delete/upsert/rollback/audit), and DuckDB large-data
aggregation.

## Publishing to PyPI

```bash
pip install build twine
python -m build
twine upload dist/*
```

## Version

3.0.0 — see `CHANGELOG.md` for the full list of fixes over the 2.2.0 prototype.
