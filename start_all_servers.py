"""Start all microservice servers without running any chains."""
import os
import sys
import time
import subprocess
from pathlib import Path
from common.chains import SERVICE_SPECS

processes = []
BASE_DIR = Path(__file__).resolve().parent


def resolve_service_script(script: str) -> Path:
    script_path = Path(script)
    if script_path.is_absolute():
        return script_path

    candidate_roots = [
        BASE_DIR,
        Path.cwd(),
        Path.cwd() / "openTel_2_simulation",
    ]

    for root in candidate_roots:
        candidate = (root / script_path).resolve()
        if candidate.exists():
            return candidate

    # Return the primary expected location for clearer error reporting.
    return (BASE_DIR / script_path).resolve()


def kill_ports(ports):
    import subprocess
    for port in ports:
        try:
            result = subprocess.run([
                "netstat", "-ano"
            ], capture_output=True, text=True)
            for line in result.stdout.splitlines():
                if f":{port}" in line and "LISTENING" in line:
                    parts = line.split()
                    pid = parts[-1]
                    if pid and pid != "0":
                        subprocess.run([
                            "taskkill", "/F", "/PID", pid
                        ], capture_output=True)
                        print(f"Killed process {pid} on port {port}", flush=True)
        except Exception as e:
            print(f"Error killing process on port {port}: {e}", flush=True)

def start_all_servers():
    # Kill all service ports before starting servers
    ports = [spec["port"] for spec in SERVICE_SPECS]
    kill_ports(ports)
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    for spec in SERVICE_SPECS:
        name, script = spec["name"], spec["script"]
        script_path = resolve_service_script(script)

        print(f"Starting {name} ({script_path.name})...", flush=True)
        if not script_path.exists():
            print(f"*** Missing service script: {script_path} ***", flush=True)
            continue

        proc = subprocess.Popen([
            sys.executable, "-u", str(script_path)
        ], env=env, cwd=str(BASE_DIR))
        processes.append((name, proc))
        time.sleep(0.5)
        ret = proc.poll()
        if ret is not None:
            print(f"*** {name} exited immediately with code {ret} ***", flush=True)
    print(f"\n--- {len(processes)}/{len(SERVICE_SPECS)} services started ---", flush=True)
    print("start_all_servers.py exiting; services will continue running in background.", flush=True)

if __name__ == "__main__":
    start_all_servers()
