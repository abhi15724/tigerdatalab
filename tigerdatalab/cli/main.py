"""TigerDataLab command-line interface.

    tigerdatalab analyze sales.csv
    tigerdatalab dashboard sales.csv
    tigerdatalab profile sales.csv
    tigerdatalab quality sales.csv
    tigerdatalab clean sales.csv
    tigerdatalab report sales.csv
    tigerdatalab ai-prepare data.csv --task sft --output ai_dataset
"""
from __future__ import annotations

import argparse
import sys

from .. import core
from ..exceptions import TigerDataLabError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tigerdatalab", description="TigerDataLab CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_analyze = sub.add_parser("analyze", help="Run full analysis and print summary")
    p_analyze.add_argument("path")

    p_dash = sub.add_parser("dashboard", help="Generate the interactive dashboard")
    p_dash.add_argument("path")
    p_dash.add_argument("-o", "--output", default="analysis/dashboard.html")

    p_profile = sub.add_parser("profile", help="Print a data profile")
    p_profile.add_argument("path")

    p_quality = sub.add_parser("quality", help="Print a data quality report")
    p_quality.add_argument("path")

    p_clean = sub.add_parser("clean", help="Clean and export the dataset")
    p_clean.add_argument("path")
    p_clean.add_argument("-o", "--output", default="cleaned_data.xlsx")

    p_report = sub.add_parser("report", help="Generate the full report bundle")
    p_report.add_argument("path")
    p_report.add_argument("-o", "--output", default="analysis")

    p_ai = sub.add_parser("ai-prepare", help="Prepare privacy-aware AI training data")
    p_ai.add_argument("path")
    p_ai.add_argument("--task", choices=["sft", "instruction", "dpo", "classification", "text"], default="sft")
    p_ai.add_argument("-o", "--output", default="ai_dataset")
    p_ai.add_argument("--split-strategy", choices=["hash", "positional"], default="hash")
    p_ai.add_argument("--train-ratio", type=float, default=.8)
    p_ai.add_argument("--validation-ratio", type=float, default=.1)

    args = parser.parse_args(argv)

    try:
        if args.command == "analyze":
            core.analyze(args.path, verbose=True)
        elif args.command == "dashboard":
            result = core.analyze(args.path, verbose=False)
            out = result.dashboard(args.output)
            print(f"Dashboard written to: {out}")
        elif args.command == "profile":
            import json
            print(json.dumps(core.profile(args.path), indent=2, default=str))
        elif args.command == "quality":
            import json
            print(json.dumps(core.quality_check(args.path), indent=2, default=str))
        elif args.command == "clean":
            from ..reporting.exporters import save_cleaned_excel
            df = core.clean_file(args.path)
            out = save_cleaned_excel(args.output, df)
            print(f"Cleaned data written to: {out}")
        elif args.command == "report":
            result = core.analyze(args.path, verbose=True)
            outputs = result.report(args.output)
            print("\nGenerated files:")
            for k, v in outputs.items():
                print(f"  {k}: {v}")
        elif args.command == "ai-prepare":
            from ..ai import prepare
            dataset = prepare(args.path, args.task).run()
            out = dataset.export(args.output, args.train_ratio, args.validation_ratio, args.split_strategy)
            print(f"AI dataset written to: {out}")
            print(f"Records: {len(dataset.prepared)} | Quality: {dataset.quality()['overall']}")
        return 0
    except (TigerDataLabError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
