"""Stop all running microservice servers by killing processes listening on their configured ports."""
import subprocess
import time
from common.chains import SERVICE_SPECS

PORTS = [spec["port"] for spec in SERVICE_SPECS]

def kill_existing_servers():
    print("Killing any existing servers on configured service ports...", flush=True)
    for port in PORTS:
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
                        print(f"  Killed PID {pid} on port {port}", flush=True)
        except Exception as e:
            print(f"Error killing processes on port {port}: {e}", flush=True)
    time.sleep(0.5)
    print("All servers stopped.", flush=True)

if __name__ == "__main__":
    kill_existing_servers()
