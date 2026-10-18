"""Simulated wearable stream (dynamic / real-time): sleep stages, HRV, resting HR, steps, SpO2 dips.

Each virtual patient is matched to a real LifeSnaps (Fitbit) volunteer and inherits
that person's typical sleep duration, efficiency, WASO, RMSSD, resting HR and steps,
then adjusted for the patient's age, BMI, diabetes status and medication.

Realism rules (plan 6.2):
* stress episodes: 2-4 consecutive short nights and/or late-bedtime runs
* OSA patients: higher ODI and WASO, lower deep %
* beta-blocker masking: RHR rise capped at about +3 bpm while the HRV drop stays visible
* ~5% missing nights (watch not worn) - CGM dropout is added in generate_cohort.py

Night d = the sleep that ends on the morning of day d. Stage percentages are drawn from
published adult polysomnography ranges (deep ~10-25%, REM ~18-25%) because the LifeSnaps
daily export only stores stage *ratios versus a 30-day average*.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .calibration import load_lifesnaps_ranges
from .config import N_DAYS, SEED
from .physiology import sleep_debt

EPOCH_MIN = 5
MISSING_NIGHT_RATE = 0.05


def personal_baselines(profiles: pd.DataFrame, seed: int = SEED) -> tuple[pd.DataFrame, str]:
    rng = np.random.default_rng(seed + 1)
    ls, source = load_lifesnaps_ranges()
    n = len(profiles)
    pick = ls.iloc[rng.integers(0, len(ls), n)].reset_index(drop=True)
    age = profiles.age.to_numpy(float)
    bmi = profiles.bmi.to_numpy(float)
    t2d = profiles.has_t2d.to_numpy()
    bb = profiles.on_beta_blocker.to_numpy()
    osa = profiles.has_osa_true.to_numpy()

    b = pd.DataFrame({"patient_id": profiles.patient_id})
    b["lifesnaps_ref"] = pick["id"].astype(str).str[-6:]
    b["tst_base"] = np.clip(pick.tst_mean + rng.normal(0.25, 0.3, n), 5.6, 8.4)
    b["tst_sd"] = np.clip(pick.tst_sd * 0.45, 0.3, 0.8)
    b["waso_base"] = np.clip(pick.waso_mean * 0.6 + 0.25 * (age - 30), 15, 90)
    b["hrv_base"] = np.clip(pick.hrv_mean * np.exp(-0.018 * (age - 28)) * np.where(t2d, 0.82, 1.0), 12, 110)
    b["hrv_cv"] = np.clip(pick.hrv_sd / pick.hrv_mean, 0.06, 0.16)
    b["rhr_base"] = np.clip(pick.rhr_mean + 0.25 * (bmi - 24) + np.where(t2d, 3, 0) - np.where(bb, 8, 0), 46, 90)
    b["rhr_sd"] = np.clip(pick.rhr_sd * 0.6, 0.8, 2.2)
    b["steps_base"] = np.clip(pick.steps_mean * (1 - 0.012 * (bmi - 25)) * np.where(age > 60, 0.8, 1.0),
                              2500, 17000)
    b["steps_cv"] = np.clip(pick.steps_sd / pick.steps_mean * 0.6, 0.12, 0.35)
    b["deep_base"] = np.clip(rng.normal(17, 3, n) - 0.08 * (age - 30) - np.where(osa, 5, 0), 5, 26)
    b["rem_base"] = np.clip(rng.normal(21, 2.5, n), 14, 27)
    odi_norm = np.clip(rng.lognormal(np.log(2.0 + 0.04 * np.maximum(0, age - 30) + 0.08 * np.maximum(0, bmi - 25)),
                                     0.35, n), 0.5, 8)
    odi_osa = np.clip(rng.lognormal(np.log(18), 0.35, n), 10, 45)
    b["odi_base"] = np.where(osa, odi_osa, odi_norm)
    b["waso_base"] = b.waso_base + np.where(osa, rng.uniform(25, 45, n), 0)
    b["bedtime_usual_min"] = np.round(rng.normal(22.75 * 60, 40, n))  # minutes after midnight of previous day
    return b, source


def _episodes(rng, n_nights):
    """Return per-night (tst_cut_h, bedtime_shift_h) for random stress episodes."""
    cut = np.zeros(n_nights)
    shift = np.zeros(n_nights)
    k = rng.choice([0, 1, 2, 3], p=[0.15, 0.40, 0.33, 0.12])
    for _ in range(k):
        length = int(rng.integers(2, 5))
        start = int(rng.integers(2, n_nights - 1))
        sl = slice(start, min(n_nights, start + length))
        kind = rng.random()
        if kind < 0.5:                     # short-sleep run
            cut[sl] += rng.uniform(1.3, 3.0)
        elif kind < 0.8:                   # late-bedtime run (partly compensated)
            s = rng.uniform(1.5, 3.0)
            shift[sl] += s
            cut[sl] += 0.55 * s
        else:                              # both
            s = rng.uniform(1.0, 2.0)
            shift[sl] += s
            cut[sl] += rng.uniform(1.2, 2.2)
    return cut, shift


def simulate_nights(profiles: pd.DataFrame, base: pd.DataFrame, seed: int = SEED,
                    overrides: dict | None = None) -> pd.DataFrame:
    """Nightly summaries for nights 0..N_DAYS-1 plus next-day steps. Returns long table."""
    rng = np.random.default_rng(seed + 2)
    overrides = overrides or {}
    rows = []
    for i, p in profiles.reset_index(drop=True).iterrows():
        bl = base.iloc[i]
        pid = p.patient_id
        cut, shift = _episodes(rng, N_DAYS)
        ar = np.zeros(N_DAYS)
        for d in range(N_DAYS):
            ar[d] = (0.3 * ar[d - 1] if d else 0) + rng.normal(0, bl.tst_sd)
        tst = np.clip(bl.tst_base + ar - cut, 3.0, 10.5)
        bedtime_shift = shift + rng.normal(0, 0.35, N_DAYS)
        waso = np.clip(bl.waso_base * rng.lognormal(0, 0.22, N_DAYS), 5, 200)
        odi = np.clip(bl.odi_base * rng.lognormal(0, 0.2, N_DAYS), 0.2, 80)
        steps_noise = rng.lognormal(0, bl.steps_cv, N_DAYS)
        hrv_noise = rng.lognormal(0, bl.hrv_cv, N_DAYS)
        rhr_noise = rng.normal(0, bl.rhr_sd, N_DAYS)
        deep_noise = rng.normal(0, 2.0, N_DAYS)
        rem_noise = rng.normal(0, 2.0, N_DAYS)
        missing = rng.random(N_DAYS) < MISSING_NIGHT_RATE

        if pid in overrides:  # persona scripting
            o = overrides[pid]
            for key, arr in (("tst", tst), ("bedtime_shift", bedtime_shift), ("waso", waso), ("odi", odi)):
                for d, v in o.get(key, {}).items():
                    arr[d] = v
            missing[:] = False
            for d, v in o.get("hrv_noise", {}).items():
                hrv_noise[d] = v
            for d, v in o.get("rhr_noise", {}).items():
                rhr_noise[d] = v

        n = dict(tst=tst, bedtime_shift=bedtime_shift, waso=waso, odi=odi)
        rows.append(_derive(pid, p, bl, n, hrv_noise, rhr_noise, steps_noise, deep_noise, rem_noise, missing))
    return pd.concat(rows, ignore_index=True)


def _derive(pid, p, bl, n, hrv_noise, rhr_noise, steps_noise, deep_noise, rem_noise, missing):
    tst, shift, waso, odi = n["tst"], n["bedtime_shift"], n["waso"], n["odi"]
    deficit = np.maximum(0, bl.tst_base - tst)
    debt = sleep_debt(tst[None, :], [bl.tst_base])[0]
    hrv, rhr = night_heart(bl, deficit, debt, shift, odi, bool(p.on_beta_blocker), hrv_noise, rhr_noise)
    sol = 12 + 4 * np.abs(shift)
    eff = tst * 60 / (tst * 60 + waso + sol)
    deep = np.clip(bl.deep_base + deep_noise - 0.15 * (odi - bl.odi_base), 3, 30)
    rem = np.clip(bl.rem_base + rem_noise - 1.5 * np.maximum(0, deficit - 1), 8, 30)
    steps = np.clip(bl.steps_base * (1 - 0.05 * deficit) * steps_noise, 300, 40000)
    df = pd.DataFrame({
        "patient_id": pid, "day": np.arange(N_DAYS),
        "tst_hours": tst, "efficiency": eff, "deep_pct": deep, "rem_pct": rem, "waso_min": waso,
        "bedtime_shift_h": shift, "bedtime_min": bl.bedtime_usual_min + shift * 60,
        "hrv_rmssd": hrv, "resting_heart_rate": rhr, "odi": odi, "steps": np.round(steps),
        "night_missing": missing,
    })
    # truth (used by physiology) kept separately from what the watch reports
    for c in ("tst_hours", "efficiency", "deep_pct", "rem_pct", "waso_min", "bedtime_shift_h", "hrv_rmssd",
              "resting_heart_rate", "odi"):
        df[c + "_true"] = df[c]
    obs_cols = ["tst_hours", "efficiency", "deep_pct", "rem_pct", "waso_min", "bedtime_shift_h", "hrv_rmssd",
                "resting_heart_rate", "odi"]
    df.loc[missing, obs_cols] = np.nan
    return df


def night_heart(bl, deficit, debt, shift, odi, beta_blocker, hrv_noise, rhr_noise):
    """Autonomic response to a night: HRV falls and RHR rises with sleep loss / mistiming / hypoxia."""
    excess_odi = np.maximum(0, odi - 5)
    hrv = bl.hrv_base * np.exp(-0.06 * deficit - 0.02 * debt - 0.05 * np.abs(shift) - 0.004 * excess_odi) * hrv_noise
    rise = 1.1 * deficit + 0.35 * debt + 0.06 * excess_odi + 0.4 * np.abs(shift)
    if beta_blocker:
        rise = np.minimum(rise, 3.0)       # beta-blocker masking
        rhr_noise = rhr_noise * 0.6
    return np.clip(hrv, 5, 200), np.clip(bl.rhr_base + rise + rhr_noise, 38, 120)


# ------------------------------------------------------------------- hypnogram (5-min epochs)
def hypnogram(tst_h, waso_min, deep_pct, rem_pct, sol_min, rng) -> str:
    """Build a stage string (W/L/D/R per 5-min epoch) with ~90-min cycles:
    deep sleep front-loaded, REM growing across the night, wake bouts scattered."""
    n_sleep = max(6, int(round(tst_h * 60 / EPOCH_MIN)))
    n_cycles = max(2, int(round(n_sleep / 18)))
    w_deep = np.linspace(1.8, 0.1, n_cycles)
    w_rem = np.linspace(0.5, 1.6, n_cycles)
    deep_total = int(round(n_sleep * deep_pct / 100))
    rem_total = int(round(n_sleep * rem_pct / 100))
    deep_c = np.floor(w_deep / w_deep.sum() * deep_total).astype(int)
    rem_c = np.floor(w_rem / w_rem.sum() * rem_total).astype(int)
    per = n_sleep // n_cycles
    seq = []
    for c in range(n_cycles):
        length = per if c < n_cycles - 1 else n_sleep - per * (n_cycles - 1)
        d, r = min(deep_c[c], max(0, length - 2)), 0
        r = min(rem_c[c], max(0, length - 2 - d))
        light = length - d - r
        l1 = max(1, light // 2)
        seq += ["L"] * l1 + ["D"] * d + ["L"] * (light - l1) + ["R"] * r
    seq = seq[:n_sleep]
    n_wake = int(round(waso_min / EPOCH_MIN))
    for _ in range(n_wake):
        pos = int(rng.integers(3, len(seq)))
        seq.insert(pos, "W")
    return "W" * max(1, int(round(sol_min / EPOCH_MIN))) + "".join(seq)


def build_hypnograms(nights: pd.DataFrame, seed: int = SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed + 3)
    out = []
    for r in nights.itertuples(index=False):
        sol = 12 + 4 * abs(r.bedtime_shift_h_true)
        stages = hypnogram(r.tst_hours_true, r.waso_min_true, r.deep_pct_true, r.rem_pct_true, sol, rng)
        out.append((r.patient_id, r.day, float(r.bedtime_min), stages, bool(r.night_missing)))
    return pd.DataFrame(out, columns=["patient_id", "day", "bedtime_min", "stages", "night_missing"])


# --------------------------------------------------------------------------- personas
def persona_overrides(base: pd.DataFrame) -> dict:
    """Script the three demo stories on top of each persona's own baseline."""
    b = base.set_index("patient_id")
    ov = {}
    # A: steady 7.4 h, then 4 nights of ~5 h with bedtime +2 h (nights 17-20 = days 18-21)
    ta = b.loc["A", "tst_base"]
    ov["A"] = {
        "tst": {d: ta + v for d, v in zip(range(17), [0.1, -0.2, 0.0, 0.2, -0.1, 0.1, 0.0, -0.2, 0.1, 0.0,
                                                          0.2, -0.1, 0.0, 0.1, -0.2, 0.0, 0.1])}
        | {17: 5.1, 18: 4.9, 19: 5.0, 20: 5.0},
        "bedtime_shift": {d: 0.0 for d in range(17)} | {17: 1.8, 18: 2.1, 19: 2.0, 20: 2.2},
        "waso": {d: 30.0 for d in range(21)},
        "hrv_noise": dict(enumerate(np.tile([1.03, 0.97, 1.01, 0.98, 1.04, 0.96, 1.0], 3))),
        "rhr_noise": dict(enumerate(np.tile([0.4, -0.3, 0.2, -0.5, 0.3, 0.0, -0.2], 3))),
    }
    # B: sleeps 7.2 h every night but WASO ~78 min and ~20 dips/hr (undiagnosed OSA)
    ov["B"] = {
        "tst": {d: 7.2 + v for d, v in enumerate(np.tile([0.1, -0.1, 0.0, 0.15, -0.15, 0.05, -0.05], 3))},
        "bedtime_shift": {d: 0.0 for d in range(21)},
        "waso": {d: 78.0 + v for d, v in enumerate(np.tile([4, -3, 2, -5, 3, 0, -1], 3))},
        "odi": {d: 22.0 + v for d, v in enumerate(np.tile([1.5, -1, 0.5, -2, 1, 0, -0.5], 3))},
    }
    # C: healthy runner, one bad 4.5 h night (the last one)
    tc = b.loc["C", "tst_base"]
    ov["C"] = {
        "tst": {d: tc + v for d, v in enumerate(np.tile([0.1, -0.2, 0.0, 0.2, -0.1, 0.1, 0.0], 3)[:20])}
        | {20: 4.5},
        "bedtime_shift": {d: 0.0 for d in range(20)} | {20: 0.5},
        "waso": {d: 22.0 for d in range(21)},
    }
    return ov


