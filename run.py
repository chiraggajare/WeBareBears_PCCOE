"""One cross-platform launcher for SleepTwin (Windows, macOS, Linux).

    python run.py                 # set up whatever is missing, then serve on http://127.0.0.1:8000
    python run.py --lan           # also reachable from phones/tablets on the same Wi-Fi
    python run.py --port 9000     # another port
    python run.py --rebuild       # re-run the data pipeline and rebuild the web app
    python run.py --open          # open the browser automatically

What it does, only when needed:
  1. downloads the open datasets      (scripts/download_data.py)
  2. simulates the cohort + trains     (python -m src.pipeline)
  3. builds the web app if Node is installed (npm ci && npm run build);
     a pre-built web/dist is used when Node is not available
  4. starts the API + website with uvicorn
"""
from __future__ import annotations

import argparse
import os
import shutil
import socket
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WEB = ROOT / "web"
MIN_PY = (3, 11)

# consistent UTF-8 console output on Windows terminals
for stream in (sys.stdout, sys.stderr):
    try:
        stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except Exception:  # noqa: BLE001
        pass


def step(msg: str) -> None:
    print(f"\n==> {msg}", flush=True)


def run(cmd: list[str], cwd: Path = ROOT) -> None:
    env = {**os.environ, "PYTHONUTF8": "1"}
    subprocess.run(cmd, cwd=str(cwd), check=True, env=env)


def lan_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))  # no packet is sent; picks the outbound interface
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


def ensure_data(rebuild: bool) -> None:
    raw_ok = (ROOT / "data/raw/nhanes/P_DEMO.xpt").exists() and \
        (ROOT / "data/raw/lifesnaps/daily_fitbit_sema_df_unprocessed.csv").exists()
    if not raw_ok:
        step("Downloading open datasets (NHANES + LifeSnaps, ~20 MB)")
        run([sys.executable, "scripts/download_data.py"])
    models_ok = (ROOT / "models/manifest.json").exists() and (ROOT / "data/processed/cgm.parquet").exists()
    if rebuild or not models_ok:
        step("Simulating 300 virtual patients and training the models (~20-60 s)")
        run([sys.executable, "-m", "src.pipeline"])


def ensure_web(rebuild: bool) -> None:
    dist = WEB / "dist" / "index.html"
    npm = shutil.which("npm")
    if dist.exists() and not rebuild:
        return
    if not npm:
        if dist.exists():
            print("Node.js not found - using the pre-built web app in web/dist.")
            return
        print("WARNING: Node.js (npm) not found and web/dist is missing - the API will run, but the website "
              "needs Node 18+ to build once (https://nodejs.org).")
        return
    step("Building the web app")
    if not (WEB / "node_modules").exists() or rebuild:
        run([npm, "ci", "--no-audit", "--no-fund"], cwd=WEB)
    run([npm, "run", "build"], cwd=WEB)


def main() -> int:
    if sys.version_info < MIN_PY:
        print(f"SleepTwin needs Python {MIN_PY[0]}.{MIN_PY[1]}+ (you have {sys.version.split()[0]}).")
        return 1
    ap = argparse.ArgumentParser(description="Run SleepTwin")
    ap.add_argument("--port", type=int, default=int(os.environ.get("SLEEPTWIN_PORT", 8000)))
    ap.add_argument("--host", default=os.environ.get("SLEEPTWIN_HOST", "127.0.0.1"),
                    help="bind address (default 127.0.0.1 = this computer only)")
    ap.add_argument("--lan", action="store_true", help="listen on the local network (0.0.0.0)")
    ap.add_argument("--rebuild", action="store_true", help="re-run pipeline and rebuild the web app")
    ap.add_argument("--skip-setup", action="store_true", help="just start the server")
    ap.add_argument("--open", action="store_true", help="open the browser")
    a = ap.parse_args()

    try:
        import fastapi  # noqa: F401
        import lightgbm  # noqa: F401
    except ImportError:
        print("Python packages missing. Run:  pip install -r requirements.txt")
        return 1
    except OSError as err:
        if "libomp" in str(err):
            print("\nLightGBM requires OpenMP runtime library (libomp) on macOS.")
            print("Please run:  brew install libomp\n")
            return 1
        raise

    if not a.skip_setup:
        ensure_data(a.rebuild)
        ensure_web(a.rebuild)

    host = "0.0.0.0" if a.lan else a.host
    local = f"http://127.0.0.1:{a.port}"
    step("Starting SleepTwin")
    print(f"  This computer : {local}")
    if host == "0.0.0.0":
        print(f"  Other devices : http://{lan_ip()}:{a.port}   (same Wi-Fi; allow Python through the firewall)")
        print("  Note: anyone on this network can open it. All data is simulated.")
    print("  Stop with Ctrl+C\n", flush=True)
    if a.open:
        threading.Thread(target=lambda: (time.sleep(2.5), webbrowser.open(local)), daemon=True).start()

    import uvicorn
    os.chdir(ROOT)
    sys.path.insert(0, str(ROOT))
    uvicorn.run("api.main:app", host=host, port=a.port, server_header=False, proxy_headers=False,
                log_level="info")
    return 0


if __name__ == "__main__":
    sys.exit(main())
