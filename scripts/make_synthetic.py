"""Generate small FIRMS-format CSVs (VIIRS + MODIS) for tests and frontend development.

Synthetic data are clearly labelled and must never be reported as research results.
Usage: python scripts/make_synthetic.py data/raw/synthetic
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

VIIRS_COLS = ["latitude", "longitude", "bright_ti4", "scan", "track", "acq_date", "acq_time", "satellite",
              "instrument", "confidence", "version", "bright_ti5", "frp", "daynight", "type"]
MODIS_COLS = ["latitude", "longitude", "brightness", "scan", "track", "acq_date", "acq_time", "satellite",
              "instrument", "confidence", "version", "bright_t31", "frp", "daynight", "type"]


def make(seed: int = 7, start: str = "2025-07-01") -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    t0 = pd.Timestamp(start)
    v_rows, m_rows = [], []

    def add_v(lat, lon, ts, conf="n", frp=None, typ=0):
        v_rows.append([round(lat, 5), round(lon, 5), round(rng.uniform(300, 367), 2), 0.4, 0.37,
                       ts.strftime("%Y-%m-%d"), int(ts.strftime("%H%M")), "N20", "VIIRS", conf, "2.0NRT",
                       round(rng.uniform(270, 300), 2), round(frp if frp is not None else rng.gamma(2, 6), 2),
                       "D" if 6 <= ts.hour < 18 else "N", typ])

    def add_m(lat, lon, ts, conf=70):
        m_rows.append([round(lat, 4), round(lon, 4), round(rng.uniform(310, 360), 1), 1.0, 1.0,
                       ts.strftime("%Y-%m-%d"), int(ts.strftime("%H%M")), "Aqua", "MODIS", conf, "6.1NRT",
                       round(rng.uniform(280, 300), 1), round(rng.gamma(2, 10), 1),
                       "D" if 6 <= ts.hour < 18 else "N", 0])

    # 1) Large multi-day fires (East Kazakhstan / Kostanay / Pavlodar-like areas)
    fires = [(49.9, 82.6, 0, 4, 60), (53.2, 63.6, 10, 2, 25), (52.3, 76.9, 20, 1, 8), (50.5, 80.2, 35, 3, 40)]
    for lat, lon, day, days, n in fires:
        for k in range(n):
            ts = t0 + pd.Timedelta(days=day + rng.uniform(0, days), hours=0)
            ts = ts.replace(hour=int(rng.choice([2, 8, 9, 20])), minute=int(rng.integers(0, 59)))
            la, lo = lat + rng.normal(0, 0.01), lon + rng.normal(0, 0.015)
            add_v(la, lo, ts, conf=rng.choice(["n", "h"]), frp=rng.gamma(2, 15))
            if k % 4 == 0:
                add_m(la + rng.normal(0, 0.004), lo + rng.normal(0, 0.004), ts + pd.Timedelta(minutes=40))

    # 2) Same location as fire 1 but 60 days later -> must be a separate event in ST-DBSCAN
    for _ in range(6):
        ts = (t0 + pd.Timedelta(days=60)).replace(hour=8, minute=int(rng.integers(0, 59)))
        add_v(49.9 + rng.normal(0, 0.005), 82.6 + rng.normal(0, 0.005), ts, conf="n")

    # 3) Isolated detections (noise)
    for _ in range(40):
        ts = (t0 + pd.Timedelta(days=float(rng.uniform(0, 80)))).replace(hour=9, minute=10)
        add_v(rng.uniform(42, 54), rng.uniform(50, 85), ts, conf="n")

    # 4) Persistent gas flare in Mangystau (type 2) -> removed by the type filter
    for d in range(50):
        add_v(43.35 + rng.normal(0, 0.001), 52.86 + rng.normal(0, 0.001), (t0 + pd.Timedelta(days=d)).replace(hour=21),
              conf="n", typ=2)

    # 5) Low-confidence + invalid + duplicate rows
    for _ in range(10):
        add_v(rng.uniform(42, 54), rng.uniform(50, 85), t0.replace(hour=10), conf="l")
    add_v(95.0, 70.0, t0.replace(hour=10))  # impossible latitude
    v_rows.append(v_rows[0].copy())  # exact duplicate

    v = pd.DataFrame(v_rows, columns=VIIRS_COLS)
    m = pd.DataFrame(m_rows, columns=MODIS_COLS)
    return v, m


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "data/raw/synthetic")
    out.mkdir(parents=True, exist_ok=True)
    v, m = make()
    v.to_csv(out / "viirs_synthetic.csv", index=False)
    m.to_csv(out / "modis_synthetic.csv", index=False)
    print(f"Wrote {len(v)} VIIRS and {len(m)} MODIS synthetic rows to {out}")
