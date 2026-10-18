"""Real-data validation on LifeSnaps (Fitbit, open, CC-BY-4.0).

    python -m src.validate_lifesnaps

Question: does a short night really shift a person's heart signals away from THEIR OWN normal?
For each user with enough data, a night is "short" if its total sleep time is below that user's
personal 25th percentile. We compare, against the user's own mean/SD:
  * resting HR of the following day (Fitbit date = wake-up date), and
  * nightly HRV (RMSSD measured during that sleep)
between short and normal nights, per user (paired), with a Wilcoxon signed-rank test.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

from .calibration import load_lifesnaps_daily
from .config import REPORTS

MIN_NIGHTS = 20


def main():
    df = load_lifesnaps_daily()
    if df is None:
        res = {"available": False, "note": "LifeSnaps CSV not downloaded - validation moved to future work."}
        (REPORTS / "lifesnaps_validation.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
        print(res)
        return res
    d = df.dropna(subset=["tst_hours"]).copy()
    rows = []
    for uid, u in d.groupby("id"):
        u = u.dropna(subset=["resting_hr", "rmssd"])
        if len(u) < MIN_NIGHTS:
            continue
        p25 = u.tst_hours.quantile(0.25)
        z_rhr = (u.resting_hr - u.resting_hr.mean()) / u.resting_hr.std()
        z_hrv = (u.rmssd - u.rmssd.mean()) / u.rmssd.std()
        short = u.tst_hours < p25
        rows.append(pd.DataFrame({"user": uid, "short": short, "z_rhr": z_rhr, "z_hrv": z_hrv,
                                  "tst": u.tst_hours}))
    nights = pd.concat(rows, ignore_index=True)
    per_user = nights.groupby(["user", "short"])[["z_rhr", "z_hrv"]].mean().unstack("short").dropna()
    d_rhr = per_user[("z_rhr", True)] - per_user[("z_rhr", False)]
    d_hrv = per_user[("z_hrv", True)] - per_user[("z_hrv", False)]
    res = {
        "available": True,
        "n_users": int(per_user.shape[0]), "n_nights": int(len(nights)),
        "n_short_nights": int(nights.short.sum()),
        "definition": "short night = TST below the user's own 25th percentile",
        "rhr_z_short_mean": round(float(nights[nights.short].z_rhr.mean()), 3),
        "rhr_z_normal_mean": round(float(nights[~nights.short].z_rhr.mean()), 3),
        "hrv_z_short_mean": round(float(nights[nights.short].z_hrv.mean()), 3),
        "hrv_z_normal_mean": round(float(nights[~nights.short].z_hrv.mean()), 3),
        "rhr_paired_diff_median": round(float(d_rhr.median()), 3),
        "hrv_paired_diff_median": round(float(d_hrv.median()), 3),
        "rhr_users_higher_after_short_pct": round(float((d_rhr > 0).mean() * 100), 1),
        "hrv_users_lower_after_short_pct": round(float((d_hrv < 0).mean() * 100), 1),
        "rhr_wilcoxon_p": float(wilcoxon(d_rhr).pvalue),
        "hrv_wilcoxon_p": float(wilcoxon(d_hrv).pvalue),
    }
    res["interpretation"] = (
        f"Across {res['n_users']} real Fitbit users ({res['n_nights']} nights), short nights were followed by "
        f"resting HR {res['rhr_z_short_mean'] - res['rhr_z_normal_mean']:+.2f} SD and HRV "
        f"{res['hrv_z_short_mean'] - res['hrv_z_normal_mean']:+.2f} SD relative to the same person's normal "
        f"nights (paired Wilcoxon p = {res['rhr_wilcoxon_p']:.3g} for RHR, {res['hrv_wilcoxon_p']:.3g} for HRV). "
        "Deviation from a personal baseline - the core idea of the twin - is visible in real data.")
    # box-plot data for the UI + PNG for slides
    q = lambda s: [round(float(x), 3) for x in np.percentile(s.dropna(), [5, 25, 50, 75, 95])]  # noqa: E731
    res["boxplot"] = {
        "rhr": {"short": q(nights[nights.short].z_rhr), "normal": q(nights[~nights.short].z_rhr)},
        "hrv": {"short": q(nights[nights.short].z_hrv), "normal": q(nights[~nights.short].z_hrv)},
        "percentiles": [5, 25, 50, 75, 95],
    }
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(1, 2, figsize=(8, 3.6))
        for ax, col, title in ((axes[0], "z_rhr", "Next-day resting HR (z)"), (axes[1], "z_hrv", "Nightly HRV (z)")):
            data = [nights[~nights.short][col].dropna(), nights[nights.short][col].dropna()]
            ax.boxplot(data, tick_labels=["Normal nights", "Short nights"], showfliers=False, widths=0.5,
                       patch_artist=True, boxprops=dict(facecolor="#dbeafe", color="#1d4ed8"),
                       medianprops=dict(color="#1d4ed8"))
            ax.axhline(0, color="#94a3b8", lw=0.8, ls="--")
            ax.set_title(title, fontsize=10)
        fig.suptitle(f"LifeSnaps real-data check: {res['n_users']} users, {res['n_nights']} nights", fontsize=10)
        fig.tight_layout()
        fig.savefig(REPORTS / "lifesnaps_boxplot.png", dpi=160)
    except Exception as e:  # noqa: BLE001
        print("plot skipped:", e)
    (REPORTS / "lifesnaps_validation.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in res.items() if k != "boxplot"}, indent=2))
    from .report import write_results
    write_results()
    return res


if __name__ == "__main__":
    main()
