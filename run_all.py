"""Launch the simulator services and execute the configured chains multiple times."""
import os
from pathlib import Path
import signal
import shutil
import subprocess
import sys
import time
from itertools import cycle
from time import perf_counter

import requests

from common.chains import CHAIN_DEFINITIONS, FORKED_CHAIN_DEFINITIONS, ENTRY_SERVICE_NAME, LONG_CHAIN_ID, SERVICE_SPECS, get_service_url


import argparse

RUN_COUNT = int(os.getenv("RUN_COUNT", "20"))
LOCAL_TRACE_EXPORT_DIR = Path(os.getenv("LOCAL_TRACE_EXPORT_DIR", "local_traces"))
RESET_LOCAL_TRACE_EXPORTS = os.getenv("RESET_LOCAL_TRACE_EXPORTS", "1") != "0"

def get_services_for_chain(chain_id):
    """Extract service specs needed for a chain (linear or forked)."""
    if chain_id in CHAIN_DEFINITIONS:
        chain = CHAIN_DEFINITIONS[chain_id]
        service_names = chain
    elif chain_id in FORKED_CHAIN_DEFINITIONS:
        forked_chain = FORKED_CHAIN_DEFINITIONS[chain_id]
        service_names = [forked_chain["entry"]]
        for branch in forked_chain["branches"]:
            service_names.extend(branch)
        service_names.append(forked_chain["join"])
    else:
        return []
    # Get unique service names in chain
    return [spec for spec in SERVICE_SPECS if spec["name"] in service_names]


def build_run_plan(total_runs: int):
    """Build a deterministic plan that cycles evenly through all configured chains."""
    chain_items = list(CHAIN_DEFINITIONS.items()) + list(FORKED_CHAIN_DEFINITIONS.items())
    return [chain for _, chain in zip(range(total_runs), cycle(chain_items))]


def kill_existing_servers():
    """Kill any processes already listening on configured service ports."""
    print("Killing any existing servers on configured service ports...", flush=True)
    for port in PORTS:
        # Use netstat + taskkill on Windows to find and kill processes on each port
        try:
            result = subprocess.run(
                ["netstat", "-ano"],
                capture_output=True, text=True
            )
            for line in result.stdout.splitlines():
                if f":{port}" in line and "LISTENING" in line:
                    parts = line.split()
                    pid = parts[-1]
                    if pid and pid != "0":
                        subprocess.run(
                            ["taskkill", "/F", "/PID", pid],
                            capture_output=True
                        )
                        print(f"  Killed PID {pid} on port {port}", flush=True)
        except Exception:
            pass
    time.sleep(0.5)


def reset_local_trace_exports():
    """Remove previous local trace exports so each run starts clean."""
    if not RESET_LOCAL_TRACE_EXPORTS:
        return
    if LOCAL_TRACE_EXPORT_DIR.exists():
        shutil.rmtree(LOCAL_TRACE_EXPORT_DIR)
        print(f"Cleared local trace exports in {LOCAL_TRACE_EXPORT_DIR}", flush=True)


processes = []


def shutdown(signum=None, frame=None):
    print("\nShutting down all services...")
    for name, proc in processes:
        proc.terminate()
    for name, proc in processes:
        proc.wait()
    print("All services stopped.")
    sys.exit(0)


