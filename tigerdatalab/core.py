"""Core orchestration: tdl.analyze() and the AnalysisResult object.

This module ties together IO, semantics, quality, analytics, insights,
visualization, dashboard, and reporting into the simple public API:

    result = tdl.analyze("sales.xlsx")
    print(result.summary())
    result.report("analysis")
    result.dashboard("analysis/dashboard")
"""
from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from .config import __version__
from .exceptions import EmptyDatasetError, NoTrendDataError, NoCustomerIdentifierError
from .io.loaders import load
from .quality.types import detect_all_dtypes, detect_semantics
from .quality.profiler import full_profile
from .quality.cleaning import clean
from .analytics.kpi import calculate_kpis
from .analytics.trends import compute_trend
from .analytics.customer import analyze_customers
from .analytics.product import analyze_products
from .analytics.category import analyze_categories
from .analytics.profitability import ensure_profit_column
from .analytics.growth import analyze_growth
from .quality.anomalies import detect_anomalies
from .insights.engine import generate_insights, generate_recommendations, RuleBasedInsightProvider
from .insights.questions import answer_business_questions
from .visualization.charts import build_charts
from .dashboard.builder import build_dashboard_html, save_dashboard
from .reporting.html import build_html_report, save_html_report
from .reporting.pdf import build_pdf_report
from .reporting.exporters import save_json, save_cleaned_excel

logger = logging.getLogger("tigerdatalab")


