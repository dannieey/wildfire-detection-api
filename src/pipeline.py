"""End-to-end processing pipeline (CLI).

Examples
--------
# Research dataset (FIRMS yearly country files, Kazakhstan 2025)
python -m src.pipeline --name kz_2025 \
    --viirs data/raw/viirs-jpss1_2025_Kazakhstan.csv data/raw/viirs-snpp_2025_Kazakhstan.csv \
    --modis data/raw/modis_2025_Kazakhstan.csv --sensitivity

# Live mode: download last 3 days from the FIRMS API (needs FIRMS_MAP_KEY) and process
python -m src.pipeline --name live --fetch-nrt --days 3
"""
from __future__ import annotations

import argparse
import json
import logging
import time
from pathlib import Path

import pandas as pd

from src.analysis.evaluation import describe_clustering, h1_cross_sensor_test, h2_temporal_vs_spatial, sensitivity_grid
from src.analysis.regions import assign_regions
from src.clustering.events import summarise_events
from src.clustering.st_dbscan import cluster_detections
from src.core.config import settings
from src.export import write_outputs
from src.ingestion.firms_client import download_nrt
from src.processing.clean import CleaningConfig, clean_detections
from src.processing.schema import load_firms_csv

log = logging.getLogger("pipeline")


def load_many(paths: list[str | Path]) -> pd.DataFrame:
    frames = [load_firms_csv(p) for p in paths]
    for p, f in zip(paths, frames):
        log.info("Loaded %s: %d rows (%s)", Path(p).name, len(f), f["sensor"].iloc[0] if len(f) else "?")
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def run(
    name: str,
    viirs: list[str],
    modis: list[str],
    regions: str | None = None,
    cfg: CleaningConfig | None = None,
    eps_km: float = settings.eps_km,
    eps_days: float = settings.eps_days,
    min_samples: int = settings.min_samples,
    evaluate: bool = True,
    sensitivity: bool = False,
    live: bool = False,
) -> dict:
    t0 = time.perf_counter()
    cfg = cfg or CleaningConfig()
    out_dir = settings.processed_dir / name
    reports, cleaned = {}, []
    for label, files in (("VIIRS", viirs), ("MODIS", modis)):
        if not files:
            continue
        df, rep = clean_detections(load_many(files), cfg)
        reports[label] = rep.to_dict() | {"files": [Path(f).name for f in files]}
        cleaned.append(df)
    if not cleaned:
        raise SystemExit("No input files given.")
    det = pd.concat(cleaned, ignore_index=True)

    regions = regions or (settings.reference_dir / "kaz_adm1.geojson")
    det["region"] = assign_regions(det, regions)
    if Path(regions).exists():
        before = len(det)
        det = det[det["region"].notna()].reset_index(drop=True)
        log.info("Outside Kazakhstan border removed: %d", before - len(det))
        for r in reports.values():
            r["outside_country_removed_total"] = before - len(det)

    t1 = time.perf_counter()
    det = cluster_detections(det, eps_km=eps_km, eps_days=eps_days, min_samples=min_samples)
    ref_time = pd.Timestamp.now(tz="UTC") if live else None
    events = summarise_events(det, reference_time=ref_time)
    t2 = time.perf_counter()

    evaluation: dict = {"params": {"eps_km": eps_km, "eps_days": eps_days, "min_samples": min_samples}}
    for sensor in det["sensor"].unique():
        evaluation[f"summary_{sensor}"] = describe_clustering(
            det[det["sensor"] == sensor], events[events["sensor"] == sensor]
        )
    v = det[det["sensor"] == "VIIRS"]
    m = det[det["sensor"] == "MODIS"]
    if evaluate and len(v) and len(m):
        evaluation["h1_cross_sensor"] = h1_cross_sensor_test(v, m, settings.match_km, settings.match_days)
    if evaluate and len(v):
        evaluation["h2_temporal_vs_spatial"] = h2_temporal_vs_spatial(v, eps_km, eps_days, min_samples)
    if sensitivity and len(v):
        evaluation["sensitivity_viirs"] = sensitivity_grid(v)

    meta = {
        "dataset": name,
        "mode": "live" if live else "archive",
        "generated_at": pd.Timestamp.now(tz="UTC").isoformat(),
        "period_start": det["acq_datetime"].min().isoformat() if len(det) else None,
        "period_end": det["acq_datetime"].max().isoformat() if len(det) else None,
        "sensors": sorted(det["sensor"].unique().tolist()),
        "regions": sorted(det["region"].dropna().unique().tolist()),
        "n_detections": int(len(det)),
        "n_events": int(len(events)),
        "timing_seconds": {"load_clean": round(t1 - t0, 2), "cluster_summarise": round(t2 - t1, 2),
                           "total": round(time.perf_counter() - t0, 2)},
        "quality": reports,
    }
    write_outputs(out_dir, det, events, meta, evaluation)
    log.info("Done: %d detections -> %d events in %.1fs. Output: %s", len(det), len(events),
             meta["timing_seconds"]["total"], out_dir)
    return meta


def main(argv=None) -> None:
    p = argparse.ArgumentParser(description="PyroScope processing pipeline")
    p.add_argument("--name", default="kz_2025", help="dataset name (folder under data/processed)")
    p.add_argument("--viirs", nargs="*", default=[])
    p.add_argument("--modis", nargs="*", default=[])
    p.add_argument("--regions", default=None, help="ADM1 GeoJSON (default data/reference/kaz_adm1.geojson)")
    p.add_argument("--start"), p.add_argument("--end")
    p.add_argument("--eps-km", type=float, default=settings.eps_km)
    p.add_argument("--eps-days", type=float, default=settings.eps_days)
    p.add_argument("--min-samples", type=int, default=settings.min_samples)
    p.add_argument("--keep-low-confidence", action="store_true")
    p.add_argument("--keep-all-types", action="store_true", help="do not drop static sources (type 2) etc.")
    p.add_argument("--no-evaluation", action="store_true")
    p.add_argument("--sensitivity", action="store_true", help="run eps_km x eps_days grid (slower)")
    p.add_argument("--fetch-nrt", action="store_true", help="download last --days from FIRMS API first")
    p.add_argument("--days", type=int, default=3)
    a = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    viirs, modis = list(a.viirs), list(a.modis)
    if a.fetch_nrt:
        for path in download_nrt(settings.raw_dir / a.name, day_range=a.days):
            (modis if "modis" in path.name else viirs).append(str(path))
    cfg = CleaningConfig(
        start=a.start, end=a.end,
        drop_low_confidence=not a.keep_low_confidence,
        keep_types=() if a.keep_all_types else (0,),
    )
    meta = run(a.name, viirs, modis, a.regions, cfg, a.eps_km, a.eps_days, a.min_samples,
               evaluate=not a.no_evaluation, sensitivity=a.sensitivity, live=a.fetch_nrt)
    print(json.dumps({k: meta[k] for k in ("dataset", "n_detections", "n_events", "timing_seconds")}, indent=2))


if __name__ == "__main__":
    main()
