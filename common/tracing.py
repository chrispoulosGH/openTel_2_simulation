"""
Shared OpenTelemetry tracing setup for all microservice simulators.
Configures OTLP export (compatible with Grafana Tempo) and Flask/Requests instrumentation.
"""

import atexit
import json
import logging
import os
import sys
import time
import random
from pathlib import Path
from threading import Lock
from urllib.parse import unquote
import requests as req_lib
from flask import request
from common.chains import (
    BRANCHED_CHAIN_DEFINITIONS,
    FORKED_CHAIN_DEFINITIONS,
    get_next_service_name,
    get_possible_downstream_urls,
    get_service_url,
)

from opentelemetry import baggage, trace
from opentelemetry.trace import Status, StatusCode
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    SpanExporter,
    SpanExportResult,
)
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

try:
    from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
    from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
    from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
except ImportError:
    LoggerProvider = None
    LoggingHandler = None
    BatchLogRecordProcessor = None
    OTLPLogExporter = None

# Configure logging to both stderr and a file so output is always visible somewhere
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stderr),
        logging.FileHandler("services.log", mode="a"),
    ],
)
logger = logging.getLogger("otel-sim")
logging.getLogger("werkzeug").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("opentelemetry").setLevel(logging.WARNING)

_otel_log_provider = None
_otel_log_handler = None


def init_otel_logging(service_name: str, otlp_endpoint: str = "localhost:4317"):
    """Optionally export Python log records to OTLP alongside local file logging."""
    global _otel_log_provider
    global _otel_log_handler

    if os.getenv("ENABLE_OTEL_LOG_EXPORT", "1") == "0":
        return

    if not all([LoggerProvider, LoggingHandler, BatchLogRecordProcessor, OTLPLogExporter]):
        logger.warning(
            "OTEL log export disabled: OpenTelemetry logs packages are not installed"
        )
        return

    if _otel_log_handler is not None:
        return

    _otel_log_provider = LoggerProvider(
        resource=Resource(attributes={SERVICE_NAME: service_name})
    )
    _otel_log_provider.add_log_record_processor(
        BatchLogRecordProcessor(
            OTLPLogExporter(endpoint=otlp_endpoint, insecure=True),
            schedule_delay_millis=1000,
        )
    )

    _otel_log_handler = LoggingHandler(
        level=logging.INFO,
        logger_provider=_otel_log_provider,
    )
    logger.addHandler(_otel_log_handler)

    atexit.register(_otel_log_provider.force_flush)
    atexit.register(_otel_log_provider.shutdown)

E2EUX_KEY = "E2EUX"
LEGACY_E2EUX_KEY = "business_process_flow"


def _json_safe_value(value):
    """Convert span/resource values into JSON-safe primitives."""
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, (list, tuple)):
        return [_json_safe_value(item) for item in value]
    return str(value)


class LocalJsonSpanExporter(SpanExporter):
    """Persist exported spans locally as JSONL so Tempo export is optional."""

    def __init__(self, service_name: str, export_dir: str):
        self._output_path = Path(export_dir) / "spans" / f"{service_name}-{os.getpid()}.jsonl"
        self._output_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()

    def export(self, spans):
        with self._lock:
            with self._output_path.open("a", encoding="utf-8") as handle:
                for span in spans:
                    parent_span_id = ""
                    if span.parent is not None:
                        parent_span_id = format(span.parent.span_id, "016x")

                    status_code = getattr(getattr(span, "status", None), "status_code", None)
                    resource_attributes = {
                        key: _json_safe_value(value)
                        for key, value in dict(getattr(span.resource, "attributes", {})).items()
                    }
                    span_attributes = {
                        key: _json_safe_value(value)
                        for key, value in dict(span.attributes).items()
                    }
                    record = {
                        "__format__": "otel-sim-local-span-v1",
                        "resource_attributes": resource_attributes,
                        "traceId": format(span.context.trace_id, "032x"),
                        "spanId": format(span.context.span_id, "016x"),
                        "parentSpanId": parent_span_id,
                        "name": span.name,
                        "kind": getattr(span.kind, "name", str(span.kind)),
                        "startTimeUnixNano": str(span.start_time),
                        "endTimeUnixNano": str(span.end_time),
                        "status": {
                            "code": getattr(status_code, "value", 0),
                            "name": getattr(status_code, "name", "UNSET"),
                        },
                        "attributes": span_attributes,
                    }
                    handle.write(json.dumps(record, sort_keys=True))
                    handle.write("\n")
        return SpanExportResult.SUCCESS

    def shutdown(self):
        return None


