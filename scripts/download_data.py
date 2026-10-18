"""Download the open datasets SleepTwin is calibrated on.

* CDC NHANES 2017-Mar 2020 pre-pandemic (public domain, anonymized)
* LifeSnaps Fitbit dataset (Zenodo 7229547, CC-BY-4.0) - only the *daily* CSV
  is extracted from the 615 MB archive using HTTP range requests, so we never
  download the large BSON dump.

Raw files land in data/raw/ (git-ignored). Run:  python scripts/download_data.py
Everything degrades gracefully: if a download fails, the simulator falls back
to published summary statistics (see src/calibration.py).
"""
from __future__ import annotations

import hashlib
import io
import os
import sys
import time
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
NHANES_DIR = RAW / "nhanes"
LIFESNAPS_DIR = RAW / "lifesnaps"

NHANES_BASE = "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/"
NHANES_FILES = [
    "P_DEMO",    # demographics
    "P_BMX",     # body measures (BMI, waist)
    "P_BPXO",    # oscillometric blood pressure
    "P_GHB",     # HbA1c
    "P_GLU",     # fasting glucose
    "P_BIOPRO",  # creatinine -> eGFR
    "P_TCHOL",   # total cholesterol
    "P_HDL",     # HDL
    "P_TRIGLY",  # triglycerides + LDL (fasting subsample)
    "P_SLQ",     # sleep questionnaire
    "P_DIQ",     # "doctor told you have diabetes" + age at diagnosis
    "P_BPQ",     # "told you have high BP" + BP medication
]

LIFESNAPS_URL = "https://zenodo.org/api/records/7229547/files/rais_anonymized.zip/content"
LIFESNAPS_MEMBER = "rais_anonymized/csv_rais_anonymized/daily_fitbit_sema_df_unprocessed.csv"

UA = {"User-Agent": "SleepTwin-research-prototype/1.1"}
MAX_FILE_BYTES = 50 * 1024 * 1024      # no single file we need is > 5 MB; cap protects disk/memory
ALLOWED_HOSTS = ("wwwn.cdc.gov", "zenodo.org")

# SHA-256 of the exact files the published results were built from. A mismatch means the source
# changed (or the download was tampered with). By default we warn and keep going (these are data files,
# never executed); set SLEEPTWIN_STRICT_DOWNLOADS=1 to reject mismatching files instead.
PINNED_SHA256 = {
    "P_DEMO.xpt": "2e46c6c26bf77cd8989f64011ace12cbf42c0f3e03414eb59acc5328c8f87913",
    "P_BMX.xpt": "7038d0da3169420a4a3cbaec09ac586a701b38e1c7b925431b60e13ac24fed66",
    "P_BPXO.xpt": "5edbcb81e99fe8dad38deb8b642570278b200c525d88ffa29ae3ceb4dd38bde4",
    "P_GHB.xpt": "dac9e423f56041c2ec46486cb16be16d3347e0a81a575985882ffad5a60e1195",
    "P_GLU.xpt": "91b83c46fb4707c431838159135e93693a0572bce54074f5a890f0ee104732b3",
    "P_BIOPRO.xpt": "f242cb9f9da5787f77d81ffb02822350e01cea4adf072d23bc96eb008182010c",
    "P_TCHOL.xpt": "759cd9c408b5d1b91f6cfb5d5e67920a301f7478c0e90ce7adf4bbd277a45ac8",
    "P_HDL.xpt": "04a344f00fe34b3dc4202ee9e47cf61e67d1f985d7c9ece228e25caa85c7fbd7",
    "P_TRIGLY.xpt": "d3eb2df386f24a559ae4db992f0ec9aaf3d2c0caec173aa1921e78100ee88b31",
    "P_SLQ.xpt": "6eb2495efaefddbebe9b39cf2f1fe8d8ce904d80addc1c5da62540921461ae2b",
    "P_DIQ.xpt": "79153f799fc2171792771c4aa250029c62807f14915f1f81405b03233b1e5ae3",
    "P_BPQ.xpt": "88af3557dd185cee2533c94c5302b361e89a54eb50754704f35d4e8120868c02",
    "daily_fitbit_sema_df_unprocessed.csv": "82c84ee495be4b0ff636a8a44271ffb124e2358d9dd52012b529b897f3d54963",
}
STRICT = os.environ.get("SLEEPTWIN_STRICT_DOWNLOADS") == "1"


