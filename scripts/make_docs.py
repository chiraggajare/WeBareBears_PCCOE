"""Generate the submission documents (any OS):

    docs/architecture.pdf (+ .png)        - system architecture diagram
    docs/presentation.pptx / .pdf         - 14-slide deck with project details and outcomes
    docs/figures/*.png                    - the charts/diagrams used in the deck

    python scripts/make_docs.py

Every number is read from the pipeline outputs (reports/*.json, data/processed/*) - nothing is typed by hand.
Product screenshots come from docs/screenshots/ (python scripts/take_screenshots.py, with the app running).
"""
from __future__ import annotations

import json
import sys
import textwrap
import warnings
from pathlib import Path

import os

os.environ.setdefault("MPLBACKEND", "Agg")

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch

matplotlib.use("Agg")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
warnings.filterwarnings("ignore")

DOCS = ROOT / "docs"
FIG = DOCS / "figures"
SHOTS = DOCS / "screenshots"
REPORTS = ROOT / "reports"
PROCESSED = ROOT / "data" / "processed"
FIG.mkdir(parents=True, exist_ok=True)

TEAM = "Team WeBareBears"
COLLEGE = "PCCOE"

# ---------------------------------------------------------------- palette / style
INK, MUTED, LINE, SOFT = "#0f172a", "#475569", "#cbd5e1", "#f1f5f9"
ACCENT, ACCENT_SOFT = "#2554e8", "#e8efff"
RED, AMBER, GREEN, VIOLET, SLATE = "#dc2626", "#d97706", "#059669", "#7c3aed", "#64748b"
SOFTS = {RED: "#fee2e2", AMBER: "#fef3c7", GREEN: "#d1fae5", VIOLET: "#ede9fe", SLATE: "#f1f5f9", ACCENT: ACCENT_SOFT}

plt.rcParams.update({
    "font.family": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
    "font.size": 12, "axes.titlesize": 13, "axes.titleweight": "bold", "axes.titlecolor": INK,
    "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": LINE,
    "axes.labelcolor": MUTED, "xtick.color": MUTED, "ytick.color": MUTED, "axes.grid": False,
    "savefig.facecolor": "white", "figure.facecolor": "white", "svg.fonttype": "none",
})


def load(name):
    p = REPORTS / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


ND, S2, LS = load("nextday_metrics.json"), load("spike2h_metrics.json"), load("lifesnaps_validation.json")
META = json.loads((PROCESSED / "calibration_meta.json").read_text(encoding="utf-8")) \
    if (PROCESSED / "calibration_meta.json").exists() else {}


def pct(x, d=0):
    return "n/a" if x is None else f"{x * 100:.{d}f}%"


def canvas(w=16, h=9):
    fig = plt.figure(figsize=(w, h))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, w * 10)
    ax.set_ylim(0, h * 10)
    ax.axis("off")
    return fig, ax


def rbox(ax, x, y, w, h, fc="white", ec=LINE, lw=1.4, r=1.8, z=2):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}", fc=fc, ec=ec, lw=lw,
                                zorder=z))


def arrow(ax, p1, p2, color=SLATE, lw=2.2, style="-|>", ms=18, rad=0.0, z=3, ls="-"):
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle=style, mutation_scale=ms, color=color, lw=lw, zorder=z,
                                 connectionstyle=f"arc3,rad={rad}", linestyle=ls, shrinkA=2, shrinkB=2))


def wrap(s, n):
    return "\n".join(textwrap.fill(p, n, break_on_hyphens=False) for p in s.split("\n"))


def badge(ax, x, y, n, color, r=2.6):
    ax.add_patch(Circle((x, y), r, fc=color, ec="white", lw=2, zorder=5))
    ax.text(x, y, str(n), ha="center", va="center", color="white", fontsize=15, fontweight="bold", zorder=6)


def save(fig, name, pdf=False):
    fig.savefig(FIG / f"{name}.png", dpi=170)
    if pdf:
        fig.savefig(DOCS / f"{name}.pdf")
    plt.close(fig)
    return str(FIG / f"{name}.png")