signal.signal(signal.SIGINT, shutdown)
signal.signal(signal.SIGTERM, shutdown)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Launch and run microservice chains.")
    parser.add_argument("--chain", type=str, default=None, help="Chain ID to run (e.g. chain_01 or lookup_customer_chain). For multiple ABPT chains, comma-separate IDs (e.g. chain_01,chain_02)")
    parser.add_argument("--runs", type=int, default=RUN_COUNT, help="Number of runs to execute per chain")
    args = parser.parse_args()

    chain_arg = args.chain
    run_count = args.runs

    if chain_arg is not None:
        # Support multiple ABPT chains: --chain chain_01,chain_02
        chain_ids = [c.strip() for c in chain_arg.split(",") if c.strip()]
        for cid in chain_ids:
            if cid not in CHAIN_DEFINITIONS and cid not in FORKED_CHAIN_DEFINITIONS:
                print(f"Unknown chain_id: {cid}", flush=True)
                all_chains = list(CHAIN_DEFINITIONS.keys()) + list(FORKED_CHAIN_DEFINITIONS.keys())
                print(f"Available chains: {all_chains}", flush=True)
                sys.exit(1)
        # If only one chain, keep old behavior
        if len(chain_ids) == 1:
            chain_id = chain_ids[0]
            services = get_services_for_chain(chain_id)
            entry_service = services[0]["name"]
            entry_url = get_service_url(entry_service)
            chain_data = CHAIN_DEFINITIONS.get(chain_id) or FORKED_CHAIN_DEFINITIONS.get(chain_id)
            chains_to_run = [(chain_id, chain_data)] * run_count
        else:
            # Multiple chains: only valid for ABPT entry chains
            # All must start with ABPT
            for cid in chain_ids:
                chain_data = CHAIN_DEFINITIONS.get(cid) or FORKED_CHAIN_DEFINITIONS.get(cid)
                entry = chain_data[0] if isinstance(chain_data, list) else chain_data.get("entry")
                if entry != "ABPT":
                    print(f"Multi-chain mode only supported for ABPT entry chains.", flush=True)
                    sys.exit(1)
            # Union of all services needed
            abpt_services = set()
            for cid in chain_ids:
                abpt_services.update(s["name"] for s in get_services_for_chain(cid))
            services = [s for s in SERVICE_SPECS if s["name"] in abpt_services]
            entry_service = "ABPT"
            entry_url = get_service_url(entry_service)
            chains_to_run = []
            for cid in chain_ids:
                chain_data = CHAIN_DEFINITIONS.get(cid) or FORKED_CHAIN_DEFINITIONS.get(cid)
                chains_to_run.extend([(cid, chain_data)] * run_count)
    else:
        services = SERVICE_SPECS
        entry_service = ENTRY_SERVICE_NAME
        entry_url = get_service_url(entry_service)
        chains_to_run = build_run_plan(run_count)

        PORTS = [spec["port"] for spec in services]

        # Make PORTS global so kill_existing_servers can access it
        globals()["PORTS"] = PORTS
        kill_existing_servers()
    reset_local_trace_exports()

    # Force unbuffered output so child prints appear immediately
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"

    for spec in services:
        name, script = spec["name"], spec["script"]
        print(f"Starting {name} ({script})...", flush=True)
        proc = subprocess.Popen(
            [sys.executable, "-u", script],
            env=env,
        )
        processes.append((name, proc))
        time.sleep(0.5)

        # Check if subprocess crashed immediately
        ret = proc.poll()
        if ret is not None:
            print(f"*** {name} exited immediately with code {ret} ***", flush=True)

    # Check all processes are still alive
    time.sleep(1)
    alive = 0
    for name, proc in processes:
        ret = proc.poll()
        if ret is not None:
            print(f"*** {name} is NOT running (exit code {ret}) ***", flush=True)
        else:
            alive += 1
    print(f"\n--- {alive}/{len(services)} services running ---", flush=True)
    print(f"Entry point:  GET {entry_url}?chain_id={chain_arg or '<chain_id>'}", flush=True)
    print("Log file:     services.log", flush=True)
    print(f"Local traces:  {LOCAL_TRACE_EXPORT_DIR / 'spans'}", flush=True)
    print("Press Ctrl+C to stop all.\n", flush=True)

    print("Configured chains", flush=True)
    print("=================", flush=True)
    for cid, chain in CHAIN_DEFINITIONS.items():
        marker = " (longer)" if cid == LONG_CHAIN_ID else ""
        print(f"  {cid}{marker}: {' -> '.join(chain)}", flush=True)
    for cid, forked_chain in FORKED_CHAIN_DEFINITIONS.items():
        marker = " (dynamic)" if forked_chain.get("dynamic") else ""
        entry = forked_chain["entry"]
        join = forked_chain["join"]
        branch_count = len(forked_chain["branches"])
        print(f"  {cid}{marker}: {entry} -> [{branch_count} branches] -> {join}", flush=True)
    print("", flush=True)

    time.sleep(1)
    print(f"=== Executing {run_count} runs through {entry_service} ===", flush=True)
    results = []
    for run_number, (cid, chain) in enumerate(chains_to_run, start=1):
        run_url = f"{entry_url}?chain_id={cid}"
        started = perf_counter()
        try:
            resp = requests.get(run_url, timeout=120)
            elapsed = perf_counter() - started
            results.append((run_number, cid, elapsed, resp.status_code, chain))
            print(
                f"[{run_number:03d}] chain={cid} status={resp.status_code} duration={elapsed:.3f}s path={' -> '.join(chain)}",
                flush=True,
            )
        except Exception as exc:
            elapsed = perf_counter() - started
            results.append((run_number, cid, elapsed, None, chain))
            print(
                f"[{run_number:03d}] chain={cid} failed after {elapsed:.3f}s path={' -> '.join(chain)} error={exc}",
                flush=True,
            )

    print("\nChain duration summary", flush=True)
    print("======================", flush=True)
    completed = 0
    failed = 0
    for run_number, cid, elapsed, status_code, chain in results:
        status_label = status_code if status_code is not None else "failed"
        marker = " <-- expected longest" if cid == LONG_CHAIN_ID else ""
        if status_code == 200:
            completed += 1
        else:
            failed += 1
        print(
            f"  run={run_number:03d} chain={cid}: {elapsed:.3f}s status={status_label} hops={len(chain)}{marker}",
            flush=True,
        )

    print("\nRun totals", flush=True)
    print("==========", flush=True)
    print(f"  planned runs: {run_count}", flush=True)
    print(f"  completed:    {completed}", flush=True)
    print(f"  failed:       {failed}", flush=True)

    print("\nCheck services.log for detailed trace output.", flush=True)

    # Wait for any child to exit
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        shutdown()
