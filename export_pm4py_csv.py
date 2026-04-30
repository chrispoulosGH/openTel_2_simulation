"""Convert exported OpenTelemetry trace JSON into a PM4PY-ready CSV."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_COLUMNS = [
    "case:concept:name",
    "concept:name",
    "time:timestamp",
    "E2EUX",
    "chain_id",
    "service.name",
    "span_id",
    "parent_span_id",
    "span_name",
    "span_kind",
    "status",
    "status_code",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert exported Tempo trace JSON or local trace exports into a PM4PY-ready CSV."
    )
    parser.add_argument(
        "input_json",
        help="Path to exported trace JSON file, local JSONL file, or local trace export directory",
    )
    parser.add_argument("output_csv", help="Path to output CSV file")
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


def attribute_value(value_obj: dict) -> object:
    for key in (
        "stringValue",
        "intValue",
        "doubleValue",
        "boolValue",
    ):
        if key in value_obj:
            return value_obj[key]
    return None


def attribute_map(attributes: list[dict] | None) -> dict[str, object]:
    mapped = {}
    for item in attributes or []:
        key = item.get("key")
        if key:
            mapped[key] = attribute_value(item.get("value", {}))
    return mapped


def nano_to_iso8601(value: int | str | None) -> str:
    if value is None:
        return ""
    timestamp = datetime.fromtimestamp(int(value) / 1_000_000_000, tz=timezone.utc)
    return timestamp.isoformat().replace("+00:00", "Z")


def status_label(status_code: object) -> str:
    if status_code == 1:
        return "OK"
    if status_code == 2:
        return "ERROR"
    return "UNSET"


def build_row(
    service_name: str,
    span: dict,
    span_attrs: dict[str, object],
) -> dict[str, object]:
    return {
        "case:concept:name": span.get("traceId", ""),
        "concept:name": f"{service_name}:{span.get('name', '')}",
        "time:timestamp": nano_to_iso8601(span.get("startTimeUnixNano")),
        "E2EUX": span_attrs.get("E2EUX", span_attrs.get("business_process_flow", "")),
        "chain_id": span_attrs.get("chain_id", ""),
        "service.name": service_name,
        "span_id": span.get("spanId", ""),
        "parent_span_id": span.get("parentSpanId", ""),
        "span_name": span.get("name", ""),
        "span_kind": span.get("kind", ""),
        "status": status_label(span.get("status", {}).get("code", "")),
        "status_code": span.get("status", {}).get("code", ""),
    }


def iter_rows_from_tempo_payload(payload: dict, span_name: str | None) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for batch in payload.get("batches", []):
        resource_attrs = attribute_map(batch.get("resource", {}).get("attributes", []))
        service_name = resource_attrs.get("service.name", "unknown")

        for library_spans in batch.get("instrumentationLibrarySpans", []):
            for span in library_spans.get("spans", []):
                if span_name is not None and span.get("name") != span_name:
                    continue

                span_attrs = attribute_map(span.get("attributes", []))
                rows.append(build_row(service_name, span, span_attrs))
    rows.sort(key=lambda row: (row["case:concept:name"], row["time:timestamp"], row["concept:name"]))
    return rows


def local_trace_files(input_path: Path) -> list[Path]:
    if input_path.is_dir():
        spans_dir = input_path / "spans"
        search_root = spans_dir if spans_dir.exists() else input_path
        return sorted(search_root.rglob("*.jsonl"))
    return [input_path]


def iter_rows_from_local_exports(input_path: Path, span_name: str | None) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for jsonl_path in local_trace_files(input_path):
        with jsonl_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                span = json.loads(line)
                if span.get("__format__") != "otel-sim-local-span-v1":
                    continue
                if span_name is not None and span.get("name") != span_name:
                    continue
                resource_attrs = span.get("resource_attributes", {})
                service_name = resource_attrs.get("service.name", "unknown")
                span_attrs = span.get("attributes", {})
                rows.append(build_row(service_name, span, span_attrs))
    rows.sort(key=lambda row: (row["case:concept:name"], row["time:timestamp"], row["concept:name"]))
    return rows


def load_rows(input_path: Path, span_name: str | None) -> list[dict[str, object]]:
    if input_path.is_dir() or input_path.suffix.lower() == ".jsonl":
        return iter_rows_from_local_exports(input_path, span_name)

    with input_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    if isinstance(payload, dict) and "batches" in payload:
        return iter_rows_from_tempo_payload(payload, span_name)

    raise ValueError(
        f"Unsupported input format for {input_path}. Expected Tempo trace JSON or local JSONL exports."
    )


def main() -> None:
    args = parse_args()
    input_path = Path(args.input_json)
    output_path = Path(args.output_csv)

    selected_span_name = None if args.all_spans else args.span_name
    rows = load_rows(input_path, selected_span_name)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=DEFAULT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {output_path}")


if __name__ == "__main__":
    main()