class AnalysisResult:
    """Holds everything computed by tdl.analyze() and exposes the public,
    self-explanatory result API (summary/kpis/quality/insights/etc.)."""

    def __init__(self, df: pd.DataFrame, source: str, load_meta: dict, insight_provider=None):
        self.source = source
        self.load_meta = load_meta
        self._insight_provider = insight_provider or RuleBasedInsightProvider()

        if df.empty:
            raise EmptyDatasetError()

        self.raw_df = df
        self.dtypes = detect_all_dtypes(df)
        semantics = detect_semantics(df, self.dtypes)
        df2, semantics, profit_derived = ensure_profit_column(df, semantics)
        self.semantics = semantics
        self.profit_derived = profit_derived

        self.cleaned_df, self.cleaning_log = clean(df2, semantics)
        self.profile = full_profile(self.cleaned_df, semantics)
        self._kpis = calculate_kpis(self.cleaned_df, semantics)

        try:
            self._trend = compute_trend(self.cleaned_df, semantics)
        except NoTrendDataError:
            self._trend = None

        self._category = analyze_categories(self.cleaned_df, semantics)
        self._product = analyze_products(self.cleaned_df, semantics)

        try:
            self._customer = analyze_customers(self.cleaned_df, semantics)
        except NoCustomerIdentifierError:
            self._customer = None

        self._growth = analyze_growth(self.cleaned_df, semantics)
        self._anomalies = detect_anomalies(self.cleaned_df, self.dtypes)

        context = {
            "kpis": self._kpis, "quality": self.profile["quality"],
            "category": self._category, "product": self._product,
            "trend": self._trend, "customer": self._customer,
        }
        self._insights = generate_insights(context, self._insight_provider)
        self._recommendations = generate_recommendations(self._insights)

        self._business_questions = answer_business_questions(
            self._kpis, self._category, self._product, self._customer,
            self._growth, self.profile["quality"],
        )

        self._chart_specs = build_charts(self.cleaned_df, semantics, self._trend, self._category, self._kpis)

    # ---------------- public result API ----------------

    def summary(self) -> str:
        q = self.profile["quality"]
        lines = [
            "TigerDataLab Analysis Summary",
            "=" * 40,
            f"Dataset: {self.source}",
            f"Rows: {self.profile['rows']:,}",
            f"Columns: {self.profile['columns']}",
            f"Memory: {self.profile['memory_bytes'] / 1024:.1f} KB",
            f"Missing values: {q['missing']['total_missing']:,}",
            f"Duplicate rows: {q['duplicates']['duplicate_rows']:,}",
            f"Numeric columns: {len(self.profile['numeric_columns'])}",
            f"Categorical columns: {len(self.profile['categorical_columns'])}",
            f"Date columns: {len(self.profile['date_columns'])}",
            f"Data quality score: {q['quality_score']}/100",
        ]
        if self._kpis:
            lines.append("")
            lines.append("Business KPIs")
            lines.append("-" * 40)
            for k, v in self._kpis.items():
                label = k.replace("_", " ").title()
                if isinstance(v, float):
                    lines.append(f"{label}: {v:,.2f}")
                else:
                    lines.append(f"{label}: {v}")
        return "\n".join(lines)

    def kpis(self) -> dict:
        return self._kpis

    def quality(self) -> dict:
        return self.profile["quality"]

    def statistics(self) -> dict:
        numeric_cols = self.profile["numeric_columns"]
        stats = {}
        for col in numeric_cols:
            s = pd.to_numeric(self.cleaned_df[col], errors="coerce").dropna()
            if s.empty:
                continue
            stats[col] = {
                "mean": float(s.mean()), "median": float(s.median()),
                "std": float(s.std()) if len(s) > 1 else 0.0,
                "min": float(s.min()), "max": float(s.max()),
                "q1": float(s.quantile(0.25)), "q3": float(s.quantile(0.75)),
            }
        return stats

    def trends(self) -> dict:
        if self._trend is None:
            return {"available": False, "message": "No valid datetime + numeric pair found."}
        return {"available": True, **self._trend}

    def customers(self) -> dict:
        if self._customer is None:
            return {"available": False, "message": "Customer-level analysis is unavailable because no customer identifier was detected."}
        return {"available": True, **self._customer}

    def products(self) -> dict:
        return self._product

    def categories(self) -> dict:
        return self._category

    def growth(self) -> dict:
        """Growth/decline tagging per product and category (first-half vs
        second-half of the date range). Degrades gracefully when no date
        column exists."""
        return self._growth

    def anomalies(self) -> dict:
        """Z-score based anomaly detection across numeric business columns."""
        return self._anomalies

    def ask(self, question_key: str | None = None) -> dict:
        """Deterministic answers to the standard business-question set
        (see README). Call with no argument to get every answer as a dict,
        or pass a key like 'which_category_generates_the_most_revenue'."""
        if question_key is None:
            return self._business_questions
        if question_key not in self._business_questions:
            return {"available": False, "answer": None,
                     "reason": f"Unknown question key '{question_key}'. "
                                f"See result.ask() for the full list of keys."}
        return self._business_questions[question_key]

    def insights(self) -> list[dict]:
        return self._insights

    def recommendations(self) -> list[str]:
        return self._recommendations

    def semantic_map(self) -> dict:
        return self.semantics

    def visualize(self):
        """Return the list of ChartSpec objects (title/x/y/metric/aggregation + Plotly figure)."""
        return self._chart_specs

    # ---------------- output generation ----------------

    def dashboard(self, path: str | Path = "analysis/dashboard.html") -> Path:
        path = Path(path)
        if path.suffix.lower() != ".html":
            path = path / "dashboard.html"
        html = build_dashboard_html(self.source, self.profile, self._kpis, self._insights, self._chart_specs)
        return save_dashboard(path, html)

    def export(self, directory: str | Path = "analysis") -> dict:
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        outputs = {}
        outputs["cleaned_data"] = save_cleaned_excel(directory / "cleaned_data.xlsx", self.cleaned_df)
        outputs["insights"] = save_json(directory / "insights.json", {"insights": self._insights, "recommendations": self._recommendations})
        outputs["quality"] = save_json(directory / "quality.json", self.profile["quality"])
        outputs["statistics"] = save_json(directory / "statistics.json", self.statistics())
        outputs["kpis"] = save_json(directory / "kpis.json", self._kpis)
        outputs["growth"] = save_json(directory / "growth.json", self._growth)
        outputs["anomalies"] = save_json(directory / "anomalies.json", self._anomalies)
        outputs["business_questions"] = save_json(directory / "business_questions.json", self._business_questions)
        return outputs

    def report(self, directory: str | Path = "analysis") -> dict:
        """Generate the full output bundle: dashboard, HTML report, PDF
        report, JSON exports, cleaned data, and charts/ directory."""
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        charts_dir = directory / "charts"
        charts_dir.mkdir(parents=True, exist_ok=True)

        outputs = self.export(directory)

        outputs["dashboard"] = self.dashboard(directory / "dashboard.html")

        html_report = build_html_report(self.source, self.profile, self._kpis, self._insights)
        outputs["html_report"] = save_html_report(directory / "analysis_report.html", html_report)

        try:
            outputs["pdf_report"] = build_pdf_report(
                directory / "business_insights.pdf", self.source, self.profile, self._kpis,
                self._insights, self._recommendations, self._customer, self._product,
                self._category, self._trend, self._growth, self._anomalies,
            )
        except ImportError:
            logger.warning("reportlab is not installed; skipping PDF report. Install with: pip install reportlab")

        for spec in self._chart_specs:
            import plotly.io as pio
            chart_path = charts_dir / f"{spec.key}.html"
            pio.write_html(spec.fig, str(chart_path), include_plotlyjs="cdn", config={"responsive": True})
        outputs["charts_dir"] = charts_dir

        return outputs

    def print_terminal_summary(self) -> None:
        print(self.summary())

    def print_table(self) -> None:
        """Print the full analysis as clean, bordered ASCII tables -
        dataset overview, KPIs, category/product breakdowns, data-quality
        outliers, insights, and recommendations."""
        from .reporting.terminal import render_terminal_report
        print(render_terminal_report(self))

    def table(self) -> str:
        """Same content as print_table(), returned as a string instead of printed."""
        from .reporting.terminal import render_terminal_report
        return render_terminal_report(self)

    def __repr__(self):
        return f"<AnalysisResult source='{self.source}' rows={self.profile['rows']} cols={self.profile['columns']}>"


