"""Coverage for the loaders that had no dedicated tests: JSON, .sql files,
SQLite/.db, and DuckDB. CSV/Excel/Parquet were already covered in
test_core.py - this file closes that gap so every SUPPORTED_EXTENSIONS
entry has at least one test exercising the full tdl.analyze() path.
"""
import pytest

import tigerdatalab as tdl
from tigerdatalab.exceptions import TigerDataLabError


def test_analyze_json(json_path):
    result = tdl.analyze(str(json_path), verbose=False)
    assert result.profile["rows"] > 0
    assert result.load_meta["format"] == "json"
    # semantics should still be detected the same as for the equivalent CSV
    assert result.semantics.get("revenue") == "revenue"
    assert result.semantics.get("customer") == "customer_id"


def test_analyze_sqlite_db(sqlite_path):
    result = tdl.analyze(str(sqlite_path), verbose=False)
    assert result.profile["rows"] > 0
    assert result.load_meta["format"] == "sqlite"
    assert result.load_meta["table"] == "sales"
    assert "revenue" in result.kpis() or "total_revenue" in result.kpis()


def test_analyze_sql_file(sql_file_path):
    result = tdl.analyze(str(sql_file_path), verbose=False)
    assert result.profile["rows"] == 50
    assert result.load_meta["format"] == "sql"
    assert result.semantics.get("category") == "category"


def test_analyze_duckdb_file(duckdb_path):
    result = tdl.analyze(str(duckdb_path), verbose=False)
    assert result.profile["rows"] > 0
    assert result.load_meta["format"] == "duckdb"
    assert result.load_meta["table"] == "sales"


def test_sql_file_rejects_destructive_statements(tmp_path):
    p = tmp_path / "bad.sql"
    p.write_text("DROP TABLE sales; SELECT 1;")
    with pytest.raises(TigerDataLabError):
        tdl.analyze(str(p), verbose=False)
