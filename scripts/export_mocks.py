"""Refresh the frozen contract examples in api/mock/ (and web/public/mock/) from the real API."""
import json
import shutil
import sys
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
warnings.filterwarnings("ignore")
from fastapi.testclient import TestClient  # noqa: E402

from api.main import app  # noqa: E402

OUT = ROOT / "api" / "mock"
OUT.mkdir(parents=True, exist_ok=True)
with TestClient(app) as c:
    calls = {
        "patients.json": c.get("/api/patients").json()[:12],
        "patient_A.json": c.get("/api/patients/A").json(),
        "trends_A.json": c.get("/api/patients/A/trends").json(),
        "what_if_A.json": c.post("/api/patients/A/what-if", json={"sleep_hours": 7.5, "bedtime_shift_h": 0,
                                                                 "cpap": False}).json(),
        "model_summary.json": c.get("/api/model/summary").json(),
    }
for name, data in calls.items():
    (OUT / name).write_text(json.dumps(data, indent=1), encoding="utf-8")
    shutil.copy(OUT / name, ROOT / "web" / "public" / "mock" / name)
print("mocks written:", ", ".join(calls))
