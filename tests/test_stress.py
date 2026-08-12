"""Stress tests: large files and messy real-world CSV quirks that a
stranger's dataset is likely to contain but which weren't covered by the
curated tests/data/ fixtures.
"""
import numpy as np
import pandas as pd
import pytest

import tigerdatalab as tdl


def test_analyze_handles_500k_rows(tmp_path):
    rng = np.random.default_rng(7)
    n = 500_000
    df = pd.DataFrame({
        "order_id": [f"ORD-{i}" for i in range(n)],
        "order_date": pd.date_range("2023-01-01", periods=n, freq="min"),
        "customer_id": rng.integers(1, 5000, size=n),
        "category": rng.choice(["A", "B", "C", "D"], size=n),
        "quantity": rng.integers(1, 20, size=n),
        "revenue": rng.uniform(10, 1000, size=n).round(2),
        "cost": rng.uniform(5, 800, size=n).round(2),
    })
    p = tmp_path / "large.csv"
    df.to_csv(p, index=False)

    result = tdl.analyze(str(p), verbose=False)
    assert result.profile["rows"] == n
    assert result.kpis()["total_revenue"] > 0
    assert result.kpis()["orders"] == n


def test_infinite_values_do_not_corrupt_kpis(tmp_path):
    # Reproduces: inf + -inf = NaN silently corrupted the ENTIRE revenue
    # total with no indication anything was wrong.
    p = tmp_path / "inf.csv"
    pd.DataFrame({
        "category": ["A", "B", "A", "B", "A"],
        "revenue": [100.0, np.inf, -np.inf, 400.0, 50.0],
        "quantity": [1, 2, 3, 4, 5],
    }).to_csv(p, index=False)

    result = tdl.analyze(str(p), verbose=False)
    kpis = result.kpis()
    assert not pd.isna(kpis["total_revenue"])
    assert kpis["total_revenue"] == pytest.approx(550.0)
    # the two infinite cells should be visible as missing, not swept away
    assert result.quality()["missing"]["by_column"].get("revenue", 0) == 2


def test_ragged_rows_are_skipped_not_fatal(tmp_path):
    # Reproduces: one row with an extra stray field made the C parser
    # raise ParserError and abort loading the ENTIRE file.
    p = tmp_path / "ragged.csv"
    p.write_text(
        "category,revenue,quantity\n"
        "A,100,1\n"
        "B,200,2\n"
        "C,300,3,extra_unexpected_field\n"
    )
    result = tdl.analyze(str(p), verbose=False)
    assert result.profile["rows"] == 2  # the malformed 3rd row is dropped
    assert "skipped" in result.load_meta["encoding"]
    assert result.kpis()["total_revenue"] == pytest.approx(300.0)


def test_all_null_column_does_not_crash(tmp_path):
    p = tmp_path / "allnull.csv"
    pd.DataFrame({
        "category": ["A", "B", "A", "B"],
        "revenue": [100.0, 200.0, 150.0, 300.0],
        "notes": [None, None, None, None],
    }).to_csv(p, index=False)
    result = tdl.analyze(str(p), verbose=False)
    assert result.profile["rows"] == 4


def test_single_row_dataset(tmp_path):
    p = tmp_path / "single.csv"
    pd.DataFrame({"category": ["A"], "revenue": [100.0]}).to_csv(p, index=False)
    result = tdl.analyze(str(p), verbose=False)
    assert result.profile["rows"] == 1
    assert result.kpis()["total_revenue"] == 100.0


def test_wide_dataframe_many_columns(tmp_path):
    wide = pd.DataFrame(
        np.random.rand(20, 300),
        columns=[f"col_{i}" for i in range(300)],
    )
    wide["category"] = ["A"] * 10 + ["B"] * 10
    p = tmp_path / "wide.csv"
    wide.to_csv(p, index=False)
    result = tdl.analyze(str(p), verbose=False)
    assert result.profile["columns"] == 301


def test_non_latin_and_emoji_text_preserved(tmp_path):
    p = tmp_path / "unicode.csv"
    pd.DataFrame({
        "category": ["电子产品", "électronique", "\U0001F600 Snacks"],
        "revenue": [10.0, 20.0, 30.0],
    }).to_csv(p, index=False, encoding="utf-8")
    result = tdl.analyze(str(p), verbose=False)
    assert list(result.cleaned_df["category"]) == ["电子产品", "électronique", "\U0001F600 Snacks"]


def test_duplicate_column_names_do_not_crash(tmp_path):
    p = tmp_path / "dupcols.csv"
    p.write_text("revenue,revenue,category\n1,2,A\n4,5,B\n")
    result = tdl.analyze(str(p), verbose=False)
    assert result.profile["columns"] == 3
