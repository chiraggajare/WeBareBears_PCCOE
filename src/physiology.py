"""Physiology: sleep -> insulin sensitivity -> Bergman minimal model CGM, plus morning BP rule.

Sleep -> insulin sensitivity (plan 6.3)
    debt_t = sum_{k=0..6} max(0, TST_base - TST_{t-k}) * 0.75^k                    (hours)
    SI_t   = SI_0 * exp(-a1*debt_t - a2*|bedtime_shift_t|*(1 + g*mtnr1b) - a3*waso_t/60)
                  * (1 + b1*dSteps_{t-1} + b2*on_metformin) * LogNormal(0, sigma)
    SI_0   = f(bmi, hba1c, age, prs_t2d, tcf7l2_risk_alleles)

    a1 is chosen so that 4 nights of ~5 h (vs a 7.5 h personal baseline) lower SI by ~25%,
    the middle of the 20-30% range reported for experimental sleep restriction:
      * Spiegel K, Leproult R, Van Cauter E. Lancet 1999;354:1435-9   (6 nights x 4 h)
      * Buxton OM et al. Diabetes 2010;59:2126-33                      (~20% lower SI, 1 week x 5 h)
      * Donga E et al. JCEM 2010;95:2963-8                             (1 night x 4 h -> ~19-25% lower)
    The MTNR1B x late-timing interaction (g) is kept small, after Garaulet M et al.
    Cell Metab 2020 / Lopez-Minguez J et al. 2018 (late eating impairs glucose tolerance
    more in rs10830963-G carriers).

Glucose (plan 6.4) - Bergman minimal model (Bergman RN et al. Am J Physiol 1979;236:E667;
Bergman RN et al. J Clin Invest 1981;68:1456):
    dG/dt = -(p1 + X)*G + p1*Gb + Ra(t)/V
    dX/dt = -p2*X + p3*(I - Ib)               SI = p3/p2  -> p3 scaled by SI_t
    I(t)  = Ib + beta*max(0, G - Gb)           lower beta for T2D / high HbA1c / TCF7L2 risk alleles
    Ra(t) = 3 meals/day, gamma(k=2) absorption, carbs ~ N(60, 15) g, jittered meal times
    CGM   = G + N(0, 5), sampled every 5 min
    Integrated with fixed-step Euler (1 min), vectorised across patients.

Morning BP (plan 6.5) - transparent rule + noise:
    sbp_morning = sbp_clinic + c1*ODI + c2*debt + c3*waso/60 - c4*on_ace_inhibitor + N(0, 6)
"""
from __future__ import annotations

import numpy as np

# ---- sleep -> SI coefficients
DECAY = 0.75
A1 = 0.042          # per hour of weighted debt  -> 5h x 4 nights vs 7.5h base ~ 25% drop
A2 = 0.060          # per hour of bedtime shift
G_MTNR1B = 0.30     # extra timing penalty for MTNR1B risk carriers
A3 = 0.050          # per hour of WASO
B1 = 0.020          # per 1000 steps above personal mean (previous day), clipped +-5k
B2 = 0.10           # metformin insulin-sensitising effect
SIGMA = 0.30        # day-to-day unmodelled variation: meal composition, stress, illness (log-normal)

# ---- Bergman parameters (per minute)
P1 = 0.005          # glucose effectiveness SG (1/min)
P2 = 0.025          # remote-insulin decay (1/min)
SI_REF = 6.0e-4     # healthy reference SI (1/min per uU/mL)
IB = 10.0           # basal insulin (uU/mL)
BETA_REF = 2.0      # healthy beta-cell response (uU/mL per mg/dL above basal)
F_ABS = 0.9         # carbohydrate bioavailability
TAU_MEAL = 60.0     # gamma(k=2) absorption time constant (min)
V_PER_KG = 1.88     # glucose distribution volume (dL/kg, Dalla Man et al. 2007)
CGM_NOISE = 5.0

# ---- BP rule
C1, C2, C3, C4, BP_NOISE = 0.55, 1.1, 3.0, 6.0, 6.0
HOME_CLINIC_SD = 7.0  # per-patient home-vs-clinic difference (white-coat / masked effect)


def si0(bmi, hba1c, age, prs, tcf7l2):
    """Baseline insulin sensitivity from EHR + genetics (mild genetic effects)."""
    bmi, hba1c, age, prs, tcf7l2 = map(np.asarray, (bmi, hba1c, age, prs, tcf7l2))
    return SI_REF * np.exp(-0.035 * (bmi - 24) - 0.14 * (hba1c - 5.3) - 0.004 * (age - 35)
                           - 0.04 * prs - 0.03 * tcf7l2)


def beta_cell(hba1c, tcf7l2, has_t2d, on_sulfonylurea=False):
    """Simple beta-cell responsivity; TCF7L2 risk alleles impair insulin secretion."""
    hba1c, tcf7l2 = np.asarray(hba1c, float), np.asarray(tcf7l2, float)
    b = BETA_REF * np.exp(-0.10 * (hba1c - 5.3)) * (1 - 0.05 * tcf7l2)
    b = b * np.where(np.asarray(has_t2d), 0.85, 1.0) * np.where(np.asarray(on_sulfonylurea), 1.25, 1.0)
    return b


