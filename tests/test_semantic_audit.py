"""Audit of the semantic-keyword detector (tigerdatalab.quality.types.detect_semantics).

Two things are tested here:
1. Common real-world column-name variants (abbreviations, alternate
   phrasing) that a stranger's dataset is likely to use actually resolve
   to the right business concept.
2. Column names that LOOK related but aren't (e.g. "job_title" is not a
   product, "payment_type" is not a product category) do NOT get
   mis-tagged - false positives are just as dangerous as missed detections.
"""
import pandas as pd

from tigerdatalab.quality.types import detect_semantics, detect_all_dtypes


def _semantics_for(columns_and_values: dict) -> dict:
    df = pd.DataFrame(columns_and_values)
    dtypes = detect_all_dtypes(df)
    return detect_semantics(df, dtypes)


def test_revenue_aliases_detected():
    for col in ["sale_amount", "total_amount", "order_value", "order_total",
                "net_amount", "gross_sales", "sales_value", "revenue"]:
        sem = _semantics_for({col: [10.0, 20.0, 30.0], "other": ["a", "b", "c"]})
        assert sem.get("revenue") == col, f"'{col}' should be detected as revenue"


def test_cost_aliases_detected():
    for col in ["cost_amount", "buying_price", "purchase_price", "cogs_amount", "unit_cost"]:
        sem = _semantics_for({col: [5.0, 6.0, 7.0], "other": ["a", "b", "c"]})
        assert sem.get("cost") == col, f"'{col}' should be detected as cost"


def test_customer_aliases_detected():
    for col in ["cust_id", "member_id", "account_id", "customer_name", "client_name"]:
        sem = _semantics_for({col: ["A", "B", "C"], "revenue": [1.0, 2.0, 3.0]})
        assert sem.get("customer") == col, f"'{col}' should be detected as customer"


def test_order_id_aliases_detected():
    for col in ["order_number", "txn_id", "receipt_no", "receipt_id", "bill_no", "bill_id"]:
        sem = _semantics_for({col: ["1", "2", "3"], "revenue": [1.0, 2.0, 3.0]})
        assert sem.get("order") == col, f"'{col}' should be detected as order"


def test_category_aliases_detected():
    for col in ["sub_category", "subcategory"]:
        sem = _semantics_for({col: ["A", "B", "A"], "revenue": [1.0, 2.0, 3.0]})
        assert sem.get("category") == col, f"'{col}' should be detected as category"


def test_product_group_resolves_to_category_when_product_already_claimed():
    # "product_group" contains "product", so on its own it's claimed by the
    # (higher-priority) product concept - which is correct, since a column
    # literally named "product_group" IS product-ish. Only once a stronger
    # product column exists elsewhere does it fall through to category.
    sem = _semantics_for({
        "name": ["Widget A", "Widget B", "Widget C"],
        "product_group": ["Hardware", "Hardware", "Software"],
        "revenue": [1.0, 2.0, 3.0],
    })
    assert sem.get("product") == "name"
    assert sem.get("category") == "product_group"


def test_price_aliases_detected():
    for col in ["list_price", "retail_price", "sale_price"]:
        sem = _semantics_for({col: [9.99, 19.99, 29.99], "other": ["a", "b", "c"]})
        assert sem.get("price") == col, f"'{col}' should be detected as price"


# --- false-positive guards: ambiguous names that should NOT be mis-tagged ---

def test_job_title_is_not_tagged_as_product():
    sem = _semantics_for({
        "employee_id": ["E1", "E2", "E3"],
        "job_title": ["Engineer", "Manager", "Analyst"],
        "salary": [50000, 60000, 70000],
    })
    assert sem.get("product") != "job_title"


def test_payment_type_is_not_tagged_as_category():
    sem = _semantics_for({
        "payment_type": ["Card", "Cash", "UPI"],
        "revenue": [100.0, 200.0, 300.0],
    })
    # "payment_type" contains none of the category keywords - it must not
    # be picked up as the product/segment category column.
    assert sem.get("category") != "payment_type"


def test_customer_name_claimed_by_customer_not_product():
    # "customer_name" should resolve to the customer concept (checked
    # earlier in SEMANTIC_PRIORITY), not leak through to product, since
    # "name" is now a product keyword and could otherwise collide.
    sem = _semantics_for({
        "customer_name": ["Alice", "Bob", "Carol"],
        "revenue": [100.0, 200.0, 300.0],
    })
    assert sem.get("customer") == "customer_name"
    assert sem.get("product") != "customer_name"
