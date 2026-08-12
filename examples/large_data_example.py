"""Large-data example: DuckDB-backed lazy aggregation, no full pandas load."""
import tigerdatalab as tdl

data = tdl.large("tests/data/large.csv")
print(f"Row count (lazy): {data.count():,}")

agg = data.aggregate("category", "SUM(revenue) AS revenue", "SUM(profit) AS profit", order_by="revenue DESC")
print(agg)
