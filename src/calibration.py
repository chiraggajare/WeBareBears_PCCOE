"""Calibration sources for the simulator.

1. NHANES 2017-Mar 2020 -> a pool of real, anonymized US adults with correlated
   age / sex / BMI / waist / BP / HbA1c / fasting glucose / eGFR / lipids / sleep
   and diagnosis history. The EHR generator resamples (and jitters) from this
   pool, so the joint distribution of the synthetic records follows NHANES.
2. LifeSnaps (Fitbit) daily export -> per-person mean/SD of sleep duration,
   efficiency, nightly RMSSD, resting HR and steps. The wearable generator
   draws each virtual patient's personal ranges from these real people.

If raw files are absent we fall back to published summary statistics
(time-box rule, plan Section 5), and record that in the data card.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from .config import PROCESSED, RAW

NHANES_DIR = RAW / "nhanes"
LIFESNAPS_CSV = RAW / "lifesnaps" / "daily_fitbit_sema_df_unprocessed.csv"
NHANES_POOL = PROCESSED / "nhanes_pool.parquet"
LIFESNAPS_RANGES = PROCESSED / "lifesnaps_person_ranges.parquet"
CALIB_META = PROCESSED / "calibration_meta.json"


# --------------------------------------------------------------------------- NHANES
def _xpt(name: str) -> pd.DataFrame:
    df = pd.read_sas(NHANES_DIR / f"{name}.xpt", format="xport", encoding="latin-1")
    return df.set_index("SEQN")


def _ckd_epi_2021(scr: pd.Series, age: pd.Series, female: pd.Series) -> pd.Series:
    """Race-free CKD-EPI 2021 creatinine equation (mL/min/1.73m2)."""
    kappa = np.where(female, 0.7, 0.9)
    alpha = np.where(female, -0.241, -0.302)
    r = scr / kappa
    egfr = 142 * np.minimum(r, 1) ** alpha * np.maximum(r, 1) ** -1.200 * 0.9938 ** age
    return pd.Series(np.where(female, egfr * 1.012, egfr), index=scr.index)


def build_nhanes_pool() -> pd.DataFrame:
    demo = _xpt("P_DEMO")[["RIAGENDR", "RIDAGEYR", "WTMECPRP"]]
    bmx = _xpt("P_BMX")[["BMXBMI", "BMXWAIST"]]
    bp = _xpt("P_BPXO")
    bp = pd.DataFrame({
        "sbp": bp[["BPXOSY1", "BPXOSY2", "BPXOSY3"]].mean(axis=1),
        "dbp": bp[["BPXODI1", "BPXODI2", "BPXODI3"]].mean(axis=1),
    })
    ghb = _xpt("P_GHB")[["LBXGH"]]
    glu = _xpt("P_GLU")[["LBXGLU"]]
    bio = _xpt("P_BIOPRO")[["LBXSCR"]]
    tc = _xpt("P_TCHOL")[["LBXTC"]]
    hdl = _xpt("P_HDL")[["LBDHDD"]]
    tg = _xpt("P_TRIGLY")
    tg = tg[[c for c in ("LBXTR", "LBDLDL") if c in tg.columns]]
    slq = _xpt("P_SLQ")[["SLD012"]]
    diq = _xpt("P_DIQ")
    diq = diq[[c for c in ("DIQ010", "DID040", "DIQ160", "DIQ070", "DIQ050") if c in diq.columns]]
    bpq = _xpt("P_BPQ")
    bpq = bpq[[c for c in ("BPQ020", "BPD035", "BPQ050A", "BPQ080", "BPQ100D") if c in bpq.columns]]

    df = demo.join([bmx, bp, ghb, glu, bio, tc, hdl, tg, slq, diq, bpq], how="left")
    df = df[(df.RIDAGEYR >= 22) & (df.RIDAGEYR <= 75)]
    df = df.dropna(subset=["BMXBMI", "sbp", "dbp", "LBXGH", "LBXSCR", "LBXTC", "LBDHDD"])

    out = pd.DataFrame(index=df.index)
    out["age"] = df.RIDAGEYR.astype(float)
    out["sex"] = np.where(df.RIAGENDR == 2, "F", "M")
    out["bmi"] = df.BMXBMI
    out["waist_cm"] = df.BMXWAIST.fillna(df.BMXBMI * 3.3)
    out["sbp"] = df.sbp
    out["dbp"] = df.dbp
    out["hba1c"] = df.LBXGH
    # fasting glucose measured only in the fasting subsample -> impute from HbA1c (ADAG-like) where missing
    fg_imp = 0.85 * (28.7 * df.LBXGH - 46.7) + 4   # ADAG estimated average glucose, scaled to fasting
    out["fasting_glucose"] = df.LBXGLU.fillna(fg_imp).clip(70, 350)
    out["egfr"] = _ckd_epi_2021(df.LBXSCR, df.RIDAGEYR, df.RIAGENDR == 2).clip(15, 140)
    out["hdl"] = df.LBDHDD
    tg_series = df["LBXTR"] if "LBXTR" in df else pd.Series(np.nan, index=df.index)
    out["triglycerides"] = tg_series.fillna((df.LBXTC - df.LBDHDD) * 0.9).clip(35, 600)
    ldl = df["LBDLDL"] if "LBDLDL" in df else pd.Series(np.nan, index=df.index)
    out["ldl"] = ldl.fillna(df.LBXTC - df.LBDHDD - out.triglycerides / 5).clip(30, 260)
    out["sleep_hours"] = df.SLD012.where(df.SLD012.between(2, 14))
    out["told_diabetes"] = (df.get("DIQ010") == 1)
    out["age_dx_diabetes"] = df.get("DID040").where(df.get("DID040", pd.Series(dtype=float)) < 100)
    out["told_prediabetes"] = (df.get("DIQ160") == 1)
    out["told_htn"] = (df.get("BPQ020") == 1)
    out["age_dx_htn"] = df.get("BPD035").where(df.get("BPD035", pd.Series(dtype=float)) < 100)
    out["told_chol"] = (df.get("BPQ080") == 1)
    out["weight"] = df.WTMECPRP

    hba = out.hba1c
    out["glycemic"] = np.select(
        [out.told_diabetes | (hba >= 6.5), out.told_prediabetes | (hba >= 5.7)],
        ["t2d", "prediabetes"], default="healthy")
    out["htn"] = out.told_htn | (out.sbp >= 140) | (out.dbp >= 90)
    out = out.reset_index(drop=True)
    out.to_parquet(NHANES_POOL)
    return out


def fallback_nhanes_pool(n: int = 6000, seed: int = 0) -> pd.DataFrame:
    """Published NHANES 2017-2020 adult summary statistics (used only if downloads fail)."""
    rng = np.random.default_rng(seed)
    age = rng.uniform(22, 75, n)
    sex = rng.choice(["M", "F"], n)
    bmi = np.clip(rng.normal(29.6, 6.8, n), 17, 55)
    hba1c = np.clip(5.3 + 0.012 * (age - 40) + 0.03 * (bmi - 29) + rng.gamma(1.2, 0.35, n) - 0.2, 4.4, 12)
    sbp = np.clip(105 + 0.45 * age + 0.4 * (bmi - 29) + rng.normal(0, 14, n), 90, 200)
    df = pd.DataFrame({
        "age": age, "sex": sex, "bmi": bmi, "waist_cm": bmi * 3.3 + rng.normal(0, 6, n),
        "sbp": sbp, "dbp": np.clip(0.45 * sbp + 18 + rng.normal(0, 8, n), 50, 120),
        "hba1c": hba1c, "fasting_glucose": np.clip(28.7 * hba1c - 60 + rng.normal(0, 10, n), 70, 350),
        "egfr": np.clip(120 - 0.8 * age + rng.normal(0, 12, n), 15, 140),
        "hdl": np.clip(rng.normal(53, 15, n), 20, 110), "triglycerides": np.clip(rng.lognormal(4.8, 0.5, n), 35, 600),
        "ldl": np.clip(rng.normal(112, 35, n), 30, 260), "sleep_hours": np.clip(rng.normal(7.4, 1.4, n), 3, 12),
        "told_diabetes": hba1c >= 6.8, "age_dx_diabetes": np.nan, "told_prediabetes": False,
        "told_htn": sbp >= 145, "age_dx_htn": np.nan, "told_chol": False, "weight": 1.0,
    })
    df["glycemic"] = np.select([df.hba1c >= 6.5, df.hba1c >= 5.7], ["t2d", "prediabetes"], "healthy")
    df["htn"] = df.told_htn | (df.sbp >= 140)
    return df


def load_nhanes_pool() -> tuple[pd.DataFrame, str]:
    if NHANES_POOL.exists():
        return pd.read_parquet(NHANES_POOL), "NHANES 2017-Mar 2020 (downloaded)"
    try:
        return build_nhanes_pool(), "NHANES 2017-Mar 2020 (downloaded)"
    except Exception as e:  # noqa: BLE001
        print(f"[calibration] NHANES unavailable ({e}); using published summary statistics")
        return fallback_nhanes_pool(), "NHANES published summary statistics (fallback)"


# ------------------------------------------------------------------------ LifeSnaps
def load_lifesnaps_daily() -> pd.DataFrame | None:
    if not LIFESNAPS_CSV.exists():
        return None
    df = pd.read_csv(LIFESNAPS_CSV, usecols=["id", "date", "rmssd", "resting_hr", "minutesAsleep",
                                             "sleep_efficiency", "steps", "minutesAwake", "spo2"])
    df["date"] = pd.to_datetime(df["date"])
    df = df.drop_duplicates(["id", "date"]).sort_values(["id", "date"])
    df["tst_hours"] = df.minutesAsleep / 60
    df.loc[~df.tst_hours.between(2, 13), "tst_hours"] = np.nan
    df.loc[~df.rmssd.between(5, 200), "rmssd"] = np.nan
    df.loc[~df.resting_hr.between(35, 110), "resting_hr"] = np.nan
    df.loc[df.steps < 300, "steps"] = np.nan
    return df.reset_index(drop=True)


def build_lifesnaps_ranges() -> pd.DataFrame:
    df = load_lifesnaps_daily()
    if df is None:
        raise FileNotFoundError(LIFESNAPS_CSV)
    g = df.groupby("id")
    r = pd.DataFrame({
        "n_nights": g.tst_hours.count(),
        "tst_mean": g.tst_hours.mean(), "tst_sd": g.tst_hours.std(),
        "eff_mean": g.sleep_efficiency.mean() / 100, "eff_sd": g.sleep_efficiency.std() / 100,
        "waso_mean": g.minutesAwake.mean(),
        "hrv_mean": g.rmssd.mean(), "hrv_sd": g.rmssd.std(),
        "rhr_mean": g.resting_hr.mean(), "rhr_sd": g.resting_hr.std(),
        "steps_mean": g.steps.mean(), "steps_sd": g.steps.std(),
    })
    r = r[(r.n_nights >= 14) & r.hrv_mean.notna() & r.rhr_mean.notna() & r.steps_mean.notna()]
    r = r.reset_index()
    r.to_parquet(LIFESNAPS_RANGES)
    return r


def fallback_lifesnaps_ranges(n: int = 60, seed: int = 1) -> pd.DataFrame:
    """Ranges reported for the LifeSnaps cohort (Yfantidou et al., Sci Data 2022)."""
    rng = np.random.default_rng(seed)
    return pd.DataFrame({
        "id": [f"fallback{i}" for i in range(n)], "n_nights": 60,
        "tst_mean": rng.normal(6.9, 0.6, n), "tst_sd": rng.uniform(0.6, 1.2, n),
        "eff_mean": rng.normal(0.92, 0.03, n), "eff_sd": rng.uniform(0.02, 0.05, n),
        "waso_mean": rng.normal(60, 12, n),
        "hrv_mean": rng.normal(45, 15, n).clip(15, 110), "hrv_sd": rng.uniform(5, 12, n),
        "rhr_mean": rng.normal(62, 7, n).clip(45, 85), "rhr_sd": rng.uniform(1.2, 3.0, n),
        "steps_mean": rng.normal(9000, 3000, n).clip(2500, 20000), "steps_sd": rng.uniform(2000, 4000, n),
    })


def load_lifesnaps_ranges() -> tuple[pd.DataFrame, str]:
    if LIFESNAPS_RANGES.exists():
        return pd.read_parquet(LIFESNAPS_RANGES), "LifeSnaps daily Fitbit export (downloaded)"
    try:
        return build_lifesnaps_ranges(), "LifeSnaps daily Fitbit export (downloaded)"
    except Exception as e:  # noqa: BLE001
        print(f"[calibration] LifeSnaps unavailable ({e}); using paper ranges")
        return fallback_lifesnaps_ranges(), "LifeSnaps paper ranges (fallback)"


def write_meta(meta: dict) -> None:
    CALIB_META.write_text(json.dumps(meta, indent=2, default=str), encoding="utf-8")


def read_meta() -> dict:
    return json.loads(CALIB_META.read_text(encoding="utf-8")) if CALIB_META.exists() else {}
