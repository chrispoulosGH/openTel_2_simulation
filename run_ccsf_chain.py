"""Run the CCSF (lookup_customer_chain) chain. Starts only required servers."""
import os
import sys
import time
import subprocess
import requests
from common.chains import CHAIN_DEFINITIONS, SERVICE_SPECS, get_service_url


import argparse

DEFAULT_CHAIN_ID = "lookup_customer_chain"
parser = argparse.ArgumentParser(description="Run the CCSF (lookup_customer_chain) chain.")
parser.add_argument("--chain", type=str, default=DEFAULT_CHAIN_ID, help="Chain ID to run (default: lookup_customer_chain)")
parser.add_argument("--runs", type=int, default=int(os.getenv("RUN_COUNT", "20")), help="Number of runs to execute (default: 20)")
args = parser.parse_args()

CHAIN_ID = args.chain
RUN_COUNT = args.runs

if CHAIN_ID not in CHAIN_DEFINITIONS:
    print(f"Unknown chain_id: {CHAIN_ID}", flush=True)
    print(f"Available chains: {list(CHAIN_DEFINITIONS.keys())}", flush=True)
    sys.exit(1)

# Get only the services needed for this chain
chain_services = CHAIN_DEFINITIONS[CHAIN_ID]
services = [s for s in SERVICE_SPECS if s["name"] in chain_services]


def run_chain():
    entry_service = services[0]["name"]
    entry_url = get_service_url(entry_service)
    for run_number in range(1, RUN_COUNT + 1):
        run_url = f"{entry_url}?chain_id={CHAIN_ID}"
        try:
            resp = requests.get(run_url, timeout=120)
            print(f"[{run_number:03d}] status={resp.status_code}", flush=True)
        except Exception as exc:
            print(f"[{run_number:03d}] failed: {exc}", flush=True)

def check_collector():
    # Try to connect to the OTLP collector endpoint before running the chain
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "localhost:4317")
    host, sep, port = otlp_endpoint.partition(":")
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2)
    try:
        s.connect((host, int(port)))
        print(f"[INFO] Successfully connected to OTLP collector at {otlp_endpoint}")
        s.close()
        return True
    except Exception as e:
        print(f"[ERROR] Could not connect to OTLP collector at {otlp_endpoint}: {e}")
        return False

if __name__ == "__main__":
    if not check_collector():
        print("Aborting chain run due to collector connection failure.")
        sys.exit(2)
    run_chain()
    print("\nChain runs complete.")
    import sys
    sys.exit(0)
