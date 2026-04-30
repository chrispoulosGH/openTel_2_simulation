"""Service for Platform Support ATTFEDGOV1 â€“ microservice simulator. Called by CCSF, calls eTRACS downstream."""
import os
import time
import random
from flask import Flask, jsonify, request
from opentelemetry import baggage, context, trace
from common.chains import CHAIN_DEFINITIONS
from common.tracing import init_tracer, instrument_app, simulate_db_call, print_e2eux, copy_baggage_to_span, call_next_service_in_chain, get_possible_downstream_urls_for_service, log_service_invocation

SERVICE_NAME = "Platform Support ATTFEDGOV1"
PORT = int(os.getenv("SERVICE_PLATFORM_SUPPORT_ATTFEDGOV1_PORT", 8024))
OTLP_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "localhost:4317")

DOWNSTREAM = get_possible_downstream_urls_for_service(SERVICE_NAME)

app = Flask(SERVICE_NAME)
tracer = init_tracer(SERVICE_NAME, OTLP_ENDPOINT)
instrument_app(app)

@app.route("/info", methods=["GET"])
def info():
    return jsonify(service=SERVICE_NAME, port=PORT, downstream=get_possible_downstream_urls_for_service(SERVICE_NAME))

@app.route("/platform-support-attfedgov1", methods=["GET"])
def handle_platform_support_attfedgov1():
    chain_id = request.args.get("chain_id", "lookup_customer_chain")
    if chain_id not in CHAIN_DEFINITIONS:
        return jsonify(error=f"Unknown chain_id: {chain_id}"), 400

    baggage_context = baggage.set_baggage("chain_id", chain_id)
    token = context.attach(baggage_context)
    try:
        current_span = trace.get_current_span()
        if current_span.is_recording():
            current_span.set_attribute("chain_id", chain_id)
        log_service_invocation(SERVICE_NAME)
        print_e2eux(SERVICE_NAME)
        with tracer.start_as_current_span("process-request") as span:
            copy_baggage_to_span(["E2EUX", "chain_id", "Business_Flow_ID"], span=span)
            time.sleep(random.uniform(0.005, 0.02))
            db_result = simulate_db_call(tracer, "db_platform_support_attfedgov1")
            time.sleep(random.uniform(0.01, 0.03))
            downstream = call_next_service_in_chain(SERVICE_NAME)
            return jsonify(service=SERVICE_NAME, chain_id=chain_id, db=db_result, downstream=downstream)
    finally:
        context.detach(token)

@app.route("/health", methods=["GET"])
def health():
    return jsonify(status="ok", service=SERVICE_NAME)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)

