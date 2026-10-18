"""Capture product screenshots for the slides with headless Chrome/Edge/Chromium (Windows, macOS, Linux).

Start the app first (python run.py), then:   python scripts/take_screenshots.py
Override the browser with CHROME=/path/to/chrome and the URL with BASE=http://127.0.0.1:8000
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "screenshots"
BASE = os.environ.get("BASE", "http://127.0.0.1:8000")
PAGES = {
    "patients": "/", "overview_A": "/patients/A", "trends_A": "/patients/A/trends",
    "whatif_A": "/patients/A/what-if?sleep=7.5&shift=0", "overview_B": "/patients/B",
    "whatif_B": "/patients/B/what-if?cpap=1", "overview_C": "/patients/C", "about": "/about",
}
CANDIDATES = [
    os.environ.get("CHROME", ""),
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    *(shutil.which(n) or "" for n in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser",
                                       "microsoft-edge", "chrome", "msedge")),
]


def find_browser() -> str | None:
    return next((c for c in CANDIDATES if c and Path(c).exists()), None)


def main() -> int:
    browser = find_browser()
    if not browser:
        print("No Chrome/Edge/Chromium found. Set CHROME=/path/to/browser.")
        return 1
    OUT.mkdir(parents=True, exist_ok=True)
    for name, path in PAGES.items():
        target = OUT / f"{name}.png"
        subprocess.run([browser, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--window-size=1440,1000",
                        "--virtual-time-budget=8000", f"--screenshot={target}", BASE + path],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120, check=False)
        print(("  ok   " if target.exists() else "  FAIL ") + str(target.relative_to(ROOT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
