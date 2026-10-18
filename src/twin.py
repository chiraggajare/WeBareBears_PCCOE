"""The digital-twin service: everything the API serves, computed from the Parquet cohort + trained models.

Snapshot convention: the dashboard is "day 21 at 13:00".
* next-day risk  = forecast for the coming 24 h, issued after last night's sleep synced (row for day index 20)
* 2-hour alert   = evaluated on the live CGM at 13:00
* What-If        = replaces the most recent night(s) with the doctor's scenario and re-runs
                   physiology (SI -> Bergman curve) and the models (risk + SHAP reasons)
"""
from __future__ import annotations

import json
import math
import time
from functools import lru_cache

import numpy as np
import pandas as pd
import shap
import warnings

warnings.filterwarnings("ignore", message=".*LightGBM binary classifier.*")

from . import physiology as ph
from .config import (DISCLAIMER, GLUCOSE_THRESHOLD, MODELS, N_DAYS, NOW_MINUTE, PROCESSED, REPORTS,
                     SAMPLES_PER_DAY, day_date, risk_level)
from .explain import reasons_from_shap
from .integrity import safe_load, verify
from .features import patient_features
from .short_horizon import PatientSeries, night_context
from .wearables import night_heart

DAY = N_DAYS - 1           # forecast row shown on the dashboard
NOW_ABS = DAY * 1440 + NOW_MINUTE


def _f(x, nd=1):
    if x is None:
        return None
    try:
        if isinstance(x, (float, np.floating)) and (math.isnan(x) or math.isinf(x)):
            return None
    except TypeError:
        pass
    return round(float(x), nd)


