"""DataOps example: controlled update/insert/delete/upsert with audit + rollback."""
import tigerdatalab as tdl

data = tdl.open("tests/data/sales.csv")
print(f"Loaded {len(data)} rows")

data.insert({"order_id": "ORD-DEMO", "product_id": "SKU-1", "category": "Electronics", "revenue": 999.0})
data.update(where={"order_id": "ORD-DEMO"}, values={"revenue": 1099.0})
data.upsert({"order_id": "ORD-DEMO", "revenue": 1199.0}, key="order_id")
data.delete(where={"order_id": "ORD-DEMO"})

print(f"Final row count: {len(data)}")
data.save("examples_output/sales_modified.csv")
data.save_audit_log("examples_output/audit.json")
print("Audit log entries:", len(data.audit_log))
