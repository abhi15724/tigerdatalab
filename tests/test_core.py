import json

import tigerdatalab as tdl


def test_analyze_csv_summary_works(csv_path):
    result = tdl.analyze(str(csv_path), verbose=False)
    text = result.summary()
    assert "Rows:" in text
    assert "Data quality score" in text


def test_analyze_xlsx(xlsx_path):
    result = tdl.analyze(str(xlsx_path), verbose=False)
    assert result.profile["rows"] > 0


def test_analyze_parquet(parquet_path):
    result = tdl.analyze(str(parquet_path), verbose=False)
    assert result.profile["rows"] > 0


def test_kpis_detected(csv_path):
    result = tdl.analyze(str(csv_path), verbose=False)
    kpis = result.kpis()
    assert "total_revenue" in kpis
    assert kpis["total_revenue"] > 0
    assert "orders" in kpis
    assert "customers" in kpis


def test_quality_report(csv_path):
    result = tdl.analyze(str(csv_path), verbose=False)
    q = result.quality()
    assert 0 <= q["quality_score"] <= 100


def test_trends_available(csv_path):
    result = tdl.analyze(str(csv_path), verbose=False)
    trend = result.trends()
    assert trend["available"] is True
    assert len(trend["periods"]) > 0


def test_trends_unavailable_gracefully(no_date_df, tmp_path):
    p = tmp_path / "no_date.csv"
    no_date_df.to_csv(p, index=False)
    result = tdl.analyze(str(p), verbose=False)
    trend = result.trends()
    assert trend["available"] is False
    assert "message" in trend


def test_insights_have_required_fields(csv_path):
    result = tdl.analyze(str(csv_path), verbose=False)
    insights = result.insights()
    assert len(insights) > 0
    for ins in insights:
        for key in ("severity", "title", "evidence", "impact", "recommendation"):
            assert key in ins


def test_dashboard_generates_and_contains_data(csv_path, tmp_path):
    result = tdl.analyze(str(csv_path), verbose=False)
    out = result.dashboard(tmp_path / "dashboard.html")
    assert out.exists()
    html = out.read_text()
    assert "Key Performance Indicators" in html
    assert "plotly" in html.lower()
    assert len(html) > 5000  # not an empty shell


def test_full_report_bundle(csv_path, tmp_path):
    result = tdl.analyze(str(csv_path), verbose=False)
    outputs = result.report(tmp_path / "analysis")
    assert outputs["dashboard"].exists()
    assert outputs["html_report"].exists()
    assert outputs["kpis"].exists()
    assert outputs["quality"].exists()
    assert outputs["insights"].exists()
    assert outputs["cleaned_data"].exists()
    charts = list(outputs["charts_dir"].glob("*.html"))
    assert len(charts) >= 5

    kpi_data = json.loads(outputs["kpis"].read_text())
    assert "total_revenue" in kpi_data


def test_customer_analysis(csv_path):
    result = tdl.analyze(str(csv_path), verbose=False)
    cust = result.customers()
    assert cust["available"] is True
    assert cust["unique_customers"] > 0


def test_customer_analysis_unavailable_when_no_id(no_date_df, tmp_path):
    p = tmp_path / "noid.csv"
    no_date_df.to_csv(p, index=False)
    result = tdl.analyze(str(p), verbose=False)
    cust = result.customers()
    assert cust["available"] is False


def test_visualize_returns_multiple_chart_types(csv_path):
    result = tdl.analyze(str(csv_path), verbose=False)
    specs = result.visualize()
    keys = {s.key for s in specs}
    assert "performance_trend" in keys
    assert "category_pie" in keys
    assert "category_donut" in keys
    assert "correlation_heatmap" in keys
    assert "boxplot" in keys
    assert len(specs) >= 8
