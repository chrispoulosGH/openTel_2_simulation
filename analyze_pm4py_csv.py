"""Summarize scenario outcomes from a PM4PY-ready CSV export."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze a PM4PY-ready CSV exported from OpenTelemetry traces."
    )
    parser.add_argument("input_csv", help="Path to the PM4PY-ready CSV file")
    return parser.parse_args()


def load_csv_rows(input_path: Path) -> list[dict[str, str]]:
    with input_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    rows.sort(key=lambda row: (row["case:concept:name"], row["time:timestamp"], row["concept:name"]))
    return rows


def summarize_cases(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    """Reduce events to one row per trace with scenario and outcome information."""
    cases: dict[str, dict[str, object]] = {}
    for row in rows:
        trace_id = row["case:concept:name"]
        case = cases.setdefault(
            trace_id,
            {
                "case:concept:name": trace_id,
                "chain_id": row.get("chain_id", ""),
                "e2eux": row.get("E2EUX", ""),
                "start_time": row.get("time:timestamp", ""),
                "end_time": row.get("time:timestamp", ""),
                "event_count": 0,
                "has_error": False,
            },
        )
        if not case["chain_id"] and row.get("chain_id"):
            case["chain_id"] = row.get("chain_id", "")
        if not case["e2eux"] and row.get("E2EUX"):
            case["e2eux"] = row.get("E2EUX", "")
        case["event_count"] += 1
        timestamp = row.get("time:timestamp", "")
        if timestamp and (not case["start_time"] or timestamp < case["start_time"]):
            case["start_time"] = timestamp
        if timestamp and (not case["end_time"] or timestamp > case["end_time"]):
            case["end_time"] = timestamp
        if row.get("status") == "ERROR":
            case["has_error"] = True

    case_summary = []
    for case in cases.values():
        case["outcome"] = "failed" if case["has_error"] else "completed"
        case_summary.append(case)
    case_summary.sort(key=lambda item: (item["chain_id"], item["start_time"], item["case:concept:name"]))
    return case_summary


def summarize_scenarios(case_summary: list[dict[str, object]]) -> list[dict[str, object]]:
    """Compute completion metrics by scenario id."""
    scenarios: dict[str, dict[str, object]] = {}
    for case in case_summary:
        chain_id = str(case.get("chain_id", ""))
        summary = scenarios.setdefault(
            chain_id,
            {"chain_id": chain_id, "runs": 0, "completed": 0, "failed": 0},
        )
        summary["runs"] += 1
        if case.get("outcome") == "completed":
            summary["completed"] += 1
        else:
            summary["failed"] += 1

    scenario_summary = []
    for summary in scenarios.values():
        runs = int(summary["runs"])
        failed = int(summary["failed"])
        summary["failure_rate"] = round(failed / runs, 3) if runs else 0.0
        scenario_summary.append(summary)
    scenario_summary.sort(key=lambda item: item["chain_id"])
    return scenario_summary


def print_table(rows: list[dict[str, object]], columns: list[str]) -> None:
    if not rows:
        print("(no rows)")
        return

    widths = {
        column: max(len(column), max(len(str(row.get(column, ""))) for row in rows))
        for column in columns
    }
    header = " ".join(column.ljust(widths[column]) for column in columns)
    divider = " ".join("=" * widths[column] for column in columns)
    print(header)
    print(divider)
    for row in rows:
        print(" ".join(str(row.get(column, "")).ljust(widths[column]) for column in columns))


def main() -> None:
    args = parse_args()
    input_path = Path(args.input_csv)

    rows = load_csv_rows(input_path)
    case_summary = summarize_cases(rows)
    scenario_summary = summarize_scenarios(case_summary)

    print("Scenario summary")
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


if __name__ == "__main__":
    main()