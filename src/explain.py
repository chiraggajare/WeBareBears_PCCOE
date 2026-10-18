"""Turn SHAP values into plain-English reasons (no mystery numbers)."""
from __future__ import annotations

import math

import numpy as np

# features that describe the same story are grouped so one reason = one idea
GROUPS = {
    "short_sleep": ["sleep_debt_7d", "short_nights_4d", "tst_z", "debt_x_hba1c"],
    "timing": ["bedtime_shift", "bedtime_shift_x_mtnr1b"],
    "hrv": ["hrv_z", "hrv_drop_x_beta_blocker"],
    "rhr": ["rhr_delta"],
    "apnea": ["odi_z", "odi_last", "odi_x_has_htn"],
    "fragmented": ["waso_3d_mean", "eff_delta", "deep_pct_7d_slope"],
    "glucose_context": ["cgm_max_prev_24h", "tir_prev_24h", "cgm_mean_z", "cgm_cv_24h"],
    "activity": ["steps_prev", "steps_z"],
    "control": ["hba1c", "has_t2d", "years_since_t2d_dx"],
    "body": ["bmi", "age"],
    "bp_history": ["sbp_clinic", "has_htn"],
    "genetics": ["prs_t2d", "tcf7l2_risk_alleles", "mtnr1b_risk_allele"],
    "meds": ["on_metformin", "on_sglt2i", "on_sulfonylurea", "on_beta_blocker", "on_ace_inhibitor"],
    "kidney_lipids": ["egfr", "ldl", "has_osa"],
    "data": ["missing_nights_7d", "cgm_missing_pct_24h"],
}
FEATURE_TO_GROUP = {f: g for g, fs in GROUPS.items() for f in fs}


def _fmt_h(x):
    return f"{x:.1f} h"


def reason_text(group: str, row: dict, ctx: dict, positive: bool) -> str:
    """ctx carries raw values (last night's TST, personal normal, etc.)."""
    g = group
    if g == "short_sleep":
        n = int(row.get("short_nights_4d", 0) or 0)
        if positive:
            last_short = ctx["tst_last"] < ctx["tst_usual"] - 1.0
            if n >= 2 and last_short:
                return f"{n} short nights in a row (last {_fmt_h(ctx['tst_last'])} vs usual {_fmt_h(ctx['tst_usual'])})"
            if n >= 2:
                return (f"{n} short nights in the last 4 (last night {_fmt_h(ctx['tst_last'])} vs usual "
                        f"{_fmt_h(ctx['tst_usual'])})")
            if n == 1:
                return f"One short night ({_fmt_h(ctx['tst_last'])} vs usual {_fmt_h(ctx['tst_usual'])})"
            return f"Sleep debt building up: last night {_fmt_h(ctx['tst_last'])} vs usual {_fmt_h(ctx['tst_usual'])}"
        return f"Sleep on track ({_fmt_h(ctx['tst_last'])} vs usual {_fmt_h(ctx['tst_usual'])})"
    if g == "timing":
        s = row.get("bedtime_shift", 0) or 0
        return (f"Bedtime {s:.1f} h later than usual" + (" (MTNR1B carrier: more timing-sensitive)"
                                                         if row.get("mtnr1b_risk_allele") and s > 1 else "")
                if positive else "Regular bedtime")
    if g == "hrv":
        pct = ctx.get("hrv_change_pct")
        if pct is None or (isinstance(pct, float) and math.isnan(pct)):
            return "HRV not recorded last night"
        if positive:
            extra = " - beta-blocker hides the heart-rate signal, HRV still shows strain" if row.get(
                "on_beta_blocker") else ""
            return f"HRV down {abs(pct):.0f}% from personal normal{extra}"
        return f"HRV {'up' if pct >= 0 else 'down'} {abs(pct):.0f}% vs personal normal (recovered)"
    if g == "rhr":
        d = row.get("rhr_delta", 0) or 0
        return (f"Resting HR {d:+.0f} bpm vs personal normal" if positive
                else f"Resting HR change ({d:+.0f} bpm) not concerning for this profile")
    if g == "apnea":
        odi = ctx.get("odi_last")
        if positive:
            return f"Frequent oxygen dips at night (~{odi:.0f}/hr) - possible sleep apnea" if odi and odi >= 10 else \
                f"More oxygen dips than usual ({odi:.0f}/hr)"
        return "Few oxygen dips at night"
    if g == "fragmented":
        w = row.get("waso_3d_mean")
        return (f"Broken sleep: ~{w:.0f} min awake per night" if positive and w else
                "Sleep continuity normal")
    if g == "glucose_context":
        m = row.get("cgm_max_prev_24h")
        return (f"Yesterday's glucose already peaked at {m:.0f} mg/dL" if positive and m and not math.isnan(m)
                else "Yesterday's glucose stayed mostly in range")
    if g == "activity":
        s = row.get("steps_prev")
        return (f"Low activity yesterday ({s:,.0f} steps)" if positive and s and not math.isnan(s)
                else "Good activity yesterday")
    if g == "control":
        return (f"Made worse by high HbA1c ({row.get('hba1c'):.1f}%)" if positive and row.get("hba1c", 0) >= 6.5
                else f"HbA1c {row.get('hba1c'):.1f}% (prediabetic range)" if positive
                else f"Good glycaemic control (HbA1c {row.get('hba1c'):.1f}%)")
    if g == "body":
        return f"BMI {row.get('bmi'):.1f}, age {row.get('age'):.0f}" if positive else "Healthy BMI / age profile"
    if g == "bp_history":
        return (f"Clinic BP already {row.get('sbp_clinic'):.0f} mmHg" if positive
                else f"Clinic BP normal ({row.get('sbp_clinic'):.0f} mmHg)")
    if g == "genetics":
        return "Higher genetic risk (simulated markers)" if positive else "Low genetic risk (simulated markers)"
    if g == "meds":
        if positive:
            missing = [m for m, key in (("ACE inhibitor", "on_ace_inhibitor"), ("metformin", "on_metformin"))
                       if not row.get(key)]
            return f"Not on {' or '.join(missing)}" if missing else "Current medication not fully protective"
        return "Medication is helping"
    if g == "kidney_lipids":
        return "Kidney / lipid profile" if positive else "Kidney / lipid profile reassuring"
    if g == "data":
        return "Some missing data (less certain)"
    return g


