"""Run all ABPT chains. Starts only required servers."""
import os
import sys
import time
import subprocess
import requests
from itertools import cycle
from common.chains import CHAIN_DEFINITIONS, SERVICE_SPECS, get_service_url


import argparse

parser = argparse.ArgumentParser(description="Run ABPT chains.")
parser.add_argument("--chain", type=str, default=None, help="Comma-separated ABPT chain IDs to run (default: all ABPT chains)")
parser.add_argument("--runs", type=int, default=int(os.getenv("RUN_COUNT", "20")), help="Number of runs to execute (default: 20)")
args = parser.parse_args()

if args.chain:
    abpt_chain_ids = [cid.strip() for cid in args.chain.split(",") if cid.strip()]
    for cid in abpt_chain_ids:
        if cid not in CHAIN_DEFINITIONS or CHAIN_DEFINITIONS[cid][0] != "ABPT":
            print(f"Unknown or non-ABPT chain_id: {cid}", flush=True)
            print(f"Available ABPT chains: {[c for c in CHAIN_DEFINITIONS if CHAIN_DEFINITIONS[c][0] == 'ABPT']}", flush=True)
            sys.exit(1)
else:
    abpt_chain_ids = [cid for cid, chain in CHAIN_DEFINITIONS.items() if chain[0] == "ABPT"]

RUN_COUNT = args.runs

# Union of all services needed for selected ABPT chains
abpt_services = set()
for cid in abpt_chain_ids:
    abpt_services.update(s["name"] for s in SERVICE_SPECS if s["name"] in CHAIN_DEFINITIONS[cid])
services = [s for s in SERVICE_SPECS if s["name"] in abpt_services]


def run_abpt_chains():
    entry_service = "ABPT"
    entry_url = get_service_url(entry_service)
    run_plan = [cid for _, cid in zip(range(RUN_COUNT), cycle(abpt_chain_ids))]
    for run_number, cid in enumerate(run_plan, start=1):
        run_url = f"{entry_url}?chain_id={cid}"
        try:
            resp = requests.get(run_url, timeout=120)
            print(f"[{run_number:03d}] chain={cid} status={resp.status_code}", flush=True)
        except Exception as exc:
            print(f"[{run_number:03d}] chain={cid} failed: {exc}", flush=True)

if __name__ == "__main__":
    run_abpt_chains()
    print("\nABPT chain runs complete.")
    import sys
    sys.exit(0)