def weight_kg(bmi, sex):
    h = np.where(np.asarray(sex) == "F", 1.57, 1.70)
    return np.asarray(bmi) * h ** 2


def sleep_debt(tst: np.ndarray, tst_base) -> np.ndarray:
    """Weighted 7-night sleep debt. tst shape (..., n_nights); returns same shape."""
    tst = np.asarray(tst, float)
    deficit = np.maximum(0.0, np.asarray(tst_base, float)[..., None] - tst)
    debt = np.zeros_like(deficit)
    for k in range(7):
        shifted = np.zeros_like(deficit)
        if k == 0:
            shifted = deficit
        else:
            shifted[..., k:] = deficit[..., :-k]
        debt += shifted * DECAY ** k
    return debt


def si_series(si_0, debt, bedtime_shift, waso_min, mtnr1b, dsteps_prev_k, on_metformin, noise=None):
    """Daily insulin sensitivity. All per-day arrays shaped (n_patients, n_days)."""
    si_0 = np.asarray(si_0)[:, None]
    mt = np.asarray(mtnr1b, float)[:, None]
    met = np.asarray(on_metformin, float)[:, None]
    sleep_term = np.exp(-A1 * debt - A2 * np.abs(bedtime_shift) * (1 + G_MTNR1B * mt) - A3 * waso_min / 60)
    act = 1 + B1 * np.clip(dsteps_prev_k, -5, 5) + B2 * met
    out = si_0 * sleep_term * act
    if noise is not None:
        out = out * noise
    return out


def meal_ra(minutes: np.ndarray, meal_times: np.ndarray, carbs_g: np.ndarray) -> np.ndarray:
    """Rate of appearance (mg/min). meal_times/carbs shaped (n_patients, n_meals); minutes 1-D."""
    t = minutes[None, None, :] - meal_times[:, :, None]
    t = np.where(t > 0, t, 0.0)
    ra = F_ABS * carbs_g[:, :, None] * 1000 * t / TAU_MEAL ** 2 * np.exp(-t / TAU_MEAL)
    return ra.sum(axis=1)


def simulate_glucose(gb, si_per_minute_fn, beta, v_dl, meal_times, carbs, n_minutes, g0=None, x0=None,
                     chunk=1440):
    """Euler-integrate the Bergman minimal model for all patients.

    gb, beta, v_dl : (n,) arrays.  si_per_minute_fn(minute_index) -> (n,) SI for that minute.
    meal_times, carbs : (n, n_meals) absolute minutes / grams.
    Returns G (n, n_minutes) plus final state.
    """
    n = len(gb)
    G = np.empty((n, n_minutes), dtype=np.float32)
    g = np.array(gb, float) if g0 is None else np.array(g0, float)
    x = np.zeros(n) if x0 is None else np.array(x0, float)
    for start in range(0, n_minutes, chunk):
        mins = np.arange(start, min(n_minutes, start + chunk), dtype=float)
        # only meals that can contribute to this chunk (absorption tail ~ 12 h is plenty)
        cols = np.where((meal_times.max(axis=0) >= start - 720) & (meal_times.min(axis=0) < mins[-1] + 1))[0]
        ra = meal_ra(mins, meal_times[:, cols], carbs[:, cols]) / v_dl[:, None]
        si_cur = None
        for j, m in enumerate(mins.astype(int)):
            if si_cur is None or m % 60 == 0:
                si_cur = si_per_minute_fn(m)
            p3 = si_cur * P2
            ins = IB + beta * np.maximum(0.0, g - gb)
            dg = -(P1 + x) * g + P1 * gb + ra[:, j]
            dx = -P2 * x + p3 * (ins - IB)
            g = np.maximum(g + dg, 30.0)
            x = x + dx
            G[:, m] = g
    return G, g, x


def morning_sbp(sbp_clinic, odi, debt, waso_min, on_ace, noise):
    return (np.asarray(sbp_clinic)[:, None] + C1 * odi + C2 * debt + C3 * waso_min / 60
            - C4 * np.asarray(on_ace, float)[:, None] + noise)


def deterministic_day_curve(gb, si, beta, v_dl, meal_minutes, carbs, warmup_g=None):
    """Noise-free 24 h glucose curve (288 x 5-min) for one patient & one SI value (What-If)."""
    gb_a = np.atleast_1d(np.asarray(gb, float))
    si_a = np.atleast_1d(np.asarray(si, float))
    mt = np.atleast_2d(np.asarray(meal_minutes, float))
    cb = np.atleast_2d(np.asarray(carbs, float))
    G, _, _ = simulate_glucose(gb_a, lambda m: si_a, np.atleast_1d(beta), np.atleast_1d(v_dl), mt, cb, 1440,
                               g0=warmup_g)
    return G[:, ::5]
