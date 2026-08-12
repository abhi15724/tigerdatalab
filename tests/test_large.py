import pytest

duckdb = pytest.importorskip("duckdb")

import tigerdatalab as tdl


def test_large_count_and_aggregate(large_csv_path):
    data = tdl.large(str(large_csv_path))
    assert data.count() == 50_000
    agg = data.aggregate("category", "SUM(revenue) AS revenue", "SUM(profit) AS profit")
    assert set(agg["category"]) == {"A", "B", "C"}
    assert (agg["revenue"] > 0).all()


def test_large_query_blocks_destructive_sql(large_csv_path):
    from tigerdatalab.exceptions import DestructiveSQLError
    data = tdl.large(str(large_csv_path))
    with pytest.raises(DestructiveSQLError):
        data.query("DROP TABLE data")


def test_large_sample_and_columns(large_csv_path):
    data = tdl.large(str(large_csv_path))
    assert "category" in data.columns()
    sample = data.sample(10)
    assert len(sample) == 10
