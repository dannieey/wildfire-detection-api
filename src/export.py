"""Serialisation helpers: CSV / GeoJSON / JSON outputs shared by the pipeline and the API."""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

DETECTION_PROPS = [
    "detection_id", "event_id", "sensor", "satellite", "acq_datetime", "acq_date", "brightness_k",
    "brightness2_k", "frp", "confidence_level", "confidence_raw", "daynight", "region",
]
EVENT_PROPS = [
    "event_id", "sensor", "n_detections", "start_time", "end_time", "duration_hours", "n_overpass_days",
    "centroid_lat", "centroid_lon", "area_km2", "max_extent_km", "max_frp", "sum_frp", "mean_frp",
    "mean_brightness_k", "share_high_confidence", "n_day", "n_night", "region", "priority", "status",
    "persistent_hotspot",
]


def jsonable(v):
    if v is None or v is pd.NA or v is pd.NaT:
        return None
    if isinstance(v, (pd.Timestamp,)):
        return v.isoformat()
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating, float)):
        return None if math.isnan(v) else float(v)
    if isinstance(v, np.bool_):
        return bool(v)
    if isinstance(v, (list, tuple)):
        return [jsonable(x) for x in v]
    if isinstance(v, dict):
        return {k: jsonable(x) for k, x in v.items()}
    try:
        if pd.isna(v):
            return None
    except (TypeError, ValueError):
        pass
    return v


def detections_geojson(df: pd.DataFrame) -> dict:
    props = [c for c in DETECTION_PROPS if c in df.columns]
    feats = [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [round(float(lon), 5), round(float(lat), 5)]},
            "properties": {k: jsonable(v) for k, v in zip(props, vals)},
        }
        for lon, lat, *vals in df[["longitude", "latitude", *props]].itertuples(index=False, name=None)
    ]
    return {"type": "FeatureCollection", "features": feats}


def events_geojson(ev: pd.DataFrame, geometry: str = "point") -> dict:
    """geometry='point' -> centroid; 'hull' -> convex-hull polygon (falls back to centroid)."""
    feats = []
    for rec in ev.to_dict(orient="records"):
        hull = rec.get("hull")
        if isinstance(hull, str):
            hull = json.loads(hull) if hull else None
        if geometry == "hull" and hull:
            geom = {"type": "Polygon", "coordinates": [hull]}
        else:
            geom = {"type": "Point", "coordinates": [rec["centroid_lon"], rec["centroid_lat"]]}
        feats.append({"type": "Feature", "id": rec["event_id"], "geometry": geom,
                      "properties": {k: jsonable(rec.get(k)) for k in EVENT_PROPS}})
    return {"type": "FeatureCollection", "features": feats}


def dump_json(obj, path: Path) -> None:
    path.write_text(json.dumps(jsonable(obj), indent=2, ensure_ascii=False), encoding="utf-8")


def write_outputs(out_dir: Path, det: pd.DataFrame, events: pd.DataFrame, meta: dict, evaluation: dict) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    det.to_csv(out_dir / "detections.csv", index=False)
    ev = events.copy()
    ev["hull"] = ev["hull"].map(lambda h: json.dumps(h) if h else "")
    ev.to_csv(out_dir / "events.csv", index=False)
    dump_json(events_geojson(events), out_dir / "events.geojson")
    dump_json(detections_geojson(det), out_dir / "detections.geojson")
    dump_json(meta, out_dir / "meta.json")
    dump_json(evaluation, out_dir / "evaluation.json")
    if "sensitivity_viirs" in evaluation:
        pd.DataFrame(evaluation["sensitivity_viirs"]).to_csv(out_dir / "sensitivity_viirs.csv", index=False)


def load_outputs(out_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, dict, dict]:
    det = pd.read_csv(out_dir / "detections.csv", low_memory=False)
    det["acq_datetime"] = pd.to_datetime(det["acq_datetime"], utc=True, format="ISO8601")
    ev = pd.read_csv(out_dir / "events.csv", low_memory=False)
    for c in ("start_time", "end_time"):
        ev[c] = pd.to_datetime(ev[c], utc=True, format="ISO8601")
    ev["hull"] = ev["hull"].map(lambda s: json.loads(s) if isinstance(s, str) and s else None)
    meta = json.loads((out_dir / "meta.json").read_text(encoding="utf-8"))
    evaluation = json.loads((out_dir / "evaluation.json").read_text(encoding="utf-8"))
    return det, ev, meta, evaluation