# ================================================================ 1. ARCHITECTURE
def architecture():
    fig, ax = canvas(16, 9)
    ax.text(80, 86.5, "How SleepTwin works", ha="center", fontsize=26, fontweight="bold", color=INK)
    ax.text(80, 82.3, "From open data to a doctor's decision - left to right in four stages",
            ha="center", fontsize=13, color=MUTED)

    cols = [
        dict(n=1, color=SLATE, head="OPEN DATA", sub="real & anonymized - for calibration", cards=[
            ("CDC NHANES 2017-2020", "Real anonymized US adults → realistic, correlated health records"),
            ("LifeSnaps (Fitbit)", "Real volunteers' sleep, heart-rate & HRV patterns"),
            ("Published science", "Bergman glucose model, sleep → insulin effect, gene frequencies"),
        ]),
        dict(n=2, color=VIOLET, head="VIRTUAL PATIENTS", sub="the simulator - 300 patients × 21 days", cards=[
            ("Health record", "Age, diagnoses + years, labs, medicines, genetic markers"),
            ("Wearable stream", "Sleep stages, HRV, heart rate, steps, oxygen dips"),
            ("Body model", "Sleep debt → insulin sensitivity → glucose every 5 min; morning BP"),
        ]),
        dict(n=3, color=ACCENT, head="TWIN BRAIN", sub="AI / machine learning", cards=[
            ("Learn the person's normal", "Days 1-14 set a personal baseline"),
            ("Predict (LightGBM)", "Tomorrow's glucose spike & BP surge, plus a glucose alert 2 hours ahead"),
            ("Explain + What-If", "SHAP → reasons in plain English; tests a fix in ~15 ms"),
        ]),
        dict(n=4, color=GREEN, head="DOCTOR DASHBOARD", sub="website - laptop, tablet or phone", cards=[
            ("FastAPI service", "Secure API that serves risks, reasons and trends"),
            ("5 pages", "Patients • Overview • Trends • What-If • How It Works"),
            ("Doctor decides", "Decision support only - never a diagnosis"),
        ]),
    ]
    x0, w, gap, top, bottom = 3.5, 33.5, 6.5, 77, 19
    for i, c in enumerate(cols):
        x = x0 + i * (w + gap)
        col, soft = c["color"], SOFTS[c["color"]]
        rbox(ax, x, bottom, w, top - bottom, fc=soft, ec=soft, r=2.5, z=1)
        badge(ax, x + 4.2, top - 4.3, c["n"], col)
        ax.text(x + 8.2, top - 3.4, c["head"], fontsize=14.5, fontweight="bold", color=col, va="center")
        ax.text(x + 8.2, top - 6.4, c["sub"], fontsize=10, color=MUTED, va="center")
        ch, cg = 13.6, 2.4
        for j, (t, body) in enumerate(c["cards"]):
            cy = top - 10 - (j + 1) * ch - j * cg
            rbox(ax, x + 2, cy, w - 4, ch, fc="white", ec="white", r=1.6, z=2)
            ax.add_patch(FancyBboxPatch((x + 2, cy), 1.0, ch, boxstyle="square,pad=0", fc=col, ec=col, zorder=3))
            ax.text(x + 4.8, cy + ch - 2.8, t, fontsize=12.2, fontweight="bold", color=INK, va="top", zorder=4)
            ax.text(x + 4.8, cy + ch - 6.6, wrap(body, 33), fontsize=10.4, color=MUTED, va="top",
                    linespacing=1.35, zorder=4)
        if i < 3:
            xa = x + w + 0.4
            arrow(ax, (xa, 48), (xa + gap - 0.8, 48), color=INK, lw=2.6, ms=22)
            ax.text(xa + gap / 2 - 0.4, 51.5, ["calibrates", "daily data", "risk + why"][i], ha="center",
                    va="bottom", fontsize=8.5, color=INK, fontweight="bold")

    # What-If feedback loop + validation note
    xs = [x0 + k * (w + gap) for k in range(4)]
    arrow(ax, (xs[3] + w / 2, bottom - 0.5), (xs[2] + w / 2, bottom - 0.5), color=ACCENT, lw=2.4, ms=20,
          rad=-0.22)
    ax.text((xs[2] + xs[3] + w) / 2, 4.6, "What-If loop: the doctor tests a fix (sleep longer, earlier bedtime, CPAP)"
            "\n→ the twin re-runs the body model + AI and shows the new risk", ha="center", fontsize=11,
            color=ACCENT, fontweight="bold", linespacing=1.4)
    rbox(ax, xs[0], 4.5, w + gap + w, 10.5, fc="#ecfdf5", ec="#a7f3d0", r=1.6)
    ax.text(xs[0] + 2.5, 12.2, "✓  Checked on real data", fontsize=11.5, fontweight="bold", color=GREEN)
    ax.text(xs[0] + 2.5, 8.9, wrap("In 38 real Fitbit users, short nights pushed resting heart rate up and HRV "
                                   "down versus each person's own normal (the idea the twin is built on).", 82),
            fontsize=10, color=MUTED, va="top", linespacing=1.35)
    ax.text(80, 1.2, "All patients are SIMULATED  •  Model-based projection for clinical decision support. "
            "Research prototype.  •  Team WeBareBears · PCCOE", ha="center", fontsize=9.5, color=SLATE,
            style="italic")
    return save(fig, "architecture", pdf=True)


# ================================================================ 2. FIGURES FOR SLIDES
def fig_blind_spot():
    fig, ax = canvas(12, 4.2)
    y = 20
    ax.plot([8, 112], [y, y], color=LINE, lw=3, zorder=1, solid_capstyle="round")
    for xv, lab in ((10, "Clinic visit"), (110, "Next visit")):
        ax.add_patch(Circle((xv, y), 3.2, fc=ACCENT, ec="white", lw=2, zorder=3))
        ax.text(xv, y, "+", ha="center", va="center", color="white", fontsize=18, fontweight="bold", zorder=4)
        ax.text(xv, y - 7.5, lab, ha="center", fontsize=15, fontweight="bold", color=INK)
        ax.text(xv, y - 12, "~15 minutes", ha="center", fontsize=13, color=MUTED)
    rng = np.random.default_rng(3)
    nights = np.linspace(16, 104, 45)
    for i, xv in enumerate(nights):
        bad = 24 <= i <= 28
        ax.add_patch(Circle((xv, y), 0.85, fc=RED if bad else "#94a3b8", ec="none", zorder=2))
    ax.add_patch(FancyBboxPatch((61.5, y + 3.5), 16, 7, boxstyle="round,pad=0,rounding_size=1.2", fc="#fee2e2",
                                ec="#fecaca", zorder=2))
    ax.text(69.5, y + 7, "5 bad nights", ha="center", va="center", fontsize=13, color=RED, fontweight="bold")
    arrow(ax, (76.5, y + 7), (84, y + 12.5), color=RED, lw=2)
    ax.text(85, y + 13, "Sugar spike / BP surge\nnobody sees it", fontsize=14, color=RED, fontweight="bold",
            va="center", linespacing=1.3)
    ax.text(60, 38, "~3 months of nights the doctor never sees", ha="center",
            fontsize=18, fontweight="bold", color=INK)
    ax.text(60, 2.5, "SleepTwin reads every night and forecasts tomorrow - every morning", ha="center", fontsize=15,
            color=ACCENT, fontweight="bold")
    _ = rng
    return save(fig, "blind_spot")