def analyze(path: str | Path, insight_provider=None, verbose: bool = True) -> AnalysisResult:
    """Load, profile, clean, and analyze a dataset in one call."""
    df, meta = load(path)
    result = AnalysisResult(df, source=str(path), load_meta=meta, insight_provider=insight_provider)
    if verbose:
        result.print_table()
    return result


def open(path: str | Path):
    """Open a dataset for controlled DataOps modification (update/insert/delete/upsert/rollback/save)."""
    from .dataops.asset import open_asset
    return open_asset(path)


def large(path: str | Path):
    """Open a large dataset (CSV/Parquet) for lazy, DuckDB-backed aggregation."""
    from .scale.duckdb_engine import LargeDataAsset
    return LargeDataAsset(path)


def profile(path: str | Path) -> dict:
    """Quick profile-only entry point (no full analysis)."""
    df, _ = load(path)
    if df.empty:
        raise EmptyDatasetError()
    dtypes = detect_all_dtypes(df)
    semantics = detect_semantics(df, dtypes)
    return full_profile(df, semantics)


def quality_check(path: str | Path) -> dict:
    df, _ = load(path)
    if df.empty:
        raise EmptyDatasetError()
    dtypes = detect_all_dtypes(df)
    semantics = detect_semantics(df, dtypes)
    from .quality.profiler import quality_score
    return quality_score(df, semantics, dtypes)


def clean_file(path: str | Path) -> pd.DataFrame:
    df, _ = load(path)
    dtypes = detect_all_dtypes(df)
    semantics = detect_semantics(df, dtypes)
    cleaned, _log = clean(df, semantics)
    return cleaned
