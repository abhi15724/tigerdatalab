"""Finance analysis example - the workflow from the bug report.

Analyzes a finance CSV end-to-end and prints a professional summary,
mirroring what a human data analyst would hand over: KPIs, data-quality
notes, insights/recommendations, and the file paths of everything that
got generated (report, dashboard, cleaned data export).

Run with:
    python examples/finance_analysis.py path/to/finance.csv
"""
import sys

import tigerdatalab as tdl


def main(path: str) -> None:
    # verbose=True prints load/clean progress as it happens
    result = tdl.analyze(path, verbose=True)

    print(f"\nLoaded '{path}' using encoding: {result.load_meta.get('encoding')}")

    print("\n" + result.summary())

    print("\nKey Business Metrics")
    print("-" * 40)
    for k, v in result.kpis().items():
        print(f"  {k}: {v}")

    print("\nTop Insights")
    print("-" * 40)
    for insight in result.insights()[:5]:
        print(f"  [{insight['severity']}] {insight['title']}")

    print("\nRecommendations")
    print("-" * 40)
    for rec in result.recommendations()[:5]:
        print(f"  - {rec}")

    # Write out a full report bundle (HTML report, dashboard, cleaned
    # data, JSON exports) and print exactly where each file landed.
    outputs = result.report("analysis_output")
    print("\nGenerated files")
    print("-" * 40)
    for key, file_path in outputs.items():
        print(f"  {key}: {file_path.resolve()}")


if __name__ == "__main__":
    csv_path = sys.argv[1] if len(sys.argv) > 1 else "tests/data/finance.csv"
    main(csv_path)
