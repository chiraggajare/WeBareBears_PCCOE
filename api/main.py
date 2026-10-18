"""SleepTwin API (FastAPI).

Run (any OS):   python run.py            or   uvicorn api.main:app --port 8000
Docs:           http://127.0.0.1:8000/docs   (disable with SLEEPTWIN_ENABLE_DOCS=0)

Frozen contract (plan Section 8):
  GET  /api/patients                    list sorted by risk
  GET  /api/patients/{id}               profile, risks, reasons, 2-hour alert, data quality
  GET  /api/patients/{id}/trends        21 days + personal-normal bands, last-night hypnogram, last 48 h CGM
  POST /api/patients/{id}/what-if       {sleep_hours, bedtime_shift_h, cpap} -> before/after risk + curves
  GET  /api/model/summary               ablation, 2-hour metrics, LifeSnaps validation, data card
If web/dist exists (npm run build), the React app is served from / as well.

Security measures (research prototype, simulated data only - still built safely):
  * strict input validation (patient-id pattern, bounded/finite What-If numbers, unknown fields rejected)
  * security headers (CSP, no framing, no MIME sniffing, no referrer leakage, permissions policy)
  * CORS limited to an allow-list (SLEEPTWIN_CORS_ORIGINS), read-only methods + POST for What-If
  * per-client rate limit on the compute endpoint (What-If)
  * request-body size cap, path-traversal-safe static file serving, allow-listed report files
  * generic error messages (no stack traces), no server banner, model files verified by SHA-256
"""
from __future__ import annotations

import logging
import os
import sys
import threading
import time
import warnings
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Path as PathParam, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field
from starlette.middleware.base import BaseHTTPMiddleware

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
warnings.filterwarnings("ignore")

from src.config import DISCLAIMER, REPORTS  # noqa: E402
from src.twin import get_twin  # noqa: E402

log = logging.getLogger("sleeptwin")

# ------------------------------------------------------------------ settings (env-configurable)
def _env_list(name: str, default: str) -> list[str]:
    return [x.strip() for x in os.environ.get(name, default).split(",") if x.strip()]


CORS_ORIGINS = _env_list("SLEEPTWIN_CORS_ORIGINS",
                         "http://localhost:5173,http://127.0.0.1:5173,http://localhost:8000,http://127.0.0.1:8000")
ENABLE_DOCS = os.environ.get("SLEEPTWIN_ENABLE_DOCS", "1") != "0"
RATE_LIMIT_PER_MIN = int(os.environ.get("SLEEPTWIN_WHATIF_RATE_PER_MIN", "120"))
MAX_BODY_BYTES = 4096
PATIENT_ID = r"^[A-Za-z0-9_-]{1,16}$"

CSP = ("default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
       "font-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'self'; form-action 'self'; "
       "frame-ancestors 'none'")
# Swagger UI at /docs loads its assets from a CDN, so it gets a slightly wider policy
DOCS_CSP = ("default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; img-src 'self' data: https://fastapi.tiangolo.com; "
            "connect-src 'self'; object-src 'none'; frame-ancestors 'none'")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    get_twin()  # load cohort + models once at startup (verifies model checksums)
    yield


app = FastAPI(title="SleepTwin API", version="1.1.0", lifespan=lifespan,
              docs_url="/docs" if ENABLE_DOCS else None, redoc_url=None,
              openapi_url="/openapi.json" if ENABLE_DOCS else None,
              description="Sleep-driven cardiometabolic digital twin (T2D + HTN). SIMULATED data. " + DISCLAIMER)


