"""Spatiotemporal DBSCAN for satellite fire detections.

Two detections are neighbours only if they are within ``eps_km`` (great-circle
distance) AND within ``eps_days`` of each other. Density reachability then chains
detections across consecutive overpasses, so a fire burning for several days
remains one candidate event while two fires at the same place months apart do
not merge. Setting ``eps_days=None`` reproduces the spatial-only baseline used
in Assignment 3.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.cluster import DBSCAN
from sklearn.neighbors import BallTree

EARTH_RADIUS_KM = 6371.0088


def st_dbscan_labels(
    lat: np.ndarray,
    lon: np.ndarray,
    t: pd.Series | np.ndarray | None,
    eps_km: float = 3.0,
    eps_days: float | None = 2.0,
    min_samples: int = 2,
) -> np.ndarray:
    """Return a cluster label per point (-1 = noise)."""
    n = len(lat)
    if n == 0:
        return np.array([], dtype=int)
    coords = np.radians(np.column_stack([lat, lon]))

    if eps_days is None or t is None:
        db = DBSCAN(eps=eps_km / EARTH_RADIUS_KM, min_samples=min_samples, metric="haversine", algorithm="ball_tree")
        return db.fit_predict(coords)

    tree = BallTree(coords, metric="haversine")
    ind, dist = tree.query_radius(coords, r=eps_km / EARTH_RADIUS_KM, return_distance=True)
    counts = np.fromiter((len(a) for a in ind), dtype=np.int64, count=n)
    rows = np.repeat(np.arange(n), counts)
    cols = np.concatenate(ind)
    d_km = np.concatenate(dist) * EARTH_RADIUS_KM

    t_days = _to_days(t)
    keep = np.abs(t_days[rows] - t_days[cols]) <= eps_days
    rows, cols, d_km = rows[keep], cols[keep], d_km[keep]

    # +1e-6 keeps zero distances (incl. self-pairs) as explicit sparse entries.
    graph = sparse.csr_matrix((d_km + 1e-6, (rows, cols)), shape=(n, n))
    db = DBSCAN(eps=eps_km + 1e-3, min_samples=min_samples, metric="precomputed")
    return db.fit_predict(graph)


def _to_days(t) -> np.ndarray:
    s = pd.to_datetime(pd.Series(t), utc=True)
    return (s - pd.Timestamp("1970-01-01", tz="UTC")).dt.total_seconds().to_numpy() / 86400.0


def cluster_detections(
    df: pd.DataFrame,
    eps_km: float = 3.0,
    eps_days: float | None = 2.0,
    min_samples: int = 2,
    group_by_sensor: bool = True,
) -> pd.DataFrame:
    """Add ``event_id`` (e.g. 'VIIRS-000123', None for noise) and ``is_noise`` columns."""
    out = df.copy()
    out["event_id"] = pd.Series(pd.NA, index=out.index, dtype="object")
    groups = out.groupby("sensor").groups.items() if group_by_sensor else [("ALL", out.index)]
    for sensor, idx in groups:
        sub = out.loc[idx]
        labels = st_dbscan_labels(
            sub["latitude"].to_numpy(), sub["longitude"].to_numpy(), sub["acq_datetime"],
            eps_km=eps_km, eps_days=eps_days, min_samples=min_samples,
        )
        ids = np.where(labels >= 0, [f"{sensor}-{l:06d}" for l in labels], None)
        out.loc[idx, "event_id"] = ids
    out["is_noise"] = out["event_id"].isna()
    return out
