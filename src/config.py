"""Shared paths and constants for SleepTwin."""
from __future__ import annotations

import datetime as dt
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW = DATA / "raw"
PROCESSED = DATA / "processed"
MODELS = ROOT / "models"
REPORTS = ROOT / "reports"

for _p in (PROCESSED, MODELS, REPORTS):
    _p.mkdir(parents=True, exist_ok=True)

SEED = 2026
N_PATIENTS = 300            # includes the 3 hand-crafted demo personas
N_DAYS = 21                 # days 0..20  (shown as day 1..21)
BASELINE_DAYS = 14          # days 0..13 learn the personal normal
PRED_DAYS = list(range(14, 21))   # prediction days 15..21 (0-indexed 14..20)
CGM_STEP_MIN = 5
SAMPLES_PER_DAY = 24 * 60 // CGM_STEP_MIN   # 288
START_DATE = dt.date(2026, 9, 27)  # day index 0 -> day index 20 = 2026-10-17
CURRENT_YEAR = 2026
NOW_MINUTE = 13 * 60        # dashboard snapshot: day 21 at 13:00 (2-hour alert evaluated here)

GLUCOSE_THRESHOLD = 180.0   # mg/dL
SBP_THRESHOLD = 145.0       # mmHg
SPIKE_2H_HORIZON = 120      # minutes

# risk bands (applied to max(glucose risk, BP risk))
CRITICAL = 0.75
WARNING = 0.40

PERSONA_IDS = ("A", "B", "C")

DISCLAIMER = "Model-based projection for clinical decision support. Research prototype."


def day_date(day_idx: int) -> dt.date:
    return START_DATE + dt.timedelta(days=int(day_idx))


def risk_level(p: float) -> str:
    if p >= CRITICAL:
        return "critical"
    if p >= WARNING:
        return "warning"
    return "stable"
