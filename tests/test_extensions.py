"""Tests for the 3.0.0 extension pass: growth/decline, anomalies,
business-question Q&A, and the KPI-cards chart."""
import tigerdatalab as tdl


def test_growth_available_with_date_and_category(csv_path):
    result = tdl.analyze(str(csv_path), verbose=False)
    growth = result.growth()
    assert growth["category"]["available"] is True
    assert "growing" in growth["category"]
    assert "declining" in growth["category"]
    assert growth["product"]["available"] is True


def test_growth_unavailable_without_date(no_date_df, tmp_path):
    p = tmp_path / "no_date.csv"
    no_date_df.to_csv(p, index=False)
    result = tdl.analyze(str(p), verbose=False)
    growth = result.growth()
    assert growth["category"]["available"] is False
    assert "reason" in growth["category"]


def test_anomalies_return_shape(csv_path):
    result = tdl.analyze(str(csv_path), verbose=False)
    anomalies = result.anomalies()
    assert "anomaly_count" in anomalies
    assert isinstance(anomalies["anomaly_count"], int)
    assert anomalies["anomaly_count"] >= 0


def test_anomalies_never_flag_boolean_columns(sales_df, tmp_path):
    p = tmp_path / "sales.csv"
    sales_df.to_csv(p, index=False)
    result = tdl.analyze(str(p), verbose=False)
    anomalies = result.anomalies()
    assert "in_stock" not in anomalies["by_column"]


def test_business_questions_full_dict(csv_path):
    result = tdl.analyze(str(csv_path), verbose=False)
    answers = result.ask()
    assert "how_much_revenue_was_generated" in answers
    assert answers["how_much_revenue_was_generated"]["available"] is True
    assert answers["how_much_revenue_was_generated"]["answer"] > 0


def test_business_questions_single_key(csv_path):
    result = tdl.analyze(str(csv_path), verbose=False)
    answer = result.ask("which_category_generates_the_most_revenue")
    assert answer["available"] is True
    assert "category" in answer["answer"]


def test_business_questions_unknown_key(csv_path):
    result = tdl.analyze(str(csv_path), verbose=False)
    answer = result.ask("not_a_real_question")
    assert answer["available"] is False


def test_business_questions_degrade_without_customer(no_date_df, tmp_path):
    p = tmp_path / "no_cust.csv"
    no_date_df.to_csv(p, index=False)
    result = tdl.analyze(str(p), verbose=False)
    answer = result.ask("how_many_unique_customers")
    assert answer["available"] is False


def test_kpi_cards_chart_present(csv_path):
    result = tdl.analyze(str(csv_path), verbose=False)
    keys = {s.key for s in result.visualize()}
    assert "kpi_cards" in keys


def test_report_bundle_includes_growth_anomalies_questions(csv_path, tmp_path):
    result = tdl.analyze(str(csv_path), verbose=False)
    outputs = result.report(tmp_path / "analysis")
    assert outputs["growth"].exists()
    assert outputs["anomalies"].exists()
    assert outputs["business_questions"].exists()