class Twin:
    def __init__(self):
        t0 = time.time()
        P = PROCESSED
        self.profiles = pd.read_parquet(P / "profiles.parquet").set_index("patient_id", drop=False)
        self.sim_base = pd.read_parquet(P / "baselines.parquet").set_index("patient_id")
        self.params = pd.read_parquet(P / "physiology_params.parquet").set_index("patient_id")
        nights = pd.read_parquet(P / "nights.parquet")
        self.nights = {k: v.sort_values("day").reset_index(drop=True) for k, v in nights.groupby("patient_id")}
        hyp = pd.read_parquet(P / "hypnograms.parquet")
        self.hyp = {k: v.set_index("day") for k, v in hyp.groupby("patient_id")}
        meals = pd.read_parquet(P / "meals.parquet")
        self.meals = {k: v for k, v in meals.groupby("patient_id")}
        cgm = pd.read_parquet(P / "cgm.parquet", columns=["patient_id", "t", "glucose_mg_dl", "glucose_noisy"])
        self.cgm = {k: v.sort_values("t").reset_index(drop=True) for k, v in cgm.groupby("patient_id")}
        cgmd = pd.read_parquet(P / "cgm_daily.parquet")
        self.cgmd = {k: v for k, v in cgmd.groupby("patient_id")}
        self.bstats = pd.read_parquet(P / "baseline_stats.parquet").set_index("patient_id")
        feats = pd.read_parquet(P / "features_nextday.parquet")
        self.feats = {k: v.set_index("day") for k, v in feats.groupby("patient_id")}
        self.fold_of = json.loads(verify(MODELS / "folds.json").read_text(encoding="utf-8"))
        self.models = {}
        for target in ("glucose_event_24h", "bp_event"):
            self.models[target] = [safe_load(MODELS / f"nextday_{target}_fold{k}.joblib") for k in range(5)]
        self.models["spike2h"] = [safe_load(MODELS / f"spike2h_fold{k}.joblib") for k in range(5)]
        self.explainers = {t: [shap.TreeExplainer(b["model"]) for b in self.models[t]] for t in self.models}
        self._summary_cache: dict[str, dict] = {}
        for pid in self.profiles.index:
            self._summary_cache[pid] = self._score(pid)
        self.load_seconds = round(time.time() - t0, 1)

    # ------------------------------------------------------------------ scoring
    def _fold(self, pid):
        return self.fold_of.get(pid, 0)

    def _predict(self, target, pid, row: pd.DataFrame):
        b = self.models[target][self._fold(pid)]
        X = row[b["features"]]
        p = float(b["model"].predict_proba(X)[:, 1][0])
        sv = self.explainers[target][self._fold(pid)].shap_values(X)
        sv = sv[1] if isinstance(sv, list) else sv
        return p, np.asarray(sv)[0], b["features"]

    def _context(self, pid, nights_p: pd.DataFrame, day=DAY):
        bs = self.bstats.loc[pid]
        n = nights_p.iloc[day]
        hrv = n.hrv_rmssd
        return {"tst_last": n.tst_hours if not pd.isna(n.tst_hours) else float("nan"),
                "tst_usual": bs.tst_mean,
                "hrv_change_pct": (hrv / bs.hrv_mean - 1) * 100 if not pd.isna(hrv) else float("nan"),
                "odi_last": n.odi if not pd.isna(n.odi) else 0.0}

    def _score(self, pid, nights_p=None):
        prof = self.profiles.loc[pid]
        if nights_p is None:
            nights_p = self.nights[pid]
            row = self.feats[pid].loc[[DAY]].reset_index()
        else:
            row = patient_features(prof, nights_p, self.cgmd[pid], self.bstats.loc[pid], days=[DAY])
        g, g_sv, g_f = self._predict("glucose_event_24h", pid, row)
        b, b_sv, b_f = self._predict("bp_event", pid, row)
        ctx = self._context(pid, nights_p)
        rd = row.iloc[0].to_dict()
        g_reasons = reasons_from_shap(g_sv, g_f, rd, ctx, k=4, prob=g)
        b_reasons = reasons_from_shap(b_sv, b_f, rd, ctx, k=4, prob=b)
        return {"risk": g, "bp_risk": b, "reasons": g_reasons, "bp_reasons": b_reasons, "row": rd}

    def spike_2h(self, pid):
        ps = PatientSeries(self.cgm[pid], self.meals[pid])
        now = ps.at(NOW_ABS)
        f = ps.features(NOW_ABS)
        nc = night_context(self.nights[pid], self.bstats.loc[pid]).set_index("day").loc[DAY].to_dict()
        prof = self.profiles.loc[pid]
        f.update(nc)
        f.update({k: float(prof[k]) for k in ("hba1c", "prs_t2d", "on_metformin", "on_sglt2i", "on_sulfonylurea")})
        reasons = []
        if pd.isna(now):
            return {"risk": None, "minutes_ahead": None, "alert": False, "current_glucose": None,
                    "trend_mg_dl_per_min": None, "reasons": ["CGM signal missing right now"]}
        if now >= GLUCOSE_THRESHOLD:
            p = 1.0
            reasons.append(f"Glucose already above {GLUCOSE_THRESHOLD:.0f} mg/dL ({now:.0f})")
        else:
            b = self.models["spike2h"][self._fold(pid)]
            p = float(b["model"].predict_proba(pd.DataFrame([f])[b["features"]])[:, 1][0])
        slope = f["slope_30"]
        minutes = None
        if now < GLUCOSE_THRESHOLD and slope and not math.isnan(slope) and slope > 0.05:
            minutes = int(min(120, max(5, round((GLUCOSE_THRESHOLD - now) / slope / 5) * 5)))
        if not reasons:
            if slope and slope > 0.3:
                reasons.append(f"Glucose rising fast: {now:.0f} mg/dL, +{slope * 30:.0f} in 30 min")
            elif slope and slope > 0:
                reasons.append(f"Glucose {now:.0f} mg/dL and rising")
            else:
                reasons.append(f"Glucose {now:.0f} mg/dL, steady or falling")
            if f["minutes_since_meal"] < 120:
                reasons.append(f"Meal logged {f['minutes_since_meal']:.0f} min ago ({f['last_meal_carbs']:.0f} g carbs)")
            if f["debt_last_night"] > 3:
                reasons.append(f"Sleep debt {f['debt_last_night']:.1f} h lowers insulin sensitivity today")
            if prof.hba1c >= 7:
                reasons.append(f"HbA1c {prof.hba1c:.1f}%")
        return {"risk": round(p, 3), "minutes_ahead": minutes if p >= 0.4 else None, "alert": p >= 0.4,
                "current_glucose": _f(now, 0), "trend_mg_dl_per_min": _f(slope, 2), "reasons": reasons[:3],
                "as_of": f"{day_date(DAY)}T{NOW_MINUTE // 60:02d}:{NOW_MINUTE % 60:02d}"}

    # ------------------------------------------------------------------ API views
    def conditions(self, prof) -> list[str]:
        c = []
        if prof.has_t2d:
            c.append("T2D")
        elif prof.has_prediabetes:
            c.append("Prediabetes")
        if prof.has_htn:
            c.append("HTN")
        if prof.has_osa:
            c.append("OSA")
        if not pd.isna(prof.dyslipidemia_dx_year):
            c.append("Dyslipidemia")
        return c or ["No chronic condition"]

    @lru_cache(maxsize=1)
    def patient_list(self):
        out = []
        for pid, prof in self.profiles.iterrows():
            s = self._summary_cache[pid]
            sp = self.spike_2h(pid)
            top = s["reasons"] if s["risk"] >= s["bp_risk"] else s["bp_reasons"]
            top_pos = [r for r in top if r["impact"] > 0 and r["kind"] != "modifier"] or [
                r for r in top if r["impact"] > 0]
            out.append({
                "id": pid, "name": prof["name"], "age": int(prof.age), "sex": prof.sex,
                "conditions": self.conditions(prof), "risk": round(s["risk"], 3), "bp_risk": round(s["bp_risk"], 3),
                "risk_level": risk_level(max(s["risk"], s["bp_risk"])),
                "spike_2h_risk": sp["risk"], "spike_2h_alert": sp["alert"],
                "top_reason": (top_pos[0]["text"] if top_pos else "Within personal normal range"),
                "persona": prof.persona or None,
            })
        out.sort(key=lambda r: -max(r["risk"], r["bp_risk"]))
        return out

    def exists(self, pid):
        return pid in self.profiles.index

    def patient_detail(self, pid):
        prof = self.profiles.loc[pid]
        s = self._summary_cache[pid]
        row = s["row"]
        miss_n = int(row.get("missing_nights_7d", 0) or 0)
        cgm_miss = float(row.get("cgm_missing_pct_24h", 0) or 0)
        dq_level = "low" if (miss_n >= 2 or cgm_miss > 0.2) else "good"
        yr = lambda v: None if pd.isna(v) else int(v)  # noqa: E731
        diagnoses = [
            {"name": "Type 2 diabetes", "year": yr(prof.t2d_dx_year), "active": bool(prof.has_t2d)},
            {"name": "Prediabetes", "year": yr(prof.prediabetes_dx_year),
             "active": bool(prof.has_prediabetes or not pd.isna(prof.prediabetes_dx_year))},
            {"name": "Hypertension", "year": yr(prof.htn_dx_year), "active": bool(prof.has_htn)},
            {"name": "Obstructive sleep apnea", "year": yr(prof.osa_dx_year), "active": bool(prof.has_osa)},
            {"name": "Dyslipidemia", "year": yr(prof.dyslipidemia_dx_year),
             "active": not pd.isna(prof.dyslipidemia_dx_year)},
        ]
        labs = [
            ("HbA1c", "hba1c", "%", 1), ("Fasting glucose", "fasting_glucose", "mg/dL", 0),
            ("LDL cholesterol", "ldl", "mg/dL", 0), ("HDL cholesterol", "hdl", "mg/dL", 0),
            ("Triglycerides", "triglycerides", "mg/dL", 0), ("eGFR", "egfr", "mL/min/1.73m²", 0),
            ("Clinic SBP", "sbp_clinic", "mmHg", 0), ("Clinic DBP", "dbp_clinic", "mmHg", 0),
        ]
        meds = [m for m, k in (("Metformin", "on_metformin"), ("SGLT2 inhibitor", "on_sglt2i"),
                               ("Sulfonylurea", "on_sulfonylurea"), ("Beta-blocker (metoprolol)", "on_beta_blocker"),
                               ("ACE inhibitor", "on_ace_inhibitor")) if prof[k]]
        return {
            "id": pid, "persona": prof.persona or None,
            "profile": {
                "demographics": {"name": prof["name"], "age": int(prof.age), "sex": prof.sex, "bmi": _f(prof.bmi),
                                 "waist_cm": _f(prof.waist_cm, 0), "city": prof.city},
                "conditions": self.conditions(prof),
                "diagnoses": [d for d in diagnoses if d["active"]],
                "labs": [{"name": n, "value": _f(prof[k], nd), "prior": _f(prof[k + "_prior"], nd), "unit": u,
                          "date": prof.labs_date, "prior_date": prof.labs_prior_date} for n, k, u, nd in labs],
                "medications": meds,
                "genetic_markers": {
                    "simulated": True,
                    "prs_t2d": _f(prof.prs_t2d, 2),
                    "tcf7l2_risk_alleles": int(prof.tcf7l2_risk_alleles),
                    "mtnr1b_risk_allele": int(prof.mtnr1b_risk_allele),
                    "notes": {
                        "prs_t2d": "Polygenic risk z-score for type 2 diabetes (0 = population average)",
                        "tcf7l2_risk_alleles": "TCF7L2 rs7903146-T copies (0/1/2); impairs insulin secretion",
                        "mtnr1b_risk_allele": "MTNR1B rs10830963-G carrier; late eating/sleep timing hurts glucose more",
                    }},
            },
            "risk": round(s["risk"], 3), "bp_risk": round(s["bp_risk"], 3),
            "risk_level": risk_level(max(s["risk"], s["bp_risk"])),
            "glucose_level": risk_level(s["risk"]), "bp_level": risk_level(s["bp_risk"]),
            "reasons": [{"text": r["text"], "impact": r["impact"], "kind": r["kind"]} for r in s["reasons"]],
            "bp_reasons": [{"text": r["text"], "impact": r["impact"], "kind": r["kind"]} for r in s["bp_reasons"]],
            "spike_2h": self.spike_2h(pid),
            "masking": self.masking(pid, row),
            "apnea_flag": self.apnea_flag(pid),
            "data_quality": {"level": dq_level, "missing_nights_7d": miss_n,
                             "cgm_missing_pct_24h": round(cgm_miss * 100, 1)},
            "forecast_for": str(day_date(DAY)),
            "disclaimer": DISCLAIMER, "simulated": True,
        }

    def apnea_flag(self, pid):
        """Hidden sleep apnea: frequent oxygen dips although sleep length looks fine and no OSA diagnosis."""
        n = self.nights[pid].iloc[DAY - 6: DAY + 1]
        odi = float(n.odi.mean()) if n.odi.notna().any() else float("nan")
        if math.isnan(odi) or odi < 15:
            return None
        prof = self.profiles.loc[pid]
        tst = float(n.tst_hours.mean())
        return {"odi_7d": _f(odi, 0), "tst_7d": _f(tst, 1), "diagnosed": bool(prof.has_osa),
                "text": (f"~{odi:.0f} oxygen dips per hour over the last week" +
                         (f" despite {tst:.1f} h of sleep - a normal sleep app would call this fine." if tst >= 6.5
                          else ".") +
                         (" Known OSA - check CPAP use." if prof.has_osa else
                          " No apnea diagnosis on record: consider a sleep study."))}

    def masking(self, pid, row):
        """Beta-blocker masking: heart rate barely moves, HRV still shows the strain."""
        prof = self.profiles.loc[pid]
        if not prof.on_beta_blocker:
            return None
        bs = self.bstats.loc[pid]
        hrv = self.nights[pid].loc[DAY, "hrv_rmssd"]
        if pd.isna(hrv):
            return None
        hrv_pct = (hrv / bs.hrv_mean - 1) * 100
        rhr_d = row.get("rhr_delta")
        flagged = hrv_pct <= -20 and rhr_d is not None and rhr_d < 4
        return {"on_beta_blocker": True, "flagged": bool(flagged), "hrv_change_pct": _f(hrv_pct, 0),
                "rhr_delta": _f(rhr_d, 1),
                "text": (f"On a beta-blocker: resting HR only {rhr_d:+.0f} bpm, but HRV is down {abs(hrv_pct):.0f}% - "
                         "the twin watches HRV so this strain is not missed.") if flagged else
                "On a beta-blocker: the twin relies on HRV rather than heart rate."}

    def trends(self, pid):
        n = self.nights[pid]
        bs = self.bstats.loc[pid]
        cd = self.cgmd[pid].set_index("day")
        band = lambda k: [_f(bs[f"{k}_mean"] - bs[f"{k}_sd"], 2), _f(bs[f"{k}_mean"] + bs[f"{k}_sd"], 2)]  # noqa
        days = []
        for r in n.itertuples():
            days.append({
                "date": str(day_date(r.day)), "day": int(r.day) + 1,
                "tst": _f(r.tst_hours, 2), "tst_band": band("tst"),
                "hrv": _f(r.hrv_rmssd), "hrv_band": band("hrv"),
                "rhr": _f(r.resting_heart_rate), "rhr_band": band("rhr"),
                "odi": _f(r.odi), "odi_band": band("odi"),
                "steps": _f(r.steps, 0), "steps_band": band("steps"),
                "efficiency": _f(r.efficiency * 100 if not pd.isna(r.efficiency) else None),
                "deep_pct": _f(r.deep_pct), "rem_pct": _f(r.rem_pct), "waso": _f(r.waso_min, 0),
                "tir": _f(cd.loc[r.day, "tir"] * 100) if r.day in cd.index else None,
                "cgm_peak": _f(cd.loc[r.day, "cgm_max"], 0) if r.day in cd.index else None,
                "missing": bool(r.night_missing), "partial": False,
            })
        # today (day 21) is only observed up to "now" - never show the rest of the day (it is what we forecast)
        cg_all = self.cgm[pid]
        today = cg_all[(cg_all.t >= DAY * 1440) & (cg_all.t <= NOW_ABS)].glucose_mg_dl
        days[-1]["cgm_peak"] = _f(today.max(), 0)
        days[-1]["tir"] = _f(((today >= 70) & (today <= GLUCOSE_THRESHOLD)).sum() / max(1, today.notna().sum()) * 100)
        days[-1]["partial"] = True
        days[-1]["steps"] = None  # today's step count is not complete at 13:00
        h = self.hyp[pid].loc[DAY]
        start = float(h.bedtime_min) - 1440  # minutes relative to midnight
        stages = [{"t": _hhmm(start + i * 5), "stage": {"W": "Wake", "L": "Light", "D": "Deep", "R": "REM"}[c]}
                  for i, c in enumerate(h.stages)]
        cg = self.cgm[pid]
        win = cg[(cg.t > NOW_ABS - 48 * 60) & (cg.t <= NOW_ABS)]
        cgm48 = [{"t": f"{day_date(t // 1440)}T{(t % 1440) // 60:02d}:{t % 60:02d}", "glucose": _f(g, 0)}
                 for t, g in zip(win.t, win.glucose_mg_dl)]
        return {"id": pid, "days": days, "baseline_days": 14,
                "personal_normal": {k: {"mean": _f(bs[f"{k}_mean"], 2), "sd": _f(bs[f"{k}_sd"], 2)}
                                    for k in ("tst", "hrv", "rhr", "odi", "steps")},
                "hypnogram": {"date": str(day_date(DAY)), "epoch_min": 5, "stages": stages,
                              "missing": bool(h.night_missing)},
                "cgm_48h": cgm48, "cgm_target": [70, 180], "simulated": True}

    # ------------------------------------------------------------------ What-If
    def typical_meals(self, pid):
        m = self.meals[pid]
        g = m.groupby("meal").agg(t=("minute_of_day", "mean"), c=("carbs_g", "mean"))
        return g.t.to_numpy(float), g.c.to_numpy(float)

    def _scenario_nights(self, pid, sleep_hours, bedtime_shift_h, cpap, nights_n):
        """Apply the doctor's scenario as *changes* on top of what the watch actually recorded, so an
        unchanged scenario reproduces the current forecast exactly. CPAP -> ODI x 0.2, WASO x 0.6."""
        n = self.nights[pid].copy()
        sb = self.sim_base.loc[pid]
        prof = self.profiles.loc[pid]
        days = list(range(DAY - nights_n + 1, DAY + 1))
        tst_old_true = n.tst_hours_true.to_numpy(float)
        tst_true = tst_old_true.copy()
        tst_true[days] = sleep_hours
        debt_old = ph.sleep_debt(tst_old_true[None, :], [sb.tst_base])[0]
        debt_new = ph.sleep_debt(tst_true[None, :], [sb.tst_base])[0]
        bb = bool(prof.on_beta_blocker)
        for d in days:
            obs = n.loc[d]
            base = {c: (obs[c] if not pd.isna(obs[c]) else obs[c + "_true"])
                    for c in ("tst_hours", "bedtime_shift_h", "waso_min", "odi", "deep_pct", "efficiency",
                              "hrv_rmssd", "resting_heart_rate")}
            waso_new = base["waso_min"] * (0.6 if cpap else 1.0)
            odi_new = base["odi"] * (0.2 if cpap else 1.0)
            deep_new = min(30.0, base["deep_pct"] + 0.15 * (base["odi"] - odi_new))
            eff = lambda tst, w, sh: tst * 60 / (tst * 60 + w + 12 + 4 * abs(sh))  # noqa: E731
            eff_new = base["efficiency"] + eff(sleep_hours, waso_new, bedtime_shift_h) - eff(
                base["tst_hours"], base["waso_min"], base["bedtime_shift_h"])

            def heart(tst, debt, sh, odi):
                return night_heart(sb, np.array([max(0.0, sb.tst_base - tst)]), np.array([debt]), np.array([sh]),
                                   np.array([odi]), bb, np.ones(1), np.zeros(1))
            h_old, r_old = heart(base["tst_hours"], debt_old[d], base["bedtime_shift_h"], base["odi"])
            h_new, r_new = heart(sleep_hours, debt_new[d], bedtime_shift_h, odi_new)
            n.loc[d, ["tst_hours", "bedtime_shift_h", "waso_min", "odi", "deep_pct", "efficiency", "hrv_rmssd",
                      "resting_heart_rate", "night_missing"]] = [
                sleep_hours, bedtime_shift_h, waso_new, odi_new, deep_new, float(np.clip(eff_new, 0.4, 1.0)),
                float(base["hrv_rmssd"] * h_new[0] / h_old[0]),
                float(base["resting_heart_rate"] + r_new[0] - r_old[0]), False]
        return n, tst_true, debt_new

    def _si_for(self, pid, n: pd.DataFrame, tst_true, debt):
        prof = self.profiles.loc[pid]
        sb = self.sim_base.loc[pid]
        shift = n.loc[DAY, "bedtime_shift_h"] if not pd.isna(n.loc[DAY, "bedtime_shift_h"]) else n.loc[
            DAY, "bedtime_shift_h_true"]
        waso = n.loc[DAY, "waso_min"] if not pd.isna(n.loc[DAY, "waso_min"]) else n.loc[DAY, "waso_min_true"]
        dsteps = (n.loc[DAY - 1, "steps"] - sb.steps_base) / 1000
        si = ph.si_series([self.params.loc[pid, "si_0"]], np.array([[debt[DAY]]]), np.array([[shift]]),
                          np.array([[waso]]), [prof.mtnr1b_risk_allele], np.array([[dsteps]]), [prof.on_metformin])
        return float(si[0, 0])

    def what_if(self, pid, sleep_hours: float, bedtime_shift_h: float, cpap: bool, nights: int = 1):
        t0 = time.perf_counter()
        before = self._summary_cache[pid]
        n_before = self.nights[pid]
        tst_b = n_before.tst_hours_true.to_numpy(float)
        debt_b = ph.sleep_debt(tst_b[None, :], [self.sim_base.loc[pid, "tst_base"]])[0]
        si_before = self._si_for(pid, n_before, tst_b, debt_b)

        n_after, tst_a, debt_a = self._scenario_nights(pid, sleep_hours, bedtime_shift_h, cpap, nights)
        after = self._score(pid, n_after)
        si_after = self._si_for(pid, n_after, tst_a, debt_a)

        pr = self.params.loc[pid]
        mt, mc = self.typical_meals(pid)
        G = ph.deterministic_day_curve(np.array([pr.gb, pr.gb]), np.array([si_before, si_after]),
                                       np.array([pr.beta, pr.beta]), np.array([pr.v_dl, pr.v_dl]),
                                       np.vstack([mt, mt]), np.vstack([mc, mc]))
        sb = self.profiles.loc[pid]
        ms = round((time.perf_counter() - t0) * 1000)
        return {
            "id": pid, "inputs": {"sleep_hours": sleep_hours, "bedtime_shift_h": bedtime_shift_h, "cpap": cpap,
                                  "nights": nights},
            "risk_before": round(before["risk"], 3), "risk_after": round(after["risk"], 3),
            "bp_before": round(before["bp_risk"], 3), "bp_after": round(after["bp_risk"], 3),
            "level_before": risk_level(max(before["risk"], before["bp_risk"])),
            "level_after": risk_level(max(after["risk"], after["bp_risk"])),
            "glucose_before": [round(float(x), 1) for x in G[0]],
            "glucose_after": [round(float(x), 1) for x in G[1]],
            "peak_before": round(float(G[0].max()), 0), "peak_after": round(float(G[1].max()), 0),
            "si_change_pct": round((si_after / si_before - 1) * 100, 1),
            "reasons_after": [{"text": r["text"], "impact": r["impact"], "kind": r["kind"]} for r in after["reasons"]],
            "bp_reasons_after": [{"text": r["text"], "impact": r["impact"], "kind": r["kind"]} for r in after["bp_reasons"]],
            "current_night": {"sleep_hours": _f(n_before.loc[DAY, "tst_hours"], 1),
                              "bedtime_shift_h": _f(n_before.loc[DAY, "bedtime_shift_h"], 1),
                              "odi": _f(n_before.loc[DAY, "odi"], 1), "usual_sleep_hours": _f(
                    self.bstats.loc[pid, "tst_mean"], 1)},
            "sex": sb.sex, "compute_ms": ms, "disclaimer": DISCLAIMER,
        }

    def model_summary(self):
        def load(name):
            p = REPORTS / name
            return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None
        from .calibration import read_meta
        return {"nextday": load("nextday_metrics.json"), "spike_2h": load("spike2h_metrics.json"),
                "lifesnaps_validation": load("lifesnaps_validation.json"), "data_card": data_card(read_meta()),
                "disclaimer": DISCLAIMER}


