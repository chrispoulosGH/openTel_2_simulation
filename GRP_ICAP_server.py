"""Service G â€“ microservice simulator. Called by D, calls J downstream."""
import os
import time
import random
from flask import Flask, jsonify
from common.tracing import init_tracer, instrument_app, simulate_db_call, print_e2eux, copy_baggage_to_span, call_next_service_in_chain, get_possible_downstream_urls_for_service

SERVICE_NAME = "GRP-ICAP"
PORT = int(os.getenv("SERVICE_G_PORT", 8007))
OTLP_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "localhost:4317")
TIMEOUT_RATE = float(os.getenv("GRP_ICAP_TIMEOUT_RATE", "0.0"))
TIMEOUT_SECONDS = float(os.getenv("GRP_ICAP_TIMEOUT_SECONDS", "6.0"))

DOWNSTREAM = get_possible_downstream_urls_for_service(SERVICE_NAME)

app = Flask(SERVICE_NAME)
tracer = init_tracer(SERVICE_NAME, OTLP_ENDPOINT)
instrument_app(app)


@app.route("/info", methods=["GET"])
def info():
    return jsonify(service=SERVICE_NAME, port=PORT, downstream=get_possible_downstream_urls_for_service(SERVICE_NAME))


@app.route("/g", methods=["GET"])
def handle_g():
    print_e2eux(SERVICE_NAME)
    with tracer.start_as_current_span("process-request") as span:
        copy_baggage_to_span(["E2EUX", "chain_id"], span=span)
        if random.random() < TIMEOUT_RATE:
            if span.is_recording():
                span.set_attribute("grp_icap.simulated_timeout", True)
                span.set_attribute("grp_icap.timeout_seconds", TIMEOUT_SECONDS)
            time.sleep(TIMEOUT_SECONDS)
            return jsonify(error="Simulated GRP-ICAP timeout"), 504

        time.sleep(random.uniform(0.008, 0.025))  # simulate queue wait
        db_result = simulate_db_call(tracer, "db_g")
        time.sleep(random.uniform(0.012, 0.04))  # simulate computation
        downstream = call_next_service_in_chain(SERVICE_NAME)
        return jsonify(service=SERVICE_NAME, db=db_result, downstream=downstream)


@app.route("/health", methods=["GET"])
def health():
    return jsonify(status="ok", service=SERVICE_NAME)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)

