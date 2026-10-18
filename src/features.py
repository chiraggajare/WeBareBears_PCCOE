"""Next-day feature engineering (plan Section 7).

For a target day d the twin has seen night d (the sleep that ended this morning) and CGM up
to the end of day d-1. It forecasts day d's CGM peak > 180 mg/dL (and morning SBP > 145).

Personal baseline = days 1-14 (index 0..13): mean/SD of each wearable signal per patient.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .config import BASELINE_DAYS, GLUCOSE_THRESHOLD, PROCESSED, SAMPLES_PER_DAY
from .physiology import DECAY

EHR_FEATURES = [
    "age", "bmi", "hba1c", "egfr", "ldl", "sbp_clinic", "years_since_t2d_dx", "has_t2d", "has_htn", "has_osa",
    "on_metformin", "on_sglt2i", "on_sulfonylurea", "on_beta_blocker", "on_ace_inhibitor",
]
GENETIC_FEATURES = ["prs_t2d", "tcf7l2_risk_alleles", "mtnr1b_risk_allele"]
WEARABLE_FEATURES = [
    # personal-baseline deviations
    "tst_z", "hrv_z", "rhr_delta", "eff_delta", "odi_z", "cgm_mean_z",
    # sleep dynamics
    "sleep_debt_7d", "short_nights_4d", "bedtime_shift", "waso_3d_mean", "deep_pct_7d_slope", "odi_last",
    # CGM context
    "tir_prev_24h", "cgm_cv_24h", "cgm_max_prev_24h",
    # activity
    "steps_prev", "steps_z",
    # data quality
    "missing_nights_7d", "cgm_missing_pct_24h",
]
INTERACTION_FEATURES = ["debt_x_hba1c", "odi_x_has_htn", "hrv_drop_x_beta_blocker", "bedtime_shift_x_mtnr1b"]

FEATURE_SETS = {
    "ehr_only": EHR_FEATURES + GENETIC_FEATURES,
    "wearables_only": WEARABLE_FEATURES,
    "fused": EHR_FEATURES + GENETIC_FEATURES + WEARABLE_FEATURES + INTERACTION_FEATURES,
}
# monotone constraints keep What-If behaviour physiologically sensible
MONOTONE = {"sleep_debt_7d": 1, "short_nights_4d": 1, "tst_z": -1, "hrv_z": -1, "bedtime_shift": 1,
            "odi_z": 1, "odi_last": 1, "waso_3d_mean": 1, "hba1c": 1, "debt_x_hba1c": 1, "odi_x_has_htn": 1,
            "hrv_drop_x_beta_blocker": 1, "bedtime_shift_x_mtnr1b": 1}

SIGNALS = {"tst": "tst_hours", "hrv": "hrv_rmssd", "rhr": "resting_heart_rate", "eff": "efficiency",
           "odi": "odi", "steps": "steps", "waso": "waso_min", "deep": "deep_pct"}


# ------------------------------------------------------------------ CGM daily aggregates
def cgm_daily(cgm: pd.DataFrame) -> pd.DataFrame:
    g = cgm.groupby(["patient_id", "day"]).glucose_mg_dl
    out = pd.DataFrame({
        "cgm_mean": g.mean(), "cgm_max": g.max(), "cgm_sd": g.std(),
        "tir": g.apply(lambda s: float(((s >= 70) & (s <= GLUCOSE_THRESHOLD)).sum() / max(1, s.notna().sum()))),
        "cgm_missing_pct": g.apply(lambda s: float(s.isna().mean())),
    }).reset_index()
    out["cgm_cv"] = out.cgm_sd / out.cgm_mean
    return out


# ------------------------------------------------------------------ personal baselines
def baseline_stats(nights: pd.DataFrame, cgmd: pd.DataFrame) -> pd.DataFrame:
    b = nights[nights.day < BASELINE_DAYS].groupby("patient_id")
    stats = {}
    for k, col in SIGNALS.items():
        stats[f"{k}_mean"] = b[col].mean()
        stats[f"{k}_sd"] = b[col].std()
    s = pd.DataFrame(stats)
    c = cgmd[cgmd.day < BASELINE_DAYS].groupby("patient_id")
    s["cgm_mean_mean"] = c.cgm_mean.mean()
    s["cgm_mean_sd"] = c.cgm_mean.std()
    floors = {"tst_sd": 0.35, "hrv_sd": 2.5, "rhr_sd": 1.0, "eff_sd": 0.015, "odi_sd": 0.8, "steps_sd": 800,
              "waso_sd": 6, "deep_sd": 1.5, "cgm_mean_sd": 4.0}
    for col, f in floors.items():
        s[col] = s[col].fillna(f).clip(lower=f)
    return s.reset_index()


def observed_debt(tst: np.ndarray, tst_base: float) -> np.ndarray:
    """Weighted 7-night debt from what the watch saw; missing nights contribute no deficit."""
    deficit = np.nan_to_num(np.maximum(0.0, tst_base - tst), nan=0.0)
    debt = np.zeros_like(deficit)
    for d in range(len(deficit)):
        for k in range(7):
            if d - k >= 0:
                debt[d] += deficit[d - k] * DECAY ** k
    return debt


def _slope(y: np.ndarray) -> float:
    m = ~np.isnan(y)
    if m.sum() < 3:
        return 0.0
    x = np.arange(len(y))[m]
    return float(np.polyfit(x, y[m], 1)[0])


# ------------------------------------------------------------------ per-patient frame
def patient_features(prof: pd.Series, nights_p: pd.DataFrame, cgmd_p: pd.DataFrame, bs: pd.Series,
                     days=None) -> pd.DataFrame:
    """Feature rows for one patient. nights_p / cgmd_p are indexed 0..N-1 by day."""
    nights_p = nights_p.sort_values("day").reset_index(drop=True)
    cgmd_p = cgmd_p.set_index("day")
    n_days = len(nights_p)
    days = range(7, n_days) if days is None else days
    tst = nights_p.tst_hours.to_numpy(float)
    debt = observed_debt(tst, bs.tst_mean)
    shift_abs = np.abs(nights_p.bedtime_shift_h.to_numpy(float))
    miss = nights_p.tst_hours.isna().to_numpy()
    rows = []
    for d in days:
        n = nights_p.iloc[d]
        prev = cgmd_p.loc[d - 1] if (d - 1) in cgmd_p.index else None
        hrv_z = (n.hrv_rmssd - bs.hrv_mean) / bs.hrv_sd
        tst_win4 = tst[max(0, d - 3): d + 1]
        r = {
            "patient_id": prof.patient_id, "day": d,
            "tst_z": (n.tst_hours - bs.tst_mean) / bs.tst_sd,
            "hrv_z": hrv_z,
            "rhr_delta": n.resting_heart_rate - bs.rhr_mean,
            "eff_delta": n.efficiency - bs.eff_mean,
            "odi_z": (n.odi - bs.odi_mean) / bs.odi_sd,
            "odi_last": n.odi,
            "cgm_mean_z": ((prev.cgm_mean - bs.cgm_mean_mean) / bs.cgm_mean_sd) if prev is not None else np.nan,
            "sleep_debt_7d": debt[d],
            "short_nights_4d": float(np.sum(tst_win4 < bs.tst_mean - 1.0)),
            "bedtime_shift": shift_abs[d],
            "waso_3d_mean": float(np.nanmean(nights_p.waso_min.to_numpy(float)[max(0, d - 2): d + 1]))
            if np.any(~np.isnan(nights_p.waso_min.to_numpy(float)[max(0, d - 2): d + 1])) else np.nan,
            "deep_pct_7d_slope": _slope(nights_p.deep_pct.to_numpy(float)[max(0, d - 6): d + 1]),
            "tir_prev_24h": prev.tir if prev is not None else np.nan,
            "cgm_cv_24h": prev.cgm_cv if prev is not None else np.nan,
            "cgm_max_prev_24h": prev.cgm_max if prev is not None else np.nan,
            "steps_prev": nights_p.steps.iloc[d - 1] if d >= 1 else np.nan,
            "steps_z": ((nights_p.steps.iloc[d - 1] - bs.steps_mean) / bs.steps_sd) if d >= 1 else np.nan,
            "missing_nights_7d": float(miss[max(0, d - 6): d + 1].sum()),
            "cgm_missing_pct_24h": prev.cgm_missing_pct if prev is not None else 1.0,
        }
        rows.append(r)
    f = pd.DataFrame(rows)
    for c in EHR_FEATURES + GENETIC_FEATURES:
        if c == "years_since_t2d_dx":
            f[c] = (2026 - prof.t2d_dx_year) if not pd.isna(prof.t2d_dx_year) else 0.0
        else:
            f[c] = float(prof[c])
    f["debt_x_hba1c"] = f.sleep_debt_7d * f.hba1c
    f["odi_x_has_htn"] = f.odi_z.fillna(0) * f.has_htn
    f["hrv_drop_x_beta_blocker"] = np.maximum(0, -f.hrv_z.fillna(0)) * f.on_beta_blocker
    f["bedtime_shift_x_mtnr1b"] = f.bedtime_shift * f.mtnr1b_risk_allele
    return f


def build_all(save: bool = True):
    profiles = pd.read_parquet(PROCESSED / "profiles.parquet")
    nights = pd.read_parquet(PROCESSED / "nights.parquet")
    cgm = pd.read_parquet(PROCESSED / "cgm.parquet", columns=["patient_id", "day", "glucose_mg_dl"])
    daily = pd.read_parquet(PROCESSED / "daily.parquet")
    cgmd = cgm_daily(cgm)
    bstats = baseline_stats(nights, cgmd)
    bs_idx = bstats.set_index("patient_id")
    frames = []
    for pid, prof in profiles.set_index("patient_id", drop=False).iterrows():
        frames.append(patient_features(prof, nights[nights.patient_id == pid], cgmd[cgmd.patient_id == pid],
                                       bs_idx.loc[pid]))
    feats = pd.concat(frames, ignore_index=True)
    feats = feats.merge(daily[["patient_id", "day", "glucose_event_24h", "bp_event", "cgm_peak", "sbp_morning"]],
                        on=["patient_id", "day"], how="left")
    if save:
        feats.to_parquet(PROCESSED / "features_nextday.parquet")
        cgmd.to_parquet(PROCESSED / "cgm_daily.parquet")
        bstats.to_parquet(PROCESSED / "baseline_stats.parquet")
    return feats, cgmd, bstats


if __name__ == "__main__":
    f, _, _ = build_all()
    print(f.shape)
    print(f[f.day >= 14].glucose_event_24h.mean())
