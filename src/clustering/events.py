"""Turn clustered detections into candidate-event summaries."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.spatial import ConvexHull, QhullError

KM_PER_DEG_LAT = 111.32


@dataclass
class PriorityRules:
    """Transparent, documented thresholds (report them in the paper)."""

    high_max_frp: float = 100.0  # MW
    high_points: int = 50
    high_area_km2: float = 25.0
    medium_max_frp: float = 30.0
    medium_points: int = 10
    active_hours: float = 48.0
    persistent_days: float = 30.0  # long-lived + tiny footprint => likely static heat source
    persistent_max_extent_km: float = 2.0


def _local_xy_km(lat: np.ndarray, lon: np.ndarray) -> np.ndarray:
    lat0 = np.radians(lat.mean())
    return np.column_stack([(lon - lon.mean()) * KM_PER_DEG_LAT * np.cos(lat0), (lat - lat.mean()) * KM_PER_DEG_LAT])


def _hull(lat: np.ndarray, lon: np.ndarray) -> tuple[list[list[float]] | None, float, float]:
    """Return (closed lon/lat ring or None, area_km2, max_extent_km)."""
    xy = _local_xy_km(lat, lon)
    extent = float(np.ptp(xy, axis=0).max()) if len(xy) > 1 else 0.0
    pts = np.unique(np.column_stack([lon, lat]), axis=0)
    if len(pts) < 3:
        return None, 0.0, extent
    try:
        h = ConvexHull(pts)
    except QhullError:  # collinear points
        return None, 0.0, extent
    ring = pts[h.vertices].tolist()
    ring.append(ring[0])
    area = float(ConvexHull(_local_xy_km(pts[:, 1], pts[:, 0])).volume)  # 2-D "volume" = area
    return ring, round(area, 3), round(extent, 3)


def summarise_events(
    df: pd.DataFrame, rules: PriorityRules | None = None, reference_time: pd.Timestamp | None = None
) -> pd.DataFrame:
    rules = rules or PriorityRules()
    clustered = df[~df["is_noise"]]
    if clustered.empty:
        return pd.DataFrame(columns=EVENT_COLUMNS)
    ref = reference_time or df["acq_datetime"].max()

    rows = []
    for event_id, g in clustered.groupby("event_id", sort=False):
        lat, lon = g["latitude"].to_numpy(), g["longitude"].to_numpy()
        ring, area, extent = _hull(lat, lon)
        start, end = g["acq_datetime"].min(), g["acq_datetime"].max()
        duration_h = (end - start).total_seconds() / 3600
        max_frp = g["frp"].max()
        n = len(g)
        if (max_frp >= rules.high_max_frp) or n >= rules.high_points or area >= rules.high_area_km2:
            priority = "high"
        elif (max_frp >= rules.medium_max_frp) or n >= rules.medium_points:
            priority = "medium"
        else:
            priority = "low"
        rows.append(
            {
                "event_id": event_id,
                "sensor": g["sensor"].iloc[0],
                "n_detections": n,
                "start_time": start,
                "end_time": end,
                "duration_hours": round(duration_h, 2),
                "n_overpass_days": g["acq_date"].nunique(),
                "centroid_lat": round(float(lat.mean()), 5),
                "centroid_lon": round(float(lon.mean()), 5),
                "min_lat": float(lat.min()), "max_lat": float(lat.max()),
                "min_lon": float(lon.min()), "max_lon": float(lon.max()),
                "area_km2": area,
                "max_extent_km": extent,
                "max_frp": _r(max_frp),
                "sum_frp": _r(g["frp"].sum()),
                "mean_frp": _r(g["frp"].mean()),
                "mean_brightness_k": _r(g["brightness_k"].mean()),
                "share_high_confidence": round(float((g["confidence_level"] == "high").mean()), 3),
                "n_day": int((g["daynight"] == "D").sum()),
                "n_night": int((g["daynight"] == "N").sum()),
                "region": _mode(g["region"]) if "region" in g else None,
                "priority": priority,
                "status": "active" if (ref - end) <= pd.Timedelta(hours=rules.active_hours) else "inactive",
                "persistent_hotspot": bool(
                    duration_h / 24 >= rules.persistent_days and extent <= rules.persistent_max_extent_km
                ),
                "hull": ring,
            }
        )
    ev = pd.DataFrame(rows, columns=EVENT_COLUMNS)
    return ev.sort_values(["start_time", "event_id"]).reset_index(drop=True)


def _r(v) -> float | None:
    return None if pd.isna(v) else round(float(v), 2)


def _mode(s: pd.Series):
    s = s.dropna()
    return None if s.empty else s.mode().iloc[0]


EVENT_COLUMNS = [
    "event_id", "sensor", "n_detections", "start_time", "end_time", "duration_hours", "n_overpass_days",
    "centroid_lat", "centroid_lon", "min_lat", "max_lat", "min_lon", "max_lon", "area_km2", "max_extent_km",
    "max_frp", "sum_frp", "mean_frp", "mean_brightness_k", "share_high_confidence", "n_day", "n_night",
    "region", "priority", "status", "persistent_hotspot", "hull",
]
