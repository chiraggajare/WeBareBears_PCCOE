"""2-hour-ahead glucose spike alert (plan Section 7).

    python -m src.short_horizon

Samples: every hour 07:00-21:00 on prediction days 15-21 while the current CGM reading is < 160 mg/dL.
Label  : spike_2h = CGM crosses 180 mg/dL within the next 120 minutes.
Features: current CGM, 30/60-min slope, minutes since last logged meal (+ its carbs), CGM CV over the
          previous 24 h, last night's sleep debt + HRV z-score, HbA1c, PRS, diabetes medication.
Metrics : AUROC, AUPRC, false alerts per patient-week, and median warning lead time
          (time from the first alert to the actual crossing).
"""
from __future__ import annotations

import json

import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score

from .config import GLUCOSE_THRESHOLD, MODELS, PRED_DAYS, PROCESSED, REPORTS, SEED, SPIKE_2H_HORIZON
from .features import observed_debt

FEATURES = ["cgm_now", "slope_30", "slope_60", "minutes_since_meal", "last_meal_carbs", "cgm_cv_24h",
            "debt_last_night", "hrv_z_last_night", "hba1c", "prs_t2d", "on_metformin", "on_sglt2i",
            "on_sulfonylurea"]
MONO = {"cgm_now": 1, "slope_30": 1, "slope_60": 1, "last_meal_carbs": 1, "debt_last_night": 1, "hba1c": 1,
        "hrv_z_last_night": -1}
THRESHOLD = 0.4
N_FOLDS = 5
HOURS = range(7, 22)   # waking hours 07:00-21:00