def get_e2eux():
    """Return the current E2EUX value from baggage, if present."""
    return baggage.get_baggage(E2EUX_KEY) or baggage.get_baggage(LEGACY_E2EUX_KEY)


def get_baggage_value_from_header(key: str):
    """Read a baggage value directly from the incoming W3C baggage header."""
    baggage_header = request.headers.get("baggage", "")
    for item in baggage_header.split(","):
        header_key, separator, value = item.strip().partition("=")
        if separator and header_key.strip() == key:
            return unquote(value.strip())
    return None


def get_e2eux_from_header():
    """Read E2EUX directly from the incoming W3C baggage header."""
    return get_baggage_value_from_header(E2EUX_KEY) or get_baggage_value_from_header(
        LEGACY_E2EUX_KEY
    )


def resolve_baggage_value(key: str, fallback=None):
    """Resolve a baggage value from current context, incoming header, or fallback."""
    if key == E2EUX_KEY:
        return get_e2eux() or fallback
    return baggage.get_baggage(key) or get_baggage_value_from_header(key) or fallback


def copy_baggage_to_span(keys, span=None, fallback_values=None):
    """Copy selected baggage keys onto the provided span or current span."""
    target_span = span or trace.get_current_span()
    if target_span is None or not target_span.is_recording():
        return {}

    copied_values = {}
    fallback_values = fallback_values or {}
    for key in keys:
        value = resolve_baggage_value(key, fallback_values.get(key))
        if value:
            target_span.set_attribute(key, value)
            copied_values[key] = value
    return copied_values


def resolve_e2eux(fallback=None):
    """Resolve E2EUX from current context, incoming header, or fallback."""
    return get_e2eux() or get_e2eux_from_header() or fallback


def get_chain_id(fallback=None):
    """Resolve the active chain identifier from baggage, request, or fallback."""
    return resolve_baggage_value("chain_id", request.args.get("chain_id") or fallback)


def resolve_e2eux_with_source(fallback=None):
    """Resolve E2EUX and report where the value came from."""
    from_baggage = get_e2eux()
    if from_baggage:
        return from_baggage, "baggage"

    from_header = get_e2eux_from_header()
    if from_header:
        return from_header, "header"

    if fallback:
        return fallback, "fallback"

    return None, "missing"


def annotate_span_with_e2eux(span):
    """Copy E2EUX baggage onto the current span for backend queries."""
    copy_baggage_to_span([E2EUX_KEY], span=span)


def annotate_current_span_with_e2eux(fallback=None):
    """Copy E2EUX onto the currently active span and report its source."""
    e2eux, source = resolve_e2eux_with_source(fallback)
    copy_baggage_to_span(
        [E2EUX_KEY],
        fallback_values={E2EUX_KEY: fallback},
    )
    return e2eux, source


def init_tracer(service_name: str, otlp_endpoint: str = "localhost:4317"):
    """Initialize OpenTelemetry tracer with OTLP gRPC exporter for Tempo."""
    init_otel_logging(service_name, otlp_endpoint)

    resource = Resource(attributes={SERVICE_NAME: service_name})
    provider = TracerProvider(resource=resource)

    # OTLP gRPC exporter -> collector / Tempo
    exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
    provider.add_span_processor(
        BatchSpanProcessor(exporter, schedule_delay_millis=1000)
    )

    local_trace_export_enabled = os.getenv("ENABLE_LOCAL_TRACE_EXPORT", "1") != "0"
    local_trace_export_dir = os.getenv("LOCAL_TRACE_EXPORT_DIR", "local_traces")
    if local_trace_export_enabled:
        provider.add_span_processor(
            BatchSpanProcessor(
                LocalJsonSpanExporter(service_name, local_trace_export_dir),
                schedule_delay_millis=1000,
            )
        )

    trace.set_tracer_provider(provider)

    # Ensure all buffered spans are flushed when the process exits
    atexit.register(provider.force_flush)
    return trace.get_tracer(service_name)


