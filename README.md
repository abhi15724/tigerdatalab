# TigerDataLab

**TigerDataLab** is an automated **Data Analytics + Data Quality + Visualization + Business Intelligence + DataOps + AI Training Data** platform built on top of pandas, NumPy, DuckDB and Plotly. It complements these libraries rather than replacing them.

> **Analyze. Clean. Understand. Prepare AI Data.**

## Quick start

```python
import tigerdatalab as tdl

result = tdl.analyze("sales.xlsx")
print(result.summary())
result.report("analysis")  # dashboard + HTML + PDF + JSON exports
```

For large datasets:

```python
data = tdl.large("sales.parquet")
data.count()
data.aggregate("category", "SUM(revenue) AS revenue", "SUM(profit) AS profit")
```

## Installation

```bash
pip install tigerdatalab

# Large-data + PDF features
pip install "tigerdatalab[all]"
```

For local development:

```bash
git clone https://github.com/abhi15724/tigerdatalab.git
cd tigerdatalab
pip install -e ".[all,dev]"
```

## What `analyze()` does

TigerDataLab turns a raw business dataset into an analysis-ready reporting bundle through a deterministic, local pipeline.

1. Loads CSV, Excel (`.xlsx`, `.xlsm`), JSON, Parquet, SQL, SQLite and DuckDB data.
2. Detects column types safely, including boolean-safe profiling.
3. Detects business semantics such as revenue, cost, profit, quantity, customer, product, category, date, discount, order and price.
4. Profiles missing values, duplicates, outliers, invalid dates and suspicious negative values into a quality score.
5. Cleans conservatively with logged transformations; data is not silently destroyed.
6. Calculates business KPIs including revenue, profit, margin, AOV, ASP, customers, orders, products and discounts.
7. Calculates trends when suitable date and metric columns exist, while degrading gracefully when they do not.
8. Performs category, product and customer analysis without inventing unavailable metrics.
9. Generates deterministic, evidence-backed insights: **finding → evidence → impact → recommendation**.
10. Generates chart specifications with explicit title, axis, metric and aggregation metadata.
11. Produces interactive Plotly dashboards, HTML reports, PDF reports and JSON exports.

## AI training-data layer

TigerDataLab also provides a local training-data preparation layer for common machine-learning and LLM dataset workflows.

Supported preparation workflows include:

- **SFT / instruction datasets**
- **Chat / conversational datasets**
- **DPO / preference datasets**
- **Classification datasets**
- **Text datasets**
- Training-data validation and schema checks
- Deterministic duplicate detection and removal
- PII detection and masking
- Dataset quality statistics
- Label/distribution analysis
- Deterministic train/validation/test splitting
- Dataset lineage and dataset cards
- JSONL training-data export

The pipeline is designed to run locally and does not require an LLM API key.

Example concept:

```python
from tigerdatalab.ai import AIDataset

rows = [
    {"prompt": "Explain revenue", "response": "Revenue is income generated from sales."},
    {"prompt": "What is AOV?", "response": "Average Order Value measures revenue per order."},
]

dataset = AIDataset(rows, "sft").run()
print(dataset.stats)
dataset.export("training_data")
```

PII-aware preparation can mask sensitive values such as email addresses and phone numbers before training-data export.

## Public API

```python
result = tdl.analyze("sales.xlsx")

result.summary()          # str
result.kpis()             # dict
result.quality()          # dict
result.statistics()       # dict
result.trends()           # dict
result.customers()        # dict
result.products()         # dict
result.categories()       # dict
result.insights()         # list[dict]
result.recommendations()  # list[str]
result.visualize()        # list[ChartSpec]
result.growth()           # dict
result.anomalies()        # dict
result.ask()              # standard business-question answers
result.ask("which_category_generates_the_most_revenue")

result.dashboard("analysis/dashboard.html")
result.export("analysis")
result.report("analysis")
```

## DataOps — controlled and audited writes

```python
data = tdl.open("sales.xlsx")

data.update(where={"product_id": "SKU-1"}, values={"price": 499})
data.insert({"product_id": "SKU-99", "product": "Mouse", "price": 399})
data.delete(where={"product_id": "SKU-99"})
data.upsert({"product_id": "SKU-1", "price": 509}, key="product_id")

data.rollback()
data.save()
data.save_audit_log("analysis/audit.json")
```

`update()` and `delete()` raise explicit errors when zero rows match instead of silently doing nothing.

## Large data — DuckDB-backed and lazy

```python
data = tdl.large("large_sales.parquet")
data.count()
data.aggregate("category", "SUM(revenue) AS revenue")
data.query("SELECT category, AVG(revenue) FROM data GROUP BY category")
```

Destructive SQL is refused by the large-data query layer.

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
result = tdl.analyze("sales.sql")
```

SQL analysis supports safe `CREATE TABLE`, `INSERT INTO` and `SELECT` workflows through DuckDB, with sqlite fallback when DuckDB is unavailable. Destructive statements such as `DROP`, `TRUNCATE`, `DELETE` and `ALTER` are refused in the SQL-analysis path; use DataOps for explicit audited writes.

## Privacy and security

TigerDataLab is designed for local processing:

- Your datasets are not uploaded by the library.
- No external AI API is required by default.
- Dataset contents are not sent to an LLM for the rule-based analytics engine.
- Arbitrary shell commands are not executed from dataset contents.
- AI training-data preparation, validation, masking and splitting can run locally.
- Optional AI/LLM integrations can be provided through extension interfaces rather than being required by the core package.

## Project layout

```text
tigerdatalab/
├── core.py                 # AnalysisResult, analyze(), open(), large()
├── config.py
├── exceptions.py
├── io/loaders.py           # CSV/Excel/JSON/Parquet/SQL/SQLite/DuckDB loading
├── quality/                # profiling and conservative cleaning
├── analytics/              # KPI, trend, customer, product, category analytics
├── insights/               # deterministic business insight engine
├── visualization/          # chart specifications and rendering
├── dashboard/              # interactive dashboard builder
├── reporting/              # HTML, PDF and export functionality
├── dataops/                # controlled writes, rollback and audit logging
├── scale/                  # DuckDB-backed large-data operations
├── ai/                     # AI training-data preparation and validation
└── cli/                    # command-line interface
```

## Testing

Run the complete test suite with:

```bash
python -m pytest -v
```

The repository includes coverage for AI training-data adapters and validation, PII masking, deduplication, deterministic splitting/export, core analytics, loaders, DataOps, SQL safety, dashboards, reporting and large-data/stress scenarios.

## Continuous integration and PyPI publishing

TigerDataLab uses GitHub Actions for automated testing, packaging and PyPI publishing.

```text
GitHub Release
      ↓
Tests (Python 3.10–3.13)
      ↓
Build wheel + source distribution
      ↓
Twine metadata validation
      ↓
PyPI Trusted Publishing (OIDC)
      ↓
PyPI
```

Publishing is handled by the repository's GitHub Actions workflow. PyPI Trusted Publishing is used instead of storing a long-lived PyPI API token in GitHub secrets.

For maintainers who need a local package build:

```bash
python -m pip install build twine
python -m build
python -m twine check dist/*
```

## Version

**3.0.6**

See [`CHANGELOG.md`](CHANGELOG.md) for release history.

## Links

- **GitHub:** https://github.com/abhi15724/tigerdatalab
- **PyPI:** https://pypi.org/project/tigerdatalab/

## License

MIT License.
