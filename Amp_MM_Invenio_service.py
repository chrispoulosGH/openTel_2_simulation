"""Service E â€“ microservice simulator. Called by B, calls H downstream."""
import os
import time
import random
from threading import Lock
from flask import Flask, jsonify
from common.tracing import init_tracer, instrument_app, simulate_db_call, simulate_sql_column_not_found, print_e2eux, copy_baggage_to_span, call_next_service_in_chain, get_possible_downstream_urls_for_service, get_chain_id, resolve_e2eux

SERVICE_NAME = "Amp-MM - Invenio"
PORT = int(os.getenv("SERVICE_E_PORT", 8015))
OTLP_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "localhost:4317")

DOWNSTREAM = get_possible_downstream_urls_for_service(SERVICE_NAME)

SQL_ERROR_TARGET_OCCURRENCES = int(os.getenv("AMP_SQL_ERROR_TARGET_OCCURRENCES", "2"))
_sql_error_count = 0
_sql_error_count_lock = Lock()

app = Flask(SERVICE_NAME)
tracer = init_tracer(SERVICE_NAME, OTLP_ENDPOINT)
instrument_app(app)


@app.route("/info", methods=["GET"])
def info():
    return jsonify(service=SERVICE_NAME, port=PORT, downstream=get_possible_downstream_urls_for_service(SERVICE_NAME))


@app.route("/e", methods=["GET"])
def handle_e():
    global _sql_error_count
    chain_id = get_chain_id() or ""
    e2eux_value = resolve_e2eux() or ""
    print_e2eux(SERVICE_NAME)
    with tracer.start_as_current_span("process-request") as span:
        copy_baggage_to_span(["E2EUX", "chain_id"], span=span)
        time.sleep(random.uniform(0.015, 0.04))  # simulate encryption

        should_inject_sql_error = False
        with _sql_error_count_lock:
            if (
                _sql_error_count < SQL_ERROR_TARGET_OCCURRENCES
                and chain_id.startswith("test_scenario_")
                and e2eux_value.lower().startswith("troubleshoot")
            ):
                _sql_error_count += 1
                should_inject_sql_error = True

        # Simulate database operation (error or success)
        try:
            if should_inject_sql_error:
                db_result = simulate_sql_column_not_found(
                    tracer,
                    "db_e",
                    table_name="main_table",
                    missing_column="customer_segment",
                    service_name=SERVICE_NAME,
                    chain_id=chain_id,
                )
            else:
                db_result = simulate_db_call(tracer, "db_e")
        except Exception as e:
            # Handle any unexpected database errors gracefully
            db_result = {"status": "error", "message": str(e), "rows": 0}

        downstream = call_next_service_in_chain(SERVICE_NAME)
        time.sleep(random.uniform(0.003, 0.012))  # simulate logging
        return jsonify(service=SERVICE_NAME, db=db_result, downstream=downstream)


@app.route("/health", methods=["GET"])
def health():
    return jsonify(status="ok", service=SERVICE_NAME)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)

