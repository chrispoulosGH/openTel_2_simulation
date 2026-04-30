"""Service A â€“ entry-point microservice simulator. Calls B and C downstream."""
import os
import time
import random
from flask import Flask, jsonify
from common.tracing import init_tracer, instrument_app, simulate_db_call, print_e2eux, copy_baggage_to_span, call_next_service_in_chain, call_branched_chain_from_fork, get_possible_downstream_urls_for_service

SERVICE_NAME = "T.Data"
PORT = int(os.getenv("SERVICE_A_PORT", 8001))
OTLP_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "localhost:4317")

DOWNSTREAM = get_possible_downstream_urls_for_service(SERVICE_NAME)

app = Flask(SERVICE_NAME)
tracer = init_tracer(SERVICE_NAME, OTLP_ENDPOINT)
instrument_app(app)


@app.route("/info", methods=["GET"])
def info():
    return jsonify(service=SERVICE_NAME, port=PORT, downstream=get_possible_downstream_urls_for_service(SERVICE_NAME))


@app.route("/a", methods=["GET"])
def handle_a():
    print_e2eux(SERVICE_NAME)
    with tracer.start_as_current_span("process-request") as span:
        copy_baggage_to_span(["E2EUX", "chain_id"], span=span)
        time.sleep(random.uniform(0.012, 0.04))  # simulate request validation
        db_result = simulate_db_call(tracer, "db_a")
        time.sleep(random.uniform(0.005, 0.02))  # simulate processing
        downstream = call_branched_chain_from_fork(SERVICE_NAME)
        if downstream is None:
            downstream = call_next_service_in_chain(SERVICE_NAME)
        time.sleep(random.uniform(0.003, 0.01))  # simulate response assembly
        return jsonify(service=SERVICE_NAME, db=db_result, downstream=downstream)


@app.route("/health", methods=["GET"])
def health():
    return jsonify(status="ok", service=SERVICE_NAME)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)