def _hhmm(minutes):
    m = int(minutes) % 1440
    return f"{m // 60:02d}:{m % 60:02d}"


def data_card(meta: dict) -> dict:
    return {
        "cohort": f"{meta.get('n_patients', 300)} virtual patients x {meta.get('n_days', 21)} days (SIMULATED)",
        "static_stream": "Synthetic EHR: demographics, diagnoses + years, labs (latest + prior), medications, "
                         "simulated genetic markers (TCF7L2, MTNR1B, T2D PRS)",
        "dynamic_stream": "Simulated wearables: sleep stages (5-min), HRV, resting HR, steps, SpO2 dips, "
                          "CGM every 5 min (Bergman minimal model)",
        "ehr_calibration": meta.get("ehr_calibration"),
        "wearable_calibration": meta.get("wearable_calibration"),
        "cohort_mix": meta.get("cohort_mix"),
        "event_rate_glucose": meta.get("event_rate_glucose_pred_days"),
        "event_rate_bp": meta.get("event_rate_bp_pred_days"),
        "glucose_range": [meta.get("glucose_min"), meta.get("glucose_max")],
        "si_drop_4x5h": meta.get("si_drop_4x5h_check"),
        "missing_nights_pct": meta.get("missing_nights_pct"),
        "cgm_missing_pct": meta.get("cgm_missing_pct"),
        "sandbox": "Only synthetic, anonymized (NHANES) or open-source (LifeSnaps CC-BY-4.0) data. "
                   "No real patient data, no personal data.",
    }


_TWIN: Twin | None = None


def get_twin() -> Twin:
    global _TWIN
    if _TWIN is None:
        _TWIN = Twin()
    return _TWIN
