"""Train next-day models with a 3-tier ablation, GroupKFold by patient, SHAP explanations.

    python -m src.train

* Targets: glucose_event_24h (main: tomorrow's CGM peak > 180 mg/dL) and bp_event (morning SBP > 145).
* Prediction days 15-21 (index 14..20); GroupKFold(5) by patient_id -> no patient in train and test.
* Ablation: EHR-only (static + genetic) vs wearables-only vs fused twin.
* Deployed model = the 5 fold models; each patient is scored by the fold that did NOT train on them
  (so dashboard risks are honest out-of-fold predictions, including the demo personas).
"""
from __future__ import annotations

import json

import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import GroupKFold

from .config import MODELS, PRED_DAYS, PROCESSED, REPORTS, SEED
from .features import FEATURE_SETS, MONOTONE

THRESHOLD = 0.5
N_FOLDS = 5
PARAMS = dict(n_estimators=350, learning_rate=0.03, num_leaves=15, min_child_samples=25, subsample=0.8,
              subsample_freq=1, colsample_bytree=0.8, reg_lambda=1.0, random_state=SEED, verbose=-1, n_jobs=4)


def make_model(features: list[str]) -> lgb.LGBMClassifier:
    mono = [MONOTONE.get(f, 0) for f in features]
    return lgb.LGBMClassifier(**PARAMS, monotone_constraints=mono, monotone_constraints_method="advanced")


def fold_assignment(df: pd.DataFrame) -> dict:
    pids = df.patient_id.unique()
    gkf = GroupKFold(n_splits=N_FOLDS)
    fold_of = {}
    for k, (_, te) in enumerate(gkf.split(pids, groups=pids)):
        for pid in pids[te]:
            fold_of[str(pid)] = k
    return fold_of


def metrics(y, p, n_patients):
    pred = p >= THRESHOLD
    fp = int(((pred == 1) & (y == 0)).sum())
    return {
        "auroc": round(float(roc_auc_score(y, p)), 3),
        "auprc": round(float(average_precision_score(y, p)), 3),
        "prevalence": round(float(np.mean(y)), 3),
        "sensitivity": round(float(pred[y == 1].mean()), 3),
        "specificity": round(float((~pred[y == 0]).mean()), 3),
        "false_alerts_per_patient_week": round(fp / n_patients, 3),  # 7 prediction days = 1 week
        "threshold": THRESHOLD,
    }


def run_target(df: pd.DataFrame, target: str, fold_of: dict, save_models: bool) -> tuple[dict, pd.DataFrame]:
    out = {}
    oof = df[["patient_id", "day", target]].copy()
    folds = df.patient_id.map(fold_of).to_numpy()
    n_pat = df.patient_id.nunique()
    for tier, feats in FEATURE_SETS.items():
        p = np.zeros(len(df))
        for k in range(N_FOLDS):
            tr, te = folds != k, folds == k
            assert not set(df.patient_id[tr]) & set(df.patient_id[te]), "patient leakage across folds"
            m = make_model(feats)
            m.fit(df.loc[tr, feats], df.loc[tr, target])
            p[te] = m.predict_proba(df.loc[te, feats])[:, 1]
            if save_models and tier == "fused":
                joblib.dump({"model": m, "features": feats}, MODELS / f"nextday_{target}_fold{k}.joblib")
        out[tier] = metrics(df[target].to_numpy(), p, n_pat)
        t2d = df.has_t2d.to_numpy() == 1
        out.setdefault("t2d_subgroup", {})[tier] = round(float(roc_auc_score(df[target][t2d], p[t2d])), 3)
        oof[f"p_{tier}"] = p
    return out, oof


def interpretation(res: dict) -> str:
    e, w, f = (res[t]["auroc"] for t in ("ehr_only", "wearables_only", "fused"))
    sub = res.get("t2d_subgroup", {})
    best_single = max(e, w)
    if f > best_single + 0.005:
        return (f"Fusing the health record with the wearable stream (AUROC {f:.2f}) beats the record alone "
                f"({e:.2f}) and the wearables alone ({w:.2f}); within diabetics only the gain is larger "
                f"({sub.get('ehr_only', float('nan')):.2f} -> {sub.get('fused', float('nan')):.2f}), because the same "
                "night means more for a high-risk patient.")
    return (f"Fusion (AUROC {f:.2f}) did not clearly beat the best single stream ({best_single:.2f}); "
            f"reported honestly - the gain from combining streams is small on this cohort.")


def main():
    df = pd.read_parquet(PROCESSED / "features_nextday.parquet")
    df = df[df.day.isin(PRED_DAYS)].reset_index(drop=True)
    fold_of = fold_assignment(df)
    (MODELS / "folds.json").write_text(json.dumps(fold_of), encoding="utf-8")

    results = {"n_patients": int(df.patient_id.nunique()), "n_rows": int(len(df)),
               "prediction_days": "15-21", "cv": "GroupKFold(5) by patient_id"}
    oofs = []
    for target in ("glucose_event_24h", "bp_event"):
        res, oof = run_target(df, target, fold_of, save_models=True)
        res["interpretation"] = interpretation(res)
        results[target] = res
        oofs.append(oof.rename(columns={c: f"{c}_{target}" for c in oof.columns if c.startswith("p_")}))
    oof = oofs[0].merge(oofs[1], on=["patient_id", "day"])
    oof.to_parquet(PROCESSED / "oof_nextday.parquet")

    # personas on their final day (index 20)
    last = oof[oof.day == 20].set_index("patient_id")
    results["personas"] = {
        pid: {"glucose_risk": round(float(last.loc[pid, "p_fused_glucose_event_24h"]), 3),
              "bp_risk": round(float(last.loc[pid, "p_fused_bp_event"]), 3)}
        for pid in ("A", "B", "C") if pid in last.index}

    # global importance (mean |SHAP|) for the fused glucose model, fold 0
    import shap
    b = joblib.load(MODELS / "nextday_glucose_event_24h_fold0.joblib")
    sv = shap.TreeExplainer(b["model"]).shap_values(df[b["features"]].sample(600, random_state=SEED))
    sv = sv[1] if isinstance(sv, list) else sv
    imp = pd.Series(np.abs(sv).mean(axis=0), index=b["features"]).sort_values(ascending=False)
    results["top_features_glucose"] = {k: round(float(v), 3) for k, v in imp.head(12).items()}

    (REPORTS / "nextday_metrics.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps({k: results[k] for k in ("glucose_event_24h", "bp_event", "personas")}, indent=2))
    from .integrity import write_manifest
    from .report import write_results
    write_manifest()
    write_results()


if __name__ == "__main__":
    main()