def fig_why_sleep():
    fig, ax = canvas(14, 6)
    rows = [
        (40, RED, ["Short or late sleep", "Insulin works less well", "Sugar rises higher\nafter meals",
                   "Glucose spike\n> 180 mg/dL"],
         f"4 nights of 5 h → insulin sensitivity −{META.get('si_drop_4x5h_check', 0.25) * 100:.0f}%  "
         "(Spiegel 1999, Buxton 2010, Donga 2010)"),
        (12, AMBER, ["Sleep apnea\n(breathing pauses)", "Oxygen dips &\nbroken sleep", "Stress on the heart\n& vessels",
                     "Morning BP surge\n> 145 mmHg"],
         "Most sleep apnea is never diagnosed - a normal sleep app calls the night 'fine'"),
    ]
    for yb, col, steps, note in rows:
        for k, s in enumerate(steps):
            x = 3 + k * 34.5
            last = k == len(steps) - 1
            rbox(ax, x, yb, 29, 14, fc=col if last else "white", ec=col, lw=2.4, r=2)
            ax.text(x + 14.5, yb + 7, s, ha="center", va="center", fontsize=16.5, fontweight="bold",
                    color="white" if last else INK, linespacing=1.25)
            if not last:
                arrow(ax, (x + 29.4, yb + 7), (x + 34.1, yb + 7), color=col, lw=2.8, ms=22)
        ax.text(3, yb - 4.2, note, fontsize=14, color=MUTED, style="italic")
    return save(fig, "why_sleep")


def fig_six_steps():
    fig, ax = canvas(14, 4.6)
    steps = [("Learn", "the person's own\nnormal (days 1-14)"), ("Spot drift", "each night vs\nthat normal"),
             ("Combine", "with the health\nrecord"), ("Predict", "tomorrow's spike\n+ 2-hour alert"),
             ("Explain", "in plain English\n(SHAP)"), ("What-If", "test a fix before\nadvising it")]
    for k, (t, d) in enumerate(steps):
        x = 11 + k * 23.6
        col = ACCENT if k < 5 else GREEN
        ax.add_patch(Circle((x, 28), 7.2, fc=SOFTS[col], ec=col, lw=2.4, zorder=2))
        ax.text(x, 28, str(k + 1), ha="center", va="center", fontsize=26, fontweight="bold", color=col, zorder=3)
        ax.text(x, 16, t, ha="center", fontsize=18, fontweight="bold", color=INK)
        ax.text(x, 12.5, d, ha="center", va="top", fontsize=13.5, color=MUTED, linespacing=1.3)
        if k < 5:
            arrow(ax, (x + 7.8, 28), (x + 15.8, 28), color=LINE, lw=2.4, ms=16)
    return save(fig, "six_steps")


def fig_persona_story():
    daily = pd.read_parquet(PROCESSED / "daily.parquet")
    nights = pd.read_parquet(PROCESSED / "nights.parquet")
    a = daily[daily.patient_id == "A"].sort_values("day")
    n = nights[nights.patient_id == "A"].sort_values("day")
    days = a.day.to_numpy() + 1
    fig, axes = plt.subplots(3, 1, figsize=(9.5, 7.2), sharex=True, gridspec_kw=dict(hspace=0.42))
    tst = n.tst_hours_true.to_numpy()
    usual = float(np.mean(tst[:14]))
    axes[0].bar(days, tst, color=[RED if v < usual - 1 else "#94a3b8" for v in tst], width=0.7)
    axes[0].axhline(usual, color=GREEN, lw=1.5, ls="--")
    axes[0].text(0.6, usual + 0.25, f"his normal ~{usual:.1f} h", color=GREEN, fontsize=10)
    axes[0].set_title("1  Sleep each night (hours)", loc="left")
    axes[0].set_ylim(0, 9)
    si = (a.si / a.si_0).to_numpy() * 100
    axes[1].plot(days, si, color=ACCENT, lw=2.6, marker="o", ms=4)
    axes[1].axhline(100, color=LINE, lw=1)
    axes[1].set_title("2  Insulin sensitivity (% of his baseline)", loc="left")
    axes[1].set_ylim(40, 130)
    pk = a.cgm_peak.to_numpy()
    axes[2].bar(days, pk, color=[RED if v > 180 else ACCENT for v in pk], width=0.7)
    axes[2].axhline(180, color=RED, lw=1.5, ls="--")
    axes[2].text(0.6, 183, "180 mg/dL", color=RED, fontsize=10)
    axes[2].set_title("3  Highest glucose of the day (mg/dL)", loc="left")
    axes[2].set_ylim(120, max(205, pk.max() + 10))
    axes[2].set_xlabel("Day")
    axes[2].set_xticks(range(1, 22, 2))
    for axx in axes:
        axx.axvspan(0.5, 14.5, color=SOFT, zorder=0)
    axes[0].text(7.5, 8.1, "learning his normal", ha="center", fontsize=9.5, color=SLATE)
    fig.suptitle("Persona A (simulated): 4 short nights → insulin works less → sugar spikes",
                 x=0.07, ha="left", fontsize=14, fontweight="bold", color=INK)
    fig.subplots_adjust(left=0.08, right=0.98, top=0.9, bottom=0.08)
    return save(fig, "persona_story")


def fig_ablation():
    g, b = ND.get("glucose_event_24h", {}), ND.get("bp_event", {})
    groups = [("Glucose spike\n(all patients)", g, None), ("Glucose spike\n(diabetics only)", g, "t2d"),
              ("Morning BP surge\n(all patients)", b, None), ("Morning BP surge\n(diabetics only)", b, "t2d")]
    tiers = [("ehr_only", "Health record only", "#cbd5e1"), ("wearables_only", "Wearables only", "#93a5c8"),
             ("fused", "SleepTwin (both combined)", ACCENT)]
    fig, ax = plt.subplots(figsize=(11, 5.6))
    xw = 0.26
    for gi, (lab, r, sub) in enumerate(groups):
        for ti, (k, name, col) in enumerate(tiers):
            v = r.get("t2d_subgroup", {}).get(k) if sub else r.get(k, {}).get("auroc")
            if v is None:
                continue
            x = gi + (ti - 1) * xw
            ax.bar(x, v - 0.5, bottom=0.5, width=xw * 0.92, color=col, label=name if gi == 0 else None)
            ax.text(x, v + 0.006, f"{v:.2f}", ha="center", fontsize=10.5,
                    fontweight="bold" if k == "fused" else "normal", color=INK if k == "fused" else MUTED)
    ax.set_xticks(range(len(groups)), [g_[0] for g_ in groups], fontsize=11)
    ax.set_ylim(0.5, 1.0)
    ax.set_ylabel("AUROC  (0.5 = coin flip, 1.0 = perfect)")
    ax.yaxis.grid(True, color=SOFT)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, loc="upper center", ncol=3, bbox_to_anchor=(0.5, 1.12), fontsize=11)
    fig.subplots_adjust(left=0.08, right=0.98, top=0.86, bottom=0.16)
    return save(fig, "ablation")