# ------------------------------------------------------------------ middleware
class SecurityHeaders(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        cl = request.headers.get("content-length")
        if cl and cl.isdigit() and int(cl) > MAX_BODY_BYTES:
            return JSONResponse({"detail": "Request body too large"}, status_code=413)
        resp = await call_next(request)
        path = request.url.path
        h = resp.headers
        h["X-Content-Type-Options"] = "nosniff"
        h["X-Frame-Options"] = "DENY"
        h["Referrer-Policy"] = "no-referrer"
        h["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), payment=(), usb=()"
        h["Cross-Origin-Opener-Policy"] = "same-origin"
        h["Content-Security-Policy"] = DOCS_CSP if path.startswith("/docs") else CSP
        if path.startswith("/api/"):
            h["Cache-Control"] = "no-store"
        return resp


class RateLimiter:
    """Sliding-window limiter per client IP (in memory; enough for a single-process prototype)."""

    def __init__(self, per_minute: int):
        self.per_minute = per_minute
        self.hits: dict[str, deque] = defaultdict(deque)
        self.lock = threading.Lock()

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        with self.lock:
            q = self.hits[key]
            while q and now - q[0] > 60:
                q.popleft()
            if len(q) >= self.per_minute:
                return False
            q.append(now)
            if len(self.hits) > 10_000:  # bound memory
                self.hits.clear()
            return True


limiter = RateLimiter(RATE_LIMIT_PER_MIN)

app.add_middleware(SecurityHeaders)
app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS, allow_methods=["GET", "POST"],
                   allow_headers=["Content-Type"], allow_credentials=False, max_age=600)


# ------------------------------------------------------------------ error handling (no internals leaked)
@app.exception_handler(RequestValidationError)
async def _validation_error(_req: Request, exc: RequestValidationError):
    fields = [".".join(str(p) for p in e.get("loc", []) if p != "body") for e in exc.errors()]
    return JSONResponse({"detail": "Invalid input", "fields": [f for f in fields if f]}, status_code=422)


@app.exception_handler(Exception)
async def _unhandled(_req: Request, exc: Exception):
    log.exception("unhandled error: %s", exc)
    return JSONResponse({"detail": "Internal error"}, status_code=500)


# ------------------------------------------------------------------ models
class WhatIfRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sleep_hours: float = Field(7.5, ge=3.0, le=10.0, allow_inf_nan=False,
                               description="Sleep duration for the scenario night(s)")
    bedtime_shift_h: float = Field(0.0, ge=-2.0, le=4.0, allow_inf_nan=False,
                                   description="Bedtime vs usual (hours; + = later)")
    cpap: bool = Field(False, description="CPAP for sleep apnea: ODI x 0.2, WASO x 0.6")
    nights: int = Field(1, ge=1, le=4, description="How many of the most recent nights the scenario covers")


PidParam = PathParam(..., pattern=PATIENT_ID, description="Patient id, e.g. A, B, C or P001")


def _twin_or_404(pid: str):
    t = get_twin()
    if not t.exists(pid):
        raise HTTPException(status_code=404, detail="Unknown patient id")
    return t


# ------------------------------------------------------------------ routes
@app.get("/api/health")
def health():
    t = get_twin()
    return {"status": "ok", "patients": len(t.profiles), "load_seconds": t.load_seconds, "simulated": True}


@app.get("/api/patients")
def patients():
    return get_twin().patient_list()


@app.get("/api/patients/{pid}")
def patient(pid: str = PidParam):
    return _twin_or_404(pid).patient_detail(pid)


@app.get("/api/patients/{pid}/trends")
def trends(pid: str = PidParam):
    return _twin_or_404(pid).trends(pid)


@app.post("/api/patients/{pid}/what-if")
def what_if(req: WhatIfRequest, request: Request, pid: str = PidParam):
    client = request.client.host if request.client else "unknown"
    if not limiter.allow(client):
        raise HTTPException(status_code=429, detail="Too many What-If requests - slow down")
    return _twin_or_404(pid).what_if(pid, req.sleep_hours, req.bedtime_shift_h, req.cpap, req.nights)


@app.get("/api/model/summary")
def model_summary():
    return get_twin().model_summary()


REPORT_FILES = {"results.md", "lifesnaps_boxplot.png"}


@app.get("/api/reports/{name}")
def report_file(name: str):
    if name not in REPORT_FILES or not (REPORTS / name).is_file():
        raise HTTPException(status_code=404, detail="not found")
    return FileResponse(REPORTS / name)


@app.api_route("/api/{rest:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"], include_in_schema=False)
def api_404(rest: str):
    raise HTTPException(status_code=404, detail="not found")


# ------------------------------------------------------------------ built frontend (single-command demo)
DIST = (ROOT / "web" / "dist").resolve()
if (DIST / "index.html").exists():
    if (DIST / "assets").is_dir():
        app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    @app.api_route("/{path:path}", methods=["GET", "HEAD"], include_in_schema=False)
    def spa(path: str):
        candidate = (DIST / path).resolve()
        # only serve real files that live inside web/dist (blocks ../ traversal); everything else -> SPA
        if path and candidate.is_file() and candidate.is_relative_to(DIST):
            return FileResponse(candidate)
        return FileResponse(DIST / "index.html")
