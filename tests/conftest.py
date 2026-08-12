import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def sales_df():
    rng = np.random.default_rng(42)
    n = 300
    dates = pd.date_range("2024-01-01", periods=n, freq="D")
    categories = rng.choice(["Electronics", "Grocery", "Apparel", "Home"], size=n, p=[0.5, 0.2, 0.2, 0.1])
    products = rng.choice([f"SKU-{i}" for i in range(1, 21)], size=n)
    customers = rng.choice([f"CUST-{i}" for i in range(1, 61)], size=n)
    quantity = rng.integers(1, 10, size=n)
    unit_price = rng.uniform(50, 500, size=n).round(2)
    revenue = quantity * unit_price
    cost = revenue * rng.uniform(0.5, 0.95, size=n)
    discount_pct = rng.uniform(0, 25, size=n).round(2)
    in_stock = rng.choice([True, False], size=n)

    return pd.DataFrame({
        "order_id": [f"ORD-{i}" for i in range(1, n + 1)],
        "order_date": dates,
        "customer_id": customers,
        "product_id": products,
        "category": categories,
        "quantity": quantity,
        "unit_price": unit_price,
        "revenue": revenue.round(2),
        "cost": cost.round(2),
        "discount_pct": discount_pct,
        "in_stock": in_stock,
    })


@pytest.fixture
def messy_df():
    return pd.DataFrame({
        "order_id": [1, 2, 2, 3, 4, None],
        "order_date": ["2024-01-01", "01/02/2024", "not-a-date", "2024-01-04", None, "2024-01-06"],
        "category": [" Electronics ", "Grocery", "Electronics", None, "Apparel", "Apparel"],
        "revenue": ["100", "200.5", None, "abc", "150", "-50"],
        "is_active": [True, False, True, True, False, None],
    })


@pytest.fixture
def no_date_df():
    return pd.DataFrame({
        "category": ["A", "B", "A", "C", "B"],
        "revenue": [100, 200, 150, 300, 250],
    })


@pytest.fixture
def csv_path(tmp_path, sales_df):
    p = tmp_path / "sales.csv"
    sales_df.to_csv(p, index=False)
    return p


@pytest.fixture
def parquet_path(tmp_path, sales_df):
    p = tmp_path / "sales.parquet"
    sales_df.to_parquet(p, index=False)
    return p


@pytest.fixture
def xlsx_path(tmp_path, sales_df):
    p = tmp_path / "sales.xlsx"
    sales_df.to_excel(p, index=False, engine="openpyxl")
    return p


@pytest.fixture
def json_path(tmp_path, sales_df):
    p = tmp_path / "sales.json"
    # orient="records" is the natural shape for a row-per-record dataset,
    # and what pd.read_json defaults to reading back.
    sales_df.to_json(p, orient="records", date_format="iso")
    return p


@pytest.fixture
def sqlite_path(tmp_path, sales_df):
    import sqlite3
    p = tmp_path / "sales.sqlite"
    con = sqlite3.connect(str(p))
    sales_df.to_sql("sales", con, index=False)
    con.close()
    return p


@pytest.fixture
def sql_file_path(tmp_path, sales_df):
    # A .sql file TigerDataLab can execute standalone: a CREATE + INSERTs
    # + a final SELECT, mirroring what a colleague would hand-write or
    # export from a DB tool.
    p = tmp_path / "sales.sql"
    cols = ["order_id", "customer_id", "product_id", "category", "quantity",
            "unit_price", "revenue", "cost", "discount_pct"]
    lines = [
        "CREATE TABLE sales (order_id TEXT, customer_id TEXT, product_id TEXT, "
        "category TEXT, quantity INTEGER, unit_price REAL, revenue REAL, "
        "cost REAL, discount_pct REAL);"
    ]
    for _, row in sales_df.head(50).iterrows():
        vals = ", ".join(
            f"'{row[c]}'" if isinstance(row[c], str) else str(row[c])
            for c in cols
        )
        lines.append(f"INSERT INTO sales ({', '.join(cols)}) VALUES ({vals});")
    lines.append("SELECT * FROM sales;")
    p.write_text("\n".join(lines))
    return p


@pytest.fixture
def duckdb_path(tmp_path, sales_df):
    import duckdb
    p = tmp_path / "sales.duckdb"
    con = duckdb.connect(str(p))
    con.execute("CREATE TABLE sales AS SELECT * FROM sales_df")
    con.close()
    return p


@pytest.fixture
def large_csv_path(tmp_path):
    rng = np.random.default_rng(1)
    n = 50_000
    df = pd.DataFrame({
        "category": rng.choice(["A", "B", "C"], size=n),
        "revenue": rng.uniform(10, 1000, size=n).round(2),
        "profit": rng.uniform(-50, 500, size=n).round(2),
    })
    p = tmp_path / "large.csv"
    df.to_csv(p, index=False)
    return p