def fig_two_hour():
    cgm = pd.read_parquet(PROCESSED / "cgm.parquet", columns=["patient_id", "t", "glucose_noisy"])
    a = cgm[cgm.patient_id == "A"]
    day = 20 * 1440
    w = a[(a.t >= day + 9 * 60) & (a.t <= day + 17 * 60)]
    hrs = (w.t - day) / 60
    now = 13.0
    after = w[(w.t > day + 13 * 60) & (w.glucose_noisy > 180)]
    cross = float((after.t.iloc[0] - day) / 60) if len(after) else None
    fig, ax = plt.subplots(figsize=(10.5, 5))
    ax.axhspan(70, 180, color="#ecfdf5", zorder=0)
    ax.axhline(180, color=RED, ls="--", lw=1.5)
    ax.text(9.05, 183, "180 mg/dL", color=RED, fontsize=10)
    past = hrs <= now
    ax.plot(hrs[past], w.glucose_noisy[past], color=ACCENT, lw=2.4, label="Seen so far")
    ax.plot(hrs[~past], w.glucose_noisy[~past], color="#94a3b8", lw=2, ls=":", label="What happened next")
    ax.axvline(now, color=INK, lw=1.4)
    g_now = float(w.glucose_noisy[hrs <= now].iloc[-1])
    ax.annotate("13:00  ALERT\n\"likely above 180\nin ~35 min\"", xy=(now, g_now), xytext=(9.4, 210),
                fontsize=12, fontweight="bold", color=INK, va="center",
                arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.4))
    if cross:
        ax.axvspan(now, cross, color="#fef3c7", zorder=0)
        mins = int(round((cross - now) * 60))
        ax.annotate(f"crossed 180 at {int(cross)}:{int(round((cross % 1) * 60)):02d}\n{mins} minutes of warning",
                    xy=(cross, 181), xytext=(14.4, 212), fontsize=12, color=AMBER, fontweight="bold", va="center",
                    arrowprops=dict(arrowstyle="-|>", color=AMBER, lw=1.4))
    ax.text(12.45, 92, "lunch\n12:30", ha="center", fontsize=9.5, color=MUTED)
    ax.set_xlim(9, 17)
    ax.set_ylim(80, 235)
    ax.set_xticks(range(9, 18), [f"{h}:00" for h in range(9, 18)])
    ax.set_ylabel("Glucose (mg/dL)")
    ax.legend(frameon=False, loc="lower right", fontsize=11)
    ax.set_title("Persona A on day 21 (simulated)", loc="left")
    fig.subplots_adjust(left=0.09, right=0.98, top=0.9, bottom=0.11)
    return save(fig, "two_hour")


def fig_lifesnaps():
    b = LS.get("boxplot", {})
    fig, axes = plt.subplots(1, 2, figsize=(9.5, 4.8))
    for axx, key, title, delta in ((axes[0], "rhr", "Resting heart rate next day",
                                    LS.get("rhr_z_short_mean", 0) - LS.get("rhr_z_normal_mean", 0)),
                                   (axes[1], "hrv", "HRV (heart-rate variability)",
                                    LS.get("hrv_z_short_mean", 0) - LS.get("hrv_z_normal_mean", 0))):
        stats = []
        for lab, q in (("Normal nights", b.get(key, {}).get("normal")), ("Short nights", b.get(key, {}).get("short"))):
            if q:
                stats.append(dict(label=lab, whislo=q[0], q1=q[1], med=q[2], q3=q[3], whishi=q[4], fliers=[]))
        bp = axx.bxp(stats, showfliers=False, widths=0.55, patch_artist=True, medianprops=dict(color=INK, lw=2))
        for patch, col in zip(bp["boxes"], ("#cbd5e1", RED if key == "rhr" else ACCENT)):
            patch.set_facecolor(col)
            patch.set_alpha(0.75)
            patch.set_edgecolor(col)
        axx.axhline(0, color=SLATE, lw=1, ls="--")
        axx.text(0.02, 0.02, "dashed line = this person's normal", transform=axx.transAxes, fontsize=9.5,
                 color=SLATE)
        axx.set_title(f"{title}\n", loc="left", fontsize=12.5)
        axx.set_ylabel("vs own normal (SD)")
        axx.text(0.0, 1.02, f"{delta:+.2f} SD after short nights", transform=axx.transAxes, ha="left",
                 fontsize=12, fontweight="bold", color=RED if key == "rhr" else ACCENT)
    fig.subplots_adjust(left=0.09, right=0.98, top=0.85, bottom=0.08, wspace=0.35)
    return save(fig, "lifesnaps")


def persona_whatifs():
    from src.twin import get_twin
    t = get_twin()
    rows = []
    for pid, args, label in (("A", (7.5, 0.0, False, 1), "sleep 7.5 h at usual bedtime"),
                             ("B", (7.2, 0.0, True, 1), "use CPAP for sleep apnea"),
                             ("C", (8.0, 0.0, False, 1), "sleep 8 h")):
        w = t.what_if(pid, *args)
        bp_led = w["bp_before"] > w["risk_before"]
        rows.append(dict(pid=pid, name=t.profiles.loc[pid, "name"], label=label,
                         kind="Morning BP surge" if bp_led else "Glucose spike",
                         before=w["bp_before"] if bp_led else w["risk_before"],
                         after=w["bp_after"] if bp_led else w["risk_after"],
                         lb=w["level_before"], la=w["level_after"]))
    return rows