class PatientSeries:
    """Fast access to one patient's CGM (observed + noisy truth) and meals on an absolute minute axis."""

    def __init__(self, cgm_p: pd.DataFrame, meals_p: pd.DataFrame):
        self.t = cgm_p.t.to_numpy()
        self.obs = cgm_p.glucose_mg_dl.to_numpy(float)
        self.truth = cgm_p.glucose_noisy.to_numpy(float)
        self.meal_t = (meals_p.day * 1440 + meals_p.minute_of_day).to_numpy(float)
        self.meal_c = meals_p.carbs_g.to_numpy(float)

    def at(self, minute):
        return self.obs[int(minute // 5)] if 0 <= minute // 5 < len(self.obs) else np.nan

    def features(self, minute: int) -> dict:
        i = int(minute // 5)
        now = self.obs[i]
        b30 = self.obs[i - 6] if i >= 6 else np.nan
        b60 = self.obs[i - 12] if i >= 12 else np.nan
        prior = self.meal_t <= minute
        if prior.any():
            j = np.where(prior)[0][-1]
            since, carbs = minute - self.meal_t[j], self.meal_c[j]
        else:
            since, carbs = 720.0, 0.0
        win = self.obs[max(0, i - 288): i + 1]
        cv = np.nanstd(win) / np.nanmean(win) if np.sum(~np.isnan(win)) > 24 else np.nan
        return {"cgm_now": now, "slope_30": (now - b30) / 30, "slope_60": (now - b60) / 60,
                "minutes_since_meal": min(since, 720.0), "last_meal_carbs": carbs if since < 240 else 0.0,
                "cgm_cv_24h": cv}

    def label(self, minute: int) -> tuple[int, float]:
        i = int(minute // 5)
        fut = self.truth[i + 1: i + 1 + SPIKE_2H_HORIZON // 5]
        above = np.where(fut > GLUCOSE_THRESHOLD)[0]
        if len(above):
            return 1, minute + (above[0] + 1) * 5
        return 0, np.nan


def night_context(nights_p: pd.DataFrame, bs: pd.Series) -> pd.DataFrame:
    nights_p = nights_p.sort_values("day")
    debt = observed_debt(nights_p.tst_hours.to_numpy(float), bs.tst_mean)
    hz = (nights_p.hrv_rmssd.to_numpy(float) - bs.hrv_mean) / bs.hrv_sd
    return pd.DataFrame({"day": nights_p.day.to_numpy(), "debt_last_night": debt, "hrv_z_last_night": hz})


def build_samples():
    profiles = pd.read_parquet(PROCESSED / "profiles.parquet").set_index("patient_id")
    cgm = pd.read_parquet(PROCESSED / "cgm.parquet")
    meals = pd.read_parquet(PROCESSED / "meals.parquet")
    nights = pd.read_parquet(PROCESSED / "nights.parquet")
    bstats = pd.read_parquet(PROCESSED / "baseline_stats.parquet").set_index("patient_id")
    rows = []
    for pid, cg in cgm.groupby("patient_id", sort=False):
        ps = PatientSeries(cg, meals[meals.patient_id == pid])
        nc = night_context(nights[nights.patient_id == pid], bstats.loc[pid]).set_index("day")
        prof = profiles.loc[pid]
        for d in PRED_DAYS:
            for h in HOURS:
                m = d * 1440 + h * 60
                now = ps.at(m)
                if np.isnan(now) or now >= 160:
                    continue
                f = ps.features(m)
                y, cross = ps.label(m)
                f.update({"patient_id": pid, "day": d, "minute": m, "spike_2h": y, "cross_minute": cross,
                          **nc.loc[d].to_dict(),
                          **{k: float(prof[k]) for k in ("hba1c", "prs_t2d", "on_metformin", "on_sglt2i",
                                                         "on_sulfonylurea")}})
                rows.append(f)
    return pd.DataFrame(rows)


def make_model():
    return lgb.LGBMClassifier(n_estimators=300, learning_rate=0.04, num_leaves=15, min_child_samples=30,
                              subsample=0.8, subsample_freq=1, colsample_bytree=0.8, random_state=SEED,
                              verbose=-1, n_jobs=4, monotone_constraints=[MONO.get(f, 0) for f in FEATURES],
                              monotone_constraints_method="advanced")


def lead_times(df: pd.DataFrame, p: np.ndarray) -> dict:
    df = df.assign(p=p)
    pos = df[df.spike_2h == 1]
    episodes = pos.groupby(["patient_id", "cross_minute"])
    leads = []
    for (pid, cross), g in episodes:
        alerted = g[g.p >= THRESHOLD]
        if len(alerted):
            leads.append(cross - alerted.minute.min())
    n_ep = episodes.ngroups
    return {"episodes": int(n_ep), "episodes_warned": int(len(leads)),
            "episode_recall": round(len(leads) / max(1, n_ep), 3),
            "median_lead_min": float(np.median(leads)) if leads else None,
            "iqr_lead_min": [float(np.percentile(leads, 25)), float(np.percentile(leads, 75))] if leads else None}


def main():
    df = build_samples()
    df.to_parquet(PROCESSED / "samples_2h.parquet")
    fold_of = json.loads((MODELS / "folds.json").read_text(encoding="utf-8"))
    folds = df.patient_id.map(fold_of).to_numpy()
    p = np.zeros(len(df))
    for k in range(N_FOLDS):
        tr, te = folds != k, folds == k
        assert not set(df.patient_id[tr]) & set(df.patient_id[te])
        m = make_model()
        m.fit(df.loc[tr, FEATURES], df.loc[tr, "spike_2h"])
        p[te] = m.predict_proba(df.loc[te, FEATURES])[:, 1]
        joblib.dump({"model": m, "features": FEATURES}, MODELS / f"spike2h_fold{k}.joblib")
    y = df.spike_2h.to_numpy()
    pred = p >= THRESHOLD
    n_pat = df.patient_id.nunique()
    res = {
        "n_samples": int(len(df)), "n_patients": int(n_pat), "event_rate": round(float(y.mean()), 3),
        "auroc": round(float(roc_auc_score(y, p)), 3), "auprc": round(float(average_precision_score(y, p)), 3),
        "threshold": THRESHOLD,
        "sensitivity": round(float(pred[y == 1].mean()), 3),
        "false_alerts_per_patient_week": round(float(((pred == 1) & (y == 0)).sum()) / n_pat, 3),
        **lead_times(df, p),
    }
    # baseline: "current CGM + slope only" (what a plain CGM trend arrow would do)
    from sklearn.linear_model import LogisticRegression
    base = np.zeros(len(df))
    Xb = df[["cgm_now", "slope_30"]].fillna(0).to_numpy()
    for k in range(N_FOLDS):
        tr, te = folds != k, folds == k
        base[te] = LogisticRegression(max_iter=500).fit(Xb[tr], y[tr]).predict_proba(Xb[te])[:, 1]
    res["trend_only_auroc"] = round(float(roc_auc_score(y, base)), 3)
    (REPORTS / "spike2h_metrics.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
    print(json.dumps(res, indent=2))
    from .integrity import write_manifest
    from .report import write_results
    write_manifest()
    write_results()


if __name__ == "__main__":
    main()