def apply_persona_baselines(base: pd.DataFrame) -> pd.DataFrame:
    base = base.copy()
    idx = base.patient_id
    sets = {
        "A": dict(tst_base=7.4, tst_sd=0.3, hrv_base=38.0, hrv_cv=0.06, rhr_base=62.0, rhr_sd=1.0,
                  steps_base=6500, steps_cv=0.15, deep_base=14, rem_base=20, odi_base=3.0, waso_base=30,
                  bedtime_usual_min=22.5 * 60),
        "B": dict(tst_base=7.2, tst_sd=0.2, hrv_base=34.0, hrv_cv=0.08, rhr_base=74.0, rhr_sd=1.2,
                  steps_base=5200, steps_cv=0.15, deep_base=9, rem_base=19, odi_base=22.0, waso_base=78,
                  bedtime_usual_min=23 * 60),
        "C": dict(tst_base=7.8, tst_sd=0.3, hrv_base=78.0, hrv_cv=0.08, rhr_base=50.0, rhr_sd=1.2,
                  steps_base=14500, steps_cv=0.15, deep_base=20, rem_base=23, odi_base=1.0, waso_base=22,
                  bedtime_usual_min=22.75 * 60),
    }
    for pid, vals in sets.items():
        for k, v in vals.items():
            base.loc[idx == pid, k] = v
    return base