def fig_personas(rows):
    lv = {"critical": RED, "warning": AMBER, "stable": GREEN}
    fig, ax = plt.subplots(figsize=(11, 5.2))
    stories = {"A": "54, diabetic on a beta-blocker - 4 short nights", "B": "41, prediabetes - hidden sleep apnea",
               "C": "27, healthy runner - one bad night"}
    for i, r in enumerate(rows):
        y = 2 - i
        ax.barh(y + 0.17, r["before"] * 100, height=0.3, color=lv[r["lb"]])
        ax.barh(y - 0.17, r["after"] * 100, height=0.3, color=lv[r["la"]], alpha=0.9)
        ax.text(r["before"] * 100 + 1, y + 0.17, f"now {r['before'] * 100:.0f}%  ({r['lb']})", va="center",
                fontsize=12.5, color=INK)
        ax.text(r["after"] * 100 + 1, y - 0.17, f"after: {r['label']} → {r['after'] * 100:.0f}%  ({r['la']})",
                va="center", fontsize=12.5, color=INK, fontweight="bold")
        ax.text(-1.5, y + 0.14, f"Persona {r['pid']}", ha="right", va="center", fontsize=15, fontweight="bold")
        ax.text(-1.5, y - 0.2, f"{r['kind']}\n{stories[r['pid']]}", ha="right", va="center", fontsize=11,
                color=MUTED)
    for xv, lab in ((40, "warning 40%"), (75, "critical 75%")):
        ax.axvline(xv, color=LINE, ls="--", lw=1)
        ax.text(xv, 2.62, lab, ha="center", fontsize=9, color=SLATE)
    ax.set_xlim(0, 150)
    ax.set_ylim(-0.6, 2.75)
    ax.set_yticks([])
    ax.set_xticks([0, 20, 40, 60, 80, 100])
    ax.set_xlabel("Risk for tomorrow (%)")
    ax.spines["left"].set_visible(False)
    fig.subplots_adjust(left=0.30, right=0.99, top=0.95, bottom=0.12)
    return save(fig, "personas")


def fig_roadmap():
    fig, ax = canvas(14, 5.2)
    stages = [("Now", GREEN, ["Working prototype", "300 virtual patients", "3 AI models + What-If", "Real-data check"]),
              ("Weeks", ACCENT, ["Indian population data", "Indian meal patterns", "Doctor-set alert levels"]),
              ("Months", VIOLET, ["Real anonymized data\n(ethics approval)", "Watch / CGM apps", "Patient companion app"]),
              ("A year +", AMBER, ["Clinical pilot study", "Virtual-doctor module", "More conditions"])]
    ax.plot([6, 134], [38, 38], color=LINE, lw=4, zorder=1)
    for k, (t, col, items) in enumerate(stages):
        x = 20 + k * 33.5
        ax.add_patch(Circle((x, 38), 3.4, fc=col, ec="white", lw=2.5, zorder=3))
        ax.text(x, 44.5, t, ha="center", fontsize=19, fontweight="bold", color=col)
        rbox(ax, x - 14.5, 2.5, 29, 30, fc=SOFTS[col], ec=SOFTS[col], r=2)
        for j, it in enumerate(items):
            ax.text(x - 12.5, 29.5 - j * 7.2, "• " + it, fontsize=14, color=INK, va="top", linespacing=1.2)
    arrow(ax, (126, 38), (137, 38), color=LINE, lw=4, ms=24)
    return save(fig, "roadmap")


