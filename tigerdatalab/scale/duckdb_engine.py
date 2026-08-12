"""Lazy, DuckDB-backed access for large datasets (millions+ rows).

Avoids `pd.read_csv(huge_file)` when the user only needs an aggregate:
the engine keeps everything in DuckDB and only materializes pandas
DataFrames for the (typically small) query results.
"""
from __future__ import annotations

from pathlib import Path


class LargeDataAsset:
    """Wraps a CSV/Parquet/SQL source via DuckDB for lazy, pushdown-friendly
    querying without loading the full dataset into pandas."""

    def __init__(self, path: str | Path):
        try:
            import duckdb
        except ImportError as e:
            raise ImportError(
                "The 'duckdb' package is required for tdl.large(). "
                "Install it with: pip install duckdb"
            ) from e

        self.path = Path(path)
        self._con = duckdb.connect(database=":memory:")
        ext = self.path.suffix.lower()

        if ext == ".csv":
            self._con.execute(
                f"CREATE VIEW data AS SELECT * FROM read_csv_auto('{self.path.as_posix()}')"
            )
        elif ext == ".parquet":
            self._con.execute(
                f"CREATE VIEW data AS SELECT * FROM read_parquet('{self.path.as_posix()}')"
            )
        elif ext in (".xlsx", ".xlsm"):
            import pandas as pd
            df = pd.read_excel(self.path, engine="openpyxl")
            self._con.register("data", df)
        else:
            raise ValueError(
                f"tdl.large() supports .csv and .parquet (and .xlsx via in-memory load) — got '{ext}'."
            )

    def count(self) -> int:
        return int(self._con.execute("SELECT COUNT(*) FROM data").fetchone()[0])

    def columns(self) -> list[str]:
        return [r[0] for r in self._con.execute("DESCRIBE data").fetchall()]

    def aggregate(self, group_by: str, *agg_exprs: str, where: str | None = None,
                  order_by: str | None = None, limit: int | None = None):
        """Run a lazy GROUP BY aggregation entirely inside DuckDB.

        Example:
            data.aggregate("category", "SUM(revenue) AS revenue", "SUM(profit) AS profit")
        """
        exprs = ", ".join(agg_exprs) if agg_exprs else "COUNT(*) AS n"
        sql = f"SELECT {group_by}, {exprs} FROM data"
        if where:
            sql += f" WHERE {where}"
        sql += f" GROUP BY {group_by}"
        if order_by:
            sql += f" ORDER BY {order_by}"
        if limit:
            sql += f" LIMIT {limit}"
        return self._con.execute(sql).fetchdf()

    def query(self, sql: str):
        """Run an arbitrary read-only SQL query against the `data` view."""
        from ..config import DESTRUCTIVE_SQL_KEYWORDS
        first_word = sql.strip().split()[0].upper() if sql.strip() else ""
        if first_word in DESTRUCTIVE_SQL_KEYWORDS:
            from ..exceptions import DestructiveSQLError
            raise DestructiveSQLError(first_word)
        return self._con.execute(sql).fetchdf()

    def sample(self, n: int = 1000):
        return self._con.execute(f"SELECT * FROM data LIMIT {n}").fetchdf()

    def to_pandas(self, limit: int | None = None):
        sql = "SELECT * FROM data"
        if limit:
            sql += f" LIMIT {limit}"
        return self._con.execute(sql).fetchdf()

    def close(self):
        self._con.close()

    def __repr__(self):
        try:
            n = self.count()
        except Exception:
            n = "?"
        return f"<LargeDataAsset path='{self.path}' rows={n}>"
