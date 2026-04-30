"""Convert an exported trace JSON to CSV and immediately analyze it."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from analyze_pm4py_csv import load_csv_rows, print_table, summarize_cases, summarize_scenarios
from export_pm4py_csv import DEFAULT_COLUMNS, load_rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert exported Tempo trace JSON or local trace exports to CSV and analyze them in one step."
    )
    parser.add_argument(
        "input_json",
        help="Path to exported trace JSON file, local JSONL file, or local trace export directory",
    )
    parser.add_argument(
        "output_csv",
        nargs="?",
        help="Optional output CSV path. Defaults to <input_json_stem>.pm4py.csv next to the input file.",
    )
    parser.add_argument(
        "--span-name",
        default="process-request",
        help="Only include spans with this exact name. Use --all-spans to disable filtering.",
    )
    parser.add_argument(
        "--all-spans",
        action="store_true",
        help="Export all spans instead of filtering to one span name.",
    )
    return parser.parse_args()


def resolve_output_csv(input_path: Path, output_csv: str | None) -> Path:
    if output_csv:
        return Path(output_csv)
    return input_path.with_name(f"{input_path.stem}.pm4py.csv")


def write_csv(rows: list[dict[str, object]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=DEFAULT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def analyze_csv(output_path: Path) -> None:
    rows = load_csv_rows(output_path)
    case_summary = summarize_cases(rows)
    scenario_summary = summarize_scenarios(case_summary)

    print(f"Wrote {len(rows)} rows to {output_path}")
    print("\nScenario summary")
    print("================")
    print_table(scenario_summary, ["chain_id", "runs", "completed", "failed", "failure_rate"])

    print("\nCase summary")
    print("============")
    print_table(
        case_summary,
        [
            "case:concept:name",
            "chain_id",
            "e2eux",
            "outcome",
            "event_count",
            "start_time",
            "end_time",
        ],
    )


def main() -> None:
    args = parse_args()
    input_path = Path(args.input_json)
    output_path = resolve_output_csv(input_path, args.output_csv)

    selected_span_name = None if args.all_spans else args.span_name
    rows = load_rows(input_path, selected_span_name)
    write_csv(rows, output_path)
    analyze_csv(output_path)


if __name__ == "__main__":
    main()