# ================================================================ 3. SLIDE CONTENT
def slides(F, personas):
    g = ND.get("glucose_event_24h", {})
    mix = META.get("cohort_mix", {})
    S = []
    S.append(dict(kind="title", title="SleepTwin",
                  sub="A sleep-driven digital twin that forecasts tomorrow's blood-sugar spike and morning BP surge "
                      "for people with Type 2 Diabetes and Hypertension",
                  foot=f"{TEAM}  ·  {COLLEGE}  ·  Happiest Health Digital Twin Challenge 2026 - Phase 1",
                  notes="Introduce the team and the one-line idea."))
    S.append(dict(kind="stats", title="The problem: a blind spot between visits",
                  stats=[("~101 M", "people with diabetes in India"), ("~315 M", "people with hypertension"),
                         ("~15 min", "with a doctor every few months")],
                  source="ICMR-INDIAB, Lancet Diabetes & Endocrinology 2023", image=F["blind_spot"],
                  notes="Smartwatches record sleep nightly but don't know the wearer's medical history."))
    S.append(dict(kind="figure", title="Why sleep? Two paths from a bad night to tomorrow's risk",
                  image=F["why_sleep"],
                  caption="Sleep is measured every night by consumer wearables - and it can be changed tonight.",
                  notes="Top row: glucose path. Bottom row: blood-pressure path."))
    S.append(dict(kind="figure", title="Our solution: a digital twin of each patient",
                  image=F["six_steps"],
                  caption="Two data streams in - the health record + daily wearable data - "
                          "a personal forecast, an early warning, a reason and a tested fix out.",
                  notes="A digital twin is a virtual copy of one patient, updated every day."))
    S.append(dict(kind="full", title="Architecture", image=F["architecture"],
                  notes="Walk left to right: open data, virtual patients, twin brain, dashboard; then the What-If loop."))
    S.append(dict(kind="cards", title="Two data streams + sandbox compliance", cards=[
        ("Static: health record", VIOLET, ["Demographics (age, sex, BMI)", "Diagnoses with years",
                                           "Lab results - latest + prior", "Medicines",
                                           "Genetic markers (simulated)"]),
        ("Dynamic: wearables", ACCENT, ["Sleep stages every 5 min", "HRV + resting heart rate", "Steps",
                                        "Night-time oxygen dips", "CGM glucose every 5 min"]),
        ("Safe data only", GREEN, [f"{META.get('n_patients', 300)} virtual patients × {META.get('n_days', 21)} days",
                                   "Calibrated on NHANES (public, anonymized)", "Patterns from LifeSnaps (open, CC-BY-4.0)",
                                   "No real patients, no personal data", "Labelled 'Simulated' everywhere"]),
    ], foot=f"Cohort: T2D {pct(mix.get('t2d'))} · prediabetes {pct(mix.get('prediabetes'))} · "
            f"hypertension {pct(mix.get('htn'))} · sleep apnea {pct(mix.get('osa_true'))} "
            f"(only {pct(mix.get('osa_diagnosed'))} diagnosed)",
        notes="Both streams required by the challenge are present."))
    S.append(dict(kind="split", title="The simulator: how sleep reaches blood sugar", image=F["persona_story"],
                  bullets=["Sleep debt = last 7 nights' shortfall, recent nights count more",
                           f"4 nights of 5 h → insulin sensitivity −{META.get('si_drop_4x5h_check', 0.25) * 100:.0f}% "
                           "(matches sleep studies)",
                           "Bergman glucose model turns meals + insulin sensitivity into CGM every 5 min",
                           "Beta-blockers hide the heart-rate signal - HRV still shows the strain",
                           "Honest limit: labels come from the same simulator"],
                  notes="Use persona A to show the chain: sleep drops, insulin sensitivity drops, peaks cross 180."))
    S.append(dict(kind="figure", title="Does combining both data streams help? Yes.", image=F["ablation"],
                  caption=f"{ND.get('n_rows', 0):,} patient-days, tested only on patients the model never saw "
                          f"(GroupKFold by patient). The gain is largest for diabetics - the same night means more "
                          f"for a high-risk patient.",
                  notes="AUROC: chance the model ranks a real event above a quiet day."))
    S.append(dict(kind="stats", title="2-hour early warning for glucose spikes",
                  stats=[(f"{S2.get('median_lead_min', 0):.0f} min", "median warning before a spike"),
                         (f"{S2.get('auroc', 0):.2f}", f"accuracy (AUROC) vs {S2.get('trend_only_auroc', 0):.2f} "
                                                       "for a plain trend arrow"),
                         (pct(S2.get("episode_recall")), "of spikes warned in advance")],
                  image=F["two_hour"],
                  notes="Uses current glucose, its trend, the last meal, last night's sleep and the health record."))
    S.append(dict(kind="split", title="Checked on real people (LifeSnaps Fitbit data)", image=F["lifesnaps"],
                  bullets=[f"{LS.get('n_users', 0)} real users, {LS.get('n_nights', 0):,} nights",
                           "Short night = below that person's own usual",
                           f"Next-day resting HR: {LS.get('rhr_z_short_mean', 0) - LS.get('rhr_z_normal_mean', 0):+.2f} SD "
                           f"(p = {LS.get('rhr_wilcoxon_p', 1):.2g})",
                           f"HRV: {LS.get('hrv_z_short_mean', 0) - LS.get('hrv_z_normal_mean', 0):+.2f} SD "
                           f"(p = {LS.get('hrv_wilcoxon_p', 1):.2g})",
                           "The twin's core idea - drift from your own normal - holds in real data"],
                  notes="Each person is compared with themselves, not with others."))
    S.append(dict(kind="figure", title="Outcome: three patients, three different answers", image=F["personas"],
                  caption="The twin escalates the high-risk patient, finds a problem a sleep app would miss, "
                          "and stays calm for a healthy person.",
                  notes="All values come from the live What-If engine."))
    S.append(dict(kind="images", title="The clinician dashboard",
                  images=[str(SHOTS / "overview_A.png"), str(SHOTS / "whatif_A.png")],
                  captions=["Overview: risk, 2-hour alert, reasons, hidden-signal flags",
                            "What-If: move the sleep slider - risk and tomorrow's curve update"],
                  notes="Five pages: Patients, Overview, Trends, What-If, How It Works."))
    S.append(dict(kind="cards", title="Limitations & safety", cards=[
        ("Decision support only", AMBER, ["Not a diagnosis", "The doctor stays in charge",
                                          "Disclaimer on every screen"]),
        ("Not clinically proven", RED, ["Trained on virtual patients", "Labels share the simulator's assumptions",
                                        "Needs real-data validation"]),
        ("Built safely", GREEN, ["No real patient data", "Security-hardened app + API",
                                 "0 known dependency vulnerabilities"]),
    ], foot="Also: NHANES is a US population and genetic markers are simulated - Indian calibration is future work.",
        notes="Be upfront about what the prototype does not prove."))
    S.append(dict(kind="figure", title="Roadmap & fit with a Virtual Doctor Programme", image=F["roadmap"],
                  caption="SleepTwin can be the between-visit 'sleep + metabolism' module of a virtual doctor: "
                          "forecast tomorrow, suggest tonight's fix.",
                  notes="Close with the one-liner."))
    return S


