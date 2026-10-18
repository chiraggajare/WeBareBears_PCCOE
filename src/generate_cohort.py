"""Generate the full virtual cohort: 300 patients x 21 days, both data streams.

    python -m src.generate_cohort

Writes Parquet files to data/processed/:
  profiles.parquet     static EHR (demographics, diagnoses + years, labs, meds, genetic markers)
  baselines.parquet    per-patient personal wearable ranges (from LifeSnaps people)
  nights.parquet       nightly sleep summary, HRV, RHR, ODI + next-day steps (observed + *_true)
  hypnograms.parquet   5-min sleep-stage epochs per night
  meals.parquet        meal log (time, carbs)
  cgm.parquet          5-min CGM for all 21 days (glucose_mg_dl, with ~5% dropout)
  daily.parquet        latent SI, sleep debt, morning SBP, labels (glucose_event_24h, bp_event)
"""
from __future__ import annotations

import time

import numpy as np
import pandas as pd

from . import physiology as ph
from .calibration import write_meta
from .config import GLUCOSE_THRESHOLD, N_DAYS, PROCESSED, SAMPLES_PER_DAY, SBP_THRESHOLD, SEED, day_date
from .profiles import generate_profiles
from .wearables import (apply_persona_baselines, build_hypnograms, persona_overrides, personal_baselines,
                        simulate_nights)

CGM_DROPOUT_HOURS = 0.05
GB_SHRINK = 0.45


def physiology_params(profiles: pd.DataFrame) -> pd.DataFrame:
    p = pd.DataFrame({"patient_id": profiles.patient_id})
    p["si_0"] = ph.si0(profiles.bmi, profiles.hba1c, profiles.age, profiles.prs_t2d, profiles.tcf7l2_risk_alleles)
    p["beta"] = ph.beta_cell(profiles.hba1c, profiles.tcf7l2_risk_alleles, profiles.has_t2d,
                             profiles.on_sulfonylurea)
    p["v_dl"] = ph.V_PER_KG * ph.weight_kg(profiles.bmi, profiles.sex)
    # CGM basal glucose. A single lab FPG overstates the free-living CGM basal level of treated patients,
    # so it is shrunk 55% toward 90 mg/dL - a documented calibration choice that keeps the next-day
    # event rate inside the plan's 15-30% band (plan 6.6). SGLT2i users lose a little more via glycosuria.
    fpg = np.clip(profiles.fasting_glucose.to_numpy(float), 75, 220)
    p["gb"] = 90 + GB_SHRINK * (fpg - 90) - np.where(profiles.on_sglt2i, 6, 0)
    return p


def make_meals(profiles: pd.DataFrame, rng) -> pd.DataFrame:
    n = len(profiles)
    personal_carbs = rng.normal(60, 11, n)   # habitual diet differs between people (not in the EHR)
    rows = []
    for d in range(N_DAYS):
        for meal, (t0, sd) in enumerate([(7.75 * 60, 30), (13.0 * 60, 40), (20.25 * 60, 40)]):
            t = np.clip(rng.normal(t0, sd, n), t0 - 90, t0 + 90)
            c = np.clip(rng.normal(personal_carbs, 15), 20, 120)
            rows.append(pd.DataFrame({"patient_id": profiles.patient_id, "day": d, "meal": meal,
                                      "minute_of_day": np.round(t), "carbs_g": np.round(c)}))
    meals = pd.concat(rows, ignore_index=True)
    # personas: regular meals so their glucose story is driven by sleep, lunch on day 21 at 12:30
    for pid in ("A", "B", "C"):
        m = meals.patient_id == pid
        meals.loc[m, "minute_of_day"] = meals.loc[m, "meal"].map({0: 465, 1: 780, 2: 1215})
        meals.loc[m, "carbs_g"] = meals.loc[m, "meal"].map({0: 55, 1: 65, 2: 60})
    a = meals.patient_id == "A"           # A follows a diabetic meal plan (smaller carb portions)
    meals.loc[a, "carbs_g"] = meals.loc[a, "meal"].map({0: 45, 1: 52, 2: 48})
    meals.loc[a & (meals.day == N_DAYS - 1) & (meals.meal == 1), ["minute_of_day", "carbs_g"]] = [750, 58]
    return meals.sort_values(["patient_id", "day", "meal"]).reset_index(drop=True)