NOTEWORTHY = {  # only call out a disturbance that is actually visible in the data
    "short_sleep": lambda r: (r.get("tst_z") or 0) < -1.5 or (r.get("short_nights_4d") or 0) >= 1,
    "timing": lambda r: (r.get("bedtime_shift") or 0) >= 1.5,
    "hrv": lambda r: (r.get("hrv_z") or 0) < -1.5,
    "apnea": lambda r: (r.get("odi_last") or 0) >= 10,
}
DYNAMIC = {"short_sleep", "timing", "hrv", "rhr", "apnea", "fragmented", "glucose_context", "activity"}
STATIC = {"control", "body", "bp_history", "genetics", "meds", "kidney_lipids"}


def reasons_from_shap(shap_row: np.ndarray, feature_names: list[str], feat_row: dict, ctx: dict, k: int = 3,
                      prob: float | None = None, high: float = 0.40) -> list[dict]:
    """Top reasons. For an elevated forecast: up to k dynamic (wearable) drivers, then the strongest
    static factor as a "made worse by" modifier - e.g. "4 short nights in a row, bedtime 2 h later,
    HRV down 34% - made worse by high HbA1c". For a low forecast: the strongest protective factors."""
    agg: dict[str, float] = {}
    for f, v in zip(feature_names, shap_row):
        g = FEATURE_TO_GROUP.get(f, f)
        agg[g] = agg.get(g, 0.0) + float(v)
    out = []
    if prob is not None and prob < high:
        # a recent disturbance that did NOT raise risk is worth showing ("no false alarm")
        noted = sorted([kv for kv in agg.items() if kv[1] > 0.02 and kv[0] in DYNAMIC and kv[0] in NOTEWORTHY
                        and NOTEWORTHY[kv[0]](feat_row)], key=lambda kv: -kv[1])[:1]
        items = sorted([kv for kv in agg.items() if kv[1] < 0], key=lambda kv: kv[1])[: k - len(noted)]
        for g, v in items:
            out.append({"text": reason_text(g, feat_row, ctx, False), "impact": round(v, 3), "group": g,
                        "kind": "protective"})
        for g, v in noted:
            out.append({"text": f"Noted: {reason_text(g, feat_row, ctx, True)[0].lower()}"
                                f"{reason_text(g, feat_row, ctx, True)[1:]} - not enough to raise risk for this profile",
                        "impact": round(v, 3), "group": g, "kind": "noted"})
        return out
    dyn = sorted([kv for kv in agg.items() if kv[1] > 0.05 and kv[0] in DYNAMIC], key=lambda kv: -kv[1])
    stat = sorted([kv for kv in agg.items() if kv[1] > 0.05 and kv[0] in STATIC], key=lambda kv: -kv[1])
    for g, v in dyn[:k]:
        out.append({"text": reason_text(g, feat_row, ctx, True), "impact": round(v, 3), "group": g,
                    "kind": "driver"})
    for g, v in stat[:1]:
        out.append({"text": reason_text(g, feat_row, ctx, True), "impact": round(v, 3), "group": g,
                    "kind": "modifier"})
    return out
