"""Check the /health endpoint of all services defined in SERVICE_SPECS."""
import requests
from common.chains import SERVICE_SPECS


def check_service_health():
    all_healthy = True
    for spec in SERVICE_SPECS:
        name = spec["name"]
        port = spec["port"]
        url = f"http://localhost:{port}/health"
        try:
            resp = requests.get(url, timeout=3)
            if resp.status_code == 200:
                print(f"[OK]   {name:30} {url}")
            else:
                print(f"[FAIL] {name:30} {url} (status {resp.status_code})")
                all_healthy = False
        except Exception as e:
            print(f"[DOWN] {name:30} {url} ({e})")
            all_healthy = False
    if all_healthy:
        print("\nAll services are healthy.")
    else:
        print("\nSome services are not healthy or unreachable.")

if __name__ == "__main__":
    check_service_health()