def daily_si(profiles, base, nights, params, rng):
    pids = profiles.patient_id.tolist()
    piv = lambda col: nights.pivot(index="patient_id", columns="day", values=col).loc[pids].to_numpy()  # noqa: E731
    tst = piv("tst_hours_true")
    shift = piv("bedtime_shift_h_true")
    waso = piv("waso_min_true")
    odi = piv("odi_true")
    steps = piv("steps")
    debt = ph.sleep_debt(tst, base.tst_base.to_numpy())
    dsteps_prev = np.zeros_like(steps)
    dsteps_prev[:, 1:] = (steps[:, :-1] - base.steps_base.to_numpy()[:, None]) / 1000
    noise = rng.lognormal(0, ph.SIGMA, size=tst.shape)
    for pid in ("A", "B", "C"):
        noise[pids.index(pid)] = 1.0
    si = ph.si_series(params.si_0, debt, shift, waso, profiles.mtnr1b_risk_allele, dsteps_prev,
                      profiles.on_metformin, noise)
    return si, debt, waso, odi


def run(seed: int = SEED, verbose: bool = True) -> dict:
    t0 = time.time()
    rng = np.random.default_rng(seed + 10)
    profiles, ehr_source = generate_profiles(seed=seed)
    base, ls_source = personal_baselines(profiles, seed)
    base = apply_persona_baselines(base)
    nights = simulate_nights(profiles, base, seed, overrides=persona_overrides(base))
    hyp = build_hypnograms(nights, seed)
    params = physiology_params(profiles)
    meals = make_meals(profiles, rng)

    si, debt, waso, odi = daily_si(profiles, base, nights, params, rng)

    n = len(profiles)
    pids = profiles.patient_id.tolist()
    mt = meals.assign(abs_min=meals.day * 1440 + meals.minute_of_day).pivot_table(
        index="patient_id", columns=["day", "meal"], values="abs_min").loc[pids].to_numpy(float)
    cb = meals.pivot_table(index="patient_id", columns=["day", "meal"], values="carbs_g").loc[pids].to_numpy(float)
    G, _, _ = ph.simulate_glucose(params.gb.to_numpy(), lambda m: si[:, min(m // 1440, N_DAYS - 1)],
                                  params.beta.to_numpy(), params.v_dl.to_numpy(), mt, cb, N_DAYS * 1440)
    cgm_true = G[:, ::5].astype(float)
    cgm = np.clip(cgm_true + rng.normal(0, ph.CGM_NOISE, cgm_true.shape), 40, 400)
    cgm_obs = cgm.copy()
    hours = cgm.reshape(n, N_DAYS * 24, 12)
    drop = rng.random((n, N_DAYS * 24)) < CGM_DROPOUT_HOURS
    for pid in ("A", "B", "C"):
        drop[pids.index(pid), -48:] = False
    cgm_obs = np.where(np.repeat(drop, 12, axis=1), np.nan, cgm_obs)
    del hours

    sbp_noise = rng.normal(0, ph.BP_NOISE, size=si.shape)
    # home-vs-clinic offset (white-coat / masked hypertension) - stable per patient, unknown to the EHR
    sbp_noise += rng.normal(0, ph.HOME_CLINIC_SD, size=(n, 1))
    for pid in ("A", "B", "C"):
        sbp_noise[pids.index(pid)] = 0.0
    sbp_m = ph.morning_sbp(profiles.sbp_clinic, odi, debt, waso, profiles.on_ace_inhibitor, sbp_noise)

    peak = cgm.reshape(n, N_DAYS, SAMPLES_PER_DAY).max(axis=2)
    daily = pd.DataFrame({
        "patient_id": np.repeat(pids, N_DAYS), "day": np.tile(np.arange(N_DAYS), n),
        "si": si.ravel(), "si_0": np.repeat(params.si_0.to_numpy(), N_DAYS), "sleep_debt": debt.ravel(),
        "cgm_peak": peak.ravel(), "sbp_morning": sbp_m.ravel(),
    })
    daily["date"] = daily.day.map(lambda d: str(day_date(d)))
    daily["glucose_event_24h"] = (daily.cgm_peak > GLUCOSE_THRESHOLD).astype(int)
    daily["bp_event"] = (daily.sbp_morning > SBP_THRESHOLD).astype(int)

    cgm_long = pd.DataFrame({
        "patient_id": np.repeat(pids, N_DAYS * SAMPLES_PER_DAY),
        "t": np.tile(np.arange(N_DAYS * SAMPLES_PER_DAY) * 5, n),
        "glucose_mg_dl": cgm_obs.ravel().astype(np.float32),
        "glucose_noisy": cgm.ravel().astype(np.float32),
    })
    cgm_long["day"] = cgm_long.t // 1440
    cgm_long["minute_of_day"] = cgm_long.t % 1440

    profiles.to_parquet(PROCESSED / "profiles.parquet")
    base.to_parquet(PROCESSED / "baselines.parquet")
    params.to_parquet(PROCESSED / "physiology_params.parquet")
    nights.to_parquet(PROCESSED / "nights.parquet")
    hyp.to_parquet(PROCESSED / "hypnograms.parquet")
    meals.to_parquet(PROCESSED / "meals.parquet")
    cgm_long.to_parquet(PROCESSED / "cgm.parquet")
    daily.to_parquet(PROCESSED / "daily.parquet")

    pred = daily[daily.day >= 14]
    stats = {
        "n_patients": n, "n_days": N_DAYS,
        "ehr_calibration": ehr_source, "wearable_calibration": ls_source,
        "glucose_min": float(np.nanmin(cgm)), "glucose_max": float(np.nanmax(cgm)),
        "event_rate_glucose_pred_days": float(pred.glucose_event_24h.mean()),
        "event_rate_bp_pred_days": float(pred.bp_event.mean()),
        "event_rate_by_group": profiles.assign(g=np.select([profiles.has_t2d, profiles.has_prediabetes],
                                                            ["t2d", "prediabetes"], "healthy"))
        .merge(pred.groupby("patient_id").glucose_event_24h.mean().rename("r"), on="patient_id")
        .groupby("g").r.mean().round(3).to_dict(),
        "cohort_mix": {"t2d": float(profiles.has_t2d.mean()), "prediabetes": float(profiles.has_prediabetes.mean()),
                       "htn": float(profiles.has_htn.mean()), "osa_true": float(profiles.has_osa_true.mean()),
                       "osa_diagnosed": float(profiles.osa_diagnosed.mean())},
        "missing_nights_pct": float(nights.night_missing.mean()),
        "cgm_missing_pct": float(np.isnan(cgm_obs).mean()),
        "si_drop_4x5h_check": si_restriction_check(),
        "seconds": round(time.time() - t0, 1),
    }
    write_meta(stats)
    if verbose:
        import json
        print(json.dumps(stats, indent=2))
    return stats


def si_restriction_check() -> float:
    """Exit-criterion check: 4 nights of 5 h vs a 7.5 h baseline -> fractional SI drop."""
    tst = np.array([[7.5] * 6 + [5.0] * 4])
    debt = ph.sleep_debt(tst, [7.5])[0, -1]
    return round(1 - float(np.exp(-ph.A1 * debt)), 3)


if __name__ == "__main__":
    run()
