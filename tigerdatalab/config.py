"""Global configuration and constants for TigerDataLab."""
from __future__ import annotations

__version__ = "3.0.4"

SUPPORTED_EXTENSIONS = [".csv", ".xlsx", ".xlsm", ".json", ".parquet", ".sql", ".db", ".sqlite", ".duckdb"]

# Row-count thresholds used to decide small / medium / large execution strategy.
SMALL_DATA_ROW_LIMIT = 100_000
MEDIUM_DATA_ROW_LIMIT = 5_000_000

# SQL keywords that TigerDataLab will never auto-execute.
DESTRUCTIVE_SQL_KEYWORDS = ["DROP", "TRUNCATE", "DELETE", "ALTER"]

# Semantic keyword dictionaries used by the column-semantics detector.
# Each business concept maps to a list of substrings matched against
# lower-cased, underscore/space-normalized column names.
SEMANTIC_KEYWORDS: dict[str, list[str]] = {
    "revenue": ["revenue", "sales_amount", "sales", "amount", "gmv", "turnover",
                "net_sales", "total_sales", "grand_total", "line_total",
                "sale_amount", "total_amount", "order_value", "order_total",
                "net_amount", "gross_sales", "sales_value"],
    "profit": ["profit", "net_profit", "gross_profit", "profit_amount", "margin_amount",
               "net_income", "earnings", "profit_value"],
    "cost": ["cost", "cogs", "cost_price", "purchase_cost", "unit_cost",
             "cost_amount", "buying_price", "purchase_price", "cogs_amount"],
    "quantity": ["quantity", "qty", "units", "units_sold", "unit_count",
                 "qty_sold", "no_of_units", "units_purchased", "order_qty"],
    "customer": ["customer_id", "customer", "buyer_id", "buyer", "client_id", "user_id",
                 "cust_id", "member_id", "account_id", "customer_name", "client_name"],
    "product": ["product_id", "product_name", "product", "item", "sku", "item_name", "name",
                "product_title", "item_code", "product_code"],
    "category": ["category", "segment", "department", "product_category", "product_type",
                 "sub_category", "subcategory", "product_group"],
    "date": ["date", "order_date", "transaction_date", "created_at", "timestamp", "order_time",
             "invoice_date", "order_dt", "txn_date", "purchase_date", "created_date", "datetime"],
    "discount": ["discount_pct", "discount_percent", "discount", "disc_pct", "disc_percent"],
    "order": ["order_id", "transaction_id", "invoice_id", "invoice_no", "order_no",
              "order_number", "txn_id", "receipt_no", "receipt_id", "bill_no", "bill_id"],
    "price": ["unit_price", "selling_price", "price", "rate", "mrp", "list_price",
              "retail_price", "sale_price"],
}

# Keys checked in priority order (more specific first) to avoid, e.g.,
# "cost_price" being tagged as "price" instead of "cost".
SEMANTIC_PRIORITY = ["order", "customer", "product", "category", "date",
                      "discount", "cost", "profit", "revenue", "quantity", "price"]
