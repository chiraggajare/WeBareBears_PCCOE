"""Security & portability tests.  Run:  pytest -q"""
import json
import warnings

import pytest

warnings.filterwarnings("ignore")

from src.config import MODELS  # noqa: E402
from src.integrity import IntegrityError, verify  # noqa: E402


@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient

    from api.main import app
    with TestClient(app) as c:
        yield c


def test_security_headers_on_api_and_pages(client):
    for path in ("/api/patients/A", "/", "/patients/A"):
        h = client.get(path).headers
        assert h["x-content-type-options"] == "nosniff"
        assert h["x-frame-options"] == "DENY"
        assert h["referrer-policy"] == "no-referrer"
        assert "frame-ancestors 'none'" in h["content-security-policy"]
        assert "default-src 'self'" in h["content-security-policy"]
        assert "server" not in {k.lower() for k in h} or "uvicorn" not in h.get("server", "")
    assert client.get("/api/patients").headers["cache-control"] == "no-store"


def test_cors_only_allows_listed_origins(client):
    ok = client.get("/api/health", headers={"Origin": "http://localhost:5173"})
    assert ok.headers.get("access-control-allow-origin") == "http://localhost:5173"
    bad = client.get("/api/health", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in bad.headers


@pytest.mark.parametrize("path", [
    "/..%2F..%2Fsrc%2Fconfig.py",
    "/%2E%2E/%2E%2E/README.md",
    "/assets/..%2F..%2F..%2Fsrc%2Fconfig.py",
    "/..%5C..%5Csrc%5Cconfig.py",
])
def test_no_path_traversal(client, path):
    r = client.get(path)
    assert "SEED = 2026" not in r.text and "# SleepTwin" not in r.text


@pytest.mark.parametrize("pid", ["A<script>", "..%2F..%2Fetc", "x" * 40, "A B", "A%00"])
def test_patient_id_is_validated(client, pid):
    r = client.get(f"/api/patients/{pid}")
    assert r.status_code in (404, 422)
    assert "Traceback" not in r.text


@pytest.mark.parametrize("body", [
    {"sleep_hours": 7.5, "bedtime_shift_h": 0, "cpap": False, "evil": 1},     # unknown field
    {"sleep_hours": "inf", "bedtime_shift_h": 0, "cpap": False},             # non-finite
    {"sleep_hours": "nan", "bedtime_shift_h": 0, "cpap": False},
    {"sleep_hours": 7.5, "bedtime_shift_h": 99, "cpap": False},              # out of range
    {"sleep_hours": 7.5, "bedtime_shift_h": 0, "cpap": False, "nights": 50},
])
def test_what_if_rejects_bad_input(client, body):
    r = client.post("/api/patients/A/what-if", json=body)
    assert r.status_code == 422
    assert r.json()["detail"] == "Invalid input"


def test_oversized_body_rejected(client):
    r = client.post("/api/patients/A/what-if", content=b"{" + b" " * 10_000 + b"}",
                    headers={"Content-Type": "application/json"})
    assert r.status_code == 413


def test_unknown_api_route_is_404_json(client):
    r = client.get("/api/does-not-exist")
    assert r.status_code == 404 and r.json()["detail"] == "not found"


def test_report_files_are_allow_listed(client):
    assert client.get("/api/reports/results.md").status_code == 200
    assert client.get("/api/reports/nextday_metrics.json").status_code == 404
    assert client.get("/api/reports/..%2F..%2FREADME.md").status_code == 404


def test_rate_limiter():
    from api.main import RateLimiter
    rl = RateLimiter(3)
    assert [rl.allow("1.2.3.4") for _ in range(4)] == [True, True, True, False]
    assert rl.allow("5.6.7.8")


def test_model_integrity_checks(tmp_path):
    assert verify(MODELS / "folds.json")  # untouched file passes
    outside = tmp_path / "evil.joblib"
    outside.write_bytes(b"x")
    with pytest.raises(IntegrityError):
        verify(outside)                    # not in models/
    rogue = MODELS / "zz_unlisted_test.joblib"
    rogue.write_bytes(b"x")
    try:
        with pytest.raises(IntegrityError):
            verify(rogue)                  # not in the manifest
    finally:
        rogue.unlink()
    manifest = json.loads((MODELS / "manifest.json").read_text(encoding="utf-8"))
    assert all(len(v) == 64 for v in manifest.values())


def test_text_outputs_are_utf8():
    from src.config import REPORTS
    (REPORTS / "results.md").read_text(encoding="utf-8")  # would raise on a bad encoding


def test_head_requests_work_for_pages(client):
    assert client.head("/").status_code == 200
    assert client.head("/patients/A").status_code == 200
