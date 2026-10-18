"""Run the whole SleepTwin pipeline end-to-end:  python -m src.pipeline

calibrate -> simulate cohort -> features -> next-day models -> 2-hour model -> LifeSnaps validation -> results.md
"""
from __future__ import annotations

import time

from . import features, generate_cohort, short_horizon, train, validate_lifesnaps
from .calibration import build_lifesnaps_ranges, build_nhanes_pool
from .integrity import write_manifest
from .report import write_results


def main():
    t0 = time.time()
    for name, fn in (("NHANES pool", build_nhanes_pool), ("LifeSnaps ranges", build_lifesnaps_ranges)):
        try:
            fn()
            print(f"[calibration] {name}: built from downloaded data")
        except Exception as e:  # noqa: BLE001
            print(f"[calibration] {name}: raw data missing ({e.__class__.__name__}) -> fallback ranges")
    print("[1/5] simulating cohort ...")
    generate_cohort.run(verbose=False)
    print("[2/5] features ...")
    features.build_all()
    print("[3/5] next-day models (ablation, GroupKFold, SHAP) ...")
    train.main()
    print("[4/5] 2-hour spike model ...")
    short_horizon.main()
    print("[5/5] LifeSnaps real-data validation ...")
    validate_lifesnaps.main()
    write_manifest()
    write_results()
    print(f"done in {time.time() - t0:.0f}s -> reports/results.md")


if __name__ == "__main__":
    main()
