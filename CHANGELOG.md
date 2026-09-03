# Changelog

## 4.1.1
- Fixed FastAPI deployment request handling that could incorrectly return HTTP 422 for `/v1/ask` and protected endpoints.
- Fixed authentication handling so missing or invalid API keys return the intended HTTP 401 response instead of validation errors.
- Preserved request auditing and rate-limit behavior for deployment endpoints.
- Optimized GitHub Actions CI to avoid installing heavyweight AI training dependencies for the standard test matrix.
- Added pip dependency caching to speed up CI and release validation.
- Optimized the PyPI publishing workflow to use the same lightweight test dependencies.
- Changed PyPI publishing to run only for published GitHub Releases, preventing an ordinary `pyproject.toml` version bump from publishing accidentally.
- Preserved backward-compatible public APIs.

## 4.0.0
- Added the unified `TigerDataLab` Data-to-AI platform facade for Data Analytics, Data Science, Data Engineering, AI Training and Company AI workflow applications.
- Added `DataPipeline` for deterministic, testable ETL transformations and pipeline manifests.
- Added `DataScience` helpers for dataset profiling, reproducible train/test splitting and numeric correlation analysis.
- Added `AIProject` for model-agnostic training dataset preparation and compatible training backends.
- Added `CompanyAIProject` for company knowledge, RAG, provider/model connection and workflow-oriented AI applications.
- Expanded the AI data layer with SFT, DPO, instruction, classification and text dataset preparation, PII masking, deduplication, schema validation, quality reporting, deterministic splits and lineage.
- Added multi-provider adapters, RAG, model routing, evaluation, allow-listed tools and workflow primitives.
- Improved deterministic lexical RAG retrieval with stop-word filtering and basic English morphology normalization.
- Added comprehensive role-based documentation for analysts, data scientists, data engineers, AI engineers and Company AI builders.
- Added GitHub Actions Trusted Publishing workflow for PyPI releases with test, build and distribution validation gates.
- Preserved the existing analytics, DataOps, CLI and public APIs for backward compatibility.

## 3.0.4
- Fixed: `result.report()` / `result.export()` crashed with a raw
  `PermissionError: [Errno 13] Permission denied` if any output file
  (most commonly `cleaned_data.xlsx`) was already open in Excel, or
  briefly locked by a cloud-sync tool (OneDrive/Dropbox/Google Drive) -
  a very common situation for anyone re-running an analysis on a file
  path under a synced folder. Every file writer (Excel, JSON, HTML
  dashboard/report, PDF) now retries briefly, then falls back to a
  timestamped filename and warns clearly, instead of losing the entire
  report bundle over one locked file.

## 3.0.3 - robustness audit
Response to a "can other analysts use this on their own data" review:

- Semantic keyword audit: expanded the revenue/cost/customer/order/category/
  price keyword lists with common real-world aliases (`cust_id`,
  `order_number`, `sub_category`, `list_price`, `buying_price`, etc.), with
  tests proving both the new aliases resolve correctly AND that ambiguous
  look-alike columns (`job_title`, `payment_type`) do NOT get mis-tagged.
- Fixed: `+inf`/`-inf` values in numeric columns silently corrupted whole
  KPI totals via `inf + -inf = NaN`, with no indication anything was
  wrong. They're now treated as invalid/missing (same as any other bad
  value), logged, and reflected honestly in the missing-value count.
- Fixed: a single malformed CSV row (wrong field count - e.g. a stray
  extra comma from a manual edit) crashed the ENTIRE file load with a raw
  `ParserError`. Malformed rows are now skipped and the count is reported
  in `result.load_meta`, instead of losing the whole dataset.
- Added test coverage for every previously-untested loader: JSON, `.sql`
  files, SQLite/`.db`, and DuckDB (all now exercised end-to-end via
  `tdl.analyze()`, not just unit-level).
- Added stress tests: 500K-row CSV (~4s, correct KPIs), all-null columns,
  single-row datasets, 300-column-wide data, duplicate column names, and
  non-Latin/emoji text - none of these crashed, but they're now locked in
  as regression tests.
- Added a GitHub Actions CI workflow (`.github/workflows/ci.yml`) running
  the full test suite on Python 3.10/3.11/3.12 on every push/PR - only
  takes effect once this repo is pushed to GitHub.
- Test suite: 44 -> 67 tests, all passing.
- Still not covered: exhaustive fuzz-testing of the semantic keyword list
  (only common aliases were audited, not an exhaustive list), non-English
  column names, and files above ~500K rows / multi-GB scale.

## 3.0.2
- Fixed: column-name normalization lower-cased headers before splitting
  words, so camelCase headers (e.g. `discountedSellingPrice`,
  `discountPercent` - very common in API-sourced/export CSVs) matched
  semantic keywords poorly or not at all. Words are now split at camelCase
  boundaries first, then normalized, giving much better concept detection
  on real-world files.
- Fixed: a plain `name` column (the most common header for a product name in
  catalog-style datasets) was never recognized as a product identifier, so
  `result.products()` incorrectly reported "not available" even when the
  data clearly had product names.
- Added: `result.print_table()` / `result.table()` - renders the full
  analysis (dataset overview, KPIs, category/product breakdowns, outliers,
  insights, recommendations) as clean bordered ASCII tables. `tdl.analyze(
  ..., verbose=True)` (the default) now prints this table report instead
  of the old plain-text summary.
- Note: KPIs like Revenue/Profit/Customers legitimately show as unavailable
  for datasets that have no revenue, cost, customer, or date columns.

## 3.0.1
- Fixed: `tdl.analyze()` crashed with `UnicodeDecodeError` on CSV files using
  common Windows/Excel encodings such as cp1252. Loader encoding detection
  now tries UTF-8, charset-normalizer, cp1252 and latin-1.
- Added `charset-normalizer` as a required dependency.

## 3.0.0 (extended)
- Added z-score anomaly detection, growth/decline detection, deterministic
  business-question Q&A, KPI Cards, category filtering and expanded PDF/
  JSON report exports.

## 3.0.0
- Full architectural rebuild from the 2.2.0 prototype into a modular package.
- Added multi-chart visualization, rule-based business insights, DataOps,
  DuckDB-backed large-data processing, SQL file support, CLI and PDF/HTML
  reporting.

## 2.2.0
- Initial prototype: core.py, viz.py, report.py.
