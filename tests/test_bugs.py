"""Regression tests for the specific bugs the spec calls out by name."""
import pandas as pd
import pytest

import tigerdatalab as tdl
from tigerdatalab.quality.types import detect_dtype, safe_quantile, detect_all_dtypes
from tigerdatalab.quality.profiler import outlier_report
from tigerdatalab.exceptions import EmptyDatasetError, UnsupportedFileTypeError


def test_summary_attribute_exists(csv_path):
    result = tdl.analyze(str(csv_path), verbose=False)
    assert hasattr(result, "summary")
    assert isinstance(result.summary(), str)


def test_boolean_column_never_quantiled(sales_df):
    # in_stock is a real boolean column in the fixture
    assert detect_dtype(sales_df["in_stock"]) == "boolean"
    assert safe_quantile(sales_df["in_stock"], 0.5) is None

    dtypes = detect_all_dtypes(sales_df)
    report = outlier_report(sales_df, dtypes)
    assert "in_stock" not in report["by_column"]


def test_output_paths_are_paths_not_dicts(csv_path, tmp_path):
    result = tdl.analyze(str(csv_path), verbose=False)
    outputs = result.export(tmp_path / "analysis")
    for key, path in outputs.items():
        assert hasattr(path, "exists"), f"{key} output should be a Path-like object"
        assert path.exists()


def test_messy_dates_do_not_crash(messy_df, tmp_path):
    p = tmp_path / "messy.csv"
    messy_df.to_csv(p, index=False)
    result = tdl.analyze(str(p), verbose=False)
    assert result.profile["rows"] >= 1


def test_missing_trend_does_not_crash_dashboard(no_date_df, tmp_path):
    p = tmp_path / "no_date.csv"
    no_date_df.to_csv(p, index=False)
    result = tdl.analyze(str(p), verbose=False)
    out = result.dashboard(tmp_path / "dashboard.html")
    html = out.read_text()
    assert "Not enough data" in html


def test_multiple_chart_types_present(csv_path):
    result = tdl.analyze(str(csv_path), verbose=False)
    keys = {s.key for s in result.visualize()}
    # more than "only one chart type"
    assert len({"performance_trend", "category_pie", "product_bar", "correlation_heatmap"} & keys) == 4


def test_every_chart_has_explanatory_metadata(csv_path):
    result = tdl.analyze(str(csv_path), verbose=False)
    for spec in result.visualize():
        meta = spec.to_meta()
        assert meta["title"]


def test_empty_dataset_raises_clear_error(tmp_path):
    p = tmp_path / "empty.csv"
    pd.DataFrame({"a": [], "b": []}).to_csv(p, index=False)
    with pytest.raises(EmptyDatasetError):
        tdl.analyze(str(p), verbose=False)


def test_unsupported_extension_raises_clear_error(tmp_path):
    p = tmp_path / "file.abc"
    p.write_text("nothing")
    with pytest.raises(UnsupportedFileTypeError):
        tdl.analyze(str(p), verbose=False)


def test_one_column_numeric_only_dataset(tmp_path):
    p = tmp_path / "single.csv"
    pd.DataFrame({"revenue": [1, 2, 3, 4, 5]}).to_csv(p, index=False)
    result = tdl.analyze(str(p), verbose=False)
    assert result.kpis().get("total_revenue") == 15


def test_camelcase_columns_detected_correctly(tmp_path):
    # Reproduces: a catalog-style CSV with camelCase headers (mrp,
    # discountPercent, discountedSellingPrice, name, Category ...) failed
    # to detect the plain "name" column as a product identifier, so
    # result.products() incorrectly reported "not available".
    p = tmp_path / "catalog.csv"
    p.write_text(
        "Category,name,mrp,discountPercent,discountedSellingPrice,quantity\n"
        "Snacks,Choco Bar,100,10,90,5\n"
        "Snacks,Wafer Pack,80,20,64,10\n"
        "Beverages,Cola Can,50,5,47.5,20\n"
    )
    result = tdl.analyze(str(p), verbose=False)
    assert result.semantics.get("product") == "name"
    assert result.products()["available"] is True


def test_print_table_runs_without_error(capsys):
    result = tdl.analyze("tests/data/finance.csv", verbose=False)
    result.print_table()
    captured = capsys.readouterr()
    assert "DATASET OVERVIEW" in captured.out
    assert "BUSINESS KPIs" in captured.out


def test_non_utf8_csv_does_not_crash(tmp_path):
    # Reproduces: UnicodeDecodeError: 'utf-8' codec can't decode byte 0x92
    # This happens on real-world CSVs exported from Excel/Windows, which
    # are commonly cp1252 and contain "smart quote" characters (0x91-0x94).
    p = tmp_path / "windows_export.csv"
    with open(p, "wb") as f:
        f.write("order_id,customer_name,notes,revenue\n".encode("utf-8"))
        f.write(
            ("1,O'Brien,Client said " + chr(0x2019) + "great job" + chr(0x2019)
             + " today,100.0\n").encode("cp1252")
        )
        f.write("2,Smith,ok,200.5\n".encode("utf-8"))
        f.write("3,Lee,fine,150.25\n".encode("utf-8"))

    result = tdl.analyze(str(p), verbose=False)
    assert result.profile["rows"] == 3
    assert result.load_meta["encoding"] != "utf-8"
    assert "\u2019" in result.cleaned_df["notes"].iloc[0]


def test_categorical_only_dataset(tmp_path):
    p = tmp_path / "cat_only.csv"
    pd.DataFrame({"category": ["A", "B", "A", "C"], "region": ["N", "S", "E", "W"]}).to_csv(p, index=False)
    result = tdl.analyze(str(p), verbose=False)
    assert result.profile["rows"] == 4