def _check_url(url: str) -> None:
    from urllib.parse import urlparse
    u = urlparse(url)
    if u.scheme != "https" or not any(u.hostname == h or u.hostname.endswith("." + h) for h in ALLOWED_HOSTS):
        raise RuntimeError(f"refusing non-allow-listed URL: {url}")


def _verify(name: str, data: bytes) -> bool:
    """True if the file matches its pinned hash (or has none)."""
    want = PINNED_SHA256.get(name)
    got = hashlib.sha256(data).hexdigest()
    if want and got != want:
        print(f"    WARNING: {name} checksum differs from the pinned version (source updated or tampered).")
        if STRICT:
            print("    strict mode: file rejected -> simulator will use fallback statistics")
            return False
    return True


def _get(url: str, headers: dict | None = None, timeout: int = 180) -> bytes:
    _check_url(url)
    last = None
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={**UA, **(headers or {})})
            with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310 - https + allow-listed host
                _check_url(r.geturl())  # also after redirects
                data = r.read(MAX_FILE_BYTES + 1)
                if len(data) > MAX_FILE_BYTES:
                    raise RuntimeError("response too large")
                return data
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"failed to fetch {url}: {last}")


def download_nhanes() -> None:
    NHANES_DIR.mkdir(parents=True, exist_ok=True)
    for name in NHANES_FILES:
        out = NHANES_DIR / f"{name}.xpt"
        if out.exists() and out.stat().st_size > 1000:
            print(f"  [skip] {out.name}")
            continue
        print(f"  downloading {name}.xpt ...", flush=True)
        try:
            data = _get(NHANES_BASE + f"{name}.xpt")
            if data[:6] != b"HEADER":  # XPT files start with a SAS header record
                raise RuntimeError("unexpected content (not a SAS XPT file)")
            if not _verify(out.name, data):
                continue
            out.write_bytes(data)
            print(f"    ok ({len(data) / 1e6:.1f} MB)")
        except Exception as e:  # noqa: BLE001
            print(f"    FAILED: {e}")


class _HttpRangeFile(io.RawIOBase):
    """Seekable read-only file over HTTP Range requests (lets zipfile read one member)."""

    def __init__(self, url: str):
        _check_url(url)
        req = urllib.request.Request(url, method="HEAD", headers=UA)
        with urllib.request.urlopen(req, timeout=60) as r:  # noqa: S310
            self.size = int(r.headers["Content-Length"])
            self.url = r.geturl()
        _check_url(self.url)
        self.pos = 0

    def seekable(self):
        return True

    def readable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, offset, whence=0):
        self.pos = offset if whence == 0 else (self.pos + offset if whence == 1 else self.size + offset)
        return self.pos

    def read(self, n=-1):
        if n is None or n < 0:
            n = self.size - self.pos
        if n == 0 or self.pos >= self.size:
            return b""
        end = min(self.size, self.pos + n) - 1
        data = _get(self.url, headers={"Range": f"bytes={self.pos}-{end}"})
        self.pos += len(data)
        return data

    def readinto(self, b):
        data = self.read(len(b))
        b[: len(data)] = data
        return len(data)


def download_lifesnaps() -> None:
    LIFESNAPS_DIR.mkdir(parents=True, exist_ok=True)
    out = LIFESNAPS_DIR / "daily_fitbit_sema_df_unprocessed.csv"
    if out.exists() and out.stat().st_size > 100_000:
        print(f"  [skip] {out.name}")
        return
    print("  extracting LifeSnaps daily CSV from Zenodo archive (range requests) ...", flush=True)
    try:
        f = _HttpRangeFile(LIFESNAPS_URL)
        z = zipfile.ZipFile(io.BufferedReader(f, buffer_size=1 << 20))
        info = z.getinfo(LIFESNAPS_MEMBER)
        if info.file_size > MAX_FILE_BYTES:
            raise RuntimeError("archive member unexpectedly large")
        with z.open(info) as src:
            data = src.read(MAX_FILE_BYTES + 1)
        if not data.startswith(b",id,date") or not _verify(out.name, data):
            raise RuntimeError("unexpected LifeSnaps CSV content")
        out.write_bytes(data)
        print(f"    ok ({out.stat().st_size / 1e6:.1f} MB)")
    except Exception as e:  # noqa: BLE001
        print(f"    FAILED: {e}\n    -> simulator will use LifeSnaps paper ranges instead")


def main() -> int:
    print("NHANES 2017-Mar 2020 (pre-pandemic):")
    download_nhanes()
    print("LifeSnaps (Zenodo 7229547):")
    download_lifesnaps()
    print("done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
