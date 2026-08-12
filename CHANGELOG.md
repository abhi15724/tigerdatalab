# Changelog

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
- Fixed: a plain `name` column (the most common header for a product name
  in catalog-style datasets) was never recognized as a product identifier,
  so `result.products()` incorrectly reported "not available" even when
  the data clearly had product names.
- Added: `result.print_table()` / `result.table()` - renders the full
  analysis (dataset overview, KPIs, category/product breakdowns, outliers,
  insights, recommendations) as clean bordered ASCII tables. `tdl.analyze(
  ..., verbose=True)` (the default) now prints this table report instead
  of the old plain-text summary.
- Note: KPIs like Revenue/Profit/Customers legitimately show as
  unavailable for datasets that have no revenue, cost, customer, or date
  columns (e.g. a product-catalog export) - this is correct behavior, not
  a bug, since that data isn't present in the file.

## 3.0.1
- Fixed: `tdl.analyze()` crashed with `UnicodeDecodeError: 'utf-8' codec
  can't decode byte 0x92 ...` on any CSV that wasn't strictly UTF-8 encoded
  (very common for CSVs exported from Excel/Windows, which use cp1252 and
  contain "smart quote" characters). `load()` now tries UTF-8 first, then
  auto-detects the encoding via `charset-normalizer`, then falls back
  through `cp1252` and `latin-1` before giving up. The encoding actually
  used is recorded in `result.load_meta["encoding"]`.
- Added `charset-normalizer` as a required dependency to support the above.

## 3.0.0 (extended)
- Added: z-score anomaly detection (`result.anomalies()`), distinct from the
  IQR-based per-column outlier report — flags rows whose numeric metrics are
  statistically unusual rather than just columns with a wide spread.
- Added: growth/decline detection per product and category
  (`result.growth()`), splitting the date range in half and tagging each
  group as growing/declining/flat; degrades gracefully with no date column.
- Added: deterministic business-question Q&A layer (`result.ask()`),
  answering the full question set from the spec (top product/category by
  revenue/profit, AOV, discount-vs-margin, growing/declining
  products/categories, etc.) directly from already-computed KPIs/analytics.
- Added: KPI Cards as a true 12th chart type (Plotly indicator grid),
  alongside the existing HTML KPI grid at the top of the dashboard.
- Added: a category dropdown filter on the "Revenue by Category" chart.
- Extended the PDF report with Growth & Decline and Anomaly Detection
  sections.
- `report()`/`export()` now also write `growth.json`, `anomalies.json`,
  and `business_questions.json`.
- 10 new tests (41 total) covering all of the above.

## 3.0.0
- Full architectural rebuild from the 2.2.0 prototype into a modular package
  (io/, quality/, analytics/, insights/, visualization/, dashboard/,
  reporting/, dataops/, scale/, cli/).
- Fixed: `AnalysisResult.summary()` AttributeError.
- Fixed: boolean columns no longer passed into `.quantile()`.
- Fixed: date detection no longer blindly parses every column; uses
  name-hint + parse-success-ratio heuristics with `format="mixed"`.
- Fixed: Performance Trend no longer crashes when no date/numeric pair
  exists — raises a clear, catchable error and the dashboard still renders
  a "not enough data" placeholder instead of crashing.
- Added: multi chart-type engine (column, bar, line, pie, donut, histogram,
  scatter, box plot, heatmap, pareto) with explicit title/x-axis/y-axis/
  metric/aggregation metadata on every chart.
- Added: rule-based business insight engine (evidence + impact +
  recommendation), no LLM required, with an `InsightProvider` interface for
  optional future LLM backends.
- Added: DataOps (`tdl.open()`) with update/insert/delete/upsert/merge,
  audit log, rollback, and zero-rows-matched safety checks.
- Added: `tdl.large()` DuckDB-backed lazy aggregation for large CSV/Parquet.
- Added: SQL file support (CREATE/INSERT/SELECT) via DuckDB with a
  destructive-statement guard (DROP/TRUNCATE/DELETE/ALTER refused).
- Added: CLI (`tigerdatalab analyze|dashboard|profile|quality|clean|report`).
- Added: PDF business report (reportlab) and HTML report generation.

## 2.2.0
- Initial prototype: core.py, viz.py, report.py.
