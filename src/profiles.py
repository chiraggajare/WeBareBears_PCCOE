"""Synthetic EHR generator (static / historical stream).

Every virtual patient gets: demographics, past diagnoses with years, lab results
(latest + 1 prior), medications and SIMULATED genetic markers.

Calibration
-----------
* Clinical variables are resampled from real anonymized NHANES 2017-Mar 2020 adults
  (survey-weighted, stratified by glycemic group) and jittered, so correlations
  between age, BMI, BP, HbA1c, glucose, eGFR and lipids follow the real population.
* Cohort mix (plan 6.1): ~40% T2D, ~25% prediabetes, ~35% healthy; HTN and OSA
  follow from the sampled people (OSA probability rises with BMI, age, male sex).
* Genetic markers use 1000 Genomes phase 3 South Asian (SAS) allele frequencies,
  verified via Ensembl REST:  TCF7L2 rs7903146-T = 0.299,  MTNR1B rs10830963-G = 0.426.
  Cases are enriched using published per-allele odds ratios (TCF7L2 OR ~1.4,
  Grant et al. 2006; MTNR1B OR ~1.15, Prokopenko et al. 2009). The PRS is a z-score.
  All genetic markers are SIMULATED and labeled as such in the UI.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .calibration import load_nhanes_pool
from .config import CURRENT_YEAR, N_PATIENTS, PERSONA_IDS, SEED, START_DATE

TCF7L2_RAF_SAS = 0.299
MTNR1B_RAF_SAS = 0.426
TCF7L2_OR = 1.4
MTNR1B_OR = 1.15
MIX = {"t2d": 0.40, "prediabetes": 0.25, "healthy": 0.35}

FIRST_M = ["Aarav", "Rohan", "Vikram", "Arjun", "Karan", "Sanjay", "Rahul", "Amit", "Deepak", "Nikhil",
           "Suresh", "Manoj", "Rakesh", "Imran", "Farhan", "Harish", "Gaurav", "Pranav", "Kunal", "Siddharth",
           "Anil", "Vivek", "Ramesh", "Mohit", "Tarun", "Naveen", "Ajay", "Abhishek", "Yash", "Varun"]
FIRST_F = ["Priya", "Ananya", "Kavya", "Sneha", "Pooja", "Neha", "Meera", "Divya", "Lakshmi", "Aisha",
           "Fatima", "Riya", "Shreya", "Nandini", "Swati", "Anjali", "Isha", "Radhika", "Sunita", "Geeta",
           "Pallavi", "Tanvi", "Bhavana", "Rekha", "Zoya", "Asha", "Deepa", "Kiran", "Manisha", "Nisha"]
LAST = ["Sharma", "Iyer", "Patel", "Reddy", "Nair", "Gupta", "Menon", "Rao", "Desai", "Kulkarni",
        "Joshi", "Mehta", "Bose", "Chatterjee", "Khan", "Singh", "Verma", "Pillai", "Shetty", "Agarwal",
        "Banerjee", "Kapoor", "Malhotra", "Naidu", "Hegde", "Saxena", "Mishra", "Pandey", "Qureshi", "Das"]
CITIES = ["Mumbai", "Delhi", "Bengaluru", "Chennai", "Hyderabad", "Pune", "Kolkata", "Ahmedabad"]


def _sample_alleles(rng, n, raf, or_, case_weight):
    """Per-allele odds ratio shifts risk-allele frequency in cases (case_weight in [0,1])."""
    raf_case = or_ * raf / (1 - raf + or_ * raf)
    p = raf + case_weight * (raf_case - raf)
    return p


def _year_from_age(age_now, age_dx):
    return int(CURRENT_YEAR - max(0, round(age_now - age_dx)))


def generate_profiles(n: int = N_PATIENTS, seed: int = SEED) -> tuple[pd.DataFrame, str]:
    rng = np.random.default_rng(seed)
    pool, source = load_nhanes_pool()
    n_random = n - len(PERSONA_IDS)

    groups = rng.choice(list(MIX), size=n_random, p=list(MIX.values()))
    rows = []
    for g in groups:
        sub = pool[pool.glycemic == g]
        w = sub.weight.fillna(sub.weight.median()).to_numpy()
        rows.append(sub.iloc[rng.choice(len(sub), p=w / w.sum())])
    base = pd.DataFrame(rows).reset_index(drop=True)

    df = pd.DataFrame()
    df["patient_id"] = [f"P{i:03d}" for i in range(1, n_random + 1)]
    sex = base.sex.to_numpy()
    df["name"] = [f"{rng.choice(FIRST_M if s == 'M' else FIRST_F)} {rng.choice(LAST)}" for s in sex]
    df["age"] = np.clip(np.round(base.age + rng.normal(0, 1.5, n_random)), 22, 78).astype(int)
    df["sex"] = sex
    df["bmi"] = np.round(base.bmi * rng.normal(1, 0.03, n_random), 1)
    df["waist_cm"] = np.round(base.waist_cm * rng.normal(1, 0.02, n_random), 0)
    df["city"] = rng.choice(CITIES, n_random)

    glyc = groups
    df["has_t2d"] = glyc == "t2d"
    df["has_prediabetes"] = glyc == "prediabetes"

    # ---- labs (latest) with small jitter for anonymization
    df["hba1c"] = np.round(np.clip(base.hba1c + rng.normal(0, 0.1, n_random), 4.3, 13), 1)
    df["fasting_glucose"] = np.round(np.clip(base.fasting_glucose * rng.normal(1, 0.03, n_random), 70, 320))
    df["ldl"] = np.round(np.clip(base.ldl * rng.normal(1, 0.04, n_random), 35, 250))
    df["hdl"] = np.round(np.clip(base.hdl * rng.normal(1, 0.04, n_random), 22, 105))
    df["triglycerides"] = np.round(np.clip(base.triglycerides * rng.normal(1, 0.05, n_random), 35, 600))
    df["egfr"] = np.round(np.clip(base.egfr * rng.normal(1, 0.03, n_random), 15, 135))
    df["sbp_clinic"] = np.round(np.clip(base.sbp + rng.normal(0, 3, n_random), 92, 200))
    df["dbp_clinic"] = np.round(np.clip(base.dbp + rng.normal(0, 2, n_random), 50, 120))

    # ---- diagnoses + years
    told_dm = base.told_diabetes.to_numpy()
    age_dx_dm = base.age_dx_diabetes.to_numpy()
    t2d_year = []
    for i in range(n_random):
        if glyc[i] != "t2d":
            t2d_year.append(np.nan)
        elif told_dm[i] and not np.isnan(age_dx_dm[i]):
            t2d_year.append(_year_from_age(df.age[i], min(age_dx_dm[i], df.age[i])))
        else:
            t2d_year.append(CURRENT_YEAR - int(rng.integers(0, 10)))
    df["t2d_dx_year"] = t2d_year
    df["prediabetes_dx_year"] = np.where(
        df.has_prediabetes & (rng.random(n_random) < 0.6), CURRENT_YEAR - rng.integers(0, 6, n_random), np.nan)
    df.loc[df.has_t2d & (rng.random(n_random) < 0.5), "prediabetes_dx_year"] = (
        df.t2d_dx_year - rng.integers(1, 5, n_random))

    df["has_htn"] = (base.htn.to_numpy()) | (df.sbp_clinic >= 140) | (df.dbp_clinic >= 90)
    age_dx_htn = base.age_dx_htn.to_numpy()
    df["htn_dx_year"] = [
        (_year_from_age(df.age[i], min(age_dx_htn[i], df.age[i])) if not np.isnan(age_dx_htn[i])
         else CURRENT_YEAR - int(rng.integers(0, 12))) if df.has_htn[i] else np.nan
        for i in range(n_random)]

    # OSA: ~20% overall, rises with BMI, age, male sex; most cases undiagnosed
    logit = -2.25 + 0.15 * (df.bmi - 28) + 0.03 * (df.age - 45) + 0.6 * (df.sex == "M")
    df["has_osa_true"] = rng.random(n_random) < 1 / (1 + np.exp(-logit))
    df["osa_diagnosed"] = df.has_osa_true & (rng.random(n_random) < 0.25)
    df["osa_dx_year"] = np.where(df.osa_diagnosed, CURRENT_YEAR - rng.integers(0, 6, n_random), np.nan)
    df["has_osa"] = df.osa_diagnosed  # what the EHR knows

    dyslip = (df.ldl >= 160) | (base.told_chol.to_numpy() & (rng.random(n_random) < 0.8))
    df["dyslipidemia_dx_year"] = np.where(dyslip, CURRENT_YEAR - rng.integers(0, 12, n_random), np.nan)

    # ---- medications
    t2d = df.has_t2d.to_numpy()
    htn_dx = df.has_htn.to_numpy()
    df["on_metformin"] = (t2d & (rng.random(n_random) < 0.85)) | (df.has_prediabetes & (rng.random(n_random) < 0.10))
    df["on_sglt2i"] = t2d & (rng.random(n_random) < 0.20)
    df["on_sulfonylurea"] = t2d & (rng.random(n_random) < 0.25)
    df["on_ace_inhibitor"] = htn_dx & (rng.random(n_random) < 0.55)
    df["on_beta_blocker"] = htn_dx & (rng.random(n_random) < 0.30)

    # ---- simulated genetic markers
    case_w = np.where(glyc == "t2d", 1.0, np.where(glyc == "prediabetes", 0.5, 0.0))
    p_t = _sample_alleles(rng, n_random, TCF7L2_RAF_SAS, TCF7L2_OR, case_w)
    df["tcf7l2_risk_alleles"] = rng.binomial(2, p_t)
    p_m = _sample_alleles(rng, n_random, MTNR1B_RAF_SAS, MTNR1B_OR, case_w)
    df["mtnr1b_risk_allele"] = (rng.binomial(2, p_m) > 0).astype(int)  # carrier of rs10830963-G
    df["prs_t2d"] = np.round(rng.normal(0.45 * case_w, 1.0), 2)

    df["persona"] = ""
    df = pd.concat([persona_profiles(), df], ignore_index=True)
    df = _add_prior_labs(df, rng)
    return df, source


def persona_profiles() -> pd.DataFrame:
    """The three hand-crafted demo patients (plan 6.7)."""
    common = dict(city="Mumbai", osa_dx_year=np.nan, has_osa=False, osa_diagnosed=False, on_sglt2i=False,
                  on_sulfonylurea=False)
    a = dict(common, patient_id="A", persona="A", name="Rajesh Iyer", age=54, sex="M", bmi=29.4, waist_cm=101,
             city="Mumbai", has_t2d=True, has_prediabetes=False, hba1c=8.1, fasting_glucose=158, ldl=128, hdl=38,
             triglycerides=210, egfr=82, sbp_clinic=134, dbp_clinic=84, t2d_dx_year=2017, prediabetes_dx_year=2014,
             has_htn=True, htn_dx_year=2019, has_osa_true=False, dyslipidemia_dx_year=2018, on_metformin=True,
             on_ace_inhibitor=False, on_beta_blocker=True, tcf7l2_risk_alleles=2, mtnr1b_risk_allele=1, prs_t2d=1.6)
    b = dict(common, patient_id="B", persona="B", name="Sunita Kulkarni", age=41, sex="F", bmi=32.0, waist_cm=98,
             city="Pune", has_t2d=False, has_prediabetes=True, hba1c=6.1, fasting_glucose=112, ldl=118, hdl=46,
             triglycerides=165, egfr=101, sbp_clinic=138, dbp_clinic=87, t2d_dx_year=np.nan,
             prediabetes_dx_year=2024, has_htn=False, htn_dx_year=np.nan, has_osa_true=True,
             dyslipidemia_dx_year=np.nan, on_metformin=False, on_ace_inhibitor=False, on_beta_blocker=False,
             tcf7l2_risk_alleles=1, mtnr1b_risk_allele=1, prs_t2d=0.4)
    c = dict(common, patient_id="C", persona="C", name="Arjun Menon", age=27, sex="M", bmi=21.8, waist_cm=78,
             city="Bengaluru", has_t2d=False, has_prediabetes=False, hba1c=5.1, fasting_glucose=86, ldl=92, hdl=64,
             triglycerides=70, egfr=118, sbp_clinic=114, dbp_clinic=70, t2d_dx_year=np.nan,
             prediabetes_dx_year=np.nan, has_htn=False, htn_dx_year=np.nan, has_osa_true=False,
             dyslipidemia_dx_year=np.nan, on_metformin=False, on_ace_inhibitor=False, on_beta_blocker=False,
             tcf7l2_risk_alleles=0, mtnr1b_risk_allele=0, prs_t2d=-1.1)
    return pd.DataFrame([a, b, c])


def _add_prior_labs(df: pd.DataFrame, rng) -> pd.DataFrame:
    n = len(df)
    df["labs_date"] = str(START_DATE - pd.Timedelta(days=12))[:10]
    df["labs_prior_date"] = str(START_DATE - pd.Timedelta(days=12 + 180))[:10]
    df["hba1c_prior"] = np.round(np.clip(df.hba1c + rng.normal(-0.1, 0.3, n), 4.3, 13), 1)
    df["fasting_glucose_prior"] = np.round(np.clip(df.fasting_glucose * rng.normal(0.98, 0.06, n), 70, 330))
    df["ldl_prior"] = np.round(np.clip(df.ldl * rng.normal(1.02, 0.07, n), 35, 250))
    df["hdl_prior"] = np.round(np.clip(df.hdl * rng.normal(1, 0.05, n), 22, 105))
    df["triglycerides_prior"] = np.round(np.clip(df.triglycerides * rng.normal(1, 0.1, n), 35, 600))
    df["egfr_prior"] = np.round(np.clip(df.egfr * rng.normal(1.01, 0.03, n), 15, 135))
    df["sbp_clinic_prior"] = np.round(df.sbp_clinic + rng.normal(0, 6, n))
    df["dbp_clinic_prior"] = np.round(df.dbp_clinic + rng.normal(0, 4, n))
    for c in ("has_t2d", "has_prediabetes", "has_htn", "has_osa", "has_osa_true", "osa_diagnosed",
              "on_metformin", "on_sglt2i", "on_sulfonylurea", "on_ace_inhibitor", "on_beta_blocker"):
        df[c] = df[c].astype(bool)
    for c in ("tcf7l2_risk_alleles", "mtnr1b_risk_allele"):
        df[c] = df[c].astype(int)
    return df
