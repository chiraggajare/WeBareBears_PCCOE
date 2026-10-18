"""Smoke tests for the simulator, models and API.  Run:  pytest -q
(The pipeline must have been run once: python -m src.pipeline)"""
import json
import time
import warnings

import numpy as np
import pandas as pd
import pytest

warnings.filterwarnings("ignore")

from src import physiology as ph  # noqa: E402
from src.config import MODELS, PROCESSED, PRED_DAYS  # noqa: E402
from src.wearables import night_heart  # noqa: E402


# ---------------------------------------------------------------- physiology
def test_sleep_restriction_lowers_si_about_25pct():
    tst = np.array([[7.5] * 6 + [5.0] * 4])
    debt = ph.sleep_debt(tst, [7.5])[0, -1]
    drop = 1 - np.exp(-ph.A1 * debt)
    assert 0.20 <= drop <= 0.30


def test_debt_is_zero_with_normal_sleep():
    assert ph.sleep_debt(np.array([[8.0] * 10]), [7.5]).max() == 0


def test_lower_si_gives_higher_glucose_peak():
    G = ph.deterministic_day_curve(np.array([130.0, 130.0]), np.array([2.5e-4, 1.8e-4]), np.array([1.5, 1.5]),
                                   np.array([150.0, 150.0]), np.array([[465, 780, 1215]] * 2),
                                   np.array([[60, 60, 60]] * 2))
    assert G.shape == (2, 288)
    assert G[1].max() > G[0].max()


def test_beta_blocker_caps_rhr_rise_but_not_hrv_drop():
    bl = pd.Series({"hrv_base": 40.0, "rhr_base": 62.0})
    args = (np.array([2.5]), np.array([6.8]), np.array([2.0]), np.array([3.0]))
    hrv_bb, rhr_bb = night_heart(bl, *args, True, np.ones(1), np.zeros(1))
    hrv_no, rhr_no = night_heart(bl, *args, False, np.ones(1), np.zeros(1))
    assert rhr_bb[0] - 62 <= 3.0 + 1e-9 < rhr_no[0] - 62
    assert hrv_bb[0] == pytest.approx(hrv_no[0]) and hrv_bb[0] < 40 * 0.75


# ---------------------------------------------------------------- generated data
@pytest.fixture(scope="module")
def daily():
    return pd.read_parquet(PROCESSED / "daily.parquet")


def test_cohort_has_both_streams():
    prof = pd.read_parquet(PROCESSED / "profiles.parquet")
    nights = pd.read_parquet(PROCESSED / "nights.parquet")
    cgm = pd.read_parquet(PROCESSED / "cgm.parquet", columns=["patient_id"])
    assert len(prof) == 300 and {"A", "B", "C"} <= set(prof.patient_id)
    for col in ("hba1c", "t2d_dx_year", "on_metformin", "prs_t2d", "tcf7l2_risk_alleles", "mtnr1b_risk_allele"):
        assert col in prof
    for col in ("tst_hours", "deep_pct", "rem_pct", "hrv_rmssd", "resting_heart_rate", "steps", "odi"):
        assert col in nights
    assert len(cgm) == 300 * 21 * 288


def test_glucose_range_and_event_rate(daily):
    cgm = pd.read_parquet(PROCESSED / "cgm.parquet", columns=["glucose_noisy"])
    assert cgm.glucose_noisy.min() >= 40 and cgm.glucose_noisy.max() <= 400
    assert 0.15 <= daily[daily.day.isin(PRED_DAYS)].glucose_event_24h.mean() <= 0.30


# ---------------------------------------------------------------- leakage
def test_no_patient_in_both_train_and_test():
    fold_of = json.loads((MODELS / "folds.json").read_text(encoding="utf-8"))
    feats = pd.read_parquet(PROCESSED / "features_nextday.parquet", columns=["patient_id"])
    # every patient maps to exactly one fold -> each fold's test set is disjoint from its train set
    assert set(feats.patient_id) <= set(fold_of)
    folds = pd.Series(fold_of)
    assert folds.nunique() == 5
    for k in range(5):
        test = set(folds[folds == k].index)
        train = set(folds[folds != k].index)
        assert not test & train


# ---------------------------------------------------------------- API
@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient

    from api.main import app
    with TestClient(app) as c:
        yield c


def test_patients_sorted_by_risk(client):
    r = client.get("/api/patients").json()
    keys = [max(p["risk"], p["bp_risk"]) for p in r]
    assert keys == sorted(keys, reverse=True)
    assert {"id", "name", "conditions", "risk", "risk_level", "bp_risk", "spike_2h_risk", "top_reason"} <= set(r[0])


def test_personas_land_in_expected_bands(client):
    lv = {p: client.get(f"/api/patients/{p}").json()["risk_level"] for p in "ABC"}
    assert lv == {"A": "critical", "B": "warning", "C": "stable"}


def test_patient_detail_contract(client):
    d = client.get("/api/patients/A").json()
    for k in ("profile", "risk", "bp_risk", "risk_level", "reasons", "spike_2h", "data_quality"):
        assert k in d
    assert d["profile"]["genetic_markers"]["simulated"] is True
    assert d["spike_2h"]["alert"] is True
    assert "Research prototype" in d["disclaimer"]


def test_trends_contract(client):
    t = client.get("/api/patients/B/trends").json()
    assert len(t["days"]) == 21 and len(t["days"][0]["tst_band"]) == 2
    assert len(t["cgm_48h"]) == 576 and t["hypnogram"]["stages"]


def test_what_if_persona_a_recovers_fast(client):
    t0 = time.perf_counter()
    w = client.post("/api/patients/A/what-if", json={"sleep_hours": 7.5, "bedtime_shift_h": 0, "cpap": False}).json()
    assert (time.perf_counter() - t0) < 0.3
    assert w["risk_after"] < w["risk_before"] and w["level_after"] == "stable"
    assert len(w["glucose_before"]) == len(w["glucose_after"]) == 288
    assert max(w["glucose_after"]) < max(w["glucose_before"])


def test_what_if_cpap_helps_persona_b(client):
    w = client.post("/api/patients/B/what-if", json={"sleep_hours": 7.2, "bedtime_shift_h": 0, "cpap": True}).json()
    assert w["bp_after"] < w["bp_before"]


def test_unknown_id_and_bad_input(client):
    assert client.get("/api/patients/NOPE").status_code == 404
    assert client.get("/api/patients/NOPE/trends").status_code == 404
    assert client.post("/api/patients/A/what-if", json={"sleep_hours": 30}).status_code == 422