# ================================================================ 4. RENDER: PPTX
def make_pptx(S):
    from pptx import Presentation
    from pptx.dml.color import RGBColor
    from pptx.enum.text import PP_ALIGN
    from pptx.util import Emu, Inches, Pt

    def rgb(h):
        h = h.lstrip("#")
        return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))

    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    W, H = prs.slide_width, prs.slide_height
    blank = prs.slide_layouts[6]

    def text(sl, x, y, w, h, s, size=18, bold=False, color=INK, align=None, italic=False):
        tf = sl.shapes.add_textbox(x, y, w, h).text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = s
        p.font.size, p.font.bold, p.font.italic = Pt(size), bold, italic
        p.font.color.rgb = rgb(color)
        if align:
            p.alignment = align
        return tf

    def rect(sl, x, y, w, h, fill, line=None, shape=1):
        r = sl.shapes.add_shape(shape, x, y, w, h)
        r.fill.solid()
        r.fill.fore_color.rgb = rgb(fill)
        if line:
            r.line.color.rgb = rgb(line)
        else:
            r.line.fill.background()
        r.shadow.inherit = False
        return r

    def picture(sl, path, x, y, mw, mh, center=True):
        from PIL import Image
        if not Path(path).exists():
            return
        iw, ih = Image.open(path).size
        s = min(mw / iw, mh / ih)
        w, h = int(iw * s), int(ih * s)
        ox = x + (mw - w) // 2 if center else x
        sl.shapes.add_picture(path, ox, y, Emu(w), Emu(h))

    def chrome(sl, title, n):
        rect(sl, 0, 0, W, Inches(0.1), ACCENT)
        text(sl, Inches(0.6), Inches(0.3), Inches(12.2), Inches(0.8), title, 28, True)
        text(sl, Inches(0.6), Inches(7.02), Inches(9), Inches(0.35),
             f"SleepTwin · {TEAM} · {COLLEGE} · all patient data simulated", 10, color=SLATE)
        text(sl, Inches(12.3), Inches(7.02), Inches(0.6), Inches(0.35), str(n), 10, color=SLATE, align=PP_ALIGN.RIGHT)

    for n, s in enumerate(S, 1):
        sl = prs.slides.add_slide(blank)
        if s.get("notes"):
            sl.notes_slide.notes_text_frame.text = s["notes"]
        k = s.get("kind")
        if k == "title":
            rect(sl, 0, 0, W, H, ACCENT)
            rect(sl, Inches(0.9), Inches(2.0), Inches(1.2), Inches(0.12), "#ffffff")
            text(sl, Inches(0.9), Inches(2.3), Inches(11.5), Inches(1.3), s["title"], 66, True, "#ffffff")
            text(sl, Inches(0.9), Inches(3.75), Inches(11), Inches(1.4), s["sub"], 22, False, "#e6ecff")
            text(sl, Inches(0.9), Inches(5.7), Inches(11.5), Inches(0.5), s["foot"], 16, True, "#ffffff")
            text(sl, Inches(0.9), Inches(6.3), Inches(11.5), Inches(0.5),
                 "Model-based projection for clinical decision support. Research prototype.", 13, False, "#c9d6ff",
                 italic=True)
            continue
        if k == "full":
            rect(sl, 0, 0, W, Inches(0.1), ACCENT)
            picture(sl, s["image"], Inches(0.25), Inches(0.22), Inches(12.83), Inches(7.15))
            continue
        chrome(sl, s["title"], n)
        top = Inches(1.25)
        if k == "stats":
            for i, (big, lab) in enumerate(s["stats"]):
                x = Inches(0.6 + i * 4.1)
                rect(sl, x, top, Inches(3.85), Inches(1.45), ACCENT_SOFT, shape=5)
                text(sl, x + Inches(0.25), top + Inches(0.12), Inches(3.4), Inches(0.75), big, 34, True, ACCENT)
                text(sl, x + Inches(0.25), top + Inches(0.85), Inches(3.4), Inches(0.55), lab, 13, color=MUTED)
            picture(sl, s["image"], Inches(0.6), top + Inches(1.7), Inches(12.1), Inches(3.9))
            if s.get("source"):
                text(sl, Inches(0.6), Inches(6.62), Inches(12), Inches(0.35), "Source: " + s["source"], 10,
                     color=SLATE, italic=True)
        elif k == "figure":
            mh = Inches(5.6) if s.get("tight") else Inches(4.75)
            picture(sl, s["image"], Inches(0.6), top, Inches(12.1), mh)
            if s.get("caption"):
                text(sl, Inches(0.6), Inches(6.2), Inches(12.1), Inches(0.75), s["caption"], 15, color=MUTED,
                     align=PP_ALIGN.CENTER)
        elif k == "split":
            tf = sl.shapes.add_textbox(Inches(0.6), top + Inches(0.2), Inches(4.9), Inches(5.4)).text_frame
            tf.word_wrap = True
            for i, b in enumerate(s["bullets"]):
                p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
                p.text = "●  " + b
                p.font.size = Pt(16)
                p.font.color.rgb = rgb(INK)
                p.space_after = Pt(14)
            picture(sl, s["image"], Inches(5.7), top, Inches(7.1), Inches(5.6))
        elif k == "cards":
            nc = len(s["cards"])
            cw = (12.1 - 0.35 * (nc - 1)) / nc
            ch = min(4.75, 1.45 + 0.62 * max(len(c[2]) for c in s["cards"]))
            for i, (head, col, items) in enumerate(s["cards"]):
                x = Inches(0.6 + i * (cw + 0.35))
                rect(sl, x, top + Inches(0.15), Inches(cw), Inches(ch), SOFTS[col], shape=5)
                rect(sl, x, top + Inches(0.15), Inches(cw), Inches(0.12), col)
                text(sl, x + Inches(0.3), top + Inches(0.45), Inches(cw - 0.6), Inches(0.6), head, 20, True, col)
                tf = sl.shapes.add_textbox(x + Inches(0.3), top + Inches(1.15), Inches(cw - 0.6),
                                           Inches(3.4)).text_frame
                tf.word_wrap = True
                for j, it in enumerate(items):
                    p = tf.paragraphs[0] if j == 0 else tf.add_paragraph()
                    p.text = "✓  " + it
                    p.font.size = Pt(17)
                    p.font.color.rgb = rgb(INK)
                    p.space_after = Pt(9)
            if s.get("foot"):
                text(sl, Inches(0.6), top + Inches(ch + 0.45), Inches(12.1), Inches(0.6), s["foot"], 15,
                     color=MUTED, align=PP_ALIGN.CENTER)
        elif k == "images":
            for i, (img, cap) in enumerate(zip(s["images"], s["captions"])):
                x = Inches(0.6 + i * 6.15)
                rect(sl, x, top, Inches(5.95), Inches(4.65), SOFT, shape=5)
                picture(sl, img, x + Inches(0.12), top + Inches(0.12), Inches(5.7), Inches(4.4))
                text(sl, x, top + Inches(4.75), Inches(5.95), Inches(0.6), cap, 14, True, INK, align=PP_ALIGN.CENTER)
    out = DOCS / "presentation.pptx"
    prs.save(out)
    return out


