"""Service H â€“ leaf microservice simulator. Called by E, no downstream calls."""
import os
import time
import random
from flask import Flask, jsonify
from common.tracing import init_tracer, instrument_app, simulate_db_call, print_e2eux, copy_baggage_to_span, call_next_service_in_chain, get_possible_downstream_urls_for_service

SERVICE_NAME = "IDP-Commerce-ES"
PORT = int(os.getenv("SERVICE_H_PORT", 8008))
OTLP_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "localhost:4317")

DOWNSTREAM = get_possible_downstream_urls_for_service(SERVICE_NAME)

app = Flask(SERVICE_NAME)
tracer = init_tracer(SERVICE_NAME, OTLP_ENDPOINT)
instrument_app(app)


@app.route("/info", methods=["GET"])
def info():
    return jsonify(service=SERVICE_NAME, port=PORT, downstream=get_possible_downstream_urls_for_service(SERVICE_NAME))


@app.route("/h", methods=["GET"])
def handle_h():
    print_e2eux(SERVICE_NAME)
    with tracer.start_as_current_span("process-request") as span:
        copy_baggage_to_span(["E2EUX", "chain_id"], span=span)
        time.sleep(random.uniform(0.01, 0.025))  # simulate token validation
        db_result = simulate_db_call(tracer, "db_h")
        time.sleep(random.uniform(0.03, 0.07))  # simulate heavy computation
        downstream = call_next_service_in_chain(SERVICE_NAME)
        return jsonify(service=SERVICE_NAME, db=db_result, downstream=downstream)


@app.route("/health", methods=["GET"])
def health():
    return jsonify(status="ok", service=SERVICE_NAME)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)