def log_service_invocation(service_name: str, e2eux=None):
    """Emit one concise line per service request with propagated E2EUX data."""
    if request.endpoint in {"info", "health"}:
        return

    if request.path == "/d" and request.args.get("chain_id") and e2eux is None:
        return

    resolved_e2eux, source = annotate_current_span_with_e2eux(e2eux)
    current_span = trace.get_current_span()
    span_context = current_span.get_span_context()
    trace_id = format(span_context.trace_id, "032x") if span_context.is_valid else "-"

    logger.info(
        "service=%s trace_id=%s method=%s path=%s E2EUX=%s source=%s",
        service_name,
        trace_id,
        request.method,
        request.path,
        resolved_e2eux or "-",
        source,
    )


def print_e2eux(service_name: str, fallback=None):
    """Print the resolved E2EUX for the current request."""
    e2eux, source = annotate_current_span_with_e2eux(fallback)
    print(
        f"{service_name} E2EUX={e2eux or '-'} source={source}",
        flush=True,
    )
    return e2eux


def get_possible_downstream_urls_for_service(service_name: str):
    """Return all possible downstream URLs for a service across configured chains."""
    return get_possible_downstream_urls(service_name)


def call_next_service_in_chain(service_name: str):
    """Call the next service for the active chain and return its response payload."""
    chain_id = get_chain_id()
    next_service_name = get_next_service_name(service_name, chain_id)
    if not next_service_name:
        return {}

    return {next_service_name: call_downstream(get_service_url(next_service_name))}


def call_forked_chain_from_entry(service_name: str):
    """Execute configured fork branches for entry service and join into final service.
    
    Skips dynamic chains, which use randomized path selection via get_next_service_name.
    """
    chain_id = get_chain_id()
    forked_chain = FORKED_CHAIN_DEFINITIONS.get(chain_id or "")
    if not forked_chain:
        return None

    if service_name != forked_chain["entry"]:
        return None
    
    # Skip dynamic chains - they use randomized routing via get_next_service_name
    if forked_chain.get("dynamic", False):
        return None

    branch_results = {}
    for branch_index, branch in enumerate(forked_chain["branches"], start=1):
        branch_name = f"branch_{branch_index}"
        service_results = {}
        for service in branch:
            service_results[service] = call_downstream(get_service_url(service))
        branch_results[branch_name] = service_results

    join_service = forked_chain["join"]
    join_result = {join_service: call_downstream(get_service_url(join_service))}
    return {
        "branches": branch_results,
        "join": join_result,
    }


def call_branched_chain_from_fork(service_name: str):
    """Execute configured branch-and-join flow from a non-entry fork service."""
    chain_id = get_chain_id()
    branched_chain = BRANCHED_CHAIN_DEFINITIONS.get(chain_id or "")
    if not branched_chain:
        return None

    if service_name != branched_chain["fork_at"]:
        return None

    branch_results = {}
    for branch_index, branch in enumerate(branched_chain["branches"], start=1):
        branch_name = f"branch_{branch_index}"
        # Call only the branch head; it cascades to its next service via
        # call_next_service_in_chain using the branched chain definition.
        branch_results[branch_name] = call_downstream(get_service_url(branch[0]))

    # After all branches complete, call the joined tail head; it cascades sequentially.
    joined_tail = branched_chain["joined_tail"]
    tail_head = joined_tail[0]
    tail_result = call_downstream(get_service_url(tail_head))

    return {
        "branches": branch_results,
        "joined_tail": {tail_head: tail_result},
    }