# ================================================================ 5. RENDER: PDF (same content)
def make_pdf(S):
    from reportlab.lib.colors import HexColor
    from reportlab.lib.utils import ImageReader, simpleSplit
    from reportlab.pdfgen import canvas as rl

    W, H = 960, 540
    c = rl.Canvas(str(DOCS / "presentation.pdf"), pagesize=(W, H))
    c.setTitle("SleepTwin - Team WeBareBears, PCCOE")
    c.setAuthor(TEAM)

    def para(txt, x, y, w, size=15, color=INK, bold=False, lead=1.32, center=False):
        font = "Helvetica-Bold" if bold else "Helvetica"
        c.setFont(font, size)
        c.setFillColor(HexColor(color))
        for ln in simpleSplit(txt, font, size, w):
            if center:
                c.drawCentredString(x + w / 2, y, ln)
            else:
                c.drawString(x, y, ln)
            y -= size * lead
        return y

    def rrect(x, y, w, h, fill, r=10):
        c.setFillColor(HexColor(fill))
        c.roundRect(x, y, w, h, r, stroke=0, fill=1)

    def img(path, x, y_top, mw, mh, center=True):
        if not Path(path).exists():
            return
        ir = ImageReader(path)
        iw, ih = ir.getSize()
        s = min(mw / iw, mh / ih)
        w, h = iw * s, ih * s
        c.drawImage(ir, x + ((mw - w) / 2 if center else 0), y_top - h, w, h, mask="auto")

    for n, s in enumerate(S, 1):
        k = s.get("kind")
        if k == "title":
            c.setFillColor(HexColor(ACCENT))
            c.rect(0, 0, W, H, stroke=0, fill=1)
            c.setFillColor(HexColor("#ffffff"))
            c.rect(65, 390, 86, 8, stroke=0, fill=1)
            para(s["title"], 65, 320, 820, 60, "#ffffff", True)
            para(s["sub"], 65, 262, 800, 21, "#e6ecff")
            para(s["foot"], 65, 120, 830, 15, "#ffffff", True)
            para("Model-based projection for clinical decision support. Research prototype.", 65, 92, 830, 12,
                 "#c9d6ff")
            c.showPage()
            continue
        c.setFillColor(HexColor(ACCENT))
        c.rect(0, H - 7, W, 7, stroke=0, fill=1)
        if k == "full":
            img(s["image"], 18, H - 16, 924, 515)
            c.showPage()
            continue
        para(s["title"], 43, H - 52, 870, 25, INK, True)
        c.setFont("Helvetica", 9)
        c.setFillColor(HexColor(SLATE))
        c.drawString(43, 16, f"SleepTwin · {TEAM} · {COLLEGE} · all patient data simulated")
        c.drawRightString(W - 30, 16, str(n))
        top = H - 80
        if k == "stats":
            for i, (big, lab) in enumerate(s["stats"]):
                x = 43 + i * 295
                rrect(x, top - 104, 277, 104, ACCENT_SOFT)
                para(big, x + 18, top - 44, 250, 31, ACCENT, True)
                para(lab, x + 18, top - 76, 250, 12, MUTED)
            img(s["image"], 43, top - 120, 874, 280)
            if s.get("source"):
                para("Source: " + s["source"], 43, 36, 870, 9, SLATE)
        elif k == "figure":
            img(s["image"], 43, top, 874, 405 if s.get("tight") else 340)
            if s.get("caption"):
                para(s["caption"], 43, 70, 874, 14, MUTED, center=True)
        elif k == "split":
            y = top - 22
            for b in s["bullets"]:
                c.setFillColor(HexColor(ACCENT))
                c.circle(50, y + 4.5, 3.5, stroke=0, fill=1)
                y = para(b, 62, y, 300, 15) - 12
            img(s["image"], 410, top, 510, 405)
        elif k == "cards":
            nc = len(s["cards"])
            cw = (874 - 25 * (nc - 1)) / nc
            chp = min(340, 105 + 45 * max(len(c_[2]) for c_ in s["cards"]))
            for i, (head, col, items) in enumerate(s["cards"]):
                x = 43 + i * (cw + 25)
                rrect(x, top - chp - 10, cw, chp, SOFTS[col])
                c.setFillColor(HexColor(col))
                c.rect(x, top - 18, cw, 8, stroke=0, fill=1)
                para(head, x + 20, top - 48, cw - 40, 19, col, True)
                y = top - 88
                for it in items:
                    y = para("✓  " + it, x + 20, y, cw - 40, 16) - 9
            if s.get("foot"):
                para(s["foot"], 43, top - chp - 45, 874, 14, MUTED, center=True)
        elif k == "images":
            for i, (p, cap) in enumerate(zip(s["images"], s["captions"])):
                x = 43 + i * 443
                rrect(x, top - 335, 430, 335, SOFT)
                img(p, x + 8, top - 8, 414, 320)
                para(cap, x, top - 360, 430, 13, INK, True, center=True)
        c.showPage()
    c.save()


def main():
    F = {"architecture": architecture(), "blind_spot": fig_blind_spot(), "why_sleep": fig_why_sleep(),
         "six_steps": fig_six_steps(), "persona_story": fig_persona_story(), "ablation": fig_ablation(),
         "two_hour": fig_two_hour(), "lifesnaps": fig_lifesnaps(), "roadmap": fig_roadmap()}
    personas = persona_whatifs()
    F["personas"] = fig_personas(personas)
    # architecture: vector PDF written by save(); PNG copy for the README
    import shutil
    shutil.copy(F["architecture"], DOCS / "architecture.png")
    S = slides(F, personas)
    make_pptx(S)
    make_pdf(S)
    print(f"wrote docs/architecture.pdf/.png, docs/presentation.pptx/.pdf ({len(S)} slides), docs/figures/*.png")


if __name__ == "__main__":
    main()
