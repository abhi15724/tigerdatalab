"""End-to-end example: the full TigerDataLab workflow on tests/data/sales.csv.

Run with:
    python examples/sales_analysis.py
"""
import tigerdatalab as tdl

result = tdl.analyze("tests/data/sales.csv")

print()
print(result.summary())

print("\nTop business findings:")
for insight in result.insights()[:3]:
    print(f"[{insight['severity']}] {insight['title']}")

outputs = result.report("analysis")
print("\nGenerated files:")
for key, path in outputs.items():
    print(f"  {key}: {path}")
