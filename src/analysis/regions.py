"""Assign detections to Kazakhstan administrative regions (oblasts).

Uses a GeoJSON of ADM1 boundaries placed at data/reference/kaz_adm1.geojson
(e.g. geoBoundaries KAZ ADM1, CC BY 4.0). Pure numpy/matplotlib point-in-polygon,
so no GeoPandas/Shapely install is needed. If the file is absent, region = None.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from matplotlib.path import Path as MplPath

NAME_KEYS = ("shapeName", "name", "NAME_1", "name_en", "NAME")


def load_regions(path: str | Path) -> list[tuple[str, list[MplPath], tuple[float, float, float, float]]]:
    gj = json.loads(Path(path).read_text(encoding="utf-8"))
    regions = []
    for feat in gj["features"]:
        props = feat.get("properties", {})
        name = next((props[k] for k in NAME_KEYS if props.get(k)), "Unknown")
        geom = feat["geometry"]
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        paths = [MplPath(np.asarray(poly[0])[:, :2]) for poly in polys]  # outer rings
        allpts = np.vstack([p.vertices for p in paths])
        bbox = (allpts[:, 0].min(), allpts[:, 1].min(), allpts[:, 0].max(), allpts[:, 1].max())
        regions.append((name, paths, bbox))
    return regions


def assign_regions(df: pd.DataFrame, regions_path: str | Path | None) -> pd.Series:
    out = pd.Series(pd.NA, index=df.index, dtype="object")
    if not regions_path or not Path(regions_path).exists() or df.empty:
        return out
    pts = df[["longitude", "latitude"]].to_numpy()
    unassigned = np.ones(len(df), dtype=bool)
    for name, paths, (x0, y0, x1, y1) in load_regions(regions_path):
        cand = unassigned & (pts[:, 0] >= x0) & (pts[:, 0] <= x1) & (pts[:, 1] >= y0) & (pts[:, 1] <= y1)
        if not cand.any():
            continue
        idx = np.flatnonzero(cand)
        inside = np.zeros(len(idx), dtype=bool)
        for p in paths:
            inside |= p.contains_points(pts[idx])
        hit = idx[inside]
        out.iloc[hit] = name
        unassigned[hit] = False
    return out