def instrument_app(app):
    """Instrument a Flask app and the requests library for trace propagation."""
    FlaskInstrumentor().instrument_app(
        app,
        request_hook=lambda span, environ: annotate_span_with_e2eux(span),
        excluded_urls="info,health",
    )
    RequestsInstrumentor().instrument(
        request_hook=lambda span, request_obj: annotate_span_with_e2eux(span)
    )
    app.before_request(lambda: log_service_invocation(app.name))


def simulate_db_call(tracer, db_name: str, operation: str = "SELECT"):
    """Simulate a database call as a child span with a small random delay."""
    with tracer.start_as_current_span(
        f"{db_name} {operation}",
        attributes={
            "db.system": "postgresql",
            "db.name": db_name,
            "db.operation": operation,
            "db.statement": f"{operation} * FROM {db_name}.main_table WHERE id = ?",
        },
    ) as span:
        annotate_span_with_e2eux(span)
        # Simulate DB latency (1–10 ms) to keep chain execution fast.
        time.sleep(random.uniform(0.001, 0.01))
        return {"status": "ok", "rows": random.randint(0, 100)}


def simulate_sql_column_not_found(
    tracer,
    db_name: str,
    table_name: str = "main_table",
    missing_column: str = "customer_segment",
    service_name: str | None = None,
    chain_id: str | None = None,
):
    """Simulate a deterministic SQL column-not-found database error.

    Creates an ERROR span and emits a structured log line that can be correlated
    using trace_id/span_id in OTEL backends.
    """
    statement = f"SELECT {missing_column} FROM {db_name}.{table_name} WHERE id = ?"
    error_message = f'column "{missing_column}" does not exist'

    with tracer.start_as_current_span(
        f"{db_name} SELECT",
        attributes={
            "db.system": "postgresql",
            "db.name": db_name,
            "db.operation": "SELECT",
            "db.statement": statement,
            "db.sql.table": table_name,
            "db.sql.missing_column": missing_column,
            "error.type": "SQL_COLUMN_NOT_FOUND",
            "error.message": error_message,
        },
    ) as span:
        annotate_span_with_e2eux(span)
        span.set_status(Status(StatusCode.ERROR, error_message))

        span_context = span.get_span_context()
        trace_id = format(span_context.trace_id, "032x") if span_context.is_valid else "-"
        span_id = format(span_context.span_id, "016x") if span_context.is_valid else "-"

        logger.error(
            "event=sql_error kind=column_not_found service=%s chain_id=%s db=%s table=%s column=%s trace_id=%s span_id=%s message=%s",
            service_name or "-",
            chain_id or "-",
            db_name,
            table_name,
            missing_column,
            trace_id,
            span_id,
            error_message,
            extra={"event": "sql_error", "loki.attribute.labels": "event"},
        )

        return {
            "status": "error",
            "error_type": "SQL_COLUMN_NOT_FOUND",
            "message": error_message,
            "db": db_name,
            "table": table_name,
            "column": missing_column,
            "statement": statement,
        }


def call_downstream(service_url: str):
    """Call a downstream service, propagating trace context automatically via instrumented requests."""
    timeout_seconds = float(os.getenv("DOWNSTREAM_TIMEOUT_SEC", "3"))
    retries = max(0, int(os.getenv("DOWNSTREAM_RETRIES", "0")))
    last_error = None

    for attempt in range(retries + 1):
        try:
            resp = req_lib.get(service_url, timeout=timeout_seconds)
            resp.raise_for_status()
            try:
                return resp.json()
            except ValueError:
                logger.warning(
                    "downstream=%s returned non-JSON response (status=%s)",
                    service_url,
                    resp.status_code,
                )
                return {
                    "error": "invalid_json_response",
                    "status_code": resp.status_code,
                    "url": service_url,
                }
        except req_lib.exceptions.RequestException as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(0.2 * (attempt + 1))
                continue

    logger.warning(
        "downstream request failed url=%s timeout=%ss retries=%s error=%s",
        service_url,
        timeout_seconds,
        retries,
        last_error,
    )
    return {
        "error": "downstream_request_failed",
        "url": service_url,
        "message": str(last_error),
        "timeout_seconds": timeout_seconds,
        "retries": retries,
    }
